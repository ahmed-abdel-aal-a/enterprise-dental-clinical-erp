"""FY-scoped GST document number allocation.

GST Rule 46(b): the serial must be consecutive and unique within the
financial year (April–March). Billing's sequential_number resets on the
calendar year, which is exactly why the module keeps its own counter —
these tests pin the two behaviours that reuse of billing's number broke:
no reset at January 1st, and a fresh series every April 1st.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.india_gst.service import allocate_fy_document_number


async def test_serial_continues_across_calendar_year_boundary(
    db_session: AsyncSession, india_gst_clinic: Clinic
):
    dec = await allocate_fy_document_number(
        db_session, india_gst_clinic.id, "GST", date(2026, 12, 31)
    )
    jan = await allocate_fy_document_number(
        db_session, india_gst_clinic.id, "GST", date(2027, 1, 15)
    )
    assert dec == "GST/FY26-27/0001"
    # Same FY → the serial keeps counting; with billing's calendar-year
    # sequence this came back as .../0001 again (a duplicate).
    assert jan == "GST/FY26-27/0002"


async def test_serial_restarts_each_april(db_session: AsyncSession, india_gst_clinic: Clinic):
    march = await allocate_fy_document_number(
        db_session, india_gst_clinic.id, "GST", date(2027, 3, 31)
    )
    april = await allocate_fy_document_number(
        db_session, india_gst_clinic.id, "GST", date(2027, 4, 1)
    )
    assert march == "GST/FY26-27/0001"
    assert april == "GST/FY27-28/0001"


async def test_prefixes_count_independently(db_session: AsyncSession, india_gst_clinic: Clinic):
    when = date(2026, 8, 21)
    inv = await allocate_fy_document_number(db_session, india_gst_clinic.id, "GST", when)
    cn = await allocate_fy_document_number(db_session, india_gst_clinic.id, "CN", when)
    assert inv == "GST/FY26-27/0001"
    assert cn == "CN/FY26-27/0001"


async def test_separate_clinics_get_independent_sequences(
    db_session: AsyncSession, india_gst_clinic: Clinic
):
    """Two clinics allocating in the same FY must each start at 0001."""
    from uuid import uuid4

    from app.core.auth.models import Clinic

    other = Clinic(
        id=uuid4(), name="Other Clinic", tax_id="B2", address={}, settings={"country": "IN"}
    )
    db_session.add(other)
    await db_session.flush()

    when = date(2026, 8, 21)
    a1 = await allocate_fy_document_number(db_session, india_gst_clinic.id, "GST", when)
    b1 = await allocate_fy_document_number(db_session, other.id, "GST", when)
    a2 = await allocate_fy_document_number(db_session, india_gst_clinic.id, "GST", when)
    b2 = await allocate_fy_document_number(db_session, other.id, "GST", when)

    assert a1 == "GST/FY26-27/0001"
    assert b1 == "GST/FY26-27/0001"
    assert a2 == "GST/FY26-27/0002"
    assert b2 == "GST/FY26-27/0002"


async def test_repeated_allocations_never_produce_duplicate_numbers(
    db_session: AsyncSession, india_gst_clinic: Clinic
):
    """Ten allocations for the same (clinic, prefix, FY) must all come
    back unique and consecutive — the ``SELECT … FOR UPDATE`` row lock
    plus the unique constraint on ``(clinic_id, prefix, fy_label)`` is
    what serializes real concurrent issuance in production. (A genuine
    concurrent race — e.g. via ``asyncio.gather`` on this session — isn't
    reproducible in the single-session test harness: ``AsyncSession``
    itself isn't safe for concurrent use, so `InvalidRequestError:
    Session is already flushing` fires before the DB-level lock is
    even reached. Same rationale as
    `tests/modules/billing/test_issue_and_payment_guards.py` — the lock
    is exercised here the same way it's exercised there: sequential
    calls proving the counter never drops or repeats a serial.)
    """
    when = date(2026, 8, 21)
    results = [
        await allocate_fy_document_number(db_session, india_gst_clinic.id, "GST", when)
        for _ in range(10)
    ]
    assert results == [f"GST/FY26-27/{n:04d}" for n in range(1, 11)]
    assert len(set(results)) == 10
