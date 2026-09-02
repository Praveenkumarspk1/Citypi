"""
User Routes
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ai_smart_city_concierge.application.commands.user_commands import (
    ActivateUserCommand,
    ChangeUserRoleCommand,
    CreateUserCommand,
    DeactivateUserCommand,
    DeleteUserCommand,
    RecordUserLoginCommand,
    SuspendUserCommand,
    UpdateUserPreferencesCommand,
    UpdateUserProfileCommand,
    UserCommandHandler,
    VerifyUserEmailCommand,
)
from ai_smart_city_concierge.application.dto.request import (
    CreateUserRequest,
    RefreshTokenRequest,
    UpdateUserPreferencesRequest,
    UpdateUserProfileRequest,
    UserLoginRequest,
)
from ai_smart_city_concierge.application.dto.response import (
    PaginatedResponse,
    TokenResponse,
    UserResponse,
)
from ai_smart_city_concierge.application.queries.user_queries import (
    GetActiveUsersQuery,
    GetUserQuery,
    GetUsersWithPreferencesQuery,
    ListUsersQuery,
    SearchUsersQuery,
    UserQueryHandler,
)
from ai_smart_city_concierge.domain.entities.user import UserRole, UserStatus
from ai_smart_city_concierge.infrastructure.auth import get_current_admin_user, get_current_user
from ai_smart_city_concierge.infrastructure.auth.jwt_auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
)

router = APIRouter(prefix="/users", tags=["users"])


# Dependency injection for handlers
def get_user_command_handler() -> UserCommandHandler:
    from ai_smart_city_concierge.infrastructure.di.container import get_container
    return get_container().get(UserCommandHandler)


def get_user_query_handler() -> UserQueryHandler:
    from ai_smart_city_concierge.infrastructure.di.container import get_container
    return get_container().get(UserQueryHandler)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    handler: UserCommandHandler = Depends(get_user_command_handler),
) -> UserResponse:
    """Create a new user"""
    command = CreateUserCommand(
        email=request.email,
        display_name=request.display_name,
        firebase_uid=request.firebase_uid,
        google_id=request.google_id,
        locale=request.locale,
        timezone=request.timezone,
        interests=request.interests,
        budget_level=request.budget_level,
        accessibility_needs=request.accessibility_needs,
        dietary_restrictions=request.dietary_restrictions,
        preferred_transport_modes=request.preferred_transport_modes,
    )
    user = await handler.handle_create_user(command)
    return UserResponse.from_entity(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    handler: UserCommandHandler = Depends(get_user_command_handler),
) -> TokenResponse:
    """User login"""
    from ai_smart_city_concierge.infrastructure.config.database import get_session_factory
    from ai_smart_city_concierge.infrastructure.persistence.sqlalchemy.repositories import (
        SQLAlchemyUserRepository,
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        user = await user_repo.get_by_email(request.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        if not user.verify_password(request.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        if not user.is_active():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )

        # Record login
        await handler.handle_record_login(RecordUserLoginCommand(user_id=user.id))

        # Create tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
) -> TokenResponse:
    """Refresh access token"""
    payload = verify_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = UUID(payload["sub"])
    access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Get current user profile"""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    request: UpdateUserProfileRequest,
    current_user: UserResponse = Depends(get_current_user),
    handler: UserCommandHandler = Depends(get_user_command_handler),
) -> UserResponse:
    """Update current user profile"""
    command = UpdateUserProfileCommand(
        user_id=UUID(current_user.id),
        display_name=request.display_name,
        avatar_url=request.avatar_url,
        locale=request.locale,
        timezone=request.timezone,
    )
    user = await handler.handle_update_profile(command)
    return UserResponse.from_entity(user)


@router.patch("/me/preferences", response_model=UserResponse)
async def update_current_user_preferences(
    request: UpdateUserPreferencesRequest,
    current_user: UserResponse = Depends(get_current_user),
    handler: UserCommandHandler = Depends(get_user_command_handler),
) -> UserResponse:
    """Update current user preferences"""
    command = UpdateUserPreferencesCommand(
        user_id=UUID(current_user.id),
        interests=request.interests,
        budget_level=request.budget_level,
        accessibility_needs=request.accessibility_needs,
        dietary_restrictions=request.dietary_restrictions,
        preferred_transport_modes=request.preferred_transport_modes,
    )
    user = await handler.handle_update_preferences(command)
    return UserResponse.from_entity(user)


@router.post("/me/verify-email", response_model=UserResponse)
async def verify_current_user_email(
    current_user: UserResponse = Depends(get_current_user),
    handler: UserCommandHandler = Depends(get_user_command_handler),
) -> UserResponse:
    """Verify current user's email"""
    command = VerifyUserEmailCommand(user_id=UUID(current_user.id))
    user = await handler.handle_verify_email(command)
    return UserResponse.from_entity(user)


# Admin routes
@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: UserRole | None = None,
    status: UserStatus | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    handler: UserQueryHandler = Depends(get_user_query_handler),
    _: UserResponse = Depends(get_current_admin_user),
) -> PaginatedResponse[UserResponse]:
    """List users (admin only)"""
    query = ListUsersQuery(
        page=page,
        page_size=page_size,
        role=role,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return await handler.handle_list_users(query)


@router.get("/search", response_model=PaginatedResponse[UserResponse])
async def search_users(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: UserRole | None = None,
    status: UserStatus | None = None,
    handler: UserQueryHandler = Depends(get_user_query_handler),
    _: UserResponse = Depends(get_current_admin_user),
) -> PaginatedResponse[UserResponse]:
    """Search users (admin only)"""
    search_query = SearchUsersQuery(
        query=query,
        page=page,
        page_size=page_size,
        role=role,
        status=status,
    )
    return await handler.handle_search_users(search_query)


@router.get("/active", response_model=PaginatedResponse[UserResponse])
async def get_active_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    since: str | None = None,
    handler: UserQueryHandler = Depends(get_user_query_handler),
    _: UserResponse = Depends(get_current_admin_user),
) -> PaginatedResponse[UserResponse]:
    """Get active users (admin only)"""
    from datetime import datetime
    since_dt = datetime.fromisoformat(since) if since else None

    query = GetActiveUsersQuery(
        page=page,
        page_size=page_size,
        since=since_dt,
    )
    return await handler.handle_get_active_users(query)


@router.get("/preferences", response_model=PaginatedResponse[UserResponse])
async def get_users_with_preferences(
    interests: list[str] | None = Query(None),
    budget_level: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    handler: UserQueryHandler = Depends(get_user_query_handler),
    _: UserResponse = Depends(get_current_admin_user),
) -> PaginatedResponse[UserResponse]:
    """Get users matching preferences (admin only)"""
    query = GetUsersWithPreferencesQuery(
        interests=interests,
        budget_level=budget_level,
        page=page,
        page_size=page_size,
    )
    return await handler.handle_get_users_with_preferences(query)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    handler: UserQueryHandler = Depends(get_user_query_handler),
    _: UserResponse = Depends(get_current_admin_user),
) -> UserResponse:
    """Get user by ID (admin only)"""
    query = GetUserQuery(user_id=user_id)
    user = await handler.handle_get_user(query)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    handler: UserCommandHandler = Depends(get_user_command_handler),
    _: UserResponse = Depends(get_current_admin_user),
) -> UserResponse:
    """Deactivate user (admin only)"""
    command = DeactivateUserCommand(user_id=user_id)
    user = await handler.handle_deactivate(command)
    return UserResponse.from_entity(user)


@router.patch("/{user_id}/suspend", response_model=UserResponse)
async def suspend_user(
    user_id: UUID,
    handler: UserCommandHandler = Depends(get_user_command_handler),
    _: UserResponse = Depends(get_current_admin_user),
) -> UserResponse:
    """Suspend user (admin only)"""
    command = SuspendUserCommand(user_id=user_id)
    user = await handler.handle_suspend(command)
    return UserResponse.from_entity(user)


@router.patch("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    handler: UserCommandHandler = Depends(get_user_command_handler),
    _: UserResponse = Depends(get_current_admin_user),
) -> UserResponse:
    """Activate user (admin only)"""
    command = ActivateUserCommand(user_id=user_id)
    user = await handler.handle_activate(command)
    return UserResponse.from_entity(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    handler: UserCommandHandler = Depends(get_user_command_handler),
    _: UserResponse = Depends(get_current_admin_user),
) -> None:
    """Delete user (admin only)"""
    command = DeleteUserCommand(user_id=user_id)
    await handler.handle_delete(command)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: UUID,
    new_role: UserRole,
    handler: UserCommandHandler = Depends(get_user_command_handler),
    _: UserResponse = Depends(get_current_admin_user),
) -> UserResponse:
    """Change user role (admin only)"""
    command = ChangeUserRoleCommand(user_id=user_id, new_role=new_role)
    user = await handler.handle_change_role(command)
    return UserResponse.from_entity(user)
