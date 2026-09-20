"""``appointment.scheduled`` → auto-link a pending recall (issue #183).

``Recall.linked_appointment_id`` is an FK to ``appointments.id``. While this
handler opened its own session it wrote that FK from a second connection,
against an appointment the publisher had only flushed — invisible there, so
Postgres rejected the write, the bus swallowed the error and the auto-link
silently never happened. The handler is transactional now (ADR 0019).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership, User
from app.modules.patients.models import Patient
from app.modules.recalls.models import Recall


@pytest_asyncio.fixture
async def dentist_id(db_session: AsyncSession, test_clinic: Clinic) -> str:
    """Appointments require a dentist/hygienist of the clinic."""
    from app.core.auth.service import hash_password

    dentist = User(
        email=f"dentist-{uuid4().hex[:8]}@test.clinic",
        password_hash=hash_password("TestPass1234"),
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(dentist)
    await db_session.flush()
    db_session.add(ClinicMembership(user_id=dentist.id, clinic_id=test_clinic.id, role="dentist"))
    await db_session.flush()
    return str(dentist.id)


async def _schedule(client: AsyncClient, headers: dict, patient_id: str, professional_id: str):
    return await client.post(
        "/api/v1/agenda/appointments",
        headers=headers,
        json={
            "patient_id": patient_id,
            "professional_id": professional_id,
            "cabinet": "Gabinete 1",
            "start_time": "2026-09-10T09:00:00Z",
            "end_time": "2026-09-10T09:30:00Z",
        },
    )


@pytest.mark.asyncio
async def test_scheduling_an_appointment_links_the_pending_recall(
    client: AsyncClient,
    auth_headers: dict,
    test_clinic: Clinic,
    test_patient: Patient,
    db_session: AsyncSession,
    dentist_id: str,
) -> None:
    created = await client.post(
        "/api/v1/recalls/",
        headers=auth_headers,
        json={
            "patient_id": str(test_patient.id),
            "due_month": "2026-08-01",
            "reason": "hygiene",
            "priority": "normal",
        },
    )
    assert created.status_code == 201, created.text
    recall_id = created.json()["data"]["id"]

    res = await _schedule(client, auth_headers, str(test_patient.id), dentist_id)
    assert res.status_code == 201, res.text
    appointment_id = res.json()["data"]["id"]

    recall = await db_session.get(Recall, recall_id)
    await db_session.refresh(recall)
    assert str(recall.linked_appointment_id) == appointment_id
    assert recall.status == "contacted_scheduled"


@pytest.mark.asyncio
async def test_ambiguous_recalls_are_left_alone(
    client: AsyncClient,
    auth_headers: dict,
    test_clinic: Clinic,
    test_patient: Patient,
    db_session: AsyncSession,
    dentist_id: str,
) -> None:
    """Two candidates → reception links manually; the handler must not guess."""
    for reason in ("hygiene", "checkup"):
        res = await client.post(
            "/api/v1/recalls/",
            headers=auth_headers,
            json={
                "patient_id": str(test_patient.id),
                "due_month": "2026-08-01",
                "reason": reason,
                "priority": "normal",
            },
        )
        assert res.status_code == 201, res.text

    res = await _schedule(client, auth_headers, str(test_patient.id), dentist_id)
    assert res.status_code == 201, res.text

    linked = await db_session.scalars(
        select(Recall.linked_appointment_id).where(Recall.patient_id == test_patient.id)
    )
    assert set(linked.all()) == {None}
