from fastapi import status

from app.core.errors import AppError
from app.core.redis import redis_client
from app.core.security import sha256_hex


async def hit(scope: str, identity: str, *, limit: int, window_seconds: int = 60) -> None:
    """Fixed-window counter in Redis; raises 429 once `limit` hits per window are exceeded."""
    # Hashed so that user input (logins, emails) never ends up in key names.
    key = f"rl:{scope}:{sha256_hex(identity)}"
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        pipe.ttl(key)
        count, _, ttl = await pipe.execute()
    if int(count) > limit:
        raise AppError(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "rate_limited",
            headers={"Retry-After": str(max(int(ttl), 1))},
        )
