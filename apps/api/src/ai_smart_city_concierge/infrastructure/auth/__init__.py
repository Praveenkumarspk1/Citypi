"""
Authentication Infrastructure
"""
from .api_key_auth import APIKeyAuth, HMACAuth
from .base_auth import AuthConfig, AuthProvider, BaseAuth, TokenPair, UserClaims
from .dependencies import (
    get_current_admin_user,
    get_current_user,
    get_current_user_or_api_key,
    get_optional_user,
    require_admin,
    require_any_role,
    require_moderator,
    require_permission,
    require_premium,
    require_role,
)
from .firebase_auth import FirebaseAuth
from .jwt_auth import JWTAuth

__all__ = [
    "FirebaseAuth",
    "JWTAuth",
    "APIKeyAuth",
    "HMACAuth",
    "BaseAuth",
    "AuthConfig",
    "UserClaims",
    "TokenPair",
    "AuthProvider",
    "get_current_user",
    "get_current_admin_user",
    "get_optional_user",
    "get_current_user_or_api_key",
    "require_admin",
    "require_moderator",
    "require_premium",
    "require_role",
    "require_any_role",
    "require_permission",
]
