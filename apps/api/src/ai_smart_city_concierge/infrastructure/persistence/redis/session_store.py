"""
Redis Session Store Implementation
"""
from typing import Any
from uuid import UUID

from ..config.redis import RedisKeys, RedisTTL, get_redis_client
from ..observability.logging import get_logger

logger = get_logger(__name__)


class SessionStore:
    """Redis-based session store for user sessions and refresh tokens."""

    async def create_session(
        self,
        user_id: UUID,
        session_data: dict[str, Any],
        ttl_seconds: int = RedisTTL.SESSION,
    ) -> str:
        """Create a new user session."""
        client = get_redis_client()
        key = RedisKeys.USER_SESSION.format(user_id=user_id)
        session_data["user_id"] = str(user_id)
        await client.hset(key, mapping={k: str(v) for k, v in session_data.items()})
        await client.expire(key, ttl_seconds)
        logger.info("Session created for user: %s", user_id)
        return key

    async def get_session(self, user_id: UUID) -> dict[str, Any] | None:
        """Get user session data."""
        client = get_redis_client()
        key = RedisKeys.USER_SESSION.format(user_id=user_id)
        data = await client.hgetall(key)
        return data if data else None

    async def delete_session(self, user_id: UUID) -> None:
        """Delete user session."""
        client = get_redis_client()
        key = RedisKeys.USER_SESSION.format(user_id=user_id)
        await client.delete(key)
        logger.info("Session deleted for user: %s", user_id)

    async def store_refresh_token(
        self,
        token_hash: str,
        user_id: UUID,
        ttl_seconds: int = RedisTTL.REFRESH_TOKEN,
    ) -> None:
        """Store refresh token hash."""
        client = get_redis_client()
        key = RedisKeys.REFRESH_TOKEN.format(token_hash=token_hash)
        await client.setex(key, ttl_seconds, str(user_id))

    async def get_refresh_token_user(self, token_hash: str) -> UUID | None:
        """Get user ID from refresh token hash."""
        client = get_redis_client()
        key = RedisKeys.REFRESH_TOKEN.format(token_hash=token_hash)
        user_id = await client.get(key)
        return UUID(user_id) if user_id else None

    async def revoke_refresh_token(self, token_hash: str) -> None:
        """Revoke refresh token."""
        client = get_redis_client()
        key = RedisKeys.REFRESH_TOKEN.format(token_hash=token_hash)
        await client.delete(key)

    async def is_session_valid(self, user_id: UUID) -> bool:
        """Check if user session is still valid."""
        client = get_redis_client()
        key = RedisKeys.USER_SESSION.format(user_id=user_id)
        return bool(await client.exists(key))
