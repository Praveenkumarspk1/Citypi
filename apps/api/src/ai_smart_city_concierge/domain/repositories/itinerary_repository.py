"""
Itinerary Repository Interface
"""
from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from ..entities.itinerary import Itinerary, ItineraryDay, ItineraryItem, ItineraryStatus
from .base import BaseRepository, FilterParams, PaginatedResult, PaginationParams


class ItineraryRepository(BaseRepository[Itinerary, UUID], ABC):
    """Itinerary repository interface"""

    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
        status: ItineraryStatus | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Get itineraries by user"""
        pass

    @abstractmethod
    async def get_public(
        self,
        pagination: PaginationParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Get public itineraries"""
        pass

    @abstractmethod
    async def get_by_share_token(self, share_token: str) -> Itinerary | None:
        """Get itinerary by share token"""
        pass

    @abstractmethod
    async def get_collaborative(self, user_id: UUID) -> list[Itinerary]:
        """Get itineraries where user is collaborator"""
        pass

    @abstractmethod
    async def get_by_date_range(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[Itinerary]:
        """Get itineraries within date range"""
        pass

    @abstractmethod
    async def get_active_by_user(self, user_id: UUID) -> list[Itinerary]:
        """Get active itineraries for user"""
        pass

    @abstractmethod
    async def add_day(self, itinerary_id: UUID, day: ItineraryDay) -> None:
        """Add day to itinerary"""
        pass

    @abstractmethod
    async def update_day(self, itinerary_id: UUID, day: ItineraryDay) -> None:
        """Update day in itinerary"""
        pass

    @abstractmethod
    async def remove_day(self, itinerary_id: UUID, day_id: UUID) -> bool:
        """Remove day from itinerary"""
        pass

    @abstractmethod
    async def add_item(self, itinerary_id: UUID, day_id: UUID, item: ItineraryItem) -> None:
        """Add item to itinerary day"""
        pass

    @abstractmethod
    async def update_item(self, itinerary_id: UUID, day_id: UUID, item: ItineraryItem) -> None:
        """Update item in itinerary day"""
        pass

    @abstractmethod
    async def remove_item(self, itinerary_id: UUID, day_id: UUID, item_id: UUID) -> bool:
        """Remove item from itinerary day"""
        pass

    @abstractmethod
    async def reorder_items(self, itinerary_id: UUID, day_id: UUID, item_ids: list[UUID]) -> None:
        """Reorder items in day"""
        pass

    @abstractmethod
    async def reorder_days(self, itinerary_id: UUID, day_ids: list[UUID]) -> None:
        """Reorder days in itinerary"""
        pass

    @abstractmethod
    async def add_collaborator(self, itinerary_id: UUID, user_id: UUID) -> None:
        """Add collaborator to itinerary"""
        pass

    @abstractmethod
    async def remove_collaborator(self, itinerary_id: UUID, user_id: UUID) -> None:
        """Remove collaborator from itinerary"""
        pass

    @abstractmethod
    async def publish(self, itinerary_id: UUID, share_token: str) -> None:
        """Publish itinerary"""
        pass

    @abstractmethod
    async def unpublish(self, itinerary_id: UUID) -> None:
        """Unpublish itinerary"""
        pass

    @abstractmethod
    async def get_popular(
        self,
        limit: int = 20,
        city: str | None = None,
        country: str | None = None,
    ) -> list[Itinerary]:
        """Get popular public itineraries"""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        user_id: UUID | None = None,
        include_public: bool = True,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Search itineraries"""
        pass

    @abstractmethod
    async def get_user_stats(self, user_id: UUID) -> dict:
        """Get itinerary statistics for user"""
        pass
