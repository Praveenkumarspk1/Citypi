"""
User Application Use Cases
"""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ...domain.entities.user import User, UserRole, UserStatus
from ...domain.repositories.base import PaginatedResult, PaginationParams, SortParams
from ...domain.repositories.user_repository import UserRepository
from ...domain.specifications.user_specification import (
    ActiveUserSpec,
    HighEngagementUserSpec,
    InterestUserSpec,
    LocationUserSpec,
    PremiumUserSpec,
    RecentActiveUserSpec,
    RoleUserSpec,
    VerifiedUserSpec,
)
from ...domain.value_objects.coordinates import Coordinates


@dataclass
class CreateUserRequest:
    """Request to create a user"""
    email: str
    username: str
    password_hash: str
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    role: UserRole = UserRole.USER
    preferred_language: str = "en"
    preferred_currency: str = "USD"
    home_location: Coordinates | None = None
    interests: list[str] | None = None
    accessibility_needs: list[str] | None = None
    oauth_provider: str | None = None
    oauth_provider_id: str | None = None


@dataclass
class UpdateUserRequest:
    """Request to update a user"""
    email: str | None = None
    username: str | None = None
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    preferred_language: str | None = None
    preferred_currency: str | None = None
    home_location: Coordinates | None = None
    interests: list[str] | None = None
    accessibility_needs: list[str] | None = None
    notification_preferences: dict[str, bool] | None = None
    privacy_settings: dict[str, Any] | None = None
    is_verified: bool | None = None


@dataclass
class SearchUsersRequest:
    """Request to search users"""
    role: UserRole | None = None
    status: UserStatus | None = None
    is_premium: bool | None = None
    coordinates: Coordinates | None = None
    radius_meters: float | None = None
    interests: list[str] | None = None
    min_engagement_score: float | None = None
    recently_active_days: int | None = None
    verified_only: bool = False
    pagination: PaginationParams | None = None
    sort: SortParams | None = None


class UserUseCases:
    """User Application Use Cases"""

    def __init__(
        self,
        user_repository: UserRepository,
        user_service: UserService,
    ):
        self.user_repository = user_repository

    async def create_user(self, request: CreateUserRequest) -> User:
        """Create a new user"""
        user = User(
            email=request.email,
            username=request.username,
            password_hash=request.password_hash,
            full_name=request.full_name,
            phone=request.phone,
            avatar_url=request.avatar_url,
            role=request.role,
            preferred_language=request.preferred_language,
            preferred_currency=request.preferred_currency,
            home_location=request.home_location,
            interests=request.interests or [],
            accessibility_needs=request.accessibility_needs or [],
            oauth_provider=request.oauth_provider,
            oauth_provider_id=request.oauth_provider_id,
        )

        return await self.user_repository.add(user)

    async def get_user(self, user_id: UUID) -> User | None:
        """Get user by ID"""
        return await self.user_repository.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email"""
        return await self.user_repository.get_by_email(email)

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username"""
        return await self.user_repository.get_by_username(username)

    async def get_user_by_provider(self, provider: str, provider_id: str) -> User | None:
        """Get user by OAuth provider"""
        return await self.user_repository.get_by_provider(provider, provider_id)

    async def update_user(self, user_id: UUID, request: UpdateUserRequest) -> User | None:
        """Update a user"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        # Update fields
        if request.email is not None:
            user.email = request.email
        if request.username is not None:
            user.username = request.username
        if request.full_name is not None:
            user.full_name = request.full_name
        if request.phone is not None:
            user.phone = request.phone
        if request.avatar_url is not None:
            user.avatar_url = request.avatar_url
        if request.role is not None:
            user.role = request.role
        if request.status is not None:
            user.status = request.status
        if request.preferred_language is not None:
            user.preferred_language = request.preferred_language
        if request.preferred_currency is not None:
            user.preferred_currency = request.preferred_currency
        if request.home_location is not None:
            user.home_location = request.home_location
        if request.interests is not None:
            user.interests = request.interests
        if request.accessibility_needs is not None:
            user.accessibility_needs = request.accessibility_needs
        if request.notification_preferences is not None:
            user.notification_preferences = request.notification_preferences
        if request.privacy_settings is not None:
            user.privacy_settings = request.privacy_settings
        if request.is_verified is not None:
            user.is_verified = request.is_verified

        return await self.user_repository.update(user)

    async def delete_user(self, user_id: UUID) -> bool:
        """Delete a user"""
        return await self.user_repository.delete(user_id)

    async def search_users(self, request: SearchUsersRequest) -> PaginatedResult[User]:
        """Search users with various filters"""
        # Build specification
        specs = []

        if request.verified_only:
            specs.append(VerifiedUserSpec())
        else:
            specs.append(ActiveUserSpec())

        if request.role:
            specs.append(RoleUserSpec(request.role))

        if request.is_premium is not None:
            if request.is_premium:
                specs.append(PremiumUserSpec())

        if request.coordinates and request.radius_meters:
            specs.append(LocationUserSpec(request.coordinates, request.radius_meters))

        if request.interests:
            specs.append(InterestUserSpec(request.interests))

        if request.min_engagement_score:
            specs.append(HighEngagementUserSpec(request.min_engagement_score))

        if request.recently_active_days:
            specs.append(RecentActiveUserSpec(request.recently_active_days))

        # Combine specifications
        if specs:
            combined_spec = specs[0]
            for spec in specs[1:]:
                combined_spec = combined_spec & spec
        else:
            combined_spec = ActiveUserSpec()

        # Use service to find matching users
        return await self.user_service.find_matching_users(
            spec=combined_spec,
            pagination=request.pagination,
            sort=request.sort,
        )

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login"""
        await self.user_repository.update_last_login(user_id)

    async def increment_itinerary_count(self, user_id: UUID) -> None:
        """Increment user's itinerary count"""
        await self.user_repository.increment_itinerary_count(user_id)

    async def increment_favorites_count(self, user_id: UUID) -> None:
        """Increment user's favorites count"""
        await self.user_repository.increment_favorites_count(user_id)

    async def increment_reviews_count(self, user_id: UUID) -> None:
        """Increment user's reviews count"""
        await self.user_repository.increment_reviews_count(user_id)

    async def get_user_stats(self) -> dict[str, Any]:
        """Get user statistics"""
        return await self.user_repository.get_stats()

    async def get_user_recommendations(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> list[User]:
        """Get user recommendations (similar users)"""
        return await self.user_service.get_similar_users(user_id, limit)
