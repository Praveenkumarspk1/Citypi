"""
Application Ports - Event Publisher interface
"""
from abc import ABC, abstractmethod

from ...domain.events.domain_events import DomainEvent


class EventPublisher(ABC):
    """Event publisher port for domain events"""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event"""
        pass

    @abstractmethod
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple domain events"""
        pass
