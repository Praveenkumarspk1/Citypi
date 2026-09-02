"""
WebSocket Itinerary Handler
Handles real-time collaborative itinerary editing
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from ...schemas.messages import WSAck, WSError, WSItineraryUpdate, WSMessage, WSMessageType
from .connection_manager import connection_manager

logger = logging.getLogger(__name__)


class ItineraryHandler:
    """Handles itinerary-related WebSocket messages for collaborative editing"""

    def __init__(self):
        self.itinerary_rooms: dict[UUID, str] = {}  # itinerary_id -> room_id

    async def handle_message(self, connection_id: UUID, message: WSMessage) -> WSMessage | None:
        """Route itinerary message to appropriate handler"""
        msg_type = message.type

        if msg_type == WSMessageType.ITINERARY_UPDATE:
            return await self.handle_itinerary_update(connection_id, message)
        elif msg_type == WSMessageType.ITINERARY_ITEM_ADDED:
            return await self.handle_item_added(connection_id, message)
        elif msg_type == WSMessageType.ITINERARY_ITEM_UPDATED:
            return await self.handle_item_updated(connection_id, message)
        elif msg_type == WSMessageType.ITINERARY_ITEM_REMOVED:
            return await self.handle_item_removed(connection_id, message)
        elif msg_type == WSMessageType.ITINERARY_COLLABORATOR_JOINED:
            return await self.handle_collaborator_joined(connection_id, message)
        elif msg_type == WSMessageType.ITINERARY_COLLABORATOR_LEFT:
            return await self.handle_collaborator_left(connection_id, message)

        return None

    async def handle_itinerary_update(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle general itinerary update"""
        try:
            update = WSItineraryUpdate(**message.payload)
        except Exception as e:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="INVALID_MESSAGE", message=str(e)).model_dump(),
                correlation_id=message.message_id,
            )

        room_id = await self._get_or_create_itinerary_room(update.itinerary_id)
        await connection_manager.join_room(connection_id, room_id)

        # Broadcast to other collaborators
        broadcast_msg = WSMessage(
            type=WSMessageType.ITINERARY_UPDATE,
            payload={
                "itinerary_id": str(update.itinerary_id),
                "action": update.action,
                "user_id": str(update.user_id),
                "data": update.data,
                "timestamp": update.timestamp.isoformat(),
            },
        )

        await connection_manager.broadcast_to_room(room_id, broadcast_msg, exclude={connection_id})

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_item_added(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle itinerary item added"""
        itinerary_id = message.payload.get("itinerary_id")
        item_data = message.payload.get("item")
        user_id = message.payload.get("user_id")

        if not itinerary_id or not item_data or not user_id:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="itinerary_id, item, and user_id required").model_dump(),
                correlation_id=message.message_id,
            )

        room_id = await self._get_or_create_itinerary_room(UUID(itinerary_id))
        await connection_manager.join_room(connection_id, room_id)

        broadcast_msg = WSMessage(
            type=WSMessageType.ITINERARY_ITEM_ADDED,
            payload={
                "itinerary_id": itinerary_id,
                "item": item_data,
                "added_by": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        await connection_manager.broadcast_to_room(room_id, broadcast_msg, exclude={connection_id})

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_item_updated(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle itinerary item updated"""
        itinerary_id = message.payload.get("itinerary_id")
        item_id = message.payload.get("item_id")
        item_data = message.payload.get("item")
        user_id = message.payload.get("user_id")

        if not itinerary_id or not item_id or not item_data or not user_id:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="itinerary_id, item_id, item, and user_id required").model_dump(),
                correlation_id=message.message_id,
            )

        room_id = await self._get_or_create_itinerary_room(UUID(itinerary_id))
        await connection_manager.join_room(connection_id, room_id)

        broadcast_msg = WSMessage(
            type=WSMessageType.ITINERARY_ITEM_UPDATED,
            payload={
                "itinerary_id": itinerary_id,
                "item_id": item_id,
                "item": item_data,
                "updated_by": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        await connection_manager.broadcast_to_room(room_id, broadcast_msg, exclude={connection_id})

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_item_removed(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle itinerary item removed"""
        itinerary_id = message.payload.get("itinerary_id")
        item_id = message.payload.get("item_id")
        user_id = message.payload.get("user_id")

        if not itinerary_id or not item_id or not user_id:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="itinerary_id, item_id, and user_id required").model_dump(),
                correlation_id=message.message_id,
            )

        room_id = await self._get_or_create_itinerary_room(UUID(itinerary_id))
        await connection_manager.join_room(connection_id, room_id)

        broadcast_msg = WSMessage(
            type=WSMessageType.ITINERARY_ITEM_REMOVED,
            payload={
                "itinerary_id": itinerary_id,
                "item_id": item_id,
                "removed_by": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        await connection_manager.broadcast_to_room(room_id, broadcast_msg, exclude={connection_id})

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_collaborator_joined(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle collaborator joined itinerary"""
        itinerary_id = message.payload.get("itinerary_id")
        user_id = message.payload.get("user_id")
        user_name = message.payload.get("user_name")

        if not itinerary_id or not user_id:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="itinerary_id and user_id required").model_dump(),
                correlation_id=message.message_id,
            )

        room_id = await self._get_or_create_itinerary_room(UUID(itinerary_id))
        await connection_manager.join_room(connection_id, room_id)

        broadcast_msg = WSMessage(
            type=WSMessageType.ITINERARY_COLLABORATOR_JOINED,
            payload={
                "itinerary_id": itinerary_id,
                "user_id": user_id,
                "user_name": user_name,
                "joined_at": datetime.utcnow().isoformat(),
            },
        )

        await connection_manager.broadcast_to_room(room_id, broadcast_msg, exclude={connection_id})

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_collaborator_left(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle collaborator left itinerary"""
        itinerary_id = message.payload.get("itinerary_id")
        user_id = message.payload.get("user_id")

        if not itinerary_id or not user_id:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="itinerary_id and user_id required").model_dump(),
                correlation_id=message.message_id,
            )

        room_id = await self._get_or_create_itinerary_room(UUID(itinerary_id))
        await connection_manager.leave_room(connection_id, room_id)

        broadcast_msg = WSMessage(
            type=WSMessageType.ITINERARY_COLLABORATOR_LEFT,
            payload={
                "itinerary_id": itinerary_id,
                "user_id": user_id,
                "left_at": datetime.utcnow().isoformat(),
            },
        )

        await connection_manager.broadcast_to_room(room_id, broadcast_msg)

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def _get_or_create_itinerary_room(self, itinerary_id: UUID) -> str:
        """Get or create room for itinerary"""
        if itinerary_id in self.itinerary_rooms:
            return self.itinerary_rooms[itinerary_id]

        room_id = f"itinerary:{itinerary_id}"
        await connection_manager.create_room(
            room_id=room_id,
            name=f"Itinerary {itinerary_id} Collaboration",
            type="itinerary",
        )
        self.itinerary_rooms[itinerary_id] = room_id
        return room_id

    async def broadcast_itinerary_change(self, itinerary_id: UUID, action: str,
                                        user_id: UUID, data: dict[str, Any]) -> int:
        """Broadcast itinerary change to all collaborators"""
        room_id = await self._get_or_create_itinerary_room(itinerary_id)

        msg = WSMessage(
            type=WSMessageType.ITINERARY_UPDATE,
            payload={
                "itinerary_id": str(itinerary_id),
                "action": action,
                "user_id": str(user_id),
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return await connection_manager.broadcast_to_room(room_id, msg)


# Global itinerary handler instance
itinerary_handler = ItineraryHandler()
