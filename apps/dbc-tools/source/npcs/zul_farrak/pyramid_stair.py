"""
Zul'Farrak build WP-D4b: the Stair (stage 2 of the Pyramid) and the Altar (stage 3) with Shadowpriest Sezz'ziz (7275)
and Nekrum Gutchewer (7796), the wave specialists (301015-301017) and Weegli's barrel (301018), normal and heroic
(.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D4b and its kick and dispel table, s3.6, s3.8,
s7 #11 A, #20 A, #31 A, #32 A, #44 A; build spec docs/dungeons/zul-farrak-rework.md SP 1346-1432 (PY4-PY16), design
SP 1180-1281). WP-D4b owns this file (its spells: kSpellsStair 213990-214029 of modules/mod-dungeon-bosses
src/ZulFarrak/ZulFarrakRework.h only; StairLogic.h names 213990-214009, SezzzizLogic.h 214010-214029, the same ids).
The engine side is src/ZulFarrak/pyramid_stair_rework.cpp (the two stage directors, the specialists, the barrel, the
crew's places) and boss_sezzziz_rework.cpp (Sezz'ziz, Nekrum); the texts and the specialists' equipment are
data/sql/updates/pending_db_world/rev_pyramid_stair_zul_farrak.sql. The lane stalker is D4a's 301019
(sandfury_executioner.py).

- 7275 Shadowpriest Sezz'ziz: boss_sezzziz_rework (the S0 rev replaces npc_shadowpriest_sezziz), normal health 95,938 =
  62.5 on the level 46 paladin base 1,535 (s3.6, s7 #1 A x1.6), DamageModifier 2.4 from 7.5 (s7 #44 A), immunity
  1972, INSTANCE_BIND with both assist flags, detection 12 (WP-S0's boss_columns). Heroic 159,951 and his melee are
  WP-H's overrides. He carries the Pyramid's loot list (L-1).
- 7796 Nekrum Gutchewer: boss_nekrum_rework (SmartAI off), 48,048 = 26.0 on the level 45 warrior base 1,848,
  DamageModifier 3.0 from 7.5 (s7 #44 A), the same columns. Heroic 79,962 is WP-H's.
- 301015 Sandfury Berserker (Blood Drinker 5649's look and loot), 301016 Sandfury Hexmaster (Shadowcaster 5648's),
  301017 Sandfury Witch Doctor (Witch Doctor 5650's): copies, since their sources stand all over the city (55, 26 and
  39 spawns). Elite as their sources, HealthModifier 3 on their sources' lowest level: 5,346 / 3,603 / 4,278 (SP).
  Each names its heroic entry (difficulty_entry_1 = WP-H's predicted 310539-310541, heroic_ids.lock's order; WP-H's
  override gives them 9,000). No SmartAI (their sources' Flee for Assist is gone: SP "Waves: Acolyte Flee for Assist
  Remove"); the C++ scripts run their kits.
- 301018 Weegli's Barrel: the fused keg (CDI 26252 at object scale 2.0, V's PY_BARREL_DISPLAY; its model info is V's
  patch SQL), a helper nobody targets, sliding upright down the lane (no stock barrel rolls). No heroic template.

Spells (213990-214029). Damage through the registry is a percent of the reference row (resolve copies: the combat log
names the mechanic, IGNORE_CASTER_MODIFIERS, NO_REDIRECTION, NO_REFLECTION); bleeds through the kit's refflat
periodic. Tooltips are number-free.

  213990  Weegli's Barrel       PY4 a player on the lane: resolve copy (Fire), 40% / 50%, Weakened, Knockdown rider
  213991  Knockdown             PY4 the rider: a 2 s stun (SV 522)
  213992  Weegli's Barrel       PY4 the barrel going off at the foot (look, SV 889)
  213993  Weegli's Barrel       PY4 a troll on the lane: the source of the script's 50% (never cast)
  213994  Rend                  PY6 the Berserker's bleed (normal): 2% of the row a second, 12 s, Physical
  213995  Rend                  PY6 the bleed opening (look, SV 372)
  213996  Trampling Charge      PY7 heroic: the charge path, resolve copy (Physical), 30% + Weakened
  213997  Curse of Blood        PY8 Curse: +10% Physical damage taken, 30 s
  213998  Sandfury Hex          PY9 heroic: Curse, a stack every 4 s, the frog at 5 (spell_zf_sandfury_hex)
  213999  Hexed                 PY9 heroic: Magic, a 2 s frog (polymorph)
  214000  Lava Spout            PY11 heroic: the totem's 8 yd zone, resolve copy (Fire), 6% every 3 s
  214001  Lava Spout Totem      PY11 heroic: the Witch Doctor's 1 s bar
  214002  Lava Spout            PY11 heroic: the totem's fire disc (look, the shipped 8 yd FlameZone 90508)
  214003-214009 spare
  214010  Blood Offering        PY12 normal: the 3 s cast (Fire, kickable)
  214011  Blood Offering        PY12 heroic: the 2 s cast
  214012  Blood Offering        PY12 a player offered: resolve copy (Shadow), 25%
  214013  Blood Frenzy          PY12 normal: +50% damage done, 15 s (SV 47)
  214014  Blood Frenzy          PY12 heroic: +50% damage done a stack (the amount is the script's), no end, no cap
  214015  Psychic Scream        PY13 the 2 s bar (Physical school, not kickable: rule 24)
  214016  Psychic Scream        PY13 the rider: a 2 s fear (Magic), SV 247
  214017  Blood Offering        PY12 the red beam (SV 7270): a channel field on him while the bar runs, never cast
  214018-214029 spare

Kept as cast (stock): Shadow Bolt 15537 (Sezz'ziz), Hamstring 26141 and Berserker Charge 19471 (Nekrum), Shadow Bolt
9613 (Hexmaster, the stock Acolyte's), Flash Heal 17843 and Healing Ward 11899 (Witch Doctor). Weakened is BM's 205000.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, Mechanic, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    self_visual,
)
from lib.dsl.registry import (
    creature_model,
    creature_template,
    creature_template_columns,
    scripted_by,
    spell,
)

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_SANDFURY,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BARREL_SCALE,
    DISPLAY_BERSERKER,
    DISPLAY_BERSERKER_2,
    DISPLAY_HEXMASTER,
    DISPLAY_HEXMASTER_2,
    DISPLAY_WITCH_DOCTOR,
    DISPLAY_WITCH_DOCTOR_2,
    PY_BARREL_BLAST,
    PY_BARREL_DISPLAY,
    PY_BLEED,
    PY_BLEED_STATE,
    PY_BLOOD_OFFERING,
    PY_CURSE,
    PY_FROG_CREATURE,
    PY_HEX,
    PY_KNOCKDOWN,
    PY_LAVA_TOTEM_ZONE,
    PY_OFFERING_BUFF,
    PY_SCREAM,
)

creature_template_columns(7275, **boss_columns(
    'boss_sezzziz_rework', 62.5, damage_modifier=2.4,
))

creature_template_columns(7796, **boss_columns(
    'boss_nekrum_rework', 26.0, damage_modifier=3.0,
))

_PY = "Zul'Farrak build WP-D4b (the Stair and the Altar)"
_SCRIPT_DAMAGE = ("Zul'Farrak: the kit's spell_dungeon_refflat_periodic sets each tick (a percent of the reference "
                  "row, hundredths in the base point), not a potency value")

_SCHOOL_MASK_PHYSICAL = 1
_SCHOOL_MASK_ALL = 127
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000      # a finished cast keeps the swing timer (LESSONS L3)
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000             # the aura never leaves the instance on the character
_INTERRUPT_KICKABLE = 0x0F                          # movement, pushback, interrupt, auto-attack (stock casters)
_PREVENTION_SILENCE = 1
_DISPEL_MAGIC, _DISPEL_CURSE = 1, 2

# StairLogic.h / SezzzizLogic.h Tune (the DT test pins each against the headers).
_KNOCKDOWN_MS = 2000                # kKnockdownMs
_BLEED_TICK = 200                   # kBleedTickHundredths (2.00% of the reference row)
_BLEED_TICK_MS = 1000               # kBleedTickMs
_BLEED_MS = 12000                   # kBleedMs
_CURSE_MS = 30000                   # kCurseMs
_CURSE_PCT = 10                     # kCursePhysicalTakenPct
_CURSE_RANGE = 40.0                 # kCurseRangeYd
_HEX_STACK_MS = 4000                # kHexStackMs
_HEX_STACKS = 5                     # kHexMaxStacks
_HEX_MS = 30000                     # the curse's life: the frog comes at 16 s
_HEXED_MS = 2000                    # kHexedMs
_TOTEM_BAR_MS = 1000                # kTotemBarMs
_OFFERING_CAST_MS = (3000, 2000)    # kOfferingCastMs
_OFFERING_RANGE = 40.0              # kOfferingRangeYd
_FRENZY_PCT = 50                    # kFrenzyPct
_FRENZY_MS = 15000                  # kFrenzyMs
_FRENZY_STACKS = 255                # kFrenzyStackLimit
_SCREAM_CAST_MS = 2000              # kScreamCastMs
_FEAR_MS = 2000                     # kFearMs

# Stock icons (Spell.dbc).
_ICON_EXPLODE = 3012                # Explode 47496
_ICON_KNOCKOUT = 314                # Knockout 17307
_ICON_REND = 245                    # Rend 772
_ICON_TRAMPLE = 168                 # Trample 5568
_ICON_CURSE_OF_BLOOD = 130          # Curse of Blood 16098
_ICON_HEX = 3058                    # Hex 16097
_ICON_SCORCHING_TOTEM = 680         # Scorching Totem 15038
_ICON_FIRE = 11                     # Lava 16455
_ICON_RITUAL_OF_BLOOD = 2724        # Uzo's Ritual of Blood 10727
_ICON_BLOOD_FURY = 1662             # Blood Fury 20572
_ICON_PSYCHIC_SCREAM = 1488         # Psychic Scream 13704

# The specialists' creature_classlevelstats bases (their sources' lowest level): warrior 44 1,782, mage 43 1,201,
# paladin 44 1,426; HealthModifier 3 on each gives SP's 5,346 / 3,603 / 4,278.
BERSERKER = 301015
HEXMASTER = 301016
WITCH_DOCTOR = 301017
BARREL = 301018
# heroic_ids.lock: WP-H's predicted ids (the kit adds after the stock set, in entry order).
BERSERKER_HEROIC = 310539
HEXMASTER_HEROIC = 310540
WITCH_DOCTOR_HEROIC = 310541


def _look(spell_id: int, name: str, visual: int, icon: int, notes: str):
    """A look cast triggered on its target: an instant DUMMY, no handler, hidden from the log."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- PY4 Weegli's Barrels --------------------------------------------------------------------------------------------

barrel_hit_213990 = resolve_copy(
    213990, "Weegli's Barrel", School.FIRE, 'A barrel of blasting powder rolls down the stair.',
    f'{_PY}, PY4: every 15 s (heroic 12 s) Weegli yells line 3 and a barrel is lit at the lip; the lane (the stair '
    'from y 1227 to 1259 at its true width, s7 #31 A) is drawn for 3 s, then the barrel rolls: every player on it '
    'takes 40% (heroic 50%) of the reference row (the tank row on the tank) with Weakened (ruling 23, both '
    'difficulties) and the Knockdown rider (213991), through the kit\'s RegistryHit (the script judges the lane). '
    'Copy of the resolve spell 205003 (Fire). The blast (SV 889) on every player hit.',
    icon=_ICON_EXPLODE, visual=PY_BARREL_BLAST,
)

knockdown_213991 = spell(
    id=213991, name='Knockdown', school=School.NORMAL, dispel=0, mechanic=Mechanic.STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_KNOCKDOWN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=Mechanic.STUN, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_KNOCKOUT,
    notes=f'{_PY}, PY4: the 2 s stun (the shared limit on loss of control, SP "Knockdown, the 2 sec cap") the '
          'barrel\'s hit leaves on every player on the lane: the registry\'s rider, cast by the lane stalker. '
          'Mechanic Stun and not NO_IMMUNITIES, so a stun immunity is a reward. Dispel none: 2 s. Knockdown 5164\'s '
          'SV 522. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Knocked down by the blast.', 'Knocked down.', CastingTimeIndex=1,
                          SpellVisualID_1=PY_KNOCKDOWN, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

barrel_blast_213992 = self_visual(
    213992, "Weegli's Barrel", PY_BARREL_BLAST,
    f'{_PY}, PY4: the barrel (301018) going off as it reaches the stair\'s foot, cast by the barrel on itself '
    '(triggered), then it is gone. V\'s PY_BARREL_BLAST (SV 889, a fiery explosion; alternates 729, 572). Look only: '
    'the hit is 213990 and the script\'s troll damage.',
    icon=_ICON_EXPLODE, school=School.FIRE,
)

barrel_troll_213993 = spell(
    id=213993, name="Weegli's Barrel", school=School.FIRE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_EXPLODE,
    notes=f'{_PY}, PY4: never cast. The source spell of the script\'s damage on every troll on the lane as the '
          'barrel rolls (Unit::DealDamage, Fire: 50% of the troll\'s health), then the troll is knocked down the '
          'stair (KnockbackFrom a point up the stair).',
    raw_overrides=kit_raw('A barrel of blasting powder rolls down the stair.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- PY6 / PY7 the Berserker ---------------------------------------------------------------------------------------

rend_213994 = spell(
    id=213994, name='Rend', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=_BLEED_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=_BLEED_TICK,
                    die_sides=0, amplitude=_BLEED_TICK_MS, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_DAMAGE)],
    spell_icon_id=_ICON_REND,
    notes=f'{_PY}, PY6 (normal): the Berserker\'s bleed on the player he charged (8 to 25 yd away, tank included, '
          'every 12 to 16 s from 4 s): 2% of the reference row a second for 12 s (the kit\'s '
          'spell_dungeon_refflat_periodic, base point 200 = 2.00% in hundredths; the tank row on the tank), Physical. '
          'Not dispellable (the kick table: "Berserker bleed: not dispellable"); ignores caster modifiers. On heroic '
          'the charge leaves Grievous Wound (213963) instead. Rend 772\'s lasting look as V pairs it (SV 15286; the '
          'one-shot 372 is 213995). AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('A deep bleeding gash.', 'Bleeding.', CastingTimeIndex=1, SpellVisualID_1=PY_BLEED_STATE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(rend_213994, 'spell_dungeon_refflat_periodic')

rend_look_213995 = _look(
    213995, 'Rend', PY_BLEED, _ICON_REND,
    f'{_PY}, PY6: the one-shot as the Berserker\'s bleed opens (triggered on the target with 213994). Rend 772\'s SV '
    '372 (the lasting look is 213994\'s 15286).')

trampling_213996 = resolve_copy(
    213996, 'Trampling Charge', School.NORMAL, 'Trampled by a charging Berserker.',
    f'{_PY}, PY7 (heroic): the Berserker\'s charge path, drawn as a 4 yd line from him to his target 1.5 s before he '
    'charges along it: 30% of the reference row (the tank row on the tank) and Weakened on everyone on it but the '
    'target (the registry\'s eligibility: every player but the target), through the registry. Copy of the resolve '
    'spell 205001 (Physical: armor cuts it).',
    icon=_ICON_TRAMPLE,
)

# --- PY8 / PY9 the Hexmaster ---------------------------------------------------------------------------------------

curse_of_blood_213997 = spell(
    id=213997, name='Curse of Blood', school=School.SHADOW, dispel=_DISPEL_CURSE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=_CURSE_RANGE, duration_ms=_CURSE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=_CURSE_PCT, die_sides=0, misc_value=_SCHOOL_MASK_PHYSICAL,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Curse of Blood: a flat percent of Physical damage taken, not a damage value')],
    spell_icon_id=_ICON_CURSE_OF_BLOOD,
    notes=f'{_PY}, PY8: the Hexmaster\'s curse on a random player within 40 yd (tank included), first at 6 s, then '
          'every 15 to 20 s: +10% Physical damage taken for 30 s. A Curse: curing it is a reward (bots cure it, '
          'priority 1). Instant, Shadow (a kick on his Shadow Bolt delays it: a kick\'s reward). Curse of Blood '
          '8282\'s SV 876. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Curses the target: more Physical damage taken.', 'Physical damage taken increased.',
                          CastingTimeIndex=1, SpellVisualID_1=PY_CURSE, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

sandfury_hex_213998 = spell(
    id=213998, name='Sandfury Hex', school=School.SHADOW, dispel=_DISPEL_CURSE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=_CURSE_RANGE, duration_ms=_HEX_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, base_points=0,
                    amplitude=_HEX_STACK_MS, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HEX,
    notes=f'{_PY}, PY9 (heroic, in place of Curse of Blood): a stacking Curse, a stack every 4 s (its periodic '
          'dummy; spell_zf_sandfury_hex); the stack that would make 5 turns the carrier into a frog for 2 s (Hexed, '
          '213999) and the curse clears: 16 s after it lands. Curing it at any stack is a reward. 5 stacks shown at '
          'most. Curse of Blood 8282\'s SV 876. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('A hex that grows until the target becomes a frog.', 'Hexed by the Sandfury. At the last '
                          'stack you become a frog.', CastingTimeIndex=1, CumulativeAura=_HEX_STACKS,
                          SpellVisualID_1=PY_CURSE, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(sandfury_hex_213998, 'spell_zf_sandfury_hex')

hexed_213999 = spell(
    id=213999, name='Hexed', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=Mechanic.POLYMORPH,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_HEXED_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=Mechanic.POLYMORPH, implicit_target_a=TARGET_UNIT_TARGET_ANY),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.TRANSFORM, base_points=0,
                    misc_value=PY_FROG_CREATURE, mechanic=Mechanic.POLYMORPH,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HEX,
    notes=f'{_PY}, PY9 (heroic): the Sandfury Hex at its last stack: the player is a frog for 2 s (the shared limit '
          'on loss of control): the frog creature 7552\'s look (V\'s PY_FROG_CREATURE) and a stun with the '
          'polymorph mechanic (the frog holds still: a confused frog could hop onto the barrel lane). Magic: curing '
          'it is a reward (bots cure it first, urgent). Hex 11641\'s SV 2295. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Turned into a frog.', 'A frog.', CastingTimeIndex=1, SpellVisualID_1=PY_HEX,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- PY11 the Lava Spout Totem (heroic) -------------------------------------------------------------------------------

lava_spout_214000 = resolve_copy(
    214000, 'Lava Spout', School.FIRE, 'Lava spouts from the totem.',
    f'{_PY}, PY11 (heroic): the Lava Spout Totem\'s zone: an 8 yd circle the totem owns (a persistent registry Zone, '
    'armed after 1.5 s, the warning floor), 6% of the reference row (the tank row on the tank) every 3 s for its 20 s '
    '(tuned from the stock 8265, SP). No Weakened (a lingering zone). Copy of the resolve spell 205003 (Fire). The '
    'totem\'s fire disc is 214002.',
    icon=_ICON_FIRE,
)

lava_totem_bar_214001 = cast_bar(
    214001, 'Lava Spout Totem', _TOTEM_BAR_MS, 'Raises a Lava Spout Totem.',
    f'{_PY}, PY11 (heroic): the Witch Doctor\'s 1 s bar, first at 10 s then every 20 s; when it ends the script raises '
    'the totem (the stock Lava Spout Totem 6017, V\'s PY_TOTEM_CREATURE, 20 s, her faction, passive and rooted) on '
    'the landing: at her feet on the landing or the top (or the plaza at the Altar), at the lip when she casts from '
    'the stair. Not interruptible (a kick must not look as if it stopped what the registry still lands).',
    icon=_ICON_SCORCHING_TOTEM, school=School.FIRE,
)

lava_glow_214002 = spell(
    id=214002, name='Lava Spout', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FIRE,
    notes=f'{_PY}, PY11 (heroic): the totem\'s fire disc, a DUMMY aura the script casts on the totem (triggered) as it '
          'rises; it goes with the totem. V\'s PY_LAVA_TOTEM_ZONE (the shipped 8 yd FlameZone STATE, SV 90508, the '
          'Stratholme hearth precedent). Look only: the registry\'s circle (214000) owns the hit.',
    raw_overrides=kit_raw('Lava spouts here.', 'Lava spouts here.', instant=True, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=PY_LAVA_TOTEM_ZONE),
)

# --- PY12 Blood Offering ----------------------------------------------------------------------------------------------


def _blood_offering(spell_id: int, cast_ms: int, which: str):
    return spell(
        id=spell_id, name='Blood Offering', school=School.FIRE, cast_time_ms=cast_ms, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_OFFERING_RANGE, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=_ICON_RITUAL_OF_BLOOD,
        notes=f'{_PY}, PY12 ({which}): Sezz\'ziz\'s {cast_ms // 1000} s cast on a surviving crew fighter in reach, '
              'else a random player (tank included), first at 6 s, then every 15 to 18 s, with emote line 0 and the '
              'red beam (214017). No effect: when it ends (OnSpellCast) the script lands it: the crew member dies '
              '(BlyCrew.h KillCrew) or the player takes 214012; he heals 15% (heroic 25%) and gains Blood Frenzy. '
              'Fire school, kickable (InterruptFlags 15, PreventionType silence): the only Fire cast he has, so a '
              'kick locks nothing else (the kick table; rule 24). Bots kick it first (required on heroic). Keeps his '
              'swing timer.',
        raw_overrides=kit_raw('Offers a victim\'s blood to the loa.', InterruptFlags=_INTERRUPT_KICKABLE,
                              PreventionType=_PREVENTION_SILENCE, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS),
    )


blood_offering_214010 = _blood_offering(214010, _OFFERING_CAST_MS[0], 'normal')
blood_offering_h_214011 = _blood_offering(214011, _OFFERING_CAST_MS[1], 'heroic')

blood_offering_hit_214012 = resolve_copy(
    214012, 'Blood Offering', School.SHADOW, 'Blood drawn for the loa.',
    f'{_PY}, PY12: a Blood Offering landed on a player (no crew fighter left in reach): 25% of the reference row (the '
    'tank row on the tank), no Weakened (a setback: his heal and frenzy are the cost), through the kit\'s '
    'RegistryHit. Copy of the resolve spell 205006 (Shadow).',
    icon=_ICON_RITUAL_OF_BLOOD,
)


def _frenzy(spell_id: int, base: int, duration_ms: int, stacks: int, which: str, notes: str):
    return spell(
        id=spell_id, name='Blood Frenzy', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=base,
                        die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded='Blood Frenzy: a flat percent of damage done, not a damage value')],
        spell_icon_id=_ICON_BLOOD_FURY, notes=f'{_PY}, PY12 ({which}): {notes}',
        raw_overrides=kit_raw('Fed by the blood of the offered.', 'Damage done increased.', instant=True,
                              CumulativeAura=stacks, SpellVisualID_1=PY_OFFERING_BUFF, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


blood_frenzy_214013 = _frenzy(
    214013, _FRENZY_PCT, _FRENZY_MS, 0, 'normal',
    'a landed Blood Offering: +50% damage done (all schools) for 15 s, cast by Sezz\'ziz on himself (triggered; a new '
    'Offering refreshes it). His reference-sized hits ignore caster modifiers: it raises his melee and Shadow Bolt. '
    'Not dispellable. Blood Fury 20572\'s SV 47.')

blood_frenzy_h_214014 = _frenzy(
    214014, 0, -1, _FRENZY_STACKS, 'heroic',
    'a landed Blood Offering: one stack for good, +50% damage done a stack with no cap (ruling 46; the old table\'s '
    '"+100% 15 s" is stale, handoff s8 #9): the base point is 0 and the script sets the amount to 50 x stacks with '
    'AuraEffect::ChangeAmount (Blood Price\'s pattern), CumulativeAura 255 shows the stacks. Not dispellable. Blood '
    'Fury 20572\'s SV 47.')

# --- PY13 Psychic Scream ----------------------------------------------------------------------------------------------

scream_bar_214015 = cast_bar(
    214015, 'Psychic Scream', _SCREAM_CAST_MS, 'Gathers a terrifying scream.',
    f'{_PY}, PY13: Sezz\'ziz\'s 2 s bar, first at 10 s then every 22 to 30 s, with the registry\'s 8 yd circle on him '
    '(the fear rider 214016 on everyone inside as it ends). Physical school and not interruptible: his Shadow Bolt is '
    'a kickable Shadow cast, and a kick locks the whole school (rule 24, LESSONS L2), so a Shadow bar would be refused '
    'after any kick. The stock Psychic Scream 13704 is retired as cast.',
    icon=_ICON_PSYCHIC_SCREAM,
)

scream_fear_214016 = spell(
    id=214016, name='Psychic Scream', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=Mechanic.FEAR,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_FEAR_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_FEAR, base_points=0,
                    mechanic=Mechanic.FEAR, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_PSYCHIC_SCREAM,
    notes=f'{_PY}, PY13: the 2 s fear (the shared limit on loss of control) the Scream leaves on everyone in its 8 yd '
          'circle, tank included: the registry\'s rider, cast by Sezz\'ziz. Magic: curing it is a reward (the kick '
          'table). Mechanic Fear and not NO_IMMUNITIES, so a fear break is a reward. V\'s PY_SCREAM (SV 247, the '
          'fear skulls). AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Terrified by the scream: runs in fear for $d.', 'Running in terror.', CastingTimeIndex=1,
                          SpellVisualID_1=PY_SCREAM, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

blood_offering_beam_214017 = spell(
    id=214017, name='Blood Offering', school=School.FIRE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG, dispel=0,
    mechanic=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=100.0, duration_ms=3000,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_RITUAL_OF_BLOOD,
    notes=f'{_PY}, PY12: the red beam from Sezz\'ziz to the one offered while the bar runs: never cast; the script '
          'sets his channel fields (UNIT_FIELD_CHANNEL_OBJECT = the target, UNIT_CHANNEL_SPELL = this id) at the '
          'bar\'s start and clears them when it ends or is kicked (D4a\'s rope pattern). V\'s PY_BLOOD_OFFERING (SV '
          '7270, Blood Siphon\'s beam; 107 Sacrifice is a gold glow, never wired).',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=PY_BLOOD_OFFERING,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- 301015-301017 the specialists, 301018 the barrel ---------------------------------------------------------------


def _specialist(entry: int, name: str, *, level: int, unit_class: int, script: str, heroic: int, loot: int,
                gold: tuple[int, int], mana: float, displays: tuple[int, int]):
    """A wave specialist: an elite Sandfury copy of a dungeon trash entry (its look, its loot, its gold), no SmartAI,
    standing still until the Stair's director sends it (MovementType 0)."""
    creature_template(
        entry, name, **{
            **KIT_CREATURE, 'faction': FACTION_SANDFURY, 'minlevel': level, 'maxlevel': level, 'rank': 1,
            'unit_class': unit_class, 'unit_flags': 0, 'HealthModifier': 3.0, 'DamageModifier': 2.4,
            'ManaModifier': mana, 'BaseAttackTime': 2000, 'ExperienceModifier': 1.25, 'detection_range': 20.0,
            'lootid': loot, 'pickpocketloot': loot, 'skinloot': 0, 'mingold': gold[0], 'maxgold': gold[1],
            'ScriptName': script, 'difficulty_entry_1': heroic,
        },
    )
    for idx, display in enumerate(displays):
        creature_model(entry, display_id=display, idx=idx)


_specialist(BERSERKER, 'Sandfury Berserker', level=44, unit_class=1, script='npc_zf_sandfury_berserker',
            heroic=BERSERKER_HEROIC, loot=5649, gold=(197, 1377), mana=1.0,
            displays=(DISPLAY_BERSERKER, DISPLAY_BERSERKER_2))
_specialist(HEXMASTER, 'Sandfury Hexmaster', level=43, unit_class=8, script='npc_zf_sandfury_hexmaster',
            heroic=HEXMASTER_HEROIC, loot=5648, gold=(185, 1293), mana=2.0,
            displays=(DISPLAY_HEXMASTER, DISPLAY_HEXMASTER_2))
_specialist(WITCH_DOCTOR, 'Sandfury Witch Doctor', level=44, unit_class=2, script='npc_zf_sandfury_witch_doctor',
            heroic=WITCH_DOCTOR_HEROIC, loot=5650, gold=(197, 1377), mana=2.0,
            displays=(DISPLAY_WITCH_DOCTOR, DISPLAY_WITCH_DOCTOR_2))

barrel_301018 = creature_template(
    BARREL, "Weegli's Barrel", **{**KIT_HELPER, 'minlevel': 46, 'maxlevel': 46, 'rank': 0, 'unit_class': 1,
                                  'type': 10, 'ScriptName': 'npc_zf_weegli_barrel'},
)
creature_model(BARREL, display_id=PY_BARREL_DISPLAY, scale=BARREL_SCALE)
