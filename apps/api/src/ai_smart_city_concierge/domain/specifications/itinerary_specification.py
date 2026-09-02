"""
Itinerary Specifications - Specification pattern for Itinerary queries
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ..entities.itinerary import Itinerary, ItineraryStatus
from ..repositories.base import Specification


class ItinerarySpecification(Specification[Itinerary]):
    """Base Itinerary specification"""
    pass


@dataclass(frozen=True)
class ItineraryUserSpecification(ItinerarySpecification):
    """Specification for itineraries by user"""
    user_id: UUID

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.user_id == self.user_id


@dataclass(frozen=True)
class ItineraryStatusSpecification(ItinerarySpecification):
    """Specification for itinerary status"""
    status: ItineraryStatus

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.status == self.status


@dataclass(frozen=True)
class ItineraryVisibilitySpecification(ItinerarySpecification):
    """Specification for itinerary visibility"""
    visibility: ItineraryVisibility

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.visibility == self.visibility


@dataclass(frozen=True)
class ItineraryDateRangeSpecification(ItinerarySpecification):
    """Specification for itineraries within date range"""
    start_date: datetime | None = None
    end_date: datetime | None = None

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        if self.start_date and itinerary.start_date < self.start_date:
            return False
        if self.end_date and itinerary.end_date > self.end_date:
            return False
        return True


@dataclass(frozen=True)
class ItineraryStartDateSpecification(ItinerarySpecification):
    """Specification for itineraries starting on/after date"""
    start_date: datetime

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.start_date >= self.start_date


@dataclass(frozen=True)
class ItineraryEndDateSpecification(ItinerarySpecification):
    """Specification for itineraries ending on/before date"""
    end_date: datetime

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.end_date <= self.end_date


@dataclass(frozen=True)
class ItineraryActiveSpecification(ItinerarySpecification):
    """Specification for active itineraries"""
    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.status == ItineraryStatus.ACTIVE


@dataclass(frozen=True)
class ItineraryCompletedSpecification(ItinerarySpecification):
    """Specification for completed itineraries"""
    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.status == ItineraryStatus.COMPLETED


@dataclass(frozen=True)
class ItineraryDraftSpecification(ItinerarySpecification):
    """Specification for draft itineraries"""
    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.status == ItineraryStatus.DRAFT


@dataclass(frozen=True)
class ItineraryPublicSpecification(ItinerarySpecification):
    """Specification for public itineraries"""
    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.visibility == ItineraryVisibility.PUBLIC


@dataclass(frozen=True)
class ItinerarySharedSpecification(ItinerarySpecification):
    """Specification for shared itineraries"""
    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.visibility in [ItineraryVisibility.SHARED, ItineraryVisibility.PUBLIC]


@dataclass(frozen=True)
class ItineraryPrivateSpecification(ItinerarySpecification):
    """Specification for private itineraries"""
    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.visibility == ItineraryVisibility.PRIVATE


@dataclass(frozen=True)
class ItineraryDurationSpecification(ItinerarySpecification):
    """Specification for itinerary duration in days"""
    min_days: int | None = None
    max_days: int | None = None

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        duration = (itinerary.end_date - itinerary.start_date).days + 1
        if self.min_days is not None and duration < self.min_days:
            return False
        if self.max_days is not None and duration > self.max_days:
            return False
        return True


@dataclass(frozen=True)
class ItineraryItemCountSpecification(ItinerarySpecification):
    """Specification for number of items in itinerary"""
    min_items: int | None = None
    max_items: int | None = None

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        total_items = sum(len(day.items) for day in itinerary.days)
        if self.min_items is not None and total_items < self.min_items:
            return False
        if self.max_items is not None and total_items > self.max_items:
            return False
        return True


@dataclass(frozen=True)
class ItineraryHasPOISpecification(ItinerarySpecification):
    """Specification for itineraries containing a specific POI"""
    poi_id: UUID

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        for day in itinerary.days:
            for item in day.items:
                if item.poi_id == self.poi_id:
                    return True
        return False


@dataclass(frozen=True)
class ItineraryCategorySpecification(ItinerarySpecification):
    """Specification for itineraries with items of specific category"""
    from ..entities.poi import POICategory
    category: POICategory

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        for day in itinerary.days:
            for item in day.items:
                if item.poi and item.poi.category == self.category:
                    return True
        return False


@dataclass(frozen=True)
class ItineraryTagSpecification(ItinerarySpecification):
    """Specification for itineraries with specific tags"""
    tags: list[str]
    match_all: bool = False

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        if not itinerary.tags:
            return False
        if self.match_all:
            return all(tag in itinerary.tags for tag in self.tags)
        return any(tag in itinerary.tags for tag in self.tags)


@dataclass(frozen=True)
class ItineraryTitleSearchSpecification(ItinerarySpecification):
    """Specification for text search in itinerary title/description"""
    query: str

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        query_lower = self.query.lower()
        return (query_lower in itinerary.title.lower() or
                (itinerary.description and query_lower in itinerary.description.lower()))


@dataclass(frozen=True)
class ItineraryCreatedAfterSpecification(ItinerarySpecification):
    """Specification for itineraries created after date"""
    date: datetime

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.created_at >= self.date


@dataclass(frozen=True)
class ItineraryUpdatedAfterSpecification(ItinerarySpecification):
    """Specification for itineraries updated after date"""
    date: datetime

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.updated_at >= self.date


@dataclass(frozen=True)
class ItinerarySharedWithUserSpecification(ItinerarySpecification):
    """Specification for itineraries shared with a user"""
    user_id: UUID

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return self.user_id in itinerary.shared_with


@dataclass(frozen=True)
class ItineraryOptimizedSpecification(ItinerarySpecification):
    """Specification for AI-optimized itineraries"""
    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        return itinerary.is_ai_generated


@dataclass(frozen=True)
class ItineraryBudgetSpecification(ItinerarySpecification):
    """Specification for itineraries within budget"""
    max_budget: float
    currency: str = "USD"

    def is_satisfied_by(self, itinerary: Itinerary) -> bool:
        if itinerary.estimated_cost is None:
            return False
        return itinerary.estimated_cost <= self.max_budget


# Composite specifications for common query patterns
class ItinerarySpecifications:
    """Factory for common Itinerary specification combinations"""

    @staticmethod
    def user_active_itineraries(user_id: UUID) -> ItinerarySpecification:
        """Get user's active itineraries"""
        return (ItineraryUserSpecification(user_id) &
                ItineraryActiveSpecification())

    @staticmethod
    def user_completed_itineraries(user_id: UUID) -> ItinerarySpecification:
        """Get user's completed itineraries"""
        return (ItineraryUserSpecification(user_id) &
                ItineraryCompletedSpecification())

    @staticmethod
    def user_draft_itineraries(user_id: UUID) -> ItinerarySpecification:
        """Get user's draft itineraries"""
        return (ItineraryUserSpecification(user_id) &
                ItineraryDraftSpecification())

    @staticmethod
    def public_itineraries() -> ItinerarySpecification:
        """Get all public itineraries"""
        return ItineraryPublicSpecification()

    @staticmethod
    def shared_itineraries() -> ItinerarySpecification:
        """Get all shared itineraries"""
        return ItinerarySharedSpecification()

    @staticmethod
    def upcoming_itineraries(days_ahead: int = 30) -> ItinerarySpecification:
        """Get itineraries starting within days_ahead"""
        from datetime import datetime, timedelta
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        return (ItineraryStartDateSpecification(datetime.utcnow()) &
                ItineraryEndDateSpecification(end_date) &
                ItineraryActiveSpecification())

    @staticmethod
    def past_itineraries() -> ItinerarySpecification:
        """Get past itineraries"""
        return ItineraryEndDateSpecification(datetime.utcnow())

    @staticmethod
    def current_itineraries() -> ItinerarySpecification:
        """Get currently active itineraries (today)"""
        now = datetime.utcnow()
        return (ItineraryStartDateSpecification(now) &
                ItineraryEndDateSpecification(now) &
                ItineraryActiveSpecification())

    @staticmethod
    def weekend_itineraries() -> ItinerarySpecification:
        """Get weekend itineraries (Saturday-Sunday)"""
        # This would need custom logic - placeholder
        return ItineraryActiveSpecification()

    @staticmethod
    def multi_day_itineraries(min_days: int = 2) -> ItinerarySpecification:
        """Get multi-day itineraries"""
        return ItineraryDurationSpecification(min_days=min_days)

    @staticmethod
    def day_trip_itineraries() -> ItinerarySpecification:
        """Get single-day itineraries"""
        return ItineraryDurationSpecification(max_days=1)

    @staticmethod
    def itineraries_with_poi(poi_id: UUID) -> ItinerarySpecification:
        """Get itineraries containing a specific POI"""
        return ItineraryHasPOISpecification(poi_id)

    @staticmethod
    def food_itineraries() -> ItinerarySpecification:
        """Get food-focused itineraries"""
        from ..entities.poi import POICategory
        return ItineraryCategorySpecification(POICategory.RESTAURANT)

    @staticmethod
    def attraction_itineraries() -> ItinerarySpecification:
        """Get attraction-focused itineraries"""
        from ..entities.poi import POICategory
        return ItineraryCategorySpecification(POICategory.ATTRACTION)

    @staticmethod
    def budget_itineraries(max_budget: float) -> ItinerarySpecification:
        """Get itineraries within budget"""
        return ItineraryBudgetSpecification(max_budget)

    @staticmethod
    def ai_generated_itineraries() -> ItinerarySpecification:
        """Get AI-generated itineraries"""
        return ItineraryOptimizedSpecification()

    @staticmethod
    def recently_created(days: int = 7) -> ItinerarySpecification:
        """Get recently created itineraries"""
        from datetime import datetime, timedelta
        return ItineraryCreatedAfterSpecification(datetime.utcnow() - timedelta(days=days))

    @staticmethod
    def recently_updated(days: int = 7) -> ItinerarySpecification:
        """Get recently updated itineraries"""
        from datetime import datetime, timedelta
        return ItineraryUpdatedAfterSpecification(datetime.utcnow() - timedelta(days=days))
