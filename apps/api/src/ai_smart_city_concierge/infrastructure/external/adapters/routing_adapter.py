"""
Routing Service Adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ....application.ports.external_services import RoutingServicePort
from ....domain.value_objects.coordinates import Coordinates


@dataclass
class RouteResult:
    """Route result"""
    distance_meters: float
    duration_seconds: float
    geometry: dict[str, Any]
    steps: list[dict[str, Any]]


class BaseRoutingAdapter(RoutingServicePort, ABC):
    """Base routing adapter"""

    @abstractmethod
    async def _route_request(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: str,
        alternatives: bool,
    ) -> RouteResult | None:
        """Make routing request"""
        pass

    @abstractmethod
    async def _matrix_request(
        self,
        origins: list[Coordinates],
        destinations: list[Coordinates],
        mode: str,
    ) -> dict[str, Any]:
        """Make matrix request"""
        pass

    @abstractmethod
    async def _isochrone_request(
        self,
        center: Coordinates,
        time_minutes: float,
        mode: str,
    ) -> dict[str, Any]:
        """Make isochrone request"""
        pass

    async def get_route(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: str = "walking",
        alternatives: bool = False,
    ) -> dict[str, Any]:
        """Get route between two points"""
        result = await self._route_request(origin, destination, mode, alternatives)
        if result:
            return {
                "distance_meters": result.distance_meters,
                "duration_seconds": result.duration_seconds,
                "geometry": result.geometry,
                "steps": result.steps,
            }
        return {}

    async def get_matrix(
        self,
        origins: list[Coordinates],
        destinations: list[Coordinates],
        mode: str = "walking",
    ) -> dict[str, Any]:
        """Get distance/duration matrix"""
        return await self._matrix_request(origins, destinations, mode)

    async def get_isochrone(
        self,
        center: Coordinates,
        time_minutes: float,
        mode: str = "walking",
    ) -> dict[str, Any]:
        """Get isochrone (reachable area)"""
        return await self._isochrone_request(center, time_minutes, mode)


class OSRMAdapter(BaseRoutingAdapter):
    """OSRM (Open Source Routing Machine) adapter"""

    def __init__(self, base_url: str = "http://router.project-osrm.org"):
        self.base_url = base_url
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    def _coords_to_string(self, coords: Coordinates) -> str:
        return f"{coords.longitude},{coords.latitude}"

    async def _route_request(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: str,
        alternatives: bool,
    ) -> RouteResult | None:
        session = await self._get_session()

        # Map mode to OSRM profile
        profile_map = {
            "walking": "foot",
            "cycling": "bike",
            "driving": "car",
        }
        profile = profile_map.get(mode, "foot")

        url = f"{self.base_url}/route/v1/{profile}/{self._coords_to_string(origin)};{self._coords_to_string(destination)}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
            "alternatives": "true" if alternatives else "false",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["code"] == "Ok" and data["routes"]:
                    route = data["routes"][0]
                    return RouteResult(
                        distance_meters=route["distance"],
                        duration_seconds=route["duration"],
                        geometry=route["geometry"],
                        steps=route["legs"][0]["steps"] if route["legs"] else [],
                    )
        return None

    async def _matrix_request(
        self,
        origins: list[Coordinates],
        destinations: list[Coordinates],
        mode: str,
    ) -> dict[str, Any]:
        session = await self._get_session()

        profile_map = {
            "walking": "foot",
            "cycling": "bike",
            "driving": "car",
        }
        profile = profile_map.get(mode, "foot")

        # Build coordinates string
        all_coords = origins + destinations
        coords_str = ";".join([self._coords_to_string(c) for c in all_coords])

        url = f"{self.base_url}/table/v1/{profile}/{coords_str}"
        params = {
            "sources": ";".join([str(i) for i in range(len(origins))]),
            "destinations": ";".join([str(i) for i in range(len(origins), len(all_coords))]),
            "annotations": "distance,duration",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["code"] == "Ok":
                    return {
                        "distances": data["distances"],
                        "durations": data["durations"],
                    }
        return {"distances": [], "durations": []}

    async def _isochrone_request(
        self,
        center: Coordinates,
        time_minutes: float,
        mode: str,
    ) -> dict[str, Any]:
        # OSRM doesn't have built-in isochrone, would need a separate service
        # This is a placeholder
        return {"geometry": None, "properties": {}}

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class ValhallaAdapter(BaseRoutingAdapter):
    """Valhalla routing adapter"""

    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    def _mode_to_costing(self, mode: str) -> str:
        costing_map = {
            "walking": "pedestrian",
            "cycling": "bicycle",
            "driving": "auto",
            "transit": "multimodal",
        }
        return costing_map.get(mode, "pedestrian")

    async def _route_request(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: str,
        alternatives: bool,
    ) -> RouteResult | None:
        session = await self._get_session()

        url = f"{self.base_url}/route"
        payload = {
            "locations": [
                {"lat": origin.latitude, "lon": origin.longitude},
                {"lat": destination.latitude, "lon": destination.longitude},
            ],
            "costing": self._mode_to_costing(mode),
            "directions_options": {
                "units": "kilometers",
            },
            "shape_match": "map_snap",
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                if "trip" in data:
                    trip = data["trip"]
                    legs = trip.get("legs", [])
                    if legs:
                        leg = legs[0]
                        return RouteResult(
                            distance_meters=leg["summary"]["length"] * 1000,
                            duration_seconds=leg["summary"]["time"],
                            geometry={"type": "LineString", "coordinates": []},  # Would decode polyline
                            steps=leg.get("maneuvers", []),
                        )
        return None

    async def _matrix_request(
        self,
        origins: list[Coordinates],
        destinations: list[Coordinates],
        mode: str,
    ) -> dict[str, Any]:
        # Valhalla has a separate matrix endpoint
        return {"distances": [], "durations": []}

    async def _isochrone_request(
        self,
        center: Coordinates,
        time_minutes: float,
        mode: str,
    ) -> dict[str, Any]:
        session = await self._get_session()

        url = f"{self.base_url}/isochrone"
        payload = {
            "locations": [{"lat": center.latitude, "lon": center.longitude}],
            "costing": self._mode_to_costing(mode),
            "contours": [{"time": time_minutes, "color": "ff0000"}],
            "polygons": True,
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
        return {"geometry": None, "properties": {}}

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class GoogleMapsRoutingAdapter(BaseRoutingAdapter):
    """Google Maps Directions API adapter"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"
        self.matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    def _mode_to_travel_mode(self, mode: str) -> str:
        mode_map = {
            "walking": "walking",
            "cycling": "bicycling",
            "driving": "driving",
            "transit": "transit",
        }
        return mode_map.get(mode, "walking")

    async def _route_request(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: str,
        alternatives: bool,
    ) -> RouteResult | None:
        session = await self._get_session()

        params = {
            "origin": f"{origin.latitude},{origin.longitude}",
            "destination": f"{destination.latitude},{destination.longitude}",
            "mode": self._mode_to_travel_mode(mode),
            "alternatives": "true" if alternatives else "false",
            "key": self.api_key,
        }

        async with session.get(self.base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["status"] == "OK" and data["routes"]:
                    route = data["routes"][0]
                    leg = route["legs"][0]
                    return RouteResult(
                        distance_meters=leg["distance"]["value"],
                        duration_seconds=leg["duration"]["value"],
                        geometry={"type": "LineString", "coordinates": []},  # Would decode polyline
                        steps=leg["steps"],
                    )
        return None

    async def _matrix_request(
        self,
        origins: list[Coordinates],
        destinations: list[Coordinates],
        mode: str,
    ) -> dict[str, Any]:
        session = await self._get_session()

        origins_str = "|".join([f"{c.latitude},{c.longitude}" for c in origins])
        destinations_str = "|".join([f"{c.latitude},{c.longitude}" for c in destinations])

        params = {
            "origins": origins_str,
            "destinations": destinations_str,
            "mode": self._mode_to_travel_mode(mode),
            "key": self.api_key,
        }

        async with session.get(self.matrix_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["status"] == "OK":
                    distances = []
                    durations = []
                    for row in data["rows"]:
                        dist_row = []
                        dur_row = []
                        for element in row["elements"]:
                            if element["status"] == "OK":
                                dist_row.append(element["distance"]["value"])
                                dur_row.append(element["duration"]["value"])
                            else:
                                dist_row.append(None)
                                dur_row.append(None)
                        distances.append(dist_row)
                        durations.append(dur_row)
                    return {"distances": distances, "durations": durations}
        return {"distances": [], "durations": []}

    async def _isochrone_request(
        self,
        center: Coordinates,
        time_minutes: float,
        mode: str,
    ) -> dict[str, Any]:
        # Google doesn't have isochrone API directly
        return {"geometry": None, "properties": {}}

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
