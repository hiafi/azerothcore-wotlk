"""
Stratholme build WP-S15: Baron Rivendare's hard mode, the Ultimatum (heroic only)
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.7, s3.5 row S15, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 3709-3747 (Hard mode), ST 3807-3828 (Implementation), ST 3868-3871 (the HM
rows)). WP-S15 owns this file (its spells: kSpellsUltimatum 206720-206734 of modules/mod-dungeon-bosses
src/Stratholme/StratholmeRework.h only; BaronHardModeLogic.h names the same ids; its creature: 300589). The engine side
is src/Stratholme/baron_hard_mode.cpp, a BaronHardMode on S14's AI (BaronFight.h); the opt-in (Ysida's gossip option,
its `conditions`, her SmartAI select row) and the texts are WP-S15's SQL rev.

- 300589 Ysida, Risen (HM1, the third missed execution): 40,000 health (HealthModifier 13.106 on the level 60 warrior
  base 3,052, the ST build spec), the Scourge's faction 21, undead, stun immune (1972), no XP and no loot. Display
  25355 (the Death Knight Initiate outfit on the human female, VISUALS-REPORT gap 22 rank 1) with Hysteria's look
  (206734). npc_st_ysida_risen: she fixes on the nearest player every second, strikes her victim every 2 s (206733)
  and throws a Death Coil (206732) every 10 s; no auto attack (DamageModifier 0). Summoned by the Baron (his servant:
  Unholy Aura counts her, the rot heals her, S14's cleanup despawns her). Hard mode only, so no heroic template
  (handoff s7 #15; source/world/dungeons/stratholme.py leaves her out).

Spells. The lane and the trail deal their damage through dungeon copies of the mod-boss-mechanics resolve spell (the
registry's percent of the reference row; the combat log names the mechanic). The execution's blow is set at launch by
its own SpellScript (30% x (1 + Condemned stacks)); the trample, Condemned's ticks, Ysida, Risen's strike and Death
Coil are the kit's generic percent spells (spell_dungeon_refflat_damage / _periodic: hundredths in the effect value,
heroic in EffectMiscValueB; the hard mode is heroic only, so both carry the heroic number). The rot's heal is an exact
amount from the script. The rest are auras, casts and looks:

  206720  Execution            HM1 the 3 s channel at Ysida (the bar, and Shadow Sear 30735's purple beam SV 7785)
  206721  Execution            HM1 the blow on the first player on the line: Shadow, 30% x (1 + Condemned stacks)
  206722  Execution            HM1 nobody on the line: the blow's look on Ysida (she loses a third of her life)
  206723  Condemned            HM2 the stack on a taker, the whole fight, no cap (Unholy Blight 50536's mist SV 11095)
  206724  Condemned            HM2 1% Shadow a second for 10 s, refreshed by every execution taken
  206725  Price of Defiance    HM1 on him once Ysida falls: +200% damage done (Unholy Frenzy 8699's SV 47)
  206726  Deathcharger         HM3 the 3 s mark on the lane's target
  206727  Deathcharger         HM3 the target's 20% (not avoidable), Charge 22911's look, lands as he does
  206728  Deathcharger         HM3 the lane's 50% Physical on everyone else inside: resolve copy (Physical)
  206729  Unholy Ground        HM3 the trail's 1 s tick: resolve copy (Shadow), 5%
  206730  Unholy Ground        HM3 the trail's look on a rot stalker (3 yd, Death and Decay 49936's SV 9735)
  206731  Rotting Vigor        HM4 the rot's heal: him 1%, his undead 5% of their health a second (exact amount)
  206732  Death Coil           Ysida, Risen: Shadow 15% (Death Coil 6789's missile SV 9152)
  206733  Risen Strike         Ysida, Risen: her 2 s swing, Physical 3% (Strike 11976's SV 39)
  206734  Risen                Ysida, Risen's lasting look (Hysteria 49016's SV 11514)

The boss's Condemned (206723 / 206724) is its own pair of ids, never the W1 item effect 205669 that shares the name
(handoff s11 #1, default: both names kept; the item's debuff sits on enemies, the boss's on players). Tooltips are
number-free (ST checklist item 8).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
)
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BR_CHARGE,
    BR_CONDEMNED,
    BR_DEATH_AND_DECAY,
    BR_EXECUTION_BEAM,
    BR_PRICE_OF_DEFIANCE,
    DISPLAY_YSIDA_RISEN,
    HM_YSIDA_RISEN_AURA,
)

_HM = 'Stratholme build WP-S15 (the Ultimatum, the Baron\'s hard mode)'
_SCRIPT_REFFLAT = ('Stratholme: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage / _periodic (DungeonKit::RefFlatOn)')
_SCRIPT_EXECUTION = ('Stratholme: 30% of reference health x (1 + Condemned stacks), set at launch by '
                     'spell_strat_ultimatum_execution (DungeonKit::RefFlatOn)')
_SCRIPT_EXACT = 'Stratholme: an exact amount from the script (CastCustomSpell base point 0)'

_TARGET_DEST_CASTER = 18
_TARGET_DEST_DYNOBJ_ALLY = 29
_ATTR1_IS_CHANNELED = 0x00000004
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_SCHOOL_MASK_ALL = 127
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): AC drops the aura before the logout save, after the login load and on
# a cross-map teleport, so Condemned never outlives the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

_ICON_EXECUTION = 1958              # Shadow Sear 30735
_ICON_CONDEMNED = 1494              # Unholy Blight 50536
_ICON_PRICE = 38                    # Unholy Frenzy 8699
_ICON_CHARGE = 457                  # Charge 22911
_ICON_DEATH_AND_DECAY = 118         # Death and Decay 49936
_ICON_DEATH_COIL = 88               # Death Coil 6789
_ICON_STRIKE = 856                  # Strike 11976
_ICON_HYSTERIA = 2731               # Hysteria 49016
_SV_DEATH_COIL = 9152               # Death Coil 6789 (the missile and its impact)
_SV_STRIKE = 39                     # Strike 11976 (the swing)
_SV_EXECUTION_HIT = 45              # Shadow Burst 28447: the shadow burst on the taker's chest

# Percents in hundredths (KT-1's generic percent spells): the shown value is EffectBasePoints + 1 as stored, the heroic
# value EffectMiscValueB. The hard mode is heroic only: both carry BaronHardModeLogic.h's number.
_EXECUTION = 3000                   # kExecutionPct 30 (the script multiplies by 1 + stacks)
_CONDEMNED_DOT = 100                # kCondemnedDotPct 1
_TRAMPLE = 2000                     # kTargetHitPct 20
_RISEN_STRIKE = 300                 # kRisenStrikePct 3
_DEATH_COIL = 1500                  # kDeathCoilPct 15
_PRICE_OF_DEFIANCE = 200            # kPriceOfDefiancePct

# --- 300589 Ysida, Risen ---------------------------------------------------------------------------------------------

# Level 60 warrior base 3,052: ceil(3,052 x 13.106) = 40,000 (BaronHardModeLogic.h kRisenHealth).
ysida_risen_300589 = creature_template(
    300589, 'Ysida, Risen', **{
        **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': 13.106, 'DamageModifier': 0.0, 'BaseAttackTime': 2000, 'ExperienceModifier': 0.0,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'RegenHealth': 0, 'lootid': 0, 'pickpocketloot': 0,
        'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': 0x40, 'ScriptName': 'npc_st_ysida_risen',
    },
)
creature_model(300589, display_id=DISPLAY_YSIDA_RISEN)


def _refflat(spell_id: int, name: str, school: School, pct: int, icon: int, desc: str, notes: str, *, visual: int = 0,
             speed: float = 0.0, melee: bool = False, script: str = 'spell_dungeon_refflat_damage'):
    """A hit at a percent of the reference row, set at launch (the kit's generic percent spell, or the execution's own
    script), cast triggered: instant, cannot crit, ignores the caster's modifiers (the target's own defensives count),
    ignores line of sight. `melee`: a melee hit (it can miss, be dodged or parried); otherwise always hits."""
    raw = kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, EffectMiscValueB_1=pct,
                  DefenseType=_DEFENSE_MELEE if melee else _DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                  AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                  AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS | (0 if melee else ATTR3_ALWAYS_HIT),
                  AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    if speed:
        raw['Speed'] = speed
    s = spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=pct - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY,
                        potency_excluded=_SCRIPT_EXECUTION if script != 'spell_dungeon_refflat_damage'
                        else _SCRIPT_REFFLAT)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )
    scripted_by(s, script)
    return s


# --- HM1 Executions --------------------------------------------------------------------------------------------------

execution_206720 = spell(
    id=206720, name='Execution', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=3000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_EXECUTION,
    notes=f'{_HM}, HM1: his 3 s channel at Ysida in her cage (emote line 12), every 25 s from 15 s through S14\'s cast '
          'queue (it holds him: no melee, no Shadow Bolt). The bar and the beam only (a DUMMY aura on her; Shadow Sear '
          '30735\'s SV 7785, chain 10 Beam_Purple). A registry line Soak (2 yd, him to her) beside it tells the bots '
          'who steps in (the fewest Condemned stacks first). At its end the script finds the first player on the '
          'line: 206721 on them, else 206722 on her. Not interruptible (he is interrupt immune anyway). Ignores LoS '
          '(the cage).',
    raw_overrides=kit_raw('Turns his blade on the prisoner.', 'The Baron\'s blade is turned on you.',
                          CastingTimeIndex=1, InterruptFlags=0, ChannelInterruptFlags=0, PreventionType=0,
                          SpellVisualID_1=BR_EXECUTION_BEAM, AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

execution_hit_206721 = _refflat(
    206721, 'Execution', School.SHADOW, _EXECUTION, _ICON_EXECUTION,
    'Takes the Baron\'s blow meant for the prisoner. Each Condemned makes it worse.',
    f'{_HM}, HM1: the blow on the first player on the line from him to Ysida (by distance from him), cast by him '
    '(triggered) at the channel\'s end: Shadow, 30% of the heroic reference row (the tank row on the tank) times (1 + '
    'the taker\'s Condemned stacks), set at launch by spell_strat_ultimatum_execution (the shown 3000 hundredths are '
    'the base). Always hits, no Weakened (the soak is the right play); the taker then gains a Condemned stack '
    '(206723) and the 10 s DoT (206724). Shadow Burst 28447\'s SV 45 (the burst on the chest).',
    visual=_SV_EXECUTION_HIT, script='spell_strat_ultimatum_execution',
)

execution_ysida_206722 = spell(
    id=206722, name='Execution', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_EXECUTION,
    notes=f'{_HM}, HM1: nobody on the line: the blow\'s look on Ysida (triggered, no effect handler); the script takes '
          'a third of her life (the third miss kills her: Ysida, Risen 300589 and the Price of Defiance 206725). '
          'Shadow Burst 28447\'s SV 45.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=_SV_EXECUTION_HIT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- HM2 Condemned ---------------------------------------------------------------------------------------------------

condemned_206723 = spell(
    id=206723, name='Condemned', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CONDEMNED,
    notes=f'{_HM}, HM2: a stack for every execution a player takes (DungeonKit::AddStacks, caster the Baron), the '
          'whole fight, no cap (CumulativeAura 255, the aura counter\'s limit): each makes the next blow +100% '
          '(spell_strat_ultimatum_execution reads the count). A DUMMY counter: the damage is 206724\'s. Not '
          'dispellable, lands through immunities; removed on his death, evade and reset, dropped on a logout or a map '
          'change. Its own id: the W1 item effect 205669 shares the name only (handoff s11 #1). Unholy Blight 50536\'s '
          'SV 11095 (the mist state).',
    raw_overrides=kit_raw('Condemned by the Baron. His executions strike harder for every stack.',
                          'Condemned. The Baron\'s executions strike you harder for every stack.',
                          CastingTimeIndex=1, CumulativeAura=255, SpellVisualID_1=BR_CONDEMNED,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

condemned_dot_206724 = spell(
    id=206724, name='Condemned', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=_CONDEMNED_DOT - 1,
                    die_sides=1, amplitude=1000, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CONDEMNED,
    notes=f'{_HM}, HM2: the taker\'s 10 s Shadow DoT, 1% of the heroic reference row a second (the tank row on the '
          'tank; spell_dungeon_refflat_periodic: 100 hundredths, MiscValueB the same), cast by him (triggered) with '
          'every execution taken; a new one refreshes it. Not dispellable; dropped on a logout or a map change, '
          'removed with the fight. No look of its own (206723 carries the mist).',
    raw_overrides=kit_raw('Shadow damage over time.', 'Taking Shadow damage every $t1 sec.', CastingTimeIndex=1,
                          EffectMiscValueB_1=_CONDEMNED_DOT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(condemned_dot_206724, 'spell_dungeon_refflat_periodic')

price_of_defiance_206725 = spell(
    id=206725, name='Price of Defiance', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
                    base_points=_PRICE_OF_DEFIANCE, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Price of Defiance: a flat +200% damage done, not a damage or heal value')],
    spell_icon_id=_ICON_PRICE,
    notes=f'{_HM}, HM1 (ruling 59): on him once Ysida falls (the third missed execution), the rest of the fight: +200% '
          'damage done, every school. It raises his melee, Mortal Strike, Cleave and Shadow Bolt; the reference-sized '
          'hits ignore caster modifiers, so they stay exact. Removed on his death, evade and reset. Not dispellable. '
          'Unholy Frenzy 8699\'s SV 47 (glowing hands and a roar flash).',
    raw_overrides=kit_raw('The prisoner\'s death drives him into a fury.', 'Damage dealt greatly increased.',
                          instant=True, SpellVisualID_1=BR_PRICE_OF_DEFIANCE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- HM3 Deathcharger ------------------------------------------------------------------------------------------------

deathcharger_mark_206726 = spell(
    id=206726, name='Deathcharger', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=3000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CHARGE,
    notes=f'{_HM}, HM3: the 3 s mark on the farthest non-tank (emote line 13), cast by him (triggered) through S14\'s '
          'cast queue (every 30 s from 22 s), while the registry lane (6 yd, him to them) follows them; at its end the '
          'lane locks and he charges. No look of its own (the lane is the telegraph). Removed with the fight.',
    raw_overrides=kit_raw('Marked for the Deathcharger.', 'The Baron will ride you down. Lead his lane away from your '
                          'allies.', CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

trample_206727 = _refflat(
    206727, 'Deathcharger', School.NORMAL, _TRAMPLE, _ICON_CHARGE, 'Ridden down by the Deathcharger.',
    f'{_HM}, HM3: the lane\'s target, cast by him (triggered) as the lane locks and he charges: Physical, 20% of the '
    'heroic reference row (the tank row on the tank, never in practice; 2000 hundredths, MiscValueB the same), not '
    'avoidable (always hits, magic defense type, ignores LoS). Speed 42 (his charge speed), so it lands as he does. '
    'Charge 22911\'s SV 3783 (the chest trail and dust at his start, the impact on the target).',
    visual=BR_CHARGE, speed=42.0,
)

lane_206728 = resolve_copy(
    206728, 'Deathcharger', School.NORMAL, 'Caught in the Deathcharger\'s path.',
    f'{_HM}, HM3: the lane\'s hit on everyone else inside it (the target is not eligible) as it locks: a 6 yd registry '
    'line from him toward the target, 50% of the heroic non-tank row, Weakened. Copy of the resolve spell 205000 '
    '(Physical). No visual (the charge is the look).',
    icon=_ICON_CHARGE,
)

trail_206729 = resolve_copy(
    206729, 'Unholy Ground', School.SHADOW, 'Rotting ground.',
    f'{_HM}, HM3: the trail\'s 1 s tick on everyone inside the charge\'s 6 yd lane for 20 s (a persistent registry '
    'line, the first tick a second after he lands): 5% of the heroic non-tank row, one Weakened per player per trail '
    '(as the heroic Death and Decay, S14\'s 206709). Copy of the resolve spell 205001 (Shadow). No visual (206730 is '
    'the look).',
    icon=_ICON_DEATH_AND_DECAY,
)

trail_look_206730 = spell(
    id=206730, name='Unholy Ground', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=20000,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=_TARGET_DEST_CASTER,
                    implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, apply_aura=AuraType.DUMMY, radius_yards=3.0)],
    spell_icon_id=_ICON_DEATH_AND_DECAY,
    notes=f'{_HM}, HM3: visual only, the trail\'s rot at a rot stalker\'s feet (300588, S14\'s, one every 5 yd along '
          'the charge, 20 s): TARGET_DEST_CASTER / TARGET_DEST_DYNOBJ_ALLY, the shape of S14\'s 206710 at 3 yd (its '
          'DUMMY aura reaches nobody). Death and Decay 49936\'s SV 9735. The registry line (206729) owns the ticks.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=BR_DEATH_AND_DECAY, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- HM4 the rot heals -----------------------------------------------------------------------------------------------

rot_heal_206731 = spell(
    id=206731, name='Rotting Vigor', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_SCRIPT_EXACT)],
    spell_icon_id=_ICON_DEATH_AND_DECAY,
    notes=f'{_HM}, HM4: the hard mode\'s rot (Death and Decay\'s 45 s and the Deathcharger trail) heals whoever of his '
          'stands in it, once a second: him 1% of his maximum health, each of his undead (the skeletons, Ysida, '
          'Risen) 5% of theirs. The unit casts it on itself (triggered) with the exact amount (CastCustomSpell base '
          'point 0). Ignores the caster\'s modifiers; a healing reduction on the unit (Mortal Strike) cuts it. No '
          'look (one a second per unit).',
    raw_overrides=kit_raw('Drinks the rot.', instant=True, InterruptFlags=0, PreventionType=0,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- Ysida, Risen ----------------------------------------------------------------------------------------------------

death_coil_206732 = _refflat(
    206732, 'Death Coil', School.SHADOW, _DEATH_COIL, _ICON_DEATH_COIL, 'Hurls unholy energy at an enemy.',
    f'{_HM}: Ysida, Risen\'s Death Coil, every 10 s from 4 s on a random player within 30 yd (npc_st_ysida_risen, '
    'triggered): Shadow, 15% of the heroic reference row (gap 22: a starting point), always hits. Death Coil 6789\'s '
    'missile SV 9152 at its speed 24 (no horror: the copy is the damage only).',
    visual=_SV_DEATH_COIL, speed=24.0,
)

risen_strike_206733 = _refflat(
    206733, 'Risen Strike', School.NORMAL, _RISEN_STRIKE, _ICON_STRIKE, 'Strikes an enemy.',
    f'{_HM}: Ysida, Risen\'s swing every 2 s on her victim in melee range (npc_st_ysida_risen; she never auto '
    'attacks): Physical, 3% of the heroic reference row (the tank row on the tank), about 1.5% a second (gap 22: a '
    'starting point). A melee hit (it can miss, be dodged or parried). Strike 11976\'s SV 39.',
    visual=_SV_STRIKE, melee=True,
)

risen_look_206734 = spell(
    id=206734, name='Risen', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_HYSTERIA,
    notes=f'{_HM}: Ysida, Risen\'s lasting look, cast on herself as she rises: Hysteria 49016\'s SV 11514 (the Death '
          'Knight blood frenzy state), so the risen crusader reads as the Scourge\'s. A DUMMY aura, no effect.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=HM_YSIDA_RISEN_AURA, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
