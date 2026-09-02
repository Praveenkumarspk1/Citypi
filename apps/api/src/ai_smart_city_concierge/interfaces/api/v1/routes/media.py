"""
Media Routes
"""
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from ai_smart_city_concierge.application.dto.request import UpdateMediaRequest
from ai_smart_city_concierge.application.dto.response import MediaResponse, PaginatedResponse
from ai_smart_city_concierge.domain.entities.media import MediaSource, MediaStatus, MediaType
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates
from ai_smart_city_concierge.infrastructure.auth import get_current_user
from ai_smart_city_concierge.infrastructure.di.container import get_media_application_service
from ai_smart_city_concierge.application.services.media_service import MediaApplicationService

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    type: MediaType = Form(...),
    user_id: UUID | None = Form(None),
    poi_id: UUID | None = Form(None),
    conversation_id: UUID | None = Form(None),
    itinerary_id: UUID | None = Form(None),
    source: MediaSource = Form(MediaSource.USER_UPLOAD),
    source_url: str | None = Form(None),
    attribution: str | None = Form(None),
    license: str | None = Form(None),
    title: str | None = Form(None),
    description: str | None = Form(None),
    alt_text: str | None = Form(None),
    tags: str | None = Form(None),
    lat: float | None = Form(None, ge=-90, le=90),
    lng: float | None = Form(None, ge=-180, le=180),
    address: str | None = Form(None),
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> MediaResponse:
    """Upload media file"""

    # Parse tags
    tag_list = tags.split(",") if tags else []

    # Parse coordinates
    coordinates = Coordinates(latitude=lat, longitude=lng) if lat is not None and lng is not None else None

    # Read file content
    content = await file.read()

    media = await service.upload_media(
        user_id=user_id or UUID(current_user["id"]),
        file_data=content,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        media_type=type,
        conversation_id=conversation_id,
        itinerary_id=itinerary_id,
    )
    return MediaResponse.from_entity(media)


@router.get("/", response_model=PaginatedResponse[MediaResponse])
async def list_media(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: MediaType | None = None,
    status: MediaStatus | None = None,
    user_id: UUID | None = None,
    poi_id: UUID | None = None,
    conversation_id: UUID | None = None,
    itinerary_id: UUID | None = None,
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[MediaResponse]:
    """List media with filters"""
    # If no user_id specified, use current user
    if user_id is None:
        user_id = UUID(current_user["id"])

    media_list, total = await service.get_user_media(
        user_id=user_id,
        media_type=type,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[MediaResponse.from_entity(m) for m in media_list],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        has_next=page * page_size < total,
        has_prev=page > 1,
    )


@router.get("/pending-moderation", response_model=PaginatedResponse[MediaResponse])
async def get_pending_moderation(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[MediaResponse]:
    """Get media pending moderation (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # This would need a method on the service
    return PaginatedResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
        total_pages=0,
        has_next=False,
        has_prev=False,
    )


@router.get("/by-source/{source}", response_model=PaginatedResponse[MediaResponse])
async def get_media_by_source(
    source: MediaSource,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[MediaResponse]:
    """Get media by source"""
    # This would need a method on the service
    return PaginatedResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
        total_pages=0,
        has_next=False,
        has_prev=False,
    )


@router.get("/without-embedding", response_model=list[MediaResponse])
async def get_media_without_embedding(
    limit: int = Query(100, ge=1, le=1000),
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> list[MediaResponse]:
    """Get media without CLIP embeddings (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # This would need a method on the service
    return []


@router.get("/search", response_model=PaginatedResponse[MediaResponse])
async def search_media(
    query: str = Query(..., min_length=1),
    type: MediaType | None = None,
    user_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[MediaResponse]:
    """Search media by title, description, tags"""
    # This would need a method on the service
    return PaginatedResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
        total_pages=0,
        has_next=False,
        has_prev=False,
    )


@router.get("/stats", response_model=dict)
async def get_media_stats(
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get media statistics (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # This would need a method on the service
    return {}


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: UUID,
    include_variants: bool = True,
    include_metadata: bool = True,
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> MediaResponse:
    """Get media by ID"""
    media = await service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return MediaResponse.from_entity(media)


@router.patch("/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: UUID,
    request: UpdateMediaRequest,
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> MediaResponse:
    """Update media metadata"""
    media = await service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    # Check ownership
    if str(media.user_id) != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to modify this media")

    updated = await service.update_media_metadata(
        media_id=media_id,
        metadata={
            "title": request.title,
            "description": request.description,
            "alt_text": request.alt_text,
            "tags": request.tags,
        },
    )
    return MediaResponse.from_entity(updated)


@router.post("/{media_id}/moderate")
async def moderate_media(
    media_id: UUID,
    approved: bool = Form(...),
    notes: str | None = Form(None),
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Moderate media (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # This would need a method on the service
    return {"success": True, "message": "Media moderated"}


@router.post("/{media_id}/view")
async def increment_media_view(
    media_id: UUID,
    service: MediaApplicationService = Depends(get_media_application_service),
) -> dict:
    """Increment media view count"""
    # This would need a method on the service
    return {"success": True}


@router.post("/{media_id}/download")
async def increment_media_download(
    media_id: UUID,
    service: MediaApplicationService = Depends(get_media_application_service),
) -> dict:
    """Increment media download count"""
    # This would need a method on the service
    return {"success": True}


@router.post("/{media_id}/like")
async def increment_media_like(
    media_id: UUID,
    service: MediaApplicationService = Depends(get_media_application_service),
) -> dict:
    """Increment media like count"""
    # This would need a method on the service
    return {"success": True}


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: UUID,
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> None:
    """Delete media"""
    media = await service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    # Check ownership
    if str(media.user_id) != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this media")

    await service.delete_media(media_id)


@router.post("/cleanup-failed")
async def cleanup_failed_media(
    days: int = Query(7, ge=1, le=365),
    service: MediaApplicationService = Depends(get_media_application_service),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Clean up failed uploads (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # This would need a method on the service
    return {"success": True, "deleted_count": 0}
