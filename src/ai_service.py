"""AI service layer for interacting with various AI backends."""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional

import httpx

from src.constants import (
    HTTP_TIMEOUT,
    MAX_KEEPALIVE_CONNECTIONS,
    MAX_CONNECTIONS,
)
from src.logger import get_logger, log_ai_request, log_ai_response, log_ai_stream_chunk

# Configure logging
logger = get_logger(__name__)


class AIService(ABC):
    """Abstract base class for AI services."""

    def __init__(self):
        self.last_tokens_input: Optional[int] = None
        self.last_tokens_output: Optional[int] = None

    @abstractmethod
    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream completion from the AI model."""
        yield ""

    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models."""
        pass

    def cancel(self):
        """Cancel the current streaming request."""
        pass

    async def close(self):
        """Close the service and cleanup resources."""
        pass

    def get_last_token_usage(self) -> tuple[Optional[int], Optional[int]]:
        """Get token usage from last request.

        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        return (self.last_tokens_input, self.last_tokens_output)


class OllamaService(AIService):
    """Ollama AI service implementation."""

    def __init__(self, endpoint: str, model: str):
        super().__init__()
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(
            timeout=HTTP_TIMEOUT,
            limits=httpx.Limits(
                max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS, max_connections=MAX_CONNECTIONS
            ),
        )
        self._cancel_event = asyncio.Event()

    def cancel(self):
        """Cancel the current streaming request."""
        if self._cancel_event:
            self._cancel_event.set()

    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream completion from Ollama."""
        # Prepare messages
        formatted_messages = []

        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        formatted_messages.extend(messages)

        # Log request
        log_ai_request(
            model=self.model,
            endpoint=self.endpoint,
            messages=messages,
            system_prompt=system_prompt,
            metadata={"service": "ollama"},
        )

        # Create cancel event
        self._cancel_event = asyncio.Event()

        start_time = time.time()
        full_response = ""
        chunk_count = 0
        error_msg = None
        tokens_input = None
        tokens_output = None

        try:
            async with self.client.stream(
                "POST",
                f"{self.endpoint}/api/chat",
                json={
                    "model": self.model,
                    "messages": formatted_messages,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if self._cancel_event.is_set():
                        # logger.info(f"Ollama request cancelled: {self.model}")
                        return  # Use return instead of break to exit generator properly

                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            content = data["message"]["content"]
                            if content:
                                full_response += content
                                chunk_count += 1
                                log_ai_stream_chunk(
                                    model=self.model,
                                    chunk_num=chunk_count,
                                    chunk_size=len(content),
                                    total_size=len(full_response),
                                )
                                yield content

                        if data.get("done", False):
                            # Extract token usage from final response
                            if "prompt_eval_count" in data:
                                tokens_input = data["prompt_eval_count"]
                                self.last_tokens_input = tokens_input
                            if "eval_count" in data:
                                tokens_output = data["eval_count"]
                                self.last_tokens_output = tokens_output
                            break
                    except json.JSONDecodeError:
                        continue

            # Ensure tokens are stored (in case they weren't set in the loop)
            if tokens_input is not None:
                self.last_tokens_input = tokens_input
            if tokens_output is not None:
                self.last_tokens_output = tokens_output

            # Log successful response
            duration = time.time() - start_time
            log_ai_response(
                model=self.model,
                response=full_response,
                duration=duration,
                success=True,
                metadata={"service": "ollama", "chunks": chunk_count},
                tokens_input=tokens_input,
                tokens_output=tokens_output,
            )

        except Exception as e:
            error_msg = str(e)
            duration = time.time() - start_time
            logger.error(f"Ollama streaming error: {e}")
            log_ai_response(
                model=self.model,
                response=full_response,
                duration=duration,
                success=False,
                error=error_msg,
                metadata={"service": "ollama"},
            )
            raise
        finally:
            self._cancel_event = None

    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            response = await self.client.get(f"{self.endpoint}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to fetch Ollama models: {e}")
            return []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class OpenAICompatibleService(AIService):
    """OpenAI-compatible API service implementation."""

    def __init__(
        self,
        endpoint: str,
        model: str,
        api_key: Optional[str] = None,
        model_type: str = "api",
    ):
        super().__init__()
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.model_type = model_type

        # Setup headers
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.client = httpx.AsyncClient(
            timeout=HTTP_TIMEOUT,
            headers=headers,
            limits=httpx.Limits(
                max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS, max_connections=MAX_CONNECTIONS
            ),
        )
        self._cancel_event = asyncio.Event()

    def cancel(self):
        """Cancel the current streaming request."""
        if self._cancel_event:
            self._cancel_event.set()

    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream completion from OpenAI-compatible API."""
        # Prepare messages
        formatted_messages = []

        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        formatted_messages.extend(messages)

        # Log request
        log_ai_request(
            model=self.model,
            endpoint=self.endpoint,
            messages=messages,
            system_prompt=system_prompt,
            metadata={"service": "openai_compatible"},
        )

        # Create cancel event
        self._cancel_event = asyncio.Event()

        start_time = time.time()
        full_response = ""
        chunk_count = 0
        error_msg = None
        tokens_input = None
        tokens_output = None

        # Determine URL based on model type
        url = f"{self.endpoint}/v1/chat/completions"
        if self.model_type == "perplexity":
            url = f"{self.endpoint}/chat/completions"

        try:
            async with self.client.stream(
                "POST",
                url,
                json={
                    "model": self.model,
                    "messages": formatted_messages,
                    "stream": True,
                    "stream_options": {"include_usage": True},  # Request usage info
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if self._cancel_event.is_set():
                        # logger.info(f"OpenAI-compatible request cancelled: {self.model}")
                        return  # Use return instead of break to exit generator properly

                    if not line or not line.startswith("data: "):
                        continue

                    if line == "data: [DONE]":
                        break

                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix

                        # Extract usage info if available
                        if "usage" in data and data["usage"] is not None:
                            usage = data["usage"]
                            tokens_input = usage.get("prompt_tokens")
                            tokens_output = usage.get("completion_tokens")
                            # Immediately store token usage when available
                            if tokens_input is not None:
                                self.last_tokens_input = tokens_input
                            if tokens_output is not None:
                                self.last_tokens_output = tokens_output

                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                full_response += content
                                chunk_count += 1
                                log_ai_stream_chunk(
                                    model=self.model,
                                    chunk_num=chunk_count,
                                    chunk_size=len(content),
                                    total_size=len(full_response),
                                )
                                yield content
                    except json.JSONDecodeError:
                        continue

            # Ensure tokens are stored (fallback)
            if tokens_input is not None:
                self.last_tokens_input = tokens_input
            if tokens_output is not None:
                self.last_tokens_output = tokens_output

            # Log successful response
            duration = time.time() - start_time
            log_ai_response(
                model=self.model,
                response=full_response,
                duration=duration,
                success=True,
                metadata={"service": "openai_compatible", "chunks": chunk_count},
                tokens_input=tokens_input,
                tokens_output=tokens_output,
            )

        except Exception as e:
            error_msg = str(e)
            duration = time.time() - start_time
            logger.error(f"OpenAI-compatible streaming error: {e}")
            log_ai_response(
                model=self.model,
                response=full_response,
                duration=duration,
                success=False,
                error=error_msg,
                metadata={"service": "openai_compatible"},
            )
            raise
        finally:
            self._cancel_event = None

    async def list_models(self) -> List[str]:
        """List available models (not supported by all APIs)."""
        try:
            response = await self.client.get(f"{self.endpoint}/v1/models")
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except Exception as e:
            logger.error(f"Failed to fetch API models: {e}")
            return []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def create_ai_service(
    model_type: str,
    endpoint: str,
    model: str,
    api_key: Optional[str] = None,
) -> AIService:
    """Factory function to create AI service instances."""
    if model_type == "ollama":
        return OllamaService(endpoint=endpoint, model=model)
    elif model_type == "api" or model_type == "perplexity":
        if not api_key:
            raise ValueError("API key is required for API-based models")
        return OpenAICompatibleService(
            endpoint=endpoint, api_key=api_key, model=model, model_type=model_type
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def _filter_gpt_models(models: List[str]) -> List[str]:
    import re

    filtered = []
    for model in models:
        model_lower = model.lower()

        # Only include specific base models
        # Allowed patterns: gpt-4o, gpt-4o-mini, gpt-4.1, gpt-5o, gpt-5o-mini, gpt-5.0, etc.
        # But exclude things like gpt-4-turbo, gpt-4-vision, etc.
        allowed_patterns = [
            r"^gpt-4o(-mini)?$",  # gpt-4o, gpt-4o-mini
            r"^gpt-4\.1(-mini)?$",  # gpt-4.1, gpt-4.1-mini
            r"^gpt-5o(-mini)?$",  # gpt-5o, gpt-5o-mini
            r"^gpt-5\.0(-mini)?$",  # gpt-5.0, gpt-5.0-mini
            r"^gpt-5(-mini)?$",  # gpt-5, gpt-5-mini
        ]

        if any(re.match(pattern, model_lower) for pattern in allowed_patterns):
            filtered.append(model)

    return filtered


async def fetch_available_models(
    model_type: str,
    endpoint: str,
    api_key: Optional[str] = None,
) -> List[str]:
    """Fetch available models from the service.

    Args:
        model_type: Type of service ("ollama", "api", or "perplexity")
        endpoint: API endpoint URL
        api_key: API key for authentication (required for API type)

    Returns:
        List of available model IDs (filtered for API type)
    """
    # Perplexity API does not support listing models via /v1/models endpoint
    # So we return a hardcoded list of known models
    if model_type == "perplexity":
        return [
            "sonar-reasoning-pro",
            "sonar-reasoning",
            "sonar-pro",
            "sonar",
            "r1-1776",
        ]

    try:
        # Create temporary service instance
        temp_service = create_ai_service(
            model_type=model_type,
            endpoint=endpoint,
            model="dummy",  # Placeholder model
            api_key=api_key,
        )

        # Fetch models
        models = await temp_service.list_models()

        # Clean up - ensure client is fully closed
        await temp_service.close()

        # Give httpx more time to cleanup internal tasks
        await asyncio.sleep(0.1)

        # Filter models based on type
        if model_type == "api":
            models = _filter_gpt_models(models)

        return models
    except Exception as e:
        logger.error(f"Failed to fetch models from {endpoint}: {e}")
        return []
