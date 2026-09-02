"""
Weather Service - Forecasts, alerts, historical weather
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any


class WeatherSource(StrEnum):
    """Weather data sources"""
    OPEN_METEO = "open_meteo"
    OPENWEATHER = "openweather"
    WEATHERAPI = "weatherapi"
    MET_NO = "met_no"
    NWS = "nws"  # National Weather Service
    CUSTOM = "custom"


class WeatherCondition(StrEnum):
    """Weather conditions"""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    LIGHT_RAIN = "light_rain"
    MODERATE_RAIN = "moderate_rain"
    HEAVY_RAIN = "heavy_rain"
    LIGHT_SNOW = "light_snow"
    MODERATE_SNOW = "moderate_snow"
    HEAVY_SNOW = "heavy_snow"
    THUNDERSTORM = "thunderstorm"
    FOG = "fog"
    MIST = "mist"
    HAZE = "haze"
    WINDY = "windy"
    EXTREME_HEAT = "extreme_heat"
    EXTREME_COLD = "extreme_cold"


class AlertSeverity(StrEnum):
    """Weather alert severity levels"""
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


class AlertType(StrEnum):
    """Weather alert types"""
    HEAT_WAVE = "heat_wave"
    COLD_WAVE = "cold_wave"
    STORM = "storm"
    HURRICANE = "hurricane"
    TORNADO = "tornado"
    FLOOD = "flood"
    HIGH_WIND = "high_wind"
    HEAVY_RAIN = "heavy_rain"
    HEAVY_SNOW = "heavy_snow"
    ICE_STORM = "ice_storm"
    FOG = "fog"
    AIR_QUALITY = "air_quality"
    UV_INDEX = "uv_index"


@dataclass(frozen=True)
class Coordinates:
    """Geographic coordinates"""
    latitude: float
    longitude: float

    def to_dict(self) -> dict:
        return {"lat": self.latitude, "lng": self.longitude}


@dataclass(frozen=True)
class CurrentWeather:
    """Current weather conditions"""
    coordinates: Coordinates
    location_name: str
    temperature: float  # Celsius
    feels_like: float
    humidity: int  # percentage
    pressure: float  # hPa
    wind_speed: float  # m/s
    wind_direction: int  # degrees
    wind_gust: float | None = None
    condition: WeatherCondition = WeatherCondition.CLEAR
    condition_description: str = ""
    visibility: float = 10000  # meters
    uv_index: float = 0.0
    cloud_cover: int = 0  # percentage
    precipitation: float = 0.0  # mm
    dew_point: float | None = None
    source: WeatherSource = WeatherSource.OPEN_METEO
    observed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "coordinates": self.coordinates.to_dict(),
            "location_name": self.location_name,
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "wind_gust": self.wind_gust,
            "condition": self.condition.value,
            "condition_description": self.condition_description,
            "visibility": self.visibility,
            "uv_index": self.uv_index,
            "cloud_cover": self.cloud_cover,
            "precipitation": self.precipitation,
            "dew_point": self.dew_point,
            "source": self.source.value,
            "observed_at": self.observed_at.isoformat(),
        }


@dataclass(frozen=True)
class HourlyForecast:
    """Hourly weather forecast"""
    time: datetime
    temperature: float
    feels_like: float
    humidity: int
    pressure: float
    wind_speed: float
    wind_direction: int
    wind_gust: float | None = None
    condition: WeatherCondition = WeatherCondition.CLEAR
    condition_description: str = ""
    precipitation_probability: int = 0
    precipitation: float = 0.0
    cloud_cover: int = 0
    uv_index: float = 0.0
    visibility: float = 10000

    def to_dict(self) -> dict:
        return {
            "time": self.time.isoformat(),
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "wind_gust": self.wind_gust,
            "condition": self.condition.value,
            "condition_description": self.condition_description,
            "precipitation_probability": self.precipitation_probability,
            "precipitation": self.precipitation,
            "cloud_cover": self.cloud_cover,
            "uv_index": self.uv_index,
            "visibility": self.visibility,
        }


@dataclass(frozen=True)
class DailyForecast:
    """Daily weather forecast"""
    date: datetime
    temperature_min: float
    temperature_max: float
    feels_like_min: float
    feels_like_max: float
    humidity_avg: int
    pressure_avg: float
    wind_speed_max: float
    wind_direction_dominant: int
    condition: WeatherCondition = WeatherCondition.CLEAR
    condition_description: str = ""
    precipitation_probability: int = 0
    precipitation_sum: float = 0.0
    precipitation_hours: float = 0.0
    uv_index_max: float = 0.0
    sunrise: datetime | None = None
    sunset: datetime | None = None
    hourly: list[HourlyForecast] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "temperature_min": self.temperature_min,
            "temperature_max": self.temperature_max,
            "feels_like_min": self.feels_like_min,
            "feels_like_max": self.feels_like_max,
            "humidity_avg": self.humidity_avg,
            "pressure_avg": self.pressure_avg,
            "wind_speed_max": self.wind_speed_max,
            "wind_direction_dominant": self.wind_direction_dominant,
            "condition": self.condition.value,
            "condition_description": self.condition_description,
            "precipitation_probability": self.precipitation_probability,
            "precipitation_sum": self.precipitation_sum,
            "precipitation_hours": self.precipitation_hours,
            "uv_index_max": self.uv_index_max,
            "sunrise": self.sunrise.isoformat() if self.sunrise else None,
            "sunset": self.sunset.isoformat() if self.sunset else None,
            "hourly": [h.to_dict() for h in self.hourly],
        }


@dataclass(frozen=True)
class WeatherForecast:
    """Complete weather forecast"""
    coordinates: Coordinates
    location_name: str
    current: CurrentWeather
    hourly: list[HourlyForecast] = field(default_factory=list)
    daily: list[DailyForecast] = field(default_factory=list)
    source: WeatherSource = WeatherSource.OPEN_METEO
    generated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "coordinates": self.coordinates.to_dict(),
            "location_name": self.location_name,
            "current": self.current.to_dict(),
            "hourly": [h.to_dict() for h in self.hourly],
            "daily": [d.to_dict() for d in self.daily],
            "source": self.source.value,
            "generated_at": self.generated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass(frozen=True)
class WeatherAlert:
    """Weather alert"""
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    coordinates: Coordinates
    area_name: str
    effective_at: datetime
    expires_at: datetime
    source: WeatherSource = WeatherSource.OPEN_METEO
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "coordinates": self.coordinates.to_dict(),
            "area_name": self.area_name,
            "effective_at": self.effective_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "source": self.source.value,
            "metadata": self.metadata,
        }

    @property
    def is_active(self) -> bool:
        now = datetime.utcnow()
        return self.effective_at <= now <= self.expires_at


@dataclass(frozen=True)
class HistoricalWeather:
    """Historical weather data"""
    coordinates: Coordinates
    date: datetime
    temperature_avg: float
    temperature_min: float
    temperature_max: float
    humidity_avg: int
    pressure_avg: float
    wind_speed_avg: float
    wind_speed_max: float
    precipitation_sum: float
    condition: WeatherCondition
    source: WeatherSource = WeatherSource.OPEN_METEO

    def to_dict(self) -> dict:
        return {
            "coordinates": self.coordinates.to_dict(),
            "date": self.date.isoformat(),
            "temperature_avg": self.temperature_avg,
            "temperature_min": self.temperature_min,
            "temperature_max": self.temperature_max,
            "humidity_avg": self.humidity_avg,
            "pressure_avg": self.pressure_avg,
            "wind_speed_avg": self.wind_speed_avg,
            "wind_speed_max": self.wind_speed_max,
            "precipitation_sum": self.precipitation_sum,
            "condition": self.condition.value,
            "source": self.source.value,
        }


class WeatherService(ABC):
    """Abstract weather service"""

    @abstractmethod
    async def get_current_weather(
        self,
        coordinates: Coordinates,
        source: WeatherSource | None = None,
    ) -> CurrentWeather:
        """Get current weather conditions"""
        pass

    @abstractmethod
    async def get_forecast(
        self,
        coordinates: Coordinates,
        days: int = 7,
        hourly: bool = True,
        source: WeatherSource | None = None,
    ) -> WeatherForecast:
        """Get weather forecast"""
        pass

    @abstractmethod
    async def get_hourly_forecast(
        self,
        coordinates: Coordinates,
        hours: int = 48,
        source: WeatherSource | None = None,
    ) -> list[HourlyForecast]:
        """Get hourly forecast"""
        pass

    @abstractmethod
    async def get_daily_forecast(
        self,
        coordinates: Coordinates,
        days: int = 7,
        source: WeatherSource | None = None,
    ) -> list[DailyForecast]:
        """Get daily forecast"""
        pass

    @abstractmethod
    async def get_alerts(
        self,
        coordinates: Coordinates,
        source: WeatherSource | None = None,
    ) -> list[WeatherAlert]:
        """Get active weather alerts"""
        pass

    @abstractmethod
    async def get_historical_weather(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
        source: WeatherSource | None = None,
    ) -> list[HistoricalWeather]:
        """Get historical weather data"""
        pass

    @abstractmethod
    async def get_weather_for_route(
        self,
        coordinates_list: list[Coordinates],
        departure_time: datetime,
    ) -> list[WeatherForecast]:
        """Get weather along a route"""
        pass

    @abstractmethod
    async def is_suitable_for_activity(
        self,
        coordinates: Coordinates,
        activity_type: str,  # walking, cycling, outdoor_dining, etc.
        time: datetime | None = None,
    ) -> dict[str, Any]:
        """Check if weather is suitable for an activity"""
        pass


class WeatherServiceImpl(WeatherService):
    """Default implementation of weather service"""

    def __init__(
        self,
        open_meteo_client=None,
        openweather_client=None,
        weatherapi_client=None,
        cache_ttl_minutes: int = 30,
    ):
        self.open_meteo_client = open_meteo_client
        self.openweather_client = openweather_client
        self.weatherapi_client = weatherapi_client
        self.cache_ttl_minutes = cache_ttl_minutes
        self._cache: dict[str, tuple] = {}  # key -> (data, expires_at)

    def _get_cache_key(self, method: str, coordinates: Coordinates, **kwargs) -> str:
        """Generate cache key"""
        return f"{method}:{coordinates.latitude:.4f},{coordinates.longitude:.4f}:{hash(str(sorted(kwargs.items())))}"

    def _get_cached(self, key: str):
        """Get cached data if not expired"""
        if key in self._cache:
            data, expires_at = self._cache[key]
            if datetime.utcnow() < expires_at:
                return data
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data):
        """Set cache with TTL"""
        expires_at = datetime.utcnow() + timedelta(minutes=self.cache_ttl_minutes)
        self._cache[key] = (data, expires_at)

    async def get_current_weather(
        self,
        coordinates: Coordinates,
        source: WeatherSource | None = None,
    ) -> CurrentWeather:
        """Get current weather conditions"""
        # Placeholder implementation
        return CurrentWeather(
            coordinates=coordinates,
            location_name="Unknown",
            temperature=20.0,
            feels_like=20.0,
            humidity=50,
            pressure=1013.25,
            wind_speed=5.0,
            wind_direction=180,
            condition=WeatherCondition.CLEAR,
            condition_description="Clear sky",
        )

    async def get_forecast(
        self,
        coordinates: Coordinates,
        days: int = 7,
        hourly: bool = True,
        source: WeatherSource | None = None,
    ) -> WeatherForecast:
        """Get weather forecast"""
        current = await self.get_current_weather(coordinates, source)

        return WeatherForecast(
            coordinates=coordinates,
            location_name="Unknown",
            current=current,
            hourly=[],
            daily=[],
            source=source or WeatherSource.OPEN_METEO,
        )

    async def get_hourly_forecast(
        self,
        coordinates: Coordinates,
        hours: int = 48,
        source: WeatherSource | None = None,
    ) -> list[HourlyForecast]:
        """Get hourly forecast"""
        return []

    async def get_daily_forecast(
        self,
        coordinates: Coordinates,
        days: int = 7,
        source: WeatherSource | None = None,
    ) -> list[DailyForecast]:
        """Get daily forecast"""
        return []

    async def get_alerts(
        self,
        coordinates: Coordinates,
        source: WeatherSource | None = None,
    ) -> list[WeatherAlert]:
        """Get active weather alerts"""
        return []

    async def get_historical_weather(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
        source: WeatherSource | None = None,
    ) -> list[HistoricalWeather]:
        """Get historical weather data"""
        return []

    async def get_weather_for_route(
        self,
        coordinates_list: list[Coordinates],
        departure_time: datetime,
    ) -> list[WeatherForecast]:
        """Get weather along a route"""
        forecasts = []
        for coords in coordinates_list:
            forecast = await self.get_forecast(coords, days=1, hourly=True)
            forecasts.append(forecast)
        return forecasts

    async def is_suitable_for_activity(
        self,
        coordinates: Coordinates,
        activity_type: str,
        time: datetime | None = None,
    ) -> dict[str, Any]:
        """Check if weather is suitable for an activity"""
        current = await self.get_current_weather(coordinates)

        # Simple suitability logic
        suitable = True
        reasons = []

        if activity_type in ["walking", "cycling", "outdoor_dining"]:
            if current.condition in [WeatherCondition.HEAVY_RAIN, WeatherCondition.THUNDERSTORM, WeatherCondition.HEAVY_SNOW]:
                suitable = False
                reasons.append(f"Unsuitable due to {current.condition.value}")
            if current.temperature > 35:
                suitable = False
                reasons.append("Too hot for outdoor activity")
            if current.temperature < -10:
                suitable = False
                reasons.append("Too cold for outdoor activity")
            if current.wind_speed > 15:
                reasons.append("Windy conditions")

        return {
            "suitable": suitable,
            "reasons": reasons,
            "current_weather": current.to_dict(),
            "activity_type": activity_type,
        }
