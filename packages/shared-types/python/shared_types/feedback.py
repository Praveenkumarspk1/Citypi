"""
Feedback Types

Type definitions for user feedback and reviews.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class FeedbackType(str, Enum):
    """Feedback types."""
    REVIEW = "review"
    RATING = "rating"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    SUGGESTION = "suggestion"
    POI_CORRECTION = "poi_correction"
    TRANSIT_CORRECTION = "transit_correction"
    WEATHER_CORRECTION = "weather_correction"
    ITINERARY_FEEDBACK = "itinerary_feedback"
    CONVERSATION_FEEDBACK = "conversation_feedback"


class FeedbackStatus(str, Enum):
    """Feedback status."""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    CLOSED = "closed"


class Feedback(BaseModel):
    """Feedback entity."""
    id: UUID
    user_id: UUID
    type: FeedbackType
    status: FeedbackStatus = FeedbackStatus.SUBMITTED
    subject_id: Optional[UUID] = None  # POI, itinerary, conversation, etc.
    subject_type: Optional[str] = None
    title: str
    content: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    tags: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    admin_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedbackCreate(BaseModel):
    """Feedback creation request."""
    user_id: UUID
    type: FeedbackType
    subject_id: Optional[UUID] = None
    subject_type: Optional[str] = None
    title: str
    content: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    tags: List[str] = Field(default_factory=list)
    attachments: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeedbackUpdate(BaseModel):
    """Feedback update request (admin)."""
    status: Optional[FeedbackStatus] = None
    admin_notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response."""
    id: UUID
    user_id: UUID
    type: FeedbackType
    status: FeedbackStatus
    subject_id: Optional[UUID] = None
    subject_type: Optional[str] = None
    title: str
    content: str
    rating: Optional[int] = None
    tags: List[str]
    attachments: List[str]
    metadata: Dict[str, Any]
    admin_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class POIReview(BaseModel):
    """POI-specific review."""
    id: UUID
    user_id: UUID
    poi_id: UUID
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    content: str
    visit_date: Optional[datetime] = None
    visit_type: Optional[str] = None  # solo, couple, family, business, friends
    photos: List[str] = Field(default_factory=list)
    helpful_count: int = 0
    reported_count: int = 0
    is_verified_visit: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class POIReviewCreate(BaseModel):
    """POI review creation request."""
    user_id: UUID
    poi_id: UUID
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    content: str
    visit_date: Optional[datetime] = None
    visit_type: Optional[str] = None
    photos: List[str] = Field(default_factory=list)


class POIReviewResponse(BaseModel):
    """POI review response."""
    id: UUID
    user_id: UUID
    poi_id: UUID
    rating: int
    title: Optional[str] = None
    content: str
    visit_date: Optional[datetime] = None
    visit_type: Optional[str] = None
    photos: List[str]
    helpful_count: int
    is_verified_visit: bool
    user_display_name: Optional[str] = None
    user_avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)