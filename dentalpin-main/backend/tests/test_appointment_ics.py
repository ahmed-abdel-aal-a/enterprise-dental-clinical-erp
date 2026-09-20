"""RFC 5545 export of an appointment (#129).

Unit tests exercise the pure builder (CRLF, escaping, UTC, folding,
stable UID) on transient ORM objects — no DB. API tests cover the
endpoint: happy path returns a parseable VEVENT, a wrong-clinic
appointment is a 404, and a SUMMARY containing a comma is escaped.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership
from app.modules.agenda.ics import build_appointment_ics
from app.modules.agenda.models import Appointment
from tests.test_appointment_transitions import _mkapt, _mkworld

# ---------------------------------------------------------------------------
# Unit — pure builder
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)


def _clinic(**overrides) -> Clinic:
    values = dict(
        id=uuid4(),
        name="Clínica Demo",
        tax_id="B1",
        address={"street": "Calle Gran Vía 123", "city": "Madrid"},
        settings={},
    )
    values.update(overrides)
    return Clinic(**values)


def _appointment(**overrides) -> Appointment:
    values = dict(
        id=uuid4(),
        clinic_id=uuid4(),
        professional_id=uuid4(),
        start_time=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 9, 1, 10, 30, tzinfo=UTC),
        treatment_type="Limpieza dental",
        status="scheduled",
    )
    values.update(overrides)
    return Appointment(**values)


def test_crlf_endings_and_envelope() -> None:
    ics = build_appointment_ics(_appointment(), _clinic(), now=_NOW)
    assert ics.startswith("BEGIN:VCALENDAR\r\n")
    assert ics.endswith("END:VCALENDAR\r\n")
    # Every line break is CRLF — no bare \n anywhere.
    assert "\n" not in ics.replace("\r\n", "")


def test_timestamps_are_utc_z() -> None:
    # A clinic-local aware time one hour ahead of UTC must convert, not
    # be reinterpreted.
    madrid = timezone(timedelta(hours=2))
    apt = _appointment(
        start_time=datetime(2026, 9, 1, 12, 0, tzinfo=madrid),
        end_time=datetime(2026, 9, 1, 12, 30, tzinfo=madrid),
    )
    ics = build_appointment_ics(apt, _clinic(), now=_NOW)
    assert "DTSTART:20260901T100000Z" in ics
    assert "DTEND:20260901T103000Z" in ics
    assert f"DTSTAMP:{_NOW.strftime('%Y%m%dT%H%M%SZ')}" in ics


def test_uid_is_stable_and_domain_qualified() -> None:
    apt = _appointment()
    first = build_appointment_ics(apt, _clinic(), now=_NOW)
    second = build_appointment_ics(apt, _clinic(), now=_NOW)
    assert f"UID:{apt.id}@dentalpin.com\r\n" in first
    assert first == second


def test_text_values_are_escaped() -> None:
    apt = _appointment(treatment_type="Cleaning, deep; with\nnotes\\here")
    ics = build_appointment_ics(apt, _clinic(name="Acme, S.L."), now=_NOW)
    assert "SUMMARY:Cleaning\\, deep\\; with\\nnotes\\\\here" in ics
    assert "LOCATION:Acme\\, S.L." in ics


def test_long_lines_fold_at_75_octets() -> None:
    apt = _appointment(treatment_type="Rehabilitación oral completa " * 6)
    ics = build_appointment_ics(apt, _clinic(), now=_NOW)
    for line in ics.split("\r\n"):
        assert len(line.encode("utf-8")) <= 75
    # Folded continuations start with a single space.
    assert "\r\n " in ics


def test_cancelled_status_maps_to_cancelled_vevent() -> None:
    ics = build_appointment_ics(_appointment(status="cancelled"), _clinic(), now=_NOW)
    assert "STATUS:CANCELLED" in ics
    ics = build_appointment_ics(_appointment(status="confirmed"), _clinic(), now=_NOW)
    assert "STATUS:CONFIRMED" in ics


# ---------------------------------------------------------------------------
# API — endpoint behaviour
# ---------------------------------------------------------------------------


async def _join_authed_user_to(db: AsyncSession, client: AsyncClient, auth_headers, clinic_id):
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = UUID(me.json()["data"]["user"]["id"])
    db.add(ClinicMembership(id=uuid4(), user_id=user_id, clinic_id=clinic_id, role="admin"))
    await db.commit()


@pytest.mark.asyncio
async def test_export_returns_parseable_vevent(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    world = await _mkworld(db_session)
    await _join_authed_user_to(db_session, client, auth_headers, world["clinic_id"])
    apt = await _mkapt(db_session, world, start=datetime(2026, 9, 2, 9, 0, tzinfo=UTC))

    r = await client.get(f"/api/v1/agenda/appointments/{apt.id}.ics", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/calendar")
    assert f'filename="appointment-{apt.id}.ics"' in r.headers["content-disposition"]
    body = r.text
    assert "BEGIN:VEVENT" in body and "END:VEVENT" in body
    assert f"UID:{apt.id}@dentalpin.com" in body
    assert "DTSTART:20260902T090000Z" in body


@pytest.mark.asyncio
async def test_export_escapes_comma_in_summary(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    world = await _mkworld(db_session)
    await _join_authed_user_to(db_session, client, auth_headers, world["clinic_id"])
    apt = await _mkapt(db_session, world, start=datetime(2026, 9, 3, 9, 0, tzinfo=UTC))
    row = (
        await db_session.execute(select(Appointment).where(Appointment.id == apt.id))
    ).scalar_one()
    row.treatment_type = "Limpieza, revisión"
    await db_session.commit()

    r = await client.get(f"/api/v1/agenda/appointments/{apt.id}.ics", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert "SUMMARY:Limpieza\\, revisión" in r.text


@pytest.mark.asyncio
async def test_export_is_clinic_scoped(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> None:
    """An appointment of a clinic the user does not belong to is a 404."""
    mine = await _mkworld(db_session)
    await _join_authed_user_to(db_session, client, auth_headers, mine["clinic_id"])
    other = await _mkworld(db_session)
    foreign_apt = await _mkapt(db_session, other, start=datetime(2026, 9, 4, 9, 0, tzinfo=UTC))

    r = await client.get(f"/api/v1/agenda/appointments/{foreign_apt.id}.ics", headers=auth_headers)
    assert r.status_code == 404
