import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import ColumnElement, Select, and_, delete, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications import service as notifications
from app.modules.posts import text
from app.modules.posts.models import Mention, Post, PostTag
from app.modules.posts.schemas import PostCreate, PostOut, PostPage, PostUpdate
from app.modules.social import service as social
from app.modules.tags import service as tags
from app.modules.tags.models import Tag
from app.modules.tags.schemas import TagOut
from app.modules.users.models import User
from app.modules.users.summary import summarize


class PostNotFoundError(Exception):
    pass


def visible_to(viewer_id: uuid.UUID | None) -> ColumnElement[bool]:
    """Posts this person may see: public ones, their own, and their friends' friends-only ones,
    minus anything from people either side has blocked."""
    live = Post.deleted_at.is_(None)
    if viewer_id is None:
        return and_(live, Post.visibility == "public")
    return and_(
        live,
        ~social.blocked_either_way(viewer_id, Post.author_id),
        or_(
            Post.visibility == "public",
            Post.author_id == viewer_id,
            Post.author_id.in_(social.friend_ids_of(viewer_id)),
        ),
    )


async def _outs(db: AsyncSession, posts: Sequence[Post]) -> list[PostOut]:
    ids = [p.id for p in posts]
    tags_by_post: dict[uuid.UUID, list[TagOut]] = defaultdict(list)
    mentions_by_post: dict[uuid.UUID, list[str]] = defaultdict(list)
    if ids:
        for post_id, tag in await db.execute(
            select(PostTag.post_id, Tag)
            .join(Tag, Tag.id == PostTag.tag_id)
            .where(PostTag.post_id.in_(ids))
            .order_by(Tag.slug)
        ):
            tags_by_post[post_id].append(tags.to_out(tag))
        for post_id, username in await db.execute(
            select(Mention.post_id, User.username)
            .join(User, User.id == Mention.user_id)
            .where(Mention.post_id.in_(ids))
        ):
            mentions_by_post[post_id].append(str(username))
    return [
        PostOut(
            id=p.id,
            kind=p.kind,
            author=summarize(p.author),
            body_md=p.body_md,
            visibility=p.visibility,
            tags=tags_by_post[p.id],
            mentions=mentions_by_post[p.id],
            created_at=p.created_at,
            edited_at=p.edited_at,
        )
        for p in posts
    ]


async def _page(
    db: AsyncSession, stmt: Select[tuple[Post]], *, cursor: uuid.UUID | None, limit: int
) -> PostPage:
    if cursor is not None:
        stmt = stmt.where(Post.id < cursor)
    posts = list(await db.scalars(stmt.order_by(Post.id.desc()).limit(limit + 1)))
    more = len(posts) > limit
    posts = posts[:limit]
    return PostPage(items=await _outs(db, posts), next_cursor=posts[-1].id if more else None)


async def _sync_tags(db: AsyncSession, post: Post) -> None:
    found = await tags.ensure_tags(db, text.hashtags(post.body_md))
    await db.execute(delete(PostTag).where(PostTag.post_id == post.id))
    if found:
        await db.execute(insert(PostTag), [{"post_id": post.id, "tag_id": t.id} for t in found])


async def _sync_mentions(db: AsyncSession, post: Post) -> None:
    """Record who the post mentions and notify anyone newly mentioned who can see it."""
    before = set(await db.scalars(select(Mention.user_id).where(Mention.post_id == post.id)))
    usernames = text.mentions(post.body_md)
    people: list[uuid.UUID] = []
    if usernames:
        stmt = select(User.id).where(
            User.username.in_(usernames),  # citext, so case doesn't matter
            User.id != post.author_id,
            ~social.blocked_either_way(post.author_id, User.id),
        )
        if post.visibility == "friends":
            stmt = stmt.where(User.id.in_(social.friend_ids_of(post.author_id)))
        people = list(await db.scalars(stmt))
    await db.execute(delete(Mention).where(Mention.post_id == post.id))
    if people:
        await db.execute(insert(Mention), [{"post_id": post.id, "user_id": u} for u in people])
    for user_id in people:
        if user_id not in before:
            notifications.notify(
                db, user_id=user_id, kind="mention", actor_id=post.author_id, subject_id=post.id
            )


async def create(db: AsyncSession, author: User, data: PostCreate) -> PostOut:
    post = Post(author_id=author.id, body_md=data.body_md, visibility=data.visibility)
    db.add(post)
    await db.flush()
    await _sync_tags(db, post)
    await _sync_mentions(db, post)
    await db.commit()
    await db.refresh(post)
    return (await _outs(db, [post]))[0]


async def get(db: AsyncSession, viewer: User | None, post_id: uuid.UUID) -> PostOut:
    post = (
        await db.execute(
            select(Post).where(Post.id == post_id, visible_to(viewer.id if viewer else None))
        )
    ).scalar_one_or_none()
    if post is None:
        raise PostNotFoundError
    return (await _outs(db, [post]))[0]


async def _own(db: AsyncSession, author: User, post_id: uuid.UUID) -> Post:
    post = await db.get(Post, post_id)
    if post is None or post.deleted_at is not None or post.author_id != author.id:
        raise PostNotFoundError
    return post


async def update(db: AsyncSession, author: User, post_id: uuid.UUID, data: PostUpdate) -> PostOut:
    post = await _own(db, author, post_id)
    if data.body_md is not None and data.body_md != post.body_md:
        post.body_md = data.body_md
        post.edited_at = datetime.now(UTC)
    if data.visibility is not None:
        post.visibility = data.visibility
    await _sync_tags(db, post)
    await _sync_mentions(db, post)
    await db.commit()
    await db.refresh(post)
    return (await _outs(db, [post]))[0]


async def remove(db: AsyncSession, author: User, post_id: uuid.UUID) -> None:
    post = await _own(db, author, post_id)
    post.deleted_at = datetime.now(UTC)
    await notifications.withdraw(db, post.id)
    await db.commit()


def _visible(viewer: User | None) -> Select[tuple[Post]]:
    return select(Post).where(visible_to(viewer.id if viewer else None))


async def feed(db: AsyncSession, viewer: User, *, cursor: uuid.UUID | None, limit: int) -> PostPage:
    """Your posts and your friends', newest first."""
    stmt = _visible(viewer).where(
        or_(Post.author_id == viewer.id, Post.author_id.in_(social.friend_ids_of(viewer.id)))
    )
    return await _page(db, stmt, cursor=cursor, limit=limit)


async def explore(
    db: AsyncSession, viewer: User | None, *, cursor: uuid.UUID | None, limit: int
) -> PostPage:
    """Everyone's public posts, newest first."""
    stmt = _visible(viewer).where(Post.visibility == "public")
    return await _page(db, stmt, cursor=cursor, limit=limit)


async def by_tag(
    db: AsyncSession, viewer: User | None, tag: Tag, *, cursor: uuid.UUID | None, limit: int
) -> PostPage:
    stmt = _visible(viewer).where(
        Post.id.in_(select(PostTag.post_id).where(PostTag.tag_id == tag.id))
    )
    return await _page(db, stmt, cursor=cursor, limit=limit)


async def by_author(
    db: AsyncSession, viewer: User | None, author: User, *, cursor: uuid.UUID | None, limit: int
) -> PostPage:
    stmt = _visible(viewer).where(Post.author_id == author.id)
    return await _page(db, stmt, cursor=cursor, limit=limit)
