"""
Database Settings

Database configuration for PostgreSQL with PostGIS.
"""
from typing import Optional, List
from pydantic import Field
from .base import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    # PostgreSQL
    database_url: str = Field(
        default="postgresql+asyncpg://concierge:concierge_dev_password@localhost:5432/concierge",
        validation_alias="DATABASE_URL",
    )
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600

    # Migration
    alembic_script_location: str = "migrations"
    alembic_version_table: str = "alembic_version"

    # Read replicas (optional)
    read_replica_urls: List[str] = Field(default_factory=list)