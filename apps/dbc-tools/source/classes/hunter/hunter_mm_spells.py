"""
Hunter - Marksmanship S2 spells 201920-201952 (hunter-rework MARKSMANSHIP.md 2.1 / 4 / 5): the three marks, the mark
DoTs, Convergence, the free Arcane Shot, the charged and payoff buffs, the Sniper crit helpers and the Mastery passive,
plus the MM const() block (TOOLTIP-RECONCILE X10, MARKSMANSHIP 4.8), the MM tooltip_vars entries (5.12), the S2a
spell_proc rows (8), the S2a script bindings / unbinds (10.2 as amended by S2a-HANDOFF A1-A21) and spellcategory 1301.

Skeleton written by S2a WP-0 0-dsl (variable stems and Names frozen for HunterData.h), completed by S2a WP-A1. Not in
S2a: 201934-201937, 201950, 201952 (S2b declares them). EquippedItemClass -1 on every row except the three player-cast
marks (2, M4).

Imports: this file imports only `_masks` (orchestrator ruling, S2a): hunter_spells.py / hunter_trigger_spells.py /
hunter_mm_ranks.py import the consts and tooltip_vars below, so every stock or rank spell is named here by bare id.
"""

from lib.dsl import AuraType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    const, custom_attr, linked_spell, pot_text, procs_on, product, scripted_by, spell, spell_category, talent_mult,
    tooltip_vars, unbind_script,
)

from . import _masks as m

# ---- constants (MARKSMANSHIP.md 4.8 / TOOLTIP-RECONCILE X10; the C++ header names are the strings) ----
MARK_MAX_STACKS = const('MARK_MAX_STACKS', 10, 'Mark stack cap (MM 4.2).', cpp_type='uint8')
MARK_GAIN = const('MARK_GAIN', 1, 'Mark stacks gained per ability against the target (MM 4.3).', cpp_type='uint8')
MARK_FAVORED_GAIN = const(
    'MARK_FAVORED_GAIN', 3, 'Mark stacks gained per favored ability, total (cast 1 + favored 2; MM 0.4, R2-13).',
    cpp_type='uint8',
)
KEEN_EYE_GAIN = const(
    'KEEN_EYE_GAIN', 2, 'Keen Eye extra stacks on each mark on the target (MM 5.10).', cpp_type='uint8',
)
SNIPER_CRIT_CHANCE = const(
    'SNIPER_CRIT_CHANCE', 20, "Sniper's Mark: Aimed Shot crit chance, flat points (MM 4.6).", cpp_type='int32',
)
SNIPER_CRIT_DAMAGE_PER_STACK = const(
    'SNIPER_CRIT_DAMAGE_PER_STACK', 10, "Sniper's Mark: Aimed Shot crit damage bonus per stack, percent (MM 4.6).",
    cpp_type='int32',
)
CHIMERA_SNIPER_CRIT_CHANCE = const(
    'CHIMERA_SNIPER_CRIT_CHANCE', 100, "Sniper's Mark: Chimera Shot crit chance, flat points (MM 5.6).",
    cpp_type='int32',
)
CHIMERA_SNIPER_CRIT_DAMAGE = const(
    'CHIMERA_SNIPER_CRIT_DAMAGE', 100, "Sniper's Mark: Chimera Shot crit damage bonus, percent (MM 5.6).",
    cpp_type='int32',
)
MARK_FALCON_HASTE_PER_STACK = const(
    'MARK_FALCON_HASTE_PER_STACK', 2, "Falcon's Haste per Falcon's Mark stack, percent (MM 4.5).", cpp_type='int32',
)
QUICKENING_MS_PER_STACK = const(
    'QUICKENING_MS_PER_STACK', 1000, "Quickening duration per consumed Falcon's Mark stack, ms (MM 5.9).",
    cpp_type='uint32',
)
PACK_RADIUS_YD = const('PACK_RADIUS_YD', 8.0, 'Trick Shots ricochet / Rain of Arrows bounce radius, yards (MM 5.2).')
PACK_MAX_TARGETS = const(
    'PACK_MAX_TARGETS', 4, 'Trick Shots ricochet / Rain of Arrows bounce target cap (MM 5.2).', cpp_type='uint8',
)
MULTI_SHOT_TARGET_CAP = const(
    'MULTI_SHOT_TARGET_CAP', 5, 'Multi-Shot target cap, primary included (MM 5.3).', cpp_type='uint8',
)
DEADEYE_CDR_MS = const(
    'DEADEYE_CDR_MS', 2000, 'Deadeye capstone: mark cooldown cut per Aimed Shot crit, ms (MM 5.2).', cpp_type='uint32',
)
FOCUSED_AIM_CDR_MS = const(
    'FOCUSED_AIM_CDR_MS', 1000, 'Focused Aim capstone: Aimed Shot cooldown cut per Steady Shot crit, ms (MM 5.11).',
    cpp_type='uint32',
)
RAPID_KILLING_HEALTH_PCT = const(
    'RAPID_KILLING_HEALTH_PCT', 35.0, 'Rapid Killing execute threshold, target health percent (MM 6 row (2,3)).',
)
RAIN_OF_ARROWS_FIRE_PCT = const(
    'RAIN_OF_ARROWS_FIRE_PCT', 10, 'Rain of Arrows capstone: Fire! chance per Volley tick, percent (MM 5.4).',
    cpp_type='int32',
)
CHIMERA_SERPENT_BURST_PCT = const(
    'CHIMERA_SERPENT_BURST_PCT', 40, "Chimera Shot: Serpent Sting burst, percent of the sting's total damage (MM 5.6).",
    cpp_type='int32',
)
# S2a A1: Convergence's two script numbers (MM 5.10). The DSL allows one direct AP coefficient per spell (D6), so
# both 201932 effects carry the centre's potency and spell_hun_convergence (S2b) scales EFFECT_1 by this percent
# (the Swipe 201726 precedent); the splash keeps the nearest CONVERGENCE_MAX_TARGETS in-combat enemies.
CONVERGENCE_SPLASH_PCT = const(
    'CONVERGENCE_SPLASH_PCT', 50, 'Convergence splash share of the centre hit, percent (MM 5.10).', cpp_type='int32',
)
CONVERGENCE_MAX_TARGETS = const(
    'CONVERGENCE_MAX_TARGETS', 5, 'Convergence splash target cap, the centre excluded (MM 5.10).', cpp_type='uint8',
)


def _n(c):
    """A const()'s value as tooltip text (whole numbers without a decimal point)."""
    value = c['value']
    return str(int(value)) if float(value).is_integer() else str(value)


def _favored_extra():
    """The extra stacks a favored ability adds on top of a normal one (MARK_FAVORED_GAIN is the total, MM 0.4)."""
    return str(int(MARK_FAVORED_GAIN['value']) - int(MARK_GAIN['value']))


def _sec(c):
    """A millisecond const() as whole seconds of tooltip text."""
    return str(int(c['value']) // 1000)


# ---- tooltip_vars (MARKSMANSHIP 5.12; rank spell ids are bare because the pulled / stock / hunter_mm_ranks.py ranks
# resolve by id). 1150 is BM's entry (hunter_bm_spells.py); S2a appends ps / rws to it there (A4). ----
mm_arcane_shot_1151 = tooltip_vars(
    1151, "Talents on Arcane Shot",
    rws=talent_mult([19507, 19508, 19509], effect=1),
    aa=talent_mult([201832, 201833, 201834], effect=1),
    fi=talent_mult([34455, 34459, 34460], effect=3),
    mult=product('rws', 'aa', 'fi'),
)
mm_serpent_sting_1152 = tooltip_vars(
    1152, "Talents on Serpent Sting",
    stings=talent_mult([19464, 19465, 19466], effect=1),
    ss=talent_mult([34466, 34467, 34468], effect=2),
    sting=product('stings', 'ss'),
)
mm_mark_dots_1170 = tooltip_vars(
    1170, "MM talents on mark DoTs",
    mfd=talent_mult([53241, 53243, 53244], effect=2),
    stings=talent_mult([19464, 19465, 19466], effect=1),
    mult=product('mfd', 'stings'),
)
mm_convergence_1171 = tooltip_vars(
    1171, "MM talents on Convergence",
    mfd=talent_mult([53241, 53243, 53244], effect=1),
)
mm_volley_1172 = tooltip_vars(
    1172, "MM talents on Volley",
    barrage=talent_mult([19461, 19462, 24691], effect=1),
    roa=talent_mult([201979, 201980], effect=1),
    mult=product('barrage', 'roa'),
)

# Aimed Shot's own cooldown category (Q17): 19434 leaves Multi-Shot's 85 (A4 sets category=1301 on 19434).
spell_category(1301, comment="Aimed Shot (split from 85)")

# ---- helpers ----

_MASK_KEYS = {1: 'A', 2: 'B', 3: 'C'}
_FAMILY = {'SpellClassSet': 9}
_HIDDEN = 464                       # 0x1D0: passive, DO_NOT_DISPLAY (0x80), the rank-passive set
_SUPPRESS_CASTER_PROCS = 0x10000    # AttributesEx3: proc-free payloads (MM 5 common rules)
_DO_NOT_RESET_COMBAT_TIMERS = 0x20000   # AttributesEx2: stock shot flag (Arcane / Aimed / Chimera Shot)
# SpellCastTimes row 18 (-1000000 ms): the +500 ranged-slot add still clamps to 0 (M2).
_USES_RANGED_SLOT_INSTANT = 18


def _mask_overrides(masks):
    """`masks` maps a 1-based effect index to its (d0, d1, d2) EffectSpellClassMask triple (letter = effect)."""
    overrides = {}
    for effect_index, triple in (masks or {}).items():
        for dword, value in enumerate(triple, start=1):
            if value:
                overrides[f'EffectSpellClassMask{_MASK_KEYS[effect_index]}_{dword}'] = value
    return overrides


def _self_aura(aura, base_points=0, misc_value=0, **kwargs):
    """One self-targeted APPLY_AURA effect (target 1)."""
    return Effect(
        type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=1, apply_aura=aura,
        misc_value=int(misc_value), **kwargs,
    )


# ---- the three marks (MARKSMANSHIP 4.1 + S2-HANDOFF stale line 2, S2a A1). Player-cast shots: EquippedItemClass 2
# (M4), raw CastingTimeIndex 18 (instant with USES_RANGED_SLOT, M2), d2 b27 (MARK_PRESS). eff2 DUMMY is the mark
# (amount 0: CalculateAmount multiplies by the stack). Stacks live in HunterMechanics (spell_hun_mark). ----
_MARK_TAIL = ' Reapplying the mark resets its stacks.'


def _mark(spell_id, name, school, icon, level, cooldown_ms, visual, description, aura_text, tooltip=None):
    return spell(
        id=spell_id,
        name=name,
        school=school,
        attributes=65538,           # 0x10002: USES_RANGED_SLOT | 0x10000, Arcane Shot's / Aimed Shot's shot attributes
        cast_time_ms=0,
        cooldown_ms=cooldown_ms,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=4,            # placeholder, M
        range_yards=35.0,
        duration_ms=15000,
        effects=[
            Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6),
            Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=110, implicit_target_a=6),
            Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.DUMMY),
        ],
        spell_icon_id=icon,
        tooltip_vars=tooltip,
        notes=f'S2a A1 / MM 4.1: {name}. Instant shot (CastingTimeIndex 18), 110 weapon potency, eff2 DUMMY = the mark '
              f'(0-10 stacks, spell_hun_mark), 15 s, {cooldown_ms // 1000} s, 4% base mana, 35 yd, Speed 40, d2 b27, '
              f'GCD 1500/133, EquippedItemClass 2 (player-cast shot, M4). Visual {visual} reused from a stock shot.',
        raw_overrides={
            'EquippedItemClass': 2, 'EquippedItemSubclass': 262156, 'SpellLevel': level,
            'SpellClassSet': 9, 'SpellClassMask_3': m.MARK_PRESS, 'DefenseType': 3,
            'CastingTimeIndex': _USES_RANGED_SLOT_INSTANT, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
            'RangeIndex': 114,          # SPELL_RANGE_RANGED (35 yd, too-close check), like 3044 / 19434
            'Speed': 40.0, 'FacingCasterFlags': 1, 'PreventionType': 2, 'CumulativeAura': int(MARK_MAX_STACKS['value']),
            'ModalNextSpell': 75, 'AttributesEx2': _DO_NOT_RESET_COMBAT_TIMERS, 'SpellVisualID_1': visual,
            'Description_Lang_enUS': description + _MARK_TAIL,
            'AuraDescription_Lang_enUS': aura_text,
        },
    )


# Viper's Bite / Viper's Venom are declared before Viper's Mark: its tooltip quotes them through pot_text().
# ---- mark DoTs (MARKSMANSHIP 5.6): Nature, RANGED, d2 b28 (MARK_DOT), proc-free, triggered at another unit ----
def _mark_dot(spell_id, name, duration_ms, icon, level, potency, description, raw=None):
    overrides = {
        'EquippedItemClass': -1, 'SpellLevel': level, 'DefenseType': 3,
        'SpellClassSet': 9, 'SpellClassMask_3': m.MARK_DOT, 'AttributesEx3': _SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': description,
        'AuraDescription_Lang_enUS': 'Taking Nature damage every $t1 sec.',
    }
    overrides.update(raw or {})
    return spell(
        id=spell_id,
        name=name,
        school=School.NATURE,
        dispel=0,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=50000.0,
        duration_ms=duration_ms,
        effects=[
            Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000,
                   ap_potency=potency, potency_kind='periodic', time_basis_ms=3000, implicit_target_a=6),
        ],
        spell_icon_id=icon,
        tooltip_vars=mm_mark_dots_1170,
        notes=f'S2a A1 / MM 5.6: {name}. Nature PERIODIC_DAMAGE every 3 s, ap_potency {potency:g} per 3 s tick '
              f'(placeholder, M), {duration_ms // 1000} s, d2 b28, SUPPRESS_CASTER_PROCS, 50000 yd (triggered at the '
              f'target), snapshots at application. tooltip_vars 1170.',
        raw_overrides=overrides,
    )


vipers_bite_201930 = _mark_dot(
    201930, "Viper's Bite", 12000, 1630, 40, 4.0,
    'Deals {pot1*mult} Nature damage every $t1 sec for $d per stack.',
    # stack = Viper's stacks consumed (SPELLVALUE_AURA_STACK; old Bite removed first)
    raw={'CumulativeAura': int(MARK_MAX_STACKS['value'])},
)
vipers_venom_201931 = _mark_dot(
    201931, "Viper's Venom", 6000, 3521, 60, 23.0,
    'Deals {pot1*mult} Nature damage every $t1 sec for $d.',
)


snipers_mark_201920 = _mark(
    201920, "Sniper's Mark", School.NORMAL, 3524, 30, 30000, 7955,
    'A precise shot that deals $s2% weapon damage and places Sniper\'s Mark on the target for $d. Each of your '
    'abilities against the target adds a stack, up to $u; Arcane Shot, Chimera Shot and Kill Shot add '
    + _favored_extra() + ' more. Your Aimed Shot consumes the mark, gaining ' + _n(SNIPER_CRIT_CHANCE)
    + '% critical strike chance and '
    + _n(SNIPER_CRIT_DAMAGE_PER_STACK) + '% critical strike damage per stack. Your Chimera Shot against the target is '
    'a guaranteed critical strike with ' + _n(CHIMERA_SNIPER_CRIT_DAMAGE) + '% more critical strike damage.',
    'Marked. Aimed Shot consumes this mark for extra critical strike chance and critical strike damage.',
)
vipers_mark_201921 = _mark(
    201921, "Viper's Mark", School.NATURE, 1630, 40, 45000, 3179,
    'A venomous shot that deals $s2% weapon damage as Nature damage and places Viper\'s Mark on the target for $d. '
    'Each of your abilities against the target adds a stack, up to $u; Serpent Sting adds ' + _favored_extra()
    + ' more. Your Aimed Shot consumes the mark and applies Viper\'s Bite, dealing '
    + pot_text(vipers_bite_201930, variant='total', var='mult')
    + ' Nature damage per stack over $201930d. Your Chimera Shot against the target adds a stack and applies Viper\'s '
    'Venom, dealing ' + pot_text(vipers_venom_201931, variant='total', var='mult') + ' Nature damage over $201931d.',
    "Marked. Aimed Shot consumes this mark to apply Viper's Bite.",
    tooltip=mm_mark_dots_1170,
)
falcons_mark_201922 = _mark(
    201922, "Falcon's Mark", School.NORMAL, 1530, 50, 60000, 8155,
    'A swift shot that deals $s2% weapon damage and places Falcon\'s Mark on the target for $d. Each of your '
    'abilities against the target adds a stack, up to $u, and each stack increases your haste by '
    + _n(MARK_FALCON_HASTE_PER_STACK) + '%. Your Aimed Shot consumes the mark and grants Quickening, increasing your '
    'haste by $201941s1% for ' + _sec(QUICKENING_MS_PER_STACK) + ' sec per stack. Your Chimera Shot against the '
    'target increases your attack power by $201947s1% for $201947d.',
    'Marked. Aimed Shot consumes this mark to grant its caster Quickening.',
)


# Convergence 201932 (MARKSMANSHIP 5.10): data only in S2a (S2b's handler step 9 casts it, spell_hun_convergence binds
# in S2b). Both effects dest-area (the centre may be a corpse). No family bit (script-keyed); family 9 for $RAP.
convergence_201932 = spell(
    id=201932,
    name='Convergence',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=300.0, potency_kind='direct',
               implicit_target_a=87, implicit_target_b=16, radius_yards=8.0),
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=300.0, potency_kind='direct',
               implicit_target_a=87, implicit_target_b=16, radius_yards=8.0),
    ],
    spell_icon_id=2235,
    tooltip_vars=mm_convergence_1171,
    notes='S2a A1 / MM 5.10: Convergence, data only (S2b casts it). eff0 the centre, eff1 the splash, both '
          'TARGET_DEST_DEST (87) + TARGET_UNIT_DEST_AREA_ENEMY (16), 8 yd, ap_potency 300 (placeholder, M). DEVIATION: '
          'MM 5.10 gives eff1 150; the DSL allows one direct AP coefficient per spell (D6), so eff1 carries 300 '
          'too and '
          'spell_hun_convergence (S2b) scales EFFECT_1 by CONVERGENCE_SPLASH_PCT (Swipe 201726 precedent). Physical, '
          'RANGED, Speed 0, Targets 0x40 (dest), SUPPRESS_CASTER_PROCS, no family bit. tooltip_vars 1171.',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 40, 'DefenseType': 3, 'SpellClassSet': 9, 'Targets': 0x40,
        'AttributesEx3': _SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': 'Deals {pot1*mfd} Physical damage to the target and ' + _n(CONVERGENCE_SPLASH_PCT)
                                 + '% as much to up to ' + _n(CONVERGENCE_MAX_TARGETS) + ' other enemies within $a2 '
                                 'yards that are in combat with you.',
    },
)

# Free Arcane Shot 201933 (MARKSMANSHIP 5.10 + S2-HANDOFF stale line 3, S2a A9): clone of Arcane Shot 3044, triggered
# by the Aimed Shot handler (Improved Aimed Shot r3). d0 b11 so Arcane Shot's talents apply; no cost, category or
# cooldown; mana restored by spell_hun_shot_mana like a cast.
# Must equal arcane_shot_3044 eff1 base_points (live 200 = 20.0% base mana); pytest-guarded (A5).
ARCANE_SHOT_MANA_TENTHS = 199
arcane_shot_free_201933 = spell(
    id=201933,
    name='Arcane Shot',
    school=School.ARCANE,
    attributes=65538,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=130.0, potency_kind='direct', implicit_target_a=6),
        # Orchestrator ruling: no import of hunter_spells.py here, so the value is a literal that must equal
        # arcane_shot_3044's eff1 (20.0% of base mana in tenths of a percent, PT-6); A5's pytest asserts the equality.
        Effect(type=EffectType.DUMMY, base_points=ARCANE_SHOT_MANA_TENTHS),
    ],
    spell_icon_id=218,
    tooltip_vars=mm_arcane_shot_1151,
    notes='S2a A9 / MM 5.10: free Arcane Shot (Improved Aimed Shot r3). Arcane SCHOOL_DAMAGE ap_potency 130 (T 1.5, = '
          '3044), eff1 DUMMY = 3044 eff1 (199, 20.0% base mana), no cost/category/cooldown, Speed 40, 50000 yd '
          '(triggered at the target), d0 b11, SUPPRESS_CASTER_PROCS, CastingTimeIndex 18, EquippedItemClass -1 '
          '(triggered helper). tooltip_vars 1151.',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 6, 'DefenseType': 3, 'PreventionType': 2,
        'SpellClassSet': 9, 'SpellClassMask_1': m.ARCANE_SHOT, 'CastingTimeIndex': _USES_RANGED_SLOT_INSTANT,
        'Speed': 40.0, 'AttributesEx2': _DO_NOT_RESET_COMBAT_TIMERS, 'AttributesEx3': _SUPPRESS_CASTER_PROCS,
        'SpellVisualID_1': 3299,
        'Description_Lang_enUS': 'An instant shot that causes {pot1*mult} Arcane damage and restores ${$m2/10}.1% of '
                                 'your base mana.',
    },
)


# ---- buffs and helpers (MARKSMANSHIP 4.5, 4.6, 5.3, 5.4, 5.6-5.10). Visible buffs (M1): no 0x40, no 0x80, no
# AttributesEx7 0x10000000. Hidden: 201948, 201949, 201951. Every SpellMod row: SpellClassSet 9 + a _masks.py mask. ----
def _buff(spell_id, name, effects, icon, duration_ms, notes, masks=None, raw=None, attributes=0):
    overrides = {'EquippedItemClass': -1}
    overrides.update(_mask_overrides(masks))
    overrides.update(raw or {})
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=attributes, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=effects, spell_icon_id=icon, notes=notes, raw_overrides=overrides,
    )


fire_mm_buff_201940 = _buff(
    201940, 'Fire!',
    [_self_aura(AuraType.ADD_PCT_MODIFIER, -101, SpellModOp.CASTING_TIME),
     _self_aura(AuraType.ADD_PCT_MODIFIER, -101, SpellModOp.COST)],
    2230, 20000,
    'S2a A14 / MM 5.8: Fire! (Master Marksman, Rain of Arrows). Aimed Shot cast time and cost -100% (stored -101), '
    'AIMED_SHOT_MASK on both, 1 charge spent by its CAST-phase spell_proc row (non-triggered casts only, MM 0.6).',
    masks={1: m.AIMED_SHOT_MASK, 2: m.AIMED_SHOT_MASK},
    raw={**_FAMILY, 'ProcCharges': 1,
         'Description_Lang_enUS': 'Your next Aimed Shot within $d is instant and costs no mana.',
         'AuraDescription_Lang_enUS': 'Your next Aimed Shot is instant and costs no mana.'},
)
quickening_201941 = _buff(
    201941, 'Quickening', [_self_aura(AuraType.HASTE_ALL, 19)], 1530, 10000,
    'S2a A1 / MM 5.9: Quickening, haste +20% (stored 19). The handler passes SPELLVALUE_AURA_DURATION = max(existing, '
    'Falcon stacks x QUICKENING_MS_PER_STACK); 10 s is the DBC ceiling (10 stacks).',
    raw={'Description_Lang_enUS': 'Increases your haste by $s1%.',
         'AuraDescription_Lang_enUS': 'Haste increased by $s1%.'},
)
falcons_haste_201942 = _buff(
    201942, "Falcon's Haste", [_self_aura(AuraType.HASTE_ALL, -1)], 1530, -1,
    "S2a A4 / MM 4.5 + S2-HANDOFF stale line 5 (MM-C2): Falcon's Haste, VISIBLE non-passive buff (X8 name). HASTE_ALL "
    'bp -1 (0); RefreshFalconHaste sets MARK_FALCON_HASTE_PER_STACK x the highest Falcon stack and removes it with the '
    'last Falcon\'s Mark. AttributesEx7 0.',
    raw={'AttributesEx7': 0,
         'AuraInterruptFlags': 0x00080000,   # AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): marks don't follow
         'Description_Lang_enUS': 'Increases your haste by ' + _n(MARK_FALCON_HASTE_PER_STACK)
                                  + "% per stack of your Falcon's Mark.",
         'AuraDescription_Lang_enUS': 'Haste increased by ' + _n(MARK_FALCON_HASTE_PER_STACK)
                                      + "% per stack of your Falcon's Mark."},
)
trick_shots_buff_201943 = _buff(
    201943, 'Trick Shots', [_self_aura(AuraType.DUMMY, -1)], 2541, 10000,
    'S2a A1 / MM 5.3: Trick Shots ricochet-ready marker, data only (S2b casts and consumes it).',
    raw={'Description_Lang_enUS': 'Your next Aimed Shot within $d ricochets to up to ' + _n(PACK_MAX_TARGETS)
                                  + ' other enemies with your marks.',
         'AuraDescription_Lang_enUS': 'Your next Aimed Shot ricochets to up to ' + _n(PACK_MAX_TARGETS)
                                      + ' other enemies with your marks.'},
)
rain_of_arrows_bounce_201944 = _buff(
    201944, 'Rain of Arrows', [_self_aura(AuraType.DUMMY, -1)], 2511, 10000,
    'S2a A1 / MM 5.4: Rain of Arrows bounce-ready marker, data only (S2b casts and consumes it).',
    raw={'Description_Lang_enUS': 'Your next Aimed Shot within $d bounces to up to ' + _n(PACK_MAX_TARGETS)
                                  + ' nearby enemies.',
         'AuraDescription_Lang_enUS': 'Your next Aimed Shot bounces to up to ' + _n(PACK_MAX_TARGETS)
                                      + ' nearby enemies.'},
)
efficiency_buff_201945 = _buff(
    201945, 'Efficiency',
    [_self_aura(AuraType.ADD_PCT_MODIFIER, -11, SpellModOp.CASTING_TIME),
     _self_aura(AuraType.ADD_PCT_MODIFIER, -11, SpellModOp.GLOBAL_COOLDOWN)],
    133, 15000,
    'S2a A14 / MM 5.10: Efficiency buff. Cast time and GCD of Steady / Aimed Shot -10% (stored -11 = rank 1; the '
    'handler passes -10/-20/-30 as BP0/BP1 from the rank), STEADY_AIMED on both, 2 charges spent by its CAST row. '
    'X7 spike: the aura text carries $s1 (does it show the server-set rank value?).',
    masks={1: m.STEADY_AIMED, 2: m.STEADY_AIMED},
    raw={**_FAMILY, 'ProcCharges': 2,
         'Description_Lang_enUS': 'Reduces the cast time and global cooldown of your next $n Steady Shots or Aimed '
                                  'Shots by $s1%.',
         'AuraDescription_Lang_enUS': 'The cast time and global cooldown of your next $n Steady Shots or Aimed Shots '
                                      'are reduced by $s1%.'},
)
precise_shots_buff_201946 = _buff(
    201946, 'Precise Shots', [_self_aura(AuraType.ADD_PCT_MODIFIER, 49, SpellModOp.DAMAGE)],
    2228, 15000,
    'S2a A14 / MM 5.10: Precise Shots buff (Precise Shots r3). Steady Shot damage +50% (stored 49), STEADY_SHOT_MASK, '
    '15 s (guess), 2 charges spent by its CAST row.',
    masks={1: m.STEADY_SHOT_MASK},
    raw={**_FAMILY, 'ProcCharges': 2,
         'Description_Lang_enUS': 'Your next $n Steady Shots deal $s1% more damage.',
         'AuraDescription_Lang_enUS': 'Your next $n Steady Shots deal $s1% more damage.'},
)
# eff1 is MOD_RANGED_ATTACK_POWER_PCT (AuraType 167, raw int: lib/dsl/constants.py has no member for it, brief 5).
chimera_shot_falcon_201947 = _buff(
    201947, "Falcon's Edge",
    [_self_aura(AuraType.MOD_ATTACK_POWER_PCT, 19), _self_aura(167, 19)],   # AuraType 167
    1530, 5000,
    "S2a A1 / MM 5.6: Falcon's Edge (X8 name; Chimera Shot's Falcon read). Attack power and ranged attack power +20% "
    '(stored 19), 5 s, visible; a recast refreshes.',
    raw={'Description_Lang_enUS': 'Increases your attack power by $s1% for $d.',
         'AuraDescription_Lang_enUS': 'Attack power increased by $s1%.'},
)
snipers_mark_aimed_crit_201948 = _buff(
    201948, "Sniper's Mark (Aimed Shot)",
    [_self_aura(AuraType.ADD_FLAT_MODIFIER, -1, SpellModOp.CRITICAL_CHANCE),
     _self_aura(AuraType.ADD_PCT_MODIFIER, -1, SpellModOp.CRIT_DAMAGE_BONUS)],
    3524, -1,
    "S2a A5 / MM 4.6: hidden Sniper crit helper for Aimed Shot (and S2b's ricochet / bounce through d0 b17). eff0 FLAT "
    'crit chance, eff1 PCT crit damage bonus, both bp -1 (0) on AIMED_SHOT_MASK; set by SetSniperCritHelper.',
    masks={1: m.AIMED_SHOT_MASK, 2: m.AIMED_SHOT_MASK},
    raw={**_FAMILY, 'AttributesEx': 0x10000000,
         'Description_Lang_enUS': "Sniper's Mark critical strike bonus for Aimed Shot."},
    attributes=_HIDDEN,
)
snipers_mark_chimera_crit_201949 = _buff(
    201949, "Sniper's Mark (Chimera Shot)",
    [_self_aura(AuraType.ADD_FLAT_MODIFIER, -1, SpellModOp.CRITICAL_CHANCE),
     _self_aura(AuraType.ADD_PCT_MODIFIER, -1, SpellModOp.CRIT_DAMAGE_BONUS)],
    3524, -1,
    "S2a A5 / MM 4.6: hidden Sniper crit helper for Chimera Shot. As 201948 on CHIMERA_SHOT_MASK.",
    masks={1: m.CHIMERA_SHOT_MASK, 2: m.CHIMERA_SHOT_MASK},
    raw={**_FAMILY, 'AttributesEx': 0x10000000,
         'Description_Lang_enUS': "Sniper's Mark critical strike bonus for Chimera Shot."},
    attributes=_HIDDEN,
)
marksmanship_mastery_201951 = _buff(
    201951, 'Marksmanship Mastery',
    [_self_aura(AuraType.ADD_PCT_MODIFIER, -1, SpellModOp.DAMAGE),
     _self_aura(AuraType.ADD_PCT_MODIFIER, -1, SpellModOp.DOT),
     _self_aura(AuraType.PERIODIC_DUMMY, 0, amplitude=1000)],
    3410, -1,
    'S2a A16 / MM 5.7 + 7: hidden Mastery passive (Marked for Death r3, linked_spell type 2). eff0 SPELLMOD_DAMAGE on '
    'the mark presses (d2 b27), eff1 SPELLMOD_DOT on the mark DoTs (d2 b28), both bp -1 (0) set by '
    'spell_hun_mm_mastery from eff2 PERIODIC_DUMMY (1 s).',
    masks={1: (0, 0, m.MARK_PRESS), 2: (0, 0, m.MARK_DOT)},
    raw={**_FAMILY, 'Description_Lang_enUS': 'Your Mastery increases the damage of your marks and their damage over '
                                             'time effects.'},
    attributes=_HIDDEN,
)


# ---- spell_proc rows (MARKSMANSHIP 8). Every key is declared only here (−53234 is A4's, in hunter_shared_spells.py).
# chance 0 = the DBC ProcChance; 100 on the deterministic carriers. ----
# Master Marksman: Steady Shot CAST -> Fire! (new row; ranks 34485-34487 carry ProcChance 4/8/12, A3).
procs_on(-34485, proc_flags=0x100, family_name=9, family_mask=m.STEADY_SHOT_MASK, spell_phase_mask=0x1)
# Wild Quiver: Auto Shot / Steady Shot damage (live key; the live row's other columns are all 0).
procs_on(-53215, proc_flags=0x140, family_name=9, family_mask=m.WILD_QUIVER_PROC, spell_type_mask=1,
         spell_phase_mask=0x2)
# Precision capstone (spell_hun_precision_capstone): your crits, HIT phase, eff0 (the crit aura) never procs.
procs_on(201965, proc_flags=0x100, family_name=9, spell_type_mask=1, spell_phase_mask=0x2, hit_mask=0x2,
         chance=100.0, disable_effects_mask=0x1)
# Rapid Killing r3: kill (PROC_FLAG_KILL) of an XP / honor target (REQ_EXP_OR_HONOR) -> eff2 casts 35098.
procs_on(201981, proc_flags=0x2, attributes_mask=0x1, chance=100.0, disable_effects_mask=0x3)
# Charged buffs: consumption by CAST rows (MM 0.6). No attributes_mask 0x2: only non-triggered casts spend charges.
procs_on(fire_mm_buff_201940, proc_flags=0x100, family_name=9, family_mask=m.AIMED_SHOT_MASK, spell_phase_mask=0x1,
         chance=100.0)
procs_on(efficiency_buff_201945, proc_flags=0x100, family_name=9, family_mask=m.STEADY_AIMED, spell_phase_mask=0x1,
         chance=100.0)
procs_on(precise_shots_buff_201946, proc_flags=0x100, family_name=9, family_mask=m.STEADY_SHOT_MASK,
         spell_phase_mask=0x1, chance=100.0)
procs_on(35098, proc_flags=0x100, family_name=9, family_mask=m.RAPID_KILLING_BUFF, spell_phase_mask=0x1, chance=100.0)


# ---- script bindings and unbinds (MARKSMANSHIP 10.2 as amended by S2a A1-A21; positive keys only, L7). Stock
# and rank spells by bare id (orchestrator ruling: no import of hunter_spells / hunter_trigger_spells /
# hunter_mm_ranks). ----
scripted_by(snipers_mark_201920, 'spell_hun_mark')
scripted_by(vipers_mark_201921, 'spell_hun_mark')
scripted_by(falcons_mark_201922, 'spell_hun_mark')
scripted_by(19434, 'spell_hun_aimed_shot_mm')                               # Aimed Shot
unbind_script(53209, 'spell_hun_chimera_shot')                             # exact live key (0-verify 2a)
scripted_by(53209, 'spell_hun_chimera_shot_mm')                            # Chimera Shot
scripted_by(3044, 'spell_hun_arcane_shot_mm')                              # additive with shot_mana / arcane_shot_bm
scripted_by(arcane_shot_free_201933, 'spell_hun_shot_mana', 'spell_hun_arcane_shot_mm')
scripted_by(56641, 'spell_hun_steady_shot_mm')                             # Steady Shot (its first binding)
scripted_by(201965, 'spell_hun_precision_capstone')                        # Precision r3
scripted_by(201981, 'spell_hun_rapid_killing_capstone')                    # Rapid Killing r3
scripted_by(marksmanship_mastery_201951, 'spell_hun_mm_mastery')
unbind_script(-53234, 'spell_hun_piercing_shots')                          # exact live key (0-verify 2a)
for _rank in (53234, 53237, 53238):                                        # Piercing Shots r1-r3
    scripted_by(_rank, 'spell_hun_piercing_shots_mm')

linked_spell(53244, marksmanship_mastery_201951.id, 2)                     # Marked for Death r3 -> Mastery passive

# SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED (0x01000000, SpellInfo.h; Aura::CanBeSaved): the script-set amounts would come
# back stale from character_aura at login. Falcon's Haste is non-passive (saved otherwise); the crit helpers are
# passive (never saved anyway), set explicitly so a later attribute change can't start saving them.
custom_attr(falcons_haste_201942, attributes=0x01000000)
custom_attr(snipers_mark_aimed_crit_201948, attributes=0x01000000)
custom_attr(snipers_mark_chimera_crit_201949, attributes=0x01000000)
