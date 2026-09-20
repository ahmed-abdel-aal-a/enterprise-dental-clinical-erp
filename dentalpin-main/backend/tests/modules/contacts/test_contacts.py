"""contacts: happy-path CRUD + tenant isolation.

This module had zero test coverage. Every query in ContactService is
already clinic_id-scoped -- this suite locks that in as a regression
test rather than fixing anything.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.contacts.schemas import ContactCreate, ContactUpdate
from app.modules.contacts.service import ContactService


@pytest.mark.asyncio
async def test_create_list_update_delete_happy_path(db_session: AsyncSession, test_clinic: Clinic):
    contact = await ContactService.create_contact(
        db_session,
        test_clinic.id,
        ContactCreate(name="Acme Dental Lab", contact_type="lab", phone="555-0100"),
    )
    assert contact.name == "Acme Dental Lab"
    assert contact.is_active is True

    rows, total = await ContactService.list_contacts(db_session, test_clinic.id)
    assert total == 1
    assert rows[0].id == contact.id

    updated = await ContactService.update_contact(
        db_session, test_clinic.id, contact.id, ContactUpdate(phone="555-0199")
    )
    assert updated.phone == "555-0199"
    assert updated.name == "Acme Dental Lab"  # unset fields untouched

    await ContactService.delete_contact(db_session, test_clinic.id, contact.id)

    # Soft delete: excluded from the default (active-only) listing...
    rows, total = await ContactService.list_contacts(db_session, test_clinic.id)
    assert total == 0

    # ...but still fetchable directly, and still shows is_active=False.
    fetched = await ContactService.get_contact(db_session, test_clinic.id, contact.id)
    assert fetched.is_active is False


@pytest.mark.asyncio
async def test_contacts_are_clinic_scoped(db_session: AsyncSession, test_clinic: Clinic):
    other_clinic = Clinic(
        id=uuid4(), name="Other Clinic", tax_id="B77777777", address={}, settings={}
    )
    db_session.add(other_clinic)
    await db_session.commit()

    other_contact = await ContactService.create_contact(
        db_session,
        other_clinic.id,
        ContactCreate(name="Other Clinic's Lab", contact_type="lab"),
    )

    # test_clinic must not be able to fetch, update, or list a contact
    # that belongs to a different clinic.
    with pytest.raises(HTTPException) as exc_info:
        await ContactService.get_contact(db_session, test_clinic.id, other_contact.id)
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException):
        await ContactService.update_contact(
            db_session, test_clinic.id, other_contact.id, ContactUpdate(name="Hijacked")
        )

    rows, total = await ContactService.list_contacts(db_session, test_clinic.id)
    assert total == 0
    assert other_contact.id not in [r.id for r in rows]
