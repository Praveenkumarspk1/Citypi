"""
Itinerary API Routes
"""
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ....application.use_cases.itinerary_use_cases import (
    CreateDayRequest,
    CreateItemRequest,
    CreateItineraryRequest,
    ItineraryUseCases,
    OptimizeItineraryRequest,
    UpdateItineraryRequest,
)
from ....domain.entities.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryItem,
    ItineraryStatus,
    ItineraryVisibility,
)
from ....domain.repositories.base import PaginationParams, SortParams
from ....domain.value_objects.coordinates import Coordinates
from ....domain.value_objects.money import Money
from ....infrastructure.config.dependencies import get_itinerary_use_cases

router = APIRouter(prefix="/itineraries", tags=["Itineraries"])


# Request/Response Models
class CoordinatesModel(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class MoneyModel(BaseModel):
    amount: float = Field(..., ge=0)
    currency: str = "USD"


class TimeRangeModel(BaseModel):
    start: str
    end: str


class CreateItineraryModel(BaseModel):
    user_id: UUID
    title: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: ItineraryStatus = ItineraryStatus.DRAFT
    visibility: ItineraryVisibility = ItineraryVisibility.PRIVATE
    budget: MoneyModel | None = None
    tags: list[str] | None = None
    metadata: dict | None = None
    is_ai_generated: bool = False
    ai_prompt: str | None = None


class UpdateItineraryModel(BaseModel):
    title: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: ItineraryStatus | None = None
    visibility: ItineraryVisibility | None = None
    budget: MoneyModel | None = None
    tags: list[str] | None = None
    metadata: dict | None = None
    shared_with: list[UUID] | None = None


class CreateDayModel(BaseModel):
    itinerary_id: UUID
    date: date
    title: str | None = None
    notes: str | None = None


class CreateItemModel(BaseModel):
    day_id: UUID
    poi_id: UUID | None = None
    custom_name: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_minutes: int | None = Field(None, ge=0)
    order: int = 0
    coordinates: CoordinatesModel | None = None
    address: str | None = None
    transport_mode: str | None = None
    transport_details: dict | None = None
    cost: MoneyModel | None = None
    notes: str | None = None
    metadata: dict | None = None


class OptimizeItineraryModel(BaseModel):
    itinerary_id: UUID
    optimization_goals: list[str] | None = None
    constraints: dict | None = None


class GenerateItineraryModel(BaseModel):
    user_id: UUID
    title: str
    start_date: date
    end_date: date
    preferences: dict
    coordinates: CoordinatesModel
    radius_meters: float = 10000


class ItineraryItemResponse(BaseModel):
    id: UUID
    day_id: UUID
    poi_id: UUID | None
    custom_name: str | None
    description: str | None
    start_time: str | None
    end_time: str | None
    duration_minutes: int | None
    order: int
    coordinates: CoordinatesModel | None
    address: str | None
    transport_mode: str | None
    transport_details: dict
    cost: MoneyModel | None
    notes: str | None
    metadata: dict


class ItineraryDayResponse(BaseModel):
    id: UUID
    itinerary_id: UUID
    date: str
    title: str | None
    notes: str | None
    items: list[ItineraryItemResponse]


class ItineraryResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    start_date: str | None
    end_date: str | None
    status: ItineraryStatus
    visibility: ItineraryVisibility
    budget: MoneyModel | None
    tags: list[str]
    metadata: dict
    is_ai_generated: bool
    ai_prompt: str | None
    shared_with: list[str]
    days: list[ItineraryDayResponse]
    created_at: str
    updated_at: str


class PaginatedItineraryResponse(BaseModel):
    items: list[ItineraryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


def money_to_model(money: Money | None) -> MoneyModel | None:
    """Convert Money to model"""
    if not money:
        return None
    return MoneyModel(amount=money.amount, currency=money.currency)


def item_to_response(item: ItineraryItem) -> ItineraryItemResponse:
    """Convert ItineraryItem to response"""
    return ItineraryItemResponse(
        id=item.id,
        day_id=item.day_id,
        poi_id=item.poi_id,
        custom_name=item.custom_name,
        description=item.description,
        start_time=item.start_time.isoformat() if item.start_time else None,
        end_time=item.end_time.isoformat() if item.end_time else None,
        duration_minutes=item.duration_minutes,
        order=item.order,
        coordinates=CoordinatesModel(
            latitude=item.coordinates.latitude,
            longitude=item.coordinates.longitude,
        ) if item.coordinates else None,
        address=item.address,
        transport_mode=item.transport_mode,
        transport_details=item.transport_details,
        cost=money_to_model(item.cost),
        notes=item.notes,
        metadata=item.metadata,
    )


def day_to_response(day: ItineraryDay) -> ItineraryDayResponse:
    """Convert ItineraryDay to response"""
    return ItineraryDayResponse(
        id=day.id,
        itinerary_id=day.itinerary_id,
        date=day.date.isoformat() if day.date else "",
        title=day.title,
        notes=day.notes,
        items=[item_to_response(item) for item in day.items],
    )


def itinerary_to_response(itinerary: Itinerary) -> ItineraryResponse:
    """Convert Itinerary to response"""
    return ItineraryResponse(
        id=itinerary.id,
        user_id=itinerary.user_id,
        title=itinerary.title,
        description=itinerary.description,
        start_date=itinerary.start_date.isoformat() if itinerary.start_date else None,
        end_date=itinerary.end_date.isoformat() if itinerary.end_date else None,
        status=itinerary.status,
        visibility=itinerary.visibility,
        budget=money_to_model(itinerary.budget),
        tags=itinerary.tags,
        metadata=itinerary.metadata,
        is_ai_generated=itinerary.is_ai_generated,
        ai_prompt=itinerary.ai_prompt,
        shared_with=[str(uid) for uid in itinerary.shared_with],
        days=[day_to_response(day) for day in itinerary.days],
        created_at=itinerary.created_at.isoformat() if itinerary.created_at else "",
        updated_at=itinerary.updated_at.isoformat() if itinerary.updated_at else "",
    )


@router.post("", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
async def create_itinerary(
    request: CreateItineraryModel,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Create a new itinerary"""
    itinerary_request = CreateItineraryRequest(
        user_id=request.user_id,
        title=request.title,
        description=request.description,
        start_date=request.start_date,
        end_date=request.end_date,
        status=request.status,
        visibility=request.visibility,
        budget=Money(amount=request.budget.amount, currency=request.budget.currency) if request.budget else None,
        tags=request.tags,
        metadata=request.metadata,
        is_ai_generated=request.is_ai_generated,
        ai_prompt=request.ai_prompt,
    )

    itinerary = await use_cases.create_itinerary(itinerary_request)
    return itinerary_to_response(itinerary)


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
async def get_itinerary(
    itinerary_id: UUID,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Get itinerary by ID"""
    itinerary = await use_cases.get_itinerary(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return itinerary_to_response(itinerary)


@router.get("/user/{user_id}", response_model=PaginatedItineraryResponse)
async def get_user_itineraries(
    user_id: UUID,
    status: ItineraryStatus | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Get itineraries for a user"""
    result = await use_cases.get_user_itineraries(
        user_id=user_id,
        pagination=PaginationParams(page=page, page_size=page_size),
        status=status.value if status else None,
    )

    return PaginatedItineraryResponse(
        items=[itinerary_to_response(i) for i in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.get("/public", response_model=PaginatedItineraryResponse)
async def get_public_itineraries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Get public itineraries"""
    result = await use_cases.get_public_itineraries(
        pagination=PaginationParams(page=page, page_size=page_size),
    )

    return PaginatedItineraryResponse(
        items=[itinerary_to_response(i) for i in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.get("/shared/{user_id}", response_model=PaginatedItineraryResponse)
async def get_shared_itineraries(
    user_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Get itineraries shared with user"""
    result = await use_cases.get_shared_itineraries(
        user_id=user_id,
        pagination=PaginationParams(page=page, page_size=page_size),
    )

    return PaginatedItineraryResponse(
        items=[itinerary_to_response(i) for i in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.put("/{itinerary_id}", response_model=ItineraryResponse)
async def update_itinerary(
    itinerary_id: UUID,
    request: UpdateItineraryModel,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Update an itinerary"""
    update_request = UpdateItineraryRequest(
        title=request.title,
        description=request.description,
        start_date=request.start_date,
        end_date=request.end_date,
        status=request.status,
        visibility=request.visibility,
        budget=Money(amount=request.budget.amount, currency=request.budget.currency) if request.budget else None,
        tags=request.tags,
        metadata=request.metadata,
        shared_with=request.shared_with,
    )

    itinerary = await use_cases.update_itinerary(itinerary_id, update_request)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return itinerary_to_response(itinerary)


@router.delete("/{itinerary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_itinerary(
    itinerary_id: UUID,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Delete an itinerary"""
    success = await use_cases.delete_itinerary(itinerary_id)
    if not success:
        raise HTTPException(status_code=404, detail="Itinerary not found")


@router.post("/days", response_model=ItineraryDayResponse, status_code=status.HTTP_201_CREATED)
async def add_day(
    request: CreateDayModel,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Add a day to an itinerary"""
    day_request = CreateDayRequest(
        itinerary_id=request.itinerary_id,
        date=request.date,
        title=request.title,
        notes=request.notes,
    )

    day = await use_cases.add_day(day_request)
    return day_to_response(day)


@router.put("/days/{day_id}", response_model=ItineraryDayResponse)
async def update_day(
    day_id: UUID,
    request: CreateDayModel,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Update an itinerary day"""
    day = ItineraryDay(
        id=day_id,
        itinerary_id=request.itinerary_id,
        date=request.date,
        title=request.title,
        notes=request.notes,
    )

    await use_cases.update_day(day)
    return day_to_response(day)


@router.delete("/{itinerary_id}/days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_day(
    itinerary_id: UUID,
    day_id: UUID,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Remove a day from an itinerary"""
    await use_cases.remove_day(itinerary_id, day_id)


@router.post("/items", response_model=ItineraryItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    request: CreateItemModel,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Add an item to an itinerary day"""
    item_request = CreateItemRequest(
        day_id=request.day_id,
        poi_id=request.poi_id,
        custom_name=request.custom_name,
        description=request.description,
        start_time=request.start_time,
        end_time=request.end_time,
        duration_minutes=request.duration_minutes,
        order=request.order,
        coordinates=Coordinates(
            latitude=request.coordinates.latitude,
            longitude=request.coordinates.longitude,
        ) if request.coordinates else None,
        address=request.address,
        transport_mode=request.transport_mode,
        transport_details=request.transport_details,
        cost=Money(amount=request.cost.amount, currency=request.cost.currency) if request.cost else None,
        notes=request.notes,
        metadata=request.metadata,
    )

    item = await use_cases.add_item(item_request)
    return item_to_response(item)


@router.put("/items/{item_id}", response_model=ItineraryItemResponse)
async def update_item(
    item_id: UUID,
    request: CreateItemModel,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Update an itinerary item"""
    item = ItineraryItem(
        id=item_id,
        day_id=request.day_id,
        poi_id=request.poi_id,
        custom_name=request.custom_name,
        description=request.description,
        start_time=request.start_time,
        end_time=request.end_time,
        duration_minutes=request.duration_minutes,
        order=request.order,
        coordinates=Coordinates(
            latitude=request.coordinates.latitude,
            longitude=request.coordinates.longitude,
        ) if request.coordinates else None,
        address=request.address,
        transport_mode=request.transport_mode,
        transport_details=request.transport_details,
        cost=Money(amount=request.cost.amount, currency=request.cost.currency) if request.cost else None,
        notes=request.notes,
        metadata=request.metadata,
    )

    await use_cases.update_item(item)
    return item_to_response(item)


@router.delete("/days/{day_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    day_id: UUID,
    item_id: UUID,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Remove an item from an itinerary day"""
    await use_cases.remove_item(day_id, item_id)


@router.post("/days/{day_id}/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_items(
    day_id: UUID,
    item_ids: list[UUID],
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Reorder items in a day"""
    await use_cases.reorder_items(day_id, item_ids)


@router.post("/optimize", response_model=ItineraryResponse)
async def optimize_itinerary(
    request: OptimizeItineraryModel,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Optimize an itinerary"""
    optimize_request = OptimizeItineraryRequest(
        itinerary_id=request.itinerary_id,
        optimization_goals=request.optimization_goals,
        constraints=request.constraints,
    )

    itinerary = await use_cases.optimize_itinerary(optimize_request)
    return itinerary_to_response(itinerary)


@router.post("/generate", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
async def generate_itinerary(
    request: GenerateItineraryModel,
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Generate an AI-powered itinerary"""
    itinerary = await use_cases.generate_itinerary(
        user_id=request.user_id,
        title=request.title,
        start_date=request.start_date,
        end_date=request.end_date,
        preferences=request.preferences,
        coordinates=Coordinates(
            latitude=request.coordinates.latitude,
            longitude=request.coordinates.longitude,
        ),
        radius_meters=request.radius_meters,
    )

    return itinerary_to_response(itinerary)


@router.post("/{itinerary_id}/duplicate", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_itinerary(
    itinerary_id: UUID,
    user_id: UUID,
    new_title: str | None = Query(None),
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Duplicate an itinerary"""
    itinerary = await use_cases.duplicate_itinerary(
        itinerary_id=itinerary_id,
        user_id=user_id,
        new_title=new_title,
    )

    return itinerary_to_response(itinerary)


@router.get("/stats", response_model=dict)
async def get_itinerary_stats(
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Get itinerary statistics"""
    return await use_cases.get_itinerary_stats()


@router.post("/search", response_model=PaginatedItineraryResponse)
async def search_itineraries(
    user_id: UUID | None = Query(None),
    status: ItineraryStatus | None = Query(None),
    visibility: ItineraryVisibility | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    min_budget: float | None = Query(None, ge=0),
    max_budget: float | None = Query(None, ge=0),
    categories: list[str] | None = Query(None),
    ai_generated: bool | None = Query(None),
    shared_with_user: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_field: str | None = Query(None),
    sort_order: str = Query("desc"),
    use_cases: ItineraryUseCases = Depends(get_itinerary_use_cases),
):
    """Search itineraries with filters"""
    result = await use_cases.search_itineraries(
        user_id=user_id,
        status=status,
        visibility=visibility,
        start_date=start_date,
        end_date=end_date,
        min_budget=min_budget,
        max_budget=max_budget,
        categories=categories,
        ai_generated=ai_generated,
        shared_with_user=shared_with_user,
        pagination=PaginationParams(page=page, page_size=page_size),
        sort=SortParams(field=sort_field, order=sort_order) if sort_field else None,
    )

    return PaginatedItineraryResponse(
        items=[itinerary_to_response(i) for i in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )
