"""
Application Ports - External service interfaces
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from ...domain.entities.poi import POI
from ...domain.entities.transit import TransitRoute, Stop as TransitStop, TransitTrip
from ...domain.entities.weather import WeatherAlert, WeatherForecast
from ...domain.value_objects.coordinates import Coordinates


# External API Client Ports
class GeocodingServicePort(ABC):
    """Geocoding service port (OpenStreetMap, Google Maps, Mapbox)"""

    @abstractmethod
    async def geocode(self, address: str) -> Coordinates | None:
        """Convert address to coordinates"""
        pass

    @abstractmethod
    async def reverse_geocode(self, coordinates: Coordinates) -> str | None:
        """Convert coordinates to address"""
        pass

    @abstractmethod
    async def autocomplete(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Autocomplete address suggestions"""
        pass


class RoutingServicePort(ABC):
    """Routing service port (OSRM, Valhalla, Google Maps, Mapbox)"""

    @abstractmethod
    async def get_route(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: str = "walking",
        alternatives: bool = False,
    ) -> dict[str, Any]:
        """Get route between two points"""
        pass

    @abstractmethod
    async def get_matrix(
        self,
        origins: list[Coordinates],
        destinations: list[Coordinates],
        mode: str = "walking",
    ) -> dict[str, Any]:
        """Get distance/duration matrix"""
        pass

    @abstractmethod
    async def get_isochrone(
        self,
        center: Coordinates,
        time_minutes: float,
        mode: str = "walking",
    ) -> dict[str, Any]:
        """Get isochrone (reachable area)"""
        pass


class PlacesServicePort(ABC):
    """Places service port (Google Places, Foursquare, OpenStreetMap)"""

    @abstractmethod
    async def search_places(
        self,
        query: str,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        category: str | None = None,
        limit: int = 20,
    ) -> list[POI]:
        """Search for places"""
        pass

    @abstractmethod
    async def get_place_details(self, place_id: str) -> POI | None:
        """Get detailed place information"""
        pass

    @abstractmethod
    async def get_place_photos(self, place_id: str, max_photos: int = 10) -> list[str]:
        """Get place photos"""
        pass

    @abstractmethod
    async def get_place_reviews(self, place_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get place reviews"""
        pass


class TransitDataServicePort(ABC):
    """Transit data service port (GTFS, Transitland, City APIs)"""

    @abstractmethod
    async def get_agencies(self, coordinates: Coordinates | None = None) -> list[dict[str, Any]]:
        """Get transit agencies"""
        pass

    @abstractmethod
    async def get_routes(
        self,
        agency_id: str | None = None,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
    ) -> list[TransitRoute]:
        """Get transit routes"""
        pass

    @abstractmethod
    async def get_stops(
        self,
        route_id: str | None = None,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
    ) -> list[TransitStop]:
        """Get transit stops"""
        pass

    @abstractmethod
    async def get_trips(
        self,
        route_id: str,
        date: datetime,
    ) -> list[TransitTrip]:
        """Get trips for a route on a date"""
        pass

    @abstractmethod
    async def get_schedule(
        self,
        stop_id: str,
        date: datetime,
        route_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get schedule for a stop"""
        pass


class RealtimeTransitServicePort(ABC):
    """Real-time transit service port (GTFS-RT, City APIs)"""

    @abstractmethod
    async def get_arrivals(
        self,
        stop_id: str,
        route_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get real-time arrivals"""
        pass

    @abstractmethod
    async def get_vehicle_positions(
        self,
        route_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get real-time vehicle positions"""
        pass

    @abstractmethod
    async def get_alerts(
        self,
        route_ids: list[str] | None = None,
        stop_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get service alerts"""
        pass


class WeatherServicePort(ABC):
    """Weather service port (Open-Meteo, OpenWeather, WeatherAPI)"""

    @abstractmethod
    async def get_current_weather(
        self,
        coordinates: Coordinates,
    ) -> dict[str, Any]:
        """Get current weather"""
        pass

    @abstractmethod
    async def get_forecast(
        self,
        coordinates: Coordinates,
        days: int = 7,
        hourly: bool = True,
    ) -> WeatherForecast:
        """Get weather forecast"""
        pass

    @abstractmethod
    async def get_alerts(
        self,
        coordinates: Coordinates,
    ) -> list[WeatherAlert]:
        """Get weather alerts"""
        pass

    @abstractmethod
    async def get_historical(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get historical weather"""
        pass


class VectorDatabasePort(ABC):
    """Vector database port (ChromaDB, Pinecone, Weaviate, Qdrant)"""

    @abstractmethod
    async def upsert_embeddings(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert embeddings"""
        pass

    @abstractmethod
    async def query_embeddings(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query similar embeddings"""
        pass

    @abstractmethod
    async def delete_embeddings(
        self,
        collection: str,
        ids: list[str],
    ) -> None:
        """Delete embeddings"""
        pass

    @abstractmethod
    async def get_embedding(
        self,
        collection: str,
        id: str,
    ) -> dict[str, Any] | None:
        """Get embedding by ID"""
        pass


class EmbeddingServicePort(ABC):
    """Embedding service port (BAAI/bge-m3, OpenAI, Cohere, local)"""

    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text"""
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts"""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name"""
        pass


class LLMServicePort(ABC):
    """LLM service port (Gemini, OpenAI, Anthropic, local)"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text completion"""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Generate structured output"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Chat completion"""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
    ):
        """Stream chat completion"""
        pass


class SpeechToTextServicePort(ABC):
    """Speech-to-text service port (faster-whisper, OpenAI Whisper, Google Speech)"""

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
    ) -> str:
        """Transcribe audio to text"""
        pass

    @abstractmethod
    async def transcribe_with_timestamps(
        self,
        audio_data: bytes,
        language: str | None = None,
    ) -> list[dict[str, Any]]:
        """Transcribe with word-level timestamps"""
        pass


class VisionAIServicePort(ABC):
    """Vision AI service port (CLIP, GPT-4V, Google Vision)"""

    @abstractmethod
    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str | None = None,
    ) -> dict[str, Any]:
        """Analyze image"""
        pass

    @abstractmethod
    async def generate_embedding(self, image_data: bytes) -> list[float]:
        """Generate image embedding"""
        pass

    @abstractmethod
    async def classify_image(
        self,
        image_data: bytes,
        categories: list[str],
    ) -> dict[str, float]:
        """Classify image into categories"""
        pass


class RecommendationEnginePort(ABC):
    """Recommendation engine port (LightFM, implicit, custom)"""

    @abstractmethod
    async def train(
        self,
        interactions: list[dict[str, Any]],
        item_features: dict[str, Any] | None = None,
        user_features: dict[str, Any] | None = None,
    ) -> None:
        """Train recommendation model"""
        pass

    @abstractmethod
    async def recommend(
        self,
        user_id: str,
        n_recommendations: int = 10,
        filter_items: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get recommendations for user"""
        pass

    @abstractmethod
    async def similar_items(
        self,
        item_id: str,
        n_similar: int = 10,
    ) -> list[dict[str, Any]]:
        """Get similar items"""
        pass

    @abstractmethod
    async def update_user(
        self,
        user_id: str,
        interactions: list[dict[str, Any]],
    ) -> None:
        """Update user model with new interactions"""
        pass


class CacheServicePort(ABC):
    """Cache service port (Redis, Memcached)"""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value from cache"""
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        """Set value in cache"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        pass

    @abstractmethod
    async def get_multi(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values"""
        pass

    @abstractmethod
    async def set_multi(
        self,
        mapping: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> None:
        """Set multiple values"""
        pass


class MessageQueuePort(ABC):
    """Message queue port (Redis/RQ, RabbitMQ, Kafka)"""

    @abstractmethod
    async def enqueue(
        self,
        queue: str,
        job_data: dict[str, Any],
        priority: int = 0,
        delay_seconds: int = 0,
    ) -> str:
        """Enqueue a job"""
        pass

    @abstractmethod
    async def dequeue(self, queue: str) -> dict[str, Any] | None:
        """Dequeue a job"""
        pass

    @abstractmethod
    async def get_queue_size(self, queue: str) -> int:
        """Get queue size"""
        pass

    @abstractmethod
    async def schedule_job(
        self,
        queue: str,
        job_data: dict[str, Any],
        run_at: datetime,
    ) -> str:
        """Schedule a job for future execution"""
        pass


class StorageServicePort(ABC):
    """Storage service port (S3, GCS, Azure Blob, local)"""

    @abstractmethod
    async def upload(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload file"""
        pass

    @abstractmethod
    async def download(self, bucket: str, key: str) -> bytes:
        """Download file"""
        pass

    @abstractmethod
    async def delete(self, bucket: str, key: str) -> None:
        """Delete file"""
        pass

    @abstractmethod
    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration_seconds: int = 3600,
    ) -> str:
        """Generate presigned URL"""
        pass

    @abstractmethod
    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[dict[str, Any]]:
        """List objects in bucket"""
        pass


class NotificationServicePort(ABC):
    """Notification service port (FCM, APNS, Email, SMS)"""

    @abstractmethod
    async def send_push(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Send push notification"""
        pass

    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: str | None = None,
    ) -> bool:
        """Send email"""
        pass

    @abstractmethod
    async def send_sms(
        self,
        to: str,
        body: str,
    ) -> bool:
        """Send SMS"""
        pass

    @abstractmethod
    async def send_in_app(
        self,
        user_id: UUID,
        notification: dict[str, Any],
    ) -> bool:
        """Send in-app notification"""
        pass


class AuthServicePort(ABC):
    """Authentication service port (JWT, OAuth, Firebase Auth)"""

    @abstractmethod
    async def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify JWT token"""
        pass

    @abstractmethod
    async def create_token(
        self,
        user_id: UUID,
        claims: dict[str, Any] | None = None,
        expires_in: int = 3600,
    ) -> str:
        """Create JWT token"""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> str | None:
        """Refresh access token"""
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> None:
        """Revoke token"""
        pass

    @abstractmethod
    async def verify_oauth_token(
        self,
        provider: str,
        token: str,
    ) -> dict[str, Any] | None:
        """Verify OAuth token"""
        pass


class RateLimiterPort(ABC):
    """Rate limiter port"""

    @abstractmethod
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> dict[str, Any]:
        """Check rate limit"""
        pass

    @abstractmethod
    async def increment(
        self,
        key: str,
        window_seconds: int,
    ) -> int:
        """Increment counter"""
        pass

    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset counter"""
        pass


class MetricsServicePort(ABC):
    """Metrics service port (Prometheus, Datadog, CloudWatch)"""

    @abstractmethod
    async def increment_counter(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        value: float = 1.0,
    ) -> None:
        """Increment counter"""
        pass

    @abstractmethod
    async def record_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record histogram value"""
        pass

    @abstractmethod
    async def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set gauge value"""
        pass


class TracingServicePort(ABC):
    """Distributed tracing service port (Jaeger, Zipkin, OpenTelemetry)"""

    @abstractmethod
    def start_span(
        self,
        name: str,
        parent_context: Any | None = None,
    ) -> Any:
        """Start a trace span"""
        pass

    @abstractmethod
    def end_span(self, span: Any) -> None:
        """End a trace span"""
        pass

    @abstractmethod
    def add_span_attribute(self, span: Any, key: str, value: Any) -> None:
        """Add attribute to span"""
        pass

    @abstractmethod
    def record_exception(self, span: Any, exception: Exception) -> None:
        """Record exception in span"""
        pass
