"""The `patient.archived` → document soft-archive cascade (audit #95, #183).

Two regressions are covered:

* the publisher must include ``clinic_id`` in the payload (it didn't);
* the cascade must actually run and be atomic with the archive.

The handler used to open its own ``async_session_maker`` session, which made
the end-to-end path untestable (the session is bound to the import-time event
loop) *and* non-atomic: it committed the archived documents even when the
request that archived the patient rolled back. It is transactional now
(ADR 0019), so both are covered here.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, User
from app.core.events import EventType, event_bus
from app.modules.media.models import Document
from app.modules.patients.models import Patient
from app.modules.patients.service import PatientService


async def _document(db: AsyncSession, clinic: Clinic, patient: Patient) -> Document:
    user_id = (await db.execute(select(User))).scalars().first().id
    doc = Document(
        clinic_id=clinic.id,
        patient_id=patient.id,
        document_type="other",
        title="Consentimiento",
        original_filename="consent.pdf",
        storage_path=f"/tmp/{uuid4()}.pdf",
        mime_type="application/pdf",
        file_size=1024,
        uploaded_by=user_id,
    )
    db.add(doc)
    await db.flush()
    return doc


@pytest.mark.asyncio
async def test_archive_patient_payload_includes_clinic_id(
    test_clinic: Clinic,
    test_patient: Patient,
    db_session: AsyncSession,
) -> None:
    captured: list[dict] = []

    async def _spy(data: dict) -> None:
        captured.append(data)

    event_bus.subscribe(EventType.PATIENT_ARCHIVED, _spy)
    try:
        await PatientService.archive_patient(db_session, test_patient)
    finally:
        event_bus.unsubscribe(EventType.PATIENT_ARCHIVED, _spy)

    assert captured, "patient.archived was not published"
    assert captured[0]["patient_id"] == str(test_patient.id)
    assert captured[0]["clinic_id"] == str(test_clinic.id)


@pytest.mark.asyncio
async def test_archiving_a_patient_archives_their_documents(
    test_clinic: Clinic,
    test_patient: Patient,
    db_session: AsyncSession,
) -> None:
    doc = await _document(db_session, test_clinic, test_patient)

    await PatientService.archive_patient(db_session, test_patient)

    await db_session.refresh(doc)
    assert doc.status == "archived"


@pytest.mark.asyncio
async def test_cascade_rolls_back_with_the_archive(
    test_clinic: Clinic,
    test_patient: Patient,
    db_session: AsyncSession,
) -> None:
    """The cascade runs on the publisher's session, so an archive that never
    commits leaves the documents alone. On its own session the handler
    committed them regardless (issue #183)."""
    doc = await _document(db_session, test_clinic, test_patient)
    await db_session.commit()
    # A rollback expires every mapped instance, so reading an attribute off
    # one afterwards would lazy-load outside the async context. Keep the ids.
    doc_id, patient_id = doc.id, test_patient.id

    await PatientService.archive_patient(db_session, test_patient)
    await db_session.rollback()

    doc_status = await db_session.scalar(select(Document.status).where(Document.id == doc_id))
    patient_status = await db_session.scalar(select(Patient.status).where(Patient.id == patient_id))
    assert doc_status == "active"
    assert patient_status != "archived"
