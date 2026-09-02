"""
API Key Authentication Implementation
"""
import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Any

from .base_auth import AuthConfig, AuthProvider, BaseAuth, TokenPair, UserClaims


class APIKeyAuth(BaseAuth):
    """API Key-based authentication"""

    def __init__(self, config: AuthConfig):
        super().__init__(config)
        # In production, use database/Redis
        self._api_keys: dict[str, dict[str, Any]] = {}
        self._key_lookup: dict[str, str] = {}  # prefix -> key_hash

    def _hash_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def _generate_key(self) -> str:
        """Generate a new API key"""
        return f"{self.config.api_key_prefix}{secrets.token_urlsafe(32)}"

    def _generate_key_id(self) -> str:
        """Generate a unique key ID"""
        return secrets.token_urlsafe(16)

    async def verify_token(self, token: str) -> UserClaims | None:
        """Verify JWT token - not supported by API Key auth"""
        return None

    async def create_token(self, claims: UserClaims) -> TokenPair:
        """Create token - not supported by API Key auth"""
        raise NotImplementedError("Token creation not supported by API Key auth")

    async def refresh_token(self, refresh_token: str) -> TokenPair | None:
        """Refresh token - not supported by API Key auth"""
        return None

    async def revoke_token(self, token: str) -> bool:
        """Revoke token - not supported by API Key auth"""
        return False

    async def verify_api_key(self, api_key: str) -> UserClaims | None:
        """Verify API key and return user claims"""
        key_hash = self._hash_key(api_key)

        if key_hash not in self._api_keys:
            return None

        key_data = self._api_keys[key_hash]

        # Check expiration
        if key_data.get("expires_at") and key_data["expires_at"] < datetime.utcnow():
            return None

        # Check if revoked
        if key_data.get("revoked", False):
            return None

        # Update last used timestamp
        key_data["last_used"] = datetime.utcnow()

        return UserClaims(
            user_id=key_data["user_id"],
            email=key_data.get("email"),
            name=key_data.get("name"),
            roles=key_data.get("roles", []),
            permissions=key_data.get("permissions", []),
            provider=AuthProvider.API_KEY,
            provider_user_id=key_data.get("key_id"),
            metadata=key_data.get("metadata", {}),
            issued_at=key_data.get("created_at"),
            expires_at=key_data.get("expires_at"),
        )

    async def create_api_key(self, user_id: str, name: str,
                            permissions: list[str] = None,
                            roles: list[str] = None,
                            expires_at: datetime | None = None,
                            metadata: dict[str, Any] = None) -> str:
        """Create new API key for user"""
        raw_key = self._generate_key()
        key_id = self._generate_key_id()
        key_hash = self._hash_key(raw_key)

        # Store key data
        self._api_keys[key_hash] = {
            "key_id": key_id,
            "user_id": user_id,
            "name": name,
            "permissions": permissions or [],
            "roles": roles or [],
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "revoked": False,
            "metadata": metadata or {},
            "last_used": None,
        }

        # Store prefix for lookup (first 8 chars after prefix)
        prefix = raw_key[len(self.config.api_key_prefix):len(self.config.api_key_prefix)+8]
        self._key_lookup[prefix] = key_hash

        return raw_key

    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        key_hash = self._hash_key(api_key)

        if key_hash in self._api_keys:
            self._api_keys[key_hash]["revoked"] = True
            return True
        return False

    async def revoke_api_key_by_id(self, key_id: str) -> bool:
        """Revoke an API key by key ID"""
        for _key_hash, key_data in self._api_keys.items():
            if key_data["key_id"] == key_id:
                key_data["revoked"] = True
                return True
        return False

    async def list_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """List API keys for user"""
        keys = []
        for _key_hash, key_data in self._api_keys.items():
            if key_data["user_id"] == user_id:
                # Don't return the actual key, only metadata
                keys.append({
                    "key_id": key_data["key_id"],
                    "name": key_data["name"],
                    "permissions": key_data["permissions"],
                    "roles": key_data["roles"],
                    "created_at": key_data["created_at"],
                    "expires_at": key_data.get("expires_at"),
                    "revoked": key_data.get("revoked", False),
                    "last_used": key_data.get("last_used"),
                    "prefix": key_data.get("prefix", ""),
                })
        return keys

    async def get_api_key(self, key_id: str) -> dict[str, Any] | None:
        """Get API key details by key ID"""
        for _key_hash, key_data in self._api_keys.items():
            if key_data["key_id"] == key_id:
                return {
                    "key_id": key_data["key_id"],
                    "user_id": key_data["user_id"],
                    "name": key_data["name"],
                    "permissions": key_data["permissions"],
                    "roles": key_data["roles"],
                    "created_at": key_data["created_at"],
                    "expires_at": key_data.get("expires_at"),
                    "revoked": key_data.get("revoked", False),
                    "last_used": key_data.get("last_used"),
                    "metadata": key_data.get("metadata", {}),
                }
        return None

    async def update_api_key(self, key_id: str,
                            name: str | None = None,
                            permissions: list[str] | None = None,
                            roles: list[str] | None = None,
                            expires_at: datetime | None = None,
                            metadata: dict[str, Any] | None = None) -> bool:
        """Update API key metadata"""
        for _key_hash, key_data in self._api_keys.items():
            if key_data["key_id"] == key_id:
                if name is not None:
                    key_data["name"] = name
                if permissions is not None:
                    key_data["permissions"] = permissions
                if roles is not None:
                    key_data["roles"] = roles
                if expires_at is not None:
                    key_data["expires_at"] = expires_at
                if metadata is not None:
                    key_data["metadata"] = metadata
                return True
        return False

    async def rotate_api_key(self, key_id: str) -> str | None:
        """Rotate (regenerate) an API key"""
        for _key_hash, key_data in self._api_keys.items():
            if key_data["key_id"] == key_id:
                user_id = key_data["user_id"]
                name = key_data["name"]
                permissions = key_data["permissions"]
                roles = key_data["roles"]
                expires_at = key_data.get("expires_at")
                metadata = key_data.get("metadata", {})

                # Revoke old key
                key_data["revoked"] = True

                # Create new key
                return await self.create_api_key(
                    user_id=user_id,
                    name=name,
                    permissions=permissions,
                    roles=roles,
                    expires_at=expires_at,
                    metadata=metadata,
                )
        return None

    async def health_check(self) -> bool:
        """Health check for API Key auth"""
        try:
            # Test key creation and verification
            test_key = await self.create_api_key(
                user_id="health-check",
                name="Health Check Key",
                permissions=["health:check"],
            )
            claims = await self.verify_api_key(test_key)
            return claims is not None and claims.user_id == "health-check"
        except Exception:
            return False

    def get_key_stats(self) -> dict[str, Any]:
        """Get API key statistics"""
        total = len(self._api_keys)
        active = sum(1 for k in self._api_keys.values() if not k.get("revoked", False))
        revoked = total - active
        expired = sum(1 for k in self._api_keys.values()
                     if k.get("expires_at") and k["expires_at"] < datetime.utcnow())

        return {
            "total": total,
            "active": active,
            "revoked": revoked,
            "expired": expired,
        }


class HMACAuth(BaseAuth):
    """HMAC-based authentication for service-to-service communication"""

    def __init__(self, config: AuthConfig):
        super().__init__(config)
        self._secrets: dict[str, str] = {}  # client_id -> secret

    def _generate_secret(self) -> str:
        """Generate HMAC secret"""
        return secrets.token_urlsafe(32)

    def _sign(self, secret: str, message: str) -> str:
        """Generate HMAC signature"""
        return hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

    def _verify_signature(self, secret: str, message: str, signature: str) -> bool:
        """Verify HMAC signature"""
        expected = self._sign(secret, message)
        return hmac.compare_digest(expected, signature)

    async def register_client(self, client_id: str, name: str) -> str:
        """Register a new client and return secret"""
        secret = self._generate_secret()
        self._secrets[client_id] = secret
        return secret

    async def verify_hmac(self, client_id: str, message: str, signature: str,
                         timestamp: int | None = None) -> UserClaims | None:
        """Verify HMAC signature"""
        if client_id not in self._secrets:
            return None

        secret = self._secrets[client_id]

        # Check timestamp if provided (prevent replay attacks)
        if timestamp is not None:
            now = int(datetime.utcnow().timestamp())
            if abs(now - timestamp) > 300:  # 5 minute window
                return None

        if not self._verify_signature(secret, message, signature):
            return None

        return UserClaims(
            user_id=client_id,
            name=client_id,
            roles=["service"],
            permissions=["service:access"],
            provider=AuthProvider.API_KEY,
            provider_user_id=client_id,
            metadata={"type": "hmac"},
        )

    async def revoke_client(self, client_id: str) -> bool:
        """Revoke a client"""
        if client_id in self._secrets:
            del self._secrets[client_id]
            return True
        return False

    async def list_clients(self) -> list[dict[str, Any]]:
        """List registered clients"""
        return [
            {"client_id": client_id, "created_at": "unknown"}
            for client_id in self._secrets.keys()
        ]

    # Not implemented for HMAC
    async def verify_token(self, token: str) -> UserClaims | None:
        return None

    async def create_token(self, claims: UserClaims) -> TokenPair:
        raise NotImplementedError

    async def refresh_token(self, refresh_token: str) -> TokenPair | None:
        return None

    async def revoke_token(self, token: str) -> bool:
        return False

    async def verify_api_key(self, api_key: str) -> UserClaims | None:
        return None

    async def create_api_key(self, user_id: str, name: str,
                            permissions: list[str] = None,
                            expires_at: datetime | None = None) -> str:
        raise NotImplementedError

    async def revoke_api_key(self, api_key: str) -> bool:
        return False

    async def list_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        return []

    async def health_check(self) -> bool:
        return True
