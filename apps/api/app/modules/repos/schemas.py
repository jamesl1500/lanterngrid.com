import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.modules.users.schemas import UserSummary

MAX_REPOS = 50


class RepoAdd(BaseModel):
    # owner/name or a github.com URL.
    repo: Annotated[str, Field(min_length=3, max_length=300)]


class RepoOut(BaseModel):
    id: uuid.UUID
    owner: UserSummary
    full_name: str
    url: str
    description: str | None
    homepage: str | None
    language: str | None
    stars: int
    forks: int
    open_issues: int
    topics: list[str]
    fork: bool
    archived: bool
    pushed_at: datetime | None
    # When the stats were last read from GitHub.
    fetched_at: datetime
    # GitHub can't find it any more (deleted or made private); the card says so.
    missing: bool
    created_at: datetime


class RepoPage(BaseModel):
    items: list[RepoOut]
    next_cursor: uuid.UUID | None
