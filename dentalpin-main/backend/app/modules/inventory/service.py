"""InventoryService — stock-list CRUD and atomic stock adjustments.

Quantity changes are guarded at the DB level (CHECK constraint + atomic
relative UPDATE), never read-modify-write in app code — PR #153's race
post-mortem, roadmap #220.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import event_bus
from app.core.events.types import EventType

from .models import InventoryItem
from .schemas import InventoryItemCreate, InventoryItemUpdate


class InventoryService:
    @staticmethod
    async def create_item(
        db: AsyncSession,
        clinic_id: UUID,
        payload: InventoryItemCreate,
        created_by: UUID | None,
    ) -> InventoryItem:
        item = InventoryItem(
            clinic_id=clinic_id,
            branch_id=payload.branch_id,
            name=payload.name,
            category=payload.category,
            unit=payload.unit,
            stock_quantity=payload.stock_quantity,
            min_quantity=payload.min_quantity,
            notes=payload.notes,
            created_by=created_by,
        )
        db.add(item)
        await db.flush()
        # A brand-new item already at/below its threshold is a low-stock
        # alert on day one.
        await InventoryService._publish_low_if_crossed(db, item, was_low=False)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def list_items(
        db: AsyncSession,
        clinic_id: UUID,
        category: str | None = None,
        low_stock_only: bool = False,
        page: int = 1,
        page_size: int = 20,
        branch_id: UUID | None = None,
    ) -> tuple[list[InventoryItem], int]:
        stmt = select(InventoryItem).where(InventoryItem.clinic_id == clinic_id)
        if branch_id:
            stmt = stmt.where(
                or_(InventoryItem.branch_id == branch_id, InventoryItem.branch_id.is_(None))
            )
        if category:
            stmt = stmt.where(InventoryItem.category == category)
        if low_stock_only:
            # SQL-level filter — stays correct under concurrency.
            stmt = stmt.where(InventoryItem.stock_quantity <= InventoryItem.min_quantity)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.order_by(InventoryItem.name.asc()).offset((page - 1) * page_size).limit(page_size)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows), total

    @staticmethod
    async def get_item(db: AsyncSession, clinic_id: UUID, item_id: UUID) -> InventoryItem:
        stmt = select(InventoryItem).where(
            InventoryItem.id == item_id, InventoryItem.clinic_id == clinic_id
        )
        item = (await db.execute(stmt)).scalar_one_or_none()
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        return item

    @staticmethod
    async def update_item(
        db: AsyncSession, clinic_id: UUID, item_id: UUID, payload: InventoryItemUpdate
    ) -> InventoryItem:
        item = await InventoryService.get_item(db, clinic_id, item_id)
        was_low = item.is_low_stock
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        await db.flush()
        await InventoryService._publish_low_if_crossed(db, item, was_low=was_low)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete_item(db: AsyncSession, clinic_id: UUID, item_id: UUID) -> None:
        item = await InventoryService.get_item(db, clinic_id, item_id)
        await db.delete(item)
        await db.commit()

    @staticmethod
    async def adjust_stock(
        db: AsyncSession,
        clinic_id: UUID,
        item_id: UUID,
        delta: Decimal,
    ) -> InventoryItem:
        """Atomically apply a relative stock change (+/- ``delta``).

        The UPDATE carries its own guard (``stock_quantity + delta >= 0``)
        so concurrent adjustments can never drive the row negative or lose
        an increment to a lost update — the DB arbitrates, not the app.
        Returns 409 when the guard rejects the delta.
        """
        # get_item gives us the 404 plus the pre-adjust low state, so the
        # alert only fires on the not-low -> low crossing.
        pre = await InventoryService.get_item(db, clinic_id, item_id)
        was_low = pre.is_low_stock

        stmt = (
            update(InventoryItem)
            .where(
                InventoryItem.id == item_id,
                InventoryItem.clinic_id == clinic_id,
                InventoryItem.stock_quantity + delta >= 0,
            )
            .values(stock_quantity=InventoryItem.stock_quantity + delta)
            .returning(InventoryItem)
        )
        updated = (await db.execute(stmt)).scalar_one_or_none()
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="adjustment would drive stock below zero",
            )

        # Low-stock crossing is evaluated on the freshly returned row.
        await InventoryService._publish_low_if_crossed(db, updated, was_low=was_low)
        await db.commit()
        await db.refresh(updated)
        return updated

    @staticmethod
    async def _publish_low_if_crossed(
        db: AsyncSession, item: InventoryItem, *, was_low: bool
    ) -> None:
        """Fire ``inventory.low_stock`` once, on the not-low → low crossing."""
        if not was_low and item.is_low_stock:
            await event_bus.publish(
                EventType.INVENTORY_STOCK_LOW,
                {
                    "clinic_id": str(item.clinic_id),
                    "item_id": str(item.id),
                    "name": item.name,
                    "category": item.category,
                    "stock_quantity": float(item.stock_quantity),
                    "min_quantity": float(item.min_quantity),
                },
                db=db,
            )
