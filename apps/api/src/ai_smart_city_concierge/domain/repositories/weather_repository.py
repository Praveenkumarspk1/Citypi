"""
Weather Repository Interface
"""
from abc import ABC, abstractmethod
from datetime import date, datetime

from ..entities.weather import (
    WeatherAlert,
    WeatherCurrent,
    WeatherDaily,
    WeatherForecast,
    WeatherHourly,
)
from ..value_objects.coordinates import Coordinates


class WeatherRepository(ABC):
    """Weather repository interface"""

    # Current weather
    @abstractmethod
    async def get_current(
        self,
        coordinates: Coordinates,
    ) -> WeatherCurrent | None:
        pass

    @abstractmethod
    async def upsert_current(self, current: WeatherCurrent) -> WeatherCurrent:
        pass

    @abstractmethod
    async def get_current_for_locations(
        self,
        coordinates_list: list[Coordinates],
    ) -> list[WeatherCurrent]:
        pass

    # Hourly forecast
    @abstractmethod
    async def get_hourly(
        self,
        coordinates: Coordinates,
        start: datetime,
        end: datetime,
    ) -> list[WeatherHourly]:
        pass

    @abstractmethod
    async def upsert_hourly(self, hourly: list[WeatherHourly]) -> list[WeatherHourly]:
        pass

    # Daily forecast
    @abstractmethod
    async def get_daily(
        self,
        coordinates: Coordinates,
        start_date: date,
        end_date: date,
    ) -> list[WeatherDaily]:
        pass

    @abstractmethod
    async def upsert_daily(self, daily: list[WeatherDaily]) -> list[WeatherDaily]:
        pass

    # Alerts
    @abstractmethod
    async def get_alerts(
        self,
        coordinates: Coordinates,
        active_only: bool = True,
    ) -> list[WeatherAlert]:
        pass

    @abstractmethod
    async def upsert_alert(self, alert: WeatherAlert) -> WeatherAlert:
        pass

    @abstractmethod
    async def get_active_alerts_for_area(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
    ) -> list[WeatherAlert]:
        pass

    # Full forecast
    @abstractmethod
    async def get_forecast(
        self,
        coordinates: Coordinates,
        days: int = 7,
    ) -> WeatherForecast | None:
        pass

    @abstractmethod
    async def upsert_forecast(self, forecast: WeatherForecast) -> WeatherForecast:
        pass

    # Cache management
    @abstractmethod
    async def cleanup_old_data(self, days: int = 30) -> int:
        """Clean up weather data older than specified days"""
        pass

    @abstractmethod
    async def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        pass
