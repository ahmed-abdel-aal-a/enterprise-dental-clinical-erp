"""Agent tools for the billing module.

Supports read operations and atomic draft invoice emission with supervisor confirmation.
Session boundaries (commit/rollback) are governed exclusively by the orchestrator stream.
"""

from __future__ import annotations

from datetime import date as date_cls
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.agents import AgentContext, Tool, ToolCategory
from .models import InvoiceSeries
from .schemas import InvoiceStatus
from .service import InvoiceItemService, InvoiceSeriesService, InvoiceService


class ListInvoicesArgs(BaseModel):
    patient_id: UUID | None = None
    status: list[InvoiceStatus] | None = None
    date_from: date_cls | None = None
    date_to: date_cls | None = None
    overdue: bool | None = Field(
        default=None, description="Solo facturas emitidas/parciales con vencimiento pasado."
    )
    is_credit_note: bool | None = None
    limit: int = Field(default=20, ge=1, le=50)


class GetInvoiceArgs(BaseModel):
    invoice_id: UUID


class InvoiceItemInput(BaseModel):
    description: str = Field(min_length=1, max_length=255, description="وصف الخدمة أو الإجراء السني")
    unit_price: Decimal = Field(gt=0, description="سعر الوحدة")
    quantity: int = Field(default=1, ge=1, description="الكمية المطلوبة")
    discount_type: Literal["percentage", "absolute"] | None = Field(default=None, description="نوع الخصم إن وجد")
    discount_value: Decimal | None = Field(default=None, description="قيمة الخصم")
    catalog_item_id: UUID | None = Field(default=None, description="معرف الإجراء من الكتالوج إن وجد")


class CreateInvoiceArgs(BaseModel):
    patient_id: UUID = Field(description="معرف المريض المطلوب إصدار الفاتورة له")
    branch_id: UUID | None = Field(default=None, description="معرف الفرع (إذا تُرِك فارغاً يُعتمد الفرع الرئيسي تلقائياً)")
    items: list[InvoiceItemInput] = Field(min_length=1, description="قائمة البنود والخدمات الطبية داخل الفاتورة")
    payment_term_days: int = Field(default=0, ge=0, description="فترة السداد بالأيام")
    internal_notes: str | None = Field(default=None, max_length=500, description="ملاحظات سريرية داخلية")
    public_notes: str | None = Field(default=None, max_length=500, description="ملاحظات تُطبع على الفاتورة")


def _invoice_summary(invoice) -> dict:
    patient = invoice.patient
    # Invoice axis only: no paid/pending amounts here (off-books rule).
    return {
        "id": invoice.id,
        "number": invoice.invoice_number,
        "patient_id": invoice.patient_id,
        "patient_name": (
            f"{patient.first_name} {patient.last_name}" if patient is not None else None
        ),
        "status": invoice.status,
        "issue_date": invoice.issue_date,
        "due_date": invoice.due_date,
        "total": invoice.total,
    }


async def _list_invoices(ctx: AgentContext, params: ListInvoicesArgs) -> dict:
    items, total = await InvoiceService.list_invoices(
        ctx.db,
        ctx.clinic_id,
        page=1,
        page_size=params.limit,
        patient_id=params.patient_id,
        status=list(params.status) if params.status else None,
        date_from=params.date_from,
        date_to=params.date_to,
        overdue=params.overdue,
        is_credit_note=params.is_credit_note,
    )
    return {"total": total, "invoices": [_invoice_summary(i) for i in items]}


async def _get_invoice(ctx: AgentContext, params: GetInvoiceArgs) -> dict:
    invoice = await InvoiceService.get_invoice(
        ctx.db,
        ctx.clinic_id,
        params.invoice_id,
        include_items=True,
        include_payments=False,  # off-books: never juxtapose the two axes
    )
    if invoice is None:
        return {"error": "not_found"}
    data = _invoice_summary(invoice)
    data["items"] = [
        {"description": i.description, "quantity": i.quantity, "total": i.line_total}
        for i in invoice.items
    ]
    return data


async def _create_invoice(ctx: AgentContext, params: CreateInvoiceArgs) -> dict:
    from app.core.branches.models import ClinicBranch

    branch_id = params.branch_id
    if not branch_id:
        b_res = await ctx.db.execute(
            select(ClinicBranch.id).where(ClinicBranch.clinic_id == ctx.clinic_id, ClinicBranch.is_main.is_(True))
        )
        branch_id = b_res.scalar_one_or_none()

    # 1. Resolve series safely (3-Tier Fallback)
    series = await InvoiceSeriesService.get_default_series(
        ctx.db, ctx.clinic_id, series_type="invoice", branch_id=branch_id
    )
    if not series:
        s_res = await ctx.db.execute(
            select(InvoiceSeries)
            .where(InvoiceSeries.clinic_id == ctx.clinic_id, InvoiceSeries.series_type == "invoice", InvoiceSeries.is_active.is_(True))
            .order_by(InvoiceSeries.is_default.desc(), InvoiceSeries.created_at.asc())
            .limit(1)
        )
        series = s_res.scalar_one_or_none()

    if not series:
        series = await InvoiceSeriesService.create_series(
            ctx.db,
            clinic_id=ctx.clinic_id,
            data={
                "prefix": "FAC",
                "series_type": "invoice",
                "description": "السلسلة الافتراضية للفواتير",
                "is_default": True,
                "branch_id": branch_id,
                "reset_yearly": True,
            },
        )

    # 2. Create base invoice as draft (using flush, NEVER commit!)
    notes = {
        "internal_notes": params.internal_notes,
        "public_notes": params.public_notes,
    }
    invoice = await InvoiceService.create_invoice(
        ctx.db,
        clinic_id=ctx.clinic_id,
        created_by=ctx.supervisor_id,
        patient_id=params.patient_id,
        series_id=series.id if series else None,
        payment_term_days=params.payment_term_days,
        notes=notes,
        branch_id=branch_id,
    )

    # 3. Add items and calculate totals atomically
    for item_data in params.items:
        await InvoiceItemService.create_item(
            ctx.db,
            ctx.clinic_id,
            invoice,
            item_data.model_dump(exclude_none=True),
        )

    # 4. Flush to database within the current transaction (No commit!)
    await ctx.db.flush()

    # 5. Reload invoice with relationships for clean summary and fresh totals
    fresh_invoice = await InvoiceService.get_invoice(
        ctx.db, ctx.clinic_id, invoice.id, include_items=True, include_payments=False
    )
    if fresh_invoice is None:
        await ctx.db.refresh(invoice)
        fresh_invoice = invoice

    return _invoice_summary(fresh_invoice)


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="list_invoices",
            description=(
                "Listar facturas de la clínica: por paciente, estado (draft, "
                "issued, partial, paid, cancelled, voided), fechas, vencidas "
                "o rectificativas. Solo lectura."
            ),
            parameters=ListInvoicesArgs,
            handler=_list_invoices,
            permissions=["billing.read"],
            category=ToolCategory.READ,
        ),
        Tool(
            name="get_invoice",
            description="Detalle de una factura con sus líneas. Solo lectura.",
            parameters=GetInvoiceArgs,
            handler=_get_invoice,
            permissions=["billing.read"],
            category=ToolCategory.READ,
        ),
        Tool(
            name="create_invoice",
            description="إنشاء مسودة فاتورة جديدة للمريض من الصفر مع تحديد بنود العلاج والأسعار والفرع. تتطلب تأكيد الطبيب.",
            parameters=CreateInvoiceArgs,
            handler=_create_invoice,
            permissions=["billing.write"],
            category=ToolCategory.WRITE,
        ),
    ]
