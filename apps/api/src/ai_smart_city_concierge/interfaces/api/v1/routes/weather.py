"""
Weather Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from ai_smart_city_concierge.application.dto.response import WeatherForecastResponse
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.infrastructure.auth import get_current_user
from ai_smart_city_concierge.infrastructure.di.container import get_weather_application_service
from ai_smart_city_concierge.application.services.weather_service import WeatherApplicationService

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/current", response_model=WeatherForecastResponse)
async def get_current_weather(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    service: WeatherApplicationService = Depends(get_weather_application_service),
    current_user: dict = Depends(get_current_user),
) -> WeatherForecastResponse:
    """Get current weather for coordinates"""
    coordinates = Coordinates(latitude=lat, longitude=lng)
    weather = await service.get_current_weather(coordinates)
    if not weather:
        raise HTTPException(status_code=404, detail="Weather data not found")
    return WeatherForecastResponse.from_entity(weather, include_hourly=False, include_daily=False)


@router.get("/forecast", response_model=WeatherForecastResponse)
async def get_weather_forecast(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    days: int = Query(7, ge=1, le=16),
    include_hourly: bool = True,
    include_alerts: bool = True,
    service: WeatherApplicationService = Depends(get_weather_application_service),
    current_user: dict = Depends(get_current_user),
) -> WeatherForecastResponse:
    """Get weather forecast for coordinates"""
    coordinates = Coordinates(latitude=lat, longitude=lng)
    forecast = await service.get_forecast(
        coordinates=coordinates,
        days=days,
    )
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return WeatherForecastResponse.from_entity(
        forecast,
        include_hourly=include_hourly,
        include_daily=True,
    )


@router.get("/alerts", response_model=list[dict])
async def get_weather_alerts(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    active_only: bool = True,
    service: WeatherApplicationService = Depends(get_weather_application_service),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Get weather alerts for coordinates"""
    coordinates = Coordinates(latitude=lat, longitude=lng)
    alerts = await service.get_alerts(coordinates)
    return [a.to_dict() for a in alerts]


@router.get("/hourly", response_model=list[dict])
async def get_hourly_forecast(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    hours: int = Query(48, ge=1, le=168),
    service: WeatherApplicationService = Depends(get_weather_application_service),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Get hourly forecast for coordinates"""
    coordinates = Coordinates(latitude=lat, longitude=lng)
    # This would need a method on the service
    return []


@router.get("/daily", response_model=list[dict])
async def get_daily_forecast(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    days: int = Query(7, ge=1, le=16),
    service: WeatherApplicationService = Depends(get_weather_application_service),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Get daily forecast for coordinates"""
    coordinates = Coordinates(latitude=lat, longitude=lng)
    # This would need a method on the service
    return []


@router.post("/batch", response_model=list[WeatherForecastResponse])
async def get_batch_weather(
    locations: list[dict],
    days: int = Query(7, ge=1, le=16),
    service: WeatherApplicationService = Depends(get_weather_application_service),
    current_user: dict = Depends(get_current_user),
) -> list[WeatherForecastResponse]:
    """Get weather for multiple locations"""
    # This would need a method on the service
    return []


@router.get("/cache/stats", response_model=dict)
async def get_cache_stats(
    service: WeatherApplicationService = Depends(get_weather_application_service),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get weather cache statistics (admin only)"""
    # Check admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return await service.get_stats()


@router.post("/cache/cleanup")
async def cleanup_cache(
    days: int = Query(30, ge=1, le=365),
    service: WeatherApplicationService = Depends(get_weather_application_service),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Clean up old weather data (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # This would need a method on the service
    return {"success": True, "deleted_count": 0}
