"""
Rate Limiting Middleware
"""
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from ....infrastructure.config.redis import RedisKeys, get_redis_client
from ....infrastructure.config.settings import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""

    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis_client = redis_client
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next):
        if not self.settings.ratelimit.enabled:
            return await call_next(request)

        # Skip rate limiting for health checks
        if request.url.path.startswith("/health") or request.url.path.startswith("/api/v1/health"):
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)

        # Determine rate limit based on endpoint
        limit, window = self._get_rate_limit(request)

        # Check rate limit
        allowed, retry_after = await self._check_rate_limit(client_id, request.url.path, limit, window)

        if not allowed:
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate Limit Exceeded",
                    "message": f"Too many requests. Limit: {limit} per {window} seconds",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                    "Retry-After": str(retry_after),
                },
            )

        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - 1))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from auth
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"

    def _get_rate_limit(self, request: Request) -> tuple[int, int]:
        """Get rate limit for endpoint"""
        path = request.url.path

        # Auth endpoints - stricter limits
        if "/auth/" in path or "/login" in path or "/register" in path:
            return self.settings.ratelimit.auth_limit, self.settings.ratelimit.auth_window

        # WebSocket endpoints
        if "/ws/" in path or "/websocket" in path:
            return self.settings.ratelimit.websocket_limit, self.settings.ratelimit.websocket_window

        # API endpoints
        if path.startswith("/api/"):
            return self.settings.ratelimit.api_limit, self.settings.ratelimit.api_window

        # Default
        return self.settings.ratelimit.default_limit, self.settings.ratelimit.default_window

    async def _check_rate_limit(
        self, client_id: str, endpoint: str, limit: int, window: int
    ) -> tuple[bool, int]:
        """Check if request is within rate limit"""
        if not self.redis_client:
            self.redis_client = get_redis_client()

        key = RedisKeys.RATE_LIMIT.format(endpoint=endpoint.replace("/", ":"), identifier=client_id)

        try:
            current = await self.redis_client.get(key)

            if current is None:
                # First request
                await self.redis_client.setex(key, window, 1)
                return True, window

            current_count = int(current)

            if current_count >= limit:
                # Rate limited
                ttl = await self.redis_client.ttl(key)
                return False, max(ttl, 1)

            # Increment counter
            await self.redis_client.incr(key)
            return True, window

        except Exception:
            # If Redis fails, allow request (fail open)
            return True, window
