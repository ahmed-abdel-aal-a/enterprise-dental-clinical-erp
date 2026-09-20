"""EventBus transactional handlers (ADR 0019).

A handler declaring a ``db`` parameter runs inside the publisher's
session and its exceptions propagate; handlers without ``db`` keep the
fire-and-log contract.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.core.events.bus import EventBus


@pytest.mark.asyncio
async def test_db_is_passed_only_to_handlers_that_declare_it() -> None:
    bus = EventBus()
    seen: list = []
    session = object()

    async def plain(data):
        seen.append(("plain", data["x"]))

    async def transactional(data, *, db):
        seen.append(("tx", data["x"], db))

    bus.subscribe("t.evt", plain)
    bus.subscribe("t.evt", transactional)
    await bus.publish("t.evt", {"x": 1}, db=session)

    assert seen == [("plain", 1), ("tx", 1, session)]


@pytest.mark.asyncio
async def test_transactional_handler_errors_propagate_plain_are_swallowed() -> None:
    bus = EventBus()

    async def plain(data):
        raise ValueError("swallowed")

    async def transactional(data, *, db):
        raise ValueError("propagates")

    bus.subscribe("t.evt", plain)
    await bus.publish("t.evt", {}, db=object())  # no raise

    bus.subscribe("t.evt", transactional)
    with pytest.raises(ValueError, match="propagates"):
        await bus.publish("t.evt", {}, db=object())


@pytest.mark.asyncio
async def test_transactional_handler_requires_db_at_publish() -> None:
    bus = EventBus()

    async def transactional(data, *, db):
        pass

    bus.subscribe("t.evt", transactional)
    with pytest.raises(RuntimeError, match="transactional publish"):
        await bus.publish("t.evt", {})


# ---------------------------------------------------------------------------
# Static contract check (issue #183)
# ---------------------------------------------------------------------------
#
# A transactional handler raises ``RuntimeError`` when its event is published
# without ``db=``. That is a loud failure, but only on the code path that
# publishes it. This walks every registered handler and every publish site in
# ``app/`` so a publisher that forgets ``db=db`` fails in CI instead of in a
# clinic.


def _transactional_events() -> set[str]:
    """Event names that have at least one transactional subscriber."""
    from app.core.events.bus import _wants_db
    from app.core.plugins import module_registry

    return {
        event
        for module in module_registry.list_discovered()
        for event, handler in module.get_event_handlers().items()
        if _wants_db(handler)
    }


def _event_constants(app_root: Path) -> dict[tuple[str, str], str]:
    """``(ClassName, ATTR) -> "event.name"`` for every event-constant class.

    Covers ``EventType`` and module-local ones such as
    ``OdontogramEventType`` without importing anything.
    """
    constants: dict[tuple[str, str], str] = {}
    for path in app_root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            if not (isinstance(node, ast.ClassDef) and node.name.endswith("EventType")):
                continue
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                ):
                    constants[(node.name, stmt.targets[0].id)] = stmt.value.value
    return constants


def _resolve(node: ast.expr, constants: dict[tuple[str, str], str]) -> str | None:
    """Resolve an expression to an event name, or ``None`` if not static."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return constants.get((node.value.id, node.attr))
    return None


def _publish_sites() -> list[tuple[str, int, frozenset[str], bool]]:
    """Every ``event_bus.publish(...)`` in ``app/``.

    Returns (file, line, candidate event names, passes ``db=``). A publish
    whose first argument is not a static constant (a dispatch table, a
    forwarded parameter) can't be pinned down, so its candidate set becomes
    *every* event referenced in that file — over-approximating towards
    "needs db=" rather than silently letting a dynamic site through.
    """
    app_root = Path(__file__).resolve().parent.parent / "app"
    constants = _event_constants(app_root)
    sites = []
    for path in sorted(app_root.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        in_file = frozenset(
            name
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and (name := _resolve(node, constants))
        )
        for node in ast.walk(tree):
            func = getattr(node, "func", None)
            if not (
                isinstance(node, ast.Call)
                and isinstance(func, ast.Attribute)
                and func.attr == "publish"
                and getattr(func.value, "id", None) == "event_bus"
                and node.args
            ):
                continue
            resolved = _resolve(node.args[0], constants)
            candidates = frozenset({resolved}) if resolved else in_file
            has_db = any(kw.arg == "db" for kw in node.keywords)
            sites.append((str(path.relative_to(app_root.parent)), node.lineno, candidates, has_db))
    return sites


def test_every_publisher_of_a_transactional_event_passes_db() -> None:
    """ADR 0019: a transactional handler needs its publisher to offer a session.

    The bus raises at publish time, but only on the path that publishes. This
    catches the same mistake in CI, on every path.
    """
    transactional = _transactional_events()
    offenders = [
        f"{file}:{line} publishes {', '.join(sorted(candidates & transactional))} without db="
        for file, line, candidates, has_db in _publish_sites()
        if not has_db and candidates & transactional
    ]
    assert not offenders, "Publishers missing db= for a transactional handler:\n" + "\n".join(
        offenders
    )
