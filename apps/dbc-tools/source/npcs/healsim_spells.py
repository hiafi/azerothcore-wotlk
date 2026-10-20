"""Healing sim damage spells - Sim Damage Pulse 202900 and Sim Pin Hit 202901 (healing-sim stage HS0).

Cast by the Sim Raid Boss (900015-900017, source/npcs/training_dummies.py) at one group member each, with the damage
passed as bp0 (`CastCustomSpell(spellId, SPELLVALUE_BASE_POINT0, amount, target, flags)`; the effect's DieSides is 1,
and SetSpellValue/CalcBaseValue turn bp0 into exactly `amount`). They have to be real spell hits (not a raw
DealDamage) so that damage-taken % auras, absorbs and the victim's "taken damage" procs all run, but nothing else
about the caster may leak into the number: that is what the attribute set below is for.

Ids 202900-202909 are this project's reservation inside the `spell` block (ids.yaml); 202902-202909 are spare.
Server-side only in intent: no client casts or renders these. dbc-tools has no server-only spell, so generate.py
still lists both rows in the Spell.dbc of patch-Z.mpq; nothing in the client ever references them.

Every bit below was checked against the core (src/server/shared/SharedDefines.h, src/server/game/Spells/):
  Attributes      0x00200000  SPELL_ATTR0_NO_ACTIVE_DEFENSE        cannot be dodged, parried or blocked
  AttributesEx    0x00000008  SPELL_ATTR1_NO_REDIRECTION           not attracted by a Grounding Totem style magnet
                  0x00000400  SPELL_ATTR1_NO_THREAT                no threat and no initial aggro (AtTargetAttacked
                                                                    gets canInitialAggro = false)
  AttributesEx2   0x00000004  SPELL_ATTR2_IGNORE_LINE_OF_SIGHT     triggered casts still run Spell::CheckCast's LoS
                  0x20000000  SPELL_ATTR2_CANT_CRIT                Unit::SpellDoneCritChance / SpellTakenCritChance
  AttributesEx3   0x00000200  SPELL_ATTR3_NOT_A_PROC               a TRIGGERED_FULL_MASK cast still triggers the
                                                                    victim's auras (SpellAuras.cpp, GetProcEffectMask)
                  0x00040000  SPELL_ATTR3_ALWAYS_HIT               no miss / dodge / parry / block / deflect / reflect
                                                                    roll (WorldObject::SpellHitResult)
                  0x20000000  SPELL_ATTR3_IGNORE_CASTER_MODIFIERS  SpellDamageBonusDone returns the bp0 amount as is,
                                                                    so the creature spell damage rate cannot change it
  AttributesEx4   0x00000001  SPELL_ATTR4_NO_CAST_LOG ("cannot be resisted")  Unit::CalcAbsorbResist skips the resist roll
  AttributesEx7   0x00000040  SPELL_ATTR7_DONT_CAUSE_SPELL_PUSHBACK  202901 only; Unit::DealDamage (Unit.cpp:1303)
Deliberately NOT set: SPELL_ATTR3_SUPPRESS_CASTER_PROCS (0x10000: it clears canEffectTrigger, so the victim's procs would
not fire), SPELL_ATTR4_IGNORE_DAMAGE_TAKEN_MODIFIERS (it would skip the damage-taken multipliers) and
SPELL_ATTR3_TREAT_AS_PERIODIC (it suppresses pushback). Armor never applies: the school is Arcane (magic), and
Unit::IsDamageReducedByArmor only reduces the physical school, so no SPELL_ATTR0_CU_IGNORE_ARMOR custom attr is needed.
DmgClass (DefenseType column) is MAGIC (1), so the victim's procs get PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG plus
PROC_FLAG_TAKEN_DAMAGE. SpellClassSet 0, so no class SpellMod can match; range index 13 (50000 yd) and the LoS
bit leave nothing to fail inside the sim layout; cast time index 1 (instant), no cooldown, cost or GCD, Speed 0
(the hit lands at once). EquippedItemClass -1 (0 would fail every triggered cast).
"""

from lib.dsl import Effect, EffectType, School
from lib.dsl.registry import spell

_NO_ACTIVE_DEFENSE = 0x00200000
_NO_REDIRECTION = 0x00000008
_NO_THREAT = 0x00000400
_IGNORE_LINE_OF_SIGHT = 0x00000004
_CANT_CRIT = 0x20000000
_NOT_A_PROC = 0x00000200
_ALWAYS_HIT = 0x00040000
_IGNORE_CASTER_MODIFIERS = 0x20000000
_NO_CAST_LOG = 0x00000001
_DONT_CAUSE_SPELL_PUSHBACK = 0x00000040


def _sim_hit(spell_id: int, name: str, notes: str, ex7: int):
    return spell(
        id=spell_id,
        name=name,
        school=School.ARCANE,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=50000.0,
        effects=[
            Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=6,
                   potency_excluded='healing sim: the damage is the caller\'s bp0 (CastCustomSpell), not a spell value'),
        ],
        notes=notes,
        raw_overrides={
            'Attributes': _NO_ACTIVE_DEFENSE,
            'AttributesEx': _NO_REDIRECTION | _NO_THREAT,
            'AttributesEx2': _IGNORE_LINE_OF_SIGHT | _CANT_CRIT,
            'AttributesEx3': _NOT_A_PROC | _ALWAYS_HIT | _IGNORE_CASTER_MODIFIERS,
            'AttributesEx4': _NO_CAST_LOG,
            'AttributesEx7': ex7,
            'CastingTimeIndex': 1,
            'DefenseType': 1,          # SPELL_DAMAGE_CLASS_MAGIC (the DBC "DmgClass" column)
            'EquippedItemClass': -1,
            'SpellClassSet': 0,
            'SpellLevel': 0,
        },
    )


# Drain mode: one hit per living draining target every DrainPulseMs; causes spell pushback like live raid damage.
sim_damage_pulse = _sim_hit(
    202900, 'Sim Damage Pulse',
    'Healing sim drain-mode hit (HS0). Boss-cast, bp0 = damage, always hits, never crits, no resist, no armor, no threat; '
    'damage-taken % auras and absorbs apply. Causes pushback.',
    ex7=0,
)

# Pin mode: the boss resets a pinned target to its pin percentage; must never push back the target's own casts.
sim_pin_hit = _sim_hit(
    202901, 'Sim Pin Hit',
    'Healing sim pin-mode hit (HS0). Same as Sim Damage Pulse plus SPELL_ATTR7_DONT_CAUSE_SPELL_PUSHBACK, so the artificial '
    'resets never delay the healer\'s own casts when the healer is a pinned target.',
    ex7=_DONT_CAUSE_SPELL_PUSHBACK,
)
