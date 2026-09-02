"""
API Routes
"""
from .analytics_routes import router as analytics_router
from .conversation_routes import router as conversation_router
from .feedback_routes import router as feedback_router
from .itinerary_routes import router as itinerary_router
from .media_routes import router as media_router
from .poi_routes import router as poi_router
from .transit_routes import router as transit_router
from .user_routes import router as user_router
from .weather_routes import router as weather_router

__all__ = [
    "poi_router",
    "user_router",
    "conversation_router",
    "itinerary_router",
    "transit_router",
    "weather_router",
    "media_router",
    "feedback_router",
    "analytics_router",
]
