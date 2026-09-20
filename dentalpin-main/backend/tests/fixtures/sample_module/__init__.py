"""Sample community module used by Etapa 6 tests.

Minimal, self-contained: manifest declaring a Nuxt layer, empty router,
no models. Tests instantiate ``SampleModule`` directly rather than
going through entry-point discovery so it stays out of the real
registry.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule


class SampleModule(BaseModule):
    """Sample community module that ships its own Nuxt layer."""

    manifest = {
        "name": "sample_community",
        "version": "0.1.0",
        "summary": "Community fixture used to exercise the layer pipeline.",
        "author": "DentalPin tests",
        "license": "MIT",
        "category": "community",
        "depends": [],
        "installable": True,
        "auto_install": False,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.sampleCommunity",
                    "icon": "i-lucide-beaker",
                    "to": "/sample",
                    "order": 90,
                }
            ],
        },
    }

    def get_models(self) -> list:
        return []

    def get_router(self) -> APIRouter:
        router = APIRouter()

        @router.get("/ping")
        async def ping() -> dict:
            return {"ok": True, "module": "sample_community"}

        return router

    def get_permissions(self) -> list[str]:
        return ["read"]

    def get_tools(self) -> list:
        return []

    # --- observability for the activation tests (issue #91) ---------------

    SAMPLE_EVENT = "sample_community.ping"

    def __init__(self) -> None:
        self.activated = False
        self.seen_events: list[dict] = []

    def get_event_handlers(self) -> dict:
        return {self.SAMPLE_EVENT: self._on_ping}

    def _on_ping(self, payload: dict) -> None:
        self.seen_events.append(payload)

    def on_activate(self) -> None:
        self.activated = True
