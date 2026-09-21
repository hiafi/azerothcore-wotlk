#!/usr/bin/env python3
"""
One-off DBC content patch: mints new SpellVisual.dbc / SpellVisualKit.dbc /
SpellVisualEffectName.dbc rows (plus one CreatureModelData.dbc / CreatureDisplayInfo.dbc row for
Divine Star's travelling orb, and one GameObjectDisplayInfo.dbc row for Angelic Feather's dropped
feather) for the Priest Phase 1 baseline spells' real models/animations - mined from another WotLK
private server's client backup ("Ascension"), same source and pattern already used for these
spells' tooltip icons (build_patch_i.py) and for the Mage rework's own VFX
(patch_mage_vfx_models.py, whose shape this mirrors almost exactly - same "hand-edit the
working-copy DBC via dbcfmt.py's table definitions, outside generate.py's own source/*.csv
pipeline" approach, see docs/ascension-asset-mining.md's Part 2).

Power Word: Barrier is deliberately NOT touched by this script - its entire visual chain
(SpellVisual 13210 -> SpellVisualKit 12286 (ChannelKit) -> SpellVisualEffectName 5211 "Power Word:
Barrier Base" -> Spells\\Priest_PowerWardBarrier.mdx) turned out to be genuine, byte-identical
*stock* Blizzard 3.3.5a client data already present in this project's own working-copy DBCs
(confirmed via lib.dbcfile.read_dbc against var/model-visual-dbc/DBFilesClient/ - real Blizzard
assets simply never wired to a live spell in vanilla WotLK). No new row, no file extraction, no
patch needed - priest_spells.py's power_word_barrier_200132 just sets SpellVisualID_1=13210
directly in its own raw_overrides. Void Eruption's "Voidform" buff (200140) is also untouched -
confirmed no matching transform asset exists anywhere in Ascension's data (see the research
session's report); it keeps no SpellVisualID override (buff-only, no visual) until/unless a
follow-up pass finds or builds something.

Idempotent, same as patch_mage_vfx_models.py: re-running replaces any row whose ID already exists
(matched against this script's own build_*_rows() output) and appends anything new.

Model/skin files themselves are NOT extracted by this script - see
apps/dbc-tools/var/model-visual-dbc/SPELLS/'s own working-copy directory (gitignored), populated by
hand via `smpq -x` against the Ascension client backup at
/mnt/drive6/Permaseeds/AscensionBackup/Data/patch-N.MPQ (the path never appears in this file, only
file basenames). Every .m2 was extracted together with its matching NN.skin companion (WotLK client
models need a skin file to render at all - the Mage working copy already established this
convention, e.g. cfx_mage_flurry_missile.m2 + cfx_mage_flurry_missile00.skin).

`SpellVisual`/`CreatureModelData`/`CreatureDisplayInfo`/`GameObjectDisplayInfo` (unlike
`SpellVisualKit`/`SpellVisualEffectName`) are also loaded server-side - `--sql-out PATH` emits the
matching pending migration from the exact same row-building functions this script already uses for
the binary DBCs, so the two can't drift.

Usage:
    python3 apps/dbc-tools/patch_priest_vfx_models.py
    python3 apps/dbc-tools/patch_priest_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib import dbcfmt, dbcfile
from lib.sql_out import _table_block

DBC_DIR = Path(__file__).resolve().parent / "var" / "model-visual-dbc" / "DBFilesClient"

NOFIELD = 4294967295  # stock "none" sentinel for StartAnimID/CharProc_1-4 - see patch_mage_vfx_models.py


def model_path(filename_no_ext: str) -> str:
    """SpellVisualEffectName.FileName / CreatureModelData.ModelName convention this project already
    established (patch_mage_vfx_models.py, proven live for Frozen Orb): always .mdx, even for a
    file that's genuinely .m2 on disk - the client resolves the alias itself."""
    return f"SPELLS\\{filename_no_ext}.mdx"


def go_model_path(filename_no_ext: str) -> str:
    """GameObjectDisplayInfo.ModelName - this project's first-ever row in this table, so no
    established .mdx-alias precedent to lean on here specifically. Ascension's own live, working
    row for this exact asset (GameObjectDisplayInfo 1013727) uses the real .m2 extension directly,
    not the .mdx alias - mirrored verbatim as the safer, proven-live choice for this table."""
    return f"SPELLS\\{filename_no_ext}.M2"


def _row(table: dbcfmt.DbcTable, id_: int, **fields) -> dict:
    row = dbcfile.empty_row(table)
    row["ID"] = id_
    row.update(fields)
    return row


def _kit_row(id_: int, **fields) -> dict:
    row = _row(
        dbcfmt.SPELLVISUALKIT, id_,
        StartAnimID=NOFIELD,
        CharProc_1=NOFIELD, CharProc_2=NOFIELD, CharProc_3=NOFIELD, CharProc_4=NOFIELD,
    )
    row.update(fields)
    return row


def _merge(path: Path, table: dbcfmt.DbcTable, new_rows: list[dict]) -> int:
    existing = dbcfile.read_dbc(path, table)
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
    if changed:
        dbcfile.write_dbc(path, table, merged)
    return changed


# --- Stock IDs reused as-is (verified byte-identical against this project's own working-copy DBCs
# via lib.dbcfile.read_dbc - no minting, no extraction needed for any of these) ---

KIT_PRECAST_HOLY_LOW_HAND = 99          # LeftHandEffect=RightHandEffect=135 "Holy Precast Low Hand"
EFFECT_HOLY_PRECAST_LOW_HAND = 135
EFFECT_HOLY_PRECAST_HIGH_HAND = 131
KIT_HALO_PRECAST_STOCK = 193            # BaseEffect=123 "Holy Precast High Base", hand=131
KIT_HALO_STATE_STOCK = 3153             # ChestEffect=129 "Holy ImpactDD Low Chest"
KIT_VOID_ERUPTION_IMPACT_STOCK = 2350   # ChestEffect=1054 "Shadow ImpactDD Uber Chest"
EFFECT_SHADOW_STRIKES_STATE_HAND = 3097  # same file/Scale Ascension's own 52630 uses, already stock
EFFECT_SHADOW_PRECAST_MED_BASE = 1703   # Leap of Faith StateKit's flourish BaseEffect, already stock
KIT_POWER_WORD_BARRIER_STOCK = 12286    # BaseEffect=5211 "Power Word: Barrier Base" (real dome model)
# "Shadow Nova" (26 stock boss-ability ranks, all resolving to the same 2 underlying models) -
# EFN 3112 "Shadow Nova Cast" (spells\shadow_nova_area_noprojection.mdx) is the most-reused/default
# variant, used directly as Void Eruption's own new cast effect per the user's request (2026-09-20
# playtest: "we can use Shadow_nova_area as the cast animation"). Genuine stock 3.3.5a data, no
# mining/extraction needed - same happy case as Power Word: Barrier's own model.
EFFECT_SHADOW_NOVA_CAST_STOCK = 3112

# --- SpellVisualEffectName.dbc: one row per extracted model (90012-90017) ---

EFFECT_DIVINE_STAR_PRECAST = 90012
EFFECT_DIVINE_STAR_IMPACT = 90013
EFFECT_HALO_CAST = 90014
# Orphaned as of 2026-09-20 - KIT_VOID_ERUPTION_CAST's BaseEffect was swapped to the stock
# EFFECT_SHADOW_NOVA_CAST_STOCK (3112) per the user's own playtest request. Left minted rather than
# removed (same "orphaned but harmless" precedent patch_mage_vfx_models.py's own
# EFFECT_METEOR_MISSILE uses) - the mined cfx_priest_voideruption_casebase.m2 file is still sitting
# in var/model-visual-dbc/SPELLS/ if this ever needs reverting.
EFFECT_VOID_ERUPTION_CASEBASE = 90015
EFFECT_VOID_ERUPTION_MISSILE = 90016
EFFECT_LEAP_OF_FAITH_TARGET_YELLOW = 90017

_EFFECT_NAMES = (
    (EFFECT_DIVINE_STAR_PRECAST, "Divine Star Precast (Custom)", "Priest_DivineStar_Precast_Yellow"),
    (EFFECT_DIVINE_STAR_IMPACT, "Divine Star Impact (Custom)", "Priest_DivineStar_Impact_Yellow"),
    (EFFECT_HALO_CAST, "Halo Cast (Custom)", "priest_halo_cast"),
    (EFFECT_VOID_ERUPTION_CASEBASE, "Void Eruption Cast Base (Custom)", "cfx_priest_voideruption_casebase"),
    (EFFECT_VOID_ERUPTION_MISSILE, "Void Eruption Missile (Custom)", "sha_lavaburst_missile_noflash_pride"),
    (EFFECT_LEAP_OF_FAITH_TARGET_YELLOW, "Leap of Faith Target Yellow (Custom)", "Priest_Leapoffaith_Target_Yellow"),
)


def build_effect_name_rows() -> list[dict]:
    return [
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, id_,
            Name=name, FileName=model_path(filename),
            AreaEffectSize=1.0, Scale=1.0, MinAllowedScale=0.01, MaxAllowedScale=100.0,
        )
        for id_, name, filename in _EFFECT_NAMES
    ]


# --- SpellVisualKit.dbc (90008-90017) ---

KIT_ANGELIC_FEATHER_CAST = 90008
KIT_DIVINE_STAR_PRECAST = 90009
KIT_DIVINE_STAR_CAST = 90010
KIT_DIVINE_STAR_IMPACT = 90011
KIT_HALO_CAST = 90012
KIT_VOID_ERUPTION_PRECAST = 90013
KIT_VOID_ERUPTION_CAST = 90014
# Leap of Faith's yellow target marker has no live Ascension SpellVisual/Kit chain pointing at it
# at all (confirmed genuinely orphaned - EFFECT_LEAP_OF_FAITH_TARGET_YELLOW's underlying model
# exists but nothing references it). Built from scratch by cloning the one proven-live template
# with the same "ally gets a target-marker decal + ongoing state glow" shape: Ascension spell
# 560718 "Terror of the Old Gods" (SpellVisual 1000304 -> CastKit 1000884/ImpactKit 1000885/
# StateKit 1000886), which uses the *purple* variant of this exact marker family (ChestEffect
# 54081). Cloned verbatim field-for-field except ChestEffect swapped to our own yellow effect, and
# CastKit's unrelated BaseEffect=54110 ("priest_shadowyapparition_precast", a Shadowy-Apparition
# flourish, not this asset family) dropped - its own archive location wasn't verified during
# research, and it's a minor supplementary flourish, not the marker itself.
KIT_LEAP_OF_FAITH_CAST = 90015
KIT_LEAP_OF_FAITH_IMPACT = 90016
KIT_LEAP_OF_FAITH_STATE = 90017


def build_kit_rows() -> list[dict]:
    return [
        _kit_row(
            KIT_ANGELIC_FEATHER_CAST,
            AnimID=54, SoundID=89660,
            LeftHandEffect=EFFECT_HOLY_PRECAST_LOW_HAND, RightHandEffect=EFFECT_HOLY_PRECAST_LOW_HAND,
        ),
        _kit_row(
            KIT_DIVINE_STAR_PRECAST,
            AnimID=51, SoundID=740,
            LeftHandEffect=EFFECT_DIVINE_STAR_PRECAST, RightHandEffect=EFFECT_DIVINE_STAR_PRECAST,
        ),
        _kit_row(
            KIT_DIVINE_STAR_CAST,
            AnimID=53,
            LeftHandEffect=EFFECT_HOLY_PRECAST_LOW_HAND, RightHandEffect=EFFECT_HOLY_PRECAST_LOW_HAND,
        ),
        _kit_row(KIT_DIVINE_STAR_IMPACT, AnimID=NOFIELD, ChestEffect=EFFECT_DIVINE_STAR_IMPACT, SoundID=27193, Flags=2048),
        _kit_row(
            KIT_HALO_CAST,
            AnimID=54, SoundID=89548, WorldEffect=EFFECT_HALO_CAST,
            LeftHandEffect=EFFECT_HOLY_PRECAST_HIGH_HAND, RightHandEffect=EFFECT_HOLY_PRECAST_HIGH_HAND,
        ),
        _kit_row(
            KIT_VOID_ERUPTION_PRECAST,
            AnimID=52, SoundID=90284,
            LeftHandEffect=EFFECT_SHADOW_STRIKES_STATE_HAND, RightHandEffect=EFFECT_SHADOW_STRIKES_STATE_HAND,
        ),
        _kit_row(
            KIT_VOID_ERUPTION_CAST,
            AnimID=54, SoundID=90285, BaseEffect=EFFECT_SHADOW_NOVA_CAST_STOCK,
            LeftHandEffect=EFFECT_SHADOW_STRIKES_STATE_HAND, RightHandEffect=EFFECT_SHADOW_STRIKES_STATE_HAND,
        ),
        _kit_row(
            KIT_LEAP_OF_FAITH_CAST,
            ChestEffect=EFFECT_LEAP_OF_FAITH_TARGET_YELLOW, SoundID=283490,
        ),
        _kit_row(KIT_LEAP_OF_FAITH_IMPACT, AnimID=NOFIELD, SoundID=5756, CharParamThree_4=2.5559700588928536e-05),
        _kit_row(
            KIT_LEAP_OF_FAITH_STATE,
            AnimID=NOFIELD,
            ChestEffect=EFFECT_LEAP_OF_FAITH_TARGET_YELLOW, BaseEffect=EFFECT_SHADOW_PRECAST_MED_BASE,
            CharProc_1=1, CharProc_2=14,
            CharParamZero_1=2555970.0, CharParamOne_1=0.20000000298023224,
            CharParamOne_4=1.9999999494757503e-05, CharParamTwo_1=2.0000200271606445,
            CharParamTwo_2=2.0, CharParamTwo_4=2.9999999242136255e-05, CharParamThree_1=3.0,
        ),
    ]


# --- SpellVisual.dbc (90011-90017) ---

SV_ANGELIC_FEATHER = 90011         # spell 200130
SV_DIVINE_STAR_CAST = 90012        # spell 200133 (the throw)
SV_DIVINE_STAR_IMPACT = 90013      # spell 200134 (divine_star_pulse - heal/damage tick burst)
SV_HALO = 90014                    # spell 200135
SV_VOID_ERUPTION = 90015           # spell 200139
SV_LEAP_OF_FAITH = 90016           # spell 200137
# Live playtest bug (2026-09-20): Power Word: Barrier's own SpellVisualID_1 was set directly to
# stock 13210 (see priest_spells.py's power_word_barrier_200132 notes) rather than minted here,
# since its whole kit/effect-name chain (SpellVisualKit 12286 -> SpellVisualEffectName 5211
# "Power Word: Barrier Base" -> Spells\Priest_PowerWardBarrier.mdx) is genuine unused stock 3.3.5a
# data - reused verbatim, not re-authored. The bug: that stock row 13210 wires kit 12286 in as its
# ChannelKit, but this spell isn't a channel at all (SPELL_EFFECT_PERSISTENT_AREA_AURA, like Death
# and Decay) - real ground-zone spells' visuals come from PersistentAreaKit, confirmed against
# Death and Decay/Blizzard/Rain of Fire/Frost Trap Aura's own stock SpellVisual rows (all wire
# their ground decal via PersistentAreaKit, never ChannelKit). Rather than mutate the shared stock
# row 13210 in place (this project's convention is to never hand-edit a real Blizzard ID - mint a
# new one that reuses the shared components instead, same as every other row in this file), this
# mints a fresh SpellVisual row that points the SAME untouched stock kit (12286) at the correct
# slot.
SV_POWER_WORD_BARRIER = 90017      # spell 200132


def build_spellvisual_rows() -> list[dict]:
    return [
        _row(dbcfmt.SPELLVISUAL, SV_ANGELIC_FEATHER, PrecastKit=KIT_PRECAST_HOLY_LOW_HAND, CastKit=KIT_ANGELIC_FEATHER_CAST),
        _row(dbcfmt.SPELLVISUAL, SV_DIVINE_STAR_CAST, PrecastKit=KIT_DIVINE_STAR_PRECAST, CastKit=KIT_DIVINE_STAR_CAST),
        _row(
            dbcfmt.SPELLVISUAL, SV_DIVINE_STAR_IMPACT,
            ImpactKit=KIT_DIVINE_STAR_IMPACT, MissileDestinationAttachment=34, Flags=576,
        ),
        _row(dbcfmt.SPELLVISUAL, SV_HALO, PrecastKit=KIT_HALO_PRECAST_STOCK, CastKit=KIT_HALO_CAST, StateKit=KIT_HALO_STATE_STOCK),
        _row(
            dbcfmt.SPELLVISUAL, SV_VOID_ERUPTION,
            PrecastKit=KIT_VOID_ERUPTION_PRECAST, CastKit=KIT_VOID_ERUPTION_CAST,
            ImpactKit=KIT_VOID_ERUPTION_IMPACT_STOCK,
            HasMissile=1, MissileModel=EFFECT_VOID_ERUPTION_MISSILE, MissileDestinationAttachment=1,
            MissileSound=3015, Flags=1, MissileMotion=13376,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_LEAP_OF_FAITH,
            CastKit=KIT_LEAP_OF_FAITH_CAST, ImpactKit=KIT_LEAP_OF_FAITH_IMPACT, StateKit=KIT_LEAP_OF_FAITH_STATE,
            Flags=1, MissileDestinationAttachment=1,
        ),
        _row(dbcfmt.SPELLVISUAL, SV_POWER_WORD_BARRIER, PersistentAreaKit=KIT_POWER_WORD_BARRIER_STOCK),
    ]


# --- CreatureModelData.dbc / CreatureDisplayInfo.dbc: Divine Star's travelling orb (90004) ---

DIVINE_STAR_ORB_MODEL_ID = 90004


def build_creature_model_row() -> dict:
    return _row(
        dbcfmt.CREATUREMODELDATA, DIVINE_STAR_ORB_MODEL_ID,
        Flags=2, ModelName=model_path("Priest_DivineStar_Missile_Yellow"), ModelScale=1.0,
        SizeClass=1, BloodID=1, FootprintParticleScale=1.0,
        WorldEffectScale=1.0, AttachedEffectScale=1.0,
    )


def build_creature_display_row() -> dict:
    return _row(
        dbcfmt.CREATUREDISPLAYINFO, DIVINE_STAR_ORB_MODEL_ID,
        ModelID=DIVINE_STAR_ORB_MODEL_ID, CreatureModelScale=1.0, CreatureModelAlpha=255, BloodLevel=1,
    )


# --- GameObjectDisplayInfo.dbc: Angelic Feather's dropped-feather GO (90001, first custom row) ---

ANGELIC_FEATHER_GO_MODEL_ID = 90001


def build_gameobject_display_row() -> dict:
    return _row(
        dbcfmt.GAMEOBJECTDISPLAYINFO, ANGELIC_FEATHER_GO_MODEL_ID,
        ModelName=go_model_path("Priest_AngelicFeather_State"),
        GeoBoxMinX=-2.257110118865967, GeoBoxMinY=-2.38496994972229, GeoBoxMinZ=-0.10669799894094467,
        GeoBoxMaxX=2.4491798877716064, GeoBoxMaxY=2.3395800590515137, GeoBoxMaxZ=3.930310010910034,
    )


def build_pending_sql() -> str:
    """Server-side counterpart for the 4 tables AzerothCore actually loads (SpellVisual,
    CreatureModelData, CreatureDisplayInfo, GameObjectDisplayInfo) - SpellVisualKit/
    SpellVisualEffectName have no LOAD_DBC call, client-only, no SQL needed. Range-deletes exactly
    the IDs each table mints here, same idempotent-on-rerun shape patch_mage_vfx_models.py uses."""
    blocks = [
        _table_block(dbcfmt.SPELLVISUAL, {"start": 90011, "end": 90017}, build_spellvisual_rows(), []),
        _table_block(dbcfmt.CREATUREMODELDATA, {"start": 90004, "end": 90004}, [build_creature_model_row()], []),
        _table_block(dbcfmt.CREATUREDISPLAYINFO, {"start": 90004, "end": 90004}, [build_creature_display_row()], []),
        _table_block(dbcfmt.GAMEOBJECTDISPLAYINFO, {"start": 90001, "end": 90001}, [build_gameobject_display_row()], []),
    ]
    return "\n\n".join(blocks) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sql-out", type=Path, default=None,
        help="Write the matching server-side SQL migration to this path (see module docstring).",
    )
    args = parser.parse_args()

    added = 0
    added += _merge(DBC_DIR / "SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME, build_effect_name_rows())
    added += _merge(DBC_DIR / "SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, build_kit_rows())
    added += _merge(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL, build_spellvisual_rows())
    added += _merge(DBC_DIR / "CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA, [build_creature_model_row()])
    added += _merge(DBC_DIR / "CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, [build_creature_display_row()])
    added += _merge(DBC_DIR / "GameObjectDisplayInfo.dbc", dbcfmt.GAMEOBJECTDISPLAYINFO, [build_gameobject_display_row()])
    print(f"added {added} row(s) across the 6 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
