"""
Scholomance build WP-S12: Ras Frostwhisper's hard mode "the Torn Keepsake", heroic only
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S12, s3.6, s10; build spec
docs/dungeons/scholomance-rework.md SC 1087-1134, 1207-1209). WP-S12 owns this file (its spells: kSpellsRasHardMode
206190-206204 of modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h only; RasHardModeLogic.h names the same
ids; its creature: the Ice Tomb 300535). The engine side is src/Scholomance/ras_hard_mode.cpp: the fight runs on S4's
AI (boss_ras_frostwhisper_rework) through RasFight.h.

The keepsake gameobjects (301150 torn page x3, 301151 / 301152 the book, empty and bound, 301154 the alchemy table that
lights the hard mode) and their heroic-only spawns at the user's spots are WP-S12's SQL rev (dbc-tools does not declare
gameobjects), with Ras's text group 3 (the hard mode start).

- 300535 Ice Tomb (RF3, hard mode only): the permanent tomb on a frozen player, a 12k target (warrior base 3,052 at
  level 60 x 3.9318; the script sets exactly 12,000 too). Hostile (the school's faction 233), not specified (type 10),
  no XP, no loot, no melee, no health regen; npc_sc_ice_tomb roots it, keeps it passive and cracks it at zero (1.5 s,
  then the thaw). Display Sindragosa's Ice Tomb 30890 at scale 0.35 (WP-V). Heroic only, summoned directly at this
  entry: NO heroic template and no difficulty_entry_1 (the wave C mint rule; source/world/dungeons/scholomance.py's
  _KIT_ADD_HEROIC does not list it).

Spells (Spell.dbc 3.3.5 for every stock id quoted; looks from WP-V's ._visuals, all stock):

  206190  Clinging to Life   RF9 the 3 s transition cast bar (no effect): the lich bar is empty, he is untargetable,
                             yells "THIS CANNOT BE!!" and turns human, healing to full over the bar
  206191  Siphon Warmth      RF10 the 2 s cast bar (emote line 2), not interruptible (the Volley is the interrupt)
  206192  Siphon Warmth      RF10 the 5 s self channel (the look; the ticks run on the script's clock), not
                             interruptible; Life Drain 28542's SV 7607
  206193  Siphoned           RF10 the drain on each warm player, 1.5 s, refreshed every tick: SV 7607 on them
  206194  Siphon Warmth      RF10 the heal on Ras: 1% of his bar per warm player per tick, at most 10% a Siphon
                             (base point 0 = the exact amount, from the script)
  206195  Siphon Backfire    RF10 each cold player's backfire on Ras: 1.3% of his bar per tick (base point 0 = the
                             amount; cast by the player, so the damage is theirs: no threat, always hits, no crit, no
                             caster modifiers or resistances; spell_sc_ras_siphon_backfire makes the hit exact
                             past his damage-taken modifiers too)
  206196  Mortal Decay       RF11 the phase 2 enrage: a Frost DoT stacking on every player every 10 s, 0.5% of the
                             heroic reference row per second per stack (spell_sc_ras_mortal_decay; ignores caster
                             modifiers, no crit, not dispellable); 15 s, refreshed at each 10 s step, dropped on a
                             logout or a map change; Blood Plague 55264's SV 11624
  206197  Thawing            RF3 HM: the broken tomb's 1.5 s cast bar while the 6 yd thaw circle warns
  206198-206204 spare.
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    cast_bar,
    kit_raw,
)
from ._visuals import DISPLAY_ICE_TOMB, ICE_TOMB_SIZE, RF_MORTAL_DECAY, RF_SIPHON_WARMTH

_RK = 'Scholomance build WP-S12 (Ras Frostwhisper hard mode, the Torn Keepsake)'
_SCRIPT_EXACT = 'Scholomance: base point 0 is the exact amount, computed by ras_hard_mode.cpp (KeepsakeFight)'
_SCRIPT_REF = 'Scholomance: a percent of reference health, set by the script (DungeonKit::RefFlatOn)'

_TARGET_UNIT_TARGET_ENEMY = 6
_ATTR1_IS_SELF_CHANNELED = 0x00000040
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000
_ATTR4_IGNORE_RESISTANCES = 0x00000001

_ICON_DEATH_PACT = 169          # Death Pact 17471 (Clinging to Life)
_ICON_LIFE_DRAIN = 546          # Life Drain 28542 (Siphon Warmth)
_ICON_BLOOD_PLAGUE = 2623       # Blood Plague 55264 (Mortal Decay)
_ICON_ICE_TOMB = 35             # Ice Tomb 16869

_DECAY_MAX_STACKS = 99          # RasHardModeLogic.h kDecayMaxStacks
_DECAY_DURATION_MS = 15000      # RasHardModeLogic.h kDecayDurationMs: longer than the 10 s step that refreshes it
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): AC drops the aura before the logout save, after the login load and on
# a cross-map teleport (a same-map teleport keeps it), so a stray Decay never ticks on a player back on the map.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

# --- 300535 Ice Tomb -------------------------------------------------------------------------------------------------

# Level 60 warrior base 3,052: ceil(3,052 x 3.9318) = 12,000 (the build spec's tomb; the script sets it too).
ice_tomb_300535 = creature_template(
    300535, 'Ice Tomb', **{
        **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'type': 10, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': 3.9318, 'DamageModifier': 0.0, 'RegenHealth': 0, 'detection_range': 0.0, 'lootid': 0,
        'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': 0x40,
        'ScriptName': 'npc_sc_ice_tomb',
    },
)
creature_model(300535, display_id=DISPLAY_ICE_TOMB, scale=ICE_TOMB_SIZE)

# --- RF9 the transition ----------------------------------------------------------------------------------------------

clinging_to_life_206190 = cast_bar(
    206190, 'Clinging to Life', 3000, 'The keepsake drags back the mortal he was.',
    f'{_RK}, RF9: the 3 s transition when the lich\'s bar empties (the hard mode\'s lethal guard): Ras is untargetable '
    '(script flags), yells group 0 "THIS CANNOT BE!!" and heals to full over the bar; at its end he takes the human '
    'form (display 3975) and phase 2 starts. S4\'s fight clock stands still meanwhile (RasHardMode::HoldsTimeline). No '
    'look (the morph is the look).',
    icon=_ICON_DEATH_PACT, school=School.FROST)

# --- RF10 Siphon Warmth ----------------------------------------------------------------------------------------------

siphon_cast_206191 = cast_bar(
    206191, 'Siphon Warmth', 2000, 'Reaches for the warmth of the living.',
    f'{_RK}, RF10: the 2 s warning before the channel, with emote line 2 and the registry Spread (8 yd, bots) for the '
    'cast and the channel. Every 30 s from 10 s into phase 2; a due Siphon waits while he casts or a Frost Mark is '
    'live. Not interruptible.',
    icon=_ICON_LIFE_DRAIN, school=School.SHADOW)

siphon_channel_206192 = spell(
    id=206192, name='Siphon Warmth', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=5000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_LIFE_DRAIN,
    notes=f'{_RK}, RF10: the 5 s channel, the look only (SPELL_ATTR1_IS_SELF_CHANNELED with a DUMMY aura, like '
          'Sneed\'s repairs): the five ticks run on the script\'s clock, so a broken channel changes nothing. Not '
          'interruptible (InterruptFlags, ChannelInterruptFlags and PreventionType 0). While it runs S4\'s Volley and '
          'Blizzard wait (he is casting) and his per-second Chill beat is the Siphon\'s (RasHardMode::HoldsChillBeat). '
          'Life Drain 28542\'s SV 7607.',
    raw_overrides=kit_raw('Drinks the warmth of the living.', 'Drinking warmth.', AttributesEx=_ATTR1_IS_SELF_CHANNELED,
                          ChannelInterruptFlags=0, InterruptFlags=0, PreventionType=0,
                          SpellVisualID_1=RF_SIPHON_WARMTH, AttributesEx4=ATTR4_NO_CAST_LOG),
)

siphoned_206193 = spell(
    id=206193, name='Siphoned', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=1500,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_LIFE_DRAIN,
    notes=f'{_RK}, RF10: the drain on each warm player at every Siphon tick (Ras casts it, triggered): the impact and '
          'a 1.5 s state, refreshed while the player stays warm. No effect: the +3 Chill a tick and Ras\'s heal are '
          'the script\'s. Ignores LoS (a triggered cast still checks it). Life Drain 28542\'s SV 7607.',
    raw_overrides=kit_raw('Your warmth is being drained.', 'Your warmth is being drained. Step away from your allies.',
                          instant=True, AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                          SpellVisualID_1=RF_SIPHON_WARMTH, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

siphon_heal_206194 = spell(
    id=206194, name='Siphon Warmth', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_SCRIPT_EXACT)],
    spell_icon_id=_ICON_LIFE_DRAIN,
    notes=f'{_RK}, RF10: Ras\'s heal at each Siphon tick, 1% of his bar (400k: 4,000) per warm player, at most 10% '
          '(40,000) per Siphon; base point 0 is the exact amount (CastCustomSpell, triggered, on himself). Ignores '
          'caster modifiers; a healing reduction on him (Mortal Strike) cuts it.',
    raw_overrides=kit_raw('Drinks the warmth of the living.', instant=True, InterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

siphon_backfire_206195 = spell(
    id=206195, name='Siphon Backfire', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_EXACT)],
    spell_icon_id=_ICON_LIFE_DRAIN,
    notes=f'{_RK}, RF10: he drinks warmth that is not there: at each Siphon tick every cold living player (not warm, '
          'not entombed) casts this on Ras (triggered, queued on his event list so a killing backfire never runs '
          'inside the hard mode\'s own update): 1.3% of his bar (5,200) each; five cold players for the full 5 s is '
          'about 32%. Base point 0 is the exact amount. The damage is the player\'s (credit) but makes no threat, '
          'always hits, cannot crit and ignores caster modifiers and resistances, and spell_sc_ras_siphon_backfire '
          'sets the hit to base point 0 after Ras\'s damage-taken modifiers (Curse of the Elements and the like), so '
          'the number is the build spec\'s. Ignores LoS. Life Drain 28542\'s SV 7607 (the impact on Ras).',
    raw_overrides=kit_raw('The warmth he reaches for is not there.', instant=True, InterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG | _ATTR4_IGNORE_RESISTANCES,
                          SpellVisualID_1=RF_SIPHON_WARMTH),
)
scripted_by(siphon_backfire_206195, 'spell_sc_ras_siphon_backfire')

# --- RF11 Mortal Decay -----------------------------------------------------------------------------------------------

mortal_decay_206196 = spell(
    id=206196, name='Mortal Decay', school=School.FROST, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=_DECAY_DURATION_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=1, die_sides=0,
                    amplitude=1000, implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REF)],
    spell_icon_id=_ICON_BLOOD_PLAGUE,
    notes=f'{_RK}, RF11: phase 2\'s enrage, the mortal body failing. Ras sets every fight player\'s stacks every 10 s '
          'to the whole 10 s elapsed in phase 2 (DungeonKit::AddStacks; 5 at 50 s, 12 at 2 min), so a revived player '
          'gets the full count. Each stack deals 0.5% of the heroic reference row a second (spell_sc_ras_mortal_decay '
          'sets the per-stack amount; the engine multiplies by the stacks): 2.5% a second at 5, 6% at 12. Frost; '
          'ignores caster modifiers, always hits, cannot crit; not dispellable (Dispel none). Removed at his death, '
          'evade or reset (and on the player\'s death). 15 s, refreshed at every 10 s step, and AuraInterruptFlags '
          'CHANGE_MAP: a player who leaves the fight or logs out loses it. Blood Plague 55264\'s SV 11624.',
    raw_overrides=kit_raw('The mortal body is failing.', 'Frost damage every second, more with each stack.',
                          instant=True, CumulativeAura=_DECAY_MAX_STACKS, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          SpellVisualID_1=RF_MORTAL_DECAY, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(mortal_decay_206196, 'spell_sc_ras_mortal_decay')

# --- RF3 HM: the broken tomb -----------------------------------------------------------------------------------------

thawing_206197 = cast_bar(
    206197, 'Thawing', 1500, 'The ice cracks.',
    f'{_RK}, RF3 hard mode: the Ice Tomb\'s 1.5 s bar when its health runs out (npc_sc_ice_tomb keeps it at 1 health '
    'and makes it unselectable): S4\'s 6 yd thaw circle (206174: 45% heroic, Weakened, +3 Chill) warns on the frozen '
    'player meanwhile, then the tomb bursts and lets them go. The crack gives the players breaking it time to step '
    'out (S4\'s instant thaw would hit every melee player on the tomb).',
    icon=_ICON_ICE_TOMB, school=School.FROST)
