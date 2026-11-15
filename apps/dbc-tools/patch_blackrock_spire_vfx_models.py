#!/usr/bin/env python3
"""
One-off DBC content patch: the client visuals the reworked Blackrock Spire bosses need (Blackrock Spire build, WP V-1
for wave 1, the Lower Spire; V-2 appends wave 2; handoff .agents/plans/blackrock-spire-build/
blackrock-spire-build.HANDOFF.md s3.10, picks s7 #27). Same shape as patch_stratholme_vfx_models.py and
patch_shadowfang_keep_vfx_models.py (whose row helpers and asset extraction it shares).

ID blocks (ids.yaml reservation `blackrock_spire`):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: 90600-90649 (wave 1 uses 90600-90602).
- GameObjectDisplayInfo 90040-90049 and CreatureModelData / CreatureDisplayInfo 90740-90769: none minted by wave 1
  (the war horn is stock GODI 7352 and the Bloodaxe rider is stock display 9602 on a stock mount); V-2 may use them.

What wave 1 mints (every look unconfirmed until seen in game):
- Wyrmthalak WT16 Shadowflame Spit patch: Ascension `mannoroth_gooflowshadow_state_projected.m2` (patch-N; a 17.8 yd
  square purple ground quad, `defile1` + `creepingmoss_shadow_radial_blendadd` + `radial_wave_purple_blendadd`) as
  SpellVisualEffectName 90600 at SPIT_PATCH_SCALE (AreaEffectSize 0, a fixed size) for a 4 yd radius patch. An AREA look
  (PersistentAreaKit WorldEffect, for an area aura's dynamic object) and a STATE look (StateKit BaseEffect, one
  stalker per patch), the Deadmines goo layout.
- Wyrmthalak HM war horn blown: Ascension `ogre_warhorn_impact_base.m2` (patch-N; orange shock rays, particles) as
  SpellVisualEffectName 90601, the ChestEffect of an impact kit, on a SpellVisual that keeps the stock Horn of
  Elemental Fury's cast kit 3469 (sound 6423, anim 81). Cast it from a stalker at the horn.
- Everything else in the s3.10 wave 1 rows is stock or shipped and needs no rows:
  `source/npcs/blackrock_spire/_visuals.py` names every id the boss files use (with the look corrections applied).
  `--dry-run` checks that they all exist in the working copy.

SpellVisual is server-loaded, so `--sql-out PATH` emits its overlay (SpellVisualKit and SpellVisualEffectName are
client-only).

Assets (gitignored working copies; `--extract` pulls them from the read-only Ascension backup): `SPELLS/` gets the
two models, their skins and the six textures they hard-code that stock does not ship (`t_vfx_hero_explosion_blur` is
stock and is not repacked).

Usage:
    python3 apps/dbc-tools/patch_blackrock_spire_vfx_models.py --extract     # once: pull the Ascension assets
    python3 apps/dbc-tools/patch_blackrock_spire_vfx_models.py --dry-run     # print rows + checks + SQL, write nothing
    python3 apps/dbc-tools/patch_blackrock_spire_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
then build_patch_m.py (patch-M.mpq carries the DBCs and SPELLS\\).
"""

from __future__ import annotations

import argparse
import importlib.util
import tempfile
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, _kit_row, _merge, _row, model_path
from patch_rogue_vfx_models import ASCENSION_DATA, NO_ATTACHMENT, SPELLS_DIR, _extract_one

# Blackrock Spire blocks (ids.yaml `reservations: blackrock_spire:`).
VISUAL_BLOCK = {"start": 90600, "end": 90649}
GODI_BLOCK = {"start": 90040, "end": 90049}
CREATURE_DISPLAY_BLOCK = {"start": 90740, "end": 90769}

# --- SpellVisualEffectName ---
EFFECT_SPIT_PATCH = 90600             # mannoroth_gooflowshadow_state_projected at SPIT_PATCH_SCALE
EFFECT_WARHORN_BURST = 90601          # ogre_warhorn_impact_base at WARHORN_BURST_SCALE

# --- SpellVisualKit ---
KIT_SPIT_PATCH_AREA = 90600           # PersistentAreaKit WorldEffect
KIT_SPIT_PATCH_STATE = 90601          # StateKit BaseEffect
KIT_HORN_BURST = 90602                # impact kit: ChestEffect = the shock-ray burst

# --- SpellVisual (same ids as _visuals.py) ---
SV_SPIT_PATCH_AREA = 90600
SV_SPIT_PATCH_STATE = 90601
SV_HORN_BLOWN = 90602

# --- Scales (first guesses; tune in game, one number each) ---
SPIT_PATCH_YARDS = 17.8               # the quad at scale 1 (VISUALS-REPORT, gap 15; mesh bounds 17.8 x 17.8 x 0.1)
SPIT_PATCH_SCALE = 0.5                # 8.9 yd across for the 4 yd radius spit (WT16); the visible disc is a guess
WARHORN_BURST_SCALE = 1.0             # particles (0.2 yd mesh): no size to derive, tune in game

# --- Stock ids reused as-is (checked by --dry-run) ---
STOCK_HORN_CAST_SV = 4079             # Horn of Elemental Fury 56893: CastKit 3469, MissileDestinationAttachment 1
STOCK_HORN_CAST_KIT = 3469            # AnimID 81 + SoundID 6423
STOCK_HORN_SOUND = 6423

MODEL_SPIT_PATCH = "mannoroth_gooflowshadow_state_projected"
MODEL_WARHORN_BURST = "ogre_warhorn_impact_base"

# Ascension assets, all in patch-N: (archive, path in the archive). The M2s name their textures `spells\<name>.blp`;
# none of these six is in the stock client (`t_vfx_hero_explosion_blur` is, so it is not packed).
SPELLS_ASSETS = [
    ("patch-N", f"SPELLS/{MODEL_SPIT_PATCH}.m2"),
    ("patch-N", f"SPELLS/{MODEL_SPIT_PATCH}00.skin"),
    ("patch-N", f"SPELLS/{MODEL_WARHORN_BURST}.m2"),
    ("patch-N", f"SPELLS/{MODEL_WARHORN_BURST}00.skin"),
    *[("patch-N", f"SPELLS/{name}.blp")
      for name in ("creepingmoss_shadow_radial_blendadd", "radial_wave_purple_blendadd", "defile1",
                   "shockwave_rays", "glowballsmoothfade_orange", "streakst2")],
]


def _asset_paths() -> list[Path]:
    return [SPELLS_DIR / Path(p).name for _, p in SPELLS_ASSETS]


def build_effect_name_rows() -> list[dict]:
    def effect(id_, name, model, scale):
        # AreaEffectSize 0: the size is the fixed Scale, not the spell radius.
        return _row(dbcfmt.SPELLVISUALEFFECTNAME, id_, Name=f"{name} (Custom)", FileName=model_path(model),
                    AreaEffectSize=0.0, Scale=scale, MinAllowedScale=0.01, MaxAllowedScale=100.0)

    return [
        effect(EFFECT_SPIT_PATCH, "Shadowflame Spit Patch 4 yd", MODEL_SPIT_PATCH, SPIT_PATCH_SCALE),
        effect(EFFECT_WARHORN_BURST, "War Horn Burst", MODEL_WARHORN_BURST, WARHORN_BURST_SCALE),
    ]


def build_kit_rows() -> list[dict]:
    return [
        _kit_row(KIT_SPIT_PATCH_AREA, WorldEffect=EFFECT_SPIT_PATCH),
        _kit_row(KIT_SPIT_PATCH_STATE, BaseEffect=EFFECT_SPIT_PATCH),
        _kit_row(KIT_HORN_BURST, ChestEffect=EFFECT_WARHORN_BURST),
    ]


def build_spellvisual_rows() -> list[dict]:
    def visual(id_, **fields):
        row = _row(dbcfmt.SPELLVISUAL, id_, MissileAttachment=NO_ATTACHMENT)
        row.update(fields)
        return row

    return [
        visual(SV_SPIT_PATCH_AREA, PersistentAreaKit=KIT_SPIT_PATCH_AREA),
        visual(SV_SPIT_PATCH_STATE, StateKit=KIT_SPIT_PATCH_STATE),
        # The stock horn cast (sound + anim) with the burst on the caster; no missile (a stalker casts it on itself).
        visual(SV_HORN_BLOWN, CastKit=STOCK_HORN_CAST_KIT, ImpactKit=KIT_HORN_BURST, MissileDestinationAttachment=1),
    ]


def _stock_rows(filename: str, table: dbcfmt.DbcTable, ids: set[int]) -> dict[int, dict]:
    found = {r["ID"]: r for r in dbcfile.read_dbc(DBC_DIR / filename, table) if r["ID"] in ids}
    missing = ids - set(found)
    if missing:
        raise SystemExit(f"{filename} lacks stock id(s) {sorted(missing)} in the working copy")
    return found


def _load_visuals():
    """source/npcs/blackrock_spire/_visuals.py by path (source/ is not a package): the ids the boss files use."""
    path = Path(__file__).resolve().parent / "source" / "npcs" / "blackrock_spire" / "_visuals.py"
    spec = importlib.util.spec_from_file_location("blackrock_spire_visuals", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_stock_ids() -> list[str]:
    """Confirms every stock or shipped id `_visuals.py` names (and the horn cast the rows reuse) exists in the working
    copy; returns a one-line note."""
    visuals = _load_visuals()
    _stock_rows("SpellVisual.dbc", dbcfmt.SPELLVISUAL,
                set(visuals.STOCK_SPELL_VISUALS) | set(visuals.MINTED_ELSEWHERE_SPELL_VISUALS) | {STOCK_HORN_CAST_SV})
    _stock_rows("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, {STOCK_HORN_CAST_KIT})
    _stock_rows("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO,
                set(visuals.STOCK_CREATURE_DISPLAYS) | set(visuals.SHIPPED_CREATURE_DISPLAYS))
    _stock_rows("GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO, set(visuals.STOCK_GAMEOBJECT_DISPLAYS))
    _stock_rows("SoundEntries.dbc", dbcfmt.SOUNDENTRIES, set(visuals.STOCK_SOUND_ENTRIES))
    return [f"{len(set(visuals.STOCK_SPELL_VISUALS))} SpellVisual ids, {len(visuals.STOCK_CREATURE_DISPLAYS)} "
            f"CreatureDisplayInfo ids (+{len(visuals.SHIPPED_CREATURE_DISPLAYS)} shipped telegraph displays), "
            f"{len(visuals.STOCK_GAMEOBJECT_DISPLAYS)} GameObjectDisplayInfo ids and "
            f"{len(visuals.STOCK_SOUND_ENTRIES)} SoundEntries ids exist"]


def build_pending_sql() -> str:
    """Server-side overlay: SpellVisual only (the other tables are client-only or unused by wave 1). Range-deletes
    exactly the ids this script mints, so a rerun is idempotent."""
    rows = build_spellvisual_rows()
    ids = [r["ID"] for r in rows]
    return _table_block(dbcfmt.SPELLVISUAL, {"start": min(ids), "end": max(ids)}, rows, []) + "\n"


def _check_block(rows: list[dict], block: dict, what: str) -> None:
    for row in rows:
        if not block["start"] <= row["ID"] <= block["end"]:
            raise SystemExit(f"{what} id {row['ID']} is outside the blackrock_spire block {block}")


def extract_assets() -> None:
    """Pulls the Ascension assets (read-only backup) into the working copy; files already present are kept."""
    added = 0
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        for archive, path in SPELLS_ASSETS:
            dest = SPELLS_DIR / Path(path).name
            if not dest.is_file():
                _extract_one(archive, path, dest, workdir)
                added += 1
    print(f"extracted {added} asset(s) from {ASCENSION_DATA} (0 means everything was already there)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sql-out", type=Path, default=None,
                        help="Write the matching server-side SQL migration to this path (see module docstring).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the rows, the stock-id and asset checks and the SQL; write nothing.")
    parser.add_argument("--extract", action="store_true",
                        help="Pull the missing assets from the Ascension backup into the working copy, then stop.")
    args = parser.parse_args()

    if args.extract:
        extract_assets()
        return

    missing = [str(p) for p in _asset_paths() if not p.is_file()]
    if missing and not args.dry_run:
        raise SystemExit(f"missing assets: {missing} - run with --extract first (see docstring)")

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
        print("assets packed by build_patch_m.py (MISSING = run --extract):")
        for path in _asset_paths():
            print(f"  {path.relative_to(DBC_DIR.parent)} ({path.stat().st_size} bytes)" if path.is_file()
                  else f"  {path.relative_to(DBC_DIR.parent)} MISSING")
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
