"""
Analytics Application Use Cases
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from ...domain.entities.analytics import AnalyticsEvent
from ...domain.repositories.analytics_repository import AnalyticsRepository
from ...domain.repositories.base import FilterParams, PaginatedResult, PaginationParams


@dataclass
class TrackEventRequest:
    """Request to track an event"""
    event_name: str
    user_id: UUID | None = None
    session_id: str | None = None
    properties: dict[str, Any] | None = None
    context: dict[str, Any] | None = None


@dataclass
class TrackMetricRequest:
    """Request to track a metric"""
    metric_name: str
    value: float
    dimensions: dict[str, str] | None = None
    timestamp: datetime | None = None


@dataclass
class GetEventsRequest:
    """Request to get events"""
    user_id: UUID | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    event_names: list[str] | None = None
    pagination: PaginationParams | None = None


@dataclass
class GetMetricsRequest:
    """Request to get metrics"""
    metric_name: str
    start_date: datetime
    end_date: datetime
    dimensions: dict[str, str] | None = None
    interval: str = "hour"


@dataclass
class GetFunnelRequest:
    """Request to get funnel"""
    steps: list[str]
    start_date: datetime
    end_date: datetime
    user_id: UUID | None = None


@dataclass
class GetRetentionRequest:
    """Request to get retention"""
    cohort_date: datetime
    periods: int = 7
    period_type: str = "day"


class AnalyticsUseCases:
    """Analytics Application Use Cases"""

    def __init__(
        self,
        analytics_repository: AnalyticsRepository,
    ):
        self.analytics_repository = analytics_repository

    async def track_event(self, request: TrackEventRequest) -> AnalyticsEvent:
        """Track an analytics event"""
        return await self.analytics_repository.track_event(
            event_name=request.event_name,
            user_id=request.user_id,
            session_id=request.session_id,
            properties=request.properties,
            context=request.context,
        )

    async def track_metric(self, request: TrackMetricRequest) -> AnalyticsMetric:
        """Track a metric"""
        return await self.analytics_repository.track_metric(
            metric_name=request.metric_name,
            value=request.value,
            dimensions=request.dimensions,
            timestamp=request.timestamp,
        )

    async def get_events(self, request: GetEventsRequest) -> PaginatedResult[AnalyticsEvent]:
        """Get analytics events"""
        if request.user_id:
            return await self.analytics_repository.get_events_by_user(
                user_id=request.user_id,
                start_date=request.start_date,
                end_date=request.end_date,
                event_names=request.event_names,
                pagination=request.pagination,
            )
        else:
            return await self.analytics_repository.list(
                pagination=request.pagination,
                filters=FilterParams(filters={
                    "event_name": request.event_names,
                } if request.event_names else {}),
            )

    async def get_metrics(self, request: GetMetricsRequest) -> list[dict[str, Any]]:
        """Get aggregated metrics"""
        return await self.analytics_repository.get_metrics(
            metric_name=request.metric_name,
            start_date=request.start_date,
            end_date=request.end_date,
            dimensions=request.dimensions,
            interval=request.interval,
        )

    async def get_funnel(self, request: GetFunnelRequest) -> list[dict[str, Any]]:
        """Get funnel conversion rates"""
        return await self.analytics_repository.get_funnel(
            steps=request.steps,
            start_date=request.start_date,
            end_date=request.end_date,
            user_id=request.user_id,
        )

    async def get_retention(self, request: GetRetentionRequest) -> list[dict[str, Any]]:
        """Get retention cohorts"""
        return await self.analytics_repository.get_retention(
            cohort_date=request.cohort_date,
            periods=request.periods,
            period_type=request.period_type,
        )

    async def get_top_events(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get top events by count"""
        return await self.analytics_repository.get_top_events(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

    async def get_active_users(
        self,
        start_date: datetime,
        end_date: datetime,
        interval: str = "day",
    ) -> list[dict[str, Any]]:
        """Get active users over time"""
        return await self.analytics_repository.get_active_users(
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )

    async def get_session_stats(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Get session statistics"""
        return await self.analytics_repository.get_session_stats(
            start_date=start_date,
            end_date=end_date,
        )

    async def get_dashboard_stats(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get dashboard statistics"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        return await self.analytics_service.get_dashboard_stats(
            start_date=start_date,
            end_date=end_date,
        )

    async def get_user_journey(
        self,
        user_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get user journey"""
        return await self.analytics_service.get_user_journey(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_conversion_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Get conversion report"""
        return await self.analytics_service.get_conversion_report(
            start_date=start_date,
            end_date=end_date,
        )
