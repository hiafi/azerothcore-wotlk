"""
Shaman - player-castable spells (real cast_time_ms/cooldown_ms, not marked passive).

Split from a single source/classes/shaman.py via split_class_file.py (.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see source/classes/README.md for the multi-file layout and lib/dsl/registry.py's load_class_package for how cross-file references (`from .shaman_...` below) resolve.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, School, SpellModOp
from lib.dsl.registry import pot_text, product, spell, talent_mult, tooltip_vars, trained_by, unbind_script, untrain

from . import _masks as m
from .shaman_resto_tooltips import (
    shaman_chainheal_1221, shaman_healtotems_1224, shaman_rain_1222, shaman_shield_1223, shaman_waves_1220,
)
from .shaman_totems import healing_stream_heal_202271, searing_bolt_202270, shaman_firetotems_1216
from .shaman_trigger_spells import fire_nova_8349, stoneclaw_totem_absorb_55328


# ---- tooltip_vars 1210-1212 and 1215 (S1a A4; S1-NOTES section 5). Elemental-tree, unconditional % talents only (the Frost
# pilot's rule): the conditional buffs (Empowerment, Gathering Flames, Echo, Reverberation, Icefury, the Fusion /
# Fury / Reach capstones, the Unrelenting Storm debuff) and cross-tree talents stay out. The rank ids are bare ints
# (shaman_talents.py imports this file, so no import of it here). 1213 (Earthquake) and 1214 (Elemental Blast) are
# in shaman_area_spells.py, 1216 (Fire totems) in shaman_totems.py. Names <= 12 chars (a chain adds a digit).
# Concussion 16035/16105/16106: eff1 = Lightning Bolt / Chain Lightning, eff2 = Thunderstorm, Lava Burst, Earthquake,
# Elemental Blast, shocks. Convection 16039/16109/16110: eff1 = mana cost, eff2 = damage. Shamanism 62097-62099: damage
# on Lightning Bolt / Chain Lightning. Call of Flame 16038/16160/16161: eff1 = Fire totems + Fire Nova, eff2 = Lava Burst.
# Booming Echoes 63370/63372/202535: shock + Elemental Blast damage. Storm, Earth and Fire 51483/51485/51486: Flame
# Shock periodic damage. SPELLMOD_DAMAGE mods multiply (Spell mod pct DAMAGE), so product() is the tooltip multiplier.
shaman_lightning_1210 = tooltip_vars(
    1210, "Lightning Bolt / Chain Lightning: Concussion (eff A), Convection (eff B), Shamanism damage",
    cnc=talent_mult([16035, 16105, 16106], effect=1),
    cnv=talent_mult([16039, 16109, 16110], effect=2),
    shm=talent_mult([62097, 62098, 62099], effect=1),
    mult=product('cnc', 'cnv', 'shm'),
)
shaman_lava_1211 = tooltip_vars(
    1211, "Lava Burst: Concussion (eff B), Convection (eff B), Call of Flame (Lava Burst effect)",
    cnc=talent_mult([16035, 16105, 16106], effect=2),
    cnv=talent_mult([16039, 16109, 16110], effect=2),
    cof=talent_mult([16038, 16160, 16161], effect=2),
    mult=product('cnc', 'cnv', 'cof'),
)
shaman_shocks_1212 = tooltip_vars(
    1212, "Shocks: Concussion (eff B), Convection (eff B), Booming Echoes; Flame Shock periodic: Storm, Earth and Fire",
    cnc=talent_mult([16035, 16105, 16106], effect=2),
    cnv=talent_mult([16039, 16109, 16110], effect=2),
    bme=talent_mult([63370, 63372, 202535], effect=1),
    sef=talent_mult([51483, 51485, 51486], effect=2),
    # S3a A4 (S3-NOTES section 14 Q2): Shamanistic Focus (Enhancement 617; 43338 + 202371/202372), eff2 = the +4/8/12% damage
    # SPELLMOD (eff1 crit, eff3 the Flame Shock DOT twin at the same %); the capstone cooldown cut is not a % and stays off.
    shf=talent_mult([43338, 202371, 202372], effect=2),
    mult=product('cnc', 'cnv', 'bme', 'shf'),
    dot=product('cnc', 'cnv', 'bme', 'sef', 'shf'),
)
shaman_storm_1215 = tooltip_vars(
    1215, "Thunderstorm: Concussion (eff B)",
    mult=talent_mult([16035, 16105, 16106], effect=2),
)

NOTE_IMBUE = 'SH0a (shaman-rework shared doc, Imbues): rewritten in place from the stock weapon enchant (effect 54, item target) into an infinite, visible, death-persistent self aura (AttributesEx3 DEATH_PERSISTENT + AttributesEx2 0x1, not consolidated, GCD 1500/133, EquippedItemClass -1). Raw Targets 16 / HELD_ITEM_ONLY / EquippedItemSubclass / d1 b11 mask / baked Description / stale EffectBasePoints_2 twins cleared. '


water_breathing_131 = spell(
    id=131,
    name='Water Breathing',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=2,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=82),
    ],
    spell_icon_id=545,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Able to breathe underwater.', 'BaseLevel': 22, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the target to breathe underwater for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17057, 'SpellClassMask_2': 268437504, 'SpellClassSet': 11, 'SpellLevel': 22, 'SpellPriority': 50, 'SpellVisualID_1': 371, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


healing_wave_331 = spell(
    id=331,
    name='Healing Wave',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=25,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=129.1, potency_kind='heal', implicit_target_a=45),
    ],
    spell_icon_id=13,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 14 @ level 80); coefficient/mana_cost_pct from max rank; MaxLevel set to 80. PLAN A9 (druid-rework code review finding #9): cast_time_ms=2500, raw CastingTimeIndex (16, 1500ms) dropped. '
          'Potency system P7-Shaman: converted to sp_potency=129.1 (shaman-potency-report.md base-implied default, not mismatched - old coefficient 1.611 was already consistent with the base).',
    tooltip_vars=shaman_waves_1220,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for {pot1*mult}.', 'EffectChainAmplitude_1': 0.20000000298023224, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 64, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


purge_370 = spell(
    id=370,
    name='Purge',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DISPEL, points_per_level=0.020833333333333332, implicit_target_a=6, misc_value=1),
    ],
    spell_icon_id=47,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Purges the enemy target, removing $m1 beneficial magic $leffect:effects;.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 2048, 'SpellClassSet': 11, 'SpellLevel': 12, 'SpellVisualID_1': 214, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lightning_bolt_403 = spell(
    id=403,
    name='Lightning Bolt',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=126.0, potency_kind='direct', implicit_target_a=6),  # 65.2 -> 126 (fills to ~1,000, user)
    ],
    spell_icon_id=62,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 1); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 14 @ level 80); coefficient/mana_cost_pct from max rank; MaxLevel set to 80. PLAN A9 (druid-rework code review finding #9): cast_time_ms=2000, raw CastingTimeIndex (16, 1500ms) dropped. '
          'Potency system P7-Shaman: converted to sp_potency=151.7 (shaman-potency-proposals.txt, mismatched row - old coefficient 0.714 undershot the base-implied value). '
          '2026-10-20 smoke-test fix pass: sp_potency 151.7 -> 65.2 (x0.43, rough damage cut so the Elemental bot lands near 1,000 DPS; tooltip follows {pot1}). '
          '2026-10-22 playtest fix pass (P1): base mana 10% -> 7% (user, all specs).',
    tooltip_vars=shaman_lightning_1210,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Casts a bolt of lightning at the target for {pot1*mult} Nature damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 20.0, 'SpellClassMask_1': 1, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellVisualID_1': 173, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


chain_lightning_421 = spell(
    id=421,
    name='Chain Lightning',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=2000,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=79.6, potency_kind='direct', implicit_target_a=6, chain_targets=3),
    ],
    spell_icon_id=165,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 32); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 8 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          'Potency system P7-Shaman: converted to sp_potency=185.0 (shaman-potency-proposals.txt, mismatched row - old coefficient 0.571 undershot the base-implied value). '
          '2026-10-20 smoke-test fix pass: sp_potency 185.0 -> 79.6 (x0.43, rough damage cut; tooltip follows {pot1}).',
    tooltip_vars=shaman_lightning_1210,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 32, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Hurls a lightning bolt at the enemy, dealing {pot1*mult} Nature damage and then jumping to additional nearby enemies.  Each jump reduces the damage by 30%.  Affects $x1 total targets.', 'EffectChainAmplitude_1': 0.699999988079071, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2, 'SpellClassSet': 11, 'SpellLevel': 32, 'SpellVisualID_1': 36, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cure_toxins_526 = spell(
    id=526,
    name='Cure Toxins',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=4),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=3),
    ],
    spell_icon_id=194,
    notes='pulled from existing data',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 16, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Cures $s1 poison $leffect:effects; and $s1 disease $leffect:effects; on a friendly target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 8, 'SpellClassSet': 11, 'SpellLevel': 16, 'SpellVisualID_1': 187, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


water_walking_546 = spell(
    id=546,
    name='Water Walking',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=30.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=21, apply_aura=104),
    ],
    spell_icon_id=101,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Allows walking over water.', 'AuraInterruptFlags': 2, 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Allows the friendly target to walk across water for $d.  Any damage will cancel the effect.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'ReagentCount_1': 1, 'Reagent_1': 17058, 'SpellClassMask_2': 536872960, 'SpellClassSet': 11, 'SpellLevel': 28, 'SpellVisualID_1': 4483, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


astral_recall_556 = spell(
    id=556,
    name='Astral Recall',
    school=School.NATURE,
    attributes=268500992,
    category=511,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=900000,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=0.0,
    effects=[
        Effect(type=5, base_points=-1, implicit_target_a=1, implicit_target_b=9),
    ],
    spell_icon_id=458,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Yanks the caster through the twisting nether back to $z.  Speak to an Innkeeper in a different place to change your home location.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 1073741824, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellVisualID_1': 220, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


chain_heal_1064 = spell(
    id=1064,
    name='Chain Heal',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=2500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=19,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=52.0, potency_kind='heal', implicit_target_a=45, chain_targets=3),
    ],
    spell_icon_id=963,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 40); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          'Potency system P7-Shaman: converted to sp_potency=52.0 - docs/potency-system.md ("Healing" table, "Decided so far") explicitly resolves Chain Heal to 52, NOT the shaman-potency-proposals.txt/base-implied value of 40.3, because 52 preserves Chain Heal\'s total healing at 500 spell power against stock (1,267 vs 1,278); its base runs ~50% over stock and its coefficient ~48% under as a result.',
    tooltip_vars=shaman_chainheal_1221,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 19, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals the friendly target for {pot1*mult}, then jumps to heal additional nearby targets.  If cast on a party member, the heal will only jump to other party members.  Each jump reduces the effectiveness of the heal by 40%.  Heals $x1 total targets.', 'EffectChainAmplitude_1': 0.6000000238418579, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 256, 'SpellClassSet': 11, 'SpellLevel': 40, 'SpellVisualID_1': 3659, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fire_nova_1535 = spell(
    id=1535,
    name='Fire Nova',
    school=School.FIRE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=22,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, base_points=-1, points_per_level=0.07352941176470588, implicit_target_a=1),
    ],
    spell_icon_id=33,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    tooltip_vars=shaman_firetotems_1216,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Causes the shaman's active Fire totem to emit a wave of flames, inflicting " + pot_text(fire_nova_8349, var='mfc') + " Fire damage to enemies within $8349a1 yards of the totem.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 134217728, 'SpellClassSet': 11, 'SpellLevel': 12, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


ancestral_spirit_2008 = spell(
    id=2008,
    name='Ancestral Spirit',
    school=School.NATURE,
    attributes=268500992,
    cast_time_ms=10000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=72,
    range_yards=30.0,
    effects=[
        Effect(type=113, base_points=64, points_per_level=25.514705882352942, misc_value=120),
    ],
    spell_icon_id=149,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 12); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx': 131072, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 12, 'CastingTimeIndex': 7, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Returns the spirit to the body, restoring a dead target to life with $s1 health and $q1 mana.  Cannot be cast when in combat.', 'EffectBonusMultiplier_1': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassSet': 11, 'SpellLevel': 12, 'SpellPriority': 50, 'SpellVisualID_1': 344, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Targets': 32768},
)


earth_elemental_totem_2062 = spell(
    id=2062,
    name='Earth Elemental Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=7399, implicit_target_a=22, implicit_target_b=41, misc_value=300270, radius_yards=5.0),
    ],
    spell_icon_id=2289,
    notes='SH0b (shared doc, Totems): learn level 66 -> 26 (raw BaseLevel and SpellLevel), Category 23 -> 0, RecoveryTime 600 s -> 120 s, category cooldown 120 s -> 0, duration 120 s -> 30 s, summon creature 15430 -> 300270 (invisible elemental totem; its Index 0 spell 33663 summons the guardian 15352), tooltip, tool strip. Stock GCD 1000/133 unchanged; cost 24% -> 8% of base mana (2026-10-20 smoke-test fix pass, user ruling); no COOLDOWN_ON_EVENT. Was: pulled from existing data',
    raw_overrides={'AttributesEx4': 65536, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Calls forth a greater earth elemental for $d to protect you and your allies. 2 min cooldown.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassMask_2': 4194304, 'SpellClassSet': 11, 'SpellLevel': 26, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)
trained_by(earth_elemental_totem_2062, 210, 26)


earthbind_totem_2484 = spell(
    id=2484,
    name='Earthbind Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=41, misc_value=2630),
    ],
    spell_icon_id=686,
    notes='SH0b (shared doc, Totems): cooldown 15 s -> 30 s, duration 45 s -> 10 s, tooltip (root on placement + slow, cooldown sentence), tool strip. Summon stays creature 2630 (NPC casters SAI 3270/4842 unchanged); d2 b5 kept. Was: pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 6, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons an Earthbind Totem for $d that roots nearby enemies for 2 sec when placed, then slows the movement speed of enemies within 10 yards by 50%. 30 sec cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassMask_3': 32, 'SpellClassSet': 11, 'SpellLevel': 6, 'SpellVisualID_1': 264, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


ghost_wolf_2645 = spell(
    id=2645,
    name='Ghost Wolf',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=98304,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=36, misc_value=16),
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=1, apply_aura=20, amplitude=5000),
    ],
    spell_icon_id=67,
    notes='pulled from existing data',
    raw_overrides={'ActiveIconID': 122, 'AttributesEx': 132096, 'AttributesEx2': 2, 'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases movement speed by $s2%$?s59289[ and regenerates $59289s1% of your maximum health every 5 sec][].\r\nEffects that reduce movement speed may not bring you below your normal movement speed.', 'BaseLevel': 16, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Turns the Shaman into a Ghost Wolf, increasing speed by $s2%$?s59289[ and regenerating $59289s1% of your maximum health every 5 sec][]. As a Ghost Wolf, the Shaman is less hindered by effects that would reduce movement speed. Only useable outdoors.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMultipleValue_1': 1.0, 'EffectMultipleValue_2': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_1': 2048, 'SpellClassSet': 11, 'SpellLevel': 16, 'SpellPriority': 50, 'SpellVisualID_1': 311, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


bloodlust_2825 = spell(
    id=2825,
    name='Bloodlust',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=0.0,
    duration_ms=40000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=192, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=61, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=65, radius_yards=100.0),
    ],
    spell_icon_id=38,
    notes='SH0a: learn level 70 -> 60 (shared doc Bloodlust and Heroism; level change only).',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 256, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee, ranged, and spell casting speed increased by $s1%.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases melee, ranged, and spell casting speed by $s1% for all party and raid members.  Lasts $d.\r\n\r\nAfter the completion of this effect, those affected will become Sated and unable to benefit from Bloodlust again for $57724d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 64, 'SpellClassSet': 11, 'SpellLevel': 60, 'SpellVisualID_1': 7870, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


fire_elemental_totem_2894 = spell(
    id=2894,
    name='Fire Elemental Totem',
    school=School.NORMAL,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=3887, implicit_target_a=22, implicit_target_b=44, misc_value=300271, radius_yards=5.0),
    ],
    spell_icon_id=2290,
    notes='SH0b (shared doc, Totems): learn level 68 -> 36 (raw BaseLevel and SpellLevel), Category 23 -> 0, RecoveryTime 600 s -> 120 s, category cooldown 120 s -> 0, duration 120 s -> 30 s, summon creature 15439 -> 300271 (invisible elemental totem; its Index 0 spell 32982 summons the guardian 15438), tooltip, tool strip. Stock GCD 1000/133, AttributesEx6 NO_CATEGORY_COOLDOWN_MODS unchanged; cost 23% -> 8% of base mana (2026-10-20 smoke-test fix pass, user ruling); no COOLDOWN_ON_EVENT. Was: pulled from existing data',
    raw_overrides={'AttributesEx4': 65536, 'AttributesEx6': 2147483648, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Calls forth a greater fire elemental for $d to rain destruction on your enemies. 2 min cooldown.', 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassMask_2': 8388608, 'SpellClassSet': 11, 'SpellLevel': 36, 'SpellVisualID_1': 221, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)
trained_by(fire_elemental_totem_2894, 210, 36)


searing_totem_3599 = spell(
    id=3599,
    name='Searing Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=44, misc_value=300278),
    ],
    spell_icon_id=680,
    notes='SH0b (shared doc, Totems): cooldown 0 -> 30 s, duration 30 s -> 10 s, summon creature 2523 -> 300278 (passive totem driven by npc_sha_searing_totem; 2523 and 3606 stay for NPC casters), tooltip with the bolt potency (202270), tool strip. Was: pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    tooltip_vars=shaman_firetotems_1216,
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Searing Totem for $d that fires a bolt at an enemy within 20 yards every 1 sec, dealing ' + pot_text(searing_bolt_202270, var='cof') + ' Fire damage. 30 sec cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 16, 'SpellClassSet': 11, 'SpellLevel': 10, 'SpellVisualID_1': 221, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


attack_3606 = spell(
    id=3606,
    name='Attack',
    school=School.FIRE,
    cast_time_ms=2200,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=20.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=17.1, implicit_target_a=6),
    ],
    spell_icon_id=680,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system P8 (2026-10-02): converted to sp_potency=17.1 (base-implied, docs/potency-system.PLAN.md P8, shaman-potency-report.md) - Searing Totem\'s own periodic attack, cast via the generic TotemAI::UpdateAI loop (me->CastSpell(victim, me->ToTotem()->GetSpell(), false)), plain cast, no custom bp. Totems are always exactly the owner\'s level (Totem::InitStats), so no lag-mechanism caveat applies.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 24, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Deals {pot1} Fire damage to the target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 19.0, 'SpellClassMask_1': 1073741824, 'SpellClassSet': 11, 'SpellLevel': 10, 'SpellVisualID_1': 67},
)


wrath_of_air_totem_3738 = spell(
    id=3738,
    name='Wrath of Air Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=43, misc_value=15447),
    ],
    spell_icon_id=340,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 64, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Wrath of Air Totem with $s1 health at the feet of the caster.  The totem provides $2895s1% spell haste to all party and raid members within $2895a1 yards.  Lasts $d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 83, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 64, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


healing_stream_totem_5394 = spell(
    id=5394,
    name='Healing Stream Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=42, misc_value=3527),
    ],
    spell_icon_id=1647,
    notes='SH0b (shared doc, Totems): cooldown 0 -> 30 s, duration 300 s -> 10 s, tooltip with the heal potency (202271), tool strip. Summon stays creature 3527. Was: pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    tooltip_vars=shaman_healtotems_1224,
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Healing Stream Totem for $d. When placed and every 2 sec, it heals the 5 most injured allies within 40 yards for ' + pot_text(healing_stream_heal_202271, var='hst') + '. 30 sec cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 82, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 524288, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


mana_spring_totem_5675 = spell(
    id=5675,
    name='Mana Spring Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=42, misc_value=3573),
    ],
    spell_icon_id=338,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 26); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Mana Spring Totem with $s1 health at the feet of the caster for $d that restores $5677s1 mana every 5 seconds to all party and raid members within $52031a1 yards.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 82, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 524288, 'SpellClassSet': 11, 'SpellLevel': 26, 'SpellVisualID_1': 364, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


stoneclaw_totem_5730 = spell(
    id=5730,
    name='Stoneclaw Totem',
    school=School.NORMAL,
    attributes=65536,
    category=45,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=30000,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=49, points_per_level=21.88888888888889, implicit_target_a=41, misc_value=3579),
    ],
    spell_icon_id=689,
    notes='SH0b (shared doc, Totems): retired (replaced by Earthen Wall): untrained from trainer 210, row kept, tool strip only (RequiredTotemCategoryID_1 -> 0). character_spell/action cleanup is in the characters SQL. Was: pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 8); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Taunting creatures.', 'BaseLevel': 8, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneclaw Totem with $s1 health at the feet of the caster for $d that taunts creatures within $5729a1 yards to attack it.  Enemies attacking the Stoneclaw Totem have a $5728h% chance to be stunned for $39796d. Stoneclaw totem also protects all your totems, causing them to absorb ' + pot_text(stoneclaw_totem_absorb_55328) + ' damage.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 8, 'SpellClassSet': 11, 'SpellLevel': 8, 'SpellVisualID_1': 362, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)
untrain(stoneclaw_totem_5730, [210])


sentry_totem_6495 = spell(
    id=6495,
    name='Sentry Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=2,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=99, implicit_target_a=43, misc_value=3968, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=195,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 139264, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Allows vision through Sentry Totem.  Right-Click on buff to switch back and forth between totem sight and shaman sight.', 'BaseLevel': 34, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons an immobile Sentry Totem with $s1 health at your feet for $d that allows vision of nearby area and warns of enemies that attack it.  Right-Click on buff to switch back and forth between totem sight and shaman sight.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 83, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 34, 'SpellVisualID_1': 368, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


lesser_healing_wave_8004 = spell(
    id=8004,
    name='Lesser Healing Wave',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=1500,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=108.4, potency_kind='heal', implicit_target_a=21),
    ],
    spell_icon_id=964,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          'Potency system P7-Shaman: converted to sp_potency=108.4 (shaman-potency-report.md base-implied default, not mismatched).',
    tooltip_vars=shaman_waves_1220,
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for {pot1*mult}.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 128, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


rockbiter_weapon_8017 = spell(
    id=8017,
    name='Rockbiter Weapon',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, points_per_level=2.75, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER),
        Effect(type=EffectType.APPLY_AURA, base_points=99, implicit_target_a=1, apply_aura=AuraType.MOD_THREAT, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.MOD_BASE_RESISTANCE_PCT, misc_value=1),
    ],
    spell_icon_id=688,
    notes=NOTE_IMBUE + 'Rockbiter: eff0 aura 99 attack power (T0a section 4 option A: BaseLevel 20 / SpellLevel 1 / MaxLevel 60, base 9 + 2.75 per level '
          '= 10/21/70/98/120 at <=20/24/42/52/60), eff1 aura 10 +100% threat all schools, eff2 armor (aura 142, physical) +60% item armor '
          '(S3a, user ruling 2026-10-21 on Q9, [tune] after the combined playtest; was the H2 placeholder 0; base_points 59 = +60%). Never a DUMMY at eff0 (icon 688 hazard, H6). Keeps d0 b22. '
          'The crit-immunity child (202200) is added by spell_sha_imbue.',
    raw_overrides={'AttributesEx': 131088, 'AttributesEx2': 1, 'AttributesEx3': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'AuraDescription_Lang_enUS': 'Immune to critical strikes. Armor and attack power increased. Threat generated increased.', 'BaseLevel': 20, 'Description_Lang_enUS': 'Imbues you with the strength of stone. You are immune to critical strikes from melee and ranged attacks, your armor is increased and your attack power is increased by $s1. You generate $s2% more threat.', 'MaxLevel': 60, 'SpellClassMask_1': 4194304, 'SpellLevel': 1, 'SpellVisualID_1': 8693},
)


flametongue_weapon_8024 = spell(
    id=8024,
    name='Flametongue Weapon',
    school=School.FIRE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=0.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=679,
    notes=NOTE_IMBUE + 'Flametongue: eff0 SPELLMOD_DAMAGE +40% scoped to Lava Burst (d1 b12) and Lava Lash (d2 b2); eff1 DUMMY is the proc '
          'carrier for spell_sha_flametongue_proc (spell_proc declared in shaman_imbues.py). Imbue bit d2 b17, d1 b11 dropped.',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 1, 'AttributesEx3': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'AuraDescription_Lang_enUS': 'Your melee hits deal additional Fire damage. Lava Lash and Lava Burst deal more damage.', 'BaseLevel': 10, 'Description_Lang_enUS': 'Imbues you with fire. Each of your melee hits deals additional Fire damage based on the speed of the weapon that hit. Your Lava Lash and Lava Burst deal $s1% more damage.', 'EffectSpellClassMaskA_1': 0, 'EffectSpellClassMaskA_2': 4096, 'EffectSpellClassMaskA_3': 4, 'MaxLevel': 80, 'SpellClassMask_3': 131072, 'SpellLevel': 10, 'SpellVisualID_1': 8722},
)


frostbrand_weapon_8033 = spell(
    id=8033,
    name='Frostbrand Weapon',
    school=School.FROST,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=0.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=SpellModOp.DAMAGE),
        Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=1, apply_aura=AuraType.ADD_FLAT_MODIFIER, misc_value=SpellModOp.JUMP_TARGETS),
    ],
    spell_icon_id=681,
    notes=NOTE_IMBUE + 'Frostbrand: eff0 SPELLMOD_DAMAGE +30% Lightning Bolt (d0 b0), eff1 +15% Chain Lightning (d0 b1), eff2 SPELLMOD_JUMP_TARGETS +2 '
          'Chain Lightning (d0 b1). The 15% melee Frost proc lives on the hidden child 202201 (shaman_imbues.py), so all three effects are spell mods. '
          'Imbue bit d2 b17, d1 b11 dropped.',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 1, 'AttributesEx3': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'AuraDescription_Lang_enUS': 'Lightning Bolt and Chain Lightning deal more damage, and your melee hits can deal Frost damage.', 'BaseLevel': 20, 'Description_Lang_enUS': 'Imbues you with frost and storm. Your Lightning Bolt deals $s1% more damage. Your Chain Lightning deals $s2% more damage and jumps to $s3 additional targets. Your melee hits have a 15% chance to deal additional Frost damage and grant you 1 charge of Maelstrom Weapon.', 'EffectSpellClassMaskA_1': 1, 'EffectSpellClassMaskB_1': 2, 'EffectSpellClassMaskC_1': 2, 'MaxLevel': 80, 'SpellClassMask_3': 131072, 'SpellLevel': 20, 'SpellVisualID_1': 8721},
)


earth_shock_8042 = spell(
    id=8042,
    name='Earth Shock',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=25.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-11, mechanic=8, implicit_target_a=6, apply_aura=138),
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=60.0, potency_kind='direct', time_basis_ms=1500, implicit_target_a=6),  # 45 -> 60 (user)
    ],
    spell_icon_id=687,
    notes='SH0a: own 6 s cooldown (Category 19 and the shared category cooldown removed, RecoveryTime 6000), potency 75 T 1500, mana 6%; aura text per shared doc. Was: pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 10 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          'Potency system P7-Shaman: eff2 (the Nature damage) converted to sp_potency=237.0 (shaman-potency-proposals.txt, mismatched row); eff1 (the attack-speed debuff) is not a damage/heal/absorb effect, left untouched. '
          '2026-10-20 smoke-test fix pass: eff2 sp_potency 75 -> 32.3 (x0.43, rough damage cut; tooltip follows {pot2}). '
          '2026-10-20 Earth Shock burst (user): eff2 sp_potency 32.3 -> 45 (Echo burst budget; the other shocks stay 32.3).',
    tooltip_vars=shaman_shocks_1212,
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Attack speed slowed.', 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly shocks the target with concussive force, dealing {pot2*mult} Nature damage and reducing its melee attack speed by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 1048576, 'SpellClassSet': 11, 'SpellLevel': 4, 'SpellVisualID_1': 3444, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


flame_shock_8050 = spell(
    id=8050,
    name='Flame Shock',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=25.0,
    duration_ms=18000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=32.3, potency_kind='direct', time_basis_ms=1500, implicit_target_a=6),
        Effect(type=EffectType.APPLY_AURA, sp_potency=10.8, potency_kind='periodic', time_basis_ms=3000, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000),
    ],
    spell_icon_id=678,
    notes='SH0a: own 6 s cooldown (category removed), potency 75 direct / 25 per 3 s tick (T 1500 / 3000), mana 6%; tooltip per shared doc. Was: pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 9 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          'Potency system P7-Shaman: eff1 converted to sp_potency=135.7, eff2 (per tick) to sp_potency=18.9 (both shaman-potency-proposals.txt, mismatched rows). '
          '2026-10-20 smoke-test fix pass: direct 75 -> 32.3, tick 25 -> 10.8 (x0.43, rough damage cut; tooltip follows {pot1}/{pot2}).',
    tooltip_vars=shaman_shocks_1212,
    raw_overrides={'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Burning for Fire damage over time.', 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly sears the target with fire, dealing {pot1*mult} Fire damage immediately and {pot2*dot} Fire damage every $t2 sec for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 268435456, 'SpellClassSet': 11, 'SpellLevel': 10, 'SpellVisualID_1': 3445, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


frost_shock_8056 = spell(
    id=8056,
    name='Frost Shock',
    school=School.FROST,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=25.0,
    duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=Mechanic.SNARE, implicit_target_a=6, apply_aura=AuraType.MOD_DECREASE_SPEED),
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=32.3, potency_kind='direct', time_basis_ms=1500, implicit_target_a=6),
    ],
    spell_icon_id=976,
    notes='SH0a: own 6 s cooldown (category removed), potency 75 T 1500, mana 6%; bonus threat removed (spell_threat 8056 row deleted in 0-world SQL, tooltip sentence dropped). Was: pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 20); RealPointsPerLevel from rank1->covers-60-overridden(undershoot-vs-top-rank) (anchor rank 7 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          'Potency system P7-Shaman: eff2 (the Frost damage) converted to sp_potency=214.6 (shaman-potency-proposals.txt, mismatched row); eff1 (the snare) is not a damage/heal/absorb effect, left untouched. '
          '2026-10-20 smoke-test fix pass: eff2 sp_potency 75 -> 32.3 (x0.43, rough damage cut; tooltip follows {pot2}). '
          '2026-10-22 playtest fix pass (P1): base mana 6% -> 4% (user, all specs).',
    tooltip_vars=shaman_shocks_1212,
    raw_overrides={'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Movement speed slowed.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly shocks the target with frost, dealing {pot2*mult} Frost damage and slowing its movement speed by $s1% for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 2147483648, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 144, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


stoneskin_totem_8071 = spell(
    id=8071,
    name='Stoneskin Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=41, misc_value=5873),
    ],
    spell_icon_id=690,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 4); RealPointsPerLevel from rank1->covers-60 (anchor rank 6 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 4, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Stoneskin Totem with $s1 health at the feet of the caster.  The totem protects party and raid members within $8072a1 yards, increasing armor by $8072s1.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 4, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


strength_of_earth_totem_8075 = spell(
    id=8075,
    name='Strength of Earth Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=41, misc_value=5874),
    ],
    spell_icon_id=691,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 10); RealPointsPerLevel from rank1->covers-60 (anchor rank 5 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Strength of Earth Totem with $s1 health at the feet of the caster.  The totem increases the strength and agility of all party and raid members within $8076a1 yards by $8076s2.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 10, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


tremor_totem_8143 = spell(
    id=8143,
    name='Tremor Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=2,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=41, misc_value=5913),
    ],
    spell_icon_id=1676,
    notes='SH0b (shared doc, Totems): cooldown 0 -> 60 s, duration 300 s -> 10 s, + d0 b15, tooltip gains "1 min cooldown" (U11), tool strip. Was: pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 18, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Tremor Totem for $d that shakes the ground around it, removing Fear, Charm and Sleep effects from party members within 30 yards. 1 min cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': m.SUMMON_D0_B29 | m.TREMOR_SUMMON, 'SpellClassSet': 11, 'SpellLevel': 18, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


cleansing_totem_8170 = spell(
    id=8170,
    name='Cleansing Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=42, misc_value=5924),
    ],
    spell_icon_id=1673,
    notes='SH0b (shared doc, Totems): cooldown 0 -> 60 s, duration 300 s -> 10 s, + d0 b16, tooltip, tool strip. Summon stays creature 5924. Was: pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 38, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Cleansing Totem for $d that removes 1 poison and 1 disease effect from party members within 30 yards when placed and every 3 sec. 1 min cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 82, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': m.SUMMON_D0_B29 | m.CLEANSING_SUMMON, 'SpellClassSet': 11, 'SpellLevel': 38, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


grounding_totem_8177 = spell(
    id=8177,
    name='Grounding Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=30000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=43, misc_value=5925),
    ],
    spell_icon_id=1677,
    notes='SH0b (shared doc, Totems): Category 230 -> 0 (230 is shared with NPC Grounding 34079 / ToC 65989, which keep it), category cooldown 15 s -> 0, RecoveryTime 30 s, duration 45 s -> 10 s, tooltip, tool strip. Was: pulled from existing data',
    raw_overrides={'AttributesEx2': 1073741824, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Grounding Totem at the feet of the caster for $d that will redirect one harmful spell cast on a nearby party member to itself, destroying the totem. Will not redirect area of effect spells. 30 sec cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 83, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 537133056, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


frost_resistance_totem_8181 = spell(
    id=8181,
    name='Frost Resistance Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=44, misc_value=5926),
    ],
    spell_icon_id=1713,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 24); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 24, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons a Frost Resistance Totem with $s1 health at the feet of the caster for $d.  The totem increases party and raid members' frost resistance by $8182s1, if within $8182a1 yards.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 24, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


fire_resistance_totem_8184 = spell(
    id=8184,
    name='Fire Resistance Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=42, misc_value=5927),
    ],
    spell_icon_id=1712,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Fire Resistance Totem with $s1 health at the feet of the caster for $d that increases the fire resistance of party and raid members within $8185a1 yards by $8185s1.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 82, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 28, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


magma_totem_8190 = spell(
    id=8190,
    name='Magma Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=27,
    range_yards=0.0,
    duration_ms=21000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=44, misc_value=5929),
    ],
    spell_icon_id=37,
    notes='SH0b (shared doc, Totems): NPC-only now (SAI 2555 / 17235 cast it; the player Magma is the ground summon 202268): untrained from trainer 210, stock row otherwise unchanged apart from the tool strip (RequiredTotemCategoryID_1 -> 0, required by lint.check_totem_tools). Was: pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 26); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 26, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Magma Totem with $s1 health at the feet of the caster for ${$d-1} sec that causes $8187s1 Fire damage to creatures within $8187a1 yards every $8188t1 seconds.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 4096, 'SpellClassSet': 11, 'SpellLevel': 26, 'SpellVisualID_1': 369, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)
untrain(magma_totem_8190, [210])


flametongue_totem_8227 = spell(
    id=8227,
    name='Flametongue Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=44, misc_value=5950),
    ],
    spell_icon_id=72,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 28); RealPointsPerLevel from rank1->covers-60 (anchor rank 4 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 28, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Flametongue Totem with $s1 health at the feet of the caster.  Party and raid members within $52109a1 yards of the totem have their spell damage and healing increased by up to $52109s1.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 28, 'SpellVisualID_1': 221, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


windfury_weapon_8232 = spell(
    id=8232,
    name='Windfury Weapon',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=0.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=220,
    notes=NOTE_IMBUE + 'Windfury: eff0 DUMMY is the proc carrier for spell_sha_windfury_proc (spell_proc declared in shaman_imbues.py). '
          'Imbue bit d2 b17, d1 b11 dropped; raw EffectBasePoints_2 45 / EffectDieSides_2 1 deleted so no ghost effect 2.',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 1, 'AttributesEx3': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'AuraDescription_Lang_enUS': 'Your melee hits can grant extra attacks.', 'BaseLevel': 30, 'Description_Lang_enUS': 'Imbues you with wind. Your melee hits have a 20% chance to grant you two extra attacks with increased attack power.', 'MaxLevel': 80, 'SpellClassMask_3': 131072, 'SpellLevel': 30, 'SpellVisualID_1': 8723},
)


windfury_totem_8512 = spell(
    id=8512,
    name='Windfury Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=11,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=43, misc_value=6112),
    ],
    spell_icon_id=1397,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases melee haste by $8515s1%.', 'BaseLevel': 32, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Windfury Totem with $s1 health at the feet of the caster.  The totem provides $8515s1% melee haste to all party and raid members within $8515a1 yards.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 83, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 32, 'SpellVisualID_1': 221, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


nature_resistance_totem_10595 = spell(
    id=10595,
    name='Nature Resistance Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=43, misc_value=7467),
    ],
    spell_icon_id=1675,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 30); RealPointsPerLevel from rank1->covers-60 (anchor rank 3 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx6': 67108864, 'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Nature Resistance Totem with $s1 health at the feet of the caster for $d that increases the nature resistance of party and raid members within $10596a1 yards by $10596s1.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 83, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


healing_wave_25357 = spell(
    id=25357,
    name='Healing Wave',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=3000,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=25,
    range_yards=40.0,
    effects=[
        Effect(
            type=EffectType.HEAL, base_points=1619, points_per_level=5.5, die_sides=231, implicit_target_a=45,
            potency_excluded="superseded rank, kept only because an item_template row casts this "
            "exact spell id (see this spell's notes=) - potency forces MaxLevel=0 (uncapped) for "
            "the whole spell, which would silently remove this rank's historical MaxLevel=65 power "
            "ceiling. Same user decision as Warlock's Immolate Rank 3/8 (potency-system.PROGRESS.md "
            "P4): exclude, keep as-is.",
        ),
    ],
    spell_icon_id=13,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid). Potency system P7-Shaman: NOT converted - MaxLevel=65 is this rank\'s own historical power cap, and potency forces MaxLevel=0 spell-wide; excluded and kept exactly as-is, same category as Flame Shock Rank 6 (29228) and Warlock\'s superseded Immolate/Shadow Bolt ranks.',
    raw_overrides={'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 14, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for $s1.', 'EffectBonusMultiplier_1': 1.6109999418258667, 'EffectChainAmplitude_1': 0.20000000298023224, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'MaxLevel': 65, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 10', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 64, 'SpellClassSet': 11, 'SpellLevel': 60, 'SpellVisualID_1': 58, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


strength_of_earth_totem_25361 = spell(
    id=25361,
    name='Strength of Earth Totem',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=41, misc_value=15464),
    ],
    spell_icon_id=691,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid)',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Strength of Earth Totem with $s1 health at the feet of the caster.  The totem increases the strength and agility of all party and raid members within $25362a1 yards by $25362s2.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 81, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 5', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 60, 'SpellVisualID_1': 319, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


flame_shock_29228 = spell(
    id=29228,
    name='Flame Shock',
    school=School.FIRE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=19,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=17,
    range_yards=25.0,
    duration_ms=18000,
    effects=[
        Effect(
            type=EffectType.SCHOOL_DAMAGE, base_points=308, points_per_level=3.5, implicit_target_a=6,
            potency_excluded="superseded rank, kept only because an item_template row casts this "
            "exact spell id (see this spell's notes=) - potency forces MaxLevel=0 (uncapped) for "
            "the whole spell, which would silently remove this rank's historical MaxLevel=67 power "
            "ceiling. Same user decision as Warlock's Immolate Rank 3/8 (potency-system.PROGRESS.md "
            "P4): exclude, keep as-is.",
        ),
        Effect(
            type=EffectType.APPLY_AURA, base_points=85, implicit_target_a=6, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000,
            potency_excluded="same MaxLevel-cap conflict as eff0 above - see that effect's reason.",
        ),
    ],
    spell_icon_id=678,
    notes='pulled from existing data; step-7: superseded rank, kept (referenced by item_template spellid). Potency system P7-Shaman: NOT converted - MaxLevel=67 is this rank\'s own historical power cap, and potency forces MaxLevel=0 spell-wide; excluded and kept exactly as-is, same category as Healing Wave Rank 10 (25357) and Warlock\'s superseded Immolate/Shadow Bolt ranks.',
    raw_overrides={'AttributesEx5': 8192, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': '$s2 Fire damage every $t2 seconds.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Instantly sears the target with fire, causing $s1 Fire damage immediately and $o2 Fire damage over $d. This periodic damage may critically strike and will occur more rapidly based on the caster's spell haste.", 'EffectBonusMultiplier_1': 0.21400000154972076, 'EffectBonusMultiplier_2': 0.10000000149011612, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'MaxLevel': 67, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 6', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_1': 268435456, 'SpellClassSet': 11, 'SpellLevel': 60, 'SpellVisualID_1': 3445, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


heroism_32182 = spell(
    id=32182,
    name='Heroism',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=300000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=26,
    range_yards=0.0,
    duration_ms=40000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=192, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=61, radius_yards=100.0),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=56, apply_aura=65, radius_yards=100.0),
    ],
    spell_icon_id=2288,
    notes='SH0a: learn level 70 -> 60 (level change only); stale raw MaxLevel 74 removed.',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx6': 67108864, 'AttributesEx7': 512, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Melee, ranged, and spell casting speed increased by $s1%.', 'BaseLevel': 60, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases melee, ranged, and spell casting speed by $s1% for all party and raid members.  Lasts $d.\r\n\r\nAfter the completion of this effect, those affected will become Exhausted and unable to benefit from Heroism again for $57723d.', 'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_3': 1.0, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 64, 'SpellClassSet': 11, 'SpellLevel': 60, 'SpellVisualID_1': 7922, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


lava_burst_51505 = spell(
    id=51505,
    name='Lava Burst',
    school=School.FIRE,
    attributes=65536,
    category=1224,
    cast_time_ms=2000,
    cooldown_ms=0,
    category_cooldown_ms=8000,
    mana_cost=0,
    mana_cost_pct=10,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=57.6, potency_kind='direct', implicit_target_a=6),  # 80.7 -> 57.6 (Elemental trim, user 2026-10-22)
    ],
    spell_icon_id=3064,
    notes='SH0a: learn level 75 -> 42 (potency 322.7 kept; BaseLevel derived from SpellLevel by the potency pass). Was: pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 75); RealPointsPerLevel from rank1->top-rank-fallback (anchor rank 2 @ level 80); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. '
          'Potency system P7-Shaman: converted to sp_potency=322.7 (shaman-potency-proposals.txt, mismatched row). '
          '2026-10-20 smoke-test fix pass: sp_potency 322.7 -> 80.7 (x0.25, the hardest cut: Lava Burst auto-crits on Flame Shock and was 40% of the bot\'s damage; tooltip follows {pot1}). '
          '2026-10-22 Elemental trim (user): sp_potency 80.7 -> 57.6 (x0.714) so Elemental lands about 1,000 DPS at 300 s after the cost cut; Lava Burst is 28% of Ele damage and 2% of Enhancement\'s (the overload copy follows at half).',
    tooltip_vars=shaman_lava_1211,
    raw_overrides={'AttributesEx3': 1048576, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 5, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You hurl molten lava at the target, dealing {pot1*mult} Fire damage. If your Flame Shock is on the target, Lava Burst will deal a critical strike.', 'EffectBasePoints_2': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_2': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'Speed': 24.0, 'SpellClassMask_2': 4096, 'SpellClassSet': 11, 'SpellLevel': 42, 'SpellPriority': 50, 'SpellVisualID_1': 11565, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


hex_51514 = spell(
    id=51514,
    name='Hex',
    school=School.NATURE,
    dispel=DispelType.CURSE,
    mechanic=Mechanic.POLYMORPH,
    attributes=1074855936,
    cast_time_ms=1500,
    cooldown_ms=45000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=3,
    range_yards=20.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=6, apply_aura=AuraType.TRANSFORM, misc_value=13321),
        Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=60),
    ],
    spell_icon_id=3058,
    notes='SH0a: learn level 80 -> 28 (shared doc Hex; level change only).',
    raw_overrides={'AttributesEx': 262144, 'AttributesEx2': 64, 'AttributesEx4': 1610612736, 'AttributesEx5': 32, 'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Cannot attack or cast spells.', 'AuraInterruptFlags': 524288, 'BaseLevel': 28, 'CastingTimeIndex': 16, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Transforms the enemy into a frog. While hexed, the target cannot attack or cast spells. Damage caused may interrupt the effect. Lasts $d. Only one target can be hexed at a time.  Only works on Humanoids and Beasts.', 'EffectBasePoints_3': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 664232, 'SpellClassMask_2': 32768, 'SpellClassSet': 11, 'SpellLevel': 28, 'SpellPriority': 50, 'SpellVisualID_1': 12780, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'TargetCreatureType': 65},
)


earthliving_weapon_51730 = spell(
    id=51730,
    name='Earthliving Weapon',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=6,
    range_yards=0.0,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=3061,
    notes=NOTE_IMBUE + 'Earthliving: eff0 DUMMY is the proc carrier for spell_sha_earthliving_proc (spell_proc declared in shaman_imbues.py). '
          'Imbue bit d1 b20 (FB R4), d1 b11 dropped; stock +healing-done effect gone (section 8); raw EffectBasePoints_2 19 / '
          'EffectDieSides_2 1 and SpellDescriptionVariableID 101 deleted.',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx2': 1, 'AttributesEx3': 1048576, 'AuraDescription_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'CastingTimeIndex': 1, 'DefenseType': 1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'AuraDescription_Lang_enUS': 'Your direct heals can also heal over time.', 'BaseLevel': 30, 'Description_Lang_enUS': 'Imbues you with the power of life. Your direct heals have a 20% chance to also heal the target over $51945d.', 'MaxLevel': 80, 'SpellClassMask_2': 1048576, 'SpellLevel': 30, 'SpellVisualID_1': 8723},
)
# Only on a stock TrainerId no NPC uses; 210 is the live Shaman trainer (docs/spell_learn_level.md).
trained_by(earthliving_weapon_51730, trainer_id=210, req_level=30, money_cost=7000)


wind_shear_57994 = spell(
    id=57994,
    name='Wind Shear',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=10000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=25.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, base_points=-1, mechanic=26, implicit_target_a=6),
        Effect(type=EffectType.THREAT, base_points=-1, implicit_target_a=6),
    ],
    spell_icon_id=220,
    notes='SH0a: learn level 16 -> 10, cooldown 6 s -> 10 s (shared doc Wind Shear); tooltip drops the stock threat sentence.',
    raw_overrides={'AttributesEx6': 8388608, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 10, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly blasts the target with a gust of wind, causing no damage but interrupting spellcasting and preventing any spell in that school from being cast for $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 134219776, 'SpellClassSet': 11, 'SpellLevel': 10, 'SpellVisualID_1': 14861},
)
# Only on a stock TrainerId no NPC uses; 210 is the live Shaman trainer (docs/spell_learn_level.md).
trained_by(wind_shear_57994, trainer_id=210, req_level=10, money_cost=1800)


earth_shield_974 = spell(
    id=974,
    name='Earth Shield',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    category=1195,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=15,
    range_yards=40.0,
    duration_ms=600000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, sp_potency=25.0, potency_kind='heal', time_basis_ms=1500, implicit_target_a=21, apply_aura=AuraType.DUMMY),
        Effect(type=EffectType.APPLY_AURA, base_points=29, implicit_target_a=21, apply_aura=149, misc_value=126),
    ],
    spell_icon_id=2015,
    notes='SH0a: now baseline at 25 (was Restoration talent 1698); heal per charge is potency 25 T 1500 on eff0 (the DUMMY the spell_sha_earth_shield script reads; 379 untouched). Was: pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    tooltip_vars=shaman_shield_1223,
    raw_overrides={'AttributesEx4': 524288, 'AttributesEx5': 32, 'AttributesEx6': 67108864, 'AttributesEx7': 1073742848, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Heals you when you take damage.', 'AuraInterruptFlags': 524288, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Protects the target with an earthen shield, reducing casting or channeling time lost when damaged by $s2%  and causing attacks to heal the shielded target for {pot1*mult}.  This effect can only occur once every few seconds.  $n charges.  Lasts $d.  Earth Shield can only be placed on one target at a time and only one Elemental Shield can be active on a target at a time.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 6, 'ProcTypeMask': 172712, 'SpellClassMask_2': 1024, 'SpellClassSet': 11, 'SpellLevel': 25, 'SpellVisualID_1': 7362, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


totem_of_wrath_30706 = spell(
    id=30706,
    name='Totem of Wrath',
    school=School.NORMAL,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=5,
    range_yards=0.0,
    duration_ms=300000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=44, misc_value=17539),
    ],
    spell_icon_id=2019,
    notes='pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level 50); RealPointsPerLevel from rank1->covers-60 (anchor rank 2 @ level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Summons a Totem of Wrath with $s1 health at the feet of the caster.  The totem increases spell power by $57658s2 for all party and raid members, and increases the critical strike chance of all attacks by $30708s1% against all enemies within $30708a1 yards.  Lasts $d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 63, 'EquippedItemClass': -1, 'MaxLevel': 80, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': 536870912, 'SpellClassSet': 11, 'SpellLevel': 50, 'SpellVisualID_1': 221, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


thunderstorm_51490 = spell(
    id=51490,
    name='Thunderstorm',
    school=School.NATURE,
    attributes=65536,
    category=1223,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=45000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=43.0, potency_kind='direct', time_basis_ms=1500, implicit_target_a=22, implicit_target_b=15, radius_yards=10.0),  # S1-FIX: 100 x0.43 (harness)
        Effect(type=137, base_points=9, implicit_target_a=1),
        Effect(type=EffectType.KNOCK_BACK, base_points=59, implicit_target_a=22, implicit_target_b=15, misc_value=300, radius_yards=10.0),
    ],
    spell_icon_id=3080,
    notes='S1a A4 (shaman-rework Elemental, Thunderstorm): potency 100 per target (T 1500; was 220.6), energize 10% (eff2 stored 9; stock '
          '8%), knockback stock, no target cap (stock split above 10 targets accepted, Q18). 45 s cooldown stays Category 1223 / '
          'CategoryRecoveryTime 45000, RecoveryTime 0 (Cooldown Haste reads either; the stun-castable rank 2 202594 shares category '
          '1223, so the cooldown is shared). SpellLevel AND BaseLevel 60 -> 20 (both are raw-only keys), AttributesEx5 0x8 (usable '
          'while stunned) dropped: baseline Thunderstorm is not castable while stunned (Q8), Call of Thunder r3 grants the stun-castable '
          'rank 202594. Cost stays 0. Description rewritten (potency x Concussion / Convection via tooltip_vars 1215, no stock '
          '"usable while stunned" sentence). Was: pulled from existing data; single-rank bootstrap: BasePoints/BaseLevel/SpellLevel kept '
          'from rank 1 (learn level 60); coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80. Potency system '
          'P7-Shaman: eff1 converted to sp_potency=220.6; eff2 (mana restore %) and eff3 (knockback) are not damage/heal/absorb effects.',
    tooltip_vars=shaman_storm_1215,
    raw_overrides={'AttributesEx5': 0, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You call down a bolt of lightning, energizing you and damaging nearby enemies. Restores $s2% of your mana and deals {pot1*mult} Nature damage to all enemies within $a1 yards, knocking them back 20 yards. 45 sec cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 11, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_2': 8192, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 11302, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


riptide_61295 = spell(
    id=61295,
    name='Riptide',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=65536,
    category=1228,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=6000,
    mana_cost=0,
    mana_cost_pct=18,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.HEAL, sp_potency=43.0, potency_kind='heal', time_basis_ms=1500, implicit_target_a=21),
        Effect(type=EffectType.APPLY_AURA, sp_potency=5.0, potency_kind='heal_periodic', time_basis_ms=3000, implicit_target_a=21, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
    ],
    spell_icon_id=3786,
    tooltip_vars=shaman_rain_1222,
    notes='S2a A4 (shaman-rework Restoration, 3C Q3): 43 potency direct (T 1500) + 5 per 3 s tick (T 3000), healing scales with '
          'level from 30 (SpellLevel and BaseLevel 30 on both potency effects; was the stock-converted 62.8 + 6.3 flat at 60). '
          'Talent 2064 moves to (4,1), learned at 30 (tier 4) with the talent: a talent-rank spell, so no trainer row (L13). 15 s, '
          '6 s cooldown (Category 1228 / CategoryRecoveryTime 6000, no Cooldown Haste), 18% mana (stock, [tune]), instant, 40 yd, '
          'family d2 b4 (Healing Way, Torrent, Purification, Tidal Focus, Tidal Mastery, the torrent hook). Description and aura '
          'text per the doc, aura text number-free; the potency numbers go through tooltip entry 1222 `tide` (Healing Way, '
          'Torrent, Purification). The latent raw EffectBasePoints_3 24 / EffectDieSides_3 1 twin (the stock +25% Chain Heal '
          'effect, absent from the typed effects) is deleted: the +25% is the Chain Heal script\'s (X3). Was: pulled from existing '
          'data; Potency system P7-Shaman 62.8 / 6.3.',
    raw_overrides={'AttributesEx3': 128, 'AttributesEx6': 67108864, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': "Healing over time. The shaman's next Chain Heal on you is stronger.", 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Heals a friendly target for {pot1*tide} and another {pot2*tide} every 3 sec over $d. Your next Chain Heal on that primary target within $d consumes the heal over time effect and heals for 25% more. 6 sec cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'InterruptFlags': 15, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_3': 16, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellVisualID_1': 12994, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


elemental_mastery_16166 = spell(
    id=16166,
    name='Elemental Mastery',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=33882112,
    category=0,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=10),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=1, trigger_spell=64701),
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.COST)),
    ],
    spell_icon_id=117,
    notes='S1a A4 (shaman-rework Elemental, Elemental Mastery, Brief Decision 11): 3 min is RecoveryTime 180000 with Category 0 / '
          'CategoryRecoveryTime 0 (stock Category 1202 was shared with Nature\'s Swiftness 16188; the "shares a cooldown" sentence is '
          'gone), Cooldown Haste applies (>= 30 s), off the GCD (StartRecoveryTime 0). eff1 (idx 0) stock: instant cast, its mask is '
          'forced to (0x3, 0x1000) at load by SpellInfoCorrections.cpp:4192, so the raw A_1/A_2 masks are left as the client-side '
          'stock. eff3 (idx 2) is the new free cast: ADD_PCT_MODIFIER SPELLMOD_COST (14) stored -101 (-100%), mask C_1 0x3 (Lightning '
          'Bolt d0 b0 + Chain Lightning d0 b1) and C_2 0x1000 (Lava Burst d1 b12); the stale mask C_1 0x90100003 / C_2 0x3810 and the '
          'latent EffectBasePoints_3 -1 / EffectDieSides_3 1 twins were deleted so the typed eff3 wins. ProcCharges 1 + spell_proc '
          '16166 (family 11 mask 3/4096/0) consume both mods on the first LB/CL/Lava Burst. Haste is 64701 (10%, 15 s, family 11 '
          'with d2 b26). Aura and description texts per the doc. Was: pulled from existing data',
    raw_overrides={'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Lightning Bolt, Chain Lightning or Lava Burst is instant and free.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'When activated, your next Lightning Bolt, Chain Lightning or Lava Burst becomes instant and costs no mana. You also gain $64701s1% spell haste for $64701d. Does not stack with other similar cast speed effects. 3 min cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2416967683, 'EffectSpellClassMaskA_2': 12288, 'EffectSpellClassMaskB_1': 3, 'EffectSpellClassMaskB_2': 4096, 'EffectSpellClassMaskC_1': 3, 'EffectSpellClassMaskC_2': 4096, 'EffectSpellClassMaskC_3': 0, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 69632, 'RangeIndex': 1, 'SpellClassMask_2': 16384, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 290, 'StartRecoveryCategory': 0, 'StartRecoveryTime': 0},
)


# The haste buff Elemental Mastery triggers (declared for S1a: moved to family 11 with d2 b26 so Shamanism's capstone
# can add +5 to it with SPELLMOD_EFFECT1; shares aura type 65 with Icy Veins and Power Infusion in spell_group 1122).
elemental_mastery_haste_64701 = spell(
    id=64701,
    name='Elemental Mastery',
    school=School.NATURE,
    dispel=DispelType.MAGIC,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=9, implicit_target_a=1, apply_aura=65, misc_value=24),
    ],
    spell_icon_id=117,
    notes='S1a A4 (shaman-rework Elemental, Brief Decision 11): pulled from the stock row (aura 65 bp 14 = 15% -> stored 9 = 10%, 15 s, '
          'misc 24 stock). SpellClassSet 0 -> 11 and the stale SpellClassMask_2 0x4000 dropped for SpellClassMask_3 = EM_HASTE (d2 '
          'b26, 0x4000000): the one bit Shamanism r3 (62099) targets with a flat SPELLMOD_EFFECT1 +5 (-> 15%). Aura text per the doc, '
          'number-free. Member of spell_group 1122 (shaman_haste_group.py).',
    raw_overrides={'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Spell haste increased.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases your spell casting speed by $s1%.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectBasePoints_2': -1, 'EffectBasePoints_3': -1, 'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EquippedItemClass': -1, 'ImplicitTargetA_2': 1, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': m.EM_HASTE, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50},
)


nature_s_swiftness_16188 = spell(
    id=16188,
    name="Nature's Swiftness",
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    attributes=33882112,
    category=1202,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=120000,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=1, apply_aura=108, misc_value=10),
    ],
    spell_icon_id=112,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 131072, 'AttributesEx4': 64, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Your next Nature spell with a casting time less than 10 secs will be an instant cast spell.', 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "When activated, your next Nature spell with a base casting time less than 10 sec. becomes an instant cast spell. Nature's Swiftness shares a cooldown with Elemental Mastery.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 2499, 'EffectSpellClassMaskA_2': 32768, 'EquippedItemClass': -1, 'InterruptFlags': 4, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 87376, 'RangeIndex': 1, 'SpellClassMask_2': 128, 'SpellClassSet': 11, 'SpellLevel': 1, 'SpellPriority': 50, 'SpellVisualID_1': 4040},
)


mana_tide_totem_16190 = spell(
    id=16190,
    name='Mana Tide Totem',
    school=School.NORMAL,
    attributes=65536,
    category=0,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=4, implicit_target_a=42, misc_value=10467),
    ],
    spell_icon_id=94,
    notes='S2a A4 (shaman-rework Restoration, Mana Tide Totem): duration 13 s -> 10 s (5 pulses incl. the one on placement at a 2 s '
          'period), cooldown 5 min -> 3 min as RecoveryTime 180000 with Category 0 / CategoryRecoveryTime 0 (Elemental Mastery shape) '
          'so Cooldown Haste applies and Restorative Totems\' SPELLMOD_COOLDOWN (d0 b25) reaches it. Summon mask d0 b29 (stock) + '
          'b25 MANA_TIDE_SUMMON, the one identity bit for that mod. The stock SpellDescriptionVariableID 61 and the latent raw '
          'EffectBasePoints_2 9 / EffectDieSides_2 1 twin are deleted. No mana cost (stock), instant, GCD 1000/133 (stock). Totem '
          'health keeps the id (SpellEffects.cpp:2636). Tooltip per the doc. Was: pulled from existing data',
    raw_overrides={'AttributesEx7': 32, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons a Mana Tide Totem for $d that restores 2.5% of maximum mana every 2 sec to the other members of your party within 30 yards, and 5% of your maximum mana to you. 3 min cooldown.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 82, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'RequiredTotemCategoryID_1': 0, 'SpellClassMask_1': m.SUMMON_D0_B29 | m.MANA_TIDE_SUMMON, 'SpellClassSet': 11, 'SpellLevel': 40, 'SpellVisualID_1': 364, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1000},
)


stormstrike_17364 = spell(
    id=17364,
    name='Stormstrike',
    school=School.NORMAL,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=8000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=8,
    range_yards=5.0,
    duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=19, implicit_target_a=6, apply_aura=271, misc_value=8),
        Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=6, trigger_spell=32175),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=-1, implicit_target_a=6, trigger_spell=32176),
    ],
    spell_icon_id=2562,
    notes='S3a A4 (shaman-rework Enhancement doc, Stormstrike): stock data kept (eff0 aura 271 +20% Nature taken from the caster, 4 charges, '
          '12 s; eff1/eff2 TRIGGER_SPELL the 32175/32176 weapon strikes; 8 s cooldown, mana 8% of base [tune]); tooltip and aura text per '
          'the doc (aura text number-free). The GCD follows spell haste through the gcd_haste aura; the cooldown is not hasted (8 s). '
          'EquippedItemClass 2 / subclass mask is the stock weapon requirement and stays (not the unset-0 hazard of L1). The Stoneskin '
          'grant binding (spell_sha_stoneskin_grant) stays; spell_sha_enh_stormstrike is added by shaman_enhancement.py (A3). '
          'Was: pulled from existing data',
    raw_overrides={'AttributesEx': 512, 'AttributesEx3': 67108866, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Nature damage taken from the shaman increased.', 'BaseLevel': 40, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Instantly attack with both weapons. In addition, the next 4 sources of Nature damage you deal to the target are increased by 20%. Lasts 12 sec. 8 sec cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 1049603, 'EffectSpellClassMaskA_2': 8192, 'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 100, 'ProcCharges': 4, 'ProcTypeMask': 139808, 'RangeIndex': 2, 'SpellClassMask_2': 16777232, 'SpellClassSet': 11, 'SpellLevel': 40, 'SpellVisualID_1': 7660, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


shamanistic_rage_30823 = spell(
    id=30823,
    name='Shamanistic Rage',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=60000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=14, implicit_target_a=1, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=30824),
        Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
    ],
    spell_icon_id=2024,
    notes='S3a A4 (Enhancement doc, Shamanistic Rage): stock data kept (eff0 PROC_TRIGGER_SPELL 30824 mana, 15% of attack power, PPM 18 in '
          'spell_proc; eff1 -30% damage taken; 15 s; AttributesEx5 8 = usable while stunned; no mana cost); on the GCD (StartRecovery 133 / '
          '1500, hasted by the gcd_haste aura) with a 1 min RecoveryTime (Category 0, so Cooldown Haste applies). Tooltip and aura text per '
          'the doc (aura text number-free). The +5 charges / Unleashed Rage clause are spell_sha_enh_shamanistic_rage (shaman_enhancement.py). '
          'Was: pulled from existing data',
    raw_overrides={'AttributesEx5': 8, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Damage taken reduced. Your melee attacks can restore mana.', 'BaseLevel': 50, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Reduces all damage taken by 30% and gives your successful melee attacks a chance to regenerate mana equal to 15% of your attack power. Also grants 5 Elemental Charge of your active imbue. Usable while stunned. Lasts 15 sec. 1 min cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712190, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 100, 'ProcTypeMask': 20, 'RangeIndex': 1, 'SpellClassMask_2': 131072, 'SpellClassSet': 11, 'SpellLevel': 50, 'SpellVisualID_1': 47, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


feral_spirit_51533 = spell(     # variable name kept (shaman_talents.py imports it, the header name SPELL_FERAL_SPIRIT stays); it IS Elemental Spirits
    id=51533,
    name='Elemental Spirits',
    school=School.NATURE,
    attributes=65536,
    cast_time_ms=0,
    cooldown_ms=120000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=12,
    range_yards=30.0,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.SUMMON, base_points=0, implicit_target_a=47, implicit_target_b=1, misc_value=300262, radius_yards=2.0),
        Effect(type=EffectType.SUMMON, base_points=0, implicit_target_a=47, implicit_target_b=1, misc_value=300263, radius_yards=2.0),
        Effect(type=EffectType.SUMMON, base_points=0, implicit_target_a=47, implicit_target_b=1, misc_value=300264, radius_yards=2.0),
    ],
    spell_icon_id=3081,
    notes='S3a A4 (Enhancement doc, Elemental Spirits; brief item 14): the stock Feral Spirit (talent-only id, no NPC caster, no other '
          'user) reworked in place. 20 s duration, 2 min RecoveryTime (Category 0 / CategoryRecoveryTime 0, so Cooldown Haste applies), '
          'instant, GCD on (StartRecovery 133 / 1500, hasted by the gcd_haste aura), mana 12% of base [tune]. Three SUMMON effects, one '
          'each (base_points 0 = 1 wolf), Fire Spirit 300262 / Frost Spirit 300263 / Wind Spirit 300264 (A3 declares the creatures), '
          'SummonProperties 61 (ally guardian, no pet bar, no one-pet rule; the stock 1161 would keep only the last wolf) as raw '
          'EffectMiscValueB_1..3; effect 3 is swapped to the Rock Spirit 300265 under Rockbiter by spell_sha_enh_elemental_spirits '
          '(SPELLVALUE_MISCVALUE2 in BeforeCast, B2). The latent raw twins EffectBasePoints_2/3 and EffectDieSides_2/3 of the stock row '
          'are deleted (they would have won the moment effects 2/3 existed). The 20 s timer buff 202407 (A3) is applied by the script. '
          'Tooltip per the doc. Was: pulled from existing data (Feral Spirit: two wolves of 29264 under 1161, 45 s, 3 min)',
    raw_overrides={'AttributesEx': 268436481, 'AttributesEx2': 524288, 'AttributesEx3': 1073872896, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 50, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': "Summons three Elemental Spirit wolves for 20 sec. The Fire Spirit's bites burn the target with Spirit Flame Shock, the Frost Spirit copies your Stormstrikes at reduced damage and the Wind Spirit's attacks can unleash Gusts. Each wolf benefits from your matching Ascendance. While Rockbiter is active, the Wind Spirit is replaced by a Rock Spirit that taunts nearby enemies when summoned and grants you 1 Stoneskin each time it hits. 2 min cooldown.", 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectMiscValueB_1': 61, 'EffectMiscValueB_2': 61, 'EffectMiscValueB_3': 61, 'EquippedItemClass': -1, 'InterruptFlags': 8, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 65536, 'SpellClassSet': 11, 'SpellLevel': 50, 'SpellVisualID_1': 13077, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


cleanse_spirit_51886 = spell(
    id=51886,
    name='Cleanse Spirit',
    school=School.NATURE,
    attributes=327680,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=7,
    range_yards=40.0,
    effects=[
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=4),
        Effect(type=EffectType.DISPEL, implicit_target_a=21, misc_value=2),
    ],
    spell_icon_id=3740,
    notes='SH0a: learn level 40 -> 36 (now baseline, was Restoration talent 2084); disease effect (misc 3) removed, curse + poison remain.',
    raw_overrides={'AttributesEx6': 512, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 36, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Removes 1 curse and 1 poison effect from a friendly target.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712190, 'PreventionType': 1, 'ProcChance': 101, 'SpellClassMask_2': 8, 'SpellClassSet': 11, 'SpellLevel': 36, 'SpellVisualID_1': 187, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


tidal_force_55198 = spell(
    id=55198,
    name='Tidal Force',
    school=School.NORMAL,
    dispel=DispelType.MAGIC,
    cast_time_ms=0,
    cooldown_ms=180000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=2000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=59, implicit_target_a=1, apply_aura=AuraType.DUMMY, misc_value=7),
    ],
    spell_icon_id=176,
    notes='pulled from existing data',
    raw_overrides={'AttributesEx': 268435456, 'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': 'Increases the critical effect chance of your Healing Wave, Lesser Healing Wave and Chain Heal by $s1%. Each critical heal reduces the chance by 20%. Lasts $55166d.', 'BaseLevel': 20, 'CastingTimeIndex': 1, 'DefenseType': 1, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'Increases the critical effect chance of your Healing Wave, Lesser Healing Wave and Chain Heal by $55198s1%. Each critical heal reduces the chance by 20%. Lasts $55166d.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EffectSpellClassMaskA_1': 448, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712172, 'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassMask_3': 1, 'SpellClassSet': 11, 'SpellLevel': 20, 'SpellVisualID_1': 12092},
)


lava_lash_60103 = spell(
    id=60103,
    name='Lava Lash',
    school=School.FIRE,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=6000,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=4,
    range_yards=5.0,
    effects=[
        Effect(type=31, base_points=109, implicit_target_a=6),
    ],
    spell_icon_id=3741,
    notes='S3a A4 (Enhancement doc, Lava Lash): eff0 WEAPON_PERCENT_DAMAGE 110% off-hand weapon, Fire (stock 100%, raised to 250% then trimmed to 110% 2026-10-22 [tune], S3-ENH-TRIM-DIAG: the engine skips the off-hand penalty on Fire strikes) '
          'after S3-ENH-DPS-DIAG B3: at 100% of a halved off-hand it was worth about 145 per cast, less than every GCD it displaced); the stock eff1 DUMMY 25 (the '
          'Flametongue-enchant +25% carrier of spell_sha_lava_lash) is deleted and that script unbound (a family-11 DUMMY with icon 688 at '
          'eff0 would also trip SpellEffects.cpp:3754; there is none). The +40% under Flametongue is 8024 eff0 SPELLMOD_DAMAGE on d2 b2 '
          '(aura, not the off-hand enchant). 6 s cooldown, mana 4% of base (stock) [tune], GCD on. EquippedItemClass 2 + InvTypes '
          '4194304 is the stock off-hand weapon requirement and stays. spell_sha_stoneskin_grant stays bound (shaman_imbues.py). '
          'Level 41 -> 30 (BaseLevel and SpellLevel): the talent moved to row 4 (level 30), as Riptide\'s 30 in S2. '
          'Was: pulled from existing data',
    raw_overrides={'AttributesEx': 134218240, 'AttributesEx3': 16777216, 'AuraDescription_Lang_Mask': 16712188, 'BaseLevel': 30, 'CastingTimeIndex': 1, 'DefenseType': 2, 'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': 'You charge your off-hand weapon with lava and instantly strike, dealing 110% off-hand weapon damage as Fire damage. Deals 40% more damage while Flametongue is active. 6 sec cooldown.', 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'EquippedItemClass': 2, 'EquippedItemInvTypes': 4194304, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': 'Rank 1', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2, 'SpellClassMask_3': 4, 'SpellClassSet': 11, 'SpellLevel': 30, 'SpellPriority': 50, 'SpellVisualID_1': 12759, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500},
)


# Lava Lash: the stock spell_sha_lava_lash (+25% with a Flametongue-enchanted off hand through the eff1 DUMMY, now deleted) retires;
# the +40% is Flametongue's own SPELLMOD. spell_sha_stoneskin_grant stays bound to 60103 (shaman_imbues.py). Exact live key (L7).
unbind_script(60103, 'spell_sha_lava_lash')
