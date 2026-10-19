#!/usr/bin/env python3
"""
DBC build pipeline — reverse entry point: pull existing Talent.dbc /
TalentTab.dbc rows into source/talents/*.yaml (companion to pull.py, which
does the same for spells — see docs/dbc-build-pipeline.md).

Reads the merged base-DBC ⊕ current-overlay view for Talent/TalentTab,
reverses each row through lib/reverse.py, and appends the results to the
matching per-class file — ready to hand-edit and regenerate.

Usage:
  python3 apps/dbc-tools/pull_talents.py --class mage
  python3 apps/dbc-tools/pull_talents.py --tab 8,9,10
  python3 apps/dbc-tools/pull_talents.py --talent 1,2,3

DSL mode (`--dsl`): prints ready-to-paste `tab(...)` / `talent(...)` declarations to stdout instead of
appending to source/talents/*.yaml (the legacy format no class uses any more), the counterpart of
pull_dsl.py for talents:
  python3 apps/dbc-tools/pull_talents.py --tab 409,410,411 --dsl
It never writes a file and skips every tab/talent id already declared under source/classes/ (or still in
source/talents/). Rank ids stay bare ints in a plain `talent(...)`: no `granted_by_talent`, so no
SkillLineAbility row is derived - an untouched reference copy that generate.py silently skips. `--tab`
does not filter on ClassMask (only `--class` does), so pet tabs (ClassMask 0, PetTalentMask 1/2/4) come through.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfmt, reverse, source, state  # noqa: E402

SOURCE_DIR = TOOL_ROOT / "source"
TALENTS_DIR = SOURCE_DIR / "talents"

# ClassMask bit = 1 << (class_id - 1). Class ID 10 is unused in 3.3.5a (see
# docs/dbc-build-pipeline.md's Two-realm strategy note), so there's no bit 512
# entry here.
CLASS_MASK = {
    "warrior": 1, "paladin": 2, "hunter": 4, "rogue": 8, "priest": 16,
    "deathknight": 32, "shaman": 64, "mage": 128, "warlock": 256, "druid": 1024,
}


def parse_id_spec(spec: str) -> list[int]:
    ids: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            ids.extend(range(int(lo), int(hi) + 1))
        else:
            ids.append(int(part))
    return ids


def print_dsl(existing_tabs, existing_talents, wanted_tab_ids, wanted_talent_ids) -> int:
    """`--dsl` mode: see the module docstring. Always returns 0 (nothing to print is not an error)."""
    from csv_to_dsl import _plain_talent_call_lines, _slug, _tab_call_lines
    from lib import spell_tables, trainer_state
    from lib.dsl import registry as dsl_registry

    creature_table_index = spell_tables.load_creature_table_index()
    dsl = dsl_registry.load_classes_dir(
        SOURCE_DIR / "classes", ids_cfg=source.load_ids(SOURCE_DIR / "ids.yaml"),
        trainer_index=trainer_state.load_trainer_index(),
        existing_group_ids={int(row["id"]) for row in trainer_state.load_table_rows("spell_group")},
        shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
        existing_creature_rows={int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")},
        creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        live_data=spell_tables.load_dsl_live_data(),
    )
    declared_tabs = {e["id"] for e in dsl["tabs"]}
    declared_talents = {e["id"] for e in dsl["talents"]}
    if TALENTS_DIR.is_dir():
        legacy = source.load_talents_yaml(TALENTS_DIR)
        declared_tabs |= {e["id"] for e in legacy["tabs"]}
        declared_talents |= {e["id"] for e in legacy["talents"]}

    tab_vars: dict[int, str] = {}
    chunks = []
    for tab_id in wanted_tab_ids:
        row = existing_tabs.get(tab_id)
        if row is None:
            print(f"# tab {tab_id}: not found in talenttab_dbc (base DBC + overlay)", file=sys.stderr)
            continue
        entry = source.talent_entry_to_yaml_safe(reverse.reverse_talenttab_row(row))
        var = _slug(entry["name"], tab_id) + "_tab"
        tab_vars[tab_id] = var
        if tab_id in declared_tabs:
            print(f"# skip tab {tab_id}: already declared under source/classes/", file=sys.stderr)
            continue
        chunks.append("\n".join(_tab_call_lines(entry, var, None)))
    for talent_id in wanted_talent_ids:
        row = existing_talents.get(talent_id)
        if row is None:
            print(f"# talent {talent_id}: not found in talent_dbc (base DBC + overlay)", file=sys.stderr)
            continue
        if talent_id in declared_talents:
            print(f"# skip talent {talent_id}: already declared under source/classes/", file=sys.stderr)
            continue
        entry = source.talent_entry_to_yaml_safe(reverse.reverse_talent_row(row))
        tab_var = tab_vars.get(entry["tab_id"])
        if tab_var is None:
            print(f"# talent {talent_id}: its tab {entry['tab_id']} is not among the pulled tabs; pull the tab "
                  f"too (--tab {entry['tab_id']}) so the talent can reference it", file=sys.stderr)
            continue
        chunks.append("\n".join(_plain_talent_call_lines(entry, f"talent_{talent_id}", tab_var)))
    if chunks:
        print("\n\n\n".join(chunks))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--class", dest="klass", choices=sorted(CLASS_MASK),
        help="pull every talent tab (by ClassMask) and every talent in it for this class",
    )
    group.add_argument("--tab", help="comma-separated TalentTab IDs and/or ranges")
    group.add_argument("--talent", help="comma-separated Talent IDs and/or ranges")
    ap.add_argument(
        "--dest", help="destination file stem (default: --class, when given)",
    )
    ap.add_argument(
        "--dsl", action="store_true",
        help="print DSL tab(...)/talent(...) declarations to stdout instead of writing source/talents/*.yaml",
    )
    args = ap.parse_args()

    existing_tabs = state.load_existing_rows(dbcfmt.TALENTTAB)
    existing_talents = state.load_existing_rows(dbcfmt.TALENT)

    if args.klass:
        mask = CLASS_MASK[args.klass]
        wanted_tab_ids = sorted(i for i, row in existing_tabs.items() if row["ClassMask"] & mask)
        wanted_talent_ids = sorted(
            i for i, row in existing_talents.items() if row["TabID"] in wanted_tab_ids
        )
        dest = args.dest or args.klass
    elif args.tab:
        wanted_tab_ids = parse_id_spec(args.tab)
        wanted_talent_ids = sorted(
            i for i, row in existing_talents.items() if row["TabID"] in wanted_tab_ids
        )
        dest = args.dest
        if not dest and not args.dsl:
            ap.error("--dest is required when pulling by --tab (no --class to default to)")
    else:
        wanted_tab_ids = []
        wanted_talent_ids = parse_id_spec(args.talent)
        dest = args.dest
        if not dest and not args.dsl:
            ap.error("--dest is required when pulling by --talent (no --class to default to)")

    if args.dsl:
        return print_dsl(existing_tabs, existing_talents, wanted_tab_ids, wanted_talent_ids)

    already = {}
    if TALENTS_DIR.is_dir():
        existing_source = source.load_talents_yaml(TALENTS_DIR)
        already["tabs"] = {e["id"] for e in existing_source["tabs"]}
        already["talents"] = {e["id"] for e in existing_source["talents"]}
    else:
        already = {"tabs": set(), "talents": set()}

    new_tabs, new_talents = [], []
    for tab_id in wanted_tab_ids:
        if tab_id in already["tabs"]:
            print(f"skip tab {tab_id}: already present in source/talents/")
            continue
        new_tabs.append(
            source.talent_entry_to_yaml_safe(reverse.reverse_talenttab_row(existing_tabs[tab_id]))
        )
    for talent_id in wanted_talent_ids:
        row = existing_talents.get(talent_id)
        if not row:
            print(f"talent {talent_id}: not found in talent_dbc (base DBC + overlay)")
            continue
        if talent_id in already["talents"]:
            print(f"skip talent {talent_id}: already present in source/talents/")
            continue
        new_talents.append(source.talent_entry_to_yaml_safe(reverse.reverse_talent_row(row)))

    if not new_tabs and not new_talents:
        print("nothing new to pull")
        return 0

    out_path = TALENTS_DIR / f"{dest}.yaml"
    if out_path.is_file():
        header, _ = source.split_leading_comments(out_path.read_text(encoding="utf-8"))
        data = source.load_talents_yaml_file(out_path)
    else:
        header, data = "", {"tabs": [], "talents": []}
    data["tabs"].extend(new_tabs)
    data["talents"].extend(new_talents)
    source.write_talents_yaml_file(out_path, header, data)

    print(f"pulled {len(new_tabs)} tab(s), {len(new_talents)} talent(s) into "
          f"{out_path.relative_to(TOOL_ROOT.parent.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
