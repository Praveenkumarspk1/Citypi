"""
Response DTOs
"""
from dataclasses import dataclass
from typing import Any, TypeVar

from ...domain.entities.analytics import AnalyticsEvent, DailyMetrics, UserMetrics
from ...domain.entities.conversation import Conversation, Message
from ...domain.entities.feedback import Feedback
from ...domain.entities.itinerary import Itinerary, ItineraryDay, ItineraryItem
from ...domain.entities.media import Media, MediaMetadata, MediaVariant
from ...domain.entities.poi import POI
from ...domain.entities.transit import TransitLeg, TransitRoute
from ...domain.entities.user import User
from ...domain.entities.weather import (
    WeatherAlert,
    WeatherCurrent,
    WeatherDaily,
    WeatherForecast,
    WeatherHourly,
)

T = TypeVar('T')


@dataclass
class PaginatedResponse[T]:
    """Generic paginated response"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


@dataclass
class ErrorResponse:
    """Error response"""
    error: str
    message: str
    details: dict[str, Any] | None = None
    code: str | None = None


@dataclass
class SuccessResponse:
    """Success response"""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Any | None = None


# User Responses
@dataclass
class UserResponse:
    id: str
    email: str
    email_verified: bool
    display_name: str | None
    avatar_url: str | None
    locale: str
    timezone: str
    role: str
    status: str
    last_login_at: str | None
    created_at: str
    updated_at: str
    deleted_at: str | None
    preferences: dict[str, Any]

    @classmethod
    def from_entity(cls, user: User) -> "UserResponse":
        return cls(
            id=str(user.id),
            email=user.email,
            email_verified=user.email_verified,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            locale=user.locale,
            timezone=user.timezone,
            role=user.role.value,
            status=user.status.value,
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
            deleted_at=user.deleted_at.isoformat() if user.deleted_at else None,
            preferences={
                "interests": user.interests,
                "budget_level": user.budget_level,
                "accessibility_needs": user.accessibility_needs,
                "dietary_restrictions": user.dietary_restrictions,
                "preferred_transport_modes": user.preferred_transport_modes,
            }
        )


@dataclass
class TokenResponse:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes


@dataclass
class LoginResponse:
    user: UserResponse
    tokens: TokenResponse


# POI Responses
@dataclass
class ContactInfoResponse:
    phone: str | None
    email: str | None
    website: str | None
    facebook: str | None
    instagram: str | None
    twitter: str | None


@dataclass
class OpeningHoursResponse:
    monday: str | None
    tuesday: str | None
    wednesday: str | None
    thursday: str | None
    friday: str | None
    saturday: str | None
    sunday: str | None
    holidays: str | None


@dataclass
class POIResponse:
    id: str
    external_id: str | None
    source: str
    name: str
    name_local: str | None
    description: str | None
    category: str
    subcategory: str | None
    tags: list[str]
    coordinates: dict[str, float]
    address: str | None
    city: str | None
    state: str | None
    country: str | None
    postal_code: str | None
    neighborhood: str | None
    contact: ContactInfoResponse
    opening_hours: OpeningHoursResponse | None
    wheelchair_accessible: bool | None
    wifi_available: bool | None
    outdoor_seating: bool | None
    takeaway: bool | None
    delivery: bool | None
    reservation_required: bool | None
    accepts_credit_cards: bool | None
    accepts_cash: bool | None
    price_level: int | None
    photos: list[str]
    featured_photo: str | None
    rating: float | None
    review_count: int
    user_ratings_total: int
    popularity_score: float
    visit_count: int
    last_visited_at: str | None
    created_at: str
    updated_at: str
    verified_at: str | None
    verified_by: str | None
    is_active: bool
    is_verified: bool
    embedding_id: str | None = None

    @classmethod
    def from_entity(cls, poi: POI, include_embedding: bool = False) -> "POIResponse":
        data = poi.to_dict(include_embedding=include_embedding)
        return cls(
            id=data["id"],
            external_id=data["external_id"],
            source=data["source"],
            name=data["name"],
            name_local=data["name_local"],
            description=data["description"],
            category=data["category"],
            subcategory=data["subcategory"],
            tags=data["tags"],
            coordinates=data["coordinates"],
            address=data["address"],
            city=data["city"],
            state=data["state"],
            country=data["country"],
            postal_code=data["postal_code"],
            neighborhood=data["neighborhood"],
            contact=ContactInfoResponse(**data["contact"]),
            opening_hours=OpeningHoursResponse(**data["opening_hours"]) if data["opening_hours"] else None,
            wheelchair_accessible=data["wheelchair_accessible"],
            wifi_available=data["wifi_available"],
            outdoor_seating=data["outdoor_seating"],
            takeaway=data["takeaway"],
            delivery=data["delivery"],
            reservation_required=data["reservation_required"],
            accepts_credit_cards=data["accepts_credit_cards"],
            accepts_cash=data["accepts_cash"],
            price_level=data["price_level"],
            photos=data["photos"],
            featured_photo=data["featured_photo"],
            rating=data["rating"],
            review_count=data["review_count"],
            user_ratings_total=data["user_ratings_total"],
            popularity_score=data["popularity_score"],
            visit_count=data["visit_count"],
            last_visited_at=data["last_visited_at"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            verified_at=data["verified_at"],
            verified_by=data["verified_by"],
            is_active=data["is_active"],
            is_verified=data["is_verified"],
            embedding_id=data.get("embedding_id"),
        )


# Conversation Responses
@dataclass
class MessageResponse:
    id: str
    role: str
    type: str
    content: str
    tokens: int
    model: str | None
    processing_time_ms: int
    attachments: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    tool_call_id: str | None
    context: dict[str, Any]
    location: dict[str, float] | None
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, message: Message) -> "MessageResponse":
        return cls(
            id=str(message.id),
            role=message.role.value,
            type=message.type.value,
            content=message.content,
            tokens=message.tokens,
            model=message.model,
            processing_time_ms=message.processing_time_ms,
            attachments=message.attachments,
            tool_calls=message.tool_calls,
            tool_call_id=message.tool_call_id,
            context=message.context,
            location=message.location.to_dict() if message.location else None,
            created_at=message.created_at.isoformat(),
            updated_at=message.updated_at.isoformat(),
        )


@dataclass
class ConversationResponse:
    id: str
    user_id: str
    title: str | None
    status: str
    language: str
    location: dict[str, float] | None
    context: dict[str, Any]
    summary: str | None
    summary_updated_at: str | None
    total_tokens: int
    total_messages: int
    model_used: str | None
    created_at: str
    updated_at: str
    last_message_at: str | None
    archived_at: str | None
    messages: list[MessageResponse] | None = None

    @classmethod
    def from_entity(cls, conversation: Conversation, include_messages: bool = False) -> "ConversationResponse":
        return cls(
            id=str(conversation.id),
            user_id=str(conversation.user_id),
            title=conversation.title,
            status=conversation.status.value,
            language=conversation.language,
            location=conversation.location.to_dict() if conversation.location else None,
            context=conversation.context,
            summary=conversation.summary,
            summary_updated_at=conversation.summary_updated_at.isoformat() if conversation.summary_updated_at else None,
            total_tokens=conversation.total_tokens,
            total_messages=conversation.total_messages,
            model_used=conversation.model_used,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            archived_at=conversation.archived_at.isoformat() if conversation.archived_at else None,
            messages=[MessageResponse.from_entity(m) for m in conversation.messages] if include_messages else None,
        )


# Itinerary Responses
@dataclass
class ItineraryItemResponse:
    id: str
    type: str
    sequence: int
    poi_id: str | None
    poi: POIResponse | None
    title: str
    description: str | None
    coordinates: dict[str, float] | None
    address: str | None
    start_time: str | None
    end_time: str | None
    duration_minutes: int
    transport_mode: str | None
    transit_details: dict[str, Any]
    from_location: dict[str, float] | None
    to_location: dict[str, float] | None
    estimated_cost: float
    currency: str
    notes: str | None
    is_flexible: bool
    is_required: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, item: ItineraryItem) -> "ItineraryItemResponse":
        return cls(
            id=str(item.id),
            type=item.type.value,
            sequence=item.sequence,
            poi_id=str(item.poi_id) if item.poi_id else None,
            poi=POIResponse.from_entity(item.poi) if item.poi else None,
            title=item.title,
            description=item.description,
            coordinates=item.coordinates.to_dict() if item.coordinates else None,
            address=item.address,
            start_time=item.start_time.isoformat() if item.start_time else None,
            end_time=item.end_time.isoformat() if item.end_time else None,
            duration_minutes=item.duration_minutes,
            transport_mode=item.transport_mode.value if item.transport_mode else None,
            transit_details=item.transit_details,
            from_location=item.from_location.to_dict() if item.from_location else None,
            to_location=item.to_location.to_dict() if item.to_location else None,
            estimated_cost=item.estimated_cost,
            currency=item.currency,
            notes=item.notes,
            is_flexible=item.is_flexible,
            is_required=item.is_required,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
        )


@dataclass
class ItineraryDayResponse:
    id: str
    date: str
    sequence: int
    title: str | None
    notes: str | None
    start_time: str
    end_time: str
    base_location: dict[str, float] | None
    base_address: str | None
    items: list[ItineraryItemResponse]
    total_duration_minutes: int
    total_cost: float
    total_distance_meters: float
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, day: ItineraryDay) -> "ItineraryDayResponse":
        return cls(
            id=str(day.id),
            date=day.date.date().isoformat(),
            sequence=day.sequence,
            title=day.title,
            notes=day.notes,
            start_time=day.start_time.isoformat(),
            end_time=day.end_time.isoformat(),
            base_location=day.base_location.to_dict() if day.base_location else None,
            base_address=day.base_address,
            items=[ItineraryItemResponse.from_entity(item) for item in day.items],
            total_duration_minutes=day.total_duration_minutes,
            total_cost=day.total_cost,
            total_distance_meters=day.total_distance_meters,
            created_at=day.created_at.isoformat(),
            updated_at=day.updated_at.isoformat(),
        )


@dataclass
class ItineraryResponse:
    id: str
    user_id: str
    title: str
    description: str | None
    status: str
    start_date: str
    end_date: str
    budget_level: str
    pace: str
    interests: list[str]
    accessibility_needs: list[str]
    dietary_restrictions: list[str]
    transport_preferences: list[str]
    base_location: dict[str, float] | None
    base_address: str | None
    city: str | None
    country: str | None
    is_public: bool
    share_token: str | None
    collaborators: list[str]
    total_estimated_cost: float
    total_distance_meters: float
    poi_count: int
    tags: list[str]
    generated_by_ai: bool
    generation_prompt: str | None
    generation_model: str | None
    generation_tokens: int
    created_at: str
    updated_at: str
    published_at: str | None
    completed_at: str | None
    days: list[ItineraryDayResponse] | None = None

    @classmethod
    def from_entity(cls, itinerary: Itinerary, include_days: bool = True) -> "ItineraryResponse":
        return cls(
            id=str(itinerary.id),
            user_id=str(itinerary.user_id),
            title=itinerary.title,
            description=itinerary.description,
            status=itinerary.status.value,
            start_date=itinerary.start_date.date().isoformat(),
            end_date=itinerary.end_date.date().isoformat(),
            budget_level=itinerary.budget_level,
            pace=itinerary.pace,
            interests=itinerary.interests,
            accessibility_needs=itinerary.accessibility_needs,
            dietary_restrictions=itinerary.dietary_restrictions,
            transport_preferences=[t.value for t in itinerary.transport_preferences],
            base_location=itinerary.base_location.to_dict() if itinerary.base_location else None,
            base_address=itinerary.base_address,
            city=itinerary.city,
            country=itinerary.country,
            is_public=itinerary.is_public,
            share_token=itinerary.share_token,
            collaborators=[str(uid) for uid in itinerary.collaborators],
            total_estimated_cost=itinerary.total_estimated_cost,
            total_distance_meters=itinerary.total_distance_meters,
            poi_count=itinerary.poi_count,
            tags=itinerary.tags,
            generated_by_ai=itinerary.generated_by_ai,
            generation_prompt=itinerary.generation_prompt,
            generation_model=itinerary.generation_model,
            generation_tokens=itinerary.generation_tokens,
            created_at=itinerary.created_at.isoformat(),
            updated_at=itinerary.updated_at.isoformat(),
            published_at=itinerary.published_at.isoformat() if itinerary.published_at else None,
            completed_at=itinerary.completed_at.isoformat() if itinerary.completed_at else None,
            days=[ItineraryDayResponse.from_entity(day) for day in itinerary.days] if include_days else None,
        )


# Transit Responses
@dataclass
class TransitLegResponse:
    id: str
    sequence: int
    mode: str
    from_stop_id: str | None
    from_stop_name: str
    from_coordinates: dict[str, float]
    to_stop_id: str | None
    to_stop_name: str
    to_coordinates: dict[str, float]
    route_id: str | None
    route_short_name: str | None
    route_long_name: str | None
    route_color: str | None
    route_type: int | None
    trip_id: str | None
    trip_headsign: str | None
    departure_time: str
    arrival_time: str
    duration_minutes: int
    wait_time_minutes: int
    distance_meters: float
    shape_points: list[dict[str, float]]
    realtime_delay: int | None
    realtime_vehicle: dict[str, Any] | None
    instructions: str

    @classmethod
    def from_entity(cls, leg: TransitLeg) -> "TransitLegResponse":
        return cls(
            id=str(leg.id),
            sequence=leg.sequence,
            mode=leg.mode.value,
            from_stop_id=leg.from_stop_id,
            from_stop_name=leg.from_stop_name,
            from_coordinates=leg.from_coordinates.to_dict(),
            to_stop_id=leg.to_stop_id,
            to_stop_name=leg.to_stop_name,
            to_coordinates=leg.to_coordinates.to_dict(),
            route_id=leg.route_id,
            route_short_name=leg.route_short_name,
            route_long_name=leg.route_long_name,
            route_color=leg.route_color,
            route_type=leg.route_type.value if leg.route_type else None,
            trip_id=leg.trip_id,
            trip_headsign=leg.trip_headsign,
            departure_time=leg.departure_time.isoformat(),
            arrival_time=leg.arrival_time.isoformat(),
            duration_minutes=leg.duration_minutes,
            wait_time_minutes=leg.wait_time_minutes,
            distance_meters=leg.distance_meters,
            shape_points=[p.to_dict() for p in leg.shape_points],
            realtime_delay=leg.realtime_delay,
            realtime_vehicle=leg.realtime_vehicle.to_dict() if leg.realtime_vehicle else None,
            instructions=leg.instructions,
        )


@dataclass
class TransitRouteResponse:
    id: str
    origin: dict[str, float]
    destination: dict[str, float]
    origin_name: str
    destination_name: str
    legs: list[TransitLegResponse]
    total_duration_minutes: int
    total_distance_meters: float
    total_cost: float
    currency: str
    departure_time: str
    arrival_time: str
    transfers: int
    walking_distance_meters: float
    walking_duration_minutes: int
    fare_details: list[dict[str, Any]]
    has_realtime: bool
    realtime_updated_at: str | None

    @classmethod
    def from_entity(cls, route: TransitRoute) -> "TransitRouteResponse":
        return cls(
            id=str(route.id),
            origin=route.origin.to_dict(),
            destination=route.destination.to_dict(),
            origin_name=route.origin_name,
            destination_name=route.destination_name,
            legs=[TransitLegResponse.from_entity(leg) for leg in route.legs],
            total_duration_minutes=route.total_duration_minutes,
            total_distance_meters=route.total_distance_meters,
            total_cost=route.total_cost,
            currency=route.currency,
            departure_time=route.departure_time.isoformat(),
            arrival_time=route.arrival_time.isoformat(),
            transfers=route.transfers,
            walking_distance_meters=route.walking_distance_meters,
            walking_duration_minutes=route.walking_duration_minutes,
            fare_details=[f.to_dict() for f in route.fare_details],
            has_realtime=route.has_realtime,
            realtime_updated_at=route.realtime_updated_at.isoformat() if route.realtime_updated_at else None,
        )


# Weather Responses
@dataclass
class WeatherCurrentResponse:
    coordinates: dict[str, float]
    timestamp: str
    temperature: float
    feels_like: float
    dew_point: float
    humidity: int
    pressure: float
    wind_speed: float
    wind_direction: int
    wind_gust: float | None
    condition: str
    condition_description: str
    cloud_cover: int
    visibility: float
    precipitation: float
    precipitation_type: str
    precipitation_probability: int
    uv_index: float
    solar_radiation: float
    air_quality_index: int | None
    pm25: float | None
    pm10: float | None
    o3: float | None
    no2: float | None
    so2: float | None
    co: float | None
    source: str

    @classmethod
    def from_entity(cls, current: WeatherCurrent) -> "WeatherCurrentResponse":
        return cls(
            coordinates=current.coordinates.to_dict(),
            timestamp=current.timestamp.isoformat(),
            temperature=current.temperature,
            feels_like=current.feels_like,
            dew_point=current.dew_point,
            humidity=current.humidity,
            pressure=current.pressure,
            wind_speed=current.wind_speed,
            wind_direction=current.wind_direction,
            wind_gust=current.wind_gust,
            condition=current.condition.value,
            condition_description=current.condition_description,
            cloud_cover=current.cloud_cover,
            visibility=current.visibility,
            precipitation=current.precipitation,
            precipitation_type=current.precipitation_type.value,
            precipitation_probability=current.precipitation_probability,
            uv_index=current.uv_index,
            solar_radiation=current.solar_radiation,
            air_quality_index=current.air_quality_index,
            pm25=current.pm25,
            pm10=current.pm10,
            o3=current.o3,
            no2=current.no2,
            so2=current.so2,
            co=current.co,
            source=current.source,
        )


@dataclass
class WeatherHourlyResponse:
    timestamp: str
    temperature: float
    feels_like: float
    dew_point: float
    humidity: int
    pressure: float
    wind_speed: float
    wind_direction: int
    wind_gust: float | None
    condition: str
    condition_description: str
    cloud_cover: int
    visibility: float
    precipitation: float
    precipitation_type: str
    precipitation_probability: int
    uv_index: float

    @classmethod
    def from_entity(cls, hourly: WeatherHourly) -> "WeatherHourlyResponse":
        return cls(
            timestamp=hourly.timestamp.isoformat(),
            temperature=hourly.temperature,
            feels_like=hourly.feels_like,
            dew_point=hourly.dew_point,
            humidity=hourly.humidity,
            pressure=hourly.pressure,
            wind_speed=hourly.wind_speed,
            wind_direction=hourly.wind_direction,
            wind_gust=hourly.wind_gust,
            condition=hourly.condition.value,
            condition_description=hourly.condition_description,
            cloud_cover=hourly.cloud_cover,
            visibility=hourly.visibility,
            precipitation=hourly.precipitation,
            precipitation_type=hourly.precipitation_type.value,
            precipitation_probability=hourly.precipitation_probability,
            uv_index=hourly.uv_index,
        )


@dataclass
class WeatherDailyResponse:
    date: str
    temperature_min: float
    temperature_max: float
    temperature_morning: float
    temperature_noon: float
    temperature_evening: float
    temperature_night: float
    feels_like_min: float
    feels_like_max: float
    sunrise: str | None
    sunset: str | None
    daylight_duration: float
    sunshine_duration: float
    condition: str
    condition_description: str
    precipitation_sum: float
    precipitation_probability_max: int
    precipitation_hours: float
    precipitation_type: str
    wind_speed_max: float
    wind_gust_max: float | None
    wind_direction_dominant: int
    uv_index_max: float
    uv_index_clear_sky_max: float
    humidity_mean: int
    pressure_mean: float
    cloud_cover_mean: int
    visibility_mean: float
    hourly: list[WeatherHourlyResponse]

    @classmethod
    def from_entity(cls, daily: WeatherDaily) -> "WeatherDailyResponse":
        return cls(
            date=daily.date.isoformat(),
            temperature_min=daily.temperature_min,
            temperature_max=daily.temperature_max,
            temperature_morning=daily.temperature_morning,
            temperature_noon=daily.temperature_noon,
            temperature_evening=daily.temperature_evening,
            temperature_night=daily.temperature_night,
            feels_like_min=daily.feels_like_min,
            feels_like_max=daily.feels_like_max,
            sunrise=daily.sunrise.isoformat() if daily.sunrise else None,
            sunset=daily.sunset.isoformat() if daily.sunset else None,
            daylight_duration=daily.daylight_duration,
            sunshine_duration=daily.sunshine_duration,
            condition=daily.condition.value,
            condition_description=daily.condition_description,
            precipitation_sum=daily.precipitation_sum,
            precipitation_probability_max=daily.precipitation_probability_max,
            precipitation_hours=daily.precipitation_hours,
            precipitation_type=daily.precipitation_type.value,
            wind_speed_max=daily.wind_speed_max,
            wind_gust_max=daily.wind_gust_max,
            wind_direction_dominant=daily.wind_direction_dominant,
            uv_index_max=daily.uv_index_max,
            uv_index_clear_sky_max=daily.uv_index_clear_sky_max,
            humidity_mean=daily.humidity_mean,
            pressure_mean=daily.pressure_mean,
            cloud_cover_mean=daily.cloud_cover_mean,
            visibility_mean=daily.visibility_mean,
            hourly=[WeatherHourlyResponse.from_entity(h) for h in daily.hourly],
        )


@dataclass
class WeatherAlertResponse:
    id: str
    title: str
    description: str
    severity: str
    certainty: str
    urgency: str
    event: str
    effective: str | None
    expires: str | None
    sender: str
    areas: list[str]
    coordinates: dict[str, float] | None
    source: str
    is_active: bool

    @classmethod
    def from_entity(cls, alert: WeatherAlert) -> "WeatherAlertResponse":
        return cls(
            id=alert.id,
            title=alert.title,
            description=alert.description,
            severity=alert.severity.value,
            certainty=alert.certainty,
            urgency=alert.urgency,
            event=alert.event,
            effective=alert.effective.isoformat() if alert.effective else None,
            expires=alert.expires.isoformat() if alert.expires else None,
            sender=alert.sender,
            areas=alert.areas,
            coordinates=alert.coordinates.to_dict() if alert.coordinates else None,
            source=alert.source,
            is_active=alert.is_active(),
        )


@dataclass
class WeatherForecastResponse:
    coordinates: dict[str, float]
    location_name: str
    timezone: str
    generated_at: str
    current: WeatherCurrentResponse | None
    hourly: list[WeatherHourlyResponse]
    daily: list[WeatherDailyResponse]
    alerts: list[WeatherAlertResponse]
    source: str
    model: str
    units: str

    @classmethod
    def from_entity(cls, forecast: WeatherForecast, include_hourly: bool = True, include_daily: bool = True) -> "WeatherForecastResponse":
        return cls(
            coordinates=forecast.coordinates.to_dict(),
            location_name=forecast.location_name,
            timezone=forecast.timezone,
            generated_at=forecast.generated_at.isoformat(),
            current=WeatherCurrentResponse.from_entity(forecast.current) if forecast.current else None,
            hourly=[WeatherHourlyResponse.from_entity(h) for h in forecast.hourly] if include_hourly else [],
            daily=[WeatherDailyResponse.from_entity(d) for d in forecast.daily] if include_daily else [],
            alerts=[WeatherAlertResponse.from_entity(a) for a in forecast.alerts],
            source=forecast.source,
            model=forecast.model,
            units=forecast.units,
        )


# Media Responses
@dataclass
class MediaVariantResponse:
    id: str
    type: str
    url: str
    width: int
    height: int
    size_bytes: int
    format: str
    mime_type: str

    @classmethod
    def from_entity(cls, variant: MediaVariant) -> "MediaVariantResponse":
        return cls(
            id=str(variant.id),
            type=variant.type,
            url=variant.url,
            width=variant.width,
            height=variant.height,
            size_bytes=variant.size_bytes,
            format=variant.format,
            mime_type=variant.mime_type,
        )


@dataclass
class MediaMetadataResponse:
    camera_make: str | None
    camera_model: str | None
    lens: str | None
    focal_length: float | None
    aperture: float | None
    iso: int | None
    exposure_time: str | None
    datetime_original: str | None
    gps_coordinates: dict[str, float] | None
    dominant_colors: list[str]
    tags: list[str]
    objects_detected: list[dict[str, Any]]
    scene_classification: str | None
    nsfw_score: float | None
    duration_seconds: float | None
    bitrate: int | None
    codec: str | None
    sample_rate: int | None
    channels: int | None
    page_count: int | None
    author: str | None
    subject: str | None
    keywords: list[str]

    @classmethod
    def from_entity(cls, metadata: MediaMetadata) -> "MediaMetadataResponse":
        return cls(
            camera_make=metadata.camera_make,
            camera_model=metadata.camera_model,
            lens=metadata.lens,
            focal_length=metadata.focal_length,
            aperture=metadata.aperture,
            iso=metadata.iso,
            exposure_time=metadata.exposure_time,
            datetime_original=metadata.datetime_original.isoformat() if metadata.datetime_original else None,
            gps_coordinates=metadata.gps_coordinates.to_dict() if metadata.gps_coordinates else None,
            dominant_colors=metadata.dominant_colors,
            tags=metadata.tags,
            objects_detected=metadata.objects_detected,
            scene_classification=metadata.scene_classification,
            nsfw_score=metadata.nsfw_score,
            duration_seconds=metadata.duration_seconds,
            bitrate=metadata.bitrate,
            codec=metadata.codec,
            sample_rate=metadata.sample_rate,
            channels=metadata.channels,
            page_count=metadata.page_count,
            author=metadata.author,
            subject=metadata.subject,
            keywords=metadata.keywords,
        )


@dataclass
class MediaResponse:
    id: str
    user_id: str | None
    poi_id: str | None
    conversation_id: str | None
    itinerary_id: str | None
    filename: str
    original_filename: str
    type: str
    mime_type: str
    size_bytes: int
    width: int
    height: int
    format: str
    storage_path: str
    bucket: str
    cdn_url: str | None
    source: str
    source_url: str | None
    attribution: str | None
    license: str | None
    title: str | None
    description: str | None
    alt_text: str | None
    tags: list[str]
    coordinates: dict[str, float] | None
    address: str | None
    status: str
    error_message: str | None
    is_moderated: bool
    moderation_status: str
    moderation_notes: str | None
    moderated_at: str | None
    moderated_by: str | None
    caption: str | None
    caption_confidence: float | None
    landmarks_detected: list[dict[str, Any]]
    view_count: int
    download_count: int
    like_count: int
    created_at: str
    updated_at: str
    processed_at: str | None
    deleted_at: str | None
    variants: list[MediaVariantResponse]
    metadata: MediaMetadataResponse

    @classmethod
    def from_entity(cls, media: Media, include_variants: bool = True, include_metadata: bool = True) -> "MediaResponse":
        return cls(
            id=str(media.id),
            user_id=str(media.user_id) if media.user_id else None,
            poi_id=str(media.poi_id) if media.poi_id else None,
            conversation_id=str(media.conversation_id) if media.conversation_id else None,
            itinerary_id=str(media.itinerary_id) if media.itinerary_id else None,
            filename=media.filename,
            original_filename=media.original_filename,
            type=media.type.value,
            mime_type=media.mime_type,
            size_bytes=media.size_bytes,
            width=media.width,
            height=media.height,
            format=media.format,
            storage_path=media.storage_path,
            bucket=media.bucket,
            cdn_url=media.cdn_url,
            source=media.source.value,
            source_url=media.source_url,
            attribution=media.attribution,
            license=media.license,
            title=media.title,
            description=media.description,
            alt_text=media.alt_text,
            tags=media.tags,
            coordinates=media.coordinates.to_dict() if media.coordinates else None,
            address=media.address,
            status=media.status.value,
            error_message=media.error_message,
            is_moderated=media.is_moderated,
            moderation_status=media.moderation_status,
            moderation_notes=media.moderation_notes,
            moderated_at=media.moderated_at.isoformat() if media.moderated_at else None,
            moderated_by=str(media.moderated_by) if media.moderated_by else None,
            caption=media.caption,
            caption_confidence=media.caption_confidence,
            landmarks_detected=media.landmarks_detected,
            view_count=media.view_count,
            download_count=media.download_count,
            like_count=media.like_count,
            created_at=media.created_at.isoformat(),
            updated_at=media.updated_at.isoformat(),
            processed_at=media.processed_at.isoformat() if media.processed_at else None,
            deleted_at=media.deleted_at.isoformat() if media.deleted_at else None,
            variants=[MediaVariantResponse.from_entity(v) for v in media.variants] if include_variants else [],
            metadata=MediaMetadataResponse.from_entity(media.metadata) if include_metadata else None,
        )


# Feedback Responses
@dataclass
class FeedbackResponse:
    id: str
    user_id: str
    type: str
    target_type: str
    target_id: str
    title: str | None
    content: str
    rating: int | None
    sentiment: str | None
    sentiment_score: float | None
    categories: list[str]
    tags: list[str]
    media_ids: list[str]
    location: dict[str, Any] | None
    status: str
    is_public: bool
    is_anonymous: bool
    moderated_at: str | None
    moderated_by: str | None
    moderation_notes: str | None
    response: str | None
    responded_at: str | None
    responded_by: str | None
    helpful_count: int
    unhelpful_count: int
    helpfulness_ratio: float
    app_version: str | None
    platform: str | None
    device_info: dict[str, Any] | None
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, feedback: Feedback) -> "FeedbackResponse":
        return cls(
            id=str(feedback.id),
            user_id=str(feedback.user_id),
            type=feedback.type.value,
            target_type=feedback.target_type,
            target_id=str(feedback.target_id),
            title=feedback.title,
            content=feedback.content,
            rating=feedback.rating,
            sentiment=feedback.sentiment.value if feedback.sentiment else None,
            sentiment_score=feedback.sentiment_score,
            categories=feedback.categories,
            tags=feedback.tags,
            media_ids=[str(mid) for mid in feedback.media_ids],
            location=feedback.location,
            status=feedback.status.value,
            is_public=feedback.is_public,
            is_anonymous=feedback.is_anonymous,
            moderated_at=feedback.moderated_at.isoformat() if feedback.moderated_at else None,
            moderated_by=str(feedback.moderated_by) if feedback.moderated_by else None,
            moderation_notes=feedback.moderation_notes,
            response=feedback.response,
            responded_at=feedback.responded_at.isoformat() if feedback.responded_at else None,
            responded_by=str(feedback.responded_by) if feedback.responded_by else None,
            helpful_count=feedback.helpful_count,
            unhelpful_count=feedback.unhelpful_count,
            helpfulness_ratio=feedback.get_helpfulness_ratio(),
            app_version=feedback.app_version,
            platform=feedback.platform,
            device_info=feedback.device_info,
            created_at=feedback.created_at.isoformat(),
            updated_at=feedback.updated_at.isoformat(),
        )


# Analytics Responses
@dataclass
class AnalyticsEventResponse:
    id: str
    event_type: str
    user_id: str | None
    session_id: str | None
    properties: dict[str, Any]
    source: str
    app_version: str | None
    platform: str | None
    device_id: str | None
    coordinates: dict[str, float] | None
    city: str | None
    country: str | None
    timestamp: str
    processing_time_ms: int | None
    correlation_id: str | None
    experiment_id: str | None
    variant: str | None

    @classmethod
    def from_entity(cls, event: AnalyticsEvent) -> "AnalyticsEventResponse":
        return cls(
            id=str(event.id),
            event_type=event.event_type.value,
            user_id=str(event.user_id) if event.user_id else None,
            session_id=event.session_id,
            properties=event.properties,
            source=event.source.value,
            app_version=event.app_version,
            platform=event.platform,
            device_id=event.device_id,
            coordinates=event.coordinates,
            city=event.city,
            country=event.country,
            timestamp=event.timestamp.isoformat(),
            processing_time_ms=event.processing_time_ms,
            correlation_id=event.correlation_id,
            experiment_id=event.experiment_id,
            variant=event.variant,
        )


@dataclass
class DailyMetricsResponse:
    date: str
    total_users: int
    new_users: int
    active_users: int
    returning_users: int
    dau: int
    mau: int
    total_sessions: int
    avg_session_duration_seconds: float
    avg_pages_per_session: float
    bounce_rate: float
    conversations_started: int
    messages_sent: int
    messages_received: int
    avg_conversation_length: float
    avg_response_time_ms: float
    poi_searches: int
    poi_views: int
    poi_favorites_added: int
    poi_reviews_submitted: int
    poi_photos_uploaded: int
    itineraries_created: int
    itineraries_viewed: int
    itineraries_completed: int
    itineraries_shared: int
    avg_itinerary_days: float
    avg_pois_per_itinerary: float
    transit_searches: int
    transit_routes_viewed: int
    transit_feedback_submitted: int
    weather_views: int
    weather_alerts_viewed: int
    voice_messages: int
    image_analyses: int
    recommendations_shown: int
    recommendations_clicked: int
    recommendation_ctr: float
    searches_performed: int
    search_results_clicked: int
    zero_result_searches: int
    total_errors: int
    error_rate: float
    api_errors: int
    avg_page_load_ms: float
    avg_api_response_ms: float
    p95_api_response_ms: float
    p99_api_response_ms: float
    premium_signups: int
    premium_churn: int
    revenue: float
    calculated_at: str

    @classmethod
    def from_entity(cls, metrics: DailyMetrics) -> "DailyMetricsResponse":
        return cls(
            date=metrics.date.isoformat(),
            total_users=metrics.total_users,
            new_users=metrics.new_users,
            active_users=metrics.active_users,
            returning_users=metrics.returning_users,
            dau=metrics.dau,
            mau=metrics.mau,
            total_sessions=metrics.total_sessions,
            avg_session_duration_seconds=metrics.avg_session_duration_seconds,
            avg_pages_per_session=metrics.avg_pages_per_session,
            bounce_rate=metrics.bounce_rate,
            conversations_started=metrics.conversations_started,
            messages_sent=metrics.messages_sent,
            messages_received=metrics.messages_received,
            avg_conversation_length=metrics.avg_conversation_length,
            avg_response_time_ms=metrics.avg_response_time_ms,
            poi_searches=metrics.poi_searches,
            poi_views=metrics.poi_views,
            poi_favorites_added=metrics.poi_favorites_added,
            poi_reviews_submitted=metrics.poi_reviews_submitted,
            poi_photos_uploaded=metrics.poi_photos_uploaded,
            itineraries_created=metrics.itineraries_created,
            itineraries_viewed=metrics.itineraries_viewed,
            itineraries_completed=metrics.itineraries_completed,
            itineraries_shared=metrics.itineraries_shared,
            avg_itinerary_days=metrics.avg_itinerary_days,
            avg_pois_per_itinerary=metrics.avg_pois_per_itinerary,
            transit_searches=metrics.transit_searches,
            transit_routes_viewed=metrics.transit_routes_viewed,
            transit_feedback_submitted=metrics.transit_feedback_submitted,
            weather_views=metrics.weather_views,
            weather_alerts_viewed=metrics.weather_alerts_viewed,
            voice_messages=metrics.voice_messages,
            image_analyses=metrics.image_analyses,
            recommendations_shown=metrics.recommendations_shown,
            recommendations_clicked=metrics.recommendations_clicked,
            recommendation_ctr=metrics.recommendation_ctr,
            searches_performed=metrics.searches_performed,
            search_results_clicked=metrics.search_results_clicked,
            zero_result_searches=metrics.zero_result_searches,
            total_errors=metrics.total_errors,
            error_rate=metrics.error_rate,
            api_errors=metrics.api_errors,
            avg_page_load_ms=metrics.avg_page_load_ms,
            avg_api_response_ms=metrics.avg_api_response_ms,
            p95_api_response_ms=metrics.p95_api_response_ms,
            p99_api_response_ms=metrics.p99_api_response_ms,
            premium_signups=metrics.premium_signups,
            premium_churn=metrics.premium_churn,
            revenue=metrics.revenue,
            calculated_at=metrics.calculated_at.isoformat(),
        )


@dataclass
class UserMetricsResponse:
    user_id: str
    first_seen: str
    last_seen: str
    total_sessions: int
    total_session_duration_seconds: int
    days_active: int
    conversations_count: int
    messages_sent: int
    avg_conversation_length: float
    poi_searches: int
    poi_views: int
    favorites_count: int
    reviews_written: int
    photos_uploaded: int
    itineraries_created: int
    itineraries_completed: int
    itineraries_shared: int
    transit_searches: int
    transit_feedback_count: int
    voice_messages_sent: int
    images_analyzed: int
    recommendations_clicked: int
    recommendations_dismissed: int
    preferred_categories: list[str]
    preferred_transport_modes: list[str]
    active_hours: list[int]
    active_days: list[int]
    engagement_score: float
    churn_risk: float
    updated_at: str

    @classmethod
    def from_entity(cls, metrics: UserMetrics) -> "UserMetricsResponse":
        return cls(
            user_id=str(metrics.user_id),
            first_seen=metrics.first_seen.isoformat(),
            last_seen=metrics.last_seen.isoformat(),
            total_sessions=metrics.total_sessions,
            total_session_duration_seconds=metrics.total_session_duration_seconds,
            days_active=metrics.days_active,
            conversations_count=metrics.conversations_count,
            messages_sent=metrics.messages_sent,
            avg_conversation_length=metrics.avg_conversation_length,
            poi_searches=metrics.poi_searches,
            poi_views=metrics.poi_views,
            favorites_count=metrics.favorites_count,
            reviews_written=metrics.reviews_written,
            photos_uploaded=metrics.photos_uploaded,
            itineraries_created=metrics.itineraries_created,
            itineraries_completed=metrics.itineraries_completed,
            itineraries_shared=metrics.itineraries_shared,
            transit_searches=metrics.transit_searches,
            transit_feedback_count=metrics.transit_feedback_count,
            voice_messages_sent=metrics.voice_messages_sent,
            images_analyzed=metrics.images_analyzed,
            recommendations_clicked=metrics.recommendations_clicked,
            recommendations_dismissed=metrics.recommendations_dismissed,
            preferred_categories=metrics.preferred_categories,
            preferred_transport_modes=metrics.preferred_transport_modes,
            active_hours=metrics.active_hours,
            active_days=metrics.active_days,
            engagement_score=metrics.engagement_score,
            churn_risk=metrics.churn_risk,
            updated_at=metrics.updated_at.isoformat(),
        )


# Analytics Additional Responses
@dataclass
class CohortAnalysisResponse:
    cohort_id: str
    cohort_name: str
    cohort_size: int
    retention_rates: list[float]
    metrics: dict[str, Any]
    created_at: str


@dataclass
class FeatureUsageResponse:
    feature_name: str
    total_users: int
    active_users: int
    usage_count: int
    avg_usage_per_user: float
    adoption_rate: float
    period_start: str
    period_end: str


@dataclass
class FunnelAnalysisResponse:
    funnel_name: str
    steps: list[dict[str, Any]]
    overall_conversion_rate: float
    drop_off_points: list[dict[str, Any]]
    period_start: str
    period_end: str
