"""
WebSocket Message Schemas
"""
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WSMessageType(StrEnum):
    """WebSocket message types"""
    # Connection
    AUTH = "auth"
    AUTH_SUCCESS = "auth_success"
    AUTH_ERROR = "auth_error"
    PING = "ping"
    PONG = "pong"
    CONNECT = "connect"
    DISCONNECT = "disconnect"

    # Chat
    CHAT_MESSAGE = "chat_message"
    CHAT_HISTORY = "chat_history"
    CHAT_TYPING = "chat_typing"
    CHAT_READ = "chat_read"

    # Location
    LOCATION_UPDATE = "location_update"
    LOCATION_SUBSCRIBE = "location_subscribe"
    LOCATION_UNSUBSCRIBE = "location_unsubscribe"
    NEARBY_USERS = "nearby_users"

    # Transit
    TRANSIT_UPDATE = "transit_update"
    TRANSIT_SUBSCRIBE = "transit_subscribe"
    TRANSIT_UNSUBSCRIBE = "transit_unsubscribe"
    VEHICLE_POSITION = "vehicle_position"
    TRIP_UPDATE = "trip_update"
    SERVICE_ALERT = "service_alert"

    # Itinerary
    ITINERARY_UPDATE = "itinerary_update"
    ITINERARY_COLLABORATOR_JOINED = "itinerary_collaborator_joined"
    ITINERARY_COLLABORATOR_LEFT = "itinerary_collaborator_left"
    ITINERARY_ITEM_ADDED = "itinerary_item_added"
    ITINERARY_ITEM_UPDATED = "itinerary_item_updated"
    ITINERARY_ITEM_REMOVED = "itinerary_item_removed"

    # Notifications
    NOTIFICATION = "notification"
    NOTIFICATION_READ = "notification_read"

    # System
    ERROR = "error"
    ACK = "ack"
    HEARTBEAT = "heartbeat"


class WSMessage(BaseModel):
    """Base WebSocket message"""
    type: WSMessageType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_id: str | None = None
    correlation_id: str | None = None


class WSAuthMessage(BaseModel):
    """Authentication message"""
    token: str
    device_id: str | None = None
    platform: str | None = None
    app_version: str | None = None


class WSPingMessage(BaseModel):
    """Ping message"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSPongMessage(BaseModel):
    """Pong message"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    server_time: datetime = Field(default_factory=datetime.utcnow)


class WSChatMessage(BaseModel):
    """Chat message"""
    conversation_id: UUID
    content: str
    message_type: str = "text"
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    location: dict[str, float] | None = None
    reply_to: UUID | None = None


class WSLocationUpdate(BaseModel):
    """Location update message"""
    user_id: UUID
    latitude: float
    longitude: float
    accuracy: float | None = None
    heading: float | None = None
    speed: float | None = None
    altitude: float | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSTransitUpdate(BaseModel):
    """Transit update message"""
    route_id: str
    vehicle_id: str | None = None
    trip_id: str | None = None
    latitude: float
    longitude: float
    bearing: float | None = None
    speed: float | None = None
    occupancy: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSItineraryUpdate(BaseModel):
    """Itinerary update message"""
    itinerary_id: UUID
    action: str  # created, updated, deleted, item_added, item_updated, item_removed, reordered
    user_id: UUID
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSNotification(BaseModel):
    """Notification message"""
    notification_id: UUID
    type: str
    title: str
    body: str
    data: dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"  # low, normal, high, urgent
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSError(BaseModel):
    """Error message"""
    code: str
    message: str
    details: dict[str, Any] | None = None
    recoverable: bool = True


class WSAck(BaseModel):
    """Acknowledgment message"""
    original_message_id: str
    success: bool
    data: dict[str, Any] | None = None
