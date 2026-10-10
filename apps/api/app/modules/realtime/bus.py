"""Fan events out to people's open sockets, on whichever API instance holds them."""

import json
import uuid
from collections.abc import Iterable
from typing import Any

from app.core.redis import redis


def channel(user_id: uuid.UUID) -> str:
    return f"rt:user:{user_id}"


async def publish(user_ids: Iterable[uuid.UUID], event: dict[str, Any]) -> None:
    """Send one event to everyone in `user_ids`. Call after the change is committed."""
    data = json.dumps(event, default=str)
    async with redis.pipeline(transaction=False) as pipe:
        for user_id in set(user_ids):
            pipe.publish(channel(user_id), data)
        await pipe.execute()
