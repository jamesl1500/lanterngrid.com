import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import ColumnElement, Select, and_, delete, func, insert, or_, select, true
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import Storage, public_url
from app.modules.media import service as media
from app.modules.notifications import service as notifications
from app.modules.posts import text
from app.modules.posts.models import (
    Achievement,
    Comment,
    Mention,
    Post,
    PostImage,
    PostTag,
    Reaction,
)
from app.modules.posts.schemas import (
    EMPTY_POST,
    REACTION_KINDS,
    AchievementIn,
    AchievementOut,
    CommentCreate,
    CommentOut,
    CommentPage,
    PostCreate,
    PostImageIn,
    PostImageOut,
    PostOut,
    PostPage,
    PostReactions,
    PostUpdate,
    ReactionCount,
    ReactionKind,
)
from app.modules.repos import service as repos
from app.modules.snippets import service as snippets
from app.modules.social import service as social
from app.modules.tags import service as tags
from app.modules.tags.models import Tag
from app.modules.tags.schemas import TagOut
from app.modules.users.models import User
from app.modules.users.summary import summarize


class PostNotFoundError(Exception):
    pass


class CommentNotFoundError(Exception):
    pass


class EmptyPostError(Exception):
    pass


class ShareError(Exception):
    """The snippet or repo isn't yours, or the snippet is friends only while the post is public."""


def visible_to(viewer_id: uuid.UUID | None) -> ColumnElement[bool]:
    """Live posts this person may see (see social.can_see)."""
    return and_(
        Post.deleted_at.is_(None), social.can_see(viewer_id, Post.author_id, Post.visibility)
    )


def _comments_visible_to(viewer_id: uuid.UUID | None) -> ColumnElement[bool]:
    """Hide comments from people either side has blocked."""
    if viewer_id is None:
        return true()
    return ~social.blocked_either_way(viewer_id, Comment.author_id)


async def _reactions(
    db: AsyncSession, post_ids: list[uuid.UUID], viewer_id: uuid.UUID | None
) -> dict[uuid.UUID, list[ReactionCount]]:
    counts: dict[uuid.UUID, dict[str, int]] = defaultdict(dict)
    mine: set[tuple[uuid.UUID, str]] = set()
    if post_ids:
        for post_id, kind, count in await db.execute(
            select(Reaction.post_id, Reaction.kind, func.count())
            .where(Reaction.post_id.in_(post_ids))
            .group_by(Reaction.post_id, Reaction.kind)
        ):
            counts[post_id][kind] = count
        if viewer_id is not None:
            mine = set(
                (
                    await db.execute(
                        select(Reaction.post_id, Reaction.kind).where(
                            Reaction.post_id.in_(post_ids), Reaction.user_id == viewer_id
                        )
                    )
                )
                .tuples()
                .all()
            )
    return {
        post_id: [
            ReactionCount(kind=kind, count=counts[post_id][kind], mine=(post_id, kind) in mine)
            for kind in REACTION_KINDS
            if counts[post_id].get(kind)
        ]
        for post_id in post_ids
    }


async def _outs(
    db: AsyncSession, posts: Sequence[Post], viewer_id: uuid.UUID | None
) -> list[PostOut]:
    ids = [p.id for p in posts]
    tags_by_post: dict[uuid.UUID, list[TagOut]] = defaultdict(list)
    mentions_by_post: dict[uuid.UUID, list[str]] = defaultdict(list)
    images_by_post: dict[uuid.UUID, list[PostImageOut]] = defaultdict(list)
    comment_counts: dict[uuid.UUID, int] = {}
    achievements: dict[uuid.UUID, AchievementOut] = {}
    shared = await snippets.by_ids(db, viewer_id, [p.snippet_id for p in posts if p.snippet_id])
    shared_repos = await repos.by_ids(db, [p.repo_id for p in posts if p.repo_id])
    if ids:
        for a in await db.scalars(select(Achievement).where(Achievement.post_id.in_(ids))):
            achievements[a.post_id] = AchievementOut(type=a.type, title=a.title)
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
        for image in await db.scalars(
            select(PostImage).where(PostImage.post_id.in_(ids)).order_by(PostImage.position)
        ):
            images_by_post[image.post_id].append(
                PostImageOut(key=image.key, url=public_url(image.key) or "", alt=image.alt)
            )
        comment_counts = dict(
            (
                await db.execute(
                    select(Comment.post_id, func.count())
                    .where(Comment.post_id.in_(ids), _comments_visible_to(viewer_id))
                    .group_by(Comment.post_id)
                )
            )
            .tuples()
            .all()
        )
    reactions = await _reactions(db, ids, viewer_id)
    return [
        PostOut(
            id=p.id,
            kind=p.kind,
            author=summarize(p.author),
            body_md=p.body_md,
            visibility=p.visibility,
            tags=tags_by_post[p.id],
            mentions=mentions_by_post[p.id],
            images=images_by_post[p.id],
            snippet=snippets.to_out(shared[p.snippet_id]) if p.snippet_id in shared else None,
            repo=repos.to_out(shared_repos[p.repo_id]) if p.repo_id in shared_repos else None,
            achievement=achievements.get(p.id),
            reactions=reactions[p.id],
            comment_count=comment_counts.get(p.id, 0),
            created_at=p.created_at,
            edited_at=p.edited_at,
        )
        for p in posts
    ]


async def _page(
    db: AsyncSession,
    stmt: Select[tuple[Post]],
    viewer: User | None,
    *,
    cursor: uuid.UUID | None,
    limit: int,
) -> PostPage:
    if cursor is not None:
        stmt = stmt.where(Post.id < cursor)
    posts = list(await db.scalars(stmt.order_by(Post.id.desc()).limit(limit + 1)))
    more = len(posts) > limit
    posts = posts[:limit]
    return PostPage(
        items=await _outs(db, posts, viewer.id if viewer else None),
        next_cursor=posts[-1].id if more else None,
    )


async def _sync_tags(db: AsyncSession, post: Post) -> None:
    found = await tags.ensure_tags(db, text.hashtags(post.body_md))
    await db.execute(delete(PostTag).where(PostTag.post_id == post.id))
    if found:
        await db.execute(insert(PostTag), [{"post_id": post.id, "tag_id": t.id} for t in found])


async def _sync_images(
    db: AsyncSession, storage: Storage, post: Post, images: list[PostImageIn]
) -> list[str]:
    """Replace the post's images; returns keys no longer used, to delete after committing."""
    current = {
        i.key: i for i in await db.scalars(select(PostImage).where(PostImage.post_id == post.id))
    }
    keys = [i.key for i in images]
    added = [key for key in keys if key not in current]
    if len(set(keys)) != len(keys):
        raise media.UploadNotFoundError
    # Each file belongs to one post, so deleting a post can delete its files.
    if added and await db.scalar(select(PostImage.key).where(PostImage.key.in_(added)).limit(1)):
        raise media.UploadNotFoundError
    for key in added:
        await media.check_upload(storage, "post", post.author_id, key)
    await db.execute(delete(PostImage).where(PostImage.post_id == post.id))
    if images:
        await db.execute(
            insert(PostImage),
            [
                {"post_id": post.id, "position": n, "key": i.key, "alt": i.alt}
                for n, i in enumerate(images)
            ],
        )
    return [key for key in current if key not in keys]


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


async def _check_snippet(
    db: AsyncSession, author: User, snippet_id: uuid.UUID, visibility: str
) -> None:
    try:
        snippet = await snippets.own(db, author, snippet_id)
    except snippets.SnippetNotFoundError:
        raise ShareError("You can only share your own snippets.") from None
    if snippet.visibility == "friends" and visibility == "public":
        raise ShareError("That snippet is friends only, so the post has to be too.")


async def _set_achievement(db: AsyncSession, post: Post, achievement: AchievementIn) -> None:
    await db.merge(Achievement(post_id=post.id, type=achievement.type, title=achievement.title))


async def create(db: AsyncSession, storage: Storage, author: User, data: PostCreate) -> PostOut:
    kind = "update"
    if data.snippet_id is not None:
        await _check_snippet(db, author, data.snippet_id, data.visibility)
        kind = "snippet"
    elif data.repo_id is not None:
        try:
            await repos.own(db, author, data.repo_id)
        except repos.RepoNotFoundError:
            raise ShareError("You can only share repos on your profile.") from None
        kind = "repo"
    elif data.achievement is not None:
        kind = "achievement"
    post = Post(
        author_id=author.id,
        kind=kind,
        body_md=data.body_md,
        visibility=data.visibility,
        snippet_id=data.snippet_id,
        repo_id=data.repo_id,
    )
    db.add(post)
    await db.flush()
    if data.achievement is not None:
        await _set_achievement(db, post, data.achievement)
    await _sync_images(db, storage, post, data.images)
    await _sync_tags(db, post)
    await _sync_mentions(db, post)
    await db.commit()
    await db.refresh(post)
    return (await _outs(db, [post], author.id))[0]


async def _visible_post(db: AsyncSession, viewer_id: uuid.UUID | None, post_id: uuid.UUID) -> Post:
    post = (
        await db.execute(select(Post).where(Post.id == post_id, visible_to(viewer_id)))
    ).scalar_one_or_none()
    if post is None:
        raise PostNotFoundError
    return post


async def get(db: AsyncSession, viewer: User | None, post_id: uuid.UUID) -> PostOut:
    viewer_id = viewer.id if viewer else None
    return (await _outs(db, [await _visible_post(db, viewer_id, post_id)], viewer_id))[0]


async def _own(db: AsyncSession, author: User, post_id: uuid.UUID) -> Post:
    post = await db.get(Post, post_id)
    if post is None or post.deleted_at is not None or post.author_id != author.id:
        raise PostNotFoundError
    return post


async def update(
    db: AsyncSession, storage: Storage, author: User, post_id: uuid.UUID, data: PostUpdate
) -> PostOut:
    post = await _own(db, author, post_id)
    if data.body_md is not None and data.body_md != post.body_md:
        post.body_md = data.body_md
        post.edited_at = datetime.now(UTC)
    if data.visibility is not None:
        if post.snippet_id is not None:
            await _check_snippet(db, author, post.snippet_id, data.visibility)
        post.visibility = data.visibility
    if data.achievement is not None and post.kind == "achievement":
        await _set_achievement(db, post, data.achievement)
    unused: list[str] = []
    if data.images is not None:
        unused = await _sync_images(db, storage, post, data.images)
    has_images = await db.scalar(
        select(func.count()).select_from(PostImage).where(PostImage.post_id == post.id)
    )
    if not post.body_md and not has_images and post.kind == "update":
        await db.rollback()
        raise EmptyPostError(EMPTY_POST)
    await _sync_tags(db, post)
    await _sync_mentions(db, post)
    await db.commit()
    for key in unused:
        await media.discard(storage, key)
    await db.refresh(post)
    return (await _outs(db, [post], author.id))[0]


async def remove(db: AsyncSession, storage: Storage, author: User, post_id: uuid.UUID) -> None:
    post = await _own(db, author, post_id)
    post.deleted_at = datetime.now(UTC)
    keys = list(await db.scalars(select(PostImage.key).where(PostImage.post_id == post.id)))
    await db.execute(delete(PostImage).where(PostImage.post_id == post.id))
    await notifications.withdraw(db, post.id)
    await notifications.withdraw_many(db, select(Comment.id).where(Comment.post_id == post.id))
    await db.commit()
    for key in keys:
        await media.discard(storage, key)


def _visible(viewer: User | None) -> Select[tuple[Post]]:
    return select(Post).where(visible_to(viewer.id if viewer else None))


async def feed(db: AsyncSession, viewer: User, *, cursor: uuid.UUID | None, limit: int) -> PostPage:
    """Your posts and your friends', newest first."""
    stmt = _visible(viewer).where(
        or_(Post.author_id == viewer.id, Post.author_id.in_(social.friend_ids_of(viewer.id)))
    )
    return await _page(db, stmt, viewer, cursor=cursor, limit=limit)


async def explore(
    db: AsyncSession, viewer: User | None, *, cursor: uuid.UUID | None, limit: int
) -> PostPage:
    """Everyone's public posts, newest first."""
    stmt = _visible(viewer).where(Post.visibility == "public")
    return await _page(db, stmt, viewer, cursor=cursor, limit=limit)


async def by_tag(
    db: AsyncSession, viewer: User | None, tag: Tag, *, cursor: uuid.UUID | None, limit: int
) -> PostPage:
    stmt = _visible(viewer).where(
        Post.id.in_(select(PostTag.post_id).where(PostTag.tag_id == tag.id))
    )
    return await _page(db, stmt, viewer, cursor=cursor, limit=limit)


async def by_author(
    db: AsyncSession, viewer: User | None, author: User, *, cursor: uuid.UUID | None, limit: int
) -> PostPage:
    stmt = _visible(viewer).where(Post.author_id == author.id)
    return await _page(db, stmt, viewer, cursor=cursor, limit=limit)


async def react(
    db: AsyncSession, user: User, post_id: uuid.UUID, kind: ReactionKind, on: bool
) -> PostReactions:
    """Add (on) or remove a reaction. Both are idempotent."""
    await _visible_post(db, user.id, post_id)
    if on:
        await db.execute(
            pg_insert(Reaction)
            .values(post_id=post_id, user_id=user.id, kind=kind)
            .on_conflict_do_nothing()
        )
    else:
        await db.execute(
            delete(Reaction).where(
                Reaction.post_id == post_id, Reaction.user_id == user.id, Reaction.kind == kind
            )
        )
    await db.commit()
    return PostReactions(reactions=(await _reactions(db, [post_id], user.id))[post_id])


async def _comment_outs(db: AsyncSession, comments: Sequence[Comment]) -> list[CommentOut]:
    # Link @names that belong to someone; comments don't record mentions like posts do.
    wanted = {c.id: text.mentions(c.body_md) for c in comments}
    names = {n for found in wanted.values() for n in found}
    existing: set[str] = set()
    if names:
        existing = {
            str(u).lower()
            for u in await db.scalars(select(User.username).where(User.username.in_(names)))
        }
    return [
        CommentOut(
            id=c.id,
            post_id=c.post_id,
            author=summarize(c.author),
            body_md=c.body_md,
            mentions=[n for n in wanted[c.id] if n in existing],
            created_at=c.created_at,
        )
        for c in comments
    ]


async def comments(
    db: AsyncSession,
    viewer: User | None,
    post_id: uuid.UUID,
    *,
    cursor: uuid.UUID | None,
    limit: int,
) -> CommentPage:
    viewer_id = viewer.id if viewer else None
    await _visible_post(db, viewer_id, post_id)
    stmt = select(Comment).where(Comment.post_id == post_id, _comments_visible_to(viewer_id))
    if cursor is not None:
        stmt = stmt.where(Comment.id > cursor)
    rows = list(await db.scalars(stmt.order_by(Comment.id).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    return CommentPage(
        items=await _comment_outs(db, rows), next_cursor=rows[-1].id if more else None
    )


async def _can_see(db: AsyncSession, user_id: uuid.UUID, post_id: uuid.UUID) -> bool:
    found = await db.scalar(select(Post.id).where(Post.id == post_id, visible_to(user_id)))
    return found is not None


async def add_comment(
    db: AsyncSession, author: User, post_id: uuid.UUID, data: CommentCreate
) -> CommentOut:
    post = await _visible_post(db, author.id, post_id)
    comment = Comment(post_id=post.id, author_id=author.id, body_md=data.body_md)
    db.add(comment)
    await db.flush()
    notified = {author.id}
    if post.author_id not in notified:
        notifications.notify(
            db, user_id=post.author_id, kind="comment", actor_id=author.id, subject_id=comment.id
        )
        notified.add(post.author_id)
    usernames = text.mentions(data.body_md)
    if usernames:
        for user_id in await db.scalars(
            select(User.id).where(
                User.username.in_(usernames), ~social.blocked_either_way(author.id, User.id)
            )
        ):
            if user_id not in notified and await _can_see(db, user_id, post.id):
                notifications.notify(
                    db, user_id=user_id, kind="mention", actor_id=author.id, subject_id=comment.id
                )
                notified.add(user_id)
    await db.commit()
    await db.refresh(comment)
    return (await _comment_outs(db, [comment]))[0]


async def remove_comment(db: AsyncSession, user: User, comment_id: uuid.UUID) -> None:
    """Commenters can delete their comments, and authors any comment on their posts."""
    row = (
        await db.execute(
            select(Comment, Post.author_id)
            .join(Post, Post.id == Comment.post_id)
            .where(Comment.id == comment_id, visible_to(user.id))
        )
    ).first()
    if row is None or user.id not in (row[0].author_id, row[1]):
        raise CommentNotFoundError
    await db.delete(row[0])
    await notifications.withdraw(db, comment_id)
    await db.commit()
