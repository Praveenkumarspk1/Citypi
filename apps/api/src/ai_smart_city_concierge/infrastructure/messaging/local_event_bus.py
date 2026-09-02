"""
Local In-Memory Event Bus
"""
import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from ...domain.events.domain_events import DomainEvent, EventType

logger = logging.getLogger(__name__)


@dataclass
class EventSubscription:
    """Event subscription"""
    id: UUID = field(default_factory=uuid4)
    event_type: EventType
    handler: Callable
    filter_func: Callable[[DomainEvent], bool] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class LocalEventBus:
    """In-memory event bus for domain events"""

    def __init__(self):
        self._subscriptions: dict[EventType, list[EventSubscription]] = defaultdict(list)
        self._global_subscriptions: list[EventSubscription] = []
        self._event_history: list[DomainEvent] = []
        self._max_history = 10000
        self._running = False
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the event bus worker"""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_queue())
        logger.info("LocalEventBus started")

    async def stop(self) -> None:
        """Stop the event bus worker"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("LocalEventBus stopped")

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable,
        filter_func: Callable[[DomainEvent], bool] | None = None,
    ) -> UUID:
        """Subscribe to an event type"""
        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
            filter_func=filter_func,
        )
        self._subscriptions[event_type].append(subscription)
        logger.debug(f"Subscribed to {event_type.value}: {subscription.id}")
        return subscription.id

    def subscribe_all(
        self,
        handler: Callable,
        filter_func: Callable[[DomainEvent], bool] | None = None,
    ) -> UUID:
        """Subscribe to all events"""
        subscription = EventSubscription(
            event_type=EventType.USER_CREATED,  # Placeholder, not used for global
            handler=handler,
            filter_func=filter_func,
        )
        self._global_subscriptions.append(subscription)
        logger.debug(f"Subscribed to all events: {subscription.id}")
        return subscription.id

    def unsubscribe(self, subscription_id: UUID) -> bool:
        """Unsubscribe by subscription ID"""
        # Check specific subscriptions
        for event_type, subs in self._subscriptions.items():
            for i, sub in enumerate(subs):
                if sub.id == subscription_id:
                    subs.pop(i)
                    logger.debug(f"Unsubscribed {subscription_id} from {event_type.value}")
                    return True

        # Check global subscriptions
        for i, sub in enumerate(self._global_subscriptions):
            if sub.id == subscription_id:
                self._global_subscriptions.pop(i)
                logger.debug(f"Unsubscribed {subscription_id} from all events")
                return True

        return False

    async def publish(self, event: DomainEvent) -> None:
        """Publish event to queue for async processing"""
        await self._queue.put(event)

    async def publish_sync(self, event: DomainEvent) -> None:
        """Publish event synchronously (immediate delivery)"""
        await self._deliver_event(event)

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple events"""
        for event in events:
            await self._queue.put(event)

    async def _process_queue(self) -> None:
        """Process event queue"""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._deliver_event(event)
                self._queue.task_done()
            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event queue: {e}")

    async def _deliver_event(self, event: DomainEvent) -> None:
        """Deliver event to subscribers"""
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        # Deliver to specific subscribers
        subscriptions = self._subscriptions.get(event.event_type, [])
        for subscription in subscriptions:
            try:
                # Check filter
                if subscription.filter_func and not subscription.filter_func(event):
                    continue

                # Call handler
                if asyncio.iscoroutinefunction(subscription.handler):
                    await subscription.handler(event)
                else:
                    subscription.handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type.value}: {e}")

        # Deliver to global subscribers
        for subscription in self._global_subscriptions:
            try:
                if subscription.filter_func and not subscription.filter_func(event):
                    continue

                if asyncio.iscoroutinefunction(subscription.handler):
                    await subscription.handler(event)
                else:
                    subscription.handler(event)
            except Exception as e:
                logger.error(f"Error in global event handler: {e}")

    def get_history(
        self,
        event_type: EventType | None = None,
        limit: int = 100,
    ) -> list[DomainEvent]:
        """Get event history"""
        history = self._event_history
        if event_type:
            history = [e for e in history if e.event_type == event_type]
        return history[-limit:]

    def get_subscription_count(self, event_type: EventType | None = None) -> int:
        """Get subscription count"""
        if event_type:
            return len(self._subscriptions.get(event_type, []))
        return sum(len(subs) for subs in self._subscriptions.values()) + len(self._global_subscriptions)

    async def replay_events(
        self,
        event_type: EventType,
        handler: Callable,
        since: datetime | None = None,
    ) -> int:
        """Replay historical events to a handler"""
        count = 0
        for event in self._event_history:
            if event.event_type != event_type:
                continue
            if since and event.timestamp < since:
                continue

            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                count += 1
            except Exception as e:
                logger.error(f"Error replaying event: {e}")

        return count


# Global instance
local_event_bus = LocalEventBus()
