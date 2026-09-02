"""
SQLAlchemy Analytics Repository Implementation
"""
import builtins
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_smart_city_concierge.domain.entities.analytics import AnalyticsEvent, AnalyticsMetric
from ai_smart_city_concierge.domain.repositories.analytics_repository import AnalyticsRepository
from ai_smart_city_concierge.domain.repositories.base import FilterParams, PaginatedResult, PaginationParams, SortParams
from ..models.analytics import AnalyticsEventModel, AnalyticsMetricModel


class SQLAlchemyAnalyticsRepository(AnalyticsRepository):
    """SQLAlchemy implementation of Analytics repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> AnalyticsEvent | None:
        """Get analytics event by ID"""
        stmt = select(AnalyticsEventModel).where(AnalyticsEventModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_ids(self, ids: list[UUID]) -> list[AnalyticsEvent]:
        """Get multiple analytics events by IDs"""
        stmt = select(AnalyticsEventModel).where(AnalyticsEventModel.id.in_(ids))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def list(
        self,
        pagination: PaginationParams | None = None,
        sort: SortParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[AnalyticsEvent]:
        """List analytics events with pagination, sorting, and filtering"""
        stmt = select(AnalyticsEventModel)
        count_stmt = select(func.count(AnalyticsEventModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(AnalyticsEventModel, key):
                    column = getattr(AnalyticsEventModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        if sort and hasattr(AnalyticsEventModel, sort.field):
            column = getattr(AnalyticsEventModel, sort.field)
            if sort.order.lower() == "desc":
                stmt = stmt.order_by(desc(column))
            else:
                stmt = stmt.order_by(asc(column))
        else:
            stmt = stmt.order_by(desc(AnalyticsEventModel.created_at))

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        if pagination:
            stmt = stmt.offset((pagination.page - 1) * pagination.page_size)
            stmt = stmt.limit(pagination.page_size)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        items = [m.to_entity() for m in models]

        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else len(items)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    async def add(self, entity: AnalyticsEvent) -> AnalyticsEvent:
        """Add a new analytics event"""
        model = AnalyticsEventModel.from_entity(entity)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def update(self, entity: AnalyticsEvent) -> AnalyticsEvent:
        """Update an existing analytics event"""
        stmt = select(AnalyticsEventModel).where(AnalyticsEventModel.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"AnalyticsEvent with id {entity.id} not found")

        for key, value in entity.__dict__.items():
            if hasattr(model, key) and key not in ('id', 'created_at'):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        await self.session.flush()
        return model.to_entity()

    async def delete(self, id: UUID) -> bool:
        """Delete an analytics event"""
        stmt = select(AnalyticsEventModel).where(AnalyticsEventModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        """Check if analytics event exists"""
        stmt = select(func.count(AnalyticsEventModel.id)).where(AnalyticsEventModel.id == id)
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self, filters: FilterParams | None = None) -> int:
        """Count analytics events with optional filters"""
        stmt = select(func.count(AnalyticsEventModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(AnalyticsEventModel, key):
                    column = getattr(AnalyticsEventModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def track_event(
        self,
        event_name: str,
        user_id: UUID | None = None,
        session_id: str | None = None,
        properties: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> AnalyticsEvent:
        """Track an analytics event"""
        event = AnalyticsEvent(
            event_name=event_name,
            user_id=user_id,
            session_id=session_id,
            properties=properties or {},
            context=context or {},
        )
        return await self.add(event)

    async def track_metric(
        self,
        metric_name: str,
        value: float,
        dimensions: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> AnalyticsMetric:
        """Track a metric"""
        metric = AnalyticsMetric(
            metric_name=metric_name,
            value=value,
            dimensions=dimensions or {},
            timestamp=timestamp or datetime.utcnow(),
        )
        model = AnalyticsMetricModel.from_entity(metric)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def get_events_by_user(
        self,
        user_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        event_names: builtins.list[str] | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[AnalyticsEvent]:
        """Get events for a user"""
        stmt = select(AnalyticsEventModel).where(AnalyticsEventModel.user_id == user_id)
        count_stmt = select(func.count(AnalyticsEventModel.id)).where(AnalyticsEventModel.user_id == user_id)

        if start_date:
            stmt = stmt.where(AnalyticsEventModel.created_at >= start_date)
            count_stmt = count_stmt.where(AnalyticsEventModel.created_at >= start_date)

        if end_date:
            stmt = stmt.where(AnalyticsEventModel.created_at <= end_date)
            count_stmt = count_stmt.where(AnalyticsEventModel.created_at <= end_date)

        if event_names:
            stmt = stmt.where(AnalyticsEventModel.event_name.in_(event_names))
            count_stmt = count_stmt.where(AnalyticsEventModel.event_name.in_(event_names))

        stmt = stmt.order_by(desc(AnalyticsEventModel.created_at))

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        if pagination:
            stmt = stmt.offset((pagination.page - 1) * pagination.page_size)
            stmt = stmt.limit(pagination.page_size)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        items = [m.to_entity() for m in models]

        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else len(items)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    async def get_metrics(
        self,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        dimensions: dict[str, str] | None = None,
        interval: str = "hour",
    ) -> builtins.list[dict[str, Any]]:
        """Get aggregated metrics"""
        # Build time bucket expression
        if interval == "minute":
            bucket = func.date_trunc('minute', AnalyticsMetricModel.timestamp)
        elif interval == "hour":
            bucket = func.date_trunc('hour', AnalyticsMetricModel.timestamp)
        elif interval == "day":
            bucket = func.date_trunc('day', AnalyticsMetricModel.timestamp)
        else:
            bucket = func.date_trunc('hour', AnalyticsMetricModel.timestamp)

        stmt = select(
            bucket.label('bucket'),
            func.avg(AnalyticsMetricModel.value).label('avg_value'),
            func.min(AnalyticsMetricModel.value).label('min_value'),
            func.max(AnalyticsMetricModel.value).label('max_value'),
            func.count(AnalyticsMetricModel.value).label('count'),
        ).where(
            and_(
                AnalyticsMetricModel.metric_name == metric_name,
                AnalyticsMetricModel.timestamp >= start_date,
                AnalyticsMetricModel.timestamp <= end_date,
            )
        ).group_by(bucket).order_by(bucket)

        if dimensions:
            for key, value in dimensions.items():
                stmt = stmt.where(getattr(AnalyticsMetricModel, f"dim_{key}") == value)

        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            {
                "timestamp": row.bucket,
                "avg": float(row.avg_value) if row.avg_value else 0,
                "min": float(row.min_value) if row.min_value else 0,
                "max": float(row.max_value) if row.max_value else 0,
                "count": row.count,
            }
            for row in rows
        ]

    async def get_funnel(
        self,
        steps: builtins.list[str],
        start_date: datetime,
        end_date: datetime,
        user_id: UUID | None = None,
    ) -> builtins.list[dict[str, Any]]:
        """Get funnel conversion rates"""
        results = []

        for i, step in enumerate(steps):
            stmt = select(func.count(func.distinct(AnalyticsEventModel.user_id))).where(
                and_(
                    AnalyticsEventModel.event_name == step,
                    AnalyticsEventModel.created_at >= start_date,
                    AnalyticsEventModel.created_at <= end_date,
                )
            )

            if user_id:
                stmt = stmt.where(AnalyticsEventModel.user_id == user_id)

            result = await self.session.execute(stmt)
            count = result.scalar() or 0

            conversion_rate = 100.0
            if i > 0 and results[i-1]["count"] > 0:
                conversion_rate = (count / results[i-1]["count"]) * 100

            results.append({
                "step": step,
                "count": count,
                "conversion_rate": conversion_rate,
            })

        return results

    async def get_retention(
        self,
        cohort_date: datetime,
        periods: int = 7,
        period_type: str = "day",
    ) -> builtins.list[dict[str, Any]]:
        """Get retention cohorts"""
        # This is a simplified implementation
        # In production, you'd use a more sophisticated cohort analysis
        results = []

        for period in range(periods):
            if period_type == "day":
                period_start = cohort_date + timedelta(days=period)
                period_end = period_start + timedelta(days=1)
            else:
                period_start = cohort_date + timedelta(weeks=period)
                period_end = period_start + timedelta(weeks=1)

            # Get users who had first event in cohort period
            cohort_stmt = select(func.count(func.distinct(AnalyticsEventModel.user_id))).where(
                and_(
                    AnalyticsEventModel.created_at >= cohort_date,
                    AnalyticsEventModel.created_at < cohort_date + timedelta(days=1),
                )
            )
            cohort_result = await self.session.execute(cohort_stmt)
            cohort_size = cohort_result.scalar() or 0

            # Get users who returned in this period
            if cohort_size > 0:
                return_stmt = select(func.count(func.distinct(AnalyticsEventModel.user_id))).where(
                    and_(
                        AnalyticsEventModel.user_id.in_(
                            select(AnalyticsEventModel.user_id).where(
                                and_(
                                    AnalyticsEventModel.created_at >= cohort_date,
                                    AnalyticsEventModel.created_at < cohort_date + timedelta(days=1),
                                )
                            )
                        ),
                        AnalyticsEventModel.created_at >= period_start,
                        AnalyticsEventModel.created_at < period_end,
                    )
                )
                return_result = await self.session.execute(return_stmt)
                returned = return_result.scalar() or 0
                retention_rate = (returned / cohort_size) * 100
            else:
                returned = 0
                retention_rate = 0

            results.append({
                "period": period,
                "period_start": period_start,
                "cohort_size": cohort_size,
                "returned": returned,
                "retention_rate": retention_rate,
            })

        return results

    async def get_top_events(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
    ) -> builtins.list[dict[str, Any]]:
        """Get top events by count"""
        stmt = select(
            AnalyticsEventModel.event_name,
            func.count(AnalyticsEventModel.id).label('count'),
            func.count(func.distinct(AnalyticsEventModel.user_id)).label('unique_users'),
        ).where(
            and_(
                AnalyticsEventModel.created_at >= start_date,
                AnalyticsEventModel.created_at <= end_date,
            )
        ).group_by(AnalyticsEventModel.event_name).order_by(
            desc(func.count(AnalyticsEventModel.id))
        ).limit(limit)

        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            {
                "event_name": row.event_name,
                "count": row.count,
                "unique_users": row.unique_users,
            }
            for row in rows
        ]

    async def get_active_users(
        self,
        start_date: datetime,
        end_date: datetime,
        interval: str = "day",
    ) -> builtins.list[dict[str, Any]]:
        """Get active users over time"""
        if interval == "day":
            bucket = func.date_trunc('day', AnalyticsEventModel.created_at)
        elif interval == "week":
            bucket = func.date_trunc('week', AnalyticsEventModel.created_at)
        else:
            bucket = func.date_trunc('month', AnalyticsEventModel.created_at)

        stmt = select(
            bucket.label('bucket'),
            func.count(func.distinct(AnalyticsEventModel.user_id)).label('active_users'),
        ).where(
            and_(
                AnalyticsEventModel.created_at >= start_date,
                AnalyticsEventModel.created_at <= end_date,
                AnalyticsEventModel.user_id.isnot(None),
            )
        ).group_by(bucket).order_by(bucket)

        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            {
                "date": row.bucket,
                "active_users": row.active_users,
            }
            for row in rows
        ]

    async def get_session_stats(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Get session statistics"""
        # Average session duration
        duration_stmt = select(func.avg(AnalyticsEventModel.session_duration)).where(
            and_(
                AnalyticsEventModel.created_at >= start_date,
                AnalyticsEventModel.created_at <= end_date,
                AnalyticsEventModel.session_duration.isnot(None),
            )
        )
        avg_duration = (await self.session.execute(duration_stmt)).scalar() or 0

        # Sessions count
        sessions_stmt = select(func.count(func.distinct(AnalyticsEventModel.session_id))).where(
            and_(
                AnalyticsEventModel.created_at >= start_date,
                AnalyticsEventModel.created_at <= end_date,
                AnalyticsEventModel.session_id.isnot(None),
            )
        )
        sessions = (await self.session.execute(sessions_stmt)).scalar() or 0

        # Events per session
        events_stmt = select(func.count(AnalyticsEventModel.id)).where(
            and_(
                AnalyticsEventModel.created_at >= start_date,
                AnalyticsEventModel.created_at <= end_date,
            )
        )
        events = (await self.session.execute(events_stmt)).scalar() or 0

        events_per_session = events / sessions if sessions > 0 else 0

        return {
            "total_sessions": sessions,
            "total_events": events,
            "avg_session_duration": float(avg_duration),
            "events_per_session": events_per_session,
        }
