"""
Itinerary Commands (CQRS Write Side)
"""
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from ...domain.entities.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryItem,
    ItineraryItemType,
    ItineraryStatus,
    TransportMode,
)
from ...domain.events.domain_events import (
    ItineraryActivatedEvent,
    ItineraryCompletedEvent,
    ItineraryCreatedEvent,
    ItineraryDayAddedEvent,
    ItineraryDeletedEvent,
    ItineraryGeneratedByAIEvent,
    ItineraryItemAddedEvent,
    ItineraryItemRemovedEvent,
    ItinerarySharedEvent,
    ItineraryUpdatedEvent,
)
from ...domain.value_objects.coordinates import Coordinates
from ..ports.event_publisher import EventPublisher
from ..ports.repositories import ItineraryRepositoryPort


@dataclass
class CreateItineraryCommand:
    """Command to create a new itinerary"""
    user_id: UUID
    title: str
    description: str | None = None
    start_date: date = None
    end_date: date = None
    budget_level: str = "moderate"
    pace: str = "moderate"
    interests: list[str] = None
    accessibility_needs: list[str] = None
    dietary_restrictions: list[str] = None
    transport_preferences: list[TransportMode] = None
    base_location: Coordinates | None = None
    base_address: str | None = None
    city: str | None = None
    country: str | None = None
    tags: list[str] = None

    def __post_init__(self):
        if self.start_date is None:
            self.start_date = date.today()
        if self.end_date is None:
            self.end_date = self.start_date
        if self.interests is None:
            self.interests = []
        if self.accessibility_needs is None:
            self.accessibility_needs = []
        if self.dietary_restrictions is None:
            self.dietary_restrictions = []
        if self.transport_preferences is None:
            self.transport_preferences = []
        if self.tags is None:
            self.tags = []


@dataclass
class UpdateItineraryCommand:
    """Command to update itinerary"""
    itinerary_id: UUID
    title: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_level: str | None = None
    pace: str | None = None
    interests: list[str] | None = None
    accessibility_needs: list[str] | None = None
    dietary_restrictions: list[str] | None = None
    transport_preferences: list[TransportMode] | None = None
    base_location: Coordinates | None = None
    base_address: str | None = None
    city: str | None = None
    country: str | None = None
    tags: list[str] | None = None
    status: ItineraryStatus | None = None


@dataclass
class AddItineraryDayCommand:
    """Command to add day to itinerary"""
    itinerary_id: UUID
    day_date: date
    title: str | None = None
    notes: str | None = None
    start_time: time = time(9, 0)
    end_time: time = time(22, 0)
    base_location: Coordinates | None = None
    base_address: str | None = None


@dataclass
class UpdateItineraryDayCommand:
    """Command to update itinerary day"""
    itinerary_id: UUID
    day_id: UUID
    title: str | None = None
    notes: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    base_location: Coordinates | None = None
    base_address: str | None = None


@dataclass
class RemoveItineraryDayCommand:
    """Command to remove day from itinerary"""
    itinerary_id: UUID
    day_id: UUID


@dataclass
class AddItineraryItemCommand:
    """Command to add item to itinerary day"""
    itinerary_id: UUID
    day_id: UUID
    type: ItineraryItemType = ItineraryItemType.POI
    poi_id: UUID | None = None
    title: str = ""
    description: str | None = None
    coordinates: Coordinates | None = None
    address: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int = 0
    transport_mode: TransportMode | None = None
    transit_details: dict[str, Any] = None
    from_location: Coordinates | None = None
    to_location: Coordinates | None = None
    estimated_cost: float = 0.0
    currency: str = "USD"
    notes: str | None = None
    is_flexible: bool = True
    is_required: bool = False

    def __post_init__(self):
        if self.transit_details is None:
            self.transit_details = {}


@dataclass
class UpdateItineraryItemCommand:
    """Command to update itinerary item"""
    itinerary_id: UUID
    day_id: UUID
    item_id: UUID
    type: ItineraryItemType | None = None
    poi_id: UUID | None = None
    title: str | None = None
    description: str | None = None
    coordinates: Coordinates | None = None
    address: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_minutes: int | None = None
    transport_mode: TransportMode | None = None
    transit_details: dict[str, Any] | None = None
    from_location: Coordinates | None = None
    to_location: Coordinates | None = None
    estimated_cost: float | None = None
    currency: str | None = None
    notes: str | None = None
    is_flexible: bool | None = None
    is_required: bool | None = None


@dataclass
class RemoveItineraryItemCommand:
    """Command to remove item from itinerary day"""
    itinerary_id: UUID
    day_id: UUID
    item_id: UUID


@dataclass
class ReorderItineraryItemsCommand:
    """Command to reorder items in day"""
    itinerary_id: UUID
    day_id: UUID
    item_ids: list[UUID]


@dataclass
class ReorderItineraryDaysCommand:
    """Command to reorder days in itinerary"""
    itinerary_id: UUID
    day_ids: list[UUID]


@dataclass
class AddCollaboratorCommand:
    """Command to add collaborator to itinerary"""
    itinerary_id: UUID
    user_id: UUID


@dataclass
class RemoveCollaboratorCommand:
    """Command to remove collaborator from itinerary"""
    itinerary_id: UUID
    user_id: UUID


@dataclass
class PublishItineraryCommand:
    """Command to publish itinerary"""
    itinerary_id: UUID
    share_token: str


@dataclass
class UnpublishItineraryCommand:
    """Command to unpublish itinerary"""
    itinerary_id: UUID


@dataclass
class ActivateItineraryCommand:
    """Command to activate itinerary"""
    itinerary_id: UUID


@dataclass
class CompleteItineraryCommand:
    """Command to complete itinerary"""
    itinerary_id: UUID


@dataclass
class CancelItineraryCommand:
    """Command to cancel itinerary"""
    itinerary_id: UUID


@dataclass
class ArchiveItineraryCommand:
    """Command to archive itinerary"""
    itinerary_id: UUID


@dataclass
class DeleteItineraryCommand:
    """Command to delete itinerary"""
    itinerary_id: UUID


@dataclass
class GenerateItineraryByAICommand:
    """Command to generate itinerary using AI"""
    user_id: UUID
    prompt: str
    model: str
    tokens: int
    title: str
    start_date: date
    end_date: date
    budget_level: str = "moderate"
    pace: str = "moderate"
    interests: list[str] = None
    accessibility_needs: list[str] = None
    dietary_restrictions: list[str] = None
    transport_preferences: list[TransportMode] = None
    base_location: Coordinates | None = None
    base_address: str | None = None
    city: str | None = None
    country: str | None = None

    def __post_init__(self):
        if self.interests is None:
            self.interests = []
        if self.accessibility_needs is None:
            self.accessibility_needs = []
        if self.dietary_restrictions is None:
            self.dietary_restrictions = []
        if self.transport_preferences is None:
            self.transport_preferences = []


class ItineraryCommandHandler:
    """Handler for itinerary commands"""

    def __init__(
        self,
        itinerary_repository: ItineraryRepositoryPortPort,
        event_publisher: EventPublisher,
    ):
        self.itinerary_repository = itinerary_repository
        self.event_publisher = event_publisher

    async def handle_create_itinerary(self, command: CreateItineraryCommand) -> Itinerary:
        """Handle create itinerary command"""
        itinerary = Itinerary(
            user_id=command.user_id,
            title=command.title,
            description=command.description,
            start_date=datetime.combine(command.start_date, time.min),
            end_date=datetime.combine(command.end_date, time.min),
            budget_level=command.budget_level,
            pace=command.pace,
            interests=command.interests,
            accessibility_needs=command.accessibility_needs,
            dietary_restrictions=command.dietary_restrictions,
            transport_preferences=command.transport_preferences,
            base_location=command.base_location,
            base_address=command.base_address,
            city=command.city,
            country=command.country,
            tags=command.tags,
        )

        created_itinerary = await self.itinerary_repository.create(itinerary)

        # Publish event
        event = ItineraryCreatedEvent.create(created_itinerary)
        await self.event_publisher.publish(event)

        return created_itinerary

    async def handle_update_itinerary(self, command: UpdateItineraryCommand) -> Itinerary:
        """Handle update itinerary command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        # Track changes
        changes = {}
        fields = [
            "title", "description", "start_date", "end_date", "budget_level",
            "pace", "interests", "accessibility_needs", "dietary_restrictions",
            "transport_preferences", "base_location", "base_address", "city",
            "country", "tags", "status"
        ]

        for field in fields:
            old_value = getattr(itinerary, field, None)
            new_value = getattr(command, field, None)
            if new_value is not None and new_value != old_value:
                changes[field] = {"old": old_value, "new": new_value}

        # Update
        if command.title is not None:
            itinerary.title = command.title
        if command.description is not None:
            itinerary.description = command.description
        if command.start_date is not None:
            itinerary.start_date = datetime.combine(command.start_date, time.min)
        if command.end_date is not None:
            itinerary.end_date = datetime.combine(command.end_date, time.min)
        if command.budget_level is not None:
            itinerary.budget_level = command.budget_level
        if command.pace is not None:
            itinerary.pace = command.pace
        if command.interests is not None:
            itinerary.interests = command.interests
        if command.accessibility_needs is not None:
            itinerary.accessibility_needs = command.accessibility_needs
        if command.dietary_restrictions is not None:
            itinerary.dietary_restrictions = command.dietary_restrictions
        if command.transport_preferences is not None:
            itinerary.transport_preferences = command.transport_preferences
        if command.base_location is not None:
            itinerary.base_location = command.base_location
        if command.base_address is not None:
            itinerary.base_address = command.base_address
        if command.city is not None:
            itinerary.city = command.city
        if command.country is not None:
            itinerary.country = command.country
        if command.tags is not None:
            itinerary.tags = command.tags
        if command.status is not None:
            itinerary.status = command.status

        itinerary.updated_at = datetime.utcnow()

        updated_itinerary = await self.itinerary_repository.update(itinerary)

        # Publish event
        if changes:
            event = ItineraryUpdatedEvent.create(updated_itinerary, changes)
            await self.event_publisher.publish(event)

        return updated_itinerary

    async def handle_add_day(self, command: AddItineraryDayCommand) -> ItineraryDay:
        """Handle add day command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        day = itinerary.add_day(
            date=datetime.combine(command.day_date, time.min),
            title=command.title,
            notes=command.notes,
            start_time=command.start_time,
            end_time=command.end_time,
            base_location=command.base_location,
            base_address=command.base_address,
        )

        await self.itinerary_repository.update(itinerary)

        # Publish event
        event = ItineraryDayAddedEvent.create(itinerary, day.id, command.day_date)
        await self.event_publisher.publish(event)

        return day

    async def handle_update_day(self, command: UpdateItineraryDayCommand) -> ItineraryDay:
        """Handle update day command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        day = next((d for d in itinerary.days if d.id == command.day_id), None)
        if not day:
            raise ValueError(f"Day {command.day_id} not found")

        if command.title is not None:
            day.title = command.title
        if command.notes is not None:
            day.notes = command.notes
        if command.start_time is not None:
            day.start_time = command.start_time
        if command.end_time is not None:
            day.end_time = command.end_time
        if command.base_location is not None:
            day.base_location = command.base_location
        if command.base_address is not None:
            day.base_address = command.base_address

        day._recalculate()
        await self.itinerary_repository.update_day(command.itinerary_id, day)

        return day

    async def handle_remove_day(self, command: RemoveItineraryDayCommand) -> bool:
        """Handle remove day command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        removed = itinerary.remove_day(command.day_id)
        if not removed:
            raise ValueError(f"Day {command.day_id} not found")

        await self.itinerary_repository.update(itinerary)
        return True

    async def handle_add_item(self, command: AddItineraryItemCommand) -> ItineraryItem:
        """Handle add item command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        day = itinerary.get_day(datetime.combine(command.day_id, time.min))  # This won't work, need day by ID
        # Actually we need to find day by ID
        day = next((d for d in itinerary.days if d.id == command.day_id), None)
        if not day:
            raise ValueError(f"Day {command.day_id} not found")

        item = ItineraryItem(
            type=command.type,
            poi_id=command.poi_id,
            title=command.title,
            description=command.description,
            coordinates=command.coordinates,
            address=command.address,
            start_time=command.start_time,
            end_time=command.end_time,
            duration_minutes=command.duration_minutes,
            transport_mode=command.transport_mode,
            transit_details=command.transit_details,
            from_location=command.from_location,
            to_location=command.to_location,
            estimated_cost=command.estimated_cost,
            currency=command.currency,
            notes=command.notes,
            is_flexible=command.is_flexible,
            is_required=command.is_required,
        )

        if command.start_time and command.end_time:
            item.set_time_range(command.start_time, command.end_time)

        day.add_item(item)
        await self.itinerary_repository.update(itinerary)

        # Publish event
        event = ItineraryItemAddedEvent.create(itinerary, command.day_id, item.id, command.type.value)
        await self.event_publisher.publish(event)

        return item

    async def handle_update_item(self, command: UpdateItineraryItemCommand) -> ItineraryItem:
        """Handle update item command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        day = next((d for d in itinerary.days if d.id == command.day_id), None)
        if not day:
            raise ValueError(f"Day {command.day_id} not found")

        item = next((i for i in day.items if i.id == command.item_id), None)
        if not item:
            raise ValueError(f"Item {command.item_id} not found")

        # Update fields
        if command.type is not None:
            item.type = command.type
        if command.poi_id is not None:
            item.poi_id = command.poi_id
        if command.title is not None:
            item.title = command.title
        if command.description is not None:
            item.description = command.description
        if command.coordinates is not None:
            item.coordinates = command.coordinates
        if command.address is not None:
            item.address = command.address
        if command.start_time is not None:
            item.start_time = command.start_time
        if command.end_time is not None:
            item.end_time = command.end_time
        if command.duration_minutes is not None:
            item.duration_minutes = command.duration_minutes
        if command.transport_mode is not None:
            item.transport_mode = command.transport_mode
        if command.transit_details is not None:
            item.transit_details = command.transit_details
        if command.from_location is not None:
            item.from_location = command.from_location
        if command.to_location is not None:
            item.to_location = command.to_location
        if command.estimated_cost is not None:
            item.estimated_cost = command.estimated_cost
        if command.currency is not None:
            item.currency = command.currency
        if command.notes is not None:
            item.notes = command.notes
        if command.is_flexible is not None:
            item.is_flexible = command.is_flexible
        if command.is_required is not None:
            item.is_required = command.is_required

        if command.start_time and command.end_time:
            item.set_time_range(command.start_time, command.end_time)

        item.updated_at = datetime.utcnow()
        day._recalculate()
        await self.itinerary_repository.update(itinerary)

        return item

    async def handle_remove_item(self, command: RemoveItineraryItemCommand) -> bool:
        """Handle remove item command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        day = next((d for d in itinerary.days if d.id == command.day_id), None)
        if not day:
            raise ValueError(f"Day {command.day_id} not found")

        removed = day.remove_item(command.item_id)
        if not removed:
            raise ValueError(f"Item {command.item_id} not found")

        await self.itinerary_repository.update(itinerary)

        # Publish event
        event = ItineraryItemRemovedEvent.create(itinerary, command.day_id, command.item_id)
        await self.event_publisher.publish(event)

        return True

    async def handle_reorder_items(self, command: ReorderItineraryItemsCommand) -> None:
        """Handle reorder items command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        day = next((d for d in itinerary.days if d.id == command.day_id), None)
        if not day:
            raise ValueError(f"Day {command.day_id} not found")

        day.reorder_items(command.item_ids)
        await self.itinerary_repository.update(itinerary)

    async def handle_reorder_days(self, command: ReorderItineraryDaysCommand) -> None:
        """Handle reorder days command"""
        # This would require updating day sequences
        pass

    async def handle_add_collaborator(self, command: AddCollaboratorCommand) -> None:
        """Handle add collaborator command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        itinerary.add_collaborator(command.user_id)
        await self.itinerary_repository.update(itinerary)

    async def handle_remove_collaborator(self, command: RemoveCollaboratorCommand) -> None:
        """Handle remove collaborator command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        itinerary.remove_collaborator(command.user_id)
        await self.itinerary_repository.update(itinerary)

    async def handle_publish(self, command: PublishItineraryCommand) -> Itinerary:
        """Handle publish itinerary command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        itinerary.publish(command.share_token)
        updated_itinerary = await self.itinerary_repository.update(itinerary)

        # Publish event
        event = ItinerarySharedEvent.create(updated_itinerary, command.share_token)
        await self.event_publisher.publish(event)

        return updated_itinerary

    async def handle_unpublish(self, command: UnpublishItineraryCommand) -> Itinerary:
        """Handle unpublish itinerary command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        itinerary.is_public = False
        itinerary.share_token = None
        updated_itinerary = await self.itinerary_repository.update(itinerary)

        return updated_itinerary

    async def handle_activate(self, command: ActivateItineraryCommand) -> Itinerary:
        """Handle activate itinerary command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        itinerary.activate()
        updated_itinerary = await self.itinerary_repository.update(itinerary)

        # Publish event
        event = ItineraryActivatedEvent.create(updated_itinerary)
        await self.event_publisher.publish(event)

        return updated_itinerary

    async def handle_complete(self, command: CompleteItineraryCommand) -> Itinerary:
        """Handle complete itinerary command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        itinerary.complete()
        updated_itinerary = await self.itinerary_repository.update(itinerary)

        # Publish event
        event = ItineraryCompletedEvent.create(updated_itinerary)
        await self.event_publisher.publish(event)

        return updated_itinerary

    async def handle_cancel(self, command: CancelItineraryCommand) -> Itinerary:
        """Handle cancel itinerary command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        itinerary.cancel()
        updated_itinerary = await self.itinerary_repository.update(itinerary)

        return updated_itinerary

    async def handle_archive(self, command: ArchiveItineraryCommand) -> Itinerary:
        """Handle archive itinerary command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        itinerary.archive()
        updated_itinerary = await self.itinerary_repository.update(itinerary)

        return updated_itinerary

    async def handle_delete(self, command: DeleteItineraryCommand) -> bool:
        """Handle delete itinerary command"""
        itinerary = await self.itinerary_repository.get_by_id(command.itinerary_id)
        if not itinerary:
            raise ValueError(f"Itinerary {command.itinerary_id} not found")

        await self.itinerary_repository.delete(command.itinerary_id)

        # Publish event
        event = ItineraryDeletedEvent.create(itinerary)
        await self.event_publisher.publish(event)

        return True

    async def handle_generate_by_ai(self, command: GenerateItineraryByAICommand) -> Itinerary:
        """Handle generate itinerary by AI command"""
        # Create base itinerary
        itinerary = Itinerary(
            user_id=command.user_id,
            title=command.title,
            start_date=datetime.combine(command.start_date, time.min),
            end_date=datetime.combine(command.end_date, time.min),
            budget_level=command.budget_level,
            pace=command.pace,
            interests=command.interests,
            accessibility_needs=command.accessibility_needs,
            dietary_restrictions=command.dietary_restrictions,
            transport_preferences=command.transport_preferences,
            base_location=command.base_location,
            base_address=command.base_address,
            city=command.city,
            country=command.country,
            generated_by_ai=True,
            generation_prompt=command.prompt,
            generation_model=command.model,
            generation_tokens=command.tokens,
        )

        created_itinerary = await self.itinerary_repository.create(itinerary)

        # Publish event
        event = ItineraryGeneratedByAIEvent.create(
            created_itinerary, command.prompt, command.model, command.tokens
        )
        await self.event_publisher.publish(event)

        return created_itinerary
