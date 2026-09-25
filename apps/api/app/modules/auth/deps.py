from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.core.config import get_settings
from app.core.db import SessionDep
from app.modules.auth import service
from app.modules.users.models import User


async def get_optional_user(request: Request, db: SessionDep) -> User | None:
    token = request.cookies.get(get_settings().session_cookie_name)
    if not token:
        return None
    found = await service.user_for_session(db, token)
    return found[0] if found else None


async def get_current_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in to continue.")
    return user


OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_member(user: Annotated[User, Depends(get_current_user)]) -> User:
    """A signed-in person who has finished onboarding, so others can find and link to them."""
    if user.username is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Pick a username first.")
    return user


MemberDep = Annotated[User, Depends(get_member)]
