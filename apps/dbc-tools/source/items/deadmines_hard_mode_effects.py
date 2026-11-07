"""
The three Edwin VanCleef hard mode item effects (item variants plan v2 section 7.2, stage IV6; designer text:
docs/dungeons/deadmines-rework.md "Hard mode bonus list: Edwin VanCleef", copied in dungeon-loot-vanilla.md).

One spell set per effect serves every tier of its item (71 / 81 / 91 / 101): the item level changes only the stats, and
every damage number comes from potency (docs/potency-system.md; user rule: everything on potency, no hand
coefficients and no hand spell_bonus_data). The scripts are modules/mod-dungeon-bosses
src/Deadmines/hard_mode_items.cpp (ids mirrored in HardModeItemsLogic.h). The Signet's look-alike Blackguard is
creature 300430 (source/npcs/deadmines/hard_mode_items.py, the `deadmines` creature spare).

Ids: the `items` reservation 205400-205599 (source/ids.yaml); this file takes 205400-205409.

  205400  Powder Keg Fuse        Use (2 min): lob a keg at an enemy (missile, the Brewfest keg throw's look). The keg is
                                 aimed at the target's position at throw time: spell_dm_powder_keg_fuse marks that spot
                                 (205401) when the missile lands and sets off 205402 there once the mark's duration has
                                 run out, whatever becomes of the target in flight.
  205401  Powder Keg Fuse        the lit keg on the ground: a 2 s hidden ground aura (Flame Patch look). Its duration
                                 IS the fuse: the script reads it, and the Use tooltip shows it ($205401d).
  205402  Powder Keg             the blast: Fire, every enemy within 6 yd, hybrid potency 150 SP + 150 AP per target
                                 (so casters and melee both scale; one off-GCD payout, T 1.5 s). Castable while dead,
                                 so a keg lobbed before a death still goes off.
  205403  Blackguard's Signet    Equip: a passive proc aura. Melee hits (auto attacks and melee-class spells that land)
                                 have a 10% chance, 10 sec internal cooldown, to fire spell_dm_blackguards_signet: a
                                 Defias Blackguard (300430) appears behind the target, plays the ambush, and 205404
                                 strikes. Item auras get no Proc Chance (Systems.md section 5), so the script rolls
                                 nothing of its own.
  205404  Blackguard Strike      the strike: Physical, melee class, attack power potency 120 (T 1.5 s), cannot be
                                 dodged, parried or blocked (the Blackguard strikes from behind). Cast by the wearer,
                                 triggered: it rolls no procs of its own.
  205405  Ambush                 the Blackguard's look as it appears (stock Ambush 8676's visual), self, no effect.
  205406  Lantern of the Roaring Flame  Use (90 sec): a 20 sec buff; the next direct heal the wearer lands (one charge)
                                 fires spell_dm_lantern_of_the_roaring_flame, which drops 205407 at the healed target.
  205407  Roaring Flame          the zone: 10 sec, 8 yd, allies standing in it take 10% less damage (stock Flame Ring
                                 look).
  205408-205409  spare

Proc chance, internal cooldown, potencies, the buff window and the zone radius are proposals waiting for the designer
(STAGE-IV6 report, designer questions). None of the looks were checked in game.
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
_TARGET_DEST_DYNOBJ_ALLY = 29
_TARGET_DEST_DEST = 87

_ATTR0_PASSIVE = 0x00000040
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR0_ALLOW_CAST_WHILE_DEAD = 0x00800000
_ATTR4_NO_CAST_LOG = 0x00000001
_ATTR5_ALWAYS_AOE_LINE_OF_SIGHT = 0x04000000

_DMG_CLASS_MAGIC = 1
_DMG_CLASS_MELEE = 2

# spell_proc (SpellMgr.h)
_PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x00000004
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_TYPE_HEAL = 0x2
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_NORMAL_OR_CRITICAL = 0x1 | 0x2

# Stock looks (none checked in game yet).
_SV_KEG_THROW = 9806            # Brewfest - Throw Keg 43660: a lobbed keg missile
_SV_FLAME_PATCH = 10483         # Flame Patch 46836: a small burning patch, the lit fuse
_SV_DETONATION = 148            # Detonation 4043 / Heavy Dynamite 4062
_SV_AMBUSH = 155                # Ambush 8676
_SV_FIRE_WARD = 290             # Fire Ward 543
_SV_FLAME_RING = 10484          # Flame Ring 46842: a ring of fire on the ground
_ICON_KEG = 1460                # Brewfest - Throw Keg
_ICON_AMBUSH = 856              # Ambush
_ICON_FIRE_WARD = 16            # Fire Ward

_KEG_SPEED = 20.0               # yd per second, the stock keg throw's
_BLAST_RADIUS = 6.0
_ZONE_RADIUS = 8.0


def _raw(desc: str = '', aura_desc: str = '', spell_level: int = 0, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': spell_level, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_TEXT_MASKS, **more}


# --- Powder Keg Fuse (trinket, Use) ----------------------------------------------------------------------------------

powder_keg_blast_205402 = spell(
    id=205402, name='Powder Keg', school=School.FIRE, attributes=_ATTR0_ALLOW_CAST_WHILE_DEAD, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=150.0, ap_potency=150.0, potency_kind='direct',
                    time_basis_ms=1500, implicit_target_a=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=_BLAST_RADIUS)],
    spell_icon_id=_ICON_KEG,
    notes='Item variants IV6, Powder Keg Fuse: the blast, cast by spell_dm_powder_keg_fuse (triggered, at the spot '
          'the keg landed) when the fuse mark 205401 runs out. Fire, every enemy within 6 yd (uncapped). Hybrid '
          'potency 150 SP + 150 AP per target, T 1.5 s (an off-GCD payout): the trinket is a Crit trinket with no '
          'primary, so casters and melee both scale off it. DefenseType MAGIC; ALLOW_CAST_WHILE_DEAD so a keg lobbed '
          'before the wearer died still goes off. ALWAYS_AOE_LINE_OF_SIGHT (AttributesEx5): the cast needs no line of '
          'sight from the wearer to the keg (a pillar, a mast or a body behind cover would otherwise fizzle it), '
          'while each target still needs one from the blast centre. Look: stock Detonation SV 148.',
    raw_overrides=_raw('Deals {pot1} Fire damage to all enemies within $a1 yd.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_DETONATION,
                       AttributesEx5=_ATTR5_ALWAYS_AOE_LINE_OF_SIGHT),
)

powder_keg_fuse_look_205401 = spell(
    id=205401, name='Powder Keg Fuse', school=School.FIRE,
    attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG | _ATTR0_ALLOW_CAST_WHILE_DEAD, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=2000,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_DEST_DEST, implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY,
                    radius_yards=2.0)],
    spell_icon_id=_ICON_KEG,
    notes='Item variants IV6, Powder Keg Fuse: the lit keg where it landed. A hidden ground aura (TARGET_DEST_DEST / '
          'TARGET_DEST_DYNOBJ_ALLY, the shape of 205407; its DUMMY aura on allies does nothing and pulls nothing) '
          'whose look is stock Flame Patch SV 10483. Its 2 s duration is the fuse: spell_dm_powder_keg_fuse reads it '
          'to time the blast, and 205400 shows it ($205401d).',
    raw_overrides=_raw(SpellVisualID_1=_SV_FLAME_PATCH, AttributesEx4=_ATTR4_NO_CAST_LOG,
                       AttributesEx5=_ATTR5_ALWAYS_AOE_LINE_OF_SIGHT),
)

powder_keg_fuse_205400 = spell(
    id=205400, name='Powder Keg Fuse', school=School.FIRE, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=30.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_KEG,
    notes='Item variants IV6, Powder Keg Fuse (VanCleef hard mode trinket), the Use: lob a keg at an enemy within '
          '30 yd, 2 min cooldown, off the GCD (StartRecoveryCategory 0). A missile (Speed 20, the stock Brewfest keg '
          'throw SV 9806). The keg is aimed at the target\'s position at the moment of the throw (OnCast): when the '
          'missile lands spell_dm_powder_keg_fuse drops the fuse mark 205401 at that spot and sets off 205402 there '
          'when the mark runs out, even if the target died or evaded in flight (the cooldown is never wasted).',
    raw_overrides=_raw(
        'Lob a lit keg at an enemy. It lands where the enemy stood and explodes $205401d later, dealing '
        + pot_text(powder_keg_blast_205402) + ' Fire damage to all enemies within $205402a1 yd.',
        Speed=_KEG_SPEED, SpellVisualID_1=_SV_KEG_THROW, StartRecoveryCategory=0, StartRecoveryTime=0,
    ),
)
scripted_by(powder_keg_fuse_205400, 'spell_dm_powder_keg_fuse')

# --- Blackguard's Signet (ring, Equip) -------------------------------------------------------------------------------

blackguard_strike_205404 = spell(
    id=205404, name='Blackguard Strike', school=School.NORMAL, attributes=_ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=30.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=120.0, potency_kind='direct', time_basis_ms=1500,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_AMBUSH,
    notes='Item variants IV6, Blackguard\'s Signet: the Blackguard\'s one strike, cast by the wearer (triggered, so it '
          'procs nothing) from spell_dm_blackguards_signet as the Blackguard 300430 appears behind the target. '
          'Physical, DefenseType MELEE (melee hit and crit), attack power potency 120, T 1.5 s (an off-GCD payout). '
          'NO_ACTIVE_DEFENSE: it comes from behind, so no dodge, parry or block. No look of its own: the '
          'Blackguard\'s ambush 205405 is the look.',
    raw_overrides=_raw('Strikes the target for {pot1} Physical damage.', spell_level=1,
                       DefenseType=_DMG_CLASS_MELEE, SpellVisualID_1=0),
)

blackguard_ambush_look_205405 = spell(
    id=205405, name='Ambush', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_AMBUSH,
    notes='Item variants IV6, Blackguard\'s Signet: visual only. The Blackguard 300430 casts it on itself as it '
          'appears (stock Ambush 8676 SV 155). DUMMY with no handler, DO_NOT_DISPLAY | DO_NOT_LOG; copies the stock '
          'visual, never the stock spell.',
    raw_overrides=_raw(SpellVisualID_1=_SV_AMBUSH, AttributesEx4=_ATTR4_NO_CAST_LOG),
)

blackguards_signet_205403 = spell(
    id=205403, name="Blackguard's Signet", school=School.NORMAL, attributes=_ATTR0_PASSIVE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_AMBUSH,
    notes='Item variants IV6, Blackguard\'s Signet (VanCleef hard mode ring), the Equip: a passive DUMMY aura with a '
          'proc. spell_proc: done melee auto attacks and melee-class spells (0x14), damage type, hit phase, normal or '
          'critical hits only, 10% chance, 10 s internal cooldown (the throttle against haste and cleaves; Systems.md '
          'section 5). spell_dm_blackguards_signet summons the Blackguard 300430 behind the target and casts 205404. '
          'Item auras get no Proc Chance (Systems.md section 5).',
    raw_overrides=_raw(
        'Your melee hits have a chance to call a Defias Blackguard from the shadows, who strikes your target for '
        + pot_text(blackguard_strike_205404) + ' Physical damage.',
        ProcTypeMask=_PROC_FLAG_DONE_MELEE_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, ProcChance=10,
    ),
)
_SIGNET_PROC_FLAGS = _PROC_FLAG_DONE_MELEE_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS
procs_on(blackguards_signet_205403, proc_flags=_SIGNET_PROC_FLAGS,
         spell_type_mask=_PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=_PROC_SPELL_PHASE_HIT,
         hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=10.0, cooldown_ms=10000)
scripted_by(blackguards_signet_205403, 'spell_dm_blackguards_signet')

# --- Lantern of the Roaring Flame (trinket, Use) ---------------------------------------------------------------------

roaring_flame_zone_205407 = spell(
    id=205407, name='Roaring Flame', school=School.FIRE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=10000,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=-11, misc_value=127, implicit_target_a=_TARGET_DEST_DEST,
                    implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, radius_yards=_ZONE_RADIUS)],
    spell_icon_id=_ICON_FIRE_WARD,
    notes='Item variants IV6, Lantern of the Roaring Flame: the warding flame. A 10 s ground zone at the healed '
          'target\'s feet (TARGET_DEST_DEST, so the script places it; TARGET_DEST_DYNOBJ_ALLY, so it holds allies), '
          '8 yd: damage taken -10% (BasePoints -11 + DieSides 1, all schools 127) while standing in it. Look: stock '
          'Flame Ring SV 10484.',
    raw_overrides=_raw('Allies standing in the flame take $s1% less damage.', 'Damage taken reduced.',
                       SpellVisualID_1=_SV_FLAME_RING),
)

lantern_of_the_roaring_flame_205406 = spell(
    id=205406, name='Lantern of the Roaring Flame', school=School.FIRE, cast_time_ms=0, cooldown_ms=90000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=20000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FIRE_WARD,
    notes='Item variants IV6, Lantern of the Roaring Flame (VanCleef hard mode trinket), the Use: 90 s cooldown, off '
          'the GCD, a visible 20 s buff with one charge. spell_proc: done positive spells of the magic or none damage '
          'class (0x4400), heal type, hit phase (a HoT cast heals nothing then, so only direct heals count), 100%, '
          '1 charge. spell_dm_lantern_of_the_roaring_flame drops 205407 at the healed target. Look on use: stock Fire '
          'Ward SV 290.',
    raw_overrides=_raw(
        "Your next direct heal within $d leaves a warding flame at the target's feet for $205407d. Allies standing "
        'in it take $205407s1% less damage.',
        'Your next direct heal leaves a warding flame.',
        ProcTypeMask=_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
        ProcChance=100, ProcCharges=1, SpellVisualID_1=_SV_FIRE_WARD, StartRecoveryCategory=0, StartRecoveryTime=0,
    ),
)
procs_on(lantern_of_the_roaring_flame_205406,
         proc_flags=_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS,
         spell_type_mask=_PROC_SPELL_TYPE_HEAL, spell_phase_mask=_PROC_SPELL_PHASE_HIT,
         hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=100.0, charges=1)
scripted_by(lantern_of_the_roaring_flame_205406, 'spell_dm_lantern_of_the_roaring_flame')
