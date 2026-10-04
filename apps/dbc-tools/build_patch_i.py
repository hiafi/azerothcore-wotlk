#!/usr/bin/env python3
"""
Priest baseline rework (docs/reworks/priest-new-spells.md): mints new SpellIcon.dbc rows for the 5
new spells that needed real icon art (Power Word: Barrier already has a matching stock icon,
3837 - see priest_spells.py's own notes on that spell - so it isn't touched here), then packages
the underlying .blp files into patch-I.mpq and deploys it. A 6th icon (Spirit Shell, Discipline
rework) was tried and reverted - see the comment above ICONS for why.

Implements docs/ascension-asset-mining.md Part 1's recommended pipeline (extract -> pack -> add
DBC rows), scoped narrowly to the 5 files this pass actually needs rather than the full 76k-icon
archive. Same "hand-edit the working-copy DBC via dbcfmt.py's table definitions, outside
generate.py's own source/*.csv pipeline" pattern patch_mage_vfx_models.py already established for
SpellVisual*/CreatureModelData/CreatureDisplayInfo - see lib/dbcfmt.py's own SPELLICON comment for
why this table needs its own bootstrap (it has no DBCfmt.h entry at all; the server never loads it,
so there's no matching SQL overlay table either, unlike those three).

Source archive: an Ascension private-server client backup at
/mnt/drive6/Permaseeds/AscensionBackup/Data/patch-I.MPQ (per docs/ascension-asset-mining.md - "I" =
Icons, 100% Interface/icons/*.blp, nothing else). Confirmed via `smpq -l` to contain real matches
for Angelic Feather/Divine Star/Halo/Leap of Faith/Void Eruption (the last shared with its own
"Voidform" buff, since no exact "voideruption" icon exists there and retail shares that icon
between the two anyway).

Custom SpellIcon.dbc ID convention established here (nothing documented it before - see
docs/ascension-asset-mining.md's own note on this gap): starts at 90100, offset from
CreatureModelData/CreatureDisplayInfo's existing 90001+/90002+ convention (a different DBC table,
so no actual collision risk either way, but a distinct round number avoids visual confusion between
the two custom ranges when reading notes/comments side by side).

Usage:
    python3 apps/dbc-tools/build_patch_i.py [--source-mpq PATH] [--deploy-root PATH]

    --source-mpq     Ascension patch-I.MPQ to extract icons from (default: the path above).
    --deploy-root    patch-service PATCH_ROOT to copy patch-I.mpq's Data/ into (default: this
                      box's DEPLOY_ROOT from lib/local_config.py, or no deployment if that file
                      doesn't exist). Pass --deploy-root '' to skip deployment and only (re)build
                      apps/dbc-tools/var/dbc-patch/patch-I.mpq locally.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.mpq_writer import write_mpq

DEFAULT_SOURCE_MPQ = Path("/mnt/drive6/Permaseeds/AscensionBackup/Data/patch-I.MPQ")
WORKING_DBC_DIR = Path(__file__).resolve().parent / "var" / "model-visual-dbc" / "DBFilesClient"
SPELLICON_DBC = WORKING_DBC_DIR / "SpellIcon.dbc"
STOCK_SPELLICON_CSV = Path(__file__).resolve().parent / "var" / "spell_icon_names.csv"
LOCAL_OUT = Path(__file__).resolve().parent / "var" / "dbc-patch" / "patch-I.mpq"

try:
    from lib.local_config import DEPLOY_ROOT as DEFAULT_DEPLOY_ROOT
except ImportError:
    DEFAULT_DEPLOY_ROOT = None

# (custom SpellIcon ID, archive-relative source path in the Ascension backup, this project's own
# spell() var name + file it lives in - for the human reading this table, not read by the script)
ICON_ID_ANGELIC_FEATHER = 90100
ICON_ID_DIVINE_STAR = 90101
ICON_ID_HALO = 90102
ICON_ID_LEAP_OF_FAITH = 90103
ICON_ID_VOID_ERUPTION = 90104  # shared by void_eruption_200139 and void_eruption_buff_200140
# 90105 (ability_priest_angelicbulwark, tried for Spirit Shell) rendered blank and was reverted to
# a stock icon - root-caused later (2026-09-22, docs/bugs-and-fixes.md): build_patch_m.py was
# packing a stale copy of SpellIcon.dbc into patch-M.mpq, which the client loads *after* patch-I and
# so shadowed every row minted here after patch-M's last rebuild. The file was never at fault; the
# id is still free in the working copy if Spirit Shell wants its icon back.
ICON_ID_HOLY_WORD_SERENITY = 90106
ICON_ID_HOLY_WORD_SANCTIFY = 90107  # was sharing 90102 (Halo) with Serenity - split out to fix that
ICON_ID_HOLY_WORD_CHASTISE = 90108  # was sharing 90104 (Void Eruption) with Apotheosis - split out
ICON_ID_APOTHEOSIS = 90109
# Druid rework (.agents/plans/druid-rework/druid-rework.PLAN.md): Balance 90110-90119, Feral
# 90120-90129, Resto 90130-90139. Cenarion Ward, Improved Insect Swarm and Primal Attunement use
# stock icons (198, 116, 2025) that already carry the wanted art, so they aren't mined here.
ICON_ID_MASS_ENTANGLEMENT = 90110
ICON_ID_FURY_OF_ELUNE = 90111  # shared by 200336 and its 200338/200339 beam/splash triggers
ICON_ID_IRONFUR = 90120
ICON_ID_BLOODLETTING = 90121
ICON_ID_SAVAGE_BITE = 90122  # 200439 (FERAL-ADDENDUM, was sharing Maul's 1680)
ICON_ID_BLOOM = 90130  # shared by 200560 and its 200561 jump
ICON_ID_FLOURISH = 90131  # shared by 200564 and its 200565/200603 buff/ground triggers

# Warlock rework Destruction pass (warlock-rework.DESTRUCTION.md §2.6/§11 Q19, B17(b)/C11): Incinerate
# 29722 needs to move off stock icon 2128 (Spell_Fire_Burnout) so the stock "+25% vs Immolate"
# hardcode (keyed on that exact icon id) goes inert, without changing Incinerate's actual art - it
# still shows the same texture, just under a new custom SpellIcon.dbc id. Unlike every row above,
# this is a "stock path, no blp" alias: the texture already ships in the client, so there's nothing
# to extract from the Ascension archive and nothing new to pack into patch-I.mpq - only a SpellIcon
# row pointing at the existing stock path. See STOCK_ALIAS_ICONS below.
ICON_ID_INCINERATE_ALIAS = 90170

# Warlock rework mined icons (DATA-INVENTORY: Aff 90150-90159, Demo 90160-90169, Destro 90171-90179).
# 90151 (Soul Swap: Exhale) and 90161 (Wild Imp/Imp Gang Boss) stay reserved for the slots the spec
# docs pre-assigned them; nothing mined for them yet.
ICON_ID_SOUL_SWAP = 90150  # shared by 200733 and its 200735 copied-DoTs buff
ICON_ID_SOUL_HARVEST = 90152  # shared by 200736 and its 200737 pet buff
ICON_ID_BURNING_RUSH = 90153
ICON_ID_DARK_SOUL_MISERY = 90154
ICON_ID_SOULBURN = 90155  # shared by 200710 and its 200711 marker
ICON_ID_HARVESTER_OF_DEATH = 90156  # talent ranks 200745-200747 and the 200748 capstone passive
ICON_ID_HAND_OF_GULDAN = 90160  # shared by 200820 and its 200821 splash
ICON_ID_DARK_APOTHEOSIS = 90162  # 200835, its 200863 talent learner and 200864 demon abilities
ICON_ID_SUMMON_DOOMGUARD = 90163
ICON_ID_CHAOS_RIFT = 90171
ICON_ID_HAVOC = 90172

# Paladin rework shared block (paladin-rework.SHARED.md B0 / B1, A2 icons 90180-90189; 90183-90189 spare).
# All three are "stock path, no blp" aliases (see STOCK_ALIAS_ICONS), so each gets its own SpellIcon.dbc
# id without changing the texture:
#   90180 - Primed: Righteousness 201063. Part A forbids SpellIcon 25 on it (icon-25 hardcode, SIC:5314),
#           so it aliases the same texture under a new id.
#   90181 - Deliverance 201061. No fitting art in the Ascension patch-I (no "deliverance" icon), so it
#           aliases the stock blue Judgement texture (SpellIcon 3014) to look distinct from Judgement's 205.
#   90182 - the two Vengeance unleash DoTs 201071 / 201077: alias of the stock icon-2292 texture, so
#           they honour Part A's "avoid SpellIcon 2292" literally (the JoV +10%/stack hardcode keys on 2292).
ICON_ID_PRIMED_RIGHTEOUSNESS_ALIAS = 90180
ICON_ID_DELIVERANCE_ALIAS = 90181
ICON_ID_VENGEANCE_DOT_ALIAS = 90182

# Paladin rework Retribution (paladin-rework.RETRIBUTION.md §2.6): block 90210-90219, 90215-90219 spare.
ICON_ID_BLADE_OF_JUSTICE = 90210  # 201400, echoes 201401-201409
ICON_ID_WAKE_OF_ASHES = 90211  # 201413, 201414
ICON_ID_EXECUTION_SENTENCE = 90212  # 201410-201412
ICON_ID_SANCTIFIED_SEALS = 90213  # Sanctified Seals ranks
ICON_ID_BLADE_OF_WRATH = 90214  # Blade of Wrath ranks and 201429

# Paladin rework Protection (paladin-rework.PROTECTION.md §2.4): block 90200-90209, 90201-90209 spare.
ICON_ID_BULWARK = 90200  # Bulwark buff 201360 / 201361

ICONS = (
    (ICON_ID_ANGELIC_FEATHER, "Interface/icons/ability_priest_angelicfeather.blp"),
    (ICON_ID_DIVINE_STAR, "Interface/icons/spell_priest_divinestar.blp"),
    (ICON_ID_HALO, "Interface/icons/ability_priest_halo.blp"),
    (ICON_ID_LEAP_OF_FAITH, "Interface/icons/priest_spell_leapoffaith_a.blp"),
    (ICON_ID_VOID_ERUPTION, "Interface/icons/spell_priest_voidform.blp"),
    (ICON_ID_HOLY_WORD_SERENITY, "Interface/icons/spell_priest_burningwill.blp"),
    (ICON_ID_HOLY_WORD_SANCTIFY, "Interface/icons/spell_holy_divineprovidence.blp"),
    (ICON_ID_HOLY_WORD_CHASTISE, "Interface/icons/spell_holy_chastise.blp"),
    (ICON_ID_APOTHEOSIS, "Interface/icons/spell_priest_chakra.blp"),
    (ICON_ID_MASS_ENTANGLEMENT, "Interface/icons/spell_druid_massentanglement.blp"),
    (ICON_ID_FURY_OF_ELUNE, "Interface/icons/ability_druid_cresentburn.blp"),
    (ICON_ID_IRONFUR, "Interface/icons/ability_druid_ironfur.blp"),
    (ICON_ID_BLOODLETTING, "Interface/icons/ability_ironmaidens_corruptedblood.blp"),
    (ICON_ID_SAVAGE_BITE, "Interface/icons/spell_druid_bearhug.blp"),
    (ICON_ID_BLOOM, "Interface/icons/ability_evoker_spiritbloom.blp"),
    (ICON_ID_FLOURISH, "Interface/icons/inv12_ability_druid_flourish_empowered.blp"),
    (ICON_ID_SOUL_SWAP, "Interface/icons/ability_warlock_soulswap.blp"),
    (ICON_ID_SOUL_HARVEST, "Interface/icons/sha_spell_shadow_shadesofdarkness_nightborne.blp"),
    (ICON_ID_BURNING_RUSH, "Interface/icons/nhi_fire_flameshot.blp"),
    (ICON_ID_DARK_SOUL_MISERY, "Interface/icons/spell_warlock_demonsoul.blp"),
    (ICON_ID_SOULBURN, "Interface/icons/_Warlock_SoulBurn.blp"),
    (ICON_ID_HARVESTER_OF_DEATH, "Interface/icons/_DeathCoil_Color_Green.blp"),
    (ICON_ID_HAND_OF_GULDAN, "Interface/icons/ability_warlock_handofguldan.blp"),
    (ICON_ID_DARK_APOTHEOSIS, "Interface/icons/spell_warlock_demonwrath.blp"),
    (ICON_ID_SUMMON_DOOMGUARD, "Interface/icons/warlock_summon_doomguard.blp"),
    (ICON_ID_CHAOS_RIFT, "Interface/icons/custom_T_Nhance_RPG_Icons_UnholyPortal.blp"),
    (ICON_ID_HAVOC, "Interface/icons/ability_warlock_baneofhavoc.blp"),
    (ICON_ID_BLADE_OF_JUSTICE, "Interface/icons/ability_paladin_bladeofjustice.blp"),
    (ICON_ID_WAKE_OF_ASHES, "Interface/icons/inv_sword_2h_artifactashbringerfire_d_03.blp"),
    (ICON_ID_EXECUTION_SENTENCE, "Interface/icons/spell_paladin_executionsentence.blp"),
    (ICON_ID_SANCTIFIED_SEALS, "Interface/icons/ability_paladin_empoweredsealsrighteous.blp"),
    (ICON_ID_BLADE_OF_WRATH, "Interface/icons/ability_paladin_bladeofjusticeblue.blp"),
    (ICON_ID_BULWARK, "Interface/icons/inv_ability_lightsmithpaladin_holybulwark.blp"),
)

# "Stock path, no blp" entries (warlock-rework DESTRUCTION §2.6/§11 Q19): a SpellIcon.dbc row that
# just aliases an existing stock texture already shipped in the client - no extraction from the
# Ascension archive, no file packed into patch-I.mpq's Interface/Icons/. Kept as a separate tuple
# rather than folded into ICONS because extract_icons()/the packaged-files loop below both key off
# ICONS's archive-relative paths; build_spellicon_rows() below merges both tuples into the DBC.
STOCK_ALIAS_ICONS = (
    (ICON_ID_INCINERATE_ALIAS, "Interface\\Icons\\Spell_Fire_Burnout"),
    (ICON_ID_PRIMED_RIGHTEOUSNESS_ALIAS, "Interface\\Icons\\Ability_ThunderBolt"),
    (ICON_ID_DELIVERANCE_ALIAS, "Interface\\Icons\\Ability_Paladin_JudgementBlue"),
    (ICON_ID_VENGEANCE_DOT_ALIAS, "Interface\\Icons\\Spell_Holy_SealOfVengeance"),
)


def _find_smpq() -> str:
    smpq = shutil.which("smpq")
    if not smpq:
        raise SystemExit("smpq not found on PATH - see lib/mpq_writer.py's docstring for setup")
    return smpq


def extract_icons(source_mpq: Path) -> dict[str, bytes]:
    """Returns {archive-relative path (forward slashes) -> file bytes} for every path in ICONS."""
    if not source_mpq.is_file():
        raise SystemExit(f"source MPQ not found: {source_mpq}")

    smpq = _find_smpq()
    paths = [p for _, p in ICONS]
    with tempfile.TemporaryDirectory(prefix="patch-i-extract-") as tmp:
        tmp_path = Path(tmp)
        subprocess.run([smpq, "-x", str(source_mpq), *paths], cwd=tmp_path, check=True,
                        capture_output=True, text=True)
        out = {}
        for _, rel in ICONS:
            extracted = tmp_path / rel
            if not extracted.is_file():
                raise SystemExit(f"expected extracted file missing: {rel} (checked {extracted})")
            out[rel] = extracted.read_bytes()
        return out


def load_or_bootstrap_spellicon_working_copy() -> list[dict]:
    """Reads the working-copy SpellIcon.dbc, bootstrapping it from var/spell_icon_names.csv (a
    full id->path dump of the real stock table, already pulled for reference - see that CSV's own
    header) on first run, since this table (unlike CreatureModelData/CreatureDisplayInfo) never had
    a binary working copy checked in yet."""
    if SPELLICON_DBC.is_file():
        return dbcfile.read_dbc(SPELLICON_DBC, dbcfmt.SPELLICON)

    if not STOCK_SPELLICON_CSV.is_file():
        raise SystemExit(f"no working-copy SpellIcon.dbc and no bootstrap CSV at {STOCK_SPELLICON_CSV}")

    rows = []
    for line in STOCK_SPELLICON_CSV.read_text().splitlines()[1:]:  # skip "id,path" header
        id_str, path = line.split(",", 1)
        rows.append({"ID": int(id_str), "TextureFilename": path})
    print(f"bootstrapped {len(rows)} stock row(s) from {STOCK_SPELLICON_CSV.name} into a new working copy")
    return rows


def build_spellicon_rows() -> list[dict]:
    rows = [
        {"ID": icon_id, "TextureFilename": "Interface\\Icons\\" + Path(rel).stem}
        for icon_id, rel in ICONS
    ]
    rows += [{"ID": icon_id, "TextureFilename": path} for icon_id, path in STOCK_ALIAS_ICONS]
    return rows


def merge_spellicon_rows(existing: list[dict], new_rows: list[dict]) -> tuple[list[dict], int]:
    new_by_id = {r["ID"]: r for r in new_rows}
    changed = 0
    merged = []
    seen = set()
    for r in existing:
        if r["ID"] in new_by_id:
            replacement = new_by_id[r["ID"]]
            if replacement != r:
                changed += 1
            merged.append(replacement)
            seen.add(r["ID"])
        else:
            merged.append(r)
    for id_, r in new_by_id.items():
        if id_ not in seen:
            merged.append(r)
            changed += 1
    return merged, changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-mpq", type=Path, default=DEFAULT_SOURCE_MPQ)
    parser.add_argument("--deploy-root", type=str, default=str(DEFAULT_DEPLOY_ROOT) if DEFAULT_DEPLOY_ROOT else "")
    args = parser.parse_args()

    icon_bytes = extract_icons(args.source_mpq)
    print(f"extracted {len(icon_bytes)} icon(s) from {args.source_mpq}")

    existing_rows = load_or_bootstrap_spellicon_working_copy()
    merged_rows, changed = merge_spellicon_rows(existing_rows, build_spellicon_rows())
    if changed:
        dbcfile.write_dbc(SPELLICON_DBC, dbcfmt.SPELLICON, merged_rows)
    print(f"SpellIcon.dbc working copy: {changed} row(s) added/changed ({len(merged_rows)} total)")

    files = {f"DBFilesClient\\SpellIcon.dbc": SPELLICON_DBC.read_bytes()}
    files.update({f"Interface\\Icons\\{Path(rel).name}": blob for rel, blob in icon_bytes.items()})

    LOCAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    write_mpq(LOCAL_OUT, files)
    print(f"built {LOCAL_OUT} ({LOCAL_OUT.stat().st_size} bytes) - "
          f"1 DBC + {len(icon_bytes)} icon file(s):")
    for icon_id, rel in ICONS:
        print(f"  {icon_id} -> Interface\\Icons\\{Path(rel).name}")
    for icon_id, path in STOCK_ALIAS_ICONS:
        print(f"  {icon_id} -> {path} (stock path, no blp)")

    if args.deploy_root:
        deploy_path = Path(args.deploy_root) / "Data" / "patch-I.mpq"
        deploy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LOCAL_OUT, deploy_path)
        print(f"deployed -> {deploy_path}")
        print("(manifest-gen container picks this up on its next timer tick - run "
              "apps/patch-service/manifest_gen.py by hand for an immediate manifest.txt refresh)")


if __name__ == "__main__":
    main()
