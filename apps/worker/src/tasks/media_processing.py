"""
Media Processing Background Tasks

Handles processing of uploaded media files - transcription (Whisper),
image analysis (CLIP), thumbnail generation, etc.
"""

import asyncio
import contextlib
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_smart_city_concierge.domain.repositories.media_repository import MediaRepository
from ai_smart_city_concierge.infrastructure.external_apis.clip_client import CLIPClient
from ai_smart_city_concierge.infrastructure.external_apis.whisper_client import WhisperClient
from ai_smart_city_concierge.infrastructure.storage.base_storage import StorageAdapter

logger = logging.getLogger(__name__)


@dataclass
class MediaProcessingTask:
    """Task for media processing."""
    media_id: str
    processing_type: str  # 'transcribe', 'analyze_image', 'generate_thumbnail', 'extract_metadata'
    priority: int = 0
    options: dict[str, Any] = None


class MediaProcessingTask:
    """
    Background task for processing media files.
    """

    def __init__(
        self,
        whisper_client: WhisperClient,
        clip_client: CLIPClient,
        storage: StorageAdapter,
        media_repository: MediaRepository,
        max_concurrent: int = 2,
        temp_dir: str = "/tmp/media_processing",
    ):
        self.whisper_client = whisper_client
        self.clip_client = clip_client
        self.storage = storage
        self.media_repository = media_repository
        self.max_concurrent = max_concurrent
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._queue: asyncio.Queue[MediaProcessingTask] = asyncio.Queue()
        self._running = False
        self._worker_tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the media processing workers."""
        if self._running:
            return

        self._running = True
        logger.info("Starting media processing workers")

        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker(f"media-processing-worker-{i}"))
            self._worker_tasks.append(task)

    async def stop(self) -> None:
        """Stop the media processing workers."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping media processing workers")

        await self._queue.join()

        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def enqueue(self, task: MediaProcessingTask) -> None:
        """Add a media processing task to the queue."""
        await self._queue.put(task)

    async def enqueue_batch(self, tasks: list[MediaProcessingTask]) -> None:
        """Add multiple media processing tasks to the queue."""
        for task in tasks:
            await self._queue.put(task)

    async def _worker(self, worker_name: str) -> None:
        """Worker coroutine that processes media tasks."""
        logger.info(f"{worker_name} started")

        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)

                try:
                    await self._process_task(task)
                except Exception as e:
                    logger.error(f"{worker_name} error processing task {task.media_id}: {e}")
                    await self._mark_failed(task.media_id, str(e))
                finally:
                    self._queue.task_done()

            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{worker_name} unexpected error: {e}")
                await asyncio.sleep(1)

        logger.info(f"{worker_name} stopped")

    async def _process_task(self, task: MediaProcessingTask) -> None:
        """Process a single media processing task."""
        logger.debug(f"Processing media {task.media_id} ({task.processing_type})")

        media = await self.media_repository.get_by_id(task.media_id)
        if not media:
            logger.warning(f"Media not found: {task.media_id}")
            return

        # Download file to temp directory
        local_path = await self._download_media(media)
        if not local_path:
            await self._mark_failed(task.media_id, "Failed to download media")
            return

        try:
            if task.processing_type == "transcribe":
                await self._transcribe_audio(media, local_path, task.options or {})
            elif task.processing_type == "analyze_image":
                await self._analyze_image(media, local_path, task.options or {})
            elif task.processing_type == "generate_thumbnail":
                await self._generate_thumbnail(media, local_path, task.options or {})
            elif task.processing_type == "extract_metadata":
                await self._extract_metadata(media, local_path, task.options or {})
            else:
                logger.warning(f"Unknown processing type: {task.processing_type}")

        finally:
            # Clean up temp file
            with contextlib.suppress(Exception):
                local_path.unlink()

    async def _download_media(self, media) -> Path | None:
        """Download media file from storage to local temp directory."""
        try:
            local_path = self.temp_dir / f"{media.id}{Path(media.filename).suffix}"
            await self.storage.download(media.storage_path, str(local_path))
            return local_path
        except Exception as e:
            logger.error(f"Failed to download media {media.id}: {e}")
            return None

    async def _transcribe_audio(
        self,
        media,
        local_path: Path,
        options: dict[str, Any],
    ) -> None:
        """Transcribe audio file using Whisper."""
        try:
            language = options.get("language", "auto")
            task_type = options.get("task", "transcribe")

            result = await self.whisper_client.transcribe(
                str(local_path),
                language=language,
                task=task_type,
            )

            if result:
                updates = {
                    "transcription": result.get("text"),
                    "transcription_segments": result.get("segments"),
                    "transcription_language": result.get("language"),
                    "transcription_duration": result.get("duration"),
                    "processed_at": datetime.utcnow().isoformat(),
                }

                await self.media_repository.update(media.id, updates)
                logger.info(f"Transcribed media {media.id} ({len(result.get('text', ''))} chars)")

        except Exception as e:
            logger.error(f"Failed to transcribe media {media.id}: {e}")
            raise

    async def _analyze_image(
        self,
        media,
        local_path: Path,
        options: dict[str, Any],
    ) -> None:
        """Analyze image using CLIP."""
        try:
            # Get image embeddings
            embeddings = await self.clip_client.get_image_embeddings(str(local_path))

            # Classify image with predefined categories
            categories = options.get("categories", [
                "landmark", "restaurant", "museum", "park", "beach", "mountain",
                "cityscape", "nature", "architecture", "food", "transportation",
                "accommodation", "shopping", "entertainment", "cultural", "religious",
            ])

            classification = await self.clip_client.classify_image(
                str(local_path),
                categories,
            )

            # Generate description
            description = await self.clip_client.generate_description(str(local_path))

            updates = {
                "image_embeddings": embeddings,
                "image_classification": classification,
                "image_description": description,
                "processed_at": datetime.utcnow().isoformat(),
            }

            await self.media_repository.update(media.id, updates)
            logger.info(f"Analyzed image {media.id}: {classification}")

        except Exception as e:
            logger.error(f"Failed to analyze image {media.id}: {e}")
            raise

    async def _generate_thumbnail(
        self,
        media,
        local_path: Path,
        options: dict[str, Any],
    ) -> None:
        """Generate thumbnail for image/video."""
        try:
            from PIL import Image

            size = options.get("size", (256, 256))
            quality = options.get("quality", 85)

            with Image.open(local_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Generate thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)

                # Save thumbnail
                thumb_path = self.temp_dir / f"{media.id}_thumb.jpg"
                img.save(thumb_path, "JPEG", quality=quality)

                # Upload thumbnail
                thumb_storage_path = f"thumbnails/{media.id}_thumb.jpg"
                await self.storage.upload(str(thumb_path), thumb_storage_path)

                # Update media record
                await self.media_repository.update(media.id, {
                    "thumbnail_path": thumb_storage_path,
                    "processed_at": datetime.utcnow().isoformat(),
                })

                # Clean up
                thumb_path.unlink()

                logger.info(f"Generated thumbnail for media {media.id}")

        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {media.id}: {e}")
            raise

    async def _extract_metadata(
        self,
        media,
        local_path: Path,
        options: dict[str, Any],
    ) -> None:
        """Extract metadata from media file."""
        try:
            metadata = {}

            # Extract EXIF data for images
            if media.mime_type.startswith("image/"):
                from PIL import Image
                from PIL.ExifTags import TAGS

                with Image.open(local_path) as img:
                    exif = img.getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            tag = TAGS.get(tag_id, tag_id)
                            metadata[f"exif_{tag}"] = str(value)

                    metadata["width"] = img.width
                    metadata["height"] = img.height
                    metadata["format"] = img.format
                    metadata["mode"] = img.mode

            # Extract audio metadata
            elif media.mime_type.startswith("audio/"):
                import mutagen

                audio_file = mutagen.File(local_path)
                if audio_file:
                    metadata["duration"] = audio_file.info.length
                    metadata["bitrate"] = getattr(audio_file.info, "bitrate", None)
                    metadata["sample_rate"] = getattr(audio_file.info, "sample_rate", None)
                    metadata["channels"] = getattr(audio_file.info, "channels", None)

                    # Extract tags
                    for key, value in audio_file.tags.items() if audio_file.tags else []:
                        metadata[f"tag_{key}"] = str(value)

            # Extract video metadata
            elif media.mime_type.startswith("video/"):
                import cv2

                cap = cv2.VideoCapture(str(local_path))
                if cap.isOpened():
                    metadata["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    metadata["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    metadata["fps"] = cap.get(cv2.CAP_PROP_FPS)
                    metadata["frame_count"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    metadata["duration"] = metadata["frame_count"] / metadata["fps"] if metadata["fps"] > 0 else 0
                    cap.release()

            # Update media record
            await self.media_repository.update(media.id, {
                "metadata": metadata,
                "processed_at": datetime.utcnow().isoformat(),
            })

            logger.info(f"Extracted metadata for media {media.id}")

        except Exception as e:
            logger.error(f"Failed to extract metadata for {media.id}: {e}")
            raise

    async def _mark_failed(self, media_id: str, error: str) -> None:
        """Mark media processing as failed."""
        await self.media_repository.update(media_id, {
            "processing_error": error,
            "processing_status": "failed",
            "processed_at": datetime.utcnow().isoformat(),
        })

    # High-level methods

    async def process_media(
        self,
        media_id: str,
        processing_types: list[str] = None,
    ) -> None:
        """Enqueue processing tasks for a specific media item."""
        if processing_types is None:
            # Auto-detect based on mime type
            media = await self.media_repository.get_by_id(media_id)
            if not media:
                return

            processing_types = ["extract_metadata"]

            if media.mime_type.startswith("audio/"):
                processing_types.append("transcribe")
            elif media.mime_type.startswith("image/"):
                processing_types.extend(["analyze_image", "generate_thumbnail"])
            elif media.mime_type.startswith("video/"):
                processing_types.extend(["generate_thumbnail", "extract_metadata"])

        tasks = [
            MediaProcessingTask(media_id=media_id, processing_type=ptype, priority=1)
            for ptype in processing_types
        ]

        await self.enqueue_batch(tasks)

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def is_running(self) -> bool:
        """Check if workers are running."""
        return self._running
