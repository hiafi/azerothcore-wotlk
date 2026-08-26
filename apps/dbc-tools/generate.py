#!/usr/bin/env python3
"""
DBC build pipeline — forward generator.

Reads source/ids.yaml plus every file under source/spells/*.csv and
source/talents/*.yaml (split by class purely for human-editability — see
apps/dbc-tools/README.md), builds full-width DBC rows, and produces:
  1. A pending world-DB SQL migration (data/sql/updates/pending_db_world/) —
     load-bearing: this alone is enough for the server (see
     docs/dbc-build-pipeline.md's "Key finding").
  2. A client patch: loose files under var/dbc-patch/DBFilesClient/ *and* an
     MPQ at var/dbc-patch/patch-Z.mpq — cosmetic-but-necessary, what the
     client actually renders (name, icon, tooltip, talent frame).
  3. The same bytes copied into env/dist/data/dbc/ if that directory exists.

Usage: python3 apps/dbc-tools/generate.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfile, dbcfmt, patch_out, resolve, source, sql_out, state  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

SOURCE_DIR = TOOL_ROOT / "source"
BASE_DBC_DIR = state.BASE_DBC_DIR
PENDING_SQL_DIR = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"

SECONDARY_TABLES = {
    "spellcasttimes": dbcfmt.SPELLCASTTIMES,
    "spellduration": dbcfmt.SPELLDURATION,
    "spellrange": dbcfmt.SPELLRANGE,
    "spellradius": dbcfmt.SPELLRADIUS,
}


def main() -> int:
    ids_cfg = source.load_ids(SOURCE_DIR / "ids.yaml")
    spell_entries = source.load_spells_csv(SOURCE_DIR / "spells")
    talents = source.load_talents_yaml(SOURCE_DIR / "talents")

    existing_spells = state.load_existing_rows(dbcfmt.SPELL)
    existing_talents = state.load_existing_rows(dbcfmt.TALENT)
    existing_talenttabs = state.load_existing_rows(dbcfmt.TALENTTAB)
    existing_skilllineabilities = state.load_existing_rows(dbcfmt.SKILLLINEABILITY)
    existing_secondary = {
        name: list(state.load_existing_rows(table).values())
        for name, table in SECONDARY_TABLES.items()
    }

    # Reconcile source/ against what's actually live: an entry is either new
    # (id inside the reserved block), a deliberate edit to something that
    # already exists (id outside the block, but changed), or an untouched
    # reference copy pulled in for reading only (id outside the block,
    # unchanged) — the last case is silently skipped. See lib/resolve.py.
    # Spell comparisons use a throwaway ReuseContext so an unchanged
    # reference spell's build attempt can't leave an orphan minted
    # secondary-table row behind (see resolve.py's build_one note).
    scratch_reuse = ReuseContext(existing_secondary, ids_cfg)
    spell_resolved = resolve.resolve_rows(
        spell_entries, ids_cfg["spell"], existing_spells,
        lambda e: build.build_spell_row(e, scratch_reuse),
    )
    talent_resolved = resolve.resolve_rows(
        talents["talents"], ids_cfg["talent"], existing_talents, build.build_talent_row,
    )
    talenttab_resolved = resolve.resolve_rows(
        talents["tabs"], ids_cfg["talenttab"], existing_talenttabs, build.build_talenttab_row,
    )
    skilllineability_resolved = resolve.resolve_rows(
        talents["skill_line_abilities"], ids_cfg["skilllineability"],
        existing_skilllineabilities, build.build_skilllineability_row,
    )
    n_unchanged = (
        spell_resolved.unchanged + talent_resolved.unchanged + talenttab_resolved.unchanged
        + skilllineability_resolved.unchanged
    )
    if n_unchanged:
        print(
            f"note: {n_unchanged} row(s) in source/ are unchanged copies of existing data "
            f"(pulled in for reference — see apps/dbc-tools/README.md) and were not "
            f"generated: {spell_resolved.unchanged} spell(s), {talent_resolved.unchanged} "
            f"talent(s), {talenttab_resolved.unchanged} talent tab(s), "
            f"{skilllineability_resolved.unchanged} skill line abilitie(s)"
        )
    n_edited = (
        len(spell_resolved.edited_ids) + len(talent_resolved.edited_ids)
        + len(talenttab_resolved.edited_ids) + len(skilllineability_resolved.edited_ids)
    )
    if n_edited:
        print(
            f"editing {len(spell_resolved.edited_ids)} existing spell(s) "
            f"{spell_resolved.edited_ids}, {len(talent_resolved.edited_ids)} talent(s) "
            f"{talent_resolved.edited_ids}, {len(talenttab_resolved.edited_ids)} talent "
            f"tab(s) {talenttab_resolved.edited_ids}, "
            f"{len(skilllineability_resolved.edited_ids)} skill line abilitie(s) "
            f"{skilllineability_resolved.edited_ids}"
        )

    # Real build pass (real ReuseContext this time) over just what survived
    # reconciliation — this is what actually gets emitted.
    reuse = ReuseContext(existing_secondary, ids_cfg)
    spell_rows = [build.build_spell_row(e, reuse) for e in spell_resolved.entries]
    talent_rows = [build.build_talent_row(e) for e in talent_resolved.entries]
    talenttab_rows = [build.build_talenttab_row(e) for e in talenttab_resolved.entries]
    skilllineability_rows = [
        build.build_skilllineability_row(e) for e in skilllineability_resolved.entries
    ]

    # -- pending SQL: reserved range + explicit edited IDs, per table --
    blocks = [
        (dbcfmt.SPELL, ids_cfg["spell"], spell_rows, spell_resolved.edited_ids),
        (dbcfmt.TALENT, ids_cfg["talent"], talent_rows, talent_resolved.edited_ids),
        (dbcfmt.TALENTTAB, ids_cfg["talenttab"], talenttab_rows, talenttab_resolved.edited_ids),
        (
            dbcfmt.SKILLLINEABILITY, ids_cfg["skilllineability"], skilllineability_rows,
            skilllineability_resolved.edited_ids,
        ),
    ]
    for name, table in SECONDARY_TABLES.items():
        blocks.append((table, ids_cfg[name], reuse.minted.get(name, []), []))

    header = (
        "-- Generated by apps/dbc-tools/generate.py — DO NOT hand-edit.\n"
        "-- Source of truth: apps/dbc-tools/source/{spells,talents}/*.\n"
        "-- Regenerate with: python3 apps/dbc-tools/generate.py"
    )
    rev = int(time.time() * 1_000_000_000)
    out_path = PENDING_SQL_DIR / f"rev_{rev}.sql"
    wrote_sql = sql_out.emit_pending_sql(out_path, blocks, header)
    print(f"SQL: wrote {out_path.relative_to(REPO_ROOT)}" if wrote_sql else "SQL: nothing to emit")

    # -- client patch: needs a complete file (base + new), so any table with
    # new/changed rows but no extracted base file gets skipped, not
    # half-written --
    new_rows_by_table = {
        dbcfmt.SPELL: {r["ID"]: r for r in spell_rows},
        dbcfmt.TALENT: {r["ID"]: r for r in talent_rows},
        dbcfmt.TALENTTAB: {r["ID"]: r for r in talenttab_rows},
        dbcfmt.SKILLLINEABILITY: {r["ID"]: r for r in skilllineability_rows},
    }
    for name, table in SECONDARY_TABLES.items():
        minted = reuse.minted.get(name, [])
        if minted:
            new_rows_by_table[table] = {r["ID"]: r for r in minted}

    dbc_files: dict[str, bytes] = {}
    for table, new_rows in new_rows_by_table.items():
        if not new_rows:
            continue
        dbc_path = BASE_DBC_DIR / table.dbc_filename
        if not dbc_path.is_file():
            print(
                f"patch: SKIPPING {table.dbc_filename} — no base client DBC at "
                f"{dbc_path.relative_to(REPO_ROOT)}; server SQL overlay is still "
                f"complete, but a client patch needs the full stock file as a base "
                f"layer (see docs/dbc-build-pipeline.md)."
            )
            continue
        base_rows = dbcfile.read_dbc(dbc_path, table)
        merged = {row[table.index_column]: row for row in base_rows}
        merged.update(new_rows)
        all_rows = list(merged.values())
        if table is dbcfmt.TALENT:
            # Talent.dbc's physical row order is load-bearing to the client - see
            # dbcfile.order_talent_rows's docstring.
            all_rows = dbcfile.order_talent_rows(all_rows, base_rows)
            dbc_files[table.dbc_filename] = dbcfile.pack_dbc_bytes(table, all_rows, sort=False)
        else:
            dbc_files[table.dbc_filename] = dbcfile.pack_dbc_bytes(table, all_rows)

    if dbc_files:
        report = patch_out.write_patch(dbc_files)
        print(f"patch: loose files -> {patch_out.LOOSE_DIR}")
        print(f"patch: mpq -> {report['mpq']}")
        if report["env_dbc"]:
            print(f"patch: also copied into {patch_out.ENV_DBC_DIR}")
    else:
        print("patch: nothing to write (no base DBCs available yet)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
