"""
Zul'Farrak build WP-D2: Antu'sul (8127) and his Servants (8156), normal and heroic
(.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D2, s3.6, s3.8, s7 #9 A, #25 A, #28 A; build spec
docs/dungeons/zul-farrak-rework.md SP 733-807, design SP 534-732, rulings 13-16). WP-D2 owns this file (its spells:
kSpellsAntusul 213890-213919 of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h only; AntusulLogic.h names
the same ids). The engine side is src/ZulFarrak/boss_antusul_rework.cpp; the texts are
data/sql/updates/pending_db_world/rev_antusul_zul_farrak.sql.

- 8127 Antu'sul: boss_antusul_rework (SmartAI off: rev_skeleton_zul_farrak.sql drops his rows), normal health 159,947 =
  104.2 on the level 46 paladin base 1,535 (s3.6, s7 #1 A x1.6), stock DamageModifier 4.25, immunity 1972,
  INSTANCE_BIND with both assist flags, detection 12 (WP-S0's boss_columns). Heroic 266,666 is WP-H's override.
- 8156 Servant of Antu'sul (stock entry, no spawns: his summons): npc_antusul_servant_rework (SmartAI off: the S0 rev),
  stock health (5,757; heroic 15,000 is WP-H's). Type 1 (beast, was 10 "not specified") so that every crowd control the
  spec names works on it: a polymorph, a fear, a hibernate (SP AS2: "a stun, fear or polymorph on a Servant stops its
  gaze"). Immunity 0 (stock).

Spells. The shrapnel, the crack, the bolt and the Shockwave deal their damage through dungeon copies of the
mod-boss-mechanics resolve spell (the registry's percent of the reference row; the combat log names the mechanic). The
bars are no-effect casts (Physical: a kicked Healing Wave locks Nature for 4-8 s and must never refuse a bar, s3.5 kick
table); every bar and the heal keep his swing timer (SPELL_ATTR2_DO_NOT_RESET_COMBAT_TIMERS, LESSONS L3). The rest are
auras and looks:

  213890  Calcify               AS3 Magic, 6 stacks (CumulativeAura), 30 s: -5% damage taken and -7% speed a stack;
                                spell_zf_antusul_calcify takes every stack on a dispel and shatters them (AS7)
  213891  Calcifying Gaze       AS2 the Servant's 6 s channel at its target (SV 90704, the white beam with the basilisk
                                pose); not interruptible; a look: the stacks are the AI's
  213892  Petrified             AS5 the statue: a 2 s stun (Petrification 17624's SV 1845)
  213893  Shatterbolt           AS6 the 2.5 s bar (Physical, not kickable)
  213894  Shatterbolt           AS6 heroic: the 2 s bar
  213895  Shatterbolt           AS6 the bolt on its target: resolve copy (Nature)
  213896  Shatterbolt           AS6 the lightning on the target (Chain Lightning 16006's SV 36)
  213897  Shatter               AS7 the shrapnel: resolve copy (Physical), Gruul's Shatter SV 8097
  213898  Petrified             AS5 the crack on the statue: resolve copy (Physical)
  213899  Earthen Shockwave     AS8 the 3 s bar (Physical, not kickable)
  213900  Earthen Shockwave     AS8 the group hit: resolve copy (Nature)
  213901  Earthen Shockwave     AS8 the ground slam on him (Ground Slam SV 8083, V's pick)
  213902  Healing Wave of Antu'sul  AS9 the 3 s heal (Nature, kickable), an exact amount from the script
  213903  Healing Wave of Antu'sul  AS9 heroic: the 2 s heal
  213904  Stoneflesh            AS10 heroic: 3 stacks on him at the pull, -10% damage taken each (Stoneskin 28995's
                                SV 7627)
  213905  Servant of Antu'sul   AS1 the dirt burst on a risen Servant (SV 7443, V's stand-in)
  213906-213919 spare.

Earth Shock 15501 (AS4) stays stock, cast triggered, with a Calcify stack added by the script. Retired from his kit (no
row here): Chain Lightning 16006, Earthgrab Totem 8376, Healing Ward 11899, Healing Wave of Antu'sul 11895, Antu'sul's
Minion 11894 and Petrify 11020 as cast. The Earthgrab Totem 6066 keeps its SmartAI: seven other creatures still cast
8376 (smart_scripts 660, 670, 761, 4440, 5485, 5710, 14324).

Tooltips are number-free.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR0_DO_NOT_DISPLAY, ATTR0_DO_NOT_LOG, ATTR1_NO_THREAT, ATTR2_IGNORE_LINE_OF_SIGHT
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    AS_CALCIFY,
    AS_GAZE_BEAM,
    AS_HEAL,
    AS_PETRIFIED,
    AS_SERVANT_RISE,
    AS_SHATTER,
    AS_SHATTERBOLT,
    AS_SHOCKWAVE,
    AS_STONEFLESH,
)

creature_template_columns(8127, **boss_columns(
    'boss_antusul_rework', 104.2, damage_modifier=4.25,
))

# The Servant's script (stock health; its SmartAI row dropped by the S0 rev) and a beast's type (crowd control).
creature_template_columns(8156, ScriptName='npc_antusul_servant_rework', AIName='', type=1)

_AS = "Zul'Farrak build WP-D2 (Antu'sul)"
_SCRIPT_EXACT = "Zul'Farrak: an exact amount from the script (CastCustomSpell base point 0)"

_SCHOOL_MASK_ALL = 127
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000      # a finished cast keeps his swing timer (LESSONS L3)
_INTERRUPT_FLAGS_STANDARD = 15      # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_DISPEL_MAGIC = 1
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): the aura never leaves the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

# AntusulLogic.h Tune (the DT test pins each against the header).
_CALCIFY_STACKS = 6                 # kCalcifyMaxStacks
_CALCIFY_MS = 30000                 # kCalcifyDurationMs
_CALCIFY_TAKEN = 5                  # kCalcifyTakenPctPerStack
_CALCIFY_SLOW = 7                   # kCalcifySlowPctPerStack
_GAZE_MS = 6000                     # kGazeMs
_PETRIFY_MS = 2000                  # kPetrifyMs
_BOLT_CAST = (2500, 2000)           # kBoltCastMs
_SHOCKWAVE_CAST = 3000              # kShockwaveCastMs
_HEAL_CAST = (3000, 2000)           # kHealCastMs
_STONEFLESH_STACKS = 3              # kStonefleshStacks
_STONEFLESH_TAKEN = 10              # kStonefleshTakenPctPerStack

# Stock icons (Spell.dbc).
_ICON_STONE_SKIN = 148              # Stone Skin 5810, Crystal Gaze 3635, Petrify 11020
_ICON_PETRIFICATION = 1642          # Petrification 17624
_ICON_CHAIN_LIGHTNING = 165         # Chain Lightning 16006
_ICON_SHOCKWAVE = 211               # Shockwave 33686
_ICON_HEALING_WAVE = 684            # Healing Wave of Antu'sul 11895
_ICON_STONESKIN = 139               # Stoneskin 28995
_ICON_GENERIC = 1                   # Antu'sul's Minion 11894


def _bar(spell_id: int, name: str, cast_ms: int, desc: str, notes: str, icon: int):
    """A named no-effect bar (DUMMY on the caster, no handler) the registry's hit lands at the end of: Physical (never
    the school of his kickable Healing Wave), not interruptible, and it keeps his swing timer."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=cast_ms, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, InterruptFlags=0, PreventionType=0, AttributesEx4=ATTR4_NO_CAST_LOG,
                              AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS),
    )


def _look(spell_id: int, name: str, visual: int, icon: int, notes: str, *, school: School = School.NATURE,
          self_cast: bool = False):
    """A look cast triggered: an instant DUMMY on the target (or himself), no handler, hidden from the log."""
    return spell(
        id=spell_id, name=name, school=school, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF if self_cast else 100.0, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY,
                        implicit_target_a=TARGET_UNIT_CASTER if self_cast else TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _heal(spell_id: int, cast_ms: int, notes: str):
    """AS9: Healing Wave of Antu'sul, a real cast on himself (kickable: InterruptFlags 15, PreventionType silence;
    Nature), an exact amount from the script (base point 0). Ignores his modifiers; a healing reduction on him cuts
    it. Keeps his swing timer."""
    return spell(
        id=spell_id, name="Healing Wave of Antu'sul", school=School.NATURE, cast_time_ms=cast_ms, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=_SCRIPT_EXACT)],
        spell_icon_id=_ICON_HEALING_WAVE, notes=notes,
        raw_overrides=kit_raw('Heals Antu\'sul.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                              PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=AS_HEAL,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                              AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
    )


# --- AS3 Calcify -----------------------------------------------------------------------------------------------------

calcify_213890 = spell(
    id=213890, name='Calcify', school=School.NATURE, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_CALCIFY_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=-_CALCIFY_TAKEN, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Calcify: a flat 5% less damage taken a stack, not a damage or heal value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-_CALCIFY_SLOW,
                    die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_STONE_SKIN,
    notes=f'{_AS}, AS3: stone on a player. Antu\'sul applies and grows it (DungeonKit::AddStacks, caster Antu\'sul): '
          'a stack each 2 s of a Servant\'s gaze (heroic 1.5 s), one with each Earth Shock on his victim, two from '
          'heroic stone dust. Up to 6 (CumulativeAura); the AI petrifies a player at the sixth (AS5) and removes it. '
          'Each stack: 5% less damage taken (all schools) and 7% slower (the engine multiplies both by the stacks; '
          '25% and 35% at 5). Mechanic none (a freedom effect never strips it), Magic: a dispel takes every stack at '
          'once and shatters them (spell_zf_antusul_calcify, AS7). A Shatterbolt or a petrify removes it with the AI. '
          '30 s, refreshed by each stack; dropped on a logout or a map change, removed on his death, evade and reset. '
          'Stone Skin 5810\'s SV 711.',
    raw_overrides=kit_raw('Stone creeps over the skin: less damage taken, slower. Dispelling it shatters the stone '
                          'on nearby allies.',
                          'Stone. Less damage taken, slower. A sixth stack petrifies. Dispelling it shatters the '
                          'stone on nearby allies.',
                          CastingTimeIndex=1, CumulativeAura=_CALCIFY_STACKS, SpellVisualID_1=AS_CALCIFY,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(calcify_213890, 'spell_zf_antusul_calcify')

# --- AS2 Calcifying Gaze ---------------------------------------------------------------------------------------------

gaze_213891 = spell(
    id=213891, name='Calcifying Gaze', school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=_GAZE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_STONE_SKIN,
    notes=f'{_AS}, AS2: a Servant\'s 6 s stare at a random player on his floor, tank included (a DUMMY aura on them: '
          'the beam and the debuff icon). A look only: Antu\'sul\'s AI lays the Calcify stacks on its own clock (one '
          'each 2 s, heroic 1.5 s) and stops the gaze when the Servant is stunned, feared or polymorphed, or its '
          'target dies. Not interruptible (InterruptFlags, ChannelInterruptFlags and PreventionType 0). SV 90704 '
          '(V: a copy of 8311 with the channel pose the basilisk has). Ignores LoS; dropped on a map change.',
    raw_overrides=kit_raw('Stares, turning flesh to stone.', 'A Servant of Antu\'sul stares at you. Stone creeps '
                          'over your skin.', CastingTimeIndex=1, InterruptFlags=0, ChannelInterruptFlags=0,
                          PreventionType=0, SpellVisualID_1=AS_GAZE_BEAM,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- AS5 Petrified ---------------------------------------------------------------------------------------------------

petrified_213892 = spell(
    id=213892, name='Petrified', school=School.NATURE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_PETRIFY_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_PETRIFICATION,
    notes=f'{_AS}, AS5: the sixth Calcify stack turns the player to stone: a 2 s stun (the cost in place of Weakened, '
          'SP AS5), tank included. A 6 yd registry circle on the statue warns the others for the 2 s (the shrapnel of '
          'six stacks, 213897); at 2 s the AI cracks it (213898 on the statue) and removes this. Mechanic none (no '
          'trinket breaks it), dispel none, NO_IMMUNITIES; dropped on a map change. Petrification 17624\'s SV 1845 '
          '(the stone tint).',
    raw_overrides=kit_raw('Turned to stone.', 'Turned to stone. The stone cracks when this ends, hurting you and '
                          'everyone close.', CastingTimeIndex=1, SpellVisualID_1=AS_PETRIFIED,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

crack_213898 = resolve_copy(
    213898, 'Petrified', School.NORMAL, 'The stone cracks.',
    f'{_AS}, AS5: the crack on the statue at the end of its 2 s (the kit\'s RegistryHit on that player): 25% normal / '
    '35% heroic of the reference row (the tank row on the tank), no Weakened (the stun was the cost). Copy of the '
    'resolve spell 205001 (Physical). No visual (the shrapnel 213897 plays it). Heroic: a crack within 6 yd of his '
    'edge also strips a Stoneflesh stack (AS10, the AI).',
    icon=_ICON_PETRIFICATION,
)

# --- AS6 Shatterbolt -------------------------------------------------------------------------------------------------

shatterbolt_bar_213893 = _bar(
    213893, 'Shatterbolt', _BOLT_CAST[0], 'Lightning that shatters stone.',
    f'{_AS}, AS6: the 2.5 s bar (normal) while a 6 yd registry circle marks the target (a random player with Calcify, '
    'anyone if nobody has a stack, tank included; the target is never counted). The AI lands the bolt (213895) and the '
    'shrapnel (213897) at its end. Physical and not kickable: a kicked Healing Wave locks Nature (s3.5 kick table).',
    _ICON_CHAIN_LIGHTNING,
)

shatterbolt_bar_h_213894 = _bar(
    213894, 'Shatterbolt', _BOLT_CAST[1], 'Lightning that shatters stone.',
    f'{_AS}, AS6 heroic: the 2 s bar (213893\'s twin).',
    _ICON_CHAIN_LIGHTNING,
)

shatterbolt_hit_213895 = resolve_copy(
    213895, 'Shatterbolt', School.NATURE, 'Lightning that shatters stone.',
    f'{_AS}, AS6: the bolt on its target (the kit\'s RegistryHit): 15% normal / 25% heroic of the reference row (the '
    'tank row on the tank), cut by the target\'s own Calcify (the AI applies the 5% a stack: the stacks go to the '
    'shrapnel before the registry lands it). No Weakened. Copy of the resolve spell 205001 (Nature). No visual (the '
    'look 213896 is the bolt).',
    icon=_ICON_CHAIN_LIGHTNING,
)

shatterbolt_look_213896 = _look(
    213896, 'Shatterbolt', AS_SHATTERBOLT, _ICON_CHAIN_LIGHTNING,
    f'{_AS}, AS6: the lightning Antu\'sul casts (triggered) on the bolt\'s target as it lands. Chain Lightning '
    '16006\'s SV 36 (stock, his old bolt).')

# --- AS7 Shatter -----------------------------------------------------------------------------------------------------

shatter_213897 = resolve_copy(
    213897, 'Shatter', School.NORMAL, 'Stone shatters into shrapnel.',
    f'{_AS}, AS7: the shrapnel: a 6 yd registry circle on the carrier (never hit by it) when a Shatterbolt lands, a '
    'dispel takes Calcify (no warning) or a statue cracks (the 2 s circle): 6% normal / 9% heroic of the reference row '
    'per stack shattered (36% / 54% at 6), cut by each victim\'s own Calcify; Weakened up to 5 stacks. Heroic stone '
    'dust: everyone hit gains 2 Calcify (the AI, a tick later). Copy of the resolve spell 205001 (Physical: armor '
    'cuts it). Gruul\'s Shatter 33671\'s SV 8097.',
    icon=_ICON_STONE_SKIN, visual=AS_SHATTER,
)

# --- AS8 Earthen Shockwave -------------------------------------------------------------------------------------------

shockwave_bar_213899 = _bar(
    213899, 'Earthen Shockwave', _SHOCKWAVE_CAST, 'Draws the stone beneath his feet.',
    f'{_AS}, AS8: the 3 s bar with emote line 3, every 20 s (heroic 18 s) from 20 s. The AI lands the group hit '
    '(213900) at its end. Physical and not kickable (s3.5 kick table).',
    _ICON_SHOCKWAVE,
)

shockwave_hit_213900 = resolve_copy(
    213900, 'Earthen Shockwave', School.NATURE, 'The ground heaves. Stone on the skin softens the blow.',
    f'{_AS}, AS8: everyone on his floor (the kit\'s RegistryHit, one per Calcify count): 50% normal / 70% heroic of '
    'the reference row (the tank row on the tank), cut by 10% of the hit per Calcify stack (ruling 15; the AI '
    'registers the hit divided by Calcify\'s own 5% a stack, which still applies when it lands), every other '
    'reduction on top. Unavoidable: no Weakened. Copy of the resolve spell 205001 (Nature). No visual (the slam on him '
    'is 213901).',
    icon=_ICON_SHOCKWAVE,
)

shockwave_look_213901 = _look(
    213901, 'Earthen Shockwave', AS_SHOCKWAVE, _ICON_SHOCKWAVE,
    f'{_AS}, AS8: the slam on Antu\'sul as the Shockwave lands (triggered, on himself). Ground Slam\'s SV 8083 (V\'s '
    'pick; Gruul\'s 8093 is the alternate).', school=School.NATURE, self_cast=True)

# --- AS9 Healing Wave of Antu'sul ------------------------------------------------------------------------------------

healing_wave_213902 = _heal(
    213902, _HEAL_CAST[0],
    f'{_AS}, AS9: the expected interrupt (descriptor interrupt list): a 3 s cast every 20 to 25 s from 15 s, healing '
    '4% of his health (the AI sets the amount at the cast\'s start). A kick locks his Nature school; his bars are '
    'Physical and Earth Shock is triggered. Healing Wave 331\'s SV 135 (V).')

healing_wave_h_213903 = _heal(
    213903, _HEAL_CAST[1],
    f'{_AS}, AS9 heroic: the 2 s cast, healing 8% of his health (213902\'s twin).')

# --- AS10 Stoneflesh -------------------------------------------------------------------------------------------------

stoneflesh_213904 = spell(
    id=213904, name='Stoneflesh', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=-_STONEFLESH_TAKEN, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Stoneflesh: a flat 10% less damage taken a stack, not a damage or heal value')],
    spell_icon_id=_ICON_STONESKIN,
    notes=f'{_AS}, AS10 heroic: Antu\'sul\'s own stone, 3 stacks at the pull (DungeonKit::AddStacks on himself), each '
          '10% less damage taken (30% at 3). Only a petrify crack within 6 yd of his edge strips one (the AI); stacks '
          'never return. Dispel none (no purge or steal takes it); mechanic none (immunity set 1972 never touches it, '
          'RB-5). For the fight; removed on his evade, reset and death. Stoneskin 28995\'s SV 7627.',
    raw_overrides=kit_raw('Hardened stone.', 'Stone skin: less damage taken. Petrified players cracking beside him '
                          'break it.', CastingTimeIndex=1, CumulativeAura=_STONEFLESH_STACKS,
                          SpellVisualID_1=AS_STONEFLESH, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- AS1 the rise ----------------------------------------------------------------------------------------------------

servant_rise_213905 = _look(
    213905, 'Servant of Antu\'sul', AS_SERVANT_RISE, _ICON_GENERIC,
    f'{_AS}, AS1: the dirt burst a Servant casts on itself as it rises at a rise point (triggered). SV 7443 (V\'s '
    'stand-in: the basilisk has no birth animation; 1266 is the alternate).', school=School.NATURE, self_cast=True)
