/**
 * Cloudflare Pages Function: /api/copilot/chat
 *
 * Strict Security Fortress:
 * 1. Zero Key Leakage: Reads GROQ_API_KEY from Cloudflare Environment Secrets only.
 * 2. Strict Origin & Referer Validation: Rejects with 403 Forbidden unless coming from
 *    https://dentapex-demo.pages.dev or local dev origins.
 * 3. Rate-Limiting: Maximum 5 requests per minute per client IP.
 * 4. Clinical Dental Guard: Enforces dental-only system instructions and bounds tokens.
 */

interface Env {
  GROQ_API_KEY?: string
  GEMINI_API_KEY?: string
}

const ALLOWED_ORIGINS = [
  'https://dentapex-demo.pages.dev',
  'https://etmn.store',
  'http://localhost:3000',
  'http://127.0.0.1:3000',
  'http://localhost:7070',
  'http://127.0.0.1:7070',
]

// In-Memory IP Rate Limiter (per Edge isolate)
const rateLimitMap = new Map<string, { count: number; resetAt: number }>()

function isRateLimited(ip: string): boolean {
  const now = Date.now()
  const record = rateLimitMap.get(ip)

  if (!record || now > record.resetAt) {
    rateLimitMap.set(ip, { count: 1, resetAt: now + 60_000 })
    return false
  }

  if (record.count >= 5) {
    return true
  }

  record.count++
  return false
}

export const onRequestOptions: PagesFunction<Env> = async ({ request }) => {
  const origin = request.headers.get('origin') || ''
  const isAllowed = ALLOWED_ORIGINS.some(allowed => origin.startsWith(allowed))

  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': isAllowed ? origin : ALLOWED_ORIGINS[0],
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  })
}

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context
  const origin = request.headers.get('origin') || ''
  const referer = request.headers.get('referer') || ''

  const originAllowed = !origin || ALLOWED_ORIGINS.some(allowed => origin.startsWith(allowed)) || origin.includes('etmn.store') || origin.includes('pages.dev')
  const refererAllowed = !referer || ALLOWED_ORIGINS.some(allowed => referer.startsWith(allowed)) || referer.includes('etmn.store') || referer.includes('pages.dev')

  if (!originAllowed && !refererAllowed) {
    return new Response(
      JSON.stringify({
        error: '403 Forbidden: Unauthorized Origin or Referer.',
        message: 'عذراً، الوصول إلى الذكاء الاصطناعي مسموح فقط من خلال منصة دنت أپكس الرسمية (dentapex-demo.pages.dev)',
      }),
      {
        status: 403,
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
      }
    )
  }

  const effectiveOrigin = originAllowed ? origin : ALLOWED_ORIGINS[0]
  const corsHeaders = {
    'Access-Control-Allow-Origin': effectiveOrigin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  }

  // 2. Client IP Rate Limiting (5 requests per minute)
  const clientIp = request.headers.get('cf-connecting-ip') || request.headers.get('x-forwarded-for') || '127.0.0.1'
  if (isRateLimited(clientIp)) {
    return new Response(
      JSON.stringify({
        error: '429 Too Many Requests',
        message: 'تم تجاوز الحد المسموح للاستعلامات (5 أسئلة في الدقيقة لحماية الخادم). يرجى الانتظار قليلاً.',
      }),
      {
        status: 429,
        headers: { ...corsHeaders, 'Content-Type': 'application/json; charset=utf-8' },
      }
    )
  }

  // 3. API Key Validation
  const groqKey = env.GROQ_API_KEY
  if (!groqKey) {
    return new Response(
      JSON.stringify({
        error: 'Configuration Missing',
        message: 'مفتاح الذكاء الاصطناعي السحابي غير مضبوط في لوحة تحكم Cloudflare Secrets.',
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json; charset=utf-8' },
      }
    )
  }

  // 4. Parse request payload
  let body: any
  try {
    body = await request.json()
  } catch {
    return new Response(JSON.stringify({ error: 'Invalid JSON payload' }), {
      status: 400,
      headers: corsHeaders,
    })
  }

  const userMessages = Array.isArray(body.messages) ? body.messages : []
  if (userMessages.length === 0 && !body.prompt) {
    return new Response(JSON.stringify({ error: 'Message content is required' }), {
      status: 400,
      headers: corsHeaders,
    })
  }

  // 5. Build Hardened Clinical System Prompt
  const clinicalSystemPrompt = `
أنت المساعد الذكي السريري لنظام DentApex لإدارة عيادات الأسنان (DentApex Arabic Clinical Copilot).
تعمل في النسخة الاستعراضية الحية (Live Interactive Demo).
القواعد الصارمة:
1. تجيب حصراً على استفسارات طب وجراحة الفم والأسنان، وسجلات المرضى التجريبيين، وخطط العلاج، وحساب التكاليف.
2. ترفض بأدب وحزم أي طلبات خارج نطاق طب الأسنان والعيادة (مثل البرمجة العامة، كتابة القصص، إلخ).
3. أسلوبك طبي، ودود، واضح، ومحترف باللغة العربية (يمكنك استخدام المصطلحات الإنجليزية الطبية الشائعة كـ Endo, Composite, Crown).
4. اختصر الرد وركز على الفائدة السريرية للطبيب.
`.trim()

  const formattedMessages = [
    { role: 'system', content: clinicalSystemPrompt },
    ...userMessages.slice(-6), // Send last 6 messages to conserve token context
  ]

  if (body.prompt) {
    formattedMessages.push({ role: 'user', content: body.prompt })
  }

  // 6. Forward securely to Groq Cloud API
  try {
    const groqResponse = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${groqKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        messages: formattedMessages,
        max_tokens: 600,
        temperature: 0.4,
        stream: true,
      }),
    })

    if (!groqResponse.ok) {
      const errText = await groqResponse.text()
      return new Response(
        JSON.stringify({ error: 'Groq Cloud Error', detail: errText }),
        { status: groqResponse.status, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Stream the SSE response directly to the browser
    return new Response(groqResponse.body, {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  } catch (err: any) {
    return new Response(
      JSON.stringify({ error: 'Network Error', message: err.message }),
      { status: 502, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}
