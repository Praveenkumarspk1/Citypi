"""
SQLAlchemy Conversation Models
"""
import uuid
from datetime import datetime

from ai_smart_city_concierge.domain.entities.conversation import (
    Conversation,
    ConversationStatus,
    Message,
    MessageRole,
    MessageType,
)
from ai_smart_city_concierge.infrastructure.config.database import Base
from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class ConversationModel(Base):
    """SQLAlchemy model for Conversation"""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False)
    language = Column(String(10), default="en", nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    context = Column(JSON, default=dict, nullable=False)
    summary = Column(Text, nullable=True)
    summary_updated_at = Column(DateTime, nullable=True)
    total_tokens = Column(Integer, default=0, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="conversations")
    messages = relationship("MessageModel", back_populates="conversation", lazy="dynamic", order_by="MessageModel.created_at")

    def to_entity(self):
        """Convert to domain entity"""
        from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
        return Conversation(
            id=self.id,
            user_id=self.user_id,
            title=self.title,
            status=self.status,
            language=self.language,
            location=Coordinates(latitude=self.location_lat, longitude=self.location_lng) if self.location_lat and self.location_lng else None,
            context=self.context or {},
            summary=self.summary,
            summary_updated_at=self.summary_updated_at,
            total_tokens=self.total_tokens,
            total_messages=self.total_messages,
            model_used=self.model_used,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_message_at=self.last_message_at,
            archived_at=self.archived_at,
        )

    @classmethod
    def from_entity(cls, entity):
        """Create model from domain entity"""
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            title=entity.title,
            status=entity.status,
            language=entity.language,
            location_lat=entity.location.latitude if entity.location else None,
            location_lng=entity.location.longitude if entity.location else None,
            context=entity.context,
            summary=entity.summary,
            summary_updated_at=entity.summary_updated_at,
            total_tokens=entity.total_tokens,
            total_messages=entity.total_messages,
            model_used=entity.model_used,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            last_message_at=entity.last_message_at,
            archived_at=entity.archived_at,
        )


class MessageModel(Base):
    """SQLAlchemy model for Message"""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(SQLEnum(MessageRole), default=MessageRole.USER, nullable=False)
    type = Column(SQLEnum(MessageType), default=MessageType.TEXT, nullable=False)
    content = Column(Text, nullable=False)
    tokens = Column(Integer, default=0, nullable=False)
    model = Column(String(100), nullable=True)
    processing_time_ms = Column(Integer, default=0, nullable=False)
    attachments = Column(JSON, default=list, nullable=False)
    tool_calls = Column(JSON, default=list, nullable=False)
    tool_call_id = Column(String(100), nullable=True)
    context = Column(JSON, default=dict, nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="messages")

    def to_entity(self):
        """Convert to domain entity"""
        from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
        return Message(
            id=self.id,
            role=self.role,
            type=self.type,
            content=self.content,
            tokens=self.tokens,
            model=self.model,
            processing_time_ms=self.processing_time_ms,
            attachments=self.attachments or [],
            tool_calls=self.tool_calls or [],
            tool_call_id=self.tool_call_id,
            context=self.context or {},
            location=Coordinates(latitude=self.location_lat, longitude=self.location_lng) if self.location_lat and self.location_lng else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity, conversation_id):
        """Create model from domain entity"""
        return cls(
            id=entity.id,
            conversation_id=conversation_id,
            role=entity.role,
            type=entity.type,
            content=entity.content,
            tokens=entity.tokens,
            model=entity.model,
            processing_time_ms=entity.processing_time_ms,
            attachments=entity.attachments,
            tool_calls=entity.tool_calls,
            tool_call_id=entity.tool_call_id,
            context=entity.context,
            location_lat=entity.location.latitude if entity.location else None,
            location_lng=entity.location.longitude if entity.location else None,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
