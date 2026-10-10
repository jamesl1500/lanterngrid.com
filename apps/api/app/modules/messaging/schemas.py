import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field

from app.modules.users.schemas import UserSummary

ConversationKind = Literal["dm", "group"]

MAX_MESSAGE_LENGTH = 4000
MAX_GROUP_SIZE = 20


def _trim(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _trim_or_none(value: object) -> object:
    return (value.strip() or None) if isinstance(value, str) else value


Username = Annotated[str, Field(min_length=1, max_length=40)]


class ConversationCreate(BaseModel):
    """One username starts (or reopens) a DM; more start a group."""

    usernames: Annotated[list[Username], Field(min_length=1, max_length=MAX_GROUP_SIZE - 1)]
    title: Annotated[
        Annotated[str, Field(max_length=80)] | None, BeforeValidator(_trim_or_none)
    ] = None


class MembersAdd(BaseModel):
    usernames: Annotated[list[Username], Field(min_length=1, max_length=MAX_GROUP_SIZE - 1)]


class MessageCreate(BaseModel):
    body: Annotated[str, BeforeValidator(_trim), Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)]
    # Made up by the sender (a UUID works). Sending again with the same one returns the
    # message from the first try, so retries never post twice.
    client_id: Annotated[str, Field(min_length=1, max_length=64)]


class MessageOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    # Null if the sender deleted their account.
    sender: UserSummary | None
    body: str
    client_id: str
    created_at: datetime


class MessagePage(BaseModel):
    """Oldest first."""

    items: list[MessageOut]
    # Pass as `before` for older messages; null at the start of the conversation.
    older_cursor: uuid.UUID | None


class MemberOut(BaseModel):
    user: UserSummary
    role: Literal["owner", "member"]
    # Read receipts: everything up to this message has been read.
    last_read_message_id: uuid.UUID | None


class ConversationOut(BaseModel):
    id: uuid.UUID
    kind: ConversationKind
    # The group's title, or null (show the other members' names).
    title: str | None
    # Everyone in it, including the viewer.
    members: list[MemberOut]
    last_message: MessageOut | None
    unread_count: int
    last_message_at: datetime
    created_at: datetime


class ConversationPage(BaseModel):
    """Most recently active first."""

    items: list[ConversationOut]
    next_cursor: str | None


class UnreadCount(BaseModel):
    # Conversations with messages the viewer hasn't read.
    conversations: int


class ReadIn(BaseModel):
    message_id: uuid.UUID
