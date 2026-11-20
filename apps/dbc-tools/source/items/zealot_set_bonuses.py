"""
The Zealot's set bonuses (docs/dungeons/scarlet-monastery-rework.md ## Loot, "The Zealot's family: Martyrdom" and "3
piece bonuses", rulings 57 to 59; copied into dungeon-loot-vanilla.md "Zealot's set bonuses (approved 2026-11-19)"):
the one 2 piece role line, Zealot's Fervor, and one 3 piece martyr moment per archetype. Haunted is a chance and
Molten a count; Zealot's plays on health.

**Zealot's Fervor (2 piece).** A smooth slope on missing health: nothing at full health, the full value at 40% health
or below (the bonus is the full value times (missing health) / 60% of maximum health, capped at the full value). One
spell per role, the role's numbers on its DUMMY effects (the tooltip's $s1 / $s2), read by ZealotSetUnitHooks
(zealot_set_bonuses.cpp) at each hit or heal:

  damage   212100  up to 6% more damage, on the wearer's own health       Plate Strength, Mail Agility, Leather
                                                                          Agility, Cloth Intellect
  healing  212101  up to 8% more healing, on the healed target's health   Cloth Spirit
  tank     212102  up to 6% less damage taken, on the wearer's own health Plate Tank, Leather Tank
  hybrid   212103  both lines of damage (own health) and healing (target) Plate Intellect, Mail Intellect, Leather
                                                                          Spirit

The damage line counts the wearer's own auto attacks, spells and damage-over-time ticks (not a pet's); the healing
line the wearer's direct heals and heal-over-time ticks (not absorbs); the tank line every hit and tick the wearer
takes. Two Zealot's sets never reach 2 pieces at once (three slots), so a Fervor never stacks with another.

**The 3 piece trigger** (ruling 59): fires once when a hit takes its owner from 35% health or more to below 35%
(alive; the Haunted Deathless shape). The four "an ally you heal" sets (Plate Intellect, Mail Intellect, Leather Spirit,
Cloth Spirit) also fire when the wearer's heal lands on any target at or below 35% health at that moment, before its
amount is added (designer ruling C4, 2026-11-20): every target a heal hits counts, the wearer included (a self-heal
counts, Blood Offering too), every target of a multi-target heal is checked, direct heals and heal-over-time ticks
alike; Cloth Spirit fires on that alone. Internal cooldown 60 sec: the spell_proc row's
Cooldown, which starts only when CheckProc passes (a proc cooldown is not a spell cooldown, so Cooldown Haste never
touches it, Systems section 4). Every row is 100%: the trigger is a health line, not a chance. spell_zealot_martyr
(bound to all ten) checks the trigger and casts the set's payout.

Values scale with health or potency, never a flat number [tune]. Damage is potency (docs/potency-system.md, T 1.5 s
for a proc payout, 2 s for a tick); percents of health or of a hit are `potency_excluded`. Payouts suppress caster
procs (SPELL_ATTR3_SUPPRESS_CASTER_PROCS). Their two areas are short (Kindled Vigil's burn 5 yd, Arcanist's Ward's
detonation 10 yd), so they hit every enemy in reach, in combat or not (designer ruling B8, 2026-11-20: only a long
reach of about 30 yd keeps an in-combat filter); Kennel Call's and Extract Confession's single target (40 yd) stays an
enemy already in combat. No look was checked in game.

Ids: the `zealot_set` reservation 212100-212299 (source/ids.yaml): 212100-212103 the Fervor lines, then ten per set in
the hub table's order: +0 the 3 piece, +1 and up its payouts; 212210-212299 spare. Scripts:
modules/mod-dungeon-bosses/src/DungeonSets/zealot_set_bonuses.cpp (ids and numbers mirrored in ZealotSetLogic.h;
lib/test_zealot_set.py checks they agree).

  Plate Strength, Battlegear of the Scarlet Champion (1004)
  212110  Unbroken Zeal (3)     you: 212111.
  212111  Unbroken Zeal         10 s: Strength +5%, and each melee ability hit heals you for 30% of its damage
                                (spell_zealot_unbroken_zeal: 212112 for the amount).
  212112  Unbroken Zeal         the heal (percent of the hit, set by the script).
  Plate Tank, Bulwark of the Last Stand (1005)
  212120  Hold the Line (3)     you: 212121.
  212121  Hold the Line         you and party members within 10 yd: damage taken -10%, 8 s.
  Plate Intellect, Vigil of the Fallen Champion (1006)
  212130  Kindled Vigil (3)     you or a target you heal: 212131 on them.
  212131  Kindled Vigil         6 s: heals 5% of maximum health every 2 s (15% in all); every 2 s the wearer's 212132
                                burns enemies within 5 yd of them (spell_zealot_kindled_vigil).
  212132  Kindled Vigil         Holy, spell power potency 35, every enemy within 5 yd of the vigil's owner.
  Mail Agility, Houndmaster's Harness (1007)
  212140  Kennel Call (3)       you: 212141 and two Scarlet tracking hounds (300894) for 12 s.
  212141  Kennel Call           12 s: damage taken -10%; every 2 s each hound bites the wearer's target
                                (spell_zealot_kennel_call: 212142, or 212143 when ranged attack power is higher).
  212142  Kennel Call           a bite: Physical, attack power potency 30.
  212143  Kennel Call           the same off ranged attack power.
  Mail Intellect, Curator's Regalia (1008)
  212150  Last Page (3)         you or a target you heal: 212151 on you.
  212151  Last Page             10 s, 3 charges: casting speed +50%; each spell with a cast time spends a charge
                                (spell_zealot_last_page).
  Leather Agility, Interrogator's Garb (1009)
  212160  Extract Confession (3) you: 212161 on your target (else the enemy that hit you).
  212161  Extract Confession    8 s, per caster: it deals 15% less damage to you; your finishing moves (and their
                                ticks) against it deal 10% more and heal you for 25% of their damage
                                (ZealotSetUnitHooks: 212162 for the amount).
  212162  Extract Confession    the heal (percent of the finisher's damage, set by the script).
  Leather Tank, Ironspine's Bones (1010)
  212170  Bone Cage (3)         you: 212171.
  212171  Bone Cage             8 s: damage taken -20%; each melee or ranged hit taken strikes the attacker with
                                212172 (PROC_TRIGGER_SPELL, spell data only).
  212172  Bone Cage             Shadow, attack power potency 15.
  Leather Spirit, Gardener's Vestments (1011)
  212180  Hallowed Thorns (3)   you or a target you heal: 212181 on them.
  212181  Hallowed Thorns       10 s: damage taken -10%; each melee or ranged hit taken strikes the attacker with the
                                wearer's 212182 (spell_zealot_hallowed_thorns: the wearer's spell power).
  212182  Hallowed Thorns       Holy, spell power potency 15.
  Cloth Intellect, Regalia of the Arcanist (1012)
  212190  Arcanist's Ward (3)   you: 212191.
  212191  Arcanist's Ward       8 s: absorbs 15% of maximum health (spell_zealot_arcanists_ward); when it breaks or
                                ends (not on death) 212192 detonates.
  212192  Arcanist's Ward       Arcane, spell power potency 150, every enemy within 10 yd of the wearer.
  Cloth Spirit, Vestments of the High Inquisitor (1013)
  212200  Blood Offering (3)    a target you heal (you included): 212201 on them.
  212201  Blood Offering        heals the target for 20% of their maximum health; the wearer loses 10% of their current
                                health (spell_zealot_blood_offering).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import pot_text, procs_on, scripted_by, spell

_TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}

_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_UNIT_CASTER_AREA_PARTY = 20
_TARGET_UNIT_TARGET_ALLY = 21

_ATTR0_PASSIVE = 0x00000040
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000

_DMG_CLASS_NONE = 0
_DMG_CLASS_MAGIC = 1
_DMG_CLASS_RANGED = 3
_RANGED_WEAPON_SUBCLASS_MASK = (1 << 2) | (1 << 3) | (1 << 18) | (1 << 16)  # bow, gun, crossbow, thrown
_ALL_SCHOOLS = 127
_STAT_STRENGTH = 0
_AURA_OBS_MOD_HEALTH = 20  # SPELL_AURA_OBS_MOD_HEALTH: a tick heals base points percent of maximum health

# spell_proc (SpellMgr.h)
_PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK = 0x00000008
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS = 0x00000020
_PROC_FLAG_TAKEN_RANGED_AUTO_ATTACK = 0x00000080
_PROC_FLAG_TAKEN_SPELL_RANGED_DMG_CLASS = 0x00000200
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG = 0x00001000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x00010000
_PROC_FLAG_DONE_PERIODIC = 0x00040000
_PROC_FLAG_TAKEN_DAMAGE = 0x00100000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_TYPE_HEAL = 0x2
_PROC_SPELL_PHASE_CAST = 0x1
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_NORMAL = 0x1
_PROC_HIT_CRITICAL = 0x2

# "An ally you heal" (ruling C4: any target the heal hits, the wearer included): the wearer's heals, direct (magic or
# none class, helpful) and heal-over-time ticks.
_HEALS_DONE = (_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS
               | _PROC_FLAG_DONE_PERIODIC)
_SPELLS_DONE = (_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG
                | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG)
# The hits a thorns strikes back at: melee and ranged, auto attacks and abilities.
_TAKEN_WEAPON_HITS = (_PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK | _PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS
                      | _PROC_FLAG_TAKEN_RANGED_AUTO_ATTACK | _PROC_FLAG_TAKEN_SPELL_RANGED_DMG_CLASS)
_HIT_OR_CRIT = _PROC_HIT_NORMAL | _PROC_HIT_CRITICAL

_OFF_GCD_MS = 1500  # potency time basis of a proc payout

# Stock looks (stock Spell.dbc, read 2026-11-19; none checked in game).
_ICON_AVENGING_WRATH = 2168
_SV_DEATH_WISH, _ICON_DEATH_WISH = 4599, 169
_ICON_CRUSADER_STRIKE = 2309
_SV_GREATER_SANCTUARY, _ICON_GREATER_SANCTUARY = 7323, 1804
_SV_INNER_FIRE, _ICON_CONSECRATION = 211, 51
_SV_HOLY_WRATH = 126
_ICON_INTIMIDATION = 166
_SV_BITE, _ICON_BITE = 376, 1680
_SV_ELEMENTAL_MASTERY, _ICON_ELEMENTAL_MASTERY = 290, 117
_SV_HUNTERS_MARK, _ICON_PSYCHIC_SCREAM = 3239, 1488
_ICON_SWIFTMEND = 1917
_SV_BONE_SHIELD, _ICON_BONE_SHIELD = 11539, 2739
_SV_THORNS, _ICON_THORNS = 201, 53
_ICON_HOLY_SHIELD = 453
_SV_ARCANE_BUBBLE, _ICON_ARCANE_BUBBLE = 968, 81  # Arcanist Doan's Arcane Bubble 9438
_SV_ARCANE_EXPLOSION, _ICON_ARCANE_EXPLOSION = 965, 122
_SV_HAND_OF_SACRIFICE, _ICON_HAND_OF_SACRIFICE = 299, 504

# Script numbers shown in tooltips (mirrored in ZealotSetLogic.h; lib/test_zealot_set.py checks they match).
FERVOR_FULL_AT_HEALTH_PCT = 40
MARTYR_HEALTH_PCT = 35
MARTYR_COOLDOWN_S = 60
UNBROKEN_ZEAL_HEAL_PCT = 30
KINDLED_VIGIL_RADIUS = 5
KENNEL_CALL_HOUNDS = 2
LAST_PAGE_CHARGES = 3
CONFESSION_LESS_DAMAGE_PCT = 15
CONFESSION_FINISHER_PCT = 10
CONFESSION_HEAL_PCT = 25
ARCANISTS_WARD_HEALTH_PCT = 15
BLOOD_OFFERING_COST_PCT = 10

_FERVOR_SLOPE = (' The bonus grows the more health is missing: nothing at full health, the full bonus at '
                 f'{FERVOR_FULL_AT_HEALTH_PCT}% health or below.')
_ICD = f' This effect cannot occur more than once every {MARTYR_COOLDOWN_S} sec.'


def _raw(desc: str = '', aura_desc: str = '', spell_level: int = 0, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': spell_level, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_TEXT_MASKS, **more}


def _bonus(spell_id: int, name: str, desc: str, icon: int, notes: str, *, effects=None, proc_type_mask: int = 0
           ) -> object:
    """A set bonus: the passive aura ItemSet.dbc names (applied by AddItemsSetItem, so no item). Its description is the
    "(N) Set:" line."""
    if effects is None:
        effects = [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER)]
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_PASSIVE, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=effects, spell_icon_id=icon, notes=notes,
        raw_overrides=_raw(desc, ProcTypeMask=proc_type_mask, ProcChance=100 if proc_type_mask else 0),
    )


def _payout(spell_id: int, name: str, school: int, effects: list, icon: int, notes: str, *, desc: str = '',
            aura_desc: str = '', duration_ms: int = 0, attributes: int = 0, range_yards=100.0, visual: int = 0,
            defense: int = _DMG_CLASS_MAGIC, spell_level: int = 1, **more) -> object:
    """A payout the set bonus casts (triggered): procs nothing of its own (SUPPRESS_CASTER_PROCS)."""
    return spell(
        id=spell_id, name=name, school=school, attributes=attributes, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=range_yards, duration_ms=duration_ms,
        effects=effects, spell_icon_id=icon, notes=notes,
        raw_overrides=_raw(desc, aura_desc, spell_level=spell_level, DefenseType=defense, SpellVisualID_1=visual,
                           AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | more.pop('AttributesEx3', 0), **more),
    )


def _aura(aura: int, *, base_points: int = 0, misc_value: int = 0, target: int = _TARGET_UNIT_CASTER, **more) -> Effect:
    return Effect(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=base_points, misc_value=misc_value,
                  implicit_target_a=target, **more)


def _strike(kind: str = 'direct', *, sp: float = 0.0, ap: float = 0.0, target: int = _TARGET_UNIT_TARGET_ENEMY,
            **more) -> Effect:
    return Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=sp, ap_potency=ap, potency_kind=kind,
                  time_basis_ms=_OFF_GCD_MS, implicit_target_a=target, **more)


def _martyr(spell_obj, *, heals: bool, self_trigger: bool = True) -> None:
    """The 3 piece's trigger row: a hit taken (the 35% crossing, `self_trigger`) and, for the heal sets, the wearer's
    heals landing (hit phase and heal-over-time ticks; the 35% check on the healed player). 100%, the 60 s internal
    cooldown; spell_zealot_martyr decides."""
    flags = (_PROC_FLAG_TAKEN_DAMAGE if self_trigger else 0) | (_HEALS_DONE if heals else 0)
    procs_on(spell_obj, proc_flags=flags,
             spell_type_mask=(_PROC_SPELL_TYPE_DAMAGE | _PROC_SPELL_TYPE_HEAL) if heals else 0,
             spell_phase_mask=_PROC_SPELL_PHASE_HIT if heals else 0, chance=100.0,
             cooldown_ms=MARTYR_COOLDOWN_S * 1000)
    scripted_by(spell_obj, 'spell_zealot_martyr')


_TRIGGER_SELF = f'When a hit takes you below {MARTYR_HEALTH_PCT}% health, '
_TRIGGER_HEAL = (f'When a hit takes you below {MARTYR_HEALTH_PCT}% health, or your heal lands on anyone at or below '
                 f'{MARTYR_HEALTH_PCT}% health (you included), ')

# =====================================================================================================================
# Zealot's Fervor, the 2 piece role line (212100-212103)

_FERVOR_NOTES = ('Zealot\'s set 2 piece, {role}. Passive DUMMY effects carry the full values ({values}); '
                 'ZealotSetUnitHooks scales them by the slope ZealotSet::FervorBonusBp (nothing at full health, the '
                 'full value at 40% health or below) at each {events}. No spell_proc row: the hooks read the aura.')

zealots_fervor_damage_212100 = _bonus(
    212100, 'Zealot\'s Fervor',
    'Your damage is increased by up to $s1%.' + _FERVOR_SLOPE,
    _ICON_AVENGING_WRATH,
    _FERVOR_NOTES.format(role='damage dealers (Plate Strength, Mail Agility, Leather Agility, Cloth Intellect)',
                         values='effect 1 +6% damage done, on the wearer\'s own health',
                         events='auto attack, spell hit and damage tick the wearer deals'),
    effects=[_aura(AuraType.DUMMY, base_points=5)],
)

zealots_fervor_healing_212101 = _bonus(
    212101, 'Zealot\'s Fervor',
    'Your healing is increased by up to $s1%, the more health your target is missing: nothing on a target at full '
    f'health, the full bonus on a target at {FERVOR_FULL_AT_HEALTH_PCT}% health or below.',
    _ICON_AVENGING_WRATH,
    _FERVOR_NOTES.format(role='healers (Cloth Spirit)', values='effect 1 +8% healing done, on the healed target\'s '
                         'health', events='direct heal and heal-over-time tick (health before the heal)'),
    effects=[_aura(AuraType.DUMMY, base_points=7)],
)

zealots_fervor_tank_212102 = _bonus(
    212102, 'Zealot\'s Fervor',
    'Damage you take is reduced by up to $s1%.' + _FERVOR_SLOPE,
    _ICON_AVENGING_WRATH,
    _FERVOR_NOTES.format(role='tanks (Plate Tank, Leather Tank)', values='effect 1 -6% damage taken, on the '
                         'wearer\'s own health', events='hit and damage tick the wearer takes'),
    effects=[_aura(AuraType.DUMMY, base_points=5)],
)

zealots_fervor_hybrid_212103 = _bonus(
    212103, 'Zealot\'s Fervor',
    'Your damage is increased by up to $s1%, the more health you are missing, and your healing by up to $s2%, the '
    'more health your target is missing: nothing at full health, the full bonus at '
    f'{FERVOR_FULL_AT_HEALTH_PCT}% health or below.',
    _ICON_AVENGING_WRATH,
    _FERVOR_NOTES.format(role='hybrids (Plate Intellect, Mail Intellect, Leather Spirit)',
                         values='effect 1 +6% damage done on the wearer\'s own health, effect 2 +8% healing done on '
                         'the healed target\'s', events='hit, tick or heal'),
    effects=[_aura(AuraType.DUMMY, base_points=5), _aura(AuraType.DUMMY, base_points=7)],
)

# =====================================================================================================================
# Plate Strength: Battlegear of the Scarlet Champion (1004)

unbroken_zeal_heal_212112 = _payout(
    212112, 'Unbroken Zeal', School.HOLY,
    [Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=_TARGET_UNIT_CASTER,
            potency_excluded='percent of the melee ability\'s damage, set by spell_zealot_unbroken_zeal')],
    _ICON_DEATH_WISH,
    'Zealot\'s set, Scarlet Champion 3 piece: the heal of a melee ability hit under Unbroken Zeal, cast on the wearer '
    'with the amount (30% of the hit, CastCustomSpell). DefenseType NONE: no healing bonus on top (Haunted Grave '
    'Bloom\'s shape).',
    desc='Heals you.', range_yards=RANGE_SELF, defense=_DMG_CLASS_NONE, spell_level=0,
)

unbroken_zeal_buff_212111 = _payout(
    212111, 'Unbroken Zeal', School.HOLY,
    [_aura(AuraType.MOD_TOTAL_STAT_PERCENTAGE, base_points=4, misc_value=_STAT_STRENGTH),
     _aura(AuraType.DUMMY, base_points=UNBROKEN_ZEAL_HEAL_PCT - 1)],
    _ICON_DEATH_WISH,
    'Zealot\'s set, Scarlet Champion 3 piece: Herod\'s frenzy. 10 s: Strength +5% (MOD_TOTAL_STAT_PERCENTAGE misc 0, '
    'base 4 + die 1); effect 2 the heal percent (30) read by spell_zealot_unbroken_zeal: spell_proc done melee-class '
    'abilities, damage, hit phase, 100%, each hit heals the wearer 212112 for 30% of its damage. Look: stock Death '
    'Wish SV 4599.',
    desc='Strength increased by $s1%, and your melee abilities heal you for $s2% of the damage they deal.',
    aura_desc='Strength increased; melee abilities heal you.', duration_ms=10000, range_yards=RANGE_SELF,
    visual=_SV_DEATH_WISH, defense=_DMG_CLASS_NONE, spell_level=0,
)
procs_on(unbroken_zeal_buff_212111, proc_flags=_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS,
         spell_type_mask=_PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_HIT_OR_CRIT,
         chance=100.0)
scripted_by(unbroken_zeal_buff_212111, 'spell_zealot_unbroken_zeal')

unbroken_zeal_212110 = _bonus(
    212110, 'Unbroken Zeal',
    _TRIGGER_SELF + 'your Strength is increased by $212111s1% for $212111d and your melee abilities heal you for '
    '$212111s2% of the damage they deal.' + _ICD,
    _ICON_DEATH_WISH,
    'Zealot\'s set, Battlegear of the Scarlet Champion 3 piece (Plate Strength). spell_proc: taken damage, 100%, 60 s '
    'internal cooldown; spell_zealot_martyr passes only the hit that crosses 35% health: 212111 on the wearer.',
    proc_type_mask=_PROC_FLAG_TAKEN_DAMAGE,
)
_martyr(unbroken_zeal_212110, heals=False)

# =====================================================================================================================
# Plate Tank: Bulwark of the Last Stand (1005)

hold_the_line_buff_212121 = _payout(
    212121, 'Hold the Line', School.HOLY,
    [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-11, misc_value=_ALL_SCHOOLS,
           target=_TARGET_UNIT_CASTER_AREA_PARTY, radius_yards=10.0)],
    _ICON_GREATER_SANCTUARY,
    'Zealot\'s set, Last Stand 3 piece: Mograine\'s last stand. The wearer and party members within 10 yd '
    '(TARGET_UNIT_CASTER_AREA_PARTY): damage taken -10% (base -11 + die 1, all schools), 8 s. Spell data only. Look: '
    'stock Greater Blessing of Sanctuary SV 7323.',
    desc='Damage taken reduced by $s1%.', aura_desc='Damage taken reduced.', duration_ms=8000,
    range_yards=RANGE_SELF, visual=_SV_GREATER_SANCTUARY, defense=_DMG_CLASS_NONE, spell_level=0,
)

hold_the_line_212120 = _bonus(
    212120, 'Hold the Line',
    _TRIGGER_SELF + 'you hold the line: you and your party members within $212121a1 yards take $212121s1% less '
    'damage for $212121d.' + _ICD,
    _ICON_GREATER_SANCTUARY,
    'Zealot\'s set, Bulwark of the Last Stand 3 piece (Plate Tank). spell_proc: taken damage, 100%, 60 s internal '
    'cooldown; spell_zealot_martyr passes only the 35% crossing: 212121 around the wearer.',
    proc_type_mask=_PROC_FLAG_TAKEN_DAMAGE,
)
_martyr(hold_the_line_212120, heals=False)

# =====================================================================================================================
# Plate Intellect: Vigil of the Fallen Champion (1006)

kindled_vigil_burn_212132 = _payout(
    212132, 'Kindled Vigil', School.HOLY,
    [_strike(sp=35.0, target=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=float(KINDLED_VIGIL_RADIUS))],
    _ICON_CONSECRATION,
    'Zealot\'s set, Fallen Champion 3 piece: the vigil flame\'s burn, cast by the wearer at the vigil owner\'s spot '
    'every 2 s (spell_zealot_kindled_vigil, CastSpell at a position: TARGET_UNIT_DEST_AREA_ENEMY from the dest, the '
    'Powder Keg blast\'s shape). Holy, spell power potency 35, T 1.5 s, every enemy within 5 yd, in combat or not '
    '(designer ruling B8: a short area hits everyone). Look: stock Holy Wrath SV 126.',
    desc='Deals {pot1} Holy damage to all enemies within $a1 yards.', visual=_SV_HOLY_WRATH,
)

kindled_vigil_aura_212131 = _payout(
    212131, 'Kindled Vigil', School.HOLY,
    [_aura(_AURA_OBS_MOD_HEALTH, base_points=4, target=_TARGET_UNIT_TARGET_ALLY, amplitude=2000,
           potency_excluded='percent of maximum health per tick (SPELL_AURA_OBS_MOD_HEALTH)'),
     _aura(AuraType.PERIODIC_DUMMY, target=_TARGET_UNIT_TARGET_ALLY, amplitude=2000)],
    _ICON_CONSECRATION,
    'Zealot\'s set, Fallen Champion 3 piece: the vigil flame over the wearer or the target the wearer healed. 6 s: '
    'OBS_MOD_HEALTH 5% of maximum health every 2 s (base 4 + die 1, 15% in all); PERIODIC_DUMMY every 2 s, '
    'spell_zealot_kindled_vigil: the caster (the wearer) casts 212132 at the owner\'s position. Look: stock Inner Fire '
    'SV 211.',
    desc='Heals $s1% of maximum health every $t1 sec for $d, and burns nearby enemies.',
    aura_desc='A vigil flame heals you and burns nearby enemies.', duration_ms=6000, visual=_SV_INNER_FIRE,
    defense=_DMG_CLASS_NONE, spell_level=0, range_yards=40.0,
)
scripted_by(kindled_vigil_aura_212131, 'spell_zealot_kindled_vigil')

kindled_vigil_212130 = _bonus(
    212130, 'Kindled Vigil',
    _TRIGGER_HEAL + 'a vigil flame burns over them for $212131d, healing them for $212131o1% of their maximum health '
    'over the time and dealing ' + pot_text(kindled_vigil_burn_212132) + ' Holy damage to all enemies within '
    '$212132a1 yards of them every $212131t2 sec.' + _ICD,
    _ICON_CONSECRATION,
    'Zealot\'s set, Vigil of the Fallen Champion 3 piece (Plate Intellect; Holy and the Holy damage paladin). '
    'spell_proc: taken damage and the wearer\'s heals (direct, hit phase, and heal-over-time ticks), 100%, 60 s '
    'internal cooldown; spell_zealot_martyr: the 35% crossing (212131 on the wearer) or a heal on any target (the '
    'wearer included, ruling C4) at or below 35% as it lands (212131 on them).',
    proc_type_mask=_PROC_FLAG_TAKEN_DAMAGE | _HEALS_DONE,
)
_martyr(kindled_vigil_212130, heals=True)

# =====================================================================================================================
# Mail Agility: Houndmaster's Harness (1007)

kennel_call_bite_212142 = _payout(
    212142, 'Kennel Call', School.NORMAL,
    [_strike(ap=30.0)], _ICON_BITE,
    'Zealot\'s set, Houndmaster\'s 3 piece: one hound\'s bite, cast by the wearer at its target (the hound plays the '
    'attack). Physical, attack power potency 30, T 1.5 s, DefenseType MAGIC (the Molten Edge AP payout shape: no '
    'dodge or parry roll, armor still applies to Physical). Look: stock Bite SV 376.',
    desc='Deals {pot1} Physical damage.', visual=_SV_BITE,
)
kennel_call_bite_ranged_212143 = _payout(
    212143, 'Kennel Call', School.NORMAL,
    [_strike(ap=30.0)], _ICON_BITE,
    'Zealot\'s set, Houndmaster\'s 3 piece: the bite off ranged attack power (DefenseType RANGED and the ranged '
    'weapon subclass mask, Molten Obsidian Shard\'s shape; EquippedItemClass -1 keeps the cast free of a weapon '
    'requirement). spell_zealot_kennel_call picks it when the wearer\'s ranged attack power is the higher.',
    desc='Deals {pot1} Physical damage.', attributes=_ATTR0_NO_ACTIVE_DEFENSE, visual=_SV_BITE,
    defense=_DMG_CLASS_RANGED, EquippedItemSubclass=_RANGED_WEAPON_SUBCLASS_MASK,
)

kennel_call_buff_212141 = _payout(
    212141, 'Kennel Call', School.NORMAL,
    [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-11, misc_value=_ALL_SCHOOLS),
     _aura(AuraType.PERIODIC_DUMMY, amplitude=2000)],
    _ICON_INTIMIDATION,
    'Zealot\'s set, Houndmaster\'s 3 piece: the hounds fight. 12 s: damage taken -10% (base -11 + die 1); '
    'PERIODIC_DUMMY every 2 s, spell_zealot_kennel_call: each of the two hound looks (300894, summoned by '
    'spell_zealot_martyr) chases the wearer\'s target (selected, else attacked; in combat and within 40 yd) and the '
    'wearer casts a bite (212142, or 212143 when ranged attack power is higher) at it per hound; the hounds leave with '
    'the buff.',
    desc='Two hounds fight beside you. Damage taken reduced by $s1%.', aura_desc='Your hounds fight beside you.',
    duration_ms=12000, range_yards=RANGE_SELF, defense=_DMG_CLASS_NONE, spell_level=0,
)
scripted_by(kennel_call_buff_212141, 'spell_zealot_kennel_call')

kennel_call_212140 = _bonus(
    212140, 'Kennel Call',
    _TRIGGER_SELF + f'you call {KENNEL_CALL_HOUNDS} Scarlet tracking hounds to fight beside you for $212141d, each '
    'biting your target for ' + pot_text(kennel_call_bite_212142) + ' Physical damage every $212141t2 sec. While '
    'they fight, you take $212141s1% less damage.' + _ICD,
    _ICON_INTIMIDATION,
    'Zealot\'s set, Houndmaster\'s Harness 3 piece (Mail Agility). spell_proc: taken damage, 100%, 60 s internal '
    'cooldown; spell_zealot_martyr passes only the 35% crossing: two hound looks (300894) and 212141 on the wearer.',
    proc_type_mask=_PROC_FLAG_TAKEN_DAMAGE,
)
_martyr(kennel_call_212140, heals=False)

# =====================================================================================================================
# Mail Intellect: Curator's Regalia (1008)

last_page_buff_212151 = _payout(
    212151, 'Last Page', School.ARCANE,
    [_aura(AuraType.MOD_CASTING_SPEED_NOT_STACK, base_points=49)],
    _ICON_ELEMENTAL_MASTERY,
    'Zealot\'s set, Curator\'s 3 piece: casting speed +50% (MOD_CASTING_SPEED_NOT_STACK, base 49 + die 1; spell haste, '
    'so the GCD follows), 10 s, 3 charges. spell_proc: done spells, cast phase, 3 charges; spell_zealot_last_page '
    'keeps only the wearer\'s own spells with a cast time (instants never spend a charge). Look: stock Elemental '
    'Mastery SV 290.',
    desc='Your next 3 spells with a cast time cast $s1% faster.', aura_desc='Your spells cast faster.',
    duration_ms=10000, range_yards=RANGE_SELF, visual=_SV_ELEMENTAL_MASTERY, defense=_DMG_CLASS_NONE, spell_level=0,
    ProcCharges=LAST_PAGE_CHARGES,
)
procs_on(last_page_buff_212151, proc_flags=_SPELLS_DONE, spell_phase_mask=_PROC_SPELL_PHASE_CAST, chance=100.0,
         charges=LAST_PAGE_CHARGES)
scripted_by(last_page_buff_212151, 'spell_zealot_last_page')

last_page_212150 = _bonus(
    212150, 'Last Page',
    _TRIGGER_HEAL + f'your next {LAST_PAGE_CHARGES} spells within $212151d cast $212151s1% faster.' + _ICD,
    _ICON_ELEMENTAL_MASTERY,
    'Zealot\'s set, Curator\'s Regalia 3 piece (Mail Intellect; Elemental and Restoration). spell_proc: taken damage '
    'and the wearer\'s heals, 100%, 60 s internal cooldown; spell_zealot_martyr: the 35% crossing or a heal on any '
    'target (the wearer included, ruling C4) at or below 35%: 212151 on the wearer either way.',
    proc_type_mask=_PROC_FLAG_TAKEN_DAMAGE | _HEALS_DONE,
)
_martyr(last_page_212150, heals=True)

# =====================================================================================================================
# Leather Agility: Interrogator's Garb (1009)

extract_confession_heal_212162 = _payout(
    212162, 'Extract Confession', School.NORMAL,
    [Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=_TARGET_UNIT_CASTER,
            potency_excluded='percent of the finishing move\'s damage, set by ZealotSetUnitHooks')],
    _ICON_PSYCHIC_SCREAM,
    'Zealot\'s set, Interrogator\'s 3 piece: the heal of a finishing move (or its tick) on a confessing target, cast '
    'on the wearer with the amount (25% of the damage, CastCustomSpell on the wearer\'s next update). DefenseType '
    'NONE: no healing bonus on top.',
    desc='Heals you.', range_yards=RANGE_SELF, defense=_DMG_CLASS_NONE, spell_level=0,
)

extract_confession_debuff_212161 = _payout(
    212161, 'Extract Confession', School.SHADOW,
    [_aura(AuraType.DUMMY, base_points=CONFESSION_LESS_DAMAGE_PCT - 1, target=_TARGET_UNIT_TARGET_ENEMY),
     _aura(AuraType.DUMMY, base_points=CONFESSION_FINISHER_PCT - 1, target=_TARGET_UNIT_TARGET_ENEMY),
     _aura(AuraType.DUMMY, base_points=CONFESSION_HEAL_PCT - 1, target=_TARGET_UNIT_TARGET_ENEMY)],
    _ICON_PSYCHIC_SCREAM,
    'Zealot\'s set, Interrogator\'s 3 piece: the confession, 8 s, one per caster. Three DUMMY amounts read by '
    'ZealotSetUnitHooks: effect 1 the target deals 15% less damage to the caster (its hits and ticks on the caster '
    'only); effect 2 the caster\'s finishing moves (a spell that needs combo points, Rupture and Rip ticks included) '
    'deal 10% more to it; effect 3 those hits heal the caster for 25% of their damage (212162). Look: stock Hunter\'s '
    'Mark SV 3239.',
    desc='Deals $s1% less damage to the interrogator and takes $s2% more damage from their finishing moves.',
    aura_desc='Confessing.', duration_ms=8000, attributes=_ATTR0_AURA_IS_DEBUFF, visual=_SV_HUNTERS_MARK,
    range_yards=40.0,
)

extract_confession_212160 = _bonus(
    212160, 'Extract Confession',
    _TRIGGER_SELF + 'your target confesses for $212161d: it deals $212161s1% less damage to you, and your finishing '
    'moves against it deal $212161s2% more damage and heal you for $212161s3% of their damage.' + _ICD,
    _ICON_PSYCHIC_SCREAM,
    'Zealot\'s set, Interrogator\'s Garb 3 piece (Leather Agility: rogues and cats). spell_proc: taken damage, 100%, '
    '60 s internal cooldown; spell_zealot_martyr passes only the 35% crossing: 212161 on the wearer\'s target '
    '(selected, else attacked), else on the enemy whose hit crossed.',
    proc_type_mask=_PROC_FLAG_TAKEN_DAMAGE,
)
_martyr(extract_confession_212160, heals=False)

# =====================================================================================================================
# Leather Tank: Ironspine's Bones (1010)

bone_cage_spike_212172 = _payout(
    212172, 'Bone Cage', School.SHADOW,
    [_strike(ap=15.0)], _ICON_BONE_SHIELD,
    'Zealot\'s set, Ironspine\'s 3 piece: the cage strikes back at an attacker. Shadow, attack power potency 15, T 1.5 '
    's, DefenseType MAGIC. Cast by the wearer through 212171\'s PROC_TRIGGER_SPELL (the attacker is the target).',
    desc='Deals {pot1} Shadow damage.',
)

bone_cage_buff_212171 = _payout(
    212171, 'Bone Cage', School.SHADOW,
    [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-21, misc_value=_ALL_SCHOOLS),
     _aura(AuraType.PROC_TRIGGER_SPELL, trigger_spell=bone_cage_spike_212172.id)],
    _ICON_BONE_SHIELD,
    'Zealot\'s set, Ironspine\'s 3 piece: a cage of bone. 8 s: damage taken -20% (base -21 + die 1, all schools); '
    'PROC_TRIGGER_SPELL: each melee or ranged hit taken (auto attacks and abilities, spell_proc 100%, no cooldown) '
    'casts 212172 at the attacker. Spell data only. Look: stock Bone Shield SV 11539.',
    desc='Damage taken reduced by $s1%. Attackers that hit you take Shadow damage.',
    aura_desc='Damage taken reduced; attackers take Shadow damage.', duration_ms=8000, range_yards=RANGE_SELF,
    visual=_SV_BONE_SHIELD, defense=_DMG_CLASS_NONE, spell_level=0,
)
procs_on(bone_cage_buff_212171, proc_flags=_TAKEN_WEAPON_HITS, hit_mask=_HIT_OR_CRIT, chance=100.0)

bone_cage_212170 = _bonus(
    212170, 'Bone Cage',
    _TRIGGER_SELF + 'a cage of bone closes over you for $212171d: you take $212171s1% less damage, and each attacker '
    'that hits you takes ' + pot_text(bone_cage_spike_212172) + ' Shadow damage.' + _ICD,
    _ICON_BONE_SHIELD,
    'Zealot\'s set, Ironspine\'s Bones 3 piece (Leather Tank). spell_proc: taken damage, 100%, 60 s internal '
    'cooldown; spell_zealot_martyr passes only the 35% crossing: 212171 on the wearer.',
    proc_type_mask=_PROC_FLAG_TAKEN_DAMAGE,
)
_martyr(bone_cage_212170, heals=False)

# =====================================================================================================================
# Leather Spirit: Gardener's Vestments (1011)

hallowed_thorns_strike_212182 = _payout(
    212182, 'Hallowed Thorns', School.HOLY,
    [_strike(sp=15.0)], _ICON_THORNS,
    'Zealot\'s set, Gardener\'s 3 piece: the thorns strike an attacker of the protected unit. Holy, spell power '
    'potency 15, T 1.5 s. Cast by the wearer (spell_zealot_hallowed_thorns), so the wearer\'s spell power counts '
    'even when the thorns sit on an ally.',
    desc='Deals {pot1} Holy damage.',
)

hallowed_thorns_buff_212181 = _payout(
    212181, 'Hallowed Thorns', School.HOLY,
    [_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-11, misc_value=_ALL_SCHOOLS,
           target=_TARGET_UNIT_TARGET_ALLY),
     _aura(AuraType.DUMMY, target=_TARGET_UNIT_TARGET_ALLY)],
    _ICON_THORNS,
    'Zealot\'s set, Gardener\'s 3 piece: holy thorns on the wearer or the target the wearer healed. 10 s: damage taken '
    '-10% (base -11 + die 1); effect 2 a DUMMY with a spell_proc row (each melee or ranged hit taken, 100%, no '
    'cooldown): spell_zealot_hallowed_thorns has the aura\'s caster (the wearer) cast 212182 at the attacker. Look: '
    'stock Thorns SV 201 (the recolor the doc asks for needs a new SpellVisualKit, a designer question).',
    desc='Damage taken reduced by $s1%. Attackers that hit you take Holy damage.',
    aura_desc='Damage taken reduced; attackers take Holy damage.', duration_ms=10000, visual=_SV_THORNS,
    defense=_DMG_CLASS_NONE, spell_level=0, range_yards=40.0,
)
procs_on(hallowed_thorns_buff_212181, proc_flags=_TAKEN_WEAPON_HITS, hit_mask=_HIT_OR_CRIT, chance=100.0)
scripted_by(hallowed_thorns_buff_212181, 'spell_zealot_hallowed_thorns')

hallowed_thorns_212180 = _bonus(
    212180, 'Hallowed Thorns',
    _TRIGGER_HEAL + 'holy thorns wreathe them for $212181d: they take $212181s1% less damage, and each attacker that '
    'hits them takes ' + pot_text(hallowed_thorns_strike_212182) + ' Holy damage.' + _ICD,
    _ICON_THORNS,
    'Zealot\'s set, Gardener\'s Vestments 3 piece (Leather Spirit; Restoration and Balance). spell_proc: taken damage '
    'and the wearer\'s heals, 100%, 60 s internal cooldown; spell_zealot_martyr: the 35% crossing (212181 on the '
    'wearer) or a heal on any target (the wearer included, ruling C4) at or below 35% (212181 on them).',
    proc_type_mask=_PROC_FLAG_TAKEN_DAMAGE | _HEALS_DONE,
)
_martyr(hallowed_thorns_212180, heals=True)

# =====================================================================================================================
# Cloth Intellect: Regalia of the Arcanist (1012)

arcanists_ward_detonation_212192 = _payout(
    212192, 'Arcanist\'s Ward', School.ARCANE,
    [_strike(sp=150.0, target=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=10.0)],
    _ICON_ARCANE_EXPLOSION,
    'Zealot\'s set, Arcanist\'s 3 piece: the bubble detonates. Arcane, spell power potency 150, T 1.5 s, every enemy '
    'within 10 yd of the wearer: spell_zealot_arcanists_ward casts it at the wearer\'s position '
    '(TARGET_UNIT_DEST_AREA_ENEMY from the dest, Kindled Vigil\'s shape), in combat or not (designer ruling B8: a '
    'short area hits everyone). Look: stock Arcane Explosion SV 965.',
    desc='Deals {pot1} Arcane damage to all enemies within $a1 yards.', visual=_SV_ARCANE_EXPLOSION,
)

arcanists_ward_absorb_212191 = _payout(
    212191, 'Arcanist\'s Ward', School.ARCANE,
    [_aura(AuraType.SCHOOL_ABSORB, misc_value=_ALL_SCHOOLS,
           potency_excluded='percent of maximum health, set by spell_zealot_arcanists_ward')],
    _ICON_ARCANE_BUBBLE,
    'Zealot\'s set, Arcanist\'s 3 piece: Doan\'s bubble. 8 s, absorbs all schools; spell_zealot_arcanists_ward sets '
    'the amount to 15% of maximum health and, when the ward breaks (depleted or dispelled), expires or is cancelled, '
    'casts 212192 (never on death, logout or another cleanup removal: review m6). Look: '
    'Arcanist Doan\'s Arcane Bubble (9438) SV 968.',
    desc='Absorbs damage. Detonates when it breaks or ends.', aura_desc='Absorbs damage.', duration_ms=8000,
    range_yards=RANGE_SELF, visual=_SV_ARCANE_BUBBLE, defense=_DMG_CLASS_NONE, spell_level=0,
)
scripted_by(arcanists_ward_absorb_212191, 'spell_zealot_arcanists_ward')

arcanists_ward_212190 = _bonus(
    212190, 'Arcanist\'s Ward',
    _TRIGGER_SELF + f'an Arcane bubble absorbs damage equal to {ARCANISTS_WARD_HEALTH_PCT}% of your maximum health '
    'for $212191d. When it breaks or ends, it detonates, dealing ' + pot_text(arcanists_ward_detonation_212192)
    + ' Arcane damage to all enemies within $212192a1 yards.' + _ICD,
    _ICON_ARCANE_BUBBLE,
    'Zealot\'s set, Regalia of the Arcanist 3 piece (Cloth Intellect). spell_proc: taken damage, 100%, 60 s internal '
    'cooldown; spell_zealot_martyr passes only the 35% crossing: 212191 on the wearer.',
    proc_type_mask=_PROC_FLAG_TAKEN_DAMAGE,
)
_martyr(arcanists_ward_212190, heals=False)

# =====================================================================================================================
# Cloth Spirit: Vestments of the High Inquisitor (1013)

blood_offering_heal_212201 = _payout(
    212201, 'Blood Offering', School.HOLY,
    [Effect(type=EffectType.HEAL_PCT, base_points=19, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
            potency_excluded='percent of the target\'s maximum health (SPELL_EFFECT_HEAL_PCT)')],
    _ICON_HAND_OF_SACRIFICE,
    'Zealot\'s set, High Inquisitor 3 piece: Whitemane\'s devotion. Heals the target for 20% of their maximum health '
    '(HEAL_PCT, base 19 + die 1); spell_zealot_blood_offering takes 10% of the caster\'s current health on the hit '
    '(never below 1). Look: stock Hand of Sacrifice SV 299.',
    desc='Heals the target for $s1% of their maximum health at the cost of the caster\'s blood.',
    range_yards=40.0, visual=_SV_HAND_OF_SACRIFICE, defense=_DMG_CLASS_NONE, spell_level=0,
)
scripted_by(blood_offering_heal_212201, 'spell_zealot_blood_offering')

blood_offering_212200 = _bonus(
    212200, 'Blood Offering',
    f'When your heal lands on anyone at or below {MARTYR_HEALTH_PCT}% health (you included), you give them your own '
    f'blood: you lose {BLOOD_OFFERING_COST_PCT}% of your current health, and they are healed for $212201s1% of their '
    'maximum health.' + _ICD,
    _ICON_HAND_OF_SACRIFICE,
    'Zealot\'s set, Vestments of the High Inquisitor 3 piece (Cloth Spirit). spell_proc: the wearer\'s heals (direct, '
    'hit phase, and heal-over-time ticks), 100%, 60 s internal cooldown; spell_zealot_martyr: a heal on any target '
    '(the wearer included: a self-heal pays 10% and heals 20%, ruling C4) at or below 35% health as it lands: '
    '212201 on them. No hit-taken trigger (ruling 59).',
    proc_type_mask=_HEALS_DONE,
)
_martyr(blood_offering_212200, heals=True, self_trigger=False)

# The bonuses by ItemSet id: (2 piece, 3 piece). source/items/zealot_set.py builds the ItemSet rows from it.
SET_BONUSES = {
    1004: (zealots_fervor_damage_212100, unbroken_zeal_212110),
    1005: (zealots_fervor_tank_212102, hold_the_line_212120),
    1006: (zealots_fervor_hybrid_212103, kindled_vigil_212130),
    1007: (zealots_fervor_damage_212100, kennel_call_212140),
    1008: (zealots_fervor_hybrid_212103, last_page_212150),
    1009: (zealots_fervor_damage_212100, extract_confession_212160),
    1010: (zealots_fervor_tank_212102, bone_cage_212170),
    1011: (zealots_fervor_hybrid_212103, hallowed_thorns_212180),
    1012: (zealots_fervor_damage_212100, arcanists_ward_212190),
    1013: (zealots_fervor_healing_212101, blood_offering_212200),
}
