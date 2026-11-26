"""
Zul'Farrak build WP-D5: Sergeant Bly's crew as a boss (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5
row D5, s3.6, s7 #12-#19, #49; build spec docs/dungeons/zul-farrak-rework.md "Sergeant Bly's crew", BC1-BC13,
rulings 24, 26-30, 46). WP-D5 owns this file (its spells: kSpellsCrewFight 214030-214069 of modules/mod-dungeon-bosses
src/ZulFarrak/ZulFarrakRework.h only; CrewFightLogic.h names the same ids and holds every number). The crew's scripts
are bound by rev_skeleton_zul_farrak.sql (S0), their type_flags and texts are rev_crew_zul_farrak.sql (CR), the stash
chest's gameobject_template rows (301360 normal, 301361 heroic) rev_bly_crew_fight_zul_farrak.sql (D5) and its loot
rev_loot_zul_farrak.sql (L-1). The crew's AI is CR's; D5's handler only fights on it.

The crew's fight columns (the Build spec "Encounter" table; s3.6 normal health x1.6, s7 #1 A): the normal health of
ZulFarrakRework.h Health (Bly 63,941 = 34.6 x warrior 1,848 at 45; Raven 39,917 = 22.4 x 1,782; Oro 40,029 = 32.1 x
mage 1,247; Murta 40,071 = 28.1 x paladin 1,426), Bly's stun immunity set 1972 (stock -325, ruling 29), and
CREATURE_FLAG_EXTRA_ALL_DIMINISH on Raven, Oro and Murta (crowd control works on them under player diminishing returns,
ruling 29; immunity set 0 kept). DamageModifier, faction, flags and loot ids stay as they are (the faction is CR's by
mode; the bodies carry no loot: L-1 empties their tables). Weegli 7607 is not in the fight: no column here. Heroic
health is WP-H's override (source/world/dungeons/zul_farrak.py `_crew`).

Spells. The registry's hits are dungeon copies of the mod-boss-mechanics resolve spell; the split strike and the Seed's
burst take the script's base point (DungeonKit::SplitShares, RefFlatOn); every damage spell ignores the caster's
modifiers (rule 2), so Avenge raises the crew's melee and stock casts, never the mechanics:

  214030  Gang Up               BC1 the mark on the called player (Hunter's Mark 1130's SV 3239), until the strike
  214031  Gang Up               BC1 one share of the split strike (Physical, the script's base point)
  214032  Guarded               BC2 on the crew member Bly guards, 8 s (the kill order's LacksAura); SV 8024
  214033  Intervene             BC2 Bly's charge look on the guarded (Intervene 3411's SV 9107)
  214034  Spell Reflection      BC3 heroic: on the guarded, reflects the next spell (one charge, 8 s); SV 7962
  214035  Vanish                BC4 Raven's vanish look (Vanish 1856's SV 255)
  214036  Ambush                BC4 the 3 yd circle's strike: resolve copy, Physical (Shadowstep 36563's SV 8262)
  214037  Gouge                 BC6 a 2 s incapacitate (copy of 12540's shape; breaks on damage); SV 256
  214038  Kidney Shot           BC5 heroic Set Up: a 2 s stun on an Ambush hit (Kidney Shot 408's SV 679)
  214039  Wound Poison          BC5 heroic Set Up: 50% less healing taken for 15 s, Poison (SV 5100)
  214040  Rain of Fire          BC8 the fire falling on the spot for 10.5 s (Rain of Fire 11990's SV 10379, look only)
  214041  Rain of Fire          BC8 a 3 s tick: resolve copy, Fire
  214042  Seed of Corruption    BC9 heroic: the Magic debuff on its carrier, 6.5 s (the script bursts it at 6 s)
  214043  Seed of Corruption    BC9 heroic: the burst on everyone within 10 yd (Shadow, the script's base point)
  214044  Greater Heal          BC7 normal: Murta's 3 s kickable heal (Holy), the script's amount (25%)
  214045  Greater Heal          BC7 heroic: the 2 s heal (50%)
  214046  Resurrection          BC12 heroic: Murta's 8 s kickable cast (Holy); the script raises its target at 50%
  214047  Soulstone             BC12 heroic: Oro's stone on Murta (Soulstone Resurrection 20707's SV 99)
  214048  Avenge                BC13 heroic: 20% damage and haste a stack, no cap (Bloodlust 2825's SV 7870)
  214049  Wound Poison          BC5 heroic: the poison's lasting look (hidden, SV 14987), removed with the poison
  214050-214069 spare.

Retired from the crew's kit in Boss mode (CR's ally kit keeps them): Heal 11642 (replaced by Greater Heal), Gouge 12540
and Rain of Fire 11990 as cast. Kept as cast: Shield Bash 11972, Revenge 12170, Backstab 7159, Shadow Bolt 9613,
Immolate 11962, Curse of Weakness 12741, Holy Smite 9734, Renew 11640, Power Word: Shield 11974. Murta's kickable casts
are all Holy (a kick on one locks the others: a reward, s3.5 kick table); nothing that must land is a non-triggered
cast.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    RESOLVE_RAW,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BC_AVENGE,
    BC_GOUGE,
    BC_GREATER_HEAL,
    BC_GUARDED,
    BC_INTERVENE,
    BC_KIDNEY,
    BC_MARK,
    BC_POISON,
    BC_POISON_STATE,
    BC_REFLECT,
    BC_RES,
    BC_ROF,
    BC_SEED,
    BC_SEED_BURST,
    BC_SHADOWSTEP,
    BC_SOULSTONE,
    BC_VANISH,
)

_D5 = "Zul'Farrak build WP-D5 (Sergeant Bly's crew)"

# --- constants (CrewFightLogic.h; lib/test_zul_farrak_bly_crew_fight.py pins each against the header) ----------------

GUARDED_MS = 8000                   # Tune::kGuardedMs
GOUGE_MS = 2000                     # Tune::kGougeMs
KIDNEY_SHOT_MS = 2000               # Tune::kKidneyShotMs
WOUND_POISON_MS = 15000             # Tune::kWoundPoisonMs
WOUND_POISON_HEALING_PCT = 50       # Tune::kWoundPoisonHealingPct
RAIN_LOOK_MS = 10500                # Tune::kRainWarnMs + Tune::kRainMs
RAIN_RADIUS_YD = 8.0                # Tune::kRainRadiusYd
SEED_AURA_MS = 6500                 # Tune::kSeedAuraMs
GREATER_HEAL_CAST_MS = (3000, 2000)  # Tune::kGreaterHealCastMs
RESURRECTION_CAST_MS = 8000         # Tune::kResurrectionCastMs
AVENGE_PCT = 20                     # Tune::kAvengePctPerStack
AVENGE_MAX_STACKS = 255             # no cap (SP ruling 46): out of reach in a fight
MARK_MS = 5000                      # outlasts Gang Up's 4 s warning; the script removes it at the strike

# The crew's normal health (s3.6, s7 #1 A): ZulFarrakRework.h Health is the engine's ceil(base x HealthModifier).
HEALTH_MODIFIER = {7604: 34.6, 7605: 22.4, 7606: 32.1, 7608: 28.1}
FLAGS_EXTRA_ALL_DIMINISH = 0x00100000   # CREATURE_FLAG_EXTRA_ALL_DIMINISH (ruling 29)

_SCRIPT_BP = ("Zul'Farrak Bly's crew: the script's base point (a percent of reference health: DungeonKit::SplitShares "
              'for the Gang Up shares, DungeonKit::RefFlatOn for the Seed burst)')
_SCRIPT_HEAL = "Zul'Farrak Bly's crew: the script's exact amount (a percent of the target's health)"

_TARGET_DEST_DEST = 87
_TARGET_DEST_DYNOBJ_ALLY = 29
_TARGET_FLAG_DEST_LOCATION = 0x40
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_DISPEL_MAGIC = 1
_DISPEL_POISON = 4
_MECHANIC_STUN = 12
_MECHANIC_KNOCKOUT = 14             # Gouge 12540's (an incapacitate)
_PREVENTION_SILENCE = 1
_PREVENTION_PACIFY = 2
_INTERRUPT_FLAGS_KICKABLE = 15
_AURA_INTERRUPT_TAKE_DAMAGE = 0x00000002
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
_AURA_REFLECT_SPELLS = 28           # SPELL_AURA_REFLECT_SPELLS (Spell Reflection 23920's)
_PROC_TAKEN_SPELL_MAGIC_NEG = 0x000222A0    # Spell Reflection 23920's ProcTypeMask (its auto proc: reflects only)
_SCHOOL_MASK_ALL = 127

# Stock icons (Spell.dbc SpellIconID of the named spell, read from the stock DBC 2026-11-25)
_ICON_HUNTERS_MARK = 538
_ICON_INTERVENE = 2205
_ICON_SHIELD_WALL = 281
_ICON_SPELL_REFLECTION = 1935
_ICON_VANISH = 252
_ICON_SHADOWSTEP = 2363
_ICON_GOUGE = 245
_ICON_KIDNEY_SHOT = 499
_ICON_WOUND_POISON = 1496
_ICON_RAIN_OF_FIRE = 547
_ICON_SEED = 1932
_ICON_GREATER_HEAL = 241
_ICON_RESURRECTION = 121
_ICON_SOULSTONE = 92
_ICON_BLOODLUST = 38

# --- the crew's fight columns ----------------------------------------------------------------------------------------

creature_template_columns(7604, HealthModifier=HEALTH_MODIFIER[7604], CreatureImmunitiesId=IMMUNITY_BOSS_STUN)
creature_template_columns(7605, HealthModifier=HEALTH_MODIFIER[7605], flags_extra=FLAGS_EXTRA_ALL_DIMINISH)
creature_template_columns(7606, HealthModifier=HEALTH_MODIFIER[7606], flags_extra=FLAGS_EXTRA_ALL_DIMINISH)
creature_template_columns(7608, HealthModifier=HEALTH_MODIFIER[7608], flags_extra=FLAGS_EXTRA_ALL_DIMINISH)


# --- helpers ---------------------------------------------------------------------------------------------------------

def _aura(*, spell_id: int, name: str, visual: int, icon: int, duration_ms: int, notes: str, desc: str = '',
          aura_desc: str = '', debuff: bool = False, hidden: bool = False, dispel: int = 0,
          school: School = School.NORMAL, target: int = TARGET_UNIT_TARGET_ANY, **raw):
    """A DUMMY aura that carries a look (the script reads it, or nothing does), cast triggered."""
    attributes = (ATTR0_AURA_IS_DEBUFF if debuff else 0) | (ATTR0_DO_NOT_DISPLAY if hidden else 0)
    return spell(
        id=spell_id, name=name, school=school, dispel=dispel, mechanic=0, attributes=attributes, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=(RANGE_SELF if target == TARGET_UNIT_CASTER else 100.0), duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=target)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, **raw),
    )


def _script_hit(*, spell_id: int, name: str, school: School, visual: int, icon: int, desc: str, notes: str):
    """A hit of the script's exact base point on one target (DieSides 0), the resolve attribute set."""
    raw = kit_raw(desc, **RESOLVE_RAW)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=school, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_BP)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _stun(*, spell_id: int, name: str, mechanic: int, duration_ms: int, visual: int, icon: int, breaks: bool,
          aura_desc: str, notes: str):
    """A stun (MOD_STUN) on an enemy, cast by Raven: Gouge breaks on damage, Kidney Shot does not."""
    raw = kit_raw('', aura_desc, instant=True, SpellVisualID_1=visual, PreventionType=_PREVENTION_PACIFY,
                  DefenseType=_DEFENSE_MELEE, AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                  AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                  AuraInterruptFlags=(_AURA_INTERRUPT_TAKE_DAMAGE if breaks else 0) | _AURA_INTERRUPT_CHANGE_MAP)
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=mechanic, attributes=ATTR0_AURA_IS_DEBUFF,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0, die_sides=0,
                        mechanic=mechanic, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _greater_heal(spell_id: int, cast_ms: int, notes: str):
    """BC7: Murta's Greater Heal, a real kickable cast (InterruptFlags 15, silence; Holy) on a crew member, the script's
    exact amount (base point 0). Keeps her swing timer."""
    return spell(
        id=spell_id, name='Greater Heal', school=School.HOLY, cast_time_ms=cast_ms, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                        potency_excluded=_SCRIPT_HEAL)],
        spell_icon_id=_ICON_GREATER_HEAL, notes=notes,
        raw_overrides=kit_raw('Heals a friendly target.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                              PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                              SpellVisualID_1=BC_GREATER_HEAL, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                              AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
    )


# --- BC1 Gang Up -----------------------------------------------------------------------------------------------------

gang_up_mark_214030 = _aura(
    spell_id=214030, name='Gang Up', visual=BC_MARK, icon=_ICON_HUNTERS_MARK, duration_ms=MARK_MS, debuff=True,
    desc='Marked for the crew.', aura_desc='The whole crew is coming for you. Get help!',
    notes=f'{_D5}, BC1: the mark on the called player (Bly, triggered, with his yell "Get $n, lads!"), the tank '
          'included: Raven, Oro and Murta turn on the mark for 6 s; at 4 s (heroic Set Up: 2 s) the strike is split '
          'among everyone within 6 yd (a registry Stack anchored on the mark, tag 17). The script removes it at the '
          'strike. Not dispellable. Hunter\'s Mark 1130\'s SV 3239.',
)

gang_up_share_214031 = _script_hit(
    spell_id=214031, name='Gang Up', school=School.NORMAL, visual=0, icon=_ICON_HUNTERS_MARK,
    desc='The crew strike together.',
    notes=f'{_D5}, BC1: one share of the strike, cast by Bly (triggered) on everyone inside the stack: 60% (heroic '
          'Focus Fire 90%, then 15% more each call, no cap) of the reference non-tank row split evenly (the base '
          'point; DieSides 0: exact). Three or more: 20% each on normal; a mark left alone takes it all. A stack: no '
          'Weakened. The resolve attribute set.',
)

# --- BC2 Bodyguard, BC3 Spell Reflection -----------------------------------------------------------------------------

guarded_214032 = _aura(
    spell_id=214032, name='Guarded', visual=BC_GUARDED, icon=_ICON_SHIELD_WALL, duration_ms=GUARDED_MS,
    desc='Bly guards a crew member.', aura_desc='Guarded by Sergeant Bly: 75% less damage taken while he stands close.',
    notes=f'{_D5}, BC2: on the crew member at the lowest health percent (Raven, Oro or Murta; never Bly), cast by Bly '
          '(triggered) every 15 s (heroic 12 s) for 8 s. No effect of its own: while Bly stands within 5 yd the '
          'script cuts the guarded\'s damage taken by 75% and deals Bly a third of what was blocked. The bots\' kill '
          'order skips a unit with it (LacksAura). Removed early when a taunt lands on Bly, either of them goes out, '
          'or the fight ends. SV 8024 (V: no standing Shield Wall look exists; 345 is a one-shot).',
)

intervene_214033 = _aura(
    spell_id=214033, name='Intervene', visual=BC_INTERVENE, icon=_ICON_INTERVENE, duration_ms=0, hidden=True,
    notes=f'{_D5}, BC2: Bly\'s charge look on the guarded (triggered) as he runs to it; the script moves him (follow). '
          'Intervene 3411\'s SV 9107. Look only.',
)

spell_reflection_214034 = spell(
    id=214034, name='Spell Reflection', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=GUARDED_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_REFLECT_SPELLS, base_points=99, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SPELL_REFLECTION,
    notes=f'{_D5}, BC3 heroic: with Guarded, cast by Bly (triggered) on the guarded: the next spell cast on it returns '
          'to its caster (REFLECT_SPELLS 100%, one charge: Spell Reflection 23920\'s ProcTypeMask, chance and charges; '
          'the engine\'s automatic proc entry procs a reflect aura on reflects only). 8 s; removed with the guard. '
          'SV 7962.',
    raw_overrides=kit_raw('Reflects the next spell cast on the guarded.', 'Reflects the next spell cast on you.',
                          instant=True, SpellVisualID_1=BC_REFLECT, ProcTypeMask=_PROC_TAKEN_SPELL_MAGIC_NEG,
                          ProcChance=100, ProcCharges=1, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- BC4 Ambush, BC5 Set Up, BC6 Gouge -------------------------------------------------------------------------------

vanish_214035 = self_visual(
    214035, 'Vanish', BC_VANISH,
    f'{_D5}, BC4: Raven\'s vanish (cast on herself, triggered) as the Ambush circle appears; the script hides her '
    'until she steps into it. Vanish 1856\'s SV 255. Look only.',
    icon=_ICON_VANISH,
)

ambush_214036 = resolve_copy(
    214036, 'Ambush', School.NORMAL, 'Raven steps out of the shadows and strikes.',
    f'{_D5}, BC4: the 3 yd circle under a random player (the tank included), 2 s (heroic 1.5 s): 40% of the reference '
    'row (the tank row on the tank) and 1 Weakened on both difficulties; Raven teleports into it and stays on that '
    'player (registry Zone, tag 18). Copy of the resolve spell 205001 (Physical); Shadowstep 36563\'s SV 8262.',
    icon=_ICON_SHADOWSTEP, visual=BC_SHADOWSTEP,
)

gouge_214037 = _stun(
    spell_id=214037, name='Gouge', mechanic=_MECHANIC_KNOCKOUT, duration_ms=GOUGE_MS, visual=BC_GOUGE,
    icon=_ICON_GOUGE, breaks=True, aura_desc='Incapacitated.',
    notes=f'{_D5}, BC6: Raven\'s 2 s Gouge (stock 12540 is 4 s: the 2 s loss-of-control cap), on a random player '
          'within 5 yd (the tank included), else her victim; first at 6 s, every 11 to 23 s. An incapacitate (mechanic '
          '14) that breaks on damage. No damage (the stock 20 is cut). Gouge\'s SV 256.',
)

kidney_shot_214038 = _stun(
    spell_id=214038, name='Kidney Shot', mechanic=_MECHANIC_STUN, duration_ms=KIDNEY_SHOT_MS, visual=BC_KIDNEY,
    icon=_ICON_KIDNEY_SHOT, breaks=False, aura_desc='Stunned.',
    notes=f'{_D5}, BC5 heroic Set Up: on every player the Ambush hit (Raven, triggered), a 2 s stun; Bly calls a Gang '
          'Up on the first, struck 2 s later. Kidney Shot 408\'s SV 679.',
)

wound_poison_214039 = spell(
    id=214039, name='Wound Poison', school=School.NATURE, dispel=_DISPEL_POISON, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=WOUND_POISON_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_PCT,
                    base_points=-(WOUND_POISON_HEALING_PCT + 1), die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Wound Poison: a flat 50% less healing taken, not a damage or heal value')],
    spell_icon_id=_ICON_WOUND_POISON,
    notes=f'{_D5}, BC5 heroic Set Up: on every player the Ambush hit (Raven, triggered): 50% less healing taken for '
          '15 s. A Poison: a cure is the reward (the bots\' dispel list). Wound Poison 13218\'s SV 5100 (a one-shot; '
          '214049 is the lasting look).',
    raw_overrides=kit_raw('Healing taken reduced.', 'Healing taken reduced by $s1%.', instant=True,
                          SpellVisualID_1=BC_POISON, DefenseType=_DEFENSE_MAGIC,
                          AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

wound_poison_look_214049 = _aura(
    spell_id=214049, name='Wound Poison', visual=BC_POISON_STATE, icon=_ICON_WOUND_POISON,
    duration_ms=WOUND_POISON_MS, hidden=True, school=School.NATURE,
    notes=f'{_D5}, BC5 heroic: the poison\'s lasting look on the poisoned player (Raven, triggered), removed by the '
          'script as soon as the poison is gone (a cure). Hidden, not dispellable, no effect. SV 14987.',
)

# --- BC8 Rain of Fire ------------------------------------------------------------------------------------------------

rain_look_214040 = spell(
    id=214040, name='Rain of Fire', school=School.FIRE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=RAIN_LOOK_MS,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=_TARGET_DEST_DEST,
                    implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, apply_aura=AuraType.DUMMY,
                    radius_yards=RAIN_RADIUS_YD)],
    spell_icon_id=_ICON_RAIN_OF_FIRE,
    notes=f'{_D5}, BC8: the fire falling on the 8 yd circle for its 1.5 s warning and 9 s of ticks, cast by Oro '
          '(triggered) at the spot. TARGET_DEST_DEST / TARGET_DEST_DYNOBJ_ALLY with a DUMMY aura (it reaches nobody); '
          'the registry Zone deals the ticks (214041). Rain of Fire 11990\'s SV 10379 (its persistent area kit, effect '
          '27, as V names it). Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=BC_ROF, Targets=_TARGET_FLAG_DEST_LOCATION,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

rain_of_fire_214041 = resolve_copy(
    214041, 'Rain of Fire', School.FIRE, 'Fire rains down on the area.',
    f'{_D5}, BC8: a tick of Oro\'s Rain of Fire, an 8 yd circle under a random player within 30 yd (the tank '
    'included): 1.5 s warning, then every 3 s for 9 s, 6% (heroic 8%) of the reference row (the tank row on the tank). '
    'A lingering patch: no Weakened (registry Zone, Persistent, tag 19). Copy of the resolve spell 205001 (Fire).',
    icon=_ICON_RAIN_OF_FIRE,
)

# --- BC9 Seed of Corruption ------------------------------------------------------------------------------------------

seed_214042 = _aura(
    spell_id=214042, name='Seed of Corruption', visual=BC_SEED, icon=_ICON_SEED, duration_ms=SEED_AURA_MS,
    debuff=True, dispel=_DISPEL_MAGIC, school=School.SHADOW,
    desc='A seed of corruption grows inside the target.',
    aura_desc='Bursts in 6 sec. for Shadow damage to you and everyone within 10 yards unless dispelled.',
    notes=f'{_D5}, BC9 heroic: Oro (triggered) on a random player (the tank included) every 20 s from 10 s: Magic, '
          'the dispel list\'s answer, with a registry RunOut 10 yd on the carrier (tag 16, telegraph only). '
          'Undispelled at 6 s the script bursts it (214043) and removes it; 6.5 s so it never ends first. Seed of '
          'Corruption 27243\'s SV 8339.',
)

seed_burst_214043 = _script_hit(
    spell_id=214043, name='Seed of Corruption', school=School.SHADOW, visual=BC_SEED_BURST, icon=_ICON_SEED,
    desc='The seed bursts.',
    notes=f'{_D5}, BC9 heroic: the burst, cast by Oro (triggered) on the carrier and everyone within 10 yd of it: 35% '
          'of the reference row each (the tank row on a tank; DungeonKit::RefFlatOn, the base point). No Weakened (a '
          'missed dispel is its own penalty). SV 7180.',
)

# --- BC7 Greater Heal, BC12 No One Left Behind -----------------------------------------------------------------------

greater_heal_214044 = _greater_heal(
    214044, GREATER_HEAL_CAST_MS[0],
    f'{_D5}, BC7 normal: when a crew member is under 50%, at most once every 15 s, Murta casts it on the lowest: a 3 s '
    'kickable Holy cast healing 25% of the target\'s health (the script sets the amount at the cast\'s start). The '
    'fight\'s interrupt (descriptor priority 3). A kick locks her Holy school: Smite and Resurrection too, a reward. '
    'Greater Heal 2060\'s SV 57.')

greater_heal_h_214045 = _greater_heal(
    214045, GREATER_HEAL_CAST_MS[1],
    f'{_D5}, BC7 heroic: as 214044 with a 2 s cast, at most once every 12 s, healing 50%.')

resurrection_214046 = spell(
    id=214046, name='Resurrection', school=School.HOLY, cast_time_ms=RESURRECTION_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_RESURRECTION,
    notes=f'{_D5}, BC12 heroic: Murta\'s 8 s kickable Holy cast on the crew member out longest (a held body on the '
          'betrayal, a yielded member on the Test), never straight after a Greater Heal; when it lands the target\'s '
          'script raises it at 50% health (Avenge still counts the fall). Descriptor interrupt priority 4. A DUMMY on '
          'any unit: the held body is not attackable and the yielded member friendly. Resurrection 2006\'s SV 41.',
    raw_overrides=kit_raw('Brings a fallen ally back to fight.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=BC_RES,
                          AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_DO_NOT_RESET_COMBAT_TIMERS),
)

soulstone_214047 = _aura(
    spell_id=214047, name='Soulstone Resurrection', visual=BC_SOULSTONE, icon=_ICON_SOULSTONE, duration_ms=-1,
    school=School.SHADOW, desc='Stores the soul of the target.',
    aura_desc='Soul stored: rises 10 sec. after falling while Oro stands.',
    notes=f'{_D5}, BC12 heroic: Oro\'s stone on Murta (triggered) from the pull: 10 s after she falls (or yields) the '
          'script raises her at 50% unless Oro is out by then; then gone, and Oro puts a new one on her 20 s later. '
          'Not dispellable (no Dispel), shown on her buff bar. Soulstone Resurrection 20707\'s SV 99 (a one-shot glow: '
          'no standing look exists).',
)

avenge_214048 = spell(
    id=214048, name='Avenge', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=AVENGE_PCT,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Avenge: a flat 20% more damage done a stack, not a damage or heal value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=AVENGE_PCT,
                    die_sides=0, implicit_target_a=TARGET_UNIT_CASTER),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK,
                    base_points=AVENGE_PCT, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BLOODLUST,
    notes=f'{_D5}, BC13 heroic: each time a crew member falls, dies or yields, every crew member still fighting gains '
          'a stack for the rest of the fight (DungeonKit::AddStacks on itself; a raised member gets the count): 20% '
          'more damage done, 20% faster attacks and casts a stack (the engine multiplies by the stacks), no cap (255 '
          'is out of reach). The crew\'s mechanics ignore caster modifiers, so it raises their melee and stock casts. '
          'Removed at the fight\'s end, a wipe or a death. Bloodlust 2825\'s SV 7870.',
    raw_overrides=kit_raw('Fighting harder for the fallen.', 'Fighting harder for the fallen.', instant=True,
                          CumulativeAura=AVENGE_MAX_STACKS, SpellVisualID_1=BC_AVENGE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_CANT_CRIT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
