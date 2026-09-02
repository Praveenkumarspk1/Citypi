"""
Itinerary Application Use Cases
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID

from ...domain.entities.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryItem,
    ItineraryStatus,
    ItineraryVisibility,
)
from ...domain.repositories.base import PaginatedResult, PaginationParams, SortParams
from ...domain.repositories.itinerary_repository import ItineraryRepository
from ...domain.services.itinerary_optimization_service import ItineraryOptimizationService
from ...domain.specifications.itinerary_specification import (
    ItineraryActiveSpecification,
    ItineraryCompletedSpecification,
    ItineraryDraftSpecification,
    ItineraryPublicSpecification,
    ItinerarySharedSpecification,
    ItineraryPrivateSpecification,
    ItinerarySharedWithUserSpecification,
    ItineraryOptimizedSpecification,
    ItineraryBudgetSpecification,
    ItineraryUserSpecification,
)
from ...domain.value_objects.coordinates import Coordinates
from ...domain.value_objects.money import Money


@dataclass
class CreateItineraryRequest:
    """Request to create an itinerary"""
    user_id: UUID
    title: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: ItineraryStatus = ItineraryStatus.DRAFT
    visibility: ItineraryVisibility = ItineraryVisibility.PRIVATE
    budget: Money | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    is_ai_generated: bool = False
    ai_prompt: str | None = None


@dataclass
class UpdateItineraryRequest:
    """Request to update an itinerary"""
    title: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: ItineraryStatus | None = None
    visibility: ItineraryVisibility | None = None
    budget: Money | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    shared_with: list[UUID] | None = None


@dataclass
class CreateDayRequest:
    """Request to create an itinerary day"""
    itinerary_id: UUID
    date: date
    title: str | None = None
    notes: str | None = None


@dataclass
class CreateItemRequest:
    """Request to create an itinerary item"""
    day_id: UUID
    poi_id: UUID | None = None
    custom_name: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_minutes: int | None = None
    order: int = 0
    coordinates: Coordinates | None = None
    address: str | None = None
    transport_mode: str | None = None
    transport_details: dict[str, Any] | None = None
    cost: Money | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class OptimizeItineraryRequest:
    """Request to optimize an itinerary"""
    itinerary_id: UUID
    optimization_goals: list[str] | None = None
    constraints: dict[str, Any] | None = None


class ItineraryUseCases:
    """Itinerary Application Use Cases"""

    def __init__(
        self,
        itinerary_repository: ItineraryRepository,
        itinerary_service: ItineraryService,
        optimization_service: ItineraryOptimizationService,
    ):
        self.itinerary_repository = itinerary_repository
        self.optimization_service = optimization_service

    async def create_itinerary(self, request: CreateItineraryRequest) -> Itinerary:
        """Create a new itinerary"""
        itinerary = Itinerary(
            user_id=request.user_id,
            title=request.title,
            description=request.description,
            start_date=request.start_date,
            end_date=request.end_date,
            status=request.status,
            visibility=request.visibility,
            budget=request.budget,
            tags=request.tags or [],
            metadata=request.metadata or {},
            is_ai_generated=request.is_ai_generated,
            ai_prompt=request.ai_prompt,
        )

        return await self.itinerary_repository.add(itinerary)

    async def get_itinerary(self, itinerary_id: UUID) -> Itinerary | None:
        """Get itinerary by ID"""
        return await self.itinerary_repository.get_by_id(itinerary_id)

    async def get_user_itineraries(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
        status: str | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Get itineraries for a user"""
        return await self.itinerary_repository.get_by_user_id(
            user_id=user_id,
            pagination=pagination,
            status=status,
        )

    async def get_public_itineraries(
        self,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Get public itineraries"""
        return await self.itinerary_repository.get_public_itineraries(pagination)

    async def get_shared_itineraries(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Get itineraries shared with user"""
        return await self.itinerary_repository.get_shared_with_user(
            user_id=user_id,
            pagination=pagination,
        )

    async def update_itinerary(
        self,
        itinerary_id: UUID,
        request: UpdateItineraryRequest,
    ) -> Itinerary | None:
        """Update an itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(itinerary_id)
        if not itinerary:
            return None

        if request.title is not None:
            itinerary.title = request.title
        if request.description is not None:
            itinerary.description = request.description
        if request.start_date is not None:
            itinerary.start_date = request.start_date
        if request.end_date is not None:
            itinerary.end_date = request.end_date
        if request.status is not None:
            itinerary.status = request.status
        if request.visibility is not None:
            itinerary.visibility = request.visibility
        if request.budget is not None:
            itinerary.budget = request.budget
        if request.tags is not None:
            itinerary.tags = request.tags
        if request.metadata is not None:
            itinerary.metadata = request.metadata
        if request.shared_with is not None:
            itinerary.shared_with = request.shared_with

        return await self.itinerary_repository.update(itinerary)

    async def delete_itinerary(self, itinerary_id: UUID) -> bool:
        """Delete an itinerary"""
        return await self.itinerary_repository.delete(itinerary_id)

    async def add_day(self, request: CreateDayRequest) -> ItineraryDay:
        """Add a day to an itinerary"""
        day = ItineraryDay(
            itinerary_id=request.itinerary_id,
            date=request.date,
            title=request.title,
            notes=request.notes,
        )

        await self.itinerary_repository.add_day(request.itinerary_id, day)
        return day

    async def update_day(self, day: ItineraryDay) -> None:
        """Update an itinerary day"""
        await self.itinerary_repository.update_day(day)

    async def remove_day(self, itinerary_id: UUID, day_id: UUID) -> None:
        """Remove a day from an itinerary"""
        await self.itinerary_repository.remove_day(itinerary_id, day_id)

    async def add_item(self, request: CreateItemRequest) -> ItineraryItem:
        """Add an item to an itinerary day"""
        item = ItineraryItem(
            day_id=request.day_id,
            poi_id=request.poi_id,
            custom_name=request.custom_name,
            description=request.description,
            start_time=request.start_time,
            end_time=request.end_time,
            duration_minutes=request.duration_minutes,
            order=request.order,
            coordinates=request.coordinates,
            address=request.address,
            transport_mode=request.transport_mode,
            transport_details=request.transport_details or {},
            cost=request.cost,
            notes=request.notes,
            metadata=request.metadata or {},
        )

        await self.itinerary_repository.add_item(request.day_id, item)
        return item

    async def update_item(self, item: ItineraryItem) -> None:
        """Update an itinerary item"""
        await self.itinerary_repository.update_item(item)

    async def remove_item(self, day_id: UUID, item_id: UUID) -> None:
        """Remove an item from an itinerary day"""
        await self.itinerary_repository.remove_item(day_id, item_id)

    async def reorder_items(self, day_id: UUID, item_ids: list[UUID]) -> None:
        """Reorder items in a day"""
        await self.itinerary_repository.reorder_items(day_id, item_ids)

    async def optimize_itinerary(self, request: OptimizeItineraryRequest) -> Itinerary:
        """Optimize an itinerary"""
        itinerary = await self.itinerary_repository.get_by_id(request.itinerary_id)
        if not itinerary:
            raise ValueError("Itinerary not found")

        optimized = await self.optimization_service.optimize(
            itinerary=itinerary,
            goals=request.optimization_goals,
            constraints=request.constraints,
        )

        return await self.itinerary_repository.update(optimized)

    async def generate_itinerary(
        self,
        user_id: UUID,
        title: str,
        start_date: date,
        end_date: date,
        preferences: dict[str, Any],
        coordinates: Coordinates,
        radius_meters: float = 10000,
    ) -> Itinerary:
        """Generate an AI-powered itinerary"""
        itinerary = await self.itinerary_service.generate_itinerary(
            user_id=user_id,
            title=title,
            start_date=start_date,
            end_date=end_date,
            preferences=preferences,
            coordinates=coordinates,
            radius_meters=radius_meters,
        )

        return await self.itinerary_repository.add(itinerary)

    async def duplicate_itinerary(
        self,
        itinerary_id: UUID,
        user_id: UUID,
        new_title: str | None = None,
    ) -> Itinerary:
        """Duplicate an itinerary"""
        original = await self.itinerary_repository.get_by_id(itinerary_id)
        if not original:
            raise ValueError("Itinerary not found")

        duplicated = Itinerary(
            user_id=user_id,
            title=new_title or f"{original.title} (Copy)",
            description=original.description,
            start_date=original.start_date,
            end_date=original.end_date,
            status=ItineraryStatus.DRAFT,
            visibility=ItineraryVisibility.PRIVATE,
            budget=original.budget,
            tags=original.tags.copy(),
            metadata=original.metadata.copy(),
            is_ai_generated=False,
        )

        new_itinerary = await self.itinerary_repository.add(duplicated)

        # Copy days and items
        for day in original.days:
            new_day = ItineraryDay(
                itinerary_id=new_itinerary.id,
                date=day.date,
                title=day.title,
                notes=day.notes,
            )
            await self.itinerary_repository.add_day(new_itinerary.id, new_day)

            for item in day.items:
                new_item = ItineraryItem(
                    day_id=new_day.id,
                    poi_id=item.poi_id,
                    custom_name=item.custom_name,
                    description=item.description,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    duration_minutes=item.duration_minutes,
                    order=item.order,
                    coordinates=item.coordinates,
                    address=item.address,
                    transport_mode=item.transport_mode,
                    transport_details=item.transport_details.copy(),
                    cost=item.cost,
                    notes=item.notes,
                    metadata=item.metadata.copy(),
                )
                await self.itinerary_repository.add_item(new_day.id, new_item)

        return new_itinerary

    async def get_itinerary_stats(self) -> dict[str, Any]:
        """Get itinerary statistics"""
        return await self.itinerary_repository.get_stats()

    async def search_itineraries(
        self,
        user_id: UUID | None = None,
        status: ItineraryStatus | None = None,
        visibility: ItineraryVisibility | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        min_budget: float | None = None,
        max_budget: float | None = None,
        categories: list[str] | None = None,
        ai_generated: bool | None = None,
        shared_with_user: UUID | None = None,
        pagination: PaginationParams | None = None,
        sort: SortParams | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Search itineraries with various filters"""
        specs = []

        if user_id:
            specs.append(UserItinerarySpec(user_id))

        if status:
            specs.append(StatusItinerarySpec(status))

        if visibility == ItineraryVisibility.PUBLIC:
            specs.append(PublicItinerarySpec())

        if start_date and end_date:
            specs.append(DateRangeItinerarySpec(start_date, end_date))

        if min_budget is not None or max_budget is not None:
            specs.append(BudgetItinerarySpec(min_budget or 0, max_budget or float('inf')))

        if categories:
            specs.append(CategoryItinerarySpec(categories))

        if ai_generated is not None and ai_generated:
            specs.append(AIGeneratedItinerarySpec())

        if shared_with_user:
            specs.append(SharedWithUserSpec(shared_with_user))

        # Combine specifications
        if specs:
            combined_spec = specs[0]
            for spec in specs[1:]:
                combined_spec = combined_spec & spec
        else:
            combined_spec = ActiveItinerarySpec()

        return await self.itinerary_service.find_matching_itineraries(
            spec=combined_spec,
            pagination=pagination,
            sort=sort,
        )
