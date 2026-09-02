"""
Distributed Tracing Service Adapters
"""
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from ....application.ports.external_services import TracingServicePort


@dataclass
class SpanContext:
    """Span context"""
    trace_id: str
    span_id: str
    parent_span_id: str | None
    baggage: dict[str, str]


@dataclass
class Span:
    """Span data"""
    name: str
    context: SpanContext
    start_time: float
    end_time: float | None
    attributes: dict[str, Any]
    events: list[dict[str, Any]]
    status: str
    status_message: str | None


class BaseTracingAdapter(TracingServicePort, ABC):
    """Base tracing adapter"""

    @abstractmethod
    async def _start_span_request(
        self,
        name: str,
        parent_context: Any | None,
    ) -> Span:
        """Start span request"""
        pass

    @abstractmethod
    async def _end_span_request(self, span: Span) -> None:
        """End span request"""
        pass

    @abstractmethod
    async def _add_attribute_request(self, span: Span, key: str, value: Any) -> None:
        """Add attribute request"""
        pass

    @abstractmethod
    async def _record_exception_request(self, span: Span, exception: Exception) -> None:
        """Record exception request"""
        pass

    def start_span(
        self,
        name: str,
        parent_context: Any | None = None,
    ) -> Any:
        """Start a trace span"""
        # This is synchronous for context management
        import asyncio
        return asyncio.create_task(self._start_span_request(name, parent_context))

    def end_span(self, span: Any) -> None:
        """End a trace span"""
        import asyncio
        asyncio.create_task(self._end_span_request(span))

    def add_span_attribute(self, span: Any, key: str, value: Any) -> None:
        """Add attribute to span"""
        import asyncio
        asyncio.create_task(self._add_attribute_request(span, key, value))

    def record_exception(self, span: Any, exception: Exception) -> None:
        """Record exception in span"""
        import asyncio
        asyncio.create_task(self._record_exception_request(span, exception))

    @asynccontextmanager
    async def trace(self, name: str, parent_context: Any | None = None):
        """Context manager for tracing"""
        span = await self._start_span_request(name, parent_context)
        try:
            yield span
        except Exception as e:
            await self._record_exception_request(span, e)
            raise
        finally:
            await self._end_span_request(span)


class JaegerTracingAdapter(BaseTracingAdapter):
    """Jaeger tracing adapter"""

    def __init__(
        self,
        service_name: str,
        agent_host: str = "localhost",
        agent_port: int = 6831,
        collector_endpoint: str | None = None,
    ):
        self.service_name = service_name
        self.agent_host = agent_host
        self.agent_port = agent_port
        self.collector_endpoint = collector_endpoint
        self._tracer = None

    async def _get_tracer(self):
        if self._tracer is None:
            from jaeger_client import Config

            config = Config(
                config={
                    "sampler": {
                        "type": "const",
                        "param": 1,
                    },
                    "local_agent": {
                        "reporting_host": self.agent_host,
                        "reporting_port": self.agent_port,
                    },
                    "logging": True,
                },
                service_name=self.service_name,
                validate=True,
            )

            if self.collector_endpoint:
                config.config["collector"] = {
                    "endpoint": self.collector_endpoint,
                }

            self._tracer = config.initialize_tracer()

        return self._tracer

    async def _start_span_request(
        self,
        name: str,
        parent_context: Any | None,
    ) -> Span:
        tracer = await self._get_tracer()

        # Extract parent context if provided
        parent_span = None
        if parent_context and hasattr(parent_context, 'context'):
            parent_span = parent_context

        # Start span
        if parent_span:
            span = tracer.start_span(name, child_of=parent_span)
        else:
            span = tracer.start_span(name)

        return Span(
            name=name,
            context=SpanContext(
                trace_id=format(span.context.trace_id, '032x'),
                span_id=format(span.context.span_id, '016x'),
                parent_span_id=format(span.parent_id, '016x') if span.parent_id else None,
                baggage={},
            ),
            start_time=span.start_time,
            end_time=None,
            attributes={},
            events=[],
            status="ok",
            status_message=None,
        )

    async def _end_span_request(self, span: Span) -> None:
        # Jaeger spans are finished automatically when context ends
        # But we can manually finish if we have the actual span object
        pass

    async def _add_attribute_request(self, span: Span, key: str, value: Any) -> None:
        span.attributes[key] = value

    async def _record_exception_request(self, span: Span, exception: Exception) -> None:
        span.status = "error"
        span.status_message = str(exception)
        span.events.append({
            "name": "exception",
            "attributes": {
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
            },
        })


class ZipkinTracingAdapter(BaseTracingAdapter):
    """Zipkin tracing adapter"""

    def __init__(
        self,
        service_name: str,
        collector_url: str = "http://localhost:9411/api/v2/spans",
    ):
        self.service_name = service_name
        self.collector_url = collector_url
        self._tracer = None

    async def _get_tracer(self):
        if self._tracer is None:
            from py_zipkin import zipkin
            self._tracer = zipkin
        return self._tracer

    async def _start_span_request(
        self,
        name: str,
        parent_context: Any | None,
    ) -> Span:
        import time
        import uuid

        trace_id = format(uuid.uuid4().int & ((1 << 64) - 1), '016x')
        span_id = format(uuid.uuid4().int & ((1 << 64) - 1), '016x')
        parent_span_id = None

        if parent_context and hasattr(parent_context, 'context'):
            parent_span_id = parent_context.context.span_id

        return Span(
            name=name,
            context=SpanContext(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                baggage={},
            ),
            start_time=time.time(),
            end_time=None,
            attributes={},
            events=[],
            status="ok",
            status_message=None,
        )

    async def _end_span_request(self, span: Span) -> None:
        import time

        import aiohttp

        span.end_time = time.time()

        # Send to Zipkin collector
        zipkin_span = {
            "traceId": span.context.trace_id,
            "id": span.context.span_id,
            "name": span.name,
            "timestamp": int(span.start_time * 1000000),
            "duration": int((span.end_time - span.start_time) * 1000000),
            "localEndpoint": {
                "serviceName": self.service_name,
            },
            "tags": span.attributes,
            "annotations": [
                {
                    "timestamp": int(event.get("timestamp", span.start_time) * 1000000),
                    "value": event.get("name", "event"),
                }
                for event in span.events
            ],
        }

        if span.context.parent_span_id:
            zipkin_span["parentId"] = span.context.parent_span_id

        if span.status == "error":
            zipkin_span["tags"]["error"] = "true"
            zipkin_span["tags"]["error.message"] = span.status_message or ""

        async with aiohttp.ClientSession() as session:
            await session.post(
                self.collector_url,
                json=[zipkin_span],
                headers={"Content-Type": "application/json"},
            )

    async def _add_attribute_request(self, span: Span, key: str, value: Any) -> None:
        span.attributes[key] = str(value)

    async def _record_exception_request(self, span: Span, exception: Exception) -> None:
        span.status = "error"
        span.status_message = str(exception)
        span.events.append({
            "name": "exception",
            "timestamp": time.time(),
            "attributes": {
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
            },
        })


class OpenTelemetryTracingAdapter(BaseTracingAdapter):
    """OpenTelemetry tracing adapter"""

    def __init__(
        self,
        service_name: str,
        exporter_endpoint: str | None = None,
        exporter_type: str = "otlp",  # otlp, jaeger, zipkin
    ):
        self.service_name = service_name
        self.exporter_endpoint = exporter_endpoint
        self.exporter_type = exporter_type
        self._tracer = None
        self._provider = None

    async def _get_tracer(self):
        if self._tracer is None:
            from opentelemetry import trace
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            # Create resource
            resource = Resource.create({
                "service.name": self.service_name,
            })

            # Create provider
            self._provider = TracerProvider(resource=resource)

            # Configure exporter
            if self.exporter_type == "otlp":
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=self.exporter_endpoint)
            elif self.exporter_type == "jaeger":
                from opentelemetry.exporter.jaeger.proto.grpc import JaegerExporter
                exporter = JaegerExporter(
                    agent_host_name="localhost",
                    agent_port=6831,
                )
            elif self.exporter_type == "zipkin":
                from opentelemetry.exporter.zipkin.proto.http import ZipkinExporter
                exporter = ZipkinExporter(endpoint=self.exporter_endpoint)
            else:
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter
                exporter = ConsoleSpanExporter()

            # Add span processor
            self._provider.add_span_processor(BatchSpanProcessor(exporter))

            # Set global tracer provider
            trace.set_tracer_provider(self._provider)

            # Get tracer
            self._tracer = trace.get_tracer(self.service_name)

        return self._tracer

    async def _start_span_request(
        self,
        name: str,
        parent_context: Any | None,
    ) -> Span:
        tracer = await self._get_tracer()

        # Start span
        if parent_context and hasattr(parent_context, 'otel_span'):
            span = tracer.start_span(name, context=parent_context.otel_span)
        else:
            span = tracer.start_span(name)

        return Span(
            name=name,
            context=SpanContext(
                trace_id=format(span.context.trace_id, '032x'),
                span_id=format(span.context.span_id, '016x'),
                parent_span_id=None,  # Would need to extract from parent
                baggage={},
            ),
            start_time=span.start_time / 1e9,
            end_time=None,
            attributes={},
            events=[],
            status="ok",
            status_message=None,
        )

    async def _end_span_request(self, span: Span) -> None:
        # OpenTelemetry spans are ended when context exits
        pass

    async def _add_attribute_request(self, span: Span, key: str, value: Any) -> None:
        span.attributes[key] = value

    async def _record_exception_request(self, span: Span, exception: Exception) -> None:
        span.status = "error"
        span.status_message = str(exception)
        span.events.append({
            "name": "exception",
            "attributes": {
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
            },
        })


class InMemoryTracingAdapter(BaseTracingAdapter):
    """In-memory tracing adapter (for development/testing)"""

    def __init__(self):
        self._spans: list[Span] = []
        self._current_spans: dict[str, Span] = {}

    async def _start_span_request(
        self,
        name: str,
        parent_context: Any | None,
    ) -> Span:
        import time
        import uuid

        trace_id = format(uuid.uuid4().int & ((1 << 64) - 1), '016x')
        span_id = format(uuid.uuid4().int & ((1 << 64) - 1), '016x')
        parent_span_id = None

        if parent_context and hasattr(parent_context, 'context'):
            parent_span_id = parent_context.context.span_id
            trace_id = parent_context.context.trace_id

        span = Span(
            name=name,
            context=SpanContext(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                baggage={},
            ),
            start_time=time.time(),
            end_time=None,
            attributes={},
            events=[],
            status="ok",
            status_message=None,
        )

        self._spans.append(span)
        self._current_spans[span_id] = span

        return span

    async def _end_span_request(self, span: Span) -> None:
        import time
        span.end_time = time.time()
        if span.context.span_id in self._current_spans:
            del self._current_spans[span.context.span_id]

    async def _add_attribute_request(self, span: Span, key: str, value: Any) -> None:
        span.attributes[key] = value

    async def _record_exception_request(self, span: Span, exception: Exception) -> None:
        span.status = "error"
        span.status_message = str(exception)
        span.events.append({
            "name": "exception",
            "attributes": {
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
            },
        })

    def get_spans(self) -> list[Span]:
        """Get all recorded spans"""
        return self._spans

    def get_trace(self, trace_id: str) -> list[Span]:
        """Get all spans for a trace"""
        return [s for s in self._spans if s.context.trace_id == trace_id]
