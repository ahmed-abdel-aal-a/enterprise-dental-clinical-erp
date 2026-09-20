"""Provider resolution.

Supports Google Gemini Flash (Default Free Tier), Groq Cloud (Free Tier),
Ollama Local AI (Advanced Offline Toggle), and OpenAI.
"""

from __future__ import annotations

from app.config import settings
from app.core.llm.base import LLMConfigError, Provider

SUPPORTED_PROVIDERS = ("gemini", "groq", "ollama", "openai")


def get_provider(name: str | None = None, *, api_key: str | None = None) -> Provider:
    """Return a configured :class:`Provider` for ``name``.

    Mandatory default is 'gemini' (Google Gemini Flash) to protect low-end
    clinic hardware (4GB RAM) with 0% CPU/RAM local consumption.
    """
    provider_name = (name or getattr(settings, "LLM_PROVIDER", None) or "gemini").lower()

    if provider_name == "gemini":
        from app.core.llm.gemini_provider import GeminiProvider

        return GeminiProvider(api_key=api_key or settings.GEMINI_API_KEY)

    if provider_name == "groq":
        from app.core.llm.groq_provider import GroqProvider

        return GroqProvider(api_key=api_key or settings.GROQ_API_KEY)

    if provider_name == "ollama":
        # Only used if explicitly enabled by the user in settings
        from app.core.llm.ollama_provider import OllamaProvider

        return OllamaProvider(base_url=getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"))

    if provider_name == "openai":
        from app.core.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=api_key or settings.OPENAI_API_KEY)

    raise LLMConfigError(
        f"Unsupported LLM provider: {provider_name!r} (supported: {', '.join(SUPPORTED_PROVIDERS)})"
    )
