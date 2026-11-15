"""
Blackrock Spire build WP-B4: Mother Smolderweb (10596), "The Clutch, with Mother's Milk", normal and heroic
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.4 rows SW, s3.5 row B4, s3.6; build spec
docs/dungeons/blackrock-spire-rework.md SP 1231-1469, SW1-SW10, rulings 33-36 and 63-64). WP-B4 owns this file (its
spells: kSpellsSmolderweb 210120-210149 of modules/mod-dungeon-bosses src/BlackrockSpire/BlackrockSpireRework.h only;
SmolderwebLogic.h names the same ids).

- 10596 Mother Smolderweb: boss_mother_smolderweb_rework (SmartAI off: the S0 SQL rev dropped her Mother's Milk,
  Crystallize and death-spiderling rows), the build spec's normal health (165k = HealthModifier 55.724 on the level 59
  warrior class base 2,961), DamageModifier 5.75 (the upstream sniff value, S0's), stun immunity 1972 (SP: stun immune;
  it adds the sleep immunity the stock -250 lacked), INSTANCE_BIND. Heroic 218k is WP-H's override. Stock Mother's Milk
  16468 is cast on nobody in the fight (Last Milk gives it to the quest holders at her death), Crystallize 16104 is
  retired from her kit, the stock death spiderlings (16103) are cast again from C++. Her loot is untouched.
- 300705 Smolderweb Broodling: her own entry (not the stock Spire Spiderling 10375, trash in the cave), a beast of
  the stock spiderling's display, 2,000 health at 5 players (HealthModifier 0.6553 on the level 60 warrior base 3,052;
  heroic 3,000 is WP-H's override, difficulty_entry_1 310289: the second wave 1 kit add of heroic_ids.lock's order),
  a weak bite (DamageModifier 1.0, the Mojo Mystic's), no loot, no XP. npc_brs_broodling (a ScriptedAI) goes for the
  player with the most Venom, else the player who hatched its egg. The ladder applies at its pull (the DD summoner
  rule).
- The Smolderweb Egg 301251 gameobject (display 364, SpiderEggSack04, ruling 36) and her three texts are the core SQL
  rev rev_mother_smolderweb_blackrock_spire.sql (dbc-tools has no gameobject_template declaration).

Spells (looks from ._visuals, WP-V-1's SW_* picks; every look unconfirmed until seen in game). The registry hits go
through dungeon copies of the mod-boss-mechanics resolve spell; the rest are riders, auras, cast bars and looks:

  210120  Crystal Spray   SW6 the 2 s rear-up before the cone (a cast bar, not interruptible), Frost
  210121  Crystal Spray   SW6 the cone's hit: resolve copy, Frost, 25% / 30% Weakened, with the Encased rider
  210122  Encased         SW6 the 2 s stun (the rider), Crystallize's sparkles
  210123  Egg Hatch       SW1-SW3 a hatched egg's hit: resolve copy, Nature, 20% / 25% Weakened; the Broodlings
                          and the burst come from the script
  210124  Mother's Milk   SW4 the splash's hit: resolve copy, Nature, 15% / 20% Weakened, with the Venom rider
  210125  Mother's Milk   SW4 / SW8 the spat missile in flight to a point (look only, Speed 20)
  210126  Venom           SW5 Poison, 1% of the reference row a second per stack, 30 s, up to 5 stacks (normal); a
                          Poison dispel clears every stack
  210127  Venom           SW5 the same with up to 8 stacks (heroic: the registry rider is picked by difficulty)
  210128  Widow's Bite    SW10 (10 players) Poison, 1% a second per stack, 15 s, each stack refreshing it, no cap; a
                          Poison dispel removes one stack
  210129  Brood Call      SW7 (heroic) the 3 s chitter (a cast bar, not interruptible), Hatch Eggs' shadow nova
  210130  Hatch           SW3 / SW7 the green burst where an egg hatches (look only)
  210131-210149 spare.

Visual ids are WP-V-1's (._visuals): the hatch burst Spawn Bile Slime SV 4339, Brood Call Hatch Eggs SV 11329, Widow's
Bite and Venom Venom Sting SV 2617 (the SP's Poison 744 is wrong: a 3 s impact). Tooltips are number-free (SP checklist
item 8).
"""

import math

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_SPIRE_MONSTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_creature,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    SW_BROOD_CALL,
    SW_CRYSTALLIZE,
    SW_HATCH_BURST,
    SW_MOTHERS_MILK,
    SW_VENOM,
)

_B4 = 'Blackrock Spire build WP-B4 (Mother Smolderweb)'

creature_template_columns(10596, **boss_columns(
    'boss_mother_smolderweb_rework', 55.724, damage_modifier=5.75,
))

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000      # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_MECHANIC_STUN = 12
_DEFENSE_MAGIC = 1
_DISPEL_POISON = 4

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004

_SCRIPT_REFFLAT = ('Blackrock Spire: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')

_ICON_MILK = 1759               # Mother's Milk 16468
_ICON_CRYSTALLIZE = 87          # Crystallize 16104
_ICON_VENOM_STING = 163         # Venom Sting 5416
_ICON_HATCH_EGGS = 3202         # Hatch Eggs 58542
_ICON_HATCH_SPIDERLINGS = 976   # Hatch Spiderlings 43134

MILK_MISSILE_SPEED = 20.0       # SmolderwebLogic.h kMilkMissileSpeed
VENOM_TICK = 100                # kVenomPctPerStack 1 (hundredths)
BITE_TICK = 100                 # kBitePctPerStack 1 (hundredths)
VENOM_MS = 30000                # kVenomMs
BITE_MS = 15000                 # kBiteMs
ENCASED_MS = 2000               # kEncasedMs
VENOM_STACKS_NORMAL = 5         # kVenomMaxStacks
VENOM_STACKS_HEROIC = 8
BITE_STACKS = 255               # kBiteStackCap: the aura counter's limit (no cap)
SPRAY_CAST_MS = 2000            # kSprayCastMs
BROOD_CALL_CAST_MS = 3000       # kBroodCallCastMs

BROODLING_DISPLAY = 9756                # the stock Spire Spiderling's (10375)
BROODLING_HEALTH_MODIFIER = 0.6553      # ceil(3,052 x 0.6553) = 2,000 (the level 60 warrior base)
BROODLING_HEROIC_ENTRY = 310289         # heroic_ids.lock: the second wave 1 kit add (H's prediction)

# --- 300705 Smolderweb Broodling -------------------------------------------------------------------------------------

_KIT_BEAST = kit_creature(faction=FACTION_SPIRE_MONSTER, type=1, family=3)

broodling_300705 = creature_template(
    300705, 'Smolderweb Broodling', **{
        **_KIT_BEAST, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': BROODLING_HEALTH_MODIFIER, 'DamageModifier': 1.0, 'BaseAttackTime': 2000,
        'ExperienceModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
        'ScriptName': 'npc_brs_broodling', 'difficulty_entry_1': BROODLING_HEROIC_ENTRY,
    },
)
creature_model(300705, display_id=BROODLING_DISPLAY)

# --- SW6 Crystal Spray -----------------------------------------------------------------------------------------------

spray_cast_210120 = cast_bar(
    210120, 'Crystal Spray', SPRAY_CAST_MS, 'She rears up and sprays crystal.',
    f'{_B4}, SW6: the 2 s rear-up every 15 s from 12 s, on her (a cast bar: not interruptible, the registry cone '
    "beside it owns the hit, 210121). Stock Crystallize 16104's SV 4001 (sparkles) on her as the bar runs. She stands "
    'still while she casts (the SP: she rears up).',
    icon=_ICON_CRYSTALLIZE, visual=SW_CRYSTALLIZE, school=School.FROST,
)

spray_hit_210121 = resolve_copy(
    210121, 'Crystal Spray', School.FROST, 'A spray of crystal.',
    f'{_B4}, SW6: the cone\'s hit: 25% (heroic 30%) of the non-tank row on everyone in the 60 degree cone 20 yd in '
    'front of her (a registry Frontal, the tank exempt: at 10 players both tanks, by role), 1 Weakened, with the 2 s '
    'Encased rider (210122). Copy of the resolve spell 205005 (Frost). The sparkles are on the stun.',
    icon=_ICON_CRYSTALLIZE,
)

encased_210122 = spell(
    id=210122, name='Encased', school=School.FROST, dispel=0, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=ENCASED_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=_MECHANIC_STUN, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CRYSTALLIZE,
    notes=f'{_B4}, SW6: the 2 s stun of Crystal Spray (the registry rider), the stock Crystallize 16104 shortened '
          'from 6 s and cut loose from its break-on-damage rule (the 25% hit is the penalty). MOD_STUN, stun '
          'mechanic: stun '
          "immunity and the stun-breaking trinkets answer it. Dispel none. Crystallize's SV 4001 (the sparkles). "
          'AuraInterruptFlags CHANGE_MAP. The duration is SmolderwebLogic.h kEncasedMs.',
    raw_overrides=kit_raw('Encased in crystal. Lasts $d.', 'Encased in crystal.', instant=True,
                          SpellVisualID_1=SW_CRYSTALLIZE, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- SW1 / SW2 / SW3 The Clutch and the hatch ------------------------------------------------------------------------

egg_hatch_210123 = resolve_copy(
    210123, 'Egg Hatch', School.NATURE, 'An egg bursts open.',
    f'{_B4}, SW1-SW3: a hatched egg\'s hit: 20% (heroic 25%) of the row on a player who stayed in the 4 yd egg (a '
    'registry Mine, players only), 1 Weakened; the script spawns the three Broodlings on them and plays the burst '
    '(210130). Copy of the resolve spell 205004 (Nature). Spawn Bile Slime 16809\'s SV 4339 (a green gore burst) on '
    'every unit hit.',
    icon=_ICON_HATCH_SPIDERLINGS, visual=SW_HATCH_BURST,
)

hatch_look_210130 = spell(
    id=210130, name='Hatch', school=School.NATURE, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_HATCH_SPIDERLINGS,
    notes=f'{_B4}, SW3 / SW7: the burst where an egg hatches, cast by her (triggered) at the egg\'s spot, for a step '
          "and for the Brood Call alike. Spawn Bile Slime 16809's SV 4339 (a green gore burst on the ground) at the "
          "point "
          '(unchecked whether a dest-only spell plays it). Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=SW_HATCH_BURST, Targets=_TARGET_FLAG_DEST_LOCATION,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- SW4 Mother's Milk -----------------------------------------------------------------------------------------------

milk_hit_210124 = resolve_copy(
    210124, 'Mother\'s Milk', School.NATURE, 'Her venom splashes.',
    f'{_B4}, SW4: the splash\'s hit: 15% (heroic 20%) of the non-tank row on everyone within 6 yd of the spot a random '
    'non-tank (two at 6 or more) stood on when she spat, 2 s later, 1 Weakened, with the Venom rider (210126, heroic '
    '210127). Copy of the resolve spell 205004 (Nature). The look is the missile (210125); Venom carries the lasting '
    'one.',
    icon=_ICON_MILK,
)

milk_look_210125 = spell(
    id=210125, name='Mother\'s Milk', school=School.NATURE, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_MILK,
    notes=f'{_B4}, SW4 / SW8: the spat missile from her to a point, cast by her (triggered), timed to land as the '
           'splash '
          'resolves (SmolderwebLogic.h MilkLaunchDelayMs) and, at her death, to each quest holder\'s feet for Last '
          'Milk. '
          "Mother's Milk 16468's SV 854 (the goo missile and the green burst) at 20 yd/s, so a long spit (about 40 yd) "
          'flies for the whole 2 s; unchecked whether a dest-only spell plays it. The registry dealt the damage. Look '
          'only.',
    raw_overrides=kit_raw(instant=True, Speed=MILK_MISSILE_SPEED, SpellVisualID_1=SW_MOTHERS_MILK,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- SW5 Venom -------------------------------------------------------------------------------------------------------


def _venom(spell_id: int, stacks: int, heroic: bool):
    return spell(
        id=spell_id, name='Venom', school=School.NATURE, dispel=_DISPEL_POISON, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=100.0, duration_ms=VENOM_MS,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=VENOM_TICK,
                        die_sides=0, amplitude=1000, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                        potency_excluded=_SCRIPT_REFFLAT)],
        spell_icon_id=_ICON_VENOM_STING,
        notes=f'{_B4}, SW5 Venom ({"heroic" if heroic else "normal"}: up to {stacks} stacks, CumulativeAura {stacks}): '
              'the rider of Mother\'s Milk (210124), a stack per hit, the boss as caster, each stack refreshing the '
              '30 s. '
              '1% of the reference non-tank row a second per stack (base point 100 hundredths, heroic the same: '
              'EffectMiscValueB 100), Nature, through spell_dungeon_refflat_periodic (the engine multiplies by the '
              'stacks); ignores caster modifiers. A Poison dispel clears every stack (spell_brs_smolderweb_venom): the '
              "dispel list's reward. The Broodlings go for the player with the most stacks. Named Venom, not Mother's "
              "Milk, so it is never confused with the quest aura. Venom Sting 5416's SV 2617 (a lasting poison state "
              "on "
              'the chest; it shows no stack count). AuraInterruptFlags CHANGE_MAP.',
        raw_overrides=kit_raw('Poisoned: taking Nature damage every $t1 sec for each stack. A Poison dispel cures '
                              'every '
                              'stack.', 'Taking Nature damage every $t1 sec for each stack.', CastingTimeIndex=1,
                              CumulativeAura=stacks, DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=VENOM_TICK,
                              SpellVisualID_1=SW_VENOM, AttributesEx=_ATTR1_NO_THREAT,
                              AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                              AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


venom_210126 = _venom(210126, VENOM_STACKS_NORMAL, False)
scripted_by(venom_210126, 'spell_dungeon_refflat_periodic', 'spell_brs_smolderweb_venom')
venom_heroic_210127 = _venom(210127, VENOM_STACKS_HEROIC, True)
scripted_by(venom_heroic_210127, 'spell_dungeon_refflat_periodic', 'spell_brs_smolderweb_venom')

# --- SW10 Widow's Bite (10 players) ----------------------------------------------------------------------------------

widows_bite_210128 = spell(
    id=210128, name='Widow\'s Bite', school=School.NATURE, dispel=_DISPEL_POISON, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=BITE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=BITE_TICK,
                    die_sides=0, amplitude=1000, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_VENOM_STING,
    notes=f'{_B4}, SW10 (rulings 63 and 64, 10 players only): her bite on her target every 6 s from 6 s adds a stack '
          '(DungeonKit::AddStacks, the boss as caster, CumulativeAura 255: the aura counter\'s limit, so no cap: a '
          'tank who keeps her past 5 or 6 stacks dies). 1% of the reference row a second per stack (the tank row on '
          'the tank), Nature, 15 s, each stack refreshing it, through spell_dungeon_refflat_periodic. The 15 s is '
          'shorter than the 18 s the other tank needs to reach 3 stacks (SmolderwebLogic.h static_assert), so the '
          'old tank has 0 stacks when it is wanted again: the taunt swap entry (BM TauntSwapEntry, 3 stacks) fires '
          'only when the held count is 10. A Poison dispel removes one stack (the engine default: a reward that buys '
          'time, never a replacement for the swap). A separate debuff from Venom, so the Broodlings do not hunt the '
          "tank. Venom Sting 5416's SV 2617 (the SP's Poison 744 is a 3 s impact). AuraInterruptFlags CHANGE_MAP.",
    raw_overrides=kit_raw('Poisoned by her bite: taking Nature damage every $t1 sec for each stack. The other tank '
                          'takes her at 3 stacks.', 'Taking Nature damage every $t1 sec for each stack.',
                          CastingTimeIndex=1, CumulativeAura=BITE_STACKS, DefenseType=_DEFENSE_MAGIC,
                          EffectMiscValueB_1=BITE_TICK, SpellVisualID_1=SW_VENOM, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(widows_bite_210128, 'spell_dungeon_refflat_periodic')

# --- SW7 Brood Call (heroic) -----------------------------------------------------------------------------------------

brood_call_210129 = cast_bar(
    210129, 'Brood Call', BROOD_CALL_CAST_MS, 'She calls to her brood.',
    f'{_B4}, SW7 (heroic): the 3 s chitter every 30 s from 25 s (emote line 1), on her. A cast bar, NOT '
    'interruptible (ruling 34: a set piece on a timer): at its end every egg within 15 yd of her hatches, 3 Broodlings '
    "each onto the player nearest it, no damage. Hatch Eggs 58542's SV 11329 (a shadow nova on her); the burst on "
    'each egg is the Hatch look (210130).',
    icon=_ICON_HATCH_EGGS, visual=SW_BROOD_CALL, school=School.SHADOW,
)

# The stack caps are the aura counters of the two Venoms: a test pins them to SmolderwebLogic.h.
assert math.ceil(3052 * BROODLING_HEALTH_MODIFIER) == 2000
