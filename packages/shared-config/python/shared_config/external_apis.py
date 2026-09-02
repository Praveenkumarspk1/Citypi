"""
External API Settings

Configuration for external API integrations.
"""
from typing import List
from pydantic import Field
from .base import BaseSettings


class ExternalAPISettings(BaseSettings):
    """External API configuration."""
    
    # Google APIs
    google_api_key: str = Field(default="", validation_alias="GOOGLE_API_KEY")
    google_places_api_key: str = Field(default="", validation_alias="GOOGLE_PLACES_API_KEY")
    google_maps_api_key: str = Field(default="", validation_alias="GOOGLE_MAPS_API_KEY")
    google_geocoding_api_key: str = Field(default="", validation_alias="GOOGLE_GEOCODING_API_KEY")

    # Geocoding
    geocoding_nominatim_url: str = "https://nominatim.openstreetmap.org"
    geocoding_user_agent: str = "smart-city-concierge/1.0"
    geocoding_rate_limit: int = 1  # requests per second

    # Routing
    routing_osrm_url: str = "http://router.project-osrm.org"
    routing_valhalla_url: str = ""
    routing_rate_limit: int = 10

    # Places
    places_provider: str = "google"  # google, foursquare, yelp
    places_radius_default: int = 5000
    places_max_results: int = 20

    # Transit
    transit_gtfs_feed_urls: List[str] = Field(default_factory=list)
    transit_gtfs_realtime_urls: List[str] = Field(default_factory=list)
    transit_refresh_interval: int = 300  # seconds

    # Weather
    weather_openweather_api_key: str = Field(default="", validation_alias="OPENWEATHER_API_KEY")
    weather_open_meteo_url: str = "https://api.open-meteo.com"
    weather_noaa_url: str = "https://api.weather.gov"
    weather_cache_ttl: int = 1800  # 30 minutes

    # LLM
    llm_provider: str = "gemini"  # gemini, openai, anthropic
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    llm_model: str = "gemini-1.5-pro"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_timeout: int = 60

    # Speech
    speech_whisper_model_size: str = "base"
    speech_device: str = "cpu"
    speech_compute_type: str = "float32"

    # Vision
    vision_clip_model_name: str = "openai/clip-vit-base-patch32"
    vision_device: str = "cpu"

    # Recommendations
    recommendation_lightfm_components: int = 64
    recommendation_lightfm_learning_rate: float = 0.05
    recommendation_lightfm_loss: str = "warp"
    recommendation_lightfm_epochs: int = 10

    # Rate limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_requests_per_hour: int = 1000
    rate_limit_burst: int = 10