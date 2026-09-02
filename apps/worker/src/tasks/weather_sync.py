"""
Weather Data Sync Background Tasks

Handles synchronization of weather forecasts, alerts, and historical data
from Open-Meteo and other weather APIs.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from ai_smart_city_concierge.domain.repositories.weather_repository import WeatherRepository
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.infrastructure.external_apis.open_meteo_client import OpenMeteoClient

logger = logging.getLogger(__name__)


@dataclass
class WeatherSyncTask:
    """Task for weather data synchronization."""
    location_id: str
    coordinates: Coordinates
    sync_type: str  # 'current', 'forecast', 'hourly', 'daily', 'alerts', 'historical'
    priority: int = 0
    force_refresh: bool = False


class WeatherSyncTask:
    """
    Background task for synchronizing weather data from weather APIs.
    """

    def __init__(
        self,
        weather_client: OpenMeteoClient,
        weather_repository: WeatherRepository,
        max_concurrent: int = 4,
        forecast_sync_interval_hours: int = 6,
        alerts_sync_interval_minutes: int = 15,
        historical_sync_interval_days: int = 1,
    ):
        self.weather_client = weather_client
        self.weather_repository = weather_repository
        self.max_concurrent = max_concurrent
        self.forecast_sync_interval_hours = forecast_sync_interval_hours
        self.alerts_sync_interval_minutes = alerts_sync_interval_minutes
        self.historical_sync_interval_days = historical_sync_interval_days
        self._queue: asyncio.Queue[WeatherSyncTask] = asyncio.Queue()
        self._running = False
        self._worker_tasks: list[asyncio.Task] = []
        self._scheduled_tasks: dict[str, asyncio.Task] = {}
        self._tracked_locations: dict[str, Coordinates] = {}

    async def start(self) -> None:
        """Start the weather sync workers and scheduled tasks."""
        if self._running:
            return

        self._running = True
        logger.info("Starting weather sync workers")

        # Start workers
        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker(f"weather-sync-worker-{i}"))
            self._worker_tasks.append(task)

        # Start scheduled sync tasks for tracked locations
        await self._start_scheduled_syncs()

    async def stop(self) -> None:
        """Stop the weather sync workers and scheduled tasks."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping weather sync workers")

        # Cancel scheduled tasks
        for task in self._scheduled_tasks.values():
            task.cancel()
        await asyncio.gather(*self._scheduled_tasks.values(), return_exceptions=True)
        self._scheduled_tasks.clear()

        # Stop workers
        await self._queue.join()

        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def enqueue(self, task: WeatherSyncTask) -> None:
        """Add a weather sync task to the queue."""
        await self._queue.put(task)

    async def enqueue_batch(self, tasks: list[WeatherSyncTask]) -> None:
        """Add multiple weather sync tasks to the queue."""
        for task in tasks:
            await self._queue.put(task)

    async def _worker(self, worker_name: str) -> None:
        """Worker coroutine that processes weather sync tasks."""
        logger.info(f"{worker_name} started")

        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)

                try:
                    await self._process_task(task)
                except Exception as e:
                    logger.error(f"{worker_name} error processing task {task.location_id}: {e}")
                finally:
                    self._queue.task_done()

            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{worker_name} unexpected error: {e}")
                await asyncio.sleep(1)

        logger.info(f"{worker_name} stopped")

    async def _start_scheduled_syncs(self) -> None:
        """Start scheduled sync tasks for all tracked locations."""
        for location_id, coordinates in self._tracked_locations.items():
            # Schedule forecast sync
            forecast_task = asyncio.create_task(
                self._scheduled_forecast_sync(location_id, coordinates)
            )
            self._scheduled_tasks[f"forecast-{location_id}"] = forecast_task

            # Schedule alerts sync
            alerts_task = asyncio.create_task(
                self._scheduled_alerts_sync(location_id, coordinates)
            )
            self._scheduled_tasks[f"alerts-{location_id}"] = alerts_task

            # Schedule historical sync
            historical_task = asyncio.create_task(
                self._scheduled_historical_sync(location_id, coordinates)
            )
            self._scheduled_tasks[f"historical-{location_id}"] = historical_task

        logger.info(f"Started scheduled weather syncs for {len(self._tracked_locations)} locations")

    async def _scheduled_forecast_sync(self, location_id: str, coordinates: Coordinates) -> None:
        """Periodically sync forecast data for a location."""
        while self._running:
            try:
                await self.enqueue(WeatherSyncTask(
                    location_id=location_id,
                    coordinates=coordinates,
                    sync_type="forecast",
                    priority=0,
                ))
                logger.debug(f"Scheduled forecast sync for location {location_id}")
            except Exception as e:
                logger.error(f"Error scheduling forecast sync for {location_id}: {e}")

            await asyncio.sleep(self.forecast_sync_interval_hours * 3600)

    async def _scheduled_alerts_sync(self, location_id: str, coordinates: Coordinates) -> None:
        """Periodically sync weather alerts for a location."""
        while self._running:
            try:
                await self.enqueue(WeatherSyncTask(
                    location_id=location_id,
                    coordinates=coordinates,
                    sync_type="alerts",
                    priority=1,
                ))
            except Exception as e:
                logger.error(f"Error scheduling alerts sync for {location_id}: {e}")

            await asyncio.sleep(self.alerts_sync_interval_minutes * 60)

    async def _scheduled_historical_sync(self, location_id: str, coordinates: Coordinates) -> None:
        """Periodically sync historical weather data for a location."""
        while self._running:
            try:
                await self.enqueue(WeatherSyncTask(
                    location_id=location_id,
                    coordinates=coordinates,
                    sync_type="historical",
                    priority=0,
                ))
                logger.debug(f"Scheduled historical sync for location {location_id}")
            except Exception as e:
                logger.error(f"Error scheduling historical sync for {location_id}: {e}")

            await asyncio.sleep(self.historical_sync_interval_days * 86400)

    async def _process_task(self, task: WeatherSyncTask) -> None:
        """Process a single weather sync task."""
        logger.debug(f"Syncing weather data for location {task.location_id} ({task.sync_type})")

        if task.sync_type == "current":
            await self._sync_current_weather(task.location_id, task.coordinates, task.force_refresh)
        elif task.sync_type == "forecast":
            await self._sync_forecast(task.location_id, task.coordinates, task.force_refresh)
        elif task.sync_type == "hourly":
            await self._sync_hourly_forecast(task.location_id, task.coordinates, task.force_refresh)
        elif task.sync_type == "daily":
            await self._sync_daily_forecast(task.location_id, task.coordinates, task.force_refresh)
        elif task.sync_type == "alerts":
            await self._sync_alerts(task.location_id, task.coordinates, task.force_refresh)
        elif task.sync_type == "historical":
            await self._sync_historical(task.location_id, task.coordinates, task.force_refresh)
        else:
            logger.warning(f"Unknown sync type: {task.sync_type}")

    async def _sync_current_weather(
        self,
        location_id: str,
        coordinates: Coordinates,
        force_refresh: bool = False,
    ) -> None:
        """Sync current weather conditions."""
        try:
            if not force_refresh:
                last_sync = await self.weather_repository.get_last_current_sync(location_id)
                if last_sync and (datetime.utcnow() - last_sync).total_seconds() < 3600:  # 1 hour
                    return

            current = await self.weather_client.get_current_weather(
                coordinates.latitude,
                coordinates.longitude,
            )

            if current:
                await self.weather_repository.upsert_current_weather(location_id, current)
                await self.weather_repository.update_last_current_sync(location_id, datetime.utcnow())
                logger.debug(f"Synced current weather for {location_id}")

        except Exception as e:
            logger.error(f"Failed to sync current weather for {location_id}: {e}")

    async def _sync_forecast(
        self,
        location_id: str,
        coordinates: Coordinates,
        force_refresh: bool = False,
    ) -> None:
        """Sync full forecast (hourly + daily)."""
        await asyncio.gather(
            self._sync_hourly_forecast(location_id, coordinates, force_refresh),
            self._sync_daily_forecast(location_id, coordinates, force_refresh),
            return_exceptions=True,
        )

    async def _sync_hourly_forecast(
        self,
        location_id: str,
        coordinates: Coordinates,
        force_refresh: bool = False,
    ) -> None:
        """Sync hourly forecast data."""
        try:
            if not force_refresh:
                last_sync = await self.weather_repository.get_last_hourly_sync(location_id)
                if last_sync and (datetime.utcnow() - last_sync).total_seconds() < self.forecast_sync_interval_hours * 3600:
                    return

            hourly = await self.weather_client.get_hourly_forecast(
                coordinates.latitude,
                coordinates.longitude,
                days=7,
            )

            if hourly:
                await self.weather_repository.upsert_hourly_forecast(location_id, hourly)
                await self.weather_repository.update_last_hourly_sync(location_id, datetime.utcnow())
                logger.debug(f"Synced hourly forecast for {location_id} ({len(hourly)} entries)")

        except Exception as e:
            logger.error(f"Failed to sync hourly forecast for {location_id}: {e}")

    async def _sync_daily_forecast(
        self,
        location_id: str,
        coordinates: Coordinates,
        force_refresh: bool = False,
    ) -> None:
        """Sync daily forecast data."""
        try:
            if not force_refresh:
                last_sync = await self.weather_repository.get_last_daily_sync(location_id)
                if last_sync and (datetime.utcnow() - last_sync).total_seconds() < self.forecast_sync_interval_hours * 3600:
                    return

            daily = await self.weather_client.get_daily_forecast(
                coordinates.latitude,
                coordinates.longitude,
                days=7,
            )

            if daily:
                await self.weather_repository.upsert_daily_forecast(location_id, daily)
                await self.weather_repository.update_last_daily_sync(location_id, datetime.utcnow())
                logger.debug(f"Synced daily forecast for {location_id} ({len(daily)} entries)")

        except Exception as e:
            logger.error(f"Failed to sync daily forecast for {location_id}: {e}")

    async def _sync_alerts(
        self,
        location_id: str,
        coordinates: Coordinates,
        force_refresh: bool = False,
    ) -> None:
        """Sync weather alerts."""
        try:
            if not force_refresh:
                last_sync = await self.weather_repository.get_last_alerts_sync(location_id)
                if last_sync and (datetime.utcnow() - last_sync).total_seconds() < self.alerts_sync_interval_minutes * 60:
                    return

            alerts = await self.weather_client.get_weather_alerts(
                coordinates.latitude,
                coordinates.longitude,
            )

            if alerts:
                await self.weather_repository.upsert_weather_alerts(location_id, alerts)
                await self.weather_repository.update_last_alerts_sync(location_id, datetime.utcnow())
                logger.debug(f"Synced {len(alerts)} weather alerts for {location_id}")

        except Exception as e:
            logger.error(f"Failed to sync weather alerts for {location_id}: {e}")

    async def _sync_historical(
        self,
        location_id: str,
        coordinates: Coordinates,
        force_refresh: bool = False,
    ) -> None:
        """Sync historical weather data."""
        try:
            if not force_refresh:
                last_sync = await self.weather_repository.get_last_historical_sync(location_id)
                if last_sync and (datetime.utcnow() - last_sync).total_seconds() < self.historical_sync_interval_days * 86400:
                    return

            # Get historical data for the past 30 days
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=30)

            historical = await self.weather_client.get_historical_weather(
                coordinates.latitude,
                coordinates.longitude,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            if historical:
                await self.weather_repository.upsert_historical_weather(location_id, historical)
                await self.weather_repository.update_last_historical_sync(location_id, datetime.utcnow())
                logger.debug(f"Synced historical weather for {location_id} ({len(historical)} entries)")

        except Exception as e:
            logger.error(f"Failed to sync historical weather for {location_id}: {e}")

    # High-level methods

    def track_location(self, location_id: str, coordinates: Coordinates) -> None:
        """Add a location to be tracked for weather updates."""
        self._tracked_locations[location_id] = coordinates

        # If already running, start scheduled tasks for this location
        if self._running:
            forecast_task = asyncio.create_task(
                self._scheduled_forecast_sync(location_id, coordinates)
            )
            self._scheduled_tasks[f"forecast-{location_id}"] = forecast_task

            alerts_task = asyncio.create_task(
                self._scheduled_alerts_sync(location_id, coordinates)
            )
            self._scheduled_tasks[f"alerts-{location_id}"] = alerts_task

            historical_task = asyncio.create_task(
                self._scheduled_historical_sync(location_id, coordinates)
            )
            self._scheduled_tasks[f"historical-{location_id}"] = historical_task

    def untrack_location(self, location_id: str) -> None:
        """Remove a location from tracking."""
        self._tracked_locations.pop(location_id, None)

        # Cancel scheduled tasks for this location
        for key in [f"forecast-{location_id}", f"alerts-{location_id}", f"historical-{location_id}"]:
            task = self._scheduled_tasks.pop(key, None)
            if task:
                task.cancel()

    async def sync_location(
        self,
        location_id: str,
        coordinates: Coordinates,
        sync_types: list[str] = None,
    ) -> None:
        """Enqueue sync tasks for a specific location."""
        if sync_types is None:
            sync_types = ["current", "forecast", "alerts"]

        tasks = [
            WeatherSyncTask(
                location_id=location_id,
                coordinates=coordinates,
                sync_type=stype,
                priority=1,
            )
            for stype in sync_types
        ]

        await self.enqueue_batch(tasks)

    async def sync_all_locations(self, sync_types: list[str] = None) -> int:
        """Enqueue sync for all tracked locations. Returns count queued."""
        if sync_types is None:
            sync_types = ["current", "forecast", "alerts"]

        count = 0
        for location_id, coordinates in self._tracked_locations.items():
            tasks = [
                WeatherSyncTask(
                    location_id=location_id,
                    coordinates=coordinates,
                    sync_type=stype,
                    priority=0,
                )
                for stype in sync_types
            ]
            await self.enqueue_batch(tasks)
            count += 1

        logger.info(f"Queued weather sync for {count} locations")
        return count

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def is_running(self) -> bool:
        """Check if workers are running."""
        return self._running

    def get_tracked_locations(self) -> dict[str, Coordinates]:
        """Get all tracked locations."""
        return self._tracked_locations.copy()
