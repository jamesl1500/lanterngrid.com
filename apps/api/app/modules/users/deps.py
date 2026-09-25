from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.db import SessionDep
from app.modules.auth.deps import OptionalUserDep
from app.modules.social import service as social
from app.modules.users import service as users
from app.modules.users.models import User


async def profile_owner(username: str, viewer: OptionalUserDep, db: SessionDep) -> User:
    """The member a /users/{username}/... route is about. Hidden from people they blocked."""
    person = await users.get_by_username(db, username)
    if (
        person is None
        or person.username is None
        or (viewer is not None and await social.has_blocked(db, person.id, viewer.id))
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No one here by that name.")
    return person


ProfileOwnerDep = Annotated[User, Depends(profile_owner)]
