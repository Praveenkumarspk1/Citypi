"""
Analytics Repository Interface
"""
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any
from uuid import UUID

from ..entities.analytics import (
    AnalyticsEvent,
    CohortAnalysis,
    DailyMetrics,
    EventType,
    FeatureUsage,
    FunnelAnalysis,
    UserMetrics,
)
from .base import PaginatedResult, PaginationParams


class AnalyticsRepository(ABC):
    """Analytics repository interface"""

    # Events
    @abstractmethod
    async def record_event(self, event: AnalyticsEvent) -> None:
        """Record an analytics event"""
        pass

    @abstractmethod
    async def record_events_batch(self, events: list[AnalyticsEvent]) -> None:
        """Record multiple analytics events"""
        pass

    @abstractmethod
    async def get_events(
        self,
        user_id: UUID | None = None,
        event_type: EventType | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[AnalyticsEvent]:
        """Get analytics events"""
        pass

    @abstractmethod
    async def get_events_by_session(
        self,
        session_id: str,
    ) -> list[AnalyticsEvent]:
        """Get events for a session"""
        pass

    # Daily metrics
    @abstractmethod
    async def get_daily_metrics(
        self,
        start_date: date,
        end_date: date,
    ) -> list[DailyMetrics]:
        """Get daily metrics for date range"""
        pass

    @abstractmethod
    async def get_daily_metric(self, date: date) -> DailyMetrics | None:
        """Get daily metrics for specific date"""
        pass

    @abstractmethod
    async def upsert_daily_metrics(self, metrics: DailyMetrics) -> DailyMetrics:
        """Upsert daily metrics"""
        pass

    @abstractmethod
    async def calculate_daily_metrics(self, date: date) -> DailyMetrics:
        """Calculate daily metrics from events"""
        pass

    # User metrics
    @abstractmethod
    async def get_user_metrics(self, user_id: UUID) -> UserMetrics | None:
        """Get user metrics"""
        pass

    @abstractmethod
    async def upsert_user_metrics(self, metrics: UserMetrics) -> UserMetrics:
        """Upsert user metrics"""
        pass

    @abstractmethod
    async def get_top_users(
        self,
        metric: str = "engagement_score",
        limit: int = 100,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[UserMetrics]:
        """Get top users by metric"""
        pass

    @abstractmethod
    async def get_users_at_risk(
        self,
        churn_threshold: float = 0.7,
        limit: int = 100,
    ) -> list[UserMetrics]:
        """Get users at risk of churning"""
        pass

    # Funnel analysis
    @abstractmethod
    async def get_funnel_analysis(
        self,
        name: str,
        start_date: date,
        end_date: date,
        segment: str | None = None,
    ) -> FunnelAnalysis | None:
        """Get funnel analysis"""
        pass

    @abstractmethod
    async def calculate_funnel(
        self,
        name: str,
        steps: list[EventType],
        start_date: date,
        end_date: date,
        segment: str | None = None,
    ) -> FunnelAnalysis:
        """Calculate funnel analysis"""
        pass

    # Cohort analysis
    @abstractmethod
    async def get_cohort_analysis(
        self,
        cohort_date: date,
        segment: str | None = None,
    ) -> CohortAnalysis | None:
        """Get cohort analysis"""
        pass

    @abstractmethod
    async def calculate_cohort(
        self,
        cohort_date: date,
        segment: str | None = None,
    ) -> CohortAnalysis:
        """Calculate cohort retention"""
        pass

    @abstractmethod
    async def get_cohorts(
        self,
        start_date: date,
        end_date: date,
        segment: str | None = None,
    ) -> list[CohortAnalysis]:
        """Get multiple cohorts"""
        pass

    # Feature usage
    @abstractmethod
    async def get_feature_usage(
        self,
        feature: str,
        start_date: date,
        end_date: date,
    ) -> FeatureUsage | None:
        """Get feature usage statistics"""
        pass

    @abstractmethod
    async def calculate_feature_usage(
        self,
        feature: str,
        start_date: date,
        end_date: date,
    ) -> FeatureUsage:
        """Calculate feature usage"""
        pass

    @abstractmethod
    async def get_all_feature_usage(
        self,
        start_date: date,
        end_date: date,
    ) -> list[FeatureUsage]:
        """Get usage for all features"""
        pass

    # Real-time / aggregations
    @abstractmethod
    async def get_realtime_active_users(self) -> int:
        """Get current active users (last 5 minutes)"""
        pass

    @abstractmethod
    async def get_event_counts(
        self,
        event_types: list[EventType],
        start_date: datetime,
        end_date: datetime,
        group_by: str = "hour",  # hour, day, week
    ) -> dict[str, list[dict[str, Any]]]:
        """Get event counts grouped by time"""
        pass

    @abstractmethod
    async def get_user_retention(
        self,
        cohort_date: date,
        days: list[int] = None,
    ) -> dict[int, float]:
        """Get retention rates for cohort"""
        pass

    @abstractmethod
    async def get_conversion_rate(
        self,
        from_event: EventType,
        to_event: EventType,
        start_date: date,
        end_date: date,
    ) -> float:
        """Get conversion rate between two events"""
        pass

    # Cleanup
    @abstractmethod
    async def cleanup_old_events(self, days: int = 90) -> int:
        """Clean up old events"""
        pass

    @abstractmethod
    async def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        pass
