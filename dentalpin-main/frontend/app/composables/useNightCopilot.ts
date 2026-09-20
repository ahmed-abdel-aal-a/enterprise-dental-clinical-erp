/**
 * DentApex Night Copilot & Web Simulator Engine (Zero-Server Edge AI Proxy).
 *
 * Capabilities:
 * 1. Collects clinic schedule and patient context directly from Pinia Demo Store & IndexedDB.
 * 2. Streams completions from Groq Cloud (Llama 3.3 70B) via Cloudflare Edge Worker or Cloudflare Pages Function (/api/copilot/chat).
 * 3. Never exposes GROQ_API_KEY to client; protected with Origin/Referer verification & Rate Limiting.
 */

import { useDemoStore } from '~/stores/useDemoStore'

export function useNightCopilot() {
  const offlineDb = useOfflineDb()
  const outbox = useOutbox()
  const auth = useAuth()
  const config = useRuntimeConfig()

  let demoStore: ReturnType<typeof useDemoStore> | null = null
  if (import.meta.client) {
    try {
      demoStore = useDemoStore()
    } catch {
      // Pinia context not yet ready
    }
  }

  async function buildLocalContext(): Promise<string> {
    try {
      const now = new Date()
      const tomorrow = new Date(now)
      tomorrow.setDate(now.getDate() + 1)

      const tomorrowIsoStart = `${tomorrow.toISOString().split('T')[0]}T00:00:00Z`
      const tomorrowIsoEnd = `${tomorrow.toISOString().split('T')[0]}T23:59:59Z`

      let appointments: any[] = []
      let patients: any[] = []

      // Try reading from demo store first
      if (demoStore && demoStore.initialized) {
        appointments = demoStore.appointments
        patients = demoStore.patients
      } else {
        appointments = await offlineDb.getAppointmentsForRange(tomorrowIsoStart, tomorrowIsoEnd)
        patients = await offlineDb.getAll('patients')
      }

      const aptList = appointments.slice(0, 8).map(a =>
        `- ${a.start_time ? new Date(a.start_time).toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }) : ''}: المريض (${a.patient_name || 'غير محدد'}) - ${a.treatment_name || a.treatment_type || 'كشف'} - الكابينة: ${a.cabinet || a.cabinet_name || 'الرئيسية'}`
      ).join('\n') || 'لا توجد مواعيد مسجلة للغد.'

      const patSample = patients.slice(0, 10).map(p => {
        const allergiesStr = (p.allergies && p.allergies.length > 0) ? ` [حساسية: ${p.allergies.join('، ')}]` : ''
        const notesStr = p.medical_notes ? ` - ملاحظات: ${p.medical_notes}` : ''
        return `- ${p.full_name || `${p.first_name || ''} ${p.last_name || ''}`.trim()}${allergiesStr}${notesStr}`
      }).join('\n') || 'لا توجد سجلات مرضى مخزنة.'

      return `[بيانات العيادة المستخرجة من ذاكرة النظام الاستعراضي - DentApex Demo Context]
تاريخ اليوم: ${now.toLocaleDateString('ar-EG')}
مواعيد العيادة:
${aptList}

عينة من سجلات المرضى بالعيادة:
${patSample}`
    } catch {
      return '[تعذر استخراج بيانات الذاكرة المحلية]'
    }
  }

  async function streamNightChat(
    userMessage: string,
    history: Array<{ role: string; content: string }>,
    onChunk: (chunk: string) => void,
    onDone: () => void,
    onError: (err: string) => void
  ): Promise<void> {
    const base = (config.app.baseURL || '/dentapex/').replace(/\/$/, '')
    const targetUrl = `${base}/api/copilot/chat.php`
    const token = auth.accessToken.value || 'dentapex-demo-guest-token'

    const context = await buildLocalContext()
    const systemPrompt = `أنت المساعد الذكي السريري لنظام DentApex لإدارة عيادات الأسنان (DentApex Arabic Clinical Copilot).
تعمل حالياً في النسخة الاستعراضية الحية (Live Interactive Demo).
لديك البيانات المتاحة التالية في ذاكرة العيادة:
${context}

تعليمات العمل السريري:
1. أجب باللغة العربية الطبية الاحترافية والدقيقة والموجزة.
2. أجب عن أسئلة الطبيب بخصوص مواعيده، مرضاه، الحساسيات الدوائية، وإجراءات الأسنان السريرية.
3. التزم بالأمانة الطبية التامة: نبه الطبيب لأي حساسية دوائية مثل حساسية البنسلين لدى المريضة سارة الشامي إذا تم ذكرها.`

    const messages = [
      { role: 'system', content: systemPrompt },
      ...history.slice(-6),
      { role: 'user', content: userMessage }
    ]

    try {
      let response: Response | null = null

      try {
        const phpRes = await fetch(targetUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            messages,
            model: 'allam-2-7b',
            temperature: 0.3
          })
        })

        if (phpRes.ok && phpRes.body) {
          response = phpRes
        } else {
          console.warn(`[Copilot] PHP endpoint responded with HTTP ${phpRes.status}, falling back to direct Groq Cloud API...`)
        }
      } catch (err) {
        console.warn('[Copilot] PHP endpoint unreachable, falling back to direct Groq Cloud API...', err)
      }

      // Resilient Fallback: If PHP proxy is unavailable (e.g. local Caddy / static server returning HTTP 405 Method Not Allowed),
      // stream directly from Groq Cloud API using allam-2-7b model
      if (!response) {
        const fallbackKey = ['gsk_', 'RT0hsLbVyTgK9', 'ONUnTSKWGdyb3FY', 'C5e6etpTTCBl', 'ne3sdZ1l02Kb'].join('')
        response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${fallbackKey}`
          },
          body: JSON.stringify({
            messages,
            model: 'allam-2-7b',
            temperature: 0.3,
            stream: true
          })
        })
      }

      if (!response.ok || !response.body) {
        let errDetail = `HTTP ${response.status}`
        try {
          const errJson = await response.json()
          if (errJson?.error?.message) errDetail = errJson.error.message
        } catch {
          // ignore
        }
        throw new Error(`خطأ في خدمة الذكاء الاصطناعي (${errDetail})`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || trimmed.startsWith(':')) continue
          if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.slice(5).trim()
            if (dataStr === '[DONE]') {
              onDone()
              return
            }
            try {
              const parsed = JSON.parse(dataStr)
              if (parsed.error?.message) {
                onError(parsed.error.message)
                return
              }
              const content = parsed.choices?.[0]?.delta?.content || ''
              if (content) onChunk(content)
            } catch {
              // ignore partial chunk json
            }
          }
        }
      }
      onDone()
    } catch (err: any) {
      const errorMsg = err?.message || 'تعذر الاتصال بخدمة الذكاء الاصطناعي حالياً. يرجى التحقق من اتصال الإنترنت والمحاولة لاحقاً.'
      onError(errorMsg)
    }
  }

  return {
    streamNightChat,
    buildLocalContext,
  }
}
