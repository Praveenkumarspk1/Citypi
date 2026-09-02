"""
Recommendation Service - Collaborative + Content-based recommendations
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class RecommendationType(StrEnum):
    """Types of recommendations"""
    POI = "poi"
    ITINERARY = "itinerary"
    RESTAURANT = "restaurant"
    ACTIVITY = "activity"
    ACCOMMODATION = "accommodation"
    TRANSIT_ROUTE = "transit_route"
    EVENT = "event"


class RecommendationAlgorithm(StrEnum):
    """Recommendation algorithms"""
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    POPULARITY = "popularity"
    TRENDING = "trending"
    PERSONALIZED = "personalized"
    CONTEXTUAL = "contextual"
    SIMILARITY = "similarity"


@dataclass(frozen=True)
class RecommendationContext:
    """Context for generating recommendations"""
    user_id: UUID
    location: dict[str, float] | None = None  # lat, lng
    time_of_day: str | None = None  # morning, afternoon, evening, night
    day_of_week: int | None = None  # 0-6
    weather: str | None = None  # sunny, rainy, cloudy, etc.
    temperature: float | None = None
    companions: int = 1  # solo, couple, family, group
    budget_level: str | None = None  # low, medium, high
    interests: list[str] = field(default_factory=list)
    accessibility_needs: list[str] = field(default_factory=list)
    current_activity: str | None = None
    trip_duration_hours: float | None = None
    previous_pois: list[UUID] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "user_id": str(self.user_id),
            "location": self.location,
            "time_of_day": self.time_of_day,
            "day_of_week": self.day_of_week,
            "weather": self.weather,
            "temperature": self.temperature,
            "companions": self.companions,
            "budget_level": self.budget_level,
            "interests": self.interests,
            "accessibility_needs": self.accessibility_needs,
            "current_activity": self.current_activity,
            "trip_duration_hours": self.trip_duration_hours,
            "previous_pois": [str(p) for p in self.previous_pois],
        }


@dataclass(frozen=True)
class RecommendationItem:
    """A single recommendation item"""
    id: UUID
    type: RecommendationType
    title: str
    description: str
    score: float  # 0-1 confidence score
    metadata: dict[str, Any] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)  # Why recommended
    algorithm: RecommendationAlgorithm = RecommendationAlgorithm.HYBRID
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "score": self.score,
            "metadata": self.metadata,
            "reasons": self.reasons,
            "algorithm": self.algorithm.value,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class RecommendationResult:
    """Complete recommendation result"""
    user_id: UUID
    context: RecommendationContext
    items: list[RecommendationItem]
    algorithm_used: RecommendationAlgorithm
    generated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "user_id": str(self.user_id),
            "context": self.context.to_dict(),
            "items": [item.to_dict() for item in self.items],
            "algorithm_used": self.algorithm_used.value,
            "generated_at": self.generated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class UserPreferenceProfile:
    """User preference profile for recommendations"""
    user_id: UUID
    category_preferences: dict[str, float] = field(default_factory=dict)  # category -> weight
    price_preferences: dict[str, float] = field(default_factory=dict)  # price_level -> weight
    feature_preferences: dict[str, float] = field(default_factory=dict)  # feature -> weight
    location_preferences: list[dict[str, Any]] = field(default_factory=list)  # preferred areas
    time_preferences: dict[str, float] = field(default_factory=dict)  # time -> weight
    companion_preferences: dict[int, float] = field(default_factory=dict)  # group_size -> weight
    negative_feedback: list[UUID] = field(default_factory=list)  # disliked POIs
    positive_feedback: list[UUID] = field(default_factory=list)  # liked POIs
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "user_id": str(self.user_id),
            "category_preferences": self.category_preferences,
            "price_preferences": self.price_preferences,
            "feature_preferences": self.feature_preferences,
            "location_preferences": self.location_preferences,
            "time_preferences": self.time_preferences,
            "companion_preferences": self.companion_preferences,
            "negative_feedback": [str(p) for p in self.negative_feedback],
            "positive_feedback": [str(p) for p in self.positive_feedback],
            "last_updated": self.last_updated.isoformat(),
        }


class RecommendationService(ABC):
    """Abstract recommendation service"""

    @abstractmethod
    async def generate_recommendations(
        self,
        context: RecommendationContext,
        limit: int = 10,
        algorithm: RecommendationAlgorithm | None = None,
        types: list[RecommendationType] | None = None,
    ) -> RecommendationResult:
        """Generate personalized recommendations"""
        pass

    @abstractmethod
    async def get_similar_pois(
        self,
        poi_id: UUID,
        limit: int = 10,
        user_id: UUID | None = None,
    ) -> list[RecommendationItem]:
        """Get POIs similar to a given POI"""
        pass

    @abstractmethod
    async def get_personalized_pois(
        self,
        user_id: UUID,
        context: RecommendationContext | None = None,
        limit: int = 20,
    ) -> list[RecommendationItem]:
        """Get personalized POI recommendations for a user"""
        pass

    @abstractmethod
    async def get_trending_pois(
        self,
        location: dict[str, float] | None = None,
        radius_km: float = 10,
        category: str | None = None,
        limit: int = 20,
    ) -> list[RecommendationItem]:
        """Get trending POIs in an area"""
        pass

    @abstractmethod
    async def get_popular_pois(
        self,
        location: dict[str, float] | None = None,
        radius_km: float = 10,
        category: str | None = None,
        limit: int = 20,
    ) -> list[RecommendationItem]:
        """Get popular POIs in an area"""
        pass

    @abstractmethod
    async def update_user_preferences(
        self,
        user_id: UUID,
        feedback: dict[str, Any],
    ) -> UserPreferenceProfile:
        """Update user preferences based on feedback"""
        pass

    @abstractmethod
    async def get_user_preference_profile(
        self,
        user_id: UUID,
    ) -> UserPreferenceProfile | None:
        """Get user preference profile"""
        pass

    @abstractmethod
    async def record_interaction(
        self,
        user_id: UUID,
        item_id: UUID,
        item_type: RecommendationType,
        interaction: str,  # view, click, save, share, dismiss, rate
        rating: float | None = None,
        context: RecommendationContext | None = None,
    ) -> None:
        """Record user interaction with recommendation"""
        pass

    @abstractmethod
    async def explain_recommendation(
        self,
        user_id: UUID,
        item_id: UUID,
        item_type: RecommendationType,
    ) -> list[str]:
        """Explain why an item was recommended"""
        pass


class RecommendationServiceImpl(RecommendationService):
    """Default implementation of recommendation service"""

    def __init__(
        self,
        poi_repository=None,
        user_repository=None,
        interaction_repository=None,
        embedding_service=None,
        lightfm_model=None,
    ):
        self.poi_repository = poi_repository
        self.user_repository = user_repository
        self.interaction_repository = interaction_repository
        self.embedding_service = embedding_service
        self.lightfm_model = lightfm_model

    async def generate_recommendations(
        self,
        context: RecommendationContext,
        limit: int = 10,
        algorithm: RecommendationAlgorithm | None = None,
        types: list[RecommendationType] | None = None,
    ) -> RecommendationResult:
        """Generate personalized recommendations"""
        # Placeholder implementation
        # In production, this would use collaborative filtering, content-based, etc.

        items = []
        # Would fetch from repository and score based on context

        return RecommendationResult(
            user_id=context.user_id,
            context=context,
            items=items,
            algorithm_used=algorithm or RecommendationAlgorithm.HYBRID,
        )

    async def get_similar_pois(
        self,
        poi_id: UUID,
        limit: int = 10,
        user_id: UUID | None = None,
    ) -> list[RecommendationItem]:
        """Get POIs similar to a given POI"""
        # Placeholder - would use embeddings or content similarity
        return []

    async def get_personalized_pois(
        self,
        user_id: UUID,
        context: RecommendationContext | None = None,
        limit: int = 20,
    ) -> list[RecommendationItem]:
        """Get personalized POI recommendations for a user"""
        # Placeholder - would use LightFM or similar
        return []

    async def get_trending_pois(
        self,
        location: dict[str, float] | None = None,
        radius_km: float = 10,
        category: str | None = None,
        limit: int = 20,
    ) -> list[RecommendationItem]:
        """Get trending POIs in an area"""
        # Placeholder - would analyze recent visits, ratings, social signals
        return []

    async def get_popular_pois(
        self,
        location: dict[str, float] | None = None,
        radius_km: float = 10,
        category: str | None = None,
        limit: int = 20,
    ) -> list[RecommendationItem]:
        """Get popular POIs in an area"""
        # Placeholder - would use visit counts, ratings, reviews
        return []

    async def update_user_preferences(
        self,
        user_id: UUID,
        feedback: dict[str, Any],
    ) -> UserPreferenceProfile:
        """Update user preferences based on feedback"""
        # Placeholder - would update profile in database
        return UserPreferenceProfile(user_id=user_id)

    async def get_user_preference_profile(
        self,
        user_id: UUID,
    ) -> UserPreferenceProfile | None:
        """Get user preference profile"""
        # Placeholder - would fetch from database
        return None

    async def record_interaction(
        self,
        user_id: UUID,
        item_id: UUID,
        item_type: RecommendationType,
        interaction: str,
        rating: float | None = None,
        context: RecommendationContext | None = None,
    ) -> None:
        """Record user interaction with recommendation"""
        # Placeholder - would store in interaction repository
        pass

    async def explain_recommendation(
        self,
        user_id: UUID,
        item_id: UUID,
        item_type: RecommendationType,
    ) -> list[str]:
        """Explain why an item was recommended"""
        # Placeholder - would generate human-readable explanations
        return ["Recommended based on your preferences"]
