"""Fan events out to people's open sockets, on whichever API instance holds them."""

import asyncio
import json
import uuid
from collections.abc import Iterable
from typing import Any

from sqlalchemy import event as sa_event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.redis import redis

_PENDING = "realtime_pending"
# Publishes started after a commit; kept so they aren't garbage collected mid-flight.
_in_flight: set[asyncio.Task[None]] = set()


def channel(user_id: uuid.UUID) -> str:
    return f"rt:user:{user_id}"


async def publish(user_ids: Iterable[uuid.UUID], event: dict[str, Any]) -> None:
    """Send one event to everyone in `user_ids`. Call after the change is committed."""
    data = json.dumps(event, default=str)
    async with redis.pipeline(transaction=False) as pipe:
        for user_id in set(user_ids):
            pipe.publish(channel(user_id), data)
        await pipe.execute()


def publish_after_commit(
    db: AsyncSession, user_ids: Iterable[uuid.UUID], event: dict[str, Any]
) -> None:
    """Send the event once `db` commits, or never if it rolls back. For code that changes
    things inside someone else's transaction, like queuing a notification."""
    db.sync_session.info.setdefault(_PENDING, []).append((list(user_ids), event))


async def _publish_all(pending: list[tuple[list[uuid.UUID], dict[str, Any]]]) -> None:
    for user_ids, event in pending:
        await publish(user_ids, event)


@sa_event.listens_for(Session, "after_commit")
def _send_pending(session: Session) -> None:
    pending = session.info.pop(_PENDING, None)
    if pending:
        task = asyncio.get_running_loop().create_task(_publish_all(pending))
        _in_flight.add(task)
        task.add_done_callback(_in_flight.discard)


@sa_event.listens_for(Session, "after_rollback")
def _drop_pending(session: Session) -> None:
    session.info.pop(_PENDING, None)


async def drain() -> None:
    """Wait for publishes started by recent commits (tests use this)."""
    while _in_flight:
        await asyncio.gather(*list(_in_flight))
