"""
SQLAlchemy Itinerary Repository Implementation
"""
import builtins
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryItem,
    ItineraryStatus,
    ItineraryVisibility,
)
from ....domain.repositories.base import FilterParams, PaginatedResult, PaginationParams, SortParams
from ....domain.repositories.itinerary_repository import ItineraryRepository
from ..models.itinerary import ItineraryDayModel, ItineraryItemModel, ItineraryModel


class SQLAlchemyItineraryRepository(ItineraryRepository):
    """SQLAlchemy implementation of Itinerary repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Itinerary | None:
        """Get itinerary by ID"""
        stmt = select(ItineraryModel).where(ItineraryModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_ids(self, ids: list[UUID]) -> list[Itinerary]:
        """Get multiple itineraries by IDs"""
        stmt = select(ItineraryModel).where(ItineraryModel.id.in_(ids))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_by_user_id(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
        status: str | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Get itineraries by user ID"""
        stmt = select(ItineraryModel).where(ItineraryModel.user_id == user_id)
        count_stmt = select(func.count(ItineraryModel.id)).where(ItineraryModel.user_id == user_id)

        if status:
            stmt = stmt.where(ItineraryModel.status == status)
            count_stmt = count_stmt.where(ItineraryModel.status == status)

        stmt = stmt.order_by(desc(ItineraryModel.updated_at))

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

    async def get_public_itineraries(
        self,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Get public itineraries"""
        stmt = select(ItineraryModel).where(
            and_(
                ItineraryModel.visibility == ItineraryVisibility.PUBLIC,
                ItineraryModel.status == ItineraryStatus.ACTIVE
            )
        )
        count_stmt = select(func.count(ItineraryModel.id)).where(
            and_(
                ItineraryModel.visibility == ItineraryVisibility.PUBLIC,
                ItineraryModel.status == ItineraryStatus.ACTIVE
            )
        )

        stmt = stmt.order_by(desc(ItineraryModel.updated_at))

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

    async def get_shared_with_user(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Itinerary]:
        """Get itineraries shared with user"""
        stmt = select(ItineraryModel).where(
            and_(
                ItineraryModel.shared_with.contains([str(user_id)]),
                ItineraryModel.status == ItineraryStatus.ACTIVE
            )
        )
        count_stmt = select(func.count(ItineraryModel.id)).where(
            and_(
                ItineraryModel.shared_with.contains([str(user_id)]),
                ItineraryModel.status == ItineraryStatus.ACTIVE
            )
        )

        stmt = stmt.order_by(desc(ItineraryModel.updated_at))

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

    async def list(
        self,
        pagination: PaginationParams | None = None,
        sort: SortParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[Itinerary]:
        """List itineraries with pagination, sorting, and filtering"""
        stmt = select(ItineraryModel)
        count_stmt = select(func.count(ItineraryModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(ItineraryModel, key):
                    column = getattr(ItineraryModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        if sort and hasattr(ItineraryModel, sort.field):
            column = getattr(ItineraryModel, sort.field)
            if sort.order.lower() == "desc":
                stmt = stmt.order_by(desc(column))
            else:
                stmt = stmt.order_by(asc(column))
        else:
            stmt = stmt.order_by(desc(ItineraryModel.updated_at))

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

    async def add(self, entity: Itinerary) -> Itinerary:
        """Add a new itinerary"""
        model = ItineraryModel.from_entity(entity)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def update(self, entity: Itinerary) -> Itinerary:
        """Update an existing itinerary"""
        stmt = select(ItineraryModel).where(ItineraryModel.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Itinerary with id {entity.id} not found")

        for key, value in entity.__dict__.items():
            if hasattr(model, key) and key not in ('id', 'created_at'):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        await self.session.flush()
        return model.to_entity()

    async def delete(self, id: UUID) -> bool:
        """Delete an itinerary"""
        stmt = select(ItineraryModel).where(ItineraryModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        """Check if itinerary exists"""
        stmt = select(func.count(ItineraryModel.id)).where(ItineraryModel.id == id)
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self, filters: FilterParams | None = None) -> int:
        """Count itineraries with optional filters"""
        stmt = select(func.count(ItineraryModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(ItineraryModel, key):
                    column = getattr(ItineraryModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def add_day(self, itinerary_id: UUID, day: ItineraryDay) -> None:
        """Add day to itinerary"""
        model = ItineraryDayModel.from_entity(day)
        self.session.add(model)

        # Update itinerary's updated_at
        stmt = select(ItineraryModel).where(ItineraryModel.id == itinerary_id)
        result = await self.session.execute(stmt)
        itinerary_model = result.scalar_one_or_none()

        if itinerary_model:
            itinerary_model.updated_at = datetime.utcnow()

        await self.session.flush()

    async def update_day(self, day: ItineraryDay) -> None:
        """Update itinerary day"""
        stmt = select(ItineraryDayModel).where(ItineraryDayModel.id == day.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            for key, value in day.__dict__.items():
                if hasattr(model, key) and key not in ('id', 'created_at'):
                    setattr(model, key, value)
            await self.session.flush()

    async def remove_day(self, itinerary_id: UUID, day_id: UUID) -> None:
        """Remove day from itinerary"""
        stmt = select(ItineraryDayModel).where(ItineraryDayModel.id == day_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)

            # Update itinerary's updated_at
            stmt = select(ItineraryModel).where(ItineraryModel.id == itinerary_id)
            result = await self.session.execute(stmt)
            itinerary_model = result.scalar_one_or_none()

            if itinerary_model:
                itinerary_model.updated_at = datetime.utcnow()

            await self.session.flush()

    async def add_item(self, day_id: UUID, item: ItineraryItem) -> None:
        """Add item to itinerary day"""
        model = ItineraryItemModel.from_entity(item)
        self.session.add(model)

        # Update day's updated_at
        stmt = select(ItineraryDayModel).where(ItineraryDayModel.id == day_id)
        result = await self.session.execute(stmt)
        day_model = result.scalar_one_or_none()

        if day_model:
            day_model.updated_at = datetime.utcnow()

        await self.session.flush()

    async def update_item(self, item: ItineraryItem) -> None:
        """Update itinerary item"""
        stmt = select(ItineraryItemModel).where(ItineraryItemModel.id == item.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            for key, value in item.__dict__.items():
                if hasattr(model, key) and key not in ('id', 'created_at'):
                    setattr(model, key, value)
            await self.session.flush()

    async def remove_item(self, day_id: UUID, item_id: UUID) -> None:
        """Remove item from itinerary day"""
        stmt = select(ItineraryItemModel).where(ItineraryItemModel.id == item_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)

            # Update day's updated_at
            stmt = select(ItineraryDayModel).where(ItineraryDayModel.id == day_id)
            result = await self.session.execute(stmt)
            day_model = result.scalar_one_or_none()

            if day_model:
                day_model.updated_at = datetime.utcnow()

            await self.session.flush()

    async def reorder_items(self, day_id: UUID, item_ids: builtins.list[UUID]) -> None:
        """Reorder items in a day"""
        for index, item_id in enumerate(item_ids):
            stmt = select(ItineraryItemModel).where(ItineraryItemModel.id == item_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                model.order = index

        # Update day's updated_at
        stmt = select(ItineraryDayModel).where(ItineraryDayModel.id == day_id)
        result = await self.session.execute(stmt)
        day_model = result.scalar_one_or_none()

        if day_model:
            day_model.updated_at = datetime.utcnow()

        await self.session.flush()

    async def get_stats(self) -> dict[str, Any]:
        """Get itinerary statistics"""
        total_stmt = select(func.count(ItineraryModel.id))
        active_stmt = select(func.count(ItineraryModel.id)).where(ItineraryModel.status == ItineraryStatus.ACTIVE)
        completed_stmt = select(func.count(ItineraryModel.id)).where(ItineraryModel.status == ItineraryStatus.COMPLETED)
        draft_stmt = select(func.count(ItineraryModel.id)).where(ItineraryModel.status == ItineraryStatus.DRAFT)
        public_stmt = select(func.count(ItineraryModel.id)).where(ItineraryModel.visibility == ItineraryVisibility.PUBLIC)
        ai_generated_stmt = select(func.count(ItineraryModel.id)).where(ItineraryModel.is_ai_generated)
        by_status_stmt = select(ItineraryModel.status, func.count(ItineraryModel.id)).group_by(ItineraryModel.status)
        by_visibility_stmt = select(ItineraryModel.visibility, func.count(ItineraryModel.id)).group_by(ItineraryModel.visibility)

        total = (await self.session.execute(total_stmt)).scalar() or 0
        active = (await self.session.execute(active_stmt)).scalar() or 0
        completed = (await self.session.execute(completed_stmt)).scalar() or 0
        draft = (await self.session.execute(draft_stmt)).scalar() or 0
        public = (await self.session.execute(public_stmt)).scalar() or 0
        ai_generated = (await self.session.execute(ai_generated_stmt)).scalar() or 0
        by_status = dict((await self.session.execute(by_status_stmt)).all())
        by_visibility = dict((await self.session.execute(by_visibility_stmt)).all())

        return {
            "total": total,
            "active": active,
            "completed": completed,
            "draft": draft,
            "public": public,
            "ai_generated": ai_generated,
            "by_status": {k.value: v for k, v in by_status.items()},
            "by_visibility": {k.value: v for k, v in by_visibility.items()},
        }
