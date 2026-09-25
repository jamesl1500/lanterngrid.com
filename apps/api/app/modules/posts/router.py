import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.core.db import SessionDep
from app.core.rate_limit import allow
from app.modules.auth.deps import MemberDep, OptionalUserDep
from app.modules.posts import service
from app.modules.posts.schemas import PostCreate, PostOut, PostPage, PostUpdate
from app.modules.social import service as social
from app.modules.tags import service as tags
from app.modules.users import service as users

router = APIRouter(tags=["posts"])

Limit = Annotated[int, Query(ge=1, le=50)]
NOT_FOUND = "That post doesn't exist or you can't see it."


@router.post("/posts", operation_id="createPost", status_code=status.HTTP_201_CREATED)
async def create_post(data: PostCreate, user: MemberDep, db: SessionDep) -> PostOut:
    if not await allow(f"post:{user.id}", limit=30, window_seconds=3600):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "That's a lot of posts for one hour. Try later."
        )
    return await service.create(db, user, data)


@router.get("/posts/{post_id}", operation_id="getPost")
async def get_post(post_id: uuid.UUID, viewer: OptionalUserDep, db: SessionDep) -> PostOut:
    try:
        return await service.get(db, viewer, post_id)
    except service.PostNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None


@router.patch("/posts/{post_id}", operation_id="updatePost")
async def update_post(
    post_id: uuid.UUID, data: PostUpdate, user: MemberDep, db: SessionDep
) -> PostOut:
    try:
        return await service.update(db, user, post_id, data)
    except service.PostNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None


@router.delete(
    "/posts/{post_id}",
    operation_id="deletePost",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_post(post_id: uuid.UUID, user: MemberDep, db: SessionDep) -> None:
    try:
        await service.remove(db, user, post_id)
    except service.PostNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND) from None


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
