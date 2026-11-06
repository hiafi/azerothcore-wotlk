"""
Deadmines Pilot (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.2, s3.3): the shared spells of the
reworked Deadmines (modules/mod-dungeon-bosses, DeadminesRework.h `DeadminesSharedSpells`). Owned by WP-K; ids
205200-205209 (205203-205209 spare). Every boss's own spells live in its own file of this package, inside its slice.

  205200  Preparing       the generic cast bar: a 2 s no-effect cast (DUMMY on the caster) the boss shows while a
                          registry mechanic it registered owns the hit (DeadminesKit::CastBar). Not interruptible
                          (InterruptFlags 0, PreventionType 0): a kick must not look as if it stopped a mechanic the
                          registry still lands. A boss whose bar should name its mechanic declares its own copy of
                          this shape in its slice (the acceptance asks that cast bars name the mechanic).
  205201  Standing in It  the slow rider of every lingering zone (rubble, puddles, fire, molten trails; DeadminesKit::
                          ImpactThenLinger / Linger): movement -30% for 2 s, re-applied by every tick that hits, so it
                          ends shortly after the player steps out. Aura text "Standing in it hurts." (DM "Aura texts",
                          approved 2026-10-28). Snare mechanic; Dispel none.
  205202  Burn It Down    VanCleef's hard mode timer (B9): a 3:00 DUMMY aura that shows the clock. B9 decides who
                          carries it and may retune the text; NO_IMMUNITIES so it lands through Divine Shield.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TEXT_MASKS,
)

_MECHANIC_SNARE = 11
_ICON_GENERIC = 1
_ICON_SLOW = 27         # stock Slow 246
_ICON_FIRE = 37         # stock Flamestrike 2120


def _raw(desc: str, aura_desc: str = '', **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'Description_Lang_enUS': desc,
            'AuraDescription_Lang_enUS': aura_desc, **TEXT_MASKS, **more}


cast_bar_205200 = spell(
    id=205200, name='Preparing', school=School.NORMAL, cast_time_ms=2000, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GENERIC,
    notes='Deadmines Pilot WP-K: the generic 2 s cast bar a boss shows while its registry mechanic owns the hit. '
          'DUMMY on the caster, no effect; not interruptible (InterruptFlags 0, PreventionType 0).',
    raw_overrides=_raw('Preparing an attack.', InterruptFlags=0, PreventionType=0, AttributesEx4=ATTR4_NO_CAST_LOG),
)

standing_in_it_205201 = spell(
    id=205201, name='Standing in It', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_SNARE,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=2000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-31,
                    mechanic=_MECHANIC_SNARE, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SLOW,
    notes='Deadmines Pilot WP-K: the lingering-zone slow rider. Movement speed -30% (BasePoints -31 + DieSides 1), '
          '2 s, refreshed by every tick that hits; AURA_IS_DEBUFF, snare mechanic, Dispel none. '
          'TARGET_UNIT_TARGET_ANY: the registry casts riders with the owner as original caster. Stock Slow icon 27.',
    raw_overrides=_raw('Standing in it hurts. Lasts $d.', 'Standing in it hurts.', CastingTimeIndex=1),
)

hard_mode_timer_205202 = spell(
    id=205202, name='Burn It Down', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=180000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FIRE,
    notes='Deadmines Pilot WP-K (for B9): the hard mode clock, a 3:00 DUMMY aura; AURA_IS_DEBUFF + NO_IMMUNITIES, '
          'Dispel none. Stock Flamestrike icon 37.',
    raw_overrides=_raw('The ship explodes when this runs out. Lasts $d.', 'The ship explodes when this runs out.',
                       CastingTimeIndex=1),
)
