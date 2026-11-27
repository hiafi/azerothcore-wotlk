"""
Gnomeregan build WP-D6Hb: the Whole Workshop, part b (Mekgineer Thermaplugg's heroic hard mode: the Electrocutioner,
Alert System and Pummeler schematics) (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D6Hb and
its kick and dispel table, s3.7, s3.8, s3.9 row 10, s7 #33 A, #35 A; build spec docs/dungeons/gnomeregan-rework.md
"Hard mode: the Whole Workshop", MT15, MT21-MT24, rulings 43-53, 68, 69). WP-D6Hb owns this file (its spells:
kSpellsHardModeB 214580-214619 of modules/mod-dungeon-bosses src/Gnomeregan/GnomereganRework.h only;
ThermapluggHardModeMachinesLogic.h names the same ids and holds every number; the C++ is
thermaplugg_hard_mode_machines.cpp; the texts, 7800 groups 10 and 11, are the core SQL rev
rev_thermaplugg_hard_mode_machines_gnomeregan.sql).

The machines are D3's, D4's and D5's (GnomereganMachines.h): they bring their own looks and hits (Electrocutioner's
Electric Justice hit 214383, his brighter crackle 214381 and the blast look 214384 on blast stalkers 301132; the light
stalker 301113 under the BM cones). This file adds what the hard mode needs on Thermaplugg:

  214580  Voltage              MT21 the meter on him: stacks the script sets (one per 1,000 volts), +3% damage done a
                               stack (his melee and Knock Away; every registry hit ignores caster modifiers and takes
                               the script's factor instead), SV 37 (V's EL_VOLTAGE)
  214581  Electric Justice     MT22 the 4 s bar (Physical, InterruptFlags 0: his kickable Detonator locks Fire only)
  214582  Spotted              MT23 the Spotted hit: resolve copy, Arcane, 50% (times his Voltage), no Weakened
  214583  Spotted              MT23 the red beam from him to the Spotted player (V's MA_SPOTTED 7851), a look
  214584  Pummeler's Fist      MT24 every punch: resolve copy, Physical, 60% (times his Voltage), Weakened
  214585  Wind Up              MT24 the fist's 4 s wind-up (V's punch pose CP_PUNCH_POSE), no effect
  214586  Gnome Face           MT24 the face lights up: a glow on its face stalker 301125 (V gap 12: SV 6594)
  214587-214619 spare.

- 301136 Pummeler's Fist: the Pummeler's display (V's MT_FIST_DISPLAY = 6774, no hands-only model) at his fight's
  scale 5, summoned behind a Gnome Face for one combination (npc_gnomer_pummelers_fist: passive, rooted, gravity
  off), not attackable, not selectable. No heroic template (INT reconcile: a helper; the boss deals its strikes),
  so it runs on its normal entry on heroic. The numerals are D4's light stalker 301113
  wearing V's numeral quads (CDI 90853-90855) by SetDisplayId: no template of their own.

Nothing here is kickable or dispellable (the kick and dispel table: the hard mode's bars must land; Voltage is not
purgeable).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR0_DO_NOT_DISPLAY, ATTR1_NO_THREAT, ATTR2_IGNORE_LINE_OF_SIGHT
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TYPE_MECHANICAL,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    CP_PUMMEL,
    CP_PUNCH_POSE,
    EL_JUSTICE_CAST,
    EL_VOLTAGE,
    MA_SPOTTED,
    MT_FIST_DISPLAY,
    MT_FIST_FACE_GLOW,
    PUMMELER_SCALE,
)

_D6HB = 'Gnomeregan build WP-D6Hb (the Whole Workshop, part b)'

# --- constants (ThermapluggHardModeMachinesLogic.h; lib/test_gnomeregan_hard_mode_machines.py pins each) ------------

FIST = 301136                       # GnomereganRework.h NPC_PUMMELERS_FIST
FIST_SCALE = PUMMELER_SCALE         # SP: "a copy of Crowd Pummeler's model at his fight's scale" (5)
JUSTICE_CAST_MS = 4000              # Tune::kJusticeCastMs
FIST_WIND_UP_MS = 4000              # Tune::kFistWarnMs (ruling 69)
FACE_LIGHT_MS = 10000               # Tune::kFaceLightMs
STACK_LIMIT = 255                   # the client's counter (D3's kVoltageStackLimit)
VOLTAGE_PCT_PER_STACK = 3           # Tune::kVoltagePctPerStack
FACE_LIGHT_VISUAL = MT_FIST_FACE_GLOW   # V gap 12's pick for a lit face (SV 6594 flares)

_SCHOOL_ALL = 127
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_FLAGS_EXTRA_NO_XP = 0x40

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_SUPERCHARGE = 320             # Supercharge 10732 (D3's Voltage icon)
_ICON_POWER_SURGE = 75              # Power Surge 28134 (D3's Electric Justice icon)
_ICON_RED_BEAM = 816                # Red Beam 31513 (D4's Spotted icon)
_ICON_CROWD_PUMMEL = 756            # Crowd Pummel 10887
_ICON_ARCING_SMASH = 277            # Arcing Smash 8374

# --- MT21 Voltage ----------------------------------------------------------------------------------------------------

voltage_214580 = spell(
    id=214580, name='Voltage', school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
                    base_points=VOLTAGE_PCT_PER_STACK - 1, misc_value=_SCHOOL_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='boss hard mode: +3% damage done a stack, the script sets the stacks')],
    spell_icon_id=_ICON_SUPERCHARGE,
    notes=f'{_D6HB}, MT21 (the Electrocutioner schematic, from 60%): the meter on Thermaplugg, one stack per 1,000 '
          'volts, set by D3\'s VoltageMeter machine (+1 every 5 s, +1 for every player a mine or a bomb hits; never '
          'resets; reasserted every second). +3% damage done a stack (the stack count multiplies the effect): his '
          'melee and Knock Away. His registry hits ignore caster modifiers (rule 2) and take the script\'s factor '
          '(1 + 3% a stack) instead: D6\'s percent hits, Electric Justice, Spotted, the fist. Lightning Shield\'s orb '
          'state SV 37 (V\'s EL_VOLTAGE; the brighter crackle from 3 stacks is D3\'s 214381). Not purgeable or '
          'stealable (Dispel 0, NO_IMMUNITIES); gone on his reset, evade or death.',
    raw_overrides=kit_raw('1,000 volts a charge. At 6,000, Electric Justice.',
                          'Charged with $s1% more damage. At 6,000 volts, Electric Justice.', instant=True,
                          CumulativeAura=STACK_LIMIT, SpellVisualID_1=EL_VOLTAGE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- MT22 Electric Justice -------------------------------------------------------------------------------------------

justice_bar_214581 = spell(
    id=214581, name='Electric Justice', school=School.NORMAL, cast_time_ms=JUSTICE_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_POWER_SURGE,
    notes=f'{_D6HB}, MT22: Thermaplugg\'s 4 s bar at every 6,000 volts (emote line 10, "%s overloads the room. Get to '
          'him!"). Physical and not interruptible (InterruptFlags 0, PreventionType 0): his one kickable cast, the '
          'Remote Detonator, locks Fire only (the kick and dispel table\'s hard mode row). The VoltageMeter machine '
          'registers the hit beside it: the room outside 8 yd of him, 75% of the reference row times his Voltage, no '
          'Weakened (D3\'s resolve copy 214383, "Electric Justice"). Power Surge 28134\'s SV 7569 (V\'s '
          'EL_JUSTICE_CAST). Keeps his swing timer.',
    raw_overrides=kit_raw('The machine overloads the room.', InterruptFlags=0, PreventionType=0,
                          SpellVisualID_1=EL_JUSTICE_CAST, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- MT23 Searchlights -----------------------------------------------------------------------------------------------

spotted_214582 = resolve_copy(
    214582, 'Spotted', School.ARCANE, 'The searchlight has found you. A bomb chute opens.',
    f'{_D6HB}, MT23 (the Alert System schematic, from 45%): a player one of the two lights turning from Thermaplugg '
    'caught, at most once per 3 s per player (D4\'s latch): 50% of the reference row times his Voltage, the tank row '
    'on the tank, no Weakened (Penalty: none); a random closed Gnome Face opens. Registry tag 82 (G1 row 10). Copy of '
    'the resolve spell 205001 (Arcane).',
    icon=_ICON_RED_BEAM,
)

spotted_beam_214583 = spell(
    id=214583, name='Spotted', school=School.ARCANE, attributes=ATTR0_DO_NOT_DISPLAY, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_RED_BEAM,
    notes=f'{_D6HB}, MT23: the red beam from Thermaplugg to a Spotted player (Red Beam 31513\'s SV 7851, V\'s '
          'MA_SPOTTED, as the Alert System\'s), cast by him (triggered) as the hit lands. Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=MA_SPOTTED, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- MT24 Fist Combination -------------------------------------------------------------------------------------------

fist_hit_214584 = resolve_copy(
    214584, "Pummeler's Fist", School.NORMAL, 'A giant fist punches out of a Gnome Face.',
    f'{_D6HB}, MT24 (the Pummeler schematic, from 30%): every punch of the fist (rulings 68, 69; section 7 #33 A): '
    'the half of the room left or right of the line from the face through the center, near (within 50 yd of the '
    'face) or far (past it); three of the four per combination, 2.5 s apart, every 18 s. 60% of the reference row '
    '(guess, Pummeler\'s heroic) times his Voltage, the tank row on the tank, Weakened. Registry tag 84 (G1 row 10). '
    'Copy of the resolve spell 205001 (Physical, as Crowd Pummeler\'s punches: armor cuts it). Crowd Pummel\'s hit '
    'flash (V\'s CP_PUMMEL 1023).',
    icon=_ICON_CROWD_PUMMEL, visual=CP_PUMMEL,
)

fist_wind_up_214585 = spell(
    id=214585, name='Wind Up', school=School.NORMAL, cast_time_ms=FIST_WIND_UP_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_ARCING_SMASH,
    notes=f'{_D6HB}, MT24: the Pummeler\'s Fist 301136 winds up behind its Gnome Face for the 4 s before the first '
          'punch (ruling 69), cast on itself (not triggered, so the bar runs). No effect: the registry lands the '
          'punches. SV 90752 (V\'s CP_PUNCH_POSE: the AttackUnarmed precast, GnomeBot\'s one punch); the script also '
          'plays the AttackUnarmed emote at every strike, so the pose shows without the patch. Not interruptible.',
    raw_overrides=kit_raw('Winds up a giant punch.', InterruptFlags=0, PreventionType=0,
                          SpellVisualID_1=CP_PUNCH_POSE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS, AttributesEx4=ATTR4_NO_CAST_LOG),
)

face_light_214586 = spell(
    id=214586, name='Gnome Face', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=FACE_LIGHT_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_ARCING_SMASH,
    notes=f'{_D6HB}, MT24: the Gnome Face the fist comes out of lights up (ruling 69) for the wind-up and the three '
          'punches: cast by D6\'s face stalker 301125 at the alcove mouth on itself (triggered), removed by the '
          'script when the combination ends. A shut face cannot be tinted (a game object), so the glow sits on the '
          'stalker in front of it (V gap 12: SV 6594\'s flares; the shipped green fog 90559 / 90560 is the vents\' '
          'look). Hidden, no effect.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=FACE_LIGHT_VISUAL, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- 301136 Pummeler's Fist ------------------------------------------------------------------------------------------

pummelers_fist_301136 = creature_template(FIST, "Pummeler's Fist", **{
    **KIT_HELPER, 'minlevel': 28, 'maxlevel': 28, 'rank': 0, 'unit_class': 1, 'type': TYPE_MECHANICAL,
    'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': 'npc_gnomer_pummelers_fist',
})
creature_model(FIST, display_id=MT_FIST_DISPLAY, scale=FIST_SCALE)
