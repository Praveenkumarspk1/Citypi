"""
Event Publisher Adapter - Wraps LocalEventBus to implement EventPublisher port
"""

from ...application.ports.event_publisher import EventPublisher
from ...domain.events.domain_events import DomainEvent
from ..messaging.local_event_bus import LocalEventBus, local_event_bus


class LocalEventBusAdapter(EventPublisher):
    """Adapter to make LocalEventBus implement EventPublisher port"""

    def __init__(self, event_bus: LocalEventBus = None):
        self._event_bus = event_bus or local_event_bus

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event"""
        await self._event_bus.publish(event)

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple domain events"""
        await self._event_bus.publish_batch(events)
