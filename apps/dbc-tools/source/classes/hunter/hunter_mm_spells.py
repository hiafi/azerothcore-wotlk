"""
Hunter - Marksmanship S2 spells 201920-201952 (hunter-rework MARKSMANSHIP.md 2.1 / 4 / 5): the three marks, the mark
DoTs, Convergence, the free Arcane Shot, the charged and payoff buffs, the Sniper crit helpers and the Mastery passive,
plus the MM const() block (TOOLTIP-RECONCILE X10, MARKSMANSHIP 4.8), the MM tooltip_vars entries (5.12), the S2a
spell_proc rows (8), the S2a script bindings / unbinds (10.2 as amended by S2a-HANDOFF A1-A21) and spellcategory 1301.

Skeleton written by S2a WP-0 0-dsl (variable stems and Names frozen for HunterData.h), completed by S2a WP-A1. S2b
WP-A1 adds 201934-201937, 201950, 201952, the 24691 spell_proc row, the S2b bindings and linked_spell(201982, 201952).
EquippedItemClass -1 on every row except the three player-cast marks (2, M4).

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
    'CHIMERA_SERPENT_BURST_PCT', 60, "Chimera Shot: Serpent Sting burst, percent of the sting's total damage (MM 5.6).",
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
# S2b A1 (S2a deviation 8, TOOLTIP-RECONCILE X10): the tooltip numbers S2a left as literals, plus the shot mask the
# Rapid Killing execute clause reads in C++ (B8; _masks.py has no C++ home, so one uint32 per SpellFamilyFlags dword).
PACK_SHOT_DAMAGE_PCT = const(
    'PACK_SHOT_DAMAGE_PCT', 50,
    "Ricochet / bounce damage, percent of Aimed Shot's (MM 5.3, 5.4).",
    cpp_type='int32',
)
BARRAGE_ICD_MS = const(
    'BARRAGE_ICD_MS', 10000, "Barrage capstone: half Volley internal cooldown, ms (MM 5.5).",
    cpp_type='uint32',
)
COMBAT_EXPERIENCE_CAPSTONE_PCT = const(
    'COMBAT_EXPERIENCE_CAPSTONE_PCT', 30, 'Combat Experience capstone: Intellect, percent of Agility (MM 5.10).',
    cpp_type='int32',
)
HUNTER_SHOTS_MASK_0 = const(
    'HUNTER_SHOTS_MASK_0', m.HUNTER_SHOTS[0], '_masks.HUNTER_SHOTS, SpellFamilyFlags[0] (MM 2.4).',
    cpp_type='uint32',
)
HUNTER_SHOTS_MASK_1 = const(
    'HUNTER_SHOTS_MASK_1', m.HUNTER_SHOTS[1], '_masks.HUNTER_SHOTS, SpellFamilyFlags[1] (MM 2.4).',
    cpp_type='uint32',
)
HUNTER_SHOTS_MASK_2 = const(
    'HUNTER_SHOTS_MASK_2', m.HUNTER_SHOTS[2], '_masks.HUNTER_SHOTS, SpellFamilyFlags[2] (MM 2.4).',
    cpp_type='uint32',
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
_DO_NOT_DISPLAY = 0x80              # Attributes: hidden aura, not passive (SharedDefines.h; client only)
_SUPPRESS_CASTER_PROCS = 0x10000    # AttributesEx3: proc-free payloads (MM 5 common rules)
_DO_NOT_RESET_COMBAT_TIMERS = 0x20000   # AttributesEx2: stock shot flag (Arcane / Aimed / Chimera Shot)
# AttributesEx2 SPELL_ATTR2_IGNORE_LINE_OF_SIGHT (SharedDefines.h): S2b R-cpp m-1. The pack shots and Convergence are
# defined around the primary target, so CheckCast's hunter-to-target / hunter-to-dest LoS is the wrong test (a marked
# mob behind a pillar would fail its ricochet with SPELL_FAILED_LINE_OF_SIGHT and log an error).
_IGNORE_LINE_OF_SIGHT = 0x4
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


def _mark(spell_id, name, school, icon, level, cooldown_ms, visual, description, aura_text, tooltip=None,
          weapon_potency=220):
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
            Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=weapon_potency, implicit_target_a=6),
            Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=6, apply_aura=AuraType.DUMMY),
        ],
        spell_icon_id=icon,
        tooltip_vars=tooltip,
        notes=f'S2a A1 / MM 4.1: {name}. Instant shot (CastingTimeIndex 18), {weapon_potency} weapon potency '
              f'(TUNE3: was 110), eff2 DUMMY = the mark '
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
    201930, "Viper's Bite", 12000, 1630, 40, 4.6,
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
    weapon_potency=215,
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
          'RANGED, Speed 0, Targets 0x40 (dest), SUPPRESS_CASTER_PROCS, IGNORE_LINE_OF_SIGHT (S2b R-cpp m-1: no '
          'hunter-to-centre LoS fail; the splash also skips the centre-to-target LoS), no family bit. '
          'tooltip_vars 1171.',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 40, 'DefenseType': 3, 'SpellClassSet': 9, 'Targets': 0x40,
        'AttributesEx2': _IGNORE_LINE_OF_SIGHT, 'AttributesEx3': _SUPPRESS_CASTER_PROCS,
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
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=65.0, potency_kind='direct', implicit_target_a=6),
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
# AttributesEx7 0x10000000. Hidden on purpose: 201948, 201949, 201951, S2b's 201952 (passives) and S2b's half Volley
# carrier 201936 (0x80 only, not passive). Every SpellMod row: SpellClassSet 9 + a _masks.py mask. ----
def _buff(spell_id, name, effects, icon, duration_ms, notes, masks=None, raw=None, attributes=0):
    overrides = {'EquippedItemClass': -1}
    overrides.update(_mask_overrides(masks))
    overrides.update(raw or {})
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=attributes, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=effects, spell_icon_id=icon, notes=notes, raw_overrides=overrides,
    )


# Fire!'s flat cast time cut (S2-FIX F-3): must exceed Aimed Shot's live base, 1500 ms DBC + 500 ms ranged-slot add.
FIRE_CAST_TIME_FLAT = -2001


fire_mm_buff_201940 = _buff(
    201940, 'Fire!',
    [_self_aura(AuraType.ADD_FLAT_MODIFIER, FIRE_CAST_TIME_FLAT, SpellModOp.CASTING_TIME),
     _self_aura(AuraType.ADD_PCT_MODIFIER, -101, SpellModOp.COST)],
    2230, 20000,
    'S2a A14 / MM 5.8: Fire! (Master Marksman, Rain of Arrows). Aimed Shot cost -100% (stored -101) and, S2-FIX F-3, '
    'a FLAT cast time cut of -2001 ms (was -100%, stored -101): the client adds the ranged-slot +500 ms after the cast '
    'time mods, so a percentage left a 0.5 s cast; a flat cut larger than the 1500 + 500 base zeroes it on both sides '
    '(Cobra Shot 201811 precedent). Flat first, then percentages and haste, so Efficiency (-10%) and haste only scale '
    'a value that is already <= 0. AIMED_SHOT_MASK on both, 1 charge spent by its CAST-phase spell_proc row '
    '(non-triggered casts only, MM 0.6).',
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
    'X7 ruled 2026-10-17: the aura text is number-free (the spike failed); S3b C-2 also drops the $n charge count.',
    masks={1: m.STEADY_AIMED, 2: m.STEADY_AIMED},
    raw={**_FAMILY, 'ProcCharges': 2,
         'Description_Lang_enUS': 'Reduces the cast time and global cooldown of your next $n Steady Shots or Aimed '
                                  'Shots by $s1%.',
         'AuraDescription_Lang_enUS': 'The cast time and global cooldown of your next Steady Shots or Aimed Shots '
                                      'are reduced.'},
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


# ---- S2b: the ricochet and bounce, Barrage's half Volley, Lone Survivor's buff, Combat Experience's capstone
# (MARKSMANSHIP 5.3, 5.4, 5.5, 5.10; S2b-HANDOFF B2, B6, B7, B9). EquippedItemClass -1 on all six (stale line 6, M4).

# Ricochet 201934 / bounce 201935 (B2): Aimed Shot copies on d0 b17 (R2-12: Aimed Shot's talents and the Sniper crit
# helper reach them), Speed 0 (launch and hit inside the handler's CastSpell), always cast with TRIGGERED_FULL_MASK (R3:
# only TRIGGERED_IGNORE_SPELL_AND_CATEGORY_CD keeps the d0 b17 load fix's 10 s RecoveryTime from starting).
# Must equal aimed_shot_19434's eff1 weapon_potency (hunter_spells.py imports this file, so no import back).
_AIMED_SHOT_WEAPON_POTENCY = 594
_PACK_SHOT_WEAPON_POTENCY = _AIMED_SHOT_WEAPON_POTENCY * int(PACK_SHOT_DAMAGE_PCT['value']) // 100   # 297


def _pack_shot(spell_id, kind, notes):
    return spell(
        id=spell_id,
        name='Aimed Shot',
        school=School.NORMAL,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=50000.0,
        effects=[
            Effect(type=EffectType.NORMALIZED_WEAPON_DMG, base_points=-1, implicit_target_a=6),
            Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=_PACK_SHOT_WEAPON_POTENCY,
                   implicit_target_a=6),
        ],
        spell_icon_id=253,
        notes=notes,
        raw_overrides={
            'EquippedItemClass': -1, 'SpellLevel': 20, 'DefenseType': 3,
            'SpellClassSet': 9, 'SpellClassMask_1': m.AIMED_SHOT,
            'CastingTimeIndex': _USES_RANGED_SLOT_INSTANT, 'Speed': 0.0, 'AttributesEx2': _IGNORE_LINE_OF_SIGHT,
            'AttributesEx3': _SUPPRESS_CASTER_PROCS, 'SpellVisualID_1': 7955,   # Aimed Shot's visual
            'Description_Lang_enUS': f'A {kind} of your Aimed Shot that deals $s2% weapon damage.',
        },
    )


aimed_shot_ricochet_201934 = _pack_shot(
    201934, 'ricochet',
    'S2b A1 / MM 5.3 (B2): Trick Shots ricochet. Physical, RANGED, d0 b17, Speed 0, CastingTimeIndex 18, no cost or '
    'cooldown, 50000 yd, SUPPRESS_CASTER_PROCS, IGNORE_LINE_OF_SIGHT (S2b R-cpp m-1), SpellLevel 20, icon 253; eff0 '
    'NORMALIZED_WEAPON_DMG bp -1, eff1 '
    'weapon_potency 110 (PACK_SHOT_DAMAGE_PCT of Aimed Shot\'s 220). spell_hun_aimed_shot_ricochet scales OnHit by '
    'Triangulation x the Sniper payoff; the handler consumes the target\'s marks afterwards. Visual 7955 (Aimed Shot).',
)
aimed_shot_bounce_201935 = _pack_shot(
    201935, 'bounce',
    'S2b A1 / MM 5.4 (B2): Rain of Arrows bounce, identical to the ricochet 201934 and unscripted (reads and consumes '
    'no marks). Visual 7955 (Aimed Shot).',
)

# Half Volley 201936 / tick 201937 (B6, Q30, the warlock Rain of Fire C5 shape): 201936 eff0 is the dynobj and the
# snapshot source (SpellDamageBonusDone at AfterEffectApply; Barrage / Rain of Arrows reach it through d2 b30), eff1 3
# unhasted 1 s ticks (no AttributesEx5 0x2000); spell_hun_half_volley_aura casts 201937 with BP0 = the snapshot.
# Hidden on purpose (M1): Attributes 0x80 only, so neither the hunter's 3 s eff1 aura nor the eff0 DUMMY on enemies
# shows an icon. Not passive (0x40) and no Stances, so no server path reads the bit: the dynobj, the periodic and the
# aura script run as before.
half_volley_201936 = spell(
    id=201936,
    name='Volley',
    school=School.ARCANE,
    attributes=_DO_NOT_DISPLAY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=3000,
    effects=[
        # Placeholder, M: one Volley tick (42243's 75.5 direct, T 1.5).
        Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=28, radius_yards=8.0,
               ap_potency=75.5, potency_kind='direct', time_basis_ms=1500),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000, implicit_target_a=1),
    ],
    spell_icon_id=126,
    tooltip_vars=mm_volley_1172,
    notes='S2b A1 / MM 5.5 (B6): Barrage\'s half Volley. Arcane, RANGED, 3 s, Targets 0x40 (dest), 50000 yd, d2 b30 '
          '(HALF_VOLLEY), SUPPRESS_CASTER_PROCS, visual 10384 (Volley\'s), SpellLevel 40 (= 42243\'s, S2b R-data M-1: '
          'the potency BaseLevel; 60 gave every hunter below 60 the level-60 base), icon 126, hidden (Attributes '
          '0x80, A3), CANNOT_BE_SAVED (custom_attr). eff0 PERSISTENT_AREA_AURA DUMMY target 28 radius 8, '
          'ap_potency 75.5 direct T 1.5 (the snapshot source, = one 42243 tick, placeholder M); '
          'eff1 PERIODIC_DUMMY 1000 ms on self, unhasted (3 ticks). '
          'tooltip_vars 1172.',
    raw_overrides={
        # SpellLevel = the Volley tick 42243's: potency derives BaseLevel from it and CalcValue lifts any lower caster
        # level to BaseLevel, so this keeps the snapshot equal to one 42243 tick at every level (pytest-guarded).
        'EquippedItemClass': -1, 'SpellLevel': 40, 'DefenseType': 3, 'Targets': 0x40,
        'SpellClassSet': 9, 'SpellClassMask_3': m.HALF_VOLLEY, 'AttributesEx3': _SUPPRESS_CASTER_PROCS,
        'SpellVisualID_1': 10384,
        'Description_Lang_enUS': 'Calls down a volley of arrows at the target location, dealing {pot1*mult} Arcane '
                                 'damage to enemies within $a1 yards that are in combat with you every $t2 sec for $d.',
        'AuraDescription_Lang_enUS': 'Raining arrows on the target area.',
    },
)
half_volley_tick_201937 = spell(
    id=201937,
    name='Volley',
    school=School.ARCANE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=100.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=87, implicit_target_b=16, radius_yards=8.0,
               potency_excluded='snapshot from 201936 eff0 passed as BP0 each tick (C5)'),
    ],
    spell_icon_id=126,
    notes='S2b A1 / MM 5.5 (B6): half Volley tick. Arcane SCHOOL_DAMAGE, TARGET_DEST_DEST (87) + '
          'TARGET_UNIT_DEST_AREA_ENEMY (16) radius 8, amount = BP0 from spell_hun_half_volley_aura (potency_excluded), '
          'IGNORE_CASTER_MODIFIERS | SUPPRESS_CASTER_PROCS (no second done pass, no procs), RANGED, 100 yd (RangeIndex '
          '135), visual 9493 (42243\'s), family 9 with no bit (FAMILY-BITS 0.6). spell_hun_half_volley_tick keeps '
          'in-combat units only.',
    raw_overrides={
        'EquippedItemClass': -1, 'SpellLevel': 60, 'DefenseType': 3, 'SpellClassSet': 9, 'RangeIndex': 135,
        'AttributesEx3': 0x20000000 | _SUPPRESS_CASTER_PROCS, 'SpellVisualID_1': 9493,
    },
)

# Lone Survivor 201950 (B7, M1 visible): the DBC 5% is a default; spell_hun_lone_survivor / RefreshLoneSurvivor set the
# rank's eff0 (Classic) or eff1 (Classless, M12) through BP0. No number in the aura text (X7 spike still pending).
lone_survivor_buff_201950 = _buff(
    201950, 'Lone Survivor',
    [_self_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 4, misc_value=127)],
    535, -1,
    'S2b A1 / MM 5.10 (B7): Lone Survivor buff, VISIBLE (M1: not passive, no 0x80, AttributesEx7 0). '
    'MOD_DAMAGE_PERCENT_DONE all schools (misc 127) bp 4 (DBC default 5%; the script passes the rank / Classless '
    'value), until removed (the rank\'s 500 ms tick, pet summon, pet death). Icon 535 (X21).',
    raw={'AttributesEx7': 0,
         'Description_Lang_enUS': 'Increases the damage you deal while you have no pet.',
         'AuraDescription_Lang_enUS': 'Damage dealt increased.'},
)

# Combat Experience capstone 201952 (B9, M1 hidden): linked to Combat Experience r3 201982 (type 2, below);
# spell_hun_combat_experience_capstone sets eff0 to COMBAT_EXPERIENCE_CAPSTONE_PCT of Agility on each eff1 tick.
combat_experience_capstone_201952 = _buff(
    201952, 'Combat Experience',
    [_self_aura(AuraType.MOD_STAT, -1, misc_value=3),     # misc 3 = STAT_INTELLECT
     _self_aura(AuraType.PERIODIC_DUMMY, 0, amplitude=1000)],
    2223, -1,
    'S2b A1 / MM 5.10 (B9): hidden Combat Experience capstone passive (attributes 464). eff0 MOD_STAT Intellect bp -1 '
    '(0), set by spell_hun_combat_experience_capstone from eff1 PERIODIC_DUMMY (1 s) to COMBAT_EXPERIENCE_CAPSTONE_PCT '
    'x Agility, only on change. Int never feeds Agility (no loop).',
    raw={'Description_Lang_enUS': 'Increases your Intellect by ' + _n(COMBAT_EXPERIENCE_CAPSTONE_PCT)
                                  + '% of your Agility.'},
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
# S2b B6: Barrage r3's half Volley. Multi-Shot CAST (non-triggered: no attributes_mask 0x2), chance 0 = the DBC 25%,
# BARRAGE_ICD_MS internal cooldown; eff0 (the SpellMod) never procs. spell_hun_barrage_capstone's OnEffectProc on eff1.
procs_on(24691, proc_flags=0x100, family_name=9, family_mask=(m.MULTI_SHOT, 0, 0), spell_phase_mask=0x1,
         cooldown_ms=int(BARRAGE_ICD_MS['value']), disable_effects_mask=0x1)


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

# S2b (S2b-HANDOFF brief; positive keys only, L7; 2643 / 1510 / 24691 / 19407 / 19412 have no live binding, and stock
# spell_hun_volley_trigger stays on -42243).
scripted_by(2643, 'spell_hun_multi_shot_mm')                               # Multi-Shot (its first binding)
scripted_by(aimed_shot_ricochet_201934, 'spell_hun_aimed_shot_ricochet')
scripted_by(convergence_201932, 'spell_hun_convergence')
scripted_by(1510, 'spell_hun_volley_mm')                                   # Volley (additive to -42243's trigger)
scripted_by(24691, 'spell_hun_barrage_capstone')                           # Barrage r3
scripted_by(half_volley_201936, 'spell_hun_half_volley_aura')
scripted_by(half_volley_tick_201937, 'spell_hun_half_volley_tick')
for _rank in (19407, 19412):                                               # Lone Survivor r1-r2
    scripted_by(_rank, 'spell_hun_lone_survivor')
scripted_by(combat_experience_capstone_201952, 'spell_hun_combat_experience_capstone')

linked_spell(53244, marksmanship_mastery_201951.id, 2)                     # Marked for Death r3 -> Mastery passive
linked_spell(201982, combat_experience_capstone_201952.id, 2)              # Combat Experience r3 -> capstone passive

# SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED (0x01000000, SpellInfo.h; Aura::CanBeSaved): the script-set amounts would come
# back stale from character_aura at login. Falcon's Haste and S2b's Lone Survivor buff are non-passive (saved
# otherwise); the crit helpers are passive (never saved anyway), set explicitly so a later attribute change can't start
# saving them. S2b's half Volley caster aura 201936 is non-passive too (R-cpp m-4): a logout in its 3 s window would
# reload it without its dynobj.
custom_attr(falcons_haste_201942, attributes=0x01000000)
custom_attr(lone_survivor_buff_201950, attributes=0x01000000)
custom_attr(half_volley_201936, attributes=0x01000000)
custom_attr(snipers_mark_aimed_crit_201948, attributes=0x01000000)
custom_attr(snipers_mark_chimera_crit_201949, attributes=0x01000000)
