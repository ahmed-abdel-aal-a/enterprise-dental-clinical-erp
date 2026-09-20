// Copilot chat state — a single shared session per browser tab (useState
// keeps it SSR-safe and shared between the drawer and the /copilot page).

import type { ApiResponse } from '~~/app/types'

export interface ToolUiMessage {
  kind: 'tool'
  callId: string
  name: string
  status: 'running' | 'done' | 'failed'
  args?: Record<string, unknown>
  result?: unknown
}

export interface ConfirmUiMessage {
  kind: 'confirmation'
  callId: string
  name: string
  args: Record<string, unknown>
  resolved?: 'confirm' | 'reject'
}

export interface TextUiMessage {
  kind: 'text'
  role: 'user' | 'assistant'
  text: string
  streaming?: boolean
}

export type CopilotUiMessage = TextUiMessage | ToolUiMessage | ConfirmUiMessage

interface PendingConfirmation {
  callId: string
  name: string
  args: Record<string, unknown>
}

export function useCopilot() {
  const api = useApi()
  const route = useRoute()
  const { stream } = useCopilotStream()
  const dataBus = useDataBus()

  const open = useState<boolean>('copilot:open', () => false)
  const conversationId = useState<string | null>('copilot:conversation', () => null)
  const messages = useState<CopilotUiMessage[]>('copilot:messages', () => [])
  const busy = useState<boolean>('copilot:busy', () => false)
  const pending = useState<PendingConfirmation | null>('copilot:pending', () => null)
  // Live activity under the composer: 'working' while a tool runs, 'writing'
  // once the assistant starts streaming text, null otherwise.
  const phase = useState<'working' | 'writing' | null>('copilot:phase', () => null)
  // id -> human label, harvested from read tools, so confirmation cards can
  // show "María García" where the args only carry a patient_id.
  const nameCache = useState<Record<string, string>>('copilot:names', () => ({}))

  function toggle() {
    open.value = !open.value
  }

  function captureContext(): Record<string, unknown> {
    const ctx: Record<string, unknown> = { screen: route.path }
    const patientId = route.params.id
    if (typeof patientId === 'string' && route.path.startsWith('/patients/')) {
      ctx.patient_id = patientId
    }
    return ctx
  }

  async function ensureSession(): Promise<void> {
    if (conversationId.value) return
    const res = await api.post<ApiResponse<{ id: string }>>('/api/v1/copilot/sessions', {
      context: captureContext()
    })
    conversationId.value = res.data.id
  }

  // Harvest id -> name pairs from read-tool results into nameCache.
  function cacheNames(toolName: string, result: unknown): void {
    if (!result || typeof result !== 'object') return
    const r = result as Record<string, unknown>
    const short = toolName.split('.').pop()
    const put = (id: unknown, label: unknown) => {
      if (typeof id === 'string' && typeof label === 'string') nameCache.value[id] = label
    }
    const rows = (key: string): Record<string, unknown>[] =>
      Array.isArray(r[key]) ? (r[key] as Record<string, unknown>[]) : []

    if (short === 'search_patients') rows('patients').forEach(p => put(p.id, p.full_name))
    else if (short === 'get_patient') put(r.id, r.full_name)
    else if (short === 'create_patient') put(r.id, `${r.first_name ?? ''} ${r.last_name ?? ''}`.trim())
    else if (short === 'get_day_overview')
      rows('appointments').forEach(a => put(a.patient_id, a.patient_name))
    else if (short === 'get_appointment') put(r.patient_id, r.patient_name)
    else if (short === 'list_professionals')
      rows('professionals').forEach(p => put(p.id, p.professional_name))
    else if (short === 'list_cabinets') rows('cabinets').forEach(c => put(c.id, c.name))
    else if (short === 'list_branches') rows('branches').forEach(b => put(b.id, b.name))
    else if (short === 'create_invoice' || short === 'get_invoice') {
      put(r.patient_id, r.patient_name)
    }
  }

  function lastStreamingAssistant(): TextUiMessage | null {
    const last = messages.value[messages.value.length - 1]
    if (last && last.kind === 'text' && last.role === 'assistant' && last.streaming) return last
    return null
  }

  function handle(event: string, data: Record<string, unknown>): void {
    if (event === 'token') {
      phase.value = 'writing'
      const current = lastStreamingAssistant()
      if (current) current.text += String(data.text ?? '')
      else messages.value.push({ kind: 'text', role: 'assistant', text: String(data.text ?? ''), streaming: true })
    } else if (event === 'tool_call') {
      phase.value = 'working'
      messages.value.push({
        kind: 'tool',
        callId: String(data.call_id),
        name: String(data.name),
        status: 'running',
        args: (data.arguments as Record<string, unknown>) ?? {}
      })
    } else if (event === 'tool_result') {
      const tool = [...messages.value].reverse().find(
        (m): m is ToolUiMessage => m.kind === 'tool' && m.callId === data.call_id
      )
      if (tool) {
        tool.status = data.ok ? 'done' : 'failed'
        tool.result = data.result
        if (data.ok) cacheNames(tool.name, data.result)
      }
    } else if (event === 'confirmation_required') {
      if (data.display_names && typeof data.display_names === 'object') {
        for (const [id, label] of Object.entries(data.display_names as Record<string, string>)) {
          if (typeof label === 'string' && label) {
            nameCache.value[id] = label
          }
        }
      }
      const c: ConfirmUiMessage = {
        kind: 'confirmation',
        callId: String(data.call_id),
        name: String(data.name),
        args: (data.arguments as Record<string, unknown>) ?? {}
      }
      messages.value.push(c)
      pending.value = { callId: c.callId, name: c.name, args: c.args }
    } else if (event === 'done') {
      phase.value = null
      const current = lastStreamingAssistant()
      if (current) current.streaming = false
    } else if (event === 'budget_exceeded') {
      messages.value.push({ kind: 'text', role: 'assistant', text: '⚠️ budget', streaming: false })
    } else if (event === 'error') {
      messages.value.push({ kind: 'text', role: 'assistant', text: `⚠️ ${data.detail ?? ''}`, streaming: false })
    }
  }

  async function send(text: string): Promise<void> {
    if (busy.value) return
    const outbox = useOutbox()
    const nightCopilot = useNightCopilot()
    const config = useRuntimeConfig()
    const edgeWorkerUrl = (config.public.edgeWorkerUrl || '').replace(/\/$/, '')

    messages.value.push({ kind: 'text', role: 'user', text })
    busy.value = true

    const isDemo = import.meta.client && (
      localStorage.getItem('dentapex_demo_mode') === 'true' ||
      window.location.hostname.includes('pages.dev') ||
      window.location.hostname.includes('cloudflare') ||
      !config.public.apiBaseUrl
    )

    // In demo mode, bypass local backend completely and stream directly via Cloudflare Function
    if (isDemo) {
      outbox.isOfflineMode.value = true
      phase.value = 'writing'
      messages.value.push({ kind: 'text', role: 'assistant', text: '', streaming: true })

      const history = messages.value
        .filter((msg): msg is TextUiMessage => msg.kind === 'text')
        .map(msg => ({ role: msg.role, content: msg.text }))

      await nightCopilot.streamNightChat(
        text,
        history,
        (chunk) => {
          const last = lastStreamingAssistant()
          if (last) last.text += chunk
        },
        () => {
          const last = lastStreamingAssistant()
          if (last) last.streaming = false
          busy.value = false
          phase.value = null
        },
        (err) => {
          const last = lastStreamingAssistant()
          if (last) {
            last.text += `\n${err}`
            last.streaming = false
          }
          busy.value = false
          phase.value = null
        }
      )
      return
    }

    try {
      await ensureSession()
      await stream(
        `/api/v1/copilot/sessions/${conversationId.value}/messages`,
        { content: text },
        {
          onEvent: (event, data) => {
            outbox.isOfflineMode.value = false
            handle(event, data)
          },
          onError: async () => {
            if (edgeWorkerUrl || typeof window !== 'undefined') {
              outbox.isOfflineMode.value = true
              phase.value = 'writing'
              messages.value.push({ kind: 'text', role: 'assistant', text: '', streaming: true })

              const history = messages.value
                .filter((msg): msg is TextUiMessage => msg.kind === 'text')
                .map(msg => ({ role: msg.role, content: msg.text }))

              await nightCopilot.streamNightChat(
                text,
                history,
                (chunk) => {
                  const last = lastStreamingAssistant()
                  if (last) last.text += chunk
                },
                () => {
                  const last = lastStreamingAssistant()
                  if (last) last.streaming = false
                  busy.value = false
                  phase.value = null
                },
                (err) => {
                  const last = lastStreamingAssistant()
                  if (last) {
                    last.text += `\n${err}`
                    last.streaming = false
                  }
                  busy.value = false
                  phase.value = null
                }
              )
            } else {
              phase.value = null
              busy.value = false
              messages.value.push({
                kind: 'text',
                role: 'assistant',
                text: 'تعذر إكمال طلبك حالياً. يرجى المحاولة بعد قليل.',
                streaming: false
              })
            }
          }
        }
      )
    } catch {
      if (edgeWorkerUrl || typeof window !== 'undefined') {
        outbox.isOfflineMode.value = true
        phase.value = 'writing'
        messages.value.push({ kind: 'text', role: 'assistant', text: '', streaming: true })

        const history = messages.value
          .filter((msg): msg is TextUiMessage => msg.kind === 'text')
          .map(msg => ({ role: msg.role, content: msg.text }))

        await nightCopilot.streamNightChat(
          text,
          history,
          (chunk) => {
            const last = lastStreamingAssistant()
            if (last) last.text += chunk
          },
          () => {
            const last = lastStreamingAssistant()
            if (last) last.streaming = false
            busy.value = false
            phase.value = null
          },
          (err) => {
            const last = lastStreamingAssistant()
            if (last) {
              last.text += `\n${err}`
              last.streaming = false
            }
            busy.value = false
            phase.value = null
          }
        )
      } else {
        phase.value = null
        busy.value = false
        messages.value.push({
          kind: 'text',
          role: 'assistant',
          text: 'تعذر الاتصال بخادم العيادة حالياً. يرجى التأكد من تشغيل جهاز العيادة.',
          streaming: false
        })
      }
    } finally {
      busy.value = false
      phase.value = null
    }
  }

  async function confirm(callId: string, decision: 'confirm' | 'reject'): Promise<void> {
    if (busy.value) return
    const card = messages.value.find(
      (m): m is ConfirmUiMessage => m.kind === 'confirmation' && m.callId === callId
    )
    if (card) card.resolved = decision
    pending.value = null
    busy.value = true
    await stream(
      `/api/v1/copilot/sessions/${conversationId.value}/confirmations/${callId}`,
      { decision },
      { onEvent: handle, onError: m => handle('error', { detail: m }) }
    )
    busy.value = false
    phase.value = null

    // A confirmed write mutated the clinic's data, but the view that owns
    // it (e.g. the agenda) doesn't know. Announce the mutated module's
    // namespace on the data bus so its page can refetch. Tool names are
    // ``{module}.{tool}`` — forward the module namespace, never a hardcoded
    // consumer, so copilot stays decoupled from every module.
    const tool = messages.value.find(
      (m): m is ToolUiMessage => m.kind === 'tool' && m.callId === callId
    )
    if (decision === 'confirm' && tool?.status === 'done') {
      const namespace = tool.name.split('.')[0]
      if (namespace) dataBus.publish(namespace)
    }
  }

  function reset(): void {
    conversationId.value = null
    messages.value = []
    pending.value = null
    phase.value = null
  }

  return { open, messages, busy, pending, phase, nameCache, toggle, send, confirm, reset }
}
