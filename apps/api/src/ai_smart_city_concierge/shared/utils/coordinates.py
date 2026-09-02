"""
Shared Utilities - Coordinates helpers
"""
from ....domain.value_objects.coordinates import Coordinates


def validate_coordinates(lat: float, lng: float) -> bool:
    """Validate latitude and longitude values."""
    return -90 <= lat <= 90 and -180 <= lng <= 180


def coordinates_to_dict(coordinates: Coordinates) -> dict[str, float]:
    """Convert Coordinates value object to dictionary."""
    return {"lat": coordinates.lat, "lng": coordinates.lng}


def coordinates_to_tuple(coordinates: Coordinates) -> tuple[float, float]:
    """Convert Coordinates value object to tuple."""
    return (coordinates.lat, coordinates.lng)
