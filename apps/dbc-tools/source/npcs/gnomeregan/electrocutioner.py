"""
Gnomeregan build WP-D3: Electrocutioner 6000 (6235) (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5
row D3 and its kick and dispel table, s3.6, s3.8, s3.9 row 5, s7 #9 A, #12 A, #20 A; build spec
docs/dungeons/gnomeregan-rework.md "Electrocutioner 6000", EL1-EL6, rulings 21-24). WP-D3 owns this file (its spells:
kSpellsElectrocutioner 214380-214419 of modules/mod-dungeon-bosses src/Gnomeregan/GnomereganRework.h only;
ElectrocutionerLogic.h names the same ids and holds every number; his texts are the core SQL rev
rev_electrocutioner_gnomeregan.sql).

- 6235 Electrocutioner 6000: boss_electrocutioner_rework (SmartAI off: rev_skeleton_gnomeregan.sql drops his rows,
  Chain Bolt 11085, Megavolt 11082, Shock 11084 and the aggro yell; S0's rev set his wander to 0), the normal health of
  s3.6 (68,002 = HealthModifier 79.72 on the level 28 warrior base 853, s7 #1 A), the stock DamageModifier 1.7, stun
  immunity 1972 (no interrupt or silence immunity: Chain Bolt can be kicked), INSTANCE_BIND with both assist flags,
  detection range 12. Heroic 400,000 is WP-H's override (source/world/dungeons/gnomeregan.py). His loot (the Workshop
  Key 6893 at 100%, ruling 58) is untouched.
- 301132 Blast Stalker: a passive helper (KIT_HELPER, the invisible stalker skin) the VoltageMeter machine and the
  discharge summon for 3 s to play SV 3 where it lands (V: EL_JUSTICE_BLAST, EL_DISCHARGE "on a stalker"). No
  script, no heroic template (stalkers get none).

Spells. Registry hits are dungeon copies of the mod-boss-mechanics resolve spell (the registry sets each target's
number: a percent of the reference row, the tank row on a tank, times his Voltage multiplier on heroic); every damage
spell ignores the caster's modifiers (rule 2). The kick table (s7 #9 A): Chain Bolt is his one kickable cast (Nature,
the reward on normal, expected on heroic); Megavolt and Electric Justice are Physical bars with InterruptFlags 0, so a
kick's Nature lockout never swallows them (it does swallow a Shock: the reward). Static and Voltage cannot be
dispelled, purged or stripped by a bubble (rule 27).

  214380  Voltage              EL1 the meter on him (stacks, SV 37), the script sets the count
  214381  Voltage              EL1 the brighter crackle from 3 stacks (hidden, SV 7867)
  214382  Electric Justice     EL2 the 4 s bar (Physical, not interruptible, Power Surge's SV 7569)
  214383  Electric Justice     EL2 the donut / circle hit: resolve copy, Nature
  214384  Electric Justice     EL2 the blast look on a blast stalker (SV 3)
  214385  Megavolt             EL3 the 2 s bar (Physical, not interruptible, SV 944)
  214386  Megavolt             EL3 the cone hit: resolve copy, Nature
  214387  Chain Bolt           EL4 the 2.5 s cast at a player (Nature, kickable, SV 36)
  214388  Chain Bolt           EL4 each struck player: resolve copy, Nature
  214389  Shock                EL5 the instant at a player (Nature, a kick's lockout refuses it, SV 97)
  214390  Shock                EL5 the hit: resolve copy, Nature
  214391  Static               EL6 heroic: the stacks on a player (SV 7867), the script sets the count
  214392  Electric Discharge   EL6 the discharge hit: resolve copy, Nature
  214393  Electric Discharge   EL6 the discharge look on a blast stalker (SV 3)
  214394-214419 spare.

Looks (V, s3.10): SV 2048 (Supercharge), 4229 (Electric Discharge) and 7678 (Overload) are never wired; the spec's
named spells are copied only for their icons.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TYPE_MECHANICAL,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INVISIBLE_STALKER,
    EL_CHAIN,
    EL_DISCHARGE,
    EL_JUSTICE_BLAST,
    EL_JUSTICE_CAST,
    EL_MEGAVOLT,
    EL_SHOCK,
    EL_STATIC,
    EL_VOLTAGE,
    EL_VOLTAGE_2,
)

_D3 = 'Gnomeregan build WP-D3 (Electrocutioner 6000)'

# --- constants (ElectrocutionerLogic.h; lib/test_gnomeregan_electrocutioner.py pins each against the header) ---------

ELECTROCUTIONER = 6235
BLAST_STALKER = 301132              # GnomereganRework.h NPC_BLAST_STALKER
HEALTH_MODIFIER = 79.72             # GnomereganRework.h HealthModifier::kElectrocutioner
JUSTICE_CAST_MS = 4000              # Tune::kJusticeCastMs
MEGAVOLT_CAST_MS = 2000             # Tune::kMegavoltCastMs
CHAIN_CAST_MS = 2500                # Tune::kChainCastMs
STACK_LIMIT = 255                   # Tune::kVoltageStackLimit (the client's counter)
STATIC_MS = 5000                    # the Static aura's life, refreshed by the script while it shows

_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15                  # the whitemane.py / jergosh.py / theka.py recipe
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000  # SharedDefines.h: the cast leaves his swing timer alone
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000         # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP

# Stock icons (Spell.dbc SpellIconID of the named spell, read from the stock DBC 2026-11-26)
_ICON_CHAIN_BOLT = 165              # Chain Bolt 11085, Megavolt 11082
_ICON_SHOCK = 117                   # Shock 11084
_ICON_SUPERCHARGE = 320             # Supercharge 10732, Electric Discharge 29151
_ICON_STATIC_CHARGE = 122           # Static Charge 31715, Overload 29768
_ICON_POWER_SURGE = 75              # Power Surge 28134

_RAW_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
    AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT | _ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
    AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
    AttributesEx4=ATTR4_NO_CAST_LOG,
)

# --- the creatures ---------------------------------------------------------------------------------------------------

creature_template_columns(ELECTROCUTIONER, **boss_columns(
    'boss_electrocutioner_rework', HEALTH_MODIFIER, damage_modifier=1.7,
))

blast_stalker_301132 = creature_template(
    BLAST_STALKER, 'Blast Stalker', **{**KIT_HELPER, 'minlevel': 28, 'maxlevel': 28, 'rank': 0, 'unit_class': 1,
                                       'type': TYPE_MECHANICAL},
)
creature_model(BLAST_STALKER, display_id=DISPLAY_INVISIBLE_STALKER)


# --- helpers ---------------------------------------------------------------------------------------------------------

def _bar(*, spell_id: int, name: str, cast_ms: int, visual: int, icon: int, desc: str, notes: str):
    """A Physical bar the players read (DUMMY on the caster, no handler) that a kick can never stop: InterruptFlags 0,
    PreventionType 0 (s7 #9 A). The registry zone registered beside it owns the hit. It leaves his swing timer
    alone."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=cast_ms, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, InterruptFlags=0, PreventionType=0, SpellVisualID_1=visual,
                              AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _at_player(*, spell_id: int, name: str, cast_ms: int, visual: int, icon: int, desc: str, notes: str,
               kickable: bool):
    """A Nature cast at a player (DUMMY on the target, no handler): the bolt's look on its way. The script deals the
    hit through the registry when it lands. Not triggered, so a kick's Nature lockout refuses it; `kickable` adds the
    interrupt flags and the silence (Chain Bolt)."""
    raw = kit_raw(desc, DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=visual, **_RAW_HIT_ATTRS)
    raw['PreventionType'] = _PREVENTION_SILENCE
    raw['InterruptFlags'] = _INTERRUPT_FLAGS_KICKABLE if kickable else 0
    if not cast_ms:
        raw['CastingTimeIndex'] = 1
    return spell(
        id=spell_id, name=name, school=School.NATURE, cast_time_ms=cast_ms, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _stacks(*, spell_id: int, name: str, visual: int, icon: int, target: int, debuff: bool, duration_ms: int,
            desc: str, aura_desc: str, notes: str, hidden: bool = False):
    """A DUMMY aura whose stack count the script sets (CumulativeAura 255, the client's counter), not dispellable or
    purgeable (Dispel 0) and NO_IMMUNITIES (a bubble or Ice Block does not strip it, rule 27); dropped on a map
    change."""
    attributes = ATTR0_NO_IMMUNITIES | (ATTR0_AURA_IS_DEBUFF if debuff else 0) | (ATTR0_DO_NOT_DISPLAY if hidden else 0)
    return spell(
        id=spell_id, name=name, school=School.NATURE, dispel=0, mechanic=0, attributes=attributes, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=(RANGE_SELF if target == TARGET_UNIT_CASTER else 100.0), duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=target)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, CumulativeAura=STACK_LIMIT, SpellVisualID_1=visual,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


# --- EL1 Voltage -----------------------------------------------------------------------------------------------------

voltage_214380 = _stacks(
    spell_id=214380, name='Voltage', visual=EL_VOLTAGE, icon=_ICON_SUPERCHARGE, target=TARGET_UNIT_CASTER,
    debuff=False, duration_ms=-1,
    desc='The machine counts up to the sentence: 1,000 volts a charge.',
    aura_desc='1,000 volts a charge. At 6,000, Electric Justice.',
    notes=f'{_D3}, EL1: the meter on him, one stack per 1,000 volts, set by the VoltageMeter machine (+1 every 5 s, '
          'per Megavolt hit, per Chain Bolt jump, heroic per Static discharge; normal back to 0 after each Justice; '
          'reasserted every second). No effect of its own: the heroic +3% a stack is the script\'s multiplier. '
          'Lightning Shield\'s orb state SV 37 (V tier 1; Supercharge 10732\'s SV 2048 is never wired). Not '
          'purgeable; gone on his reset, evade or death.',
)

voltage_charged_214381 = _stacks(
    spell_id=214381, name='Voltage', visual=EL_VOLTAGE_2, icon=_ICON_SUPERCHARGE, target=TARGET_UNIT_CASTER,
    debuff=False, duration_ms=-1, hidden=True, desc='', aura_desc='',
    notes=f'{_D3}, EL1: the brighter crackle while the meter holds 3 stacks or more (V tier 2: Static Charge 31715\'s '
          'SV 7867), added and removed by the machine. Hidden, no effect.',
)

# --- EL2 Electric Justice --------------------------------------------------------------------------------------------

justice_bar_214382 = _bar(
    spell_id=214382, name='Electric Justice', cast_ms=JUSTICE_CAST_MS, visual=EL_JUSTICE_CAST,
    icon=_ICON_POWER_SURGE, desc='The machine reaches 6,000 volts and carries out the sentence.',
    notes=f'{_D3}, EL2: the 4 s bar of the execution (the yell "Electric justice!", stock text group 0, and the '
          'emote). Physical and not interruptible (s7 #9 A): his kickable Chain Bolt locks Nature only. Power Surge '
          '28134\'s SV 7569 (lightning hands and a blue-white tint). The registry zone beside it is the hit.',
)

justice_hit_214383 = resolve_copy(
    214383, 'Electric Justice', School.NATURE, 'Lightning fills the platform.',
    f'{_D3}, EL2: the execution, 4 s after the bar starts: the donut outside 8 yd of him to the platform\'s far edge '
    '(heroic in turn with a 15 yd circle on him, donut first): 75% of the reference row, the tank row on the tank, no '
    'Weakened; heroic times his Voltage (+3% a stack). Registry tags 40 / 41. Copy of the resolve spell 205001 '
    '(Nature).',
    icon=_ICON_POWER_SURGE,
)

justice_blast_214384 = self_visual(
    214384, 'Electric Justice', EL_JUSTICE_BLAST,
    f'{_D3}, EL2: the blast as the execution lands, cast by each Blast Stalker 301132 on itself (triggered): six on a '
    'ring 14 yd out through the donut, one on him for the heroic circle. SV 3 (the thunderclap ring and the called '
    'lightning; Overload 29768\'s SV 7678 is never wired). Look only.',
    icon=_ICON_STATIC_CHARGE, school=School.NATURE,
)

# --- EL3 Megavolt ----------------------------------------------------------------------------------------------------

megavolt_bar_214385 = _bar(
    spell_id=214385, name='Megavolt', cast_ms=MEGAVOLT_CAST_MS, visual=EL_MEGAVOLT, icon=_ICON_CHAIN_BOLT,
    desc='The machine turns and charges a cone of lightning.',
    notes=f'{_D3}, EL3: the 2 s bar of the cone (every 12 s, first at 10 s): he turns to a random player on the '
          'platform, tank included (heroic two cones at two players). Physical and not interruptible (s7 #9 A: the '
          'stock Megavolt\'s InterruptFlags 9 are dropped; it is the dodge). Megavolt 11082\'s SV 944. The registry '
          'cones beside it are the hit.',
)

megavolt_hit_214386 = resolve_copy(
    214386, 'Megavolt', School.NATURE, 'A cone of lightning.',
    f'{_D3}, EL3: the 40 degree, 30 yd cone fixed at the bar\'s start: 40% (heroic 60%, times his Voltage) of the '
    'reference row and Weakened, the tank row on the tank; +1 V (heroic +2) per player hit. Registry tag 42. Copy of '
    'the resolve spell 205001 (Nature).',
    icon=_ICON_CHAIN_BOLT,
)

# --- EL4 Chain Bolt --------------------------------------------------------------------------------------------------

chain_bolt_214387 = _at_player(
    spell_id=214387, name='Chain Bolt', cast_ms=CHAIN_CAST_MS, visual=EL_CHAIN, icon=_ICON_CHAIN_BOLT,
    kickable=True, desc='A bolt of lightning that leaps to nearby enemies.',
    notes=f'{_D3}, EL4: first at 3 s, then every 20 s, a 2.5 s cast at a random player on the platform, tank '
          'included. His one kickable cast (InterruptFlags 15, silence; Nature: a kick locks Nature, so it also '
          'refuses his next Shock, never a bar): the reward on normal, expected on heroic (the descriptor\'s '
          'interrupt). When it lands the script strikes the target and jumps (214388). Chain Bolt 11085\'s SV 36. '
          'Ignores line of sight; leaves his swing timer alone.',
)

chain_bolt_hit_214388 = resolve_copy(
    214388, 'Chain Bolt', School.NATURE, 'The bolt leaps to the nearest ally.',
    f'{_D3}, EL4: each player the bolt strikes: the target, then the nearest player within 6 yd (heroic 10) of the '
    'last one struck, at most 2 jumps (heroic no limit). 20% each (heroic 40% on the target and each jump 25% more '
    'than the last, times his Voltage), the tank row on the tank, no Weakened; +1 V a jump. Registry tags 45 / 44. '
    'Copy of the resolve spell 205001 (Nature), Chain Bolt\'s SV 36.',
    icon=_ICON_CHAIN_BOLT, visual=EL_CHAIN,
)

# --- EL5 Shock -------------------------------------------------------------------------------------------------------

shock_214389 = _at_player(
    spell_id=214389, name='Shock', cast_ms=0, visual=EL_SHOCK, icon=_ICON_SHOCK, kickable=False,
    desc='A jolt of lightning.',
    notes=f'{_D3}, EL5: first at 6 s, then every 8 s, an instant at a random player within 20 yd of him (and his '
          'victim every 3 s once it has been out of his reach 5 s: RB-4). Not triggered: a kick\'s Nature lockout '
          'refuses it, and that Shock is lost (the reward). The hit is 214390. Shock 11084\'s SV 97.',
)

shock_hit_214390 = resolve_copy(
    214390, 'Shock', School.NATURE, 'A jolt of lightning.',
    f'{_D3}, EL5: 10% (heroic 15%, times his Voltage) of the reference row, the tank row on the tank, no Weakened, no '
    'charge. Registry tag 49. Copy of the resolve spell 205001 (Nature).',
    icon=_ICON_SHOCK,
)

# --- EL6 Static (heroic) ---------------------------------------------------------------------------------------------

static_214391 = _stacks(
    spell_id=214391, name='Static', visual=EL_STATIC, icon=_ICON_STATIC_CHARGE, target=TARGET_UNIT_TARGET_ANY,
    debuff=True, duration_ms=STATIC_MS,
    desc='Every step builds static. At 20 it discharges.',
    aura_desc='Moving builds static; standing still drains it. At 20 it discharges into you and the nearest ally.',
    notes=f'{_D3}, EL6 heroic: one stack per yard the player moved (horizontal; a teleport adds none), 2 drained a '
          'second standing still, set by the script every 250 ms (its life refreshed while it shows, so one left by '
          'a crash runs out). At 20 the player discharges (214392) and it resets. BM-G\'s move cost reads this '
          'count (bots above 12 make no optional move). Not dispellable, NO_IMMUNITIES. Static Charge 31715\'s SV '
          '7867. Removed from everyone on his reset, evade or death.',
)

discharge_hit_214392 = resolve_copy(
    214392, 'Electric Discharge', School.NATURE, 'Built-up static discharges.',
    f'{_D3}, EL6 heroic: a Static discharge: 40% (times his Voltage) of the reference row to the carrier, with '
    'Weakened, and to the nearest ally within 10 yd, the tank row on a tank; +1 V to him. Registry tag 46. Copy of '
    'the resolve spell 205001 (Nature).',
    icon=_ICON_SUPERCHARGE,
)

discharge_look_214393 = self_visual(
    214393, 'Electric Discharge', EL_DISCHARGE,
    f'{_D3}, EL6: the discharge\'s look, cast by a Blast Stalker 301132 (triggered) at the carrier\'s feet. SV 3 '
    '(Electric Discharge 29151\'s SV 4229 is the wrong tone and never wired). Look only.',
    icon=_ICON_SUPERCHARGE, school=School.NATURE,
)
