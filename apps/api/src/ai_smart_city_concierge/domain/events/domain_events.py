"""
Domain Events
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from ..entities.conversation import Conversation, Message
from ..entities.feedback import Feedback
from ..entities.itinerary import Itinerary
from ..entities.media import Media
from ..entities.poi import POI
from ..entities.transit import TransitRoute
from ..entities.user import User
from ..entities.weather import WeatherForecast
from ..value_objects.coordinates import Coordinates


class EventType(StrEnum):
    """Domain event types"""
    # User events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_EMAIL_VERIFIED = "user_email_verified"
    USER_LOGGED_IN = "user_logged_in"
    USER_PREFERENCES_UPDATED = "user_preferences_updated"

    # POI events
    POI_CREATED = "poi_created"
    POI_UPDATED = "poi_updated"
    POI_DELETED = "poi_deleted"
    POI_VERIFIED = "poi_verified"
    POI_RATING_UPDATED = "poi_rating_updated"
    POI_PHOTO_ADDED = "poi_photo_added"
    POI_FAVORITED = "poi_favorited"
    POI_UNFAVORITED = "poi_unfavorited"

    # Conversation events
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_MESSAGE_ADDED = "conversation_message_added"
    CONVERSATION_UPDATED = "conversation_updated"
    CONVERSATION_ARCHIVED = "conversation_archived"
    CONVERSATION_DELETED = "conversation_deleted"
    CONVERSATION_SUMMARY_GENERATED = "conversation_summary_generated"

    # Itinerary events
    ITINERARY_CREATED = "itinerary_created"
    ITINERARY_UPDATED = "itinerary_updated"
    ITINERARY_DELETED = "itinerary_deleted"
    ITINERARY_DAY_ADDED = "itinerary_day_added"
    ITINERARY_ITEM_ADDED = "itinerary_item_added"
    ITINERARY_ITEM_REMOVED = "itinerary_item_removed"
    ITINERARY_ACTIVATED = "itinerary_activated"
    ITINERARY_COMPLETED = "itinerary_completed"
    ITINERARY_SHARED = "itinerary_shared"
    ITINERARY_GENERATED_BY_AI = "itinerary_generated_by_ai"

    # Transit events
    TRANSIT_ROUTE_CALCULATED = "transit_route_calculated"
    TRANSIT_REALTIME_UPDATED = "transit_realtime_updated"
    TRANSIT_ALERT_CREATED = "transit_alert_created"
    TRANSIT_ROUTE_CREATED = "transit_route_created"
    TRANSIT_STOP_ADDED = "transit_stop_added"
    TRANSIT_TRIP_PLANNED = "transit_trip_planned"
    TRANSIT_VEHICLE_POSITION_UPDATED = "transit_vehicle_position_updated"
    TRANSIT_SERVICE_ALERT_CREATED = "transit_service_alert_created"

    # Weather events
    WEATHER_FETCHED = "weather_fetched"
    WEATHER_ALERT_ISSUED = "weather_alert_issued"

    # Media events
    MEDIA_UPLOADED = "media_uploaded"
    MEDIA_PROCESSED = "media_processed"
    MEDIA_DELETED = "media_deleted"
    MEDIA_MODERATED = "media_moderated"

    # Feedback events
    FEEDBACK_SUBMITTED = "feedback_submitted"
    FEEDBACK_MODERATED = "feedback_moderated"
    FEEDBACK_RESPONDED = "feedback_responded"

    # Recommendation events
    RECOMMENDATION_GENERATED = "recommendation_generated"
    RECOMMENDATION_SAVED = "recommendation_saved"
    RECOMMENDATION_CLICKED = "recommendation_clicked"
    RECOMMENDATION_DISMISSED = "recommendation_dismissed"
    RECOMMENDATION_FEEDBACK = "recommendation_feedback"

    # Search events
    SEARCH_PERFORMED = "search_performed"

    # Analytics events
    ANALYTICS_EVENT_RECORDED = "analytics_event_recorded"


@dataclass
class DomainEvent:
    """Base domain event"""
    id: UUID = field(default_factory=uuid4)
    event_type: EventType = EventType.USER_CREATED
    aggregate_id: UUID = field(default_factory=uuid4)
    aggregate_type: str = ""
    user_id: UUID | None = None
    correlation_id: UUID | None = None
    causation_id: UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "event_type": self.event_type.value,
            "aggregate_id": str(self.aggregate_id),
            "aggregate_type": self.aggregate_type,
            "user_id": str(self.user_id) if self.user_id else None,
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
            "causation_id": str(self.causation_id) if self.causation_id else None,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
        }


# User Events
@dataclass
class UserCreatedEvent(DomainEvent):
    event_type: EventType = EventType.USER_CREATED
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user: User, correlation_id: UUID | None = None) -> "UserCreatedEvent":
        return cls(
            aggregate_id=user.id,
            user_id=user.id,
            correlation_id=correlation_id,
            payload=user.to_dict(),
        )


@dataclass
class UserUpdatedEvent(DomainEvent):
    event_type: EventType = EventType.USER_UPDATED
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user: User, changes: dict[str, Any], correlation_id: UUID | None = None) -> "UserUpdatedEvent":
        return cls(
            aggregate_id=user.id,
            user_id=user.id,
            correlation_id=correlation_id,
            payload={"user": user.to_dict(), "changes": changes},
        )


@dataclass
class UserDeletedEvent(DomainEvent):
    event_type: EventType = EventType.USER_DELETED
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user: User, correlation_id: UUID | None = None) -> "UserDeletedEvent":
        return cls(
            aggregate_id=user.id,
            user_id=user.id,
            correlation_id=correlation_id,
            payload={"user_id": str(user.id), "email": user.email},
        )


@dataclass
class UserEmailVerifiedEvent(DomainEvent):
    event_type: EventType = EventType.USER_EMAIL_VERIFIED
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user: User, correlation_id: UUID | None = None) -> "UserEmailVerifiedEvent":
        return cls(
            aggregate_id=user.id,
            user_id=user.id,
            correlation_id=correlation_id,
            payload={"user_id": str(user.id), "email": user.email},
        )


@dataclass
class UserLoggedInEvent(DomainEvent):
    event_type: EventType = EventType.USER_LOGGED_IN
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user: User, ip_address: str | None = None, user_agent: str | None = None, correlation_id: UUID | None = None) -> "UserLoggedInEvent":
        return cls(
            aggregate_id=user.id,
            user_id=user.id,
            correlation_id=correlation_id,
            payload={"user_id": str(user.id), "ip_address": ip_address, "user_agent": user_agent},
        )


@dataclass
class UserPreferencesUpdatedEvent(DomainEvent):
    event_type: EventType = EventType.USER_PREFERENCES_UPDATED
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user: User, preferences: dict[str, Any], correlation_id: UUID | None = None) -> "UserPreferencesUpdatedEvent":
        return cls(
            aggregate_id=user.id,
            user_id=user.id,
            correlation_id=correlation_id,
            payload={"user_id": str(user.id), "preferences": preferences},
        )


# POI Events
@dataclass
class POICreatedEvent(DomainEvent):
    event_type: EventType = EventType.POI_CREATED
    aggregate_type: str = "POI"

    @classmethod
    def create(cls, poi: POI, correlation_id: UUID | None = None) -> "POICreatedEvent":
        return cls(
            aggregate_id=poi.id,
            user_id=poi.verified_by,
            correlation_id=correlation_id,
            payload=poi.to_dict(),
        )


@dataclass
class POIUpdatedEvent(DomainEvent):
    event_type: EventType = EventType.POI_UPDATED
    aggregate_type: str = "POI"

    @classmethod
    def create(cls, poi: POI, changes: dict[str, Any], correlation_id: UUID | None = None) -> "POIUpdatedEvent":
        return cls(
            aggregate_id=poi.id,
            user_id=poi.verified_by,
            correlation_id=correlation_id,
            payload={"poi": poi.to_dict(), "changes": changes},
        )


@dataclass
class POIDeletedEvent(DomainEvent):
    event_type: EventType = EventType.POI_DELETED
    aggregate_type: str = "POI"

    @classmethod
    def create(cls, poi: POI, correlation_id: UUID | None = None) -> "POIDeletedEvent":
        return cls(
            aggregate_id=poi.id,
            correlation_id=correlation_id,
            payload={"poi_id": str(poi.id), "name": poi.name},
        )


@dataclass
class POIVerifiedEvent(DomainEvent):
    event_type: EventType = EventType.POI_VERIFIED
    aggregate_type: str = "POI"

    @classmethod
    def create(cls, poi: POI, verified_by: UUID, correlation_id: UUID | None = None) -> "POIVerifiedEvent":
        return cls(
            aggregate_id=poi.id,
            user_id=verified_by,
            correlation_id=correlation_id,
            payload={"poi_id": str(poi.id), "verified_by": str(verified_by)},
        )


@dataclass
class POIRatingUpdatedEvent(DomainEvent):
    event_type: EventType = EventType.POI_RATING_UPDATED
    aggregate_type: str = "POI"

    @classmethod
    def create(cls, poi: POI, old_rating: float | None, new_rating: float, review_count: int, correlation_id: UUID | None = None) -> "POIRatingUpdatedEvent":
        return cls(
            aggregate_id=poi.id,
            correlation_id=correlation_id,
            payload={"poi_id": str(poi.id), "old_rating": old_rating, "new_rating": new_rating, "review_count": review_count},
        )


@dataclass
class POIPhotoAddedEvent(DomainEvent):
    event_type: EventType = EventType.POI_PHOTO_ADDED
    aggregate_type: str = "POI"

    @classmethod
    def create(cls, poi: POI, photo_url: str, uploaded_by: UUID, correlation_id: UUID | None = None) -> "POIPhotoAddedEvent":
        return cls(
            aggregate_id=poi.id,
            user_id=uploaded_by,
            correlation_id=correlation_id,
            payload={"poi_id": str(poi.id), "photo_url": photo_url, "uploaded_by": str(uploaded_by)},
        )


@dataclass
class POIFavoritedEvent(DomainEvent):
    event_type: EventType = EventType.POI_FAVORITED
    aggregate_type: str = "POI"

    @classmethod
    def create(cls, poi: POI, user_id: UUID, correlation_id: UUID | None = None) -> "POIFavoritedEvent":
        return cls(
            aggregate_id=poi.id,
            user_id=user_id,
            correlation_id=correlation_id,
            payload={"poi_id": str(poi.id), "user_id": str(user_id)},
        )


@dataclass
class POIUnfavoritedEvent(DomainEvent):
    event_type: EventType = EventType.POI_UNFAVORITED
    aggregate_type: str = "POI"

    @classmethod
    def create(cls, poi: POI, user_id: UUID, correlation_id: UUID | None = None) -> "POIUnfavoritedEvent":
        return cls(
            aggregate_id=poi.id,
            user_id=user_id,
            correlation_id=correlation_id,
            payload={"poi_id": str(poi.id), "user_id": str(user_id)},
        )


# Conversation Events
@dataclass
class ConversationStartedEvent(DomainEvent):
    event_type: EventType = EventType.CONVERSATION_STARTED
    aggregate_type: str = "Conversation"

    @classmethod
    def create(cls, conversation: Conversation, correlation_id: UUID | None = None) -> "ConversationStartedEvent":
        return cls(
            aggregate_id=conversation.id,
            user_id=conversation.user_id,
            correlation_id=correlation_id,
            payload=conversation.to_dict(),
        )


@dataclass
class ConversationMessageAddedEvent(DomainEvent):
    event_type: EventType = EventType.CONVERSATION_MESSAGE_ADDED
    aggregate_type: str = "Conversation"

    @classmethod
    def create(cls, conversation: Conversation, message: Message, correlation_id: UUID | None = None) -> "ConversationMessageAddedEvent":
        return cls(
            aggregate_id=conversation.id,
            user_id=conversation.user_id,
            correlation_id=correlation_id,
            payload={"conversation_id": str(conversation.id), "message": message.to_dict()},
        )


@dataclass
class ConversationUpdatedEvent(DomainEvent):
    event_type: EventType = EventType.CONVERSATION_UPDATED
    aggregate_type: str = "Conversation"

    @classmethod
    def create(cls, conversation: Conversation, changes: dict[str, Any], correlation_id: UUID | None = None) -> "ConversationUpdatedEvent":
        return cls(
            aggregate_id=conversation.id,
            user_id=conversation.user_id,
            correlation_id=correlation_id,
            payload={"conversation": conversation.to_dict(), "changes": changes},
        )


@dataclass
class ConversationArchivedEvent(DomainEvent):
    event_type: EventType = EventType.CONVERSATION_ARCHIVED
    aggregate_type: str = "Conversation"

    @classmethod
    def create(cls, conversation: Conversation, correlation_id: UUID | None = None) -> "ConversationArchivedEvent":
        return cls(
            aggregate_id=conversation.id,
            user_id=conversation.user_id,
            correlation_id=correlation_id,
            payload={"conversation_id": str(conversation.id)},
        )


@dataclass
class ConversationDeletedEvent(DomainEvent):
    event_type: EventType = EventType.CONVERSATION_DELETED
    aggregate_type: str = "Conversation"

    @classmethod
    def create(cls, conversation: Conversation, correlation_id: UUID | None = None) -> "ConversationDeletedEvent":
        return cls(
            aggregate_id=conversation.id,
            user_id=conversation.user_id,
            correlation_id=correlation_id,
            payload={"conversation_id": str(conversation.id)},
        )


@dataclass
class ConversationSummaryGeneratedEvent(DomainEvent):
    event_type: EventType = EventType.CONVERSATION_SUMMARY_GENERATED
    aggregate_type: str = "Conversation"

    @classmethod
    def create(cls, conversation: Conversation, summary: str, correlation_id: UUID | None = None) -> "ConversationSummaryGeneratedEvent":
        return cls(
            aggregate_id=conversation.id,
            user_id=conversation.user_id,
            correlation_id=correlation_id,
            payload={"conversation_id": str(conversation.id), "summary": summary},
        )


# Itinerary Events
@dataclass
class ItineraryCreatedEvent(DomainEvent):
    event_type: EventType = EventType.ITINERARY_CREATED
    aggregate_type: str = "Itinerary"

    @classmethod
    def create(cls, itinerary: Itinerary, correlation_id: UUID | None = None) -> "ItineraryCreatedEvent":
        return cls(
            aggregate_id=itinerary.id,
            user_id=itinerary.user_id,
            correlation_id=correlation_id,
            payload=itinerary.to_dict(),
        )


@dataclass
class ItineraryUpdatedEvent(DomainEvent):
    event_type: EventType = EventType.ITINERARY_UPDATED
    aggregate_type: str = "Itinerary"

    @classmethod
    def create(cls, itinerary: Itinerary, changes: dict[str, Any], correlation_id: UUID | None = None) -> "ItineraryUpdatedEvent":
        return cls(
            aggregate_id=itinerary.id,
            user_id=itinerary.user_id,
            correlation_id=correlation_id,
            payload={"itinerary": itinerary.to_dict(), "changes": changes},
        )


@dataclass
class ItineraryDeletedEvent(DomainEvent):
    event_type: EventType = EventType.ITINERARY_DELETED
    aggregate_type: str = "Itinerary"

    @classmethod
    def create(cls, itinerary: Itinerary, correlation_id: UUID | None = None) -> "ItineraryDeletedEvent":
        return cls(
            aggregate_id=itinerary.id,
            user_id=itinerary.user_id,
            correlation_id=correlation_id,
            payload={"itinerary_id": str(itinerary.id), "title": itinerary.title},
        )


@dataclass
class ItineraryDayAddedEvent(DomainEvent):
    event_type: EventType = EventType.ITINERARY_DAY_ADDED
    aggregate_type: str = "Itinerary"

    @classmethod
    def create(cls, itinerary: Itinerary, day_id: UUID, date: datetime, correlation_id: UUID | None = None) -> "ItineraryDayAddedEvent":
        return cls(
            aggregate_id=itinerary.id,
            user_id=itinerary.user_id,
            correlation_id=correlation_id,
            payload={"itinerary_id": str(itinerary.id), "day_id": str(day_id), "date": date.isoformat()},
        )


@dataclass
class ItineraryItemAddedEvent(DomainEvent):
    event_type: EventType = EventType.ITINERARY_ITEM_ADDED
    aggregate_type: str = "Itinerary"

    @classmethod
    def create(cls, itinerary: Itinerary, day_id: UUID, item_id: UUID, item_type: str, correlation_id: UUID | None = None) -> "ItineraryItemAddedEvent":
        return cls(
            aggregate_id=itinerary.id,
            user_id=itinerary.user_id,
            correlation_id=correlation_id,
            payload={"itinerary_id": str(itinerary.id), "day_id": str(day_id), "item_id": str(item_id), "item_type": item_type},
        )


@dataclass
class ItineraryItemRemovedEvent(DomainEvent):
    event_type: EventType = EventType.ITINERARY_ITEM_REMOVED
    aggregate_type: str = "Itinerary"

    @classmethod
    def create(cls, itinerary: Itinerary, day_id: UUID, item_id: UUID, correlation_id: UUID | None = None) -> "ItineraryItemRemovedEvent":
        return cls(
            aggregate_id=itinerary.id,
            user_id=itinerary.user_id,
            correlation_id=correlation_id,
            payload={"itinerary_id": str(itinerary.id), "day_id": str(day_id), "item_id": str(item_id)},
        )


@dataclass
class ItineraryActivatedEvent(DomainEvent):
    event_type: EventType = EventType.ITINERARY_ACTIVATED
    aggregate_type: str = "Itinerary"

    @classmethod
    def create(cls, itinerary: Itinerary, correlation_id: UUID | None = None) -> "ItineraryActivatedEvent":
        return cls(
            aggregate_id=itinerary.id,
            user_id=itinerary.user_id,
            correlation_id=correlation_id,
            payload={"itinerary_id": str(itinerary.id)},
        )


@dataclass
class ItineraryCompletedEvent(DomainEvent):
    event_type: EventType = EventType.ITINERARY_COMPLETED
    aggregate_type: str = "Itinerary"

    @classmethod
    def create(cls, itinerary: Itinerary, correlation_id: UUID | None = None) -> "ItineraryCompletedEvent":
        return cls(
            aggregate_id=itinerary.id,
            user_id=itinerary.user_id,
            correlation_id=correlation_id,
            payload={"itinerary_id": str(itinerary.id)},
        )


@dataclass
class ItinerarySharedEvent(DomainEvent):
    event_type: EventType = EventType.ITINERARY_SHARED
    aggregate_type: str = "Itinerary"

    @classmethod
    def create(cls, itinerary: Itinerary, share_token: str, correlation_id: UUID | None = None) -> "ItinerarySharedEvent":
        return cls(
            aggregate_id=itinerary.id,
            user_id=itinerary.user_id,
            correlation_id=correlation_id,
            payload={"itinerary_id": str(itinerary.id), "share_token": share_token},
        )


@dataclass
class ItineraryGeneratedByAIEvent(DomainEvent):
    event_type: EventType = EventType.ITINERARY_GENERATED_BY_AI
    aggregate_type: str = "Itinerary"

    @classmethod
    def create(cls, itinerary: Itinerary, prompt: str, model: str, tokens: int, correlation_id: UUID | None = None) -> "ItineraryGeneratedByAIEvent":
        return cls(
            aggregate_id=itinerary.id,
            user_id=itinerary.user_id,
            correlation_id=correlation_id,
            payload={"itinerary_id": str(itinerary.id), "prompt": prompt, "model": model, "tokens": tokens},
        )


# Transit Events
@dataclass
class TransitRouteCalculatedEvent(DomainEvent):
    event_type: EventType = EventType.TRANSIT_ROUTE_CALCULATED
    aggregate_type: str = "TransitRoute"

    @classmethod
    def create(cls, route: TransitRoute, user_id: UUID | None, correlation_id: UUID | None = None) -> "TransitRouteCalculatedEvent":
        return cls(
            aggregate_id=route.id,
            user_id=user_id,
            correlation_id=correlation_id,
            payload=route.to_dict(),
        )


@dataclass
class TransitRealtimeUpdatedEvent(DomainEvent):
    event_type: EventType = EventType.TRANSIT_REALTIME_UPDATED
    aggregate_type: str = "TransitRoute"

    @classmethod
    def create(cls, route_id: UUID, updates: dict[str, Any], correlation_id: UUID | None = None) -> "TransitRealtimeUpdatedEvent":
        return cls(
            aggregate_id=route_id,
            correlation_id=correlation_id,
            payload={"route_id": str(route_id), "updates": updates},
        )


@dataclass
class TransitAlertCreatedEvent(DomainEvent):
    event_type: EventType = EventType.TRANSIT_ALERT_CREATED
    aggregate_type: str = "TransitAlert"

    @classmethod
    def create(cls, alert_id: UUID, route_id: UUID | None, message: str, severity: str, correlation_id: UUID | None = None) -> "TransitAlertCreatedEvent":
        return cls(
            aggregate_id=alert_id,
            correlation_id=correlation_id,
            payload={"alert_id": str(alert_id), "route_id": str(route_id) if route_id else None, "message": message, "severity": severity},
        )


# Weather Events

@dataclass
class TransitRouteCreatedEvent(DomainEvent):
    @property
    def route_id(self) -> str:
        return self.aggregate_id
    
    @property
    def name(self) -> str:
        return self.payload.get("name", "")
    event_type: EventType = EventType.TRANSIT_ROUTE_CREATED
    aggregate_type: str = "TransitRoute"

    @classmethod
    def create(cls, route_id: str, name: str, short_name: str, description: str, transport_mode: str, color: str, text_color: str, correlation_id: UUID | None = None) -> "TransitRouteCreatedEvent":
        return cls(
            aggregate_id=route_id,
            correlation_id=correlation_id,
            payload={"route_id": route_id, "name": name, "short_name": short_name, "description": description, "transport_mode": transport_mode, "color": color, "text_color": text_color},
        )

@dataclass
class TransitStopAddedEvent(DomainEvent):
    @property
    def stop_id(self) -> str:
        return self.aggregate_id
    
    @property
    def route_id(self) -> str:
        return self.payload.get("route_id", "")
    
    @property
    def name(self) -> str:
        return self.payload.get("name", "")
    event_type: EventType = EventType.TRANSIT_STOP_ADDED
    aggregate_type: str = "TransitStop"

    @classmethod
    def create(cls, route_id: str, stop_id: str, name: str, coordinates: Coordinates, stop_order: int, is_accessible: bool, correlation_id: UUID | None = None) -> "TransitStopAddedEvent":
        return cls(
            aggregate_id=stop_id,
            correlation_id=correlation_id,
            payload={"route_id": route_id, "stop_id": stop_id, "name": name, "coordinates": coordinates.to_dict(), "stop_order": stop_order, "is_accessible": is_accessible},
        )

@dataclass
class TransitTripPlannedEvent(DomainEvent):
    @property
    def origin_stop_id(self) -> str:
        return self.payload.get("origin_stop_id", "")
    
    @property
    def destination_stop_id(self) -> str:
        return self.payload.get("destination_stop_id", "")
    event_type: EventType = EventType.TRANSIT_TRIP_PLANNED
    aggregate_type: str = "TransitTrip"

    @classmethod
    def create(cls, route_id: str, origin_stop_id: str, destination_stop_id: str, departure_time: time, arrival_time: time, intermediate_stops: list[str], correlation_id: UUID | None = None) -> "TransitTripPlannedEvent":
        return cls(
            aggregate_id=route_id,
            correlation_id=correlation_id,
            payload={"route_id": route_id, "origin_stop_id": origin_stop_id, "destination_stop_id": destination_stop_id, "departure_time": departure_time.isoformat(), "arrival_time": arrival_time.isoformat(), "intermediate_stops": intermediate_stops},
        )

@dataclass
class TransitVehiclePositionUpdatedEvent(DomainEvent):
    @property
    def vehicle_id(self) -> str:
        return self.aggregate_id
    
    @property
    def route_id(self) -> str:
        return self.payload.get("route_id", "")
    event_type: EventType = EventType.TRANSIT_VEHICLE_POSITION_UPDATED
    aggregate_type: str = "TransitVehicle"

    @classmethod
    def create(cls, route_id: str, vehicle_id: str, position: Coordinates, current_stop_id: str, next_stop_id: str, occupancy: float, timestamp: datetime, correlation_id: UUID | None = None) -> "TransitVehiclePositionUpdatedEvent":
        return cls(
            aggregate_id=vehicle_id,
            correlation_id=correlation_id,
            payload={"route_id": route_id, "vehicle_id": vehicle_id, "position": position.to_dict(), "current_stop_id": current_stop_id, "next_stop_id": next_stop_id, "occupancy": occupancy, "timestamp": timestamp.isoformat()},
        )

@dataclass
class TransitServiceAlertCreatedEvent(DomainEvent):
    @property
    def alert_id(self) -> str:
        return self.aggregate_id
    
    @property
    def route_id(self) -> str:
        return self.payload.get("route_id", "")
    event_type: EventType = EventType.TRANSIT_SERVICE_ALERT_CREATED
    aggregate_type: str = "TransitAlert"

    @classmethod
    def create(cls, route_id: str, alert_id: str, cause: str, effect: str, severity: str, description: str, affected_routes: list[str], active_period_start: datetime, active_period_end: datetime, correlation_id: UUID | None = None) -> "TransitServiceAlertCreatedEvent":
        return cls(
            aggregate_id=alert_id,
            correlation_id=correlation_id,
            payload={"route_id": route_id, "alert_id": alert_id, "cause": cause, "effect": effect, "severity": severity, "description": description, "affected_routes": affected_routes, "active_period_start": active_period_start.isoformat(), "active_period_end": active_period_end.isoformat()},
        )

@dataclass
class WeatherFetchedEvent(DomainEvent):
    event_type: EventType = EventType.WEATHER_FETCHED
    aggregate_type: str = "WeatherForecast"

    @classmethod
    def create(cls, forecast: WeatherForecast, user_id: UUID | None, correlation_id: UUID | None = None) -> "WeatherFetchedEvent":
        return cls(
            aggregate_id=uuid4(),  # Weather forecasts don't have persistent IDs
            user_id=user_id,
            correlation_id=correlation_id,
            payload={"coordinates": forecast.coordinates.to_dict(), "location_name": forecast.location_name, "source": forecast.source},
        )


@dataclass
class WeatherAlertIssuedEvent(DomainEvent):
    event_type: EventType = EventType.WEATHER_ALERT_ISSUED
    aggregate_type: str = "WeatherAlert"

    @classmethod
    def create(cls, alert_id: str, coordinates: Coordinates, severity: str, event: str, correlation_id: UUID | None = None) -> "WeatherAlertIssuedEvent":
        return cls(
            aggregate_id=uuid4(),
            correlation_id=correlation_id,
            payload={"alert_id": alert_id, "coordinates": coordinates.to_dict(), "severity": severity, "event": event},
        )


# Media Events
@dataclass
class MediaUploadedEvent(DomainEvent):
    event_type: EventType = EventType.MEDIA_UPLOADED
    aggregate_type: str = "Media"

    @classmethod
    def create(cls, media: Media, correlation_id: UUID | None = None) -> "MediaUploadedEvent":
        return cls(
            aggregate_id=media.id,
            user_id=media.user_id,
            correlation_id=correlation_id,
            payload=media.to_dict(),
        )


@dataclass
class MediaProcessedEvent(DomainEvent):
    event_type: EventType = EventType.MEDIA_PROCESSED
    aggregate_type: str = "Media"

    @classmethod
    def create(cls, media: Media, correlation_id: UUID | None = None) -> "MediaProcessedEvent":
        return cls(
            aggregate_id=media.id,
            user_id=media.user_id,
            correlation_id=correlation_id,
            payload={"media_id": str(media.id), "status": media.status.value, "variants": len(media.variants)},
        )


@dataclass
class MediaDeletedEvent(DomainEvent):
    event_type: EventType = EventType.MEDIA_DELETED
    aggregate_type: str = "Media"

    @classmethod
    def create(cls, media: Media, correlation_id: UUID | None = None) -> "MediaDeletedEvent":
        return cls(
            aggregate_id=media.id,
            user_id=media.user_id,
            correlation_id=correlation_id,
            payload={"media_id": str(media.id), "filename": media.filename},
        )


@dataclass
class MediaModeratedEvent(DomainEvent):
    event_type: EventType = EventType.MEDIA_MODERATED
    aggregate_type: str = "Media"

    @classmethod
    def create(cls, media: Media, moderator_id: UUID, approved: bool, notes: str | None = None, correlation_id: UUID | None = None) -> "MediaModeratedEvent":
        return cls(
            aggregate_id=media.id,
            user_id=moderator_id,
            correlation_id=correlation_id,
            payload={"media_id": str(media.id), "approved": approved, "notes": notes},
        )


# Feedback Events
@dataclass
class FeedbackSubmittedEvent(DomainEvent):
    event_type: EventType = EventType.FEEDBACK_SUBMITTED
    aggregate_type: str = "Feedback"

    @classmethod
    def create(cls, feedback: Feedback, correlation_id: UUID | None = None) -> "FeedbackSubmittedEvent":
        return cls(
            aggregate_id=feedback.id,
            user_id=feedback.user_id,
            correlation_id=correlation_id,
            payload=feedback.to_dict(),
        )


@dataclass
class FeedbackModeratedEvent(DomainEvent):
    event_type: EventType = EventType.FEEDBACK_MODERATED
    aggregate_type: str = "Feedback"

    @classmethod
    def create(cls, feedback: Feedback, moderator_id: UUID, action: str, notes: str | None = None, correlation_id: UUID | None = None) -> "FeedbackModeratedEvent":
        return cls(
            aggregate_id=feedback.id,
            user_id=moderator_id,
            correlation_id=correlation_id,
            payload={"feedback_id": str(feedback.id), "action": action, "notes": notes},
        )


@dataclass
class FeedbackRespondedEvent(DomainEvent):
    event_type: EventType = EventType.FEEDBACK_RESPONDED
    aggregate_type: str = "Feedback"

    @classmethod
    def create(cls, feedback: Feedback, responder_id: UUID, response: str, correlation_id: UUID | None = None) -> "FeedbackRespondedEvent":
        return cls(
            aggregate_id=feedback.id,
            user_id=responder_id,
            correlation_id=correlation_id,
            payload={"feedback_id": str(feedback.id), "response": response},
        )


# Recommendation Events
@dataclass
class RecommendationGeneratedEvent(DomainEvent):
    event_type: EventType = EventType.RECOMMENDATION_GENERATED
    aggregate_type: str = "Recommendation"

    @classmethod
    def create(cls, user_id: UUID, recommendation_id: UUID, rec_type: str, algorithm: str, items: List[dict[str, Any]], correlation_id: UUID | None = None) -> "RecommendationGeneratedEvent":
        return cls(
            aggregate_id=recommendation_id,
            user_id=user_id,
            correlation_id=correlation_id,
            payload={"recommendation_id": str(recommendation_id), "type": rec_type, "algorithm": algorithm, "items": items},
        )



@dataclass
class RecommendationSavedEvent(DomainEvent):
    event_type: EventType = EventType.RECOMMENDATION_SAVED
    aggregate_type: str = "Recommendation"

    @classmethod
    def create(cls, user_id: UUID, recommendation_id: UUID, rec_type: str, algorithm: str, items: List[dict[str, Any]], saved_at: datetime | None = None, correlation_id: UUID | None = None) -> "RecommendationSavedEvent":
        return cls(
            aggregate_id=recommendation_id,
            user_id=user_id,
            correlation_id=correlation_id,
            payload={"recommendation_id": str(recommendation_id), "type": rec_type, "algorithm": algorithm, "items": items, "saved_at": saved_at.isoformat() if saved_at else datetime.utcnow().isoformat()},
        )

@dataclass
class RecommendationClickedEvent(DomainEvent):
    event_type: EventType = EventType.RECOMMENDATION_CLICKED
    aggregate_type: str = "Recommendation"

    @classmethod
    def create(cls, user_id: UUID, recommendation_id: UUID, item_id: UUID, item_type: str, position: int, correlation_id: UUID | None = None) -> "RecommendationClickedEvent":
        return cls(
            aggregate_id=recommendation_id,
            user_id=user_id,
            correlation_id=correlation_id,
            payload={"recommendation_id": str(recommendation_id), "item_id": str(item_id), "item_type": item_type, "position": position},
        )


@dataclass
class RecommendationDismissedEvent(DomainEvent):
    event_type: EventType = EventType.RECOMMENDATION_DISMISSED
    aggregate_type: str = "Recommendation"

    @classmethod
    def create(cls, user_id: UUID, recommendation_id: UUID, item_id: UUID, item_type: str, correlation_id: UUID | None = None) -> "RecommendationDismissedEvent":
        return cls(
            aggregate_id=recommendation_id,
            user_id=user_id,
            correlation_id=correlation_id,
            payload={"recommendation_id": str(recommendation_id), "item_id": str(item_id), "item_type": item_type},
        )


@dataclass
class RecommendationFeedbackEvent(DomainEvent):
    event_type: EventType = EventType.RECOMMENDATION_FEEDBACK
    aggregate_type: str = "Recommendation"

    @classmethod
    def create(cls, user_id: UUID, recommendation_id: UUID, item_id: UUID, rating: int, action: str, correlation_id: UUID | None = None) -> "RecommendationFeedbackEvent":
        return cls(
            aggregate_id=recommendation_id,
            user_id=user_id,
            correlation_id=correlation_id,
            payload={"recommendation_id": str(recommendation_id), "item_id": str(item_id), "rating": rating, "action": action},
        )


# Search Events
@dataclass
class SearchPerformedEvent(DomainEvent):
    event_type: EventType = EventType.SEARCH_PERFORMED
    aggregate_type: str = "Search"

    @classmethod
    def create(cls, user_id: UUID | None, query: str, filters: dict[str, Any], results_count: int, correlation_id: UUID | None = None) -> "SearchPerformedEvent":
        return cls(
            aggregate_id=uuid4(),
            user_id=user_id,
            correlation_id=correlation_id,
            payload={"query": query, "filters": filters, "results_count": results_count},
        )


# Analytics Events
@dataclass
class AnalyticsEventRecordedEvent(DomainEvent):
    event_type: EventType = EventType.ANALYTICS_EVENT_RECORDED
    aggregate_type: str = "AnalyticsEvent"

    @classmethod
    def create(cls, event_type: str, user_id: UUID | None, properties: dict[str, Any], correlation_id: UUID | None = None) -> "AnalyticsEventRecordedEvent":
        return cls(
            aggregate_id=uuid4(),
            user_id=user_id,
            correlation_id=correlation_id,
            payload={"event_type": event_type, "properties": properties},
        )

# User Events (for UserAggregate compatibility)
@dataclass
class UserRegistered(DomainEvent):
    event_type: EventType = EventType.USER_CREATED
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user_id: UUID, email: str, firebase_uid: str | None = None, google_id: str | None = None, timestamp: datetime | None = None) -> "UserRegistered":
        return cls(
            aggregate_id=user_id,
            user_id=user_id,
            payload={"email": email, "firebase_uid": firebase_uid, "google_id": google_id},
            timestamp=timestamp or datetime.utcnow(),
        )


@dataclass
class UserProfileUpdated(DomainEvent):
    event_type: EventType = EventType.USER_UPDATED
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user_id: UUID, old_values: dict[str, Any], new_values: dict[str, Any], timestamp: datetime | None = None) -> "UserProfileUpdated":
        return cls(
            aggregate_id=user_id,
            user_id=user_id,
            payload={"old_values": old_values, "new_values": new_values},
            timestamp=timestamp or datetime.utcnow(),
        )


@dataclass
class UserEmailVerified(DomainEvent):
    event_type: EventType = EventType.USER_EMAIL_VERIFIED
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user_id: UUID, timestamp: datetime | None = None) -> "UserEmailVerified":
        return cls(
            aggregate_id=user_id,
            user_id=user_id,
            payload={},
            timestamp=timestamp or datetime.utcnow(),
        )


@dataclass
class UserRoleChanged(DomainEvent):
    event_type: EventType = EventType.USER_UPDATED
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user_id: UUID, old_role: str, new_role: str, timestamp: datetime | None = None) -> "UserRoleChanged":
        return cls(
            aggregate_id=user_id,
            user_id=user_id,
            payload={"old_role": old_role, "new_role": new_role},
            timestamp=timestamp or datetime.utcnow(),
        )


@dataclass
class UserStatusChanged(DomainEvent):
    event_type: EventType = EventType.USER_UPDATED
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user_id: UUID, old_status: str, new_status: str, reason: str = "", timestamp: datetime | None = None) -> "UserStatusChanged":
        return cls(
            aggregate_id=user_id,
            user_id=user_id,
            payload={"old_status": old_status, "new_status": new_status, "reason": reason},
            timestamp=timestamp or datetime.utcnow(),
        )


@dataclass
class UserLoggedIn(DomainEvent):
    event_type: EventType = EventType.USER_LOGGED_IN
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user_id: UUID, timestamp: datetime | None = None) -> "UserLoggedIn":
        return cls(
            aggregate_id=user_id,
            user_id=user_id,
            payload={},
            timestamp=timestamp or datetime.utcnow(),
        )


@dataclass
class UserDeactivated(DomainEvent):
    event_type: EventType = EventType.USER_DELETED
    aggregate_type: str = "User"

    @classmethod
    def create(cls, user_id: UUID, reason: str = "", timestamp: datetime | None = None) -> "UserDeactivated":
        return cls(
            aggregate_id=user_id,
            user_id=user_id,
            payload={"reason": reason},
            timestamp=timestamp or datetime.utcnow(),
        )

# Event Publisher Interface
from abc import ABC, abstractmethod


class EventPublisher(ABC):
    """Abstract event publisher"""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event"""
        pass

    @abstractmethod
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple domain events"""
        pass


class EventBus:
    """In-memory event bus for domain events"""

    def __init__(self):
        self._handlers: dict[EventType, list[callable]] = {}
        self._global_handlers: list[callable] = []

    def subscribe(self, event_type: EventType, handler: callable) -> None:
        """Subscribe to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: callable) -> None:
        """Subscribe to all events"""
        self._global_handlers.append(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Publish event to handlers"""
        # Call specific handlers
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if callable(handler):
                    await handler(event) if hasattr(handler, '__await__') else handler(event)
            except Exception:
                # Log error but don't fail
                pass

        # Call global handlers
        for handler in self._global_handlers:
            try:
                if callable(handler):
                    await handler(event) if hasattr(handler, '__await__') else handler(event)
            except Exception:
                pass

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple events"""
        for event in events:
            await self.publish(event)


# Global event bus instance
event_bus = EventBus()



