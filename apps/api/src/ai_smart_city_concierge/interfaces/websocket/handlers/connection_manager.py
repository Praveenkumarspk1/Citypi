"""
WebSocket Connection Manager
Manages WebSocket connections, rooms, and message routing
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from ...schemas.connection import ConnectionState, WSConnectionInfo, WSRoomInfo, WSUserPresence
from ...schemas.messages import (
    WSMessage,
    WSPingMessage,
    WSPongMessage,
)

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """Internal connection representation"""
    websocket: WebSocket
    info: WSConnectionInfo
    authenticated: bool = False
    last_ping: datetime = field(default_factory=datetime.utcnow)


class ConnectionManager:
    """Manages WebSocket connections and message routing"""

    def __init__(self):
        self.connections: dict[UUID, Connection] = {}
        self.user_connections: dict[UUID, set[UUID]] = {}  # user_id -> connection_ids
        self.rooms: dict[str, WSRoomInfo] = {}
        self.room_members: dict[str, set[UUID]] = {}  # room_id -> connection_ids
        self.subscriptions: dict[str, dict[UUID, dict[str, Any]]] = {}  # type -> connection_id -> filters
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> UUID:
        """Accept new WebSocket connection"""
        await websocket.accept()

        connection_id = uuid4()
        connection_info = WSConnectionInfo(
            connection_id=connection_id,
            state=ConnectionState.CONNECTED,
        )

        connection = Connection(
            websocket=websocket,
            info=connection_info,
        )

        async with self._lock:
            self.connections[connection_id] = connection

        logger.info(f"New WebSocket connection: {connection_id}")
        return connection_id

    async def disconnect(self, connection_id: UUID, code: int = 1000, reason: str = "Normal closure"):
        """Disconnect WebSocket connection"""
        async with self._lock:
            connection = self.connections.pop(connection_id, None)

            if not connection:
                return

            # Remove from user connections
            if connection.info.user_id:
                user_conns = self.user_connections.get(connection.info.user_id, set())
                user_conns.discard(connection_id)
                if not user_conns:
                    self.user_connections.pop(connection.info.user_id, None)

            # Remove from rooms
            for room_id in list(connection.info.subscriptions):
                await self._leave_room_internal(connection_id, room_id)

            # Remove subscriptions
            for _sub_type, subs in self.subscriptions.items():
                subs.pop(connection_id, None)

        # Close WebSocket
        if connection.websocket.client_state == WebSocketState.CONNECTED:
            try:
                await connection.websocket.close(code=code, reason=reason)
            except Exception as e:
                logger.warning(f"Error closing WebSocket {connection_id}: {e}")

        logger.info(f"WebSocket disconnected: {connection_id}")

    async def authenticate(self, connection_id: UUID, user_id: UUID,
                          device_id: str | None = None,
                          platform: str | None = None,
                          app_version: str | None = None) -> bool:
        """Authenticate a connection"""
        async with self._lock:
            connection = self.connections.get(connection_id)
            if not connection:
                return False

            connection.info.user_id = user_id
            connection.info.device_id = device_id
            connection.info.platform = platform
            connection.info.app_version = app_version
            connection.info.state = ConnectionState.AUTHENTICATED
            connection.authenticated = True

            # Track user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)

            logger.info(f"Connection {connection_id} authenticated as user {user_id}")
            return True

    async def send_message(self, connection_id: UUID, message: WSMessage) -> bool:
        """Send message to specific connection"""
        async with self._lock:
            connection = self.connections.get(connection_id)
            if not connection or connection.websocket.client_state != WebSocketState.CONNECTED:
                return False

        try:
            await connection.websocket.send_text(message.model_dump_json())
            connection.last_ping = datetime.utcnow()
            return True
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id, code=1011, reason="Send error")
            return False

    async def send_to_user(self, user_id: UUID, message: WSMessage) -> int:
        """Send message to all connections of a user"""
        async with self._lock:
            connection_ids = self.user_connections.get(user_id, set()).copy()

        sent = 0
        for conn_id in connection_ids:
            if await self.send_message(conn_id, message):
                sent += 1
        return sent

    async def broadcast(self, message: WSMessage, exclude: set[UUID] | None = None) -> int:
        """Broadcast message to all authenticated connections"""
        async with self._lock:
            connection_ids = {
                cid for cid, conn in self.connections.items()
                if conn.authenticated and conn.websocket.client_state == WebSocketState.CONNECTED
            }

        if exclude:
            connection_ids -= exclude

        sent = 0
        for conn_id in connection_ids:
            if await self.send_message(conn_id, message):
                sent += 1
        return sent

    async def broadcast_to_room(self, room_id: str, message: WSMessage,
                               exclude: set[UUID] | None = None) -> int:
        """Broadcast message to all members of a room"""
        async with self._lock:
            connection_ids = self.room_members.get(room_id, set()).copy()

        if exclude:
            connection_ids -= exclude

        sent = 0
        for conn_id in connection_ids:
            if await self.send_message(conn_id, message):
                sent += 1
        return sent

    async def create_room(self, room_id: str, name: str, type: str,
                         max_members: int | None = None,
                         metadata: dict[str, Any] | None = None) -> WSRoomInfo:
        """Create a new room"""
        async with self._lock:
            if room_id in self.rooms:
                raise ValueError(f"Room {room_id} already exists")

            room = WSRoomInfo(
                room_id=room_id,
                name=name,
                type=type,
                max_members=max_members,
                metadata=metadata or {},
            )
            self.rooms[room_id] = room
            self.room_members[room_id] = set()

        logger.info(f"Created room: {room_id} ({name})")
        return room

    async def join_room(self, connection_id: UUID, room_id: str) -> bool:
        """Add connection to room"""
        async with self._lock:
            connection = self.connections.get(connection_id)
            room = self.rooms.get(room_id)

            if not connection or not room:
                return False

            # Check room capacity
            if room.max_members and len(self.room_members[room_id]) >= room.max_members:
                return False

            # Add to room
            self.room_members[room_id].add(connection_id)
            room.members.add(connection.info.user_id) if connection.info.user_id else None
            connection.info.subscriptions.add(room_id)

        logger.info(f"Connection {connection_id} joined room {room_id}")
        return True

    async def leave_room(self, connection_id: UUID, room_id: str) -> bool:
        """Remove connection from room"""
        return await self._leave_room_internal(connection_id, room_id)

    async def _leave_room_internal(self, connection_id: UUID, room_id: str) -> bool:
        """Internal method to leave room (must hold lock)"""
        connection = self.connections.get(connection_id)
        room = self.rooms.get(room_id)

        if not connection or not room:
            return False

        self.room_members[room_id].discard(connection_id)
        if connection.info.user_id:
            room.members.discard(connection.info.user_id)
        connection.info.subscriptions.discard(room_id)

        # Clean up empty rooms
        if not self.room_members[room_id]:
            self.room_members.pop(room_id, None)
            self.rooms.pop(room_id, None)

        logger.info(f"Connection {connection_id} left room {room_id}")
        return True

    async def subscribe(self, connection_id: UUID, sub_type: str,
                       filters: dict[str, Any] | None = None) -> str:
        """Subscribe to a topic"""
        subscription_id = f"{sub_type}:{connection_id}"

        async with self._lock:
            connection = self.connections.get(connection_id)
            if not connection:
                raise ValueError("Connection not found")

            if sub_type not in self.subscriptions:
                self.subscriptions[sub_type] = {}

            self.subscriptions[sub_type][connection_id] = filters or {}
            connection.info.subscriptions.add(subscription_id)

        logger.info(f"Connection {connection_id} subscribed to {sub_type}")
        return subscription_id

    async def unsubscribe(self, connection_id: UUID, sub_type: str) -> bool:
        """Unsubscribe from a topic"""
        async with self._lock:
            connection = self.connections.get(connection_id)
            if not connection:
                return False

            if sub_type in self.subscriptions:
                self.subscriptions[sub_type].pop(connection_id, None)

            connection.info.subscriptions.discard(f"{sub_type}:{connection_id}")

        logger.info(f"Connection {connection_id} unsubscribed from {sub_type}")
        return True

    async def get_subscribers(self, sub_type: str,
                             filters: dict[str, Any] | None = None) -> list[UUID]:
        """Get connections subscribed to a topic matching filters"""
        async with self._lock:
            subs = self.subscriptions.get(sub_type, {})

            if not filters:
                return list(subs.keys())

            # Filter by subscription filters
            matching = []
            for conn_id, sub_filters in subs.items():
                match = True
                for key, value in filters.items():
                    if sub_filters.get(key) != value:
                        match = False
                        break
                if match:
                    matching.append(conn_id)
            return matching

    async def get_connection_info(self, connection_id: UUID) -> WSConnectionInfo | None:
        """Get connection information"""
        async with self._lock:
            connection = self.connections.get(connection_id)
            return connection.info if connection else None

    async def get_user_presence(self, user_id: UUID) -> WSUserPresence | None:
        """Get user presence information"""
        async with self._lock:
            connection_ids = self.user_connections.get(user_id, set())
            if not connection_ids:
                return None

            # Get first connection info
            connection = self.connections.get(next(iter(connection_ids)))
            if not connection:
                return None

            return WSUserPresence(
                user_id=user_id,
                status="online",
                last_seen=connection.info.last_activity,
                device_id=connection.info.device_id,
                platform=connection.info.platform,
            )

    async def update_activity(self, connection_id: UUID):
        """Update last activity timestamp"""
        async with self._lock:
            connection = self.connections.get(connection_id)
            if connection:
                connection.info.last_activity = datetime.utcnow()

    async def handle_ping(self, connection_id: UUID, message: WSPingMessage) -> WSPongMessage:
        """Handle ping message"""
        await self.update_activity(connection_id)
        return WSPongMessage(
            timestamp=message.timestamp,
            server_time=datetime.utcnow(),
        )

    def get_stats(self) -> dict[str, Any]:
        """Get connection manager statistics"""
        return {
            "total_connections": len(self.connections),
            "authenticated_connections": sum(1 for c in self.connections.values() if c.authenticated),
            "unique_users": len(self.user_connections),
            "rooms": len(self.rooms),
            "subscriptions": sum(len(s) for s in self.subscriptions.values()),
        }


# Global connection manager instance
connection_manager = ConnectionManager()
