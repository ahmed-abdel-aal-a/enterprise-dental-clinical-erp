"""``boot_upgrade_targets`` — which Alembic heads a boot applies (ADR 0020).

Pure graph test on the real ``alembic.ini`` + discovered modules; no DB.
"""

from __future__ import annotations

from app.core.plugins.alembic_paths import (
    boot_upgrade_targets,
    resolve_module_branch_head,
)
from app.core.plugins.loader import register_discovered


def test_targets_are_core_heads_plus_wanted_module_heads() -> None:
    modules = register_discovered()
    targets = boot_upgrade_targets(modules, wanted=lambda m: True)

    assert targets[0].isdigit(), "core head comes first"
    for module in modules:
        head = resolve_module_branch_head(module)
        if head is not None:
            assert head in targets, f"{module.name} head {head} missing"
    # A module whose branch tip is not a global head (budget chains into
    # payments) must still be named — ``heads`` alone would miss it.
    assert resolve_module_branch_head(next(m for m in modules if m.name == "budget")) in targets


def test_unwanted_module_branch_is_never_named() -> None:
    modules = register_discovered()
    perio = next(m for m in modules if m.name == "periodontogram")
    perio_head = resolve_module_branch_head(perio)
    assert perio_head is not None

    targets = boot_upgrade_targets(modules, wanted=lambda m: m.name != "periodontogram")
    assert perio_head not in targets
    # …and everything else is untouched.
    for module in modules:
        if module.name == "periodontogram":
            continue
        head = resolve_module_branch_head(module)
        if head is not None:
            assert head in targets


def test_core_heads_do_not_depend_on_wanted() -> None:
    modules = register_discovered()
    only_core = boot_upgrade_targets(modules, wanted=lambda m: False)
    assert only_core, "core heads are always applied"
    assert all(t.isdigit() for t in only_core), only_core
