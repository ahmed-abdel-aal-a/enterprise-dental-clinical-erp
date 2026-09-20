"""``dentapex db ...`` subcommands.

``db upgrade`` is what the container entrypoint runs before uvicorn
instead of ``alembic upgrade heads`` (ADR 0020): it applies the core
heads plus the branch head of every module that is ``installed`` — or,
when ``core_module`` has no row for it yet, whose manifest says
``auto_install``. A branch nobody installed is never applied, so an
uninstalled module's tables do not come back on the next restart
(issue #91). Installing a module applies its branch through the pending
processor, as before.

Runs Alembic in-process: there is no event loop in the CLI, so
``env.py``'s ``asyncio.run`` is fine here (the lifespan can't do that,
hence the processor's subprocess).
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import text

from app.core.plugins.alembic_paths import alembic_cfg_path, boot_upgrade_targets
from app.core.plugins.loader import register_discovered
from app.core.plugins.state import ModuleState
from app.database import async_session_maker


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("db", help="Database schema operations")
    db_sub = parser.add_subparsers(dest="db_command", required=True)

    p_upgrade = db_sub.add_parser(
        "upgrade",
        help="Apply core migrations plus the branches of installed modules (boot step)",
    )
    p_upgrade.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the Alembic targets without applying them",
    )
    p_upgrade.set_defaults(func=_cmd_upgrade)


def _cmd_upgrade(args: argparse.Namespace) -> int:
    modules = register_discovered()
    states = asyncio.run(_load_states())

    def wanted(module) -> bool:
        state = states.get(module.name)
        if state is None:
            return module.get_manifest().auto_install
        return state == ModuleState.INSTALLED.value

    targets = boot_upgrade_targets(modules, wanted)
    if not targets:
        print("db upgrade: no Alembic targets (no script directory?)")
        return 1

    print(f"db upgrade: targets = {targets}")
    if args.dry_run:
        return 0

    from alembic.config import Config

    from alembic import command

    cfg = Config(str(alembic_cfg_path()))
    for target in targets:
        command.upgrade(cfg, target)
    print(f"db upgrade: applied {len(targets)} target(s)")
    return 0


async def _load_states() -> dict[str, str]:
    """``name -> state`` from ``core_module``, or ``{}`` before the table exists."""
    async with async_session_maker() as session:
        exists = await session.scalar(text("SELECT to_regclass('core_module')"))
        if exists is None:
            return {}
        rows = await session.execute(text("SELECT name, state FROM core_module"))
        return {name: state for name, state in rows.all()}
