# 0018 — First-run onboarding: seed via `clinic.created`, state in `clinic.settings`

- **Status:** accepted
- **Date:** 2026-08-16
- **Deciders:** Ramon Martinez
- **Tags:** onboarding, modules, events, core

## Context

Until now `POST /auth/setup` created a clinic + admin and nothing else: no
VAT types, no catalog, no invoice series, no cabinet, 24/7 hours. Country
was never asked, so every install became `Europe/Madrid`/`EUR`. The only
post-install help was a two-rule checklist hidden under `/settings`,
dismissed per browser via localStorage.

We want a fresh clinic to be **operative on first login** and a guided
"getting started" card on the dashboard — without core importing module
code and without adding tables.

## Decision

1. **Country presets live in core** (`backend/app/core/auth/country_presets.py`)
   and only carry country-level data (currency, timezone, language, tax-id
   format, `vat_preset` key, suggested modules). Only `ES` has fiscal
   logic in v1; every other code falls back to a generic preset.
2. `POST /auth/setup` commits the clinic, then **publishes
   `clinic.created`** with a self-sufficient payload
   `{clinic_id, country, currency, timezone, language, vat_preset, created_by, source}`.
   **Modules seed their own defaults by subscribing** (catalog → VAT +
   catalog, billing → `FAC`/`RECT` series, agenda → one cabinet,
   schedules → Mon–Fri template). Handlers open their own session, are
   idempotent ("skip if the clinic already has any"), and never raise —
   a failing seed leaves a usable clinic and the checklist shows the gap.
3. **Onboarding state is server-side in `clinic.settings.onboarding`**
   (`{dismissed_at, completed_at, skipped: {rule_id: iso}}`), mutated via
   `PATCH /auth/clinic/settings/onboarding`. Completion of each step is
   *derived* from data by client-side rules (`registerGettingStartedRule`);
   only skip/dismiss are stored. localStorage dismissal is removed.
4. **Team invites without email** use a signed JWT (`type: "invite"`,
   bound to `token_version`, 7-day expiry, single use) consumed by the
   public `POST /auth/set-password`. No invitation table.

## Consequences

### Good

- Core stays module-agnostic; each module owns what "ready to work" means for it.
- No migrations: presets are code, state is JSONB, invites are stateless tokens.
- The checklist self-heals: it reflects real data, not a stored "done" flag.

### Bad / accepted trade-offs

- Seeding runs inline in `/setup` (~1–2 s once).
- A handler failure has no one-click "reseed" yet (idempotent handlers make
  a future button trivial).
- Non-EUR clinics receive the catalog with prices at 0.
- Existing installs see the card once more after localStorage dismissal is dropped.

## Alternatives considered

- **Core calls `seed_catalog()` etc. directly from `/setup`** — violates
  module isolation (ADR 0001); CI would reject the imports.
- **`BaseModule.on_clinic_created` lifecycle hook** — new machinery for one
  event; the bus already gives ordering-free, awaited, isolated handlers.
- **Aggregate `GET /auth/clinic/onboarding-status` in core** — core would
  query module tables. Rejected; each rule fetches its own module endpoint.
- **Separate `/onboarding` wizard with its own forms** — duplicates settings
  pages; the card + guided bar reuses them.

## How to verify the rule still holds

- `backend/tests/test_setup_onboarding.py` — preset application, seeding per
  module, idempotency, generic fallback.
- `grep -rn "from app.modules" backend/app/core/auth/` must stay empty.

## References

- `backend/app/core/auth/router.py` (`setup`, `setup_presets`)
- `backend/app/core/auth/country_presets.py`
- `backend/app/modules/{catalog,billing,agenda,schedules}/events.py`
- `docs/features/onboarding.md`
