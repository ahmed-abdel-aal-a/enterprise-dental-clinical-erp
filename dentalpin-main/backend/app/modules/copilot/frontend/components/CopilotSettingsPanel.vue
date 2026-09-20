<script setup lang="ts">
// Copilot settings: Multi-provider AI (Gemini Flash default, Groq, Ollama local toggle, OpenAI) + Morning digest.
// Mounted at /settings/integrations/copilot via the settings registry.
import type { ApiResponse } from '~~/app/types'
import { errorDetail } from '~~/app/utils/error'

interface CopilotSettings {
  provider: string
  model: string
  redaction_enabled: boolean
  digest_enabled: boolean
  digest_hour: number
  digest_recipient_user_ids: string[]
  has_gemini_key?: boolean
  has_groq_key?: boolean
  has_openai_key?: boolean
  ollama_base_url?: string
}

interface ToolStat { tool_name: string, calls: number, errors: number }
interface CopilotMetrics {
  window_days: number
  total_tool_calls: number
  failed_tool_calls: number
  error_rate: number
  avg_execution_ms: number
  conversations: number
  top_tools: ToolStat[]
  period_input_tokens: number
  period_output_tokens: number
  monthly_token_limit: number | null
  token_usage_pct: number | null
}

const { t } = useI18n()

function toolDisplayName(name: string): string {
  const i18nKey = name.replace(/\./g, '_')
  const key = `copilot.settings.metrics.toolNames.${i18nKey}`
  const translated = t(key)
  return translated !== key ? translated : name
}

const toast = useToast()
const api = useApi()
const { users, fetchUsers } = useUsers()

const settings = ref<CopilotSettings | null>(null)
const metrics = ref<CopilotMetrics | null>(null)
const isLoading = ref(false)
const isSaving = ref(false)

// AI Provider state
const apiKeyInput = ref('')
const showApiKey = ref(false)
const ollamaEnabled = ref(false)

const providerOptions = computed(() => {
  const options = [
    {
      label: t('copilot.settings.engine.providers.gemini'),
      value: 'gemini',
      description: 'Google Gemini Flash (1500 RPD Free - 0% RAM/CPU)'
    },
    {
      label: t('copilot.settings.engine.providers.groq'),
      value: 'groq',
      description: 'Groq Cloud Llama 3.3 (14,400 RPD Free)'
    },
    {
      label: t('copilot.settings.engine.providers.openai'),
      value: 'openai',
      description: 'OpenAI GPT-4o-mini / GPT-5.4-mini (Paid)'
    }
  ]
  if (ollamaEnabled.value) {
    options.splice(2, 0, {
      label: t('copilot.settings.engine.providers.ollama'),
      value: 'ollama',
      description: 'Ollama Local AI (Offline - Requires 8GB+ RAM)'
    })
  }
  return options
})

const modelOptions = computed(() => {
  if (!settings.value) return []
  const provider = settings.value.provider
  if (provider === 'gemini') {
    return [
      { label: 'gemini-3.6-flash (موصى به للأجهزة الضعيفة)', value: 'gemini-3.6-flash' },
      { label: 'gemini-2.5-flash', value: 'gemini-2.5-flash' }
    ]
  }
  if (provider === 'groq') {
    return [
      { label: 'openai/gpt-oss-120b (النموذج الذكي الأساسي - 120B عالي الدقة)', value: 'openai/gpt-oss-120b' },
      { label: 'qwen/qwen3.8-27b (نموذج Qwen 3.8 27B فائق السرعة والذكاء)', value: 'qwen/qwen3.8-27b' },
      { label: 'openai/gpt-oss-20b (نموذج 20B خفيف وفائق السرعة)', value: 'openai/gpt-oss-20b' }
    ]
  }
  if (provider === 'ollama') {
    return [
      { label: 'llama3.2 (3B - مخصص للأجهزة المتوسطة)', value: 'llama3.2' },
      { label: 'llama3.1 (8B)', value: 'llama3.1' },
      { label: 'mistral (7B)', value: 'mistral' }
    ]
  }
  return [
    { label: 'gpt-4o-mini', value: 'gpt-4o-mini' },
    { label: 'gpt-5.4-mini', value: 'gpt-5.4-mini' }
  ]
})

const hourOptions = Array.from({ length: 24 }, (_, h) => ({
  label: `${String(h).padStart(2, '0')}:00`,
  value: h
}))

const recipientOptions = computed(() =>
  users.value.map(u => ({
    label: `${u.first_name} ${u.last_name}`.trim() || u.email,
    value: u.id
  }))
)

const tokensUsedPct = computed(() =>
  metrics.value?.token_usage_pct != null ? Math.round(metrics.value.token_usage_pct * 100) : null
)
const errorRatePct = computed(() =>
  metrics.value ? Math.round(metrics.value.error_rate * 100) : 0
)

function onProviderChange(newProvider: string) {
  if (!settings.value) return
  settings.value.provider = newProvider
  if (newProvider === 'gemini') {
    settings.value.model = 'gemini-3.6-flash'
  } else if (newProvider === 'groq') {
    settings.value.model = 'openai/gpt-oss-120b'
  } else if (newProvider === 'ollama') {
    settings.value.model = 'llama3.2'
  } else if (newProvider === 'openai') {
    settings.value.model = 'gpt-4o-mini'
  }
  apiKeyInput.value = ''
}

function onOllamaToggle(val: boolean) {
  ollamaEnabled.value = val
  if (!val && settings.value && settings.value.provider === 'ollama') {
    // Revert to gemini default when disabling local Ollama
    onProviderChange('gemini')
  } else if (val && settings.value) {
    settings.value.provider = 'ollama'
    settings.value.model = 'llama3.2'
  }
}

async function load() {
  isLoading.value = true
  try {
    const [res] = await Promise.all([
      api.get<ApiResponse<CopilotSettings>>('/api/v1/copilot/settings'),
      fetchUsers()
    ])
    settings.value = res.data
    ollamaEnabled.value = res.data.provider === 'ollama'

    try {
      const m = await api.get<ApiResponse<CopilotMetrics>>('/api/v1/copilot/metrics?days=30')
      metrics.value = m.data
    } catch {
      metrics.value = null
    }
  } finally {
    isLoading.value = false
  }
}

onMounted(load)

async function save() {
  if (!settings.value || isSaving.value) return
  isSaving.value = true
  try {
    const payload: Record<string, any> = {
      provider: settings.value.provider,
      model: settings.value.model,
      redaction_enabled: settings.value.redaction_enabled,
      digest_enabled: settings.value.digest_enabled,
      digest_hour: settings.value.digest_hour,
      digest_recipient_user_ids: settings.value.digest_recipient_user_ids
    }
    if (apiKeyInput.value.trim()) {
      payload.api_key = apiKeyInput.value.trim()
    }

    const res = await api.patch<ApiResponse<CopilotSettings>>('/api/v1/copilot/settings', payload)
    settings.value = res.data
    apiKeyInput.value = ''
    toast.add({ title: t('copilot.settings.saved'), color: 'success' })
  } catch (e) {
    toast.add({ title: t('common.error'), description: errorDetail(e), color: 'error' })
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <USkeleton
      v-if="isLoading && !settings"
      class="h-40 w-full"
    />

    <template v-if="settings">
      <!-- AI Engine & Provider Configuration Card -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-base">
                {{ t('copilot.settings.engine.title') }}
              </p>
              <p class="text-sm text-muted">
                {{ t('copilot.settings.engine.description') }}
              </p>
            </div>
            <UBadge
              v-if="settings.provider === 'gemini'"
              color="success"
              variant="subtle"
            >
              Google Gemini Flash (الافتراضي الموصى به)
            </UBadge>
          </div>
        </template>

        <div class="flex flex-col gap-5">
          <!-- Provider Selection -->
          <UFormField :label="t('copilot.settings.engine.provider')">
            <USelect
              :model-value="settings.provider"
              :items="providerOptions"
              class="w-full sm:w-96"
              @update:model-value="onProviderChange"
            />
          </UFormField>

          <!-- Gemini Free Tier Box -->
          <div
            v-if="settings.provider === 'gemini'"
            class="rounded-lg border border-emerald-200 dark:border-emerald-800/50 bg-emerald-50 dark:bg-emerald-950/20 p-4 text-sm flex flex-col gap-3"
          >
            <div class="flex items-center justify-between">
              <span class="font-semibold text-emerald-800 dark:text-emerald-300">
                ✨ خطة Google Gemini Flash المجانية (1,500 طلب يومياً - استهلاك 0% من موارد الجهاز)
              </span>
              <UBadge
                :color="settings.has_gemini_key ? 'success' : 'warning'"
                variant="soft"
              >
                {{ settings.has_gemini_key ? t('copilot.settings.engine.apiKeyConfigured') : t('copilot.settings.engine.apiKeyMissing') }}
              </UBadge>
            </div>
            <p class="text-emerald-700 dark:text-emerald-400 text-xs">
              لحماية الأجهزة الضعيفة (4GB RAM)، يعمل Gemini سحابياً بسرعة خارقة وبدون أي تكلفة أو بطاقة بنكية.
            </p>
            <div class="flex flex-wrap items-center gap-3">
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium transition"
              >
                <span>{{ t('copilot.settings.engine.getGeminiKey') }}</span>
                <span>↗</span>
              </a>
            </div>
          </div>

          <!-- Groq Free Tier Box -->
          <div
            v-if="settings.provider === 'groq'"
            class="rounded-lg border border-sky-200 dark:border-sky-800/50 bg-sky-50 dark:bg-sky-950/20 p-4 text-sm flex flex-col gap-3"
          >
            <div class="flex items-center justify-between">
              <span class="font-semibold text-sky-800 dark:text-sky-300">
                ⚡ مزود Groq Cloud (سرعة فائقة - 14,400 طلب يومياً مجاناً)
              </span>
              <UBadge
                :color="settings.has_groq_key ? 'success' : 'warning'"
                variant="soft"
              >
                {{ settings.has_groq_key ? t('copilot.settings.engine.apiKeyConfigured') : t('copilot.settings.engine.apiKeyMissing') }}
              </UBadge>
            </div>
            <div class="flex flex-wrap items-center gap-3">
              <a
                href="https://console.groq.com/keys"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-700 text-white text-xs font-medium transition"
              >
                <span>{{ t('copilot.settings.engine.getGroqKey') }}</span>
                <span>↗</span>
              </a>
            </div>
          </div>

          <!-- API Key Input Field (For Gemini, Groq, OpenAI) -->
          <UFormField
            v-if="settings.provider !== 'ollama'"
            :label="t('copilot.settings.engine.apiKey')"
            :help="settings.provider === 'gemini' ? 'مفتاح API الخاص بك مشفر محلياً ولا يغادر الخادم.' : ''"
          >
            <div class="flex items-center gap-2 max-w-md">
              <UInput
                v-model="apiKeyInput"
                :type="showApiKey ? 'text' : 'password'"
                :placeholder="t('copilot.settings.engine.apiKeyPlaceholder')"
                class="w-full font-mono text-sm"
              />
              <UButton
                variant="ghost"
                color="neutral"
                size="sm"
                @click="showApiKey = !showApiKey"
              >
                {{ showApiKey ? 'إخفاء' : 'إظهار' }}
              </UButton>
            </div>
          </UFormField>

          <!-- Model Selection -->
          <UFormField :label="t('copilot.settings.engine.model')">
            <USelect
              v-model="settings.model"
              :items="modelOptions"
              class="w-full sm:w-80 font-mono text-sm"
            />
          </UFormField>

          <!-- PHI Redaction Toggle -->
          <UFormField
            :label="t('copilot.settings.engine.redaction')"
            help="تشفير الأسماء وأرقام الهوية الطبية تلقائياً قبل إرسال الطلب للمزود."
          >
            <USwitch v-model="settings.redaction_enabled" />
          </UFormField>
        </div>
      </UCard>

      <!-- Ollama Local AI Card (Advanced Protection Toggle) -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <p class="font-medium text-base">
                {{ t('copilot.settings.engine.ollama.title') }}
              </p>
              <p class="text-sm text-muted">
                {{ t('copilot.settings.engine.ollama.enableToggle') }}
              </p>
            </div>
            <USwitch
              :model-value="ollamaEnabled"
              @update:model-value="onOllamaToggle"
            />
          </div>
        </template>

        <div
          v-if="ollamaEnabled"
          class="flex flex-col gap-4"
        >
          <!-- Strict Hardware Warning Banner -->
          <div class="rounded-lg border-2 border-amber-400 bg-amber-50 dark:bg-amber-950/40 p-4 text-amber-900 dark:text-amber-200">
            <div class="flex items-start gap-3">
              <span class="text-2xl">⚠️</span>
              <div class="flex flex-col gap-1 text-sm">
                <span class="font-bold">تحذير أمان الأجهزة الضعيفة (Strict Hardware Warning):</span>
                <p class="leading-relaxed">
                  {{ t('copilot.settings.engine.ollama.warning') }}
                </p>
              </div>
            </div>
          </div>

          <!-- Portable Storage Path Notice -->
          <div class="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-900 p-3 text-xs flex items-center gap-2">
            <span>💾</span>
            <span>{{ t('copilot.settings.engine.ollama.portableNotice') }}</span>
          </div>

          <UFormField
            :label="t('copilot.settings.engine.ollama.baseUrl')"
            help="يجب تشغيل خادم Ollama المحلي على هذا العنوان قبل إرسال المحادثات."
          >
            <UInput
              model-value="http://127.0.0.1:11434/v1"
              readonly
              class="w-full sm:w-80 font-mono text-sm"
            />
          </UFormField>
        </div>
        <div
          v-else
          class="text-sm text-muted"
        >
          الذكاء الاصطناعي المحلي معطل افتراضياً لحماية أجهزة العيادة الضعيفة. قم بتفعيله فقط إذا كان جهازك مزوداً برامات 8GB+ ومعالج قوي.
        </div>
      </UCard>

      <!-- Morning Digest Card -->
      <UCard>
        <template #header>
          <div>
            <p class="font-medium text-base">
              {{ t('copilot.settings.digest.title') }}
            </p>
            <p class="text-sm text-muted">
              {{ t('copilot.settings.digest.description') }}
            </p>
          </div>
        </template>

        <div class="flex flex-col gap-4">
          <UFormField :label="t('copilot.settings.digest.enabled')">
            <USwitch v-model="settings.digest_enabled" />
          </UFormField>

          <UFormField
            v-if="settings.digest_enabled"
            :label="t('copilot.settings.digest.hour')"
            :help="t('copilot.settings.digest.hourHelp')"
          >
            <USelect
              v-model="settings.digest_hour"
              :items="hourOptions"
              class="w-full sm:w-40"
            />
          </UFormField>

          <UFormField
            v-if="settings.digest_enabled"
            :label="t('copilot.settings.digest.recipients')"
            :help="t('copilot.settings.digest.recipientsHelp')"
          >
            <USelectMenu
              v-model="settings.digest_recipient_user_ids"
              :items="recipientOptions"
              value-key="value"
              multiple
              :placeholder="t('copilot.settings.digest.recipientsPlaceholder')"
              class="w-full sm:w-80"
            />
          </UFormField>
        </div>
      </UCard>

      <!-- Usage Metrics Card -->
      <UCard v-if="metrics">
        <template #header>
          <div>
            <p class="font-medium text-base">
              {{ t('copilot.settings.metrics.title') }}
            </p>
            <p class="text-sm text-muted">
              {{ t('copilot.settings.metrics.description', { days: metrics.window_days }) }}
            </p>
          </div>
        </template>

        <div class="flex flex-col gap-4">
          <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p class="text-2xl font-semibold">
                {{ metrics.total_tool_calls }}
              </p>
              <p class="text-xs text-muted">
                {{ t('copilot.settings.metrics.toolCalls') }}
              </p>
            </div>
            <div>
              <p
                class="text-2xl font-semibold"
                :class="errorRatePct > 10 ? 'text-error' : ''"
              >
                {{ errorRatePct }}%
              </p>
              <p class="text-xs text-muted">
                {{ t('copilot.settings.metrics.errorRate') }}
              </p>
            </div>
            <div>
              <p class="text-2xl font-semibold">
                {{ metrics.avg_execution_ms }} ms
              </p>
              <p class="text-xs text-muted">
                {{ t('copilot.settings.metrics.avgLatency') }}
              </p>
            </div>
            <div>
              <p class="text-2xl font-semibold">
                {{ metrics.conversations }}
              </p>
              <p class="text-xs text-muted">
                {{ t('copilot.settings.metrics.conversations') }}
              </p>
            </div>
          </div>

          <div v-if="tokensUsedPct !== null">
            <div class="mb-1 flex justify-between text-sm">
              <span class="text-muted">{{ t('copilot.settings.metrics.tokenBudget') }}</span>
              <span>{{ tokensUsedPct }}%</span>
            </div>
            <UProgress
              :model-value="tokensUsedPct"
              :color="tokensUsedPct >= 80 ? 'warning' : 'primary'"
            />
          </div>

          <div v-if="metrics.top_tools.length">
            <p class="mb-2 text-sm font-medium">
              {{ t('copilot.settings.metrics.topTools') }}
            </p>
            <div class="flex flex-col gap-1 text-sm">
              <div
                v-for="tool in metrics.top_tools"
                :key="tool.tool_name"
                class="flex justify-between"
              >
                <span class="font-mono text-xs">{{ toolDisplayName(tool.tool_name) }}</span>
                <span class="text-muted">
                  {{ tool.calls }}
                  <template v-if="tool.errors">
                    · <span class="text-error">{{ tool.errors }} err</span>
                  </template>
                </span>
              </div>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Global Save Action -->
      <div class="flex justify-end gap-3 sticky bottom-4 bg-background/80 backdrop-blur p-3 rounded-lg border shadow-sm">
        <UButton
          size="lg"
          color="primary"
          :loading="isSaving"
          @click="save"
        >
          {{ t('common.save') }}
        </UButton>
      </div>
    </template>
  </div>
</template>
