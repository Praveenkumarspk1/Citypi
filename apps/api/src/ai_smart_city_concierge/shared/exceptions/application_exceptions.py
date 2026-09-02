"""
Application-level exceptions
"""


class ApplicationException(Exception):
    """Base exception for application layer."""

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or "APPLICATION_ERROR"


class NotFoundException(ApplicationException):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str | None = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, code="NOT_FOUND")


class ValidationException(ApplicationException):
    """Invalid input data."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, code="VALIDATION_ERROR")
        self.field = field


class ConflictException(ApplicationException):
    """Resource conflict."""

    def __init__(self, message: str):
        super().__init__(message, code="CONFLICT")


class UnauthorizedException(ApplicationException):
    """Unauthorized access."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, code="UNAUTHORIZED")


class ForbiddenException(ApplicationException):
    """Forbidden access."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, code="FORBIDDEN")


class ServiceUnavailableException(ApplicationException):
    """External service unavailable."""

    def __init__(self, service: str):
        super().__init__(f"Service unavailable: {service}", code="SERVICE_UNAVAILABLE")
        self.service = service
