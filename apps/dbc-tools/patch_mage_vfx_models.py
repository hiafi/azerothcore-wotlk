#!/usr/bin/env python3
"""
One-off DBC content patch: mints new SpellVisual.dbc / SpellVisualKit.dbc /
SpellVisualEffectName.dbc rows (plus one CreatureModelData.dbc / CreatureDisplayInfo.dbc row) for
the Mage VFX wired up this pass - real models for Meteor/Frozen Orb/Glacial Spike/Flurry, a shared
precast flourish for Meteor/Flashpoint/Frozen Orb/Flurry, and a real cast-time visual for Glacial
Spike (the one spell of these five with an actual cast bar - see docs/reworks/fire-mage-meteor-vfx.md).

Same "hand-edit the working-copy DBC via dbcfmt.py's table definitions, outside generate.py's own
source/*.csv pipeline" pattern the deleted patch_frozen_orb_model.py used for Frozen Orb's existing
model row (90001) - see docs/ascension-asset-mining.md's Part 2, and dbcfmt.py's own comment on
CREATUREMODELDATA/CREATUREDISPLAYINFO/SPELLVISUAL*. Run this before build_patch_m.py, which just
repackages whatever's currently sitting in the working copy.

Idempotent: re-running replaces any row whose ID already exists (matched against this script's own
build_*_rows() output) and appends anything new, so it's safe to run again after a fresh asset
extraction, or after editing a row-building function to fix a field on an ID already minted.

Model files themselves are NOT extracted by this script (see apps/dbc-tools/var/model-visual-dbc/
SPELLS/'s own working-copy directory, gitignored, populated by hand via `smpq -x` against a local
Ascension client backup - the path to that backup never appears in this file, only file basenames
that already exist client-side under stock WotLK's own Spells folder naming convention).

`SpellVisual`/`CreatureModelData`/`CreatureDisplayInfo` (unlike `SpellVisualKit`/`SpellVisualEffectName`)
are also loaded server-side, straight into `sSpellVisualStore`/`sCreatureModelDataStore`/
`sCreatureDisplayInfoStore` via `spellvisual_dbc`/`creaturemodeldata_dbc`/`creaturedisplayinfo_dbc`
SQL overlay tables (`DBCStores.cpp`'s `LOAD_DBC` calls - confirmed live: booting worldserver with
only the client-patch DBCs updated, no matching SQL, produced "Creature (Entry: 300002) lists
non-existing CreatureDisplayID id (90003)" at boot). `--sql-out PATH` emits the matching pending
migration from the exact same row-building functions this script already uses for the binary DBCs,
so the two can't drift - the client sees a model ID, the server accepts that same ID as real.

Usage:
    python3 apps/dbc-tools/patch_mage_vfx_models.py
    python3 apps/dbc-tools/patch_mage_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib import dbcfmt, dbcfile
from lib.sql_out import _table_block

DBC_DIR = Path(__file__).resolve().parent / "var" / "model-visual-dbc" / "DBFilesClient"

# Every extracted asset ships under this archive-relative path (see build_patch_m.py, which packs
# var/model-visual-dbc/SPELLS/* at this same "SPELLS\\" prefix). Referenced here as a backslash
# path ending in .mdx, matching the stock client's own convention even for files that are genuinely
# .m2 on disk - already proven working for Frozen Orb's existing custom model (ID 90001), whose
# ModelName is "Spells\\IceNuke_Missile.mdx" despite the real file being IceNuke_Missile.m2; the
# client resolves the .mdx -> .m2 alias itself.
def model_path(filename_no_ext: str) -> str:
    return f"SPELLS\\{filename_no_ext}.mdx"


def _row(table: dbcfmt.DbcTable, id_: int, **fields) -> dict:
    row = dbcfile.empty_row(table)
    row["ID"] = id_
    row.update(fields)
    return row


# "None" sentinel every stock SpellVisualKit row uses for CharProc_1-4 AND StartAnimID when unset
# (confirmed against Frostbolt's real CastKit 202, Meteor's real CastKit 172, and stock precast kit
# 171 - all three use this for both, never 0). dbcfile.empty_row()'s generic 0-fill is wrong for
# both fields: CharProc 0 is apparently a real (if degenerate, all-zeroed) proc type, and
# StartAnimID 0 is presumably a real animation ID too (plausibly "Stand") - discovered while
# diagnosing why a hand effect AND a real AnimID (2 different values tried) both failed to render
# any change at all on a from-scratch kit ("we still stand there" - see build_kit_rows()'s notes).
# If StartAnimID=0 forces the client to display anim 0 before anything else, and it never advances
# past that first step, that alone would explain both symptoms.
NOFIELD = 4294967295


def _kit_row(id_: int, **fields) -> dict:
    """_row() for SpellVisualKit.dbc specifically, pre-filled with the stock "none" sentinel on
    StartAnimID and all 4 CharProc slots so every custom kit matches stock convention unless a row
    deliberately sets one of these fields for real."""
    row = _row(
        dbcfmt.SPELLVISUALKIT, id_,
        StartAnimID=NOFIELD,
        CharProc_1=NOFIELD, CharProc_2=NOFIELD, CharProc_3=NOFIELD, CharProc_4=NOFIELD,
    )
    row.update(fields)
    return row


def _merge(path: Path, table: dbcfmt.DbcTable, new_rows: list[dict]) -> int:
    """Read existing rows, upsert new_rows by ID (replace a matching ID, append a new one), write back.

    Returns the number of rows actually changed (added or replaced; 0 on a rerun where nothing
    about this script's output differs from what's already on disk)."""
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


# --- SpellVisualEffectName.dbc: one row per extracted model (90001-90009) ---

EFFECT_METEOR_MISSILE = 90001
EFFECT_METEOR_IMPACT_WORLD = 90002
EFFECT_GLACIALSPIKE_STATEHAND = 90003
EFFECT_GLACIALSPIKE_DUMMYHOLD = 90004
EFFECT_GLACIALSPIKE_CONVERGING = 90005
EFFECT_GLACIALSPIKE_LAUNCHED = 90006
EFFECT_GLACIALSPIKE_IMPACTCHEST = 90007
EFFECT_FLURRY_MISSILE = 90008
EFFECT_FLURRY_IMPACTCHEST = 90009
# Not from the cfx_mage_glacialspike_* family - found by browsing patch-N.MPQ for any Spike/
# Glacial/Icicle-named model after EFFECT_GLACIALSPIKE_LAUNCHED (below) turned out to be mostly
# particle effects live. User-confirmed correct after inspecting it in a model viewer.
EFFECT_GLACIALSPIKE_LAUNCHED_V2 = 90011

# (id, display name, extracted filename without extension)
# NOTE: EFFECT_METEOR_MISSILE (90001) is unused by any SpellVisual/SpellVisualKit row below - the
# falling meteor is a temporary summoned creature instead (see build_creature_model_row/
# build_creature_display_row and spell_mage.cpp's npc_mage_meteor_missile), same scope decision
# fire-mage-meteor-vfx.md documents. Minted anyway and left orphaned rather than removed, matching
# this codebase's own precedent for a superseded-but-harmless row (frozen_orb_periodic_200009's own
# notes: "left as an orphaned row rather than deleted") - available if a future pass ever revisits
# the DBC-native-missile alternative the VFX doc's "Open questions" section left open.
_EFFECT_NAMES = (
    (EFFECT_METEOR_MISSILE, "Meteor Missile (Custom)", "mage_meteor_missile"),
    (EFFECT_METEOR_IMPACT_WORLD, "Meteor Impact/Burn (Custom)", "mage_meteor_impactstate_world"),
    (EFFECT_GLACIALSPIKE_STATEHAND, "Glacial Spike Cast Hand (Custom)", "cfx_mage_glacialspike_statehand"),
    (EFFECT_GLACIALSPIKE_DUMMYHOLD, "Glacial Spike Windup 1 (Custom)", "cfx_mage_glacialspike_dummyholdmissile"),
    (EFFECT_GLACIALSPIKE_CONVERGING, "Glacial Spike Windup 2 (Custom)", "cfx_mage_glacialspike_convergingmissiles"),
    (EFFECT_GLACIALSPIKE_LAUNCHED, "Glacial Spike Launch (Custom)", "cfx_mage_glacialspike_launchedmissile"),
    (EFFECT_GLACIALSPIKE_IMPACTCHEST, "Glacial Spike Impact (Custom)", "cfx_mage_glacialspike_impactchest"),
    (EFFECT_FLURRY_MISSILE, "Flurry Missile (Custom)", "cfx_mage_flurry_missile"),
    (EFFECT_FLURRY_IMPACTCHEST, "Flurry Impact (Custom)", "cfx_mage_flurry_impactchest"),
    (EFFECT_GLACIALSPIKE_LAUNCHED_V2, "Glacial Spike Launch v2 (Custom)", "cfx_mage_iciclemastery_launchedmissile"),
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


# --- SpellVisualKit.dbc: one row per role that needs a Kit wrapper (90001-90004) ---
# (HasMissile+MissileModel on a SpellVisual row points straight at a SpellVisualEffectName ID with
# no Kit indirection needed - confirmed against stock kit 9239's BaseEffect field and spell 7479's
# own InstantAreaKit usage - so the windup/launch missile stages below don't need their own Kit.)

KIT_METEOR_IMPACT = 90001
KIT_GLACIALSPIKE_CAST = 90002
KIT_GLACIALSPIKE_IMPACT = 90003
KIT_FLURRY_IMPACT = 90004
KIT_FIRE_PRECAST_HAND = 90005
KIT_FROST_PRECAST_HAND = 90006
KIT_GLACIALSPIKE_PRECAST = 90007

# Stock SpellVisualEffectName IDs (not minted by this script - already shipped in the base 3.3.5a
# client). Found by tracing what real instant/quick-flourish mage spells use for their own
# PrecastKit hand glow: Pyroblast (SpellVisual 2253, PrecastKit 30) and Blast Wave (SpellVisual 963,
# PrecastKit 60) both point at effect 287 "Fire Precast Hand"; Frostbolt (SpellVisual 13, PrecastKit
# 194) points at effect 117 "Ice Precast Low Hand" (the "Frost_Precast_*" effects, e.g. 63/206, are
# all "zzOLD__"-prefixed and unused by any live stock kit - Ice_Precast_Low_Hand is the current one).
EFFECT_FIRE_PRECAST_HAND = 287
EFFECT_ICE_PRECAST_HAND = 117
# Frostbolt's own real CastKit (202, for its real ~3s cast bar - not its PrecastKit 194 above) uses
# this for LeftHandEffect/RightHandEffect - the exact same proven "hand glows for the whole visible
# cast bar" mechanism Glacial Spike (also a real cast-bar spell) needs. Confirmed live/undisputed
# retail behavior (Frostbolt's hand visibly glows blue for its entire cast), unlike the untested
# custom EFFECT_GLACIALSPIKE_STATEHAND model.
EFFECT_ICE_CAST_HAND = 421


def build_kit_rows() -> list[dict]:
    return [
        _kit_row(KIT_METEOR_IMPACT, BaseEffect=EFFECT_METEOR_IMPACT_WORLD),
        # 6th pass (2026-09-18): live results from the 5th pass ruled two things out and pointed at
        # a real bug -
        #  - CharProc_1=8 + a blue color (Meteor's own stock hand-glow recipe, just recolored)
        #    produced NO glow at all on a player Mage, unlike Meteor's NPC/boss use of it. Dropped
        #    in favor of the one mechanism actually proven live on a player character: Frostbolt's
        #    own real CastKit (202) - LeftHandEffect=RightHandEffect=EFFECT_ICE_CAST_HAND (421).
        #  - AnimID=124 (like AnimID=53 before it - two different, real, player-valid animation IDs
        #    from AnimationData.dbc) produced no visible animation change at all ("we still stand
        #    there"). _kit_row's own new StartAnimID=NOFIELD default (see above) targets the likely
        #    cause: this kit's StartAnimID was 0 (a real anim ID, not "none") since our helper
        #    zero-filled it - if the client shows StartAnimID before AnimID and never advances past
        #    it, that alone explains "stuck standing" regardless of which AnimID is set. Reverted to
        #    AnimID=53 (Frostbolt's own exact value) to test against the fully-proven baseline
        #    rather than guessing a 3rd animation.
        _kit_row(
            KIT_GLACIALSPIKE_CAST,
            AnimID=53, SoundID=7140,
            LeftHandEffect=EFFECT_ICE_CAST_HAND, RightHandEffect=EFFECT_ICE_CAST_HAND,
        ),
        # New PrecastKit for 200002 (see SV_GLACIAL_SPIKE_CAST below). Playtest feedback (6th pass):
        # the converging visual correctly fires at cast start now (confirmed live), but anchors at
        # the character's base, not above the head - moved from WorldEffect to HeadEffect, the field
        # this kit format has specifically for head-bone attachment. The "plays twice, needs a
        # delay" feedback has no obvious corresponding field anywhere in SpellVisualKit/
        # SpellVisualEffectName (no duration/loop-count column exists) - likely the model's own
        # native animation length being shorter than however long the client holds PrecastKit open,
        # not something adjustable from here.
        # 7th pass (2026-09-19): CastKit's hand glow only flashes at cast *completion*, not held
        # through the bar - so also put the same hand effect on the PrecastKit to get a flash at
        # cast *start* too (bracket start+end rather than end-only) until/unless a sustained-hold
        # mechanism is found.
        # 8th pass (2026-09-19): live glow confirmed working (both kits), but the raised-hands cast
        # ANIMATION still never played. Root cause found by decoding Frostbolt's real PrecastKit
        # (194) byte-for-byte: it sets AnimID=51 (ReadySpellDirected) - the transition-in pose that
        # the CastKit's AnimID=53 (SpellCastDirected) loop continues from. Our PrecastKit never set
        # an AnimID at all (defaulted to 0), so the client never had a transition to play before the
        # CastKit's loop was supposed to take over - explains "hands glow, but we still stand there"
        # even after CastKit's own AnimID=53 was confirmed byte-identical to Frostbolt's. Added
        # AnimID=51 here to match Frostbolt's exact two-stage precast->cast animation handoff.
        _kit_row(
            KIT_GLACIALSPIKE_PRECAST,
            AnimID=51,
            HeadEffect=EFFECT_GLACIALSPIKE_CONVERGING,
            LeftHandEffect=EFFECT_ICE_CAST_HAND, RightHandEffect=EFFECT_ICE_CAST_HAND,
        ),
        _kit_row(KIT_GLACIALSPIKE_IMPACT, ChestEffect=EFFECT_GLACIALSPIKE_IMPACTCHEST),
        _kit_row(KIT_FLURRY_IMPACT, ChestEffect=EFFECT_FLURRY_IMPACTCHEST),
        # AnimID=108 kept from the stock kit 171 flourish these spells used before (the gesture
        # itself already looked right - only the missing hand glow was the actual bug) - now with a
        # school-flavored hand effect actually attached, which kit 171 never had.
        _kit_row(
            KIT_FIRE_PRECAST_HAND,
            AnimID=108, LeftHandEffect=EFFECT_FIRE_PRECAST_HAND, RightHandEffect=EFFECT_FIRE_PRECAST_HAND,
        ),
        _kit_row(
            KIT_FROST_PRECAST_HAND,
            AnimID=108, LeftHandEffect=EFFECT_ICE_PRECAST_HAND, RightHandEffect=EFFECT_ICE_PRECAST_HAND,
        ),
    ]


# --- SpellVisual.dbc: one row per spell/stage (90001-90010) ---
# PrecastKit is correct (not CastKit) for these four 0-cast-time spells - see
# fire-mage-meteor-vfx.md's "Casting animation" section. Originally wired to stock kit 171 (spell
# 7479's own PrecastKit verbatim), which turned out to carry an AnimID and nothing else - no hand
# effect, so the flourish played with no glow. KIT_FIRE_PRECAST_HAND/KIT_FROST_PRECAST_HAND (above)
# keep that same AnimID but add the school-flavored hand glow real stock spells use for their own
# precast (Pyroblast/Blast Wave -> Fire Precast Hand, Frostbolt -> Ice Precast Low Hand).

SV_FLASHPOINT = 90001              # spell 200111
SV_METEOR_CAST = 90002             # spell 200095
SV_METEOR_IMPACT = 90003           # spell 200096
SV_FROZEN_ORB_CAST = 90004         # spell 200007
SV_GLACIAL_SPIKE_CAST = 90005      # spell 200002 (real 2.5s cast bar - gets both a CastKit and,
                                    # as of the 5th pass, a PrecastKit too for the converging visual)
# 90006/90007 are orphaned - 200025/200026 (the old 2-stage post-cast ramp) are no longer cast by
# anything (see spell_mage_glacial_spike's class comment in spell_mage.cpp); left minted rather
# than removed, same "orphaned but harmless" precedent as EFFECT_METEOR_MISSILE above.
SV_GLACIAL_SPIKE_WINDUP1 = 90006   # spell 200025 (unused)
SV_GLACIAL_SPIKE_WINDUP2 = 90007   # spell 200026 (unused)
SV_GLACIAL_SPIKE_IMPACT = 90008    # spell 200027
SV_FLURRY = 90009                  # spell 200004 (button spell - PrecastKit only, see 90010)
SV_FLURRY_BOLT = 90010             # spell 200037 (one of 3 sequential bolts - missile+impact)


def build_spellvisual_rows() -> list[dict]:
    return [
        _row(dbcfmt.SPELLVISUAL, SV_FLASHPOINT, PrecastKit=KIT_FIRE_PRECAST_HAND),
        _row(dbcfmt.SPELLVISUAL, SV_METEOR_CAST, PrecastKit=KIT_FIRE_PRECAST_HAND),
        _row(
            dbcfmt.SPELLVISUAL, SV_METEOR_IMPACT,
            InstantAreaKit=KIT_METEOR_IMPACT, PersistentAreaKit=KIT_METEOR_IMPACT,
        ),
        _row(dbcfmt.SPELLVISUAL, SV_FROZEN_ORB_CAST, PrecastKit=KIT_FROST_PRECAST_HAND),
        _row(
            dbcfmt.SPELLVISUAL, SV_GLACIAL_SPIKE_CAST,
            PrecastKit=KIT_GLACIALSPIKE_PRECAST, CastKit=KIT_GLACIALSPIKE_CAST,
        ),
        _row(dbcfmt.SPELLVISUAL, SV_GLACIAL_SPIKE_WINDUP1, HasMissile=1, MissileModel=EFFECT_GLACIALSPIKE_DUMMYHOLD),
        _row(dbcfmt.SPELLVISUAL, SV_GLACIAL_SPIKE_WINDUP2, HasMissile=1, MissileModel=EFFECT_GLACIALSPIKE_CONVERGING),
        # Playtest feedback (2026-09-18): EFFECT_GLACIALSPIKE_LAUNCHED ("...launchedmissile") reads
        # as mostly particle effects live, with little solid visible mesh for the actual spike in
        # flight; the DUMMYHOLD swap that followed ("didn't do anything for us") was no better.
        # Final swap after browsing patch-N.MPQ for any Spike/Glacial/Icicle-named model and
        # checking candidates in a model viewer: EFFECT_GLACIALSPIKE_LAUNCHED_V2
        # ("cfx_mage_iciclemastery_launchedmissile" - not from the glacialspike asset family at
        # all), user-confirmed correct. (LAUNCHED/DUMMYHOLD are left orphaned rather than removed -
        # same precedent as EFFECT_METEOR_MISSILE above; DUMMYHOLD is still in active use elsewhere,
        # as the precast HeadEffect and the orphaned windup1 spell's MissileModel.)
        _row(
            dbcfmt.SPELLVISUAL, SV_GLACIAL_SPIKE_IMPACT,
            HasMissile=1, MissileModel=EFFECT_GLACIALSPIKE_LAUNCHED_V2, ImpactKit=KIT_GLACIALSPIKE_IMPACT,
        ),
        # Playtest feedback (2026-09-18): Flurry redesigned into 3 sequential bolts (see
        # spell_mage_flurry::FireBolts, spell_mage.cpp) - the button spell (200004) now only gets
        # the cast flourish, and each bolt (200037) carries its own missile+impact visual below.
        _row(dbcfmt.SPELLVISUAL, SV_FLURRY, PrecastKit=KIT_FROST_PRECAST_HAND),
        # MissileMotion=22 - undocumented client-only enum (no lookup table anywhere, client or
        # server; AzerothCore doesn't even load this field - see docs/MissileMotionReference.md).
        # Playtest feedback (2026-09-18): 41 ("Test Spiral") and 26 ("Wave Beam") both tried and
        # rejected live; trying 22 next - the only stock spell using it is named "Shadow Spiral"
        # (37500).
        _row(
            dbcfmt.SPELLVISUAL, SV_FLURRY_BOLT,
            HasMissile=1, MissileModel=EFFECT_FLURRY_MISSILE, ImpactKit=KIT_FLURRY_IMPACT,
            MissileMotion=22,
        ),
    ]


# --- CreatureModelData.dbc / CreatureDisplayInfo.dbc: Frozen Orb's model swap ---
# 90001 is already taken (Frozen Orb's *current* model, Spells\IceNuke_Missile.mdx) - this mints
# 90002 pointing at the purpose-built Mage_FrostOrb_Orb model instead. The pending SQL migration
# (data/sql/updates/pending_db_world/) repoints creature_template_model's CreatureDisplayID for
# entry 300001 from 90001 to 90002, same shape as the existing 26753->90001 swap already in
# data/sql/updates/db_world/2026_09_01_01.sql.
FROZEN_ORB_MODEL_ID = 90002


def build_creature_model_row() -> dict:
    return _row(
        dbcfmt.CREATUREMODELDATA, FROZEN_ORB_MODEL_ID,
        ModelName=model_path("Mage_FrostOrb_Orb"), ModelScale=1.0,
    )


def build_creature_display_row() -> dict:
    # Mirrors row 90001's own values exactly (read from the working copy) - ModelID/CreatureModelScale
    # /CreatureModelAlpha are the only fields that matter for a plain "swap the model" row.
    return _row(
        dbcfmt.CREATUREDISPLAYINFO, FROZEN_ORB_MODEL_ID,
        ModelID=FROZEN_ORB_MODEL_ID, CreatureModelScale=1.0, CreatureModelAlpha=255,
    )


# Meteor's falling-meteor visual creature (NPC_MAGE_METEOR_MISSILE, spell_mage.cpp) needs its own
# CreatureModelData/CreatureDisplayInfo row - same mechanism as Frozen Orb's orb, a different model.
METEOR_MISSILE_MODEL_ID = 90003


def build_meteor_missile_model_row() -> dict:
    return _row(
        dbcfmt.CREATUREMODELDATA, METEOR_MISSILE_MODEL_ID,
        ModelName=model_path("mage_meteor_missile"), ModelScale=1.0,
    )


def build_meteor_missile_display_row() -> dict:
    return _row(
        dbcfmt.CREATUREDISPLAYINFO, METEOR_MISSILE_MODEL_ID,
        ModelID=METEOR_MISSILE_MODEL_ID, CreatureModelScale=1.0, CreatureModelAlpha=255,
    )


def build_pending_sql() -> str:
    """The server-side counterpart to the binary DBC rows above, for the 3 tables AzerothCore
    actually loads (`DBCStores.cpp`'s `LOAD_DBC(sSpellVisualStore/sCreatureModelDataStore/
    sCreatureDisplayInfoStore, ...)`). `SpellVisualKit`/`SpellVisualEffectName` have no LOAD_DBC
    call at all (confirmed by grep) - client-only, no SQL needed. Range-deletes exactly the IDs
    each table mints here (never touching 90001, which Frozen Orb's pre-existing row still owns in
    CreatureModelData/CreatureDisplayInfo) - same idempotent-on-rerun shape `lib/sql_out.py` uses
    for the normal generate.py pipeline, reused directly here rather than re-implemented."""
    blocks = [
        _table_block(dbcfmt.SPELLVISUAL, {"start": 90001, "end": 90010}, build_spellvisual_rows(), []),
        _table_block(
            dbcfmt.CREATUREMODELDATA, {"start": 90002, "end": 90003},
            [build_creature_model_row(), build_meteor_missile_model_row()], [],
        ),
        _table_block(
            dbcfmt.CREATUREDISPLAYINFO, {"start": 90002, "end": 90003},
            [build_creature_display_row(), build_meteor_missile_display_row()], [],
        ),
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
    added += _merge(
        DBC_DIR / "CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA,
        [build_creature_model_row(), build_meteor_missile_model_row()],
    )
    added += _merge(
        DBC_DIR / "CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO,
        [build_creature_display_row(), build_meteor_missile_display_row()],
    )
    print(f"added {added} row(s) across the 5 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
