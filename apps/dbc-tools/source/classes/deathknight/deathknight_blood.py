"""
Death Knight - S1a Blood: new rows 203120-203137 (Crimson Resolve, Marrowrend, Thick Blood, Gorefiend's Grasp,
Sanguine Ground, Crimson Scourge) plus the three tooltip_vars entries 1250 / 1251 / 1252 and the consts they own.
Source of truth: docs/reworks/death-knight-blood-rework.md and .agents/plans/death-knight-rework/death-knight-rework.S1a-WP-BRIEF.md.

SkillLineAbility rows 30740-30742 (Marrowrend, Gorefiend's Grasp, Crimson Communion) are bundled by granted_by_talent in
deathknight_talents.py; this file only provides the castable spells. Talent rank spells are hidden passives (attributes
0x1D0, the A New Dawn shape); a rank's SpellLevel is 9 + 5 x talent row + its rank (brief D3).
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    bonus_coefficients, const, procs_on, scripted_by, spell, spell_rune_cost, talent_mult, tooltip_vars,
)

from . import _masks as m

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_DO_NOT_SHEATH = 0x40000
_ATTR0_TALENT_PASSIVE = 464                         # ABILITY 0x10 | PASSIVE 0x40 | DO_NOT_DISPLAY 0x80 | DO_NOT_LOG 0x100
_ATTR2_IGNORE_LOS = 0x4
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_NO_INITIAL_AGGRO = 0x20000                   # SPELL_ATTR3_SUPPRESS_TARGET_PROCS, TITLE "No initial aggro"
_ATTR3_ALWAYS_HIT = 0x40000
_SPELLFAMILY_DEATHKNIGHT = 15
_MECHANIC_GRIP = 6                                  # Mechanics::MECHANIC_GRIP (Death Grip's spell mechanic)

# ---- Aura / misc values / targets ----
_AURA_MOD_CUSTOM_STAT_PCT = int(AuraType.MOD_CUSTOM_STAT_PCT)           # 306, misc = 1 << CR_*
_AURA_MOD_TOTAL_STAT_PERCENTAGE = int(AuraType.MOD_TOTAL_STAT_PERCENTAGE)  # 137, misc = Stats (STAT_STAMINA 2)
_CR_VERSATILITY = 1 << 21
_STAT_STAMINA = 2
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_UNIT_TARGET_ANY = 25
_TARGET_DEST_TARGET_ANY = 63

# ---- spell_proc masks (src/server/game/Spells/SpellMgr.h) ----
_PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x4
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x4000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x10000
_PROC_SPELL_TYPE_ALL = 0x7
_PROC_SPELL_PHASE_CAST = 0x1
_PROC_ATTR_REQ_SPELLMOD = 0x8

# ---- Learn levels (S1-HANDOFF section 3: row N, rank R -> 9 + 5 N + R; brief D3) ----
_LEVEL_MARROWREND = 20           # row 2
_LEVEL_GOREFIENDS_GRASP = 30     # row 4
_LEVEL_SANGUINE_GROUND = 35      # row 5 rank 1


def _rank_level(row, rank):
    return 9 + 5 * row + rank


# =====================================================================================================================
# Script numbers (D8 tier 3: not tooltip numbers, not potency); C++ reads them as DeathKnightData::<NAME>
# =====================================================================================================================

MARROWREND_CHARGES = const(
    'MARROWREND_CHARGES', 3, 'Bone Shield charges one Marrowrend cast grants (the shield caps at 6) [tune].',
)
MARROWREND_CAP_BONUS_PCT = const(
    'MARROWREND_CAP_BONUS_PCT', 20,
    'Percent more damage Marrowrend deals while the Death Knight already has the maximum Bone Shield charges [tune].',
)
SANGUINE_HEAL_PCT = const(
    'SANGUINE_HEAL_PCT', 1,
    'Percent of maximum health each Sanguine Ground tick heals while standing in the Death Knight\'s own Death and '
    'Decay [fixed].',
)
RED_THIRST_MS_PER_10_RP = const(
    'RED_THIRST_MS_PER_10_RP', 500,
    'Milliseconds Red Thirst (Thick Blood capstone) takes off the remaining Vampiric Blood cooldown per 10 Runic Power '
    'spent, in real time (Cooldown Haste does not scale it) [fixed].',
)
GOREFIENDS_GRASP_RADIUS = const(
    'GOREFIENDS_GRASP_RADIUS', 15,
    'Yards around Gorefiend\'s Grasp\'s target inside which engaged enemies are pulled; the spell effect\'s radius_yards '
    'is the same number [tune].',
)

# =====================================================================================================================
# tooltip_vars (U24: unconditional Blood-tree % talents only; ids 1250-1252 from source/ids.yaml)
# =====================================================================================================================
# Declared up here so deathknight_trigger_spells.py (Heart Strike, Blood Boil, Death Strike) and deathknight_spells.py
# (Death and Decay) can import them from `.deathknight_blood`. Talent ranks are read by their rank spell ids
# ($<rank>m<effect>), so retuning a rank updates every tooltip that shows it. Variable names stay under 12 chars.
#
# 1250 Bloody Strikes (talent 2015, ranks 48977 / 49394 / 49395): E1 Heart Strike, E2 Marrowrend, E3 Blood Boil.
#   Use `{pot2*heart}` style in a Heart Strike text, `${$s1*$<heart>}%` for the weapon percent; the matching variable is
#   `heart` (Heart Strike), `marrow` (Marrowrend) or `boil` (Blood Boil). One spell reads one entry, so Heart Strike,
#   Marrowrend and Blood Boil all point at this entry and each uses its own variable.
bloody_strikes_tooltip_1250 = tooltip_vars(
    1250, 'Bloody Strikes: Heart Strike (E1), Marrowrend (E2), Blood Boil (E3) damage on their tooltips',
    heart=talent_mult([48977, 49394, 49395], effect=1),
    marrow=talent_mult([48977, 49394, 49395], effect=2),
    boil=talent_mult([48977, 49394, 49395], effect=3),
)
# 1251 Improved Death Strike (talent 2259, ranks 62905 / 62908): E1 damage, E3 healing done by Death Strike's heal.
#   `dsdmg` multiplies the damage, `dsheal` multiplies the "% of damage taken" heal text.
improved_death_strike_tooltip_1251 = tooltip_vars(
    1251, 'Improved Death Strike: Death Strike damage (E1) and healing (E3) on the Death Strike tooltip',
    dsdmg=talent_mult([62905, 62908], effect=1),
    dsheal=talent_mult([62905, 62908], effect=3),
)

# =====================================================================================================================
# Crimson Resolve (203120-203122, talent 60330, row 0): Versatility +1/2/3%
# =====================================================================================================================


def _passive_rank(spell_id, name, effects, icon, level, description, notes, masks=None, proc_chance=None):
    """A talent rank spell: hidden passive (attributes 0x1D0), duration -1, self range, family 15. `masks` maps a 1-based
    effect index to its (d0, d1, d2) EffectSpellClassMask triple (A / B / C dwords of that effect)."""
    raw = {
        'EquippedItemClass': -1, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellLevel': level, 'CastingTimeIndex': 1,
        'ProcChance': 101 if proc_chance is None else proc_chance,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': description, 'AuraDescription_Lang_Mask': 16712188,
        'RuneCostID': 0,
    }
    for i in range(1, len(effects) + 1):
        raw[f'EffectChainAmplitude_{i}'] = 1.0
    for effect_index, triple in (masks or {}).items():
        for dword, value in enumerate(triple, start=1):
            if value:
                raw[f'EffectSpellClassMask{"ABC"[effect_index - 1]}_{dword}'] = value
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_TALENT_PASSIVE,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1,
        effects=effects, spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _capstone_text(text, capstone, last):
    """Capstone line under the rank text: grey below the last rank, plain on the last (paladin_holy_ranks.py _desc)."""
    if last:
        return f'{text}\n\nCapstone Bonus: {capstone}'
    return f'{text}\n\n|cFF9D9D9DCapstone Bonus: {capstone}|r'


_ICON_CRIMSON_RESOLVE = 4178        # achievement_dungeon_crimsonhall (S1a-0VERIFY section 4)
_CRIMSON_RESOLVE_NOTE = (
    'death-knight-rework S1a, Blood doc "Crimson Resolve" (0,3): hidden passive, aura 306 MOD_CUSTOM_STAT_PCT misc '
    '1 << 21 (Versatility), stored amount = percent - 1 (A New Dawn 201240 precedent). No capstone, no family bits. '
    'SpellLevel 9 + 5 x row 0 + rank.'
)
crimson_resolve_203120 = _passive_rank(
    203120, 'Crimson Resolve',
    [Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=_TARGET_UNIT_CASTER,
            apply_aura=_AURA_MOD_CUSTOM_STAT_PCT, misc_value=_CR_VERSATILITY)],
    _ICON_CRIMSON_RESOLVE, _rank_level(0, 1), 'Increases your Versatility by 1%.', _CRIMSON_RESOLVE_NOTE,
)
crimson_resolve_203121 = _passive_rank(
    203121, 'Crimson Resolve',
    [Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=_TARGET_UNIT_CASTER,
            apply_aura=_AURA_MOD_CUSTOM_STAT_PCT, misc_value=_CR_VERSATILITY)],
    _ICON_CRIMSON_RESOLVE, _rank_level(0, 2), 'Increases your Versatility by 2%.', _CRIMSON_RESOLVE_NOTE,
)
crimson_resolve_203122 = _passive_rank(
    203122, 'Crimson Resolve',
    [Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=_TARGET_UNIT_CASTER,
            apply_aura=_AURA_MOD_CUSTOM_STAT_PCT, misc_value=_CR_VERSATILITY)],
    _ICON_CRIMSON_RESOLVE, _rank_level(0, 3), 'Increases your Versatility by 3%.', _CRIMSON_RESOLVE_NOTE,
)

# =====================================================================================================================
# Marrowrend (203123, talent 60331, row 2): the Blood rune-spender for Frost + Unholy runes
# =====================================================================================================================

# 1 Unholy Rune + 1 Frost Rune, +20 Runic Power (above the class rule of 15 on purpose, Blood doc). SpellRuneCost 2601.
spell_rune_cost(2601, unholy=1, frost=1, runic_power=20, comment='Marrowrend: 1 Unholy + 1 Frost Rune, +20 Runic Power')

# Obliterate 203054's frame (a single-target melee strike, the stock Heart Strike / Obliterate frame minus the chain):
# eff0 WEAPON_PERCENT_DAMAGE weapon_potency 80 FIRST, eff1 NORMALIZED_WEAPON_DMG sp_potency 10 direct SECOND (EffectWeaponDmg
# multiplies a flat effect that sits before the percent effect by the percent). EFFECT_2 stays empty. d2 b8 (MARROWREND) is
# the only family bit; never d0 b22. The +3 Bone Shield charges, the cap bonus (script: SetHitDamage x
# (100 + MARROWREND_CAP_BONUS_PCT)% at 6 charges) and the DRW copy rule are spell_dk_marrowrend's.
marrowrend_203123 = spell(
    id=203123,
    name='Marrowrend',
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
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=80, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=10, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=599,
    tooltip_vars=bloody_strikes_tooltip_1250,
    notes=(
        'death-knight-rework S1a (Blood doc "Marrowrend", S1a-HANDOFF known-hard 2, brief D3 / D10): talent spell, SpellLevel '
        '20 (row 2), no cooldown, GCD 133 / 1500, melee range, main-hand weapon. eff0 WEAPON_PERCENT_DAMAGE weapon_potency '
        '80 first, eff1 NORMALIZED_WEAPON_DMG sp_potency 10 direct T 1500 second (Obliterate 203054 layout); EFFECT_2 '
        'empty. RuneCostID 2601 = 0 Blood / 1 Unholy / 1 Frost / +20 RP. d2 b8 (m.MARROWREND) the only family bit. '
        'Frame of Obliterate (Attributes 262160, Ex 134218240, Ex3 1024, DefenseType 2, PreventionType 2, FacingCasterFlags '
        '1, RangeIndex 2). SpellVisualID_1 15339 = Lord Marrowgar\'s Bone Spike impact (S1a-0VERIFY item 4); icon 599 '
        'INV_Misc_Bone_09. Tooltip multiplies both numbers by the Bloody Strikes variable (tooltip_vars 1250, U24). '
        'SkillLineAbility 30740 (Blood line 770) comes from granted_by_talent in deathknight_talents.py. '
        'spell_dk_marrowrend adds the Bone Shield charges / cap bonus.'
    ),
    raw_overrides={
        'AttributesEx': 134218240, 'AttributesEx3': 1024, 'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1,
        'DefenseType': 2, 'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Smash the target, dealing ${$s1*$<marrow>}% weapon damage plus {pot2.avg*marrow} and '
                                 'granting you 3 charges of Bone Shield, up to 6. If you already have 6 charges, '
                                 'Marrowrend deals 20% more damage instead.',
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'EquippedItemClass': 2, 'EquippedItemSubclass': 173555, 'FacingCasterFlags': 1, 'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': '', 'Name_Lang_Mask': 16712190, 'PreventionType': 2, 'ProcChance': 101, 'RangeIndex': 2,
        'RuneCostID': 2601, 'SpellClassMask_3': m.MARROWREND, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT,
        'SpellLevel': _LEVEL_MARROWREND, 'SpellVisualID_1': 15339, 'StartRecoveryCategory': 133,
        'StartRecoveryTime': 1500,
    },
)
scripted_by(marrowrend_203123, 'spell_dk_marrowrend')

# =====================================================================================================================
# Thick Blood (203124-203126, talent 60332, row 3): Stamina +2/4/6%; rank 3 is the Red Thirst marker
# =====================================================================================================================

_ICON_THICK_BLOOD = 1841            # INV_Misc_Organ_02 (unused in tab 398)
_RED_THIRST = ('Red Thirst. Every 10 Runic Power you spend reduces the remaining cooldown of Vampiric Blood by 0.5 sec.')
_THICK_BLOOD_NOTE = (
    'death-knight-rework S1a, Blood doc "Thick Blood" (3,0): hidden passive, aura 137 MOD_TOTAL_STAT_PERCENTAGE misc 2 '
    '(Stamina), stored amount = percent - 1. Rank 3 (203126) is the Red Thirst marker: PlayerScript '
    'OnRunicPowerSpent reads HasAura(203126) (HasSpell is false for passive talent ranks). SpellLevel 9 + 5 x row 3 + rank.'
)
thick_blood_203124 = _passive_rank(
    203124, 'Thick Blood',
    [Effect(type=EffectType.APPLY_AURA, base_points=1, implicit_target_a=_TARGET_UNIT_CASTER,
            apply_aura=_AURA_MOD_TOTAL_STAT_PERCENTAGE, misc_value=_STAT_STAMINA)],
    _ICON_THICK_BLOOD, _rank_level(3, 1), _capstone_text('Increases your total Stamina by 2%.', _RED_THIRST, False),
    _THICK_BLOOD_NOTE,
)
thick_blood_203125 = _passive_rank(
    203125, 'Thick Blood',
    [Effect(type=EffectType.APPLY_AURA, base_points=3, implicit_target_a=_TARGET_UNIT_CASTER,
            apply_aura=_AURA_MOD_TOTAL_STAT_PERCENTAGE, misc_value=_STAT_STAMINA)],
    _ICON_THICK_BLOOD, _rank_level(3, 2), _capstone_text('Increases your total Stamina by 4%.', _RED_THIRST, False),
    _THICK_BLOOD_NOTE,
)
thick_blood_203126 = _passive_rank(
    203126, 'Thick Blood',
    [Effect(type=EffectType.APPLY_AURA, base_points=5, implicit_target_a=_TARGET_UNIT_CASTER,
            apply_aura=_AURA_MOD_TOTAL_STAT_PERCENTAGE, misc_value=_STAT_STAMINA)],
    _ICON_THICK_BLOOD, _rank_level(3, 3), _capstone_text('Increases your total Stamina by 6%.', _RED_THIRST, True),
    _THICK_BLOOD_NOTE,
)

# =====================================================================================================================
# Gorefiend's Grasp (203127, talent 60333, row 4) and its per-target pull helper (203128)
# =====================================================================================================================

# Custom SpellIcon 90310 = Ascension ability_deathknight_aoedeathgrip (the retail Gorefiend's Grasp art), minted by
# build_patch_i.py (ICON_ID_GOREFIENDS_GRASP) into patch-I. Playtest fix: it had Winter's Grasp (2947), same as a mage icon.
# The talent 60333 takes its icon from rank spell 203127, so this one constant covers the cast, the talent and the helper.
_ICON_GOREFIENDS_GRASP = 90310

# Castable: 30 yd, unit target of any kind (eff0 TARGET_UNIT_TARGET_ANY, a no-op DUMMY that makes the explicit target
# selectable on friends, enemies and self), eff1 DUMMY on TARGET_DEST_TARGET_ANY / TARGET_UNIT_DEST_AREA_ENEMY 15 yd
# (GOREFIENDS_GRASP_RADIUS) around that target: spell_dk_gorefiends_grasp filters the area list in
# OnObjectAreaTargetSelect(EFFECT_1, TARGET_UNIT_DEST_AREA_ENEMY) to engaged enemies (no bosses) and casts the helper 203128
# triggered on each. Instant, GCD 133 / 1500, 90 s (Cooldown Haste applies: a base cooldown of 30 s or more), no cost, no
# rune, no family bits. Normal school and DefenseType 1 (magic: GCD hasted by the core) so no school immunity or resist
# blocks it, like Death Grip. SkillLineAbility 30741 is bundled by granted_by_talent.
gorefiends_grasp_203127 = spell(
    id=203127,
    name="Gorefiend's Grasp",
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=90000,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ANY),
        Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_TARGET_ANY,
               implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=15.0),
    ],
    spell_icon_id=_ICON_GOREFIENDS_GRASP,
    notes=(
        'death-knight-rework S1a (Blood doc "Gorefiend\'s Grasp", U20): talent spell, no cost, no family bits, 90 s, GCD '
        '133 / 1500, 30 yd. eff0 DUMMY TARGET_UNIT_TARGET_ANY (explicit friend / foe / self target), eff1 DUMMY '
        'TARGET_DEST_TARGET_ANY + TARGET_UNIT_DEST_AREA_ENEMY radius 15 yd (const GOREFIENDS_GRASP_RADIUS); the script '
        'filters eff1\'s list (engaged enemies, no bosses, not the caster) and casts helper 203128 on each. AttributesEx3 '
        '0x20000 (no initial aggro) + 0x10000 (no caster procs) so a cast on an unengaged hostile neither pulls it nor '
        'rolls procs (S1a-REVIEW m1). Tooltip is '
        'the doc text minus its cooldown sentence. SkillLineAbility 30741 (Blood line 770) from granted_by_talent.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1, 'DefenseType': 1, 'PreventionType': 1, 'EquippedItemClass': -1, 'ProcChance': 101,
        'AttributesEx3': _ATTR3_NO_INITIAL_AGGRO | _ATTR3_SUPPRESS_CASTER_PROCS,
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellLevel': _LEVEL_GOREFIENDS_GRASP, 'RuneCostID': 0,
        'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188,
        'Description_Lang_enUS': "Shadowy tendrils coil around all enemies within 15 yards of a hostile or friendly "
                                 "target, pulling them to the target's location.",
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
    },
)
scripted_by(gorefiends_grasp_203127, 'spell_dk_gorefiends_grasp')
# The pull helper (hidden, cast triggered by the script on each engaged enemy). Spell Mechanic GRIP (Death Grip's) so
# grip-immune creatures resist it. eff0 is a DUMMY the script hooks (the target jumps to the explicit target's position, the
# 57604 shape) and carries the threat number as ap_potency 50 direct: the script reads the generated coefficient exactly as
# spell_dk_anti_magic_zone_rework reads 50461's (Effects[0].CalcValue(owner) + SpellBonusEntry::ap_bonus x the owner's
# attack power, DeathKnightMechanics.cpp ComputeInitialZonePool). No GCD, no cost, 50000 yd range, ignores line of sight
# (the area was already checked from the target), always hits, rolls no procs.
gorefiends_grasp_pull_203128 = spell(
    id=203128,
    name="Gorefiend's Grasp",
    school=School.NORMAL,
    mechanic=_MECHANIC_GRIP,
    attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.DUMMY, ap_potency=50.0, potency_kind='direct', time_basis_ms=1500,
               mechanic=_MECHANIC_GRIP, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_GOREFIENDS_GRASP,
    notes=(
        'death-knight-rework S1a (U20): hidden per-target helper of 203127. Spell + effect Mechanic GRIP (6), eff0 DUMMY on '
        'the enemy with ap_potency 50 direct T 1500 (the threat coefficient: spell_dk_gorefiends_grasp_pull reads '
        'CalcValue + ap_bonus x AP, the AMZ pool precedent), SpellLevel 30 (row 4), AttributesEx2 IGNORE_LOS, AttributesEx3 '
        'ALWAYS_HIT + SUPPRESS_CASTER_PROCS (rolls no procs), range 50000 yd (script cast), no family bits, no GCD. Visual '
        '10906 = Death Grip\'s chain (S1a-0VERIFY item 4). The potency number is threat, not damage: the effect deals none.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1, 'DefenseType': 1, 'PreventionType': 1, 'EquippedItemClass': -1, 'ProcChance': 101,
        'AttributesEx2': _ATTR2_IGNORE_LOS, 'AttributesEx3': _ATTR3_ALWAYS_HIT | _ATTR3_SUPPRESS_CASTER_PROCS,
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellLevel': _LEVEL_GOREFIENDS_GRASP, 'RuneCostID': 0,
        'SpellVisualID_1': 10906,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188,
        'Description_Lang_enUS': "Pulls the target to the location of Gorefiend's Grasp's target.",
        'EffectChainAmplitude_1': 1.0,
    },
)
scripted_by(gorefiends_grasp_pull_203128, 'spell_dk_gorefiends_grasp_pull')

# =====================================================================================================================
# Sanguine Ground (203129-203131, talent 60334, row 5): Death and Decay +10/20/30%, capstone tick heal
# =====================================================================================================================

_ICON_SANGUINE_GROUND = 2001        # INV_Misc_Gem_BloodGem_01
_SANGUINE_CAPSTONE = ('Each tick of your Death and Decay heals you for 1% of your maximum health while you stand in it.')
_SANGUINE_NOTE = (
    'death-knight-rework S1a, Blood doc "Sanguine Ground" (5,0): eff0 ADD_PCT_MODIFIER SPELLMOD_DAMAGE stored 9 / 19 / 29 '
    '(+10 / 20 / 30%) on the Death and Decay tick 52212, mask d2 b3 only (m.DEATH_AND_DECAY_TICK, effect-1 dword 3: '
    'EffectSpellClassMaskA_3), family 15 (only a player\'s Death and Decay carries the bit; Hexlord\'s casts are untouched). '
    'Rank 3 (203131) is the capstone marker: the 43265 script casts the hidden tick aura 203132 when the DK has it. '
    'SpellLevel 9 + 5 x row 5 + rank.'
)


def _sanguine_rank(spell_id, rank, stored, percent):
    return _passive_rank(
        spell_id, 'Sanguine Ground',
        [Effect(type=EffectType.APPLY_AURA, base_points=stored, implicit_target_a=_TARGET_UNIT_CASTER,
                apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.DAMAGE))],
        _ICON_SANGUINE_GROUND, _rank_level(5, rank),
        _capstone_text(f'Increases the damage of your Death and Decay by {percent}%.', _SANGUINE_CAPSTONE, rank == 3),
        _SANGUINE_NOTE, masks={1: (0, 0, m.DEATH_AND_DECAY_TICK)},
    )


sanguine_ground_203129 = _sanguine_rank(203129, 1, 9, 10)
sanguine_ground_203130 = _sanguine_rank(203130, 2, 19, 20)
sanguine_ground_203131 = _sanguine_rank(203131, 3, 29, 30)

# Entry 1252: Sanguine Ground's damage on the Death and Decay tooltip (variable `sang`, effect 1 of each rank).
sanguine_ground_tooltip_1252 = tooltip_vars(
    1252, 'Sanguine Ground: Death and Decay damage on its tooltip',
    sang=talent_mult([sanguine_ground_203129, sanguine_ground_203130, sanguine_ground_203131], effect=1),
)

# The hidden self aura cast by the 43265 player script (capstone only): PERIODIC_DUMMY every 1000 ms (no haste-periodic
# attribute, so never hasted), 10 s = a full Death and Decay. spell_dk_sanguine_ground stores the Blood Gorged state on
# apply and heals 1% (203133) on each tick while the DK stands inside its own Death and Decay.
sanguine_ground_tick_203132 = spell(
    id=203132,
    name='Sanguine Ground',
    school=School.NORMAL,
    attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_SANGUINE_GROUND,
    notes=(
        'death-knight-rework S1a (U19): hidden self aura (DO_NOT_DISPLAY, not passive so it can expire), PERIODIC_DUMMY '
        '1000 ms unhasted, 10 s. Cast by spell_dk_death_and_decay_blood when the Death Knight has 203131; '
        'spell_dk_sanguine_ground ticks it. No family bits, no cost.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'RuneCostID': 0,
        'ProcChance': 101,
        'Description_Lang_enUS': 'Heals you while you stand in your Death and Decay.',
        'AuraDescription_Lang_enUS': 'Healing while standing in Death and Decay.',
    },
)
scripted_by(sanguine_ground_tick_203132, 'spell_dk_sanguine_ground')

# The tick's heal: a percent of maximum health the script supplies (CastCustomSpell BP0 = SANGUINE_HEAL_PCT % of max
# health), so the HEAL effect is potency_excluded. DefenseType 1 + an all-zero spell_bonus_data row so Versatility and
# healing-done percent apply and spell power stays out (the 45470 shape, U23). d2 b15 (m.DK_SELF_HEAL) marks it as a Death
# Knight self-heal for the Voracious capstone. CANT_CRIT (a flat percent) and SUPPRESS_CASTER_PROCS.
sanguine_ground_heal_203133 = spell(
    id=203133,
    name='Sanguine Ground',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[
        Effect(type=EffectType.HEAL, implicit_target_a=_TARGET_UNIT_CASTER,
               potency_excluded='percent of maximum health: the amount comes from spell_dk_sanguine_ground via '
                                'CastCustomSpell BP0 (SANGUINE_HEAL_PCT), not CalcValue'),
    ],
    spell_icon_id=_ICON_SANGUINE_GROUND,
    notes=(
        'death-knight-rework S1a (U19 / U23): the Sanguine Ground tick heal, HEAL value 0 (script BP0 = 1% of max health), '
        'potency_excluded (percent of max health). DefenseType 1 + all-zero bonus row so Versatility applies. d2 b15 '
        '(DK_SELF_HEAL) for the Voracious capstone, AttributesEx2 CANT_CRIT, AttributesEx3 SUPPRESS_CASTER_PROCS. '
        'SpellLevel 35 (Sanguine Ground row 5).'
    ),
    raw_overrides={
        'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'ProcChance': 101,
        'AttributesEx2': _ATTR2_CANT_CRIT, 'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS,
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellClassMask_3': m.DK_SELF_HEAL,
        'SpellLevel': _LEVEL_SANGUINE_GROUND, 'RuneCostID': 0,
        'Description_Lang_enUS': 'Heals you for 1% of your maximum health.',
    },
)
bonus_coefficients(sanguine_ground_heal_203133, direct=0.0, dot=0.0, ap=0.0, ap_dot=0.0,
                   comment='Death Knight - Sanguine Ground heal: no spell power; DefenseType 1 only so Versatility applies')

# =====================================================================================================================
# Crimson Scourge (203134-203136, talent 60335, row 5) and its buff (203137)
# =====================================================================================================================

_ICON_CRIMSON_SCOURGE = 2968        # Ability_Warrior_BloodNova (S1a-0VERIFY section 4)
_CRIMSON_SCOURGE_NOTE = (
    'death-knight-rework S1a, Blood doc "Crimson Scourge" (5,3): hidden passive, eff0 PROC_TRIGGER_SPELL -> 203137 (self). '
    'ProcChance 5 / 10 / 15 on the rank spell; the shared chain row (procs_on -203134) carries Chance 0 = "use the spell\'s", '
    'cooldown 10000 ms, ProcFlags DONE melee auto attack only (either hand, no abilities). '
    'spell_dk_crimson_scourge.CheckProc: the auto attack\'s target carries the owner\'s Blood Plague (55078). '
    'SpellLevel 9 + 5 x row 5 + rank.'
)


def _crimson_scourge_rank(spell_id, rank, chance):
    return _passive_rank(
        spell_id, 'Crimson Scourge',
        [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=203137,
                implicit_target_a=_TARGET_UNIT_CASTER)],
        _ICON_CRIMSON_SCOURGE, _rank_level(5, rank),
        f'Your auto attacks against targets infected with your Blood Plague have a {chance}% chance to make your next '
        'Death and Decay cost no runes and reset its cooldown. This effect cannot occur more than once every 10 sec.',
        _CRIMSON_SCOURGE_NOTE, proc_chance=chance,
    )


crimson_scourge_203134 = _crimson_scourge_rank(203134, 1, 5)
crimson_scourge_203135 = _crimson_scourge_rank(203135, 2, 10)
crimson_scourge_203136 = _crimson_scourge_rank(203136, 3, 15)
procs_on(-203134, proc_flags=_PROC_FLAG_DONE_MELEE_AUTO_ATTACK, spell_phase_mask=0, chance=0.0, cooldown_ms=10000)
scripted_by(-203134, 'spell_dk_crimson_scourge')

# The visible buff (name shown to players: Crimson Scourge): the next Death and Decay costs nothing (SpellMod COST -100%
# on 43265, d0 b5; rune costs honour it) and has no cooldown (AfterEffectApply removes the cooldown). One charge, spent by
# the Death and Decay cast through the REQ_SPELLMOD proc row (CAST phase, the shaman Icefury shape), 15 s, refreshed by a
# new proc (no stacking). Non-passive, no consolidation flag, aura text number-free and verbatim.
crimson_scourge_buff_203137 = spell(
    id=203137,
    name='Crimson Scourge',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-101, implicit_target_a=_TARGET_UNIT_CASTER,
               apply_aura=AuraType.ADD_PCT_MODIFIER, misc_value=int(SpellModOp.COST)),
    ],
    spell_icon_id=_ICON_CRIMSON_SCOURGE,
    notes=(
        'death-knight-rework S1a (U14): the proc buff. eff0 ADD_PCT_MODIFIER SPELLMOD_COST stored -101 (-100%) on Death and '
        'Decay 43265 (EffectSpellClassMaskA_1 = m.DEATH_AND_DECAY, d0 b5), ProcCharges 1, 15 s. spell_proc row '
        '(REQ_SPELLMOD, CAST phase, family 15 mask d0 b5, charges 1) spends the charge on the Death and Decay cast. '
        'spell_dk_crimson_scourge_buff removes the Death and Decay cooldown on apply; spell_dk_death_and_decay_blood '
        'puts the Runic Power back when this cast consumed the buff. Visible (not passive), no Consolidated Buffs flag.'
    ),
    raw_overrides={
        'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'RuneCostID': 0,
        'ProcChance': 101, 'ProcCharges': 1, 'SpellLevel': 0,
        'EffectSpellClassMaskA_1': m.DEATH_AND_DECAY, 'EffectChainAmplitude_1': 1.0,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Your next Death and Decay costs no runes and has no cooldown.',
        'AuraDescription_Lang_enUS': 'Your next Death and Decay costs no runes and has no cooldown.',
    },
)
procs_on(
    crimson_scourge_buff_203137,
    proc_flags=_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
    family_name=_SPELLFAMILY_DEATHKNIGHT, family_mask=(m.DEATH_AND_DECAY, 0, 0), spell_type_mask=_PROC_SPELL_TYPE_ALL,
    spell_phase_mask=_PROC_SPELL_PHASE_CAST, attributes_mask=_PROC_ATTR_REQ_SPELLMOD, chance=100.0, charges=1,
)
scripted_by(crimson_scourge_buff_203137, 'spell_dk_crimson_scourge_buff')
