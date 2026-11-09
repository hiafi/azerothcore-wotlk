"""
Stratholme build WP-S14: Baron Rivendare (10440), normal and heroic
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows BR, s3.5 row S14, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 3842-3906, design ST 3487-3841). WP-S14 owns this file (its spells: kSpellsBaron
206705-206719 of modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; BaronLogic.h names the same ids).
The hard mode (S15, baron_hard_mode.py) adds its own ids 206720-206734 and fights on the same C++ AI (BaronFight.h).

- 10440 Baron Rivendare: boss_baron_rivendare_rework (SmartAI off; WP-S14's SQL rev drops the twenty stock rows and
  the leash's `conditions`), the build spec's normal health (250k: HealthModifier 96.525 on the level 62 paladin class
  base 2,590), his stock immunity set -419 (handoff s7 #3: stun, interrupt and silence immune), INSTANCE_BIND,
  DamageModifier 8 (the stock value). Heroic 300k is WP-H's override (source/world/dungeons/stratholme.py).
- 11197 Mindless Skeleton (stock, his alone: it spawns nowhere else and only he summons it): npc_st_mindless_skeleton
  (SmartAI off; the rev drops its three rows), 6,000 health on normal (HealthModifier 1.8536 on the level 62 warrior
  base 3,237; the stock 357 was 0.11); heroic 7,500 is WP-H's override. Its stock immunity set -122 stays (stuns, roots,
  Shackle Undead and Turn Undead work: crowd control is a reward). No auto attack: the AI strikes with 206711.
- 300588 rot stalker: an invisible, unselectable trigger (KIT_HELPER, the Scholomance Blizzard anchor's shape) that
  carries a rot's look; the registry circle owns the damage. Death and Decay's rot (S14) and the hard mode's
  Deathcharger trail (S15) both use it. No heroic template (not a combat add, handoff s7 #15).

Spells. The rot's ticks deal their damage through a dungeon copy of the mod-boss-mechanics resolve spell (the
registry's percent of the reference row; the combat log names the mechanic). The Unholy Aura pulse and the skeletons'
strike set their damage at launch (DungeonKit::RefFlatOn). The rest are auras and looks:

  206705  Unholy Aura           BR4 the aura on him from the pull: PERIODIC_TRIGGER_SPELL every 2 s (the stock 17467's
                                shape and SV 682)
  206706  Unholy Aura           BR4 the pulse: Shadow on everyone in his fight within 100 yd, 1% / 1.5% of the
                                reference row +0.5% per living servant (spell_strat_baron_unholy_aura_pulse); stock
                                17466's SV 4322
  206707  Raise Dead            BR1 / BR2 the rising look a skeleton casts on itself (Raise Dead 17475's SV 634)
  206708  Death and Decay       BR3 the 3 s mark on the target while the circle follows them
  206709  Death and Decay       BR3 the rot's 1 s tick: resolve copy (Shadow), 4% / 5%
  206710  Death and Decay       BR3 the rot's look on the stalker's spot (Death and Decay 49936's SV 9735, an area aura)
  206711  Mindless Strike       BR1 the skeletons' strike every 2 s: Physical, 2% normal / 2.5% heroic of the reference
                                row (the tank row on the tank), the kit's spell_dungeon_refflat_damage (hundredths)
  206712-206719 spare (206720-206734 are S15's).

The stock tank kit (Shadow Bolt 17393, Mortal Strike 15708, Cleave 15284) is cast by id; DD scales it on heroic.
Death Pact 17471, Raise Dead 17473 / 17475-17480 and Unholy Aura 17467 are retired from him (never cast).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR0_NO_ACTIVE_DEFENSE,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BARON_STOCK,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import BR_DEATH_AND_DECAY, DISPLAY_INVISIBLE_STALKER

creature_template_columns(10440, **boss_columns(
    'boss_baron_rivendare_rework', 96.525, damage_modifier=8, CreatureImmunitiesId=IMMUNITY_BARON_STOCK,
))

# 11197 Mindless Skeleton: 6,000 on normal (3,237 x 1.8536 = 6,000).
creature_template_columns(11197, ScriptName='npc_st_mindless_skeleton', AIName='', HealthModifier=1.8536)

_BR = 'Stratholme build WP-S14 (Baron Rivendare)'
_SCRIPT_EXCLUDED = 'Stratholme: a percent of reference health, set by the script (DungeonKit::RefFlat)'

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_DEST_CASTER = 18
_TARGET_SRC_CASTER = 22
_TARGET_DEST_DYNOBJ_ALLY = 29
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2

_ICON_UNHOLY_AURA = 93             # Unholy Aura 17467
_ICON_RAISE_DEAD = 61              # Raise Dead 17473
_ICON_DEATH_AND_DECAY = 118        # Death and Decay 49936
_ICON_STRIKE = 856                 # Strike 11976
_SV_UNHOLY_AURA = 682              # Unholy Aura 17467 (the aura on him)
_SV_UNHOLY_PULSE = 4322            # Unholy Aura 17466 (the pulse's hit)
_SV_RAISE_DEAD = 634               # Raise Dead 17475 (the summon's rising)
_SV_STRIKE = 39                    # Strike 11976 (the swing)

# The pulse's percent is set by its script from the living servants, so the effect's value is only a tooltip floor;
# the strike's is read by the kit's spell_dungeon_refflat_damage (hundredths of the shown value; heroic MiscValueB).
_STRIKE_NORMAL_HUNDREDTHS = 200    # BaronLogic.h kSkeletonStrikePct.normal (2%)
_STRIKE_HEROIC_HUNDREDTHS = 250    # kSkeletonStrikePct.heroic (2.5%)

# --- 300588 rot stalker ----------------------------------------------------------------------------------------------
rot_stalker_300588 = creature_template(
    300588, 'Rotting Ground', **{**KIT_HELPER, 'minlevel': 62, 'maxlevel': 62, 'rank': 0, 'unit_class': 1,
                                 'type': 10, 'flags_extra': 0x40 | 0x80, 'ScriptName': ''},
)
creature_model(300588, display_id=DISPLAY_INVISIBLE_STALKER)

# --- BR4 Unholy Aura -------------------------------------------------------------------------------------------------

unholy_aura_206705 = spell(
    id=206705, name='Unholy Aura', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=2000,
                    trigger_spell=206706, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_UNHOLY_AURA,
    notes=f'{_BR}, BR4: the stock Unholy Aura 17467 reworked (never the stock id): an aura he casts on himself at the '
          'pull (removed on his death, evade and reset) that triggers the pulse 206706 every 2 s, the stock shape '
          '(PERIODIC_TRIGGER_SPELL). The stock 17467\'s SV 682 (the dark aura on him).',
    raw_overrides=kit_raw('Unholy energy pulses from the caster.', 'Unholy energy pulses from you every $t1 sec.',
                          instant=True, SpellVisualID_1=_SV_UNHOLY_AURA, AttributesEx4=ATTR4_NO_CAST_LOG),
)

unholy_pulse_206706 = spell(
    id=206706, name='Unholy Aura', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, implicit_target_a=_TARGET_SRC_CASTER,
                    implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                    potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_UNHOLY_AURA,
    notes=f'{_BR}, BR4: the 2 s pulse (ruling 56: 100 yd, the stock 30 yd did not reach across the room): Shadow on '
          'every enemy in combat with him within 100 yd (spell_strat_baron_unholy_aura_pulse filters the area targets '
          'to his fight and sets the damage at launch: 1% normal / 1.5% heroic of the reference row +0.5% per living '
          'servant, RefFlatOn, so the tank takes the tank row). Not avoidable: the resolve spell\'s attribute set '
          '(always hits, ignores line of sight and caster modifiers, cannot crit, no threat). The stock 17466\'s SV '
          '4322 (the shadow hit).',
    raw_overrides=kit_raw('Inflicts Shadow damage to nearby enemies.', instant=True,
                          SpellVisualID_1=_SV_UNHOLY_PULSE, DefenseType=_DEFENSE_MAGIC,
                          Attributes=ATTR0_NO_ACTIVE_DEFENSE,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(unholy_pulse_206706, 'spell_strat_baron_unholy_aura_pulse')

# --- BR1 / BR2 the rising --------------------------------------------------------------------------------------------

rise_206707 = self_visual(
    206707, 'Raise Dead', _SV_RAISE_DEAD,
    f'{_BR}, BR1 / BR2: the look a Mindless Skeleton casts on itself as it rises (a Raise Dead wave at a wall, or a '
    'bone pile raised by a heroic rot). Raise Dead 17475\'s SV 634; the stock summon spells are never cast.',
    icon=_ICON_RAISE_DEAD, school=School.SHADOW,
)

# --- BR3 Death and Decay ---------------------------------------------------------------------------------------------

death_and_decay_206708 = spell(
    id=206708, name='Death and Decay', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=3000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_DEATH_AND_DECAY,
    notes=f'{_BR}, BR3: the 3 s mark on a random non-tank, cast by him (triggered) with emote line 10, while the '
          'registry circle (6 yd, DungeonKit::FollowThenLand) follows them; where they stand at its end the ground '
          'rots (300588 with 206710, the registry zone with 206709). Dispel none. No look of its own (the marker is '
          'the telegraph).',
    raw_overrides=kit_raw('Marks the ground beneath you for rot.', 'The ground will rot where you stand. Carry it '
                          'away from your allies.', CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

rot_206709 = resolve_copy(
    206709, 'Death and Decay', School.SHADOW, 'Rotting ground.',
    f'{_BR}, BR3: the rot\'s 1 s tick on everyone inside its 6 yd circle: 4% normal / 5% heroic of the non-tank row, '
    'one Weakened per player per rot (WeakenedOncePerPlayer), the first tick one second after the landing (the '
    'grace). Copy of the resolve spell 205001 (Shadow). No visual (a tick every second; 206710 is the look). The '
    'hard mode (S15) makes Death and Decay last 45 s.',
    icon=_ICON_DEATH_AND_DECAY,
)

rot_look_206710 = spell(
    id=206710, name='Death and Decay', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=45000,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=_TARGET_DEST_CASTER,
                    implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, apply_aura=AuraType.DUMMY, radius_yards=6.0)],
    spell_icon_id=_ICON_DEATH_AND_DECAY,
    notes=f'{_BR}, BR3: visual only, the rot at the rot stalker\'s feet (TARGET_DEST_CASTER / '
          'TARGET_DEST_DYNOBJ_ALLY, the Scholomance Blizzard look\'s shape: its DUMMY aura reaches nobody). 45 s, the '
          'longest rot (the hard mode\'s); a shorter rot\'s stalker despawns with its area (10 s normal, 15 s heroic). '
          'Death and Decay 49936\'s SV 9735 (the rune quad, scaled by the 6 yd radius; VISUALS-REPORT: unconfirmed '
          'whether the client stretches it). The registry circle (206709) owns the ticks.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=BR_DEATH_AND_DECAY, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- BR1 the skeletons' strike ---------------------------------------------------------------------------------------

skeleton_strike_206711 = spell(
    id=206711, name='Mindless Strike', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_STRIKE_NORMAL_HUNDREDTHS - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_STRIKE,
    notes=f'{_BR}, BR1: a Mindless Skeleton\'s swing (npc_st_mindless_skeleton strikes its victim in melee range every '
          '2 s and never auto attacks): Physical, 2% normal / 2.5% heroic of the reference row (the tank row on the '
          'tank): about 1% / 1.25% a second, the build spec\'s number on both difficulties. The kit\'s '
          'spell_dungeon_refflat_damage reads the percent in hundredths (shown value 200; EffectMiscValueB 250 on '
          'heroic). A melee hit (DefenseType melee: it can miss, be dodged or parried), ignores caster modifiers, '
          'cannot crit. Strike 11976\'s SV 39 and icon.',
    raw_overrides=kit_raw('Strikes an enemy.', instant=True, DefenseType=_DEFENSE_MELEE, SpellVisualID_1=_SV_STRIKE,
                          EffectMiscValueB_1=_STRIKE_HEROIC_HUNDREDTHS, AttributesEx2=ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(skeleton_strike_206711, 'spell_dungeon_refflat_damage')
