"""Clinic-timezone semantics for appointment datetimes (issue #161).

Naive datetimes entering the service are clinic-local wall-clock and must
be persisted as the equivalent UTC instant; aware datetimes pass through
unchanged; naive list filters are interpreted in the clinic timezone.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership, User
from app.core.auth.service import hash_password
from app.modules.agenda.models import Cabinet
from app.modules.agenda.service import AppointmentService
from app.modules.agenda.tz import as_utc, safe_zone
from app.modules.patients.models import Patient

LIMA = ZoneInfo("America/Lima")


async def _mkworld(db: AsyncSession) -> dict[str, UUID]:
    """Clinic in America/Lima (UTC-5, no DST) + staff + patient."""
    clinic = Clinic(
        id=uuid4(),
        name="Lima Clinic",
        tax_id="B00000002",
        timezone="America/Lima",
        settings={},
    )
    admin = User(
        id=uuid4(),
        email=f"admin-{uuid4().hex[:8]}@test.clinic",
        password_hash=hash_password("TestPass1234"),
        first_name="Admin",
        last_name="User",
        is_active=True,
    )
    dentist = User(
        id=uuid4(),
        email=f"dentist-{uuid4().hex[:8]}@test.clinic",
        password_hash=hash_password("TestPass1234"),
        first_name="Dentist",
        last_name="User",
        is_active=True,
    )
    db.add_all([clinic, admin, dentist])
    await db.flush()
    db.add_all(
        [
            ClinicMembership(id=uuid4(), user_id=admin.id, clinic_id=clinic.id, role="admin"),
            ClinicMembership(id=uuid4(), user_id=dentist.id, clinic_id=clinic.id, role="dentist"),
        ]
    )
    cabinet = Cabinet(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Gabinete 1",
        color="#3B82F6",
        display_order=0,
        is_active=True,
    )
    patient = Patient(id=uuid4(), clinic_id=clinic.id, first_name="Juan", last_name="Paciente")
    db.add_all([cabinet, patient])
    await db.commit()
    return {
        "clinic_id": clinic.id,
        "admin_id": admin.id,
        "dentist_id": dentist.id,
        "cabinet_id": cabinet.id,
        "patient_id": patient.id,
    }


def _payload(world: dict[str, UUID], start: datetime, end: datetime) -> dict:
    return {
        "patient_id": world["patient_id"],
        "professional_id": world["dentist_id"],
        "cabinet_id": world["cabinet_id"],
        "start_time": start,
        "end_time": end,
    }


@pytest.mark.asyncio
async def test_naive_create_is_clinic_local(db_session: AsyncSession):
    world = await _mkworld(db_session)
    apt = await AppointmentService.create_appointment(
        db_session,
        world["clinic_id"],
        _payload(world, datetime(2026, 8, 7, 11, 0), datetime(2026, 8, 7, 12, 0)),
    )
    # 11:00 America/Lima == 16:00 UTC
    assert apt.start_time.astimezone(UTC) == datetime(2026, 8, 7, 16, 0, tzinfo=UTC)
    assert apt.end_time.astimezone(UTC) == datetime(2026, 8, 7, 17, 0, tzinfo=UTC)
    # Round-trip: clinic wall-clock is what the user typed.
    assert apt.start_time.astimezone(LIMA).hour == 11


@pytest.mark.asyncio
async def test_aware_create_keeps_instant(db_session: AsyncSession):
    world = await _mkworld(db_session)
    start = datetime(2026, 8, 7, 16, 0, tzinfo=UTC)
    apt = await AppointmentService.create_appointment(
        db_session,
        world["clinic_id"],
        _payload(world, start, start + timedelta(hours=1)),
    )
    assert apt.start_time.astimezone(UTC) == start


@pytest.mark.asyncio
async def test_naive_list_filters_are_clinic_local(db_session: AsyncSession):
    world = await _mkworld(db_session)
    await AppointmentService.create_appointment(
        db_session,
        world["clinic_id"],
        # 22:00 Lima == 03:00 UTC next day — a UTC day window would miss it.
        _payload(world, datetime(2026, 8, 7, 22, 0), datetime(2026, 8, 7, 23, 0)),
    )
    await db_session.commit()
    items, total = await AppointmentService.list_appointments(
        db_session,
        world["clinic_id"],
        start_date=datetime(2026, 8, 7, 0, 0),
        end_date=datetime(2026, 8, 7, 23, 59, 59),
    )
    assert total == 1
    assert items[0].start_time.astimezone(LIMA).hour == 22


@pytest.mark.asyncio
async def test_naive_update_is_clinic_local(db_session: AsyncSession):
    world = await _mkworld(db_session)
    apt = await AppointmentService.create_appointment(
        db_session,
        world["clinic_id"],
        _payload(world, datetime(2026, 8, 7, 11, 0), datetime(2026, 8, 7, 12, 0)),
    )
    apt = await AppointmentService.update_appointment(
        db_session,
        apt,
        {"start_time": datetime(2026, 8, 7, 14, 0), "end_time": datetime(2026, 8, 7, 15, 0)},
    )
    assert apt.start_time.astimezone(UTC) == datetime(2026, 8, 7, 19, 0, tzinfo=UTC)


def test_as_utc_and_safe_zone():
    tz = safe_zone("America/Lima")
    assert as_utc(datetime(2026, 8, 7, 11, 0), tz) == datetime(2026, 8, 7, 16, 0, tzinfo=UTC)
    aware = datetime(2026, 8, 7, 11, 0, tzinfo=UTC)
    assert as_utc(aware, tz) == aware
    # Invalid ids fall back instead of raising.
    assert safe_zone("Not/AZone").key == "Europe/Madrid"
    assert safe_zone(None).key == "Europe/Madrid"
