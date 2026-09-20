"""Groq Cloud provider for DentApex (Ultra-fast Llama-3 Free Tier: 14,400 RPD).

Connects to Groq Cloud via OpenAI-compatible API endpoint:
https://api.groq.com/openai/v1
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.llm.base import LLMConfigError, ProviderEvent, ProviderMessage
from app.core.llm.openai_provider import OpenAIProvider

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_API_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider(OpenAIProvider):
    """Streams completions from Groq Cloud with ultra-high speed and automatic 429 backoff."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = GROQ_API_BASE_URL,
    ) -> None:
        if not api_key:
            raise LLMConfigError("Groq provider requires GROQ_API_KEY")
        self._api_key = api_key
        self._base_url = base_url
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=3,
        )

    async def complete(
        self,
        *,
        system: str,
        messages: list[ProviderMessage],
        tools: list[dict],
        model: str = DEFAULT_GROQ_MODEL,
        max_tokens: int = 4096,
    ) -> AsyncIterator[ProviderEvent]:
        effective_model = model if model else DEFAULT_GROQ_MODEL
        async for ev in super().complete(
            system=system,
            messages=messages,
            tools=tools,
            model=effective_model,
            max_tokens=max_tokens,
        ):
            yield ev
