"""
Domain Repository Interfaces
"""
from .analytics_repository import AnalyticsRepository
from .conversation_repository import ConversationRepository
from .feedback_repository import FeedbackRepository
from .itinerary_repository import ItineraryRepository
from .media_repository import MediaRepository
from .poi_repository import POIRepository
from .transit_repository import TransitRepository
from .user_repository import UserRepository
from .weather_repository import WeatherRepository

__all__ = [
    "UserRepository",
    "ConversationRepository",
    "ItineraryRepository",
    "POIRepository",
    "TransitRepository",
    "WeatherRepository",
    "MediaRepository",
    "FeedbackRepository",
    "AnalyticsRepository",
]
