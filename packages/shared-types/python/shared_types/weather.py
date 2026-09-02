"""
Weather Types

Type definitions for weather data.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from .common import Coordinates


class WeatherCondition(str, Enum):
    """Weather condition codes."""
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
    HEAVY_SNOW_SHOWERS = "heavy_snow_showers"
    THUNDERSTORM = "thunderstorm"
    THUNDERSTORM_WITH_HAIL = "thunderstorm_with_hail"


class WeatherSeverity(str, Enum):
    """Weather alert severity."""
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


class WeatherUrgency(str, Enum):
    """Weather alert urgency."""
    IMMEDIATE = "immediate"
    EXPECTED = "expected"
    FUTURE = "future"
    PAST = "past"


class WeatherCertainty(str, Enum):
    """Weather alert certainty."""
    OBSERVED = "observed"
    LIKELY = "likely"
    POSSIBLE = "possible"
    UNLIKELY = "unlikely"


class WeatherAlert(BaseModel):
    """Weather alert."""
    id: UUID
    location_id: UUID
    event: str
    severity: WeatherSeverity
    urgency: WeatherUrgency
    certainty: WeatherCertainty
    headline: str
    description: str
    instruction: Optional[str] = None
    effective: datetime
    onset: Optional[datetime] = None
    expires: Optional[datetime] = None
    ends: Optional[datetime] = None
    sender: str
    areas: List[str] = Field(default_factory=list)
    geocode: Dict[str, List[str]] = Field(default_factory=dict)
    parameters: Dict[str, List[str]] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeatherCurrent(BaseModel):
    """Current weather conditions."""
    location_id: UUID
    coordinates: Coordinates
    temperature: float  # Celsius
    feels_like: float
    humidity: int  # percentage
    pressure: float  # hPa
    wind_speed: float  # m/s
    wind_direction: int  # degrees
    wind_gust: Optional[float] = None
    cloud_cover: int  # percentage
    visibility: float  # meters
    uv_index: Optional[float] = None
    condition: WeatherCondition
    condition_description: str
    precipitation: float  # mm
    precipitation_probability: int  # percentage
    dew_point: Optional[float] = None
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeatherHourly(BaseModel):
    """Hourly weather forecast."""
    location_id: UUID
    timestamp: datetime
    temperature: float
    feels_like: float
    humidity: int
    pressure: float
    wind_speed: float
    wind_direction: int
    wind_gust: Optional[float] = None
    cloud_cover: int
    visibility: float
    uv_index: Optional[float] = None
    condition: WeatherCondition
    condition_description: str
    precipitation: float
    precipitation_probability: int
    dew_point: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeatherDaily(BaseModel):
    """Daily weather forecast."""
    location_id: UUID
    date: datetime
    temperature_min: float
    temperature_max: float
    feels_like_min: float
    feels_like_max: float
    humidity: int
    pressure: float
    wind_speed: float
    wind_direction: int
    wind_gust: Optional[float] = None
    cloud_cover: int
    visibility: float
    uv_index: Optional[float] = None
    condition: WeatherCondition
    condition_description: str
    precipitation: float
    precipitation_probability: int
    sunrise: datetime
    sunset: datetime
    daylight_hours: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LocationWeather(BaseModel):
    """Complete weather for a location."""
    location_id: UUID
    coordinates: Coordinates
    timezone: str
    current: Optional[WeatherCurrent] = None
    hourly: List[WeatherHourly] = Field(default_factory=list)
    daily: List[WeatherDaily] = Field(default_factory=list)
    alerts: List[WeatherAlert] = Field(default_factory=list)
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeatherLocation(BaseModel):
    """Weather monitoring location."""
    id: UUID
    name: str
    coordinates: Coordinates
    timezone: str
    elevation: Optional[float] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)