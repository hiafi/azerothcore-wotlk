"""
Paladin - spells that are never directly cast - proc/periodic-tick effects, trigger_spell targets, hidden talent-rank buffs, etc..

Split from a single source/classes/paladin.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .paladin_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import leave_spell_group, linked_spell, pot_text, procs_on, product, remove_spell_proc, scripted_by, spell, spell_group, talent_mult, tooltip_vars, trained_by, unbind_script, untrain
from . import _masks as m
from .paladin_holy_spells import holy_heal_tooltip


def _mask(effect_index: int, mask: tuple) -> dict:
    """The `EffectSpellClassMask{A,B,C}_{1,2,3}` raw_overrides of one effect: the LETTER is the effect (1-based `effect_index`
    -> A/B/C), the NUMBER the dword of the (d0, d1, d2) `mask` (dbcfmt.py:127-139, dbc-tools.md gotcha). Paladin Holy rework
    (HOLY.md 3 item 10): every mask edit goes through here so a stale hand-typed key can't override the constant."""
    letter = 'ABC'[effect_index - 1]
    return {f'EffectSpellClassMask{letter}_{dword + 1}': value for dword, value in enumerate(mask) if value}


# Ret talents scaling Ret-owned spells on their tooltips (RETRIBUTION §5.3, P9 tooltip_vars). SpellMods never move a
# tooltip, so each entry reads the always-on percent talents from their rank spells (bare ids: the rank spells are
# declared further down this file, some of them after the spells that use these entries).
# 1120: Blade of Justice. Strength of Faith 201446-8 e1, Smite Evil 31866-8 e2 (aura 79), Blade of Wrath 201457-9 e1.
ret_blade_of_justice_tooltip = tooltip_vars(
    1120, "Ret talents on Blade of Justice",
    sof=talent_mult([201446, 201447, 201448], effect=1),
    smite=talent_mult([31866, 31867, 31868], effect=2),
    wrath=talent_mult([201457, 201458, 201459], effect=1),
    mult=product("sof", "smite", "wrath"),
)

# 1121: Execution Sentence 201410 (A1's castable), burst 201411, splash 201412. mult = direct strikes (SPELLMOD_DAMAGE),
# dot = the DoT (SPELLMOD_DOT, reads Sanctity e2 and The Art of War e3).
ret_execution_sentence_tooltip = tooltip_vars(
    1121, "Ret talents on Execution Sentence",
    sof=talent_mult([201446, 201447, 201448], effect=1),
    smite=talent_mult([31866, 31867, 31868], effect=2),
    sanc=talent_mult([32043, 35396, 35397], effect=1),
    aow=talent_mult([53486, 53488, 201472], effect=1),
    sancdot=talent_mult([32043, 35396, 35397], effect=2),
    aowdot=talent_mult([53486, 53488, 201472], effect=3),
    mult=product("sof", "smite", "sanc", "aow"),
    dot=product("sof", "smite", "sancdot", "aowdot"),
)

# 1122: Wake of Ashes 201413 (A1's castable). Purify the Unclean 201451-3 e1, Sanctity of Battle e1.
ret_wake_of_ashes_tooltip = tooltip_vars(
    1122, "Ret talents on Wake of Ashes",
    sof=talent_mult([201446, 201447, 201448], effect=1),
    smite=talent_mult([31866, 31867, 31868], effect=2),
    purify=talent_mult([201451, 201452, 201453], effect=1),
    sanc=talent_mult([32043, 35396, 35397], effect=1),
    mult=product("sof", "smite", "purify", "sanc"),
)


righteousness_echo_201401 = spell(
    id=201401, name='Righteousness Echo', school=School.HOLY,
    attributes=2359296,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=60.0, implicit_target_a=6),
    ],
    spell_icon_id=90210,
    notes='paladin-rework S1 RETRIBUTION §4.2: Blade of Justice echo = the seal ability-form passive (B1.4) at x3 weapon potency; SUPPRESS_CASTER_PROCS so it never procs a seal passive or a talent. Righteousness: 60 weapon.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Strikes the target with the power of your seal.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'SpellClassMask_3': m.SEAL_PASSIVE, 'DefenseType': 2, 'AttributesEx3': 327680, 'AttributesEx2': 4, 'SpellLevel': 30},
)


command_echo_201402 = spell(
    id=201402, name='Command Echo', school=School.HOLY | School.FIRE,
    attributes=2359296,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6, chain_targets=3),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=30.0, implicit_target_a=6, chain_targets=3),
    ],
    spell_icon_id=90210,
    notes='paladin-rework S1 RETRIBUTION §4.2: Blade of Justice echo = the seal ability-form passive (B1.4) at x3 weapon potency; SUPPRESS_CASTER_PROCS so it never procs a seal passive or a talent. Command: 30 weapon, target + 2 chained enemies; P | C.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Strikes the target with the power of your seal.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'SpellClassMask_3': m.SEAL_PASSIVE | m.SEAL_PASSIVE_COMMAND, 'DefenseType': 2, 'AttributesEx3': 327680, 'AttributesEx2': 4, 'SpellLevel': 30},
)


vengeance_echo_201403 = spell(
    id=201403, name='Vengeance Echo', school=School.HOLY | School.SHADOW,
    attributes=2359296,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=30.0, implicit_target_a=6),
    ],
    spell_icon_id=90210,
    notes='paladin-rework S1 RETRIBUTION §4.2: Blade of Justice echo = the seal ability-form passive (B1.4) at x3 weapon potency; SUPPRESS_CASTER_PROCS so it never procs a seal passive or a talent. Vengeance: the script then applies Echoing Vengeance 201407.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Strikes the target with the power of your seal.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'SpellClassMask_3': m.SEAL_PASSIVE, 'DefenseType': 2, 'AttributesEx3': 327680, 'AttributesEx2': 4, 'SpellLevel': 30},
)


justice_echo_201404 = spell(
    id=201404, name='Justice Echo', school=School.HOLY | School.FROST,
    attributes=2359296,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=30.0, implicit_target_a=6),
    ],
    spell_icon_id=90210,
    notes='paladin-rework S1 RETRIBUTION §4.2: Blade of Justice echo = the seal ability-form passive (B1.4) at x3 weapon potency; SUPPRESS_CASTER_PROCS so it never procs a seal passive or a talent. Justice: the script then casts the 0.5 s stun 201096 on non-player-controlled targets without Justice Recovery 201106.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Strikes the target with the power of your seal.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'SpellClassMask_3': m.SEAL_PASSIVE, 'DefenseType': 2, 'AttributesEx3': 327680, 'AttributesEx2': 4, 'SpellLevel': 30},
)


light_echo_201405 = spell(
    id=201405, name='Light Echo', school=School.HOLY,
    attributes=2359296,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=15.0, implicit_target_a=6),
    ],
    spell_icon_id=90210,
    notes='paladin-rework S1 RETRIBUTION §4.2: Blade of Justice echo = the seal ability-form passive (B1.4) at x3 weapon potency; SUPPRESS_CASTER_PROCS so it never procs a seal passive or a talent. Light: the script then casts Echoing Light 201408.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Strikes the target with the power of your seal.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'SpellClassMask_3': m.SEAL_PASSIVE, 'DefenseType': 2, 'AttributesEx3': 327680, 'AttributesEx2': 4, 'SpellLevel': 30},
)


wisdom_echo_201406 = spell(
    id=201406, name='Wisdom Echo', school=School.HOLY | School.ARCANE,
    attributes=2359296,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6),
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=15.0, implicit_target_a=6),
    ],
    spell_icon_id=90210,
    notes='paladin-rework S1 RETRIBUTION §4.2: Blade of Justice echo = the seal ability-form passive (B1.4) at x3 weapon potency; SUPPRESS_CASTER_PROCS so it never procs a seal passive or a talent. Wisdom: the script then casts Echoing Wisdom 201409 and energizes 60% of base mana.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Strikes the target with the power of your seal.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'SpellClassMask_3': m.SEAL_PASSIVE, 'DefenseType': 2, 'AttributesEx3': 327680, 'AttributesEx2': 4, 'SpellLevel': 30},
)


echoing_vengeance_201407 = spell(
    id=201407, name='Echoing Vengeance', school=School.HOLY | School.SHADOW,
    dispel=DispelType.MAGIC,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=5.4, ap_potency=5.4, potency_kind='periodic', implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000),
    ],
    spell_icon_id=90210,
    notes='paladin-rework S1 RETRIBUTION §4.2: DoT of the Vengeance echo, 5 s, 36 total; icon 90210 (never 2292) and no d1 bits (JoV hardcode); a new application from the same caster replaces the old one.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Burns the target with twilight fire.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Taking {pot1} Twilight damage every $t1 sec.", 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'SpellClassMask_3': m.SEAL_PASSIVE, 'DefenseType': 1, 'AttributesEx2': 4, 'SpellLevel': 30},
)


echoing_light_201408 = spell(
    id=201408, name='Echoing Light', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.HEAL, implicit_target_a=21, potency_excluded='percent of base health (R "Values outside potency"); BP from spell_pal_blade_of_justice'),
    ],
    spell_icon_id=90210,
    notes="paladin-rework S1 RETRIBUTION §4.2: heal for 60% of the paladin's base health (script SPELLVALUE_BASE_POINT0) on self + the 3 most injured allies; no spell_bonus_data row, EffectBonusMultiplier 0.",
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Heals the target for 60% of the Paladin's base health.", 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'DefenseType': 1, 'AttributesEx3': 65536, 'AttributesEx2': 4, 'EffectBonusMultiplier_1': 0.0, 'SpellLevel': 30},
)


echoing_wisdom_201409 = spell(
    id=201409, name='Echoing Wisdom', school=School.HOLY | School.ARCANE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=6, potency_excluded='percent of max mana (R); BP from spell_pal_blade_of_justice'),
    ],
    spell_icon_id=90210,
    notes="paladin-rework S1 RETRIBUTION §4.2: Divine damage for 1.5% of the paladin's max mana (script SPELLVALUE_BASE_POINT0); no spell_bonus_data row, EffectBonusMultiplier 0.",
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Deals damage equal to 1.5% of the Paladin's maximum mana.", 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'DefenseType': 1, 'AttributesEx3': 65536, 'AttributesEx2': 4, 'EffectBonusMultiplier_1': 0.0, 'SpellLevel': 30},
)


vindication_strike_201420 = spell(
    id=201420, name='Vindication', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=20.0, ap_potency=20.0, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=1798,
    notes='paladin-rework S1 RETRIBUTION §4.5: the Vindication proc hit (rank eff0 triggers it), no family bits. Never use 26017/67 (C12 key).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Deals {pot1} Holy damage.", 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'DefenseType': 1, 'SpellLevel': 25},
)


vindication_buff_201421 = spell(
    id=201421, name='Vindication', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 20),
    ],
    spell_icon_id=1798,
    notes='paladin-rework S1 RETRIBUTION §4.5: +3% Mastery (aura 306, misc 1<<20) for 10 s, triggered by the rank eff1 (refresh).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Mastery.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Mastery increased by $s1%.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101},
)


benediction_buff_201422 = spell(
    id=201422, name='Benediction', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=0),
    ],
    spell_icon_id=101,
    notes='paladin-rework S1 RETRIBUTION §4.6: +X% Strength for 20 s; the amount is set by spell_pal_benediction from the rank eff1 (SPELLVALUE_BASE_POINT0).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Strength.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Strength increased by $s1%.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101},
)


eye_for_an_eye_buff_201423 = spell(
    id=201423, name='Eye for an Eye', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=0),
    ],
    spell_icon_id=1820,
    notes='paladin-rework S1 RETRIBUTION §4.6: capstone buff, -20% damage taken and +10% Strength for 10 s.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces damage taken and increases your Strength.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced by 20%. Strength increased by 10%.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101},
)


sanctity_of_battle_empower_201424 = spell(
    id=201424, name='Sanctity of Battle', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.ABILITY_IGNORE_AURASTATE),
        Effect(type=EffectType.APPLY_AURA, base_points=34, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
    ],
    spell_icon_id=3106,
    notes='paladin-rework S1 RETRIBUTION §4.6: 15 s empower, 1 charge; Hammer of Wrath at any health +35% (eff0/eff1 scoped to HoW), Flash of Light guaranteed crit (eff2); the charge is spent by Player::RemoveSpellMods when HoW or Flash of Light uses a mod (ProcTypeMask 0, no spell_proc row, warlock 200991 precedent). Divine Storm +50% and its consumption are scripted (spell_pal_divine_storm_ret).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Hammer of Wrath, Flash of Light or Divine Storm is empowered.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Hammer of Wrath can be used at any health and deals 35% more damage, your next Flash of Light is a critical strike, or your next Divine Storm deals 50% more damage.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'ProcCharges': 1, 'ProcTypeMask': 0, 'EffectSpellClassMaskA_2': m.HAMMER_OF_WRATH, 'EffectSpellClassMaskB_2': m.HAMMER_OF_WRATH, 'EffectSpellClassMaskC_1': m.FLASH_OF_LIGHT},
)


improved_judgements_marker_201425 = spell(
    id=201425, name='Improved Judgements', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=205,
    notes='paladin-rework S1 RETRIBUTION §4.6: marker, your next stack grant gives +1 (consumed by Paladin::ModifyStackGainRet); 20 s is a starting guess.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next stack-building ability grants an additional stack.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next ability that grants seal stacks grants 1 additional stack.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'ProcTypeMask': 0},
)


swift_retribution_buff_201426 = spell(
    id=201426, name='Swift Retribution', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=3028,
    notes='paladin-rework S1 RETRIBUTION §4.6: self haste per stack (rank 1); CumulativeAura 3, amounts scale with stacks.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your haste.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased by $s1%.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'CumulativeAura': 3},
)


swift_retribution_buff_201427 = spell(
    id=201427, name='Swift Retribution', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
    ],
    spell_icon_id=3028,
    notes='paladin-rework S1 RETRIBUTION §4.6: self haste per stack (rank 2); CumulativeAura 3, amounts scale with stacks.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your haste.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased by $s1%.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'CumulativeAura': 3},
)


swift_retribution_buff_201428 = spell(
    id=201428, name='Swift Retribution', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=3028,
    notes='paladin-rework S1 RETRIBUTION §4.6: self haste per stack (rank 3); CumulativeAura 3, amounts scale with stacks. Rank 3 adds +5% Exorcism per stack (Holy Fire/Smite dropped, §0.1 item 8).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your haste.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Haste increased by $s1%. Exorcism damage increased by $s2%.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'CumulativeAura': 3, 'EffectSpellClassMaskB_2': m.EXORCISM},
)


blade_of_wrath_mastery_201429 = spell(
    id=201429, name='Blade of Wrath', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=20, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 20, radius_yards=30.0),
    ],
    spell_icon_id=90214,
    notes='paladin-rework S1 RETRIBUTION §4.6: party +2% Mastery for 10 s within 30 yd; proc-triggered by the rank 3 passive 201459 (CAST phase row).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the Mastery of your party members.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Mastery increased by $s1%.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101},
)


crusaders_aegis_shield_201430 = spell(
    id=201430, name="Crusader's Aegis", school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=300.0, potency_kind='absorb', implicit_target_a=20, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=127, radius_yards=30.0),
    ],
    spell_icon_id=2820,
    notes='paladin-rework S1 RETRIBUTION §4.6: party absorb (300 healing potency) for 10 s within 30 yd, cast when Avenging Wrath is cast (201462 CAST row). SCHOOL_ABSORB gets no engine SP bonus: spell_pal_crusaders_aegis_absorb adds Paladin::CalculateAbsorbBonus.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Absorbs {pot1} damage.", 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Absorbs {pot1} damage.", 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'SpellLevel': 50},
)


crusade_ramp_201431 = spell(
    id=201431, name='Crusade', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=2171,
    notes='paladin-rework S1 RETRIBUTION §4.6: ramp, +2% damage per seal stack gained while Avenging Wrath is up (cap 15%); the amount is set by script; removed with Avenging Wrath through linked_spell(-31884, -201431).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your damage.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage increased by $s1%.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101},
)


pursuit_of_justice_speed_201432 = spell(
    id=201432, name='Pursuit of Justice', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_SPEED_NOT_STACK),
    ],
    spell_icon_id=1797,
    notes='paladin-rework S1 RETRIBUTION §4.6: +10/20% movement speed while Seal of Justice is active (amount from the rank eff1, set by script); removed with the seal.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your movement speed.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed increased by $s1%.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101},
)


pursuit_of_justice_freedom_201433 = spell(
    id=201433, name='Pursuit of Justice', school=School.HOLY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=21, apply_aura=AuraType.MOD_INCREASE_SPEED),
    ],
    spell_icon_id=1797,
    notes='paladin-rework S1 RETRIBUTION §4.6 (fixed in review-2): +30% speed on the Hand of Freedom target (self or ally), 6 s; target A 21 and range 50000.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your movement speed.', 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed increased by $s1%.', 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101},
)


sheath_of_light_capstone_201434 = spell(
    id=201434, name='Sheath of Light', school=School.HOLY,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3030,
    notes='paladin-rework S1 RETRIBUTION §4.6/§4.11: hidden passive linked to Sheath of Light rank 3 (53503); carries the Flash-of-Light-on-self mana proc (the chain -53501 already has a stock row, so a positive row on a rank would be dropped).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Flash of Light on yourself restores mana.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101},
)


vindication_67 = spell(
    id=67,
    name='Vindication',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-24, points_per_level=-9.375000190734863, implicit_target_a=6, apply_aura=AuraType.MOD_ATTACK_POWER, misc_value=1),
    ],
    spell_icon_id=1822,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 136, 'AttributesEx2': 4, 'AttributesEx3': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack power reduced by $s1.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Gives the Paladin's damaging melee attacks a chance to reduce the target's attack poewr by $s1 for $d.", 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 16384, 'SpellClassSet': 10, 'SpellLevel': 20, 'SpellVisualID_1': 6839},
)


devotion_aura_465 = spell(
    id=465,
    name='Devotion Aura',
    school=School.HOLY,
    attributes=151322640,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=54, points_per_level=14.556962025316455, implicit_target_a=1, apply_aura=22, misc_value=1, radius_yards=40.0),
    ],
    spell_icon_id=291,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80 | paladin-rework S1 SHARED Part C C1.2: button (60 s RecoveryTime, Category 1300 / 15 s, IS_ABILITY flat GCD).',
    category=1300,
    raw_overrides={'ActiveIconID': 122, 'AttributesEx2': 17, 'AttributesEx3': 1114112, 'AttributesEx4': 3145728, 'AttributesEx7': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases armor by $s1.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives $s1 additional armor to party and raid members within $a1 yards. Activating it also reduces damage taken by party and raid members within $a1 yards by $201161s2% for $201161d. Players may only have one Aura on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 64, 'SpellClassMask_3': 32, 'SpellClassSet': 10, 'SpellLevel': 1, 'SpellVisualID_1': 160, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


sense_undead_5502 = spell(
    id=5502,
    name='Sense Undead',
    school=School.HOLY,
    attributes=151257104,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=44, misc_value=6),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=168, misc_value=32),
    ],
    spell_icon_id=308,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268566560, 'AttributesEx3': 1048576, 'AttributesEx6': 4096, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Detecting Undead.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Shows the location of all nearby undead on the minimap until cancelled.   Only one form of tracking can be active at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 134217728, 'SpellClassSet': 10, 'SpellLevel': 20, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


retribution_aura_7294 = spell(
    id=7294,
    name='Retribution Aura',
    school=School.HOLY,
    attributes=151322640,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=9, points_per_level=1.59375, implicit_target_a=1, apply_aura=15, radius_yards=40.0),
        Effect(type=65, base_points=-1, implicit_target_a=1, apply_aura=79, misc_value=127, radius_yards=40.0),
        Effect(type=65, base_points=-1, implicit_target_a=1, apply_aura=193, misc_value=127, radius_yards=40.0),
    ],
    spell_icon_id=555,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 16); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80 | paladin-rework S1 SHARED Part C C1.2: button (60 s RecoveryTime, Category 1300 / 15 s, IS_ABILITY flat GCD).',
    category=1300,
    raw_overrides={'ActiveIconID': 122, 'AttributesEx2': 17, 'AttributesEx3': 1114112, 'AttributesEx4': 3145728, 'AttributesEx6': 1073741824, 'AttributesEx7': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Does $s1 Holy damage to anyone who strikes you.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Causes $s1 Holy damage to any enemy that strikes a party or raid member within $a1 yards. Activating it also increases the Mastery of party and raid members within $a1 yards by $201160s1% for $201160d. Players may only have one Aura on them per Paladin at any one time.', 'EffectBonusMultiplier_1': 0.032999999821186066, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 8, 'SpellClassMask_3': 32, 'SpellClassSet': 10, 'SpellLevel': 16, 'SpellVisualID_1': 682, 'StanceBarOrder': 1, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


concentration_aura_19746 = spell(
    id=19746,
    name='Concentration Aura',
    school=School.HOLY,
    attributes=151322640,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=99, implicit_target_a=1, apply_aura=85, misc_value=0, radius_yards=40.0),
    ],
    spell_icon_id=1487,
    notes='pulled from existing data | paladin-rework S1 SHARED Part C C1.2/C1.3: button; eff0 aura 149 (pushback) -> 85 MOD_POWER_REGEN misc 0 bp 99 (live 100 = 1.00% in hundredths, scaled to mp5 by spell_pal_concentration_aura); effect index 0 keeps d0 b17.',
    category=1300,
    raw_overrides={'ActiveIconID': 122, 'AttributesEx2': 17, 'AttributesEx3': 1114112, 'AttributesEx4': 2097152, 'AttributesEx7': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Mana regeneration increased.', 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Restores $/100;s1% of the Paladin's base mana every 5 sec to party and raid members within $a1 yards. Activating it also restores $/100;201164s1% of their maximum mana every 5 sec for $201164d. Players may only have one Aura on them per Paladin at any one time.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 131072, 'SpellClassMask_3': 32, 'SpellClassSet': 10, 'SpellLevel': 22, 'SpellVisualID_1': 5139, 'StanceBarOrder': 2, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


resistance_aura_19876 = spell(
    id=19876,
    name='Resistance Aura',
    school=School.HOLY,
    attributes=151322640,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=29, points_per_level=1.9230769230769231, implicit_target_a=1, apply_aura=143, misc_value=52, radius_yards=40.0),
    ],
    spell_icon_id=140,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80 | paladin-rework S1 SHARED Part C C1.2/C1.3: button; Shadow Resistance Aura -> Resistance Aura (misc 32 -> 52, all three schools); d0 b26 and d1 b4 reclaimed (stripped; d2 0x20 kept).',
    category=1300,
    raw_overrides={'ActiveIconID': 122, 'AttributesEx2': 17, 'AttributesEx3': 1114112, 'AttributesEx4': 3145728, 'AttributesEx7': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Shadow, Frost and Fire resistance by $s1.', 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives $s1 additional Shadow, Frost and Fire resistance to all party and raid members within $a1 yards. Activating it also gives them an absorb of magic damage equal to $201162s1% of their maximum health for $201162d. Players may only have one Aura on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 32, 'SpellClassSet': 10, 'SpellLevel': 28, 'SpellVisualID_1': 321, 'StanceBarOrder': 3, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frost_resistance_aura_19888 = spell(
    id=19888,
    name='Frost Resistance Aura',
    school=School.HOLY,
    attributes=151322624,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=29, points_per_level=2.0833333333333335, implicit_target_a=1, apply_aura=143, misc_value=16, radius_yards=40.0),
    ],
    spell_icon_id=133,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx2': 17, 'AttributesEx3': 1114112, 'AttributesEx4': 3145728, 'AttributesEx7': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Frost resistance by $s1.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives $s1 additional Frost resistance to all party and raid members within $a1 yards.  Players may only have one Aura on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 67108864, 'SpellClassMask_2': 16, 'SpellClassMask_3': 32, 'SpellClassSet': 10, 'SpellLevel': 32, 'SpellVisualID_1': 321, 'StanceBarOrder': 4, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fire_resistance_aura_19891 = spell(
    id=19891,
    name='Fire Resistance Aura',
    school=School.HOLY,
    attributes=151322624,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=29, points_per_level=2.272727272727273, implicit_target_a=1, apply_aura=143, misc_value=4, radius_yards=40.0),
    ],
    spell_icon_id=33,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 36); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 5 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx2': 17, 'AttributesEx3': 1114112, 'AttributesEx4': 3145728, 'AttributesEx7': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases Fire resistance by $s1.', 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Gives $s1 additional Fire resistance to all party and raid members within $a1 yards.  Players may only have one Aura on them per Paladin at any one time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 67108864, 'SpellClassMask_2': 16, 'SpellClassMask_3': 32, 'SpellClassSet': 10, 'SpellLevel': 36, 'SpellVisualID_1': 321, 'StanceBarOrder': 5, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


improved_blessing_of_salvation_20194 = spell(
    id=20194,
    name='Improved Blessing of Salvation',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=299999, points_per_level=5000.0, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=305,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the duration of your Blessing of Salvation by $/60000;s1 min.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 256, 'EffectSpellClassMaskA_1': 256, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


lay_on_hands_20233 = spell(
    id=20233,
    name='Lay on Hands',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, points_per_level=-0.16666666666666666, implicit_target_a=21, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
    ],
    spell_icon_id=79,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Reduces physical damage taken by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants the target of your Lay on Hands spell $s1% reduced physical damage taken for $d.  In addition, the cooldown for your Lay on Hands spell is reduced.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 2147500032, 'SpellClassSet': 10},
)


improved_flash_of_light_20249 = spell(
    id=20249,
    name='Improved Flash of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, points_per_level=0.06666666666666667, implicit_target_a=1, apply_aura=107, misc_value=7),
    ],
    spell_icon_id=242,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Flash of Light spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1073741824, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


heart_of_the_crusader_21183 = spell(
    id=21183,
    name='Heart of the Crusader',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=197),
    ],
    spell_icon_id=237,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80 | paladin-rework S1 RETRIBUTION §4.8: debuff duration 20 s -> 15 s. Rank 1 points_per_level 0.0339 removed: it gave +2 by level 60 (3%), not the promised 1%.',
    raw_overrides={'AttributesEx2': 268435460, 'AttributesEx3': 262656, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases chance of critical strikes against the target by $s1%.', 'BaseLevel': 1, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'In addition to the normal effect, your Judgement and Deliverance will also increase the critical strike chance of all attacks made against that target by an additional $20335s1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'SpellClassMask_1': 536870912, 'SpellClassSet': 10, 'SpellLevel': 1},
)


righteous_fury_25780 = spell(
    id=25780,
    name='Righteous Fury',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=79, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=127),
    ],
    spell_icon_id=301,
    notes='pulled from existing data | paladin-rework S1 SHARED Part C C3: new eff2 MOD_THREAT misc 127 bp 14 (+15% all schools) folded in from Tenacity.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Holy threat increased by $s1%, all threat by $s3%.', 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the threat generated by your Holy spells by $s1% and all threat you generate by $s3%. While active, melee and ranged attacks against you cannot critically strike.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 1, 'SpellClassSet': 10, 'SpellLevel': 16, 'SpellVisualID_1': 298, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


holy_shock_25912 = spell(
    id=25912,
    name='Holy Shock',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=250.0, potency_kind='direct', implicit_target_a=6),
    ],
    spell_icon_id=156,
    tooltip_vars=holy_heal_tooltip,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (paladin pass): converted to sp_potency=250.0 (paladin-potency-proposals.txt, user value; was 305.8 from a stale worktree copy of the proposals file, corrected 2026-10-02). | paladin-rework S2 HOLY 4.1: SpellLevel 40 -> 30; description quotes only its own value ({pot1*shock}, entry 1105 owned by paladin_holy_spells.py); NOT_A_PROC (AttributesEx3 0x200) kept for the resolver',
    raw_overrides={'AttributesEx3': 512, 'AttributesEx4': 1, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts the target with Holy energy, causing {pot1*shock} Holy damage.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2097152, 'SpellClassSet': 10, 'SpellLevel': 30, 'SpellVisualID_1': 128, 'StartRecoveryCategory': 133},
)


holy_shock_25914 = spell(
    id=25914,
    name='Holy Shock',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=150.0, potency_kind='heal', implicit_target_a=21),
    ],
    spell_icon_id=156,
    tooltip_vars=holy_heal_tooltip,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P7 (paladin pass): converted to sp_potency=125.0 (paladin-potency-proposals.txt, user value; was 137.8 from a stale worktree copy of the proposals file, corrected 2026-10-02). | paladin-rework S2 HOLY 4.1: sp_potency 125 -> 150 (A2), SpellLevel 40 -> 30; description quotes only its own value ({pot1*shock}); NOT_A_PROC kept for the resolver',
    raw_overrides={'AttributesEx3': 512, 'AttributesEx4': 1, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Blasts the target with Holy energy, healing an ally for {pot1*shock}.', 'EffectBonusMultiplier_2': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 65536, 'SpellClassSet': 10, 'SpellLevel': 30, 'SpellVisualID_1': 135, 'StartRecoveryCategory': 133},
)


crusader_aura_32223 = spell(
    id=32223,
    name='Crusader Aura',
    school=School.HOLY,
    attributes=151322640,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=15000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=65, base_points=19, implicit_target_a=1, apply_aura=172, radius_yards=40.0),
        Effect(type=65, base_points=19, implicit_target_a=1, apply_aura=211, radius_yards=40.0),
        Effect(type=35, base_points=19, implicit_target_a=1, apply_aura=210, radius_yards=40.0),
    ],
    spell_icon_id=2291,
    notes="pulled from existing data | paladin-rework S1 SHARED Part C C1.2/C1.3: button; learn level 62 -> 20 (trainer row is the Part C castables owner's); d0 b26 and d1 b4 reclaimed.",
    category=1300,
    raw_overrides={'ActiveIconID': 122, 'AttributesEx2': 17, 'AttributesEx3': 1114112, 'AttributesEx4': 3145728, 'AttributesEx6': 4096, 'AttributesEx7': 4, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Mounted speed increased by $s1%.  This does not stack with other movement speed increasing effects.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the mounted speed by $s1% for all party and raid members within $a1 yards. Activating it also increases their movement speed by $201163s1% for $201163d. Players may only have one Aura on them per Paladin at any one time.  This does not stack with other movement speed increasing effects.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 32, 'SpellClassSet': 10, 'SpellLevel': 20, 'SpellVisualID_1': 321, 'StanceBarOrder': 7, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


judgements_of_the_pure_53655 = spell(
    id=53655,
    name='Judgements of the Pure',
    school=School.HOLY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, misc_value=5),
    ],
    spell_icon_id=3018,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 0); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80 | paladin-rework S2 HOLY 4.1: HASTE_ALL bp 1 (+2%), points_per_level 0.2 -> 0; stale eff1 class mask d0 0x800000 cleared; cast by Paladin::OnJudgementCastHoly',
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee, ranged and casting speed increased by $s1%.', 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Melee, ranged and casting speed increased by $s1% for $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'SpellVisualID_1': 12015},
)


improved_blessing_of_might_20042 = spell(
    id=20042,
    name='Improved Blessing of Might',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=298,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the attack power bonus of your Blessing of Might by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_blessing_of_might_20045 = spell(
    id=20045,
    name='Improved Blessing of Might',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=298,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the attack power bonus of your Blessing of Might by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


benediction_20101 = spell(
    id=20101,
    name='Benediction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=101,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (0,3): eff0 ADD_PCT COST -> DUMMY (10/20/30% base mana, misc 0, trigger 0, masks cleared), new eff1 DUMMY (+5/10/15% Strength); spell_proc -20101 below.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Killing an enemy that yields experience or honor restores $s1% of your base mana and increases your Strength by $s2% for 20 sec. This effect cannot occur more than once every 5 sec.\n\n|cFF9D9D9DCapstone Bonus: Party members within 30 yards below 50% mana also regain 10% of their base mana.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


benediction_20102 = spell(
    id=20102,
    name='Benediction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=101,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (0,3): eff0 ADD_PCT COST -> DUMMY (10/20/30% base mana, misc 0, trigger 0, masks cleared), new eff1 DUMMY (+5/10/15% Strength); spell_proc -20101 below.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Killing an enemy that yields experience or honor restores $s1% of your base mana and increases your Strength by $s2% for 20 sec. This effect cannot occur more than once every 5 sec.\n\n|cFF9D9D9DCapstone Bonus: Party members within 30 yards below 50% mana also regain 10% of their base mana.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


benediction_20103 = spell(
    id=20103,
    name='Benediction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=101,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (0,3): eff0 ADD_PCT COST -> DUMMY (10/20/30% base mana, misc 0, trigger 0, masks cleared), new eff1 DUMMY (+5/10/15% Strength); spell_proc -20101 below.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Killing an enemy that yields experience or honor restores $s1% of your base mana and increases your Strength by $s2% for 20 sec. This effect cannot occur more than once every 5 sec.\n\nCapstone Bonus: Party members within 30 yards below 50% mana also regain 10% of their base mana.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


benediction_20104 = spell(
    id=20104,
    name='Benediction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=101,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §3 item 11: orphaned rank; eff0 ADD_PCT COST (mask deleted = wildcard on every paladin spell cost) -> maskless DUMMY like 20101-20103.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of all instant cast spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


benediction_20105 = spell(
    id=20105,
    name='Benediction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=101,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §3 item 11: orphaned rank; eff0 ADD_PCT COST (mask deleted = wildcard on every paladin spell cost) -> maskless DUMMY like 20101-20103.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of all instant cast spells by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_devotion_aura_20138 = spell(
    id=20138,
    name='Improved Devotion Aura',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=16, implicit_target_a=1, apply_aura=108, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=12),
    ],
    spell_icon_id=291,
    notes='pulled from existing data | paladin-rework S1 SHARED Part C C1.7: eff1 EFFECT2 +2/4/6 healing -> -2/-4/-6 (stored -3/-5/-7): lands on the Devotion burst 201161 (d2 b25 retarget).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the armor bonus of your Devotion Aura by $s1% and the damage reduction of its active effect by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskB_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_devotion_aura_20139 = spell(
    id=20139,
    name='Improved Devotion Aura',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=33, implicit_target_a=1, apply_aura=108, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=12),
    ],
    spell_icon_id=291,
    notes='pulled from existing data | paladin-rework S1 SHARED Part C C1.7: eff1 EFFECT2 +2/4/6 healing -> -2/-4/-6 (stored -3/-5/-7): lands on the Devotion burst 201161 (d2 b25 retarget).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the armor bonus of your Devotion Aura by $s1% and the damage reduction of its active effect by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskB_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_devotion_aura_20140 = spell(
    id=20140,
    name='Improved Devotion Aura',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=12),
    ],
    spell_icon_id=291,
    notes='pulled from existing data | paladin-rework S1 SHARED Part C C1.7: eff1 EFFECT2 +2/4/6 healing -> -2/-4/-6 (stored -3/-5/-7): lands on the Devotion burst 201161 (d2 b25 retarget).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the armor bonus of your Devotion Aura by $s1% and the damage reduction of its active effect by $s2%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 64, 'EffectSpellClassMaskB_1': 64, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


guardian_s_favor_20174 = spell(
    id=20174,
    name="Guardian's Favor",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=1999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=303,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Hand of Protection by $/1000;s1 sec and increases the duration of your Hand of Freedom by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskB_1': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


guardian_s_favor_20175 = spell(
    id=20175,
    name="Guardian's Favor",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-120001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=3999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=303,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Hand of Protection by $/60000;s1 min and increases the duration of your Hand of Freedom by $/1000;s2 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 128, 'EffectSpellClassMaskB_1': 16, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


spiritual_focus_20205 = spell(
    id=20205,
    name='Spiritual Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.REDUCE_PUSHBACK, misc_value=127),
    ],
    spell_icon_id=1499,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (0,1): eff1 SPELLMOD misc 9 -> HASTE_ALL bp 0, new eff2 REDUCE_PUSHBACK misc 127 bp 32 (all spells, Q8); stale class mask A_1 deleted',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your melee, ranged and spell haste by $s1%, and reduces the pushback you suffer from damaging attacks while casting by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Taking damage while casting Holy Light increases that Holy Light's critical strike chance by 30%. This effect cannot occur more than once every 10 sec.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


spiritual_focus_20206 = spell(
    id=20206,
    name='Spiritual Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.REDUCE_PUSHBACK, misc_value=127),
    ],
    spell_icon_id=1499,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (0,1): eff1 SPELLMOD misc 9 -> HASTE_ALL bp 1, new eff2 REDUCE_PUSHBACK misc 127 bp 65 (all spells, Q8); stale class mask A_1 deleted',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your melee, ranged and spell haste by $s1%, and reduces the pushback you suffer from damaging attacks while casting by $s2%.\n\n|cFF9D9D9DCapstone Bonus: Taking damage while casting Holy Light increases that Holy Light's critical strike chance by 30%. This effect cannot occur more than once every 10 sec.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


spiritual_focus_20207 = spell(
    id=20207,
    name='Spiritual Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.REDUCE_PUSHBACK, misc_value=127),
    ],
    spell_icon_id=1499,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (0,1): eff1 SPELLMOD misc 9 -> HASTE_ALL bp 2, new eff2 REDUCE_PUSHBACK misc 127 bp 99 (all spells, Q8); stale class mask A_1 deleted; r3 capstone proc row (7) + spell_pal_spiritual_focus_capstone',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases your melee, ranged and spell haste by $s1%, and reduces the pushback you suffer from damaging attacks while casting by $s2%.\n\nCapstone Bonus: Taking damage while casting Holy Light increases that Holy Light's critical strike chance by 30%. This effect cannot occur more than once every 10 sec.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


spiritual_focus_20208 = spell(
    id=20208,
    name='Spiritual Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=69, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=1499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting Flash of Light and Holy Light by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3221225472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


spiritual_focus_20209 = spell(
    id=20209,
    name='Spiritual Focus',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=55, implicit_target_a=1, apply_aura=108, misc_value=9),
    ],
    spell_icon_id=1499,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the pushback suffered from damaging attacks while casting Flash of Light and Holy Light by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 3221225472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


illumination_20210 = spell(
    id=20210,
    name='Illumination',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=112, misc_value=2689),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=241,
    notes="pulled from existing data | paladin-rework S2 HOLY 5 (2,0): ProcChance 20 -> 33, eff2 bp 29 -> 49 (50% of base cost), new eff3 ADD_PCT DAMAGE 10% on Light's Hammer; stock row -20210 unchanged",
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effectiveness of your Light's Hammer by $s3%. Your critical heals from Flash of Light, Holy Light and Holy Shock have a $h% chance to restore mana equal to $s2% of the spell's base cost.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 3221225472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(3, (0, 0, m.LIGHTS_HAMMER))},
)


illumination_20212 = spell(
    id=20212,
    name='Illumination',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=112, misc_value=2689),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=241,
    notes="pulled from existing data | paladin-rework S2 HOLY 5 (2,0): ProcChance 40 -> 66, eff2 bp 29 -> 49 (50% of base cost), new eff3 ADD_PCT DAMAGE 20% on Light's Hammer; stock row -20210 unchanged",
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effectiveness of your Light's Hammer by $s3%. Your critical heals from Flash of Light, Holy Light and Holy Shock have a $h% chance to restore mana equal to $s2% of the spell's base cost.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 3221225472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(3, (0, 0, m.LIGHTS_HAMMER))},
)


illumination_20213 = spell(
    id=20213,
    name='Illumination',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=112, misc_value=2689),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=241,
    notes="pulled from existing data | paladin-rework S2 HOLY 5 (2,0): ProcChance 60 -> 100, eff2 bp 29 -> 49 (50% of base cost), new eff3 ADD_PCT DAMAGE 30% on Light's Hammer; stock row -20210 unchanged",
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effectiveness of your Light's Hammer by $s3%. Your critical heals from Flash of Light, Holy Light and Holy Shock have a $h% chance to restore mana equal to $s2% of the spell's base cost.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 3221225472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(3, (0, 0, m.LIGHTS_HAMMER))},
)


illumination_20214 = spell(
    id=20214,
    name='Illumination',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=112, misc_value=2689),
    ],
    spell_icon_id=241,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'After getting a critical effect from your Flash of Light, Holy Light, or Holy Shock heal spell you have a $h% chance to gain mana equal to $s2% of the base cost of the spell.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 3221225472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 80, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 10},
)


illumination_20215 = spell(
    id=20215,
    name='Illumination',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=18350),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=112, misc_value=2689),
    ],
    spell_icon_id=241,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'After getting a critical effect from your Flash of Light, Holy Light, or Holy Shock heal spell you have a $h% chance to gain mana equal to $s2% of the base cost of the spell.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 3221225472, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 17408, 'RangeIndex': 1, 'SpellClassSet': 10},
)


seals_of_the_pure_20224 = spell(
    id=20224,
    name='Seals of the Pure',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=25,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Seal of Righteousness, Seal of Vengeance and Seal of Corruption and their Judgement effects by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskA_2': 4196352, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


seals_of_the_pure_20225 = spell(
    id=20225,
    name='Seals of the Pure',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=25,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Seal of Righteousness, Seal of Vengeance and Seal of Corruption and their Judgement effects by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskA_2': 4196352, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_lay_on_hands_20234 = spell(
    id=20234,
    name='Improved Lay on Hands',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=lay_on_hands_20233.id),
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=79,
    notes='pulled from existing data | paladin-rework S2 HOLY 5.2 (2,2): eff1 cooldown -120001 -> -60001 (-1 min on the 5 min base); mask key B_1 0x8000 left (matches)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants the target of your Lay on Hands spell $20233s1% reduced physical damage taken for $20233d.  In addition, the cooldown for your Lay on Hands spell is reduced by ${$m2/-60000} min.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_lay_on_hands_20235 = spell(
    id=20235,
    name='Improved Lay on Hands',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=20236),
        Effect(type=EffectType.APPLY_AURA, base_points=-120001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=79,
    notes='pulled from existing data | paladin-rework S2 HOLY 5.2 (2,2): eff1 cooldown -240001 -> -120001 (-2 min on the 5 min base); mask key B_1 0x8000 left (matches)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Grants the target of your Lay on Hands spell $20236s1% reduced physical damage taken for $20236d.  In addition, the cooldown for your Lay on Hands spell is reduced by ${$m2/-60000} min.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 32768, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassSet': 10},
)


healing_light_20237 = spell(
    id=20237,
    name='Healing Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=70,
    notes="pulled from existing data | paladin-rework S2 HOLY 5 (1,0): mask -> HEALING_LIGHT (adds Light's Hammer d2 b14); raw mask keys rewritten from the constant (HOLY 3 item 10)",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effectiveness of your Holy Light, Flash of Light, Holy Shock and Light's Hammer by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, m.HEALING_LIGHT)},
)


healing_light_20238 = spell(
    id=20238,
    name='Healing Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=70,
    notes="pulled from existing data | paladin-rework S2 HOLY 5 (1,0): mask -> HEALING_LIGHT (adds Light's Hammer d2 b14); raw mask keys rewritten from the constant (HOLY 3 item 10)",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effectiveness of your Holy Light, Flash of Light, Holy Shock and Light's Hammer by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, m.HEALING_LIGHT)},
)


healing_light_20239 = spell(
    id=20239,
    name='Healing Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108),
    ],
    spell_icon_id=70,
    notes="pulled from existing data | paladin-rework S2 HOLY 5 (1,0): mask -> HEALING_LIGHT (adds Light's Hammer d2 b14); raw mask keys rewritten from the constant (HOLY 3 item 10)",
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the effectiveness of your Holy Light, Flash of Light, Holy Shock and Light's Hammer by $s1%.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, m.HEALING_LIGHT)},
)


improved_blessing_of_wisdom_20244 = spell(
    id=20244,
    name='Improved Blessing of Wisdom',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=306,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Blessing of Wisdom spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 65536, 'EffectSpellClassMaskA_1': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_blessing_of_wisdom_20245 = spell(
    id=20245,
    name='Improved Blessing of Wisdom',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=8),
    ],
    spell_icon_id=306,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the effect of your Blessing of Wisdom spell by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectItemType_1': 65536, 'EffectSpellClassMaskA_1': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_concentration_aura_20254 = spell(
    id=20254,
    name='Improved Concentration Aura',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT1),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=1487,
    notes='pulled from existing data | paladin-rework S2 HOLY 5.2 (3,0): eff0 ADD_FLAT EFFECT1 -> ADD_PCT EFFECT1 +10% on CONCENTRATION_SCOPE (19746 d0 b17 + burst 201164 d2 b26); eff1/eff2 stock (SIC forces them onto d2 b26)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the mana restored by your Concentration Aura and its burst by $s1%, and reduces the duration of Silence and Interrupt effects on party and raid members affected by your Concentration Aura by $s2%. The duration reduction does not stack with other similar effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 131072, 'EffectSpellClassMaskC_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, m.CONCENTRATION_SCOPE)},
)


improved_concentration_aura_20255 = spell(
    id=20255,
    name='Improved Concentration Aura',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT1),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=1487,
    notes='pulled from existing data | paladin-rework S2 HOLY 5.2 (3,0): eff0 ADD_FLAT EFFECT1 -> ADD_PCT EFFECT1 +20% on CONCENTRATION_SCOPE (19746 d0 b17 + burst 201164 d2 b26); eff1/eff2 stock (SIC forces them onto d2 b26)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the mana restored by your Concentration Aura and its burst by $s1%, and reduces the duration of Silence and Interrupt effects on party and raid members affected by your Concentration Aura by $s2%. The duration reduction does not stack with other similar effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 131072, 'EffectSpellClassMaskC_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, m.CONCENTRATION_SCOPE)},
)


improved_concentration_aura_20256 = spell(
    id=20256,
    name='Improved Concentration Aura',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT1),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=107, misc_value=23),
    ],
    spell_icon_id=1487,
    notes='pulled from existing data | paladin-rework S2 HOLY 5.2 (3,0): eff0 ADD_FLAT EFFECT1 -> ADD_PCT EFFECT1 +30% on CONCENTRATION_SCOPE (19746 d0 b17 + burst 201164 d2 b26); eff1/eff2 stock (SIC forces them onto d2 b26)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the mana restored by your Concentration Aura and its burst by $s1%, and reduces the duration of Silence and Interrupt effects on party and raid members affected by your Concentration Aura by $s2%. The duration reduction does not stack with other similar effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskB_1': 131072, 'EffectSpellClassMaskC_1': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, m.CONCENTRATION_SCOPE)},
)


seals_of_the_pure_20330 = spell(
    id=20330,
    name='Seals of the Pure',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=25,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Seal of Righteousness, Seal of Vengeance and Seal of Corruption and their Judgement effects by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskA_2': 4196352, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


seals_of_the_pure_20331 = spell(
    id=20331,
    name='Seals of the Pure',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=25,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Seal of Righteousness, Seal of Vengeance and Seal of Corruption and their Judgement effects by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskA_2': 4196352, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


seals_of_the_pure_20332 = spell(
    id=20332,
    name='Seals of the Pure',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=25,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Seal of Righteousness, Seal of Vengeance and Seal of Corruption and their Judgement effects by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1024, 'EffectSpellClassMaskA_2': 4196352, 'EffectSpellClassMaskB_2': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


heart_of_the_crusader_20335 = spell(
    id=20335,
    name='Heart of the Crusader',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=237,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (1,0): text only on ranks 1-2',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Judgement and Deliverance increase the critical strike chance of all attacks against their targets by $s1% for 15 sec. Does not stack with other similar effects.\n\n|cFF9D9D9DCapstone Bonus: Your seals trigger a 1 sec global cooldown instead of 1.5 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskB_1': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 10},
)


heart_of_the_crusader_20336 = spell(
    id=20336,
    name='Heart of the Crusader',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
    ],
    spell_icon_id=237,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (1,0): text only on ranks 1-2',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Judgement and Deliverance increase the critical strike chance of all attacks against their targets by $s1% for 15 sec. Does not stack with other similar effects.\n\n|cFF9D9D9DCapstone Bonus: Your seals trigger a 1 sec global cooldown instead of 1.5 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskB_1': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 10},
)


heart_of_the_crusader_20337 = spell(
    id=20337,
    name='Heart of the Crusader',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=12),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-501, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=21),
    ],
    spell_icon_id=237,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (1,0): rank 3 adds eff2 ADD_FLAT GLOBAL_COOLDOWN -501 (-0.5 s) scoped to ALL_PLAYER_SEALS (eff index 2, SIC:4978-5000 rewrites eff1); A_1/B_1 kept for the debuff spells.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Judgement and Deliverance increase the critical strike chance of all attacks against their targets by $s1% for 15 sec. Does not stack with other similar effects.\n\nCapstone Bonus: Your seals trigger a 1 sec global cooldown instead of 1.5 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 536870912, 'EffectSpellClassMaskB_1': 536870912, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskC_1': m.ALL_PLAYER_SEALS[0], 'EffectSpellClassMaskC_2': m.ALL_PLAYER_SEALS[1]},
)


sanctified_light_20359 = spell(
    id=20359,
    name='Sanctified Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
    ],
    spell_icon_id=299,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (4,2): crit mask -> HOLY_HEAL_CASTS_AND_SHOCK (adds Flash of Light); new eff2 ADD_PCT CRIT_DAMAGE_BONUS on HOLY_HEALS; stale A_1/A_2 and orphan eff2 BasePoints/DieSides deleted',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy Light, Flash of Light and Holy Shock by $s1%, and your critical heals from Holy Light, Flash of Light and Holy Shock heal for an additional ${$m2/2}%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, m.HOLY_HEAL_CASTS_AND_SHOCK), **_mask(2, m.HOLY_HEALS)},
)


sanctified_light_20360 = spell(
    id=20360,
    name='Sanctified Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
    ],
    spell_icon_id=299,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (4,2): crit mask -> HOLY_HEAL_CASTS_AND_SHOCK (adds Flash of Light); new eff2 ADD_PCT CRIT_DAMAGE_BONUS on HOLY_HEALS; stale A_1/A_2 and orphan eff2 BasePoints/DieSides deleted',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy Light, Flash of Light and Holy Shock by $s1%, and your critical heals from Holy Light, Flash of Light and Holy Shock heal for an additional ${$m2/2}%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, m.HOLY_HEAL_CASTS_AND_SHOCK), **_mask(2, m.HOLY_HEALS)},
)


sanctified_light_20361 = spell(
    id=20361,
    name='Sanctified Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CRIT_DAMAGE_BONUS),
    ],
    spell_icon_id=299,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (4,2): crit mask -> HOLY_HEAL_CASTS_AND_SHOCK (adds Flash of Light); new eff2 ADD_PCT CRIT_DAMAGE_BONUS on HOLY_HEALS; stale A_1/A_2 and orphan eff2 BasePoints/DieSides deleted',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy Light, Flash of Light and Holy Shock by $s1%, and your critical heals from Holy Light, Flash of Light and Holy Shock heal for an additional ${$m2/2}%.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, m.HOLY_HEAL_CASTS_AND_SHOCK), **_mask(2, m.HOLY_HEALS)},
)


improved_righteous_fury_20468 = spell(
    id=20468,
    name='Improved Righteous Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=301,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While Righteous Fury is active, all damage taken is reduced by $s2%.', 'EffectBasePoints_1': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_righteous_fury_20469 = spell(
    id=20469,
    name='Improved Righteous Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-5, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=301,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While Righteous Fury is active, all damage taken is reduced by $s2%.', 'EffectBasePoints_1': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_righteous_fury_20470 = spell(
    id=20470,
    name='Improved Righteous Fury',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=107, misc_value=12),
    ],
    spell_icon_id=301,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'While Righteous Fury is active, all damage taken is reduced by $s2%.', 'EffectBasePoints_1': -1, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_1': 1, 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_hammer_of_justice_20487 = spell(
    id=20487,
    name='Improved Hammer of Justice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=302,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Decreases the cooldown of your Hammer of Justice spell by $/1000;s1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_hammer_of_justice_20488 = spell(
    id=20488,
    name='Improved Hammer of Justice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-20001, implicit_target_a=1, apply_aura=107, misc_value=11),
    ],
    spell_icon_id=302,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Decreases the cooldown of your Hammer of Justice spell by $/1000;s1 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


improved_judgements_25956 = spell(
    id=25956,
    name='Improved Judgements',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=205,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (4,0): eff0 ADD_FLAT COOLDOWN -> ADD_PCT DAMAGE scoped to JUDGEMENT_ALL (U|J|Dv); new eff1 ADD_PCT DOT on U (the Vengeance unleash DoT).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Judgement and Deliverance by $s1%, and your Exorcism triggers your active seal's effect.\n\n|cFF9D9D9DCapstone Bonus: When your Judgement or Deliverance releases a Primed seal, your next ability that grants seal stacks grants 1 additional stack.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_1': m.JUDGEMENT_ALL[0], 'EffectSpellClassMaskA_3': m.JUDGEMENT_ALL[2], 'EffectSpellClassMaskB_1': m.UNLEASH},
)


improved_judgements_25957 = spell(
    id=25957,
    name='Improved Judgements',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=205,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (4,0): eff0 ADD_FLAT COOLDOWN -> ADD_PCT DAMAGE scoped to JUDGEMENT_ALL (U|J|Dv); new eff1 ADD_PCT DOT on U (the Vengeance unleash DoT).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Judgement and Deliverance by $s1%, and your Exorcism triggers your active seal's effect.\n\n|cFF9D9D9DCapstone Bonus: When your Judgement or Deliverance releases a Primed seal, your next ability that grants seal stacks grants 1 additional stack.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_1': m.JUDGEMENT_ALL[0], 'EffectSpellClassMaskA_3': m.JUDGEMENT_ALL[2], 'EffectSpellClassMaskB_1': m.UNLEASH},
)


spiritual_attunement_31785 = spell(
    id=31785,
    name='Spiritual Attunement',
    school=School.HOLY,
    attributes=64,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1949,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A passive ability that gives the Paladin mana when healed by other friendly targets' spells.  The amount of mana gained is equal to $s1% of the amount healed.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 559104, 'RangeIndex': 1, 'SpellClassMask_2': 4096, 'SpellClassSet': 10},
)


pure_of_heart_31822 = spell(
    id=31822,
    name='Pure of Heart',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2142,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (4,0): eff1 -> DUMMY bp 19 (mana % of Intellect, TUNE); stock eff2/eff3 and the stale mask removed; r3 is 201279',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Purify or Cleanse removes a Disease or Poison effect, you restore mana equal to $s1% of your Intellect every sec for 5 sec.\n\n|cFF9D9D9DCapstone Bonus: The duration of Disease effects on you is reduced by 30%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


pure_of_heart_31823 = spell(
    id=31823,
    name='Pure of Heart',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=2142,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (4,0): eff1 -> DUMMY bp 39 (mana % of Intellect, TUNE); stock eff2/eff3 and the stale mask removed; r3 is 201279',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Purify or Cleanse removes a Disease or Poison effect, you restore mana equal to $s1% of your Intellect every sec for 5 sec.\n\n|cFF9D9D9DCapstone Bonus: The duration of Disease effects on you is reduced by 30%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


purifying_power_31825 = spell(
    id=31825,
    name='Purifying Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-16, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=-26, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=2173,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (5,3): cost -15/-30% on Cleanse/Purify/Consecration/Holy Wrath, Holy Wrath cooldown -25/-50% (Exorcism dropped: stale B_2 0x200002 rewritten), new eff3 Holy Wrath damage +10/+20%; Consecration +dmg is linked passive 201239/201280 (paladin_holy_spells.py); stray row-level SpellClassMask_1 4096 on 31826 deleted (31825 lacks it)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Holy Wrath and Consecration by $s3%, reduces the cooldown of your Holy Wrath by $s2%, and reduces the mana cost of your Cleanse, Purify, Holy Wrath and Consecration by $s1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, (0x1020, 0x200000, 0)), **_mask(2, (0, m.HOLY_WRATH, 0)), **_mask(3, (0, m.HOLY_WRATH, 0))},
)


purifying_power_31826 = spell(
    id=31826,
    name='Purifying Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=2173,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (5,3): cost -15/-30% on Cleanse/Purify/Consecration/Holy Wrath, Holy Wrath cooldown -25/-50% (Exorcism dropped: stale B_2 0x200002 rewritten), new eff3 Holy Wrath damage +10/+20%; Consecration +dmg is linked passive 201239/201280 (paladin_holy_spells.py); stray row-level SpellClassMask_1 4096 on 31826 deleted (31825 lacks it)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Holy Wrath and Consecration by $s3%, reduces the cooldown of your Holy Wrath by $s2%, and reduces the mana cost of your Cleanse, Purify, Holy Wrath and Consecration by $s1%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, (0x1020, 0x200000, 0)), **_mask(2, (0, m.HOLY_WRATH, 0)), **_mask(3, (0, m.HOLY_WRATH, 0))},
)


blessed_life_31828 = spell(
    id=31828,
    name='Blessed Life',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=31934),
    ],
    spell_icon_id=2137,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'All attacks against you have a $h% chance to cause half damage.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 4128, 'EffectSpellClassMaskB_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 4, 'ProcTypeMask': 1048576, 'RangeIndex': 1, 'SpellClassSet': 10},
)


blessed_life_31829 = spell(
    id=31829,
    name='Blessed Life',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=31934),
    ],
    spell_icon_id=2137,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'All attacks against you have a $h% chance to cause half damage.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 4128, 'EffectSpellClassMaskB_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 7, 'ProcTypeMask': 1048576, 'RangeIndex': 1, 'SpellClassSet': 10},
)


blessed_life_31830 = spell(
    id=31830,
    name='Blessed Life',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=31934),
    ],
    spell_icon_id=2137,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'All attacks against you have a $h% chance to cause half damage.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectSpellClassMaskA_1': 4128, 'EffectSpellClassMaskB_2': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 1048576, 'RangeIndex': 1, 'SpellClassSet': 10},
)


light_s_grace_31833 = spell(
    id=31833,
    name="Light's Grace",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=0),
    ],
    spell_icon_id=2141,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (6,0): eff1 PROC_TRIGGER_SPELL 31834 -> DUMMY bp 0, trigger_spell 0 / misc 0 (X5), ProcChance -> 100, stale masks deleted; row -31833 rewritten (CAST phase)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Holy Light increases the healing of your next Flash of Light by 10%, and your Flash of Light increases the healing of your next Holy Light by 5%. Each effect lasts 15 sec.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 10},
)


light_s_grace_31835 = spell(
    id=31835,
    name="Light's Grace",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=0),
    ],
    spell_icon_id=2141,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (6,0): eff1 PROC_TRIGGER_SPELL 31834 -> DUMMY bp 0, trigger_spell 0 / misc 0 (X5), ProcChance -> 100, stale masks deleted; row -31833 rewritten (CAST phase)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Holy Light increases the healing of your next Flash of Light by 20%, and your Flash of Light increases the healing of your next Holy Light by 10%. Each effect lasts 15 sec.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 10},
)


light_s_grace_31836 = spell(
    id=31836,
    name="Light's Grace",
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=0),
    ],
    spell_icon_id=2141,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (6,0): eff1 PROC_TRIGGER_SPELL 31834 -> DUMMY bp 0, trigger_spell 0 / misc 0 (X5), ProcChance -> 100, stale masks deleted; row -31833 rewritten (CAST phase)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your Holy Light increases the healing of your next Flash of Light by 30%, and your Flash of Light increases the healing of your next Holy Light by 15%. Each effect lasts 15 sec.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 10},
)


holy_guidance_31837 = spell(
    id=31837,
    name='Holy Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_DAMAGE_OF_STAT_PERCENT, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_HEALING_OF_STAT_PERCENT, misc_value=3),
    ],
    spell_icon_id=2139,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (7,2): eff1 misc 126 -> 2 (Holy); stray mask A_1 deleted; EffectMiscValueB_1 3 (the Intellect stat selector of aura 174) deliberately kept',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Holy spell power and your healing power by $s1% of your Intellect.\n\n|cFF9D9D9DCapstone Bonus: Your Holy Shock increases the critical strike chance of all attacks against an enemy target by 5%, or the critical strike chance of your heals on a friendly target by 5%, for 20 sec.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


holy_guidance_31838 = spell(
    id=31838,
    name='Holy Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_DAMAGE_OF_STAT_PERCENT, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_HEALING_OF_STAT_PERCENT, misc_value=3),
    ],
    spell_icon_id=2139,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (7,2): eff1 misc 126 -> 2 (Holy); stray mask A_1 deleted; EffectMiscValueB_1 3 (the Intellect stat selector of aura 174) deliberately kept',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Holy spell power and your healing power by $s1% of your Intellect.\n\n|cFF9D9D9DCapstone Bonus: Your Holy Shock increases the critical strike chance of all attacks against an enemy target by 5%, or the critical strike chance of your heals on a friendly target by 5%, for 20 sec.|r', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


holy_guidance_31839 = spell(
    id=31839,
    name='Holy Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_DAMAGE_OF_STAT_PERCENT, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=11, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_HEALING_OF_STAT_PERCENT, misc_value=3),
    ],
    spell_icon_id=2139,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (7,2): eff1 misc 126 -> 2 (Holy); stray mask A_1 deleted; EffectMiscValueB_1 3 (the Intellect stat selector of aura 174) deliberately kept',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Holy spell power and your healing power by $s1% of your Intellect.\n\nCapstone Bonus: Your Holy Shock increases the critical strike chance of all attacks against an enemy target by 5%, or the critical strike chance of your heals on a friendly target by 5%, for 20 sec.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


holy_guidance_31840 = spell(
    id=31840,
    name='Holy Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=175, misc_value=3),
    ],
    spell_icon_id=2139,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by $s1% of your total Intellect.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 67240008, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


holy_guidance_31841 = spell(
    id=31841,
    name='Holy Guidance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=175, misc_value=3),
    ],
    spell_icon_id=2139,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by $s1% of your total Intellect.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 3, 'EffectSpellClassMaskA_1': 67240008, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


stoicism_31844 = spell(
    id=31844,
    name='Stoicism',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=232, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=2213,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of all Stun effects by an additional $s1% and reduces the chance your helpful spells and damage over time effects will be dispelled by an additional $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67240008, 'EffectSpellClassMaskB_1': 994124691, 'EffectSpellClassMaskB_2': 2269654336, 'EffectSpellClassMaskB_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


stoicism_31845 = spell(
    id=31845,
    name='Stoicism',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=232, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=2213,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of all Stun effects by an additional $s1% and reduces the chance your helpful spells and damage over time effects will be dispelled by an additional $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67240008, 'EffectSpellClassMaskB_1': 994124691, 'EffectSpellClassMaskB_2': 2269654336, 'EffectSpellClassMaskB_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


sacred_duty_31848 = spell(
    id=31848,
    name='Sacred Duty',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=107, misc_value=11),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=81,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Stamina by $s3%, reduces the cooldown of your Divine Shield and Divine Protection spells by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


sacred_duty_31849 = spell(
    id=31849,
    name='Sacred Duty',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=107, misc_value=11),
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=137, misc_value=2),
    ],
    spell_icon_id=81,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your total Stamina by $s3%, reduces the cooldown of your Divine Shield and Divine Protection spells by $/1000;S1 sec.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


ardent_defender_31850 = spell(
    id=31850,
    name='Ardent Defender',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(
            type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=69, misc_value=127,
            potency_excluded="percent-of-other-damage: Effects[EFFECT_0].CalcValue() is read directly as "
            "a flat percent (absorbPct) by spell_pal_ardent_defender::Absorb (CalculatePct(damageToReduce, "
            "absorbPct)), not a damage/absorb amount the potency hook could price - the effect's own "
            "amount is actually set to -1 (unlimited) by DoEffectCalcAmount, so this base_points value "
            "never reaches CalcValue's potency path at all. Same category as the Warlock pilot's "
            "Healthstones/Conflagrate percent-of-other-damage exclusions.",
        ),
        Effect(
            type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY,
            potency_excluded="percent-of-max-health: Effects[EFFECT_1].CalcValue() is read directly as a "
            "flat percent (healPct) by spell_pal_ardent_defender::Absorb (CountPctFromMaxHealth(healPct * "
            "pctFromDefense)), not a heal amount - same category as Warlock's Healthstones exclusion.",
        ),
    ],
    spell_icon_id=2135,
    notes='pulled from existing data. Potency system P7 (paladin pass): NOT converted - both effects are read as flat percentages by spell_pal_ardent_defender (src/server/scripts/Spells/spell_paladin.cpp), not damage/heal amounts; see each effect\'s own potency_excluded=.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage that takes you below 35% health is reduced by $s1%.  In addition, attacks which would otherwise kill you cause you to be healed by up to $s2% of your maximum health (amount healed based on defense).  This healing effect cannot occur more often than once every $66233d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


ardent_defender_31851 = spell(
    id=31851,
    name='Ardent Defender',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(
            type=EffectType.APPLY_AURA, base_points=12, implicit_target_a=1, apply_aura=69, misc_value=127,
            potency_excluded="percent-of-other-damage: same shape as Ardent Defender rank 1 (31850) - see "
            "its eff0 potency_excluded= for the full reasoning.",
        ),
        Effect(
            type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY,
            potency_excluded="percent-of-max-health: same shape as Ardent Defender rank 1 (31850) - see "
            "its eff1 potency_excluded= for the full reasoning.",
        ),
    ],
    spell_icon_id=2135,
    notes='pulled from existing data. Potency system P7 (paladin pass): NOT converted - see Ardent Defender rank 1 (31850)\'s notes= and each effect\'s own potency_excluded=.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage that takes you below 35% health is reduced by $s1%.  In addition, attacks which would otherwise kill you cause you to be healed by up to $s2% of your maximum health (amount healed based on defense).  This healing effect cannot occur more often than once every $66233d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


ardent_defender_31852 = spell(
    id=31852,
    name='Ardent Defender',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(
            type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=69, misc_value=127,
            potency_excluded="percent-of-other-damage: same shape as Ardent Defender rank 1 (31850) - see "
            "its eff0 potency_excluded= for the full reasoning.",
        ),
        Effect(
            type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY,
            potency_excluded="percent-of-max-health: same shape as Ardent Defender rank 1 (31850) - see "
            "its eff1 potency_excluded= for the full reasoning.",
        ),
    ],
    spell_icon_id=2135,
    notes='pulled from existing data. Potency system P7 (paladin pass): NOT converted - see Ardent Defender rank 1 (31850)\'s notes= and each effect\'s own potency_excluded=.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Damage that takes you below 35% health is reduced by $s1%.  In addition, attacks which would otherwise kill you cause you to be healed by up to $s2% of your maximum health (amount healed based on defense).  This healing effect cannot occur more often than once every $66233d.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


combat_expertise_31858 = spell(
    id=31858,
    name='Combat Expertise',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=240),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=137, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=2143,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your expertise by $s1, total Stamina and chance to critically hit by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


combat_expertise_31859 = spell(
    id=31859,
    name='Combat Expertise',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=240),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=137, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=2143,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your expertise by $s1, total Stamina and chance to critically hit by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


combat_expertise_31860 = spell(
    id=31860,
    name='Combat Expertise',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=240),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=137, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=290),
    ],
    spell_icon_id=2143,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your expertise by $s1, total Stamina and chance to critically hit by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 4194304, 'EffectSpellClassMaskB_1': 4194304, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


sanctified_retribution_31869 = spell(
    id=31869,
    name='Sanctified Retribution',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=3),
    ],
    spell_icon_id=502,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (4,3): eff0 EFFECT2 bp 0 (+1% party damage via 63531) scoped to d2 0x8000000 (SIC re-applies it on 31869 only; new ranks author it), eff1 PCT EFFECT1 +50% Retribution Aura damage; stale A_1 deleted.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Retribution Aura by $s2%, and all damage dealt by friendly targets affected by any of your auras by $s1%. Does not stack with other similar effects.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_3': m.LOADTIME_SANCTIFIED_RETRIBUTION, 'EffectSpellClassMaskB_1': m.RETRIBUTION_AURA},
)


judgements_of_the_wise_31876 = spell(
    id=31876,
    name='Judgements of the Wise',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3017,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (6,0): DBC ProcChance 33/66 -> 50/100.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your damaging Judgement and Deliverance seal releases have a $h% chance to grant Replenishment to up to 10 party or raid members, restoring 1% of their maximum mana every 5 sec for $57669d, and to restore $31930s1% of your base mana. Once per cast.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 272, 'RangeIndex': 1, 'SpellClassSet': 10, 'SpellVisualID_1': 11906},
)


judgements_of_the_wise_31877 = spell(
    id=31877,
    name='Judgements of the Wise',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3017,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (6,0): DBC ProcChance 33/66 -> 50/100.',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your damaging Judgement and Deliverance seal releases have a $h% chance to grant Replenishment to up to 10 party or raid members, restoring 1% of their maximum mana every 5 sec for $57669d, and to restore $31930s1% of your base mana. Once per cast.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 272, 'RangeIndex': 1, 'SpellClassSet': 10},
)


judgements_of_the_wise_31878 = spell(
    id=31878,
    name='Judgements of the Wise',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3017,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your damaging Judgement spells have a $h% chance to grant the Replenishment effect to up to 10 party or raid members mana regeneration equal to 1% of their maximum mana per 5 sec for $57669d, and to immediately grant you $31930s1% of your base mana.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 272, 'RangeIndex': 1, 'SpellClassSet': 10},
)


fanaticism_31879 = spell(
    id=31879,
    name='Fanaticism',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=12),
    ],
    spell_icon_id=2169,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (8,0): eff0 crit on JUDGEMENT_ALL, eff1 threat -> ADD_FLAT EFFECT2 on Execution Sentence (its aura-271 effect).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Judgement and Deliverance by $s1%, and your seal effects and seal releases deal $s2% more damage to the target of your Execution Sentence.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_1': m.JUDGEMENT_ALL[0], 'EffectSpellClassMaskA_3': m.JUDGEMENT_ALL[2], 'EffectSpellClassMaskB_3': m.EXECUTION_SENTENCE},
)


fanaticism_31880 = spell(
    id=31880,
    name='Fanaticism',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=13, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=12),
    ],
    spell_icon_id=2169,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (8,0): eff0 crit on JUDGEMENT_ALL, eff1 threat -> ADD_FLAT EFFECT2 on Execution Sentence (its aura-271 effect).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Judgement and Deliverance by $s1%, and your seal effects and seal releases deal $s2% more damage to the target of your Execution Sentence.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_1': m.JUDGEMENT_ALL[0], 'EffectSpellClassMaskA_3': m.JUDGEMENT_ALL[2], 'EffectSpellClassMaskB_3': m.EXECUTION_SENTENCE},
)


fanaticism_31881 = spell(
    id=31881,
    name='Fanaticism',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=12),
    ],
    spell_icon_id=2169,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (8,0): eff0 crit on JUDGEMENT_ALL, eff1 threat -> ADD_FLAT EFFECT2 on Execution Sentence (its aura-271 effect).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Judgement and Deliverance by $s1%, and your seal effects and seal releases deal $s2% more damage to the target of your Execution Sentence.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_1': m.JUDGEMENT_ALL[0], 'EffectSpellClassMaskA_3': m.JUDGEMENT_ALL[2], 'EffectSpellClassMaskB_3': m.EXECUTION_SENTENCE},
)


sanctity_of_battle_32043 = spell(
    id=32043,
    name='Sanctity of Battle',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201424),
    ],
    spell_icon_id=3106,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (3,2): eff0 -> ADD_PCT DAMAGE (SANCTITY_DAMAGE), eff1 -> ADD_PCT DOT (SANCTITY_DOT), eff2 -> PROC_TRIGGER 201424; icon 237 -> 3106; DBC ProcChance 33/66/100.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your abilities by $s1%:\nExorcism\nCrusader Strike\nDivine Storm\nExecution Sentence\nConsecration\nWake of Ashes\n\nYour Exorcism damage has a $h% chance to empower you for 15 sec: your next Hammer of Wrath can be used at any health and deals 35% more damage, your next Flash of Light is a critical strike, or your next Divine Storm deals 50% more damage. The first of these you use consumes the effect.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_1': m.SANCTITY_DAMAGE[0], 'EffectSpellClassMaskA_2': m.SANCTITY_DAMAGE[1], 'EffectSpellClassMaskA_3': m.SANCTITY_DAMAGE[2], 'EffectSpellClassMaskB_1': m.SANCTITY_DOT[0], 'EffectSpellClassMaskB_3': m.SANCTITY_DOT[2], 'ProcChance': 33},
)


spiritual_attunement_33776 = spell(
    id=33776,
    name='Spiritual Attunement',
    school=School.HOLY,
    attributes=64,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=1949,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "A passive ability that gives the Paladin mana when healed by other friendly targets' spells.  The amount of mana gained is equal to $s1% of the amount healed.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 559104, 'RangeIndex': 1, 'SpellClassMask_2': 4096, 'SpellClassSet': 10},
)


sanctity_of_battle_35396 = spell(
    id=35396,
    name='Sanctity of Battle',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201424),
    ],
    spell_icon_id=3106,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (3,2): eff0 -> ADD_PCT DAMAGE (SANCTITY_DAMAGE), eff1 -> ADD_PCT DOT (SANCTITY_DOT), eff2 -> PROC_TRIGGER 201424; icon 237 -> 3106; DBC ProcChance 33/66/100.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your abilities by $s1%:\nExorcism\nCrusader Strike\nDivine Storm\nExecution Sentence\nConsecration\nWake of Ashes\n\nYour Exorcism damage has a $h% chance to empower you for 15 sec: your next Hammer of Wrath can be used at any health and deals 35% more damage, your next Flash of Light is a critical strike, or your next Divine Storm deals 50% more damage. The first of these you use consumes the effect.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_1': m.SANCTITY_DAMAGE[0], 'EffectSpellClassMaskA_2': m.SANCTITY_DAMAGE[1], 'EffectSpellClassMaskA_3': m.SANCTITY_DAMAGE[2], 'EffectSpellClassMaskB_1': m.SANCTITY_DOT[0], 'EffectSpellClassMaskB_3': m.SANCTITY_DOT[2], 'ProcChance': 66},
)


sanctity_of_battle_35397 = spell(
    id=35397,
    name='Sanctity of Battle',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201424),
    ],
    spell_icon_id=3106,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (3,2): eff0 -> ADD_PCT DAMAGE (SANCTITY_DAMAGE), eff1 -> ADD_PCT DOT (SANCTITY_DOT), eff2 -> PROC_TRIGGER 201424; icon 237 -> 3106; DBC ProcChance 33/66/100.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your abilities by $s1%:\nExorcism\nCrusader Strike\nDivine Storm\nExecution Sentence\nConsecration\nWake of Ashes\n\nYour Exorcism damage has a $h% chance to empower you for 15 sec: your next Hammer of Wrath can be used at any health and deals 35% more damage, your next Flash of Light is a critical strike, or your next Divine Storm deals 50% more damage. The first of these you use consumes the effect.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_1': m.SANCTITY_DAMAGE[0], 'EffectSpellClassMaskA_2': m.SANCTITY_DAMAGE[1], 'EffectSpellClassMaskA_3': m.SANCTITY_DAMAGE[2], 'EffectSpellClassMaskB_1': m.SANCTITY_DOT[0], 'EffectSpellClassMaskB_3': m.SANCTITY_DOT[2], 'ProcChance': 100},
)


sanctified_wrath_53375 = spell(
    id=53375,
    name='Sanctified Wrath',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=3029,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (7,2): eff0 -> Hammer of Wrath crit, eff1 -> Exorcism cooldown PCT, eff2 (stock Avenging Wrath rider key) -> Exorcism damage PCT; spell_pal_avenging_wrath is unbound from 31884 by the Avenging Wrath owner (RETRIBUTION §0.2 item 9).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of Hammer of Wrath by $s1%, increases the damage of Exorcism by $s3% and reduces its cooldown by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_2': m.HAMMER_OF_WRATH, 'EffectSpellClassMaskB_2': m.EXORCISM, 'EffectSpellClassMaskC_2': m.EXORCISM},
)


sanctified_wrath_53376 = spell(
    id=53376,
    name='Sanctified Wrath',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
        Effect(type=EffectType.APPLY_AURA, base_points=-41, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=3029,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (7,2): eff0 -> Hammer of Wrath crit, eff1 -> Exorcism cooldown PCT, eff2 (stock Avenging Wrath rider key) -> Exorcism damage PCT; spell_pal_avenging_wrath is unbound from 31884 by the Avenging Wrath owner (RETRIBUTION §0.2 item 9).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of Hammer of Wrath by $s1%, increases the damage of Exorcism by $s3% and reduces its cooldown by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_2': m.HAMMER_OF_WRATH, 'EffectSpellClassMaskB_2': m.EXORCISM, 'EffectSpellClassMaskC_2': m.EXORCISM},
)


swift_retribution_53379 = spell(
    id=53379,
    name='Swift Retribution',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201426),
    ],
    spell_icon_id=3028,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (8,2): eff0 unchanged (63531 party haste, SIC retarget), new eff1 PROC_TRIGGER -> the self haste stack buff.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auras increase the casting, melee and ranged attack speed of party and raid members by $s1%. Does not stack with other similar effects. Your Crusader Strike and Judgement increase your haste by $201426s1% for 10 sec, stacking up to 3 times.\n\n|cFF9D9D9DCapstone Bonus: Each stack also increases the damage of your Exorcism by 5%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


righteous_vengeance_53380 = spell(
    id=53380,
    name='Righteous Vengeance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=15),
    ],
    spell_icon_id=3025,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (9,1): description only (the proc row -53380 is rekeyed below).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Judgement, Deliverance, Crusader Strike, Divine Storm, Hammer of Wrath, Exorcism, Hammer of the Righteous or Shield of Righteousness deal a critical strike, the target takes $s1% of the damage dealt as additional Holy damage over $61840d. Remaining damage from a previous effect is added to a new one.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 8388608, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69904, 'RangeIndex': 1, 'SpellClassSet': 10},
)


righteous_vengeance_53381 = spell(
    id=53381,
    name='Righteous Vengeance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=15),
    ],
    spell_icon_id=3025,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (9,1): description only (the proc row -53380 is rekeyed below).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Judgement, Deliverance, Crusader Strike, Divine Storm, Hammer of Wrath, Exorcism, Hammer of the Righteous or Shield of Righteousness deal a critical strike, the target takes $s1% of the damage dealt as additional Holy damage over $61840d. Remaining damage from a previous effect is added to a new one.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 8388608, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69904, 'RangeIndex': 1, 'SpellClassSet': 10},
)


righteous_vengeance_53382 = spell(
    id=53382,
    name='Righteous Vengeance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=15),
    ],
    spell_icon_id=3025,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (9,1): description only (the proc row -53380 is rekeyed below).',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When your Judgement, Deliverance, Crusader Strike, Divine Storm, Hammer of Wrath, Exorcism, Hammer of the Righteous or Shield of Righteousness deal a critical strike, the target takes $s1% of the damage dealt as additional Holy damage over $61840d. Remaining damage from a previous effect is added to a new one.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EffectSpellClassMaskA_1': 8388608, 'EffectSpellClassMaskA_2': 131072, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69904, 'RangeIndex': 1, 'SpellClassSet': 10},
)


swift_retribution_53484 = spell(
    id=53484,
    name='Swift Retribution',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201427),
    ],
    spell_icon_id=3028,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (8,2): eff0 unchanged (63531 party haste, SIC retarget), new eff1 PROC_TRIGGER -> the self haste stack buff.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auras increase the casting, melee and ranged attack speed of party and raid members by $s1%. Does not stack with other similar effects. Your Crusader Strike and Judgement increase your haste by $201427s1% for 10 sec, stacking up to 3 times.\n\n|cFF9D9D9DCapstone Bonus: Each stack also increases the damage of your Exorcism by 5%.|r', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


the_art_of_war_53486 = spell(
    id=53486,
    name='The Art of War',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59578),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=3034,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (7,1): eff0 ADD_PCT DAMAGE (AOW_DAMAGE), eff1 triggers 59578 on every rank, new eff2 ADD_PCT DOT (AOW_DOT); DBC ProcChance 10/20/30.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Judgement, Deliverance, Crusader Strike, Execution Sentence and Divine Storm by $s1%. Damage from these and your main-hand auto attacks has a $h% chance to make your next Flash of Light or Exorcism instant within 20 sec; Divine Storm rolls at half the chance on each target hit. This effect cannot occur more than once every 6 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'ProcTypeMask': 4116, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_1': m.AOW_DAMAGE[0], 'EffectSpellClassMaskA_2': m.AOW_DAMAGE[1], 'EffectSpellClassMaskA_3': m.AOW_DAMAGE[2], 'EffectSpellClassMaskC_1': m.AOW_DOT[0], 'EffectSpellClassMaskC_3': m.AOW_DOT[2]},
)


the_art_of_war_53488 = spell(
    id=53488,
    name='The Art of War',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59578),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=3034,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (7,1): eff0 ADD_PCT DAMAGE (AOW_DAMAGE), eff1 triggers 59578 on every rank, new eff2 ADD_PCT DOT (AOW_DOT); DBC ProcChance 10/20/30.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Judgement, Deliverance, Crusader Strike, Execution Sentence and Divine Storm by $s1%. Damage from these and your main-hand auto attacks has a $h% chance to make your next Flash of Light or Exorcism instant within 20 sec; Divine Storm rolls at half the chance on each target hit. This effect cannot occur more than once every 6 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 20, 'ProcTypeMask': 4116, 'RangeIndex': 1, 'SpellClassSet': 10, 'EffectSpellClassMaskA_1': m.AOW_DAMAGE[0], 'EffectSpellClassMaskA_2': m.AOW_DAMAGE[1], 'EffectSpellClassMaskA_3': m.AOW_DAMAGE[2], 'EffectSpellClassMaskC_1': m.AOW_DOT[0], 'EffectSpellClassMaskC_3': m.AOW_DOT[2]},
)


sheath_of_light_53501 = spell(
    id=53501,
    name='Sheath of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=237, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=238, misc_value=127),
    ],
    spell_icon_id=3030,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (4,2): description only.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by an amount equal to $s1% of your attack power, and your critical heals heal the target for an additional $s2% of the healed amount over 12 sec. A new effect replaces the old one.\n\n|cFF9D9D9DCapstone Bonus: Your Flash of Light on yourself restores 8% of your base mana. This effect cannot occur more than once every 10 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 10},
)


sheath_of_light_53502 = spell(
    id=53502,
    name='Sheath of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=237, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=238, misc_value=127),
    ],
    spell_icon_id=3030,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (4,2): description only.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by an amount equal to $s1% of your attack power, and your critical heals heal the target for an additional $s2% of the healed amount over 12 sec. A new effect replaces the old one.\n\n|cFF9D9D9DCapstone Bonus: Your Flash of Light on yourself restores 8% of your base mana. This effect cannot occur more than once every 10 sec.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 10},
)


sheath_of_light_53503 = spell(
    id=53503,
    name='Sheath of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=237, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=238, misc_value=127),
    ],
    spell_icon_id=3030,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (4,2): description only.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by an amount equal to $s1% of your attack power, and your critical heals heal the target for an additional $s2% of the healed amount over 12 sec. A new effect replaces the old one.\n\nCapstone Bonus: Your Flash of Light on yourself restores 8% of your base mana. This effect cannot occur more than once every 10 sec.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 10},
)


stoicism_53519 = spell(
    id=53519,
    name='Stoicism',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=232, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=107, misc_value=28),
    ],
    spell_icon_id=2213,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the duration of all Stun effects by an additional $s1% and reduces the chance your helpful spells and damage over time effects will be dispelled by an additional $s2%.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 67240008, 'EffectSpellClassMaskB_1': 994124691, 'EffectSpellClassMaskB_2': 2269654336, 'EffectSpellClassMaskB_3': 2, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


divine_guardian_53527 = spell(
    id=53527,
    name='Divine Guardian',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=231, misc_value=3, trigger_spell=70940),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=108, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=3837,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When Divine Sacrifice is activated, your party and raid members within $70940a1 yards take $s1% reduced damage for $70940d.  In addition, increases the duration of your Sacred Shield by $s2% and the amount absorbed by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': 4, 'EffectSpellClassMaskB_2': 524288, 'EffectSpellClassMaskC_2': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 10},
)


divine_guardian_53530 = spell(
    id=53530,
    name='Divine Guardian',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=231, misc_value=3, trigger_spell=70940),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=108, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=3),
    ],
    spell_icon_id=3837,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When Divine Sacrifice is activated, your party and raid members within $70940a1 yards take $s1% reduced damage for $70940d.  In addition, increases the duration of your Sacred Shield by $s2% and the amount absorbed by $s3%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': 4, 'EffectSpellClassMaskB_2': 524288, 'EffectSpellClassMaskC_2': 524288, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 10},
)


sacred_cleansing_53551 = spell(
    id=53551,
    name='Sacred Cleansing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=53659),
    ],
    spell_icon_id=3019,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (7,0): DBC ProcChance 10 -> 33; stock row -53551 kept; buff 53659 8 s',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Cleanse and Purify have a $h% chance to increase the target's resistance to Disease, Magic and Poison by $53659s1% for $53659d.\n\n|cFF9D9D9DCapstone Bonus: When your Cleanse removes an effect, it also places your Glimmer of Light on the target, if you know Glimmer of Light.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2149580800, 'EffectSpellClassMaskA_2': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 10},
)


sacred_cleansing_53552 = spell(
    id=53552,
    name='Sacred Cleansing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=53659),
    ],
    spell_icon_id=3019,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (7,0): DBC ProcChance 20 -> 66; stock row -53551 kept; buff 53659 8 s',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Cleanse and Purify have a $h% chance to increase the target's resistance to Disease, Magic and Poison by $53659s1% for $53659d.\n\n|cFF9D9D9DCapstone Bonus: When your Cleanse removes an effect, it also places your Glimmer of Light on the target, if you know Glimmer of Light.|r", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2149580800, 'EffectSpellClassMaskA_2': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 10},
)


sacred_cleansing_53553 = spell(
    id=53553,
    name='Sacred Cleansing',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=53659),
    ],
    spell_icon_id=3019,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (7,0): DBC ProcChance 30 -> 100; stock row -53551 kept; buff 53659 8 s',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your Cleanse and Purify have a $h% chance to increase the target's resistance to Disease, Magic and Poison by $53659s1% for $53659d.\n\nCapstone Bonus: When your Cleanse removes an effect, it also places your Glimmer of Light on the target, if you know Glimmer of Light.", 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2149580800, 'EffectSpellClassMaskA_2': 65536, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 16384, 'RangeIndex': 1, 'SpellClassSet': 10},
)


enlightened_judgements_53556 = spell(
    id=53556,
    name='Enlightened Judgements',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.RANGE),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3020,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (9,3): range mod U -> JUDGEMENT_OWN_HITS (J+Dv), eff2 hit chance -> DUMMY bp 49/99 (pulse %), eff3 removed',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your Judgement and Deliverance by $s1 yards. Your Judgement and Deliverance make each of your Glimmers of Light pulse for $s2% of the value of your last Glimmer pulse of its kind.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, m.JUDGEMENT_OWN_HITS)},
)


enlightened_judgements_53557 = spell(
    id=53557,
    name='Enlightened Judgements',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.RANGE),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3020,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (9,3): range mod U -> JUDGEMENT_OWN_HITS (J+Dv), eff2 hit chance -> DUMMY bp 49/99 (pulse %), eff3 removed',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the range of your Judgement and Deliverance by $s1 yards. Your Judgement and Deliverance make each of your Glimmers of Light pulse for $s2% of the value of your last Glimmer pulse of its kind.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 5, 'RangeIndex': 1, 'SpellClassSet': 10, **_mask(1, m.JUDGEMENT_OWN_HITS)},
)


infusion_of_light_53569 = spell(
    id=53569,
    name='Infusion of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=0),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3021,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (9,1): eff1 PROC_TRIGGER_SPELL -> DUMMY bp 19/39 (Shock proc %, TUNE) with trigger_spell 0 / misc 0 (X5); new real eff2 DUMMY bp 49/99 (Flash HoT %) replaces the orphan eff3 raw keys; row -53569 rewritten (DisableEffectsMask 0x2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your healing Holy Shock has a $s1% chance to grant Infusion of Light for 15 sec, reducing the cast time of your next Flash of Light by 50% or increasing the critical strike chance of your next Holy Light by 10%. In addition, your Flash of Light heals targets with Sacred Shield for an additional $s2% over $66922d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 81920, 'RangeIndex': 1, 'SpellClassSet': 10},
)


infusion_of_light_53576 = spell(
    id=53576,
    name='Infusion of Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.DUMMY, trigger_spell=0),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3021,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (9,1): eff1 PROC_TRIGGER_SPELL -> DUMMY bp 19/39 (Shock proc %, TUNE) with trigger_spell 0 / misc 0 (X5); new real eff2 DUMMY bp 49/99 (Flash HoT %) replaces the orphan eff3 raw keys; row -53569 rewritten (DisableEffectsMask 0x2)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your healing Holy Shock has a $s1% chance to grant Infusion of Light for 15 sec, reducing the cast time of your next Flash of Light by 100% or increasing the critical strike chance of your next Holy Light by 20%. In addition, your Flash of Light heals targets with Sacred Shield for an additional $s2% over $66922d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 81920, 'RangeIndex': 1, 'SpellClassSet': 10},
)


guarded_by_the_light_53583 = spell(
    id=53583,
    name='Guarded by the Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=107, misc_value=28),
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=63521),
    ],
    spell_icon_id=3026,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces spell damage taken by $s2% and gives a $h% chance to refresh the duration of your Divine Plea when you hit an enemy.  In addition, your Divine Plea spell is $s1% less likely to be dispelled.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 50, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 10},
)


guarded_by_the_light_53585 = spell(
    id=53585,
    name='Guarded by the Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=107, misc_value=28),
        Effect(type=EffectType.APPLY_AURA, base_points=-7, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=63521),
    ],
    spell_icon_id=3026,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces spell damage taken by $s2% and gives a $h% chance to refresh the duration of your Divine Plea when you hit an enemy.  In addition, your Divine Plea spell is $s1% less likely to be dispelled.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': 1, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassSet': 10},
)


touched_by_the_light_53590 = spell(
    id=53590,
    name='Touched by the Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=50, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=175),
    ],
    spell_icon_id=3024,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by an amount equal to $s1% of your Strength and increases the amount healed by your critical heals by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'RangeIndex': 1, 'SpellClassSet': 10},
)


touched_by_the_light_53591 = spell(
    id=53591,
    name='Touched by the Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=50, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=175),
    ],
    spell_icon_id=3024,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by an amount equal to $s1% of your Strength and increases the amount healed by your critical heals by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'RangeIndex': 1, 'SpellClassSet': 10},
)


touched_by_the_light_53592 = spell(
    id=53592,
    name='Touched by the Light',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=174, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=50, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=175),
    ],
    spell_icon_id=3024,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell power by an amount equal to $s1% of your Strength and increases the amount healed by your critical heals by $s2%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2048, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 10, 'RangeIndex': 1, 'SpellClassSet': 10},
)


swift_retribution_53648 = spell(
    id=53648,
    name='Swift Retribution',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=107, misc_value=23),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201428),
    ],
    spell_icon_id=3028,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (8,2): eff0 unchanged (63531 party haste, SIC retarget), new eff1 PROC_TRIGGER -> the self haste stack buff.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your auras increase the casting, melee and ranged attack speed of party and raid members by $s1%. Does not stack with other similar effects. Your Crusader Strike and Judgement increase your haste by $201428s1% for 10 sec, stacking up to 3 times.\n\nCapstone Bonus: Each stack also increases the damage of your Exorcism by 5%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


blessed_hands_53660 = spell(
    id=53660,
    name='Blessed Hands',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.EFFECT1),
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT1),
    ],
    spell_icon_id=3022,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (3,1): 3 ranks (r3 is 201278); cost -10%, Sacrifice +3, Salvation +33% (Q7 TUNE); masks already per-effect (A_1/B_1/C_1 kept)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Hand of Freedom, Hand of Sacrifice and Hand of Salvation by $s1%, increases the effectiveness of your Hand of Salvation by $s3% and the effectiveness of your Hand of Sacrifice by an additional $s2%.\n\n|cFF9D9D9DCapstone Bonus: While one of your Hand spells is on a target, your healing done to that target is increased by 15%.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8464, 'EffectSpellClassMaskB_1': 8192, 'EffectSpellClassMaskC_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


blessed_hands_53661 = spell(
    id=53661,
    name='Blessed Hands',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.COST),
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.EFFECT1),
        Effect(type=EffectType.APPLY_AURA, base_points=65, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.EFFECT1),
    ],
    spell_icon_id=3022,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (3,1): 3 ranks (r3 is 201278); cost -20%, Sacrifice +7, Salvation +66% (Q7 TUNE); masks already per-effect (A_1/B_1/C_1 kept)',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the mana cost of your Hand of Freedom, Hand of Sacrifice and Hand of Salvation by $s1%, increases the effectiveness of your Hand of Salvation by $s3% and the effectiveness of your Hand of Sacrifice by an additional $s2%.\n\n|cFF9D9D9DCapstone Bonus: While one of your Hand spells is on a target, your healing done to that target is increased by 15%.|r', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 8464, 'EffectSpellClassMaskB_1': 8192, 'EffectSpellClassMaskC_1': 256, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10},
)


judgements_of_the_pure_53671 = spell(
    id=53671,
    name='Judgements of the Pure',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=3018,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (8,3): eff1 seal damage / eff2 seal DoT on SEAL_DAMAGE (U+P), eff3 own hits on JUDGEMENT_OWN_HITS (J+Dv); all eight stale mask keys deleted; DBC ProcTypeMask -> 0 and ProcChance 101 (CR4) with remove_spell_proc(-53671)',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Seals, including the Seal power unleashed by your Judgement and Deliverance, by $s1%, and the direct damage of your Judgement and Deliverance by $s3%. Your Judgement and Deliverance increase your melee, ranged and casting speed by $53655s1% for 1 min.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 10, 'SpellVisualID_1': 12015, **_mask(1, m.SEAL_DAMAGE), **_mask(2, m.SEAL_DAMAGE), **_mask(3, m.JUDGEMENT_OWN_HITS)},
)


judgements_of_the_pure_53673 = spell(
    id=53673,
    name='Judgements of the Pure',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=15, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=3018,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (8,3): eff1 seal damage / eff2 seal DoT on SEAL_DAMAGE (U+P), eff3 own hits on JUDGEMENT_OWN_HITS (J+Dv); all eight stale mask keys deleted; DBC ProcTypeMask -> 0 and ProcChance 101 (CR4) with remove_spell_proc(-53671)',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Seals, including the Seal power unleashed by your Judgement and Deliverance, by $s1%, and the direct damage of your Judgement and Deliverance by $s3%. Your Judgement and Deliverance increase your melee, ranged and casting speed by $53656s1% for 1 min.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 10, 'SpellVisualID_1': 12015, **_mask(1, m.SEAL_DAMAGE), **_mask(2, m.SEAL_DAMAGE), **_mask(3, m.JUDGEMENT_OWN_HITS)},
)


judgements_of_the_just_53695 = spell(
    id=53695,
    name='Judgements of the Just',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=-5001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=499, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=3015,
    notes='pulled from existing data | paladin-rework S1 SHARED B7: Judgements of the Just removed, ProcTypeMask 69904 -> 0 so SpellMgr builds no default row once remove_spell_proc(-53695) deletes the stock one.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Hammer of Justice by $/1000;s2 sec, increases the duration of your Seal of Justice effect by $/1000;S3 sec and your Judgement spells also reduce the melee attack speed of the target by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': 64, 'EffectSpellClassMaskB_1': 2048, 'EffectSpellClassMaskC_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 10},
)


judgements_of_the_just_53696 = spell(
    id=53696,
    name='Judgements of the Just',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-21, implicit_target_a=1, apply_aura=107, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, implicit_target_a=1, apply_aura=107, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=999, implicit_target_a=1, apply_aura=107, misc_value=1),
    ],
    spell_icon_id=3015,
    notes='pulled from existing data | paladin-rework S1 SHARED B7: Judgements of the Just removed, ProcTypeMask 69904 -> 0 so SpellMgr builds no default row once remove_spell_proc(-53695) deletes the stock one.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Hammer of Justice by $/1000;s2 sec, increases the duration of your Seal of Justice effect by $/1000;S3 sec and your Judgement spells also reduce the melee attack speed of the target by $s1%.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_3': 64, 'EffectSpellClassMaskB_1': 2048, 'EffectSpellClassMaskC_1': 512, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 10},
)


shield_of_the_templar_53709 = spell(
    id=53709,
    name='Shield of the Templar',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=63529),
    ],
    spell_icon_id=3016,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces all damage taken by $s2% and grants your Avenger's Shield a $h% chance to silence your targets for $63529d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskA_2': 1048640, 'EffectSpellClassMaskB_1': 16384, 'EffectSpellClassMaskB_2': 1048640, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'ProcChance': 33, 'ProcTypeMask': 65792, 'RangeIndex': 1, 'SpellClassSet': 10},
)


shield_of_the_templar_53710 = spell(
    id=53710,
    name='Shield of the Templar',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-3, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=63529),
    ],
    spell_icon_id=3016,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces all damage taken by $s2% and grants your Avenger's Shield a $h% chance to silence your targets for $63529d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskA_2': 1048640, 'EffectSpellClassMaskB_1': 16384, 'EffectSpellClassMaskB_2': 1048640, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'Name_Lang_Mask': 16712190, 'ProcChance': 66, 'ProcTypeMask': 65792, 'RangeIndex': 1, 'SpellClassSet': 10},
)


shield_of_the_templar_53711 = spell(
    id=53711,
    name='Shield of the Templar',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        None,
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=63529),
    ],
    spell_icon_id=3016,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Reduces all damage taken by $s2% and grants your Avenger's Shield a $h% chance to silence your targets for $63529d.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 16384, 'EffectSpellClassMaskA_2': 1048640, 'EffectSpellClassMaskB_1': 16384, 'EffectSpellClassMaskB_2': 1048640, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 65792, 'RangeIndex': 1, 'SpellClassSet': 10},
)


judgements_of_the_pure_54151 = spell(
    id=54151,
    name='Judgements of the Pure',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DOT),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
    ],
    spell_icon_id=3018,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (8,3): eff1 seal damage / eff2 seal DoT on SEAL_DAMAGE (U+P), eff3 own hits on JUDGEMENT_OWN_HITS (J+Dv); all eight stale mask keys deleted; DBC ProcTypeMask -> 0 and ProcChance 101 (CR4) with remove_spell_proc(-53671)',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Seals, including the Seal power unleashed by your Judgement and Deliverance, by $s1%, and the direct damage of your Judgement and Deliverance by $s3%. Your Judgement and Deliverance increase your melee, ranged and casting speed by $53657s1% for 1 min.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'ProcTypeMask': 0, 'RangeIndex': 1, 'SpellClassSet': 10, 'SpellVisualID_1': 12015, **_mask(1, m.SEAL_DAMAGE), **_mask(2, m.SEAL_DAMAGE), **_mask(3, m.JUDGEMENT_OWN_HITS)},
)


judgements_of_the_pure_54154 = spell(
    id=54154,
    name='Judgements of the Pure',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=54152),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=3018,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Seal and Judgement spells by $s2%, and your Judgement spells increase your casting and melee haste by $54152s1% for $54152d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2149580800, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskB_1': 33555456, 'EffectSpellClassMaskB_2': 541068800, 'EffectSpellClassMaskB_3': 24, 'EffectSpellClassMaskC_1': 41943040, 'EffectSpellClassMaskC_2': 536873984, 'EffectSpellClassMaskC_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 4', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69904, 'RangeIndex': 1, 'SpellClassSet': 10, 'SpellVisualID_1': 12015},
)


judgements_of_the_pure_54155 = spell(
    id=54155,
    name='Judgements of the Pure',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=7, trigger_spell=54153),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108),
        Effect(type=EffectType.APPLY_AURA, base_points=24, implicit_target_a=1, apply_aura=108, misc_value=22),
    ],
    spell_icon_id=3018,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx3': 67108864, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage done by your Seal and Judgement spells by $s2%, and your Judgement spells increase your casting and melee haste by $54153s1% for $54153d.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2149580800, 'EffectSpellClassMaskA_2': 65536, 'EffectSpellClassMaskB_1': 33555456, 'EffectSpellClassMaskB_2': 541068800, 'EffectSpellClassMaskB_3': 24, 'EffectSpellClassMaskC_1': 41943040, 'EffectSpellClassMaskC_2': 536873984, 'EffectSpellClassMaskC_3': 8, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 100, 'ProcTypeMask': 69904, 'RangeIndex': 1, 'SpellClassSet': 10, 'SpellVisualID_1': 12015},
)


sacred_shield_58597 = spell(
    id=58597,
    name='Sacred Shield',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=134283264,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=60.0, potency_kind='absorb', implicit_target_a=21, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=21, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3026,
    notes='pulled from existing data | paladin-rework S1 SHARED B5.11: eff0 converted to sp_potency 60 absorb, learn 60; spell_pal_sacred_shield replaced by spell_pal_sacred_shield_absorb (generated coefficient through Paladin::CalculateAbsorbBonus).',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 60, 'EquippedItemClass': -1, 'SpellVisualID_1': 12581, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': "Each time the target takes damage they gain a Sacred Shield, absorbing {pot1} damage and increasing the paladin's chance to critically hit with Flash of Light by $s2% for up to $d. They cannot gain this effect more than once every 6 sec.  Lasts $d.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Absorbs damage and increases the casting paladin's chance to critically hit with Flash of Light by $s2%.", 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'SpellClassMask_2': 524288, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


forbearance_25771 = spell(
    id=25771,
    name='Forbearance',
    school=School.HOLY,
    mechanic=25,
    attributes=603979776,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=25, apply_aura=AuraType.MECHANIC_IMMUNITY, misc_value=25),
    ],
    spell_icon_id=236,
    notes='pulled from existing data | paladin-rework S1 SHARED Part C C2.1: Forbearance no longer mentions Divine Protection.',
    raw_overrides={'AttributesEx': 196744, 'AttributesEx2': 4, 'AttributesEx5': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Once protected, the target cannot be protected by Divine Shield or Hand of Protection again for $25771d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Cannot be protected by Divine Shield or Hand of Protection.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'SpellClassMask_3': 128, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


vengeance_20049 = spell(
    id=20049,
    name='Vengeance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=20050),
    ],
    spell_icon_id=84,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (5,2): description only.',
    raw_overrides={'AttributesEx3': 67633152, 'CastingTimeIndex': 1, 'ProcTypeMask': 69972, 'ProcChance': 100, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes increase your Holy damage and the damage of your Crusader Strike and Divine Storm by $20050s1% for $20050d. Stacks up to $20050u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


vengeance_20056 = spell(
    id=20056,
    name='Vengeance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=20052),
    ],
    spell_icon_id=84,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (5,2): description only.',
    raw_overrides={'AttributesEx3': 67633152, 'CastingTimeIndex': 1, 'ProcTypeMask': 69972, 'ProcChance': 100, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes increase your Holy damage and the damage of your Crusader Strike and Divine Storm by $20052s1% for $20052d. Stacks up to $20052u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


vengeance_20057 = spell(
    id=20057,
    name='Vengeance',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=20053),
    ],
    spell_icon_id=84,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (5,2): description only.',
    raw_overrides={'AttributesEx3': 67633152, 'CastingTimeIndex': 1, 'ProcTypeMask': 69972, 'ProcChance': 100, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your critical strikes increase your Holy damage and the damage of your Crusader Strike and Divine Storm by $20053s1% for $20053d. Stacks up to $20053u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


two_handed_weapon_specialization_20111 = spell(
    id=20111,
    name='Two-Handed Weapon Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_WEAPON_CRIT_PERCENT),
    ],
    spell_icon_id=1635,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (5,1): eff0 bp 1/3/5 -> 0/1/2, new eff1 MOD_WEAPON_CRIT_PERCENT 0/1/2; the two-hander requirement (EquippedItem*) gates both.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 354, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the physical damage you deal and your melee critical strike chance by $s1% while wielding a two-handed weapon.\n\n|cFF9D9D9DCapstone Bonus: Your Crusader Strike and Divine Storm deal 2% more damage for each seal stack you hold.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StanceBarOrder': 4294967295, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


two_handed_weapon_specialization_20112 = spell(
    id=20112,
    name='Two-Handed Weapon Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_WEAPON_CRIT_PERCENT),
    ],
    spell_icon_id=1635,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (5,1): eff0 bp 1/3/5 -> 0/1/2, new eff1 MOD_WEAPON_CRIT_PERCENT 0/1/2; the two-hander requirement (EquippedItem*) gates both.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 354, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the physical damage you deal and your melee critical strike chance by $s1% while wielding a two-handed weapon.\n\n|cFF9D9D9DCapstone Bonus: Your Crusader Strike and Divine Storm deal 2% more damage for each seal stack you hold.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StanceBarOrder': 4294967295, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


two_handed_weapon_specialization_20113 = spell(
    id=20113,
    name='Two-Handed Weapon Specialization',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_WEAPON_CRIT_PERCENT),
    ],
    spell_icon_id=1635,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (5,1): eff0 bp 1/3/5 -> 0/1/2, new eff1 MOD_WEAPON_CRIT_PERCENT 0/1/2; the two-hander requirement (EquippedItem*) gates both.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': 2, 'EquippedItemSubclass': 354, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the physical damage you deal and your melee critical strike chance by $s1% while wielding a two-handed weapon.\n\nCapstone Bonus: Your Crusader Strike and Divine Storm deal 2% more damage for each seal stack you hold.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'StanceBarOrder': 4294967295, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


conviction_20117 = spell(
    id=20117,
    name='Conviction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
        None,
    ],
    spell_icon_id=204,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (2,0): eff0 aura 52 -> MOD_CRIT_PCT (290); eff1 stripped on r1/r2, DUMMY proc carrier on r3 (trigger 0, misc 0; spell_pal_conviction prevents).',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to get a critical strike with all spells and attacks by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Critical strikes from your Crusader Strike, Hammer of Wrath, Exorcism and Divine Storm grant 2 seal stacks instead of 1. Divine Storm counts a critical strike on any target.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


conviction_20118 = spell(
    id=20118,
    name='Conviction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
        None,
    ],
    spell_icon_id=204,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (2,0): eff0 aura 52 -> MOD_CRIT_PCT (290); eff1 stripped on r1/r2, DUMMY proc carrier on r3 (trigger 0, misc 0; spell_pal_conviction prevents).',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to get a critical strike with all spells and attacks by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Critical strikes from your Crusader Strike, Hammer of Wrath, Exorcism and Divine Storm grant 2 seal stacks instead of 1. Divine Storm counts a critical strike on any target.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


conviction_20119 = spell(
    id=20119,
    name='Conviction',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=204,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (2,0): eff0 aura 52 -> MOD_CRIT_PCT (290); eff1 stripped on r1/r2, DUMMY proc carrier on r3 (trigger 0, misc 0; spell_pal_conviction prevents).',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your chance to get a critical strike with all spells and attacks by $s1%.\n\nCapstone Bonus: Critical strikes from your Crusader Strike, Hammer of Wrath, Exorcism and Divine Storm grant 2 seal stacks instead of 1. Divine Storm counts a critical strike on any target.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


eye_for_an_eye_9799 = spell(
    id=9799,
    name='Eye for an Eye',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 21),
    ],
    spell_icon_id=1820,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (3,3): eff0 DUMMY -> MOD_CUSTOM_STAT_PCT misc 1<<21 (Versatility); the proc row -9799 is rekeyed below.',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'CastingTimeIndex': 1, 'ProcTypeMask': 664232, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Versatility by $s1%.\n\n|cFF9D9D9DCapstone Bonus: When damage brings you below 50% health, you take 20% less damage and your Strength is increased by 10% for 10 sec. This effect cannot occur more than once every 60 sec.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


eye_for_an_eye_25988 = spell(
    id=25988,
    name='Eye for an Eye',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 21),
    ],
    spell_icon_id=1820,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (3,3): eff0 DUMMY -> MOD_CUSTOM_STAT_PCT misc 1<<21 (Versatility); the proc row -9799 is rekeyed below.',
    raw_overrides={'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'CastingTimeIndex': 1, 'ProcTypeMask': 664232, 'ProcChance': 100, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Versatility by $s1%.\n\n|cFF9D9D9DCapstone Bonus: When damage brings you below 50% health, you take 20% less damage and your Strength is increased by 10% for 10 sec. This effect cannot occur more than once every 60 sec.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


vindication_9452 = spell(
    id=9452,
    name='Vindication',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201420),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201421),
    ],
    spell_icon_id=1798,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (3,1): eff0 now triggers the hit 201420, new eff1 triggers the Mastery buff 201421; DBC ProcChance 5/10/15, ProcTypeMask 0x14.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 20, 'ProcChance': 5, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a $h% chance to deal ' + pot_text(vindication_strike_201420) + ' Holy damage to the target and increase your Mastery by 3% for 10 sec. This effect cannot occur more than once every 4 sec.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


vindication_26016 = spell(
    id=26016,
    name='Vindication',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201420),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201421),
    ],
    spell_icon_id=1798,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (3,1): eff0 now triggers the hit 201420, new eff1 triggers the Mastery buff 201421; DBC ProcChance 5/10/15, ProcTypeMask 0x14.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 20, 'ProcChance': 10, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a $h% chance to deal ' + pot_text(vindication_strike_201420) + ' Holy damage to the target and increase your Mastery by 3% for 10 sec. This effect cannot occur more than once every 4 sec.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


pursuit_of_justice_26022 = spell(
    id=26022,
    name='Pursuit of Justice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=6, implicit_target_a=1, apply_aura=AuraType.MOD_MOUNTED_SPEED_NOT_STACK),
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        None,
    ],
    spell_icon_id=1797,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (2,3): eff0 aura 31 -> MOD_MOUNTED_SPEED_NOT_STACK (172), eff1 DUMMY 10/20 (read by spell_pal_pursuit_of_justice_seal), disarm eff2 removed.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your mounted speed by $s1%, and your movement speed by $s2% while Seal of Justice is active. Does not stack with other movement speed increasing effects.\n\n|cFF9D9D9DCapstone Bonus: Your Hand of Freedom also removes all stun effects from the target and increases its movement speed by 30% for its duration.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


pursuit_of_justice_26023 = spell(
    id=26023,
    name='Pursuit of Justice',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.MOD_MOUNTED_SPEED_NOT_STACK),
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.DUMMY),
        None,
    ],
    spell_icon_id=1797,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (2,3): eff0 aura 31 -> MOD_MOUNTED_SPEED_NOT_STACK (172), eff1 DUMMY 10/20 (read by spell_pal_pursuit_of_justice_seal), disarm eff2 removed.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your mounted speed by $s1%, and your movement speed by $s2% while Seal of Justice is active. Does not stack with other movement speed increasing effects.\n\nCapstone Bonus: Your Hand of Freedom also removes all stun effects from the target and increases its movement speed by 30% for its duration.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


smite_evil_31866 = spell(
    id=31866,
    name='Smite Evil',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE_VERSUS, misc_value=108),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=203,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (1,2): stock Crusade rank spells renamed Smite Evil, icon 2171 -> 203, effects unchanged.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s2%, and all damage you deal to Humanoids, Demons, Undead and Elementals by an additional $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


smite_evil_31867 = spell(
    id=31867,
    name='Smite Evil',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE_VERSUS, misc_value=108),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=203,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (1,2): stock Crusade rank spells renamed Smite Evil, icon 2171 -> 203, effects unchanged.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s2%, and all damage you deal to Humanoids, Demons, Undead and Elementals by an additional $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


smite_evil_31868 = spell(
    id=31868,
    name='Smite Evil',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE_VERSUS, misc_value=108),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
    ],
    spell_icon_id=203,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (1,2): stock Crusade rank spells renamed Smite Evil, icon 2171 -> 203, effects unchanged.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s2%, and all damage you deal to Humanoids, Demons, Undead and Elementals by an additional $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


divine_purpose_31871 = spell(
    id=31871,
    name='Divine Purpose',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=16, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=3),
        None,
    ],
    spell_icon_id=2170,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (5,3): eff0 -> ADD_FLAT COOLDOWN on Divine Shield, eff1 -> ADD_FLAT EFFECT1 (damage penalty), old HoF-stun eff2 -> None; SpellClassSet 0 -> 10 (a family-0 SpellMod matches every spell); ProcTypeMask 0 so SpellMgr builds no replacement for the removed -31871 row.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Divine Shield by 30 sec and its damage penalty to 33%.\n\n|cFF9D9D9DCapstone Bonus: Damage that would kill you casts Divine Shield on you instead, if you know it, it is not on cooldown and you are not affected by Forbearance.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectSpellClassMaskA_3': m.DIVINE_SHIELD, 'EffectSpellClassMaskB_3': m.DIVINE_SHIELD, 'SpellClassSet': 10, 'ProcTypeMask': 0},
)


divine_purpose_31872 = spell(
    id=31872,
    name='Divine Purpose',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-60001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=32, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=3),
        None,
    ],
    spell_icon_id=2170,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §5 (5,3): eff0 -> ADD_FLAT COOLDOWN on Divine Shield, eff1 -> ADD_FLAT EFFECT1 (damage penalty), old HoF-stun eff2 -> None; SpellClassSet 0 -> 10 (a family-0 SpellMod matches every spell); ProcTypeMask 0 so SpellMgr builds no replacement for the removed -31871 row.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Divine Shield by 1 min and its damage penalty to 17%.\n\n|cFF9D9D9DCapstone Bonus: Damage that would kill you casts Divine Shield on you instead, if you know it, it is not on cooldown and you are not affected by Forbearance.|r', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectSpellClassMaskA_3': m.DIVINE_SHIELD, 'EffectSpellClassMaskB_3': m.DIVINE_SHIELD, 'SpellClassSet': 10, 'ProcTypeMask': 0},
)


vengeance_20050 = spell(
    id=20050,
    name='Vengeance',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=84,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §4.8: duration 30 -> 15 s, eff0 aura 79 misc 3 -> 2 (Holy only), new eff1 ADD_PCT DAMAGE on Crusader Strike / Divine Storm.',
    raw_overrides={'AttributesEx4': 64, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'SpellVisualID_1': 6597, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Increases your Holy damage and the damage of your Crusader Strike and Divine Storm by $s1% for $d. Stacks up to $u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Holy damage and the damage of your Crusader Strike and Divine Storm increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'SpellClassMask_2': 2147500032, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectSpellClassMaskB_2': m.VENGEANCE_STRIKES[1]},
)


vengeance_20052 = spell(
    id=20052,
    name='Vengeance',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=84,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §4.8: duration 30 -> 15 s, eff0 aura 79 misc 3 -> 2 (Holy only), new eff1 ADD_PCT DAMAGE on Crusader Strike / Divine Storm.',
    raw_overrides={'AttributesEx4': 64, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'SpellVisualID_1': 6597, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Increases your Holy damage and the damage of your Crusader Strike and Divine Storm by $s1% for $d. Stacks up to $u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Holy damage and the damage of your Crusader Strike and Divine Storm increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'SpellClassMask_2': 2147500032, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectSpellClassMaskB_2': m.VENGEANCE_STRIKES[1]},
)


vengeance_20053 = spell(
    id=20053,
    name='Vengeance',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=84,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §4.8: duration 30 -> 15 s, eff0 aura 79 misc 3 -> 2 (Holy only), new eff1 ADD_PCT DAMAGE on Crusader Strike / Divine Storm.',
    raw_overrides={'AttributesEx4': 64, 'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'CumulativeAura': 3, 'EquippedItemClass': -1, 'SpellVisualID_1': 6597, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Increases your Holy damage and the damage of your Crusader Strike and Divine Storm by $s1% for $d. Stacks up to $u times.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Holy damage and the damage of your Crusader Strike and Divine Storm increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'SpellClassMask_2': 2147500032, 'PreventionType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectSpellClassMaskB_2': m.VENGEANCE_STRIKES[1]},
)


the_art_of_war_59578 = spell(
    id=59578,
    name='The Art of War',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=10),
    ],
    spell_icon_id=3034,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §4.8: duration 15 -> 20 s; description and subtext no longer quote the old rank-2 damage text.',
    raw_overrides={'AttributesEx4': 576, 'AttributesEx6': 64, 'CastingTimeIndex': 1, 'ProcTypeMask': 81920, 'ProcChance': 100, 'ProcCharges': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectSpellClassMaskA_1': 1073741824, 'EffectSpellClassMaskA_2': 2, 'SpellVisualID_1': 11955, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your next Flash of Light or Exorcism is instant cast.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Flash of Light or Exorcism spell is instant cast.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'SpellClassMask_3': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


righteous_vengeance_61840 = spell(
    id=61840,
    name='Righteous Vengeance',
    school=School.HOLY,
    dispel=DispelType.MAGIC,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000, potency_excluded="percent of crit damage (B15 rollover)"),
    ],
    spell_icon_id=3025,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §4.8/§0.2 item 5: AttributesEx3 |= SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (the rollover amount is already a percent of a fully modified crit).',
    raw_overrides={'AttributesEx2': 4, 'AttributesEx3': 537133056, 'AttributesEx4': 9437440, 'AttributesEx6': 536870912, 'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 5652, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Your critical strikes cause the opponent to take holy damage.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taking holy damage.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'SpellClassMask_1': 536870912, 'DefenseType': 2, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)


heart_of_the_crusader_54498 = spell(
    id=54498,
    name='Heart of the Crusader',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=6, apply_aura=AuraType.MOD_ATTACKER_SPELL_AND_WEAPON_CRIT_CHANCE),
    ],
    spell_icon_id=237,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §4.8: debuff duration 20 s -> 15 s.',
    raw_overrides={'AttributesEx2': 268435460, 'AttributesEx3': 262656, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'In addition to the normal effect, your Judgement and Deliverance will also increase the critical strike chance of all attacks made against that target by an additional $20336s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases chance of critical strikes against the target by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'SpellClassMask_1': 536870912, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


heart_of_the_crusader_54499 = spell(
    id=54499,
    name='Heart of the Crusader',
    school=School.HOLY,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=6, apply_aura=AuraType.MOD_ATTACKER_SPELL_AND_WEAPON_CRIT_CHANCE),
    ],
    spell_icon_id=237,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §4.8: debuff duration 20 s -> 15 s.',
    raw_overrides={'AttributesEx2': 268435460, 'AttributesEx3': 262656, 'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 1, 'SpellLevel': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'In addition to the normal effect, your Judgement and Deliverance will also increase the critical strike chance of all attacks made against that target by an additional $20337s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases chance of critical strikes against the target by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'SpellClassMask_1': 536870912, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


judgements_of_the_wise_31930 = spell(
    id=31930,
    name='Judgements of the Wise',
    school=School.HOLY,
    attributes=537133056,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=14, implicit_target_a=1),
    ],
    spell_icon_id=3017,
    notes='pulled from existing data | paladin-rework S1 RETRIBUTION §4.8: eff0 ENERGIZE 24 -> 14 (15% of base mana, the % is hardcoded by id, C28).',
    raw_overrides={'AttributesEx2': 536870916, 'CastingTimeIndex': 1, 'SpellLevel': 1, 'DurationIndex': 0, 'EquippedItemClass': -1, 'SpellVisualID_1': 11906, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'Description_Lang_enUS': 'Gain $s1% of your base mana.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)

# ---------------------------------------------------------------------------
# paladin-rework S1 RETRIBUTION - new talent rank spells (RETRIBUTION §2.1 / §5). Every rank is a hidden passive
# (attributes 464, duration -1, target 1, SpellClassSet 10 so an aura-107/108 carrier never leaks into other families).
# paladin_talents.py imports these by variable name.
# ---------------------------------------------------------------------------

zeal_201440 = spell(
    id=201440, name='Zeal', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 20),
    ],
    spell_icon_id=2268,
    notes='paladin-rework S1 RETRIBUTION §5 (0,0): +1/2/3% Mastery (aura 306, misc 1<<20).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Mastery by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'ProcChance': 101},
)


zeal_201441 = spell(
    id=201441, name='Zeal', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 20),
    ],
    spell_icon_id=2268,
    notes='paladin-rework S1 RETRIBUTION §5 (0,0): +1/2/3% Mastery (aura 306, misc 1<<20).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Mastery by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'ProcChance': 101},
)


zeal_201442 = spell(
    id=201442, name='Zeal', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 20),
    ],
    spell_icon_id=2268,
    notes='paladin-rework S1 RETRIBUTION §5 (0,0): +1/2/3% Mastery (aura 306, misc 1<<20).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Mastery by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 101},
)


divine_might_201443 = spell(
    id=201443, name='Divine Might', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=0),
    ],
    spell_icon_id=239,
    notes='paladin-rework S1 RETRIBUTION §5 (0,1): +1/2/3% Strength.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Strength by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'ProcChance': 101},
)


divine_might_201444 = spell(
    id=201444, name='Divine Might', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=0),
    ],
    spell_icon_id=239,
    notes='paladin-rework S1 RETRIBUTION §5 (0,1): +1/2/3% Strength.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Strength by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'ProcChance': 101},
)


divine_might_201445 = spell(
    id=201445, name='Divine Might', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=0),
    ],
    spell_icon_id=239,
    notes='paladin-rework S1 RETRIBUTION §5 (0,1): +1/2/3% Strength.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Strength by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 101},
)


strength_of_faith_201446 = spell(
    id=201446, name='Strength of Faith', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
    ],
    spell_icon_id=2844,
    notes='paladin-rework S1 RETRIBUTION §5 (0,2): +1/2/3% all damage (aura 79) and +1/2/3% crit on RET_HOLY_DAMAGE (eff1).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and the critical strike chance of your Holy spells and abilities by $s2%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'ProcChance': 101, 'EffectSpellClassMaskB_1': m.RET_HOLY_DAMAGE[0], 'EffectSpellClassMaskB_2': m.RET_HOLY_DAMAGE[1], 'EffectSpellClassMaskB_3': m.RET_HOLY_DAMAGE[2]},
)


strength_of_faith_201447 = spell(
    id=201447, name='Strength of Faith', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
    ],
    spell_icon_id=2844,
    notes='paladin-rework S1 RETRIBUTION §5 (0,2): +1/2/3% all damage (aura 79) and +1/2/3% crit on RET_HOLY_DAMAGE (eff1).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and the critical strike chance of your Holy spells and abilities by $s2%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'ProcChance': 101, 'EffectSpellClassMaskB_1': m.RET_HOLY_DAMAGE[0], 'EffectSpellClassMaskB_2': m.RET_HOLY_DAMAGE[1], 'EffectSpellClassMaskB_3': m.RET_HOLY_DAMAGE[2]},
)


strength_of_faith_201448 = spell(
    id=201448, name='Strength of Faith', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=7),
    ],
    spell_icon_id=2844,
    notes='paladin-rework S1 RETRIBUTION §5 (0,2): +1/2/3% all damage (aura 79) and +1/2/3% crit on RET_HOLY_DAMAGE (eff1).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases all damage you deal by $s1% and the critical strike chance of your Holy spells and abilities by $s2%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 101, 'EffectSpellClassMaskB_1': m.RET_HOLY_DAMAGE[0], 'EffectSpellClassMaskB_2': m.RET_HOLY_DAMAGE[1], 'EffectSpellClassMaskB_3': m.RET_HOLY_DAMAGE[2]},
)


improved_crusader_strike_201449 = spell(
    id=201449, name='Improved Crusader Strike', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=2309,
    notes='paladin-rework S1 RETRIBUTION §5 (1,1): +5/10% Crusader Strike damage.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Crusader Strike by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'ProcChance': 101, 'EffectSpellClassMaskA_2': m.CRUSADER_STRIKE},
)


improved_crusader_strike_201450 = spell(
    id=201450, name='Improved Crusader Strike', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=2309,
    notes='paladin-rework S1 RETRIBUTION §5 (1,1): +5/10% Crusader Strike damage.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Crusader Strike by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'ProcChance': 101, 'EffectSpellClassMaskA_2': m.CRUSADER_STRIKE},
)


purify_the_unclean_201451 = spell(
    id=201451, name='Purify the Unclean', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=300,
    notes='paladin-rework S1 RETRIBUTION §5 (3,0): +3/6/9% damage (PURIFY_DAMAGE) and DoT (PURIFY_DOT: Consecration snapshots through SPELLMOD_DOT).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Seal of Command, Divine Storm, Consecration, Holy Wrath, Deliverance and Wake of Ashes by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'ProcChance': 101, 'EffectSpellClassMaskA_1': m.PURIFY_DAMAGE[0], 'EffectSpellClassMaskA_2': m.PURIFY_DAMAGE[1], 'EffectSpellClassMaskA_3': m.PURIFY_DAMAGE[2], 'EffectSpellClassMaskB_1': m.PURIFY_DOT[0]},
)


purify_the_unclean_201452 = spell(
    id=201452, name='Purify the Unclean', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=300,
    notes='paladin-rework S1 RETRIBUTION §5 (3,0): +3/6/9% damage (PURIFY_DAMAGE) and DoT (PURIFY_DOT: Consecration snapshots through SPELLMOD_DOT).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Seal of Command, Divine Storm, Consecration, Holy Wrath, Deliverance and Wake of Ashes by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'ProcChance': 101, 'EffectSpellClassMaskA_1': m.PURIFY_DAMAGE[0], 'EffectSpellClassMaskA_2': m.PURIFY_DAMAGE[1], 'EffectSpellClassMaskA_3': m.PURIFY_DAMAGE[2], 'EffectSpellClassMaskB_1': m.PURIFY_DOT[0]},
)


purify_the_unclean_201453 = spell(
    id=201453, name='Purify the Unclean', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=300,
    notes='paladin-rework S1 RETRIBUTION §5 (3,0): +3/6/9% damage (PURIFY_DAMAGE) and DoT (PURIFY_DOT: Consecration snapshots through SPELLMOD_DOT).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Seal of Command, Divine Storm, Consecration, Holy Wrath, Deliverance and Wake of Ashes by $s1%.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 101, 'EffectSpellClassMaskA_1': m.PURIFY_DAMAGE[0], 'EffectSpellClassMaskA_2': m.PURIFY_DAMAGE[1], 'EffectSpellClassMaskA_3': m.PURIFY_DAMAGE[2], 'EffectSpellClassMaskB_1': m.PURIFY_DOT[0]},
)


sanctified_seals_201454 = spell(
    id=201454, name='Sanctified Seals', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=90213,
    notes='paladin-rework S1 RETRIBUTION §5 (5,0): DUMMY 2/4/6%, read by Paladin::GetSanctifiedSealsPct (unleash-only scaler); ProcTypeMask 0 so no proc row is built.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage, healing and other effects your Judgement and Deliverance release from a Primed seal by $s1%.\n\n|cFF9D9D9DCapstone Bonus: This bonus is increased by your Mastery, and your Seal of Light's Holy damage bonus gains an additional 6.25% of your Mastery per seal stack.|r", 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'ProcChance': 101, 'ProcTypeMask': 0},
)


sanctified_seals_201455 = spell(
    id=201455, name='Sanctified Seals', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=90213,
    notes='paladin-rework S1 RETRIBUTION §5 (5,0): DUMMY 2/4/6%, read by Paladin::GetSanctifiedSealsPct (unleash-only scaler); ProcTypeMask 0 so no proc row is built.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage, healing and other effects your Judgement and Deliverance release from a Primed seal by $s1%.\n\n|cFF9D9D9DCapstone Bonus: This bonus is increased by your Mastery, and your Seal of Light's Holy damage bonus gains an additional 6.25% of your Mastery per seal stack.|r", 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'ProcChance': 101, 'ProcTypeMask': 0},
)


sanctified_seals_201456 = spell(
    id=201456, name='Sanctified Seals', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=90213,
    notes='paladin-rework S1 RETRIBUTION §5 (5,0): DUMMY 2/4/6%, read by Paladin::GetSanctifiedSealsPct (unleash-only scaler); ProcTypeMask 0 so no proc row is built.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage, healing and other effects your Judgement and Deliverance release from a Primed seal by $s1%.\n\nCapstone Bonus: This bonus is increased by your Mastery, and your Seal of Light's Holy damage bonus gains an additional 6.25% of your Mastery per seal stack.", 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 101, 'ProcTypeMask': 0},
)


blade_of_wrath_201457 = spell(
    id=201457, name='Blade of Wrath', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=90214,
    notes='paladin-rework S1 RETRIBUTION §5 (6,3): +5/10/15% Blade of Justice damage; rank 3 adds eff1 PROC_TRIGGER -> the party Mastery buff 201429 (CAST-phase row 201459).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Blade of Justice by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Blade of Justice increases the Mastery of you and your party members within 30 yards by 2% for 10 sec.|r', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'ProcChance': 101, 'EffectSpellClassMaskA_3': m.BLADE_OF_JUSTICE},
)


blade_of_wrath_201458 = spell(
    id=201458, name='Blade of Wrath', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
    ],
    spell_icon_id=90214,
    notes='paladin-rework S1 RETRIBUTION §5 (6,3): +5/10/15% Blade of Justice damage; rank 3 adds eff1 PROC_TRIGGER -> the party Mastery buff 201429 (CAST-phase row 201459).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Blade of Justice by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Your Blade of Justice increases the Mastery of you and your party members within 30 yards by 2% for 10 sec.|r', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'ProcChance': 101, 'EffectSpellClassMaskA_3': m.BLADE_OF_JUSTICE},
)


blade_of_wrath_201459 = spell(
    id=201459, name='Blade of Wrath', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=0),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201429),
    ],
    spell_icon_id=90214,
    notes='paladin-rework S1 RETRIBUTION §5 (6,3): +5/10/15% Blade of Justice damage; rank 3 adds eff1 PROC_TRIGGER -> the party Mastery buff 201429 (CAST-phase row 201459).',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Blade of Justice by $s1%.\n\nCapstone Bonus: Your Blade of Justice increases the Mastery of you and your party members within 30 yards by 2% for 10 sec.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 101, 'EffectSpellClassMaskA_3': m.BLADE_OF_JUSTICE},
)


crusaders_aegis_201460 = spell(
    id=201460, name="Crusader's Aegis", school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=3),
    ],
    spell_icon_id=2820,
    notes="paladin-rework S1 RETRIBUTION §5 (8,3): +3/6/10 on Avenging Wrath's +20% (EFFECT1); rank 3 adds eff1 PROC_TRIGGER -> the party absorb 201430 (CAST-phase row 201462).",
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage bonus of your Avenging Wrath by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Casting Avenging Wrath shields you and your party members within 30 yards, absorbing ' + pot_text(crusaders_aegis_shield_201430) + ' damage for 10 sec.|r', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'ProcChance': 101, 'EffectSpellClassMaskA_2': m.AVENGING_WRATH},
)


crusaders_aegis_201461 = spell(
    id=201461, name="Crusader's Aegis", school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=3),
    ],
    spell_icon_id=2820,
    notes="paladin-rework S1 RETRIBUTION §5 (8,3): +3/6/10 on Avenging Wrath's +20% (EFFECT1); rank 3 adds eff1 PROC_TRIGGER -> the party absorb 201430 (CAST-phase row 201462).",
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage bonus of your Avenging Wrath by $s1%.\n\n|cFF9D9D9DCapstone Bonus: Casting Avenging Wrath shields you and your party members within 30 yards, absorbing ' + pot_text(crusaders_aegis_shield_201430) + ' damage for 10 sec.|r', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'ProcChance': 101, 'EffectSpellClassMaskA_2': m.AVENGING_WRATH},
)


crusaders_aegis_201462 = spell(
    id=201462, name="Crusader's Aegis", school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201430),
    ],
    spell_icon_id=2820,
    notes="paladin-rework S1 RETRIBUTION §5 (8,3): +3/6/10 on Avenging Wrath's +20% (EFFECT1); rank 3 adds eff1 PROC_TRIGGER -> the party absorb 201430 (CAST-phase row 201462).",
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage bonus of your Avenging Wrath by $s1%.\n\nCapstone Bonus: Casting Avenging Wrath shields you and your party members within 30 yards, absorbing ' + pot_text(crusaders_aegis_shield_201430) + ' damage for 10 sec.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 101, 'EffectSpellClassMaskA_2': m.AVENGING_WRATH},
)


crusade_201463 = spell(
    id=201463, name='Crusade', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=11),
    ],
    spell_icon_id=2171,
    notes='paladin-rework S1 RETRIBUTION §5 (9,0): -10/-20/-30 s Avenging Wrath cooldown; rank 3 (201465) is read by id for the ramp and Radiant Glory.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Avenging Wrath by $/1000;s1 sec.\n\n|cFF9D9D9DCapstone Bonus: Each seal stack you gain while Avenging Wrath is active increases your damage by 2%, up to 15%, until it ends. Wake of Ashes activates Avenging Wrath for 6 sec, or extends an active one by 6 sec.|r', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'ProcChance': 101, 'EffectSpellClassMaskA_2': m.AVENGING_WRATH},
)


crusade_201464 = spell(
    id=201464, name='Crusade', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-20001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=11),
    ],
    spell_icon_id=2171,
    notes='paladin-rework S1 RETRIBUTION §5 (9,0): -10/-20/-30 s Avenging Wrath cooldown; rank 3 (201465) is read by id for the ramp and Radiant Glory.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Avenging Wrath by $/1000;s1 sec.\n\n|cFF9D9D9DCapstone Bonus: Each seal stack you gain while Avenging Wrath is active increases your damage by 2%, up to 15%, until it ends. Wake of Ashes activates Avenging Wrath for 6 sec, or extends an active one by 6 sec.|r', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'ProcChance': 101, 'EffectSpellClassMaskA_2': m.AVENGING_WRATH},
)


crusade_201465 = spell(
    id=201465, name='Crusade', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-30001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=11),
    ],
    spell_icon_id=2171,
    notes='paladin-rework S1 RETRIBUTION §5 (9,0): -10/-20/-30 s Avenging Wrath cooldown; rank 3 (201465) is read by id for the ramp and Radiant Glory.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Avenging Wrath by $/1000;s1 sec.\n\nCapstone Bonus: Each seal stack you gain while Avenging Wrath is active increases your damage by 2%, up to 15%, until it ends. Wake of Ashes activates Avenging Wrath for 6 sec, or extends an active one by 6 sec.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 101, 'EffectSpellClassMaskA_2': m.AVENGING_WRATH},
)


vindication_201466 = spell(
    id=201466, name='Vindication', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201420),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201421),
    ],
    spell_icon_id=1798,
    notes='paladin-rework S1 RETRIBUTION §5 (3,1): new rank 3 (clone of 26016): 15% chance.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Your melee attacks have a $h% chance to deal ' + pot_text(vindication_strike_201420) + ' Holy damage to the target and increase your Mastery by 3% for 10 sec. This effect cannot occur more than once every 4 sec.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 15, 'ProcTypeMask': 20},
)


eye_for_an_eye_201467 = spell(
    id=201467, name='Eye for an Eye', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT, misc_value=1 << 21),
    ],
    spell_icon_id=1820,
    notes='paladin-rework S1 RETRIBUTION §5 (3,3): new rank 3 (clone of 25988): +3% Versatility; the capstone is gated by rank 3 in spell_pal_eye_for_an_eye_ret.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your Versatility by $s1%.\n\nCapstone Bonus: When damage brings you below 50% health, you take 20% less damage and your Strength is increased by 10% for 10 sec. This effect cannot occur more than once every 60 sec.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 100, 'AttributesEx3': 67108864, 'AttributesEx4': 524288, 'ProcTypeMask': 664232},
)


improved_judgements_201468 = spell(
    id=201468, name='Improved Judgements', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=205,
    notes='paladin-rework S1 RETRIBUTION §5 (4,0): new rank 3 (clone of 25957): +9% Judgement/Deliverance damage; the capstone is Paladin::OnJudgementCastRet.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the damage of your Judgement and Deliverance by $s1%, and your Exorcism triggers your active seal's effect.\n\nCapstone Bonus: When your Judgement or Deliverance releases a Primed seal, your next ability that grants seal stacks grants 1 additional stack.", 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 101, 'EffectSpellClassMaskA_1': m.JUDGEMENT_ALL[0], 'EffectSpellClassMaskA_3': m.JUDGEMENT_ALL[2], 'EffectSpellClassMaskB_1': m.UNLEASH},
)


swift_retribution_aura_201165 = spell(
    id=201165, name='Swift Retribution', school=School.HOLY, attributes=151322880,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=0.0, duration_ms=-1,
    effects=[
        None,
        None,
        Effect(type=EffectType.APPLY_AREA_AURA_RAID, base_points=-1, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, radius_yards=40.0),
    ],
    spell_icon_id=3028,
    notes='paladin-rework follow-up: the haste half of the old shared 63531, split out so Swift Retribution shows its own aura on the target (63531 is Sanctified Retribution only). Clone of 63531 (hidden attribute 0x80 cleared): haste on effect INDEX 2 so the talent\'s SPELLMOD_EFFECT3 mod (misc 23) finds it, family d2 0x8000000 (LOADTIME_SANCTIFIED_RETRIBUTION) written as data instead of the SpellInfoCorrections fix 63531 needs. Applied by spell_pal_swift_retribution; target filter is spell_pal_sanctified_retribution_effect.',
    raw_overrides={'AttributesEx2': 17, 'AttributesEx3': 1114112, 'AttributesEx4': 2097152, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Haste increased by the paladin's Swift Retribution. Does not stack with the same effect from other paladins.", 'BaseLevel': 1, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Haste increased by the paladin's Swift Retribution. Does not stack with the same effect from other paladins.", 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 10, 'SpellClassMask_3': m.LOADTIME_SANCTIFIED_RETRIBUTION, 'SpellLevel': 1},
)
scripted_by(swift_retribution_aura_201165, 'spell_pal_sanctified_retribution_effect')
# Stock group 1053 {63531} is nested in both 1054 (Haste Buffs) and 1056 (Damage Done Buffs) because 63531 used to carry
# both effects. Now 63531 is damage only (stays in 1056 through 1053) and 201165 is haste only (1054 directly), so the
# two talents' auras apply together and each only competes with its own kind of raid buff.
leave_spell_group(1054, -1053)
spell_group(1054, swift_retribution_aura_201165)


sanctified_retribution_201469 = spell(
    id=201469, name='Sanctified Retribution', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=3),
    ],
    spell_icon_id=502,
    notes='paladin-rework S1 RETRIBUTION §5 (4,3): new rank 2 (clone of 31869): +2% party damage via 63531 (authored on d2 0x8000000), +100% Retribution Aura damage.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Retribution Aura by $s2%, and all damage dealt by friendly targets affected by any of your auras by $s1%. Does not stack with other similar effects.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 2', 'ProcChance': 101, 'EffectSpellClassMaskA_3': m.LOADTIME_SANCTIFIED_RETRIBUTION, 'EffectSpellClassMaskB_1': m.RETRIBUTION_AURA},
)


sanctified_retribution_201470 = spell(
    id=201470, name='Sanctified Retribution', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=12),
        Effect(type=EffectType.APPLY_AURA, base_points=149, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=3),
    ],
    spell_icon_id=502,
    notes='paladin-rework S1 RETRIBUTION §5 (4,3): new rank 3 (clone of 31869): +3% party damage via 63531 (authored on d2 0x8000000), +150% Retribution Aura damage.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Retribution Aura by $s2%, and all damage dealt by friendly targets affected by any of your auras by $s1%. Does not stack with other similar effects.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 101, 'EffectSpellClassMaskA_3': m.LOADTIME_SANCTIFIED_RETRIBUTION, 'EffectSpellClassMaskB_1': m.RETRIBUTION_AURA},
)


divine_purpose_201471 = spell(
    id=201471, name='Divine Purpose', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-90001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=11),
        Effect(type=EffectType.APPLY_AURA, base_points=49, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=127),
    ],
    spell_icon_id=2170,
    notes='paladin-rework S1 RETRIBUTION §5 (5,3): new rank 3 (clone of 31872): -90 s Divine Shield cooldown, no damage penalty, eff2 unlimited SCHOOL_ABSORB (the lethal-save absorb, spell_pal_divine_purpose_ret); SpellClassSet 10, ProcTypeMask 0.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces the cooldown of your Divine Shield by 1.5 min and removes its damage penalty.\n\nCapstone Bonus: Damage that would kill you casts Divine Shield on you instead, if you know it, it is not on cooldown and you are not affected by Forbearance.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 101, 'ProcTypeMask': 0, 'EffectSpellClassMaskA_3': m.DIVINE_SHIELD, 'EffectSpellClassMaskB_3': m.DIVINE_SHIELD},
)


the_art_of_war_201472 = spell(
    id=201472, name='The Art of War', school=School.NORMAL,
    attributes=464,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=59578),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=22),
    ],
    spell_icon_id=3034,
    notes='paladin-rework S1 RETRIBUTION §5 (7,1): new rank 3 (clone of 53488): +9% damage, 30% proc chance, DoT part on AOW_DOT.',
    raw_overrides={'EquippedItemClass': -1, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the damage of your Judgement, Deliverance, Crusader Strike, Execution Sentence and Divine Storm by $s1%. Damage from these and your main-hand auto attacks has a $h% chance to make your next Flash of Light or Exorcism instant within 20 sec; Divine Storm rolls at half the chance on each target hit. This effect cannot occur more than once every 6 sec.', 'AuraDescription_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 3', 'ProcChance': 30, 'ProcTypeMask': 4116, 'EffectSpellClassMaskA_1': m.AOW_DAMAGE[0], 'EffectSpellClassMaskA_2': m.AOW_DAMAGE[1], 'EffectSpellClassMaskA_3': m.AOW_DAMAGE[2], 'EffectSpellClassMaskC_1': m.AOW_DOT[0], 'EffectSpellClassMaskC_3': m.AOW_DOT[2]},
)



# ---------------------------------------------------------------------------
# paladin-rework S1 RETRIBUTION - spell_proc rows (§7), removals, script bindings, links.
# Flags: DONE_MELEE_AUTO 0x4, DONE_SPELL_MELEE 0x10, DONE_SPELL_RANGED 0x100, DONE_SPELL_NONE_NEG 0x1000,
# DONE_SPELL_MAGIC_NEG 0x10000, DONE_SPELL_NONE_POS 0x400, DONE_SPELL_MAGIC_POS 0x4000, TAKEN_DAMAGE 0x100000, KILL 0x2.
# Every row with a spell flag sets a phase (phase 0 never fires). Chance 0 = the rank's DBC ProcChance.
# ---------------------------------------------------------------------------

# Heart of the Crusader: own hits of Judgement / Deliverance, every cast, each Deliverance target. eff1 is the SIC-forced DUMMY with
# TriggerSpell 21183/54498/54499 (the stock handler only prevents EFFECT_0), so it is disabled too (0x6).
procs_on(-20335, proc_flags=0x10 | 0x100 | 0x10000, family_name=10, family_mask=m.JUDGEMENT_CASTS,
         spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, disable_effects_mask=0x6, chance=100)
# Judgements of the Wise: damaging unleash only (U); type 0 so the aura-only Vengeance unleashes count; triggered casts allowed.
procs_on(-31876, proc_flags=0x10 | 0x100 | 0x10000, family_name=10, family_mask=(m.UNLEASH, 0, 0),
         spell_phase_mask=m.PROC_SPELL_PHASE_HIT, attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC, chance=0)
# Righteous Vengeance: per critting hit, per target, no guard.
procs_on(-53380, proc_flags=0x10 | 0x100 | 0x1000 | 0x10000, family_name=10, family_mask=m.RV_PROC,
         spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, hit_mask=m.PROC_HIT_CRITICAL,
         attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC, chance=100)
# The Art of War: own hits + Crusader Strike / Divine Storm / Execution Sentence + main-hand autos, 6 s ICD; eff0/eff2 are SpellMods (0x5).
procs_on(-53486, proc_flags=0x4 | 0x10 | 0x100 | 0x10000, family_name=10, family_mask=m.AOW_PROC,
         spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT,
         attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC, disable_effects_mask=0x5, chance=0, cooldown_ms=6000)
# Vindication: melee attacks, flat 5/10/15% (no PPM), 4 s ICD.
procs_on(-9452, proc_flags=0x4 | 0x10, family_name=0, spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=m.PROC_SPELL_PHASE_HIT, ppm=0.0, chance=0, cooldown_ms=4000)
# Eye for an Eye: damage taken (normal + crit), 60 s ICD; the rank-3 gate lives in spell_pal_eye_for_an_eye_ret.
procs_on(-9799, proc_flags=0x100000, attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC, chance=100, cooldown_ms=60000)
# Conviction capstone (rank 3 only; no Conviction chain row exists): crits of CS / HoW / Exorcism / DS.
procs_on(conviction_20119, proc_flags=0x10 | 0x100 | 0x10000, family_name=10, family_mask=m.CONVICTION_PROC,
         spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, hit_mask=m.PROC_HIT_CRITICAL,
         disable_effects_mask=0x1, chance=100)
# Sanctity of Battle: Exorcism damage, 33/66/100% from the rank's DBC ProcChance; eff0/eff1 are SpellMods (0x3).
procs_on(-32043, proc_flags=0x10000, family_name=10, family_mask=(0, m.EXORCISM, 0), spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=m.PROC_SPELL_PHASE_HIT, disable_effects_mask=0x3, chance=0)
# Swift Retribution: once per Crusader Strike / Judgement cast (CAST phase also fires on a missed cast, accepted: RETRIBUTION §10 Q17).
procs_on(-53379, proc_flags=0x10 | 0x100 | 0x1000 | 0x10000, family_name=10, family_mask=m.SWIFT_RET_PROC,
         spell_phase_mask=m.PROC_SPELL_PHASE_CAST, disable_effects_mask=0x1, chance=100)
# Benediction: kills that yield experience or honor (PROC_ATTR_REQ_EXP_OR_HONOR 0x1), 5 s ICD; eff1 is a DUMMY read by script (0x2).
procs_on(-20101, proc_flags=0x2, attributes_mask=0x1, disable_effects_mask=0x2, chance=100, cooldown_ms=5000)
# Sheath of Light capstone helper 201434: Flash of Light heals (the chain -53501 keeps its stock crit-heal row for the HoT path).
procs_on(sheath_of_light_capstone_201434, proc_flags=0x4000, family_name=10, family_mask=(m.FLASH_OF_LIGHT, 0, 0), spell_type_mask=2,
         spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100, cooldown_ms=10000)
# Blade of Wrath rank 3: every Blade of Justice cast (CAST phase, fires on a missed cast too, accepted).
procs_on(blade_of_wrath_201459, proc_flags=0x10000, family_name=10, family_mask=(0, 0, m.BLADE_OF_JUSTICE),
         spell_phase_mask=m.PROC_SPELL_PHASE_CAST, disable_effects_mask=0x1, chance=100)
# Crusader's Aegis rank 3: a self-cast Avenging Wrath (triggered Avenging Wrath from Radiant Glory cannot proc it).
procs_on(crusaders_aegis_201462, proc_flags=0x400 | 0x4000, family_name=10, family_mask=(0, m.AVENGING_WRATH, 0),
         spell_phase_mask=m.PROC_SPELL_PHASE_CAST, disable_effects_mask=0x1, chance=100)

# Level-60 set bonuses (user ruling): Judgement Armor 8pc 23591 and Battlegear of Eternal Justice 3pc 26135 keyed on Judgement / Deliverance
# casts (J | Dv own hits). CAST phase = one proc per cast, so Deliverance's five own hits cannot fire it five times (fires on a missed cast too,
# like Swift Retribution). Stock rows: family 10 d0 U, ProcFlags 16, phase HIT, attr 2, chance from the spell (0); effects/triggers untouched.
for _set_bonus in (23591, 26135):
    procs_on(_set_bonus, proc_flags=0x10 | 0x100 | 0x10000, family_name=10, family_mask=m.JUDGEMENT_CASTS,
             spell_phase_mask=m.PROC_SPELL_PHASE_CAST, attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC, chance=0)

# Divine Purpose: the stock HoF stun-removal row goes (the ranks' DBC ProcTypeMask is already 0, so SpellMgr builds no replacement).
remove_spell_proc(-31871)
# Judgements of the Just (SHARED B7, user ruling F9): the talent no longer exists. ProcTypeMask is 0 on 53695/53696 above.
remove_spell_proc(-53695)

# Script bindings for spells declared in this file (RETRIBUTION §5.2, SHARED C1.6 / C1.7). The 201411 / 201412 / 201414 helpers, 20185 / 20186, Sacred Shield's bindings, spell_category(1300) and the -31884 link are paladin_spells.py's.
scripted_by(conviction_20119, 'spell_pal_conviction')
# Heart of the Crusader: the stock class resolves GetSpellWithRank(21183, rank) and the 21183 chain was deleted by the single-rank rollout, so ranks 2/3
# never cast their own debuff; the fork class casts 21183 / 54498 / 54499 by talent rank (user ruling, script route).
unbind_script(-20335, 'spell_pal_heart_of_the_crusader')
scripted_by(-20335, 'spell_pal_heart_of_the_crusader_ret')
scripted_by(-9452, 'spell_pal_vindication')
scripted_by(-53486, 'spell_pal_art_of_war')
scripted_by(-31876, 'spell_pal_judgements_of_the_wise_guard')
scripted_by(-20101, 'spell_pal_benediction')
unbind_script(-9799, 'spell_pal_eye_for_an_eye')
scripted_by(-9799, 'spell_pal_eye_for_an_eye_ret')
unbind_script(-31871, 'spell_pal_divine_purpose')
scripted_by(divine_purpose_201471, 'spell_pal_divine_purpose_ret')
scripted_by(sheath_of_light_capstone_201434, 'spell_pal_sheath_of_light_capstone')
unbind_script(31869, 'spell_pal_sanctified_retribution')
scripted_by(-31869, 'spell_pal_sanctified_retribution')
scripted_by(crusaders_aegis_shield_201430, 'spell_pal_crusaders_aegis_absorb')
linked_spell(53503, sheath_of_light_capstone_201434.id, 2)

# SHARED Part C: the five aura buttons (C1.6), the Concentration scaler, Improved Devotion Aura retarget (C1.7).
for _aura in (devotion_aura_465, retribution_aura_7294, concentration_aura_19746, resistance_aura_19876, crusader_aura_32223):
    scripted_by(_aura, 'spell_pal_aura_press')
scripted_by(concentration_aura_19746, 'spell_pal_concentration_aura')
unbind_script(-20138, 'spell_pal_improved_devotion_aura')
unbind_script(63514, 'spell_pal_improved_devotion_aura_effect')
# C1.3: Crusader Aura becomes a level-20 trainer spell (SpellLevel/BaseLevel 62 -> 20 above); Frost / Fire Resistance Aura retire (PLAN #62: DSL and DBC
# rows stay, the characters migration C1.8 handles saved auras).
trained_by(crusader_aura_32223, trainer_id=202, req_level=20, money_cost=4000)
untrain(frost_resistance_aura_19888, trainer_ids=[202])
untrain(fire_resistance_aura_19891, trainer_ids=[202])


divine_intellect_20257 = spell(
    id=20257,
    name='Divine Intellect',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_HEALING_OF_STAT_PERCENT, misc_value=3),
    ],
    spell_icon_id=44,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (1,1): eff1 total-stat% -> spell crit (Holy) bp 0; new eff2 healing power from Intellect bp 2',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy spells by $s1%, and increases your healing power by $s2% of your Intellect.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


divine_intellect_20258 = spell(
    id=20258,
    name='Divine Intellect',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_HEALING_OF_STAT_PERCENT, misc_value=3),
    ],
    spell_icon_id=44,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (1,1): eff1 total-stat% -> spell crit (Holy) bp 1; new eff2 healing power from Intellect bp 5',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy spells by $s1%, and increases your healing power by $s2% of your Intellect.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


divine_intellect_20259 = spell(
    id=20259,
    name='Divine Intellect',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=2),
        Effect(type=EffectType.APPLY_AURA, base_points=8, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_HEALING_OF_STAT_PERCENT, misc_value=3),
    ],
    spell_icon_id=44,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (1,1): eff1 total-stat% -> spell crit (Holy) bp 2; new eff2 healing power from Intellect bp 8',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy spells by $s1%, and increases your healing power by $s2% of your Intellect.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


holy_power_5923 = spell(
    id=5923,
    name='Holy Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=2),
    ],
    spell_icon_id=1824,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (5,2): bp 0 -> 1 (+2%)',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy spells by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


holy_power_5924 = spell(
    id=5924,
    name='Holy Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=2),
    ],
    spell_icon_id=1824,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (5,2): bp 1 -> 3 (+4%)',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy spells by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


holy_power_5925 = spell(
    id=5925,
    name='Holy Power',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE_SCHOOL, misc_value=2),
    ],
    spell_icon_id=1824,
    notes='pulled from existing data | paladin-rework S2 HOLY 5 (5,2): bp 2 -> 5 (+6%)',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical strike chance of your Holy spells by $s1%.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


unyielding_faith_9453 = spell(
    id=9453,
    name='Unyielding Faith',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=-5001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=1823,
    notes="pulled from existing data | paladin-rework S2 HOLY 5 (1,2): SpellClassSet 0 -> 10; eff1 crit mask ALL_PALADIN, eff2 Light's Hammer cooldown; rank 3 is 201277 (paladin_holy_ranks.py)",
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your spells and abilities by $s1%, and reduces the cooldown of your Light's Hammer by ${$m2/-1000} sec.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'SpellClassSet': 10, **_mask(1, m.ALL_PALADIN), **_mask(2, (0, 0, m.LIGHTS_HAMMER))},
)


unyielding_faith_25836 = spell(
    id=25836,
    name='Unyielding Faith',
    school=School.NORMAL,
    attributes=464,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=-10001, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.COOLDOWN),
    ],
    spell_icon_id=1823,
    notes="pulled from existing data | paladin-rework S2 HOLY 5 (1,2): SpellClassSet 0 -> 10; eff1 crit mask ALL_PALADIN, eff2 Light's Hammer cooldown; rank 3 is 201277 (paladin_holy_ranks.py)",
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Increases the critical strike chance of your spells and abilities by $s1%, and reduces the cooldown of your Light's Hammer by ${$m2/-1000} sec.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'SpellClassSet': 10, **_mask(1, m.ALL_PALADIN), **_mask(2, (0, 0, m.LIGHTS_HAMMER))},
)


judgements_of_the_pure_53656 = spell(
    id=53656,
    name='Judgements of the Pure',
    school=School.HOLY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, misc_value=5),
    ],
    spell_icon_id=3018,
    notes='pulled from existing data | paladin-rework S2 HOLY 4.1: HASTE_ALL bp 3 (+4%); stale eff1 class mask d0 0x800000 cleared; cast by Paladin::OnJudgementCastHoly',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 12015, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Melee, ranged and casting speed increased by $s1% for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee, ranged and casting speed increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


judgements_of_the_pure_53657 = spell(
    id=53657,
    name='Judgements of the Pure',
    school=School.HOLY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL, misc_value=5),
    ],
    spell_icon_id=3018,
    notes='pulled from existing data | paladin-rework S2 HOLY 4.1: HASTE_ALL bp 5 (+6%); stale eff1 class mask d0 0x800000 cleared; cast by Paladin::OnJudgementCastHoly',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellVisualID_1': 12015, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Melee, ranged and casting speed increased by $s1% for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee, ranged and casting speed increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0},
)


infusion_of_light_53672 = spell(
    id=53672,
    name='Infusion of Light',
    school=School.HOLY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
    ],
    spell_icon_id=3021,
    notes='pulled from existing data | paladin-rework S2 HOLY 4.1: eff2 ADD_FLAT CASTING_TIME -0.75/-1.5 s -> ADD_PCT CASTING_TIME -50/-100% (Q5); orphan eff3 BasePoints/DieSides raw keys deleted (empty slot, spec gives eff3 nothing); ProcTypeMask 0x4000 + ProcCharges 1 kept (auto REQ_SPELLMOD row)',
    raw_overrides={'AttributesEx6': 64, 'CastingTimeIndex': 1, 'ProcTypeMask': 16384, 'ProcChance': 100, 'ProcCharges': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 2147483648, 'EffectSpellClassMaskB_1': 1073741824, 'SpellVisualID_1': 12008, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': "Your next Flash of Light's cast time is reduced by $s2% or your next Holy Light's critical strike chance is increased by $s1%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Your next Flash of Light's cast time is reduced by $s2% or your next Holy Light's critical strike chance is increased by $s1%.", 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


infusion_of_light_54149 = spell(
    id=54149,
    name='Infusion of Light',
    school=School.HOLY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.CRITICAL_CHANCE),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.CASTING_TIME),
    ],
    spell_icon_id=3021,
    notes='pulled from existing data | paladin-rework S2 HOLY 4.1: eff2 ADD_FLAT CASTING_TIME -0.75/-1.5 s -> ADD_PCT CASTING_TIME -50/-100% (Q5); orphan eff3 BasePoints/DieSides raw keys deleted (empty slot, spec gives eff3 nothing); ProcTypeMask 0x4000 + ProcCharges 1 kept (auto REQ_SPELLMOD row)',
    raw_overrides={'AttributesEx6': 64, 'CastingTimeIndex': 1, 'ProcTypeMask': 16384, 'ProcChance': 100, 'ProcCharges': 1, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 2147483648, 'EffectSpellClassMaskB_1': 1073741824, 'SpellVisualID_1': 12008, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'NameSubtext_Lang_Mask': 16712190, 'Description_Lang_enUS': "Your next Flash of Light's cast time is reduced by $s2% or your next Holy Light's critical strike chance is increased by $s1%.", 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Your next Flash of Light's cast time is reduced by $s2% or your next Holy Light's critical strike chance is increased by $s1%.", 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


sacred_cleansing_53659 = spell(
    id=53659,
    name='Sacred Cleansing',
    school=School.HOLY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=21, apply_aura=178, misc_value=3),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=21, apply_aura=178, misc_value=1),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=21, apply_aura=178, misc_value=4),
    ],
    spell_icon_id=3019,
    notes='pulled from existing data | paladin-rework S2 HOLY 4.1: duration 10 s -> 8 s (0.2 item 5)',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectSpellClassMaskA_1': 2149580800, 'EffectSpellClassMaskA_2': 65536, 'SpellVisualID_1': 12009, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172, 'Description_Lang_enUS': 'Resistance to Disease, Magic and Poison increased by $s1% for $d.', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Resistance to Disease, Magic and Poison increased by $s1%.', 'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 10, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBonusMultiplier_1': 1.0},
)


# ---------------------------------------------------------------------------
# TEMPORARY SHIM - delete once paladin_talents.py imports the renamed variables (A3 / WP-A3). The three stock Crusade
# rank spells became Smite Evil (smite_evil_31866 / 31867 / 31868, RETRIBUTION §2.1) and 19876 lost "Shadow"
# (resistance_aura_19876); the talents file still imports the old names. Module __getattr__ (PEP 562) serves them without
# declaring a second variable for the same spell (a second name would win the PaladinData.h short name).
# ---------------------------------------------------------------------------
_LEGACY_NAMES = {
    'crusade_31866': 'smite_evil_31866',
    'crusade_31867': 'smite_evil_31867',
    'crusade_31868': 'smite_evil_31868',
    'shadow_resistance_aura_19876': 'resistance_aura_19876',
}


def __getattr__(name):
    if name in _LEGACY_NAMES:
        return globals()[_LEGACY_NAMES[name]]
    raise AttributeError(name)


# ---------------------------------------------------------------------------
# paladin-rework S2 HOLY - spell_proc rows (HOLY.md 7), removals, script bindings for the spells declared in this file.
# Flags: DONE_SPELL_MAGIC_POS 0x4000, TAKEN_DAMAGE 0x100000. Phase 1 CAST, 2 HIT. Chance 0 = the rank's DBC ProcChance.
# The Holy-new rows (resolver 201206, Merciful Strikes, Zealous Exorcism, Sunlight, ...) live in paladin_holy_spells.py /
# paladin_holy_ranks.py.
# ---------------------------------------------------------------------------

# Spiritual Focus capstone (rank 3 only): damage taken, 10 s ICD (starts only on a real proc). TAKEN_DAMAGE is not a spell proc
# flag, so SpellPhaseMask stays 0 (HOLY 7 lists phase 2; LoadSpellProcs logs "SpellPhaseMask ... won't be used" for it, and S1's
# Eye for an Eye row -9799 also has none). The "casting Holy Light" gate lives in spell_pal_spiritual_focus_capstone::CheckProc.
procs_on(spiritual_focus_20207, proc_flags=0x100000, chance=100, cooldown_ms=10000)

# Light's Grace: Holy Light / Flash of Light casts (CAST phase, was HIT on Holy Light only); eff1 is a DUMMY now (trigger_spell 0, X5), chance
# is the rank's DBC ProcChance (100) - the script picks the buff by rank.
procs_on(-31833, proc_flags=0x4000, family_name=10, family_mask=(m.HOLY_LIGHT | m.FLASH_OF_LIGHT, 0, 0),
         spell_phase_mask=m.PROC_SPELL_PHASE_CAST, chance=0)

# Infusion of Light: Flash of Light heals only (the Holy Shock roll moved to the resolver), HIT phase, triggered casts allowed; eff2 is the HoT
# percent read by the script (DisableEffectsMask 0x2). Was (FoL + Holy Shock, type 3).
procs_on(-53569, proc_flags=0x4000, family_name=10, family_mask=(m.FLASH_OF_LIGHT, 0, 0), spell_type_mask=2,
         spell_phase_mask=m.PROC_SPELL_PHASE_HIT, attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC, disable_effects_mask=0x2, chance=0)

# Judgements of the Pure: the stock -53671 row goes (the haste is cast by Paladin::OnJudgementCastHoly once per Judgement / Deliverance cast;
# the ranks' DBC ProcTypeMask is 0 above so SpellMgr builds no replacement). Ranks 54154 / 54155 are orphaned by the 5 -> 3 rank cut.
remove_spell_proc(-53671)

unbind_script(-53569, 'spell_pal_infusion_of_light')
scripted_by(spiritual_focus_20207, 'spell_pal_spiritual_focus_capstone')
scripted_by(infusion_of_light_53569, 'spell_pal_infusion_of_light_holy')
scripted_by(infusion_of_light_53576, 'spell_pal_infusion_of_light_holy')
scripted_by(holy_shock_25912, 'spell_pal_holy_shock_hit')
scripted_by(holy_shock_25914, 'spell_pal_holy_shock_hit')
scripted_by(light_s_grace_31833, 'spell_pal_lights_grace_holy')
scripted_by(light_s_grace_31835, 'spell_pal_lights_grace_holy')
scripted_by(light_s_grace_31836, 'spell_pal_lights_grace_holy')
