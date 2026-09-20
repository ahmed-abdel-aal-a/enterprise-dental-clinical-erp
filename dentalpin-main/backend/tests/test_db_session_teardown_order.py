"""Regression for #188: full-suite local deadlock.

``db_session``'s per-test ``drop_all`` must run *after* the global
``app.database.engine`` is disposed, not before. If it runs first, a
lingering own-session connection (patient_timeline & co., which use
``app.database.async_session_maker`` directly) can still hold locks that
block the ``DROP TABLE`` — the deadlock reported in #188.

This doesn't reproduce the deadlock itself (timing/protocol-dependent
across event loops, and per #188 doesn't reliably reproduce even in CI).
Instead it asserts the concrete, controllable invariant the fix provides:
``engine.dispose()`` is called before ``Base.metadata.drop_all`` during
``db_session`` teardown.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.database as database_module

_ORDER: list[str] = []


@pytest.fixture(autouse=True)
def _spy_dispose_and_drop_all(monkeypatch):
    """Record call order of engine.dispose() and Base.metadata.drop_all()."""
    engine_cls = type(database_module.engine)
    real_dispose = engine_cls.dispose

    async def spy_dispose(self, *args, **kwargs):
        _ORDER.append("dispose")
        return await real_dispose(self, *args, **kwargs)

    monkeypatch.setattr(engine_cls, "dispose", spy_dispose)

    real_drop_all = database_module.Base.metadata.drop_all

    def spy_drop_all(bind, **kwargs):
        _ORDER.append("drop_all")
        return real_drop_all(bind, **kwargs)

    monkeypatch.setattr(database_module.Base.metadata, "drop_all", spy_drop_all)


@pytest.mark.asyncio
async def test_a_uses_db_session(db_session: AsyncSession) -> None:
    """Just needs to go through one full db_session setup/teardown cycle."""
    assert db_session is not None


@pytest.mark.asyncio
async def test_b_dispose_happened_before_drop_all() -> None:
    """Runs after test_a's teardown has fully completed (serial, no xdist).

    Pre-fix: only the autouse ``_dispose_app_engine`` fixture disposes the
    engine, and it's torn down *last* (LIFO) — so drop_all is recorded
    before dispose and this fails. Post-fix: db_session disposes
    explicitly first.
    """
    assert "dispose" in _ORDER, "engine.dispose() was never called"
    assert "drop_all" in _ORDER, "Base.metadata.drop_all() was never called"
    assert _ORDER.index("dispose") < _ORDER.index("drop_all"), (
        f"dispose must happen before drop_all, got order: {_ORDER}"
    )
