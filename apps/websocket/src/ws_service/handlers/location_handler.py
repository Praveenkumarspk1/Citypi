"""
Location WebSocket Handler

Handles real-time location sharing and proximity updates.
"""
from datetime import datetime

import redis.asyncio as redis
import structlog

from ws_service.connection_manager import ConnectionManager

logger = structlog.get_logger()


class LocationHandler:
    """Handles location sharing WebSocket connections and messages."""

    def __init__(self, connection_manager: ConnectionManager, redis_client: redis.Redis):
        self.connection_manager = connection_manager
        self.redis = redis_client
        self.broadcast_radius = 1000.0  # meters
        self.update_throttle = 5  # seconds
        self._last_update: dict[str, float] = {}  # user_id -> timestamp

        # Register message handlers
        self.connection_manager.register_handler("location_update", self._handle_location_update)
        self.connection_manager.register_handler("location_subscribe", self._handle_subscribe)
        self.connection_manager.register_handler("location_unsubscribe", self._handle_unsubscribe)
        self.connection_manager.register_handler("location_get_nearby", self._handle_get_nearby)

    async def handle_connection(self, websocket, user_id: str) -> None:
        """Handle a new location WebSocket connection."""
        connection_id = await self.connection_manager.connect(websocket, user_id, {"handler": "location"})

        try:
            # Send welcome message
            await self.connection_manager.send_to_connection(connection_id, {
                "type": "location_welcome",
                "user_id": user_id,
                "connection_id": connection_id,
                "broadcast_radius": self.broadcast_radius,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Listen for messages
            while True:
                data = await websocket.receive_json()
                await self.connection_manager.handle_message(user_id, data)

        except Exception as e:
            logger.error("Location connection error", user_id=user_id, error=str(e))
        finally:
            await self.connection_manager.disconnect(connection_id)

    async def broadcast_location(
        self,
        user_id: str,
        latitude: float,
        longitude: float,
        accuracy: float | None = None,
        heading: float | None = None,
        speed: float | None = None,
    ) -> dict:
        """Broadcast a location update to nearby users."""
        # Throttle updates
        now = datetime.utcnow().timestamp()
        last = self._last_update.get(user_id, 0)
        if now - last < self.update_throttle:
            return {"status": "throttled", "user_id": user_id}

        self._last_update[user_id] = now

        location_data = {
            "type": "location_update",
            "user_id": user_id,
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": accuracy,
            "heading": heading,
            "speed": speed,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store location in Redis for proximity queries
        await self._store_location(user_id, latitude, longitude, accuracy)

        # Find nearby users
        nearby_users = await self._get_nearby_users(latitude, longitude, self.broadcast_radius)

        # Broadcast to nearby users (excluding sender)
        sent = await self.connection_manager.broadcast_to_users(
            [u for u in nearby_users if u != user_id],
            location_data,
        )

        return {"status": "broadcast", "sent_to": sent, "user_id": user_id}

    async def _handle_location_update(self, user_id: str, message: dict) -> None:
        """Handle incoming location update."""
        latitude = message.get("latitude")
        longitude = message.get("longitude")
        accuracy = message.get("accuracy")
        heading = message.get("heading")
        speed = message.get("speed")

        if latitude is None or longitude is None:
            logger.warning("Invalid location update", user_id=user_id)
            return

        await self.broadcast_location(user_id, latitude, longitude, accuracy, heading, speed)

    async def _handle_subscribe(self, user_id: str, message: dict) -> None:
        """Handle subscription to location updates."""
        target_user_id = message.get("target_user_id")
        radius = message.get("radius", self.broadcast_radius)

        if not target_user_id:
            return

        # Store subscription
        sub_key = f"location:subscriptions:{user_id}"
        await self.redis.hset(sub_key, target_user_id, str(radius))
        await self.redis.expire(sub_key, 86400)  # 24 hours

        # Send current location if available
        location = await self._get_location(target_user_id)
        if location:
            await self.connection_manager.send_to_user(user_id, {
                "type": "location_update",
                "user_id": target_user_id,
                **location,
            })

    async def _handle_unsubscribe(self, user_id: str, message: dict) -> None:
        """Handle unsubscription from location updates."""
        target_user_id = message.get("target_user_id")

        if not target_user_id:
            return

        sub_key = f"location:subscriptions:{user_id}"
        await self.redis.hdel(sub_key, target_user_id)

    async def _handle_get_nearby(self, user_id: str, message: dict) -> None:
        """Handle request for nearby users."""
        latitude = message.get("latitude")
        longitude = message.get("longitude")
        radius = message.get("radius", self.broadcast_radius)
        limit = message.get("limit", 50)

        if latitude is None or longitude is None:
            return

        nearby_users = await self._get_nearby_users(latitude, longitude, radius, limit)

        # Get their locations
        users_data = []
        for nearby_user_id in nearby_users:
            if nearby_user_id != user_id:
                location = await self._get_location(nearby_user_id)
                if location:
                    users_data.append({
                        "user_id": nearby_user_id,
                        **location,
                    })

        await self.connection_manager.send_to_user(user_id, {
            "type": "location_nearby",
            "users": users_data,
            "count": len(users_data),
        })

    async def _store_location(self, user_id: str, latitude: float, longitude: float, accuracy: float | None) -> None:
        """Store user location in Redis with geospatial index."""
        # Store in sorted set for geospatial queries
        key = "location:users"
        member = f"{user_id}:{latitude}:{longitude}"
        await self.redis.zadd(key, {member: datetime.utcnow().timestamp()})
        await self.redis.expire(key, 3600)  # 1 hour

        # Also store detailed location
        detail_key = f"location:detail:{user_id}"
        await self.redis.hset(detail_key, mapping={
            "latitude": str(latitude),
            "longitude": str(longitude),
            "accuracy": str(accuracy) if accuracy else "",
            "updated_at": str(datetime.utcnow().timestamp()),
        })
        await self.redis.expire(detail_key, 3600)

    async def _get_location(self, user_id: str) -> dict | None:
        """Get stored location for a user."""
        detail_key = f"location:detail:{user_id}"
        data = await self.redis.hgetall(detail_key)
        if not data:
            return None
        return {
            "latitude": float(data.get("latitude", 0)),
            "longitude": float(data.get("longitude", 0)),
            "accuracy": float(data.get("accuracy", 0)) if data.get("accuracy") else None,
            "updated_at": float(data.get("updated_at", 0)),
        }

    async def _get_nearby_users(self, latitude: float, longitude: float, radius: float, limit: int = 50) -> list[str]:
        """Get users within radius (simplified - in production use Redis GEO commands)."""
        # This is a simplified implementation
        # In production, use Redis GEORADIUS or similar
        key = "location:users"
        members = await self.redis.zrange(key, 0, -1)

        nearby = []
        for member in members:
            parts = member.split(":")
            if len(parts) >= 3:
                user_id = parts[0]
                lat = float(parts[1])
                lng = float(parts[2])

                # Simple distance calculation (Haversine would be better)
                distance = self._calculate_distance(latitude, longitude, lat, lng)
                if distance <= radius:
                    nearby.append(user_id)
                    if len(nearby) >= limit:
                        break

        return nearby

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters (simplified)."""
        from math import atan2, cos, radians, sin, sqrt

        R = 6371000  # Earth radius in meters
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
