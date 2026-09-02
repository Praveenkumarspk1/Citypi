"""
Auth Routes - Authentication endpoints
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ai_smart_city_concierge.application.commands.user_commands import (
    CreateUserCommand,
    ForgotPasswordCommand,
    RecordUserLoginCommand,
    ResetPasswordCommand,
    ResendVerificationEmailCommand,
    UserCommandHandler,
    UserLoginCommand,
    VerifyUserEmailCommand,
)
from ai_smart_city_concierge.application.dto.request import (
    CreateUserRequest,
    RefreshTokenRequest,
    UserLoginRequest,
)
from ai_smart_city_concierge.application.dto.response import (
    LoginResponse,
    TokenResponse,
    UserResponse,
)
from ai_smart_city_concierge.application.queries.user_queries import (
    GetUserByEmailQuery,
    GetUserByEmailVerificationTokenQuery,
    UserQueryHandler,
)
from ai_smart_city_concierge.infrastructure.auth import get_current_user
from ai_smart_city_concierge.infrastructure.auth.jwt_auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# Dependency injection for handlers
def get_user_command_handler() -> UserCommandHandler:
    from ai_smart_city_concierge.infrastructure.di.container import get_container
    return get_container().get(UserCommandHandler)


def get_user_query_handler() -> UserQueryHandler:
    from ai_smart_city_concierge.infrastructure.di.container import get_container
    return get_container().get(UserQueryHandler)


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: CreateUserRequest,
    handler: UserCommandHandler = Depends(get_user_command_handler),
) -> LoginResponse:
    """Register a new user"""
    command = CreateUserCommand(
        email=request.email,
        display_name=request.display_name,
        firebase_uid=request.firebase_uid,
        google_id=request.google_id,
        password=request.password,
        locale=request.locale,
        timezone=request.timezone,
        interests=request.interests,
        budget_level=request.budget_level,
        accessibility_needs=request.accessibility_needs,
        dietary_restrictions=request.dietary_restrictions,
        preferred_transport_modes=request.preferred_transport_modes,
    )
    user = await handler.handle_create_user(command)
    
    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return LoginResponse(
        user=UserResponse.from_entity(user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        ),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: UserLoginRequest,
    handler: UserCommandHandler = Depends(get_user_command_handler),
) -> LoginResponse:
    """User login with email and password"""
    command = UserLoginCommand(
        email=request.email,
        password=request.password,
    )
    user = await handler.handle_login(command)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return LoginResponse(
        user=UserResponse.from_entity(user),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        ),
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


@router.post("/logout", response_model=dict)
async def logout(
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    """Logout current user (token blacklisting would be implemented here)"""
    # In a full implementation, we would blacklist the refresh token
    return {"message": "Successfully logged out"}


@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    email: str,
    handler: UserCommandHandler = Depends(get_user_command_handler),
) -> dict:
    """Initiate password reset"""
    command = ForgotPasswordCommand(email=email)
    await handler.handle_forgot_password(command)

    # Don't reveal if user exists for security
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password", response_model=UserResponse)
async def reset_password(
    token: str,
    new_password: str,
    handler: UserCommandHandler = Depends(get_user_command_handler),
) -> UserResponse:
    """Reset user password with token"""
    command = ResetPasswordCommand(token=token, new_password=new_password)
    user = await handler.handle_reset_password(command)
    return UserResponse.from_entity(user)


@router.post("/verify-email", response_model=UserResponse)
async def verify_email(
    token: str,
    handler: UserCommandHandler = Depends(get_user_command_handler),
    query_handler: UserQueryHandler = Depends(get_user_query_handler),
) -> UserResponse:
    """Verify user email with token"""
    # Use query handler to get user by verification token
    query = GetUserByEmailVerificationTokenQuery(token=token)
    user_response = await query_handler.handle_get_user_by_email_verification_token(query)

    if not user_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    command = VerifyUserEmailCommand(user_id=user_response.id)
    updated_user = await handler.handle_verify_email(command)
    return UserResponse.from_entity(updated_user)


@router.post("/resend-verification", response_model=dict)
async def resend_verification_email(
    email: str,
    handler: UserCommandHandler = Depends(get_user_command_handler),
) -> dict:
    """Resend email verification link"""
    command = ResendVerificationEmailCommand(email=email)
    await handler.handle_resend_verification_email(command)

    # Don't reveal if user exists for security
    return {"message": "If the email exists and is not verified, a verification link has been sent"}
