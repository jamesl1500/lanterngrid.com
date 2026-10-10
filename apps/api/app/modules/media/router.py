from fastapi import APIRouter, HTTPException, status

from app.core.db import SessionDep
from app.core.storage import StorageDep
from app.modules.auth.deps import CurrentUserDep
from app.modules.auth.limits import limit_writes
from app.modules.media import service
from app.modules.media.schemas import (
    AttachImage,
    ImageKind,
    ProfileImages,
    UploadRequest,
    UploadTicket,
)

router = APIRouter(tags=["media"])


@router.post("/me/uploads", operation_id="createUpload", status_code=status.HTTP_201_CREATED)
async def create_upload(
    data: UploadRequest, user: CurrentUserDep, storage: StorageDep
) -> UploadTicket:
    await limit_writes(user, "upload")
    return service.create_upload(storage, user, data)


@router.put("/me/images/{kind}", operation_id="setMyImage")
async def set_my_image(
    kind: ImageKind, data: AttachImage, user: CurrentUserDep, db: SessionDep, storage: StorageDep
) -> ProfileImages:
    await limit_writes(user, "profile")
    try:
        return await service.attach(db, storage, user, kind, data.key)
    except service.UploadNotFoundError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "We couldn't find that upload. Try again."
        ) from None
    except service.UploadRejectedError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "That file is too large or isn't a supported image."
        ) from None


@router.delete("/me/images/{kind}", operation_id="removeMyImage")
async def remove_my_image(
    kind: ImageKind, user: CurrentUserDep, db: SessionDep, storage: StorageDep
) -> ProfileImages:
    return await service.remove(db, storage, user, kind)
