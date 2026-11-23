"""
Scarlet Monastery build WP-D2: Ironspine (6489), "Spare Parts in a rotting yard"
(.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D2, s3.6, s3.8, s3.10, s7 #24 A;
build spec docs/dungeons/scarlet-monastery-1-graveyard.md GY 378-433). WP-D2 owns this file (its spells:
kSpellsIronspine 212350-212389 in modules/mod-dungeon-bosses src/ScarletMonastery/ScarletMonasteryRework.h;
IronspineLogic.h names the same ids).

- 6489 Ironspine: boss_ironspine_rework (SmartAI off: WP-S0's rev dropped the rows, the 90% despawn on AI init, Curse
  of Weakness 702 and Poison Cloud 3815 with them), normal HealthModifier 34.059 (36k on the level 32 warrior base
  1,057), stun immune (1972), INSTANCE_BIND, DamageModifier 2.4 (the stock base value). Heroic 240k and the tier's melee
  are WP-H's heroic template (source/world/dungeons/scarlet_monastery.py). His spawn (guid 12164) moves to the lawn in
  data/sql/updates/pending_db_world/rev_ironspine_scarlet_monastery.sql (s7 #24 A), with the texts.
- 300900 Ironspine's Fist, 300901 Ironspine's Ribcage, 300902 Ironspine's Eye (IR2): the three parts, each 3,000
  health on normal (HealthModifier 2.83823 on the level 32 warrior base 1,057; heroic 20,000 through WP-H's overrides
  on their heroic templates, the mint order of heroic_ids.lock: `difficulty_entry_1` below once H has minted them).
  Undead (faction 21, type 6), level 32, stun immune like him (1972: only killing a part stops it), no melee, no loot,
  no XP. npc_sm_ironspine_part (a passive NullCreatureAI): the boss throws, moves, reattaches and despawns them. Models
  are WP-V's picks (VISUALS): the Fist SC_BoneArm_01 (a stand animation only: its hops are script jump arcs), the
  Ribcage Marrowgar's bone spike (RISKY: a spike, not a ribcage), the Eye the Eye of Kilrogg.

Spells (Spell.dbc 3.3.5 for every stock id and icon quoted; looks from ._visuals):

  212350  Grave Rot          IR1 the 1.5 s cast bar (Nature), emote line 0; the registry pool is the hit
  212351  Grave Rot          IR1 / IR5 / IR2 a pool's tick: resolve copy, Nature, 5% / 8% a second (tank too)
  212352  Grave Rot          IR1 the pool's look at 7 yd (V's SV 90550, the stalker's state aura)
  212353  Grave Rot          IR1 ... 8 yd (90551, heroic growth)
  212354  Grave Rot          IR1 ... 9 yd (90552)
  212355  Grave Rot          IR1 ... 10 yd (90553)
  212356  Shatter            IR2 a part breaks off: Bone Shards' SV 4362 on him (look only)
  212357  Reassembled        IR2 +10% damage done per stack (3 at most on normal: the script caps it; no cap on heroic)
  212358  Reassemble         IR2 a part reattaches: heals him 10% / 15% (base point 0 from the script)
  212359  Fist Slam          IR3 a hop's landing: resolve copy, Physical, 35% / 45% + Weakened (tank too)
  212360  Fist Slam          IR3 the landing's look, the Fist on itself (Ground Slam's SV 8083)
  212361  Crush              IR4 the cage's hold: a root (root mechanic: a root break frees the player), 12 s
  212362  Crush              IR4 a squeeze: Physical, base point 0 from the script (RefFlatOn), ignores armor
  212363  Ribcage Closed     IR4 on the cage while it holds anyone (the bots' "Ribcage first" condition)
  212364  Eye of Ironspine   IR5 the 2 s mark on a player a pool will land under
  212365  Glare              IR6 the Eye's 2 s cast bar (heroic), Eyebeam's SV 9205
  212366  Glare              IR6 the 2 s stun on a player facing the Eye
  212367-212389 spare
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import self_visual, timer_aura
from lib.dsl.registry import (
    creature_model,
    creature_template,
    creature_template_columns,
    custom_attr,
    spell,
)

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_UNDEAD,
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
    DISPLAY_IRONSPINE_EYE,
    DISPLAY_IRONSPINE_FIST,
    DISPLAY_IRONSPINE_RIBCAGE,
    EYE_SCALE_RANGE,
    FIST_SCALE_RANGE,
    IR_CRUSH_HELD,
    IR_FIST_LANDING,
    IR_GLARE,
    IR_REASSEMBLED,
    IR_SHATTER,
    SV_GRAVE_ROT,
)

_D2 = 'Scarlet Monastery build WP-D2 (Ironspine)'

creature_template_columns(6489, **boss_columns(
    'boss_ironspine_rework', 34.059, damage_modifier=2.4,
))

# --- Boss-kit creatures (IR2: the parts) ------------------------------------------------------------------------------

# The parts' heroic templates (WP-H mints them in heroic_ids.lock; `extra=` in scarlet_monastery.py). Filled in once H
# has minted them: {entry: heroic entry}. Until then the normal rows carry no difficulty_entry_1 (Shared-file request in
# the D2 report).
PART_HEROIC_ENTRIES: dict[int, int] = {300900: 310458, 300901: 310459, 300902: 310460}

# Level 32 warrior base 1,057: ceil(1,057 x 2.83823) = 3,000 (GY "Each part": 3k normal, 20k heroic).
PART_HEALTH_MODIFIER = 2.83823
_PART_SCRIPT = 'npc_sm_ironspine_part'
_FLAGS_EXTRA_NO_XP = 0x40


def _part(entry: int, name: str):
    columns = {
        **KIT_CREATURE, 'faction': FACTION_UNDEAD, 'type': 6, 'minlevel': 32, 'maxlevel': 32, 'rank': 1,
        'unit_class': 1, 'unit_flags': 0, 'HealthModifier': PART_HEALTH_MODIFIER, 'DamageModifier': 0.0,
        'BaseAttackTime': 2000, 'ExperienceModifier': 0.0, 'RegenHealth': 0, 'lootid': 0, 'pickpocketloot': 0,
        'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': _PART_SCRIPT,
    }
    if entry in PART_HEROIC_ENTRIES:
        columns['difficulty_entry_1'] = PART_HEROIC_ENTRIES[entry]
    return creature_template(entry, name, **columns)


# The Fist and the Eye are small models: the middle of WP-V's creature scale range (2.5 to 3).
_FIST_SCALE = sum(FIST_SCALE_RANGE) / 2
_EYE_SCALE = sum(EYE_SCALE_RANGE) / 2

ironspine_fist_300900 = _part(300900, "Ironspine's Fist")
creature_model(300900, display_id=DISPLAY_IRONSPINE_FIST, scale=_FIST_SCALE)
ironspine_ribcage_300901 = _part(300901, "Ironspine's Ribcage")
creature_model(300901, display_id=DISPLAY_IRONSPINE_RIBCAGE)
ironspine_eye_300902 = _part(300902, "Ironspine's Eye")
creature_model(300902, display_id=DISPLAY_IRONSPINE_EYE, scale=_EYE_SCALE)

# --- Constants -------------------------------------------------------------------------------------------------------
_TARGET_UNIT_TARGET_ENEMY = 6

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR0_NO_IMMUNITIES = 0x20000000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000

# SPELL_ATTR0_CU_IGNORE_ARMOR (SpellInfo.h SpellCustomAttributes): Unit::IsDamageReducedByArmor skips it.
_CU_IGNORE_ARMOR = 0x00008000
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a map change or a logout drops it.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SCHOOL_MASK_ALL = 127
_MECHANIC_ROOT = 7
_MECHANIC_STUN = 12
_DEFENSE_MAGIC = 1

_ICON_POISON_CLOUD = 149    # Poison Cloud 3815 (the stock cast Grave Rot replaces)
_ICON_BONE_SHARDS = 1590    # Bone Shards 17014
_ICON_BONE_ARMOR = 93       # Bone Armor 11445
_ICON_GROUND_SLAM = 2144    # Ground Slam 33525
_ICON_IMPALED = 2163        # Impaled 69065
_ICON_EYEBEAM = 184         # Eyebeam 40620

_SCRIPT_HEAL = 'Scarlet Monastery: a percent of his own health, base point 0 set by boss_ironspine_rework'
_SCRIPT_CRUSH = ('Scarlet Monastery: a percent of the reference row (DungeonKit::RefFlatOn, the boss the owner), base '
                 'point 0 set by boss_ironspine_rework')

# --- IR1 Grave Rot ---------------------------------------------------------------------------------------------------
grave_rot_cast_212350 = cast_bar(
    212350, 'Grave Rot', 1500, 'Retches up a pool of grave rot.',
    f'{_D2} IR1 Grave Rot (stock Poison Cloud 3815, changed): the 1.5 s cast (emote line 0) at 6 s, then every 14 s, 2 '
    's less per part killed for good (8 s at least). The registry pool registered beside it under him (the kit\'s '
    'GrowingZone, 212351 its tick) is the hit; the bar is what players read. Not kickable (the kit\'s cast bar: '
    'InterruptFlags 0, PreventionType 0; the descriptor lists it with priority 0). Icon of Poison Cloud.',
    icon=_ICON_POISON_CLOUD, school=School.NATURE,
)

grave_rot_212351 = resolve_copy(
    212351, 'Grave Rot', School.NATURE, 'Grave rot eats at anyone standing in it.',
    f'{_D2} IR1 / IR5 / IR2: a Grave Rot pool\'s tick, 5% (heroic 8%) of the reference row a second, the tank\'s row '
    'on the tank (TankDamage, same percent), no Weakened (a lingering patch). The 7 yd pools under him (normal: for '
    'the fight; heroic: 7 -> 10 yd over 30 s, gone at 60 s), under 2 players while the Eye is loose (2 s marker) and '
    'where a part is killed. Copy of the resolve spell 205004 (Nature). Icon of Poison Cloud.',
    icon=_ICON_POISON_CLOUD,
)


def _rot_look(spell_id: int, radius: int):
    # Not passive: a passive aura is never sent to the client, so its state visual would not show (custom-spells.md).
    return spell(
        id=spell_id, name='Grave Rot', school=School.NATURE, dispel=0, mechanic=0,
        attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG | _ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_POISON_CLOUD,
        notes=f'{_D2} IR1: the look of a {radius} yd Grave Rot pool. The kit\'s GrowingZone summons the generic '
              'stalker 300922 on the pool and casts the rung nearest the pool\'s radius on it (triggered), swapping '
              'it as a heroic pool grows: a hidden DUMMY aura whose StateKit is WP-V\'s minted rung (SV '
              f'{SV_GRAVE_ROT[radius]}, the stock goo_flow_state scaled to {radius} yd; never Slime Pool\'s SV 118, a '
              'one-shot puff). The registry zone owns the ticks.',
        raw_overrides=kit_raw('A pool of grave rot.', 'A pool of grave rot.', SpellVisualID_1=SV_GRAVE_ROT[radius],
                              AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG, CastingTimeIndex=1),
    )


grave_rot_look_7_212352 = _rot_look(212352, 7)
grave_rot_look_8_212353 = _rot_look(212353, 8)
grave_rot_look_9_212354 = _rot_look(212354, 9)
grave_rot_look_10_212355 = _rot_look(212355, 10)

# --- IR2 Shatter -----------------------------------------------------------------------------------------------------
shatter_212356 = self_visual(
    212356, 'Shatter', IR_SHATTER,
    f'{_D2} IR2 Shatter: a part breaks off (emote line 1), cast on himself (triggered) as the part is thrown 15-20 yd. '
    'Bone Shards 17014\'s SpellVisual 4362 (WP-V\'s alternate Reassembled look, a bone burst). Look only.',
    icon=_ICON_BONE_SHARDS,
)

reassembled_212357 = spell(
    id=212357, name='Reassembled', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=10,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BONE_ARMOR,
    notes=f'{_D2} IR2 Reassembled: +1 stack each time a part reaches him (a group failure: longer and harder, never '
          'lost). +10% damage dealt per stack (SPELL_AURA_MOD_DAMAGE_PERCENT_DONE, every school: his melee; the '
          'percent hits ignore caster modifiers). 3 stacks at most on normal (the group-failure cap below 60; the '
          'script caps it with DungeonKit::AddStacks), no cap on heroic (StackAmount 99). Lasts the fight, not '
          'dispellable. Bone Armor 11445\'s SpellVisual 2737 (a lasting bone state on the chest).',
    raw_overrides=kit_raw('Increases damage dealt by $s1% per application.', 'Damage dealt increased by $s1%.',
                          instant=True, CumulativeAura=99, SpellVisualID_1=IR_REASSEMBLED,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

reassemble_heal_212358 = spell(
    id=212358, name='Reassemble', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_SCRIPT_HEAL)],
    spell_icon_id=_ICON_BONE_ARMOR,
    notes=f'{_D2} IR2: a part reaches him and reattaches: he heals 10% (heroic 15%) of his maximum health (3,600 / '
          '36,000). Cast triggered on himself with base point 0 set from the script. Ignores caster modifiers; the '
          'healing-reduction effects on him (Mortal Strike, Wound Poison) still count.',
    raw_overrides=kit_raw('A part of him returns.', instant=True, InterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- IR3 the Fist ----------------------------------------------------------------------------------------------------
fist_slam_212359 = resolve_copy(
    212359, 'Fist Slam', School.NORMAL, 'Ironspine\'s Fist lands hard.',
    f'{_D2} IR3 Fist Slam: each knuckle-hop of the loose Fist (6 yd every 3 s toward him) lands on a 5 yd circle '
    'marked 2 s before: 35% (heroic 45%) of the reference row + Weakened, the tank\'s row on the tank (TankDamage). '
    'Its last hops land in the melee around him. Copy of the resolve spell 205001 (Physical). Icon of Ground Slam.',
    icon=_ICON_GROUND_SLAM,
)

fist_landing_212360 = self_visual(
    212360, 'Fist Slam', IR_FIST_LANDING,
    f'{_D2} IR3: a Fist landing\'s look, cast by the Fist on itself (triggered) as each hop lands (and as it lands '
    'from the Shatter). Ground Slam 33525\'s SpellVisual 8083 (a 6.9 yd ThunderClap ring and a shake; the marker '
    'carries the real 5 yd). Look only.',
    icon=_ICON_GROUND_SLAM,
)

# --- IR4 the Ribcage and the Crush -----------------------------------------------------------------------------------
crush_212361 = spell(
    id=212361, name='Crush', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_ROOT,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=12000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT, base_points=0,
                    mechanic=_MECHANIC_ROOT, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_IMPALED,
    notes=f'{_D2} IR4 Crush: the Ribcage closes over a random non-tank (heroic: and everyone within 6 yd of them, the '
          'tank too; emote line 3) and holds them: DungeonKit::HoldInUnit\'s holdSpell, applied by the cage (AddAura) '
          'for up to 12 s. A root (MOD_ROOT) with the root mechanic on the spell and the effect: the prisoner keeps '
          'every other action (heals, casts, attacks the cage from inside), and a root break (Hand of Freedom, Escape '
          'Artist, a shapeshift, root immunity) frees that player and ends their Crush (the script sees the aura go). '
          'The squeeze itself is 212362, ticked by the script while this aura holds. Dispel none; AuraInterruptFlags '
          'CHANGE_MAP. Impaled 69065\'s SpellVisual 15325 (the impaled pose on the prisoner).',
    raw_overrides=kit_raw('The ribs close and squeeze harder every 2 sec.',
                          'Rooted. The ribs squeeze harder every 2 sec. Break the cage or the root.', instant=True,
                          SpellVisualID_1=IR_CRUSH_HELD, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

crush_tick_212362 = spell(
    id=212362, name='Crush', school=School.NORMAL, attributes=_ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_CRUSH)],
    spell_icon_id=_ICON_IMPALED,
    notes=f'{_D2} IR4 the squeeze: every 2 s while a prisoner is held, the cage casts it on them (triggered) with base '
          'point 0 = DungeonKit::RefFlatOn(Ironspine, prisoner, pct): ticks weighted 1 to 6 that total 50% (heroic '
          '120%) of the reference row by the 12 s timeout (normal 2.4, 4.8, 7.1, 9.5, 11.9, 14.3%; IronspineLogic.h '
          'CrushTickPct). Heroic 120% kills an unhealed prisoner (hub ruling 14). Physical, but '
          'SPELL_ATTR0_CU_IGNORE_ARMOR (spell_custom_attr) so the percent is exact on cloth and plate alike; the '
          'resolve attribute set (no active defense, redirection or reflection, no threat, ignores LoS, cannot crit, '
          'always hits, ignores caster modifiers). The prisoner\'s Impaled pose is the hold\'s look.',
    raw_overrides=kit_raw('The ribs squeeze.', instant=True, DefenseType=_DEFENSE_MAGIC, InterruptFlags=0,
                          PreventionType=0,
                          AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
custom_attr(crush_tick_212362, _CU_IGNORE_ARMOR)

ribcage_closed_212363 = spell(
    id=212363, name='Ribcage Closed', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG | _ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_IMPALED,
    notes=f'{_D2} IR4: on the Ribcage while it holds anyone (cast on itself, triggered, when it closes; removed when '
          'the last prisoner is free). The bots\' kill order reads it: the Ribcage first while it holds a player '
          '(Condition::HasAura, BreakOut). A hidden DUMMY with no look.',
    raw_overrides=kit_raw(instant=True, AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- IR5 the Eye's sight ---------------------------------------------------------------------------------------------
eye_sight_212364 = timer_aura(
    212364, 'Eye of Ironspine', 2000, 'The Eye sees for him. Grave rot will well up under you after $d.',
    'Grave rot will well up under you. Move.',
    f'{_D2} IR5: while the Eye is loose, each Grave Rot also drops a pool under 2 random players (the tank included). '
    'Ironspine casts this 2 s mark on each (triggered) as their pool\'s 2 s marker goes down; the pool is a registry '
    'zone like his (212351). A DUMMY debuff with a clock, no effect of its own. Icon of Eyebeam 40620.',
    icon=_ICON_EYEBEAM, school=School.NATURE,
)

# --- IR6 the Eye's Glare (heroic) ------------------------------------------------------------------------------------
glare_cast_212365 = cast_bar(
    212365, 'Glare', 2000, 'Opens wide. Anyone facing it is held in its gaze.',
    f'{_D2} IR6 Glare (heroic): every 6 s while the Eye is loose (first 6 s after it lands), the Eye casts it (the '
    'Eye\'s line 0). The registry Gaze registered beside it (mod-boss-mechanics F13: players facing the Eye within 40 '
    'yd at the resolve) owns the hit; 212366 is its rider. Not kickable (the kit\'s cast bar). Eyebeam 40620\'s '
    'SpellVisual 9205 (a Beam_Red channel kit; the doc\'s Eye Beam SV 7434 has no beam). Icon of Eyebeam.',
    icon=_ICON_EYEBEAM, visual=IR_GLARE, school=School.SHADOW,
)

glare_212366 = spell(
    id=212366, name='Glare', school=School.SHADOW, dispel=0, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=2000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=_MECHANIC_STUN, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_EYEBEAM,
    notes=f'{_D2} IR6 (heroic): held in the Eye\'s gaze: a 2 s stun (the cost in place of Weakened, shared doc section '
          '4) on anyone facing the Eye when the Glare lands. The registry\'s rider (cast with Ironspine as the '
          'original caster). Stun mechanic (a trinket or stun immunity is a class tool against it); Dispel none; '
          'AuraInterruptFlags CHANGE_MAP. No look of its own (the stun pose).',
    raw_overrides=kit_raw('Held in the Eye\'s gaze.', 'Stunned.', instant=True,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
