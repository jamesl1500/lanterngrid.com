import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.core.db import SessionDep
from app.core.rate_limit import allow
from app.modules.auth.deps import MemberDep
from app.modules.social import service
from app.modules.social.schemas import (
    FriendRequestCreate,
    FriendRequestOut,
    FriendRequestPage,
    RequestDirection,
    UserPage,
)
from app.modules.users import service as users
from app.modules.users.models import User
from app.modules.users.schemas import UserSummary
from app.modules.users.summary import summarize

router = APIRouter(tags=["social"])

NOT_FOUND = "No one here by that name."
Limit = Annotated[int, Query(ge=1, le=50)]


async def _person(db: SessionDep, username: str) -> User:
    user = await users.get_by_username(db, username)
    if user is None or user.username is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return user


@router.post("/friend-requests", operation_id="sendFriendRequest")
async def send_friend_request(
    data: FriendRequestCreate, user: MemberDep, db: SessionDep
) -> FriendRequestOut:
    if not await allow(f"friend-request:{user.id}", limit=50, window_seconds=86400):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "That's a lot of requests for one day. Try tomorrow."
        )
    other = await _person(db, data.username)
    try:
        return await service.send_request(db, user, other)
    except service.NotAllowedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "You can't send a friend request to this person."
        ) from None
    except service.AlreadyFriendsError:
        raise HTTPException(status.HTTP_409_CONFLICT, "You're already friends.") from None
    except service.TooSoonError:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "You asked recently. Try again in a few days."
        ) from None


@router.get("/me/friend-requests", operation_id="listFriendRequests")
async def list_friend_requests(
    user: MemberDep,
    db: SessionDep,
    direction: RequestDirection = "incoming",
    cursor: uuid.UUID | None = None,
    limit: Limit = 20,
) -> FriendRequestPage:
    return await service.requests(db, user.id, direction, cursor=cursor, limit=limit)


def _missing_request() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "That request is no longer open.")


@router.post("/friend-requests/{request_id}/accept", operation_id="acceptFriendRequest")
async def accept_friend_request(
    request_id: uuid.UUID, user: MemberDep, db: SessionDep
) -> FriendRequestOut:
    try:
        return await service.respond(db, user, request_id, accept=True)
    except service.NotFoundError:
        raise _missing_request() from None


@router.post("/friend-requests/{request_id}/decline", operation_id="declineFriendRequest")
async def decline_friend_request(
    request_id: uuid.UUID, user: MemberDep, db: SessionDep
) -> FriendRequestOut:
    try:
        return await service.respond(db, user, request_id, accept=False)
    except service.NotFoundError:
        raise _missing_request() from None


@router.post("/friend-requests/{request_id}/cancel", operation_id="cancelFriendRequest")
async def cancel_friend_request(
    request_id: uuid.UUID, user: MemberDep, db: SessionDep
) -> FriendRequestOut:
    try:
        return await service.cancel(db, user, request_id)
    except service.NotFoundError:
        raise _missing_request() from None


@router.get("/users/{username}/friends", operation_id="listFriends")
async def list_friends(
    username: str, db: SessionDep, cursor: uuid.UUID | None = None, limit: Limit = 24
) -> UserPage:
    person = await _person(db, username)
    return await service.friends(db, person.id, cursor=cursor, limit=limit)


@router.delete(
    "/me/friends/{username}",
    operation_id="removeFriend",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def remove_friend(username: str, user: MemberDep, db: SessionDep) -> None:
    try:
        await service.unfriend(db, user, await _person(db, username))
    except service.NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "You aren't friends.") from None


@router.get("/me/blocks", operation_id="listBlocks")
async def list_blocks(user: MemberDep, db: SessionDep) -> list[UserSummary]:
    return [summarize(u) for u in await service.blocked(db, user.id)]


@router.put(
    "/me/blocks/{username}",
    operation_id="blockUser",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def block_user(username: str, user: MemberDep, db: SessionDep) -> None:
    try:
        await service.block(db, user, await _person(db, username))
    except service.NotAllowedError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't block yourself.") from None


@router.delete(
    "/me/blocks/{username}",
    operation_id="unblockUser",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def unblock_user(username: str, user: MemberDep, db: SessionDep) -> None:
    await service.unblock(db, user, await _person(db, username))


@router.get("/people/search", operation_id="searchPeople")
async def search_people(
    user: MemberDep,
    db: SessionDep,
    q: Annotated[str, Query(max_length=50)] = "",
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
) -> list[UserSummary]:
    return [summarize(u) for u in await service.search_people(db, user, q, limit)]
