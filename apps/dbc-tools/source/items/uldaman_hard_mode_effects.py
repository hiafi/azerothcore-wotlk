"""
The three Uldaman hard mode item effects (designer text: docs/dungeons/uldaman-rework.md ## Loot, "Hard mode:
Archaedas, The Makers' Lights", approved 2026-11-21, ruling 35): Waking Stone, Lightbound Choker and Fragment of the
Disks. After the Gnomeregan precedent (gnomeregan_hard_mode_effects.py).

The trample's damage comes from potency (user rule: everything on potency); the Disk's replay is a share of healing
that already carried the healer's bonuses, sized by its script. All three items are scale="budget"
(uldaman_hard_mode.py): every tier above the hard mode ladder's 71 carries its own copies (lib/item_spell_copies.py) of
the Waking Stone and its trample, of the Choker and Two Lights (MOD_RATING on haste, a secondary-curve rating, so its
rating grows by itself on the secondary-curve ratio, faster than the rest), and of the Disk's recording (its share,
`scale_amount=True`, the Sergeant's Whistle precedent). A script casts its tier's copy (ItemSpellCopies::Resolve). The
Disk's replay and its heal stay one spell for every tier: they carry no number, so no tooltip names their ids. The
scripts are modules/mod-dungeon-bosses src/Uldaman/hard_mode_items.cpp (ids mirrored in UldamanHardModeItemsLogic.h);
the Waking Earthen's look is source/npcs/uldaman/hard_mode_items.py (creature 301200).

Ids: the `uldaman_items` reservation 214680-214719 (source/ids.yaml); this file takes 214680-214686.

  214680  Waking Stone            Use (2 min, off the GCD): 4 sec on the wearer, effect 1 PERIODIC_DUMMY every 0.25 sec
                                  amount 20 = how far ahead the earthen marches (yd), effect 2 DUMMY amount 3 = the
                                  half width of its path (yd). spell_uldaman_item_waking_stone sends a Waking Earthen
                                  (301200) from beside the wearer to the spot 20 yd ahead and, on each tick, casts the
                                  tier's 214681 once on every enemy in combat its last step passed within 3 yd of.
  214681  Earthen Trample         Physical, one enemy, attack power potency 400, DefenseType MELEE, then the stock War
                                  Stomp 45 knockback. spell_uldaman_item_earthen_trample keeps the knockback off
                                  bosses.
  214682  Lightbound Choker       Equip: a passive proc aura. The wearer's own casts, cast phase, 100%.
                                  spell_uldaman_item_lightbound_choker: a damaging or healing spell (not triggered, not
                                  an item's, not an auto attack or auto repeat, not passive) of another school than
                                  the last one casts the tier's 214683.
  214683  Two Lights              8 sec on the wearer, up to 3 stacks: haste rating +10 per stack (MOD_RATING, the stock
                                  melee + ranged + spell haste mask; 1.0% each at level 60; it grows with the tier on
                                  the secondary curve: 10 / 14 / 18 / 25 a stack; user G17 2026-11-27).
  214684  Fragment of the Disks   Use (2 min, off the GCD): 6 sec on the wearer, effect 1 DUMMY amount 50 = the share of
                                  the recorded healing the Disk replays, in percent (grows with the tier: 50 / 53 / 55 /
                                  63). Landed heals and heal over time ticks, triggered heals too, 100%.
                                  spell_uldaman_item_fragment_of_the_disks records the effective healing per target;
                                  when the 6 sec run out it casts 214685 and hands the record over.
  214685  Disk Replay             6 sec on the wearer, a PERIODIC_DUMMY every 1 sec. spell_uldaman_item_disk_replay
                                  heals each recorded target a sixth of its share per tick (214686).
  214686  Echo of the Disks       the replayed heal, sized by the script. No potency, no crit, no caster modifiers, no
                                  procs.
  214687-214719  spare

In-combat filter: the trample reaches only enemies already in combat (handoff section 5), so a march never pulls a
pack; enemies under a crowd control that damage breaks are skipped too (the Stormcharged Fang's rule). The replay is a
heal (no filter).

Every number is a proposal waiting for the designer (STAGE-UG-HM report). None of the looks were checked in game.
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
_TARGET_UNIT_TARGET_ALLY = 21

_ATTR0_PASSIVE = 0x00000040
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR0_NO_AURA_CANCEL = 0x80000000
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000

_DMG_CLASS_MELEE = 2
# CombatRating mask CR_HASTE_MELEE | CR_HASTE_RANGED | CR_HASTE_SPELL (the stock haste rating auras' value, Kiss of the
# Spider 28866; Clearance: PRISMATIC's)
_HASTE_RATING_MASK = (1 << 17) | (1 << 18) | (1 << 19)

# spell_proc (SpellMgr.h)
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS = 0x00000100
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG = 0x00001000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x00010000
_PROC_FLAG_DONE_PERIODIC = 0x00040000
_PROC_SPELL_TYPE_HEAL = 0x2
_PROC_SPELL_TYPE_MASK_ALL = 0x7
_PROC_SPELL_PHASE_CAST = 0x1
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_NORMAL_OR_CRITICAL = 0x1 | 0x2
_PROC_ATTR_TRIGGERED_CAN_PROC = 0x2

# Every kind of spell the wearer casts (the cast phase event a non-triggered cast raises, Spell::_cast): melee, ranged,
# magic and none class, helpful or harmful. No auto attack flag. (The Master Punch Card's.)
_OWN_CASTS = (_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS | _PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
              | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG
              | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG)
# Landed heals: helpful magic and none class spells and periodic ticks (the Sergeant's Whistle's).
_HEALS = (_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS
          | _PROC_FLAG_DONE_PERIODIC)

# Stock looks and icons, read from Spell.dbc by spell (none checked in game yet).
_SV_AWAKEN_EARTHEN = 1843       # Awaken Earthen Dwarf 10259 (a statue waking; the Archaedas doc's)
_SV_TRAMPLE = 672               # Trample 5568
_SV_POWER_INFUSION = 7553       # Power Infusion 10060
_SV_FLASH_HEAL = 3077           # Flash Heal 2061
_ICON_AWAKEN_EARTHEN = 66       # Awaken Earthen Dwarf 10259's icon
_ICON_TRAMPLE = 168             # Trample 5568's icon
_ICON_HOLY_SHOCK = 156          # Holy Shock 20473's icon (light and shadow)
_ICON_POWER_INFUSION = 1872     # Power Infusion 10060's icon
_ICON_STONED = 220              # Stoned 10255's icon (the Uldaman statues)
_ICON_DIVINE_HYMN = 3209        # Divine Hymn 64843's icon

# An off-GCD payout's time basis (the Deadmines items' precedent).
_PROC_PAYOUT_MS = 1500

_MARCH_MS = 4000                # the march's time limit; at 8 yd/s the 19 yd walk takes about 2.4 sec
_MARCH_TICK_MS = 250            # 2 yd a step at 8 yd/s, inside the 3 yd half width
_MARCH_YARDS = 20
_PATH_HALF_WIDTH = 3
_TRAMPLE_POTENCY = 400.0
# the stock War Stomp 45 knockback (effect 2): MiscValue 75 = 7.5 yd/s away, BasePoints 56 + DieSides 1 = 5.7 yd/s up
_KNOCKBACK_XY = 75
_KNOCKBACK_Z = 57
_LIGHTS_MS = 8000
_LIGHTS_STACKS = 3
_LIGHTS_HASTE_RATING = 10       # at level 60, 10 rating = 1% haste
_RECORD_MS = 6000
_REPLAY_SHARE_PCT = 50
_REPLAY_MS = 6000
_REPLAY_TICK_MS = 1000


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
# Hard mode: Archaedas, The Makers' Lights

# --- Waking Stone (trinket, Use) -------------------------------------------------------------------------------------

earthen_trample_214681 = spell(
    id=214681, name='Earthen Trample', school=School.NORMAL, attributes=_ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=_TRAMPLE_POTENCY, potency_kind='direct',
               time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.KNOCK_BACK, base_points=_KNOCKBACK_Z - 1, misc_value=_KNOCKBACK_XY,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_TRAMPLE,
    notes='Uldaman hard mode, Waking Stone: the earthen\'s trample, cast by the wearer (triggered) from '
          'spell_uldaman_item_waking_stone on each enemy in combat the earthen passes, once per enemy per march. '
          'Physical, DefenseType MELEE (melee crit, armor), attack power potency 400, T 1.5 s (an off-GCD payout). '
          'NO_ACTIVE_DEFENSE: no dodge, parry or block. Effect 2 KNOCK_BACK from the wearer\'s spot, the stock War '
          'Stomp 45 values (MiscValue 75 = 7.5 yd/s away, 57 = 5.7 yd/s up). The engine refuses a knockback on '
          'world bosses, instance_encounters bosses, knockback-immune creatures, giants, vehicles and rooted units '
          '(Spell::EffectKnockBack); spell_uldaman_item_earthen_trample also keeps it off a creature that binds the '
          'instance or runs a BossAI script (Olaf, Eric, the new Uldaman bosses). IGNORE_LINE_OF_SIGHT: the script '
          'checks the line from the earthen instead. SUPPRESS_CASTER_PROCS. Look: stock Trample SV 672.',
    raw_overrides=_raw('Tramples the target for {pot1} Physical damage and knocks it back.', spell_level=1,
                       DefenseType=_DMG_CLASS_MELEE, SpellVisualID_1=_SV_TRAMPLE,
                       AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)
scripted_by(earthen_trample_214681, 'spell_uldaman_item_earthen_trample')

waking_stone_214680 = spell(
    id=214680, name='Waking Stone', school=School.NORMAL, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_MARCH_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, base_points=_MARCH_YARDS - 1,
               amplitude=_MARCH_TICK_MS, implicit_target_a=_TARGET_UNIT_CASTER),
        _dummy(_PATH_HALF_WIDTH),
    ],
    spell_icon_id=_ICON_AWAKEN_EARTHEN,
    notes='Uldaman hard mode, Waking Stone (Archaedas, The Makers\' Lights, trinket), the Use: 2 min cooldown, off the '
          'GCD, a visible 4 s self aura (the march\'s time limit). Effect 1 PERIODIC_DUMMY every 0.25 s, amount 20 '
          '(BasePoints 19 + DieSides 1) = how far ahead of the wearer the earthen marches, in yards; effect 2 DUMMY '
          'amount 3 = the half width of its path. spell_uldaman_item_waking_stone summons a Waking Earthen (301200, '
          'look only) 1 yd ahead of the wearer and runs it to the first obstacle or 20 yd ahead along the wearer\'s '
          'facing (8 yd/s); each tick it casts the tier\'s 214681 on every enemy in combat, attackable, not under a '
          'breakable crowd control, in the earthen\'s sight and within 3 yd (plus the enemy\'s combat reach, 5 yd up '
          'or down) of the step the earthen just walked, once per enemy per march. The earthen goes when it arrives, '
          'when the 4 s run out or when the wearer dies or leaves. A positive aura on the caster, so the bots\' "use '
          'trinket" action takes it. Look: stock Awaken Earthen Dwarf SV 1843.',
    raw_overrides=_raw(
        'Wake an earthen that marches $s1 yd ahead of you. Every enemy in combat within $s2 yd of its path is '
        'trampled for ' + pot_text(earthen_trample_214681) + ' Physical damage and knocked back, once per march. '
        'Bosses are not knocked back.',
        'An earthen marches ahead of you.',
        SpellVisualID_1=_SV_AWAKEN_EARTHEN, StartRecoveryCategory=0, StartRecoveryTime=0,
    ),
)
scripted_by(waking_stone_214680, 'spell_uldaman_item_waking_stone')

# --- Lightbound Choker (neck, Equip) ---------------------------------------------------------------------------------

two_lights_214683 = spell(
    id=214683, name='Two Lights', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_LIGHTS_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_RATING,
                    base_points=_LIGHTS_HASTE_RATING - 1, misc_value=_HASTE_RATING_MASK,
                    implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_POWER_INFUSION,
    notes='Uldaman hard mode, Lightbound Choker: Two Lights, cast by the wearer (triggered) from '
          'spell_uldaman_item_lightbound_choker. 8 s, up to 3 stacks (CumulativeAura; each new one refreshes the '
          'duration): haste rating +10 per stack (MOD_RATING, the stock melee + ranged + spell haste mask 917504): '
          '1.0% a stack at level 60, 3.0% at 3 on the 71 tier (user G17 2026-11-27: 10, was 15). '
          'MOD_RATING on haste (CR 17-19) is a secondary-curve '
          'rating, so each tier\'s copy scales by the secondary-curve ratio (item_spell_copies.tier_rating_ratio, '
          '1.3667 / 1.8444 / 2.5111), not the primary one: 14 / 18 / 25 a stack, 4.2 / 5.4 / 7.5% at 3 stacks. '
          'Haste is a stock rating (Systems.md section 2 keeps aura 306 for the four custom stats). '
          'SUPPRESS_CASTER_PROCS. Look: stock Power Infusion SV 7553.',
    raw_overrides=_raw('Increases your haste rating by $s1 for $d. Stacks up to $u times.',
                       'Two Lights: haste rating increased by $s1 for each light.', spell_level=1,
                       CumulativeAura=_LIGHTS_STACKS, SpellVisualID_1=_SV_POWER_INFUSION,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

lightbound_choker_214682 = _equip_aura(
    214682, 'Lightbound Choker', School.HOLY, [_dummy(1)],
    'Each damaging or healing spell you cast of a different school than your last grants Two Lights, increasing your '
    'haste rating by $214683s1 for $214683d, stacking up to $214683u times.',
    _ICON_HOLY_SHOCK,
    'Uldaman hard mode, Lightbound Choker (Archaedas, The Makers\' Lights, neck), the Equip: a passive aura with a '
    'proc. Effect 1 DUMMY, no number. spell_proc: done melee, ranged, magic and none class spells, helpful or harmful '
    '(0x15510), every spell type, cast phase (the event Spell::_cast raises for non-triggered casts only: once per '
    'cast, whether or not it then hits), 100%, no internal cooldown (the 3 stacks are the cap). '
    'spell_uldaman_item_lightbound_choker: a spell counts when the wearer cast it, not triggered, not cast by an item, '
    'not an auto repeat (Auto Shot, Shoot, Throw), not passive, and it deals damage or heals by its data (a damage, '
    'weapon damage, leech or heal effect, a periodic damage, leech or heal aura, or one level of triggered spell that '
    'does). Its school is its whole school mask: a multi-school spell (Frostfire Bolt) is its own school. A counting '
    'spell of another school than the last counting one casts the tier\'s 214683; the first one after the Choker is '
    'put on only sets the school.',
    proc_type_mask=_OWN_CASTS, proc_chance=100,
)
procs_on(lightbound_choker_214682, proc_flags=_OWN_CASTS, spell_type_mask=_PROC_SPELL_TYPE_MASK_ALL,
         spell_phase_mask=_PROC_SPELL_PHASE_CAST, chance=100.0)
scripted_by(lightbound_choker_214682, 'spell_uldaman_item_lightbound_choker')

# --- Fragment of the Disks (held in off-hand, Use) -------------------------------------------------------------------

echo_of_the_disks_214686 = spell(
    id=214686, name='Echo of the Disks', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded='a share of the healing the Disk recorded, set by spell_uldaman_item_disk_replay '
                                     '(custom base points)')],
    spell_icon_id=_ICON_DIVINE_HYMN,
    notes='Uldaman hard mode, Fragment of the Disks: one replayed heal, cast by the wearer (triggered) from '
          'spell_uldaman_item_disk_replay with its amount set to a sixth of the target\'s share. No potency: a share '
          'of healing that already had the healer\'s bonuses and crit (the target\'s healing taken undone when it was '
          'recorded, applied once now), so one spell for every tier. DefenseType 0, CANT_CRIT and '
          'IGNORE_CASTER_MODIFIERS (the Crew\'s Aid 213807 precedent; Systems.md section 6, stored healing: the '
          'release takes no modifiers). IGNORE_LINE_OF_SIGHT: the replay follows its targets. '
          'SUPPRESS_CASTER_PROCS: the replay procs nothing and is never recorded again. Look: stock Flash Heal SV '
          '3077.',
    raw_overrides=_raw('Heals the target.', spell_level=1, SpellVisualID_1=_SV_FLASH_HEAL,
                       AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_IGNORE_CASTER_MODIFIERS),
)

disk_replay_214685 = spell(
    id=214685, name='Disk Replay', school=School.HOLY, attributes=_ATTR0_NO_AURA_CANCEL, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_REPLAY_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, base_points=0,
                    amplitude=_REPLAY_TICK_MS, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_DIVINE_HYMN,
    notes='Uldaman hard mode, Fragment of the Disks: the replay on the wearer, cast by the wearer (triggered) from '
          'spell_uldaman_item_fragment_of_the_disks when the recording runs out, which hands it the record. 6 s, a '
          'PERIODIC_DUMMY every 1 s (a dummy: no haste ticks, Systems.md section 6). '
          'spell_uldaman_item_disk_replay heals each recorded target, alive, on the map and within 100 yd, a sixth '
          'of its share per tick (214686; the last tick takes the rounding rest). A target out of reach on a tick '
          'misses that tick. NO_AURA_CANCEL. One spell for every tier (the share is on the recording\'s copy).',
    raw_overrides=_raw('Replays recorded healing.', 'The Disk replays your recorded healing.', spell_level=1,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)
scripted_by(disk_replay_214685, 'spell_uldaman_item_disk_replay')

fragment_of_the_disks_214684 = spell(
    id=214684, name='Fragment of the Disks', school=School.HOLY, attributes=_ATTR0_NO_AURA_CANCEL, cast_time_ms=0,
    cooldown_ms=120000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_RECORD_MS, effects=[_dummy(_REPLAY_SHARE_PCT, scale_amount=True)],
    spell_icon_id=_ICON_STONED,
    notes='Uldaman hard mode, Fragment of the Disks (Archaedas, The Makers\' Lights, held in off-hand), the Use: 2 min '
          'cooldown, off the GCD, a visible 6 s recording on the wearer. Effect 1 DUMMY amount 50 (BasePoints 49 + '
          'DieSides 1) = the share of the recorded healing the Disk replays, in percent, growing with the tier '
          '(scale_amount: 50 / 53 / 55 / 63). spell_proc: done positive magic and none class spells and periodic '
          'ticks (0x44400), heal type, hit phase, normal or critical, 100%, TRIGGERED_CAN_PROC (triggered heals are '
          'the wearer\'s healing too). spell_uldaman_item_fragment_of_the_disks records, per target, the effective '
          'healing (no overhealing) before the target\'s own healing taken modifiers; not recorded: item Uses\' direct '
          'heals (a bandage\'s ticks carry no cast item and are recorded), heals cast by the wearer\'s pets and '
          'totems (Healing Stream Totem, a Lightwell: another actor), heals sized from another heal '
          '(IGNORE_CASTER_MODIFIERS: Beacon of Light, the Whistle\'s copy, the Disk\'s own replay). When the 6 s run '
          'out (not on death) it casts 214685 on the wearer and hands it the record. NO_AURA_CANCEL. Not a positive '
          'Use the bots press: the bots\' "use trinket" reads the trinket slots only. A held in off-hand item can be '
          'swapped in combat (ItemTemplate::CanChangeEquipStateInCombat), and each tier\'s copy has its own 2 min '
          'cooldown, so a wearer with two tiers gets a second Use after the equip cooldown (accepted, the Gnomeregan '
          'n2 and Zul\'Farrak n4 class).',
    raw_overrides=_raw(
        'The Disk records your healing for $d. Then, over the next 6 sec, it replays $s1% of it on the same targets. '
        'Overhealing is not recorded.',
        'The Disk records your healing.',
        StartRecoveryCategory=0, StartRecoveryTime=0,
        ProcTypeMask=_HEALS, ProcChance=100, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)
procs_on(fragment_of_the_disks_214684, proc_flags=_HEALS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL,
         attributes_mask=_PROC_ATTR_TRIGGERED_CAN_PROC, chance=100.0)
scripted_by(fragment_of_the_disks_214684, 'spell_uldaman_item_fragment_of_the_disks')
