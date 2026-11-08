#!/usr/bin/env python3
"""
One-off DBC content patch: the client visuals the reworked Shadowfang Keep bosses need (Shadowfang Keep build WP-V;
handoff .agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.10, picks s7 #16). Same shape as
patch_deadmines_vfx_models.py (whose layout this follows) and patch_priest_vfx_models.py (the row helpers).

ID blocks (ids.yaml reservation `shadowfang_keep`):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: 90400-90449 (this script uses 90400).
- GameObjectDisplayInfo: 90030-90034 (90030 used).
- CreatureModelData / CreatureDisplayInfo: 90720-90729 (none used: the fragments, echoes and door stand-in are stock
  displays, s7 #16).

What it mints (only the two top picks that need a client patch; every look unconfirmed until seen in game):
- Fenrus FN8 shadow lightning: Ascension `purple_leishen_lightningcall_projected.m2` (patch-N; a purple bolt 13.9 x 27.6
  x 50 yd at scale 1 with a projected crack decal at the base) as SpellVisualEffectName 90400 at SHADOW_LIGHTNING_SCALE,
  the BaseEffect of ImpactKit 90400, which is the stock Lightning Cloud impact kit 318 (the sky bolt's thunder sound)
  with its model swapped (318 carries its model in BaseEffect too, so the strike anchors at the target's base).
  SV_SHADOW_LIGHTNING 90400 carries only that impact kit. Nine textures ship in SPELLS\\ (the model hard-codes
  `spells\\<name>.blp`); `firering1a` is stock and is not repacked.
- Rethilgore RG3 Cell Key: Ascension `6hu_barracks_keyring01.m2` (patch-WC2; an iron jail key ring, 0.38 x 0.58 x
  0.14 yd, lying flat) as GameObjectDisplayInfo 90030 (gameobject 301100). The model hard-codes two textures with full
  archive paths (`world\\expansion05\\doodads\\human\\doodads\\6hu_barracks_prisonextras1.blp` and
  `world\\expansion05\\doodads\\ironhorde\\nex_envmap01t.blp`), so the whole set is packed at those paths (EXTRA/).
  The gameobject template needs size CELL_KEY_SIZE (2.75): the ring is tiny.
- Everything else in the s3.10 table is stock and needs no rows: `source/npcs/shadowfang_keep/_visuals.py` names every
  stock SpellVisual / display id the boss files use (with the nine look corrections applied). `--dry-run` checks that
  they all exist in the working copy.

SpellVisual and GameObjectDisplayInfo are server-loaded, so `--sql-out PATH` emits their overlay.
SpellVisualKit and SpellVisualEffectName are client-only.

Assets (gitignored working copies; `--extract` pulls them from the read-only Ascension backup):
`SPELLS/` (the lightning model, its skin and nine textures) and `EXTRA/world/expansion05/...` (the key ring, its skin
and two textures).

Usage:
    python3 apps/dbc-tools/patch_shadowfang_keep_vfx_models.py --extract     # once: pull the Ascension assets
    python3 apps/dbc-tools/patch_shadowfang_keep_vfx_models.py --dry-run     # print rows + checks + SQL, write nothing
    python3 apps/dbc-tools/patch_shadowfang_keep_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
then build_patch_m.py (patch-M.mpq carries the DBCs, SPELLS\\ and the EXTRA tree).
"""

from __future__ import annotations

import argparse
import importlib.util
import tempfile
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, _kit_row, _merge, _row, model_path
from patch_rogue_vfx_models import ASCENSION_DATA, EXTRA_DIR, NO_ATTACHMENT, SPELLS_DIR, _extract_one

# Shadowfang Keep blocks (ids.yaml `reservations: shadowfang_keep:`).
VISUAL_BLOCK = {"start": 90400, "end": 90449}
GODI_BLOCK = {"start": 90030, "end": 90034}

# --- SpellVisualEffectName ---
EFFECT_SHADOW_LIGHTNING = 90400       # purple_leishen_lightningcall_projected.m2 (Ascension SVEN 361536), scale below

# --- SpellVisualKit ---
KIT_SHADOW_LIGHTNING = 90400          # ImpactKit: BaseEffect = the purple strike + the stock thunder sound

# --- SpellVisual ---
SV_SHADOW_LIGHTNING = 90400           # Fenrus FN8: the instant damage spell that hits the player

# --- GameObjectDisplayInfo ---
GODI_CELL_KEY = 90030                 # 6hu_barracks_keyring01.m2 -> gameobject_template 301100 Cell Key

# --- Scales and sizes (first guesses; tune in game, one number each) ---
# The bolt is 13.9 x 27.6 yd across and 50 yd tall at scale 1; the strike circle is 3 yd (6 yd across). Ascension plays
# it at 1.0; the report suggests 0.3-0.5 for 3 yd.
SHADOW_LIGHTNING_SCALE = 0.4
CELL_KEY_SIZE = 2.75                  # gameobject_template.size for 301100 (the ring is 0.38 x 0.58 yd at size 1)

# --- Stock ids reused as-is (checked by --dry-run) ---
STOCK_LIGHTNING_CLOUD_SV = 986        # Lightning Cloud 6535: ImpactKit 318 = CallLightning_Impact + thunder sound 30
STOCK_LIGHTNING_CLOUD_KIT = 318

# Vertex extents of the Ascension models (M2 header bounding box, read from the files in patch-WC2).
KEY_RING_BOX = (-0.1907, -0.2899, -0.0068, 0.1907, 0.2899, 0.1298)

MODEL_SHADOW_LIGHTNING = "purple_leishen_lightningcall_projected"
MODEL_CELL_KEY = "world\\expansion05\\doodads\\human\\doodads\\6hu_barracks_keyring01.m2"

# Ascension assets: (archive, path in the archive, destination relative to the working-copy root).
# The lightning model is flat in SPELLS/ (SPELLS\purple_leishen_lightningcall_projected.mdx) with its textures beside it
# (the M2 names them `spells\<name>.blp`); none is in the stock client (firering1a is, so it is not packed).
SPELLS_ASSETS = [
    ("patch-N", "SPELLS/purple_leishen_lightningcall_projected.m2"),
    ("patch-N", "SPELLS/purple_leishen_lightningcall_projected00.skin"),
    *[("patch-N", f"SPELLS/{name}.blp")
      for name in ("starflash_grey_bright", "glowball", "t_vfx_glow01", "purple_itk_lightning_cloud",
                   "purple_itk_lightning_geo", "purple_lightningcall_crack", "purple_lightningcall_crackflash",
                   "purple_lightningundertile", "lightningcall_blackcrack")],
]
# The key ring packs at its own archive path (lowercase), model + skin + the two textures its M2 names.
KEY_RING_DIR = "world/expansion05/doodads"
EXTRA_ASSETS = [
    ("patch-WC2", "world/EXPANSION05/DOODADS/human/doodads/6hu_barracks_keyring01.m2",
     f"{KEY_RING_DIR}/human/doodads/6hu_barracks_keyring01.m2"),
    ("patch-WC2", "world/EXPANSION05/DOODADS/human/doodads/6hu_barracks_keyring0100.skin",
     f"{KEY_RING_DIR}/human/doodads/6hu_barracks_keyring0100.skin"),
    ("patch-WC2", "world/EXPANSION05/DOODADS/human/doodads/6hu_barracks_prisonextras1.blp",
     f"{KEY_RING_DIR}/human/doodads/6hu_barracks_prisonextras1.blp"),
    ("patch-WC2", "world/EXPANSION05/DOODADS/ironhorde/nex_envmap01t.blp",
     f"{KEY_RING_DIR}/ironhorde/nex_envmap01t.blp"),
]


def _asset_paths() -> list[Path]:
    return [SPELLS_DIR / Path(p).name for _, p in SPELLS_ASSETS] + [EXTRA_DIR / dest for _, _, dest in EXTRA_ASSETS]


def build_effect_name_rows() -> list[dict]:
    # AreaEffectSize 0: the size is the fixed Scale, not the spell radius.
    return [_row(dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_SHADOW_LIGHTNING, Name="Shadow Lightning Strike (Custom)",
                 FileName=model_path(MODEL_SHADOW_LIGHTNING), AreaEffectSize=0.0, Scale=SHADOW_LIGHTNING_SCALE,
                 MinAllowedScale=0.01, MaxAllowedScale=100.0)]


def build_kit_rows(stock_kit: dict) -> list[dict]:
    """`stock_kit` is the stock kit 318 row: the strike keeps its thunder sound, the model is the purple one, in the
    same slot as 318's own model (BaseEffect)."""
    return [_kit_row(KIT_SHADOW_LIGHTNING, BaseEffect=EFFECT_SHADOW_LIGHTNING, SoundID=stock_kit["SoundID"])]


def build_spellvisual_rows() -> list[dict]:
    row = _row(dbcfmt.SPELLVISUAL, SV_SHADOW_LIGHTNING, MissileAttachment=NO_ATTACHMENT)
    row["ImpactKit"] = KIT_SHADOW_LIGHTNING
    return [row]


def build_gameobject_display_row() -> dict:
    min_x, min_y, min_z, max_x, max_y, max_z = KEY_RING_BOX
    return _row(
        dbcfmt.GAMEOBJECTDISPLAYINFO, GODI_CELL_KEY,
        ModelName=MODEL_CELL_KEY,
        GeoBoxMinX=min_x, GeoBoxMinY=min_y, GeoBoxMinZ=min_z, GeoBoxMaxX=max_x, GeoBoxMaxY=max_y, GeoBoxMaxZ=max_z,
    )


def _stock_rows(filename: str, table: dbcfmt.DbcTable, ids: set[int]) -> dict[int, dict]:
    found = {r["ID"]: r for r in dbcfile.read_dbc(DBC_DIR / filename, table) if r["ID"] in ids}
    missing = ids - set(found)
    if missing:
        raise SystemExit(f"{filename} lacks stock id(s) {sorted(missing)} in the working copy")
    return found


def _load_visuals():
    """source/npcs/shadowfang_keep/_visuals.py by path (source/ is not a package): the ids the boss files use."""
    path = Path(__file__).resolve().parent / "source" / "npcs" / "shadowfang_keep" / "_visuals.py"
    spec = importlib.util.spec_from_file_location("sfk_visuals", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stock_kit() -> dict:
    return _stock_rows("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, {STOCK_LIGHTNING_CLOUD_KIT})[
        STOCK_LIGHTNING_CLOUD_KIT]


def check_stock_ids() -> list[str]:
    """Confirms every stock id `_visuals.py` names exists in the working copy; returns a one-line note per table."""
    visuals = _load_visuals()
    _stock_rows("SpellVisual.dbc", dbcfmt.SPELLVISUAL, set(visuals.STOCK_SPELL_VISUALS) | {STOCK_LIGHTNING_CLOUD_SV})
    _stock_rows("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, set(visuals.STOCK_CREATURE_DISPLAYS))
    _stock_rows("GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO, set(visuals.STOCK_GAMEOBJECT_DISPLAYS))
    return [f"{len(set(visuals.STOCK_SPELL_VISUALS))} SpellVisual ids, {len(visuals.STOCK_CREATURE_DISPLAYS)} "
            f"CreatureDisplayInfo ids and {len(visuals.STOCK_GAMEOBJECT_DISPLAYS)} GameObjectDisplayInfo ids exist"]


def build_pending_sql() -> str:
    """Server-side overlay: SpellVisual and GameObjectDisplayInfo (the other two tables are client-only). Range-deletes
    exactly the ids this script mints, so a rerun is idempotent."""
    return "\n\n".join([
        _table_block(dbcfmt.SPELLVISUAL, {"start": SV_SHADOW_LIGHTNING, "end": SV_SHADOW_LIGHTNING},
                     build_spellvisual_rows(), []),
        _table_block(dbcfmt.GAMEOBJECTDISPLAYINFO, {"start": GODI_CELL_KEY, "end": GODI_CELL_KEY},
                     [build_gameobject_display_row()], []),
    ]) + "\n"


def _check_block(rows: list[dict], block: dict, what: str) -> None:
    for row in rows:
        if not block["start"] <= row["ID"] <= block["end"]:
            raise SystemExit(f"{what} id {row['ID']} is outside the shadowfang_keep block {block}")


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
        for archive, path, dest_rel in EXTRA_ASSETS:
            dest = EXTRA_DIR / dest_rel
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
    kit_rows = build_kit_rows(_stock_kit())
    visual_rows = build_spellvisual_rows()
    for rows, what in ((effect_rows, "SpellVisualEffectName"), (kit_rows, "SpellVisualKit"),
                       (visual_rows, "SpellVisual")):
        _check_block(rows, VISUAL_BLOCK, what)
    _check_block([build_gameobject_display_row()], GODI_BLOCK, "GameObjectDisplayInfo")

    if args.dry_run:
        for note in check_stock_ids():
            print("stock:", note)
        for row in effect_rows:
            print("SpellVisualEffectName:", row)
        for row in kit_rows:
            print("SpellVisualKit (non-zero fields):", {k: v for k, v in row.items() if v and v != 4294967295})
        for row in visual_rows:
            print("SpellVisual (non-zero fields):", {k: v for k, v in row.items() if v})
        print("GameObjectDisplayInfo:", build_gameobject_display_row())
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
    added += _merge(DBC_DIR / "GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO,
                    [build_gameobject_display_row()])
    print(f"added {added} row(s) across the 4 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
