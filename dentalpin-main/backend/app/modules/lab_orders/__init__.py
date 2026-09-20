"""Lab work orders sent to external laboratories for patients."""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import LabOrder
from .router import router


class LabOrdersModule(BaseModule):
    """Lab work order tracking, linked to patients and external contacts."""

    manifest = {
        "name": "lab_orders",
        "version": "0.1.0",
        "summary": "Track lab work orders per patient — from sent to received.",
        "author": "DentApex Team",
        "license": "BSL-1.1",
        "category": "community",
        "depends": ["patients", "contacts"],
        "installable": True,
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
            "navigation": [
                {
                    "label": "nav.labOrdersForm",
                    "icon": "i-lucide-clipboard-plus",
                    "to": "/lab-orders/new",
                    "permission": "lab_orders.write",
                    "order": 92,
                },
                {
                    "label": "nav.labOrdersStatus",
                    "icon": "i-lucide-flask-conical",
                    "to": "/lab-orders",
                    "permission": "lab_orders.read",
                    "order": 92.5,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [LabOrder]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write"]

    def get_tools(self) -> list:
        from . import tools

        return tools.get_tools()
