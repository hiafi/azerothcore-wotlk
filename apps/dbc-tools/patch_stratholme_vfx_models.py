#!/usr/bin/env python3
"""
One-off DBC content patch: the client visuals the reworked Stratholme bosses need (Stratholme build, WP V-1 for wave 1,
V-2 appends wave 2; handoff .agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.10, picks s7 #21). Same shape
as patch_shadowfang_keep_vfx_models.py and patch_deadmines_vfx_models.py (whose row helpers it shares).

ID blocks (ids.yaml reservation `stratholme`):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: 90500-90549 (wave 1 uses 90500-90506, wave 2 90503-90515,
  per table: see the constants below).
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

What wave 2 (V-2) adds, also stock models only:
- FlameZone glow rings (`spells\\flamezone.m2`, the orange disc): the Unforgiven's 10 yd firelight ring and Forresten's
  8 yd hearth glow, a StateKit (BaseEffect) for a fire stalker's aura, at a fixed scale (AreaEffectSize 0).
- HolyZone glow discs (`spells\\holyzone.m2`, pale gold): one per Galford holy-fire puddle size (4, 5, 6, 8 yd), the
  same StateKit shape, one stalker per puddle.
- The Carrion Swarm fan (`dreadlord_carrion_swarm_cast.m2`, SVEN 3140's model) at 0.75 (a 30 yd fan about 58 degrees
  wide) as a PrecastKit BaseEffect, so it plays through the 2.5 s cast instead of at its end. The stock SV 9099 plays
  the 40 yd fan from its CastKit (cast end) and a stun swirl state; the new SV drops both.
- The lie judgment: Judgement of Darkness's shadow hands (stock CastKit 6817), the red judgement flash (SVEN 4600) as
  the impact kit, and the stock shadow chest impact (kit 117) as the TargetImpactKit.
- Everything else in the s3.10 wave 2 rows is stock: `_visuals.py` names the ids.

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
EFFECT_FLAMEZONE_10 = 90503           # flamezone at FLAMEZONE_10_SCALE (Unforgiven firelight ring, 10 yd radius)
EFFECT_FLAMEZONE_8 = 90504            # flamezone at FLAMEZONE_8_SCALE (Forresten hearth glow, 8 yd radius)
EFFECT_HOLYZONE_4 = 90505             # holyzone at HOLYZONE_4_SCALE (Galford puddles, radius in the name)
EFFECT_HOLYZONE_5 = 90506
EFFECT_HOLYZONE_6 = 90507
EFFECT_HOLYZONE_8 = 90508
EFFECT_CARRION_FAN = 90509            # dreadlord_carrion_swarm_cast at CARRION_FAN_SCALE (30 yd fan)

# --- SpellVisualKit (AREA: WorldEffect, the PersistentAreaKit of an area aura; STATE: BaseEffect, a stalker aura) ---
KIT_WEB_PATCH_5_AREA = 90500
KIT_WEB_PATCH_5_STATE = 90501
KIT_WEB_PATCH_7_AREA = 90502
KIT_WEB_PATCH_7_STATE = 90503
KIT_GUT_PUDDLE_AREA = 90504
KIT_GUT_PUDDLE_STATE = 90505
KIT_KEENED_SKULL_STATE = 90506        # StateKit: HeadEffect = stock SVEN 311
KIT_FLAMEZONE_10_STATE = 90507        # wave 2: StateKit BaseEffect on a stalker aura
KIT_FLAMEZONE_8_STATE = 90508
KIT_HOLYZONE_4_STATE = 90509
KIT_HOLYZONE_5_STATE = 90510
KIT_HOLYZONE_6_STATE = 90511
KIT_HOLYZONE_8_STATE = 90512
KIT_CARRION_FAN_PRECAST = 90513       # the fan on the caster through the cast (PrecastKit BaseEffect + hands)
KIT_CARRION_FAN_CAST = 90514          # the stock cast kit 7721 without its 40 yd fan (hands + anim + sound)
KIT_LIE_JUDGMENT_IMPACT = 90515       # ChestEffect = stock SVEN 4600 (red judgement flash) + the stock impact sound

# --- SpellVisual (same ids as _visuals.py) ---
SV_WEB_PATCH_5_AREA = 90500
SV_WEB_PATCH_5_STATE = 90501
SV_WEB_PATCH_7_AREA = 90502
SV_WEB_PATCH_7_STATE = 90503
SV_GUT_PUDDLE_AREA = 90504
SV_GUT_PUDDLE_STATE = 90505
SV_KEENED_SKULL_STATE = 90506
SV_FLAMEZONE_10_STATE = 90507
SV_FLAMEZONE_8_STATE = 90508
SV_HOLYZONE_4_STATE = 90509
SV_HOLYZONE_5_STATE = 90510
SV_HOLYZONE_6_STATE = 90511
SV_HOLYZONE_8_STATE = 90512
SV_CARRION_FAN = 90513
SV_LIE_JUDGMENT = 90514

# --- Scales (first guesses; tune in game, one number each) ---
WEB_STATE_YARDS = 2.3                 # Web_State's quad at scale 1 (VISUALS-REPORT, Nerub'enkan)
WEB_PATCH_5_SCALE = 4.3               # 10 yd across / 2.3 (rounded)
WEB_PATCH_7_SCALE = 6.0               # 14 yd across / 2.3 (rounded)
GOO_FLOW_YARDS = 47.8                 # goo_flow_state at scale 1 (patch_deadmines_vfx_models.py)
GUT_PUDDLE_SCALE = 0.25               # 12 yd across / 47.8 (rounded)
# The zone-glow models are one flat quad each; the visible disc reaches about 0.8 of the half quad (VISUALS-REPORT).
FLAMEZONE_RADIUS_PER_SCALE = 3.7      # visible radius in yd at scale 1 (quad 9.2 yd)
HOLYZONE_RADIUS_PER_SCALE = 3.3       # visible radius in yd at scale 1 (quad 8.2 yd)
FLAMEZONE_10_SCALE = 2.7              # 10 / 3.7
FLAMEZONE_8_SCALE = 2.2               # 8 / 3.7 (rounded)
HOLYZONE_4_SCALE = 1.2                # 4 / 3.3 (rounded)
HOLYZONE_5_SCALE = 1.5
HOLYZONE_6_SCALE = 1.8
HOLYZONE_8_SCALE = 2.5                # 8 / 3.3 is 2.4; 2.5 keeps the ring just past the hitbox (a glow, not a hit area)
CARRION_FAN_YARDS = 40.0              # SVEN 3140 at scale 1: 40 yd long, about 58 degrees wide
CARRION_FAN_SCALE = 0.75              # 30 yd, the BZ1 cone's length

# --- Stock ids reused as-is (checked by --dry-run) ---
STOCK_WEB_STATE_EFFECT = 595          # Spells\Web_State.mdx
STOCK_CURSE_HEAD_EFFECT = 311         # Spells\CurseofWeakness_Head.mdx
STOCK_CARRION_FAN_EFFECT = 3140       # spells\dreadlord_carrion_swarm_cast.mdx (the model at scale 1)
STOCK_JUDGEMENT_RED_EFFECT = 4600     # spells\judgement_impact_chest_red.mdx
STOCK_SHADOW_CHEST_IMPACT_KIT = 117   # ChestEffect 149 Shadow_ImpactDD_Low_Chest + sound 743
STOCK_SHADOW_HANDS_CAST_KIT = 6817    # Judgement of Darkness's cast kit: shadow hands, anim 53, sound 12335
STOCK_CARRION_IMPACT_KIT = 6819       # Carrion Swarm's chest impact (dreadlord_carrion_impact)
STOCK_JUDGEMENT_IMPACT_SOUND = 1272   # the sound of kit 6849 (the gold judgement flash)
STOCK_CARRION_PRECAST_SOUND = 745     # the sound of kit 6818
STOCK_CARRION_CAST_SOUND = 11786      # the sound of kits 6831 / 7721
STOCK_SHADOW_HANDS_EFFECT = 623       # Shadow_Precast_Uber_Hand

MODEL_WEB_STATE = "Web_State"
MODEL_GOO_FLOW = "goo_flow_state"
MODEL_FLAMEZONE = "flamezone"
MODEL_HOLYZONE = "holyzone"
MODEL_CARRION_FAN = "dreadlord_carrion_swarm_cast"
ANIM_PRECAST = 51                     # kit 6818's AnimID (the cast-start pose)
ANIM_CAST = 53                        # kits 6817 / 7721's AnimID


def build_effect_name_rows() -> list[dict]:
    def effect(id_, name, model, scale):
        # AreaEffectSize 0: the size is the fixed Scale, not the spell radius.
        return _row(dbcfmt.SPELLVISUALEFFECTNAME, id_, Name=f"{name} (Custom)", FileName=model_path(model),
                    AreaEffectSize=0.0, Scale=scale, MinAllowedScale=0.01, MaxAllowedScale=100.0)

    return [
        effect(EFFECT_WEB_PATCH_5, "Web Patch 5 yd", MODEL_WEB_STATE, WEB_PATCH_5_SCALE),
        effect(EFFECT_WEB_PATCH_7, "Web Patch 7 yd", MODEL_WEB_STATE, WEB_PATCH_7_SCALE),
        effect(EFFECT_GUT_PUDDLE, "Gut Puddle 6 yd", MODEL_GOO_FLOW, GUT_PUDDLE_SCALE),
        effect(EFFECT_FLAMEZONE_10, "Flame Zone 10 yd", MODEL_FLAMEZONE, FLAMEZONE_10_SCALE),
        effect(EFFECT_FLAMEZONE_8, "Flame Zone 8 yd", MODEL_FLAMEZONE, FLAMEZONE_8_SCALE),
        effect(EFFECT_HOLYZONE_4, "Holy Zone 4 yd", MODEL_HOLYZONE, HOLYZONE_4_SCALE),
        effect(EFFECT_HOLYZONE_5, "Holy Zone 5 yd", MODEL_HOLYZONE, HOLYZONE_5_SCALE),
        effect(EFFECT_HOLYZONE_6, "Holy Zone 6 yd", MODEL_HOLYZONE, HOLYZONE_6_SCALE),
        effect(EFFECT_HOLYZONE_8, "Holy Zone 8 yd", MODEL_HOLYZONE, HOLYZONE_8_SCALE),
        effect(EFFECT_CARRION_FAN, "Carrion Swarm Fan 30 yd", MODEL_CARRION_FAN, CARRION_FAN_SCALE),
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
        _kit_row(KIT_FLAMEZONE_10_STATE, BaseEffect=EFFECT_FLAMEZONE_10),
        _kit_row(KIT_FLAMEZONE_8_STATE, BaseEffect=EFFECT_FLAMEZONE_8),
        _kit_row(KIT_HOLYZONE_4_STATE, BaseEffect=EFFECT_HOLYZONE_4),
        _kit_row(KIT_HOLYZONE_5_STATE, BaseEffect=EFFECT_HOLYZONE_5),
        _kit_row(KIT_HOLYZONE_6_STATE, BaseEffect=EFFECT_HOLYZONE_6),
        _kit_row(KIT_HOLYZONE_8_STATE, BaseEffect=EFFECT_HOLYZONE_8),
        _kit_row(KIT_CARRION_FAN_PRECAST, AnimID=ANIM_PRECAST, BaseEffect=EFFECT_CARRION_FAN,
                 LeftHandEffect=STOCK_SHADOW_HANDS_EFFECT, RightHandEffect=STOCK_SHADOW_HANDS_EFFECT,
                 SoundID=STOCK_CARRION_PRECAST_SOUND),
        _kit_row(KIT_CARRION_FAN_CAST, AnimID=ANIM_CAST, LeftHandEffect=STOCK_SHADOW_HANDS_EFFECT,
                 RightHandEffect=STOCK_SHADOW_HANDS_EFFECT, SoundID=STOCK_CARRION_CAST_SOUND),
        _kit_row(KIT_LIE_JUDGMENT_IMPACT, ChestEffect=STOCK_JUDGEMENT_RED_EFFECT,
                 SoundID=STOCK_JUDGEMENT_IMPACT_SOUND),
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
        visual(SV_FLAMEZONE_10_STATE, StateKit=KIT_FLAMEZONE_10_STATE),
        visual(SV_FLAMEZONE_8_STATE, StateKit=KIT_FLAMEZONE_8_STATE),
        visual(SV_HOLYZONE_4_STATE, StateKit=KIT_HOLYZONE_4_STATE),
        visual(SV_HOLYZONE_5_STATE, StateKit=KIT_HOLYZONE_5_STATE),
        visual(SV_HOLYZONE_6_STATE, StateKit=KIT_HOLYZONE_6_STATE),
        visual(SV_HOLYZONE_8_STATE, StateKit=KIT_HOLYZONE_8_STATE),
        # The fan plays through the cast (PrecastKit); the cast kit keeps hands and sound; the stock chest impact stays.
        # No StateKit: the stock SV 9099 carries a stun swirl state that would show on a target that is not stunned.
        visual(SV_CARRION_FAN, PrecastKit=KIT_CARRION_FAN_PRECAST, CastKit=KIT_CARRION_FAN_CAST,
               ImpactKit=STOCK_CARRION_IMPACT_KIT, MissileDestinationAttachment=1),
        # Judgement of Darkness with a red flash instead of the gold one, and a shadow impact on the target.
        visual(SV_LIE_JUDGMENT, CastKit=STOCK_SHADOW_HANDS_CAST_KIT, ImpactKit=KIT_LIE_JUDGMENT_IMPACT,
               TargetImpactKit=STOCK_SHADOW_CHEST_IMPACT_KIT, MissileDestinationAttachment=1),
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
                {STOCK_WEB_STATE_EFFECT, STOCK_CURSE_HEAD_EFFECT, STOCK_CARRION_FAN_EFFECT,
                 STOCK_JUDGEMENT_RED_EFFECT, STOCK_SHADOW_HANDS_EFFECT})
    _stock_rows("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT,
                {STOCK_SHADOW_CHEST_IMPACT_KIT, STOCK_SHADOW_HANDS_CAST_KIT, STOCK_CARRION_IMPACT_KIT})
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
