"""
Media Domain Entities
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from ..value_objects.coordinates import Coordinates


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class MediaSource(StrEnum):
    USER_UPLOAD = "user_upload"
    POI_OFFICIAL = "poi_official"
    GOOGLE_PLACES = "google_places"
    TRIPADVISOR = "tripadvisor"
    YELP = "yelp"
    FLICKR = "flickr"
    UNSPLASH = "unsplash"
    WIKIMEDIA = "wikimedia"
    OPENSTREETMAP = "openstreetmap"
    AI_GENERATED = "ai_generated"


class MediaStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


@dataclass
class MediaVariant:
    """Media variant (thumbnail, different resolutions, etc.)"""
    id: UUID = field(default_factory=uuid4)
    type: str = ""  # thumbnail, small, medium, large, original
    url: str = ""
    width: int = 0
    height: int = 0
    size_bytes: int = 0
    format: str = ""
    mime_type: str = ""

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "type": self.type,
            "url": self.url,
            "width": self.width,
            "height": self.height,
            "size_bytes": self.size_bytes,
            "format": self.format,
            "mime_type": self.mime_type,
        }


@dataclass
class MediaMetadata:
    """Extended media metadata"""
    # EXIF data
    camera_make: str | None = None
    camera_model: str | None = None
    lens: str | None = None
    focal_length: float | None = None
    aperture: float | None = None
    iso: int | None = None
    exposure_time: str | None = None
    datetime_original: datetime | None = None
    gps_coordinates: Coordinates | None = None

    # Image analysis
    dominant_colors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    objects_detected: list[dict[str, Any]] = field(default_factory=list)
    scene_classification: str | None = None
    nsfw_score: float | None = None

    # Audio/Video
    duration_seconds: float | None = None
    bitrate: int | None = None
    codec: str | None = None
    sample_rate: int | None = None
    channels: int | None = None

    # Document
    page_count: int | None = None
    author: str | None = None
    subject: str | None = None
    keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "camera_make": self.camera_make,
            "camera_model": self.camera_model,
            "lens": self.lens,
            "focal_length": self.focal_length,
            "aperture": self.aperture,
            "iso": self.iso,
            "exposure_time": self.exposure_time,
            "datetime_original": self.datetime_original.isoformat() if self.datetime_original else None,
            "gps_coordinates": self.gps_coordinates.to_dict() if self.gps_coordinates else None,
            "dominant_colors": self.dominant_colors,
            "tags": self.tags,
            "objects_detected": self.objects_detected,
            "scene_classification": self.scene_classification,
            "nsfw_score": self.nsfw_score,
            "duration_seconds": self.duration_seconds,
            "bitrate": self.bitrate,
            "codec": self.codec,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "page_count": self.page_count,
            "author": self.author,
            "subject": self.subject,
            "keywords": self.keywords,
        }


@dataclass
class Media:
    """
    Media aggregate root.
    Represents an uploaded or referenced media file.
    """
    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    poi_id: UUID | None = None
    conversation_id: UUID | None = None
    itinerary_id: UUID | None = None

    # File info
    filename: str = ""
    original_filename: str = ""
    type: MediaType = MediaType.IMAGE
    mime_type: str = ""
    size_bytes: int = 0
    width: int = 0
    height: int = 0
    format: str = ""

    # Storage
    storage_path: str = ""  # Path in MinIO/S3
    bucket: str = ""
    cdn_url: str | None = None

    # Variants
    variants: list[MediaVariant] = field(default_factory=list)

    # Metadata
    metadata: MediaMetadata = field(default_factory=MediaMetadata)

    # Source & Attribution
    source: MediaSource = MediaSource.USER_UPLOAD
    source_url: str | None = None
    attribution: str | None = None
    license: str | None = None

    # Content
    title: str | None = None
    description: str | None = None
    alt_text: str | None = None
    tags: list[str] = field(default_factory=list)

    # Location context
    coordinates: Coordinates | None = None
    address: str | None = None

    # Status
    status: MediaStatus = MediaStatus.PENDING
    error_message: str | None = None

    # Moderation
    is_moderated: bool = False
    moderation_status: str = "pending"  # pending, approved, rejected
    moderation_notes: str | None = None
    moderated_at: datetime | None = None
    moderated_by: UUID | None = None

    # AI Analysis
    clip_embedding: list[float] | None = None
    clip_embedding_id: str | None = None
    caption: str | None = None
    caption_confidence: float | None = None
    landmarks_detected: list[dict[str, Any]] = field(default_factory=list)

    # Usage stats
    view_count: int = 0
    download_count: int = 0
    like_count: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.filename:
            raise ValueError("Filename is required")
        if self.size_bytes < 0:
            raise ValueError("Size cannot be negative")

    def add_variant(self, variant: MediaVariant) -> None:
        """Add a media variant"""
        # Remove existing variant of same type
        self.variants = [v for v in self.variants if v.type != variant.type]
        self.variants.append(variant)
        self.updated_at = datetime.utcnow()

    def get_variant(self, variant_type: str) -> MediaVariant | None:
        """Get variant by type"""
        for variant in self.variants:
            if variant.type == variant_type:
                return variant
        return None

    def get_thumbnail_url(self) -> str | None:
        """Get thumbnail URL"""
        thumb = self.get_variant("thumbnail")
        return thumb.url if thumb else self.cdn_url

    def get_best_url(self, max_width: int = 1920) -> str:
        """Get best variant URL for given max width"""
        suitable = [v for v in self.variants if v.width <= max_width and v.width > 0]
        if suitable:
            best = max(suitable, key=lambda v: v.width)
            return best.url
        return self.cdn_url or ""

    def mark_processing(self) -> None:
        """Mark as processing"""
        self.status = MediaStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_ready(self) -> None:
        """Mark as ready"""
        self.status = MediaStatus.READY
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark as failed"""
        self.status = MediaStatus.FAILED
        self.error_message = error
        self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """Soft delete media"""
        self.status = MediaStatus.DELETED
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def approve(self, moderator_id: UUID) -> None:
        """Approve media"""
        self.is_moderated = True
        self.moderation_status = "approved"
        self.moderated_at = datetime.utcnow()
        self.moderated_by = moderator_id
        self.updated_at = datetime.utcnow()

    def reject(self, moderator_id: UUID, notes: str) -> None:
        """Reject media"""
        self.is_moderated = True
        self.moderation_status = "rejected"
        self.moderation_notes = notes
        self.moderated_at = datetime.utcnow()
        self.moderated_by = moderator_id
        self.updated_at = datetime.utcnow()

    def increment_view(self) -> None:
        """Increment view count"""
        self.view_count += 1
        self.updated_at = datetime.utcnow()

    def increment_download(self) -> None:
        """Increment download count"""
        self.download_count += 1
        self.updated_at = datetime.utcnow()

    def increment_like(self) -> None:
        """Increment like count"""
        self.like_count += 1
        self.updated_at = datetime.utcnow()

    def set_clip_embedding(self, embedding: list[float], embedding_id: str) -> None:
        """Set CLIP embedding reference"""
        self.clip_embedding = embedding
        self.clip_embedding_id = embedding_id
        self.updated_at = datetime.utcnow()

    def set_caption(self, caption: str, confidence: float) -> None:
        """Set AI-generated caption"""
        self.caption = caption
        self.caption_confidence = confidence
        self.updated_at = datetime.utcnow()

    def add_landmark(self, landmark: dict[str, Any]) -> None:
        """Add detected landmark"""
        self.landmarks_detected.append(landmark)
        self.updated_at = datetime.utcnow()

    def to_dict(self, include_variants: bool = True, include_metadata: bool = True) -> dict:
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "poi_id": str(self.poi_id) if self.poi_id else None,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "itinerary_id": str(self.itinerary_id) if self.itinerary_id else None,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "type": self.type.value,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "storage_path": self.storage_path,
            "bucket": self.bucket,
            "cdn_url": self.cdn_url,
            "source": self.source.value,
            "source_url": self.source_url,
            "attribution": self.attribution,
            "license": self.license,
            "title": self.title,
            "description": self.description,
            "alt_text": self.alt_text,
            "tags": self.tags,
            "coordinates": self.coordinates.to_dict() if self.coordinates else None,
            "address": self.address,
            "status": self.status.value,
            "error_message": self.error_message,
            "is_moderated": self.is_moderated,
            "moderation_status": self.moderation_status,
            "moderation_notes": self.moderation_notes,
            "moderated_at": self.moderated_at.isoformat() if self.moderated_at else None,
            "moderated_by": str(self.moderated_by) if self.moderated_by else None,
            "caption": self.caption,
            "caption_confidence": self.caption_confidence,
            "landmarks_detected": self.landmarks_detected,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "like_count": self.like_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        if include_variants:
            data["variants"] = [v.to_dict() for v in self.variants]
        if include_metadata:
            data["metadata"] = self.metadata.to_dict()
        return data
