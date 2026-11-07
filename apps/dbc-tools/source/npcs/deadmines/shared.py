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

from lib.dsl import School
from lib.dsl.dungeon_kit import cast_bar, standing_in_it, timer_aura

_ICON_FIRE = 37         # stock Flamestrike 2120

# 205200 and 205201 are the shared dungeon kit's (mod-dungeon-bosses DungeonKitIds.h: SPELL_KIT_CAST_BAR,
# SPELL_KIT_STANDING_IN_IT): every reworked dungeon uses them by id. They stay declared here, in the Deadmines block
# that minted them, with the kit's builders (lib/dsl/dungeon_kit.py).

cast_bar_205200 = cast_bar(
    205200, 'Preparing', 2000, 'Preparing an attack.',
    'Deadmines Pilot WP-K: the generic 2 s cast bar a boss shows while its registry mechanic owns the hit. '
    'DUMMY on the caster, no effect; not interruptible (InterruptFlags 0, PreventionType 0).',
)

standing_in_it_205201 = standing_in_it(
    205201,
    'Deadmines Pilot WP-K: the lingering-zone slow rider. Movement speed -30% (BasePoints -31 + DieSides 1), '
    '2 s, refreshed by every tick that hits; AURA_IS_DEBUFF, snare mechanic, Dispel none. '
    'TARGET_UNIT_TARGET_ANY: the registry casts riders with the owner as original caster. Stock Slow icon 27.',
)

hard_mode_timer_205202 = timer_aura(
    205202, 'Burn It Down', 180000, 'The ship explodes when this runs out. Lasts $d.',
    'The ship explodes when this runs out.',
    'Deadmines Pilot WP-K (for B9): the hard mode clock, a 3:00 DUMMY aura; AURA_IS_DEBUFF + NO_IMMUNITIES, '
    'Dispel none. Stock Flamestrike icon 37.',
    icon=_ICON_FIRE, school=School.FIRE,
)
