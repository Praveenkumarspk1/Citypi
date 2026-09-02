"""
Faster-Whisper Speech-to-Text Client
"""
import os
import tempfile
from typing import Any

from ...application.ports.external_services import SpeechToTextServicePort


class WhisperClient(SpeechToTextServicePort):
    """Faster-Whisper STT client (local, CPU-optimized)"""

    def __init__(
        self,
        model_size: str = "small",  # tiny, base, small, medium, large-v3
        device: str = "cpu",  # cpu, cuda
        compute_type: str = "int8",  # int8, float16, float32
        download_root: str | None = None,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.download_root = download_root or os.getenv("WHISPER_MODEL_DIR", os.path.expanduser("~/.cache/whisper"))
        self._model = None

    def _get_model(self):
        """Lazy load model"""
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=self.download_root,
            )
        return self._model

    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
    ) -> str:
        """Transcribe audio to text"""
        model = self._get_model()

        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            segments, info = model.transcribe(
                tmp_path,
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
            )

            # Combine all segments
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    async def transcribe_with_timestamps(
        self,
        audio_data: bytes,
        language: str | None = None,
    ) -> list[dict[str, Any]]:
        """Transcribe with word-level timestamps"""
        model = self._get_model()

        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            segments, info = model.transcribe(
                tmp_path,
                language=language,
                beam_size=5,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
            )

            results = []
            for segment in segments:
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": [],
                }

                if segment.words:
                    for word in segment.words:
                        segment_data["words"].append({
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability,
                        })

                results.append(segment_data)

            return results
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    async def detect_language(self, audio_data: bytes) -> str:
        """Detect language of audio"""
        model = self._get_model()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            # Use first 30 seconds for language detection
            segments, info = model.transcribe(
                tmp_path,
                beam_size=1,
                language=None,  # Auto-detect
            )
            return info.language
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def get_model_info(self) -> dict[str, Any]:
        """Get model information"""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "download_root": self.download_root,
        }
