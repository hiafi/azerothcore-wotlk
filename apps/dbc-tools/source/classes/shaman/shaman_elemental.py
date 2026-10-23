"""
Shaman - S1a A3: the Elemental spec's new spells (docs/reworks/shaman-elemental-rework.md section 5; brief
.agents/plans/shaman-rework/shaman-rework.S1a-WP-BRIEF.md id map, S1-NOTES sections 1-3, 0-VERIFY 2b/5/8/11).

Ids 202520-202595 (Ele block 202520-202639):
    202520-202536  talent rank spells (Raze 3, Wind Rush 3, Power of the Elements, Conduit, Icefury, Fusion 2,
                   Call of the Elements castable, Elemental Focus r2, Call of Thunder r2/r3, Booming Echoes r3,
                   Elemental Oath r3)
    202560-202590  buffs, debuffs, charges and guardian auras (read by the C++ by id)
    202591-202593  Lightning Overload copies (LB, CL, Lava Burst)
    202595         Astral Shift, empowered
SkillLineAbility 30690 (Call of the Elements). (202594, the stun-castable Thunderstorm rank 2, its SkillLineAbility 30691
and the superseded_by edit of the stock row 17659 were removed in playtest fix pass 2 / P6: Call of Thunder's capstone is
now "Thunderstorm restores 100% more mana". Ids 202594 and 30691 stay retired; clients may have cached them.)

Conventions
- SpellClassSet 11 on every row (a family-0 SpellMod would match every spell); `EquippedItemClass -1` (L1).
- Static rows store live - 1 (a +10% mod is base_points 9). Percent SpellMods multiply by the stack count in
  `AuraEffect::CalculateAmount`, so a per-stack value is stored per stack.
- Buffs and debuffs carry NO family bit (FB 4.3); a talent's rank spell is a passive hidden aura (attributes 0x1D0).
- Visible buffs are non-passive with no consolidation flag (AttributesEx7 0x10000000 cleared) and a number-free
  aura text verbatim from the doc. Hidden helpers carry SPELL_ATTR0_DO_NOT_DISPLAY (0x80) and are non-passive, so
  they are saved with the player. Guardian-side auras are owner-added (L5): AttributesEx3 0x100000 + Ex2 0x1.
- Capstone tooltip format (talent-tooltip-audit step 5): "\\n\\n|cFF9D9D9DCapstone Bonus: ...|r" on every rank below
  the last, plain on the last.
- Consumable charge buffs carry DBC `ProcCharges` (the engine's charge cap) and an explicit `spell_proc` row with
  PROC_ATTR_REQ_SPELLMOD (declared at the bottom of this file, see "Consumption rows"). SpellMods with charges
  keep applying to the spell that already applied them after the last charge is gone (Player.cpp:10049).

Bindings declared here: spell_sha_ele_overload_copy (the three copies), spell_sha_ele_call_of_the_elements (202531),
spell_sha_ele_empowerment (202560-202563). Every other class-table binding is on a stock id owned by A2 / A4.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import const, procs_on, scripted_by, skill_line_ability, spell, unbind_script

from . import _masks as m
from .shaman_spells import chain_lightning_421, lava_burst_51505, lightning_bolt_403

SPELLFAMILY_SHAMAN = 11
NOTE = 'shaman-rework S1a A3: '

# ---- Spell.dbc flag values ------------------------------------------------------------------------------------------
ATTR0_PASSIVE_HIDDEN = 0x1D0          # PASSIVE | DO_NOT_DISPLAY | ...: the talent-rank shape (stock attributes 464)
ATTR0_DO_NOT_DISPLAY = 0x80
ATTR0_NOT_SHAPESHIFTED = 0x10000
ATTR1_NO_THREAT = 0x400
ATTR2_ALLOW_DEAD_TARGET = 0x1
ATTR2_IGNORE_LOS = 0x4
ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000

# ---- Aura types not in the DSL enum / handy aliases ----------------------------------------------------------------------
AURA_MOD_INCREASE_HEALTH_PERCENT = 133
AURA_MOD_THREAT = 10
TARGET_UNIT_CASTER = 1
TARGET_UNIT_TARGET_ENEMY = 6

CR_MASTERY_BIT = 1 << 20
CR_PROC_CHANCE_BIT = 1 << 11

SCHOOL_ALL = 127
SCHOOL_ALL_MAGIC = 126
SCHOOL_NATURE = 8
SCHOOL_OTHER_MAGIC = 118              # Holy | Fire | Frost | Shadow | Arcane (everything magic but Nature)

# ---- Family masks (SpellClassSet 11) -----------------------------------------------------------------------------------
LB = 0x1                              # d0 b0
CL = 0x2                              # d0 b1
EARTH_SHOCK = 0x100000                # d0 b20
FLAME_SHOCK = 0x10000000              # d0 b28
FROST_SHOCK = 0x80000000              # d0 b31
SHOCKS = EARTH_SHOCK | FLAME_SHOCK | FROST_SHOCK
SEARING_MAGMA = m.SEARING_MAGMA_BOLT  # d0 b30 (Searing bolt, Magma pulse); never d0 b29 / d1 b23 (Fire Elemental)
FLAMETONGUE_ATTACK = m.FLAMETONGUE_ATTACK
FROSTBRAND_ATTACK = m.FROSTBRAND_ATTACK
LAVA_BURST = 0x1000                   # d1 b12
THUNDERSTORM = 0x2000                 # d1 b13
FIRE_NOVA_DAMAGE = 0x80040000         # d1 b18 + b31: Fire Nova damage 8349 (its own mask)
WIND_SHEAR = 0x8000000                # d1 b27, Wind Shear 57994 only (never b11: Purge / Water Walking)
EARTHQUAKE = m.EARTHQUAKE             # d2 b19
ELEMENTAL_BLAST = m.ELEMENTAL_BLAST   # d2 b20

# Every shaman Fire / Frost / Nature damage spell: the stock Elemental Fury mask (0xD1300003 / 0x43000, which includes
# the Flametongue / Frostbrand Attack bits) plus Earthquake and Elemental Blast. Used by every "crit damage bonus"
# mod (Lightning Mastery, Fusion Fire) and by the Unrelenting Storm debuff (aura 271 reads the shaman's spell damage).
FFN_MASK = (
    LB | CL | EARTH_SHOCK | FLAMETONGUE_ATTACK | FROSTBRAND_ATTACK | FLAME_SHOCK | SEARING_MAGMA | FROST_SHOCK,
    LAVA_BURST | THUNDERSTORM | 0x40000,
    EARTHQUAKE | ELEMENTAL_BLAST,
)

# ---- Spell icons (stock SpellIconID; unique inside the Elemental tree, the V stage mints art) -------------------------------
ICON_RAZE = 19                        # Lightning Shield
ICON_WIND_RUSH = 220                  # Wind Shear
ICON_POTE = 2290                      # Fire Elemental Totem
ICON_EARTH = 2289                     # Earth Elemental Totem
ICON_FIRE = 2290
ICON_WATER = 2134                     # Summon Water Elemental
ICON_STORM = 1397                     # Air Attunement
ICON_CONDUIT = 1677                   # Grounding Totem
ICON_ICEFURY = 976                    # Frost Shock
ICON_FUSION = 3741                    # Lava Lash
ICON_COTE = 3991                      # stock Call of the Elements
ICON_FOCUS = 212
ICON_THUNDER = 141
ICON_ECHOES = 2460
ICON_OATH = 3053
ICON_LB = 62
ICON_CL = 165
ICON_LAVA_BURST = 3064
ICON_FLAME_SHOCK = 678
ICON_RAW_POWER = 320
ICON_US = 2010
ICON_REVERB = 501
ICON_PRECISION = 2017
ICON_DEVASTATION = 1930
ICON_REACH = 1921
ICON_RISING_FLAMES = 33
ICON_FURY = 1137
ICON_WARDING = 198
ICON_ASTRAL = 3066
ICON_THUNDERSTORM = 3080


# =====================================================================================================================
# Script numbers (generated into ShamanData::)
# =====================================================================================================================
EMPOWERMENT_PCT = const('EMPOWERMENT_PCT', 10, 'Elemental Empowerment, percent damage [fixed]; Conduit capstone adds Mastery.')
GATHERING_FLAMES_MAX = const('GATHERING_FLAMES_MAX', 5, 'Gathering Flames stack cap [fixed].')
ECHO_MAX = const('ECHO_MAX', 10, 'Echo stack cap [fixed].')
ECHO_DURATION_MS = const('ECHO_DURATION_MS', 30000, 'Echo duration, ms, refreshed by each Echo [tune] (20 s until the 2026-10-20 Earth Shock burst ruling).')
ECHO_EARTH_ELEMENTAL_GRANT = const('ECHO_EARTH_ELEMENTAL_GRANT', 5, 'Echo granted by each Earth Elemental summon with the Booming Echoes capstone [tune].')
ICEFURY_MAX_CHARGES = const('ICEFURY_MAX_CHARGES', 3, 'Icefury maximum charges [tune]; also the DBC ProcCharges of 202566.')
ICEFURY_WATER_EXTRA = const('ICEFURY_WATER_EXTRA', 2, 'Extra Icefury charges per Elemental Blast in the Water window [fixed].')
ICEFURY_MANA_PCT = const('ICEFURY_MANA_PCT', 5, 'Percent of max mana a Frost Shock that spends an Icefury charge restores while any elemental is active [fixed].')
RAW_POWER_DURATION_MS = const('RAW_POWER_DURATION_MS', 15000, 'Raw Power duration, ms, refreshed by each new stack [tune].')
LM_CHANCE_PER_STACK = const('LM_CHANCE_PER_STACK', 7, 'Lightning Mastery chance per Raw Power stack, percent [tune] (5 until the 2026-10-20 smoke-test fix pass).')
RAW_POWER_CHANCE_R1 = const('RAW_POWER_CHANCE_R1', 33, 'Lightning Mastery rank 1: chance a critical cast grants Raw Power, percent [fixed].')
RAW_POWER_CHANCE_R2 = const('RAW_POWER_CHANCE_R2', 66, 'Lightning Mastery rank 2 Raw Power chance, percent [fixed].')
RAW_POWER_CHANCE_R3 = const('RAW_POWER_CHANCE_R3', 100, 'Lightning Mastery rank 3 Raw Power chance, percent [fixed].')
LO_CHANCE_R1 = const('LO_CHANCE_R1', 6, 'Lightning Overload rank 1 chance per target hit, percent [fixed].')
LO_CHANCE_R2 = const('LO_CHANCE_R2', 13, 'Lightning Overload rank 2 chance, percent [fixed].')
LO_CHANCE_R3 = const('LO_CHANCE_R3', 20, 'Lightning Overload rank 3 chance, percent [fixed].')
LO_CRIT_MULT = const('LO_CRIT_MULT', 3, 'Lightning Overload chance multiplier on a critical hit [fixed].')
SHAMANISM_CHANCE = const('SHAMANISM_CHANCE', 33, 'Shamanism cooldown-reduction chance per Lightning Bolt / Chain Lightning hit, percent [fixed].')
SHAMANISM_CDR_MS = const('SHAMANISM_CDR_MS', 1000, 'Shamanism reduction of Elemental Mastery / Thunderstorm, real ms [fixed].')
PRECISION_CAPSTONE_CHANCE = const('PRECISION_CAPSTONE_CHANCE', 10, 'Elemental Precision capstone chance per cast, percent [fixed].')
REACH_CAPSTONE_CHANCE = const('REACH_CAPSTONE_CHANCE', 33, 'Elemental Reach capstone chance, percent [fixed].')
REACH_MIN_DISTANCE_YD = const('REACH_MIN_DISTANCE_YD', 20.0, 'Elemental Reach capstone minimum target distance at hit time, yd [fixed].')
REACH_ICD_MS = const('REACH_ICD_MS', 15000, 'Elemental Reach capstone internal cooldown, ms [fixed].')
LAVA_SURGE_CHANCE = const('LAVA_SURGE_CHANCE', 15, 'Lava Surge chance per Flame Shock tick, percent [fixed].')
LAVA_SURGE_ICD_MS = const('LAVA_SURGE_ICD_MS', 6000, 'Lava Surge internal cooldown, ms [fixed].')
COTE_SUMMON_MS = const('COTE_SUMMON_MS', 15000, 'Call of the Elements summon duration, ms [fixed].')
COTE_EXTEND_MS = const('COTE_EXTEND_MS', 15000, 'Call of the Elements extension of the active elemental, ms [fixed].')
CONDUIT_LOCKOUT_MS = const('CONDUIT_LOCKOUT_MS', 30000, 'Elemental lockout base with Conduit of the Elements, ms [fixed].')
RISING_FLAMES_TICK_MS = const('RISING_FLAMES_TICK_MS', 2000, 'Rising Flames capstone stack period, ms [fixed].')
RISING_FLAMES_PCT_PER_STACK = const('RISING_FLAMES_PCT_PER_STACK', 10, 'Rising Flames capstone Fire Nova damage per stack, percent [fixed].')
ASTRAL_SHIFT_PLAIN_PCT = const('ASTRAL_SHIFT_PLAIN_PCT', 10, 'Astral Shift damage taken reduction while stunned / feared / silenced, percent [fixed].')
ASTRAL_SHIFT_EMPOWERED_PCT = const('ASTRAL_SHIFT_EMPOWERED_PCT', 25, 'Empowered Astral Shift damage taken reduction, percent [fixed].')
ASTRAL_SHIFT_EMPOWERED_MS = const('ASTRAL_SHIFT_EMPOWERED_MS', 6000, 'Empowered Astral Shift duration, ms [fixed].')
WARDING_HEALTH_PCT = const('WARDING_HEALTH_PCT', 10, 'Elemental Warding capstone maximum health, percent [fixed].')
WATER_ELEMENTAL_BONUS_PCT = const('WATER_ELEMENTAL_BONUS_PCT', 30, 'Water Elemental damage bonus (Power of the Elements), percent [fixed].')
EARTH_ELEMENTAL_BONUS_PCT = const('EARTH_ELEMENTAL_BONUS_PCT', 20, 'Earth Elemental damage bonus (Elemental Warding capstone), percent [fixed].')
UNRELENTING_STORM_STACKS = const('UNRELENTING_STORM_STACKS', 3, 'Unrelenting Storm stacks that arm the Chain Lightning capstone [fixed].')
DEVASTATION_PC_R1 = const('DEVASTATION_PC_R1', 3, 'Elemental Devastation rank 1 Proc Chance bonus, percent points [fixed].')
DEVASTATION_PC_R2 = const('DEVASTATION_PC_R2', 6, 'Elemental Devastation rank 2 Proc Chance bonus [fixed].')
DEVASTATION_PC_R3 = const('DEVASTATION_PC_R3', 10, 'Elemental Devastation rank 3 Proc Chance bonus [fixed].')
FOCUS_COST_R1 = const('FOCUS_COST_R1', 15, 'Elemental Focus rank 1 Clearcasting mana cost reduction, percent [fixed].')
FOCUS_COST_R2 = const('FOCUS_COST_R2', 30, 'Elemental Focus rank 2 Clearcasting mana cost reduction, percent [fixed].')
US_HASTE_TENTHS_R1 = const('US_HASTE_TENTHS_R1', 5, 'Unrelenting Storm rank 1 haste per stack, tenths of a percent (0.5%) [fixed].')
US_HASTE_TENTHS_R2 = const('US_HASTE_TENTHS_R2', 10, 'Unrelenting Storm rank 2 haste per stack, tenths of a percent [fixed].')
US_HASTE_TENTHS_R3 = const('US_HASTE_TENTHS_R3', 15, 'Unrelenting Storm rank 3 haste per stack, tenths of a percent [fixed].')


# =====================================================================================================================
# Helpers
# =====================================================================================================================
def _text(description: str = '', aura: str = '') -> dict:
    return {
        'Description_Lang_Mask': 16712190 if description else 16712188,
        'Description_Lang_enUS': description,
        'AuraDescription_Lang_Mask': 16712190 if aura else 16712188,
        'AuraDescription_Lang_enUS': aura,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_Mask': 16712188,
    }


def _emask(effect: int, mask) -> dict:
    """EffectSpellClassMask{A,B,C}_{1,2,3}: the LETTER is the effect (1 -> A), the number the dword. `mask` is an int
    (dword 0) or a (d0, d1, d2) tuple."""
    letter = 'ABC'[effect - 1]
    dwords = mask if isinstance(mask, tuple) else (mask, 0, 0)
    return {f'EffectSpellClassMask{letter}_{i + 1}': value for i, value in enumerate(dwords) if value}


def _raw(description: str = '', aura: str = '', level: int = 1, **extra) -> dict:
    raw = {
        **_text(description, aura),
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'CastingTimeIndex': 1,
        'EquippedItemClass': -1,
        'ProcChance': 101,
        'SpellClassSet': SPELLFAMILY_SHAMAN,
        'SpellLevel': level,
    }
    raw.update(extra)
    return raw


def _aura(aura, base_points: int = 0, misc_value: int = 0, target: int = TARGET_UNIT_CASTER, **kw) -> Effect:
    return Effect(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=base_points, misc_value=int(misc_value),
                  implicit_target_a=target, **kw)


def _mod(op: SpellModOp, pct: bool, base_points: int) -> Effect:
    """A self-targeted SpellMod; the scope mask goes through `_emask` on the same effect slot."""
    return _aura(AuraType.ADD_PCT_MODIFIER if pct else AuraType.ADD_FLAT_MODIFIER, base_points, int(op))


def _dummy(base_points: int = 0) -> Effect:
    return _aura(AuraType.DUMMY, base_points)


def _desc(text: str, capstone: str | None = None, last: bool = False) -> str:
    """talent-tooltip-audit step 5: grey capstone clause on every non-final rank, plain on the final one."""
    if capstone is None:
        return text
    if last:
        return f'{text}\n\nCapstone Bonus: {capstone}'
    return f'{text}\n\n|cFF9D9D9DCapstone Bonus: {capstone}|r'


def _rank(spell_id: int, name: str, effects: list, icon: int, level: int, description: str, notes: str,
          subtext: str = '', **raw_extra):
    """A talent rank spell: hidden passive, infinite, self."""
    raw = _raw(description, '', level, **raw_extra)
    if subtext:
        raw['NameSubtext_Lang_Mask'] = 16712190
        raw['NameSubtext_Lang_enUS'] = subtext
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_PASSIVE_HIDDEN,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1, effects=effects, spell_icon_id=icon,
        notes=NOTE + notes, raw_overrides=raw,
    )


def _buff(spell_id: int, name: str, effects: list, icon: int, duration_ms: int, aura: str = '', description: str = '',
          notes: str = '', school=School.NATURE, hidden: bool = False, stacks: int = 0, charges: int = 0,
          level: int = 1, guardian: bool = False, **raw_extra):
    """A self buff. Visible by default (non-passive, no consolidation flag); `hidden` adds DO_NOT_DISPLAY;
    `guardian` adds the owner-added death-persistence pair (L5). `stacks` = CumulativeAura, `charges` = ProcCharges."""
    raw = _raw(description, aura, level, **raw_extra)
    if stacks:
        raw['CumulativeAura'] = stacks
    if charges:
        raw['ProcCharges'] = charges
        raw['ProcChance'] = 100
    if guardian:
        raw['AttributesEx2'] = ATTR2_ALLOW_DEAD_TARGET
        raw['AttributesEx3'] = ATTR3_ALLOW_AURA_WHILE_DEAD
    return spell(
        id=spell_id, name=name, school=school, attributes=ATTR0_DO_NOT_DISPLAY if hidden else 0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=duration_ms, effects=effects, spell_icon_id=icon,
        notes=NOTE + notes, raw_overrides=raw,
    )


# =====================================================================================================================
# Talent rank spells 202520-202536 (the learn level of row N is 10 + 5N)
# =====================================================================================================================

# ---- Raze (60280, row 0): spell crit +1/2/3% -------------------------------------------------------------------------
def _raze(spell_id: int, pct: int):
    return _rank(
        spell_id, 'Raze', [_aura(AuraType.MOD_SPELL_CRIT_CHANCE, pct - 1)], ICON_RAZE, 10,
        f'Increases your spell critical strike chance by {pct}%.',
        f'Raze rank {pct}: aura 57 spell crit +{pct}% (bp {pct - 1}).',
    )


raze_rank1_202520 = _raze(202520, 1)
raze_rank2_202521 = _raze(202521, 2)
raze_rank3_202522 = _raze(202522, 3)

# ---- Wind Rush (60281, row 0): Wind Shear cooldown -1/2/3 s; capstone haste buff 202582 (C++) -------------------------
_WIND_RUSH_CAPSTONE = 'Successfully interrupting a spell with Wind Shear increases your haste by 15% for 10 sec.'


def _wind_rush(spell_id: int, secs: int, last: bool):
    return _rank(
        spell_id, 'Wind Rush', [_mod(SpellModOp.COOLDOWN, False, -1000 * secs - 1)], ICON_WIND_RUSH, 10,
        _desc(f'Reduces the cooldown of your Wind Shear by {secs} sec.', _WIND_RUSH_CAPSTONE, last),
        f'Wind Rush rank {secs}: SPELLMOD_COOLDOWN flat -{secs} s on Wind Shear 57994 only (d1 b27 {WIND_SHEAR:#x}, '
        f'never b11). Rank 3 is the capstone: spell_sha_ele_wind_rush (on 57994) grants 202582 on a successful '
        f'interrupt when rank 3 is known.',
        **_emask(1, (0, WIND_SHEAR, 0)),
    )


wind_rush_rank1_202523 = _wind_rush(202523, 1, False)
wind_rush_rank2_202524 = _wind_rush(202524, 2, False)
wind_rush_rank3_202525 = _wind_rush(202525, 3, True)

# ---- Power of the Elements (60282, row 4): passive marker; the Empowerment / Gathering Flames rows do the work -------
power_of_the_elements_202526 = _rank(
    202526, 'Power of the Elements', [_dummy()], ICON_POTE, 30,
    'While one of your elementals is active, you gain its Elemental Empowerment, increasing the damage of its matching '
    'spells by 10%. Earth Elemental: Earth Shock and Earthquake. Fire Elemental: Lava Burst, Flame Shock, Fire Nova and '
    'your Fire totems; each Lava Burst you cast grants Gathering Flames, increasing the damage of your Flame Shock by '
    '20%, stacking up to 5 times until the Fire Elemental expires. Water Elemental: Frost Shock and Elemental Blast. '
    'Storm Elemental: Lightning Bolt, Chain Lightning and Thunderstorm, and your Chain Lightning jumps to 2 additional '
    'targets. Each elemental\'s own damage is also empowered. Your Earth Elemental no longer taunts or generates threat, '
    'and your Water Elemental deals 30% more damage.',
    'marker (DUMMY): the AllCreatureScript hooks read HasAura(202526) to add / remove the Empowerment buffs '
    '202560-202563 and the guardian auras.',
)

# ---- Conduit of the Elements (60283, row 7): marker -------------------------------------------------------------------
conduit_of_the_elements_202527 = _rank(
    202527, 'Conduit of the Elements', [_dummy()], ICON_CONDUIT, 45,
    _desc('Reduces the shared lockout between your elementals to 30 sec.',
          'Your Mastery increases your Elemental Empowerment.', True),
    'marker (DUMMY): Shaman::GetElementalLockoutBaseMs returns CONDUIT_LOCKOUT_MS with it; the capstone (Empowerment '
    '= 10% + Mastery) is part of the same marker (single rank, so the capstone line is plain).',
)

# ---- Icefury (60284, row 8): marker; charge buff 202566 ----------------------------------------------------------------
icefury_202528 = _rank(
    202528, 'Icefury', [_dummy()], ICON_ICEFURY, 50,
    'Casting Elemental Blast grants 1 charge of Icefury for 15 sec. Your Frost Shock consumes a charge to ignore its '
    'cooldown and deal 100% more damage. While one of your elementals is active, a Frost Shock that consumes a charge '
    'restores 5% of your maximum mana. While your Water Elemental is active, Elemental Blast grants 2 additional '
    'charges.',
    'marker (DUMMY): spell_sha_ele_spell_hooks (on Elemental Blast 202282) grants the charge buff 202566. 2026-10-20 '
    'smoke-test fix pass: the mana refund works in every elemental window, not only Water (user ruling).',
)


# ---- Fusion of Elements (60285, row 8): Elemental Blast +10/20%; capstone buffs 202576-202578 (C++) -------------------
_FUSION_CAPSTONE = ('Your Elemental Blast grants you a bonus for 10 sec based on your active elemental. Fire: 10% '
                    'critical strike damage bonus. Storm: 5% haste. Earth, Water or no elemental: 5% Mastery.')


def _fusion(spell_id: int, pct: int, last: bool):
    return _rank(
        spell_id, 'Fusion of Elements', [_mod(SpellModOp.DAMAGE, True, pct - 1)], ICON_FUSION, 50,
        _desc(f'Increases the damage of your Elemental Blast by {pct}%.', _FUSION_CAPSTONE, last),
        f'Fusion of Elements rank {pct // 10}: SPELLMOD_DAMAGE pct +{pct}% on Elemental Blast (d2 b20). Rank 2 is the '
        f'capstone (C++ picks 202576-8 on an EB cast).',
        **_emask(1, (0, 0, ELEMENTAL_BLAST)),
    )


fusion_rank1_202529 = _fusion(202529, 10, False)
fusion_rank2_202530 = _fusion(202530, 20, True)
# The brief names the variables fusion_of_elements_rank1 / _rank2; the header names (SPELL_FUSION_RANK1 / 2) come from
# the first-bound variable name above (`_collect_var_names` uses setdefault over the module namespace).
fusion_of_elements_rank1_202529 = fusion_rank1_202529
fusion_of_elements_rank2_202530 = fusion_rank2_202530

# ---- Call of the Elements (60286, row 10): the castable IS the talent's single rank --------------------------------------
call_of_the_elements_202531 = spell(
    id=202531, name='Call of the Elements', school=School.NORMAL, attributes=ATTR0_NOT_SHAPESHIFTED, category=0,
    cast_time_ms=0, cooldown_ms=180000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=15,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=ICON_COTE,
    notes=NOTE + 'Call of the Elements (talent 60286 rank, SLA 30690): instant, 15% of base mana, RecoveryTime 180000 '
          '(Category 0; Cooldown Haste divides it, base >= 30 s), GCD 1500 / 133, no range (self), no family bits. '
          'Effect 1 is SPELL_EFFECT_DUMMY on the caster: spell_sha_ele_call_of_the_elements (OnEffectHitTarget, '
          'EFFECT_0, SPELL_EFFECT_DUMMY) casts the missing elementals as triggered casts (no cooldown / lockout) and '
          'extends the active one. Icon 3991 = the stock spell.',
    raw_overrides=_raw(
        'Summons each of your elementals that is not already active for 15 sec and extends your active elemental by '
        '15 sec. Does not trigger your elementals\' cooldowns or their shared lockout. 3 min cooldown.', '', 60,
        DefenseType=0, PreventionType=1, StartRecoveryCategory=133, StartRecoveryTime=1500,
    ),
)

# ---- Elemental Focus rank 2 (talent 574, row 2): mirror of the rewritten 16164; amount by rank is the script's --------
elemental_focus_rank2_202532 = spell(
    id=202532, name='Elemental Focus', school=School.NORMAL, attributes=ATTR0_PASSIVE_HIDDEN,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[_dummy(29)],
    spell_icon_id=ICON_FOCUS,
    notes=NOTE + 'Elemental Focus rank 2: mirrors A2\'s rank 1 (16164): the proc effect is a DUMMY whose value is the '
          'Clearcasting cost reduction live (30 = stored 29), AttributesEx3 0x4000000, ProcTypeMask 65536, ProcChance 100. '
          'Procs through the talent-chain key -16164 (A2\'s spell_proc row); spell_sha_ele_elemental_focus (-16164) casts '
          'Clearcasting 16246 and sets its cost cut from this effect\'s live value (FOCUS_COST_R1 / R2 document it).',
    raw_overrides=_raw(
        'After landing a critical strike with a Fire, Frost or Nature damage spell, you enter a Clearcasting state '
        'that reduces the mana cost of your next two Fire, Frost or Nature spells by 30%.', '', 20,
        AttributesEx3=67108864, ProcTypeMask=65536, ProcChance=100,
    ),
)

# ---- Call of Thunder ranks 2 / 3 (talent 562, row 4): crit +4 / +6% on LB, CL, Thunderstorm -------------------------------
_COT_CAPSTONE = 'Thunderstorm restores 100% more mana.'
COT_CAPSTONE_MANA_BP = 99              # SPELLMOD_EFFECT2 percent on Thunderstorm's energize (effect 2): stored live - 1


def _call_of_thunder(spell_id: int, pct: int, last: bool):
    effects = [_mod(SpellModOp.CRITICAL_CHANCE, False, pct - 1)]
    masks = _emask(1, (LB | CL, THUNDERSTORM, 0))
    if last:
        # Capstone: +100% on Thunderstorm's second effect (the 10% mana energize, ENERGIZE_PCT); Unit::ApplyEffectModifiers
        # runs SPELLMOD_EFFECT2 over effect index 1 of every cast, so the 10% becomes 20%.
        effects.append(_mod(SpellModOp.EFFECT2, True, COT_CAPSTONE_MANA_BP))
        masks.update(_emask(2, (0, THUNDERSTORM, 0)))
    return _rank(
        spell_id, 'Call of Thunder', effects, ICON_THUNDER, 30,
        _desc(f'Increases the critical strike chance of your Lightning Bolt, Chain Lightning and Thunderstorm by '
              f'{pct}%.', _COT_CAPSTONE, last),
        f'Call of Thunder +{pct}% crit, flat SPELLMOD_CRITICAL_CHANCE on LB d0 b0 / CL d0 b1 / Thunderstorm d1 b13 '
        f'(copies by parent bit). Rank 3 is the capstone (playtest fix pass 2 / P6): a second effect, pct '
        f'SPELLMOD_EFFECT2 +100% scoped to Thunderstorm d1 b13 only (effect-B mask), doubles Thunderstorm\'s energize '
        f'(its effect 2, ENERGIZE_PCT 10% -> 20%). Data only, no script. Replaces the stun-castable Thunderstorm rank 2.',
        **masks,
    )


call_of_thunder_rank2_202533 = _call_of_thunder(202533, 4, False)
call_of_thunder_rank3_202534 = _call_of_thunder(202534, 6, True)

# ---- Booming Echoes rank 3 (talent 2262, row 7): shocks + Elemental Blast +15%; capstone = Echo (C++) ------------------------
booming_echoes_rank3_202535 = _rank(
    202535, 'Booming Echoes', [_mod(SpellModOp.DAMAGE, True, 14), _mod(SpellModOp.DOT, True, 14)], ICON_ECHOES, 45,
    _desc('Increases the damage of your Shock spells and Elemental Blast by 15%.',
          'Each of your Lightning Overloads grants 1 Echo, stacking up to 10 times. Lasts 30 sec. Each Echo increases '
          'the damage of your next Earth Shock by 30% and its critical strike damage bonus by 10%. Summoning your Earth '
          'Elemental grants 5 Echoes. Earth Shock consumes all Echoes, or half of them while your Earth Elemental is active.', True),
    'Booming Echoes rank 3 (capstone): SPELLMOD_DAMAGE pct +15% on the three shocks (d0) and Elemental Blast (d2 b20), '
    'effect 2 SPELLMOD_DOT +15% on Flame Shock; same shape as A2\'s ranks 1 / 2. Echo 202565 is granted by the overload '
    'script when it casts a copy.',
    **_emask(1, (SHOCKS, 0, ELEMENTAL_BLAST)), **_emask(2, FLAME_SHOCK),
)

# ---- Elemental Oath rank 3 (talent 2049, row 7): self + party / raid spell crit +3% ----------------------------------------
# Stock 51466 / 51470 shape (area aura raid on the caster, 100 yd, aura 57, attributes 0x50, Ex6 0x40000000,
# Ex7 cleared by A2); no Clearcasting damage clause (Decision 1), so rank 3 is a single effect and is not touched by the
# SpellInfoCorrections.cpp:333 fix. Group 1035 membership follows the talent chain (Talent.dbc), nothing to declare.
elemental_oath_rank3_202536 = spell(
    id=202536, name='Elemental Oath', school=School.NORMAL, attributes=80, category=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AREA_AURA_RAID, base_points=2, implicit_target_a=TARGET_UNIT_CASTER,
                    apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE, misc_value=0, radius_yards=100.0)],
    spell_icon_id=ICON_OATH,
    notes=NOTE + 'Elemental Oath rank 3: +3% spell crit on the shaman and (area aura raid, 100 yd) the party / raid. '
          'Mirrors A2\'s rewritten 51466 / 51470 (attributes 80, AttributesEx6 0x40000000, AttributesEx7 cleared so the '
          'buff is not consolidated); no Clearcasting damage clause.',
    raw_overrides=_raw(
        'Increases your spell critical strike chance by 3%. Increases the spell critical strike chance of all party and '
        'raid members by 3%. Does not stack with other similar effects.', 'Spell critical strike chance increased.', 45,
        AttributesEx6=1073741824, SpellPriority=50,
    ),
)


# =====================================================================================================================
# Elemental Empowerment buffs 202560-202563 (Power of the Elements)
# =====================================================================================================================
# Effect 1 = SPELLMOD_DAMAGE pct +10% (the hooks / spell_sha_ele_empowerment rewrite the amount to 10 + Mastery with
# Conduit), effect 2 = the second mod where the window needs one (Fire: Flame Shock's DoT so the snapshot carries it;
# Storm: +2 Chain Lightning jumps), effect 3 = PERIODIC_DUMMY 1 s (spell_sha_ele_empowerment's OnEffectPeriodic, EFFECT_2).
# Infinite, visible, no stack / charge. Copies carry the parent bits, so the Storm window empowers them.
_EMPOWER_TEXT = 'Your elemental empowers your matching spells.'
_EMPOWER_PERIODIC_MS = 1000


def _empowerment(spell_id: int, name: str, icon: int, mask_d: tuple, notes: str, second: Effect | None = None,
                 second_mask=None):
    effects = [_mod(SpellModOp.DAMAGE, True, 9), second, _aura(AuraType.PERIODIC_DUMMY, 0, amplitude=_EMPOWER_PERIODIC_MS)]
    raw = _emask(1, mask_d)
    if second_mask is not None:
        raw.update(_emask(2, second_mask))
    return _buff(
        spell_id, name, effects, icon, -1, _EMPOWER_TEXT,
        f'Your {name.split()[0].lower()} elemental empowers its matching spells.',
        f'{name}: SPELLMOD_DAMAGE pct +10% (stored 9) on {notes}. Effect 3 PERIODIC_DUMMY (1 s) is the hook for '
        f'spell_sha_ele_empowerment (Conduit capstone: amount = 10 + Mastery, written to every mod effect).',
        **raw,
    )


empowerment_earth_202560 = _empowerment(
    202560, 'Earth Empowerment', ICON_EARTH, (EARTH_SHOCK, 0, EARTHQUAKE),
    'Earth Shock (d0 b20) and Earthquake cast + tick (d2 b19)',
)
empowerment_fire_202561 = _empowerment(
    202561, 'Fire Empowerment', ICON_FIRE, (FLAME_SHOCK | SEARING_MAGMA, LAVA_BURST | FIRE_NOVA_DAMAGE, 0),
    'Flame Shock (d0 b28), Searing / Magma bolts (d0 b30), Lava Burst (d1 b12) and Fire Nova damage 8349 (d1 b18 + b31); '
    'never d0 b29 / d1 b23 (the Fire Elemental is not a Fire totem). Effect 2 SPELLMOD_DOT +10% on Flame Shock so the '
    'periodic part is empowered (and snapshotted) too',
    second=_mod(SpellModOp.DOT, True, 9), second_mask=(FLAME_SHOCK, 0, 0),
)
empowerment_water_202562 = _empowerment(
    202562, 'Water Empowerment', ICON_WATER, (FROST_SHOCK, 0, ELEMENTAL_BLAST),
    'Frost Shock (d0 b31) and Elemental Blast (d2 b20)',
)
empowerment_storm_202563 = _empowerment(
    202563, 'Storm Empowerment', ICON_STORM, (LB | CL, THUNDERSTORM, 0),
    'Lightning Bolt (d0 b0), Chain Lightning (d0 b1) and Thunderstorm (d1 b13); effect 2 SPELLMOD_JUMP_TARGETS flat '
    '+2 (stored 1) on Chain Lightning, which adds to Frostbrand\'s (stock 3 + 2 + 2 = 7 <= 8)',
    second=_mod(SpellModOp.JUMP_TARGETS, False, 1), second_mask=(CL, 0, 0),
)

# ---- Gathering Flames: +20% per stack on Flame Shock damage and DoT, 5 stacks, until the Fire Elemental ends --------------
gathering_flames_202564 = _buff(
    202564, 'Gathering Flames',
    [_mod(SpellModOp.DAMAGE, True, 19), _mod(SpellModOp.DOT, True, 19)],
    ICON_FLAME_SHOCK, -1, 'Your Flame Shock deals more damage.',
    'Each Lava Burst you cast while the Fire Elemental is active increases the damage of your Flame Shock by 20%.',
    'Gathering Flames: SPELLMOD_DAMAGE + SPELLMOD_DOT pct +20% per stack (stored 19; mods multiply by stacks) on Flame '
    'Shock (d0 b28), CumulativeAura 5, infinite (cleared when the Fire Elemental expires, not on a CotE extension).',
    school=School.FIRE, stacks=5, **_emask(1, FLAME_SHOCK), **_emask(2, FLAME_SHOCK),
)

# ---- Booming Echo: 10 stacks, 30 s; +30% Earth Shock damage and +10% crit damage bonus per stack ---------------------------
booming_echo_202565 = _buff(
    202565, 'Booming Echo',
    [_mod(SpellModOp.DAMAGE, True, 29), _mod(SpellModOp.CRIT_DAMAGE_BONUS, True, 9)],
    ICON_ECHOES, 30000, 'Your next Earth Shock deals more damage.',
    'Each Echo increases the damage of your next Earth Shock by 30% and its critical strike damage bonus by 10%.',
    'Echo: SPELLMOD_DAMAGE pct +30% (stored 29) and SPELLMOD_CRIT_DAMAGE_BONUS pct +10% (stored 9) per stack on Earth '
    'Shock (d0 b20), CumulativeAura 10, 30 s (refreshed by each Echo; was 20 s, +10% damage until the 2026-10-20 burst ruling, then +20%). Read and consumed by the Earth Shock hook, no proc row.',
    stacks=10, **_emask(1, EARTH_SHOCK), **_emask(2, EARTH_SHOCK),
)

# ---- Icefury charges: Frost Shock ignores its cooldown and deals +100%, max 3 charges, 15 s --------------------------------
icefury_charges_202566 = _buff(
    202566, 'Icefury',
    [_mod(SpellModOp.COOLDOWN, True, -101), _mod(SpellModOp.DAMAGE, True, 99)],
    ICON_ICEFURY, 15000, 'Your Frost Shock ignores its cooldown and deals more damage.',
    'Your Frost Shock consumes a charge to ignore its cooldown and deal 100% more damage.',
    'Icefury: SPELLMOD_COOLDOWN pct -100% (stored -101) + SPELLMOD_DAMAGE pct +100% (stored 99) on Frost Shock '
    '(d0 b31), ProcCharges 3 (= ICEFURY_MAX_CHARGES, the engine cap), 15 s. Consumed through the REQ_SPELLMOD row at '
    'the bottom of this file. The script sets 1 / 3 charges and refreshes the duration.',
    school=School.FROST, charges=3, **_emask(1, FROST_SHOCK), **_emask(2, FROST_SHOCK),
)

# ---- Raw Power: stacks, refreshed, no cap but the engine's 255 ---------------------------------------------------------------
raw_power_202567 = _buff(
    202567, 'Raw Power', [_dummy()], ICON_RAW_POWER, 15000,
    'Your critical strikes build toward Lightning Mastery.',
    'Your critical strikes build toward Lightning Mastery.',
    'Raw Power: DUMMY stack holder, CumulativeAura 255 (engine max), 15 s (RAW_POWER_DURATION_MS), refreshed by every '
    'stack. No proc row; spell_sha_ele_lightning_mastery grants and consumes it.',
    stacks=255,
)

# ---- Lightning Mastery buff: +50% crit damage bonus, 8 s [tune] -----------------------------------------------------------------
lightning_mastery_buff_202568 = _buff(
    202568, 'Lightning Mastery', [_mod(SpellModOp.CRIT_DAMAGE_BONUS, True, 49)], ICON_RAW_POWER, 8000,
    'Critical strike damage increased.',
    'Increases your spell critical strike damage bonus by 50%.',
    'Lightning Mastery buff: SPELLMOD_CRIT_DAMAGE_BONUS pct +50% (stored 49) on every shaman Fire / Frost / Nature '
    'damage spell (FFN mask incl. Earthquake + Elemental Blast), 8 s [tune] (Q5). Applied / consumed by the script.',
    **_emask(1, FFN_MASK),
)

# ---- Lava Surge buff: next Lava Burst instant, 1 charge, 15 s ---------------------------------------------------------------------
lava_surge_buff_202569 = _buff(
    202569, 'Lava Surge', [_mod(SpellModOp.CASTING_TIME, True, -101)], ICON_LAVA_BURST, 15000,
    'Your next Lava Burst is instant.',
    'Your next Lava Burst within 15 sec is instant.',
    'Lava Surge: SPELLMOD_CASTING_TIME pct -100% (stored -101) on Lava Burst (d1 b12), ProcCharges 1, 15 s. A pct mod '
    'on a base of 0 is skipped (Player::ApplySpellMod), so the instant Lava Burst copy does not eat the charge.',
    school=School.FIRE, charges=1, **_emask(1, (0, LAVA_BURST, 0)),
)

# ---- Unrelenting Storm: haste per stack (3 stacks, 8 s), the ready marker and the target debuff ----------------------------------
unrelenting_storm_buff_202570 = _buff(
    202570, 'Unrelenting Storm', [_aura(AuraType.HASTE_ALL, 0)], ICON_US, 8000, 'Haste increased.',
    'Casting Lightning Bolt, Lava Burst or Elemental Blast increases your spell and melee haste.',
    'Unrelenting Storm haste: aura 193 (all haste; not in the Temporary Haste groups), CumulativeAura 3, 8 s. The '
    'base amount is a 1% placeholder per stack: the script sets the real per-rank amount (US_HASTE_TENTHS_R1..R3 = '
    '0.5 / 1 / 1.5% per stack; an integer aura cannot hold half a percent, so it writes round(tenths x stacks / 10)).',
    stacks=3,
)
unrelenting_storm_ready_202571 = _buff(
    202571, 'Unrelenting Storm', [_mod(SpellModOp.DAMAGE, True, 14)], ICON_US, 8000, '',
    'Your next Chain Lightning consumes your Unrelenting Storm stacks to deal 15% more damage.',
    'Unrelenting Storm ready: hidden SPELLMOD_DAMAGE pct +15% (stored 14) on Chain Lightning (d0 b1), ProcCharges 1, '
    '8 s. Granted with the third stack; consumed by the Chain Lightning hit through the REQ_SPELLMOD row at the bottom.',
    hidden=True, charges=1, **_emask(1, CL),
)
unrelenting_storm_debuff_202572 = spell(
    id=202572, name='Unrelenting Storm', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=50000.0, duration_ms=12000,
    effects=[_aura(AuraType.MOD_DAMAGE_FROM_CASTER, 9, 0, target=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=ICON_US,
    notes=NOTE + 'Unrelenting Storm debuff: aura 271 +10% (stored 9), per-caster, 12 s, mask = every shaman damage group '
          '(FFN mask: LB, CL, shocks, Searing / Magma, Lava Burst, Thunderstorm, Fire Nova damage, Earthquake cast + '
          'tick, Elemental Blast, Flametongue / Frostbrand Attack). Script-cast helper: range 50000, family 11 so '
          'IsAffectedOnSpell reads the mask. Does not stack: the same caster refreshes.',
    raw_overrides=_raw(
        'Takes more spell damage from the shaman.', 'Takes more spell damage from the shaman.', 1,
        DefenseType=1, PreventionType=1, **_emask(1, FFN_MASK),
    ),
)

# ---- Reverberation: +20% direct damage on the OTHER two shocks + Elemental Blast, 8 s, one cast ---------------------------------
_REVERB_TEXT = 'Your next different Shock deals more damage.'


def _reverberation(spell_id: int, source: str, school, other_shocks: int):
    return _buff(
        spell_id, 'Reverberation', [_mod(SpellModOp.DAMAGE, True, 19)], ICON_REVERB, 8000, _REVERB_TEXT,
        f'When you deal damage with {source}, the direct damage of your next different Shock spell or Elemental Blast '
        f'within 8 sec is increased by 20%.',
        f'Reverberation ({source} variant): SPELLMOD_DAMAGE pct +20% (stored 19; never DOT) on the other two shocks and '
        f'Elemental Blast (d2 b20), ProcCharges 1, 8 s. Granted by the script on the named shock\'s damage; consumed '
        f'by the next different shock / EB hit (REQ_SPELLMOD row at the bottom).',
        school=school, charges=1, **_emask(1, (other_shocks, 0, ELEMENTAL_BLAST)),
    )


reverberation_earth_202573 = _reverberation(202573, 'Earth Shock', School.NATURE, FLAME_SHOCK | FROST_SHOCK)
reverberation_frost_202574 = _reverberation(202574, 'Frost Shock', School.FROST, EARTH_SHOCK | FLAME_SHOCK)
reverberation_flame_202575 = _reverberation(202575, 'Flame Shock', School.FIRE, EARTH_SHOCK | FROST_SHOCK)

# ---- Fusion of Elements capstone buffs (10 s) --------------------------------------------------------------------------------------
fusion_fire_202576 = _buff(
    202576, 'Fusion of Elements', [_mod(SpellModOp.CRIT_DAMAGE_BONUS, True, 9)], ICON_FUSION, 10000,
    'Critical strike damage increased.', 'Your critical strike damage bonus is increased by 10%.',
    'Fusion (Fire): SPELLMOD_CRIT_DAMAGE_BONUS pct +10% (stored 9) on every shaman damage spell (FFN mask), 10 s. '
    'Flame Shock snapshots it at apply (SPELLMOD_CRIT_DAMAGE_BONUS reaches the periodic crit).',
    school=School.FIRE, **_emask(1, FFN_MASK),
)
fusion_storm_202577 = _buff(
    202577, 'Fusion of Elements', [_aura(AuraType.HASTE_ALL, 4)], ICON_FUSION, 10000, 'Haste increased.',
    'Your haste is increased by 5%.',
    'Fusion (Storm): aura 193 haste +5% (stored 4), 10 s, not in the Temporary Haste groups.',
)
fusion_mastery_202578 = _buff(
    202578, 'Fusion of Elements', [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 4, CR_MASTERY_BIT)], ICON_FUSION, 10000,
    'Mastery increased.', 'Your Mastery is increased by 5.',
    'Fusion (Earth / Water / none): aura 306 Mastery +5 (stored 4, misc 1 << 20), 10 s.',
)

# ---- Elemental Precision capstone: next Elemental Blast is a guaranteed critical strike, 20 s ----------------------------------------
precision_buff_202579 = _buff(
    202579, 'Elemental Precision', [_mod(SpellModOp.CRITICAL_CHANCE, False, 99)], ICON_PRECISION, 20000,
    'Your next Elemental Blast is a guaranteed critical strike.',
    'Your next Elemental Blast within 20 sec is a guaranteed critical strike.',
    'Elemental Precision buff: flat SPELLMOD_CRITICAL_CHANCE +100% (stored 99) on Elemental Blast (d2 b20), '
    'ProcCharges 1, 20 s. Consumed on the EB hit (crit is rolled at hit, so the row is HIT phase).',
    charges=1, **_emask(1, (0, 0, ELEMENTAL_BLAST)),
)

# ---- Elemental Devastation: Proc Chance bonus, 10 s, refreshed (amount set by rank by the script) --------------------------------------------
devastation_buff_202580 = _buff(
    202580, 'Elemental Devastation', [_aura(AuraType.MOD_CUSTOM_STAT_PCT, 2, CR_PROC_CHANCE_BIT)], ICON_DEVASTATION,
    10000, 'Proc Chance increased.',
    'Your non-periodic Fire, Frost and Nature spell critical strikes increase your Proc Chance.',
    'Elemental Devastation buff: aura 306 Proc Chance (misc 1 << 11), placeholder +3 (stored 2); spell_sha_ele_devastation '
    'sets 3 / 6 / 10 by rank (DEVASTATION_PC_R1..R3), 10 s, refreshes, never stacks.',
)

# ---- Elemental Reach capstone: +6% magic damage, 10 s ---------------------------------------------------------------------------------------
reach_buff_202581 = _buff(
    202581, 'Elemental Reach', [_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 5, SCHOOL_ALL_MAGIC)], ICON_REACH, 10000,
    'Magic damage increased.',
    'Your magic damage is increased by 6%.',
    'Elemental Reach buff: aura 79 magic damage +6% (stored 5, school mask 126), 10 s.',
)

# ---- Wind Rush capstone: haste +15% for 10 s ------------------------------------------------------------------------------------------------
wind_rush_haste_202582 = _buff(
    202582, 'Wind Rush', [_aura(AuraType.HASTE_ALL, 14)], ICON_WIND_RUSH, 10000, 'Haste increased.',
    'Your haste is increased by 15%.',
    'Wind Rush capstone buff: aura 193 haste +15% (stored 14), 10 s, refreshes, never stacks; not in the Temporary Haste '
    'groups.',
)

# ---- Rising Flames capstone: stacks to 5, kept until a Fire Nova consumes them ----------------------------------------------------------------------
rising_flames_buff_202583 = _buff(
    202583, 'Rising Flames', [_dummy()], ICON_RISING_FLAMES, -1, 'Your next Fire Nova deals more damage.',
    'Each stack increases the damage of your next Fire Nova by 10%.',
    'Rising Flames: DUMMY stack holder, CumulativeAura 5, infinite (until consumed). spell_sha_fire_nova_rework reads '
    'the stacks, scales the 8349 damage by 1 + 0.10 x stacks (RISING_FLAMES_PCT_PER_STACK) and removes it.',
    school=School.FIRE, stacks=5,
)

# ---- Elemental Fury capstone: hidden, while Clearcasting is up --------------------------------------------------------------------------------------
fury_capstone_202584 = _buff(
    202584, 'Elemental Fury', [
        _aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 7, SCHOOL_NATURE),
        _aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 4, SCHOOL_OTHER_MAGIC),
    ],
    ICON_FURY, -1, '', 'While Clearcasting is active, your Nature damage is increased by 8% and your other magic damage by 5%.',
    'Elemental Fury capstone: hidden aura 79 Nature +8% (stored 7, misc 8) and other magic +5% (stored 4, misc 118). '
    'Elemental Blast (Fire + Frost + Nature) takes both (+13.4%, Q15). Added / removed by spell_sha_ele_fury_capstone '
    'with Clearcasting 16246.',
    hidden=True,
)

# ---- Elemental Warding capstone: +10% maximum health while the Earth Elemental is up -----------------------------------------------------------------
warding_health_202585 = _buff(
    202585, 'Elemental Warding', [_aura(AURA_MOD_INCREASE_HEALTH_PERCENT, 9)], ICON_WARDING, -1,
    'Maximum health increased.',
    'While your Earth Elemental is active, your maximum health is increased by 10%.',
    'Elemental Warding capstone: aura 133 max health +10% (stored 9), infinite, added / removed with the Earth Elemental.',
    school=School.NORMAL,
)

# ---- Guardian-side auras (owner-added, L5): hidden, death-persistent, infinite -----------------------------------------------------------------------
earth_elemental_damage_202586 = _buff(
    202586, 'Elemental Warding', [_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 19, SCHOOL_ALL)], ICON_EARTH, -1, '',
    'Increases the damage dealt by your Earth Elemental by 20%.',
    'Earth Elemental +20% damage (Elemental Warding capstone): aura 79 all schools (stored 19), owner-added on the guardian.',
    hidden=True, guardian=True,
)
water_elemental_damage_202587 = _buff(
    202587, 'Power of the Elements', [_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 29, SCHOOL_ALL)], ICON_WATER, -1, '',
    'Increases the damage dealt by your Water Elemental by 30%.',
    'Water Elemental +30% damage (Power of the Elements): aura 79 all schools (stored 29), owner-added on the guardian. '
    'Healing is never raised (aura 79 does not touch heals).',
    hidden=True, guardian=True,
)
elemental_empowered_202588 = _buff(
    202588, 'Elemental Empowerment', [_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 9, SCHOOL_ALL)], ICON_FIRE, -1, '',
    'Increases the damage dealt by this elemental by 10%.',
    'Guardian-side Empowerment: aura 79 all schools +10% (stored 9); Shaman::RefreshEmpowerment rewrites the amount to '
    '10 + Mastery with Conduit. Owner-added on each guardian.',
    hidden=True, guardian=True,
)
earth_elemental_no_threat_202589 = _buff(
    202589, 'Power of the Elements', [_aura(AURA_MOD_THREAT, -101, SCHOOL_ALL)], ICON_EARTH, -1, '',
    'Your Earth Elemental generates no threat.',
    'Earth Elemental threat -100% (stored -101, all schools), owner-added on the guardian (L5). The AI also skips Angered '
    'Earth 36213 (pet_shaman_rework.cpp).',
    hidden=True, guardian=True,
)

# ---- Astral Shift: plain (-10%, script sets by rank / CC) and empowered (-25%, 6 s) ------------------------------------------------------------------------
astral_shift_buff_202590 = _buff(
    202590, 'Astral Shift', [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -11, SCHOOL_ALL)], ICON_ASTRAL, -1,
    'Damage taken reduced.',
    'You shift into the Astral Plane, reducing all damage taken by 10%.',
    'Astral Shift: aura 87 all schools -10% (stored -11), infinite; ShamanAstralShiftUnitScript (OnAuraApply) adds it '
    'while stunned / feared / silenced and removes it when the CC ends (ASTRAL_SHIFT_PLAIN_PCT).',
)
astral_shift_empowered_202595 = _buff(
    202595, 'Empowered Astral Shift', [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -26, SCHOOL_ALL)], ICON_ASTRAL, 6000,
    'Damage taken reduced.',
    'You shift into the Astral Plane, reducing all damage taken by 25% for 6 sec.',
    'Empowered Astral Shift: aura 87 all schools -25% (stored -26), 6 s (ASTRAL_SHIFT_EMPOWERED_MS); replaces the plain '
    'one while it lasts (the script removes 202590 and re-adds it after).',
)


# =====================================================================================================================
# Lightning Overload copies 202591-202593 (Decision 13)
# =====================================================================================================================
# 50% of the parent's potency at the parent's cast-time basis (T = 2000), NO_THREAT, triggered-only, instant, free, no
# cooldown, no range beyond the parent's 30 yd. They carry the PARENT bits (the one allowed exception to FB 4.3: Concussion,
# Convection, Shamanism, Call of Thunder, Frostbrand, the Storm Empowerment and Echo reach them by bit) and neither
# NOT_A_PROC (SH0a-CODE-REVIEW m2) nor SPELL_ATTR6_IGNORE_CASTER_DAMAGE_MODIFIERS (they keep caster mods). The Lava Burst
# copy carries family 11 + d1 b12 so Unit.cpp:9136 auto-crits it on the shaman's own Flame Shock (Q14).
# NOTE (needs B2): the Frostbrand (+2) and Storm (+2) SPELLMOD_JUMP_TARGETS mods match the Chain Lightning copy by its d0 b1
# bit, so it would jump; spell_sha_ele_overload_copy must trim the CL copy's targets to the primary one.
# AttributesEx2 0x4 (S1a review m3): triggered casts still run the caster-to-target LoS check, and a Chain Lightning jump
# target can be visible to the previous target only. The copy is only ever cast at a target the parent just hit, so the
# parent's own LoS filtering stands in for it.
def _overload_copy(spell_id: int, name: str, school, parent, parent_t_ms: int, mask_d0: int, mask_d1: int, level: int,
                   icon: int, speed: float, visual: int, description: str, chain_amp: float = 1.0):
    potency = parent.effects[0].sp_potency / 2
    return spell(
        id=spell_id, name=name, school=school, attributes=0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=potency, potency_kind='direct',
                        time_basis_ms=parent_t_ms, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
        spell_icon_id=icon,
        notes=NOTE + f'{name} Lightning Overload copy: potency {potency:g} = half of the parent ({parent.id}) at T '
              f'{parent_t_ms}; AttributesEx NO_THREAT (0x400), AttributesEx2 IGNORE_LINE_OF_SIGHT (0x4: a Chain Lightning jump target is '
              f'LoS-checked from the previous target, not the shaman; the copy is only cast at a target the parent '
              f'just hit); parent bits d0 {mask_d0:#x} / d1 {mask_d1:#x}; no '
              f'NOT_A_PROC, no IGNORE_CASTER_DAMAGE_MODIFIERS; single target. Cast triggered by '
              f'spell_sha_ele_lightning_overload; spell_sha_ele_overload_copy rolls Shamanism / Echo.',
        raw_overrides=_raw(
            description, '', level, AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LOS, DefenseType=1,
            PreventionType=1, Speed=speed,
            SpellVisualID_1=visual, InterruptFlags=15, FacingCasterFlags=0,
            EffectChainAmplitude_1=chain_amp,
            **({'SpellClassMask_1': mask_d0} if mask_d0 else {}), **({'SpellClassMask_2': mask_d1} if mask_d1 else {}),
        ),
    )


lightning_bolt_overload_202591 = _overload_copy(
    202591, 'Lightning Bolt', School.NATURE, lightning_bolt_403, 2000, LB, 0, 1, ICON_LB, 20.0, 173,
    'Casts a bolt of lightning at the target for {pot1} Nature damage.',
)
chain_lightning_overload_202592 = _overload_copy(
    202592, 'Chain Lightning', School.NATURE, chain_lightning_421, 2000, CL, 0, 32, ICON_CL, 20.0, 36,
    'Hurls a lightning bolt at the enemy, dealing {pot1} Nature damage.',
    chain_amp=0.7,   # the parent's per-jump factor, as a safety net if a jump leaks through (script trims to 1 target)
)
lava_burst_overload_202593 = _overload_copy(
    202593, 'Lava Burst', School.FIRE, lava_burst_51505, 2000, 0, LAVA_BURST, 42, ICON_LAVA_BURST, 24.0, 11565,
    'You hurl molten lava at the target, dealing {pot1} Fire damage. If your Flame Shock is on the target, Lava Burst '
    'will deal a critical strike.',
)
for _copy in (lightning_bolt_overload_202591, chain_lightning_overload_202592, lava_burst_overload_202593):
    scripted_by(_copy, 'spell_sha_ele_overload_copy')


# SkillLineAbility: CotE (talent-granted, so the spell is learned with the talent).
skill_line_ability(id=30690, skill_line=375, spell_id=call_of_the_elements_202531.id, class_mask=64, acquire_method=0)

# ---- Script bindings on ids this file owns ------------------------------------------------------------------------------------------------
scripted_by(call_of_the_elements_202531, 'spell_sha_ele_call_of_the_elements')
for _empower in (empowerment_earth_202560, empowerment_fire_202561, empowerment_water_202562, empowerment_storm_202563):
    scripted_by(_empower, 'spell_sha_ele_empowerment')


# =====================================================================================================================
# Consumption rows (PROC_ATTR_REQ_SPELLMOD = 0x8): the charged mod buffs above are spent by the cast / hit they modify.
# Hostile magic damage-class casts are PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG (0x10000). CAST phase (1) where the mod is
# applied while casting (Icefury's cooldown, Lava Surge's cast time); HIT phase (2) where it is applied at damage / crit
# time (Reverberation, Unrelenting Storm ready, Elemental Precision). Chance 100, charges = the DBC ProcCharges.
# =====================================================================================================================
PROC_FLAG_DONE_MAGIC_NEG = 0x10000
PROC_ATTR_REQ_SPELLMOD = 0x8
PHASE_CAST = 0x1
PHASE_HIT = 0x2
TYPE_ALL = 7
TYPE_DAMAGE = 1


def _consume(buff, mask, phase: int, charges: int):
    procs_on(
        buff, proc_flags=PROC_FLAG_DONE_MAGIC_NEG, family_name=SPELLFAMILY_SHAMAN, family_mask=mask,
        spell_type_mask=TYPE_ALL if phase == PHASE_CAST else TYPE_DAMAGE, spell_phase_mask=phase,
        attributes_mask=PROC_ATTR_REQ_SPELLMOD, chance=100, charges=charges,
    )


_consume(icefury_charges_202566, (FROST_SHOCK, 0, 0), PHASE_CAST, 3)
_consume(lava_surge_buff_202569, (0, LAVA_BURST, 0), PHASE_CAST, 1)
_consume(unrelenting_storm_ready_202571, (CL, 0, 0), PHASE_HIT, 1)
_consume(reverberation_earth_202573, (FLAME_SHOCK | FROST_SHOCK, 0, ELEMENTAL_BLAST), PHASE_HIT, 1)
_consume(reverberation_frost_202574, (EARTH_SHOCK | FLAME_SHOCK, 0, ELEMENTAL_BLAST), PHASE_HIT, 1)
_consume(reverberation_flame_202575, (EARTH_SHOCK | FROST_SHOCK, 0, ELEMENTAL_BLAST), PHASE_HIT, 1)
_consume(precision_buff_202579, (0, 0, ELEMENTAL_BLAST), PHASE_HIT, 1)


# --- Class-table bindings on stock ids (S1a brief: assigned by the orchestrator) ---
# One hook class on every Elemental damage spell the rework watches (player-caster gate inside the script).
for _hook_spell in (403, 421, 51505, 202282, 8042, 8050, 8056):
    scripted_by(_hook_spell, 'spell_sha_ele_spell_hooks')
unbind_script(-8050, 'spell_sha_flame_shock')                 # stock Lava Flows dispel hook: Lava Flows is cast-based now
scripted_by(57994, 'spell_sha_ele_wind_rush')                 # Wind Rush capstone (interrupt success)
unbind_script(-1535, 'spell_sha_fire_nova')                   # baseline Fire Elemental eruption + Rising Flames
scripted_by(-1535, 'spell_sha_fire_nova_rework')
