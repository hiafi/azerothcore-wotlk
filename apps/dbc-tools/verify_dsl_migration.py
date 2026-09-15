#!/usr/bin/env python3
"""
Row-level fidelity check for a `csv_to_dsl.py` conversion - the actual
safety net for Phase 4 of `.agents/plans/spell-source-dsl/
spell-source-dsl.PLAN.md`, not `csv_to_dsl.py`'s own logic.

Loads a class's OLD source (`source/spells/<class>*.csv` +
`source/talents/<class>.yaml`, via `lib.source`, exactly as `generate.py`
already does) and its NEW source (`source/classes/<class>.py`, via
`lib.dsl.registry`), builds every row through the *same*, completely
unmodified `lib.build` functions with one shared `ReuseContext`, and asserts
the two full-width rows are identical for every ID - the same technique
Phase 0's `lib/test_dsl.py` used for 3 hand-picked spells, scaled to every
row a real class actually has. `granted_by_talent`'s auto-derived
`SkillLineAbility` rows are matched back to the old YAML's explicit ones by
`spell_id` (not by row `id`, which Phase 2 doesn't auto-mint - see the
plan's "known limitation") since a migration is expected to keep every
existing ID unchanged, not just every value.

Exit code 0 and "MATCH" printed for everything means it's safe to delete the
old CSV/YAML files for this class; anything else must be root-caused (a
`csv_to_dsl.py` bug, most likely) before doing that; deleting them without
this passing is exactly what turns "still authoritative" into a real data
loss for both formats at once.

Usage: python3 apps/dbc-tools/verify_dsl_migration.py <class>
"""

from __future__ import annotations

import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, source  # noqa: E402
from lib.dsl import registry as dsl_registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

SOURCE_DIR = TOOL_ROOT / "source"


def _fresh_reuse() -> ReuseContext:
    ids_cfg = source.load_ids(SOURCE_DIR / "ids.yaml")
    return ReuseContext(existing_rows_by_table={}, ids_cfg=ids_cfg)


class FakeTrainerIndex:
    """`trained_by()` isn't exercised by this migration (neither source
    format carries trainer_spell data - see the plan's Phase 3 vs Phase 4
    scope note), but `load_class_file` still needs *something* if a class
    file happens to import it; a trainer_index that calls everything dead
    would surface that immediately as a loud failure rather than silently
    doing nothing."""

    existing_trainer_spells: dict = {}

    def trainer_problems(self, trainer_id: int) -> list[str]:
        return [f"verify_dsl_migration.py: no real TrainerIndex - trained_by() shouldn't be "
                f"called during a Phase 4 migration (TrainerId {trainer_id})"]


def _diff(label: str, old: dict, new: dict) -> list[str]:
    problems = []
    keys = set(old) | set(new)
    for key in sorted(keys, key=str):
        if old.get(key) != new.get(key):
            problems.append(f"  {label}: field {key!r} differs: old={old.get(key)!r} new={new.get(key)!r}")
    return problems


def verify(class_name: str) -> list[str]:
    problems: list[str] = []
    ids_cfg = source.load_ids(SOURCE_DIR / "ids.yaml")

    old_spells = {
        e["id"]: e for e in source.load_one_spell_file(SOURCE_DIR / "spells" / f"{class_name}.csv")
    }
    talents_path = SOURCE_DIR / "spells" / f"{class_name}_talents.csv"
    if talents_path.is_file():
        old_spells.update({e["id"]: e for e in source.load_one_spell_file(talents_path)})
    old_talent_data = source.load_talents_yaml_file(SOURCE_DIR / "talents" / f"{class_name}.yaml")
    old_talents = {e["id"]: e for e in old_talent_data["talents"]}
    old_tabs = {e["id"]: e for e in old_talent_data["tabs"]}
    old_slas_by_spell_id = {e["spell_id"]: e for e in old_talent_data["skill_line_abilities"]}

    # A migrated class is either a single `<class>.py` file or a `<class>/` directory (split via
    # split_class_file.py) - try the directory layout first since that's what a class ends up in
    # once split; both loaders return the same `Registry` shape either way.
    class_dir = SOURCE_DIR / "classes" / class_name
    if class_dir.is_dir():
        new_registry = dsl_registry.load_class_package(
            class_dir, ids_cfg=ids_cfg, trainer_index=FakeTrainerIndex(),
        )
    else:
        new_registry = dsl_registry.load_class_file(
            SOURCE_DIR / "classes" / f"{class_name}.py", ids_cfg=ids_cfg, trainer_index=FakeTrainerIndex(),
        )
    new_spells = {e["id"]: e for e in new_registry.spells}
    new_talents = {e["id"]: e for e in new_registry.talents}
    new_tabs = {e["id"]: e for e in new_registry.tabs}
    new_slas_by_spell_id = {e["spell_id"]: e for e in new_registry.skill_line_abilities}

    if set(old_spells) != set(new_spells):
        problems.append(
            f"spell ID sets differ: only in old={sorted(set(old_spells) - set(new_spells))} "
            f"only in new={sorted(set(new_spells) - set(old_spells))}"
        )
    reuse = _fresh_reuse()
    for spell_id in sorted(set(old_spells) & set(new_spells)):
        old_row = build.build_spell_row(old_spells[spell_id], reuse)
        new_row = build.build_spell_row(new_spells[spell_id], reuse)
        problems.extend(_diff(f"spell {spell_id} ({old_spells[spell_id].get('name')})", old_row, new_row))

    if set(old_talents) != set(new_talents):
        problems.append(
            f"talent ID sets differ: only in old={sorted(set(old_talents) - set(new_talents))} "
            f"only in new={sorted(set(new_talents) - set(old_talents))}"
        )
    for talent_id in sorted(set(old_talents) & set(new_talents)):
        old_row = build.build_talent_row(old_talents[talent_id])
        new_row = build.build_talent_row(new_talents[talent_id])
        problems.extend(_diff(f"talent {talent_id}", old_row, new_row))

    if set(old_tabs) != set(new_tabs):
        problems.append(
            f"tab ID sets differ: only in old={sorted(set(old_tabs) - set(new_tabs))} "
            f"only in new={sorted(set(new_tabs) - set(old_tabs))}"
        )
    for tab_id in sorted(set(old_tabs) & set(new_tabs)):
        old_row = build.build_talenttab_row(old_tabs[tab_id])
        new_row = build.build_talenttab_row(new_tabs[tab_id])
        problems.extend(_diff(f"tab {tab_id}", old_row, new_row))

    # Matched by spell_id, not row id - granted_by_talent's derived
    # SkillLineAbility rows keep whatever id csv_to_dsl.py copied from the
    # old data (Phase 2 doesn't auto-mint), so the ids always agree when
    # everything else does; spell_id is the more informative key for a
    # mismatch message anyway (names the actual spell involved).
    if set(old_slas_by_spell_id) != set(new_slas_by_spell_id):
        problems.append(
            f"SkillLineAbility spell_id sets differ: only in old="
            f"{sorted(set(old_slas_by_spell_id) - set(new_slas_by_spell_id))} only in new="
            f"{sorted(set(new_slas_by_spell_id) - set(old_slas_by_spell_id))}"
        )
    for spell_id in sorted(set(old_slas_by_spell_id) & set(new_slas_by_spell_id)):
        old_row = build.build_skilllineability_row(old_slas_by_spell_id[spell_id])
        new_row = build.build_skilllineability_row(new_slas_by_spell_id[spell_id])
        problems.extend(_diff(f"skill_line_ability for spell {spell_id}", old_row, new_row))

    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <class>", file=sys.stderr)
        return 2
    class_name = argv[1]
    problems = verify(class_name)
    if not problems:
        print(f"MATCH: {class_name} - every spell/talent/tab/skill_line_ability row is identical")
        return 0
    print(f"MISMATCH: {class_name} - {len(problems)} problem(s):")
    for p in problems:
        print(p)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
