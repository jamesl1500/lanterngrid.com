import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import (
    NotificationKind,
    NotificationOut,
    NotificationPage,
)
from app.modules.posts.models import Comment
from app.modules.users.summary import summarize


def notify(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    kind: NotificationKind,
    actor_id: uuid.UUID,
    subject_id: uuid.UUID | None = None,
) -> None:
    """Queue a notification in the caller's transaction."""
    db.add(Notification(user_id=user_id, kind=kind, actor_id=actor_id, subject_id=subject_id))


def _post_id(n: Notification, comment_posts: dict[uuid.UUID, uuid.UUID]) -> uuid.UUID | None:
    if n.subject_id is None or n.kind not in ("comment", "mention"):
        return None
    return comment_posts.get(n.subject_id, n.subject_id if n.kind == "mention" else None)


async def page(
    db: AsyncSession, user_id: uuid.UUID, *, cursor: uuid.UUID | None, limit: int
) -> NotificationPage:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if cursor is not None:
        stmt = stmt.where(Notification.id < cursor)
    rows = list(await db.scalars(stmt.order_by(Notification.id.desc()).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    # Comment and mention subjects may be comments; link those to their post.
    subjects = [n.subject_id for n in rows if n.kind in ("comment", "mention") and n.subject_id]
    comment_posts: dict[uuid.UUID, uuid.UUID] = {}
    if subjects:
        comment_posts = dict(
            (await db.execute(select(Comment.id, Comment.post_id).where(Comment.id.in_(subjects))))
            .tuples()
            .all()
        )
    return NotificationPage(
        items=[
            NotificationOut(
                id=n.id,
                kind=n.kind,
                actor=summarize(n.actor),
                subject_id=n.subject_id,
                post_id=_post_id(n, comment_posts),
                created_at=n.created_at,
                read=n.read_at is not None,
            )
            for n in rows
        ],
        next_cursor=rows[-1].id if more else None,
    )


async def unread_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    count = await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
    )
    return count or 0


async def mark_read(db: AsyncSession, user_id: uuid.UUID, up_to: uuid.UUID | None = None) -> None:
    stmt = update(Notification).where(
        Notification.user_id == user_id, Notification.read_at.is_(None)
    )
    if up_to is not None:
        stmt = stmt.where(Notification.id <= up_to)
    await db.execute(stmt.values(read_at=datetime.now(UTC)))


async def mark_subject_read(db: AsyncSession, user_id: uuid.UUID, subject_id: uuid.UUID) -> None:
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.subject_id == subject_id,
            Notification.read_at.is_(None),
        )
        .values(read_at=datetime.now(UTC))
    )


async def withdraw(db: AsyncSession, subject_id: uuid.UUID) -> None:
    """Remove notifications about something that no longer applies, like a cancelled request."""
    await db.execute(delete(Notification).where(Notification.subject_id == subject_id))


async def withdraw_many(db: AsyncSession, subject_ids: Select[tuple[uuid.UUID]]) -> None:
    await db.execute(delete(Notification).where(Notification.subject_id.in_(subject_ids)))
