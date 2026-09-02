"""
User Repository Interface
"""
from abc import ABC, abstractmethod
from uuid import UUID

from ..entities.user import User, UserRole, UserStatus
from .base import BaseRepository, FilterParams, PaginatedResult, PaginationParams


class UserRepository(BaseRepository[User, UUID], ABC):
    """User repository interface"""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email"""
        pass

    @abstractmethod
    async def get_by_firebase_uid(self, firebase_uid: str) -> User | None:
        """Get user by Firebase UID"""
        pass

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> User | None:
        """Get user by Google ID"""
        pass

    @abstractmethod
    async def get_by_role(self, role: UserRole, pagination: PaginationParams | None = None) -> PaginatedResult[User]:
        """Get users by role"""
        pass

    @abstractmethod
    async def get_by_status(self, status: UserStatus, pagination: PaginationParams | None = None) -> PaginatedResult[User]:
        """Get users by status"""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        pagination: PaginationParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[User]:
        """Search users by name, email"""
        pass

    @abstractmethod
    async def get_active_users(
        self,
        pagination: PaginationParams | None = None,
        since: datetime | None = None,
    ) -> PaginatedResult[User]:
        """Get active users"""
        pass

    @abstractmethod
    async def get_users_with_preferences(
        self,
        interests: list[str] | None = None,
        budget_level: str | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[User]:
        """Get users matching preferences"""
        pass

    @abstractmethod
    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp"""
        pass

    @abstractmethod
    async def increment_login_count(self, user_id: UUID) -> None:
        """Increment user's login count"""
        pass


