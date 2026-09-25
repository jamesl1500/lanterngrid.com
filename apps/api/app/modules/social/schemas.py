import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.modules.users.schemas import UserSummary

RequestDirection = Literal["incoming", "outgoing"]


class FriendRequestCreate(BaseModel):
    username: str


class FriendRequestOut(BaseModel):
    id: uuid.UUID
    status: Literal["pending", "accepted", "declined", "cancelled"]
    # The other person: the sender for incoming requests, the recipient for outgoing ones.
    user: UserSummary
    created_at: datetime


class UserPage(BaseModel):
    items: list[UserSummary]
    next_cursor: uuid.UUID | None


class FriendRequestPage(BaseModel):
    items: list[FriendRequestOut]
    next_cursor: uuid.UUID | None
