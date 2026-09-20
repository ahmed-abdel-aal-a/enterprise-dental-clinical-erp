"""activity_journal: HTTP surface — filters, pagination, tenant isolation."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.activity_journal.models import ActivityJournalEntry


def _row(clinic_id, event_type: str, occurred: datetime, patient_id=None):
    return ActivityJournalEntry(
        clinic_id=clinic_id,
        event_type=event_type,
        source_table=event_type.split(".", 1)[0],
        patient_id=patient_id,
        payload={"clinic_id": str(clinic_id)},
        occurred_at=occurred,
    )


@pytest.mark.asyncio
async def test_list_filters_and_pagination_over_http(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_clinic: Clinic
):
    """HTTP-level regression for the filters: date params used to be typed
    as str in sibling modules and 500'd on asyncpg once actually sent."""
    pid = uuid4()
    db_session.add_all(
        [
            _row(
                test_clinic.id,
                "appointment.scheduled",
                datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
                pid,
            ),
            _row(
                test_clinic.id,
                "appointment.completed",
                datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
                pid,
            ),
            _row(test_clinic.id, "budget.sent", datetime(2026, 9, 1, 9, 0, tzinfo=UTC)),
        ]
    )
    await db_session.commit()

    async def _list(**params) -> dict:
        res = await client.get("/api/v1/activity_journal/", params=params, headers=auth_headers)
        assert res.status_code == 200, res.text
        return res.json()

    body = await _list()
    assert body["total"] == 3
    # Ordered by occurred_at desc.
    assert [e["event_type"] for e in body["data"]] == [
        "budget.sent",
        "appointment.completed",
        "appointment.scheduled",
    ]

    august = await _list(date_from="2026-08-01", date_to="2026-08-31")
    assert august["total"] == 2

    by_type = await _list(event_type="appointment.completed")
    assert by_type["total"] == 1
    assert by_type["data"][0]["patient_id"] == str(pid)

    by_patient = await _list(patient_id=str(pid))
    assert by_patient["total"] == 2

    paged = await _list(page=2, page_size=2)
    assert paged["total"] == 3
    assert len(paged["data"]) == 1


@pytest.mark.asyncio
async def test_entries_are_clinic_scoped_over_http(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_clinic: Clinic
):
    other = Clinic(id=uuid4(), name="Other Clinic", tax_id="B33333333", address={}, settings={})
    db_session.add(other)
    await db_session.flush()
    db_session.add(_row(other.id, "patient.created", datetime.now(UTC)))
    await db_session.commit()

    res = await client.get("/api/v1/activity_journal/", headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total"] == 0
    assert body["data"] == []


@pytest.mark.asyncio
async def test_get_single_entry_scoped(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_clinic: Clinic
):
    entry = _row(test_clinic.id, "invoice.sent", datetime(2026, 8, 10, tzinfo=UTC))
    db_session.add(entry)
    await db_session.commit()

    res = await client.get(f"/api/v1/activity_journal/{entry.id}", headers=auth_headers)
    assert res.status_code == 200, res.text
    assert res.json()["data"]["event_type"] == "invoice.sent"

    res = await client.get(f"/api/v1/activity_journal/{uuid4()}", headers=auth_headers)
    assert res.status_code == 404
