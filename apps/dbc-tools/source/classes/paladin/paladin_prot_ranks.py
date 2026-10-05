"""
Paladin - Protection talent rank spells (paladin-rework S3, WP-A2c).

Source of truth: .agents/plans/paladin-rework/paladin-rework.PROTECTION.md section 2.1 (ids 201320-201355), section 4
(common rules, DUMMY = APPLY_AURA DUMMY, section 4.3 / 4.4 / 4.6 DBC fields), section 5 (talent table: effects, masks),
section 5.1 (per-rank tooltips), section 7 (spell_proc rows) and section 2.7 (script bindings).

Declared here, in id order (variable names `<talent>_<id>`):
    201320-201322 Improved Auras                 201337-201338 Improved Blessing of Sanctuary
    201323-201325 Improved Consecration          201339-201340 Shield Discipline
    201326-201328 Sanctified Resolve             201341-201342 Vengeful Bulwark
    201329-201330 Improved Seal of Command       201343-201345 Radiant Bulwark
    201331-201332 Improved Hammer of the         201346-201347 Bulwark of Faith
                  Righteous                      201348-201350 Inner Light
    201333-201334 Light's Reservoir              201351-201352 Light's Defender
    201335-201336 Consecrated Shield             201353-201355 Avenging Light

Every rank is a hidden passive (attributes 0x1D0, duration -1, RangeIndex 1, target 1, no family bits, SpellClassSet 10 so
a SpellMod never leaks into another family, never icon 25). Stored base_points are live - 1 (die_sides 1); a DUMMY effect
with a spell_proc row carries trigger_spell 0 / misc 0 (PROTECTION section 4, X5) and the row's DisableEffectsMask names
the value-only effects. SpellLevel is the talent row's learn level (row N -> 10 + 5N). Tooltips are the section 5.1 text
with literal per-rank numbers; the capstone format is "<text>\\n\\n|cFF9D9D9DCapstone Bonus: <capstone>|r" below the last
rank and the same without colour on the last rank.

The rank objects are module-level variables; paladin_talents.py (A3) imports them. The helper spells (Bulwark grant
201361, Light's Reservoir heal 201373, ...) belong to paladin_prot_spells.py (A2a) and paladin_trigger_spells.py and are
referenced by bare id, except Improved Seal of Command's tooltip, which needs the DoT's `pot_text` and therefore imports
201371 from paladin_prot_spells.py.

Notes below number effects 1-based (eff1 = the spec's eff0).

Effect class masks: `EffectSpellClassMask{A,B,C}_{1,2,3}` - the LETTER is the effect index (A = effect 1) and the digit
the dword (lib/dbcfmt.py:130-143), set through `_rank(masks={effect_index: (d0, d1, d2)})`.
"""

from lib.dsl import AuraType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import pot_text, procs_on, scripted_by, spell

from . import _masks as m
from .paladin_prot_spells import improved_soc_dot_201371


# --- helpers -------------------------------------------------------------------------------------------------------

_MASK_KEYS = {1: 'A', 2: 'B', 3: 'C'}

_BULWARK_GRANT = 201361  # Bulwark "+1 stack" granter (A2a, paladin_prot_spells.py), referenced by bare id

_CR_VERSATILITY = 1 << 21  # 1 << CombatRating.VERSATILITY
_MISC_SCHOOL_ALL = 127  # aura 87 misc: every school
_MISC_SCHOOL_MAGIC = 126  # aura 87 misc: magic schools (Holy..Arcane)


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


def _grant_proc():
    """PROC_TRIGGER_SPELL -> Bulwark grant 201361 (the rank's default handler casts it; bare-int trigger id)."""
    return _aura(AuraType.PROC_TRIGGER_SPELL, 0, 0, _BULWARK_GRANT)


def _desc(text, capstone=None, last=False):
    """PROTECTION section 5.1 tooltip rule: grey capstone line on every rank below the last, plain on the last."""
    if capstone is None:
        return text
    if last:
        return f"{text}\n\nCapstone Bonus: {capstone}"
    return f"{text}\n\n|cFF9D9D9DCapstone Bonus: {capstone}|r"


def _rank(spell_id, name, effects, icon, level, description, notes, masks=None, extra_raw=None):
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
    raw.update(extra_raw or {})
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=464,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1,
        effects=effects, spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


# =====================================================================================================================
# (0,0) Improved Auras 60125 - row 0 (level 10). eff1 ADD_FLAT DURATION +2/4/6 s on the aura bursts (AB); r3 eff2
# ADD_FLAT GLOBAL_COOLDOWN -500 ms on the Aura abilities (AURA, d2 0x20 = the load-time hardcode bit).
# =====================================================================================================================

_AURAS_NOTE = (
    'paladin-rework S3 PROTECTION section 5 (0,0): eff1 DURATION +2/4/6 s (bp 1999/3999/5999) mask AURA_BURST; r3 eff2 '
    'GLOBAL_COOLDOWN -500 ms (bp -501) mask AURA, 1.5 s -> 1.0 s (floor 1000).'
)
_AURAS_CAPSTONE = "The global cooldown of your Aura abilities is reduced to 1 sec."


def _improved_auras(spell_id, rank, bp, sec):
    effects = [_mod(SpellModOp.DURATION, bp)]
    masks = {1: m.AURA_BURSTS}
    if rank == 3:
        effects.append(_mod(SpellModOp.GLOBAL_COOLDOWN, -501))
        masks[2] = (0, 0, m.AURA)
    return _rank(
        spell_id, 'Improved Auras', effects, 2136, 10,
        _desc(
            f"Increases the duration of your Aura active effects by {sec} sec.", _AURAS_CAPSTONE, last=(rank == 3),
        ),
        _AURAS_NOTE, masks=masks,
    )


improved_auras_201320 = _improved_auras(201320, 1, 1999, 2)
improved_auras_201321 = _improved_auras(201321, 2, 3999, 4)
improved_auras_201322 = _improved_auras(201322, 3, 5999, 6)

# =====================================================================================================================
# (0,1) Improved Consecration 60126 - row 0 (level 10). eff1 MOD_DAMAGE_PERCENT_TAKEN (all schools) -1/2/3%, eff2 DUMMY
# slow 6/13/20% (read by spell_pal_improved_consecration_slow; the instant tick is the Consecration hook). No row.
# =====================================================================================================================

_CONSECRATION_NOTE = (
    'paladin-rework S3 PROTECTION section 5 (0,1): eff1 aura 87 misc 127 bp -2/-3/-4 (live -1/-2/-3%), eff2 DUMMY bp 5/12/19 '
    '(live slow 6/13/20%, read by spell_pal_improved_consecration_slow); the instant tick is Paladin::RegisterProtectionHooks.'
)


def _improved_consecration(spell_id, dr_bp, dr_pct, slow_bp, slow_pct):
    return _rank(
        spell_id, 'Improved Consecration',
        [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, dr_bp, _MISC_SCHOOL_ALL), _dummy(slow_bp)], 51, 10,
        f"Reduces all damage you take by {dr_pct}%. Your Consecration deals one tick of damage immediately when cast, and "
        f"enemies it hits have their melee attack speed slowed by {slow_pct}% for 15 sec.",
        _CONSECRATION_NOTE,
    )


improved_consecration_201323 = _improved_consecration(201323, -2, 1, 5, 6)
improved_consecration_201324 = _improved_consecration(201324, -3, 2, 12, 13)
improved_consecration_201325 = _improved_consecration(201325, -4, 3, 19, 20)

# =====================================================================================================================
# (1,0) Sanctified Resolve 1748 - row 1 (level 15). eff1 MOD_CUSTOM_STAT_PCT Versatility +1/2/3% (bp 0/1/2).
# =====================================================================================================================

_RESOLVE_NOTE = 'paladin-rework S3 PROTECTION section 5 (1,0): Versatility +1/2/3% (aura 306, misc 1<<21, bp 0/1/2).'


def _sanctified_resolve(spell_id, bp, pct):
    return _rank(
        spell_id, 'Sanctified Resolve', [_aura(AuraType.MOD_CUSTOM_STAT_PCT, bp, _CR_VERSATILITY)], 2213, 15,
        f"Increases your Versatility by {pct}%.", _RESOLVE_NOTE,
    )


sanctified_resolve_201326 = _sanctified_resolve(201326, 0, 1)
sanctified_resolve_201327 = _sanctified_resolve(201327, 1, 2)
sanctified_resolve_201328 = _sanctified_resolve(201328, 2, 3)

# =====================================================================================================================
# (1,1) Improved Seal of Command 1425 - row 1 (level 15). eff1 ADD_PCT DAMAGE +15/30% on COMMAND_ALL (C | CU); r2 eff2
# DUMMY marker for the capstone DoT (spell_pal_improved_soc_dot reads rank 2 known). No row.
# =====================================================================================================================

_SOC_NOTE = (
    'paladin-rework S3 PROTECTION section 5 (1,1): eff1 DAMAGE +15/30% (bp 14/29) on COMMAND_ALL (C d2 0x400 | CU d2 0x80000); '
    'r2 eff2 DUMMY bp 0 = capstone marker (DoT 201371 cast by spell_pal_improved_soc_dot).'
)


def _improved_soc(spell_id, rank, bp, pct):
    effects = [_mod(SpellModOp.DAMAGE, bp, pct=True)]
    if rank == 2:
        effects.append(_dummy(0))
    return _rank(
        spell_id, 'Improved Seal of Command', effects, 561, 15,
        _desc(
            f"Increases the damage of your Seal of Command's passive effect and its unleash by {pct}%.",
            f"Your Seal of Command unleash also deals {pot_text(improved_soc_dot_201371)} Holy and Fire damage to each "
            f"target every 2 sec for 6 sec.",
            last=(rank == 2),
        ),
        _SOC_NOTE, masks={1: m.COMMAND_ALL},
    )


improved_seal_of_command_201329 = _improved_soc(201329, 1, 14, 15)
improved_seal_of_command_201330 = _improved_soc(201330, 2, 29, 30)

# =====================================================================================================================
# (3,0) Improved Hammer of the Righteous 60127 - row 3 (level 25). eff1 ADD_FLAT JUMP_TARGETS +2 (bp 1, both ranks), eff2
# ADD_PCT DAMAGE +10/20% (bp 9/19); both on Hammer of the Righteous (d1 0x40000).
# =====================================================================================================================

_IHOTR_NOTE = (
    'paladin-rework S3 PROTECTION section 5 (3,0): eff1 JUMP_TARGETS bp 1 (+2 targets, both ranks), eff2 DAMAGE bp 9/19 '
    '(+10/20%); both masks (0, HAMMER_OF_THE_RIGHTEOUS, 0).'
)


def _improved_hotr(spell_id, bp, pct):
    return _rank(
        spell_id, 'Improved Hammer of the Righteous',
        [_mod(SpellModOp.JUMP_TARGETS, 1), _mod(SpellModOp.DAMAGE, bp, pct=True)], 439, 25,
        f"Your Hammer of the Righteous strikes 2 additional targets and deals {pct}% more damage.", _IHOTR_NOTE,
        masks={1: (0, m.HAMMER_OF_THE_RIGHTEOUS, 0), 2: (0, m.HAMMER_OF_THE_RIGHTEOUS, 0)},
    )


improved_hammer_of_the_righteous_201331 = _improved_hotr(201331, 9, 10)
improved_hammer_of_the_righteous_201332 = _improved_hotr(201332, 19, 20)

# =====================================================================================================================
# (3,1) Light's Reservoir 1521 - row 3 (level 25). eff1 DUMMY 15/30% of the heal (bp 14/29). Row (section 7): Holy Light /
# Flash of Light, HIT phase, self casts only (CheckProc). Script spell_pal_lights_reservoir -> heal 201373.
# =====================================================================================================================

_RESERVOIR_NOTE = (
    "paladin-rework S3 PROTECTION section 5 (3,1): eff1 DUMMY bp 14/29 (live 15/30% of the total heal); spell_proc row on "
    "Holy Light / Flash of Light (HL_FOL), HIT phase; spell_pal_lights_reservoir casts 201373 on another party member."
)


def _lights_reservoir(spell_id, bp, pct):
    return _rank(
        spell_id, "Light's Reservoir", [_dummy(bp)], 3033, 25,
        f"Your Holy Light and Flash of Light cast on yourself also heal another party member within 30 yards, lowest "
        f"health first, for {pct}% of the amount healed.",
        _RESERVOIR_NOTE,
    )


lights_reservoir_201333 = _lights_reservoir(201333, 14, 15)
lights_reservoir_201334 = _lights_reservoir(201334, 29, 30)

# =====================================================================================================================
# (4,2) Consecrated Shield 1426 - row 4 (level 30). eff1 ADD_FLAT EFFECT3 -5/-10 (bp -6/-11) on Holy Shield (d1 0x40): its
# eff2 is aura 87 misc 126 (magic damage taken). No row.
# =====================================================================================================================

_CSHIELD_NOTE = (
    'paladin-rework S3 PROTECTION section 5 (4,2): eff1 EFFECT3 bp -6/-11 (-5/-10% on Holy Shield eff2) mask (0, HOLY_SHIELD, 0).'
)


def _consecrated_shield(spell_id, bp, pct):
    return _rank(
        spell_id, 'Consecrated Shield', [_mod(SpellModOp.EFFECT3, bp)], 1880, 30,
        f"While your Holy Shield is active, magic damage you take is reduced by {pct}%.", _CSHIELD_NOTE,
        masks={1: (0, m.HOLY_SHIELD, 0)},
    )


consecrated_shield_201335 = _consecrated_shield(201335, -6, 5)
consecrated_shield_201336 = _consecrated_shield(201336, -11, 10)

# =====================================================================================================================
# (4,3) Improved Blessing of Sanctuary 60128 - row 4 (level 30). eff1 DUMMY DR +1/2% (bp 0/1), eff2 DUMMY mana +50/100%
# (bp 49/99); read by spell_pal_blessing_of_sanctuary_prot. No row, no script on the ranks.
# =====================================================================================================================

_IBOS_NOTE = (
    'paladin-rework S3 PROTECTION section 5 (4,3): eff1 DUMMY bp 0/1 (+1/2% DR), eff2 DUMMY bp 49/99 (+50/100% mana), both read '
    'by spell_pal_blessing_of_sanctuary_prot (20911 / 25899); no proc.'
)


def _improved_bos(spell_id, dr_bp, dr_pct, mana_bp, mana_pct):
    return _rank(
        spell_id, 'Improved Blessing of Sanctuary', [_dummy(dr_bp), _dummy(mana_bp)], 1804, 30,
        f"Increases the damage reduction of your Blessing of Sanctuary by {dr_pct}% and the mana it returns by "
        f"{mana_pct}%.",
        _IBOS_NOTE,
    )


improved_blessing_of_sanctuary_201337 = _improved_bos(201337, 0, 1, 49, 50)
improved_blessing_of_sanctuary_201338 = _improved_bos(201338, 1, 2, 99, 100)

# =====================================================================================================================
# (5,3) Shield Discipline 60129 - row 5 (level 35). eff1 MOD_SHIELD_BLOCKVALUE_PCT +10/20% (bp 9/19), eff2 ADD_FLAT CHARGES
# +2/+4 (bp 1/3) on Holy Shield (d1 0x40). No row.
# =====================================================================================================================

_SDISC_NOTE = (
    'paladin-rework S3 PROTECTION section 5 (5,3): eff1 aura 150 bp 9/19 (block value +10/20%), eff2 CHARGES bp 1/3 (+2/+4) mask '
    '(0, HOLY_SHIELD, 0).'
)


def _shield_discipline(spell_id, bv_bp, bv_pct, ch_bp, charges):
    return _rank(
        spell_id, 'Shield Discipline',
        [_aura(AuraType.MOD_SHIELD_BLOCKVALUE_PCT, bv_bp), _mod(SpellModOp.CHARGES, ch_bp)], 2007, 35,
        f"Increases your block value by {bv_pct}% and the number of Holy Shield charges by {charges}.", _SDISC_NOTE,
        masks={2: (0, m.HOLY_SHIELD, 0)},
    )


shield_discipline_201339 = _shield_discipline(201339, 9, 10, 1, 2)
shield_discipline_201340 = _shield_discipline(201340, 19, 20, 3, 4)

# =====================================================================================================================
# (7,1) Vengeful Bulwark 60130 - row 7 (level 45). eff1 PROC_TRIGGER_SPELL -> Bulwark grant 201361. Row: Shield of
# Righteousness casts (CAST phase), ICD 12 / 8 s by rank. Default handler, no script.
# =====================================================================================================================

_VENGEFUL_NOTE = (
    'paladin-rework S3 PROTECTION section 5 (7,1): eff1 PROC_TRIGGER_SPELL -> 201361 (default handler); row (section 7) on '
    'Shield of Righteousness casts (d1 0x100000), CAST phase, ICD 12000 / 8000.'
)


def _vengeful_bulwark(spell_id, sec):
    return _rank(
        spell_id, 'Vengeful Bulwark', [_grant_proc()], 3031, 45,
        f"Your Shield of Righteousness also grants a stack of Bulwark. This effect cannot occur more than once every "
        f"{sec} sec.",
        _VENGEFUL_NOTE,
    )


vengeful_bulwark_201341 = _vengeful_bulwark(201341, 12)
vengeful_bulwark_201342 = _vengeful_bulwark(201342, 8)

# =====================================================================================================================
# (8,0) Radiant Bulwark 60131 - row 8 (level 50). eff1 DUMMY bp 16/32/49 (live 17/33/50% of the overheal, user ruling F4).
# DBC ProcTypeMask 0x4000. Row: Holy Light heals (HIT). Script spell_pal_radiant_bulwark (CheckProc + absorb 201363).
# =====================================================================================================================

_RADIANT_NOTE = (
    'paladin-rework S3 PROTECTION section 4.3 / 5 (8,0): eff1 DUMMY bp 16/32/49 (live 17/33/50% absorb of the overheal, user '
    'ruling 2026-10-03 F4), DBC ProcTypeMask 0x4000; row on Holy Light heals; spell_pal_radiant_bulwark.'
)


def _radiant_bulwark(spell_id, bp, pct):
    return _rank(
        spell_id, 'Radiant Bulwark', [_dummy(bp)], 1801, 50,
        f"At 5 stacks of Bulwark, your next Holy Light becomes instant and costs no mana, on any target. If that Holy "
        f"Light heals you, its overhealing grants you an absorb shield equal to {pct}% of the excess, up to 50% of your "
        f"maximum health, for 10 sec. A larger shield replaces a smaller one.",
        _RADIANT_NOTE, extra_raw={'ProcTypeMask': 0x4000},
    )


radiant_bulwark_201343 = _radiant_bulwark(201343, 16, 17)
radiant_bulwark_201344 = _radiant_bulwark(201344, 32, 33)
radiant_bulwark_201345 = _radiant_bulwark(201345, 49, 50)

# =====================================================================================================================
# (8,2) Bulwark of Faith 2194 - row 8 (level 50). eff1 MOD_DAMAGE_PERCENT_TAKEN misc 126 (magic) bp -4/-7 (live -3/6%); r2
# eff2 PROC_TRIGGER_SPELL -> 201361. Row 201347 only (magic damage taken, direct + periodic, 6 s ICD).
# =====================================================================================================================

_FAITH_NOTE = (
    'paladin-rework S3 PROTECTION section 5 (8,2): eff1 aura 87 misc 126 bp -4/-7 (live -3/-6% magic damage taken); r2 eff2 '
    'PROC_TRIGGER_SPELL -> 201361; row 201347 (school 126, 0xA2000, AttributesMask 0x2, DisableEffectsMask 0x1, ICD 6000).'
)
_FAITH_CAPSTONE = "Taking magic damage grants a stack of Bulwark. This effect cannot occur more than once every 6 sec."


def _bulwark_of_faith(spell_id, rank, bp, pct):
    effects = [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, bp, _MISC_SCHOOL_MAGIC)]
    if rank == 2:
        effects.append(_grant_proc())
    return _rank(
        spell_id, 'Bulwark of Faith', effects, 3026, 50,
        _desc(f"Reduces the magic damage you take by {pct}%.", _FAITH_CAPSTONE, last=(rank == 2)), _FAITH_NOTE,
    )


bulwark_of_faith_201346 = _bulwark_of_faith(201346, 1, -4, 3)
bulwark_of_faith_201347 = _bulwark_of_faith(201347, 2, -7, 6)

# =====================================================================================================================
# (8,3) Inner Light 60132 - row 8 (level 50). eff1 ADD_PCT DAMAGE +5/10/15% (bp 4/9/14) on Shield of Righteousness (d1
# 0x100000). No row.
# =====================================================================================================================

_INNER_NOTE = 'paladin-rework S3 PROTECTION section 5 (8,3): eff1 DAMAGE bp 4/9/14 (+5/10/15%) mask (0, SHIELD_OF_RIGHTEOUSNESS, 0).'


def _inner_light(spell_id, bp, pct):
    return _rank(
        spell_id, 'Inner Light', [_mod(SpellModOp.DAMAGE, bp, pct=True)], 329, 50,
        f"Increases the damage of your Shield of Righteousness by {pct}%.", _INNER_NOTE,
        masks={1: (0, m.SHIELD_OF_RIGHTEOUSNESS, 0)},
    )


inner_light_201348 = _inner_light(201348, 4, 5)
inner_light_201349 = _inner_light(201349, 9, 10)
inner_light_201350 = _inner_light(201350, 14, 15)

# =====================================================================================================================
# (9,1) Light's Defender 60150 - row 9 (level 55). eff1 ADD_FLAT DURATION +2/4 s (bp 1999/3999), eff2 ADD_PCT DAMAGE +50/100%
# (bp 49/99); both on Holy Shield (d1 0x40). No row.
# =====================================================================================================================

_DEFENDER_NOTE = (
    "paladin-rework S3 PROTECTION section 5 (9,1): eff1 DURATION bp 1999/3999 (+2/4 s), eff2 DAMAGE bp 49/99 (+50/100%); both "
    "masks (0, HOLY_SHIELD, 0)."
)


def _lights_defender(spell_id, dur_bp, sec, dmg_bp, pct):
    return _rank(
        spell_id, "Light's Defender", [_mod(SpellModOp.DURATION, dur_bp), _mod(SpellModOp.DAMAGE, dmg_bp, pct=True)], 2430, 55,
        f"Increases the duration of your Holy Shield by {sec} sec and its Holy damage by {pct}%.", _DEFENDER_NOTE,
        masks={1: (0, m.HOLY_SHIELD, 0), 2: (0, m.HOLY_SHIELD, 0)},
    )


lights_defender_201351 = _lights_defender(201351, 1999, 2, 49, 50)
lights_defender_201352 = _lights_defender(201352, 3999, 4, 99, 100)

# =====================================================================================================================
# (9,2) Avenging Light 2200 - row 9 (level 55). eff1 DUMMY bp 0; DBC ProcChance 3/6/10 (user ruling F3), ProcTypeMask
# 0x2A8. Row: Holy Shield blocks (HitMask 0x40), 10 s ICD. Script spell_pal_avenging_light.
# =====================================================================================================================

_AVENGING_NOTE = (
    'paladin-rework S3 PROTECTION section 4.6 / 5 (9,2): eff1 DUMMY bp 0, DBC ProcChance 3/6/10 (user ruling 2026-10-03 F3), '
    'ProcTypeMask 0x2A8; row (section 7) HitMask 0x40, ICD 10000; spell_pal_avenging_light.'
)


def _avenging_light(spell_id, chance):
    return _rank(
        spell_id, 'Avenging Light', [_dummy(0)], 1951, 55,
        f"Your Holy Shield blocks have a {chance}% chance to reset the cooldown of your Avenger's Shield and make your "
        f"next Avenger's Shield throw three shields. This effect cannot occur more than once every 10 sec.",
        _AVENGING_NOTE, extra_raw={'ProcChance': chance, 'ProcTypeMask': 0x2A8},
    )


avenging_light_201353 = _avenging_light(201353, 3)
avenging_light_201354 = _avenging_light(201354, 6)
avenging_light_201355 = _avenging_light(201355, 10)


# =====================================================================================================================
# spell_proc rows (PROTECTION section 7). Proc flags: 0x10 DONE spell melee, 0x4000 DONE magic pos, 0x2A8 TAKEN melee /
# ranged, 0xA2000 TAKEN magic / periodic. Phases: 1 CAST, 2 HIT. Family 10. Redoubt, Touched by the Light, Anticipation and
# the helper rows belong to other agents.
# =====================================================================================================================

# Light's Reservoir: Holy Light / Flash of Light heals, HIT phase; self casts only (CheckProc).
for _reservoir_rank in (lights_reservoir_201333, lights_reservoir_201334):
    procs_on(
        _reservoir_rank, proc_flags=0x4000, family_name=10, family_mask=m.HL_FOL, spell_type_mask=2,
        spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100,
    )

# Vengeful Bulwark: every Shield of Righteousness cast (CAST phase, hit mask 0 skips the hit check), ICD 12 / 8 s.
for _vengeful_rank, _icd in ((vengeful_bulwark_201341, 12000), (vengeful_bulwark_201342, 8000)):
    procs_on(
        _vengeful_rank, proc_flags=0x10, family_name=10, family_mask=(0, m.SHIELD_OF_RIGHTEOUSNESS, 0),
        spell_phase_mask=m.PROC_SPELL_PHASE_CAST, chance=100, cooldown_ms=_icd,
    )

# Radiant Bulwark: Holy Light heals (CheckProc: the free instant Holy Light on self with overheal).
for _radiant_rank in (radiant_bulwark_201343, radiant_bulwark_201344, radiant_bulwark_201345):
    procs_on(
        _radiant_rank, proc_flags=0x4000, family_name=10, family_mask=(m.HOLY_LIGHT, 0, 0), spell_type_mask=2,
        spell_phase_mask=m.PROC_SPELL_PHASE_HIT, chance=100,
    )

# Bulwark of Faith rank 2: magic damage taken, direct + periodic, triggered NPC spells count, 6 s ICD; eff1 is the DR aura.
procs_on(
    bulwark_of_faith_201347, proc_flags=0xA2000, school_mask=126, spell_type_mask=1,
    spell_phase_mask=m.PROC_SPELL_PHASE_HIT, attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC, disable_effects_mask=0x1,
    chance=100, cooldown_ms=6000,
)

# Avenging Light: Holy Shield blocks (HitMask BLOCK), chance = the rank's DBC ProcChance, 10 s ICD.
for _avenging_rank in (avenging_light_201353, avenging_light_201354, avenging_light_201355):
    procs_on(
        _avenging_rank, proc_flags=0x2A8, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, hit_mask=0x40, chance=0,
        cooldown_ms=10000,
    )


# =====================================================================================================================
# Script bindings (PROTECTION section 2.7). Vengeful Bulwark and Bulwark of Faith use the default PROC_TRIGGER_SPELL handler
# (no script on the ranks); the Bulwark grant is 201361's own script (A2a).
# =====================================================================================================================

for _reservoir_rank in (lights_reservoir_201333, lights_reservoir_201334):
    scripted_by(_reservoir_rank, 'spell_pal_lights_reservoir')
for _radiant_rank in (radiant_bulwark_201343, radiant_bulwark_201344, radiant_bulwark_201345):
    scripted_by(_radiant_rank, 'spell_pal_radiant_bulwark')
for _avenging_rank in (avenging_light_201353, avenging_light_201354, avenging_light_201355):
    scripted_by(_avenging_rank, 'spell_pal_avenging_light')
