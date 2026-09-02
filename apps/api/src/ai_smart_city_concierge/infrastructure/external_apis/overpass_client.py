"""
Overpass API Client for OpenStreetMap data
"""
from dataclasses import dataclass
from typing import Any

import aiohttp

from ...application.ports.external_services import PlacesServicePort
from ...domain.entities.poi import POI, POICategory, POISource
from ...domain.value_objects.coordinates import Coordinates


@dataclass
class OverpassConfig:
    """Overpass API configuration"""
    endpoint: str = "https://overpass-api.de/api/interpreter"
    timeout: int = 30
    max_results: int = 100


class OverpassClient(PlacesServicePort):
    """Overpass API client for querying OpenStreetMap data"""

    # OSM tag to POI category mapping
    CATEGORY_TAGS = {
        POICategory.RESTAURANT: ["amenity=restaurant", "amenity=cafe", "amenity=fast_food"],
        POICategory.HOTEL: ["tourism=hotel", "tourism=hostel", "tourism=guest_house"],
        POICategory.ATTRACTION: ["tourism=attraction", "tourism=museum", "tourism=artwork"],
        POICategory.SHOP: ["shop=*"],
        POICategory.PARK: ["leisure=park", "leisure=garden", "leisure=nature_reserve"],
        POICategory.TRANSIT_STOP: ["highway=bus_stop", "railway=station", "railway=subway_entrance"],
        POICategory.HEALTHCARE: ["amenity=hospital", "amenity=clinic", "amenity=pharmacy"],
        POICategory.EDUCATION: ["amenity=school", "amenity=university", "amenity=college"],
        POICategory.ENTERTAINMENT: ["amenity=cinema", "amenity=theatre", "amenity=nightclub"],
        POICategory.FUEL: ["amenity=fuel", "amenity=charging_station"],
        POICategory.PARKING: ["amenity=parking"],
        POICategory.PUBLIC_FACILITY: ["amenity=toilets", "amenity=drinking_water", "amenity=post_box"],
    }

    def __init__(self, config: OverpassConfig | None = None):
        self.config = config or OverpassConfig()
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

    def _build_query(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        category: POICategory | None = None,
        query: str | None = None,
        bbox: tuple | None = None,
    ) -> str:
        """Build Overpass QL query"""
        parts = ["[out:json][timeout:25];"]

        # Area filter
        if bbox:
            # bbox: (south, west, north, east)
            parts.append(f"({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});")
        elif coordinates and radius_meters:
            parts.append(f"({coordinates.latitude},{coordinates.longitude},{radius_meters});")
        else:
            # Default to world (will be limited by max_results)
            parts.append("({{bbox}});")

        # Tag filters
        if query:
            # Text search in name, description, etc.
            parts.append(f'["name"~"{query}",i];')
        elif category and category in self.CATEGORY_TAGS:
            tag_filters = "[" + "][".join(self.CATEGORY_TAGS[category]) + "];"
            parts.append(tag_filters)

        # Output
        parts.append("out center meta;")

        return "".join(parts)

    async def _execute_query(self, query: str) -> dict[str, Any]:
        """Execute Overpass query"""
        session = await self._get_session()

        async with session.post(
            self.config.endpoint,
            data={"data": query},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as response:
            response.raise_for_status()
            return await response.json()

    def _parse_element(self, element: dict[str, Any]) -> POI | None:
        """Parse Overpass element to POI"""
        try:
            tags = element.get("tags", {})

            # Get coordinates
            if element["type"] == "node":
                lat = element["lat"]
                lon = element["lon"]
            elif "center" in element:
                lat = element["center"]["lat"]
                lon = element["center"]["lon"]
            else:
                return None

            coordinates = Coordinates(latitude=lat, longitude=lon)

            # Determine category
            category = POICategory.OTHER
            for cat, tag_list in self.CATEGORY_TAGS.items():
                for tag in tag_list:
                    key, value = tag.split("=") if "=" in tag else (tag, "*")
                    if key in tags:
                        if value == "*" or tags[key] == value:
                            category = cat
                            break
                if category != POICategory.OTHER:
                    break

            # Build address
            address_parts = []
            for key in ["addr:housenumber", "addr:street", "addr:city", "addr:postcode", "addr:country"]:
                if key in tags:
                    address_parts.append(tags[key])
            address = ", ".join(address_parts) if address_parts else None

            # Contact info
            contact = {}
            for key in ["phone", "email", "website", "contact:phone", "contact:email", "contact:website"]:
                if key in tags:
                    contact[key.replace("contact:", "")] = tags[key]

            # Opening hours
            tags.get("opening_hours")

            # Create POI
            poi = POI(
                name=tags.get("name", "Unnamed"),
                name_local=tags.get("name:local", tags.get("name:en")),
                description=tags.get("description"),
                category=category,
                subcategory=tags.get("cuisine") or tags.get("shop") or tags.get("tourism"),
                tags=[k for k in tags.keys() if not k.startswith("addr:") and not k.startswith("contact:")],
                coordinates=coordinates,
                address=address,
                city=tags.get("addr:city"),
                state=tags.get("addr:state"),
                country=tags.get("addr:country"),
                postal_code=tags.get("addr:postcode"),
                external_id=f"osm_{element['type']}_{element['id']}",
                source=POISource.OPENSTREETMAP,
            )

            return poi
        except Exception:
            return None

    async def search_places(
        self,
        query: str,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        category: str | None = None,
        limit: int = 20,
    ) -> list[POI]:
        """Search for places"""
        poi_category = None
        if category:
            try:
                poi_category = POICategory(category.upper())
            except ValueError:
                pass

        query_str = self._build_query(
            coordinates=coordinates,
            radius_meters=radius_meters,
            category=poi_category,
            query=query,
        )

        result = await self._execute_query(query_str)

        pois = []
        for element in result.get("elements", [])[:limit]:
            poi = self._parse_element(element)
            if poi:
                pois.append(poi)

        return pois

    async def get_place_details(self, place_id: str) -> POI | None:
        """Get detailed place information"""
        # Extract OSM ID from place_id (format: osm_type_id)
        if not place_id.startswith("osm_"):
            return None

        parts = place_id.split("_")
        if len(parts) != 3:
            return None

        element_type = parts[1]
        element_id = parts[2]

        query = f"[out:json];{element_type}({element_id});out center meta;"
        result = await self._execute_query(query)

        for element in result.get("elements", []):
            return self._parse_element(element)

        return None

    async def get_place_photos(self, place_id: str, max_photos: int = 10) -> list[str]:
        """Get place photos (not directly available from Overpass)"""
        # Overpass doesn't provide photos directly
        # Could integrate with Wikimedia or other photo services
        return []

    async def get_place_reviews(self, place_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get place reviews (not available from Overpass)"""
        return []

    async def get_nearby_pois(
        self,
        coordinates: Coordinates,
        radius_meters: float = 1000,
        categories: list[POICategory] | None = None,
        limit: int = 50,
    ) -> list[POI]:
        """Get nearby POIs"""
        all_pois = []

        if categories:
            for category in categories:
                query = self._build_query(
                    coordinates=coordinates,
                    radius_meters=radius_meters,
                    category=category,
                )
                result = await self._execute_query(query)

                for element in result.get("elements", []):
                    poi = self._parse_element(element)
                    if poi:
                        all_pois.append(poi)
        else:
            # Search all categories
            query = self._build_query(
                coordinates=coordinates,
                radius_meters=radius_meters,
            )
            result = await self._execute_query(query)

            for element in result.get("elements", [])[:limit]:
                poi = self._parse_element(element)
                if poi:
                    all_pois.append(poi)

        # Deduplicate by external_id
        seen = set()
        unique_pois = []
        for poi in all_pois:
            if poi.external_id not in seen:
                seen.add(poi.external_id)
                unique_pois.append(poi)

        return unique_pois[:limit]

    async def search_by_bbox(
        self,
        bbox: tuple,  # (south, west, north, east)
        category: POICategory | None = None,
        limit: int = 100,
    ) -> list[POI]:
        """Search POIs within bounding box"""
        query = self._build_query(bbox=bbox, category=category)
        result = await self._execute_query(query)

        pois = []
        for element in result.get("elements", [])[:limit]:
            poi = self._parse_element(element)
            if poi:
                pois.append(poi)

        return pois
