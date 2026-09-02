"""
Dead Letter Queue Handler
Processes failed events that exceeded retry limits.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from ai_smart_city_concierge.infrastructure.config.redis import get_redis_client, RedisKeys

logger = logging.getLogger(__name__)


class DeadLetterHandler:
    """Handles events that failed processing after max retries."""

    async def handle_failed_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        error: str,
        retry_count: int = 0,
    ) -> None:
        """Send a failed event to the dead letter queue."""
        client = get_redis_client()
        dead_letter_data = {
            "event_type": event_type,
            "payload": str(payload),
            "error": error,
            "retry_count": str(retry_count),
            "failed_at": datetime.utcnow().isoformat(),
        }
        await client.xadd(RedisKeys.TASK_DEAD_LETTER, dead_letter_data)
        logger.warning(
            "Event %s moved to dead letter queue after %d retries: %s",
            event_type,
            retry_count,
            error,
        )

    async def get_dead_letters(self, count: int = 100) -> list[dict[str, Any]]:
        """Retrieve dead letter events for inspection."""
        client = get_redis_client()
        entries = await client.xrange(RedisKeys.TASK_DEAD_LETTER, count=count)
        result = []
        for entry_id, data in entries:
            result.append({"id": entry_id, **data})
        return result

    async def retry_dead_letter(self, entry_id: str) -> bool:
        """Retry a specific dead letter event."""
        client = get_redis_client()
        entries = await client.xrange(RedisKeys.TASK_DEAD_LETTER)
        for entry_id_key, data in entries:
            if entry_id_key.decode() if isinstance(entry_id_key, bytes) else entry_id_key == entry_id:
                # Re-enqueue to task queue
                await client.xadd(RedisKeys.TASK_QUEUE, data)
                # Remove from DLQ
                await client.xdel(RedisKeys.TASK_DEAD_LETTER, entry_id)
                logger.info("Dead letter %s re-enqueued for retry", entry_id)
                return True
        return False

    async def purge_dead_letters(self, older_than_hours: int = 168) -> int:
        """Purge dead letter events older than specified hours."""
        client = get_redis_client()
        entries = await client.xrange(RedisKeys.TASK_DEAD_LETTER)
        purged = 0
        cutoff = datetime.utcnow().timestamp() - (older_than_hours * 3600)
        for entry_id, data in entries:
            failed_at = data.get(b"failed_at", b"")
            if failed_at:
                try:
                    failed_time = datetime.fromisoformat(failed_at.decode()).timestamp()
                    if failed_time < cutoff:
                        await client.xdel(RedisKeys.TASK_DEAD_LETTER, entry_id)
                        purged += 1
                except (ValueError, AttributeError):
                    continue
        logger.info("Purged %d dead letter events older than %d hours", purged, older_than_hours)
        return purged
