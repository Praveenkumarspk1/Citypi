"""
Conversation Types

Type definitions for chat conversations and messages.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class MessageRole(str, Enum):
    """Message sender role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageType(str, Enum):
    """Message content type."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"
    POI_CARD = "poi_card"
    ITINERARY_CARD = "itinerary_card"
    TRANSIT_CARD = "transit_card"
    WEATHER_CARD = "weather_card"
    QUICK_REPLY = "quick_reply"
    BUTTON = "button"


class ConversationStatus(str, Enum):
    """Conversation status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    BLOCKED = "blocked"


class Message(BaseModel):
    """Chat message."""
    id: UUID
    conversation_id: UUID
    role: MessageRole
    type: MessageType = MessageType.TEXT
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[str] = Field(default_factory=list)
    tokens_used: int = 0
    model_used: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Conversation(BaseModel):
    """Conversation entity."""
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    status: ConversationStatus = ConversationStatus.ACTIVE
    language: str = "en"
    context: Dict[str, Any] = Field(default_factory=dict)
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    """Conversation creation request."""
    user_id: UUID
    title: Optional[str] = None
    language: str = "en"
    context: Dict[str, Any] = Field(default_factory=dict)


class ConversationUpdate(BaseModel):
    """Conversation update request."""
    title: Optional[str] = None
    status: Optional[ConversationStatus] = None
    context: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Conversation response with messages."""
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    status: ConversationStatus
    language: str
    context: Dict[str, Any]
    message_count: int
    last_message_at: Optional[datetime] = None
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    """Message creation request."""
    conversation_id: UUID
    role: MessageRole
    type: MessageType = MessageType.TEXT
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[str] = Field(default_factory=list)


class MessageResponse(BaseModel):
    """Message response."""
    id: UUID
    conversation_id: UUID
    role: MessageRole
    type: MessageType
    content: str
    metadata: Dict[str, Any]
    attachments: List[str]
    tokens_used: int
    model_used: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuickReply(BaseModel):
    """Quick reply button."""
    title: str
    payload: str
    image_url: Optional[str] = None


class Button(BaseModel):
    """Interactive button."""
    title: str
    payload: str
    url: Optional[str] = None
    type: str = "postback"  # postback, web_url, phone_number