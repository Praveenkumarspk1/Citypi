"""
Rate Limiter Adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ....application.ports.external_services import RateLimiterPort


@dataclass
class RateLimitResult:
    """Rate limit check result"""
    allowed: bool
    current: int
    limit: int
    remaining: int
    reset_at: float
    retry_after: float | None = None


class BaseRateLimiterAdapter(RateLimiterPort, ABC):
    """Base rate limiter adapter"""

    @abstractmethod
    async def _check_rate_limit_request(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check rate limit request"""
        pass

    @abstractmethod
    async def _increment_request(
        self,
        key: str,
        window_seconds: int,
    ) -> int:
        """Increment counter request"""
        pass

    @abstractmethod
    async def _reset_request(self, key: str) -> None:
        """Reset counter request"""
        pass

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> dict[str, Any]:
        """Check rate limit"""
        result = await self._check_rate_limit_request(key, limit, window_seconds)
        return {
            "allowed": result.allowed,
            "current": result.current,
            "limit": result.limit,
            "remaining": result.remaining,
            "reset_at": result.reset_at,
            "retry_after": result.retry_after,
        }

    async def increment(
        self,
        key: str,
        window_seconds: int,
    ) -> int:
        """Increment counter"""
        return await self._increment_request(key, window_seconds)

    async def reset(self, key: str) -> None:
        """Reset counter"""
        await self._reset_request(key)


class RedisRateLimiterAdapter(BaseRateLimiterAdapter):
    """Redis-based rate limiter (sliding window)"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as redis
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )
        return self._client

    def _get_keys(self, key: str, window_seconds: int) -> tuple:
        import time
        now = time.time()
        window_start = int(now // window_seconds) * window_seconds
        current_key = f"ratelimit:{key}:{window_start}"
        previous_key = f"ratelimit:{key}:{window_start - window_seconds}"
        return current_key, previous_key, window_start, now

    async def _check_rate_limit_request(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        client = await self._get_client()

        current_key, previous_key, window_start, now = self._get_keys(key, window_seconds)

        # Get current and previous window counts
        pipe = client.pipeline()
        pipe.get(current_key)
        pipe.get(previous_key)
        pipe.ttl(current_key)
        results = await pipe.execute()

        current_count = int(results[0]) if results[0] else 0
        previous_count = int(results[1]) if results[1] else 0
        results[2] if results[2] > 0 else window_seconds

        # Calculate weighted count for sliding window
        previous_weight = (window_start + window_seconds - now) / window_seconds
        weighted_count = current_count + (previous_count * previous_weight)

        allowed = weighted_count < limit
        remaining = max(0, limit - int(weighted_count))
        reset_at = window_start + window_seconds
        retry_after = None if allowed else (reset_at - now)

        return RateLimitResult(
            allowed=allowed,
            current=int(weighted_count),
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=retry_after,
        )

    async def _increment_request(
        self,
        key: str,
        window_seconds: int,
    ) -> int:
        client = await self._get_client()

        current_key, _, window_start, _ = self._get_keys(key, window_seconds)

        # Increment current window
        pipe = client.pipeline()
        pipe.incr(current_key)
        pipe.expire(current_key, window_seconds * 2)
        results = await pipe.execute()

        return results[0]

    async def _reset_request(self, key: str) -> None:
        client = await self._get_client()

        # Delete all rate limit keys for this key
        pattern = f"ratelimit:{key}:*"
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


class TokenBucketRateLimiterAdapter(BaseRateLimiterAdapter):
    """Token bucket rate limiter"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as redis
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )
        return self._client

    async def _check_rate_limit_request(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        client = await self._get_client()
        import time

        bucket_key = f"tokenbucket:{key}"
        now = time.time()

        # Get bucket state
        pipe = client.pipeline()
        pipe.hmget(bucket_key, "tokens", "last_refill")
        pipe.ttl(bucket_key)
        results = await pipe.execute()

        tokens_data = results[0]
        results[1]

        if tokens_data[0] is None:
            # New bucket
            tokens = limit
            last_refill = now
        else:
            tokens = float(tokens_data[0])
            last_refill = float(tokens_data[1])

        # Refill tokens
        elapsed = now - last_refill
        refill_rate = limit / window_seconds
        tokens = min(limit, tokens + elapsed * refill_rate)

        allowed = tokens >= 1
        if allowed:
            tokens -= 1

        # Save bucket state
        await client.hmset(bucket_key, {
            "tokens": tokens,
            "last_refill": now,
        })
        await client.expire(bucket_key, window_seconds * 2)

        remaining = int(tokens)
        reset_at = now + (1 - tokens) / refill_rate if tokens < 1 else now + window_seconds
        retry_after = None if allowed else (1 - tokens) / refill_rate

        return RateLimitResult(
            allowed=allowed,
            current=limit - remaining,
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=retry_after,
        )

    async def _increment_request(
        self,
        key: str,
        window_seconds: int,
    ) -> int:
        # For token bucket, increment is handled in check_rate_limit
        result = await self._check_rate_limit_request(key, 1, window_seconds)
        return 1 if result.allowed else 0

    async def _reset_request(self, key: str) -> None:
        client = await self._get_client()
        bucket_key = f"tokenbucket:{key}"
        await client.delete(bucket_key)

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


class InMemoryRateLimiterAdapter(BaseRateLimiterAdapter):
    """In-memory rate limiter (for development/testing)"""

    def __init__(self):
        self._windows: dict[str, dict[int, int]] = {}
        self._token_buckets: dict[str, dict[str, float]] = {}

    async def _check_rate_limit_request(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        import time

        now = time.time()
        window_start = int(now // window_seconds) * window_seconds

        if key not in self._windows:
            self._windows[key] = {}

        # Clean old windows
        cutoff = window_start - window_seconds
        self._windows[key] = {
            k: v for k, v in self._windows[key].items()
            if k >= cutoff
        }

        current_count = self._windows[key].get(window_start, 0)
        previous_count = self._windows[key].get(window_start - window_seconds, 0)

        previous_weight = (window_start + window_seconds - now) / window_seconds
        weighted_count = current_count + (previous_count * previous_weight)

        allowed = weighted_count < limit
        remaining = max(0, limit - int(weighted_count))
        reset_at = window_start + window_seconds
        retry_after = None if allowed else (reset_at - now)

        return RateLimitResult(
            allowed=allowed,
            current=int(weighted_count),
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=retry_after,
        )

    async def _increment_request(
        self,
        key: str,
        window_seconds: int,
    ) -> int:
        import time

        now = time.time()
        window_start = int(now // window_seconds) * window_seconds

        if key not in self._windows:
            self._windows[key] = {}

        self._windows[key][window_start] = self._windows[key].get(window_start, 0) + 1

        return self._windows[key][window_start]

    async def _reset_request(self, key: str) -> None:
        if key in self._windows:
            del self._windows[key]
        if key in self._token_buckets:
            del self._token_buckets[key]
