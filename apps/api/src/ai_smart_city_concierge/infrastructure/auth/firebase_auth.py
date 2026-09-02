"""
Firebase Authentication Implementation
"""
import os
from datetime import datetime
from typing import Any

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from firebase_admin.auth import (
    ExpiredIdTokenError,
    InvalidIdTokenError,
    RevokedIdTokenError,
    UserRecord,
)

from .base_auth import AuthConfig, AuthProvider, BaseAuth, TokenPair, UserClaims


class FirebaseAuth(BaseAuth):
    """Firebase Authentication adapter"""

    def __init__(self, config: AuthConfig):
        super().__init__(config)
        self._app: firebase_admin.App | None = None
        self._initialized = False

    def _initialize(self) -> None:
        """Initialize Firebase Admin SDK"""
        if self._initialized:
            return

        if self.config.firebase_credentials_path and os.path.exists(self.config.firebase_credentials_path):
            cred = credentials.Certificate(self.config.firebase_credentials_path)
        else:
            # Use default credentials (ADC)
            cred = credentials.ApplicationDefault()

        self._app = firebase_admin.initialize_app(cred, {
            'projectId': self.config.firebase_project_id,
        })
        self._initialized = True

    async def verify_token(self, token: str) -> UserClaims | None:
        """Verify Firebase ID token"""
        self._initialize()

        try:
            decoded_token = firebase_auth.verify_id_token(
                token,
                app=self._app,
                check_revoked=True,
            )

            # Get user record for additional info
            user_record = firebase_auth.get_user(decoded_token['uid'], app=self._app)

            return UserClaims(
                user_id=decoded_token['uid'],
                email=decoded_token.get('email') or user_record.email,
                name=decoded_token.get('name') or user_record.display_name,
                roles=decoded_token.get('roles', []),
                permissions=decoded_token.get('permissions', []),
                provider=AuthProvider.FIREBASE,
                provider_user_id=decoded_token['uid'],
                metadata={
                    'email_verified': decoded_token.get('email_verified', False),
                    'firebase': {
                        'sign_in_provider': decoded_token.get('firebase', {}).get('sign_in_provider'),
                        'identities': decoded_token.get('firebase', {}).get('identities', {}),
                    }
                },
                issued_at=datetime.utcfromtimestamp(decoded_token.get('iat', 0)) if decoded_token.get('iat') else None,
                expires_at=datetime.utcfromtimestamp(decoded_token.get('exp', 0)) if decoded_token.get('exp') else None,
            )
        except (ExpiredIdTokenError, RevokedIdTokenError, InvalidIdTokenError, ValueError):
            return None
        except Exception:
            return None

    async def create_token(self, claims: UserClaims) -> TokenPair:
        """Create custom Firebase token (for server-side token generation)"""
        self._initialize()

        # Create custom token
        custom_token = firebase_auth.create_custom_token(
            claims.user_id,
            developer_claims={
                'roles': claims.roles,
                'permissions': claims.permissions,
                'metadata': claims.metadata,
            },
            app=self._app,
        )

        # Firebase custom tokens are exchanged for ID tokens client-side
        # We return the custom token as access_token
        # Refresh token handling is done by Firebase client SDK
        return TokenPair(
            access_token=custom_token.decode() if isinstance(custom_token, bytes) else custom_token,
            refresh_token="",  # Handled by Firebase client
            token_type="Bearer",
            expires_in=3600,  # Custom tokens expire in 1 hour
        )

    async def refresh_token(self, refresh_token: str) -> TokenPair | None:
        """Refresh token - handled by Firebase client SDK"""
        # Firebase handles token refresh client-side
        # This is a placeholder for server-side refresh if needed
        return None

    async def revoke_token(self, token: str) -> bool:
        """Revoke user's tokens (revoke refresh tokens)"""
        self._initialize()

        try:
            # Decode token to get user ID
            decoded = firebase_auth.verify_id_token(token, app=self._app, check_revoked=False)
            user_id = decoded['uid']

            # Revoke all refresh tokens for user
            firebase_auth.revoke_refresh_tokens(user_id, app=self._app)
            return True
        except Exception:
            return False

    async def verify_api_key(self, api_key: str) -> UserClaims | None:
        """Verify API key - not directly supported by Firebase"""
        # Firebase doesn't have native API key support
        # This would need a custom implementation
        return None

    async def create_api_key(self, user_id: str, name: str,
                            permissions: list[str] = None,
                            expires_at: datetime | None = None) -> str:
        """Create API key - not directly supported by Firebase"""
        # Would need custom implementation
        raise NotImplementedError("API keys not supported by Firebase Auth")

    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoke API key - not directly supported by Firebase"""
        return False

    async def list_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """List API keys - not directly supported by Firebase"""
        return []

    async def health_check(self) -> bool:
        """Health check for Firebase auth"""
        try:
            self._initialize()
            # Try to list users (limited)
            firebase_auth.list_users(max_results=1, app=self._app)
            return True
        except Exception:
            return False

    # Additional Firebase-specific methods

    async def get_user(self, user_id: str) -> UserRecord | None:
        """Get Firebase user by ID"""
        self._initialize()
        try:
            return firebase_auth.get_user(user_id, app=self._app)
        except Exception:
            return None

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        """Get Firebase user by email"""
        self._initialize()
        try:
            return firebase_auth.get_user_by_email(email, app=self._app)
        except Exception:
            return None

    async def create_user(self, email: str, password: str,
                         display_name: str | None = None,
                         email_verified: bool = False) -> UserRecord:
        """Create new Firebase user"""
        self._initialize()
        return firebase_auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=email_verified,
            app=self._app,
        )

    async def update_user(self, user_id: str, **kwargs) -> UserRecord:
        """Update Firebase user"""
        self._initialize()
        return firebase_auth.update_user(user_id, app=self._app, **kwargs)

    async def delete_user(self, user_id: str) -> bool:
        """Delete Firebase user"""
        self._initialize()
        try:
            firebase_auth.delete_user(user_id, app=self._app)
            return True
        except Exception:
            return False

    async def set_custom_claims(self, user_id: str, claims: dict[str, Any]) -> bool:
        """Set custom claims on user"""
        self._initialize()
        try:
            firebase_auth.set_custom_user_claims(user_id, claims, app=self._app)
            return True
        except Exception:
            return False

    async def send_password_reset_email(self, email: str) -> bool:
        """Send password reset email"""
        self._initialize()
        try:
            firebase_auth.generate_password_reset_link(email, app=self._app)
            return True
        except Exception:
            return False

    async def send_email_verification(self, email: str) -> bool:
        """Send email verification"""
        self._initialize()
        try:
            firebase_auth.generate_email_verification_link(email, app=self._app)
            return True
        except Exception:
            return False

    async def list_users(self, max_results: int = 1000) -> list[UserRecord]:
        """List Firebase users"""
        self._initialize()
        users = []
        page = firebase_auth.list_users(max_results=max_results, app=self._app)
        for user in page.iterate_all():
            users.append(user)
        return users
