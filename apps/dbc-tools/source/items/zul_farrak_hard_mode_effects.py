"""
The three Zul'Farrak hard mode item effects (designer text: docs/dungeons/zul-farrak-rework.md ## Loot, "Hard mode:
Gahz'rilla, The Crew at the Pool", approved 2026-11-24, ruling 47): Scale of the Storm God, Stormcharged Fang and
Sergeant's Whistle. After the Ragefire Chasm precedent (ragefire_chasm_hard_mode_effects.py).

Both damage numbers come from potency (user rule: everything on potency); the Whistle's copied heal is a share of a heal
that already carries the healer's bonuses and crit, sized by its script. All three items are scale="budget"
(zul_farrak_hard_mode.py): every tier above the hard mode ladder's 71 carries its own copies of the Scale and its
discharge, of the Fang and its arc, and of the Whistle (its share, `scale_amount=True`, the Scarlet Monastery review m5
precedent) (lib/item_spell_copies.py), so a script casts its tier's copy (ItemSpellCopies::Resolve). The two charge
buffs and the Crew's Aid stay one spell for every tier: they carry no number that grows, so no tooltip names their ids.
The scripts are modules/mod-dungeon-bosses src/ZulFarrak/hard_mode_items.cpp (ids mirrored in
ZulFarrakHardModeItemsLogic.h); the Whistle's crew, look only, is source/npcs/zul_farrak/hard_mode_items.py (creatures
301000-301004).

Ids: the `zul_farrak_items` reservation 213800-213839 (source/ids.yaml); this file takes 213800-213807.

  213800  Scale of the Storm God  Equip: a passive proc aura, effect 1 DUMMY amount 10 = the stacks a discharge needs,
                                  effect 2 DUMMY amount 6 = the seconds between two discharges. Taken direct hits and
                                  done melee-class abilities, 100%. spell_zf_scale_of_the_storm_god: each hit that deals
                                  damage to the wearer gives one 213801 (an area hit, a triggered hit too); a melee
                                  ability that lands at 10 stacks takes them all and casts the tier's 213802.
  213801  Static Charge           the stacks on the wearer, up to 10, 30 sec, refreshed by each hit. No effect.
  213802  Static Discharge        Nature, every enemy in combat within 8 yd of the wearer, attack power potency 90.
                                  spell_zf_static_discharge is the in-combat filter.
  213803  Stormcharged Fang       Equip: a passive proc aura, effect 1 DUMMY amount 5 = the charges an arc needs,
                                  radius 10 yd = how far from the target it arcs, effect 2 DUMMY amount 2 = the enemies
                                  it arcs to. Landed damaging spells, 100%. spell_zf_stormcharged_fang: a critical hit
                                  gives one 213804, once per cast; at 5 the next cast that lands near other enemies in
                                  combat takes them all and casts the tier's 213805 on the two nearest to its target.
  213804  Stormcharged            the charges on the wearer, up to 5, 30 sec, refreshed by each critical hit. No effect.
  213805  Storm Arc               Nature, one enemy, spell power potency 150.
  213806  Sergeant's Whistle      Use (2 min, off the GCD): 12 sec on the wearer, effect 1 DUMMY amount 40 = the share
                                  of the heal in percent (grows with the tier: 40 / 42 / 44 / 50), radius 10 yd = how
                                  far from the healed target it looks, effect 2 DUMMY amount 2 = the allies it heals.
                                  Landed heals and heal over time ticks, 100%. spell_zf_sergeants_whistle copies the
                                  wearer's single target heals (213807) and shows the crew while it lasts.
  213807  The Crew's Aid          the copied heal, sized by the script. No potency, no crit, no procs.
  213808         Call of Sul'thraze, the list's join (zul_farrak_effects.py)
  213809-213839  spare

In-combat filter: both damage effects reach only enemies already in combat (designer text, ruling 47; gear handoff
section 5), so neither pulls a pack. The Scarlet and Ragefire short areas (ruling B8, 1A) do not filter: a designer
question.

The stacks' duration, the discharge's 6 sec, the potencies and the share are proposals waiting for the designer
(STAGE-ZG-HM report). None of the looks were checked in game.
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
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_SRC_CASTER = 22

_ATTR0_PASSIVE = 0x00000040
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000

_DMG_CLASS_MAGIC = 1

# spell_proc (SpellMgr.h)
_PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK = 0x00000008
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS = 0x00000020
_PROC_FLAG_TAKEN_RANGED_AUTO_ATTACK = 0x00000080
_PROC_FLAG_TAKEN_SPELL_RANGED_DMG_CLASS = 0x00000200
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG = 0x00001000
_PROC_FLAG_TAKEN_SPELL_NONE_DMG_CLASS_NEG = 0x00002000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x00010000
_PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG = 0x00020000
_PROC_FLAG_DONE_PERIODIC = 0x00040000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_TYPE_HEAL = 0x2
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_NORMAL_OR_CRITICAL = 0x1 | 0x2
_PROC_ATTR_TRIGGERED_CAN_PROC = 0x2

_TAKEN_HITS = (_PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK | _PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS
               | _PROC_FLAG_TAKEN_RANGED_AUTO_ATTACK | _PROC_FLAG_TAKEN_SPELL_RANGED_DMG_CLASS
               | _PROC_FLAG_TAKEN_SPELL_NONE_DMG_CLASS_NEG | _PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG)
_HARMFUL_SPELLS = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG
_HEALS = (_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS
          | _PROC_FLAG_DONE_PERIODIC)

# Stock looks and icons, read from Spell.dbc by name (none checked in game yet).
_SV_LIGHTNING_SHIELD = 37       # Static Electricity 3742 (the dungeon doc's Static Charge look)
_SV_THUNDERSTORM = 11302        # Thunderstorm 51490
_SV_CHAIN_LIGHTNING = 36        # Chain Lightning 421 (the dungeon doc's Static Discharge look)
_SV_CALL_PET = 3401             # Call Pet 883 (a whistle)
_SV_GREATER_HEAL = 57           # Greater Heal 2060 (Murta's heal in the dungeon doc)
_ICON_MONSTER_SCALES = 1536     # INV_Misc_MonsterScales_15
_ICON_LIGHTNING_SHIELD = 19     # Spell_Nature_LightningShield
_ICON_CHAIN_LIGHTNING = 165     # Spell_Nature_ChainLightning
_ICON_LIGHTNING_OVERLOAD = 2018  # Spell_Nature_LightningOverload
_ICON_BEAST_CALL = 455          # Ability_Hunter_BeastCall

# An off-GCD payout's time basis (the Deadmines items' precedent).
_PROC_PAYOUT_MS = 1500

_CHARGE_MS = 30000
_DISCHARGE_RADIUS = 8.0
_ARC_RADIUS = 10.0
_WHISTLE_RADIUS = 10.0
_STATIC_STACKS = 10
_FANG_STACKS = 5


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


def _charge_buff(spell_id: int, name: str, stacks: int, icon: int, desc: str, aura_desc: str, notes: str,
                 **more) -> object:
    """A visible stack on the wearer, 30 sec, no effect of its own."""
    return spell(
        id=spell_id, name=name, school=School.NATURE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_CHARGE_MS, effects=[_dummy(1)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=_raw(desc, aura_desc, spell_level=1, CumulativeAura=stacks,
                           AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS, **more),
    )


# =====================================================================================================================
# Hard mode: Gahz'rilla, The Crew at the Pool

# --- Scale of the Storm God (trinket, Equip) -------------------------------------------------------------------------

static_discharge_213802 = spell(
    id=213802, name='Static Discharge', school=School.NATURE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=90.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_SRC_CASTER,
                    implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=_DISCHARGE_RADIUS)],
    spell_icon_id=_ICON_LIGHTNING_OVERLOAD,
    notes='Zul\'Farrak hard mode, Scale of the Storm God: the discharge, cast by the wearer (triggered) from '
          'spell_zf_scale_of_the_storm_god. Nature, every enemy in combat within 8 yd of the wearer (TARGET_SRC_CASTER '
          '/ TARGET_UNIT_SRC_AREA_ENEMY; spell_zf_static_discharge drops the ones out of combat). Attack power potency '
          '90, T 1.5 s (a Strength trinket). DefenseType MAGIC. SUPPRESS_CASTER_PROCS and NO_REFLECTION: it never '
          'charges the Scale again. Look: stock Thunderstorm SV 11302.',
    raw_overrides=_raw('Deals {pot1} Nature damage to enemies in combat within $a1 yd.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_THUNDERSTORM,
                       AttributesEx=_ATTR1_NO_REFLECTION, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)
scripted_by(static_discharge_213802, 'spell_zf_static_discharge')

static_charge_213801 = _charge_buff(
    213801, 'Static Charge', _STATIC_STACKS, _ICON_LIGHTNING_SHIELD,
    'Charged with static.', 'Static Charge. At full charge, your next melee ability discharges it.',
    'Zul\'Farrak hard mode, Scale of the Storm God: the stacks on the wearer, cast by spell_zf_scale_of_the_storm_god. '
    'Up to 10 (CumulativeAura), 30 s, refreshed by each hit. No effect of its own. Look: stock Static Electricity '
    'SV 37 (the dungeon doc\'s Static Charge).',
    SpellVisualID_1=_SV_LIGHTNING_SHIELD,
)

scale_of_the_storm_god_213800 = _equip_aura(
    213800, 'Scale of the Storm God', School.NATURE,
    [_dummy(_STATIC_STACKS), _dummy(6)],
    'Each hit that damages you builds Static Charge. At $s1 stacks, your next melee ability discharges them, dealing '
    + pot_text(static_discharge_213802) + ' Nature damage to enemies in combat within $213802a1 yd. $s2 sec cooldown.',
    _ICON_MONSTER_SCALES,
    'Zul\'Farrak hard mode, Scale of the Storm God (Gahz\'rilla, The Crew at the Pool, trinket), the Equip: a passive '
    'aura with a proc. Effect 1 DUMMY amount 10 (BasePoints 9 + DieSides 1) = the stacks a discharge needs, effect 2 '
    'DUMMY amount 6 = the seconds between two discharges (the area payout\'s throttle; stacks build meanwhile). '
    'spell_proc: taken melee, ranged, magic and none class hits (0x222A8, no periodic tick) and done melee-class '
    'abilities (0x10, no auto attack), damage type, hit phase, normal or critical, 100%, no internal cooldown (the '
    'script keeps the discharge\'s), TRIGGERED_CAN_PROC (many boss hits are triggered casts; the script refuses a '
    'triggered ability of the wearer). spell_zf_scale_of_the_storm_god.',
    proc_type_mask=_TAKEN_HITS | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS, proc_chance=100,
)
procs_on(scale_of_the_storm_god_213800, proc_flags=_TAKEN_HITS | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS,
         spell_type_mask=_PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=_PROC_SPELL_PHASE_HIT,
         hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, attributes_mask=_PROC_ATTR_TRIGGERED_CAN_PROC, chance=100.0)
scripted_by(scale_of_the_storm_god_213800, 'spell_zf_scale_of_the_storm_god')

# --- Stormcharged Fang (dagger, Equip) -------------------------------------------------------------------------------

storm_arc_213805 = spell(
    id=213805, name='Storm Arc', school=School.NATURE, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=150.0, potency_kind='direct',
                    time_basis_ms=_PROC_PAYOUT_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_CHAIN_LIGHTNING,
    notes='Zul\'Farrak hard mode, Stormcharged Fang: one arc, cast by the wearer (triggered) from '
          'spell_zf_stormcharged_fang on each of the two enemies in combat nearest the spell\'s target. Nature, spell '
          'power potency 150, T 1.5 s (an off-GCD payout). DefenseType MAGIC. IGNORE_LINE_OF_SIGHT: the script checks '
          'the line from the spell\'s target instead (it arcs from there). SUPPRESS_CASTER_PROCS and NO_REFLECTION: an '
          'arc never charges the Fang. Look: stock Chain Lightning SV 36.',
    raw_overrides=_raw('Deals {pot1} Nature damage.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       SpellVisualID_1=_SV_CHAIN_LIGHTNING, AttributesEx=_ATTR1_NO_REFLECTION,
                       AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

stormcharged_213804 = _charge_buff(
    213804, 'Stormcharged', _FANG_STACKS, _ICON_CHAIN_LIGHTNING,
    'Charged with lightning.', 'Stormcharged. At full charge, your next damaging spell arcs to nearby enemies.',
    'Zul\'Farrak hard mode, Stormcharged Fang: the charges on the wearer, cast by spell_zf_stormcharged_fang. Up to 5 '
    '(CumulativeAura), 30 s, refreshed by each critical hit. No effect and no look of its own.',
)

stormcharged_fang_213803 = _equip_aura(
    213803, 'Stormcharged Fang', School.NATURE,
    [_dummy(_FANG_STACKS, radius_yards=_ARC_RADIUS), _dummy(2)],
    'Your critical hits with damaging spells charge the Fang, up to $s1 charges. At $s1, your next damaging spell also '
    'arcs to $s2 more enemies in combat within $a1 yd of its target, dealing ' + pot_text(storm_arc_213805)
    + ' Nature damage to each.',
    _ICON_LIGHTNING_OVERLOAD,
    'Zul\'Farrak hard mode, Stormcharged Fang (Gahz\'rilla, The Crew at the Pool, dagger), the Equip: a passive aura '
    'with a proc. Effect 1 DUMMY amount 5 (BasePoints 4 + DieSides 1) = the charges an arc needs, radius 10 yd = how '
    'far from the spell\'s target it arcs; effect 2 DUMMY amount 2 = the enemies it arcs to. spell_proc: done harmful '
    'magic and none class spells (0x11000, no periodic tick), damage type, hit phase, normal or critical, 100%, no '
    'internal cooldown (the charges throttle it). spell_zf_stormcharged_fang acts once per cast: a critical hit gives '
    'one charge; at 5 a hit with other enemies in combat around its target takes the charges and arcs (no such enemy: '
    'the charges are kept). An area cast is one charge whatever it hits, and the cast that gives the fifth charge does '
    'not arc.',
    proc_type_mask=_HARMFUL_SPELLS, proc_chance=100,
)
procs_on(stormcharged_fang_213803, proc_flags=_HARMFUL_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=100.0)
scripted_by(stormcharged_fang_213803, 'spell_zf_stormcharged_fang')

# --- Sergeant's Whistle (trinket, Use) -------------------------------------------------------------------------------

the_crews_aid_213807 = spell(
    id=213807, name="The Crew's Aid", school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded='a share of the heal it copies, set by spell_zf_sergeants_whistle (custom base '
                                     'points)')],
    spell_icon_id=_ICON_BEAST_CALL,
    notes='Zul\'Farrak hard mode, Sergeant\'s Whistle: the copied heal, cast by the healer (triggered) from '
          'spell_zf_sergeants_whistle with its amount set to the Whistle aura\'s share of the heal. No potency: a '
          'share of a heal that already had the healer\'s bonuses and crit (the first target\'s healing taken undone, '
          'its own target\'s applied), so one spell for every tier. DefenseType '
          '0, CANT_CRIT and IGNORE_CASTER_MODIFIERS (the Spirit Chain 206834 precedent). IGNORE_LINE_OF_SIGHT: the '
          'script checks the line from the healed target instead. SUPPRESS_CASTER_PROCS: a copy never copies again. '
          'Look: stock Greater Heal SV 57 (Murta\'s heal).',
    raw_overrides=_raw('Heals the target.', spell_level=1, SpellVisualID_1=_SV_GREATER_HEAL,
                       AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_IGNORE_CASTER_MODIFIERS),
)

sergeants_whistle_213806 = spell(
    id=213806, name="Sergeant's Whistle", school=School.HOLY, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=12000,
    effects=[_dummy(40, radius_yards=_WHISTLE_RADIUS, scale_amount=True), _dummy(2)],
    spell_icon_id=_ICON_BEAST_CALL,
    notes='Zul\'Farrak hard mode, Sergeant\'s Whistle (Gahz\'rilla, The Crew at the Pool, trinket), the Use: 2 min '
          'cooldown, off the GCD, 12 s on the wearer. Effect 1 DUMMY amount 40 (BasePoints 39 + DieSides 1) = the '
          'share of the heal in percent, growing with the tier (scale_amount), radius 10 yd = how far from the healed '
          'target it looks; effect 2 DUMMY amount 2 = the allies it heals. spell_proc: done positive magic and none '
          'class spells and periodic ticks (0x44400), heal type, hit phase, normal or critical, 100%. '
          'spell_zf_sergeants_whistle casts 213807 on the two injured group members lowest on health within 10 yd of '
          'the healed target (the wearer included, never the target, never a pet) and shows the crew 301000-301004 '
          'around the wearer while it lasts. Area and chain heals (by data or by script: Bloom, Empowered Penance, '
          'Glyph of Prayer of Healing), item heals and heals that are themselves a copy of another heal '
          '(IGNORE_CASTER_MODIFIERS, e.g. Beacon of Light) are not copied. The share is of the heal before the healed '
          'target\'s healing taken modifiers; the copy takes its own target\'s. A positive aura on the caster, '
          'so the bots\' "use trinket" action takes it. SUPPRESS_CASTER_PROCS. Look: stock Call Pet SV 3401 (the '
          'whistle).',
    raw_overrides=_raw(
        'Call the crew for $d: your single target heals also heal the $s2 allies lowest on health within $a1 yd of the '
        'target for $s1% of the amount.',
        'The crew is here. Your single target heals also heal nearby allies.',
        SpellVisualID_1=_SV_CALL_PET, StartRecoveryCategory=0, StartRecoveryTime=0,
        ProcTypeMask=_HEALS, ProcChance=100, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)
procs_on(sergeants_whistle_213806, proc_flags=_HEALS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=100.0)
scripted_by(sergeants_whistle_213806, 'spell_zf_sergeants_whistle')
