"""Fixed-window counters in Redis that slow down abuse.

`enforce` is the one most routes want: it counts an attempt and answers 429, with a
Retry-After header, once there have been too many.
"""

from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from app.core.redis import redis

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR


@dataclass(frozen=True)
class Rule:
    limit: int
    window_seconds: int
    # Shown to the person when they hit the limit.
    message: str


async def _count(key: str, window_seconds: int) -> tuple[int, int]:
    """Count one attempt against `key`; returns the count so far and seconds until it resets."""
    full_key = f"ratelimit:{key}"
    async with redis.pipeline(transaction=True) as pipe:
        pipe.incr(full_key)
        pipe.expire(full_key, window_seconds, nx=True)
        pipe.ttl(full_key)
        count, _, ttl = await pipe.execute()
    return int(count), max(int(ttl), 1)


async def allow(key: str, *, limit: int, window_seconds: int) -> bool:
    """Count one attempt against `key`. False once more than `limit` happen in the window."""
    count, _ = await _count(key, window_seconds)
    return count <= limit


async def enforce(key: str, rule: Rule) -> None:
    """Count one attempt against `key` and raise 429 once there are more than the rule allows."""
    count, retry_after = await _count(key, rule.window_seconds)
    if count > rule.limit:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            rule.message,
            headers={"Retry-After": str(retry_after)},
        )


def client_ip(request: Request) -> str:
    # Uvicorn runs with --proxy-headers in production, so this is the visitor, not the proxy.
    return request.client.host if request.client else "unknown"
