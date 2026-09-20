"""Activity journal HTTP surface. Mounts under ``/api/v1/activity_journal/*``.

Read-only by design: rows are appended by the event handlers, so there
is no POST/PATCH/DELETE here (a hard DELETE would defeat the audit
purpose — same reasoning as the lab_orders review).
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .schemas import ActivityJournalEntryResponse
from .service import ActivityJournalService

router = APIRouter()


@router.get("/", response_model=PaginatedApiResponse[ActivityJournalEntryResponse])
async def list_entries(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("activity_journal.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    event_type: str | None = Query(default=None),
    actor_id: UUID | None = Query(default=None),
    patient_id: UUID | None = Query(default=None),
    # Typed as date (not str) — a str here 500s on asyncpg with
    # ``operator does not exist: timestamptz >= character varying``
    # (the expenses #245 lesson).
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedApiResponse[ActivityJournalEntryResponse]:
    entries, total = await ActivityJournalService.list_entries(
        db,
        ctx.clinic_id,
        event_type=event_type,
        actor_id=actor_id,
        patient_id=patient_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return PaginatedApiResponse(
        data=[ActivityJournalEntryResponse.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{entry_id}", response_model=ApiResponse[ActivityJournalEntryResponse])
async def get_entry(
    entry_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("activity_journal.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ActivityJournalEntryResponse]:
    entry = await ActivityJournalService.get_entry(db, ctx.clinic_id, entry_id)
    return ApiResponse(data=ActivityJournalEntryResponse.model_validate(entry))
