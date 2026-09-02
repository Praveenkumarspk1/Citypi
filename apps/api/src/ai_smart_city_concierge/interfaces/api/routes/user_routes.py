"""
User API Routes
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from ....application.use_cases.user_use_cases import (
    CreateUserRequest,
    SearchUsersRequest,
    UpdateUserRequest,
    UserUseCases,
)
from ....domain.entities.user import User, UserRole, UserStatus
from ....domain.repositories.base import PaginationParams, SortParams
from ....domain.value_objects.coordinates import Coordinates
from ....infrastructure.config.dependencies import get_user_use_cases

router = APIRouter(prefix="/users", tags=["Users"])


# Request/Response Models
class CoordinatesModel(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class CreateUserModel(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password_hash: str
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    role: UserRole = UserRole.USER
    preferred_language: str = "en"
    preferred_currency: str = "USD"
    home_location: CoordinatesModel | None = None
    interests: list[str] | None = None
    accessibility_needs: list[str] | None = None
    oauth_provider: str | None = None
    oauth_provider_id: str | None = None


class UpdateUserModel(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50)
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    preferred_language: str | None = None
    preferred_currency: str | None = None
    home_location: CoordinatesModel | None = None
    interests: list[str] | None = None
    accessibility_needs: list[str] | None = None
    notification_preferences: dict | None = None
    privacy_settings: dict | None = None
    is_verified: bool | None = None


class SearchUsersModel(BaseModel):
    role: UserRole | None = None
    status: UserStatus | None = None
    is_premium: bool | None = None
    coordinates: CoordinatesModel | None = None
    radius_meters: float | None = Field(None, gt=0, le=50000)
    interests: list[str] | None = None
    min_engagement_score: float | None = Field(None, ge=0)
    recently_active_days: int | None = Field(None, ge=1)
    verified_only: bool = False
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_field: str | None = None
    sort_order: str = "desc"


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: str | None
    phone: str | None
    avatar_url: str | None
    role: UserRole
    status: UserStatus
    preferred_language: str
    preferred_currency: str
    home_location: CoordinatesModel | None
    interests: list[str]
    accessibility_needs: list[str]
    notification_preferences: dict
    privacy_settings: dict
    is_verified: bool
    is_premium: bool
    last_login_at: str | None
    itinerary_count: int
    favorites_count: int
    reviews_count: int
    created_at: str
    updated_at: str


class PaginatedUserResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


def user_to_response(user: User) -> UserResponse:
    """Convert User entity to response model"""
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        role=user.role,
        status=user.status,
        preferred_language=user.preferred_language,
        preferred_currency=user.preferred_currency,
        home_location=CoordinatesModel(
            latitude=user.home_location.latitude,
            longitude=user.home_location.longitude,
        ) if user.home_location else None,
        interests=user.interests,
        accessibility_needs=user.accessibility_needs,
        notification_preferences=user.notification_preferences,
        privacy_settings=user.privacy_settings,
        is_verified=user.is_verified,
        is_premium=user.is_premium,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        itinerary_count=user.itinerary_count,
        favorites_count=user.favorites_count,
        reviews_count=user.reviews_count,
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserModel,
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Create a new user"""
    user_request = CreateUserRequest(
        email=request.email,
        username=request.username,
        password_hash=request.password_hash,
        full_name=request.full_name,
        phone=request.phone,
        avatar_url=request.avatar_url,
        role=request.role,
        preferred_language=request.preferred_language,
        preferred_currency=request.preferred_currency,
        home_location=Coordinates(
            latitude=request.home_location.latitude,
            longitude=request.home_location.longitude,
        ) if request.home_location else None,
        interests=request.interests,
        accessibility_needs=request.accessibility_needs,
        oauth_provider=request.oauth_provider,
        oauth_provider_id=request.oauth_provider_id,
    )

    user = await use_cases.create_user(user_request)
    return user_to_response(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Get user by ID"""
    user = await use_cases.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_response(user)


@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Get user by email"""
    user = await use_cases.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_response(user)


@router.get("/username/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Get user by username"""
    user = await use_cases.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    request: UpdateUserModel,
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Update a user"""
    update_request = UpdateUserRequest(
        email=request.email,
        username=request.username,
        full_name=request.full_name,
        phone=request.phone,
        avatar_url=request.avatar_url,
        role=request.role,
        status=request.status,
        preferred_language=request.preferred_language,
        preferred_currency=request.preferred_currency,
        home_location=Coordinates(
            latitude=request.home_location.latitude,
            longitude=request.home_location.longitude,
        ) if request.home_location else None,
        interests=request.interests,
        accessibility_needs=request.accessibility_needs,
        notification_preferences=request.notification_preferences,
        privacy_settings=request.privacy_settings,
        is_verified=request.is_verified,
    )

    user = await use_cases.update_user(user_id, update_request)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_response(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Delete a user"""
    success = await use_cases.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")


@router.post("/search", response_model=PaginatedUserResponse)
async def search_users(
    request: SearchUsersModel,
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Search users with filters"""
    search_request = SearchUsersRequest(
        role=request.role,
        status=request.status,
        is_premium=request.is_premium,
        coordinates=Coordinates(
            latitude=request.coordinates.latitude,
            longitude=request.coordinates.longitude,
        ) if request.coordinates else None,
        radius_meters=request.radius_meters,
        interests=request.interests,
        min_engagement_score=request.min_engagement_score,
        recently_active_days=request.recently_active_days,
        verified_only=request.verified_only,
        pagination=PaginationParams(page=request.page, page_size=request.page_size),
        sort=SortParams(field=request.sort_field, order=request.sort_order) if request.sort_field else None,
    )

    result = await use_cases.search_users(search_request)

    return PaginatedUserResponse(
        items=[user_to_response(user) for user in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.post("/{user_id}/login", status_code=status.HTTP_204_NO_CONTENT)
async def update_last_login(
    user_id: UUID,
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Update user's last login"""
    await use_cases.update_last_login(user_id)


@router.post("/{user_id}/itinerary-count", status_code=status.HTTP_204_NO_CONTENT)
async def increment_itinerary_count(
    user_id: UUID,
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Increment user's itinerary count"""
    await use_cases.increment_itinerary_count(user_id)


@router.post("/{user_id}/favorites-count", status_code=status.HTTP_204_NO_CONTENT)
async def increment_favorites_count(
    user_id: UUID,
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Increment user's favorites count"""
    await use_cases.increment_favorites_count(user_id)


@router.post("/{user_id}/reviews-count", status_code=status.HTTP_204_NO_CONTENT)
async def increment_reviews_count(
    user_id: UUID,
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Increment user's reviews count"""
    await use_cases.increment_reviews_count(user_id)


@router.get("/stats", response_model=dict)
async def get_user_stats(
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Get user statistics"""
    return await use_cases.get_user_stats()


@router.get("/recommendations/{user_id}", response_model=list[UserResponse])
async def get_user_recommendations(
    user_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    """Get user recommendations (similar users)"""
    users = await use_cases.get_user_recommendations(user_id, limit)
    return [user_to_response(user) for user in users]
