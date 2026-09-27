import hashlib
import hmac
from collections.abc import Awaitable
from typing import cast

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.services.errors import DependencyUnavailable, RateLimited

COUNTER_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return {count, redis.call('TTL', KEYS[1])}
"""


class RateLimiter:
    def __init__(self, redis: Redis, secret: str) -> None:
        self.redis = redis
        self.secret = secret.encode()

    async def check(self, subject: str, limit: int, window_seconds: int = 60) -> None:
        digest = hmac.new(self.secret, subject.encode(), hashlib.sha256).hexdigest()
        try:
            result = await cast(
                Awaitable[list[int]],
                self.redis.eval(
                    COUNTER_SCRIPT, 1, f"taskman:rate:{digest}", str(window_seconds)
                ),
            )
        except (RedisError, OSError) as exc:
            raise DependencyUnavailable from exc
        count, ttl = result
        if count > limit:
            raise RateLimited(max(1, ttl))
