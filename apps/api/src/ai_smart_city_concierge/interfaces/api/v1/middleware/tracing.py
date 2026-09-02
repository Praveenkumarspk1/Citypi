"""
Tracing Middleware
Propagates OpenTelemetry trace context across requests.
"""
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ....infrastructure.observability.logging import get_logger
from ....infrastructure.observability.tracing import get_tracer

logger = get_logger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for distributed tracing with OpenTelemetry."""

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        span_name = f"{request.method} {request.url.path}"

        tracer = get_tracer()
        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.host", request.url.hostname or "")
            span.set_attribute("trace.id", trace_id)

            start_time = time.time()

            try:
                response = await call_next(request)
                duration = time.time() - start_time

                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_duration_ms", round(duration * 1000, 2))

                response.headers["X-Request-ID"] = trace_id
                return response

            except Exception as exc:
                duration = time.time() - start_time
                span.set_attribute("http.response_duration_ms", round(duration * 1000, 2))
                span.record_exception(exc)
                raise
