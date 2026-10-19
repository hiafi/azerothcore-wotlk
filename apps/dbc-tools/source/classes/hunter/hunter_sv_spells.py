"""
Hunter - Survival S3 spells 202040-202072 (hunter-rework SURVIVAL.md 2.1 / 2.4 / 5 / 7.3): the four castables (Mantis
Strike, Wildfire Bomb, Tar Bomb, Cluster Bombs), their helpers (Tarred, Tar, Burning Tar, the Cluster Bombs follow-up,
Shrapnel, the two Explosive Shot splashes, the Improved Glaive Toss slow, the Explosive Trap ground fire, the Point of
No Escape marker, the Wyvern sleep, Survivalist's two helpers, the T.N.T. Mastery passive) and the ten Favored Prey
buffs, plus the SV const() block (TOOLTIP-RECONCILE X10, SURVIVAL 9.2), the SV tooltip_vars entries (7.3), the S3a
spell_proc rows (8.1), the S3a script bindings / unbinds (9.3 as amended by S3a-HANDOFF A1-A20 and the S3a WP brief),
the Favored Prey spell_group 1242 and the Survivalist / T.N.T. aura links.

Skeleton written by S3a WP-0 0-dsl (variable stems and Names frozen for HunterData.h), completed by S3a WP-A1. Every
row: EquippedItemClass -1 (none is a player-cast ranged shot that needs a weapon: Mantis Strike is an AP instant like
Raptor Strike, N5), SpellClassSet 9, the family bit only where SURVIVAL 2.4 gives one, SpellLevel = the talent row's
learn level (10 + 5N) or SURVIVAL 5's value. CastingTimeIndex 1 on the four castables (stale line 14, the Commands'
precedent), 0 on the triggered helpers (the MM helper precedent; S3b C-3 moved them to 1 as well, custom-spells.md), 1
on the two hidden passives (the rank-passive
precedent). AttributesEx2 IGNORE_LINE_OF_SIGHT (0x4) exactly on 202048, 202049, 202050, 202053, 202056, 202057, 202059
(stale line 12). Aura texts as SURVIVAL 5 writes them; user ruling 5 (X7) keeps only Burning Tar 202050 number-free
here (orchestrator ruling, S3a).

Imports: this file imports only `_masks`. hunter_spells.py / hunter_trigger_spells.py / hunter_sv_ranks.py import the
consts and tooltip_vars below, so every stock or rank spell is named here by BARE ID (the rank passives of
hunter_sv_ranks.py import this file; a variable reference would be a cycle; the MM file's precedent). NEVER import
hunter_spells.py, hunter_trigger_spells.py or hunter_sv_ranks.py from here.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    const, linked_spell, pot_text, procs_on, product, scripted_by, spell, spell_group, spell_group_rule, talent_mult,
    tooltip_vars, unbind_script,
)

from . import _masks as m

# ---- constants (SURVIVAL 9.2 file constants + TOOLTIP-RECONCILE X10; the C++ header names are the strings).
# An integer const() that C++ divides by 100 is written `/ 100.0f` there (B2). ----
SHRAPNEL_RADIUS_YD = const(
    'SHRAPNEL_RADIUS_YD', 8.0, 'Shrapnel: distance from the primary within which it picks a victim, yards (SV 5.7).',
)
CLUSTER_BOMBS_FOLLOWUP_COUNT = const(
    'CLUSTER_BOMBS_FOLLOWUP_COUNT', 4, 'Cluster Bombs: follow-up blasts after the cast (SV 5.8).', cpp_type='uint8',
)
# The four offsets {500, 600, 700, 800} are evenly spaced: offset i = FIRST + i * (LAST - FIRST) / (COUNT - 1).
CLUSTER_BOMBS_FOLLOWUP_MS = const(
    'CLUSTER_BOMBS_FOLLOWUP_MS', 500, 'Cluster Bombs: first follow-up offset after the cast, ms (SV 5.8).',
    cpp_type='uint32',
)
CLUSTER_BOMBS_FOLLOWUP_LAST_MS = const(
    'CLUSTER_BOMBS_FOLLOWUP_LAST_MS', 800, 'Cluster Bombs: last follow-up offset after the cast, ms (SV 5.8).',
    cpp_type='uint32',
)
CLUSTER_BOMBS_SCATTER_YD = const(
    'CLUSTER_BOMBS_SCATTER_YD', 3.0, 'Cluster Bombs: follow-up scatter distance from the centre, yards (SV 5.8).',
)
IGT_SLOW_MIN_DISTANCE_YD = const(
    'IGT_SLOW_MIN_DISTANCE_YD', 10.0, 'Improved Glaive Toss capstone: slow only beyond this distance, yards (SV 6).',
)
SNAKE_STING_REFRESH_MS = const(
    'SNAKE_STING_REFRESH_MS', 3000, "Snake Trap snakes re-cast Serpent Sting at or below this time left, ms (SV 0.13).",
    cpp_type='uint32',
)
THRILL_MM_CUT_FACTOR = const(
    'THRILL_MM_CUT_FACTOR', 2, 'Thrill of the Hunt: cooldown cut multiplier for Aimed Shot, Multi-Shot, Chimera Shot '
    '(SV 0.8).', cpp_type='uint32',
)
THRILL_MANA_REFUND_PCT = const(
    'THRILL_MANA_REFUND_PCT', 40, "Thrill of the Hunt: mana refunded, percent of the cost (the stock script's literal; "
    'text only, SV 6.1).', cpp_type='int32',
)


def _n(c):
    """A const()'s value as tooltip text (whole numbers without a decimal point)."""
    value = c['value']
    return str(int(value)) if float(value).is_integer() else str(value)


# ---- tooltip_vars (SURVIVAL 7.3; Q31: always-on in-tree % talents of SV only; names <= 12 chars). The rank ids are
# bare ints (hunter_sv_ranks.py imports this file). hunter_spells.py attaches 1153 to Mongoose Bite 1495 (`{pot1*df}`),
# hunter_shared_spells.py attaches 1154 to Glaive Toss 201600 (`{pot1*igt}`). ----
sv_strike_1153 = tooltip_vars(
    1153, "Survival strikes: Deadly Focus, Improved Mantis Strike",
    df=talent_mult([202080, 202081], effect=1),
    ims=talent_mult([202100, 202101, 202102], effect=1),
    mantis=product('df', 'ims'),
)   # Mongoose Bite 1495: {pot1*df}; Mantis Strike 202040: {pot1*mantis}; Raptor Strike: none
sv_glaive_1154 = tooltip_vars(
    1154, "Glaive Toss: Improved Glaive Toss",
    igt=talent_mult([202088, 202089, 202090], effect=1),
)
# SURVIVAL 7.3 sketches ONE entry (1180). Rendered it is 1116 chars, over the 1024 limit (lib/dsl/tooltip.py
# MAX_ENTRY_LENGTH), so the Explosive Trap's variables (vp, tmdot, etblast, etfire; the only users are 13813's text)
# move to the spare entry 1181 and repeat tnt / tntdot there (WP brief resolution 9). 1180 = 774 chars, 1181 = 629.
sv_explosive_1180 = tooltip_vars(
    1180, "Survival explosives: T.N.T., Demolitions, Dark Hunting",
    tnt=talent_mult([56333, 56336, 56337], effect=1),
    tntdot=talent_mult([56333, 56336, 56337], effect=2),
    demo=talent_mult([202095, 202096, 202097], effect=1),
    demodot=talent_mult([202095, 202096, 202097], effect=2),
    dh=talent_mult([202107, 202108], effect=1),
    tntdemo=product('tnt', 'demo'), wbdot=product('tntdot', 'demodot'), btar=product('tntdot', 'dh'),
)
sv_trap_1181 = tooltip_vars(
    1181, "Survival Explosive Trap: T.N.T., Volatile Payload, Trap Mastery",
    tnt=talent_mult([56333, 56336, 56337], effect=1),
    tntdot=talent_mult([56333, 56336, 56337], effect=2),
    vp=talent_mult([202103, 202104, 202105], effect=1),
    tmdot=talent_mult([19376, 63457, 63458], effect=2),
    etblast=product('tnt', 'vp'), etfire=product('tntdot', 'tmdot'),
)
# The names the S3a handoff A15 / the SURVIVAL 7.3 sketch call them.
sv_strike_tooltip = sv_strike_1153
sv_glaive_tooltip = sv_glaive_1154
sv_explosive_tooltip = sv_explosive_1180
sv_trap_tooltip = sv_trap_1181

# ---- helpers ----
_MASK_KEYS = {1: 'A', 2: 'B', 3: 'C'}
_FAMILY = {'SpellClassSet': 9}
_HIDDEN = 464                       # 0x1D0: passive, DO_NOT_DISPLAY (0x80), the rank-passive set
_DO_NOT_DISPLAY = 0x80              # Attributes: hidden aura, not passive
_CASTABLE = 0x50000                 # SURVIVAL 5 common rules: castables' Attributes (no USES_RANGED_SLOT)
_SUPPRESS_CASTER_PROCS = 0x10000    # AttributesEx3: proc-free payloads
_IGNORE_CASTER_MODIFIERS = 0x20000000   # AttributesEx3
_CANT_CRIT = 0x20000000             # AttributesEx2
# AttributesEx2 SPELL_ATTR2_IGNORE_LINE_OF_SIGHT (SharedDefines.h): removes CheckCast's hunter -> target / dest LoS and
# CheckEffectTarget's per-target LoS (S2b-FIX side effect). S3-HANDOFF stale line 12 lists exactly seven SV helpers.
_IGNORE_LINE_OF_SIGHT = 0x4
_RANGE_UNLIMITED = 50000.0          # every triggered helper that targets another unit
_CAST_INSTANT = 1                   # SpellCastTimes row 1: stock instants (the DSL's 0 has no client row)
_TARGETS_DEST_LOCATION = 0x40       # raw Targets: ground cursor / dest-only cast (13813, Convergence 201932)


def _mask_overrides(masks):
    """`masks` maps a 1-based effect index to its (d0, d1, d2) EffectSpellClassMask triple (letter = effect)."""
    overrides = {}
    for effect_index, triple in (masks or {}).items():
        for dword, value in enumerate(triple, start=1):
            if value:
                overrides[f'EffectSpellClassMask{_MASK_KEYS[effect_index]}_{dword}'] = value
    return overrides


def _aura(aura, base_points=0, misc_value=0, target=1, **kwargs):
    """One APPLY_AURA effect (target 1 = self, 6 = the target)."""
    return Effect(
        type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=target, apply_aura=aura,
        misc_value=int(misc_value), **kwargs,
    )


def _castable(spell_id, name, school, icon, level, effects, notes, bit=None, cooldown_ms=0, mana_pct=0,
              range_yards=35.0, duration_ms=None, raw=None, **kwargs):
    """A talent-taught instant castable: Attributes 0x50000, CastingTimeIndex 1, GCD 1500 / category 133, RANGED, unit
    facing, pacify prevention, EquippedItemClass -1 (SURVIVAL 5 common rules, A4). `bit` is its one (dword, value)
    family bit. A ground-targeted castable passes raw FacingCasterFlags 0."""
    overrides = {
        'EquippedItemClass': -1, 'SpellLevel': level, 'DefenseType': 3, 'SpellClassSet': 9,
        'CastingTimeIndex': _CAST_INSTANT, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
        'FacingCasterFlags': 1, 'PreventionType': 2,
    }
    if bit is not None:
        overrides[f'SpellClassMask_{bit[0]}'] = bit[1]
    overrides.update(raw or {})
    return spell(
        id=spell_id, name=name, school=school, attributes=_CASTABLE, cast_time_ms=0, cooldown_ms=cooldown_ms,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=mana_pct, range_yards=range_yards, duration_ms=duration_ms,
        effects=effects, spell_icon_id=icon, notes=notes, raw_overrides=overrides, **kwargs,
    )


def _helper(spell_id, name, school, icon, level, effects, notes, duration_ms=None, range_yards=_RANGE_UNLIMITED,
            attributes=0, raw=None, **kwargs):
    """A triggered helper or buff: no cast time, no cost, family 9 with no bit unless `raw` adds one."""
    # CastingTimeIndex 1 (S3b C-3): the DSL's 0 has no SpellCastTimes row; no helper uses the ranged slot (0 / 18 are
    # for USES_RANGED_SLOT instants, custom-spells.md), so 1 is the right instant everywhere here.
    overrides = {'EquippedItemClass': -1, 'SpellLevel': level, 'CastingTimeIndex': _CAST_INSTANT, **_FAMILY}
    overrides.update(raw or {})
    return spell(
        id=spell_id, name=name, school=school, attributes=attributes, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=range_yards, duration_ms=duration_ms,
        effects=effects, spell_icon_id=icon, notes=notes, raw_overrides=overrides, **kwargs,
    )


# ---- 5.1 Mantis Strike 202040 + its enable 202041 (talent (4,0), learn 30; replaces Counterattack 19306) ----
mantis_strike_202040 = _castable(
    202040, 'Mantis Strike', School.NORMAL, 278, 30,
    [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=128.0, potency_kind='direct', implicit_target_a=6),
     _aura(AuraType.MOD_ROOT, 0, 0, target=6, mechanic=Mechanic.ROOT)],
    'S3a A1 / SV 5.1 + A4: Mantis Strike. Physical RANGED instant AP strike (no weapon, N5): eff0 SCHOOL_DAMAGE 160 AP '
    'potency (T 1.5), eff1 MOD_ROOT with mechanic ROOT on the effect, 2 s root, 3% base mana (placeholder, M), no '
    'cooldown, 5 yd (RangeIndex 12, no melee flag; Deadly Focus +10), CasterAuraSpell 202041 (the enable, consumed by '
    'spell_hun_mantis_strike AfterCast), CasterAuraState 0, d1 b19 (MANTIS_STRIKE), CastingTimeIndex 1, '
    'tooltip_vars 1153. Icon 278 (Counterattack, placeholder V3).',
    bit=(2, m.MANTIS_STRIKE), mana_pct=3, range_yards=5.0, duration_ms=2000, tooltip_vars=sv_strike_1153,
    raw={'RangeIndex': 12, 'CasterAuraSpell': 202041, 'CasterAuraState': 0,
         'Description_Lang_enUS': 'A swift strike that deals {pot1*mantis} Physical damage and immobilizes the target '
                                  'for $d. Usable only while Killer Instinct allows it.',
         'AuraDescription_Lang_enUS': 'Immobile.'},
)
mantis_strike_enable_202041 = _helper(
    202041, 'Mantis Strike', School.NORMAL, 278, 30, [_aura(AuraType.DUMMY, 0)],
    'S3a A1 / SV 5.1: the visible Mantis Strike enable buff (M1), DUMMY on self, 6 s, CasterAuraSpell of 202040, no '
    'bit; triggered by Killer Instinct r3 19373 (CAST row below), a new grant refreshes it.',
    duration_ms=6000, range_yards=RANGE_SELF,
    raw={'Description_Lang_enUS': 'Allows the use of Mantis Strike for $d.',
         'AuraDescription_Lang_enUS': 'Mantis Strike is usable.'},
)

# ---- 5.2 Mongoose Fury 202042, Predator's Guard 202043, Scavenger 202044 (triggered only, no bits) ----
mongoose_fury_202042 = _helper(
    202042, 'Mongoose Fury', School.NORMAL, 86, 15,
    [_aura(AuraType.ADD_PCT_MODIFIER, 99, SpellModOp.DAMAGE)],
    'S3a A1 / SV 5.2: Mongoose Fury (Relentless r3 202087, row (1,0) learn 15). +100% next Mongoose Bite (stored 99), '
    'A mask d0 Mongoose Bite, 1 charge, 10 s, visible (M1), ProcTypeMask 0 and no spell_proc row (the charge is spent '
    'by Player::RemoveSpellMods, paladin 201424 precedent).',
    duration_ms=10000, range_yards=RANGE_SELF,
    raw={**_mask_overrides({1: (m.MONGOOSE_BITE, 0, 0)}), 'ProcCharges': 1, 'ProcTypeMask': 0,
         'Description_Lang_enUS': 'Your next Mongoose Bite deals $s1% more damage.',
         'AuraDescription_Lang_enUS': 'Your next Mongoose Bite deals $s1% more damage.'},
)
predators_guard_buff_202043 = _helper(
    202043, "Predator's Guard", School.NORMAL, 558, 25,
    [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -7, 127),
     _aura(AuraType.ADD_PCT_MODIFIER, 19, SpellModOp.DAMAGE)],
    "S3a A1 / SV 5.2: Predator's Guard buff (Predator's Guard r3 202094, row (3,0) learn 25). eff0 -6% damage taken "
    '(stored -7, misc 127), eff1 +20% Raptor Strike / Mongoose Bite / Mantis Strike (stored 19, B mask THREE_STRIKES), '
    '8 s, visible (M1).',
    duration_ms=8000, range_yards=RANGE_SELF,
    raw={**_mask_overrides({2: m.THREE_STRIKES}), 'ProcTypeMask': 0,
         'Description_Lang_enUS': 'Damage taken reduced by $s1%. Raptor Strike, Mongoose Bite and Mantis Strike '
                                  'damage increased by $s2%.',
         'AuraDescription_Lang_enUS': 'Damage taken reduced by $s1%. Raptor Strike, Mongoose Bite and Mantis Strike '
                                      'damage increased by $s2%.'},
)
scavenger_energize_202044 = _helper(
    202044, 'Scavenger', School.NORMAL, 2240, 35,
    [Effect(type=EffectType.ENERGIZE_PCT, base_points=2, implicit_target_a=1, misc_value=0)],
    'S3a A1 / SV 5.2: Scavenger (Resourcefulness r3 34493, row (5,2) learn 35). ENERGIZE_PCT (137) misc 0 (mana) 3% of '
    'maximum mana (stored 2), instant, self, no aura.',
    range_yards=RANGE_SELF,
    raw={'Description_Lang_enUS': 'Restores $s1% of your maximum mana.'},
)

# ---- 5.3 Wildfire Bomb 202045 (talent (2,1), learn 20; impact + burn in one spell, d1 b6) ----
wildfire_bomb_202045 = _castable(
    202045, 'Wildfire Bomb', School.FIRE, 2505, 20,
    [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=84.0, potency_kind='direct', implicit_target_a=53,
            implicit_target_b=16, radius_yards=8.0),
     Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000, ap_potency=16.0,
            potency_kind='periodic', implicit_target_a=53, implicit_target_b=16, radius_yards=8.0)],
    'S3a A1 / SV 5.3 + A4: Wildfire Bomb. Fire instant, unit-targeted, 15 yd, 18 s cooldown (< 30 s: no Cooldown '
    'Haste), category 0, 6% base mana (placeholder, M), eff0 impact 120 AP potency (T 1.5), eff1 burn 23 AP potency '
    'per 1 s tick for 6 s (snapshots at impact), both A 53 / B 16 8 yd. Dispel Magic. d1 b6 (WILDFIRE_BOMB), '
    'CastingTimeIndex 1, tooltip_vars 1180. The impact is a direct Fire hit (Burning Tar), the burn never is.',
    bit=(2, m.WILDFIRE_BOMB), cooldown_ms=18000, mana_pct=6, range_yards=15.0, duration_ms=6000,
    dispel=DispelType.MAGIC, tooltip_vars=sv_explosive_1180,
    raw={'Description_Lang_enUS': 'Hurl a bomb at an enemy. It explodes for {pot1*tntdemo} Fire damage to the target '
                                  'and all enemies within $a1 yards, and burns them for {pot2.total*wbdot} Fire '
                                  'damage over $d.',
         'AuraDescription_Lang_enUS': 'Burning for Fire damage every $t2 sec.'},
)

# ---- 5.4 Tarred 202048, Tar 202049, Burning Tar 202050, Tar Bomb 202047 (talent (8,1), learn 50) ----
tarred_202048 = _helper(
    202048, 'Tarred', School.NORMAL, 2565, 50, [_aura(AuraType.DUMMY, 0, 0, target=6)],
    'S3a A1 / SV 5.4 + A3: Tarred, DUMMY debuff on the target 12 s, no mechanic, Dispel 0, no bit, visible (M1), '
    'IGNORE_LINE_OF_SIGHT (stale line 12: the parent area selection already filtered from the impact point). Carries '
    "the Burning Tar proc: raw ProcTypeMask 0x20200, ProcChance 100; S3b ships its spell_proc row and "
    "spell_hun_tarred. Interim (A19): the engine's default proc entry procs a scriptless DUMMY, a no-op.",
    duration_ms=12000,
    raw={'ProcTypeMask': 0x20200, 'ProcChance': 100, 'AttributesEx2': _IGNORE_LINE_OF_SIGHT,
         'Description_Lang_enUS': 'Coats the target in tar for $d.',
         'AuraDescription_Lang_enUS': 'Coated in tar. Direct Fire damage from the hunter adds Burning Tar.'},
)
tar_slow_202049 = _helper(
    202049, 'Tar', School.NATURE, 2565, 50, [_aura(AuraType.MOD_DECREASE_SPEED, -51, 0, target=6,
                                                  mechanic=Mechanic.SNARE)],
    'S3a A1 / SV 5.4 + A3: Tar, -50% movement speed (stored -51), snare mechanic on the EFFECT only (spell Mechanic 0, '
    'so a snare-immune target still gets Tarred), 12 s, Dispel Magic, visible (M1), IGNORE_LINE_OF_SIGHT (stale line '
    '12).',
    duration_ms=12000, dispel=DispelType.MAGIC,
    raw={'AttributesEx2': _IGNORE_LINE_OF_SIGHT,
         'Description_Lang_enUS': 'Reduces movement speed by $s1% for $d.',
         'AuraDescription_Lang_enUS': 'Movement speed reduced by $s1%.'},
)
burning_tar_202050 = _helper(
    202050, 'Burning Tar', School.FIRE, 1939, 50,
    [_aura(AuraType.PERIODIC_DAMAGE, 0, 0, target=6, amplitude=1000, ap_potency=16.8, potency_kind='periodic',
           time_basis_ms=1500)],
    'S3a A1 / SV 5.10 + A3: Burning Tar, the bank DoT. Fire PERIODIC_DAMAGE 1 s ticks (hasted), 6 s, eff0 24 AP '
    'potency as the chunk SOURCE (time basis 1500: a payout priced as an instant; the S3b script reads CalcValue), '
    'RANGED, Dispel 0, StackAmount 255 (CumulativeAura, display), d1 b27 (BURNING_TAR), IGNORE_LINE_OF_SIGHT (stale '
    'line 12), not IGNORE_CASTER_MODIFIERS, not SUPPRESS_CASTER_PROCS (ticks raise DONE_PERIODIC for Lock and Load). '
    'Inert in S3a (only S3b code casts it).',
    duration_ms=6000,
    raw={'SpellClassMask_2': m.BURNING_TAR, 'DefenseType': 3, 'CumulativeAura': 255,
         'AttributesEx2': _IGNORE_LINE_OF_SIGHT,
         'Description_Lang_enUS': 'Burns the target with the damage your Fire hits add while it is Tarred.',
         'AuraDescription_Lang_enUS': 'Burning for Fire damage every $t1 sec.'},
)
tar_bomb_202047 = _castable(
    202047, 'Tar Bomb', School.NATURE, 2565, 50,
    [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=30.0, potency_kind='direct', implicit_target_a=53,
            implicit_target_b=16, radius_yards=8.0),
     Effect(type=EffectType.TRIGGER_SPELL, trigger_spell=202048, implicit_target_a=53, implicit_target_b=16,
            radius_yards=8.0),
     Effect(type=EffectType.TRIGGER_SPELL, trigger_spell=202049, implicit_target_a=53, implicit_target_b=16,
            radius_yards=8.0)],
    'S3a A1 / SV 5.4 + A4: Tar Bomb. Nature instant, unit-targeted, impact 30 AP potency (T 1.5), A 53 / B 16 8 yd, '
    '15 yd, 30 s on its own RecoveryTime (category 0: Cooldown Haste eligible, Dark Hunting -5 s first), 6% base mana '
    '(placeholder, M); eff1 / eff2 TRIGGER_SPELL Tarred 202048 and Tar 202049 on every hit target (LAUNCH_TARGET, '
    '0-verify finding 10). d1 b26 (TAR_BOMB), CastingTimeIndex 1, tooltip_vars 1180.',
    bit=(2, m.TAR_BOMB), cooldown_ms=30000, mana_pct=6, range_yards=15.0, tooltip_vars=sv_explosive_1180,
    raw={'Description_Lang_enUS':
         'Throw a bomb of tar at an enemy, dealing {pot1*tnt} Nature damage to it and all enemies within $a1 yards '
         'and coating them in tar for $202048d. Tarred enemies are slowed by $202049s1%. Each time your direct Fire '
         'damage hits a Tarred enemy, it gains a stack of Burning Tar, adding '
         + pot_text(burning_tar_202050, var='btar') + ' Fire damage to Burning Tar and resetting it to $202050d.'},
)

# ---- 5.8 Cluster Bombs 202051 / 202052 (talent (10,1), learn 60; d2 b5 on both) ----
cluster_bombs_blast_202052 = _helper(
    202052, 'Cluster Bombs', School.FIRE, 2499, 60,
    [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=76.5, potency_kind='direct', implicit_target_a=87,
            implicit_target_b=16, radius_yards=5.0)],
    'S3a A1 / SV 5.8: a Cluster Bombs follow-up blast, Fire 90 AP potency (T 1.5) at TARGET_DEST_DEST (87) + '
    'TARGET_UNIT_DEST_AREA_ENEMY (16) 5 yd, cast at a scripted position by spell_hun_cluster_bombs (SpellCastTargets '
    'dst), RANGED, AttributesEx3 SUPPRESS_CASTER_PROCS (rolls nothing), d2 b5 (CLUSTER_BOMBS), no 0x4 (stale line 12: '
    'a scatter point the centre cannot see is replaced by the centre). Burning Tar via OnDirectFireHit (SV 0.23).',
    raw={'SpellClassMask_3': m.CLUSTER_BOMBS, 'DefenseType': 3, 'AttributesEx3': _SUPPRESS_CASTER_PROCS,
         'SpellVisualID_1': 90091,   # patch_hunter_vfx_models.py: stock dynamite explosion, one per blast
         'Description_Lang_enUS': 'Deals {pot1} Fire damage to all enemies within $a1 yards.'},
)
cluster_bombs_202051 = _castable(
    202051, 'Cluster Bombs', School.FIRE, 2499, 60,
    [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=72.0, potency_kind='direct', implicit_target_a=87,
            implicit_target_b=16, radius_yards=5.0),
     Effect(type=EffectType.DUMMY, implicit_target_a=87)],
    'S3a A1 / SV 5.8 + A4: Cluster Bombs. The cast is the first blast (eff0 Fire 90 AP potency, T 1.5, A 87 / B 16 5 '
    'yd at the destination; unsuppressed: rolls the once-per-cast procs, SV 0.16); eff1 DUMMY A 87 is the scheduler of '
    'the 4 follow-ups 202052 (spell_hun_cluster_bombs, OnEffectHit). Ground cursor (raw Targets 0x40, the trap shape), '
    'FacingCasterFlags 0 (not unit-targeted, A4), 30 yd, 50 s (Cooldown Haste eligible), 10% base mana (placeholder, '
    'M), d2 b5 (CLUSTER_BOMBS), CastingTimeIndex 1, tooltip_vars 1180.',
    bit=(3, m.CLUSTER_BOMBS), cooldown_ms=50000, mana_pct=10, range_yards=30.0, tooltip_vars=sv_explosive_1180,
    raw={'Targets': _TARGETS_DEST_LOCATION, 'FacingCasterFlags': 0,
         'SpellVisualID_1': 90091,   # patch_hunter_vfx_models.py: the first of the five explosions
         'Description_Lang_enUS':
         'Hurl a cluster of bombs at the target location. The first blast deals {pot1*tnt} Fire damage to all '
         'enemies within $a1 yards. Over the next second, ' + _n(CLUSTER_BOMBS_FOLLOWUP_COUNT)
         + ' more bombs explode near the center, each dealing '
         + pot_text(cluster_bombs_blast_202052, var='tnt') + ' Fire damage to all enemies within $202052a1 yards.'},
)

# ---- 5.7 / 5.6 Shrapnel 202053 and the two Explosive Shot splashes (no bits, proc-free) ----
shrapnel_hit_202053 = _helper(
    202053, 'Shrapnel', School.FIRE, 2147, 35,
    [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=34.0, potency_kind='direct', implicit_target_a=6)],
    'S3a A1 / SV 5.7: Shrapnel. Fire 40 AP potency (T 1.5) at one enemy picked by Hunter::TryShrapnel, RANGED, '
    'AttributesEx3 SUPPRESS_CASTER_PROCS, IGNORE_LINE_OF_SIGHT (stale line 12: the shrapnel flies from the primary; '
    'TryShrapnel filters candidates by the primary\'s LoS, N3), no bit (Mastery and Point of No Escape by '
    'spell_hun_shrapnel); Burning Tar via OnDirectFireHit.',
    raw={'DefenseType': 3, 'AttributesEx3': _SUPPRESS_CASTER_PROCS, 'AttributesEx2': _IGNORE_LINE_OF_SIGHT,
         'Description_Lang_enUS': 'Deals {pot1} Fire damage.'},
)
# WP brief resolution 2 (0-verify finding 2): the splashes are DEST spells, A 87 (TARGET_DEST_DEST) / B 16 + raw Targets
# 0x40, the Convergence 201932 precedent. At A 53 a killing blow on the primary fizzled them (CheckTarget TARGETS_DEAD).
# B1 casts them with SetDst(*primary) + SetUnitTarget(primary); the unit is stripped by InitExplicitTargets but kept as
# the original target, which spell_hun_explosive_shot_splash removes from the area list. 202054 eff1 is a plain DUMMY
# effect with NO implicit target (an APPLY_AURA at target 6 would make the explicit target mask UNIT_ENEMY again).
_SPLASH_NOTE = ('A 87 / B 16 8 yd + raw Targets 0x40 (WP brief resolution 2), BP0 from the script, '
                'EffectBonusMultiplier 0, IGNORE_CASTER_MODIFIERS | SUPPRESS_CASTER_PROCS, CANT_CRIT, RANGED, no 0x4 '
                '(stale line 12: native per-target LoS from the dest; the hunter -> dest check stays), no bit.')
explosive_shot_splash_202054 = _helper(
    202054, 'Explosive Shot', School.FIRE, 3407, 30,
    [Effect(type=EffectType.SCHOOL_DAMAGE, potency_excluded='40% share of the primary hit as dealt (script BP0)',
            implicit_target_a=87, implicit_target_b=16, radius_yards=8.0),
     Effect(type=EffectType.DUMMY, base_points=39)],
    'S3a A1 / SV 5.6: the hit splash, 40% of the dealt 53301 hit. ' + _SPLASH_NOTE + ' eff1 DUMMY bp 39 (live 40, no '
    'target) is the splash percent for both splashes (read through SpellInfo by B1; tooltip $202054s2). Its AfterHit '
    'calls OnDirectFireHit (SV 0.23).',
    raw={'DefenseType': 3, 'Targets': _TARGETS_DEST_LOCATION, 'AttributesEx2': _CANT_CRIT,
         'AttributesEx3': _IGNORE_CASTER_MODIFIERS | _SUPPRESS_CASTER_PROCS, 'EffectBonusMultiplier_1': 0.0},
)
explosive_shot_blast_splash_202055 = _helper(
    202055, 'Explosive Shot', School.FIRE, 3407, 30,
    [Effect(type=EffectType.SCHOOL_DAMAGE, potency_excluded='40% share of the primary blast as dealt (script BP0)',
            implicit_target_a=87, implicit_target_b=16, radius_yards=8.0)],
    'S3a A1 / SV 5.6: the blast splash, 40% (202054 eff1) of each dealt 53352 blast. ' + _SPLASH_NOTE
    + ' Never adds Burning Tar (on the OnDirectFireHit exclusion list).',
    raw={'DefenseType': 3, 'Targets': _TARGETS_DEST_LOCATION, 'AttributesEx2': _CANT_CRIT,
         'AttributesEx3': _IGNORE_CASTER_MODIFIERS | _SUPPRESS_CASTER_PROCS, 'EffectBonusMultiplier_1': 0.0},
)

# ---- 5.11 small helpers ----
glaive_toss_slow_202056 = _helper(
    202056, 'Improved Glaive Toss', School.NORMAL, 1650, 15,
    [_aura(AuraType.MOD_DECREASE_SPEED, -31, 0, target=6, mechanic=Mechanic.SNARE)],
    'S3a A1 / SV 5.11: the Improved Glaive Toss capstone slow (row (1,1) learn 15), -30% (stored -31), snare mechanic '
    'on the effect, 3 s, Dispel Magic, visible (M1), IGNORE_LINE_OF_SIGHT (stale line 12: the target was already hit). '
    'Cast by spell_hun_glaive_toss_sv beyond IGT_SLOW_MIN_DISTANCE_YD.',
    duration_ms=3000, dispel=DispelType.MAGIC,
    raw={'AttributesEx2': _IGNORE_LINE_OF_SIGHT,
         'Description_Lang_enUS': 'Reduces movement speed by $s1% for $d.',
         'AuraDescription_Lang_enUS': 'Movement speed reduced by $s1%.'},
)
explosive_trap_fire_202057 = _helper(
    202057, 'Explosive Trap', School.FIRE, 37, 34,
    [Effect(type=EffectType.SCHOOL_DAMAGE, potency_excluded='snapshot BP from spell_hun_explosive_trap_fire',
            implicit_target_a=6)],
    'S3a A1 / SV 5.9: the Explosive Trap ground-fire tick (C5 snapshot shape), BP0 = the placement snapshot, '
    'EffectBonusMultiplier 0, MAGIC defense type like 13812 (its load correction), IGNORE_CASTER_MODIFIERS | '
    'SUPPRESS_CASTER_PROCS, IGNORE_LINE_OF_SIGHT (stale line 12: the dynobj already put the unit in the fire), level '
    '34 (= 13813), no bit. Inert in S3a (S3b rewrites 13812 eff1 and binds spell_hun_explosive_trap_fire_tick).',
    raw={'DefenseType': 1, 'AttributesEx3': _IGNORE_CASTER_MODIFIERS | _SUPPRESS_CASTER_PROCS,
         'AttributesEx2': _IGNORE_LINE_OF_SIGHT, 'EffectBonusMultiplier_1': 0.0},
)
point_of_no_escape_marker_202058 = _helper(
    202058, 'Point of No Escape', School.NORMAL, 3520, 45,
    [_aura(AuraType.MOD_DAMAGE_FROM_CASTER, -1, 0, target=6)],
    'S3a A1 / SV 0.3 + 5.11: the hidden Point of No Escape marker debuff (row (7,2) learn 45). Aura 271 bp -1 (amount '
    'by S3b\'s spell_hun_point_of_no_escape), A mask PONE_ALL_EXCEPT_BURNING_TAR (no d1 b27, no d1 b28), 12 s '
    '(extended by script), Attributes 0x80 (hidden, M1), Dispel 0, no 0x4 (applied with AddAura, no CheckCast). Inert '
    'in S3a.',
    duration_ms=12000, attributes=_DO_NOT_DISPLAY,
    raw={**_mask_overrides({1: m.PONE_ALL_EXCEPT_BURNING_TAR})},
)
wyvern_sting_sleep_202059 = _helper(
    202059, 'Wyvern Sting', School.NATURE, 1721, 40,
    [_aura(AuraType.MOD_STUN, 0, 0, target=6, mechanic=Mechanic.SLEEP)],
    'S3a A1 / SV 0.12 + 5.11: the 30 s Wyvern Sting sleep after the rework (row (6,1) learn 40). MOD_STUN with '
    'mechanic SLEEP on the effect, Dispel Poison (a sting), broken by damage (AuraInterruptFlags 4718594 = stock '
    '19386\'s), d1 b12 and SpellIconID 1721 (the Wyvern DR / PvP key, approved d1 b12 reuse), DmgClass 0, visible '
    '(M1), IGNORE_LINE_OF_SIGHT (stale line 12: cast 2 s after the sting). Inert in S3a (S3b casts it).',
    duration_ms=30000, dispel=DispelType.POISON,
    raw={'SpellClassMask_2': m.WYVERN_STING, 'DefenseType': 0, 'AttributesEx2': _IGNORE_LINE_OF_SIGHT,
         'AuraInterruptFlags': 4718594,
         'Description_Lang_enUS': 'Puts the target to sleep for $d. Any damage other than Serpent Sting wakes the '
                                  'target.',
         'AuraDescription_Lang_enUS': 'Asleep.'},
)
survivalist_speed_202060 = _helper(
    202060, 'Survivalist', School.NORMAL, 164, 20, [_aura(AuraType.MOD_INCREASE_SPEED, 29, 0)],
    'S3a A1 / SV 5.11: the Survivalist capstone speed buff (row (2,3) learn 20), +30% (stored 29), 3 s (Deterrence '
    'sets its duration by script), visible (M1). Inert in S3a (S3b casts it).',
    duration_ms=3000, range_yards=RANGE_SELF,
    raw={'Description_Lang_enUS': 'Increases movement speed by $s1% for $d.',
         'AuraDescription_Lang_enUS': 'Movement speed increased by $s1%.'},
)
survivalist_deterrence_202061 = _helper(
    202061, 'Survivalist', School.NORMAL, 164, 20,
    [_aura(AuraType.ADD_FLAT_MODIFIER, 999, SpellModOp.DURATION)],
    'S3a A1 / SV 0.9 + 5.11: hidden passive (464, M1), Deterrence +1 s (flat DURATION, stored 999), A mask d1 '
    'DETERRENCE; aura-linked to all three Survivalist ranks (linked_spell type 2 below).',
    duration_ms=-1, attributes=_HIDDEN, range_yards=0.0,
    raw={**_mask_overrides({1: (0, m.DETERRENCE, 0)}), 'RangeIndex': 1, 'CastingTimeIndex': _CAST_INSTANT,
         'Description_Lang_enUS': 'Increases the duration of your Deterrence by ${$m1/1000} sec.'},
)
tnt_mastery_202062 = _helper(
    202062, 'T.N.T.', School.NORMAL, 355, 50,
    [_aura(AuraType.ADD_PCT_MODIFIER, -1, SpellModOp.DAMAGE),
     _aura(AuraType.ADD_PCT_MODIFIER, -1, SpellModOp.DOT),
     _aura(AuraType.PERIODIC_DUMMY, 0, 0, amplitude=1000)],
    'S3a A1 / SV 7.1 + A13: the T.N.T. Mastery hidden passive (464, M1; T.N.T. row (8,2) learn 50). eff0 pct DAMAGE on '
    'SV_TNT_DAMAGE, eff1 pct DOT on SV_MASTERY_DOT, both bp -1 (0, set to round(Mastery) by spell_hun_tnt_mastery '
    'DoEffectCalcAmount + the eff2 PERIODIC_DUMMY 1 s refresh). Aura-linked to T.N.T. r3 (56337).',
    duration_ms=-1, attributes=_HIDDEN, range_yards=0.0,
    raw={**_mask_overrides({1: m.SV_TNT_DAMAGE, 2: m.SV_MASTERY_DOT}), 'RangeIndex': 1,
         'CastingTimeIndex': _CAST_INSTANT,
         'Description_Lang_enUS': 'Your Mastery increases the damage of your explosives.'},
)

# ---- 5.11 Favored Prey 202063-202072: ten exclusive self buffs (spell_group 1242), one per creature type ----
_FAVORED_PREY = (
    # (id, variable stem, creature-type bit, plural for the text)
    (202063, 'beast', 0x1, 'Beasts'),
    (202064, 'dragonkin', 0x2, 'Dragonkin'),
    (202065, 'demon', 0x4, 'Demons'),
    (202066, 'elemental', 0x8, 'Elementals'),
    (202067, 'giant', 0x10, 'Giants'),
    (202068, 'undead', 0x20, 'Undead'),
    (202069, 'humanoid', 0x40, 'Humanoids'),
    (202070, 'critter', 0x80, 'Critters'),
    (202071, 'mechanical', 0x100, 'Mechanicals'),
    (202072, 'not_specified', 0x200, 'creatures of no type'),
)


def _favored_prey(spell_id, plural, type_bit):
    return _helper(
        spell_id, 'Favored Prey', School.NORMAL, 3522, 10,
        [_aura(AuraType.MOD_DAMAGE_DONE_VERSUS, 4, type_bit)],
        f'S3a A1 / SV 5.11: Favored Prey buff vs {plural} (row (0,3) learn 10). MOD_DAMAGE_DONE_VERSUS (168) misc '
        f'{type_bit:#x} (1 << (CreatureType - 1)), +5% (stored 4), 10 s, visible (M1), no bit. Member of the exclusive '
        'spell_group 1242: a new type replaces the old one, the same type refreshes.',
        duration_ms=10000, range_yards=RANGE_SELF,
        raw={'Description_Lang_enUS': f'Increases your damage against {plural} by $s1% for $d.',
             'AuraDescription_Lang_enUS': f'Damage against {plural} increased by $s1%.'},
    )


favored_prey_beast_202063 = _favored_prey(202063, 'Beasts', 0x1)
favored_prey_dragonkin_202064 = _favored_prey(202064, 'Dragonkin', 0x2)
favored_prey_demon_202065 = _favored_prey(202065, 'Demons', 0x4)
favored_prey_elemental_202066 = _favored_prey(202066, 'Elementals', 0x8)
favored_prey_giant_202067 = _favored_prey(202067, 'Giants', 0x10)
favored_prey_undead_202068 = _favored_prey(202068, 'Undead', 0x20)
favored_prey_humanoid_202069 = _favored_prey(202069, 'Humanoids', 0x40)
favored_prey_critter_202070 = _favored_prey(202070, 'Critters', 0x80)
favored_prey_mechanical_202071 = _favored_prey(202071, 'Mechanicals', 0x100)
favored_prey_not_specified_202072 = _favored_prey(202072, 'creatures of no type', 0x200)
_FAVORED_PREY_BUFFS = (
    favored_prey_beast_202063, favored_prey_dragonkin_202064, favored_prey_demon_202065, favored_prey_elemental_202066,
    favored_prey_giant_202067, favored_prey_undead_202068, favored_prey_humanoid_202069, favored_prey_critter_202070,
    favored_prey_mechanical_202071, favored_prey_not_specified_202072,
)
assert [s.id for s in _FAVORED_PREY_BUFFS] == [row[0] for row in _FAVORED_PREY]

# spell_group 1242 (SURVIVAL 2.3, ids.yaml spell_group block) + rule 1 = SPELL_GROUP_STACK_RULE_EXCLUSIVE.
spell_group(1242, *_FAVORED_PREY_BUFFS)
spell_group_rule(1242, stack_rule=1, description='Favored Prey (hunter Survival): one creature type at a time')

# ---- aura links (SURVIVAL 0.9, 7.1; S3a-HANDOFF A2). Type 2: the helper comes and goes with the rank's aura. ----
for _rank in (19255, 19256, 19257):                                         # Survivalist r1-r3 -> Deterrence +1 s
    linked_spell(_rank, survivalist_deterrence_202061.id, 2)
linked_spell(56337, tnt_mastery_202062.id, 2)                               # T.N.T. r3 -> the Mastery passive


# ---- spell_proc rows (SURVIVAL 8.1 with S3a-HANDOFF A2 / A9-A12; positive keys for new rows, stale line 8; the live
# keys -34500 / -19184 re-declared with their exact key). chance 0 = the rank's DBC ProcChance (A2 / A3 set it, Proc
# Chance applies on top). Phase CAST 0x1 / HIT 0x2 / FINISH 0x4; hit NORMAL 0x1 / CRIT 0x2; type DAMAGE 1.
# DONE_RANGED_AUTO 0x40, DONE_SPELL_RANGED 0x100, TRAP_ACTIVATION 0x200000. Not here: -53290 / -34497 (A4 edits them in
# place in hunter_shared_spells.py). The S3b rows (Tarred 202048, Lock and Load -56342 / 56453) are at the end of this
# block. ----
# Killer Instinct r3: Mongoose Bite / Explosive Shot / Glaive Toss cast -> eff1 202041 (eff0 crit aura never procs).
procs_on(19373, proc_flags=0x100, family_name=9, family_mask=m.KILLER_INSTINCT_PROC, spell_phase_mask=0x1,
         disable_effects_mask=0x1)
# Relentless r3: Raptor Strike / Mantis Strike cast -> eff1 Mongoose Fury 202042.
procs_on(202087, proc_flags=0x100, family_name=9, family_mask=m.RELENTLESS_PROC, spell_phase_mask=0x1,
         disable_effects_mask=0x1)
# Predator's Guard r3: Mongoose Bite / Mantis Strike damage hit -> eff1 202043.
procs_on(202094, proc_flags=0x100, family_name=9, family_mask=m.STRIKE_HITS, spell_type_mask=1, spell_phase_mask=0x2,
         hit_mask=0x3, disable_effects_mask=0x1)
# Resourcefulness r3: Mongoose Bite / Mantis Strike damage hit -> eff2 Scavenger 202044 (eff0 / eff1 SpellMods).
procs_on(34493, proc_flags=0x100, family_name=9, family_mask=m.STRIKE_HITS, spell_type_mask=1, spell_phase_mask=0x2,
         hit_mask=0x3, disable_effects_mask=0x3)
# Demolitions r3: the Explosive Shot hit's crit (only 53301 carries d1 b31: once per cast) -> the script's eff2.
procs_on(202097, proc_flags=0x100, family_name=9, family_mask=(0, m.EXPLOSIVE_SHOT, 0), spell_type_mask=1,
         spell_phase_mask=0x2, hit_mask=0x2, disable_effects_mask=0x3)
# Volatile Payload r3: Wildfire Bomb cast -> spell_hun_volatile_payload eff1 (eff0 SpellMod).
procs_on(202105, proc_flags=0x100, family_name=9, family_mask=(0, m.WILDFIRE_BOMB, 0), spell_phase_mask=0x1,
         disable_effects_mask=0x1)
# Favored Prey r3: once-per-cast ranged damage cast or Auto Shot hit (spell_hun_favored_prey DoCheckProc, SV 7.2).
procs_on(202084, proc_flags=0x140, family_name=9, spell_phase_mask=0x3, disable_effects_mask=0x1)
# Expose Weakness (live key -34500, re-declared in place; was family 0 / HIT): crits of the once-per-cast gate
# (spell_hun_sv_ranged_cast_proc) -> eff0 aura 231 passes the rank's BP0 into 34501.
procs_on(-34500, proc_flags=0x140, family_name=9, spell_type_mask=1, spell_phase_mask=0x3, hit_mask=0x2)
# Master Tactician r1-r3 (new, positive keys; there is no live -34506 row): the once-per-cast gate -> 34837.
for _rank in (34506, 34507, 34508):
    procs_on(_rank, proc_flags=0x140, family_name=9, spell_type_mask=1, spell_phase_mask=0x3, hit_mask=0x3)
# Entrapment (live key -19184, re-declared in place; V-m2): ProcFlags TRAP_ACTIVATION on the row (r1/r2 carry DBC
# ProcTypeMask 0 after A3), Frost Trap / Snake Trap, FINISH, triggered casts proc (the trap trigger casts the effect);
# eff0 (the SpellMod) never procs, so only 19388's eff1 (-> 64804) fires.
procs_on(-19184, proc_flags=0x200000, family_name=9, family_mask=(m.FROST_TRAP_AURA, m.SNAKE_TRAP_EFFECT, 0),
         spell_phase_mask=0x4, attributes_mask=0x2, disable_effects_mask=0x1)
# ---- S3b rows (SURVIVAL 8.1; S3b-HANDOFF B1 / B4) ----
# Tarred (B1): TAKEN_SPELL_MAGIC_NEG | TAKEN_SPELL_RANGED (0x20200), Fire, damage type, phase 0 (a phase on TAKEN-only
# flags would log "SpellPhaseMask value defined, but it won't be used", V-m1), TRIGGERED_CAN_PROC (trap blasts and
# triggered Fire hits count). spell_hun_tarred does the actor / damage / DOT checks; chance 100.
procs_on(202048, proc_flags=0x20200, family_name=0, school_mask=4, spell_type_mask=1, spell_phase_mask=0, hit_mask=0,
         attributes_mask=0x2, chance=100.0)
# Lock and Load (B4), trap / periodic trigger (live key -56342, re-declared exact: was ICD 22000 and no HIT | FINISH
# phase set). proc_flags 0 = the DBC ProcTypeMask 0x240000; LOCK_AND_LOAD_PROC is the live row's mask (Freezing / Frost
# Trap, Burning Tar, Explosive / Immolation Trap effects). chance 0 -> the DBC ProcChance 100, which Proc Chance lifts
# to
# >= 100: the row cannot fail, spell_hun_lock_and_load_rework rolls RollProcChance(eff) itself (V-m17: do not "fix").
# Cooldown 0: the 5 s marker 67544 is the ICD. disable_effects_mask 0x4 (eff2 never procs: Chain Reaction's DUMMY on
# r3).
procs_on(-56342, proc_flags=0, family_name=9, family_mask=m.LOCK_AND_LOAD_PROC, spell_phase_mask=0x2 | 0x4,
         attributes_mask=0x2, disable_effects_mask=0x4, chance=0.0, cooldown_ms=0)
# Lock and Load buff 56453 (B4, X22): the charge is spent by the next NON-triggered Arcane Shot / Explosive Shot cast
# (CAST phase, no TRIGGERED_CAN_PROC, so MM's free triggered Arcane Shot 201933 never eats it).
procs_on(56453, proc_flags=0x100, family_name=9, family_mask=(m.ARCANE_SHOT, m.EXPLOSIVE_SHOT, 0), spell_phase_mask=0x1,
         chance=100.0)


# ---- script bindings and unbinds (SURVIVAL 9.3 as amended by the S3a WP brief's script table; positive keys only,
# stale line 8; unbinds use the exact live keys, 0-verify 2a: -53301 and -53290 each hold one live row). Stock and rank
# spells by bare id (no import of hunter_spells / hunter_trigger_spells / hunter_sv_ranks; the MM precedent). S3b's
# classes (tarred, burning_tar, lock_and_load_rework, explosive_trap_fire*, point_of_no_escape, frost_trap_aura_sv,
# freezing_trap_sv, wyvern rework, deterrence / disengage / feign death sv) bind in the S3b block at the end. ----
scripted_by(mantis_strike_202040, 'spell_hun_mantis_strike')
unbind_script(-53301, 'spell_hun_explosive_shot')                           # exact live key (stock TakeAmmo, moot)
scripted_by(53301, 'spell_hun_explosive_shot_rework')                       # Explosive Shot (Spell + Aura pair)
scripted_by(53352, 'spell_hun_explosive_shot_blast')                        # Explosive Shot blast
scripted_by(explosive_shot_splash_202054, 'spell_hun_explosive_shot_splash')
scripted_by(explosive_shot_blast_splash_202055, 'spell_hun_explosive_shot_splash')
scripted_by(shrapnel_hit_202053, 'spell_hun_shrapnel')
scripted_by(cluster_bombs_202051, 'spell_hun_cluster_bombs')
scripted_by(cluster_bombs_blast_202052, 'spell_hun_cluster_bombs_blast')    # V1: OnDirectFireHit
scripted_by(202097, 'spell_hun_demolitions')                                # Demolitions r3
scripted_by(202105, 'spell_hun_volatile_payload')                           # Volatile Payload r3
scripted_by(202084, 'spell_hun_favored_prey')                               # Favored Prey r3
for _rank in (34500, 34502, 34503, 34506, 34507, 34508):   # Expose Weakness r1-r3, Master Tactician r1-r3
    scripted_by(_rank, 'spell_hun_sv_ranged_cast_proc')
unbind_script(-53290, 'spell_hun_hunting_party')                            # exact live key
for _rank in (53290, 53291, 53292):                                         # Hunting Party r1-r3
    scripted_by(_rank, 'spell_hun_hunting_party_rework')
for _rank in (34497, 34498):                                # Thrill of the Hunt r1-r2 (stock -34497 stays bound)
    scripted_by(_rank, 'spell_hun_thrill_of_the_hunt_sv')
scripted_by(tnt_mastery_202062, 'spell_hun_tnt_mastery')
scripted_by(201600, 'spell_hun_glaive_toss_sv')                             # Glaive Toss (additive to SHARED's)

# ---- S3b bindings (S3b WP brief class table; positive keys, bare ids for stock / trigger-file spells). The exact
# unbind
# keys -56342 and -19386 each hold one live row (S3b-HANDOFF B4 / B7). Hook indices follow the BUILT rows (L3). ----
scripted_by(tarred_202048, 'spell_hun_tarred')                              # DUMMY eff0: proc + PoNE apply / remove
scripted_by(burning_tar_202050, 'spell_hun_burning_tar')                    # PERIODIC_DAMAGE eff0: bank tick
scripted_by(point_of_no_escape_marker_202058, 'spell_hun_point_of_no_escape')   # aura 271 eff0
scripted_by(13810, 'spell_hun_frost_trap_aura_sv')                          # Frost Trap aura, eff0 aura 33 (bare id)
unbind_script(-56342, 'spell_hun_lock_and_load')                            # exact live key (stock script)
for _rank in (56342, 56343, 56344):                                         # Lock and Load r1-r3
    scripted_by(_rank, 'spell_hun_lock_and_load_rework')
scripted_by(13812, 'spell_hun_explosive_trap_fire')                         # Explosive Trap effect, eff1 PERIODIC_DUMMY
scripted_by(explosive_trap_fire_202057, 'spell_hun_explosive_trap_fire_tick')
scripted_by(3355, 'spell_hun_freezing_trap_sv')                             # Freezing Trap Effect, eff0 MOD_STUN
unbind_script(-19386, 'spell_hun_wyvern_sting')                             # exact live key (stock script)
scripted_by(19386, 'spell_hun_wyvern_sting_rework')                         # Wyvern Sting, eff0 MOD_DAMAGE_PERCENT_DONE
scripted_by(19263, 'spell_hun_deterrence_sv')                               # Deterrence, eff0 MOD_DODGE_PERCENT
scripted_by(781, 'spell_hun_disengage_sv')                                  # Disengage (additive to stock's)
scripted_by(5384, 'spell_hun_feign_death_sv')                               # Feign Death
