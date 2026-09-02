"""
WebSocket Interface
Real-time communication layer for the AI Smart City Concierge
"""
from .handlers import (
    chat_handler,
    connection_manager,
    itinerary_handler,
    location_handler,
    notification_handler,
    transit_handler,
)
from .schemas.connection import (
    ConnectionState,
    WSConnectionInfo,
    WSRoomInfo,
    WSUserPresence,
)
from .schemas.messages import (
    WSAck,
    WSAuthMessage,
    WSChatMessage,
    WSError,
    WSItineraryUpdate,
    WSLocationUpdate,
    WSMessage,
    WSMessageType,
    WSNotification,
    WSPingMessage,
    WSPongMessage,
    WSTransitUpdate,
)
from .server import router as websocket_router

__all__ = [
    "websocket_router",
    "connection_manager",
    "chat_handler",
    "location_handler",
    "transit_handler",
    "itinerary_handler",
    "notification_handler",
    "WSMessage",
    "WSMessageType",
    "WSAuthMessage",
    "WSPingMessage",
    "WSPongMessage",
    "WSChatMessage",
    "WSLocationUpdate",
    "WSTransitUpdate",
    "WSItineraryUpdate",
    "WSNotification",
    "WSError",
    "WSAck",
    "WSConnectionInfo",
    "WSUserPresence",
    "WSRoomInfo",
    "ConnectionState",
]
