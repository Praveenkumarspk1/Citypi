"""
LLM Service Adapters
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

from ....application.ports.external_services import LLMServicePort


@dataclass
class LLMResponse:
    """LLM response"""
    content: str
    model: str
    usage: dict[str, int]
    finish_reason: str


@dataclass
class LLMStreamChunk:
    """LLM streaming chunk"""
    content: str
    finish_reason: str | None


class BaseLLMAdapter(LLMServicePort, ABC):
    """Base LLM adapter"""

    @abstractmethod
    async def _generate_request(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Generate text completion request"""
        pass

    @abstractmethod
    async def _generate_structured_request(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None,
        temperature: float,
    ) -> dict[str, Any]:
        """Generate structured output request"""
        pass

    @abstractmethod
    async def _chat_request(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Chat completion request"""
        pass

    @abstractmethod
    async def _stream_chat_request(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        """Stream chat completion request"""
        pass

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text completion"""
        response = await self._generate_request(prompt, system_prompt, temperature, max_tokens)
        return response.content

    async def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Generate structured output"""
        return await self._generate_structured_request(prompt, schema, system_prompt, temperature)

    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Chat completion"""
        response = await self._chat_request(messages, system_prompt, temperature, max_tokens)
        return response.content

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion"""
        async for chunk in self._stream_chat_request(messages, system_prompt, temperature):
            yield chunk.content


class OpenAILLMAdapter(BaseLLMAdapter):
    """OpenAI LLM adapter"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key
        self.model = model
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    def _build_messages(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
    ) -> list[dict[str, str]]:
        result = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})
        result.extend(messages)
        return result

    async def _generate_request(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        client = await self._get_client()

        messages = [{"role": "user", "content": prompt}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=response.choices[0].finish_reason,
        )

    async def _generate_structured_request(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None,
        temperature: float,
    ) -> dict[str, Any]:
        client = await self._get_client()

        # Use function calling for structured output
        functions = [{
            "name": "structured_output",
            "description": "Generate structured output",
            "parameters": schema,
        }]

        messages = [{"role": "user", "content": prompt}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            functions=functions,
            function_call={"name": "structured_output"},
            temperature=temperature,
        )

        import json
        function_args = response.choices[0].message.function_call.arguments
        return json.loads(function_args)

    async def _chat_request(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        client = await self._get_client()

        full_messages = self._build_messages(messages, system_prompt)

        response = await client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=response.choices[0].finish_reason,
        )

    async def _stream_chat_request(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        client = await self._get_client()

        full_messages = self._build_messages(messages, system_prompt)

        stream = await client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield LLMStreamChunk(
                    content=chunk.choices[0].delta.content,
                    finish_reason=chunk.choices[0].finish_reason,
                )


class AnthropicLLMAdapter(BaseLLMAdapter):
    """Anthropic Claude LLM adapter"""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key
        self.model = model
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def _generate_request(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        client = await self._get_client()

        messages = [{"role": "user", "content": prompt}]

        response = await client.messages.create(
            model=self.model,
            messages=messages,
            system=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
        )

    async def _generate_structured_request(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None,
        temperature: float,
    ) -> dict[str, Any]:
        # Anthropic doesn't have native function calling, use prompt engineering
        structured_prompt = f"{prompt}\n\nOutput must be valid JSON matching this schema: {schema}"
        return await self._generate_request(structured_prompt, system_prompt, temperature, 4096)

    async def _chat_request(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        client = await self._get_client()

        response = await client.messages.create(
            model=self.model,
            messages=messages,
            system=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
        )

    async def _stream_chat_request(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        client = await self._get_client()

        stream = await client.messages.create(
            model=self.model,
            messages=messages,
            system=system_prompt,
            temperature=temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.type == "content_block_delta":
                yield LLMStreamChunk(
                    content=chunk.delta.text,
                    finish_reason=None,
                )
            elif chunk.type == "message_delta":
                yield LLMStreamChunk(
                    content="",
                    finish_reason=chunk.delta.stop_reason,
                )


class GoogleGeminiAdapter(BaseLLMAdapter):
    """Google Gemini LLM adapter"""

    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model = model
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client

    async def _generate_request(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        client = await self._get_client()

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = await client.generate_content_async(
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        return LLMResponse(
            content=response.text,
            model=self.model,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            },
            finish_reason=response.candidates[0].finish_reason.name if response.candidates else "STOP",
        )

    async def _generate_structured_request(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None,
        temperature: float,
    ) -> dict[str, Any]:
        # Use prompt engineering for structured output
        structured_prompt = f"{prompt}\n\nOutput must be valid JSON matching this schema: {schema}"
        response = await self._generate_request(structured_prompt, system_prompt, temperature, 4096)
        import json
        return json.loads(response.content)

    async def _chat_request(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        client = await self._get_client()

        # Convert messages to Gemini format
        chat = client.start_chat(history=[])

        # Add system prompt as first user message if provided
        if system_prompt:
            await chat.send_message_async(system_prompt)

        # Send all messages
        for msg in messages[:-1]:
            await chat.send_message_async(msg["content"])

        # Get response for last message
        response = await chat.send_message_async(
            messages[-1]["content"],
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        return LLMResponse(
            content=response.text,
            model=self.model,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            },
            finish_reason=response.candidates[0].finish_reason.name if response.candidates else "STOP",
        )

    async def _stream_chat_request(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        client = await self._get_client()

        full_prompt = ""
        if system_prompt:
            full_prompt += f"{system_prompt}\n\n"
        full_prompt += "\n".join([f"{m['role']}: {m['content']}" for m in messages])

        response = await client.generate_content_async(
            full_prompt,
            generation_config={
                "temperature": temperature,
            },
            stream=True,
        )

        async for chunk in response:
            if chunk.text:
                yield LLMStreamChunk(
                    content=chunk.text,
                    finish_reason=None,
                )


class LocalLLMAdapter(BaseLLMAdapter):
    """Local LLM adapter (using llama.cpp, ollama, or similar)"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        self._session = None

    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session

    async def _generate_request(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        session = await self._get_session()

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return LLMResponse(
                    content=data.get("response", ""),
                    model=self.model,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                    },
                    finish_reason=data.get("done_reason", "stop"),
                )

        return LLMResponse(content="", model=self.model, usage={}, finish_reason="error")

    async def _generate_structured_request(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None,
        temperature: float,
    ) -> dict[str, Any]:
        structured_prompt = f"{prompt}\n\nOutput must be valid JSON matching this schema: {schema}"
        response = await self._generate_request(structured_prompt, system_prompt, temperature, 4096)
        import json
        return json.loads(response.content)

    async def _chat_request(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        session = await self._get_session()

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        if system_prompt:
            payload["messages"].insert(0, {"role": "system", "content": system_prompt})

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return LLMResponse(
                    content=data.get("message", {}).get("content", ""),
                    model=self.model,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                    },
                    finish_reason=data.get("done_reason", "stop"),
                )

        return LLMResponse(content="", model=self.model, usage={}, finish_reason="error")

    async def _stream_chat_request(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        temperature: float,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        session = await self._get_session()

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        if system_prompt:
            payload["messages"].insert(0, {"role": "system", "content": system_prompt})

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                async for line in response.content:
                    if line:
                        import json
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield LLMStreamChunk(
                                    content=data["message"]["content"],
                                    finish_reason=data.get("done_reason"),
                                )
                        except json.JSONDecodeError:
                            pass

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
