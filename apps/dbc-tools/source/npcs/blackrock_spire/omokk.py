"""
Blackrock Spire build WP-B1: Highlord Omokk (9196), normal and heroic
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.4 rows OM, s3.5 row B1, s3.6, s3.8 NM 1,
s3.10 gap 6; build spec docs/dungeons/blackrock-spire-rework.md "Highlord Omokk", Build spec OM1-OM11). WP-B1 owns
this file (its spells: kSpellsOmokk 210020-210059 of modules/mod-dungeon-bosses
src/BlackrockSpire/BlackrockSpireRework.h only; OmokkLogic.h names the same ids; its creatures 300700-300702). The
engine side is src/BlackrockSpire/boss_highlord_omokk_rework.cpp; lib/test_blackrock_spire_omokk.py pins both sides.

- 9196 Highlord Omokk: boss_highlord_omokk_rework (SmartAI off; he never had any), the build spec's normal health at 5
  players (175k = HealthModifier 62.859 on the level 57 warrior class base 2,784; the flex scaler multiplies it at the
  pull: 393,750 at 10), DamageModifier 3.5 (the stock value; the live 5 is a mod-progression leftover; his melee grows
  with Crowd's Roar instead), stun immunity 1972, INSTANCE_BIND. Heroic 230k is WP-H's override
  (source/world/dungeons/blackrock_spire.py). Retired: Frenzy 8269 and Knock Away 10101 (the stock C++ script; it stays
  registered, unbound). Omokk's Head 12534 is L-1's cut (loot).
- 300700 Spirestone Brawl Fan: the crowd (OM1). Summoned on the pull into the stands (18 in the hall; 10 at the bridge
  doors in the heroic showdown); not selectable, not attackable (KIT_HELPER), no loot, no XP. Four stock Spirestone ogre
  looks at equal chance. npc_brs_brawl_fan (a NullCreatureAI: the boss moves it, makes it cheer and jeer, and throws
  the bottles and the rock from it). No heroic template (handoff s7 #23).
- 300701 Spirestone Brawler: Bull Rush's charger (OM9, heroic showdown): paws at a door (2 s bar), charges its lane,
  gone 6 s after it appears. Not selectable, not attackable. The Spirestone Reaver look, a size bigger. npc_brs_brawler.
- 300702 Spirestone Mojo Mystic (OM6, heroic only): a level 60 elite caster, 12,000 health at 5 players (HealthModifier
  5.618 on the level 60 mage class base 2,136; 27,000 at 10 through the flex scaler at its pull), faction 40, no melee
  (the script keeps it passive), stun and silence work on it (no immunity set: the chant is the expected interrupt).
  The Spirestone Mystic look. npc_brs_mojo_mystic. Its heroic entry is 310288 (heroic_ids.lock prediction, STAGE-H
  report; WP-H's override sets 12k).

Spells. The registry hits (the band, Haymaker, Pelting, Belly Slam, Bull Rush) deal their damage through copies of the
mod-boss-mechanics resolve spell (Physical); the pile's shove is the kit's generic percent hit
(spell_dungeon_refflat_damage, 25% / 35% in hundredths), Pit Drop has its own SpellScript in the boss file. The rest are
auras, cast bars, missiles and looks:

  210020  Crowd Shove        OM1 the band's hit: resolve copy, Physical, 25% / 35% + Weakened, then 8 yd toward the ring
  210021  Crowd Shove        OM1 a climber's hit on the pile (script: kit refflat damage 2500 / 3500 hundredths)
  210022  Haymaker           OM2 the 2.5 s wind-up (cast bar; emote line 1 per target)
  210023  Haymaker           OM2 heroic: the 1.5 s second punch (cast bar)
  210024  Haymaker           OM2 the punch: resolve copy, Physical, 40% / 50%, then 15 yd along the line
  210025  Pelting            OM3 a bottle's landing: resolve copy, Physical, 25% / 30% + Weakened (4 yd)
  210026-210031  Pelting     OM3 the six bottles in flight (fan to circle; acid, tar, blood, frosty, orange, grape)
  210032  Crowd's Roar       OM4 +10% damage done and +10% attack speed a stack, 5 at most, the fight
  210033  Booed              OM5 +10% damage taken a stack, 3 at most, the fight
  210034  Throw Rock         OM5 the rock from the crowd at Omokk when it boos him (look; no damage)
  210035  Ogre Mojo         OM6 the Mojo Mystic's 3 s kickable chant at Omokk (Nature)
  210036  Mojo Frenzy        OM6 +50% damage done and +60% attack speed, 15 s (the stock Frenzy values)
  210037  Mojo Frenzy        OM6 its look, re-cast every 3 s while it lasts
  210038  Belly Slam         OM8 the 2 s cast bar
  210039  Belly Slam         OM8 the slam: resolve copy, Physical, 15% + Weakened in 8 yd, the tank too; 20 yd away
  210040  Bull Rush          OM9 the Brawler pawing the ground (2 s bar on the Brawler)
  210041  Bull Rush          OM9 the charge: resolve copy, Physical, 15% + Weakened in the 3 x 20 yd lane
  210042  Pit Drop           OM10 the crowd's catch: 70% (35% under Slow Fall or Levitate), own SpellScript
  210043  Belly Slam         OM8 the slam's look on him, hit or miss
  210044  Haymaker           OM2 the punch's look on him, hit or miss
  210045  Shoved             OM1 the 1.5 s lockout after a shove (hidden DUMMY aura): the band skips its wearer
  210046-210059 spare

Visual ids are V-1's (._visuals OM_*); every look is unconfirmed until seen in game. The crowd band marker (gap 6) is
the registry's own red line (the telegraph kit's 92048 / 93048 ladder), nothing here.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import self_visual
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    OM_BELLY_FLOP,
    OM_CROWD_SHOVE,
    OM_FRENZY,
    OM_GROUND_SLAM,
    OM_HAYMAKER,
    OM_MOJO_MADNESS,
    OM_PELTING,
    OM_SHOULDER_CHARGE,
    OM_THROW_ROCK,
)

creature_template_columns(9196, **boss_columns(
    'boss_highlord_omokk_rework', 62.859, damage_modifier=3.5,
))

_OM = 'Blackrock Spire build WP-B1 (Highlord Omokk)'
_SCRIPT_REFFLAT = ('Blackrock Spire: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')
_SCRIPT_OWN = ('Blackrock Spire: a percent of reference health set at launch by the boss file\'s own SpellScript '
               '(DungeonKit::RefFlatOn)')

_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000

_INTERRUPT_FLAGS_STANDARD = 15      # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_SCHOOL_MASK_ALL = 127

_FLAGS_EXTRA_NO_XP = 0x40

# Icons (the working-copy Spell.dbc, read 2026-11-15).
_ICON_CROWD_PUMMEL = 756            # Crowd Pummel 10887
_ICON_UPPERCUT = 148                # Hulking Uppercut 50084
_ICON_THROW_ROCK = 2305             # Throw Rock 36645
_ICON_FRENZY = 95                   # Frenzy 8269
_ICON_DEMORALIZING_SHOUT = 282      # Demoralizing Shout 1160 (Booed)
_ICON_MOJO_MADNESS = 2513           # Mojo Madness 43712
_ICON_BELLY_FLOP = 2395             # Belly Flop 61115
_ICON_CHARGE = 457                  # Shoulder Charge 31994

# Numbers (OmokkLogic.h; lib/test_blackrock_spire_omokk.py pins both sides).
_SHOVE_NORMAL = 2500                # kCrowdShovePct 25 / 35, in hundredths
_SHOVE_HEROIC = 3500
_HAYMAKER_CAST_MS = 2500            # kHaymakerCastMs
_HAYMAKER_TWO_MS = 1500             # kHaymakerTwoMs
_BOTTLE_SPEED = 10.0                # kBottleSpeed (the stock bottle throws')
_ROAR_MAX = 5                       # kRoarMaxStacks
_ROAR_DONE = 10                     # kRoarDamagePct
_ROAR_HASTE = 10                    # kRoarHastePct
_BOOED_MAX = 3                      # kBooedMaxStacks
_BOOED_TAKEN = 10                   # kBooedTakenPct
_SHOVE_LOCKOUT_MS = 1500            # kShoveLockoutMs (Shoved 210045)
_ROCK_SPEED = 30.0                  # stock Throw Rock 36645's
_MOJO_CAST_MS = 3000                # kMojoCastMs
_MOJO_RANGE = 60.0                  # kMojoRangeYd
_MOJO_FRENZY_MS = 15000             # kMojoFrenzyMs
_MOJO_DONE = 50                     # kMojoFrenzyDamagePct
_MOJO_HASTE = 60                    # kMojoFrenzyHastePct
_SLAM_CAST_MS = 2000                # kBellySlamCastMs
_RUSH_WARN_MS = 2000                # kBullRushWarnMs

# Stock Spirestone ogre looks [creature_template_model, read 2026-11-15].
_DISPLAY_REAVER = 11581             # Spirestone Reaver 9200
_DISPLAY_ENFORCER = 11577           # Spirestone Enforcer 9199
_DISPLAY_BATTLE_MAGE = 11543        # Spirestone Battle Mage 9197
_DISPLAY_MYSTIC = 11579             # Spirestone Mystic 9198

# --- 300700 the crowd, 300701 the Brawler, 300702 the Mojo Mystic ----------------------------------------------------

brawl_fan_300700 = creature_template(
    300700, 'Spirestone Brawl Fan', **{
        **KIT_HELPER, 'minlevel': 58, 'maxlevel': 58, 'rank': 0, 'unit_class': 1, 'type': 7, 'speed_run': 1.14286,
        'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': 'npc_brs_brawl_fan',
    },
)
creature_model(300700, display_id=_DISPLAY_REAVER, idx=0)
creature_model(300700, display_id=_DISPLAY_ENFORCER, idx=1)
creature_model(300700, display_id=_DISPLAY_BATTLE_MAGE, idx=2)
creature_model(300700, display_id=_DISPLAY_MYSTIC, idx=3)

brawler_300701 = creature_template(
    300701, 'Spirestone Brawler', **{
        **KIT_HELPER, 'minlevel': 58, 'maxlevel': 58, 'rank': 0, 'unit_class': 1, 'type': 7,
        'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': 'npc_brs_brawler',
    },
)
creature_model(300701, display_id=_DISPLAY_REAVER, scale=1.15)

# Level 60 elite mage: 2,136 x 5.618 = 12,000 (heroic: WP-H's override, the same 12k; 310288 its heroic entry).
mojo_mystic_300702 = creature_template(
    300702, 'Spirestone Mojo Mystic', **{
        **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'unit_class': 8, 'unit_flags': 0,
        'HealthModifier': 5.618, 'DamageModifier': 1.0, 'BaseAttackTime': 2000, 'speed_run': 1.14286,
        'ExperienceModifier': 1.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
        'ScriptName': 'npc_brs_mojo_mystic', 'difficulty_entry_1': 310288,
    },
)
creature_model(300702, display_id=_DISPLAY_MYSTIC)

# --- OM1 The Ring -----------------------------------------------------------------------------------------------------

crowd_shove_210020 = resolve_copy(
    210020, 'Crowd Shove', School.NORMAL, 'The crowd beats you and shoves you back into the ring.',
    f'{_OM}, OM1: the band, a 2 yd strip along the foot of the rock pile, across the two north alcove mouths and the '
    'doorway (on the bridge: in front of both door crowds), a persistent registry Line per strip ticking every 0.5 s: '
    '25% / 35% of the row (the tank\'s on the tank) + Weakened to anyone inside, then the script throws them 8 yd back '
    'toward the ring\'s middle and the crowd\'s favor grows (a Crowd\'s Roar stack). Copy of the resolve spell 205001 '
    '(Physical). Crowd Pummel 10887\'s SV 1023 on every unit hit.',
    icon=_ICON_CROWD_PUMMEL, visual=OM_CROWD_SHOVE,
)

pile_shove_210021 = spell(
    id=210021, name='Crowd Shove', school=School.NORMAL, dispel=0, mechanic=0, attributes=_ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_SHOVE_NORMAL - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CROWD_PUMMEL,
    notes=f'{_OM}, OM1: a player who climbs the rock pile (walked or thrown there) is shoved by the crowd standing on '
          'it: the script polls every 0.5 s and casts this on them (triggered): 25% / 35% of the row '
          '(spell_dungeon_refflat_damage reads 2500 hundredths, EffectMiscValueB 3500 on heroic), plus a Weakened '
          'stack, the 8 yd throw back into the ring and a Crowd\'s Roar stack, as the band. Crowd Pummel\'s SV 1023.',
    raw_overrides=kit_raw('The crowd beats you and shoves you back into the ring.', instant=True,
                          EffectMiscValueB_1=_SHOVE_HEROIC, SpellVisualID_1=OM_CROWD_SHOVE,
                          AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(pile_shove_210021, 'spell_dungeon_refflat_damage')

shoved_210045 = spell(
    id=210045, name='Shoved', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=_ATTR0_DO_NOT_DISPLAY | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_SHOVE_LOCKOUT_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_CROWD_PUMMEL,
    notes=f'{_OM}, OM1: the shove\'s lockout (R-1-A m1). boss_highlord_omokk_rework puts it on every unit the crowd '
          'shoves (band or pile; AddAura) for 1.5 s (kShoveLockoutMs); the band\'s registry line skips anyone wearing '
          'it (Eligibility maxStacks 0), so a player still listed inside the 2 yd strip at the next 0.5 s tick (the '
          'server sees the throw only from the next movement packet) is not shoved twice. A hidden DUMMY aura, no '
          'effect of its own, not dispellable.',
    raw_overrides=kit_raw(instant=True, AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- OM2 Haymaker -----------------------------------------------------------------------------------------------------

haymaker_cast_210022 = cast_bar(
    210022, 'Haymaker', _HAYMAKER_CAST_MS, 'Winds up a haymaker.',
    f'{_OM}, OM2: the 2.5 s wind-up, every 15 s from 10 s (emote line 1 names each target): a 5 x 30 yd line from him '
    'toward each of 1 / 2 random non-tanks\' spots at the start of the cast. Not kickable (cast_bar): the registry '
    'line owns the hit (210024). Knock Away 10101 is retired.',
    icon=_ICON_UPPERCUT,
)

haymaker_two_cast_210023 = cast_bar(
    210023, 'Haymaker', _HAYMAKER_TWO_MS, 'Throws the second punch.',
    f'{_OM}, OM2 heroic: the one-two. As the first line lands, a second line toward the same player\'s new spot, 1.5 s '
    '(the blackrock-spire-followups drill, row 0, tag 2): this bar. Not kickable.',
    icon=_ICON_UPPERCUT,
)

haymaker_210024 = resolve_copy(
    210024, 'Haymaker', School.NORMAL, 'A huge ogre fist.',
    f'{_OM}, OM2: the punch: 40% / 50% of the row (the tank\'s on the tank) to everyone in the 5 x 30 yd line, no '
    'Weakened (SP OM2), then the script throws each 15 yd along the line (into the band across the ring: a Crowd '
    'Shove on top, 65% / 85%), a Crowd\'s Roar stack per player hit. Copy of the resolve spell 205001 (Physical). '
    'Hulking Uppercut 50084\'s SV 208 (anim, sound, shake) on every unit hit.',
    icon=_ICON_UPPERCUT, visual=OM_HAYMAKER,
)

haymaker_look_210044 = self_visual(
    210044, 'Haymaker', OM_HAYMAKER,
    f'{_OM}, OM2: the punch\'s look on Omokk (cast on himself, triggered) as each line lands, hit or miss. Hulking '
    'Uppercut\'s SV 208 (V-1: animation, sound and a shake; the line marker carries the warning).',
    icon=_ICON_UPPERCUT,
)

# --- OM3 Pelting ------------------------------------------------------------------------------------------------------

pelting_210025 = resolve_copy(
    210025, 'Pelting', School.NORMAL, 'A bottle from the crowd shatters at your feet.',
    f'{_OM}, OM3: every 12 s / 10 s from 6 s, a 4 yd circle under each of 2 / 4 (heroic 3 / 6) random players and '
    'under every Weakened player, 2 s: 25% / 30% of the row + Weakened. Never lands while a Haymaker line is down '
    '(the volley waits until 1 s after the last punch). Copy of the resolve spell 205001 (Physical). No look of its '
    'own: the bottle in flight (210026-210031) shatters on the spot as the circle resolves.',
    icon=_ICON_THROW_ROCK,
)


def _bottle(spell_id: int, stock_id: int, visual: int, flavor: str):
    return spell(
        id=spell_id, name='Pelting', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=_ICON_THROW_ROCK,
        notes=f'{_OM}, OM3: a {flavor} bottle in flight, cast by a Brawl Fan (triggered) at a Pelting circle\'s '
              f'center, timed to land as the circle resolves (Speed {_BOTTLE_SPEED:.0f} yd/s; the script holds the '
              f'throw by the fan\'s distance). The stock throw {stock_id}\'s SV {visual}. Look only.',
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Speed=_BOTTLE_SPEED,
                              Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=_ATTR1_NO_THREAT,
                              AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


_BOTTLE_FLAVORS = {39154: 'acid', 39147: 'tar', 39148: 'blood', 39149: 'frosty', 39146: 'orange juice',
                   39155: 'grape'}
bottles_210026_210031 = [
    _bottle(210026 + n, stock, visual, _BOTTLE_FLAVORS[stock])
    for n, (stock, visual) in enumerate(OM_PELTING.items())
]

# --- OM4 Crowd's Roar, OM5 Booed --------------------------------------------------------------------------------------

crowds_roar_210032 = spell(
    id=210032, name='Crowd\'s Roar', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
                    base_points=_ROAR_DONE, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Crowd\'s Roar: a flat +10% damage done a stack, not a damage or heal value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE,
                    base_points=_ROAR_HASTE, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Crowd\'s Roar: a flat +10% attack speed a stack, not a damage or heal value')],
    spell_icon_id=_ICON_FRENZY,
    notes=f'{_OM}, OM4: Crowd\'s Roar, the crowd\'s favor (Frenzy 8269 retired). Every player who lands in the crowd '
          '(a Crowd Shove), is hit by a Haymaker or is caught by Pit Drop gives Omokk a stack, 5 at most '
          '(CumulativeAura 5), for the rest of the fight: +10% damage done and +10% attack speed a stack (his melee; '
          'his custom hits ignore caster modifiers), so 5 stacks are about the stock Frenzy. The judge (OM5) takes one '
          'off when nobody fed the crowd in its 30 s. A landed Ogre Mojo adds 2. The script sets the count '
          '(DungeonKit::AddStacks, caster Omokk). Not dispellable. Frenzy\'s SV 870 (a roar flash at each change).',
    raw_overrides=kit_raw('The crowd cheers him on.', 'Damage done increased by $s1%. Attack speed increased by $s2%.',
                          CastingTimeIndex=1, CumulativeAura=_ROAR_MAX, SpellVisualID_1=OM_FRENZY,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

booed_210033 = spell(
    id=210033, name='Booed', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=_BOOED_TAKEN, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Booed: a flat +10% damage taken a stack, not a damage or heal value')],
    spell_icon_id=_ICON_DEMORALIZING_SHOUT,
    notes=f'{_OM}, OM5: Booed. Every 30 s from the pull the crowd judges: if nobody fed it in that window, a Crowd\'s '
          'Roar stack comes off and Omokk gains a Booed stack (CumulativeAura 3), +10% damage taken a stack, for the '
          'rest of the fight; a rock from the crowd hits him (210034) and the crowd jeers (emote line 3); at the third '
          'he yells line 4. A clean group reaches 3 by 1:30. A debuff on him (shown as one), not dispellable. No look '
          'of its own (the rock is the moment).',
    raw_overrides=kit_raw('The crowd has turned on him.', 'Damage taken increased by $s1%.', CastingTimeIndex=1,
                          CumulativeAura=_BOOED_MAX, AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

crowd_rock_210034 = spell(
    id=210034, name='Throw Rock', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_THROW_ROCK,
    notes=f'{_OM}, OM5: the crowd\'s rock at Omokk when it boos him, cast by a random Brawl Fan (triggered) on him. A '
          'DUMMY: no damage (Booed is the cost). Throw Rock 36645\'s SV 1506 (Boulder_Missile), its Speed 30. Look '
          'only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=OM_THROW_ROCK, Speed=_ROCK_SPEED,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- OM6 Mojo (heroic) ------------------------------------------------------------------------------------------------

ogre_mojo_210035 = spell(
    id=210035, name='Ogre Mojo', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=_MOJO_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_MOJO_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ALLY)],
    spell_icon_id=_ICON_MOJO_MADNESS,
    notes=f'{_OM}, OM6 heroic: Ogre Mojo, every 25 s from 20 s: 1 / 2 Spirestone Mojo Mystics (300702) step out of '
          'the crowd and chant it at Omokk, a 3 s cast (emote line 6). Kickable (InterruptFlags 15, PreventionType 1; '
          'the boss data\'s interrupt list, priority 3, expected). Landed on him (his AI\'s SpellHit): Mojo Frenzy '
          '(210036) and 2 Crowd\'s Roar stacks. Interrupted, killed or landed, the Mystic walks back into the crowd. '
          'A DUMMY on a friend; Nature, a school none of Omokk\'s bars use. Ignores line of sight (the crowd chants '
          'over the ring). Mojo Madness 43712\'s SV 7306 (yellow-orange hands and a burst).',
    raw_overrides=kit_raw('Chants ogre mojo into the highlord.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                          PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=OM_MOJO_MADNESS,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT),
)

mojo_frenzy_210036 = spell(
    id=210036, name='Mojo Frenzy', school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_MOJO_FRENZY_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
                    base_points=_MOJO_DONE, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Mojo Frenzy: a flat +50% damage done, not a damage or heal value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE,
                    base_points=_MOJO_HASTE, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Mojo Frenzy: a flat +60% attack speed, not a damage or heal value')],
    spell_icon_id=_ICON_MOJO_MADNESS,
    notes=f'{_OM}, OM6 heroic: Mojo Frenzy, the stock Frenzy 8269 values (+50% damage done, +60% attack speed) for '
          '15 s when an Ogre Mojo lands (Omokk casts it on himself, triggered); a second landing refreshes it. Not '
          'dispellable (stock Frenzy was not). Mojo Madness\'s SV 7306 at the application; its burst is one-shot, so '
          'the script re-casts the look (210037) every 3 s while it lasts.',
    raw_overrides=kit_raw('The mojo drives him into a frenzy.',
                          'Damage done increased by $s1%. Attack speed increased by $s2%.', CastingTimeIndex=1,
                          SpellVisualID_1=OM_MOJO_MADNESS, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

mojo_frenzy_look_210037 = self_visual(
    210037, 'Mojo Frenzy', OM_MOJO_MADNESS,
    f'{_OM}, OM6 heroic: the Mojo Frenzy\'s look, re-cast by Omokk on himself (triggered) every 3 s while the frenzy '
    'lasts (V-1: Mojo Madness\'s SV 7306 is a 1.9 s burst, not a lasting state).',
    icon=_ICON_MOJO_MADNESS, school=School.NATURE,
)

# --- OM8 Belly Slam, OM9 Bull Rush (heroic showdown) ------------------------------------------------------------------

belly_slam_cast_210038 = cast_bar(
    210038, 'Belly Slam', _SLAM_CAST_MS, 'Rears back to slam the bridge.',
    f'{_OM}, OM8 heroic: the 2 s cast on the bridge, 3 s after landing and then every 15 s: an 8 yd circle on him, '
    'the tank too. Not kickable (cast_bar): the registry circle owns the hit (210039). No Bull Rush lane is down '
    'during it.',
    icon=_ICON_BELLY_FLOP,
)

belly_slam_210039 = resolve_copy(
    210039, 'Belly Slam', School.NORMAL, 'The bridge shakes under his belly.',
    f'{_OM}, OM8 heroic: the slam: 15% of the row (the tank\'s on the tank) + Weakened to everyone within 8 yd of him, '
    'then the script throws each 20 yd away from him (along the bridge onto it or into a door crowd; beside him off '
    'the bridge). Copy of the resolve spell 205001 (Physical). Ground Slam 33525\'s SV 8083 on every unit hit; the '
    'slam\'s own look on him is 210043.',
    icon=_ICON_BELLY_FLOP, visual=OM_GROUND_SLAM,
)

belly_slam_look_210043 = self_visual(
    210043, 'Belly Slam', OM_BELLY_FLOP,
    f'{_OM}, OM8 heroic: the slam\'s look on Omokk (cast on himself, triggered) as the circle lands, hit or miss. '
    'Belly Flop 61115\'s SV 12882 (a crack and a shake; V-1: half Ground Slam\'s size, the circle marker is the read).',
    icon=_ICON_BELLY_FLOP,
)

bull_rush_cast_210040 = cast_bar(
    210040, 'Bull Rush', _RUSH_WARN_MS, 'Paws the ground.',
    f'{_OM}, OM9 heroic: a Spirestone Brawler (300701) paws at a bridge door for 2 s (cast on itself; the doors in '
    'turn, every 8 s from 5 s after landing), then charges its 3 x 20 yd lane. Not kickable (cast_bar): the registry '
    'lane owns the hit (210041).',
    icon=_ICON_CHARGE,
)

bull_rush_210041 = resolve_copy(
    210041, 'Bull Rush', School.NORMAL, 'An ogre charges down the bridge.',
    f'{_OM}, OM9 heroic: the charge: 15% of the row (the tank\'s on the tank) + Weakened to everyone in the 3 x 20 yd '
    'lane from the door toward a random non-tank\'s spot (1 / 2 lanes from the same door), then the script throws each '
    'sideways, 3 yd past the near edge of the deck (off the bridge: Pit Drop catches them). Copy of the resolve spell '
    '205001 (Physical). Shoulder Charge 31994\'s SV 3783 on every unit hit (no aura, so V-1\'s StunSwirl note does not '
    'apply).',
    icon=_ICON_CHARGE, visual=OM_SHOULDER_CHARGE,
)

# --- OM10 Pit Drop ----------------------------------------------------------------------------------------------------

pit_drop_210042 = spell(
    id=210042, name='Pit Drop', school=School.NORMAL, dispel=0, mechanic=0, attributes=_ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=200.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_OWN)],
    spell_icon_id=_ICON_CROWD_PUMMEL,
    notes=f'{_OM}, OM10 heroic: Pit Drop. On the bridge the crowd catches every falling player 8 yd under the deck '
          '(the kit\'s FallWatch; about 1.5 s into the 50 yd drop once the server sees the client fall) and hauls them '
          'back to the nearer door (a 2 s jump): Omokk casts this on them (triggered) in place of fall damage: 70% of '
          'the row, half under Slow Fall or Levitate (feather fall or hover): spell_brs_omokk_pit_drop sets the value '
          'at launch. A Crowd\'s Roar stack per catch. Always hits, cannot crit, ignores line of sight. Crowd '
          'Pummel\'s SV 1023 (the crowd beats them on the way up).',
    raw_overrides=kit_raw('The crowd catches you and hauls you back onto the bridge, roughly.', instant=True,
                          SpellVisualID_1=OM_CROWD_SHOVE,
                          AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(pit_drop_210042, 'spell_brs_omokk_pit_drop')
