"""staff_tasks — the clinic's staff handoff board.

Internal tasks and handoff notes between staff members (front desk,
clinical, management): "call patient X back", "prepare implant kit for
room 2". Standalone — ``depends: []``. The only FKs outside its own
table point at core rows (clinics, users).

Status lifecycle: open → claimed → done, with cancelled as an escape
hatch (see service._VALID_TRANSITIONS). Claiming an unassigned task
assigns the claimer.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import StaffTask
from .router import router


class StaffTasksModule(BaseModule):
    """Staff handoff board — internal task tracking between team members."""

    manifest = {
        "name": "staff_tasks",
        "version": "0.1.0",
        "summary": "Staff handoff board — internal tasks and handoffs between team members.",
        "author": "DentApex Team",
        "license": "BSL-1.1",
        "category": "community",
        "depends": [],
        "installable": True,
        # Optional module: ships inactive, the admin activates it from the
        # module admin UI (repo policy for new non-core modules).
        "auto_install": False,
        "removable": True,
        # A handoff board only works if the whole team can read AND write
        # it — it is collaboration infrastructure, not sensitive data
        # (same breadth precedent as patient_relationships).
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
                    "label": "nav.staffTasks",
                    "icon": "i-lucide-clipboard-list",
                    "to": "/tasks",
                    "permission": "staff_tasks.read",
                    "order": 91,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [StaffTask]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write"]

    def get_tools(self) -> list:
        from . import tools

        return tools.get_tools()
