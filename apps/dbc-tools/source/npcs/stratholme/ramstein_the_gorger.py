"""
Stratholme build WP-S13: Ramstein the Gorger (10439), "Feeding Time" and "Bursting at the Seams"
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows RG, s3.5 row S13, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 3215-3483, RG1-RG5). WP-S13 owns this file (its spells: kSpellsRamstein
206685-206704 in modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; RamsteinLogic.h names the same ids;
its creatures: the Half-Digested Corpse 300586 and the gut puddle stalker 300587, and the meat 11030's columns).

- 10439 Ramstein the Gorger: boss_ramstein_the_gorger_rework (SmartAI off; WP-S13's SQL rev drops stock rows 10439 x4
  and the walk-in action list 1043900 x8), normal HealthModifier 66.794 (210k on the level 61 warrior base 3,144), stun
  immune (1972; the build spec asked for -273, handoff s8 #5 replaces it), INSTANCE_BIND. DamageModifier 9: the stock
  value (WP-T tunes melee). Heroic health 230k and the tier's melee are WP-H's heroic template
  (source/world/dungeons/stratholme.py).
- 11030 Mindless Undead (his meat; stock id, his alone since the instance's Mindless stage is gone): npc_st_meat (a
  NullCreatureAI: the boss script walks it and eats it, it never attacks), SmartAI off (the stock "attack start" row
  goes in the SQL rev), level 57, HealthModifier 1.43678: ceil(2,784 x 1.43678) = 4,000 (the level 57 warrior base).
  Fear immunity (-93) stays, so roots, stuns, slows, knockbacks and novas all work on it (the class tool reward of
  RG1). Heroic 5,000 is WP-H's override (source/world/dungeons/stratholme.py). The heroic copy is made from the stock
  row, so it keeps the stock AIName; the script name comes from the normal entry (Creature::GetScriptId), which is what
  binds npc_st_meat on heroic.
- 300586 Half-Digested Corpse (RG3 crawler): a combat add the tear spills, zombie display 1201 (ZombieSkinGreen,
  runner-up 1200), level 60 elite undead, HealthModifier 0.98296: ceil(3,052 x 0.98296) = 3,000. Slow (speed_run 0.5 =
  3.5 yd/s, the meat's pace); melee on a random nearby player (npc_st_half_digested_corpse). Crowd control works on
  it (no immunity set). Heroic 4,000 is WP-H's `_KIT_ADD_HEROIC` (applied because this file declares it), and its row
  names its heroic entry (difficulty_entry_1 310191: the lock's predicted id; wave 1 mints Web Cocoon 310189, Ice Tomb
  310190, then this one).
- 300587 Gut puddle stalker (RG3): an invisible helper (KIT_HELPER, display 11686) that carries the puddle's look
  aura 206691 for 20 s. Not selectable or attackable, no heroic template (handoff s3.3: stalkers run on their normal
  entry).

Spells (Spell.dbc 3.3.5 for every stock id quoted; looks from ._visuals, all stock or WP-V-1's minted rows):

  206685  Gorge                  RG2 the bite's look: he casts it on himself as the meal begins (triggered).
                                 Cannibalize 20578's SV 5724 (a channel kit: unconfirmed on an instant spell, gap 21)
  206686  Gorge                  RG2 the meal: heals him 3% / 4% of his maximum health (half for a heroic corpse, none
                                 for a returning crawler), base point 0 from the script
  206687  Gorged                 RG2 +15% size and +10% damage dealt per stack, 8 stacks (heroic 10); the script caps it
  206688  Bursting at the Seams  RG3 the tear's look: Gore 4102's SV 39 (a hit flash and a sound), on himself
  206689  Exposed                RG3 +50% damage taken for 8 s (heroic 6 s): the reward window after the tear
  206690  Gut Puddle             RG3 the puddle's tick: resolve copy, Nature, 4% a second, Weakened once per player
  206691  Gut Puddle             RG3 the puddle's look on the stalker (the goo_flow_state row at a 6 yd radius)
  206692  Trample                RG4 the stomp's hit: resolve copy, Physical, 25% / 30% + 3% per stack, Weakened
  206693  Trample                RG4 the stomp's look: War Stomp 45's SV 2355 (a ground crack), on himself
  206694  Trample                RG4 the tank's share: the stock weapon hit (5568's WEAPON_DAMAGE as 100% weapon damage)
  206695  Knockout               RG5 stock 17307 without its stun: the weapon hit and the knockback
  206696-206704 spare
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import self_visual
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_CRAWLER,
    DISPLAY_INVISIBLE_STALKER,
    RG_CANNIBALIZE,
    RG_EXPOSE_WEAKNESS,
    RG_GORE,
    RG_TRAMPLE,
    SV_GUT_PUDDLE_STATE,
)

_S13 = 'Stratholme build WP-S13 (Ramstein)'

creature_template_columns(10439, **boss_columns(
    'boss_ramstein_the_gorger_rework', 66.794, damage_modifier=9,
))

# The meat: level 57 warrior base 2,784: ceil(2,784 x 1.43678) = 4,000 (RG1). The stock row's SmartAI (one "attack
# start" row) goes in the SQL rev.
creature_template_columns(11030, ScriptName='npc_st_meat', AIName='', minlevel=57, maxlevel=57,
                          HealthModifier=1.43678)

# --- Boss-kit creatures ----------------------------------------------------------------------------------------------

# Level 60 elite undead warrior: ceil(3,052 x 0.98296) = 3,000 (heroic 4,000: stratholme.py `_KIT_ADD_HEROIC`).
half_digested_corpse_300586 = creature_template(
    300586, 'Half-Digested Corpse', **{
        **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'type': 6, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': 0.98296, 'DamageModifier': 1.0, 'BaseAttackTime': 2000, 'speed_walk': 1.4,
        'speed_run': 0.5, 'ExperienceModifier': 1.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0,
        'maxgold': 0, 'ScriptName': 'npc_st_half_digested_corpse', 'difficulty_entry_1': 310191,
    },
)
creature_model(300586, display_id=DISPLAY_CRAWLER)

_FLAGS_EXTRA_NO_XP = 0x40
_FLAGS_EXTRA_TRIGGER = 0x80

gut_puddle_stalker_300587 = creature_template(
    300587, 'Gut Puddle', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'type': 10,
                             'flags_extra': _FLAGS_EXTRA_NO_XP | _FLAGS_EXTRA_TRIGGER,
                             'ScriptName': 'npc_st_gut_puddle'},
)
creature_model(300587, display_id=DISPLAY_INVISIBLE_STALKER)

# --- Constants -------------------------------------------------------------------------------------------------------
_TARGET_UNIT_TARGET_ENEMY = 6

_ATTR0_IS_ABILITY = 0x00000010
_ATTR1_NO_THREAT = 0x00000400
_ATTR3_NOT_A_PROC = 0x00000200

_PREVENTION_PACIFY = 2
_DEFENSE_MELEE = 2
_SCHOOL_MASK_ALL = 127

_ICON_CANNIBALIZE = 146     # Cannibalize 20578
_ICON_GENERIC = 1
_ICON_TRAMPLE = 168         # Trample 5568
_ICON_KNOCKOUT = 314        # Knockout 17307
_ICON_WAR_STOMP = 50        # War Stomp
_SV_TRAMPLE_STOCK = 672     # Trample 5568's SpellVisual (the tank's weapon hit)
_SV_KNOCKOUT = 1187         # Knockout 17307's SpellVisual

_SCRIPT_HEAL = 'Stratholme: a percent of his own health, base point 0 set by boss_ramstein_the_gorger_rework'

# --- RG2 Gorge -------------------------------------------------------------------------------------------------------
gorge_look_206685 = self_visual(
    206685, 'Gorge', RG_CANNIBALIZE,
    f'{_S13} RG2 Gorge: the bite\'s look. He casts it on himself (triggered, instant) as a meat reaches him (3 yd, or '
    'his reach once he is big), 1.5 s before the meal lands, with the emote line 1 beside it. He fights on through '
    "the bite: it is not a cast. Cannibalize 20578's SpellVisual 5724 (a channel kit with star particles at the "
    'base, 2.8 s; on an instant spell it may show nothing: build spec gap 21, an in-game check). Look only.',
    icon=_ICON_CANNIBALIZE,
)

gorge_heal_206686 = spell(
    id=206686, name='Gorge', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_SCRIPT_HEAL)],
    spell_icon_id=_ICON_CANNIBALIZE,
    notes=f'{_S13} RG2 Gorge: the meal lands 1.5 s after the bite began. A meat that reached him heals him 3% (heroic '
          '4%) of his maximum health (6,300 / 9,200); a heroic corpse he bites where he stands, half of that; a '
          'crawler that came back, none (a stack only). Cast triggered on himself with base point 0 set from the '
          'script (a percent of his own health). Ignores caster modifiers; the healing-reduction effects on him '
          '(Mortal Strike, Wound Poison) still count.',
    raw_overrides=kit_raw('Eats the dead and heals.', instant=True, InterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

gorged_206687 = spell(
    id=206687, name='Gorged', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_SCALE, base_points=15, die_sides=0,
               implicit_target_a=TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=10, die_sides=0,
               misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_CANNIBALIZE,
    notes=f'{_S13} RG2 Gorged: +1 stack for every meal (a meat, a heroic corpse, a returning crawler), up to 8 (heroic '
          '10; the script caps it, DungeonKit::AddStacks). Per stack +15% size (SPELL_AURA_MOD_SCALE: his stock 2.0 '
          'grows to 4.4 at 8 stacks and 5.0 at 10) and +10% damage dealt (SPELL_AURA_MOD_DAMAGE_PERCENT_DONE, every '
          'school: it raises his melee, Knockout and the tank\'s Trample hit; the custom percent hits ignore caster '
          'modifiers, so the reference-sized hits stay exact). The script also reads the count for the Trample '
          'radius and percent and the number of crawlers the tear spills. The tear removes every stack. Until then it '
          'lasts the fight, not dispellable.',
    raw_overrides=kit_raw('Increases size by $s1% and damage dealt by $s2% per application.',
                          'Size increased by $s1% and damage dealt by $s2%.', instant=True, CumulativeAura=10,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- RG3 Bursting at the Seams ---------------------------------------------------------------------------------------
seams_look_206688 = self_visual(
    206688, 'Bursting at the Seams', RG_GORE,
    f'{_S13} RG3 Bursting at the Seams: the tear\'s look (emote line 2 beside it), cast on himself (triggered) as the '
    "seam opens. Gore 4102's SpellVisual 39 (DecisiveStrike: a hit flash and a sound). Look only.",
    icon=_ICON_GENERIC,
)

exposed_206689 = spell(
    id=206689, name='Exposed', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=8000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=50,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Exposed: a flat +50% damage taken, not a damage or heal value')],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_S13} RG3 Exposed: after the tear his guts are open and he takes 50% more damage from every school '
          '(SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN) for 8 s (heroic 6 s: DungeonKit::ShortenAura right after the cast). '
          'The same length however fat he was, so feeding him never pays. A debuff on him, so the group reads it in '
          "his debuff list; mechanic none, dispel none. Expose Weakness 7140's SpellVisual 603 (shadow hands, a "
          'shadow burst and a tint).',
    raw_overrides=kit_raw('Takes $s1% more damage from all sources.', 'Damage taken increased by $s1%.', instant=True,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=RG_EXPOSE_WEAKNESS),
)

gut_puddle_tick_206690 = resolve_copy(
    206690, 'Gut Puddle', School.NATURE, 'Guts burn your feet.',
    f'{_S13} RG3 Gut puddle: the tick of the 6 yd puddle under him at the tear, every 1 s for 20 s, 4% of the '
    'non-tank row (the tank row on the tank: it hits anyone), Weakened once per player per puddle '
    '(WeakenedOncePerPlayer), after a 1 s grace. A lingering zone, outline only until it arms. Resolve copy (Nature) '
    'of the mod-boss-mechanics spell 205001. No impact look (a tick every second; the puddle is the look).',
    icon=_ICON_GENERIC,
)

gut_puddle_look_206691 = spell(
    id=206691, name='Gut Puddle', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_S13} RG3 Gut puddle: the look, a DUMMY aura on the stalker 300587 (the script casts it on the stalker '
          "at the tear, triggered). SV 90505 is WP-V-1's goo_flow_state StateKit at 0.25 (12 yd across, the 6 yd "
          'puddle). It reaches nobody; the registry zone (206690) owns the ticks. The stalker despawns after 20 s, '
          'which ends the aura.',
    raw_overrides=kit_raw('A puddle of guts.', 'A puddle of guts.', instant=True, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=SV_GUT_PUDDLE_STATE),
)

# --- RG4 Trample -----------------------------------------------------------------------------------------------------
trample_hit_206692 = resolve_copy(
    206692, 'Trample', School.NORMAL, 'The ground shakes under his weight.',
    f'{_S13} RG4 Trample: the stomp\'s hit, 1.5 s after the rear-up: a circle on him of 10 yd + 1 yd per Gorged '
    'stack (read as the rear-up begins), 25% (heroic 30%) + 3% per stack of the non-tank row, Weakened, never the '
    'tank (TankExempt: the tank takes 206694). Resolve copy (Physical) of the mod-boss-mechanics spell 205001. '
    "Gore 4102's SpellVisual 39 (a hit flash and a sound) on every unit hit: the visible impact.",
    icon=_ICON_TRAMPLE, visual=RG_GORE,
)

trample_look_206693 = self_visual(
    206693, 'Trample', RG_TRAMPLE,
    f'{_S13} RG4 Trample: the stomp\'s look, cast on himself (triggered) as the circle resolves. War Stomp 45\'s '
    'SpellVisual 2355 (a 6.9 yd ground crack and stun stars at his feet; the telegraph kit\'s ring shows the real '
    '10-20 yd radius). Look only.',
    icon=_ICON_WAR_STOMP,
)

trample_tank_206694 = spell(
    id=206694, name='Trample', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_TRAMPLE,
    notes=f'{_S13} RG4 Trample: the tank\'s share, the stock weapon hit. Stock Trample 5568 is WEAPON_DAMAGE +7 on '
          'everyone within 10 yd; the percent circle (206692) now hits everyone else, so this is a single-target '
          '100% weapon hit (WEAPON_PERCENT_DAMAGE, weapon_potency 100: the potency lint takes no flat weapon bonus; '
          "the stock +7 is noise against his swing) on his victim, cast triggered as the stomp resolves; Gorged's "
          "+10% per stack raises it. Stock look: Trample's SpellVisual 672, icon 168.",
    raw_overrides=kit_raw('Inflicts $s1% weapon damage.', instant=True, DefenseType=_DEFENSE_MELEE,
                          PreventionType=_PREVENTION_PACIFY, SpellVisualID_1=_SV_TRAMPLE_STOCK),
)

# --- RG5 Knockout (stock 17307 without the stun) ---------------------------------------------------------------------
knockout_206695 = spell(
    id=206695, name='Knockout', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.KNOCK_BACK, base_points=112, die_sides=75, misc_value=75,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_KNOCKOUT,
    notes=f'{_S13} RG5 Knockout: stock 17307 (weapon damage +299, the knockback 7.5 / 11.3-18.7 and a 6 s stun on '
          'the tank) without its third effect, the stun (stock rule flag 1: the tank walks back in while he lumbers '
          'after them). The weapon hit is 100% weapon damage (WEAPON_PERCENT_DAMAGE, weapon_potency 100: the '
          "potency lint takes no flat weapon bonus; the stock +299 is noise against his swing), so it follows the "
          "template's melee (heroic: the heroic template's). Cast triggered on his victim in melee range: first 4 to "
          "9 s, then every 10 to 15 s (the stock SmartAI timers). Stock look: SpellVisual 1187, icon 314.",
    raw_overrides=kit_raw('Inflicts $s1% weapon damage to an enemy and knocks it back.', instant=True,
                          DefenseType=_DEFENSE_MELEE, PreventionType=_PREVENTION_PACIFY,
                          SpellVisualID_1=_SV_KNOCKOUT),
)
