"""
SQLAlchemy Media Models
"""
import uuid
from datetime import datetime

from ai_smart_city_concierge.domain.entities.media import (
    Media,
    MediaMetadata,
    MediaSource,
    MediaStatus,
    MediaType,
    MediaVariant,
)
from ai_smart_city_concierge.infrastructure.config.database import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class MediaModel(Base):
    """SQLAlchemy model for Media"""
    __tablename__ = "media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    poi_id = Column(UUID(as_uuid=True), ForeignKey("pois.id"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    itinerary_id = Column(UUID(as_uuid=True), ForeignKey("itineraries.id"), nullable=True, index=True)

    # File info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    type = Column(SQLEnum(MediaType), default=MediaType.IMAGE, nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, default=0, nullable=False)
    width = Column(Integer, default=0, nullable=False)
    height = Column(Integer, default=0, nullable=False)
    format = Column(String(20), nullable=True)

    # Storage
    storage_path = Column(String(500), nullable=False)
    bucket = Column(String(100), nullable=False)
    cdn_url = Column(String(500), nullable=True)

    # Variants (stored as JSON)
    variants = Column(JSON, default=list, nullable=False)

    # Metadata (stored as JSON)
    metadata_json = Column("metadata", JSON, default=dict, nullable=False)

    # Source & Attribution
    source = Column(SQLEnum(MediaSource), default=MediaSource.USER_UPLOAD, nullable=False)
    source_url = Column(String(500), nullable=True)
    attribution = Column(String(500), nullable=True)
    license = Column(String(100), nullable=True)

    # Content
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    alt_text = Column(String(500), nullable=True)
    tags = Column(JSON, default=list, nullable=False)

    # Location context
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String(500), nullable=True)

    # Status
    status = Column(SQLEnum(MediaStatus), default=MediaStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)

    # Moderation
    is_moderated = Column(Boolean, default=False, nullable=False)
    moderation_status = Column(String(20), default="pending", nullable=False)
    moderation_notes = Column(Text, nullable=True)
    moderated_at = Column(DateTime, nullable=True)
    moderated_by = Column(UUID(as_uuid=True), nullable=True)

    # AI Analysis
    clip_embedding = Column(JSON, nullable=True)  # Store embedding directly for small ones
    clip_embedding_id = Column(String(255), nullable=True)
    caption = Column(Text, nullable=True)
    caption_confidence = Column(Float, nullable=True)
    landmarks_detected = Column(JSON, default=list, nullable=False)

    # Usage stats
    view_count = Column(Integer, default=0, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="media")
    poi = relationship("POIModel", back_populates="media")
    conversation = relationship("ConversationModel")
    itinerary = relationship("ItineraryModel")

    __table_args__ = (
        Index('ix_media_user_type_status', 'user_id', 'type', 'status'),
        Index('ix_media_poi_type', 'poi_id', 'type'),
        Index('ix_media_status_created', 'status', 'created_at'),
    )

    def to_entity(self):
        from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
        return Media(
            id=self.id,
            user_id=self.user_id,
            poi_id=self.poi_id,
            conversation_id=self.conversation_id,
            itinerary_id=self.itinerary_id,
            filename=self.filename,
            original_filename=self.original_filename,
            type=self.type,
            mime_type=self.mime_type,
            size_bytes=self.size_bytes,
            width=self.width,
            height=self.height,
            format=self.format,
            storage_path=self.storage_path,
            bucket=self.bucket,
            cdn_url=self.cdn_url,
            variants=[MediaVariant(**v) for v in (self.variants or [])],
            metadata=MediaMetadata(**self.metadata_json) if self.metadata_json else MediaMetadata(),
            source=self.source,
            source_url=self.source_url,
            attribution=self.attribution,
            license=self.license,
            title=self.title,
            description=self.description,
            alt_text=self.alt_text,
            tags=self.tags or [],
            coordinates=Coordinates(latitude=self.latitude, longitude=self.longitude) if self.latitude and self.longitude else None,
            address=self.address,
            status=self.status,
            error_message=self.error_message,
            is_moderated=self.is_moderated,
            moderation_status=self.moderation_status,
            moderation_notes=self.moderation_notes,
            moderated_at=self.moderated_at,
            moderated_by=self.moderated_by,
            clip_embedding=self.clip_embedding,
            clip_embedding_id=self.clip_embedding_id,
            caption=self.caption,
            caption_confidence=self.caption_confidence,
            landmarks_detected=self.landmarks_detected or [],
            view_count=self.view_count,
            download_count=self.download_count,
            like_count=self.like_count,
            created_at=self.created_at,
            updated_at=self.updated_at,
            processed_at=self.processed_at,
            deleted_at=self.deleted_at,
        )

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            poi_id=entity.poi_id,
            conversation_id=entity.conversation_id,
            itinerary_id=entity.itinerary_id,
            filename=entity.filename,
            original_filename=entity.original_filename,
            type=entity.type,
            mime_type=entity.mime_type,
            size_bytes=entity.size_bytes,
            width=entity.width,
            height=entity.height,
            format=entity.format,
            storage_path=entity.storage_path,
            bucket=entity.bucket,
            cdn_url=entity.cdn_url,
            variants=[v.to_dict() for v in entity.variants],
            metadata_json=entity.metadata.to_dict(),
            source=entity.source,
            source_url=entity.source_url,
            attribution=entity.attribution,
            license=entity.license,
            title=entity.title,
            description=entity.description,
            alt_text=entity.alt_text,
            tags=entity.tags,
            latitude=entity.coordinates.latitude if entity.coordinates else None,
            longitude=entity.coordinates.longitude if entity.coordinates else None,
            address=entity.address,
            status=entity.status,
            error_message=entity.error_message,
            is_moderated=entity.is_moderated,
            moderation_status=entity.moderation_status,
            moderation_notes=entity.moderation_notes,
            moderated_at=entity.moderated_at,
            moderated_by=entity.moderated_by,
            clip_embedding=entity.clip_embedding,
            clip_embedding_id=entity.clip_embedding_id,
            caption=entity.caption,
            caption_confidence=entity.caption_confidence,
            landmarks_detected=entity.landmarks_detected,
            view_count=entity.view_count,
            download_count=entity.download_count,
            like_count=entity.like_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            processed_at=entity.processed_at,
            deleted_at=entity.deleted_at,
        )
