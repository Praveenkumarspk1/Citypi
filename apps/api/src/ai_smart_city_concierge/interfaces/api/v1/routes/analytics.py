"""
Analytics Routes
"""
from datetime import date, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ai_smart_city_concierge.application.dto.response import (
    AnalyticsEventResponse,
    CohortAnalysisResponse,
    DailyMetricsResponse,
    FeatureUsageResponse,
    FunnelAnalysisResponse,
    PaginatedResponse,
    UserMetricsResponse,
)
from ai_smart_city_concierge.domain.entities.analytics import EventSource, EventType
from ai_smart_city_concierge.infrastructure.auth import get_current_user
from ai_smart_city_concierge.infrastructure.di.container import get_analytics_use_cases
from ai_smart_city_concierge.application.use_cases.analytics_use_cases import AnalyticsUseCases

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/events", response_model=AnalyticsEventResponse, status_code=status.HTTP_201_CREATED)
async def record_event(
    event_type: EventType,
    properties: dict[str, Any] = None,
    session_id: str | None = None,
    source: EventSource = EventSource.WEB,
    app_version: str | None = None,
    platform: str | None = None,
    device_id: str | None = None,
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    city: str | None = None,
    country: str | None = None,
    correlation_id: str | None = None,
    experiment_id: str | None = None,
    variant: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> AnalyticsEventResponse:
    """Record an analytics event"""
    if properties is None:
        properties = {}
    service = get_analytics_service()

    coordinates = {"lat": lat, "lng": lng} if lat is not None and lng is not None else None

    event = await service.record_event(
        event_type=event_type,
        user_id=UUID(current_user["id"]) if current_user else None,
        session_id=session_id,
        properties=properties,
        source=source,
        app_version=app_version,
        platform=platform,
        device_id=device_id,
        coordinates=coordinates,
        city=city,
        country=country,
        correlation_id=correlation_id,
        experiment_id=experiment_id,
        variant=variant,
    )
    return AnalyticsEventResponse.from_entity(event)


@router.post("/events/batch", response_model=list[AnalyticsEventResponse])
async def record_events_batch(
    events: list[dict[str, Any]],
    current_user: dict = Depends(get_current_user),
) -> list[AnalyticsEventResponse]:
    """Record multiple analytics events"""
    service = get_analytics_service()

    # Convert to AnalyticsEvent objects
    from ai_smart_city_concierge.domain.entities.analytics import AnalyticsEvent
    event_objects = []
    for e in events:
        event = AnalyticsEvent(
            event_type=EventType(e["event_type"]),
            user_id=UUID(current_user["id"]) if current_user else None,
            session_id=e.get("session_id"),
            properties=e.get("properties", {}),
            source=EventSource(e.get("source", "web")),
            app_version=e.get("app_version"),
            platform=e.get("platform"),
            device_id=e.get("device_id"),
            coordinates=e.get("coordinates"),
            city=e.get("city"),
            country=e.get("country"),
            correlation_id=e.get("correlation_id"),
            experiment_id=e.get("experiment_id"),
            variant=e.get("variant"),
        )
        event_objects.append(event)

    await service.record_events_batch(event_objects)
    return [AnalyticsEventResponse.from_entity(e) for e in event_objects]


@router.get("/events", response_model=PaginatedResponse[AnalyticsEventResponse])
async def get_events(
    user_id: UUID | None = None,
    event_type: EventType | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[AnalyticsEventResponse]:
    """Get analytics events (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    events = await service.get_events(
        user_id=user_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[AnalyticsEventResponse.from_entity(e) for e in events.items],
        total=events.total,
        page=events.page,
        page_size=events.page_size,
        total_pages=events.total_pages,
        has_next=events.has_next,
        has_prev=events.has_prev,
    )


@router.get("/events/session/{session_id}", response_model=list[AnalyticsEventResponse])
async def get_events_by_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> list[AnalyticsEventResponse]:
    """Get events for a session"""
    service = get_analytics_service()
    events = await service.get_events_by_session(session_id)
    return [AnalyticsEventResponse.from_entity(e) for e in events]


# Daily Metrics
@router.get("/metrics/daily", response_model=list[DailyMetricsResponse])
async def get_daily_metrics(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: dict = Depends(get_current_user),
) -> list[DailyMetricsResponse]:
    """Get daily metrics for date range (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    metrics = await service.get_daily_metrics(start_date, end_date)
    return [DailyMetricsResponse.from_entity(m) for m in metrics]


@router.get("/metrics/daily/{target_date}", response_model=DailyMetricsResponse)
async def get_daily_metric(
    target_date: date,
    current_user: dict = Depends(get_current_user),
) -> DailyMetricsResponse:
    """Get daily metrics for specific date (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    metrics = await service.get_daily_metric(target_date)
    if not metrics:
        raise HTTPException(status_code=404, detail="Metrics not found")
    return DailyMetricsResponse.from_entity(metrics)


@router.post("/metrics/daily/calculate/{target_date}", response_model=DailyMetricsResponse)
async def calculate_daily_metrics(
    target_date: date,
    current_user: dict = Depends(get_current_user),
) -> DailyMetricsResponse:
    """Calculate daily metrics from events (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    metrics = await service.calculate_daily_metrics(target_date)
    return DailyMetricsResponse.from_entity(metrics)


# User Metrics
@router.get("/metrics/user/{user_id}", response_model=UserMetricsResponse)
async def get_user_metrics(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> UserMetricsResponse:
    """Get user metrics"""
    if current_user.get("role") != "admin" and str(user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    service = get_analytics_service()
    metrics = await service.get_user_metrics(user_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="User metrics not found")
    return UserMetricsResponse.from_entity(metrics)


@router.get("/metrics/users/top", response_model=list[UserMetricsResponse])
async def get_top_users(
    metric: str = Query("engagement_score"),
    limit: int = Query(100, ge=1, le=1000),
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: dict = Depends(get_current_user),
) -> list[UserMetricsResponse]:
    """Get top users by metric (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    users = await service.get_top_users(metric, limit, start_date, end_date)
    return [UserMetricsResponse.from_entity(u) for u in users]


@router.get("/metrics/users/at-risk", response_model=list[UserMetricsResponse])
async def get_users_at_risk(
    churn_threshold: float = Query(0.7, ge=0, le=1),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
) -> list[UserMetricsResponse]:
    """Get users at risk of churning (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    users = await service.get_users_at_risk(churn_threshold, limit)
    return [UserMetricsResponse.from_entity(u) for u in users]


# Funnel Analysis
@router.get("/funnel/{name}", response_model=FunnelAnalysisResponse)
async def get_funnel_analysis(
    name: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    segment: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> FunnelAnalysisResponse:
    """Get funnel analysis (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    funnel = await service.get_funnel_analysis(name, start_date, end_date, segment)
    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel not found")
    return FunnelAnalysisResponse.from_entity(funnel)


@router.post("/funnel/calculate", response_model=FunnelAnalysisResponse)
async def calculate_funnel(
    name: str,
    steps: list[EventType],
    start_date: date,
    end_date: date,
    segment: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> FunnelAnalysisResponse:
    """Calculate funnel analysis (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    funnel = await service.calculate_funnel(name, steps, start_date, end_date, segment)
    return FunnelAnalysisResponse.from_entity(funnel)


# Cohort Analysis
@router.get("/cohort/{cohort_date}", response_model=CohortAnalysisResponse)
async def get_cohort_analysis(
    cohort_date: date,
    segment: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> CohortAnalysisResponse:
    """Get cohort analysis (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    cohort = await service.get_cohort_analysis(cohort_date, segment)
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")
    return CohortAnalysisResponse.from_entity(cohort)


@router.post("/cohort/calculate", response_model=CohortAnalysisResponse)
async def calculate_cohort(
    cohort_date: date,
    segment: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> CohortAnalysisResponse:
    """Calculate cohort retention (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    cohort = await service.calculate_cohort(cohort_date, segment)
    return CohortAnalysisResponse.from_entity(cohort)


@router.get("/cohorts", response_model=list[CohortAnalysisResponse])
async def get_cohorts(
    start_date: date = Query(...),
    end_date: date = Query(...),
    segment: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> list[CohortAnalysisResponse]:
    """Get multiple cohorts (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    cohorts = await service.get_cohorts(start_date, end_date, segment)
    return [CohortAnalysisResponse.from_entity(c) for c in cohorts]


# Feature Usage
@router.get("/features/{feature}", response_model=FeatureUsageResponse)
async def get_feature_usage(
    feature: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: dict = Depends(get_current_user),
) -> FeatureUsageResponse:
    """Get feature usage statistics (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    usage = await service.get_feature_usage(feature, start_date, end_date)
    if not usage:
        raise HTTPException(status_code=404, detail="Feature usage not found")
    return FeatureUsageResponse.from_entity(usage)


@router.post("/features/calculate", response_model=FeatureUsageResponse)
async def calculate_feature_usage(
    feature: str,
    start_date: date,
    end_date: date,
    current_user: dict = Depends(get_current_user),
) -> FeatureUsageResponse:
    """Calculate feature usage (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    usage = await service.calculate_feature_usage(feature, start_date, end_date)
    return FeatureUsageResponse.from_entity(usage)


@router.get("/features", response_model=list[FeatureUsageResponse])
async def get_all_feature_usage(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: dict = Depends(get_current_user),
) -> list[FeatureUsageResponse]:
    """Get usage for all features (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    features = await service.get_all_feature_usage(start_date, end_date)
    return [FeatureUsageResponse.from_entity(f) for f in features]


# Real-time / Aggregations
@router.get("/realtime/active-users")
async def get_realtime_active_users(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get current active users (last 5 minutes) (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    count = await service.get_realtime_active_users()
    return {"active_users": count}


@router.get("/events/counts")
async def get_event_counts(
    event_types: list[EventType] = Query(...),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    group_by: str = Query("hour"),
    current_user: dict = Depends(get_current_user),
) -> dict[str, list[dict[str, Any]]]:
    """Get event counts grouped by time (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    return await service.get_event_counts(event_types, start_date, end_date, group_by)


@router.get("/retention/{cohort_date}")
async def get_user_retention(
    cohort_date: date,
    days: list[int] = Query([1, 7, 30]),
    current_user: dict = Depends(get_current_user),
) -> dict[int, float]:
    """Get retention rates for cohort (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    return await service.get_user_retention(cohort_date, days)


@router.get("/conversion-rate")
async def get_conversion_rate(
    from_event: EventType = Query(...),
    to_event: EventType = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: dict = Depends(get_current_user),
) -> float:
    """Get conversion rate between two events (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    return await service.get_conversion_rate(from_event, to_event, start_date, end_date)


# Cleanup
@router.post("/cleanup/events")
async def cleanup_old_events(
    days: int = Query(90, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Clean up old events (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    deleted = await service.cleanup_old_events(days)
    return {"success": True, "deleted_count": deleted}


@router.get("/storage/stats")
async def get_storage_stats(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get storage statistics (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_analytics_service()
    return await service.get_storage_stats()
