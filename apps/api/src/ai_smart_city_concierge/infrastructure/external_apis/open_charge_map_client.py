"""
OpenChargeMap API Client
Fetches EV charging station data from the OpenChargeMap API.
"""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from ...infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)


class OpenChargeMapClient:
    """Client for the OpenChargeMap API (v3)."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        settings = get_settings()
        self._api_key = api_key or settings.external.openchargemap_api_key
        self._base_url = base_url or settings.external.openchargemap_url
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_charging_stations(
        self,
        latitude: float,
        longitude: float,
        distance_km: float = 10.0,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch nearby EV charging stations."""
        session = await self._get_session()

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "distance": distance_km,
            "distanceunit": "km",
            "maxresults": max_results,
        }

        headers = {}
        if self._api_key:
            headers["X-API-Key"] = self._api_key

        url = f"{self._base_url}/poi"

        try:
            async with session.get(url, params=params, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as exc:
            logger.error("OpenChargeMap request failed: %s", exc)
            return []

    async def get_station_by_id(self, station_id: int) -> dict[str, Any] | None:
        """Fetch a single charging station by ID."""
        session = await self._get_session()

        headers = {}
        if self._api_key:
            headers["X-API-Key"] = self._api_key

        url = f"{self._base_url}/poi"

        try:
            async with session.get(url, params={"chargepointid": station_id}, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data[0] if data else None
        except aiohttp.ClientError as exc:
            logger.error("OpenChargeMap request failed: %s", exc)
            return None
