---
module: activity_journal
---

# Activity journal — append-only staff activity log

`activity_journal` is a **pure listener** on the event bus: it
subscribes to every event type that is published transactionally and
writes one immutable row per occurrence — who did what, when, with the
full event payload stored verbatim as JSONB. It writes only to its own
table; it never mutates or deletes rows, and nothing in the module can
edit history.

## Design

- **Transactional handlers (ADR 0019).** Every handler declares `db`,
  so rows are flushed inside the *publisher's* transaction: if the
  business operation rolls back, so does its audit row. A test pins
  both directions (commit persists / rollback discards).
- **Curated subscription set.** The module subscribes to exactly those
  EventTypes whose publishers *all* pass `db=db` (audited across
  `app/`). Events with any non-transactional publisher (email,
  copilot, migration tooling, legacy odontogram updates…) are excluded
  on purpose — the bus raises `RuntimeError` when a transactional
  handler receives no session, so subscribing to them would break
  those flows. See [events.md](./events.md) for the full list.
- **Built to be extended.** The schema (actor / patient / source
  entity columns + full JSONB payload) is designed so the GDPR /
  audit-trail work (#44) can build on this table instead of
  duplicating it.

## Data captured

| Column | Meaning |
| --- | --- |
| `event_type` | Event value, e.g. `appointment.scheduled` |
| `actor_id` | User attribution when the payload carries one (`user_id` / `actor_id` / `created_by`) |
| `patient_id` | Extracted for filtering when present |
| `source_table` / `source_entity_id` | Event namespace + primary entity id |
| `payload` | Full event data, verbatim JSONB |
| `occurred_at` | From the payload when it carries a timestamp, else now |

## Screens

- [Activity log](../../user-manual/en/activity_journal/screens/journal.md):
  filterable, paginated read-only list with per-row payload viewer.

## API

Read-only by design — there is no POST/PATCH/DELETE:

- `GET /api/v1/activity_journal/` — filters (`event_type`, `patient_id`,
  `date_from`, `date_to`) + pagination.
- `GET /api/v1/activity_journal/{entry_id}`

## Agent tools

- `search_activity` — search the log by event type / patient / date
  range. Marked `exposes_free_text=True`: payloads contain free prose
  from other modules, so it stays off the cloud LLM path.

## Install policy

Optional module: `depends: []`, `auto_install=False`, `removable=True`.
Activated from the module admin UI. Ships admin-only
(`role_permissions: {"admin": ["*"]}`) — staff-activity data is
sensitive; clinics can widen it deliberately.
