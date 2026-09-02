"""
Application Ports - Repository interfaces (Ports for infrastructure)
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, TypeVar
from uuid import UUID

from ...domain.entities.conversation import Conversation, Message
from ...domain.entities.feedback import Feedback
from ...domain.entities.itinerary import Itinerary, ItineraryDay, ItineraryItem
from ...domain.entities.media import Media
from ...domain.entities.poi import POI, POICategory, POISource
from ...domain.entities.transit import TransitRoute, TransitTrip
from ...domain.entities.user import User
from ...domain.entities.weather import WeatherAlert, WeatherForecast
from ...domain.repositories.base import (
    BaseRepository,
    FilterParams,
    PaginatedResult,
    PaginationParams,
)
from ...domain.value_objects.coordinates import Coordinates

T = TypeVar('T')


# Repository Ports (interfaces that infrastructure must implement)
class UserRepositoryPort(BaseRepository[User, UUID], ABC):
    """User repository port"""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email"""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Get user by username"""
        pass

    @abstractmethod
    async def get_by_provider(self, provider: str, provider_id: str) -> User | None:
        """Get user by OAuth provider"""
        pass

    @abstractmethod
    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp"""
        pass

    @abstractmethod
    async def increment_itinerary_count(self, user_id: UUID) -> None:
        """Increment user's itinerary count"""
        pass

    @abstractmethod
    async def increment_favorites_count(self, user_id: UUID) -> None:
        """Increment user's favorites count"""
        pass

    @abstractmethod
    async def increment_reviews_count(self, user_id: UUID) -> None:
        """Increment user's reviews count"""
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Get user statistics"""
        pass

    @abstractmethod
    async def get_by_email_verification_token(self, token: str) -> User | None:
        """Get user by email verification token"""
        pass

    @abstractmethod
    async def get_by_password_reset_token(self, token: str) -> User | None:
        """Get user by password reset token"""
        pass


class ConversationRepositoryPort(BaseRepository[Conversation, UUID], ABC):
    """Conversation repository port"""

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Conversation]:
        """Get conversations by user ID"""
        pass

    @abstractmethod
    async def get_with_messages(
        self,
        conversation_id: UUID,
        message_limit: int = 50,
    ) -> Conversation | None:
        """Get conversation with messages"""
        pass

    @abstractmethod
    async def add_message(self, conversation_id: UUID, message: Message) -> None:
        """Add message to conversation"""
        pass

    @abstractmethod
    async def update_message(self, message: Message) -> None:
        """Update a message"""
        pass

    @abstractmethod
    async def get_unread_count(self, user_id: UUID) -> int:
        """Get unread message count for user"""
        pass


class ItineraryRepositoryPort(BaseRepository[Itinerary, UUID], ABC):
    """Itinerary repository port"""

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
        status: str | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Get itineraries by user ID"""
        pass

    @abstractmethod
    async def get_public_itineraries(
        self,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Get public itineraries"""
        pass

    @abstractmethod
    async def get_shared_with_user(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Get itineraries shared with user"""
        pass

    @abstractmethod
    async def add_day(self, itinerary_id: UUID, day: ItineraryDay) -> None:
        """Add day to itinerary"""
        pass

    @abstractmethod
    async def update_day(self, day: ItineraryDay) -> None:
        """Update itinerary day"""
        pass

    @abstractmethod
    async def remove_day(self, itinerary_id: UUID, day_id: UUID) -> None:
        """Remove day from itinerary"""
        pass

    @abstractmethod
    async def add_item(self, day_id: UUID, item: ItineraryItem) -> None:
        """Add item to itinerary day"""
        pass

    @abstractmethod
    async def update_item(self, item: ItineraryItem) -> None:
        """Update itinerary item"""
        pass

    @abstractmethod
    async def remove_item(self, day_id: UUID, item_id: UUID) -> None:
        """Remove item from itinerary day"""
        pass

    @abstractmethod
    async def reorder_items(self, day_id: UUID, item_ids: list[UUID]) -> None:
        """Reorder items in a day"""
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Get itinerary statistics"""
        pass


class POIRepositoryPort(BaseRepository[POI, UUID], ABC):
    """POI repository port"""

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


class TransitRepositoryPort(BaseRepository[TransitRoute, UUID], ABC):
    """Transit repository port"""

    @abstractmethod
    async def get_stops_nearby(
        self,
        coordinates: Coordinates,
        radius_meters: float = 500,
        modes: list[str] | None = None,
    ) -> list[TransitStop]:
        """Get transit stops near coordinates"""
        pass

    @abstractmethod
    async def get_stop_by_id(self, stop_id: str) -> TransitStop | None:
        """Get stop by ID"""
        pass

    @abstractmethod
    async def get_routes_for_stop(self, stop_id: str) -> list[TransitRoute]:
        """Get routes serving a stop"""
        pass

    @abstractmethod
    async def get_route_by_id(self, route_id: str) -> TransitRoute | None:
        """Get route by ID"""
        pass

    @abstractmethod
    async def get_trips_for_route(
        self,
        route_id: str,
        date: datetime | None = None,
        direction_id: int | None = None,
    ) -> list[TransitTrip]:
        """Get trips for a route"""
        pass

    @abstractmethod
    async def get_schedule_for_stop(
        self,
        stop_id: str,
        date: datetime,
        route_ids: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get schedule for a stop"""
        pass

    @abstractmethod
    async def get_realtime_arrivals(
        self,
        stop_id: str,
        route_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get real-time arrivals for a stop"""
        pass

    @abstractmethod
    async def get_alerts(
        self,
        route_ids: list[str] | None = None,
        stop_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get transit alerts"""
        pass

    @abstractmethod
    async def get_vehicle_positions(
        self,
        route_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get real-time vehicle positions"""
        pass


class WeatherRepositoryPort(BaseRepository[WeatherForecast, UUID], ABC):
    """Weather repository port"""

    @abstractmethod
    async def get_current_weather(
        self,
        coordinates: Coordinates,
    ) -> dict[str, Any] | None:
        """Get current weather"""
        pass

    @abstractmethod
    async def get_forecast(
        self,
        coordinates: Coordinates,
        days: int = 7,
    ) -> WeatherForecast | None:
        """Get weather forecast"""
        pass

    @abstractmethod
    async def get_alerts(
        self,
        coordinates: Coordinates,
    ) -> list[WeatherAlert]:
        """Get weather alerts"""
        pass

    @abstractmethod
    async def get_historical(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get historical weather"""
        pass


class MediaRepositoryPort(BaseRepository[Media, UUID], ABC):
    """Media repository port"""

    @abstractmethod
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> list[Media]:
        """Get media for an entity"""
        pass

    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Media]:
        """Get media by user"""
        pass

    @abstractmethod
    async def update_processing_status(
        self,
        media_id: UUID,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update media processing status"""
        pass


class FeedbackRepositoryPort(BaseRepository[Feedback, UUID], ABC):
    """Feedback repository port"""

    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback by user"""
        pass

    @abstractmethod
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback for an entity"""
        pass

    @abstractmethod
    async def get_pending_moderation(
        self,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback pending moderation"""
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Get feedback statistics"""
        pass


class AnalyticsRepositoryPort(ABC):
    """Analytics repository port"""

    @abstractmethod
    async def track_event(
        self,
        event_name: str,
        user_id: UUID | None,
        properties: dict[str, Any],
        timestamp: datetime | None = None,
    ) -> None:
        """Track an analytics event"""
        pass

    @abstractmethod
    async def get_user_metrics(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Get user metrics"""
        pass

    @abstractmethod
    async def get_system_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Get system metrics"""
        pass

    @abstractmethod
    async def get_funnel_metrics(
        self,
        funnel_name: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Get funnel metrics"""
        pass
