"""
User Queries (CQRS Read Side)
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ...domain.entities.user import UserRole, UserStatus
from ..dto.response import PaginatedResponse, UserResponse
from ..ports.repositories import UserRepositoryPort


@dataclass
class GetUserQuery:
    """Query to get user by ID"""
    user_id: UUID


@dataclass
class GetUserByEmailQuery:
    """Query to get user by email"""
    email: str


@dataclass
class GetUserByFirebaseUIDQuery:
    """Query to get user by Firebase UID"""
    firebase_uid: str


@dataclass
class GetUserByGoogleIDQuery:
    """Query to get user by Google ID"""
    google_id: str


@dataclass
class ListUsersQuery:
    """Query to list users with pagination and filters"""
    page: int = 1
    page_size: int = 20
    role: UserRole | None = None
    status: UserStatus | None = None
    search: str | None = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


@dataclass
class SearchUsersQuery:
    """Query to search users"""
    query: str
    page: int = 1
    page_size: int = 20
    role: UserRole | None = None
    status: UserStatus | None = None


@dataclass
class GetActiveUsersQuery:
    """Query to get active users"""
    page: int = 1
    page_size: int = 20
    since: datetime | None = None


@dataclass
class GetUsersWithPreferencesQuery:
    """Query to get users matching preferences"""
    interests: list[str] | None = None
    budget_level: str | None = None
    page: int = 1
    page_size: int = 20


@dataclass
class GetUserByEmailVerificationTokenQuery:
    """Query to get user by email verification token"""
    token: str


@dataclass
class GetUserByPasswordResetTokenQuery:
    """Query to get user by password reset token"""
    token: str


class UserQueryHandler:
    """Handler for user queries"""

    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository

    async def handle_get_user(self, query: GetUserQuery) -> UserResponse | None:
        """Handle get user query"""
        user = await self.user_repository.get_by_id(query.user_id)
        if not user:
            return None
        return UserResponse.from_entity(user)

    async def handle_get_user_by_email(self, query: GetUserByEmailQuery) -> UserResponse | None:
        """Handle get user by email query"""
        user = await self.user_repository.get_by_email(query.email)
        if not user:
            return None
        return UserResponse.from_entity(user)

    async def handle_get_user_by_firebase_uid(self, query: GetUserByFirebaseUIDQuery) -> UserResponse | None:
        """Handle get user by Firebase UID query"""
        user = await self.user_repository.get_by_firebase_uid(query.firebase_uid)
        if not user:
            return None
        return UserResponse.from_entity(user)

    async def handle_get_user_by_google_id(self, query: GetUserByGoogleIDQuery) -> UserResponse | None:
        """Handle get user by Google ID query"""
        user = await self.user_repository.get_by_google_id(query.google_id)
        if not user:
            return None
        return UserResponse.from_entity(user)

    async def handle_list_users(self, query: ListUsersQuery) -> PaginatedResponse[UserResponse]:
        """Handle list users query"""
        from ..ports.repositories import FilterParams, PaginationParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)
        sort = SortParams(field=query.sort_by, order=query.sort_order)

        filters = {}
        if query.role:
            filters["role"] = query.role.value
        if query.status:
            filters["status"] = query.status.value
        if query.search:
            filters["search"] = query.search

        filter_params = FilterParams(filters=filters) if filters else None

        result = await self.user_repository.list(pagination, sort, filter_params)

        return PaginatedResponse(
            items=[UserResponse.from_entity(user) for user in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_search_users(self, query: SearchUsersQuery) -> PaginatedResponse[UserResponse]:
        """Handle search users query"""
        result = await self.user_repository.search(
            query=query.query,
            pagination=PaginationParams(page=query.page, page_size=query.page_size),
            filters=FilterParams(filters={
                "role": query.role.value if query.role else None,
                "status": query.status.value if query.status else None,
            }) if query.role or query.status else None,
        )

        return PaginatedResponse(
            items=[UserResponse.from_entity(user) for user in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_active_users(self, query: GetActiveUsersQuery) -> PaginatedResponse[UserResponse]:
        """Handle get active users query"""
        result = await self.user_repository.get_active_users(
            pagination=PaginationParams(page=query.page, page_size=query.page_size),
            since=query.since,
        )

        return PaginatedResponse(
            items=[UserResponse.from_entity(user) for user in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_users_with_preferences(self, query: GetUsersWithPreferencesQuery) -> PaginatedResponse[UserResponse]:
        """Handle get users with preferences query"""
        result = await self.user_repository.get_users_with_preferences(
            interests=query.interests,
            budget_level=query.budget_level,
            pagination=PaginationParams(page=query.page, page_size=query.page_size),
        )

        return PaginatedResponse(
            items=[UserResponse.from_entity(user) for user in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_user_by_email_verification_token(self, query: GetUserByEmailVerificationTokenQuery) -> UserResponse | None:
        """Handle get user by email verification token query"""
        user = await self.user_repository.get_by_email_verification_token(query.token)
        if not user:
            return None
        return UserResponse.from_entity(user)

    async def handle_get_user_by_password_reset_token(self, query: GetUserByPasswordResetTokenQuery) -> UserResponse | None:
        """Handle get user by password reset token query"""
        user = await self.user_repository.get_by_password_reset_token(query.token)
        if not user:
            return None
        return UserResponse.from_entity(user)


from ..ports.repositories import FilterParams, PaginationParams
