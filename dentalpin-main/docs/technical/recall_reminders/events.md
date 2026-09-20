---
module: recall_reminders
last_verified_commit: 0000000
---

# recall_reminders — events

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

_This module does not publish any events._

## Consumed

| Event | Handler | Effect |
|-------|---------|--------|
| `recall.created` | `handlers._on_recall_created` | Enqueues a `recall_reminder` notification for the recall's patient. |

**Transactional (ADR 0019):** the handler declares `db` and runs
inside `recalls`' own publish transaction, in a savepoint. Queues on
the publisher's session; nothing is sent here — the outbox tick owns
the network I/O — so a rolled-back recall queues no reminder.
`recalls/service.py`'s `RECALL_CREATED` publish passes `db=db` for
this reason.

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`).
2. Publish from a service method after `flush()` — the bus runs handlers
   inline, *before* the request commits. Pass `db=db` so transactional
   subscribers can join the transaction (ADR 0019, issue #183).
3. Add the row to the table(s) above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.
