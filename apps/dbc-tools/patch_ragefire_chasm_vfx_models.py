#!/usr/bin/env python3
"""
One-off DBC content patch: the client visuals the reworked Ragefire Chasm bosses need (Ragefire Chasm build, WP V;
handoff .agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.10 and s7 #37, picks VISUALS-REPORT.md
"Part 2: new rows"). Same shape as patch_scarlet_monastery_vfx_models.py (whose row helpers and asset extraction it
shares).

ID blocks (ids.yaml reservation `ragefire_chasm`):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: 90370-90399 (one number for SpellVisual and Kit; the effect-name
  ids are the same numbers plus 90377 / 90378 for the second effect of a kit). Used: 90370, 90371, 90373-90376
  (SpellVisual and Kit) and 90370, 90371, 90377, 90378 (EffectName). **90372 is deliberately not shipped** (the
  Ascension blood lake, s7 #37: the red aura SV 90554 plays instead).
- CreatureModelData / CreatureDisplayInfo / GameObjectDisplayInfo: none minted (VR reserves 90830-90839 / 90070-90074,
  nothing is needed).

What it mints (every look unconfirmed until seen in game; scales are first guesses, one number each):
- 90370 Taragaman's Felstorm: a StateKit with AnimID 126 (the Felguard owns it), BaseEffect = the Ascension
  `cfx_warrior_bladestorm_statebase` (6 steel-blue ribbons) and ChestEffect = the Ascension
  `7fx_argus_felstorm_felinfused_statebase` (a green fel-fire wreath). VR put both on Base; the kit has one Base slot,
  so the wreath rides the chest. Both models are particle-only (size unmeasured, tune the scale in game); the ring
  marker carries the 8 / 10 yd radius. Fallback: stock SV 6044.
- 90371 the fel spot eruption (and fel pulse if wanted): an ImpactKit with the stock `fel_firenova_area` (Base) and
  `fel_hellfire_impact_base` (Chest) at scale 1.0 each, sound 4100 / 4274 as the stock rows. Fallback SV 9004.
- 90373-90376 Bazzalan's missing swings: copies of the stock SpellVisual 671 (Eviscerate), 250 (Rupture), 8144 (Envenom)
  and 12317 (Fan of Knives) whose cast kit (733 / 394 / 6964 / 11409) is copied too with the AnimID the Satyr model
  lacks swapped for one it has: 57 -> 17 (Eviscerate, Rupture, Envenom), 126 -> 54 (Fan). Everything else (hand
  effects, impact kits, sounds, missile) is the stock row's.

SpellVisual is server-loaded, so `--sql-out PATH` emits its overlay (SpellVisualKit and SpellVisualEffectName are
client-only). No creature or gameobject display is minted, so no creature_model_info row is needed.

Assets (gitignored working copies; `--extract` pulls them from the read-only Ascension backup (patch-N) into
var/model-visual-dbc/SPELLS/, where build_patch_m.py packs them into patch-M): two models, their skins and the 10
textures they hard-code that the working copy does not have yet (smoke_puffy_mask_verysoft and arcane_wisps_desat are
already shipped). If an Ascension file is missing in the backup, --extract stops with the file name; the stock fallback
SV 6044 keeps working and the boss files can wire it with one constant (`TG_FELSTORM_FALLBACK`).

Usage:
    cd apps/dbc-tools
    python3 patch_ragefire_chasm_vfx_models.py --extract     # once: pull the Ascension assets
    python3 patch_ragefire_chasm_vfx_models.py --dry-run     # print rows + checks + SQL, write nothing
    python3 patch_ragefire_chasm_vfx_models.py --sql-out ../../data/sql/updates/pending_db_world/rev_<ts>.sql
then build_patch_m.py (patch-M.mpq carries the DBCs and SPELLS\\). The orchestrator runs the last two at deploy.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import tempfile
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, _kit_row, _merge, _row, model_path
from patch_rogue_vfx_models import ASCENSION_DATA, SPELLS_DIR, _extract_one

# Ragefire Chasm block (ids.yaml `reservations: ragefire_chasm:`).
VISUAL_BLOCK = {"start": 90370, "end": 90399}

# --- SpellVisual = SpellVisualKit ids ---
SV_FELSTORM = 90370
SV_FEL_SPOT = 90371
SV_EVISCERATE = 90373
SV_RUPTURE = 90374
SV_ENVENOM = 90375
SV_FAN_OF_KNIVES = 90376

# --- SpellVisualEffectName ids (the second effect of a kit takes a spare number, never 90372) ---
EN_FELSTORM_BLADES = 90370
EN_FEL_SPOT_NOVA = 90371
EN_FELSTORM_WREATH = 90377
EN_FEL_SPOT_HELLFIRE = 90378

# --- Scales (first guesses; tune in game, one number each) ---
FELSTORM_BLADES_SCALE = 1.0
FELSTORM_WREATH_SCALE = 1.0
FEL_SPOT_NOVA_SCALE = 1.0
FEL_SPOT_HELLFIRE_SCALE = 1.0
FELSTORM_ANIM = 126                    # the Felguard owns it; the storm kit keeps the stock animation

# Stock sounds of the fel spot rows (SV 9004 / stock fel nova kit 7356)
FEL_SPOT_SOUND = 4274

# (new SV = kit id, stock SpellVisual it copies, kit field, AnimID in the stock kit, AnimID the Satyr has)
SWING_COPIES = (
    (SV_EVISCERATE, 671, "CastKit", 57, 17),
    (SV_RUPTURE, 250, "CastKit", 57, 17),
    (SV_ENVENOM, 8144, "CastKit", 57, 17),
    (SV_FAN_OF_KNIVES, 12317, "CastKit", 126, 54),
)

# --- Stock models the fel spot row reuses (verified by --dry-run to be named by a stock SpellVisualEffectName row) ---
STOCK_FEL_NOVA_FILE = "spells\\fel_firenova_area.mdx"             # stock SVEN 3298
STOCK_FEL_HELLFIRE_FILE = "spells\\fel_hellfire_impact_base.mdx"  # stock SVEN 3411
STOCK_EFFECT_FILES = (STOCK_FEL_NOVA_FILE, STOCK_FEL_HELLFIRE_FILE)

MODEL_BLADES = "cfx_warrior_bladestorm_statebase"
MODEL_WREATH = "7fx_argus_felstorm_felinfused_statebase"
# Textures the two M2s name (`spells\\<name>.blp`, read from the models); all asc-N except the two already shipped.
BLADES_TEXTURES = ("arc_center_wispy_tri_lowfreq", "dirt_scroll_wispy", "ribbonne1_dirt",
                   "warrior_bladestorm_circle", "warrior_bladestorm_secondaryribbon")
WREATH_TEXTURES = ("7fx_alphamask_shockwavesoft2", "fel_barrier_distorted_alt_ba", "fel_firewreath_01",
                   "fel_firewreath_02", "fire_fel_mod2x_streak_a_lessbright")
ALREADY_SHIPPED_TEXTURES = ("smoke_puffy_mask_verysoft", "arcane_wisps_desat")
SPELLS_ASSETS = [
    ("patch-N", f"SPELLS/{MODEL_BLADES}.m2"),
    ("patch-N", f"SPELLS/{MODEL_BLADES}00.skin"),
    ("patch-N", f"SPELLS/{MODEL_WREATH}.m2"),
    ("patch-N", f"SPELLS/{MODEL_WREATH}00.skin"),
    *[("patch-N", f"SPELLS/{name}.blp") for name in (*BLADES_TEXTURES, *WREATH_TEXTURES)],
]


def _asset_paths() -> list[Path]:
    return [SPELLS_DIR / Path(p).name for _, p in SPELLS_ASSETS]


def _effect_rows() -> list[tuple[int, str, str, float]]:
    """(id, name, FileName, scale) of every effect; AreaEffectSize 0 on all of them (a fixed size, not the radius)."""
    return [
        (EN_FELSTORM_BLADES, "Felstorm Blades", model_path(MODEL_BLADES), FELSTORM_BLADES_SCALE),
        (EN_FEL_SPOT_NOVA, "Fel Spot Nova", STOCK_FEL_NOVA_FILE, FEL_SPOT_NOVA_SCALE),
        (EN_FELSTORM_WREATH, "Felstorm Fel Wreath", model_path(MODEL_WREATH), FELSTORM_WREATH_SCALE),
        (EN_FEL_SPOT_HELLFIRE, "Fel Spot Hellfire", STOCK_FEL_HELLFIRE_FILE, FEL_SPOT_HELLFIRE_SCALE),
    ]


def build_effect_name_rows() -> list[dict]:
    return [_row(dbcfmt.SPELLVISUALEFFECTNAME, id_, Name=f"{name} (Custom)", FileName=file_name,
                 AreaEffectSize=0.0, Scale=scale, MinAllowedScale=0.01, MaxAllowedScale=100.0)
            for id_, name, file_name, scale in _effect_rows()]


def _stock(filename: str, table: dbcfmt.DbcTable, ids: set[int]) -> dict[int, dict]:
    found = {r["ID"]: r for r in dbcfile.read_dbc(DBC_DIR / filename, table) if r["ID"] in ids}
    missing = ids - set(found)
    if missing:
        raise SystemExit(f"{filename} lacks stock id(s) {sorted(missing)} in the working copy")
    return found


def build_kit_rows() -> list[dict]:
    """The Felstorm state kit, the fel spot impact kit and the four swing cast-kit copies (AnimID swapped)."""
    rows = [
        _kit_row(SV_FELSTORM, AnimID=FELSTORM_ANIM, BaseEffect=EN_FELSTORM_BLADES, ChestEffect=EN_FELSTORM_WREATH,
                 SoundID=4354),
        _kit_row(SV_FEL_SPOT, BaseEffect=EN_FEL_SPOT_NOVA, ChestEffect=EN_FEL_SPOT_HELLFIRE, SoundID=FEL_SPOT_SOUND),
    ]
    stock_visuals = _stock("SpellVisual.dbc", dbcfmt.SPELLVISUAL, {src for _, src, _, _, _ in SWING_COPIES})
    kit_ids = {stock_visuals[src][field] for _, src, field, _, _ in SWING_COPIES}
    stock_kits = _stock("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, kit_ids)
    for new_id, src, field, old_anim, new_anim in SWING_COPIES:
        kit = dict(stock_kits[stock_visuals[src][field]])
        if kit["AnimID"] != old_anim:
            raise SystemExit(f"stock kit {kit['ID']} of SV {src} has AnimID {kit['AnimID']}, expected {old_anim}")
        kit["ID"] = new_id
        kit["AnimID"] = new_anim
        rows.append(kit)
    return rows


def build_spellvisual_rows() -> list[dict]:
    row = _row(dbcfmt.SPELLVISUAL, SV_FELSTORM, MissileAttachment=-1)
    row["StateKit"] = SV_FELSTORM
    spot = _row(dbcfmt.SPELLVISUAL, SV_FEL_SPOT, MissileAttachment=-1)
    spot["ImpactKit"] = SV_FEL_SPOT
    rows = [row, spot]
    stock_visuals = _stock("SpellVisual.dbc", dbcfmt.SPELLVISUAL, {src for _, src, _, _, _ in SWING_COPIES})
    for new_id, src, field, _, _ in SWING_COPIES:
        copy = dict(stock_visuals[src])
        copy["ID"] = new_id
        copy[field] = new_id
        rows.append(copy)
    return rows


def _load_visuals():
    """source/npcs/ragefire_chasm/_visuals.py by path (source/ is not a package): the ids the boss files use."""
    path = Path(__file__).resolve().parent / "source" / "npcs" / "ragefire_chasm" / "_visuals.py"
    spec = importlib.util.spec_from_file_location("ragefire_chasm_visuals", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_stock_ids() -> list[str]:
    """Confirms every stock or shipped id `_visuals.py` names (and the stock models the rows reuse) exists in the
    working copy; returns a one-line note."""
    visuals = _load_visuals()
    _stock("SpellVisual.dbc", dbcfmt.SPELLVISUAL, set(visuals.STOCK_SPELL_VISUALS) | set(visuals.SHIPPED_SPELL_VISUALS))
    used = {r["FileName"].lower() for r in dbcfile.read_dbc(DBC_DIR / "SpellVisualEffectName.dbc",
                                                            dbcfmt.SPELLVISUALEFFECTNAME) if r["ID"] < 90000}
    for file_name in STOCK_EFFECT_FILES:
        if file_name.lower() not in used:
            raise SystemExit(f"no stock SpellVisualEffectName names the model {file_name}")
    _stock("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, set(visuals.STOCK_CREATURE_DISPLAYS))
    _stock("GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO, set(visuals.STOCK_GAMEOBJECT_DISPLAYS))
    return [f"{len(set(visuals.STOCK_SPELL_VISUALS))} stock + {len(set(visuals.SHIPPED_SPELL_VISUALS))} shipped "
            f"SpellVisual ids, {len(visuals.STOCK_CREATURE_DISPLAYS)} CreatureDisplayInfo ids and "
            f"{len(visuals.STOCK_GAMEOBJECT_DISPLAYS)} GameObjectDisplayInfo ids exist (plus the "
            f"{len(STOCK_EFFECT_FILES)} stock effect models the fel spot row reuses)"]


def _same_row(a: dict, b: dict) -> bool:
    """The rows are equal, with floats compared as the DBC stores them (float32: 0.01 reads back as 0.00999...)."""
    return a.keys() == b.keys() and all(
        math.isclose(a[k], b[k], rel_tol=1e-6, abs_tol=1e-7) if isinstance(a[k], float) else a[k] == b[k] for k in a)


def check_no_collisions() -> None:
    """The ids this script mints must be free in the working copy or already equal to its own rows (a merge replaces
    rows silently, so a foreign row in the block would be lost)."""
    for filename, table, builder in (
            ("SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME, build_effect_name_rows),
            ("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, build_kit_rows),
            ("SpellVisual.dbc", dbcfmt.SPELLVISUAL, build_spellvisual_rows)):
        mine = {r["ID"]: r for r in builder()}
        for row in dbcfile.read_dbc(DBC_DIR / filename, table):
            if row["ID"] in mine and not _same_row(row, mine[row["ID"]]):
                raise SystemExit(f"{filename}: id {row['ID']} already holds a different row")
            if VISUAL_BLOCK["start"] <= row["ID"] <= VISUAL_BLOCK["end"] and row["ID"] not in mine:
                raise SystemExit(f"{filename}: foreign row {row['ID']} inside the ragefire_chasm block")


def build_pending_sql() -> str:
    """Server-side overlay: SpellVisual only (Kit and EffectName are client-only). Range-deletes exactly the ids this
    script spans, so a rerun is idempotent (90372 is inside the span and absent everywhere: nothing to delete)."""
    rows = build_spellvisual_rows()
    ids = [r["ID"] for r in rows]
    # The DBC holds signed columns (MissileAttachment -1) as unsigned; the server column is a signed int.
    rows = [{k: (v - (1 << 32) if isinstance(v, int) and v >= 1 << 31 else v) for k, v in r.items()} for r in rows]
    return _table_block(dbcfmt.SPELLVISUAL, {"start": min(ids), "end": max(ids)}, rows, []) + "\n"


def _check_block(rows: list[dict], block: dict, what: str) -> None:
    for row in rows:
        if not block["start"] <= row["ID"] <= block["end"]:
            raise SystemExit(f"{what} id {row['ID']} is outside the ragefire_chasm block {block}")


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
        check_no_collisions()
        print("no foreign row in the minted id block of the working copy")
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
    check_no_collisions()
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
