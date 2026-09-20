"""activity_journal — append-only, event-driven staff activity log.

Pure listener on the event bus (ADR 0019): rows are written inside the
publisher's transaction by transactional handlers and are never mutated
or deleted by this module. The schema is deliberately generic — full
event payload as JSONB plus extracted actor/patient/entity columns — so
the GDPR/audit-trail work (#44) can build on this table instead of
duplicating it.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ActivityJournalEntry(Base):
    """One immutable row per subscribed event occurrence.

    ``payload`` keeps the full event data verbatim; ``actor_id`` /
    ``patient_id`` / ``source_entity_id`` are extracted convenience
    columns for filtering (they stay loose UUIDs — no FKs — because the
    referenced rows live in other modules' tables that may be absent).
    """

    __tablename__ = "activity_journal_entries"
    __table_args__ = (
        Index("ix_activity_journal_clinic_occurred", "clinic_id", "occurred_at"),
        Index("ix_activity_journal_clinic_event", "clinic_id", "event_type"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)

    # Event type value, e.g. ``appointment.scheduled``.
    event_type: Mapped[str] = mapped_column(String(100))

    # Loose attribution — events carry actor ids only sometimes; NULL when
    # the payload has none. Never a FK: users live outside this module.
    actor_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    patient_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # First segment of the event type (``appointment`` for
    # ``appointment.scheduled``) + the primary entity id from the payload.
    source_table: Mapped[str] = mapped_column(String(50))
    source_entity_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Full event payload verbatim — the audit value of the row.
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
