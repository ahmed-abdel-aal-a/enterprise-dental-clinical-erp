"""Pydantic schemas for the activity journal (read-only surface)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActivityJournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    event_type: str
    actor_id: UUID | None = None
    patient_id: UUID | None = None
    source_table: str
    source_entity_id: UUID | None = None
    payload: dict
    occurred_at: datetime
