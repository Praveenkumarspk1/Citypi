"""
Metrics Collection
"""
import logging
import time
from dataclasses import dataclass
from threading import Lock

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logger = logging.getLogger(__name__)


@dataclass
class MetricLabels:
    """Standard metric labels"""
    service: str = "ai-smart-city-concierge"
    version: str = "1.0.0"
    environment: str = "development"


class MetricsCollector:
    """Application metrics collector"""

    def __init__(self, labels: MetricLabels | None = None):
        self.labels = labels or MetricLabels()
        self._registry = CollectorRegistry()
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}
        self._gauges: dict[str, Gauge] = {}
        self._lock = Lock()

        # Initialize standard metrics
        self._init_standard_metrics()

    def _init_standard_metrics(self) -> None:
        """Initialize standard application metrics"""

        # HTTP metrics
        self._counters["http_requests_total"] = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
            registry=self._registry,
        )

        self._histograms["http_request_duration_seconds"] = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self._registry,
        )

        # Business metrics
        self._counters["conversations_started_total"] = Counter(
            "conversations_started_total",
            "Total conversations started",
            ["user_type"],
            registry=self._registry,
        )

        self._counters["messages_sent_total"] = Counter(
            "messages_sent_total",
            "Total messages sent",
            ["direction", "type"],
            registry=self._registry,
        )

        self._counters["itineraries_created_total"] = Counter(
            "itineraries_created_total",
            "Total itineraries created",
            ["source"],
            registry=self._registry,
        )

        self._counters["pois_searched_total"] = Counter(
            "pois_searched_total",
            "Total POI searches",
            ["category", "source"],
            registry=self._registry,
        )

        self._counters["transit_routes_calculated_total"] = Counter(
            "transit_routes_calculated_total",
            "Total transit routes calculated",
            ["mode"],
            registry=self._registry,
        )

        self._counters["weather_requests_total"] = Counter(
            "weather_requests_total",
            "Total weather requests",
            ["type"],
            registry=self._registry,
        )

        # AI/ML metrics
        self._histograms["llm_tokens_used"] = Histogram(
            "llm_tokens_used",
            "LLM tokens used per request",
            ["model", "type"],
            buckets=[10, 50, 100, 250, 500, 1000, 2000, 5000, 10000],
            registry=self._registry,
        )

        self._histograms["embedding_generation_duration_seconds"] = Histogram(
            "embedding_generation_duration_seconds",
            "Embedding generation duration",
            ["model"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
            registry=self._registry,
        )

        self._histograms["vector_search_duration_seconds"] = Histogram(
            "vector_search_duration_seconds",
            "Vector search duration",
            ["collection"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=self._registry,
        )

        # External API metrics
        self._counters["external_api_requests_total"] = Counter(
            "external_api_requests_total",
            "Total external API requests",
            ["api", "endpoint", "status"],
            registry=self._registry,
        )

        self._histograms["external_api_duration_seconds"] = Histogram(
            "external_api_duration_seconds",
            "External API request duration",
            ["api", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
            registry=self._registry,
        )

        # Cache metrics
        self._counters["cache_operations_total"] = Counter(
            "cache_operations_total",
            "Total cache operations",
            ["operation", "result"],
            registry=self._registry,
        )

        self._histograms["cache_operation_duration_seconds"] = Histogram(
            "cache_operation_duration_seconds",
            "Cache operation duration",
            ["operation"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
            registry=self._registry,
        )

        # Database metrics
        self._histograms["db_query_duration_seconds"] = Histogram(
            "db_query_duration_seconds",
            "Database query duration",
            ["operation", "table"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self._registry,
        )

        self._counters["db_errors_total"] = Counter(
            "db_errors_total",
            "Total database errors",
            ["operation", "error_type"],
            registry=self._registry,
        )

        # Queue metrics
        self._gauges["queue_size"] = Gauge(
            "queue_size",
            "Current queue size",
            ["queue"],
            registry=self._registry,
        )

        self._counters["queue_jobs_total"] = Counter(
            "queue_jobs_total",
            "Total queue jobs",
            ["queue", "status"],
            registry=self._registry,
        )

        self._histograms["queue_job_duration_seconds"] = Histogram(
            "queue_job_duration_seconds",
            "Queue job processing duration",
            ["queue"],
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
            registry=self._registry,
        )

        # Error metrics
        self._counters["errors_total"] = Counter(
            "errors_total",
            "Total errors",
            ["type", "component"],
            registry=self._registry,
        )

        # Active users/connections
        self._gauges["active_users"] = Gauge(
            "active_users",
            "Number of active users",
            registry=self._registry,
        )

        self._gauges["active_connections"] = Gauge(
            "active_connections",
            "Number of active connections",
            ["type"],
            registry=self._registry,
        )

    def increment_counter(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        value: float = 1.0,
    ) -> None:
        """Increment a counter"""
        with self._lock:
            if name not in self._counters:
                logger.warning(f"Counter {name} not found")
                return

            # Merge with default labels
            all_labels = {**self.labels.__dict__, **(labels or {})}
            self._counters[name].labels(**all_labels).inc(value)

    def record_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a histogram value"""
        with self._lock:
            if name not in self._histograms:
                logger.warning(f"Histogram {name} not found")
                return

            all_labels = {**self.labels.__dict__, **(labels or {})}
            self._histograms[name].labels(**all_labels).observe(value)

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge value"""
        with self._lock:
            if name not in self._gauges:
                logger.warning(f"Gauge {name} not found")
                return

            all_labels = {**self.labels.__dict__, **(labels or {})}
            self._gauges[name].labels(**all_labels).set(value)

    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format"""
        return generate_latest(self._registry)

    def get_content_type(self) -> str:
        """Get Prometheus content type"""
        return CONTENT_TYPE_LATEST


class PrometheusMetrics:
    """Prometheus metrics exporter"""

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    async def metrics_endpoint(self) -> tuple[bytes, str]:
        """Metrics endpoint handler"""
        metrics = self.collector.get_metrics()
        content_type = self.collector.get_content_type()
        return metrics, content_type


# Global metrics collector
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def init_metrics(labels: MetricLabels | None = None) -> MetricsCollector:
    """Initialize global metrics collector"""
    global _metrics_collector
    _metrics_collector = MetricsCollector(labels)
    return _metrics_collector


# Convenience functions
def increment_counter(name: str, labels: dict[str, str] | None = None, value: float = 1.0) -> None:
    get_metrics_collector().increment_counter(name, labels, value)


def record_histogram(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    get_metrics_collector().record_histogram(name, value, labels)


def set_gauge(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    get_metrics_collector().set_gauge(name, value, labels)


# Context manager for timing
class Timer:
    """Context manager for timing operations"""

    def __init__(self, histogram_name: str, labels: dict[str, str] | None = None):
        self.histogram_name = histogram_name
        self.labels = labels
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        record_histogram(self.histogram_name, duration, self.labels)
