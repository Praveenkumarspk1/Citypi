"""
Weather API Routes
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ....application.use_cases.weather_use_cases import (
    GetHistoricalWeatherRequest,
    GetWeatherRequest,
    WeatherUseCases,
)
from ....domain.value_objects.coordinates import Coordinates
from ....infrastructure.config.dependencies import get_weather_use_cases

router = APIRouter(prefix="/weather", tags=["Weather"])


# Request/Response Models
class CoordinatesModel(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class WeatherCurrentResponse(BaseModel):
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    wind_speed: float
    wind_direction: int
    weather_code: int
    weather_description: str
    visibility: float
    uv_index: float | None
    timestamp: str


class WeatherHourlyResponse(BaseModel):
    time: str
    temperature: float
    feels_like: float
    humidity: int
    precipitation_probability: int
    precipitation: float
    weather_code: int
    weather_description: str
    wind_speed: float
    wind_direction: int
    uv_index: float | None


class WeatherDailyResponse(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    feels_like_max: float
    feels_like_min: float
    humidity_max: int
    humidity_min: int
    precipitation_probability: int
    precipitation: float
    weather_code: int
    weather_description: str
    wind_speed_max: float
    uv_index_max: float | None
    sunrise: str
    sunset: str


class WeatherForecastResponse(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    current: WeatherCurrentResponse
    hourly: list[WeatherHourlyResponse]
    daily: list[WeatherDailyResponse]


class WeatherAlertResponse(BaseModel):
    id: str
    event: str
    severity: str
    urgency: str
    certainty: str
    effective: str
    expires: str
    description: str
    instruction: str | None
    areas: list[str]


class WeatherHistoricalResponse(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    temperature_avg: float
    precipitation: float
    weather_code: int
    weather_description: str


class WeatherImpactResponse(BaseModel):
    activity_type: str
    date: str
    suitable: bool
    score: float
    reasons: list[str]
    recommendations: list[str]


class UVIndexResponse(BaseModel):
    date: str
    uv_index: float
    risk_level: str


class PollenForecastResponse(BaseModel):
    date: str
    pollen_type: str
    level: int
    category: str


class AirQualityResponse(BaseModel):
    aqi: int
    category: str
    pollutants: dict
    timestamp: str


@router.get("/current", response_model=WeatherCurrentResponse)
async def get_current_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    use_cases: WeatherUseCases = Depends(get_weather_use_cases),
):
    """Get current weather"""
    weather = await use_cases.get_current_weather(
        Coordinates(latitude=latitude, longitude=longitude)
    )
    if not weather:
        raise HTTPException(status_code=404, detail="Weather data not available")
    return weather


@router.get("/forecast", response_model=WeatherForecastResponse)
async def get_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(7, ge=1, le=14),
    include_hourly: bool = Query(True),
    use_cases: WeatherUseCases = Depends(get_weather_use_cases),
):
    """Get weather forecast"""
    request = GetWeatherRequest(
        coordinates=Coordinates(latitude=latitude, longitude=longitude),
        days=days,
        include_hourly=include_hourly,
    )

    forecast = await use_cases.get_forecast(request)
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not available")
    return forecast


@router.get("/alerts", response_model=list[WeatherAlertResponse])
async def get_alerts(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    use_cases: WeatherUseCases = Depends(get_weather_use_cases),
):
    """Get weather alerts"""
    return await use_cases.get_alerts(
        Coordinates(latitude=latitude, longitude=longitude)
    )


@router.get("/historical", response_model=list[WeatherHistoricalResponse])
async def get_historical(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: date = Query(...),
    end_date: date = Query(...),
    use_cases: WeatherUseCases = Depends(get_weather_use_cases),
):
    """Get historical weather"""
    request = GetHistoricalWeatherRequest(
        coordinates=Coordinates(latitude=latitude, longitude=longitude),
        start_date=start_date,
        end_date=end_date,
    )

    return await use_cases.get_historical(request)


@router.get("/itinerary", response_model=dict)
async def get_weather_for_itinerary(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: date = Query(...),
    end_date: date = Query(...),
    use_cases: WeatherUseCases = Depends(get_weather_use_cases),
):
    """Get weather for itinerary dates"""
    return await use_cases.get_weather_for_itinerary(
        coordinates=Coordinates(latitude=latitude, longitude=longitude),
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/impact", response_model=WeatherImpactResponse)
async def check_weather_impact(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    activity_type: str = Query(..., min_length=1),
    date: date = Query(...),
    use_cases: WeatherUseCases = Depends(get_weather_use_cases),
):
    """Check weather impact on activity"""
    return await use_cases.check_weather_impact(
        coordinates=Coordinates(latitude=latitude, longitude=longitude),
        activity_type=activity_type,
        date=date,
    )


@router.get("/uv-index", response_model=UVIndexResponse)
async def get_uv_index(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    date: date = Query(...),
    use_cases: WeatherUseCases = Depends(get_weather_use_cases),
):
    """Get UV index for date"""
    uv_index = await use_cases.get_uv_index(
        Coordinates(latitude=latitude, longitude=longitude),
        date,
    )
    if uv_index is None:
        raise HTTPException(status_code=404, detail="UV index not available")

    # Determine risk level
    if uv_index <= 2:
        risk_level = "Low"
    elif uv_index <= 5:
        risk_level = "Moderate"
    elif uv_index <= 7:
        risk_level = "High"
    elif uv_index <= 10:
        risk_level = "Very High"
    else:
        risk_level = "Extreme"

    return UVIndexResponse(
        date=date.isoformat(),
        uv_index=uv_index,
        risk_level=risk_level,
    )


@router.get("/pollen", response_model=list[PollenForecastResponse])
async def get_pollen_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(5, ge=1, le=7),
    use_cases: WeatherUseCases = Depends(get_weather_use_cases),
):
    """Get pollen forecast"""
    return await use_cases.get_pollen_forecast(
        Coordinates(latitude=latitude, longitude=longitude),
        days,
    )


@router.get("/air-quality", response_model=AirQualityResponse)
async def get_air_quality(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    use_cases: WeatherUseCases = Depends(get_weather_use_cases),
):
    """Get air quality"""
    air_quality = await use_cases.get_air_quality(
        Coordinates(latitude=latitude, longitude=longitude)
    )
    if not air_quality:
        raise HTTPException(status_code=404, detail="Air quality data not available")
    return air_quality
