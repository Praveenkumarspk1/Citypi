"""
SQLAlchemy POI Repository Implementation
"""
import builtins
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .....domain.entities.poi import POI, POICategory, POISource
from .....domain.repositories.base import (
    FilterParams,
    PaginatedResult,
    PaginationParams,
    SortParams,
)
from .....domain.repositories.poi_repository import POIRepository
from .....domain.value_objects.coordinates import Coordinates
from ..models.poi import POIModel


class SQLAlchemyPOIRepository(POIRepository):
    """SQLAlchemy implementation of POI repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> POI | None:
        """Get POI by ID"""
        stmt = select(POIModel).where(POIModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_ids(self, ids: list[UUID]) -> list[POI]:
        """Get multiple POIs by IDs"""
        stmt = select(POIModel).where(POIModel.id.in_(ids))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_by_external_id(self, external_id: str, source: POISource) -> POI | None:
        """Get POI by external ID and source"""
        stmt = select(POIModel).where(
            and_(POIModel.external_id == external_id, POIModel.source == source)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list(
        self,
        pagination: PaginationParams | None = None,
        sort: SortParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[POI]:
        """List POIs with pagination, sorting, and filtering"""
        stmt = select(POIModel)
        count_stmt = select(func.count(POIModel.id))

        # Apply filters
        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(POIModel, key):
                    column = getattr(POIModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        # Apply sorting
        if sort and hasattr(POIModel, sort.field):
            column = getattr(POIModel, sort.field)
            if sort.order.lower() == "desc":
                stmt = stmt.order_by(desc(column))
            else:
                stmt = stmt.order_by(asc(column))
        else:
            stmt = stmt.order_by(desc(POIModel.popularity_score))

        # Get total count
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
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

    async def add(self, entity: POI) -> POI:
        """Add a new POI"""
        model = POIModel.from_entity(entity)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def update(self, entity: POI) -> POI:
        """Update an existing POI"""
        stmt = select(POIModel).where(POIModel.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"POI with id {entity.id} not found")

        # Update fields
        for key, value in entity.__dict__.items():
            if hasattr(model, key) and key not in ('id', 'created_at'):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        await self.session.flush()
        return model.to_entity()

    async def delete(self, id: UUID) -> bool:
        """Delete a POI"""
        stmt = select(POIModel).where(POIModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        """Check if POI exists"""
        stmt = select(func.count(POIModel.id)).where(POIModel.id == id)
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self, filters: FilterParams | None = None) -> int:
        """Count POIs with optional filters"""
        stmt = select(func.count(POIModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(POIModel, key):
                    column = getattr(POIModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_by_category(
        self,
        category: POICategory,
        pagination: PaginationParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get POIs by category"""
        stmt = select(POIModel).where(POIModel.category == category)
        count_stmt = select(func.count(POIModel.id)).where(POIModel.category == category)

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(POIModel, key):
                    column = getattr(POIModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(POIModel.popularity_score))

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

    async def get_nearby(
        self,
        coordinates: Coordinates,
        radius_meters: float,
        categories: builtins.list[POICategory] | None = None,
        pagination: PaginationParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get POIs near coordinates using PostGIS"""
        # Convert radius to degrees (approximate)
        radius_deg = radius_meters / 111000.0

        stmt = select(POIModel).where(
            and_(
                POIModel.latitude.between(
                    coordinates.latitude - radius_deg,
                    coordinates.latitude + radius_deg
                ),
                POIModel.longitude.between(
                    coordinates.longitude - radius_deg,
                    coordinates.longitude + radius_deg
                )
            )
        )
        count_stmt = select(func.count(POIModel.id)).where(
            and_(
                POIModel.latitude.between(
                    coordinates.latitude - radius_deg,
                    coordinates.latitude + radius_deg
                ),
                POIModel.longitude.between(
                    coordinates.longitude - radius_deg,
                    coordinates.longitude + radius_deg
                )
            )
        )

        if categories:
            stmt = stmt.where(POIModel.category.in_(categories))
            count_stmt = count_stmt.where(POIModel.category.in_(categories))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(POIModel, key):
                    column = getattr(POIModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(POIModel.popularity_score))

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

    async def get_within_bounds(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        categories: builtins.list[POICategory] | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get POIs within bounding box"""
        stmt = select(POIModel).where(
            and_(
                POIModel.latitude.between(min_lat, max_lat),
                POIModel.longitude.between(min_lng, max_lng)
            )
        )
        count_stmt = select(func.count(POIModel.id)).where(
            and_(
                POIModel.latitude.between(min_lat, max_lat),
                POIModel.longitude.between(min_lng, max_lng)
            )
        )

        if categories:
            stmt = stmt.where(POIModel.category.in_(categories))
            count_stmt = count_stmt.where(POIModel.category.in_(categories))

        stmt = stmt.order_by(desc(POIModel.popularity_score))

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

    async def search(
        self,
        query: str,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        categories: builtins.list[POICategory] | None = None,
        pagination: PaginationParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[POI]:
        """Search POIs by name, description, tags"""
        search_term = f"%{query.lower()}%"

        stmt = select(POIModel).where(
            or_(
                func.lower(POIModel.name).like(search_term),
                func.lower(POIModel.description).like(search_term),
                func.lower(POIModel.tags.cast(text)).like(search_term),
            )
        )
        count_stmt = select(func.count(POIModel.id)).where(
            or_(
                func.lower(POIModel.name).like(search_term),
                func.lower(POIModel.description).like(search_term),
                func.lower(POIModel.tags.cast(text)).like(search_term),
            )
        )

        if coordinates and radius_meters:
            radius_deg = radius_meters / 111000.0
            stmt = stmt.where(
                and_(
                    POIModel.latitude.between(
                        coordinates.latitude - radius_deg,
                        coordinates.latitude + radius_deg
                    ),
                    POIModel.longitude.between(
                        coordinates.longitude - radius_deg,
                        coordinates.longitude + radius_deg
                    )
                )
            )
            count_stmt = count_stmt.where(
                and_(
                    POIModel.latitude.between(
                        coordinates.latitude - radius_deg,
                        coordinates.latitude + radius_deg
                    ),
                    POIModel.longitude.between(
                        coordinates.longitude - radius_deg,
                        coordinates.longitude + radius_deg
                    )
                )
            )

        if categories:
            stmt = stmt.where(POIModel.category.in_(categories))
            count_stmt = count_stmt.where(POIModel.category.in_(categories))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(POIModel, key):
                    column = getattr(POIModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(POIModel.popularity_score))

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

    async def get_popular(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        category: POICategory | None = None,
        limit: int = 20,
    ) -> builtins.list[POI]:
        """Get popular POIs"""
        stmt = select(POIModel).where(POIModel.is_active).order_by(
            desc(POIModel.popularity_score)
        )

        if coordinates and radius_meters:
            radius_deg = radius_meters / 111000.0
            stmt = stmt.where(
                and_(
                    POIModel.latitude.between(
                        coordinates.latitude - radius_deg,
                        coordinates.latitude + radius_deg
                    ),
                    POIModel.longitude.between(
                        coordinates.longitude - radius_deg,
                        coordinates.longitude + radius_deg
                    )
                )
            )

        if category:
            stmt = stmt.where(POIModel.category == category)

        stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_trending(
        self,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
        days: int = 7,
        limit: int = 20,
    ) -> builtins.list[POI]:
        """Get trending POIs (recently popular)"""
        from datetime import timedelta
        since = datetime.utcnow() - timedelta(days=days)

        stmt = select(POIModel).where(
            and_(
                POIModel.is_active,
                POIModel.last_visited_at >= since
            )
        ).order_by(desc(POIModel.visit_count))

        if coordinates and radius_meters:
            radius_deg = radius_meters / 111000.0
            stmt = stmt.where(
                and_(
                    POIModel.latitude.between(
                        coordinates.latitude - radius_deg,
                        coordinates.latitude + radius_deg
                    ),
                    POIModel.longitude.between(
                        coordinates.longitude - radius_deg,
                        coordinates.longitude + radius_deg
                    )
                )
            )

        stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_by_source(
        self,
        source: POISource,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get POIs by source"""
        stmt = select(POIModel).where(POIModel.source == source)
        count_stmt = select(func.count(POIModel.id)).where(POIModel.source == source)

        stmt = stmt.order_by(desc(POIModel.created_at))

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

    async def get_verified(
        self,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get verified POIs"""
        stmt = select(POIModel).where(POIModel.is_verified)
        count_stmt = select(func.count(POIModel.id)).where(POIModel.is_verified)

        stmt = stmt.order_by(desc(POIModel.popularity_score))

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

    async def get_unverified(
        self,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[POI]:
        """Get unverified POIs"""
        stmt = select(POIModel).where(not POIModel.is_verified)
        count_stmt = select(func.count(POIModel.id)).where(not POIModel.is_verified)

        stmt = stmt.order_by(desc(POIModel.created_at))

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

    async def get_without_embedding(
        self,
        limit: int = 100,
    ) -> builtins.list[POI]:
        """Get POIs without vector embeddings"""
        stmt = select(POIModel).where(
            and_(
                POIModel.is_active,
                or_(POIModel.embedding_id.is_(None), POIModel.embedding_id == "")
            )
        ).order_by(desc(POIModel.popularity_score)).limit(limit)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def update_rating(self, poi_id: UUID, rating: float, review_count: int) -> None:
        """Update POI rating"""
        stmt = select(POIModel).where(POIModel.id == poi_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.rating = rating
            model.review_count = review_count
            model.user_ratings_total = review_count
            model.updated_at = datetime.utcnow()
            await self.session.flush()

    async def increment_visit_count(self, poi_id: UUID) -> None:
        """Increment POI visit count"""
        stmt = select(POIModel).where(POIModel.id == poi_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.visit_count += 1
            model.last_visited_at = datetime.utcnow()
            model.updated_at = datetime.utcnow()
            await self.session.flush()

    async def update_popularity(self, poi_id: UUID, score: float) -> None:
        """Update POI popularity score"""
        stmt = select(POIModel).where(POIModel.id == poi_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.popularity_score = score
            model.updated_at = datetime.utcnow()
            await self.session.flush()

    async def set_embedding_id(self, poi_id: UUID, embedding_id: str) -> None:
        """Set vector embedding reference"""
        stmt = select(POIModel).where(POIModel.id == poi_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.embedding_id = embedding_id
            model.updated_at = datetime.utcnow()
            await self.session.flush()

    async def get_by_ids_with_details(self, ids: builtins.list[UUID]) -> builtins.list[POI]:
        """Get POIs by IDs with full details"""
        stmt = select(POIModel).where(POIModel.id.in_(ids))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_stats(self) -> dict[str, Any]:
        """Get POI statistics"""
        total_stmt = select(func.count(POIModel.id))
        active_stmt = select(func.count(POIModel.id)).where(POIModel.is_active)
        verified_stmt = select(func.count(POIModel.id)).where(POIModel.is_verified)
        by_category_stmt = select(POIModel.category, func.count(POIModel.id)).group_by(POIModel.category)
        by_source_stmt = select(POIModel.source, func.count(POIModel.id)).group_by(POIModel.source)
        avg_rating_stmt = select(func.avg(POIModel.rating)).where(POIModel.rating.isnot(None))

        total = (await self.session.execute(total_stmt)).scalar() or 0
        active = (await self.session.execute(active_stmt)).scalar() or 0
        verified = (await self.session.execute(verified_stmt)).scalar() or 0
        by_category = dict((await self.session.execute(by_category_stmt)).all())
        by_source = dict((await self.session.execute(by_source_stmt)).all())
        avg_rating = (await self.session.execute(avg_rating_stmt)).scalar() or 0.0

        return {
            "total": total,
            "active": active,
            "verified": verified,
            "by_category": {k.value: v for k, v in by_category.items()},
            "by_source": {k.value: v for k, v in by_source.items()},
            "average_rating": float(avg_rating),
        }

    async def bulk_upsert(self, pois: builtins.list[POI]) -> builtins.list[POI]:
        """Bulk upsert POIs"""
        results = []
        for poi in pois:
            # Check if exists by external_id and source
            existing = await self.get_by_external_id(poi.external_id, poi.source)
            if existing:
                poi.id = existing.id
                updated = await self.update(poi)
                results.append(updated)
            else:
                added = await self.add(poi)
                results.append(added)
        return results

    async def delete_by_source(self, source: POISource) -> int:
        """Delete all POIs from a source"""
        stmt = select(POIModel).where(POIModel.source == source)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        count = len(models)
        for model in models:
            await self.session.delete(model)

        await self.session.flush()
        return count
