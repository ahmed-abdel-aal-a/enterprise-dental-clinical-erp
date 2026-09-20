"""Module discovery and loading.

Discovery happens in two stages:

1. **Entry points** — the primary mechanism. Modules (internal or
   third-party) declare an entry point in the ``dentalpin.modules``
   group. This is how published PyPI packages plug in without any
   filesystem layout assumptions.

2. **Filesystem scan** — a dev-mode fallback that walks
   ``backend/app/modules/`` and imports any package containing a
   ``BaseModule`` subclass. Controlled by
   ``settings.DENTALPIN_DEV_MODULE_SCAN``. The fallback skips modules
   that an entry point already provided, so entry points win when both
   are present.

Discovery and mounting are two steps on purpose (issue #91):

* :func:`register_discovered` — discover, topo-sort and register every
  module in the :data:`module_registry`. Nothing is mounted; the
  lifecycle machinery (reconcile, pending processor) needs the full list.
* :func:`mount_modules` — mount a chosen subset: router, event handlers,
  tools, ``on_activate()``, and mark it active. The lifespan passes the
  modules whose ``core_module.state`` is ``installed``; tests and scripts
  that want everything pass the full discovered list explicitly.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from collections.abc import Iterable
from importlib import metadata
from pathlib import Path

from fastapi import FastAPI

from app.config import settings

from .base import BaseModule
from .registry import module_registry
from .topology import topological_sort

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUPS = ["dentapex.modules", "dentalpin.modules"]


def _resolve_load_order(modules: list[BaseModule]) -> list[BaseModule]:
    return topological_sort(
        modules,
        key=lambda m: m.name,
        deps_of=lambda m: m.dependencies,
    )


def _instantiate_module_class(cls: type) -> BaseModule | None:
    """Instantiate a BaseModule subclass, return None on failure."""
    if not (isinstance(cls, type) and issubclass(cls, BaseModule) and cls is not BaseModule):
        return None
    try:
        return cls()
    except Exception as exc:
        logger.error("Failed to instantiate module class %s: %s", cls.__name__, exc)
        return None


def _discover_entry_points() -> list[BaseModule]:
    """Discover modules registered as entry points."""
    modules: list[BaseModule] = []

    for group in ENTRY_POINT_GROUPS:
        try:
            eps = metadata.entry_points(group=group)
        except TypeError:
            eps = metadata.entry_points().get(group, [])  # type: ignore[union-attr]

        for ep in eps:
            try:
                cls = ep.load()
            except Exception as exc:
                logger.error("Failed to load entry point %s: %s", ep.name, exc)
                continue

            instance = _instantiate_module_class(cls)
            if instance is None:
                logger.warning("Entry point %s did not resolve to a BaseModule subclass", ep.name)
                continue

            modules.append(instance)
            logger.info("Discovered module via entry point: %s", instance.name)

    return modules


def _discover_filesystem(seen: set[str]) -> list[BaseModule]:
    """Filesystem scan fallback for dev mode.

    Skips modules already present in ``seen`` (names discovered via
    entry points).
    """
    modules: list[BaseModule] = []
    modules_path = Path(__file__).parent.parent.parent / "modules"

    if not modules_path.exists():
        logger.warning("Modules directory not found: %s", modules_path)
        return modules

    for module_info in pkgutil.iter_modules([str(modules_path)]):
        if not module_info.ispkg:
            continue

        try:
            pkg = importlib.import_module(f"app.modules.{module_info.name}")
        except Exception as exc:
            logger.error("Failed to import module %s: %s", module_info.name, exc)
            continue

        for attr_name in dir(pkg):
            cls = getattr(pkg, attr_name)
            instance = _instantiate_module_class(cls)
            if instance is None:
                continue
            if instance.name in seen:
                # Entry point already provided this module.
                break
            modules.append(instance)
            seen.add(instance.name)
            logger.info("Discovered module via filesystem scan: %s", instance.name)
            break

    return modules


def discover_modules() -> list[BaseModule]:
    """Run both discovery stages and return all unique modules."""
    modules = _discover_entry_points()
    seen = {m.name for m in modules}

    if getattr(settings, "DENTAPEX_DEV_MODULE_SCAN", False) or getattr(settings, "DENTALPIN_DEV_MODULE_SCAN", False):
        modules.extend(_discover_filesystem(seen))
    else:
        logger.info("Module filesystem discovery disabled; skipping")

    return modules


def register_discovered() -> list[BaseModule]:
    """Discover every module and register it; return them in load order.

    Idempotent: modules already in the registry (tests, CLI re-entry)
    are kept as-is. Raises on a dependency cycle — fail loud at boot.
    """
    for module in discover_modules():
        if not module_registry.is_discovered(module.name):
            module_registry.register(module)

    ordered = _resolve_load_order(module_registry.list_discovered())
    if not ordered:
        logger.warning("No modules discovered")
    return ordered


def mount_modules(app: FastAPI, modules: Iterable[BaseModule]) -> list[BaseModule]:
    """Mount ``modules`` (router, event handlers, tools) and mark them active.

    ``modules`` must come in dependency order (``register_discovered``
    output, possibly filtered). A module whose declared dependency is not
    active is skipped with an error — that state is only reachable through
    ``uninstall --force`` and mounting it would fail at first request
    anyway. Already-active modules are skipped silently. Returns what was
    mounted this call.
    """
    from app.core.agents.tools.registry import tool_registry
    from app.core.events import event_bus

    mounted: list[BaseModule] = []
    for module in modules:
        if module_registry.is_active(module.name):
            continue
        missing = [dep for dep in module.dependencies if not module_registry.is_active(dep)]
        if missing:
            logger.error("Not mounting %s: dependencies not active: %s", module.name, missing)
            continue

        app.include_router(
            module.get_router(),
            prefix=f"/api/v1/{module.name}",
            tags=[module.name],
        )
        for event_type, handler in module.get_event_handlers().items():
            event_bus.subscribe(event_type, handler)
        tool_registry.register_from(module)
        module.on_activate()
        module_registry.activate(module.name)
        mounted.append(module)
        logger.info("Mounted module: %s", module.name)

    return mounted
