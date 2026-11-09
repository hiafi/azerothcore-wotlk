"""
Stratholme build WP-S2: Hearthsinger Forresten (10558), normal and heroic
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows HF, s3.5 row S2, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 826-882, design ST 680-824). WP-S2 owns this file (its spells: kSpellsForresten
206440-206459 of modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; ForrestenLogic.h names the same
ids; its creatures: the Gutter Rat 300602 and the hearth stalker 300603).

- 10558 Hearthsinger Forresten: boss_hearthsinger_forresten_rework (SmartAI off; WP-S2's SQL rev drops the five stock
  rows: Incorporeal Defense on reset, Shoot, Multi-Shot, Demoralizing Shout and Enchanting Lullaby), the build spec's
  normal health (175k: HealthModifier 62.859 on the level 57 warrior class base 2,784), DamageModifier 3.5 (the stock
  value, base SQL; the live 5.4 is a mod-progression leftover), stun immunity 1972 (the build spec asked for his own
  set, stun immune and interruptible: handoff s7 #3 rules 1972), INSTANCE_BIND. Heroic health 240k and the tier's melee
  are WP-H's (source/world/dungeons/stratholme.py). Shoot 16100 and Multi-Shot 14443 stay stock (DD scales them on
  heroic).
- 300602 Gutter Rat (HF2, HF3, HF7): the three Plagued Rat displays 1141, 1418 and 2176 (10441 itself stays the gate
  trap's), level 57 beast, faction 7 (his), HealthModifier 0.35918: ceil(2,784 x 0.35918) = 1,000 (heroic 1,500 is
  WP-H's `_KIT_ADD_HEROIC`, applied because this file declares it; the heroic row is 310192, the lock's predicted id
  after wave 1's three adds). DamageModifier 0.4 (the stock rat's). Melee on the players; Plague Bite rides its bites.
  npc_st_gutter_rat.
- 300603 Hearth stalker (HF5): invisible (KIT_HELPER), carries the hearth's glow aura 206448. No heroic template
  (handoff s3.3: stalkers run on their normal entry). npc_st_hearth_stalker.

Spells. The note and the two line hits are dungeon copies of the mod-boss-mechanics resolve spell (the registry's
percent of the reference row; the combat log names the mechanic); Plague Bite is the kit's generic percent DoT:

  206440  Note               HF4 the note's hit: resolve copy (Arcane), 20%, Weakened, with the Dance rider
  206441  Dance              HF4 the 1.5 s dance a note's hit gives (an emote state; no loss of control)
  206442  Drowsy             HF6 the stacking meter (3 stacks), 6 s, refreshed by each stack
  206443  Asleep             HF6 the 2 s sleep at three Drowsy stacks (MOD_STUN, mechanic sleep)
  206444  Rat Line           HF7 a rat line's hit: resolve copy (Physical), 15%, Weakened
  206445  Crescendo          HF11 the big line's hit: resolve copy (Physical), 30%, Weakened
  206446  Crescendo          HF8 the 3 s cast on the interrupt list
  206447  Plague Bite        HF3 Disease, 1% of the reference row a second a stack, 10 s, 5 stacks
  206448  Hearth             HF5 the hearth's glow on its stalker
  206449-206459 spare

Visual ids are WP-V-2's (._visuals; every look is unconfirmed until seen in game).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INVISIBLE_STALKER,
    DISPLAYS_FORRESTEN_RATS,
    FO_BLACK_ROT,
    FO_DROWSY,
    FO_DROWSY_ALT,
    FO_LISTENING_MUSIC,
    FO_SIREN_SONG,
    RG_GORE,
    SV_FLAMEZONE_8_STATE,
)

_HF = 'Stratholme build WP-S2 (Hearthsinger Forresten)'

_FACTION_FORRESTEN = 7                       # his stock faction: the rats are his
_FLAGS_EXTRA_NO_XP = 0x40
_FLAGS_EXTRA_TRIGGER = 0x80
_DISPEL_DISEASE = 3
_MECHANIC_SLEEP = 10
_DEFENSE_MAGIC = 1
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000      # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_INTERRUPT_FLAGS_STANDARD = 15               # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1

_ICON_GENERIC = 1
_ICON_LISTENING_MUSIC = 2712                 # Listening to Music 50493
_ICON_PICCOLO = 1610                         # Piccolo of the Flaming Fire 18400
_ICON_SLEEP = 44                             # Sleep 12098
_ICON_SIREN_SONG = 1722                      # Siren's Song 25678
_ICON_BLACK_ROT = 330                        # Black Rot 16448

_SCRIPT_DAMAGE = ('a percent of the reference row (hundredths in the value) through the kit\'s '
                  'spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(10558, **boss_columns(
        'boss_hearthsinger_forresten_rework', 62.859, damage_modifier=3.5,
    ))

# --- Boss-kit creatures ----------------------------------------------------------------------------------------------

# Level 57 beast: ceil(2,784 x 0.35918) = 1,000 (heroic 1,500: stratholme.py `_KIT_ADD_HEROIC`).
gutter_rat_300602 = creature_template(
    300602, 'Gutter Rat', **{
        **KIT_CREATURE, 'faction': _FACTION_FORRESTEN, 'type': 1, 'minlevel': 57, 'maxlevel': 57, 'rank': 0,
        'unit_class': 1, 'unit_flags': 0, 'HealthModifier': 0.35918, 'DamageModifier': 0.4, 'BaseAttackTime': 2000,
        'speed_walk': 1.0, 'speed_run': 1.14286, 'ExperienceModifier': 1.0, 'lootid': 0, 'pickpocketloot': 0,
        'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'ScriptName': 'npc_st_gutter_rat', 'difficulty_entry_1': 310192,
    },
)
for _idx, _display in enumerate(DISPLAYS_FORRESTEN_RATS):
    creature_model(300602, display_id=_display, idx=_idx)

hearth_stalker_300603 = creature_template(
    300603, 'Hearth', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'type': 10,
                         'flags_extra': _FLAGS_EXTRA_NO_XP | _FLAGS_EXTRA_TRIGGER,
                         'ScriptName': 'npc_st_hearth_stalker'},
)
creature_model(300603, display_id=DISPLAY_INVISIBLE_STALKER)

# --- HF4 The Jig: the note and the dance -----------------------------------------------------------------------------

note_206440 = resolve_copy(
    206440, 'Note', School.ARCANE, 'A note of the tune strikes the ground.',
    f'{_HF}, HF4: the note\'s hit, a 4 yd circle with a 1.5 s marker under 2 random players (heroic: every player) '
    'and 2 random floor spots, every beat of The Jig (2 s; 1 s after a missed Crescendo): 20% of the reference row, '
    'the tank too (its own row), 1 Weakened, with the Dance rider (206441), through the registry. Copy of the '
    'resolve spell 205001 (Arcane). Listening to Music 50493\'s SV 11381 (gold stars, 1.9 s: a stand-in for notes, '
    'V-2 FO_LISTENING_MUSIC) on every unit hit: the visible impact.',
    icon=_ICON_LISTENING_MUSIC, visual=FO_LISTENING_MUSIC,
)

dance_206441 = spell(
    id=206441, name='Dance', school=School.ARCANE, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=1500,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_PICCOLO,
    notes=f'{_HF}, HF4: the 1.5 s dance a note\'s hit gives (the registry rider, cast by him on every unit hit). A '
          'DUMMY aura whose script (spell_st_forresten_dance) sets the emote state to the dance (10, '
          'EMOTE_STATE_DANCE) on apply and clears it on remove: the player keeps control (ST: "the player dances for '
          '1.5 sec"; the shared 2 s limit on loss of control is not touched). Dispel none. Piccolo 18400\'s SV 4682 '
          'is a sound only (no model, no animation) and is not wired. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Dancing.', 'Dancing to the tune.', CastingTimeIndex=1, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(dance_206441, 'spell_st_forresten_dance')

# --- HF6 Drowsy and the sleep ----------------------------------------------------------------------------------------

drowsy_206442 = spell(
    id=206442, name='Drowsy', school=School.ARCANE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=6000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SLEEP,
    notes=f'{_HF}, HF6: a non-tank outside the hearth gains a stack every 2 s during The Lullaby (the script, '
          'DungeonKit::AddStacks with him as the caster); at 3 stacks the script removes it and puts the player to '
          'sleep (206443) for 2 s. 6 s, each stack refreshes it, 3 stacks (CumulativeAura 3). A DUMMY aura: the '
          'count is the tell, and the bots\' hearth Stack is the answer. Dispel none, NO_IMMUNITIES. The rats go for '
          'the drowsy first. The script clears it at the song\'s end, on his death, evade and reset. '
          'AuraInterruptFlags CHANGE_MAP. Hibernate 2637\'s SV 4999 (green sleep Zs over the head; Enchanting '
          'Lullaby\'s SV 2576 is red hearts and stays out: V-2 FO_DROWSY_ALT).',
    raw_overrides=kit_raw('Falling asleep. At 3 stacks you sleep for 2 sec.',
                          'Falling asleep. Stay by the hearth.', CastingTimeIndex=1, CumulativeAura=3,
                          SpellVisualID_1=FO_DROWSY_ALT, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

asleep_206443 = spell(
    id=206443, name='Asleep', school=School.ARCANE, dispel=0, mechanic=_MECHANIC_SLEEP,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=2000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=_MECHANIC_SLEEP, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SLEEP,
    notes=f'{_HF}, HF6: the 2 s sleep at three Drowsy stacks (the shared 2 s limit on loss of control), applied by '
          'him through the script. MOD_STUN with the sleep mechanic (sleep and stun immunities and trinkets work), '
          'Dispel none (2 s is not worth a cure), and damage does not wake it (the rats bite sleepers: no '
          'AuraInterruptFlags beyond CHANGE_MAP). Sleep 12098\'s SV 87 (Sleep_State_Head, green Zs: V-2 FO_DROWSY).',
    raw_overrides=kit_raw('Fast asleep for $d.', 'Fast asleep.', CastingTimeIndex=1, SpellVisualID_1=FO_DROWSY,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- HF7 Rat volley and HF11 the big lines ---------------------------------------------------------------------------

rat_line_206444 = resolve_copy(
    206444, 'Rat Line', School.NORMAL, 'A swarm of rats runs through you.',
    f'{_HF}, HF7: a rat line\'s hit, the 2 yd line a Gutter Rat runs out and back (the registry tracks the rat) in '
    'The Piper\'s Tune: 15% of the reference row, the tank too (its own row), 1 Weakened, through the registry. Copy '
    'of the resolve spell 205001 (Physical). Gore 4102\'s SV 39 (a hit flash and a sound, V-1 RG_GORE) on every unit '
    'hit: the visible impact.',
    icon=_ICON_BLACK_ROT, visual=RG_GORE,
)

crescendo_line_206445 = resolve_copy(
    206445, 'Crescendo', School.NORMAL, 'The song swells into a wall of sound.',
    f'{_HF}, HF11: the big line\'s hit, a 6 yd line from him through each non-tank (a 2 s marker, out to his wall, at '
    'most 60 yd) when a Piper\'s Tune Crescendo is not interrupted: 30% of the reference row, the tank too if he '
    'stands in it, 1 Weakened, through the registry. Copy of the resolve spell 205001 (Physical). Siren\'s Song '
    '25678\'s SV 371 (bubbles and a gold ribbon, V-2 FO_SIREN_SONG) on every unit hit.',
    icon=_ICON_SIREN_SONG, visual=FO_SIREN_SONG,
)

# --- HF8 Crescendo ---------------------------------------------------------------------------------------------------

crescendo_206446 = spell(
    id=206446, name='Crescendo', school=School.ARCANE, cast_time_ms=3000, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SIREN_SONG,
    notes=f'{_HF}, HF8: once a song, 5 to 12 s into it, a 3 s cast (emote line 4, "builds toward a crescendo"). '
          'Interruptible: InterruptFlags 15 (movement, pushback, interrupt, auto-attack) and PreventionType 1 (a '
          'silence stops it); the descriptor\'s interrupt list, priority 3 (top), every song + break. Completed '
          '(OnSpellCast): The Jig goes to a beat a second, The Lullaby\'s hearth moves 15..20 yd with a 2 s glow, '
          'The Piper\'s Tune adds a 6 yd line through each non-tank (206445), and on heroic four more Gutter Rats; '
          'stopped (OnSpellFailed): nothing, the reward. A DUMMY effect on himself, no damage. Siren\'s Song 25678\'s '
          'SV 371 plays on him as the bar starts (V-2 FO_SIREN_SONG).',
    raw_overrides=kit_raw('Builds toward a crescendo. If the cast finishes, the song turns on you.',
                          InterruptFlags=_INTERRUPT_FLAGS_STANDARD, PreventionType=_PREVENTION_SILENCE,
                          SpellVisualID_1=FO_SIREN_SONG),
)

# --- HF3 Plague Bite -------------------------------------------------------------------------------------------------

plague_bite_206447 = spell(
    id=206447, name='Plague Bite', school=School.NATURE, dispel=_DISPEL_DISEASE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=100, die_sides=0,
                    amplitude=1000, implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_DAMAGE)],
    spell_icon_id=_ICON_BLACK_ROT,
    notes=f'{_HF}, HF3: every Gutter Rat bite that lands adds a stack (npc_st_gutter_rat::DamageDealt, '
          'DungeonKit::AddStacks with him as the caster, so every rat\'s bites add up), up to 5 (CumulativeAura 5), '
          '10 s, each stack refreshes it. Every second 1% of the reference row a stack (base point 100 = 1.00% in '
          'hundredths, heroic the same: EffectMiscValueB 0), the tank row on the tank, through '
          'spell_dungeon_refflat_periodic; ignores caster modifiers. A Disease: the dispel list, priority 1 (a '
          'reward, ST). Black Rot 16448\'s SV 717 (a green puff on the chest, V-2 FO_BLACK_ROT; the stock Black Rot '
          'is the rat\'s retired kit). AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Diseased by a rat. Nature damage over time that grows with every bite.',
                          'Taking Nature damage every $t1 sec.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          CumulativeAura=5, SpellVisualID_1=FO_BLACK_ROT, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(plague_bite_206447, 'spell_dungeon_refflat_periodic')

# --- HF5 the hearth --------------------------------------------------------------------------------------------------

hearth_glow_206448 = spell(
    id=206448, name='Hearth', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_HF}, HF5 / HF10: the hearth\'s glow, a DUMMY aura on the stalker 300603 (the script casts it on the '
          'stalker, triggered, when the hearth lights; a moved hearth is a new stalker, so the glow relights). '
          'WP-V-2\'s FlameZone orange disc at 8 yd (SV 90508, a StateKit: SV_FLAMEZONE_8_STATE). It reaches nobody; '
          'the registry Stack owns the circle (the safe place against Drowsy). The stalker despawns when the '
          'hearth moves or the song ends, which ends the aura.',
    raw_overrides=kit_raw('A hearth glows here.', 'A hearth glows here.', instant=True, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=SV_FLAMEZONE_8_STATE),
)
