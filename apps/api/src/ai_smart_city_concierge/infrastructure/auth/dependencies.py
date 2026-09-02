"""
Authentication Dependencies
FastAPI dependencies for extracting and validating user authentication
"""
from functools import lru_cache
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config.settings import get_settings
from .base_auth import AuthConfig, AuthProvider
from .jwt_auth import JWTAuth

# Security scheme
security = HTTPBearer(auto_error=False)


def get_auth_config() -> AuthConfig:
    """Get authentication configuration from settings"""
    settings = get_settings()
    return AuthConfig(
        provider=AuthProvider.JWT,
        secret_key=settings.auth.secret_key,
        algorithm=settings.auth.algorithm,
        access_token_expire_minutes=settings.auth.access_token_expire_minutes,
        refresh_token_expire_days=settings.auth.refresh_token_expire_days,
        issuer=settings.auth.issuer,
        audience=settings.auth.audience,
        firebase_project_id=settings.auth.firebase_project_id,
        firebase_credentials_path=settings.auth.firebase_credentials_path,
        api_key_header=settings.auth.api_key_header,
        api_key_prefix=settings.auth.api_key_prefix,
    )


@lru_cache
def get_jwt_auth() -> JWTAuth:
    """Get JWT authentication handler (cached singleton)"""
    config = get_auth_config()
    return JWTAuth(config)


async def get_current_user_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    auth: JWTAuth = Depends(get_jwt_auth),
) -> dict[str, Any] | None:
    """Extract and verify user claims from JWT token"""
    if not credentials:
        return None

    token = credentials.credentials
    claims = await auth.verify_token(token)

    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": claims.user_id,
        "email": claims.email,
        "name": claims.name,
        "roles": claims.roles,
        "permissions": claims.permissions,
        "provider": claims.provider.value,
        "provider_user_id": claims.provider_user_id,
        "metadata": claims.metadata,
    }


async def get_current_user(
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> dict[str, Any]:
    """Get current authenticated user (requires authentication)"""
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return claims


async def get_current_admin_user(
    claims: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Get current user and verify admin role"""
    if "admin" not in claims.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return claims


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    auth: JWTAuth = Depends(get_jwt_auth),
) -> dict[str, Any] | None:
    """Get current user if authenticated, otherwise None (optional authentication)"""
    if not credentials:
        return None

    token = credentials.credentials
    claims = await auth.verify_token(token)

    if not claims:
        return None

    return {
        "id": claims.user_id,
        "email": claims.email,
        "name": claims.name,
        "roles": claims.roles,
        "permissions": claims.permissions,
        "provider": claims.provider.value,
        "provider_user_id": claims.provider_user_id,
        "metadata": claims.metadata,
    }


async def get_api_key_user(
    request: Request,
    auth: JWTAuth = Depends(get_jwt_auth),
) -> dict[str, Any] | None:
    """Get user from API key (X-API-Key header)"""
    settings = get_settings()
    api_key = request.headers.get(settings.auth.api_key_header)

    if not api_key:
        return None

    claims = await auth.verify_api_key(api_key)

    if not claims:
        return None

    return {
        "id": claims.user_id,
        "email": claims.email,
        "name": claims.name,
        "roles": claims.roles,
        "permissions": claims.permissions,
        "provider": claims.provider.value,
        "provider_user_id": claims.provider_user_id,
        "metadata": claims.metadata,
    }


async def get_current_user_or_api_key(
    jwt_user: dict[str, Any] | None = Depends(get_optional_user),
    api_key_user: dict[str, Any] | None = Depends(get_api_key_user),
) -> dict[str, Any]:
    """Get user from either JWT token or API key"""
    user = jwt_user or api_key_user

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required (JWT token or API key)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Role-based access control dependencies
def require_role(role: str):
    """Dependency factory for requiring a specific role"""
    async def role_checker(claims: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if role not in claims.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return claims
    return role_checker


def require_any_role(roles: list):
    """Dependency factory for requiring any of the specified roles"""
    async def role_checker(claims: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_roles = claims.get("roles", [])
        if not any(r in user_roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {roles} required",
            )
        return claims
    return role_checker


def require_permission(permission: str):
    """Dependency factory for requiring a specific permission"""
    async def permission_checker(claims: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if permission not in claims.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return claims
    return permission_checker


# Common role dependencies
require_admin = require_role("admin")
require_moderator = require_any_role(["admin", "moderator"])
require_premium = require_any_role(["admin", "premium", "pro"])


# Import lru_cache
