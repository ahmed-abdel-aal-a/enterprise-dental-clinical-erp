"""Branch-scoped uninstall/reinstall coverage for lab_orders."""

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
LAB_ORDER_TABLES = {"lab_orders"}


def _alembic(*args: str) -> None:
    subprocess.run(["alembic", "-c", str(ALEMBIC_INI), *args], cwd=BACKEND_ROOT, check=True)


def _dsn() -> str:
    return settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


async def _tables() -> set[str]:
    conn = await asyncpg.connect(_dsn())
    try:
        rows = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name != 'alembic_version'"
        )
        return {row["table_name"] for row in rows}
    finally:
        await conn.close()


def test_lab_orders_uninstall_roundtrip_is_branch_scoped() -> None:
    _alembic("upgrade", "heads")
    before = asyncio.run(_tables())
    assert LAB_ORDER_TABLES.issubset(before)
    baseline = before - LAB_ORDER_TABLES

    # Walk the branch down one revision at a time until the module's tables
    # are gone. ``lab_orders@-1`` always resolves against the branch's
    # *current* head, so this uninstalls completely regardless of how many
    # ``labo_*`` revisions ship later.
    # (Do NOT use ``lab_orders@base``: in this repo's merged multi-head
    # graph it resolves to the whole-graph base and tears down unrelated
    # chains.)
    after_down = before
    for _ in range(10):
        _alembic("downgrade", "lab_orders@-1")
        after_down = asyncio.run(_tables())
        if LAB_ORDER_TABLES.isdisjoint(after_down):
            break
    else:
        raise AssertionError(
            f"lab_orders tables survived full downgrade: {LAB_ORDER_TABLES & asyncio.run(_tables())}"
        )
    assert baseline <= after_down

    _alembic("upgrade", "lab_orders@head")
    after_up = asyncio.run(_tables())
    assert before <= after_up
