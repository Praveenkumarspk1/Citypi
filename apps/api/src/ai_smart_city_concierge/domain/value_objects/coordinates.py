"""
Coordinates Value Object
"""
import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Coordinates:
    """
    Immutable geographic coordinates (latitude, longitude).
    Uses WGS84 datum.
    """
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        """Validate coordinates after initialization"""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")

    def distance_to(self, other: "Coordinates") -> float:
        """
        Calculate distance to another coordinate using Haversine formula.
        Returns distance in meters.
        """
        R = 6371000  # Earth radius in meters

        lat1 = math.radians(self.latitude)
        lat2 = math.radians(other.latitude)
        dlat = math.radians(other.latitude - self.latitude)
        dlon = math.radians(other.longitude - self.longitude)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def distance_km_to(self, other: "Coordinates") -> float:
        """Distance in kilometers"""
        return self.distance_to(other) / 1000

    def bearing_to(self, other: "Coordinates") -> float:
        """
        Calculate initial bearing to another coordinate.
        Returns bearing in degrees (0-360).
        """
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(other.latitude)
        dlon = math.radians(other.longitude - self.longitude)

        y = math.sin(dlon) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2) -
             math.sin(lat1) * math.cos(lat2) * math.cos(dlon))

        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360

    def midpoint_to(self, other: "Coordinates") -> "Coordinates":
        """Calculate midpoint between two coordinates"""
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(other.latitude)
        dlon = math.radians(other.longitude - self.longitude)

        bx = math.cos(lat2) * math.cos(dlon)
        by = math.cos(lat2) * math.sin(dlon)

        lat3 = math.atan2(
            math.sin(lat1) + math.sin(lat2),
            math.sqrt((math.cos(lat1) + bx) ** 2 + by ** 2)
        )
        lon3 = math.radians(self.longitude) + math.atan2(
            by, math.cos(lat1) + bx
        )

        return Coordinates(
            latitude=math.degrees(lat3),
            longitude=math.degrees(lon3)
        )

    def is_within_radius(self, center: "Coordinates", radius_meters: float) -> bool:
        """Check if this coordinate is within radius of center"""
        return self.distance_to(center) <= radius_meters

    def to_tuple(self) -> tuple[float, float]:
        """Return as (lat, lng) tuple"""
        return (self.latitude, self.longitude)

    def to_lng_lat_tuple(self) -> tuple[float, float]:
        """Return as (lng, lat) tuple for GeoJSON"""
        return (self.longitude, self.latitude)

    def to_dict(self) -> dict:
        """Return as dictionary"""
        return {"lat": self.latitude, "lng": self.longitude}

    def to_geojson(self) -> dict:
        """Return as GeoJSON Point"""
        return {
            "type": "Point",
            "coordinates": [self.longitude, self.latitude]
        }

    @classmethod
    def from_tuple(cls, coords: tuple[float, float]) -> "Coordinates":
        """Create from (lat, lng) tuple"""
        return cls(latitude=coords[0], longitude=coords[1])

    @classmethod
    def from_lng_lat_tuple(cls, coords: tuple[float, float]) -> "Coordinates":
        """Create from (lng, lat) tuple"""
        return cls(latitude=coords[1], longitude=coords[0])

    @classmethod
    def from_dict(cls, data: dict) -> "Coordinates":
        """Create from dictionary with lat/lng keys"""
        return cls(
            latitude=data.get("lat", data.get("latitude", 0)),
            longitude=data.get("lng", data.get("longitude", 0))
        )

    @classmethod
    def from_geojson(cls, geojson: dict) -> "Coordinates":
        """Create from GeoJSON Point"""
        coords = geojson.get("coordinates", [0, 0])
        return cls(latitude=coords[1], longitude=coords[0])

    def __str__(self) -> str:
        return f"({self.latitude:.6f}, {self.longitude:.6f})"

    def __repr__(self) -> str:
        return f"Coordinates(latitude={self.latitude}, longitude={self.longitude})"


# Common coordinate constants
class KnownCoordinates:
    """Predefined coordinates for major cities"""
    SAN_FRANCISCO = Coordinates(37.7749, -122.4194)
    NEW_YORK = Coordinates(40.7128, -74.0060)
    LONDON = Coordinates(51.5074, -0.1278)
    TOKYO = Coordinates(35.6762, 139.6503)
    PARIS = Coordinates(48.8566, 2.3522)
    SYDNEY = Coordinates(-33.8688, 151.2093)
    SINGAPORE = Coordinates(1.3521, 103.8198)
    DUBAI = Coordinates(25.2048, 55.2708)
