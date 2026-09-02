"""
Task Scheduler
Manages cron-like scheduled tasks using APScheduler.
"""
import logging
from typing import Any, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages scheduled background tasks."""

    def __init__(self):
        self._scheduler = AsyncIOScheduler()
        self._jobs: dict[str, Any] = {}

    def start(self) -> None:
        """Start the scheduler."""
        self._scheduler.start()
        logger.info("Task scheduler started with %d jobs", len(self._jobs))

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self._scheduler.shutdown(wait=True)
        logger.info("Task scheduler shutdown")

    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        cron_expression: str,
        args: tuple | None = None,
        kwargs: dict | None = None,
    ) -> None:
        """Add a cron-style scheduled job."""
        trigger = CronTrigger.from_crontab(cron_expression)
        job = self._scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            args=args or (),
            kwargs=kwargs or {},
            replace_existing=True,
        )
        self._jobs[job_id] = job
        logger.info("Added cron job '%s' with schedule '%s'", job_id, cron_expression)

    def add_interval_job(
        self,
        func: Callable,
        job_id: str,
        minutes: int = 0,
        hours: int = 0,
        args: tuple | None = None,
        kwargs: dict | None = None,
    ) -> None:
        """Add an interval-based scheduled job."""
        trigger = IntervalTrigger(minutes=minutes, hours=hours)
        job = self._scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            args=args or (),
            kwargs=kwargs or {},
            replace_existing=True,
        )
        self._jobs[job_id] = job
        logger.info("Added interval job '%s' every %dm %dh", job_id, minutes, hours)

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job."""
        if job_id in self._jobs:
            self._scheduler.remove_job(job_id)
            del self._jobs[job_id]
            logger.info("Removed scheduled job '%s'", job_id)
            return True
        return False

    def get_jobs(self) -> list[dict[str, Any]]:
        """Get all scheduled jobs."""
        return [
            {
                "id": job.id,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
            for job in self._scheduler.get_jobs()
        ]
