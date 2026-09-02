"""
Unit tests for weather sync tasks
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from apps.worker.src.tasks.weather_sync import (
    sync_current_weather,
    sync_weather_forecast,
    sync_weather_alerts,
    sync_historical_weather,
    batch_sync_weather,
)
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates


class TestWeatherSync:
    """Test cases for weather sync tasks"""

    @pytest.fixture
    def coordinates(self):
        """Test coordinates for Paris"""
        return Coordinates(latitude=48.8566, longitude=2.3522)

    @pytest.mark.asyncio
    async def test_sync_current_weather(self, coordinates):
        """Test syncing current weather"""
        with patch('apps.worker.src.tasks.weather_sync.get_open_meteo_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get_current_weather.return_value = {
                "temperature": 22.5,
                "humidity": 65,
                "wind_speed": 10.2,
                "wind_direction": 180,
                "pressure": 1013.25,
                "weather_code": 0,
                "weather_description": "Clear sky",
                "visibility": 10000,
                "uv_index": 5.2,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            mock_client.return_value = mock_client_instance

            result = await sync_current_weather(coordinates.latitude, coordinates.longitude)

            assert result is not None
            assert result["temperature"] == 22.5
            assert result["humidity"] == 65
            assert result["weather_description"] == "Clear sky"
            mock_client_instance.get_current_weather.assert_called_once_with(
                coordinates.latitude, coordinates.longitude
            )

    @pytest.mark.asyncio
    async def test_sync_weather_forecast(self, coordinates):
        """Test syncing weather forecast"""
        with patch('apps.worker.src.tasks.weather_sync.get_open_meteo_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get_forecast.return_value = {
                "daily": [
                    {
                        "date": "2024-01-15",
                        "temperature_max": 25.0,
                        "temperature_min": 15.0,
                        "weather_code": 0,
                        "weather_description": "Clear sky",
                        "precipitation_probability": 0,
                        "wind_speed_max": 15.0,
                        "uv_index_max": 6.0,
                    },
                    {
                        "date": "2024-01-16",
                        "temperature_max": 23.0,
                        "temperature_min": 14.0,
                        "weather_code": 1,
                        "weather_description": "Mainly clear",
                        "precipitation_probability": 10,
                        "wind_speed_max": 12.0,
                        "uv_index_max": 5.0,
                    },
                ],
                "hourly": [
                    {
                        "time": "2024-01-15T00:00:00Z",
                        "temperature": 16.0,
                        "weather_code": 0,
                        "precipitation": 0.0,
                    }
                ],
            }
            mock_client.return_value = mock_client_instance

            result = await sync_weather_forecast(coordinates.latitude, coordinates.longitude, days=7)

            assert result is not None
            assert "daily" in result
            assert len(result["daily"]) == 2
            assert result["daily"][0]["temperature_max"] == 25.0
            mock_client_instance.get_forecast.assert_called_once_with(
                coordinates.latitude, coordinates.longitude, 7
            )

    @pytest.mark.asyncio
    async def test_sync_weather_alerts(self, coordinates):
        """Test syncing weather alerts"""
        with patch('apps.worker.src.tasks.weather_sync.get_open_meteo_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get_alerts.return_value = [
                {
                    "alert_id": "ALERT_001",
                    "event": "Heat Advisory",
                    "severity": "moderate",
                    "certainty": "likely",
                    "urgency": "expected",
                    "description": "Temperatures expected to reach 35°C",
                    "instruction": "Stay hydrated and avoid prolonged sun exposure",
                    "effective": datetime.now(timezone.utc).isoformat(),
                    "expires": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat(),
                    "areas": ["Paris", "Ile-de-France"],
                }
            ]
            mock_client.return_value = mock_client_instance

            result = await sync_weather_alerts(coordinates.latitude, coordinates.longitude)

            assert result is not None
            assert "alerts" in result
            assert len(result["alerts"]) == 1
            assert result["alerts"][0]["event"] == "Heat Advisory"
            assert result["alerts"][0]["severity"] == "moderate"
            mock_client_instance.get_alerts.assert_called_once_with(
                coordinates.latitude, coordinates.longitude
            )

    @pytest.mark.asyncio
    async def test_sync_historical_weather(self, coordinates):
        """Test syncing historical weather"""
        with patch('apps.worker.src.tasks.weather_sync.get_open_meteo_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get_historical.return_value = {
                "daily": [
                    {
                        "date": "2024-01-10",
                        "temperature_max": 18.0,
                        "temperature_min": 8.0,
                        "weather_code": 2,
                        "weather_description": "Partly cloudy",
                        "precipitation_sum": 0.0,
                    },
                    {
                        "date": "2024-01-11",
                        "temperature_max": 16.0,
                        "temperature_min": 7.0,
                        "weather_code": 3,
                        "weather_description": "Overcast",
                        "precipitation_sum": 2.5,
                    },
                ]
            }
            mock_client.return_value = mock_client_instance

            start_date = "2024-01-10"
            end_date = "2024-01-11"
            result = await sync_historical_weather(
                coordinates.latitude, coordinates.longitude, start_date, end_date
            )

            assert result is not None
            assert "daily" in result
            assert len(result["daily"]) == 2
            assert result["daily"][0]["precipitation_sum"] == 0.0
            assert result["daily"][1]["precipitation_sum"] == 2.5
            mock_client_instance.get_historical.assert_called_once_with(
                coordinates.latitude, coordinates.longitude, start_date, end_date
            )

    @pytest.mark.asyncio
    async def test_batch_sync_weather(self, coordinates):
        """Test batch syncing weather for multiple locations"""
        coords_list = [
            Coordinates(latitude=48.8566, longitude=2.3522),  # Paris
            Coordinates(latitude=51.5074, longitude=-0.1278),  # London
            Coordinates(latitude=40.7128, longitude=-74.0060),  # New York
        ]

        with patch('apps.worker.src.tasks.weather_sync.sync_current_weather') as mock_current, \
             patch('apps.worker.src.tasks.weather_sync.sync_weather_forecast') as mock_forecast, \
             patch('apps.worker.src.tasks.weather_sync.sync_weather_alerts') as mock_alerts:

            mock_current.return_value = {"temperature": 20.0, "weather_description": "Clear"}
            mock_forecast.return_value = {"daily": [{"date": "2024-01-15", "temperature_max": 22.0}]}
            mock_alerts.return_value = {"alerts": []}

            result = await batch_sync_weather(coords_list)

            assert result is not None
            assert "locations_synced" in result
            assert result["locations_synced"] == 3
            assert mock_current.call_count == 3
            assert mock_forecast.call_count == 3
            assert mock_alerts.call_count == 3

    @pytest.mark.asyncio
    async def test_sync_handles_api_error(self, coordinates):
        """Test that sync handles API errors gracefully"""
        with patch('apps.worker.src.tasks.weather_sync.get_open_meteo_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get_current_weather.side_effect = Exception("API rate limit exceeded")
            mock_client.return_value = mock_client_instance

            with pytest.raises(Exception, match="API rate limit exceeded"):
                await sync_current_weather(coordinates.latitude, coordinates.longitude)

    @pytest.mark.asyncio
    async def test_sync_handles_empty_response(self, coordinates):
        """Test that sync handles empty API response"""
        with patch('apps.worker.src.tasks.weather_sync.get_open_meteo_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get_forecast.return_value = {"daily": [], "hourly": []}
            mock_client.return_value = mock_client_instance

            result = await sync_weather_forecast(coordinates.latitude, coordinates.longitude, days=7)

            assert result is not None
            assert result["daily"] == []
            assert result["hourly"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])