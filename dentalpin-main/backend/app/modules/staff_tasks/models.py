"""StaffTask model — one handoff/task row on the clinic's board."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import User


class StaffTask(Base, TimestampMixin):
    """An internal task or handoff note between clinic staff members.

    Lifecycle: ``open`` → (optionally) ``claimed`` → ``done``, with
    ``cancelled`` as an escape hatch. ``assignee_id`` is optional while
    ``open`` — claiming assigns the claimer.
    """

    __tablename__ = "staff_tasks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)

    title: Mapped[str] = mapped_column(String(200))
    details: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    priority: Mapped[str] = mapped_column(String(10), default="normal")

    assignee_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))

    due_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Eager so list/get/refresh never lazy-load in async context; users is
    # a core table, so this is not a cross-module dependency.
    assignee: Mapped[User | None] = relationship("User", foreign_keys=[assignee_id], lazy="joined")

    @property
    def assignee_name(self) -> str | None:
        """Display name for the board — who has the task."""
        if self.assignee is None:
            return None
        return f"{self.assignee.first_name} {self.assignee.last_name}".strip() or None
