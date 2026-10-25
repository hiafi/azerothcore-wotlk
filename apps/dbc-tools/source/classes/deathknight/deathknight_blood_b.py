"""
Death Knight - S1a Blood: new rows 203138-203156 (Voracious, Crimson Communion, Blood Nova, Purgatory, Bonestorm, Blood
Shield, Subversion Runic Power, Vendetta strike, Blood Gorged poll, Dancing Rune Weapon parry buff), the link rows that
attach them to the stock Vendetta / Dancing Rune Weapon / Blood Gorged ranks, and the script numbers they own.
Source of truth: docs/reworks/death-knight-blood-rework.md (section 5: tooltips and aura texts verbatim, minus the
"N min cooldown." sentences) and .agents/plans/death-knight-rework/death-knight-rework.S1a-WP-BRIEF.md (rulings D1-D10,
id map, known data facts), S1-HANDOFF U5-U12, U15, U18-U23.

Ids and header names (generator rule: lowest id of a name gets SPELL_<NAME>, a second same-name row gets _<id>):
203138 / 203139 Voracious r1 / r2 (capstone) · 203140 Voracious Heal · 203141 Crimson Communion · 203142 Crimson Communion
Heal · 203143 Blood Nova · 203144 Blood Nova Eruption · 203145 Purgatory · 203146 Shroud of Purgatory · 203147 Purgatory
Lockout · 203148 Bonestorm · 203149 Bonestorm Tick · 203150 Bonestorm Heal · 203151 Blood Shield · 203152 Subversion
Runic Power · 203153 Vendetta Strike · 203154 Vendetta Strike Heal · 203155 Blood Gorged Mastery · 203156 Dancing Rune
Weapon Parry. The talent / SkillLineAbility rows of the three castables (Crimson Communion, Blood Nova, Bonestorm) and
of the two passives (Voracious, Purgatory) are deathknight_talents.py's (granted_by_talent).

Conventions: SpellClassSet 15 on every row, EquippedItemClass -1, CastingTimeIndex 1 on instants, GCD 133 / 1500 on the
three castables (magic / none class, no IS_ABILITY, so the core spell-haste GCD branch covers them: Spell.cpp
TriggerGlobalCooldown), SpellLevel = 9 + 5 x row + rank (brief D3), stored static base points = live - 1, visible buffs
are not passive and carry no consolidation flag, aura texts are number-free. Heals whose amount a script passes
(CastCustomSpell BASE_POINT0) are potency_excluded with the reason. Family bits come from _masks.py: d2 b13
BLOOD_OTHER_MAGIC on the two Shadow damage rows, d2 b15 DK_SELF_HEAL on the DK's self-heal group; no bit on the castables,
the Purgatory rows, Blood Shield, the parry buff and the hidden passives (FB 4.3).
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, RANGE_SELF, School
from lib.dsl.registry import (
    bonus_coefficients, const, linked_spell, pot_text, procs_on, scripted_by, spell, unbind_script,
)

from . import _masks as m

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_ATTR0_PASSIVE = 0x40
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR0_NO_IMMUNITIES = 0x20000000
_ATTR0_NO_AURA_CANCEL = 0x80000000
_ATTR1_USE_ALL_MANA = 0x2
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000
_ATTR5_SPELL_HASTE_AFFECTS_PERIODIC = 0x2000
_HIDDEN_PASSIVE = _ATTR0_PASSIVE | _ATTR0_DO_NOT_DISPLAY
_TALENT_PASSIVE = 464                      # 0x1D0, the stock talent-rank passive frame (Vendetta 49015)
_SPELLFAMILY_DEATHKNIGHT = 15

# ---- Aura types not in the DSL enum (src/server/game/Spells/Auras/SpellAuraDefines.h) ----
_AURA_MOD_PARRY_PERCENT = 47
_AURA_MOD_HEALTH_REGEN_PERCENT = 88
_AURA_SCHOOL_HEAL_ABSORB = 301

# ---- Misc values / targets (SharedDefines.h) ----
_MISC_ALL_SCHOOLS = 127
_MISC_POWER_RUNIC_POWER = 6
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_CASTER_AREA_PARTY = 20

# ---- spell_proc masks (src/server/game/Spells/SpellMgr.h) ----
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x10
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_PHASE_HIT = 0x2

# ---- Stock icons / visuals (0-verify item 4) ----
_SV_BONE_STORM = 7428           # Marrowgar Bone Storm 69076 (the aura)
_SV_BLOOD_NOVA = 15283          # Saurfang Blood Nova 72378
_SV_BLOOD_QUEEN_ESSENCE = 15344  # Essence of the Blood Queen 70871
_SV_HARVEST_SOUL = 14539        # Harvest Soul 68980 (P0's Shroud)
_SV_POWER_WORD_SHIELD = 784     # Power Word: Shield, every rank

# Script numbers (D8 tier 3: not tooltip numbers, not potency). Every [tune] value changes here, never in C++.
BLOOD_SHIELD_CAP_PCT = const(
    'BLOOD_SHIELD_CAP_PCT', 30, 'Blood Shield stacks up to this percent of the Death Knight\'s CURRENT maximum health '
    '(Vampiric Blood counts) [fixed].',
)
BLOOD_NOVA_COST_PCT = const(
    'BLOOD_NOVA_COST_PCT', 10, 'Blood Nova health cost, percent of maximum health; the cast is refused at or below it '
    '[fixed].',
)
BLOOD_NOVA_DAMAGE_PCT = const(
    'BLOOD_NOVA_DAMAGE_PCT', 20, 'Blood Nova eruption damage, percent of maximum health at cast time, per enemy [fixed].',
)
BLOOD_NOVA_DELAY_MS = const(
    'BLOOD_NOVA_DELAY_MS', 1000, 'Delay between the Blood Nova cast and its eruption [fixed].', cpp_type='uint32',
)
BONESTORM_MIN_RP = const(
    'BONESTORM_MIN_RP', 10, 'Minimum Runic Power (display units) Bonestorm needs to be cast [tune].',
)
BONESTORM_MS_PER_10_RP = const(
    'BONESTORM_MS_PER_10_RP', 1000, 'Bonestorm duration in milliseconds per 10 Runic Power spent [tune].',
    cpp_type='uint32',
)
BONESTORM_MAX_MS = const(
    'BONESTORM_MAX_MS', 10000, 'Bonestorm maximum duration in milliseconds [tune].', cpp_type='uint32',
)
BONESTORM_HEAL_PCT = const(
    'BONESTORM_HEAL_PCT', 1, 'Percent of current maximum health Bonestorm heals per enemy hit per tick [tune].',
)
BONESTORM_HEAL_TARGET_CAP = const(
    'BONESTORM_HEAL_TARGET_CAP', 5, 'Enemies per Bonestorm tick that count toward its heal [tune].', cpp_type='uint8',
)
CRIMSON_COMMUNION_LEECH_PCT = const(
    'CRIMSON_COMMUNION_LEECH_PCT', 15, 'Percent of the damage each affected player deals that heals them while Crimson '
    'Communion lasts [fixed].',
)
BLOOD_GORGED_THRESHOLD_PCT = const(
    'BLOOD_GORGED_THRESHOLD_PCT', 75, 'Blood Gorged applies above this percent of maximum health (the core aura state '
    '23 threshold, kept in step by hand) [fixed].',
)
BLOOD_GORGED_MASTERY_SHARE_PCT = const(
    'BLOOD_GORGED_MASTERY_SHARE_PCT', 50, 'Percent of Mastery the Blood Gorged capstone adds to the damage bonus [tune].',
)
BLOODWORM_CAP = const(
    'BLOODWORM_CAP', 8, 'Bloodworms alive per Death Knight; the oldest are replaced past it [fixed].', cpp_type='uint8',
)
BLOODWORM_HEAL_PCT = const(
    'BLOODWORM_HEAL_PCT', 100, 'Percent of a Bloodworm\'s damage that heals its owner (stock 150) [tune].',
)
VENDETTA_STRIKE_HEAL_PCT_RANK1 = const(
    'VENDETTA_STRIKE_HEAL_PCT_RANK1', 5, 'Vendetta rank 1: percent of the Heart Strike / Marrowrend damage healed '
    '[tune].',
)
VENDETTA_STRIKE_HEAL_PCT_RANK2 = const(
    'VENDETTA_STRIKE_HEAL_PCT_RANK2', 10, 'Vendetta rank 2: percent of the Heart Strike / Marrowrend damage healed '
    '[tune].',
)
VENDETTA_STRIKE_HEAL_PCT_RANK3 = const(
    'VENDETTA_STRIKE_HEAL_PCT_RANK3', 15, 'Vendetta rank 3: percent of the Heart Strike / Marrowrend damage healed '
    '[tune].',
)


def _grey(text):
    """The capstone line on a rank below the last (paladin / hunter rank-text convention)."""
    return f'|cFF9D9D9D{text}|r'


def _self_heal(spell_id, name, level, icon, description, notes, *, magic_class=False, suppress_procs=False):
    """One DK self-heal helper: a HEAL on the caster whose amount a script passes (CastCustomSpell BASE_POINT0), d2 b15.
    `magic_class` = DefenseType 1 plus the all-zero spell_bonus_data row (the 45470 shape: Versatility and healing-done
    percent apply, spell power stays out, U23); otherwise DmgClass NONE with no row, so neither applies (a leech heal's
    damage already carried Versatility)."""
    raw = {
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT,
        'SpellClassMask_3': m.DK_SELF_HEAL,
        'EquippedItemClass': -1,
        'CastingTimeIndex': 1,
        'SpellLevel': level,
        'Description_Lang_enUS': description,
    }
    if magic_class:
        raw['DefenseType'] = 1
    if suppress_procs:
        raw['AttributesEx3'] = _ATTR3_SUPPRESS_CASTER_PROCS
    s = spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[
            Effect(type=EffectType.HEAL, implicit_target_a=_TARGET_UNIT_CASTER,
                   potency_excluded=notes[0]),
        ],
        spell_icon_id=icon, notes=notes[1], raw_overrides=raw,
    )
    if magic_class:
        bonus_coefficients(s, direct=0.0, dot=0.0, ap=0.0, ap_dot=0.0,
                           comment=f'Death Knight - {name}: no spell power; DefenseType 1 only so Versatility applies')
    return s


# =====================================================================================================================
# Voracious (row 6, 2 ranks): leech 2 / 4% of all damage dealt; the capstone (rank 2) raises the DK's own healing taken
# =====================================================================================================================

_VORACIOUS_TEXT = 'You are healed for {pct}% of all damage you deal.'
_VORACIOUS_CAPSTONE = ('Capstone: Your Mastery increases the healing you receive from your own Death Knight abilities '
                       'and talents.')


def _voracious_rank(spell_id, rank, base_points, level):
    capstone = rank == 2
    text = _VORACIOUS_TEXT.format(pct=2 * rank)
    text += '\n\n' + (_VORACIOUS_CAPSTONE if capstone else _grey(_VORACIOUS_CAPSTONE))
    return spell(
        id=spell_id, name='Voracious', school=School.NORMAL, attributes=_TALENT_PASSIVE, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[
            Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=base_points,
                   implicit_target_a=_TARGET_UNIT_CASTER),
        ],
        spell_icon_id=147,
        notes=(
            f'S1a Blood (6,2) Voracious rank {rank}: hidden passive talent aura (frame of stock Vendetta 49015). Effect 1 '
            f'DUMMY stored {base_points} = live {2 * rank}: the leech percent the '
            'UnitScript OnDamage hook reads live (GetAuraEffect(203139, 0) else 203138). '
            + ('Rank 2 is the capstone: HasAura(203139) gates DeathKnight::ApplyVoraciousCapstone (Mastery 1:1 on the '
               'DK\'s own heals, U6). ' if capstone else '')
            + f'SpellLevel {level} = 9 + 5 x 6 + {rank} (D3). No family bits, no proc row (U5: the leech is cast from '
              'OnDamage, not procced).'
        ),
        raw_overrides={
            'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
            'SpellLevel': level, 'ProcChance': 101, 'Description_Lang_enUS': text,
        },
    )


voracious_203138 = _voracious_rank(203138, 1, 1, 40)
voracious_203139 = _voracious_rank(203139, 2, 3, 41)

# The leech heal: cast by DeathKnight::OnDamageDealt on the DK itself, amount = damage x leech %, per target hit.
# A leech heal's damage already carried Versatility, so it stays DmgClass NONE with no bonus row (U23).
voracious_heal_203140 = _self_heal(
    203140, 'Voracious Heal', 40, 147,
    'Heals you for a share of the damage you deal.',
    ('percent of damage dealt: the amount comes from the damage event via CastCustomSpell, not CalcValue',
     'S1a Blood (6,2) U5: the Voracious leech. HEAL on the caster, value 0 in data (script BASE_POINT0 = leech % of the '
     'damage dealt). DefenseType 0 and no spell_bonus_data row, so neither Versatility nor spell power applies (U23). d2 '
     'b15 DK_SELF_HEAL (counts for the capstone; the helper skips it as a heal source so it never doubles). '
     'SUPPRESS_CASTER_PROCS and TRIGGERED_FULL_MASK on the cast: it rolls no procs and, being a heal, never recurses '
     'into OnDamage. Cast from UnitScript::OnDamage so it fills the Shroud and takes Vampiric Blood.'),
    suppress_procs=True,
)

# =====================================================================================================================
# Crimson Communion (row 6, 1 rank): castable party leech
# =====================================================================================================================

crimson_communion_203141 = spell(
    id=203141, name='Crimson Communion', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, power_type=PowerType.MANA, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER_AREA_PARTY,
               radius_yards=40.0),
    ],
    spell_icon_id=3176,
    notes=(
        'S1a Blood (6,3) U21: instant, GCD 133 / 1500 (magic class, core-hasted), 120 s Cooldown Haste (core: base cooldown '
        '>= 30 s), no cost (no rune, no Runic Power: Classless can use it), self range. Effect 1 APPLY_AURA DUMMY on '
        'TARGET_UNIT_CASTER_AREA_PARTY radius 40 yd (the DK and party members; spell_dk_crimson_communion drops every '
        'non-player: pets, guardians, totems), 10 s visible buff (not passive, no consolidation flag), SpellVisual 15344 '
        '(Essence of the Blood Queen, 0-verify item 4). The leech percent is the const CRIMSON_COMMUNION_LEECH_PCT; each '
        'affected player casts 203142 on themselves from their own damage (DeathKnight::OnDamageDealt). DefenseType 1 / '
        'PreventionType 1 (a silenced Death Knight cannot cast it). SpellLevel 40 = 9 + 5 x 6 + 1 (D3). No family bits '
        '(FB 4.3). SLA 30742 / talent 60337 are deathknight_talents.py\'s (granted_by_talent).'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 40,
        'DefenseType': 1, 'PreventionType': 1, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
        'SpellVisualID_1': _SV_BLOOD_QUEEN_ESSENCE,
        'Description_Lang_enUS': 'You and your party members within 40 yards are healed for 15% of the damage you deal '
                                 'for 10 sec.',
        'AuraDescription_Lang_enUS': 'Healed by a share of the damage you deal.',
    },
)
scripted_by(crimson_communion_203141, 'spell_dk_crimson_communion')

# Cast by each affected player on themselves (a Death Knight's talents do not raise another player's leech; their own
# healing-taken effects do). Tagged d2 b15 for the DK's own share (the capstone reads it); a non-DK caster never has 203139.
crimson_communion_heal_203142 = _self_heal(
    203142, 'Crimson Communion Heal', 40, 3176,
    'Heals you for a share of the damage you deal.',
    ('percent of damage dealt: the amount comes from the damage event via CastCustomSpell, not CalcValue',
     'S1a Blood (6,3) U21: the Crimson Communion leech heal, cast by each affected player on themselves (their own '
     'healing-taken mods apply, the DK\'s talents do not). HEAL on the caster, value 0 in data (script BASE_POINT0 = '
     'CRIMSON_COMMUNION_LEECH_PCT % of the damage dealt). DefenseType 0 and no bonus row (U23). d2 b15 DK_SELF_HEAL '
     'marks the Death Knight\'s own share for the Voracious capstone (a non-DK never knows 203139). '
     'SUPPRESS_CASTER_PROCS: rolls no procs.'),
    suppress_procs=True,
)

# =====================================================================================================================
# Blood Nova (row 7, 1 rank): castable, health cost, delayed Shadow eruption
# =====================================================================================================================

blood_nova_203143 = spell(
    id=203143, name='Blood Nova', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=60000,
    category_cooldown_ms=0, power_type=PowerType.MANA, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=2957,
    notes=(
        'S1a Blood (7,2) U10: instant, GCD 133 / 1500 (magic class, core-hasted), 60 s Cooldown Haste (core), self range, no '
        'cost row (the health cost is spell_dk_blood_nova: CheckCast refuses at <= BLOOD_NOVA_COST_PCT of max health, OnCast '
        'ModifyHealth, never DealDamage). One DUMMY effect on the caster; the script schedules the eruption 203144 after '
        'BLOOD_NOVA_DELAY_MS at BLOOD_NOVA_DAMAGE_PCT of max health. SpellVisual 15283 (Saurfang Blood Nova 72378, 0-verify '
        'item 4) on the cast. DefenseType 1 / PreventionType 1. SpellLevel 45 = 9 + 5 x 7 + 1 (D3). No family bits (FB 4.3). '
        'SLA 30743 / talent 60338 are deathknight_talents.py\'s (granted_by_talent).'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 45,
        'DefenseType': 1, 'PreventionType': 1, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
        'SpellVisualID_1': _SV_BLOOD_NOVA,
        'Description_Lang_enUS': 'Sacrifice 10% of your maximum health. After 1 sec, your blood erupts, dealing Shadow '
                                 'damage equal to 20% of your maximum health to all enemies within 8 yards.',
    },
)
scripted_by(blood_nova_203143, 'spell_dk_blood_nova')

# The eruption: cast by the cast script at the DK, TRIGGERED_FULL_MASK, BASE_POINT0 = 20% of the max health at cast time.
# Shadow, magic class, crit, percent damage mods apply; zero bonus row so neither attack power nor spell power adds.
blood_nova_eruption_203144 = spell(
    id=203144, name='Blood Nova Eruption', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, power_type=PowerType.MANA, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=8.0,
               potency_excluded='percent of max health'),
    ],
    spell_icon_id=2957,
    notes=(
        'S1a Blood (7,2) U10 / U12: Shadow, DmgClass MAGIC (DefenseType 1), 8 yd TARGET_UNIT_SRC_AREA_ENEMY around the '
        'caster, no target cap. Value 0 in data: the cast script passes BASE_POINT0 = BLOOD_NOVA_DAMAGE_PCT % of maximum '
        'health (potency_excluded: percent of max health). Zero spell_bonus_data row (no attack power, no spell power), '
        'crits (Runic Focus reads d2 b13: 200%), percent damage mods apply. d2 b13 BLOOD_OTHER_MAGIC (R1). '
        'SpellLevel 45. No visual of its own (the cast carries 15283).'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellClassMask_3': m.BLOOD_OTHER_MAGIC, 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'SpellLevel': 45, 'DefenseType': 1, 'PreventionType': 1,
        'Description_Lang_enUS': 'Your blood erupts, dealing Shadow damage equal to 20% of your maximum health to all '
                                 'enemies within 8 yards.',
    },
)
bonus_coefficients(blood_nova_eruption_203144, direct=0.0, dot=0.0, ap=0.0, ap_dot=0.0,
                   comment='Death Knight - Blood Nova Eruption: percent of max health, no attack power or spell power')

# =====================================================================================================================
# Purgatory (row 9, 1 rank): marker passive, Shroud of Purgatory (heal absorb), Purgatory Lockout (4 min debuff)
# =====================================================================================================================

purgatory_203145 = spell(
    id=203145, name='Purgatory', school=School.SHADOW, attributes=_TALENT_PASSIVE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=4148,
    notes=(
        'S1a Blood (9,2) U9: hidden passive marker (the talent aura, P0 203687 shape); DeathKnightUnitScript::DealDamage '
        'reads HasAura(203145) through DeathKnight::TryPurgatory. SpellLevel 55 = 9 + 5 x 9 + 1 (D3). No family bits, no '
        'script, no proc row.'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 55,
        'ProcChance': 101,
        'Description_Lang_enUS': 'Damage that would kill you is prevented. Instead, you gain Shroud of Purgatory, which '
                                 'absorbs incoming healing equal to the damage prevented, for 3 sec. If the Shroud has '
                                 'not been healed through when it expires, you die. This effect cannot occur more than '
                                 'once every 4 min.',
    },
)

# P0 203688 shape (passed): eff0 heal absorb (aura 301, all schools), amount = the prevented damage passed live by
# CastCustomSpell BASE_POINT0; eff1 aura 88 stored -101 = live -100% so natural regeneration (ModifyHealth, which never
# meets the heal absorb) cannot climb off 1 HP. NO_AURA_CANCEL so a right-click cannot dodge the expiry kill.
shroud_of_purgatory_203146 = spell(
    id=203146, name='Shroud of Purgatory', school=School.SHADOW, attributes=_ATTR0_NO_AURA_CANCEL | _ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_SCHOOL_HEAL_ABSORB, misc_value=_MISC_ALL_SCHOOLS,
               implicit_target_a=_TARGET_UNIT_CASTER,
               potency_excluded='amount is the damage Purgatory prevented, passed live by CastCustomSpell '
                                '(SPELLVALUE_BASE_POINT0)'),
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_HEALTH_REGEN_PERCENT, base_points=-101,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=3513,
    notes=(
        'S1a Blood (9,2) U9, P0 203688 shape: visible 3 s self aura (not passive), Attributes NO_AURA_CANCEL | '
        'NO_IMMUNITIES (an immune DK still gets it), SpellVisual '
        '14539 (Harvest Soul). eff0 SCHOOL_HEAL_ABSORB (301) misc 127 all schools, amount = min(damage - (health - 1), max '
        'health) passed live; eff1 MOD_HEALTH_REGEN_PERCENT (88) stored -101 = live -100%. spell_dk_shroud_of_purgatory '
        'kills on EXPIRE with an unfilled amount (DeathKnight::OnShroudExpired). Duration 3 s (index 27). SpellLevel 55.'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 55,
        'SpellVisualID_1': _SV_HARVEST_SOUL,
        'Description_Lang_enUS': 'Incoming healing fills the Shroud. If it is not filled when it expires, you die.',
        'AuraDescription_Lang_enUS': 'Incoming healing fills the Shroud. If it is not filled when it expires, you die.',
    },
)
scripted_by(shroud_of_purgatory_203146, 'spell_dk_shroud_of_purgatory')

# P0 203689 shape plus NO_IMMUNITIES (P0 review m3): a lockout the DK is immune-blocked from receiving (Divine Shield,
# Ice Block) would let Purgatory re-trigger on every lethal hit; ALLOW_AURA_WHILE_DEAD so dying never resets it.
purgatory_lockout_203147 = spell(
    id=203147, name='Purgatory Lockout', school=School.SHADOW,
    attributes=_ATTR0_AURA_IS_DEBUFF | _ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=240000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=2109,
    notes=(
        'S1a Blood (9,2) U9, P0 203689 shape: visible 4 min self debuff (not passive; AURA_IS_DEBUFF), AttributesEx3 '
        'ALLOW_AURA_WHILE_DEAD (dying does not reset the lockout) and Attributes NO_IMMUNITIES (P0 m3: an immunity cannot '
        'refuse it, so the TryPurgatory loop guard HasAura(203147) always holds). Duration 4 min (index 26).'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 55,
        'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD,
        'Description_Lang_enUS': 'Purgatory cannot protect you again yet.',
        'AuraDescription_Lang_enUS': 'Purgatory cannot protect you again yet.',
    },
)

# =====================================================================================================================
# Bonestorm (row 10, 1 rank): castable aura, 40-potency Shadow tick, health heal
# =====================================================================================================================

# The tick: cast by the aura's PERIODIC_TRIGGER_SPELL each second on the DK, 8 yd around it, no cap. AP potency 40 direct
# (T 1500 default), Shadow, magic class, d2 b13 (R1), SUPPRESS_CASTER_PROCS (the tick rolls no procs; the script grants
# Bloody Vengeance / Unending Thirst itself on a crit, U11).
bonestorm_tick_203149 = spell(
    id=203149, name='Bonestorm Tick', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, power_type=PowerType.MANA, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=40.0, potency_kind='direct', time_basis_ms=1000,
               implicit_target_a=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=8.0),
    ],
    spell_icon_id=2782,
    notes=(
        'S1a Blood (10,1) U11 / U12: the Bonestorm tick. Shadow, DmgClass MAGIC (DefenseType 1), SCHOOL_DAMAGE ap_potency '
        '40 direct (time basis defaults to 1500), 8 yd TARGET_UNIT_SRC_AREA_ENEMY, no target cap. d2 b13 BLOOD_OTHER_MAGIC '
        '(R1; Runic Focus reads it: 200% crits). AttributesEx3 SUPPRESS_CASTER_PROCS: rolls no procs; '
        'spell_dk_bonestorm_tick counts targets for the heal, grants the crit stacks and applies the U13 Blood Gorged '
        'snapshot correction. SpellLevel 60 = 9 + 5 x 10 + 1 (D3).'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellClassMask_3': m.BLOOD_OTHER_MAGIC, 'EquippedItemClass': -1,
        'CastingTimeIndex': 1, 'SpellLevel': 60, 'DefenseType': 1, 'PreventionType': 1,
        'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': 'Whirling bones deal {pot1} Shadow damage to all enemies within 8 yards.',
    },
)
scripted_by(bonestorm_tick_203149, 'spell_dk_bonestorm_tick')

# The cast and the visible aura are one spell: USE_ALL_MANA on a Runic Power row drains every point and GetPowerCost()
# is the amount spent (Red Thirst reads it); duration here is the 10 s cap, spell_dk_bonestorm shortens it to 1 s per
# 10 RP. PERIODIC_TRIGGER_SPELL 1000 ms is hasted only through SPELL_ATTR5_SPELL_HASTE_AFFECTS_PERIODIC (0-verify item 7).
bonestorm_203148 = spell(
    id=203148, name='Bonestorm', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=60000,
    category_cooldown_ms=0, power_type=PowerType.RUNIC_POWER, mana_cost=100, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000,
               trigger_spell=bonestorm_tick_203149.id, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=2782,
    notes=(
        'S1a Blood (10,1) U11: instant, GCD 133 / 1500 (magic class, core-hasted), 60 s Cooldown Haste (core), self range. '
        'AttributesEx USE_ALL_MANA (0x2) on PowerType RUNIC_POWER: the cost is every Runic Power point, so '
        'Spell::GetPowerCost() feeds Red Thirst; ManaCost 100 (= 10 RP, stored x10) is ignored by the server '
        '(SpellInfo::CalcPowerCost returns all power first) and only makes the client grey the button below 10 RP / show a '
        'cost line [playtest row: client display]. The 10 RP minimum and the one-active rule are spell_dk_bonestorm '
        'CheckCast. Effect 1 APPLY_AURA PERIODIC_TRIGGER_SPELL amplitude 1000 ms -> 203149 with AttributesEx5 '
        'HASTE_AFFECTS_PERIODIC (haste adds ticks), duration 10 s cap (index 1; the script sets 1 s per 10 RP). Visible '
        'aura (not passive), SpellVisual 7428 (Marrowgar Bone Storm 69076). DefenseType 1 / PreventionType 1. SpellLevel 60. '
        'SLA 30744 / talent 60340 are deathknight_talents.py\'s (granted_by_talent).'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 60,
        'DefenseType': 1, 'PreventionType': 1, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
        'AttributesEx': _ATTR1_USE_ALL_MANA, 'AttributesEx5': _ATTR5_SPELL_HASTE_AFFECTS_PERIODIC,
        'SpellVisualID_1': _SV_BONE_STORM,
        'Description_Lang_enUS': 'Consumes all Runic Power to create a whirl of bone around you for 1 sec per 10 Runic '
                                 'Power spent, up to 10 sec. Every sec, the storm deals '
                                 + pot_text(bonestorm_tick_203149)
                                 + ' Shadow damage to all enemies within 8 yards and heals you for 1% of your maximum '
                                   'health for each enemy it hits, up to 5 enemies.',
        'AuraDescription_Lang_enUS': 'Whirling bones damage nearby enemies and heal you.',
    },
)
scripted_by(bonestorm_203148, 'spell_dk_bonestorm')

# Cast by spell_dk_bonestorm_tick AfterCast: BASE_POINT0 = min(5, targets) x 1% of current max health (the current max
# health reads live each tick, so Vampiric Blood pressed mid-storm raises the rest). A percent-of-max-health heal gets
# Versatility (U23: DefenseType 1 plus the all-zero bonus row, the 45470 shape).
bonestorm_heal_203150 = _self_heal(
    203150, 'Bonestorm Heal', 60, 2782,
    'Heals you for a share of your maximum health for each enemy the storm hits.',
    ('percent of max health: the amount is min(5, targets) x BONESTORM_HEAL_PCT of the current maximum health, passed by '
     'CastCustomSpell, not CalcValue',
     'S1a Blood (10,1) U11 / U23: the Bonestorm heal. HEAL on the caster, value 0 in data (script BASE_POINT0). '
     'DefenseType 1 plus an all-zero spell_bonus_data row so Versatility and healing-done percent apply and spell power '
     'stays out. d2 b15 DK_SELF_HEAL (counts for the Voracious capstone). Its overheal never becomes Blood Shield (that '
     'is 45470 only).'),
    magic_class=True,
)

# =====================================================================================================================
# Blood Shield (Improved Death Strike capstone): visible all-school absorb
# =====================================================================================================================

blood_shield_203151 = spell(
    id=203151, name='Blood Shield', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=_MISC_ALL_SCHOOLS,
               implicit_target_a=_TARGET_UNIT_CASTER,
               potency_excluded='amount is the Death Strike overheal (capped at BLOOD_SHIELD_CAP_PCT of current max '
                                'health), set by DeathKnight::GrantBloodShield; it takes no further bonuses'),
    ],
    spell_icon_id=693,
    notes=(
        'S1a Blood (7,0) U7: visible 10 s self absorb (not passive, no consolidation flag), all schools (misc 127), '
        'SpellVisual 784 (Power Word: Shield). Amount set by DeathKnight::GrantBloodShield (adds to the existing aura up to '
        'BLOOD_SHIELD_CAP_PCT of current max HP, refreshes the 10 s); DmgClass NONE and no bonus row: no bonus applies when '
        'it is created. Also binds spell_dk_ams_damage_record so its absorbs feed the Death Strike damage record. No '
        'family bits. SpellLevel 0 (no potency).'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'SpellVisualID_1': _SV_POWER_WORD_SHIELD,
        'Description_Lang_enUS': 'Healing from your Death Strike that exceeds your maximum health becomes a Blood Shield, '
                                 'absorbing damage of any school.',
        'AuraDescription_Lang_enUS': 'Absorbs damage of any school.',
    },
)
scripted_by(blood_shield_203151, 'spell_dk_ams_damage_record')

# =====================================================================================================================
# Subversion capstone: +5 Runic Power on a crit from the four strikes
# =====================================================================================================================

subversion_runic_power_203152 = spell(
    id=203152, name='Subversion Runic Power', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[
        Effect(type=EffectType.ENERGIZE, base_points=49, implicit_target_a=_TARGET_UNIT_CASTER,
               misc_value=_MISC_POWER_RUNIC_POWER),
    ],
    spell_icon_id=3009,
    notes=(
        'S1a Blood (0,1) Subversion rank 3 capstone: PROC_TRIGGER_SPELL target of 49491 (E2). ENERGIZE Runic Power (misc 6) '
        'stored 49 = live 50 = 5 RP (RP x10). The once-per-cast guard is spell_dk_subversion_capstone (U25). SpellLevel 12 = '
        '9 + 5 x 0 + 3. No family bits, no cost.'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 12,
        'Description_Lang_enUS': 'Generates 5 Runic Power.',
    },
)

# =====================================================================================================================
# Vendetta strike heal: hidden proc passive 203153 (linked to the three Vendetta ranks) -> heal 203154
# =====================================================================================================================

vendetta_strike_203153 = spell(
    id=203153, name='Vendetta Strike', school=School.SHADOW, attributes=_HIDDEN_PASSIVE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=3008,
    notes=(
        'S1a Blood (3,3) Vendetta strike heal: hidden passive added and removed with each Vendetta rank (spell_linked_spell '
        'type 2 rows below: 49015 / 50154 / 55136). One DUMMY effect; spell_proc: family 15, mask Heart Strike d0 + '
        'Marrowrend d2, DONE spell melee damage class, type DAMAGE, phase HIT (2), chance 100. spell_dk_vendetta_strike '
        'checks the actor (the DK, never a Dancing Rune Weapon copy), reads the rank by which Vendetta aura is present '
        '(consts VENDETTA_STRIKE_HEAL_PCT_RANK1/2/3) and casts 203154 per target hit. Not affected by Proc Chance.'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'ProcChance': 100,
        'SpellLevel': 0,
        'Description_Lang_enUS': 'Your Heart Strike and Marrowrend heal you for a share of the damage they deal.',
    },
)
procs_on(vendetta_strike_203153, proc_flags=_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, family_name=_SPELLFAMILY_DEATHKNIGHT,
         family_mask=(m.HEART_STRIKE, 0, m.MARROWREND), spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, chance=100)
scripted_by(vendetta_strike_203153, 'spell_dk_vendetta_strike')

# Percent of the damage the strike dealt to one target: a leech-style heal (DmgClass NONE, no bonus row, U23).
vendetta_strike_heal_203154 = _self_heal(
    203154, 'Vendetta Strike Heal', 0, 3008,
    'Heals you for a share of the damage your strike dealt.',
    ('percent of damage dealt: the amount is the rank percent of the strike\'s damage, passed by CastCustomSpell',
     'S1a Blood (3,3): the Vendetta strike heal, cast per target hit by spell_dk_vendetta_strike. HEAL on the caster, value '
     '0 in data (script BASE_POINT0). DefenseType 0 and no bonus row (U23: the damage already carried Versatility). d2 b15 '
     'DK_SELF_HEAL (counts for the capstone, "stacks with Voracious\'s own leech"). SUPPRESS_CASTER_PROCS.'),
    suppress_procs=True,
)

# =====================================================================================================================
# Blood Gorged capstone: hidden 1 s poll on rank 3
# =====================================================================================================================

blood_gorged_mastery_203155 = spell(
    id=203155, name='Blood Gorged Mastery', school=School.NORMAL, attributes=_HIDDEN_PASSIVE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=24,
    notes=(
        'S1a Blood (9,1) U18: hidden passive 1 s PERIODIC_DUMMY (never hasted: no ATTR5 haste bit), added and removed with '
        'the Blood Gorged rank 3 damage passive 50109 (61156 is a LEARN_SPELL rank, never an aura) by the type 2 '
        'link row below. spell_dk_blood_gorged_mastery ticks '
        'DeathKnight::RefreshBloodGorged: it sets the rank 3 damage passive 50109\'s amount to 9 + Mastery x '
        'BLOOD_GORGED_MASTERY_SHARE_PCT % (SetAmount, or ChangeAmount while aura state 23 is on).'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'Description_Lang_enUS': 'Your Mastery increases the damage bonus of Blood Gorged.',
    },
)
scripted_by(blood_gorged_mastery_203155, 'spell_dk_blood_gorged_mastery')

# =====================================================================================================================
# Dancing Rune Weapon: the visible +20% parry buff
# =====================================================================================================================

dancing_rune_weapon_parry_203156 = spell(
    id=203156, name='Dancing Rune Weapon Parry', school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_PARRY_PERCENT, base_points=19,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=2873,
    notes=(
        'S1a Blood (6,1) U15: the visible 12 s parry buff of Dancing Rune Weapon (not passive, no consolidation flag), '
        'MOD_PARRY_PERCENT (47) stored 19 = live +20%, cast by the type 0 link row below when 49028 is cast. Spell '
        'Deflection (49145) reads parry, so this buff counts. Duration 12 s (index 29).'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'Description_Lang_enUS': 'Parry chance increased.',
        'AuraDescription_Lang_enUS': 'Parry chance increased.',
    },
)

# =====================================================================================================================
# Link rows and the stock-script unbind (the Vendetta / Blood Gorged / Dancing Rune Weapon rank rows are A2's / A4's)
# =====================================================================================================================

# Vendetta ranks add the strike-heal passive in lockstep with their own aura (type 2: aura).
linked_spell(49015, vendetta_strike_203153.id, 2, comment='Vendetta rank 1 - strike heal passive (S1a)')
linked_spell(50154, vendetta_strike_203153.id, 2, comment='Vendetta rank 2 - strike heal passive (S1a)')
linked_spell(55136, vendetta_strike_203153.id, 2, comment='Vendetta rank 3 - strike heal passive (S1a)')
# Dancing Rune Weapon: the parry buff is applied when it is cast (type 0: cast).
linked_spell(49028, dancing_rune_weapon_parry_203156.id, 0, comment='Dancing Rune Weapon - parry buff (S1a)')
# Blood Gorged rank 3's applied damage passive adds the Mastery poll.
# Keyed on the rank 3 damage passive 50109, not the LEARN_SPELL rank spell 61156 (61154-61156 are never applied as auras).
linked_spell(50109, blood_gorged_mastery_203155.id, 2, comment='Blood Gorged rank 3 damage passive - Mastery poll (S1a)')

# D2 (0-verify item 8): Vendetta rank 2 is bound twice (the -49015 chain row covers all three ranks, an explicit 50154 row
# binds rank 2 again), so a rank 2 kill healed twice. Drop the explicit duplicate; the chain row still binds all three.
unbind_script(50154, 'spell_dk_vendetta')
