"""patient_relationships — patient-to-patient relationships (Lien de Parentée).

Originally also held insurance exemption status (APCI/ALD); removed in
Phase 8.1 — APCI is now a computed flag off systemic-disease reference
data (see models.py docstring), not a manually-entered field, so it
doesn't belong in this module. Depends on ``patients`` only (cross-module
read of ``Patient.full_name``, allowed under ADR 0002).
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import PatientRelationship
from .router import router


class PatientRelationshipsModule(BaseModule):
    """Patient relationships, surfaced on the patient page."""

    manifest = {
        "name": "patient_relationships",
        "version": "0.2.0",
        "summary": "Patient family relationships (Lien de Parentée).",
        "author": "DentApex Team",
        "license": "BSL-1.1",
        "category": "community",
        "depends": ["patients"],
        "installable": True,
        # Optional module: ships inactive, the admin activates it from the
        # module admin UI (repo policy for new non-core modules).
        "auto_install": False,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["read", "write"],
            "hygienist": ["read"],
            "assistant": ["read", "write"],
            "receptionist": ["read", "write"],
        },
        "frontend": {
            "layer_path": "frontend",
            # No standalone nav entry — surfaces inline on the patient page
            # via the `patient.summary.cards` slot (slots.client.ts), same
            # extension point patients_clinical already uses.
        },
    }

    def get_models(self) -> list:
        return [PatientRelationship]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        # Registry namespaces with the module name -> final perms are
        # ``patient_relationships.read`` / ``patient_relationships.write``
        # (same convention as patients/recalls).
        return ["read", "write"]
