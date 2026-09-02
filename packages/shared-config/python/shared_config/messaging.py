"""
Messaging Settings

Configuration for message queues and event streaming.
"""
from typing import List
from pydantic import Field
from .base import BaseSettings


class MessagingSettings(BaseSettings):
    """Messaging configuration."""
    
    # Provider
    messaging_provider: str = "redis"  # redis, rabbitmq, kafka, nats

    # Redis Streams
    redis_streams_max_length: int = 10000
    redis_streams_consumer_group: str = "concierge"
    redis_streams_block_ms: int = 5000
    redis_streams_count: int = 100

    # RabbitMQ
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/", validation_alias="RABBITMQ_URL")
    rabbitmq_exchange: str = "concierge"
    rabbitmq_exchange_type: str = "topic"
    rabbitmq_durable: bool = True
    rabbitmq_prefetch_count: int = 10
    rabbitmq_heartbeat: int = 60

    # Kafka
    kafka_bootstrap_servers: List[str] = Field(default_factory=lambda: ["localhost:9092"])
    kafka_client_id: str = "concierge"
    kafka_group_id: str = "concierge-consumer"
    kafka_auto_offset_reset: str = "latest"
    kafka_enable_auto_commit: bool = True
    kafka_security_protocol: str = "PLAINTEXT"
    kafka_sasl_mechanism: str = ""
    kafka_sasl_username: str = ""
    kafka_sasl_password: str = ""

    # NATS
    nats_url: str = Field(default="nats://localhost:4222", validation_alias="NATS_URL")
    nats_cluster_id: str = ""
    nats_client_id: str = "concierge"

    # Topics/Queues
    topic_chat_messages: str = "chat.messages"
    topic_location_updates: str = "location.updates"
    topic_transit_updates: str = "transit.updates"
    topic_notifications: str = "notifications"
    topic_analytics_events: str = "analytics.events"
    topic_ai_tasks: str = "ai.tasks"
    topic_media_processing: str = "media.processing"
    topic_webhooks: str = "webhooks"
    topic_dlq: str = "dlq"

    # Retry
    max_retries: int = 3
    retry_delay_seconds: int = 60
    retry_exponential_backoff: bool = True
    retry_max_delay_seconds: int = 3600

    # Dead letter queue
    dlq_enabled: bool = True
    dlq_max_size: int = 10000
    dlq_ttl_days: int = 7

    # Consumer
    consumer_concurrency: int = 4
    consumer_prefetch: int = 10
    consumer_ack_timeout: int = 300

    # Producer
    producer_batch_size: int = 100
    producer_linger_ms: int = 10
    producer_compression: str = "snappy"
    producer_acks: str = "all"