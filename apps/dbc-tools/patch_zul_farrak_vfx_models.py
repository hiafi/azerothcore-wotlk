#!/usr/bin/env python3
"""
One-off DBC content patch: the client visuals the reworked Zul'Farrak bosses need (Zul'Farrak build, WP V; handoff
.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.10 and appendix C, picks VISUALS-REPORT.md "Part 2: new
rows"). Same shape as patch_ragefire_chasm_vfx_models.py (whose row helpers and asset extraction it shares).

ID blocks (ids.yaml reservation `zul_farrak`):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: 90700-90749. Used: SpellVisual 90700-90707; Kit 90700, 90701,
  90703-90707 and the second kits of the two hydra poses, 90711 and 90712; EffectName 90700, 90701, 90707. (90702 has
  no kit or effect: its only slot is the stock InstantAreaKit 9161.)
- CreatureModelData / CreatureDisplayInfo: 90830-90849. Used: 90830-90832 (the three discs).
- GameObjectDisplayInfo: none minted.

What it mints (every look unconfirmed until seen in game; scales are first guesses, one number each):
- 90700 / 90701 Ukorz's quicksand pit and bladestorm trail: StateKit BaseEffect on the Ascension
  `8fx_toldagor_sandqueen_sandtrap_state` (a crater ring and sand swirl, 10.9 yd across) at scale 1.1 / 0.73. Fallback
  stock SV 7437 plus the marker.
- 90702 Storm Strike: a copy of stock SV 3 keeping only its InstantAreaKit 9161 (call lightning, sound 30).
- 90703 Bladestorm (blades only): StateKit, AnimID 126, BaseEffect = SVEN 90370 (the model Ragefire Chasm's patch-M rows
  ship: `cfx_warrior_bladestorm_statebase`), sound 4354. Needs RFC's SVEN 90370 live. Fallback stock SV 6044.
- 90704 Basilisk gaze: a copy of stock SV 8311 whose channel kit is a copy of kit 7084 with AnimID 124 -> 51.
- 90705 / 90706 Hydra poses: copies of stock SV 36 / 854 whose precast and cast kits are copies with the animation the
  Hydra lacks (51 / 53) swapped for 32.
- 90707 Hydra Static Charge: StateKit, BaseEffect = the stock `LightningShield_State_Base` model at scale 7.0, sound
  3256 (stock SV 37 is the same model at 0.3 yd: nearly invisible on a 24 yd hydra).
- 90830 / 90831 / 90832 creature displays on the Ascension element discs `target_water_state_projected`,
  `target_frost_state_projected` and `target_lightning_state_projected` (each a 9.6 yd quad, 0 emitters: creature
  scale = radius / 4.8). The water disc's second texture names a file that is in no archive
  (`world\\expansion08\\doodads\\ardenweald\\target_anima_ardenweald_state_3507129.blp`): the script re-points it to
  the shipped `targetarea_everybase` (a one-string edit of the extracted model, in place, same length rule as
  lib/m2_patch.set_texture_path).

SpellVisual, CreatureModelData and CreatureDisplayInfo are server-loaded, so `--sql-out PATH` emits their overlay
(SpellVisualKit and SpellVisualEffectName are client-only) plus the creature_model_info rows: the three discs (radius
0.5, reach 0.5: flat, so melee targeting does not see them) and the four stock displays whose live row holds 0 or a
size that is wrong for the use (6697, 25175, 29716, 26252: RB-10; a zero radius makes a boss unhittable).
These four UPDATEs are by display id, so they reach every creature that wears the display (live SELECT 2026-11-25,
creature_template_model; R-1-LOOT m-2). The other users, all judged harmless (none is targetable combat content whose
fight depends on the old size):
- 6697: only Theka's shapeshift 7791 (ZF). Live row 0 / 0.
- 29716: Ghostly Troll Celebrant 35253 (4 gossip spawns on map 1, row 0 / 0, an ordinary NPC that gains a troll's
  radius 0.306 and reach 1.5) and Spectral Troll 300917 (Scarlet Monastery's not-selectable, not-attackable phantom of
  `npc_sm_hollis_phantom`: reach 0 -> 1.5 only changes its spacing). Both look unchanged.
- 25175: [ph] exploding barrel 28173 and Barrel o' Fun 29737 (second of two displays, no world spawns): live row 0 / 0,
  so the new 0.7 / 0.8 only gives them a size.
- 26252: Goblin Sapper Backpack 29440 and 29556 (type 10, unit_flags 0x2000000, no world spawn, SmartAI or
  summon-group row, so spell-summoned; the summoning spell is stock DBC, not checked): the one row that SHRINKS
  (radius 0.75 -> 0.3, reach 3.75 -> 0.5), to the model's own size (PowderKegFused is 0.45 x 0.5 x 0.75 yd). A prop
  of this kind is not attacked or meleed, so the smaller reach should matter to nothing.
No ZF-only display copy is made: nothing above changes in a way a player can see, and a copy would need a new display
row in 90833-90849 that `_visuals.py`, `theka.py`, `pyramid_stair.py` and the C++ constants would all have to follow.
If a Backpack ever looks or behaves wrong, mint the copy then.

Assets (gitignored working copies; `--extract` pulls them from the read-only Ascension backup (patch-N) into
var/model-visual-dbc/SPELLS/, where build_patch_m.py packs them into patch-M, and applies the water-disc texture edit):
4 models, their 4 skins and 14 textures. If an Ascension file is missing in the backup, --extract stops with its name;
every row has a stock fallback and the boss files wire it with one constant (`*_FALLBACK` in _visuals.py). The discs'
fallback is the BM marker circle.

Usage:
    cd apps/dbc-tools
    python3 patch_zul_farrak_vfx_models.py --extract     # once: pull the Ascension assets (+ the water disc edit)
    python3 patch_zul_farrak_vfx_models.py --dry-run     # print rows + checks + SQL, write nothing
    python3 patch_zul_farrak_vfx_models.py --sql-out ../../data/sql/updates/pending_db_world/rev_<ts>.sql
then build_patch_m.py (patch-M.mpq carries the DBCs and SPELLS\\). The orchestrator runs the last two at deploy.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import struct
import tempfile
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, _kit_row, _merge, _row, model_path
from patch_rogue_vfx_models import ASCENSION_DATA, NO_ATTACHMENT, SPELLS_DIR, _extract_one

# Zul'Farrak blocks (ids.yaml `reservations: zul_farrak:`).
VISUAL_BLOCK = {"start": 90700, "end": 90749}
DISPLAY_BLOCK = {"start": 90830, "end": 90849}

# --- SpellVisual ids (SpellVisual = Kit = EffectName number where they have them) ---
SV_QUICKSAND_PIT = 90700
SV_QUICKSAND_TRAIL = 90701
SV_STORM_STRIKE = 90702
SV_BLADESTORM = 90703
SV_BASILISK_GAZE = 90704
SV_HYDRA_DISCHARGE_POSE = 90705
SV_HYDRA_SPIT_POSE = 90706
SV_STATIC_CHARGE = 90707

# --- SpellVisualKit ids: the SpellVisual numbers, plus a second kit for the poses that change two kits ---
KIT_HYDRA_DISCHARGE_CAST = 90711
KIT_HYDRA_SPIT_CAST = 90712

# --- SpellVisualEffectName ids ---
EFFECT_QUICKSAND_PIT = 90700
EFFECT_QUICKSAND_TRAIL = 90701
EFFECT_STATIC_CHARGE = 90707

# --- CreatureModelData = CreatureDisplayInfo ids ---
CDI_WATER_DISC = 90830
CDI_ICE_DISC = 90831
CDI_STORM_DISC = 90832
CMD_WATER_DISC = 90830
CMD_ICE_DISC = 90831
CMD_STORM_DISC = 90832

# --- Scales (first guesses; tune in game, one number each) ---
QUICKSAND_PIT_SCALE = 1.1              # the model is 10.9 yd across: about 12 yd for the 6 yd radius pit
QUICKSAND_TRAIL_SCALE = 0.73           # about 8 yd across for the 4 yd trail
STATIC_CHARGE_SCALE = 7.0              # LightningShield_State_Base (0.3 yd) on a 24 yd hydra: 6 to 8
BLADESTORM_ANIM = 126                  # the Felguard / troll Whirlwind clip; the state kit owns it
STATIC_CHARGE_SOUND = 3256             # stock SV 37's kit sound
BLADESTORM_SOUND = 4354                # stock Whirlwind state sound
HYDRA_POSE_ANIM = 32                   # the clip the Hydra has for a cast (it lacks 51-54)
BASILISK_GAZE_ANIM = 51                # the Basilisk lacks 124 (the stock beam kit's clip) and 53 / 54

# Rows this script reuses by id (--dry-run verifies them in the working copy).
RFC_BLADES_EFFECT = 90370            # RFC's SVEN (shipped in patch-M): `SPELLS\\cfx_warrior_bladestorm_statebase`
STOCK_LIGHTNING_SHIELD_EFFECT = 296    # SVEN `Spells\\LightningShield_State_Base.mdx`
STOCK_LIGHTNING_SHIELD_FILE = "spells\\lightningshield_state_base.mdx"
BLADES_FILE = "spells\\cfx_warrior_bladestorm_statebase.mdx"

# (new SV, stock SV it copies, [(SpellVisual field, new kit id, expected old AnimID, new AnimID), ...])
POSE_COPIES = (
    (SV_BASILISK_GAZE, 8311, (("ChannelKit", SV_BASILISK_GAZE, 124, BASILISK_GAZE_ANIM),)),
    (SV_HYDRA_DISCHARGE_POSE, 36, (("PrecastKit", SV_HYDRA_DISCHARGE_POSE, 51, HYDRA_POSE_ANIM),
                                   ("CastKit", KIT_HYDRA_DISCHARGE_CAST, 53, HYDRA_POSE_ANIM))),
    (SV_HYDRA_SPIT_POSE, 854, (("PrecastKit", SV_HYDRA_SPIT_POSE, 51, HYDRA_POSE_ANIM),
                               ("CastKit", KIT_HYDRA_SPIT_CAST, 53, HYDRA_POSE_ANIM))),
)
STORM_STRIKE_SOURCE_SV = 3             # keeps only InstantAreaKit
STORM_STRIKE_INSTANT_KIT = 9161

# --- Assets: (archive, path in the archive); every one is asc-N ---
MODEL_SAND_TRAP = "8fx_toldagor_sandqueen_sandtrap_state"
MODEL_WATER_DISC = "target_water_state_projected"
MODEL_ICE_DISC = "target_frost_state_projected"
MODEL_STORM_DISC = "target_lightning_state_projected"
MODELS = (MODEL_SAND_TRAP, MODEL_WATER_DISC, MODEL_ICE_DISC, MODEL_STORM_DISC)
SAND_TRAP_TEXTURES = ("8fx_mask_crater_sand_a", "8fx_smoke_sand_dissolve", "8fx_sand_spreadburst_a",
                      "8fx_mask_shockwave_water_01", "smoke_plumes_blurred_vertical_blendadd",
                      "starfield04_mgp_a_yellowlight", "8fx_sandtrap_base", "smoke_wispyenergy_sand_a")
WATER_DISC_TEXTURES = ("target_water_state_4485122", "targetarea_everybase")
ICE_DISC_TEXTURES = ("target_frost_state_4497647", "targetarea_everybase_hot")
STORM_DISC_TEXTURES = ("targetarea_lightning", "targetarea_everybase_medium_low")
TEXTURES = (*SAND_TRAP_TEXTURES, *WATER_DISC_TEXTURES, *ICE_DISC_TEXTURES, *STORM_DISC_TEXTURES)
# The models' hard-coded texture names, in texture order (read from the Ascension M2s; the second water one is the
# missing file the edit replaces). Pinned by the test, which reads the real models.
MODEL_TEXTURES = {
    MODEL_SAND_TRAP: SAND_TRAP_TEXTURES,
    MODEL_WATER_DISC: WATER_DISC_TEXTURES,
    MODEL_ICE_DISC: ICE_DISC_TEXTURES,
    MODEL_STORM_DISC: STORM_DISC_TEXTURES,
}
WATER_MISSING_TEXTURE = "world\\expansion08\\doodads\\ardenweald\\target_anima_ardenweald_state_3507129.blp"
WATER_FIXED_TEXTURE = "spells\\targetarea_everybase.blp"
SPELLS_ASSETS = [
    *[("patch-N", f"SPELLS/{model}.m2") for model in MODELS],
    *[("patch-N", f"SPELLS/{model}00.skin") for model in MODELS],
    *[("patch-N", f"SPELLS/{name}.blp") for name in TEXTURES],
]

# creature_model_info (server only), (DisplayID, BoundingRadius, CombatReach, Gender, DisplayID_Other_Gender).
# The three discs are flat (radius and reach 0.5 as the handoff says; gender 2, none, like every object-like display).
DISC_MODEL_INFO = ((CDI_WATER_DISC, 0.5, 0.5), (CDI_ICE_DISC, 0.5, 0.5), (CDI_STORM_DISC, 0.5, 0.5))
# Live rows of stock displays that hold 0 or a size wrong for the use (VR flag 11, RB-10). Updates only the size: the
# row's gender and other-gender columns stay. 6697 is TrollMale x1.2 (0.306 / 1.5 x 1.2); 29716 is a TrollMale ghost;
# 26252 (PowderKegFused, 0.45 x 0.5 x 0.75 yd) is used at object scale 2.0, so its row is the scale-1 size (the live
# reach 3.75 is far too large for a keg); 25175 (G_BarrelExplode x1.5, 1.4 x 1.4 x 0.7) is the alternate keg.
STOCK_MODEL_INFO_UPDATES = (
    (6697, 0.3672, 1.8),
    (25175, 0.7, 0.8),
    (29716, 0.306, 1.5),
    (26252, 0.3, 0.5),
)


def _asset_paths() -> list[Path]:
    return [SPELLS_DIR / Path(p).name for _, p in SPELLS_ASSETS]


def _effect_rows() -> list[tuple[int, str, str, float]]:
    """(id, name, FileName, scale) of every effect; AreaEffectSize 0 on all of them (a fixed size, not the radius)."""
    return [
        (EFFECT_QUICKSAND_PIT, "Quicksand Pit", model_path(MODEL_SAND_TRAP), QUICKSAND_PIT_SCALE),
        (EFFECT_QUICKSAND_TRAIL, "Quicksand Trail", model_path(MODEL_SAND_TRAP), QUICKSAND_TRAIL_SCALE),
        (EFFECT_STATIC_CHARGE, "Hydra Static Charge", "Spells\\LightningShield_State_Base.mdx", STATIC_CHARGE_SCALE),
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


def _stock_pose_kits() -> dict[int, dict]:
    """The stock kits the pose copies start from, by the stock SpellVisual's slot."""
    visuals = _stock("SpellVisual.dbc", dbcfmt.SPELLVISUAL, {src for _, src, _ in POSE_COPIES})
    kit_ids = {visuals[src][field] for _, src, changes in POSE_COPIES for field, _, _, _ in changes}
    return _stock("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, kit_ids)


def build_kit_rows() -> list[dict]:
    """Quicksand pit and trail, bladestorm and static charge state kits, plus the pose kits (stock copies with the
    AnimID the Basilisk / Hydra lacks swapped for one they have). Sorted by id."""
    rows = [
        _kit_row(SV_QUICKSAND_PIT, BaseEffect=EFFECT_QUICKSAND_PIT),
        _kit_row(SV_QUICKSAND_TRAIL, BaseEffect=EFFECT_QUICKSAND_TRAIL),
        _kit_row(SV_BLADESTORM, AnimID=BLADESTORM_ANIM, BaseEffect=RFC_BLADES_EFFECT, SoundID=BLADESTORM_SOUND),
        _kit_row(SV_STATIC_CHARGE, BaseEffect=EFFECT_STATIC_CHARGE, SoundID=STATIC_CHARGE_SOUND),
    ]
    visuals = _stock("SpellVisual.dbc", dbcfmt.SPELLVISUAL, {src for _, src, _ in POSE_COPIES})
    stock_kits = _stock_pose_kits()
    for _, src, changes in POSE_COPIES:
        for field, new_id, old_anim, new_anim in changes:
            kit = dict(stock_kits[visuals[src][field]])
            if kit["AnimID"] != old_anim:
                raise SystemExit(f"stock kit {kit['ID']} of SV {src} has AnimID {kit['AnimID']}, expected {old_anim}")
            kit["ID"] = new_id
            kit["AnimID"] = new_anim
            rows.append(kit)
    return sorted(rows, key=lambda r: r["ID"])


def build_spellvisual_rows() -> list[dict]:
    pit = _row(dbcfmt.SPELLVISUAL, SV_QUICKSAND_PIT, MissileAttachment=NO_ATTACHMENT)
    pit["StateKit"] = SV_QUICKSAND_PIT
    trail = _row(dbcfmt.SPELLVISUAL, SV_QUICKSAND_TRAIL, MissileAttachment=NO_ATTACHMENT)
    trail["StateKit"] = SV_QUICKSAND_TRAIL
    blades = _row(dbcfmt.SPELLVISUAL, SV_BLADESTORM, MissileAttachment=NO_ATTACHMENT)
    blades["StateKit"] = SV_BLADESTORM
    charge = _row(dbcfmt.SPELLVISUAL, SV_STATIC_CHARGE, MissileAttachment=NO_ATTACHMENT)
    charge["StateKit"] = SV_STATIC_CHARGE
    stock = _stock("SpellVisual.dbc", dbcfmt.SPELLVISUAL, {src for _, src, _ in POSE_COPIES} | {STORM_STRIKE_SOURCE_SV})
    strike = _row(dbcfmt.SPELLVISUAL, SV_STORM_STRIKE)
    for key in ("MissileDestinationAttachment", "MissileAttachment"):
        strike[key] = stock[STORM_STRIKE_SOURCE_SV][key]
    strike["InstantAreaKit"] = STORM_STRIKE_INSTANT_KIT
    rows = [pit, trail, strike, blades]
    for new_id, src, changes in POSE_COPIES:
        copy = dict(stock[src])
        copy["ID"] = new_id
        for field, kit_id, _, _ in changes:
            copy[field] = kit_id
        rows.append(copy)
    rows.append(charge)
    return sorted(rows, key=lambda r: r["ID"])


def build_creature_model_rows() -> list[dict]:
    """The three disc models: flat quads used as creature models, Flags/SizeClass/BloodID as the proven-live marker and
    keg rows, no collision box."""
    return [_row(dbcfmt.CREATUREMODELDATA, cmd, Flags=0, ModelName=model_path(model), ModelScale=1.0, SizeClass=1,
                 BloodID=1, FootprintParticleScale=1.0, WorldEffectScale=1.0, AttachedEffectScale=1.0)
            for cmd, model in ((CMD_WATER_DISC, MODEL_WATER_DISC), (CMD_ICE_DISC, MODEL_ICE_DISC),
                               (CMD_STORM_DISC, MODEL_STORM_DISC))]


def build_creature_display_rows() -> list[dict]:
    return [_row(dbcfmt.CREATUREDISPLAYINFO, cdi, ModelID=cmd, CreatureModelScale=1.0, CreatureModelAlpha=255,
                 BloodLevel=1)
            for cdi, cmd in ((CDI_WATER_DISC, CMD_WATER_DISC), (CDI_ICE_DISC, CMD_ICE_DISC),
                             (CDI_STORM_DISC, CMD_STORM_DISC))]


def build_creature_model_info_sql() -> str:
    """The `creature_model_info` rows (idempotent: deletes the three disc ids first; the stock displays' rows are
    updated in place, only their size columns)."""
    ids = ", ".join(str(display) for display, _, _ in DISC_MODEL_INFO)
    values = ",\n".join(f"({display}, {radius}, {reach}, 2, 0)" for display, radius, reach in DISC_MODEL_INFO)
    lines = [f"DELETE FROM `creature_model_info` WHERE `DisplayID` IN ({ids});",
             "INSERT INTO `creature_model_info` (`DisplayID`, `BoundingRadius`, `CombatReach`, `Gender`, "
             f"`DisplayID_Other_Gender`) VALUES\n{values};"]
    for display, radius, reach in STOCK_MODEL_INFO_UPDATES:
        lines.append(f"UPDATE `creature_model_info` SET `BoundingRadius` = {radius}, `CombatReach` = {reach} "
                     f"WHERE `DisplayID` = {display};")
    return "\n".join(lines)


# --- The water disc's missing second texture --------------------------------------------------------------------


def set_texture_name(data: bytes, index: int, expected_old: str, new: str) -> bytes:
    """The M2's hard-coded texture `index` renamed in place (the name must fit the old name's bytes). The entry's length
    counts the new name and its terminator, as Blizzard's files do. Raises SystemExit when the old name is not the one
    this patch was written for."""
    count, ofs = struct.unpack_from("<II", data, 0x50)
    if not 0 <= index < count:
        raise SystemExit(f"the model has {count} texture(s), no index {index}")
    entry = ofs + 16 * index
    tex_type, _, name_len, name_ofs = struct.unpack_from("<IIII", data, entry)
    if tex_type != 0:
        raise SystemExit(f"texture {index} is type {tex_type}, not a hard-coded path")
    old = data[name_ofs:name_ofs + name_len].split(b"\0", 1)[0].decode("ascii")
    if old.lower() == new.lower():
        return data
    if old.lower() != expected_old.lower():
        raise SystemExit(f"texture {index} is {old!r}, expected {expected_old!r}")
    raw = new.encode("ascii") + b"\0"
    if len(raw) > name_len:
        raise SystemExit(f"{new!r} does not fit the {name_len} bytes of {old!r}")
    out = bytearray(data)
    out[name_ofs:name_ofs + name_len] = raw + bytes(name_len - len(raw))
    struct.pack_into("<I", out, entry + 8, len(raw))
    return bytes(out)


def fix_water_disc(data: bytes) -> bytes:
    """`target_water_state_projected.m2` with its second texture re-pointed to the shipped targetarea_everybase."""
    return set_texture_name(data, 1, WATER_MISSING_TEXTURE, WATER_FIXED_TEXTURE)


def texture_names(data: bytes) -> list[str]:
    """The hard-coded (type 0) texture paths of an M2, in texture order."""
    count, ofs = struct.unpack_from("<II", data, 0x50)
    names = []
    for i in range(count):
        tex_type, _, name_len, name_ofs = struct.unpack_from("<IIII", data, ofs + 16 * i)
        if tex_type == 0:
            names.append(data[name_ofs:name_ofs + name_len].split(b"\0", 1)[0].decode("ascii"))
    return names


def _load_visuals():
    """source/npcs/zul_farrak/_visuals.py by path (source/ is not a package): the ids the boss files use."""
    path = Path(__file__).resolve().parent / "source" / "npcs" / "zul_farrak" / "_visuals.py"
    spec = importlib.util.spec_from_file_location("zul_farrak_visuals", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_stock_ids() -> list[str]:
    """Confirms every stock or shipped id `_visuals.py` names (and the stock rows and models this script reuses)
    exists in the working copy; returns one-line notes."""
    visuals = _load_visuals()
    _stock("SpellVisual.dbc", dbcfmt.SPELLVISUAL, set(visuals.STOCK_SPELL_VISUALS) | set(visuals.SHIPPED_SPELL_VISUALS))
    effects = _stock("SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME,
                     {STOCK_LIGHTNING_SHIELD_EFFECT, RFC_BLADES_EFFECT})
    if effects[STOCK_LIGHTNING_SHIELD_EFFECT]["FileName"].lower() != STOCK_LIGHTNING_SHIELD_FILE:
        raise SystemExit(f"stock SVEN {STOCK_LIGHTNING_SHIELD_EFFECT} is not {STOCK_LIGHTNING_SHIELD_FILE}")
    if effects[RFC_BLADES_EFFECT]["FileName"].lower() != BLADES_FILE:
        raise SystemExit(f"SVEN {RFC_BLADES_EFFECT} (Ragefire Chasm's blades) is not {BLADES_FILE}")
    _stock("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, {STORM_STRIKE_INSTANT_KIT})
    _stock_pose_kits()
    _stock("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, set(visuals.STOCK_CREATURE_DISPLAYS))
    _stock("GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO, set(visuals.STOCK_GAMEOBJECT_DISPLAYS))
    return [f"{len(set(visuals.STOCK_SPELL_VISUALS))} stock + {len(set(visuals.SHIPPED_SPELL_VISUALS))} shipped "
            f"SpellVisual ids, {len(visuals.STOCK_CREATURE_DISPLAYS)} CreatureDisplayInfo ids and "
            f"{len(visuals.STOCK_GAMEOBJECT_DISPLAYS)} GameObjectDisplayInfo ids exist (plus the stock kits and the "
            f"two effect models the rows reuse)"]


def _same_row(a: dict, b: dict) -> bool:
    """The rows are equal, with floats compared as the DBC stores them (float32: 0.01 reads back as 0.00999...)."""
    return a.keys() == b.keys() and all(
        math.isclose(a[k], b[k], rel_tol=1e-6, abs_tol=1e-7) if isinstance(a[k], float) else a[k] == b[k] for k in a)


def check_no_collisions() -> None:
    """The ids this script mints must be free in the working copy or already equal to its own rows (a merge replaces
    rows silently, so a foreign row in a reserved block would be lost)."""
    for filename, table, builder, block in (
            ("SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME, build_effect_name_rows, VISUAL_BLOCK),
            ("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, build_kit_rows, VISUAL_BLOCK),
            ("SpellVisual.dbc", dbcfmt.SPELLVISUAL, build_spellvisual_rows, VISUAL_BLOCK),
            ("CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA, build_creature_model_rows, DISPLAY_BLOCK),
            ("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, build_creature_display_rows, DISPLAY_BLOCK)):
        mine = {r["ID"]: r for r in builder()}
        for row in dbcfile.read_dbc(DBC_DIR / filename, table):
            if row["ID"] in mine and not _same_row(row, mine[row["ID"]]):
                raise SystemExit(f"{filename}: id {row['ID']} already holds a different row")
            if block["start"] <= row["ID"] <= block["end"] and row["ID"] not in mine:
                raise SystemExit(f"{filename}: foreign row {row['ID']} inside the zul_farrak block")


def build_pending_sql() -> str:
    """Server-side overlay: SpellVisual, CreatureModelData and CreatureDisplayInfo (the other tables are client-only)
    plus the creature_model_info rows. Range-deletes exactly the ids this script spans, so a rerun is idempotent."""
    rows = build_spellvisual_rows()
    ids = [r["ID"] for r in rows]
    # The DBC holds signed columns (MissileAttachment -1) as unsigned; the server column is a signed int.
    rows = [{k: (v - (1 << 32) if isinstance(v, int) and v >= 1 << 31 else v) for k, v in r.items()} for r in rows]
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
            raise SystemExit(f"{what} id {row['ID']} is outside the zul_farrak block {block}")


def extract_assets() -> None:
    """Pulls the Ascension assets (read-only backup) into the working copy (files already present are kept) and
    applies the water disc's texture edit to the working copy's model."""
    added = 0
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        for archive, path in SPELLS_ASSETS:
            dest = SPELLS_DIR / Path(path).name
            if not dest.is_file():
                _extract_one(archive, path, dest, workdir)
                added += 1
    print(f"extracted {added} asset(s) from {ASCENSION_DATA} (0 means everything was already there)")
    water = SPELLS_DIR / f"{MODEL_WATER_DISC}.m2"
    before = water.read_bytes()
    after = fix_water_disc(before)
    if after != before:
        water.write_bytes(after)
        print(f"re-pointed the second texture of {water.name} to {WATER_FIXED_TEXTURE}")


def _water_disc_dry_run() -> str:
    """Reports the edit the water disc needs without writing anything (reads the working copy, else the backup)."""
    working = SPELLS_DIR / f"{MODEL_WATER_DISC}.m2"
    if working.is_file():
        source = "working copy"
        data = working.read_bytes()
    else:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "water.m2"
            try:
                _extract_one("patch-N", f"SPELLS/{MODEL_WATER_DISC}.m2", dest, Path(tmp))
            except (OSError, SystemExit, Exception) as exc:  # noqa: BLE001 - report, never fail a dry run on this
                return f"water disc edit: not checked (no working copy, backup unreadable: {exc})"
            data = dest.read_bytes()
        source = "Ascension backup"
    before = texture_names(data)
    after = texture_names(fix_water_disc(data))
    return f"water disc edit ({source}): textures {before} -> {after}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sql-out", type=Path, default=None,
                        help="Write the matching server-side SQL migration to this path (see module docstring).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the rows, the stock-id and asset checks and the SQL; write nothing.")
    parser.add_argument("--extract", action="store_true",
                        help="Pull the missing assets from the Ascension backup into the working copy, apply the "
                             "water disc edit, then stop.")
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
    model_rows = build_creature_model_rows()
    display_rows = build_creature_display_rows()
    for rows, what, block in ((effect_rows, "SpellVisualEffectName", VISUAL_BLOCK), (kit_rows, "SpellVisualKit",
                                                                                     VISUAL_BLOCK),
                              (visual_rows, "SpellVisual", VISUAL_BLOCK),
                              (model_rows, "CreatureModelData", DISPLAY_BLOCK),
                              (display_rows, "CreatureDisplayInfo", DISPLAY_BLOCK)):
        _check_block(rows, block, what)

    if args.dry_run:
        for note in check_stock_ids():
            print("stock:", note)
        check_no_collisions()
        print("no foreign row in the minted id blocks of the working copy")
        print(_water_disc_dry_run())
        for row in effect_rows:
            print("SpellVisualEffectName:", row)
        for row in kit_rows:
            print("SpellVisualKit (non-zero fields):", {k: v for k, v in row.items() if v and v != 4294967295})
        for row in visual_rows:
            print("SpellVisual (non-zero fields):", {k: v for k, v in row.items() if v})
        for row in model_rows:
            print("CreatureModelData:", {k: v for k, v in row.items() if v})
        for row in display_rows:
            print("CreatureDisplayInfo:", {k: v for k, v in row.items() if v})
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
    added += _merge(DBC_DIR / "CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA, model_rows)
    added += _merge(DBC_DIR / "CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, display_rows)
    print(f"added {added} row(s) across the 5 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
