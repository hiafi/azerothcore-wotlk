#!/usr/bin/env python3
"""
One-off DBC content patch: mints new SpellVisual.dbc / SpellVisualKit.dbc /
SpellVisualEffectName.dbc / SoundEntries.dbc rows for the Balance Druid rework's Starsurge
(200333) and Fury of Elune (200336 aura + 200338 beam tick) - mined from the Ascension client
backup, same source and shape as patch_priest_vfx_models.py (whose row helpers this reuses).

What Ascension ships, traced from its own Spell.dbc:
- Starsurge 954800 -> SpellVisual 117080: Precast/CastKit with druid_starsurge_precast_omni hand
  flares, a druid_starsurge_missile projectile (EffectName scale 1.1) and a TargetImpactKit with
  druid_starsurge_impact. Its impact sound (SoundEntries 23611) is only Lightning Bolt's impact,
  so the Lunar Strike impact sound (Ascension 70929) is used instead - it's being minted for Fury
  of Elune anyway and fits an Astral hit.
- Fury of Elune 86406 -> SpellVisual 20231: a PersistentAreaKit whose WorldEffect is
  cfx_druid_furyofelune_statebase (the real Legion beam) with a looping beam sound. Our 200336 is
  an aura on the target (the beam follows it for free), not a ground zone, so the same model goes
  on the aura's StateKit as a BaseEffect instead. The 0.5s damage tick (200338) gets the stock
  Moonfire impact (EffectName 1885) plus the Fury of Elune damage-impact sound.

Resto's Flourish (200564) and Bloom (200560 cast, 200561 jump) were added later:
- Flourish: stock nature cast hands (kit 183) and the stock "Flourish Impact" burst + sound (kit
  10691, druid_flourish.mdx). The ground effect is Ascension's Druid_Efflorescence_Persistent on
  the PersistentAreaKit of 200603, a hidden 1.5 s ground zone Flourish's buff triggers at the
  caster's feet. Model settings (AreaEffectSize 0, Scale 3.4) are Ascension's own Efflorescence
  row (SpellVisualEffectName 236522 in SpellVisual 22251).
- Bloom: Ascension's Wrath orb (Druid_Wrath_Missile_V2, its SpellVisual 278885) on the stock
  "Parabola (High)" MissileMotion (224), landing with the stock Nourish flower (kit 10693). The
  jump copy has no CastKit, since Druid::StartBloomJumps casts it from the previous target.

Assets (gitignored working copies, extracted by hand via `smpq -x`, see
docs/ascension-asset-mining.md):
- var/model-visual-dbc/SPELLS/: the 6 models + NN.skin files (patch-N.MPQ), plus the 16
  textures they reference that stock 3.3.5a doesn't have (read from each .m2's texture table -
  the rest resolve to stock common.MPQ/lichking.MPQ/patch*.MPQ files). Resto added only
  rune11.blp (Efflorescence); the Wrath orb's 3 textures are all stock.
- var/model-visual-dbc/SOUND/: the sounds (patch-O.MPQ), converted .ogg -> 16-bit PCM .wav since
  stock 3.3.5a SoundEntries never references an .ogg. build_patch_m.py packs them at
  Sound\\Spells\\.
- var/model-visual-dbc/DBFilesClient/SoundEntries.dbc: the server's stock copy
  (env/dist/data/dbc/), which these rows extend.

SoundEntries rows ship client-only: the server loads SoundEntries.dbc, but nothing server-side
looks up a sound that only a SpellVisualKit references. SpellVisual is server-loaded, so
`--sql-out PATH` emits its overlay, same as the Priest/Mage scripts.

Usage:
    python3 apps/dbc-tools/patch_druid_vfx_models.py
    python3 apps/dbc-tools/patch_druid_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib import dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import (
    DBC_DIR, NOFIELD, SOUND_FLAG_LOOPING, _kit_row, _merge, _row, _sound_row, model_path,
)

# --- Stock IDs reused as-is ---

EFFECT_MOONFIRE_IMPACT_BASE_STOCK = 1885  # spells\moonfire_impact_base.mdx (Moonfire's ImpactKit 3293)
KIT_NATURE_CAST_HAND_STOCK = 183          # Healing Touch/Nourish CastKit: anim 54 + Nature_Cast_Hand
KIT_FLOURISH_IMPACT_STOCK = 10691         # druid_flourish.mdx + Druid_Flourish sound (stock SV 11568)
KIT_NOURISH_IMPACT_STOCK = 10693          # druid_nourish.mdx flower + sound (Nourish's ImpactKit)
MISSILE_MOTION_PARABOLA_HIGH_STOCK = 224  # SpellMissileMotion.dbc "Parabola (High)"
MISSILE_DESTINATION_CHEST = 1             # stock heals' MissileDestinationAttachment
SOUND_STARSURGE_PRECAST_STOCK = 3087      # Ascension's own Starsurge PrecastKit sound, stock
SOUND_MAGIC_CAST_STOCK = 1641             # Ascension's own Starsurge CastKit sound, stock (Moonfire/Starfire cast)
NO_ATTACHMENT = -1                        # SpellVisual's signed "none" (dbcfmt.SPELLVISUAL.signed)

# --- SoundEntries.dbc (90001-90004; stock tops out at 18019) ---

SOUND_STARSURGE_IMPACT = 90001
SOUND_FURY_OF_ELUNE_START = 90002
SOUND_FURY_OF_ELUNE_BEAM_LOOP = 90003
SOUND_FURY_OF_ELUNE_IMPACT = 90004


def build_sound_rows() -> list[dict]:
    return [
        _sound_row(
            SOUND_STARSURGE_IMPACT, "spell_dr_revamp_lunarstrike_impactv2",
            [f"spell_dr_revamp_lunarstrike_impactv2_0{i}" for i in (1, 2, 3)],
            min_distance=6.0, cutoff=32.0,
        ),
        _sound_row(
            SOUND_FURY_OF_ELUNE_START, "spell_dr_furyofelune_start_01",
            ["spell_dr_furyofelune_start_01"], min_distance=12.0, cutoff=55.0,
        ),
        _sound_row(
            SOUND_FURY_OF_ELUNE_BEAM_LOOP, "spell_dr_talent_furyofelune_beam_loop_01",
            ["spell_dr_talent_furyofelune_beam_loop_01"], min_distance=21.0, cutoff=75.0,
            flags=SOUND_FLAG_LOOPING,
        ),
        _sound_row(
            SOUND_FURY_OF_ELUNE_IMPACT, "spell_dr_furyofelune_damageimpact",
            [f"spell_dr_furyofelune_damageimpact_0{i}" for i in range(1, 7)],
            min_distance=6.0, cutoff=32.0,
        ),
    ]


# --- SpellVisualEffectName.dbc (90018-90023) ---

EFFECT_STARSURGE_MISSILE = 90018
EFFECT_STARSURGE_PRECAST = 90019
EFFECT_STARSURGE_IMPACT = 90020
EFFECT_FURY_OF_ELUNE_STATEBASE = 90021
EFFECT_EFFLORESCENCE_PERSISTENT = 90022
EFFECT_BLOOM_MISSILE = 90023


def build_effect_name_rows() -> list[dict]:
    rows = []
    for id_, name, filename, scale in (
        (EFFECT_STARSURGE_MISSILE, "Starsurge Missile (Custom)", "Druid_Starsurge_Missile", 1.1),
        (EFFECT_STARSURGE_PRECAST, "Starsurge Precast (Custom)", "Druid_Starsurge_Precast_Omni", 1.0),
        (EFFECT_STARSURGE_IMPACT, "Starsurge Impact (Custom)", "Druid_Starsurge_Impact", 1.0),
        (EFFECT_FURY_OF_ELUNE_STATEBASE, "Fury of Elune State Base (Custom)", "cfx_druid_furyofelune_statebase", 1.0),
        (EFFECT_BLOOM_MISSILE, "Bloom Missile (Custom)", "Druid_Wrath_Missile_V2", 1.0),
    ):
        rows.append(_row(
            dbcfmt.SPELLVISUALEFFECTNAME, id_,
            Name=name, FileName=model_path(filename),
            AreaEffectSize=1.0, Scale=scale, MinAllowedScale=0.01, MaxAllowedScale=100.0,
        ))
    # AreaEffectSize 0 keeps the model at a fixed Scale instead of stretching it to the zone radius.
    rows.append(_row(
        dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_EFFLORESCENCE_PERSISTENT,
        Name="Efflorescence Persistent (Custom)", FileName=model_path("Druid_Efflorescence_Persistent"),
        AreaEffectSize=0.0, Scale=3.4, MinAllowedScale=0.01, MaxAllowedScale=100.0,
    ))
    return rows


# --- SpellVisualKit.dbc (90018-90024) ---

KIT_STARSURGE_PRECAST = 90018
KIT_STARSURGE_CAST = 90019
KIT_STARSURGE_IMPACT = 90020
KIT_FURY_OF_ELUNE_CAST = 90021
KIT_FURY_OF_ELUNE_STATE = 90022
KIT_FURY_OF_ELUNE_TICK = 90023
KIT_EFFLORESCENCE_PERSISTENT = 90024


def build_kit_rows() -> list[dict]:
    return [
        _kit_row(
            KIT_STARSURGE_PRECAST,
            AnimID=51, SoundID=SOUND_STARSURGE_PRECAST_STOCK,
            LeftHandEffect=EFFECT_STARSURGE_PRECAST, RightHandEffect=EFFECT_STARSURGE_PRECAST,
        ),
        _kit_row(
            KIT_STARSURGE_CAST,
            AnimID=53, SoundID=SOUND_MAGIC_CAST_STOCK,
            LeftHandEffect=EFFECT_STARSURGE_PRECAST, RightHandEffect=EFFECT_STARSURGE_PRECAST,
        ),
        _kit_row(KIT_STARSURGE_IMPACT, AnimID=NOFIELD, BaseEffect=EFFECT_STARSURGE_IMPACT, SoundID=SOUND_STARSURGE_IMPACT),
        _kit_row(KIT_FURY_OF_ELUNE_CAST, AnimID=54, SoundID=SOUND_FURY_OF_ELUNE_START),
        _kit_row(
            KIT_FURY_OF_ELUNE_STATE,
            AnimID=NOFIELD, BaseEffect=EFFECT_FURY_OF_ELUNE_STATEBASE, SoundID=SOUND_FURY_OF_ELUNE_BEAM_LOOP,
        ),
        _kit_row(
            KIT_FURY_OF_ELUNE_TICK,
            AnimID=NOFIELD, BaseEffect=EFFECT_MOONFIRE_IMPACT_BASE_STOCK, SoundID=SOUND_FURY_OF_ELUNE_IMPACT,
        ),
        _kit_row(KIT_EFFLORESCENCE_PERSISTENT, AnimID=NOFIELD, BaseEffect=EFFECT_EFFLORESCENCE_PERSISTENT),
    ]


# --- SpellVisual.dbc (90018-90024) ---

SV_STARSURGE = 90018          # spell 200333
SV_FURY_OF_ELUNE = 90019      # spell 200336 (the aura on the target)
SV_FURY_OF_ELUNE_TICK = 90020  # spell 200338 (0.5s beam damage)
SV_FLOURISH = 90021            # spell 200564
SV_FLOURISH_GROUND = 90022     # spell 200603 (the 1.5 s ground zone)
SV_BLOOM = 90023               # spell 200560 (druid -> first target)
SV_BLOOM_JUMP = 90024          # spell 200561 (previous target -> next target)


def build_spellvisual_rows() -> list[dict]:
    return [
        _row(
            dbcfmt.SPELLVISUAL, SV_STARSURGE,
            PrecastKit=KIT_STARSURGE_PRECAST, CastKit=KIT_STARSURGE_CAST, TargetImpactKit=KIT_STARSURGE_IMPACT,
            HasMissile=1, MissileModel=EFFECT_STARSURGE_MISSILE, MissileDestinationAttachment=34,
            MissileAttachment=NO_ATTACHMENT, Flags=512,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_FURY_OF_ELUNE,
            CastKit=KIT_FURY_OF_ELUNE_CAST, StateKit=KIT_FURY_OF_ELUNE_STATE,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_FURY_OF_ELUNE_TICK,
            ImpactKit=KIT_FURY_OF_ELUNE_TICK,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_FLOURISH,
            CastKit=KIT_NATURE_CAST_HAND_STOCK, ImpactKit=KIT_FLOURISH_IMPACT_STOCK,
            MissileDestinationAttachment=MISSILE_DESTINATION_CHEST, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_FLOURISH_GROUND,
            PersistentAreaKit=KIT_EFFLORESCENCE_PERSISTENT,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_BLOOM,
            CastKit=KIT_NATURE_CAST_HAND_STOCK, ImpactKit=KIT_NOURISH_IMPACT_STOCK,
            HasMissile=1, MissileModel=EFFECT_BLOOM_MISSILE, MissileMotion=MISSILE_MOTION_PARABOLA_HIGH_STOCK,
            MissileDestinationAttachment=MISSILE_DESTINATION_CHEST, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_BLOOM_JUMP,
            ImpactKit=KIT_NOURISH_IMPACT_STOCK,
            HasMissile=1, MissileModel=EFFECT_BLOOM_MISSILE, MissileMotion=MISSILE_MOTION_PARABOLA_HIGH_STOCK,
            MissileDestinationAttachment=MISSILE_DESTINATION_CHEST, MissileAttachment=NO_ATTACHMENT,
        ),
    ]


def build_pending_sql() -> str:
    """Server-side overlay for SpellVisual only - see the module docstring for SoundEntries."""
    return _table_block(dbcfmt.SPELLVISUAL, {"start": 90018, "end": 90024}, build_spellvisual_rows(), []) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sql-out", type=Path, default=None,
        help="Write the matching server-side SQL migration to this path (see module docstring).",
    )
    args = parser.parse_args()

    added = 0
    added += _merge(DBC_DIR / "SoundEntries.dbc", dbcfmt.SOUNDENTRIES, build_sound_rows())
    added += _merge(DBC_DIR / "SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME, build_effect_name_rows())
    added += _merge(DBC_DIR / "SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, build_kit_rows())
    added += _merge(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL, build_spellvisual_rows())
    print(f"added {added} row(s) across the 4 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
