"""
Scheduled Cron Jobs

Defines scheduled tasks for the worker service.
"""

import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import croniter

logger = logging.getLogger(__name__)


class ScheduleType(StrEnum):
    """Types of schedules."""
    CRON = "cron"
    INTERVAL = "interval"
    ONCE = "once"


@dataclass
class ScheduledJob:
    """A scheduled job definition."""
    name: str
    func: Callable
    schedule_type: ScheduleType
    cron_expression: str | None = None
    interval_seconds: int | None = None
    run_once_at: datetime | None = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    enabled: bool = True
    max_runs: int | None = None
    run_count: int = 0
    last_run: datetime | None = None
    next_run: datetime | None = None

    def __post_init__(self):
        self._calculate_next_run()

    def _calculate_next_run(self) -> None:
        """Calculate the next run time."""
        now = datetime.utcnow()

        if self.schedule_type == ScheduleType.CRON and self.cron_expression:
            try:
                cron = croniter.croniter(self.cron_expression, now)
                self.next_run = cron.get_next(datetime)
            except Exception as e:
                logger.error(f"Invalid cron expression for job {self.name}: {e}")
                self.next_run = None

        elif self.schedule_type == ScheduleType.INTERVAL and self.interval_seconds:
            if self.last_run:
                self.next_run = self.last_run + timedelta(seconds=self.interval_seconds)
            else:
                self.next_run = now

        elif self.schedule_type == ScheduleType.ONCE and self.run_once_at:
            if self.run_once_at > now:
                self.next_run = self.run_once_at
            else:
                self.next_run = None  # Already passed

    def should_run(self) -> bool:
        """Check if the job should run now."""
        if not self.enabled:
            return False

        if self.max_runs and self.run_count >= self.max_runs:
            return False

        if not self.next_run:
            return False

        return datetime.utcnow() >= self.next_run

    def mark_run(self) -> None:
        """Mark the job as run."""
        self.last_run = datetime.utcnow()
        self.run_count += 1
        self._calculate_next_run()


class Scheduler:
    """
    Cron-like scheduler for background jobs.
    """

    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval_seconds = check_interval_seconds
        self._jobs: dict[str, ScheduledJob] = {}
        self._running = False
        self._scheduler_task: asyncio.Task | None = None

    def add_job(
        self,
        name: str,
        func: Callable,
        cron: str | None = None,
        interval_seconds: int | None = None,
        run_once_at: datetime | None = None,
        args: tuple = (),
        kwargs: dict = None,
        enabled: bool = True,
        max_runs: int | None = None,
    ) -> ScheduledJob:
        """Add a scheduled job."""
        if cron:
            schedule_type = ScheduleType.CRON
        elif interval_seconds:
            schedule_type = ScheduleType.INTERVAL
        elif run_once_at:
            schedule_type = ScheduleType.ONCE
        else:
            raise ValueError("Must specify cron, interval_seconds, or run_once_at")

        job = ScheduledJob(
            name=name,
            func=func,
            schedule_type=schedule_type,
            cron_expression=cron,
            interval_seconds=interval_seconds,
            run_once_at=run_once_at,
            args=args,
            kwargs=kwargs or {},
            enabled=enabled,
            max_runs=max_runs,
        )

        self._jobs[name] = job
        logger.info(f"Added scheduled job: {name} ({schedule_type.value})")
        return job

    def remove_job(self, name: str) -> bool:
        """Remove a scheduled job."""
        if name in self._jobs:
            del self._jobs[name]
            logger.info(f"Removed scheduled job: {name}")
            return True
        return False

    def enable_job(self, name: str) -> bool:
        """Enable a scheduled job."""
        if name in self._jobs:
            self._jobs[name].enabled = True
            return True
        return False

    def disable_job(self, name: str) -> bool:
        """Disable a scheduled job."""
        if name in self._jobs:
            self._jobs[name].enabled = False
            return True
        return False

    def get_job(self, name: str) -> ScheduledJob | None:
        """Get a job by name."""
        return self._jobs.get(name)

    def list_jobs(self) -> list[ScheduledJob]:
        """List all scheduled jobs."""
        return list(self._jobs.values())

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return

        self._running = True
        logger.info("Starting scheduler")
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())

    async def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping scheduler")

        if self._scheduler_task:
            self._scheduler_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._scheduler_task

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_run_jobs()
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")

            await asyncio.sleep(self.check_interval_seconds)

    async def _check_and_run_jobs(self) -> None:
        """Check all jobs and run those that are due."""
        for job in self._jobs.values():
            if job.should_run():
                await self._run_job(job)

    async def _run_job(self, job: ScheduledJob) -> None:
        """Run a single job."""
        logger.info(f"Running scheduled job: {job.name}")

        try:
            if asyncio.iscoroutinefunction(job.func):
                await job.func(*job.args, **job.kwargs)
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, job.func, *job.args, **job.kwargs)

            job.mark_run()
            logger.debug(f"Completed scheduled job: {job.name}")

        except Exception as e:
            logger.error(f"Scheduled job {job.name} failed: {e}")
            job.mark_run()  # Still mark as run to avoid retry loops

    async def run_job_now(self, name: str) -> bool:
        """Manually trigger a job to run immediately."""
        job = self._jobs.get(name)
        if not job:
            return False

        await self._run_job(job)
        return True

    def get_next_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get upcoming job runs."""
        jobs_with_next = [
            {
                "name": job.name,
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "enabled": job.enabled,
                "run_count": job.run_count,
                "max_runs": job.max_runs,
            }
            for job in self._jobs.values()
            if job.next_run
        ]

        jobs_with_next.sort(key=lambda x: x["next_run"] or "")
        return jobs_with_next[:limit]


# Predefined schedule expressions
class Schedules:
    """Common schedule expressions."""

    # Every minute
    EVERY_MINUTE = "* * * * *"

    # Every 5 minutes
    EVERY_5_MINUTES = "*/5 * * * *"

    # Every 15 minutes
    EVERY_15_MINUTES = "*/15 * * * *"

    # Every 30 minutes
    EVERY_30_MINUTES = "*/30 * * * *"

    # Every hour at minute 0
    HOURLY = "0 * * * *"

    # Every hour at minute 30
    HOURLY_HALF = "30 * * * *"

    # Daily at midnight UTC
    DAILY_MIDNIGHT = "0 0 * * *"

    # Daily at 6 AM UTC
    DAILY_6AM = "0 6 * * *"

    # Daily at noon UTC
    DAILY_NOON = "0 12 * * *"

    # Weekly on Monday at midnight
    WEEKLY_MONDAY = "0 0 * * 1"

    # Monthly on 1st at midnight
    MONTHLY_FIRST = "0 0 1 * *"

    # Every 6 hours
    EVERY_6_HOURS = "0 */6 * * *"

    # Every 12 hours
    EVERY_12_HOURS = "0 */12 * * *"

    # Business hours (9 AM - 5 PM, weekdays)
    BUSINESS_HOURS = "0 9-17 * * 1-5"


# Import timedelta
from datetime import timedelta
