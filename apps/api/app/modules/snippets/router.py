import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.core.db import SessionDep
from app.core.rate_limit import allow
from app.modules.auth.deps import MemberDep, OptionalUserDep
from app.modules.snippets import service
from app.modules.snippets.schemas import (
    MAX_PINS,
    PinIn,
    Pins,
    PinType,
    SnippetCreate,
    SnippetOut,
    SnippetPage,
    SnippetUpdate,
)
from app.modules.social import service as social
from app.modules.users import service as users
from app.modules.users.models import User

router = APIRouter(tags=["snippets"])

NOT_FOUND = "That snippet doesn't exist or you can't see it."


async def _person(db: SessionDep, username: str, viewer: User | None) -> User:
    person = await users.get_by_username(db, username)
    if (
        person is None
        or person.username is None
        or (viewer is not None and await social.has_blocked(db, person.id, viewer.id))
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No one here by that name.")
    return person


@router.post("/snippets", operation_id="createSnippet", status_code=status.HTTP_201_CREATED)
async def create_snippet(data: SnippetCreate, user: MemberDep, db: SessionDep) -> SnippetOut:
    if not await allow(f"snippet:{user.id}", limit=30, window_seconds=3600):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "That's a lot of snippets for one hour. Try later."
        )
    return await service.create(db, user, data)


@router.get("/snippets/{snippet_id}", operation_id="getSnippet")
async def get_snippet(snippet_id: uuid.UUID, viewer: OptionalUserDep, db: SessionDep) -> SnippetOut:
    try:
        return service.to_out(await service.visible(db, viewer.id if viewer else None, snippet_id))
    except service.SnippetNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None


@router.patch("/snippets/{snippet_id}", operation_id="updateSnippet")
async def update_snippet(
    snippet_id: uuid.UUID, data: SnippetUpdate, user: MemberDep, db: SessionDep
) -> SnippetOut:
    try:
        return await service.update(db, user, snippet_id, data)
    except service.SnippetNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None


@router.delete(
    "/snippets/{snippet_id}",
    operation_id="deleteSnippet",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_snippet(snippet_id: uuid.UUID, user: MemberDep, db: SessionDep) -> None:
    try:
        await service.remove(db, user, snippet_id)
    except service.SnippetNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None


@router.get("/users/{username}/snippets", operation_id="listUserSnippets")
async def list_user_snippets(
    username: str,
    viewer: OptionalUserDep,
    db: SessionDep,
    cursor: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> SnippetPage:
    owner = await _person(db, username, viewer)
    return await service.by_owner(db, viewer, owner, cursor=cursor, limit=limit)


@router.get("/users/{username}/pins", operation_id="listPins")
async def list_pins(username: str, viewer: OptionalUserDep, db: SessionDep) -> Pins:
    return await service.pins(db, viewer, await _person(db, username, viewer))


@router.put("/me/pins/{type}/{item_id}", operation_id="pinItem")
async def pin_item(type: PinType, item_id: uuid.UUID, user: MemberDep, db: SessionDep) -> Pins:
    try:
        return await service.pin(db, user, PinIn(type=type, id=item_id))
    except service.SnippetNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None
    except service.TooManyPinsError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"You can pin up to {MAX_PINS} things. Unpin one first.",
        ) from None


@router.delete("/me/pins/{type}/{item_id}", operation_id="unpinItem")
async def unpin_item(type: PinType, item_id: uuid.UUID, user: MemberDep, db: SessionDep) -> Pins:
    return await service.unpin(db, user, PinIn(type=type, id=item_id))
