"""
Transit WebSocket Handler

Handles real-time transit updates, alerts, and vehicle tracking.
"""
import json
from datetime import datetime

import redis.asyncio as redis
import structlog

from ws_service.connection_manager import ConnectionManager

logger = structlog.get_logger()


class TransitHandler:
    """Handles transit WebSocket connections and messages."""

    def __init__(self, connection_manager: ConnectionManager, redis_client: redis.Redis):
        self.connection_manager = connection_manager
        self.redis = redis_client
        self.alert_cooldown = 60  # seconds
        self._last_alert: dict[str, float] = {}  # alert_key -> timestamp

        # Register message handlers
        self.connection_manager.register_handler("transit_subscribe", self._handle_subscribe)
        self.connection_manager.register_handler("transit_unsubscribe", self._handle_unsubscribe)
        self.connection_manager.register_handler("transit_get_vehicles", self._handle_get_vehicles)
        self.connection_manager.register_handler("transit_get_predictions", self._handle_get_predictions)

    async def handle_connection(self, websocket, user_id: str) -> None:
        """Handle a new transit WebSocket connection."""
        connection_id = await self.connection_manager.connect(websocket, user_id, {"handler": "transit"})

        try:
            # Send welcome message
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "transit_welcome",
                "user_id": user_id,
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Listen for messages
            while True:
                data = await websocket.receive_json()
                await self.connection_manager.handle_message(user_id, data)

        except Exception as e:
            logger.error("Transit connection error", user_id=user_id, error=str(e))
        finally:
            await self.connection_manager.disconnect(connection_id)

    async def send_alert(
        self,
        user_ids: list[str],
        route_id: str,
        message: str,
        severity: str = "info",
        metadata: dict = None,
    ) -> dict:
        """Send a transit alert to users."""
        alert_key = f"{route_id}:{message}"
        now = datetime.utcnow().timestamp()
        last = self._last_alert.get(alert_key, 0)

        if now - last < self.alert_cooldown:
            return {"status": "cooldown", "route_id": route_id}

        self._last_alert[alert_key] = now

        alert = {
            "type": "transit_alert",
            "alert_id": f"alert_{now}",
            "route_id": route_id,
            "message": message,
            "severity": severity,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store alert
        await self._store_alert(alert)

        # Send to users
        sent = await self.connection_manager.broadcast_to_users(user_ids, alert)

        return {"status": "sent", "sent_to": sent, "alert_id": alert["alert_id"]}

    async def broadcast_vehicle_update(
        self,
        route_id: str,
        vehicle_id: str,
        latitude: float,
        longitude: float,
        heading: float,
        speed: float,
        occupancy: str = "unknown",
    ) -> dict:
        """Broadcast a vehicle position update."""
        update = {
            "type": "transit_vehicle_update",
            "route_id": route_id,
            "vehicle_id": vehicle_id,
            "latitude": latitude,
            "longitude": longitude,
            "heading": heading,
            "speed": speed,
            "occupancy": occupancy,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Get subscribers for this route
        subscribers = await self._get_route_subscribers(route_id)

        # Send to subscribers
        sent = await self.connection_manager.broadcast_to_users(subscribers, update)

        return {"status": "broadcast", "sent_to": sent, "route_id": route_id}

    async def _handle_subscribe(self, user_id: str, message: dict) -> None:
        """Handle subscription to transit updates."""
        route_id = message.get("route_id")
        stop_id = message.get("stop_id")

        if route_id:
            sub_key = f"transit:subscriptions:route:{route_id}"
            await self.redis.sadd(sub_key, user_id)
            await self.redis.expire(sub_key, 86400)  # 24 hours

        if stop_id:
            sub_key = f"transit:subscriptions:stop:{stop_id}"
            await self.redis.sadd(sub_key, user_id)
            await self.redis.expire(sub_key, 86400)

        # Send current status if available
        if route_id:
            vehicles = await self._get_route_vehicles(route_id)
            await self.connection_manager.send_to_user(user_id, {
                "type": "transit_vehicles",
                "route_id": route_id,
                "vehicles": vehicles,
            })

    async def _handle_unsubscribe(self, user_id: str, message: dict) -> None:
        """Handle unsubscription from transit updates."""
        route_id = message.get("route_id")
        stop_id = message.get("stop_id")

        if route_id:
            sub_key = f"transit:subscriptions:route:{route_id}"
            await self.redis.srem(sub_key, user_id)

        if stop_id:
            sub_key = f"transit:subscriptions:stop:{stop_id}"
            await self.redis.srem(sub_key, user_id)

    async def _handle_get_vehicles(self, user_id: str, message: dict) -> None:
        """Handle request for vehicles on a route."""
        route_id = message.get("route_id")
        if not route_id:
            return

        vehicles = await self._get_route_vehicles(route_id)
        await self.connection_manager.send_to_user(user_id, {
            "type": "transit_vehicles",
            "route_id": route_id,
            "vehicles": vehicles,
        })

    async def _handle_get_predictions(self, user_id: str, message: dict) -> None:
        """Handle request for arrival predictions."""
        stop_id = message.get("stop_id")
        route_id = message.get("route_id")
        if not stop_id:
            return

        predictions = await self._get_stop_predictions(stop_id, route_id)
        await self.connection_manager.send_to_user(user_id, {
            "type": "transit_predictions",
            "stop_id": stop_id,
            "route_id": route_id,
            "predictions": predictions,
        })

    async def _store_alert(self, alert: dict) -> None:
        """Store alert in history."""
        key = "transit:alerts:history"
        await self.redis.lpush(key, json.dumps(alert))
        await self.redis.ltrim(key, 0, 99)  # Keep last 100
        await self.redis.expire(key, 86400 * 7)  # 7 days

    async def _get_route_subscribers(self, route_id: str) -> list[str]:
        """Get subscribers for a route."""
        sub_key = f"transit:subscriptions:route:{route_id}"
        return list(await self.redis.smembers(sub_key))

    async def _get_route_vehicles(self, route_id: str) -> list[dict]:
        """Get current vehicles for a route."""
        key = f"transit:vehicles:{route_id}"
        vehicles = await self.redis.hgetall(key)
        return [
            {
                "vehicle_id": vid,
                "latitude": float(data.get("latitude", 0)),
                "longitude": float(data.get("longitude", 0)),
                "heading": float(data.get("heading", 0)),
                "speed": float(data.get("speed", 0)),
                "occupancy": data.get("occupancy", "unknown"),
                "updated_at": float(data.get("updated_at", 0)),
            }
            for vid, data in vehicles.items()
        ]

    async def _get_stop_predictions(self, stop_id: str, route_id: str | None = None) -> list[dict]:
        """Get arrival predictions for a stop."""
        # This would integrate with GTFS-realtime in production
        # For now, return mock data
        return [
            {
                "route_id": route_id or "unknown",
                "trip_id": "trip_123",
                "vehicle_id": "vehicle_456",
                "predicted_arrival": datetime.utcnow().isoformat(),
                "scheduled_arrival": datetime.utcnow().isoformat(),
                "delay_seconds": 0,
            }
        ]

    async def update_vehicle_position(
        self,
        route_id: str,
        vehicle_id: str,
        latitude: float,
        longitude: float,
        heading: float,
        speed: float,
        occupancy: str = "unknown",
    ) -> None:
        """Update vehicle position (called from external GTFS processor)."""
        key = f"transit:vehicles:{route_id}"
        await self.redis.hset(key, vehicle_id, json.dumps({
            "latitude": str(latitude),
            "longitude": str(longitude),
            "heading": str(heading),
            "speed": str(speed),
            "occupancy": occupancy,
            "updated_at": str(datetime.utcnow().timestamp()),
        }))
        await self.redis.expire(key, 300)  # 5 minutes

        # Broadcast to subscribers
        await self.broadcast_vehicle_update(route_id, vehicle_id, latitude, longitude, heading, speed, occupancy)
