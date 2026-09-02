"""
Redis Configuration and Client Management
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis

from .settings import get_settings

settings = get_settings()


# Global connection pool
_redis_pool: ConnectionPool | None = None
_redis_client: Redis | None = None


def get_redis_pool() -> ConnectionPool:
    """Get or create Redis connection pool"""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            settings.redis.url,
            max_connections=settings.redis.max_connections,
            socket_timeout=settings.redis.socket_timeout,
            socket_connect_timeout=settings.redis.socket_connect_timeout,
            decode_responses=settings.redis.decode_responses,
        )
    return _redis_pool


def get_redis_client() -> Redis:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(connection_pool=get_redis_pool())
    return _redis_client


async def close_redis() -> None:
    """Close Redis connections"""
    global _redis_pool, _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None


@asynccontextmanager
async def get_redis() -> AsyncGenerator[Redis, None]:
    """Context manager for Redis client"""
    client = get_redis_client()
    try:
        yield client
    finally:
        pass  # Connection returned to pool automatically


# Redis key prefixes for namespacing
class RedisKeys:
    """Redis key prefixes for different data types"""

    # Sessions
    USER_SESSION = "session:user:{user_id}"
    REFRESH_TOKEN = "token:refresh:{token_hash}"

    # Caching
    POI_SEARCH = "cache:poi:search:{query_hash}"
    POI_DETAILS = "cache:poi:details:{poi_id}"
    TRANSIT_ROUTES = "cache:transit:routes:{origin_hash}:{dest_hash}"
    WEATHER_CURRENT = "cache:weather:current:{lat}:{lng}"
    WEATHER_FORECAST = "cache:weather:forecast:{lat}:{lng}:{days}"
    USER_PREFERENCES = "cache:user:preferences:{user_id}"
    ITINERARY = "cache:itinerary:{itinerary_id}"

    # Rate limiting
    RATE_LIMIT = "ratelimit:{endpoint}:{identifier}"

    # WebSocket
    WS_CONNECTION = "ws:connection:{connection_id}"
    WS_USER_CONNECTIONS = "ws:user:{user_id}:connections"
    WS_ROOM = "ws:room:{room_id}"

    # Task queue (Redis Streams)
    TASK_QUEUE = "queue:tasks"
    TASK_PROCESSING = "queue:tasks:processing"
    TASK_DEAD_LETTER = "queue:tasks:dead-letter"

    # Embeddings cache
    EMBEDDING_CACHE = "embedding:cache:{text_hash}"

    # Analytics
    ANALYTICS_EVENTS = "analytics:events"
    ANALYTICS_DAILY = "analytics:daily:{date}"

    # Pub/Sub channels
    CHANNEL_NOTIFICATIONS = "channel:notifications"
    CHANNEL_CONVERSATIONS = "channel:conversations"
    CHANNEL_PRESENCE = "channel:presence"


# TTL constants (in seconds)
class RedisTTL:
    """Default TTL values for different key types"""

    SESSION = 7 * 24 * 60 * 60  # 7 days
    REFRESH_TOKEN = 7 * 24 * 60 * 60  # 7 days
    POI_SEARCH = 5 * 60  # 5 minutes
    POI_DETAILS = 60 * 60  # 1 hour
    TRANSIT_ROUTES = 5 * 60  # 5 minutes
    WEATHER_CURRENT = 10 * 60  # 10 minutes
    WEATHER_FORECAST = 60 * 60  # 1 hour
    USER_PREFERENCES = 30 * 60  # 30 minutes
    ITINERARY = 60 * 60  # 1 hour
    EMBEDDING_CACHE = 30 * 24 * 60 * 60  # 30 days
    RATE_LIMIT = 60  # 1 minute (window)
    WS_CONNECTION = 24 * 60 * 60  # 1 day


async def health_check_redis() -> bool:
    """Check Redis connectivity"""
    try:
        client = get_redis_client()
        await client.ping()
        return True
    except Exception:
        return False
