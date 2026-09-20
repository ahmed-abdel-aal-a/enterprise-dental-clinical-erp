"""Agent tools for lab work orders, all scoped through AgentContext.clinic_id."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.agents import AgentContext, Tool, ToolCategory

from .schemas import LabOrderCreate, LabOrderUpdate, OrderStatus, WorkType
from .service import LabOrderService


class ListLabOrdersArgs(BaseModel):
    patient_id: UUID | None = None
    order_status: OrderStatus | None = None
    limit: int = Field(default=20, ge=1, le=100)


class CreateLabOrderArgs(BaseModel):
    patient_id: UUID
    lab_contact_id: UUID
    work_type: WorkType
    tooth_reference: str | None = None
    sent_date: date
    expected_date: date | None = None
    notes: str | None = None


class UpdateLabOrderStatusArgs(BaseModel):
    order_id: UUID
    status: OrderStatus


def _summary(order) -> dict:
    return {
        "id": order.id,  # native UUID — the registry's jsonify coerces
        "patient_id": order.patient_id,
        "lab_contact_id": order.lab_contact_id,
        "work_type": order.work_type,
        "status": order.status,
        "sent_date": order.sent_date,
        "expected_date": order.expected_date,
    }


async def _list(ctx: AgentContext, params: ListLabOrdersArgs) -> dict:
    orders, total = await LabOrderService.list_orders(
        ctx.db,
        ctx.clinic_id,
        patient_id=params.patient_id,
        order_status=params.order_status,
        page=1,
        page_size=params.limit,
    )
    return {"total": total, "lab_orders": [_summary(order) for order in orders]}


async def _create(ctx: AgentContext, params: CreateLabOrderArgs) -> dict:
    payload = LabOrderCreate(
        patient_id=params.patient_id,
        lab_contact_id=params.lab_contact_id,
        work_type=params.work_type,
        tooth_reference=params.tooth_reference,
        sent_date=params.sent_date,
        expected_date=params.expected_date,
        notes=params.notes,
    )
    # AgentContext carries no user identity — agent-initiated orders are
    # attributed to no staff row (created_by stays null); the actor trail
    # lives in agent_audit_logs instead.
    return _summary(await LabOrderService.create_order(ctx.db, ctx.clinic_id, payload, None))


async def _update_status(ctx: AgentContext, params: UpdateLabOrderStatusArgs) -> dict:
    order = await LabOrderService.update_order(
        ctx.db, ctx.clinic_id, params.order_id, LabOrderUpdate(status=params.status)
    )
    return _summary(order)


def get_tools() -> list[Tool]:
    return [
        Tool(
            "list_lab_orders",
            "List lab orders for this clinic.",
            ListLabOrdersArgs,
            _list,
            ["lab_orders.read"],
            ToolCategory.READ,
        ),
        Tool(
            "create_lab_order",
            "Create a lab work order for this clinic.",
            CreateLabOrderArgs,
            _create,
            ["lab_orders.write"],
            ToolCategory.WRITE,
        ),
        Tool(
            "update_lab_order_status",
            "Update a lab order status for this clinic.",
            UpdateLabOrderStatusArgs,
            _update_status,
            ["lab_orders.write"],
            ToolCategory.WRITE,
        ),
    ]
