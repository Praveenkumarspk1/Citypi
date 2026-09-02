"""
Itinerary Generation Background Tasks

Handles AI-powered itinerary generation and optimization using LLMs
and domain services.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from ai_smart_city_concierge.domain.aggregates.itinerary_aggregate import ItineraryAggregate
from ai_smart_city_concierge.domain.repositories.itinerary_repository import ItineraryRepository
from ai_smart_city_concierge.domain.repositories.poi_repository import POIRepository
from ai_smart_city_concierge.domain.services.itinerary_optimization_service import (
    ItineraryOptimizationService,
)
from ai_smart_city_concierge.domain.services.poi_service import POIService
from ai_smart_city_concierge.domain.services.transit_service import TransitService
from ai_smart_city_concierge.domain.services.weather_service import WeatherService
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.infrastructure.external_apis.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


@dataclass
class ItineraryGenerationTask:
    """Task for itinerary generation."""
    user_id: str
    request_id: str
    title: str
    description: str
    start_date: str
    end_date: str
    base_location: Coordinates
    base_address: str
    city: str
    country: str
    interests: list[str]
    budget_level: str
    pace: str
    accessibility_needs: list[str]
    dietary_restrictions: list[str]
    transport_preferences: list[str]
    priority: int = 0


class ItineraryGenerationTask:
    """
    Background task for generating AI-powered itineraries.
    """

    def __init__(
        self,
        gemini_client: GeminiClient,
        itinerary_optimization_service: ItineraryOptimizationService,
        poi_service: POIService,
        transit_service: TransitService,
        weather_service: WeatherService,
        itinerary_repository: ItineraryRepository,
        poi_repository: POIRepository,
        max_concurrent: int = 2,
    ):
        self.gemini_client = gemini_client
        self.itinerary_optimization_service = itinerary_optimization_service
        self.poi_service = poi_service
        self.transit_service = transit_service
        self.weather_service = weather_service
        self.itinerary_repository = itinerary_repository
        self.poi_repository = poi_repository
        self.max_concurrent = max_concurrent
        self._queue: asyncio.Queue[ItineraryGenerationTask] = asyncio.Queue()
        self._running = False
        self._worker_tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the itinerary generation workers."""
        if self._running:
            return

        self._running = True
        logger.info("Starting itinerary generation workers")

        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker(f"itinerary-generation-worker-{i}"))
            self._worker_tasks.append(task)

    async def stop(self) -> None:
        """Stop the itinerary generation workers."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping itinerary generation workers")

        await self._queue.join()

        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def enqueue(self, task: ItineraryGenerationTask) -> None:
        """Add an itinerary generation task to the queue."""
        await self._queue.put(task)

    async def _worker(self, worker_name: str) -> None:
        """Worker coroutine that processes itinerary generation tasks."""
        logger.info(f"{worker_name} started")

        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)

                try:
                    await self._process_task(task)
                except Exception as e:
                    logger.error(f"{worker_name} error processing task {task.request_id}: {e}")
                    await self._mark_request_failed(task.request_id, str(e))
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

    async def _process_task(self, task: ItineraryGenerationTask) -> None:
        """Process a single itinerary generation task."""
        logger.info(f"Generating itinerary for request {task.request_id}")

        # Create initial itinerary aggregate
        itinerary = ItineraryAggregate.create(
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            start_date=task.start_date,
            end_date=task.end_date,
            base_location=task.base_location,
            base_address=task.base_address,
            city=task.city,
            country=task.country,
            interests=task.interests,
            budget_level=task.budget_level,
            pace=task.pace,
            accessibility_needs=task.accessibility_needs,
            dietary_restrictions=task.dietary_restrictions,
            transport_preferences=task.transport_preferences,
        )

        # Save initial draft
        await self.itinerary_repository.save(itinerary)

        try:
            # Step 1: Find relevant POIs based on interests and location
            pois = await self._find_relevant_pois(task)
            logger.debug(f"Found {len(pois)} relevant POIs for itinerary {task.request_id}")

            # Step 2: Get weather forecast for the dates
            weather = await self._get_weather_forecast(task)

            # Step 3: Generate day-by-day plan using LLM
            daily_plans = await self._generate_daily_plans(task, pois, weather)

            # Step 4: Optimize the itinerary (TSP, transit routing, etc.)
            optimized_itinerary = await self._optimize_itinerary(
                itinerary, daily_plans, task
            )

            # Step 5: Add transit routes between locations
            await self._add_transit_routes(optimized_itinerary, task)

            # Step 6: Calculate costs and finalize
            await self._finalize_itinerary(optimized_itinerary, task)

            # Save completed itinerary
            await self.itinerary_repository.save(optimized_itinerary)

            logger.info(f"Completed itinerary generation for request {task.request_id}")

        except Exception as e:
            logger.error(f"Failed to generate itinerary for {task.request_id}: {e}")
            await self._mark_request_failed(task.request_id, str(e))
            raise

    async def _find_relevant_pois(self, task: ItineraryGenerationTask) -> list[Any]:
        """Find POIs relevant to the itinerary request."""
        all_pois = []

        for interest in task.interests:
            # Search POIs by category/interest near base location
            pois = await self.poi_service.search_pois(
                query=interest,
                location=task.base_location,
                radius_km=20,
                limit=50,
            )
            all_pois.extend(pois)

        # Deduplicate by ID
        seen = set()
        unique_pois = []
        for poi in all_pois:
            if poi.id not in seen:
                seen.add(poi.id)
                unique_pois.append(poi)

        # Sort by rating and popularity
        unique_pois.sort(key=lambda p: (p.rating * 0.7 + p.popularity_score * 0.3), reverse=True)

        return unique_pois[:100]  # Limit to top 100

    async def _get_weather_forecast(self, task: ItineraryGenerationTask) -> dict[str, Any]:
        """Get weather forecast for the itinerary dates."""
        try:
            start = datetime.fromisoformat(task.start_date)
            end = datetime.fromisoformat(task.end_date)
            days = (end - start).days + 1

            forecast = await self.weather_service.get_forecast(
                task.base_location,
                days=days,
            )

            return forecast
        except Exception as e:
            logger.warning(f"Failed to get weather forecast: {e}")
            return {}

    async def _generate_daily_plans(
        self,
        task: ItineraryGenerationTask,
        pois: list[Any],
        weather: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate day-by-day plans using LLM."""
        # Prepare context for LLM
        poi_summaries = [
            {
                "id": poi.id,
                "name": poi.name,
                "category": poi.category,
                "subcategory": poi.subcategory,
                "rating": poi.rating,
                "coordinates": {
                    "lat": poi.coordinates.latitude,
                    "lng": poi.coordinates.longitude,
                } if poi.coordinates else None,
                "opening_hours": str(poi.opening_hours) if poi.opening_hours else None,
                "tags": poi.tags,
            }
            for poi in pois[:50]  # Limit context size
        ]

        prompt = self._build_itinerary_prompt(task, poi_summaries, weather)

        # Generate using Gemini
        response = await self.gemini_client.generate_text(prompt)

        # Parse response into daily plans
        daily_plans = self._parse_itinerary_response(response, task)

        return daily_plans

    def _build_itinerary_prompt(
        self,
        task: ItineraryGenerationTask,
        pois: list[dict[str, Any]],
        weather: dict[str, Any],
    ) -> str:
        """Build the prompt for itinerary generation."""
        start = datetime.fromisoformat(task.start_date)
        end = datetime.fromisoformat(task.end_date)
        num_days = (end - start).days + 1

        poi_list = "\n".join([
            f"- {p['name']} ({p['category']}/{p.get('subcategory', '')}): "
            f"Rating {p['rating']}, Tags: {', '.join(p.get('tags', [])[:5])}"
            for p in pois
        ])

        weather_summary = ""
        if weather and weather.get("daily"):
            for i, day in enumerate(weather["daily"][:num_days]):
                date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
                weather_summary += f"\n{date}: {day.get('condition', 'Unknown')}, "
                weather_summary += f"{day.get('temp_min', '?')}-{day.get('temp_max', '?')}°C, "
                weather_summary += f"Precip: {day.get('precipitation_probability', 0)}%"

        return f"""
You are an expert travel planner creating a {num_days}-day itinerary for {task.city}, {task.country}.

USER PREFERENCES:
- Interests: {', '.join(task.interests)}
- Budget: {task.budget_level}
- Pace: {task.pace}
- Accessibility needs: {', '.join(task.accessibility_needs) if task.accessibility_needs else 'None'}
- Dietary restrictions: {', '.join(task.dietary_restrictions) if task.dietary_restrictions else 'None'}
- Preferred transport: {', '.join(task.transport_preferences)}

BASE LOCATION: {task.base_address} ({task.base_location.latitude}, {task.base_location.longitude})

WEATHER FORECAST:{weather_summary}

AVAILABLE POIs:
{poi_list}

Create a detailed day-by-day itinerary with:
1. Morning, afternoon, evening activities for each day
2. Specific POIs from the list above (use their IDs)
3. Estimated durations
4. Meal suggestions matching dietary restrictions
5. Transit/walking between locations
6. Weather-appropriate alternatives

Return as JSON with this structure:
{{
  "days": [
    {{
      "day_number": 1,
      "date": "YYYY-MM-DD",
      "title": "Day title",
      "items": [
        {{
          "type": "poi_visit|meal|activity|transit|rest",
          "poi_id": "poi_id_or_null",
          "title": "Activity title",
          "description": "Details",
          "start_time": "HH:MM",
          "end_time": "HH:MM",
          "duration_minutes": 120,
          "coordinates": {{"lat": 0, "lng": 0}},
          "transport_mode": "walking|transit|driving",
          "estimated_cost": 0,
          "notes": "Any special notes"
        }}
      ]
    }}
  ]
}}
"""

    def _parse_itinerary_response(
        self,
        response: str,
        task: ItineraryGenerationTask,
    ) -> list[dict[str, Any]]:
        """Parse LLM response into daily plans."""
        import json

        try:
            # Extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            return data.get("days", [])
        except Exception as e:
            logger.error(f"Failed to parse itinerary response: {e}")
            # Return empty plans - will use fallback
            return []

    async def _optimize_itinerary(
        self,
        itinerary: ItineraryAggregate,
        daily_plans: list[dict[str, Any]],
        task: ItineraryGenerationTask,
    ) -> ItineraryAggregate:
        """Optimize the itinerary using the optimization service."""
        # Convert daily plans to itinerary items
        for day_plan in daily_plans:
            day_number = day_plan.get("day_number", 1)
            day_plan.get("date", task.start_date)

            for item in day_plan.get("items", []):
                itinerary.add_item(
                    day_number=day_number,
                    item_type=item.get("type", "activity"),
                    poi_id=item.get("poi_id"),
                    title=item.get("title", ""),
                    description=item.get("description"),
                    start_time=item.get("start_time", "09:00"),
                    end_time=item.get("end_time", "10:00"),
                    duration_minutes=item.get("duration_minutes", 60),
                    coordinates=item.get("coordinates"),
                    transport_mode=item.get("transport_mode"),
                    estimated_cost=item.get("estimated_cost", 0),
                    notes=item.get("notes"),
                )

        # Run optimization
        optimized = await self.itinerary_optimization_service.optimize(
            itinerary,
            constraints={
                "pace": task.pace,
                "budget_level": task.budget_level,
                "transport_preferences": task.transport_preferences,
            }
        )

        return optimized

    async def _add_transit_routes(
        self,
        itinerary: ItineraryAggregate,
        task: ItineraryGenerationTask,
    ) -> None:
        """Add transit routes between consecutive items."""
        for day in itinerary.days:
            items = day.items
            for i in range(len(items) - 1):
                current = items[i]
                next_item = items[i + 1]

                if current.coordinates and next_item.coordinates:
                    # Get transit route
                    route = await self.transit_service.plan_route(
                        origin=current.coordinates,
                        destination=next_item.coordinates,
                        departure_time=current.end_time,
                        preferences={
                            "modes": task.transport_preferences,
                            "wheelchair_accessible": "wheelchair" in task.accessibility_needs,
                        }
                    )

                    if route:
                        # Add transit item between activities
                        # Insert transit item (simplified - would need proper insertion)
                        pass

    async def _finalize_itinerary(
        self,
        itinerary: ItineraryAggregate,
        task: ItineraryGenerationTask,
    ) -> None:
        """Finalize itinerary with costs, validation, etc."""
        # Calculate total estimated cost
        total_cost = 0
        for day in itinerary.days:
            for item in day.items:
                total_cost += item.estimated_cost or 0

        itinerary.total_estimated_cost = total_cost
        itinerary.currency = "USD"  # Would be based on location
        itinerary.status = "active"
        itinerary.completed_at = datetime.utcnow().isoformat()

    async def _mark_request_failed(self, request_id: str, error: str) -> None:
        """Mark a generation request as failed."""
        # This would update a request tracking table
        logger.error(f"Itinerary generation request {request_id} failed: {error}")

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def is_running(self) -> bool:
        """Check if workers are running."""
        return self._running
