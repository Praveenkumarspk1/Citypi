"""
POI Application Service
"""
from typing import Any
from uuid import UUID

from ...domain.entities.poi import POI, POICategory, POISource
from ...domain.events.domain_events import (
    POICreatedEvent,
    POIDeletedEvent,
    POIFavoritedEvent,
    POIPhotoAddedEvent,
    POIRatingUpdatedEvent,
    POIUnfavoritedEvent,
    POIUpdatedEvent,
    POIVerifiedEvent,
)
from ...domain.repositories.poi_repository import POIRepository
from ...domain.services.poi_service import POIService as DomainPOIService
from ...domain.specifications.poi_specification import (
    POIActiveSpecification,
    POICategorySpecification,
    POICoordinatesSpecification,
    POINameSpecification,
    POIVerifiedSpecification,
)
from ...domain.value_objects.coordinates import Coordinates
from ..ports.cache import CachePort
from ..ports.event_publisher import EventPublisher
from ..ports.external_services import EmbeddingServicePort, VectorDBServicePort


class POIApplicationService:
    """Application service for POI management"""

    def __init__(
        self,
        poi_repository: POIRepository,
        poi_service: DomainPOIService,
        embedding_service: EmbeddingServicePort,
        vector_db: VectorDBServicePort,
        cache: CachePort,
        event_bus: EventPublisher,
    ):
        self.poi_repository = poi_repository
        self.poi_service = poi_service
        self.embedding_service = embedding_service
        self.vector_db = vector_db
        self.cache = cache
        self.event_bus = event_bus

    async def create_poi(
        self,
        name: str,
        name_local: str | None = None,
        description: str | None = None,
        category: POICategory = POICategory.OTHER,
        subcategory: str | None = None,
        tags: list[str] | None = None,
        coordinates: Coordinates | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        postal_code: str | None = None,
        neighborhood: str | None = None,
        contact: Any | None = None,
        opening_hours: Any | None = None,
        external_id: str | None = None,
        source: POISource = POISource.MANUAL,
    ) -> POI:
        """Create a new POI"""
        # Check if POI with same external ID exists
        if external_id:
            existing = await self.poi_repository.get_by_external_id(external_id, source)
            if existing:
                raise ValueError(f"POI with external ID {external_id} already exists")

        poi = POI(
            name=name,
            name_local=name_local,
            description=description,
            category=category,
            subcategory=subcategory,
            tags=tags or [],
            coordinates=coordinates or Coordinates(0, 0),
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            neighborhood=neighborhood,
            contact=contact,
            opening_hours=opening_hours,
            external_id=external_id,
            source=source,
        )

        created_poi = await self.poi_repository.create(poi)

        # Generate embedding for the POI
        try:
            embedding_text = f"{poi.name} {poi.description or ''} {poi.category.value} {' '.join(poi.tags)}"
            embedding = await self.embedding_service.generate_embedding(embedding_text)
            await self.vector_db.upsert(
                collection="poi_embeddings",
                id=str(created_poi.id),
                vector=embedding,
                metadata={
                    "poi_id": str(created_poi.id),
                    "name": created_poi.name,
                    "category": created_poi.category.value,
                    "city": created_poi.city,
                    "country": created_poi.country,
                },
            )
            created_poi.set_embedding_id(str(created_poi.id))
        except Exception:
            pass  # Embedding generation is optional

        # Publish domain event
        event = POICreatedEvent.create(created_poi)
        await self.event_bus.publish(event)

        await self.cache.set(f"poi:{created_poi.id}", created_poi)

        return created_poi

    async def get_poi(self, poi_id: UUID, include_embedding: bool = False) -> POI | None:
        """Get POI by ID"""
        cached = await self.cache.get(f"poi:{poi_id}")
        if cached:
            return cached

        poi = await self.poi_repository.get_by_id(poi_id)
        if poi:
            await self.cache.set(f"poi:{poi_id}", poi)
        return poi

    async def get_poi_by_external_id(self, external_id: str, source: POISource) -> POI | None:
        """Get POI by external ID"""
        return await self.poi_repository.get_by_external_id(external_id, source)

    async def list_pois(
        self,
        category: POICategory | None = None,
        source: POISource | None = None,
        verified_only: bool = False,
        active_only: bool = True,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "popularity_score",
        sort_order: str = "desc",
    ) -> tuple[list[POI], int]:
        """List POIs with pagination and filters"""
        spec = POIActiveSpecification() if active_only else None

        if verified_only:
            verified_spec = POIVerifiedSpecification()
            spec = spec & verified_spec if spec else verified_spec

        if category:
            cat_spec = POICategorySpecification(category)
            spec = spec & cat_spec if spec else cat_spec

        return await self.poi_repository.find(
            specification=spec,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def search_pois(
        self,
        query: str,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        categories: list[POICategory] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[POI], int]:
        """Search POIs using hybrid search (vector + keyword)"""
        # Use vector search if coordinates and radius provided
        if coordinates and radius_meters:
            embedding = await self.embedding_service.generate_embedding(query)
            results = await self.vector_db.search(
                collection="poi_embeddings",
                query_vector=embedding,
                limit=page_size * 3,  # Get more for filtering
                filter_metadata={
                    "city": coordinates.city if hasattr(coordinates, 'city') else None,
                } if hasattr(coordinates, 'city') else None,
            )

            poi_ids = [UUID(r.id) for r in results]
            pois = await self.poi_repository.get_by_ids(poi_ids)

            # Filter by category if specified
            if categories:
                pois = [p for p in pois if p.category in categories]

            # Filter by radius
            if radius_meters and coordinates:
                pois = [p for p in pois if p.coordinates.distance_to(coordinates) <= radius_meters]

            return pois[:page_size], len(pois)

        # Fallback to keyword search
        return await self.poi_repository.search(
            query=query,
            coordinates=coordinates,
            radius_meters=radius_meters,
            categories=categories,
            page=page,
            page_size=page_size,
        )

    async def get_nearby_pois(
        self,
        coordinates: Coordinates,
        radius_meters: float = 1000,
        categories: list[POICategory] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[POI], int]:
        """Get nearby POIs"""
        spec = POIActiveSpecification() & POICoordinatesSpecification(coordinates, radius_meters)

        if categories:
            for cat in categories:
                spec = spec & POICategorySpecification(cat)

        return await self.poi_repository.find(
            specification=spec,
            page=page,
            page_size=page_size,
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

    async def update_poi(
        self,
        poi_id: UUID,
        **kwargs,
    ) -> POI | None:
        """Update POI"""
        poi = await self.poi_repository.get_by_id(poi_id)
        if not poi:
            return None

        changes = {}
        for key, new_value in kwargs.items():
            if new_value is not None and hasattr(poi, key):
                old_value = getattr(poi, key)
                if new_value != old_value:
                    changes[key] = {"old": old_value, "new": new_value}
                    setattr(poi, key, new_value)

        if changes:
            poi.updated_at = datetime.utcnow()
            updated_poi = await self.poi_repository.update(poi)

            event = POIUpdatedEvent.create(updated_poi, changes)
            await self.event_bus.publish(event)

            await self.cache.set(f"poi:{poi_id}", updated_poi)

        return poi

    async def add_photo(self, poi_id: UUID, photo_url: str, featured: bool = False) -> POI | None:
        """Add photo to POI"""
        poi = await self.poi_repository.get_by_id(poi_id)
        if not poi:
            return None

        poi.add_photo(photo_url, featured)
        updated_poi = await self.poi_repository.update(poi)

        event = POIPhotoAddedEvent.create(updated_poi, photo_url, featured)
        await self.event_bus.publish(event)

        await self.cache.set(f"poi:{poi_id}", updated_poi)

        return updated_poi

    async def update_rating(self, poi_id: UUID, rating: float, review_count: int) -> POI | None:
        """Update POI rating"""
        poi = await self.poi_repository.get_by_id(poi_id)
        if not poi:
            return None

        old_rating = poi.rating
        poi.update_rating(rating, review_count)
        updated_poi = await self.poi_repository.update(poi)

        # Optimized update
        await self.poi_repository.update_rating(poi_id, rating, review_count)

        event = POIRatingUpdatedEvent.create(updated_poi, old_rating, rating, review_count)
        await self.event_bus.publish(event)

        await self.cache.set(f"poi:{poi_id}", updated_poi)

        return updated_poi

    async def verify_poi(self, poi_id: UUID, verified_by: UUID) -> POI | None:
        """Verify POI"""
        poi = await self.poi_repository.get_by_id(poi_id)
        if not poi:
            return None

        poi.verify(verified_by)
        updated_poi = await self.poi_repository.update(poi)

        event = POIVerifiedEvent.create(updated_poi, verified_by)
        await self.event_bus.publish(event)

        await self.cache.set(f"poi:{poi_id}", updated_poi)

        return updated_poi

    async def increment_visit(self, poi_id: UUID) -> POI | None:
        """Increment POI visit count"""
        poi = await self.poi_repository.get_by_id(poi_id)
        if not poi:
            return None

        poi.increment_visit()
        updated_poi = await self.poi_repository.update(poi)

        # Optimized update
        await self.poi_repository.increment_visit_count(poi_id)

        await self.cache.set(f"poi:{poi_id}", updated_poi)

        return updated_poi

    async def favorite_poi(self, poi_id: UUID, user_id: UUID) -> bool:
        """Favorite POI"""
        poi = await self.poi_repository.get_by_id(poi_id)
        if not poi:
            return False

        event = POIFavoritedEvent.create(poi, user_id)
        await self.event_bus.publish(event)

        return True

    async def unfavorite_poi(self, poi_id: UUID, user_id: UUID) -> bool:
        """Unfavorite POI"""
        poi = await self.poi_repository.get_by_id(poi_id)
        if not poi:
            return False

        event = POIUnfavoritedEvent.create(poi, user_id)
        await self.event_bus.publish(event)

        return True

    async def delete_poi(self, poi_id: UUID) -> bool:
        """Delete POI"""
        poi = await self.poi_repository.get_by_id(poi_id)
        if not poi:
            return False

        await self.poi_repository.delete(poi_id)

        event = POIDeletedEvent.create(poi)
        await self.event_bus.publish(event)

        await self.cache.delete(f"poi:{poi_id}")

        return True

    async def bulk_upsert(self, pois: list[POI]) -> list[POI]:
        """Bulk upsert POIs"""
        return await self.poi_repository.bulk_upsert(pois)

    async def get_stats(self) -> dict[str, Any]:
        """Get POI statistics"""
        return await self.poi_repository.get_stats()