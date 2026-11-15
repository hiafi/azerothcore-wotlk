"""
The eleven new Blackrock Depths hard mode item effects (wave 2 dungeon items; designer text:
docs/dungeons/blackrock-depths-rework.md ## Loot, "Hard mode lists", approved 2026-11-14, copied in
dungeon-loot-vanilla.md): the Ring of Law Encore (Theldren's Executioner, Lefty's Shiv, Korv's Spirit Fetish), Lord
Incendius (Black Anvil Bulwark, Fist of the Lake Lord, Scepter of the Molten Lake), Golem Lord Argelmach (Prototype
Power Core, Golemwright's Mending Rod, Electron's Lethal Coil) and Emperor Dagran Thaurissan (Volcanic Heartstone, Orb
of the Sorcerer-Thane). The twelfth hard mode item, Ironfoe, keeps its stock Fury of Forgewright (15494) and needs
nothing here. After the Stratholme precedent (stratholme_hard_mode_effects.py).

Every damage and healing number comes from potency (user rule: everything on potency), except Korv's chained heal,
which is half of the heal that triggered it (`potency_excluded`). The effects the designer scales by item level are
declared with scale="budget" on the item (blackrock_depths.py): every tier above the hard mode ladder's 71 carries its
own copies (lib/item_spell_copies.py), so a script casts its tier's copy (ItemSpellCopies::Resolve). Theldren's 10% and
Korv's half are percents and stay one spell. The scripts are modules/mod-dungeon-bosses src/BlackrockDepths/
hard_mode_items.cpp (ids mirrored in BlackrockDepthsHardModeItemsLogic.h); the two summoned looks are
source/npcs/blackrock_depths/hard_mode_items.py (creatures 300655 Lava Spawn, 300656 Mending Servo).

Ids: the `blackrock_depths_items` reservation 206830-206899 (source/ids.yaml); this file takes 206830-206854.

The Ring of Law, the Encore
  206830  Theldren's Executioner  Equip: a passive DUMMY aura. Effect 1 amount 10 = percent more melee damage, effect 2
                                  amount 30 = the target's health threshold in percent. The damage hook is the module's
                                  UnitScript BrdExecutionerDamage (auto attacks and melee-class spells of the wearer on
                                  a target strictly below 30% health). No numbers to scale.
  206831  Lefty's Shiv            Equip: PROC_TRIGGER_SPELL. Landed melee hits, 15%, no internal cooldown (the stack
                                  needs procs), cast 206832 on the target. Data only.
  206832  Vicious Wound           the bleed: Physical, mechanic bleed, 15 sec, a tick every 3 sec, attack power potency
                                  9 a tick (one 1.5 sec payout of 45 per stack), stacks to 5 (CumulativeAura), each new
                                  stack refreshes the duration.
  206833  Korv's Spirit Fetish    Equip: a passive DUMMY proc aura, amount 50 = the share of the heal, radius 15 yd.
                                  A landed direct heal (20%) fires spell_brd_korvs_spirit_fetish: the most injured
                                  other group member within 15 yd of the healed target gets 206834.
  206834  Spirit Chain            the chained heal, sized by the script (half the heal). No potency, never crits, no
                                  caster bonuses (DefenseType 0: the first heal already had them).

Lord Incendius, Lord of the Lake
  206835  Black Anvil Bulwark     Equip: PROC_TRIGGER_SPELL. Taken melee attacks the wearer blocked (hit mask BLOCK),
                                  20%, 6 sec internal cooldown, cast 206836. Data only.
  206836  Anvil Eruption          Fire, every enemy within 8 yd of the wearer, attack power potency 100 (T 1.5 sec).
  206837  Fist of the Lake Lord   Equip: PROC_TRIGGER_SPELL. Landed melee hits, 15%, 6 sec internal cooldown, cast
                                  206838 at the target. Data only.
  206838  Lake Lord's Slam        Fire, every enemy within 5 yd of the target, attack power potency 90 (T 1.5 sec).
  206839  Scepter of the Molten Lake  Equip: a passive DUMMY proc aura. Landed damaging spells, 10%, 25 sec internal
                                  cooldown (longer than the Lava Spawn). spell_brd_scepter_of_the_molten_lake summons
                                  the Lava Spawn 300655 beside the wearer and puts the tier's 206840 on the wearer.
  206840  Lava Spawn              the wearer's 10 sec buff, a PERIODIC_DUMMY every 2 sec: spell_brd_lava_spawn makes
                                  the wearer's Lava Spawn hurl at the wearer's target (the tier's 206841, cast by the
                                  wearer so the number scales with the wearer) and dismisses the Spawn when it ends.
  206841  Molten Hurl             Fire, one enemy, spell power potency 40 (T 1.5 sec): five hurls, 200 over the Spawn.

Golem Lord Argelmach, the Prototype
  206842  Prototype Power Core    Use (2 min): 12 sec, a PERIODIC_DUMMY every 2 sec, amount 3 = the orbs, radius 10 yd.
                                  spell_brd_prototype_power_core: each orb strikes a nearby enemy in combat (different
                                  enemies while there are enough) with the tier's 206843. Lightning Shield's orbs look.
  206843  Arcane Orb Strike       Arcane, one enemy, hybrid potency 15 SP + 15 AP (T 1.5 sec; a trinket with no
                                  primary): 18 strikes over the Core.
  206844  Golemwright's Mending Rod  Equip: a passive DUMMY proc aura. Landed heals, 10%, 25 sec internal cooldown.
                                  spell_brd_golemwrights_mending_rod deploys the Mending Servo 300656 at the healed
                                  target and puts the tier's 206845 on the wearer.
  206845  Mending Servo           the wearer's 10 sec buff, a PERIODIC_DUMMY every 2 sec, radius 20 yd:
                                  spell_brd_mending_servo heals the most injured group member within 20 yd of the Servo
                                  with the tier's 206846 (cast by the wearer).
  206846  Servo Mend              a heal, healing potency 45 (T 1.5 sec): five mends, 225 over the Servo.
  206847  Electron's Lethal Coil  Equip: a passive DUMMY proc aura, effect 1 amount 15 = the charge chance in percent,
                                  radius 8 yd = the arc. spell_proc: landed damaging attacks and spells, 100% (the
                                  script needs every hit: it rolls the charge itself and detonates on the next hit).
                                  spell_brd_electrons_lethal_coil.
  206848  Lethal Attraction       the 8 sec charge on the target (a DUMMY debuff, one per wearer).
  206849  Lethal Arc              Nature, one enemy, hybrid potency 60 SP + 60 AP (T 1.5 sec; a ring): every other enemy
                                  in combat within 8 yd of the charged target takes it.

Emperor Dagran Thaurissan, the Avatar of Ragnaros
  206850  Volcanic Heartstone     Use (2 min): 8 sec, 20% less damage taken (MOD_DAMAGE_PERCENT_TAKEN -20, all schools).
                                  spell_brd_volcanic_heartstone: when it ends any way but death, the wearer casts the
                                  tier's 206851.
  206851  Heartstone Eruption     Fire, every enemy within 8 yd of the wearer, hybrid potency 150 SP + 150 AP
                                  (T 1.5 sec; a tank trinket with no primary).
  206852  Orb of the Sorcerer-Thane  Equip: a passive DUMMY proc aura, radius 2 yd = half the beam's width. Landed
                                  damaging spells, 10%, 12 sec internal cooldown. spell_brd_orb_of_the_sorcerer_thane:
                                  the target and every other enemy in combat on the line from the wearer to it take the
                                  tier's 206853.
  206853  Shadow Beam             Shadow, one enemy, spell power potency 120 (T 1.5 sec).
  206854-206899  spare

Chances, internal cooldowns, potencies, radii and durations are proposals waiting for the designer (STAGE-BRD report,
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
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_SRC_CASTER = 22
_TARGET_DEST_TARGET_ENEMY = 53

_ATTR0_PASSIVE = 0x00000040
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
_ATTR4_NO_CAST_LOG = 0x00000001

_DMG_CLASS_MAGIC = 1
_DMG_CLASS_MELEE = 2
_MECHANIC_BLEED = 15
_SCHOOL_MASK_ALL = 127

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
_PROC_HIT_BLOCK = 0x40

_MELEE_HITS = _PROC_FLAG_DONE_MELEE_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS
_RANGED_HITS = _PROC_FLAG_DONE_RANGED_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
_HARMFUL_SPELLS = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG
_HELPFUL_SPELLS = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS
_TAKEN_MELEE = _PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK | _PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS
_DAMAGING_HITS = _MELEE_HITS | _RANGED_HITS | _HARMFUL_SPELLS

# Stock looks and icons, picked by name from Spell.dbc (none checked in game yet).
_ICON_EXECUTE = 1648            # Execute 5308
_SV_DEEP_WOUNDS = 121           # Deep Wounds 12721
_ICON_DEEP_WOUNDS = 243
_SV_CHAIN_HEAL = 3659           # Chain Heal 1064
_ICON_CHAIN_HEAL = 963
_SV_FIRE_NOVA = 14908           # Fire Nova 8349
_ICON_FIRE_NOVA = 33
_SV_FLAMESTRIKE = 10383         # Flamestrike 2120
_ICON_FLAMESTRIKE = 37
_SV_FIRE_BLAST = 143            # Fire Blast 2136: an impact on the target, no missile from the wearer
_ICON_FIRE_BLAST = 12
_ICON_LAVA_BURST = 3064         # Lava Burst 51505
_SV_LIGHTNING_SHIELD = 37       # Lightning Shield 324: three orbs circling the wearer
_ICON_LIGHTNING_SHIELD = 19
_SV_ARCANE_MISSILES = 262       # Arcane Missiles 5143
_ICON_ARCANE_EXPLOSION = 122
_SV_FLASH_HEAL = 3077           # Flash Heal 2061
_ICON_FLASH_HEAL = 242
_SV_CHAIN_LIGHTNING = 36        # Chain Lightning 421
_ICON_CHAIN_LIGHTNING = 165
_SV_STONEFORM = 5787            # Stoneform 20594
_ICON_STONEFORM = 93
_SV_HELLFIRE = 781              # Hellfire Effect 5857
_ICON_HELLFIRE = 937
_SV_SHADOW_BOLT = 64            # Shadow Bolt 686: a bolt from the wearer to each enemy on the line
_ICON_MIND_FLAY = 548           # Mind Flay 15407

# An off-GCD proc payout's time basis (the Deadmines items' precedent). A periodic payout keeps the tick as its time
# basis and takes potency per tick = payout potency x 1.5 sec / duration.
_PROC_PAYOUT_MS = 1500

_ERUPTION_RADIUS = 8.0
_SLAM_RADIUS = 5.0
_FETISH_RADIUS = 15.0
_CORE_RADIUS = 10.0
_SERVO_RADIUS = 20.0
_ARC_RADIUS = 8.0
_HEARTSTONE_RADIUS = 8.0
_BEAM_HALF_WIDTH = 2.0


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


# =====================================================================================================================
# Hard mode: the Ring of Law, the Encore

# --- Theldren's Executioner (two-hand axe, Equip) --------------------------------------------------------------------

theldrens_executioner_206830 = _equip_aura(
    206830, "Theldren's Executioner", School.NORMAL,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=9,
            implicit_target_a=_TARGET_UNIT_CASTER),
     Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=29,
            implicit_target_a=_TARGET_UNIT_CASTER)],
    'Your melee attacks deal $s1% more damage to enemies below $s2% health.',
    _ICON_EXECUTE,
    'Blackrock Depths hard mode, Theldren\'s Executioner (the Encore, two-hand axe), the Equip: a passive DUMMY aura. '
    'Effect 1 amount 10 (BasePoints 9 + DieSides 1) = percent more damage, effect 2 amount 30 = the health threshold. '
    'The module\'s UnitScript BrdExecutionerDamage grows the wearer\'s auto attacks and melee-class spell hits on a '
    'target strictly below the threshold. A percent: one spell for every tier.',
)

# --- Lefty's Shiv (dagger, Equip) ------------------------------------------------------------------------------------

vicious_wound_206832 = spell(
    id=206832, name='Vicious Wound', school=School.NORMAL, mechanic=_MECHANIC_BLEED,
    attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=15000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000,
                    ap_potency=9.0, potency_kind='periodic', implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_DEEP_WOUNDS,
    notes='Blackrock Depths hard mode, Lefty\'s Shiv: the wound. Physical bleed (mechanic 15, so armor does not reduce '
          'it), 15 s, a tick every 3 s, attack power potency 9 a tick (time basis = the tick): one stack adds up to '
          'one 1.5 s off-GCD payout of potency 45. Stacks to 5 (CumulativeAura; the engine multiplies the tick by the '
          'stacks), each new stack refreshes the duration. DefenseType MELEE. Cast by the wearer (triggered by '
          '206831), so it procs nothing. Look: stock Deep Wounds SV 121.',
    raw_overrides=_raw('Deals {pot1} Physical damage every $t1 sec for $d. Stacks up to $u times.', 'Bleeding.',
                       spell_level=1, CumulativeAura=5, DefenseType=_DMG_CLASS_MELEE,
                       SpellVisualID_1=_SV_DEEP_WOUNDS),
)

leftys_shiv_206831 = _equip_aura(
    206831, "Lefty's Shiv", School.NORMAL,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, base_points=0,
            trigger_spell=vicious_wound_206832.id, implicit_target_a=_TARGET_UNIT_CASTER)],
    'Your melee hits have a chance to open a Vicious Wound, dealing '
    + pot_text(vicious_wound_206832, variant='total') + ' Physical damage over $206832d. Stacks up to $206832u '
    'times.',
    _ICON_DEEP_WOUNDS,
    'Blackrock Depths hard mode, Lefty\'s Shiv (the Encore, dagger), the Equip: a passive PROC_TRIGGER_SPELL aura that '
    'casts 206832 on the target. spell_proc: done melee auto attacks and melee-class spells (0x14), damage type, hit '
    'phase, normal or critical, 15%, no internal cooldown (the stack needs procs). Data only, no script.',
    proc_type_mask=_MELEE_HITS, proc_chance=15,
)
procs_on(leftys_shiv_206831, proc_flags=_MELEE_HITS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=15.0)

# --- Korv's Spirit Fetish (held in off-hand, Equip) ------------------------------------------------------------------

spirit_chain_206834 = spell(
    id=206834, name='Spirit Chain', school=School.NATURE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded='half of the direct heal that triggered it, set by '
                                     'spell_brd_korvs_spirit_fetish (custom base points)')],
    spell_icon_id=_ICON_CHAIN_HEAL,
    notes='Blackrock Depths hard mode, Korv\'s Spirit Fetish: the chained heal, cast by the healer (triggered) from '
          'spell_brd_korvs_spirit_fetish with its amount set to the Fetish aura amount (50%) of the heal. No '
          'potency: a share of another heal. DefenseType 0, CANT_CRIT and IGNORE_CASTER_MODIFIERS: the first heal '
          'already had the healer\'s bonuses and crit. SUPPRESS_CASTER_PROCS. Look: stock Chain Heal SV 3659.',
    raw_overrides=_raw('Heals the target.', spell_level=1, SpellVisualID_1=_SV_CHAIN_HEAL,
                       AttributesEx2=_ATTR2_CANT_CRIT,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_IGNORE_CASTER_MODIFIERS),
)

_HEAL_PROCS = _HELPFUL_SPELLS

korvs_spirit_fetish_206833 = _equip_aura(
    206833, "Korv's Spirit Fetish", School.NATURE,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=49,
            implicit_target_a=_TARGET_UNIT_CASTER, radius_yards=_FETISH_RADIUS)],
    'Your direct heals have a chance to chain to the most injured party member within $a1 yd of the target, healing '
    'them for $s1% of the amount.',
    _ICON_CHAIN_HEAL,
    'Blackrock Depths hard mode, Korv\'s Spirit Fetish (the Encore, held in off-hand), the Equip: a passive DUMMY '
    'aura, amount 50 (BasePoints 49 + DieSides 1) = the share of the heal, radius 15 yd = how far from the healed '
    'target the chain looks. spell_proc: done positive magic and none class spells (0x4400), heal type, hit phase '
    '(direct heals only: a heal over time\'s cast heals nothing then, its ticks are periodic), normal or critical, '
    '20%, no internal cooldown. spell_brd_korvs_spirit_fetish casts 206834 on the group member (not the healed one) '
    'with the lowest health fraction below full.',
    proc_type_mask=_HEAL_PROCS, proc_chance=20,
)
procs_on(korvs_spirit_fetish_206833, proc_flags=_HEAL_PROCS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=20.0)
scripted_by(korvs_spirit_fetish_206833, 'spell_brd_korvs_spirit_fetish')

# =====================================================================================================================
# Hard mode: Lord Incendius, Lord of the Lake

# --- Black Anvil Bulwark (shield, Equip) -----------------------------------------------------------------------------

anvil_eruption_206836 = spell(
    id=206836, name='Anvil Eruption', school=School.FIRE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=100.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_SRC_CASTER,
                    implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=_ERUPTION_RADIUS)],
    spell_icon_id=_ICON_FIRE_NOVA,
    notes='Blackrock Depths hard mode, Black Anvil Bulwark: the eruption, cast by the wearer (triggered by 206835). '
          'Fire, every enemy within 8 yd of the wearer (TARGET_SRC_CASTER / TARGET_UNIT_SRC_AREA_ENEMY). Attack power '
          'potency 100, T 1.5 s (an off-GCD payout): a Strength tank shield. DefenseType MAGIC. SUPPRESS_CASTER_PROCS. '
          'Look: stock Fire Nova SV 14908.',
    raw_overrides=_raw('Deals {pot1} Fire damage to enemies within $a1 yd.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_FIRE_NOVA,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

black_anvil_bulwark_206835 = _equip_aura(
    206835, 'Black Anvil Bulwark', School.FIRE,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, base_points=0,
            trigger_spell=anvil_eruption_206836.id, implicit_target_a=_TARGET_UNIT_CASTER)],
    'Your blocks have a chance to erupt in flame, dealing ' + pot_text(anvil_eruption_206836)
    + ' Fire damage to enemies within $206836a1 yd.',
    _ICON_FIRE_NOVA,
    'Blackrock Depths hard mode, Black Anvil Bulwark (Lord Incendius, shield), the Equip: a passive PROC_TRIGGER_SPELL '
    'aura that casts 206836. spell_proc: taken melee auto attacks and melee-class spells (0x28), hit mask BLOCK, 20%, '
    '6 s internal cooldown. Data only, no script.',
    proc_type_mask=_TAKEN_MELEE, proc_chance=20,
)
procs_on(black_anvil_bulwark_206835, proc_flags=_TAKEN_MELEE, hit_mask=_PROC_HIT_BLOCK, chance=20.0,
         cooldown_ms=6000)

# --- Fist of the Lake Lord (fist weapon, Equip) ----------------------------------------------------------------------

lake_lords_slam_206838 = spell(
    id=206838, name="Lake Lord's Slam", school=School.FIRE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=90.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_DEST_TARGET_ENEMY,
                    implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=_SLAM_RADIUS)],
    spell_icon_id=_ICON_FLAMESTRIKE,
    notes='Blackrock Depths hard mode, Fist of the Lake Lord: the slam, cast by the wearer (triggered by 206837) at '
          'the target. Fire, every enemy within 5 yd of the target (TARGET_DEST_TARGET_ENEMY / '
          'TARGET_UNIT_DEST_AREA_ENEMY). Attack power potency 90, T 1.5 s. DefenseType MAGIC. SUPPRESS_CASTER_PROCS. '
          'Look: stock Flamestrike SV 10383.',
    raw_overrides=_raw('Deals {pot1} Fire damage to enemies within $a1 yd of the target.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_FLAMESTRIKE,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

fist_of_the_lake_lord_206837 = _equip_aura(
    206837, 'Fist of the Lake Lord', School.FIRE,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, base_points=0,
            trigger_spell=lake_lords_slam_206838.id, implicit_target_a=_TARGET_UNIT_CASTER)],
    'Your melee hits have a chance to slam the ground under the target, dealing ' + pot_text(lake_lords_slam_206838)
    + ' Fire damage to enemies within $206838a1 yd of it.',
    _ICON_FLAMESTRIKE,
    'Blackrock Depths hard mode, Fist of the Lake Lord (Lord Incendius, fist weapon), the Equip: a passive '
    'PROC_TRIGGER_SPELL aura that casts 206838 at the target. spell_proc: done melee auto attacks and melee-class '
    'spells (0x14), damage type, hit phase, normal or critical, 15%, 6 s internal cooldown. Data only, no script.',
    proc_type_mask=_MELEE_HITS, proc_chance=15,
)
procs_on(fist_of_the_lake_lord_206837, proc_flags=_MELEE_HITS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=15.0,
         cooldown_ms=6000)

# --- Scepter of the Molten Lake (staff, Equip) -----------------------------------------------------------------------

molten_hurl_206841 = spell(
    id=206841, name='Molten Hurl', school=School.FIRE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=40.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_LAVA_BURST,
    notes='Blackrock Depths hard mode, Scepter of the Molten Lake: the Lava Spawn\'s hurl, cast by the wearer '
          '(triggered) from spell_brd_lava_spawn, so the number scales with the wearer. Fire, one enemy, spell power '
          'potency 40, T 1.5 s (five hurls over the Spawn: 200). DefenseType MAGIC. SUPPRESS_CASTER_PROCS. Look: '
          'stock Fire Blast SV 143 (an impact on the target; the Spawn plays its cast animation).',
    raw_overrides=_raw('Deals {pot1} Fire damage.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       SpellVisualID_1=_SV_FIRE_BLAST, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

lava_spawn_206840 = spell(
    id=206840, name='Lava Spawn', school=School.FIRE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, base_points=0, amplitude=2000,
                    implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_LAVA_BURST,
    notes='Blackrock Depths hard mode, Scepter of the Molten Lake: the wearer\'s 10 s buff while the Lava Spawn '
          '(creature 300655) fights. A PERIODIC_DUMMY every 2 s: spell_brd_lava_spawn makes the Spawn face the '
          'wearer\'s target and play its cast, and the wearer casts the tier\'s 206841 on it (the selected enemy, else '
          'the wearer\'s victim). When the buff ends, the Spawn is dismissed.',
    raw_overrides=_raw('Your Lava Spawn hurls Fire at your target every $t1 sec, dealing '
                       + pot_text(molten_hurl_206841) + ' Fire damage.',
                       'A Lava Spawn fights at your side.', AttributesEx4=_ATTR4_NO_CAST_LOG),
)
scripted_by(lava_spawn_206840, 'spell_brd_lava_spawn')

scepter_of_the_molten_lake_206839 = _equip_aura(
    206839, 'Scepter of the Molten Lake', School.FIRE,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
            implicit_target_a=_TARGET_UNIT_CASTER)],
    'Your damaging spells have a chance to call a Lava Spawn for $206840d, which hurls Fire at your target every '
    '$206840t1 sec, dealing ' + pot_text(molten_hurl_206841) + ' Fire damage.',
    _ICON_LAVA_BURST,
    'Blackrock Depths hard mode, Scepter of the Molten Lake (Lord Incendius, staff), the Equip: a passive DUMMY aura '
    'with a proc. spell_proc: done harmful magic and none class spells, damage type, hit phase, normal or critical, '
    '10%, 25 s internal cooldown (longer than the Spawn, so one is out at a time). '
    'spell_brd_scepter_of_the_molten_lake summons the Lava Spawn 300655 beside the wearer and puts the tier\'s 206840 '
    'on the wearer.',
    proc_type_mask=_HARMFUL_SPELLS, proc_chance=10,
)
procs_on(scepter_of_the_molten_lake_206839, proc_flags=_HARMFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=10.0,
         cooldown_ms=25000)
scripted_by(scepter_of_the_molten_lake_206839, 'spell_brd_scepter_of_the_molten_lake')

# =====================================================================================================================
# Hard mode: Golem Lord Argelmach, the Prototype

# --- Prototype Power Core (trinket, Use) -----------------------------------------------------------------------------

arcane_orb_strike_206843 = spell(
    id=206843, name='Arcane Orb Strike', school=School.ARCANE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=15.0, ap_potency=15.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_ARCANE_EXPLOSION,
    notes='Blackrock Depths hard mode, Prototype Power Core: one orb\'s strike, cast by the wearer (triggered) from '
          'spell_brd_prototype_power_core. Arcane, one enemy, hybrid potency 15 SP + 15 AP, T 1.5 s (a trinket with '
          'no primary, so casters and melee both scale off it); three orbs every 2 s for 12 s. DefenseType MAGIC. '
          'SUPPRESS_CASTER_PROCS. Look: stock Arcane Missiles SV 262.',
    raw_overrides=_raw('Deals {pot1} Arcane damage.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       SpellVisualID_1=_SV_ARCANE_MISSILES, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

prototype_power_core_206842 = spell(
    id=206842, name='Prototype Power Core', school=School.ARCANE, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=12000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, base_points=2, amplitude=2000,
                    implicit_target_a=_TARGET_UNIT_CASTER, radius_yards=_CORE_RADIUS)],
    spell_icon_id=_ICON_LIGHTNING_SHIELD,
    notes='Blackrock Depths hard mode, Prototype Power Core (Golem Lord Argelmach, trinket), the Use: 2 min cooldown, '
          'off the GCD, 12 s. A PERIODIC_DUMMY every 2 s, amount 3 (BasePoints 2 + DieSides 1) = the orbs, radius '
          '10 yd: spell_brd_prototype_power_core has each orb strike an enemy in combat within 10 yd with the tier\'s '
          '206843, different enemies while there are enough. Look: stock Lightning Shield SV 37 (three circling orbs).',
    raw_overrides=_raw(
        'Three arcane orbs circle you for $d, each striking a nearby enemy every $t1 sec for '
        + pot_text(arcane_orb_strike_206843) + ' Arcane damage.',
        'Arcane orbs circle you.', SpellVisualID_1=_SV_LIGHTNING_SHIELD, **_off_gcd(),
    ),
)
scripted_by(prototype_power_core_206842, 'spell_brd_prototype_power_core')

# --- Golemwright's Mending Rod (main-hand mace, Equip) ---------------------------------------------------------------

servo_mend_206846 = spell(
    id=206846, name='Servo Mend', school=School.NATURE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, sp_potency=45.0, potency_kind='heal', time_basis_ms=_PROC_PAYOUT_MS,
                    implicit_target_a=_TARGET_UNIT_TARGET_ALLY)],
    spell_icon_id=_ICON_FLASH_HEAL,
    notes='Blackrock Depths hard mode, Golemwright\'s Mending Rod: one mend, cast by the wearer (triggered) from '
          'spell_brd_mending_servo, so the number scales with the healer. Healing potency 45, T 1.5 s (five mends '
          'over the Servo: 225). DefenseType MAGIC so spell power adds. SUPPRESS_CASTER_PROCS. Look: stock Flash Heal '
          'SV 3077.',
    raw_overrides=_raw('Heals {pot1}.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_FLASH_HEAL,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

mending_servo_206845 = spell(
    id=206845, name='Mending Servo', school=School.NATURE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, base_points=0, amplitude=2000,
                    implicit_target_a=_TARGET_UNIT_CASTER, radius_yards=_SERVO_RADIUS)],
    spell_icon_id=_ICON_FLASH_HEAL,
    notes='Blackrock Depths hard mode, Golemwright\'s Mending Rod: the healer\'s 10 s buff while the Mending Servo '
          '(creature 300656) is deployed. A PERIODIC_DUMMY every 2 s, radius 20 yd: spell_brd_mending_servo heals the '
          'group member with the lowest health fraction below full within 20 yd of the Servo with the tier\'s 206846. '
          'When the buff ends, the Servo is dismissed.',
    raw_overrides=_raw('Your Mending Servo heals the most injured party member within $a1 yd every $t1 sec for '
                       + pot_text(servo_mend_206846) + '.',
                       'A Mending Servo is deployed.', AttributesEx4=_ATTR4_NO_CAST_LOG),
)
scripted_by(mending_servo_206845, 'spell_brd_mending_servo')

golemwrights_mending_rod_206844 = _equip_aura(
    206844, "Golemwright's Mending Rod", School.NATURE,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
            implicit_target_a=_TARGET_UNIT_CASTER)],
    'Your heals have a chance to deploy a Mending Servo for $206845d, which heals the most injured party member within '
    '$206845a1 yd every $206845t1 sec for ' + pot_text(servo_mend_206846) + '.',
    _ICON_FLASH_HEAL,
    'Blackrock Depths hard mode, Golemwright\'s Mending Rod (Golem Lord Argelmach, main-hand mace), the Equip: a '
    'passive DUMMY aura with a proc. spell_proc: done positive magic and none class spells (0x4400), heal type, hit '
    'phase, normal or critical, 10%, 25 s internal cooldown (longer than the Servo). '
    'spell_brd_golemwrights_mending_rod deploys the Servo 300656 at the healed target and puts the tier\'s 206845 on '
    'the healer.',
    proc_type_mask=_HEAL_PROCS, proc_chance=10,
)
procs_on(golemwrights_mending_rod_206844, proc_flags=_HEAL_PROCS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=10.0,
         cooldown_ms=25000)
scripted_by(golemwrights_mending_rod_206844, 'spell_brd_golemwrights_mending_rod')

# --- Electron's Lethal Coil (ring, Equip) ----------------------------------------------------------------------------

lethal_arc_206849 = spell(
    id=206849, name='Lethal Arc', school=School.NATURE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=60.0, ap_potency=60.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_CHAIN_LIGHTNING,
    notes='Blackrock Depths hard mode, Electron\'s Lethal Coil: the arc, cast by the wearer (triggered) from '
          'spell_brd_electrons_lethal_coil on every other enemy in combat within 8 yd of the charged target. Nature, '
          'hybrid potency 60 SP + 60 AP, T 1.5 s (a ring with no primary). DefenseType MAGIC. SUPPRESS_CASTER_PROCS: '
          'an arc never charges or detonates anything. Look: stock Chain Lightning SV 36.',
    raw_overrides=_raw('Deals {pot1} Nature damage.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       SpellVisualID_1=_SV_CHAIN_LIGHTNING, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

lethal_attraction_206848 = spell(
    id=206848, name='Lethal Attraction', school=School.NATURE, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=8000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_CHAIN_LIGHTNING,
    notes='Blackrock Depths hard mode, Electron\'s Lethal Coil: the charge, cast by the wearer (triggered) on the '
          'target. A DUMMY debuff for 8 s, one per wearer (a new charge refreshes it). The wearer\'s next landed hit '
          'on it removes it and arcs (spell_brd_electrons_lethal_coil). DefenseType MAGIC.',
    raw_overrides=_raw('Charged. The next hit from the one who charged it arcs to nearby enemies.',
                       'Charged with Lethal Attraction.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       AttributesEx4=_ATTR4_NO_CAST_LOG),
)

electrons_lethal_coil_206847 = _equip_aura(
    206847, "Electron's Lethal Coil", School.NATURE,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=14,
            implicit_target_a=_TARGET_UNIT_CASTER, radius_yards=_ARC_RADIUS)],
    'Your damaging attacks and spells have a chance to charge the target with Lethal Attraction for $206848d. Your '
    'next hit on it arcs to every enemy within $a1 yd of it, dealing ' + pot_text(lethal_arc_206849)
    + ' Nature damage.',
    _ICON_CHAIN_LIGHTNING,
    'Blackrock Depths hard mode, Electron\'s Lethal Coil (Golem Lord Argelmach, ring), the Equip: a passive DUMMY '
    'aura, amount 15 (BasePoints 14 + DieSides 1) = the charge chance in percent, radius 8 yd = the arc. spell_proc: '
    'done melee, ranged and harmful magic and none class spells, damage type, hit phase, normal or critical, 100%, no '
    'internal cooldown: spell_brd_electrons_lethal_coil needs every hit. A hit on a target the wearer charged earlier '
    'removes the charge and casts the tier\'s 206849 on every other enemy in combat within 8 yd of it; any other hit '
    'rolls the charge chance and charges the target with the tier\'s 206848.',
    proc_type_mask=_DAMAGING_HITS, proc_chance=100,
)
procs_on(electrons_lethal_coil_206847, proc_flags=_DAMAGING_HITS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=100.0)
scripted_by(electrons_lethal_coil_206847, 'spell_brd_electrons_lethal_coil')

# =====================================================================================================================
# Hard mode: Emperor Dagran Thaurissan, the Avatar of Ragnaros

# --- Volcanic Heartstone (trinket, Use) ------------------------------------------------------------------------------

heartstone_eruption_206851 = spell(
    id=206851, name='Heartstone Eruption', school=School.FIRE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=150.0, ap_potency=150.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_SRC_CASTER,
                    implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=_HEARTSTONE_RADIUS)],
    spell_icon_id=_ICON_HELLFIRE,
    notes='Blackrock Depths hard mode, Volcanic Heartstone: the burst when the stone breaks, cast by the wearer '
          '(triggered) from spell_brd_volcanic_heartstone. Fire, every enemy within 8 yd of the wearer, hybrid '
          'potency 150 SP + 150 AP, T 1.5 s (a tank trinket with no primary: warriors and paladins both scale off it). '
          'DefenseType MAGIC. SUPPRESS_CASTER_PROCS. Look: stock Hellfire Effect SV 781.',
    raw_overrides=_raw('Deals {pot1} Fire damage to enemies within $a1 yd.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_HELLFIRE,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

volcanic_heartstone_206850 = spell(
    id=206850, name='Volcanic Heartstone', school=School.FIRE, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=8000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-21,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_STONEFORM,
    notes='Blackrock Depths hard mode, Volcanic Heartstone (Emperor Dagran Thaurissan, tank trinket), the Use: 2 min '
          'cooldown, off the GCD, 8 s. MOD_DAMAGE_PERCENT_TAKEN -20 (BasePoints -21 + DieSides 1, all schools; a '
          'percent, the same on every tier). spell_brd_volcanic_heartstone: when the stone ends any way but death, '
          'the wearer casts the tier\'s 206851. Look: stock Stoneform SV 5787.',
    raw_overrides=_raw(
        'Encase yourself in stone, reducing damage taken by $s1% for $d. When the stone breaks it bursts, dealing '
        + pot_text(heartstone_eruption_206851) + ' Fire damage to enemies within $206851a1 yd.',
        'Encased in stone. Damage taken reduced.', SpellVisualID_1=_SV_STONEFORM, **_off_gcd(),
    ),
)
scripted_by(volcanic_heartstone_206850, 'spell_brd_volcanic_heartstone')

# --- Orb of the Sorcerer-Thane (held in off-hand, Equip) -------------------------------------------------------------

shadow_beam_206853 = spell(
    id=206853, name='Shadow Beam', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=120.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_MIND_FLAY,
    notes='Blackrock Depths hard mode, Orb of the Sorcerer-Thane: the beam, cast by the wearer (triggered) from '
          'spell_brd_orb_of_the_sorcerer_thane on the target and on every other enemy in combat on the line between. '
          'Shadow, spell power potency 120, T 1.5 s. DefenseType MAGIC. SUPPRESS_CASTER_PROCS. Look: stock Shadow Bolt '
          'SV 64 (a bolt from the wearer to each enemy hit).',
    raw_overrides=_raw('Deals {pot1} Shadow damage.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       SpellVisualID_1=_SV_SHADOW_BOLT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

orb_of_the_sorcerer_thane_206852 = _equip_aura(
    206852, 'Orb of the Sorcerer-Thane', School.SHADOW,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
            implicit_target_a=_TARGET_UNIT_CASTER, radius_yards=_BEAM_HALF_WIDTH)],
    'Your damaging spells have a chance to loose a shadow beam at the target, dealing '
    + pot_text(shadow_beam_206853) + ' Shadow damage to it and to every enemy on the line between you.',
    _ICON_MIND_FLAY,
    'Blackrock Depths hard mode, Orb of the Sorcerer-Thane (Emperor Dagran Thaurissan, held in off-hand), the Equip: a '
    'passive DUMMY aura with a proc, radius 2 yd = half the beam\'s width. spell_proc: done harmful magic and none '
    'class spells, damage type, hit phase, normal or critical, 10%, 12 s internal cooldown. '
    'spell_brd_orb_of_the_sorcerer_thane casts the tier\'s 206853 on the target and on every other enemy in combat '
    'whose center is within 2 yd of the line from the wearer to the target.',
    proc_type_mask=_HARMFUL_SPELLS, proc_chance=10,
)
procs_on(orb_of_the_sorcerer_thane_206852, proc_flags=_HARMFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=10.0,
         cooldown_ms=12000)
scripted_by(orb_of_the_sorcerer_thane_206852, 'spell_brd_orb_of_the_sorcerer_thane')


# Totem of Rage's stock Equip, moved onto potency (the list's "keeps ... moved onto potency", user rule: everything on
# potency). A stock id (27859, the item keeps slot 1 with keep_spells), so it lives here instead of source/spells/
# npc.csv (one owner per spell; the csv row was removed). The aura is the stock one: OVERRIDE_CLASS_SCRIPTS 4418, read
# by Unit.cpp as flat spell power for Earth, Flame and Frost Shock (class mask 0x90010000 on effect 1). Only the amount
# changed: base potency 2.83 (an 'absorb'-kind line, no coefficient, T 1.5 s) resolves to 30 at level 60, the stock
# value, and follows the level curve below it. The item is not scale="budget": every tier carries the same spell.
increased_shock_damage_27859 = spell(
    id=27859, name='Increased Shock Damage', school=School.NORMAL, attributes=464, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.OVERRIDE_CLASS_SCRIPTS, misc_value=4418,
                    base_potency=2.83, potency_kind='absorb', implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=13,
    notes='Totem of Rage (22395), the Equip, moved onto potency (Blackrock Depths list: "keeps Increased Shock '
          'Damage"). Stock aura OVERRIDE_CLASS_SCRIPTS 4418 (Unit.cpp: flat spell power for Earth, Flame and Frost '
          'Shock); base potency 2.83 = 30 at level 60 (the stock +30), scaled below it by the level curve.',
    raw_overrides={
        'AuraDescription_Lang_Mask': 16712188, 'CastingTimeIndex': 1, 'Description_Lang_Mask': 16712190,
        'Description_Lang_enUS': 'Increases spell power of Earth Shock, Flame Shock, and Frost Shock by {pot1}.',
        'EffectBonusMultiplier_1': 1.0, 'EffectBonusMultiplier_2': 1.0, 'EffectBonusMultiplier_3': 1.0,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'EffectSpellClassMaskA_1': 2416967680, 'EquippedItemClass': -1, 'NameSubtext_Lang_Mask': 16712188,
        'Name_Lang_Mask': 16712190, 'ProcChance': 101, 'RangeIndex': 1, 'SpellClassSet': 11, 'SpellLevel': 1,
    },
)
