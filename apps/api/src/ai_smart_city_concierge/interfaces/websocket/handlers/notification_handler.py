"""
WebSocket Notification Handler
Handles real-time notifications and alerts
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from ...schemas.messages import WSAck, WSError, WSMessage, WSMessageType, WSNotification
from .connection_manager import connection_manager

logger = logging.getLogger(__name__)


class NotificationHandler:
    """Handles notification-related WebSocket messages"""

    def __init__(self):
        self.notification_room = "notifications:global"
        self._initialized = False

    async def initialize(self):
        """Initialize notification room"""
        if not self._initialized:
            await connection_manager.create_room(
                room_id=self.notification_room,
                name="Global Notifications",
                type="notification",
            )
            self._initialized = True

    async def handle_message(self, connection_id: UUID, message: WSMessage) -> WSMessage | None:
        """Route notification message to appropriate handler"""
        msg_type = message.type

        if msg_type == WSMessageType.NOTIFICATION:
            return await self.handle_notification(connection_id, message)
        elif msg_type == WSMessageType.NOTIFICATION_READ:
            return await self.handle_notification_read(connection_id, message)

        return None

    async def handle_notification(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle incoming notification (typically from server)"""
        try:
            notification = WSNotification(**message.payload)
        except Exception as e:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="INVALID_MESSAGE", message=str(e)).model_dump(),
                correlation_id=message.message_id,
            )

        # Broadcast to user's connections
        sent = await connection_manager.send_to_user(notification.notification_id, message)

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(
                original_message_id=message.message_id or "",
                success=True,
                data={"delivered_to": sent},
            ).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_notification_read(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle notification read receipt"""
        notification_id = message.payload.get("notification_id")

        if not notification_id:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="notification_id required").model_dump(),
                correlation_id=message.message_id,
            )

        # In production, update database
        # For now, just acknowledge
        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def send_notification(self, user_id: UUID, notification: WSNotification) -> int:
        """Send notification to specific user"""
        msg = WSMessage(
            type=WSMessageType.NOTIFICATION,
            payload=notification.model_dump(),
        )

        return await connection_manager.send_to_user(user_id, msg)

    async def broadcast_notification(self, notification: WSNotification,
                                    exclude: list[UUID] | None = None) -> int:
        """Broadcast notification to all connected users"""
        msg = WSMessage(
            type=WSMessageType.NOTIFICATION,
            payload=notification.model_dump(),
        )

        exclude_set = set(exclude) if exclude else None
        return await connection_manager.broadcast(msg, exclude=exclude_set)

    async def send_system_notification(self, user_id: UUID, title: str, body: str,
                                      notification_type: str = "system",
                                      data: dict[str, Any] | None = None,
                                      priority: str = "normal") -> int:
        """Send system notification to user"""
        notification = WSNotification(
            notification_id=UUID(int=0),  # Will be replaced by server
            type=notification_type,
            title=title,
            body=body,
            data=data or {},
            priority=priority,
            timestamp=datetime.utcnow(),
        )

        return await self.send_notification(user_id, notification)

    async def send_poi_notification(self, user_id: UUID, poi_id: UUID, poi_name: str,
                                   action: str, data: dict[str, Any] | None = None) -> int:
        """Send POI-related notification"""
        notification = WSNotification(
            notification_id=UUID(int=0),
            type="poi",
            title=f"POI {action}",
            body=f"{poi_name} has been {action}",
            data={"poi_id": str(poi_id), "action": action, **(data or {})},
            priority="normal",
            timestamp=datetime.utcnow(),
        )

        return await self.send_notification(user_id, notification)

    async def send_itinerary_notification(self, user_id: UUID, itinerary_id: UUID,
                                         action: str, data: dict[str, Any] | None = None) -> int:
        """Send itinerary-related notification"""
        notification = WSNotification(
            notification_id=UUID(int=0),
            type="itinerary",
            title=f"Itinerary {action}",
            body=f"Your itinerary has been {action}",
            data={"itinerary_id": str(itinerary_id), "action": action, **(data or {})},
            priority="normal",
            timestamp=datetime.utcnow(),
        )

        return await self.send_notification(user_id, notification)

    async def send_transit_notification(self, user_id: UUID, route_id: str,
                                       alert_type: str, message: str,
                                       data: dict[str, Any] | None = None) -> int:
        """Send transit-related notification"""
        notification = WSNotification(
            notification_id=UUID(int=0),
            type="transit",
            title=f"Transit Alert: {alert_type}",
            body=message,
            data={"route_id": route_id, "alert_type": alert_type, **(data or {})},
            priority="high",
            timestamp=datetime.utcnow(),
        )

        return await self.send_notification(user_id, notification)

    async def send_weather_alert(self, user_id: UUID, alert_type: str, message: str,
                                severity: str, data: dict[str, Any] | None = None) -> int:
        """Send weather alert notification"""
        priority_map = {
            "minor": "low",
            "moderate": "normal",
            "severe": "high",
            "extreme": "urgent",
        }

        notification = WSNotification(
            notification_id=UUID(int=0),
            type="weather",
            title=f"Weather Alert: {alert_type}",
            body=message,
            data={"alert_type": alert_type, "severity": severity, **(data or {})},
            priority=priority_map.get(severity, "normal"),
            timestamp=datetime.utcnow(),
        )

        return await self.send_notification(user_id, notification)


# Global notification handler instance
notification_handler = NotificationHandler()
