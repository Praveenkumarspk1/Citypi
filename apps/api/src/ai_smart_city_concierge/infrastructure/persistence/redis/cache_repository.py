"""
Redis Cache Repository Implementation
"""
from typing import Any

from ...application.ports import CacheServicePort
from ..config.redis import get_redis_client
from ..observability.logging import get_logger

logger = get_logger(__name__)


class CacheRepository(CacheServicePort):
    """Redis-based cache repository implementation."""

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        client = get_redis_client()
        value = await client.get(key)
        if value is not None:
            logger.debug("Cache hit: %s", key)
        else:
            logger.debug("Cache miss: %s", key)
        return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        """Set value in cache."""
        client = get_redis_client()
        if ttl_seconds:
            await client.setex(key, ttl_seconds, value)
        else:
            await client.set(key, value)
        logger.debug("Cache set: %s (ttl=%s)", key, ttl_seconds)

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        client = get_redis_client()
        await client.delete(key)
        logger.debug("Cache delete: %s", key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        client = get_redis_client()
        return bool(await client.exists(key))

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        client = get_redis_client()
        return await client.incrby(key, amount)

    async def get_multi(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values."""
        client = get_redis_client()
        values = await client.mget(keys)
        return {k: v for k, v in zip(keys, values, strict=False) if v is not None}

    async def set_multi(
        self,
        mapping: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> None:
        """Set multiple values."""
        client = get_redis_client()
        pipeline = client.pipeline()
        for key, value in mapping.items():
            if ttl_seconds:
                pipeline.setex(key, ttl_seconds, value)
            else:
                pipeline.set(key, value)
        await pipeline.execute()
