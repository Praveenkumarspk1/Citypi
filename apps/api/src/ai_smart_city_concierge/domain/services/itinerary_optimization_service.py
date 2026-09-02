"""
Itinerary Optimization Service - TSP, constraints, scheduling
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID

from ..entities.poi import POI
from ..value_objects.coordinates import Coordinates
from ..value_objects.opening_hours import OpeningHours
from ..value_objects.time_range import TimeRange
from ..value_objects.transport_mode import TransportModeType


class OptimizationObjective(StrEnum):
    """Optimization objectives"""
    MINIMIZE_TRAVEL_TIME = "minimize_travel_time"
    MINIMIZE_TOTAL_DISTANCE = "minimize_total_distance"
    MAXIMIZE_VISITS = "maximize_visits"
    MAXIMIZE_RATING = "maximize_rating"
    BALANCE_ACTIVITIES = "balance_activities"
    MINIMIZE_COST = "minimize_cost"
    MINIMIZE_CO2 = "minimize_co2"
    MAXIMIZE_ENJOYMENT = "maximize_enjoyment"


class ConstraintType(StrEnum):
    """Constraint types"""
    TIME_WINDOW = "time_window"  # POI must be visited within time window
    OPENING_HOURS = "opening_hours"  # POI must be open during visit
    MAX_DAILY_DURATION = "max_daily_duration"  # Max hours per day
    MAX_DAILY_DISTANCE = "max_daily_distance"  # Max km per day
    REQUIRED_POI = "required_poi"  # Must include this POI
    EXCLUDED_POI = "excluded_poi"  # Must not include this POI
    PREFERRED_ORDER = "preferred_order"  # POI A before POI B
    TRANSPORT_MODE = "transport_mode"  # Preferred/required transport
    BUDGET = "budget"  # Max total cost
    ACCESSIBILITY = "accessibility"  # Wheelchair accessible only
    MEAL_TIMES = "meal_times"  # Lunch/dinner at specific times
    BREAK_TIMES = "break_times"  # Required breaks


@dataclass(frozen=True)
class OptimizationConstraint:
    """Optimization constraint"""
    type: ConstraintType
    parameters: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0  # Hard constraint if weight >= 1000
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "parameters": self.parameters,
            "weight": self.weight,
            "description": self.description,
        }


@dataclass(frozen=True)
class VisitRequest:
    """Request to visit a POI"""
    poi_id: UUID
    duration_minutes: int = 60
    preferred_time: TimeRange | None = None
    priority: int = 1  # 1-10, higher = more important
    is_required: bool = False
    transport_mode: TransportModeType | None = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "poi_id": str(self.poi_id),
            "duration_minutes": self.duration_minutes,
            "preferred_time": self.preferred_time.to_dict() if self.preferred_time else None,
            "priority": self.priority,
            "is_required": self.is_required,
            "transport_mode": self.transport_mode.value if self.transport_mode else None,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class OptimizationRequest:
    """Itinerary optimization request"""
    visits: list[VisitRequest]
    start_location: Coordinates
    end_location: Coordinates | None = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    days: int = 1
    objectives: list[OptimizationObjective] = field(default_factory=lambda: [OptimizationObjective.BALANCE_ACTIVITIES])
    constraints: list[OptimizationConstraint] = field(default_factory=list)
    transport_modes: list[TransportModeType] = field(default_factory=lambda: [TransportModeType.WALKING, TransportModeType.PUBLIC_TRANSIT_BUS])
    max_walking_distance_m: float = 1000
    include_meal_breaks: bool = True
    meal_preferences: dict[str, Any] = field(default_factory=dict)
    weather_aware: bool = True
    accessibility_required: bool = False

    def to_dict(self) -> dict:
        return {
            "visits": [v.to_dict() for v in self.visits],
            "start_location": self.start_location.to_dict(),
            "end_location": self.end_location.to_dict() if self.end_location else None,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "days": self.days,
            "objectives": [o.value for o in self.objectives],
            "constraints": [c.to_dict() for c in self.constraints],
            "transport_modes": [m.value for m in self.transport_modes],
            "max_walking_distance_m": self.max_walking_distance_m,
            "include_meal_breaks": self.include_meal_breaks,
            "meal_preferences": self.meal_preferences,
            "weather_aware": self.weather_aware,
            "accessibility_required": self.accessibility_required,
        }


@dataclass(frozen=True)
class OptimizedVisit:
    """Optimized visit in the itinerary"""
    visit_request: VisitRequest
    poi: POI
    start_time: datetime
    end_time: datetime
    travel_time_from_previous_minutes: float
    travel_distance_from_previous_km: float
    transport_mode: TransportModeType
    route_polyline: str | None = None
    is_feasible: bool = True
    constraint_violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "visit_request": self.visit_request.to_dict(),
            "poi": self.poi.to_dict() if self.poi else None,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "travel_time_from_previous_minutes": self.travel_time_from_previous_minutes,
            "travel_distance_from_previous_km": self.travel_distance_from_previous_km,
            "transport_mode": self.transport_mode.value,
            "route_polyline": self.route_polyline,
            "is_feasible": self.is_feasible,
            "constraint_violations": self.constraint_violations,
        }


@dataclass(frozen=True)
class OptimizedDay:
    """Optimized day in the itinerary"""
    date: datetime
    visits: list[OptimizedVisit]
    total_travel_time_minutes: float
    total_travel_distance_km: float
    total_visit_time_minutes: int
    total_cost: float
    total_co2_g: float
    start_location: Coordinates
    end_location: Coordinates
    is_feasible: bool = True
    constraint_violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "visits": [v.to_dict() for v in self.visits],
            "total_travel_time_minutes": self.total_travel_time_minutes,
            "total_travel_distance_km": self.total_travel_distance_km,
            "total_visit_time_minutes": self.total_visit_time_minutes,
            "total_cost": self.total_cost,
            "total_co2_g": self.total_co2_g,
            "start_location": self.start_location.to_dict(),
            "end_location": self.end_location.to_dict(),
            "is_feasible": self.is_feasible,
            "constraint_violations": self.constraint_violations,
        }


@dataclass(frozen=True)
class OptimizationResult:
    """Complete optimization result"""
    request: OptimizationRequest
    days: list[OptimizedDay]
    total_score: float
    objective_scores: dict[str, float]
    is_feasible: bool
    constraint_violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    computation_time_ms: float = 0.0
    algorithm_used: str = "genetic_algorithm"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "request": self.request.to_dict(),
            "days": [d.to_dict() for d in self.days],
            "total_score": self.total_score,
            "objective_scores": self.objective_scores,
            "is_feasible": self.is_feasible,
            "constraint_violations": self.constraint_violations,
            "warnings": self.warnings,
            "computation_time_ms": self.computation_time_ms,
            "algorithm_used": self.algorithm_used,
            "metadata": self.metadata,
        }


class ItineraryOptimizationService(ABC):
    """Abstract itinerary optimization service"""

    @abstractmethod
    async def optimize_itinerary(
        self,
        request: OptimizationRequest,
    ) -> OptimizationResult:
        """Optimize itinerary based on requests and constraints"""
        pass

    @abstractmethod
    async def optimize_single_day(
        self,
        visits: list[VisitRequest],
        start_location: Coordinates,
        start_time: datetime,
        end_time: datetime,
        constraints: list[OptimizationConstraint] = None,
    ) -> list[OptimizedVisit]:
        """Optimize a single day's visits"""
        pass

    @abstractmethod
    async def reoptimize_after_change(
        self,
        current_itinerary: OptimizationResult,
        change: dict[str, Any],  # added/removed/modified visit
    ) -> OptimizationResult:
        """Re-optimize after a change"""
        pass

    @abstractmethod
    async def suggest_additions(
        self,
        current_itinerary: OptimizationResult,
        candidate_pois: list[POI],
        max_additions: int = 3,
    ) -> list[VisitRequest]:
        """Suggest POIs to add to itinerary"""
        pass

    @abstractmethod
    async def calculate_travel_matrix(
        self,
        locations: list[Coordinates],
        modes: list[TransportModeType],
    ) -> dict[tuple[int, int], dict[str, float]]:
        """Calculate travel time/distance matrix between locations"""
        pass

    @abstractmethod
    async def check_feasibility(
        self,
        visits: list[OptimizedVisit],
        constraints: list[OptimizationConstraint],
    ) -> tuple[bool, list[str]]:
        """Check if a sequence of visits is feasible"""
        pass

    @abstractmethod
    async def score_itinerary(
        self,
        itinerary: OptimizationResult,
        objectives: list[OptimizationObjective],
    ) -> dict[str, float]:
        """Score an itinerary against objectives"""
        pass


class ItineraryOptimizationServiceImpl(ItineraryOptimizationService):
    """Default implementation using genetic algorithm / OR-Tools"""

    def __init__(
        self,
        routing_service=None,
        poi_service=None,
        weather_service=None,
        ortools_available: bool = False,
    ):
        self.routing_service = routing_service
        self.poi_service = poi_service
        self.weather_service = weather_service
        self.ortools_available = ortools_available

    async def optimize_itinerary(
        self,
        request: OptimizationRequest,
    ) -> OptimizationResult:
        """Optimize itinerary using genetic algorithm or OR-Tools"""
        # Placeholder implementation
        # In production, would use:
        # - OR-Tools for VRP/TSP with time windows
        # - Genetic algorithm for multi-objective optimization
        # - Simulated annealing for local search

        # For now, return a simple sequential itinerary
        days = []
        current_time = request.start_time
        current_location = request.start_location

        # Group visits by day (simple round-robin for now)
        visits_per_day = max(1, len(request.visits) // request.days)

        for day_idx in range(request.days):
            day_visits = request.visits[day_idx * visits_per_day:(day_idx + 1) * visits_per_day]
            if not day_visits and day_idx == request.days - 1:
                # Add remaining visits to last day
                day_visits = request.visits[day_idx * visits_per_day:]

            optimized_visits = []
            for visit_req in day_visits:
                # Get POI (placeholder)
                poi = None
                if self.poi_service:
                    poi = await self.poi_service.get_poi_by_id(visit_req.poi_id)

                # Calculate travel from previous location
                travel_time = 0.0
                travel_distance = 0.0
                if poi and hasattr(poi, 'coordinates'):
                    travel_distance = current_location.distance_km_to(poi.coordinates)
                    travel_time = travel_distance / 5.0 * 60  # Walking speed 5 km/h

                visit_start = current_time + timedelta(minutes=travel_time)
                visit_end = visit_start + timedelta(minutes=visit_req.duration_minutes)

                optimized_visit = OptimizedVisit(
                    visit_request=visit_req,
                    poi=poi,
                    start_time=visit_start,
                    end_time=visit_end,
                    travel_time_from_previous_minutes=travel_time,
                    travel_distance_from_previous_km=travel_distance,
                    transport_mode=TransportModeType.WALKING,
                )
                optimized_visits.append(optimized_visit)

                current_time = visit_end
                if poi and hasattr(poi, 'coordinates'):
                    current_location = poi.coordinates

            day = OptimizedDay(
                date=current_time.replace(hour=0, minute=0, second=0, microsecond=0),
                visits=optimized_visits,
                total_travel_time_minutes=sum(v.travel_time_from_previous_minutes for v in optimized_visits),
                total_travel_distance_km=sum(v.travel_distance_from_previous_km for v in optimized_visits),
                total_visit_time_minutes=sum(v.visit_request.duration_minutes for v in optimized_visits),
                total_cost=0.0,
                total_co2_g=0.0,
                start_location=request.start_location,
                end_location=current_location,
            )
            days.append(day)

        return OptimizationResult(
            request=request,
            days=days,
            total_score=0.8,
            objective_scores={obj.value: 0.8 for obj in request.objectives},
            is_feasible=True,
            algorithm_used="sequential_placeholder",
        )

    async def optimize_single_day(
        self,
        visits: list[VisitRequest],
        start_location: Coordinates,
        start_time: datetime,
        end_time: datetime,
        constraints: list[OptimizationConstraint] = None,
    ) -> list[OptimizedVisit]:
        """Optimize a single day's visits"""
        # Placeholder - would use TSP solver with time windows
        return []

    async def reoptimize_after_change(
        self,
        current_itinerary: OptimizationResult,
        change: dict[str, Any],
    ) -> OptimizationResult:
        """Re-optimize after a change"""
        # Placeholder - would do incremental optimization
        return current_itinerary

    async def suggest_additions(
        self,
        current_itinerary: OptimizationResult,
        candidate_pois: list[POI],
        max_additions: int = 3,
    ) -> list[VisitRequest]:
        """Suggest POIs to add to itinerary"""
        # Placeholder - would score candidates based on fit
        return []

    async def calculate_travel_matrix(
        self,
        locations: list[Coordinates],
        modes: list[TransportModeType],
    ) -> dict[tuple[int, int], dict[str, float]]:
        """Calculate travel time/distance matrix between locations"""
        matrix = {}
        for i, loc1 in enumerate(locations):
            for j, loc2 in enumerate(locations):
                if i != j:
                    distance = loc1.distance_km_to(loc2)
                    # Use first mode for estimation
                    mode = modes[0] if modes else TransportModeType.WALKING
                    transport_mode = TransportModes.by_type(mode)
                    if transport_mode:
                        time_min = transport_mode.estimate_time(distance)
                    else:
                        time_min = distance / 5.0 * 60
                    matrix[(i, j)] = {
                        "distance_km": distance,
                        "time_minutes": time_min,
                    }
        return matrix

    async def check_feasibility(
        self,
        visits: list[OptimizedVisit],
        constraints: list[OptimizationConstraint],
    ) -> tuple[bool, list[str]]:
        """Check if a sequence of visits is feasible"""
        violations = []

        for constraint in constraints or []:
            if constraint.type == ConstraintType.OPENING_HOURS:
                for visit in visits:
                    if visit.poi and visit.poi.opening_hours:
                        oh = OpeningHours.from_dict(visit.poi.opening_hours)
                        if not oh.is_open_at(visit.start_time):
                            violations.append(f"POI {visit.poi.name} is closed at {visit.start_time}")

            elif constraint.type == ConstraintType.MAX_DAILY_DURATION:
                max_minutes = constraint.parameters.get("max_minutes", 480)
                total_time = sum(v.visit_request.duration_minutes for v in visits) + \
                           sum(v.travel_time_from_previous_minutes for v in visits)
                if total_time > max_minutes:
                    violations.append(f"Daily duration {total_time}min exceeds max {max_minutes}min")

        return len(violations) == 0, violations

    async def score_itinerary(
        self,
        itinerary: OptimizationResult,
        objectives: list[OptimizationObjective],
    ) -> dict[str, float]:
        """Score an itinerary against objectives"""
        scores = {}

        for obj in objectives:
            if obj == OptimizationObjective.MINIMIZE_TRAVEL_TIME:
                total_travel = sum(d.total_travel_time_minutes for d in itinerary.days)
                scores[obj.value] = max(0, 1 - total_travel / 480)  # Normalize to 8 hours

            elif obj == OptimizationObjective.MAXIMIZE_VISITS:
                total_visits = sum(len(d.visits) for d in itinerary.days)
                scores[obj.value] = min(1, total_visits / 10)  # Normalize to 10 visits

            elif obj == OptimizationObjective.MAXIMIZE_RATING:
                all_visits = [v for d in itinerary.days for v in d.visits]
                if all_visits:
                    avg_rating = sum(v.poi.rating for v in all_visits if v.poi and v.poi.rating) / len(all_visits)
                    scores[obj.value] = avg_rating / 5.0
                else:
                    scores[obj.value] = 0

            elif obj == OptimizationObjective.MINIMIZE_COST:
                total_cost = sum(d.total_cost for d in itinerary.days)
                scores[obj.value] = max(0, 1 - total_cost / 100)  # Normalize to $100

            else:
                scores[obj.value] = 0.5  # Default

        return scores


# Import at bottom to avoid circular imports
from ..value_objects.transport_mode import TransportModes
