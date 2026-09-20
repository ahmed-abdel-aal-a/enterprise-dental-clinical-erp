"""``last_visit`` ordering counts completed appointments only.

The patient list's ``last_visit`` sort and ``get_recent_patients`` used
``MAX(start_time)`` over *any* appointment, so a future booking or a
cancellation ranked a patient as recently seen — disagreeing with the
patient-summary last-visit card, which shows the last **completed**
appointment (PR #251 review). Both now share the completed-only
definition.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.models import Patient
from app.modules.patients.service import PatientService
from tests.test_appointment_transitions import _mkapt, _mkworld


async def _world_with_three_patients(db: AsyncSession) -> tuple[dict[str, UUID], list[Patient]]:
    """A (from _mkworld), B and C in one clinic.

    - A: completed visit on May 2 → most recent actual visit.
    - B: completed visit on May 1, plus a *scheduled* appointment far in
      the future — under MAX(start_time) over any status B would
      outrank A.
    - C: only a scheduled appointment — never visited.
    """
    world = await _mkworld(db)
    extra = [
        Patient(id=uuid4(), clinic_id=world["clinic_id"], first_name=fn, last_name="Paciente")
        for fn in ("Berta", "Carla")
    ]
    db.add_all(extra)
    await db.commit()
    b, c = extra

    await _mkapt(db, world, start=datetime(2026, 5, 2, 9, 0, tzinfo=UTC), status="completed")
    world_b = {**world, "patient_id": b.id}
    await _mkapt(db, world_b, start=datetime(2026, 5, 1, 9, 0, tzinfo=UTC), status="completed")
    await _mkapt(db, world_b, start=datetime(2027, 1, 15, 9, 0, tzinfo=UTC))
    world_c = {**world, "patient_id": c.id}
    await _mkapt(db, world_c, start=datetime(2027, 1, 16, 9, 0, tzinfo=UTC))

    a = await db.get(Patient, world["patient_id"])
    assert a is not None
    return world, [a, b, c]


@pytest.mark.asyncio
async def test_last_visit_sort_counts_completed_only(db_session: AsyncSession) -> None:
    world, (a, b, c) = await _world_with_three_patients(db_session)

    patients, total = await PatientService.list_patients(
        db_session, world["clinic_id"], sort="last_visit:desc"
    )
    assert total == 3
    # A (completed May 2) before B (completed May 1, future booking
    # ignored); C never visited → NULLS LAST.
    assert [p.id for p in patients] == [a.id, b.id, c.id]


@pytest.mark.asyncio
async def test_recent_patients_counts_completed_only(db_session: AsyncSession) -> None:
    world, (a, b, c) = await _world_with_three_patients(db_session)

    recent = await PatientService.get_recent_patients(db_session, world["clinic_id"])
    assert [p.id for p in recent] == [a.id, b.id]
