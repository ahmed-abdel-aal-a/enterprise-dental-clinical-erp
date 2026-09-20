# Task 03: دمج الذكاء الاصطناعي المجاني 100% (Gemini Flash, Groq, Ollama)

## 1. الهدف الهندسي وتحديد المزود الافتراضي
استبدال الاعتماد الحصري على OpenAI المدفوع في DentalPin بمحركات ذكاء اصطناعي مجانية تماماً:
1. **Google Gemini Flash Free Tier (الخيار الافتراضي الإلزامي للأجهزة الضعيفة):** 1,500 طلب يومياً مجاناً، يتجدد تلقائياً كل 24 ساعة بدون أي بطاقة بنكية، باستهلاك **0% من رام ومعالج الجهاز**.
2. **Groq Cloud (Llama 3.3):** 14,400 طلب يومياً مجاناً بسرعة استجابة خارقة ومجانية سحابياً.
3. **Ollama Local AI (ميزة اختيارية فقط للأجهزة القوية):**

> [!IMPORTANT]
> **تنبيه صارم بخصوص نموذج Ollama المحلي (Optional Toggle Only):**
> نموذج Ollama المحلي **لن يتم تشغيله افتراضياً على الإطلاق** على الأجهزة الضعيفة (4GB RAM)، لأنه يتطلب عتاداً قوياً (RAM 8GB+ مع كارت شاشة خارجي). تم إدراجه كـ **زر تفعيل اختياري (Optional Toggle)** داخل إعدادات البرنامج المتقدمة فقط للأطباء الذين يملكون أجهزة عمل قوية ويرغبون في العمل أوفلاين 100%. الخيار الافتراضي والأساسي الذي سيعمل به التطبيق فور تثبيته هو **Google Gemini Flash API** السحابي المجاني.

---

## 2. الأكواد الدقيقة التي سيتم كتابتها وتعديلها

### 2.1 إنشاء gemini_provider.py
المسار الجديد: ackend/app/core/llm/gemini_provider.py
يقوم بالاتصال بـ Google Gemini عبر واجهة OpenAI المتوافقة رسمياً مع دعم استدعاء الأدوات (Tool Calling) والـ Streaming:

`python
"Google Gemini Flash provider for DentalPin (Default Free Tier: 1500 RPD)."

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
from app.core.llm.openai_provider import _to_openai_messages, _sanitize_tool_schema


class GeminiProvider:
    "Streams completions from Google Gemini Flash via OpenAI compatibility endpoint."

    def __init__(self, *, api_key: str) -> None:
        if not api_key:
            raise LLMConfigError(Gemini provider requires GEMINI_API_KEY)
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=https://generativelanguage.googleapis.com/v1beta/openai/,
        )

    async def complete(
        self,
        *,
        system: str,
        messages: list[ProviderMessage],
        tools: list[dict],
        model: str = gemini-1.5-flash,
        max_tokens: int = 2048,
    ) -> AsyncIterator[ProviderEvent]:
        wire_messages = _to_openai_messages(system, messages)
        kwargs: dict[str, Any] = {
            model: model,
            messages: wire_messages,
            max_tokens: max_tokens,
            stream: True,
            stream_options: {include_usage: True},
        }
        if tools:
            kwargs[tools] = [_sanitize_tool_schema(t) for t in tools]
            kwargs[parallel_tool_calls] = False

        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.usage is not None:
                yield Usage(
                    input_tokens=chunk.usage.prompt_tokens,
                    output_tokens=chunk.usage.completion_tokens,
                )
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                yield TextDelta(text=delta.content)
            if delta.tool_calls:
                tc = delta.tool_calls[0]
                yield ToolUse(id=tc.id, name=tc.function.name, input=tc.function.arguments)
        yield Done(stop_reason=stop)
`

---

### 2.2 إنشاء groq_provider.py
المسار الجديد: ackend/app/core/llm/groq_provider.py
يقوم بالاتصال بـ Groq Cloud لتشغيل Llama 3.3 70B بسرعة فائقة ومجاناً:

`python
"Groq Cloud provider (Ultra-fast Llama-3 Free Tier: 14,400 RPD)."

from __future__ import annotations
from openai import AsyncOpenAI
from app.core.llm.base import LLMConfigError
from app.core.llm.openai_provider import OpenAIProvider


class GroqProvider(OpenAIProvider):
    def __init__(self, *, api_key: str) -> None:
        if not api_key:
            raise LLMConfigError(Groq provider requires GROQ_API_KEY)
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=https://api.groq.com/openai/v1,
        )
`

---

### 2.3 تعديل ackend/app/core/llm/factory.py
المسار: ackend/app/core/llm/factory.py
توسيع قائمة المزودين ليتعرف النظام على المزودات الجديدة تلقائياً، وتثبيت Gemini كالافتراضي:

`python
from __future__ import annotations
from app.config import settings
from app.core.llm.base import LLMConfigError, Provider

SUPPORTED_PROVIDERS = (gemini, groq, openai, ollama)


def get_provider(name: str | None = None, *, api_key: str | None = None) -> Provider:
    # الافتراضي الإلزامي هو gemini لحماية الأجهزة الضعيفة
    provider_name = (name or settings.LLM_PROVIDER or gemini).lower()
    
    if provider_name == gemini:
        from app.core.llm.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=api_key or settings.GEMINI_API_KEY)

    if provider_name == groq:
        from app.core.llm.groq_provider import GroqProvider
        return GroqProvider(api_key=api_key or settings.GROQ_API_KEY)

    if provider_name == ollama:
        # لا يُستدعى إلا إذا قام المستخدم بتفعيله يدوياً من الإعدادات
        from app.core.llm.ollama_provider import OllamaProvider
        return OllamaProvider(base_url=settings.OLLAMA_BASE_URL)

    if provider_name == openai:
        from app.core.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=api_key or settings.OPENAI_API_KEY)

    raise LLMConfigError(fUnsupported LLM provider: {provider_name!r})
`

---

### 2.4 تعديل واجهة إعدادات العيادة لإدخال المفتاح وزر Ollama الاختياري
المسار: ackend/app/modules/copilot/frontend/components/CopilotSettingsModal.vue
* **المزود الافتراضي:** Google Gemini Flash (موصى به - مجاني وسريع للأجهزة الضعيفة).
* **خانة إدخال المفتاح:** رابط مباشر istudio.google.com لاستخراج المفتاح المجاني بحساب Gmail.
* **قسم متقدم (للمحترفين فقط):** خيار تفعيل Ollama Local مع تنبيه تحذيري: *يتطلب رامات 8GB أو كارت شاشة خارجي*.
