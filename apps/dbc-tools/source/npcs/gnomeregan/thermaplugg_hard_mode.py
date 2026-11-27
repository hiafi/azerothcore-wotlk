"""
Gnomeregan build WP-D6Ha: the Whole Workshop, part a, Mekgineer Thermaplugg's heroic hard mode
(.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D6Ha, s3.6, s3.7, s3.8, s7 #1 A, #32 A, #35 A,
#38 i A, s10; build spec docs/dungeons/gnomeregan-rework.md SP 1738-1864 (MT15-MT20, MT25), rulings 43-53). WP-D6Ha
owns this file (its spells: kSpellsHardModeA 214540-214579 of modules/mod-dungeon-bosses
src/Gnomeregan/GnomereganRework.h only; the console's 214620-214639 stay unused; ThermapluggHardModeLogic.h names the
same ids and lib/test_gnomeregan_hard_mode.py diffs them). The engine side is src/Gnomeregan/thermaplugg_hard_mode.cpp
(the console, package SchematicsA through D6's ThermapluggFight.h, D1's Duplicator and D2's DoseField); the console's
gameobject_template, gossip and npc_text and the texts are data/sql/updates/pending_db_world/
rev_thermaplugg_hard_mode_gnomeregan.sql. Every hard mode value of SP 1799 (faces, Override, bomb health, blasts,
mines, Detonator, lockout) and the 800,000 health are D6's (thermaplugg.py, ThermapluggLogic.h). The hard mode's units
have no heroic templates (helpers: Thermaplugg deals every hit).

- 301135 Wandering Puddle: MT19, the nature disc (WP-V's MT_PUDDLE at disc_scale(4)) a leaking player drops; it forms
  in 1.5 s and drifts at 2 yd/s for 2 min, turning at the walls (npc_gnomer_wandering_puddle). Not selectable, not
  attackable. No heroic template (INT reconcile: a helper the boss's registry hits speak for; it runs on its normal
  entry on heroic).
- 301137 Workshop Alarm: the room alarm at the Clearance Console (npc_gnomer_workshop_stalker): the Reactor Leak's
  lines 0-4 and the console's "Loading schematic" lines 5-9. An invisible stalker. No heroic template.
- 301138 Workshop Vent: the green vapor at each open face once the Fallout schematic runs (MT17), and the Reactor
  Leak's room-wide disc. An invisible stalker (the script sets the disc). No heroic template.

Spells (214540-214548; 214549-214579 spare). Registry damage is a percent of the reference row through resolve copies
(IGNORE_CASTER_MODIFIERS, NO_REDIRECTION, NO_REFLECTION), all Nature (rule 2). The only kickable cast is the bombs'
Duplication (a reward; a stun stops it too); the dose, Meltdown and the Leak cannot be dispelled. Tooltips are
number-free.

  214540  Irradiated            MT18 the hard mode dose: +3% damage and healing done AND +3% damage taken a stack
                                (CumulativeAura 255, ruling 49), cast by him (D2's DoseField). Dispel none,
                                NO_IMMUNITIES, CHANGE_MAP. MT_DOSE (SV 1712)
  214541  Irradiated            MT18 the bright glow at 10 and up (Leaking): hidden, MT_DOSE_BRIGHT (SV 6594)
  214542  Duplication           MT16 a walking bomb's 2 s bar (Nature, kickable); leaves a 1 s aura of itself (done).
                                MT_DUPLICATE (SV 2073)
  214543  Venting               MT17 the vapor on a vent stalker: hidden, MT_VENT (SV 90559, shipped)
  214544  Wandering Puddle      MT19 resolve copy: 8% a second inside an armed puddle (+1 dose)
  214545  Meltdown              MT20 resolve copy: 5% a second (the carrier and everyone within 6 yd)
  214546  Meltdown              MT20 the carrier's debuff (the read)
  214547  Reactor Leak          MT25 resolve copy: 10% a second to his threat list from 180 s
  214548  Reactor Leak          MT25 the flooded room: a green ScreenEffect (MT_LEAK_SCREEN_EFFECT 282) on each player
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
)
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INVISIBLE_STALKER,
    MT_DOSE,
    MT_DOSE_BRIGHT,
    MT_DUPLICATE,
    MT_LEAK_SCREEN_EFFECT,
    MT_PUDDLE,
    MT_VENT,
    PUDDLE_DISC_SCALE,
)

_HM = 'Gnomeregan build WP-D6Ha (the Whole Workshop, part a)'

WANDERING_PUDDLE = 301135
ROOM_ALARM = 301137
VENT_STALKER = 301138

# ThermapluggHardModeLogic.h Tune (the DT test pins each against the header).
_DOSE_PCT = 3                       # kDosePctPerStack
_AURA_STACK_LIMIT = 255             # kAuraStackLimit
_DUP_CAST_MS = 2000                 # kDupCastMs
_DONE_MARK_MS = 1000                # the Duplication bar's own aura, read by D1's machine at the bar's end

_SCHOOL_MASK_ALL = 127
_AURA_SCREEN_EFFECT = 260           # SPELL_AURA_SCREEN_EFFECT (misc = a ScreenEffect.dbc id)
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_INTERRUPT_KICKABLE = 0x0F          # movement, pushback, interrupt, auto-attack (stock casters)
_PREVENTION_SILENCE = 1
_FLAGS_EXTRA_NO_XP = 0x40
_FLAGS_EXTRA_NO_XP_TRIGGER = _FLAGS_EXTRA_NO_XP | 0x80

# Stock icons (Spell.dbc).
_ICON_IRRADIATED = 203              # Irradiated 9775
_ICON_RADIATION = 160               # Radiation Poisoning 11638
_ICON_GLOWY = 1479                  # Glowy (Green) 22577
_ICON_DUPE = 91                     # Summon Dupe Bug 10858


def _hidden_look(spell_id: int, name: str, visual: int, icon: int, notes: str):
    """A hidden DUMMY aura that carries a StateKit look on its holder (Unit::AddAura by the script, no cast)."""
    return spell(
        id=spell_id, name=name, school=School.NATURE, dispel=0, mechanic=0,
        attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


# --- MT18 the dose ----------------------------------------------------------------------------------------------------

irradiated_214540 = spell(
    id=214540, name='Irradiated', school=School.NATURE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=_DOSE_PCT,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Irradiated: a flat percent of damage done a stack, not a damage value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=_DOSE_PCT,
                    die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Irradiated: a flat percent of healing done a stack, not a heal value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=_DOSE_PCT,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Irradiated: a flat percent of damage taken a stack, not a damage value')],
    spell_icon_id=_ICON_IRRADIATED,
    notes=f'{_HM}, MT18 (ruling 49): the hard mode dose on every player from the Fallout schematic (75%): +3% damage '
          'and healing done and +3% damage taken a stack, as one aura whose amounts multiply by the stacks, so a 70% '
          'blast is 89% at 9 dose and kills from full at 15. The DoseField machine (D2\'s ViscousFalloutMachine.cpp, '
          'the package as owner) keeps the count and mirrors it as the stack count, cast by him, on every change and '
          'every second (rule 25); the client counter shows at most 255. It never drains; venting +1 per open face '
          'every 8 s, a puddle +1 a second; a plate touch halves it (loses half, rounded up: D2\'s Halve). Leaking at '
          '10, Meltdown at 20. A debuff nobody can remove: Dispel none, NO_IMMUNITIES (rule 27), CHANGE_MAP; removed '
          'at the end of the pull. Fallout\'s look (MT_DOSE, SV 1712).',
    raw_overrides=kit_raw('Irradiated by the workshop. Damage and healing done increased, and damage taken.',
                          'Damage and healing done increased by $s1%. Damage taken increased by $s3%.',
                          CastingTimeIndex=1, CumulativeAura=_AURA_STACK_LIMIT, SpellVisualID_1=MT_DOSE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

dose_glow_214541 = _hidden_look(
    214541, 'Irradiated', MT_DOSE_BRIGHT, _ICON_GLOWY,
    f'{_HM}, MT18: the dose\'s bright glow at 10 and up (the Leaking read: a puddle every 10 s), added and removed by '
    'the script every second (Glowy (Green) 22577\'s SV 6594, MT_DOSE_BRIGHT).')

# --- MT16 Bomb Duplication --------------------------------------------------------------------------------------------

duplication_214542 = spell(
    id=214542, name='Duplication', school=School.NATURE, cast_time_ms=_DUP_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_DONE_MARK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_DUPE,
    notes=f'{_HM}, MT16 (the Techbot schematic, 90%): a walking bomb (301120-301123) alive 10 s casts it (D1\'s '
          'Duplicator, the package\'s spec: first at 10 s of life, again every 10 s, no cap; D6 holds its walk while '
          'it casts) and becomes two: the copy rises beside it at its current health (ruling 47) and D6 adopts it as '
          'a bomb of its type (AdoptBomb). Nature school, kickable (InterruptFlags 15, PreventionType silence): the '
          'bomb\'s only cast; a stun stops it too (the reward, the kick and dispel table). Completed, it leaves a 1 s '
          'DUMMY aura of itself on the bomb, which the machine reads as "done". Not The Big One, not the Sticky Bomb. '
          'Techbot\'s look (MT_DUPLICATE, SV 2073). Keeps the swing timer.',
    raw_overrides=kit_raw('Duplicates itself.', 'Duplicated.', InterruptFlags=_INTERRUPT_KICKABLE,
                          PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=MT_DUPLICATE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS),
)

# --- MT17 venting -----------------------------------------------------------------------------------------------------

vent_214543 = _hidden_look(
    214543, 'Venting', MT_VENT, _ICON_RADIATION,
    f'{_HM}, MT17 (the Fallout schematic, 75%): the green vapor at an open face, on a vent stalker (301138) at the '
    'alcove mouth while the face stays open; every 8 s each open face vents 1 dose into every player in the room. The '
    'Scarlet Monastery radiation fog (MT_VENT, SV 90559, shipped).')

# --- MT19 the Wandering Puddle, MT20 Meltdown -------------------------------------------------------------------------

puddle_214544 = resolve_copy(
    214544, 'Wandering Puddle', School.NATURE, 'Standing in a wandering puddle.',
    f'{_HM}, MT19 (ruling 48): every player inside any armed Wandering Puddle (4 yd, armed 1.5 s after it forms), '
    'once a second however many overlap (kit RegistryHit): 8% of the reference row, no Weakened (a lingering patch), '
    'the tank row on the tank; +1 dose. The puddles are the script\'s (a lasting telegraph-only zone rides each for '
    'the bots).',
    icon=_ICON_RADIATION,
)

meltdown_214545 = resolve_copy(
    214545, 'Meltdown', School.NATURE, 'Melting down.',
    f'{_HM}, MT20: a carrier at 20 dose and up takes 5% of the reference row a second (kit RegistryHit), and everyone '
    'else within 6 yd of each carrier takes 5% a tick from the lasting 6 yd registry Spread on the carrier. No '
    'Weakened; the tank row on the tank. Fallout\'s heroic Meltdown.',
    icon=_ICON_RADIATION,
)

meltdown_aura_214546 = spell(
    id=214546, name='Meltdown', school=School.NATURE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_RADIATION,
    notes=f'{_HM}, MT20: the read on a carrier at 20 dose and up: added by the script with the 6 yd Spread and removed '
          'when the dose falls below 20 (a plate), at death and at the end of the pull. Dispel none, NO_IMMUNITIES, '
          'CHANGE_MAP. No look of its own (the ring and the bright glow carry it).',
    raw_overrides=kit_raw('Melting down.', 'Melting down: you and everyone within 6 yd take damage every second. '
                          'Shed your dose at a plate.', CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- MT25 the Reactor Leak --------------------------------------------------------------------------------------------

reactor_leak_214547 = resolve_copy(
    214547, 'Reactor Leak', School.NATURE, 'The reactor floods the workshop.',
    f'{_HM}, MT25 (rulings 46, 50): from 180 s after the pull, every player on his threat list wherever they stand (s7 '
    '#35 A) takes 10% of the reference row a second until the fight ends (kit RegistryHit), no ramp, no safe spot; the '
    'dose\'s damage taken multiplies it. No Weakened; the tank row on the tank.',
    icon=_ICON_RADIATION,
)

leak_aura_214548 = spell(
    id=214548, name='Reactor Leak', school=School.NATURE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_SCREEN_EFFECT, misc_value=MT_LEAK_SCREEN_EFFECT,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_RADIATION,
    notes=f'{_HM}, MT25: the flooded room on each player the Leak reaches (the green ScreenEffect 282 "Icecrown - '
          'Emerald Nightmare", MT_LEAK_SCREEN_EFFECT, through aura 260), added at its first tick, removed at the end '
          'of the pull. Dispel none, NO_IMMUNITIES, CHANGE_MAP.',
    raw_overrides=kit_raw('The reactor is leaking.', 'The reactor is leaking: damage every second until the '
                          'Mekgineer falls.', CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- the creatures ----------------------------------------------------------------------------------------------------

wandering_puddle_301135 = creature_template(
    WANDERING_PUDDLE, 'Wandering Puddle', **{
        **KIT_HELPER, 'minlevel': 28, 'maxlevel': 28, 'rank': 0, 'unit_class': 1,
        # no XP; not a trigger (0x80), as D6Ha built it (the puddle is a visible disc)
        'flags_extra': _FLAGS_EXTRA_NO_XP,
        'ScriptName': 'npc_gnomer_wandering_puddle'},
)
creature_model(WANDERING_PUDDLE, display_id=MT_PUDDLE, scale=PUDDLE_DISC_SCALE)


def _stalker(entry: int, name: str):
    creature_template(
        entry, name, **{**KIT_HELPER, 'minlevel': 28, 'maxlevel': 28, 'rank': 0, 'unit_class': 1,
                        'flags_extra': _FLAGS_EXTRA_NO_XP_TRIGGER, 'ScriptName': 'npc_gnomer_workshop_stalker'},
    )
    creature_model(entry, display_id=DISPLAY_INVISIBLE_STALKER)


_stalker(ROOM_ALARM, 'Workshop Alarm')
_stalker(VENT_STALKER, 'Workshop Vent')

