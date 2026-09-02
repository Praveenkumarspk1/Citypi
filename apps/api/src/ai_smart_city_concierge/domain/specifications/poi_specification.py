"""
POI Specifications - Specification pattern for POI queries
"""
from dataclasses import dataclass, field
from datetime import datetime

from ..entities.poi import POI, POICategory, POISource
from ..repositories.base import Specification
from ..value_objects.coordinates import Coordinates


class POISpecification(Specification[POI]):
    """Base POI specification"""
    pass


@dataclass(frozen=True)
class POICategorySpecification(POISpecification):
    """Specification for POI category"""
    category: POICategory

    def is_satisfied_by(self, poi: POI) -> bool:
        return poi.category == self.category


@dataclass(frozen=True)
class POISubcategorySpecification(POISpecification):
    """Specification for POI subcategory"""
    subcategory: str

    def is_satisfied_by(self, poi: POI) -> bool:
        return poi.subcategory and poi.subcategory.lower() == self.subcategory.lower()


@dataclass(frozen=True)
class POISourceSpecification(POISpecification):
    """Specification for POI source"""
    source: POISource

    def is_satisfied_by(self, poi: POI) -> bool:
        return poi.source == self.source


@dataclass(frozen=True)
class POIRatingSpecification(POISpecification):
    """Specification for minimum rating"""
    min_rating: float

    def is_satisfied_by(self, poi: POI) -> bool:
        return poi.rating is not None and poi.rating >= self.min_rating


@dataclass(frozen=True)
class POIReviewCountSpecification(POISpecification):
    """Specification for minimum review count"""
    min_reviews: int

    def is_satisfied_by(self, poi: POI) -> bool:
        return poi.review_count >= self.min_reviews


@dataclass(frozen=True)
class POIPriceLevelSpecification(POISpecification):
    """Specification for price level"""
    max_price_level: int | None = None
    min_price_level: int | None = None

    def is_satisfied_by(self, poi: POI) -> bool:
        if poi.price_level is None:
            return False
        if self.min_price_level is not None and poi.price_level < self.min_price_level:
            return False
        if self.max_price_level is not None and poi.price_level > self.max_price_level:
            return False
        return True


@dataclass(frozen=True)
class POILocationSpecification(POISpecification):
    """Specification for POI within radius of coordinates"""
    center: Coordinates
    radius_meters: float

    def is_satisfied_by(self, poi: POI) -> bool:
        poi_coords = Coordinates(poi.latitude, poi.longitude)
        return poi_coords.is_within_radius(self.center, self.radius_meters)


@dataclass(frozen=True)
class POIBoundsSpecification(POISpecification):
    """Specification for POI within bounding box"""
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float

    def is_satisfied_by(self, poi: POI) -> bool:
        return (self.min_lat <= poi.latitude <= self.max_lat and
                self.min_lng <= poi.longitude <= self.max_lng)


@dataclass(frozen=True)
class POIWheelchairAccessibleSpecification(POISpecification):
    """Specification for wheelchair accessible POIs"""
    required: bool = True

    def is_satisfied_by(self, poi: POI) -> bool:
        if poi.wheelchair_accessible is None:
            return not self.required
        return poi.wheelchair_accessible == self.required


@dataclass(frozen=True)
class POIOpenNowSpecification(POISpecification):
    """Specification for POIs open at a specific time"""
    check_time: datetime | None = None

    def __post_init__(self):
        if self.check_time is None:
            object.__setattr__(self, 'check_time', datetime.utcnow())

    def is_satisfied_by(self, poi: POI) -> bool:
        if not poi.opening_hours:
            return True  # Assume open if no hours specified
        from ..value_objects.opening_hours import OpeningHours
        oh = OpeningHours.from_dict(poi.opening_hours)
        return oh.is_open_at(self.check_time)


@dataclass(frozen=True)
class POIHasPhotosSpecification(POISpecification):
    """Specification for POIs with photos"""
    required: bool = True

    def is_satisfied_by(self, poi: POI) -> bool:
        has_photos = bool(poi.photos and len(poi.photos) > 0)
        return has_photos == self.required


@dataclass(frozen=True)
class POIHasWifiSpecification(POISpecification):
    """Specification for POIs with WiFi"""
    required: bool = True

    def is_satisfied_by(self, poi: POI) -> bool:
        if poi.wifi_available is None:
            return not self.required
        return poi.wifi_available == self.required


@dataclass(frozen=True)
class POIOutdoorSeatingSpecification(POISpecification):
    """Specification for POIs with outdoor seating"""
    required: bool = True

    def is_satisfied_by(self, poi: POI) -> bool:
        if poi.outdoor_seating is None:
            return not self.required
        return poi.outdoor_seating == self.required


@dataclass(frozen=True)
class POITakeawaySpecification(POISpecification):
    """Specification for POIs with takeaway"""
    required: bool = True

    def is_satisfied_by(self, poi: POI) -> bool:
        if poi.takeaway is None:
            return not self.required
        return poi.takeaway == self.required


@dataclass(frozen=True)
class POIDeliverySpecification(POISpecification):
    """Specification for POIs with delivery"""
    required: bool = True

    def is_satisfied_by(self, poi: POI) -> bool:
        if poi.delivery is None:
            return not self.required
        return poi.delivery == self.required


@dataclass(frozen=True)
class POIReservationsSpecification(POISpecification):
    """Specification for POIs requiring reservations"""
    required: bool = True

    def is_satisfied_by(self, poi: POI) -> bool:
        if poi.reservation_required is None:
            return not self.required
        return poi.reservation_required == self.required


@dataclass(frozen=True)
class POICreditCardsSpecification(POISpecification):
    """Specification for POIs accepting credit cards"""
    required: bool = True

    def is_satisfied_by(self, poi: POI) -> bool:
        if poi.accepts_credit_cards is None:
            return not self.required
        return poi.accepts_credit_cards == self.required


@dataclass(frozen=True)
class POICashSpecification(POISpecification):
    """Specification for POIs accepting cash"""
    required: bool = True

    def is_satisfied_by(self, poi: POI) -> bool:
        if poi.accepts_cash is None:
            return not self.required
        return poi.accepts_cash == self.required


@dataclass(frozen=True)
class POIVerifiedSpecification(POISpecification):
    """Specification for verified POIs"""
    required: bool = True

    def is_satisfied_by(self, poi: POI) -> bool:
        return poi.is_verified == self.required


@dataclass(frozen=True)
class POIActiveSpecification(POISpecification):
    """Specification for active POIs"""
    required: bool = True

    def is_satisfied_by(self, poi: POI) -> bool:
        return poi.is_active == self.required


@dataclass(frozen=True)
class POITagsSpecification(POISpecification):
    """Specification for POIs with specific tags"""
    tags: list[str]
    match_all: bool = False  # If True, all tags must match; if False, any tag matches

    def is_satisfied_by(self, poi: POI) -> bool:
        if not poi.tags:
            return False
        if self.match_all:
            return all(tag in poi.tags for tag in self.tags)
        return any(tag in poi.tags for tag in self.tags)


@dataclass(frozen=True)
class POITextSearchSpecification(POISpecification):
    """Specification for text search in POI name/description"""
    query: str
    search_fields: list[str] = field(default_factory=lambda: ["name", "description", "tags"])

    def is_satisfied_by(self, poi: POI) -> bool:
        query_lower = self.query.lower()
        for field in self.search_fields:
            value = getattr(poi, field, None)
            if value:
                if isinstance(value, list):
                    if any(query_lower in str(v).lower() for v in value):
                        return True
                elif query_lower in str(value).lower():
                    return True
        return False


@dataclass(frozen=True)
class POIPopularitySpecification(POISpecification):
    """Specification for popular POIs"""
    min_popularity: float = 0.0

    def is_satisfied_by(self, poi: POI) -> bool:
        return poi.popularity_score >= self.min_popularity


@dataclass(frozen=True)
class POIVisitCountSpecification(POISpecification):
    """Specification for POIs with minimum visit count"""
    min_visits: int = 0

    def is_satisfied_by(self, poi: POI) -> bool:
        return poi.visit_count >= self.min_visits


@dataclass(frozen=True)
class POIAccessibilitySpecification(POISpecification):
    """Specification for POIs with accessibility features"""
    required_features: list[str] = field(default_factory=list)

    def is_satisfied_by(self, poi: POI) -> bool:
        if not self.required_features:
            return True
        if not poi.accessibility_profile:
            return False
        return all(poi.accessibility_profile.has_feature(f) for f in self.required_features)


@dataclass(frozen=True)
class POIDistanceSpecification(POISpecification):
    """Specification for POIs within distance from a point"""
    from_point: Coordinates
    max_distance_meters: float

    def is_satisfied_by(self, poi: POI) -> bool:
        poi_coords = Coordinates(poi.latitude, poi.longitude)
        return poi_coords.distance_to(self.from_point) <= self.max_distance_meters


# Composite specifications for common query patterns
class POISpecifications:
    """Factory for common POI specification combinations"""

    @staticmethod
    def nearby_cafes(center: Coordinates, radius_meters: float = 500) -> POISpecification:
        """Find nearby cafes"""
        return (POICategorySpecification(POICategory.CAFE) &
                POILocationSpecification(center, radius_meters) &
                POIActiveSpecification())

    @staticmethod
    def highly_rated_restaurants(min_rating: float = 4.0, min_reviews: int = 10) -> POISpecification:
        """Find highly rated restaurants"""
        return (POICategorySpecification(POICategory.RESTAURANT) &
                POIRatingSpecification(min_rating) &
                POIReviewCountSpecification(min_reviews) &
                POIActiveSpecification())

    @staticmethod
    def accessible_attractions(center: Coordinates, radius_meters: float = 1000) -> POISpecification:
        """Find wheelchair accessible attractions"""
        return (POICategorySpecification(POICategory.ATTRACTION) &
                POIWheelchairAccessibleSpecification() &
                POILocationSpecification(center, radius_meters) &
                POIActiveSpecification())

    @staticmethod
    def open_now_restaurants(check_time: datetime | None = None) -> POISpecification:
        """Find restaurants open now"""
        return (POICategorySpecification(POICategory.RESTAURANT) &
                POIOpenNowSpecification(check_time) &
                POIActiveSpecification())

    @staticmethod
    def budget_friendly_eats(max_price_level: int = 2) -> POISpecification:
        """Find budget-friendly restaurants"""
        return (POICategorySpecification(POICategory.RESTAURANT) &
                POIPriceLevelSpecification(max_price_level=max_price_level) &
                POIActiveSpecification())

    @staticmethod
    def popular_tourist_spots(min_popularity: float = 0.7) -> POISpecification:
        """Find popular tourist attractions"""
        return (POICategorySpecification(POICategory.ATTRACTION) &
                POIPopularitySpecification(min_popularity) &
                POIActiveSpecification())

    @staticmethod
    def verified_pois() -> POISpecification:
        """Find verified POIs"""
        return POIVerifiedSpecification() & POIActiveSpecification()

    @staticmethod
    def pois_with_wifi() -> POISpecification:
        """Find POIs with WiFi"""
        return POIHasWifiSpecification() & POIActiveSpecification()

    @staticmethod
    def outdoor_dining_spots() -> POISpecification:
        """Find restaurants with outdoor seating"""
        return (POICategorySpecification(POICategory.RESTAURANT) &
                POIOutdoorSeatingSpecification() &
                POIActiveSpecification())

    @staticmethod
    def delivery_restaurants() -> POISpecification:
        """Find restaurants with delivery"""
        return (POICategorySpecification(POICategory.RESTAURANT) &
                POIDeliverySpecification() &
                POIActiveSpecification())

    @staticmethod
    def text_search(query: str, category: POICategory | None = None) -> POISpecification:
        """Text search with optional category filter"""
        spec = POITextSearchSpecification(query) & POIActiveSpecification()
        if category:
            spec = spec & POICategorySpecification(category)
        return spec

    @staticmethod
    def in_bounds(min_lat: float, max_lat: float, min_lng: float, max_lng: float,
                  category: POICategory | None = None) -> POISpecification:
        """POIs within bounding box"""
        spec = POIBoundsSpecification(min_lat, max_lat, min_lng, max_lng) & POIActiveSpecification()
        if category:
            spec = spec & POICategorySpecification(category)
        return spec
