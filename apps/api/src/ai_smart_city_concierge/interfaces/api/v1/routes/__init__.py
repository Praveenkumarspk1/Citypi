"""
API v1 Routes
"""
from .analytics import router as analytics_router
from .auth import router as auth_router
from .conversations import router as conversations_router
from .feedback import router as feedback_router
from .health import router as health_router
from .itineraries import router as itineraries_router
from .media import router as media_router
from .pois import router as pois_router
from .transit import router as transit_router
from .users import router as users_router
from .weather import router as weather_router

__all__ = [
    "health_router",
    "auth_router",
    "users_router",
    "pois_router",
    "conversations_router",
    "itineraries_router",
    "transit_router",
    "weather_router",
    "media_router",
    "feedback_router",
    "analytics_router",
]
