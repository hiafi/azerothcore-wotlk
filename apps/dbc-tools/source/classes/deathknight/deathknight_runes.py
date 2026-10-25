"""
Death Knight - DK0b rune rows: Runeforging as six self-aura runes (Fallen Crusader 53344 and Razorice 53343 rewritten in
place, Exsanguination / Boiling Blight / Apocalypse / Unending Thirst new), their proc buffs and helpers, and the Frost
Vulnerability row Razorice stacks. Pulled stock rows are listed in DK0b-WP-BRIEF.md; ids 203040-203051 are this file's.

Source of truth: docs/reworks/death-knight-shared-rework.md ("Runeforging" and the six rune entries: tooltips and aura
texts verbatim, proc buff texts number-free), DK0b-HANDOFF.md known-hard items 1 and 2, DK0b-WP-BRIEF.md corrections 1-3
and 8 (they win over the handoff), DK0b-0VERIFY.md items 2, 6, 8, 9, 10 and 16, and the passed P0 spike rune shape
(p0-spike-ref/deathknight_p0_spike.py _rune(): 203685 / 203686).

The rune frame (every one of the six): a self APPLY_AURA, permanent, visible (not passive, no DO_NOT_DISPLAY 0x80, no
TRADESKILL 0x20), `Attributes` exactly 0x10000000 (NOT_IN_COMBAT_ONLY_PEACEFUL: swap out of combat only),
`AttributesEx3` 0x100000 (ALLOW_AURA_WHILE_DEAD: survives death), instant (CastingTimeIndex 1), self range, no item
requirement, no ENCHANT_ITEM, GCD 133 / 1500, no cost, SpellClassSet 15 with no family bits (FB 4.3), SpellLevel =
BaseLevel = the learn level (6 / 20 / 20 / 20 / 30 / 40), one at a time through spell_group 1271 rule 1. The rune's
single proc effect is PROC_TRIGGER_SPELL (effect 0); the C++ half (spell_dk_rune_rework and friends) writes the glow,
guards the proc (actor, once per cast, dual-wield half) and, for Razorice / Apocalypse, replaces the default trigger.

Ids: 53344 Fallen Crusader and 53343 Razorice keep their stock ids (the stock Unholy Strength 53365 / Frost
Vulnerability 51714 too); 203040 Rune of Exsanguination, 203041 its HoT, 203042 Rune of Boiling Blight, 203043 its burst,
203044 Rune of the Apocalypse, 203045 Conquest (Haste), 203046 War (Critical Strike), 203047 Famine (Versatility),
203048 Death (Mastery), 203049 Rune of Unending Thirst, 203050 its Mastery buff, 203051 Razor Frost (Razorice's damage).
SkillLineAbility 30730-30733 (the four new runes); spell_group 1271. 53344 / 53343's own SkillLineAbility rows (18126 /
18108, 18124) and the trainer rows are deathknight_trainers.py's.
"""

from lib.dsl import AuraType, Effect, EffectType, PowerType, RANGE_SELF, School
from lib.dsl.registry import (
    const, procs_on, scripted_by, skill_line_ability, spell, spell_group, spell_group_rule, unbind_script,
)

from . import _masks as m

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_ATTR0_NOT_IN_COMBAT_ONLY_PEACEFUL = 0x10000000
_ATTR0_DO_NOT_SHEATH = 0x40000
_ATTR2_IGNORE_LOS = 0x4
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_ALWAYS_HIT = 0x40000
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000
_SPELLFAMILY_DEATHKNIGHT = 15

# ---- Aura types not in the DSL enum (src/server/game/Spells/Auras/SpellAuraDefines.h) ----
_AURA_OBS_MOD_HEALTH = 20                       # % of max health per tick
_AURA_MOD_DAMAGE_DONE_VERSUS = 168              # misc = creature type mask
_AURA_MOD_CRIT_PCT = 290
_AURA_MOD_CUSTOM_STAT_PCT = 306                 # misc = 1 << CR_*; stored amount = percent - 1

# ---- Misc values / targets ----
_CREATURE_TYPE_UNDEAD_MASK = 0x20               # 1 << (CREATURE_TYPE_UNDEAD 6 - 1)
_CR_MASTERY = 1 << 20
_CR_VERSATILITY = 1 << 21
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6

# ---- spell_proc masks (src/server/game/Spells/SpellMgr.h) ----
_PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x4
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x10
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x10000
_PROC_FLAG_DONE_PERIODIC = 0x40000
_MELEE_HIT_PROC_FLAGS = _PROC_FLAG_DONE_MELEE_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_CRITICAL = 0x2

# ---- Learn levels (shared doc learn-level table) ----
_LEVEL_FALLEN_CRUSADER = 6
_LEVEL_RAZORICE = 20
_LEVEL_EXSANGUINATION = 20
_LEVEL_BOILING_BLIGHT = 20
_LEVEL_APOCALYPSE = 30
_LEVEL_UNENDING_THIRST = 40

# Script numbers (D8 tier 3: not tooltip numbers, not potency). Glow ids are the visual enchant ids P0-RESULTS chose
# (3847 Fallen Crusader, 3370 Razorice); 0 = no glow (DK0b U1: the four new runes launch without one, adding one later is
# this one line plus a rebuild).
RUNE_GLOW_FALLEN_CRUSADER = const(
    'RUNE_GLOW_FALLEN_CRUSADER', 3847, 'Weapon glow (SpellItemEnchantment visual id) while Rune of the Fallen Crusader '
    'is the active rune; 0 = none [tune].', cpp_type='uint16',
)
RUNE_GLOW_RAZORICE = const(
    'RUNE_GLOW_RAZORICE', 3370, 'Weapon glow (SpellItemEnchantment visual id) while Rune of Razorice is the active rune; '
    '0 = none [tune].', cpp_type='uint16',
)
RUNE_GLOW_EXSANGUINATION = const(
    'RUNE_GLOW_EXSANGUINATION', 0, 'Weapon glow while Rune of Exsanguination is active; 0 = none (DK0b U1) [tune].',
    cpp_type='uint16',
)
RUNE_GLOW_BOILING_BLIGHT = const(
    'RUNE_GLOW_BOILING_BLIGHT', 0, 'Weapon glow while Rune of Boiling Blight is active; 0 = none (DK0b U1) [tune].',
    cpp_type='uint16',
)
RUNE_GLOW_APOCALYPSE = const(
    'RUNE_GLOW_APOCALYPSE', 0, 'Weapon glow while Rune of the Apocalypse is active; 0 = none (DK0b U1) [tune].',
    cpp_type='uint16',
)
RUNE_GLOW_UNENDING_THIRST = const(
    'RUNE_GLOW_UNENDING_THIRST', 0, 'Weapon glow while Rune of Unending Thirst is active; 0 = none (DK0b U1) [tune].',
    cpp_type='uint16',
)
RAZORICE_DAMAGE_PCT = const(
    'RAZORICE_DAMAGE_PCT', 2, 'Percent of the triggering hit\'s own damage Razor Frost 203051 deals as Frost damage '
    '(stock 2% of weapon damage; per hit, never per weapon) [tune].',
)


def _rune(spell_id, name, level, icon, effects, tooltip, aura_text, notes, school=School.NORMAL):
    """One rune self-aura frame (known-hard 1, brief correction 2). `effects` is the rune's effect list (effect 0 =
    the PROC_TRIGGER_SPELL the script hooks). Nothing stale from the stock enchant row survives: `Attributes` is exactly
    0x10000000, no item class / focus / targets / interrupt flags / enchant effect, self range, instant."""
    return spell(
        id=spell_id,
        name=name,
        school=school,
        attributes=_ATTR0_NOT_IN_COMBAT_ONLY_PEACEFUL,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        power_type=PowerType.MANA,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=effects,
        spell_icon_id=icon,
        notes=notes,
        raw_overrides={
            'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT,
            'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD,
            'EquippedItemClass': -1,
            'CastingTimeIndex': 1,
            'RuneCostID': 0,
            'BaseLevel': level,
            'SpellLevel': level,
            'StartRecoveryCategory': 133,
            'StartRecoveryTime': 1500,
            'Description_Lang_enUS': tooltip,
            'AuraDescription_Lang_enUS': aura_text,
        },
    )


def _proc_trigger(trigger_spell_id, *extra_effects):
    """The rune's effect list: effect 0 PROC_TRIGGER_SPELL (self aura target), then any rune-owned aura effects."""
    return [
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=trigger_spell_id,
               implicit_target_a=_TARGET_UNIT_CASTER),
        *extra_effects,
    ]


# =====================================================================================================================
# Rune of the Fallen Crusader (stock 53344, trained @6) and its proc buff Unholy Strength (stock 53365)
# =====================================================================================================================

# Shared doc "Rune of the Fallen Crusader": 2 procs per minute (rolled as a per-hit chance of 2 x weapon speed / 60,
# half per hand when dual wielding: spell_dk_rune_rework's RuneProcAllowed), Strength +15%, 3% of maximum health over
# 15 sec, +5% damage to Undead on the rune's own aura. eff0 stays the stock proc trigger shape (but self-cast 53365);
# eff1 is aura 168 MOD_DAMAGE_DONE_VERSUS, misc 0x20 (Undead), stored 4 = +5% [tune]. The enchant effect, the item
# class, the focus requirement and the 5 s cast are gone (brief correction 2).
rune_of_the_fallen_crusader_53344 = _rune(
    53344, 'Rune of the Fallen Crusader', _LEVEL_FALLEN_CRUSADER, 204,
    _proc_trigger(
        53365,
        Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=_TARGET_UNIT_CASTER,
               apply_aura=_AURA_MOD_DAMAGE_DONE_VERSUS, misc_value=_CREATURE_TYPE_UNDEAD_MASK),
    ),
    'Your melee attacks have a chance to increase your Strength by 15% and heal you for 3% of your maximum health over '
    '15 sec. Your attacks deal additional damage to Undead.',
    'Your melee attacks may increase your Strength and heal you. Your attacks deal more damage to Undead.',
    'pulled from the stock Spell.dbc, rewritten in place (dk-rework DK0b, shared doc "Rune of the Fallen Crusader", '
    'brief correction 2): a self-aura rune, not an ENCHANT_ITEM. eff0 PROC_TRIGGER_SPELL -> 53365 Unholy Strength '
    '(self), eff1 aura 168 MOD_DAMAGE_DONE_VERSUS misc 0x20 (Undead) stored 4 = +5%. Attributes 0x10000000 only (stock '
    '0x101A0: TRADESKILL 0x20, DO_NOT_DISPLAY 0x80, DO_NOT_LOG 0x100, NOT_SHAPESHIFTED 0x10000 all gone), Ex 0x400 / Ex2 '
    '0x2000 / Targets 0x10 / InterruptFlags 15 / RequiresSpellFocus 1552 / item class 2 / visual 11759 / 5 s cast '
    '(CastingTimeIndex 6) cleared, AttributesEx3 0x100000 (survives death), instant, self range, GCD 133 / 1500, '
    'SpellLevel = BaseLevel 6 (was 40 / 0). Proc row: ppm 2 on melee auto attacks and melee-class spells, phase HIT; '
    'the per-hit scaling, the dual-wield half and the once-per-cast guard are spell_dk_rune_rework (DoCheckProc). '
    'Group 1271 (one rune at a time). Stock SkillLineAbility 18126 (776) is moved to 770 by deathknight_trainers.py.',
)
procs_on(rune_of_the_fallen_crusader_53344, proc_flags=_MELEE_HIT_PROC_FLAGS, spell_phase_mask=_PROC_SPELL_PHASE_HIT,
         ppm=2.0)
scripted_by(rune_of_the_fallen_crusader_53344, 'spell_dk_rune_rework')

# Stock 53365 (stock-only before this pull). eff0 aura 137 MOD_TOTAL_STAT_PERCENTAGE +15% Strength is unchanged; eff1 was
# the instant HEAL_PCT effect 136 (3% at once), now APPLY_AURA 20 OBS_MOD_HEALTH, stored 0 = 1% of maximum health, every
# 5 sec for the stock 15 sec = 3 ticks = the doc's "3% of your maximum health over 15 sec" (brief correction 3). The heal
# is a percent of health, not a potency number (the doc wins): potency_excluded. The stock crit re-roll script
# (spell_dk_rune_of_the_fallen_crusader) is unbound; the rune's own script replaces it.
unholy_strength_53365 = spell(
    id=53365,
    name='Unholy Strength',
    school=1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    duration_ms=15000,
    effects=[
        Effect(type=6, base_points=14, implicit_target_a=1, apply_aura=137),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=_TARGET_UNIT_CASTER,
               apply_aura=_AURA_OBS_MOD_HEALTH, amplitude=5000,
               potency_excluded='doc-fixed 1% of maximum health per tick (3% over 15 sec): a percent of health, not a '
                                'damage / heal potency number (shared doc "Rune of the Fallen Crusader")'),
    ],
    spell_icon_id=239,
    notes='pulled from existing data (stock-only); dk-rework DK0b (brief correction 3): eff1 effect 136 HEAL_PCT (instant '
          '3%) -> APPLY_AURA aura 20 OBS_MOD_HEALTH stored 0 (1%) amplitude 5000 over the stock 15 s (3 ticks), '
          'potency_excluded; eff0 aura 137 +15% Strength kept. The stale "Affixes your rune weapon" tooltip is replaced; '
          'the aura text is the doc\'s proc buff text. The stock crit re-roll binding is declared removed below.',
    raw_overrides={'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 55, 'CumulativeAura': 1,
                   'EquippedItemClass': -1, 'SpellVisualID_1': 4345, 'SpellPriority': 50, 'Name_Lang_Mask': 16712190,
                   'NameSubtext_Lang_Mask': 16712172,
                   'Description_Lang_enUS': 'Increases your total Strength by $s1% and heals you for $s2% of your '
                                            'maximum health every 5 sec for $d.',
                   'Description_Lang_Mask': 16712190,
                   'AuraDescription_Lang_enUS': 'Strength increased. Healing over time.',
                   'AuraDescription_Lang_Mask': 16712190,
                   'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)
unbind_script(53365, 'spell_dk_rune_of_the_fallen_crusader')

# =====================================================================================================================
# Rune of Razorice (stock 53343, trained @20), Razor Frost (203051) and Frost Vulnerability (stock 51714)
# =====================================================================================================================

# Shared doc "Rune of Razorice": every melee hit deals extra Frost damage (2% of that hit, RAZORICE_DAMAGE_PCT) and adds a
# Frost Vulnerability stack (2% each, up to 5) to the target. Chance 100: the doc's "each melee hit adds a stack, melee
# abilities one stack per cast" (RuneProcAllowed's once-per-cast guard). One PROC_TRIGGER_SPELL effect; the default
# trigger is prevented by spell_dk_rune_of_the_razorice_rework, which casts 203051 (bp = the pct of the hit) and 51714
# on the target, both triggered, caster -> target (bug 1051). trigger_spell here is only the declared default.
rune_of_razorice_53343 = _rune(
    53343, 'Rune of Razorice', _LEVEL_RAZORICE, 119,
    _proc_trigger(203051),
    'Your melee attacks deal additional Frost damage and cause the target to take 2% more Frost damage from you, '
    'stacking up to 5 times.',
    'Your melee attacks deal extra Frost damage and make the target more vulnerable to your Frost damage.',
    'pulled from the stock Spell.dbc, rewritten in place (dk-rework DK0b, shared doc "Rune of Razorice", brief '
    'correction 2): same self-aura frame as 53344 (Attributes 0x10000000, Ex3 0x100000, instant, self, no enchant '
    'effect / item class / focus / targets, SpellLevel = BaseLevel 20, was 40 / 0). eff0 PROC_TRIGGER_SPELL -> 203051 '
    '(declared default only: spell_dk_rune_of_razorice_rework prevents it and casts 203051 + 51714 itself). Proc row: '
    'chance 100 on melee auto attacks and melee-class spells, phase HIT; once per cast through RuneProcAllowed. Stock '
    'SkillLineAbility 18108 (Frost 771, class 32, acquire 0) and 18124 (stock 776, acquire 1) both exist; the client '
    'filed it under 776, so deathknight_trainers.py moves 18124 to 771 with acquire 0.',
)
procs_on(rune_of_razorice_53343, proc_flags=_MELEE_HIT_PROC_FLAGS, spell_phase_mask=_PROC_SPELL_PHASE_HIT, chance=100.0)
scripted_by(rune_of_razorice_53343, 'spell_dk_rune_rework', 'spell_dk_rune_of_razorice_rework')

# Razorice's damage (U12): Frost SCHOOL_DAMAGE on the hit target, bp supplied by the script as RAZORICE_DAMAGE_PCT % of the
# triggering hit's own DamageInfo damage (never the main hand's weapon: an aura-triggered stock Razor Frost 50401 always
# reads the main hand, A19), so the effect is potency_excluded. Shape of stock 50401 (ALWAYS_HIT, CANT_CRIT,
# SUPPRESS_CASTER_PROCS so the extra damage can neither miss, crit nor re-proc) but a SCHOOL_DAMAGE on a magic-class row
# (Versatility / damage-done multipliers apply). Family 15 Frost with no bit: 51714's reader mask never matches it, so
# it is not amplified by its own stacks.
razor_frost_203051 = spell(
    id=203051,
    name='Razor Frost',
    school=School.FROST,
    attributes=_ATTR0_DO_NOT_SHEATH,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               potency_excluded='amount is RAZORICE_DAMAGE_PCT % of the triggering hit, set by '
                                'spell_dk_rune_of_razorice_rework (SPELLVALUE_BASE_POINT0), not CalcValue'),
    ],
    spell_icon_id=2727,
    notes='dk-rework DK0b (shared doc "Rune of Razorice", U12): Razorice\'s Frost damage helper. SCHOOL_DAMAGE on the '
          'target, base points set per hit by the rune script (RAZORICE_DAMAGE_PCT % of the hit), potency_excluded. '
          'ALWAYS_HIT + SUPPRESS_CASTER_PROCS (AttributesEx3 0x50000), CANT_CRIT (AttributesEx2) like stock 50401; '
          'DefenseType 1; no facing check and IGNORE_LOS (a triggered cast still runs both); family 15 with no '
          'bit (not read by 51714). No GCD, no cost, 50000 yd range (script cast at '
          'another unit, bug 554).',
    raw_overrides={
        'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 0,
        'AttributesEx2': _ATTR2_CANT_CRIT | _ATTR2_IGNORE_LOS,
        'AttributesEx3': _ATTR3_ALWAYS_HIT | _ATTR3_SUPPRESS_CASTER_PROCS,
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellLevel': 0, 'RuneCostID': 0,
        'Description_Lang_enUS': 'Your rune causes extra Frost damage.',
    },
)

# Stock 51714 pulled from npc.csv:1497 (brief correction 1 / U12 changed): eff0 aura 271 (MOD_DAMAGE_FROM_CASTER, Frost
# misc 16) +1% per stack x 5, now read through the Frost-school union mask _masks.FROST_VULN_READ instead of the stock
# 0x402 / 0x4048007 set (a zero mask would match every family-15 spell of every school, DK0b-0VERIFY item 8). The stale
# EffectBasePoints_2 / EffectDieSides_2 keys (Effect_2 is empty) are gone; the stock SpellClassMask_1 d0 b21 carrier bit
# stays. The doc's debuff text.
frost_vulnerability_51714 = spell(
    id=51714,
    name='Frost Vulnerability',
    school=16,
    attributes=262144,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    duration_ms=20000,
    effects=[
        Effect(type=6, base_points=1, implicit_target_a=6, apply_aura=271, misc_value=16),
    ],
    spell_icon_id=2727,
    notes='pulled from existing data; dk-rework DK0b (brief correction 1): eff0 reader mask = _masks.FROST_VULN_READ '
          '(union of the Frost-school DK bits) so only the Death Knight\'s own Frost damage is amplified, not a zero '
          'mask (all family-15 spells, every school); stale EffectBasePoints_2 / EffectDieSides_2 dropped; tooltip and '
          'aura text from the shared doc.',
    raw_overrides={'AttributesEx': 136, 'AttributesEx3': 128, 'CastingTimeIndex': 1, 'ProcChance': 101,
                   'SpellLevel': 1, 'CumulativeAura': 5, 'EquippedItemClass': -1,
                   'EffectSpellClassMaskA_1': m.FROST_VULN_READ[0], 'EffectSpellClassMaskA_2': m.FROST_VULN_READ[1],
                   'EffectSpellClassMaskA_3': m.FROST_VULN_READ[2],
                   'SpellVisualID_1': 8721, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188,
                   'Description_Lang_enUS': 'The target takes $s1% more Frost damage from the Death Knight. Stacks up '
                                            'to 5 times.',
                   'Description_Lang_Mask': 16712190,
                   'AuraDescription_Lang_enUS': 'Taking more Frost damage from the Death Knight.',
                   'AuraDescription_Lang_Mask': 16712190,
                   'SpellClassSet': 15, 'SpellClassMask_1': 2097152, 'DefenseType': 1,
                   'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0},
)

# =====================================================================================================================
# Rune of Exsanguination (203040, trained @20) and its heal over time (203041)
# =====================================================================================================================

# Shared doc "Rune of Exsanguination": 15% chance per melee hit (once per cast), 1 s internal cooldown, a HoT of 10 potency
# every 2 sec for 6 sec that stacks up to 3 times (CumulativeAura 3, each application adds a stack and refreshes). The
# HoT is ap_potency 10 heal_periodic, can crit (DefenseType 1: a DmgClass NONE periodic heal never crits, 0-verify item 7)
# and its ticks are hasted at application (server default).
rune_of_exsanguination_203040 = _rune(
    203040, 'Rune of Exsanguination', _LEVEL_EXSANGUINATION, 3878,
    _proc_trigger(203041),
    'Your melee attacks have a 15% chance to heal you over 6 sec. Stacks up to 3 times.',
    'Your melee attacks may heal you over time.',
    'dk-rework DK0b (shared doc "Rune of Exsanguination", known-hard 2): Blood\'s signature rune, level 20. eff0 '
    'PROC_TRIGGER_SPELL -> 203041 (self). Proc row: chance 15, cooldown 1000 ms, melee auto attacks and melee-class '
    'spells, phase HIT; once per cast via RuneProcAllowed. Icon 3878 spell_fire_rune is a placeholder (V stage). No '
    'glow at launch (RUNE_GLOW_EXSANGUINATION 0). SkillLineAbility 30730 on the Blood line 770.',
)
procs_on(rune_of_exsanguination_203040, proc_flags=_MELEE_HIT_PROC_FLAGS, spell_phase_mask=_PROC_SPELL_PHASE_HIT,
         chance=15.0, cooldown_ms=1000)
scripted_by(rune_of_exsanguination_203040, 'spell_dk_rune_rework')

exsanguination_203041 = spell(
    id=203041,
    name='Exsanguination',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, ap_potency=10.0, potency_kind='heal_periodic',
               implicit_target_a=_TARGET_UNIT_CASTER, apply_aura=AuraType.PERIODIC_HEAL, amplitude=2000),
    ],
    spell_icon_id=3006,
    notes='dk-rework DK0b (shared doc "Rune of Exsanguination"): the proc buff. PERIODIC_HEAL every 2 s for 6 s '
          '(3 ticks), ap_potency 10 heal_periodic, SpellLevel 20, CumulativeAura 3. DefenseType 1 so the HoT can crit '
          'and Versatility applies (DmgClass NONE periodic heals never crit); family 15; S1a adds the '
          'self-heal bit d2 b15 (DK_SELF_HEAL, SpellClassMask_3). Icon 3006 is a placeholder (V stage).',
    raw_overrides={
        'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'CumulativeAura': 3,
        'SpellClassMask_3': m.DK_SELF_HEAL,  # S1a: the spell's own family bit d2 b15, the Voracious capstone self-heal group
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellLevel': _LEVEL_EXSANGUINATION, 'RuneCostID': 0,
        'Description_Lang_enUS': 'Heals you for {pot1} every 2 sec for $d. Stacks up to 3 times.',
        'AuraDescription_Lang_enUS': 'Healing over time.',
    },
)

# =====================================================================================================================
# Rune of Boiling Blight (203042, trained @20) and its burst (203043)
# =====================================================================================================================

# Shared doc "Rune of Boiling Blight": each periodic tick of the Death Knight's diseases (Blood Plague / Frost Fever, the
# _masks.DISEASES proc mask, spell type DAMAGE) has a 10% chance to burst for 200 potency Shadow damage on the ticked
# target; 1 s internal cooldown per Death Knight (all targets). The burst is ap_potency 200 direct, class bit d2 b11
# (_masks.ROT_DAMAGE, Runic Focus / Rage of Rivendare read it), SUPPRESS_CASTER_PROCS (rolls no procs).
rune_of_boiling_blight_203042 = _rune(
    203042, 'Rune of Boiling Blight', _LEVEL_BOILING_BLIGHT, 4068,
    _proc_trigger(203043),
    'The periodic damage of your diseases has a 10% chance to burst for Shadow damage.',
    'The periodic damage of your diseases may burst for Shadow damage.',
    'dk-rework DK0b (shared doc "Rune of Boiling Blight", known-hard 2): Unholy\'s signature rune, level 20. eff0 '
    'PROC_TRIGGER_SPELL -> 203043 on the proc target (the diseased enemy). Proc row: DONE_PERIODIC, spell type DAMAGE, '
    'family 15 mask _masks.DISEASES (d1 b25 / b26), chance 10, cooldown 1000 ms, phase HIT; the actor-only guard is '
    'RuneProcAllowed. Icon 4068 spell_shadow_rune is a placeholder (V stage). No glow. SkillLineAbility 30731 on the '
    'Unholy line 772.',
)
procs_on(rune_of_boiling_blight_203042, proc_flags=_PROC_FLAG_DONE_PERIODIC, family_name=_SPELLFAMILY_DEATHKNIGHT,
         family_mask=m.DISEASES, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=_PROC_SPELL_PHASE_HIT,
         chance=10.0, cooldown_ms=1000)
scripted_by(rune_of_boiling_blight_203042, 'spell_dk_rune_rework')

boiling_blight_203043 = spell(
    id=203043,
    name='Boiling Blight',
    school=School.SHADOW,
    attributes=_ATTR0_DO_NOT_SHEATH,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=50000.0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=200.0, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=4068,
    notes='dk-rework DK0b (shared doc "Rune of Boiling Blight"): the burst. Shadow SCHOOL_DAMAGE on the target, '
          'ap_potency 200 direct T 1500, SpellLevel 20, DefenseType 1 (magic: crits at spell crit chance, Runic Focus '
          'doubles it), family 15 with d2 b11 only (_masks.ROT_DAMAGE, the N4 Rot damage group), AttributesEx3 0x50000 (ALWAYS_HIT + no caster procs) '
          'SUPPRESS_CASTER_PROCS (rolls no procs), no facing check and IGNORE_LOS (ticks land on targets beside, '
          'behind or out of sight of the DK; DK0b review M1). No GCD, no cost, 50000 yd (script/proc cast at another unit, bug '
          '554). Mastery / Rage of Rivendare are S3\'s.',
    raw_overrides={
        'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'FacingCasterFlags': 0,
        'AttributesEx2': _ATTR2_IGNORE_LOS, 'AttributesEx3': _ATTR3_ALWAYS_HIT | _ATTR3_SUPPRESS_CASTER_PROCS,
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellClassMask_3': m.ROT_DAMAGE,
        'SpellLevel': _LEVEL_BOILING_BLIGHT, 'RuneCostID': 0,
        'Description_Lang_enUS': 'Bursts for {pot1} Shadow damage.',
    },
)

# =====================================================================================================================
# Rune of the Apocalypse (203044, trained @30) and the four Horsemen blessings (203045-203048)
# =====================================================================================================================

# Shared doc "Rune of the Apocalypse": 3 procs per minute (per-hit chance scaled by weapon speed, half per hand when dual
# wielding), 10 s internal cooldown, one of the four Horsemen at random (spell_dk_rune_of_the_apocalypse casts one of
# 203045-203048 on the owner), each +5 percentage points for 12 s (stored 4 = +5). User ruling 2026-10-24: War (Critical
# Strike), Famine (Versatility), Death (Mastery), Conquest (Haste). trigger_spell 203045 is the declared default only.
rune_of_the_apocalypse_203044 = _rune(
    203044, 'Rune of the Apocalypse', _LEVEL_APOCALYPSE, 3924,
    _proc_trigger(203045),
    'Your melee attacks have a chance to call upon one of the Four Horsemen, granting you Haste, Versatility, Critical '
    'Strike or Mastery for a short time.',
    'Your melee attacks may call upon one of the Four Horsemen.',
    'dk-rework DK0b (shared doc "Rune of the Apocalypse", known-hard 2): level 30. eff0 PROC_TRIGGER_SPELL -> 203045 '
    '(declared default only: spell_dk_rune_of_the_apocalypse prevents it and casts one of 203045-203048 at random on '
    'the owner). Proc row: ppm 3, cooldown 10000 ms, melee auto attacks and melee-class spells, phase HIT; DW half and '
    'once-per-cast via RuneProcAllowed. Icon 3924 spell_holy_rune is a placeholder (V stage). No glow. '
    'SkillLineAbility 30732 on the Blood line 770.',
)
procs_on(rune_of_the_apocalypse_203044, proc_flags=_MELEE_HIT_PROC_FLAGS, spell_phase_mask=_PROC_SPELL_PHASE_HIT,
         ppm=3.0, cooldown_ms=10000)
scripted_by(rune_of_the_apocalypse_203044, 'spell_dk_rune_rework', 'spell_dk_rune_of_the_apocalypse')


def _blessing(spell_id, name, icon, effect, description, aura_text, notes):
    return spell(
        id=spell_id,
        name=name,
        school=School.NORMAL,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        power_type=PowerType.MANA,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=RANGE_SELF,
        duration_ms=12000,
        effects=[effect],
        spell_icon_id=icon,
        notes=notes,
        raw_overrides={
            'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'SpellLevel': 0,
            'Description_Lang_enUS': description, 'AuraDescription_Lang_enUS': aura_text,
        },
    )


conquest_203045 = _blessing(
    203045, 'Conquest', 1651,
    Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=_TARGET_UNIT_CASTER,
           apply_aura=AuraType.HASTE_ALL),
    'Your Haste is increased by $s1% for $d.', 'Haste increased.',
    'dk-rework DK0b (shared doc "Rune of the Apocalypse"): Horseman of Conquest (Haste). Aura 193 HASTE_ALL stored 4 = '
    '+5% (cast + melee + ranged haste), 12 s, family 0. Icon 1651 is a placeholder (V stage).',
)
war_203046 = _blessing(
    203046, 'War', 3841,
    Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=_TARGET_UNIT_CASTER,
           apply_aura=_AURA_MOD_CRIT_PCT),
    'Your critical strike chance is increased by $s1% for $d.', 'Critical strike chance increased.',
    'dk-rework DK0b (shared doc "Rune of the Apocalypse"): Horseman of War (Critical Strike). Aura 290 MOD_CRIT_PCT '
    'stored 4 = +5 points, 12 s, family 0. Icon 3841 is a placeholder (V stage).',
)
famine_203047 = _blessing(
    203047, 'Famine', 3201,
    Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=_TARGET_UNIT_CASTER,
           apply_aura=_AURA_MOD_CUSTOM_STAT_PCT, misc_value=_CR_VERSATILITY),
    'Your Versatility is increased by $s1% for $d.', 'Versatility increased.',
    'dk-rework DK0b (shared doc "Rune of the Apocalypse"): Horseman of Famine (Versatility). Aura 306 '
    'MOD_CUSTOM_STAT_PCT misc 1 << 21, stored 4 = +5, 12 s, family 0. Icon 3201 is a placeholder (V stage).',
)
death_203048 = _blessing(
    203048, 'Death', 2519,
    Effect(type=EffectType.APPLY_AURA, base_points=4, implicit_target_a=_TARGET_UNIT_CASTER,
           apply_aura=_AURA_MOD_CUSTOM_STAT_PCT, misc_value=_CR_MASTERY),
    'Your Mastery is increased by $s1% for $d.', 'Mastery increased.',
    'dk-rework DK0b (shared doc "Rune of the Apocalypse"): Horseman of Death (Mastery). Aura 306 '
    'MOD_CUSTOM_STAT_PCT misc 1 << 20, stored 4 = +5, 12 s, family 0. Icon 2519 is a placeholder (V stage).',
)

# =====================================================================================================================
# Rune of Unending Thirst (203049, trained @40) and its Mastery buff (203050)
# =====================================================================================================================

# Shared doc "Rune of Unending Thirst": 20% chance on any critical strike by the Death Knight (direct melee and magic
# abilities, auto attacks, periodic crits; hit mask CRITICAL), 30 s internal cooldown, +8% Mastery for 10 s (refresh, no
# stack). The killing-blow clause (always, bypasses the cooldown) is the PlayerScript hook (OnRuneKillingBlow) casting
# 203050 triggered. spell_dk_rune_rework guards the proc (actor, once per cast for direct abilities).
rune_of_unending_thirst_203049 = _rune(
    203049, 'Rune of Unending Thirst', _LEVEL_UNENDING_THIRST, 3923,
    _proc_trigger(203050),
    'Your critical strikes have a 20% chance, and your killing blows always, grant you Mastery for 10 sec.',
    'Your critical strikes and killing blows may grant you Mastery.',
    'dk-rework DK0b (shared doc "Rune of Unending Thirst", known-hard 2): level 40. eff0 PROC_TRIGGER_SPELL -> 203050 '
    '(self). Proc row: melee auto attacks, melee-class spells, negative magic-class spells and DONE_PERIODIC, hit mask '
    'CRITICAL only, chance 20, cooldown 30000 ms, phase HIT. The killing-blow clause is deathknight_hooks.cpp '
    '(OnRuneKillingBlow). Icon 3923 spell_nature_rune is a placeholder (V stage). No glow. SkillLineAbility 30733 on '
    'the Blood line 770.',
)
procs_on(rune_of_unending_thirst_203049,
         proc_flags=(_MELEE_HIT_PROC_FLAGS | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_PERIODIC),
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_CRITICAL, chance=20.0, cooldown_ms=30000)
scripted_by(rune_of_unending_thirst_203049, 'spell_dk_rune_rework')

unending_thirst_203050 = spell(
    id=203050,
    name='Unending Thirst',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=PowerType.MANA,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=7, implicit_target_a=_TARGET_UNIT_CASTER,
               apply_aura=_AURA_MOD_CUSTOM_STAT_PCT, misc_value=_CR_MASTERY),
    ],
    spell_icon_id=3011,
    notes='dk-rework DK0b (shared doc "Rune of Unending Thirst"): the proc buff. Aura 306 MOD_CUSTOM_STAT_PCT misc '
          '1 << 20 stored 7 = +8% Mastery [tune], 10 s, refreshes and does not stack, family 0. Icon 3011 is a '
          'placeholder (V stage).',
    raw_overrides={
        'CastingTimeIndex': 1, 'EquippedItemClass': -1, 'SpellLevel': 0,
        'Description_Lang_enUS': 'Your Mastery is increased by $s1% for $d.',
        'AuraDescription_Lang_enUS': 'Mastery increased.',
    },
)

# =====================================================================================================================
# One rune at a time, and the four new runes' spellbook rows
# =====================================================================================================================

# Group 1271 rule 1 (exclusive: a new rune replaces the active one). Casting is also out of combat only (Attributes
# 0x10000000). The shaman imbue / rogue poison exclusivity is a later Classless stage.
spell_group(
    1271, rune_of_the_fallen_crusader_53344, rune_of_razorice_53343, rune_of_exsanguination_203040,
    rune_of_boiling_blight_203042, rune_of_the_apocalypse_203044, rune_of_unending_thirst_203049,
)
spell_group_rule(1271, stack_rule=1, description='Death Knight runes')

# Spellbook tabs (U11): Exsanguination, Apocalypse and Unending Thirst on Blood 770, Boiling Blight on Unholy 772; all
# class 32, acquire 0 (trainer-taught, rows in deathknight_trainers.py). Fallen Crusader (override 18126 -> 770) and
# Razorice (stock 18108, Frost 771) are deathknight_trainers.py's.
skill_line_ability(id=30730, skill_line=770, spell_id=rune_of_exsanguination_203040.id, class_mask=32, acquire_method=0)
skill_line_ability(id=30731, skill_line=772, spell_id=rune_of_boiling_blight_203042.id, class_mask=32, acquire_method=0)
skill_line_ability(id=30732, skill_line=770, spell_id=rune_of_the_apocalypse_203044.id, class_mask=32, acquire_method=0)
skill_line_ability(id=30733, skill_line=770, spell_id=rune_of_unending_thirst_203049.id, class_mask=32,
                   acquire_method=0)
