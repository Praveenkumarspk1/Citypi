"""
Point of Interest (POI) Domain Entity
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from ..value_objects.coordinates import Coordinates


class POICategory(StrEnum):
    """POI categories based on OSM taxonomy"""
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    BAR = "bar"
    FAST_FOOD = "fast_food"
    MUSEUM = "museum"
    GALLERY = "gallery"
    PARK = "park"
    GARDEN = "garden"
    NATURE_RESERVE = "nature_reserve"
    HOTEL = "hotel"
    HOSTEL = "hostel"
    GUEST_HOUSE = "guest_house"
    APARTMENT = "apartment"
    CAMPING = "camping"
    SHOP = "shop"
    MALL = "mall"
    MARKET = "market"
    SUPERMARKET = "supermarket"
    CONVENIENCE = "convenience"
    PHARMACY = "pharmacy"
    BAKERY = "bakery"
    CLOTHING = "clothing"
    ELECTRONICS = "electronics"
    BOOKSTORE = "bookstore"
    TRANSPORT_STATION = "transport_station"
    BUS_STOP = "bus_stop"
    TRAIN_STATION = "train_station"
    SUBWAY_STATION = "subway_station"
    AIRPORT = "airport"
    FERRY_TERMINAL = "ferry_terminal"
    TAXI_STAND = "taxi_stand"
    BIKE_RENTAL = "bike_rental"
    CAR_RENTAL = "car_rental"
    CHARGING_STATION = "charging_station"
    FUEL = "fuel"
    PARKING = "parking"
    LANDMARK = "landmark"
    MONUMENT = "monument"
    VIEWPOINT = "viewpoint"
    HISTORIC = "historic"
    RELIGIOUS = "religious"
    CHURCH = "church"
    TEMPLE = "temple"
    MOSQUE = "mosque"
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    DOCTOR = "doctor"
    DENTIST = "dentist"
    VETERINARY = "veterinary"
    UNIVERSITY = "university"
    SCHOOL = "school"
    LIBRARY = "library"
    CINEMA = "cinema"
    THEATRE = "theatre"
    NIGHTCLUB = "nightclub"
    CASINO = "casino"
    STADIUM = "stadium"
    SPORTS_CENTER = "sports_center"
    SWIMMING_POOL = "swimming_pool"
    GYM = "gym"
    BEACH = "beach"
    MARINA = "marina"
    HARBOR = "harbor"
    ATM = "atm"
    BANK = "bank"
    POST_OFFICE = "post_office"
    POLICE = "police"
    FIRE_STATION = "fire_station"
    EMBASSY = "embassy"
    COURTHOUSE = "courthouse"
    TOWN_HALL = "town_hall"
    COMMUNITY_CENTER = "community_center"
    PUBLIC_TOILET = "public_toilet"
    DRINKING_WATER = "drinking_water"
    WIFI = "wifi"
    RECYCLING = "recycling"
    WASTE_BASKET = "waste_basket"
    BENCH = "bench"
    SHELTER = "shelter"
    INFORMATION = "information"
    TOURIST_INFO = "tourist_info"
    OTHER = "other"


class POISource(StrEnum):
    """Source of POI data"""
    OSM = "osm"
    OVERPASS = "overpass"
    GOOGLE_PLACES = "google_places"
    FOURSQUARE = "foursquare"
    YELP = "yelp"
    TRIPADVISOR = "tripadvisor"
    MANUAL = "manual"
    USER_GENERATED = "user_generated"
    PARTNER = "partner"


@dataclass
class OpeningHours:
    """Opening hours for a POI"""
    monday: str | None = field(default_factory=lambda: [])
    tuesday: str | None = None
    wednesday: str | None = None
    thursday: str | None = None
    friday: str | None = None
    saturday: str | None = None
    sunday: str | None = None
    holidays: str | None = None

    def is_open_now(self, timezone: str = "UTC") -> bool:
        """Check if POI is open now (simplified)"""
        # This would need proper timezone handling and parsing
        # For now, return True if we have any hours
        return any([
            self.monday, self.tuesday, self.wednesday,
            self.thursday, self.friday, self.saturday, self.sunday
        ])

    def to_dict(self) -> dict:
        return {
            "monday": self.monday,
            "tuesday": self.tuesday,
            "wednesday": self.wednesday,
            "thursday": self.thursday,
            "friday": self.friday,
            "saturday": self.saturday,
            "sunday": self.sunday,
            "holidays": self.holidays,
        }


@dataclass
class ContactInfo:
    """Contact information for a POI"""
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    facebook: str | None = None
    instagram: str | None = None
    twitter: str | None = None

    def to_dict(self) -> dict:
        return {
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "facebook": self.facebook,
            "instagram": self.instagram,
            "twitter": self.twitter,
        }


@dataclass
class POI:
    """
    Point of Interest aggregate root.
    Represents a place of interest in the city.
    """
    id: UUID = field(default_factory=uuid4)
    external_id: str | None = None  # OSM ID, Google Place ID, etc.
    source: POISource = POISource.OSM

    # Basic info
    name: str = ""
    name_local: str | None = None
    description: str | None = None
    category: POICategory = POICategory.OTHER
    subcategory: str | None = None
    tags: list[str] = field(default_factory=list)

    # Location
    coordinates: Coordinates = field(default_factory=lambda: Coordinates(0, 0))
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    neighborhood: str | None = None

    # Contact & Hours
    contact: ContactInfo = field(default_factory=ContactInfo)
    opening_hours: OpeningHours | None = None

    # Attributes
    wheelchair_accessible: bool | None = None
    wifi_available: bool | None = None
    outdoor_seating: bool | None = None
    takeaway: bool | None = None
    delivery: bool | None = None
    reservation_required: bool | None = None
    accepts_credit_cards: bool | None = None
    accepts_cash: bool | None = None
    price_level: int | None = None  # 1-4

    # Media
    photos: list[str] = field(default_factory=list)  # URLs
    featured_photo: str | None = None

    # Ratings & Reviews
    rating: float | None = None
    review_count: int = 0
    user_ratings_total: int = 0

    # Popularity & Trends
    popularity_score: float = 0.0
    visit_count: int = 0
    last_visited_at: datetime | None = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    verified_at: datetime | None = None
    verified_by: UUID | None = None
    is_active: bool = True
    is_verified: bool = False

    # Vector embedding reference
    embedding_id: str | None = None

    def __post_init__(self) -> None:
        """Validate POI after initialization"""
        if not self.name:
            raise ValueError("POI name is required")
        if not isinstance(self.coordinates, Coordinates):
            raise ValueError("Coordinates must be a Coordinates object")

    def update_basic_info(
        self,
        name: str | None = None,
        name_local: str | None = None,
        description: str | None = None,
        category: POICategory | None = None,
        subcategory: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Update basic POI information"""
        if name is not None:
            self.name = name
        if name_local is not None:
            self.name_local = name_local
        if description is not None:
            self.description = description
        if category is not None:
            self.category = category
        if subcategory is not None:
            self.subcategory = subcategory
        if tags is not None:
            self.tags = tags
        self.updated_at = datetime.utcnow()

    def update_location(
        self,
        coordinates: Coordinates | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        postal_code: str | None = None,
        neighborhood: str | None = None,
    ) -> None:
        """Update location information"""
        if coordinates is not None:
            self.coordinates = coordinates
        if address is not None:
            self.address = address
        if city is not None:
            self.city = city
        if state is not None:
            self.state = state
        if country is not None:
            self.country = country
        if postal_code is not None:
            self.postal_code = postal_code
        if neighborhood is not None:
            self.neighborhood = neighborhood
        self.updated_at = datetime.utcnow()

    def update_contact(self, contact: ContactInfo) -> None:
        """Update contact information"""
        self.contact = contact
        self.updated_at = datetime.utcnow()

    def update_hours(self, hours: OpeningHours) -> None:
        """Update opening hours"""
        self.opening_hours = hours
        self.updated_at = datetime.utcnow()

    def add_photo(self, photo_url: str, featured: bool = False) -> None:
        """Add a photo"""
        if photo_url not in self.photos:
            self.photos.append(photo_url)
        if featured or not self.featured_photo:
            self.featured_photo = photo_url
        self.updated_at = datetime.utcnow()

    def remove_photo(self, photo_url: str) -> None:
        """Remove a photo"""
        if photo_url in self.photos:
            self.photos.remove(photo_url)
        if self.featured_photo == photo_url:
            self.featured_photo = self.photos[0] if self.photos else None
        self.updated_at = datetime.utcnow()

    def update_rating(self, rating: float, review_count: int) -> None:
        """Update rating"""
        self.rating = rating
        self.review_count = review_count
        self.updated_at = datetime.utcnow()

    def increment_visit(self) -> None:
        """Increment visit count"""
        self.visit_count += 1
        self.last_visited_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_popularity(self, score: float) -> None:
        """Update popularity score"""
        self.popularity_score = score
        self.updated_at = datetime.utcnow()

    def verify(self, verified_by: UUID) -> None:
        """Mark POI as verified"""
        self.is_verified = True
        self.verified_at = datetime.utcnow()
        self.verified_by = verified_by
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate POI"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate POI"""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def set_embedding_id(self, embedding_id: str) -> None:
        """Set vector embedding reference"""
        self.embedding_id = embedding_id
        self.updated_at = datetime.utcnow()

    def distance_to(self, coordinates: Coordinates) -> float:
        """Calculate distance to given coordinates in meters"""
        return self.coordinates.distance_to(coordinates)

    def distance_km_to(self, coordinates: Coordinates) -> float:
        """Calculate distance in kilometers"""
        return self.distance_to(coordinates) / 1000

    def is_within_radius(self, center: Coordinates, radius_meters: float) -> bool:
        """Check if POI is within radius of center"""
        return self.coordinates.is_within_radius(center, radius_meters)

    def to_dict(self, include_embedding: bool = False) -> dict:
        """Convert to dictionary"""
        data = {
            "id": str(self.id),
            "external_id": self.external_id,
            "source": self.source.value,
            "name": self.name,
            "name_local": self.name_local,
            "description": self.description,
            "category": self.category.value,
            "subcategory": self.subcategory,
            "tags": self.tags,
            "coordinates": self.coordinates.to_dict(),
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "postal_code": self.postal_code,
            "neighborhood": self.neighborhood,
            "contact": self.contact.to_dict(),
            "opening_hours": self.opening_hours.to_dict() if self.opening_hours else None,
            "wheelchair_accessible": self.wheelchair_accessible,
            "wifi_available": self.wifi_available,
            "outdoor_seating": self.outdoor_seating,
            "takeaway": self.takeaway,
            "delivery": self.delivery,
            "reservation_required": self.reservation_required,
            "accepts_credit_cards": self.accepts_credit_cards,
            "accepts_cash": self.accepts_cash,
            "price_level": self.price_level,
            "photos": self.photos,
            "featured_photo": self.featured_photo,
            "rating": self.rating,
            "review_count": self.review_count,
            "user_ratings_total": self.user_ratings_total,
            "popularity_score": self.popularity_score,
            "visit_count": self.visit_count,
            "last_visited_at": self.last_visited_at.isoformat() if self.last_visited_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "verified_by": str(self.verified_by) if self.verified_by else None,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
        }
        if include_embedding:
            data["embedding_id"] = self.embedding_id
        return data

    def to_geojson(self) -> dict:
        """Convert to GeoJSON Feature"""
        return {
            "type": "Feature",
            "geometry": self.coordinates.to_geojson(),
            "properties": {
                "id": str(self.id),
                "name": self.name,
                "category": self.category.value,
                "subcategory": self.subcategory,
                "address": self.address,
                "rating": self.rating,
                "featured_photo": self.featured_photo,
            }
        }
