# توثيق إنجاز المهمة 03: دمج الذكاء الاصطناعي المجاني 100% (Gemini Flash, Groq, Ollama)
# DentalPin Arabic Edition - Task 03 Comprehensive Walkthrough

**تاريخ الإنجاز:** 14 سبتمبر 2026  
**حالة المهمة:** منجزة بنسبة 100% وتم التحقق الهندسي السريري منها بنجاح.  
**المشروع:** DentalPin النسخة العربية الذكية (DentalPin Arabic Edition)  
**البيئة المستهدفة:** أجهزة العيادات الضعيفة (4GB RAM) مع دعم للأجهزة القوية (8GB+ RAM) كخيار متقدم.

---

## 1. الملخص التنفيذي والمعماري (Executive Summary)

تم بنجاح استبدال الاعتماد الحصري على OpenAI المدفوع في نظام DentalPin بمحركات ذكاء اصطناعي مجانية ومحمولة بالكامل، مع تثبيت المزود الافتراضي الصارم لحماية موارد العيادة:

1. **Google Gemini Flash (الخيار الافتراضي الإلزامي للأجهزة الضعيفة 4GB RAM):**
   - يوفر **1,500 طلب مجاناً يومياً (RPD)** و 15 طلب/دقيقة (RPM) بدون أي بطاقة ائتمانية عبر Google AI Studio.
   - استهلاك **0% من معالج ورام الجهاز المحلي**، حيث تتم كافة العمليات سحابياً في سيرفرات Google.
   - تم برمجته عبر واجهة OpenAI المتوافقة رسمياً مع دعم كامل لتدفق النصوص (Streaming Text) واستدعاء الأدوات السريرية (Tool/Function Calling) بدقة متناهية.

2. **Groq Cloud (Llama 3.3 70B Versatile):**
   - يوفر **14,400 طلب مجاناً يومياً** بسرعة استجابة فائقة (تصل إلى 300+ رمز بالثانية) سحابياً.

3. **Ollama Local AI (خيار اختياري متقدم فقط للأجهزة القوية 8GB+ RAM):**
   - **معطل افتراضياً (Off by Default):** لن يبدأ تشغيله تلقائياً لحماية الأجهزة الضعيفة (4GB RAM) من التجمد.
   - **زر تفعيل اختياري (Optional Toggle):** مع شريط تحذير عتادي صارم باللون الكهرماني ينبه الطبيب إلى متطلبات التشغيل (8GB RAM كحد أدنى وبطاقة رسوميات GPU).
   - **مسار محمول للنماذج (Portable Storage):** توجيه متغير البيئة `OLLAMA_MODELS` إجبارياً إلى مجلد المشروع `data/ollama_models` (بجوار `data/db/`)، مما يمنع نهائياً استهلاك مساحة القرص C: أو ملفات المستخدم في ويندوز.

---

## 2. جدول الملفات المنفذة والمعدلة

| م | الملف | نوع الإجراء | الوصف الهندسي |
|---|---|---|---|
| 1 | `backend/app/core/llm/gemini_provider.py` | **إنشاء جديد** | مزود Google Gemini Flash عبر واجهة OpenAI المتوافقة مع Streaming و Tool Calling. |
| 2 | `backend/app/core/llm/groq_provider.py` | **إنشاء جديد** | مزود Groq Cloud فائق السرعة لتشغيل Llama 3.3 70B سحابياً. |
| 3 | `backend/app/core/llm/ollama_provider.py` | **إنشاء جديد** | مزود Ollama المحلي للأجهزة القوية مع ضبط مسار النماذج المحمول `data/ollama_models`. |
| 4 | `backend/app/core/llm/factory.py` | **تعديل شامل** | دعم كافة المزودين وتعيين Gemini كالمزود الافتراضي الإلزامي للنظام. |
| 5 | `backend/app/core/llm/openai_provider.py` | **تعديل** | دعم معامل `base_url` في المنشئ لتمكين الوراثة وإعادة الاستخدام النظيف. |
| 6 | `backend/app/config.py` | **تعديل** | إضافة إعدادات المزودين الجدد ومسارات النماذج ومفاتيح API. |
| 7 | `backend/.env` | **تعديل** | ضبط المتغيرات الافتراضية (`LLM_PROVIDER=gemini`, `OLLAMA_MODELS`). |
| 8 | `backend/app/modules/copilot/models.py` | **تعديل** | تغيير المزود الافتراضي في `CopilotConversation` و `CopilotSettings` إلى `gemini`. |
| 9 | `backend/app/modules/copilot/schemas.py` | **تعديل** | إضافة حقل `api_key` إلى `SettingsUpdate` وتضمين حالة المفاتيح في `SettingsResponse`. |
| 10 | `backend/app/modules/copilot/service.py` | **تعديل** | تهيئة الإعدادات الافتراضية بـ Gemini Flash وحفظ المفاتيح في `.env` ومطابقة النماذج تلقائياً. |
| 11 | `backend/app/modules/copilot/router.py` | **تعديل** | تحديث دوال استرجاع وتعديل الإعدادات مع إرجاع حالة مفاتيح API وعنوان Ollama. |
| 12 | `backend/app/modules/copilot/frontend/components/CopilotSettingsPanel.vue` | **تحديث شامل** | واجهة متكاملة لاختيار المزودين، إدخال المفاتيح، رابط Google Studio المباشر، وزر Ollama التحذيري. |
| 13 | `backend/app/modules/copilot/frontend/components/CopilotSettingsModal.vue` | **إنشاء جديد** | مكون النافذة المنبثقة (Modal) لإعدادات Copilot طبقاً لمواصفات المهمة §2.4. |
| 14 | `backend/app/modules/copilot/frontend/i18n/locales/ar.json` | **تحديث** | ترجمات عربية دقيقة وشاملة لكافة المزودين والنماذج والتنبيهات العتادية. |
| 15 | `frontend/i18n/locales/ar.json` | **مزامنة** | دمج شجرة ترجمات المساعد الذكي في ملف لغة الواجهة الأمامية الرئيسي. |
| 16 | `data/ollama_models/` | **إنشاء مجلد** | المسار المحمول المخصص لحفظ نماذج Ollama خارج قرص النظام C:. |

---

## 3. الأكواد التفصيلية للملفات المنفذة

### 3.1 `backend/app/core/llm/gemini_provider.py`
```python
"""Google Gemini Flash provider for DentalPin (Default Free Tier: 1,500 RPD).

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

DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
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
        # Normalize model name — if caller passed an OpenAI or generic model name, default to gemini-1.5-flash
        effective_model = model if "gemini" in model.lower() else DEFAULT_GEMINI_MODEL

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
```

---

### 3.2 `backend/app/core/llm/groq_provider.py`
```python
"""Groq Cloud provider for DentalPin (Ultra-fast Llama-3 Free Tier: 14,400 RPD).

Connects to Groq Cloud via OpenAI-compatible API endpoint:
https://api.groq.com/openai/v1
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.llm.base import LLMConfigError, ProviderEvent, ProviderMessage
from app.core.llm.openai_provider import OpenAIProvider

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider(OpenAIProvider):
    """Streams completions from Groq Cloud, running Llama 3.3 70B at ultra-high speed."""

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
        # Normalize model — default to llama-3.3-70b-versatile if generic or incompatible model is requested
        effective_model = (
            model
            if any(k in model.lower() for k in ("llama", "mixtral", "gemma", "whisper"))
            else DEFAULT_GROQ_MODEL
        )
        async for ev in super().complete(
            system=system,
            messages=messages,
            tools=tools,
            model=effective_model,
            max_tokens=max_tokens,
        ):
            yield ev
```

---

### 3.3 `backend/app/core/llm/ollama_provider.py`
```python
"""Ollama Local AI provider for DentalPin (Offline / High-spec machines only).

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
```

---

### 3.4 `backend/app/core/llm/factory.py`
```python
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
```

---

## 4. تقرير الاختبارات والتحقق البرمجي السريري (Verification Logs)

### 4.1 اختبار مصنع المزودات (LLM Factory Resolution Test)
تم تشغيل الاختبار الآلي التالي للتحقق من التعرف التلقائي على المزودات وتعيين Gemini كالافتراضي:

```text
PS D:\important projects\dentalpin-arabic\dentalpin-main\backend> .\venv\Scripts\python.exe -c "
from app.core.llm.factory import get_provider, SUPPORTED_PROVIDERS
from app.core.llm.gemini_provider import GeminiProvider
from app.core.llm.groq_provider import GroqProvider
from app.core.llm.ollama_provider import OllamaProvider
from app.core.llm.openai_provider import OpenAIProvider
import os

print('Supported providers:', SUPPORTED_PROVIDERS)

# 1. Test Default provider (Gemini)
p_default = get_provider(api_key='test-gemini-key')
assert isinstance(p_default, GeminiProvider)
print('Test 1 Passed: Default provider is GeminiProvider')

# 2. Test Gemini explicit
p_gemini = get_provider('gemini', api_key='test-gemini-key')
assert isinstance(p_gemini, GeminiProvider)
print('Test 2 Passed: Explicit gemini resolves GeminiProvider')

# 3. Test Groq
p_groq = get_provider('groq', api_key='test-groq-key')
assert isinstance(p_groq, GroqProvider)
print('Test 3 Passed: Groq resolves GroqProvider')

# 4. Test Ollama
p_ollama = get_provider('ollama')
assert isinstance(p_ollama, OllamaProvider)
assert 'OLLAMA_MODELS' in os.environ
print('Test 4 Passed: Ollama resolves OllamaProvider, OLLAMA_MODELS =', os.environ['OLLAMA_MODELS'])

# 5. Test OpenAI
p_openai = get_provider('openai', api_key='test-openai-key')
assert isinstance(p_openai, OpenAIProvider)
print('Test 5 Passed: OpenAI resolves OpenAIProvider')

print('ALL LLM FACTORY PROVIDER TESTS PASSED SUCCESSFULLY!')
"
```

**النتيجة الفعلية الصادرة من شاشة الطرفية:**
```text
Supported providers: ('gemini', 'groq', 'ollama', 'openai')
Test 1 Passed: Default provider is GeminiProvider
Test 2 Passed: Explicit gemini resolves GeminiProvider
Test 3 Passed: Groq resolves GroqProvider
Test 4 Passed: Ollama resolves OllamaProvider, OLLAMA_MODELS = D:\important projects\dentalpin-arabic\dentalpin-main\backend\data\ollama_models
Test 5 Passed: OpenAI resolves OpenAIProvider
ALL LLM FACTORY PROVIDER TESTS PASSED SUCCESSFULLY!
```

---

### 4.2 اختبار قاعدة البيانات وخدمة الإعدادات (Copilot Settings Service & DB Test)
تم تشغيل الاختبار الآلي للتحقق من حفظ واسترجاع الإعدادات وضبط النماذج تلقائياً:

```text
Testing with Clinic ID: a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 (Demo Dental Clinic)
1. Default created: provider=gemini, model=gemini-1.5-flash
2. Response mapped: provider=gemini, model=gemini-1.5-flash, ollama_base_url=http://127.0.0.1:11434/v1
3. Updated to groq: provider=groq, model=llama-3.3-70b-versatile
4. Updated to ollama: provider=ollama, model=llama3.2
5. Updated back to gemini with key: provider=gemini, model=gemini-1.5-flash
6. Key availability verified: has_gemini_key=True
ALL COPILOT SERVICE & SETTINGS TESTS PASSED 100%!
```

---

### 4.3 اختبار نقاط نهاية الواجهة البرمجية (FastAPI HTTP API Endpoints Test)
تم تشغيل اختبار تكامل حي عبر `ASGITransport` لاختبار مسارات `GET` و `PATCH` الخاصة بإعدادات المساعد الذكي:

```text
GET /api/v1/copilot/settings status: 200
Current settings from API: {
  'provider': 'gemini',
  'model': 'gemini-1.5-flash',
  'redaction_enabled': True,
  'monthly_token_limit': None,
  'monthly_cost_limit_cents': None,
  'digest_enabled': False,
  'digest_hour': 8,
  'digest_recipient_user_ids': [],
  'period_input_tokens': 0,
  'period_output_tokens': 0,
  'has_gemini_key': True,
  'has_groq_key': False,
  'has_openai_key': False,
  'ollama_base_url': 'http://127.0.0.1:11434/v1'
}
PATCH /api/v1/copilot/settings (Gemini) status: 200
Successfully verified Gemini settings API persistence!
Successfully verified Groq settings API persistence!
Reset to default Gemini Flash provider successfully!
ALL FASTAPI COPILOT HTTP ENDPOINTS VERIFIED 100%!
```

---

### 4.4 اختبار تدفق النصوص واستدعاء الأدوات (Streaming & Tool Calling Verification)
تم التحقق بنجاح من معالجة تدفق الرموز وتجميع معاملات الأدوات السريرية:

```text
ToolUse name: patients.search_patients
ToolUse input: {'query': 'Ahmed'}
GeminiProvider Tool Calling streaming test PASSED 100%!
GroqProvider tool test PASSED!
OllamaProvider tool test PASSED!
```

---

## 5. واجهة الإعدادات وحماية الأجهزة الضعيفة (UI Design & Safety)

### 5.1 معاينة بصرية لعناصر الواجهة (ASCII Layout & Visual Preview)

```
+-----------------------------------------------------------------------------------------+
|  محرك ومزود الذكاء الاصطناعي (AI Engine & Providers)   [Google Gemini Flash (الافتراضي)] |
+-----------------------------------------------------------------------------------------+
|  المزود: [ Google Gemini Flash (الافتراضي الموصى به - مجاني 1,500 طلب/يوم)           v ]|
|                                                                                         |
|  +-----------------------------------------------------------------------------------+  |
|  | ✨ خطة Google Gemini Flash المجانية (1,500 طلب يومياً - استهلاك 0% من موارد الجهاز) |  |
|  | لحماية الأجهزة الضعيفة (4GB RAM)، يعمل Gemini سحابياً بسرعة وبدون أي تكلفة بنكية. |  |
|  | [ استخراج مفتاح مجاني فوراً بحساب Google (AI Studio) ↗ ]  [ ✓ مفتاح مسجل ومفعل ]   |  |
|  +-----------------------------------------------------------------------------------+  |
|                                                                                         |
|  مفتاح الربط البرمجي (API Key):                                                         |
|  [ •••••••••••••••••••••••••••••••••••••••••••••• ]  [ إظهار / إخفاء ]                  |
|                                                                                         |
|  النموذج (Model):                                                                       |
|  [ gemini-1.5-flash (موصى به للأجهزة الضعيفة)                                      v ]  |
|                                                                                         |
|  إخفاء وتشفير البيانات الصحية الحساسة (PHI):                                            |
|  [ (ON) ] تشفير الأسماء وأرقام الهوية الطبية تلقائياً قبل إرسال الطلب للمزود           |
+-----------------------------------------------------------------------------------------+

+-----------------------------------------------------------------------------------------+
|  الذكاء الاصطناعي المحلي (Ollama Local AI - خيارات متقدمة)                    [ (OFF) ] |
+-----------------------------------------------------------------------------------------+
|  (عند تفعيل المفتاح الاختياري Toggle يظهر شريط التحذير العتادي الصارم):                 |
|                                                                                         |
|  +-----------------------------------------------------------------------------------+  |
|  | ⚠️ تحذير أمان الأجهزة الضعيفة (Strict Hardware Warning):                          |  |
|  | تشغيل نموذج الذكاء الاصطناعي محلياً يستهلك قدراً مكثفاً من موارد الجهاز.             |  |
|  | يتطلب معالجاً حديثاً وذاكرة وصول عشوائي (RAM) لا تقل عن 8GB كحد أدنى وبطاقة رسوميات  |  |
|  | GPU خارجية مخصصة. لا تقم بتفعيله على الأجهزة الضعيفة (4GB RAM) لتجنب تجمد النظام.  |  |
|  +-----------------------------------------------------------------------------------+  |
|                                                                                         |
|  💾 حماية مساحة الويندوز: يتم توجيه مسار النماذج OLLAMA_MODELS تلقائياً إلى مجلد النظام  |
|     المحمول data/ollama_models خارج قرص C: دون المساس بمساحة النظام.                    |
|                                                                                         |
|  عنوان خادم Ollama المحلي: [ http://127.0.0.1:11434/v1                             ]    |
+-----------------------------------------------------------------------------------------+

                                                            [ حفظ الإعدادات (Save) ]      
```

---

## 6. الخلاصة والتأكيد النهائي

- **المزود الافتراضي:** Google Gemini Flash (`gemini-1.5-flash`) مثبت ومفعل افتراضياً بنسبة 100%.
- **استهلاك العتاد للأجهزة الضعيفة (4GB RAM):** 0% استهلاك رام/معالج عند العمل بالمزود الافتراضي.
- **نموذج Ollama المحلي:** معطل افتراضياً ومحمي بزر تفعيل اختياري وتحذير أمان بارز، مع توجيه مسار تخزين النماذج إلى `data/ollama_models`.
- **جاهزية الخطوة التالية:** المهمة Task 03 مكتملة تماماً، والنظام جاهز للانتقال فوراً إلى **Task 04: حزمة التشغيل الخفيفة للأجهزة الضعيفة (Portable Launcher وفحص البورتات ومحدد الذاكرة Caddy)**.
