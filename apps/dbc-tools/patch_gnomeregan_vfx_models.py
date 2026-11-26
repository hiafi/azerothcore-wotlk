#!/usr/bin/env python3
"""
One-off DBC content patch: the client visuals the reworked Gnomeregan bosses need (Gnomeregan build, WP V; handoff
.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.10 and appendix C, picks VISUALS-REPORT.md "Part 2: new
rows"). Same shape as patch_zul_farrak_vfx_models.py (whose row helpers and asset extraction it shares).

ID blocks (ids.yaml reservation `gnomeregan`):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: 90750-90799. Used: SpellVisual 90750-90753; Kit 90751, 90752,
  90753; EffectName 90751. (90750 reuses SV 854's stock kits; 90752 copies SV 8083's cast kit by id.)
- CreatureModelData / CreatureDisplayInfo: 90850-90869. Used: CDI 90850-90856; CMD 90850 and 90853-90856 (90851 and
  90852 are GnomeBomBot skins on the stock model 851, so they have a display row and no model row).
- SoundEntries: 90151-90160. Used: 90151, 90152 (the geiger ticks).
- GameObjectDisplayInfo (90075-90079): none minted.

What it mints (every look unconfirmed until seen in game; scales are first guesses, one number each):
- SV 90750 arcing glob: a copy of stock SV 854 (Acid Spit: GooBolt missile and its kits) with MissilePathType 2, the arc
  SV 8824's incendiary bomb uses. Fallback SV 854.
- SV 90751 big Voltage / Safe Mode State: StateKit, BaseEffect = the stock LightningShield_State_Base model at scale
  5.0, sound 3256 (stock SV 37 is the same model at 0.3 yd). Fallback SV 37 / 7867.
- SV 90752 punch pose: a copy of stock SV 8083 (Gruul's Ground Slam: ThunderClap ring, shake 6) whose precast kit is a
  copy of kit 6908 with AnimID 118 (SpecialUnarmed, absent on GnomeBot) changed to 16 (AttackUnarmed, the one punch
  GnomeBot has). Fallback SV 8083 and an emote.
- SV 90753 alarm pulse: InstantAreaKit = a ThunderClap_Cast_Base ring (the model SV 2074's area kit uses) plus sound
  5763 (the alert bot loop). Fallback SV 2074.
- CMD + CDI 90850: the Ascension nature disc `target_nature_state_projected` (a 9.6 yd quad, textures
  targetarea_naturea and targetarea_everybase, both in patch-N): creature scale = radius / 4.8.
- CDI 90851 / 90852: stock GnomeBomBot (model 851) in the GnomeSpiderTankSkinGreen / Blue skins at display scale 0.5
  (copies of stock row 6977, the red 0.5 one). Model info 0.75 / 1.0.
- CMD + CDI 90853-90855: numeral quads 1, 2, 3, built like the BM markers (patch_bossmechanics_markers: the source
  quad model patched to a 4-vertex quad, projected texture, DXT5 BLP) with a digit alpha plane drawn here (a stroke
  glyph, white, the model's own tint white). --extract writes models, skins and textures into the working copy; the
  source quad comes from var/bossmech-src (the BM script's --extract).
- CMD + CDI 90856: the Ascension light cone `custom_cone_white` (a flat 44.4 yd quad, soft white cone texture,
  scale 0.79 for 30 yd). Optional; the BM cone is the fallback.
- SoundEntries 90151 / 90152: Ascension patch-O `fx_timer_tick_2click` / `4click` (ogg converted to wav like the rogue
  rows). Optional; stock 11757 is the fallback.

SpellVisual, CreatureModelData and CreatureDisplayInfo are server-loaded, so `--sql-out PATH` emits their overlay
(SpellVisualKit, SpellVisualEffectName and SoundEntries are client-only) plus the creature_model_info rows: the discs,
numerals and cone (radius 0.5, reach 0.5: flat, so melee targeting does not see them) and the two bombs (0.75 / 1.0).
No stock display's size is edited (RB-10 check, live SELECT 2026-11-26): 7288, 3233, 5497, 6915, 6888, 6967, 6968,
6982, 6981, 6774, 6980, 6977, 19139, 6271 and 6973-6976 all hold a non-zero row; 6774 stays untouched on purpose (the
window ruling: the display is shared by four creatures). The one zero row, stock 21209 (a blue GnomeBomBot at 0.35),
is only the optional alternate to 90852 and is NOT touched: if a boss ever wears it, add the row then.

Assets (gitignored working copies; `--extract` pulls them from the read-only Ascension backup into
var/model-visual-dbc/SPELLS/ and SOUND/, where build_patch_m.py packs them into patch-M, and draws the numerals):
2 models, their 2 skins and 4 textures from patch-N, 2 ogg files from patch-O converted to wav, and the three numeral
models, skins and textures. If an Ascension file is missing in the backup, --extract stops with its name; every row has
a stock fallback and the boss files wire it with one constant (`*_FALLBACK` / `*_ALT` in _visuals.py). The discs'
fallback is the BM marker circle. targetarea_everybase.blp is shared with Zul'Farrak's water disc: --extract keeps a
file that is already there.

Usage:
    cd apps/dbc-tools
    python3 patch_gnomeregan_vfx_models.py --extract     # once: pull the Ascension assets, draw the numerals
    python3 patch_gnomeregan_vfx_models.py --dry-run     # print rows + checks + SQL, write nothing
    python3 patch_gnomeregan_vfx_models.py --sql-out ../../data/sql/updates/pending_db_world/rev_<ts>.sql
then build_patch_m.py (patch-M.mpq carries the DBCs, SPELLS\\ and SOUND\\). The orchestrator runs the last two at
deploy.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import subprocess
import tempfile
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.blp_write import encode_blp
from lib.m2_patch import patch_model, patch_skin
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, _kit_row, _merge, _row, _sound_row, model_path
from patch_rogue_vfx_models import ASCENSION_DATA, NO_ATTACHMENT, SOUND_DIR, SPELLS_DIR, _extract_one
import patch_bossmechanics_markers as bm

# Gnomeregan blocks (ids.yaml `reservations: gnomeregan:`).
VISUAL_BLOCK = {"start": 90750, "end": 90799}
DISPLAY_BLOCK = {"start": 90850, "end": 90869}
SOUND_BLOCK = {"start": 90151, "end": 90160}

# --- SpellVisual ids (SpellVisual = Kit = EffectName number where they have them) ---
SV_ARCING_GLOB = 90750
SV_BIG_VOLTAGE = 90751
SV_PUNCH_POSE = 90752
SV_ALARM_PULSE = 90753

# --- SpellVisualKit ids: the SpellVisual numbers where a kit is new ---
KIT_BIG_VOLTAGE = 90751
KIT_PUNCH_PRECAST = 90752
KIT_ALARM_PULSE = 90753

# --- SpellVisualEffectName ids ---
EFFECT_BIG_VOLTAGE = 90751

# --- CreatureModelData / CreatureDisplayInfo ids ---
CDI_NATURE_DISC = 90850
CDI_BOMB_RADIO = 90851
CDI_BOMB_FROST = 90852
CDI_NUMERAL_1 = 90853
CDI_NUMERAL_2 = 90854
CDI_NUMERAL_3 = 90855
CDI_LIGHT_CONE = 90856
CMD_NATURE_DISC = 90850
CMD_NUMERAL_1 = 90853
CMD_NUMERAL_2 = 90854
CMD_NUMERAL_3 = 90855
CMD_LIGHT_CONE = 90856

# --- SoundEntries ids ---
SOUND_GEIGER_2 = 90151
SOUND_GEIGER_4 = 90152

# --- Scales (first guesses; tune in game, one number each) ---
BIG_VOLTAGE_SCALE = 5.0                # LightningShield_State_Base (0.3 yd) on a 3 yd bot or tank: 4 to 6
BIG_VOLTAGE_SOUND = 3256               # stock SV 37's kit sound
ALARM_PULSE_SOUND = 5763               # GnomeAlertBotLoop
PUNCH_ANIM_OLD = 118                   # SpecialUnarmed: absent on GnomeBot
PUNCH_ANIM_NEW = 16                    # AttackUnarmed: the punch GnomeBot has (1.67 s)
MISSILE_PATH_ARC = 2                   # SV 8824's MissilePathType
BOMB_DISPLAY_SCALE = 0.5               # as stock 6977
BOMB_MODEL = 851                       # CreatureModelData 851, GnomeBomBot.mdx
BOMB_SKIN_GREEN = "GnomeSpiderTankSkinGreen"
BOMB_SKIN_BLUE = "GnomeSpiderTankSkinBlue"

# Rows this script reuses by id (--dry-run verifies them in the working copy).
STOCK_LIGHTNING_SHIELD_EFFECT = 296    # SVEN `Spells\\LightningShield_State_Base.mdx`
STOCK_LIGHTNING_SHIELD_FILE = "spells\\lightningshield_state_base.mdx"
STOCK_THUNDERCLAP_EFFECT = 349         # SVEN `Spells\\ThunderClap_Cast_Base.mdx`
STOCK_THUNDERCLAP_FILE = "spells\\thunderclap_cast_base.mdx"
STOCK_BOMB_DISPLAY = 6977              # the red 0.5 GnomeBomBot display the green and blue rows copy
GLOB_SOURCE_SV = 854
PUNCH_SOURCE_SV = 8083
PUNCH_SOURCE_PRECAST_KIT = 6908        # stock kit with AnimID 118, SV 8083's precast

# --- Assets: (archive, path in the archive) ---
MODEL_NATURE_DISC = "target_nature_state_projected"
MODEL_LIGHT_CONE = "custom_cone_white"
MODELS = (MODEL_NATURE_DISC, MODEL_LIGHT_CONE)
NATURE_DISC_TEXTURES = ("targetarea_naturea", "targetarea_everybase")
LIGHT_CONE_TEXTURES = ("9fx_generic_titan_precast_cone_base_3948565",)
TEXTURES = (*NATURE_DISC_TEXTURES, *LIGHT_CONE_TEXTURES)
# The models' hard-coded texture names, in texture order (read from the Ascension M2s; pinned by the test).
MODEL_TEXTURES = {MODEL_NATURE_DISC: NATURE_DISC_TEXTURES, MODEL_LIGHT_CONE: LIGHT_CONE_TEXTURES}
SPELLS_ASSETS = [
    *[("patch-N", f"SPELLS/{model}.m2") for model in MODELS],
    *[("patch-N", f"SPELLS/{model}00.skin") for model in MODELS],
    *[("patch-N", f"SPELLS/{name}.blp") for name in TEXTURES],
]
# SoundEntries id -> (archive directory, file stems): converted .ogg -> .wav into SOUND/ (packed at Sound\\Spells\\).
SOUND_ARCHIVE = "patch-O"
SOUND_FILES = {
    SOUND_GEIGER_2: ("sound/spells", ["fx_timer_tick_2click"]),
    SOUND_GEIGER_4: ("sound/spells", ["fx_timer_tick_4click"]),
}
# The numeral quads drawn here: display id, digit.
NUMERALS = ((CDI_NUMERAL_1, 1), (CDI_NUMERAL_2, 2), (CDI_NUMERAL_3, 3))
NUMERAL_WORDS = {1: "one", 2: "two", 3: "three"}
NUMERAL_PREFIX = "gnomer_numeral_"      # + the word: gnomer_numeral_one.m2 and gnomer_numeral_one00.skin
NUMERAL_TEXTURE_SIZE = 256
NUMERAL_GLYPH_FRAC = 0.70              # glyph height as a fraction of the texture side (rows 0.15 to 0.85)
NUMERAL_STROKE_FRAC = 0.075            # half the stroke width, as a fraction of the side
NUMERAL_FLIP = False                   # True turns every digit 180 degrees (if a playtest reads them upside down)
# Digit centerlines in a unit square (x right, y down); the glyph spans y 0.15 to 0.85 and x about 0.30 to 0.70.
NUMERAL_STROKES = {
    1: (((0.50, 0.15), (0.50, 0.85)), ((0.50, 0.15), (0.36, 0.30)), ((0.34, 0.85), (0.66, 0.85))),
    2: (((0.30, 0.30), (0.34, 0.21), (0.50, 0.15), (0.66, 0.21), (0.71, 0.32), (0.64, 0.46), (0.30, 0.85),
         (0.72, 0.85)),),
    3: (((0.29, 0.22), (0.50, 0.15), (0.69, 0.23), (0.69, 0.40), (0.48, 0.50), (0.69, 0.60), (0.71, 0.77),
         (0.50, 0.85), (0.28, 0.78)),),
}

# creature_model_info (server only), (DisplayID, BoundingRadius, CombatReach, Gender, DisplayID_Other_Gender).
# The flat displays use radius and reach 0.5 (melee targeting must not see them; gender 2, none, like every
# object-like display); the bombs 0.75 / 1.0 (as stock 6977).
FLAT_MODEL_INFO = tuple((display, 0.5, 0.5) for display in
                        (CDI_NATURE_DISC, CDI_NUMERAL_1, CDI_NUMERAL_2, CDI_NUMERAL_3, CDI_LIGHT_CONE))
BOMB_MODEL_INFO = ((CDI_BOMB_RADIO, 0.75, 1.0), (CDI_BOMB_FROST, 0.75, 1.0))
MODEL_INFO = (FLAT_MODEL_INFO[0], *BOMB_MODEL_INFO, *FLAT_MODEL_INFO[1:])


def numeral_model(digit: int) -> str:
    return f"{NUMERAL_PREFIX}{NUMERAL_WORDS[digit]}"


def _asset_paths() -> list[Path]:
    paths = [SPELLS_DIR / Path(p).name for _, p in SPELLS_ASSETS]
    for _, digit in NUMERALS:
        paths += [SPELLS_DIR / f"{numeral_model(digit)}.m2", SPELLS_DIR / f"{numeral_model(digit)}00.skin",
                  SPELLS_DIR / f"{numeral_model(digit)}.blp"]
    paths += [SOUND_DIR / f"{stem}.wav" for _, stems in SOUND_FILES.values() for stem in stems]
    return paths


def _effect_rows() -> list[tuple[int, str, str, float]]:
    """(id, name, FileName, scale) of every effect; AreaEffectSize 0 on all of them (a fixed size, not the radius)."""
    return [(EFFECT_BIG_VOLTAGE, "Big Voltage State", "Spells\\LightningShield_State_Base.mdx", BIG_VOLTAGE_SCALE)]


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
    """The big Voltage state kit, the punch precast (a copy of stock kit 6908 with the AnimID GnomeBot has) and the
    alarm pulse area kit. Sorted by id."""
    stock = _stock("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, {PUNCH_SOURCE_PRECAST_KIT})[PUNCH_SOURCE_PRECAST_KIT]
    if stock["AnimID"] != PUNCH_ANIM_OLD:
        raise SystemExit(f"stock kit {PUNCH_SOURCE_PRECAST_KIT} has AnimID {stock['AnimID']}, "
                         f"expected {PUNCH_ANIM_OLD}")
    punch = dict(stock)
    punch["ID"] = KIT_PUNCH_PRECAST
    punch["AnimID"] = PUNCH_ANIM_NEW
    rows = [
        _kit_row(KIT_BIG_VOLTAGE, BaseEffect=EFFECT_BIG_VOLTAGE, SoundID=BIG_VOLTAGE_SOUND),
        punch,
        _kit_row(KIT_ALARM_PULSE, WorldEffect=STOCK_THUNDERCLAP_EFFECT, SoundID=ALARM_PULSE_SOUND),
    ]
    return sorted(rows, key=lambda r: r["ID"])


def build_spellvisual_rows() -> list[dict]:
    stock = _stock("SpellVisual.dbc", dbcfmt.SPELLVISUAL, {GLOB_SOURCE_SV, PUNCH_SOURCE_SV})
    glob = dict(stock[GLOB_SOURCE_SV])
    glob["ID"] = SV_ARCING_GLOB
    glob["MissilePathType"] = MISSILE_PATH_ARC
    voltage = _row(dbcfmt.SPELLVISUAL, SV_BIG_VOLTAGE, MissileAttachment=NO_ATTACHMENT)
    voltage["StateKit"] = KIT_BIG_VOLTAGE
    punch = dict(stock[PUNCH_SOURCE_SV])
    punch["ID"] = SV_PUNCH_POSE
    punch["PrecastKit"] = KIT_PUNCH_PRECAST
    pulse = _row(dbcfmt.SPELLVISUAL, SV_ALARM_PULSE, MissileAttachment=NO_ATTACHMENT)
    pulse["InstantAreaKit"] = KIT_ALARM_PULSE
    return sorted([glob, voltage, punch, pulse], key=lambda r: r["ID"])


def _flat_model_row(cmd: int, model: str) -> dict:
    return _row(dbcfmt.CREATUREMODELDATA, cmd, Flags=0, ModelName=model_path(model), ModelScale=1.0, SizeClass=1,
                BloodID=1, FootprintParticleScale=1.0, WorldEffectScale=1.0, AttachedEffectScale=1.0)


def build_creature_model_rows() -> list[dict]:
    """The nature disc, the three numeral quads and the light cone: flat quads used as creature models, Flags /
    SizeClass / BloodID as the proven-live marker rows, no collision box."""
    rows = [_flat_model_row(CMD_NATURE_DISC, MODEL_NATURE_DISC)]
    rows += [_flat_model_row(cmd, numeral_model(digit))
             for cmd, (_, digit) in zip((CMD_NUMERAL_1, CMD_NUMERAL_2, CMD_NUMERAL_3), NUMERALS)]
    rows.append(_flat_model_row(CMD_LIGHT_CONE, MODEL_LIGHT_CONE))
    return rows


def _display_row(cdi: int, cmd: int, **fields) -> dict:
    return _row(dbcfmt.CREATUREDISPLAYINFO, cdi, ModelID=cmd, CreatureModelScale=1.0, CreatureModelAlpha=255,
                BloodLevel=1, **fields)


def build_creature_display_rows() -> list[dict]:
    """The seven displays: the discs and quads are model-scale 1.0, the two bombs copy stock row 6977 (model 851 at
    0.5) with their own skin."""
    bomb = _stock("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, {STOCK_BOMB_DISPLAY})[STOCK_BOMB_DISPLAY]
    if bomb["ModelID"] != BOMB_MODEL or abs(bomb["CreatureModelScale"] - BOMB_DISPLAY_SCALE) > 1e-6:
        raise SystemExit(f"stock display {STOCK_BOMB_DISPLAY} is not model {BOMB_MODEL} at {BOMB_DISPLAY_SCALE}")
    rows = [_display_row(CDI_NATURE_DISC, CMD_NATURE_DISC)]
    for cdi, skin in ((CDI_BOMB_RADIO, BOMB_SKIN_GREEN), (CDI_BOMB_FROST, BOMB_SKIN_BLUE)):
        row = dict(bomb)
        row["ID"] = cdi
        row["TextureVariation_1"] = skin
        rows.append(row)
    for (cdi, digit), cmd in zip(NUMERALS, (CMD_NUMERAL_1, CMD_NUMERAL_2, CMD_NUMERAL_3)):
        rows.append(_display_row(cdi, cmd, TextureVariation_1=numeral_model(digit)))
    rows.append(_display_row(CDI_LIGHT_CONE, CMD_LIGHT_CONE))
    return sorted(rows, key=lambda r: r["ID"])


def build_sound_rows() -> list[dict]:
    """The two geiger ticks, set like stock 11757 (SimonGame_Visual_GameTick: volume 0.69, distance 7 to 30)."""
    names = {SOUND_GEIGER_2: "Gnomeregan Geiger Tick 2 (Custom)", SOUND_GEIGER_4: "Gnomeregan Geiger Tick 4 (Custom)"}
    rows = []
    for id_, (_, stems) in SOUND_FILES.items():
        row = _sound_row(id_, names[id_], stems, min_distance=7.0, cutoff=30.0)
        row["Volumefloat"] = 0.69
        row["SoundType"] = 1
        rows.append(row)
    return rows


def build_creature_model_info_sql() -> str:
    """The `creature_model_info` rows (idempotent: deletes the seven ids first)."""
    ids = ", ".join(str(display) for display, _, _ in MODEL_INFO)
    values = ",\n".join(f"({display}, {radius}, {reach}, 2, 0)" for display, radius, reach in MODEL_INFO)
    return "\n".join([f"DELETE FROM `creature_model_info` WHERE `DisplayID` IN ({ids});",
                      "INSERT INTO `creature_model_info` (`DisplayID`, `BoundingRadius`, `CombatReach`, `Gender`, "
                      f"`DisplayID_Other_Gender`) VALUES\n{values};"])


# --- The numeral glyphs -----------------------------------------------------------------------------------------------


def _segment_distance(px: float, py: float, a: tuple[float, float], b: tuple[float, float]) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def numeral_alpha(digit: int, size: int = NUMERAL_TEXTURE_SIZE) -> bytes:
    """The alpha plane of one numeral: opaque white strokes with an antialiased edge, transparent elsewhere. Row 0 is
    the top of the image; NUMERAL_FLIP turns the glyph 180 degrees."""
    segments = []
    for stroke in NUMERAL_STROKES[digit]:
        for a, b in zip(stroke, stroke[1:]):
            segments.append((a, b))
    half = NUMERAL_STROKE_FRAC * size

    def alpha(row: float, col: float) -> float:
        # _plane hands in pixel offsets from the center: row (down) and column (right)
        if NUMERAL_FLIP:
            row, col = -row, -col
        px = (col + size / 2.0) / size
        py = (row + size / 2.0) / size
        dist = min(_segment_distance(px, py, a, b) for a, b in segments) * size
        return 255.0 * bm._cov(dist - half)

    return bm._plane(size, alpha)


def build_numeral_assets(src_model: bytes, src_skin: bytes) -> dict[str, bytes]:
    """{file name: bytes} for the three numeral models, skins and textures (white quads, the BM recipe)."""
    files: dict[str, bytes] = {}
    for _, digit in NUMERALS:
        stem = numeral_model(digit)
        files[f"{stem}.m2"] = patch_model(src_model, bm.QUAD, skins=False, texture_path=f"spells\\{stem}.blp",
                                          rgb=(1.0, 1.0, 1.0))
        files[f"{stem}00.skin"] = patch_skin(src_skin, bm.QUAD)
        files[f"{stem}.blp"] = encode_blp(NUMERAL_TEXTURE_SIZE, NUMERAL_TEXTURE_SIZE, bm.WHITE, numeral_alpha(digit),
                                          clear_cols=True, clear_rows=True)
    return files


def _numeral_source() -> tuple[bytes, bytes]:
    model, skin, _ = bm.read_source(bm.DEFAULT_VAR / "bossmech-src")
    return model, skin


# --- Checks -----------------------------------------------------------------------------------------------------------


def _load_visuals():
    """source/npcs/gnomeregan/_visuals.py by path (source/ is not a package): the ids the boss files use."""
    path = Path(__file__).resolve().parent / "source" / "npcs" / "gnomeregan" / "_visuals.py"
    spec = importlib.util.spec_from_file_location("gnomeregan_visuals", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_stock_ids() -> list[str]:
    """Confirms every stock or shipped id `_visuals.py` names (and the stock rows and models this script reuses)
    exists in the working copy; returns one-line notes."""
    visuals = _load_visuals()
    _stock("SpellVisual.dbc", dbcfmt.SPELLVISUAL, set(visuals.STOCK_SPELL_VISUALS) | set(visuals.SHIPPED_SPELL_VISUALS))
    effects = _stock("SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME,
                     {STOCK_LIGHTNING_SHIELD_EFFECT, STOCK_THUNDERCLAP_EFFECT})
    for effect, wanted in ((STOCK_LIGHTNING_SHIELD_EFFECT, STOCK_LIGHTNING_SHIELD_FILE),
                           (STOCK_THUNDERCLAP_EFFECT, STOCK_THUNDERCLAP_FILE)):
        if effects[effect]["FileName"].lower() != wanted:
            raise SystemExit(f"stock SVEN {effect} is not {wanted}")
    _stock("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, {PUNCH_SOURCE_PRECAST_KIT})
    _stock("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, set(visuals.STOCK_CREATURE_DISPLAYS))
    _stock("GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO, set(visuals.STOCK_GAMEOBJECT_DISPLAYS))
    _stock("SoundEntries.dbc", dbcfmt.SOUNDENTRIES, set(visuals.STOCK_SOUNDS))
    _stock("CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA, {BOMB_MODEL})
    return [f"{len(set(visuals.STOCK_SPELL_VISUALS))} stock + {len(set(visuals.SHIPPED_SPELL_VISUALS))} shipped "
            f"SpellVisual ids, {len(visuals.STOCK_CREATURE_DISPLAYS)} CreatureDisplayInfo ids, "
            f"{len(visuals.STOCK_GAMEOBJECT_DISPLAYS)} GameObjectDisplayInfo ids and {len(visuals.STOCK_SOUNDS)} "
            f"SoundEntries ids exist (plus the stock kits, effect models and model 851 the rows reuse)"]


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
            ("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, build_creature_display_rows, DISPLAY_BLOCK),
            ("SoundEntries.dbc", dbcfmt.SOUNDENTRIES, build_sound_rows, SOUND_BLOCK)):
        mine = {r["ID"]: r for r in builder()}
        for row in dbcfile.read_dbc(DBC_DIR / filename, table):
            if row["ID"] in mine and not _same_row(row, mine[row["ID"]]):
                raise SystemExit(f"{filename}: id {row['ID']} already holds a different row")
            if block["start"] <= row["ID"] <= block["end"] and row["ID"] not in mine:
                raise SystemExit(f"{filename}: foreign row {row['ID']} inside the gnomeregan block")


def _signed(rows: list[dict]) -> list[dict]:
    """The DBC holds signed columns (MissileAttachment -1, a stock display's BloodLevel -1) as unsigned; the server
    columns are signed ints, so 4294967295 would overflow."""
    return [{k: (v - (1 << 32) if isinstance(v, int) and v >= 1 << 31 else v) for k, v in r.items()} for r in rows]


def build_pending_sql() -> str:
    """Server-side overlay: SpellVisual, CreatureModelData and CreatureDisplayInfo (the other tables are client-only)
    plus the creature_model_info rows. Range-deletes exactly the ids this script spans, so a rerun is idempotent."""
    blocks = []
    for table, builder in ((dbcfmt.SPELLVISUAL, build_spellvisual_rows),
                           (dbcfmt.CREATUREMODELDATA, build_creature_model_rows),
                           (dbcfmt.CREATUREDISPLAYINFO, build_creature_display_rows)):
        built = _signed(builder())
        built_ids = [r["ID"] for r in built]
        blocks.append(_table_block(table, {"start": min(built_ids), "end": max(built_ids)}, built, []))
    blocks.append(build_creature_model_info_sql())
    return "\n\n".join(blocks) + "\n"


def _check_block(rows: list[dict], block: dict, what: str) -> None:
    for row in rows:
        if not block["start"] <= row["ID"] <= block["end"]:
            raise SystemExit(f"{what} id {row['ID']} is outside the gnomeregan block {block}")


# --- Extraction -------------------------------------------------------------------------------------------------------


def extract_assets() -> None:
    """Pulls the Ascension assets (read-only backup) into the working copy (files already present are kept), converts
    the geiger ticks, and draws the numeral models, skins and textures."""
    added = 0
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        for archive, path in SPELLS_ASSETS:
            dest = SPELLS_DIR / Path(path).name
            if not dest.is_file():
                _extract_one(archive, path, dest, workdir)
                added += 1
        for directory, stems in SOUND_FILES.values():
            for stem in stems:
                dest = SOUND_DIR / f"{stem}.wav"
                if dest.is_file():
                    continue
                ogg = workdir / f"{stem}.ogg"
                _extract_one(SOUND_ARCHIVE, f"{directory}/{stem}.ogg", ogg, workdir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(ogg), "-acodec", "pcm_s16le",
                                str(dest)], check=True)
                added += 1
    src_model, src_skin = _numeral_source()
    for name, data in build_numeral_assets(src_model, src_skin).items():
        dest = SPELLS_DIR / name
        if not dest.is_file() or dest.read_bytes() != data:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            added += 1
    print(f"extracted or drew {added} asset(s) into {DBC_DIR.parent} (0 means everything was already there); "
          f"Ascension source {ASCENSION_DATA}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sql-out", type=Path, default=None,
                        help="Write the matching server-side SQL migration to this path (see module docstring).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the rows, the stock-id and asset checks and the SQL; write nothing.")
    parser.add_argument("--extract", action="store_true",
                        help="Pull the missing assets from the Ascension backup into the working copy, convert the "
                             "sounds, draw the numerals, then stop.")
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
    sound_rows = build_sound_rows()
    for rows, what, block in ((effect_rows, "SpellVisualEffectName", VISUAL_BLOCK), (kit_rows, "SpellVisualKit",
                                                                                     VISUAL_BLOCK),
                              (visual_rows, "SpellVisual", VISUAL_BLOCK),
                              (model_rows, "CreatureModelData", DISPLAY_BLOCK),
                              (display_rows, "CreatureDisplayInfo", DISPLAY_BLOCK),
                              (sound_rows, "SoundEntries", SOUND_BLOCK)):
        _check_block(rows, block, what)

    if args.dry_run:
        for note in check_stock_ids():
            print("stock:", note)
        check_no_collisions()
        print("no foreign row in the minted id blocks of the working copy")
        numerals = build_numeral_assets(*_numeral_source())
        print(f"numerals drawn in memory: {len(numerals)} files, "
              + ", ".join(f"{name} {len(data)} bytes" for name, data in numerals.items() if name.endswith('.blp')))
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
        for row in sound_rows:
            print("SoundEntries (non-empty fields):", {k: v for k, v in row.items() if v not in (0, 0.0, "")})
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
    added += _merge(DBC_DIR / "SoundEntries.dbc", dbcfmt.SOUNDENTRIES, sound_rows)
    print(f"added {added} row(s) across the 6 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
