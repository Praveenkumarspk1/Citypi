"""
Itinerary Queries (CQRS Read Side)
"""
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from ...domain.entities.itinerary import ItineraryStatus
from ..dto.response import ItineraryResponse, PaginatedResponse
from ..ports.repositories import ItineraryRepositoryPort


@dataclass
class GetItineraryQuery:
    """Query to get itinerary by ID"""
    itinerary_id: UUID
    include_days: bool = True


@dataclass
class GetItineraryByShareTokenQuery:
    """Query to get itinerary by share token"""
    share_token: str


@dataclass
class GetItinerariesByUserQuery:
    """Query to get itineraries by user"""
    user_id: UUID
    status: ItineraryStatus | None = None
    page: int = 1
    page_size: int = 20


@dataclass
class GetPublicItinerariesQuery:
    """Query to get public itineraries"""
    page: int = 1
    page_size: int = 20
    city: str | None = None
    country: str | None = None
    budget_level: str | None = None
    pace: str | None = None


@dataclass
class GetCollaborativeItinerariesQuery:
    """Query to get collaborative itineraries for user"""
    user_id: UUID


@dataclass
class GetItinerariesByDateRangeQuery:
    """Query to get itineraries by date range"""
    user_id: UUID
    start_date: date
    end_date: date


@dataclass
class GetActiveItinerariesByUserQuery:
    """Query to get active itineraries by user"""
    user_id: UUID


@dataclass
class SearchItinerariesQuery:
    """Query to search itineraries"""
    query: str
    user_id: UUID | None = None
    include_public: bool = True
    page: int = 1
    page_size: int = 20


@dataclass
class GetPopularItinerariesQuery:
    """Query to get popular itineraries"""
    limit: int = 20
    city: str | None = None
    country: str | None = None


@dataclass
class GetItineraryStatsQuery:
    """Query to get itinerary statistics for user"""
    user_id: UUID


class ItineraryQueryHandler:
    """Handler for itinerary queries"""

    def __init__(self, itinerary_repository: ItineraryRepositoryPortPort):
        self.itinerary_repository = itinerary_repository

    async def handle_get_itinerary(self, query: GetItineraryQuery) -> ItineraryResponse | None:
        """Handle get itinerary query"""
        itinerary = await self.itinerary_repository.get_by_id(query.itinerary_id)
        if not itinerary:
            return None
        return ItineraryResponse.from_entity(itinerary, include_days=query.include_days)

    async def handle_get_itinerary_by_share_token(self, query: GetItineraryByShareTokenQuery) -> ItineraryResponse | None:
        """Handle get itinerary by share token query"""
        itinerary = await self.itinerary_repository.get_by_share_token(query.share_token)
        if not itinerary:
            return None
        return ItineraryResponse.from_entity(itinerary, include_days=True)

    async def handle_get_itineraries_by_user(self, query: GetItinerariesByUserQuery) -> PaginatedResponse[ItineraryResponse]:
        """Handle get itineraries by user query"""
        from ..ports.repositories import PaginationParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)
        result = await self.itinerary_repository.get_by_user(
            query.user_id,
            status=query.status,
            pagination=pagination,
        )

        return PaginatedResponse(
            items=[ItineraryResponse.from_entity(itin, include_days=True) for itin in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_public_itineraries(self, query: GetPublicItinerariesQuery) -> PaginatedResponse[ItineraryResponse]:
        """Handle get public itineraries query"""
        from ..ports.repositories import FilterParams, PaginationParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)

        filters = {}
        if query.city:
            filters["city"] = query.city
        if query.country:
            filters["country"] = query.country
        if query.budget_level:
            filters["budget_level"] = query.budget_level
        if query.pace:
            filters["pace"] = query.pace

        filter_params = FilterParams(filters=filters) if filters else None

        result = await self.itinerary_repository.get_public(pagination, filter_params)

        return PaginatedResponse(
            items=[ItineraryResponse.from_entity(itin, include_days=True) for itin in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_collaborative_itineraries(self, query: GetCollaborativeItinerariesQuery) -> list[ItineraryResponse]:
        """Handle get collaborative itineraries query"""
        itineraries = await self.itinerary_repository.get_collaborative(query.user_id)
        return [ItineraryResponse.from_entity(itin, include_days=True) for itin in itineraries]

    async def handle_get_itineraries_by_date_range(self, query: GetItinerariesByDateRangeQuery) -> list[ItineraryResponse]:
        """Handle get itineraries by date range query"""
        itineraries = await self.itinerary_repository.get_by_date_range(
            query.user_id,
            query.start_date,
            query.end_date,
        )
        return [ItineraryResponse.from_entity(itin, include_days=True) for itin in itineraries]

    async def handle_get_active_itineraries_by_user(self, query: GetActiveItinerariesByUserQuery) -> list[ItineraryResponse]:
        """Handle get active itineraries by user query"""
        itineraries = await self.itinerary_repository.get_active_by_user(query.user_id)
        return [ItineraryResponse.from_entity(itin, include_days=True) for itin in itineraries]

    async def handle_search_itineraries(self, query: SearchItinerariesQuery) -> PaginatedResponse[ItineraryResponse]:
        """Handle search itineraries query"""
        from ..ports.repositories import PaginationParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)
        result = await self.itinerary_repository.search(
            query=query.query,
            user_id=query.user_id,
            include_public=query.include_public,
            pagination=pagination,
        )

        return PaginatedResponse(
            items=[ItineraryResponse.from_entity(itin, include_days=True) for itin in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_popular_itineraries(self, query: GetPopularItinerariesQuery) -> list[ItineraryResponse]:
        """Handle get popular itineraries query"""
        itineraries = await self.itinerary_repository.get_popular(
            limit=query.limit,
            city=query.city,
            country=query.country,
        )
        return [ItineraryResponse.from_entity(itin, include_days=True) for itin in itineraries]

    async def handle_get_itinerary_stats(self, query: GetItineraryStatsQuery) -> dict:
        """Handle get itinerary stats query"""
        return await self.itinerary_repository.get_user_stats(query.user_id)
