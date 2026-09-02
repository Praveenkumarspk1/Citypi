"""
Itinerary Routes
"""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ai_smart_city_concierge.application.commands.itinerary_commands import (
    ActivateItineraryCommand,
    AddCollaboratorCommand,
    AddItineraryDayCommand,
    AddItineraryItemCommand,
    ArchiveItineraryCommand,
    CancelItineraryCommand,
    CompleteItineraryCommand,
    CreateItineraryCommand,
    DeleteItineraryCommand,
    GenerateItineraryByAICommand,
    ItineraryCommandHandler,
    PublishItineraryCommand,
    RemoveCollaboratorCommand,
    RemoveItineraryDayCommand,
    RemoveItineraryItemCommand,
    ReorderItineraryDaysCommand,
    ReorderItineraryItemsCommand,
    UnpublishItineraryCommand,
    UpdateItineraryCommand,
    UpdateItineraryDayCommand,
    UpdateItineraryItemCommand,
)
from ai_smart_city_concierge.application.dto.request import (
    AddCollaboratorRequest,
    AddItineraryDayRequest,
    AddItineraryItemRequest,
    CreateItineraryRequest,
    GenerateItineraryByAIRequest,
    PublishItineraryRequest,
    ReorderItineraryDaysRequest,
    ReorderItineraryItemsRequest,
    UpdateItineraryDayRequest,
    UpdateItineraryItemRequest,
    UpdateItineraryRequest,
)
from ai_smart_city_concierge.application.dto.response import ItineraryResponse, PaginatedResponse
from ai_smart_city_concierge.application.queries.itinerary_queries import (
    GetActiveItinerariesByUserQuery,
    GetCollaborativeItinerariesQuery,
    GetItinerariesByDateRangeQuery,
    GetItinerariesByUserQuery,
    GetItineraryByShareTokenQuery,
    GetItineraryQuery,
    GetItineraryStatsQuery,
    GetPopularItinerariesQuery,
    GetPublicItinerariesQuery,
    ItineraryQueryHandler,
    SearchItinerariesQuery,
)
from ai_smart_city_concierge.domain.entities.itinerary import (
    ItineraryStatus,
)
from ai_smart_city_concierge.infrastructure.auth import get_current_user
from ai_smart_city_concierge.infrastructure.di.container import (
    get_itinerary_command_handler,
    get_itinerary_query_handler,
)

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


@router.post("/", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
async def create_itinerary(
    request: CreateItineraryRequest,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Create a new itinerary"""
    command = CreateItineraryCommand(
        user_id=UUID(current_user["id"]),
        title=request.title,
        description=request.description,
        start_date=request.start_date,
        end_date=request.end_date,
        budget_level=request.budget_level,
        pace=request.pace,
        interests=request.interests,
        accessibility_needs=request.accessibility_needs,
        dietary_restrictions=request.dietary_restrictions,
        transport_preferences=request.transport_preferences,
        base_location=request.base_location,
        base_address=request.base_address,
        city=request.city,
        country=request.country,
        tags=request.tags,
    )
    itinerary = await handler.handle_create_itinerary(command)
    return ItineraryResponse.from_entity(itinerary)


@router.get("/", response_model=PaginatedResponse[ItineraryResponse])
async def get_itineraries(
    status: ItineraryStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    handler: ItineraryQueryHandler = Depends(get_itinerary_query_handler),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[ItineraryResponse]:
    """Get itineraries for current user"""
    query = GetItinerariesByUserQuery(
        user_id=UUID(current_user["id"]),
        status=status,
        page=page,
        page_size=page_size,
    )
    return await handler.handle_get_itineraries_by_user(query)


@router.get("/public", response_model=PaginatedResponse[ItineraryResponse])
async def get_public_itineraries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    city: str | None = None,
    country: str | None = None,
    budget_level: str | None = None,
    pace: str | None = None,
    handler: ItineraryQueryHandler = Depends(get_itinerary_query_handler),
) -> PaginatedResponse[ItineraryResponse]:
    """Get public itineraries"""
    query = GetPublicItinerariesQuery(
        page=page,
        page_size=page_size,
        city=city,
        country=country,
        budget_level=budget_level,
        pace=pace,
    )
    return await handler.handle_get_public_itineraries(query)


@router.get("/collaborative", response_model=list[ItineraryResponse])
async def get_collaborative_itineraries(
    handler: ItineraryQueryHandler = Depends(get_itinerary_query_handler),
    current_user: dict = Depends(get_current_user),
) -> list[ItineraryResponse]:
    """Get collaborative itineraries for current user"""
    query = GetCollaborativeItinerariesQuery(user_id=UUID(current_user["id"]))
    return await handler.handle_get_collaborative_itineraries(query)


@router.get("/active", response_model=list[ItineraryResponse])
async def get_active_itineraries(
    handler: ItineraryQueryHandler = Depends(get_itinerary_query_handler),
    current_user: dict = Depends(get_current_user),
) -> list[ItineraryResponse]:
    """Get active itineraries for current user"""
    query = GetActiveItinerariesByUserQuery(user_id=UUID(current_user["id"]))
    return await handler.handle_get_active_itineraries_by_user(query)


@router.get("/by-date-range", response_model=list[ItineraryResponse])
async def get_itineraries_by_date_range(
    start_date: date = Query(...),
    end_date: date = Query(...),
    handler: ItineraryQueryHandler = Depends(get_itinerary_query_handler),
    current_user: dict = Depends(get_current_user),
) -> list[ItineraryResponse]:
    """Get itineraries within date range"""
    query = GetItinerariesByDateRangeQuery(
        user_id=UUID(current_user["id"]),
        start_date=start_date,
        end_date=end_date,
    )
    return await handler.handle_get_itineraries_by_date_range(query)


@router.get("/search", response_model=PaginatedResponse[ItineraryResponse])
async def search_itineraries(
    query: str = Query(..., min_length=1),
    include_public: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    handler: ItineraryQueryHandler = Depends(get_itinerary_query_handler),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[ItineraryResponse]:
    """Search itineraries"""
    search_query = SearchItinerariesQuery(
        query=query,
        user_id=UUID(current_user["id"]),
        include_public=include_public,
        page=page,
        page_size=page_size,
    )
    return await handler.handle_search_itineraries(search_query)


@router.get("/popular", response_model=list[ItineraryResponse])
async def get_popular_itineraries(
    limit: int = Query(20, ge=1, le=100),
    city: str | None = None,
    country: str | None = None,
    handler: ItineraryQueryHandler = Depends(get_itinerary_query_handler),
) -> list[ItineraryResponse]:
    """Get popular public itineraries"""
    query = GetPopularItinerariesQuery(limit=limit, city=city, country=country)
    return await handler.handle_get_popular_itineraries(query)


@router.get("/stats", response_model=dict)
async def get_itinerary_stats(
    handler: ItineraryQueryHandler = Depends(get_itinerary_query_handler),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get itinerary statistics for current user"""
    query = GetItineraryStatsQuery(user_id=UUID(current_user["id"]))
    return await handler.handle_get_itinerary_stats(query)


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
async def get_itinerary(
    itinerary_id: UUID,
    include_days: bool = True,
    handler: ItineraryQueryHandler = Depends(get_itinerary_query_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Get itinerary by ID"""
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=include_days)
    itinerary = await handler.handle_get_itinerary(query)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    # Check access
    if str(itinerary.user_id) != current_user["id"] and not itinerary.is_public:
        if UUID(current_user["id"]) not in itinerary.collaborators:
            raise HTTPException(status_code=403, detail="Not authorized to access this itinerary")

    return itinerary


@router.get("/share/{share_token}", response_model=ItineraryResponse)
async def get_itinerary_by_share_token(
    share_token: str,
    handler: ItineraryQueryHandler = Depends(get_itinerary_query_handler),
) -> ItineraryResponse:
    """Get public itinerary by share token"""
    query = GetItineraryByShareTokenQuery(share_token=share_token)
    itinerary = await handler.handle_get_itinerary_by_share_token(query)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return itinerary


@router.patch("/{itinerary_id}", response_model=ItineraryResponse)
async def update_itinerary(
    itinerary_id: UUID,
    request: UpdateItineraryRequest,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Update itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = UpdateItineraryCommand(
        itinerary_id=itinerary_id,
        title=request.title,
        description=request.description,
        start_date=request.start_date,
        end_date=request.end_date,
        budget_level=request.budget_level,
        pace=request.pace,
        interests=request.interests,
        accessibility_needs=request.accessibility_needs,
        dietary_restrictions=request.dietary_restrictions,
        transport_preferences=request.transport_preferences,
        base_location=request.base_location,
        base_address=request.base_address,
        city=request.city,
        country=request.country,
        tags=request.tags,
        status=request.status,
    )
    updated = await handler.handle_update_itinerary(command)
    return ItineraryResponse.from_entity(updated)


@router.post("/{itinerary_id}/days", response_model=ItineraryResponse)
async def add_itinerary_day(
    itinerary_id: UUID,
    request: AddItineraryDayRequest,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Add day to itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = AddItineraryDayCommand(
        itinerary_id=itinerary_id,
        day_date=request.day_date,
        title=request.title,
        notes=request.notes,
        start_time=request.start_time,
        end_time=request.end_time,
        base_location=request.base_location,
        base_address=request.base_address,
    )
    await handler.handle_add_day(command)
    # Return updated itinerary
    updated = await query_handler.handle_get_itinerary(GetItineraryQuery(itinerary_id=itinerary_id))
    return ItineraryResponse.from_entity(updated)


@router.patch("/{itinerary_id}/days/{day_id}", response_model=ItineraryResponse)
async def update_itinerary_day(
    itinerary_id: UUID,
    day_id: UUID,
    request: UpdateItineraryDayRequest,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Update itinerary day"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = UpdateItineraryDayCommand(
        itinerary_id=itinerary_id,
        day_id=day_id,
        title=request.title,
        notes=request.notes,
        start_time=request.start_time,
        end_time=request.end_time,
        base_location=request.base_location,
        base_address=request.base_address,
    )
    await handler.handle_update_day(command)
    updated = await query_handler.handle_get_itinerary(GetItineraryQuery(itinerary_id=itinerary_id))
    return ItineraryResponse.from_entity(updated)


@router.delete("/{itinerary_id}/days/{day_id}", response_model=ItineraryResponse)
async def remove_itinerary_day(
    itinerary_id: UUID,
    day_id: UUID,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Remove day from itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = RemoveItineraryDayCommand(itinerary_id=itinerary_id, day_id=day_id)
    await handler.handle_remove_day(command)
    updated = await query_handler.handle_get_itinerary(GetItineraryQuery(itinerary_id=itinerary_id))
    return ItineraryResponse.from_entity(updated)


@router.post("/{itinerary_id}/days/{day_id}/items", response_model=ItineraryResponse)
async def add_itinerary_item(
    itinerary_id: UUID,
    day_id: UUID,
    request: AddItineraryItemRequest,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Add item to itinerary day"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = AddItineraryItemCommand(
        itinerary_id=itinerary_id,
        day_id=day_id,
        type=request.type,
        poi_id=request.poi_id,
        title=request.title,
        description=request.description,
        coordinates=request.coordinates,
        address=request.address,
        start_time=request.start_time,
        end_time=request.end_time,
        duration_minutes=request.duration_minutes,
        transport_mode=request.transport_mode,
        transit_details=request.transit_details,
        from_location=request.from_location,
        to_location=request.to_location,
        estimated_cost=request.estimated_cost,
        currency=request.currency,
        notes=request.notes,
        is_flexible=request.is_flexible,
        is_required=request.is_required,
    )
    await handler.handle_add_item(command)
    updated = await query_handler.handle_get_itinerary(GetItineraryQuery(itinerary_id=itinerary_id))
    return ItineraryResponse.from_entity(updated)


@router.patch("/{itinerary_id}/days/{day_id}/items/{item_id}", response_model=ItineraryResponse)
async def update_itinerary_item(
    itinerary_id: UUID,
    day_id: UUID,
    item_id: UUID,
    request: UpdateItineraryItemRequest,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Update itinerary item"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = UpdateItineraryItemCommand(
        itinerary_id=itinerary_id,
        day_id=day_id,
        item_id=item_id,
        type=request.type,
        poi_id=request.poi_id,
        title=request.title,
        description=request.description,
        coordinates=request.coordinates,
        address=request.address,
        start_time=request.start_time,
        end_time=request.end_time,
        duration_minutes=request.duration_minutes,
        transport_mode=request.transport_mode,
        transit_details=request.transit_details,
        from_location=request.from_location,
        to_location=request.to_location,
        estimated_cost=request.estimated_cost,
        currency=request.currency,
        notes=request.notes,
        is_flexible=request.is_flexible,
        is_required=request.is_required,
    )
    await handler.handle_update_item(command)
    updated = await query_handler.handle_get_itinerary(GetItineraryQuery(itinerary_id=itinerary_id))
    return ItineraryResponse.from_entity(updated)


@router.delete("/{itinerary_id}/days/{day_id}/items/{item_id}", response_model=ItineraryResponse)
async def remove_itinerary_item(
    itinerary_id: UUID,
    day_id: UUID,
    item_id: UUID,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Remove item from itinerary day"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = RemoveItineraryItemCommand(
        itinerary_id=itinerary_id,
        day_id=day_id,
        item_id=item_id,
    )
    await handler.handle_remove_item(command)
    updated = await query_handler.handle_get_itinerary(GetItineraryQuery(itinerary_id=itinerary_id))
    return ItineraryResponse.from_entity(updated)


@router.post("/{itinerary_id}/days/{day_id}/reorder", response_model=ItineraryResponse)
async def reorder_itinerary_items(
    itinerary_id: UUID,
    day_id: UUID,
    request: ReorderItineraryItemsRequest,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Reorder items in day"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = ReorderItineraryItemsCommand(
        itinerary_id=itinerary_id,
        day_id=day_id,
        item_ids=request.item_ids,
    )
    await handler.handle_reorder_items(command)
    updated = await query_handler.handle_get_itinerary(GetItineraryQuery(itinerary_id=itinerary_id))
    return ItineraryResponse.from_entity(updated)


@router.post("/{itinerary_id}/reorder-days", response_model=ItineraryResponse)
async def reorder_itinerary_days(
    itinerary_id: UUID,
    request: ReorderItineraryDaysRequest,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Reorder days in itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = ReorderItineraryDaysCommand(
        itinerary_id=itinerary_id,
        day_ids=request.day_ids,
    )
    await handler.handle_reorder_days(command)
    updated = await query_handler.handle_get_itinerary(GetItineraryQuery(itinerary_id=itinerary_id))
    return ItineraryResponse.from_entity(updated)


@router.post("/{itinerary_id}/collaborators", response_model=ItineraryResponse)
async def add_collaborator(
    itinerary_id: UUID,
    request: AddCollaboratorRequest,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Add collaborator to itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = AddCollaboratorCommand(
        itinerary_id=itinerary_id,
        user_id=request.user_id,
    )
    await handler.handle_add_collaborator(command)
    updated = await query_handler.handle_get_itinerary(GetItineraryQuery(itinerary_id=itinerary_id))
    return ItineraryResponse.from_entity(updated)


@router.delete("/{itinerary_id}/collaborators/{user_id}", response_model=ItineraryResponse)
async def remove_collaborator(
    itinerary_id: UUID,
    user_id: UUID,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Remove collaborator from itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = RemoveCollaboratorCommand(
        itinerary_id=itinerary_id,
        user_id=user_id,
    )
    await handler.handle_remove_collaborator(command)
    updated = await query_handler.handle_get_itinerary(GetItineraryQuery(itinerary_id=itinerary_id))
    return ItineraryResponse.from_entity(updated)


@router.post("/{itinerary_id}/publish", response_model=ItineraryResponse)
async def publish_itinerary(
    itinerary_id: UUID,
    request: PublishItineraryRequest,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Publish itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = PublishItineraryCommand(
        itinerary_id=itinerary_id,
        share_token=request.share_token,
    )
    published = await handler.handle_publish(command)
    return ItineraryResponse.from_entity(published)


@router.post("/{itinerary_id}/unpublish", response_model=ItineraryResponse)
async def unpublish_itinerary(
    itinerary_id: UUID,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Unpublish itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = UnpublishItineraryCommand(itinerary_id=itinerary_id)
    unpublished = await handler.handle_unpublish(command)
    return ItineraryResponse.from_entity(unpublished)


@router.post("/{itinerary_id}/activate", response_model=ItineraryResponse)
async def activate_itinerary(
    itinerary_id: UUID,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Activate itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = ActivateItineraryCommand(itinerary_id=itinerary_id)
    activated = await handler.handle_activate(command)
    return ItineraryResponse.from_entity(activated)


@router.post("/{itinerary_id}/complete", response_model=ItineraryResponse)
async def complete_itinerary(
    itinerary_id: UUID,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Complete itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = CompleteItineraryCommand(itinerary_id=itinerary_id)
    completed = await handler.handle_complete(command)
    return ItineraryResponse.from_entity(completed)


@router.post("/{itinerary_id}/cancel", response_model=ItineraryResponse)
async def cancel_itinerary(
    itinerary_id: UUID,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Cancel itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = CancelItineraryCommand(itinerary_id=itinerary_id)
    cancelled = await handler.handle_cancel(command)
    return ItineraryResponse.from_entity(cancelled)


@router.post("/{itinerary_id}/archive", response_model=ItineraryResponse)
async def archive_itinerary(
    itinerary_id: UUID,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Archive itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this itinerary")

    command = ArchiveItineraryCommand(itinerary_id=itinerary_id)
    archived = await handler.handle_archive(command)
    return ItineraryResponse.from_entity(archived)


@router.delete("/{itinerary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_itinerary(
    itinerary_id: UUID,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> None:
    """Delete itinerary"""
    # Verify ownership
    query_handler = get_itinerary_query_handler()
    query = GetItineraryQuery(itinerary_id=itinerary_id, include_days=False)
    itinerary = await query_handler.handle_get_itinerary(query)

    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if str(itinerary.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this itinerary")

    command = DeleteItineraryCommand(itinerary_id=itinerary_id)
    await handler.handle_delete(command)


@router.post("/generate", response_model=ItineraryResponse)
async def generate_itinerary_by_ai(
    request: GenerateItineraryByAIRequest,
    handler: ItineraryCommandHandler = Depends(get_itinerary_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ItineraryResponse:
    """Generate itinerary using AI"""
    command = GenerateItineraryByAICommand(
        user_id=UUID(current_user["id"]),
        prompt=request.prompt,
        model=request.model,
        tokens=request.tokens,
        title=request.title,
        start_date=request.start_date,
        end_date=request.end_date,
        budget_level=request.budget_level,
        pace=request.pace,
        interests=request.interests,
        accessibility_needs=request.accessibility_needs,
        dietary_restrictions=request.dietary_restrictions,
        transport_preferences=request.transport_preferences,
        base_location=request.base_location,
        base_address=request.base_address,
        city=request.city,
        country=request.country,
    )
    itinerary = await handler.handle_generate_by_ai(command)
    return ItineraryResponse.from_entity(itinerary)
