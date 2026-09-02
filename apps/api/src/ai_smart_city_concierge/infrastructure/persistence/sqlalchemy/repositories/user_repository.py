"""
SQLAlchemy User Repository Implementation
"""
import builtins
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.user import User, UserStatus
from ....domain.repositories.base import FilterParams, PaginatedResult, PaginationParams, SortParams
from ....domain.repositories.user_repository import UserRepository
from ..models.user import UserModel


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of User repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> User | None:
        """Get user by ID"""
        stmt = select(UserModel).where(UserModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_ids(self, ids: list[UUID]) -> list[User]:
        """Get multiple users by IDs"""
        stmt = select(UserModel).where(UserModel.id.in_(ids))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email"""
        stmt = select(UserModel).where(func.lower(UserModel.email) == email.lower())
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username"""
        stmt = select(UserModel).where(func.lower(UserModel.username) == username.lower())
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_provider(self, provider: str, provider_id: str) -> User | None:
        """Get user by OAuth provider"""
        stmt = select(UserModel).where(
            and_(UserModel.oauth_provider == provider, UserModel.oauth_provider_id == provider_id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list(
        self,
        pagination: PaginationParams | None = None,
        sort: SortParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[User]:
        """List users with pagination, sorting, and filtering"""
        stmt = select(UserModel)
        count_stmt = select(func.count(UserModel.id))

        # Apply filters
        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(UserModel, key):
                    column = getattr(UserModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        # Apply sorting
        if sort and hasattr(UserModel, sort.field):
            column = getattr(UserModel, sort.field)
            if sort.order.lower() == "desc":
                stmt = stmt.order_by(desc(column))
            else:
                stmt = stmt.order_by(asc(column))
        else:
            stmt = stmt.order_by(desc(UserModel.created_at))

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

    async def add(self, entity: User) -> User:
        """Add a new user"""
        model = UserModel.from_entity(entity)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def update(self, entity: User) -> User:
        """Update an existing user"""
        stmt = select(UserModel).where(UserModel.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"User with id {entity.id} not found")

        # Update fields
        for key, value in entity.__dict__.items():
            if hasattr(model, key) and key not in ('id', 'created_at'):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        await self.session.flush()
        return model.to_entity()

    async def delete(self, id: UUID) -> bool:
        """Delete a user"""
        stmt = select(UserModel).where(UserModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        """Check if user exists"""
        stmt = select(func.count(UserModel.id)).where(UserModel.id == id)
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self, filters: FilterParams | None = None) -> int:
        """Count users with optional filters"""
        stmt = select(func.count(UserModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(UserModel, key):
                    column = getattr(UserModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp"""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.last_login_at = datetime.utcnow()
            model.updated_at = datetime.utcnow()
            await self.session.flush()

    async def increment_itinerary_count(self, user_id: UUID) -> None:
        """Increment user's itinerary count"""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.itinerary_count += 1
            model.updated_at = datetime.utcnow()
            await self.session.flush()

    async def increment_favorites_count(self, user_id: UUID) -> None:
        """Increment user's favorites count"""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.favorites_count += 1
            model.updated_at = datetime.utcnow()
            await self.session.flush()

    async def increment_reviews_count(self, user_id: UUID) -> None:
        """Increment user's reviews count"""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.reviews_count += 1
            model.updated_at = datetime.utcnow()
            await self.session.flush()

    async def get_stats(self) -> dict[str, Any]:
        """Get user statistics"""
        total_stmt = select(func.count(UserModel.id))
        active_stmt = select(func.count(UserModel.id)).where(UserModel.status == UserStatus.ACTIVE)
        verified_stmt = select(func.count(UserModel.id)).where(UserModel.is_verified)
        by_role_stmt = select(UserModel.role, func.count(UserModel.id)).group_by(UserModel.role)
        by_status_stmt = select(UserModel.status, func.count(UserModel.id)).group_by(UserModel.status)
        recent_stmt = select(func.count(UserModel.id)).where(
            UserModel.created_at >= datetime.utcnow().replace(day=1)
        )

        total = (await self.session.execute(total_stmt)).scalar() or 0
        active = (await self.session.execute(active_stmt)).scalar() or 0
        verified = (await self.session.execute(verified_stmt)).scalar() or 0
        by_role = dict((await self.session.execute(by_role_stmt)).all())
        by_status = dict((await self.session.execute(by_status_stmt)).all())
        recent = (await self.session.execute(recent_stmt)).scalar() or 0

        return {
            "total": total,
            "active": active,
            "verified": verified,
            "by_role": {k.value: v for k, v in by_role.items()},
            "by_status": {k.value: v for k, v in by_status.items()},
            "new_this_month": recent,
        }

    async def get_by_email_verification_token(self, token: str) -> User | None:
        """Get user by email verification token"""
        stmt = select(UserModel).where(UserModel.email_verification_token == token)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_password_reset_token(self, token: str) -> User | None:
        """Get user by password reset token"""
        stmt = select(UserModel).where(UserModel.password_reset_token == token)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def search(
        self,
        query: str,
        pagination: PaginationParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[User]:
        """Search users by name, email"""
        stmt = select(UserModel)
        count_stmt = select(func.count(UserModel.id))

        # Search in email, display_name, username
        search_conditions = or_(
            func.lower(UserModel.email).contains(query.lower()),
            func.lower(UserModel.display_name).contains(query.lower()),
            func.lower(UserModel.username).contains(query.lower()),
        )
        stmt = stmt.where(search_conditions)
        count_stmt = count_stmt.where(search_conditions)

        # Apply additional filters
        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(UserModel, key):
                    column = getattr(UserModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        # Apply sorting
        stmt = stmt.order_by(desc(UserModel.created_at))

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

    async def get_active_users(
        self,
        pagination: PaginationParams | None = None,
        since: datetime | None = None,
    ) -> PaginatedResult[User]:
        """Get active users"""
        stmt = select(UserModel).where(UserModel.status == UserStatus.ACTIVE)
        count_stmt = select(func.count(UserModel.id)).where(UserModel.status == UserStatus.ACTIVE)

        if since:
            stmt = stmt.where(UserModel.last_login_at >= since)
            count_stmt = count_stmt.where(UserModel.last_login_at >= since)

        stmt = stmt.order_by(desc(UserModel.last_login_at))

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

    async def get_users_with_preferences(
        self,
        interests: builtins.list[str] | None = None,
        budget_level: str | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[User]:
        """Get users matching preferences"""
        stmt = select(UserModel)
        count_stmt = select(func.count(UserModel.id))

        conditions = []

        if interests:
            # PostgreSQL JSONB contains operator
            for interest in interests:
                conditions.append(UserModel.interests.contains([interest]))

        if budget_level:
            conditions.append(UserModel.budget_level == budget_level)

        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(UserModel.created_at))

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
