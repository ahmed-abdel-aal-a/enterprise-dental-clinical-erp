"""Only installed modules are live at runtime (issue #91).

``register_discovered`` fills the registry; ``mount_modules`` wires a
chosen subset and marks it active. The lifespan passes the modules whose
``core_module.state`` is ``installed``, so an ``uninstalled`` module has no
routes, no event handlers, no tools, no scheduler jobs and grants no
permissions — whatever is on disk.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest
from fastapi import APIRouter, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.auth.permissions import get_role_permissions
from app.core.events import event_bus
from app.core.plugins import BaseModule
from app.core.plugins.db_models import ModuleRecord
from app.core.plugins.loader import mount_modules
from app.core.plugins.processor import PendingProcessor
from app.core.plugins.registry import module_registry
from app.core.plugins.service import ModuleService
from app.core.plugins.state import ModuleState
from tests.fixtures.sample_module import SampleModule

PING = "/api/v1/sample_community/ping"


class _DependentModule(BaseModule):
    manifest = {
        "name": "needs_ghost",
        "version": "0.1.0",
        "depends": ["ghost_module"],
        "auto_install": False,
        "removable": True,
        "role_permissions": {"receptionist": ["read"]},
    }

    def get_models(self) -> list:
        return []

    def get_router(self) -> APIRouter:
        return APIRouter()

    def get_permissions(self) -> list[str]:
        return ["read"]

    def get_tools(self) -> list:
        return []


@pytest.fixture
def sample() -> Iterator[SampleModule]:
    module = SampleModule()
    module_registry.register(module)
    try:
        yield module
    finally:
        event_bus.unsubscribe(SampleModule.SAMPLE_EVENT, module._on_ping)  # noqa: SLF001
        module_registry.unregister("sample_community")


async def _status(app: FastAPI, path: str) -> int:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        return (await client.get(path)).status_code


@pytest.mark.asyncio
async def test_mount_modules_wires_only_the_given_modules(sample: SampleModule) -> None:
    app = FastAPI()

    assert mount_modules(app, []) == []
    assert not module_registry.is_active("sample_community")
    assert await _status(app, PING) == 404
    assert not sample.activated

    assert mount_modules(app, [sample]) == [sample]
    assert module_registry.is_active("sample_community")
    assert await _status(app, PING) == 200
    assert sample.activated
    await event_bus.publish(SampleModule.SAMPLE_EVENT, {"n": 1})
    assert sample.seen_events == [{"n": 1}]

    # Idempotent: a second pass neither re-mounts nor re-subscribes.
    routes_before = len(app.routes)
    assert mount_modules(app, [sample]) == []
    assert len(app.routes) == routes_before
    await event_bus.publish(SampleModule.SAMPLE_EVENT, {"n": 2})
    assert sample.seen_events == [{"n": 1}, {"n": 2}]


def test_mount_skips_module_whose_dependency_is_not_active(caplog) -> None:
    module = _DependentModule()
    module_registry.register(module)
    try:
        with caplog.at_level(logging.ERROR):
            assert mount_modules(FastAPI(), [module]) == []
        assert not module_registry.is_active("needs_ghost")
        assert "ghost_module" in caplog.text
    finally:
        module_registry.unregister("needs_ghost")


def test_role_permissions_follow_activation() -> None:
    """Manifest grants apply once the module is active — not while it is
    merely on disk, and not after it is gone."""
    module = _DependentModule()
    module_registry.register(module)
    try:
        assert "needs_ghost.read" not in get_role_permissions("receptionist")
        assert "needs_ghost.read" not in module_registry.get_all_permissions()

        module_registry.activate("needs_ghost")
        assert "needs_ghost.read" in get_role_permissions("receptionist")
        assert "needs_ghost.read" in module_registry.get_all_permissions()
    finally:
        module_registry.unregister("needs_ghost")
    assert "needs_ghost.read" not in get_role_permissions("receptionist")


@pytest.mark.asyncio
async def test_boot_mounts_only_installed_modules(
    db_session: AsyncSession, sample: SampleModule, tmp_path, monkeypatch
) -> None:
    """The lifespan recipe: reconcile → process pending → mount ``installed``."""
    from app.core.plugins import frontend_layers

    monkeypatch.setattr(frontend_layers, "DEFAULT_FRONTEND_ROOT", tmp_path)
    svc = ModuleService(db_session)
    await svc.reconcile_with_db()

    # auto_install=False ⇒ reconciled as uninstalled ⇒ not mounted.
    assert "sample_community" not in await ModuleService.installed_names(db_session)
    app = FastAPI()
    mount_modules(app, [m for m in [sample] if m.name in await svc.installed_names(db_session)])
    assert await _status(app, PING) == 404
    assert not module_registry.is_active("sample_community")

    # Admin installs + "restart": the processor finalises state=installed.
    await svc.install("sample_community")
    await PendingProcessor(async_sessionmaker(db_session.bind, expire_on_commit=False)).run()
    installed = await ModuleService.installed_names(db_session)
    assert "sample_community" in installed
    app = FastAPI()
    mount_modules(app, [m for m in [sample] if m.name in installed])
    assert await _status(app, PING) == 200
    assert module_registry.is_active("sample_community")

    # Uninstall finalised (what _remove writes) + "restart": gone again.
    record = (
        await db_session.execute(
            select(ModuleRecord).where(ModuleRecord.name == "sample_community")
        )
    ).scalar_one()
    record.state = ModuleState.UNINSTALLED.value
    await db_session.commit()
    assert "sample_community" not in await ModuleService.installed_names(db_session)
