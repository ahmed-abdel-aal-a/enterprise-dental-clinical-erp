"""inventory — standalone stock list with low-stock alerts (roadmap #220).

Base version only: flat stock list, per-item minimum quantities, atomic
stock adjustments guarded at the DB level, and an ``inventory.low_stock``
event fired on the not-low → low crossing. Cost tracking, stock
movements and auto-deduction come later with the inventory core upgrade
(#226); treatment_consumables (#225) links catalog treatments to these
items.

``depends: []`` — fully standalone. The only FKs point at core tables
(clinics, users).
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import InventoryItem
from .router import router


class InventoryModule(BaseModule):
    """Stock list with low-stock alerts."""

    manifest = {
        "name": "inventory",
        "version": "0.1.0",
        "summary": "Standalone stock list with per-item minimums and low-stock alerts.",
        "author": "lamanji",
        "license": "BSL-1.1",
        "category": "community",
        "depends": [],
        "installable": True,
        # Optional module: ships inactive, the admin activates it from the
        # module admin UI (repo policy for new non-core modules).
        "auto_install": False,
        "removable": True,
        # Stock levels are operational data, not sensitive — the whole team
        # participates (same breadth precedent as patient_relationships).
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["read", "write"],
            "hygienist": ["read", "write"],
            "assistant": ["read", "write"],
            "receptionist": ["read", "write"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.inventory",
                    "icon": "i-lucide-package",
                    "to": "/inventory",
                    "permission": "inventory.read",
                    "order": 93,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [InventoryItem]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write"]

    def get_tools(self) -> list:
        from . import tools

        return tools.get_tools()
