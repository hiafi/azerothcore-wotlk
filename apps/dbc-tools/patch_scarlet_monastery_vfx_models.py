#!/usr/bin/env python3
"""
One-off DBC content patch: the client visuals the reworked Scarlet Monastery bosses need (Scarlet Monastery build, WP V,
both waves built in one pass; handoff .agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.10 and
s7 #34, picks VISUALS-REPORT.md "Part 2: new rows"). Same shape as patch_blackrock_depths_vfx_models.py (whose row
helpers and asset extraction it shares).

ID blocks (ids.yaml reservation `scarlet_monastery`):
- SpellVisual / SpellVisualKit / SpellVisualEffectName: 90550-90599 (one number for all three; 90550-90564 used,
  90565-90599 spare for the tuning round).
- CreatureModelData / CreatureDisplayInfo 90800-90829 (90800-90807 used). The spectre displays reuse the stock
  CreatureModelData of the display they copy, so only 90805-90807 carry a CreatureModelData row.
- GameObjectDisplayInfo 90060-90069: none minted (every object look is a stock display); free.

What it mints (every look unconfirmed until seen in game; scales are first guesses, one number each):
- 90550-90553 Grave Rot pool rungs 7 / 8 / 9 / 10 yd (Ironspine, the Eye's pools): the stock `goo_flow_state` (a 47.8 yd
  quad; the Strat gut puddle SV 90505 is the 6 yd rung of the same model) at 0.25 * radius / 6, a STATE on a stalker.
- 90554 the hard mode red aura (Thalnos, the answered stones, the blood rite, Herod): the stock
  `deathknight_plaguestrikestatered` at 1.0, a STATE.
- 90555-90557 held seal glows on the Champion (Command, Righteousness, Justice; optional): the three stock seal impact
  models at 1.0 as STATE rows. Whether the client loops an impact model is untested: the fallback is a 3 s re-cast.
- 90558-90560 Emerald Dream mist 6 / 9 / 12 yd (Hollis Grey, +3 yd per page): the stock `LargeGreenRadiationFog`
  (particles, size unmeasured) at 1.5 / 2.25 / 3.0 as a STATE.
- 90561 Plague Cask cloud 8 yd (Kell; optional, stock SV 7184 first): the stock `GreenRadiationFog` at 3.0 as a STATE.
- 90562 the Consecrated Hall (Herod's hard mode, the whole floor): the stock `holyzone` at hall radius / 3.2 (the stock
  Strat rungs are 4 yd at 1.2 ... 8 yd at 2.5: 3.2 yd of radius per unit of scale), the hall radius being the pit plus
  the ledge ring (NAVMESH-REPORT, Herod: ledge ring out to r 25.5).
- 90563 / 90564 holy light pillars 3 yd / 6 yd (Herod's prayer; Penance and the father's light): the Ascension
  `7fx_lightforged_vindicaar_lightsjudgement_impact` (2.9 yd wide, 15.8 yd tall, 7 particles, one looping state) at
  1.0 / 2.0. The stock Beam of Light SV 12479 is a 135 x 135 x 315 yd model: never wired.
- CDI 90800-90803 the spectre heroes (Galvar, Fairbell, Voss, Goodchilde): copies of CDI 25917 / 25842 / 10339 / 25841
  at CreatureModelAlpha 128 (the Agitated Orc Spirit / Azshir precedent). CDI 90804 the spectre of Alexandros: a copy
  of CDI 16139 at alpha 140. Each reuses its base display's CreatureModelData (HumanMale 49 / the mounted rider).
- CMD + CDI 90805 the Cursed Book (optional, stock CDI 28103 first) on the stock open book `BookLargeOpen02`;
  90806 the crimson Rallying Banner (optional, stock CDI 14541 first) on `CrimsonBanner01`; 90807 the Ravager
  (optional, untested: an item component model loaded as a creature model, stock GODI 8494 first) on
  `Axe_2H_War_C_01`.

SpellVisual, CreatureModelData and CreatureDisplayInfo are server-loaded, so `--sql-out PATH` emits their overlay
(SpellVisualKit and SpellVisualEffectName are client-only). The same file carries the `creature_model_info` row of every
minted display (bounding radius, combat reach): without one the creature can never spawn (Creature::InitEntry cancels
the load when ObjectMgr::GetCreatureModelRandomGender finds no row), and the rows must land in the same import as the
creaturedisplayinfo_dbc rows (ObjectMgr::LoadCreatureModelInfo dereferences the display row; a model-info row for a
display the DBC lacks crashes the boot).

Assets (gitignored working copies; `--extract` pulls them from the read-only Ascension backup into
var/model-visual-dbc/SPELLS/, where build_patch_m.py packs them into patch-M): one model, its skin and the 12 textures
it hard-codes.

Usage:
    cd apps/dbc-tools
    python3 patch_scarlet_monastery_vfx_models.py --extract     # once: pull the Ascension assets
    python3 patch_scarlet_monastery_vfx_models.py --dry-run     # print rows + checks + SQL, write nothing
    python3 patch_scarlet_monastery_vfx_models.py --sql-out ../../data/sql/updates/pending_db_world/rev_<ts>.sql
then build_patch_m.py (patch-M.mpq carries the DBCs and SPELLS\\). The orchestrator runs the last two at deploy.
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

# Scarlet Monastery blocks (ids.yaml `reservations: scarlet_monastery:`).
VISUAL_BLOCK = {"start": 90550, "end": 90599}
GODI_BLOCK = {"start": 90060, "end": 90069}
CREATURE_DISPLAY_BLOCK = {"start": 90800, "end": 90829}

# --- SpellVisual = SpellVisualKit = SpellVisualEffectName ids (one number each; every row is a StateKit BaseEffect) ---
SV_GRAVE_ROT = {7: 90550, 8: 90551, 9: 90552, 10: 90553}       # rung radius in yd -> id
SV_RED_AURA = 90554
SV_SEAL_COMMAND = 90555
SV_SEAL_RIGHTEOUSNESS = 90556
SV_SEAL_JUSTICE = 90557
SV_DREAM_MIST = {6: 90558, 9: 90559, 12: 90560}                # rung radius in yd -> id
SV_PLAGUE_CLOUD = 90561
SV_CONSECRATED_HALL = 90562
SV_PILLAR_3 = 90563
SV_PILLAR_6 = 90564

# --- CreatureModelData / CreatureDisplayInfo (same id; ids.yaml 90800-90829) ---
CDI_SPECTRE_GALVAR = 90800
CDI_SPECTRE_FAIRBELL = 90801
CDI_SPECTRE_VOSS = 90802
CDI_SPECTRE_GOODCHILDE = 90803
CDI_SPECTRE_ALEXANDROS = 90804
CMD_CURSED_BOOK = CDI_CURSED_BOOK = 90805
CMD_RALLYING_BANNER = CDI_RALLYING_BANNER = 90806
CMD_RAVAGER = CDI_RAVAGER = 90807

# (spectre display, the stock display it copies, alpha)
SPECTRES = (
    (CDI_SPECTRE_GALVAR, 25917, 128),
    (CDI_SPECTRE_FAIRBELL, 25842, 128),
    (CDI_SPECTRE_VOSS, 10339, 128),
    (CDI_SPECTRE_GOODCHILDE, 25841, 128),
    (CDI_SPECTRE_ALEXANDROS, 16139, 140),
)
SPECTRE_ALPHA = 128
ALEXANDROS_ALPHA = 140

# --- Scales (first guesses; tune in game, one number each) ---
GOO_QUAD_YARDS = 47.8                  # goo_flow_state at scale 1 (mesh bounds 47.8 x 47.6 x 0.1)
GRAVE_ROT_REFERENCE = (6, 0.25)        # the shipped Strat 6 yd rung: scale 0.25 for radius 6 -> scale = 0.25 * r / 6
GRAVE_ROT_RADII = (7, 8, 9, 10)
RED_AURA_SCALE = 1.0
SEAL_SCALE = 1.0
DREAM_MIST_SCALES = {6: 1.5, 9: 2.25, 12: 3.0}   # LargeGreenRadiationFog, particles only: tune in game
PLAGUE_CLOUD_SCALE = 3.0               # GreenRadiationFog: the stock "Cloud: Green - 3.00" row is the same scale
HOLYZONE_YARDS_PER_SCALE = 3.2         # the Strat rungs: 4 yd at 1.2, 5 at 1.5, 6 at 1.8, 8 at 2.5
HALL_RADIUS = 25.5                     # Herod's pit + ledge ring (NAVMESH-REPORT: ledge ring r 12.3 to 25.5)
HALL_SCALE = round(HALL_RADIUS / HOLYZONE_YARDS_PER_SCALE, 3)
PILLAR_SCALES = {SV_PILLAR_3: 1.0, SV_PILLAR_6: 2.0}   # 2.9 yd wide at 1.0
PILLAR_WIDTH_YARDS = 2.9
PILLAR_HEIGHT_YARDS = 15.8

# --- Stock models the rows reuse (verified by --dry-run to be named by a stock SpellVisualEffectName row) ---
STOCK_GOO_FILE = "SPELLS\\goo_flow_state.mdx"
STOCK_RED_AURA_FILE = "spells\\deathknight_plaguestrikestatered.mdx"    # stock SVEN 6283
STOCK_SEAL_COMMAND_FILE = "spells\\sealofcommand_impact_base.mdx"       # stock SVEN 3161
STOCK_SEAL_RIGHTEOUSNESS_FILE = "spells\\sealofrighteous_impact_base.mdx"   # stock SVEN 3155
STOCK_SEAL_JUSTICE_FILE = "Spells\\SealOfSalvation_Impact_Base.mdx"     # stock SVEN 430
STOCK_LARGE_MIST_FILE = "Spells\\LargeGreenRadiationFog.mdx"            # stock SVEN 2968
STOCK_CLOUD_FILE = "Spells\\GreenRadiationFog.mdx"                      # stock SVEN 1309
STOCK_HOLYZONE_FILE = "SPELLS\\holyzone.mdx"                            # the Strat rows' model (stock SVEN 6017)
STOCK_EFFECT_FILES = (STOCK_GOO_FILE, STOCK_RED_AURA_FILE, STOCK_SEAL_COMMAND_FILE, STOCK_SEAL_RIGHTEOUSNESS_FILE,
                      STOCK_SEAL_JUSTICE_FILE, STOCK_LARGE_MIST_FILE, STOCK_CLOUD_FILE, STOCK_HOLYZONE_FILE)
BOOK_MODEL = "World\\Generic\\Human\\Passive Doodads\\Books\\BookLargeOpen02.mdx"     # stock GODI 470's model
BANNER_MODEL = "World\\Generic\\Human\\Passive Doodads\\Banners\\CrimsonBanner01.mdx"  # stock GODI 6389's model
RAVAGER_MODEL = "Item\\ObjectComponents\\Weapon\\Axe_2H_War_C_01.mdx"     # item component: untested as a creature model

MODEL_PILLAR = "7fx_lightforged_vindicaar_lightsjudgement_impact"

# Ascension assets, all in patch-N: (archive, path in the archive). The M2 names its textures `spells\\<name>.blp`;
# all twelve are asc-N (VISUALS-REPORT, "Ascension assets"), none is in the stock client.
PILLAR_TEXTURES = ("7fx_fire_puff_holy", "7fx_energyscroll_holy", "white8x8", "magicgun_flash01",
                   "7fx_alphamask_shockwaveholy_b", "7fx_swirl_holy", "7fx_crystalized01",
                   "smoke_wispy_mask_blendadd_bright", "dirt_scroll_wispy_holy_v2", "7fx_hotspot_yellowsoft",
                   "reality_tear", "7fx_energyscroll_holy_dark")
SPELLS_ASSETS = [
    ("patch-N", f"SPELLS/{MODEL_PILLAR}.m2"),
    ("patch-N", f"SPELLS/{MODEL_PILLAR}00.skin"),
    *[("patch-N", f"SPELLS/{name}.blp") for name in PILLAR_TEXTURES],
]

# creature_model_info (server only): (display, bounding radius, combat reach, gender, other-gender display).
# Spectres copy the live human male rows (0.306 / 1.5, gender 0; CDI 25917's own live row is 0 / 0 and would be reset
# by ObjectMgr) and the mounted rider's (1.2 / 3.0). The object-like displays are gender 2 (none) like every other.
HUMAN_MALE_RADIUS = 0.306
HUMAN_MALE_REACH = 1.5
CREATURE_MODEL_INFO = (
    (CDI_SPECTRE_GALVAR, HUMAN_MALE_RADIUS, HUMAN_MALE_REACH, 0, 0),
    (CDI_SPECTRE_FAIRBELL, HUMAN_MALE_RADIUS, HUMAN_MALE_REACH, 0, 0),
    (CDI_SPECTRE_VOSS, HUMAN_MALE_RADIUS, HUMAN_MALE_REACH, 0, 0),
    (CDI_SPECTRE_GOODCHILDE, HUMAN_MALE_RADIUS, HUMAN_MALE_REACH, 0, 0),
    (CDI_SPECTRE_ALEXANDROS, 1.2, 3.0, 0, 0),
    (CDI_CURSED_BOOK, 0.5, 0.5, 2, 0),
    (CDI_RALLYING_BANNER, 0.5, 1.0, 2, 0),
    (CDI_RAVAGER, 0.5, 0.5, 2, 0),
)

# (CMD id, model, collision width, collision height): the object-like displays carry a model row of their own.
OBJECT_MODELS = (
    (CMD_CURSED_BOOK, BOOK_MODEL, 0.9, 0.3),
    (CMD_RALLYING_BANNER, BANNER_MODEL, 0.5, 4.6),
    (CMD_RAVAGER, RAVAGER_MODEL, 0.5, 1.8),
)


def _asset_paths() -> list[Path]:
    return [SPELLS_DIR / Path(p).name for _, p in SPELLS_ASSETS]


def _effect_rows() -> list[tuple[int, str, str, float]]:
    """(id, name, FileName, scale) of every effect; AreaEffectSize 0 on all of them (a fixed size, not the radius)."""
    ref_radius, ref_scale = GRAVE_ROT_REFERENCE
    rows = [(SV_GRAVE_ROT[r], f"Grave Rot Pool {r} yd", STOCK_GOO_FILE, round(ref_scale * r / ref_radius, 3))
            for r in GRAVE_ROT_RADII]
    rows += [
        (SV_RED_AURA, "Hard Mode Red Aura", STOCK_RED_AURA_FILE, RED_AURA_SCALE),
        (SV_SEAL_COMMAND, "Seal of Command Held", STOCK_SEAL_COMMAND_FILE, SEAL_SCALE),
        (SV_SEAL_RIGHTEOUSNESS, "Seal of Righteousness Held", STOCK_SEAL_RIGHTEOUSNESS_FILE, SEAL_SCALE),
        (SV_SEAL_JUSTICE, "Seal of Justice Held", STOCK_SEAL_JUSTICE_FILE, SEAL_SCALE),
    ]
    rows += [(SV_DREAM_MIST[r], f"Dream Mist {r} yd", STOCK_LARGE_MIST_FILE, DREAM_MIST_SCALES[r])
             for r in sorted(SV_DREAM_MIST)]
    rows += [
        (SV_PLAGUE_CLOUD, "Plague Cask Cloud 8 yd", STOCK_CLOUD_FILE, PLAGUE_CLOUD_SCALE),
        (SV_CONSECRATED_HALL, "Consecrated Hall", STOCK_HOLYZONE_FILE, HALL_SCALE),
        (SV_PILLAR_3, "Holy Light Pillar 3 yd", model_path(MODEL_PILLAR), PILLAR_SCALES[SV_PILLAR_3]),
        (SV_PILLAR_6, "Holy Light Pillar 6 yd", model_path(MODEL_PILLAR), PILLAR_SCALES[SV_PILLAR_6]),
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


def _object_model_row(id_: int, model: str, width: float, height: float) -> dict:
    """A static creature model: Flags/SizeClass/BloodID as the BRD kegs, plus the collision box."""
    return _row(dbcfmt.CREATUREMODELDATA, id_, Flags=0, ModelName=model, ModelScale=1.0, SizeClass=1, BloodID=1,
                FootprintParticleScale=1.0, CollisionWidth=width, CollisionHeight=height,
                WorldEffectScale=1.0, AttachedEffectScale=1.0)


def build_creature_model_rows() -> list[dict]:
    return [_object_model_row(*spec) for spec in OBJECT_MODELS]


def _stock_display_rows() -> dict[int, dict]:
    wanted = {base for _, base, _ in SPECTRES}
    return _stock_rows("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, wanted)


def build_creature_display_rows() -> list[dict]:
    """The spectre copies (the stock row of the base display, new id, new alpha; the model, the extended display and
    the textures stay the base's) and the three object-like displays (own CreatureModelData of the same id)."""
    base_rows = _stock_display_rows()
    rows = []
    for cdi, base, alpha in SPECTRES:
        row = dict(base_rows[base])
        row["ID"] = cdi
        row["CreatureModelAlpha"] = alpha
        rows.append(row)
    for cmd, _, _, _ in OBJECT_MODELS:
        rows.append(_row(dbcfmt.CREATUREDISPLAYINFO, cmd, ModelID=cmd, CreatureModelScale=1.0,
                         CreatureModelAlpha=255, BloodLevel=1))
    return rows


def build_creature_model_info_sql() -> str:
    """The `creature_model_info` rows of every minted display (idempotent: deletes exactly its ids first)."""
    ids = ", ".join(str(display) for display, *_ in CREATURE_MODEL_INFO)
    values = ",\n".join(f"({display}, {radius}, {reach}, {gender}, {other})"
                        for display, radius, reach, gender, other in CREATURE_MODEL_INFO)
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
    """source/npcs/scarlet_monastery/_visuals.py by path (source/ is not a package): the ids the boss files use."""
    path = Path(__file__).resolve().parent / "source" / "npcs" / "scarlet_monastery" / "_visuals.py"
    spec = importlib.util.spec_from_file_location("scarlet_monastery_visuals", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_stock_ids() -> list[str]:
    """Confirms every stock or shipped id `_visuals.py` names (and the stock models the rows reuse) exists in the
    working copy; returns a one-line note."""
    visuals = _load_visuals()
    _stock_rows("SpellVisual.dbc", dbcfmt.SPELLVISUAL,
                set(visuals.STOCK_SPELL_VISUALS) | set(visuals.SHIPPED_SPELL_VISUALS))
    used = {r["FileName"].lower() for r in dbcfile.read_dbc(DBC_DIR / "SpellVisualEffectName.dbc",
                                                            dbcfmt.SPELLVISUALEFFECTNAME) if r["ID"] < 90000}
    for file_name in STOCK_EFFECT_FILES:
        if file_name.lower() not in used:
            raise SystemExit(f"no stock SpellVisualEffectName names the model {file_name}")
    _stock_rows("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, set(visuals.STOCK_CREATURE_DISPLAYS))
    _stock_rows("GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO, set(visuals.STOCK_GAMEOBJECT_DISPLAYS))
    objects = {r["ModelName"].lower() for r in dbcfile.read_dbc(DBC_DIR / "GameObjectDisplayInfo.dbc",
                                                                dbcfmt.GAMEOBJECTDISPLAYINFO)}
    for model in (BOOK_MODEL, BANNER_MODEL):
        if model.lower() not in objects:
            raise SystemExit(f"no stock GameObjectDisplayInfo names the model {model}")
    return [f"{len(set(visuals.STOCK_SPELL_VISUALS))} stock + {len(set(visuals.SHIPPED_SPELL_VISUALS))} shipped "
            f"SpellVisual ids, {len(visuals.STOCK_CREATURE_DISPLAYS)} CreatureDisplayInfo ids and "
            f"{len(visuals.STOCK_GAMEOBJECT_DISPLAYS)} GameObjectDisplayInfo ids exist (plus the "
            f"{len(STOCK_EFFECT_FILES)} stock effect models, the open book and the banner model the rows reuse)"]


def check_no_collisions() -> None:
    """The ids this script mints must be free in the working copy or already equal to its own rows (a merge replaces
    rows silently, so a foreign row in the block would be lost)."""
    for filename, table, builder in (
            ("SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME, build_effect_name_rows),
            ("SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, build_kit_rows),
            ("SpellVisual.dbc", dbcfmt.SPELLVISUAL, build_spellvisual_rows),
            ("CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA, build_creature_model_rows),
            ("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, build_creature_display_rows)):
        mine = {r["ID"]: r for r in builder()}
        for row in dbcfile.read_dbc(DBC_DIR / filename, table):
            if row["ID"] in mine and row != mine[row["ID"]]:
                raise SystemExit(f"{filename}: id {row['ID']} already holds a different row")


def build_pending_sql() -> str:
    """Server-side overlay: SpellVisual, CreatureModelData and CreatureDisplayInfo (the other tables are
    client-only) plus every minted display's creature_model_info row. Range-deletes exactly the ids this script mints,
    so a rerun is idempotent."""
    rows = build_spellvisual_rows()
    ids = [r["ID"] for r in rows]
    blocks = [_table_block(dbcfmt.SPELLVISUAL, {"start": min(ids), "end": max(ids)}, rows, [])]
    for table, builder in ((dbcfmt.CREATUREMODELDATA, build_creature_model_rows),
                           (dbcfmt.CREATUREDISPLAYINFO, build_creature_display_rows)):
        built = builder()
        if table is dbcfmt.CREATUREDISPLAYINFO:
            # The DBC holds BloodLevel unsigned (a cloned stock row's -1 reads 4294967295); the server column is a
            # signed int, so db-import refuses the raw value.
            built = [{**r, "BloodLevel": r["BloodLevel"] - (1 << 32) if r["BloodLevel"] >= 1 << 31 else r["BloodLevel"]}
                     for r in built]
        built_ids = [r["ID"] for r in built]
        blocks.append(_table_block(table, {"start": min(built_ids), "end": max(built_ids)}, built, []))
    blocks.append(build_creature_model_info_sql())
    return "\n\n".join(blocks) + "\n"


def _check_block(rows: list[dict], block: dict, what: str) -> None:
    for row in rows:
        if not block["start"] <= row["ID"] <= block["end"]:
            raise SystemExit(f"{what} id {row['ID']} is outside the scarlet_monastery block {block}")


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
        check_no_collisions()
        print("no foreign row in the minted id blocks of the working copy")
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
