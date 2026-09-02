"""
Outbox Pattern for Transactional Event Publishing
"""
import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.events.domain_events import DomainEvent, EventType

logger = logging.getLogger(__name__)


class OutboxStatus(StrEnum):
    """Outbox message status"""
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass
class OutboxMessage:
    """Outbox message"""
    id: UUID = field(default_factory=uuid4)
    event_type: EventType
    aggregate_id: UUID
    aggregate_type: str
    payload: dict
    metadata: dict = field(default_factory=dict)
    status: OutboxStatus = OutboxStatus.PENDING
    retry_count: int = 0
    max_retries: int = 5
    created_at: datetime = field(default_factory=datetime.utcnow)
    published_at: datetime | None = None
    error_message: str | None = None


class OutboxRepository:
    """Repository for outbox messages (uses SQLAlchemy)"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, message: OutboxMessage) -> OutboxMessage:
        """Save outbox message"""
        # This would use a SQLAlchemy model for the outbox table
        # For now, we'll use a simplified approach
        # In production, you'd have a proper OutboxModel
        pass

    async def get_pending(self, limit: int = 100) -> list[OutboxMessage]:
        """Get pending messages"""
        # Query for pending messages
        pass

    async def mark_published(self, message_id: UUID) -> None:
        """Mark message as published"""
        pass

    async def mark_failed(self, message_id: UUID, error: str) -> None:
        """Mark message as failed"""
        pass

    async def increment_retry(self, message_id: UUID) -> None:
        """Increment retry count"""
        pass


class OutboxPattern:
    """Outbox pattern implementation for reliable event publishing"""

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        event_publisher: Callable[[DomainEvent], Any],
        poll_interval: float = 5.0,
        batch_size: int = 100,
        max_retries: int = 5,
    ):
        self.session_factory = session_factory
        self.event_publisher = event_publisher
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.max_retries = max_retries
        self._running = False
        self._worker_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the outbox processor"""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_loop())
        logger.info("OutboxPattern processor started")

    async def stop(self) -> None:
        """Stop the outbox processor"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("OutboxPattern processor stopped")

    async def save_event(self, event: DomainEvent) -> OutboxMessage:
        """Save event to outbox within transaction"""
        async with self.session_factory():
            message = OutboxMessage(
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                payload=event.payload,
                metadata=event.metadata,
                max_retries=self.max_retries,
            )

            # Save to database (would use actual model)
            # await self._save_to_db(session, message)
            # await session.commit()

            return message

    async def _process_loop(self) -> None:
        """Main processing loop"""
        while self._running:
            try:
                await self._process_batch()
            except Exception as e:
                logger.error(f"Error in outbox processing loop: {e}")

            await asyncio.sleep(self.poll_interval)

    async def _process_batch(self) -> None:
        """Process a batch of pending messages"""
        async with self.session_factory() as session:
            # Get pending messages
            # messages = await self._get_pending_from_db(session, self.batch_size)
            messages = []  # Placeholder

            for message in messages:
                await self._process_message(session, message)

            await session.commit()

    async def _process_message(self, session: AsyncSession, message: OutboxMessage) -> None:
        """Process a single outbox message"""
        try:
            # Reconstruct domain event
            event = DomainEvent(
                id=message.id,
                event_type=message.event_type,
                aggregate_id=message.aggregate_id,
                aggregate_type=message.aggregate_type,
                payload=message.payload,
                metadata=message.metadata,
                timestamp=message.created_at,
            )

            # Publish event
            await self.event_publisher(event)

            # Mark as published
            message.status = OutboxStatus.PUBLISHED
            message.published_at = datetime.utcnow()

            # Update in database
            # await self._update_in_db(session, message)

            logger.debug(f"Published outbox message {message.id}")

        except Exception as e:
            message.retry_count += 1
            message.error_message = str(e)

            if message.retry_count >= message.max_retries:
                message.status = OutboxStatus.FAILED
                logger.error(f"Outbox message {message.id} failed after {message.max_retries} retries: {e}")
            else:
                logger.warning(f"Outbox message {message.id} retry {message.retry_count}/{message.max_retries}: {e}")

            # Update in database
            # await self._update_in_db(session, message)


# SQLAlchemy model for outbox table (to be added to models)
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from ...infrastructure.persistence.sqlalchemy.models.base import Base

class OutboxModel(Base):
    __tablename__ = "outbox_messages"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    aggregate_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    aggregate_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)  # JSON
    metadata = Column(Text, nullable=False)  # JSON
    status = Column(SQLEnum(OutboxStatus), nullable=False, default=OutboxStatus.PENDING, index=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=5)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index('ix_outbox_status_created', 'status', 'created_at'),
    )
"""
