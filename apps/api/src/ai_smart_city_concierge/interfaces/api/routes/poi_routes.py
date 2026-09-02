"""
POI API Routes
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ....application.use_cases.poi_use_cases import (
    CreatePOIRequest,
    POIUseCases,
    SearchPOIsRequest,
    UpdatePOIRequest,
)
from ....domain.entities.poi import POI, POICategory, POISource
from ....domain.repositories.base import PaginationParams, SortParams
from ....domain.value_objects.accessibility import AccessibilityInfo
from ....domain.value_objects.coordinates import Coordinates
from ....domain.value_objects.opening_hours import OpeningHours
from ....infrastructure.config.dependencies import get_poi_use_cases

router = APIRouter(prefix="/pois", tags=["POIs"])


# Request/Response Models
class CoordinatesModel(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class OpeningHoursModel(BaseModel):
    monday: str | None = None
    tuesday: str | None = None
    wednesday: str | None = None
    thursday: str | None = None
    friday: str | None = None
    saturday: str | None = None
    sunday: str | None = None


class AccessibilityModel(BaseModel):
    wheelchair_accessible: bool = False
    wheelchair_accessible_entrance: bool = False
    wheelchair_accessible_parking: bool = False
    wheelchair_accessible_restroom: bool = False
    hearing_impaired_accessible: bool = False
    visually_impaired_accessible: bool = False


class CreatePOIModel(BaseModel):
    name: str
    description: str
    category: POICategory
    coordinates: CoordinatesModel
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    opening_hours: OpeningHoursModel | None = None
    price_level: int | None = Field(None, ge=0, le=4)
    currency: str = "USD"
    accessibility: AccessibilityModel | None = None
    tags: list[str] | None = None
    photos: list[str] | None = None
    source: POISource = POISource.MANUAL
    external_id: str | None = None


class UpdatePOIModel(BaseModel):
    name: str | None = None
    description: str | None = None
    category: POICategory | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    opening_hours: OpeningHoursModel | None = None
    price_level: int | None = Field(None, ge=0, le=4)
    accessibility: AccessibilityModel | None = None
    tags: list[str] | None = None
    photos: list[str] | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class SearchPOIsModel(BaseModel):
    query: str | None = None
    coordinates: CoordinatesModel | None = None
    radius_meters: float | None = Field(None, gt=0, le=50000)
    categories: list[POICategory] | None = None
    min_rating: float | None = Field(None, ge=0, le=5)
    max_price_level: int | None = Field(None, ge=0, le=4)
    accessibility_required: bool | None = None
    open_now: bool | None = None
    has_wifi: bool | None = None
    has_photos: bool | None = None
    verified_only: bool = False
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_field: str | None = None
    sort_order: str = "desc"


class POIResponse(BaseModel):
    id: UUID
    name: str
    description: str
    category: POICategory
    coordinates: CoordinatesModel
    address: str | None
    phone: str | None
    email: str | None
    website: str | None
    opening_hours: OpeningHoursModel | None
    price_level: int | None
    currency: str
    accessibility: AccessibilityModel | None
    tags: list[str]
    photos: list[str]
    source: POISource
    external_id: str | None
    rating: float
    review_count: int
    popularity_score: float
    is_active: bool
    is_verified: bool
    created_at: str
    updated_at: str


class PaginatedPOIResponse(BaseModel):
    items: list[POIResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


def poi_to_response(poi: POI) -> POIResponse:
    """Convert POI entity to response model"""
    return POIResponse(
        id=poi.id,
        name=poi.name,
        description=poi.description,
        category=poi.category,
        coordinates=CoordinatesModel(
            latitude=poi.coordinates.latitude,
            longitude=poi.coordinates.longitude,
        ),
        address=poi.address,
        phone=poi.phone,
        email=poi.email,
        website=poi.website,
        opening_hours=OpeningHoursModel(
            monday=poi.opening_hours.monday if poi.opening_hours else None,
            tuesday=poi.opening_hours.tuesday if poi.opening_hours else None,
            wednesday=poi.opening_hours.wednesday if poi.opening_hours else None,
            thursday=poi.opening_hours.thursday if poi.opening_hours else None,
            friday=poi.opening_hours.friday if poi.opening_hours else None,
            saturday=poi.opening_hours.saturday if poi.opening_hours else None,
            sunday=poi.opening_hours.sunday if poi.opening_hours else None,
        ) if poi.opening_hours else None,
        price_level=poi.price_level,
        currency=poi.currency,
        accessibility=AccessibilityModel(
            wheelchair_accessible=poi.accessibility.wheelchair_accessible if poi.accessibility else False,
            wheelchair_accessible_entrance=poi.accessibility.wheelchair_accessible_entrance if poi.accessibility else False,
            wheelchair_accessible_parking=poi.accessibility.wheelchair_accessible_parking if poi.accessibility else False,
            wheelchair_accessible_restroom=poi.accessibility.wheelchair_accessible_restroom if poi.accessibility else False,
            hearing_impaired_accessible=poi.accessibility.hearing_impaired_accessible if poi.accessibility else False,
            visually_impaired_accessible=poi.accessibility.visually_impaired_accessible if poi.accessibility else False,
        ) if poi.accessibility else None,
        tags=poi.tags,
        photos=poi.photos,
        source=poi.source,
        external_id=poi.external_id,
        rating=poi.rating,
        review_count=poi.review_count,
        popularity_score=poi.popularity_score,
        is_active=poi.is_active,
        is_verified=poi.is_verified,
        created_at=poi.created_at.isoformat() if poi.created_at else "",
        updated_at=poi.updated_at.isoformat() if poi.updated_at else "",
    )


@router.post("", response_model=POIResponse, status_code=status.HTTP_201_CREATED)
async def create_poi(
    request: CreatePOIModel,
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Create a new POI"""
    poi_request = CreatePOIRequest(
        name=request.name,
        description=request.description,
        category=request.category,
        coordinates=Coordinates(
            latitude=request.coordinates.latitude,
            longitude=request.coordinates.longitude,
        ),
        address=request.address,
        phone=request.phone,
        email=request.email,
        website=request.website,
        opening_hours=OpeningHours(
            monday=request.opening_hours.monday if request.opening_hours else None,
            tuesday=request.opening_hours.tuesday if request.opening_hours else None,
            wednesday=request.opening_hours.wednesday if request.opening_hours else None,
            thursday=request.opening_hours.thursday if request.opening_hours else None,
            friday=request.opening_hours.friday if request.opening_hours else None,
            saturday=request.opening_hours.saturday if request.opening_hours else None,
            sunday=request.opening_hours.sunday if request.opening_hours else None,
        ) if request.opening_hours else None,
        price_level=request.price_level,
        currency=request.currency,
        accessibility=AccessibilityInfo(
            wheelchair_accessible=request.accessibility.wheelchair_accessible if request.accessibility else False,
            wheelchair_accessible_entrance=request.accessibility.wheelchair_accessible_entrance if request.accessibility else False,
            wheelchair_accessible_parking=request.accessibility.wheelchair_accessible_parking if request.accessibility else False,
            wheelchair_accessible_restroom=request.accessibility.wheelchair_accessible_restroom if request.accessibility else False,
            hearing_impaired_accessible=request.accessibility.hearing_impaired_accessible if request.accessibility else False,
            visually_impaired_accessible=request.accessibility.visually_impaired_accessible if request.accessibility else False,
        ) if request.accessibility else None,
        tags=request.tags,
        photos=request.photos,
        source=request.source,
        external_id=request.external_id,
    )

    poi = await use_cases.create_poi(poi_request)
    return poi_to_response(poi)


@router.get("/{poi_id}", response_model=POIResponse)
async def get_poi(
    poi_id: UUID,
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Get POI by ID"""
    poi = await use_cases.get_poi(poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    return poi_to_response(poi)


@router.put("/{poi_id}", response_model=POIResponse)
async def update_poi(
    poi_id: UUID,
    request: UpdatePOIModel,
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Update a POI"""
    update_request = UpdatePOIRequest(
        name=request.name,
        description=request.description,
        category=request.category,
        address=request.address,
        phone=request.phone,
        email=request.email,
        website=request.website,
        opening_hours=OpeningHours(
            monday=request.opening_hours.monday if request.opening_hours else None,
            tuesday=request.opening_hours.tuesday if request.opening_hours else None,
            wednesday=request.opening_hours.wednesday if request.opening_hours else None,
            thursday=request.opening_hours.thursday if request.opening_hours else None,
            friday=request.opening_hours.friday if request.opening_hours else None,
            saturday=request.opening_hours.saturday if request.opening_hours else None,
            sunday=request.opening_hours.sunday if request.opening_hours else None,
        ) if request.opening_hours else None,
        price_level=request.price_level,
        accessibility=AccessibilityInfo(
            wheelchair_accessible=request.accessibility.wheelchair_accessible if request.accessibility else False,
            wheelchair_accessible_entrance=request.accessibility.wheelchair_accessible_entrance if request.accessibility else False,
            wheelchair_accessible_parking=request.accessibility.wheelchair_accessible_parking if request.accessibility else False,
            wheelchair_accessible_restroom=request.accessibility.wheelchair_accessible_restroom if request.accessibility else False,
            hearing_impaired_accessible=request.accessibility.hearing_impaired_accessible if request.accessibility else False,
            visually_impaired_accessible=request.accessibility.visually_impaired_accessible if request.accessibility else False,
        ) if request.accessibility else None,
        tags=request.tags,
        photos=request.photos,
        is_active=request.is_active,
        is_verified=request.is_verified,
    )

    poi = await use_cases.update_poi(poi_id, update_request)
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")
    return poi_to_response(poi)


@router.delete("/{poi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_poi(
    poi_id: UUID,
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Delete a POI"""
    success = await use_cases.delete_poi(poi_id)
    if not success:
        raise HTTPException(status_code=404, detail="POI not found")


@router.post("/search", response_model=PaginatedPOIResponse)
async def search_pois(
    request: SearchPOIsModel,
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Search POIs with filters"""
    search_request = SearchPOIsRequest(
        query=request.query,
        coordinates=Coordinates(
            latitude=request.coordinates.latitude,
            longitude=request.coordinates.longitude,
        ) if request.coordinates else None,
        radius_meters=request.radius_meters,
        categories=request.categories,
        min_rating=request.min_rating,
        max_price_level=request.max_price_level,
        accessibility_required=request.accessibility_required,
        open_now=request.open_now,
        has_wifi=request.has_wifi,
        has_photos=request.has_photos,
        verified_only=request.verified_only,
        pagination=PaginationParams(page=request.page, page_size=request.page_size),
        sort=SortParams(field=request.sort_field, order=request.sort_order) if request.sort_field else None,
    )

    result = await use_cases.search_pois(search_request)

    return PaginatedPOIResponse(
        items=[poi_to_response(poi) for poi in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.get("/nearby", response_model=PaginatedPOIResponse)
async def get_nearby_pois(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_meters: float = Query(1000, gt=0, le=50000),
    categories: list[POICategory] | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Get POIs near coordinates"""
    result = await use_cases.get_nearby_pois(
        coordinates=Coordinates(latitude=latitude, longitude=longitude),
        radius_meters=radius_meters,
        categories=categories,
        pagination=PaginationParams(page=page, page_size=page_size),
    )

    return PaginatedPOIResponse(
        items=[poi_to_response(poi) for poi in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.get("/popular", response_model=list[POIResponse])
async def get_popular_pois(
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius_meters: float | None = Query(None, gt=0, le=50000),
    category: POICategory | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Get popular POIs"""
    coordinates = None
    if latitude is not None and longitude is not None:
        coordinates = Coordinates(latitude=latitude, longitude=longitude)

    pois = await use_cases.get_popular_pois(
        coordinates=coordinates,
        radius_meters=radius_meters,
        category=category,
        limit=limit,
    )

    return [poi_to_response(poi) for poi in pois]


@router.get("/trending", response_model=list[POIResponse])
async def get_trending_pois(
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius_meters: float | None = Query(None, gt=0, le=50000),
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100),
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Get trending POIs"""
    coordinates = None
    if latitude is not None and longitude is not None:
        coordinates = Coordinates(latitude=latitude, longitude=longitude)

    pois = await use_cases.get_trending_pois(
        coordinates=coordinates,
        radius_meters=radius_meters,
        days=days,
        limit=limit,
    )

    return [poi_to_response(poi) for poi in pois]


@router.get("/recommendations/{user_id}", response_model=list[POIResponse])
async def get_poi_recommendations(
    user_id: UUID,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_meters: float = Query(5000, gt=0, le=50000),
    limit: int = Query(10, ge=1, le=50),
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Get personalized POI recommendations"""
    pois = await use_cases.get_poi_recommendations(
        user_id=user_id,
        coordinates=Coordinates(latitude=latitude, longitude=longitude),
        radius_meters=radius_meters,
        limit=limit,
    )

    return [poi_to_response(poi) for poi in pois]


@router.post("/{poi_id}/visit", status_code=status.HTTP_204_NO_CONTENT)
async def increment_visit(
    poi_id: UUID,
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Increment POI visit count"""
    await use_cases.increment_visit(poi_id)


@router.post("/{poi_id}/rating", status_code=status.HTTP_204_NO_CONTENT)
async def update_rating(
    poi_id: UUID,
    rating: float = Query(..., ge=0, le=5),
    review_count: int = Query(..., ge=0),
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Update POI rating"""
    await use_cases.update_rating(poi_id, rating, review_count)


@router.get("/stats", response_model=dict)
async def get_poi_stats(
    use_cases: POIUseCases = Depends(get_poi_use_cases),
):
    """Get POI statistics"""
    return await use_cases.get_poi_stats()
