"""
POI Repository Interface
"""
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from ..entities.poi import POI, POICategory, POISource
from ..value_objects.coordinates import Coordinates
from .base import BaseRepository, FilterParams, PaginatedResult, PaginationParams


class POIRepository(BaseRepository[POI, UUID], ABC):
    """POI repository interface"""

    @abstractmethod
    async def get_by_external_id(self, external_id: str, source: POISource) -> POI | None:
        """Get POI by external ID and source"""
        pass

    @abstractmethod
    async def get_by_category(
        self,
        category: POICategory,
        pagination: PaginationParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get POIs by category"""
        pass

    @abstractmethod
    async def get_nearby(
        self,
        coordinates: Coordinates,
        radius_meters: float,
        categories: list[POICategory] | None = None,
        pagination: PaginationParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get POIs near coordinates"""
        pass

    @abstractmethod
    async def get_within_bounds(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        categories: list[POICategory] | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get POIs within bounding box"""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        categories: list[POICategory] | None = None,
        pagination: PaginationParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[POI]:
        """Search POIs by name, description, tags"""
        pass

    @abstractmethod
    async def get_popular(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        category: POICategory | None = None,
        limit: int = 20,
    ) -> list[POI]:
        """Get popular POIs"""
        pass

    @abstractmethod
    async def get_trending(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        days: int = 7,
        limit: int = 20,
    ) -> list[POI]:
        """Get trending POIs"""
        pass

    @abstractmethod
    async def get_by_source(
        self,
        source: POISource,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get POIs by source"""
        pass

    @abstractmethod
    async def get_verified(
        self,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get verified POIs"""
        pass

    @abstractmethod
    async def get_unverified(
        self,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get unverified POIs"""
        pass

    @abstractmethod
    async def get_without_embedding(
        self,
        limit: int = 100,
    ) -> list[POI]:
        """Get POIs without vector embeddings"""
        pass

    @abstractmethod
    async def update_rating(self, poi_id: UUID, rating: float, review_count: int) -> None:
        """Update POI rating"""
        pass

    @abstractmethod
    async def increment_visit_count(self, poi_id: UUID) -> None:
        """Increment POI visit count"""
        pass

    @abstractmethod
    async def update_popularity(self, poi_id: UUID, score: float) -> None:
        """Update POI popularity score"""
        pass

    @abstractmethod
    async def set_embedding_id(self, poi_id: UUID, embedding_id: str) -> None:
        """Set vector embedding reference"""
        pass

    @abstractmethod
    async def get_by_ids_with_details(self, ids: list[UUID]) -> list[POI]:
        """Get POIs by IDs with full details"""
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Get POI statistics"""
        pass

    @abstractmethod
    async def bulk_upsert(self, pois: list[POI]) -> list[POI]:
        """Bulk upsert POIs"""
        pass

    @abstractmethod
    async def delete_by_source(self, source: POISource) -> int:
        """Delete all POIs from a source"""
        pass
