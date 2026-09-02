"""
Task Queue Infrastructure

Redis-based task queue for background job processing using RQ (Redis Queue).
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class TaskStatus(StrEnum):
    """Task status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class TaskPriority(int, Enum):
    """Task priority levels (higher = more urgent)."""
    LOW = 0
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class QueuedTask:
    """A task in the queue."""
    id: str
    task_type: str
    payload: dict[str, Any]
    priority: int = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueuedTask":
        return cls(**data)


class TaskQueue:
    """
    Redis-based task queue with priority support.

    Uses Redis sorted sets for priority queueing and streams for task processing.
    """

    def __init__(
        self,
        redis_client: Redis,
        queue_name: str = "default",
        max_concurrent: int = 10,
        default_timeout: int = 300,
    ):
        self.redis = redis_client
        self.queue_name = queue_name
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout

        # Redis keys
        self._queue_key = f"queue:{queue_name}:tasks"
        self._processing_key = f"queue:{queue_name}:processing"
        self._completed_key = f"queue:{queue_name}:completed"
        self._failed_key = f"queue:{queue_name}:failed"
        self._task_prefix = f"queue:{queue_name}:task:"
        self._lock_prefix = f"queue:{queue_name}:lock:"

        # Lua script for atomic task claiming
        self._claim_script = self.redis.register_script("""
            local task = redis.call('ZPOPMIN', KEYS[1], 1)
            if #task > 0 then
                local task_id = task[1]
                redis.call('HSET', KEYS[2], task_id, ARGV[1])
                redis.call('EXPIRE', KEYS[2], ARGV[2])
                return task_id
            end
            return nil
        """)

    async def enqueue(
        self,
        task_type: str,
        payload: dict[str, Any],
        priority: int = TaskPriority.NORMAL,
        task_id: str | None = None,
        max_retries: int = 3,
        timeout_seconds: int = 300,
    ) -> str:
        """
        Add a task to the queue.

        Returns the task ID.
        """
        import uuid

        if task_id is None:
            task_id = f"{task_type}:{uuid.uuid4().hex[:12]}"

        task = QueuedTask(
            id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
        )

        # Store task data
        await self.redis.hset(
            f"{self._task_prefix}{task_id}",
            mapping=task.to_dict()
        )

        # Add to priority queue (sorted set with negative priority for max-heap)
        await self.redis.zadd(
            self._queue_key,
            {task_id: -priority}
        )

        logger.debug(f"Enqueued task {task_id} ({task_type}) with priority {priority}")
        return task_id

    async def enqueue_batch(
        self,
        tasks: list[dict[str, Any]],
    ) -> list[str]:
        """Enqueue multiple tasks at once."""
        task_ids = []

        pipe = self.redis.pipeline()
        for task_data in tasks:
            task_id = task_data.get("task_id") or f"{task_data['task_type']}:{uuid.uuid4().hex[:12]}"
            task = QueuedTask(
                id=task_id,
                task_type=task_data["task_type"],
                payload=task_data["payload"],
                priority=task_data.get("priority", TaskPriority.NORMAL),
                max_retries=task_data.get("max_retries", 3),
                timeout_seconds=task_data.get("timeout_seconds", 300),
            )

            pipe.hset(f"{self._task_prefix}{task_id}", mapping=task.to_dict())
            pipe.zadd(self._queue_key, {task_id: -task.priority})
            task_ids.append(task_id)

        await pipe.execute()
        logger.info(f"Enqueued batch of {len(task_ids)} tasks")
        return task_ids

    async def dequeue(self, worker_id: str) -> QueuedTask | None:
        """
        Claim the next highest-priority task for processing.

        Returns the task or None if queue is empty.
        """
        # Use Lua script for atomic claim
        task_id = await self._claim_script(
            keys=[self._queue_key, self._processing_key],
            args=[worker_id, self.default_timeout]
        )

        if not task_id:
            return None

        # Get task data
        task_data = await self.redis.hgetall(f"{self._task_prefix}{task_id}")
        if not task_data:
            # Task data missing, clean up
            await self.redis.hdel(self._processing_key, task_id)
            return None

        task = QueuedTask.from_dict(task_data)
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow().isoformat()

        # Update task status
        await self.redis.hset(
            f"{self._task_prefix}{task_id}",
            mapping=task.to_dict()
        )

        logger.debug(f"Worker {worker_id} claimed task {task_id}")
        return task

    async def complete_task(self, task_id: str, result: dict[str, Any] | None = None) -> bool:
        """Mark a task as completed."""
        task_data = await self.redis.hgetall(f"{self._task_prefix}{task_id}")
        if not task_data:
            return False

        task = QueuedTask.from_dict(task_data)
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow().isoformat()

        if result:
            task.payload["result"] = result

        # Move from processing to completed
        pipe = self.redis.pipeline()
        pipe.hdel(self._processing_key, task_id)
        pipe.hset(f"{self._task_prefix}{task_id}", mapping=task.to_dict())
        pipe.zadd(self._completed_key, {task_id: datetime.utcnow().timestamp()})
        pipe.expire(f"{self._task_prefix}{task_id}", 86400)  # Keep for 24h
        await pipe.execute()

        logger.debug(f"Completed task {task_id}")
        return True

    async def fail_task(self, task_id: str, error: str) -> bool:
        """Mark a task as failed, potentially scheduling a retry."""
        task_data = await self.redis.hgetall(f"{self._task_prefix}{task_id}")
        if not task_data:
            return False

        task = QueuedTask.from_dict(task_data)
        task.error = error
        task.retry_count += 1

        if task.retry_count < task.max_retries:
            # Schedule retry with exponential backoff
            task.status = TaskStatus.RETRYING
            delay = min(2 ** task.retry_count * 60, 3600)  # Max 1 hour

            # Re-queue with delay
            await asyncio.sleep(delay)
            task.status = TaskStatus.PENDING
            await self.redis.zadd(self._queue_key, {task_id: -task.priority})
            logger.info(f"Scheduled retry {task.retry_count}/{task.max_retries} for task {task_id} in {delay}s")
        else:
            # Max retries exceeded
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow().isoformat()

            pipe = self.redis.pipeline()
            pipe.hdel(self._processing_key, task_id)
            pipe.hset(f"{self._task_prefix}{task_id}", mapping=task.to_dict())
            pipe.zadd(self._failed_key, {task_id: datetime.utcnow().timestamp()})
            pipe.expire(f"{self._task_prefix}{task_id}", 604800)  # Keep for 7 days
            await pipe.execute()

            logger.error(f"Task {task_id} failed after {task.max_retries} retries: {error}")

        await self.redis.hset(f"{self._task_prefix}{task_id}", mapping=task.to_dict())
        return True

    async def get_task_status(self, task_id: str) -> QueuedTask | None:
        """Get the current status of a task."""
        task_data = await self.redis.hgetall(f"{self._task_prefix}{task_id}")
        if not task_data:
            return None
        return QueuedTask.from_dict(task_data)

    async def get_queue_stats(self) -> dict[str, int]:
        """Get queue statistics."""
        pipe = self.redis.pipeline()
        pipe.zcard(self._queue_key)
        pipe.hlen(self._processing_key)
        pipe.zcard(self._completed_key)
        pipe.zcard(self._failed_key)
        results = await pipe.execute()

        return {
            "pending": results[0],
            "processing": results[1],
            "completed": results[2],
            "failed": results[3],
        }

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        # Remove from queue
        removed = await self.redis.zrem(self._queue_key, task_id)
        if removed:
            # Delete task data
            await self.redis.delete(f"{self._task_prefix}{task_id}")
            logger.info(f"Cancelled task {task_id}")
            return True
        return False

    async def requeue_failed(self, task_id: str) -> bool:
        """Re-queue a failed task for retry."""
        task_data = await self.redis.hgetall(f"{self._task_prefix}{task_id}")
        if not task_data:
            return False

        task = QueuedTask.from_dict(task_data)
        if task.status != TaskStatus.FAILED:
            return False

        # Reset for retry
        task.status = TaskStatus.PENDING
        task.retry_count = 0
        task.error = None
        task.started_at = None
        task.completed_at = None

        pipe = self.redis.pipeline()
        pipe.hset(f"{self._task_prefix}{task_id}", mapping=task.to_dict())
        pipe.zrem(self._failed_key, task_id)
        pipe.zadd(self._queue_key, {task_id: -task.priority})
        await pipe.execute()

        logger.info(f"Re-queued failed task {task_id}")
        return True

    async def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """Clean up old completed/failed tasks."""
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)

        # Get old completed tasks
        old_completed = await self.redis.zrangebyscore(
            self._completed_key, 0, cutoff
        )

        # Get old failed tasks
        old_failed = await self.redis.zrangebyscore(
            self._failed_key, 0, cutoff
        )

        all_old = list(old_completed) + list(old_failed)
        if not all_old:
            return 0

        # Delete task data and remove from sorted sets
        pipe = self.redis.pipeline()
        for task_id in all_old:
            pipe.delete(f"{self._task_prefix}{task_id}")
        pipe.zrem(self._completed_key, *old_completed)
        pipe.zrem(self._failed_key, *old_failed)
        await pipe.execute()

        logger.info(f"Cleaned up {len(all_old)} old tasks")
        return len(all_old)


class TaskWorker:
    """
    Generic task worker that processes tasks from a queue.
    """

    def __init__(
        self,
        queue: TaskQueue,
        worker_id: str,
        handlers: dict[str, Callable],
        max_concurrent: int = 5,
    ):
        self.queue = queue
        self.worker_id = worker_id
        self.handlers = handlers
        self.max_concurrent = max_concurrent
        self._running = False
        self._worker_tasks: list[asyncio.Task] = []
        self._semaphore: asyncio.Semaphore | None = None

    async def start(self) -> None:
        """Start the worker."""
        if self._running:
            return

        self._running = True
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        logger.info(f"Starting worker {self.worker_id}")

        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker_loop(f"{self.worker_id}-{i}"))
            self._worker_tasks.append(task)

    async def stop(self) -> None:
        """Stop the worker."""
        if not self._running:
            return

        self._running = False
        logger.info(f"Stopping worker {self.worker_id}")

        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def _worker_loop(self, loop_id: str) -> None:
        """Main worker loop."""
        logger.info(f"Worker loop {loop_id} started")

        while self._running:
            try:
                async with self._semaphore:
                    task = await self.queue.dequeue(self.worker_id)

                    if not task:
                        await asyncio.sleep(1)
                        continue

                    await self._process_task(task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop {loop_id} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"Worker loop {loop_id} stopped")

    async def _process_task(self, task: QueuedTask) -> None:
        """Process a single task."""
        handler = self.handlers.get(task.task_type)
        if not handler:
            logger.error(f"No handler for task type: {task.task_type}")
            await self.queue.fail_task(task.id, f"No handler for task type: {task.task_type}")
            return

        try:
            logger.debug(f"Processing task {task.id} ({task.task_type})")
            result = await handler(task.payload)
            await self.queue.complete_task(task.id, result)
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            await self.queue.fail_task(task.id, str(e))


# Import uuid for batch enqueue
import uuid
