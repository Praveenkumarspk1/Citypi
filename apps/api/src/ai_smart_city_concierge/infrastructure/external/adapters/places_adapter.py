"""
Places Service Adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ....application.ports.external_services import PlacesServicePort
from ....domain.entities.poi import POI, POICategory, POISource
from ....domain.value_objects.coordinates import Coordinates


@dataclass
class PlaceResult:
    """Place search result"""
    poi: POI
    relevance: float


class BasePlacesAdapter(PlacesServicePort, ABC):
    """Base places adapter"""

    @abstractmethod
    async def _search_places_request(
        self,
        query: str,
        coordinates: Coordinates | None,
        radius_meters: float | None,
        category: str | None,
        limit: int,
    ) -> list[PlaceResult]:
        """Search places request"""
        pass

    @abstractmethod
    async def _get_place_details_request(self, place_id: str) -> POI | None:
        """Get place details request"""
        pass

    @abstractmethod
    async def _get_place_photos_request(self, place_id: str, max_photos: int) -> list[str]:
        """Get place photos request"""
        pass

    @abstractmethod
    async def _get_place_reviews_request(self, place_id: str, limit: int) -> list[dict[str, Any]]:
        """Get place reviews request"""
        pass

    async def search_places(
        self,
        query: str,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        category: str | None = None,
        limit: int = 20,
    ) -> list[POI]:
        """Search for places"""
        results = await self._search_places_request(query, coordinates, radius_meters, category, limit)
        return [r.poi for r in results]

    async def get_place_details(self, place_id: str) -> POI | None:
        """Get detailed place information"""
        return await self._get_place_details_request(place_id)

    async def get_place_photos(self, place_id: str, max_photos: int = 10) -> list[str]:
        """Get place photos"""
        return await self._get_place_photos_request(place_id, max_photos)

    async def get_place_reviews(self, place_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get place reviews"""
        return await self._get_place_reviews_request(place_id, limit)


class GooglePlacesAdapter(BasePlacesAdapter):
    """Google Places API adapter"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    def _category_to_type(self, category: str | None) -> str | None:
        if not category:
            return None
        type_map = {
            "restaurant": "restaurant",
            "cafe": "cafe",
            "bar": "bar",
            "hotel": "lodging",
            "museum": "museum",
            "park": "park",
            "shopping_mall": "shopping_mall",
            "supermarket": "supermarket",
            "pharmacy": "pharmacy",
            "hospital": "hospital",
            "bank": "bank",
            "atm": "atm",
            "gas_station": "gas_station",
            "parking": "parking",
            "subway_station": "subway_station",
            "bus_station": "bus_station",
            "train_station": "train_station",
            "airport": "airport",
        }
        return type_map.get(category.lower())

    async def _search_places_request(
        self,
        query: str,
        coordinates: Coordinates | None,
        radius_meters: float | None,
        category: str | None,
        limit: int,
    ) -> list[PlaceResult]:
        session = await self._get_session()

        url = f"{self.base_url}/textsearch/json"
        params = {
            "query": query,
            "key": self.api_key,
        }

        if coordinates and radius_meters:
            params["location"] = f"{coordinates.latitude},{coordinates.longitude}"
            params["radius"] = min(int(radius_meters), 50000)

        if category:
            place_type = self._category_to_type(category)
            if place_type:
                params["type"] = place_type

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["status"] == "OK":
                    results = []
                    for item in data["results"][:limit]:
                        poi = self._parse_place(item)
                        if poi:
                            results.append(PlaceResult(poi=poi, relevance=1.0))
                    return results
        return []

    async def _get_place_details_request(self, place_id: str) -> POI | None:
        session = await self._get_session()

        url = f"{self.base_url}/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,geometry,types,rating,user_ratings_total,price_level,opening_hours,photos,reviews,website,formatted_phone_number,international_phone_number,url,editorial_summary",
            "key": self.api_key,
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["status"] == "OK":
                    return self._parse_place(data["result"], detailed=True)
        return None

    async def _get_place_photos_request(self, place_id: str, max_photos: int) -> list[str]:
        session = await self._get_session()

        url = f"{self.base_url}/details/json"
        params = {
            "place_id": place_id,
            "fields": "photos",
            "key": self.api_key,
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["status"] == "OK" and "photos" in data["result"]:
                    photos = []
                    for photo in data["result"]["photos"][:max_photos]:
                        photo_ref = photo["photo_reference"]
                        photo_url = f"{self.base_url}/photo?maxwidth=800&photoreference={photo_ref}&key={self.api_key}"
                        photos.append(photo_url)
                    return photos
        return []

    async def _get_place_reviews_request(self, place_id: str, limit: int) -> list[dict[str, Any]]:
        session = await self._get_session()

        url = f"{self.base_url}/details/json"
        params = {
            "place_id": place_id,
            "fields": "reviews",
            "key": self.api_key,
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["status"] == "OK" and "reviews" in data["result"]:
                    return data["result"]["reviews"][:limit]
        return []

    def _parse_place(self, data: dict[str, Any], detailed: bool = False) -> POI | None:
        try:
            location = data.get("geometry", {}).get("location", {})
            coordinates = Coordinates(
                latitude=location.get("lat", 0),
                longitude=location.get("lng", 0),
            )

            # Map Google types to our categories
            types = data.get("types", [])
            category = self._map_types_to_category(types)

            # Parse opening hours
            opening_hours = None
            if "opening_hours" in data:
                oh = data["opening_hours"]
                opening_hours = {
                    "periods": oh.get("periods", []),
                    "weekday_text": oh.get("weekday_text", []),
                }

            # Parse photos
            photos = []
            if "photos" in data:
                for photo in data["photos"][:10]:
                    photo_ref = photo["photo_reference"]
                    photos.append(f"{self.base_url}/photo?maxwidth=800&photoreference={photo_ref}&key={self.api_key}")

            return POI(
                name=data.get("name", ""),
                description=data.get("editorial_summary", {}).get("overview", "") if detailed else "",
                category=category,
                coordinates=coordinates,
                address=data.get("formatted_address"),
                phone=data.get("formatted_phone_number") or data.get("international_phone_number"),
                website=data.get("website") or data.get("url"),
                opening_hours=opening_hours,
                price_level=data.get("price_level"),
                rating=data.get("rating", 0.0),
                review_count=data.get("user_ratings_total", 0),
                photos=photos,
                source=POISource.GOOGLE_PLACES,
                external_id=data.get("place_id"),
                tags=types,
            )
        except Exception:
            return None

    def _map_types_to_category(self, types: list[str]) -> POICategory:
        type_priority = {
            "restaurant": POICategory.RESTAURANT,
            "cafe": POICategory.CAFE,
            "bar": POICategory.BAR,
            "lodging": POICategory.HOTEL,
            "hotel": POICategory.HOTEL,
            "museum": POICategory.MUSEUM,
            "art_gallery": POICategory.ATTRACTION,
            "tourist_attraction": POICategory.ATTRACTION,
            "park": POICategory.PARK,
            "shopping_mall": POICategory.SHOPPING,
            "store": POICategory.SHOPPING,
            "supermarket": POICategory.SHOPPING,
            "pharmacy": POICategory.PHARMACY,
            "hospital": POICategory.HOSPITAL,
            "doctor": POICategory.HOSPITAL,
            "bank": POICategory.BANK,
            "atm": POICategory.ATM,
            "gas_station": POICategory.GAS_STATION,
            "parking": POICategory.PARKING,
            "subway_station": POICategory.TRANSIT_STOP,
            "bus_station": POICategory.TRANSIT_STOP,
            "train_station": POICategory.TRANSIT_STOP,
            "airport": POICategory.AIRPORT,
        }

        for t in types:
            if t in type_priority:
                return type_priority[t]

        return POICategory.OTHER

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class FoursquarePlacesAdapter(BasePlacesAdapter):
    """Foursquare Places API adapter"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.foursquare.com/v3/places"
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": self.api_key,
                    "Accept": "application/json",
                }
            )
        return self._session

    async def _search_places_request(
        self,
        query: str,
        coordinates: Coordinates | None,
        radius_meters: float | None,
        category: str | None,
        limit: int,
    ) -> list[PlaceResult]:
        session = await self._get_session()

        url = f"{self.base_url}/search"
        params = {
            "query": query,
            "limit": limit,
        }

        if coordinates and radius_meters:
            params["ll"] = f"{coordinates.latitude},{coordinates.longitude}"
            params["radius"] = min(int(radius_meters), 100000)

        if category:
            params["categories"] = self._category_to_foursquare(category)

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                results = []
                for item in data.get("results", []):
                    poi = self._parse_place(item)
                    if poi:
                        results.append(PlaceResult(poi=poi, relevance=1.0))
                return results
        return []

    async def _get_place_details_request(self, place_id: str) -> POI | None:
        session = await self._get_session()

        url = f"{self.base_url}/{place_id}"
        params = {
            "fields": "name,location,geocodes,categories,rating,price,stats,photos,tips,website,tel,email,hours,description",
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_place(data, detailed=True)
        return None

    async def _get_place_photos_request(self, place_id: str, max_photos: int) -> list[str]:
        session = await self._get_session()

        url = f"{self.base_url}/{place_id}/photos"
        params = {"limit": max_photos}

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                photos = []
                for photo in data:
                    prefix = photo.get("prefix", "")
                    suffix = photo.get("suffix", "")
                    photos.append(f"{prefix}original{suffix}")
                return photos
        return []

    async def _get_place_reviews_request(self, place_id: str, limit: int) -> list[dict[str, Any]]:
        session = await self._get_session()

        url = f"{self.base_url}/{place_id}/tips"
        params = {"limit": limit}

        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data
        return []

    def _parse_place(self, data: dict[str, Any], detailed: bool = False) -> POI | None:
        try:
            geocodes = data.get("geocodes", {}).get("main", {})
            coordinates = Coordinates(
                latitude=geocodes.get("latitude", 0),
                longitude=geocodes.get("longitude", 0),
            )

            location = data.get("location", {})
            address_parts = [
                location.get("address"),
                location.get("locality"),
                location.get("region"),
                location.get("postcode"),
                location.get("country"),
            ]
            address = ", ".join([p for p in address_parts if p])

            categories = data.get("categories", [])
            category = self._map_foursquare_category(categories)

            photos = []
            if "photos" in data:
                for photo in data["photos"][:10]:
                    prefix = photo.get("prefix", "")
                    suffix = photo.get("suffix", "")
                    photos.append(f"{prefix}original{suffix}")

            return POI(
                name=data.get("name", ""),
                description=data.get("description", "") if detailed else "",
                category=category,
                coordinates=coordinates,
                address=address,
                phone=data.get("tel"),
                email=data.get("email"),
                website=data.get("website"),
                price_level=self._price_to_level(data.get("price")),
                rating=data.get("rating", 0.0),
                review_count=data.get("stats", {}).get("total_tips", 0),
                photos=photos,
                source=POISource.FOURSQUARE,
                external_id=data.get("fsq_id"),
                tags=[c["name"] for c in categories],
            )
        except Exception:
            return None

    def _category_to_foursquare(self, category: str) -> str:
        category_map = {
            "restaurant": "13065",
            "cafe": "13032",
            "bar": "13003",
            "hotel": "19014",
            "museum": "10027",
            "park": "16038",
            "shopping_mall": "17069",
        }
        return category_map.get(category.lower(), "")

    def _map_foursquare_category(self, categories: list[dict]) -> POICategory:
        category_map = {
            "13065": POICategory.RESTAURANT,
            "13032": POICategory.CAFE,
            "13003": POICategory.BAR,
            "19014": POICategory.HOTEL,
            "10027": POICategory.MUSEUM,
            "16038": POICategory.PARK,
            "17069": POICategory.SHOPPING,
        }

        for cat in categories:
            cat_id = cat.get("id", "")
            if cat_id in category_map:
                return category_map[cat_id]

        return POICategory.OTHER

    def _price_to_level(self, price: int | None) -> int | None:
        if price is None:
            return None
        return min(max(price, 1), 4)

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


class OpenStreetMapPlacesAdapter(BasePlacesAdapter):
    """OpenStreetMap Overpass API adapter"""

    def __init__(self, base_url: str = "https://overpass-api.de/api/interpreter"):
        self.base_url = base_url
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    async def _search_places_request(
        self,
        query: str,
        coordinates: Coordinates | None,
        radius_meters: float | None,
        category: str | None,
        limit: int,
    ) -> list[PlaceResult]:
        session = await self._get_session()

        # Build Overpass query
        if coordinates and radius_meters:
            bbox = self._get_bbox(coordinates, radius_meters)
            query_str = f"""
            [out:json][timeout:25];
            (
              node["name"~"{query}",i]({bbox});
              way["name"~"{query}",i]({bbox});
              relation["name"~"{query}",i]({bbox});
            );
            out center {limit};
            """
        else:
            query_str = f"""
            [out:json][timeout:25];
            (
              node["name"~"{query}",i];
              way["name"~"{query}",i];
              relation["name"~"{query}",i];
            );
            out center {limit};
            """

        async with session.post(self.base_url, data=query_str) as response:
            if response.status == 200:
                data = await response.json()
                results = []
                for element in data.get("elements", []):
                    poi = self._parse_element(element)
                    if poi:
                        results.append(PlaceResult(poi=poi, relevance=1.0))
                return results
        return []

    async def _get_place_details_request(self, place_id: str) -> POI | None:
        # OSM doesn't have a direct details endpoint like Google
        # Would need to query by ID
        return None

    async def _get_place_photos_request(self, place_id: str, max_photos: int) -> list[str]:
        # OSM doesn't have photos directly
        return []

    async def _get_place_reviews_request(self, place_id: str, limit: int) -> list[dict[str, Any]]:
        # OSM doesn't have reviews
        return []

    def _get_bbox(self, coordinates: Coordinates, radius_meters: float) -> str:
        # Approximate bounding box
        deg_per_km = 1 / 111.0
        radius_deg = (radius_meters / 1000.0) * deg_per_km
        return f"{coordinates.latitude - radius_deg},{coordinates.longitude - radius_deg},{coordinates.latitude + radius_deg},{coordinates.longitude + radius_deg}"

    def _parse_element(self, element: dict[str, Any]) -> POI | None:
        try:
            tags = element.get("tags", {})

            if element["type"] == "node":
                coordinates = Coordinates(
                    latitude=element["lat"],
                    longitude=element["lon"],
                )
            elif "center" in element:
                coordinates = Coordinates(
                    latitude=element["center"]["lat"],
                    longitude=element["center"]["lon"],
                )
            else:
                return None

            category = self._map_osm_tags_to_category(tags)

            address_parts = [
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:city"),
                tags.get("addr:postcode"),
                tags.get("addr:country"),
            ]
            address = " ".join([p for p in address_parts if p]) or None

            return POI(
                name=tags.get("name", ""),
                description="",
                category=category,
                coordinates=coordinates,
                address=address,
                phone=tags.get("phone"),
                website=tags.get("website"),
                opening_hours=tags.get("opening_hours"),
                source=POISource.OPENSTREETMAP,
                external_id=f"{element['type']}/{element['id']}",
                tags={k: v for k, v in tags.items() if k not in ["name", "phone", "website", "opening_hours"]},
            )
        except Exception:
            return None

    def _map_osm_tags_to_category(self, tags: dict[str, str]) -> POICategory:
        # Map OSM tags to categories
        if tags.get("amenity") == "restaurant":
            return POICategory.RESTAURANT
        elif tags.get("amenity") == "cafe":
            return POICategory.CAFE
        elif tags.get("amenity") == "bar":
            return POICategory.BAR
        elif tags.get("amenity") == "pub":
            return POICategory.BAR
        elif tags.get("tourism") == "hotel":
            return POICategory.HOTEL
        elif tags.get("tourism") == "museum":
            return POICategory.MUSEUM
        elif tags.get("tourism") == "attraction":
            return POICategory.ATTRACTION
        elif tags.get("leisure") == "park":
            return POICategory.PARK
        elif tags.get("shop") == "mall":
            return POICategory.SHOPPING
        elif tags.get("amenity") == "pharmacy":
            return POICategory.PHARMACY
        elif tags.get("amenity") == "hospital":
            return POICategory.HOSPITAL
        elif tags.get("amenity") == "bank":
            return POICategory.BANK
        elif tags.get("amenity") == "atm":
            return POICategory.ATM
        elif tags.get("amenity") == "fuel":
            return POICategory.GAS_STATION
        elif tags.get("amenity") == "parking":
            return POICategory.PARKING
        elif tags.get("public_transport") == "station":
            return POICategory.TRANSIT_STOP
        elif tags.get("aeroway") == "aerodrome":
            return POICategory.AIRPORT

        return POICategory.OTHER

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
