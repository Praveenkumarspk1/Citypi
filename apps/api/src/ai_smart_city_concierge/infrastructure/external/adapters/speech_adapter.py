"""
Speech-to-Text Service Adapters
"""
from abc import ABC, abstractmethod
from typing import Any

from ....application.ports.external_services import SpeechToTextServicePort


@dataclass
class TranscriptionResult:
    """Transcription result"""
    text: str
    language: str
    duration: float
    confidence: float


@dataclass
class TimestampedTranscription:
    """Transcription with timestamps"""
    word: str
    start: float
    end: float
    confidence: float


class BaseSpeechToTextAdapter(SpeechToTextServicePort, ABC):
    """Base speech-to-text adapter"""

    @abstractmethod
    async def _transcribe_request(
        self,
        audio_data: bytes,
        language: str | None,
    ) -> TranscriptionResult:
        """Transcribe audio request"""
        pass

    @abstractmethod
    async def _transcribe_with_timestamps_request(
        self,
        audio_data: bytes,
        language: str | None,
    ) -> list[TimestampedTranscription]:
        """Transcribe with timestamps request"""
        pass

    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
    ) -> str:
        """Transcribe audio to text"""
        result = await self._transcribe_request(audio_data, language)
        return result.text

    async def transcribe_with_timestamps(
        self,
        audio_data: bytes,
        language: str | None = None,
    ) -> list[dict[str, Any]]:
        """Transcribe with word-level timestamps"""
        result = await self._transcribe_with_timestamps_request(audio_data, language)
        return [
            {
                "word": r.word,
                "start": r.start,
                "end": r.end,
                "confidence": r.confidence,
            }
            for r in result
        ]


class FasterWhisperAdapter(BaseSpeechToTextAdapter):
    """faster-whisper adapter (local)"""

    def __init__(self, model_size: str = "large-v3", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    async def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )

    async def _transcribe_request(
        self,
        audio_data: bytes,
        language: str | None,
    ) -> TranscriptionResult:
        await self._load_model()

        # Save audio to temp file
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            segments, info = self._model.transcribe(
                temp_path,
                language=language,
                beam_size=5,
            )

            text = " ".join([seg.text for seg in segments])

            return TranscriptionResult(
                text=text.strip(),
                language=info.language,
                duration=info.duration,
                confidence=sum(seg.avg_logprob for seg in segments) / len(segments) if segments else 0,
            )
        finally:
            os.unlink(temp_path)

    async def _transcribe_with_timestamps_request(
        self,
        audio_data: bytes,
        language: str | None,
    ) -> list[TimestampedTranscription]:
        await self._load_model()

        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            segments, info = self._model.transcribe(
                temp_path,
                language=language,
                beam_size=5,
                word_timestamps=True,
            )

            results = []
            for segment in segments:
                if segment.words:
                    for word in segment.words:
                        results.append(TimestampedTranscription(
                            word=word.word,
                            start=word.start,
                            end=word.end,
                            confidence=word.probability,
                        ))

            return results
        finally:
            os.unlink(temp_path)


class OpenAIWhisperAdapter(BaseSpeechToTextAdapter):
    """OpenAI Whisper API adapter"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def _transcribe_request(
        self,
        audio_data: bytes,
        language: str | None,
    ) -> TranscriptionResult:
        client = await self._get_client()

        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            with open(temp_path, "rb") as audio_file:
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                )

            return TranscriptionResult(
                text=response.text,
                language=response.language,
                duration=response.duration,
                confidence=1.0,  # OpenAI doesn't provide confidence
            )
        finally:
            os.unlink(temp_path)

    async def _transcribe_with_timestamps_request(
        self,
        audio_data: bytes,
        language: str | None,
    ) -> list[TimestampedTranscription]:
        client = await self._get_client()

        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            with open(temp_path, "rb") as audio_file:
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["word"],
                )

            results = []
            if hasattr(response, 'words') and response.words:
                for word in response.words:
                    results.append(TimestampedTranscription(
                        word=word.word,
                        start=word.start,
                        end=word.end,
                        confidence=1.0,
                    ))

            return results
        finally:
            os.unlink(temp_path)


class GoogleSpeechAdapter(BaseSpeechToTextAdapter):
    """Google Cloud Speech-to-Text adapter"""

    def __init__(self, credentials_path: str | None = None):
        self.credentials_path = credentials_path
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from google.cloud import speech
            if self.credentials_path:
                self._client = speech.SpeechClient.from_service_account_file(self.credentials_path)
            else:
                self._client = speech.SpeechClient()
        return self._client

    async def _transcribe_request(
        self,
        audio_data: bytes,
        language: str | None,
    ) -> TranscriptionResult:
        client = await self._get_client()

        from google.cloud import speech

        audio = speech.RecognitionAudio(content=audio_data)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language or "en-US",
            enable_automatic_punctuation=True,
        )

        response = client.recognize(config=config, audio=audio)

        text = " ".join([result.alternatives[0].transcript for result in response.results])
        confidence = sum(result.alternatives[0].confidence for result in response.results) / len(response.results) if response.results else 0

        return TranscriptionResult(
            text=text,
            language=language or "en-US",
            duration=0,  # Not provided
            confidence=confidence,
        )

    async def _transcribe_with_timestamps_request(
        self,
        audio_data: bytes,
        language: str | None,
    ) -> list[TimestampedTranscription]:
        client = await self._get_client()

        from google.cloud import speech

        audio = speech.RecognitionAudio(content=audio_data)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language or "en-US",
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
        )

        response = client.recognize(config=config, audio=audio)

        results = []
        for result in response.results:
            alternative = result.alternatives[0]
            for word_info in alternative.words:
                results.append(TimestampedTranscription(
                    word=word_info.word,
                    start=word_info.start_time.total_seconds(),
                    end=word_info.end_time.total_seconds(),
                    confidence=alternative.confidence,
                ))

        return results


class AzureSpeechAdapter(BaseSpeechToTextAdapter):
    """Azure Speech Service adapter"""

    def __init__(self, subscription_key: str, region: str):
        self.subscription_key = subscription_key
        self.region = region
        self._speech_config = None

    async def _get_speech_config(self):
        if self._speech_config is None:
            import azure.cognitiveservices.speech as speechsdk
            self._speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key,
                region=self.region,
            )
        return self._speech_config

    async def _transcribe_request(
        self,
        audio_data: bytes,
        language: str | None,
    ) -> TranscriptionResult:
        import azure.cognitiveservices.speech as speechsdk

        speech_config = await self._get_speech_config()
        speech_config.speech_recognition_language = language or "en-US"

        # Create audio input from bytes
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config,
            )

            result = recognizer.recognize_once_async().get()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return TranscriptionResult(
                    text=result.text,
                    language=language or "en-US",
                    duration=0,
                    confidence=1.0,
                )
            else:
                return TranscriptionResult(
                    text="",
                    language=language or "en-US",
                    duration=0,
                    confidence=0,
                )
        finally:
            os.unlink(temp_path)

    async def _transcribe_with_timestamps_request(
        self,
        audio_data: bytes,
        language: str | None,
    ) -> list[TimestampedTranscription]:
        # Azure doesn't easily provide word-level timestamps in simple mode
        # Would need continuous recognition with detailed output
        return []
