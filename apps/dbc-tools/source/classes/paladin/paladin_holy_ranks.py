"""
Paladin - Holy talent rank spells (paladin-rework S2, WP-A2c).

Source of truth: .agents/plans/paladin-rework/paladin-rework.HOLY.md section 2.1 (ids 201240-201279), section 4
(common rules, DUMMY-with-proc X5 table), section 5 (talent table: effects, masks, per-rank tooltips), section 7
(spell_proc rows) and section 2.7 (script bindings).

Declared here, in id order:
    201240-201242 A New Dawn          201257-201259 Blessed Crusade     201271-201273 Shock and Awe
    201243-201245 Enduring Light      201260-201261 Light's Fervor      201274-201276 Overflowing Light
    201246-201248 Illuminated Steel   201262-201264 Dawn before Dusk    201277 Unyielding Faith r3 (clone of 25836)
    201249-201251 Merciful Strikes    201265-201267 Radiant Exorcism    201278 Blessed Hands r3 (clone of 53661)
    201252-201253 Zealous Exorcism    201268-201270 Glimmer of Light    201279 Pure of Heart r3 (clone of 31823)
    201254-201256 Sunlight

Every rank is a hidden passive (attributes 0x1D0, duration -1, RangeIndex 1, target 1, SpellClassSet 10 so a SpellMod
never leaks into another family, never icon 25). Stored base_points are live - 1 (die_sides 1); a DUMMY effect with a
spell_proc row carries trigger_spell 0 / misc 0 (HOLY section 4, X5) and the row's DisableEffectsMask names the
value-only DUMMY effects. SpellLevel is the talent row's learn level (row N -> 10 + 5N). Tooltips are the section 5
text with literal per-rank numbers (SpellMods never move a tooltip); the capstone format is
"<text>\\n\\n|cFF9D9D9DCapstone Bonus: <capstone>|r" below the last rank and the same without colour on the last.

The rank objects are module-level variables; paladin_talents.py (A3) imports them. Helpers owned by other files
(Crusader's Zeal 201213, Sunlight 201232, ...) are referenced by bare id only.
"""

from dataclasses import replace

from lib import potency as _potency
from lib.dsl import AuraType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import procs_on, scripted_by, spell

from . import _masks as m


# --- helpers -------------------------------------------------------------------------------------------------------

_MASK_KEYS = {1: 'A', 2: 'B', 3: 'C'}


def _aura(aura, base_points=0, misc_value=0, trigger_spell=0):
    """One self-targeted APPLY_AURA effect (target 1)."""
    return Effect(
        type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=1, apply_aura=aura,
        misc_value=int(misc_value), trigger_spell=trigger_spell,
    )


def _mod(op, base_points, pct=False):
    """A SpellMod effect (the class mask goes in `masks=` of `_rank`, keyed by this effect's 1-based index)."""
    return _aura(AuraType.ADD_PCT_MODIFIER if pct else AuraType.ADD_FLAT_MODIFIER, base_points, op)


def _dummy(base_points=0):
    """A DUMMY effect: trigger_spell 0 and misc 0 so a spell_proc row on its spell never casts a stale trigger (X5)."""
    return _aura(AuraType.DUMMY, base_points)


def _desc(text, capstone=None, last=False):
    """HOLY section 5 tooltip rule: grey capstone line on every rank below the last, plain on the last."""
    if capstone is None:
        return text
    if last:
        return f"{text}\n\nCapstone Bonus: {capstone}"
    return f"{text}\n\n|cFF9D9D9DCapstone Bonus: {capstone}|r"


def _rank(spell_id, name, effects, icon, level, description, notes, masks=None):
    """A talent rank spell. `masks` maps a 1-based effect index to its (d0, d1, d2) EffectSpellClassMask triple."""
    raw = {
        'EquippedItemClass': -1, 'SpellClassSet': 10, 'SpellLevel': level, 'ProcChance': 101,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': description,
        'AuraDescription_Lang_Mask': 16712188,
    }
    for i in range(1, len(effects) + 1):
        raw[f'EffectChainAmplitude_{i}'] = 1.0
    for effect_index, triple in (masks or {}).items():
        for dword, value in enumerate(triple, start=1):
            if value:
                raw[f'EffectSpellClassMask{_MASK_KEYS[effect_index]}_{dword}'] = value
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=464,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1,
        effects=effects, spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


_CR_VERSATILITY = 1 << 21  # 1 << CombatRating.VERSATILITY
_CR_COOLDOWN_HASTE = 1 << 22  # 1 << CombatRating.COOLDOWN_HASTE
_MISC_SCHOOL_HOLY_DISEASE = 3  # aura 246 misc 3 = Disease

# --- Sunlight tooltip ----------------------------------------------------------------------------------------------
# A talent-pane rank tooltip must show its own rank's fraction, which a tooltip variable can't do, so each rank keeps
# the literal ${...} expression of Sunlight's hit 201232 scaled by the rank constant (HOLY section 4.1 exception).
# 201232 (A2a, paladin_holy_spells.py): hybrid 7.5 SP + 7.5 AP, direct, instant (time basis 1.5 s), SpellLevel 25.
# Re-copy these numbers here if 201232's potency ever changes (HOLY section 11 risk 8).
_SUNLIGHT_HIT = _potency.resolve(
    _potency.PotencyEffect(sp_potency=7.5, ap_potency=7.5, kind=_potency.KIND_DIRECT, t_ms=1500.0), spell_level=25,
)


def _sunlight_damage(fraction):
    """`{pot1}` of 201232 with every linear term (level terms and the SP/AP bonus) multiplied by `fraction`."""
    if fraction == 1.0:
        scaled = _SUNLIGHT_HIT
    else:
        scaled = replace(
            _SUNLIGHT_HIT,
            points_per_level=_SUNLIGHT_HIT.points_per_level * fraction,
            sp_coefficient=_SUNLIGHT_HIT.sp_coefficient * fraction,
            ap_coefficient=_SUNLIGHT_HIT.ap_coefficient * fraction,
            tooltip_low_intercept=_SUNLIGHT_HIT.tooltip_low_intercept * fraction,
            tooltip_low_slope=_SUNLIGHT_HIT.tooltip_low_slope * fraction,
        )
    return _potency.expand_placeholders("{pot1}", {1: scaled}, {1: 1.0})


# =====================================================================================================================
# (0,0) A New Dawn 60110 - row 0 (level 10). eff1 MOD_CUSTOM_STAT_PCT Versatility +1/2/3%.
# =====================================================================================================================

_NEW_DAWN_NOTE = 'paladin-rework S2 HOLY section 5 (0,0): Versatility +1/2/3% (aura 306, misc 1<<21).'

a_new_dawn_r1_201240 = _rank(
    201240, 'A New Dawn', [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 0, _CR_VERSATILITY)], 1946, 10,
    "Increases your Versatility by 1%.", _NEW_DAWN_NOTE,
)
a_new_dawn_r2_201241 = _rank(
    201241, 'A New Dawn', [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 1, _CR_VERSATILITY)], 1946, 10,
    "Increases your Versatility by 2%.", _NEW_DAWN_NOTE,
)
a_new_dawn_r3_201242 = _rank(
    201242, 'A New Dawn', [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 2, _CR_VERSATILITY)], 1946, 10,
    "Increases your Versatility by 3%.", _NEW_DAWN_NOTE,
)

# =====================================================================================================================
# (0,2) Enduring Light 1744 - row 0 (level 10). eff1 MOD_CUSTOM_STAT_PCT Cooldown Haste +2/4/6% (seals excluded by
# SHARED A7's deny list).
# =====================================================================================================================

_ENDURING_NOTE = 'paladin-rework S2 HOLY section 5 (0,2): Cooldown Haste +2/4/6% (aura 306, misc 1<<22); seals excluded by SHARED A7.'

enduring_light_r1_201243 = _rank(
    201243, 'Enduring Light', [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 1, _CR_COOLDOWN_HASTE)], 2177, 10,
    "Increases your Cooldown Haste by 2%. Does not affect your Seals.", _ENDURING_NOTE,
)
enduring_light_r2_201244 = _rank(
    201244, 'Enduring Light', [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 3, _CR_COOLDOWN_HASTE)], 2177, 10,
    "Increases your Cooldown Haste by 4%. Does not affect your Seals.", _ENDURING_NOTE,
)
enduring_light_r3_201245 = _rank(
    201245, 'Enduring Light', [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 5, _CR_COOLDOWN_HASTE)], 2177, 10,
    "Increases your Cooldown Haste by 6%. Does not affect your Seals.", _ENDURING_NOTE,
)

# =====================================================================================================================
# (0,3) Illuminated Steel 60111 - row 0 (level 10). eff1 MOD_WEAPON_CRIT_PERCENT (amount from the script, bp 0),
# eff2 DUMMY 33/66/100 (percent of the spell crit gained from Intellect). Script: spell_pal_illuminated_steel.
# No spell_proc row; the DBC ProcTypeMask stays 0.
# =====================================================================================================================

_STEEL_NOTE = (
    'paladin-rework S2 HOLY section 5 (0,3): melee crit = rank% of the spell crit from Intellect; eff1 amount is set by '
    'spell_pal_illuminated_steel (DoEffectCalcAmount), eff2 DUMMY is the rank percent read by the script.'
)


def _steel(spell_id, bp, pct):
    return _rank(
        spell_id, 'Illuminated Steel', [_aura(AuraType.MOD_WEAPON_CRIT_PERCENT), _dummy(bp)], 2143, 10,
        f"Increases your melee critical strike chance by {pct}% of the spell critical strike chance you gain from "
        f"Intellect.", _STEEL_NOTE,
    )


illuminated_steel_r1_201246 = _steel(201246, 32, 33)
illuminated_steel_r2_201247 = _steel(201247, 65, 66)
illuminated_steel_r3_201248 = _steel(201248, 99, 100)

# =====================================================================================================================
# (1,3) Merciful Strikes 60112 - row 1 (level 15). eff1 DUMMY window % (4/9/14, selects 201217/18/19), eff2 DUMMY heal %
# (9/19/29). Row: Crusader Strike hits, HIT phase, DisableEffectsMask 0x2. Script: spell_pal_merciful_strikes.
# =====================================================================================================================

_MERCIFUL_NOTE = (
    'paladin-rework S2 HOLY section 5 (1,3): eff1 DUMMY = Merciful window % (selects the 201217-9 buff), eff2 DUMMY = heal %; '
    'spell_proc row (section 7) on Crusader Strike with DisableEffectsMask 0x2 (the script handles EFFECT_0).'
)


def _merciful(spell_id, rank, window_bp, window_pct, heal_bp, heal_pct):
    return _rank(
        spell_id, 'Merciful Strikes', [_dummy(window_bp), _dummy(heal_bp)], 2819, 15,
        f"Your Holy Shock increases the damage of your Crusader Strike and the direct damage of your Judgement by "
        f"{window_pct}% for 10 sec. Your Crusader Strike and Judgement hits heal up to 3 injured party or raid members "
        f"for {heal_pct}% of the damage dealt, divided evenly among them.", _MERCIFUL_NOTE,
    )


merciful_strikes_talent_r1_201249 = _merciful(201249, 1, 4, 5, 9, 10)
merciful_strikes_talent_r2_201250 = _merciful(201250, 2, 9, 10, 19, 20)
merciful_strikes_talent_r3_201251 = _merciful(201251, 3, 14, 15, 29, 30)

# =====================================================================================================================
# (2,3) Zealous Exorcism 1463 - row 2 (level 20). eff1 ADD_PCT_MODIFIER COST on Exorcism -40/-80%, eff2 DUMMY cooldown
# cut in ms (999/1999 = live 1000/2000). Row: any melee crit, DisableEffectsMask 0x1. Script: spell_pal_zealous_exorcism.
# =====================================================================================================================

_ZEALOUS_NOTE = (
    'paladin-rework S2 HOLY section 5 (2,3): eff1 COST mod on Exorcism (d1 0x2), eff2 DUMMY = ms of Exorcism cooldown cut per '
    'melee crit (stored live - 1); spell_proc row on any melee crit with DisableEffectsMask 0x1; script handles EFFECT_1.'
)


def _zealous(spell_id, cost_bp, cost_pct, ms_bp, sec):
    return _rank(
        spell_id, 'Zealous Exorcism', [_mod(SpellModOp.COST, cost_bp, pct=True), _dummy(ms_bp)], 158, 20,
        f"Your melee critical strikes reduce the remaining cooldown of your Exorcism by {sec} sec, and the mana cost of "
        f"your Exorcism is reduced by {cost_pct}%.", _ZEALOUS_NOTE, masks={1: (0, m.EXORCISM, 0)},
    )


zealous_exorcism_r1_201252 = _zealous(201252, -41, 40, 999, 1)
zealous_exorcism_r2_201253 = _zealous(201253, -81, 80, 1999, 2)

# =====================================================================================================================
# (3,3) Sunlight 60113 - row 3 (level 25). eff1 PROC_TRIGGER_SPELL -> 201232 (the rank's default handler casts it),
# eff2 DUMMY rank % (33/66/100, read by spell_pal_sunlight_hit on 201232). Row: auto attacks + Crusader Strike hits,
# DisableEffectsMask 0x2. No script on the ranks.
# =====================================================================================================================

_SUNLIGHT_NOTE = (
    'paladin-rework S2 HOLY section 5 (3,3): eff1 PROC_TRIGGER_SPELL -> Sunlight 201232 (default handler, no script), eff2 DUMMY = '
    'rank % applied by spell_pal_sunlight_hit; spell_proc row on autos + Crusader Strike, DisableEffectsMask 0x2. Tooltip keeps the '
    'literal ${...} expression of 201232 scaled by the rank fraction (section 4.1 exception).'
)
_SUNLIGHT_CAPSTONE = "Each Sunlight has a 10% chance to strike the target again."


def _sunlight(spell_id, rank, rank_bp, fraction):
    return _rank(
        spell_id, 'Sunlight', [_aura(AuraType.PROC_TRIGGER_SPELL, 0, 0, 201232), _dummy(rank_bp)], 2176, 25,
        _desc(
            f"Your melee auto attacks and Crusader Strike hits call down Sunlight on the target for "
            f"{_sunlight_damage(fraction)} Holy damage.",
            _SUNLIGHT_CAPSTONE, last=(rank == 3),
        ),
        _SUNLIGHT_NOTE,
    )


sunlight_talent_r1_201254 = _sunlight(201254, 1, 32, 0.33)
sunlight_talent_r2_201255 = _sunlight(201255, 2, 65, 0.66)
sunlight_talent_r3_201256 = _sunlight(201256, 3, 99, 1.0)

# =====================================================================================================================
# (4,3) Blessed Crusade 60114 - row 4 (level 30). eff1 ADD_PCT_MODIFIER DAMAGE on Crusader Strike +10/20/30%; rank 3 eff2
# PROC_TRIGGER_SPELL -> Crusader's Zeal 201213 with a CAST-phase 30% row on 201259 only. Data only, no script.
# =====================================================================================================================

_CRUSADE_NOTE = (
    'paladin-rework S2 HOLY section 5 (4,3): Crusader Strike damage +10/20/30% (d1 0x8000); rank 3 eff2 PROC_TRIGGER_SPELL -> '
    "Crusader's Zeal 201213, CAST-phase 30% row (section 7)."
)
_CRUSADE_CAPSTONE = (
    "Your Crusader Strike has a 30% chance to grant Crusader's Zeal, increasing your melee attack speed by 10% for 8 sec."
)


def _crusade(spell_id, rank, bp, pct):
    effects = [_mod(SpellModOp.DAMAGE, bp, pct=True)]
    if rank == 3:
        effects.append(_aura(AuraType.PROC_TRIGGER_SPELL, 0, 0, 201213))
    return _rank(
        spell_id, 'Blessed Crusade', effects, 2171, 30,
        _desc(f"Increases the damage of your Crusader Strike by {pct}%.", _CRUSADE_CAPSTONE, last=(rank == 3)),
        _CRUSADE_NOTE, masks={1: (0, m.CRUSADER_STRIKE, 0)},
    )


blessed_crusade_r1_201257 = _crusade(201257, 1, 9, 10)
blessed_crusade_r2_201258 = _crusade(201258, 2, 19, 20)
blessed_crusade_r3_201259 = _crusade(201259, 3, 29, 30)

# =====================================================================================================================
# (5,1) Light's Fervor 60115 - row 5 (level 35). eff1 DUMMY Holy Shock cooldown cut (ms, stored live - 1), eff2 DUMMY
# Crusader Strike cooldown cut. Rows: CAST phase on Holy Light / Flash of Light (r2 also Crusader Strike), DisableEffectsMask
# 0x2. Script: spell_pal_lights_fervor.
# =====================================================================================================================

_FERVOR_NOTE = (
    "paladin-rework S2 HOLY section 5 (5,1): eff1 DUMMY = Holy Shock cooldown cut ms, eff2 DUMMY = Crusader Strike cut ms (stored "
    "live - 1); CAST-phase rows (section 7), DisableEffectsMask 0x2; r2's row adds Crusader Strike (Daybreak roll). "
    "Script handles EFFECT_0."
)
_FERVOR_CAPSTONE = (
    "Your Flash of Light, Holy Light and Crusader Strike have a 10% chance to grant Daybreak, causing your next Holy Shock "
    "within 12 sec to trigger no cooldown."
)


def _fervor(spell_id, rank, shock_bp, shock_sec, cs_bp, cs_sec):
    return _rank(
        spell_id, "Light's Fervor", [_dummy(shock_bp), _dummy(cs_bp)], 2899, 35,
        _desc(
            f"Your Flash of Light and Holy Light reduce the remaining cooldown of your Holy Shock by {shock_sec} sec and "
            f"of your Crusader Strike by {cs_sec} sec.",
            _FERVOR_CAPSTONE, last=(rank == 2),
        ),
        _FERVOR_NOTE,
    )


light_s_fervor_r1_201260 = _fervor(201260, 1, 249, '0.25', 749, '0.75')
light_s_fervor_r2_201261 = _fervor(201261, 2, 499, '0.5', 1499, '1.5')

# =====================================================================================================================
# (6,2) Dawn before Dusk 60116 - row 6 (level 40). eff1 DUMMY (rank selects buff 201227/28/29). Row: CAST phase on Holy
# Light / Flash of Light (Holy Shock handled by the resolver). Script: spell_pal_dawn_before_dusk.
# =====================================================================================================================

_DAWN_NOTE = (
    'paladin-rework S2 HOLY section 5 (6,2): eff1 DUMMY (the script picks buff 201227/28/29 by rank); CAST-phase row on Holy Light '
    '/ Flash of Light (section 7); Holy Shock is handled by the resolver.'
)


def _dawn(spell_id, pct):
    return _rank(
        spell_id, 'Dawn before Dusk', [_dummy(0)], 2063, 40,
        f"Your Holy Light, Flash of Light and Holy Shock grant Dawn before Dusk for 30 sec, increasing the critical strike "
        f"chance of those spells by {pct}% per stack. Stacks up to 3 times; the next cast at 3 stacks removes it.",
        _DAWN_NOTE,
    )


dawn_before_dusk_talent_r1_201262 = _dawn(201262, 1)
dawn_before_dusk_talent_r2_201263 = _dawn(201263, 2)
dawn_before_dusk_talent_r3_201264 = _dawn(201264, 3)

# =====================================================================================================================
# (6,3) Radiant Exorcism 60117 - row 6 (level 40). eff1 ADD_PCT_MODIFIER DAMAGE on Exorcism + Hammer of Wrath +10/20/30%
# (d1 0x82). The capstone cleave is Exorcism's script (spell_pal_exorcism_radiant, bound on 879 by A3); no script here.
# =====================================================================================================================

_RADIANT_NOTE = (
    'paladin-rework S2 HOLY section 5 (6,3): Exorcism + Hammer of Wrath damage +10/20/30% (d1 0x82); rank 3 capstone is read '
    '(201267 known) by spell_pal_exorcism_radiant on Exorcism, nothing scripted on the ranks.'
)
_RADIANT_CAPSTONE = "Your Exorcism also strikes up to 2 other enemies within 8 yards of its target for 50% of its damage."


def _radiant(spell_id, rank, bp, pct):
    return _rank(
        spell_id, 'Radiant Exorcism', [_mod(SpellModOp.DAMAGE, bp, pct=True)], 177, 40,
        _desc(
            f"Increases the damage of your Exorcism and Hammer of Wrath by {pct}%.", _RADIANT_CAPSTONE, last=(rank == 3),
        ),
        _RADIANT_NOTE, masks={1: (0, m.EXORCISM | m.HAMMER_OF_WRATH, 0)},
    )


radiant_exorcism_talent_r1_201265 = _radiant(201265, 1, 9, 10)
radiant_exorcism_talent_r2_201266 = _radiant(201266, 2, 19, 20)
radiant_exorcism_talent_r3_201267 = _radiant(201267, 3, 29, 30)

# =====================================================================================================================
# (7,1) Glimmer of Light 60118 - row 7 (level 45). r1/r2 eff1 ADD_PCT_MODIFIER DAMAGE on Holy Shock (cast, damage and heal)
# +5/10%; r3 eff1 DUMMY 15 (no SpellMod - the r3 term and Mastery are read live by the Holy script). No row, no script.
# =====================================================================================================================

_GLIMMER_NOTE = (
    'paladin-rework S2 HOLY section 5 (7,1): r1/r2 eff1 SPELLMOD_DAMAGE +5/10% on HOLY_SHOCK_ALL; r3 eff1 DUMMY 15 (the 15% '
    'Holy Shock bonus is applied by ComputeShockValue / spell_pal_holy_shock_hit with Mastery added live).'
)
_GLIMMER_CAPSTONE = "Glimmer of Light's increase to your Holy Shock is also increased by your Mastery."


def _glimmer(spell_id, rank, effect, pct):
    return _rank(
        spell_id, 'Glimmer of Light', [effect], 3645, 45,
        _desc(
            f"Increases the healing and damage of your Holy Shock by {pct}%. Your Holy Shock places Glimmer of Light on "
            f"its target for 30 sec, and each Holy Shock you cast makes every one of your Glimmers pulse for 15% of the "
            f"healing or damage your Holy Shock would deal to that target - healing allies and damaging enemies. You can "
            f"maintain up to 5 Glimmers.",
            _GLIMMER_CAPSTONE, last=(rank == 3),
        ),
        _GLIMMER_NOTE, masks=({1: m.HOLY_SHOCK_ALL} if rank < 3 else None),
    )


glimmer_of_light_talent_r1_201268 = _glimmer(201268, 1, _mod(SpellModOp.DAMAGE, 4, pct=True), 5)
glimmer_of_light_talent_r2_201269 = _glimmer(201269, 2, _mod(SpellModOp.DAMAGE, 9, pct=True), 10)
glimmer_of_light_talent_r3_201270 = _glimmer(201270, 3, _dummy(14), 15)

# =====================================================================================================================
# (7,3) Shock and Awe 60119 - row 7 (level 45). eff1 DUMMY (rank selects buff 201214/15/16). Read by the resolver and
# spell_pal_shock_and_awe_buff; no row, no script on the ranks.
# =====================================================================================================================

_AWE_NOTE = (
    'paladin-rework S2 HOLY section 5 (7,3): eff1 DUMMY (the resolver picks buff 201214/15/16 by rank); no proc row, DBC '
    'ProcTypeMask stays 0.'
)
_AWE_CAPSTONE = (
    "Your damaging Holy Shock has a 25% chance to grant Awe, making your next Exorcism within 20 sec instant and increasing "
    "its damage by 30%."
)


def _awe(spell_id, rank, ap_pct, threat_pct):
    return _rank(
        spell_id, 'Shock and Awe', [_dummy(0)], 2603, 45,
        _desc(
            f"Your damaging Holy Shock increases your attack power by {ap_pct}% of your Intellect for 30 sec and, while "
            f"Righteous Fury is not active, reduces the threat you cause by {threat_pct}%.",
            _AWE_CAPSTONE, last=(rank == 3),
        ),
        _AWE_NOTE,
    )


shock_and_awe_talent_r1_201271 = _awe(201271, 1, 33, 10)
shock_and_awe_talent_r2_201272 = _awe(201272, 2, 66, 20)
shock_and_awe_talent_r3_201273 = _awe(201273, 3, 100, 30)

# =====================================================================================================================
# (8,0) Overflowing Light 60120 - row 8 (level 50). eff1 DUMMY splash % (19/39/59). Row: HIT phase critical Holy Light /
# Flash of Light heals, main target. Script: spell_pal_overflowing_light.
# =====================================================================================================================

_OVERFLOW_NOTE = (
    'paladin-rework S2 HOLY section 5 (8,0): eff1 DUMMY = splash % of the crit heal; HIT-phase row on critical Holy Light / '
    'Flash of Light heals (section 7). r3 also cuts Lay on Hands (script).'
)
_OVERFLOW_CAPSTONE = "Your Holy Light critical heals reduce the remaining cooldown of your Lay on Hands by 3 sec."


def _overflow(spell_id, rank, bp, pct):
    return _rank(
        spell_id, 'Overflowing Light', [_dummy(bp)], 1868, 50,
        _desc(
            f"When your Holy Light or Flash of Light critically heals its target, the most injured ally within 10 yards of "
            f"that target is healed for {pct}% of the amount.",
            _OVERFLOW_CAPSTONE, last=(rank == 3),
        ),
        _OVERFLOW_NOTE,
    )


overflowing_light_talent_r1_201274 = _overflow(201274, 1, 19, 20)
overflowing_light_talent_r2_201275 = _overflow(201275, 2, 39, 40)
overflowing_light_talent_r3_201276 = _overflow(201276, 3, 59, 60)

# =====================================================================================================================
# New top ranks of three kept talents (HOLY section 5): clones of the stock rank 2 spell, rewritten to the rank 3 values.
# =====================================================================================================================

# (1,2) Unyielding Faith 1628 - row 1 (level 15), clone of 25836: crit on every paladin spell/ability +3% (ALL_PALADIN),
# Light's Hammer cooldown -15 s (LIGHTS_HAMMER). SpellClassSet 10 is load-bearing (stock was 0).
unyielding_faith_r3_201277 = _rank(
    201277, 'Unyielding Faith',
    [_mod(SpellModOp.CRITICAL_CHANCE, 2), _mod(SpellModOp.COOLDOWN, -15001)], 1823, 15,
    "Increases the critical strike chance of your spells and abilities by 3%, and reduces the cooldown of your Light's "
    "Hammer by 15 sec.",
    'paladin-rework S2 HOLY section 5 (1,2): rank 3, clone of 25836 (stock rank 2); eff1 CRIT +3% on every paladin spell '
    "(ALL_PALADIN), eff2 COOLDOWN -15 s on Light's Hammer (d2 b14).",
    masks={1: m.ALL_PALADIN, 2: (0, 0, m.LIGHTS_HAMMER)},
)

# (3,1) Blessed Hands 2198 - row 3 (level 25), clone of 53661: Hand costs -30%, Hand of Salvation +100%, Hand of Sacrifice
# +10 points. The capstone buff 201238 is applied by spell_pal_blessed_hands_capstone (bound on the Hands by A3).
blessed_hands_talent_r3_201278 = _rank(
    201278, 'Blessed Hands',
    [
        _mod(SpellModOp.COST, -31, pct=True),
        _mod(SpellModOp.EFFECT1, 9),
        _mod(SpellModOp.EFFECT1, 99, pct=True),
    ],
    3022, 25,
    _desc(
        "Reduces the mana cost of your Hand of Freedom, Hand of Sacrifice and Hand of Salvation by 30%, increases the "
        "effectiveness of your Hand of Salvation by 100% and the effectiveness of your Hand of Sacrifice by an additional "
        "10%.",
        "While one of your Hand spells is on a target, your healing done to that target is increased by 15%.", last=True,
    ),
    'paladin-rework S2 HOLY section 5 (3,1): rank 3, clone of 53661 (stock rank 2); cost -30% (HAND_COSTS), Sacrifice +10 '
    'points (d0 0x2000), Salvation +100% (d0 0x100); capstone read by spell_pal_blessed_hands_capstone (201278 known).',
    masks={1: (m.HAND_COSTS[0], 0, 0), 2: (m.HAND_OF_SACRIFICE, 0, 0), 3: (m.HAND_OF_SALVATION, 0, 0)},
)

# (4,0) Pure of Heart 1742 - row 4 (level 30), clone of 31823: eff1 DUMMY mana % of Intellect (59 = live 60%, read by
# spell_pal_cleanse_holy), eff2 aura 246 Disease duration on self -30% (misc 3). Stock masks cleared.
pure_of_heart_talent_r3_201279 = _rank(
    201279, 'Pure of Heart',
    [_dummy(59), _aura(AuraType.MOD_AURA_DURATION_BY_DISPEL_NOT_STACK, -31, _MISC_SCHOOL_HOLY_DISEASE)], 2142, 30,
    _desc(
        "When your Purify or Cleanse removes a Disease or Poison effect, you restore mana equal to 60% of your Intellect "
        "every sec for 5 sec.",
        "The duration of Disease effects on you is reduced by 30%.", last=True,
    ),
    'paladin-rework S2 HOLY section 5 (4,0): rank 3, clone of 31823 (stock rank 2); eff1 DUMMY mana % of Int [TUNE] (read by '
    'spell_pal_cleanse_holy), eff2 aura 246 misc 3 -30% Disease duration on self; no class masks.',
)


# =====================================================================================================================
# spell_proc rows (HOLY section 7). Proc flags: 0x4 auto attack, 0x10 melee spell, 0x4000 magic positive. Phases: 1 CAST,
# 2 HIT. Family 10. 201206 / 20207 / the rewrites of stock rows belong to other agents.
# =====================================================================================================================

_HOLY_LIGHT_FLASH = (m.HOLY_LIGHT | m.FLASH_OF_LIGHT, 0, 0)  # (0xC0000000, 0, 0)

# Merciful Strikes: single-target Crusader Strike hits, once per CS.
for _merciful_rank in (merciful_strikes_talent_r1_201249, merciful_strikes_talent_r2_201250, merciful_strikes_talent_r3_201251):
    procs_on(
        _merciful_rank, proc_flags=0x10, family_name=10, family_mask=(0, m.CRUSADER_STRIKE, 0), spell_type_mask=1,
        spell_phase_mask=m.PROC_SPELL_PHASE_HIT, disable_effects_mask=0x2, chance=100,
    )

# Zealous Exorcism: any melee crit (autos bypass the family/phase checks); the script guards once per Spell*.
for _zealous_rank in (zealous_exorcism_r1_201252, zealous_exorcism_r2_201253):
    procs_on(
        _zealous_rank, proc_flags=0x14, spell_type_mask=1, spell_phase_mask=m.PROC_SPELL_PHASE_HIT,
        hit_mask=m.PROC_HIT_CRITICAL, disable_effects_mask=0x1, chance=100,
    )

# Sunlight: auto attacks (bypass the family mask) and Crusader Strike hits; eff1's default handler casts 201232.
for _sunlight_rank in (sunlight_talent_r1_201254, sunlight_talent_r2_201255, sunlight_talent_r3_201256):
    procs_on(
        _sunlight_rank, proc_flags=0x14, family_name=10, family_mask=(0, m.CRUSADER_STRIKE, 0), spell_type_mask=1,
        spell_phase_mask=m.PROC_SPELL_PHASE_HIT, disable_effects_mask=0x2, chance=100,
    )

# Blessed Crusade rank 3: every Crusader Strike cast, 30% (data only; triggers Crusader's Zeal 201213).
procs_on(
    blessed_crusade_r3_201259, proc_flags=0x10, family_name=10, family_mask=(0, m.CRUSADER_STRIKE, 0),
    spell_phase_mask=m.PROC_SPELL_PHASE_CAST, chance=30,
)

# Light's Fervor: r1 Holy Light / Flash of Light casts, r2 adds Crusader Strike (Daybreak roll only).
procs_on(
    light_s_fervor_r1_201260, proc_flags=0x4000, family_name=10, family_mask=_HOLY_LIGHT_FLASH,
    spell_phase_mask=m.PROC_SPELL_PHASE_CAST, disable_effects_mask=0x2, chance=100,
)
procs_on(
    light_s_fervor_r2_201261, proc_flags=0x4000 | 0x10, family_name=10, family_mask=(m.HOLY_LIGHT | m.FLASH_OF_LIGHT, m.CRUSADER_STRIKE, 0),
    spell_phase_mask=m.PROC_SPELL_PHASE_CAST, disable_effects_mask=0x2, chance=100,
)

# Dawn before Dusk: Holy Light / Flash of Light casts (Holy Shock is handled by the resolver).
for _dawn_rank in (dawn_before_dusk_talent_r1_201262, dawn_before_dusk_talent_r2_201263, dawn_before_dusk_talent_r3_201264):
    procs_on(
        _dawn_rank, proc_flags=0x4000, family_name=10, family_mask=_HOLY_LIGHT_FLASH,
        spell_phase_mask=m.PROC_SPELL_PHASE_CAST, chance=100,
    )

# Overflowing Light: critical Holy Light / Flash of Light heals, HIT phase, main target.
for _overflow_rank in (overflowing_light_talent_r1_201274, overflowing_light_talent_r2_201275, overflowing_light_talent_r3_201276):
    procs_on(
        _overflow_rank, proc_flags=0x4000, family_name=10, family_mask=_HOLY_LIGHT_FLASH, spell_type_mask=2,
        spell_phase_mask=m.PROC_SPELL_PHASE_HIT, hit_mask=m.PROC_HIT_CRITICAL, chance=100,
    )


# =====================================================================================================================
# Script bindings (HOLY section 2.7). Sunlight ranks have no script (default PROC_TRIGGER_SPELL handler); Blessed Crusade
# rank 3 is data only.
# =====================================================================================================================

for _steel_rank in (illuminated_steel_r1_201246, illuminated_steel_r2_201247, illuminated_steel_r3_201248):
    scripted_by(_steel_rank, 'spell_pal_illuminated_steel')
for _merciful_rank in (merciful_strikes_talent_r1_201249, merciful_strikes_talent_r2_201250, merciful_strikes_talent_r3_201251):
    scripted_by(_merciful_rank, 'spell_pal_merciful_strikes')
for _zealous_rank in (zealous_exorcism_r1_201252, zealous_exorcism_r2_201253):
    scripted_by(_zealous_rank, 'spell_pal_zealous_exorcism')
for _fervor_rank in (light_s_fervor_r1_201260, light_s_fervor_r2_201261):
    scripted_by(_fervor_rank, 'spell_pal_lights_fervor')
for _dawn_rank in (dawn_before_dusk_talent_r1_201262, dawn_before_dusk_talent_r2_201263, dawn_before_dusk_talent_r3_201264):
    scripted_by(_dawn_rank, 'spell_pal_dawn_before_dusk')
for _overflow_rank in (overflowing_light_talent_r1_201274, overflowing_light_talent_r2_201275, overflowing_light_talent_r3_201276):
    scripted_by(_overflow_rank, 'spell_pal_overflowing_light')
