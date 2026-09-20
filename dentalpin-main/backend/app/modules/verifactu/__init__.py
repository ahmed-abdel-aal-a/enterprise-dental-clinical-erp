"""Verifactu (AEAT) compliance module — Spain.

Implements the RRSIF / Veri*Factu spec (RD 1007/2023, Orden HAC/1177/2024)
mandatory for Spanish clinics from 2027. Extends the billing module via
the ``BillingComplianceHook`` registry; never imports billing internals
directly.

Manual install only (``auto_install=False``). Becomes irreversible once
fiscal records are sent to AEAT (uninstall blocks).
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule
from app.core.scheduling import ScheduledJob

from .models import (
    VerifactuCertificate,
    VerifactuRecord,
    VerifactuSettings,
    VerifactuVatClassification,
)
from .router import router


class VerifactuModule(BaseModule):
    manifest = {
        "name": "verifactu",
        "version": "0.1.0",
        "summary": "Cumplimiento Veri*Factu (AEAT) para clínicas en España.",
        "author": "DentApex Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["billing", "catalog"],
        "installable": True,
        "auto_install": False,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["records.read"],
            "hygienist": [],
            "assistant": [],
            "receptionist": ["records.read"],
        },
        "frontend": {
            "layer_path": "frontend",
        },
    }

    def get_models(self) -> list:
        return [
            VerifactuSettings,
            VerifactuCertificate,
            VerifactuRecord,
            VerifactuVatClassification,
        ]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "settings.read",
            "settings.configure",
            "records.read",
            "queue.manage",
            "environment.promote",
        ]

    def get_event_handlers(self) -> dict:
        from app.core.events import EventType

        from .events import on_invoice_paid
        from .tasks import on_rejected_event

        return {
            "invoice.paid": on_invoice_paid,
            EventType.VERIFACTU_RECORD_REJECTED: on_rejected_event,
        }

    def get_scheduled_jobs(self) -> list[ScheduledJob]:
        from .tasks import scheduled_jobs

        return scheduled_jobs()

    def on_activate(self) -> None:
        # Re-attached on every boot the module is installed (issue #91):
        # the billing workflow looks the hook up by country at request
        # time, so it must live in this process, not in the DB.
        from app.modules.billing.hooks import BillingHookRegistry

        from .hook import VerifactuHook

        BillingHookRegistry.register(VerifactuHook())

    async def install(self, ctx) -> None:
        from sqlalchemy import select

        from app.modules.catalog.models import VatType

        # Seed default AEAT classification for every existing
        # zero-rated VAT type. For dental clinics, rate=0 typically
        # means "exento sanitario art. 20.uno.3.º LIVA" → ``E1``. The
        # admin can later override this from the verifactu config
        # panel. Idempotent: only inserts when no override exists yet.
        zero_rates = await ctx.db.execute(
            select(VatType.id, VatType.clinic_id).where(VatType.rate == 0)
        )
        for vat_type_id, clinic_id in zero_rates.all():
            existing = await ctx.db.execute(
                select(VerifactuVatClassification.id).where(
                    VerifactuVatClassification.clinic_id == clinic_id,
                    VerifactuVatClassification.vat_type_id == vat_type_id,
                )
            )
            if existing.first() is not None:
                continue
            ctx.db.add(
                VerifactuVatClassification(
                    clinic_id=clinic_id,
                    vat_type_id=vat_type_id,
                    classification="E1",
                    exemption_cause="E1",
                    notes="Servicios sanitarios — art. 20.uno.3.º LIVA (semilla por defecto).",
                )
            )

    async def uninstall(self, ctx) -> None:
        from sqlalchemy import select

        from .models import VerifactuRecord

        result = await ctx.db.execute(
            select(VerifactuRecord.id)
            .where(VerifactuRecord.state.in_(("accepted", "accepted_with_errors")))
            .limit(1)
        )
        if result.first() is not None:
            raise RuntimeError(
                "No se puede desinstalar verifactu: existen registros "
                "fiscales aceptados por la AEAT. La ley exige conservar el "
                "libro de facturación 4 años. Exporta el libro antes de "
                "intentar desinstalar."
            )
        # Nothing to detach: the hook, jobs and handlers are only wired by
        # the loader while the module is installed, and the processor runs
        # before mounting on the next boot.
