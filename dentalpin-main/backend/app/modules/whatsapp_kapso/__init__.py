"""whatsapp_kapso — WhatsApp delivery for notifications via Kapso.

Community, removable. Registers a ``KapsoAdapter`` into the notifications
channel registry from ``on_activate`` — i.e. on every boot the module is
installed, and never while it is not (issue #91). That is the only
cross-module dependency, declared in ``manifest.depends``;
``notifications`` does not depend on this module.

Issue #63. See ADR 0016 (channel adapters) + ADR 0017 (inbound/conversation).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from app.core.plugins import BaseModule
from app.modules.notifications.channels import channel_registry

from .adapter import KapsoAdapter
from .models import WhatsappKapsoSettings, WhatsappKapsoTemplate
from .router import router

if TYPE_CHECKING:
    from app.core.plugins.base import ModuleContext

# Table names exercised by the round-trip uninstall test.
KAPSO_TABLES = {"whatsapp_kapso_settings", "whatsapp_kapso_templates"}


class WhatsappKapsoModule(BaseModule):
    manifest = {
        "name": "whatsapp_kapso",
        "version": "0.1.0",
        "summary": "WhatsApp para notifications vía Kapso (Meta Cloud API).",
        "author": "DentApex Team",
        "license": "BSL-1.1",
        "category": "community",
        "depends": ["notifications", "patients"],
        "installable": True,
        "auto_install": False,
        "removable": True,
        "role_permissions": {"admin": ["*"]},
        "frontend": {"layer_path": "frontend", "navigation": []},
    }

    def get_models(self) -> list:
        return [WhatsappKapsoSettings, WhatsappKapsoTemplate]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        # Namespaced → whatsapp_kapso.settings.read / .write
        return ["settings.read", "settings.write"]

    def on_activate(self) -> None:
        # Idempotent in the registry. Not registered ⇒ the gateway falls
        # back to the next configured channel (email).
        channel_registry.register(KapsoAdapter())

    async def uninstall(self, ctx: ModuleContext) -> None:
        channel_registry.unregister("whatsapp_kapso")
