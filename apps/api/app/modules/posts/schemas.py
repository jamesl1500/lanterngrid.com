import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field

from app.modules.tags.schemas import TagOut
from app.modules.users.schemas import UserSummary

PostKind = Literal["update"]
Visibility = Literal["public", "friends"]

MAX_POST_LENGTH = 5000


def _trim(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


Body = Annotated[
    str,
    BeforeValidator(_trim),
    Field(min_length=1, max_length=MAX_POST_LENGTH),
]


class PostCreate(BaseModel):
    body_md: Body
    visibility: Visibility = "public"


class PostUpdate(BaseModel):
    """Fields left out are unchanged."""

    body_md: Body | None = None
    visibility: Visibility | None = None


class PostOut(BaseModel):
    id: uuid.UUID
    kind: PostKind
    author: UserSummary
    body_md: str
    visibility: Visibility
    # Tags and people the body links to. Use these to turn #tag and @name into links.
    tags: list[TagOut]
    mentions: list[str]
    created_at: datetime
    edited_at: datetime | None


class PostPage(BaseModel):
    items: list[PostOut]
    next_cursor: uuid.UUID | None
