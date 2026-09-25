import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import uuid7
from app.core.storage import Storage, public_url
from app.modules.media.schemas import (
    EXTENSIONS,
    MAX_BYTES,
    ImageKind,
    ProfileImages,
    UploadRequest,
    UploadTicket,
)
from app.modules.users.models import User

log = logging.getLogger(__name__)


class UploadNotFoundError(Exception):
    pass


class UploadRejectedError(Exception):
    pass


def _key_pattern(kind: ImageKind, user: User) -> re.Pattern[str]:
    extensions = "|".join(EXTENSIONS.values())
    return re.compile(rf"{kind}s/{user.id}/[0-9a-f-]{{36}}\.(?:{extensions})")


def create_upload(storage: Storage, user: User, data: UploadRequest) -> UploadTicket:
    key = f"{data.kind}s/{user.id}/{uuid7()}.{EXTENSIONS[data.content_type]}"
    url = storage.presign_upload(key, content_type=data.content_type, size=data.size)
    return UploadTicket(key=key, upload_url=url, headers={"Content-Type": data.content_type})


def images(user: User) -> ProfileImages:
    return ProfileImages(
        avatar_url=public_url(user.profile.avatar_key),
        banner_url=public_url(user.profile.banner_key),
    )


async def _discard(storage: Storage, key: str | None) -> None:
    # Best effort: a leftover file costs a little storage, a failed request costs the person.
    if key is None:
        return
    try:
        await storage.delete(key)
    except Exception:
        log.warning("Couldn't delete %s", key, exc_info=True)


async def attach(
    db: AsyncSession, storage: Storage, user: User, kind: ImageKind, key: str
) -> ProfileImages:
    """Point the profile at an uploaded file after checking it is theirs and within limits."""
    if not _key_pattern(kind, user).fullmatch(key):
        raise UploadNotFoundError
    stored = await storage.head(key)
    if stored is None:
        raise UploadNotFoundError
    if stored.size > MAX_BYTES[kind] or stored.content_type not in EXTENSIONS:
        await _discard(storage, key)
        raise UploadRejectedError
    field = f"{kind}_key"
    previous: str | None = getattr(user.profile, field)
    if previous == key:
        return images(user)
    setattr(user.profile, field, key)
    await db.commit()
    await _discard(storage, previous)
    return images(user)


async def remove(db: AsyncSession, storage: Storage, user: User, kind: ImageKind) -> ProfileImages:
    field = f"{kind}_key"
    previous: str | None = getattr(user.profile, field)
    setattr(user.profile, field, None)
    await db.commit()
    await _discard(storage, previous)
    return images(user)
