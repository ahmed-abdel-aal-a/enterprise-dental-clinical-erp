"""Ollama Local AI provider for DentApex (Offline / High-spec machines only).

Connects to a local Ollama instance via OpenAI-compatible endpoint:
http://127.0.0.1:11434/v1

HARDWARE REQUIREMENTS & SAFETY:
- Requires 8GB+ RAM and preferably a dedicated GPU.
- Must NOT be used as the default provider on low-end clinic hardware (4GB RAM).
- Configures OLLAMA_MODELS environment variable to ensure models are stored
  portably in the project data folder (data/ollama_models) rather than the C: drive.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

from openai import AsyncOpenAI

from app.config import settings
from app.core.llm.base import ProviderEvent, ProviderMessage
from app.core.llm.openai_provider import OpenAIProvider

DEFAULT_OLLAMA_MODEL = "llama3.2"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"


def configure_portable_ollama_models_path() -> Path:
    """Ensure OLLAMA_MODELS points to the portable data directory."""
    models_dir = Path(getattr(settings, "OLLAMA_MODELS_PATH", "data/ollama_models")).resolve()
    # If running from backend directory, check relative to project root
    if not models_dir.exists():
        alt_dir = Path(__file__).resolve().parents[4] / "data" / "ollama_models"
        if alt_dir.parent.exists():
            models_dir = alt_dir
    models_dir.mkdir(parents=True, exist_ok=True)
    os.environ["OLLAMA_MODELS"] = str(models_dir)
    return models_dir


class OllamaProvider(OpenAIProvider):
    """Streams completions from a local Ollama instance (Offline Optional AI)."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str = "ollama",
    ) -> None:
        configure_portable_ollama_models_path()
        resolved_url = base_url or getattr(settings, "OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
        self._base_url = resolved_url
        self._api_key = api_key or "ollama"
        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )

    async def complete(
        self,
        *,
        system: str,
        messages: list[ProviderMessage],
        tools: list[dict],
        model: str = DEFAULT_OLLAMA_MODEL,
        max_tokens: int = 4096,
    ) -> AsyncIterator[ProviderEvent]:
        # Normalize model — default to llama3.2 if model is generic or OpenAI-specific
        effective_model = (
            model
            if any(k in model.lower() for k in ("llama", "mistral", "qwen", "phi", "gemma"))
            else DEFAULT_OLLAMA_MODEL
        )
        async for ev in super().complete(
            system=system,
            messages=messages,
            tools=tools,
            model=effective_model,
            max_tokens=max_tokens,
        ):
            yield ev
