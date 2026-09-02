"""
JWT Authentication Implementation
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from jwt import PyJWTError

from .base_auth import AuthConfig, AuthProvider, BaseAuth, TokenPair, UserClaims


class JWTAuth(BaseAuth):
    """JWT-based authentication"""

    def __init__(self, config: AuthConfig):
        super().__init__(config)
        self._token_blacklist: set = set()  # In production, use Redis
        self._api_keys: dict[str, dict[str, Any]] = {}  # In production, use database
        self._refresh_tokens: dict[str, dict[str, Any]] = {}  # In production, use database

    async def verify_token(self, token: str) -> UserClaims | None:
        """Verify and decode JWT token"""
        if token in self._token_blacklist:
            return None

        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
                audience=self.config.audience,
            )

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                return None

            return UserClaims(
                user_id=payload.get("sub", ""),
                email=payload.get("email"),
                name=payload.get("name"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                provider=AuthProvider.JWT,
                provider_user_id=payload.get("provider_user_id"),
                metadata=payload.get("metadata", {}),
                issued_at=datetime.utcfromtimestamp(payload.get("iat", 0)) if payload.get("iat") else None,
                expires_at=datetime.utcfromtimestamp(exp) if exp else None,
            )
        except PyJWTError:
            return None

    async def create_token(self, claims: UserClaims) -> TokenPair:
        """Create JWT access and refresh tokens"""
        now = datetime.utcnow()

        # Access token payload
        access_payload = {
            "sub": claims.user_id,
            "email": claims.email,
            "name": claims.name,
            "roles": claims.roles,
            "permissions": claims.permissions,
            "provider": claims.provider.value,
            "provider_user_id": claims.provider_user_id,
            "metadata": claims.metadata,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self.config.access_token_expire_minutes)).timestamp()),
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "type": "access",
        }

        # Refresh token payload
        refresh_payload = {
            "sub": claims.user_id,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=self.config.refresh_token_expire_days)).timestamp()),
            "iss": self.config.issuer,
            "aud": self.config.audience,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32),  # Unique token ID
        }

        access_token = jwt.encode(
            access_payload,
            self.config.secret_key,
            algorithm=self.config.algorithm,
        )

        refresh_token = jwt.encode(
            refresh_payload,
            self.config.secret_key,
            algorithm=self.config.algorithm,
        )

        # Store refresh token for validation
        self._refresh_tokens[refresh_payload["jti"]] = {
            "user_id": claims.user_id,
            "created_at": now,
            "revoked": False,
        }

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.config.access_token_expire_minutes * 60,
        )

    async def refresh_token(self, refresh_token: str) -> TokenPair | None:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(
                refresh_token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
                audience=self.config.audience,
            )

            # Verify it's a refresh token
            if payload.get("type") != "refresh":
                return None

            jti = payload.get("jti")
            if not jti or jti not in self._refresh_tokens:
                return None

            token_data = self._refresh_tokens[jti]
            if token_data["revoked"]:
                return None

            # Create new claims
            claims = UserClaims(
                user_id=payload["sub"],
                provider=AuthProvider.JWT,
            )

            # Revoke old refresh token
            token_data["revoked"] = True

            # Create new token pair
            return await self.create_token(claims)

        except PyJWTError:
            return None

    async def revoke_token(self, token: str) -> bool:
        """Revoke a token (add to blacklist)"""
        try:
            # Decode without verification to get JTI
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
            )

            jti = payload.get("jti")
            if jti and jti in self._refresh_tokens:
                self._refresh_tokens[jti]["revoked"] = True

            # Add to blacklist
            self._token_blacklist.add(token)
            return True
        except PyJWTError:
            return False

    async def verify_api_key(self, api_key: str) -> UserClaims | None:
        """Verify API key and return user claims"""
        # Hash the API key for lookup
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        if key_hash not in self._api_keys:
            return None

        key_data = self._api_keys[key_hash]

        # Check expiration
        if key_data.get("expires_at") and key_data["expires_at"] < datetime.utcnow():
            return None

        # Check if revoked
        if key_data.get("revoked", False):
            return None

        return UserClaims(
            user_id=key_data["user_id"],
            email=key_data.get("email"),
            name=key_data.get("name"),
            roles=key_data.get("roles", []),
            permissions=key_data.get("permissions", []),
            provider=AuthProvider.API_KEY,
            provider_user_id=key_data.get("key_id"),
            metadata=key_data.get("metadata", {}),
        )

    async def create_api_key(self, user_id: str, name: str,
                            permissions: list[str] = None,
                            expires_at: datetime | None = None) -> str:
        """Create new API key for user"""
        # Generate API key
        key_id = secrets.token_urlsafe(16)
        raw_key = f"{self.config.api_key_prefix}{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Store key data
        self._api_keys[key_hash] = {
            "key_id": key_id,
            "user_id": user_id,
            "name": name,
            "permissions": permissions or [],
            "roles": [],  # API keys don't have roles by default
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "revoked": False,
            "metadata": {},
        }

        return raw_key

    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        if key_hash in self._api_keys:
            self._api_keys[key_hash]["revoked"] = True
            return True
        return False

    async def list_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """List API keys for user"""
        keys = []
        for _key_hash, key_data in self._api_keys.items():
            if key_data["user_id"] == user_id:
                keys.append({
                    "key_id": key_data["key_id"],
                    "name": key_data["name"],
                    "permissions": key_data["permissions"],
                    "created_at": key_data["created_at"],
                    "expires_at": key_data.get("expires_at"),
                    "revoked": key_data.get("revoked", False),
                    "last_used": key_data.get("last_used"),
                })
        return keys

    async def health_check(self) -> bool:
        """Health check for JWT auth"""
        try:
            # Test token creation and verification
            claims = UserClaims(user_id="health-check", provider=AuthProvider.JWT)
            token_pair = await self.create_token(claims)
            verified = await self.verify_token(token_pair.access_token)
            return verified is not None and verified.user_id == "health-check"
        except Exception:
            return False

    def _hash_token(self, token: str) -> str:
        """Hash token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()


# Standalone functions for backward compatibility
async def create_access_token(user_id: UUID | str) -> str:
    """Create access token for user"""
    config = AuthConfig()
    auth = JWTAuth(config)
    claims = UserClaims(user_id=str(user_id), provider=AuthProvider.JWT)
    token_pair = await auth.create_token(claims)
    return token_pair.access_token


async def create_refresh_token(user_id: UUID | str) -> str:
    """Create refresh token for user"""
    config = AuthConfig()
    auth = JWTAuth(config)
    claims = UserClaims(user_id=str(user_id), provider=AuthProvider.JWT)
    token_pair = await auth.create_token(claims)
    return token_pair.refresh_token


async def verify_token(token: str) -> dict | None:
    """Verify token and return payload"""
    config = AuthConfig()
    auth = JWTAuth(config)
    claims = await auth.verify_token(token)
    if not claims:
        return None
    return {
        "sub": claims.user_id,
        "email": claims.email,
        "name": claims.name,
        "roles": claims.roles,
        "permissions": claims.permissions,
        "provider": claims.provider.value,
        "provider_user_id": claims.provider_user_id,
        "metadata": claims.metadata,
        "type": "access",
    }
