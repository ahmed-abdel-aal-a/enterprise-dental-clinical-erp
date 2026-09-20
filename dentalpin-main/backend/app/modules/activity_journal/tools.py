"""Agent tool for the activity journal. Thin wrapper over the read service."""

from __future__ import annotations

from datetime import date as date_cls
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.agents import AgentContext, Tool, ToolCategory

from .service import ActivityJournalService


class SearchActivityArgs(BaseModel):
    event_type: str | None = Field(
        default=None, description="Event type value, e.g. 'appointment.scheduled'."
    )
    patient_id: UUID | None = None
    date_from: date_cls | None = None
    date_to: date_cls | None = None
    limit: int = Field(default=20, ge=1, le=100)


async def _search_activity(ctx: AgentContext, params: SearchActivityArgs) -> dict:
    entries, total = await ActivityJournalService.list_entries(
        ctx.db,
        ctx.clinic_id,
        event_type=params.event_type,
        patient_id=params.patient_id,
        date_from=params.date_from,
        date_to=params.date_to,
        page=1,
        page_size=params.limit,
    )
    return {
        "total": total,
        "entries": [
            {
                "id": e.id,  # native UUID — the registry's jsonify coerces
                "event_type": e.event_type,
                "actor_id": e.actor_id,
                "patient_id": e.patient_id,
                "occurred_at": e.occurred_at,
            }
            for e in entries
        ],
    }


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="search_activity",
            description=(
                "Search the staff activity log (who did what, when), optionally "
                "filtered by event type, patient or date range."
            ),
            parameters=SearchActivityArgs,
            handler=_search_activity,
            permissions=["activity_journal.read"],
            category=ToolCategory.READ,
            # The stored payloads contain free prose from other modules
            # (budget notes, recall reasons, ...) — keep it off the cloud
            # LLM path, same criterion as expenses/recalls.
            exposes_free_text=True,
        ),
    ]
