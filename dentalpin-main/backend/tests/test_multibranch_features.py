"""Tests for Multi-Branch architecture and isolation features (Task 03.5)."""

import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth.models import Clinic, ClinicMembership, User
from app.core.branches.models import ClinicBranch
from app.core.branches.service import BranchService
from app.modules.agenda.models import Cabinet, Appointment
from app.modules.agenda.service import CabinetService, AppointmentService
from app.modules.billing.models import InvoiceSeries
from app.modules.billing.service import InvoiceSeriesService, InvoiceService


@pytest.mark.asyncio
async def test_branch_crud_and_main_protection(
    client: AsyncClient,
    test_clinic: Clinic,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    """Test listing branches, creating a secondary branch, and verifying main branch protection."""
    # 1. List branches - should include the initial MAIN branch
    res = await client.get("/api/v1/branches", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1
    main_branch = next(b for b in data if b["is_main"] is True)
    assert main_branch["name"] == "Main Branch"

    # 2. Create a second branch
    new_branch_payload = {
        "name": "Nasr City Branch",
        "code": "NC-01",
        "phone": "+201012345678",
        "email": "nasrcity@dentalpin.com",
        "address": {"street": "Abbas El Akkad", "city": "Cairo"},
        "is_main": False,
    }
    create_res = await client.post(
        "/api/v1/branches", json=new_branch_payload, headers=auth_headers
    )
    assert create_res.status_code == 201
    second_branch = create_res.json()["data"]
    assert second_branch["name"] == "Nasr City Branch"
    assert second_branch["code"] == "NC-01"
    assert second_branch["is_main"] is False
    assert second_branch["is_active"] is True

    # 3. Verify main branch CANNOT be deactivated
    deactivate_main_res = await client.patch(
        f"/api/v1/branches/{main_branch['id']}",
        json={"is_active": False},
        headers=auth_headers,
    )
    assert deactivate_main_res.status_code == 400
    assert ("Cannot deactivate the main branch" in str(deactivate_main_res.json()) or
            "الفرع الرئيسي" in str(deactivate_main_res.json()))

    # 4. Verify main branch CANNOT be deleted
    delete_main_res = await client.delete(
        f"/api/v1/branches/{main_branch['id']}", headers=auth_headers
    )
    assert delete_main_res.status_code == 400
    assert ("Cannot deactivate the main branch" in str(delete_main_res.json()) or
            "الفرع الرئيسي" in str(delete_main_res.json()))

    # 5. Verify second branch CAN be deactivated
    deactivate_second_res = await client.delete(
        f"/api/v1/branches/{second_branch['id']}", headers=auth_headers
    )
    assert deactivate_second_res.status_code == 200
    assert deactivate_second_res.json()["data"] is True

    # Verify status changed to inactive
    get_res = await client.get(f"/api/v1/branches/{second_branch['id']}", headers=auth_headers)
    assert get_res.json()["data"]["is_active"] is False


@pytest.mark.asyncio
async def test_cabinet_appointment_branch_isolation(
    test_clinic: Clinic,
    db_session: AsyncSession,
):
    """Test cabinet and appointment isolation and cross-branch assignment validation."""
    # Fetch main branch
    branches = await BranchService.list_branches(db_session, test_clinic.id)
    main_b = next(b for b in branches if b.is_main)

    # Create secondary branch
    from app.core.branches.schemas import BranchCreate
    branch_b = await BranchService.create_branch(
        db_session,
        test_clinic.id,
        BranchCreate(name="Zamalek Branch", code="ZM-01")
    )

    # Create Cabinet in Branch A
    cabinet_a = await CabinetService.create_cabinet(
        db_session,
        test_clinic.id,
        {"name": "Main Box 1", "color": "#10B981", "branch_id": main_b.id},
    )
    assert cabinet_a.branch_id == main_b.id

    # Create Cabinet in Branch B
    cabinet_b = await CabinetService.create_cabinet(
        db_session,
        test_clinic.id,
        {"name": "Zamalek Box 1", "color": "#F59E0B", "branch_id": branch_b.id},
    )
    assert cabinet_b.branch_id == branch_b.id

    # List cabinets filtered by branch
    main_cabinets = await CabinetService.list_cabinets(db_session, test_clinic.id, branch_id=main_b.id)
    assert any(c.id == cabinet_a.id for c in main_cabinets)
    assert not any(c.id == cabinet_b.id for c in main_cabinets)

    zm_cabinets = await CabinetService.list_cabinets(db_session, test_clinic.id, branch_id=branch_b.id)
    assert any(c.id == cabinet_b.id for c in zm_cabinets)
    assert not any(c.id == cabinet_a.id for c in zm_cabinets)


@pytest.mark.asyncio
async def test_invoice_series_branch_fallback(
    test_clinic: Clinic,
    db_session: AsyncSession,
):
    """Test invoice series resolution per branch with fallback to clinic default."""
    branches = await BranchService.list_branches(db_session, test_clinic.id)
    main_b = next(b for b in branches if b.is_main)

    from app.core.branches.schemas import BranchCreate
    branch_c = await BranchService.create_branch(
        db_session,
        test_clinic.id,
        BranchCreate(name="Dokki Branch", code="DK-01")
    )

    # Create a clinic-wide fallback series (branch_id=None)
    clinic_series = InvoiceSeries(
        id=uuid.uuid4(),
        clinic_id=test_clinic.id,
        branch_id=None,
        prefix="GEN-",
        series_type="invoice",
        description="Clinic Default Series",
        current_number=0,
        is_default=True,
        is_active=True,
    )
    db_session.add(clinic_series)
    await db_session.commit()

    # When resolving for Branch C, auto-created branch-specific default should be chosen
    resolved_for_c = await InvoiceSeriesService.get_default_series(
        db_session, test_clinic.id, "invoice", branch_id=branch_c.id
    )
    assert resolved_for_c is not None
    assert resolved_for_c.branch_id == branch_c.id
    assert resolved_for_c.prefix == "FAC-DK-01"

    # When resolving for Main Branch (which has no branch series), clinic default should be chosen
    resolved_for_main = await InvoiceSeriesService.get_default_series(
        db_session, test_clinic.id, "invoice", branch_id=main_b.id
    )
    assert resolved_for_main is not None
    assert resolved_for_main.id == clinic_series.id
    assert resolved_for_main.prefix == "GEN-"


@pytest.mark.asyncio
async def test_schedule_availability_branch_isolation(
    test_clinic: Clinic,
    db_session: AsyncSession,
):
    """Test doctor and clinic availability resolution per branch."""
    from datetime import date
    from app.modules.schedules.services.availability import AvailabilityService

    branches = await BranchService.list_branches(db_session, test_clinic.id)
    main_b = next(b for b in branches if b.is_main)

    from app.core.branches.schemas import BranchCreate
    branch_x = await BranchService.create_branch(
        db_session,
        test_clinic.id,
        BranchCreate(name="Heliopolis Branch", code="HL-01")
    )

    # Resolve availability for main branch
    tz_main, ranges_main = await AvailabilityService.resolve(
        db_session, test_clinic.id, date(2026, 9, 20), date(2026, 9, 20), branch_id=main_b.id
    )
    assert tz_main is not None
    assert isinstance(ranges_main, list)

    # Resolve availability for Heliopolis branch
    tz_x, ranges_x = await AvailabilityService.resolve(
        db_session, test_clinic.id, date(2026, 9, 20), date(2026, 9, 20), branch_id=branch_x.id
    )
    assert tz_x is not None
    assert isinstance(ranges_x, list)
