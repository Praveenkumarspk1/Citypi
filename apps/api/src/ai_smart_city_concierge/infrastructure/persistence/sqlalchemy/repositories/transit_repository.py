"""
SQLAlchemy Transit Repository Implementation
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.transit import TransitRoute, TransitStop, TransitTrip
from ....domain.repositories.base import FilterParams, PaginatedResult, PaginationParams, SortParams
from ....domain.repositories.transit_repository import TransitRepository
from ....domain.value_objects.coordinates import Coordinates
from ..models.transit import TransitRouteModel, TransitStopModel, TransitTripModel


class SQLAlchemyTransitRepository(TransitRepository):
    """SQLAlchemy implementation of Transit repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # TransitRoute methods
    async def get_route_by_id(self, route_id: str) -> TransitRoute | None:
        """Get route by ID"""
        stmt = select(TransitRouteModel).where(TransitRouteModel.id == route_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_routes(
        self,
        agency_id: str | None = None,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[TransitRoute]:
        """Get transit routes"""
        stmt = select(TransitRouteModel)
        count_stmt = select(func.count(TransitRouteModel.id))

        if agency_id:
            stmt = stmt.where(TransitRouteModel.agency_id == agency_id)
            count_stmt = count_stmt.where(TransitRouteModel.agency_id == agency_id)

        if coordinates and radius_meters:
            radius_deg = radius_meters / 111000.0
            stmt = stmt.where(
                and_(
                    TransitRouteModel.bounds_min_lat.between(
                        coordinates.latitude - radius_deg,
                        coordinates.latitude + radius_deg
                    ),
                    TransitRouteModel.bounds_min_lng.between(
                        coordinates.longitude - radius_deg,
                        coordinates.longitude + radius_deg
                    )
                )
            )
            count_stmt = count_stmt.where(
                and_(
                    TransitRouteModel.bounds_min_lat.between(
                        coordinates.latitude - radius_deg,
                        coordinates.latitude + radius_deg
                    ),
                    TransitRouteModel.bounds_min_lng.between(
                        coordinates.longitude - radius_deg,
                        coordinates.longitude + radius_deg
                    )
                )
            )

        stmt = stmt.order_by(TransitRouteModel.short_name)

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

    # TransitStop methods
    async def get_stop_by_id(self, stop_id: str) -> TransitStop | None:
        """Get stop by ID"""
        stmt = select(TransitStopModel).where(TransitStopModel.id == stop_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_stops_nearby(
        self,
        coordinates: Coordinates,
        radius_meters: float = 500,
        modes: list[str] | None = None,
    ) -> list[TransitStop]:
        """Get transit stops near coordinates"""
        radius_deg = radius_meters / 111000.0

        stmt = select(TransitStopModel).where(
            and_(
                TransitStopModel.latitude.between(
                    coordinates.latitude - radius_deg,
                    coordinates.latitude + radius_deg
                ),
                TransitStopModel.longitude.between(
                    coordinates.longitude - radius_deg,
                    coordinates.longitude + radius_deg
                )
            )
        )

        if modes:
            stmt = stmt.where(TransitStopModel.mode.in_(modes))

        stmt = stmt.limit(100)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_routes_for_stop(self, stop_id: str) -> list[TransitRoute]:
        """Get routes serving a stop"""
        stmt = select(TransitRouteModel).where(
            TransitRouteModel.stop_ids.contains([stop_id])
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    # TransitTrip methods
    async def get_trips_for_route(
        self,
        route_id: str,
        date: datetime | None = None,
        direction_id: int | None = None,
    ) -> list[TransitTrip]:
        """Get trips for a route"""
        stmt = select(TransitTripModel).where(TransitTripModel.route_id == route_id)

        if date:
            stmt = stmt.where(TransitTripModel.service_date == date.date())

        if direction_id is not None:
            stmt = stmt.where(TransitTripModel.direction_id == direction_id)

        stmt = stmt.order_by(TransitTripModel.departure_time)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_schedule_for_stop(
        self,
        stop_id: str,
        date: datetime,
        route_ids: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get schedule for a stop"""
        stmt = select(TransitTripModel).where(
            and_(
                TransitTripModel.stop_ids.contains([stop_id]),
                TransitTripModel.service_date == date.date()
            )
        )

        if route_ids:
            stmt = stmt.where(TransitTripModel.route_id.in_(route_ids))

        stmt = stmt.order_by(TransitTripModel.departure_time).limit(limit)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_schedule_dict(stop_id) for m in models]

    async def get_realtime_arrivals(
        self,
        stop_id: str,
        route_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get real-time arrivals for a stop"""
        # This would typically query a real-time table
        # For now, return empty list
        return []

    async def get_alerts(
        self,
        route_ids: list[str] | None = None,
        stop_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get transit alerts"""
        # This would typically query an alerts table
        return []

    async def get_vehicle_positions(
        self,
        route_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get real-time vehicle positions"""
        # This would typically query a vehicle positions table
        return []

    # BaseRepository methods (minimal implementation)
    async def get_by_id(self, id: UUID) -> TransitRoute | None:
        return await self.get_route_by_id(str(id))

    async def get_by_ids(self, ids: list[UUID]) -> list[TransitRoute]:
        stmt = select(TransitRouteModel).where(TransitRouteModel.id.in_([str(i) for i in ids]))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def list(
        self,
        pagination: PaginationParams | None = None,
        sort: SortParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[TransitRoute]:
        return await self.get_routes(pagination=pagination)

    async def add(self, entity: TransitRoute) -> TransitRoute:
        model = TransitRouteModel.from_entity(entity)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def update(self, entity: TransitRoute) -> TransitRoute:
        stmt = select(TransitRouteModel).where(TransitRouteModel.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"TransitRoute with id {entity.id} not found")

        for key, value in entity.__dict__.items():
            if hasattr(model, key) and key not in ('id', 'created_at'):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        await self.session.flush()
        return model.to_entity()

    async def delete(self, id: UUID) -> bool:
        stmt = select(TransitRouteModel).where(TransitRouteModel.id == str(id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        stmt = select(func.count(TransitRouteModel.id)).where(TransitRouteModel.id == str(id))
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self, filters: FilterParams | None = None) -> int:
        stmt = select(func.count(TransitRouteModel.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0
