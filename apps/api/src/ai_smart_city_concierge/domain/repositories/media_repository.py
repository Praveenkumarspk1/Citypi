"""
Media Repository Interface
"""
from abc import ABC, abstractmethod
from uuid import UUID

from ..entities.media import Media, MediaSource, MediaStatus, MediaType
from .base import BaseRepository, PaginatedResult, PaginationParams


class MediaRepository(BaseRepository[Media, UUID], ABC):
    """Media repository interface"""

    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
        media_type: MediaType | None = None,
        status: MediaStatus | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Media]:
        """Get media by user"""
        pass

    @abstractmethod
    async def get_by_poi(
        self,
        poi_id: UUID,
        media_type: MediaType | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Media]:
        """Get media for POI"""
        pass

    @abstractmethod
    async def get_by_conversation(
        self,
        conversation_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Media]:
        """Get media for conversation"""
        pass

    @abstractmethod
    async def get_by_itinerary(
        self,
        itinerary_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Media]:
        """Get media for itinerary"""
        pass

    @abstractmethod
    async def get_by_source(
        self,
        source: MediaSource,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Media]:
        """Get media by source"""
        pass

    @abstractmethod
    async def get_pending_moderation(
        self,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Media]:
        """Get media pending moderation"""
        pass

    @abstractmethod
    async def get_by_status(
        self,
        status: MediaStatus,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Media]:
        """Get media by status"""
        pass

    @abstractmethod
    async def get_without_embedding(
        self,
        limit: int = 100,
    ) -> list[Media]:
        """Get media without CLIP embeddings"""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        media_type: MediaType | None = None,
        user_id: UUID | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Media]:
        """Search media by title, description, tags"""
        pass

    @abstractmethod
    async def update_status(self, media_id: UUID, status: MediaStatus, error: str | None = None) -> None:
        """Update media status"""
        pass

    @abstractmethod
    async def add_variant(self, media_id: UUID, variant_data: dict) -> None:
        """Add media variant"""
        pass

    @abstractmethod
    async def set_moderation(
        self,
        media_id: UUID,
        moderator_id: UUID,
        approved: bool,
        notes: str | None = None,
    ) -> None:
        """Set moderation status"""
        pass

    @abstractmethod
    async def set_clip_embedding(self, media_id: UUID, embedding: list[float], embedding_id: str) -> None:
        """Set CLIP embedding"""
        pass

    @abstractmethod
    async def set_caption(self, media_id: UUID, caption: str, confidence: float) -> None:
        """Set AI-generated caption"""
        pass

    @abstractmethod
    async def add_landmark(self, media_id: UUID, landmark: dict) -> None:
        """Add detected landmark"""
        pass

    @abstractmethod
    async def increment_view(self, media_id: UUID) -> None:
        """Increment view count"""
        pass

    @abstractmethod
    async def increment_download(self, media_id: UUID) -> None:
        """Increment download count"""
        pass

    @abstractmethod
    async def increment_like(self, media_id: UUID) -> None:
        """Increment like count"""
        pass

    @abstractmethod
    async def get_stats(self) -> dict:
        """Get media statistics"""
        pass

    @abstractmethod
    async def cleanup_failed(self, days: int = 7) -> int:
        """Clean up failed uploads older than specified days"""
        pass
