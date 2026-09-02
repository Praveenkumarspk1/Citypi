"""
WebSocket Connection Schemas
"""
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ConnectionState(StrEnum):
    """WebSocket connection states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class WSConnectionInfo(BaseModel):
    """WebSocket connection information"""
    connection_id: UUID
    user_id: UUID | None = None
    state: ConnectionState = ConnectionState.CONNECTING
    device_id: str | None = None
    platform: str | None = None
    app_version: str | None = None
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    subscriptions: set[str] = Field(default_factory=set)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WSUserPresence(BaseModel):
    """User presence information"""
    user_id: UUID
    status: str = "online"  # online, away, busy, offline
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    device_id: str | None = None
    platform: str | None = None
    location: dict[str, float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WSRoomInfo(BaseModel):
    """WebSocket room information"""
    room_id: str
    name: str
    type: str  # chat, location, transit, itinerary, notification
    members: set[UUID] = Field(default_factory=set)
    max_members: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WSRoomCreate(BaseModel):
    """Room creation request"""
    name: str
    type: str
    max_members: int | None = None
    is_private: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class WSRoomJoin(BaseModel):
    """Room join request"""
    room_id: str
    user_id: UUID


class WSRoomLeave(BaseModel):
    """Room leave request"""
    room_id: str
    user_id: UUID


class WSSubscription(BaseModel):
    """Subscription information"""
    subscription_id: str
    type: str  # location, transit, itinerary, notifications
    filters: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
