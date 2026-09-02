"""
Analytics API Routes
"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from ....application.use_cases.analytics_use_cases import (
    AnalyticsUseCases,
    GetEventsRequest,
    GetFunnelRequest,
    GetMetricsRequest,
    GetRetentionRequest,
    TrackEventRequest,
    TrackMetricRequest,
)
from ....domain.entities.analytics import AnalyticsEvent
from ....domain.repositories.base import PaginationParams
from ....infrastructure.config.dependencies import get_analytics_use_cases

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# Request/Response Models
class TrackEventModel(BaseModel):
    event_name: str
    user_id: UUID | None = None
    session_id: str | None = None
    properties: dict | None = None
    context: dict | None = None


class TrackMetricModel(BaseModel):
    metric_name: str
    value: float
    dimensions: dict | None = None
    timestamp: datetime | None = None


class AnalyticsEventResponse(BaseModel):
    id: UUID
    event_name: str
    user_id: UUID | None
    session_id: str | None
    properties: dict
    context: dict
    created_at: str


class AnalyticsMetricResponse(BaseModel):
    id: UUID
    metric_name: str
    value: float
    dimensions: dict
    timestamp: str


class PaginatedEventResponse(BaseModel):
    items: list[AnalyticsEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class FunnelStepResponse(BaseModel):
    step: str
    count: int
    conversion_rate: float


class RetentionPeriodResponse(BaseModel):
    period: int
    period_start: str
    cohort_size: int
    returned: int
    retention_rate: float


class TopEventResponse(BaseModel):
    event_name: str
    count: int
    unique_users: int


class ActiveUsersResponse(BaseModel):
    date: str
    active_users: int


class SessionStatsResponse(BaseModel):
    total_sessions: int
    total_events: int
    avg_session_duration: float
    events_per_session: float


class DashboardStatsResponse(BaseModel):
    total_users: int
    active_users_7d: int
    active_users_30d: int
    total_events: int
    total_sessions: int
    avg_session_duration: float
    top_events: list[TopEventResponse]
    active_users_trend: list[ActiveUsersResponse]
    funnel: list[FunnelStepResponse]


def event_to_response(event: AnalyticsEvent) -> AnalyticsEventResponse:
    """Convert AnalyticsEvent to response"""
    return AnalyticsEventResponse(
        id=event.id,
        event_name=event.event_name,
        user_id=event.user_id,
        session_id=event.session_id,
        properties=event.properties,
        context=event.context,
        created_at=event.created_at.isoformat() if event.created_at else "",
    )


@router.post("/events", response_model=AnalyticsEventResponse, status_code=status.HTTP_201_CREATED)
async def track_event(
    request: TrackEventModel,
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Track an analytics event"""
    event_request = TrackEventRequest(
        event_name=request.event_name,
        user_id=request.user_id,
        session_id=request.session_id,
        properties=request.properties,
        context=request.context,
    )

    event = await use_cases.track_event(event_request)
    return event_to_response(event)


@router.post("/metrics", response_model=AnalyticsMetricResponse, status_code=status.HTTP_201_CREATED)
async def track_metric(
    request: TrackMetricModel,
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Track a metric"""
    metric_request = TrackMetricRequest(
        metric_name=request.metric_name,
        value=request.value,
        dimensions=request.dimensions,
        timestamp=request.timestamp,
    )

    metric = await use_cases.track_metric(metric_request)
    return AnalyticsMetricResponse(
        id=metric.id,
        metric_name=metric.metric_name,
        value=metric.value,
        dimensions=metric.dimensions,
        timestamp=metric.timestamp.isoformat() if metric.timestamp else "",
    )


@router.get("/events", response_model=PaginatedEventResponse)
async def get_events(
    user_id: UUID | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    event_names: list[str] | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Get analytics events"""
    request = GetEventsRequest(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        event_names=event_names,
        pagination=PaginationParams(page=page, page_size=page_size),
    )

    result = await use_cases.get_events(request)

    return PaginatedEventResponse(
        items=[event_to_response(e) for e in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.get("/metrics", response_model=list[dict])
async def get_metrics(
    metric_name: str = Query(..., min_length=1),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    dimensions: str | None = Query(None),  # JSON string
    interval: str = Query("hour", regex="^(minute|hour|day)$"),
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Get aggregated metrics"""
    import json
    dims = json.loads(dimensions) if dimensions else None

    request = GetMetricsRequest(
        metric_name=metric_name,
        start_date=start_date,
        end_date=end_date,
        dimensions=dims,
        interval=interval,
    )

    return await use_cases.get_metrics(request)


@router.get("/funnel", response_model=list[FunnelStepResponse])
async def get_funnel(
    steps: list[str] = Query(..., min_length=2),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    user_id: UUID | None = Query(None),
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Get funnel conversion rates"""
    request = GetFunnelRequest(
        steps=steps,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
    )

    funnel = await use_cases.get_funnel(request)
    return [FunnelStepResponse(**step) for step in funnel]


@router.get("/retention", response_model=list[RetentionPeriodResponse])
async def get_retention(
    cohort_date: datetime = Query(...),
    periods: int = Query(7, ge=1, le=90),
    period_type: str = Query("day", regex="^(day|week)$"),
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Get retention cohorts"""
    request = GetRetentionRequest(
        cohort_date=cohort_date,
        periods=periods,
        period_type=period_type,
    )

    retention = await use_cases.get_retention(request)
    return [RetentionPeriodResponse(**period) for period in retention]


@router.get("/top-events", response_model=list[TopEventResponse])
async def get_top_events(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    limit: int = Query(10, ge=1, le=50),
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Get top events by count"""
    events = await use_cases.get_top_events(start_date, end_date, limit)
    return [TopEventResponse(**event) for event in events]


@router.get("/active-users", response_model=list[ActiveUsersResponse])
async def get_active_users(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    interval: str = Query("day", regex="^(day|week|month)$"),
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Get active users over time"""
    users = await use_cases.get_active_users(start_date, end_date, interval)
    return [ActiveUsersResponse(**user) for user in users]


@router.get("/session-stats", response_model=SessionStatsResponse)
async def get_session_stats(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Get session statistics"""
    stats = await use_cases.get_session_stats(start_date, end_date)
    return SessionStatsResponse(**stats)


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Get dashboard statistics"""
    stats = await use_cases.get_dashboard_stats(start_date, end_date)
    return DashboardStatsResponse(**stats)


@router.get("/user-journey/{user_id}", response_model=list[dict])
async def get_user_journey(
    user_id: UUID,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Get user journey"""
    return await use_cases.get_user_journey(user_id, start_date, end_date)


@router.get("/conversion-report", response_model=dict)
async def get_conversion_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    use_cases: AnalyticsUseCases = Depends(get_analytics_use_cases),
):
    """Get conversion report"""
    return await use_cases.get_conversion_report(start_date, end_date)
