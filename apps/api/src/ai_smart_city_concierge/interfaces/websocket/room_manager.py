"""
WebSocket Room Manager
Manages WebSocket rooms/subscriptions for group communication.
"""
import logging
from typing import Any
from uuid import UUID

from ..infrastructure.config.redis import RedisKeys, get_redis_client

logger = logging.getLogger(__name__)


class RoomManager:
    """Manages WebSocket rooms for group subscriptions."""

    async def create_room(self, room_id: str, metadata: dict[str, Any] | None = None) -> None:
        """Create a new WebSocket room."""
        client = get_redis_client()
        key = RedisKeys.WS_ROOM.format(room_id=room_id)
        room_data = {"room_id": room_id, "created_at": str(__import__("datetime").datetime.utcnow().isoformat())}
        if metadata:
            room_data.update(metadata)
        await client.hset(key, mapping={k: str(v) for k, v in room_data.items()})
        logger.debug("Room created: %s", room_id)

    async def delete_room(self, room_id: str) -> None:
        """Delete a WebSocket room."""
        client = get_redis_client()
        key = RedisKeys.WS_ROOM.format(room_id=room_id)
        await client.delete(key)
        logger.debug("Room deleted: %s", room_id)

    async def join_room(self, room_id: str, connection_id: UUID) -> None:
        """Add a connection to a room."""
        client = get_redis_client()
        key = f"{RedisKeys.WS_ROOM.format(room_id=room_id)}:members"
        await client.sadd(key, str(connection_id))
        logger.debug("Connection %s joined room %s", connection_id, room_id)

    async def leave_room(self, room_id: str, connection_id: UUID) -> None:
        """Remove a connection from a room."""
        client = get_redis_client()
        key = f"{RedisKeys.WS_ROOM.format(room_id=room_id)}:members"
        await client.srem(key, str(connection_id))
        logger.debug("Connection %s left room %s", connection_id, room_id)

    async def get_room_members(self, room_id: str) -> list[UUID]:
        """Get all members of a room."""
        client = get_redis_client()
        key = f"{RedisKeys.WS_ROOM.format(room_id=room_id)}:members"
        members = await client.smembers(key)
        return [UUID(m) for m in members]

    async def get_room_info(self, room_id: str) -> dict[str, Any] | None:
        """Get room information."""
        client = get_redis_client()
        key = RedisKeys.WS_ROOM.format(room_id=room_id)
        data = await client.hgetall(key)
        return data if data else None

    async def room_exists(self, room_id: str) -> bool:
        """Check if a room exists."""
        client = get_redis_client()
        key = RedisKeys.WS_ROOM.format(room_id=room_id)
        return bool(await client.exists(key))
