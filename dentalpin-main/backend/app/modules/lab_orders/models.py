"""SQLAlchemy model for a lab work order."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class LabOrder(Base, TimestampMixin):
    """Work sent to an external laboratory for a specific patient."""

    __tablename__ = "lab_orders"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=False)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    lab_contact_id: Mapped[UUID] = mapped_column(
        ForeignKey("contacts.id"), index=True, nullable=False
    )

    work_type: Mapped[str] = mapped_column(String(20), index=True)
    tooth_reference: Mapped[str | None] = mapped_column(String(50))
    impression_type: Mapped[str | None] = mapped_column(String(20))
    antagonist_info: Mapped[str | None] = mapped_column(String(500))
    shade: Mapped[str | None] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), index=True, default="sent")

    sent_date: Mapped[date] = mapped_column(Date)
    expected_date: Mapped[date | None] = mapped_column(Date)
    received_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
