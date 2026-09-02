"""
SQLAlchemy Feedback Repository Implementation
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.feedback import Feedback
from ....domain.repositories.base import FilterParams, PaginatedResult, PaginationParams, SortParams
from ....domain.repositories.feedback_repository import FeedbackRepository
from ..models.feedback import FeedbackModel


class SQLAlchemyFeedbackRepository(FeedbackRepository):
    """SQLAlchemy implementation of Feedback repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Feedback | None:
        """Get feedback by ID"""
        stmt = select(FeedbackModel).where(FeedbackModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_ids(self, ids: list[UUID]) -> list[Feedback]:
        """Get multiple feedback by IDs"""
        stmt = select(FeedbackModel).where(FeedbackModel.id.in_(ids))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_by_user(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback by user"""
        stmt = select(FeedbackModel).where(FeedbackModel.user_id == user_id)
        count_stmt = select(func.count(FeedbackModel.id)).where(FeedbackModel.user_id == user_id)

        stmt = stmt.order_by(desc(FeedbackModel.created_at))

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

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback for an entity"""
        stmt = select(FeedbackModel).where(
            and_(
                FeedbackModel.entity_type == entity_type,
                FeedbackModel.entity_id == entity_id
            )
        )
        count_stmt = select(func.count(FeedbackModel.id)).where(
            and_(
                FeedbackModel.entity_type == entity_type,
                FeedbackModel.entity_id == entity_id
            )
        )

        stmt = stmt.order_by(desc(FeedbackModel.created_at))

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
    ) -> PaginatedResult[Feedback]:
        """List feedback with pagination, sorting, and filtering"""
        stmt = select(FeedbackModel)
        count_stmt = select(func.count(FeedbackModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(FeedbackModel, key):
                    column = getattr(FeedbackModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        if sort and hasattr(FeedbackModel, sort.field):
            column = getattr(FeedbackModel, sort.field)
            if sort.order.lower() == "desc":
                stmt = stmt.order_by(desc(column))
            else:
                stmt = stmt.order_by(asc(column))
        else:
            stmt = stmt.order_by(desc(FeedbackModel.created_at))

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

    async def add(self, entity: Feedback) -> Feedback:
        """Add a new feedback"""
        model = FeedbackModel.from_entity(entity)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def update(self, entity: Feedback) -> Feedback:
        """Update an existing feedback"""
        stmt = select(FeedbackModel).where(FeedbackModel.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Feedback with id {entity.id} not found")

        for key, value in entity.__dict__.items():
            if hasattr(model, key) and key not in ('id', 'created_at'):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        await self.session.flush()
        return model.to_entity()

    async def delete(self, id: UUID) -> bool:
        """Delete a feedback"""
        stmt = select(FeedbackModel).where(FeedbackModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        """Check if feedback exists"""
        stmt = select(func.count(FeedbackModel.id)).where(FeedbackModel.id == id)
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self, filters: FilterParams | None = None) -> int:
        """Count feedback with optional filters"""
        stmt = select(func.count(FeedbackModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(FeedbackModel, key):
                    column = getattr(FeedbackModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_stats(self) -> dict[str, Any]:
        """Get feedback statistics"""
        total_stmt = select(func.count(FeedbackModel.id))
        by_type_stmt = select(FeedbackModel.type, func.count(FeedbackModel.id)).group_by(FeedbackModel.type)
        by_status_stmt = select(FeedbackModel.status, func.count(FeedbackModel.id)).group_by(FeedbackModel.status)
        avg_rating_stmt = select(func.avg(FeedbackModel.rating)).where(FeedbackModel.rating.isnot(None))
        recent_stmt = select(func.count(FeedbackModel.id)).where(
            FeedbackModel.created_at >= datetime.utcnow().replace(day=1)
        )

        total = (await self.session.execute(total_stmt)).scalar() or 0
        by_type = dict((await self.session.execute(by_type_stmt)).all())
        by_status = dict((await self.session.execute(by_status_stmt)).all())
        avg_rating = (await self.session.execute(avg_rating_stmt)).scalar() or 0.0
        recent = (await self.session.execute(recent_stmt)).scalar() or 0

        return {
            "total": total,
            "by_type": {k.value: v for k, v in by_type.items()},
            "by_status": {k.value: v for k, v in by_status.items()},
            "average_rating": float(avg_rating),
            "new_this_month": recent,
        }
