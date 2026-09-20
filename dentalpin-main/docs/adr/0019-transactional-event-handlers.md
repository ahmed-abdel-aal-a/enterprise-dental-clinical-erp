# 0019 — Transactional event handlers (opt-in `db` on the event bus)

- **Status:** accepted
- **Date:** 2026-08-17
- **Deciders:** Ramón Martínez (DentalPin Core)
- **Tags:** modules, events, finance

## Context

`EventBus.publish` is synchronous and inline (the publisher awaits every
subscriber), but each handler opened its own `async_session_maker()`
session while publishers fire events **after `flush`, before the request
commits**. Under READ COMMITTED a second connection cannot see those
rows, so a handler that must react to what the publisher just wrote
reads stale state — and its own commit is a second, non-atomic
transaction.

Issue #178 made this concrete for money. Billing's reaction to
`payment.refunded` (recompute invoice status) silently did nothing:
`total_paid` dropped to 0 while `status` stayed `partial`. And there was
no bridge at all between a payment allocated to a budget (`payments`
module) and the invoices issued from that budget (`billing` module), so
three "record a payment" buttons produced three different totals.

ADR 0010 already states that invoice ↔ payment consistency must be
synchronous and transactional; the bus simply had no way to deliver
that. Options were a hook registry (a second extension mechanism next
to the bus), publish-after-commit (visible but not atomic), or giving
the bus the missing capability.

## Decision

The event bus supports **transactional handlers**, opt-in on both sides:

- A publisher may offer its session: `event_bus.publish(type, payload, db=db)`.
- A handler opts in by declaring a keyword parameter named `db`:
  `async def on_x(data, *, db: AsyncSession)`. It runs inside the
  publisher's transaction — same session, **no commit of its own, no
  external I/O** — and its exception **propagates** to the publisher
  (rolling the whole request back).
- Handlers without `db` keep the previous contract: own session,
  errors logged and swallowed. They must not depend on rows the
  publisher has only flushed.
- Subscribing a `db` handler to an event published without `db` raises
  `RuntimeError` at publish time — a wiring mistake surfaces
  immediately, never as silent drift.

Semantically this is Django-signals: decoupled by event name, but
inline and inside the caller's unit of work. Module isolation is
untouched — subscribers still register by name in
`get_event_handlers()`, no imports across the boundary.

First users: `payments` publishes `payment.allocated` and
`payment.refunded` with `db`; `billing` consumes both transactionally
(`billing/events.py`, `billing/payment_bridge.py`).

## Consequences

### Good

- Money paths that span modules are atomic without coupling them.
- ADR 0010's "synchronous transactional recalc via `payment.refunded`"
  is now true in the code, not only on paper.
- One extension mechanism (the bus), not two.
- Failure is loud: a broken transactional subscriber fails the request
  instead of leaving a half-written state.

### Bad / accepted trade-offs

- A transactional handler can fail an unrelated publisher's request.
  Rule: keep them short, DB-only, idempotent, and covered by tests in
  the *publisher's* suite as well as the subscriber's.
- The `db` parameter is a signature convention detected by
  introspection; a typo (`session`) silently downgrades the handler to
  own-session. Reviewers check the signature when a handler is meant
  to be transactional.
- Existing own-session handlers carried the same latent bug. The audit
  (issue #183) found three instances of it, two of them live and silent:
  `recalls` could never link a recall to a new appointment (FK to a row
  its second connection couldn't see), `notifications` never queued the
  welcome message for a patient created through the API, and
  `budget.superseded` had already been worked around by committing before
  publishing. 23 handlers moved to the transactional contract; the rest are
  payload-only or fire after the publisher commits, and say so in their
  docstring. Three workarounds (`SKIP LOCKED`, the commit-first publish, a
  lock-avoidance flag rationale) went away with them.

## Alternatives considered

- **Hook registry in `payments` (like `BillingHookRegistry`)** — in-tx
  and explicit, but a second cross-module mechanism next to the bus,
  and it wouldn't fix the class of bug in existing handlers.
- **Publish after commit** — handlers would see committed rows, but a
  failure between the two commits leaves inconsistent money; also a
  cross-cutting change to every publisher.
- **Pass the session inside the payload** — same effect, but hidden in
  a dict, unlogged, and impossible to enforce at publish time.

## How to verify the rule still holds

- `backend/tests/test_event_bus_transactional.py` — `db` passthrough,
  exception propagation, `RuntimeError` on missing `db`.
- `backend/tests/modules/billing/test_payment_bridge.py` — the #178
  reproduction asserting convergence across surfaces, in-tx refund
  recompute, reallocate unlink/relink.
- `grep -rn "async_session_maker" backend/app/modules/*/events.py`
  lists own-session handlers; any of them that reads publisher-written
  rows is a candidate for `db`.
- `test_every_publisher_of_a_transactional_event_passes_db` (same file)
  walks the registry and every publish site in `app/`, so a publisher
  that forgets `db=` fails CI instead of raising in production.

## References

- `backend/app/core/events/bus.py`
- `backend/app/modules/payments/workflow.py` (`_publish_allocated`, `refund_payment`)
- `backend/app/modules/billing/events.py`, `backend/app/modules/billing/payment_bridge.py`
- Issue #178, ADR 0003, ADR 0010
