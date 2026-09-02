"""
Open-Meteo Weather API Client
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp

from ...application.ports.external_services import WeatherServicePort
from ...domain.entities.weather import WeatherAlert, WeatherCondition, WeatherForecast
from ...domain.value_objects.coordinates import Coordinates


@dataclass
class OpenMeteoConfig:
    """Open-Meteo configuration"""
    base_url: str = "https://api.open-meteo.com/v1"
    timeout: int = 10


class OpenMeteoClient(WeatherServicePort):
    """Open-Meteo weather API client (free, no API key required)"""

    # WMO weather code mapping
    WEATHER_CODES = {
        0: ("Clear sky", WeatherCondition.CLEAR),
        1: ("Mainly clear", WeatherCondition.CLEAR),
        2: ("Partly cloudy", WeatherCondition.PARTLY_CLOUDY),
        3: ("Overcast", WeatherCondition.CLOUDY),
        45: ("Fog", WeatherCondition.FOG),
        48: ("Depositing rime fog", WeatherCondition.FOG),
        51: ("Light drizzle", WeatherCondition.DRIZZLE),
        53: ("Moderate drizzle", WeatherCondition.DRIZZLE),
        55: ("Dense drizzle", WeatherCondition.DRIZZLE),
        56: ("Light freezing drizzle", WeatherCondition.FREEZING_RAIN),
        57: ("Dense freezing drizzle", WeatherCondition.FREEZING_RAIN),
        61: ("Slight rain", WeatherCondition.RAIN),
        63: ("Moderate rain", WeatherCondition.RAIN),
        65: ("Heavy rain", WeatherCondition.HEAVY_RAIN),
        66: ("Light freezing rain", WeatherCondition.FREEZING_RAIN),
        67: ("Heavy freezing rain", WeatherCondition.FREEZING_RAIN),
        71: ("Slight snow fall", WeatherCondition.SNOW),
        73: ("Moderate snow fall", WeatherCondition.SNOW),
        75: ("Heavy snow fall", WeatherCondition.HEAVY_SNOW),
        77: ("Snow grains", WeatherCondition.SNOW),
        80: ("Slight rain showers", WeatherCondition.RAIN),
        81: ("Moderate rain showers", WeatherCondition.RAIN),
        82: ("Violent rain showers", WeatherCondition.HEAVY_RAIN),
        85: ("Slight snow showers", WeatherCondition.SNOW),
        86: ("Heavy snow showers", WeatherCondition.HEAVY_SNOW),
        95: ("Thunderstorm", WeatherCondition.THUNDERSTORM),
        96: ("Thunderstorm with slight hail", WeatherCondition.THUNDERSTORM),
        99: ("Thunderstorm with heavy hail", WeatherCondition.THUNDERSTORM),
    }

    def __init__(self, config: OpenMeteoConfig | None = None):
        self.config = config or OpenMeteoConfig()
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _make_request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Make request to Open-Meteo API"""
        session = await self._get_session()
        url = f"{self.config.base_url}{endpoint}"

        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    def _parse_weather_code(self, code: int) -> tuple[str, WeatherCondition]:
        """Parse WMO weather code"""
        return self.WEATHER_CODES.get(code, ("Unknown", WeatherCondition.CLEAR))

    async def get_current_weather(
        self,
        coordinates: Coordinates,
    ) -> dict[str, Any]:
        """Get current weather"""
        params = {
            "latitude": coordinates.latitude,
            "longitude": coordinates.longitude,
            "current_weather": "true",
            "timezone": "auto",
        }

        result = await self._make_request("/forecast", params)

        current = result.get("current_weather", {})
        code = current.get("weathercode", 0)
        description, condition = self._parse_weather_code(code)

        return {
            "temperature": current.get("temperature"),
            "windspeed": current.get("windspeed"),
            "winddirection": current.get("winddirection"),
            "weathercode": code,
            "description": description,
            "condition": condition.value,
            "time": current.get("time"),
            "location": {
                "latitude": coordinates.latitude,
                "longitude": coordinates.longitude,
            },
        }

    async def get_forecast(
        self,
        coordinates: Coordinates,
        days: int = 7,
        hourly: bool = True,
    ) -> WeatherForecast:
        """Get weather forecast"""
        params = {
            "latitude": coordinates.latitude,
            "longitude": coordinates.longitude,
            "daily": [
                "weathercode",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
                "precipitation_sum",
                "windspeed_10m_max",
                "winddirection_10m_dominant",
                "uv_index_max",
            ],
            "timezone": "auto",
            "forecast_days": min(days, 16),  # Max 16 days
        }

        if hourly:
            params["hourly"] = [
                "temperature_2m",
                "relativehumidity_2m",
                "precipitation_probability",
                "precipitation",
                "weathercode",
                "windspeed_10m",
                "winddirection_10m",
                "uv_index",
            ]

        result = await self._make_request("/forecast", params)

        # Parse daily forecast
        daily_data = result.get("daily", {})
        daily_forecasts = []

        for i in range(len(daily_data.get("time", []))):
            code = daily_data["weathercode"][i]
            description, condition = self._parse_weather_code(code)

            daily_forecasts.append({
                "date": daily_data["time"][i],
                "temperature_max": daily_data["temperature_2m_max"][i],
                "temperature_min": daily_data["temperature_2m_min"][i],
                "precipitation_probability": daily_data["precipitation_probability_max"][i],
                "precipitation_sum": daily_data["precipitation_sum"][i],
                "windspeed_max": daily_data["windspeed_10m_max"][i],
                "winddirection_dominant": daily_data["winddirection_10m_dominant"][i],
                "uv_index_max": daily_data["uv_index_max"][i],
                "weathercode": code,
                "description": description,
                "condition": condition.value,
            })

        # Parse hourly forecast
        hourly_forecasts = []
        if hourly and "hourly" in result:
            hourly_data = result["hourly"]
            for i in range(len(hourly_data.get("time", []))):
                code = hourly_data["weathercode"][i]
                description, condition = self._parse_weather_code(code)

                hourly_forecasts.append({
                    "time": hourly_data["time"][i],
                    "temperature": hourly_data["temperature_2m"][i],
                    "humidity": hourly_data["relativehumidity_2m"][i],
                    "precipitation_probability": hourly_data["precipitation_probability"][i],
                    "precipitation": hourly_data["precipitation"][i],
                    "weathercode": code,
                    "description": description,
                    "condition": condition.value,
                    "windspeed": hourly_data["windspeed_10m"][i],
                    "winddirection": hourly_data["winddirection_10m"][i],
                    "uv_index": hourly_data["uv_index"][i],
                })

        # Get location name from reverse geocoding (optional)
        location_name = f"{coordinates.latitude:.4f}, {coordinates.longitude:.4f}"

        return WeatherForecast(
            coordinates=coordinates,
            location_name=location_name,
            source="open-meteo",
            daily=daily_forecasts,
            hourly=hourly_forecasts if hourly else None,
            generated_at=datetime.utcnow(),
        )

    async def get_alerts(
        self,
        coordinates: Coordinates,
    ) -> list[WeatherAlert]:
        """Get weather alerts (Open-Meteo doesn't provide alerts directly)"""
        # Open-Meteo doesn't have alerts endpoint
        # Could integrate with National Weather Service or other alert providers
        return []

    async def get_historical(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get historical weather data"""
        params = {
            "latitude": coordinates.latitude,
            "longitude": coordinates.longitude,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": [
                "weathercode",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "windspeed_10m_max",
            ],
            "timezone": "auto",
        }

        result = await self._make_request("/forecast", params)

        daily_data = result.get("daily", {})
        historical = []

        for i in range(len(daily_data.get("time", []))):
            code = daily_data["weathercode"][i]
            description, condition = self._parse_weather_code(code)

            historical.append({
                "date": daily_data["time"][i],
                "temperature_max": daily_data["temperature_2m_max"][i],
                "temperature_min": daily_data["temperature_2m_min"][i],
                "precipitation_sum": daily_data["precipitation_sum"][i],
                "windspeed_max": daily_data["windspeed_10m_max"][i],
                "weathercode": code,
                "description": description,
                "condition": condition.value,
            })

        return historical

    async def get_marine_weather(
        self,
        coordinates: Coordinates,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get marine weather (waves, tides)"""
        params = {
            "latitude": coordinates.latitude,
            "longitude": coordinates.longitude,
            "daily": [
                "wave_height_max",
                "wave_direction_dominant",
                "wave_period_max",
                "wind_wave_height_max",
                "wind_wave_direction_dominant",
                "wind_wave_period_max",
                "swell_wave_height_max",
                "swell_wave_direction_dominant",
                "swell_wave_period_max",
            ],
            "timezone": "auto",
            "forecast_days": min(days, 7),
        }

        result = await self._make_request("/marine", params)
        return result

    async def get_air_quality(
        self,
        coordinates: Coordinates,
        days: int = 3,
    ) -> dict[str, Any]:
        """Get air quality forecast"""
        params = {
            "latitude": coordinates.latitude,
            "longitude": coordinates.longitude,
            "hourly": [
                "pm10",
                "pm2_5",
                "carbon_monoxide",
                "nitrogen_dioxide",
                "sulphur_dioxide",
                "ozone",
                "aerosol_optical_depth",
                "dust",
                "uv_index",
                "uv_index_clear_sky",
            ],
            "timezone": "auto",
            "forecast_days": min(days, 5),
        }

        result = await self._make_request("/air-quality", params)
        return result
