"""
WebSocket Chat Handler
Handles real-time chat messaging over WebSocket
"""
import logging
from datetime import datetime
from uuid import UUID

from ...schemas.messages import WSAck, WSChatMessage, WSError, WSMessage, WSMessageType
from .connection_manager import connection_manager

logger = logging.getLogger(__name__)


class ChatHandler:
    """Handles chat-related WebSocket messages"""

    def __init__(self):
        self.conversation_rooms: dict[UUID, str] = {}  # conversation_id -> room_id

    async def handle_message(self, connection_id: UUID, message: WSMessage) -> WSMessage | None:
        """Route chat message to appropriate handler"""
        msg_type = message.type

        if msg_type == WSMessageType.CHAT_MESSAGE:
            return await self.handle_chat_message(connection_id, message)
        elif msg_type == WSMessageType.CHAT_HISTORY:
            return await self.handle_chat_history(connection_id, message)
        elif msg_type == WSMessageType.CHAT_TYPING:
            return await self.handle_typing(connection_id, message)
        elif msg_type == WSMessageType.CHAT_READ:
            return await self.handle_read_receipt(connection_id, message)

        return None

    async def handle_chat_message(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle incoming chat message"""
        try:
            chat_msg = WSChatMessage(**message.payload)
        except Exception as e:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="INVALID_MESSAGE", message=str(e)).model_dump(),
                correlation_id=message.message_id,
            )

        # Get or create conversation room
        room_id = await self._get_or_create_conversation_room(chat_msg.conversation_id)

        # Add connection to room if not already
        await connection_manager.join_room(connection_id, room_id)

        # Create response message
        response = WSMessage(
            type=WSMessageType.CHAT_MESSAGE,
            payload={
                "conversation_id": str(chat_msg.conversation_id),
                "content": chat_msg.content,
                "message_type": chat_msg.message_type,
                "attachments": chat_msg.attachments,
                "location": chat_msg.location,
                "reply_to": str(chat_msg.reply_to) if chat_msg.reply_to else None,
                "sender_connection_id": str(connection_id),
                "timestamp": datetime.utcnow().isoformat(),
            },
            correlation_id=message.message_id,
        )

        # Broadcast to room (excluding sender)
        await connection_manager.broadcast_to_room(room_id, response, exclude={connection_id})

        # Send acknowledgment to sender
        ack = WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(
                original_message_id=message.message_id or "",
                success=True,
                data={"message_id": str(uuid4())},
            ).model_dump(),
            correlation_id=message.message_id,
        )

        return ack

    async def handle_chat_history(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle chat history request"""
        conversation_id = message.payload.get("conversation_id")
        message.payload.get("limit", 50)
        message.payload.get("offset", 0)

        if not conversation_id:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="conversation_id required").model_dump(),
                correlation_id=message.message_id,
            )

        # In production, fetch from database
        # For now, return empty history
        response = WSMessage(
            type=WSMessageType.CHAT_HISTORY,
            payload={
                "conversation_id": conversation_id,
                "messages": [],
                "has_more": False,
            },
            correlation_id=message.message_id,
        )

        return response

    async def handle_typing(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle typing indicator"""
        conversation_id = message.payload.get("conversation_id")
        is_typing = message.payload.get("is_typing", True)

        if not conversation_id:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="conversation_id required").model_dump(),
                correlation_id=message.message_id,
            )

        room_id = await self._get_or_create_conversation_room(UUID(conversation_id))

        # Broadcast typing indicator to room (excluding sender)
        typing_msg = WSMessage(
            type=WSMessageType.CHAT_TYPING,
            payload={
                "conversation_id": conversation_id,
                "user_connection_id": str(connection_id),
                "is_typing": is_typing,
            },
        )

        await connection_manager.broadcast_to_room(room_id, typing_msg, exclude={connection_id})

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_read_receipt(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle read receipt"""
        conversation_id = message.payload.get("conversation_id")
        message_id = message.payload.get("message_id")

        if not conversation_id or not message_id:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="conversation_id and message_id required").model_dump(),
                correlation_id=message.message_id,
            )

        room_id = await self._get_or_create_conversation_room(UUID(conversation_id))

        # Broadcast read receipt to room
        read_msg = WSMessage(
            type=WSMessageType.CHAT_READ,
            payload={
                "conversation_id": conversation_id,
                "message_id": message_id,
                "read_by_connection_id": str(connection_id),
                "read_at": datetime.utcnow().isoformat(),
            },
        )

        await connection_manager.broadcast_to_room(room_id, read_msg, exclude={connection_id})

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def _get_or_create_conversation_room(self, conversation_id: UUID) -> str:
        """Get or create room for conversation"""
        if conversation_id in self.conversation_rooms:
            return self.conversation_rooms[conversation_id]

        room_id = f"conversation:{conversation_id}"
        await connection_manager.create_room(
            room_id=room_id,
            name=f"Conversation {conversation_id}",
            type="chat",
        )
        self.conversation_rooms[conversation_id] = room_id
        return room_id

    async def send_system_message(self, conversation_id: UUID, content: str,
                                 message_type: str = "system") -> int:
        """Send system message to conversation"""
        room_id = await self._get_or_create_conversation_room(conversation_id)

        msg = WSMessage(
            type=WSMessageType.CHAT_MESSAGE,
            payload={
                "conversation_id": str(conversation_id),
                "content": content,
                "message_type": message_type,
                "is_system": True,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return await connection_manager.broadcast_to_room(room_id, msg)


# Global chat handler instance
chat_handler = ChatHandler()
