"""
POI Service - Search, categorization, enrichment
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from ..entities.poi import POI, POICategory, POISource
from ..value_objects.coordinates import Coordinates


class POISearchType(StrEnum):
    """POI search types"""
    TEXT = "text"
    CATEGORY = "category"
    NEARBY = "nearby"
    BOUNDS = "bounds"
    SIMILAR = "similar"
    TRENDING = "trending"
    POPULAR = "popular"


@dataclass(frozen=True)
class POISearchRequest:
    """POI search request"""
    query: str | None = None
    coordinates: Coordinates | None = None
    radius_meters: float | None = None
    categories: list[POICategory] = field(default_factory=list)
    subcategories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    min_rating: float | None = None
    max_price_level: int | None = None
    wheelchair_accessible: bool | None = None
    open_now: bool = False
    source: POISource | None = None
    verified_only: bool = False
    has_photos: bool = False
    has_wifi: bool = False
    has_outdoor_seating: bool = False
    accepts_credit_cards: bool = False
    accepts_cash: bool = False
    page: int = 1
    page_size: int = 20
    sort_by: str = "relevance"  # relevance, distance, rating, popularity, review_count
    sort_order: str = "desc"

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "coordinates": self.coordinates.to_dict() if self.coordinates else None,
            "radius_meters": self.radius_meters,
            "categories": [c.value for c in self.categories],
            "subcategories": self.subcategories,
            "tags": self.tags,
            "min_rating": self.min_rating,
            "max_price_level": self.max_price_level,
            "wheelchair_accessible": self.wheelchair_accessible,
            "open_now": self.open_now,
            "source": self.source.value if self.source else None,
            "verified_only": self.verified_only,
            "has_photos": self.has_photos,
            "has_wifi": self.has_wifi,
            "has_outdoor_seating": self.has_outdoor_seating,
            "accepts_credit_cards": self.accepts_credit_cards,
            "accepts_cash": self.accepts_cash,
            "page": self.page,
            "page_size": self.page_size,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
        }


@dataclass(frozen=True)
class POISearchResult:
    """POI search result"""
    pois: list[POI]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    search_time_ms: float
    facets: dict[str, dict[str, int]] = field(default_factory=dict)  # category -> count, etc.

    def to_dict(self) -> dict:
        return {
            "pois": [poi.to_dict() for poi in self.pois],
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
            "search_time_ms": self.search_time_ms,
            "facets": self.facets,
        }


@dataclass(frozen=True)
class POIEnrichmentRequest:
    """Request to enrich POI data"""
    poi_id: UUID
    enrich_photos: bool = True
    enrich_reviews: bool = True
    enrich_opening_hours: bool = True
    enrich_contact: bool = True
    enrich_accessibility: bool = True
    enrich_transit: bool = False
    enrich_weather: bool = False
    external_sources: list[str] = field(default_factory=list)  # google_places, foursquare, etc.


@dataclass(frozen=True)
class POIEnrichmentResult:
    """Result of POI enrichment"""
    poi_id: UUID
    enriched_fields: list[str]
    photos_added: int = 0
    reviews_added: int = 0
    opening_hours_updated: bool = False
    contact_updated: bool = False
    accessibility_updated: bool = False
    transit_info_added: bool = False
    weather_info_added: bool = False
    errors: list[str] = field(default_factory=list)
    enriched_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "poi_id": str(self.poi_id),
            "enriched_fields": self.enriched_fields,
            "photos_added": self.photos_added,
            "reviews_added": self.reviews_added,
            "opening_hours_updated": self.opening_hours_updated,
            "contact_updated": self.contact_updated,
            "accessibility_updated": self.accessibility_updated,
            "transit_info_added": self.transit_info_added,
            "weather_info_added": self.weather_info_added,
            "errors": self.errors,
            "enriched_at": self.enriched_at.isoformat(),
        }


@dataclass(frozen=True)
class POICategoryStats:
    """Statistics for a POI category"""
    category: POICategory
    count: int
    avg_rating: float
    avg_price_level: float
    top_subcategories: list[dict[str, int]] = field(default_factory=list)
    top_tags: list[dict[str, int]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "count": self.count,
            "avg_rating": self.avg_rating,
            "avg_price_level": self.avg_price_level,
            "top_subcategories": self.top_subcategories,
            "top_tags": self.top_tags,
        }


class POIService(ABC):
    """Abstract POI service"""

    @abstractmethod
    async def search_pois(
        self,
        request: POISearchRequest,
    ) -> POISearchResult:
        """Search POIs with various filters"""
        pass

    @abstractmethod
    async def get_poi_by_id(
        self,
        poi_id: UUID,
        include_embedding: bool = False,
    ) -> POI | None:
        """Get POI by ID"""
        pass

    @abstractmethod
    async def get_poi_by_external_id(
        self,
        external_id: str,
        source: POISource,
    ) -> POI | None:
        """Get POI by external ID"""
        pass

    @abstractmethod
    async def get_nearby_pois(
        self,
        coordinates: Coordinates,
        radius_meters: float = 1000,
        categories: list[POICategory] | None = None,
        limit: int = 20,
    ) -> list[POI]:
        """Get POIs near coordinates"""
        pass

    @abstractmethod
    async def get_pois_within_bounds(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        categories: list[POICategory] | None = None,
        limit: int = 50,
    ) -> list[POI]:
        """Get POIs within bounding box"""
        pass

    @abstractmethod
    async def get_similar_pois(
        self,
        poi_id: UUID,
        limit: int = 10,
    ) -> list[POI]:
        """Get POIs similar to a given POI"""
        pass

    @abstractmethod
    async def get_popular_pois(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        category: POICategory | None = None,
        limit: int = 20,
    ) -> list[POI]:
        """Get popular POIs"""
        pass

    @abstractmethod
    async def get_trending_pois(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        days: int = 7,
        limit: int = 20,
    ) -> list[POI]:
        """Get trending POIs"""
        pass

    @abstractmethod
    async def enrich_poi(
        self,
        request: POIEnrichmentRequest,
    ) -> POIEnrichmentResult:
        """Enrich POI with external data"""
        pass

    @abstractmethod
    async def bulk_enrich_pois(
        self,
        poi_ids: list[UUID],
        request: POIEnrichmentRequest,
    ) -> list[POIEnrichmentResult]:
        """Enrich multiple POIs"""
        pass

    @abstractmethod
    async def categorize_poi(
        self,
        poi: POI,
        use_ml: bool = True,
    ) -> POICategory:
        """Categorize a POI using ML or rules"""
        pass

    @abstractmethod
    async def suggest_categories(
        self,
        name: str,
        description: str,
        coordinates: Coordinates,
    ) -> list[POICategory]:
        """Suggest categories for a new POI"""
        pass

    @abstractmethod
    async def get_category_stats(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
    ) -> list[POICategoryStats]:
        """Get statistics by category"""
        pass

    @abstractmethod
    async def update_poi_rating(
        self,
        poi_id: UUID,
        rating: float,
        review_count: int,
    ) -> None:
        """Update POI rating"""
        pass

    @abstractmethod
    async def increment_visit_count(
        self,
        poi_id: UUID,
    ) -> None:
        """Increment POI visit count"""
        pass

    @abstractmethod
    async def update_popularity(
        self,
        poi_id: UUID,
        score: float,
    ) -> None:
        """Update POI popularity score"""
        pass

    @abstractmethod
    async def set_embedding_id(
        self,
        poi_id: UUID,
        embedding_id: str,
    ) -> None:
        """Set vector embedding reference"""
        pass

    @abstractmethod
    async def get_pois_without_embedding(
        self,
        limit: int = 100,
    ) -> list[POI]:
        """Get POIs without vector embeddings"""
        pass

    @abstractmethod
    async def bulk_upsert_pois(
        self,
        pois: list[POI],
    ) -> list[POI]:
        """Bulk upsert POIs"""
        pass

    @abstractmethod
    async def delete_pois_by_source(
        self,
        source: POISource,
    ) -> int:
        """Delete all POIs from a source"""
        pass


class POIServiceImpl(POIService):
    """Default implementation of POI service"""

    def __init__(
        self,
        poi_repository=None,
        embedding_service=None,
        external_apis: dict[str, Any] = None,
        ml_categorizer=None,
    ):
        self.poi_repository = poi_repository
        self.embedding_service = embedding_service
        self.external_apis = external_apis or {}
        self.ml_categorizer = ml_categorizer

    async def search_pois(
        self,
        request: POISearchRequest,
    ) -> POISearchResult:
        """Search POIs with various filters"""
        # Placeholder - would delegate to repository
        return POISearchResult(
            pois=[],
            total=0,
            page=request.page,
            page_size=request.page_size,
            total_pages=0,
            has_next=False,
            has_prev=False,
            search_time_ms=0.0,
        )

    async def get_poi_by_id(
        self,
        poi_id: UUID,
        include_embedding: bool = False,
    ) -> POI | None:
        """Get POI by ID"""
        if self.poi_repository:
            return await self.poi_repository.get_by_id(poi_id)
        return None

    async def get_poi_by_external_id(
        self,
        external_id: str,
        source: POISource,
    ) -> POI | None:
        """Get POI by external ID"""
        if self.poi_repository:
            return await self.poi_repository.get_by_external_id(external_id, source)
        return None

    async def get_nearby_pois(
        self,
        coordinates: Coordinates,
        radius_meters: float = 1000,
        categories: list[POICategory] | None = None,
        limit: int = 20,
    ) -> list[POI]:
        """Get POIs near coordinates"""
        if self.poi_repository:
            return await self.poi_repository.get_nearby(
                coordinates, radius_meters, categories, limit=limit
            )
        return []

    async def get_pois_within_bounds(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        categories: list[POICategory] | None = None,
        limit: int = 50,
    ) -> list[POI]:
        """Get POIs within bounding box"""
        if self.poi_repository:
            return await self.poi_repository.get_within_bounds(
                min_lat, max_lat, min_lng, max_lng, categories, limit=limit
            )
        return []

    async def get_similar_pois(
        self,
        poi_id: UUID,
        limit: int = 10,
    ) -> list[POI]:
        """Get POIs similar to a given POI"""
        # Would use embeddings for similarity search
        return []

    async def get_popular_pois(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        category: POICategory | None = None,
        limit: int = 20,
    ) -> list[POI]:
        """Get popular POIs"""
        if self.poi_repository:
            return await self.poi_repository.get_popular(
                coordinates, radius_meters, category, limit
            )
        return []

    async def get_trending_pois(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        days: int = 7,
        limit: int = 20,
    ) -> list[POI]:
        """Get trending POIs"""
        if self.poi_repository:
            return await self.poi_repository.get_trending(
                coordinates, radius_meters, days, limit
            )
        return []

    async def enrich_poi(
        self,
        request: POIEnrichmentRequest,
    ) -> POIEnrichmentResult:
        """Enrich POI with external data"""
        # Placeholder - would call external APIs
        return POIEnrichmentResult(
            poi_id=request.poi_id,
            enriched_fields=[],
        )

    async def bulk_enrich_pois(
        self,
        poi_ids: list[UUID],
        request: POIEnrichmentRequest,
    ) -> list[POIEnrichmentResult]:
        """Enrich multiple POIs"""
        results = []
        for poi_id in poi_ids:
            req = POIEnrichmentRequest(poi_id=poi_id)
            results.append(await self.enrich_poi(req))
        return results

    async def categorize_poi(
        self,
        poi: POI,
        use_ml: bool = True,
    ) -> POICategory:
        """Categorize a POI using ML or rules"""
        # Placeholder - would use ML model or rule-based categorization
        return poi.category

    async def suggest_categories(
        self,
        name: str,
        description: str,
        coordinates: Coordinates,
    ) -> list[POICategory]:
        """Suggest categories for a new POI"""
        # Placeholder - would use ML or keyword matching
        return [POICategory.OTHER]

    async def get_category_stats(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
    ) -> list[POICategoryStats]:
        """Get statistics by category"""
        return []

    async def update_poi_rating(
        self,
        poi_id: UUID,
        rating: float,
        review_count: int,
    ) -> None:
        """Update POI rating"""
        if self.poi_repository:
            await self.poi_repository.update_rating(poi_id, rating, review_count)

    async def increment_visit_count(
        self,
        poi_id: UUID,
    ) -> None:
        """Increment POI visit count"""
        if self.poi_repository:
            await self.poi_repository.increment_visit_count(poi_id)

    async def update_popularity(
        self,
        poi_id: UUID,
        score: float,
    ) -> None:
        """Update POI popularity score"""
        if self.poi_repository:
            await self.poi_repository.update_popularity(poi_id, score)

    async def set_embedding_id(
        self,
        poi_id: UUID,
        embedding_id: str,
    ) -> None:
        """Set vector embedding reference"""
        if self.poi_repository:
            await self.poi_repository.set_embedding_id(poi_id, embedding_id)

    async def get_pois_without_embedding(
        self,
        limit: int = 100,
    ) -> list[POI]:
        """Get POIs without vector embeddings"""
        if self.poi_repository:
            return await self.poi_repository.get_without_embedding(limit)
        return []

    async def bulk_upsert_pois(
        self,
        pois: list[POI],
    ) -> list[POI]:
        """Bulk upsert POIs"""
        if self.poi_repository:
            return await self.poi_repository.bulk_upsert(pois)
        return pois

    async def delete_pois_by_source(
        self,
        source: POISource,
    ) -> int:
        """Delete all POIs from a source"""
        if self.poi_repository:
            return await self.poi_repository.delete_by_source(source)
        return 0
