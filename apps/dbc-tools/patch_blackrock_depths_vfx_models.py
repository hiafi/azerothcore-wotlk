#!/usr/bin/env python3
"""
One-off DBC content patch: the client visuals the reworked Blackrock Depths bosses need (Blackrock Depths build, WP V-1
for wave 1 and V-2 for wave 2, both built in one pass; handoff .agents/plans/blackrock-depths-build/
blackrock-depths-build.HANDOFF.md s3.10, picks VISUALS-REPORT.md "Free id blocks and proposed new rows"). Same shape as
patch_blackrock_spire_vfx_models.py (whose row helpers and asset extraction it shares).

ID blocks (ids.yaml reservation `blackrock_depths`):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: 90650-90699 (one number for all three; 90650-90659 used,
  90660-90669 spare for the tuning round, 90670-90699 free).
- CreatureModelData / CreatureDisplayInfo 90770-90799 (90770 and 90771 used: the keg and its alternate).
- GameObjectDisplayInfo 90050-90059: none minted (every object look is a stock display); free.

What it mints (every look unconfirmed until seen in game; scales are first guesses, one number each):
- 90650 Lager Puddle (Hurley, 5 yd radius, 30 s): Ascension `Goo_flow_state_wheat_beer` (a 47.8 yd quad of tinted slime;
  the amber tint is inferred from the model name, not decoded) at scale 0.21 as a STATE on a stalker.
- 90651 Crumbled Edge crack piece (Incendius): Ascension `groundcrack_fire_state` (a 29.4 yd quad of radial lava cracks)
  at 0.35 (about 10 yd across) as a STATE, one stalker every 10 yd along the band under the orange kit line.
- 90652 Moira's fire cage (the Emperor fight): the stock `FlameCircleEffect` at 0.64 (about a 1.5 yd ring of fire; stock
  Ring of Flame is scale 3.0 for 7 yd) as a STATE; cast Fire Shield SV 8581 beside it for the flame whirl. No asset.
- 90653-90656 Vault security field rungs 6, 7, 8, 9 yd (the Vault Sentinels, H grows 1 yd per 10 s): Ascension
  `target_arcane_state_centeronly` (a 9.6 yd quad, the visible disc about 0.45 of it, so scale = radius / 4.3) as a
  STATE on a stalker; a stalker aura cannot resize, so the boss swaps rung as the field grows.
- 90657 purple rune ring (Doom mark and Hatred, the Seven): Ascension `7fx_odyn_runicbrandpurple_state` (a 3.8 yd ring
  under the bearer, the BRS orange / yellow brands' purple sibling) as a BASE state.
- 90658 Portal Anchor (Flamelash): the stock `Creature_SpellPortalLarge_Red` (a 12 yd tall portal) at 0.4 (about 4 yd
  tall) as a STATE. No asset.
- 90659 web patch 6 yd (optional, Anub'shiah's Web Spit): the Stratholme stock `Web_State` at 5.2 (6 yd radius) as a
  STATE. The shipped 7 yd (SV 90503) and 5 yd (SV 90501) rows are the first picks. No asset.
- CreatureModelData + CreatureDisplayInfo 90770: Hurley's Thunderbrew Lager Keg on the stock `World\\Goober\\G_Keg.mdx`
  (2.7 yd, the Thunderbrew Lager Keg object's own model, with its beer mist); 90771 the alternate on the stock
  `BeerKeg02.mdx` (1.4 yd). The spec's display 24860 is an invisible stalker. No asset.

SpellVisual, CreatureModelData and CreatureDisplayInfo are server-loaded, so `--sql-out PATH` emits their overlay
(SpellVisualKit and SpellVisualEffectName are client-only). The same file carries the `creature_model_info` rows of the
two keg displays (bounding radius, combat reach): without one the keg can never spawn (Creature::InitEntry cancels the
load when ObjectMgr::GetCreatureModelRandomGender finds no row), and the rows must land in the same import as the
creaturedisplayinfo_dbc rows (ObjectMgr::LoadCreatureModelInfo dereferences the display row; a model-info row for a
display the DBC lacks crashes the boot). Review R-1-KIT M2; Deadmines' iron shot does the same.

Assets (gitignored working copies; `--extract` pulls them from the read-only Ascension backup into
var/model-visual-dbc/SPELLS/, where build_patch_m.py packs them into patch-M): 4 models, their skins and the 15 textures
they hard-code that stock does not ship (some are the BRS brand textures and are kept if already present).

Usage:
    python3 apps/dbc-tools/patch_blackrock_depths_vfx_models.py --extract     # once: pull the Ascension assets
    python3 apps/dbc-tools/patch_blackrock_depths_vfx_models.py --dry-run     # print rows + checks + SQL, write nothing
    python3 apps/dbc-tools/patch_blackrock_depths_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
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

# Blackrock Depths blocks (ids.yaml `reservations: blackrock_depths:`).
VISUAL_BLOCK = {"start": 90650, "end": 90699}
GODI_BLOCK = {"start": 90050, "end": 90059}
CREATURE_DISPLAY_BLOCK = {"start": 90770, "end": 90799}

# --- SpellVisualEffectName ---
EFFECT_LAGER_PUDDLE = 90650           # Goo_flow_state_wheat_beer at LAGER_PUDDLE_SCALE
EFFECT_CRUMBLED_EDGE_CRACK = 90651    # groundcrack_fire_state at CRACK_SCALE
EFFECT_MOIRA_FIRE_CAGE = 90652        # the stock FlameCircleEffect at FIRE_CAGE_SCALE
EFFECT_SECURITY_FIELD_FIRST = 90653   # target_arcane_state_centeronly at radius / FIELD_DISC_RADIUS: 90653 + i
EFFECT_PURPLE_RING = 90657            # 7fx_odyn_runicbrandpurple_state
EFFECT_PORTAL_ANCHOR = 90658          # the stock Creature_SpellPortalLarge_Red at PORTAL_ANCHOR_SCALE
EFFECT_WEB_PATCH_6 = 90659            # the stock Web_State at WEB_PATCH_6_SCALE

# --- SpellVisualKit (= the SpellVisual id that uses it; every row is a StateKit BaseEffect) ---
KIT_LAGER_PUDDLE = 90650
KIT_CRUMBLED_EDGE_CRACK = 90651
KIT_MOIRA_FIRE_CAGE = 90652
KIT_SECURITY_FIELD_FIRST = 90653      # 90653 + i
KIT_PURPLE_RING = 90657
KIT_PORTAL_ANCHOR = 90658
KIT_WEB_PATCH_6 = 90659

# --- SpellVisual (same ids as _visuals.py) ---
SV_LAGER_PUDDLE = 90650
SV_CRUMBLED_EDGE_CRACK = 90651
SV_MOIRA_FIRE_CAGE = 90652
SV_SECURITY_FIELD = {6: 90653, 7: 90654, 8: 90655, 9: 90656}
SV_PURPLE_RING = 90657
SV_PORTAL_ANCHOR = 90658
SV_WEB_PATCH_6 = 90659

# --- CreatureModelData / CreatureDisplayInfo (same id; ids.yaml 90770-90799) ---
CMD_LAGER_KEG = 90770
CDI_LAGER_KEG = 90770
CMD_LAGER_KEG_ALT = 90771
CDI_LAGER_KEG_ALT = 90771

# creature_model_info (server only): bounding radius and combat reach of the keg displays, from the model sizes above
# (the main keg is 2.7 x 2.7 x 2.6 yd with the 1.3 yd collision of KEG_COLLISION_WIDTH; the alternate is 1.4 yd). Gender
# 2 (none), no other-gender display, like every object-like creature display.
KEG_BOUNDING_RADIUS = 1.3
KEG_COMBAT_REACH = 1.5
KEG_ALT_BOUNDING_RADIUS = 0.7
KEG_ALT_COMBAT_REACH = 0.8
CREATURE_MODEL_INFO = (
    (CDI_LAGER_KEG, KEG_BOUNDING_RADIUS, KEG_COMBAT_REACH),
    (CDI_LAGER_KEG_ALT, KEG_ALT_BOUNDING_RADIUS, KEG_ALT_COMBAT_REACH),
)

# --- Scales (first guesses; tune in game, one number each) ---
LAGER_PUDDLE_YARDS = 47.8             # the quad at scale 1 (VISUALS-REPORT gap 29; mesh bounds 47.8 x 47.6 x 0.1)
LAGER_PUDDLE_RADIUS = 5.0             # HU: 5 yd radius, 30 s
LAGER_PUDDLE_SCALE = 0.21             # 47.8 x 0.21 = 10 yd across (the Deadmines goo uses 0.17 for 4 yd)
CRACK_QUAD_YARDS = 29.4               # groundcrack_fire_state at scale 1 (mesh bounds 29.4 x 29.4 x 0.0)
CRACK_SCALE = 0.35                    # about 10 yd across, one stalker every 10 yd along the band (gap 35)
FIRE_CAGE_SCALE = 0.64                # stock Ring of Flame is 3.0 for a 7 yd radius: 0.43 per yd, a 1.5 yd ring
SECURITY_FIELD_RADII = (6, 7, 8, 9)   # VA3: 6 yd, H grows to 9 yd
FIELD_QUAD_YARDS = 9.6                # target_arcane_state_centeronly at scale 1 (4 vertices, 9.6 x 9.6)
FIELD_DISC_RADIUS = 4.3               # its visible disc at scale 1 (about 0.9 of the half quad; a guess)
PURPLE_RING_SCALE = 1.0               # the runic brand ring is 3.8 yd across at scale 1: the size of a player
PORTAL_ANCHOR_SCALE = 0.4             # 12 yd tall at 1.0: about 4 yd tall for the stationary anchor
WEB_PATCH_6_SCALE = 5.2               # Web_State: 4.3 is 5 yd, 6.0 is 7 yd (Stratholme): 6 yd radius

# --- Stock ids reused as-is (checked by --dry-run) ---
STOCK_PORTAL_FILE = "Spells\\Creature_SpellPortalLarge_Red.mdx"     # SVEN 3597 (stock Boss Fire Portal State's)
STOCK_PORTAL_EFFECT = 3597
STOCK_FLAME_CIRCLE_FILE = "Spells\\FlameCircleEffect.mdx"           # the ring-of-fire model (stock SVEN 3106)
STOCK_FLAME_CIRCLE_EFFECT = 3106
STOCK_WEB_STATE_FILE = "SPELLS\\Web_State.mdx"                      # the Stratholme patch rows' model (SVEN 90501)
STOCK_WEB_EFFECT = 90501
KEG_MODEL = "World\\Goober\\G_Keg.mdx"                              # stock, the Thunderbrew Lager Keg object's model
KEG_ALT_MODEL = "World\\GENERIC\\HUMAN\\PASSIVE DOODADS\\BeerKegs\\BeerKeg02.mdx"   # stock, 1.4 yd
KEG_COLLISION_WIDTH = 1.3             # VR: "collision about 1.3 yd"
KEG_COLLISION_HEIGHT = 2.6            # the model is 2.6 yd tall (2.7 x 2.7 x 2.6)

MODEL_LAGER_PUDDLE = "Goo_flow_state_wheat_beer"
MODEL_CRUMBLED_EDGE_CRACK = "groundcrack_fire_state"
MODEL_SECURITY_FIELD = "target_arcane_state_centeronly"
MODEL_PURPLE_RING = "7fx_odyn_runicbrandpurple_state"

# Ascension assets, all in patch-N: (archive, path in the archive). The M2s name their textures `spells\\<name>.blp`;
# none of these is in the stock client except what the M2s also name from stock (t_vfx_border3b, t_vfx_lava_green,
# t_vfx_lava2, LAVALUMP2, glow128: not repacked). The three brand textures (t_vfx_ring_aura_half, star5a_a,
# t_vfx_border_slide_blendadd) are the BRS wave 2 ones: listed again so this patch does not depend on that extraction.
SPELLS_ASSETS = [
    *[("patch-N", f"SPELLS/{name}.m2")
      for name in (MODEL_LAGER_PUDDLE, MODEL_CRUMBLED_EDGE_CRACK, MODEL_SECURITY_FIELD, MODEL_PURPLE_RING)],
    *[("patch-N", f"SPELLS/{name}00.skin")
      for name in (MODEL_LAGER_PUDDLE, MODEL_CRUMBLED_EDGE_CRACK, MODEL_SECURITY_FIELD, MODEL_PURPLE_RING)],
    *[("patch-N", f"SPELLS/{name}.blp")
      for name in ("slime03_bw", "slime02b_bw", "t_vfx_lava_green_b",
                   "groundcrack_undulate_1", "groundcrack_undulate_2", "groundcrack_undulate_3",
                   "groundcrack_glow", "groundcrack_glow2", "groundcrack_shadow",
                   "targetarea_arcanea", "targetarea_everybase_centeronly",
                   "cloud_magic_purple", "t_vfx_ring_aura_half", "star5a_a", "t_vfx_border_slide_blendadd")],
]


def _asset_paths() -> list[Path]:
    return [SPELLS_DIR / Path(p).name for _, p in SPELLS_ASSETS]


def _effect_rows() -> list[tuple[int, str, str, float]]:
    """(id, name, FileName, scale) of every effect; AreaEffectSize 0 on all of them (a fixed size, not the radius)."""
    rows = [
        (EFFECT_LAGER_PUDDLE, "Lager Puddle 5 yd", model_path(MODEL_LAGER_PUDDLE), LAGER_PUDDLE_SCALE),
        (EFFECT_CRUMBLED_EDGE_CRACK, "Crumbled Edge Crack", model_path(MODEL_CRUMBLED_EDGE_CRACK), CRACK_SCALE),
        (EFFECT_MOIRA_FIRE_CAGE, "Moira Fire Cage", STOCK_FLAME_CIRCLE_FILE, FIRE_CAGE_SCALE),
    ]
    for i, radius in enumerate(SECURITY_FIELD_RADII):
        rows.append((EFFECT_SECURITY_FIELD_FIRST + i, f"Security Field {radius} yd", model_path(MODEL_SECURITY_FIELD),
                     round(radius / FIELD_DISC_RADIUS, 3)))
    rows += [
        (EFFECT_PURPLE_RING, "Purple Rune Ring", model_path(MODEL_PURPLE_RING), PURPLE_RING_SCALE),
        (EFFECT_PORTAL_ANCHOR, "Portal Anchor", STOCK_PORTAL_FILE, PORTAL_ANCHOR_SCALE),
        (EFFECT_WEB_PATCH_6, "Web Patch 6 yd", STOCK_WEB_STATE_FILE, WEB_PATCH_6_SCALE),
    ]
    return rows


def build_effect_name_rows() -> list[dict]:
    return [_row(dbcfmt.SPELLVISUALEFFECTNAME, id_, Name=f"{name} (Custom)", FileName=file_name,
                 AreaEffectSize=0.0, Scale=scale, MinAllowedScale=0.01, MaxAllowedScale=100.0)
            for id_, name, file_name, scale in _effect_rows()]


def build_kit_rows() -> list[dict]:
    """One StateKit BaseEffect per look: kit id = SpellVisual id = SpellVisualEffectName id."""
    return [_kit_row(id_, BaseEffect=id_) for id_, _, _, _ in _effect_rows()]


def build_spellvisual_rows() -> list[dict]:
    rows = []
    for id_, _, _, _ in _effect_rows():
        row = _row(dbcfmt.SPELLVISUAL, id_, MissileAttachment=NO_ATTACHMENT)
        row["StateKit"] = id_
        rows.append(row)
    return rows


def _model_row(id_: int, model: str, *, scale: float = 1.0) -> dict:
    """A keg-style static creature model: Flags/SizeClass/BloodID as the Deadmines iron shot, plus the collision box."""
    return _row(dbcfmt.CREATUREMODELDATA, id_, Flags=0, ModelName=model, ModelScale=scale, SizeClass=1, BloodID=1,
                FootprintParticleScale=1.0, CollisionWidth=KEG_COLLISION_WIDTH, CollisionHeight=KEG_COLLISION_HEIGHT,
                WorldEffectScale=1.0, AttachedEffectScale=1.0)


def build_creature_model_rows() -> list[dict]:
    return [_model_row(CMD_LAGER_KEG, KEG_MODEL), _model_row(CMD_LAGER_KEG_ALT, KEG_ALT_MODEL)]


def build_creature_display_rows() -> list[dict]:
    return [_row(dbcfmt.CREATUREDISPLAYINFO, cdi, ModelID=cmd, CreatureModelScale=1.0, CreatureModelAlpha=255,
                 BloodLevel=1)
            for cdi, cmd in ((CDI_LAGER_KEG, CMD_LAGER_KEG), (CDI_LAGER_KEG_ALT, CMD_LAGER_KEG_ALT))]


def build_creature_model_info_sql() -> str:
    """The `creature_model_info` rows of the keg displays (idempotent: deletes exactly its ids first)."""
    ids = ", ".join(str(display) for display, _, _ in CREATURE_MODEL_INFO)
    values = ",\n".join(f"({display}, {radius}, {reach}, 2, 0)" for display, radius, reach in CREATURE_MODEL_INFO)
    return (f"DELETE FROM `creature_model_info` WHERE `DisplayID` IN ({ids});\n"
            "INSERT INTO `creature_model_info` (`DisplayID`, `BoundingRadius`, `CombatReach`, `Gender`, "
            f"`DisplayID_Other_Gender`) VALUES\n{values};")


def _stock_rows(filename: str, table: dbcfmt.DbcTable, ids: set[int]) -> dict[int, dict]:
    found = {r["ID"]: r for r in dbcfile.read_dbc(DBC_DIR / filename, table) if r["ID"] in ids}
    missing = ids - set(found)
    if missing:
        raise SystemExit(f"{filename} lacks stock id(s) {sorted(missing)} in the working copy")
    return found


def _load_visuals():
    """source/npcs/blackrock_depths/_visuals.py by path (source/ is not a package): the ids the boss files use."""
    path = Path(__file__).resolve().parent / "source" / "npcs" / "blackrock_depths" / "_visuals.py"
    spec = importlib.util.spec_from_file_location("blackrock_depths_visuals", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_stock_ids() -> list[str]:
    """Confirms every stock or shipped id `_visuals.py` names (and the stock effects the rows reuse) exists in the
    working copy; returns a one-line note."""
    visuals = _load_visuals()
    _stock_rows("SpellVisual.dbc", dbcfmt.SPELLVISUAL,
                set(visuals.STOCK_SPELL_VISUALS) | set(visuals.SHIPPED_SPELL_VISUALS))
    stock_effects = _stock_rows("SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME,
                                {STOCK_PORTAL_EFFECT, STOCK_FLAME_CIRCLE_EFFECT, STOCK_WEB_EFFECT})
    for effect_id, file_name in ((STOCK_PORTAL_EFFECT, STOCK_PORTAL_FILE),
                                 (STOCK_FLAME_CIRCLE_EFFECT, STOCK_FLAME_CIRCLE_FILE),
                                 (STOCK_WEB_EFFECT, STOCK_WEB_STATE_FILE)):
        if stock_effects[effect_id]["FileName"].lower() != file_name.lower():
            raise SystemExit(f"stock SVEN {effect_id} is not {file_name}")
    _stock_rows("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, set(visuals.STOCK_CREATURE_DISPLAYS))
    _stock_rows("GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO, set(visuals.STOCK_GAMEOBJECT_DISPLAYS))
    return [f"{len(set(visuals.STOCK_SPELL_VISUALS))} stock + {len(set(visuals.SHIPPED_SPELL_VISUALS))} shipped "
            f"SpellVisual ids, {len(visuals.STOCK_CREATURE_DISPLAYS)} CreatureDisplayInfo ids and "
            f"{len(visuals.STOCK_GAMEOBJECT_DISPLAYS)} GameObjectDisplayInfo ids exist (plus the stock portal, "
            f"flame circle and web effects the rows reuse)"]


def build_pending_sql() -> str:
    """Server-side overlay: SpellVisual, CreatureModelData and CreatureDisplayInfo (the other tables are
    client-only) plus the keg displays' creature_model_info rows. Range-deletes exactly the ids this script mints,
    so a rerun is idempotent."""
    rows = build_spellvisual_rows()
    ids = [r["ID"] for r in rows]
    blocks = [_table_block(dbcfmt.SPELLVISUAL, {"start": min(ids), "end": max(ids)}, rows, [])]
    for table, builder in ((dbcfmt.CREATUREMODELDATA, build_creature_model_rows),
                           (dbcfmt.CREATUREDISPLAYINFO, build_creature_display_rows)):
        built = builder()
        built_ids = [r["ID"] for r in built]
        blocks.append(_table_block(table, {"start": min(built_ids), "end": max(built_ids)}, built, []))
    blocks.append(build_creature_model_info_sql())
    return "\n\n".join(blocks) + "\n"


def _check_block(rows: list[dict], block: dict, what: str) -> None:
    for row in rows:
        if not block["start"] <= row["ID"] <= block["end"]:
            raise SystemExit(f"{what} id {row['ID']} is outside the blackrock_depths block {block}")


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
    model_rows = build_creature_model_rows()
    display_rows = build_creature_display_rows()
    for rows, what in ((model_rows, "CreatureModelData"), (display_rows, "CreatureDisplayInfo")):
        _check_block(rows, CREATURE_DISPLAY_BLOCK, what)

    if args.dry_run:
        for note in check_stock_ids():
            print("stock:", note)
        for row in effect_rows:
            print("SpellVisualEffectName:", row)
        for row in kit_rows:
            print("SpellVisualKit (non-zero fields):", {k: v for k, v in row.items() if v and v != 4294967295})
        for row in visual_rows:
            print("SpellVisual (non-zero fields):", {k: v for k, v in row.items() if v})
        for row in model_rows:
            print("CreatureModelData (non-zero fields):", {k: v for k, v in row.items() if v})
        for row in display_rows:
            print("CreatureDisplayInfo (non-zero fields):", {k: v for k, v in row.items() if v})
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
    added += _merge(DBC_DIR / "CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA, model_rows)
    added += _merge(DBC_DIR / "CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, display_rows)
    print(f"added {added} row(s) across the 5 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
