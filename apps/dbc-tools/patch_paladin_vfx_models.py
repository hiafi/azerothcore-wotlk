#!/usr/bin/env python3
"""
One-off DBC content patch: mints SpellVisual.dbc / SpellVisualKit.dbc / SpellVisualEffectName.dbc /
SoundEntries.dbc rows for the Paladin rework's Light's Hammer (201200), Divine Toll (201203) and
Execution Sentence (201410-201412), mined from the Ascension client backup - same source and shape as patch_warlock_vfx_models.py.

Light's Hammer:
- Ascension's 954801 throws spells\\paladin_lightshammer_missile (SpellVisual 125212, Speed 20) and
  summons creature 105939 at the impact point; that creature shows Paladin_LightsHammer_State. Ours
  is a 14 s PERSISTENT_AREA_AURA with no travel time, so the grounded hammer goes on the dynamic
  object's PersistentAreaKit instead (the Efflorescence pattern, patch_druid_vfx_models.py) and the
  landing burst (Paladin_LightsHammer_Impact) on its ImpactAreaKit. The missile is left out: it
  needs Speed on the spell, which would delay every heal/damage tick by the flight time.
- AreaEffectSize 0 keeps both models at a fixed Scale instead of stretching them to the 10 yd radius.
- CastKit is stock 6409 (Hammer of Wrath's throw: anim 107 + holy hammer in the right hand), the
  kit the old stand-in SpellVisual 7250 already played.
- Impact sound: Ascension's spell_pa_lightshammer_impact01-05 (their SoundEntries 27265).
- The 2 s ticks mirror Ascension's "Arcing Light" ticks: the damage tick 201202 (their SpellVisual
  124246) plays the impact model on each enemy's chest with a lightning-bolt impact sound (stock 1506
  in place of their custom 27256), the heal tick 201201 (their 125282) plays
  Paladin_Veneration_Impact at each ally's feet with stock Flash Heal 1434.

Divine Toll:
- Ascension has no Divine Toll. Its retail cast art, cfx_kyrian_paladin_castchest (the Kyrian bell
  burst), is in patch-N.MPQ but Ascension never wires it to a SpellVisualEffectName, so it is
  untested on this client. The cast kit therefore layers it on top of a copy of stock Holy Nova's
  cast kit 3154 (holynova_impact_base ring + Holy_Precast_High hands, anim 54, sound 2562): if the
  Kyrian model renders blank, the Holy Nova burst still plays.

Execution Sentence:
- Ascension's 954817/954818 (SpellVisual 123279) shows the falling hammer as a StateKit on the 10 s
  DoT: Paladin_ExecutionSentence_VerticleMissile on BaseEffect (its one animation runs 11.7 s, so the
  hammer is still descending when the aura ends, same as Ascension) with the looping
  spell_pa_executionsentence_state sound (their 28665). Ours is the same 10 s DoT, 201410.
- Cast: stock kit 191 (Holy_Precast_High hands, anim 54, sound 2562); Ascension's 100191 is the
  same kit with the effect IDs shifted by 100000.
- Final strike 201411: Ascension's burst SpellVisual 111823 model
  (cfx_paladin_holyshock_healcrit_impactchest on ChestEffect) with spell_pa_executionsentence_impact
  (their 28666, which Ascension plays at cast instead). The splash 201412 plays the same burst
  without a sound, so up to 4 extra targets don't stack impact sounds.

Assets (gitignored working copies, extracted by hand via `smpq -x`, see
docs/ascension-asset-mining.md):
- var/model-visual-dbc/SPELLS/: Paladin_LightsHammer_Impact / _State and cfx_kyrian_paladin_castchest
  and Paladin_Veneration_Impact (.m2 + 00.skin, patch-N.MPQ), plus their non-stock textures (hammer_01, t_vfx_smokeanim02_blured,
  t_lightning_circle_d, shockwave1agrey, cfx_kyrian_demonhunter_3154184/5,
  cfx_kyrian_warrior_3154187/8/9, 7fx_smoketile_blue_1; GLOW_256 was already there).
  Paladin_ExecutionSentence_VerticleMissile (all its textures are stock) and
  cfx_paladin_holyshock_healcrit_impactchest with flare1_tc_holy2tone_pala2, fairydust_2x2_a2,
  fairydust2offsettwinkle_2x2_a and 7fx_alphamask_shockwavesoft1_noedge (white8x8 was already there).
- var/model-visual-dbc/EXTRA/world/expansion08/doodads/fx/: smoke_soft_01_3165011 and
  9fx_generic_anima_ardenweald_nova_raidlow_3525790 (patch-WC2.MPQ), hard-coded at that path.
- var/model-visual-dbc/SOUND/: spell_pa_lightshammer_impact01-05 and spell_pa_executionsentence_state /
  _impact (patch-O.MPQ), .ogg -> .wav.

SoundEntries rows ship client-only; SpellVisual is server-loaded, so `--sql-out PATH` emits its
overlay, same as the other VFX scripts.

Usage:
    python3 apps/dbc-tools/patch_paladin_vfx_models.py
    python3 apps/dbc-tools/patch_paladin_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
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

KIT_HAMMER_OF_WRATH_CAST_STOCK = 6409  # anim 107 + holy_hammer_missile in the right hand (stock SV 7250)
EFFECT_HOLY_NOVA_BASE_STOCK = 1722     # spells\holynova_impact_base.mdx (stock kit 3154)
EFFECT_HOLY_PRECAST_HIGH_HAND_STOCK = 131  # Spells\Holy_Precast_High_Hand.mdx (stock kit 3154)
ANIM_SPELL_CAST_OMNI_STOCK = 54        # stock kit 3154's AnimID
SOUND_HOLY_NOVA_CAST_STOCK = 2562      # stock kit 3154's SoundID
SOUND_LIGHTNING_BOLT_IMPACT_STOCK = 1506
SOUND_FLASH_HEAL_STOCK = 1434
KIT_HOLY_CAST_HIGH_STOCK = 191         # Holy_Precast_High hands, anim 54, sound 2562
NO_ATTACHMENT = -1                     # SpellVisual's signed "none" (dbcfmt.SPELLVISUAL.signed)

# --- SoundEntries.dbc (paladin range 90031-90040) ---

SOUND_LIGHTS_HAMMER_IMPACT = 90031
SOUND_EXECUTION_SENTENCE_STATE = 90032
SOUND_EXECUTION_SENTENCE_IMPACT = 90033


def build_sound_rows() -> list[dict]:
    return [
        _sound_row(
            SOUND_LIGHTS_HAMMER_IMPACT, "spell_pa_lightshammer_impact",
            [f"spell_pa_lightshammer_impact{i:02d}" for i in range(1, 6)],
            min_distance=20.0, cutoff=60.0,
        ),
        _sound_row(
            SOUND_EXECUTION_SENTENCE_STATE, "spell_pa_executionsentence_state",
            ["spell_pa_executionsentence_state"], min_distance=8.0, cutoff=45.0, flags=SOUND_FLAG_LOOPING,
        ),
        _sound_row(
            SOUND_EXECUTION_SENTENCE_IMPACT, "spell_pa_executionsentence_impact",
            ["spell_pa_executionsentence_impact"], min_distance=15.0, cutoff=45.0,
        ),
    ]


# --- SpellVisualEffectName.dbc (paladin range 90040-90059) ---

EFFECT_LIGHTS_HAMMER_IMPACT = 90040
EFFECT_LIGHTS_HAMMER_STATE = 90041
EFFECT_DIVINE_TOLL_BELL = 90042
EFFECT_LIGHTS_HAMMER_HEAL_TICK = 90043
EFFECT_EXECUTION_SENTENCE_HAMMER = 90044
EFFECT_EXECUTION_SENTENCE_BURST = 90045


def build_effect_name_rows() -> list[dict]:
    # Impact scale 2.0 is Ascension's own (effect name 112244); the state and bell have no area
    # placement precedent there, so they start at 1.0 (tune after playtest).
    return [
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_LIGHTS_HAMMER_IMPACT,
            Name="Light's Hammer Impact (Custom)", FileName=model_path("Paladin_LightsHammer_Impact"),
            AreaEffectSize=0.0, Scale=2.0, MinAllowedScale=0.01, MaxAllowedScale=100.0,
        ),
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_LIGHTS_HAMMER_STATE,
            Name="Light's Hammer State (Custom)", FileName=model_path("Paladin_LightsHammer_State"),
            AreaEffectSize=0.0, Scale=1.0, MinAllowedScale=0.01, MaxAllowedScale=100.0,
        ),
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_DIVINE_TOLL_BELL,
            Name="Divine Toll Bell (Custom)", FileName=model_path("cfx_kyrian_paladin_castchest"),
            AreaEffectSize=1.0, Scale=1.0, MinAllowedScale=0.01, MaxAllowedScale=100.0,
        ),
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_LIGHTS_HAMMER_HEAL_TICK,
            Name="Light's Hammer Heal Tick (Custom)", FileName=model_path("Paladin_Veneration_Impact"),
            AreaEffectSize=1.0, Scale=1.0, MinAllowedScale=0.01, MaxAllowedScale=100.0,
        ),
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_EXECUTION_SENTENCE_HAMMER,
            Name="Execution Sentence Hammer (Custom)", FileName=model_path("Paladin_ExecutionSentence_VerticleMissile"),
            AreaEffectSize=1.0, Scale=1.0, MinAllowedScale=0.01, MaxAllowedScale=100.0,
        ),
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_EXECUTION_SENTENCE_BURST,
            Name="Execution Sentence Burst (Custom)", FileName=model_path("cfx_paladin_holyshock_healcrit_impactchest"),
            AreaEffectSize=1.0, Scale=1.0, MinAllowedScale=0.01, MaxAllowedScale=100.0,
        ),
    ]


# --- SpellVisualKit.dbc (paladin range 90040-90059) ---

KIT_LIGHTS_HAMMER_IMPACT = 90040
KIT_LIGHTS_HAMMER_PERSISTENT = 90041
KIT_DIVINE_TOLL_CAST = 90042
KIT_LIGHTS_HAMMER_DAMAGE_TICK = 90043
KIT_LIGHTS_HAMMER_HEAL_TICK = 90044
KIT_EXECUTION_SENTENCE_STATE = 90045
KIT_EXECUTION_SENTENCE_BURST = 90046
KIT_EXECUTION_SENTENCE_SPLASH = 90047


def build_kit_rows() -> list[dict]:
    return [
        _kit_row(
            KIT_LIGHTS_HAMMER_IMPACT,
            AnimID=NOFIELD, BaseEffect=EFFECT_LIGHTS_HAMMER_IMPACT, SoundID=SOUND_LIGHTS_HAMMER_IMPACT,
        ),
        _kit_row(KIT_LIGHTS_HAMMER_PERSISTENT, AnimID=NOFIELD, BaseEffect=EFFECT_LIGHTS_HAMMER_STATE),
        # Stock Holy Nova cast kit 3154 plus the Kyrian bell on its free chest slot
        _kit_row(
            KIT_DIVINE_TOLL_CAST,
            AnimID=ANIM_SPELL_CAST_OMNI_STOCK, BaseEffect=EFFECT_HOLY_NOVA_BASE_STOCK,
            LeftHandEffect=EFFECT_HOLY_PRECAST_HIGH_HAND_STOCK, RightHandEffect=EFFECT_HOLY_PRECAST_HIGH_HAND_STOCK,
            ChestEffect=EFFECT_DIVINE_TOLL_BELL, SoundID=SOUND_HOLY_NOVA_CAST_STOCK,
        ),
        _kit_row(
            KIT_LIGHTS_HAMMER_DAMAGE_TICK,
            AnimID=NOFIELD, ChestEffect=EFFECT_LIGHTS_HAMMER_IMPACT, SoundID=SOUND_LIGHTNING_BOLT_IMPACT_STOCK,
        ),
        _kit_row(
            KIT_LIGHTS_HAMMER_HEAL_TICK,
            AnimID=NOFIELD, BaseEffect=EFFECT_LIGHTS_HAMMER_HEAL_TICK, SoundID=SOUND_FLASH_HEAL_STOCK,
        ),
        _kit_row(
            KIT_EXECUTION_SENTENCE_STATE,
            AnimID=NOFIELD, BaseEffect=EFFECT_EXECUTION_SENTENCE_HAMMER, SoundID=SOUND_EXECUTION_SENTENCE_STATE,
        ),
        _kit_row(
            KIT_EXECUTION_SENTENCE_BURST,
            AnimID=NOFIELD, ChestEffect=EFFECT_EXECUTION_SENTENCE_BURST, SoundID=SOUND_EXECUTION_SENTENCE_IMPACT,
        ),
        _kit_row(KIT_EXECUTION_SENTENCE_SPLASH, AnimID=NOFIELD, ChestEffect=EFFECT_EXECUTION_SENTENCE_BURST),
    ]


# --- SpellVisual.dbc (paladin range 90040-90059) ---

SV_LIGHTS_HAMMER = 90040  # spell 201200
SV_DIVINE_TOLL = 90041    # spell 201203
SV_LIGHTS_HAMMER_DAMAGE_TICK = 90042  # spell 201202
SV_LIGHTS_HAMMER_HEAL_TICK = 90043    # spell 201201
SV_EXECUTION_SENTENCE = 90044         # spell 201410
SV_EXECUTION_SENTENCE_BURST = 90045   # spell 201411
SV_EXECUTION_SENTENCE_SPLASH = 90046  # spell 201412


def build_spellvisual_rows() -> list[dict]:
    return [
        _row(
            dbcfmt.SPELLVISUAL, SV_LIGHTS_HAMMER,
            CastKit=KIT_HAMMER_OF_WRATH_CAST_STOCK, ImpactAreaKit=KIT_LIGHTS_HAMMER_IMPACT,
            PersistentAreaKit=KIT_LIGHTS_HAMMER_PERSISTENT,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_DIVINE_TOLL,
            CastKit=KIT_DIVINE_TOLL_CAST,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_LIGHTS_HAMMER_DAMAGE_TICK,
            ImpactKit=KIT_LIGHTS_HAMMER_DAMAGE_TICK,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_LIGHTS_HAMMER_HEAL_TICK,
            ImpactKit=KIT_LIGHTS_HAMMER_HEAL_TICK,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_EXECUTION_SENTENCE,
            CastKit=KIT_HOLY_CAST_HIGH_STOCK, StateKit=KIT_EXECUTION_SENTENCE_STATE,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_EXECUTION_SENTENCE_BURST,
            ImpactKit=KIT_EXECUTION_SENTENCE_BURST,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_EXECUTION_SENTENCE_SPLASH,
            ImpactKit=KIT_EXECUTION_SENTENCE_SPLASH,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
    ]


def build_pending_sql() -> str:
    """Server-side overlay for SpellVisual only - see the module docstring for SoundEntries."""
    return _table_block(
        dbcfmt.SPELLVISUAL, {"start": SV_LIGHTS_HAMMER, "end": SV_EXECUTION_SENTENCE_SPLASH}, build_spellvisual_rows(), []
    ) + "\n"


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
