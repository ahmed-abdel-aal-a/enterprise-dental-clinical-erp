# 0020 — Install state gates the runtime (only `installed` modules are live)

- **Status:** accepted
- **Date:** 2026-08-19
- **Deciders:** Ramón Martínez (DentalPin Core)
- **Tags:** modules, lifecycle, migrations

## Context

`core_module.state` (`installed` / `uninstalled` / `to_*`) was written by the
install and uninstall flows and read by nothing at runtime. The loader mounted
every module found on disk — router, event handlers, copilot tools — and the
scheduler, the RBAC merge and `TenantContext.modules_enabled` all iterated the
same "everything discovered" list (audit 2026-07-03 S1, issue #91). Two modules
even registered themselves before any state could be consulted: `verifactu`
attached its billing hook in `__init__` and `whatsapp_kapso` its channel adapter
at import time.

`auto_install=False` was therefore cosmetic: an uninstalled module kept firing
handlers against dropped tables, its routes answered (or 500'd), and PR #189's
`recall_reminders` — a patient-facing handler — would have gone live on the
first deploy while the admin UI said "not installed". Separately,
`docker-entrypoint.sh` ran `alembic upgrade heads` on every boot, so an
uninstalled module's branch (and tables) came back on the next restart.

## Decision

**A module is live in a process iff its `core_module.state` is `installed`.**

- Boot order: `register_discovered()` (discover + register, nothing mounted) →
  `reconcile_with_db()` → `PendingProcessor.run()` →
  `mount_modules(app, installed)` → `init_scheduler()`. Mounting is the one
  step that is *not* best-effort: if the DB is unreachable there, the process
  raises and the container restarts rather than serving an empty API.
- `ModuleRegistry` keeps two views: **discovered** (lifecycle machinery:
  reconcile, processor, CLI) and **active** (RBAC grants, scheduler jobs,
  `modules_enabled`, `/-/active`, feature gates such as
  `migration_import`'s `is_active("verifactu")`). `is_loaded()` /
  `list_modules()` no longer exist — callers choose on purpose.
- `BaseModule.on_activate()` is the only place for in-memory cross-module
  registrations (hook registries, channel adapters). It runs once per boot,
  after the module is mounted, only for installed modules. Nothing ever
  registers from `__init__` or at import time.
- Modules still never hot-(un)load: there is no `deactivate`. A restart
  re-evaluates from the DB, which is the contract the admin UI already states
  ("restart required").
- Boot migrations follow the same rule: `python -m app.cli db upgrade`
  applies the core heads plus the branch head of each module that is
  `installed` (or, with no row yet, `auto_install=True`), instead of
  `alembic upgrade heads`. Installing a module applies its branch through the
  processor (`alembic upgrade <name>@head`), as before.

## Consequences

### Good

- "Uninstalled" means uninstalled: no routes, handlers, tools, jobs, grants or
  schema resurrection. `auto_install=False` is a real opt-in.
- `creating-modules.md`'s existing promise ("uninstalling a module drops its
  grants automatically") and three docstrings become true instead of aspirational.
- `modules_enabled` finally has an enforcement point (ADR 0012 direction).
- `verifactu`'s scheduler jobs, previously added only from `install()` and lost
  on the next restart, are declared via `get_scheduled_jobs()`.

### Bad / accepted trade-offs

- Deployments whose DB has an in-use module in `uninstalled` (possible on
  instances reconciled before `auto_install` existed) go dark for that module
  after upgrading. Mitigation: `dentalpin modules list` before deploying;
  `modules install <name>` + restart for anything in use (idempotent: migrate
  is a no-op, seed + lifecycle hook + finalize run).
- A module `installed` in the DB whose dependency is not active (only reachable
  via `uninstall --force`) is skipped with an error log and hidden from
  `/-/active`; the loader does not try to repair state.
- `db upgrade` does not downgrade anything. Tables an older boot created for a
  module that was never installed stay until that module is installed and
  uninstalled once.

## Alternatives considered

- **Hot unsubscribe/unmount on uninstall** — requires owner metadata on the bus,
  router removal in Starlette and a `deactivate` contract, for a system whose
  admin UI already says "restart required". Rejected: complexity without a user
  benefit.
- **Filter Alembic `version_locations` by state** (original design §6.2) — a
  stale `alembic_version` row for an excluded directory would make Alembic
  crash-loop at boot, and offline mode has no DB. Rejected in favour of keeping
  the full graph loaded and filtering the *targets*.
- **Per-module guard inside each opt-in handler** (`if state != installed:
  return`) — fixes one symptom per module and keeps the core lie. Rejected.

## How to verify the rule still holds

- `backend/tests/test_module_activation.py` — mount gating, `on_activate`,
  dependency skip, permissions following activation, the reconcile → install →
  mount round-trip.
- `backend/tests/test_modules_active_endpoint.py::test_active_requires_the_module_to_be_mounted`.
- `backend/tests/test_boot_upgrade_targets.py` (unit) and the
  `alembic_roundtrip` CI job (`test_boot_upgrade_roundtrip.py`): an
  uninstalled module's tables stay absent across `db upgrade`.
- `grep -rn "channel_registry.register\|BillingHookRegistry.register" backend/app/modules` —
  every hit must be inside an `on_activate`.

## References

- `backend/app/core/plugins/loader.py` (`register_discovered`, `mount_modules`)
- `backend/app/core/plugins/registry.py`
- `backend/app/main.py` (lifespan)
- `backend/app/cli/db.py`, `backend/docker-entrypoint.sh`
- `docs/technical/module-system-architecture.md` §5.2 step 6 (the original intent)
- `docs/technical/audit-2026-07-03.md` S1 · Issue #91 · PR #189
