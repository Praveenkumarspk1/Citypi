"""
Observability Settings

Configuration for monitoring, logging, tracing, and metrics.
"""
from typing import List, Dict
from pydantic import Field
from .base import BaseSettings


class ObservabilitySettings(BaseSettings):
    """Observability configuration."""
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json, text
    log_file: str = ""
    log_rotation: str = "1 day"
    log_retention: str = "30 days"
    log_compression: str = "gz"

    # Metrics (Prometheus)
    metrics_enabled: bool = True
    metrics_port: int = 9090
    metrics_path: str = "/metrics"
    metrics_namespace: str = "concierge"
    metrics_subsystem: str = ""

    # Tracing (Jaeger)
    tracing_enabled: bool = True
    tracing_service_name: str = "concierge"
    tracing_jaeger_agent_host: str = "localhost"
    tracing_jaeger_agent_port: int = 6831
    tracing_jaeger_collector_endpoint: str = "http://localhost:14268/api/traces"
    tracing_sample_rate: float = 1.0
    tracing_exporter: str = "jaeger"  # jaeger, otlp, zipkin

    # OpenTelemetry
    otel_endpoint: str = "http://localhost:4317"
    otel_headers: Dict[str, str] = Field(default_factory=dict)
    otel_resource_attributes: Dict[str, str] = Field(default_factory=dict)

    # Logging aggregation (Loki)
    loki_enabled: bool = True
    loki_url: str = "http://localhost:3100"
    loki_tenant: str = ""
    loki_labels: Dict[str, str] = Field(default_factory=dict)

    # Health checks
    health_check_interval: int = 30
    health_check_timeout: int = 10
    health_check_failure_threshold: int = 3

    # Alerting
    alert_enabled: bool = True
    alert_webhook_url: str = ""
    alert_slack_webhook: str = ""
    alert_pagerduty_key: str = ""

    # Profiling
    profiling_enabled: bool = False
    profiling_interval: int = 60