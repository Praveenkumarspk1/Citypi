"""
POI Routes
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ai_smart_city_concierge.application.commands.poi_commands import (
    ActivatePOICommand,
    AddPOIPhotoCommand,
    BulkUpsertPOIsCommand,
    CreatePOICommand,
    DeactivatePOICommand,
    DeletePOICommand,
    FavoritePOICommand,
    IncrementPOIVisitCommand,
    POICommandHandler,
    RemovePOIPhotoCommand,
    UnfavoritePOICommand,
    UpdatePOICommand,
    UpdatePOIRatingCommand,
    VerifyPOICommand,
)
from ai_smart_city_concierge.application.dto.request import (
    AddPOIPhotoRequest,
    CreatePOIRequest,
    FavoritePOIRequest,
    UpdatePOIRatingRequest,
    UpdatePOIRequest,
    VerifyPOIRequest,
)
from ai_smart_city_concierge.application.dto.response import PaginatedResponse, POIResponse
from ai_smart_city_concierge.application.queries.poi_queries import (
    GetNearbyPOIsQuery,
    GetPOIByExternalIDQuery,
    GetPOIQuery,
    GetPOIsBySourceQuery,
    GetPOIStatsQuery,
    GetPOIsWithinBoundsQuery,
    GetPOIsWithoutEmbeddingQuery,
    GetPopularPOIsQuery,
    GetTrendingPOIsQuery,
    GetUnverifiedPOIsQuery,
    GetVerifiedPOIsQuery,
    ListPOIsQuery,
    POIQueryHandler,
    SearchPOIsQuery,
)
from ai_smart_city_concierge.domain.entities.poi import POICategory, POISource
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.infrastructure.auth import get_current_admin_user, get_current_user
from ai_smart_city_concierge.infrastructure.di.container import (
    get_poi_command_handler,
    get_poi_query_handler,
)

router = APIRouter(prefix="/pois", tags=["pois"])


@router.post("/", response_model=POIResponse, status_code=status.HTTP_201_CREATED)
async def create_poi(
    request: CreatePOIRequest,
    handler: POICommandHandler = Depends(get_poi_command_handler),
    _: dict = Depends(get_current_admin_user),
) -> POIResponse:
    """Create a new POI (admin only)"""
    command = CreatePOICommand(
        name=request.name,
        name_local=request.name_local,
        description=request.description,
        category=request.category,
        subcategory=request.subcategory,
        tags=request.tags,
        coordinates=request.coordinates,
        address=request.address,
        city=request.city,
        state=request.state,
        country=request.country,
        postal_code=request.postal_code,
        neighborhood=request.neighborhood,
        contact=request.contact,
        opening_hours=request.opening_hours,
        external_id=request.external_id,
        source=request.source,
    )
    poi = await handler.handle_create_poi(command)
    return POIResponse.from_entity(poi)


@router.get("/", response_model=PaginatedResponse[POIResponse])
async def list_pois(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: POICategory | None = None,
    source: POISource | None = None,
    verified_only: bool = False,
    active_only: bool = True,
    sort_by: str = "popularity_score",
    sort_order: str = "desc",
    handler: POIQueryHandler = Depends(get_poi_query_handler),
) -> PaginatedResponse[POIResponse]:
    """List POIs with pagination and filters"""
    query = ListPOIsQuery(
        page=page,
        page_size=page_size,
        category=category,
        source=source,
        verified_only=verified_only,
        active_only=active_only,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return await handler.handle_list_pois(query)


@router.get("/search", response_model=PaginatedResponse[POIResponse])
async def search_pois(
    query: str = Query(..., min_length=1),
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    radius_meters: float | None = Query(None, ge=0, le=50000),
    categories: list[POICategory] | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "relevance",
    sort_order: str = "desc",
    handler: POIQueryHandler = Depends(get_poi_query_handler),
) -> PaginatedResponse[POIResponse]:
    """Search POIs by name, description, tags"""
    coordinates = Coordinates(latitude=lat, longitude=lng) if lat is not None and lng is not None else None

    search_query = SearchPOIsQuery(
        query=query,
        coordinates=coordinates,
        radius_meters=radius_meters,
        categories=categories,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return await handler.handle_search_pois(search_query)


@router.get("/nearby", response_model=PaginatedResponse[POIResponse])
async def get_nearby_pois(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_meters: float = Query(1000, ge=0, le=50000),
    categories: list[POICategory] | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    handler: POIQueryHandler = Depends(get_poi_query_handler),
) -> PaginatedResponse[POIResponse]:
    """Get POIs near coordinates"""
    coordinates = Coordinates(latitude=lat, longitude=lng)

    query = GetNearbyPOIsQuery(
        coordinates=coordinates,
        radius_meters=radius_meters,
        categories=categories,
        page=page,
        page_size=page_size,
    )
    return await handler.handle_get_nearby_pois(query)


@router.get("/within-bounds", response_model=PaginatedResponse[POIResponse])
async def get_pois_within_bounds(
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lng: float = Query(..., ge=-180, le=180),
    max_lng: float = Query(..., ge=-180, le=180),
    categories: list[POICategory] | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    handler: POIQueryHandler = Depends(get_poi_query_handler),
) -> PaginatedResponse[POIResponse]:
    """Get POIs within bounding box"""
    query = GetPOIsWithinBoundsQuery(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lng=min_lng,
        max_lng=max_lng,
        categories=categories,
        page=page,
        page_size=page_size,
    )
    return await handler.handle_get_pois_within_bounds(query)


@router.get("/popular", response_model=list[POIResponse])
async def get_popular_pois(
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    radius_meters: float | None = Query(None, ge=0, le=50000),
    category: POICategory | None = None,
    limit: int = Query(20, ge=1, le=100),
    handler: POIQueryHandler = Depends(get_poi_query_handler),
) -> list[POIResponse]:
    """Get popular POIs"""
    coordinates = Coordinates(latitude=lat, longitude=lng) if lat is not None and lng is not None else None

    query = GetPopularPOIsQuery(
        coordinates=coordinates,
        radius_meters=radius_meters,
        category=category,
        limit=limit,
    )
    return await handler.handle_get_popular_pois(query)


@router.get("/trending", response_model=list[POIResponse])
async def get_trending_pois(
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    radius_meters: float | None = Query(None, ge=0, le=50000),
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100),
    handler: POIQueryHandler = Depends(get_poi_query_handler),
) -> list[POIResponse]:
    """Get trending POIs"""
    coordinates = Coordinates(latitude=lat, longitude=lng) if lat is not None and lng is not None else None

    query = GetTrendingPOIsQuery(
        coordinates=coordinates,
        radius_meters=radius_meters,
        days=days,
        limit=limit,
    )
    return await handler.handle_get_trending_pois(query)


@router.get("/by-source/{source}", response_model=PaginatedResponse[POIResponse])
async def get_pois_by_source(
    source: POISource,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    handler: POIQueryHandler = Depends(get_poi_query_handler),
) -> PaginatedResponse[POIResponse]:
    """Get POIs by source"""
    query = GetPOIsBySourceQuery(
        source=source,
        page=page,
        page_size=page_size,
    )
    return await handler.handle_get_pois_by_source(query)


@router.get("/verified", response_model=PaginatedResponse[POIResponse])
async def get_verified_pois(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    handler: POIQueryHandler = Depends(get_poi_query_handler),
) -> PaginatedResponse[POIResponse]:
    """Get verified POIs"""
    query = GetVerifiedPOIsQuery(page=page, page_size=page_size)
    return await handler.handle_get_verified_pois(query)


@router.get("/unverified", response_model=PaginatedResponse[POIResponse])
async def get_unverified_pois(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    handler: POIQueryHandler = Depends(get_poi_query_handler),
    _: dict = Depends(get_current_admin_user),
) -> PaginatedResponse[POIResponse]:
    """Get unverified POIs (admin only)"""
    query = GetUnverifiedPOIsQuery(page=page, page_size=page_size)
    return await handler.handle_get_unverified_pois(query)


@router.get("/without-embedding", response_model=list[POIResponse])
async def get_pois_without_embedding(
    limit: int = Query(100, ge=1, le=1000),
    handler: POIQueryHandler = Depends(get_poi_query_handler),
    _: dict = Depends(get_current_admin_user),
) -> list[POIResponse]:
    """Get POIs without vector embeddings (admin only)"""
    query = GetPOIsWithoutEmbeddingQuery(limit=limit)
    return await handler.handle_get_pois_without_embedding(query)


@router.get("/stats", response_model=dict)
async def get_poi_stats(
    handler: POIQueryHandler = Depends(get_poi_query_handler),
    _: dict = Depends(get_current_admin_user),
) -> dict:
    """Get POI statistics (admin only)"""
    query = GetPOIStatsQuery()
    return await handler.handle_get_poi_stats(query)


@router.get("/{poi_id}", response_model=POIResponse)
async def get_poi(
    poi_id: UUID,
    include_embedding: bool = False,
    handler: POIQueryHandler = Depends(get_poi_query_handler),
) -> POIResponse:
    """Get POI by ID"""
    query = GetPOIQuery(poi_id=poi_id, include_embedding=include_embedding)
    poi = await handler.handle_get_poi(query)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    return poi


@router.get("/external/{external_id}", response_model=POIResponse)
async def get_poi_by_external_id(
    external_id: str,
    source: POISource = Query(...),
    handler: POIQueryHandler = Depends(get_poi_query_handler),
) -> POIResponse:
    """Get POI by external ID"""
    query = GetPOIByExternalIDQuery(external_id=external_id, source=source)
    poi = await handler.handle_get_poi_by_external_id(query)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    return poi


@router.patch("/{poi_id}", response_model=POIResponse)
async def update_poi(
    poi_id: UUID,
    request: UpdatePOIRequest,
    handler: POICommandHandler = Depends(get_poi_command_handler),
    _: dict = Depends(get_current_admin_user),
) -> POIResponse:
    """Update POI (admin only)"""
    command = UpdatePOICommand(
        poi_id=poi_id,
        name=request.name,
        name_local=request.name_local,
        description=request.description,
        category=request.category,
        subcategory=request.subcategory,
        tags=request.tags,
        coordinates=request.coordinates,
        address=request.address,
        city=request.city,
        state=request.state,
        country=request.country,
        postal_code=request.postal_code,
        neighborhood=request.neighborhood,
        contact=request.contact,
        opening_hours=request.opening_hours,
        wheelchair_accessible=request.wheelchair_accessible,
        wifi_available=request.wifi_available,
        outdoor_seating=request.outdoor_seating,
        takeaway=request.takeaway,
        delivery=request.delivery,
        reservation_required=request.reservation_required,
        accepts_credit_cards=request.accepts_credit_cards,
        accepts_cash=request.accepts_cash,
        price_level=request.price_level,
    )
    poi = await handler.handle_update_poi(command)
    return POIResponse.from_entity(poi)


@router.post("/{poi_id}/photos", response_model=POIResponse)
async def add_poi_photo(
    poi_id: UUID,
    request: AddPOIPhotoRequest,
    handler: POICommandHandler = Depends(get_poi_command_handler),
    _: dict = Depends(get_current_admin_user),
) -> POIResponse:
    """Add photo to POI (admin only)"""
    command = AddPOIPhotoCommand(
        poi_id=poi_id,
        photo_url=request.photo_url,
        featured=request.featured,
    )
    poi = await handler.handle_add_photo(command)
    return POIResponse.from_entity(poi)


@router.delete("/{poi_id}/photos", response_model=POIResponse)
async def remove_poi_photo(
    poi_id: UUID,
    photo_url: str = Query(...),
    handler: POICommandHandler = Depends(get_poi_command_handler),
    _: dict = Depends(get_current_admin_user),
) -> POIResponse:
    """Remove photo from POI (admin only)"""
    command = RemovePOIPhotoCommand(poi_id=poi_id, photo_url=photo_url)
    poi = await handler.handle_remove_photo(command)
    return POIResponse.from_entity(poi)


@router.patch("/{poi_id}/rating", response_model=POIResponse)
async def update_poi_rating(
    poi_id: UUID,
    request: UpdatePOIRatingRequest,
    handler: POICommandHandler = Depends(get_poi_command_handler),
    _: dict = Depends(get_current_admin_user),
) -> POIResponse:
    """Update POI rating (admin only)"""
    command = UpdatePOIRatingCommand(
        poi_id=poi_id,
        rating=request.rating,
        review_count=request.review_count,
    )
    poi = await handler.handle_update_rating(command)
    return POIResponse.from_entity(poi)


@router.post("/{poi_id}/verify", response_model=POIResponse)
async def verify_poi(
    poi_id: UUID,
    request: VerifyPOIRequest,
    handler: POICommandHandler = Depends(get_poi_command_handler),
    _: dict = Depends(get_current_admin_user),
) -> POIResponse:
    """Verify POI (admin only)"""
    command = VerifyPOICommand(poi_id=poi_id, verified_by=request.verified_by)
    poi = await handler.handle_verify(command)
    return POIResponse.from_entity(poi)


@router.post("/{poi_id}/visit", response_model=POIResponse)
async def increment_poi_visit(
    poi_id: UUID,
    handler: POICommandHandler = Depends(get_poi_command_handler),
) -> POIResponse:
    """Increment POI visit count"""
    command = IncrementPOIVisitCommand(poi_id=poi_id)
    poi = await handler.handle_increment_visit(command)
    return POIResponse.from_entity(poi)


@router.post("/{poi_id}/favorite")
async def favorite_poi(
    poi_id: UUID,
    request: FavoritePOIRequest,
    handler: POICommandHandler = Depends(get_poi_command_handler),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Favorite POI"""
    command = FavoritePOICommand(poi_id=poi_id, user_id=UUID(current_user["id"]))
    await handler.handle_favorite(command)
    return {"success": True, "message": "POI added to favorites"}


@router.delete("/{poi_id}/favorite")
async def unfavorite_poi(
    poi_id: UUID,
    handler: POICommandHandler = Depends(get_poi_command_handler),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Unfavorite POI"""
    command = UnfavoritePOICommand(poi_id=poi_id, user_id=UUID(current_user["id"]))
    await handler.handle_unfavorite(command)
    return {"success": True, "message": "POI removed from favorites"}


@router.patch("/{poi_id}/deactivate", response_model=POIResponse)
async def deactivate_poi(
    poi_id: UUID,
    handler: POICommandHandler = Depends(get_poi_command_handler),
    _: dict = Depends(get_current_admin_user),
) -> POIResponse:
    """Deactivate POI (admin only)"""
    command = DeactivatePOICommand(poi_id=poi_id)
    poi = await handler.handle_deactivate(command)
    return POIResponse.from_entity(poi)


@router.patch("/{poi_id}/activate", response_model=POIResponse)
async def activate_poi(
    poi_id: UUID,
    handler: POICommandHandler = Depends(get_poi_command_handler),
    _: dict = Depends(get_current_admin_user),
) -> POIResponse:
    """Activate POI (admin only)"""
    command = ActivatePOICommand(poi_id=poi_id)
    poi = await handler.handle_activate(command)
    return POIResponse.from_entity(poi)


@router.delete("/{poi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_poi(
    poi_id: UUID,
    handler: POICommandHandler = Depends(get_poi_command_handler),
    _: dict = Depends(get_current_admin_user),
) -> None:
    """Delete POI (admin only)"""
    command = DeletePOICommand(poi_id=poi_id)
    await handler.handle_delete(command)


@router.post("/bulk", response_model=list[POIResponse])
async def bulk_upsert_pois(
    pois: list[dict],
    handler: POICommandHandler = Depends(get_poi_command_handler),
    _: dict = Depends(get_current_admin_user),
) -> list[POIResponse]:
    """Bulk upsert POIs (admin only)"""
    # Convert dicts to POI entities
    from ai_smart_city_concierge.domain.entities.poi import (
        POI,
        ContactInfo,
        OpeningHours,
        POICategory,
        POISource,
    )
    from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates

    poi_entities = []
    for p in pois:
        poi = POI(
            name=p["name"],
            name_local=p.get("name_local"),
            description=p.get("description"),
            category=POICategory(p.get("category", "other")),
            subcategory=p.get("subcategory"),
            tags=p.get("tags", []),
            coordinates=Coordinates(**p["coordinates"]) if p.get("coordinates") else Coordinates(0, 0),
            address=p.get("address"),
            city=p.get("city"),
            state=p.get("state"),
            country=p.get("country"),
            postal_code=p.get("postal_code"),
            neighborhood=p.get("neighborhood"),
            contact=ContactInfo(**p["contact"]) if p.get("contact") else ContactInfo(),
            opening_hours=OpeningHours(**p["opening_hours"]) if p.get("opening_hours") else None,
            external_id=p.get("external_id"),
            source=POISource(p.get("source", "manual")),
        )
        poi_entities.append(poi)

    command = BulkUpsertPOIsCommand(pois=poi_entities)
    created_pois = await handler.handle_bulk_upsert(command)
    return [POIResponse.from_entity(poi) for poi in created_pois]
