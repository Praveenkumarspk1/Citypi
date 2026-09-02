"""
Weather Domain Entities
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from ..value_objects.coordinates import Coordinates


class WeatherCondition(StrEnum):
    """Weather condition codes (based on WMO/Open-Meteo)"""
    CLEAR = "clear"
    MAINLY_CLEAR = "mainly_clear"
    PARTLY_CLOUDY = "partly_cloudy"
    OVERCAST = "overcast"
    FOG = "fog"
    DEPOSITING_RIME_FOG = "depositing_rime_fog"
    LIGHT_DRIZZLE = "light_drizzle"
    MODERATE_DRIZZLE = "moderate_drizzle"
    DENSE_DRIZZLE = "dense_drizzle"
    LIGHT_FREEZING_DRIZZLE = "light_freezing_drizzle"
    DENSE_FREEZING_DRIZZLE = "dense_freezing_drizzle"
    SLIGHT_RAIN = "slight_rain"
    MODERATE_RAIN = "moderate_rain"
    HEAVY_RAIN = "heavy_rain"
    LIGHT_FREEZING_RAIN = "light_freezing_rain"
    HEAVY_FREEZING_RAIN = "heavy_freezing_rain"
    SLIGHT_SNOW = "slight_snow"
    MODERATE_SNOW = "moderate_snow"
    HEAVY_SNOW = "heavy_snow"
    SNOW_GRAINS = "snow_grains"
    SLIGHT_RAIN_SHOWERS = "slight_rain_showers"
    MODERATE_RAIN_SHOWERS = "moderate_rain_showers"
    VIOLENT_RAIN_SHOWERS = "violent_rain_showers"
    SLIGHT_SNOW_SHOWERS = "slight_snow_showers"
    MODERATE_SNOW_SHOWERS = "moderate_snow_showers"
    HEAVY_SNOW_SHOWERS = "heavy_snow_showers"
    THUNDERSTORM = "thunderstorm"
    THUNDERSTORM_SLIGHT_HAIL = "thunderstorm_slight_hail"
    THUNDERSTORM_HEAVY_HAIL = "thunderstorm_heavy_hail"
    UNKNOWN = "unknown"


class WeatherSeverity(StrEnum):
    """Weather severity levels"""
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


class PrecipitationType(StrEnum):
    """Precipitation types"""
    NONE = "none"
    RAIN = "rain"
    SNOW = "snow"
    SLEET = "sleet"
    HAIL = "hail"
    DRIZZLE = "drizzle"
    FREEZING_RAIN = "freezing_rain"
    FREEZING_DRIZZLE = "freezing_drizzle"
    MIXED = "mixed"


@dataclass
class WeatherCurrent:
    """Current weather conditions"""
    coordinates: Coordinates = field(default_factory=lambda: Coordinates(0, 0))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Temperature
    temperature: float = 0.0  # Celsius
    feels_like: float = 0.0
    dew_point: float = 0.0

    # Humidity & Pressure
    humidity: int = 0  # percentage
    pressure: float = 0.0  # hPa

    # Wind
    wind_speed: float = 0.0  # m/s
    wind_direction: int = 0  # degrees
    wind_gust: float | None = None

    # Conditions
    condition: WeatherCondition = WeatherCondition.UNKNOWN
    condition_description: str = ""
    cloud_cover: int = 0  # percentage
    visibility: float = 0.0  # meters

    # Precipitation
    precipitation: float = 0.0  # mm
    precipitation_type: PrecipitationType = PrecipitationType.NONE
    precipitation_probability: int = 0  # percentage

    # UV & Solar
    uv_index: float = 0.0
    solar_radiation: float = 0.0  # W/m²

    # Air Quality (optional)
    air_quality_index: int | None = None
    pm25: float | None = None
    pm10: float | None = None
    o3: float | None = None
    no2: float | None = None
    so2: float | None = None
    co: float | None = None

    # Source
    source: str = "open-meteo"
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "coordinates": self.coordinates.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "dew_point": self.dew_point,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "wind_gust": self.wind_gust,
            "condition": self.condition.value,
            "condition_description": self.condition_description,
            "cloud_cover": self.cloud_cover,
            "visibility": self.visibility,
            "precipitation": self.precipitation,
            "precipitation_type": self.precipitation_type.value,
            "precipitation_probability": self.precipitation_probability,
            "uv_index": self.uv_index,
            "solar_radiation": self.solar_radiation,
            "air_quality_index": self.air_quality_index,
            "pm25": self.pm25,
            "pm10": self.pm10,
            "o3": self.o3,
            "no2": self.no2,
            "so2": self.so2,
            "co": self.co,
            "source": self.source,
        }

    def get_wind_direction_name(self) -> str:
        """Get wind direction as cardinal name"""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                      "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(self.wind_direction / 22.5) % 16
        return directions[index]

    def is_precipitating(self) -> bool:
        """Check if currently precipitating"""
        return self.precipitation > 0

    def get_severity(self) -> WeatherSeverity:
        """Determine weather severity"""
        if self.condition in (WeatherCondition.THUNDERSTORM,
                              WeatherCondition.THUNDERSTORM_SLIGHT_HAIL,
                              WeatherCondition.THUNDERSTORM_HEAVY_HAIL):
            return WeatherSeverity.SEVERE
        if self.condition in (WeatherCondition.HEAVY_RAIN, WeatherCondition.HEAVY_SNOW,
                              WeatherCondition.VIOLENT_RAIN_SHOWERS, WeatherCondition.HEAVY_SNOW_SHOWERS):
            return WeatherSeverity.MODERATE
        if self.condition in (WeatherCondition.MODERATE_RAIN, WeatherCondition.MODERATE_SNOW,
                              WeatherCondition.MODERATE_RAIN_SHOWERS, WeatherCondition.MODERATE_SNOW_SHOWERS):
            return WeatherSeverity.MINOR
        return WeatherSeverity.NONE


@dataclass
class WeatherHourly:
    """Hourly weather forecast"""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Temperature
    temperature: float = 0.0
    feels_like: float = 0.0
    dew_point: float = 0.0

    # Humidity & Pressure
    humidity: int = 0
    pressure: float = 0.0

    # Wind
    wind_speed: float = 0.0
    wind_direction: int = 0
    wind_gust: float | None = None

    # Conditions
    condition: WeatherCondition = WeatherCondition.UNKNOWN
    condition_description: str = ""
    cloud_cover: int = 0
    visibility: float = 0.0

    # Precipitation
    precipitation: float = 0.0
    precipitation_type: PrecipitationType = PrecipitationType.NONE
    precipitation_probability: int = 0

    # UV
    uv_index: float = 0.0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "dew_point": self.dew_point,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "wind_gust": self.wind_gust,
            "condition": self.condition.value,
            "condition_description": self.condition_description,
            "cloud_cover": self.cloud_cover,
            "visibility": self.visibility,
            "precipitation": self.precipitation,
            "precipitation_type": self.precipitation_type.value,
            "precipitation_probability": self.precipitation_probability,
            "uv_index": self.uv_index,
        }


@dataclass
class WeatherDaily:
    """Daily weather forecast"""
    date: date = field(default_factory=date.today)

    # Temperature
    temperature_min: float = 0.0
    temperature_max: float = 0.0
    temperature_morning: float = 0.0
    temperature_noon: float = 0.0
    temperature_evening: float = 0.0
    temperature_night: float = 0.0

    # Feels like
    feels_like_min: float = 0.0
    feels_like_max: float = 0.0

    # Sun
    sunrise: datetime | None = None
    sunset: datetime | None = None
    daylight_duration: float = 0.0  # seconds
    sunshine_duration: float = 0.0  # seconds

    # Conditions
    condition: WeatherCondition = WeatherCondition.UNKNOWN
    condition_description: str = ""

    # Precipitation
    precipitation_sum: float = 0.0
    precipitation_probability_max: int = 0
    precipitation_hours: float = 0.0
    precipitation_type: PrecipitationType = PrecipitationType.NONE

    # Wind
    wind_speed_max: float = 0.0
    wind_gust_max: float | None = None
    wind_direction_dominant: int = 0

    # UV
    uv_index_max: float = 0.0
    uv_index_clear_sky_max: float = 0.0

    # Other
    humidity_mean: int = 0
    pressure_mean: float = 0.0
    cloud_cover_mean: int = 0
    visibility_mean: float = 0.0

    # Hourly breakdown
    hourly: list[WeatherHourly] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "temperature_min": self.temperature_min,
            "temperature_max": self.temperature_max,
            "temperature_morning": self.temperature_morning,
            "temperature_noon": self.temperature_noon,
            "temperature_evening": self.temperature_evening,
            "temperature_night": self.temperature_night,
            "feels_like_min": self.feels_like_min,
            "feels_like_max": self.feels_like_max,
            "sunrise": self.sunrise.isoformat() if self.sunrise else None,
            "sunset": self.sunset.isoformat() if self.sunset else None,
            "daylight_duration": self.daylight_duration,
            "sunshine_duration": self.sunshine_duration,
            "condition": self.condition.value,
            "condition_description": self.condition_description,
            "precipitation_sum": self.precipitation_sum,
            "precipitation_probability_max": self.precipitation_probability_max,
            "precipitation_hours": self.precipitation_hours,
            "precipitation_type": self.precipitation_type.value,
            "wind_speed_max": self.wind_speed_max,
            "wind_gust_max": self.wind_gust_max,
            "wind_direction_dominant": self.wind_direction_dominant,
            "uv_index_max": self.uv_index_max,
            "uv_index_clear_sky_max": self.uv_index_clear_sky_max,
            "humidity_mean": self.humidity_mean,
            "pressure_mean": self.pressure_mean,
            "cloud_cover_mean": self.cloud_cover_mean,
            "visibility_mean": self.visibility_mean,
            "hourly": [h.to_dict() for h in self.hourly],
        }

    def get_daylight_hours(self) -> float:
        """Get daylight hours"""
        return self.daylight_duration / 3600

    def get_sunshine_hours(self) -> float:
        """Get sunshine hours"""
        return self.sunshine_duration / 3600


@dataclass
class WeatherAlert:
    """Weather alert/warning"""
    id: str = ""
    title: str = ""
    description: str = ""
    severity: WeatherSeverity = WeatherSeverity.NONE
    certainty: str = "unknown"  # observed, likely, possible, unlikely, unknown
    urgency: str = "unknown"    # immediate, expected, future, past, unknown
    event: str = ""
    effective: datetime | None = None
    expires: datetime | None = None
    sender: str = ""
    areas: list[str] = field(default_factory=list)
    coordinates: Coordinates | None = None
    source: str = "open-meteo"

    def is_active(self) -> bool:
        """Check if alert is currently active"""
        now = datetime.utcnow()
        if self.effective and self.effective > now:
            return False
        if self.expires and self.expires < now:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "certainty": self.certainty,
            "urgency": self.urgency,
            "event": self.event,
            "effective": self.effective.isoformat() if self.effective else None,
            "expires": self.expires.isoformat() if self.expires else None,
            "sender": self.sender,
            "areas": self.areas,
            "coordinates": self.coordinates.to_dict() if self.coordinates else None,
            "source": self.source,
            "is_active": self.is_active(),
        }


@dataclass
class WeatherForecast:
    """Complete weather forecast for a location"""
    coordinates: Coordinates = field(default_factory=lambda: Coordinates(0, 0))
    location_name: str = ""
    timezone: str = "UTC"
    generated_at: datetime = field(default_factory=datetime.utcnow)

    # Current
    current: WeatherCurrent | None = None

    # Hourly (48 hours)
    hourly: list[WeatherHourly] = field(default_factory=list)

    # Daily (7-16 days)
    daily: list[WeatherDaily] = field(default_factory=list)

    # Alerts
    alerts: list[WeatherAlert] = field(default_factory=list)

    # Source metadata
    source: str = "open-meteo"
    model: str = "best_match"
    units: str = "metric"

    def to_dict(self, include_hourly: bool = True, include_daily: bool = True) -> dict:
        data = {
            "coordinates": self.coordinates.to_dict(),
            "location_name": self.location_name,
            "timezone": self.timezone,
            "generated_at": self.generated_at.isoformat(),
            "current": self.current.to_dict() if self.current else None,
            "alerts": [a.to_dict() for a in self.alerts],
            "source": self.source,
            "model": self.model,
            "units": self.units,
        }
        if include_hourly:
            data["hourly"] = [h.to_dict() for h in self.hourly]
        if include_daily:
            data["daily"] = [d.to_dict() for d in self.daily]
        return data

    def get_current_condition(self) -> WeatherCurrent | None:
        """Get current weather"""
        return self.current

    def get_forecast_for_date(self, target_date: date) -> WeatherDaily | None:
        """Get daily forecast for specific date"""
        for daily in self.daily:
            if daily.date == target_date:
                return daily
        return None

    def get_forecast_for_datetime(self, target_dt: datetime) -> WeatherHourly | None:
        """Get hourly forecast for specific datetime"""
        for hourly in self.hourly:
            if hourly.timestamp.replace(minute=0, second=0, microsecond=0) == target_dt.replace(minute=0, second=0, microsecond=0):
                return hourly
        return None

    def has_severe_alerts(self) -> bool:
        """Check if there are severe weather alerts"""
        return any(a.severity in (WeatherSeverity.SEVERE, WeatherSeverity.EXTREME) and a.is_active() for a in self.alerts)

    def get_active_alerts(self) -> list[WeatherAlert]:
        """Get all active alerts"""
        return [a for a in self.alerts if a.is_active()]


# Weather condition mapping from WMO codes
WMO_CODE_MAP = {
    0: WeatherCondition.CLEAR,
    1: WeatherCondition.MAINLY_CLEAR,
    2: WeatherCondition.PARTLY_CLOUDY,
    3: WeatherCondition.OVERCAST,
    45: WeatherCondition.FOG,
    48: WeatherCondition.DEPOSITING_RIME_FOG,
    51: WeatherCondition.LIGHT_DRIZZLE,
    53: WeatherCondition.MODERATE_DRIZZLE,
    55: WeatherCondition.DENSE_DRIZZLE,
    56: WeatherCondition.LIGHT_FREEZING_DRIZZLE,
    57: WeatherCondition.DENSE_FREEZING_DRIZZLE,
    61: WeatherCondition.SLIGHT_RAIN,
    63: WeatherCondition.MODERATE_RAIN,
    65: WeatherCondition.HEAVY_RAIN,
    66: WeatherCondition.LIGHT_FREEZING_RAIN,
    67: WeatherCondition.HEAVY_FREEZING_RAIN,
    71: WeatherCondition.SLIGHT_SNOW,
    73: WeatherCondition.MODERATE_SNOW,
    75: WeatherCondition.HEAVY_SNOW,
    77: WeatherCondition.SNOW_GRAINS,
    80: WeatherCondition.SLIGHT_RAIN_SHOWERS,
    81: WeatherCondition.MODERATE_RAIN_SHOWERS,
    82: WeatherCondition.VIOLENT_RAIN_SHOWERS,
    85: WeatherCondition.SLIGHT_SNOW_SHOWERS,
    86: WeatherCondition.MODERATE_SNOW_SHOWERS,
    87: WeatherCondition.HEAVY_SNOW_SHOWERS,
    95: WeatherCondition.THUNDERSTORM,
    96: WeatherCondition.THUNDERSTORM_SLIGHT_HAIL,
    99: WeatherCondition.THUNDERSTORM_HEAVY_HAIL,
}


def wmo_code_to_condition(code: int) -> WeatherCondition:
    """Convert WMO weather code to WeatherCondition"""
    return WMO_CODE_MAP.get(code, WeatherCondition.UNKNOWN)


def wmo_code_to_description(code: int) -> str:
    """Get human-readable description for WMO code"""
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Moderate snow showers",
        87: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return descriptions.get(code, "Unknown")
