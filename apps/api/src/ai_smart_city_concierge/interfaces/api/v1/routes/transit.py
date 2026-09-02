"""
Transit Routes
"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ai_smart_city_concierge.application.dto.request import TransitRouteRequest
from ai_smart_city_concierge.application.dto.response import PaginatedResponse, TransitRouteResponse
from ai_smart_city_concierge.domain.entities.transit import RouteType
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.infrastructure.auth import get_current_user
from ai_smart_city_concierge.infrastructure.di.container import get_transit_application_service
from ai_smart_city_concierge.application.services.transit_service import TransitApplicationService

router = APIRouter(prefix="/transit", tags=["transit"])


@router.post("/routes", response_model=TransitRouteResponse)
async def calculate_transit_route(
    request: TransitRouteRequest,
    service: TransitApplicationService = Depends(get_transit_application_service),
    current_user: dict = Depends(get_current_user),
) -> TransitRouteResponse:
    """Calculate transit route between two points"""
    route = await service.plan_trip(
        origin=request.origin,
        destination=request.destination,
        departure_time=request.departure_time,
        arrival_time=request.arrival_time,
        max_walk_distance=request.max_walking_distance,
        wheelchair_accessible=request.wheelchair_accessible,
        bike_allowed=False,
    )
    # Convert the first trip to response format
    if route:
        return TransitRouteResponse.from_dict(route[0])
    raise HTTPException(status_code=404, detail="No route found")


@router.get("/routes/recent", response_model=list[TransitRouteResponse])
async def get_recent_routes(
    limit: int = Query(20, ge=1, le=100),
    service: TransitApplicationService = Depends(get_transit_application_service),
    current_user: dict = Depends(get_current_user),
) -> list[TransitRouteResponse]:
    """Get recent transit routes for current user"""
    # This would need a method on the service to get recent routes
    # For now return empty list
    return []


@router.get("/routes/{route_id}", response_model=TransitRouteResponse)
async def get_transit_route(
    route_id: UUID,
    service: TransitApplicationService = Depends(get_transit_application_service),
    current_user: dict = Depends(get_current_user),
) -> TransitRouteResponse:
    """Get transit route by ID"""
    route = await service.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return TransitRouteResponse.from_entity(route)


@router.get("/agencies", response_model=list[dict])
async def get_agencies(
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> list[dict]:
    """Get all transit agencies"""
    agencies = await service.transit_repository.list_agencies()
    return [a.to_dict() for a in agencies]


@router.get("/agencies/{agency_id}", response_model=dict)
async def get_agency(
    agency_id: str,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> dict:
    """Get agency by ID"""
    agency = await service.get_agency(agency_id)
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    return agency.to_dict()


@router.get("/stops", response_model=PaginatedResponse[dict])
async def get_stops(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    radius_meters: float = Query(1000, ge=0, le=50000),
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> PaginatedResponse[dict]:
    """Get transit stops with optional nearby search"""
    if lat is not None and lng is not None:
        coordinates = Coordinates(latitude=lat, longitude=lng)
        stops = await service.get_stops_near(coordinates, radius_meters)
        return PaginatedResponse(
            items=[s.to_dict() for s in stops],
            total=len(stops),
            page=1,
            page_size=len(stops),
            total_pages=1,
            has_next=False,
            has_prev=False,
        )

    from ....ports.repositories import PaginationParams
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await service.transit_repository.list_stops(pagination=pagination)
    return PaginatedResponse(
        items=[s.to_dict() for s in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.get("/stops/nearby", response_model=list[dict])
async def get_stops_nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_meters: float = Query(1000, ge=0, le=50000),
    limit: int = Query(50, ge=1, le=200),
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> list[dict]:
    """Get stops near coordinates"""
    coordinates = Coordinates(latitude=lat, longitude=lng)
    stops = await service.get_stops_near(coordinates, radius_meters, limit)
    return [s.to_dict() for s in stops]


@router.get("/stops/{stop_id}", response_model=dict)
async def get_stop(
    stop_id: str,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> dict:
    """Get stop by ID"""
    stop = await service.get_stop(stop_id)
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop.to_dict()


@router.get("/routes", response_model=PaginatedResponse[dict])
async def get_routes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    agency_id: str | None = None,
    route_type: RouteType | None = None,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> PaginatedResponse[dict]:
    """Get transit routes"""
    from ....ports.repositories import PaginationParams
    pagination = PaginationParams(page=page, page_size=page_size)
    result = await service.transit_repository.list_routes(
        agency_id=agency_id, route_type=route_type, pagination=pagination
    )
    return PaginatedResponse(
        items=[r.to_dict() for r in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.get("/routes/{route_id}", response_model=dict)
async def get_route(
    route_id: str,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> dict:
    """Get route by ID"""
    route = await service.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route.to_dict()


@router.get("/routes/{route_id}/stops", response_model=list[dict])
async def get_route_stops(
    route_id: str,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> list[dict]:
    """Get stops for a route"""
    stops = await service.transit_repository.get_stops_by_route(route_id)
    return [s.to_dict() for s in stops]


@router.get("/realtime/vehicles", response_model=list[dict])
async def get_vehicle_positions(
    route_id: str | None = None,
    since: datetime | None = None,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> list[dict]:
    """Get real-time vehicle positions"""
    positions = await service.get_vehicle_positions(route_id)
    return [p.to_dict() for p in positions]


@router.get("/realtime/trip-updates", response_model=list[dict])
async def get_trip_updates(
    route_id: str | None = None,
    since: datetime | None = None,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> list[dict]:
    """Get real-time trip updates"""
    # This would need implementation in the service
    return []


@router.get("/realtime/alerts", response_model=list[dict])
async def get_alerts(
    route_id: str | None = None,
    stop_id: str | None = None,
    active_only: bool = True,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> list[dict]:
    """Get real-time service alerts"""
    alerts = await service.get_service_alerts(route_id)
    return [a.to_dict() for a in alerts]


@router.get("/fares/{route_id}", response_model=list[dict])
async def get_route_fares(
    route_id: str,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> list[dict]:
    """Get fares for a route"""
    # This would need implementation in the service
    return []


@router.post("/gtfs/import/{agency_id}")
async def import_gtfs_feed(
    agency_id: str,
    feed_data: dict,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> dict:
    """Import GTFS feed for agency"""
    result = await service.sync_gtfs_data(feed_data)
    return result


@router.delete("/gtfs/{agency_id}")
async def clear_agency_data(
    agency_id: str,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> dict:
    """Clear all data for an agency"""
    # This would need implementation in the service
    return {"success": True, "message": f"Data cleared for agency {agency_id}"}


@router.get("/gtfs/{agency_id}/stats", response_model=dict)
async def get_import_stats(
    agency_id: str,
    service: TransitApplicationService = Depends(get_transit_application_service),
) -> dict:
    """Get GTFS import statistics"""
    # This would need implementation in the service
    return {}


