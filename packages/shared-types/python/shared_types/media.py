"""
Media Types

Type definitions for media files.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class MediaType(str, Enum):
    """Media file types."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class MediaStatus(str, Enum):
    """Media processing status."""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class Media(BaseModel):
    """Media file entity."""
    id: UUID
    user_id: UUID
    conversation_id: Optional[UUID] = None
    itinerary_id: Optional[UUID] = None
    poi_id: Optional[UUID] = None
    type: MediaType
    status: MediaStatus = MediaStatus.PENDING
    original_filename: str
    file_size: int
    mime_type: str
    storage_path: str
    storage_bucket: str
    cdn_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # seconds for audio/video
    format: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    alt_text: Optional[str] = None
    is_public: bool = False
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaUpload(BaseModel):
    """Media upload request."""
    user_id: UUID
    conversation_id: Optional[UUID] = None
    itinerary_id: Optional[UUID] = None
    poi_id: Optional[UUID] = None
    type: MediaType
    original_filename: str
    file_size: int
    mime_type: str
    is_public: bool = False
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    alt_text: Optional[str] = None


class MediaUpdate(BaseModel):
    """Media update request."""
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    alt_text: Optional[str] = None
    is_public: Optional[bool] = None


class MediaResponse(BaseModel):
    """Media response."""
    id: UUID
    user_id: UUID
    conversation_id: Optional[UUID] = None
    itinerary_id: Optional[UUID] = None
    poi_id: Optional[UUID] = None
    type: MediaType
    status: MediaStatus
    original_filename: str
    file_size: int
    mime_type: str
    cdn_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    format: Optional[str] = None
    metadata: Dict[str, Any]
    tags: List[str]
    description: Optional[str] = None
    alt_text: Optional[str] = None
    is_public: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaProcessingResult(BaseModel):
    """Media processing result."""
    media_id: UUID
    success: bool
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    format: Optional[str] = None
    thumbnails: List[str] = Field(default_factory=list)
    transcript: Optional[str] = None  # for audio/video
    objects_detected: List[Dict[str, Any]] = Field(default_factory=list)
    text_extracted: Optional[str] = None
    error: Optional[str] = None