"""
Itinerary Application Service
"""
from datetime import date, datetime
from typing import Any
from uuid import UUID

from ...domain.entities.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryItem,
    ItineraryItemType,
    ItineraryStatus,
    ItineraryVisibility,
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
from ...domain.repositories.itinerary_repository import ItineraryRepository
from ...domain.services.itinerary_optimization_service import ItineraryOptimizationService
from ...domain.specifications.itinerary_specification import (
    ItineraryActiveSpecification,
    ItineraryBudgetSpecification,
    ItineraryDateRangeSpecification,
    ItineraryPublicSpecification,
    ItinerarySharedWithUserSpecification,
    ItineraryUserSpecification,
)
from ...domain.value_objects.coordinates import Coordinates
from ...domain.value_objects.money import Money
from ..ports.cache import CachePort
from ..ports.event_publisher import EventPublisher
from ..ports.external_services import LLMServicePort, EmbeddingServicePort, VectorDBServicePort


class ItineraryService:
    """Application service for itinerary management"""

    def __init__(
        self,
        itinerary_repository: ItineraryRepository,
        optimization_service: ItineraryOptimizationService,
        llm_service: LLMServicePort,
        embedding_service: EmbeddingServicePort,
        vector_db: VectorDBServicePort,
        cache: CachePort,
        event_bus: EventPublisher,
    ):
        self.itinerary_repository = itinerary_repository
        self.optimization_service = optimization_service
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.vector_db = vector_db
        self.cache = cache
        self.event_bus = event_bus

    async def create_itinerary(
        self,
        user_id: UUID,
        title: str,
        description: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        budget_level: str = "moderate",
        pace: str = "moderate",
        interests: list[str] | None = None,
        accessibility_needs: list[str] | None = None,
        dietary_restrictions: list[str] | None = None,
        transport_preferences: list[TransportMode] | None = None,
        base_location: Coordinates | None = None,
        base_address: str | None = None,
        city: str | None = None,
        country: str | None = None,
        tags: list[str] | None = None,
        status: ItineraryStatus = ItineraryStatus.DRAFT,
        visibility: ItineraryVisibility = ItineraryVisibility.PRIVATE,
    ) -> Itinerary:
        """Create a new itinerary"""
        itinerary = Itinerary(
            user_id=user_id,
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            budget_level=budget_level,
            pace=pace,
            interests=interests or [],
            accessibility_needs=accessibility_needs or [],
            dietary_restrictions=dietary_restrictions or [],
            transport_preferences=transport_preferences or [],
            base_location=base_location,
            base_address=base_address,
            city=city,
            country=country,
            tags=tags or [],
            status=status,
            visibility=visibility,
        )

        created_itinerary = await self.itinerary_repository.create(itinerary)

        # Publish domain event
        event = ItineraryCreatedEvent.create(created_itinerary)
        await self.event_bus.publish(event)

        # Cache
        await self.cache.set(f"itinerary:{created_itinerary.id}", created_itinerary)

        return created_itinerary

    async def get_itinerary(self, itinerary_id: UUID, include_days: bool = True) -> Itinerary | None:
        """Get itinerary by ID"""
        # Try cache first
        cached = await self.cache.get(f"itinerary:{itinerary_id}")
        if cached:
            return cached

        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if itinerary:
            await self.cache.set(f"itinerary:{itinerary_id}", itinerary)
        return itinerary

    async def get_user_itineraries(
        self,
        user_id: UUID,
        status: ItineraryStatus | None = None,
        visibility: ItineraryVisibility | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Itinerary], int]:
        """Get itineraries for a user with pagination"""
        spec = ItineraryUserSpecification(user_id)

        if status:
            if status == ItineraryStatus.ACTIVE:
                spec = spec & ItineraryActiveSpecification()

        if visibility:
            if visibility == ItineraryVisibility.PUBLIC:
                spec = spec & ItineraryPublicSpecification()

        return await self.itinerary_repository.find(
            specification=spec,
            page=page,
            page_size=page_size,
        )

    async def get_public_itineraries(
        self,
        page: int = 1,
        page_size: int = 20,
        city: str | None = None,
        country: str | None = None,
        budget_level: str | None = None,
        pace: str | None = None,
    ) -> tuple[list[Itinerary], int]:
        """Get public itineraries"""
        spec = ItineraryPublicSpecification()

        if city:
            spec = spec & ItineraryCitySpecification(city)
        if country:
            spec = spec & ItineraryCountrySpecification(country)
        if budget_level:
            spec = spec & ItineraryBudgetSpecification(budget_level)

        return await self.itinerary_repository.find(
            specification=spec,
            page=page,
            page_size=page_size,
        )

    async def get_shared_itineraries(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Itinerary], int]:
        """Get itineraries shared with user"""
        spec = ItinerarySharedWithUserSpecification(user_id)
        return await self.itinerary_repository.find(
            specification=spec,
            page=page,
            page_size=page_size,
        )

    async def get_itineraries_by_date_range(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Itinerary], int]:
        """Get itineraries within date range"""
        spec = ItineraryUserSpecification(user_id) & ItineraryDateRangeSpecification(start_date, end_date)
        return await self.itinerary_repository.find(
            specification=spec,
            page=page,
            page_size=page_size,
        )

    async def update_itinerary(
        self,
        itinerary_id: UUID,
        title: str | None = None,
        description: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        budget_level: str | None = None,
        pace: str | None = None,
        interests: list[str] | None = None,
        accessibility_needs: list[str] | None = None,
        dietary_restrictions: list[str] | None = None,
        transport_preferences: list[TransportMode] | None = None,
        base_location: Coordinates | None = None,
        base_address: str | None = None,
        city: str | None = None,
        country: str | None = None,
        tags: list[str] | None = None,
        status: ItineraryStatus | None = None,
    ) -> Itinerary | None:
        """Update itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        changes = {}
        fields = {
            "title": title,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "budget_level": budget_level,
            "pace": pace,
            "interests": interests,
            "accessibility_needs": accessibility_needs,
            "dietary_restrictions": dietary_restrictions,
            "transport_preferences": transport_preferences,
            "base_location": base_location,
            "base_address": base_address,
            "city": city,
            "country": country,
            "tags": tags,
            "status": status,
        }

        for field, new_value in fields.items():
            if new_value is not None:
                old_value = getattr(itinerary, field)
                if new_value != old_value:
                    changes[field] = {"old": old_value, "new": new_value}
                    setattr(itinerary, field, new_value)

        if changes:
            itinerary.updated_at = datetime.utcnow()
            updated_itinerary = await self.itinerary_repository.update(itinerary)

            event = ItineraryUpdatedEvent.create(updated_itinerary, changes)
            await self.event_bus.publish(event)

            await self.cache.set(f"itinerary:{itinerary_id}", updated_itinerary)

        return itinerary

    async def delete_itinerary(self, itinerary_id: UUID) -> bool:
        """Delete itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return False

        await self.itinerary_repository.delete(itinerary_id)

        event = ItineraryDeletedEvent.create(itinerary)
        await self.event_bus.publish(event)

        await self.cache.delete(f"itinerary:{itinerary_id}")

        return True

    async def add_day(
        self,
        itinerary_id: UUID,
        day_date: date,
        title: str | None = None,
        notes: str | None = None,
        start_time: Any = None,
        end_time: Any = None,
        base_location: Coordinates | None = None,
        base_address: str | None = None,
    ) -> ItineraryDay | None:
        """Add day to itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        day = itinerary.add_day(
            date=datetime.combine(day_date, datetime.min.time()),
            title=title,
            notes=notes,
            start_time=start_time,
            end_time=end_time,
            base_location=base_location,
            base_address=base_address,
        )

        await self.itinerary_repository.update(itinerary)

        event = ItineraryDayAddedEvent.create(itinerary, day.id, day_date)
        await self.event_bus.publish(event)

        await self.cache.set(f"itinerary:{itinerary_id}", itinerary)

        return day

    async def update_day(
        self,
        itinerary_id: UUID,
        day_id: UUID,
        title: str | None = None,
        notes: str | None = None,
        start_time: Any = None,
        end_time: Any = None,
        base_location: Coordinates | None = None,
        base_address: str | None = None,
    ) -> ItineraryDay | None:
        """Update itinerary day"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        day = next((d for d in itinerary.days if d.id == day_id), None)
        if not day:
            return None

        if title is not None:
            day.title = title
        if notes is not None:
            day.notes = notes
        if start_time is not None:
            day.start_time = start_time
        if end_time is not None:
            day.end_time = end_time
        if base_location is not None:
            day.base_location = base_location
        if base_address is not None:
            day.base_address = base_address

        day._recalculate()
        await self.itinerary_repository.update_day(itinerary_id, day)
        await self.itinerary_repository.update(itinerary)

        await self.cache.set(f"itinerary:{itinerary_id}", itinerary)

        return day

    async def remove_day(self, itinerary_id: UUID, day_id: UUID) -> bool:
        """Remove day from itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return False

        removed = itinerary.remove_day(day_id)
        if not removed:
            return False

        await self.itinerary_repository.update(itinerary)
        await self.cache.set(f"itinerary:{itinerary_id}", itinerary)

        return True

    async def add_item(
        self,
        itinerary_id: UUID,
        day_id: UUID,
        type: ItineraryItemType = ItineraryItemType.POI,
        poi_id: UUID | None = None,
        title: str = "",
        description: str | None = None,
        coordinates: Coordinates | None = None,
        address: str | None = None,
        start_time: Any = None,
        end_time: Any = None,
        duration_minutes: int = 0,
        transport_mode: TransportMode | None = None,
        transit_details: dict[str, Any] | None = None,
        from_location: Coordinates | None = None,
        to_location: Coordinates | None = None,
        estimated_cost: float = 0.0,
        currency: str = "USD",
        notes: str | None = None,
        is_flexible: bool = True,
        is_required: bool = False,
    ) -> ItineraryItem | None:
        """Add item to itinerary day"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        day = next((d for d in itinerary.days if d.id == day_id), None)
        if not day:
            return None

        item = ItineraryItem(
            type=type,
            poi_id=poi_id,
            title=title,
            description=description,
            coordinates=coordinates,
            address=address,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            transport_mode=transport_mode,
            transit_details=transit_details or {},
            from_location=from_location,
            to_location=to_location,
            estimated_cost=estimated_cost,
            currency=currency,
            notes=notes,
            is_flexible=is_flexible,
            is_required=is_required,
        )

        if start_time and end_time:
            item.set_time_range(start_time, end_time)

        day.add_item(item)
        await self.itinerary_repository.update(itinerary)

        event = ItineraryItemAddedEvent.create(itinerary, day_id, item.id, type.value)
        await self.event_bus.publish(event)

        await self.cache.set(f"itinerary:{itinerary_id}", itinerary)

        return item

    async def update_item(
        self,
        itinerary_id: UUID,
        day_id: UUID,
        item_id: UUID,
        **kwargs,
    ) -> ItineraryItem | None:
        """Update itinerary item"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        day = next((d for d in itinerary.days if d.id == day_id), None)
        if not day:
            return None

        item = next((i for i in day.items if i.id == item_id), None)
        if not item:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(item, key):
                setattr(item, key, value)

        if kwargs.get("start_time") and kwargs.get("end_time"):
            item.set_time_range(kwargs["start_time"], kwargs["end_time"])

        item.updated_at = datetime.utcnow()
        day._recalculate()
        await self.itinerary_repository.update(itinerary)
        await self.cache.set(f"itinerary:{itinerary_id}", itinerary)

        return item

    async def remove_item(self, itinerary_id: UUID, day_id: UUID, item_id: UUID) -> bool:
        """Remove item from itinerary day"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return False

        day = next((d for d in itinerary.days if d.id == day_id), None)
        if not day:
            return False

        removed = day.remove_item(item_id)
        if not removed:
            return False

        await self.itinerary_repository.update(itinerary)

        event = ItineraryItemRemovedEvent.create(itinerary, day_id, item_id)
        await self.event_bus.publish(event)

        await self.cache.set(f"itinerary:{itinerary_id}", itinerary)

        return True

    async def reorder_items(self, itinerary_id: UUID, day_id: UUID, item_ids: list[UUID]) -> bool:
        """Reorder items in day"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return False

        day = next((d for d in itinerary.days if d.id == day_id), None)
        if not day:
            return False

        day.reorder_items(item_ids)
        await self.itinerary_repository.update(itinerary)
        await self.cache.set(f"itinerary:{itinerary_id}", itinerary)

        return True

    async def add_collaborator(self, itinerary_id: UUID, user_id: UUID) -> bool:
        """Add collaborator to itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return False

        itinerary.add_collaborator(user_id)
        await self.itinerary_repository.update(itinerary)
        await self.cache.set(f"itinerary:{itinerary_id}", itinerary)

        return True

    async def remove_collaborator(self, itinerary_id: UUID, user_id: UUID) -> bool:
        """Remove collaborator from itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return False

        itinerary.remove_collaborator(user_id)
        await self.itinerary_repository.update(itinerary)
        await self.cache.set(f"itinerary:{itinerary_id}", itinerary)

        return True

    async def publish(self, itinerary_id: UUID, share_token: str) -> Itinerary | None:
        """Publish itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        itinerary.publish(share_token)
        updated_itinerary = await self.itinerary_repository.update(itinerary)

        event = ItinerarySharedEvent.create(updated_itinerary, share_token)
        await self.event_bus.publish(event)

        await self.cache.set(f"itinerary:{itinerary_id}", updated_itinerary)

        return updated_itinerary

    async def unpublish(self, itinerary_id: UUID) -> Itinerary | None:
        """Unpublish itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        itinerary.is_public = False
        itinerary.share_token = None
        updated_itinerary = await self.itinerary_repository.update(itinerary)
        await self.cache.set(f"itinerary:{itinerary_id}", updated_itinerary)

        return updated_itinerary

    async def activate(self, itinerary_id: UUID) -> Itinerary | None:
        """Activate itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        itinerary.activate()
        updated_itinerary = await self.itinerary_repository.update(itinerary)

        event = ItineraryActivatedEvent.create(updated_itinerary)
        await self.event_bus.publish(event)

        await self.cache.set(f"itinerary:{itinerary_id}", updated_itinerary)

        return updated_itinerary

    async def complete(self, itinerary_id: UUID) -> Itinerary | None:
        """Complete itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        itinerary.complete()
        updated_itinerary = await self.itinerary_repository.update(itinerary)

        event = ItineraryCompletedEvent.create(updated_itinerary)
        await self.event_bus.publish(event)

        await self.cache.set(f"itinerary:{itinerary_id}", updated_itinerary)

        return updated_itinerary

    async def cancel(self, itinerary_id: UUID) -> Itinerary | None:
        """Cancel itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        itinerary.cancel()
        updated_itinerary = await self.itinerary_repository.update(itinerary)
        await self.cache.set(f"itinerary:{itinerary_id}", updated_itinerary)

        return updated_itinerary

    async def archive(self, itinerary_id: UUID) -> Itinerary | None:
        """Archive itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        itinerary.archive()
        updated_itinerary = await self.itinerary_repository.update(itinerary)
        await self.cache.set(f"itinerary:{itinerary_id}", updated_itinerary)

        return updated_itinerary

    async def generate_by_ai(
        self,
        user_id: UUID,
        prompt: str,
        model: str,
        tokens: int,
        title: str,
        start_date: date,
        end_date: date,
        budget_level: str = "moderate",
        pace: str = "moderate",
        interests: list[str] | None = None,
        accessibility_needs: list[str] | None = None,
        dietary_restrictions: list[str] | None = None,
        transport_preferences: list[TransportMode] | None = None,
        base_location: Coordinates | None = None,
        base_address: str | None = None,
        city: str | None = None,
        country: str | None = None,
    ) -> Itinerary:
        """Generate itinerary using AI"""
        # Create base itinerary
        itinerary = Itinerary(
            user_id=user_id,
            title=title,
            start_date=start_date,
            end_date=end_date,
            budget_level=budget_level,
            pace=pace,
            interests=interests or [],
            accessibility_needs=accessibility_needs or [],
            dietary_restrictions=dietary_restrictions or [],
            transport_preferences=transport_preferences or [],
            base_location=base_location,
            base_address=base_address,
            city=city,
            country=country,
            generated_by_ai=True,
            generation_prompt=prompt,
            generation_model=model,
            generation_tokens=tokens,
        )

        created_itinerary = await self.itinerary_repository.create(itinerary)

        event = ItineraryGeneratedByAIEvent.create(
            created_itinerary, prompt, model, tokens
        )
        await self.event_bus.publish(event)

        await self.cache.set(f"itinerary:{created_itinerary.id}", created_itinerary)

        return created_itinerary

    async def optimize_itinerary(
        self,
        itinerary_id: UUID,
        optimization_goals: list[str] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> Itinerary | None:
        """Optimize an itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        optimized = await self.optimization_service.optimize(
            itinerary=itinerary,
            goals=optimization_goals,
            constraints=constraints,
        )

        updated = await self.itinerary_repository.update(optimized)
        await self.cache.set(f"itinerary:{itinerary_id}", updated)

        return updated

    async def get_stats(self, user_id: UUID | None = None) -> dict[str, Any]:
        """Get itinerary statistics"""
        return await self.itinerary_repository.get_stats(user_id)

    async def duplicate_itinerary(
        self,
        itinerary_id: UUID,
        user_id: UUID,
        new_title: str | None = None,
    ) -> Itinerary | None:
        """Duplicate an itinerary"""
        original = await self.itinerary_repository.get_by_id(itinerary_id)
        if not original:
            return None

        duplicated = Itinerary(
            user_id=user_id,
            title=new_title or f"{original.title} (Copy)",
            description=original.description,
            start_date=original.start_date,
            end_date=original.end_date,
            status=ItineraryStatus.DRAFT,
            visibility=ItineraryVisibility.PRIVATE,
            budget_level=original.budget_level,
            pace=original.pace,
            interests=original.interests.copy(),
            accessibility_needs=original.accessibility_needs.copy(),
            dietary_restrictions=original.dietary_restrictions.copy(),
            transport_preferences=original.transport_preferences.copy(),
            base_location=original.base_location,
            base_address=original.base_address,
            city=original.city,
            country=original.country,
            tags=original.tags.copy(),
            generated_by_ai=False,
        )

        new_itinerary = await self.itinerary_repository.create(duplicated)

        # Copy days and items
        for day in original.days:
            new_day = ItineraryDay(
                itinerary_id=new_itinerary.id,
                date=day.date,
                title=day.title,
                notes=day.notes,
                start_time=day.start_time,
                end_time=day.end_time,
                base_location=day.base_location,
                base_address=day.base_address,
            )
            await self.itinerary_repository.add_day(new_itinerary.id, new_day)

            for item in day.items:
                new_item = ItineraryItem(
                    day_id=new_day.id,
                    type=item.type,
                    poi_id=item.poi_id,
                    title=item.title,
                    description=item.description,
                    coordinates=item.coordinates,
                    address=item.address,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    duration_minutes=item.duration_minutes,
                    transport_mode=item.transport_mode,
                    transit_details=item.transit_details.copy(),
                    from_location=item.from_location,
                    to_location=item.to_location,
                    estimated_cost=item.estimated_cost,
                    currency=item.currency,
                    notes=item.notes,
                    is_flexible=item.is_flexible,
                    is_required=item.is_required,
                )
                await self.itinerary_repository.add_item(new_day.id, new_item)

        await self.cache.set(f"itinerary:{new_itinerary.id}", new_itinerary)

        return new_itinerary


# Missing specification classes - need to add to specifications
class ItineraryCitySpecification:
    def __init__(self, city: str):
        self.city = city

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.city == self.city

    def __and__(self, other):
        return AndSpecification(self, other)


class ItineraryCountrySpecification:
    def __init__(self, country: str):
        self.country = country

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.country == self.country

    def __and__(self, other):
        return AndSpecification(self, other)


class AndSpecification:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return self.left.is_satisfied_by(itinerary) and self.right.is_satisfied_by(itinerary)

    def __and__(self, other):
        return AndSpecification(self, other)