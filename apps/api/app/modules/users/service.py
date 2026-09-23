from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.modules.users.schemas import (
    OnboardingRequest,
    ProfileUpdate,
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
