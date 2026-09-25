import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.core.db import SessionDep
from app.core.rate_limit import allow
from app.modules.auth.deps import MemberDep
from app.modules.messaging import service
from app.modules.messaging.schemas import (
    MAX_GROUP_SIZE,
    ConversationCreate,
    ConversationOut,
    ConversationPage,
    MembersAdd,
    MessageCreate,
    MessageOut,
    MessagePage,
    ReadIn,
    UnreadCount,
)

router = APIRouter(tags=["messaging"])

NOT_FOUND = "That conversation doesn't exist or you're not in it."


def _people_error(e: Exception) -> HTTPException:
    if isinstance(e, service.UnknownPeopleError):
        names = ", ".join(f"@{u}" for u in e.usernames)
        return HTTPException(status.HTTP_400_BAD_REQUEST, f"No one here called {names}.")
    if isinstance(e, service.NotFriendsError):
        return HTTPException(
            status.HTTP_403_FORBIDDEN, f"You can only message friends, and @{e.username} isn't one."
        )
    return HTTPException(
        status.HTTP_400_BAD_REQUEST, f"A group can have up to {MAX_GROUP_SIZE} people."
    )


@router.post(
    "/conversations", operation_id="createConversation", status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    data: ConversationCreate, user: MemberDep, db: SessionDep
) -> ConversationOut:
    try:
        return await service.create(db, user, data)
    except (service.UnknownPeopleError, service.NotFriendsError, service.GroupFullError) as e:
        raise _people_error(e) from None


@router.get("/conversations", operation_id="listConversations")
async def list_conversations(
    user: MemberDep,
    db: SessionDep,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 30,
) -> ConversationPage:
    try:
        return await service.inbox(db, user, cursor=cursor, limit=limit)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That cursor isn't valid.") from None


@router.get("/conversations/unread-count", operation_id="getUnreadConversations")
async def unread_count(user: MemberDep, db: SessionDep) -> UnreadCount:
    return UnreadCount(conversations=await service.unread_conversations(db, user))


@router.get("/conversations/{conversation_id}", operation_id="getConversation")
async def get_conversation(
    conversation_id: uuid.UUID, user: MemberDep, db: SessionDep
) -> ConversationOut:
    try:
        return await service.get(db, user, conversation_id)
    except service.ConversationNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None


@router.get("/conversations/{conversation_id}/messages", operation_id="listMessages")
async def list_messages(
    conversation_id: uuid.UUID,
    user: MemberDep,
    db: SessionDep,
    before: uuid.UUID | None = None,
    after: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> MessagePage:
    try:
        return await service.messages(
            db, user, conversation_id, before=before, after=after, limit=limit
        )
    except service.ConversationNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None


@router.post(
    "/conversations/{conversation_id}/messages",
    operation_id="sendMessage",
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: uuid.UUID, data: MessageCreate, user: MemberDep, db: SessionDep
) -> MessageOut:
    if not await allow(f"message:{user.id}", limit=60, window_seconds=60):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "You're sending messages very fast. Slow down a bit."
        )
    try:
        return await service.send(db, user, conversation_id, data)
    except service.ConversationNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None
    except service.NotFriendsError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "You can only message people who are still your friends."
        ) from None


@router.post(
    "/conversations/{conversation_id}/read",
    operation_id="markConversationRead",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def mark_read(
    conversation_id: uuid.UUID, data: ReadIn, user: MemberDep, db: SessionDep
) -> None:
    try:
        await service.mark_read(db, user, conversation_id, data.message_id)
    except service.ConversationNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None


@router.post("/conversations/{conversation_id}/members", operation_id="addConversationMembers")
async def add_members(
    conversation_id: uuid.UUID, data: MembersAdd, user: MemberDep, db: SessionDep
) -> ConversationOut:
    try:
        return await service.add_members(db, user, conversation_id, data.usernames)
    except service.ConversationNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None
    except service.NotAGroupError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Start a group to add people.") from None
    except service.NotOwnerError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only the group's owner can add people."
        ) from None
    except (service.UnknownPeopleError, service.NotFriendsError, service.GroupFullError) as e:
        raise _people_error(e) from None


@router.delete(
    "/conversations/{conversation_id}/members/me",
    operation_id="leaveConversation",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def leave(conversation_id: uuid.UUID, user: MemberDep, db: SessionDep) -> None:
    try:
        await service.leave(db, user, conversation_id)
    except service.ConversationNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None
    except service.NotAGroupError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't leave a DM.") from None
