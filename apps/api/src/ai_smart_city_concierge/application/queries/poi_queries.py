"""
POI Queries (CQRS Read Side)
"""
from dataclasses import dataclass
from uuid import UUID

from ...domain.entities.poi import POICategory, POISource
from ...domain.value_objects.coordinates import Coordinates
from ..dto.response import PaginatedResponse, POIResponse
from ..ports.repositories import POIRepositoryPort


@dataclass
class GetPOIQuery:
    """Query to get POI by ID"""
    poi_id: UUID
    include_embedding: bool = False


@dataclass
class GetPOIByExternalIDQuery:
    """Query to get POI by external ID"""
    external_id: str
    source: POISource


@dataclass
class ListPOIsQuery:
    """Query to list POIs with pagination and filters"""
    page: int = 1
    page_size: int = 20
    category: POICategory | None = None
    source: POISource | None = None
    verified_only: bool = False
    active_only: bool = True
    sort_by: str = "popularity_score"
    sort_order: str = "desc"


@dataclass
class SearchPOIsQuery:
    """Query to search POIs"""
    query: str
    coordinates: Coordinates | None = None
    radius_meters: float | None = None
    categories: list[POICategory] | None = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "relevance"
    sort_order: str = "desc"


@dataclass
class GetNearbyPOIsQuery:
    """Query to get nearby POIs"""
    coordinates: Coordinates
    radius_meters: float = 1000
    categories: list[POICategory] | None = None
    page: int = 1
    page_size: int = 20


@dataclass
class GetPOIsWithinBoundsQuery:
    """Query to get POIs within bounding box"""
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float
    categories: list[POICategory] | None = None
    page: int = 1
    page_size: int = 20


@dataclass
class GetPopularPOIsQuery:
    """Query to get popular POIs"""
    coordinates: Coordinates | None = None
    radius_meters: float | None = None
    category: POICategory | None = None
    limit: int = 20


@dataclass
class GetTrendingPOIsQuery:
    """Query to get trending POIs"""
    coordinates: Coordinates | None = None
    radius_meters: float | None = None
    days: int = 7
    limit: int = 20


@dataclass
class GetPOIsBySourceQuery:
    """Query to get POIs by source"""
    source: POISource
    page: int = 1
    page_size: int = 20


@dataclass
class GetVerifiedPOIsQuery:
    """Query to get verified POIs"""
    page: int = 1
    page_size: int = 20


@dataclass
class GetUnverifiedPOIsQuery:
    """Query to get unverified POIs"""
    page: int = 1
    page_size: int = 20


@dataclass
class GetPOIsWithoutEmbeddingQuery:
    """Query to get POIs without embeddings"""
    limit: int = 100


@dataclass
class GetPOIStatsQuery:
    """Query to get POI statistics"""
    pass


class POIQueryHandler:
    """Handler for POI queries"""

    def __init__(self, poi_repository: POIRepositoryPortPort):
        self.poi_repository = poi_repository

    async def handle_get_poi(self, query: GetPOIQuery) -> POIResponse | None:
        """Handle get POI query"""
        poi = await self.poi_repository.get_by_id(query.poi_id)
        if not poi:
            return None
        return POIResponse.from_entity(poi, include_embedding=query.include_embedding)

    async def handle_get_poi_by_external_id(self, query: GetPOIByExternalIDQuery) -> POIResponse | None:
        """Handle get POI by external ID query"""
        poi = await self.poi_repository.get_by_external_id(query.external_id, query.source)
        if not poi:
            return None
        return POIResponse.from_entity(poi)

    async def handle_list_pois(self, query: ListPOIsQuery) -> PaginatedResponse[POIResponse]:
        """Handle list POIs query"""
        from ..ports.repositories import FilterParams, PaginationParams, SortParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)
        sort = SortParams(field=query.sort_by, order=query.sort_order)

        filters = {}
        if query.category:
            filters["category"] = query.category.value
        if query.source:
            filters["source"] = query.source.value
        if query.verified_only:
            filters["is_verified"] = True
        if query.active_only:
            filters["is_active"] = True

        filter_params = FilterParams(filters=filters) if filters else None

        result = await self.poi_repository.list(pagination, sort, filter_params)

        return PaginatedResponse(
            items=[POIResponse.from_entity(poi) for poi in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_search_pois(self, query: SearchPOIsQuery) -> PaginatedResponse[POIResponse]:
        """Handle search POIs query"""
        from ..ports.repositories import FilterParams, PaginationParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)

        filters = {}
        if query.categories:
            filters["categories"] = [c.value for c in query.categories]

        filter_params = FilterParams(filters=filters) if filters else None

        result = await self.poi_repository.search(
            query=query.query,
            coordinates=query.coordinates,
            radius_meters=query.radius_meters,
            categories=query.categories,
            pagination=pagination,
            filters=filter_params,
        )

        return PaginatedResponse(
            items=[POIResponse.from_entity(poi) for poi in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_nearby_pois(self, query: GetNearbyPOIsQuery) -> PaginatedResponse[POIResponse]:
        """Handle get nearby POIs query"""
        from ..ports.repositories import FilterParams, PaginationParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)

        filters = {}
        if query.categories:
            filters["categories"] = [c.value for c in query.categories]

        filter_params = FilterParams(filters=filters) if filters else None

        result = await self.poi_repository.get_nearby(
            coordinates=query.coordinates,
            radius_meters=query.radius_meters,
            categories=query.categories,
            pagination=pagination,
            filters=filter_params,
        )

        return PaginatedResponse(
            items=[POIResponse.from_entity(poi) for poi in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_pois_within_bounds(self, query: GetPOIsWithinBoundsQuery) -> PaginatedResponse[POIResponse]:
        """Handle get POIs within bounds query"""
        from ..ports.repositories import PaginationParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)

        result = await self.poi_repository.get_within_bounds(
            min_lat=query.min_lat,
            max_lat=query.max_lat,
            min_lng=query.min_lng,
            max_lng=query.max_lng,
            categories=query.categories,
            pagination=pagination,
        )

        return PaginatedResponse(
            items=[POIResponse.from_entity(poi) for poi in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_popular_pois(self, query: GetPopularPOIsQuery) -> list[POIResponse]:
        """Handle get popular POIs query"""
        pois = await self.poi_repository.get_popular(
            coordinates=query.coordinates,
            radius_meters=query.radius_meters,
            category=query.category,
            limit=query.limit,
        )
        return [POIResponse.from_entity(poi) for poi in pois]

    async def handle_get_trending_pois(self, query: GetTrendingPOIsQuery) -> list[POIResponse]:
        """Handle get trending POIs query"""
        pois = await self.poi_repository.get_trending(
            coordinates=query.coordinates,
            radius_meters=query.radius_meters,
            days=query.days,
            limit=query.limit,
        )
        return [POIResponse.from_entity(poi) for poi in pois]

    async def handle_get_pois_by_source(self, query: GetPOIsBySourceQuery) -> PaginatedResponse[POIResponse]:
        """Handle get POIs by source query"""
        from ..ports.repositories import PaginationParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)
        result = await self.poi_repository.get_by_source(query.source, pagination)

        return PaginatedResponse(
            items=[POIResponse.from_entity(poi) for poi in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_verified_pois(self, query: GetVerifiedPOIsQuery) -> PaginatedResponse[POIResponse]:
        """Handle get verified POIs query"""
        from ..ports.repositories import PaginationParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)
        result = await self.poi_repository.get_verified(pagination)

        return PaginatedResponse(
            items=[POIResponse.from_entity(poi) for poi in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_unverified_pois(self, query: GetUnverifiedPOIsQuery) -> PaginatedResponse[POIResponse]:
        """Handle get unverified POIs query"""
        from ..ports.repositories import PaginationParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)
        result = await self.poi_repository.get_unverified(pagination)

        return PaginatedResponse(
            items=[POIResponse.from_entity(poi) for poi in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_pois_without_embedding(self, query: GetPOIsWithoutEmbeddingQuery) -> list[POIResponse]:
        """Handle get POIs without embedding query"""
        pois = await self.poi_repository.get_without_embedding(query.limit)
        return [POIResponse.from_entity(poi) for poi in pois]

    async def handle_get_poi_stats(self, query: GetPOIStatsQuery) -> dict:
        """Handle get POI stats query"""
        return await self.poi_repository.get_stats()
