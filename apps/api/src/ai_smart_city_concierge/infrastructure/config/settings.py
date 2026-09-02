"""
Application Configuration using Pydantic Settings
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    host: str = "localhost"
    port: int = 5432
    user: str = "concierge"
    password: str = "concierge_dev_password"
    name: str = "concierge"
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis configuration"""
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    max_connections: int = 50
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    decode_responses: bool = True

    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class ChromaDBSettings(BaseSettings):
    """ChromaDB configuration"""
    model_config = SettingsConfigDict(env_prefix="CHROMADB_")

    host: str = "localhost"
    port: int = 8000
    ssl: bool = False
    auth_token: str | None = None

    @property
    def url(self) -> str:
        protocol = "https" if self.ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"


class MinIOSettings(BaseSettings):
    """MinIO/S3 configuration"""
    model_config = SettingsConfigDict(env_prefix="MINIO_")

    endpoint: str = "localhost:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin123"
    bucket: str = "concierge-media"
    secure: bool = False
    region: str = "us-east-1"


class AISettings(BaseSettings):
    """AI/ML Model configuration"""
    model_config = SettingsConfigDict(env_prefix="AI_")

    # Gemini API
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 2048
    gemini_top_p: float = 0.95
    gemini_top_k: int = 40

    # Embeddings
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimensions: int = 1024
    embedding_batch_size: int = 32
    embedding_device: str = "cpu"  # cpu or cuda
    embedding_normalize: bool = True

    # Whisper STT
    whisper_model: str = "small"  # tiny, base, small, medium, large
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"  # int8, float16, float32

    # CLIP Vision
    clip_model: str = "openai/clip-vit-base-patch32"
    clip_device: str = "cpu"

    # Reranker
    reranker_model: str = "BAAI/bge-reranker-base"
    reranker_device: str = "cpu"

    # Recommendation
    lightfm_components: int = 64
    lightfm_learning_rate: float = 0.05
    lightfm_epochs: int = 30
    lightfm_loss: str = "warp"


class AuthSettings(BaseSettings):
    """Authentication configuration"""
    model_config = SettingsConfigDict(env_prefix="AUTH_")

    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    bcrypt_rounds: int = 12

    # OAuth
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration"""
    model_config = SettingsConfigDict(env_prefix="RATELIMIT_")

    enabled: bool = True
    default_limit: int = 100
    default_window: int = 60  # seconds
    auth_limit: int = 20
    auth_window: int = 60
    api_limit: int = 1000
    api_window: int = 60
    websocket_limit: int = 50
    websocket_window: int = 60


class ObservabilitySettings(BaseSettings):
    """Observability configuration"""
    model_config = SettingsConfigDict(env_prefix="OBS_")

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or console
    log_file: str | None = None

    # Metrics
    metrics_enabled: bool = True
    metrics_port: int = 9090
    metrics_path: str = "/metrics"

    # Tracing
    tracing_enabled: bool = True
    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    service_name: str = "concierge-api"
    sample_rate: float = 0.1

    # Health checks
    health_check_interval: int = 30


class ExternalAPISettings(BaseSettings):
    """External API configuration"""
    model_config = SettingsConfigDict(env_prefix="EXTERNAL_")

    # OpenStreetMap / Overpass
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    overpass_rate_limit: int = 60  # per minute
    nominatim_url: str = "https://nominatim.openstreetmap.org"
    nominatim_rate_limit: int = 1  # per second

    # Open-Meteo
    open_meteo_url: str = "https://api.open-meteo.com/v1"
    open_meteo_rate_limit: int = 100

    # GTFS (mobilitydatabase.org - successor to transitfeeds.com)
    gtfs_static_url: str | None = None
    gtfs_realtime_url: str | None = None
    gtfs_api_key: str | None = None
    gtfs_rate_limit: int = 10

    # OpenChargeMap
    openchargemap_url: str = "https://api.openchargemap.io/v3"
    openchargemap_api_key: str | None = None
    openchargemap_rate_limit: int = 100

    # Socrata
    socrata_domain: str | None = None
    socrata_app_token: str | None = None
    socrata_rate_limit: int = 100


class AppSettings(BaseSettings):
    """Main application settings"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = True
    api_prefix: str = "/api/v1"
    app_name: str = "Smart City Concierge"
    app_version: str = "0.1.0"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def cors_allow_methods_list(self) -> list[str]:
        return [method.strip() for method in self.cors_allow_methods.split(",")]

    @property
    def cors_allow_headers_list(self) -> list[str]:
        return [header.strip() for header in self.cors_allow_headers.split(",")]

    # Sub-settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    chromadb: ChromaDBSettings = ChromaDBSettings()
    minio: MinIOSettings = MinIOSettings()
    ai: AISettings = AISettings()
    auth: AuthSettings = AuthSettings()
    ratelimit: RateLimitSettings = RateLimitSettings()
    observability: ObservabilitySettings = ObservabilitySettings()
    external: ExternalAPISettings = ExternalAPISettings()


@lru_cache
def get_settings() -> AppSettings:
    """Get cached settings instance"""
    return AppSettings()


# Global settings instance
settings = get_settings()
