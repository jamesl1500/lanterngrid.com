import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.core.db import SessionDep
from app.core.rate_limit import allow
from app.core.storage import StorageDep
from app.modules.auth.deps import MemberDep, OptionalUserDep
from app.modules.media import service as media
from app.modules.posts import service
from app.modules.posts.schemas import (
    CommentCreate,
    CommentOut,
    CommentPage,
    PostCreate,
    PostOut,
    PostPage,
    PostReactions,
    PostUpdate,
    ReactionKind,
)
from app.modules.social import service as social
from app.modules.tags import service as tags
from app.modules.users import service as users

router = APIRouter(tags=["posts"])

Limit = Annotated[int, Query(ge=1, le=50)]
NOT_FOUND = "That post doesn't exist or you can't see it."
BAD_IMAGE = "One of those images didn't upload properly, or is too large. Try adding it again."


@contextmanager
def _post_errors() -> Iterator[None]:
    try:
        yield
    except service.PostNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None
    except (media.UploadNotFoundError, media.UploadRejectedError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, BAD_IMAGE) from None
    except service.EmptyPostError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from None


@router.post("/posts", operation_id="createPost", status_code=status.HTTP_201_CREATED)
async def create_post(
    data: PostCreate, user: MemberDep, db: SessionDep, storage: StorageDep
) -> PostOut:
    if not await allow(f"post:{user.id}", limit=30, window_seconds=3600):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "That's a lot of posts for one hour. Try later."
        )
    with _post_errors():
        return await service.create(db, storage, user, data)


@router.get("/posts/{post_id}", operation_id="getPost")
async def get_post(post_id: uuid.UUID, viewer: OptionalUserDep, db: SessionDep) -> PostOut:
    with _post_errors():
        return await service.get(db, viewer, post_id)


@router.patch("/posts/{post_id}", operation_id="updatePost")
async def update_post(
    post_id: uuid.UUID, data: PostUpdate, user: MemberDep, db: SessionDep, storage: StorageDep
) -> PostOut:
    with _post_errors():
        return await service.update(db, storage, user, post_id, data)


@router.delete(
    "/posts/{post_id}",
    operation_id="deletePost",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_post(
    post_id: uuid.UUID, user: MemberDep, db: SessionDep, storage: StorageDep
) -> None:
    with _post_errors():
        await service.remove(db, storage, user, post_id)


@router.put("/posts/{post_id}/reactions/{kind}", operation_id="addReaction")
async def add_reaction(
    post_id: uuid.UUID, kind: ReactionKind, user: MemberDep, db: SessionDep
) -> PostReactions:
    with _post_errors():
        return await service.react(db, user, post_id, kind, on=True)


@router.delete("/posts/{post_id}/reactions/{kind}", operation_id="removeReaction")
async def remove_reaction(
    post_id: uuid.UUID, kind: ReactionKind, user: MemberDep, db: SessionDep
) -> PostReactions:
    with _post_errors():
        return await service.react(db, user, post_id, kind, on=False)


@router.get("/posts/{post_id}/comments", operation_id="listComments")
async def list_comments(
    post_id: uuid.UUID,
    viewer: OptionalUserDep,
    db: SessionDep,
    cursor: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> CommentPage:
    with _post_errors():
        return await service.comments(db, viewer, post_id, cursor=cursor, limit=limit)


@router.post(
    "/posts/{post_id}/comments", operation_id="createComment", status_code=status.HTTP_201_CREATED
)
async def create_comment(
    post_id: uuid.UUID, data: CommentCreate, user: MemberDep, db: SessionDep
) -> CommentOut:
    if not await allow(f"comment:{user.id}", limit=120, window_seconds=3600):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "That's a lot of comments for one hour. Try later."
        )
    with _post_errors():
        return await service.add_comment(db, user, post_id, data)


@router.delete(
    "/comments/{comment_id}",
    operation_id="deleteComment",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_comment(comment_id: uuid.UUID, user: MemberDep, db: SessionDep) -> None:
    try:
        await service.remove_comment(db, user, comment_id)
    except service.CommentNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "That comment doesn't exist or isn't yours to delete."
        ) from None


@router.get("/feed", operation_id="getFeed")
async def get_feed(
    user: MemberDep, db: SessionDep, cursor: uuid.UUID | None = None, limit: Limit = 20
) -> PostPage:
    return await service.feed(db, user, cursor=cursor, limit=limit)


@router.get("/explore", operation_id="getExplore")
async def get_explore(
    viewer: OptionalUserDep, db: SessionDep, cursor: uuid.UUID | None = None, limit: Limit = 20
) -> PostPage:
    return await service.explore(db, viewer, cursor=cursor, limit=limit)


@router.get("/tags/{slug}/posts", operation_id="listTagPosts")
async def list_tag_posts(
    slug: str,
    viewer: OptionalUserDep,
    db: SessionDep,
    cursor: uuid.UUID | None = None,
    limit: Limit = 20,
) -> PostPage:
    tag = await tags.get(db, slug)
    if tag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such tag.")
    return await service.by_tag(db, viewer, tag, cursor=cursor, limit=limit)


@router.get("/users/{username}/posts", operation_id="listUserPosts")
async def list_user_posts(
    username: str,
    viewer: OptionalUserDep,
    db: SessionDep,
    cursor: uuid.UUID | None = None,
    limit: Limit = 20,
) -> PostPage:
    author = await users.get_by_username(db, username)
    if (
        author is None
        or author.username is None
        or (viewer is not None and await social.has_blocked(db, author.id, viewer.id))
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No one here by that name.")
    return await service.by_author(db, viewer, author, cursor=cursor, limit=limit)
