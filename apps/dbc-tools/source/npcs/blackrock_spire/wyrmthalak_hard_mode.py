"""
Blackrock Spire build WP-B9: Overlord Wyrmthalak's hard mode, the war horn
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.7, s3.4 row "WT hard mode", s3.5 row B9,
s7 #14, #22, #25, #26, #28; build spec docs/dungeons/blackrock-spire-rework.md SP 2436-2521 rows WT9-WT17, design SP
2322-2389, rulings 48-49). WP-B9 owns this file (its spells: kSpellsWarHorn 210290-210339 of
modules/mod-dungeon-bosses src/BlackrockSpire/BlackrockSpireRework.h; WyrmthalakHardModeLogic.h names the same ids).
The engine side is src/BlackrockSpire/wyrmthalak_hard_mode.cpp on B8's hooks (WyrmthalakFight.h). The Bloodaxe War
Horn gameobject 301255 (template and spawn) is the core SQL rev rev_wyrmthalak_hard_mode_blackrock_spire.sql; his
texts 7-9 are B8's rev.

It declares no creature: the hard mode reuses B8's champions 300708-300710 and rider 300711 (100k / 6k by script
through DungeonKit::Flex::SetHealth, x the flex ladder), Urok's Stolen Magic Shard 300706 and Stolen Power /
Overcharge spells 210151, 210152, 210160-210162 (B5, UrokShards.h), Voone's Chain Anchor 300704, Stuck Axe 301250 and
chain beam 210097 (B3), and B8's black flame patch 210253 and Throw Axe 210260. The hard mode runs on heroic only.

Spells (looks from ._visuals, WP-V-1's picks; every look unconfirmed until seen in game):

  210290  Tribal Ward          WT13 -20% damage taken a stack on him, one stack per living champion (3 = -60%)
  210291  Bloodaxe War Horn    WT9 the horn's burst (V-1's minted SV 90602: the stock horn's cast kit and the war horn
                               impact), a stalker at the horn casts it on itself
  210292  Caustic Poison       WT14 Poison, 0.5% of the reference row a stack every 2 s, 10 stacks, 20 s refreshed
  210293  Caustic Roar         WT14 the 2.5 s cast (Nature, interruptible, line 8); landed (its SpellScript) the hit
  210294  Caustic Roar         WT14 the landed roar (resolve copy, Nature): 20% and 2 Caustic Poison stacks, everyone
  210295  Throw Spear          WT15 the spear in flight (Throw Spear 54617's missile SV 11993, 30 yd/s)
  210296  Spear Impact         WT15 the impact (resolve copy, Physical): 10% on the speared player
  210297  Spear Chain          WT15 the chain beam on the speared player (Skadi's Harpoon Chain SV 10920), 20 s
  210298  Spear Chain          WT15 a chain crossing (resolve copy, Physical): 10%, Weakened once per player
  210299  Shadowflame Spit     WT16 a spit circle (resolve copy, Shadow): 25%, Weakened
  210300  Shadowflame Spit     WT16 the spit in flight (Shadow Bolt's missile SV 64)
  210301  Shadowflame Spit     WT16 the landing (Shadow Flame 22972's burst SV 6700)
  210302  Shadowflame          WT16 a burning patch's tick (resolve copy, Shadow): 5% a second, Weakened once
  210303  Chained Axe          WT11 a chain crossing (resolve copy, Physical): 10%, Weakened
  210304  Haul                 WT11 the haul (resolve copy, Physical): 35%, Weakened
  210305  Rabies               WT12 Disease, 1.5% of the reference row a stack every 3 s, 5 stacks, 30 s refreshed (SP:
                               Gizrul's HG6 heroic numbers; B7's HG6 spell was not declared yet, so the riders carry
                               their own copy)
  210306  Rabid Bite           WT12 the kept rider's passive: every melee hit procs Rabies on its target
  210307-210339 spare.

Tooltips are number-free where the number is a reference percent (Systems.md s10).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
from lib.dsl.registry import procs_on, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    HG_RABIES,
    SV_HORN_BLOWN,
    SW_VENOM,
    WT_CAUSTIC_ROAR,
    WT_HARPOON_CHAIN,
    WT_SPEAR_THROW,
    WT_SPIT_LANDING,
    WT_SPIT_MISSILE,
)

_B9 = 'Blackrock Spire build WP-B9 (Wyrmthalak\'s hard mode, the war horn)'
_SCRIPT_REFFLAT = ('Blackrock Spire: a percent of reference health in hundredths per stack, set by the kit\'s '
                   'spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')
_REFFLAT_PERIODIC = 'spell_dungeon_refflat_periodic'
_ROAR_SCRIPT = 'spell_brs_wyrmthalak_caustic_roar'

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_TARGET_FLAG_UNIT = 0x2
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_ATTR3_SUPPRESS_TARGET_PROCS = 0x00020000
_ATTR5_ALLOW_ACTION_DURING_CHANNEL = 0x00000001
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a debuff never outlives the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SCHOOL_MASK_ALL = 127
_DISPEL_DISEASE = 3
_DISPEL_POISON = 4
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15
# SpellMgr.h: PROC_FLAG_DONE_MELEE_AUTO_ATTACK, PROC_HIT_NORMAL | PROC_HIT_CRITICAL.
_PROC_DONE_MELEE_AUTO_ATTACK = 0x4
_PROC_HIT_NORMAL_OR_CRIT = 0x1 | 0x2

# Icons of the stock spells the looks come from (Spell.dbc, the working copy).
_ICON_SHIELD_WALL = 281             # Shield Wall 871 (Tribal Ward: the tribes shield him)
_ICON_HORN = 1550                   # Horn of Elemental Fury 56893
_ICON_CORROSIVE_POISON = 68         # Corrosive Poison 3396
_ICON_BELLOWING_ROAR = 11           # Bellowing Roar 18431
_ICON_SPEAR = 370                   # Throw Spear 54617 / Impale 48261
_ICON_SHADOWFLAME = 3317            # Shadowflame 47897
_ICON_THROW_AXE = 1529              # Throw Axe 16075
_ICON_RABIES = 203                  # Rabies 3150
_ICON_BITE = 1680                   # Bite 17259

# WyrmthalakHardModeLogic.h: the numbers the declarations carry (lib/test_blackrock_spire_wyrmthalak_hard_mode.py pins
# them against the header).
_TRIBAL_WARD_PCT = -20              # kTribalWardPctPerChampion
_TRIBAL_WARD_STACKS = 3             # kTribalWardMaxStacks
_POISON_HUNDREDTHS = 50             # kPoisonHundredthsPerStack
_POISON_TICK_MS = 2000              # kPoisonTickMs
_POISON_MAX = 10                    # kPoisonMaxStacks
_POISON_MS = 20000                  # kPoisonMs
_ROAR_CAST_MS = 2500                # kRoarCastMs
_SPEAR_SPEED = 30.0                 # kSpearMissileSpeed
_SPEAR_CHAIN_MS = 20000             # kSpearChainMs
_SPIT_SPEED = 20.0                  # kSpitMissileSpeed
_RABIES_HUNDREDTHS = 150            # kRabiesHundredthsPerStack
_RABIES_TICK_MS = 3000              # kRabiesTickMs
_RABIES_MAX = 5                     # kRabiesMaxStacks
_RABIES_MS = 30000                  # kRabiesMs

# --- WT13 Tribal Ward ------------------------------------------------------------------------------------------------

tribal_ward_210290 = spell(
    id=210290, name='Tribal Ward', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=_TRIBAL_WARD_PCT, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Tribal Ward: a flat -20% damage taken per stack, not a damage or heal value')],
    spell_icon_id=_ICON_SHIELD_WALL,
    notes=f'{_B9}, WT13: on Wyrmthalak while the hard mode runs, one stack per living champion (the script keeps the '
          'count, DungeonKit::AddStacks, CumulativeAura 3): -20% damage taken a stack, every school (-60% with all '
          'three champions up). Not dispellable or stealable; removed when the pull ends. No look: the buff icon and '
          'the bots\' kill order (the champions first) carry it.',
    raw_overrides=kit_raw('The tribes of the Spire shield their overlord.', 'Damage taken reduced by $s1% for each '
                          'living champion.', instant=True, CumulativeAura=_TRIBAL_WARD_STACKS,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- WT9 the war horn ------------------------------------------------------------------------------------------------

horn_blown_210291 = self_visual(
    210291, 'Bloodaxe War Horn', SV_HORN_BLOWN,
    f'{_B9}, WT9: the horn is blown (go_brs_war_horn, heroic, before the pull): a Chain Anchor 300704 stalker on the '
    'horn (an invisible unit without the trigger bit, so its looks show) casts it on itself (triggered) and despawns '
    'after 5 s. V-1\'s minted SV 90602: the stock Horn of Elemental Fury 56893 cast kit (sound 6423, anim 81) plus the '
    'Ascension ogre_warhorn_impact_base burst (`[look unconfirmed]`).',
    icon=_ICON_HORN,
)

# --- WT14 Caustic Venom ----------------------------------------------------------------------------------------------

caustic_poison_210292 = spell(
    id=210292, name='Caustic Poison', school=School.NATURE, dispel=_DISPEL_POISON, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_POISON_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                    base_points=_POISON_HUNDREDTHS - 1, die_sides=1, amplitude=_POISON_TICK_MS,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CORROSIVE_POISON,
    notes=f'{_B9}, WT14 (the Bloodaxe Champion dead): a stack from him (DungeonKit::AddStacks, caster Wyrmthalak, '
          'CumulativeAura 10, every stack refreshing the 20 s) on every player his abilities hit (Cleave, Black '
          'Dragonfire, Tail Swipe, the spear\'s impact, the spit\'s circles; never a burn, patch or chain tick), 2 '
          'from a landed Caustic Roar. Every 2 s 0.5% of the reference row per stack (50 hundredths, heroic the same '
          'in MiscValueB; spell_dungeon_refflat_periodic multiplies by the stacks), Nature, ignores caster modifiers. '
          'Poison: the bots\' dispel list (priority 1, a reward). Venom Sting\'s lasting poison state (SW_VENOM, SV '
          '2617). Dropped on a map change, removed with the fight.',
    raw_overrides=kit_raw('Caustic venom eats at the flesh. Cure the poison to stop it.',
                          'Taking Nature damage every $t1 sec for each stack.', CastingTimeIndex=1,
                          CumulativeAura=_POISON_MAX, DefenseType=_DEFENSE_MAGIC,
                          EffectMiscValueB_1=_POISON_HUNDREDTHS, SpellVisualID_1=SW_VENOM,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(caustic_poison_210292, _REFFLAT_PERIODIC)

caustic_roar_210293 = spell(
    id=210293, name='Caustic Roar', school=School.NATURE, cast_time_ms=_ROAR_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BELLOWING_ROAR,
    notes=f'{_B9}, WT14 (the Bloodaxe Champion dead): 8 s after the unlock, then every 20 s through his cast queue, '
          'emote line 8. DUMMY on the caster, 2.5 s, interruptible and silence-preventable (InterruptFlags 15, '
          'PreventionType silence; his immunity set 1972 holds no interrupt or silence): the expected interrupt '
          '(the descriptor\'s list, priority 3). Nature, a school none of his other casts use (the breath bar is '
          'Fire), so a kick locks nothing else. Landed, spell_brs_wyrmthalak_caustic_roar (AfterCast; a kicked cast '
          'never gets there) hits everyone with 210294 and 2 Caustic Poison stacks. Bellowing Roar 18431\'s SV 4939 '
          '(the roar\'s sound, a shake and a fear impact on the head).',
    raw_overrides=kit_raw('Wyrmthalak roars a cloud of caustic venom over everyone.',
                          InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=WT_CAUSTIC_ROAR),
)
scripted_by(caustic_roar_210293, _ROAR_SCRIPT)

caustic_roar_hit_210294 = resolve_copy(
    210294, 'Caustic Roar', School.NATURE, 'A caustic roar burns everyone nearby.',
    f'{_B9}, WT14: the landed roar, through DungeonKit::RegistryHit on every player of the fight: 20% of the reference '
    'row (the tank its own row), no Weakened (it cannot be dodged, only interrupted), and 2 Caustic Poison stacks. '
    'Copy of the mod-boss-mechanics resolve spell 205004 (Nature), no look (the cast\'s roar is the look).',
    icon=_ICON_BELLOWING_ROAR,
)

# --- WT15 the Spear Chain --------------------------------------------------------------------------------------------

spear_throw_210295 = spell(
    id=210295, name='Throw Spear', school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SPEAR,
    notes=f'{_B9}, WT15 (the Smolderthorn Champion dead): the spear in flight, cast by him (triggered) at a random '
          'non-tank 10 s after the unlock, then every 30 s (his cast queue, line 9 "%s hurls his spear at $n!"); the '
          'impact 210296 lands when it would arrive (the script times it at 30 yd/s). Throw Spear 54617\'s '
          'HumanSpear01 missile (SV 11993; V-1: Impale 48261\'s SV 10724 has no spear in flight). Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=WT_SPEAR_THROW, Speed=_SPEAR_SPEED, Targets=_TARGET_FLAG_UNIT,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

spear_impact_210296 = resolve_copy(
    210296, 'Spear Impact', School.NORMAL, 'A spear strikes and chains its target to Wyrmthalak.',
    f'{_B9}, WT15: the spear\'s impact on the speared player, through DungeonKit::RegistryHit: 10% of the reference '
    'row, no Weakened, a Caustic Poison stack once the venom is unlocked. Copy of the resolve spell 205001 (Physical), '
    'no look (the spear is the look).',
    icon=_ICON_SPEAR,
)

spear_chain_210297 = spell(
    id=210297, name='Spear Chain', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=_SPEAR_CHAIN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SPEAR,
    notes=f'{_B9}, WT15: the chain from him to the speared player for 20 s. Channeled by a Chain Anchor 300704 that '
          'follows him (a channel on Wyrmthalak himself would hold his casts and melee): the channel draws the beam '
          '(Skadi\'s Harpoon Chain 49679\'s SV 10920, kit 10076, ruling 32) and its aura on the speared player is '
          'the tell and keeps them off their own chain (the registry line\'s eligibility: 0 stacks of this aura). '
          'IS_CHANNELED + NO_THREAT, ignores LoS, suppresses procs, always hits, ALLOW_ACTION_DURING_CHANNEL, no '
          'interrupt flags (the anchor moves). Not dispellable; the script ends it with the chain or the fight.',
    raw_overrides=kit_raw('Speared and chained to Wyrmthalak.', 'Chained to Wyrmthalak. Keep the chain away from '
                          'your allies.', CastingTimeIndex=1, InterruptFlags=0, AuraInterruptFlags=0,
                          ChannelInterruptFlags=0, AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_SUPPRESS_TARGET_PROCS | ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AttributesEx5=_ATTR5_ALLOW_ACTION_DURING_CHANNEL,
                          SpellVisualID_1=WT_HARPOON_CHAIN),
)

spear_chain_hit_210298 = resolve_copy(
    210298, 'Spear Chain', School.NORMAL, 'The spear\'s chain lashes everyone it crosses.',
    f'{_B9}, WT15: a crossing of the spear chain, a live 2 yd line from him to the speared player (both ends move), '
    'every 2 s from 2 s to 20 s: 10% of the reference row (the tank its own row), Weakened once per player (s7 #25: '
    'WeakenedOncePerPlayer). The speared player is never on it. Copy of the resolve spell 205001 (Physical), no look '
    '(the beam is 210297).',
    icon=_ICON_SPEAR,
)

# --- WT16 Shadowflame Spit -------------------------------------------------------------------------------------------

spit_210299 = resolve_copy(
    210299, 'Shadowflame Spit', School.SHADOW, 'Shadowflame splashes the ground.',
    f'{_B9}, WT16 (the Spirestone Champion dead): 5 s after the unlock, then every 15 s, a 4 yd circle under every '
    'player, 2 s: 25% of the reference row (the tank its own row), 1 Weakened, a Caustic Poison stack once the venom '
    'is unlocked. 2 (3 at 6 or more) of the circles stay as patches (210302). Copy of the resolve spell 205006 '
    '(Shadow), no look (the landing is 210301).',
    icon=_ICON_SHADOWFLAME,
)

spit_missile_210300 = spell(
    id=210300, name='Shadowflame Spit', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_SHADOWFLAME,
    notes=f'{_B9}, WT16: the spit in flight, cast by him (triggered) at each circle\'s centre, timed to land with '
          'the circle (20 yd/s). Shadow Bolt 686\'s purple bolt (SV 64, V-1\'s pick: Shadow Flame 22992\'s SV 6719 '
          'is a flame stream at the mouth with no ground). Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=WT_SPIT_MISSILE, Speed=_SPIT_SPEED,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

spit_landing_210301 = spell(
    id=210301, name='Shadowflame Spit', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_SHADOWFLAME,
    notes=f'{_B9}, WT16: the landing, cast by him (triggered) at each circle\'s centre as it resolves. Shadow Flame '
          '22972\'s InstantArea burst (SV 6700: dust and a red glow; V-1\'s gap 15 pick). Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=WT_SPIT_LANDING, Targets=_TARGET_FLAG_DEST_LOCATION,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

spit_patch_210302 = resolve_copy(
    210302, 'Shadowflame', School.SHADOW, 'The ground burns with shadowflame.',
    f'{_B9}, WT16: a burning patch where a spit landed, 4 yd, 40 s, its first tick a second after the landing: 5% of '
    'the reference row a second (the tank its own row), Weakened once per player (s7 #25: WeakenedOncePerPlayer), no '
    'Caustic Poison (a lingering zone, like the burns). Copy of the resolve spell 205006 (Shadow), no look of its own '
    '(B8\'s black flame patch 210253 under it: "patches look like the breath burn").',
    icon=_ICON_SHADOWFLAME,
)

# --- WT11 Chained Axes -----------------------------------------------------------------------------------------------

axe_chain_hit_210303 = resolve_copy(
    210303, 'Chained Axe', School.NORMAL, 'An axe\'s chain lashes everyone it crosses.',
    f'{_B9}, WT11: a crossing of a chain from a stuck axe to the Smolderthorn Champion (a live 2 yd line; the G1 '
    'drill\'s row 5), every 2 s from 2 s to 8 s after the axes land: 10% of the reference row (the tank its own row), '
    '1 Weakened. Copy of the resolve spell 205001 (Physical), no look (Voone\'s chain beam 210097 from the axe\'s '
    'anchor).',
    icon=_ICON_THROW_AXE,
)

haul_210304 = resolve_copy(
    210304, 'Haul', School.NORMAL, 'The Smolderthorn Champion hauls his axes back along their chains.',
    f'{_B9}, WT11: at 8 s the chains go taut (1.5 s) and the champion hauls each axe home: a 3 yd line from the axe to '
    'where he stood at the taut (frozen; the G1 drill\'s tag 6, the heroic sign-off gate), 35% of the reference row '
    '(the tank its own row), 1 Weakened, no exclusion at his end (as SP; designer question). Copy of the resolve spell '
    '205001 (Physical), no look (the axe flies home: B8\'s Throw Axe 210260 from the anchor).',
    icon=_ICON_THROW_AXE,
)

# --- WT12 riders that stay -------------------------------------------------------------------------------------------

rabies_210305 = spell(
    id=210305, name='Rabies', school=School.NATURE, dispel=_DISPEL_DISEASE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_RABIES_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                    base_points=_RABIES_HUNDREDTHS - 1, die_sides=1, amplitude=_RABIES_TICK_MS,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_RABIES,
    notes=f'{_B9}, WT12: a kept Bloodaxe Worg Rider\'s melee procs it on its target (210306): a stack (CumulativeAura '
          '5, each stack refreshing the 30 s; one aura per rider), every 3 s 1.5% of the reference row per stack (150 '
          'hundredths, heroic the same; SP: Gizrul\'s HG6 heroic numbers; spell_dungeon_refflat_periodic), Nature, '
          'ignores caster modifiers. Disease: the bots\' dispel list (priority 1, a reward). The lasting poison state '
          '(HG_RABIES, SV 2617; the stock Rabies SV 631 is a 3 s impact). Dropped on a map change, removed with the '
          'fight.',
    raw_overrides=kit_raw('Infected by a rabid worg. Cure the disease to stop it.',
                          'Taking Nature damage every $t1 sec for each stack.', CastingTimeIndex=1,
                          CumulativeAura=_RABIES_MAX, DefenseType=_DEFENSE_MAGIC,
                          EffectMiscValueB_1=_RABIES_HUNDREDTHS, SpellVisualID_1=HG_RABIES,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(rabies_210305, _REFFLAT_PERIODIC)

rabid_bite_210306 = spell(
    id=210306, name='Rabid Bite', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=210305,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BITE,
    notes=f'{_B9}, WT12: the passive a kept rider wears (the script adds it as the rider turns to fight): every melee '
          'hit (PROC_FLAG_DONE_MELEE_AUTO_ATTACK, normal or critical, 100%) triggers Rabies 210305 on its target. Its '
          'spell_proc row is the source of truth (ProcTypeMask / ProcChance match it). No look.',
    raw_overrides=kit_raw('Melee attacks infect the target with Rabies.', 'Melee attacks infect the target with '
                          'Rabies.', instant=True, ProcTypeMask=_PROC_DONE_MELEE_AUTO_ATTACK, ProcChance=100,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
procs_on(rabid_bite_210306, proc_flags=_PROC_DONE_MELEE_AUTO_ATTACK, hit_mask=_PROC_HIT_NORMAL_OR_CRIT, chance=100.0)
