"""
Authentication Client

Handles authentication flows and token management.
"""
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from threading import Lock

from .base import BaseClient
from .exceptions import AuthenticationError


@dataclass
class TokenPair:
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    scope: str = ""
    created_at: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """Check if access token is expired."""
        return time.time() >= self.created_at + self.expires_in - 60  # 60s buffer

    @property
    def expires_at(self) -> float:
        """Get token expiration timestamp."""
        return self.created_at + self.expires_in


class TokenManager:
    """Manages access and refresh tokens."""
    
    def __init__(
        self,
        client: BaseClient,
        auto_refresh: bool = True,
    ):
        self.client = client
        self.auto_refresh = auto_refresh
        self._tokens: Optional[TokenPair] = None
        self._lock = Lock()

    def set_tokens(self, access_token: str, refresh_token: str, expires_in: int, **kwargs):
        """Set token pair."""
        with self._lock:
            self._tokens = TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                **kwargs,
            )

    def get_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if needed."""
        with self._lock:
            if not self._tokens:
                return None
            
            if self._tokens.is_expired and self.auto_refresh:
                self._refresh_token()
            
            return self._tokens.access_token if self._tokens else None

    def get_refresh_token(self) -> Optional[str]:
        """Get refresh token."""
        with self._lock:
            return self._tokens.refresh_token if self._tokens else None

    def clear_tokens(self):
        """Clear stored tokens."""
        with self._lock:
            self._tokens = None

    def _refresh_token(self) -> bool:
        """Refresh access token using refresh token."""
        if not self._tokens or not self._tokens.refresh_token:
            return False
        
        try:
            response = self.client.post(
                "/auth/refresh",
                json={"refresh_token": self._tokens.refresh_token},
            )
            data = response.json()
            self.set_tokens(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                expires_in=data.get("expires_in", 900),
            )
            return True
        except Exception:
            self.clear_tokens()
            return False

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.get_access_token() is not None


class AuthClient:
    """Authentication API client."""
    
    def __init__(self, client: BaseClient):
        self.client = client

    def register(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user."""
        response = self.client.post("/auth/register", json=data)
        return response.json()

    def login(self, email: str, password: str) -> TokenPair:
        """Login with email and password."""
        response = self.client.post("/auth/login", json={
            "email": email,
            "password": password,
        })
        data = response.json()
        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data.get("expires_in", 900),
        )

    def refresh(self, refresh_token: str) -> TokenPair:
        """Refresh access token."""
        response = self.client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        data = response.json()
        return TokenPair(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data.get("expires_in", 900),
        )

    def logout(self) -> Dict[str, Any]:
        """Logout current user."""
        response = self.client.post("/auth/logout")
        return response.json()

    def forgot_password(self, email: str) -> Dict[str, Any]:
        """Initiate password reset."""
        response = self.client.post("/auth/forgot-password", json={"email": email})
        return response.json()

    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Reset password with token."""
        response = self.client.post("/auth/reset-password", json={
            "token": token,
            "new_password": new_password,
        })
        return response.json()

    def verify_email(self, token: str) -> Dict[str, Any]:
        """Verify email with token."""
        response = self.client.post("/auth/verify-email", json={"token": token})
        return response.json()

    def get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user."""
        response = self.client.get("/users/me")
        return response.json()

    def update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile."""
        response = self.client.patch("/users/me", json=data)
        return response.json()

    def update_preferences(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences."""
        response = self.client.patch("/users/me/preferences", json=data)
        return response.json()

    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change password."""
        response = self.client.post("/users/me/change-password", json={
            "current_password": current_password,
            "new_password": new_password,
        })
        return response.json()

    def delete_account(self, password: str) -> Dict[str, Any]:
        """Delete account."""
        response = self.client.delete("/users/me", json={"password": password})
        return response.json()