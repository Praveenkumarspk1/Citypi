"""
Geocoding Service Adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ....application.ports.external_services import GeocodingServicePort
from ....domain.value_objects.coordinates import Coordinates


@dataclass
class GeocodingResult:
    """Geocoding result"""
    coordinates: Coordinates
    address: str
    place_id: str
    confidence: float


class BaseGeocodingAdapter(GeocodingServicePort, ABC):
    """Base geocoding adapter"""

    @abstractmethod
    async def _geocode_request(self, address: str) -> GeocodingResult | None:
        """Make geocoding request"""
        pass

    @abstractmethod
    async def _reverse_geocode_request(self, coordinates: Coordinates) -> str | None:
        """Make reverse geocoding request"""
        pass

    @abstractmethod
    async def _autocomplete_request(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Make autocomplete request"""
        pass

    async def geocode(self, address: str) -> Coordinates | None:
        """Convert address to coordinates"""
        result = await self._geocode_request(address)
        return result.coordinates if result else None

    async def reverse_geocode(self, coordinates: Coordinates) -> str | None:
        """Convert coordinates to address"""
        return await self._reverse_geocode_request(coordinates)

    async def autocomplete(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Autocomplete address suggestions"""
        return await self._autocomplete_request(query, limit)


class OpenStreetMapGeocodingAdapter(BaseGeocodingAdapter):
    """OpenStreetMap Nominatim geocoding adapter"""

    def __init__(self, base_url: str = "https://nominatim.openstreetmap.org", user_agent: str = "AI-Smart-City-Concierge"):
        self.base_url = base_url
        self.user_agent = user_agent
        self._session = None

    async def _get_session(self):
        """Get aiohttp session"""
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent}
            )
        return self._session

    async def _geocode_request(self, address: str) -> GeocodingResult | None:
        session = await self._get_session()
        url = f"{self.base_url}/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    result = data[0]
                    return GeocodingResult(
                        coordinates=Coordinates(
                            latitude=float(result["lat"]),
                            longitude=float(result["lon"]),
                        ),
                        address=result.get("display_name", address),
                        place_id=result.get("place_id", ""),
                        confidence=float(result.get("importance", 0)),
                    )
        return None

    async def _reverse_geocode_request(self, coordinates: Coordinates) -> str | None:
        session = await self._get_session()
        url = f"{self.base_url}/reverse"
        params = {
            "lat": coordinates.latitude,
            "lon": coordinates.longitude,
            "format": "json",
            "addressdetails": 1,
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("display_name")
        return None

    async def _autocomplete_request(self, query: str, limit: int) -> list[dict[str, Any]]:
        session = await self._get_session()
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "format": "json",
            "limit": limit,
            "addressdetails": 1,
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return [
                    {
                        "place_id": item.get("place_id"),
                        "address": item.get("display_name"),
                        "coordinates": {
                            "latitude": float(item["lat"]),
                            "longitude": float(item["lon"]),
                        },
                        "type": item.get("type"),
                        "importance": float(item.get("importance", 0)),
                    }
                    for item in data
                ]
        return []

    async def close(self):
        """Close session"""
        if self._session:
            await self._session.close()
            self._session = None


class GoogleMapsGeocodingAdapter(BaseGeocodingAdapter):
    """Google Maps Geocoding API adapter"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    async def _geocode_request(self, address: str) -> GeocodingResult | None:
        session = await self._get_session()
        params = {
            "address": address,
            "key": self.api_key,
        }

        async with session.get(self.base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["status"] == "OK" and data["results"]:
                    result = data["results"][0]
                    location = result["geometry"]["location"]
                    return GeocodingResult(
                        coordinates=Coordinates(
                            latitude=location["lat"],
                            longitude=location["lng"],
                        ),
                        address=result["formatted_address"],
                        place_id=result["place_id"],
                        confidence=1.0,
                    )
        return None

    async def _reverse_geocode_request(self, coordinates: Coordinates) -> str | None:
        session = await self._get_session()
        params = {
            "latlng": f"{coordinates.latitude},{coordinates.longitude}",
            "key": self.api_key,
        }

        async with session.get(self.base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["status"] == "OK" and data["results"]:
                    return data["results"][0]["formatted_address"]
        return None

    async def _autocomplete_request(self, query: str, limit: int) -> list[dict[str, Any]]:
        # Google Places Autocomplete would be a different endpoint
        # This is a simplified implementation
        return []

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class MapboxGeocodingAdapter(BaseGeocodingAdapter):
    """Mapbox Geocoding API adapter"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places"
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    async def _geocode_request(self, address: str) -> GeocodingResult | None:
        session = await self._get_session()
        url = f"{self.base_url}/{address}.json"
        params = {
            "access_token": self.access_token,
            "limit": 1,
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["features"]:
                    feature = data["features"][0]
                    coords = feature["center"]
                    return GeocodingResult(
                        coordinates=Coordinates(
                            latitude=coords[1],
                            longitude=coords[0],
                        ),
                        address=feature["place_name"],
                        place_id=feature["id"],
                        confidence=feature.get("relevance", 0),
                    )
        return None

    async def _reverse_geocode_request(self, coordinates: Coordinates) -> str | None:
        session = await self._get_session()
        url = f"{self.base_url}/{coordinates.longitude},{coordinates.latitude}.json"
        params = {
            "access_token": self.access_token,
            "limit": 1,
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["features"]:
                    return data["features"][0]["place_name"]
        return None

    async def _autocomplete_request(self, query: str, limit: int) -> list[dict[str, Any]]:
        session = await self._get_session()
        url = f"{self.base_url}/{query}.json"
        params = {
            "access_token": self.access_token,
            "limit": limit,
            "autocomplete": "true",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return [
                    {
                        "place_id": feature["id"],
                        "address": feature["place_name"],
                        "coordinates": {
                            "latitude": feature["center"][1],
                            "longitude": feature["center"][0],
                        },
                        "type": feature.get("place_type", []),
                        "relevance": feature.get("relevance", 0),
                    }
                    for feature in data["features"]
                ]
        return []

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
