"""
Itinerary Aggregate
"""
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from ..entities.itinerary import ItemType, Itinerary, ItineraryDay, ItineraryItem, ItineraryStatus
from ..events import (
    ItineraryCompleted,
    ItineraryCreated,
    ItineraryDayAdded,
    ItineraryItemAdded,
    ItineraryItemRemoved,
    ItineraryItemReordered,
    ItineraryPublished,
    ItineraryShared,
)
from ..value_objects.coordinates import Coordinates
from ..value_objects.money import Money


class OptimizationStrategy(Enum):
    """Itinerary optimization strategies"""
    MINIMIZE_TRAVEL_TIME = "minimize_travel_time"
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_RATING = "maximize_rating"
    BALANCE = "balance"
    THEME_BASED = "theme_based"


@dataclass
class ItineraryAggregate:
    """
    Itinerary aggregate root.
    Manages multi-day itinerary with items, optimization, and sharing.
    """
    itinerary: 'Itinerary'
    _uncommitted_events: list = field(default_factory=list, init=False)

    @classmethod
    def create(
        cls,
        user_id: UUID,
        title: str,
        start_date: date,
        end_date: date,
        description: str = "",
        budget: Money | None = None,
        theme: str | None = None,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.BALANCE,
    ) -> "ItineraryAggregate":
        """Create a new itinerary"""
        if start_date > end_date:
            raise ValueError("Start date must be before end date")

        days_count = (end_date - start_date).days + 1

        itinerary = Itinerary(
            id=uuid4(),
            user_id=user_id,
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=ItineraryStatus.DRAFT,
            budget=budget,
            theme=theme,
            optimization_strategy=optimization_strategy,
            total_days=days_count,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Create empty days
        for i in range(days_count):
            day_date = start_date + timedelta(days=i)
            day = ItineraryDay(
                id=uuid4(),
                itinerary_id=itinerary.id,
                day_number=i + 1,
                date=day_date,
                created_at=datetime.utcnow(),
            )
            itinerary.days.append(day)

        aggregate = cls(itinerary=itinerary)
        aggregate._add_event(ItineraryCreated(
            itinerary_id=itinerary.id,
            user_id=user_id,
            title=title,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            timestamp=datetime.utcnow(),
        ))
        return aggregate

    def add_day(
        self,
        date: date,
        title: str = "",
        notes: str = "",
        start_time: time | None = None,
        end_time: time | None = None,
    ) -> 'ItineraryDay':
        """Add a day to the itinerary"""
        day_number = len(self.itinerary.days) + 1
        day = ItineraryDay(
            id=uuid4(),
            itinerary_id=self.itinerary.id,
            day_number=day_number,
            date=date,
            title=title,
            notes=notes,
            start_time=start_time,
            end_time=end_time,
            created_at=datetime.utcnow(),
        )
        self.itinerary.days.append(day)
        self.itinerary.total_days = len(self.itinerary.days)
        self.itinerary.updated_at = datetime.utcnow()

        self._add_event(ItineraryDayAdded(
            itinerary_id=self.itinerary.id,
            day_id=day.id,
            day_number=day_number,
            date=date.isoformat(),
            timestamp=datetime.utcnow(),
        ))
        return day

    def remove_day(self, day_id: UUID) -> bool:
        """Remove a day from the itinerary"""
        for i, day in enumerate(self.itinerary.days):
            if day.id == day_id:
                self.itinerary.days.pop(i)
                # Renumber remaining days
                for j, d in enumerate(self.itinerary.days):
                    d.day_number = j + 1
                self.itinerary.total_days = len(self.itinerary.days)
                self.itinerary.updated_at = datetime.utcnow()
                return True
        return False

    def reorder_days(self, day_ids: list[UUID]) -> None:
        """Reorder days by providing new order of day IDs"""
        day_map = {day.id: day for day in self.itinerary.days}
        new_days = []
        for day_id in day_ids:
            if day_id in day_map:
                new_days.append(day_map[day_id])
        # Add any missing days at the end
        for day in self.itinerary.days:
            if day.id not in day_ids:
                new_days.append(day)

        for i, day in enumerate(new_days):
            day.day_number = i + 1

        self.itinerary.days = new_days
        self.itinerary.updated_at = datetime.utcnow()

    def add_item(
        self,
        day_id: UUID,
        item_type: ItemType,
        poi_id: UUID | None = None,
        title: str = "",
        description: str = "",
        start_time: time | None = None,
        end_time: time | None = None,
        duration_minutes: int = 60,
        location: Coordinates | None = None,
        address: str = "",
        cost: Money | None = None,
        transport_mode: str | None = None,
        travel_time_minutes: int = 0,
        notes: str = "",
        tags: list[str] | None = None,
    ) -> Optional['ItineraryItem']:
        """Add an item to a specific day"""
        day = next((d for d in self.itinerary.days if d.id == day_id), None)
        if not day:
            return None

        item = ItineraryItem(
            id=uuid4(),
            day_id=day_id,
            item_type=item_type,
            poi_id=poi_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            location=location,
            address=address,
            cost=cost,
            transport_mode=transport_mode,
            travel_time_minutes=travel_time_minutes,
            notes=notes,
            tags=tags or [],
            order=len(day.items),
            created_at=datetime.utcnow(),
        )

        day.items.append(item)
        day.updated_at = datetime.utcnow()
        self.itinerary.updated_at = datetime.utcnow()

        self._add_event(ItineraryItemAdded(
            itinerary_id=self.itinerary.id,
            day_id=day_id,
            item_id=item.id,
            item_type=item_type.value,
            title=title,
            timestamp=datetime.utcnow(),
        ))
        return item

    def remove_item(self, day_id: UUID, item_id: UUID) -> bool:
        """Remove an item from a day"""
        day = next((d for d in self.itinerary.days if d.id == day_id), None)
        if not day:
            return False

        for i, item in enumerate(day.items):
            if item.id == item_id:
                day.items.pop(i)
                # Reorder remaining items
                for j, item in enumerate(day.items):
                    item.order = j
                day.updated_at = datetime.utcnow()
                self.itinerary.updated_at = datetime.utcnow()

                self._add_event(ItineraryItemRemoved(
                    itinerary_id=self.itinerary.id,
                    day_id=day_id,
                    item_id=item_id,
                    timestamp=datetime.utcnow(),
                ))
                return True
        return False

    def reorder_items(self, day_id: UUID, item_ids: list[UUID]) -> None:
        """Reorder items within a day"""
        day = next((d for d in self.itinerary.days if d.id == day_id), None)
        if not day:
            return

        item_map = {item.id: item for item in day.items}
        new_items = []
        for item_id in item_ids:
            if item_id in item_map:
                new_items.append(item_map[item_id])

        # Add any missing items at the end
        for item in day.items:
            if item.id not in item_ids:
                new_items.append(item)

        for i, item in enumerate(new_items):
            item.order = i

        day.items = new_items
        day.updated_at = datetime.utcnow()
        self.itinerary.updated_at = datetime.utcnow()

        self._add_event(ItineraryItemReordered(
            itinerary_id=self.itinerary.id,
            day_id=day_id,
            item_ids=[str(id) for id in item_ids],
            timestamp=datetime.utcnow(),
        ))

    def move_item(self, item_id: UUID, from_day_id: UUID, to_day_id: UUID, new_order: int) -> bool:
        """Move an item from one day to another"""
        from_day = next((d for d in self.itinerary.days if d.id == from_day_id), None)
        to_day = next((d for d in self.itinerary.days if d.id == to_day_id), None)

        if not from_day or not to_day:
            return False

        item = next((item for item in from_day.items if item.id == item_id), None)
        if not item:
            return False

        from_day.items.remove(item)
        # Reorder from_day
        for i, item in enumerate(from_day.items):
            item.order = i
        from_day.updated_at = datetime.utcnow()

        # Insert into to_day at new_order
        to_day.items.insert(new_order, item)
        item.day_id = to_day_id
        for i, item in enumerate(to_day.items):
            item.order = i
        to_day.updated_at = datetime.utcnow()

        self.itinerary.updated_at = datetime.utcnow()
        return True

    def set_budget(self, budget: Money) -> None:
        """Set itinerary budget"""
        self.itinerary.budget = budget
        self.itinerary.updated_at = datetime.utcnow()

    def set_theme(self, theme: str) -> None:
        """Set itinerary theme"""
        self.itinerary.theme = theme
        self.itinerary.updated_at = datetime.utcnow()

    def set_optimization_strategy(self, strategy: OptimizationStrategy) -> None:
        """Set optimization strategy"""
        self.itinerary.optimization_strategy = strategy
        self.itinerary.updated_at = datetime.utcnow()

    def optimize(self) -> None:
        """Optimize itinerary based on strategy"""
        # This would call the domain service for optimization
        # For now, just mark as optimized
        self.itinerary.updated_at = datetime.utcnow()

    def share(self, share_token: str, permissions: str = "view") -> None:
        """Share itinerary with a token"""
        self.itinerary.share_token = share_token
        self.itinerary.share_permissions = permissions
        self.itinerary.updated_at = datetime.utcnow()

        self._add_event(ItineraryShared(
            itinerary_id=self.itinerary.id,
            share_token=share_token,
            permissions=permissions,
            timestamp=datetime.utcnow(),
        ))

    def unshare(self) -> None:
        """Remove sharing"""
        self.itinerary.share_token = None
        self.itinerary.share_permissions = None
        self.itinerary.updated_at = datetime.utcnow()

    def publish(self) -> None:
        """Publish itinerary publicly"""
        if self.itinerary.status == ItineraryStatus.DRAFT:
            self.itinerary.status = ItineraryStatus.PUBLISHED
            self.itinerary.published_at = datetime.utcnow()
            self.itinerary.updated_at = datetime.utcnow()

            self._add_event(ItineraryPublished(
                itinerary_id=self.itinerary.id,
                timestamp=datetime.utcnow(),
            ))

    def complete(self) -> None:
        """Mark itinerary as completed"""
        if self.itinerary.status in (ItineraryStatus.ACTIVE, ItineraryStatus.PUBLISHED):
            self.itinerary.status = ItineraryStatus.COMPLETED
            self.itinerary.completed_at = datetime.utcnow()
            self.itinerary.updated_at = datetime.utcnow()

            self._add_event(ItineraryCompleted(
                itinerary_id=self.itinerary.id,
                timestamp=datetime.utcnow(),
            ))

    def get_total_cost(self) -> Money:
        """Calculate total estimated cost"""
        total = Money.zero()
        for day in self.itinerary.days:
            for item in day.items:
                if item.cost:
                    total += item.cost
        return total

    def get_total_duration(self) -> timedelta:
        """Get total duration of all items"""
        total_minutes = 0
        for day in self.itinerary.days:
            for item in day.items:
                total_minutes += item.duration_minutes
        return timedelta(minutes=total_minutes)

    def get_items_by_type(self, item_type: ItemType) -> list['ItineraryItem']:
        """Get all items of a specific type"""
        items = []
        for day in self.itinerary.days:
            for item in day.items:
                if item.item_type == item_type:
                    items.append(item)
        return items

    def get_pois(self) -> list[UUID]:
        """Get all POI IDs in the itinerary"""
        pois = set()
        for day in self.itinerary.days:
            for item in day.items:
                if item.poi_id:
                    pois.add(item.poi_id)
        return list(pois)

    def get_daily_summary(self, day_id: UUID) -> dict:
        """Get summary for a specific day"""
        day = next((d for d in self.itinerary.days if d.id == day_id), None)
        if not day:
            return {}

        total_cost = Money.zero()
        total_duration = 0
        item_types = {}

        for item in day.items:
            if item.cost:
                total_cost += item.cost
            total_duration += item.duration_minutes
            item_types[item.item_type.value] = item_types.get(item.item_type.value, 0) + 1

        return {
            "day": day.to_dict(),
            "total_cost": total_cost.to_dict(),
            "total_duration_minutes": total_duration,
            "item_count": len(day.items),
            "item_types": item_types,
        }

    def get_overall_summary(self) -> dict:
        """Get overall itinerary summary"""
        total_cost = self.get_total_cost()
        total_duration = self.get_total_duration()
        total_items = sum(len(day.items) for day in self.itinerary.days)

        item_types = {}
        for day in self.itinerary.days:
            for item in day.items:
                item_types[item.item_type.value] = item_types.get(item.item_type.value, 0) + 1

        return {
            "itinerary": self.itinerary.to_dict(),
            "total_cost": total_cost.to_dict(),
            "total_duration": str(total_duration),
            "total_items": total_items,
            "total_days": len(self.itinerary.days),
            "item_types": item_types,
            "pois_count": len(self.get_pois()),
        }

    def _add_event(self, event) -> None:
        self._uncommitted_events.append(event)

    def get_uncommitted_events(self) -> list:
        events = self._uncommitted_events.copy()
        self._uncommitted_events.clear()
        return events

    def to_dict(self) -> dict:
        return {
            "itinerary": self.itinerary.to_dict(),
            "uncommitted_events_count": len(self._uncommitted_events),
        }
