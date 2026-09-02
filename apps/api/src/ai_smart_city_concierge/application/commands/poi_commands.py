"""
POI Commands (CQRS Write Side)
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ...domain.entities.poi import POI, ContactInfo, OpeningHours, POICategory, POISource
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
from ...domain.value_objects.coordinates import Coordinates
from ..ports.event_publisher import EventPublisher
from ..ports.repositories import POIRepositoryPort


@dataclass
class CreatePOICommand:
    """Command to create a new POI"""
    name: str
    name_local: str | None = None
    description: str | None = None
    category: POICategory = POICategory.OTHER
    subcategory: str | None = None
    tags: list[str] = None
    coordinates: Coordinates = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    neighborhood: str | None = None
    contact: ContactInfo | None = None
    opening_hours: OpeningHours | None = None
    external_id: str | None = None
    source: POISource = POISource.MANUAL

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.coordinates is None:
            self.coordinates = Coordinates(0, 0)


@dataclass
class UpdatePOICommand:
    """Command to update POI"""
    poi_id: UUID
    name: str | None = None
    name_local: str | None = None
    description: str | None = None
    category: POICategory | None = None
    subcategory: str | None = None
    tags: list[str] | None = None
    coordinates: Coordinates | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    neighborhood: str | None = None
    contact: ContactInfo | None = None
    opening_hours: OpeningHours | None = None
    wheelchair_accessible: bool | None = None
    wifi_available: bool | None = None
    outdoor_seating: bool | None = None
    takeaway: bool | None = None
    delivery: bool | None = None
    reservation_required: bool | None = None
    accepts_credit_cards: bool | None = None
    accepts_cash: bool | None = None
    price_level: int | None = None


@dataclass
class AddPOIPhotoCommand:
    """Command to add photo to POI"""
    poi_id: UUID
    photo_url: str
    featured: bool = False


@dataclass
class RemovePOIPhotoCommand:
    """Command to remove photo from POI"""
    poi_id: UUID
    photo_url: str


@dataclass
class UpdatePOIRatingCommand:
    """Command to update POI rating"""
    poi_id: UUID
    rating: float
    review_count: int


@dataclass
class VerifyPOICommand:
    """Command to verify POI"""
    poi_id: UUID
    verified_by: UUID


@dataclass
class IncrementPOIVisitCommand:
    """Command to increment POI visit count"""
    poi_id: UUID


@dataclass
class UpdatePOIPopularityCommand:
    """Command to update POI popularity"""
    poi_id: UUID
    score: float


@dataclass
class SetPOIEmbeddingCommand:
    """Command to set POI embedding reference"""
    poi_id: UUID
    embedding_id: str


@dataclass
class FavoritePOICommand:
    """Command to favorite POI"""
    poi_id: UUID
    user_id: UUID


@dataclass
class UnfavoritePOICommand:
    """Command to unfavorite POI"""
    poi_id: UUID
    user_id: UUID


@dataclass
class DeactivatePOICommand:
    """Command to deactivate POI"""
    poi_id: UUID


@dataclass
class ActivatePOICommand:
    """Command to activate POI"""
    poi_id: UUID


@dataclass
class DeletePOICommand:
    """Command to delete POI"""
    poi_id: UUID


@dataclass
class BulkUpsertPOIsCommand:
    """Command to bulk upsert POIs"""
    pois: list[POI]


class POICommandHandler:
    """Handler for POI commands"""

    def __init__(
        self,
        poi_repository: POIRepositoryPortPort,
        event_publisher: EventPublisher,
    ):
        self.poi_repository = poi_repository
        self.event_publisher = event_publisher

    async def handle_create_poi(self, command: CreatePOICommand) -> POI:
        """Handle create POI command"""
        # Check if POI with same external ID exists
        if command.external_id:
            existing = await self.poi_repository.get_by_external_id(command.external_id, command.source)
            if existing:
                raise ValueError(f"POI with external ID {command.external_id} already exists")

        # Create POI
        poi = POI(
            name=command.name,
            name_local=command.name_local,
            description=command.description,
            category=command.category,
            subcategory=command.subcategory,
            tags=command.tags,
            coordinates=command.coordinates,
            address=command.address,
            city=command.city,
            state=command.state,
            country=command.country,
            postal_code=command.postal_code,
            neighborhood=command.neighborhood,
            contact=command.contact or ContactInfo(),
            opening_hours=command.opening_hours,
            external_id=command.external_id,
            source=command.source,
        )

        # Save
        created_poi = await self.poi_repository.create(poi)

        # Publish event
        event = POICreatedEvent.create(created_poi)
        await self.event_publisher.publish(event)

        return created_poi

    async def handle_update_poi(self, command: UpdatePOICommand) -> POI:
        """Handle update POI command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        # Track changes
        changes = {}
        fields = [
            "name", "name_local", "description", "category", "subcategory", "subcategory",
            "tags", "coordinates", "address", "city", "state", "country",
            "postal_code", "neighborhood", "contact", "opening_hours",
            "wheelchair_accessible", "wifi_available", "outdoor_seating",
            "takeaway", "delivery", "reservation_required", "accepts_credit_cards",
            "accepts_cash", "price_level"
        ]

        for field in fields:
            old_value = getattr(poi, field, None)
            new_value = getattr(command, field, None)
            if new_value is not None and new_value != old_value:
                changes[field] = {"old": old_value, "new": new_value}

        # Update
        poi.update_basic_info(
            name=command.name,
            name_local=command.name_local,
            description=command.description,
            category=command.category,
            subcategory=command.subcategory,
            tags=command.tags,
        )

        if command.coordinates or command.address or command.city or command.state or command.country or command.postal_code or command.neighborhood:
            poi.update_location(
                coordinates=command.coordinates,
                address=command.address,
                city=command.city,
                state=command.state,
                country=command.country,
                postal_code=command.postal_code,
                neighborhood=command.neighborhood,
            )

        if command.contact:
            poi.update_contact(command.contact)

        if command.opening_hours:
            poi.update_hours(command.opening_hours)

        # Update attributes
        attr_fields = [
            "wheelchair_accessible", "wifi_available", "outdoor_seating",
            "takeaway", "delivery", "reservation_required", "accepts_credit_cards",
            "accepts_cash", "price_level"
        ]
        for field in attr_fields:
            value = getattr(command, field)
            if value is not None:
                setattr(poi, field, value)

        poi.updated_at = datetime.utcnow()

        updated_poi = await self.poi_repository.update(poi)

        # Publish event
        if changes:
            event = POIUpdatedEvent.create(updated_poi, changes)
            await self.event_publisher.publish(event)

        return updated_poi

    async def handle_add_photo(self, command: AddPOIPhotoCommand) -> POI:
        """Handle add photo command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        poi.add_photo(command.photo_url, command.featured)
        updated_poi = await self.poi_repository.update(poi)

        # Publish event
        event = POIPhotoAddedEvent.create(updated_poi, command.photo_url, command.featured)
        await self.event_publisher.publish(event)

        return updated_poi

    async def handle_remove_photo(self, command: RemovePOIPhotoCommand) -> POI:
        """Handle remove photo command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        poi.remove_photo(command.photo_url)
        updated_poi = await self.poi_repository.update(poi)

        return updated_poi

    async def handle_update_rating(self, command: UpdatePOIRatingCommand) -> POI:
        """Handle update rating command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        old_rating = poi.rating
        poi.update_rating(command.rating, command.review_count)
        updated_poi = await self.poi_repository.update(poi)

        # Update in repository (optimized)
        await self.poi_repository.update_rating(command.poi_id, command.rating, command.review_count)

        # Publish event
        event = POIRatingUpdatedEvent.create(updated_poi, old_rating, command.rating, command.review_count)
        await self.event_publisher.publish(event)

        return updated_poi

    async def handle_verify(self, command: VerifyPOICommand) -> POI:
        """Handle verify POI command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        poi.verify(command.verified_by)
        updated_poi = await self.poi_repository.update(poi)

        # Publish event
        event = POIVerifiedEvent.create(updated_poi, command.verified_by)
        await self.event_publisher.publish(event)

        return updated_poi

    async def handle_increment_visit(self, command: IncrementPOIVisitCommand) -> POI:
        """Handle increment visit command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        poi.increment_visit()
        updated_poi = await self.poi_repository.update(poi)

        # Update in repository (optimized)
        await self.poi_repository.increment_visit_count(command.poi_id)

        return updated_poi

    async def handle_update_popularity(self, command: UpdatePOIPopularityCommand) -> POI:
        """Handle update popularity command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        poi.update_popularity(command.score)
        updated_poi = await self.poi_repository.update(poi)

        # Update in repository (optimized)
        await self.poi_repository.update_popularity(command.poi_id, command.score)

        return updated_poi

    async def handle_set_embedding(self, command: SetPOIEmbeddingCommand) -> POI:
        """Handle set embedding command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        poi.set_embedding_id(command.embedding_id)
        updated_poi = await self.poi_repository.update(poi)

        # Update in repository (optimized)
        await self.poi_repository.set_embedding_id(command.poi_id, command.embedding_id)

        return updated_poi

    async def handle_favorite(self, command: FavoritePOICommand) -> None:
        """Handle favorite POI command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        # Publish event
        event = POIFavoritedEvent.create(poi, command.user_id)
        await self.event_publisher.publish(event)

    async def handle_unfavorite(self, command: UnfavoritePOICommand) -> None:
        """Handle unfavorite POI command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        # Publish event
        event = POIUnfavoritedEvent.create(poi, command.user_id)
        await self.event_publisher.publish(event)

    async def handle_deactivate(self, command: DeactivatePOICommand) -> POI:
        """Handle deactivate POI command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        poi.deactivate()
        updated_poi = await self.poi_repository.update(poi)

        return updated_poi

    async def handle_activate(self, command: ActivatePOICommand) -> POI:
        """Handle activate POI command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        poi.activate()
        updated_poi = await self.poi_repository.update(poi)

        return updated_poi

    async def handle_delete(self, command: DeletePOICommand) -> bool:
        """Handle delete POI command"""
        poi = await self.poi_repository.get_by_id(command.poi_id)
        if not poi:
            raise ValueError(f"POI {command.poi_id} not found")

        await self.poi_repository.delete(command.poi_id)

        # Publish event
        event = POIDeletedEvent.create(poi)
        await self.event_publisher.publish(event)

        return True

    async def handle_bulk_upsert(self, command: BulkUpsertPOIsCommand) -> list[POI]:
        """Handle bulk upsert POIs command"""
        return await self.poi_repository.bulk_upsert(command.pois)
