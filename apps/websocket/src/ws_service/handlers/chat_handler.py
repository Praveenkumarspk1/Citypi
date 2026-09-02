"""
Chat WebSocket Handler

Handles real-time chat messaging between users and AI assistant.
"""
import json
from datetime import datetime

import redis.asyncio as redis
import structlog

from ws_service.connection_manager import ConnectionManager

logger = structlog.get_logger()


class ChatHandler:
    """Handles chat WebSocket connections and messages."""

    def __init__(self, connection_manager: ConnectionManager, redis_client: redis.Redis):
        self.connection_manager = connection_manager
        self.redis = redis_client
        self.max_history = 100

        # Register message handlers
        self.connection_manager.register_handler("chat_message", self._handle_chat_message)
        self.connection_manager.register_handler("chat_history", self._handle_chat_history)
        self.connection_manager.register_handler("chat_typing", self._handle_typing_indicator)
        self.connection_manager.register_handler("chat_read", self._handle_read_receipt)

    async def handle_connection(self, websocket, user_id: str) -> None:
        """Handle a new chat WebSocket connection."""
        connection_id = await self.connection_manager.connect(websocket, user_id, {"handler": "chat"})

        try:
            # Send welcome message
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "chat_welcome",
                "user_id": user_id,
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Send recent chat history
            await self._send_recent_history(user_id, connection_id)

            # Listen for messages
            while True:
                data = await websocket.receive_json()
                await self.connection_manager.handle_message(user_id, data)

        except Exception as e:
            logger.error("Chat connection error", user_id=user_id, error=str(e))
        finally:
            await self.connection_manager.disconnect(connection_id)

    async def send_message(
        self,
        recipient_id: str,
        sender_id: str,
        content: str,
        message_type: str = "text",
        metadata: dict = None,
    ) -> dict:
        """Send a chat message to a recipient."""
        message = {
            "type": "chat_message",
            "message_id": f"msg_{datetime.utcnow().timestamp()}",
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "content": content,
            "message_type": message_type,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store in history
        await self._store_message(recipient_id, message)

        # Send to recipient if online
        sent = await self.connection_manager.send_to_user(recipient_id, message)

        # Also send to sender for confirmation
        await self.connection_manager.send_to_user(sender_id, {
            **message,
            "type": "chat_sent",
            "delivered": sent > 0,
        })

        return {"status": "sent", "delivered": sent > 0, "message_id": message["message_id"]}

    async def _handle_chat_message(self, user_id: str, message: dict) -> None:
        """Handle incoming chat message."""
        recipient_id = message.get("recipient_id")
        content = message.get("content")
        message_type = message.get("message_type", "text")
        metadata = message.get("metadata", {})

        if not recipient_id or not content:
            logger.warning("Invalid chat message", user_id=user_id)
            return

        # Store message in history
        chat_message = {
            "type": "chat_message",
            "message_id": f"msg_{datetime.utcnow().timestamp()}",
            "sender_id": user_id,
            "recipient_id": recipient_id,
            "content": content,
            "message_type": message_type,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._store_message(recipient_id, chat_message)
        await self._store_message(user_id, chat_message)  # Also store for sender

        # Send to recipient
        await self.connection_manager.send_to_user(recipient_id, chat_message)

        # Confirm to sender
        await self.connection_manager.send_to_user(user_id, {
            **chat_message,
            "type": "chat_sent",
            "delivered": True,
        })

    async def _handle_chat_history(self, user_id: str, message: dict) -> None:
        """Handle request for chat history."""
        conversation_id = message.get("conversation_id")
        limit = message.get("limit", 50)
        offset = message.get("offset", 0)

        history = await self._get_history(user_id, conversation_id, limit, offset)

        await self.connection_manager.send_to_user(user_id, {
            "type": "chat_history",
            "conversation_id": conversation_id,
            "messages": history,
            "limit": limit,
            "offset": offset,
        })

    async def _handle_typing_indicator(self, user_id: str, message: dict) -> None:
        """Handle typing indicator."""
        recipient_id = message.get("recipient_id")
        is_typing = message.get("is_typing", False)

        if not recipient_id:
            return

        await self.connection_manager.send_to_user(recipient_id, {
            "type": "chat_typing",
            "sender_id": user_id,
            "recipient_id": recipient_id,
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def _handle_read_receipt(self, user_id: str, message: dict) -> None:
        """Handle read receipt."""
        message_ids = message.get("message_ids", [])
        sender_id = message.get("sender_id")

        if not message_ids or not sender_id:
            return

        # Store read receipts
        for msg_id in message_ids:
            key = f"chat:read:{msg_id}:{user_id}"
            await self.redis.set(key, "1", ex=86400 * 30)  # 30 days

        # Notify sender
        await self.connection_manager.send_to_user(sender_id, {
            "type": "chat_read",
            "reader_id": user_id,
            "message_ids": message_ids,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def _send_recent_history(self, user_id: str, connection_id: str) -> None:
        """Send recent chat history on connection."""
        history = await self._get_history(user_id, None, 20, 0)
        await self.connection_manager.send_to_connection(connection_id, {
            "type": "chat_history",
            "messages": history,
        })

    async def _store_message(self, user_id: str, message: dict) -> None:
        """Store a message in chat history."""
        conversation_key = f"chat:history:{user_id}"
        await self.redis.lpush(conversation_key, json.dumps(message))
        await self.redis.ltrim(conversation_key, 0, self.max_history - 1)
        await self.redis.expire(conversation_key, 86400 * 30)  # 30 days

    async def _get_history(self, user_id: str, conversation_id: str = None, limit: int = 50, offset: int = 0) -> list[dict]:
        """Get chat history for a user."""
        conversation_key = f"chat:history:{user_id}"
        messages = await self.redis.lrange(conversation_key, offset, offset + limit - 1)
        return [json.loads(msg) for msg in messages]
