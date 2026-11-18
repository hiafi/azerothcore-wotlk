"""
Blackrock Depths build WP-D7: Pyromancer Loregrain (9024), "Franclorn's last stand", normal and heroic
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 / s3.5 / s3.6 / s3.8 rows D7, s7 #21, s8
#18 / #36; build spec docs/dungeons/blackrock-depths-2-shadowforge-city.md S2 165-219, the moving ward S2 147-156,
rulings 37-39 and 91). WP-D7 owns this file (its spells: kSpellsLoregrain 211020-211049 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h only; LoregrainLogic.h names the same ids).

- 9024 Pyromancer Loregrain: boss_pyromancer_loregrain_rework (SmartAI off: the S0 SQL rev drops his four rows), the
  build spec's normal health (130k = HealthModifier 78.313 on the level 52 mage class base 1,660), DamageModifier 3.5
  (the stock base value), stun immunity 1972, INSTANCE_BIND. Heroic 220k is WP-H's override
  (source/world/dungeons/blackrock_depths.py). Scorching Totem 15038 and the stock casts are retired from his kit: the
  copies below replace Molten Blast 15095 and Flame Shock 15616 (15616 is on DD's double-use list: rule 15), the new
  Fire Ward replaces 15041, the Fury meter replaces his 15288 addon aura (removed by the SQL rev). His loot is kept.
- 300792 Defiling Totem (LG4): the stock Scorching Totem's display (4589; 9637 spawns nowhere), level 52, 4,000 at 5
  players (HealthModifier 1.687 on the level 52 warrior base 2,371; heroic 7,000 is WP-H's override, difficulty_entry_1
  310403 from STAGE-H-REPORT section 3), type totem, faction 54, rooted where the boss plants it, no melee, no loot,
  no XP, stun immunity set 1972; npc_brd_defiling_totem (a NullCreatureAI). Kill order.
- 9542 Franclorn's Spirit: the stock entry (no spawns), summoned by the script at the pull (made not selectable, not
  attackable, rooted); no template change (D10 summons a short-lived copy too).

Spells. The tide, the Wrath, the splash and the patch hits are dungeon copies of the mod-boss-mechanics resolve spell
(the registry's percent of the reference row; the combat log names the mechanic). Molten Blast, Flame Shock and
Searing Bolt carry their percent in hundredths for the kit's spell_dungeon_refflat_damage / _periodic (normal in the
effect, heroic in EffectMiscValueB; custom ids are never DD-scaled). The rest are cast bars, looks and the meter:

  211020  Fire Tide            LG1 the tide's hit: resolve copy (Fire), 30% / 45% x (1 + Fury / 100), at most 75%
  211021  Fire Tide            LG1 the 4 s cast bar (Physical: never locked by a Molten Blast kick; no kick of its own)
  211022  Wrath of Ragnaros    LG7 the 4 s cast bar (normal, section 7 #21)
  211023  Wrath of Ragnaros    LG7 the 2 s cast bar (heroic)
  211024  Wrath of Ragnaros    LG7 the Wrath's hit: resolve copy (Fire), the tide's rule at Fury 100 (60% / 75%)
  211025  Franclorn's Ward     LG3 the spirit throws Loregrain clear (a look on him; the jump is the script's)
  211026  Defiling Presence    LG4 the totem's tooltip aura (DUMMY, no effect)
  211027  Molten Splash        LG5 the lob from Loregrain to the marked spot's stalker (look)
  211028  Molten Splash        LG5 the 4 yd hit: resolve copy (Fire), 20% / 35%, Weakened
  211029  Molten Splash        LG5 the patch's tick: resolve copy (Fire), 4% / 6% a second (gap 20 default)
  211030  Molten Splash        LG5 the patch's look: the 4 yd lava pool state on a stalker
  211031  Fury of Ragnaros     LG6 the meter: a stacking DUMMY on him, 1-100 stacks
  211032  Fire Ward            LG9 absorbs 8% of his health from any school (the amount is the script's), Magic
  211033  Molten Blast         LG8 2 s, interruptible, Fire: 15% / 25% of the target's row
  211034  Flame Shock          LG10 Fire, Magic: 6% / 10%, then 3% / 5% every 3 s for 12 s
  211035  Searing Bolt         LG3 his answer while he holds at the ward's edge with his victim out of reach: 10% / 15%
                               every 2 s (rule 10: no free damage window)
  211036-211049 spare.

Visual ids are WP-V-1's (._visuals) except the kept copies' own stock looks (Molten Blast 15095's SV 305, Flame Shock
15616's SV 516: a shared-file request asks V for LG_MOLTEN_BLAST / LG_FLAME_SHOCK constants). The repel and the totem's
aura have no look of their own (the jump and the totem are the looks). Every look is unconfirmed until seen in game.
Tooltips are number-free.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT, ATTR2_IGNORE_LINE_OF_SIGHT
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    LG_FLAME_SHOCK,
    LG_MOLTEN_BLAST,
    DISPLAY_DEFILING_TOTEM,
    LG_FIRE_TIDE,
    LG_FIRE_WARD,
    LG_FURY_OF_RAGNAROS,
    LG_MOLTEN_SPLASH,
    LG_MOLTEN_SPLASH_PATCH,
    LG_WRATH_OF_RAGNAROS,
)

creature_template_columns(9024, **boss_columns(
    'boss_pyromancer_loregrain_rework', 78.313, damage_modifier=3.5,
))

_LG = 'Blackrock Depths build WP-D7 (Pyromancer Loregrain)'

_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage / _periodic (DungeonKit::RefFlatOn)')

_TARGET_UNIT_TARGET_ENEMY = 6
_DEFENSE_MAGIC = 1
_DISPEL_MAGIC = 1
_INTERRUPT_FLAGS_KICKABLE = 15              # the stock casters' set (Molten Blast 15095)
_PREVENTION_SILENCE = 1
_SCHOOL_MASK_ALL = 127                      # SCHOOL_ABSORB misc: every school
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_CREATURE_TYPE_TOTEM = 11
_FLAGS_EXTRA_NO_XP = 0x40

# LoregrainLogic.h numbers (lib/test_blackrock_depths_loregrain.py pins them against the header).
_TIDE_WARN_MS = 4000                        # kTideWarnMs
_WRATH_WARN_MS = (4000, 2000)               # kWrathWarnMs
_MOLTEN_BLAST = (1500, 2500)                # kMoltenBlastPct, hundredths
_MOLTEN_BLAST_CAST_MS = 2000                # kMoltenBlastCastMs
_MOLTEN_BLAST_RANGE = 30.0                  # kMoltenBlastRangeYd
_FLAME_SHOCK = (600, 1000)                  # kFlameShockPct
_FLAME_SHOCK_TICK = (300, 500)              # kFlameShockTickPct
_FLAME_SHOCK_TICK_MS = 3000                 # kFlameShockTickMs
_FLAME_SHOCK_MS = 12000                     # kFlameShockMs
_FLAME_SHOCK_RANGE = 20.0                   # kFlameShockRangeYd
_SEARING_BOLT = (1000, 1500)                # kSearingBoltPct
_FIRE_WARD_MS = 30000                       # kFireWardMs
_FURY_MAX = 100                             # kFuryMax

_ICON_FLAME_WAVE = 2128                     # Flame Wave 33804
_ICON_WRATH = 816                           # Wrath of Ragnaros 20566
_ICON_FURY = 1487                           # Fury of Ragnaros 15288
_ICON_FIRE_WARD = 16                        # Fire Ward 15041
_ICON_MOLTEN_BLAST = 11                     # Molten Blast 15095
_ICON_FLAME_SHOCK = 678                     # Flame Shock 15616
_ICON_LAVA_BURST = 3064                     # Lava Burst 51505
_ICON_SCORCHING_TOTEM = 680                 # Scorching Totem 15038
_ICON_FIRE_BLAST = 12                       # Fire Blast 16144

_LAVA_BURST_SPEED = 24.0                    # Lava Burst 51505's missile speed

# --- 300792 Defiling Totem -------------------------------------------------------------------------------------------

defiling_totem_300792 = creature_template(
    300792, 'Defiling Totem', **{
        **KIT_CREATURE, 'minlevel': 52, 'maxlevel': 52, 'rank': 0, 'unit_class': 1, 'type': _CREATURE_TYPE_TOTEM,
        'unit_flags': 0, 'HealthModifier': 1.687, 'DamageModifier': 0.0, 'BaseAttackTime': 2000,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'detection_range': 0.0, 'lootid': 0, 'pickpocketloot': 0,
        'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
        'ScriptName': 'npc_brd_defiling_totem', 'difficulty_entry_1': 310403,
    },
)
creature_model(300792, display_id=DISPLAY_DEFILING_TOTEM)

# --- LG1 Fire Tide, LG7 Wrath of Ragnaros ----------------------------------------------------------------------------

fire_tide_hit_211020 = resolve_copy(
    211020, 'Fire Tide', School.FIRE, 'Ragnaros\'s fire floods the corridor.',
    f'{_LG}, LG1: the tide\'s hit on everyone outside Franclorn\'s Ward (a registry Donut from the ward\'s edge to 45 '
    'yd, anchored on the ward\'s spot, its inner radius locked at the warning start): 30% (heroic 45%) of the row x (1 '
    '+ Fury / 100), at most 75%, the tank on its own row (ruling 88), Weakened. Copy of the resolve spell 205001 '
    '(Fire). No impact look (the cast bar 211021 carries the tide\'s look).',
    icon=_ICON_FLAME_WAVE,
)

fire_tide_cast_211021 = cast_bar(
    211021, 'Fire Tide', _TIDE_WARN_MS, 'Ragnaros\'s fire is about to flood the corridor. Get into Franclorn\'s Ward.',
    f'{_LG}, LG1: the 4 s glow before each Fire Tide (beside the yell, the boss emote of the ward\'s move and the '
    'registry markers). Physical so a Molten Blast kick\'s Fire lockout never stops it, and not interruptible itself '
    '(cast_bar: the registry owns the hit). Flame Wave 75413\'s SV 13372 (a rune base and a fire nova at the boss).',
    icon=_ICON_FLAME_WAVE, visual=LG_FIRE_TIDE,
)

wrath_cast_normal_211022 = cast_bar(
    211022, 'Wrath of Ragnaros', _WRATH_WARN_MS[0], 'The Firelord\'s fury overflows. Get into Franclorn\'s Ward.',
    f'{_LG}, LG7 (normal): the Wrath\'s 4 s cast bar (section 7 #21 default: the normal ladder keeps a 60% hit to a '
    '4 s warning). Physical, not interruptible. Fire Blast 16144\'s SV 143 (hands and a chest flash).',
    icon=_ICON_WRATH, visual=LG_WRATH_OF_RAGNAROS,
)

wrath_cast_heroic_211023 = cast_bar(
    211023, 'Wrath of Ragnaros', _WRATH_WARN_MS[1], 'The Firelord\'s fury overflows. Get into Franclorn\'s Ward.',
    f'{_LG}, LG7 (heroic): the Wrath\'s 2 s cast bar (S2 188; heroic may pass the ladder, ruling 89). Physical, not '
    'interruptible. Fire Blast 16144\'s SV 143.',
    icon=_ICON_WRATH, visual=LG_WRATH_OF_RAGNAROS,
)

wrath_hit_211024 = resolve_copy(
    211024, 'Wrath of Ragnaros', School.FIRE, 'The Firelord\'s wrath erupts.',
    f'{_LG}, LG7: the Wrath\'s hit, an extra Fire Tide at Fury 100 (no ward move, section 7 #21): the tide\'s rule at '
    'Fury 100, 60% (heroic 75%, the cap), Weakened; the Fury then drops to 30, and on heroic the ward cracks 1 yd for '
    'the fight when it lands. Copy of the resolve spell 205001 (Fire).',
    icon=_ICON_WRATH,
)

# --- LG3 Franclorn's Ward --------------------------------------------------------------------------------------------

ward_repel_211025 = spell(
    id=211025, name='Franclorn\'s Ward', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FIRE_WARD,
    notes=f'{_LG}, LG3: Franclorn\'s Spirit throws Loregrain out of the ward (S2 156: "the spirit repels him"), cast '
          'by the spirit on him (triggered) as boss_pyromancer_loregrain_rework jumps him to a computed spot in the '
          'corridor (DungeonKit::JumpTo, RepelLanding in LoregrainLogic.h). No effect; no look of its own yet (the '
          'jump is the look; a shared-file request asks V for one).',
    raw_overrides=kit_raw('The architect\'s spirit casts the defiler out.', instant=True, InterruptFlags=0,
                          PreventionType=0, AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- LG4 Defiling Totem ----------------------------------------------------------------------------------------------

defiling_presence_211026 = spell(
    id=211026, name='Defiling Presence', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SCORCHING_TOTEM,
    notes=f'{_LG}, LG4: the Defiling Totem\'s tooltip aura, cast by the totem on itself (triggered) when the boss '
          'plants it. No effect: the script shrinks the ward 1 yd and feeds 2 Fury a second per living totem. Not '
          'dispellable; it dies with the totem.',
    raw_overrides=kit_raw('Defiles Franclorn\'s Ward and feeds the Firelord\'s fury.',
                          'Shrinking Franclorn\'s Ward and feeding Loregrain\'s fury.', CastingTimeIndex=1,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- LG5 Molten Splash -----------------------------------------------------------------------------------------------

splash_lob_211027 = spell(
    id=211027, name='Molten Splash', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_LAVA_BURST,
    notes=f'{_LG}, LG5: the lob, cast by Loregrain (triggered) on the stalker at each marked spot as the 2 s marker '
          'starts: Lava Burst 51505\'s SV 11565 (a real lob and a molten splash), its missile speed 24 yd/s (a 20 yd '
          'lob lands in under a second; the registry\'s 2 s circle owns the hit). No effect.',
    raw_overrides=kit_raw('Molten rock arcs toward the ground.', instant=True, InterruptFlags=0, PreventionType=0,
                          Speed=_LAVA_BURST_SPEED, SpellVisualID_1=LG_MOLTEN_SPLASH, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

splash_hit_211028 = resolve_copy(
    211028, 'Molten Splash', School.FIRE, 'Molten rock splashes the ground.',
    f'{_LG}, LG5: the 4 yd circle at each of 2 (heroic 3) random players\' spots (the tank included, ruling 88), 2 s: '
    '20% (heroic 35%) of the row, the tank on its own row, Weakened. Copy of the resolve spell 205001 (Fire). The lob '
    '211027 is the look.',
    icon=_ICON_LAVA_BURST,
)

patch_hit_211029 = resolve_copy(
    211029, 'Molten Splash', School.FIRE, 'The molten rock burns on the ground.',
    f'{_LG}, LG5: the patch\'s tick, a second from a second after the splash lands: 4% (heroic 6%) of the row a '
    'second on everyone inside the 4 yd patch (gap 20, the section 7 #21 default), no Weakened (a lingering patch '
    'never applies it). The patch burns until the next tide washes it (its center outside that tide\'s ward) or, '
    'sheltered in the ward, for the fight. Copy of the resolve spell 205001 (Fire).',
    icon=_ICON_LAVA_BURST,
)

patch_look_211030 = spell(
    id=211030, name='Molten Splash', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_LAVA_BURST,
    notes=f'{_LG}, LG5: the patch\'s look, a DUMMY aura the patch\'s stalker (the shared stalker 300796) casts on '
          'itself (triggered) as the splash lands: the shipped 4 yd lava pool state (SV 90606, Blackrock Spire\'s '
          'ladder). No effect; the stalker despawns with the patch.',
    raw_overrides=kit_raw('Molten rock.', 'Molten rock.', CastingTimeIndex=1, SpellVisualID_1=LG_MOLTEN_SPLASH_PATCH,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- LG6 Fury of Ragnaros --------------------------------------------------------------------------------------------

fury_211031 = spell(
    id=211031, name='Fury of Ragnaros', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FURY,
    notes=f'{_LG}, LG6: the Fury meter (the stock addon aura 15288 is removed by the SQL rev): one stack per point, '
          '1-100 (CumulativeAura 100), set by the script (DungeonKit::AddStacks, the boss as caster): +10 per Molten '
          'Blast landed, +3 a second while Fire Ward holds, +2 a second per living Defiling Totem; -15 per Molten '
          'Blast interrupted, -10 per totem killed, -20 when Fire Ward breaks or is purged. Each Fire Tide hits for '
          '(1 + Fury / 100) times its base; at 100 Wrath of Ragnaros fires and the meter drops to 30. No effect of its '
          'own; not dispellable. Fury of Ragnaros 15288\'s SV 141 (a glow as stacks change).',
    raw_overrides=kit_raw('The Firelord\'s fury builds. At its peak it erupts.',
                          'Each stack makes the Fire Tide hit harder. At 100 the Firelord\'s wrath erupts.',
                          CastingTimeIndex=1, CumulativeAura=_FURY_MAX, SpellVisualID_1=LG_FURY_OF_RAGNAROS,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- LG9 Fire Ward ---------------------------------------------------------------------------------------------------

fire_ward_211032 = spell(
    id=211032, name='Fire Ward', school=School.FIRE, dispel=_DISPEL_MAGIC, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_FIRE_WARD_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, base_points=0, die_sides=0,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Fire Ward: the absorb is 8% of his maximum health, set by the script')],
    spell_icon_id=_ICON_FIRE_WARD,
    notes=f'{_LG}, LG9 (the stock Fire Ward 15041 changed): 5 s after the pull, then every 30 s, cast by '
          'boss_pyromancer_loregrain_rework on himself (triggered, CastCustomSpell: base point 0 = 8% of his maximum '
          'health, 10,400 normal / 17,600 heroic) absorbing any school. Magic: the purge list (priority 2). While it '
          'holds the Fury gains 3 a second; when it breaks or is purged with more than 0.75 s left the Fury drops 20. '
          '30 s (the next cast replaces it). Fire Reflector 23097\'s SV 6764 (the lasting red ribbons, V-1: never the '
          'one-shot SV 290).',
    raw_overrides=kit_raw('Absorbs damage of any school.', 'Absorbs damage of any school.', CastingTimeIndex=1,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=LG_FIRE_WARD, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- LG8 Molten Blast ------------------------------------------------------------------------------------------------

molten_blast_211033 = spell(
    id=211033, name='Molten Blast', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=_MOLTEN_BLAST_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_MOLTEN_BLAST_RANGE,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_MOLTEN_BLAST[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_MOLTEN_BLAST,
    notes=f'{_LG}, LG8 (a copy of the stock Molten Blast 15095, gap 36 "stock rescaled"): 6 s after the pull, then '
          'every 12 s on both difficulties (ruling 91), on a random player within 30 yd in his sight (the tank '
          'included): 2 s, 15% (heroic 25%) of the target\'s row (1500 / 2500 hundredths; RefFlatOn: the tank row for '
          'the tank), Fire. Interruptible and silence-preventable (InterruptFlags 15, PreventionType silence; his '
          'immunity set 1972 lets both work): the interrupt list (priority 2, heroic 3: a reward on normal, expected '
          'on heroic). Landed it feeds 10 Fury, interrupted it takes 15. Ignores his modifiers. The stock SV 305.',
    raw_overrides=kit_raw('Hurls a blast of molten fire.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                          EffectMiscValueB_1=_MOLTEN_BLAST[1], SpellVisualID_1=LG_MOLTEN_BLAST,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(molten_blast_211033, 'spell_dungeon_refflat_damage')

# --- LG10 Flame Shock ------------------------------------------------------------------------------------------------

flame_shock_211034 = spell(
    id=211034, name='Flame Shock', school=School.FIRE, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=_FLAME_SHOCK_RANGE, duration_ms=_FLAME_SHOCK_MS,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_FLAME_SHOCK[0] - 1, die_sides=1,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=_FLAME_SHOCK_TICK[0],
               die_sides=0, amplitude=_FLAME_SHOCK_TICK_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               potency_excluded=_SCRIPT_REFFLAT),
    ],
    spell_icon_id=_ICON_FLAME_SHOCK,
    notes=f'{_LG}, LG10 (a copy of the stock Flame Shock 15616, which is on DD\'s double-use list: rule 15; gap 36 '
          '"stock rescaled"): 9 s after the pull, then every 8-21 s on a random player within 20 yd in his sight (the '
          'tank included): 6% (heroic 10%) of the target\'s row, then 3% (heroic 5%) every 3 s for 12 s, Fire. Magic: '
          'the dispel list (priority 1, a reward). Ignores his modifiers. The stock SV 516.',
    raw_overrides=kit_raw('Burns the target with fire, and more over time.', 'Burning. Taking fire damage every $t2 '
                          'sec.', instant=True, InterruptFlags=0, DefenseType=_DEFENSE_MAGIC,
                          EffectMiscValueB_1=_FLAME_SHOCK[1], EffectMiscValueB_2=_FLAME_SHOCK_TICK[1],
                          SpellVisualID_1=LG_FLAME_SHOCK, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(flame_shock_211034, 'spell_dungeon_refflat_damage', 'spell_dungeon_refflat_periodic')

# --- LG3 Searing Bolt (rule 10) --------------------------------------------------------------------------------------

searing_bolt_211035 = spell(
    id=211035, name='Searing Bolt', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_SEARING_BOLT[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_FIRE_BLAST,
    notes=f'{_LG}, LG3 (rule 10, no free damage window; not in the build spec, a designer question): while Loregrain '
          'holds at the ward\'s edge (his victim in the ward) and his victim is out of his melee reach, he casts this '
          'on it every 2 s (triggered): 10% (heroic 15%) of the target\'s row (the tank\'s, usually; RefFlatOn), '
          'Fire, ignores his modifiers, not interruptible. The stock Molten Blast SV 305 (a fire bolt).',
    raw_overrides=kit_raw('Sears a foe the defiler cannot reach.', instant=True, InterruptFlags=0, PreventionType=0,
                          DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=_SEARING_BOLT[1],
                          SpellVisualID_1=LG_MOLTEN_BLAST, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(searing_bolt_211035, 'spell_dungeon_refflat_damage')
