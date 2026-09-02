"""
WebSocket Location Handler
Handles real-time location sharing and nearby user discovery
"""
import logging
from datetime import datetime
from uuid import UUID

from ...schemas.messages import WSAck, WSError, WSLocationUpdate, WSMessage, WSMessageType
from .connection_manager import connection_manager

logger = logging.getLogger(__name__)


class LocationHandler:
    """Handles location-related WebSocket messages"""

    def __init__(self):
        self.location_room = "location:global"
        self._initialized = False

    async def initialize(self):
        """Initialize location room"""
        if not self._initialized:
            await connection_manager.create_room(
                room_id=self.location_room,
                name="Global Location Updates",
                type="location",
            )
            self._initialized = True

    async def handle_message(self, connection_id: UUID, message: WSMessage) -> WSMessage | None:
        """Route location message to appropriate handler"""
        msg_type = message.type

        if msg_type == WSMessageType.LOCATION_UPDATE:
            return await self.handle_location_update(connection_id, message)
        elif msg_type == WSMessageType.LOCATION_SUBSCRIBE:
            return await self.handle_subscribe(connection_id, message)
        elif msg_type == WSMessageType.LOCATION_UNSUBSCRIBE:
            return await self.handle_unsubscribe(connection_id, message)
        elif msg_type == WSMessageType.NEARBY_USERS:
            return await self.handle_nearby_users(connection_id, message)

        return None

    async def handle_location_update(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle location update from user"""
        try:
            location_update = WSLocationUpdate(**message.payload)
        except Exception as e:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="INVALID_MESSAGE", message=str(e)).model_dump(),
                correlation_id=message.message_id,
            )

        # Update connection activity
        await connection_manager.update_activity(connection_id)

        # Broadcast to location subscribers
        update_msg = WSMessage(
            type=WSMessageType.LOCATION_UPDATE,
            payload={
                "user_id": str(location_update.user_id),
                "latitude": location_update.latitude,
                "longitude": location_update.longitude,
                "accuracy": location_update.accuracy,
                "heading": location_update.heading,
                "speed": location_update.speed,
                "altitude": location_update.altitude,
                "timestamp": location_update.timestamp.isoformat(),
            },
        )

        # Get subscribers interested in this area
        await connection_manager.get_subscribers(
            "location",
            filters={"area": self._get_area_key(location_update.latitude, location_update.longitude)}
        )

        # Also broadcast to global location room
        await connection_manager.broadcast_to_room(self.location_room, update_msg)

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_subscribe(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle location subscription"""
        filters = message.payload.get("filters", {})

        # Subscribe to location updates
        subscription_id = await connection_manager.subscribe(
            connection_id=connection_id,
            sub_type="location",
            filters=filters,
        )

        # Also join global location room
        await connection_manager.join_room(connection_id, self.location_room)

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(
                original_message_id=message.message_id or "",
                success=True,
                data={"subscription_id": subscription_id},
            ).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_unsubscribe(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle location unsubscription"""
        await connection_manager.unsubscribe(connection_id, "location")
        await connection_manager.leave_room(connection_id, self.location_room)

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_nearby_users(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle nearby users request"""
        latitude = message.payload.get("latitude")
        longitude = message.payload.get("longitude")
        radius_meters = message.payload.get("radius_meters", 1000)
        message.payload.get("limit", 50)

        if latitude is None or longitude is None:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="latitude and longitude required").model_dump(),
                correlation_id=message.message_id,
            )

        # Get all connections in location room
        # In production, this would query a spatial index
        nearby_users = []

        # For now, return empty list
        response = WSMessage(
            type=WSMessageType.NEARBY_USERS,
            payload={
                "users": nearby_users,
                "center": {"latitude": latitude, "longitude": longitude},
                "radius_meters": radius_meters,
            },
            correlation_id=message.message_id,
        )

        return response

    def _get_area_key(self, latitude: float, longitude: float, grid_size: float = 0.01) -> str:
        """Get grid area key for location"""
        lat_grid = int(latitude / grid_size)
        lng_grid = int(longitude / grid_size)
        return f"{lat_grid},{lng_grid}"

    async def broadcast_location_update(self, user_id: UUID, latitude: float, longitude: float,
                                       accuracy: float | None = None,
                                       heading: float | None = None,
                                       speed: float | None = None) -> int:
        """Broadcast location update to subscribers"""
        update_msg = WSMessage(
            type=WSMessageType.LOCATION_UPDATE,
            payload={
                "user_id": str(user_id),
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": accuracy,
                "heading": heading,
                "speed": speed,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return await connection_manager.broadcast_to_room(self.location_room, update_msg)


# Global location handler instance
location_handler = LocationHandler()
