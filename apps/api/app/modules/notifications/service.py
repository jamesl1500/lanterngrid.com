import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import (
    NotificationKind,
    NotificationOut,
    NotificationPage,
)
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


async def page(
    db: AsyncSession, user_id: uuid.UUID, *, cursor: uuid.UUID | None, limit: int
) -> NotificationPage:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if cursor is not None:
        stmt = stmt.where(Notification.id < cursor)
    rows = list(await db.scalars(stmt.order_by(Notification.id.desc()).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    return NotificationPage(
        items=[
            NotificationOut(
                id=n.id,
                kind=n.kind,
                actor=summarize(n.actor),
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
