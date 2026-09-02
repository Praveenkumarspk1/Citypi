"""
Metrics Service Adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ....application.ports.external_services import MetricsServicePort


@dataclass
class MetricData:
    """Metric data point"""
    name: str
    value: float
    labels: dict[str, str]
    timestamp: float


class BaseMetricsAdapter(MetricsServicePort, ABC):
    """Base metrics adapter"""

    @abstractmethod
    async def _increment_counter_request(
        self,
        name: str,
        labels: dict[str, str] | None,
        value: float,
    ) -> None:
        """Increment counter request"""
        pass

    @abstractmethod
    async def _record_histogram_request(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None,
    ) -> None:
        """Record histogram request"""
        pass

    @abstractmethod
    async def _set_gauge_request(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None,
    ) -> None:
        """Set gauge request"""
        pass

    async def increment_counter(
        self,
        name: str,
        labels: dict[str, str] | None = None,
        value: float = 1.0,
    ) -> None:
        """Increment counter"""
        await self._increment_counter_request(name, labels, value)

    async def record_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record histogram value"""
        await self._record_histogram_request(name, value, labels)

    async def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set gauge value"""
        await self._set_gauge_request(name, value, labels)


class PrometheusMetricsAdapter(BaseMetricsAdapter):
    """Prometheus metrics adapter"""

    def __init__(self, port: int = 9090, path: str = "/metrics"):
        self.port = port
        self.path = path
        self._registry = None
        self._counters: dict[str, Any] = {}
        self._histograms: dict[str, Any] = {}
        self._gauges: dict[str, Any] = {}
        self._server = None

    async def _get_registry(self):
        if self._registry is None:
            from prometheus_client import CollectorRegistry
            self._registry = CollectorRegistry()
        return self._registry

    def _get_counter(self, name: str, labels: dict[str, str] | None):
        from prometheus_client import Counter

        label_names = sorted(labels.keys()) if labels else []
        key = f"{name}:{','.join(label_names)}"

        if key not in self._counters:
            registry = await self._get_registry()
            self._counters[key] = Counter(
                name,
                f"Counter for {name}",
                labelnames=label_names,
                registry=registry,
            )

        return self._counters[key]

    def _get_histogram(self, name: str, labels: dict[str, str] | None):
        from prometheus_client import Histogram

        label_names = sorted(labels.keys()) if labels else []
        key = f"{name}:{','.join(label_names)}"

        if key not in self._histograms:
            registry = await self._get_registry()
            self._histograms[key] = Histogram(
                name,
                f"Histogram for {name}",
                labelnames=label_names,
                registry=registry,
            )

        return self._histograms[key]

    def _get_gauge(self, name: str, labels: dict[str, str] | None):
        from prometheus_client import Gauge

        label_names = sorted(labels.keys()) if labels else []
        key = f"{name}:{','.join(label_names)}"

        if key not in self._gauges:
            registry = await self._get_registry()
            self._gauges[key] = Gauge(
                name,
                f"Gauge for {name}",
                labelnames=label_names,
                registry=registry,
            )

        return self._gauges[key]

    async def _increment_counter_request(
        self,
        name: str,
        labels: dict[str, str] | None,
        value: float,
    ) -> None:
        counter = self._get_counter(name, labels)
        if labels:
            counter.labels(**labels).inc(value)
        else:
            counter.inc(value)

    async def _record_histogram_request(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None,
    ) -> None:
        histogram = self._get_histogram(name, labels)
        if labels:
            histogram.labels(**labels).observe(value)
        else:
            histogram.observe(value)

    async def _set_gauge_request(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None,
    ) -> None:
        gauge = self._get_gauge(name, labels)
        if labels:
            gauge.labels(**labels).set(value)
        else:
            gauge.set(value)

    async def start_server(self):
        """Start Prometheus metrics HTTP server"""
        from prometheus_client import start_http_server
        start_http_server(self.port, registry=await self._get_registry())

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        from prometheus_client import generate_latest
        return generate_latest(await self._get_registry()).decode()


class DatadogMetricsAdapter(BaseMetricsAdapter):
    """Datadog metrics adapter"""

    def __init__(self, api_key: str, app_key: str, host: str | None = None):
        self.api_key = api_key
        self.app_key = app_key
        self.host = host
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from datadog import initialize, statsd
            initialize(api_key=self.api_key, app_key=self.app_key)
            self._client = statsd
        return self._client

    async def _increment_counter_request(
        self,
        name: str,
        labels: dict[str, str] | None,
        value: float,
    ) -> None:
        client = await self._get_client()
        tags = [f"{k}:{v}" for k, v in (labels or {}).items()]
        if self.host:
            tags.append(f"host:{self.host}")
        client.increment(name, value, tags=tags)

    async def _record_histogram_request(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None,
    ) -> None:
        client = await self._get_client()
        tags = [f"{k}:{v}" for k, v in (labels or {}).items()]
        if self.host:
            tags.append(f"host:{self.host}")
        client.histogram(name, value, tags=tags)

    async def _set_gauge_request(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None,
    ) -> None:
        client = await self._get_client()
        tags = [f"{k}:{v}" for k, v in (labels or {}).items()]
        if self.host:
            tags.append(f"host:{self.host}")
        client.gauge(name, value, tags=tags)


class CloudWatchMetricsAdapter(BaseMetricsAdapter):
    """AWS CloudWatch metrics adapter"""

    def __init__(
        self,
        namespace: str,
        region: str = "us-east-1",
        access_key: str | None = None,
        secret_key: str | None = None,
    ):
        self.namespace = namespace
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import boto3
            self._client = boto3.client(
                "cloudwatch",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )
        return self._client

    async def _increment_counter_request(
        self,
        name: str,
        labels: dict[str, str] | None,
        value: float,
    ) -> None:
        client = await self._get_client()

        dimensions = [{"Name": k, "Value": v} for k, v in (labels or {}).items()]

        client.put_metric_data(
            Namespace=self.namespace,
            MetricData=[{
                "MetricName": name,
                "Dimensions": dimensions,
                "Value": value,
                "Unit": "Count",
            }],
        )

    async def _record_histogram_request(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None,
    ) -> None:
        # CloudWatch doesn't have native histograms, use statistics
        client = await self._get_client()

        dimensions = [{"Name": k, "Value": v} for k, v in (labels or {}).items()]

        client.put_metric_data(
            Namespace=self.namespace,
            MetricData=[{
                "MetricName": name,
                "Dimensions": dimensions,
                "Value": value,
                "Unit": "None",
            }],
        )

    async def _set_gauge_request(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None,
    ) -> None:
        client = await self._get_client()

        dimensions = [{"Name": k, "Value": v} for k, v in (labels or {}).items()]

        client.put_metric_data(
            Namespace=self.namespace,
            MetricData=[{
                "MetricName": name,
                "Dimensions": dimensions,
                "Value": value,
                "Unit": "None",
            }],
        )


class InMemoryMetricsAdapter(BaseMetricsAdapter):
    """In-memory metrics adapter (for development/testing)"""

    def __init__(self):
        self._counters: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._gauges: dict[str, float] = {}

    def _make_key(self, name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    async def _increment_counter_request(
        self,
        name: str,
        labels: dict[str, str] | None,
        value: float,
    ) -> None:
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value

    async def _record_histogram_request(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None,
    ) -> None:
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    async def _set_gauge_request(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None,
    ) -> None:
        key = self._make_key(name, labels)
        self._gauges[key] = value

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics for inspection"""
        return {
            "counters": self._counters,
            "histograms": {k: {"count": len(v), "sum": sum(v), "min": min(v), "max": max(v)}
                          for k, v in self._histograms.items()},
            "gauges": self._gauges,
        }
