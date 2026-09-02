"""
External API Configuration
"""
from dataclasses import dataclass

from pydantic_settings import BaseSettings, SettingsConfigDict


class ExternalAPISettings(BaseSettings):
    """External API configuration"""
    model_config = SettingsConfigDict(env_prefix="EXTERNAL_")

    # OpenStreetMap / Overpass API
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    overpass_rate_limit: int = 60  # requests per minute
    overpass_timeout: float = 30.0

    # Nominatim Geocoding
    nominatim_url: str = "https://nominatim.openstreetmap.org"
    nominatim_rate_limit: int = 1  # 1 request per second (policy)
    nominatim_timeout: float = 10.0
    nominatim_user_agent: str = "SmartCityConcierge/1.0"

    # Open-Meteo Weather
    open_meteo_url: str = "https://api.open-meteo.com/v1"
    open_meteo_rate_limit: int = 100
    open_meteo_timeout: float = 10.0

    # GTFS
    gtfs_static_base_url: str = ""
    gtfs_realtime_base_url: str = ""
    gtfs_rate_limit: int = 10
    gtfs_timeout: float = 30.0

    # OpenChargeMap
    openchargemap_url: str = "https://api.openchargemap.io/v3"
    openchargemap_api_key: str = ""
    openchargemap_rate_limit: int = 100
    openchargemap_timeout: float = 10.0

    # Socrata Open Data
    socrata_domain: str = "data.city.gov"
    socrata_app_token: str = ""
    socrata_rate_limit: int = 100
    socrata_timeout: float = 10.0

    # MapTiler (for map tiles)
    maptiler_api_key: str = ""
    maptiler_base_url: str = "https://api.maptiler.com"

    # Google Maps (optional, for places API)
    google_maps_api_key: str = ""
    google_places_url: str = "https://maps.googleapis.com/maps/api/place"

    # Timezone API
    timezone_api_url: str = "https://api.timezonedb.com/v2.1"
    timezone_api_key: str = ""


@dataclass
class OverpassConfig:
    """Overpass API configuration"""
    url: str = "https://overpass-api.de/api/interpreter"
    rate_limit: int = 60
    timeout: float = 30.0

    # Common POI categories for Overpass queries
    POI_CATEGORIES = {
        "restaurant": ["amenity=restaurant", "amenity=cafe", "amenity=fast_food"],
        "museum": ["tourism=museum"],
        "park": ["leisure=park", "boundary=national_park"],
        "hotel": ["tourism=hotel", "tourism=hostel", "tourism=guest_house"],
        "shop": ["shop=*"],
        "transport": ["public_transport=station", "railway=station", "bus_station=yes"],
        "landmark": ["tourism=attraction", "historic=*"],
        "healthcare": ["amenity=hospital", "amenity=clinic", "amenity=pharmacy"],
        "education": ["amenity=university", "amenity=school", "amenity=college"],
        "entertainment": ["amenity=cinema", "amenity=theatre", "amenity=nightclub"],
        "fuel": ["amenity=fuel"],
        "charging": ["amenity=charging_station"],
        "parking": ["amenity=parking"],
        "atm": ["amenity=atm"],
        "bank": ["amenity=bank"],
        "post_office": ["amenity=post_office"],
        "police": ["amenity=police"],
        "fire_station": ["amenity=fire_station"],
        "library": ["amenity=library"],
        "toilet": ["amenity=toilets"],
        "drinking_water": ["amenity=drinking_water"],
        "wifi": ["amenity=wifi"],
    }


@dataclass
class GTFSConfig:
    """GTFS configuration for transit agencies"""
    # Example agencies - add more as needed
    AGENCIES = {
        "sfmta": {
            "name": "San Francisco Muni",
            "static_url": "https://www.sfmta.com/sites/default/files/gtfs/google_transit.zip",
            "realtime_url": "https://gtfs.sfmta.com/gtfsrealtime/vehicle_positions.pb",
            "timezone": "America/Los_Angeles",
        },
        "bart": {
            "name": "BART",
            "static_url": "https://www.bart.gov/sites/default/files/docs/gtfs.zip",
            "realtime_url": "https://api.bart.gov/gtfsrt/tripupdate.aspx",
            "timezone": "America/Los_Angeles",
        },
        "nyc_mta": {
            "name": "NYC MTA Subway",
            "static_url": "https://new.mta.info/document/2024/01/gtfs-subway",
            "realtime_url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
            "timezone": "America/New_York",
        },
        "london_tfl": {
            "name": "Transport for London",
            "static_url": "https://tfl.gov.uk/static/cms/gtfs.zip",
            "realtime_url": "https://api.tfl.gov.uk/gtfs/realtime",
            "timezone": "Europe/London",
        },
    }


# Global settings instance
_external_api_settings: ExternalAPISettings | None = None


def get_external_api_settings() -> ExternalAPISettings:
    """Get external API settings"""
    global _external_api_settings
    if _external_api_settings is None:
        _external_api_settings = ExternalAPISettings()
    return _external_api_settings


# API Client configurations
class APIClientConfig:
    """Base configuration for API clients"""

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        rate_limit: int = 60,
        headers: dict | None = None,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.headers = headers or {}


# Pre-configured client configs
def get_overpass_config() -> APIClientConfig:
    settings = get_external_api_settings()
    return APIClientConfig(
        base_url=settings.overpass_url,
        timeout=settings.overpass_timeout,
        rate_limit=settings.overpass_rate_limit,
    )


def get_nominatim_config() -> APIClientConfig:
    settings = get_external_api_settings()
    return APIClientConfig(
        base_url=settings.nominatim_url,
        timeout=settings.nominatim_timeout,
        rate_limit=settings.nominatim_rate_limit,
        headers={"User-Agent": settings.nominatim_user_agent},
    )


def get_open_meteo_config() -> APIClientConfig:
    settings = get_external_api_settings()
    return APIClientConfig(
        base_url=settings.open_meteo_url,
        timeout=settings.open_meteo_timeout,
        rate_limit=settings.open_meteo_rate_limit,
    )


def get_openchargemap_config() -> APIClientConfig:
    settings = get_external_api_settings()
    return APIClientConfig(
        base_url=settings.openchargemap_url,
        timeout=settings.openchargemap_timeout,
        rate_limit=settings.openchargemap_rate_limit,
        headers={"Authorization": f"Bearer {settings.openchargemap_api_key}"} if settings.openchargemap_api_key else {},
    )


def get_socrata_config() -> APIClientConfig:
    settings = get_external_api_settings()
    return APIClientConfig(
        base_url=f"https://{settings.socrata_domain}",
        timeout=settings.socrata_timeout,
        rate_limit=settings.socrata_rate_limit,
        headers={"X-App-Token": settings.socrata_app_token} if settings.socrata_app_token else {},
    )
