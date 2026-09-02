"""
Weather Application Service
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from ...domain.entities.weather import (
    WeatherAlert,
    WeatherCondition,
    WeatherData,
    WeatherForecast,
)
from ...domain.events.domain_events import WeatherAlertTriggeredEvent
from ...domain.repositories.weather_repository import WeatherRepository
from ...domain.services.weather_service import WeatherService as DomainWeatherService
from ...domain.value_objects.coordinates import Coordinates
from ...domain.value_objects.weather_condition import WeatherConditionType
from ..ports.cache import CachePort
from ..ports.event_publisher import EventPublisher
from ..ports.external_services import WeatherServicePort


class WeatherApplicationService:
    """Application service for weather management"""

    def __init__(
        self,
        weather_repository: WeatherRepository,
        weather_service: DomainWeatherService,
        external_weather: WeatherServicePort,
        cache: CachePort,
        event_bus: EventPublisher,
    ):
        self.weather_repository = weather_repository
        self.weather_service = weather_service
        self.external_weather = external_weather
        self.cache = cache
        self.event_bus = event_bus

    async def get_current_weather(self, coordinates: Coordinates) -> WeatherData | None:
        """Get current weather for coordinates"""
        cache_key = f"weather:current:{coordinates.latitude}:{coordinates.longitude}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Check repository for recent data
        recent = await self.weather_repository.get_latest_for_coordinates(coordinates)
        if recent and (datetime.utcnow() - recent.recorded_at).total_seconds() < 300:  # 5 min
            await self.cache.set(cache_key, recent, ttl=300)
            return recent

        # Fetch from external service
        weather = await self.external_weather.get_current_weather(coordinates)
        if weather:
            # Save to repository
            saved = await self.weather_repository.create(weather)
            await self.cache.set(cache_key, saved, ttl=300)
            return saved

        return None

    async def get_forecast(
        self,
        coordinates: Coordinates,
        days: int = 7,
        hourly: bool = False,
    ) -> WeatherForecast | None:
        """Get weather forecast"""
        cache_key = f"weather:forecast:{coordinates.latitude}:{coordinates.longitude}:{days}:{hourly}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        forecast = await self.external_weather.get_forecast(coordinates, days, hourly)
        if forecast:
            await self.weather_repository.create_forecast(forecast)
            await self.cache.set(cache_key, forecast, ttl=1800)  # 30 min cache
            return forecast

        return None

    async def get_historical_weather(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
    ) -> list[WeatherData]:
        """Get historical weather data"""
        return await self.weather_repository.get_historical(
            coordinates=coordinates,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_alerts(self, coordinates: Coordinates) -> list[WeatherAlert]:
        """Get active weather alerts"""
        cache_key = f"weather:alerts:{coordinates.latitude}:{coordinates.longitude}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        alerts = await self.external_weather.get_alerts(coordinates)
        if alerts:
            await self.cache.set(cache_key, alerts, ttl=600)  # 10 min cache

            # Check for new alerts and publish events
            for alert in alerts:
                existing = await self.weather_repository.get_alert_by_id(alert.id)
                if not existing:
                    await self.weather_repository.create_alert(alert)
                    event = WeatherAlertTriggeredEvent.create(alert)
                    await self.event_bus.publish(event)

        return alerts

    async def get_weather_by_condition(
        self,
        condition: WeatherConditionType,
        radius_meters: float = 50000,
    ) -> list[WeatherData]:
        """Get weather data by condition type"""
        return await self.weather_repository.get_by_condition(condition, radius_meters)

    async def search_weather(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WeatherData], int]:
        """Search weather data"""
        return await self.weather_repository.search(query, page, page_size)

    async def sync_weather_data(self, coordinates: Coordinates) -> WeatherData | None:
        """Sync weather data for coordinates"""
        weather = await self.external_weather.get_current_weather(coordinates)
        if weather:
            saved = await self.weather_repository.create(weather)
            await self.cache.set(
                f"weather:current:{coordinates.latitude}:{coordinates.longitude}",
                saved,
                ttl=300,
            )
            return saved
        return None

    async def get_stats(self) -> dict[str, Any]:
        """Get weather statistics"""
        return await self.weather_repository.get_stats()