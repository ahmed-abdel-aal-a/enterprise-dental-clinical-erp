"""Contacts module — directory of external labs, suppliers, and other providers.

Standalone module: no dependency on any other module. Foundation for
the lab-work-order module (lab_orders): an order links to a contact
created here.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import Contact
from .router import router


class ContactsModule(BaseModule):
    """Directory of external labs, suppliers, and other providers."""

    manifest = {
        "name": "contacts",
        "version": "0.1.0",
        "summary": "Directory of external labs, suppliers, and other provider contacts.",
        "author": "lamanji",
        "license": "BSL-1.1",
        "category": "community",
        "depends": [],
        "installable": True,
        "auto_install": False,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["read"],
            "hygienist": ["read"],
            "assistant": ["read", "write"],
            "receptionist": ["read", "write"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.contacts",
                    "icon": "i-lucide-building-2",
                    "to": "/contacts",
                    "permission": "contacts.read",
                    "order": 91,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [Contact]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write"]

    def get_tools(self) -> list:
        from . import tools

        return tools.get_tools()
