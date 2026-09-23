from fastapi import APIRouter, HTTPException, status

from app.core.db import SessionDep
from app.modules.auth.deps import CurrentUserDep
from app.modules.auth.service import build_me
from app.modules.users import service
from app.modules.users.schemas import (
    LinksUpdate,
    Me,
    OnboardingRequest,
    ProfileLinkOut,
    ProfileSettings,
    ProfileUpdate,
    PublicProfile,
    UsernameAvailability,
)

router = APIRouter(tags=["users"])


@router.get("/users/{username}", operation_id="getPublicProfile")
async def get_public_profile(username: str, db: SessionDep) -> PublicProfile:
    user = await service.get_by_username(db, username)
    if user is None or user.username is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No one here by that name.")
    return await service.public_profile(db, user)


@router.get("/usernames/{username}", operation_id="checkUsername")
async def check_username(username: str, db: SessionDep) -> UsernameAvailability:
    return await service.check_username(db, username)


@router.post("/me/onboarding", operation_id="completeOnboarding")
async def complete_onboarding(data: OnboardingRequest, user: CurrentUserDep, db: SessionDep) -> Me:
    if user.username is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "You've already picked a username.")
    try:
        await service.complete_onboarding(db, user, data)
    except service.UsernameTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "That username is taken.") from None
    return await build_me(db, user)


@router.get("/me/profile", operation_id="getMyProfile")
async def get_my_profile(user: CurrentUserDep, db: SessionDep) -> ProfileSettings:
    return await service.profile_settings(db, user)


@router.patch("/me/profile", operation_id="updateMyProfile")
async def update_my_profile(
    data: ProfileUpdate, user: CurrentUserDep, db: SessionDep
) -> ProfileSettings:
    return await service.profile_settings(db, await service.update_profile(db, user, data))


@router.put("/me/links", operation_id="setMyLinks")
async def set_my_links(
    data: LinksUpdate, user: CurrentUserDep, db: SessionDep
) -> list[ProfileLinkOut]:
    await service.set_links(db, user.id, data.links)
    return await service.links(db, user.id)
