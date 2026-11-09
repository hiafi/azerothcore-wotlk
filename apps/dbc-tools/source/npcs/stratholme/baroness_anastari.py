"""
Stratholme build WP-S10: Baroness Anastari (10436), normal and heroic
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows BA, s3.5 row S10, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 2630-2677, design ST 2411-2629). WP-S10 owns this file (its spells:
kSpellsBaroness 206625-206644 of modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; BaronessLogic.h
names the same ids).

- 10436 Baroness Anastari: boss_baroness_anastari_rework (SmartAI was already off; the stock C++ boss_baroness_anastari
  stays registered and is unbound by this edit), the build spec's normal health (170k: HealthModifier 71.76 on the level
  59 paladin class base 2,369), DamageModifier 3.5 (the stock value: base SQL and the 2026_09_27_06 sniff update; the
  live 7.25 is a mod-progression leftover), stun immunity 1972 (ST says -273, handoff s7 #3 rules 1972: stun immune,
  interrupts and silences not), INSTANCE_BIND (flags_extra 1). Heroic 220k is WP-H's override
  (source/world/dungeons/stratholme.py). No boss-kit units (ST: no adds, no stalkers).
- Retired with the possession loop: Banshee Curse 16867, Silence 18327, Possess 17244, Possessed 17246, Possess 17250.
  Kept: Banshee Wail 16565 on the tank (DD scales it on heroic).

Spells. The Wail, its heroic echo and the Visage cone deal their damage through dungeon copies of the mod-boss-mechanics
resolve spell (the registry's percent of the reference row; the combat log names the mechanic); the Death Knell is a
script spell whose base point 0 is a share the script computes (DungeonKit::WeightedShares). The rest is cast bars,
debuffs and the Lament:

  206625  Keened             BA1 the doomed player's debuff, 6 s (heroic 5 s, set by the script): the skull
  206626  Death Knell        BA2 one share of the Knell, Shadow, base point 0 from the script; no Weakened
  206627  Death's Echo       BA3 +100% Death Knell damage taken per stack, 45 s, no cap, refreshed by each stack
  206628  Wail of the Banshee BA4 the 3 s cast bar (not interruptible: the registry owns the hit)
  206629  Wail of the Banshee BA4 the 12 yd ring's hit: resolve copy (Shadow), 45% / 50%, no Weakened; Terrified rider
  206630  Terrified          the 2 s fear (mechanic Fear), the rider of the Wail, its echo and the Visage
  206631  Wail's Echo        BA5 (heroic) the donut's hit: resolve copy (Shadow), 40%, no Weakened; Terrified rider
  206632  Horrifying Visage  BA6 the 2 s cast bar (normal)
  206633  Horrifying Visage  BA6 the 1.5 s cast bar (heroic)
  206634  Horrifying Visage  BA6 the cone's hit: resolve copy (Shadow), 30% / 35% + 1 Weakened; Terrified rider
  206635  Lament for the Living BA7 (heroic) the 2.5 s interruptible cast: completed, a Death's Echo stack on everyone
  206636-206644 spare.

Visual ids are WP-V-1's (._visuals; every look is unconfirmed until seen in game).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import RESOLVE_RAW, TARGET_UNIT_TARGET_ENEMY
from lib.dsl.registry import creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BA_BANSHEE_SHRIEK,
    BA_DEATH_KNELL,
    BA_TERRIFIED,
    BA_VISAGE,
    BA_WAIL,
    BA_WAIL_ALT,
    SV_KEENED_SKULL_STATE,
)

creature_template_columns(10436, **boss_columns(
    'boss_baroness_anastari_rework', 71.76, damage_modifier=3.5,
))

_BA = 'Stratholme build WP-S10 (Baroness Anastari)'

_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000      # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_MECHANIC_FEAR = 5
_INTERRUPT_FLAGS_STANDARD = 15               # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_STACKS_NO_CAP = 255
_KEENED_MS = 6000                            # BaronessLogic.h kKeenMs (heroic 5 s: the script shortens the aura)
_ECHO_MS = 45000                             # BaronessLogic.h kEchoDurationMs
_TERRIFIED_MS = 2000                         # BaronessLogic.h kTerrifiedMs
_WAIL_CAST_MS = 3000                         # BaronessLogic.h kWailCastMs
_VISAGE_CAST_MS = 2000                       # BaronessLogic.h kVisageCastMs normal
_VISAGE_CAST_HEROIC_MS = 1500                # ... heroic
_LAMENT_CAST_MS = 2500                       # BaronessLogic.h kLamentCastMs

_ICON_CURSE_OF_DOOM = 91                     # Curse of Doom 603
_ICON_SHADOW_BURST = 207                     # Shadow Burst 28447 (Spell_Shadow_AntiShadow)
_ICON_DEATH_SCREAM = 134                     # Spell_Shadow_DeathScream
_ICON_FEAR = 98                              # Fear 6215 (Spell_Shadow_Possession)
_ICON_PSYCHIC_SCREAM = 1488                  # Spell_Shadow_PsychicScream
_ICON_RAGING_SCREAM = 89                     # Spell_Shadow_RagingScream

_SCRIPT_SHARE = 'Stratholme: a share of the Death Knell, the script\'s base point (DungeonKit::WeightedShares)'

# --- BA1 The Keening -------------------------------------------------------------------------------------------------

keened_206625 = spell(
    id=206625, name='Keened', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_KEENED_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CURSE_OF_DOOM,
    notes=f'{_BA}, BA1 The Keening: the doomed player\'s debuff, put on the player with the fewest allies within 10 yd '
          '(ties: the farthest from her, then random) by boss_baroness_anastari_rework; 6 s (heroic 5 s: the script '
          'shortens the aura at the cast), and the Death Knell lands when the script\'s clock ends it or the doomed '
          'dies. A DUMMY aura: the tell only. Dispel none and NO_IMMUNITIES (nothing hides or removes the omen); '
          'AuraInterruptFlags CHANGE_MAP (a release out of the instance drops it). The skull over the head is the '
          'minted Curse of Weakness head state kit (V-1, SV 90506), which lasts the whole keen where Curse of Doom\'s '
          'impact kit is gone in 3 s.',
    raw_overrides=kit_raw('The Baroness keens for you. When it ends, the Death Knell strikes you and everyone close '
                          'to you.', 'The Death Knell comes for you. Stand with your allies.',
                          CastingTimeIndex=1, SpellVisualID_1=SV_KEENED_SKULL_STATE, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- BA2 Death Knell -------------------------------------------------------------------------------------------------

death_knell_206626 = spell(
    id=206626, name='Death Knell', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_SHARE)],
    spell_icon_id=_ICON_SHADOW_BURST,
    notes=f'{_BA}, BA2 Death Knell: one share of the toll, cast (triggered) by the Baroness on each player the Knell '
          'hits when the keen ends: 90% (heroic 100%) of the reference non-tank row, split evenly among the doomed and '
          'every player within 6 yd of them, each share x (1 + Death\'s Echo stacks). boss_baroness_anastari_rework '
          'computes the shares (DungeonKit::WeightedShares) and casts each with the share as base point 0 (DieSides 0: '
          'exact). Shadow, no Weakened (a split hit: the right play is to stand together). The resolve attribute set '
          '(no active defense, redirection, reflection or threat; ignores LoS; cannot crit; not a proc; always hits; '
          'ignores caster modifiers). Shadow Burst 28447\'s SV 45 on every player hit: the visible impact.',
    raw_overrides=kit_raw('A bell tolls for the dead and for those who stood near them.',
                          **{**RESOLVE_RAW, 'SpellVisualID_1': BA_DEATH_KNELL}),
)

# --- BA3 Death's Echo ------------------------------------------------------------------------------------------------

deaths_echo_206627 = spell(
    id=206627, name="Death's Echo", school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_ECHO_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CURSE_OF_DOOM,
    notes=f'{_BA}, BA3 Death\'s Echo: every player a Death Knell hits gains a stack (heroic: the Lament, completed, '
          'gives everyone one), +100% damage taken from the Death Knell per stack (the script reads the stack count, '
          'DungeonKit::Stacks, and raises the share; the aura itself has no number), 45 s, each new stack refreshes '
          'it, no cap (CumulativeAura 255, DungeonKit::AddStacks; Odo\'s Frenzy is the precedent). Not dispellable: Dispel '
          'none and NO_IMMUNITIES. The bots\' soak eligibility reads its stacks (players without it join the stack on '
          'the doomed; holders keep out of the 6 yd). AuraInterruptFlags CHANGE_MAP; the script removes it from '
          'everyone on her death, evade and reset.',
    raw_overrides=kit_raw('Death has heard your name. The Death Knell hurts you more.',
                          'Death has heard your name. The Death Knell hurts you more.',
                          CastingTimeIndex=1, CumulativeAura=_STACKS_NO_CAP, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- BA4 Wail of the Banshee and Terrified ----------------------------------------------------------------------------

wail_bar_206628 = cast_bar(
    206628, 'Wail of the Banshee', _WAIL_CAST_MS, 'A scream that kills and terrifies.',
    f'{_BA}, BA4: the 3 s cast bar (emote line 2, a 12 yd ring marker on her); she stands still while she casts. Not '
    'interruptible (cast_bar): the registry circle on her owns the hit (206629). Banshee Shriek 16838\'s SV 569 (a '
    'white ring and the shout, V-1 BA_BANSHEE_SHRIEK) plays on her as the bar starts.',
    icon=_ICON_DEATH_SCREAM, visual=BA_BANSHEE_SHRIEK, school=School.SHADOW,
)

wail_hit_206629 = resolve_copy(
    206629, 'Wail of the Banshee', School.SHADOW, 'A scream that kills and terrifies.',
    f'{_BA}, BA4: the ring\'s hit: 45% (heroic 50%) of the row, in 12 yd around her, the tank too (its own row), no '
    'Weakened (over 30%), with the Terrified rider (206630), through the registry. Copy of the resolve spell 205001 '
    '(Shadow). Wail of Souls 17631\'s SV 4341 (the skull-spirit ribbon and the shadow impact, V-1 BA_WAIL) on every '
    'unit hit: the visible impact.',
    icon=_ICON_DEATH_SCREAM, visual=BA_WAIL,
)

terrified_206630 = spell(
    id=206630, name='Terrified', school=School.SHADOW, dispel=0, mechanic=_MECHANIC_FEAR,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_TERRIFIED_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_FEAR, base_points=0,
                    mechanic=_MECHANIC_FEAR, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FEAR,
    notes=f'{_BA}: the one 2 s fear (the shared limit on loss of control) the Wail (206629), its heroic echo (206631) '
          'and the Visage (206634) apply as the registry\'s rider, cast by the Baroness on every unit hit: the player '
          'runs in fear from her for 2 s. Mechanic Fear and not NO_IMMUNITIES, so a fear break (Will of the Forsaken, '
          'Fear Ward on the right player, Berserker Rage) is a reward (ST). Dispel none: 2 s is not worth a cure. '
          'Howl of Terror 17928\'s SV 4801 (Fear_State_Head and the fear base at the feet, a STATE kit, V-1 '
          'BA_TERRIFIED); Terrify 7399\'s SV 736 is only a color tint. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Fills the target with dread: they run in terror for $d.', 'Running in terror.',
                          CastingTimeIndex=1, SpellVisualID_1=BA_TERRIFIED, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- BA5 The Wail's echo (heroic) ------------------------------------------------------------------------------------

wail_echo_hit_206631 = resolve_copy(
    206631, "Wail's Echo", School.SHADOW, 'The scream comes back.',
    f'{_BA}, BA5 (heroic): the donut\'s hit, 2 s after the Wail lands: 40% of the row on everyone between 8 and 32 yd '
    'from her (an 8 / 32 yd donut: below an inner / outer ratio of 0.25 the marker draws no hole, orchestrator '
    'ruling), the tank too, no Weakened (over 30%), with the Terrified rider, through the registry. Copy of the '
    'resolve spell 205001 (Shadow). The Wail of Souls impact SV 4341 on every unit hit.',
    icon=_ICON_DEATH_SCREAM, visual=BA_WAIL,
)

# --- BA6 Horrifying Visage -------------------------------------------------------------------------------------------

visage_bar_206632 = cast_bar(
    206632, 'Horrifying Visage', _VISAGE_CAST_MS, 'She lifts her veil, and her face is the last thing you see.',
    f'{_BA}, BA6 normal: the 2 s cast bar (emote line 3 names the player she turns to; the cone marker is on the '
    'floor from the cast start and does not track). Not interruptible (cast_bar). Soul Scream 32421\'s SV 7945 '
    '(the shout ring, V-1 BA_VISAGE).',
    icon=_ICON_PSYCHIC_SCREAM, visual=BA_VISAGE, school=School.SHADOW,
)

visage_bar_heroic_206633 = cast_bar(
    206633, 'Horrifying Visage', _VISAGE_CAST_HEROIC_MS, 'She lifts her veil, and her face is the last thing you see.',
    f'{_BA}, BA6 heroic: the same bar at 1.5 s; heroic aims two cones at two different players at once. Not '
    'interruptible (cast_bar). SV 7945.',
    icon=_ICON_PSYCHIC_SCREAM, visual=BA_VISAGE, school=School.SHADOW,
)

visage_hit_206634 = resolve_copy(
    206634, 'Horrifying Visage', School.SHADOW, 'Her face is the last thing you see.',
    f'{_BA}, BA6: the cone\'s hit: 30% (heroic 35%) of the row on everyone inside the 60 degree 30 yd cone aimed at '
    'the chosen player\'s spot at the cast start, the tank too (its own row), 1 Weakened (the mechanic has it at every '
    'difficulty), with the Terrified rider, through the registry. Copy of the resolve spell 205001 (Shadow). Soul '
    'Scream\'s SV 7945 (a ring and confusion marks over the head, V-1 BA_WAIL_ALT) on every unit hit.',
    icon=_ICON_PSYCHIC_SCREAM, visual=BA_WAIL_ALT,
)

# --- BA7 Lament for the Living (heroic) ------------------------------------------------------------------------------

lament_206635 = spell(
    id=206635, name='Lament for the Living', school=School.SHADOW, cast_time_ms=_LAMENT_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_RAGING_SCREAM,
    notes=f'{_BA}, BA7 (heroic): the 2.5 s cast every 30 s from 21 s (yell line 4). Interruptible: InterruptFlags 15 '
          '(movement, pushback, interrupt, auto-attack) and PreventionType 1 (a silence stops it); the descriptor\'s '
          'interrupt list, priority 3, every 30 s, expected on heroic. OnSpellCast (completed) = a Death\'s Echo stack '
          'on every player in the fight (DungeonKit::AddStacks), which wrecks the next rotation; OnSpellFailed = '
          'stopped. A DUMMY effect on herself, no damage. The Wail of Souls SV 4341 plays on her as the bar starts.',
    raw_overrides=kit_raw('Mourns the living. If the lament finishes, every player gains Death\'s Echo.',
                          InterruptFlags=_INTERRUPT_FLAGS_STANDARD, PreventionType=_PREVENTION_SILENCE,
                          SpellVisualID_1=BA_WAIL),
)
