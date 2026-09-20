"""Event handlers consumed by the periodontogram module.

PR-1 ships logging-only handlers. Real refresh logic lands in PR-3 once
``OdontogramService`` pre-fill is wired and the draft auto-syncs with
performed treatments.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def on_odontogram_treatment_performed(data: dict[str, Any]) -> None:
    """React to an odontogram treatment performed.

    Today: no-op (logging). PR-3 will refresh the active draft's
    ``is_implant`` / ``is_present`` flags when a treatment that changes
    the physical state of the tooth is recorded.

    own-session: payload-only, no DB access (issue #183). When PR-3 gives it
    real work, re-read §6 of creating-modules.md — refreshing flags off the
    publisher's rows would make it transactional.
    """
    logger.debug(
        "periodontogram: odontogram.treatment.performed received: %s",
        data.get("treatment_id"),
    )


async def on_patient_archived(data: dict[str, Any]) -> None:
    """Discard any active draft when its patient is archived.

    PR-3 will move this from a logging stub to a real cleanup. For now
    the partial unique index already protects against draft re-use
    against an archived patient.

    own-session: payload-only, no DB access (issue #183). The real cleanup
    is a cascade of the archive, so PR-3 should make it transactional.
    """
    logger.debug(
        "periodontogram: patient.archived received: %s",
        data.get("patient_id"),
    )
