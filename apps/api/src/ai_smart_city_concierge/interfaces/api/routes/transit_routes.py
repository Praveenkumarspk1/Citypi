"""
Transit API Routes
"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ....application.use_cases.transit_use_cases import (
    GetRealtimeRequest,
    GetRoutesRequest,
    GetScheduleRequest,
    GetStopsRequest,
    TransitUseCases,
)
from ....domain.entities.transit import TransitMode
from ....domain.repositories.base import PaginatedResult, PaginationParams
from ....domain.value_objects.coordinates import Coordinates
from ....infrastructure.config.dependencies import get_transit_use_cases

router = APIRouter(prefix="/transit", tags=["Transit"])


# Request/Response Models
class CoordinatesModel(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class TransitRouteResponse(BaseModel):
    id: str
    agency_id: str
    short_name: str
    long_name: str
    description: str | None
    mode: TransitMode
    color: str | None
    text_color: str | None
    url: str | None


class TransitStopResponse(BaseModel):
    id: str
    code: str | None
    name: str
    description: str | None
    latitude: float
    longitude: float
    zone_id: str | None
    url: str | None
    location_type: int
    parent_station: str | None
    wheelchair_boarding: int
    platform_code: str | None


class TransitTripResponse(BaseModel):
    id: str
    route_id: str
    service_id: str
    trip_headsign: str | None
    trip_short_name: str | None
    direction_id: int
    block_id: str | None
    shape_id: str | None
    wheelchair_accessible: int
    bikes_allowed: int


class ScheduleItemResponse(BaseModel):
    trip_id: str
    route_id: str
    route_short_name: str
    route_long_name: str
    departure_time: str
    arrival_time: str
    direction_id: int
    headsign: str | None


class RealtimeArrivalResponse(BaseModel):
    trip_id: str
    route_id: str
    route_short_name: str
    route_long_name: str
    predicted_departure: str
    scheduled_departure: str
    delay_seconds: int
    direction_id: int
    headsign: str | None
    vehicle_id: str | None


class AlertResponse(BaseModel):
    id: str
    cause: str
    effect: str
    url: str | None
    header_text: str | None
    description_text: str | None
    severity_level: int
    active_period_start: str
    active_period_end: str | None
    informed_entity: list[dict]


class VehiclePositionResponse(BaseModel):
    vehicle_id: str
    trip_id: str
    route_id: str
    latitude: float
    longitude: float
    bearing: float
    speed: float
    timestamp: str
    congestion_level: int
    occupancy_status: int


class TripPlanResponse(BaseModel):
    itineraries: list[dict]


@router.get("/routes/{route_id}", response_model=TransitRouteResponse)
async def get_route(
    route_id: str,
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Get transit route by ID"""
    route = await use_cases.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


@router.get("/routes", response_model=PaginatedResult[TransitRouteResponse])
async def get_routes(
    agency_id: str | None = Query(None),
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius_meters: float | None = Query(None, gt=0, le=50000),
    mode: TransitMode | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Get transit routes"""
    coordinates = None
    if latitude is not None and longitude is not None:
        coordinates = Coordinates(latitude=latitude, longitude=longitude)

    request = GetRoutesRequest(
        agency_id=agency_id,
        coordinates=coordinates,
        radius_meters=radius_meters,
        mode=mode,
        pagination=PaginationParams(page=page, page_size=page_size),
    )

    return await use_cases.get_routes(request)


@router.get("/stops/{stop_id}", response_model=TransitStopResponse)
async def get_stop(
    stop_id: str,
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Get transit stop by ID"""
    stop = await use_cases.get_stop(stop_id)
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop


@router.get("/stops/nearby", response_model=list[TransitStopResponse])
async def get_stops_nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_meters: float = Query(500, gt=0, le=5000),
    modes: list[TransitMode] | None = Query(None),
    accessible_only: bool = Query(False),
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Get transit stops near coordinates"""
    request = GetStopsRequest(
        coordinates=Coordinates(latitude=latitude, longitude=longitude),
        radius_meters=radius_meters,
        modes=modes,
        accessible_only=accessible_only,
    )

    return await use_cases.get_stops_nearby(request)


@router.get("/stops/{stop_id}/routes", response_model=list[TransitRouteResponse])
async def get_routes_for_stop(
    stop_id: str,
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Get routes serving a stop"""
    return await use_cases.get_routes_for_stop(stop_id)


@router.get("/routes/{route_id}/trips", response_model=list[TransitTripResponse])
async def get_trips_for_route(
    route_id: str,
    date: date | None = Query(None),
    direction_id: int | None = Query(None, ge=0, le=1),
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Get trips for a route"""
    return await use_cases.get_trips_for_route(route_id, date, direction_id)


@router.get("/stops/{stop_id}/schedule", response_model=list[ScheduleItemResponse])
async def get_schedule(
    stop_id: str,
    date: date = Query(...),
    route_ids: list[str] | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Get schedule for a stop"""
    request = GetScheduleRequest(
        stop_id=stop_id,
        date=date,
        route_ids=route_ids,
        limit=limit,
    )

    return await use_cases.get_schedule(request)


@router.get("/stops/{stop_id}/realtime", response_model=list[RealtimeArrivalResponse])
async def get_realtime_arrivals(
    stop_id: str,
    route_ids: list[str] | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Get real-time arrivals for a stop"""
    request = GetRealtimeRequest(
        stop_id=stop_id,
        route_ids=route_ids,
        limit=limit,
    )

    return await use_cases.get_realtime_arrivals(request)


@router.get("/alerts", response_model=list[AlertResponse])
async def get_alerts(
    route_ids: list[str] | None = Query(None),
    stop_ids: list[str] | None = Query(None),
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Get transit alerts"""
    return await use_cases.get_alerts(route_ids, stop_ids)


@router.get("/vehicles", response_model=list[VehiclePositionResponse])
async def get_vehicle_positions(
    route_ids: list[str] | None = Query(None),
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Get real-time vehicle positions"""
    return await use_cases.get_vehicle_positions(route_ids)


@router.post("/plan-trip", response_model=TripPlanResponse)
async def plan_trip(
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lng: float = Query(..., ge=-180, le=180),
    dest_lat: float = Query(..., ge=-90, le=90),
    dest_lng: float = Query(..., ge=-180, le=180),
    departure_time: datetime | None = Query(None),
    arrival_time: datetime | None = Query(None),
    modes: list[TransitMode] | None = Query(None),
    max_walk_distance: float = Query(1000, ge=0, le=5000),
    wheelchair_accessible: bool = Query(False),
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Plan a transit trip"""
    origin = Coordinates(latitude=origin_lat, longitude=origin_lng)
    destination = Coordinates(latitude=dest_lat, longitude=dest_lng)

    itineraries = await use_cases.plan_trip(
        origin=origin,
        destination=destination,
        departure_time=departure_time,
        arrival_time=arrival_time,
        modes=modes,
        max_walk_distance=max_walk_distance,
        wheelchair_accessible=wheelchair_accessible,
    )

    return TripPlanResponse(itineraries=itineraries)


@router.get("/stops/{stop_id}/next-departures", response_model=list[RealtimeArrivalResponse])
async def get_next_departures(
    stop_id: str,
    route_ids: list[str] | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Get next departures from a stop"""
    return await use_cases.get_next_departures(stop_id, route_ids, limit)


@router.get("/routes/search", response_model=PaginatedResult[TransitRouteResponse])
async def search_routes(
    query: str = Query(..., min_length=1),
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius_meters: float | None = Query(None, gt=0, le=50000),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: TransitUseCases = Depends(get_transit_use_cases),
):
    """Search transit routes"""
    coordinates = None
    if latitude is not None and longitude is not None:
        coordinates = Coordinates(latitude=latitude, longitude=longitude)

    return await use_cases.search_routes(
        query=query,
        coordinates=coordinates,
        radius_meters=radius_meters,
        pagination=PaginationParams(page=page, page_size=page_size),
    )
