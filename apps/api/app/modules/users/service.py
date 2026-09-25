import uuid
from collections.abc import Sequence

from sqlalchemy import delete, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import public_url
from app.modules.tags import service as tags
from app.modules.users.models import ProfileLink, User
from app.modules.users.schemas import (
    OnboardingRequest,
    ProfileLinkIn,
    ProfileLinkOut,
    ProfileSettings,
    ProfileUpdate,
    PublicProfile,
    UsernameAvailability,
    username_problem,
)


class UsernameTakenError(Exception):
    pass


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    # username is citext, so this match is case-insensitive.
    return (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()


async def check_username(db: AsyncSession, username: str) -> UsernameAvailability:
    problem = username_problem(username)
    if problem is None:
        taken = await db.scalar(select(func.count()).where(User.username == username))
        if taken:
            return UsernameAvailability(username=username, available=False, problem="taken")
    return UsernameAvailability(username=username, available=problem is None, problem=problem)


async def complete_onboarding(db: AsyncSession, user: User, data: OnboardingRequest) -> User:
    if await get_by_username(db, data.username):
        raise UsernameTakenError
    user.username = data.username
    user.display_name = data.display_name
    user.profile.headline = data.headline
    await tags.set_user_tags(db, user.id, data.tags)
    try:
        await db.commit()
    except IntegrityError as exc:  # lost a race for the same name
        await db.rollback()
        raise UsernameTakenError from exc
    return user


async def update_profile(db: AsyncSession, user: User, data: ProfileUpdate) -> User:
    changes = data.model_dump(exclude_unset=True)
    if "display_name" in changes:
        if changes["display_name"] is None:
            del changes["display_name"]
        else:
            user.display_name = changes.pop("display_name")
    if changes.get("accent_color", "") is None:
        del changes["accent_color"]
    for field, value in changes.items():
        setattr(user.profile, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def links(db: AsyncSession, user_id: uuid.UUID) -> list[ProfileLinkOut]:
    rows = await db.scalars(
        select(ProfileLink).where(ProfileLink.user_id == user_id).order_by(ProfileLink.position)
    )
    return [ProfileLinkOut(kind=link.kind, url=link.url) for link in rows]


async def set_links(db: AsyncSession, user_id: uuid.UUID, items: Sequence[ProfileLinkIn]) -> None:
    await db.execute(delete(ProfileLink).where(ProfileLink.user_id == user_id))
    if items:
        await db.execute(
            insert(ProfileLink),
            [
                {"user_id": user_id, "kind": item.kind, "url": item.url, "position": i}
                for i, item in enumerate(items)
            ],
        )
    await db.commit()


async def profile_settings(db: AsyncSession, user: User) -> ProfileSettings:
    p = user.profile
    return ProfileSettings(
        display_name=user.display_name,
        headline=p.headline,
        bio=p.bio,
        location=p.location,
        website=p.website,
        accent_color=p.accent_color,
        avatar_url=public_url(p.avatar_key),
        banner_url=public_url(p.banner_key),
        links=await links(db, user.id),
        tags=await tags.user_tags(db, user.id),
    )


async def public_profile(db: AsyncSession, user: User) -> PublicProfile:
    assert user.username is not None
    p = user.profile
    return PublicProfile(
        username=user.username,
        display_name=user.display_name,
        headline=p.headline,
        bio=p.bio,
        location=p.location,
        website=p.website,
        accent_color=p.accent_color,
        avatar_url=public_url(p.avatar_key),
        banner_url=public_url(p.banner_key),
        links=await links(db, user.id),
        tags=await tags.user_tags(db, user.id),
        joined_at=user.created_at,
    )
