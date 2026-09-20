"""Catalog event handlers.

``clinic.created`` → seed VAT types (by country preset), categories and the
default treatment catalog so a fresh clinic can budget/bill on day one.
Idempotent: ``seed_catalog`` skips existing VAT rates / category keys /
internal codes. Failures are logged, not raised — the ``catalog-empty``
getting-started rule surfaces them and ``POST /catalog/seed`` repairs them.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.database import async_session_maker

from .seed import seed_clinic_defaults

logger = logging.getLogger(__name__)


async def on_clinic_created(data: dict[str, Any]) -> None:
    """own-session (issue #183): ``clinic.created`` is published after
    ``POST /auth/setup`` commits, so there are no uncommitted rows to miss —
    and seeding a fresh clinic must not stretch the signup transaction.
    """
    clinic_id_raw = data.get("clinic_id")
    if not clinic_id_raw:
        return
    try:
        clinic_id = UUID(str(clinic_id_raw))
    except (ValueError, TypeError):
        return

    async with async_session_maker() as db:
        try:
            summary = await seed_clinic_defaults(db, clinic_id)
            await db.commit()
            logger.info("catalog.on_clinic_created seeded %s for %s", summary, clinic_id)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("catalog.on_clinic_created failed: %s", exc, exc_info=True)
            await db.rollback()
