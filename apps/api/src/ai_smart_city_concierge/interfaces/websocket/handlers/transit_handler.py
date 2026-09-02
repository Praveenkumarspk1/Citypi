"""
WebSocket Transit Handler
Handles real-time transit updates (vehicle positions, trip updates, service alerts)
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from ...schemas.messages import WSAck, WSError, WSMessage, WSMessageType, WSTransitUpdate
from .connection_manager import connection_manager

logger = logging.getLogger(__name__)


class TransitHandler:
    """Handles transit-related WebSocket messages"""

    def __init__(self):
        self.transit_rooms: dict[str, str] = {}  # route_id -> room_id
        self._initialized = False

    async def initialize(self):
        """Initialize transit rooms"""
        if not self._initialized:
            # Create global transit room
            await connection_manager.create_room(
                room_id="transit:global",
                name="Global Transit Updates",
                type="transit",
            )
            self._initialized = True

    async def handle_message(self, connection_id: UUID, message: WSMessage) -> WSMessage | None:
        """Route transit message to appropriate handler"""
        msg_type = message.type

        if msg_type == WSMessageType.TRANSIT_SUBSCRIBE:
            return await self.handle_subscribe(connection_id, message)
        elif msg_type == WSMessageType.TRANSIT_UNSUBSCRIBE:
            return await self.handle_unsubscribe(connection_id, message)
        elif msg_type == WSMessageType.VEHICLE_POSITION:
            return await self.handle_vehicle_position(connection_id, message)
        elif msg_type == WSMessageType.TRIP_UPDATE:
            return await self.handle_trip_update(connection_id, message)
        elif msg_type == WSMessageType.SERVICE_ALERT:
            return await self.handle_service_alert(connection_id, message)

        return None

    async def handle_subscribe(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle transit subscription"""
        route_id = message.payload.get("route_id")
        stop_id = message.payload.get("stop_id")
        agency_id = message.payload.get("agency_id")

        filters = {}
        if route_id:
            filters["route_id"] = route_id
        if stop_id:
            filters["stop_id"] = stop_id
        if agency_id:
            filters["agency_id"] = agency_id

        # Subscribe to transit updates
        subscription_id = await connection_manager.subscribe(
            connection_id=connection_id,
            sub_type="transit",
            filters=filters,
        )

        # Join relevant rooms
        if route_id:
            room_id = await self._get_or_create_route_room(route_id)
            await connection_manager.join_room(connection_id, room_id)

        # Join global transit room
        await connection_manager.join_room(connection_id, "transit:global")

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
        """Handle transit unsubscription"""
        route_id = message.payload.get("route_id")

        await connection_manager.unsubscribe(connection_id, "transit")

        if route_id:
            room_id = f"transit:route:{route_id}"
            await connection_manager.leave_room(connection_id, room_id)

        await connection_manager.leave_room(connection_id, "transit:global")

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_vehicle_position(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle vehicle position update (from GTFS-realtime feed)"""
        try:
            transit_update = WSTransitUpdate(**message.payload)
        except Exception as e:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="INVALID_MESSAGE", message=str(e)).model_dump(),
                correlation_id=message.message_id,
            )

        # Broadcast to route-specific room
        if transit_update.route_id:
            room_id = await self._get_or_create_route_room(transit_update.route_id)

            position_msg = WSMessage(
                type=WSMessageType.VEHICLE_POSITION,
                payload={
                    "route_id": transit_update.route_id,
                    "vehicle_id": transit_update.vehicle_id,
                    "trip_id": transit_update.trip_id,
                    "latitude": transit_update.latitude,
                    "longitude": transit_update.longitude,
                    "bearing": transit_update.bearing,
                    "speed": transit_update.speed,
                    "occupancy": transit_update.occupancy,
                    "timestamp": transit_update.timestamp.isoformat(),
                },
            )

            await connection_manager.broadcast_to_room(room_id, position_msg)

        # Also broadcast to global transit room
        await connection_manager.broadcast_to_room("transit:global", position_msg)

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_trip_update(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle trip update (delays, cancellations, etc.)"""
        trip_id = message.payload.get("trip_id")
        route_id = message.payload.get("route_id")
        delay_seconds = message.payload.get("delay_seconds")
        stop_time_updates = message.payload.get("stop_time_updates", [])

        if not trip_id or not route_id:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="trip_id and route_id required").model_dump(),
                correlation_id=message.message_id,
            )

        room_id = await self._get_or_create_route_room(route_id)

        trip_msg = WSMessage(
            type=WSMessageType.TRIP_UPDATE,
            payload={
                "trip_id": trip_id,
                "route_id": route_id,
                "delay_seconds": delay_seconds,
                "stop_time_updates": stop_time_updates,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        await connection_manager.broadcast_to_room(room_id, trip_msg)
        await connection_manager.broadcast_to_room("transit:global", trip_msg)

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def handle_service_alert(self, connection_id: UUID, message: WSMessage) -> WSMessage:
        """Handle service alert"""
        alert_id = message.payload.get("alert_id")
        cause = message.payload.get("cause")
        effect = message.payload.get("effect")
        description = message.payload.get("description")
        affected_routes = message.payload.get("affected_routes", [])
        affected_stops = message.payload.get("affected_stops", [])
        severity = message.payload.get("severity", "medium")

        if not alert_id:
            return WSMessage(
                type=WSMessageType.ERROR,
                payload=WSError(code="MISSING_PARAMETER", message="alert_id required").model_dump(),
                correlation_id=message.message_id,
            )

        alert_msg = WSMessage(
            type=WSMessageType.SERVICE_ALERT,
            payload={
                "alert_id": alert_id,
                "cause": cause,
                "effect": effect,
                "description": description,
                "affected_routes": affected_routes,
                "affected_stops": affected_stops,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Broadcast to affected route rooms
        for route_id in affected_routes:
            room_id = await self._get_or_create_route_room(route_id)
            await connection_manager.broadcast_to_room(room_id, alert_msg)

        # Broadcast to global transit room
        await connection_manager.broadcast_to_room("transit:global", alert_msg)

        return WSMessage(
            type=WSMessageType.ACK,
            payload=WSAck(original_message_id=message.message_id or "", success=True).model_dump(),
            correlation_id=message.message_id,
        )

    async def _get_or_create_route_room(self, route_id: str) -> str:
        """Get or create room for transit route"""
        if route_id in self.transit_rooms:
            return self.transit_rooms[route_id]

        room_id = f"transit:route:{route_id}"
        await connection_manager.create_room(
            room_id=room_id,
            name=f"Route {route_id} Updates",
            type="transit",
        )
        self.transit_rooms[route_id] = room_id
        return room_id

    async def broadcast_vehicle_position(self, route_id: str, vehicle_id: str, trip_id: str,
                                        latitude: float, longitude: float,
                                        bearing: float | None = None,
                                        speed: float | None = None,
                                        occupancy: str | None = None) -> int:
        """Broadcast vehicle position to route subscribers"""
        room_id = await self._get_or_create_route_room(route_id)

        msg = WSMessage(
            type=WSMessageType.VEHICLE_POSITION,
            payload={
                "route_id": route_id,
                "vehicle_id": vehicle_id,
                "trip_id": trip_id,
                "latitude": latitude,
                "longitude": longitude,
                "bearing": bearing,
                "speed": speed,
                "occupancy": occupancy,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return await connection_manager.broadcast_to_room(room_id, msg)

    async def broadcast_trip_update(self, route_id: str, trip_id: str, delay_seconds: int,
                                   stop_time_updates: list[dict[str, Any]]) -> int:
        """Broadcast trip update to route subscribers"""
        room_id = await self._get_or_create_route_room(route_id)

        msg = WSMessage(
            type=WSMessageType.TRIP_UPDATE,
            payload={
                "trip_id": trip_id,
                "route_id": route_id,
                "delay_seconds": delay_seconds,
                "stop_time_updates": stop_time_updates,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return await connection_manager.broadcast_to_room(room_id, msg)

    async def broadcast_service_alert(self, alert_id: str, cause: str, effect: str,
                                     description: str, affected_routes: list[str],
                                     affected_stops: list[str], severity: str = "medium") -> int:
        """Broadcast service alert to affected routes"""
        alert_msg = WSMessage(
            type=WSMessageType.SERVICE_ALERT,
            payload={
                "alert_id": alert_id,
                "cause": cause,
                "effect": effect,
                "description": description,
                "affected_routes": affected_routes,
                "affected_stops": affected_stops,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        total_sent = 0
        for route_id in affected_routes:
            room_id = await self._get_or_create_route_room(route_id)
            total_sent += await connection_manager.broadcast_to_room(room_id, alert_msg)

        # Also broadcast globally
        total_sent += await connection_manager.broadcast_to_room("transit:global", alert_msg)

        return total_sent


# Global transit handler instance
transit_handler = TransitHandler()
