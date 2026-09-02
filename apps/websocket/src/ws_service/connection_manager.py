"""
WebSocket Connection Manager

Manages WebSocket connections, user sessions, and message routing.
"""
import asyncio
import json
from uuid import uuid4

import redis.asyncio as redis
import structlog
from fastapi import WebSocket

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections and user sessions."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self._connections: dict[str, WebSocket] = {}  # connection_id -> WebSocket
        self._user_connections: dict[str, set[str]] = {}  # user_id -> Set[connection_id]
        self._connection_user: dict[str, str] = {}  # connection_id -> user_id
        self._connection_metadata: dict[str, dict] = {}  # connection_id -> metadata
        self._cleanup_task: asyncio.Task | None = None
        self._running = False

        # Message handlers by type
        self._message_handlers: dict[str, callable] = {}

    def register_handler(self, message_type: str, handler: callable) -> None:
        """Register a message handler for a specific message type."""
        self._message_handlers[message_type] = handler

    async def connect(self, websocket: WebSocket, user_id: str, metadata: dict = None) -> str:
        """Accept a new WebSocket connection."""
        await websocket.accept()

        connection_id = str(uuid4())
        self._connections[connection_id] = websocket
        self._connection_user[connection_id] = user_id
        self._connection_metadata[connection_id] = metadata or {}

        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(connection_id)

        # Store in Redis for distributed deployment
        await self._store_connection(connection_id, user_id, metadata or {})

        logger.info("WebSocket connected", connection_id=connection_id, user_id=user_id)
        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """Disconnect a WebSocket connection."""
        if connection_id not in self._connections:
            return

        user_id = self._connection_user.get(connection_id)
        websocket = self._connections.get(connection_id)

        # Remove from local tracking
        self._connections.pop(connection_id, None)
        self._connection_user.pop(connection_id, None)
        self._connection_metadata.pop(connection_id, None)

        if user_id and user_id in self._user_connections:
            self._user_connections[user_id].discard(connection_id)
            if not self._user_connections[user_id]:
                self._user_connections.pop(user_id, None)

        # Remove from Redis
        await self._remove_connection(connection_id)

        # Close WebSocket if still open
        if websocket:
            try:
                await websocket.close()
            except Exception:
                pass

        logger.info("WebSocket disconnected", connection_id=connection_id, user_id=user_id)

    async def disconnect_user(self, user_id: str) -> None:
        """Disconnect all connections for a user."""
        connection_ids = self._user_connections.get(user_id, set()).copy()
        for connection_id in connection_ids:
            await self.disconnect(connection_id)

    async def disconnect_all(self) -> None:
        """Disconnect all connections."""
        connection_ids = list(self._connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)

    async def send_to_connection(self, connection_id: str, message: dict) -> bool:
        """Send a message to a specific connection."""
        websocket = self._connections.get(connection_id)
        if not websocket:
            return False

        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error("Failed to send message", connection_id=connection_id, error=str(e))
            await self.disconnect(connection_id)
            return False

    async def send_to_user(self, user_id: str, message: dict) -> int:
        """Send a message to all connections of a user."""
        connection_ids = self._user_connections.get(user_id, set())
        sent = 0
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent += 1
        return sent

    async def broadcast(self, message: dict, exclude_user: str = None) -> int:
        """Broadcast a message to all connected users."""
        sent = 0
        for user_id, connection_ids in self._user_connections.items():
            if user_id != exclude_user:
                for connection_id in connection_ids:
                    if await self.send_to_connection(connection_id, message):
                        sent += 1
        return sent

    async def broadcast_to_users(self, user_ids: list[str], message: dict) -> int:
        """Broadcast a message to specific users."""
        sent = 0
        for user_id in user_ids:
            sent += await self.send_to_user(user_id, message)
        return sent

    async def handle_message(self, user_id: str, message: dict) -> None:
        """Route a message to the appropriate handler."""
        message_type = message.get("type", "unknown")
        handler = self._message_handlers.get(message_type)

        if handler:
            try:
                await handler(user_id, message)
            except Exception as e:
                logger.error("Handler error", message_type=message_type, user_id=user_id, error=str(e))
        else:
            logger.warning("No handler for message type", message_type=message_type, user_id=user_id)

    def get_user_connections(self, user_id: str) -> list[str]:
        """Get all connection IDs for a user."""
        return list(self._user_connections.get(user_id, set()))

    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self._user_connections and len(self._user_connections[user_id]) > 0

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self._connections)

    def get_user_count(self) -> int:
        """Get number of unique connected users."""
        return len(self._user_connections)

    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": self.get_connection_count(),
            "unique_users": self.get_user_count(),
            "connections_per_user": {
                user_id: len(conns) for user_id, conns in self._user_connections.items()
            },
        }

    async def _store_connection(self, connection_id: str, user_id: str, metadata: dict) -> None:
        """Store connection info in Redis."""
        key = f"ws:connection:{connection_id}"
        data = {
            "connection_id": connection_id,
            "user_id": user_id,
            "metadata": metadata,
        }
        await self.redis.set(key, json.dumps(data), ex=3600)  # 1 hour TTL

        # Add to user's connection set
        user_key = f"ws:user:{user_id}:connections"
        await self.redis.sadd(user_key, connection_id)
        await self.redis.expire(user_key, 3600)

    async def _remove_connection(self, connection_id: str) -> None:
        """Remove connection info from Redis."""
        key = f"ws:connection:{connection_id}"
        data = await self.redis.get(key)
        if data:
            conn_data = json.loads(data)
            user_id = conn_data.get("user_id")
            if user_id:
                user_key = f"ws:user:{user_id}:connections"
                await self.redis.srem(user_key, connection_id)
        await self.redis.delete(key)

    async def start_cleanup_task(self) -> None:
        """Start the periodic cleanup task."""
        if self._running:
            return
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Started connection cleanup task")

    async def stop_cleanup_task(self) -> None:
        """Stop the periodic cleanup task."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped connection cleanup task")

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of stale connections."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Cleanup task error", error=str(e))

    async def _cleanup_stale_connections(self) -> None:
        """Remove stale connections that haven't sent pings."""
        # This would check for connections that haven't sent heartbeats
        # For now, we rely on WebSocket close events
        pass
