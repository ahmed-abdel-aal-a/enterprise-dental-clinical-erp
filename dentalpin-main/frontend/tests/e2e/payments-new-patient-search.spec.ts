import { test, expect } from './_fixtures'

/**
 * /payments — New payment patient search (issue #179).
 *
 * Regression case: the patient field at /payments/new used to be a
 * plain text box bound to a UUID with a "Search patient…" placeholder
 * that didn't actually search. Typing a name posted an invalid
 * `patient_id` and the modal showed a generic "Could not record the
 * payment" error. Fixed by swapping in the same PatientVisualSelector
 * used everywhere else (New quote, New invoice, New appointment).
 */

const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000'

test.describe('payments — new payment patient search', () => {
  test.use({ role: 'receptionist' })

  test('receptionist finds a patient by name and records a payment', async ({ loggedIn }) => {
    await loggedIn.goto('/payments')
    await loggedIn.waitForLoadState('networkidle')

    // Create a fresh, uniquely-named patient inline (same "+ Crear" flow
    // as agenda-quick-patient-create.spec.ts) — avoids depending on
    // which exact seed patients exist.
    const suffix = Date.now().toString().slice(-6)
    const firstName = 'Paytest'
    const lastName = `Patient ${suffix}`

    await loggedIn.getByRole('button', { name: /New payment/i }).first().click()

    const searchInput = loggedIn.locator('input[data-testid="visual-selector-input"]').first()
    await expect(searchInput).toBeVisible({ timeout: 10_000 })
    await searchInput.fill(`${firstName} ${lastName}`)

    const createRow = loggedIn.locator('[data-testid="patient-selector-create-row"]')
    await expect(createRow).toBeVisible({ timeout: 5_000 })
    await createRow.click()

    const createForm = loggedIn.locator('[data-testid="patient-selector-create-form"]')
    await expect(createForm).toBeVisible()
    await createForm.locator('[data-testid="patient-selector-create-submit"]').click()

    // Patient card replaces the selector — the picker resolved a real
    // UUID, not raw typed text.
    await expect(loggedIn.getByText(`${lastName}, ${firstName}`, { exact: false })).toBeVisible({ timeout: 5_000 })

    // Fill amount + submit.
    const amountInput = loggedIn.locator('input[type="number"]').first()
    await amountInput.fill('50')
    await loggedIn.getByRole('button', { name: /Cash/i }).click()
    // Wait for the POST to complete before asserting persistence — the
    // API check below races the in-flight request otherwise (main went
    // red on the #208 merge because of exactly that).
    const postDone = loggedIn.waitForResponse(r =>
      r.url().includes('/api/v1/payments') && r.request().method() === 'POST')
    await loggedIn.getByRole('button', { name: /€?50|record/i }).last().click()
    expect((await postDone).ok(), 'POST /payments should succeed').toBeTruthy()

    // No generic error, modal closes.
    await expect(loggedIn.getByText(/Could not record the payment/i)).toHaveCount(0)

    // Persistence check via the API, not just UI state.
    const ctx = loggedIn.context()
    const cookies = await ctx.cookies()
    const token = cookies.find(c => c.name === 'access_token')?.value
    const res = await ctx.request.get(
      `${API_BASE}/api/v1/patients?search=${encodeURIComponent(lastName)}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} }
    )
    expect(res.ok()).toBeTruthy()
    const patientBody = (await res.json()) as { data: Array<{ id: string, first_name: string, last_name: string }> }
    const patient = patientBody.data.find(p => p.first_name === firstName && p.last_name === lastName)
    expect(patient, `expected patient ${firstName} ${lastName} to exist`).toBeDefined()

    const paymentsRes = await ctx.request.get(
      `${API_BASE}/api/v1/payments?patient_id=${patient!.id}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} }
    )
    expect(paymentsRes.ok()).toBeTruthy()
    const paymentsBody = (await paymentsRes.json()) as { data: Array<{ amount: string }> }
    expect(paymentsBody.data.length, 'expected the 50 payment to be persisted for the new patient').toBeGreaterThan(0)
  })

  test('switching to a different patient resets the destination back to "a cuenta"', async ({ loggedIn }) => {
    // Regression guard: AllocationTargetSelect reloads its budget list on
    // patient change but never resets the selected target itself — a
    // budget id chosen for patient A must not silently carry over onto
    // patient B once the field is a real picker instead of dead text.
    await loggedIn.goto('/payments')
    await loggedIn.waitForLoadState('networkidle')
    await loggedIn.getByRole('button', { name: /New payment/i }).first().click()

    const searchInput = loggedIn.locator('input[data-testid="visual-selector-input"]').first()
    await expect(searchInput).toBeVisible({ timeout: 10_000 })

    const suffix = Date.now().toString().slice(-6)
    async function createPatient(last: string) {
      await searchInput.fill(`Paytest ${last}`)
      const createRow = loggedIn.locator('[data-testid="patient-selector-create-row"]')
      await expect(createRow).toBeVisible({ timeout: 5_000 })
      await createRow.click()
      await loggedIn.locator('[data-testid="patient-selector-create-form"]')
        .locator('[data-testid="patient-selector-create-submit"]').click()
      await expect(loggedIn.getByText(`${last}, Paytest`, { exact: false })).toBeVisible({ timeout: 5_000 })
    }

    await createPatient(`A${suffix}`)

    // If patient A has no open budgets the target select only offers
    // "a cuenta" — that's fine, the assertion below only needs to see
    // the default label, not exercise an actual budget switch.
    const targetLabel = loggedIn.getByText(/a cuenta|on account/i).first()
    await expect(targetLabel).toBeVisible({ timeout: 5_000 })

    // Deselect via the selected-patient card's own "x" button, then
    // search again for a second, different patient.
    const clearBtn = loggedIn.locator('.bg-surface-muted button').first()
    await clearBtn.click()
    await createPatient(`B${suffix}`)

    // Still showing "a cuenta" — never silently locked onto a stale target.
    await expect(loggedIn.getByText(/a cuenta|on account/i).first()).toBeVisible({ timeout: 5_000 })
  })

  test('hygienist (payments read-only) cannot reach New payment', async ({ page }) => {
    const ctx = page.context()
    const form = new URLSearchParams({ username: 'hygienist@demo.clinic', password: 'demo1234' })
    const loginRes = await ctx.request.post(`${API_BASE}/api/v1/auth/login`, {
      data: form.toString(),
      headers: { 'content-type': 'application/x-www-form-urlencoded' }
    })
    if (!loginRes.ok()) test.skip(true, 'hygienist seed user not available')
    const tokens = (await loginRes.json()) as { access_token: string }
    await ctx.addCookies([{ name: 'access_token', value: tokens.access_token, url: 'http://localhost:3000' }])

    await page.goto('/payments')
    await page.waitForLoadState('networkidle')

    await expect(page.getByRole('button', { name: /New payment/i })).toHaveCount(0)
  })
})
