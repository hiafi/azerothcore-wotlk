#!/usr/bin/env python3
"""
One-off DBC content patch: the client visuals the reworked Stratholme bosses need (Stratholme build, WP V-1 for wave 1,
V-2 appends wave 2; handoff .agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.10, picks s7 #21). Same shape
as patch_shadowfang_keep_vfx_models.py and patch_deadmines_vfx_models.py (whose row helpers it shares).

ID blocks (ids.yaml reservation `stratholme`):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: 90500-90549 (wave 1 uses 90500-90506).
- No GameObjectDisplayInfo, CreatureDisplayInfo or SoundEntries row is minted (every pick is a stock display or sound).

What wave 1 mints (stock models only: no model or texture ships; every look unconfirmed until seen in game):
- Nerub'enkan NE3 web patch: stock `Spells\\Web_State.mdx` (SpellVisualEffectName 595, a 2.3 yd ground web quad) at a
  fixed scale with AreaEffectSize 0: 4.3 for the 5 yd radius (10 / 2.3), 6.0 for the 7 yd heroic radius (14 / 2.3).
  Each size has an AREA look (PersistentAreaKit WorldEffect, for an area aura's dynamic object) and a STATE look
  (StateKit BaseEffect, a stalker aura, one stalker per patch), the Deadmines goo layout.
- Ramstein RG3 gut puddle: stock `goo_flow_state.m2` (47.8 yd at scale 1, the Deadmines Fish Stew model) at 0.25 for a
  6 yd radius (12 yd across); AREA and STATE looks. The shipped Fish Stew rows (4 yd radius) stay available.
- Baroness BA1 Keened skull: stock CurseofWeakness_Head (SpellVisualEffectName 311) as a StateKit HeadEffect, so the
  skull lasts the whole 5 s keen (Curse of Doom's own kit is a 3 s impact kit). No sound.
- Everything else in the s3.10 wave 1 rows is stock and needs no rows: `source/npcs/stratholme/_visuals.py` names every
  stock SpellVisual / display / sound id the boss files use (with the look corrections applied). `--dry-run` checks that
  they all exist in the working copy.

SpellVisual is server-loaded, so `--sql-out PATH` emits its overlay. SpellVisualKit and SpellVisualEffectName are
client-only.

Usage:
    python3 apps/dbc-tools/patch_stratholme_vfx_models.py --dry-run     # print rows + checks + SQL, write nothing
    python3 apps/dbc-tools/patch_stratholme_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
then build_patch_m.py (patch-M.mpq carries the DBCs). No asset needs extracting.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, _kit_row, _merge, _row, model_path
from patch_rogue_vfx_models import NO_ATTACHMENT

# Stratholme block (ids.yaml `reservations: stratholme:`).
VISUAL_BLOCK = {"start": 90500, "end": 90549}

# --- SpellVisualEffectName ---
EFFECT_WEB_PATCH_5 = 90500            # Web_State at WEB_PATCH_5_SCALE
EFFECT_WEB_PATCH_7 = 90501            # Web_State at WEB_PATCH_7_SCALE
EFFECT_GUT_PUDDLE = 90502             # goo_flow_state at GUT_PUDDLE_SCALE

# --- SpellVisualKit (AREA: WorldEffect, the PersistentAreaKit of an area aura; STATE: BaseEffect, a stalker aura) ---
KIT_WEB_PATCH_5_AREA = 90500
KIT_WEB_PATCH_5_STATE = 90501
KIT_WEB_PATCH_7_AREA = 90502
KIT_WEB_PATCH_7_STATE = 90503
KIT_GUT_PUDDLE_AREA = 90504
KIT_GUT_PUDDLE_STATE = 90505
KIT_KEENED_SKULL_STATE = 90506        # StateKit: HeadEffect = stock SVEN 311

# --- SpellVisual (same ids as _visuals.py) ---
SV_WEB_PATCH_5_AREA = 90500
SV_WEB_PATCH_5_STATE = 90501
SV_WEB_PATCH_7_AREA = 90502
SV_WEB_PATCH_7_STATE = 90503
SV_GUT_PUDDLE_AREA = 90504
SV_GUT_PUDDLE_STATE = 90505
SV_KEENED_SKULL_STATE = 90506

# --- Scales (first guesses; tune in game, one number each) ---
WEB_STATE_YARDS = 2.3                 # Web_State's quad at scale 1 (VISUALS-REPORT, Nerub'enkan)
WEB_PATCH_5_SCALE = 4.3               # 10 yd across / 2.3 (rounded)
WEB_PATCH_7_SCALE = 6.0               # 14 yd across / 2.3 (rounded)
GOO_FLOW_YARDS = 47.8                 # goo_flow_state at scale 1 (patch_deadmines_vfx_models.py)
GUT_PUDDLE_SCALE = 0.25               # 12 yd across / 47.8 (rounded)

# --- Stock ids reused as-is (checked by --dry-run) ---
STOCK_WEB_STATE_EFFECT = 595          # Spells\Web_State.mdx
STOCK_CURSE_HEAD_EFFECT = 311         # Spells\CurseofWeakness_Head.mdx

MODEL_WEB_STATE = "Web_State"
MODEL_GOO_FLOW = "goo_flow_state"


def build_effect_name_rows() -> list[dict]:
    def effect(id_, name, model, scale):
        # AreaEffectSize 0: the size is the fixed Scale, not the spell radius.
        return _row(dbcfmt.SPELLVISUALEFFECTNAME, id_, Name=f"{name} (Custom)", FileName=model_path(model),
                    AreaEffectSize=0.0, Scale=scale, MinAllowedScale=0.01, MaxAllowedScale=100.0)

    return [
        effect(EFFECT_WEB_PATCH_5, "Web Patch 5 yd", MODEL_WEB_STATE, WEB_PATCH_5_SCALE),
        effect(EFFECT_WEB_PATCH_7, "Web Patch 7 yd", MODEL_WEB_STATE, WEB_PATCH_7_SCALE),
        effect(EFFECT_GUT_PUDDLE, "Gut Puddle 6 yd", MODEL_GOO_FLOW, GUT_PUDDLE_SCALE),
    ]


def build_kit_rows() -> list[dict]:
    return [
        _kit_row(KIT_WEB_PATCH_5_AREA, WorldEffect=EFFECT_WEB_PATCH_5),
        _kit_row(KIT_WEB_PATCH_5_STATE, BaseEffect=EFFECT_WEB_PATCH_5),
        _kit_row(KIT_WEB_PATCH_7_AREA, WorldEffect=EFFECT_WEB_PATCH_7),
        _kit_row(KIT_WEB_PATCH_7_STATE, BaseEffect=EFFECT_WEB_PATCH_7),
        _kit_row(KIT_GUT_PUDDLE_AREA, WorldEffect=EFFECT_GUT_PUDDLE),
        _kit_row(KIT_GUT_PUDDLE_STATE, BaseEffect=EFFECT_GUT_PUDDLE),
        _kit_row(KIT_KEENED_SKULL_STATE, HeadEffect=STOCK_CURSE_HEAD_EFFECT),
    ]


def build_spellvisual_rows() -> list[dict]:
    def visual(id_, **fields):
        row = _row(dbcfmt.SPELLVISUAL, id_, MissileAttachment=NO_ATTACHMENT)
        row.update(fields)
        return row

    return [
        visual(SV_WEB_PATCH_5_AREA, PersistentAreaKit=KIT_WEB_PATCH_5_AREA),
        visual(SV_WEB_PATCH_5_STATE, StateKit=KIT_WEB_PATCH_5_STATE),
        visual(SV_WEB_PATCH_7_AREA, PersistentAreaKit=KIT_WEB_PATCH_7_AREA),
        visual(SV_WEB_PATCH_7_STATE, StateKit=KIT_WEB_PATCH_7_STATE),
        visual(SV_GUT_PUDDLE_AREA, PersistentAreaKit=KIT_GUT_PUDDLE_AREA),
        visual(SV_GUT_PUDDLE_STATE, StateKit=KIT_GUT_PUDDLE_STATE),
        visual(SV_KEENED_SKULL_STATE, StateKit=KIT_KEENED_SKULL_STATE),
    ]


def _stock_rows(filename: str, table: dbcfmt.DbcTable, ids: set[int]) -> dict[int, dict]:
    found = {r["ID"]: r for r in dbcfile.read_dbc(DBC_DIR / filename, table) if r["ID"] in ids}
    missing = ids - set(found)
    if missing:
        raise SystemExit(f"{filename} lacks stock id(s) {sorted(missing)} in the working copy")
    return found


def _load_visuals():
    """source/npcs/stratholme/_visuals.py by path (source/ is not a package): the ids the boss files use."""
    path = Path(__file__).resolve().parent / "source" / "npcs" / "stratholme" / "_visuals.py"
    spec = importlib.util.spec_from_file_location("stratholme_visuals", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_stock_ids() -> list[str]:
    """Confirms every stock id `_visuals.py` names (and the two stock effect names the rows point at) exists in the
    working copy; returns a one-line note."""
    visuals = _load_visuals()
    _stock_rows("SpellVisual.dbc", dbcfmt.SPELLVISUAL,
                set(visuals.STOCK_SPELL_VISUALS) | set(visuals.MINTED_ELSEWHERE_SPELL_VISUALS))
    _stock_rows("SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME,
                {STOCK_WEB_STATE_EFFECT, STOCK_CURSE_HEAD_EFFECT})
    _stock_rows("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, set(visuals.STOCK_CREATURE_DISPLAYS))
    _stock_rows("GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO, set(visuals.STOCK_GAMEOBJECT_DISPLAYS))
    _stock_rows("SoundEntries.dbc", dbcfmt.SOUNDENTRIES, set(visuals.STOCK_SOUND_ENTRIES))
    return [f"{len(set(visuals.STOCK_SPELL_VISUALS))} SpellVisual ids, {len(visuals.STOCK_CREATURE_DISPLAYS)} "
            f"CreatureDisplayInfo ids, {len(visuals.STOCK_GAMEOBJECT_DISPLAYS)} GameObjectDisplayInfo ids and "
            f"{len(visuals.STOCK_SOUND_ENTRIES)} SoundEntries ids exist"]


def build_pending_sql() -> str:
    """Server-side overlay: SpellVisual only (the other two tables are client-only). Range-deletes exactly the ids this
    script mints, so a rerun is idempotent."""
    rows = build_spellvisual_rows()
    ids = [r["ID"] for r in rows]
    return _table_block(dbcfmt.SPELLVISUAL, {"start": min(ids), "end": max(ids)}, rows, []) + "\n"


def _check_block(rows: list[dict], block: dict, what: str) -> None:
    for row in rows:
        if not block["start"] <= row["ID"] <= block["end"]:
            raise SystemExit(f"{what} id {row['ID']} is outside the stratholme block {block}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sql-out", type=Path, default=None,
                        help="Write the matching server-side SQL migration to this path (see module docstring).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the rows, the stock-id checks and the SQL; write nothing.")
    args = parser.parse_args()

    effect_rows = build_effect_name_rows()
    kit_rows = build_kit_rows()
    visual_rows = build_spellvisual_rows()
    for rows, what in ((effect_rows, "SpellVisualEffectName"), (kit_rows, "SpellVisualKit"),
                       (visual_rows, "SpellVisual")):
        _check_block(rows, VISUAL_BLOCK, what)

    if args.dry_run:
        for note in check_stock_ids():
            print("stock:", note)
        for row in effect_rows:
            print("SpellVisualEffectName:", row)
        for row in kit_rows:
            print("SpellVisualKit (non-zero fields):", {k: v for k, v in row.items() if v and v != 4294967295})
        for row in visual_rows:
            print("SpellVisual (non-zero fields):", {k: v for k, v in row.items() if v})
        print(build_pending_sql())
        return

    check_stock_ids()
    added = 0
    added += _merge(DBC_DIR / "SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME, effect_rows)
    added += _merge(DBC_DIR / "SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, kit_rows)
    added += _merge(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL, visual_rows)
    print(f"added {added} row(s) across the 3 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
