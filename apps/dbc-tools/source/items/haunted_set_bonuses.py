"""
The Haunted set bonuses (docs/dungeons/dungeon-loot-vanilla.md "Haunted set bonuses (approved 2026-11-06)"): a 3 piece
and a 5 piece bonus per archetype set, 20 bonus spells and their payouts. Haunted is the Scourge: each 5 piece calls
a wraith that repeats or extends what you just did, at random.

Rules the spells follow (the design's): every value scales with the player's stats or health, never a flat rating
(one bonus serves every item level); damage and healing are potency (docs/potency-system.md; "everything on
potency"); every proc is a flat chance times Proc Chance (set bonuses carry no item, so `Aura::CalcProcChance`
multiplies a spell_proc chance by it; a script roll multiplies it itself, `HauntedSet::ProcChancePct`) and rolls
once per cast; payouts suppress caster procs (SPELL_ATTR3_SUPPRESS_CASTER_PROCS), so a payout never feeds another
bonus. Proc payouts are off-GCD (potency time basis 1.5 s). Values are starting points [tune]: the dps sim measures each
one before the build is final. No look was checked in game.

Ids: the `haunted_set` reservation 205700-205899 (source/ids.yaml), ten per set; 205800-205899 spare. Scripts:
modules/mod-dungeon-bosses/src/DungeonSets/haunted_set_bonuses.cpp (ids mirrored in HauntedSetLogic.h).

  Cloth Intellect, Magister's (181)
  205700  Wraith Volley (3)      damaging spell cast 10%, periodic damage tick 4% (script roll x Proc Chance), 4 s
                                 ICD (spell_proc): bolts 205701 at the target and up to 2 other enemies within 10 yd.
  205701  Wraith Volley          the bolt: Shadow, spell power potency 100 per target, a Shadow Bolt missile.
  205702  Soul Rend (5)          marker: each enemy a bolt hits gets 205703 (spell_haunted_wraith_volley_bolt).
  205703  Soul Rend              debuff, 10 s: your spells deal 5% more damage to it (MOD_DAMAGE_FROM_CASTER, family
                                 0 = every spell, per caster, read live by every tick). Refreshed by the next bolt.
  Cloth Spirit, Devout (182)
  205710  Soul Shroud (3)        direct heals (hit phase, heal type: a HoT cast heals nothing then) trigger 205711.
  205711  Soul Shroud            the target takes 3% less damage, 6 s.
  205712  Wraith of Solace (5)   direct heal cast, 12%, 3 s ICD: 205713 on the most injured ally within 30 yd other
                                 than the heal's target (the script picks it before the roll, so no ally, no cooldown).
  205713  Wraith of Solace       Shadow heal, spell power potency 150.
  Leather Spirit, Wildheart (185)
  205720  Lingering Death (3)    marker: your periodic damage and healing auras last 10% longer
                                 (AllSpellScript::OnCalcMaxDuration; the engine folds the leftover part of a tick into
                                 the last tick, so 10% longer is 10% more damage or healing).
  205721  Grave Bloom (5)        each periodic damage or heal tick, 5%, 2 s ICD: the tick repeats on a second target
                                 within 15 yd of the first, the most injured ally (heal) or the nearest other enemy
                                 in combat (damage).
  205722  Grave Bloom            the repeated heal tick (the tick's amount, by script; DefenseType 0: no second bonus).
  205723  Grave Bloom            the repeated damage tick, Shadow (likewise).
  Mail Intellect, The Elements (187)
  205730  Frozen Chorus (3)      damaging spell or direct heal cast, 10%, 6 s ICD: 205731 (a damaging cast) or 205732
                                 (a heal) at the spell's target.
  205731  Frozen Chorus          Frost damage that arcs between 3 enemies, spell power potency 80 each.
  205732  Frozen Chorus          healing that arcs between 3 injured allies, spell power potency 80 each.
  205733  Gathering Chorus (5)   spell critical strikes (direct damage or heal, hit phase) trigger 205734.
  205734  Gathering Chorus       a stack, up to 5, 30 s: the next Frozen Chorus is 20% stronger per stack; all are
                                 consumed when it fires (spell_haunted_frozen_chorus_payout).
  Plate Intellect, Lightforge (188)
  205740  Unbroken Faith (3)     a 1 s periodic check: above 80% mana, 205741 is on you; at or below, it is gone.
  205741  Unbroken Faith         +4% healing done, +4% Holy damage done (a visible buff).
  205742  Soul Released (5)      direct heal or Holy damage spell cast, 12%, 4 s ICD: 205743 on the most injured ally
                                 within 30 yd and 205744 on the nearest enemy within 20 yd in combat.
  205743  Soul Released          Holy heal, spell power potency 100.
  205744  Soul Released          Holy damage, spell power potency 100.
  Plate Strength, Valor (189)
  205750  Bone Shatter (3)       melee ability cast, 10%, 5 s ICD: 205751 around the ability's target.
  205751  Bone Shatter           Physical, every enemy within 8 yd of the target, attack power potency 100 each,
                                 cannot be dodged, parried or blocked.
  205752  Broken Bones (5)       marker: each Bone Shatter also casts 205753 on you.
  205753  Broken Bones           armor penetration +10%, 15 s (Physical only: armor reduces nothing else).
  Mail Agility, Beaststalker's (186)
  205760  Haunting Mark (3)      melee and ranged abilities, 15%, 4 s ICD: 205761 on the target.
  205761  Haunting Mark          debuff, 15 s: your next ability against it deals 15% more damage and consumes it
                                 (HauntedSetUnitHooks::ModifySpellDamageTaken).
  205762  Grasp of the Dead (5)  melee or ranged ability, 10%, 4 s ICD: 205763 (a melee ability) or 205764 (ranged).
  205763  Grasp of the Dead      Physical, attack power potency 120, cannot be dodged, parried or blocked.
  205764  Grasp of the Dead      the same off ranged attack power (DefenseType ranged, the ranged weapon mask).
  Leather Agility, Shadowcraft (184)
  205770  Wraith Venom (3)       marker: a poison hit or bleed tick, 8% (script roll x Proc Chance), 2 s ICD per rogue:
                                 205771 on the target (HauntedSetUnitHooks).
  205771  Wraith Venom           Shadow damage over 6 s, a tick every 2 s, attack power potency 5 a tick (a rate: poison
                                 hits and bleed ticks come several a second, so the venom is up most of the time and
                                 this is about 3% more damage). One per target per caster: a new infection refreshes
                                 it.
  205772  Grave Rot (5)          marker: a poison hit or bleed tick, 6% (x Proc Chance), 3 s ICD: 205773 on the target,
                                 and the caster's bleeds, damage-over-time poisons and Wraith Venom on it last 2 s
                                 longer, at most 6 s per application of each (user ruling 2026-11-06: a refresh or a
                                 reapplication starts a fresh 6 s).
  205773  Grave Rot              Shadow, attack power potency 15 (on a rogue the 3 s cooldown, not the 6%, sets its
                                 rate: about every 3 to 4 s).
  Leather Tank, Protector's (1000)
  205780  Grave Hide (3)         Stamina +3% (MOD_TOTAL_STAT_PERCENTAGE).
  205781  Bone Ward (5)          you dodge, 100%, 1 s ICD: 205782 on you.
  205782  Bone Ward              absorb, 3% of your maximum health per stack, up to 3 stacks, 10 s, each stack
                                 refreshing (spell_haunted_bone_ward sets the amount).
  Plate Tank, Shadowguard (1001)
  205790  Spirit Bulwark (3)     you block or parry, 100%, 1 s ICD: 205791.
  205791  Spirit Bulwark         heals you for 1% of your maximum health.
  205792  Deathless (5)          a hit takes you from 35% health or more to below 35%, 60 s ICD: 205793.
  205793  Deathless              heals you for 15% of your maximum health over 6 s (5% every 2 s).
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
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_UNIT_TARGET_CHAINHEAL_ALLY = 45
_TARGET_DEST_TARGET_ENEMY = 53

_ATTR0_PASSIVE = 0x00000040
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000

_DMG_CLASS_NONE = 0
_DMG_CLASS_MAGIC = 1
_DMG_CLASS_MELEE = 2
_DMG_CLASS_RANGED = 3
_RANGED_WEAPON_SUBCLASS_MASK = (1 << 2) | (1 << 3) | (1 << 18) | (1 << 16)  # bow, gun, crossbow, thrown
_ALL_SCHOOLS = 127
_SCHOOL_MASK_HOLY = 2
_STAT_STAMINA = 2
_AURA_OBS_MOD_HEALTH = 20  # SPELL_AURA_OBS_MOD_HEALTH: a tick heals base points percent of maximum health
_AURA_MOD_ARMOR_PENETRATION_PCT = 280

# spell_proc (SpellMgr.h)
_PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK = 0x00000008
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS = 0x00000020
_PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS = 0x00000100
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
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
_PROC_HIT_DODGE = 0x10
_PROC_HIT_PARRY = 0x20
_PROC_HIT_BLOCK = 0x40

_HEALS = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS
_SPELLS = _HEALS | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG
_ABILITIES = _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS | _PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
_TAKEN_MELEE = _PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK | _PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS
_HIT_OR_CRIT = _PROC_HIT_NORMAL | _PROC_HIT_CRITICAL

_OFF_GCD_MS = 1500  # potency time basis of a proc payout

# Stock looks (stock Spell.dbc, read 2026-11-06; none checked in game).
_SV_SHADOW_BOLT, _ICON_SHADOW_BOLT = 64, 213
_ICON_HAUNT = 3172
_SV_PAIN_SUPPRESSION, _ICON_PAIN_SUPPRESSION = 8039, 2178
_SV_GUARDIAN_SPIRIT, _ICON_GUARDIAN_SPIRIT = 12114, 2873
_ICON_REJUVENATION = 64
_SV_LIFEBLOOM, _ICON_LIFEBLOOM = 8145, 2101
_SV_SHADOW_WORD_PAIN = 71
_SV_FROSTBOLT, _ICON_FROSTBOLT = 13, 188
_SV_CHAIN_HEAL, _ICON_CHAIN_HEAL = 3659, 963
_ICON_ICY_VEINS = 2162
_SV_DIVINE_PLEA, _ICON_DIVINE_PLEA = 11947, 2821
_SV_HOLY_LIGHT, _ICON_HOLY_LIGHT = 2936, 70
_SV_EXORCISM, _ICON_EXORCISM = 324, 292
_SV_THUNDER_CLAP, _ICON_BONE_SHIELD = 145, 2739
_ICON_SUNDER_ARMOR = 565
_SV_HUNTERS_MARK, _ICON_HUNTERS_MARK = 3239, 538
_SV_DEATH_COIL, _ICON_RAISE_DEAD = 10755, 221
_ICON_SHADOW_WORD_PAIN = 234
_SV_CORRUPTION, _ICON_CORRUPTION = 8629, 313
_ICON_UNBREAKABLE_ARMOR = 2703
_SV_BONE_SHIELD = 11539
_ICON_HOLY_SHIELD = 453
_SV_VAMPIRIC_BLOOD, _ICON_VAMPIRIC_BLOOD = 11149, 153

# Script numbers shown in tooltips (mirrored in HauntedSetLogic.h; lib/test_haunted_set.py checks they match).
WRAITH_VOLLEY_CAST_PCT = 10
WRAITH_VOLLEY_TICK_PCT = 4
WRAITH_VOLLEY_EXTRA_TARGETS = 2
WRAITH_VOLLEY_RADIUS = 10
SOLACE_RANGE = 30
LINGERING_DEATH_PCT = 10
GRAVE_BLOOM_RADIUS = 15
CHORUS_TARGETS = 3
CHORUS_STACK_PCT = 20
UNBROKEN_FAITH_MANA_PCT = 80
SOUL_RELEASED_HEAL_RANGE = 30
SOUL_RELEASED_ENEMY_RANGE = 20
WRAITH_VENOM_PCT = 8
WRAITH_VENOM_ICD_S = 2
GRAVE_ROT_PCT = 6
GRAVE_ROT_ICD_S = 3
GRAVE_ROT_EXTEND_S = 2
GRAVE_ROT_EXTEND_CAP_S = 6
BONE_WARD_PCT = 3
DEATHLESS_HEALTH_PCT = 35


def _raw(desc: str = '', aura_desc: str = '', spell_level: int = 0, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': spell_level, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_TEXT_MASKS, **more}


def _bonus(spell_id: int, name: str, desc: str, icon: int, notes: str, *, aura: int = AuraType.DUMMY,
           base_points: int = 0, misc_value: int = 0, trigger: int = 0, amplitude: int = 0, proc_type_mask: int = 0,
           proc_chance: int = 0) -> object:
    """A set bonus: the passive aura ItemSet.dbc names (applied by AddItemsSetItem, so no item: Proc Chance reaches
    its procs). Its description is the "(N) Set:" line."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_PASSIVE, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=base_points, misc_value=misc_value,
                        trigger_spell=trigger, amplitude=amplitude, implicit_target_a=_TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=_raw(desc, ProcTypeMask=proc_type_mask, ProcChance=proc_chance),
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


def _direct(kind: str, *, sp: float = 0.0, ap: float = 0.0, target: int = _TARGET_UNIT_TARGET_ENEMY,
            effect: int = EffectType.SCHOOL_DAMAGE, **more) -> Effect:
    return Effect(type=effect, sp_potency=sp, ap_potency=ap, potency_kind=kind, time_basis_ms=_OFF_GCD_MS,
                  implicit_target_a=target, **more)


# =====================================================================================================================
# Cloth Intellect: Magister's (181)

soul_rend_debuff_205703 = _payout(
    205703, 'Soul Rend', School.SHADOW,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_FROM_CASTER, base_points=4,
            implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    _ICON_HAUNT,
    'Haunted set, Magister\'s 5 piece: the debuff a Wraith Volley bolt leaves. MOD_DAMAGE_FROM_CASTER +5% (base 4 + '
    'die 1), family 0, so every spell of the caster and every tick, read live (Unit::SpellDamageBonusTaken); per '
    'caster, so it never stacks with another player\'s. 10 s, refreshed by the next bolt.',
    desc='Your spells deal $s1% more damage to the target.', aura_desc='Vulnerable to the caster\'s spells.',
    duration_ms=10000, attributes=_ATTR0_AURA_IS_DEBUFF,
)

wraith_volley_bolt_205701 = _payout(
    205701, 'Wraith Volley', School.SHADOW,
    [_direct('direct', sp=100.0)], _ICON_SHADOW_BOLT,
    'Haunted set, Magister\'s 3 piece: one wraith bolt. Shadow, spell power potency 100, T 1.5 s (an off-GCD '
    'payout); a missile (Speed 20, the Shadow Bolt look). spell_haunted_wraith_volley_bolt puts Soul Rend 205703 on '
    'the enemy it hits when the caster has the 5 piece 205702.',
    desc='Deals {pot1} Shadow damage.', visual=_SV_SHADOW_BOLT, Speed=20.0,
)
scripted_by(wraith_volley_bolt_205701, 'spell_haunted_wraith_volley_bolt')

wraith_volley_205700 = _bonus(
    205700, 'Wraith Volley',
    f'Your damaging spells have a {WRAITH_VOLLEY_CAST_PCT}% chance, and your periodic damage a '
    f'{WRAITH_VOLLEY_TICK_PCT}% chance, to call a wraith that looses Shadow bolts at your target and up to '
    f'{WRAITH_VOLLEY_EXTRA_TARGETS} other enemies within {WRAITH_VOLLEY_RADIUS} yards, each dealing '
    + pot_text(wraith_volley_bolt_205701) + ' Shadow damage. This effect cannot occur more than once every 4 sec.',
    _ICON_SHADOW_BOLT,
    'Haunted set, Magister\'s 3 piece (Cloth Intellect). spell_proc: done harmful magic spells (0x10000, cast phase) '
    'and periodic damage (0x40000, hit phase), 100% in the row, 4 s internal cooldown; spell_haunted_wraith_volley\'s '
    'CheckProc rolls 10% on a damaging cast and 4% on a periodic tick, times Proc Chance (a script roll), so the '
    'cooldown starts only on a success. The bolts 205701 go to the target and up to 2 other enemies within 10 yd of '
    'it.',
    proc_type_mask=_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_PERIODIC, proc_chance=100,
)
procs_on(wraith_volley_205700, proc_flags=_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_PERIODIC,
         spell_type_mask=_PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=_PROC_SPELL_PHASE_CAST | _PROC_SPELL_PHASE_HIT,
         chance=100.0, cooldown_ms=4000)
scripted_by(wraith_volley_205700, 'spell_haunted_wraith_volley')

soul_rend_205702 = _bonus(
    205702, 'Soul Rend',
    'Each enemy hit by your Wraith Volley becomes vulnerable to you: your spells deal $205703s1% more damage to it '
    'for $205703d.',
    _ICON_HAUNT,
    'Haunted set, Magister\'s 5 piece: a marker read by spell_haunted_wraith_volley_bolt (the debuff is 205703).',
)

# =====================================================================================================================
# Cloth Spirit: Devout (182)

soul_shroud_buff_205711 = _payout(
    205711, 'Soul Shroud', School.SHADOW,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-4,
            misc_value=_ALL_SCHOOLS, implicit_target_a=_TARGET_UNIT_TARGET_ALLY)],
    _ICON_PAIN_SUPPRESSION,
    'Haunted set, Devout 3 piece: the shroud. Damage taken -3% (base -4 + die 1, all schools), 6 s, on the healed '
    'target. A second healer\'s shroud is a second aura (own caster). Look: stock Pain Suppression SV 8039.',
    desc='Damage taken reduced by $s1%.', aura_desc='Damage taken reduced.', duration_ms=6000,
    visual=_SV_PAIN_SUPPRESSION, defense=_DMG_CLASS_NONE, spell_level=0,
)

soul_shroud_205710 = _bonus(
    205710, 'Soul Shroud',
    'Your direct heals shroud the target, reducing the damage it takes by $205711s1% for $205711d.',
    _ICON_PAIN_SUPPRESSION,
    'Haunted set, Devout 3 piece (Cloth Spirit). A PROC_TRIGGER_SPELL aura: done helpful spells (0x4400), heal type, '
    'hit phase (a HoT cast heals nothing in its hit phase, so only direct heals count), normal or critical, 100%: '
    '205711 on the healed target. No script.',
    aura=AuraType.PROC_TRIGGER_SPELL, trigger=soul_shroud_buff_205711.id, proc_type_mask=_HEALS, proc_chance=100,
)
procs_on(soul_shroud_205710, proc_flags=_HEALS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_HIT_OR_CRIT, chance=100.0)

wraith_of_solace_heal_205713 = _payout(
    205713, 'Wraith of Solace', School.SHADOW,
    [_direct('heal', sp=150.0, effect=EffectType.HEAL, target=_TARGET_UNIT_TARGET_ALLY)], _ICON_GUARDIAN_SPIRIT,
    'Haunted set, Devout 5 piece: the wraith\'s heal. Spell power potency 150 (heal), T 1.5 s. Look: stock Guardian '
    'Spirit SV 12114.',
    desc='Heals the target for {pot1}.', visual=_SV_GUARDIAN_SPIRIT,
)

wraith_of_solace_205712 = _bonus(
    205712, 'Wraith of Solace',
    'Your direct heals have a $h% chance to call a wraith that heals the most injured ally within '
    f'{SOLACE_RANGE} yards other than your target for ' + pot_text(wraith_of_solace_heal_205713)
    + '. This effect cannot occur more than once every 3 sec.',
    _ICON_GUARDIAN_SPIRIT,
    'Haunted set, Devout 5 piece (Cloth Spirit). spell_proc: done helpful spells (0x4400), cast phase (one roll per '
    'cast), 12% (x Proc Chance), 3 s internal cooldown. spell_haunted_wraith_of_solace\'s CheckProc keeps casts with a '
    'direct heal effect and picks the ally first (the most injured group member or self within 30 yd, not the '
    'cast\'s target): with no injured ally there is no roll and no cooldown. The heal is 205713.',
    proc_type_mask=_HEALS, proc_chance=12,
)
procs_on(wraith_of_solace_205712, proc_flags=_HEALS, spell_phase_mask=_PROC_SPELL_PHASE_CAST, chance=12.0,
         cooldown_ms=3000)
scripted_by(wraith_of_solace_205712, 'spell_haunted_wraith_of_solace')

# =====================================================================================================================
# Leather Spirit: Wildheart (185)

lingering_death_205720 = _bonus(
    205720, 'Lingering Death',
    f'Your heal-over-time and damage-over-time effects last {LINGERING_DEATH_PCT}% longer.',
    _ICON_REJUVENATION,
    'Haunted set, Wildheart 3 piece (Leather Spirit): a marker. HauntedSetSpellHooks::OnCalcMaxDuration lengthens '
    'every aura the wearer casts that has a periodic damage, leech or heal effect (not channels, not passives) by 10%, '
    'on creation and on every refresh. The engine folds the leftover part of a tick into the last tick '
    '(AuraEffect::GetFinalTickBonusMultiplier), so 10% longer is 10% more.',
)

grave_bloom_heal_205722 = _payout(
    205722, 'Grave Bloom', School.SHADOW,
    [Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
            potency_excluded='repeats a heal tick: the script passes the tick\'s own amount (CastCustomSpell)')],
    _ICON_LIFEBLOOM,
    'Haunted set, Wildheart 5 piece: the repeated heal tick. The amount is the tick\'s, set by '
    'spell_haunted_grave_bloom; DefenseType 0 with no spell_bonus_data row, so the engine adds no second spell power '
    'or done bonus (the tick already had them). Look: stock Lifebloom SV 8145.',
    visual=_SV_LIFEBLOOM, defense=_DMG_CLASS_NONE, spell_level=0,
)

grave_bloom_damage_205723 = _payout(
    205723, 'Grave Bloom', School.SHADOW,
    [Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            potency_excluded='repeats a damage tick: the script passes the tick\'s own amount (CastCustomSpell)')],
    _ICON_LIFEBLOOM,
    'Haunted set, Wildheart 5 piece: the repeated damage tick, Shadow. The amount is the tick\'s (script); '
    'DefenseType 0, no second bonus. Look: stock Shadow Word: Pain SV 71.',
    visual=_SV_SHADOW_WORD_PAIN, defense=_DMG_CLASS_NONE, spell_level=0,
)

grave_bloom_205721 = _bonus(
    205721, 'Grave Bloom',
    'Each tick of your periodic effects has a $h% chance to repeat on a second target within '
    f'{GRAVE_BLOOM_RADIUS} yards: a heal on the most injured ally, damage on another enemy. This effect cannot occur '
    'more than once every 2 sec.',
    _ICON_LIFEBLOOM,
    'Haunted set, Wildheart 5 piece (Leather Spirit). spell_proc: done periodic (0x40000), damage or heal type, hit '
    'phase, normal or critical, 5% (x Proc Chance), 2 s internal cooldown. spell_haunted_grave_bloom: the second '
    'target is within 15 yd of the tick\'s target (a heal: the most injured group member or self, not the first '
    'target; damage: the nearest other enemy in combat with the wearer); CheckProc finds it first, so no target means '
    'no roll. 205722 / 205723 carry the tick\'s amount.',
    proc_type_mask=_PROC_FLAG_DONE_PERIODIC, proc_chance=5,
)
procs_on(grave_bloom_205721, proc_flags=_PROC_FLAG_DONE_PERIODIC,
         spell_type_mask=_PROC_SPELL_TYPE_DAMAGE | _PROC_SPELL_TYPE_HEAL, spell_phase_mask=_PROC_SPELL_PHASE_HIT,
         hit_mask=_HIT_OR_CRIT, chance=5.0, cooldown_ms=2000)
scripted_by(grave_bloom_205721, 'spell_haunted_grave_bloom')

# =====================================================================================================================
# Mail Intellect: The Elements (187)

frozen_chorus_damage_205731 = _payout(
    205731, 'Frozen Chorus', School.FROST,
    [_direct('direct', sp=80.0, chain_targets=CHORUS_TARGETS)], _ICON_FROSTBOLT,
    'Haunted set, The Elements 3 piece: the Frost arc, the cast\'s target and 2 more enemies (ChainTargets 3, the '
    'Chain Lightning shape, no falloff). Spell power potency 80 per target, T 1.5 s. '
    'spell_haunted_frozen_chorus_payout multiplies it by the Gathering Chorus stacks. Look: stock Frostbolt SV 13.',
    desc='Frost damage that arcs between up to $x1 enemies, {pot1} each.', visual=_SV_FROSTBOLT,
)
frozen_chorus_heal_205732 = _payout(
    205732, 'Frozen Chorus', School.FROST,
    [_direct('heal', sp=80.0, effect=EffectType.HEAL, target=_TARGET_UNIT_TARGET_CHAINHEAL_ALLY,
             chain_targets=CHORUS_TARGETS)], _ICON_CHAIN_HEAL,
    'Haunted set, The Elements 3 piece: the healing arc, the heal\'s target and 2 more injured allies '
    '(TARGET_UNIT_TARGET_CHAINHEAL_ALLY, ChainTargets 3, no falloff). Spell power potency 80 per target (heal), '
    'T 1.5 s; Gathering Chorus applies. Look: stock Chain Heal SV 3659.',
    desc='Healing that arcs between up to $x1 injured allies, {pot1} each.', visual=_SV_CHAIN_HEAL,
)
scripted_by(frozen_chorus_damage_205731, 'spell_haunted_frozen_chorus_payout')
scripted_by(frozen_chorus_heal_205732, 'spell_haunted_frozen_chorus_payout')

frozen_chorus_205730 = _bonus(
    205730, 'Frozen Chorus',
    'Your damaging spells and direct heals have a $h% chance to call a wraith chorus that arcs between '
    f'{CHORUS_TARGETS} targets, dealing ' + pot_text(frozen_chorus_damage_205731)
    + ' Frost damage to each enemy or healing each injured ally for ' + pot_text(frozen_chorus_heal_205732)
    + '. This effect cannot occur more than once every 6 sec.',
    _ICON_FROSTBOLT,
    'Haunted set, The Elements 3 piece (Mail Intellect). spell_proc: done spells (0x14400: harmful magic, helpful '
    'magic or none), cast phase, 10% (x Proc Chance), 6 s internal cooldown. spell_haunted_frozen_chorus\'s CheckProc '
    'keeps casts with a direct damage or direct heal effect and a target; the payout is 205731 at a damaging cast\'s '
    'target or 205732 at a heal\'s.',
    proc_type_mask=_SPELLS, proc_chance=10,
)
procs_on(frozen_chorus_205730, proc_flags=_SPELLS, spell_phase_mask=_PROC_SPELL_PHASE_CAST, chance=10.0,
         cooldown_ms=6000)
scripted_by(frozen_chorus_205730, 'spell_haunted_frozen_chorus')

gathering_chorus_buff_205734 = _payout(
    205734, 'Gathering Chorus', School.FROST,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=CHORUS_STACK_PCT - 1,
            implicit_target_a=_TARGET_UNIT_CASTER)],
    _ICON_ICY_VEINS,
    'Haunted set, The Elements 5 piece: the stacks, up to 5 (CumulativeAura), 30 s, each crit refreshing. A DUMMY '
    'whose amount is the 20% per stack spell_haunted_frozen_chorus_payout reads; all are consumed when Frozen Chorus '
    'fires.',
    desc='Your next Frozen Chorus is $s1% stronger per stack.', aura_desc='Your next Frozen Chorus is stronger.',
    duration_ms=30000, range_yards=RANGE_SELF, defense=_DMG_CLASS_NONE, spell_level=0, CumulativeAura=5,
)

gathering_chorus_205733 = _bonus(
    205733, 'Gathering Chorus',
    'Your spell critical strikes, damage or healing, make your next Frozen Chorus $205734s1% stronger, stacking up '
    'to $205734u times. All stacks are consumed when Frozen Chorus fires.',
    _ICON_ICY_VEINS,
    'Haunted set, The Elements 5 piece (Mail Intellect). A PROC_TRIGGER_SPELL aura: done spells (0x14400), damage or '
    'heal type, hit phase, critical only, 100%: a stack of 205734 on the wearer. No script.',
    aura=AuraType.PROC_TRIGGER_SPELL, trigger=gathering_chorus_buff_205734.id, proc_type_mask=_SPELLS,
    proc_chance=100,
)
procs_on(gathering_chorus_205733, proc_flags=_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE | _PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_CRITICAL, chance=100.0)

# =====================================================================================================================
# Plate Intellect: Lightforge (188)

unbroken_faith_buff_205741 = _payout(
    205741, 'Unbroken Faith', School.HOLY,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=3,
            implicit_target_a=_TARGET_UNIT_CASTER),
     Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=3,
            misc_value=_SCHOOL_MASK_HOLY, implicit_target_a=_TARGET_UNIT_CASTER)],
    _ICON_DIVINE_PLEA,
    'Haunted set, Lightforge 3 piece: the buff while above 80% mana. Healing done +4% (base 3 + die 1), Holy damage '
    'done +4%. No duration: spell_haunted_unbroken_faith puts it on and takes it off. Visible, so the player sees '
    'when it holds.',
    desc='Healing and Holy damage increased by $s1%.', aura_desc='Healing and Holy damage increased.',
    duration_ms=-1, range_yards=RANGE_SELF, defense=_DMG_CLASS_NONE, spell_level=0, visual=_SV_DIVINE_PLEA,
)

unbroken_faith_205740 = _bonus(
    205740, 'Unbroken Faith',
    f'While you are above {UNBROKEN_FAITH_MANA_PCT}% mana, your heals and Holy damage are $205741s1% stronger.',
    _ICON_DIVINE_PLEA,
    'Haunted set, Lightforge 3 piece (Plate Intellect). A PERIODIC_DUMMY every 1 s: spell_haunted_unbroken_faith '
    'keeps 205741 on the wearer while mana is above 80% and removes it otherwise, and when the bonus goes.',
    aura=AuraType.PERIODIC_DUMMY, amplitude=1000,
)
scripted_by(unbroken_faith_205740, 'spell_haunted_unbroken_faith')

soul_released_heal_205743 = _payout(
    205743, 'Soul Released', School.HOLY,
    [_direct('heal', sp=100.0, effect=EffectType.HEAL, target=_TARGET_UNIT_TARGET_ALLY)], _ICON_HOLY_LIGHT,
    'Haunted set, Lightforge 5 piece: the freed soul\'s heal. Spell power potency 100 (heal), T 1.5 s. Look: stock '
    'Holy Light SV 2936.',
    desc='Heals the target for {pot1}.', visual=_SV_HOLY_LIGHT,
)
soul_released_damage_205744 = _payout(
    205744, 'Soul Released', School.HOLY,
    [_direct('direct', sp=100.0)], _ICON_EXORCISM,
    'Haunted set, Lightforge 5 piece: the freed soul\'s strike. Holy, spell power potency 100, T 1.5 s. Look: stock '
    'Exorcism SV 324.',
    desc='Deals {pot1} Holy damage.', visual=_SV_EXORCISM,
)

soul_released_205742 = _bonus(
    205742, 'Soul Released',
    'Your direct heals and Holy damage spells have a $h% chance to free a trapped soul, healing the most injured ally '
    f'within {SOUL_RELEASED_HEAL_RANGE} yards for ' + pot_text(soul_released_heal_205743)
    + f' and dealing ' + pot_text(soul_released_damage_205744) + ' Holy damage to the nearest enemy within '
    f'{SOUL_RELEASED_ENEMY_RANGE} yards. This effect cannot occur more than once every 4 sec.',
    _ICON_HOLY_LIGHT,
    'Haunted set, Lightforge 5 piece (Plate Intellect). spell_proc: done spells (0x14400), cast phase, 12% (x Proc '
    'Chance), 4 s internal cooldown. spell_haunted_soul_released\'s CheckProc keeps casts with a direct heal effect '
    'or a Holy direct damage effect; the payout heals the most injured group member or self within 30 yd (205743) '
    'and strikes the nearest enemy in combat with the wearer within 20 yd (205744), either half alone when the other '
    'has no target.',
    proc_type_mask=_SPELLS, proc_chance=12,
)
procs_on(soul_released_205742, proc_flags=_SPELLS, spell_phase_mask=_PROC_SPELL_PHASE_CAST, chance=12.0,
         cooldown_ms=4000)
scripted_by(soul_released_205742, 'spell_haunted_soul_released')

# =====================================================================================================================
# Plate Strength: Valor (189)

bone_shatter_burst_205751 = _payout(
    205751, 'Bone Shatter', School.NORMAL,
    [_direct('direct', ap=100.0, target=_TARGET_DEST_TARGET_ENEMY, implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY,
             radius_yards=8.0)],
    _ICON_BONE_SHIELD,
    'Haunted set, Valor 3 piece: the shards. Physical, every enemy within 8 yd of the ability\'s target (uncapped), '
    'attack power potency 100 each, T 1.5 s. DefenseType MELEE (melee crit, armor applies), NO_ACTIVE_DEFENSE. Look: '
    'stock Thunder Clap SV 145.',
    desc='Bone shards burst from the target, dealing {pot1} Physical damage to every enemy within $a1 yards of it.',
    attributes=_ATTR0_NO_ACTIVE_DEFENSE, visual=_SV_THUNDER_CLAP, defense=_DMG_CLASS_MELEE,
)

broken_bones_buff_205753 = _payout(
    205753, 'Broken Bones', School.NORMAL,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_ARMOR_PENETRATION_PCT, base_points=9,
            implicit_target_a=_TARGET_UNIT_CASTER)],
    _ICON_SUNDER_ARMOR,
    'Haunted set, Valor 5 piece: armor penetration +10% (SPELL_AURA_MOD_ARMOR_PENETRATION_PCT, base 9 + die 1; family '
    '0 and EquippedItemClass -1, so every attack: Unit::CalcArmorReducedDamage), 15 s, refreshed by the next Bone '
    'Shatter. Armor reduces only Physical damage, so Holy and magic damage gain nothing.',
    desc='Your armor penetration is increased by $s1%.', aura_desc='Armor penetration increased.',
    duration_ms=15000, range_yards=RANGE_SELF, defense=_DMG_CLASS_NONE, spell_level=0,
)

bone_shatter_205750 = _bonus(
    205750, 'Bone Shatter',
    'Your melee abilities have a $h% chance to burst bone shards from your target, dealing '
    + pot_text(bone_shatter_burst_205751) + ' Physical damage to every enemy within $205751a1 yards of it. This '
    'effect cannot occur more than once every 5 sec.',
    _ICON_BONE_SHIELD,
    'Haunted set, Valor 3 piece (Plate Strength). spell_proc: done melee-class spells (0x10), cast phase (one roll per '
    'ability, a cleave included), 10% (x Proc Chance), 5 s internal cooldown. spell_haunted_bone_shatter casts 205751 '
    'at the ability\'s target (the wearer\'s victim for a self-targeted ability), and Broken Bones 205753 on the '
    'wearer with the 5 piece 205752.',
    proc_type_mask=_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, proc_chance=10,
)
procs_on(bone_shatter_205750, proc_flags=_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, spell_phase_mask=_PROC_SPELL_PHASE_CAST,
         chance=10.0, cooldown_ms=5000)
scripted_by(bone_shatter_205750, 'spell_haunted_bone_shatter')

broken_bones_205752 = _bonus(
    205752, 'Broken Bones',
    'Each Bone Shatter increases your armor penetration by $205753s1% for $205753d.',
    _ICON_SUNDER_ARMOR,
    'Haunted set, Valor 5 piece (Plate Strength): a marker read by spell_haunted_bone_shatter (the buff is 205753).',
)

# =====================================================================================================================
# Mail Agility: Beaststalker's (186)

haunting_mark_debuff_205761 = _payout(
    205761, 'Haunting Mark', School.SHADOW,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=14,
            implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    _ICON_HUNTERS_MARK,
    'Haunted set, Beaststalker\'s 3 piece: the mark. A DUMMY debuff, 15 s, whose amount (15%, base 14 + die 1) '
    'HauntedSetUnitHooks::ModifySpellDamageTaken adds to the next melee or ranged ability of the mark\'s caster '
    'against the target, then removes the mark. Per caster. Look: stock Hunter\'s Mark SV 3239.',
    desc='Your next ability against the target deals $s1% more damage.', aura_desc='Haunted.',
    duration_ms=15000, attributes=_ATTR0_AURA_IS_DEBUFF, visual=_SV_HUNTERS_MARK, defense=_DMG_CLASS_NONE,
    spell_level=0,
)

haunting_mark_205760 = _bonus(
    205760, 'Haunting Mark',
    'Your melee and ranged abilities have a $h% chance to mark the target. Your next ability against it deals '
    '$205761s1% more damage. This effect cannot occur more than once every 4 sec.',
    _ICON_HUNTERS_MARK,
    'Haunted set, Beaststalker\'s 3 piece (Mail Agility). A PROC_TRIGGER_SPELL aura: done melee- and ranged-class '
    'spells (0x110), damage type, hit phase, normal or critical, 15% (x Proc Chance), 4 s internal cooldown: 205761 on '
    'the target. The ability that marks gains nothing (the mark lands after its damage).',
    aura=AuraType.PROC_TRIGGER_SPELL, trigger=haunting_mark_debuff_205761.id, proc_type_mask=_ABILITIES,
    proc_chance=15,
)
procs_on(haunting_mark_205760, proc_flags=_ABILITIES, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_HIT_OR_CRIT, chance=15.0, cooldown_ms=4000)

grasp_melee_205763 = _payout(
    205763, 'Grasp of the Dead', School.NORMAL,
    [_direct('direct', ap=120.0)], _ICON_RAISE_DEAD,
    'Haunted set, Beaststalker\'s 5 piece: the claw, after a melee ability. Physical, attack power potency 120, '
    'T 1.5 s, '
    'DefenseType MELEE, NO_ACTIVE_DEFENSE. Look: stock Death Coil SV 10755 (a placeholder for the ground claw).',
    desc='The dead claw up from the ground, dealing {pot1} Physical damage.', attributes=_ATTR0_NO_ACTIVE_DEFENSE,
    visual=_SV_DEATH_COIL, defense=_DMG_CLASS_MELEE,
)
grasp_ranged_205764 = _payout(
    205764, 'Grasp of the Dead', School.NORMAL,
    [_direct('direct', ap=120.0)], _ICON_RAISE_DEAD,
    'Haunted set, Beaststalker\'s 5 piece: the claw after a ranged ability. The same strike off ranged attack power: '
    'DefenseType RANGED and the ranged weapon subclass mask make the server add ranged attack power '
    '(SpellInfo::IsRangedWeaponSpell); EquippedItemClass -1 keeps the cast free of a weapon requirement (the '
    'Polkelt\'s '
    'Specimen Launcher shape).',
    desc='The dead claw up from the ground, dealing {pot1} Physical damage.', attributes=_ATTR0_NO_ACTIVE_DEFENSE,
    visual=_SV_DEATH_COIL, defense=_DMG_CLASS_RANGED, EquippedItemSubclass=_RANGED_WEAPON_SUBCLASS_MASK,
)

grasp_of_the_dead_205762 = _bonus(
    205762, 'Grasp of the Dead',
    'Your melee and ranged abilities have a $h% chance to make the dead claw up from the ground under your target, '
    'dealing ' + pot_text(grasp_melee_205763) + ' Physical damage. This effect cannot occur more than once every 4 '
    'sec.',
    _ICON_RAISE_DEAD,
    'Haunted set, Beaststalker\'s 5 piece (Mail Agility). spell_proc: done melee- and ranged-class spells (0x110), '
    'damage type, hit phase, normal or critical, 10% (x Proc Chance), 4 s internal cooldown. '
    'spell_haunted_grasp_of_the_dead casts 205764 after a ranged ability (ranged attack power) and 205763 after a '
    'melee '
    'one.',
    proc_type_mask=_ABILITIES, proc_chance=10,
)
procs_on(grasp_of_the_dead_205762, proc_flags=_ABILITIES, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_HIT_OR_CRIT, chance=10.0, cooldown_ms=4000)
scripted_by(grasp_of_the_dead_205762, 'spell_haunted_grasp_of_the_dead')

# =====================================================================================================================
# Leather Agility: Shadowcraft (184)

wraith_venom_dot_205771 = _payout(
    205771, 'Wraith Venom', School.SHADOW,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000, ap_potency=5.0,
            potency_kind='periodic', implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    _ICON_SHADOW_WORD_PAIN,
    'Haunted set, Shadowcraft 3 piece: the infection. Shadow damage every 2 s for 6 s, attack power potency 5 a tick '
    '(time basis = the tick: a rate of about 3% of a filler stream while it is up, and it is up most of the time). One '
    'per target per caster: a new infection refreshes it, never stacks. Its '
    'ticks are Shadow, not a bleed or a poison (no mechanic, Dispel none), so they never infect again. DefenseType '
    'MAGIC. Look: stock Shadow Word: Pain SV 71.',
    desc='Deals {pot1} Shadow damage every $t1 sec for $d.', aura_desc='Taking Shadow damage over time.',
    duration_ms=6000, attributes=_ATTR0_AURA_IS_DEBUFF, visual=_SV_SHADOW_WORD_PAIN,
)

wraith_venom_205770 = _bonus(
    205770, 'Wraith Venom',
    f'Your poison damage and bleed ticks, Instant Poison included, have a {WRAITH_VENOM_PCT}% chance to infect the '
    'target with Wraith Venom, dealing ' + pot_text(wraith_venom_dot_205771, variant='total')
    + f' Shadow damage over $205771d. This effect cannot occur more than once every {WRAITH_VENOM_ICD_S} sec.',
    _ICON_SHADOW_WORD_PAIN,
    'Haunted set, Shadowcraft 3 piece (Leather Agility): a marker. Poisons roll nothing by the shared rogue rule, so '
    'HauntedSetUnitHooks rolls it on every rogue poison damage hit (Rogue::IsRoguePoisonDamage: direct, Instant '
    'Poison, and periodic) and every bleed tick (mechanic bleed: rogue Garrote, Rupture, cat Rake, Rip) the wearer '
    'deals: 8% times Proc Chance, 2 s internal cooldown per wearer (a spell cooldown on this id), then 205771 on the '
    'target, cast next update.',
)

grave_rot_strike_205773 = _payout(
    205773, 'Grave Rot', School.SHADOW,
    [_direct('direct', ap=15.0)], _ICON_CORRUPTION,
    'Haunted set, Shadowcraft 5 piece: the wraith reopening the wound. Shadow, attack power potency 15, T 1.5 s (on a '
    'rogue the 3 s cooldown sets its rate, about every 3 to 4 s), '
    'DefenseType MAGIC. Look: stock Corruption SV 8629.',
    desc='Deals {pot1} Shadow damage.', visual=_SV_CORRUPTION,
)

grave_rot_205772 = _bonus(
    205772, 'Grave Rot',
    f'Your poison damage and bleed ticks have a {GRAVE_ROT_PCT}% chance to call a wraith that reopens the wound, '
    'dealing ' + pot_text(grave_rot_strike_205773) + f' Shadow damage, and your bleeds, damage-over-time poisons and '
    f'Wraith Venom on the target last {GRAVE_ROT_EXTEND_S} sec longer, up to {GRAVE_ROT_EXTEND_CAP_S} sec per '
    f'application. This effect cannot occur more than once every {GRAVE_ROT_ICD_S} sec.',
    _ICON_CORRUPTION,
    'Haunted set, Shadowcraft 5 piece (Leather Agility): a marker. HauntedSetUnitHooks rolls it on the same events as '
    'Wraith Venom: 6% times Proc Chance, 3 s internal cooldown per wearer, then 205773 on the target and +2 s '
    '(duration '
    'and maximum duration, so the last-tick fold stays right) on every bleed, rogue poison and Wraith Venom aura the '
    'wearer has on it, at most +6 s per application of each (user ruling 2026-11-06; tracked per target and aura, a '
    'refresh or a reapplication starts a fresh 6 s).',
)

# =====================================================================================================================
# Leather Tank: Protector's (1000)

grave_hide_205780 = _bonus(
    205780, 'Grave Hide',
    'Your Stamina is increased by $s1%.',
    _ICON_UNBREAKABLE_ARMOR,
    'Haunted set, Protector\'s 3 piece (Leather Tank). MOD_TOTAL_STAT_PERCENTAGE, Stamina (misc 2), +3% (base 2 + '
    'die 1). No script.',
    aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE, base_points=2, misc_value=_STAT_STAMINA,
)

bone_ward_absorb_205782 = _payout(
    205782, 'Bone Ward', School.SHADOW,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, base_points=0, misc_value=_ALL_SCHOOLS,
            implicit_target_a=_TARGET_UNIT_CASTER,
            potency_excluded='percent of maximum health per stack, set by spell_haunted_bone_ward')],
    _ICON_BONE_SHIELD,
    'Haunted set, Protector\'s 5 piece: the ward. Absorbs all schools, 10 s, up to 3 stacks (CumulativeAura), each '
    'new stack refreshing the ward. spell_haunted_bone_ward sets the amount to 3% of maximum health per stack (a '
    'restack recalculates it, so the ward is full again). Look: stock Bone Shield SV 11539.',
    desc='Absorbs damage.', aura_desc='Absorbs damage.', duration_ms=10000, range_yards=RANGE_SELF,
    visual=_SV_BONE_SHIELD, defense=_DMG_CLASS_NONE, spell_level=0, CumulativeAura=3,
)
scripted_by(bone_ward_absorb_205782, 'spell_haunted_bone_ward')

bone_ward_205781 = _bonus(
    205781, 'Bone Ward',
    f'When you dodge, you gain a Bone Ward that absorbs damage equal to {BONE_WARD_PCT}% of your maximum health for '
    '$205782d, stacking up to $205782u times. This effect cannot occur more than once every 1 sec.',
    _ICON_BONE_SHIELD,
    'Haunted set, Protector\'s 5 piece (Leather Tank). A PROC_TRIGGER_SPELL aura: taken melee auto attacks and '
    'melee-class spells (0x28), dodge only, 100%, 1 s internal cooldown: a stack of 205782.',
    aura=AuraType.PROC_TRIGGER_SPELL, trigger=bone_ward_absorb_205782.id, proc_type_mask=_TAKEN_MELEE,
    proc_chance=100,
)
procs_on(bone_ward_205781, proc_flags=_TAKEN_MELEE, hit_mask=_PROC_HIT_DODGE, chance=100.0, cooldown_ms=1000)

# =====================================================================================================================
# Plate Tank: Shadowguard (1001)

spirit_bulwark_heal_205791 = _payout(
    205791, 'Spirit Bulwark', School.HOLY,
    [Effect(type=EffectType.HEAL_PCT, base_points=0, implicit_target_a=_TARGET_UNIT_CASTER,
            potency_excluded='percent of maximum health (SPELL_EFFECT_HEAL_PCT)')],
    _ICON_HOLY_SHIELD,
    'Haunted set, Shadowguard 3 piece: heals the wearer for 1% of maximum health (HEAL_PCT, base 0 + die 1).',
    desc='Heals you for $s1% of your maximum health.', range_yards=RANGE_SELF, defense=_DMG_CLASS_NONE,
    spell_level=0,
)

spirit_bulwark_205790 = _bonus(
    205790, 'Spirit Bulwark',
    'Blocking or parrying an attack heals you for $205791s1% of your maximum health. This effect cannot occur more '
    'than once every 1 sec.',
    _ICON_HOLY_SHIELD,
    'Haunted set, Shadowguard 3 piece (Plate Tank). A PROC_TRIGGER_SPELL aura: taken melee auto attacks and '
    'melee-class spells (0x28), block or parry, 100%, 1 s internal cooldown: 205791.',
    aura=AuraType.PROC_TRIGGER_SPELL, trigger=spirit_bulwark_heal_205791.id, proc_type_mask=_TAKEN_MELEE,
    proc_chance=100,
)
procs_on(spirit_bulwark_205790, proc_flags=_TAKEN_MELEE, hit_mask=_PROC_HIT_BLOCK | _PROC_HIT_PARRY, chance=100.0,
         cooldown_ms=1000)

deathless_hot_205793 = _payout(
    205793, 'Deathless', School.SHADOW,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_OBS_MOD_HEALTH, base_points=4, amplitude=2000,
            implicit_target_a=_TARGET_UNIT_CASTER,
            potency_excluded='percent of maximum health per tick (SPELL_AURA_OBS_MOD_HEALTH)')],
    _ICON_VAMPIRIC_BLOOD,
    'Haunted set, Shadowguard 5 piece: the dead rise in you. SPELL_AURA_OBS_MOD_HEALTH: 5% of maximum health (base 4 '
    '+ die 1) every 2 s for 6 s, 15% in all. Look: stock Vampiric Blood SV 11149.',
    desc='Heals you for $s1% of your maximum health every $t1 sec for $d.', aura_desc='Healing.',
    duration_ms=6000, range_yards=RANGE_SELF, visual=_SV_VAMPIRIC_BLOOD, defense=_DMG_CLASS_NONE, spell_level=0,
)

deathless_205792 = _bonus(
    205792, 'Deathless',
    f'When a hit takes you below {DEATHLESS_HEALTH_PCT}% health, the dead rise in you, healing you for '
    '$205793o1% of your maximum health over $205793d. This effect cannot occur more than once every 60 sec.',
    _ICON_VAMPIRIC_BLOOD,
    'Haunted set, Shadowguard 5 piece (Plate Tank). spell_proc: taken damage (0x100000), 100%, 60 s internal '
    'cooldown. spell_haunted_deathless\'s CheckProc passes only the hit that takes the wearer from 35% health or more '
    'to below 35% (alive), so the cooldown starts only then: 205793.',
    proc_type_mask=_PROC_FLAG_TAKEN_DAMAGE, proc_chance=100,
)
procs_on(deathless_205792, proc_flags=_PROC_FLAG_TAKEN_DAMAGE, chance=100.0, cooldown_ms=60000)
scripted_by(deathless_205792, 'spell_haunted_deathless')

# The set bonuses by ItemSet id: (3 piece, 5 piece). source/items/haunted_set.py builds the ItemSet rows from it.
SET_BONUSES = {
    181: (wraith_volley_205700, soul_rend_205702),
    182: (soul_shroud_205710, wraith_of_solace_205712),
    184: (wraith_venom_205770, grave_rot_205772),
    185: (lingering_death_205720, grave_bloom_205721),
    186: (haunting_mark_205760, grasp_of_the_dead_205762),
    187: (frozen_chorus_205730, gathering_chorus_205733),
    188: (unbroken_faith_205740, soul_released_205742),
    189: (bone_shatter_205750, broken_bones_205752),
    1000: (grave_hide_205780, bone_ward_205781),
    1001: (spirit_bulwark_205790, deathless_205792),
}
