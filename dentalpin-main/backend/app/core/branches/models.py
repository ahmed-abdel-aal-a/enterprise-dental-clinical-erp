"""Clinic Branch entity representing a physical location."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, ClinicMembership
    from app.modules.agenda.models import Appointment, Cabinet
    from app.modules.billing.models import Invoice, InvoiceSeries
    from app.modules.inventory.models import InventoryItem
    from app.modules.schedules.models import ScheduleShift


class ClinicBranch(Base, TimestampMixin):
    """Clinic Branch entity - represents a physical clinic location/facility."""

    __tablename__ = "clinic_branches"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    address: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    clinic: Mapped["Clinic"] = relationship(back_populates="branches")
    cabinets: Mapped[list["Cabinet"]] = relationship(
        back_populates="branch",
        cascade="all, delete-orphan",
        order_by="Cabinet.display_order",
    )
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="branch")
    invoice_series: Mapped[list["InvoiceSeries"]] = relationship(back_populates="branch")
    inventory_items: Mapped[list["InventoryItem"]] = relationship(back_populates="branch")

    __table_args__ = (
        UniqueConstraint("clinic_id", "name", name="uq_clinic_branches_clinic_name"),
        UniqueConstraint("clinic_id", "code", name="uq_clinic_branches_clinic_code"),
        Index("ix_clinic_branches_clinic_id", "clinic_id"),
    )
