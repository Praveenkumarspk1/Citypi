"""
Exceptions

Custom exceptions for the API client.
"""
from typing import Optional, Dict, Any
import httpx


class APIClientError(Exception):
    """Base exception for API client errors."""
    
    def __init__(
        self,
        message: str,
        response: Optional[httpx.Response] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.response = response
        self.code = code
        self.details = details
        self.status_code = response.status_code if response else None

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class APIError(APIClientError):
    """General API error."""
    pass


class AuthenticationError(APIClientError):
    """Authentication/authorization error."""
    pass


class RateLimitError(APIClientError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, response: Optional[httpx.Response] = None, retry_after: Optional[int] = None):
        super().__init__(message, response, code="RATE_LIMITED")
        self.retry_after = retry_after


class NotFoundError(APIClientError):
    """Resource not found."""
    pass


class ValidationError(APIClientError):
    """Request validation error."""
    pass


class ServerError(APIClientError):
    """Server-side error (5xx)."""
    pass


class NetworkError(APIClientError):
    """Network/connection error."""
    pass


class TimeoutError(APIClientError):
    """Request timeout."""
    pass


# Exception mapping
STATUS_CODE_EXCEPTIONS = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthenticationError,
    404: NotFoundError,
    422: ValidationError,
    429: RateLimitError,
    500: ServerError,
    502: ServerError,
    503: ServerError,
    504: ServerError,
}


def map_exception(response: httpx.Response) -> APIClientError:
    """Map HTTP response to appropriate exception."""
    exception_class = STATUS_CODE_EXCEPTIONS.get(response.status_code, APIError)
    
    try:
        error_data = response.json()
        message = error_data.get("error", f"HTTP {response.status_code}")
        code = error_data.get("code")
        details = error_data.get("details")
    except Exception:
        message = f"HTTP {response.status_code}"
        code = None
        details = None
    
    return exception_class(message, response=response, code=code, details=details)