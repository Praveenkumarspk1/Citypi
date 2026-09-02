"""
SQLAlchemy Media Repository Implementation
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.media import Media, MediaStatus
from ....domain.repositories.base import FilterParams, PaginatedResult, PaginationParams, SortParams
from ....domain.repositories.media_repository import MediaRepository
from ..models.media import MediaModel


class SQLAlchemyMediaRepository(MediaRepository):
    """SQLAlchemy implementation of Media repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Media | None:
        """Get media by ID"""
        stmt = select(MediaModel).where(MediaModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_ids(self, ids: list[UUID]) -> list[Media]:
        """Get multiple media by IDs"""
        stmt = select(MediaModel).where(MediaModel.id.in_(ids))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> list[Media]:
        """Get media for an entity"""
        stmt = select(MediaModel).where(
            and_(
                MediaModel.entity_type == entity_type,
                MediaModel.entity_id == entity_id
            )
        ).order_by(MediaModel.order, MediaModel.created_at)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_by_user(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Media]:
        """Get media by user"""
        stmt = select(MediaModel).where(MediaModel.user_id == user_id)
        count_stmt = select(func.count(MediaModel.id)).where(MediaModel.user_id == user_id)

        stmt = stmt.order_by(desc(MediaModel.created_at))

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
    ) -> PaginatedResult[Media]:
        """List media with pagination, sorting, and filtering"""
        stmt = select(MediaModel)
        count_stmt = select(func.count(MediaModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(MediaModel, key):
                    column = getattr(MediaModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        if sort and hasattr(MediaModel, sort.field):
            column = getattr(MediaModel, sort.field)
            if sort.order.lower() == "desc":
                stmt = stmt.order_by(desc(column))
            else:
                stmt = stmt.order_by(asc(column))
        else:
            stmt = stmt.order_by(desc(MediaModel.created_at))

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

    async def add(self, entity: Media) -> Media:
        """Add a new media"""
        model = MediaModel.from_entity(entity)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def update(self, entity: Media) -> Media:
        """Update an existing media"""
        stmt = select(MediaModel).where(MediaModel.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Media with id {entity.id} not found")

        for key, value in entity.__dict__.items():
            if hasattr(model, key) and key not in ('id', 'created_at'):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        await self.session.flush()
        return model.to_entity()

    async def delete(self, id: UUID) -> bool:
        """Delete a media"""
        stmt = select(MediaModel).where(MediaModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        """Check if media exists"""
        stmt = select(func.count(MediaModel.id)).where(MediaModel.id == id)
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self, filters: FilterParams | None = None) -> int:
        """Count media with optional filters"""
        stmt = select(func.count(MediaModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(MediaModel, key):
                    column = getattr(MediaModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update_processing_status(
        self,
        media_id: UUID,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update media processing status"""
        stmt = select(MediaModel).where(MediaModel.id == media_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.status = MediaStatus(status)
            if metadata:
                model.processing_metadata = metadata
            model.updated_at = datetime.utcnow()
            await self.session.flush()
