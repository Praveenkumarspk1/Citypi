"""
Redis Settings

Redis configuration for caching, messaging, and sessions.
"""
from typing import List
from pydantic import Field
from .base import BaseSettings


class RedisSettings(BaseSettings):
    """Redis configuration."""
    
    # Main Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )
    redis_max_connections: int = 100
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    redis_retry_on_timeout: bool = True
    redis_health_check_interval: int = 30

    # Cluster (optional)
    redis_cluster_nodes: List[str] = Field(default_factory=list)
    redis_cluster_max_redirects: int = 3

    # Sentinel (optional)
    redis_sentinel_master: str = ""
    redis_sentinel_nodes: List[str] = Field(default_factory=list)

    # Database numbers
    redis_cache_db: int = 0
    redis_session_db: int = 1
    redis_queue_db: int = 2
    redis_rate_limit_db: int = 3
    redis_websocket_db: int = 4