"""
Unit tests for transit sync tasks
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, time, timezone, timedelta
from uuid import uuid4

from apps.worker.src.tasks.transit_sync import (
    sync_gtfs_feed,
    sync_vehicle_positions,
    sync_service_alerts,
    sync_trip_updates,
    process_gtfs_schedule,
)
from ai_smart_city_concierge.domain.aggregates.transit_aggregate import TransitAggregate
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.domain.value_objects.transport_mode import TransportMode


class TestTransitSync:
    """Test cases for transit sync tasks"""

    @pytest.fixture
    def mock_route(self):
        """Create a mock transit route"""
        route = TransitAggregate.create_route(
            route_id="R1",
            name="Red Line",
            short_name="R",
            description="Main north-south line",
            transport_mode=TransportMode.SUBWAY,
            color="#FF0000",
            text_color="#FFFFFF",
        )
        route.add_stop(
            stop_id="S1",
            name="Central Station",
            coordinates=Coordinates(latitude=40.7128, longitude=-74.0060),
            stop_order=1,
            is_accessible=True,
        )
        route.add_stop(
            stop_id="S2",
            name="Downtown",
            coordinates=Coordinates(latitude=40.72, longitude=-74.01),
            stop_order=2,
            is_accessible=True,
        )
        return route

    @pytest.mark.asyncio
    async def test_sync_gtfs_feed(self, mock_route):
        """Test syncing GTFS feed"""
        with patch('apps.worker.src.tasks.transit_sync.get_gtfs_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.fetch_feed.return_value = {
                "agencies": [{"agency_id": "A1", "agency_name": "Metro Transit"}],
                "routes": [
                    {
                        "route_id": "R1",
                        "route_short_name": "R",
                        "route_long_name": "Red Line",
                        "route_type": 1,  # Subway
                        "route_color": "FF0000",
                        "route_text_color": "FFFFFF",
                    }
                ],
                "stops": [
                    {"stop_id": "S1", "stop_name": "Central Station", "stop_lat": 40.7128, "stop_lon": -74.0060},
                    {"stop_id": "S2", "stop_name": "Downtown", "stop_lat": 40.72, "stop_lon": -74.01},
                ],
                "trips": [
                    {"trip_id": "T1", "route_id": "R1", "service_id": "S1", "trip_headsign": "Downtown"},
                ],
                "stop_times": [
                    {"trip_id": "T1", "stop_id": "S1", "stop_sequence": 1, "arrival_time": "08:00:00", "departure_time": "08:00:00"},
                    {"trip_id": "T1", "stop_id": "S2", "stop_sequence": 2, "arrival_time": "08:15:00", "departure_time": "08:15:00"},
                ],
                "calendar": [
                    {"service_id": "S1", "monday": 1, "tuesday": 1, "wednesday": 1, "thursday": 1, "friday": 1, "saturday": 0, "sunday": 0, "start_date": "20240101", "end_date": "20241231"},
                ],
            }
            mock_client.return_value = mock_client_instance

            result = await sync_gtfs_feed("https://example.com/gtfs.zip")

            assert result is not None
            assert "routes_synced" in result
            assert "stops_synced" in result
            assert "trips_synced" in result
            mock_client_instance.fetch_feed.assert_called_once_with("https://example.com/gtfs.zip")

    @pytest.mark.asyncio
    async def test_sync_vehicle_positions(self, mock_route):
        """Test syncing vehicle positions"""
        with patch('apps.worker.src.tasks.transit_sync.get_gtfs_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.fetch_vehicle_positions.return_value = [
                {
                    "vehicle_id": "V1",
                    "route_id": "R1",
                    "latitude": 40.715,
                    "longitude": -74.008,
                    "current_stop_id": "S1",
                    "next_stop_id": "S2",
                    "occupancy": 0.7,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "vehicle_id": "V2",
                    "route_id": "R1",
                    "latitude": 40.718,
                    "longitude": -74.009,
                    "current_stop_id": "S1",
                    "next_stop_id": "S2",
                    "occupancy": 0.3,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            ]
            mock_client.return_value = mock_client_instance

            result = await sync_vehicle_positions("R1")

            assert result is not None
            assert "vehicles_updated" in result
            assert result["vehicles_updated"] == 2
            mock_client_instance.fetch_vehicle_positions.assert_called_once_with("R1")

    @pytest.mark.asyncio
    async def test_sync_service_alerts(self, mock_route):
        """Test syncing service alerts"""
        with patch('apps.worker.src.tasks.transit_sync.get_gtfs_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.fetch_service_alerts.return_value = [
                {
                    "alert_id": "A1",
                    "cause": "construction",
                    "effect": "delay",
                    "severity": "moderate",
                    "description": "Track maintenance causing 10-minute delays",
                    "affected_routes": ["R1"],
                    "active_period_start": datetime.now(timezone.utc).isoformat(),
                    "active_period_end": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
                }
            ]
            mock_client.return_value = mock_client_instance

            result = await sync_service_alerts("R1")

            assert result is not None
            assert "alerts_synced" in result
            assert result["alerts_synced"] == 1
            mock_client_instance.fetch_service_alerts.assert_called_once_with("R1")

    @pytest.mark.asyncio
    async def test_sync_trip_updates(self, mock_route):
        """Test syncing trip updates"""
        with patch('apps.worker.src.tasks.transit_sync.get_gtfs_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.fetch_trip_updates.return_value = [
                {
                    "trip_id": "T1",
                    "route_id": "R1",
                    "stop_time_updates": [
                        {"stop_id": "S1", "arrival_delay": 120, "departure_delay": 120},
                        {"stop_id": "S2", "arrival_delay": 180, "departure_delay": 180},
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ]
            mock_client.return_value = mock_client_instance

            result = await sync_trip_updates("R1")

            assert result is not None
            assert "trips_updated" in result
            assert result["trips_updated"] == 1
            mock_client_instance.fetch_trip_updates.assert_called_once_with("R1")

    @pytest.mark.asyncio
    async def test_process_gtfs_schedule(self, mock_route):
        """Test processing GTFS schedule into route"""
        with patch('apps.worker.src.tasks.transit_sync.get_gtfs_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.fetch_feed.return_value = {
                "routes": [
                    {
                        "route_id": "R1",
                        "route_short_name": "R",
                        "route_long_name": "Red Line",
                        "route_type": 1,
                        "route_color": "FF0000",
                        "route_text_color": "FFFFFF",
                    }
                ],
                "stops": [
                    {"stop_id": "S1", "stop_name": "Central Station", "stop_lat": 40.7128, "stop_lon": -74.0060},
                    {"stop_id": "S2", "stop_name": "Downtown", "stop_lat": 40.72, "stop_lon": -74.01},
                ],
                "trips": [
                    {"trip_id": "T1", "route_id": "R1", "service_id": "S1", "trip_headsign": "Downtown"},
                ],
                "stop_times": [
                    {"trip_id": "T1", "stop_id": "S1", "stop_sequence": 1, "arrival_time": "08:00:00", "departure_time": "08:00:00"},
                    {"trip_id": "T1", "stop_id": "S2", "stop_sequence": 2, "arrival_time": "08:15:00", "departure_time": "08:15:00"},
                ],
                "calendar": [
                    {"service_id": "S1", "monday": 1, "tuesday": 1, "wednesday": 1, "thursday": 1, "friday": 1, "saturday": 0, "sunday": 0, "start_date": "20240101", "end_date": "20241231"},
                ],
            }
            mock_client.return_value = mock_client_instance

            route = await process_gtfs_schedule("https://example.com/gtfs.zip", "R1")

            assert route is not None
            assert route.route_id == "R1"
            assert route.name == "Red Line"
            assert len(route.stops) == 2
            assert len(route.trips) == 1

    @pytest.mark.asyncio
    async def test_sync_handles_empty_feed(self):
        """Test that sync handles empty GTFS feed"""
        with patch('apps.worker.src.tasks.transit_sync.get_gtfs_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.fetch_feed.return_value = {
                "agencies": [],
                "routes": [],
                "stops": [],
                "trips": [],
                "stop_times": [],
                "calendar": [],
            }
            mock_client.return_value = mock_client_instance

            result = await sync_gtfs_feed("https://example.com/empty.zip")

            assert result is not None
            assert result["routes_synced"] == 0
            assert result["stops_synced"] == 0

    @pytest.mark.asyncio
    async def test_sync_handles_api_error(self):
        """Test that sync handles API errors gracefully"""
        with patch('apps.worker.src.tasks.transit_sync.get_gtfs_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.fetch_feed.side_effect = Exception("Network error")
            mock_client.return_value = mock_client_instance

            with pytest.raises(Exception, match="Network error"):
                await sync_gtfs_feed("https://example.com/gtfs.zip")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])