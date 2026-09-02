"""
Authentication Middleware
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED

from ai_smart_city_concierge.infrastructure.auth.jwt import verify_token
from ....infrastructure.config.settings import get_settings


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware to extract user from JWT token"""

    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        # Paths that don't require authentication
        self.public_paths = {
            "/health",
            "/api/v1/health",
            "/api/v1/users/login",
            "/api/v1/users/register",
            "/api/v1/users/refresh",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        if request.url.path in self.public_paths:
            return await call_next(request)

        # Skip auth for paths starting with public prefixes
        for path in self.public_paths:
            if request.url.path.startswith(path):
                return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": "Missing or invalid authorization header",
                    "code": "MISSING_TOKEN",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ")[1]

        # Verify token
        payload = verify_token(token)
        if not payload:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": "Invalid or expired token",
                    "code": "INVALID_TOKEN",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Add user info to request state
        request.state.user_id = payload.get("sub")
        request.state.user_email = payload.get("email")
        request.state.user_role = payload.get("role", "user")
        request.state.token_type = payload.get("type", "access")

        return await call_next(request)
