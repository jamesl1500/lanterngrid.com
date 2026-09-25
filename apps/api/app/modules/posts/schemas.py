import uuid
from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, BeforeValidator, Field, model_validator

from app.modules.repos.schemas import RepoOut
from app.modules.snippets.schemas import SnippetOut
from app.modules.tags.schemas import TagOut
from app.modules.users.schemas import UserSummary

PostKind = Literal["update", "snippet", "repo", "achievement"]
AchievementType = Literal[
    "shipped", "launched", "promoted", "new_job", "certified", "first_oss_merge", "milestone"
]
Visibility = Literal["public", "friends"]

MAX_POST_LENGTH = 5000
MAX_COMMENT_LENGTH = 2000
MAX_IMAGES = 4

# In the order the web shows them.
ReactionKind = Literal["like", "ship", "love", "idea", "laugh", "eyes"]
REACTION_KINDS: tuple[ReactionKind, ...] = ("like", "ship", "love", "idea", "laugh", "eyes")


def _trim(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


# May be empty when the post has images.
Body = Annotated[str, BeforeValidator(_trim), Field(max_length=MAX_POST_LENGTH)]
CommentBody = Annotated[
    str, BeforeValidator(_trim), Field(min_length=1, max_length=MAX_COMMENT_LENGTH)
]
EMPTY_POST = "Write something or add an image."
ONE_ATTACHMENT = "A post can share one snippet, repo or achievement."


class PostImageIn(BaseModel):
    """An image uploaded with kind `post`."""

    key: str = Field(max_length=300)
    alt: Annotated[str, BeforeValidator(_trim), Field(max_length=300)] = ""


class AchievementIn(BaseModel):
    type: AchievementType
    title: Annotated[str, BeforeValidator(_trim), Field(min_length=1, max_length=100)]


class AchievementOut(BaseModel):
    type: AchievementType
    title: str


class PostCreate(BaseModel):
    body_md: Body = ""
    visibility: Visibility = "public"
    images: list[PostImageIn] = Field(default=[], max_length=MAX_IMAGES)
    # Share one of your snippets or repos, or celebrate something (an achievement post).
    snippet_id: uuid.UUID | None = None
    repo_id: uuid.UUID | None = None
    achievement: AchievementIn | None = None

    @model_validator(mode="after")
    def _check(self) -> Self:
        attached = [a for a in (self.snippet_id, self.repo_id, self.achievement) if a is not None]
        if len(attached) > 1:
            raise ValueError(ONE_ATTACHMENT)
        if not (self.body_md or self.images or attached):
            raise ValueError(EMPTY_POST)
        return self


class PostUpdate(BaseModel):
    """Fields left out are unchanged. `images` replaces the post's images."""

    body_md: Body | None = None
    visibility: Visibility | None = None
    images: list[PostImageIn] | None = Field(default=None, max_length=MAX_IMAGES)
    # Only for achievement posts.
    achievement: AchievementIn | None = None


class PostImageOut(BaseModel):
    key: str
    url: str
    alt: str


class ReactionCount(BaseModel):
    kind: ReactionKind
    count: int
    # Whether the viewer reacted with this.
    mine: bool


class PostReactions(BaseModel):
    reactions: list[ReactionCount]


class PostOut(BaseModel):
    id: uuid.UUID
    kind: PostKind
    author: UserSummary
    body_md: str
    visibility: Visibility
    # Tags and people the body links to. Use these to turn #tag and @name into links.
    tags: list[TagOut]
    mentions: list[str]
    images: list[PostImageOut]
    # The shared snippet, when the viewer can see it (null if it was deleted or hidden).
    snippet: SnippetOut | None
    # The shared repo (null if its owner removed it).
    repo: RepoOut | None
    achievement: AchievementOut | None
    # Only kinds someone used, in REACTION_KINDS order.
    reactions: list[ReactionCount]
    comment_count: int
    created_at: datetime
    edited_at: datetime | None


class PostPage(BaseModel):
    items: list[PostOut]
    next_cursor: uuid.UUID | None


class CommentCreate(BaseModel):
    body_md: CommentBody


class CommentOut(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    author: UserSummary
    body_md: str
    # People the body mentions who have an account, to link @name.
    mentions: list[str]
    created_at: datetime


class CommentPage(BaseModel):
    """Oldest first. Pass `next_cursor` as `cursor` for the next (newer) page."""

    items: list[CommentOut]
    next_cursor: uuid.UUID | None
