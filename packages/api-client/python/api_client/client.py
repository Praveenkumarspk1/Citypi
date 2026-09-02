"""
Main API Client

Synchronous and asynchronous HTTP clients for the API.
"""
import httpx
from typing import Optional, Dict, Any, Type, TypeVar
from pydantic import BaseModel

from shared_config import BaseSettings
from .base import BaseClient as BaseClientBase
from .auth import TokenManager
from .endpoints import (
    ChatEndpoint,
    POIEndpoint,
    ItineraryEndpoint,
    TransitEndpoint,
    WeatherEndpoint,
    UserEndpoint,
    ConversationEndpoint,
    MediaEndpoint,
    FeedbackEndpoint,
    AnalyticsEndpoint,
)
from .exceptions import APIError, AuthenticationError, RateLimitError, NotFoundError


T = TypeVar("T", bound=BaseModel)


class APIClient(BaseClientBase):
    """Synchronous API client."""
    
    def __init__(
        self,
        base_url: str,
        token_manager: Optional[TokenManager] = None,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(base_url, timeout, headers)
        self.token_manager = token_manager
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._get_headers(),
        )
        self._init_endpoints()

    def _init_endpoints(self):
        """Initialize API endpoints."""
        self.chat = ChatEndpoint(self)
        self.pois = POIEndpoint(self)
        self.itineraries = ItineraryEndpoint(self)
        self.transit = TransitEndpoint(self)
        self.weather = WeatherEndpoint(self)
        self.users = UserEndpoint(self)
        self.conversations = ConversationEndpoint(self)
        self.media = MediaEndpoint(self)
        self.feedback = FeedbackEndpoint(self)
        self.analytics = AnalyticsEndpoint(self)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return super()._get_headers(self.token_manager)

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 401:
            raise AuthenticationError("Unauthorized", response=response)
        elif response.status_code == 403:
            raise AuthenticationError("Forbidden", response=response)
        elif response.status_code == 404:
            raise NotFoundError("Resource not found", response=response)
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded", response=response)
        elif response.status_code >= 500:
            raise APIError(f"Server error: {response.status_code}", response=response)
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                raise APIError(
                    error_data.get("error", f"HTTP {response.status_code}"),
                    response=response,
                    code=error_data.get("code"),
                    details=error_data.get("details"),
                )
            except Exception:
                raise APIError(f"HTTP {response.status_code}", response=response)
        
        try:
            return response.json()
        except Exception:
            return {"data": response.text}

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make HTTP request."""
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        return self._client.request(
            method=method,
            url=path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=request_headers,
        )

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return self.request("GET", path, params=params, **kwargs)

    def post(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return self.request("POST", path, json=json, **kwargs)

    def put(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return self.request("PUT", path, json=json, **kwargs)

    def patch(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return self.request("PATCH", path, json=json, **kwargs)

    def delete(self, path: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncAPIClient(BaseClientBase):
    """Asynchronous API client."""
    
    def __init__(
        self,
        base_url: str,
        token_manager: Optional[TokenManager] = None,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(base_url, timeout, headers)
        self.token_manager = token_manager
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._get_headers(),
        )
        self._init_endpoints()

    def _init_endpoints(self):
        """Initialize API endpoints."""
        self.chat = ChatEndpoint(self)
        self.pois = POIEndpoint(self)
        self.itineraries = ItineraryEndpoint(self)
        self.transit = TransitEndpoint(self)
        self.weather = WeatherEndpoint(self)
        self.users = UserEndpoint(self)
        self.conversations = ConversationEndpoint(self)
        self.media = MediaEndpoint(self)
        self.feedback = FeedbackEndpoint(self)
        self.analytics = AnalyticsEndpoint(self)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return super()._get_headers(self.token_manager)

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make HTTP request."""
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        return await self._client.request(
            method=method,
            url=path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=request_headers,
        )

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return await self.request("GET", path, params=params, **kwargs)

    async def post(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return await self.request("POST", path, json=json, **kwargs)

    async def put(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return await self.request("PUT", path, json=json, **kwargs)

    async def patch(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return await self.request("PATCH", path, json=json, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("DELETE", path, **kwargs)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def create_client(
    base_url: str = None,
    token_manager: Optional[TokenManager] = None,
    async_client: bool = False,
    **kwargs,
):
    """Factory function to create API client."""
    if base_url is None:
        settings = BaseSettings()
        base_url = f"http://localhost:8000{settings.api_prefix}"
    
    if async_client:
        return AsyncAPIClient(base_url, token_manager, **kwargs)
    return APIClient(base_url, token_manager, **kwargs)