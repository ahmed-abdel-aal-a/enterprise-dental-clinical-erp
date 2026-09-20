"""Agent tools for the inventory stock list. Wrappers over InventoryService."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.agents import AgentContext, Tool, ToolCategory

from .schemas import ItemCategory
from .service import InventoryService


class ListItemsArgs(BaseModel):
    category: ItemCategory | None = None
    low_stock_only: bool = False
    limit: int = Field(default=20, ge=1, le=100)


class CreateItemArgs(BaseModel):
    name: str = Field(min_length=1)
    category: ItemCategory = "other"
    unit: str = "units"
    stock_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    min_quantity: Decimal = Field(default=Decimal("0"), ge=0)


class AdjustStockArgs(BaseModel):
    item_id: str = Field(min_length=1)
    delta: Decimal


def _summary(item) -> dict:
    return {
        "id": item.id,  # native UUID — the registry's jsonify coerces
        "name": item.name,
        "category": item.category,
        "unit": item.unit,
        "stock_quantity": item.stock_quantity,
        "min_quantity": item.min_quantity,
        "is_low_stock": item.is_low_stock,
    }


async def _list_items(ctx: AgentContext, params: ListItemsArgs) -> dict:
    items, total = await InventoryService.list_items(
        ctx.db,
        ctx.clinic_id,
        category=params.category,
        low_stock_only=params.low_stock_only,
        page=1,
        page_size=params.limit,
    )
    return {"total": total, "items": [_summary(i) for i in items]}


async def _create_item(ctx: AgentContext, params: CreateItemArgs) -> dict:
    from .schemas import InventoryItemCreate

    payload = InventoryItemCreate(
        name=params.name,
        category=params.category,
        unit=params.unit,
        stock_quantity=params.stock_quantity,
        min_quantity=params.min_quantity,
    )
    # AgentContext carries no user identity — agent-created items are
    # attributed to no staff row; the actor trail lives in agent_audit_logs.
    item = await InventoryService.create_item(ctx.db, ctx.clinic_id, payload, None)
    return _summary(item)


async def _adjust_stock(ctx: AgentContext, params: AdjustStockArgs) -> dict:
    from uuid import UUID

    item = await InventoryService.adjust_stock(
        ctx.db, ctx.clinic_id, UUID(params.item_id), params.delta
    )
    return _summary(item)


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="list_inventory_items",
            description=(
                "List the clinic's stock items with quantities, optionally "
                "filtered by category or limited to low-stock items."
            ),
            parameters=ListItemsArgs,
            handler=_list_items,
            permissions=["inventory.read"],
            category=ToolCategory.READ,
            # Item names/descriptions are user-entered prose — keep off the
            # cloud LLM path under redaction (same criterion as recalls'
            # get_recall and expenses' list/create).
            exposes_free_text=True,
        ),
        Tool(
            name="create_inventory_item",
            description=(
                "Add a new item to the clinic's stock list with its "
                "quantity and low-stock threshold."
            ),
            parameters=CreateItemArgs,
            handler=_create_item,
            permissions=["inventory.write"],
            category=ToolCategory.WRITE,
            exposes_free_text=True,
        ),
        Tool(
            name="adjust_inventory_stock",
            description=(
                "Apply a relative stock change (+/- delta) to an inventory "
                "item. Rejected if it would drive stock below zero."
            ),
            parameters=AdjustStockArgs,
            handler=_adjust_stock,
            permissions=["inventory.write"],
            category=ToolCategory.WRITE,
            exposes_free_text=True,
        ),
    ]
