#!/usr/bin/env python3
"""
One-off DBC content patch: the client visuals the reworked Blackrock Spire bosses need (Blackrock Spire build, WP V-1
for wave 1, the Lower Spire; V-2 appends wave 2; handoff .agents/plans/blackrock-spire-build/
blackrock-spire-build.HANDOFF.md s3.10, picks s7 #27). Same shape as patch_stratholme_vfx_models.py and
patch_shadowfang_keep_vfx_models.py (whose row helpers and asset extraction it shares).

ID blocks (ids.yaml reservation `blackrock_spire`):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: 90600-90649 (wave 1 uses 90600-90602, wave 2 90603-90616).
- CreatureModelData / CreatureDisplayInfo 90740-90769: wave 2 mints 90740 (the frost wall). GameObjectDisplayInfo
  90040-90049: none minted (the war horn is stock GODI 7352, the banner stock display 14542); free.

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

What wave 2 mints (V-2; the Upper Spire, B10-B15; every look unconfirmed until seen in game):
- Solakar SK4 held flame: a StateKit with the stock Torch SVEN 3032 in the RIGHT WEAPON slot (SV 90603). No new model.
- Rend and Gyth RG7 6 yd shadowflame pool: the wave 1 shadow quad again at scale 0.7 (SVEN 90602), AREA + STATE
  looks (SV 90604 / 90605).
- The Beast's Molten Blood pool: Ascension `magmazone.m2` (a 7.2 yd lava quad, visible disc about 2.9 yd radius at
  scale 1) as a STATE on a stalker, one rung per yard of radius from 4 to 10 (SVEN 90603-90609, SV 90606-90612), since
  neither a stalker aura nor a model row resizes at runtime and the pool grows 0.5 yd per Heat stack.
- Drakkisath DR2 / DR3 brands: Ascension `7fx_odyn_runicbrandorange_state` / `...yellow_state` (a 3.8 yd rune ring under
  the bearer) as Base states (SVEN 90610 / 90611, SV 90613 / 90614).
- Drakkisath DR17 12 yd ring of fire fallback: the STOCK `FlameCircleEffect` model (no asset) at scale 5.14 (stock Ring
  of Flame is scale 3.0 for a 7 yd radius), a fixed size, AREA + STATE looks (SVEN 90612, SV 90615 / 90616). The stock
  Ring of Flame (SV 8386) is the first pick; these are the fallback if the client does not scale it.
- Rend and Gyth RG6 frost wall: Ascension `frostwhisper_icewall_base.m2` as a creature display (CreatureModelData +
  CreatureDisplayInfo 90740, model scale 0.6).

SpellVisual, CreatureModelData and CreatureDisplayInfo are server-loaded, so `--sql-out PATH` emits their overlay
(SpellVisualKit and SpellVisualEffectName are client-only).

Assets (gitignored working copies; `--extract` pulls them from the read-only Ascension backup): `SPELLS/` gets the
models, their skins and the textures they hard-code that stock does not ship (wave 1: 2 models + 6 textures,
`t_vfx_hero_explosion_blur` is stock and is not repacked; wave 2: 5 more models and 9 more textures, the ones neither
stock nor already in the working copy).

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
# wave 2 (V-2)
EFFECT_SHADOWFLAME_POOL = 90602       # mannoroth_gooflowshadow_state_projected at SHADOWFLAME_POOL_SCALE (6 yd)
EFFECT_MAGMA_POOL_FIRST = 90603       # magmazone at MAGMA_POOL_RADII[i] / MAGMA_DISC_RADIUS: 90603 + i
EFFECT_BRAND_SEARING = 90610          # 7fx_odyn_runicbrandorange_state (orange)
EFFECT_BRAND_COLLAPSING = 90611       # 7fx_odyn_runicbrandyellow_state (yellow)
EFFECT_RING_OF_FIRE = 90612           # the stock FlameCircleEffect at RING_OF_FIRE_SCALE

# --- SpellVisualKit ---
KIT_SPIT_PATCH_AREA = 90600           # PersistentAreaKit WorldEffect
KIT_SPIT_PATCH_STATE = 90601          # StateKit BaseEffect
KIT_HORN_BURST = 90602                # impact kit: ChestEffect = the shock-ray burst
# wave 2 (V-2): kit ids = the SpellVisual ids that use them
KIT_TORCH_HELD = 90603                # StateKit: RightWeaponEffect = the stock torch
KIT_SHADOWFLAME_POOL_AREA = 90604     # PersistentAreaKit WorldEffect
KIT_SHADOWFLAME_POOL_STATE = 90605    # StateKit BaseEffect
KIT_MAGMA_POOL_FIRST = 90606          # StateKit BaseEffect, one per rung: 90606 + i
KIT_BRAND_SEARING = 90613             # StateKit BaseEffect
KIT_BRAND_COLLAPSING = 90614          # StateKit BaseEffect
KIT_RING_OF_FIRE_AREA = 90615         # PersistentAreaKit WorldEffect
KIT_RING_OF_FIRE_STATE = 90616        # StateKit BaseEffect

# --- SpellVisual (same ids as _visuals.py) ---
SV_SPIT_PATCH_AREA = 90600
SV_SPIT_PATCH_STATE = 90601
SV_HORN_BLOWN = 90602
# wave 2 (V-2)
SV_TORCH_HELD = 90603
SV_SHADOWFLAME_POOL_AREA = 90604
SV_SHADOWFLAME_POOL_STATE = 90605
SV_MAGMA_POOL_STATE = {4: 90606, 5: 90607, 6: 90608, 7: 90609, 8: 90610, 9: 90611, 10: 90612}
SV_BRAND_SEARING = 90613
SV_BRAND_COLLAPSING = 90614
SV_RING_OF_FIRE_AREA = 90615
SV_RING_OF_FIRE_STATE = 90616

# --- CreatureModelData / CreatureDisplayInfo (same id; ids.yaml 90740-90769) ---
CMD_ICE_WALL = 90740
CDI_ICE_WALL = 90740

# --- Scales (first guesses; tune in game, one number each) ---
SPIT_PATCH_YARDS = 17.8               # the quad at scale 1 (VISUALS-REPORT, gap 15; mesh bounds 17.8 x 17.8 x 0.1)
SPIT_PATCH_SCALE = 0.5                # 8.9 yd across for the 4 yd radius spit (WT16); the visible disc is a guess
WARHORN_BURST_SCALE = 1.0             # particles (0.2 yd mesh): no size to derive, tune in game
SHADOWFLAME_POOL_RADIUS = 6.0         # RG7 pool radius in yd (SP: 6 yd)
SHADOWFLAME_POOL_SCALE = 0.7          # 17.8 x 0.7 = 12.5 yd across for the 6 yd radius (the visible disc is a guess)
MAGMA_QUAD_YARDS = 7.2                # magmazone.m2's flat quad at scale 1 (VISUALS-REPORT, gap 19)
MAGMA_DISC_RADIUS = 2.9               # its visible lava disc at scale 1 (about 0.8 of the half quad; a guess)
MAGMA_POOL_RADII = (4, 5, 6, 7, 8, 9, 10)   # the rungs: 4.5 yd heroic to 5 yd normal plus 0.5 yd per Heat stack
BRAND_SCALE = 1.0                     # the runic brand ring is 3.8 yd across at scale 1: the size of a player
STOCK_RING_OF_FIRE_SCALE = 3.0        # stock Ring of Flame 35831 (SVEN 3106) ...
STOCK_RING_OF_FIRE_RADIUS = 7.0       # ... for a 7 yd dynamic object
RING_OF_FIRE_RADIUS = 12.0            # DR17: 12 yd
RING_OF_FIRE_SCALE = STOCK_RING_OF_FIRE_SCALE * RING_OF_FIRE_RADIUS / STOCK_RING_OF_FIRE_RADIUS   # 5.14
ICE_WALL_SCALE = 0.6                  # 26.9 yd wide x 3.5 thick x 13.5 tall at 1: about 16 x 2.1 x 8 yd (RG6, 2 pieces)

# --- Stock ids reused as-is (checked by --dry-run) ---
STOCK_HORN_CAST_SV = 4079             # Horn of Elemental Fury 56893: CastKit 3469, MissileDestinationAttachment 1
STOCK_HORN_CAST_KIT = 3469            # AnimID 81 + SoundID 6423
STOCK_HORN_SOUND = 6423
STOCK_TORCH_EFFECT = 3032             # SpellVisualEffectName 'Torch' (TorchSpell.mdx), Torch Toss's weapon-slot effect
STOCK_FLAME_CIRCLE_FILE = "Spells\\FlameCircleEffect.mdx"   # stock model: the ring of fire (no asset to pack)
STOCK_FLAME_CIRCLE_EFFECT = 3106      # Ring of Flame 35831's world effect (the scale 3.0 row)

MODEL_SPIT_PATCH = "mannoroth_gooflowshadow_state_projected"
MODEL_WARHORN_BURST = "ogre_warhorn_impact_base"
MODEL_MAGMA_POOL = "magmazone"
MODEL_BRAND_SEARING = "7fx_odyn_runicbrandorange_state"
MODEL_BRAND_COLLAPSING = "7fx_odyn_runicbrandyellow_state"
MODEL_ICE_WALL = "Frostwhisper_Icewall_Base"

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
    # wave 2 (V-2): models + skins (the icewall, the magma quad and the two brands have one skin each) ...
    *[("patch-N", f"SPELLS/{name}.m2") for name in (MODEL_MAGMA_POOL, MODEL_BRAND_SEARING, MODEL_BRAND_COLLAPSING)],
    ("patch-N", f"SPELLS/{MODEL_ICE_WALL}.M2"),
    *[("patch-N", f"SPELLS/{name}00.skin")
      for name in (MODEL_MAGMA_POOL, MODEL_BRAND_SEARING, MODEL_BRAND_COLLAPSING, MODEL_ICE_WALL)],
    # ... and the nine textures they hard-code that neither stock nor the working copy has (the others they name,
    # iceshard3, ember_offset_streak, white8x8, fire_*_mod2x_a and t_vfx_fire_anim_stylized_desat_02, are already in
    # the working copy; glow128, armorreflect3, t_vfx_lava2_blur and snow1 are stock).
    *[("patch-N", f"SPELLS/{name}.blp")
      for name in ("t_vfx_ring_aura_half", "star5a_a", "t_vfx_border_slide_blendadd", "cloud_magic_yellow",
                   "cloud_magic_red", "lava_4x4_mod4x", "lava_contrasty_mod2x", "lava_4x4_mod4x_red",
                   "magmazone_8_2261960")],
]


def _asset_paths() -> list[Path]:
    return [SPELLS_DIR / Path(p).name for _, p in SPELLS_ASSETS]


def build_effect_name_rows() -> list[dict]:
    def effect(id_, name, model, scale):
        # AreaEffectSize 0: the size is the fixed Scale, not the spell radius.
        return _row(dbcfmt.SPELLVISUALEFFECTNAME, id_, Name=f"{name} (Custom)", FileName=model_path(model),
                    AreaEffectSize=0.0, Scale=scale, MinAllowedScale=0.01, MaxAllowedScale=100.0)

    rows = [
        effect(EFFECT_SPIT_PATCH, "Shadowflame Spit Patch 4 yd", MODEL_SPIT_PATCH, SPIT_PATCH_SCALE),
        effect(EFFECT_WARHORN_BURST, "War Horn Burst", MODEL_WARHORN_BURST, WARHORN_BURST_SCALE),
        # wave 2 (V-2)
        effect(EFFECT_SHADOWFLAME_POOL, "Shadowflame Pool 6 yd", MODEL_SPIT_PATCH, SHADOWFLAME_POOL_SCALE),
    ]
    for i, radius in enumerate(MAGMA_POOL_RADII):
        rows.append(effect(EFFECT_MAGMA_POOL_FIRST + i, f"Magma Pool {radius} yd", MODEL_MAGMA_POOL,
                           round(radius / MAGMA_DISC_RADIUS, 3)))
    rows += [
        effect(EFFECT_BRAND_SEARING, "Searing Brand", MODEL_BRAND_SEARING, BRAND_SCALE),
        effect(EFFECT_BRAND_COLLAPSING, "Collapsing Brand", MODEL_BRAND_COLLAPSING, BRAND_SCALE),
    ]
    ring = effect(EFFECT_RING_OF_FIRE, "Ring of Fire 12 yd", "FlameCircleEffect", RING_OF_FIRE_SCALE)
    ring["FileName"] = STOCK_FLAME_CIRCLE_FILE     # the stock model, not a SPELLS\\ asset of ours
    return rows + [ring]


def build_kit_rows() -> list[dict]:
    return [
        _kit_row(KIT_SPIT_PATCH_AREA, WorldEffect=EFFECT_SPIT_PATCH),
        _kit_row(KIT_SPIT_PATCH_STATE, BaseEffect=EFFECT_SPIT_PATCH),
        _kit_row(KIT_HORN_BURST, ChestEffect=EFFECT_WARHORN_BURST),
        # wave 2 (V-2)
        _kit_row(KIT_TORCH_HELD, RightWeaponEffect=STOCK_TORCH_EFFECT),
        _kit_row(KIT_SHADOWFLAME_POOL_AREA, WorldEffect=EFFECT_SHADOWFLAME_POOL),
        _kit_row(KIT_SHADOWFLAME_POOL_STATE, BaseEffect=EFFECT_SHADOWFLAME_POOL),
        *[_kit_row(KIT_MAGMA_POOL_FIRST + i, BaseEffect=EFFECT_MAGMA_POOL_FIRST + i)
          for i in range(len(MAGMA_POOL_RADII))],
        _kit_row(KIT_BRAND_SEARING, BaseEffect=EFFECT_BRAND_SEARING),
        _kit_row(KIT_BRAND_COLLAPSING, BaseEffect=EFFECT_BRAND_COLLAPSING),
        _kit_row(KIT_RING_OF_FIRE_AREA, WorldEffect=EFFECT_RING_OF_FIRE),
        _kit_row(KIT_RING_OF_FIRE_STATE, BaseEffect=EFFECT_RING_OF_FIRE),
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
        # wave 2 (V-2): the held torch, the pools, the brands and the ring (a lasting aura gets a StateKit)
        visual(SV_TORCH_HELD, StateKit=KIT_TORCH_HELD),
        visual(SV_SHADOWFLAME_POOL_AREA, PersistentAreaKit=KIT_SHADOWFLAME_POOL_AREA),
        visual(SV_SHADOWFLAME_POOL_STATE, StateKit=KIT_SHADOWFLAME_POOL_STATE),
        *[visual(SV_MAGMA_POOL_STATE[radius], StateKit=KIT_MAGMA_POOL_FIRST + i)
          for i, radius in enumerate(MAGMA_POOL_RADII)],
        visual(SV_BRAND_SEARING, StateKit=KIT_BRAND_SEARING),
        visual(SV_BRAND_COLLAPSING, StateKit=KIT_BRAND_COLLAPSING),
        visual(SV_RING_OF_FIRE_AREA, PersistentAreaKit=KIT_RING_OF_FIRE_AREA),
        visual(SV_RING_OF_FIRE_STATE, StateKit=KIT_RING_OF_FIRE_STATE),
    ]


def build_creature_model_rows() -> list[dict]:
    """The frost wall's model: the Ascension icewall at ICE_WALL_SCALE (Flags/SizeClass/BloodID as the proven-live
    Divine Star orb row). The model's long axis is its local Y."""
    return [_row(dbcfmt.CREATUREMODELDATA, CMD_ICE_WALL, Flags=2, ModelName=model_path(MODEL_ICE_WALL),
                 ModelScale=ICE_WALL_SCALE, SizeClass=1, BloodID=1, FootprintParticleScale=1.0,
                 WorldEffectScale=1.0, AttachedEffectScale=1.0)]


def build_creature_display_rows() -> list[dict]:
    return [_row(dbcfmt.CREATUREDISPLAYINFO, CDI_ICE_WALL, ModelID=CMD_ICE_WALL, CreatureModelScale=1.0,
                 CreatureModelAlpha=255, BloodLevel=1)]


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
    stock_effects = _stock_rows("SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME,
                                {STOCK_TORCH_EFFECT, STOCK_FLAME_CIRCLE_EFFECT})
    if stock_effects[STOCK_FLAME_CIRCLE_EFFECT]["FileName"].lower() != STOCK_FLAME_CIRCLE_FILE.lower():
        raise SystemExit(f"stock SVEN {STOCK_FLAME_CIRCLE_EFFECT} is not {STOCK_FLAME_CIRCLE_FILE}")
    _stock_rows("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO,
                set(visuals.STOCK_CREATURE_DISPLAYS) | set(visuals.SHIPPED_CREATURE_DISPLAYS))
    _stock_rows("GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO, set(visuals.STOCK_GAMEOBJECT_DISPLAYS))
    _stock_rows("SoundEntries.dbc", dbcfmt.SOUNDENTRIES, set(visuals.STOCK_SOUND_ENTRIES))
    return [f"{len(set(visuals.STOCK_SPELL_VISUALS))} SpellVisual ids, {len(visuals.STOCK_CREATURE_DISPLAYS)} "
            f"CreatureDisplayInfo ids (+{len(visuals.SHIPPED_CREATURE_DISPLAYS)} shipped telegraph displays), "
            f"{len(visuals.STOCK_GAMEOBJECT_DISPLAYS)} GameObjectDisplayInfo ids and "
            f"{len(visuals.STOCK_SOUND_ENTRIES)} SoundEntries ids exist (plus the stock torch and flame circle "
            f"effects the wave 2 rows reuse)"]


def build_pending_sql() -> str:
    """Server-side overlay: SpellVisual, CreatureModelData and CreatureDisplayInfo (the other tables are
    client-only). Range-deletes exactly the ids this script mints, so a rerun is idempotent."""
    rows = build_spellvisual_rows()
    ids = [r["ID"] for r in rows]
    blocks = [_table_block(dbcfmt.SPELLVISUAL, {"start": min(ids), "end": max(ids)}, rows, [])]
    for table, builder, id_ in ((dbcfmt.CREATUREMODELDATA, build_creature_model_rows, CMD_ICE_WALL),
                                (dbcfmt.CREATUREDISPLAYINFO, build_creature_display_rows, CDI_ICE_WALL)):
        blocks.append(_table_block(table, {"start": id_, "end": id_}, builder(), []))
    return "\n\n".join(blocks) + "\n"


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
