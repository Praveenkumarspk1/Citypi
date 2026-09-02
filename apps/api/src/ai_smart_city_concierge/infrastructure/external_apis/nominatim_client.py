"""
Nominatim Geocoding Client
"""
from dataclasses import dataclass
from typing import Any

import aiohttp

from ...application.ports.external_services import GeocodingServicePort
from ...domain.value_objects.coordinates import Coordinates


@dataclass
class NominatimConfig:
    """Nominatim configuration"""
    base_url: str = "https://nominatim.openstreetmap.org"
    user_agent: str = "AI-Smart-City-Concierge/1.0"
    timeout: int = 10
    rate_limit: float = 1.0  # requests per second


class NominatimClient(GeocodingServicePort):
    """Nominatim geocoding client (free, no API key required)"""

    def __init__(self, config: NominatimConfig | None = None):
        self.config = config or NominatimConfig()
        self._session: aiohttp.ClientSession | None = None
        self._last_request_time = 0.0

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": self.config.user_agent},
            )
        return self._session

    async def close(self) -> None:
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _rate_limit(self) -> None:
        """Enforce rate limiting"""
        import asyncio
        import time

        min_interval = 1.0 / self.config.rate_limit
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self._last_request_time = time.time()

    async def _make_request(self, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Make request to Nominatim API"""
        await self._rate_limit()

        session = await self._get_session()
        url = f"{self.config.base_url}{endpoint}"

        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def geocode(self, address: str) -> Coordinates | None:
        """Convert address to coordinates"""
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }

        results = await self._make_request("/search", params)

        if results:
            result = results[0]
            return Coordinates(
                latitude=float(result["lat"]),
                longitude=float(result["lon"]),
            )

        return None

    async def reverse_geocode(self, coordinates: Coordinates) -> str | None:
        """Convert coordinates to address"""
        params = {
            "lat": coordinates.latitude,
            "lon": coordinates.longitude,
            "format": "json",
            "addressdetails": 1,
            "zoom": 18,
        }

        result = await self._make_request("/reverse", params)

        if "display_name" in result:
            return result["display_name"]

        return None

    async def autocomplete(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Autocomplete address suggestions"""
        params = {
            "q": query,
            "format": "json",
            "limit": limit,
            "addressdetails": 1,
            "dedupe": 1,
        }

        results = await self._make_request("/search", params)

        suggestions = []
        for result in results:
            suggestions.append({
                "display_name": result.get("display_name", ""),
                "lat": float(result["lat"]),
                "lon": float(result["lon"]),
                "type": result.get("type", ""),
                "class": result.get("class", ""),
                "importance": result.get("importance", 0),
                "address": result.get("address", {}),
            })

        return suggestions

    async def structured_geocode(
        self,
        street: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        postal_code: str | None = None,
    ) -> Coordinates | None:
        """Geocode structured address components"""
        params = {
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }

        if street:
            params["street"] = street
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        if country:
            params["country"] = country
        if postal_code:
            params["postalcode"] = postal_code

        results = await self._make_request("/search", params)

        if results:
            result = results[0]
            return Coordinates(
                latitude=float(result["lat"]),
                longitude=float(result["lon"]),
            )

        return None

    async def search_nearby(
        self,
        coordinates: Coordinates,
        radius_meters: float = 1000,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for places near coordinates"""
        params = {
            "lat": coordinates.latitude,
            "lon": coordinates.longitude,
            "format": "json",
            "limit": limit,
            "addressdetails": 1,
            "accept-language": "en",
        }

        # Note: Nominatim doesn't directly support radius search
        # This uses the reverse geocode with zoom level approximation
        results = await self._make_request("/reverse", params)

        if isinstance(results, list):
            return results
        return [results] if results else []
