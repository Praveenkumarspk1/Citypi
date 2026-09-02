"""
Notification WebSocket Handler

Handles real-time push notifications and in-app alerts.
"""
import json
from datetime import datetime

import redis.asyncio as redis
import structlog

from ws_service.connection_manager import ConnectionManager

logger = structlog.get_logger()


class NotificationHandler:
    """Handles notification WebSocket connections and messages."""

    def __init__(self, connection_manager: ConnectionManager, redis_client: redis.Redis):
        self.connection_manager = connection_manager
        self.redis = redis_client
        self.notification_ttl = 86400  # 24 hours

        # Register message handlers
        self.connection_manager.register_handler("notification_ack", self._handle_ack)
        self.connection_manager.register_handler("notification_list", self._handle_list)
        self.connection_manager.register_handler("notification_mark_read", self._handle_mark_read)
        self.connection_manager.register_handler("notification_delete", self._handle_delete)

    async def handle_connection(self, websocket, user_id: str) -> None:
        """Handle a new notification WebSocket connection."""
        connection_id = await self.connection_manager.connect(websocket, user_id, {"handler": "notification"})

        try:
            # Send welcome message
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "notification_welcome",
                "user_id": user_id,
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Send unread count
            unread_count = await self._get_unread_count(user_id)
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "notification_unread_count",
                "count": unread_count,
            })

            # Listen for messages
            while True:
                data = await websocket.receive_json()
                await self.connection_manager.handle_message(user_id, data)

        except Exception as e:
            logger.error("Notification connection error", user_id=user_id, error=str(e))
        finally:
            await self.connection_manager.disconnect(connection_id)

    async def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        notification_type: str = "info",
        data: dict = None,
        priority: str = "normal",
        action_url: str = None,
    ) -> dict:
        """Send a notification to a user."""
        notification = {
            "type": "notification",
            "notification_id": f"notif_{datetime.utcnow().timestamp()}",
            "user_id": user_id,
            "title": title,
            "body": body,
            "notification_type": notification_type,
            "data": data or {},
            "priority": priority,
            "action_url": action_url,
            "read": False,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store notification
        await self._store_notification(user_id, notification)

        # Send to user if online
        sent = await self.connection_manager.send_to_user(user_id, notification)

        # Update unread count
        unread_count = await self._get_unread_count(user_id)
        await self.connection_manager.send_to_user(user_id, {
            "type": "notification_unread_count",
            "count": unread_count,
        })

        return {"status": "sent", "delivered": sent > 0, "notification_id": notification["notification_id"]}

    async def broadcast_notification(
        self,
        user_ids: list[str],
        title: str,
        body: str,
        notification_type: str = "info",
        data: dict = None,
        priority: str = "normal",
    ) -> dict:
        """Broadcast a notification to multiple users."""
        results = []
        for user_id in user_ids:
            result = await self.send_notification(user_id, title, body, notification_type, data, priority)
            results.append(result)

        return {"status": "broadcast", "results": results}

    async def _handle_ack(self, user_id: str, message: dict) -> None:
        """Handle notification acknowledgment."""
        notification_id = message.get("notification_id")
        if notification_id:
            await self._mark_read(user_id, notification_id)

    async def _handle_list(self, user_id: str, message: dict) -> None:
        """Handle request for notification list."""
        limit = message.get("limit", 50)
        offset = message.get("offset", 0)
        unread_only = message.get("unread_only", False)

        notifications = await self._get_notifications(user_id, limit, offset, unread_only)
        unread_count = await self._get_unread_count(user_id)

        await self.connection_manager.send_to_user(user_id, {
            "type": "notification_list",
            "notifications": notifications,
            "unread_count": unread_count,
            "limit": limit,
            "offset": offset,
        })

    async def _handle_mark_read(self, user_id: str, message: dict) -> None:
        """Handle mark notification as read."""
        notification_ids = message.get("notification_ids", [])
        for notification_id in notification_ids:
            await self._mark_read(user_id, notification_id)

        unread_count = await self._get_unread_count(user_id)
        await self.connection_manager.send_to_user(user_id, {
            "type": "notification_unread_count",
            "count": unread_count,
        })

    async def _handle_delete(self, user_id: str, message: dict) -> None:
        """Handle notification deletion."""
        notification_ids = message.get("notification_ids", [])
        for notification_id in notification_ids:
            await self._delete_notification(user_id, notification_id)

        unread_count = await self._get_unread_count(user_id)
        await self.connection_manager.send_to_user(user_id, {
            "type": "notification_unread_count",
            "count": unread_count,
        })

    async def _store_notification(self, user_id: str, notification: dict) -> None:
        """Store notification in user's inbox."""
        key = f"notification:inbox:{user_id}"
        await self.redis.lpush(key, json.dumps(notification))
        await self.redis.ltrim(key, 0, 99)  # Keep last 100
        await self.redis.expire(key, self.notification_ttl)

        # Also store in unread set
        unread_key = f"notification:unread:{user_id}"
        await self.redis.sadd(unread_key, notification["notification_id"])
        await self.redis.expire(unread_key, self.notification_ttl)

    async def _mark_read(self, user_id: str, notification_id: str) -> None:
        """Mark notification as read."""
        unread_key = f"notification:unread:{user_id}"
        await self.redis.srem(unread_key, notification_id)

        # Update in inbox
        key = f"notification:inbox:{user_id}"
        notifications = await self.redis.lrange(key, 0, -1)
        for i, notif_json in enumerate(notifications):
            notif = json.loads(notif_json)
            if notif.get("notification_id") == notification_id:
                notif["read"] = True
                await self.redis.lset(key, i, json.dumps(notif))
                break

    async def _delete_notification(self, user_id: str, notification_id: str) -> None:
        """Delete a notification."""
        unread_key = f"notification:unread:{user_id}"
        await self.redis.srem(unread_key, notification_id)

        key = f"notification:inbox:{user_id}"
        notifications = await self.redis.lrange(key, 0, -1)
        for notif_json in notifications:
            notif = json.loads(notif_json)
            if notif.get("notification_id") == notification_id:
                await self.redis.lrem(key, 1, notif_json)
                break

    async def _get_notifications(self, user_id: str, limit: int, offset: int, unread_only: bool) -> list[dict]:
        """Get notifications for a user."""
        key = f"notification:inbox:{user_id}"
        notifications = await self.redis.lrange(key, offset, offset + limit - 1)
        result = [json.loads(n) for n in notifications]

        if unread_only:
            unread_key = f"notification:unread:{user_id}"
            unread_ids = await self.redis.smembers(unread_key)
            result = [n for n in result if n.get("notification_id") in unread_ids]

        return result

    async def _get_unread_count(self, user_id: str) -> int:
        """Get unread notification count for a user."""
        unread_key = f"notification:unread:{user_id}"
        return await self.redis.scard(unread_key)
