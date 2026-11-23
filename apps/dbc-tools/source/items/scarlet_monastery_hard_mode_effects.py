"""
The twelve Scarlet Monastery hard mode item effects (designer text: docs/dungeons/scarlet-monastery-rework.md ## Loot,
"Hard mode lists", approved 2026-11-19, ruling 59; copied in dungeon-loot-vanilla.md): Bloodmage Thalnos, the
Desecration (Pureblood's Rallying Standard, Fairbell's Censer, Voss's Blessed Signet), Arcanist Doan, the Kel'Thuzad
Heresy (Shard of the Phylactery, Heretic's Wand, Fissure-touched Grips), Herod, Call to Arms (Scarlet Garrison Rifle,
Garrison Bulwark, Staff of the Consecrated Hall) and High Inquisitor Whitemane, The Truth (Father's Verdict, Treads of
Denial, Inquisitor's Rosary). After the Blackrock Depths precedent (blackrock_depths_hard_mode_effects.py).

Every damage, healing and absorb number comes from potency (user rule: everything on potency). The effects that grow
with item level are declared with scale="budget" on the item (scarlet_monastery_hard_mode.py): every tier above the
hard mode ladder's 71 carries its own copies (lib/item_spell_copies.py), so a script casts its tier's copy
(ItemSpellCopies::Resolve). The Shard's 10% and the Rosary's Versatility are percents that stay the same on every
tier (the Shard still scales: its absorb is a potency line); the Rallying Standard's 5% and Denial's 10% grow with the
tier (review m5, 2026-11-20: `Effect(scale_amount=True)` on their tier copies). The scripts are
modules/mod-dungeon-bosses src/ScarletMonastery/hard_mode_items.cpp (ids mirrored in
ScarletMonasteryHardModeItemsLogic.h); the banner look is source/npcs/scarlet_monastery/hard_mode_items.py (creature
300880).

One shared script (Systems.md section 5, "A cast rolls once"):
  spell_sm_one_roll_per_cast  on every cast-triggered proc aura (Censer, Signet, Wand, Grips, Rifle, Staff): the proc
                              check lets each cast reach the spell_proc roll once, so an area spell is one roll, not
                              one per target (the Scholomance Bonechill Blade's guard). The Verdict and the Rosary
                              carry the same guard in their own scripts.

Area payouts (designer ruling B8, 2026-11-20): a short-range area (about 10 yd) hits every enemy in it, in combat or
not; only a long-reach one (about 30 yd) would keep an in-combat filter. All three here are short: Shadow Fissure 6 yd,
Garrison Volley 5 yd and the Verdict's extra targets 8 yd, so none filters.

Ids: the `scarlet_monastery_items` reservation 212000-212099 (source/ids.yaml); this file takes 212000-212023.

Bloodmage Thalnos, the Desecration
  212000  Pureblood's Rallying Standard  Use (2 min, off the GCD): 15 sec, a PERIODIC_DUMMY every 1 sec, radius 10 yd.
                                  Scaled per tier (review m5): the tier's copies of 212000 and 212001.
                                  spell_sm_pureblood_rallying_standard plants Galvar's banner (300880) at the wearer's
                                  feet; every second the wearer's party members (the wearer included) within 10 yd of
                                  the banner get 212001, unless they carry another player's 212002. A member buffed
                                  for the first time gets 212002 from the wearer. The banner and the buffs leave with
                                  the aura.
  212001  Rallied                 +5% damage done, all schools, 2 sec (refreshed every second near the banner); the
                                  percent grows with the tier (scale_amount: 5 / 5 / 6 / 6).
  212002  Recently Rallied        the 2 min lockout debuff: "Cannot benefit from a Rallying Standard." One spell for
                                  every tier (so any standard's lockout locks out every other); kept through death and
                                  immunities (the Sated attributes, review m3).
  212003  Fairbell's Censer       Equip: PROC_TRIGGER_SPELL. Landed damaging spells (magic and none class), 20%, no
                                  internal cooldown (the stack needs procs), one roll per cast; cast 212004 on the
                                  target.
  212004  Penitent Fire           Fire, 8 sec, a tick every 2 sec, spell power potency 12 a tick (48 a stack), stacks
                                  to 3, each new stack refreshes the duration.
  212005  Voss's Blessed Signet   Equip: PROC_TRIGGER_SPELL. Landed direct heals, 20%, 6 sec internal cooldown, one
                                  roll per cast; cast 212006 on the healed target.
  212006  Voss's Blessing         absorbs all schools for 6 sec, base potency 60 (a set amount, no spell power).

Arcanist Doan, the Kel'Thuzad Heresy
  212007  Shard of the Phylactery  Use (2 min, off the GCD): 15 sec, an absorb (base potency 150) plus +10% spell
                                  damage (every school but Physical) and +10% healing done. A depleted absorb removes
                                  the whole aura (Unit.cpp), so the bonus ends with the shield. Data only.
  212008  Heretic's Wand          Equip: PROC_TRIGGER_SPELL. Landed damaging spells, 20%, no internal cooldown (a
                                  refreshing debuff), one roll per cast; cast 212009 on the target.
  212009  Icy Death               Frost, 8 sec, a tick every 2 sec, spell power potency 18 a tick, 30% slower movement
                                  (mechanic snare). A refresh, not a stack.
  212010  Fissure-touched Grips   Equip: PROC_TRIGGER_SPELL. Landed melee-class abilities (no auto attacks; any
                                  ability, finishers included, designer 2026-11-19), 20%, 6 sec internal cooldown, one
                                  roll per cast; cast 212011 at the target.
  212011  Shadow Fissure          Shadow, every enemy within 6 yd of the target, attack power potency 90.

Herod, Call to Arms
  212012  Scarlet Garrison Rifle  Equip: PROC_TRIGGER_SPELL. Landed ranged auto attacks and ranged-class abilities,
                                  15%, 6 sec internal cooldown, one roll per cast; cast 212013 at the target.
  212013  Garrison Volley         Physical, every enemy within 5 yd of the target, ranged attack power potency
                                  90 (DefenseType RANGED and the ranged weapon subclass mask, so the server adds ranged
                                  attack power and the tooltip reads $RAP).
  212014  Garrison Bulwark        Equip: PROC_TRIGGER_SPELL. Taken melee attacks the wearer blocked (hit mask BLOCK),
                                  20%, 6 sec internal cooldown; cast 212015 on the wearer. Data only.
  212015  Pillar of Light         a heal on the wearer, attack power potency 100 (a Strength tank shield).
  212016  Staff of the Consecrated Hall  Equip: PROC_TRIGGER_SPELL. Landed direct heals, 15%, 6 sec internal cooldown,
                                  one roll per cast; cast 212017 at the healed target.
  212017  Consecrated Pillar      a heal on every party member within 5 yd of the healed target, healing potency 70.

High Inquisitor Whitemane, The Truth
  212018  Father's Verdict        Equip: a passive DUMMY proc aura, amount 2 = the other enemies, radius 8 yd. Landed
                                  melee hits (auto attacks and melee-class abilities), 15%, 6 sec internal cooldown, one
                                  roll per cast. spell_sm_fathers_verdict casts the tier's 212019 on the target and on
                                  the two nearest other enemies within 8 yd in front of the wearer (a cleave,
                                  not a line, designer 2026-11-19).
  212019  Verdict                 Holy, one enemy, attack power potency 100.
  212020  Treads of Denial        Equip: PROC_TRIGGER_SPELL. Taken melee attacks the wearer parried (hit mask PARRY),
                                  25%, 10 sec internal cooldown; cast 212021 on the wearer. Data only.
  212021  Denial                  10% less damage taken, all schools, 6 sec; the percent grows with the tier
                                  (scale_amount: 10 / 11 / 11 / 13; review m5).
  212022  Inquisitor's Rosary     Equip: a passive DUMMY proc aura, amount 50 = the health threshold in percent. Landed
                                  direct heals on another player below 50% health before the heal, 25%, 10 sec internal
                                  cooldown, one roll per cast. spell_sm_inquisitors_rosary casts 212023 on the healer
                                  and on the healed player.
  212023  Inquisitor's Resolve    +3% Versatility (aura 306 MOD_CUSTOM_STAT_PCT, Systems.md: never MOD_RATING), 8 sec
                                  (designer 2026-11-19: Versatility for both, not healing taken).
  212024-212099  spare

Chances, internal cooldowns, potencies, radii and durations are proposals waiting for the designer (STAGE-SM-HM report,
designer questions). None of the looks were checked in game.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import pot_text, procs_on, scripted_by, spell

_TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}

# Implicit targets (SharedDefines.h Targets)
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_UNIT_DEST_AREA_PARTY = 34
_TARGET_DEST_TARGET_ENEMY = 53
_TARGET_DEST_TARGET_ANY = 63

_ATTR0_PASSIVE = 0x00000040
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR0_NO_IMMUNITIES = 0x20000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000
_ATTR4_NO_CAST_LOG = 0x00000001

_DMG_CLASS_MAGIC = 1
_DMG_CLASS_RANGED = 3
_MECHANIC_SNARE = 11
_SCHOOL_MASK_ALL = 127
_SCHOOL_MASK_SPELLS = 126       # every school but Physical: "your spells"
_RANGED_WEAPON_SUBCLASS_MASK = (1 << 2) | (1 << 3) | (1 << 18) | (1 << 16)  # bow, gun, crossbow, thrown
_CR_VERSATILITY = 1 << 21       # aura 306 misc value (CombatRating.VERSATILITY as a bit)
_AURA_MOD_CUSTOM_STAT_PCT = int(AuraType.MOD_CUSTOM_STAT_PCT)

# spell_proc (SpellMgr.h)
_PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x00000004
_PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK = 0x00000008
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS = 0x00000020
_PROC_FLAG_DONE_RANGED_AUTO_ATTACK = 0x00000040
_PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS = 0x00000100
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG = 0x00001000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x00010000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_TYPE_HEAL = 0x2
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_NORMAL_OR_CRITICAL = 0x1 | 0x2
_PROC_HIT_PARRY = 0x20
_PROC_HIT_BLOCK = 0x40

_MELEE_HITS = _PROC_FLAG_DONE_MELEE_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS
_MELEE_ABILITIES = _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS
_RANGED_HITS = _PROC_FLAG_DONE_RANGED_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
_HARMFUL_SPELLS = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG
_HELPFUL_SPELLS = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS
_TAKEN_MELEE = _PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK | _PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS

# Stock looks and icons, picked by name from Spell.dbc (none checked in game yet).
_ICON_BATTLE_STANDARD = 1691    # Battle Standard 23034
_SV_IMMOLATE = 46               # Immolate 348
_ICON_IMMOLATE = 31
_SV_POWER_WORD_SHIELD = 784     # Power Word: Shield 17
_ICON_POWER_WORD_SHIELD = 566
_SV_ICE_BARRIER = 4302          # Ice Barrier 11426
_ICON_UNSTABLE_AFFLICTION = 2039  # a dark shard
_SV_FROSTBOLT_VOLLEY = 13       # Frostbolt Volley 8398 (the Doan section doc's Icy Death fallback look)
_ICON_FROST_FEVER = 3142        # Frost Fever 55095
_SV_SHADOW_FISSURE = 12678      # Shadow Fissure 27810 (the Doan section doc's fissure look)
_ICON_SHADOW_FISSURE = 1468
_SV_VOLLEY = 10384              # Volley 1510
_ICON_VOLLEY = 126
_SV_BEAM_OF_LIGHT = 12479       # Beam of Light 57772 (the Herod section doc's pillar of Light)
_ICON_HOLY_SHIELD = 453         # Holy Shield 20925
_ICON_BEACON_OF_LIGHT = 3032    # Beacon of Light 53563
_SV_DIVINE_STORM = 12006        # Divine Storm 53385
_ICON_DIVINE_STORM = 3027
_SV_DIVINE_PROTECTION = 11817   # Divine Protection 498
_ICON_DIVINE_PROTECTION = 73
_SV_POWER_INFUSION = 7553       # Power Infusion 10060
_ICON_POWER_INFUSION = 1872

# An off-GCD proc payout's time basis (the Deadmines items' precedent). A periodic payout keeps the tick as its time
# basis.
_PROC_PAYOUT_MS = 1500

_STANDARD_RADIUS = 10.0
_FISSURE_RADIUS = 6.0
_VOLLEY_RADIUS = 5.0
_PILLAR_RADIUS = 5.0
_VERDICT_RADIUS = 8.0

_ROLL_ONCE = 'spell_sm_one_roll_per_cast'


def _raw(desc: str = '', aura_desc: str = '', spell_level: int = 0, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': spell_level, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_TEXT_MASKS, **more}


def _off_gcd() -> dict:
    return {'StartRecoveryCategory': 0, 'StartRecoveryTime': 0}


def _equip_aura(spell_id: int, name: str, school: int, effects: list, desc: str, icon: int, notes: str, *,
                proc_type_mask: int = 0, proc_chance: int = 0) -> object:
    """A passive Equip aura on the wearer (an item's equip spell)."""
    return spell(
        id=spell_id, name=name, school=school, attributes=_ATTR0_PASSIVE, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=effects, spell_icon_id=icon, notes=notes,
        raw_overrides=_raw(desc, ProcTypeMask=proc_type_mask, ProcChance=proc_chance),
    )


def _trigger(trigger_spell: int) -> list:
    """A PROC_TRIGGER_SPELL effect on the wearer that casts `trigger_spell` (on the proc's other side)."""
    return [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, base_points=0,
                   trigger_spell=trigger_spell, implicit_target_a=_TARGET_UNIT_CASTER)]


# =====================================================================================================================
# Hard mode: Bloodmage Thalnos, the Desecration (the four risen heroes)

# --- Pureblood's Rallying Standard (trinket, Use) --------------------------------------------------------------------

rallied_212001 = spell(
    id=212001, name='Rallied', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=2000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=4,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_TARGET_ALLY, scale_amount=True)],
    spell_icon_id=_ICON_BATTLE_STANDARD,
    notes='Scarlet Monastery hard mode, Pureblood\'s Rallying Standard: the buff near the banner. +5% damage done, all '
          'schools (BasePoints 4 + DieSides 1), 2 s; spell_sm_pureblood_rallying_standard refreshes it every second '
          'on each party member within the banner\'s 10 yd (Unit::AddAura from the wearer, so the caster is the '
          'wearer) and removes it when the banner falls. Each tier has its own copy (reached by 212000\'s $212001s1) '
          'and the percent grows with the tier (scale_amount; review m5, 2026-11-20).',
    raw_overrides=_raw('Damage done increased by $s1%.', 'Rallied: damage done increased.',
                       AttributesEx4=_ATTR4_NO_CAST_LOG),
)

recently_rallied_212002 = spell(
    id=212002, name='Recently Rallied', school=School.HOLY,
    attributes=_ATTR0_AURA_IS_DEBUFF | _ATTR0_NO_IMMUNITIES, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=120000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ALLY)],
    spell_icon_id=_ICON_BATTLE_STANDARD,
    notes='Scarlet Monastery hard mode, Pureblood\'s Rallying Standard: the lockout (designer 2026-11-19: two '
          'standards in one group don\'t stack). A 2 min DUMMY debuff (AURA_IS_DEBUFF, so it cannot be clicked off), '
          'put on a player the first time a standard buffs them, cast by that standard\'s wearer; another wearer\'s '
          'standard skips a player who carries it. Never refreshed (the 2 min run from the first buff). Sated\'s '
          'attributes (review m3): NO_IMMUNITIES, so a school immunity (Divine Shield, Ice Block, Cloak of Shadows) '
          'cannot purge it, and ALLOW_AURA_WHILE_DEAD, so death does not clear it. One spell for every tier: 212000\'s '
          'text names the 2 min as a literal, not $212002d, so the tier copies never copy it and any standard\'s '
          'lockout blocks every other standard.',
    raw_overrides=_raw(aura_desc='Cannot benefit from a Rallying Standard.', AttributesEx4=_ATTR4_NO_CAST_LOG,
                       AttributesEx3=_ATTR3_ALLOW_AURA_WHILE_DEAD),
)

pureblood_rallying_standard_212000 = spell(
    id=212000, name="Pureblood's Rallying Standard", school=School.HOLY, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=15000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, base_points=0, amplitude=1000,
                    implicit_target_a=_TARGET_UNIT_CASTER, radius_yards=_STANDARD_RADIUS)],
    spell_icon_id=_ICON_BATTLE_STANDARD,
    notes='Scarlet Monastery hard mode, Pureblood\'s Rallying Standard (Bloodmage Thalnos, trinket), the Use: 2 min '
          'cooldown, off the GCD, 15 s. A PERIODIC_DUMMY every 1 s, radius 10 yd. '
          'spell_sm_pureblood_rallying_standard plants Galvar\'s banner (creature 300880) at the wearer\'s feet on '
          'apply and pulses at once, then every second: each party member (the wearer\'s subgroup, the wearer '
          'included) alive within 10 yd of the banner gets 212001, unless they carry another wearer\'s 212002; one '
          'without any 212002 gets it from this wearer first. The banner and the 212001 buffs leave with the aura. '
          'A positive aura on the caster, so the bots\' "use trinket" action takes it. Scaled per tier (review m5): '
          'the item declares scale="budget", so each tier above 71 has copies of 212000 and 212001 (the lockout '
          'stays one spell, see 212002).',
    raw_overrides=_raw(
        'Plant Galvar\'s banner for $d. You and party members within $a1 yd of it deal $212001s1% more damage. Each '
        'player it rallies cannot benefit from another Rallying Standard for 2 min.',
        'A Rallying Standard is planted.', **_off_gcd(),
    ),
)
scripted_by(pureblood_rallying_standard_212000, 'spell_sm_pureblood_rallying_standard')

# --- Fairbell's Censer (held in off-hand, Equip) ---------------------------------------------------------------------

penitent_fire_212004 = spell(
    id=212004, name='Penitent Fire', school=School.FIRE, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=8000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000,
                    sp_potency=12.0, potency_kind='periodic', implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_IMMOLATE,
    notes='Scarlet Monastery hard mode, Fairbell\'s Censer: the penitent fire, cast by the wearer (triggered by '
          '212003). Fire, 8 s, a tick every 2 s, spell power potency 12 a tick (time basis = the tick; 48 a stack). '
          'Stacks to 3 (CumulativeAura; the engine multiplies the tick by the stacks), each new stack refreshes the '
          'duration. DefenseType MAGIC. Look: stock Immolate SV 46.',
    raw_overrides=_raw('Deals {pot1} Fire damage every $t1 sec for $d. Stacks up to $u times.', 'Burning in penitent '
                       'fire.', spell_level=1, CumulativeAura=3, DefenseType=_DMG_CLASS_MAGIC,
                       SpellVisualID_1=_SV_IMMOLATE),
)

fairbells_censer_212003 = _equip_aura(
    212003, "Fairbell's Censer", School.FIRE, _trigger(penitent_fire_212004.id),
    'Your damaging spells have a chance to set the target alight in penitent fire, dealing '
    + pot_text(penitent_fire_212004, variant='total') + ' Fire damage over $212004d. Stacks up to $212004u times.',
    _ICON_IMMOLATE,
    'Scarlet Monastery hard mode, Fairbell\'s Censer (Bloodmage Thalnos, held in off-hand), the Equip: a passive '
    'PROC_TRIGGER_SPELL aura that casts 212004 on the target. spell_proc: done harmful magic and none class spells, '
    'damage type, hit phase, normal or critical, 20%, no internal cooldown (the stack needs procs). '
    'spell_sm_one_roll_per_cast lets each cast roll once.',
    proc_type_mask=_HARMFUL_SPELLS, proc_chance=20,
)
procs_on(fairbells_censer_212003, proc_flags=_HARMFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=20.0)
scripted_by(fairbells_censer_212003, _ROLL_ONCE)

# --- Voss's Blessed Signet (ring, Equip) -----------------------------------------------------------------------------

voss_blessing_212006 = spell(
    id=212006, name="Voss's Blessing", school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=6000,
    # rebase_exempt: scales with item level, not the potency rebase (level60-stat-curve LS5b)
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, rebase_exempt=True,
                    base_potency=60.0,
                    potency_kind='absorb', misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_TARGET_ALLY)],
    spell_icon_id=_ICON_POWER_WORD_SHIELD,
    notes='Scarlet Monastery hard mode, Voss\'s Blessed Signet: the shield, cast by the healer (triggered by 212005) '
          'on the healed target. Absorbs all schools for 6 s. A set amount: base potency 60 (about 650 at level 60), '
          'no spell power (an absorb only gets spell power from a script; the Stratholme Ysida\'s Ward precedent); '
          'the tier copies scale it. Look: stock Power Word: Shield SV 784.',
    raw_overrides=_raw('Absorbs {pot1} damage.', 'Absorbs damage.', spell_level=1,
                       SpellVisualID_1=_SV_POWER_WORD_SHIELD),
)

voss_blessed_signet_212005 = _equip_aura(
    212005, "Voss's Blessed Signet", School.HOLY, _trigger(voss_blessing_212006.id),
    'Your direct heals have a chance to shield the target, absorbing ' + pot_text(voss_blessing_212006)
    + ' damage for $212006d.',
    _ICON_POWER_WORD_SHIELD,
    'Scarlet Monastery hard mode, Voss\'s Blessed Signet (Bloodmage Thalnos, ring), the Equip: a passive '
    'PROC_TRIGGER_SPELL aura that casts 212006 on the healed target. spell_proc: done positive magic and none class '
    'spells (0x4400), heal type, hit phase (direct heals only: a heal over time\'s ticks are periodic), normal or '
    'critical, 20%, 6 s internal cooldown (the shield\'s length). spell_sm_one_roll_per_cast lets each cast roll once.',
    proc_type_mask=_HELPFUL_SPELLS, proc_chance=20,
)
procs_on(voss_blessed_signet_212005, proc_flags=_HELPFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=20.0,
         cooldown_ms=6000)
scripted_by(voss_blessed_signet_212005, _ROLL_ONCE)

# =====================================================================================================================
# Hard mode: Arcanist Doan, the Kel'Thuzad Heresy

# --- Shard of the Phylactery (trinket, Use) --------------------------------------------------------------------------

shard_of_the_phylactery_212007 = spell(
    id=212007, name='Shard of the Phylactery', school=School.SHADOW, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=15000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=_SCHOOL_MASK_ALL,
               rebase_exempt=True,  # scales with item level, not the potency rebase (level60-stat-curve LS5b)
               base_potency=150.0, potency_kind='absorb', implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=9,
               misc_value=_SCHOOL_MASK_SPELLS, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=9,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_UNSTABLE_AFFLICTION,
    notes='Scarlet Monastery hard mode, Shard of the Phylactery (Arcanist Doan, trinket), the Use: 2 min cooldown, off '
          'the GCD, 15 s. Effect 1 absorbs all schools (base potency 150, about 1,600 at level 60, no spell power; '
          'the tier copies scale it); effects 2 and 3 +10% damage done for every school but Physical and +10% '
          'healing done (BasePoints 9 + DieSides 1). A depleted absorb removes the whole aura (Unit.cpp; the '
          'Scholomance Honor Roll precedent), so the bonus ends with the shield. Data only. A positive aura on the '
          'caster, so the bots\' "use trinket" action takes it. Look: stock Ice Barrier SV 4302.',
    raw_overrides=_raw(
        'The shard absorbs {pot1} damage for $d. While it holds, your spells deal $s2% more damage and healing.',
        'The phylactery shard holds: spell damage and healing increased.', spell_level=1,
        SpellVisualID_1=_SV_ICE_BARRIER, **_off_gcd(),
    ),
)

# --- Heretic's Wand (wand, Equip) ------------------------------------------------------------------------------------

icy_death_212009 = spell(
    id=212009, name='Icy Death', school=School.FROST, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=8000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000, sp_potency=18.0,
               potency_kind='periodic', implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-31,
               mechanic=_MECHANIC_SNARE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_FROST_FEVER,
    notes='Scarlet Monastery hard mode, Heretic\'s Wand: Icy Death, cast by the wearer (triggered by 212008). Frost, '
          '8 s, a tick every 2 s, spell power potency 18 a tick (time basis = the tick); 30% slower movement '
          '(BasePoints -31 + DieSides 1, mechanic snare so slow immunity applies). A new proc refreshes it (no '
          'stacks). DefenseType MAGIC. Look: stock Frostbolt Volley SV 13 (the Doan section doc\'s Icy Death look).',
    raw_overrides=_raw('Deals {pot1} Frost damage every $t1 sec and slows movement by $s2% for $d.',
                       'Icy Death: taking Frost damage, movement slowed.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_FROSTBOLT_VOLLEY),
)

heretics_wand_212008 = _equip_aura(
    212008, "Heretic's Wand", School.FROST, _trigger(icy_death_212009.id),
    'Your damaging spells have a chance to apply Icy Death, dealing ' + pot_text(icy_death_212009, variant='total')
    + ' Frost damage over $212009d and slowing the target\'s movement by $212009s2%.',
    _ICON_FROST_FEVER,
    'Scarlet Monastery hard mode, Heretic\'s Wand (Arcanist Doan, wand), the Equip: a passive PROC_TRIGGER_SPELL aura '
    'that casts 212009 on the target. spell_proc: done harmful magic and none class spells (the wand\'s own Shoot is '
    'ranged class: not counted), damage type, hit phase, normal or critical, 20%, no internal cooldown (a refresh, '
    'not a stack). spell_sm_one_roll_per_cast lets each cast roll once.',
    proc_type_mask=_HARMFUL_SPELLS, proc_chance=20,
)
procs_on(heretics_wand_212008, proc_flags=_HARMFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=20.0)
scripted_by(heretics_wand_212008, _ROLL_ONCE)

# --- Fissure-touched Grips (leather hands, Equip) --------------------------------------------------------------------

shadow_fissure_212011 = spell(
    id=212011, name='Shadow Fissure', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=90.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_DEST_TARGET_ENEMY,
                    implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=_FISSURE_RADIUS)],
    spell_icon_id=_ICON_SHADOW_FISSURE,
    notes='Scarlet Monastery hard mode, Fissure-touched Grips: the fissure, cast by the wearer (triggered by 212010) '
          'at the target. Shadow, every enemy within 6 yd of the target, in combat or not (TARGET_DEST_TARGET_ENEMY / '
          'TARGET_UNIT_DEST_AREA_ENEMY; designer ruling B8: a short area hits everyone). Attack power potency 90, '
          'T 1.5 s (an off-GCD payout; the Lake Lord\'s Slam\'s number). DefenseType MAGIC. SUPPRESS_CASTER_PROCS. '
          'Look: stock Shadow Fissure SV 12678 (the Doan section doc\'s fissure).',
    raw_overrides=_raw('Deals {pot1} Shadow damage to enemies within $a1 yd of the target.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_SHADOW_FISSURE,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

fissure_touched_grips_212010 = _equip_aura(
    212010, 'Fissure-touched Grips', School.SHADOW, _trigger(shadow_fissure_212011.id),
    'Your melee abilities have a chance to open a Shadow Fissure under the target, dealing '
    + pot_text(shadow_fissure_212011) + ' Shadow damage to enemies within $212011a1 yd of it.',
    _ICON_SHADOW_FISSURE,
    'Scarlet Monastery hard mode, Fissure-touched Grips (Arcanist Doan, leather hands), the Equip: a passive '
    'PROC_TRIGGER_SPELL aura that casts 212011 at the target. spell_proc: done melee-class spells only (0x10: any '
    'melee ability, finishers included, no auto attacks; designer 2026-11-19), damage type, hit phase, normal or '
    'critical, 20%, 6 s internal cooldown (an area payout). spell_sm_one_roll_per_cast lets each cast roll once.',
    proc_type_mask=_MELEE_ABILITIES, proc_chance=20,
)
procs_on(fissure_touched_grips_212010, proc_flags=_MELEE_ABILITIES, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=20.0,
         cooldown_ms=6000)
scripted_by(fissure_touched_grips_212010, _ROLL_ONCE)

# =====================================================================================================================
# Hard mode: Herod, Call to Arms

# --- Scarlet Garrison Rifle (gun, Equip) -----------------------------------------------------------------------------

garrison_volley_212013 = spell(
    id=212013, name='Garrison Volley', school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=90.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_DEST_TARGET_ENEMY,
                    implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=_VOLLEY_RADIUS)],
    spell_icon_id=_ICON_VOLLEY,
    notes='Scarlet Monastery hard mode, Scarlet Garrison Rifle: the garrison volley, cast by the wearer (triggered by '
          '212012) at the target. Physical, every enemy within 5 yd of the target, in combat or not (designer ruling '
          'B8). Ranged attack power potency 90, T 1.5 s: DefenseType RANGED and the ranged weapon '
          'subclass mask make SpellInfo::IsRangedWeaponSpell true, so the server adds ranged attack power and the '
          'tooltip reads $RAP; EquippedItemClass -1 keeps the cast free of any weapon requirement (the Scholomance '
          'acid pool precedent). SUPPRESS_CASTER_PROCS. Look: stock Volley SV 10384.',
    raw_overrides=_raw('Deals {pot1} Physical damage to enemies within $a1 yd of the target.', spell_level=1,
                       DefenseType=_DMG_CLASS_RANGED, EquippedItemSubclass=_RANGED_WEAPON_SUBCLASS_MASK,
                       SpellVisualID_1=_SV_VOLLEY, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

scarlet_garrison_rifle_212012 = _equip_aura(
    212012, 'Scarlet Garrison Rifle', School.NORMAL, _trigger(garrison_volley_212013.id),
    'Your ranged attacks have a chance to call a garrison volley, dealing ' + pot_text(garrison_volley_212013)
    + ' Physical damage to the target and enemies within $212013a1 yd of it.',
    _ICON_VOLLEY,
    'Scarlet Monastery hard mode, Scarlet Garrison Rifle (Herod, gun), the Equip: a passive PROC_TRIGGER_SPELL aura '
    'that casts 212013 at the target. spell_proc: done ranged auto attacks and ranged-class spells (0x140), damage '
    'type, hit phase, normal or critical, 15%, 6 s internal cooldown (an area payout). spell_sm_one_roll_per_cast '
    'lets each cast roll once (Multi-Shot is one roll).',
    proc_type_mask=_RANGED_HITS, proc_chance=15,
)
procs_on(scarlet_garrison_rifle_212012, proc_flags=_RANGED_HITS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=15.0,
         cooldown_ms=6000)
scripted_by(scarlet_garrison_rifle_212012, _ROLL_ONCE)

# --- Garrison Bulwark (shield, Equip) --------------------------------------------------------------------------------

pillar_of_light_212015 = spell(
    id=212015, name='Pillar of Light', school=School.HOLY, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, ap_potency=144.0, potency_kind='heal', time_basis_ms=_PROC_PAYOUT_MS,
                    implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_HOLY_SHIELD,
    notes='Scarlet Monastery hard mode, Garrison Bulwark: the pillar of Light on the wearer, cast by the wearer '
          '(triggered by 212014). A heal, attack power potency 100 (a Strength tank shield; SpellHealingBonusDone adds '
          'the AP coefficient, the Fury heal precedent), T 1.5 s. DefenseType MAGIC so the bonus applies. '
          'SUPPRESS_CASTER_PROCS. Look: stock Beam of Light SV 12479 (the Herod section doc\'s pillar).'
          ' Effect 1 ap_potency 100.0 -> 144.0 (2026-11-21, level60-stat-curve round S9: targeted trims after S8, user '
          'ruling: attack-power heals and absorbs option A (restore the pre-rebase level), x1.44).',
    raw_overrides=_raw('Heals you for {pot1}.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       SpellVisualID_1=_SV_BEAM_OF_LIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

garrison_bulwark_212014 = _equip_aura(
    212014, 'Garrison Bulwark', School.HOLY, _trigger(pillar_of_light_212015.id),
    'Your blocks have a chance to call a pillar of Light on you, healing you for ' + pot_text(pillar_of_light_212015)
    + '.',
    _ICON_HOLY_SHIELD,
    'Scarlet Monastery hard mode, Garrison Bulwark (Herod, shield), the Equip: a passive PROC_TRIGGER_SPELL aura that '
    'casts 212015 on the wearer. spell_proc: taken melee auto attacks and melee-class spells (0x28), hit mask BLOCK, '
    '20%, 6 s internal cooldown (the Black Anvil Bulwark\'s shape). Data only, no script.',
    proc_type_mask=_TAKEN_MELEE, proc_chance=20,
)
procs_on(garrison_bulwark_212014, proc_flags=_TAKEN_MELEE, hit_mask=_PROC_HIT_BLOCK, chance=20.0, cooldown_ms=6000)

# --- Staff of the Consecrated Hall (staff, Equip) --------------------------------------------------------------------

consecrated_pillar_212017 = spell(
    id=212017, name='Consecrated Pillar', school=School.HOLY, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, sp_potency=70.0, potency_kind='heal', time_basis_ms=_PROC_PAYOUT_MS,
                    implicit_target_a=_TARGET_DEST_TARGET_ANY, implicit_target_b=_TARGET_UNIT_DEST_AREA_PARTY,
                    radius_yards=_PILLAR_RADIUS)],
    spell_icon_id=_ICON_BEACON_OF_LIGHT,
    notes='Scarlet Monastery hard mode, Staff of the Consecrated Hall: the pillar of Light, cast by the healer '
          '(triggered by 212016) at the healed target. Heals every party member within 5 yd of it, the target '
          'included when it is one (TARGET_DEST_TARGET_ANY / TARGET_UNIT_DEST_AREA_PARTY). Healing potency 70, '
          'T 1.5 s. DefenseType MAGIC so spell power adds. SUPPRESS_CASTER_PROCS. Look: stock Beam of Light SV 12479.',
    raw_overrides=_raw('Heals party members within $a1 yd of the target for {pot1}.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_BEAM_OF_LIGHT,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

staff_of_the_consecrated_hall_212016 = _equip_aura(
    212016, 'Staff of the Consecrated Hall', School.HOLY, _trigger(consecrated_pillar_212017.id),
    'Your direct heals have a chance to call a pillar of Light on the target, healing it and party members within '
    '$212017a1 yd for ' + pot_text(consecrated_pillar_212017) + '.',
    _ICON_BEACON_OF_LIGHT,
    'Scarlet Monastery hard mode, Staff of the Consecrated Hall (Herod, staff), the Equip: a passive '
    'PROC_TRIGGER_SPELL aura that casts 212017 at the healed target. spell_proc: done positive magic and none class '
    'spells (0x4400), heal type, hit phase (direct heals only), normal or critical, 15%, 6 s internal cooldown (an '
    'area payout). spell_sm_one_roll_per_cast lets each cast roll once.',
    proc_type_mask=_HELPFUL_SPELLS, proc_chance=15,
)
procs_on(staff_of_the_consecrated_hall_212016, proc_flags=_HELPFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=15.0,
         cooldown_ms=6000)
scripted_by(staff_of_the_consecrated_hall_212016, _ROLL_ONCE)

# =====================================================================================================================
# Hard mode: High Inquisitor Whitemane, The Truth

# --- Father's Verdict (two-hand sword, Equip) ------------------------------------------------------------------------

verdict_212019 = spell(
    id=212019, name='Verdict', school=School.HOLY, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=100.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_DIVINE_STORM,
    notes='Scarlet Monastery hard mode, Father\'s Verdict: one enemy\'s share of the cleave, cast by the wearer '
          '(triggered) from spell_sm_fathers_verdict on the target and on up to two other enemies in front. Holy, '
          'attack power potency 100, T 1.5 s (a two-hander\'s slower swings). DefenseType MAGIC. '
          'SUPPRESS_CASTER_PROCS. Look: stock Divine Storm SV 12006.',
    raw_overrides=_raw('Deals {pot1} Holy damage.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       SpellVisualID_1=_SV_DIVINE_STORM, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

fathers_verdict_212018 = _equip_aura(
    212018, "Father's Verdict", School.HOLY,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=1,
            implicit_target_a=_TARGET_UNIT_CASTER, radius_yards=_VERDICT_RADIUS)],
    'Your melee hits have a chance to swing the Verdict, a cleave of Holy light dealing ' + pot_text(verdict_212019)
    + ' Holy damage to the target and up to $s1 other enemies in front of you within $a1 yd.',
    _ICON_DIVINE_STORM,
    'Scarlet Monastery hard mode, Father\'s Verdict (High Inquisitor Whitemane, two-hand sword), the Equip: a passive '
    'DUMMY aura with a proc, amount 2 (BasePoints 1 + DieSides 1) = the other enemies, radius 8 yd. spell_proc: done '
    'melee auto attacks and melee-class spells (0x14), damage type, hit phase, normal or critical, 15%, 6 s internal '
    'cooldown. spell_sm_fathers_verdict (one roll per cast) casts the tier\'s 212019 on the target, then on the '
    'nearest other enemies within 8 yd in the wearer\'s front half, in combat or not (designer ruling B8, '
    '2026-11-20; designer 2026-11-19: a cleave, not a '
    'line).',
    proc_type_mask=_MELEE_HITS, proc_chance=15,
)
procs_on(fathers_verdict_212018, proc_flags=_MELEE_HITS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=15.0,
         cooldown_ms=6000)
scripted_by(fathers_verdict_212018, 'spell_sm_fathers_verdict')

# --- Treads of Denial (plate feet, Equip) ----------------------------------------------------------------------------

denial_212021 = spell(
    id=212021, name='Denial', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=6000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-11,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_CASTER, scale_amount=True)],
    spell_icon_id=_ICON_DIVINE_PROTECTION,
    notes='Scarlet Monastery hard mode, Treads of Denial: the buff, cast by the wearer (triggered by 212020). '
          'MOD_DAMAGE_PERCENT_TAKEN -10 (BasePoints -11 + DieSides 1), all schools, 6 s. Each tier has its own copy '
          '(212020\'s trigger) and the percent grows with the tier (scale_amount; review m5, 2026-11-20). Look: '
          'stock Divine Protection SV 11817.',
    raw_overrides=_raw('Damage taken reduced by $s1% for $d.', 'Denial: damage taken reduced.',
                       SpellVisualID_1=_SV_DIVINE_PROTECTION, AttributesEx4=_ATTR4_NO_CAST_LOG),
)

treads_of_denial_212020 = _equip_aura(
    212020, 'Treads of Denial', School.HOLY, _trigger(denial_212021.id),
    'Your parries have a chance to grant Denial, reducing damage taken by $212021s1% for $212021d.',
    _ICON_DIVINE_PROTECTION,
    'Scarlet Monastery hard mode, Treads of Denial (High Inquisitor Whitemane, plate feet), the Equip: a passive '
    'PROC_TRIGGER_SPELL aura that casts 212021 on the wearer. spell_proc: taken melee auto attacks and melee-class '
    'spells (0x28), hit mask PARRY, 25%, 10 s internal cooldown (parries rise with the number of attackers; at most '
    '60% uptime). Data only, no script.',
    proc_type_mask=_TAKEN_MELEE, proc_chance=25,
)
procs_on(treads_of_denial_212020, proc_flags=_TAKEN_MELEE, hit_mask=_PROC_HIT_PARRY, chance=25.0, cooldown_ms=10000)

# --- Inquisitor's Rosary (neck, Equip) -------------------------------------------------------------------------------

inquisitors_resolve_212023 = spell(
    id=212023, name="Inquisitor's Resolve", school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=8000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_CUSTOM_STAT_PCT, base_points=2,
                    misc_value=_CR_VERSATILITY, implicit_target_a=_TARGET_UNIT_TARGET_ALLY)],
    spell_icon_id=_ICON_POWER_INFUSION,
    notes='Scarlet Monastery hard mode, Inquisitor\'s Rosary: the buff, cast by the healer (triggered) from '
          'spell_sm_inquisitors_rosary on the healer and on the healed player. +3% Versatility (aura 306 '
          'MOD_CUSTOM_STAT_PCT, misc 1 << CR_VERSATILITY, BasePoints 2 + DieSides 1; Systems.md: custom stats by '
          'aura 306, never MOD_RATING), 8 s. A percent: one spell for every tier. Look: stock Power Infusion SV 7553.',
    raw_overrides=_raw('Versatility increased by $s1% for $d.', 'Inquisitor\'s Resolve: Versatility increased.',
                       SpellVisualID_1=_SV_POWER_INFUSION, AttributesEx4=_ATTR4_NO_CAST_LOG),
)

inquisitors_rosary_212022 = _equip_aura(
    212022, "Inquisitor's Rosary", School.HOLY,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=49,
            implicit_target_a=_TARGET_UNIT_CASTER)],
    'Your heals on an ally below $s1% health have a chance to raise your Versatility and theirs by $212023s1% for '
    '$212023d.',
    _ICON_POWER_INFUSION,
    'Scarlet Monastery hard mode, Inquisitor\'s Rosary (High Inquisitor Whitemane, neck), the Equip: a passive DUMMY '
    'aura with a proc, amount 50 (BasePoints 49 + DieSides 1) = the health threshold in percent. spell_proc: done '
    'positive magic and none class spells (0x4400), heal type, hit phase (direct heals), normal or critical, 25%, '
    '10 s internal cooldown. spell_sm_inquisitors_rosary\'s check (run before the roll) passes a heal on another '
    'player whose health before the heal was below the threshold, once per cast; the proc casts 212023 on the healer '
    'and on the healed player (designer 2026-11-19: Versatility for both, not healing taken).',
    proc_type_mask=_HELPFUL_SPELLS, proc_chance=25,
)
procs_on(inquisitors_rosary_212022, proc_flags=_HELPFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=25.0,
         cooldown_ms=10000)
scripted_by(inquisitors_rosary_212022, 'spell_sm_inquisitors_rosary')
