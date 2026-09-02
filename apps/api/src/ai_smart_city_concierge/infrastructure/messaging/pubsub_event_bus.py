"""
Google Cloud Pub/Sub Event Bus
"""
import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message

from ...domain.events.domain_events import DomainEvent, EventType

logger = logging.getLogger(__name__)


@dataclass
class PubSubSubscription:
    """Pub/Sub subscription"""
    id: UUID = field(default_factory=uuid4)
    event_type: EventType
    handler: Callable
    subscription_path: str
    filter_func: Callable[[DomainEvent], bool] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    future: asyncio.Future | None = None


class PubSubEventBus:
    """Google Cloud Pub/Sub event bus for domain events"""

    def __init__(
        self,
        project_id: str,
        topic_prefix: str = "ai-smart-city-concierge",
        credentials_path: str | None = None,
    ):
        self.project_id = project_id
        self.topic_prefix = topic_prefix

        # Initialize clients
        if credentials_path:
            self._publisher = pubsub_v1.PublisherClient.from_service_account_json(credentials_path)
            self._subscriber = pubsub_v1.SubscriberClient.from_service_account_json(credentials_path)
        else:
            self._publisher = pubsub_v1.PublisherClient()
            self._subscriber = pubsub_v1.SubscriberClient()

        self._topic_cache: dict[str, str] = {}
        self._subscriptions: dict[EventType, PubSubSubscription] = {}
        self._running = False

    def _get_topic_path(self, event_type: EventType) -> str:
        """Get or create topic path for event type"""
        topic_name = f"{self.topic_prefix}.{event_type.value}"

        if topic_name not in self._topic_cache:
            self._topic_cache[topic_name] = self._publisher.topic_path(self.project_id, topic_name)

        return self._topic_cache[topic_name]

    def _get_subscription_path(self, event_type: EventType, subscription_suffix: str = "sub") -> str:
        """Get subscription path"""
        subscription_name = f"{self.topic_prefix}.{event_type.value}.{subscription_suffix}"
        return self._subscriber.subscription_path(self.project_id, subscription_name)

    async def _ensure_topic_exists(self, event_type: EventType) -> None:
        """Ensure topic exists"""
        topic_path = self._get_topic_path(event_type)

        try:
            self._publisher.get_topic(request={"topic": topic_path})
        except Exception:
            # Create topic
            self._publisher.create_topic(request={"name": topic_path})
            logger.info(f"Created Pub/Sub topic: {topic_path}")

    async def start(self) -> None:
        """Start the event bus"""
        self._running = True
        logger.info("PubSubEventBus started")

    async def stop(self) -> None:
        """Stop the event bus and close subscriptions"""
        self._running = False

        for subscription in self._subscriptions.values():
            if subscription.future:
                subscription.future.cancel()
                try:
                    await subscription.future
                except asyncio.CancelledError:
                    pass

        self._subscriptions.clear()
        logger.info("PubSubEventBus stopped")

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable,
        filter_func: Callable[[DomainEvent], bool] | None = None,
        subscription_suffix: str = "sub",
    ) -> UUID:
        """Subscribe to an event type via Pub/Sub"""
        # Ensure topic exists
        asyncio.create_task(self._ensure_topic_exists(event_type))

        subscription_path = self._get_subscription_path(event_type, subscription_suffix)

        # Create subscription if it doesn't exist
        try:
            self._subscriber.get_subscription(request={"subscription": subscription_path})
        except Exception:
            topic_path = self._get_topic_path(event_type)
            self._subscriber.create_subscription(
                request={"name": subscription_path, "topic": topic_path}
            )
            logger.info(f"Created Pub/Sub subscription: {subscription_path}")

        # Create subscription object
        subscription = PubSubSubscription(
            event_type=event_type,
            handler=handler,
            subscription_path=subscription_path,
            filter_func=filter_func,
        )

        # Start listening
        subscription.future = asyncio.create_task(self._listen(subscription))
        self._subscriptions[event_type] = subscription

        logger.debug(f"Subscribed to {event_type.value} via Pub/Sub: {subscription.id}")
        return subscription.id

    async def _listen(self, subscription: PubSubSubscription) -> None:
        """Listen for messages on subscription"""
        def callback(message: Message) -> None:
            try:
                # Parse event
                data = json.loads(message.data.decode("utf-8"))
                event = DomainEvent(**data)

                # Check filter
                if subscription.filter_func and not subscription.filter_func(event):
                    message.ack()
                    return

                # Call handler
                if asyncio.iscoroutinefunction(subscription.handler):
                    asyncio.create_task(subscription.handler(event))
                else:
                    subscription.handler(event)

                message.ack()
            except Exception as e:
                logger.error(f"Error processing Pub/Sub message: {e}")
                message.nack()

        streaming_pull_future = self._subscriber.subscribe(
            subscription.subscription_path,
            callback=callback,
        )

        try:
            await streaming_pull_future
        except asyncio.CancelledError:
            streaming_pull_future.cancel()
            raise
        except Exception as e:
            logger.error(f"Error in Pub/Sub listener: {e}")

    async def publish(self, event: DomainEvent) -> None:
        """Publish event to Pub/Sub"""
        topic_path = self._get_topic_path(event.event_type)

        # Ensure topic exists
        await self._ensure_topic_exists(event.event_type)

        # Serialize event
        data = json.dumps(event.to_dict()).encode("utf-8")

        # Publish
        future = self._publisher.publish(topic_path, data)

        # Wait for publish to complete
        await asyncio.wrap_future(future)

        logger.debug(f"Published event {event.event_type.value} to Pub/Sub")

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple events"""
        for event in events:
            await self.publish(event)

    def unsubscribe(self, event_type: EventType) -> bool:
        """Unsubscribe from event type"""
        if event_type in self._subscriptions:
            subscription = self._subscriptions[event_type]
            if subscription.future:
                subscription.future.cancel()
            del self._subscriptions[event_type]
            logger.debug(f"Unsubscribed from {event_type.value}")
            return True
        return False

    def get_subscription_count(self) -> int:
        """Get active subscription count"""
        return len(self._subscriptions)
