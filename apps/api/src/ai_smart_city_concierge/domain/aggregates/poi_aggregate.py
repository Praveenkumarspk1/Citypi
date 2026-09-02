"""
POI Aggregate
"""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from ..entities.poi import POI, POICategory, POISource
from ..events import (
    POICreated,
    POIPhotoAdded,
    POIReviewAdded,
    POIStatusChanged,
    POIUpdated,
    POIVerified,
)
from ..value_objects.address import Address
from ..value_objects.coordinates import Coordinates
from ..value_objects.opening_hours import OpeningHours
from ..value_objects.rating import Rating, RatingDistribution


@dataclass
class POIAggregate:
    """
    POI aggregate root.
    Manages point of interest lifecycle, reviews, photos, and verification.
    """
    poi: 'POI'
    _uncommitted_events: list = field(default_factory=list, init=False)

    @classmethod
    def create(
        cls,
        name: str,
        category: POICategory,
        coordinates: Coordinates,
        source: POISource = POISource.USER_GENERATED,
        external_id: str | None = None,
        name_local: str | None = None,
        description: str = "",
        address: Address | None = None,
        opening_hours: OpeningHours | None = None,
        contact_phone: str | None = None,
        contact_email: str | None = None,
        contact_website: str | None = None,
        contact_facebook: str | None = None,
        contact_instagram: str | None = None,
        contact_twitter: str | None = None,
        wheelchair_accessible: bool | None = None,
        wifi_available: bool | None = None,
        outdoor_seating: bool | None = None,
        takeaway: bool | None = None,
        delivery: bool | None = None,
        reservation_required: bool | None = None,
        accepts_credit_cards: bool | None = None,
        accepts_cash: bool | None = None,
        price_level: int | None = None,
        photos: list[str] | None = None,
        featured_photo: str | None = None,
        tags: list[str] | None = None,
        created_by: UUID | None = None,
    ) -> "POIAggregate":
        """Create a new POI"""
        poi = POI(
            id=uuid4(),
            external_id=external_id,
            source=source,
            name=name,
            name_local=name_local,
            description=description,
            category=category,
            subcategory=None,
            tags=tags or [],
            latitude=coordinates.latitude,
            longitude=coordinates.longitude,
            address=address.to_dict() if address else None,
            city=address.city if address else None,
            state=address.state if address else None,
            country=address.country if address else None,
            postal_code=address.postal_code if address else None,
            neighborhood=address.neighborhood if address else None,
            contact_phone=contact_phone,
            contact_email=contact_email,
            contact_website=contact_website,
            contact_facebook=contact_facebook,
            contact_instagram=contact_instagram,
            contact_twitter=contact_twitter,
            opening_hours=opening_hours.to_dict() if opening_hours else None,
            wheelchair_accessible=wheelchair_accessible,
            wifi_available=wifi_available,
            outdoor_seating=outdoor_seating,
            takeaway=takeaway,
            delivery=delivery,
            reservation_required=reservation_required,
            accepts_credit_cards=accepts_credit_cards,
            accepts_cash=accepts_cash,
            price_level=price_level,
            photos=photos or [],
            featured_photo=featured_photo,
            rating=Rating.unrated(),
            rating_distribution=RatingDistribution.empty(),
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=created_by,
        )

        aggregate = cls(poi=poi)
        aggregate._add_event(POICreated(
            poi_id=poi.id,
            name=poi.name,
            category=poi.category.value,
            coordinates={"lat": poi.latitude, "lng": poi.longitude},
            source=poi.source.value,
            created_by=created_by,
            timestamp=datetime.utcnow(),
        ))
        return aggregate

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
        old_values = {}
        new_values = {}

        if name is not None and name != self.poi.name:
            old_values["name"] = self.poi.name
            new_values["name"] = name
            self.poi.name = name

        if name_local is not None and name_local != self.poi.name_local:
            old_values["name_local"] = self.poi.name_local
            new_values["name_local"] = name_local
            self.poi.name_local = name_local

        if description is not None and description != self.poi.description:
            old_values["description"] = self.poi.description
            new_values["description"] = description
            self.poi.description = description

        if category is not None and category != self.poi.category:
            old_values["category"] = self.poi.category.value
            new_values["category"] = category.value
            self.poi.category = category

        if subcategory is not None and subcategory != self.poi.subcategory:
            old_values["subcategory"] = self.poi.subcategory
            new_values["subcategory"] = subcategory
            self.poi.subcategory = subcategory

        if tags is not None and tags != self.poi.tags:
            old_values["tags"] = self.poi.tags
            new_values["tags"] = tags
            self.poi.tags = tags

        if new_values:
            self.poi.updated_at = datetime.utcnow()
            self._add_event(POIUpdated(
                poi_id=self.poi.id,
                old_values=old_values,
                new_values=new_values,
                timestamp=datetime.utcnow(),
            ))

    def update_location(
        self,
        coordinates: Coordinates | None = None,
        address: Address | None = None,
    ) -> None:
        """Update POI location"""
        old_values = {}
        new_values = {}

        if coordinates is not None:
            old_values["latitude"] = self.poi.latitude
            old_values["longitude"] = self.poi.longitude
            new_values["latitude"] = coordinates.latitude
            new_values["longitude"] = coordinates.longitude
            self.poi.latitude = coordinates.latitude
            self.poi.longitude = coordinates.longitude

        if address is not None:
            old_values["address"] = self.poi.address
            new_values["address"] = address.to_dict()
            self.poi.address = address.to_dict()
            self.poi.city = address.city
            self.poi.state = address.state
            self.poi.country = address.country
            self.postal_code = address.postal_code
            self.neighborhood = address.neighborhood

        if new_values:
            self.poi.updated_at = datetime.utcnow()
            self._add_event(POIUpdated(
                poi_id=self.poi.id,
                old_values=old_values,
                new_values=new_values,
                timestamp=datetime.utcnow(),
            ))

    def update_contact_info(
        self,
        phone: str | None = None,
        email: str | None = None,
        website: str | None = None,
        facebook: str | None = None,
        instagram: str | None = None,
        twitter: str | None = None,
    ) -> None:
        """Update contact information"""
        old_values = {}
        new_values = {}

        fields = {
            "contact_phone": phone,
            "contact_email": email,
            "contact_website": website,
            "contact_facebook": facebook,
            "contact_instagram": instagram,
            "contact_twitter": twitter,
        }

        for field, value in fields.items():
            if value is not None and value != getattr(self.poi, field):
                old_values[field] = getattr(self.poi, field)
                new_values[field] = value
                setattr(self.poi, field, value)

        if new_values:
            self.poi.updated_at = datetime.utcnow()
            self._add_event(POIUpdated(
                poi_id=self.poi.id,
                old_values=old_values,
                new_values=new_values,
                timestamp=datetime.utcnow(),
            ))

    def update_opening_hours(self, opening_hours: OpeningHours) -> None:
        """Update opening hours"""
        if self.poi.opening_hours != opening_hours.to_dict():
            self.poi.opening_hours = opening_hours.to_dict()
            self.poi.updated_at = datetime.utcnow()
            self._add_event(POIUpdated(
                poi_id=self.poi.id,
                old_values={"opening_hours": self.poi.opening_hours},
                new_values={"opening_hours": opening_hours.to_dict()},
                timestamp=datetime.utcnow(),
            ))

    def update_features(
        self,
        wheelchair_accessible: bool | None = None,
        wifi_available: bool | None = None,
        outdoor_seating: bool | None = None,
        takeaway: bool | None = None,
        delivery: bool | None = None,
        reservation_required: bool | None = None,
        accepts_credit_cards: bool | None = None,
        accepts_cash: bool | None = None,
        price_level: int | None = None,
    ) -> None:
        """Update POI features"""
        old_values = {}
        new_values = {}

        fields = {
            "wheelchair_accessible": wheelchair_accessible,
            "wifi_available": wifi_available,
            "outdoor_seating": outdoor_seating,
            "takeaway": takeaway,
            "delivery": delivery,
            "reservation_required": reservation_required,
            "accepts_credit_cards": accepts_credit_cards,
            "accepts_cash": accepts_cash,
            "price_level": price_level,
        }

        for field, value in fields.items():
            if value is not None and value != getattr(self.poi, field):
                old_values[field] = getattr(self.poi, field)
                new_values[field] = value
                setattr(self.poi, field, value)

        if new_values:
            self.poi.updated_at = datetime.utcnow()
            self._add_event(POIUpdated(
                poi_id=self.poi.id,
                old_values=old_values,
                new_values=new_values,
                timestamp=datetime.utcnow(),
            ))

    def add_photo(self, photo_url: str, is_featured: bool = False) -> None:
        """Add a photo to the POI"""
        if photo_url not in self.poi.photos:
            self.poi.photos.append(photo_url)
            if is_featured or not self.poi.featured_photo:
                self.poi.featured_photo = photo_url
            self.poi.updated_at = datetime.utcnow()
            self._add_event(POIPhotoAdded(
                poi_id=self.poi.id,
                photo_url=photo_url,
                is_featured=is_featured,
                timestamp=datetime.utcnow(),
            ))

    def remove_photo(self, photo_url: str) -> bool:
        """Remove a photo from the POI"""
        if photo_url in self.poi.photos:
            self.poi.photos.remove(photo_url)
            if self.poi.featured_photo == photo_url:
                self.poi.featured_photo = self.poi.photos[0] if self.poi.photos else None
            self.poi.updated_at = datetime.utcnow()
            return True
        return False

    def add_review(
        self,
        user_id: UUID,
        rating: Rating,
        review_text: str = "",
        photos: list[str] | None = None,
    ) -> None:
        """Add a review to the POI"""
        # Update rating
        new_rating = self.poi.rating.add_review(rating.value)
        self.poi.rating = new_rating

        # Update distribution
        stars = rating.stars
        self.poi.rating_distribution = self.poi.rating_distribution.add_rating(stars)

        self.poi.updated_at = datetime.utcnow()
        self._add_event(POIReviewAdded(
            poi_id=self.poi.id,
            user_id=user_id,
            rating=rating.value,
            review_text=review_text,
            photos=photos or [],
            timestamp=datetime.utcnow(),
        ))

    def verify(self, verified_by: UUID) -> None:
        """Verify the POI"""
        if not self.poi.is_verified:
            self.poi.is_verified = True
            self.poi.verified_at = datetime.utcnow()
            self.poi.verified_by = verified_by
            self.poi.updated_at = datetime.utcnow()
            self._add_event(POIVerified(
                poi_id=self.poi.id,
                verified_by=verified_by,
                timestamp=datetime.utcnow(),
            ))

    def change_status(self, is_active: bool) -> None:
        """Activate or deactivate POI"""
        if self.poi.is_active != is_active:
            self.poi.is_active = is_active
            self.poi.updated_at = datetime.utcnow()
            self._add_event(POIStatusChanged(
                poi_id=self.poi.id,
                is_active=is_active,
                timestamp=datetime.utcnow(),
            ))

    def update_rating(self, new_rating: Rating) -> None:
        """Update POI rating (for external sync)"""
        if new_rating != self.poi.rating:
            self.poi.rating = new_rating
            self.poi.updated_at = datetime.utcnow()
            self._add_event(POIUpdated(
                poi_id=self.poi.id,
                old_values={"rating": str(self.poi.rating.value)},
                new_values={"rating": str(new_rating.value)},
                timestamp=datetime.utcnow(),
            ))

    def add_tag(self, tag: str) -> None:
        """Add a tag to the POI"""
        if tag not in self.poi.tags:
            self.poi.tags.append(tag)
            self.poi.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the POI"""
        if tag in self.poi.tags:
            self.poi.tags.remove(tag)
            self.poi.updated_at = datetime.utcnow()
            return True
        return False

    def get_distance_to(self, coordinates: Coordinates) -> float:
        """Get distance to coordinates in meters"""
        poi_coords = Coordinates(self.poi.latitude, self.poi.longitude)
        return poi_coords.distance_to(coordinates)

    def is_within_radius(self, center: Coordinates, radius_meters: float) -> bool:
        """Check if POI is within radius of center"""
        poi_coords = Coordinates(self.poi.latitude, self.poi.longitude)
        return poi_coords.is_within_radius(center, radius_meters)

    def is_open_now(self) -> bool:
        """Check if POI is currently open"""
        if not self.poi.opening_hours:
            return True  # Assume open if no hours specified
        return OpeningHours.from_dict(self.poi.opening_hours).is_open_at(datetime.utcnow())

    def get_current_status(self) -> dict:
        """Get current open/closed status"""
        is_open = self.is_open_now()
        return {
            "is_open": is_open,
            "opening_hours": self.poi.opening_hours,
            "timezone": "UTC",  # Would be from POI location
        }

    def to_dict(self) -> dict:
        return {
            "poi": self.poi.to_dict(),
            "uncommitted_events_count": len(self._uncommitted_events),
        }

    def _add_event(self, event) -> None:
        self._uncommitted_events.append(event)

    def get_uncommitted_events(self) -> list:
        events = self._uncommitted_events.copy()
        self._uncommitted_events.clear()
        return events
