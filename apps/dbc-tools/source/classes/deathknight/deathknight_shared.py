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
    const, custom_attr, linked_spell, scripted_by, skill_line_ability, spell, unbind_script,
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
