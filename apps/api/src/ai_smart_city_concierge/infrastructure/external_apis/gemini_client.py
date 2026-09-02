"""
Gemini LLM Client
"""
import os
from collections.abc import AsyncGenerator
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig, HarmBlockThreshold, HarmCategory

from ...application.ports.external_services import LLMServicePort


class GeminiClient(LLMServicePort):
    """Gemini 1.5 Flash API client"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        self._model = None

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(model)

    def _get_model(self):
        """Get or create model instance"""
        if self._model is None and self.api_key:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text completion"""
        model = self._get_model()
        if not model:
            raise ValueError("Gemini API key not configured")

        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            top_p=0.95,
            top_k=40,
        )

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        response = await model.generate_content_async(
            full_prompt,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )

        return response.text or ""

    async def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Generate structured output (JSON)"""
        model = self._get_model()
        if not model:
            raise ValueError("Gemini API key not configured")

        # Add schema instruction to prompt
        schema_prompt = f"""
{prompt}

Please respond with a valid JSON object matching this schema:
{schema}

Return only the JSON object, no additional text.
"""

        full_prompt = schema_prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {schema_prompt}"

        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=2048,
            response_mime_type="application/json",
        )

        response = await model.generate_content_async(
            full_prompt,
            generation_config=generation_config,
        )

        import json
        try:
            return json.loads(response.text or "{}")
        except json.JSONDecodeError:
            # Try to extract JSON from response
            text = response.text or ""
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            return {}

    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Chat completion"""
        model = self._get_model()
        if not model:
            raise ValueError("Gemini API key not configured")

        # Convert messages to Gemini format
        chat_history = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                # System messages are handled separately
                continue
            elif role == "assistant":
                chat_history.append({"role": "model", "parts": [content]})
            else:
                chat_history.append({"role": "user", "parts": [content]})

        # Start chat with history
        chat = model.start_chat(history=chat_history[:-1] if chat_history else [])

        # Send last message
        last_message = chat_history[-1]["parts"][0] if chat_history else ""

        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = await chat.send_message_async(
            last_message,
            generation_config=generation_config,
        )

        return response.text or ""

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion"""
        model = self._get_model()
        if not model:
            raise ValueError("Gemini API key not configured")

        # Convert messages to Gemini format
        chat_history = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                continue
            elif role == "assistant":
                chat_history.append({"role": "model", "parts": [content]})
            else:
                chat_history.append({"role": "user", "parts": [content]})

        chat = model.start_chat(history=chat_history[:-1] if chat_history else [])
        last_message = chat_history[-1]["parts"][0] if chat_history else ""

        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=2048,
        )

        response = await chat.send_message_async(
            last_message,
            generation_config=generation_config,
            stream=True,
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    def get_model_name(self) -> str:
        """Get model name"""
        return self.model_name

    async def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        model = self._get_model()
        if not model:
            return 0

        result = await model.count_tokens_async(text)
        return result.total_tokens
