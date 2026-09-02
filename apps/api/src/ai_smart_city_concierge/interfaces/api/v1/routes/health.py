"""
Health Check Routes
"""
from typing import Any

from fastapi import APIRouter

from ai_smart_city_concierge.infrastructure.config.database import health_check_db
from ai_smart_city_concierge.infrastructure.config.redis import health_check_redis
from ai_smart_city_concierge.infrastructure.config.settings import get_settings
from ai_smart_city_concierge.infrastructure.config.vector_store import health_check_vector_store

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """Liveness probe - returns 200 if service is running"""
    return {"status": "alive"}


@router.get("/ready")
async def readiness_check() -> dict[str, Any]:
    """Readiness probe - checks all dependencies"""
    settings = get_settings()

    checks = {
        "database": await health_check_db(),
        "redis": await health_check_redis(),
        "vector_store": await health_check_vector_store(),
    }

    all_healthy = all(checks.values())

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get("/startup")
async def startup_check() -> dict[str, str]:
    """Startup probe - returns 200 if service has started"""
    return {"status": "started"}


@router.get("/")
async def health_check() -> dict[str, Any]:
    """General health check endpoint"""
    settings = get_settings()

    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }
