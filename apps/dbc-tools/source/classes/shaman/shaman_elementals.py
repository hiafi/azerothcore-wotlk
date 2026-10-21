"""
Shaman - SH0b A4: the four elementals' data half (docs/reworks/shaman-shared-rework.md section 6 "Elementals", "Earth
Elemental", "Fire Elemental", "Water Elemental", "Storm Elemental"; .agents/plans/shaman-rework/shaman-rework.SH0b-WP-BRIEF.md
decisions 7, 10, 12, 13).

The two-step (CORE-AUDIT-A A5): the player summon puts an invisible, untargetable ELEMENTAL TOTEM in the element's slot,
and that totem's Index-0 passive (`creature_template_spell`) summons the guardian with SummonProperties 61. The guardian
summon must sit on Index 0 or the totem's despawn leaves the elemental behind (Unit::SetMinion reads Totem::GetSpell(),
m_spells[0]). Replacing, recalling, right-clicking, expiring or killing the totem therefore all dismiss the elemental.

Ids (brief id map): 202272 Water Elemental Totem (player, @46), 202273 Storm Elemental Totem (@56), 202274 / 202275 the
Water / Storm totem passives (SUMMON the guardian, 2 min), 202276 Water Bolt, 202277 its heal, 202278 Storm Bolt,
202279 the hidden owner-stat aura. Creatures: 300260 / 300261 Water / Storm guardians, 300270-300273 the Earth / Fire /
Water / Storm elemental totems. SkillLineAbility 30664 / 30665. Stock Earth / Fire Elemental (2062 / 2894, A1's rows) keep
their ids and their stock passives (33663 / 32982) on the new totems' Index 0.

Summon rows copy the stock 2062 / 2894 shape: Category 0, RecoveryTime 120000 (the elemental's own 2 min; the 2 min
lockout over the other three is scripted, `spell_sha_elemental_lockout`), no category recovery, no COOLDOWN_ON_EVENT,
GCD 1000 / 133 (the stock totem GCD, brief decision 4), cost 8 % of base mana ([tune]; 24 % until the 2026-10-20 smoke-test fix pass), 30 s duration, instant,
SUMMON with SummonProperties in EffectMiscValueB_1 (82 Water slot, 83 Air slot) so the totem is a real `Totem`. Family
bits: summon-family d0 b29 plus the element's own bit (Water d1 b21, Storm d1 b8). No tool item (Totem_n and
RequiredTotemCategoryID_n stay 0). AttributesEx6 NO_CATEGORY_COOLDOWN_MODS is Fire-only (stock 2894) and is not copied.

Guardian spells follow the warlock P8 shape (SpellLevel 1, no learn level, plain `me->CastSpell` from the guardian): they
are potency rows, so the generated correction applies through the normal CalcValue hook with the guardian as caster and
the owner's spell power flows in through the hidden owner-stat aura 202279. Water Bolt and its heal carry shaman family
bits (d2 b25 / d2 b24) so Restoration / Elemental talents can reach them through the owner's spell mods (the guardian's
GetSpellModOwner is the shaman); Storm Bolt carries none (shared doc: "no bit"). Aura texts are number-free.

Script bindings (brief script table; B3 writes them in spell_shaman_totems.cpp): `spell_sha_elemental_lockout` on 2062,
2894, 202272, 202273; `spell_sha_water_bolt` on 202276 (eff0 hit); `spell_sha_elemental_owner_stats` on 202279;
`spell_sha_elemental_engaged_aoe` on 12470 / 13376 and
`spell_sha_angered_earth_engaged` on 36213 (m2: stock AoEs hit only engaged enemies).
"""

from lib.dsl import AuraType, Effect, EffectType, RANGE_SELF, School
from lib.dsl.registry import (
    const, creature_model, creature_spell, creature_template, pot_text, scripted_by, skill_line_ability, spell,
    trained_by,
)

from . import _masks as m
from .shaman_resto_tooltips import shaman_healtotems_1224

SPELLFAMILY_SHAMAN = 11

SPELL_ATTR0_PASSIVE = 0x40
SPELL_ATTR0_DO_NOT_DISPLAY = 0x80
SPELL_ATTR0_NOT_SHAPESHIFTED = 0x10000
SPELL_ATTR4_NOT_IN_ARENA_OR_RATED_BATTLEGROUND = 0x10000   # stock 2062 / 2894 carry it
SPELL_ATTR7_SUMMON_PLAYER_TOTEM = 0x20                     # "Summons player-owned totem"

TARGET_UNIT_CASTER = 1
TARGET_UNIT_TARGET_ENEMY = 6
TARGET_UNIT_TARGET_ALLY = 21
TARGET_DEST_CASTER_SUMMON = 22     # stock 2062 / 2894 effect A
TARGET_DEST_CASTER_FRONT_LEFT = 42  # stock 5394 (Water slot)
TARGET_DEST_CASTER_BACK_RIGHT = 43  # stock 3738 / 8512 (Air slot)
TARGET_DEST_CASTER_32 = 32         # stock passives 32982 / 33663: the guardian lands next to the totem

SUMMON_PROPS_WATER = 82            # totem SummonProperties: Fire 63, Earth 81, Water 82, Air 83
SUMMON_PROPS_AIR = 83
SUMMON_PROPS_GUARDIAN = 61         # ally guardian, no slot (stock 32982 / 33663)

TRAINER_SHAMAN = 210
SKILL_LINE_ELEMENTAL = 375
SKILL_LINE_RESTORATION = 374
CLASS_MASK_SHAMAN = 64

SCHOOL_MASK_ALL_MAGIC = 126        # MOD_DAMAGE_DONE misc: Holy through Arcane
SCHOOL_MASK_ALL = 127              # MOD_HEALING_DONE misc

# Stock icons: Summon Water Elemental 31687 (mage), Thunderstorm 51490, Earth Elemental Totem 2062 (hidden aura).
ICON_WATER_ELEMENTAL = 2134
ICON_STORM_ELEMENTAL = 3080
ICON_WATERBOLT = 176               # stock Waterbolt 31707
ICON_LIGHTNING_BOLT = 62           # stock Lightning Bolt 403
ICON_EARTH_ELEMENTAL = 2289

# Stock visuals: Waterbolt 31707 SV 7875 (Ice cast kit, WaterBolt missile), Lightning Bolt 403 SV 173; totem cast 319.
SV_WATERBOLT = 7875
SV_LIGHTNING_BOLT = 173
SV_TOTEM_CAST = 319

# Stock elemental-totem passives (Index 0 of the Earth / Fire elemental totems) and display ids.
SPELL_STOCK_EARTH_ELEMENTAL_PASSIVE = 33663   # summons Greater Earth Elemental 15352
SPELL_STOCK_FIRE_ELEMENTAL_PASSIVE = 32982    # summons Greater Fire Elemental 15438
DISPLAY_EARTH_TOTEM = 4588
DISPLAY_FIRE_TOTEM = 4589
DISPLAY_WATER_TOTEM = 4587
DISPLAY_AIR_TOTEM = 4590
DISPLAY_WATER_ELEMENTAL = 525      # mage Water Elemental (creature 510)
DISPLAY_WIND_ELEMENTAL = 8714      # air elemental (creatures 5898, 11576)

UNIT_FLAG_NON_ATTACKABLE = 0x2
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
UNIT_FLAG2_2048 = 2048             # every stock totem / elemental carries it

NOTE = 'shaman-rework SH0b A4: '

# =====================================================================================================================
# Script numbers (generated into ShamanData::)
# =====================================================================================================================
ELEMENTAL_LOCKOUT_MS = const('ELEMENTAL_LOCKOUT_MS', 120000,
                             'Base shared lockout over the other three elementals, ms [fixed] (30 s with Conduit later); '
                             'divided by (1 + Cooldown Haste).')
WATER_BOLT_HEAL_TARGETS = const('WATER_BOLT_HEAL_TARGETS', 3, 'Players Water Bolt heals, lowest health percent first [fixed].')
WATER_BOLT_HEAL_RANGE_YD = const('WATER_BOLT_HEAL_RANGE_YD', 40.0, 'Radius around the Water Elemental that Water Bolt heals, yd [fixed].')
ELEMENTAL_CHASE_RANGE_YD = const('ELEMENTAL_CHASE_RANGE_YD', 30.0, 'Water / Storm Elemental chase to within this range of the target, yd [tune].')
ELEMENTAL_TARGET_RANGE_YD = const('ELEMENTAL_TARGET_RANGE_YD', 40.0, 'Engaged-target search radius of every elemental, yd [tune].')
ELEMENTAL_STAT_REFRESH_MS = const('ELEMENTAL_STAT_REFRESH_MS', 2000, 'Owner-stat aura refresh period on Water / Storm Elementals, ms [tune].')
ELEMENTAL_TOTEM_DISPLAY_INVISIBLE = const('ELEMENTAL_TOTEM_DISPLAY_INVISIBLE', 11686,
                                          'Invisible-stalker display the elemental totems switch to in IsSummonedBy.',
                                          cpp_type='uint32')


# =====================================================================================================================
# Spells
# =====================================================================================================================
def _summon_raw(spell_level, props, description, element_mask):
    """Columns the two player summons carry (the stock 2062 / 2894 raw block, minus the tool columns)."""
    return {
        'AttributesEx4': SPELL_ATTR4_NOT_IN_ARENA_OR_RATED_BATTLEGROUND,
        'AttributesEx7': SPELL_ATTR7_SUMMON_PLAYER_TOTEM,
        'BaseLevel': spell_level,
        'SpellLevel': spell_level,
        'CastingTimeIndex': 1,
        'DefenseType': 1,
        'Description_Lang_enUS': description,
        'EffectMiscValueB_1': props,
        'EquippedItemClass': -1,
        'ProcChance': 101,
        'RangeIndex': 1,
        'SpellClassSet': SPELLFAMILY_SHAMAN,
        'SpellClassMask_1': m.SUMMON_D0_B29,
        'SpellClassMask_2': element_mask,
        'SpellVisualID_1': SV_TOTEM_CAST,
        'StartRecoveryCategory': 133,
        'StartRecoveryTime': 1000,
    }


storm_elemental_totem_202273 = spell(
    id=202273, name='Storm Elemental Totem', school=School.NORMAL, attributes=SPELL_ATTR0_NOT_SHAPESHIFTED, category=0,
    cast_time_ms=0, cooldown_ms=120000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=8, range_yards=RANGE_SELF,
    duration_ms=30000,
    effects=[Effect(
        type=EffectType.SUMMON, base_points=3887, implicit_target_a=TARGET_DEST_CASTER_SUMMON,
        implicit_target_b=TARGET_DEST_CASTER_BACK_RIGHT, misc_value=300273, radius_yards=5.0,
    )],
    spell_icon_id=ICON_STORM_ELEMENTAL,
    notes=NOTE + 'Storm Elemental, learned at 56 (trainer 210). Summons the invisible Air slot totem 300273 (props 83), '
          'whose Index-0 passive 202275 summons the guardian 300261. Same cooldown / category / GCD / cost [tune] / '
          'HP as 202272, Air\'s back-right spawn point (3738 / 8512). Family d0 b29 + d1 b8. Bound to '
          'spell_sha_elemental_lockout. Icon 3080 = Thunderstorm (placeholder, art is the V stage).',
    raw_overrides=_summon_raw(
        56, SUMMON_PROPS_AIR,
        'Calls forth a greater storm elemental for $d that strikes your enemies with lightning. 2 min cooldown.',
        m.STORM_ELEMENTAL_SUMMON),
)


def _guardian_passive(spell_id, name, creature, icon, notes):
    """The totem's Index-0 passive: SUMMON the guardian (props 61), 2 min. Stock 32982 / 33663 shape (instant, so the
    totem is a TOTEM_PASSIVE; summon next to the totem); their dead SPAWN and trigger effects are not copied. The
    guardian outlives nothing: the totem is the clock (30 s) and its removal despawns the guardian."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=120000,
        effects=[Effect(
            type=EffectType.SUMMON, implicit_target_a=TARGET_DEST_CASTER_32, misc_value=creature, radius_yards=5.0,
        )],
        spell_icon_id=icon, notes=NOTE + notes,
        raw_overrides={
            'CastingTimeIndex': 1, 'EffectMiscValueB_1': SUMMON_PROPS_GUARDIAN, 'EquippedItemClass': -1,
            'ProcChance': 101, 'RangeIndex': 1,
            'Description_Lang_enUS': 'Summons the elemental that fights for the shaman while its totem stands.',
        },
    )


water_elemental_passive_202274 = _guardian_passive(
    202274, 'Water Elemental Totem Passive', 300260, ICON_WATER_ELEMENTAL,
    'Index-0 passive of totem 300272 (creature_spell): SUMMON guardian 300260, props 61, 2 min. Hidden, no family bits.')
storm_elemental_passive_202275 = _guardian_passive(
    202275, 'Storm Elemental Totem Passive', 300261, ICON_STORM_ELEMENTAL,
    'Index-0 passive of totem 300273 (creature_spell): SUMMON guardian 300261, props 61, 2 min. Hidden, no family bits.')

# ---- Water Bolt (guardian-cast, potency 100 Frost; heal 10 Nature to the 3 most injured players) ----
water_bolt_heal_202277 = spell(
    id=202277, name='Water Bolt', school=School.NATURE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(
        type=EffectType.HEAL, sp_potency=10.0, potency_kind='heal', time_basis_ms=2000,
        implicit_target_a=TARGET_UNIT_TARGET_ALLY,
    )],
    spell_icon_id=ICON_WATERBOLT,
    notes=NOTE + 'Water Bolt\'s heal (shared doc: Nature school, 10 potency each, T 2000 = the bolt\'s 2 s cast, about 141 at 60), '
          'cast by spell_sha_water_bolt from the Water Elemental on up to 3 lowest-percent players within 40 yd (pets never '
          'chosen) as a triggered plain CastSpell, caster = the guardian (no owner GUID, so it rolls none of the shaman\'s '
          'procs). range_yards 50000 (RangeIndex 13): the targets sit anywhere near the elemental (L6). Family d2 b24 so '
          'Purification-style talents reach it. SpellLevel 1 (no learn level, warlock P8 shape).',
    raw_overrides={
        'SpellClassSet': SPELLFAMILY_SHAMAN, 'SpellClassMask_3': m.WATER_BOLT_HEAL, 'EquippedItemClass': -1,
        'DefenseType': 1, 'PreventionType': 1, 'SpellLevel': 1, 'CastingTimeIndex': 1, 'AttributesEx2': 0x4,
        'Description_Lang_enUS': 'Heals the target for {pot1}.',
    },
)

water_bolt_202276 = spell(
    id=202276, name='Water Bolt', school=School.FROST, attributes=0, cast_time_ms=2000, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=45.0,
    effects=[Effect(
        type=EffectType.SCHOOL_DAMAGE, sp_potency=43.0, potency_kind='direct', implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
    )],
    spell_icon_id=ICON_WATERBOLT,
    notes=NOTE + 'the Water Elemental\'s only ability (shared doc "Water Elemental"): 2 s cast, 43 potency Frost damage '
          '(was 100; x0.43 smoke-test fix pass 2026-10-20) (T 2000 = the cast); spell_sha_water_bolt (eff0 hit) heals the 3 lowest players via 202277. Plain CastSpell from '
          'the guardian, SpellLevel 1 (warlock P8 shape). Range 45 yd = stock Waterbolt 31707 (RangeIndex 36); the AI '
          'chases to 30 yd and searches 40 yd (consts). Missile speed 16 and SV 7875 are Waterbolt\'s ("mage Waterbolt" '
          'visual). Family d2 b25.',
    raw_overrides={
        'SpellClassSet': SPELLFAMILY_SHAMAN, 'SpellClassMask_3': m.WATER_BOLT_DAMAGE, 'EquippedItemClass': -1,
        'DefenseType': 1, 'PreventionType': 1, 'SpellLevel': 1, 'Speed': 16.0, 'SpellVisualID_1': SV_WATERBOLT,
        'Description_Lang_enUS': 'Hurls a bolt of water that deals {pot1} Frost damage to an enemy and heals the 3 most '
                                 'injured allies within 40 yards for ' + pot_text(water_bolt_heal_202277, var='wel') + ' each.',
    },
    tooltip_vars=shaman_healtotems_1224,
)

water_elemental_totem_202272 = spell(
    id=202272, name='Water Elemental Totem', school=School.NORMAL, attributes=SPELL_ATTR0_NOT_SHAPESHIFTED, category=0,
    cast_time_ms=0, cooldown_ms=120000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=8, range_yards=RANGE_SELF,
    duration_ms=30000,
    effects=[Effect(
        type=EffectType.SUMMON, base_points=3887, implicit_target_a=TARGET_DEST_CASTER_SUMMON,
        implicit_target_b=TARGET_DEST_CASTER_FRONT_LEFT, misc_value=300272, radius_yards=5.0,
    )],
    spell_icon_id=ICON_WATER_ELEMENTAL,
    notes=NOTE + 'Water Elemental, learned at 46 (trainer 210). Summons the invisible Water slot totem 300272 (props 82), '
          'whose Index-0 passive 202274 summons the guardian 300260. Category 0 / RecoveryTime 120000 / no category '
          'recovery / no COOLDOWN_ON_EVENT; GCD 1000/133 (stock totem); cost 8% of base mana [tune] (was 24%, Earth Elemental\'s; 2026-10-20 smoke-test fix pass); '
          'shape and HP (3887) copied from stock 2894 with Water\'s front-left spawn point (5394). Family d0 b29 + d1 b21. '
          'Bound to spell_sha_elemental_lockout. Icon 2134 = mage Summon Water Elemental.',
    raw_overrides=_summon_raw(
        46, SUMMON_PROPS_WATER,
        'Calls forth a greater water elemental for $d. Its Water Bolt damages an enemy and heals your 3 most injured '
        'allies for ' + pot_text(water_bolt_heal_202277, var='wel') + ' each. 2 min cooldown.',
        m.WATER_ELEMENTAL_SUMMON),
    tooltip_vars=shaman_healtotems_1224,   # S2a WP-R L4: the heal number (Tidecaller, Purification) on the tooltip the player reads
)

# ---- Storm Bolt (guardian-cast, potency 120 Nature, no family bit) ----
storm_bolt_202278 = spell(
    id=202278, name='Storm Bolt', school=School.NATURE, attributes=0, cast_time_ms=2000, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=45.0,
    effects=[Effect(
        type=EffectType.SCHOOL_DAMAGE, sp_potency=51.6, potency_kind='direct', implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
    )],
    spell_icon_id=ICON_LIGHTNING_BOLT,
    notes=NOTE + 'the Storm Elemental\'s only ability (shared doc "Storm Elemental"): 2 s cast, 51.6 potency Nature damage '
          '(was 120 / about 428 at 60; x0.43 smoke-test fix pass 2026-10-20; about 184 now, T 2000 = the cast), no heal, no family bit (SpellClassSet 11 with an empty mask). Plain '
          'CastSpell from the guardian, SpellLevel 1. Range 45 yd (same as Water Bolt, so both guardians have equal '
          'reach). Missile speed 20 and SV 173 are Lightning Bolt\'s.',
    raw_overrides={
        'SpellClassSet': SPELLFAMILY_SHAMAN, 'EquippedItemClass': -1, 'DefenseType': 1, 'PreventionType': 1,
        'SpellLevel': 1, 'Speed': 20.0, 'SpellVisualID_1': SV_LIGHTNING_BOLT,
        'Description_Lang_enUS': 'Strikes an enemy with lightning for {pot1} Nature damage.',
    },
)

# ---- Hidden owner-stat aura (H1): the owner's spell power as damage and healing done, script-refreshed ----
elemental_owner_stats_202279 = spell(
    id=202279, name='Elemental Spell Power', school=School.NATURE,
    attributes=SPELL_ATTR0_PASSIVE | SPELL_ATTR0_DO_NOT_DISPLAY, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_DONE, base_points=-1,
               implicit_target_a=TARGET_UNIT_CASTER, misc_value=SCHOOL_MASK_ALL_MAGIC),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE, base_points=-1,
               implicit_target_a=TARGET_UNIT_CASTER, misc_value=SCHOOL_MASK_ALL),
    ],
    spell_icon_id=ICON_EARTH_ELEMENTAL,
    notes=NOTE + 'H1: the Water / Storm Elemental\'s inheritance of the owner\'s spell power ("Inherits from the player: level, '
          'and spell power for spell potency"). eff0 aura 13 (all magic schools, mask 126) + eff1 aura 135 (healing, mask '
          '127); stored base points -1 = live 0 until spell_sha_elemental_owner_stats sets both amounts to the owner\'s spell '
          'power (aura script, refreshed every ELEMENTAL_STAT_REFRESH_MS; the damage amount is the owner\'s spell power in the guardian\'s own bolt school only: Frost for Water, Nature for Storm). Added by the owner in IsSummonedBy through '
          'Shaman::RefreshElementalAuras (L5: owner-cast auras on a guardian are added by the owner). Hidden passive, '
          'infinite (ends with the guardian), no family bits, nothing else inherited (versatility / crit / haste stay 0).',
    raw_overrides={
        'SpellClassSet': SPELLFAMILY_SHAMAN, 'EquippedItemClass': -1, 'SpellLevel': 1, 'CastingTimeIndex': 1,
        'Description_Lang_enUS': 'The elemental deals and heals for the strength of its summoner\'s spell power.',
    },
)

# =====================================================================================================================
# Creatures
# =====================================================================================================================
# Elemental totems (decision 10): 15430 / 15439's columns, untargetable (NON_ATTACKABLE | NOT_SELECTABLE, A5 point 3),
# the invisible-totem AI (display 11686 is set in IsSummonedBy). Index 0 = the guardian-summoning passive.
def _elemental_totem(entry, name, display, health_modifier):
    row = creature_template(
        entry, name, subname='', minlevel=1, maxlevel=80, faction=14, speed_walk=1.0, speed_run=1.0, speed_swim=1.0,
        speed_flight=1.0, detection_range=20.0, unit_class=1,
        unit_flags=UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE, unit_flags2=UNIT_FLAG2_2048, type=11,
        BaseAttackTime=2000, RangeAttackTime=2000, HealthModifier=health_modifier, flags_extra=0,
        ScriptName='npc_sha_elemental_totem',
    )
    creature_model(entry, display_id=display)
    return row


earth_elemental_totem_300270 = _elemental_totem(300270, 'Earth Elemental Totem', DISPLAY_EARTH_TOTEM, 1.3)   # 15430
fire_elemental_totem_300271 = _elemental_totem(300271, 'Fire Elemental Totem', DISPLAY_FIRE_TOTEM, 1.0)      # 15439
water_elemental_totem_300272 = _elemental_totem(300272, 'Water Elemental Totem', DISPLAY_WATER_TOTEM, 1.0)   # 15439 shape
storm_elemental_totem_300273 = _elemental_totem(300273, 'Storm Elemental Totem', DISPLAY_AIR_TOTEM, 1.0)    # 15439 shape

creature_spell(300270, 0, SPELL_STOCK_EARTH_ELEMENTAL_PASSIVE)
creature_spell(300271, 0, SPELL_STOCK_FIRE_ELEMENTAL_PASSIVE)
creature_spell(300272, 0, water_elemental_passive_202274)
creature_spell(300273, 0, storm_elemental_passive_202275)


# Water / Storm guardians (decision 12): 15438's columns (type 4 elemental, faction overwritten by SummonGuardian from the
# owner, selectable, hostile-engaging), NOT the warlock _GUARDIAN_COMMON (that one is unselectable). Level set from the
# owner at summon. unit_class 2 (mana) for Water, 1 for Storm; HealthModifier / ManaModifier from 15438 [tune].
def _guardian(entry, name, display, unit_class, script):
    row = creature_template(
        entry, name, subname='', minlevel=1, maxlevel=80, faction=14, speed_walk=1.0, speed_run=1.14286, speed_swim=1.0,
        speed_flight=1.0, detection_range=20.0, unit_class=unit_class, unit_flags=0, unit_flags2=UNIT_FLAG2_2048,
        type=4, DamageModifier=1.0, BaseAttackTime=2000, RangeAttackTime=2000, HealthModifier=1.0, ManaModifier=1.0,
        flags_extra=0, ScriptName=script,
    )
    creature_model(entry, display_id=display)
    return row


water_elemental_guardian_300260 = _guardian(300260, 'Greater Water Elemental', DISPLAY_WATER_ELEMENTAL, 2, 'npc_sha_water_elemental')
storm_elemental_guardian_300261 = _guardian(300261, 'Greater Storm Elemental', DISPLAY_WIND_ELEMENTAL, 1, 'npc_sha_storm_elemental')

creature_spell(300260, 0, water_bolt_202276)
creature_spell(300261, 0, storm_bolt_202278)

# Stock guardians (decision 13): ids are hard-coded in Pet.cpp (stat scaling by NPC_FIRE_ELEMENTAL / NPC_EARTH_ELEMENTAL) and
# spell_shaman.cpp:353 (Fire Elemental's AP inheritance), so the entries stay; only the AI changes. An existing entry keeps
# every unmentioned column.
greater_fire_elemental_15438 = creature_template(15438, 'Greater Fire Elemental', ScriptName='npc_sha_fire_elemental_rework')
greater_earth_elemental_15352 = creature_template(15352, 'Greater Earth Elemental', ScriptName='npc_sha_earth_elemental_rework')

# =====================================================================================================================
# Bindings, trainer rows (Earth / Fire's are A1's, next to their rows), SkillLineAbility
# =====================================================================================================================
# The lockout fires after any of the four summons; stock ids by bare number (A1 rewrites the rows in shaman_spells.py).
for _lockout_spell in (2062, 2894, water_elemental_totem_202272, storm_elemental_totem_202273):
    scripted_by(_lockout_spell, 'spell_sha_elemental_lockout')
scripted_by(water_bolt_202276, 'spell_sha_water_bolt')
scripted_by(water_bolt_heal_202277, 'spell_sha_resto_water_bolt_heal')   # S2a: x Totemic Resonance (guardian heal)
scripted_by(elemental_owner_stats_202279, 'spell_sha_elemental_owner_stats')
# SH0b m2: the stock area abilities of the Earth / Fire Elementals hit only enemies already engaged with the owner or the
# group (a player-owned elemental only; NPC casters keep the stock targeting). Stock ids by bare number, no prior binding.
scripted_by(12470, 'spell_sha_elemental_engaged_aoe')   # Fire Nova, eff0 22/15
scripted_by(13376, 'spell_sha_elemental_engaged_aoe')   # Fire Shield pulse (13377 triggers it), eff0 22/15
scripted_by(36213, 'spell_sha_angered_earth_engaged')   # Angered Earth, eff0 ATTACK_ME + eff1 threat, both 22/15

trained_by(water_elemental_totem_202272, TRAINER_SHAMAN, 46)
trained_by(storm_elemental_totem_202273, TRAINER_SHAMAN, 56)

skill_line_ability(id=30664, skill_line=SKILL_LINE_RESTORATION, spell_id=water_elemental_totem_202272.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30665, skill_line=SKILL_LINE_ELEMENTAL, spell_id=storm_elemental_totem_202273.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
