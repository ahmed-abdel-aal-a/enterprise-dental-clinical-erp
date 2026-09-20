"""Expenses module — fixed/recurring office cost tracking.

Standalone module: no dependency on any other module. Sensitive by
nature (rent, salaries), so ``role_permissions`` defaults to admin-only;
clinics can widen it from the module admin UI.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import Expense
from .router import router


class ExpensesModule(BaseModule):
    """Fixed office expense tracking (rent, utilities, salaries, ...)."""

    manifest = {
        "name": "expenses",
        "version": "0.1.0",
        "summary": "Fixed/recurring office expense tracking with monthly category totals.",
        "author": "DentApex Team",
        "license": "BSL-1.1",
        "category": "community",
        "depends": [],
        "installable": True,
        # Optional module: ships inactive, the admin activates it from the
        # module admin UI (repo policy for new non-core modules).
        "auto_install": False,
        "removable": True,
        # Rent and salaries are sensitive — default to admin-only and let
        # each clinic widen it deliberately.
        "role_permissions": {
            "admin": ["*"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.expenses",
                    "icon": "i-lucide-wallet",
                    "to": "/expenses",
                    "permission": "expenses.read",
                    "order": 90,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [Expense]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write"]

    def get_tools(self) -> list:
        from . import tools

        return tools.get_tools()
