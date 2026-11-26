"""
The three Gnomeregan hard mode item effects (designer text: docs/dungeons/gnomeregan-rework.md ## Loot, "Hard mode:
Mekgineer Thermaplugg, the Whole Workshop", approved 2026-11-24, rulings 56 to 58): Leaking Reactor Core, Walking Bomb
Launcher and Master Punch Card. After the Zul'Farrak precedent (zul_farrak_hard_mode_effects.py).

Both damage numbers come from potency (user rule: everything on potency). All three items are scale="budget"
(gnomeregan_hard_mode.py): every tier above the hard mode ladder's 71 carries its own copies (lib/item_spell_copies.py)
of Meltdown (its damage done percent, `scale_amount=True`, the Scarlet Monastery review m5 precedent) and its pulse, of
the Launcher, its mark and its blast, and of the Card and Clearance: PRISMATIC (MOD_RATING, a stat aura, so its
ratings grow by themselves). A script casts its tier's copy (ItemSpellCopies::Resolve). Punched stays one spell for
every tier: it carries no number, so no tooltip names its id. The scripts are modules/mod-dungeon-bosses
src/Gnomeregan/hard_mode_items.cpp (ids mirrored in GnomereganHardModeItemsLogic.h); the Walking Bomb's look is
source/npcs/gnomeregan/hard_mode_items.py (creature 301100).

Ids: the `gnomeregan_items` reservation 214240-214279 (source/ids.yaml); this file takes 214240-214247.

  214240  Meltdown                Use (2 min, off the GCD): 15 sec on the wearer. Effect 1 MOD_DAMAGE_PERCENT_DONE +15
                                  (all schools; grows with the tier: 15 / 16 / 17 / 19), effect 2 PERIODIC_TRIGGER_SPELL
                                  every 3 sec (five pulses of 214241), effect 3 MOD_DAMAGE_PERCENT_TAKEN +20 (all
                                  schools; the same on every tier: the risk). Cannot be cancelled.
  214241  Radiation Pulse         Nature, every enemy in combat within 8 yd of the wearer, attack power potency 50.
                                  spell_gnomer_item_meltdown_pulse is the in-combat filter.
  214242  Walking Bomb Launcher   Equip: a passive proc aura, effect 1 DUMMY amount 3 = the fuse, in yards (how close
                                  to its target the bomb blows). Landed ranged auto attacks and ranged-class abilities
                                  that crit, 35%, 10 sec internal cooldown, one roll per cast.
                                  spell_gnomer_item_walking_bomb_launcher puts the tier's 214243 on the target and sends
                                  a Launched Walking Bomb (301100) running at it from beside the wearer.
  214243  Walking Bomb            the mark on the target, 8 sec, a PERIODIC_DUMMY every 0.5 sec (amount 3 = the fuse).
                                  spell_gnomer_item_walking_bomb: at the fuse the wearer casts the tier's 214244 where
                                  the bomb stands; the bomb falls apart when the mark ends any other way (the target
                                  died, it ran out, the wearer left).
  214244  Walking Bomb Blast      Fire, every enemy in combat within 8 yd of the bomb, ranged attack power potency 150.
                                  spell_gnomer_item_walking_bomb_blast is the in-combat filter.
  214245  Master Punch Card       Equip: a passive proc aura, effect 1 DUMMY amount 5 = the punches Clearance needs,
                                  effect 2 DUMMY amount 30 = the seconds the card cannot be punched after Clearance.
                                  The wearer's own casts, cast phase, 100%. spell_gnomer_item_master_punch_card punches
                                  each different spell once (its first rank; not triggered, not an item's, not an auto
                                  attack, Auto Shot, Shoot or Throw).
  214246  Punched                 the punches on the wearer, up to 5, no duration. No effect of its own.
  214247  Clearance: PRISMATIC    10 sec on the wearer: haste rating +50 and critical strike rating +70 (MOD_RATING, the
                                  stock melee + ranged + spell masks; 5% each at level 60; they grow with the tier).
  214248-214279  spare

In-combat filter: both damage effects reach only enemies already in combat (designer text, handoff section 5), so
neither pulls a pack. The Scarlet and Ragefire short areas (ruling B8, 1A) do not filter: a designer question, as on
Zul'Farrak.

Every number is a proposal waiting for the designer (STAGE-GG-HM report). None of the looks were checked in game.
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
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_SRC_CASTER = 22
_TARGET_DEST_DEST = 87

_ATTR0_PASSIVE = 0x00000040
_ATTR0_NO_AURA_CANCEL = 0x80000000
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_ATTR5_ALWAYS_AOE_LINE_OF_SIGHT = 0x04000000  # the cast skips the wearer-to-spot sight check; targets still need
                                              # sight of the spot

_DMG_CLASS_MAGIC = 1
_SCHOOL_MASK_ALL = 127
# bow, gun, crossbow, thrown (SpellInfo::IsRangedWeaponSpell): the server adds ranged attack power and the tooltip
# reads $RAP; EquippedItemClass -1 keeps the cast free of any weapon requirement (the Scarlet Garrison Rifle
# precedent, scarlet_monastery_hard_mode_effects.py)
_RANGED_WEAPON_SUBCLASS_MASK = (1 << 2) | (1 << 3) | (1 << 18) | (1 << 16)
# CombatRating masks: CR_HASTE_MELEE | CR_HASTE_RANGED | CR_HASTE_SPELL (the stock haste rating auras' value, Kiss of
# the Spider 28866) and CR_CRIT_MELEE | CR_CRIT_RANGED | CR_CRIT_SPELL
_HASTE_RATING_MASK = (1 << 17) | (1 << 18) | (1 << 19)
_CRIT_RATING_MASK = (1 << 8) | (1 << 9) | (1 << 10)

# spell_proc (SpellMgr.h)
_PROC_FLAG_DONE_RANGED_AUTO_ATTACK = 0x00000040
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS = 0x00000100
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG = 0x00001000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x00010000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_TYPE_MASK_ALL = 0x7
_PROC_SPELL_PHASE_CAST = 0x1
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_CRITICAL = 0x2

_RANGED_HITS = _PROC_FLAG_DONE_RANGED_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
# Every kind of spell the wearer casts (the cast phase event a non-triggered cast raises, Spell::_cast): melee, ranged,
# magic and none class, helpful or harmful. No auto attack flag.
_OWN_CASTS = (_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS | _PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
              | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG
              | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG)

# Stock looks and icons, read from Spell.dbc and SpellIcon by name (none checked in game yet).
_SV_RADIATION_AURA = 1725       # Radiation 9798 (the Gnomeregan irradiated trash's glow)
_SV_RADIATION_PULSE = 1713      # Radiation 9770
_SV_WALKING_BOMB_EFFECT = 5619  # Walking Bomb Effect 11504 (the stock bomb's blast; the dungeon doc's)
_SV_PRISMATIC_FORM = 653        # Prismatic Form 4933-4936
_ICON_POWER_CORE = 2303         # INV_Gizmo_KhoriumPowerCore
_ICON_CORPSE_EXPLODE = 160      # Spell_Shadow_CorpseExplode (Radiation 9769 / 9798)
_ICON_BOMB = 2565               # INV_Misc_Bomb_01
_ICON_PUNCH_CARD_PRISMATIC = 2921  # INV_Misc_PunchCards_Prismatic
_ICON_PUNCH_CARD_YELLOW = 2683  # INV_Misc_PunchCards_Yellow
_ICON_PRISMATIC_CLOAK = 2126    # Spell_Arcane_PrismaticCloak

# An off-GCD payout's time basis (the Deadmines items' precedent).
_PROC_PAYOUT_MS = 1500

_MELTDOWN_MS = 15000
_MELTDOWN_DAMAGE_PCT = 15
_MELTDOWN_TAKEN_PCT = 20
_PULSE_MS = 3000
_PULSE_RADIUS = 8.0
_FUSE_YARDS = 3
_BOMB_MS = 8000
_BOMB_TICK_MS = 500
_BLAST_RADIUS = 8.0
_PUNCHES = 5
_CARD_LOCK_SEC = 30
_CLEARANCE_MS = 10000
_CLEARANCE_HASTE_RATING = 50    # at level 60, 10 rating = 1% haste
_CLEARANCE_CRIT_RATING = 70     # at level 60, 14 rating = 1% crit


def _raw(desc: str = '', aura_desc: str = '', spell_level: int = 0, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': spell_level, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_TEXT_MASKS, **more}


def _dummy(amount: int, **more) -> Effect:
    """A DUMMY aura on the caster whose amount is `amount` (BasePoints + the 1 of the die)."""
    return Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=amount - 1,
                  implicit_target_a=_TARGET_UNIT_CASTER, **more)


def _equip_aura(spell_id: int, name: str, school: int, effects: list, desc: str, icon: int, notes: str, *,
                proc_type_mask: int, proc_chance: int) -> object:
    """A passive Equip aura on the wearer (an item's equip spell)."""
    return spell(
        id=spell_id, name=name, school=school, attributes=_ATTR0_PASSIVE, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=effects, spell_icon_id=icon, notes=notes,
        raw_overrides=_raw(desc, ProcTypeMask=proc_type_mask, ProcChance=proc_chance),
    )


# =====================================================================================================================
# Hard mode: Mekgineer Thermaplugg, the Whole Workshop

# --- Leaking Reactor Core (trinket, Use) -----------------------------------------------------------------------------

radiation_pulse_214241 = spell(
    id=214241, name='Radiation Pulse', school=School.NATURE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=50.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_SRC_CASTER,
                    implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=_PULSE_RADIUS)],
    spell_icon_id=_ICON_CORPSE_EXPLODE,
    notes='Gnomeregan hard mode, Leaking Reactor Core: one pulse of Meltdown, cast by the wearer (triggered by '
          '214240\'s tick every 3 s). Nature, every enemy in combat within 8 yd of the wearer (TARGET_SRC_CASTER / '
          'TARGET_UNIT_SRC_AREA_ENEMY; spell_gnomer_item_meltdown_pulse drops the ones out of combat). Attack power '
          'potency 50, T 1.5 s (a Strength trinket; Meltdown\'s own damage bonus applies to it too). DefenseType '
          'MAGIC. '
          'SUPPRESS_CASTER_PROCS and NO_REFLECTION: a pulse procs nothing. Look: stock Radiation SV 1713.',
    raw_overrides=_raw('Deals {pot1} Nature damage to enemies in combat within $a1 yd.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_RADIATION_PULSE,
                       AttributesEx=_ATTR1_NO_REFLECTION, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)
scripted_by(radiation_pulse_214241, 'spell_gnomer_item_meltdown_pulse')

meltdown_214240 = spell(
    id=214240, name='Meltdown', school=School.NATURE, attributes=_ATTR0_NO_AURA_CANCEL, cast_time_ms=0,
    cooldown_ms=120000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_MELTDOWN_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
               base_points=_MELTDOWN_DAMAGE_PCT - 1, misc_value=_SCHOOL_MASK_ALL,
               implicit_target_a=_TARGET_UNIT_CASTER, scale_amount=True),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, base_points=0,
               amplitude=_PULSE_MS, trigger_spell=radiation_pulse_214241.id, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
               base_points=_MELTDOWN_TAKEN_PCT - 1, misc_value=_SCHOOL_MASK_ALL,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_POWER_CORE,
    notes='Gnomeregan hard mode, Leaking Reactor Core (Mekgineer Thermaplugg, the Whole Workshop, trinket), the Use: '
          '2 min cooldown, off the GCD, a visible 15 s self buff. Effect 1 MOD_DAMAGE_PERCENT_DONE +15 (BasePoints 14 '
          '+ DieSides 1, all schools 127; scale_amount: 15 / 16 / 17 / 19 on the four tiers). Effect 2 '
          'PERIODIC_TRIGGER_SPELL every 3 s: 214241 at 3, 6, 9, 12 and 15 s. Effect 3 MOD_DAMAGE_PERCENT_TAKEN +20 '
          '(all schools; a percent, the same on every tier: the risk is the same at every item level). '
          'NO_AURA_CANCEL: the wearer cannot drop the risk early. A positive spell (the damage taken aura is not '
          'one SpellInfo::_IsPositiveEffect calls negative), so the bots\' "use trinket" action takes it. Look: '
          'stock Radiation SV 1725 (the irradiated trash\'s glow).',
    raw_overrides=_raw(
        'Vent the reactor for $d: you deal $s1% more damage and pulse ' + pot_text(radiation_pulse_214241)
        + ' Nature damage to enemies in combat within $214241a1 yd every $t2 sec, but you take $s3% more damage.',
        'Meltdown: dealing $s1% more damage and leaking radiation. Taking $s3% more damage.',
        SpellVisualID_1=_SV_RADIATION_AURA, StartRecoveryCategory=0, StartRecoveryTime=0,
    ),
)

# --- Walking Bomb Launcher (gun, Equip) ------------------------------------------------------------------------------

walking_bomb_blast_214244 = spell(
    id=214244, name='Walking Bomb Blast', school=School.FIRE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=150.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_DEST_DEST,
                    implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=_BLAST_RADIUS)],
    spell_icon_id=_ICON_BOMB,
    notes='Gnomeregan hard mode, Walking Bomb Launcher: the bomb\'s blast, cast by the wearer (triggered by the mark '
          '214243\'s tick) at the spot where the bomb stands (TARGET_DEST_DEST, the script gives the spot). Fire, '
          'every enemy in combat within 8 yd of the spot (TARGET_UNIT_DEST_AREA_ENEMY; '
          'spell_gnomer_item_walking_bomb_blast drops the ones out of combat). Ranged attack power potency 150, T '
          '1.5 s: the ranged weapon subclass mask makes SpellInfo::IsRangedWeaponSpell true, so the server adds '
          'ranged attack power and the tooltip reads $RAP; EquippedItemClass -1 keeps the cast free of any weapon '
          'requirement. DefenseType MAGIC (spell crit; a ranged or melee class payout would consume the Haunted '
          'set\'s Haunting Mark). Range 100 and ALWAYS_AOE_LINE_OF_SIGHT: the wearer need not see the spot, each '
          'target needs sight of it. SUPPRESS_CASTER_PROCS and NO_REFLECTION: a blast procs nothing and never rolls '
          'another bomb. Look: stock Walking Bomb Effect SV 5619.',
    raw_overrides=_raw('Deals {pot1} Fire damage to enemies in combat within $a1 yd.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, EquippedItemSubclass=_RANGED_WEAPON_SUBCLASS_MASK,
                       SpellVisualID_1=_SV_WALKING_BOMB_EFFECT, AttributesEx=_ATTR1_NO_REFLECTION,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS, AttributesEx5=_ATTR5_ALWAYS_AOE_LINE_OF_SIGHT),
)
scripted_by(walking_bomb_blast_214244, 'spell_gnomer_item_walking_bomb_blast')

walking_bomb_214243 = spell(
    id=214243, name='Walking Bomb', school=School.FIRE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_BOMB_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, base_points=_FUSE_YARDS - 1,
                    amplitude=_BOMB_TICK_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_BOMB,
    notes='Gnomeregan hard mode, Walking Bomb Launcher: the mark on the bomb\'s target, cast by the wearer (triggered '
          'by 214242). 8 s, a PERIODIC_DUMMY every 0.5 s, amount 3 (BasePoints 2 + DieSides 1) = the fuse in yards. '
          'spell_gnomer_item_walking_bomb holds the bomb (301100) the Launcher sent: when the bomb is within the fuse '
          'of the target the wearer casts the tier\'s 214244 where the bomb stands; when the mark ends any other way '
          '(the target died or left combat, 8 s ran out, the wearer is gone) the bomb falls apart. No damage, no '
          'threat of its own. DispelType none. SUPPRESS_CASTER_PROCS. No look of its own (the bomb is the look). It '
          'names 214244 in its text so the blast is in its copy family (each tier\'s mark casts its own blast).',
    raw_overrides=_raw('A Walking Bomb is coming for you. It blows when it arrives, dealing '
                       + pot_text(walking_bomb_blast_214244) + ' Fire damage to enemies within $214244a1 yd.',
                       'A Walking Bomb is coming.', spell_level=1,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)
scripted_by(walking_bomb_214243, 'spell_gnomer_item_walking_bomb')

walking_bomb_launcher_214242 = _equip_aura(
    214242, 'Walking Bomb Launcher', School.FIRE, [_dummy(_FUSE_YARDS)],
    'Your ranged critical strikes have a chance to launch a Walking Bomb at your target. It blows when it arrives, '
    'dealing ' + pot_text(walking_bomb_blast_214244) + ' Fire damage to enemies in combat within $214244a1 yd of it. '
    'It falls apart if its target dies or it has not arrived within $214243d.',
    _ICON_BOMB,
    'Gnomeregan hard mode, Walking Bomb Launcher (Mekgineer Thermaplugg, the Whole Workshop, gun), the Equip: a '
    'passive aura with a proc. Effect 1 DUMMY amount 3 (BasePoints 2 + DieSides 1) = the fuse in yards (the mark '
    'carries its own copy). spell_proc: done ranged auto attacks and ranged-class spells (0x140), damage type, hit '
    'phase, critical only, 35%, 10 s internal cooldown (an area payout; longer than a bomb lives, so a wearer has one '
    'bomb at most). spell_gnomer_item_walking_bomb_launcher lets each cast roll once (Multi-Shot is one roll), puts '
    'the tier\'s 214243 on the target and runs a Launched Walking Bomb (301100, look only: not selectable, not '
    'attackable, passive, 0.6 scale, 8 yd/s, MoveFollow) at it from beside the wearer. Item auras get no Proc Chance '
    '(Systems.md section 5).',
    proc_type_mask=_RANGED_HITS, proc_chance=35,
)
procs_on(walking_bomb_launcher_214242, proc_flags=_RANGED_HITS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_CRITICAL, chance=35.0, cooldown_ms=10000)
scripted_by(walking_bomb_launcher_214242, 'spell_gnomer_item_walking_bomb_launcher')

# --- Master Punch Card (trinket, Equip) ------------------------------------------------------------------------------

clearance_prismatic_214247 = spell(
    id=214247, name='Clearance: PRISMATIC', school=School.ARCANE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_CLEARANCE_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_RATING, base_points=_CLEARANCE_HASTE_RATING - 1,
               misc_value=_HASTE_RATING_MASK, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_RATING, base_points=_CLEARANCE_CRIT_RATING - 1,
               misc_value=_CRIT_RATING_MASK, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_PRISMATIC_CLOAK,
    notes='Gnomeregan hard mode, Master Punch Card: Clearance, cast by the wearer (triggered) from '
          'spell_gnomer_item_master_punch_card at the fifth punch. 10 s: haste rating +50 (MOD_RATING, the stock '
          'melee + ranged + spell haste mask 917504) and critical strike rating +70 (MOD_RATING, mask 1792): 5% each '
          'at level 60. MOD_RATING is a stat aura, so each tier\'s copy carries its own ratings (53 / 74, 55 / 78, '
          '63 / 88). Haste and Crit are stock ratings (Systems.md section 2 keeps aura 306 for the four custom '
          'stats). SUPPRESS_CASTER_PROCS. Look: stock Prismatic Form SV 653.',
    raw_overrides=_raw('Increases your haste rating by $s1 and your critical strike rating by $s2 for $d.',
                       'Clearance: PRISMATIC. Haste rating increased by $s1, critical strike rating by $s2.',
                       spell_level=1, SpellVisualID_1=_SV_PRISMATIC_FORM,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

punched_214246 = spell(
    id=214246, name='Punched', school=School.ARCANE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1, effects=[_dummy(1)],
    spell_icon_id=_ICON_PUNCH_CARD_YELLOW,
    notes='Gnomeregan hard mode, Master Punch Card: the punches on the wearer, cast by '
          'spell_gnomer_item_master_punch_card, one stack per punch, up to 5 (CumulativeAura). No duration: punches '
          'stay through combat and out of it until Clearance clears them. The card script treats fewer stacks than '
          'punches (death, a cancel) as a cleared card, and clears them when the card is put on or taken off (a login '
          'reloads the stacks but not which spells punched them). No effect of its own.',
    raw_overrides=_raw('Punched.', 'Punch card: each different spell you cast punches it.', spell_level=1,
                       CumulativeAura=_PUNCHES, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

master_punch_card_214245 = _equip_aura(
    214245, 'Master Punch Card', School.ARCANE, [_dummy(_PUNCHES), _dummy(_CARD_LOCK_SEC)],
    'Each different spell you cast punches the card, up to $s1 punches. At $s1 you gain Clearance: PRISMATIC, '
    'increasing your haste rating by $214247s1 and your critical strike rating by $214247s2 for $214247d, and the '
    'card clears. The card cannot be punched for $s2 sec after Clearance.',
    _ICON_PUNCH_CARD_PRISMATIC,
    'Gnomeregan hard mode, Master Punch Card (Mekgineer Thermaplugg, the Whole Workshop, trinket), the Equip: a '
    'passive aura with a proc. Effect 1 DUMMY amount 5 (BasePoints 4 + DieSides 1) = the punches Clearance needs, '
    'effect 2 DUMMY amount 30 = the seconds the card cannot be punched after Clearance (the throttle: punches come '
    'with haste). spell_proc: done melee, ranged, magic and none class spells, helpful or harmful (0x15510), every '
    'spell type, cast phase (the event Spell::_cast raises for non-triggered casts only), 100%, no internal cooldown '
    '(the script keeps the card\'s). spell_gnomer_item_master_punch_card: a punch is a spell the wearer cast, by its '
    'first rank, that has not punched the card since it last cleared; not triggered, not cast by an item, not an auto '
    'repeat (Auto Shot, Shoot, Throw), not passive. The fifth clears the card and casts the tier\'s 214247.',
    proc_type_mask=_OWN_CASTS, proc_chance=100,
)
procs_on(master_punch_card_214245, proc_flags=_OWN_CASTS, spell_type_mask=_PROC_SPELL_TYPE_MASK_ALL,
         spell_phase_mask=_PROC_SPELL_PHASE_CAST, chance=100.0)
scripted_by(master_punch_card_214245, 'spell_gnomer_item_master_punch_card')
