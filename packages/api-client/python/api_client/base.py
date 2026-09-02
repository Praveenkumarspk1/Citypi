"""
Base Client

Base HTTP client class to avoid circular imports.
"""
from typing import Optional, Dict, Any
import httpx


class BaseClient:
    """Base HTTP client with common functionality."""
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = headers or {}

    def _get_headers(self, token_manager=None) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            **self.default_headers,
        }
        if token_manager:
            token = token_manager.get_access_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        return headers