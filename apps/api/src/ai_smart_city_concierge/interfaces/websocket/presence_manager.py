"""
WebSocket Presence Manager
Tracks user online/offline status and presence information.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from ..infrastructure.config.redis import RedisKeys, get_redis_client

logger = logging.getLogger(__name__)


class PresenceManager:
    """Manages user presence (online/offline/away) status."""

    async def set_online(self, user_id: UUID, connection_id: UUID) -> None:
        """Mark user as online."""
        client = get_redis_client()
        key = RedisKeys.WS_USER_CONNECTIONS.format(user_id=user_id)
        await client.sadd(key, str(connection_id))
        await client.expire(key, 86400)
        logger.debug("User %s is now online (connection: %s)", user_id, connection_id)

    async def set_offline(self, user_id: UUID, connection_id: UUID) -> None:
        """Mark user as offline."""
        client = get_redis_client()
        key = RedisKeys.WS_USER_CONNECTIONS.format(user_id=user_id)
        await client.srem(key, str(connection_id))
        remaining = await client.scard(key)
        if remaining == 0:
            await client.delete(key)
        logger.debug("User %s connection %s offline (%d remaining)", user_id, connection_id, remaining)

    async def is_online(self, user_id: UUID) -> bool:
        """Check if user is currently online."""
        client = get_redis_client()
        key = RedisKeys.WS_USER_CONNECTIONS.format(user_id=user_id)
        return bool(await client.exists(key))

    async def get_active_connections(self, user_id: UUID) -> list[UUID]:
        """Get all active connection IDs for a user."""
        client = get_redis_client()
        key = RedisKeys.WS_USER_CONNECTIONS.format(user_id=user_id)
        members = await client.smembers(key)
        return [UUID(m) for m in members]

    async def get_online_users(self) -> list[UUID]:
        """Get all currently online users."""
        client = get_redis_client()
        pattern = RedisKeys.WS_USER_CONNECTIONS.format(user_id="*")
        keys = await client.keys(pattern)
        users = []
        for key in keys:
            user_id = key.split(":")[2]
            users.append(UUID(user_id))
        return users

    async def get_presence_info(self, user_id: UUID) -> dict[str, Any]:
        """Get detailed presence information for a user."""
        is_online = await self.is_online(user_id)
        connections = await self.get_active_connections(user_id)
        return {
            "user_id": str(user_id),
            "is_online": is_online,
            "connection_count": len(connections),
            "last_seen": datetime.utcnow().isoformat() + "Z" if is_online else None,
        }
