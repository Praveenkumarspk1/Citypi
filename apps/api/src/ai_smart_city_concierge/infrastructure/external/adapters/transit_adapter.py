"""
Transit Data Service Adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ....application.ports.external_services import (
    RealtimeTransitServicePort,
    TransitDataServicePort,
)
from ....domain.entities.transit import TransitMode, TransitRoute, TransitStop, TransitTrip
from ....domain.value_objects.coordinates import Coordinates


@dataclass
class TransitAgency:
    """Transit agency"""
    id: str
    name: str
    url: str
    timezone: str
    lang: str
    phone: str | None
    fare_url: str | None
    email: str | None


class BaseTransitDataAdapter(TransitDataServicePort, ABC):
    """Base transit data adapter"""

    @abstractmethod
    async def _get_agencies_request(self, coordinates: Coordinates | None) -> list[TransitAgency]:
        """Get agencies request"""
        pass

    @abstractmethod
    async def _get_routes_request(
        self,
        agency_id: str | None,
        coordinates: Coordinates | None,
        radius_meters: float | None,
    ) -> list[TransitRoute]:
        """Get routes request"""
        pass

    @abstractmethod
    async def _get_stops_request(
        self,
        route_id: str | None,
        coordinates: Coordinates | None,
        radius_meters: float | None,
    ) -> list[TransitStop]:
        """Get stops request"""
        pass

    @abstractmethod
    async def _get_trips_request(self, route_id: str, date: datetime) -> list[TransitTrip]:
        """Get trips request"""
        pass

    @abstractmethod
    async def _get_schedule_request(
        self,
        stop_id: str,
        date: datetime,
        route_ids: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Get schedule request"""
        pass

    async def get_agencies(self, coordinates: Coordinates | None = None) -> list[dict[str, Any]]:
        """Get transit agencies"""
        agencies = await self._get_agencies_request(coordinates)
        return [
            {
                "id": a.id,
                "name": a.name,
                "url": a.url,
                "timezone": a.timezone,
                "lang": a.lang,
                "phone": a.phone,
                "fare_url": a.fare_url,
                "email": a.email,
            }
            for a in agencies
        ]

    async def get_routes(
        self,
        agency_id: str | None = None,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
    ) -> list[TransitRoute]:
        """Get transit routes"""
        return await self._get_routes_request(agency_id, coordinates, radius_meters)

    async def get_stops(
        self,
        route_id: str | None = None,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
    ) -> list[TransitStop]:
        """Get transit stops"""
        return await self._get_stops_request(route_id, coordinates, radius_meters)

    async def get_trips(
        self,
        route_id: str,
        date: datetime,
    ) -> list[TransitTrip]:
        """Get trips for a route on a date"""
        return await self._get_trips_request(route_id, date)

    async def get_schedule(
        self,
        stop_id: str,
        date: datetime,
        route_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get schedule for a stop"""
        return await self._get_schedule_request(stop_id, date, route_ids)


class GTFSStaticAdapter(BaseTransitDataAdapter):
    """GTFS Static data adapter (loads from local files or database)"""

    def __init__(self, gtfs_path: str):
        self.gtfs_path = gtfs_path
        self._agencies_cache = None
        self._routes_cache = None
        self._stops_cache = None
        self._trips_cache = {}

    async def _load_gtfs_data(self):
        """Load GTFS data from files"""
        import csv
        import os

        # Load agencies
        agencies_file = os.path.join(self.gtfs_path, "agency.txt")
        if os.path.exists(agencies_file):
            self._agencies_cache = []
            with open(agencies_file) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._agencies_cache.append(TransitAgency(
                        id=row.get("agency_id", ""),
                        name=row.get("agency_name", ""),
                        url=row.get("agency_url", ""),
                        timezone=row.get("agency_timezone", ""),
                        lang=row.get("agency_lang", ""),
                        phone=row.get("agency_phone"),
                        fare_url=row.get("agency_fare_url"),
                        email=row.get("agency_email"),
                    ))

        # Load routes
        routes_file = os.path.join(self.gtfs_path, "routes.txt")
        if os.path.exists(routes_file):
            self._routes_cache = []
            with open(routes_file) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._routes_cache.append(TransitRoute(
                        id=row.get("route_id", ""),
                        agency_id=row.get("agency_id", ""),
                        short_name=row.get("route_short_name", ""),
                        long_name=row.get("route_long_name", ""),
                        description=row.get("route_desc"),
                        mode=self._parse_mode(row.get("route_type", "3")),
                        color=row.get("route_color"),
                        text_color=row.get("route_text_color"),
                        url=row.get("route_url"),
                    ))

        # Load stops
        stops_file = os.path.join(self.gtfs_path, "stops.txt")
        if os.path.exists(stops_file):
            self._stops_cache = []
            with open(stops_file) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._stops_cache.append(TransitStop(
                        id=row.get("stop_id", ""),
                        code=row.get("stop_code"),
                        name=row.get("stop_name", ""),
                        description=row.get("stop_desc"),
                        latitude=float(row.get("stop_lat", 0)),
                        longitude=float(row.get("stop_lon", 0)),
                        zone_id=row.get("zone_id"),
                        url=row.get("stop_url"),
                        location_type=int(row.get("location_type", 0)),
                        parent_station=row.get("parent_station"),
                        wheelchair_boarding=int(row.get("wheelchair_boarding", 0)),
                        platform_code=row.get("platform_code"),
                    ))

    def _parse_mode(self, route_type: str) -> TransitMode:
        mode_map = {
            "0": TransitMode.TRAM,
            "1": TransitMode.SUBWAY,
            "2": TransitMode.RAIL,
            "3": TransitMode.BUS,
            "4": TransitMode.FERRY,
            "5": TransitMode.CABLE_CAR,
            "6": TransitMode.GONDOLA,
            "7": TransitMode.FUNICULAR,
        }
        return mode_map.get(route_type, TransitMode.BUS)

    async def _get_agencies_request(self, coordinates: Coordinates | None) -> list[TransitAgency]:
        if self._agencies_cache is None:
            await self._load_gtfs_data()
        return self._agencies_cache or []

    async def _get_routes_request(
        self,
        agency_id: str | None,
        coordinates: Coordinates | None,
        radius_meters: float | None,
    ) -> list[TransitRoute]:
        if self._routes_cache is None:
            await self._load_gtfs_data()

        routes = self._routes_cache or []

        if agency_id:
            routes = [r for r in routes if r.agency_id == agency_id]

        if coordinates and radius_meters:
            # Filter by bounding box (simplified)
            radius_deg = radius_meters / 111000.0
            routes = [
                r for r in routes
                if abs(r.bounds_min_lat - coordinates.latitude) <= radius_deg
                and abs(r.bounds_min_lng - coordinates.longitude) <= radius_deg
            ]

        return routes

    async def _get_stops_request(
        self,
        route_id: str | None,
        coordinates: Coordinates | None,
        radius_meters: float | None,
    ) -> list[TransitStop]:
        if self._stops_cache is None:
            await self._load_gtfs_data()

        stops = self._stops_cache or []

        if route_id:
            # Filter stops by route (would need stop_times.txt)
            pass

        if coordinates and radius_meters:
            radius_deg = radius_meters / 111000.0
            stops = [
                s for s in stops
                if abs(s.latitude - coordinates.latitude) <= radius_deg
                and abs(s.longitude - coordinates.longitude) <= radius_deg
            ]

        return stops

    async def _get_trips_request(self, route_id: str, date: datetime) -> list[TransitTrip]:
        # Would load from trips.txt and calendar.txt
        # Simplified implementation
        return []

    async def _get_schedule_request(
        self,
        stop_id: str,
        date: datetime,
        route_ids: list[str] | None,
    ) -> list[dict[str, Any]]:
        # Would load from stop_times.txt and calendar.txt
        # Simplified implementation
        return []


class TransitlandAdapter(BaseTransitDataAdapter):
    """Transitland API adapter"""

    def __init__(self, base_url: str = "https://transit.land/api/v2/rest"):
        self.base_url = base_url
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    async def _get_agencies_request(self, coordinates: Coordinates | None) -> list[TransitAgency]:
        session = await self._get_session()

        url = f"{self.base_url}/operators"
        params = {"per_page": 100}

        if coordinates:
            params["lat"] = coordinates.latitude
            params["lon"] = coordinates.longitude
            params["r"] = 50000

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                agencies = []
                for item in data.get("operators", []):
                    agencies.append(TransitAgency(
                        id=item.get("onestop_id", ""),
                        name=item.get("name", ""),
                        url=item.get("url", ""),
                        timezone=item.get("timezone", ""),
                        lang="",
                        phone=item.get("phone"),
                        fare_url=item.get("fare_url"),
                        email=item.get("email"),
                    ))
                return agencies
        return []

    async def _get_routes_request(
        self,
        agency_id: str | None,
        coordinates: Coordinates | None,
        radius_meters: float | None,
    ) -> list[TransitRoute]:
        session = await self._get_session()

        url = f"{self.base_url}/routes"
        params = {"per_page": 100}

        if agency_id:
            params["operator_onestop_id"] = agency_id

        if coordinates:
            params["lat"] = coordinates.latitude
            params["lon"] = coordinates.longitude
            params["r"] = radius_meters or 50000

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                routes = []
                for item in data.get("routes", []):
                    routes.append(TransitRoute(
                        id=item.get("onestop_id", ""),
                        agency_id=item.get("operator_onestop_id", ""),
                        short_name=item.get("short_name", ""),
                        long_name=item.get("long_name", ""),
                        description=item.get("description"),
                        mode=self._parse_mode(item.get("vehicle_type", "")),
                        color=item.get("color"),
                        text_color=item.get("text_color"),
                        url=item.get("url"),
                    ))
                return routes
        return []

    async def _get_stops_request(
        self,
        route_id: str | None,
        coordinates: Coordinates | None,
        radius_meters: float | None,
    ) -> list[TransitStop]:
        session = await self._get_session()

        url = f"{self.base_url}/stops"
        params = {"per_page": 100}

        if route_id:
            params["route_onestop_id"] = route_id

        if coordinates:
            params["lat"] = coordinates.latitude
            params["lon"] = coordinates.longitude
            params["r"] = radius_meters or 1000

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                stops = []
                for item in data.get("stops", []):
                    geometry = item.get("geometry", {})
                    coords = geometry.get("coordinates", [0, 0])
                    stops.append(TransitStop(
                        id=item.get("onestop_id", ""),
                        code=item.get("stop_code"),
                        name=item.get("name", ""),
                        description=item.get("description"),
                        latitude=coords[1],
                        longitude=coords[0],
                        zone_id=item.get("zone_id"),
                        url=item.get("url"),
                        location_type=0,
                        parent_station=item.get("parent_station_onestop_id"),
                        wheelchair_boarding=1 if item.get("wheelchair_boarding") == "yes" else 0,
                        platform_code=item.get("platform_code"),
                    ))
                return stops
        return []

    async def _get_trips_request(self, route_id: str, date: datetime) -> list[TransitTrip]:
        # Would need to query schedule API
        return []

    async def _get_schedule_request(
        self,
        stop_id: str,
        date: datetime,
        route_ids: list[str] | None,
    ) -> list[dict[str, Any]]:
        # Would need to query schedule API
        return []

    def _parse_mode(self, vehicle_type: str) -> TransitMode:
        mode_map = {
            "tram": TransitMode.TRAM,
            "subway": TransitMode.SUBWAY,
            "rail": TransitMode.RAIL,
            "bus": TransitMode.BUS,
            "ferry": TransitMode.FERRY,
            "cable_car": TransitMode.CABLE_CAR,
            "gondola": TransitMode.GONDOLA,
            "funicular": TransitMode.FUNICULAR,
        }
        return mode_map.get(vehicle_type.lower(), TransitMode.BUS)

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class BaseRealtimeTransitAdapter(RealtimeTransitServicePort, ABC):
    """Base real-time transit adapter"""

    @abstractmethod
    async def _get_arrivals_request(
        self,
        stop_id: str,
        route_ids: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Get arrivals request"""
        pass

    @abstractmethod
    async def _get_vehicle_positions_request(
        self,
        route_ids: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Get vehicle positions request"""
        pass

    @abstractmethod
    async def _get_alerts_request(
        self,
        route_ids: list[str] | None,
        stop_ids: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Get alerts request"""
        pass

    async def get_arrivals(
        self,
        stop_id: str,
        route_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get real-time arrivals"""
        return await self._get_arrivals_request(stop_id, route_ids, limit)

    async def get_vehicle_positions(
        self,
        route_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get real-time vehicle positions"""
        return await self._get_vehicle_positions_request(route_ids)

    async def get_alerts(
        self,
        route_ids: list[str] | None = None,
        stop_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get service alerts"""
        return await self._get_alerts_request(route_ids, stop_ids)


class GTFSRealtimeAdapter(BaseRealtimeTransitAdapter):
    """GTFS-Realtime adapter"""

    def __init__(self, feed_url: str):
        self.feed_url = feed_url
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    async def _get_arrivals_request(
        self,
        stop_id: str,
        route_ids: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        session = await self._get_session()

        async with session.get(self.feed_url) as response:
            if response.status == 200:
                await response.read()
                # Parse GTFS-Realtime protobuf
                # This would require gtfs-realtime-bindings
                # Simplified implementation
                return []
        return []

    async def _get_vehicle_positions_request(
        self,
        route_ids: list[str] | None,
    ) -> list[dict[str, Any]]:
        return []

    async def _get_alerts_request(
        self,
        route_ids: list[str] | None,
        stop_ids: list[str] | None,
    ) -> list[dict[str, Any]]:
        return []

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class CityTransitAPIAdapter(BaseRealtimeTransitAdapter):
    """Generic city transit API adapter"""

    def __init__(self, base_url: str, api_key: str | None = None):
        self.base_url = base_url
        self.api_key = api_key
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def _get_arrivals_request(
        self,
        stop_id: str,
        route_ids: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        session = await self._get_session()

        url = f"{self.base_url}/stops/{stop_id}/arrivals"
        params = {"limit": limit}
        if route_ids:
            params["route_ids"] = ",".join(route_ids)

        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
        return []

    async def _get_vehicle_positions_request(
        self,
        route_ids: list[str] | None,
    ) -> list[dict[str, Any]]:
        session = await self._get_session()

        url = f"{self.base_url}/vehicles"
        params = {}
        if route_ids:
            params["route_ids"] = ",".join(route_ids)

        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
        return []

    async def _get_alerts_request(
        self,
        route_ids: list[str] | None,
        stop_ids: list[str] | None,
    ) -> list[dict[str, Any]]:
        session = await self._get_session()

        url = f"{self.base_url}/alerts"
        params = {}
        if route_ids:
            params["route_ids"] = ",".join(route_ids)
        if stop_ids:
            params["stop_ids"] = ",".join(stop_ids)

        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
        return []

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
