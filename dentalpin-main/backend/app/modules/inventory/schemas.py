"""Pydantic schemas for the inventory module."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ItemCategory = Literal["consumables", "equipment", "office", "other"]


class InventoryItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: ItemCategory = "other"
    unit: str = Field(default="units", max_length=20)
    stock_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    min_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    notes: str | None = Field(default=None, max_length=2000)
    branch_id: UUID | None = None


class InventoryItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: ItemCategory | None = None
    unit: str | None = Field(default=None, max_length=20)
    # Absolute set — the CHECK constraint still blocks negatives at the DB
    # level. Incremental changes must go through the atomic adjust endpoint.
    stock_quantity: Decimal | None = Field(default=None, ge=0)
    min_quantity: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)
    branch_id: UUID | None = None


class StockAdjustPayload(BaseModel):
    """Relative stock change. ``delta`` may be negative (consumption).

    No ``reason`` field yet — there is no movements table to record it
    against until the inventory core upgrade (#226).
    """

    delta: Decimal


class InventoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    branch_id: UUID | None = None
    name: str
    category: ItemCategory
    unit: str
    stock_quantity: Decimal
    min_quantity: Decimal
    is_low_stock: bool
    notes: str | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
