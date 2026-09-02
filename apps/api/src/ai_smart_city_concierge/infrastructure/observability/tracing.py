"""
Distributed Tracing
"""
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from opentelemetry import trace
from opentelemetry.baggage import get_baggage, set_baggage
from opentelemetry.exporter.jaeger.proto.grpc import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)


@dataclass
class TracingConfig:
    """Tracing configuration"""
    service_name: str = "ai-smart-city-concierge"
    service_version: str = "1.0.0"
    environment: str = "development"
    jaeger_endpoint: str | None = None
    otlp_endpoint: str | None = None
    sample_rate: float = 1.0
    enable_console_exporter: bool = False


class TracingManager:
    """Distributed tracing manager"""

    def __init__(self, config: TracingConfig | None = None):
        self.config = config or TracingConfig()
        self._tracer_provider: TracerProvider | None = None
        self._tracer = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize tracing"""
        if self._initialized:
            return

        # Create resource
        resource = Resource.create({
            SERVICE_NAME: self.config.service_name,
            SERVICE_VERSION: self.config.service_version,
            "deployment.environment": self.config.environment,
        })

        # Create tracer provider
        self._tracer_provider = TracerProvider(
            resource=resource,
        )

        # Configure exporters
        self._configure_exporters()

        # Set global tracer provider
        trace.set_tracer_provider(self._tracer_provider)

        # Get tracer
        self._tracer = trace.get_tracer(
            self.config.service_name,
            version=self.config.service_version,
        )

        # Set up propagators
        self._configure_propagators()

        # Auto-instrument libraries
        self._auto_instrument()

        self._initialized = True
        logger.info(f"Tracing initialized: service={self.config.service_name}")

    def _configure_exporters(self) -> None:
        """Configure span exporters"""
        # Jaeger exporter
        if self.config.jaeger_endpoint:
            jaeger_exporter = JaegerExporter(
                endpoint=self.config.jaeger_endpoint,
            )
            self._tracer_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
            logger.info(f"Jaeger exporter configured: {self.config.jaeger_endpoint}")

        # OTLP exporter
        if self.config.otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.config.otlp_endpoint,
            )
            self._tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
            logger.info(f"OTLP exporter configured: {self.config.otlp_endpoint}")

        # Console exporter (for development)
        if self.config.enable_console_exporter:
            console_exporter = ConsoleSpanExporter()
            self._tracer_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
            logger.info("Console exporter enabled")

    def _configure_propagators(self) -> None:
        """Configure context propagators"""
        # Use B3 and W3C tracecontext propagators
        propagator = CompositePropagator([
            B3MultiFormat(),
        ])
        set_global_textmap(propagator)

    def _auto_instrument(self) -> None:
        """Auto-instrument common libraries"""
        try:
            FastAPIInstrumentor.instrument()
        except Exception as e:
            logger.warning(f"FastAPI instrumentation failed: {e}")

        try:
            SQLAlchemyInstrumentor.instrument()
        except Exception as e:
            logger.warning(f"SQLAlchemy instrumentation failed: {e}")

        try:
            RedisInstrumentor.instrument()
        except Exception as e:
            logger.warning(f"Redis instrumentation failed: {e}")

        try:
            HTTPXClientInstrumentor.instrument()
        except Exception as e:
            logger.warning(f"HTTPX instrumentation failed: {e}")

        try:
            AioHttpClientInstrumentor.instrument()
        except Exception as e:
            logger.warning(f"AioHTTP instrumentation failed: {e}")

    def get_tracer(self):
        """Get tracer instance"""
        if not self._initialized:
            self.initialize()
        return self._tracer

    @asynccontextmanager
    async def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None,
        links: list | None = None,
    ):
        """Start a new span as context manager"""
        tracer = self.get_tracer()

        with tracer.start_as_current_span(
            name,
            kind=kind,
            attributes=attributes or {},
            links=links or [],
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def start_span_sync(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None,
    ):
        """Start a new span (synchronous)"""
        tracer = self.get_tracer()
        return tracer.start_span(name, kind=kind, attributes=attributes or {})

    def add_span_attributes(self, attributes: dict[str, Any]) -> None:
        """Add attributes to current span"""
        span = trace.get_current_span()
        if span and span.is_recording():
            for key, value in attributes.items():
                span.set_attribute(key, value)

    def add_span_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add event to current span"""
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event(name, attributes or {})

    def set_span_status(self, status: StatusCode, description: str | None = None) -> None:
        """Set current span status"""
        span = trace.get_current_span()
        if span and span.is_recording():
            span.set_status(Status(status, description))

    def record_exception(self, exception: Exception) -> None:
        """Record exception in current span"""
        span = trace.get_current_span()
        if span and span.is_recording():
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR, str(exception)))

    def get_current_trace_id(self) -> str | None:
        """Get current trace ID"""
        span = trace.get_current_span()
        if span and span.get_span_context():
            return format(span.get_span_context().trace_id, "032x")
        return None

    def get_current_span_id(self) -> str | None:
        """Get current span ID"""
        span = trace.get_current_span()
        if span and span.get_span_context():
            return format(span.get_span_context().span_id, "016x")
        return None

    def inject_context(self, carrier: dict[str, str]) -> None:
        """Inject trace context into carrier"""
        trace.get_tracer_provider().inject(carrier)

    def extract_context(self, carrier: dict[str, str]) -> Any:
        """Extract trace context from carrier"""
        return trace.get_tracer_provider().extract(carrier)

    def set_baggage(self, key: str, value: str) -> None:
        """Set baggage value"""
        set_baggage(key, value)

    def get_baggage(self, key: str) -> str | None:
        """Get baggage value"""
        return get_baggage(key)

    def shutdown(self) -> None:
        """Shutdown tracing"""
        if self._tracer_provider:
            self._tracer_provider.shutdown()
            self._initialized = False
            logger.info("Tracing shutdown")


class JaegerTracer:
    """Jaeger-specific tracer wrapper"""

    def __init__(self, config: TracingConfig):
        self.config = config
        self._manager = TracingManager(config)

    def initialize(self) -> None:
        self._manager.initialize()

    @property
    def tracer(self):
        return self._manager.get_tracer()

    def start_span(self, name: str, **kwargs):
        return self._manager.start_span_sync(name, **kwargs)

    @asynccontextmanager
    async def trace(self, name: str, **kwargs):
        async with self._manager.start_span(name, **kwargs) as span:
            yield span

    def shutdown(self) -> None:
        self._manager.shutdown()


# Global tracing manager
_tracing_manager: TracingManager | None = None


def get_tracing_manager() -> TracingManager:
    """Get global tracing manager"""
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager()
    return _tracing_manager


def get_tracer() -> trace.Tracer:
    """Get global tracer instance (convenience function)."""
    return get_tracing_manager().get_tracer()


def init_tracing(config: TracingConfig | None = None) -> TracingManager:
    """Initialize global tracing"""
    global _tracing_manager
    _tracing_manager = TracingManager(config)
    _tracing_manager.initialize()
    return _tracing_manager


# Decorator for tracing functions
def trace_function(
    name: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
):
    """Decorator to trace a function"""
    def decorator(func: Callable):
        span_name = name or f"{func.__module__}.{func.__qualname__}"

        async def async_wrapper(*args, **kwargs):
            manager = get_tracing_manager()
            async with manager.start_span(span_name, kind=kind, attributes=attributes) as span:
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        def sync_wrapper(*args, **kwargs):
            manager = get_tracing_manager()
            with manager.start_span_sync(span_name, kind=kind, attributes=attributes) as span:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
