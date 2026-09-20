"""core & modules — add clinic_branches table, branch_id foreign keys, schedule/inventory/series links, backfill, and strict NOT NULL enforcement.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-15
"""

from collections.abc import Sequence
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = ("ag_0006", "bil_0005", "pay_0004", "sch_0001", "inv_0001")


def upgrade() -> None:
    # 1. إنشاء جدول clinic_branches
    op.create_table(
        "clinic_branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("is_main", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("display_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("clinic_id", "name", name="uq_clinic_branches_clinic_name"),
        sa.UniqueConstraint("clinic_id", "code", name="uq_clinic_branches_clinic_code"),
    )
    op.create_index("ix_clinic_branches_clinic_id", "clinic_branches", ["clinic_id"])

    # 2. إضافة الأعمدة كـ nullable مبدئياً لإتاحة الـ Backfill
    op.add_column("cabinets", sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinic_branches.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_cabinets_branch_id", "cabinets", ["branch_id"])

    op.add_column("appointments", sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinic_branches.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_appointments_branch_id", "appointments", ["branch_id"])

    op.add_column("invoices", sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinic_branches.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_invoices_branch_id", "invoices", ["branch_id"])

    op.add_column("payments", sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinic_branches.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_payments_branch_id", "payments", ["branch_id"])

    op.add_column("budgets", sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinic_branches.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_budgets_branch_id", "budgets", ["branch_id"])

    op.add_column("invoice_series", sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinic_branches.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_invoice_series_branch_id", "invoice_series", ["branch_id"])

    op.add_column("schedule_shifts", sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinic_branches.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_schedule_shifts_branch_id", "schedule_shifts", ["branch_id"])

    op.add_column("clinic_weekly_schedules", sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinic_branches.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_clinic_weekly_schedules_branch_id", "clinic_weekly_schedules", ["branch_id"])

    op.add_column("clinic_overrides", sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinic_branches.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_clinic_overrides_branch_id", "clinic_overrides", ["branch_id"])

    op.add_column("inventory_items", sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinic_branches.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_inventory_items_branch_id", "inventory_items", ["branch_id"])

    op.add_column("clinic_memberships", sa.Column("default_branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinic_branches.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_clinic_memberships_default_branch_id", "clinic_memberships", ["default_branch_id"])

    # 3. الترحيل الآمن للبيانات القائمة (Backfill Logic منفصلة لكل أمر لتوافق asyncpg)
    op.execute(
        """
        INSERT INTO clinic_branches (id, clinic_id, name, code, phone, email, address, is_main, is_active, display_order, settings)
        SELECT 
            gen_random_uuid(),
            c.id,
            'الفرع الرئيسي',
            'MAIN',
            c.phone,
            c.email,
            COALESCE(c.address, '{}'::jsonb),
            true,
            true,
            0,
            '{}'::jsonb
        FROM clinics c
        ON CONFLICT (clinic_id, code) DO NOTHING
        """
    )

    op.execute(
        """
        UPDATE cabinets c
        SET branch_id = b.id
        FROM clinic_branches b
        WHERE b.clinic_id = c.clinic_id AND b.is_main = true AND c.branch_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE appointments a
        SET branch_id = b.id
        FROM clinic_branches b
        WHERE b.clinic_id = a.clinic_id AND b.is_main = true AND a.branch_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE invoices i
        SET branch_id = b.id
        FROM clinic_branches b
        WHERE b.clinic_id = i.clinic_id AND b.is_main = true AND i.branch_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE payments p
        SET branch_id = b.id
        FROM clinic_branches b
        WHERE b.clinic_id = p.clinic_id AND b.is_main = true AND p.branch_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE budgets bg
        SET branch_id = b.id
        FROM clinic_branches b
        WHERE b.clinic_id = bg.clinic_id AND b.is_main = true AND bg.branch_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE invoice_series s
        SET branch_id = b.id
        FROM clinic_branches b
        WHERE b.clinic_id = s.clinic_id AND b.is_main = true AND s.branch_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE schedule_shifts ss
        SET branch_id = b.id
        FROM clinic_branches b, professional_weekly_schedules pws
        WHERE ss.professional_weekly_id = pws.id AND pws.clinic_id = b.clinic_id AND b.is_main = true AND ss.branch_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE inventory_items ii
        SET branch_id = b.id
        FROM clinic_branches b
        WHERE b.clinic_id = ii.clinic_id AND b.is_main = true AND ii.branch_id IS NULL
        """
    )

    op.execute(
        """
        UPDATE clinic_memberships cm
        SET default_branch_id = b.id
        FROM clinic_branches b
        WHERE b.clinic_id = cm.clinic_id AND b.is_main = true AND cm.default_branch_id IS NULL
        """
    )

    # 4. تشديد قيود قاعدة البيانات (Strict NOT NULL Enforcement بعد الـ Backfill مباشرة)
    op.alter_column("cabinets", "branch_id", nullable=False)
    op.alter_column("appointments", "branch_id", nullable=False)
    op.alter_column("invoices", "branch_id", nullable=False)
    op.alter_column("payments", "branch_id", nullable=False)
    op.alter_column("budgets", "branch_id", nullable=False)


def downgrade() -> None:
    # إرجاع الأعمدة إلى Nullable قبل الحذف
    op.alter_column("budgets", "branch_id", nullable=True)
    op.alter_column("payments", "branch_id", nullable=True)
    op.alter_column("invoices", "branch_id", nullable=True)
    op.alter_column("appointments", "branch_id", nullable=True)
    op.alter_column("cabinets", "branch_id", nullable=True)

    op.drop_index("ix_clinic_memberships_default_branch_id", table_name="clinic_memberships")
    op.drop_column("clinic_memberships", "default_branch_id")

    op.drop_index("ix_inventory_items_branch_id", table_name="inventory_items")
    op.drop_column("inventory_items", "branch_id")

    op.drop_index("ix_clinic_overrides_branch_id", table_name="clinic_overrides")
    op.drop_column("clinic_overrides", "branch_id")

    op.drop_index("ix_clinic_weekly_schedules_branch_id", table_name="clinic_weekly_schedules")
    op.drop_column("clinic_weekly_schedules", "branch_id")

    op.drop_index("ix_schedule_shifts_branch_id", table_name="schedule_shifts")
    op.drop_column("schedule_shifts", "branch_id")

    op.drop_index("ix_invoice_series_branch_id", table_name="invoice_series")
    op.drop_column("invoice_series", "branch_id")

    op.drop_index("ix_budgets_branch_id", table_name="budgets")
    op.drop_column("budgets", "branch_id")

    op.drop_index("ix_payments_branch_id", table_name="payments")
    op.drop_column("payments", "branch_id")

    op.drop_index("ix_invoices_branch_id", table_name="invoices")
    op.drop_column("invoices", "branch_id")

    op.drop_index("ix_appointments_branch_id", table_name="appointments")
    op.drop_column("appointments", "branch_id")

    op.drop_index("ix_cabinets_branch_id", table_name="cabinets")
    op.drop_column("cabinets", "branch_id")

    op.drop_index("ix_clinic_branches_clinic_id", table_name="clinic_branches")
    op.drop_table("clinic_branches")
