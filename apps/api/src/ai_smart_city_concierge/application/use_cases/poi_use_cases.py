"""
POI Application Use Cases
"""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ...domain.entities.poi import POI, POICategory, POISource
from ...domain.repositories.base import PaginatedResult, PaginationParams, SortParams
from ...domain.repositories.poi_repository import POIRepository
from ...domain.specifications.poi_specification import (
    AccessiblePOISpec,
    ActivePOISpec,
    CategoryPOISpec,
    HasPhotosPOISpec,
    HasWifiPOISpec,
    HighlyRatedPOISpec,
    NearbyPOISpec,
    OpenNowPOISpec,
    PriceRangePOISpec,
    SearchPOISpec,
    VerifiedPOISpec,
)
from ...domain.value_objects.accessibility import AccessibilityInfo
from ...domain.value_objects.coordinates import Coordinates
from ...domain.value_objects.opening_hours import OpeningHours


@dataclass
class CreatePOIRequest:
    """Request to create a POI"""
    name: str
    description: str
    category: POICategory
    coordinates: Coordinates
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    opening_hours: OpeningHours | None = None
    price_level: int | None = None
    currency: str = "USD"
    accessibility: AccessibilityInfo | None = None
    tags: list[str] | None = None
    photos: list[str] | None = None
    source: POISource = POISource.MANUAL
    external_id: str | None = None


@dataclass
class UpdatePOIRequest:
    """Request to update a POI"""
    name: str | None = None
    description: str | None = None
    category: POICategory | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    opening_hours: OpeningHours | None = None
    price_level: int | None = None
    accessibility: AccessibilityInfo | None = None
    tags: list[str] | None = None
    photos: list[str] | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


@dataclass
class SearchPOIsRequest:
    """Request to search POIs"""
    query: str | None = None
    coordinates: Coordinates | None = None
    radius_meters: float | None = None
    categories: list[POICategory] | None = None
    min_rating: float | None = None
    max_price_level: int | None = None
    accessibility_required: bool | None = None
    open_now: bool | None = None
    has_wifi: bool | None = None
    has_photos: bool | None = None
    verified_only: bool = False
    pagination: PaginationParams | None = None
    sort: SortParams | None = None


class POIUseCases:
    """POI Application Use Cases"""

    def __init__(
        self,
        poi_repository: POIRepository,
        poi_service: POIService,
    ):
        self.poi_repository = poi_repository

    async def create_poi(self, request: CreatePOIRequest) -> POI:
        """Create a new POI"""
        poi = POI(
            name=request.name,
            description=request.description,
            category=request.category,
            coordinates=request.coordinates,
            address=request.address,
            phone=request.phone,
            email=request.email,
            website=request.website,
            opening_hours=request.opening_hours,
            price_level=request.price_level,
            currency=request.currency,
            accessibility=request.accessibility,
            tags=request.tags or [],
            photos=request.photos or [],
            source=request.source,
            external_id=request.external_id,
        )

        return await self.poi_repository.add(poi)

    async def get_poi(self, poi_id: UUID) -> POI | None:
        """Get POI by ID"""
        return await self.poi_repository.get_by_id(poi_id)

    async def update_poi(self, poi_id: UUID, request: UpdatePOIRequest) -> POI | None:
        """Update a POI"""
        poi = await self.poi_repository.get_by_id(poi_id)
        if not poi:
            return None

        # Update fields
        if request.name is not None:
            poi.name = request.name
        if request.description is not None:
            poi.description = request.description
        if request.category is not None:
            poi.category = request.category
        if request.address is not None:
            poi.address = request.address
        if request.phone is not None:
            poi.phone = request.phone
        if request.email is not None:
            poi.email = request.email
        if request.website is not None:
            poi.website = request.website
        if request.opening_hours is not None:
            poi.opening_hours = request.opening_hours
        if request.price_level is not None:
            poi.price_level = request.price_level
        if request.accessibility is not None:
            poi.accessibility = request.accessibility
        if request.tags is not None:
            poi.tags = request.tags
        if request.photos is not None:
            poi.photos = request.photos
        if request.is_active is not None:
            poi.is_active = request.is_active
        if request.is_verified is not None:
            poi.is_verified = request.is_verified

        return await self.poi_repository.update(poi)

    async def delete_poi(self, poi_id: UUID) -> bool:
        """Delete a POI"""
        return await self.poi_repository.delete(poi_id)

    async def search_pois(self, request: SearchPOIsRequest) -> PaginatedResult[POI]:
        """Search POIs with various filters"""
        # Build specification
        specs = []

        if request.verified_only:
            specs.append(VerifiedPOISpec())
        else:
            specs.append(ActivePOISpec())

        if request.categories:
            specs.append(CategoryPOISpec(request.categories))

        if request.coordinates and request.radius_meters:
            specs.append(NearbyPOISpec(request.coordinates, request.radius_meters))

        if request.min_rating:
            specs.append(HighlyRatedPOISpec(request.min_rating))

        if request.max_price_level is not None:
            specs.append(PriceRangePOISpec(0, request.max_price_level))

        if request.accessibility_required:
            specs.append(AccessiblePOISpec())

        if request.open_now:
            specs.append(OpenNowPOISpec())

        if request.has_wifi:
            specs.append(HasWifiPOISpec())

        if request.has_photos:
            specs.append(HasPhotosPOISpec())

        if request.query:
            specs.append(SearchPOISpec(request.query))

        # Combine specifications
        if specs:
            combined_spec = specs[0]
            for spec in specs[1:]:
                combined_spec = combined_spec & spec
        else:
            combined_spec = ActivePOISpec()

        # Use service to find matching POIs
        return await self.poi_service.find_matching_pois(
            spec=combined_spec,
            pagination=request.pagination,
            sort=request.sort,
        )

    async def get_nearby_pois(
        self,
        coordinates: Coordinates,
        radius_meters: float = 1000,
        categories: list[POICategory] | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get POIs near coordinates"""
        return await self.poi_repository.get_nearby(
            coordinates=coordinates,
            radius_meters=radius_meters,
            categories=categories,
            pagination=pagination,
        )

    async def get_popular_pois(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        category: POICategory | None = None,
        limit: int = 20,
    ) -> list[POI]:
        """Get popular POIs"""
        return await self.poi_repository.get_popular(
            coordinates=coordinates,
            radius_meters=radius_meters,
            category=category,
            limit=limit,
        )

    async def get_trending_pois(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        days: int = 7,
        limit: int = 20,
    ) -> list[POI]:
        """Get trending POIs"""
        return await self.poi_repository.get_trending(
            coordinates=coordinates,
            radius_meters=radius_meters,
            days=days,
            limit=limit,
        )

    async def get_poi_recommendations(
        self,
        user_id: UUID,
        coordinates: Coordinates,
        radius_meters: float = 5000,
        limit: int = 10,
    ) -> list[POI]:
        """Get personalized POI recommendations"""
        return await self.poi_service.get_recommendations(
            user_id=user_id,
            coordinates=coordinates,
            radius_meters=radius_meters,
            limit=limit,
        )

    async def increment_visit(self, poi_id: UUID) -> None:
        """Increment POI visit count"""
        await self.poi_repository.increment_visit_count(poi_id)

    async def update_rating(self, poi_id: UUID, rating: float, review_count: int) -> None:
        """Update POI rating"""
        await self.poi_repository.update_rating(poi_id, rating, review_count)

    async def get_poi_stats(self) -> dict[str, Any]:
        """Get POI statistics"""
        return await self.poi_repository.get_stats()

    async def bulk_import_pois(self, pois: list[POI]) -> list[POI]:
        """Bulk import POIs"""
        return await self.poi_repository.bulk_upsert(pois)
