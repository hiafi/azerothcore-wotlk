"""
Warrior - S2 Arms delta, data half owned by agent A2: every new Arms spell 204490-204544, the first declarations of the
stock Arms rank rows S2 edits (12296, 12163/12711/12712, 46854/46855, 46865/46866, 29723/29725/29724,
46867/56611/56612, 12281/12812/12813, 30069/30070), and every S2 `scripted_by` / `unbind_script` /
`remove_spell_proc` / `procs_on` on a stock or legacy id (so the big rank files only carry row edits; S2 handoff D1).

Source of truth: docs/reworks/warrior-arms-rework.md (tooltips and aura texts verbatim),
.agents/plans/warrior-rework/warrior-rework.S2-WP-BRIEF.md (frozen variable names, class names, rulings R1-R21; the
brief wins), warrior-rework.S2-HANDOFF.md (D3-D28, D30) and warrior-rework.S2-0VERIFY.md (part A items 1-3, 9, 12-15, 17
and part B items 4-8, 10, 11). Row shapes: research arms-data.md sections 2, 4.2, 8, 11.1; the shapes proven by the P0
spike (p0-spike-ref/warrior_p0_spike.py: Colossus Smash, its debuff, the Sweeping copy) and S1 (warrior_protection.py:
the percent-bleed tick 204775, the empowered Revenge buff, the rank-row shape of Resolve in warrior_trigger_spells.py).

Ids: 204490-204544 as D30 (204545 stays unused: 0-verify B item 4 proves the RADIUS SpellMod reaches the Heroic Leap
landing). Talents 60450-60460 and their grid are warrior_talents.py (A3); the SkillLineAbility rows 30850-30852 are
emitted there by `granted_by_talent(..., skill_line_ability_ids=[...])`, so no `skill_line_ability()` call lives here.
The existing rank rows S2 only edits (Heavy Blows, Improved Rend 1-2, Improved Charge, Impale, Deep Wounds, Improved
Overpower, Taste for Blood, Second Wind, Improved Mortal Strike, Blood Frenzy, Juggernaut 1, Endless Rage 1, ...) stay
in warrior_trigger_spells.py / warrior_spells.py (A1 / A3).

Deviations from the handoff that the brief or the 0-verify already ruled, all honoured here: no `spell_group(1108,
30070)` (R8: 30070 is rank 2 of 30069's chain and LoadSpellGroups rejects a non-first rank), no `procs_on` row for
Exploiter (R7: the debuff is applied by the Execute-cast dispatcher branch, the rank rows are DUMMY carriers with
ProcTypeMask / ProcChance 0), Weight of the Earth is a `SpellClassSet 4` RADIUS mod (R9), Sudden Death keeps
`SpellFamilyName 4` with an empty mask in its proc row (R10), aura 52 for Two-Handed Weapon Specialization's crit (R20).

Bindings use raw ids, never imports of variables from the sibling files, so this file has no import cycle with the rank
files A1 and A3 are editing.
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import custom_attr, procs_on, remove_spell_proc, scripted_by, spell, unbind_script

from . import _masks
from ._tooltips import _desc


# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h, decoded) ----
_ATTR0_IS_ABILITY = 0x10                    # SPELL_ATTR0_ABILITY: a melee ability, not a "spell"
_ATTR0_PASSIVE = 0x40                       # SPELL_ATTR0_PASSIVE: always on, no cast
_ATTR0_DO_NOT_DISPLAY = 0x80                # SPELL_ATTR0_DO_NOT_DISPLAY: not in the spellbook, aura bar or combat log
_HIDDEN_PASSIVE = _ATTR0_PASSIVE | _ATTR0_DO_NOT_DISPLAY
_TALENT_RANK_ATTRIBUTES = 464               # 0x1D0: the passive talent-rank shape (Resolve, warrior_trigger_spells.py)
_ABILITY_ATTRIBUTES = 0x50010               # stock warrior strike buttons (12294, 50622): IS_ABILITY + two stock bits
_SWEEPING_ATTRIBUTES = 0x40010              # stock 12328 minus any NOT_SHAPESHIFTED 0x10000 (D4: usable in any form)
_ATTR_EX_STRIKE = 0x8000200                 # stock Mortal Strike's AttributesEx (P0 Colossus Smash frame)
_ATTR2_CANT_CRIT = 0x20000000               # SPELL_ATTR2_CANT_CRIT
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x4           # SPELL_ATTR2_IGNORE_LINE_OF_SIGHT (a tick must not die behind a corner)
_ATTR3_STRIKE_FRAME = 0x400                 # stock Mortal Strike's AttributesEx3 (P0 Colossus Smash frame)
_ATTR3_DOT_STACKING_RULE = 0x80             # SPELL_ATTR3_DOT_STACKING_RULE: one instance of the aura per caster
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000      # SPELL_ATTR3_SUPPRESS_CASTER_PROCS: the hit raises no caster procs
_ATTR3_ALWAYS_HIT = 0x40000                 # SPELL_ATTR3_ALWAYS_HIT: never missed, dodged, parried or blocked
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000   # SPELL_ATTR3_IGNORE_CASTER_MODIFIERS: caster done-mods not applied
_ATTR4_SUPPRESS_WEAPON_PROCS = 0x800000     # SPELL_ATTR4_SUPPRESS_WEAPON_PROCS: no weapon enchant / item procs
# Server-only custom attribute (SpellInfo.h SPELL_ATTR0_CU_IGNORE_ARMOR). A share of a hit that already went through
# armor must not lose armor a second time (Unit.cpp checks armor before the bleed exemption). Not 0x200000 (ignore
# damage-taken mods): the target's taken-mods (Colossus Smash, Blood Frenzy, Mangle) must still raise each tick.
_CU_IGNORE_ARMOR = 0x8000

# ---- Auras / targets / misc values ----
_SPELLFAMILY_WARRIOR = 4
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_SRC_AREA_ENEMY = 22            # Whirlwind 50622's effect 0 (A) ...
_TARGET_SRC_CASTER = 15                     # ... and its B
_MECHANIC_BLEED = 15
_SCHOOLS_ALL = 127                          # aura 87 misc 127: every school
_AURA_MOD_INCREASE_ENERGY = 35              # SPELL_AURA_MOD_INCREASE_ENERGY: misc = power (1 = rage), amount in tenths
_AURA_MOD_ARMOR_PENETRATION_PCT = 280       # SPELL_AURA_MOD_ARMOR_PENETRATION_PCT (Mace Specialization's aura)
_POWER_RAGE_MISC = 1
_CR_MASTERY = 1 << 20                       # aura 306 misc = 1 << CombatRating.MASTERY (20), Unwavering Sentinel shape
_SCRIPT_CAST_RANGE = 50000.0                # a spell a script casts at another unit: a real range (bug log 570)
_WEAPON_CLASS = 2
_WEAPON_SUBCLASSES = 173555                 # stock strike buttons' EquippedItemSubclass
_TWO_HANDED_SUBCLASSES = 354                # 0x162: two-handed axe | mace | polearm | sword (stock THWS gate)
_DMG_CLASS_MELEE = 2
_PREVENTION_PACIFY = 2
_GCD_CATEGORY = 133
_GCD_MS = 1500

# ---- Stock icons / visuals (arms-data 4.2, 0-verify item 13; V replaces Colossus Smash's and Avatar's) ----
_ICON_ANGER_MANAGEMENT = 238
_ICON_OVERPOWER = 26                        # Battlelord (doc: stock Overpower icon)
_ICON_COLOSSUS_SMASH = 90421                # was Slam's 559 (Q14); playtest 2026-10-30: Ascension art (patch-I)
_ICON_AVATAR = 90420                        # was Recklessness's 138; playtest 2026-10-30: Ascension art (patch-I)
_ICON_FAN_OF_KNIVES = 2904                  # stock Fan of Knives: Improved Sweeping Strikes (playtest 2026-10-30)
_ICON_SWEEPING = 515
_ICON_DEEP_WOUNDS = 243
_ICON_SECOND_WIND = 1697
_ICON_WHIRLWIND = 83
_ICON_HEROIC_LEAP = 3149
_ICON_STRENGTH_OF_ARMS = 279                # the stock rank rows' icon, kept
_ICON_JUGGERNAUT = 2769
_ICON_ENDLESS_RAGE = 1962
_ICON_WRECKING_CREW = 2770
_ICON_SWORD_SPEC = 1462
_ICON_AXE_SPEC = 1474                       # Poleaxe Specialization's
_ICON_MACE_SPEC = 367                       # Mace Specialization's
_ICON_REND = 245
_ICON_MARTIAL_PROWESS = 563                 # Riposte: free after Deflection retires (V replaces)
_ICON_THWM = 1976                           # Weapon Mastery's, free after it retires (V replaces)
_ICON_LINGERING_WOUNDS = 218                # Impaling Bolt (V replaces)
_ICON_EXPLOITER = 565                       # Sunder
_ICON_MOMENTUM = 85                         # Upgrade Moon Glaive (V replaces)
_SV_MORTAL_STRIKE = 39
_SV_RECKLESSNESS = 236
_SV_SWEEPING = 211
_SV_SUNDER = 406
_SV_WHIRLWIND = 223
_SV_BLADESTORM_WHIRL = 11756
_SV_BLEED = 372

# ---- SpellClassSet 4 family bits the Arms rows carry or read (FAMILY-BITS section 2 / arms-data section 8) ----
_CHARGE_D0 = 0x1
_OVERPOWER_D0 = 0x4
_REND_D0 = 0x20
_SLAM_D0 = 0x200000
_MORTAL_STRIKE_D0 = 0x2000000
_EXECUTE_D0 = 0x20000000
_THUNDER_CLAP_D0 = 0x80
_DEEP_WOUNDS_D1 = 0x10
_SWEEPING_D1 = 0x100000
_BLADESTORM_D1 = 0x4000
# Wrecking Crew's list (D22): Overpower | Thunder Clap | Mortal Strike | Execute, Bladestorm (d1), Heroic Leap |
# Colossus Smash (d2).
_WRECKING_CREW_MASK = (_OVERPOWER_D0 | _THUNDER_CLAP_D0 | _MORTAL_STRIKE_D0 | _EXECUTE_D0, _BLADESTORM_D1,
                       _masks.HEROIC_LEAP | _masks.COLOSSUS_SMASH)

# ---- Index rows (existing only, no row minted: handoff D30, 0-verify item 15) ----
_RANGE_INDEX_SELF = 1
_RANGE_INDEX_MELEE = 2
_DURATION_INFINITE = 21


def _raw(description, aura_description=None, level=None, **extra):
    """Per-spell defaults of the Arms kit plus `extra` raw columns (applied last): family 4, no equipment requirement,
    instant cast, chain amplitudes 1.0 (a 0 makes a second target take nothing), `level` sets BaseLevel and
    SpellLevel together (the potency anchor and the trainer-level lint)."""
    raw = {
        'SpellClassSet': _SPELLFAMILY_WARRIOR,
        'EquippedItemClass': -1,
        'CastingTimeIndex': 1,
        'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'EffectChainAmplitude_3': 1.0,
        'Description_Lang_enUS': description,
    }
    if level is not None:
        raw['BaseLevel'] = level
        raw['SpellLevel'] = level
    if aura_description is not None:
        raw['AuraDescription_Lang_enUS'] = aura_description
    raw.update(extra)
    return raw


def _rank_raw(description, subtext='', **extra):
    """The passive talent-rank frame (Resolve, warrior_trigger_spells.py): family 4, no equipment gate, SpellLevel 1,
    ProcChance 101 (no proc unless `extra` says so), self range."""
    raw = _raw(description, SpellLevel=1, SpellPriority=50, ProcChance=101, RangeIndex=_RANGE_INDEX_SELF,
               NameSubtext_Lang_enUS=subtext)
    raw.update(extra)
    return raw


def _arms(spell_id, name, effects, icon, notes, raw, *, attributes=0, rage=0, range_yards=None, cooldown_ms=0,
          duration_ms=None, mechanic=0):
    """Every non-rank Arms spell: physical, instant, rage cost if any, no category, raw index columns in `raw`."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, mechanic=mechanic, attributes=attributes, category=0,
        cast_time_ms=0, cooldown_ms=cooldown_ms, category_cooldown_ms=0, power_type=PowerType.RAGE,
        mana_cost=rage * 10, mana_cost_pct=0, range_yards=range_yards, duration_ms=duration_ms, effects=effects,
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _talent_rank(spell_id, name, effects, icon, notes, raw, *, attributes=_TALENT_RANK_ATTRIBUTES):
    """A passive talent-rank spell: no cooldown, no cost, self range, 0.0 yd (Resolve shape)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=attributes, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0, effects=effects, spell_icon_id=icon,
        notes=notes, raw_overrides=raw,
    )


def _self_aura(aura, **kwargs):
    return Effect(type=EffectType.APPLY_AURA, apply_aura=aura, implicit_target_a=_TARGET_UNIT_CASTER, **kwargs)


def _spellmod(aura, op, base_points, **kwargs):
    """ADD_FLAT_MODIFIER / ADD_PCT_MODIFIER on the caster; the family-bit mask goes in the spell's
    EffectSpellClassMask{A,B,C}_{1,2,3} raw column (letter = effect index, number = dword)."""
    return _self_aura(aura, base_points=base_points, misc_value=int(op), **kwargs)


def _carrier(base_points):
    """A DUMMY value carrier the C++ reads (value = base_points + 1)."""
    return _self_aura(AuraType.DUMMY, base_points=base_points)


def _weapon_strike(percent, target=_TARGET_UNIT_TARGET_ENEMY, **kwargs):
    return Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=float(percent), implicit_target_a=target,
                  **kwargs)


# =====================================================================================================================
# 204490 Colossus Smash (button) and 204491 (the debuff)  -- D3, doc "Colossus Smash"
# =====================================================================================================================
# Button: the P0 spike shape (warrior_p0_spike.py p0_colossus_smash_204888, PASSED): stock Mortal Strike frame
# (Attributes 0x50010, AttributesEx 0x8000200, AttributesEx3 0x400, FacingCasterFlags 1, melee range index 2, weapon
# class 2 / 173555, DmgClass melee, pacify prevention), GCD 133 / 1500, 20 rage, RecoveryTime 20000 with Category 0 (a
# 20 s base is below the Cooldown Haste 30 s floor, so it is never eligible; Mortal Strike's cut is in real seconds),
# SpellLevel = BaseLevel 40. SpellClassMask_3 = 0xA = b1 (Colossus Smash, reads: Impale, Wrecking Crew, Two-Handed
# Weapon Mastery) | b3 (the R1 damaging-ability group, Impale and Recklessness read it). eff0 WEAPON_PERCENT_DAMAGE 150%
# [tune], eff1 TRIGGER_SPELL -> 204491 on the target (the hit lands before the debuff: the multiplier hook skips the
# button's own id as well, D3). Icon 90421 (patch-I, playtest 2026-10-30; was Slam's 559). Visual 39.
colossus_smash_204490 = _arms(
    204490, 'Colossus Smash',
    [_weapon_strike(420),
     Effect(type=EffectType.TRIGGER_SPELL, die_sides=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            trigger_spell=204491)],
    _ICON_COLOSSUS_SMASH,
    'warrior-rework S2 A2 (D3, doc "Colossus Smash"): the button, P0 p0_colossus_smash_204888 shape. Attributes '
    '0x50010, AttributesEx 0x8000200, AttributesEx3 0x400, melee range (index 2), weapon class 2 / 173555, GCD '
    '133 / 1500, 20 rage, RecoveryTime 20000 (Category 0: never Cooldown-Haste eligible, the allow list must not '
    'gain it), SpellLevel = BaseLevel 40, SpellClassMask_3 = 0xA (d2 b1 Colossus Smash | b3 damaging-ability group). '
    'eff0 WEAPON_PERCENT_DAMAGE 150% [tune], eff1 TRIGGER_SPELL -> 204491 on the target. Icon 90421 (patch-I; was '
    'Slam\'s 559), visual 39 (Mortal Strike\'s swing).',
    _raw('Smash the target for 420% weapon damage and expose it for 6 sec, increasing the damage it takes from you by '
         '15% plus your Mastery. Your Mortal Strike reduces the remaining cooldown of Colossus Smash by 2 sec.',
         level=40, RangeIndex=_RANGE_INDEX_MELEE, FacingCasterFlags=1, DefenseType=_DMG_CLASS_MELEE,
         PreventionType=_PREVENTION_PACIFY, EquippedItemClass=_WEAPON_CLASS, EquippedItemSubclass=_WEAPON_SUBCLASSES,
         AttributesEx=_ATTR_EX_STRIKE, AttributesEx3=_ATTR3_STRIKE_FRAME, SpellPriority=50,
         SpellClassMask_3=_masks.COLOSSUS_SMASH | _masks.DAMAGING_ABILITY_GROUP, SpellVisualID_1=_SV_MORTAL_STRIKE,
         StartRecoveryCategory=_GCD_CATEGORY, StartRecoveryTime=_GCD_MS, DurationIndex=_DURATION_INFINITE),
    attributes=_ABILITY_ATTRIBUTES, rage=20, range_yards=5.0, cooldown_ms=20000,
)

# Debuff: visible APPLY_AURA DUMMY on the target (never aura 271: the core already reads 271 on weapon strikes, so it
# would apply twice and leak into the Sweeping share, handoff C1). 6 s (DurationIndex 32), AttributesEx3 0x80 (one
# instance per caster), SpellClassMask_3 = 0x2 (d2 b1), 50000 yd (script / trigger cast, bug 570). The +15% (+ Mastery
# with the talent) multiplier lives in WarriorUnitScript, caster-only.
colossus_smash_debuff_204491 = _arms(
    204491, 'Colossus Smash',
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    _ICON_COLOSSUS_SMASH,
    'warrior-rework S2 A2 (D3): the debuff 204490 triggers, Avatar / Weight of the Earth / the Sweeping copy cast. '
    'Visible APPLY_AURA DUMMY (never aura 271, handoff C1) on the target, 6 s (DurationIndex 32), AttributesEx3 0x80 '
    '(DOT_STACKING_RULE: one instance per caster), SpellClassMask_3 = 0x2 (d2 b1; Two-Handed Weapon Mastery\'s '
    'DURATION mod reads it), 50000 yd. The caster-only +15% is WarriorUnitScript\'s, not an aura.',
    _raw('Taking more damage from the warrior who smashed it.', 'Taking more damage from the warrior who smashed it.',
         AttributesEx3=_ATTR3_DOT_STACKING_RULE, SpellClassMask_3=_masks.COLOSSUS_SMASH, SpellVisualID_1=_SV_SUNDER,
         SpellPriority=50),
    range_yards=_SCRIPT_CAST_RANGE, duration_ms=6000,
)


# =====================================================================================================================
# 204492 Avatar  -- D7, doc "Avatar"
# =====================================================================================================================
# Off the GCD, no cost, RecoveryTime 90000 (Cooldown Haste applies), 20 s (idx 18), MOD_SCALE (61) +30% [tune] on the
# caster, SpellLevel = BaseLevel 60, no family bit. Recklessness' icon 138 and glow 236 (handoff Q14, D35). The melee
# hook that applies the Colossus Smash debuff while the aura is up is WarriorUnitScript's (OnSpellDamageTakenFinal).
avatar_204492 = _arms(
    204492, 'Avatar',
    [_self_aura(AuraType.MOD_SCALE, base_points=29)],
    _ICON_AVATAR,
    'warrior-rework S2 A2 (D7, doc "Avatar"): off the GCD (no StartRecoveryTime), no cost, 90 s cooldown (Cooldown '
    'Haste applies), 20 s (DurationIndex 18), eff0 MOD_SCALE (61) +30% [tune] (bp 29 + die 1) on the caster, visible, '
    'SpellLevel = BaseLevel 60, no family bit. Icon 90420 (patch-I, playtest 2026-10-30), visual 236 is '
    'Recklessness\'s.',
    _raw('You grow larger for 20 sec. Each of your melee abilities applies your Colossus Smash to every enemy it '
         'strikes.', 'Your attacks smash through enemy defenses.', level=60, SpellVisualID_1=_SV_RECKLESSNESS,
         SpellPriority=50),
    attributes=_ATTR0_IS_ABILITY, range_yards=RANGE_SELF, cooldown_ms=90000, duration_ms=20000,
)


# =====================================================================================================================
# 204493 Sweeping Strikes (Arms) and 204494 (the copy)  -- D4, doc "Sweeping Strikes"
# =====================================================================================================================
# 204493 replaces stock 12328 as talent 133's rank (12328 keeps its load-time correction and its NPC users). Attributes
# 0x40010 (no NOT_SHAPESHIFTED 0x10000: usable in any form), off the GCD, 30 rage, RecoveryTime 30000 with NO category
# (a shared category does not lock across spell families on this core, handoff C2/Q8: the Blade Flurry cross-cooldown
# is the scripts'), 10 s (idx 1; Improved Sweeping Strikes' DURATION mod reads d1 0x100000), visible self DUMMY,
# SpellLevel = BaseLevel 30, PreventionType 2, stock visual 211 and icon 515.
sweeping_strikes_arms_204493 = _arms(
    204493, 'Sweeping Strikes',
    [_self_aura(AuraType.DUMMY)],
    _ICON_SWEEPING,
    'warrior-rework S2 A2 (D4, doc "Sweeping Strikes"): the Arms Sweeping Strikes, talent 133\'s rank. Attributes '
    '0x40010 (stock 12328\'s, no NOT_SHAPESHIFTED 0x10000), off the GCD, 30 rage, RecoveryTime 30000 and no category '
    '(Cooldown Haste applies; the Blade Flurry cross-cooldown is the two scripts\'), 10 s (DurationIndex 1), eff0 '
    'DUMMY on the caster (the copy capture is WarriorUnitScript\'s), own mask d1 0x100000 (Improved Sweeping Strikes\' '
    'DURATION mod), SpellLevel = BaseLevel 30, PreventionType 2, visual 211. SkillLineAbility 30852 is emitted by '
    'talent 133\'s granted_by_talent.',
    _raw('For 10 sec, your single-target melee abilities also strike up to 4 additional nearby enemies for 40% of '
         'their damage. Rend and Colossus Smash apply in full to each enemy struck. Shares a cooldown with Blade '
         'Flurry.', 'Your melee abilities strike nearby enemies.', level=30, PreventionType=_PREVENTION_PACIFY,
         SpellClassMask_2=_SWEEPING_D1, SpellVisualID_1=_SV_SWEEPING, SpellPriority=50),
    attributes=_SWEEPING_ATTRIBUTES, rage=30, range_yards=RANGE_SELF, cooldown_ms=30000, duration_ms=10000,
)

# 204494: the P0 copy (p0_sweeping_copy_204890, PASSED). Physical SCHOOL_DAMAGE, amount = bp0 the C++ passes (40% /
# 45% / 50% of the main hit before the main target's own taken-mods), DmgClass melee (rolls its own crit), 50000 yd,
# FacingCasterFlags 0, AttributesEx3 IGNORE_CASTER_MODIFIERS | ALWAYS_HIT | SUPPRESS_CASTER_PROCS, AttributesEx4
# SUPPRESS_WEAPON_PROCS. No CANT_CRIT, no CU_IGNORE_ARMOR (the extra target's own armor applies), no family bits.
# Visible (D28 allows either; the combat log shows the extra hits).
sweeping_strikes_copy_204494 = _arms(
    204494, 'Sweeping Strikes',
    [Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            potency_excluded='percent-of-other-damage: 40/45/50% of the main hit, passed as bp0 by the Sweeping '
                             'capture (WarriorUnitScript), no potency of its own')],
    _ICON_SWEEPING,
    'warrior-rework S2 A2 (D4, P0 p0_sweeping_copy_204890 shape): cast triggered by the Sweeping capture on up to 4 '
    'engaged enemies within 8 yd of the main target with bp0 = the share. Physical SCHOOL_DAMAGE, DmgClass melee (its '
    'own crit roll), 50000 yd, FacingCasterFlags 0, AttributesEx3 IGNORE_CASTER_MODIFIERS | ALWAYS_HIT | '
    'SUPPRESS_CASTER_PROCS, AttributesEx4 SUPPRESS_WEAPON_PROCS, no CANT_CRIT, no CU_IGNORE_ARMOR, no family bits, '
    'visible in the combat log (D28: either).',
    _raw('A share of your strike hits a nearby enemy.', DefenseType=_DMG_CLASS_MELEE, FacingCasterFlags=0,
         AttributesEx3=(_ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_ALWAYS_HIT | _ATTR3_SUPPRESS_CASTER_PROCS),
         AttributesEx4=_ATTR4_SUPPRESS_WEAPON_PROCS, SpellVisualID_1=_SV_SWEEPING, SpellPriority=50,
         DurationIndex=_DURATION_INFINITE),
    range_yards=_SCRIPT_CAST_RANGE,
)


# =====================================================================================================================
# 204495 Bladestorm whirl  -- D10, doc "Bladestorm"
# =====================================================================================================================
# 46924's periodic trigger moves to this id (A3): WEAPON_PERCENT_DAMAGE 100% [tune] at A 22 / B 15, radius 8 yd
# (idx 14),
# MaxTargets 5, own mask d1 0x4000 only (Wrecking Crew names Bladestorm; NOT Whirlwind's d1 0x4 / d2 0x8, so Seismic
# Reverberation never echoes it and Sweeping never copies it), AttributesEx3 SUPPRESS_CASTER_PROCS, SpellLevel 50,
# the stock whirl visual 11756. One whirl per second, the once-per-whirl proc roll is the spell script's AfterCast.
bladestorm_whirl_204495 = _arms(
    204495, 'Bladestorm',
    [Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=170.0, implicit_target_a=_TARGET_UNIT_SRC_AREA_ENEMY,
            implicit_target_b=_TARGET_SRC_CASTER, radius_yards=8.0)],
    2782,
    'warrior-rework S2 A2 (D10, doc "Bladestorm"): the Arms Bladestorm whirl, 46924\'s periodic trigger target. '
    'eff0 WEAPON_PERCENT_DAMAGE 100% [tune] at A 22 / B 15 (UNIT_SRC_AREA_ENEMY from SRC_CASTER), EffectRadiusIndex '
    '14 (8 yd), MaxTargets 5 [tune], own mask d1 0x4000 only (Wrecking Crew\'s Bladestorm bit; not Whirlwind\'s d1 '
    '0x4 / d2 0x8, so Seismic never echoes and Sweeping never copies it), AttributesEx3 SUPPRESS_CASTER_PROCS, '
    'SpellLevel = BaseLevel 50, DmgClass melee, visual 11756. No GCD, no cost, no off-hand trigger (Arms is '
    'two-handed).',
    _raw('A whirl of steel strikes up to 5 nearby enemies.', level=50, MaxTargets=5, DefenseType=_DMG_CLASS_MELEE,
         PreventionType=_PREVENTION_PACIFY, SpellClassMask_2=_BLADESTORM_D1, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
         SpellVisualID_1=_SV_BLADESTORM_WHIRL, SpellPriority=50, RangeIndex=_RANGE_INDEX_SELF,
         DurationIndex=_DURATION_INFINITE),
    attributes=_ABILITY_ATTRIBUTES,
)


# =====================================================================================================================
# 204496 Deep Wounds holder and 204497 tick  -- D5, doc "Deep Wounds"
# =====================================================================================================================
# Holder: the visible "Bleeding." debuff on the target (PERIODIC_DUMMY 1000 ms, no spell-haste-periodic attribute so
# the cadence is fixed, 6 s = DurationIndex 32, mechanic bleed). Keeps d1 0x10 (stock 12721's bit: Blood Frenzy's
# aura 109 mask and the doc's "Blood Frenzy keys on it"). Its AuraScript casts the tick every period and Blood Frenzy
# is updated from its apply / remove. Cast on the target by Warrior::ApplyPercentBleed (accumulate = true).
deep_wounds_holder_204496 = _arms(
    204496, 'Deep Wounds',
    [Effect(type=EffectType.APPLY_AURA, mechanic=_MECHANIC_BLEED, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000)],
    _ICON_DEEP_WOUNDS,
    'warrior-rework S2 A2 (D5, doc "Deep Wounds"): the visible bleed holder, Bloodstorm holder 200030 shape. '
    'PERIODIC_DUMMY 1000 ms (no AttributesEx5 0x2000 haste bit: a fixed cadence), 6 s (DurationIndex 32), mechanic '
    'bleed (15), own mask d1 0x10 (Blood Frenzy\'s bit), aura text "Bleeding.", stock bleed visual 372, 50000 yd. '
    'The accumulating amount is Warrior::ApplyPercentBleed(accumulate = true); spell_warr_deep_wounds_holder casts the '
    'tick 204497 each period and updates Blood Frenzy.',
    _raw('Bleeding for Physical damage every 1 sec.', 'Bleeding.', SpellClassMask_2=_DEEP_WOUNDS_D1,
         SpellVisualID_1=_SV_BLEED, SpellPriority=50, PreventionType=1),
    range_yards=_SCRIPT_CAST_RANGE, duration_ms=6000, mechanic=_MECHANIC_BLEED,
)

# Tick: the Bloodstorm tick shape (204775): physical SCHOOL_DAMAGE, mechanic bleed, hidden, CANT_CRIT (a
# percent-of-damage rule: Deep Wounds never crits), IGNORE_CASTER_MODIFIERS (the amount already carries every
# modifier; two-hander talents and Versatility must not raise it), ALWAYS_HIT, SUPPRESS_CASTER_PROCS, custom attr
# 0x8000 (IGNORE_ARMOR: the basis is raw weapon damage and the bleed exemption sits after the armor check),
# DefenseType 0 (DmgClass none), 50000 yd, potency-excluded. No family bits and no 0x200000: the target's taken-mods
# (Colossus Smash, Blood Frenzy, Mangle) still raise each tick.
deep_wounds_tick_204497 = _arms(
    204497, 'Deep Wounds',
    [Effect(type=EffectType.SCHOOL_DAMAGE, mechanic=_MECHANIC_BLEED, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            potency_excluded='the amount is the per-tick share of the accumulated Deep Wounds total that '
                             'spell_warr_deep_wounds_holder passes as bp0 (percent-of-other-damage rule, Arms doc '
                             '"Deep Wounds"); no potency of its own')],
    _ICON_DEEP_WOUNDS,
    'warrior-rework S2 A2 (D5, Bloodstorm tick 204775 shape): the hidden tick the holder casts each second with bp0 = '
    'Warrior::GetPercentBleedTick. Physical SCHOOL_DAMAGE, mechanic 15, Attributes 0x80, Ex2 CANT_CRIT + 0x4 '
    'IGNORE_LINE_OF_SIGHT (S2 fix pass m2: CheckCast runs the caster-to-target LoS test for triggered casts, so a tick '
    'behind a corner was silently lost), Ex3 '
    'IGNORE_CASTER_MODIFIERS + ALWAYS_HIT + SUPPRESS_CASTER_PROCS, DefenseType 0, custom_attr 0x8000 '
    '(CU_IGNORE_ARMOR), 50000 yd, potency_excluded. SpellClassSet 4 with no carrier bits.',
    _raw('Deals Physical damage to the target.', DefenseType=0, AttributesEx2=_ATTR2_CANT_CRIT | _ATTR2_IGNORE_LINE_OF_SIGHT,
         AttributesEx3=(_ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_ALWAYS_HIT | _ATTR3_SUPPRESS_CASTER_PROCS),
         SpellPriority=50),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=_SCRIPT_CAST_RANGE, mechanic=_MECHANIC_BLEED,
)
custom_attr(deep_wounds_tick_204497, _CU_IGNORE_ARMOR)


# =====================================================================================================================
# 204498 Momentum buff  -- D24, doc "Momentum"
# =====================================================================================================================
# Visible, 15 s (DurationIndex 8) [tune], ProcCharges 1 (the next Slam spends it, the Slam! 46916 / Empowered Revenge
# 204770 shape): eff0 ADD_PCT_MODIFIER COST -100% (bp -101) on Slam's bit (EffectSpellClassMaskA_1 = d0 0x200000), eff1
# ADD_PCT_MODIFIER DAMAGE +30% [tune] (bp 29) on the same bit (EffectSpellClassMaskB_1). One charge shared by both mods.
momentum_buff_204498 = _arms(
    204498, 'Momentum',
    [_spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.COST, -101),
     _spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.DAMAGE, 29)],
    _ICON_MOMENTUM,
    'warrior-rework S2 A2 (D24, doc "Momentum"): visible 15 s buff (DurationIndex 8) [tune], ProcCharges 1 (the next '
    'Slam cast spends it), eff0 ADD_PCT_MODIFIER COST -100% (bp -101) on Slam (EffectSpellClassMaskA_1 = d0 0x200000), '
    'eff1 ADD_PCT_MODIFIER DAMAGE +30% [tune] (bp 29) on Slam (EffectSpellClassMaskB_1 = d0 0x200000). A second proc '
    'refreshes, never stacks.',
    _raw('Your next Slam costs no rage and deals 30% more damage.', 'Your next Slam is free and stronger.',
         ProcChance=101, ProcCharges=1, EffectSpellClassMaskA_1=_SLAM_D0, EffectSpellClassMaskB_1=_SLAM_D0,
         SpellPriority=50),
    range_yards=RANGE_SELF, duration_ms=15000,
)


# =====================================================================================================================
# 204499 / 204500 Juggernaut buffs  -- D13, doc "Juggernaut"
# =====================================================================================================================
# 204499: the visible half (the doc's aura text), 20 s cap [tune] (DurationIndex 18), DUMMY marker; consumed by Mortal
# Strike when it applies the Rend (Warrior::OnMortalStrikeHit). 204500: the hidden one-charge Slam-crit modifier
# (eff0 ADD_FLAT_MODIFIER CRITICAL_CHANCE +100, bp 99, on Slam's bit), ProcCharges 1, hidden (0x80, not PASSIVE so its
# 20 s duration is honoured). The visible text can outlive the crit half (handoff Q15).
juggernaut_buff_204499 = _arms(
    204499, 'Juggernaut',
    [_carrier(0)],
    _ICON_JUGGERNAUT,
    'warrior-rework S2 A2 (D13, doc "Juggernaut"): the visible marker buff, 20 s cap [tune] (DurationIndex 18), eff0 '
    'DUMMY. Granted by the Charge / Heroic Leap landing scripts with the rank chance; consumed by Mortal Strike\'s '
    'AfterHit when it applies Rend. Its twin 204500 carries the Slam-crit half.',
    _raw('Your next Slam will critically strike and your next Mortal Strike applies Rend.',
         'Your next Slam will critically strike and your next Mortal Strike applies Rend.', SpellPriority=50),
    range_yards=RANGE_SELF, duration_ms=20000,
)

juggernaut_crit_204500 = _arms(
    204500, 'Juggernaut',
    [_spellmod(AuraType.ADD_FLAT_MODIFIER, SpellModOp.CRITICAL_CHANCE, 99)],
    _ICON_JUGGERNAUT,
    'warrior-rework S2 A2 (D13): the hidden half of Juggernaut. eff0 ADD_FLAT_MODIFIER CRITICAL_CHANCE +100 (bp 99) '
    'on Slam (EffectSpellClassMaskA_1 = d0 0x200000), ProcCharges 1 (the next Slam cast spends it), 20 s '
    '(DurationIndex 18), Attributes 0x80 (hidden, not PASSIVE so the duration holds).',
    _raw('Your next Slam critically strikes.', ProcChance=101, ProcCharges=1, EffectSpellClassMaskA_1=_SLAM_D0,
         SpellPriority=50),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=RANGE_SELF, duration_ms=20000,
)


# =====================================================================================================================
# 204501 / 204502 Strength of Arms buffs  -- D14, doc "Strength of Arms"
# =====================================================================================================================
# Visible, 20 s [tune] (DurationIndex 18), CumulativeAura 2, eff0 ADD_PCT_MODIFIER DAMAGE +5% / +10% per stack on
# Mortal Strike (EffectSpellClassMaskA_1 = d0 0x2000000). No ProcCharges: Mortal Strike's AfterHit removes the aura
# (deterministic; the research disagreed on whether a charge drop keeps the stacks, handoff C19).
strength_of_arms_buff_r1_204501 = _arms(
    204501, 'Strength of Arms',
    [_spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.DAMAGE, 4)],
    _ICON_STRENGTH_OF_ARMS,
    'warrior-rework S2 A2 (D14, doc "Strength of Arms"): rank 1 buff (+5% per stack). Visible 20 s [tune] '
    '(DurationIndex 18), CumulativeAura 2, eff0 ADD_PCT_MODIFIER DAMAGE bp 4 on Mortal Strike '
    '(EffectSpellClassMaskA_1 = d0 0x2000000). No ProcCharges: Mortal Strike\'s AfterHit removes it.',
    _raw('Your next Mortal Strike deals 5% more damage per stack.', 'Your next Mortal Strike is stronger.',
         CumulativeAura=2, EffectSpellClassMaskA_1=_MORTAL_STRIKE_D0, SpellPriority=50),
    range_yards=RANGE_SELF, duration_ms=20000,
)

strength_of_arms_buff_r2_204502 = _arms(
    204502, 'Strength of Arms',
    [_spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.DAMAGE, 9)],
    _ICON_STRENGTH_OF_ARMS,
    'warrior-rework S2 A2 (D14, doc "Strength of Arms"): rank 2 buff (+10% per stack). Same shape as 204501 with bp 9.',
    _raw('Your next Mortal Strike deals 10% more damage per stack.', 'Your next Mortal Strike is stronger.',
         CumulativeAura=2, EffectSpellClassMaskA_1=_MORTAL_STRIKE_D0, SpellPriority=50),
    range_yards=RANGE_SELF, duration_ms=20000,
)


# =====================================================================================================================
# 204503 Endless Rage overflow  -- D11, doc "Endless Rage"
# =====================================================================================================================
# Visible, 20 s [tune], CumulativeAura 20 (R13: ModStackAmount(+1) at the cap keeps 20 stacks and refreshes the
# duration), eff0 ADD_PCT_MODIFIER DAMAGE +1% per stack (bp 0 + die 1) on Mortal Strike (EffectSpellClassMaskA_1 = d0
# 0x2000000). No ProcCharges: Mortal Strike's AfterHit removes it (D11).
endless_rage_overflow_204503 = _arms(
    204503, 'Endless Rage',
    [_spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.DAMAGE, 0)],
    _ICON_ENDLESS_RAGE,
    'warrior-rework S2 A2 (D11, doc "Endless Rage"): the overflow buff. Visible 20 s [tune] (DurationIndex 18), '
    'CumulativeAura 20 (1% per stack, up to 20%), eff0 ADD_PCT_MODIFIER DAMAGE bp 0 (1% per stack) on Mortal Strike '
    '(EffectSpellClassMaskA_1 = d0 0x2000000). No ProcCharges: Mortal Strike\'s AfterHit removes it; every new point '
    'of overflow ModStackAmount(+1) refreshes the 20 s.',
    _raw('Your next Mortal Strike deals 1% more damage per stack.', 'Your next Mortal Strike deals more damage.',
         CumulativeAura=20, EffectSpellClassMaskA_1=_MORTAL_STRIKE_D0, SpellPriority=50),
    range_yards=RANGE_SELF, duration_ms=20000,
)


# =====================================================================================================================
# 204504 Exploiter debuff  -- D15, doc "Exploiter" (R7: applied by the Execute-cast dispatcher branch, not a data proc)
# =====================================================================================================================
# Per-caster (AttributesEx3 0x80) visible target aura, CumulativeAura 2, 20 s [tune] (DurationIndex 18), DUMMY. The
# multiplier (1 + rank% x stacks, stacks add) is WarriorUnitScript's, Mortal Strike's id only.
exploiter_debuff_204504 = _arms(
    204504, 'Exploiter',
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    _ICON_EXPLOITER,
    'warrior-rework S2 A2 (D15, R7): the Exploiter debuff on the target. Visible, per caster (AttributesEx3 0x80), '
    'CumulativeAura 2, 20 s [tune] (DurationIndex 18), DUMMY, 50000 yd. Applied by Warrior::OnSpellCast on an Execute '
    'cast (a CAST-phase data proc would target the player\'s selection, 0-verify B item 7); the multiplier is '
    'WarriorUnitScript\'s, Mortal Strike only; Mortal Strike\'s AfterHit removes this caster\'s stacks.',
    _raw('Takes more damage from the warrior\'s next Mortal Strike.',
         'Takes more damage from the warrior\'s next Mortal Strike.', AttributesEx3=_ATTR3_DOT_STACKING_RULE,
         CumulativeAura=2, SpellPriority=50),
    range_yards=_SCRIPT_CAST_RANGE, duration_ms=20000,
)


# =====================================================================================================================
# 204505-204507 Wrecking Crew buffs  -- D22, doc "Wrecking Crew"
# =====================================================================================================================
# 12 s (DurationIndex 29), visible, NOT an Enrage (Dispel 0, Mechanic 0, no group 1104). eff0 ADD_PCT_MODIFIER DAMAGE
# +5 / 10 / 15% on (0x22000084, 0x4000, 0x3) = Overpower | Thunder Clap | Mortal Strike | Execute, Bladestorm (d1),
# Heroic Leap | Colossus Smash (d2): EffectSpellClassMaskA_1/_2/_3. eff1 ADD_PCT_MODIFIER DOT the same percent on Rend
# (EffectSpellClassMaskB_1 = d0 0x20, fixed into the Rend at application). Each crit refreshes, no stacking.
def _wrecking_crew_buff(spell_id, rank, percent):
    return _arms(
        spell_id, 'Wrecking Crew',
        [_spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.DAMAGE, percent - 1),
         _spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.DOT, percent - 1)],
        _ICON_WRECKING_CREW,
        f'warrior-rework S2 A2 (D22, doc "Wrecking Crew"): rank {rank} buff (+{percent}%). Visible 12 s (DurationIndex '
        f'29), not an Enrage. eff0 ADD_PCT_MODIFIER DAMAGE bp {percent - 1} on (0x22000084, 0x4000, 0x3) '
        f'(EffectSpellClassMaskA_1/_2/_3), eff1 ADD_PCT_MODIFIER DOT bp {percent - 1} on Rend '
        f'(EffectSpellClassMaskB_1 = d0 0x20).',
        _raw(f'Increases the damage of your Overpower, Mortal Strike, Execute, Rend, Thunder Clap, Heroic Leap, '
             f'Colossus Smash and Bladestorm by {percent}%.', 'Your strikes hit harder.',
             EffectSpellClassMaskA_1=_WRECKING_CREW_MASK[0], EffectSpellClassMaskA_2=_WRECKING_CREW_MASK[1],
             EffectSpellClassMaskA_3=_WRECKING_CREW_MASK[2], EffectSpellClassMaskB_1=_REND_D0, SpellPriority=50),
        range_yards=RANGE_SELF, duration_ms=12000,
    )


wrecking_crew_buff_r1_204505 = _wrecking_crew_buff(204505, 1, 5)
wrecking_crew_buff_r2_204506 = _wrecking_crew_buff(204506, 2, 10)
wrecking_crew_buff_r3_204507 = _wrecking_crew_buff(204507, 3, 15)


# =====================================================================================================================
# 204508 Anger Management capstone buff  -- D12, doc "Anger Management"
# =====================================================================================================================
# Visible, 4 s (DurationIndex 35) [tune], eff0 MOD_DAMAGE_PERCENT_TAKEN (87) all schools -30% [tune] (bp -31 + die 1).
# Cast on every Charge by spell_warr_charge_rework when the warrior has the rank-3 capstone (B6).
anger_management_capstone_204508 = _arms(
    204508, 'Anger Management',
    [_self_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-31, misc_value=_SCHOOLS_ALL)],
    _ICON_ANGER_MANAGEMENT,
    'warrior-rework S2 A2 (D12, doc "Anger Management"): the capstone buff, visible 4 s (DurationIndex 35) [tune], '
    'eff0 MOD_DAMAGE_PERCENT_TAKEN (87) misc 127 -30% [tune] (bp -31 + die 1). Cast by the Charge script when the '
    'warrior knows the rank-3 capstone.',
    _raw('Taking less damage.', 'Taking less damage.', SpellPriority=50),
    range_yards=RANGE_SELF, duration_ms=4000,
)


# =====================================================================================================================
# 204509 Seismic Reverberation echo  -- D19, doc "Seismic Reverberation"
# =====================================================================================================================
# The Blade Flurry copy shape: hidden SCHOOL_DAMAGE, bp0 = the stored share, CANT_CRIT, DmgClass none, IGNORE_CASTER_
# MODIFIERS | ALWAYS_HIT | SUPPRESS_CASTER_PROCS, custom attr 0x8000 (the share is post-armor), 50000 yd, no family bits
# (it must not carry Whirlwind's d1 0x4 / d2 0x8) and skipped by the Colossus Smash multiplier by id.
seismic_reverberation_echo_204509 = _arms(
    204509, 'Seismic Reverberation',
    [Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            potency_excluded='the amount is 25/50% of each enemy\'s total Whirlwind damage that the 1680 script '
                             'passes as bp0 (percent-of-other-damage rule, Arms doc "Seismic Reverberation"); no '
                             'potency of its own')],
    _ICON_WHIRLWIND,
    'warrior-rework S2 A2 (D19, Blade Flurry copy shape): the hidden echo cast +500 ms after a Whirlwind that struck '
    '3 or more enemies, bp0 = 25/50% of that enemy\'s total Whirlwind damage. Physical SCHOOL_DAMAGE, Attributes 0x80, '
    'Ex2 CANT_CRIT, Ex3 IGNORE_CASTER_MODIFIERS + ALWAYS_HIT + SUPPRESS_CASTER_PROCS, DefenseType 0, custom_attr '
    '0x8000, 50000 yd, potency_excluded, no family bits. The Colossus Smash multiplier skips it by id.',
    _raw('Strikes the enemy again for a share of your Whirlwind\'s damage.', DefenseType=0,
         AttributesEx2=_ATTR2_CANT_CRIT,
         AttributesEx3=(_ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_ALWAYS_HIT | _ATTR3_SUPPRESS_CASTER_PROCS),
         SpellVisualID_1=_SV_WHIRLWIND, SpellPriority=50),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=_SCRIPT_CAST_RANGE,
)
custom_attr(seismic_reverberation_echo_204509, _CU_IGNORE_ARMOR)


# =====================================================================================================================
# 204510 Second Wind heal  -- D18, doc "Second Wind"
# =====================================================================================================================
# Hidden HEAL on the caster, bp0 = damage x 2/4% (x2 below 35% health) from the C++. No IGNORE_CASTER_MODIFIERS (the
# warrior's healing modifiers apply, doc), potency-excluded (percent-of-other-damage).
second_wind_heal_204510 = _arms(
    204510, 'Second Wind',
    [Effect(type=EffectType.HEAL, implicit_target_a=_TARGET_UNIT_CASTER,
            potency_excluded='the amount is 2/4% of a Rend or Deep Wounds tick (doubled below 35% health) that '
                             'Warrior::OnBleedTick passes as bp0 (percent-of-other-damage rule, Arms doc "Second '
                             'Wind"); no potency of its own')],
    _ICON_SECOND_WIND,
    'warrior-rework S2 A2 (D18, doc "Second Wind"): the hidden self heal Warrior::OnBleedTick casts with bp0 = bleed '
    'damage x 2/4% (x2 below 35% health). HEAL at the caster, Attributes 0x80, NO IGNORE_CASTER_MODIFIERS (healing '
    'modifiers apply), potency_excluded, range self.',
    _raw('Heals you for a share of your bleed damage.', SpellPriority=50),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=RANGE_SELF,
)


# =====================================================================================================================
# 204511 Weapon Specialization sword strike  -- D17, doc "Weapon Specialization"
# =====================================================================================================================
# WEAPON_PERCENT_DAMAGE 120% [tune] at the target, cast by spell_warr_weapon_spec_sword (CAST-phase procs carry no
# victim, handoff C12). Melee DmgClass (its own crit), 50000 yd, AttributesEx3 SUPPRESS_CASTER_PROCS and AttributesEx4
# SUPPRESS_WEAPON_PROCS, no rage, no GCD, no family bits (not copied by Sweeping, not an Impale target), SpellLevel 1.
# Hidden (D28).
weapon_specialization_strike_204511 = _arms(
    204511, 'Weapon Specialization',
    [_weapon_strike(120)],
    _ICON_SWORD_SPEC,
    'warrior-rework S2 A2 (D17, doc "Weapon Specialization"): the sword extra strike, cast triggered by '
    'spell_warr_weapon_spec_sword. WEAPON_PERCENT_DAMAGE 120% [tune], DmgClass melee, 50000 yd, AttributesEx3 '
    'SUPPRESS_CASTER_PROCS + AttributesEx4 SUPPRESS_WEAPON_PROCS (it rolls nothing), no rage, no GCD, no family '
    'bits, SpellLevel = BaseLevel 1, Attributes 0x80 (hidden).',
    _raw('Strikes the target with your weapon.', level=1, DefenseType=_DMG_CLASS_MELEE,
         PreventionType=_PREVENTION_PACIFY, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
         AttributesEx4=_ATTR4_SUPPRESS_WEAPON_PROCS, SpellPriority=50, DurationIndex=_DURATION_INFINITE),
    attributes=_ATTR0_DO_NOT_DISPLAY, range_yards=_SCRIPT_CAST_RANGE,
)


# =====================================================================================================================
# 204512-204520 Weapon Specialization passives  -- D17, doc "Weapon Specialization"
# =====================================================================================================================
# Nine hidden passives (0xC0, SpellClassSet 4, NO equipment gate): WarriorPlayerScript keeps exactly the one that
# matches the main-hand weapon at the learned rank (Q3). Axe / polearm: aura 52 crit +2/4/6% and aura 163 misc 1 crit
# damage +2/4/6% [tune]. Mace: aura 280 armor penetration +5/10/15% [tune]. Sword: aura 42 -> 204511, DBC ProcChance
# 3/6/10 [tune], ProcTypeMask 0x14; the spell_proc rows are at the end of the file.
def _weapon_spec_axe(spell_id, rank, percent):
    return _talent_rank(
        spell_id, 'Weapon Specialization',
        [_self_aura(AuraType.MOD_WEAPON_CRIT_PERCENT, base_points=percent - 1),
         _self_aura(AuraType.MOD_CRIT_DAMAGE_BONUS, base_points=percent - 1, misc_value=1)],
        _ICON_AXE_SPEC,
        f'warrior-rework S2 A2 (D17): axe / polearm passive, rank {rank}. Hidden 0xC0, family 4, no equipment gate '
        f'(WarriorPlayerScript keeps one passive for the main-hand weapon). eff0 aura 52 crit +{percent}%, eff1 '
        f'aura 163 misc 1 crit damage +{percent}% [tune].',
        _rank_raw(f'Axes and polearms: critical strike chance and critical strike damage increased by {percent}%.'),
        attributes=_HIDDEN_PASSIVE,
    )


def _weapon_spec_mace(spell_id, rank, percent):
    return _talent_rank(
        spell_id, 'Weapon Specialization',
        [_self_aura(_AURA_MOD_ARMOR_PENETRATION_PCT, base_points=percent - 1)],
        _ICON_MACE_SPEC,
        f'warrior-rework S2 A2 (D17): mace passive, rank {rank}. Hidden 0xC0, family 4, no equipment gate. eff0 aura '
        f'280 armor penetration +{percent}% [tune].',
        _rank_raw(f'Maces: armor penetration increased by {percent}%.'),
        attributes=_HIDDEN_PASSIVE,
    )


def _weapon_spec_sword(spell_id, rank, chance):
    return _talent_rank(
        spell_id, 'Weapon Specialization',
        [_self_aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=204511)],
        _ICON_SWORD_SPEC,
        f'warrior-rework S2 A2 (D17): sword passive, rank {rank}. Hidden 0xC0, family 4, no equipment gate. eff0 '
        f'PROC_TRIGGER_SPELL -> 204511 (spell_warr_weapon_spec_sword prevents the default action and casts the strike '
        f'at the right target), DBC ProcChance {chance} [tune], ProcTypeMask 0x14; spell_proc: flags 0x14, CAST phase, '
        f'Cooldown 3000 (end of file).',
        _rank_raw(f'Swords: your melee hits have a {chance}% chance to grant an extra attack on the same target for '
                  f'120% weapon damage, no more than once every 3 sec.', ProcTypeMask=0x14, ProcChance=chance),
        attributes=_HIDDEN_PASSIVE,
    )


weapon_specialization_axe_r1_204512 = _weapon_spec_axe(204512, 1, 2)
weapon_specialization_mace_r1_204513 = _weapon_spec_mace(204513, 1, 5)
weapon_specialization_sword_r1_204514 = _weapon_spec_sword(204514, 1, 3)
weapon_specialization_axe_r2_204515 = _weapon_spec_axe(204515, 2, 4)
weapon_specialization_mace_r2_204516 = _weapon_spec_mace(204516, 2, 10)
weapon_specialization_sword_r2_204517 = _weapon_spec_sword(204517, 2, 6)
weapon_specialization_axe_r3_204518 = _weapon_spec_axe(204518, 3, 6)
weapon_specialization_mace_r3_204519 = _weapon_spec_mace(204519, 3, 15)
weapon_specialization_sword_r3_204520 = _weapon_spec_sword(204520, 3, 10)


# =====================================================================================================================
# Minted talent ranks  -- D14-D24, doc "Talents and spells"
# =====================================================================================================================
# Martial Prowess 204521-204523 (D24): aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 20 (CR_MASTERY) +1 / 2 / 3% (the
# Unwavering Sentinel shape; value = bp + 1). No capstone.
def _martial_prowess(spell_id, percent):
    return _talent_rank(
        spell_id, 'Martial Prowess',
        [_self_aura(AuraType.MOD_CUSTOM_STAT_PCT, base_points=percent - 1, misc_value=_CR_MASTERY)],
        _ICON_MARTIAL_PROWESS,
        f'warrior-rework S2 A2 (D24, doc "Martial Prowess"): rank {percent}. aura 306 MOD_CUSTOM_STAT_PCT misc 1 << 20 '
        f'(Mastery) +{percent}% (bp {percent - 1} + die 1). Passive talent shape (464), family 4, no carrier bits.',
        _rank_raw(f'Increases your Mastery by {percent}%.'),
    )


martial_prowess_204521 = _martial_prowess(204521, 1)
martial_prowess_204522 = _martial_prowess(204522, 2)
martial_prowess_204523 = _martial_prowess(204523, 3)


# Two-Handed Weapon Mastery 204524-204525 (D16): gated on a two-hander in either hand (EquippedItemClass 2 / subclass
# 0x162, the stock THWS gate). eff0 aura 213 +15 / 30% rage from damage dealt, eff1 aura 79 misc 1 +3 / 6% physical,
# eff2 ADD_FLAT_MODIFIER DURATION +1 / 2 s on the Colossus Smash debuff (EffectSpellClassMaskC_3 = d2 0x2). The Titan's
# Grip clause is deferred to S3 (handoff Q10).
def _two_handed_weapon_mastery(spell_id, rank, rage, damage, seconds):
    return _talent_rank(
        spell_id, 'Two-Handed Weapon Mastery',
        [_self_aura(AuraType.MOD_RAGE_FROM_DAMAGE_DEALT, base_points=rage - 1),
         _self_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=damage - 1, misc_value=1),
         _spellmod(AuraType.ADD_FLAT_MODIFIER, SpellModOp.DURATION, seconds * 1000 - 1)],
        _ICON_THWM,
        f'warrior-rework S2 A2 (D16, doc "Two-Handed Weapon Mastery"): rank {rank}. EquippedItemClass 2 / subclass '
        f'0x162 (stock THWS gate). eff0 aura 213 rage from damage dealt +{rage}% (read by Warrior::RewardRage), eff1 '
        f'aura 79 misc 1 +{damage}%, eff2 ADD_FLAT_MODIFIER DURATION +{seconds} s (bp {seconds * 1000 - 1}) on the '
        f'Colossus Smash debuff (EffectSpellClassMaskC_3 = d2 0x2). Titan\'s Grip clause deferred to S3.',
        _rank_raw(f'You generate {rage}% more rage from damage dealt, deal {damage}% more Physical melee damage, and '
                  f'your Colossus Smash lasts {seconds} sec longer. Only active while wielding a single two-handed '
                  f'weapon; does not work with Titan\'s Grip.', EquippedItemClass=_WEAPON_CLASS,
                  EquippedItemSubclass=_TWO_HANDED_SUBCLASSES, EffectSpellClassMaskC_3=_masks.COLOSSUS_SMASH),
    )


two_handed_weapon_mastery_204524 = _two_handed_weapon_mastery(204524, 1, 15, 3, 1)
two_handed_weapon_mastery_204525 = _two_handed_weapon_mastery(204525, 2, 30, 6, 2)


# Lingering Wounds 204526-204528 (D23): eff0 ADD_FLAT_MODIFIER DURATION +2 / 4 / 6 s on Rend (EffectSpellClassMaskA_1 =
# d0 0x20). Rend is 15 s (DurationIndex 8) -> 21 s at 3 ranks; extra time is extra ticks at the same rate.
def _lingering_wounds(spell_id, seconds):
    return _talent_rank(
        spell_id, 'Lingering Wounds',
        [_spellmod(AuraType.ADD_FLAT_MODIFIER, SpellModOp.DURATION, seconds * 1000 - 1)],
        _ICON_LINGERING_WOUNDS,
        f'warrior-rework S2 A2 (D23, doc "Lingering Wounds"): +{seconds} s. eff0 ADD_FLAT_MODIFIER DURATION bp '
        f'{seconds * 1000 - 1} on Rend (EffectSpellClassMaskA_1 = d0 0x20).',
        _rank_raw(f'Increases the duration of your Rend by {seconds} sec.', EffectSpellClassMaskA_1=_REND_D0),
    )


lingering_wounds_204526 = _lingering_wounds(204526, 2)
lingering_wounds_204527 = _lingering_wounds(204527, 4)
lingering_wounds_204528 = _lingering_wounds(204528, 6)


# Improved Sweeping Strikes 204529-204530 (D24): eff0 ADD_FLAT_MODIFIER DURATION +2 / 4 s on Sweeping Strikes (own mask
# d1 0x100000 = EffectSpellClassMaskA_2), eff1 DUMMY carrier 45 / 50 (the extra-hit percent, read by the copy).
def _improved_sweeping_strikes(spell_id, rank, seconds, percent):
    return _talent_rank(
        spell_id, 'Improved Sweeping Strikes',
        [_spellmod(AuraType.ADD_FLAT_MODIFIER, SpellModOp.DURATION, seconds * 1000 - 1), _carrier(percent - 1)],
        _ICON_FAN_OF_KNIVES,
        f'warrior-rework S2 A2 (D24, doc "Improved Sweeping Strikes"): rank {rank}. eff0 ADD_FLAT_MODIFIER DURATION '
        f'+{seconds} s (bp {seconds * 1000 - 1}) on Sweeping Strikes (EffectSpellClassMaskA_2 = d1 0x100000), eff1 '
        f'DUMMY carrier {percent} (the extra-hit percent [tune], read by the Sweeping copy).',
        _rank_raw(f'Increases the duration of your Sweeping Strikes by {seconds} sec and increases the damage of its '
                  f'extra hits from 40% to {percent}%.', EffectSpellClassMaskA_2=_SWEEPING_D1),
    )


improved_sweeping_strikes_204529 = _improved_sweeping_strikes(204529, 1, 2, 45)
improved_sweeping_strikes_204530 = _improved_sweeping_strikes(204530, 2, 4, 50)


# Exploiter 204531-204532 (D15, R7): eff0 DUMMY carrier 15 / 30 (per-stack percent). ProcTypeMask / ProcChance 0: no
# proc row (the debuff is applied by Warrior::OnSpellCast on an Execute cast).
def _exploiter(spell_id, rank, percent):
    return _talent_rank(
        spell_id, 'Exploiter',
        [_carrier(percent - 1)],
        _ICON_EXPLOITER,
        f'warrior-rework S2 A2 (D15, R7): rank {rank} carrier, {percent}% per stack (bp {percent - 1}), read by '
        f'Warrior::GetExploiterMultiplier. ProcTypeMask / ProcChance 0 and no spell_proc row: the debuff 204504 is '
        f'applied by the Execute-cast dispatcher branch.',
        _rank_raw(f'Your Execute makes the target take {percent}% more damage from your next Mortal Strike, stacking '
                  f'up to 2 times. Lasts 20 sec.', ProcTypeMask=0, ProcChance=0),
    )


exploiter_204531 = _exploiter(204531, 1, 15)
exploiter_204532 = _exploiter(204532, 2, 30)


# Battlelord 204533-204534 (D24): eff0 ADD_PCT_MODIFIER DAMAGE +10 / 20% on Overpower (EffectSpellClassMaskA_1 = d0
# 0x4).
def _battlelord(spell_id, percent):
    return _talent_rank(
        spell_id, 'Battlelord',
        [_spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.DAMAGE, percent - 1)],
        _ICON_OVERPOWER,
        f'warrior-rework S2 A2 (D24, doc "Battlelord"): +{percent}%. eff0 ADD_PCT_MODIFIER DAMAGE bp {percent - 1} on '
        f'Overpower (EffectSpellClassMaskA_1 = d0 0x4).',
        _rank_raw(f'Increases the damage of your Overpower by {percent}%.', EffectSpellClassMaskA_1=_OVERPOWER_D0),
    )


battlelord_204533 = _battlelord(204533, 10)
battlelord_204534 = _battlelord(204534, 20)


# Momentum 204535-204536 (D24): eff0 PROC_TRIGGER_SPELL -> 204498, DBC ProcChance 15 / 30, ProcTypeMask 0x10; the
# spell_proc rows (flags 0x10, family 4, Overpower d0 0x4, CAST phase) are at the end of the file.
def _momentum(spell_id, rank, chance):
    return _talent_rank(
        spell_id, 'Momentum',
        [_self_aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=204498)],
        _ICON_MOMENTUM,
        f'warrior-rework S2 A2 (D24, doc "Momentum"): rank {rank}. eff0 PROC_TRIGGER_SPELL -> 204498, DBC ProcChance '
        f'{chance} [fixed], ProcTypeMask 0x10; spell_proc: flags 0x10, family 4, Overpower d0 0x4, CAST phase (rolls '
        f'once per Overpower cast; Proc Chance multiplies the chance).',
        _rank_raw(f'Your Overpower hits have a {chance}% chance to make your next Slam cost no rage and deal 30% more '
                  f'damage.', ProcTypeMask=0x10, ProcChance=chance),
    )


momentum_204535 = _momentum(204535, 1, 15)
momentum_204536 = _momentum(204536, 2, 30)

# Weight of the Earth 204537 (D8, R9): eff0 ADD_FLAT_MODIFIER RADIUS +8 yd (bp 7 + die 1) on the Heroic Leap landing
# (EffectSpellClassMaskA_3 = d2 0x1; the mod is applied after the radius cap, so 8 yd -> 16 yd), eff1 DUMMY marker. The
# rank MUST be SpellClassSet 4: a family-0 SpellMod would apply to every spell (0-verify B item 4).
weight_of_the_earth_204537 = _talent_rank(
    204537, 'Weight of the Earth',
    [_spellmod(AuraType.ADD_FLAT_MODIFIER, SpellModOp.RADIUS, 7), _carrier(0)],
    _ICON_HEROIC_LEAP,
    'warrior-rework S2 A2 (D8, R9, doc "Weight of the Earth"): eff0 ADD_FLAT_MODIFIER RADIUS +8 yd (bp 7) on the '
    'Heroic Leap landing (EffectSpellClassMaskA_3 = d2 0x1), eff1 DUMMY marker (the landing script reads it). '
    'SpellClassSet 4 (a family-0 SpellMod would hit every spell). 204545 is not needed.',
    _rank_raw('Doubles the radius of your Heroic Leap\'s landing from 8 to 16 yards, and enemies it strikes are '
              'afflicted by your Colossus Smash. The extra radius only strikes enemies already in combat.',
              EffectSpellClassMaskA_3=_masks.HEROIC_LEAP),
)


# Seismic Reverberation 204538-204539 (D19): eff0 DUMMY carrier 25 / 50.
def _seismic_reverberation(spell_id, rank, percent):
    return _talent_rank(
        spell_id, 'Seismic Reverberation',
        [_carrier(percent - 1)],
        _ICON_WHIRLWIND,
        f'warrior-rework S2 A2 (D19, doc "Seismic Reverberation"): rank {rank} carrier, the echo is {percent}% '
        f'(bp {percent - 1}), read by the 1680 script.',
        _rank_raw(f'If your Whirlwind strikes 3 or more enemies, it strikes them again 0.5 sec later for {percent}% '
                  f'of its damage.'),
    )


seismic_reverberation_204538 = _seismic_reverberation(204538, 1, 25)
seismic_reverberation_204539 = _seismic_reverberation(204539, 2, 50)

# Improved Rend rank 3, 204540 (D23): eff0 ADD_PCT_MODIFIER DOT +30% (bp 29, op 22: the op that scales the whole tick,
# not EFFECT1) on Rend (EffectSpellClassMaskA_1 = d0 0x20), eff1 ADD_FLAT_MODIFIER CRITICAL_CHANCE +10% (bp 9) on Rend
# (EffectSpellClassMaskB_1). Ranks 1-2 are A1's rows in warrior_trigger_spells.py.
improved_rend_204540 = _talent_rank(
    204540, 'Improved Rend',
    [_spellmod(AuraType.ADD_PCT_MODIFIER, SpellModOp.DOT, 29),
     _spellmod(AuraType.ADD_FLAT_MODIFIER, SpellModOp.CRITICAL_CHANCE, 9)],
    _ICON_REND,
    'warrior-rework S2 A2 (D23, doc "Improved Rend"): rank 3. eff0 ADD_PCT_MODIFIER DOT (22) +30% (bp 29) on Rend '
    '(EffectSpellClassMaskA_1 = d0 0x20), eff1 ADD_FLAT_MODIFIER CRITICAL_CHANCE +10% (bp 9) on Rend '
    '(EffectSpellClassMaskB_1 = d0 0x20).',
    _rank_raw('Increases the bleed damage done by your Rend by 30% and its critical strike chance by 10%.',
              subtext='Rank 3', EffectSpellClassMaskA_1=_REND_D0, EffectSpellClassMaskB_1=_REND_D0),
)


# Anger Management (D12): 12296 is rank 1 (a stock row, first-declared here), 204541 / 204542 are ranks 2 / 3. eff0
# PERIODIC_ENERGIZE (24) rage 2 / 4 / 6 every 3 s (bp 19 / 39 / 59 tenths; not aura 85: Player::Regenerate bypasses
# ModifyPower, is not combat gated and drops overflow), eff1 ADD_FLAT_MODIFIER ALL_EFFECTS +5 / 10 / 15 on Charge
# (EffectSpellClassMaskB_1 = d0 0x1; the in-combat Charge rage reads it through ApplyEffectModifiers, B6), eff2 DUMMY
# marker (the capstone). SpellClassSet 4. The combat gate is spell_warr_anger_management's OnEffectPeriodic.
def _anger_management_effects(rage_bp, charge_bp):
    return [_self_aura(AuraType.PERIODIC_ENERGIZE, base_points=rage_bp, misc_value=_POWER_RAGE_MISC, amplitude=3000),
            _spellmod(AuraType.ADD_FLAT_MODIFIER, SpellModOp.ALL_EFFECTS, charge_bp),
            _carrier(0)]


_ANGER_CAPSTONE = 'Your Charge also reduces your damage taken by 30% for 4 sec.'

anger_management_12296 = spell(
    id=12296,
    name='Anger Management',
    school=School.NORMAL,
    attributes=_TALENT_RANK_ATTRIBUTES,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=_anger_management_effects(19, 49),
    spell_icon_id=_ICON_ANGER_MANAGEMENT,
    notes='warrior-rework S2 A2 (D12, doc "Anger Management"): stock 12296 (MOD_POWER_REGEN) first-declared and '
          'rewritten: rank 1. eff0 PERIODIC_ENERGIZE rage 2 every 3000 ms (bp 19 tenths), eff1 ADD_FLAT_MODIFIER '
          'ALL_EFFECTS +5 on Charge (EffectSpellClassMaskB_1 = d0 0x1), eff2 DUMMY capstone marker, SpellClassSet 4, '
          'capstone clause via _desc (grey on ranks 1-2). Tick gated to combat by spell_warr_anger_management.',
    raw_overrides=_rank_raw(
        _desc('Generates 2 rage every 3 sec and increases the rage generated by your Charge by 5.', _ANGER_CAPSTONE,
              last=False),
        EffectSpellClassMaskB_1=_CHARGE_D0, Name_Lang_Mask=16712190, NameSubtext_Lang_Mask=16712188,
        Description_Lang_Mask=16712190, AuraDescription_Lang_Mask=16712188),
)

anger_management_204541 = _talent_rank(
    204541, 'Anger Management',
    _anger_management_effects(39, 99),
    _ICON_ANGER_MANAGEMENT,
    'warrior-rework S2 A2 (D12, doc "Anger Management"): rank 2. eff0 PERIODIC_ENERGIZE rage 4 every 3000 ms (bp 39), '
    'eff1 ADD_FLAT_MODIFIER ALL_EFFECTS +10 on Charge (EffectSpellClassMaskB_1 = d0 0x1), eff2 DUMMY capstone marker.',
    _rank_raw(_desc('Generates 4 rage every 3 sec and increases the rage generated by your Charge by 10.',
                    _ANGER_CAPSTONE, last=False), EffectSpellClassMaskB_1=_CHARGE_D0),
)

anger_management_204542 = _talent_rank(
    204542, 'Anger Management',
    _anger_management_effects(59, 149),
    _ICON_ANGER_MANAGEMENT,
    'warrior-rework S2 A2 (D12, doc "Anger Management"): rank 3 (the capstone rank). eff0 PERIODIC_ENERGIZE rage 6 '
    'every 3000 ms (bp 59), eff1 ADD_FLAT_MODIFIER ALL_EFFECTS +15 on Charge (EffectSpellClassMaskB_1 = d0 0x1), eff2 '
    'DUMMY capstone marker (spell_warr_charge_rework casts 204508 on every Charge when this rank is known).',
    _rank_raw(_desc('Generates 6 rage every 3 sec and increases the rage generated by your Charge by 15.',
                    _ANGER_CAPSTONE, last=True), EffectSpellClassMaskB_1=_CHARGE_D0),
)

# Juggernaut rank 2, 204543 (D13): eff0 empty (the stock "Charge in combat" aura is baseline since W0b), eff1 DUMMY
# carrier 100 (the chance), eff2 ADD_FLAT_MODIFIER COOLDOWN -4 s on Heroic Leap (EffectSpellClassMaskC_3 = d2 0x1; bp
# -4001 + die 1 = -4000 ms). ProcTypeMask / ProcChance 0: the grants are scripted (Charge / the landing).
juggernaut_204543 = _talent_rank(
    204543, 'Juggernaut',
    [None, _carrier(99), _spellmod(AuraType.ADD_FLAT_MODIFIER, SpellModOp.COOLDOWN, -4001)],
    _ICON_JUGGERNAUT,
    'warrior-rework S2 A2 (D13, doc "Juggernaut"): rank 2. eff0 empty, eff1 DUMMY carrier 100 (the grant chance), '
    'eff2 ADD_FLAT_MODIFIER COOLDOWN -4000 ms (bp -4001) on Heroic Leap (EffectSpellClassMaskC_3 = d2 0x1). '
    'ProcTypeMask / ProcChance 0; remove_spell_proc(64976) at the end of the file.',
    _rank_raw('Following a Heroic Leap, or a Charge from more than 20 yards away or at a target above 90% health, you '
              'have a 100% chance for your next Slam to critically hit and your next Mortal Strike to apply Rend. '
              'Reduces the cooldown of your Heroic Leap by 4 sec.', ProcTypeMask=0, ProcChance=0,
              EffectSpellClassMaskC_3=_masks.HEROIC_LEAP),
)

# Endless Rage rank 2, 204544 (D11): eff0 aura 35 MOD_INCREASE_ENERGY misc 1 (rage) +20 maximum rage (bp 199 tenths +
# die 1 = 200), eff1 DUMMY capstone marker. Capstone clause via _desc (grey on rank 1 = A1's 29623, plain here).
endless_rage_204544 = _talent_rank(
    204544, 'Endless Rage',
    [_self_aura(_AURA_MOD_INCREASE_ENERGY, base_points=199, misc_value=_POWER_RAGE_MISC), _carrier(0)],
    _ICON_ENDLESS_RAGE,
    'warrior-rework S2 A2 (D11, doc "Endless Rage"): rank 2 (the capstone rank). eff0 aura 35 MOD_INCREASE_ENERGY misc '
    '1 (rage) +200 tenths (bp 199 + die 1), eff1 DUMMY capstone marker read by Warrior::OnRageOverflow. Capstone '
    'clause via _desc (plain on the last rank).',
    _rank_raw(_desc('Increases your maximum rage by 20.',
                    'Rage you would gain above your maximum instead increases the damage of your next Mortal Strike '
                    'by 1% per point, up to 20%, for 20 sec.', last=True)),
)


# =====================================================================================================================
# First declarations of the stock rank rows S2 edits  -- D9, D12, D14, D17, D20-D22, D24 (pull_dsl.py text, renamed)
# =====================================================================================================================
# Each is the live stock row re-declared field for field except the S2 change named in its notes. Variable names are
# the brief's (the header constant is the name minus its trailing _<id>, upper-cased).
def _two_handed_weapon_specialization(spell_id, rank, percent):
    return spell(
        id=spell_id,
        name='Two-Handed Weapon Specialization',
        school=School.NORMAL,
        attributes=262352,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=0.0,
        effects=[
            Effect(type=EffectType.APPLY_AURA, base_points=percent - 1, implicit_target_a=_TARGET_UNIT_CASTER,
                   apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=1),
            Effect(type=EffectType.APPLY_AURA, base_points=percent - 1, implicit_target_a=_TARGET_UNIT_CASTER,
                   apply_aura=AuraType.MOD_WEAPON_CRIT_PERCENT),
        ],
        spell_icon_id=366,
        notes=f'warrior-rework S2 A2 (D24, R20, doc "Two-Handed Weapon Specialization"): stock row first-declared, '
              f'rank {rank}. eff0 aura 79 misc 1 {percent}% (was 2/4/6), new eff1 aura 52 MOD_WEAPON_CRIT_PERCENT '
              f'+{percent}% '
              f'(reaches Rend ticks, 0-verify item 9). Same two-hander gate (class 2 / subclass 354), SpellClassSet 0 '
              f'(no SpellMod).',
        raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1, 'DurationIndex': 0, 'RangeIndex': 1,
                       'EquippedItemClass': _WEAPON_CLASS, 'EquippedItemSubclass': _TWO_HANDED_SUBCLASSES,
                       'SpellPriority': 50, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': f'Rank {rank}',
                       'NameSubtext_Lang_Mask': 16712190,
                       'Description_Lang_enUS': f'Increases the physical damage you deal with two-handed melee '
                                                f'weapons by {percent}% and your critical strike chance by {percent}%.',
                       'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188,
                       'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
    )


two_handed_weapon_specialization_12163 = _two_handed_weapon_specialization(12163, 1, 1)
two_handed_weapon_specialization_12711 = _two_handed_weapon_specialization(12711, 2, 2)
two_handed_weapon_specialization_12712 = _two_handed_weapon_specialization(12712, 3, 3)


# Trauma 46854 / 46855 (D21): eff0 becomes a DUMMY carrier 15 / 30% (read by Warrior::ApplyDeepWounds), no proc
# (ProcTypeMask / ProcChance 0, remove_spell_proc(-46854) below), stale masks and the dead effect-2 raws cleared. The
# group bleed debuffs 46856 / 46857 stay as inert stock rows.
def _trauma(spell_id, rank, percent):
    return spell(
        id=spell_id,
        name='Trauma',
        school=School.NORMAL,
        attributes=464,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=0.0,
        effects=[_carrier(percent - 1)],
        spell_icon_id=2968,
        notes=f'warrior-rework S2 A2 (D21, doc "Trauma"): stock row first-declared, rank {rank}. eff0 was '
              f'PROC_TRIGGER_SPELL -> {46856 + rank - 1}; now a DUMMY carrier {percent}% (bp {percent - 1}) that '
              f'Warrior::ApplyDeepWounds reads. ProcTypeMask / ProcChance 0, spell_proc -46854 removed, stale masks '
              f'(0x2010, 0x8) cleared.',
        raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 0, 'ProcChance': 0, 'SpellLevel': 1, 'DurationIndex': 0,
                       'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190,
                       'NameSubtext_Lang_enUS': f'Rank {rank}', 'NameSubtext_Lang_Mask': 16712190,
                       'Description_Lang_enUS': f'Increases the damage of your Deep Wounds by {percent}%.',
                       'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188,
                       'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
    )


trauma_46854 = _trauma(46854, 1, 15)
trauma_46855 = _trauma(46855, 2, 30)


# Strength of Arms 46865 / 46866 (D14): eff0 Strength +2 / 4% kept (bp 1 / 3), eff1 Stamina +1 / 2% (bp 0 / 1), eff2
# MOD_EXPERTISE -> PROC_TRIGGER_SPELL -> the buff 204501 / 204502; DBC ProcTypeMask 0x10, ProcChance 100; the spell_proc
# row is -46865 (end of the file). Stale masks (0x40000001 / 0x2010 / 0x8) cleared.
def _strength_of_arms(spell_id, rank, strength_bp, stamina_bp, buff, strength, stamina, damage):
    return spell(
        id=spell_id,
        name='Strength of Arms',
        school=School.NORMAL,
        attributes=464,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=0.0,
        effects=[
            Effect(type=EffectType.APPLY_AURA, base_points=strength_bp, implicit_target_a=_TARGET_UNIT_CASTER,
                   apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE),
            Effect(type=EffectType.APPLY_AURA, base_points=stamina_bp, implicit_target_a=_TARGET_UNIT_CASTER,
                   apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, misc_value=2),
            Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_UNIT_CASTER,
                   apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=buff),
        ],
        spell_icon_id=_ICON_STRENGTH_OF_ARMS,
        notes=f'warrior-rework S2 A2 (D14, doc "Strength of Arms"): stock row first-declared, rank {rank}. eff0 '
              f'Strength +{strength}% kept, eff1 Stamina +{stamina}% (was {strength}%), eff2 MOD_EXPERTISE -> '
              f'PROC_TRIGGER_SPELL -> {buff} (the {damage}% per stack Mortal Strike buff). DBC ProcTypeMask 0x10, '
              f'ProcChance 100; spell_proc -46865 (flags 0x10, family 4, Overpower | Slam | Execute, CAST phase) at '
              f'the end of the file. Stale masks cleared.',
        raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 0x10, 'ProcChance': 100, 'SpellLevel': 1,
                       'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50,
                       'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': f'Rank {rank}',
                       'NameSubtext_Lang_Mask': 16712190,
                       'Description_Lang_enUS': f'Increases your total Strength by {strength}% and Stamina by '
                                                f'{stamina}%. After using Overpower, Slam or Execute, your next Mortal '
                                                f'Strike deals {damage}% more damage, stacking up to 2 times.',
                       'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188,
                       'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
    )


strength_of_arms_46865 = _strength_of_arms(46865, 1, 1, 0, 204501, 2, 1, 5)
strength_of_arms_46866 = _strength_of_arms(46866, 2, 3, 1, 204502, 4, 2, 10)


# Sudden Death 29723 / 29725 (rank 2) / 29724 (rank 3) (D9, R15): SpellClassSet 0 and icon 1989 and eff0 aura 42 and
# eff1 bp 2 / 6 / 9 stay (stock Execute's rage-kept lookup, spell_warrior.cpp, needs exactly that). eff0 bp 4 / 9 / 14
# (the tooltip's $s1 = 5 / 10 / 15), DBC ProcChance 5 / 10 / 15, ProcTypeMask 0x14. Stale masks cleared. The trigger
# 52437 stays a valid id; spell_warr_sudden_death_reset prevents the default action.
def _sudden_death(spell_id, rank, chance, rage_kept):
    return spell(
        id=spell_id,
        name='Sudden Death',
        school=School.NORMAL,
        attributes=464,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=0.0,
        effects=[
            Effect(type=EffectType.APPLY_AURA, base_points=chance - 1, implicit_target_a=_TARGET_UNIT_CASTER,
                   apply_aura=AuraType.PROC_TRIGGER_SPELL, misc_value=11, trigger_spell=52437),
        ],
        spell_icon_id=1989,
        notes=f'warrior-rework S2 A2 (D9, R15, doc "Sudden Death"): stock row first-declared, rank {rank}. Stays '
              f'SpellClassSet 0, icon 1989, eff0 aura 42, eff1 bp {rage_kept - 1} (Execute\'s rage-kept lookup reads '
              f'Effects[1].CalcValue() = {rage_kept}). eff0 bp {chance - 1} (tooltip $s1 = {chance}), DBC ProcChance '
              f'{chance}, ProcTypeMask 0x14; spell_proc -29723 (flags 0x14, family 4, CAST phase, Cooldown 6000) at '
              f'the end of the file. Stale masks cleared.',
        raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 0x14, 'ProcChance': chance, 'SpellLevel': 1,
                       'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'EffectDieSides_2': 1,
                       'EffectBasePoints_2': rage_kept - 1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190,
                       'NameSubtext_Lang_enUS': f'Rank {rank}', 'NameSubtext_Lang_Mask': 16712190,
                       'Description_Lang_enUS': f'Your melee hits have a {chance}% chance to reset the cooldown of '
                                                f'your Mortal Strike. This cannot occur more than once every 6 sec. '
                                                f'Mortal Strike cannot trigger this effect. You keep at least '
                                                f'{rage_kept} rage after using Execute.',
                       'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188,
                       'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
    )


sudden_death_29723 = _sudden_death(29723, 1, 5, 3)
sudden_death_29725 = _sudden_death(29725, 2, 10, 7)
sudden_death_29724 = _sudden_death(29724, 3, 15, 10)


# Wrecking Crew 46867 / 56611 / 56612 (D22): eff0 PROC_TRIGGER_SPELL retargeted from the stock Enrage 57518-57520 to the
# new buffs 204505-204507 (not an Enrage). The stock spell_proc -46867 row (crit hit, HIT phase) and the DBC
# ProcTypeMask 0x14 / ProcChance 100 are kept; stale masks and the dead effect-2 raws cleared.
def _wrecking_crew(spell_id, rank, buff, percent):
    return spell(
        id=spell_id,
        name='Wrecking Crew',
        school=School.NORMAL,
        attributes=464,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=0.0,
        effects=[
            Effect(type=EffectType.APPLY_AURA, base_points=-1, implicit_target_a=_TARGET_UNIT_CASTER,
                   apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=buff),
        ],
        spell_icon_id=_ICON_WRECKING_CREW,
        notes=f'warrior-rework S2 A2 (D22, doc "Wrecking Crew"): stock row first-declared, rank {rank}. eff0 trigger '
              f'{57518 + rank - 1} -> {buff} ({percent}% on the named Arms abilities, 12 s, not an Enrage). Stock '
              f'spell_proc -46867 row (crit, HIT phase) and DBC ProcTypeMask 0x14 / ProcChance 100 kept. Stale masks '
              f'cleared.',
        raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 20, 'ProcChance': 100, 'SpellLevel': 1,
                       'DurationIndex': 0, 'RangeIndex': 1, 'EquippedItemClass': -1, 'SpellPriority': 50,
                       'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': f'Rank {rank}',
                       'NameSubtext_Lang_Mask': 16712190,
                       'Description_Lang_enUS': f'Your main-hand and melee ability critical strikes increase the '
                                                f'damage of your Overpower, Mortal Strike, Execute, Rend, Thunder '
                                                f'Clap, Heroic Leap, Colossus Smash and Bladestorm by {percent}% for '
                                                f'12 sec.',
                       'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188,
                       'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
    )


wrecking_crew_46867 = _wrecking_crew(46867, 1, 204505, 5)
wrecking_crew_56611 = _wrecking_crew(56611, 2, 204506, 10)
wrecking_crew_56612 = _wrecking_crew(56612, 3, 204507, 15)


# Weapon Specialization 12281 / 12812 / 12813 (D17, R16): the stock Sword Specialization ranks (3 of 5; 12814 / 12815
# drop out of the talent) become DUMMY markers carrying the merged doc tooltip. The proc, its equipment gate and
# AttributesEx3 0x80000 are gone (ProcTypeMask / ProcChance 0, EquippedItemClass -1 / subclass 0) so the marker is
# always present for the equip hook's rank lookup; remove_spell_proc(-12281) below. The 16459 extra-attack spell is
# never used again.
def _weapon_specialization(spell_id, rank, axe, mace, sword):
    return spell(
        id=spell_id,
        name='Weapon Specialization',
        school=School.NORMAL,
        attributes=464,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=0.0,
        effects=[_carrier(0)],
        spell_icon_id=_ICON_SWORD_SPEC,
        notes=f'warrior-rework S2 A2 (D17, R16, doc "Weapon Specialization"): stock Sword Specialization rank {rank} '
              f'first-declared and renamed. eff0 was PROC_TRIGGER_SPELL -> 16459, now a DUMMY marker; ProcTypeMask / '
              f'ProcChance 0, EquippedItemClass -1 / subclass 0, AttributesEx3 0x80000 dropped, spell_proc -12281 '
              f'removed. The bonus is the hidden passive WarriorPlayerScript keeps for the main-hand weapon '
              f'(204512-204520).',
        raw_overrides={'CastingTimeIndex': 1, 'ProcTypeMask': 0, 'ProcChance': 0, 'SpellLevel': 1, 'DurationIndex': 0,
                       'RangeIndex': 1, 'EquippedItemClass': -1, 'EquippedItemSubclass': 0, 'SpellPriority': 50,
                       'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': f'Rank {rank}',
                       'NameSubtext_Lang_Mask': 16712190,
                       'Description_Lang_enUS': f'Grants a bonus based on your equipped melee weapon. Axes and '
                                                f'polearms: critical strike chance and critical strike damage '
                                                f'increased by {axe}%. Maces: armor penetration increased by {mace}%. '
                                                f'Swords: your melee hits have a {sword}% chance to grant an extra '
                                                f'attack on the same target for 120% weapon damage, no more than once '
                                                f'every 3 sec.',
                       'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188,
                       'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
    )


weapon_specialization_12281 = _weapon_specialization(12281, 1, 2, 5, 3)
weapon_specialization_12812 = _weapon_specialization(12812, 2, 4, 10, 6)
weapon_specialization_12813 = _weapon_specialization(12813, 3, 6, 15, 10)


# Blood Frenzy debuffs 30069 / 30070 (D20): the stock rows, unchanged, first-declared only so the C++ has header
# constants (SPELL_BLOOD_FRENZY_DEBUFF_R1 / _R2). MOD_DAMAGE_PERCENT_TAKEN misc 1 +2 / 4% (bp 1 / 3), 21 s
# (DurationIndex 86; review finding 8: finite, so a caster who logs out or changes map cannot leave it permanent;
# Rend's and Deep Wounds' AuraScripts re-cast it to refresh while one of the warrior's bleeds is up). R8: no
# spell_group(1108, 30070): 30070 is rank 2 of 30069's chain, which is already in group 1108.
def _blood_frenzy_debuff(spell_id, rank, base_points):
    return spell(
        id=spell_id,
        name='Blood Frenzy',
        school=School.NORMAL,
        attributes=256,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=_SCRIPT_CAST_RANGE,
        duration_ms=21000,
        effects=[
            Effect(type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                   apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=1),
        ],
        spell_icon_id=2005,
        notes=f'warrior-rework S2 A2 (D20): stock Blood Frenzy debuff rank {rank} first-declared, unchanged '
              f'(+{base_points + 1}% physical damage taken, 21 s, DurationIndex 86). The Rend / Deep Wounds scripts '
              f'apply and remove it (R8: group 1108 already covers rank 2).',
        raw_overrides={'AttributesEx2': 4, 'CastingTimeIndex': 1, 'ProcChance': 101, 'SpellLevel': 1,
                       'EquippedItemClass': -1, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190,
                       'NameSubtext_Lang_enUS': f'Rank {rank}', 'NameSubtext_Lang_Mask': 16712190,
                       'Description_Lang_Mask': 16712188,
                       'AuraDescription_Lang_enUS': 'Taking more physical damage.',
                       'AuraDescription_Lang_Mask': 16712190, 'EffectChainAmplitude_1': 1.0,
                       'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
    )


blood_frenzy_debuff_r1_30069 = _blood_frenzy_debuff(30069, 1, 1)
blood_frenzy_debuff_r2_30070 = _blood_frenzy_debuff(30070, 2, 3)


# =====================================================================================================================
# S2 script bindings, proc-row removals and proc rows on stock / legacy ids (D1, D5, D9, D17, D18, D24; brief section 2)
# =====================================================================================================================
# New fork classes (registered in spell_warrior_arms.cpp, AddSC_warrior_arms_spell_scripts). Chains (-id) bind every
# rank through spell_ranks.
scripted_by(12294, 'spell_warr_mortal_strike_arms')           # Mortal Strike: AfterHit chain (CS cut, Taste, ...)
scripted_by(772, 'spell_warr_rend_arms')                      # Rend: Blood Frenzy upkeep (AfterEffectApply / Remove)
scripted_by(-12834, 'spell_warr_deep_wounds_rework')          # Deep Wounds ranks: OnEffectProc -> ApplyDeepWounds
scripted_by(204496, 'spell_warr_deep_wounds_holder')          # holder: casts the tick 204497 each period + Blood Frenzy
scripted_by(-29723, 'spell_warr_sudden_death_reset')          # Sudden Death ranks: CheckProc + Mortal Strike reset
scripted_by(204401, 'spell_warr_heroic_leap_landing')         # landing: ring filter, Colossus Smash, Juggernaut grant
scripted_by(204495, 'spell_warr_bladestorm_whirl')            # Bladestorm whirl: once-per-whirl proc roll
scripted_by(1680, 'spell_warr_whirlwind_seismic')             # Whirlwind: Seismic Reverberation sums + delayed echo
scripted_by(-12296, 'spell_warr_anger_management')            # Anger Management ranks: periodic energize combat gate
scripted_by(204514, 'spell_warr_weapon_spec_sword')           # Weapon Specialization sword passives (ranks 1-3)
scripted_by(204517, 'spell_warr_weapon_spec_sword')
scripted_by(204520, 'spell_warr_weapon_spec_sword')
scripted_by(204493, 'spell_warr_sweeping_strikes_rework')     # Sweeping Strikes (Arms): puts Blade Flurry 13877 on 30 s

# Stock classes S2 retires from these ids (the stock classes stay registered where other ids still use them).
unbind_script(-12834, 'spell_warr_deep_wounds_aura')          # D5: replaced by spell_warr_deep_wounds_rework
unbind_script(-12162, 'spell_warr_deep_wounds')               # D5: the stock holder chain is no longer used
unbind_script(-29723, 'spell_war_sudden_death_aura')          # D9: the free-Execute buff is gone
unbind_script(-29723, 'spell_warr_extra_proc')                # D9: T10 4P row only; the -46913 row (Bloodsurge) stays
unbind_script(-29834, 'spell_warr_second_wind')               # D18: the stun / immobilize rage + heal is gone

# spell_proc rows the rewritten ranks no longer use (their ProcTypeMask / ProcChance are zeroed in the rank rows, so no
# default entry is built either).
remove_spell_proc(-12281)                                     # Sword Specialization -> a Weapon Specialization marker
remove_spell_proc(-29834)                                     # Second Wind: a DUMMY carrier now (D18)
remove_spell_proc(-46854)                                     # Trauma: a DUMMY carrier now (D21)
remove_spell_proc(64976)                                      # Juggernaut: scripted grants now (D13)
remove_spell_proc(-12289)                                     # Improved Hamstring (retired talent): no proc left

# spell_proc rows. Chance 0 means "use the rank's DBC ProcChance" (SpellMgr.cpp LoadSpellProcs).
# Sudden Death (D9, R10): melee swings and every non-triggered warrior-family melee cast, ONE roll per swing / cast, a
# 6 s ICD shared by both. SpellFamilyName 4 with an empty mask (a family-0 row would roll on every melee cast incl.
# Charge and Heroic Leap, 0-verify B item 5); CAST phase (1) so an ability rolls once at cast, swings skip the
# phase test. No spell_type_mask: it filters nothing at the CAST phase (the event's type mask is ALL); the CheckProc
# scripts (spell_warr_sudden_death_reset) gate the roll on direct-damage casts.
procs_on(-29723, proc_flags=0x14, family_name=_SPELLFAMILY_WARRIOR, spell_phase_mask=0x1, cooldown_ms=6000)
# Taste for Blood (D6): the stock row with Cooldown 5800 -> 0 (Rend ticks have no Spell*, so they roll per tick; spread
# Rends roll too). Family 4, Rend d0 0x20, HIT phase (2) kept; the DBC ProcTypeMask 0x40000 (done periodic) still
# drives it.
procs_on(-56636, proc_flags=0, family_name=_SPELLFAMILY_WARRIOR, family_mask=(_REND_D0, 0, 0), spell_phase_mask=0x2,
         cooldown_ms=0)
# Strength of Arms (D14): after Overpower, Slam or Execute 5308 (d0 0x4 | 0x200000 | 0x20000000), CAST phase, 100%.
procs_on(-46865, proc_flags=0x10, family_name=_SPELLFAMILY_WARRIOR,
         family_mask=(_OVERPOWER_D0 | _SLAM_D0 | _EXECUTE_D0, 0, 0), spell_phase_mask=0x1, chance=100)
# Weapon Specialization sword passives (D17): swings and melee casts, CAST phase, 3 s ICD, the rank's DBC chance 3/6/10.
procs_on(204514, proc_flags=0x14, spell_phase_mask=0x1, cooldown_ms=3000)
procs_on(204517, proc_flags=0x14, spell_phase_mask=0x1, cooldown_ms=3000)
procs_on(204520, proc_flags=0x14, spell_phase_mask=0x1, cooldown_ms=3000)
# Momentum (D24): an Overpower cast (d0 0x4), CAST phase (rolls once per cast), the rank's DBC chance 15/30.
procs_on(204535, proc_flags=0x10, family_name=_SPELLFAMILY_WARRIOR, family_mask=(_OVERPOWER_D0, 0, 0),
         spell_phase_mask=0x1)
procs_on(204536, proc_flags=0x10, family_name=_SPELLFAMILY_WARRIOR, family_mask=(_OVERPOWER_D0, 0, 0),
         spell_phase_mask=0x1)
