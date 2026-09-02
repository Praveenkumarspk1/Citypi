"""
API Client Package

HTTP client for communicating with the AI Smart City Concierge API.
"""
from .client import APIClient, AsyncAPIClient
from .auth import AuthClient, TokenManager
from .endpoints import (
    ChatEndpoint,
    POIEndpoint,
    ItineraryEndpoint,
    TransitEndpoint,
    WeatherEndpoint,
    UserEndpoint,
    ConversationEndpoint,
    MediaEndpoint,
    FeedbackEndpoint,
    AnalyticsEndpoint,
)
from .models import *
from .exceptions import *

__all__ = [
    "APIClient",
    "AsyncAPIClient",
    "AuthClient",
    "TokenManager",
    "ChatEndpoint",
    "POIEndpoint",
    "ItineraryEndpoint",
    "TransitEndpoint",
    "WeatherEndpoint",
    "UserEndpoint",
    "ConversationEndpoint",
    "MediaEndpoint",
    "FeedbackEndpoint",
    "AnalyticsEndpoint",
]