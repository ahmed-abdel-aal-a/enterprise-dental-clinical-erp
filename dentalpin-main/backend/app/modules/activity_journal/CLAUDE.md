# Activity journal module

Append-only, event-driven staff activity log. Pure listener on the event
bus: subscribes to every EventType that is published transactionally and
writes one immutable row per occurrence (actor, patient, source entity,
full JSONB payload). Custom clinic module — standalone, `depends: []`.

## Public API

Routes mounted at `/api/v1/activity_journal/`.

- `GET /activity_journal`          — list, filterable by event type/patient/date range, paginated; `activity_journal.read`
- `GET /activity_journal/{id}`     — single entry; `activity_journal.read`

No POST/PATCH/DELETE — append-only by construction.

## Event subscriptions

See `get_event_handlers()` in `__init__.py` and
`docs/technical/activity_journal/events.md`: only event types whose
publishers all pass `db=db`. Handlers are transactional (ADR 0019) —
rows commit/rollback with the publisher's operation.

## Dependencies

`manifest.depends = []` — standalone.

## Permissions

`activity_journal.read` only (no write exists). Default role grants:
**admin only** — the log records which staff member did what.
Clinics can widen from the module admin UI.

## Tools exposed

| Tool | Category | Wraps | Permission |
|---|---|---|---|
| `search_activity` | READ | `ActivityJournalService.list_entries` | `activity_journal.read` |

`search_activity` is marked `exposes_free_text=True`: stored payloads
contain free prose from other modules (budget notes, recall reasons,
…), so it stays off the cloud LLM path under redaction.
