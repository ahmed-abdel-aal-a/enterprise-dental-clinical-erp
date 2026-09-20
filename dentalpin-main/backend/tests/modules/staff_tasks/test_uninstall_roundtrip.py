"""Branch-scoped uninstall/reinstall coverage for staff_tasks."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import asyncpg
import pytest

from app.config import settings

pytestmark = pytest.mark.alembic_roundtrip
BACKEND_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
STAFF_TASK_TABLES = {"staff_tasks"}


def _alembic(*args: str) -> None:
    subprocess.run(["alembic", "-c", str(ALEMBIC_INI), *args], cwd=BACKEND_ROOT, check=True)


def _dsn() -> str:
    return settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


async def _tables() -> set[str]:
    conn = await asyncpg.connect(_dsn())
    try:
        rows = await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name != 'alembic_version'"
        )
        return {row["table_name"] for row in rows}
    finally:
        await conn.close()


def test_staff_tasks_uninstall_roundtrip_is_branch_scoped() -> None:
    """install → uninstall → reinstall drops only staff_tasks' tables."""
    _alembic("upgrade", "heads")
    before = asyncio.run(_tables())
    assert STAFF_TASK_TABLES.issubset(before)
    baseline = before - STAFF_TASK_TABLES

    # Walk the branch down one revision at a time until the module's table
    # is gone. ``staff_tasks@-1`` always resolves against the branch's
    # *current* head, so this uninstalls completely regardless of how many
    # ``stk_*`` revisions ship later.
    # (Do NOT use ``staff_tasks@base``: in this repo's merged multi-head
    # graph it resolves to the whole-graph base and tears down unrelated
    # chains.)
    after_down = before
    for _ in range(10):
        _alembic("downgrade", "staff_tasks@-1")
        after_down = asyncio.run(_tables())
        if STAFF_TASK_TABLES.isdisjoint(after_down):
            break
    else:
        raise AssertionError(
            f"staff_tasks tables survived full downgrade: {STAFF_TASK_TABLES & asyncio.run(_tables())}"
        )
    assert baseline <= after_down

    _alembic("upgrade", "staff_tasks@head")
    after_up = asyncio.run(_tables())
    assert before <= after_up
