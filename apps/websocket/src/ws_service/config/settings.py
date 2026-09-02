"""
WebSocket Service Configuration
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings for WebSocket service."""

    # App
    app_name: str = "AI Smart City Concierge"
    app_version: str = "0.1.0"
    debug: bool = True
    environment: str = "development"

    # API
    api_prefix: str = "/api/v1"
    cors_origins: str = "*"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 100

    # JWT Auth
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "smart-city-concierge"
    jwt_audience: str = "smart-city-concierge-users"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_connection_timeout: int = 300
    ws_max_message_size: int = 1024 * 1024  # 1MB
    ws_max_connections_per_user: int = 5

    # Connection Manager
    cm_cleanup_interval: int = 60
    cm_stale_connection_timeout: int = 300

    # Handlers
    chat_max_history: int = 100
    location_broadcast_radius: float = 1000.0  # meters
    location_update_throttle: int = 5  # seconds
    transit_alert_cooldown: int = 60  # seconds
    notification_ttl: int = 86400  # 24 hours

    # Observability
    log_level: str = "INFO"
    otel_service_name: str = "websocket-service"
    jaeger_agent_host: str = "jaeger"
    jaeger_agent_port: int = 6831
    jaeger_collector_endpoint: str = "http://jaeger:14268/api/traces"
    prometheus_port: int = 9090
    prometheus_path: str = "/metrics"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def cors_allow_methods_list(self) -> list[str]:
        return [method.strip() for method in self.cors_allow_methods.split(",")]

    @property
    def cors_allow_headers_list(self) -> list[str]:
        return [header.strip() for header in self.cors_allow_headers.split(",")]


# Cached settings instance
_settings: Settings = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
