"""InventoryItem model — one stock-list row for the clinic.

Base version (#220): a flat stock list with per-item minimum quantities
and low-stock awareness. Cost tracking, stock movements and
auto-deduction arrive later with the inventory core upgrade (#226).

Concurrency: ``stock_quantity`` carries a CHECK (>= 0) constraint at the
DB level, and quantity changes go through an atomic single-UPDATE path
(:meth:`InventoryService.adjust_stock`) — never read-modify-write. PR
#153's earlier inventory died on exactly this race; see roadmap #220.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.branches.models import ClinicBranch


class InventoryItem(Base, TimestampMixin):
    """A stock item the clinic keeps on hand."""

    __tablename__ = "inventory_items"
    __table_args__ = (
        CheckConstraint("stock_quantity >= 0", name="ck_inventory_items_stock_non_negative"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    branch_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinic_branches.id"), index=True, nullable=True
    )

    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50), index=True)
    unit: Mapped[str] = mapped_column(String(20), default="units")
    stock_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    min_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))

    branch: Mapped[ClinicBranch | None] = relationship()

    @property
    def is_low_stock(self) -> bool:
        """True when current stock has reached the minimum threshold."""
        return self.stock_quantity <= self.min_quantity
