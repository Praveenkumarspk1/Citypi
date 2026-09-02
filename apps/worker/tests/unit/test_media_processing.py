"""
Unit tests for media processing tasks
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.worker.src.tasks.media_processing import (
    transcribe_audio,
    analyze_image,
    generate_image_caption,
    extract_text_from_image,
    process_media_upload,
)
from ai_smart_city_concierge.domain.value_objects.coordinates import Coordinates


class TestMediaProcessing:
    """Test cases for media processing tasks"""

    @pytest.fixture
    def mock_audio_file(self):
        """Mock audio file data"""
        return {
            "file_id": str(uuid4()),
            "filename": "voice_message.ogg",
            "content_type": "audio/ogg",
            "size": 1024000,
            "data": b"fake_audio_data",
        }

    @pytest.fixture
    def mock_image_file(self):
        """Mock image file data"""
        return {
            "file_id": str(uuid4()),
            "filename": "photo.jpg",
            "content_type": "image/jpeg",
            "size": 2048000,
            "data": b"fake_image_data",
        }

    @pytest.mark.asyncio
    async def test_transcribe_audio(self, mock_audio_file):
        """Test audio transcription"""
        with patch('apps.worker.src.tasks.media_processing.get_whisper_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.transcribe.return_value = {
                "text": "Hello, I would like to visit the Eiffel Tower tomorrow.",
                "language": "en",
                "duration": 5.2,
                "segments": [
                    {"start": 0.0, "end": 2.5, "text": "Hello, I would like to visit"},
                    {"start": 2.5, "end": 5.2, "text": "the Eiffel Tower tomorrow."},
                ],
            }
            mock_client.return_value = mock_client_instance

            result = await transcribe_audio(mock_audio_file["data"], mock_audio_file["content_type"])

            assert result is not None
            assert "Eiffel Tower" in result["text"]
            assert result["language"] == "en"
            assert len(result["segments"]) == 2
            mock_client_instance.transcribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_image(self, mock_image_file):
        """Test image analysis"""
        with patch('apps.worker.src.tasks.media_processing.get_clip_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.analyze_image.return_value = {
                "labels": ["Eiffel Tower", "landmark", "tower", "iron structure", "Paris", "sky"],
                "confidence": [0.95, 0.92, 0.88, 0.85, 0.90, 0.75],
                "description": "A photo of the Eiffel Tower in Paris on a clear day",
                "objects": [
                    {"label": "Eiffel Tower", "confidence": 0.95, "bbox": [0.1, 0.1, 0.8, 0.9]},
                    {"label": "sky", "confidence": 0.75, "bbox": [0.0, 0.0, 1.0, 0.4]},
                ],
                "colors": ["#8B7355", "#C0C0C0", "#87CEEB"],
            }
            mock_client.return_value = mock_client_instance

            result = await analyze_image(mock_image_file["data"])

            assert result is not None
            assert "Eiffel Tower" in result["labels"]
            assert result["description"] is not None
            assert len(result["objects"]) == 2
            mock_client_instance.analyze_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_image_caption(self, mock_image_file):
        """Test image caption generation"""
        with patch('apps.worker.src.tasks.media_processing.get_gemini_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.generate_caption.return_value = {
                "caption": "The iconic Eiffel Tower stands tall against a clear blue sky in Paris, France.",
                "alt_text": "Eiffel Tower in Paris on a sunny day",
                "tags": ["Eiffel Tower", "Paris", "landmark", "tourism", "architecture"],
            }
            mock_client.return_value = mock_client_instance

            result = await generate_image_caption(mock_image_file["data"])

            assert result is not None
            assert "Eiffel Tower" in result["caption"]
            assert "Paris" in result["caption"]
            assert len(result["tags"]) == 5
            mock_client_instance.generate_caption.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_text_from_image(self, mock_image_file):
        """Test OCR text extraction from image"""
        with patch('apps.worker.src.tasks.media_processing.get_gemini_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.extract_text.return_value = {
                "text": "Eiffel Tower\nOpen: 9:00 AM - 11:45 PM\nTickets: €25.00",
                "blocks": [
                    {"text": "Eiffel Tower", "confidence": 0.98, "bbox": [100, 50, 300, 80]},
                    {"text": "Open: 9:00 AM - 11:45 PM", "confidence": 0.92, "bbox": [100, 100, 300, 130]},
                    {"text": "Tickets: €25.00", "confidence": 0.95, "bbox": [100, 150, 250, 180]},
                ],
                "language": "en",
            }
            mock_client.return_value = mock_client_instance

            result = await extract_text_from_image(mock_image_file["data"])

            assert result is not None
            assert "Eiffel Tower" in result["text"]
            assert "€25.00" in result["text"]
            assert len(result["blocks"]) == 3
            mock_client_instance.extract_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_media_upload_audio(self, mock_audio_file):
        """Test processing audio media upload"""
        with patch('apps.worker.src.tasks.media_processing.transcribe_audio') as mock_transcribe, \
             patch('apps.worker.src.tasks.media_processing.upload_to_storage') as mock_upload:

            mock_transcribe.return_value = {
                "text": "Hello, I want to visit the Louvre.",
                "language": "en",
            }
            mock_upload.return_value = "https://storage.example.com/audio/abc123.ogg"

            result = await process_media_upload(
                file_data=mock_audio_file["data"],
                filename=mock_audio_file["filename"],
                content_type=mock_audio_file["content_type"],
            )

            assert result is not None
            assert result["type"] == "audio"
            assert "transcription" in result
            assert result["storage_url"] == "https://storage.example.com/audio/abc123.ogg"
            mock_transcribe.assert_called_once()
            mock_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_media_upload_image(self, mock_image_file):
        """Test processing image media upload"""
        with patch('apps.worker.src.tasks.media_processing.analyze_image') as mock_analyze, \
             patch('apps.worker.src.tasks.media_processing.generate_image_caption') as mock_caption, \
             patch('apps.worker.src.tasks.media_processing.upload_to_storage') as mock_upload:

            mock_analyze.return_value = {
                "labels": ["Louvre Museum", "museum", "pyramid"],
                "description": "The Louvre Museum glass pyramid",
            }
            mock_caption.return_value = {
                "caption": "The iconic glass pyramid of the Louvre Museum in Paris.",
                "tags": ["Louvre", "Paris", "museum"],
            }
            mock_upload.return_value = "https://storage.example.com/images/def456.jpg"

            result = await process_media_upload(
                file_data=mock_image_file["data"],
                filename=mock_image_file["filename"],
                content_type=mock_image_file["content_type"],
            )

            assert result is not None
            assert result["type"] == "image"
            assert "analysis" in result
            assert "caption" in result
            assert result["storage_url"] == "https://storage.example.com/images/def456.jpg"
            mock_analyze.assert_called_once()
            mock_caption.assert_called_once()
            mock_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_handles_error(self, mock_audio_file):
        """Test transcription handles errors"""
        with patch('apps.worker.src.tasks.media_processing.get_whisper_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.transcribe.side_effect = Exception("Audio format not supported")
            mock_client.return_value = mock_client_instance

            with pytest.raises(Exception, match="Audio format not supported"):
                await transcribe_audio(mock_audio_file["data"], mock_audio_file["content_type"])

    @pytest.mark.asyncio
    async def test_analyze_handles_error(self, mock_image_file):
        """Test image analysis handles errors"""
        with patch('apps.worker.src.tasks.media_processing.get_clip_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.analyze_image.side_effect = Exception("Image too large")
            mock_client.return_value = mock_client_instance

            with pytest.raises(Exception, match="Image too large"):
                await analyze_image(mock_image_file["data"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])