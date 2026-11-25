"""
Ragefire Chasm build WP-D3: Bazzalan (11519), normal and heroic (.agents/plans/ragefire-chasm-build/
ragefire-chasm-build.HANDOFF.md s3.5 row D3, s3.6; build spec docs/dungeons/ragefire-chasm-rework.md "Bazzalan",
BZ1-BZ8). WP-D3 owns this file (its spells: kSpellsBazzalan 213610-213649 of modules/mod-dungeon-bosses
src/RagefireChasm/RagefireChasmRework.h only; BazzalanLogic.h names the same ids).

- 11519 Bazzalan: boss_bazzalan_rework (SmartAI off: WP-S0's rev drops its two rows), the build spec's normal health
  (9,256 = HealthModifier 26 on the level 16 warrior base 356), the stock DamageModifier 2.2 (until T), stun immunity
  1972, INSTANCE_BIND with both assist flags, detection range 12. Heroic health 250,264 is WP-H's override
  (source/world/dungeons/ragefire_chasm.py). He keeps his scimitar (creature_equip_template untouched).
- Sinister Strike 14873 and Deadly Poison 2818 (live rogue rework rows) are retired as his casts: copies here.
- No boss-kit adds, no new creatures. Texts: data/sql/updates/pending_db_world/rev_bazzalan_ragefire_chasm.sql.

Spells. The tank hits and the flat numbers are the C++'s (SetEffectValue at launch, a CalcAmount hook); the bleed takes
the kit's spell_dungeon_refflat_periodic (hundredths of the reference row); the fans are registry hits (resolve copy).
Every damage spell ignores caster modifiers (rule 2):

  213610  Sinister Strike     BZ1 one of his swings + 1, cast triggered
  213611  Combo Points        BZ1 the stacking aura on him, 1 to 5
  213612  Eviscerate          BZ3 the kickable 2 s cast on his target (Physical): 35% / 50% of the tank row
  213613  Rupture             BZ4 the 2 s bar (Shadow, not interruptible)
  213614  Rupture             BZ4 the cut (look only)
  213615  Rupture             BZ4 normal: the 12 s bleed, 40% in all
  213616  Rupture             BZ4 heroic: the bleed to the end of the fight, 2% every 2 s
  213617  Fan of Knives       BZ5 and each BZ7 spin: the 2 s bar (Shadow, not interruptible)
  213618  Fan of Knives       BZ5 35% / BZ7 45% and Weakened (resolve copy, Physical)
  213619  Envenom             BZ6 heroic: the kickable 2 s cast (Nature), 10% of the tank row per Deadly Poison stack
  213620  Shadowstep          BZ7 heroic: the 2 s bar (Shadow, not interruptible)
  213621  Shadowstep          BZ7 the smoke, leaving and landing (look only)
  213622  Deadly Poison       BZ8 the copy of 2818, 5 stacks, 12 s
  213623  Wound Poison        BZ8 heroic: 10% less healing taken per stack, 3 stacks, 15 s
  213624  Crippling Poison    BZ7 heroic: the spin's rider, 50% slower, 8 s
  213625-213649 spare.

Interrupts (handoff s3.5 rule 25, STAGE-G1 finding 1): the kickable casts are Physical and Nature, PreventionType 1 and
InterruptFlags 15; every bar that must play is Shadow (a kick locks the kicked school only), PreventionType 0 and
InterruptFlags 0.

Visual ids are WP-V's (._visuals; every look is unconfirmed until seen in game).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    MECHANIC_SNARE,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BZ_ENVENOM,
    BZ_EVISCERATE,
    BZ_FAN_OF_KNIVES,
    BZ_POISON,
    BZ_POISON_STATE,
    BZ_RUPTURE,
    BZ_RUPTURE_STATE,
    BZ_SHADOWSTEP,
    BZ_SINISTER_STRIKE,
)

_D3 = 'Ragefire Chasm build WP-D3 (Bazzalan)'

creature_template_columns(11519, **boss_columns(
    'boss_bazzalan_rework', 26.0, damage_modifier=2.2,
))

_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_DISPEL_POISON = 4
_INTERRUPT_FLAGS_KICKABLE = 15
_MECHANIC_BLEED = 15
_PREVENTION_SILENCE = 1

_SCRIPT_SWING = 'Ragefire Chasm D3: his own swing (Unit::CalculateDamage), set at launch by the script'
_SCRIPT_TANK = 'Ragefire Chasm D3: a percent of the tank row, set at launch by the script (DungeonKit::RefFlat)'
_SCRIPT_PCT = ('Ragefire Chasm D3: a percent of reference health (hundredths in the value, heroic in '
               'EffectMiscValueB), set by the kit\'s spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')
_SCRIPT_DEADLY = ('Ragefire Chasm D3: 6 a tick per stack on normal (stock), 0.5% of the tank row on heroic, set by '
                  'spell_rfc_bazzalan_deadly_poison')

# Icons of the stock spell each one stands in for (SpellIconID).
_ICON_SINISTER_STRIKE = 130     # Sinister Strike 1752
_ICON_EVISCERATE = 514          # Eviscerate 2098
_ICON_RUPTURE = 500             # Rupture 1943
_ICON_FAN_OF_KNIVES = 2904      # Fan of Knives 51723
_ICON_ENVENOM = 2237            # Envenom 32645
_ICON_SHADOWSTEP = 2363         # Shadowstep 36563
_ICON_DEADLY_POISON = 513       # Deadly Poison 2818
_ICON_WOUND_POISON = 1496       # Wound Poison 13218
_ICON_CRIPPLING_POISON = 163    # Crippling Poison 3409

# RagefireChasmRework.h namespace Bazzalan (lib/test_ragefire_chasm_bazzalan.py pins each one).
COMBO_MAX = 5                   # kComboMax
FINISHER_CAST_MS = 2000         # kFinisherCastMs (and kFanWarnMs, kShadowstepWarnMs)
RUPTURE_TICK_MS = 2000          # kRuptureTickMs
RUPTURE_MS = 12000              # kRuptureNormalMs
RUPTURE_TICK = 667              # kRuptureNormalTotalPct 40 over 6 ticks, hundredths
RUPTURE_HEROIC_TICK = 200       # kRuptureHeroicTickPct 2, hundredths
DEADLY_STACKS = 5               # kDeadlyStacks
DEADLY_MS = 12000               # kDeadlyMs
DEADLY_TICK_MS = 3000           # kDeadlyTickMs
WOUND_PCT = 10                  # kWoundHealingPctPerStack
WOUND_STACKS = 3                # kWoundStacks
WOUND_MS = 15000                # kWoundMs
CRIPPLING_PCT = 50              # kCripplingSlowPct
CRIPPLING_MS = 8000             # kCripplingMs

# Magic class (DmgClass decides, not the school): without these Spell Reflection sends the hit back and a Grounding
# Totem takes it.
_EX1_HIT = ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION
_EX2_HIT = ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT
_EX3_HIT = ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS


def _kickable(spell_id: int, name: str, school: School, *, icon: int, visual: int, desc: str, notes: str, script: str):
    """A real 2 s cast on his target, interruptible and silence-preventable (the whitemane.py recipe): 100 yd, no line
    of sight, always hits, cannot crit, is not reflected or redirected; the script sets the damage at launch."""
    s = spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=FINISHER_CAST_MS, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_TANK)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                              DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=visual, AttributesEx=_EX1_HIT,
                              AttributesEx2=_EX2_HIT, AttributesEx3=_EX3_HIT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )
    scripted_by(s, script)
    return s


def _rupture(spell_id: int, tick: int, duration_ms: int, *, attributes: int, aura_desc: str, notes: str):
    """The bleed: `tick` hundredths of the reference row every 2 s (the tank row on the tank) through the kit's
    spell_dungeon_refflat_periodic. Bleed mechanic: armor does not reduce it."""
    s = spell(
        id=spell_id, name='Rupture', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_BLEED, attributes=attributes,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=tick,
                        die_sides=0, amplitude=RUPTURE_TICK_MS, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                        potency_excluded=_SCRIPT_PCT)],
        spell_icon_id=_ICON_RUPTURE, notes=notes,
        raw_overrides=kit_raw('Cuts the target open.', aura_desc, instant=True, InterruptFlags=0, PreventionType=0,
                              DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=tick, SpellVisualID_1=BZ_RUPTURE_STATE,
                              AttributesEx=_EX1_HIT, AttributesEx2=_EX2_HIT, AttributesEx3=_EX3_HIT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )
    scripted_by(s, 'spell_dungeon_refflat_periodic')
    return s


# --- BZ1 Sinister Strike, combo points -------------------------------------------------------------------------------

sinister_strike_213610 = spell(
    id=213610, name='Sinister Strike', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_SWING)],
    spell_icon_id=_ICON_SINISTER_STRIKE,
    notes=f'{_D3}, BZ1: his own copy of Sinister Strike 14873 (rule 15: 14873 carries a live rogue rework row), cast '
          'by the script (triggered: a kicked Eviscerate locks Physical) on his target at 2 s, then every 3 s (heroic '
          '2 s), in melee range only. One roll of his main-hand damage (Unit::CalculateDamage) + 1, the live row\'s '
          'flat bonus; Physical (armor applies), melee defense (dodge, parry and block apply, as on a swing), cannot '
          'crit. The script adds the combo point with the cast, hit or not. Stock look (V BZ_SINISTER_STRIKE, SV 253).',
    raw_overrides=kit_raw('An instant strike with the caster\'s weapon.', instant=True, InterruptFlags=0,
                          PreventionType=0, DefenseType=_DEFENSE_MELEE, SpellVisualID_1=BZ_SINISTER_STRIKE,
                          AttributesEx2=ATTR2_CANT_CRIT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(sinister_strike_213610, 'spell_rfc_bazzalan_sinister_strike')

combo_points_213611 = spell(
    id=213611, name='Combo Points', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SINISTER_STRIKE,
    notes=f'{_D3}, BZ1: the combo points on him (DungeonKit::AddStacks), one a Sinister Strike, 5 at most; at 5 he '
          'readies a finisher and they are spent when its bar ends, kicked or not. A DUMMY buff with stacks, the '
          'whole read (no look). Not dispellable; removed with his reset, evade and death.',
    raw_overrides=kit_raw('', 'Combo points. At 5 he readies a finisher.', instant=True, CumulativeAura=COMBO_MAX,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- BZ3 Eviscerate --------------------------------------------------------------------------------------------------

eviscerate_213612 = _kickable(
    213612, 'Eviscerate', School.NORMAL, icon=_ICON_EVISCERATE, visual=BZ_EVISCERATE,
    desc='A finishing blow.', script='spell_rfc_bazzalan_eviscerate',
    notes=f'{_D3}, BZ3: the 2 s finisher on his target (emote 1): 35% (heroic 50%) of the tank row, whoever holds him '
          '(spell_rfc_bazzalan_eviscerate, at launch; Physical, so armor applies; no Weakened). Kickable '
          '(InterruptFlags 15, PreventionType silence): the interrupt spends his points for nothing, a reward on '
          'normal, expected on heroic (descriptor priority 2 / 4). The Satyr swing of Eviscerate 2098 (V '
          'SV_EVISCERATE, SV 90373).',
)

# --- BZ4 Rupture -----------------------------------------------------------------------------------------------------

rupture_cast_213613 = cast_bar(
    213613, 'Rupture', FINISHER_CAST_MS, 'Readies a bleeding cut.',
    f'{_D3}, BZ4: the 2 s bar on him (emote 2 names the player). Not interruptible; Shadow, so a kicked Eviscerate or '
    'Envenom never locks it (rule 25). When it ends: the cut (213614) and the bleed on the named player (dead by then: '
    'another one).',
    icon=_ICON_RUPTURE, school=School.SHADOW,
)

rupture_look_213614 = spell(
    id=213614, name='Rupture', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_RUPTURE,
    notes=f'{_D3}, BZ4: look only, cast by him (triggered) on the player as the bar ends: the Satyr swing and Rupture '
          '1943\'s burst of blood on the player (V SV_RUPTURE, SV 90374). A DUMMY with no handler.',
    raw_overrides=kit_raw(instant=True, InterruptFlags=0, PreventionType=0, SpellVisualID_1=BZ_RUPTURE,
                          AttributesEx=_EX1_HIT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

rupture_213615 = _rupture(
    213615, RUPTURE_TICK, RUPTURE_MS, attributes=ATTR0_AURA_IS_DEBUFF,
    aura_desc='Bleeding. Taking Physical damage every $t1 sec.',
    notes=f'{_D3}, BZ4 (normal): 12 s, six ticks of 6.67% (667 hundredths): 40% of the reference row in all, on a '
          'random player, the tank included (its own row). Bleed mechanic (armor does not reduce it), not dispellable, '
          'no Weakened (rule 31): the healer\'s work. The lasting blood state (V BZ_RUPTURE_STATE, SV 15286). Leaving '
          'the map drops it.',
)

rupture_heroic_213616 = _rupture(
    213616, RUPTURE_HEROIC_TICK, -1, attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES,
    aura_desc='Bleeding. Taking Physical damage every $t1 sec until the fight ends.',
    notes=f'{_D3}, BZ4 (heroic): to the end of the fight, 2% (200 hundredths) of the reference row every 2 s, at most '
          'one a player (the pick skips who bleeds). NO_IMMUNITIES: Divine Shield and Ice Block do not shed it (their '
          'ticks are still immune). Removed on his reset, evade and death (the script); leaving the map drops it.',
)

# --- BZ5 and BZ7 Fan of Knives ---------------------------------------------------------------------------------------

fan_cast_213617 = cast_bar(
    213617, 'Fan of Knives', FINISHER_CAST_MS, 'Spins with a fan of knives.',
    f'{_D3}, BZ5 (normal, emote 3) and each BZ7 spin (heroic): the 2 s bar on him while the registry\'s 8 yd (6 yd) '
    'circle shows. Not interruptible; Shadow (rule 25; the hit is Physical). The Satyr spin and the knives of Fan of '
    'Knives 51723 as it completes (V SV_FAN_OF_KNIVES, SV 90376).',
    icon=_ICON_FAN_OF_KNIVES, visual=BZ_FAN_OF_KNIVES, school=School.SHADOW,
)

fan_213618 = resolve_copy(
    213618, 'Fan of Knives', School.NORMAL, 'Cut by a fan of knives.',
    f'{_D3}, BZ5 / BZ7: the hit on everyone inside, the tank included: 35% on normal (tag 8), 45% and the Crippling '
    'Poison rider on heroic (tag 9), plus Weakened, through the registry Zone. Copy of the resolve spell 205001 '
    '(Physical; armor applies).',
    icon=_ICON_FAN_OF_KNIVES,
)

# --- BZ6 Envenom (heroic) --------------------------------------------------------------------------------------------

envenom_213619 = _kickable(
    213619, 'Envenom', School.NATURE, icon=_ICON_ENVENOM, visual=BZ_ENVENOM,
    desc='Consumes the poison on the target.', script='spell_rfc_bazzalan_envenom',
    notes=f'{_D3}, BZ6 (heroic): the 2 s finisher on his target (emote 4): 10% of the tank row per stack of his Deadly '
          'Poison (213622) there as it lands, up to 50%, and consumes them (spell_rfc_bazzalan_envenom); cured, it '
          'lands for nothing. Nature, no Weakened. Kickable, expected (descriptor priority 4). The Satyr swing of '
          'Envenom 32645 (V SV_ENVENOM, SV 90375).',
)

# --- BZ7 Shadowstep (heroic) -----------------------------------------------------------------------------------------

shadowstep_cast_213620 = cast_bar(
    213620, 'Shadowstep', FINISHER_CAST_MS, 'Readies a step through the shadows.',
    f'{_D3}, BZ7 (heroic): the finisher\'s 2 s bar before the three landings (emote 5 names each player as he lands). '
    'Not interruptible; Shadow (rule 25).',
    icon=_ICON_SHADOWSTEP, school=School.SHADOW,
)

shadowstep_look_213621 = self_visual(
    213621, 'Shadowstep', BZ_SHADOWSTEP,
    f'{_D3}, BZ7: the smoke of Shadowstep 36563 (V BZ_SHADOWSTEP, SV 8262; stock plays it only where he leaves), cast '
    'where he leaves and again where he lands.',
    icon=_ICON_SHADOWSTEP, school=School.SHADOW,
)

# --- BZ8 poisons -----------------------------------------------------------------------------------------------------

deadly_poison_213622 = spell(
    id=213622, name='Deadly Poison', school=School.NATURE, dispel=_DISPEL_POISON, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=DEADLY_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=0, die_sides=0,
                    amplitude=DEADLY_TICK_MS, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_DEADLY)],
    spell_icon_id=_ICON_DEADLY_POISON,
    notes=f'{_D3}, BZ8: his own copy of Deadly Poison 2818 at the stock values (rule 15: 2818 carries a live rogue '
          'rework row), cast by him (triggered) on his target on half of his landed swings (2.0 s swings: "50% every 2 '
          's"). Poison, 12 s, a tick every 3 s, stacks to 5: 6 a stack on normal, 0.5% of the tank row a stack on '
          'heroic (spell_rfc_bazzalan_deadly_poison; handoff s7 #35 A). The fuel of Envenom; a cure is the reward. The '
          'lasting green state (V BZ_POISON_STATE, SV 14987).',
    raw_overrides=kit_raw('Poisons the target.', 'Nature damage every $t1 sec.', instant=True, InterruptFlags=0,
                          PreventionType=0, DefenseType=_DEFENSE_MAGIC, CumulativeAura=DEADLY_STACKS,
                          SpellVisualID_1=BZ_POISON_STATE, AttributesEx=_EX1_HIT, AttributesEx2=_EX2_HIT,
                          AttributesEx3=_EX3_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(deadly_poison_213622, 'spell_rfc_bazzalan_deadly_poison')

wound_poison_213623 = spell(
    id=213623, name='Wound Poison', school=School.NATURE, dispel=_DISPEL_POISON, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=WOUND_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_PCT, base_points=-(WOUND_PCT + 1),
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_WOUND_POISON,
    notes=f'{_D3}, BZ8 (heroic): every landed swing on his target adds a stack (3 at most, 15 s): 10% less healing '
          'taken a stack (BasePoints -11 + DieSides 1; the engine multiplies by the stacks). Poison: a cure is the '
          'reward. Deadly Poison 2818\'s splash (V BZ_POISON, SV 5100; Wound Poison 13218 shares it).',
    raw_overrides=kit_raw('Poisons the target.', 'Healing taken reduced by $s1%.', instant=True, InterruptFlags=0,
                          PreventionType=0, DefenseType=_DEFENSE_MAGIC, CumulativeAura=WOUND_STACKS,
                          SpellVisualID_1=BZ_POISON, AttributesEx=_EX1_HIT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

crippling_poison_213624 = spell(
    id=213624, name='Crippling Poison', school=School.NATURE, dispel=_DISPEL_POISON, mechanic=MECHANIC_SNARE,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=CRIPPLING_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED,
                    base_points=-(CRIPPLING_PCT + 1), mechanic=MECHANIC_SNARE,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CRIPPLING_POISON,
    notes=f'{_D3}, BZ7 (heroic): the registry rider of a Shadowstep spin, on everyone it hits: 50% slower for 8 s '
          '(BasePoints -51 + DieSides 1). Poison: a cure is the reward (a slowed player still clears the next 6 yd in '
          '2 s). Crippling Poison 3409 shares Deadly Poison\'s splash (V BZ_POISON, SV 5100).',
    raw_overrides=kit_raw('Slows the target.', 'Movement slowed by $s1%.', instant=True, InterruptFlags=0,
                          PreventionType=0, SpellVisualID_1=BZ_POISON, AttributesEx=_EX1_HIT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
