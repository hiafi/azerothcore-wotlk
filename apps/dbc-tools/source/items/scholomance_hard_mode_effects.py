"""
The Scholomance item effects (wave 1 dungeon items; designer text: docs/dungeons/scholomance-rework.md ## Loot, "Loot
for the encounters without a token" and "Hard mode lists", copied in docs/dungeons/dungeon-loot-vanilla.md). Despite
the file name this holds every new Scholomance item effect: the six on the normal list (Rattlegore, the instructors)
and the six on the two hard mode lists (Ras Frostwhisper, Darkmaster Gandling). The kept stock effects (Barovian Family
Sword, Frightskull Shaft, Ebon Hilt of Marduk, Silent Fang, Headmaster's Charge) stay stock spells (keep_spells=True
in scholomance.py) and are not declared here.

Every damage, healing and absorb number comes from potency (docs/potency-system.md; user rule: everything on potency,
no hand coefficients and no hand spell_bonus_data). The effects with such a number are declared with
scale="budget" on their item (stage IV10), and so are Spare Rib and the Jar (stat auras): every tier but the ladder's
effect reference tier (Heroic 66, hard mode 71) carries its own copy, potency and stat aura amounts (Spare Rib's armor,
the Jar's Intellect) times the tier's stat budget over the reference's (wave 1 integration). Percentages (the -1%
Demerit, the Chill, the +1% Honor Roll) and the Phylactery Shard's armor (unscaled item) stay the same on every tier.
The scripts are modules/mod-dungeon-bosses src/Scholomance/scholomance_items.cpp
(ids mirrored in ScholomanceItemsLogic.h).

Ids: the `scholomance_items` reservation 205620-205659 (source/ids.yaml); this file takes 205620-205642.

Normal list
  205620  Spare Rib               Rattlegore. Use (2 min): +1,000 armor for 15 sec. Bone Armor look.
  205621  Jar of Torn Souls       Malicia. Equip: a passive PROC_TRIGGER_SPELL aura. Landed damaging spells (magic and
                                  none class), 15%, no internal cooldown, cast 205622.
  205622  Torn Soul               +10 Intellect for 10 sec, stacks to 5 (CumulativeAura), each proc refreshes.
  205623  Rib Spreader            Krastinov. Equip: PROC_TRIGGER_SPELL. Landed melee hits (auto attacks and melee
                                  spells), 15%, 6 sec internal cooldown (the wound's length), cast 205624 on the target.
  205624  Open Wound              the bleed: Physical, mechanic bleed, 6 sec, a tick every 2 sec, attack power potency
                                  15 a tick (time basis = the tick), so the whole bleed adds up to one 1.5 sec
                                  off-GCD payout of potency 60. DefenseType MELEE.
  205625  Polkelt's Specimen Launcher  Polkelt. Equip: PROC_TRIGGER_SPELL. Landed ranged hits (Auto Shot and ranged
                                  spells, 0x140), 10%, 10 sec internal cooldown (approved 2026-11-02), cast 205626 at
                                  the target.
  205626  Specimen Acid           the pool: a persistent area aura on the ground under the target (TARGET_DEST_TARGET_
                                  ENEMY / TARGET_DEST_DYNOBJ_ENEMY), 6 yd, 6 sec, Nature damage every sec to enemies in
                                  it, attack power potency 22.5 a tick: one 1.5 sec payout of 90 per target.
                                  DefenseType RANGED plus the ranged weapon subclass mask, so it scales with ranged
                                  attack power (SpellInfo::IsRangedWeaponSpell; EquippedItemClass stays -1, so no
                                  weapon is required). Slime Pool look.
  205627  The Dean's Rod          Alexei. Equip: PROC_TRIGGER_SPELL. Taken melee attacks the wielder parried
                                  (hit mask PARRY), 100%, cast 205628 on the attacker.
  205628  Demerit                 the attacker deals 1% less damage, stacks to 5, 30 sec, refreshed by each parry.
                                  Debuff text approved: "Has earned a Demerit. Deals less damage."
  205629  Krastinov's Suture Kit  Krastinov. Use (2 min): a 20 sec buff with 3 charges. Landed direct heals (positive
                                  magic and none class spells, heal type, hit phase: a heal over time's cast heals
                                  nothing then) cast 205630 on the healed target and use a charge.
  205630  Stitches                a heal over time on the healed target: 6 sec, a tick every 2 sec, healing
                                  potency 18.75 a tick: one 1.5 sec payout of 75 over the whole stitch.

Hard mode lists
  205631  Phylactery Shard        Ras. Use (2 min): +1,500 armor for 10 sec (effect 1) and a DUMMY (effect 2) whose
                                  amount, 30, is the percent. spell_proc: any damage taken, 100%.
                                  spell_scholo_phylactery_shard adds up the damage taken while it is up; when it ends
                                  (any way but death) the wearer casts 205632 for 30% of it.
  205632  Phylactery Mend         the heal, sized by the script (custom base points). A percent of damage taken, so it
                                  is out of potency by design (potency_excluded) and DefenseType 0, so spell power
                                  does not add to it.
  205633  Frostwhisper's Chillband  Ras. Equip: PROC_TRIGGER_SPELL. Landed damaging attacks and spells, 15%, 6 sec
                                  internal cooldown (the Chill's length), cast 205634 on the target.
  205634  Chill                   the target attacks (MOD_MELEE_HASTE, as Thunder Clap) and casts (HASTE_SPELLS, as
                                  Curse of Tongues) 10% slower for 6 sec. Frost, magic dispel.
  205635  Bonechill Blade         Ras. Equip: PROC_TRIGGER_SPELL. Landed harmful spells (magic and none class), 20%,
                                  10 sec internal cooldown, cast 205636 on the target. spell_scholo_bonechill_blade's
                                  CheckProc lets one cast roll only once (designer: "rolls once per cast"; an area
                                  spell would otherwise roll on every target it hits).
  205636  Frost Blast             a copy of stock Frost Blast 18276 (Frost, single target, stock look and icon) with
                                  spell power potency 120 (T 1.5 sec, an off-GCD payout) in place of its flat 90.
  205637  Transfer Papers         Gandling. Use (2 min): swap places with a friendly party member within 30 yd
                                  (TARGET_UNIT_TARGET_PARTY). spell_scholo_transfer_papers checks the target and does
                                  the swap. No damage or healing: full stat budget on the item (budget_mult 1.0).
  205638  Honor Roll Ribbon       Gandling. Equip: a passive PERIODIC_TRIGGER_SPELL aura, 205639 every 30 sec.
  205639  Honor Roll              30 sec: a shield that absorbs all schools (absorb potency, base only: base_potency 30,
                                  about 320 at level 60, the designer's starting guess of 5% of reference health)
                                  plus +1% damage done and +1% healing done. A depleted absorb removes the whole aura
                                  (Unit.cpp), so the bonus ends with the shield; the next 30 sec tick puts it back.
  205640  Darkmaster's Portal Rod Gandling. Equip: a passive DUMMY aura with a proc. Landed damaging spells (magic and
                                  none class), 10%, 15 sec internal cooldown. spell_scholo_darkmasters_portal_rod
                                  summons the portal (creature 300465, source/npcs/scholomance/hard_mode_items.py)
                                  behind the target, the portal casts its look 205642, and the wearer casts 205641.
  205641  Portal Barrage          Arcane, 3 sec, a tick every 0.6 sec (5 missiles), spell power potency 75 a tick:
                                  one 1.5 sec payout of 150 over the barrage. Arcane Missiles look.
  205642  Darkmaster's Portal     the portal's 3 sec ground aura (Summoning Portal look) under it, no effect.
  205643-205659  spare

Chances, internal cooldowns, potencies, armor, Intellect and buff windows are proposals waiting for the designer
(STAGE-W1-SCHOLO report, designer questions). None of the looks were checked in game.
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
_TARGET_DEST_DYNOBJ_ENEMY = 28
_TARGET_DEST_DYNOBJ_ALLY = 29
_TARGET_UNIT_TARGET_PARTY = 35
_TARGET_DEST_TARGET_ENEMY = 53
_TARGET_DEST_DEST = 87

# Aura types the DSL enum does not name (SpellAuraDefines.h)
_AURA_MOD_RESISTANCE = 22
_AURA_HASTE_SPELLS = 216

_ATTR0_PASSIVE = 0x00000040
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR4_NO_CAST_LOG = 0x00000001

_DMG_CLASS_MAGIC = 1
_DMG_CLASS_MELEE = 2
_DMG_CLASS_RANGED = 3

_DISPEL_MAGIC = 1
_MECHANIC_BLEED = 15
_SCHOOL_MASK_ALL = 127
_SCHOOL_MASK_NORMAL = 1   # MOD_RESISTANCE misc value: armor
_STAT_INTELLECT = 3       # MOD_STAT misc value
_RANGED_WEAPON_SUBCLASS_MASK = (1 << 2) | (1 << 3) | (1 << 18) | (1 << 16)  # bow, gun, crossbow, thrown

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
_PROC_FLAG_TAKEN_DAMAGE = 0x00100000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_TYPE_HEAL = 0x2
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_NORMAL_OR_CRITICAL = 0x1 | 0x2
_PROC_HIT_PARRY = 0x20

_MELEE_HITS = _PROC_FLAG_DONE_MELEE_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS
_RANGED_HITS = _PROC_FLAG_DONE_RANGED_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
_HARMFUL_SPELLS = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG
_HELPFUL_SPELLS = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS
_TAKEN_MELEE = _PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK | _PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS

# Stock looks and icons, picked by name (none checked in game yet).
_SV_BONE_ARMOR = 2737           # Bone Armor 11445
_ICON_BONE_ARMOR = 93
_ICON_SHADOWFORM = 217          # Torn Soul (no visual of its own)
_SV_REND = 372                  # Rend 772
_ICON_REND = 245
_SV_SLIME_POOL = 14287          # Slime Pool 66883: a persistent pool on the ground
_ICON_SLIME_POOL = 263
_SV_DEMORALIZING_SHOUT = 210    # Demoralizing Shout 1160
_ICON_DEMORALIZING_SHOUT = 282
_SV_FIRST_AID = 100             # First Aid 746
_ICON_FIRST_AID = 104
_SV_ICE_BARRIER = 4302          # Ice Barrier 11426: the ice around the heart
_ICON_ICE_BARRIER = 32
_SV_CHILLED = 675               # Chilled 6136
_ICON_FROST_ARMOR = 181
_SV_FROST_BLAST = 13            # stock Frost Blast 18276
_ICON_FROST_BLAST = 188
_SV_BLINK = 263                 # Blink 1953
_ICON_BLINK = 1499
_SV_POWER_WORD_SHIELD = 784     # Power Word: Shield 17
_ICON_POWER_WORD_SHIELD = 566
_SV_ARCANE_MISSILES = 262       # Arcane Missiles 5143
_ICON_ARCANE_MISSILES = 225
_SV_SUMMONING_PORTAL = 4020     # Summoning Portal 16136: a persistent portal on the ground
_ICON_SUMMONING_PORTAL = 1490

# An off-GCD proc payout's time basis (the Deadmines items' precedent). A periodic payout keeps the tick as its time
# basis (the potency model counts ticks as duration / time basis) and takes potency per tick = payout potency x 1.5 s
# / duration, which adds up to the same total.
_PROC_PAYOUT_MS = 1500


def _raw(desc: str = '', aura_desc: str = '', spell_level: int = 0, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': spell_level, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_TEXT_MASKS, **more}


def _off_gcd() -> dict:
    return {'StartRecoveryCategory': 0, 'StartRecoveryTime': 0}


def _equip_aura(spell_id: int, name: str, aura: int, desc: str, icon: int, notes: str, *, trigger: int = 0,
                proc_type_mask: int = 0, proc_chance: int = 0, amplitude: int = 0) -> object:
    """A passive Equip aura on the wearer (an item's equip spell)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_PASSIVE, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=0, trigger_spell=trigger,
                        amplitude=amplitude, implicit_target_a=_TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=_raw(desc, ProcTypeMask=proc_type_mask, ProcChance=proc_chance),
    )


# =====================================================================================================================
# Normal list

# --- Spare Rib (Rattlegore, trinket, Use) ----------------------------------------------------------------------------

spare_rib_205620 = spell(
    id=205620, name='Spare Rib', school=School.NORMAL, cast_time_ms=0, cooldown_ms=120000, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=15000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_RESISTANCE, base_points=999,
                    misc_value=_SCHOOL_MASK_NORMAL, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BONE_ARMOR,
    notes='Scholomance items, Spare Rib (Rattlegore, tank trinket), the Use: brace a loose rib across your chest, '
          '+1,000 armor (MOD_RESISTANCE, armor) for 15 s, 2 min cooldown, off the GCD. The armor is the same on every '
          'tier (an aura amount, not potency). Look: stock Bone Armor SV 2737.',
    raw_overrides=_raw('Brace a loose rib across your chest, increasing your armor by $s1 for $d.', 'Armor increased.',
                       SpellVisualID_1=_SV_BONE_ARMOR, **_off_gcd()),
)

# --- Jar of Torn Souls (Instructor Malicia, trinket, Equip) ----------------------------------------------------------

torn_soul_205622 = spell(
    id=205622, name='Torn Soul', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STAT, base_points=9,
                    misc_value=_STAT_INTELLECT, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SHADOWFORM,
    notes='Scholomance items, Jar of Torn Souls: the Soul. +10 Intellect for 10 s, stacks up to 5 (CumulativeAura), '
          'each new Soul refreshes the stack. Triggered by 205621 (on the wearer whatever the proc target: '
          'TARGET_UNIT_CASTER).',
    raw_overrides=_raw('Intellect increased by $s1.', 'Intellect increased.', CumulativeAura=5),
)

jar_of_torn_souls_205621 = _equip_aura(
    205621, 'Jar of Torn Souls', AuraType.PROC_TRIGGER_SPELL,
    'Your damaging spells have a chance to tear loose a Soul, increasing your Intellect by $205622s1 for $205622d, '
    'stacking up to $205622u times.',
    _ICON_SHADOWFORM,
    'Scholomance items, Jar of Torn Souls (Instructor Malicia, caster trinket), the Equip: a passive '
    'PROC_TRIGGER_SPELL aura that casts 205622. spell_proc: done harmful magic and none class spells, damage type, hit '
    'phase, normal or critical, 15%, no internal cooldown (the stack needs frequent procs). Item auras get no Proc '
    'Chance (Systems.md section 5).',
    trigger=torn_soul_205622.id, proc_type_mask=_HARMFUL_SPELLS, proc_chance=15,
)
procs_on(jar_of_torn_souls_205621, proc_flags=_HARMFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=15.0)

# --- Rib Spreader (Doctor Theolen Krastinov, fist weapon, Equip) -----------------------------------------------------

open_wound_205624 = spell(
    id=205624, name='Open Wound', school=School.NORMAL, mechanic=_MECHANIC_BLEED,
    attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=6000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000,
                    ap_potency=15.0, potency_kind='periodic',
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_REND,
    notes='Scholomance items, Rib Spreader: the wound. Physical bleed (mechanic 15, so armor does not reduce it), '
          '6 s, a tick every 2 s, attack power potency 15 a tick (time basis = the tick): the whole bleed adds up to '
          'one 1.5 s off-GCD payout of potency 60. DefenseType MELEE. Cast by the wearer (triggered by 205623), so it '
          'procs nothing. A new wound refreshes the old one. Look: stock Rend SV 372.',
    raw_overrides=_raw('Deals {pot1} Physical damage every $t1 sec for $d.', 'Bleeding.', spell_level=1,
                       DefenseType=_DMG_CLASS_MELEE, SpellVisualID_1=_SV_REND),
)

rib_spreader_205623 = _equip_aura(
    205623, 'Rib Spreader', AuraType.PROC_TRIGGER_SPELL,
    'Your melee attacks have a chance to open a wound that bleeds the target for '
    + pot_text(open_wound_205624, variant='total') + ' Physical damage over $205624d.',
    _ICON_REND,
    'Scholomance items, Rib Spreader (Doctor Theolen Krastinov, fist weapon), the Equip: a passive PROC_TRIGGER_SPELL '
    'aura that casts 205624 on the target. spell_proc: done melee auto attacks and melee-class spells (0x14), damage '
    'type, hit phase, normal or critical, 15%, 6 s internal cooldown (the wound\'s length, so a wound is never '
    'clipped). Any melee hit of the wearer counts (either hand), as the Deadmines Signet.',
    trigger=open_wound_205624.id, proc_type_mask=_MELEE_HITS, proc_chance=15,
)
procs_on(rib_spreader_205623, proc_flags=_MELEE_HITS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=15.0,
         cooldown_ms=6000)

# --- Polkelt's Specimen Launcher (Lorekeeper Polkelt, gun, Equip) ----------------------------------------------------

specimen_acid_205626 = spell(
    id=205626, name='Specimen Acid', school=School.NATURE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=6000,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000,
                    ap_potency=22.5, potency_kind='periodic',
                    implicit_target_a=_TARGET_DEST_TARGET_ENEMY, implicit_target_b=_TARGET_DEST_DYNOBJ_ENEMY,
                    radius_yards=6.0)],
    spell_icon_id=_ICON_SLIME_POOL,
    notes='Scholomance items, Polkelt\'s Specimen Launcher: the flask of acid (Polkelt\'s Ripe pools). A 6 yd pool on '
          'the ground under the target for 6 s (TARGET_DEST_TARGET_ENEMY / TARGET_DEST_DYNOBJ_ENEMY), Nature damage '
          'every second to enemies standing in it (uncapped). Attack power potency 22.5 a tick (time basis = the '
          'tick): the whole pool adds up to one 1.5 s off-GCD payout of potency 90 per target. DefenseType RANGED '
          'and the ranged weapon subclass mask make the server add ranged attack power '
          '(SpellInfo::IsRangedWeaponSpell); '
          'EquippedItemClass -1 keeps the cast free of any weapon requirement. The 10 s internal cooldown is longer '
          'than the pool, so only one pool is ever down. Look: stock Slime Pool SV 14287.',
    raw_overrides=_raw('Deals {pot1} Nature damage every $t1 sec to enemies standing in the acid.', 'Dissolving.',
                       spell_level=1, DefenseType=_DMG_CLASS_RANGED, EquippedItemSubclass=_RANGED_WEAPON_SUBCLASS_MASK,
                       SpellVisualID_1=_SV_SLIME_POOL),
)

polkelts_specimen_launcher_205625 = _equip_aura(
    205625, "Polkelt's Specimen Launcher", AuraType.PROC_TRIGGER_SPELL,
    'Your ranged attacks have a chance to fire a flask of acid that splashes the ground under the target, dealing '
    + pot_text(specimen_acid_205626, variant='total') + ' Nature damage over $205626d to enemies in the pool.',
    _ICON_SLIME_POOL,
    'Scholomance items, Polkelt\'s Specimen Launcher (Lorekeeper Polkelt, gun), the Equip: a passive '
    'PROC_TRIGGER_SPELL aura that casts 205626 at the target. spell_proc: done ranged auto attacks and ranged-class '
    'spells (0x140), damage type, hit phase, normal or critical, 10%, 10 s internal cooldown (approved 2026-11-02: '
    'one roll per ranged hit, never more than 6 pools a minute).',
    trigger=specimen_acid_205626.id, proc_type_mask=_RANGED_HITS, proc_chance=10,
)
procs_on(polkelts_specimen_launcher_205625, proc_flags=_RANGED_HITS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=10.0,
         cooldown_ms=10000)

# --- The Dean's Rod (Lord Alexei Barov, one-hand mace, Equip) --------------------------------------------------------

demerit_205628 = spell(
    id=205628, name='Demerit', school=School.NORMAL, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=30000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=-2,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_DEMORALIZING_SHOUT,
    notes='Scholomance items, The Dean\'s Rod: the Demerit (the item version of Alexei\'s AB9 Demerits). The attacker '
          'deals 1% less damage to everyone (BasePoints -2 + DieSides 1, all schools), stacks up to 5, 30 s, each '
          'parry adds a stack and refreshes it. Not dispellable. Debuff text approved 2026-11-02. Look: stock '
          'Demoralizing Shout SV 210.',
    raw_overrides=_raw('Deals $s1% less damage. Stacks up to $u times.', 'Has earned a Demerit. Deals less damage.',
                       CumulativeAura=5, SpellVisualID_1=_SV_DEMORALIZING_SHOUT),
)

the_deans_rod_205627 = _equip_aura(
    205627, "The Dean's Rod", AuraType.PROC_TRIGGER_SPELL,
    'Your parries give the attacker a Demerit, reducing the damage it deals by $205628s1% for $205628d. Stacks up to '
    '$205628u times.',
    _ICON_DEMORALIZING_SHOUT,
    'Scholomance items, The Dean\'s Rod (Lord Alexei Barov, Strength tank mace), the Equip: a passive '
    'PROC_TRIGGER_SPELL aura that casts 205628 on the attacker (a taken proc\'s proc target is the attacker). '
    'spell_proc: taken melee auto attacks and melee-class spells (0x28), hit mask PARRY, 100%, no internal cooldown: '
    'the parry is the gate (approved 2026-11-02; items get no Proc Chance).',
    trigger=demerit_205628.id, proc_type_mask=_TAKEN_MELEE, proc_chance=100,
)
procs_on(the_deans_rod_205627, proc_flags=_TAKEN_MELEE, hit_mask=_PROC_HIT_PARRY, chance=100.0)

# --- Krastinov's Suture Kit (Doctor Theolen Krastinov, trinket, Use) -------------------------------------------------

stitches_205630 = spell(
    id=205630, name='Stitches', school=School.NATURE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=6000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_HEAL, amplitude=2000,
                    sp_potency=18.75, potency_kind='heal_periodic',
                    implicit_target_a=_TARGET_UNIT_TARGET_ALLY)],
    spell_icon_id=_ICON_FIRST_AID,
    notes='Scholomance items, Krastinov\'s Suture Kit: the stitch. A heal over time on the healed target, 6 s, a tick '
          'every 2 s, healing potency 18.75 a tick (time basis = the tick): the whole stitch adds up to one 1.5 s '
          'payout of potency 75. DefenseType MAGIC so spell power adds. Cast by the healer (triggered by 205629), so '
          'it procs nothing and uses no charge; a new stitch on the same target refreshes it. Look: stock First Aid '
          'SV 100.',
    raw_overrides=_raw('Heals {pot1} every $t1 sec for $d.', 'Stitched.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_FIRST_AID),
)

krastinovs_suture_kit_205629 = spell(
    id=205629, name="Krastinov's Suture Kit", school=School.NATURE, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=20000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, base_points=0,
                    trigger_spell=stitches_205630.id, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FIRST_AID,
    notes='Scholomance items, Krastinov\'s Suture Kit (Doctor Theolen Krastinov, healer trinket), the Use: 2 min '
          'cooldown, off the GCD, a visible 20 s buff with 3 charges. spell_proc: done positive magic and none class '
          'spells (0x4400), heal type, hit phase (a heal over time\'s cast heals nothing then, so only direct heals '
          'count), 100%, 3 charges. Each casts 205630 on the healed target (the proc target).',
    raw_overrides=_raw(
        'Your next $n direct heals within $d also stitch the target, healing it for '
        + pot_text(stitches_205630, variant='total') + ' over $205630d.',
        'Your direct heals stitch the target.',
        ProcTypeMask=_HELPFUL_SPELLS, ProcChance=100, ProcCharges=3, SpellVisualID_1=_SV_FIRST_AID, **_off_gcd(),
    ),
)
procs_on(krastinovs_suture_kit_205629, proc_flags=_HELPFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=100.0, charges=3)

# =====================================================================================================================
# Hard mode: Ras Frostwhisper, the Torn Keepsake

# --- Phylactery Shard (trinket, Use) ---------------------------------------------------------------------------------

phylactery_mend_205632 = spell(
    id=205632, name='Phylactery Mend', school=School.FROST, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=_TARGET_UNIT_CASTER,
                    potency_excluded='a percent of the damage taken while 205631 was up, sized by '
                                     'spell_scholo_phylactery_shard (custom base points)')],
    spell_icon_id=_ICON_ICE_BARRIER,
    notes='Scholomance items, Phylactery Shard: the heal when the ice ends. Cast by the wearer on themselves from '
          'spell_scholo_phylactery_shard with custom base points = 205631 effect 2\'s percent of the damage taken '
          'while it was up. Out of potency by design (a percent of damage taken); DefenseType 0 so spell power does '
          'not add to it. Same on every tier.',
    raw_overrides=_raw('Heals you.'),
)

phylactery_shard_205631 = spell(
    id=205631, name='Phylactery Shard', school=School.FROST, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_RESISTANCE, base_points=1499,
               misc_value=_SCHOOL_MASK_NORMAL, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=29,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_ICE_BARRIER,
    notes='Scholomance items, Phylactery Shard (Ras Frostwhisper hard mode, tank trinket), the Use: 2 min cooldown, '
          'off the GCD. Effect 1: +1,500 armor for 10 s. Effect 2: a DUMMY whose amount (30) is the percent healed. '
          'spell_proc: any damage taken (PROC_FLAG_TAKEN_DAMAGE), 100%, no cooldown; '
          'spell_scholo_phylactery_shard adds up the damage taken while the aura is up and, when it ends any way but '
          'death, casts 205632 for that percent of it. Look: stock Ice Barrier SV 4302.',
    raw_overrides=_raw(
        'Ice hardens around your heart, increasing your armor by $s1 for $d. When it ends, heals you for $s2% of the '
        'damage you took while it was active.',
        'Armor increased. Heals you when it ends.',
        ProcTypeMask=_PROC_FLAG_TAKEN_DAMAGE, ProcChance=100, SpellVisualID_1=_SV_ICE_BARRIER, **_off_gcd(),
    ),
)
procs_on(phylactery_shard_205631, proc_flags=_PROC_FLAG_TAKEN_DAMAGE, chance=100.0)
scripted_by(phylactery_shard_205631, 'spell_scholo_phylactery_shard')

# --- Frostwhisper's Chillband (ring, Equip) --------------------------------------------------------------------------

_DAMAGING_HITS = _MELEE_HITS | _RANGED_HITS | _HARMFUL_SPELLS

chill_205634 = spell(
    id=205634, name='Chill', school=School.FROST, dispel=_DISPEL_MAGIC, attributes=_ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=-11,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_HASTE_SPELLS, base_points=-11,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_FROST_ARMOR,
    notes='Scholomance items, Frostwhisper\'s Chillband: the Chill. The target attacks 10% slower (MOD_MELEE_HASTE '
          '-10, the Thunder Clap pattern) and casts 10% slower (HASTE_SPELLS -10, the Curse of Tongues pattern) for '
          '6 s. Frost, magic dispel. A new Chill refreshes it. Look: stock Chilled SV 675.',
    raw_overrides=_raw('Attack and casting speed slowed by $s1%.', 'Attack and casting speed slowed.',
                       SpellVisualID_1=_SV_CHILLED),
)

frostwhispers_chillband_205633 = _equip_aura(
    205633, "Frostwhisper's Chillband", AuraType.PROC_TRIGGER_SPELL,
    'Your damaging attacks and spells have a chance to Chill the target, slowing its attack and casting speed by '
    '$205634s1% for $205634d.',
    _ICON_FROST_ARMOR,
    'Scholomance items, Frostwhisper\'s Chillband (Ras Frostwhisper hard mode, ring), the Equip: a passive '
    'PROC_TRIGGER_SPELL aura that casts 205634 on the target. spell_proc: done melee, ranged and harmful magic and '
    'none class spells, damage type, hit phase, normal or critical, 15%, 6 s internal cooldown (the Chill\'s length).',
    trigger=chill_205634.id, proc_type_mask=_DAMAGING_HITS, proc_chance=15,
)
procs_on(frostwhispers_chillband_205633, proc_flags=_DAMAGING_HITS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=15.0,
         cooldown_ms=6000)

# --- Bonechill Blade (one-hand sword, Equip) -------------------------------------------------------------------------

bonechill_frost_blast_205636 = spell(
    id=205636, name='Frost Blast', school=School.FROST, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=120.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_FROST_BLAST,
    notes='Scholomance items, Bonechill Blade: the blast, a copy of stock Frost Blast 18276 (Frost, one target, its '
          'look SV 13 and icon 188) with spell power potency 120 at T 1.5 s (an off-GCD payout) in place of the stock '
          'flat 90. DefenseType MAGIC. Cast by the wearer (triggered by 205635), so it procs nothing.',
    raw_overrides=_raw('Blasts a target for {pot1} Frost damage.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       SpellVisualID_1=_SV_FROST_BLAST),
)

bonechill_blade_205635 = _equip_aura(
    205635, 'Bonechill Blade', AuraType.PROC_TRIGGER_SPELL,
    'Your harmful spells have a chance to blast the target for ' + pot_text(bonechill_frost_blast_205636)
    + ' Frost damage.',
    _ICON_FROST_BLAST,
    'Scholomance items, Bonechill Blade (Ras Frostwhisper hard mode, caster sword; the stock Bonechill Hammer moved '
    'to the hard mode list as a sword), the Equip: a passive PROC_TRIGGER_SPELL aura that casts 205636 on the '
    'target. spell_proc: done harmful magic and none class spells, damage type, hit phase, normal or critical, 20%, '
    '10 s internal cooldown. spell_scholo_bonechill_blade\'s CheckProc lets each cast roll once (designer: "rolls '
    'once per cast"): an area spell reaches the roll on its first target only.',
    trigger=bonechill_frost_blast_205636.id, proc_type_mask=_HARMFUL_SPELLS, proc_chance=20,
)
procs_on(bonechill_blade_205635, proc_flags=_HARMFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=20.0,
         cooldown_ms=10000)
scripted_by(bonechill_blade_205635, 'spell_scholo_bonechill_blade')

# =====================================================================================================================
# Hard mode: Darkmaster Gandling, the honors program

# --- Transfer Papers (trinket, Use) ----------------------------------------------------------------------------------

transfer_papers_205637 = spell(
    id=205637, name='Transfer Papers', school=School.ARCANE, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=30.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_PARTY)],
    spell_icon_id=_ICON_BLINK,
    notes='Scholomance items, Transfer Papers (Darkmaster Gandling hard mode, trinket), the Use: swap places with a '
          'friendly party member within 30 yd, 2 min cooldown, off the GCD. TARGET_UNIT_TARGET_PARTY; '
          'spell_scholo_transfer_papers refuses a target that is not another living player in the caster\'s group, '
          'or either side on a taxi or a vehicle, and does the swap (each keeps its own facing). Line of sight is the '
          'normal spell check. No damage or healing, so the item has the full stat budget. Look: stock Blink SV 263.',
    raw_overrides=_raw('Swap places with a friendly party member within 30 yd.', SpellVisualID_1=_SV_BLINK,
                       **_off_gcd()),
)
scripted_by(transfer_papers_205637, 'spell_scholo_transfer_papers')

# --- Honor Roll Ribbon (neck, Equip) ---------------------------------------------------------------------------------

honor_roll_205639 = spell(
    id=205639, name='Honor Roll', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=_SCHOOL_MASK_ALL,
               base_potency=30.0, potency_kind='absorb', implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=0,
               misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=0,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_POWER_WORD_SHIELD,
    notes='Scholomance items, Honor Roll Ribbon: the Honor Roll. 30 s: absorbs damage of every school (absorb '
          'potency, base only: base_potency 30, about 320 at level 60, the designer\'s starting guess of 5% of '
          'reference health; no spell power coefficient, SCHOOL_ABSORB gets none from the engine anyway), +1% damage '
          'done and +1% healing done (BasePoints 0 + DieSides 1). A depleted absorb removes the whole aura '
          '(Unit.cpp), so the bonus ends with the shield; the Ribbon\'s next 30 s tick puts it back. Look: stock '
          'Power Word: Shield SV 784.',
    raw_overrides=_raw('Absorbs {pot1} damage. While the shield holds, your damage and healing are increased by $s2%.',
                       'On the Honor Roll: damage and healing increased.',
                       SpellVisualID_1=_SV_POWER_WORD_SHIELD),
)

honor_roll_ribbon_205638 = _equip_aura(
    205638, 'Honor Roll Ribbon', AuraType.PERIODIC_TRIGGER_SPELL,
    'Every $t1 sec you are placed on the Honor Roll, gaining a shield that absorbs ' + pot_text(honor_roll_205639)
    + ' damage. While the shield holds, your damage and healing are increased by $205639s2%.',
    _ICON_POWER_WORD_SHIELD,
    'Scholomance items, Honor Roll Ribbon (Darkmaster Gandling hard mode, neck), the Equip: a passive '
    'PERIODIC_TRIGGER_SPELL aura, 205639 every 30 s (the first 30 s after equipping). No script.',
    trigger=honor_roll_205639.id, amplitude=30000,
)

# --- Darkmaster's Portal Rod (held in off-hand, Equip) ---------------------------------------------------------------

portal_barrage_205641 = spell(
    id=205641, name='Portal Barrage', school=School.ARCANE, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=3000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=600,
                    sp_potency=75.0, potency_kind='periodic',
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_ARCANE_MISSILES,
    notes='Scholomance items, Darkmaster\'s Portal Rod: the stream of arcane missiles. Arcane, 3 s, a tick every '
          '0.6 s (5 missiles), spell power potency 75 a tick (time basis = the tick): the whole barrage adds up to one '
          '1.5 s off-GCD payout of potency 150. DefenseType MAGIC. Cast by the wearer (triggered by '
          'spell_scholo_darkmasters_portal_rod), so it procs nothing. Look: stock Arcane Missiles SV 262.',
    raw_overrides=_raw('Deals {pot1} Arcane damage every $t1 sec for $d.', 'Under fire from a portal.',
                       spell_level=1, DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_ARCANE_MISSILES),
)

darkmasters_portal_look_205642 = spell(
    id=205642, name="Darkmaster's Portal", school=School.ARCANE,
    attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=3000,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_DEST_DEST, implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY,
                    radius_yards=1.0)],
    spell_icon_id=_ICON_SUMMONING_PORTAL,
    notes='Scholomance items, Darkmaster\'s Portal Rod: the portal behind the target, visual only. A hidden 3 s ground '
          'aura (TARGET_DEST_DEST / TARGET_DEST_DYNOBJ_ALLY, the Deadmines fuse mark\'s shape; its DUMMY aura does '
          'nothing) cast by the summoned portal 300465 at its feet. Look: stock Summoning Portal SV 4020. The same on '
          'every tier (the script casts it by its own id).',
    raw_overrides=_raw(SpellVisualID_1=_SV_SUMMONING_PORTAL, AttributesEx4=_ATTR4_NO_CAST_LOG),
)

darkmasters_portal_rod_205640 = _equip_aura(
    205640, "Darkmaster's Portal Rod", AuraType.DUMMY,
    'Your damaging spells have a chance to open a portal behind the target that fires a stream of arcane missiles at '
    'it, dealing ' + pot_text(portal_barrage_205641, variant='total') + ' Arcane damage over $205641d.',
    _ICON_ARCANE_MISSILES,
    'Scholomance items, Darkmaster\'s Portal Rod (Darkmaster Gandling hard mode, held in off-hand), the Equip: a '
    'passive DUMMY aura with a proc. spell_proc: done harmful magic and none class spells, damage type, hit phase, '
    'normal or critical, 10%, 15 s internal cooldown. spell_scholo_darkmasters_portal_rod opens the portal look '
    '205642 behind the target and the wearer casts the tier\'s 205641 on it (triggered, so it procs nothing).',
    proc_type_mask=_HARMFUL_SPELLS, proc_chance=10,
)
procs_on(darkmasters_portal_rod_205640, proc_flags=_HARMFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=10.0,
         cooldown_ms=15000)
scripted_by(darkmasters_portal_rod_205640, 'spell_scholo_darkmasters_portal_rod')
