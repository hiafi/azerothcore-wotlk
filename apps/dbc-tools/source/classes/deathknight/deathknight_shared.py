"""
Death Knight - DK0a shared rows: Blood Presence (the tank aura) and its crit-immunity child, the Anti-Magic Zone aura,
Death's Caress, and the three stock rows whose only change is a SpellLevel move (Death Grip, Death Gate, Path of Frost).

Source of truth: docs/reworks/death-knight-shared-rework.md (Blood Presence, Death's Caress, Anti-Magic Zone, the learn
level table), .agents/plans/death-knight-rework/death-knight-rework.DK0a-WP-BRIEF.md (rulings 5, 8, 10, 12 win over the
handoff), DK0a-HANDOFF.md known-hard items 2, 6, 7, 11, DK0a-0VERIFY.md (items 2, 4, 6, 8, 18, 19) and the passed P0
spike shapes (Blood Presence copy 203682 / crit child 203683, p0-spike-ref/deathknight_p0_spike.py).

Ids: 203000 Blood Presence crit-immunity child, 203001 Death's Caress (SkillLineAbility 30720). 48266, 50461, 49576, 50977
and 3714 keep their stock ids (the presence hardcode in SpellInfo.cpp keys on 48266). 48266, 50461, 49576 and 50977 were
pulled out of source/spells/npc.csv / generic.csv into this file (pull_dsl.py); 3714 was stock-DBC only.

Conventions: Blood Presence stays on the Rune power type with RuneCostID 0 (no cost) and off the GCD (StartRecovery 0 / 0);
the hidden child is passive + DO_NOT_DISPLAY with AttributesEx3 ALLOW_AURA_WHILE_DEAD and AttributesEx2 ALLOW_DEAD_TARGET so
it follows its parent through death, no family bits (Rockbiter child 202200 shape); EquippedItemClass -1 on every row; aura
texts are number-free; family bits come from _masks.py. The two script numbers live in the generated DeathKnightData.h.
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, RANGE_SELF, School
from lib.dsl.registry import (
    const, custom_attr, linked_spell, scripted_by, skill_line_ability, spell, spell_rune_cost, unbind_script,
)

from . import _masks as m

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_ATTR0_PASSIVE = 0x40
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_DO_NOT_SHEATH = 0x40000
_ATTR2_ALLOW_DEAD_TARGET = 0x1
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000
_SPELLFAMILY_DEATHKNIGHT = 15

# Stock 48266 Blood Presence frame (var/extractors/dbc/Spell.dbc 0xA9050010 / 0x80000400) minus the two bits the rework
# clears: Attributes NO_AURA_CANCEL 0x80000000 (right-click cancels it) and AttributesEx CAST_WHEN_LEARNED 0x80000000
# (it is no longer cast on learn, DK0a decision D4).
_BLOOD_PRESENCE_ATTR0 = 0xA9050010 & ~0x80000000   # 0x29050010
_BLOOD_PRESENCE_ATTR1 = 0x80000400 & ~0x80000000   # 0x400
_BLOOD_PRESENCE_CATEGORY = 47                       # shared by the three stock presences
_BLOOD_PRESENCE_ICON = 2636

# ---- Aura types not in the DSL enum (src/server/game/Spells/Auras/SpellAuraDefines.h) ----
_AURA_MOD_ATTACKER_MELEE_CRIT_CHANCE = 187
_AURA_MOD_ATTACKER_RANGED_CRIT_CHANCE = 188

# ---- Misc values / targets (SharedDefines.h) ----
_MISC_ALL_SCHOOLS = 127
_MISC_NON_PHYSICAL_SCHOOLS = 126                    # stock 50461 EffectMiscValue: every school but Physical
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_DEST_TARGET_ENEMY = 53

# Script numbers (D8 tier 3: not tooltip numbers, not potency).
DEATHS_CARESS_EXTRA_TARGETS = const(
    'DEATHS_CARESS_EXTRA_TARGETS', 2,
    'Additional nearby enemies Death\'s Caress hits besides its target [fixed].',
)
AMZ_SPELL_REDUCTION_PCT = const(
    'AMZ_SPELL_REDUCTION_PCT', 75,
    'Percent of spell damage the Anti-Magic Zone absorbs while its shared pool lasts (stock 75) [fixed].',
)

# =====================================================================================================================
# Blood Presence (shared doc "Blood Presence"): the tank aura, a toggle off the GCD
# =====================================================================================================================

# The crit-immunity child (Rockbiter child 202200 / spike 203683 shape): attacker melee / ranged crit chance stored -1001
# (live -1000, far past any crit chance). Added and removed with 48266 by the spell_linked_spell type 2 row below.
blood_presence_crit_immunity_203000 = spell(
    id=203000, name='Blood Presence Crit Immunity', school=School.NORMAL,
    attributes=_ATTR0_PASSIVE | _ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, power_type=PowerType.MANA, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_ATTACKER_MELEE_CRIT_CHANCE, base_points=-1001,
               implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_ATTACKER_RANGED_CRIT_CHANCE, base_points=-1001,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_BLOOD_PRESENCE_ICON,
    notes='DK0a, shared doc "Blood Presence": hidden passive child of 48266 (spell_linked_spell type 2, SpellAuras.cpp '
          'HandleAuraSpecificMods adds and removes it with the parent). eff0 / eff1 attacker melee / ranged crit chance '
          '-1001 (live -1000) = crit immunity. No family bits, no SkillLineAbility. AttributesEx3 0x100000 + '
          'AttributesEx2 0x1 so it follows the parent through death. Shape of the passed P0 spike 203683.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT,
        'EquippedItemClass': -1,
        'SpellLevel': 1,
        'CastingTimeIndex': 1,
        'AttributesEx2': _ATTR2_ALLOW_DEAD_TARGET,
        'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD,
        'Description_Lang_enUS': 'You are immune to critical strikes from melee and ranged attacks.',
    },
)

# Stock 48266 rewritten in place (the SPELL_SPECIFIC_PRESENCE hardcode in SpellInfo.cpp keys on the id). eff0 aura 79
# stored -6 = -5% damage done; eff1 aura 10 (MOD_THREAT) stored 44 = +45% threat (doc [tune], stock Frost Presence's);
# stock eff1 aura 118 and eff2 aura 10 -20% are gone, so the third slot builds empty. Rune power type with RuneCostID 0
# (no cost; stock cost 1 Blood Rune, RuneCostID 484), StartRecovery 0 / 0 (off the GCD) and the 1 s category cooldown
# stay. AttributesEx2 0x11 keeps USE_SHAPESHIFT_BAR so it sits on the stance bar. SpellLevel 10 (trainer level, was 55).
blood_presence_48266 = spell(
    id=48266,
    name='Blood Presence',
    school=School.NORMAL,
    attributes=_BLOOD_PRESENCE_ATTR0,
    category=_BLOOD_PRESENCE_CATEGORY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=1000,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=_TARGET_UNIT_CASTER,
               apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=_MISC_ALL_SCHOOLS),
        Effect(type=EffectType.APPLY_AURA, base_points=44, implicit_target_a=_TARGET_UNIT_CASTER,
               apply_aura=AuraType.MOD_THREAT, misc_value=_MISC_ALL_SCHOOLS),
    ],
    spell_icon_id=_BLOOD_PRESENCE_ICON,
    notes=(
        'pulled from source/spells/npc.csv; dk-rework DK0a (shared doc "Blood Presence", brief known-hard 2): the tank '
        'aura. eff0 MOD_DAMAGE_PERCENT_DONE stored -6 (-5%), eff1 MOD_THREAT stored 44 (+45% [tune]); the stock +15% '
        'damage, the 4% damage heal (aura 118) and the -20% threat are gone. Attributes 0x29050010 (NO_AURA_CANCEL '
        'cleared: right-click cancels), AttributesEx 0x400 (CAST_WHEN_LEARNED cleared), AttributesEx2 0x11 kept '
        '(stance bar), Category 47 / 1 s, off the GCD, RuneCostID 0, SpellLevel 10 (trainer @10, was 55). The crit '
        'immunity is the 203000 child (linked type 2); the Tank Class Passive Threat 57340 link (U1) is linked below. '
        'custom_attr 0x06000000 makes eff0 / eff1 positive (aura 79 with a negative amount reads as a debuff, P0 2d). '
        'Bound to no script (spell_dk_presence unbound: it stays on 48263 / 48265, which are never cast again).'
    ),
    raw_overrides={
        'AttributesEx': _BLOOD_PRESENCE_ATTR1, 'AttributesEx2': 17, 'AttributesEx3': 1114112,
        'AttributesEx4': 2097152, 'AttributesEx6': 4096, 'CastingTimeIndex': 1, 'ProcChance': 101,
        'BaseLevel': 10, 'SpellLevel': 10, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 11114,
        'ActiveIconID': _BLOOD_PRESENCE_ICON, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'You are immune to critical strikes from melee and ranged attacks, and you generate '
                                 'more threat. Your damage dealt is reduced by 5%. Lasts until cancelled.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Immune to critical strikes from melee and ranged attacks. Threat generated '
                                     'increased. Damage dealt reduced.',
        'AuraDescription_Lang_Mask': 16712190,
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellClassMask_1': m.BLOOD_PRESENCE, 'PreventionType': 2,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'RuneCostID': 0,
    },
)
linked_spell(48266, blood_presence_crit_immunity_203000.id, 2,
             comment='Blood Presence - crit immunity child (DK0a)')
# U1: every stock tank aura links "Tank Class Passive Threat" 57340 (+43%), so Blood Presence's total threat equals
# stock Frost Presence's and starts at parity with Defensive Stance / Righteous Fury / Bear. The remover mirrors 48263's.
linked_spell(48266, 57340, 2, comment='Blood Presence - Tank Class Passive Threat (DK0a, U1)')
linked_spell(-48266, -57340, 0, comment='Blood Presence - remove Tank Class Passive Threat (DK0a, U1)')
custom_attr(blood_presence_48266, 0x06000000)   # SPELL_ATTR0_CU_POSITIVE_EFF0 | SPELL_ATTR0_CU_POSITIVE_EFF1
unbind_script(blood_presence_48266, 'spell_dk_presence')

# =====================================================================================================================
# Anti-Magic Zone aura 50461 (shared doc "Anti-Magic Zone"): the area aura the zone creature casts on its party
# =====================================================================================================================

# Stock 50461 kept as the area-party aura (type 35, aura 69 SCHOOL_ABSORB misc 126, radius 7 yd); the 74 base points (the
# old 75%) are gone: the 75% is the const AMZ_SPELL_REDUCTION_PCT and the absorb pool is ap_potency 500 (brief ruling 10 /
# U12), one shared pool per zone that spell_dk_anti_magic_zone_rework reads (flat = this effect's CalcValue, plus
# spell_bonus_data ap_bonus x the owner's attack power) while setting every member copy unlimited (-1). SpellLevel 52 is
# the learn level of the talent spell 51052 (trainer @52); pot_text() on this spell needs it.
anti_magic_zone_50461 = spell(
    id=50461,
    name='Anti-Magic Zone',
    school=School.SHADOW,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=35, ap_potency=500.0, potency_kind='absorb', implicit_target_a=_TARGET_UNIT_CASTER,
               apply_aura=AuraType.SCHOOL_ABSORB, misc_value=_MISC_NON_PHYSICAL_SCHOOLS, radius_yards=7.0),
    ],
    spell_icon_id=3144,
    notes=(
        'pulled from source/spells/npc.csv; dk-rework DK0a (shared doc "Anti-Magic Zone", brief ruling 10): the area aura '
        'the zone creature 28306 casts on party / raid members within 7 yd. eff0 keeps its shape (type 35 area-party, aura '
        '69 SCHOOL_ABSORB misc 126) with ap_potency 500 absorb (5297 flat + ap_bonus 2.1429 x attack power at level 60) '
        'instead of the old 74 base points; the 75% is the const AMZ_SPELL_REDUCTION_PCT, the pool is shared per zone '
        '(spell_dk_anti_magic_zone_rework, ConsumeZoneAbsorb) and each member copy is set to -1 (unlimited). SpellLevel 52 '
        '(was 55). Stock spell_dk_anti_magic_zone is unbound. 50462 (d0 b17, no caller) is left alone. The stock '
        'description "...absorbs ${$51052m1+2*$AP}" is replaced by the shared doc tooltip with {pot1}.'
    ),
    raw_overrides={
        'AttributesEx': 68, 'AttributesEx3': 1048576, 'AttributesEx4': 1, 'AttributesEx5': 1024, 'CastingTimeIndex': 1,
        'ProcChance': 101, 'SpellLevel': 52, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 11242,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188,
        'Description_Lang_enUS': 'Places a large, stationary Anti-Magic Zone that reduces spell damage taken by party or '
                                 'raid members inside it by 75%. The zone lasts 10 sec or until it absorbs {pot1} spell '
                                 'damage.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Spell damage taken reduced.',
        'AuraDescription_Lang_Mask': 16712190,
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellClassMask_2': m.AMZ,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'RuneCostID': 824,
    },
)
scripted_by(anti_magic_zone_50461, 'spell_dk_anti_magic_zone_rework')
unbind_script(anti_magic_zone_50461, 'spell_dk_anti_magic_zone')

# =====================================================================================================================
# Death's Caress (shared doc "Death's Caress"): new, level 12
# =====================================================================================================================

# Shadow, magic class, 30 yd. eff0 the target, eff1 every enemy within 10 yd of it (the target-dest + dest-area shape of
# Howling Blast's AoE effect); both ap_potency 50 direct, T 1500. spell_dk_deaths_caress trims eff1 to the const
# DEATHS_CARESS_EXTRA_TARGETS engaged enemies nearest the target (never the target itself, never a not-engaged unit) and
# casts Blood Plague 55078 on every unit either effect hits. 1 Unholy Rune + 10 RP: stock SpellRuneCost 221 (0,1,0,+10 RP).
# d2 b12 (m.DEATHS_CARESS) is the only family bit. Visual: Death Coil's missile / cast / impact (SpellVisual 10755, 0-verify
# item 19, brief ruling 8); icon 2730 Spell_DeathKnight_Butcher (used by no baseline DK spell).
deaths_caress_203001 = spell(
    id=203001,
    name="Death's Caress",
    school=School.SHADOW,
    attributes=_ATTR0_DO_NOT_SHEATH,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=50.0, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=50.0, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=_TARGET_DEST_TARGET_ENEMY, implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY,
               radius_yards=10.0),
    ],
    spell_icon_id=2730,
    notes=(
        'DK0a (shared doc "Death\'s Caress", brief ruling 8, known-hard 7): level 12, Shadow, magic class '
        '(DefenseType 1), PreventionType 1, 30 yd. eff0 SCHOOL_DAMAGE on the target, eff1 SCHOOL_DAMAGE on '
        'TARGET_DEST_TARGET_ENEMY / TARGET_UNIT_DEST_AREA_ENEMY 10 yd around it, both ap_potency 50 direct T 1500; '
        'spell_dk_deaths_caress picks the extra targets (const DEATHS_CARESS_EXTRA_TARGETS) and lands Blood Plague. '
        'RuneCostID 221 = (0 Blood, 1 Unholy, 0 Frost, +10 RP), GCD 1500 / category 133, no cooldown. Family bit d2 b12 '
        'only. SkillLineAbility 30720 on the Unholy line 772 (class 32, acquire 0: trainer-taught); trained_by is '
        'deathknight_trainers.py\'s.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1, 'DefenseType': 1, 'PreventionType': 1, 'FacingCasterFlags': 1, 'EquippedItemClass': -1,
        'SpellLevel': 12, 'RuneCostID': 221, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT,
        'SpellClassMask_3': m.DEATHS_CARESS,
        'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
        'SpellVisualID_1': 10755,
        'Description_Lang_enUS': 'Reach out with necrotic tendrils, dealing {pot1} Shadow damage to an enemy and up to 2 '
                                 'additional nearby enemies, and infecting each with Blood Plague.',
    },
)
scripted_by(deaths_caress_203001, 'spell_dk_deaths_caress')
skill_line_ability(id=30720, skill_line=772, spell_id=deaths_caress_203001.id, class_mask=32, acquire_method=0)

# =====================================================================================================================
# SpellLevel moves (shared doc learn-level table; the trainer rows are deathknight_trainers.py's)
# =====================================================================================================================

# Death Grip: taught by the trainer at 16 (stock: granted at creation, level 55). The NPC casters (33772 Faceless Horror,
# boss scripts) are unaffected by a spell level.
death_grip_49576 = spell(
    id=49576,
    name='Death Grip',
    school=School.NORMAL,
    mechanic=6,
    cast_time_ms=0,
    cooldown_ms=35000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=-1, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=2723,
    notes='pulled from source/spells/npc.csv; dk-rework DK0a: only SpellLevel / BaseLevel 55 -> 16 (shared doc learn-level '
          'table: Death Grip is taught by the trainer at 16). Everything else is the stock row.',
    raw_overrides={'AttributesEx': 524288, 'AttributesEx2': 1048640, 'AttributesEx6': 276824064, 'FacingCasterFlags': 1, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 16, 'SpellLevel': 16, 'EquippedItemClass': -1, 'SpellVisualID_1': 10906, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Harness the unholy energy that surrounds and binds all matter, drawing the target toward the death knight and forcing the enemy to attack the death knight for $49560d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellClassMask_1': 33554432, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'RuneCostID': 683},
)

# Death Gate: learned at 10 (stock 55), a port to Ebon Hold only.
death_gate_50977 = spell(
    id=50977,
    name='Death Gate',
    school=School.SHADOW,
    attributes=268435456,
    category=511,
    cast_time_ms=10000,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=60000,
    effects=[
        Effect(type=50, die_sides=0, implicit_target_a=47, misc_value=190942, radius_yards=3.0),
    ],
    spell_icon_id=1493,
    notes='pulled from source/spells/generic.csv; dk-rework DK0a: only SpellLevel / BaseLevel 55 -> 10 (learn-level table: '
          'Death Gate at 10). Everything else is the stock row.',
    raw_overrides={'AttributesEx': 131072, 'CastingTimeIndex': 7, 'InterruptFlags': 15, 'ProcChance': 101, 'BaseLevel': 10, 'SpellLevel': 10, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 11635, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Opens a gate which the Death Knight can use to return to Ebon Hold.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712172, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'DefenseType': 1, 'PreventionType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'RuneCostID': 852},
)

# Path of Frost: learned at 40 (stock 61). Stock-DBC-only before this change (no csv line, no live row).
path_of_frost_3714 = spell(
    id=3714,
    name='Path of Frost',
    school=School.NORMAL,
    attributes=151257104,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AREA_AURA_RAID, die_sides=0, implicit_target_a=1, apply_aura=104, radius_yards=50.0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=250),
        Effect(type=EffectType.DUMMY, base_points=60067, implicit_target_a=1),
    ],
    spell_icon_id=3147,
    notes='pulled from the stock Spell.dbc; dk-rework DK0a: only SpellLevel / BaseLevel 61 -> 40 (learn-level table: Path of '
          'Frost at 40). Everything else is the stock row.',
    raw_overrides={'AttributesEx': 131072, 'CastingTimeIndex': 1, 'AuraInterruptFlags': 3, 'ProcChance': 101, 'BaseLevel': 40, 'SpellLevel': 40, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 12486, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': "The Death Knight's freezing aura creates ice beneath $Ghis:her; feet, allowing $Ghim:her; and $Ghis:her; party or raid to walk on water for $d.  Works while mounted.  Any damage will cancel the effect.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Grants the ability to walk across water.', 'AuraDescription_Lang_Mask': 16712190, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'RuneCostID': 1204},
)


# =====================================================================================================================
# DK0b (shared doc "Haste and runes", "Runic Focus", "Obliterate", section 8): rune haste, Obliterate on a new id,
# Runic Focus with disease crits, the two diseases' DefenseType, Raise Dead's reagent
# =====================================================================================================================

_ATTR0_HIDDEN_PASSIVE = _ATTR0_PASSIVE | _ATTR0_DO_NOT_DISPLAY
_ATTR0_RUNIC_FOCUS = 0x150                          # stock: ABILITY 0x10 | PASSIVE 0x40 | DO_NOT_LOG 0x100
_AURA_MOD_POWER_REGEN_PERCENT = int(AuraType.MOD_POWER_REGEN_PERCENT)   # 110
_AURA_PERIODIC_DUMMY = int(AuraType.PERIODIC_DUMMY)                     # 226
_POWER_RUNE = 5                                     # EffectMiscValue of aura 110: POWER_RUNE
_RUNE_BLOOD, _RUNE_UNHOLY, _RUNE_FROST = 0, 1, 2    # EffectMiscValueB of aura 110 (RuneType, Player.h)
_ICON_IMPROVED_UNHOLY_PRESENCE = 2633               # stock 63622, the spike's pick for the rune haste pair
_ICON_ANNIHILATION = 2710                           # the icon Spell::EffectWeaponDmg's Obliterate branch keys on

# Script number (D8 tier 3): the ceiling of the rune-regeneration haste, in percent. 50 = a 5 s rune at 100% haste.
RUNE_HASTE_MAX_PCT = const(
    'RUNE_HASTE_MAX_PCT', 50,
    'Highest percent of rune-regeneration haste spell haste can grant (50 = a 10 s rune recharges in 5 s) [fixed].',
)

# ---- Rune haste (known-hard 4, P0 item 1 shape, passed as 203680 / 203681) ----
# 203052 carries three MOD_POWER_REGEN_PERCENT (110) effects on POWER_RUNE, one per base rune type (MiscValueB 0 Blood /
# 1 Unholy / 2 Frost; a Death Rune regenerates as its base type), stored -1 = live 0 (DieSides 1, stock 63622's values).
# spell_dk_rune_haste_sync (203053) keeps the live amount equal to the spell haste percent. Hidden passive, duration 0.
rune_haste_203052 = spell(
    id=203052,
    name='Rune Haste',
    school=School.NORMAL,
    attributes=_ATTR0_HIDDEN_PASSIVE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_POWER_REGEN_PERCENT, misc_value=_POWER_RUNE,
               base_points=-1, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_POWER_REGEN_PERCENT, misc_value=_POWER_RUNE,
               base_points=-1, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_POWER_REGEN_PERCENT, misc_value=_POWER_RUNE,
               base_points=-1, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_IMPROVED_UNHOLY_PRESENCE,
    notes=(
        'DK0b (shared doc "Haste and runes", known-hard 4, P0 203680 shape): hidden passive (0x40 | 0x80), three aura 110 '
        'effects on POWER_RUNE, MiscValueB 0 / 1 / 2 (Blood / Unholy / Frost), stored -1 = live 0. Granted to every DK by '
        'the type-2 link from Runic Focus 61455; spell_dk_rune_haste_sync (203053) ChangeAmount()s all three to the '
        'spell haste percent (capped at RUNE_HASTE_MAX_PCT).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'RuneCostID': 0,
        'EffectMiscValueB_1': _RUNE_BLOOD, 'EffectMiscValueB_2': _RUNE_UNHOLY, 'EffectMiscValueB_3': _RUNE_FROST,
        'Description_Lang_enUS': 'Rune regeneration follows your haste.',
        'AuraDescription_Lang_enUS': 'Rune regeneration speed increased.',
    },
)

# PERIODIC_DUMMY every 500 ms, never hasted (no haste-periodic attribute), no gcd. The script is the whole spell.
rune_haste_sync_203053 = spell(
    id=203053,
    name='Rune Haste Sync',
    school=School.NORMAL,
    attributes=_ATTR0_HIDDEN_PASSIVE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_PERIODIC_DUMMY, amplitude=500,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_IMPROVED_UNHOLY_PRESENCE,
    notes=(
        'DK0b (P0 203681 shape): hidden passive PERIODIC_DUMMY 500 ms. spell_dk_rune_haste_sync rescales every recharging '
        'rune by the haste change, then ChangeAmount()s 203052 to the spell haste percent '
        '(DeathKnight::SyncRuneHaste, clamp 0..RUNE_HASTE_MAX_PCT). Linked from Runic Focus 61455.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'RuneCostID': 0,
        'Description_Lang_enUS': 'Keeps rune regeneration in step with your haste.',
    },
)
scripted_by(rune_haste_sync_203053, 'spell_dk_rune_haste_sync')

# ---- Obliterate (shared doc "Obliterate", U2, U3, U9, known-hard 5) ----
# 1 Frost Rune + 15 RP (spell_rune_cost 2600; stock 587 is 1 Frost + 1 Unholy), 160% weapon damage + a 10 potency flat.
# Stock 49020's frame (Mograine 30838 keeps casting that one; its DSL row, SLA 17555 and rank chain stay). The percent
# effect is FIRST and the flat NORMALIZED_WEAPON_DMG second: EffectWeaponDmg multiplies a flat effect that sits before
# the percent effect by the percent (Frost Strike 49143 does the same). EFFECT_2 stays empty: SpellEffects.cpp reads
# Effects[EFFECT_2].CalcValue() as the per-disease bonus, which then reads 0. The core still *consumes* the diseases on
# d1 b17 unless the first icon-2710 DUMMY found rolls, so 203055 (live 100) rides along on every DK (U3, U5).
spell_rune_cost(2600, frost=1, runic_power=15, comment='Obliterate: 1 Frost Rune, +15 Runic Power')

obliterate_203054 = spell(
    id=203054,
    name='Obliterate',
    school=School.NORMAL,
    attributes=262160,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=5.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=160, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=10, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=2639,
    notes=(
        'DK0b (shared doc "Obliterate", U2 / U3 / U9): the baseline Obliterate on a new id, level 20, trained (SLA 30734, '
        'Frost line 771, class 32, acquire 0). Frame of stock 49020 (Attributes 262160, AttributesEx 134218240, '
        'AttributesEx3 1024 main hand, DefenseType 2, FacingCasterFlags 1, PreventionType 2, RangeIndex 2, main-hand '
        'weapon, icon 2639, visual 11613, GCD 133 / 1500). eff0 WEAPON_PERCENT_DAMAGE weapon_potency 160 FIRST, eff1 '
        'NORMALIZED_WEAPON_DMG sp_potency 10 direct T 1500; no EFFECT_2 (the core\'s per-disease value reads 0). '
        'RuneCostID 2600 = 1 Frost + 15 RP. d1 b17 (m.OBLITERATE) is the only family bit. Disease consumption is '
        'suppressed by the always-100 guard 203055.'
    ),
    raw_overrides={
        'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1,
        'DefenseType': 2, 'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'A brutal instant attack that deals $s1% weapon damage plus {pot2.avg}.',
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2,
        'RuneCostID': 2600, 'SpellClassMask_2': m.OBLITERATE, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT,
        'SpellLevel': 20, 'SpellVisualID_1': 11613, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
    },
)
skill_line_ability(id=30734, skill_line=771, spell_id=obliterate_203054.id, class_mask=32, acquire_method=0)

# The disease-consumption guard (U3): Spell::EffectWeaponDmg's Obliterate branch calls
# GetDummyAuraEffect(SPELLFAMILY_DEATHKNIGHT, 2710, EFFECT_0) and skips the consumption when roll_chance_i(amount) passes.
# The lookup is first-match, so the guard must be a family-15 aura with icon 2710 and a DUMMY (aura 4) on effect 0, stored
# 99 = live 100. No script. Granted by the type-2 link from Runic Focus; stock Annihilation 51468 / 72 / 73 (also icon
# 2710) are raised to 100 in deathknight_trigger_spells.py.
obliterate_disease_guard_203055 = spell(
    id=203055,
    name='Obliterate Disease Guard',
    school=School.NORMAL,
    attributes=_ATTR0_HIDDEN_PASSIVE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=99,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_ANNIHILATION,
    notes=(
        'DK0b (U3): hidden passive, eff0 APPLY_AURA DUMMY stored 99 = live 100, SpellIconID 2710, family 15, no family '
        'bits. Obliterate 203054 reads it as "Annihilation" and never consumes diseases. Linked from Runic Focus 61455.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'RuneCostID': 0,
        'Description_Lang_enUS': 'Your Obliterate never consumes diseases.',
    },
)

# ---- Runic Focus 61455 (shared doc "Runic Focus", U5, U6, known-hard 6) ----
# Stock: aura 108 ADD_PCT_MODIFIER misc 15 (SPELLMOD_CRIT_DAMAGE_BONUS) +100% on the DK spell mask below. DK0b
# adds the reader bits of the two diseases (d1 b25, b26) and Boiling Blight's burst / Death's Caress (d2 b11, b12), so
# the diseases crit for 150% + 100% = 200% (DefenseType 1 on both, below). Passive, known at creation (SLA 20646 acquire
# 2): the type-2 links add the three hidden DK0b passives to every DK (Blood Presence's child precedent).
_RUNIC_FOCUS_STOCK_MASK = (0x80040202, 0x10022, 0x9)
_RUNIC_FOCUS_MASK = tuple(a | b for a, b in zip(_RUNIC_FOCUS_STOCK_MASK, m.RUNIC_FOCUS_READ_ADD))

runic_focus_61455 = spell(
    id=61455,
    name='Runic Focus',
    school=School.NORMAL,
    attributes=_ATTR0_RUNIC_FOCUS,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=_TARGET_UNIT_CASTER, apply_aura=108,
               misc_value=15),
    ],
    spell_icon_id=2432,
    notes=(
        'pulled from existing data; dk-rework DK0b (shared doc "Runic Focus", U5 / U6): reader mask = stock (d0 0x80040202, '
        'd1 0x10022, d2 0x9) | _masks.RUNIC_FOCUS_READ_ADD (d1 b25 Blood Plague, d1 b26 Frost Fever, d2 b11 Boiling Blight '
        'burst, d2 b12 Death\'s Caress); the new tooltip. The type-2 spell_linked_spell rows below add Rune Haste 203052, '
        'Rune Haste Sync 203053 and the Obliterate guard 203055 to every Death Knight (SLA 20646, acquire 2, is '
        'untouched: every DK has the skill line 771 at creation).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1,
        'EffectSpellClassMaskA_1': _RUNIC_FOCUS_MASK[0], 'EffectSpellClassMaskA_2': _RUNIC_FOCUS_MASK[1],
        'EffectSpellClassMaskA_3': _RUNIC_FOCUS_MASK[2],
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Passive', 'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Unlike most casters, a Death Knight's spells and diseases deal double damage on critical "
                                 "strikes. Your diseases can critically strike.",
        'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188,
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0,
    },
)
linked_spell(runic_focus_61455.id, rune_haste_203052.id, type=2,
             comment='Runic Focus -> Rune Haste (every DK, DK0b U5)')
linked_spell(runic_focus_61455.id, rune_haste_sync_203053.id, type=2,
             comment='Runic Focus -> Rune Haste Sync (every DK, DK0b U5)')
linked_spell(runic_focus_61455.id, obliterate_disease_guard_203055.id, type=2,
             comment='Runic Focus -> Obliterate disease guard (every DK, DK0b U3 / U5)')

# ---- The two diseases (U6): DefenseType 1 (magic) so they crit at spell crit chance for 200% ----
# Stock Blood Plague was DefenseType 2 (melee crit chance, 200% base + Runic Focus's +100% = 300%) and Frost Fever 0 (never
# crits). Everything else is the stock row; live spell_custom_attr 512 (IGNORE_BINARY) on 55095 lives in
# deathknight_trigger_spells.py. Disease masks: d1 b25 / b26 (m.BLOOD_PLAGUE_DISEASE / FROST_FEVER_DISEASE), d1 b11 (stock),
# d2 b1 (stock).
blood_plague_55078 = spell(
    id=55078,
    name='Blood Plague',
    school=School.SHADOW,
    dispel=3,
    mechanic=22,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, points_per_level=0.39399999380111694, mechanic=22,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000,
               misc_value=_MISC_ALL_SCHOOLS),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3141,
    notes=(
        'pulled from existing data; dk-rework DK0b (U6): DefenseType 2 -> 1 (magic class: spell crit chance, 150% base + '
        'Runic Focus +100% = 200%). Everything else is the stock row. Stock spell_bonus_data ap_dot_bonus and the live '
        'custom_attr are untouched.'
    ),
    raw_overrides={
        'AttributesEx2': 4, 'AttributesEx3': 262144, 'AttributesEx4': 8388608, 'CastingTimeIndex': 1, 'BaseLevel': 1,
        'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'A disease dealing Shadow damage every 3 sec for $d.', 'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Deals Shadow damage over $d.', 'AuraDescription_Lang_Mask': 16712190,
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT,
        'SpellClassMask_2': m.BLOOD_PLAGUE_DISEASE | 0x800,     # stock 0x2000800: d1 b25 + b11
        'SpellClassMask_3': 0x2,                                # stock d2 b1
        'DefenseType': 1,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'RuneCostID': 1143,
    },
)

frost_fever_55095 = spell(
    id=55095,
    name='Frost Fever',
    school=School.FROST,
    dispel=3,
    mechanic=22,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.RUNE,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, points_per_level=0.3199999928474426, mechanic=22,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000,
               misc_value=_MISC_ALL_SCHOOLS),
        Effect(type=EffectType.APPLY_AURA, base_points=-15, mechanic=8, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               apply_aura=138),
        Effect(type=EffectType.APPLY_AURA, base_points=-15, mechanic=8, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               apply_aura=140),
    ],
    spell_icon_id=3142,
    notes=(
        'pulled from existing data; dk-rework DK0b (U6): DefenseType 0 -> 1 (magic class: Frost Fever can now crit, spell '
        'crit chance, 150% base + Runic Focus +100% = 200%). Everything else is the stock row; live spell_custom_attr 512 '
        '(IGNORE_BINARY) stays, declared in deathknight_trigger_spells.py.'
    ),
    raw_overrides={
        'AttributesEx3': 262144, 'AttributesEx4': 9437184, 'CastingTimeIndex': 1, 'ProcChance': 101,
        'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190,
        'Description_Lang_enUS': "A disease dealing Frost damage every 3 sec and reducing the target's melee and ranged "
                                 "attack speed by $55095s2% for $55095d.",
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Deals Frost damage over $d.\nReduces melee and ranged attack speed.',
        'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT,
        'SpellClassMask_2': m.FROST_FEVER_DISEASE | 0x800,      # stock 0x4000800: d1 b26 + b11
        'SpellClassMask_3': 0x2,                                # stock d2 b1
        'DefenseType': 1,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'RuneCostID': 2295,
    },
)

# ---- Raise Dead's reagent row (U7): Corpse Dust is gone ----
# 48289 is the hidden self spell Raise Dead (46584) casts with the Corpse Dust reagent (item 37201). The stock row's
# Reagent_1 / ReagentCount_1 are simply not carried: the row is built blank, so absent means 0, server (spell_dbc) and
# client (Spell.dbc) alike. The item stays on its npc_vendor rows and in bags.
raise_dead_48289 = spell(
    id=48289,
    name='Raise Dead',
    school=School.SHADOW,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=61,
    notes=(
        'pulled from existing data; dk-rework DK0b (U7, shared doc section 8): Reagent_1 37201 / ReagentCount_1 1 cleared '
        '(Corpse Dust removed from Raise Dead). Everything else is the stock row.'
    ),
    raw_overrides={
        'AttributesEx5': 2, 'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'RangeIndex': 1,
        'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172,
        'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188,
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellClassMask_1': 4096,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
    },
)
