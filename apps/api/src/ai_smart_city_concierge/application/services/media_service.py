"""
Media Application Service
"""
from typing import Any
from uuid import UUID

from ...domain.entities.media import Media, MediaType
from ...domain.events.domain_events import MediaUploadedEvent, MediaProcessedEvent
from ...domain.repositories.media_repository import MediaRepository
from ..ports.cache import CachePort
from ..ports.event_publisher import EventPublisher
from ..ports.external_services import (
    StorageServicePort,
    SpeechToTextServicePort,
    VisionAIServicePort,
)


class MediaApplicationService:
    """Application service for media management"""

    def __init__(
        self,
        media_repository: MediaRepository,
        storage: StorageServicePort,
        speech_service: SpeechToTextServicePort,
        vision_service: VisionAIServicePort,
        cache: CachePort,
        event_bus: EventPublisher,
    ):
        self.media_repository = media_repository
        self.storage = storage
        self.speech_service = speech_service
        self.vision_service = vision_service
        self.cache = cache
        self.event_bus = event_bus

    async def upload_media(
        self,
        user_id: UUID,
        file_data: bytes,
        filename: str,
        content_type: str,
        media_type: MediaType,
        conversation_id: UUID | None = None,
        itinerary_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Media:
        """Upload media file"""
        # Upload to storage
        storage_path = f"media/{user_id}/{filename}"
        url = await self.storage.upload(storage_path, file_data, content_type)

        # Create media entity
        media = Media(
            user_id=user_id,
            filename=filename,
            original_filename=filename,
            content_type=content_type,
            media_type=media_type,
            url=url,
            size=len(file_data),
            conversation_id=conversation_id,
            itinerary_id=itinerary_id,
            metadata=metadata or {},
            status="uploaded",
        )

        saved_media = await self.media_repository.create(media)

        # Publish event
        event = MediaUploadedEvent.create(saved_media)
        await self.event_bus.publish(event)

        # Process asynchronously based on type
        if media_type == MediaType.AUDIO:
            await self._process_audio(saved_media, file_data)
        elif media_type == MediaType.IMAGE:
            await self._process_image(saved_media, file_data)
        elif media_type == MediaType.VIDEO:
            await self._process_video(saved_media, file_data)

        return saved_media

    async def _process_audio(self, media: Media, file_data: bytes) -> None:
        """Process audio file (STT)"""
        try:
            media.status = "processing"
            await self.media_repository.update(media)

            # Transcribe
            result = await self.speech_service.transcribe(file_data)

            media.transcription = result.text
            media.language = result.language
            media.duration_seconds = result.duration
            media.status = "completed"
            await self.media_repository.update(media)

            event = MediaProcessedEvent.create(media, "transcription")
            await self.event_bus.publish(event)

        except Exception as e:
            media.status = "failed"
            media.error = str(e)
            await self.media_repository.update(media)

    async def _process_image(self, media: Media, file_data: bytes) -> None:
        """Process image file (CLIP analysis)"""
        try:
            media.status = "processing"
            await self.media_repository.update(media)

            # Analyze with CLIP
            result = await self.vision_service.analyze(file_data)

            media.description = result.description
            media.tags = result.tags
            media.objects_detected = result.objects
            media.colors = result.colors
            media.status = "completed"
            await self.media_repository.update(media)

            event = MediaProcessedEvent.create(media, "vision_analysis")
            await self.event_bus.publish(event)

        except Exception as e:
            media.status = "failed"
            media.error = str(e)
            await self.media_repository.update(media)

    async def _process_video(self, media: Media, file_data: bytes) -> None:
        """Process video file"""
        try:
            media.status = "processing"
            await self.media_repository.update(media)

            # For video, we could extract frames and analyze
            # For now, just mark as completed
            media.status = "completed"
            await self.media_repository.update(media)

            event = MediaProcessedEvent.create(media, "video_processing")
            await self.event_bus.publish(event)

        except Exception as e:
            media.status = "failed"
            media.error = str(e)
            await self.media_repository.update(media)

    async def get_media(self, media_id: UUID) -> Media | None:
        """Get media by ID"""
        cached = await self.cache.get(f"media:{media_id}")
        if cached:
            return cached

        media = await self.media_repository.get_by_id(media_id)
        if media:
            await self.cache.set(f"media:{media_id}", media)
        return media

    async def get_user_media(
        self,
        user_id: UUID,
        media_type: MediaType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Media], int]:
        """Get media for a user"""
        return await self.media_repository.get_by_user(
            user_id=user_id,
            media_type=media_type,
            page=page,
            page_size=page_size,
        )

    async def get_conversation_media(self, conversation_id: UUID) -> list[Media]:
        """Get media for a conversation"""
        return await self.media_repository.get_by_conversation(conversation_id)

    async def get_itinerary_media(self, itinerary_id: UUID) -> list[Media]:
        """Get media for an itinerary"""
        return await self.media_repository.get_by_itinerary(itinerary_id)

    async def delete_media(self, media_id: UUID) -> bool:
        """Delete media"""
        media = await self.media_repository.get_by_id(media_id)
        if not media:
            return False

        # Delete from storage
        await self.storage.delete(media.url)

        # Delete from repository
        await self.media_repository.delete(media_id)

        await self.cache.delete(f"media:{media_id}")

        return True

    async def update_media_metadata(
        self,
        media_id: UUID,
        metadata: dict[str, Any],
    ) -> Media | None:
        """Update media metadata"""
        media = await self.media_repository.get_by_id(media_id)
        if not media:
            return None

        media.metadata.update(metadata)
        media.updated_at = datetime.utcnow()
        updated = await self.media_repository.update(media)

        await self.cache.set(f"media:{media_id}", updated)

        return updated

    async def generate_presigned_upload_url(
        self,
        user_id: UUID,
        filename: str,
        content_type: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate presigned URL for direct upload"""
        storage_path = f"media/{user_id}/{filename}"
        return await self.storage.generate_presigned_url(storage_path, expires_in)

    async def generate_presigned_download_url(
        self,
        media_id: UUID,
        expires_in: int = 3600,
    ) -> str | None:
        """Generate presigned URL for download"""
        media = await self.get_media(media_id)
        if not media:
            return None

        return await self.storage.generate_presigned_download_url(media.url, expires_in)