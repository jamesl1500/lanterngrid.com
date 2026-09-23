from app.core.redis import redis


async def allow(key: str, *, limit: int, window_seconds: int) -> bool:
    """Count one attempt against `key`. False once more than `limit` happen in the window."""
    full_key = f"ratelimit:{key}"
    async with redis.pipeline(transaction=True) as pipe:
        pipe.incr(full_key)
        pipe.expire(full_key, window_seconds, nx=True)
        count, _ = await pipe.execute()
    return int(count) <= limit
