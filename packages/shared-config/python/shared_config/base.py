"""
Base Settings

Base configuration class with common functionality.
"""
from typing import Optional, List, Dict, Any
from functools import lru_cache
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic import Field, ConfigDict


class BaseSettings(PydanticBaseSettings):
    """Base settings class with common configuration."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

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

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def cors_allow_methods_list(self) -> List[str]:
        return [method.strip() for method in self.cors_allow_methods.split(",")]

    @property
    def cors_allow_headers_list(self) -> List[str]:
        return [header.strip() for header in self.cors_allow_headers.split(",")]


# Cached settings instances
_settings_cache: Dict[str, BaseSettings] = {}


def get_settings(settings_class: type = BaseSettings) -> BaseSettings:
    """Get cached settings instance."""
    key = settings_class.__name__
    if key not in _settings_cache:
        _settings_cache[key] = settings_class()
    return _settings_cache[key]


def clear_settings_cache() -> None:
    """Clear settings cache (useful for testing)."""
    global _settings_cache
    _settings_cache.clear()