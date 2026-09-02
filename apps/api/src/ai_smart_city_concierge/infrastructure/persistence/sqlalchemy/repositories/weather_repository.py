"""
SQLAlchemy Weather Repository Implementation
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.weather import WeatherAlert, WeatherForecast
from ....domain.repositories.base import FilterParams, PaginatedResult, PaginationParams, SortParams
from ....domain.repositories.weather_repository import WeatherRepository
from ....domain.value_objects.coordinates import Coordinates
from ..models.weather import WeatherAlertModel, WeatherForecastModel


class SQLAlchemyWeatherRepository(WeatherRepository):
    """SQLAlchemy implementation of Weather repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_current_weather(
        self,
        coordinates: Coordinates,
    ) -> dict[str, Any] | None:
        """Get current weather"""
        # Find nearest weather station or cached forecast
        radius_deg = 0.1  # ~11km

        stmt = select(WeatherForecastModel).where(
            and_(
                WeatherForecastModel.latitude.between(
                    coordinates.latitude - radius_deg,
                    coordinates.latitude + radius_deg
                ),
                WeatherForecastModel.longitude.between(
                    coordinates.longitude - radius_deg,
                    coordinates.longitude + radius_deg
                ),
                WeatherForecastModel.forecast_date >= datetime.utcnow().date()
            )
        ).order_by(WeatherForecastModel.created_at.desc()).limit(1)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            return model.to_current_weather_dict()
        return None

    async def get_forecast(
        self,
        coordinates: Coordinates,
        days: int = 7,
    ) -> WeatherForecast | None:
        """Get weather forecast"""
        radius_deg = 0.1

        stmt = select(WeatherForecastModel).where(
            and_(
                WeatherForecastModel.latitude.between(
                    coordinates.latitude - radius_deg,
                    coordinates.latitude + radius_deg
                ),
                WeatherForecastModel.longitude.between(
                    coordinates.longitude - radius_deg,
                    coordinates.longitude + radius_deg
                ),
                WeatherForecastModel.forecast_date >= datetime.utcnow().date()
            )
        ).order_by(WeatherForecastModel.forecast_date).limit(days)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        if not models:
            return None

        # Combine into a single forecast entity
        return models[0].to_forecast_entity(models)

    async def get_alerts(
        self,
        coordinates: Coordinates,
    ) -> list[WeatherAlert]:
        """Get weather alerts"""
        radius_deg = 1.0  # ~111km for alerts

        stmt = select(WeatherAlertModel).where(
            and_(
                WeatherAlertModel.latitude.between(
                    coordinates.latitude - radius_deg,
                    coordinates.latitude + radius_deg
                ),
                WeatherAlertModel.longitude.between(
                    coordinates.longitude - radius_deg,
                    coordinates.longitude + radius_deg
                ),
                WeatherAlertModel.expires_at >= datetime.utcnow()
            )
        ).order_by(WeatherAlertModel.severity.desc())

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_historical(
        self,
        coordinates: Coordinates,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get historical weather"""
        radius_deg = 0.1

        stmt = select(WeatherForecastModel).where(
            and_(
                WeatherForecastModel.latitude.between(
                    coordinates.latitude - radius_deg,
                    coordinates.latitude + radius_deg
                ),
                WeatherForecastModel.longitude.between(
                    coordinates.longitude - radius_deg,
                    coordinates.longitude + radius_deg
                ),
                WeatherForecastModel.forecast_date.between(start_date.date(), end_date.date())
            )
        ).order_by(WeatherForecastModel.forecast_date)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_historical_dict() for m in models]

    # BaseRepository methods
    async def get_by_id(self, id: UUID) -> WeatherForecast | None:
        stmt = select(WeatherForecastModel).where(WeatherForecastModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_ids(self, ids: list[UUID]) -> list[WeatherForecast]:
        stmt = select(WeatherForecastModel).where(WeatherForecastModel.id.in_(ids))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def list(
        self,
        pagination: PaginationParams | None = None,
        sort: SortParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[WeatherForecast]:
        stmt = select(WeatherForecastModel)
        count_stmt = select(func.count(WeatherForecastModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(WeatherForecastModel, key):
                    column = getattr(WeatherForecastModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        if sort and hasattr(WeatherForecastModel, sort.field):
            column = getattr(WeatherForecastModel, sort.field)
            if sort.order.lower() == "desc":
                stmt = stmt.order_by(desc(column))
            else:
                stmt = stmt.order_by(asc(column))
        else:
            stmt = stmt.order_by(desc(WeatherForecastModel.created_at))

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

    async def add(self, entity: WeatherForecast) -> WeatherForecast:
        model = WeatherForecastModel.from_entity(entity)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def update(self, entity: WeatherForecast) -> WeatherForecast:
        stmt = select(WeatherForecastModel).where(WeatherForecastModel.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"WeatherForecast with id {entity.id} not found")

        for key, value in entity.__dict__.items():
            if hasattr(model, key) and key not in ('id', 'created_at'):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        await self.session.flush()
        return model.to_entity()

    async def delete(self, id: UUID) -> bool:
        stmt = select(WeatherForecastModel).where(WeatherForecastModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        stmt = select(func.count(WeatherForecastModel.id)).where(WeatherForecastModel.id == id)
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self, filters: FilterParams | None = None) -> int:
        stmt = select(func.count(WeatherForecastModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(WeatherForecastModel, key):
                    column = getattr(WeatherForecastModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar() or 0
