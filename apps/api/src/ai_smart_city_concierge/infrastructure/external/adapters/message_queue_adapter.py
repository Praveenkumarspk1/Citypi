"""
Message Queue Adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ....application.ports.external_services import MessageQueuePort


@dataclass
class Job:
    """Job data"""
    id: str
    queue: str
    data: dict[str, Any]
    priority: int
    created_at: datetime
    scheduled_at: datetime | None = None
    attempts: int = 0
    max_attempts: int = 3


class BaseMessageQueueAdapter(MessageQueuePort, ABC):
    """Base message queue adapter"""

    @abstractmethod
    async def _enqueue_request(
        self,
        queue: str,
        job_data: dict[str, Any],
        priority: int,
        delay_seconds: int,
    ) -> str:
        """Enqueue job request"""
        pass

    @abstractmethod
    async def _dequeue_request(self, queue: str) -> Job | None:
        """Dequeue job request"""
        pass

    @abstractmethod
    async def _get_queue_size_request(self, queue: str) -> int:
        """Get queue size request"""
        pass

    @abstractmethod
    async def _schedule_job_request(
        self,
        queue: str,
        job_data: dict[str, Any],
        run_at: datetime,
    ) -> str:
        """Schedule job request"""
        pass

    async def enqueue(
        self,
        queue: str,
        job_data: dict[str, Any],
        priority: int = 0,
        delay_seconds: int = 0,
    ) -> str:
        """Enqueue a job"""
        return await self._enqueue_request(queue, job_data, priority, delay_seconds)

    async def dequeue(self, queue: str) -> dict[str, Any] | None:
        """Dequeue a job"""
        job = await self._dequeue_request(queue)
        if job:
            return {
                "id": job.id,
                "queue": job.queue,
                "data": job.data,
                "priority": job.priority,
                "created_at": job.created_at.isoformat(),
                "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
                "attempts": job.attempts,
                "max_attempts": job.max_attempts,
            }
        return None

    async def get_queue_size(self, queue: str) -> int:
        """Get queue size"""
        return await self._get_queue_size_request(queue)

    async def schedule_job(
        self,
        queue: str,
        job_data: dict[str, Any],
        run_at: datetime,
    ) -> str:
        """Schedule a job for future execution"""
        return await self._schedule_job_request(queue, job_data, run_at)


class RedisMessageQueueAdapter(BaseMessageQueueAdapter):
    """Redis-based message queue adapter (using Redis lists and sorted sets)"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as redis
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )
        return self._client

    def _queue_key(self, queue: str) -> str:
        return f"queue:{queue}"

    def _scheduled_key(self, queue: str) -> str:
        return f"queue:{queue}:scheduled"

    def _job_key(self, job_id: str) -> str:
        return f"job:{job_id}"

    async def _enqueue_request(
        self,
        queue: str,
        job_data: dict[str, Any],
        priority: int,
        delay_seconds: int,
    ) -> str:
        client = await self._get_client()
        import json
        import time
        import uuid

        job_id = str(uuid.uuid4())
        now = time.time()
        scheduled_at = now + delay_seconds

        job = {
            "id": job_id,
            "queue": queue,
            "data": job_data,
            "priority": priority,
            "created_at": now,
            "scheduled_at": scheduled_at,
            "attempts": 0,
            "max_attempts": 3,
        }

        # Store job data
        await client.set(self._job_key(job_id), json.dumps(job))

        if delay_seconds > 0:
            # Add to scheduled queue (sorted set with score = scheduled_at)
            await client.zadd(self._scheduled_key(queue), {job_id: scheduled_at})
        else:
            # Add to main queue (list, with priority handling)
            # Use LPUSH for high priority, RPUSH for normal
            if priority > 0:
                await client.lpush(self._queue_key(queue), job_id)
            else:
                await client.rpush(self._queue_key(queue), job_id)

        return job_id

    async def _dequeue_request(self, queue: str) -> Job | None:
        client = await self._get_client()
        import json
        import time

        # First, check scheduled jobs that are ready
        now = time.time()
        ready_jobs = await client.zrangebyscore(
            self._scheduled_key(queue),
            0,
            now,
            start=0,
            num=10,
        )

        for job_id in ready_jobs:
            # Move from scheduled to main queue
            await client.zrem(self._scheduled_key(queue), job_id)
            job_data = await client.get(self._job_key(job_id))
            if job_data:
                job = json.loads(job_data)
                if job["priority"] > 0:
                    await client.lpush(self._queue_key(queue), job_id)
                else:
                    await client.rpush(self._queue_key(queue), job_id)

        # Dequeue from main queue
        job_id = await client.lpop(self._queue_key(queue))
        if not job_id:
            return None

        job_data = await client.get(self._job_key(job_id))
        if not job_data:
            return None

        job = json.loads(job_data)
        job["attempts"] += 1

        # Update job data
        await client.set(self._job_key(job_id), json.dumps(job))

        return Job(
            id=job["id"],
            queue=job["queue"],
            data=job["data"],
            priority=job["priority"],
            created_at=datetime.fromtimestamp(job["created_at"]),
            scheduled_at=datetime.fromtimestamp(job["scheduled_at"]) if job["scheduled_at"] else None,
            attempts=job["attempts"],
            max_attempts=job["max_attempts"],
        )

    async def _get_queue_size_request(self, queue: str) -> int:
        client = await self._get_client()
        main_size = await client.llen(self._queue_key(queue))
        scheduled_size = await client.zcard(self._scheduled_key(queue))
        return main_size + scheduled_size

    async def _schedule_job_request(
        self,
        queue: str,
        job_data: dict[str, Any],
        run_at: datetime,
    ) -> str:
        delay_seconds = max(0, int(run_at.timestamp() - time.time()))
        return await self._enqueue_request(queue, job_data, 0, delay_seconds)

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


class RabbitMQAdapter(BaseMessageQueueAdapter):
    """RabbitMQ message queue adapter"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        username: str = "guest",
        password: str = "guest",
        virtual_host: str = "/",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        self._connection = None
        self._channel = None

    async def _get_connection(self):
        if self._connection is None:
            import aio_pika
            self._connection = await aio_pika.connect_robust(
                host=self.host,
                port=self.port,
                login=self.username,
                password=self.password,
                virtualhost=self.virtual_host,
            )
        return self._connection

    async def _get_channel(self):
        if self._channel is None:
            connection = await self._get_connection()
            self._channel = await connection.channel()
            await self._channel.set_qos(prefetch_count=10)
        return self._channel

    async def _enqueue_request(
        self,
        queue: str,
        job_data: dict[str, Any],
        priority: int,
        delay_seconds: int,
    ) -> str:
        channel = await self._get_channel()
        import json
        import uuid

        job_id = str(uuid.uuid4())

        # Declare queue
        await channel.declare_queue(queue, durable=True)

        message = aio_pika.Message(
            body=json.dumps({
                "id": job_id,
                "queue": queue,
                "data": job_data,
                "priority": priority,
                "created_at": datetime.utcnow().isoformat(),
                "attempts": 0,
                "max_attempts": 3,
            }).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            priority=priority,
        )

        if delay_seconds > 0:
            # Use delayed message exchange (requires rabbitmq_delayed_message_exchange plugin)
            await channel.default_exchange.publish(
                message,
                routing_key=queue,
                headers={"x-delay": delay_seconds * 1000},
            )
        else:
            await channel.default_exchange.publish(
                message,
                routing_key=queue,
            )

        return job_id

    async def _dequeue_request(self, queue: str) -> Job | None:
        channel = await self._get_channel()
        import json

        # Declare queue
        q = await channel.declare_queue(queue, durable=True)

        # Get message
        message = await q.get(fail=False)
        if not message:
            return None

        async with message.process():
            data = json.loads(message.body.decode())
            return Job(
                id=data["id"],
                queue=data["queue"],
                data=data["data"],
                priority=data["priority"],
                created_at=datetime.fromisoformat(data["created_at"]),
                attempts=data["attempts"],
                max_attempts=data["max_attempts"],
            )

    async def _get_queue_size_request(self, queue: str) -> int:
        channel = await self._get_channel()
        q = await channel.declare_queue(queue, durable=True, passive=True)
        return q.declaration_result.message_count

    async def _schedule_job_request(
        self,
        queue: str,
        job_data: dict[str, Any],
        run_at: datetime,
    ) -> str:
        delay_seconds = max(0, int(run_at.timestamp() - datetime.utcnow().timestamp()))
        return await self._enqueue_request(queue, job_data, 0, delay_seconds)

    async def close(self):
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._channel = None


class InMemoryMessageQueueAdapter(BaseMessageQueueAdapter):
    """In-memory message queue adapter (for development/testing)"""

    def __init__(self):
        self._queues: dict[str, list[Job]] = {}
        self._scheduled: dict[str, list[Job]] = {}

    async def _enqueue_request(
        self,
        queue: str,
        job_data: dict[str, Any],
        priority: int,
        delay_seconds: int,
    ) -> str:
        import time
        import uuid

        job_id = str(uuid.uuid4())
        now = time.time()
        scheduled_at = now + delay_seconds

        job = Job(
            id=job_id,
            queue=queue,
            data=job_data,
            priority=priority,
            created_at=datetime.fromtimestamp(now),
            scheduled_at=datetime.fromtimestamp(scheduled_at) if delay_seconds > 0 else None,
        )

        if queue not in self._queues:
            self._queues[queue] = []
        if queue not in self._scheduled:
            self._scheduled[queue] = []

        if delay_seconds > 0:
            self._scheduled[queue].append(job)
            # Sort by scheduled_at
            self._scheduled[queue].sort(key=lambda j: j.scheduled_at)
        else:
            if priority > 0:
                self._queues[queue].insert(0, job)
            else:
                self._queues[queue].append(job)

        return job_id

    async def _dequeue_request(self, queue: str) -> Job | None:

        # Move scheduled jobs that are ready
        now = datetime.utcnow()
        if queue in self._scheduled:
            ready = [j for j in self._scheduled[queue] if j.scheduled_at and j.scheduled_at <= now]
            for job in ready:
                self._scheduled[queue].remove(job)
                if job.priority > 0:
                    self._queues[queue].insert(0, job)
                else:
                    self._queues[queue].append(job)

        if queue not in self._queues or not self._queues[queue]:
            return None

        job = self._queues[queue].pop(0)
        job.attempts += 1
        return job

    async def _get_queue_size_request(self, queue: str) -> int:
        main = len(self._queues.get(queue, []))
        scheduled = len(self._scheduled.get(queue, []))
        return main + scheduled

    async def _schedule_job_request(
        self,
        queue: str,
        job_data: dict[str, Any],
        run_at: datetime,
    ) -> str:
        delay_seconds = max(0, int(run_at.timestamp() - datetime.utcnow().timestamp()))
        return await self._enqueue_request(queue, job_data, 0, delay_seconds)
