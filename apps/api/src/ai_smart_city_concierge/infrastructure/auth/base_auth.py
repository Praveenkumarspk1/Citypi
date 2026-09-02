"""
Base Authentication Interface
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any


class AuthProvider(StrEnum):
    """Authentication provider types"""
    FIREBASE = "firebase"
    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"


@dataclass
class AuthConfig:
    """Authentication configuration"""
    provider: AuthProvider = AuthProvider.JWT
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    issuer: str = "ai-smart-city-concierge"
    audience: str = "ai-smart-city-concierge-api"

    # Firebase specific
    firebase_project_id: str | None = None
    firebase_credentials_path: str | None = None

    # API Key specific
    api_key_header: str = "X-API-Key"
    api_key_prefix: str = "sk_"

    # OAuth2 specific
    oauth2_client_id: str | None = None
    oauth2_client_secret: str | None = None
    oauth2_authorize_url: str | None = None
    oauth2_token_url: str | None = None
    oauth2_scopes: list[str] = field(default_factory=list)


@dataclass
class UserClaims:
    """User claims from authentication"""
    user_id: str
    email: str | None = None
    name: str | None = None
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    provider: AuthProvider = AuthProvider.JWT
    provider_user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    issued_at: datetime | None = None
    expires_at: datetime | None = None

    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions

    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles"""
        return any(role in self.roles for role in roles)

    def has_all_roles(self, roles: list[str]) -> bool:
        """Check if user has all specified roles"""
        return all(role in self.roles for role in roles)


@dataclass
class TokenPair:
    """Access and refresh token pair"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 1800  # seconds


class BaseAuth(ABC):
    """Abstract base class for authentication providers"""

    def __init__(self, config: AuthConfig):
        self.config = config

    @abstractmethod
    async def verify_token(self, token: str) -> UserClaims | None:
        """Verify and decode token, return user claims"""
        pass

    @abstractmethod
    async def create_token(self, claims: UserClaims) -> TokenPair:
        """Create access and refresh tokens for user claims"""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> TokenPair | None:
        """Refresh access token using refresh token"""
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke a token (add to blacklist)"""
        pass

    @abstractmethod
    async def verify_api_key(self, api_key: str) -> UserClaims | None:
        """Verify API key and return user claims"""
        pass

    @abstractmethod
    async def create_api_key(self, user_id: str, name: str,
                            permissions: list[str] = None,
                            expires_at: datetime | None = None) -> str:
        """Create new API key for user"""
        pass

    @abstractmethod
    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        pass

    @abstractmethod
    async def list_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """List API keys for user"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Health check for auth provider"""
        pass

    def _create_claims(self, user_id: str, email: str | None = None,
                       name: str | None = None, roles: list[str] = None,
                       permissions: list[str] = None,
                       provider: AuthProvider = AuthProvider.JWT,
                       provider_user_id: str | None = None,
                       metadata: dict[str, Any] = None) -> UserClaims:
        """Helper to create user claims"""
        now = datetime.utcnow()
        return UserClaims(
            user_id=user_id,
            email=email,
            name=name,
            roles=roles or [],
            permissions=permissions or [],
            provider=provider,
            provider_user_id=provider_user_id,
            metadata=metadata or {},
            issued_at=now,
            expires_at=now + timedelta(minutes=self.config.access_token_expire_minutes),
        )
