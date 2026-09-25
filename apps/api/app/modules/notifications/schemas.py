import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.modules.users.schemas import UserSummary

NotificationKind = Literal["friend_request", "friend_accepted"]


class NotificationOut(BaseModel):
    id: uuid.UUID
    kind: NotificationKind
    actor: UserSummary
    created_at: datetime
    read: bool


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    # Pass as `cursor` to get the next (older) page; null when there are no more.
    next_cursor: uuid.UUID | None


class UnreadCount(BaseModel):
    count: int


class MarkRead(BaseModel):
    """Mark everything up to and including `up_to` as read, or everything when it's null."""

    up_to: uuid.UUID | None = None
