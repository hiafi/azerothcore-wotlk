#!/usr/bin/env python3
"""
One-off DBC content patch: the client visuals the reworked Deadmines bosses need (Deadmines Pilot WP-V; handoff
.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.10 gaps 2, 3a, 3b, 4 and 6, picks s7 #9). Same shape as
patch_rogue_vfx_models.py (whose asset helpers and constants this reuses) and patch_priest_vfx_models.py (the row
helpers).

ID blocks (ids.yaml reservation `deadmines`):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: 90340-90369 (this script uses 90340-90344).
- GameObjectDisplayInfo: 90020-90029 (90020 used).
- CreatureModelData / CreatureDisplayInfo: 90700-90719 (90700 used).

What it mints (every look unconfirmed until seen in game; the scales are first guesses):
- 3a Hot shot molten trail: stock `spells\\goo_flow_stateyellow.m2` (an orange slag pool, 47.8 yd across at scale 1,
  anims stand + 158 spawn + 159 despawn) as SpellVisualEffectName 90340 at scale HOT_SHOT_SCALE (4 yd / 47.8 yd =
  0.084, one 4 yd lane segment). Two SpellVisuals, because the segment can be cast two ways: SV_HOT_SHOT_AREA 90340
  (PersistentAreaKit 90340, WorldEffect: a spell with a persistent area aura / dynamic object effect) and
  SV_HOT_SHOT_STATE 90341 (StateKit 90341, BaseEffect: an aura on a stalker standing at the segment). A StateKit also
  plays on every unit that carries the aura, so never put SV_HOT_SHOT_STATE on a spell that hits players.
- 4 Fish Stew puddle: stock `spells\\goo_flow_state.m2` (the green pool, same model family) as SpellVisualEffectName
  90341 at STEW_SCALE (a 4 yd radius puddle = 8 yd across: 8 / 47.8 = 0.167). SV_STEW_AREA 90342 and SV_STEW_STATE
  90343, the same two shapes as the Hot shot pair.
- 2 Splinter Spray: Ascension `spells\\hitimpacts\\ifx_element_wood_hit.m2` (particles only: wood chips, a smoke puff,
  a gold hit streak; patch-N.MPQ) as SpellVisualEffectName 90342 on the target's ChestEffect, scale 2.0 (a weapon-hit
  effect is small). SV_SPLINTER_SPRAY 90344 is Steam Blast's SpellVisual 11064 (the cone: PrecastKit 10205 hands, the
  steam at each target) with its ImpactKit swapped for KIT_SPLINTER_IMPACT 90344 = Steam Blast's impact kit 7387
  (WorldEffect 3725 + sound 11807) plus the wood chips on the chest. The model keeps its textures at
  `spells\\hitimpacts\\*.blp` (a texture path inside the M2), so the six textures are packed at that full path
  (EXTRA/SPELLS/hitimpacts/), the model and skin flat in SPELLS/.
- 3b Iron shot: stock `creature\\demolishercannonball\\demolishercannonball.m2` (a 1.7 yd dark iron ball, stock
  texture) as CreatureModelData 90700 + CreatureDisplayInfo 90700 (scale 1.0; the creature template's own scale
  resizes it). The server also needs a creature_model_info row for the display (ObjectMgr logs "No model data" without
  one), so the SQL overlay writes it.
- 6 Falling mainmast: stock `World\\Expansion02\\Doodads\\DaggerCap\\BurningShip\\HF_BurningShip_Mast.M2` (a burning
  ship mast, 6.0 x 6.9 x 19.2 yd, upright, no fall animation) as GameObjectDisplayInfo 90020. The model's vertices run
  z -9.6..+9.6 around its origin, so a mast spawned lying (pitched 90 degrees) is centred on the spawn point.
- 1a Pocketed, 1b Gold Fever, 5 Harpoon rope: stock, no rows. Pocketed = SpellVisual 12528 (Treasure Sparkle), Gold
  Fever = SpellVisual 47 (Unholy Frenzy; optional gold tint SV 11903), rope = stock GameObjectDisplayInfo 7538.
  `--dry-run` checks that those stock ids exist.

SpellVisual, CreatureModelData, CreatureDisplayInfo and GameObjectDisplayInfo are server-loaded, so `--sql-out PATH`
emits their overlay (plus the creature_model_info row). SpellVisualKit and SpellVisualEffectName are client-only.

Assets (gitignored working copies; `--extract` pulls the Ascension ones from the backup, read-only):
`SPELLS/ifx_element_wood_hit.m2` + `...00.skin`, and `EXTRA/SPELLS/hitimpacts/` with the six textures. The stock models
ship nothing.

Usage:
    python3 apps/dbc-tools/patch_deadmines_vfx_models.py --extract     # once: pull the wood-chip assets
    python3 apps/dbc-tools/patch_deadmines_vfx_models.py --dry-run     # print rows + checks + SQL, write nothing
    python3 apps/dbc-tools/patch_deadmines_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
then build_patch_m.py (patch-M.mpq carries the DBCs, SPELLS\\ and the EXTRA tree).
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, _kit_row, _merge, _row, go_model_path, model_path
from patch_rogue_vfx_models import ASCENSION_DATA, EXTRA_DIR, NO_ATTACHMENT, SPELLS_DIR, _extract_one

# Deadmines blocks (ids.yaml `reservations: deadmines:`).
VISUAL_BLOCK = {"start": 90340, "end": 90369}
GODI_BLOCK = {"start": 90020, "end": 90029}
CREATURE_DISPLAY_BLOCK = {"start": 90700, "end": 90719}

# --- SpellVisualEffectName ---
EFFECT_HOT_SHOT_SLAG = 90340          # goo_flow_stateyellow.m2, scale HOT_SHOT_SCALE
EFFECT_STEW_PUDDLE = 90341            # goo_flow_state.m2, scale STEW_SCALE
EFFECT_SPLINTER_CHIPS = 90342         # ifx_element_wood_hit.m2 (Ascension SVEN 50120), scale 2.0

# --- SpellVisualKit ---
KIT_HOT_SHOT_AREA = 90340             # PersistentAreaKit: WorldEffect
KIT_HOT_SHOT_STATE = 90341            # StateKit: BaseEffect
KIT_STEW_AREA = 90342
KIT_STEW_STATE = 90343
KIT_SPLINTER_IMPACT = 90344           # Steam Blast impact kit 7387 + the wood chips on the chest

# --- SpellVisual ---
SV_HOT_SHOT_AREA = 90340              # a persistent area aura / dynamic object spell (the trail segment)
SV_HOT_SHOT_STATE = 90341             # an aura on a stalker at the segment
SV_STEW_AREA = 90342                  # the Fish Stew puddle as a persistent area aura
SV_STEW_STATE = 90343                 # the Fish Stew puddle as an aura on a stalker
SV_SPLINTER_SPRAY = 90344             # Splinter Spray: Steam Blast 11064 with the wood-chip impact

# --- GameObjectDisplayInfo / CreatureModelData + CreatureDisplayInfo ---
GODI_MAINMAST = 90020                 # HF_BurningShip_Mast.M2 -> gameobject_template 301002 Burning Mainmast
CDI_IRON_SHOT = 90700                 # CreatureModelData 90700 + CreatureDisplayInfo 90700 -> creature 300423

# --- Scales (a model is 47.8 yd across at scale 1; tune in game, one number each) ---
GOO_MODEL_YARDS = 47.82
HOT_SHOT_SEGMENT_YARDS = 4.0          # one lane segment (the lane is 4 yd wide)
STEW_PUDDLE_YARDS = 8.0               # a Circle(4) puddle: radius 4 yd
HOT_SHOT_SCALE = round(HOT_SHOT_SEGMENT_YARDS / GOO_MODEL_YARDS, 3)   # 0.084
STEW_SCALE = round(STEW_PUDDLE_YARDS / GOO_MODEL_YARDS, 3)            # 0.167
SPLINTER_CHIPS_SCALE = 2.0

# --- Stock ids reused as-is (checked by --dry-run) ---
STOCK_STEAM_BLAST_SV = 11064          # Steam Blast 50375: PrecastKit 10205, ImpactKit 7387
STOCK_STEAM_IMPACT_KIT = 7387         # WorldEffect 3725 + sound 11807
STOCK_POCKETED_SV = 12528             # Treasure Sparkle 58042 (gap 1a)
STOCK_GOLD_FEVER_SV = 47              # Unholy Frenzy 8699 / Frenzy 32964 (gap 1b)
STOCK_GOLD_TINT_SV = 11903            # AuraYellow, optional gold tint for Gold Fever
STOCK_ROPE_GODI = 7538                # CaveKoboldRopeCoil (gap 5; Rope Pile 186905 is a stock type 10)

MODEL_HOT_SHOT = "goo_flow_stateyellow"
MODEL_STEW = "goo_flow_state"
MODEL_SPLINTER = "ifx_element_wood_hit"
MODEL_IRON_SHOT = "Creature\\DemolisherCannonball\\DemolisherCannonball.mdx"
MODEL_MAINMAST = "World\\Expansion02\\Doodads\\DaggerCap\\BurningShip\\HF_BurningShip_Mast.M2"

# Ascension assets: (archive, path in the archive). The model is flat in SPELLS/ (SPELLS\ifx_element_wood_hit.mdx);
# its textures are hard-coded as spells\hitimpacts\<name>.blp inside the M2, and none is in the stock client.
SPELLS_ASSETS = [
    ("patch-N", "SPELLS/hitimpacts/ifx_element_wood_hit.m2"),
    ("patch-N", "SPELLS/hitimpacts/ifx_element_wood_hit00.skin"),
]
EXTRA_ASSETS = [
    ("patch-N", f"SPELLS/hitimpacts/{name}.blp")
    for name in ("weaponimpact_trihit_gold", "weaponimpact_streak_gold", "smoke_puffy_mask_verysoft", "sand_scroll",
                 "incense_brown", "wood_chips_2x2")
]

# Vertex extent of the mast M2 (the GameObjectDisplayInfo geo box), read from the stock file.
MAST_BOX = (-3.0151, -3.4469, -9.6157, 3.0151, 3.4469, 9.6158)
# creature_model_info for the iron shot display (bounding radius, combat reach): a 1.7 yd ball.
IRON_SHOT_BOUNDING_RADIUS = 0.85
IRON_SHOT_COMBAT_REACH = 1.0


def _asset_paths() -> list[Path]:
    return [SPELLS_DIR / Path(p).name for _, p in SPELLS_ASSETS] + [EXTRA_DIR / p for _, p in EXTRA_ASSETS]


def build_effect_name_rows() -> list[dict]:
    def effect(id_, name, model, area, scale):
        return _row(dbcfmt.SPELLVISUALEFFECTNAME, id_, Name=f"{name} (Custom)", FileName=model_path(model),
                    AreaEffectSize=area, Scale=scale, MinAllowedScale=0.01, MaxAllowedScale=100.0)

    # AreaEffectSize 0: the size is the fixed Scale, not the spell radius (a dynamic object would otherwise rescale
    # the 47.8 yd pool by its radius). The wood chips follow the target's size like the other chest impacts.
    return [
        effect(EFFECT_HOT_SHOT_SLAG, "Hot Shot Slag Pool", MODEL_HOT_SHOT, 0.0, HOT_SHOT_SCALE),
        effect(EFFECT_STEW_PUDDLE, "Fish Stew Puddle", MODEL_STEW, 0.0, STEW_SCALE),
        effect(EFFECT_SPLINTER_CHIPS, "Splinter Spray Wood Chips", MODEL_SPLINTER, 1.0, SPLINTER_CHIPS_SCALE),
    ]


def build_kit_rows(steam_impact_kit: dict) -> list[dict]:
    """`steam_impact_kit` is the stock kit 7387 row: the splinter kit keeps its world effect and sound."""
    return [
        _kit_row(KIT_HOT_SHOT_AREA, WorldEffect=EFFECT_HOT_SHOT_SLAG),
        _kit_row(KIT_HOT_SHOT_STATE, BaseEffect=EFFECT_HOT_SHOT_SLAG),
        _kit_row(KIT_STEW_AREA, WorldEffect=EFFECT_STEW_PUDDLE),
        _kit_row(KIT_STEW_STATE, BaseEffect=EFFECT_STEW_PUDDLE),
        _kit_row(KIT_SPLINTER_IMPACT, WorldEffect=steam_impact_kit["WorldEffect"], SoundID=steam_impact_kit["SoundID"],
                 ChestEffect=EFFECT_SPLINTER_CHIPS),
    ]


def build_spellvisual_rows(steam_blast: dict) -> list[dict]:
    """`steam_blast` is the stock SpellVisual 11064 row."""
    def visual(id_, **fields):
        row = _row(dbcfmt.SPELLVISUAL, id_, MissileAttachment=NO_ATTACHMENT)
        row.update(fields)
        return row

    splinter = dict(steam_blast)
    splinter["ID"] = SV_SPLINTER_SPRAY
    splinter["ImpactKit"] = KIT_SPLINTER_IMPACT
    return [
        visual(SV_HOT_SHOT_AREA, PersistentAreaKit=KIT_HOT_SHOT_AREA),
        visual(SV_HOT_SHOT_STATE, StateKit=KIT_HOT_SHOT_STATE),
        visual(SV_STEW_AREA, PersistentAreaKit=KIT_STEW_AREA),
        visual(SV_STEW_STATE, StateKit=KIT_STEW_STATE),
        splinter,
    ]


def build_creature_model_row() -> dict:
    return _row(
        dbcfmt.CREATUREMODELDATA, CDI_IRON_SHOT,
        Flags=0, ModelName=MODEL_IRON_SHOT, ModelScale=1.0,
        SizeClass=1, BloodID=1, FootprintParticleScale=1.0,
        WorldEffectScale=1.0, AttachedEffectScale=1.0,
    )


def build_creature_display_row() -> dict:
    return _row(
        dbcfmt.CREATUREDISPLAYINFO, CDI_IRON_SHOT,
        ModelID=CDI_IRON_SHOT, CreatureModelScale=1.0, CreatureModelAlpha=255, BloodLevel=1,
    )


def build_gameobject_display_row() -> dict:
    min_x, min_y, min_z, max_x, max_y, max_z = MAST_BOX
    return _row(
        dbcfmt.GAMEOBJECTDISPLAYINFO, GODI_MAINMAST,
        ModelName=MODEL_MAINMAST,
        GeoBoxMinX=min_x, GeoBoxMinY=min_y, GeoBoxMinZ=min_z, GeoBoxMaxX=max_x, GeoBoxMaxY=max_y, GeoBoxMaxZ=max_z,
    )


def _stock_rows(filename: str, table: dbcfmt.DbcTable, ids: set[int]) -> dict[int, dict]:
    found = {r["ID"]: r for r in dbcfile.read_dbc(DBC_DIR / filename, table) if r["ID"] in ids}
    missing = ids - set(found)
    if missing:
        raise SystemExit(f"{filename} lacks stock id(s) {sorted(missing)} in the working copy")
    return found


def _stock_inputs() -> tuple[dict, dict]:
    kit = _stock_rows("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, {STOCK_STEAM_IMPACT_KIT})[STOCK_STEAM_IMPACT_KIT]
    sv = _stock_rows("SpellVisual.dbc", dbcfmt.SPELLVISUAL, {STOCK_STEAM_BLAST_SV})[STOCK_STEAM_BLAST_SV]
    return kit, sv


def check_stock_ids() -> list[str]:
    """Confirms the ids the stock picks (1a, 1b, 5) and the copied rows rely on exist in the working copy."""
    _stock_rows("SpellVisual.dbc", dbcfmt.SPELLVISUAL, {STOCK_POCKETED_SV, STOCK_GOLD_FEVER_SV, STOCK_GOLD_TINT_SV})
    _stock_rows("GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO, {STOCK_ROPE_GODI})
    return [f"SpellVisual {STOCK_POCKETED_SV} (Pocketed), {STOCK_GOLD_FEVER_SV} (Gold Fever), {STOCK_GOLD_TINT_SV} "
            f"(gold tint), GameObjectDisplayInfo {STOCK_ROPE_GODI} (rope) exist"]


def build_pending_sql() -> str:
    """Server-side overlay: SpellVisual, CreatureModelData, CreatureDisplayInfo, GameObjectDisplayInfo (the other two
    tables are client-only) plus the creature_model_info row the iron shot's display needs. Range-deletes exactly the
    ids this script mints, so a rerun is idempotent."""
    kit, steam = _stock_inputs()
    visual_rows = build_spellvisual_rows(steam)
    blocks = [
        _table_block(dbcfmt.SPELLVISUAL, {"start": min(r["ID"] for r in visual_rows),
                                          "end": max(r["ID"] for r in visual_rows)}, visual_rows, []),
        _table_block(dbcfmt.CREATUREMODELDATA, {"start": CDI_IRON_SHOT, "end": CDI_IRON_SHOT},
                     [build_creature_model_row()], []),
        _table_block(dbcfmt.CREATUREDISPLAYINFO, {"start": CDI_IRON_SHOT, "end": CDI_IRON_SHOT},
                     [build_creature_display_row()], []),
        _table_block(dbcfmt.GAMEOBJECTDISPLAYINFO, {"start": GODI_MAINMAST, "end": GODI_MAINMAST},
                     [build_gameobject_display_row()], []),
        (f"DELETE FROM `creature_model_info` WHERE `DisplayID` = {CDI_IRON_SHOT};\n"
         "INSERT INTO `creature_model_info` (`DisplayID`, `BoundingRadius`, `CombatReach`, `Gender`, "
         f"`DisplayID_Other_Gender`) VALUES\n({CDI_IRON_SHOT}, {IRON_SHOT_BOUNDING_RADIUS}, "
         f"{IRON_SHOT_COMBAT_REACH}, 2, 0);"),
    ]
    return "\n\n".join(blocks) + "\n"


def _check_block(rows: list[dict], block: dict, what: str) -> None:
    for row in rows:
        if not block["start"] <= row["ID"] <= block["end"]:
            raise SystemExit(f"{what} id {row['ID']} is outside the deadmines block {block}")


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
        for archive, path in EXTRA_ASSETS:
            dest = EXTRA_DIR / path
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
    if missing:
        raise SystemExit(f"missing assets: {missing} - run with --extract first (see docstring)")

    steam_kit, steam_sv = _stock_inputs()
    effect_rows = build_effect_name_rows()
    kit_rows = build_kit_rows(steam_kit)
    visual_rows = build_spellvisual_rows(steam_sv)
    for rows, what in ((effect_rows, "SpellVisualEffectName"), (kit_rows, "SpellVisualKit"),
                       (visual_rows, "SpellVisual")):
        _check_block(rows, VISUAL_BLOCK, what)
    _check_block([build_gameobject_display_row()], GODI_BLOCK, "GameObjectDisplayInfo")
    _check_block([build_creature_model_row(), build_creature_display_row()], CREATURE_DISPLAY_BLOCK,
                 "CreatureModelData / CreatureDisplayInfo")

    if args.dry_run:
        for note in check_stock_ids():
            print("stock:", note)
        for row in effect_rows:
            print("SpellVisualEffectName:", row)
        for row in kit_rows:
            print("SpellVisualKit (non-zero fields):", {k: v for k, v in row.items() if v and v != 4294967295})
        for row in visual_rows:
            print("SpellVisual (non-zero fields):", {k: v for k, v in row.items() if v})
        print("CreatureModelData:", build_creature_model_row())
        print("CreatureDisplayInfo:", build_creature_display_row())
        print("GameObjectDisplayInfo:", build_gameobject_display_row())
        print("assets packed by build_patch_m.py:")
        for path in _asset_paths():
            print(f"  {path.relative_to(DBC_DIR.parent)} ({path.stat().st_size} bytes)")
        print(build_pending_sql())
        return

    check_stock_ids()
    added = 0
    added += _merge(DBC_DIR / "SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME, effect_rows)
    added += _merge(DBC_DIR / "SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, kit_rows)
    added += _merge(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL, visual_rows)
    added += _merge(DBC_DIR / "CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA, [build_creature_model_row()])
    added += _merge(DBC_DIR / "CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, [build_creature_display_row()])
    added += _merge(DBC_DIR / "GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO,
                    [build_gameobject_display_row()])
    print(f"added {added} row(s) across the 6 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
