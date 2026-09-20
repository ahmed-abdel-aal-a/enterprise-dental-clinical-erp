"""Service layer for Clinic Branch management with soft-delete protection and automatic series provisioning."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import ClinicMembership
from app.core.branches.models import ClinicBranch
from app.core.branches.schemas import BranchCreate, BranchUpdate
from app.modules.billing.models import InvoiceSeries


class BranchService:
    @staticmethod
    async def list_branches(
        db: AsyncSession, clinic_id: UUID, active_only: bool = False
    ) -> list[ClinicBranch]:
        query = select(ClinicBranch).where(ClinicBranch.clinic_id == clinic_id)
        if active_only:
            query = query.where(ClinicBranch.is_active.is_(True))
        query = query.order_by(ClinicBranch.display_order, ClinicBranch.name)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_branch(db: AsyncSession, clinic_id: UUID, branch_id: UUID) -> ClinicBranch | None:
        query = select(ClinicBranch).where(
            ClinicBranch.clinic_id == clinic_id, ClinicBranch.id == branch_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_main_branch(db: AsyncSession, clinic_id: UUID) -> ClinicBranch | None:
        query = select(ClinicBranch).where(
            ClinicBranch.clinic_id == clinic_id, ClinicBranch.is_main.is_(True)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_branch(
        db: AsyncSession, clinic_id: UUID, data: BranchCreate
    ) -> ClinicBranch:
        code_upper = data.code.strip().upper()

        if data.is_main:
            # إلغاء تعيين أي فرع رئيسي سابق
            await db.execute(
                update(ClinicBranch)
                .where(ClinicBranch.clinic_id == clinic_id, ClinicBranch.is_main.is_(True))
                .values(is_main=False)
            )

        branch = ClinicBranch(
            clinic_id=clinic_id,
            name=data.name.strip(),
            code=code_upper,
            phone=data.phone,
            email=data.email,
            address=data.address.model_dump(),
            is_main=data.is_main,
            is_active=data.is_active,
            display_order=data.display_order,
            settings=data.settings,
        )
        db.add(branch)
        await db.flush()

        # توليد سلسلة فواتير ضريبية مستقلة للفرع تلقائياً
        branch_prefix = f"FAC-{code_upper}"
        existing_series = await db.execute(
            select(InvoiceSeries).where(
                InvoiceSeries.clinic_id == clinic_id, InvoiceSeries.prefix == branch_prefix
            )
        )
        if not existing_series.scalar_one_or_none():
            auto_series = InvoiceSeries(
                clinic_id=clinic_id,
                branch_id=branch.id,
                prefix=branch_prefix,
                series_type="invoice",
                description=f"سلسلة فواتير {branch.name}",
                is_default=True,
                is_active=True,
            )
            db.add(auto_series)

        await db.commit()
        await db.refresh(branch)
        return branch

    @staticmethod
    async def update_branch(
        db: AsyncSession, clinic_id: UUID, branch_id: UUID, data: BranchUpdate
    ) -> ClinicBranch | None:
        branch = await BranchService.get_branch(db, clinic_id, branch_id)
        if not branch:
            return None

        update_dict = data.model_dump(exclude_unset=True)

        # منع إلغاء تعيين الفرع الرئيسي دون وجود بديل
        if "is_main" in update_dict and not update_dict["is_main"] and branch.is_main:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="لا يمكن إلغاء صفة الفرع الرئيسي دون تعيين فرع آخر كفرع رئيسي",
            )

        if update_dict.get("is_main"):
            await db.execute(
                update(ClinicBranch)
                .where(ClinicBranch.clinic_id == clinic_id, ClinicBranch.is_main.is_(True))
                .values(is_main=False)
            )

        # إذا تم تعطيل الفرع، إعادة توجيه المستخدمين للفرع الرئيسي
        if "is_active" in update_dict and not update_dict["is_active"]:
            if branch.is_main:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="لا يمكن تعطيل الفرع الرئيسي للمنشأة الطبية",
                )
            main_branch = await BranchService.get_main_branch(db, clinic_id)
            fallback_id = main_branch.id if main_branch else None
            await db.execute(
                update(ClinicMembership)
                .where(
                    ClinicMembership.clinic_id == clinic_id,
                    ClinicMembership.default_branch_id == branch_id,
                )
                .values(default_branch_id=fallback_id)
            )

        if "address" in update_dict and update_dict["address"] is not None:
            update_dict["address"] = (
                data.address.model_dump() if data.address else branch.address
            )

        if "code" in update_dict and update_dict["code"]:
            update_dict["code"] = update_dict["code"].strip().upper()

        for field, value in update_dict.items():
            setattr(branch, field, value)

        await db.commit()
        await db.refresh(branch)
        return branch

    @staticmethod
    async def delete_branch(db: AsyncSession, clinic_id: UUID, branch_id: UUID) -> bool:
        branch = await BranchService.get_branch(db, clinic_id, branch_id)
        if not branch:
            return False

        if branch.is_main:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="لا يمكن تعطيل أو أرشفة الفرع الرئيسي للمنشأة الطبية",
            )

        # تحصين المنطق: إعادة تعيين المستخدمين التابعين لهذا الفرع إلى الفرع الرئيسي فوراً
        main_branch = await BranchService.get_main_branch(db, clinic_id)
        fallback_id = main_branch.id if main_branch else None
        await db.execute(
            update(ClinicMembership)
            .where(
                ClinicMembership.clinic_id == clinic_id,
                ClinicMembership.default_branch_id == branch_id,
            )
            .values(default_branch_id=fallback_id)
        )

        branch.is_active = False
        await db.commit()
        return True
