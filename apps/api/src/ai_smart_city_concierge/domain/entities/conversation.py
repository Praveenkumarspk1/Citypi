"""
Conversation Domain Entity
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from ..value_objects.coordinates import Coordinates


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageType(StrEnum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    LOCATION = "location"
    POI_CARD = "poi_card"
    ITINERARY = "itinerary"
    TRANSIT = "transit"
    WEATHER = "weather"
    ERROR = "error"


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class Message:
    """Individual message in a conversation"""
    id: UUID = field(default_factory=uuid4)
    role: MessageRole = MessageRole.USER
    type: MessageType = MessageType.TEXT
    content: str = ""

    # Metadata
    tokens: int = 0
    model: str | None = None
    processing_time_ms: int = 0

    # Attachments
    attachments: list[dict[str, Any]] = field(default_factory=list)

    # Tool calls (for assistant messages)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_call_id: str | None = None

    # Context
    context: dict[str, Any] = field(default_factory=dict)

    # Location context (if message is location-based)
    location: Coordinates | None = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "role": self.role.value,
            "type": self.type.value,
            "content": self.content,
            "tokens": self.tokens,
            "model": self.model,
            "processing_time_ms": self.processing_time_ms,
            "attachments": self.attachments,
            "tool_calls": self.tool_calls,
            "tool_call_id": self.tool_call_id,
            "context": self.context,
            "location": self.location.to_dict() if self.location else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Conversation:
    """
    Conversation aggregate root.
    Represents a chat session between user and AI assistant.
    """
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    title: str | None = None
    status: ConversationStatus = ConversationStatus.ACTIVE

    # Context
    language: str = "en"
    location: Coordinates | None = None
    context: dict[str, Any] = field(default_factory=dict)

    # Messages
    messages: list[Message] = field(default_factory=list)

    # Summary for long conversations
    summary: str | None = None
    summary_updated_at: datetime | None = None

    # Metadata
    total_tokens: int = 0
    total_messages: int = 0
    model_used: str | None = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_message_at: datetime | None = None
    archived_at: datetime | None = None

    def add_message(
        self,
        role: MessageRole,
        content: str,
        type: MessageType = MessageType.TEXT,
        **kwargs
    ) -> Message:
        """Add a message to the conversation"""
        message = Message(
            role=role,
            type=type,
            content=content,
            **kwargs
        )
        self.messages.append(message)
        self.total_messages += 1
        self.total_tokens += message.tokens
        self.last_message_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return message

    def add_user_message(
        self,
        content: str,
        type: MessageType = MessageType.TEXT,
        location: Coordinates | None = None,
        **kwargs
    ) -> Message:
        """Add a user message"""
        return self.add_message(
            role=MessageRole.USER,
            content=content,
            type=type,
            location=location,
            **kwargs
        )

    def add_assistant_message(
        self,
        content: str,
        type: MessageType = MessageType.TEXT,
        tokens: int = 0,
        model: str | None = None,
        processing_time_ms: int = 0,
        tool_calls: list[dict[str, Any]] | None = None,
        **kwargs
    ) -> Message:
        """Add an assistant message"""
        return self.add_message(
            role=MessageRole.ASSISTANT,
            content=content,
            type=type,
            tokens=tokens,
            model=model,
            processing_time_ms=processing_time_ms,
            tool_calls=tool_calls or [],
            **kwargs
        )

    def add_system_message(self, content: str) -> Message:
        """Add a system message"""
        return self.add_message(
            role=MessageRole.SYSTEM,
            content=content,
            type=MessageType.TEXT,
        )

    def add_tool_message(
        self,
        content: str,
        tool_call_id: str,
        **kwargs
    ) -> Message:
        """Add a tool result message"""
        return self.add_message(
            role=MessageRole.TOOL,
            content=content,
            type=MessageType.TEXT,
            tool_call_id=tool_call_id,
            **kwargs
        )

    def get_recent_messages(self, limit: int = 10) -> list[Message]:
        """Get recent messages"""
        return self.messages[-limit:]

    def get_messages_for_llm(
        self,
        max_tokens: int = 4000,
        include_system: bool = True
    ) -> list[dict[str, Any]]:
        """
        Get messages formatted for LLM API.
        Truncates to fit within token limit.
        """
        formatted = []
        token_count = 0

        # Add system message if requested
        if include_system:
            system_msg = next((m for m in self.messages if m.role == MessageRole.SYSTEM), None)
            if system_msg:
                formatted.append({"role": "system", "content": system_msg.content})
                token_count += system_msg.tokens

        # Add recent messages in reverse order (newest first)
        for msg in reversed(self.messages):
            if msg.role == MessageRole.SYSTEM:
                continue

            msg_tokens = msg.tokens or len(msg.content) // 4  # rough estimate
            if token_count + msg_tokens > max_tokens:
                break

            formatted.insert(0 if include_system else len(formatted), {
                "role": msg.role.value,
                "content": msg.content,
            })
            token_count += msg_tokens

        return formatted

    def update_summary(self, summary: str) -> None:
        """Update conversation summary"""
        self.summary = summary
        self.summary_updated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_location(self, location: Coordinates) -> None:
        """Update conversation location context"""
        self.location = location
        self.updated_at = datetime.utcnow()

    def update_context(self, context: dict[str, Any]) -> None:
        """Update conversation context"""
        self.context.update(context)
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive conversation"""
        self.status = ConversationStatus.ARCHIVED
        self.archived_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def delete(self) -> None:
        """Soft delete conversation"""
        self.status = ConversationStatus.DELETED
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate conversation"""
        self.status = ConversationStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        return self.status == ConversationStatus.ACTIVE

    def to_dict(self, include_messages: bool = False) -> dict:
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "status": self.status.value,
            "language": self.language,
            "location": self.location.to_dict() if self.location else None,
            "context": self.context,
            "summary": self.summary,
            "summary_updated_at": self.summary_updated_at.isoformat() if self.summary_updated_at else None,
            "total_tokens": self.total_tokens,
            "total_messages": self.total_messages,
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
        }
        if include_messages:
            data["messages"] = [m.to_dict() for m in self.messages]
        return data
