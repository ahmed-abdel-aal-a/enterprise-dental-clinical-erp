"""Event handlers for the integrations module.

Transactional (ADR 0019), matching notifications/handlers.py exactly:
each body queues WebhookDelivery rows on the publisher's own session —
DB-only, no network I/O. The scheduled dispatch tick owns the network
I/O, so a rolled-back request queues no delivery.

Phase 1 ships two triggers end-to-end (issue #65) — the full trigger
catalog (issue #65 §3) is a follow-up PR.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class IntegrationsHandlers:
    """Event handlers for webhook trigger events.

    Both handlers are identical apart from which ``EventType`` they
    enqueue for, so they share ``_enqueue`` rather than duplicating
    the transactional/error-handling shape per trigger.
    """

    @staticmethod
    async def _enqueue(event_type: str, data: dict[str, Any], *, db: AsyncSession) -> None:
        """Queue a delivery for every subscription listing ``event_type``.

        Transactional (ADR 0019): queues on the publisher's session, no
        network I/O here — the outbox tick does the sending. A handler
        error must not fail the publisher's own transaction (same
        reasoning notifications/handlers.py documents), so a malformed
        payload is logged and swallowed, never raised.
        """
        from .gateway import WebhookGateway

        try:
            clinic_id = UUID(data["clinic_id"])
        except (KeyError, ValueError) as exc:
            logger.error("integrations: malformed %s payload: %s", event_type, exc)
            return

        # occurred_at: stamped here rather than trusting the publisher's own
        # payload to carry one, since not every EventType payload does.
        payload = {**data, "occurred_at": datetime.now(UTC).isoformat()}

        async with db.begin_nested():
            await WebhookGateway.enqueue_for_event(db, clinic_id, event_type, payload)

    @staticmethod
    async def on_patient_created(data: dict[str, Any], *, db: AsyncSession) -> None:
        from app.core.events import EventType

        await IntegrationsHandlers._enqueue(EventType.PATIENT_CREATED, data, db=db)

    @staticmethod
    async def on_appointment_completed(data: dict[str, Any], *, db: AsyncSession) -> None:
        from app.core.events import EventType

        await IntegrationsHandlers._enqueue(EventType.APPOINTMENT_COMPLETED, data, db=db)
