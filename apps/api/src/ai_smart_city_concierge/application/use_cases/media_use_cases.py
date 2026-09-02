"""
Media Application Use Cases
"""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ...domain.entities.media import Media, MediaStatus, MediaType
from ...domain.repositories.base import PaginatedResult, PaginationParams
from ...domain.repositories.media_repository import MediaRepository


@dataclass
class UploadMediaRequest:
    """Request to upload media"""
    user_id: UUID
    entity_type: str
    entity_id: UUID
    media_type: MediaType
    file_data: bytes
    filename: str
    content_type: str
    title: str | None = None
    description: str | None = None
    alt_text: str | None = None
    order: int = 0
    metadata: dict[str, Any] | None = None


@dataclass
class UpdateMediaRequest:
    """Request to update media"""
    title: str | None = None
    description: str | None = None
    alt_text: str | None = None
    order: int | None = None
    metadata: dict[str, Any] | None = None
    status: MediaStatus | None = None


class MediaUseCases:
    """Media Application Use Cases"""

    def __init__(
        self,
        media_repository: MediaRepository,
        media_service: MediaService,
    ):
        self.media_repository = media_repository

    async def upload_media(self, request: UploadMediaRequest) -> Media:
        """Upload media"""
        # Process and store media
        media = await self.media_service.process_upload(
            user_id=request.user_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            media_type=request.media_type,
            file_data=request.file_data,
            filename=request.filename,
            content_type=request.content_type,
            title=request.title,
            description=request.description,
            alt_text=request.alt_text,
            order=request.order,
            metadata=request.metadata,
        )

        return await self.media_repository.add(media)

    async def get_media(self, media_id: UUID) -> Media | None:
        """Get media by ID"""
        return await self.media_repository.get_by_id(media_id)

    async def get_media_for_entity(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> list[Media]:
        """Get media for an entity"""
        return await self.media_repository.get_by_entity(entity_type, entity_id)

    async def get_user_media(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Media]:
        """Get media by user"""
        return await self.media_repository.get_by_user(user_id, pagination)

    async def update_media(self, media_id: UUID, request: UpdateMediaRequest) -> Media | None:
        """Update media"""
        media = await self.media_repository.get_by_id(media_id)
        if not media:
            return None

        if request.title is not None:
            media.title = request.title
        if request.description is not None:
            media.description = request.description
        if request.alt_text is not None:
            media.alt_text = request.alt_text
        if request.order is not None:
            media.order = request.order
        if request.metadata is not None:
            media.metadata = request.metadata
        if request.status is not None:
            media.status = request.status

        return await self.media_repository.update(media)

    async def delete_media(self, media_id: UUID) -> bool:
        """Delete media"""
        return await self.media_repository.delete(media_id)

    async def update_processing_status(
        self,
        media_id: UUID,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update media processing status"""
        await self.media_repository.update_processing_status(media_id, status, metadata)

    async def generate_thumbnails(self, media_id: UUID) -> list[str]:
        """Generate thumbnails for media"""
        media = await self.media_repository.get_by_id(media_id)
        if not media:
            raise ValueError("Media not found")

        return await self.media_service.generate_thumbnails(media)

    async def extract_metadata(self, media_id: UUID) -> dict[str, Any]:
        """Extract metadata from media"""
        media = await self.media_repository.get_by_id(media_id)
        if not media:
            raise ValueError("Media not found")

        return await self.media_service.extract_metadata(media)

    async def moderate_media(self, media_id: UUID) -> dict[str, Any]:
        """Moderate media content"""
        media = await self.media_repository.get_by_id(media_id)
        if not media:
            raise ValueError("Media not found")

        return await self.media_service.moderate_content(media)
