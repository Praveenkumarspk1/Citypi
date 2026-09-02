"""
Media API Routes
"""
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from ....application.use_cases.media_use_cases import (
    MediaUseCases,
    UpdateMediaRequest,
    UploadMediaRequest,
)
from ....domain.entities.media import Media, MediaStatus, MediaType
from ....domain.repositories.base import PaginationParams
from ....infrastructure.config.dependencies import get_media_use_cases

router = APIRouter(prefix="/media", tags=["Media"])


# Request/Response Models
class MediaResponse(BaseModel):
    id: UUID
    user_id: UUID
    entity_type: str
    entity_id: UUID
    media_type: MediaType
    url: str
    thumbnail_url: str | None
    title: str | None
    description: str | None
    alt_text: str | None
    order: int
    status: MediaStatus
    width: int | None
    height: int | None
    duration: float | None
    file_size: int
    mime_type: str
    metadata: dict
    created_at: str
    updated_at: str


class PaginatedMediaResponse(BaseModel):
    items: list[MediaResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class UploadMediaForm(BaseModel):
    entity_type: str
    entity_id: UUID
    media_type: MediaType
    title: str | None = None
    description: str | None = None
    alt_text: str | None = None
    order: int = 0


def media_to_response(media: Media) -> MediaResponse:
    """Convert Media entity to response model"""
    return MediaResponse(
        id=media.id,
        user_id=media.user_id,
        entity_type=media.entity_type,
        entity_id=media.entity_id,
        media_type=media.media_type,
        url=media.url,
        thumbnail_url=media.thumbnail_url,
        title=media.title,
        description=media.description,
        alt_text=media.alt_text,
        order=media.order,
        status=media.status,
        width=media.width,
        height=media.height,
        duration=media.duration,
        file_size=media.file_size,
        mime_type=media.mime_type,
        metadata=media.metadata,
        created_at=media.created_at.isoformat() if media.created_at else "",
        updated_at=media.updated_at.isoformat() if media.updated_at else "",
    )


@router.post("/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    entity_id: UUID = Form(...),
    media_type: MediaType = Form(...),
    title: str | None = Form(None),
    description: str | None = Form(None),
    alt_text: str | None = Form(None),
    order: int = Form(0),
    user_id: UUID = Form(...),  # In real app, get from auth
    use_cases: MediaUseCases = Depends(get_media_use_cases),
):
    """Upload media file"""
    file_data = await file.read()

    request = UploadMediaRequest(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        media_type=media_type,
        file_data=file_data,
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        title=title,
        description=description,
        alt_text=alt_text,
        order=order,
    )

    media = await use_cases.upload_media(request)
    return media_to_response(media)


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: UUID,
    use_cases: MediaUseCases = Depends(get_media_use_cases),
):
    """Get media by ID"""
    media = await use_cases.get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return media_to_response(media)


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[MediaResponse])
async def get_media_for_entity(
    entity_type: str,
    entity_id: UUID,
    use_cases: MediaUseCases = Depends(get_media_use_cases),
):
    """Get media for an entity"""
    return [media_to_response(m) for m in await use_cases.get_media_for_entity(entity_type, entity_id)]


@router.get("/user/{user_id}", response_model=PaginatedMediaResponse)
async def get_user_media(
    user_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: MediaUseCases = Depends(get_media_use_cases),
):
    """Get media by user"""
    result = await use_cases.get_user_media(
        user_id=user_id,
        pagination=PaginationParams(page=page, page_size=page_size),
    )

    return PaginatedMediaResponse(
        items=[media_to_response(m) for m in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.put("/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: UUID,
    request: UpdateMediaRequest,
    use_cases: MediaUseCases = Depends(get_media_use_cases),
):
    """Update media"""
    media = await use_cases.update_media(media_id, request)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return media_to_response(media)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: UUID,
    use_cases: MediaUseCases = Depends(get_media_use_cases),
):
    """Delete media"""
    success = await use_cases.delete_media(media_id)
    if not success:
        raise HTTPException(status_code=404, detail="Media not found")


@router.post("/{media_id}/processing-status", status_code=status.HTTP_204_NO_CONTENT)
async def update_processing_status(
    media_id: UUID,
    status: str = Form(...),
    metadata: str | None = Form(None),
    use_cases: MediaUseCases = Depends(get_media_use_cases),
):
    """Update media processing status"""
    import json
    meta = json.loads(metadata) if metadata else None
    await use_cases.update_processing_status(media_id, status, meta)


@router.post("/{media_id}/thumbnails", response_model=list[str])
async def generate_thumbnails(
    media_id: UUID,
    use_cases: MediaUseCases = Depends(get_media_use_cases),
):
    """Generate thumbnails for media"""
    return await use_cases.generate_thumbnails(media_id)


@router.get("/{media_id}/metadata", response_model=dict)
async def extract_metadata(
    media_id: UUID,
    use_cases: MediaUseCases = Depends(get_media_use_cases),
):
    """Extract metadata from media"""
    return await use_cases.extract_metadata(media_id)


@router.post("/{media_id}/moderate", response_model=dict)
async def moderate_media(
    media_id: UUID,
    use_cases: MediaUseCases = Depends(get_media_use_cases),
):
    """Moderate media content"""
    return await use_cases.moderate_media(media_id)
