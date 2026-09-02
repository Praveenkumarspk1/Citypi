"""
Weather Application Use Cases
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from ...domain.entities.weather import WeatherAlert, WeatherForecast
from ...domain.repositories.weather_repository import WeatherRepository
from ...domain.value_objects.coordinates import Coordinates


@dataclass
class GetWeatherRequest:
    """Request to get weather"""
    coordinates: Coordinates
    days: int = 7
    include_hourly: bool = True


@dataclass
class GetHistoricalWeatherRequest:
    """Request to get historical weather"""
    coordinates: Coordinates
    start_date: date
    end_date: date


class WeatherUseCases:
    """Weather Application Use Cases"""

    def __init__(
        self,
        weather_repository: WeatherRepository,
        weather_service: WeatherService,
    ):
        self.weather_repository = weather_repository

    async def get_current_weather(self, coordinates: Coordinates) -> dict[str, Any] | None:
        """Get current weather"""
        return await self.weather_repository.get_current_weather(coordinates)

    async def get_forecast(self, request: GetWeatherRequest) -> WeatherForecast | None:
        """Get weather forecast"""
        return await self.weather_repository.get_forecast(
            coordinates=request.coordinates,
            days=request.days,
        )

    async def get_alerts(self, coordinates: Coordinates) -> list[WeatherAlert]:
        """Get weather alerts"""
        return await self.weather_repository.get_alerts(coordinates)

    async def get_historical(self, request: GetHistoricalWeatherRequest) -> list[dict[str, Any]]:
        """Get historical weather"""
        return await self.weather_repository.get_historical(
            coordinates=request.coordinates,
            start_date=datetime.combine(request.start_date, datetime.min.time()),
            end_date=datetime.combine(request.end_date, datetime.max.time()),
        )

    async def get_weather_for_itinerary(
        self,
        coordinates: Coordinates,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Get weather for itinerary dates"""
        return await self.weather_service.get_weather_for_itinerary(
            coordinates=coordinates,
            start_date=start_date,
            end_date=end_date,
        )

    async def check_weather_impact(
        self,
        coordinates: Coordinates,
        activity_type: str,
        date: date,
    ) -> dict[str, Any]:
        """Check weather impact on activity"""
        return await self.weather_service.check_weather_impact(
            coordinates=coordinates,
            activity_type=activity_type,
            date=date,
        )

    async def get_uv_index(self, coordinates: Coordinates, date: date) -> float | None:
        """Get UV index for date"""
        return await self.weather_service.get_uv_index(coordinates, date)

    async def get_pollen_forecast(
        self,
        coordinates: Coordinates,
        days: int = 5,
    ) -> list[dict[str, Any]]:
        """Get pollen forecast"""
        return await self.weather_service.get_pollen_forecast(coordinates, days)

    async def get_air_quality(
        self,
        coordinates: Coordinates,
    ) -> dict[str, Any] | None:
        """Get air quality"""
        return await self.weather_service.get_air_quality(coordinates)
