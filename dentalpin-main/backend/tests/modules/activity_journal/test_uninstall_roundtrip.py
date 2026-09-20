"""activity_journal round-trip uninstall test.

Mirrors expenses/patient_relationships: install -> uninstall -> reinstall
must drop ONLY the activity_journal table and leave every other module
untouched. The module owns a single revision (ajr_0001), so the
branch-scoped downgrade target is ``activity_journal@-1``. Marked
``alembic_roundtrip`` and excluded from the default pytest run.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import asyncpg
import pytest

from app.config import settings

pytestmark = pytest.mark.alembic_roundtrip

BACKEND_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"

JOURNAL_TABLES = {"activity_journal_entries"}


def _alembic(*args: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), *args],
        cwd=BACKEND_ROOT,
        check=True,
    )


def _dsn() -> str:
    return settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


async def _list_tables_async() -> set[str]:
    conn = await asyncpg.connect(_dsn())
    try:
        rows = await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name != 'alembic_version'"
        )
        return {row["table_name"] for row in rows}
    finally:
        await conn.close()


def _list_tables() -> set[str]:
    return asyncio.run(_list_tables_async())


def test_activity_journal_uninstall_roundtrip_is_branch_scoped() -> None:
    _alembic("upgrade", "heads")
    before = _list_tables()
    assert JOURNAL_TABLES.issubset(before), (
        f"expected journal table at heads; missing: {JOURNAL_TABLES - before}"
    )
    baseline_other = before - JOURNAL_TABLES

    _alembic("downgrade", "activity_journal@-1")
    after_down = _list_tables()
    assert JOURNAL_TABLES.isdisjoint(after_down), (
        f"journal table survived downgrade: {JOURNAL_TABLES & after_down}"
    )
    assert baseline_other <= after_down, (
        f"downgrade leaked into other modules; missing: {baseline_other - after_down}"
    )

    _alembic("upgrade", "activity_journal@head")
    after_up = _list_tables()
    assert before <= after_up, (
        f"reinstall did not restore every table; missing: {before - after_up}"
    )
