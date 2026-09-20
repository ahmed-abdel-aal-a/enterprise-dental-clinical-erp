"""Google Gemini Flash provider for DentApex (Default Free Tier: 1,500 RPD).

Connects to Google Gemini Flash via its official OpenAI-compatible endpoint:
https://generativelanguage.googleapis.com/v1beta/openai/

Zero local RAM/CPU overhead — mandatory default for low-end hardware (4GB RAM).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from app.core.llm.base import (
    Done,
    LLMConfigError,
    ProviderEvent,
    ProviderMessage,
    TextDelta,
    ToolUse,
    Usage,
)
from app.core.llm.openai_provider import (
    _from_openai_name,
    _parse_args,
    _sanitize_tool_schema,
    _to_openai_messages,
)

DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class GeminiProvider:
    """Streams completions from Google Gemini Flash via OpenAI compatibility endpoint."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = GEMINI_API_BASE_URL,
    ) -> None:
        if not api_key:
            raise LLMConfigError("Gemini provider requires GEMINI_API_KEY")
        self._api_key = api_key
        self._base_url = base_url
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def complete(
        self,
        *,
        system: str,
        messages: list[ProviderMessage],
        tools: list[dict],
        model: str = DEFAULT_GEMINI_MODEL,
        max_tokens: int = 4096,
    ) -> AsyncIterator[ProviderEvent]:
        # Normalize model name — if caller passed an obsolete 1.5/2.0 name or generic, map to 3.6-flash
        effective_model = (
            DEFAULT_GEMINI_MODEL
            if not model or model in ("gemini-1.5-flash", "gemini-2.0-flash", "gemini") or "gemini" not in model.lower()
            else model
        )

        wire_messages = _to_openai_messages(system, messages)
        kwargs: dict[str, Any] = {
            "model": effective_model,
            "messages": wire_messages,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            kwargs["tools"] = [_sanitize_tool_schema(t) for t in tools]
            kwargs["parallel_tool_calls"] = False

        pending: dict[int, dict[str, str]] = {}
        stop_reason = "stop"

        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.usage is not None:
                yield Usage(
                    input_tokens=chunk.usage.prompt_tokens,
                    output_tokens=chunk.usage.completion_tokens,
                )
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if delta is not None and delta.content:
                yield TextDelta(text=delta.content)

            if delta is not None and delta.tool_calls:
                for tc in delta.tool_calls:
                    slot = pending.setdefault(tc.index, {"id": "", "name": "", "args": ""})
                    if tc.id:
                        slot["id"] = tc.id
                    if tc.function is not None:
                        if tc.function.name:
                            slot["name"] = tc.function.name
                        if tc.function.arguments:
                            slot["args"] += tc.function.arguments

            if choice.finish_reason:
                stop_reason = choice.finish_reason

        for slot in pending.values():
            yield ToolUse(
                id=slot["id"],
                name=_from_openai_name(slot["name"]),
                input=_parse_args(slot["args"]),
            )

        yield Done(stop_reason=stop_reason)
