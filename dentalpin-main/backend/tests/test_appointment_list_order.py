"""``list_appointments`` honours the ``order`` parameter.

``asc`` (the default, unchanged behaviour) pages oldest-first;
``desc`` pages newest-first so most-recent-first consumers (the
patient last-visit card) can fetch ``page_size=1`` instead of paging
to the tail.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agenda.service import AppointmentService
from tests.test_appointment_transitions import _mkapt, _mkworld


@pytest.mark.asyncio
async def test_list_appointments_order(db_session: AsyncSession) -> None:
    world = await _mkworld(db_session)
    starts = [
        datetime(2026, 5, 4, 9, 0, tzinfo=UTC),
        datetime(2026, 5, 5, 9, 0, tzinfo=UTC),
        datetime(2026, 5, 6, 9, 0, tzinfo=UTC),
    ]
    for start in starts:
        await _mkapt(db_session, world, start=start)

    ascending, total = await AppointmentService.list_appointments(
        db_session, world["clinic_id"], patient_id=world["patient_id"]
    )
    assert total == 3
    assert [a.start_time for a in ascending] == starts

    descending, total = await AppointmentService.list_appointments(
        db_session, world["clinic_id"], patient_id=world["patient_id"], order="desc"
    )
    assert total == 3
    assert [a.start_time for a in descending] == list(reversed(starts))

    newest, total = await AppointmentService.list_appointments(
        db_session,
        world["clinic_id"],
        patient_id=world["patient_id"],
        order="desc",
        page_size=1,
    )
    assert total == 3
    assert [a.start_time for a in newest] == [starts[-1]]


@pytest.mark.asyncio
async def test_list_appointments_desc_with_status_filter(db_session: AsyncSession) -> None:
    """The last-visit card's exact query: completed only, newest first."""
    world = await _mkworld(db_session)
    completed_starts = [
        datetime(2026, 5, 11, 9, 0, tzinfo=UTC),
        datetime(2026, 5, 12, 9, 0, tzinfo=UTC),
    ]
    for start in completed_starts:
        await _mkapt(db_session, world, start=start, status="completed")
    # A later appointment that is merely scheduled must not win.
    await _mkapt(
        db_session, world, start=datetime(2026, 5, 13, 9, 0, tzinfo=UTC) + timedelta(hours=1)
    )

    newest, total = await AppointmentService.list_appointments(
        db_session,
        world["clinic_id"],
        None,
        None,
        None,
        None,
        "completed",
        patient_id=world["patient_id"],
        order="desc",
        page_size=1,
    )
    assert total == 2
    assert [a.start_time for a in newest] == [completed_starts[-1]]
