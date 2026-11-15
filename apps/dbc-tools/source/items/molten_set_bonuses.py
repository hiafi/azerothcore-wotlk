"""
The Molten set bonuses (docs/dungeons/dungeon-loot-vanilla.md "Molten set bonuses (approved 2026-11-06)"): a 3 piece
and a 5 piece bonus per archetype set, 20 bonus spells, the ten Heat buffs and their payouts. Molten is the opposite
of Haunted's chance: heat builds with every action and erupts on a count.

**Heat, the family rule** (revision 2): Heat is a stacking buff on you, 30 sec, each gain refreshing it, gone when you
leave combat (AuraInterruptFlags LEAVE_COMBAT); its own tooltip is number-free. A critical strike or critical heal
gives 2 Heat instead of 1 in every set (Darkmantle: 1 per combo point spent, 1 more on a crit). The action that
reaches the count erupts with it and Heat resets to 0 (the overflow is lost). Heat is a count, not a chance: every
Heat proc row is 100% and the script never rolls, so Proc Chance never touches it. Every 3 piece tooltip says what
grants Heat, how much, what happens at the count, and how long Heat lasts. One Heat buff per set, so two Molten sets
worn together (a 5 + 3 of two Molten archetypes) keep two counts.

**One gain per cast.** A cast grants its Heat once, at its hit (the crit is only known there): the hit on the cast's
own target, or the first hit of a cast with none (the Death Knight rework's once-per-cast guard shape). An area spell
is one cast; periodic ticks are their own events (only Stoked Flame counts them, and only their crits).

**Cooldown hooks** (Flare-up, Thunderhead, Stoke the Forge, Banked Coals): "a spell or ability with a cooldown of 30
sec or more" is the Cooldown Haste rule's list (docs/Systems.md section 4): an unmodified base RecoveryTime or
CategoryRecoveryTime of 30 sec or more, plus the allow list, minus the deny list (mirrored from Player.cpp in
MoltenSetLogic.h; lib/test_molten_set.py checks they agree). Item casts never count (trinkets, potions: the rule
skips item cooldowns). Cast phase, one per cast.

Damage and healing are potency (docs/potency-system.md; "everything on potency"), off-GCD payouts (time basis 1.5 s;
ticks their own 2 s). Payouts suppress caster procs (SPELL_ATTR3_SUPPRESS_CASTER_PROCS), which gates only the cast's
own hit (Spell.cpp): the periodic payouts' ticks (Molten Edge, Burning Shards, Hallowed Flame) still raise periodic
procs, class talents and other sets included. No payout builds Heat or erupts again because spell_molten_heat and
spell_molten_cooldown_heat skip every id of the molten_set slice (kSpellsMoltenSet), and Haunting Mark skips it too.
Heat builds only while the wearer is in combat (both scripts check; the buff's LEAVE_COMBAT only fires on leaving).
Area payouts reach only enemies already in combat (and the eruption's own target), and an eruption's fallback enemy
(the wearer's victim or selection) must be in combat: a bonus never pulls a pack. Values are starting points [tune]:
a 3 piece eruption is sized like a Haunted 3 piece proc (about 100 potency every 10 to 15 sec); the dps and heal sims
measure each one before the build is final. No look was checked in game.

Ids: the `molten_set` reservation 206900-206999 (source/ids.yaml), ten per set in this order: +0 the 3 piece, +1 the 5
piece, +2 the Heat buff, +3 and up the payouts. Scripts: modules/mod-dungeon-bosses/src/DungeonSets/
molten_set_bonuses.cpp (ids and script numbers mirrored in MoltenSetLogic.h).

  Cloth Intellect, Sorcerer's (517)                         Heat 10
  206900  Stoked Flame (3)     direct damage spell 1 (crit 2), periodic damage crit 1; at 10 the target erupts.
  206901  Flare-up (5)         a spell with a 30 sec+ cooldown erupts your Heat at once, at full strength.
  206902  Heat
  206903  Stoked Flame         Fire, spell power potency 100, the target and every enemy within 8 yd.
  Cloth Spirit, Virtuous (514)                              Heat 8
  206910  Cauterize (3)        direct heal 1 (crit 2); at 8 the heal cauterizes its target and up to 3 allies within
                               10 yd of it.
  206911  Mending Flame (5)    marker: Cauterize heals allies below 50% health for 50% more (spell_molten_cauterize).
  206912  Heat
  206913  Cauterize            Fire heal, spell power potency 30 per ally.
  Leather Spirit, Feralheart (513)                          Heat 8
  206920  Ember Bloom (3)      a damage or healing spell 1 (crit 2); at 8 your next periodic spell blooms (206923).
  206921  Fanned Embers (5)    marker: a bloom also gives 206924.
  206922  Heat
  206923  Ember Bloom          the ready buff (30 s, out of combat clears): your next periodic damage or healing spell
                               instantly deals or heals two of its ticks (AuraEffect::PeriodicTick, the real tick:
                               spell power, crit and procs as usual). One charge.
  206924  Fanned Embers        your next direct damage or healing spell within 10 sec is 30% stronger. One charge.
  Mail Intellect, The Five Thunders (519)                   Heat 10
  206930  Molten Thunder (3)   a damage or healing spell 1 (crit 2); at 10 molten thunder strikes the spell's target:
                               Fire damage to it and enemies within 8 yd, or healing it and up to 4 allies within 8 yd.
  206931  Thunderhead (5)      a spell with a 30 sec+ cooldown grants 5 Heat.
  206932  Heat
  206933  Molten Thunder       Fire, spell power potency 100, the target and every enemy within 8 yd.
  206934  Molten Thunder       Fire heal, spell power potency 40 per ally.
  Plate Intellect, Soulforge (516)                          Heat 8
  206940  Hallowed Flame (3)   a Holy spell or ability 1 (crit 2); at 8 it sets its target alight for 6 sec.
  206941  Tended Flame (5)     marker: each Hallowed Flame tick restores 1% of your maximum mana (206945).
  206942  Heat
  206943  Hallowed Flame       Holy heal over time on an ally, spell power potency 20 a tick, every 2 s for 6 s.
  206944  Hallowed Flame       Holy damage over time on an enemy, spell power potency 20 a tick, every 2 s for 6 s.
  206945  Tended Flame         1% of maximum mana (ENERGIZE_PCT).
  Plate Strength, Heroism (511)                             Heat 10
  206950  Molten Edge (3)      a melee or ranged ability 1 (crit 2); at 10 the ability sears its target.
  206951  Stoke the Forge (5)  an ability with a 30 sec+ cooldown grants 10 Heat (an eruption).
  206952  Heat
  206953  Molten Edge          Fire damage over time, attack power potency 25 a tick, every 2 s for 6 s.
  Mail Agility, Beastmaster's (515)                         Heat 8
  206960  Obsidian Shard (3)   a melee or ranged ability 1 (crit 2); at 8 a shard hits the target and bounces to 1
                               more enemy within 10 yd.
  206961  Burning Shards (5)   marker: shards leave their targets burning (206965 / 206966).
  206962  Heat
  206963  Obsidian Shard       Physical, attack power potency 70 (after a melee ability).
  206964  Obsidian Shard       the same off ranged attack power (after a ranged ability).
  206965  Burning Shards       Fire damage over time, attack power potency 10 a tick, every 2 s for 6 s (melee).
  206966  Burning Shards       the same off ranged attack power.
  Leather Agility, Darkmantle (512)                         Heat 10
  206970  Slag Burst (3)       a finishing move 1 per combo point spent, 1 more on a crit; at 10 it erupts.
  206971  Rekindle (5)         marker: an eruption gives 206974.
  206972  Heat
  206973  Slag Burst           Fire, attack power potency 100, the target and every enemy within 5 yd.
  206974  Rekindle             your next combo point generator grants 1 extra combo point (20 s). One charge.
  Leather Tank, Guardian's (1002)                           Heat 10
  206980  Scorching Hide (3)   a melee or ranged ability 1 (crit 2); at 10 you erupt.
  206981  Tempered Hide (5)    marker: an eruption gives 206984.
  206982  Heat
  206983  Scorching Hide       Fire, attack power potency 80, every enemy within 8 yd of you; threat x3 (spell_threat).
  206984  Tempered Hide        damage taken -5%, 6 s.
  Plate Tank, Impenetrable (1003)                           Heat 10
  206990  Molten Plate (3)     a melee or ranged ability 1 (crit 2); at 10 your armor rises (206993).
  206991  Banked Coals (5)     an ability with a 30 sec+ cooldown grants 10 Heat (an eruption).
  206992  Heat
  206993  Molten Plate         armor +10%, 8 s.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import pot_text, procs_on, scripted_by, spell, spell_threat

_TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}

_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_SRC_CASTER = 22
_TARGET_DEST_TARGET_ENEMY = 53

_ATTR0_PASSIVE = 0x00000040
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_AURA_INTERRUPT_LEAVE_COMBAT = 0x80000000

_DMG_CLASS_NONE = 0
_DMG_CLASS_MAGIC = 1
_DMG_CLASS_MELEE = 2
_DMG_CLASS_RANGED = 3
_RANGED_WEAPON_SUBCLASS_MASK = (1 << 2) | (1 << 3) | (1 << 18) | (1 << 16)  # bow, gun, crossbow, thrown
_ALL_SCHOOLS = 127
_ARMOR = 1  # SPELL_AURA_MOD_RESISTANCE_PCT misc: the Physical school mask, armor
_POWER_MANA = 0

# spell_proc (SpellMgr.h)
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS = 0x00000100
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG = 0x00001000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x00010000
_PROC_FLAG_DONE_PERIODIC = 0x00040000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_TYPE_HEAL = 0x2
_PROC_SPELL_TYPE_ALL = 0x7  # damage, heal, and neither (an aura cast: a HoT, Rupture, Slice and Dice)
_PROC_SPELL_PHASE_CAST = 0x1
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_NORMAL = 0x1
_PROC_HIT_CRITICAL = 0x2

_SPELLS = (_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS
           | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS)
_MELEE = _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS
_ABILITIES = _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS | _PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
_EVERY_CAST = _SPELLS | _ABILITIES
# Every finishing move: melee and ranged class (Eviscerate, Rip, Deadly Throw) and class NONE (Slice and Dice, Savage
# Roar).
_FINISHERS = _ABILITIES | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG
_HIT_OR_CRIT = _PROC_HIT_NORMAL | _PROC_HIT_CRITICAL

_OFF_GCD_MS = 1500  # potency time basis of a proc payout
_HEAT_DURATION_MS = 30000

# Stock looks (stock Spell.dbc, read 2026-11-14; none checked in game).
_ICON_HOT_STREAK = 2999
_SV_FLAMESTRIKE, _ICON_FLAMESTRIKE = 10383, 37
_ICON_COMBUSTION = 33
_SV_FLASH_HEAL, _ICON_HOLY_FIRE = 3077, 156
_ICON_FLASH_HEAL = 242
_ICON_WILD_GROWTH = 2864
_ICON_STARFIRE = 1485
_SV_LAVA_BURST, _ICON_LAVA_BURST = 11565, 3064
_SV_HEALING_WAVE = 58
_ICON_HEROISM = 2288
_SV_HOLY_FIRE = 3400
_SV_RENEW = 0
_ICON_POWER_INFUSION = 1872
_ICON_LAVA_LASH = 3741
_SV_IMMOLATE, _ICON_IMMOLATE = 46, 31
_ICON_BLOOD_FURY = 1662
_SV_DEADLY_THROW, _ICON_DEADLY_THROW = 7929, 2097
_SV_LIVING_BOMB, _ICON_CONFLAGRATE = 10692, 12
_ICON_ADRENALINE_RUSH = 235
_SV_HELLFIRE, _ICON_FIRE_SHIELD = 5423, 16
_ICON_SHIELD_WALL = 281
_ICON_MOLTEN_ARMOR = 2307
_ICON_BLOODRAGE = 86

# Heat counts and script numbers shown in tooltips (mirrored in MoltenSetLogic.h; lib/test_molten_set.py checks they
# match).
STOKED_FLAME_HEAT = 10
CAUTERIZE_HEAT = 8
EMBER_BLOOM_HEAT = 8
MOLTEN_THUNDER_HEAT = 10
HALLOWED_FLAME_HEAT = 8
MOLTEN_EDGE_HEAT = 10
OBSIDIAN_SHARD_HEAT = 8
SLAG_BURST_HEAT = 10
SCORCHING_HIDE_HEAT = 10
MOLTEN_PLATE_HEAT = 10
CRIT_HEAT = 2
COOLDOWN_HOOK_MIN_S = 30
CAUTERIZE_EXTRA_ALLIES = 3
CAUTERIZE_RADIUS = 10
MENDING_FLAME_HEALTH_PCT = 50
MENDING_FLAME_BONUS_PCT = 50
EMBER_BLOOM_TICKS = 2
MOLTEN_THUNDER_RADIUS = 8
MOLTEN_THUNDER_EXTRA_ALLIES = 4
THUNDERHEAD_HEAT = 5
STOKE_THE_FORGE_HEAT = 10
BANKED_COALS_HEAT = 10
OBSIDIAN_SHARD_BOUNCE_RADIUS = 10
REKINDLE_COMBO_POINTS = 1

_HEAT_LASTS = ' Heat lasts 30 sec, refreshed by each gain, and fades when you leave combat.'


def _raw(desc: str = '', aura_desc: str = '', spell_level: int = 0, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': spell_level, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_TEXT_MASKS, **more}


def _bonus(spell_id: int, name: str, desc: str, icon: int, notes: str, *, proc_type_mask: int = 0) -> object:
    """A set bonus: the passive aura ItemSet.dbc names (applied by AddItemsSetItem, so no item). A DUMMY: every
    Molten bonus is a script or a marker read by one. Its description is the "(N) Set:" line."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_PASSIVE, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
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


def _self_buff(spell_id: int, name: str, school: int, effects: list, icon: int, notes: str, *, desc: str,
               aura_desc: str, duration_ms: int, **more) -> object:
    """A visible buff on the wearer (not passive, so the client shows it), gone when the wearer leaves combat."""
    return _payout(spell_id, name, school, effects, icon, notes, desc=desc, aura_desc=aura_desc,
                   duration_ms=duration_ms, range_yards=RANGE_SELF, defense=_DMG_CLASS_NONE, spell_level=0,
                   AuraInterruptFlags=_AURA_INTERRUPT_LEAVE_COMBAT, **more)


def _heat(spell_id: int, set_name: str, count: int) -> object:
    """The set's Heat: a DUMMY whose stack count is the Heat (CumulativeAura = the count; the script erupts and
    removes it on reaching the count, so a held stack is at most count - 1). 30 s, each gain refreshing it; leaving
    combat removes it. Number-free tooltip (designer)."""
    return _self_buff(
        spell_id, 'Heat', School.FIRE,
        [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER)],
        _ICON_HOT_STREAK,
        f'Molten set, {set_name}: the Heat count. A DUMMY whose stacks are the Heat (CumulativeAura {count}); '
        'MoltenSet::AddHeat sets the stacks and refreshes the 30 s, and removes it at the eruption. '
        'AuraInterruptFlags LEAVE_COMBAT: out of combat it is gone. Number-free tooltip (designer).',
        desc='Heat: building toward an eruption.', aura_desc='Heat: building toward an eruption.',
        duration_ms=_HEAT_DURATION_MS, CumulativeAura=count,
    )


def _direct(kind: str, *, sp: float = 0.0, ap: float = 0.0, target: int = _TARGET_UNIT_TARGET_ENEMY,
            effect: int = EffectType.SCHOOL_DAMAGE, **more) -> Effect:
    return Effect(type=effect, sp_potency=sp, ap_potency=ap, potency_kind=kind, time_basis_ms=_OFF_GCD_MS,
                  implicit_target_a=target, **more)


def _area_at_target(*, sp: float = 0.0, ap: float = 0.0, radius: float) -> Effect:
    """Damage to the target and every enemy within `radius` yards of it (the Bone Shatter shape)."""
    return _direct('direct', sp=sp, ap=ap, target=_TARGET_DEST_TARGET_ENEMY,
                   implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=radius)


def _dot(*, sp: float = 0.0, ap: float = 0.0, target: int = _TARGET_UNIT_TARGET_ENEMY,
         heal: bool = False) -> Effect:
    return Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_HEAL if heal else AuraType.PERIODIC_DAMAGE,
                  amplitude=2000, sp_potency=sp, ap_potency=ap, potency_kind='heal_periodic' if heal else 'periodic',
                  implicit_target_a=target)


def _heat_proc(spell_obj, proc_flags: int) -> None:
    """The 3 piece's Heat row: 100% (a count, never a chance), hit phase (the crit is known there), every spell type
    (an aura cast counts too); spell_molten_heat keeps the set's own events, once per cast."""
    procs_on(spell_obj, proc_flags=proc_flags, spell_type_mask=_PROC_SPELL_TYPE_ALL,
             spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_HIT_OR_CRIT, chance=100.0)
    scripted_by(spell_obj, 'spell_molten_heat')


def _cooldown_proc(spell_obj) -> None:
    """A 5 piece cooldown hook: every cast of the wearer, cast phase (one per cast; a cast phase has no outcome, so no
    hit mask); spell_molten_cooldown_heat keeps the Cooldown Haste rule's spells, item casts excluded."""
    procs_on(spell_obj, proc_flags=_EVERY_CAST, spell_phase_mask=_PROC_SPELL_PHASE_CAST, chance=100.0)
    scripted_by(spell_obj, 'spell_molten_cooldown_heat')


# =====================================================================================================================
# Cloth Intellect: Sorcerer's (517)

stoked_flame_eruption_206903 = _payout(
    206903, 'Stoked Flame', School.FIRE,
    [_area_at_target(sp=100.0, radius=8.0)], _ICON_FLAMESTRIKE,
    'Molten set, Sorcerer\'s 3 piece: the eruption. Fire, spell power potency 100, T 1.5 s, the target and every enemy '
    'within 8 yd of it (uncapped; spell_molten_eruption_in_combat keeps only enemies already in combat, and the '
    'target). Look: stock Flamestrike SV 10383.',
    desc='Deals {pot1} Fire damage to the target and every enemy within $a1 yards of it.', visual=_SV_FLAMESTRIKE,
)
scripted_by(stoked_flame_eruption_206903, 'spell_molten_eruption_in_combat')

stoked_flame_heat_206902 = _heat(206902, 'Sorcerer\'s', STOKED_FLAME_HEAT)

stoked_flame_206900 = _bonus(
    206900, 'Stoked Flame',
    f'Your direct damage spells grant 1 Heat, or {CRIT_HEAT} when they critically strike, and your periodic damage '
    f'critical strikes grant 1 Heat. At {STOKED_FLAME_HEAT} Heat, your target erupts, dealing '
    + pot_text(stoked_flame_eruption_206903) + ' Fire damage to it and all enemies within $206903a1 yards.'
    + _HEAT_LASTS,
    _ICON_FLAMESTRIKE,
    'Molten set, Sorcerer\'s 3 piece (Cloth Intellect). spell_proc: done spells (magic and none, helpful and harmful) '
    'and periodic, hit phase, normal or critical, 100% (Heat is a count). spell_molten_heat: a direct damage spell '
    'gives 1 Heat (2 on a crit), once per cast; a periodic damage tick gives 1 only when it crits. At 10 the event\'s '
    'target erupts (206903).',
    proc_type_mask=_SPELLS | _PROC_FLAG_DONE_PERIODIC,
)
_heat_proc(stoked_flame_206900, _SPELLS | _PROC_FLAG_DONE_PERIODIC)

flare_up_206901 = _bonus(
    206901, 'Flare-up',
    f'Casting a spell with a cooldown of {COOLDOWN_HOOK_MIN_S} sec or more erupts your Stoked Flame Heat at once, at '
    'full strength.',
    _ICON_COMBUSTION,
    'Molten set, Sorcerer\'s 5 piece (Cloth Intellect). spell_proc: every cast, cast phase, 100%. '
    'spell_molten_cooldown_heat: a spell on the Cooldown Haste rule\'s list (base cooldown 30 s or more, the allow '
    'list, not the deny list; no item cast) erupts 206903 at the cast\'s enemy target (else the wearer\'s victim) '
    'whatever the Heat, and resets it. No enemy: nothing happens, the Heat stays.',
    proc_type_mask=_EVERY_CAST,
)
_cooldown_proc(flare_up_206901)

# =====================================================================================================================
# Cloth Spirit: Virtuous (514)

cauterize_heal_206913 = _payout(
    206913, 'Cauterize', School.FIRE,
    [_direct('heal', sp=30.0, effect=EffectType.HEAL, target=_TARGET_UNIT_TARGET_ALLY)], _ICON_HOLY_FIRE,
    'Molten set, Virtuous 3 piece: the cauterizing heal, one cast per ally (the script picks them). Fire heal, spell '
    'power potency 30, T 1.5 s. spell_molten_cauterize: with the 5 piece (Mending Flame 206911) an ally below 50% '
    'health is healed 50% more. Look: stock Flash Heal SV 3077.',
    desc='Heals the target for {pot1}.', visual=_SV_FLASH_HEAL,
)
scripted_by(cauterize_heal_206913, 'spell_molten_cauterize')

cauterize_heat_206912 = _heat(206912, 'Virtuous', CAUTERIZE_HEAT)

cauterize_206910 = _bonus(
    206910, 'Cauterize',
    f'Your direct heals grant 1 Heat, or {CRIT_HEAT} when they critically heal. At {CAUTERIZE_HEAT} Heat, your heal '
    f'also cauterizes the target and up to {CAUTERIZE_EXTRA_ALLIES} allies within {CAUTERIZE_RADIUS} yards, healing '
    'each for ' + pot_text(cauterize_heal_206913) + '.' + _HEAT_LASTS,
    _ICON_HOLY_FIRE,
    'Molten set, Virtuous 3 piece (Cloth Spirit). spell_proc: done spells, hit phase, 100%. spell_molten_heat: a '
    'direct heal gives 1 Heat (2 on a critical heal), once per cast. At 8, 206913 on the healed target and on the 3 '
    'most injured other group members (or the wearer) within 10 yd of it.',
    proc_type_mask=_SPELLS,
)
_heat_proc(cauterize_206910, _SPELLS)

mending_flame_206911 = _bonus(
    206911, 'Mending Flame',
    f'Cauterize heals allies below {MENDING_FLAME_HEALTH_PCT}% health for {MENDING_FLAME_BONUS_PCT}% more.',
    _ICON_FLASH_HEAL,
    'Molten set, Virtuous 5 piece (Cloth Spirit): a marker read by spell_molten_cauterize (the target\'s health '
    'before the heal lands).',
)

# =====================================================================================================================
# Leather Spirit: Feralheart (513)

fanned_embers_buff_206924 = _self_buff(
    206924, 'Fanned Embers', School.FIRE,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=29,
            misc_value=_ALL_SCHOOLS, implicit_target_a=_TARGET_UNIT_CASTER),
     Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=29,
            implicit_target_a=_TARGET_UNIT_CASTER)],
    _ICON_STARFIRE,
    'Molten set, Feralheart 5 piece: damage and healing done +30% (base 29 + die 1), 10 s, one charge: spell_proc '
    'consumes it on the next direct damage or healing spell (done spells, damage or heal type, hit phase; periodic '
    'ticks are not in the flags, so they never consume it). While it is up (rarely past the next cast) a DoT or HoT '
    'tick would also gain the 30%.',
    desc='Your next direct damage or healing spell is $s1% stronger.',
    aura_desc='Your next direct damage or healing spell is stronger.', duration_ms=10000, ProcCharges=1,
)
procs_on(fanned_embers_buff_206924, proc_flags=_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE | _PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_HIT_OR_CRIT, chance=100.0, charges=1)

ember_bloom_ready_206923 = _self_buff(
    206923, 'Ember Bloom', School.FIRE,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER)],
    _ICON_WILD_GROWTH,
    'Molten set, Feralheart 3 piece: the bloom, ready. 30 s, one charge, gone out of combat. spell_proc: done spells, '
    'hit phase, every type (a HoT cast heals nothing at its hit). spell_molten_ember_bloom keeps the wearer\'s own '
    'cast of a spell with a periodic damage or heal effect (not a channel), once per cast; next update it runs two '
    'real ticks of every periodic damage or heal effect that cast left on the target (AuraEffect::PeriodicTick: spell '
    'power, crit and procs as a normal tick), then Fanned Embers 206924 with the 5 piece 206921.',
    desc='Your next periodic damage or healing spell instantly deals or heals two of its ticks.',
    aura_desc='Your next periodic spell blooms.', duration_ms=_HEAT_DURATION_MS, ProcCharges=1,
)
procs_on(ember_bloom_ready_206923, proc_flags=_SPELLS, spell_type_mask=_PROC_SPELL_TYPE_ALL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_HIT_OR_CRIT, chance=100.0, charges=1)
scripted_by(ember_bloom_ready_206923, 'spell_molten_ember_bloom')

ember_bloom_heat_206922 = _heat(206922, 'Feralheart', EMBER_BLOOM_HEAT)

ember_bloom_206920 = _bonus(
    206920, 'Ember Bloom',
    f'Your damage and healing spells grant 1 Heat, or {CRIT_HEAT} when they critically strike or heal. At '
    f'{EMBER_BLOOM_HEAT} Heat, your next periodic spell blooms, instantly dealing or healing {EMBER_BLOOM_TICKS} of '
    'its ticks.' + _HEAT_LASTS,
    _ICON_WILD_GROWTH,
    'Molten set, Feralheart 3 piece (Leather Spirit). spell_proc: done spells, hit phase, 100%. spell_molten_heat: '
    'a spell with a damage or healing effect, direct or periodic, gives 1 Heat (2 on a crit), once per cast (its '
    'ticks are not casts). At 8, the bloom 206923 on the wearer.',
    proc_type_mask=_SPELLS,
)
_heat_proc(ember_bloom_206920, _SPELLS)

fanned_embers_206921 = _bonus(
    206921, 'Fanned Embers',
    'When Ember Bloom blooms, your next direct damage or healing spell within $206924d is $206924s1% stronger.',
    _ICON_STARFIRE,
    'Molten set, Feralheart 5 piece (Leather Spirit): a marker read by spell_molten_ember_bloom (the buff is 206924).',
)

# =====================================================================================================================
# Mail Intellect: The Five Thunders (519)

molten_thunder_damage_206933 = _payout(
    206933, 'Molten Thunder', School.FIRE,
    [_area_at_target(sp=100.0, radius=float(MOLTEN_THUNDER_RADIUS))], _ICON_LAVA_BURST,
    'Molten set, The Five Thunders 3 piece: the strike on an enemy. Fire, spell power potency 100, T 1.5 s, the '
    'target and every enemy within 8 yd of it (spell_molten_eruption_in_combat: only enemies already in combat, and '
    'the target). Look: stock Lava Burst SV 11565.',
    desc='Deals {pot1} Fire damage to the target and every enemy within $a1 yards of it.', visual=_SV_LAVA_BURST,
)
scripted_by(molten_thunder_damage_206933, 'spell_molten_eruption_in_combat')

molten_thunder_heal_206934 = _payout(
    206934, 'Molten Thunder', School.FIRE,
    [_direct('heal', sp=40.0, effect=EffectType.HEAL, target=_TARGET_UNIT_TARGET_ALLY)], _ICON_LAVA_BURST,
    'Molten set, The Five Thunders 3 piece: the strike on an ally, one cast per ally (the script picks the target and '
    'up to 4 other group members within 8 yd of it, most injured first). Fire heal, spell power potency 40, T 1.5 s. '
    'Look: stock Healing Wave SV 58.',
    desc='Heals the target for {pot1}.', visual=_SV_HEALING_WAVE,
)

molten_thunder_heat_206932 = _heat(206932, 'The Five Thunders', MOLTEN_THUNDER_HEAT)

molten_thunder_206930 = _bonus(
    206930, 'Molten Thunder',
    f'Your damage and healing spells grant 1 Heat, or {CRIT_HEAT} when they critically strike or heal. At '
    f'{MOLTEN_THUNDER_HEAT} Heat, molten thunder strikes your target, dealing '
    + pot_text(molten_thunder_damage_206933) + ' Fire damage to it and all enemies within $206933a1 yards, or '
    'healing it and up to ' + f'{MOLTEN_THUNDER_EXTRA_ALLIES} allies within {MOLTEN_THUNDER_RADIUS} yards for '
    + pot_text(molten_thunder_heal_206934) + ' each.' + _HEAT_LASTS,
    _ICON_LAVA_BURST,
    'Molten set, The Five Thunders 3 piece (Mail Intellect). spell_proc: done spells, hit phase, 100%. '
    'spell_molten_heat: a spell with a damage or healing effect gives 1 Heat (2 on a crit), once per cast. At 10, '
    '206933 at an enemy target, or 206934 on an ally target and up to 4 group members within 8 yd of it.',
    proc_type_mask=_SPELLS,
)
_heat_proc(molten_thunder_206930, _SPELLS)

thunderhead_206931 = _bonus(
    206931, 'Thunderhead',
    f'Casting a spell with a cooldown of {COOLDOWN_HOOK_MIN_S} sec or more grants {THUNDERHEAD_HEAT} Molten Thunder '
    'Heat.',
    _ICON_HEROISM,
    'Molten set, The Five Thunders 5 piece (Mail Intellect). spell_proc: every cast, cast phase, 100%. '
    'spell_molten_cooldown_heat: a spell on the Cooldown Haste rule\'s list (no item cast) adds 5 Heat; reaching 10 '
    'strikes the cast\'s target (an enemy: damage; an ally or none: healing on the wearer\'s target or the wearer).',
    proc_type_mask=_EVERY_CAST,
)
_cooldown_proc(thunderhead_206931)

# =====================================================================================================================
# Plate Intellect: Soulforge (516)

tended_flame_mana_206945 = _payout(
    206945, 'Tended Flame', School.HOLY,
    [Effect(type=EffectType.ENERGIZE_PCT, base_points=0, misc_value=_POWER_MANA,
            implicit_target_a=_TARGET_UNIT_CASTER)],
    _ICON_POWER_INFUSION,
    'Molten set, Soulforge 5 piece: 1% of maximum mana (ENERGIZE_PCT, base 0 + die 1), cast on the wearer by '
    'spell_molten_hallowed_flame at each Hallowed Flame tick.',
    desc='Restores $s1% of your maximum mana.', range_yards=RANGE_SELF, defense=_DMG_CLASS_NONE, spell_level=0,
)

hallowed_flame_hot_206943 = _payout(
    206943, 'Hallowed Flame', School.HOLY,
    [_dot(sp=20.0, target=_TARGET_UNIT_TARGET_ALLY, heal=True)], _ICON_HOLY_FIRE,
    'Molten set, Soulforge 3 piece: the flame on an ally. Holy heal every 2 s for 6 s, spell power potency 20 a tick '
    '(time basis the tick). spell_molten_hallowed_flame: each tick restores the caster 1% mana with the 5 piece.',
    desc='Heals the target for {pot1} every $t1 sec for $d.', aura_desc='Healing over time.', duration_ms=6000,
)
hallowed_flame_dot_206944 = _payout(
    206944, 'Hallowed Flame', School.HOLY,
    [_dot(sp=20.0)], _ICON_HOLY_FIRE,
    'Molten set, Soulforge 3 piece: the flame on an enemy. Holy damage every 2 s for 6 s, spell power potency 20 a '
    'tick. spell_molten_hallowed_flame: each tick restores the caster 1% mana with the 5 piece. Look: stock Holy Fire '
    'SV 3400.',
    desc='Deals {pot1} Holy damage every $t1 sec for $d.', aura_desc='Burning.', duration_ms=6000,
    attributes=_ATTR0_AURA_IS_DEBUFF, visual=_SV_HOLY_FIRE,
)
scripted_by(hallowed_flame_hot_206943, 'spell_molten_hallowed_flame')
scripted_by(hallowed_flame_dot_206944, 'spell_molten_hallowed_flame')

hallowed_flame_heat_206942 = _heat(206942, 'Soulforge', HALLOWED_FLAME_HEAT)

hallowed_flame_206940 = _bonus(
    206940, 'Hallowed Flame',
    f'Your Holy spells grant 1 Heat, or {CRIT_HEAT} when they critically strike or heal. At {HALLOWED_FLAME_HEAT} '
    'Heat, your spell also sets its target alight for $206943d: healing an ally for '
    + pot_text(hallowed_flame_hot_206943, variant='total') + ' over the time, or burning an enemy for '
    + pot_text(hallowed_flame_dot_206944, variant='total') + ' Holy damage.' + _HEAT_LASTS,
    _ICON_HOLY_FIRE,
    'Molten set, Soulforge 3 piece (Plate Intellect). spell_proc: done spells and melee and ranged abilities '
    '(Judgement and Avenger\'s Shield are ranged class), hit phase, 100%. '
    'spell_molten_heat: a spell or ability with the Holy school gives 1 Heat (2 on a crit), once per cast. At 8, '
    '206943 on an ally target (the wearer when the cast had none) or 206944 on an enemy target.',
    proc_type_mask=_SPELLS | _ABILITIES,
)
_heat_proc(hallowed_flame_206940, _SPELLS | _ABILITIES)

tended_flame_206941 = _bonus(
    206941, 'Tended Flame',
    'Each tick of Hallowed Flame restores $206945s1% of your maximum mana.',
    _ICON_POWER_INFUSION,
    'Molten set, Soulforge 5 piece (Plate Intellect): a marker read by spell_molten_hallowed_flame (the mana is '
    '206945).',
)

# =====================================================================================================================
# Plate Strength: Heroism (511)

molten_edge_sear_206953 = _payout(
    206953, 'Molten Edge', School.FIRE,
    [_dot(ap=25.0)], _ICON_LAVA_LASH,
    'Molten set, Heroism 3 piece: the sear. Fire damage every 2 s for 6 s, attack power potency 25 a tick (about 100 '
    'potency in all), DefenseType MAGIC (the Haunted AP payouts\' shape). A second sear refreshes it. Look: stock '
    'Immolate SV 46.',
    desc='Deals {pot1} Fire damage every $t1 sec for $d.', aura_desc='Seared.', duration_ms=6000,
    attributes=_ATTR0_AURA_IS_DEBUFF, visual=_SV_IMMOLATE,
)

molten_edge_heat_206952 = _heat(206952, 'Heroism', MOLTEN_EDGE_HEAT)

molten_edge_206950 = _bonus(
    206950, 'Molten Edge',
    f'Your melee and ranged abilities grant 1 Heat, or {CRIT_HEAT} when they critically strike. At {MOLTEN_EDGE_HEAT} '
    'Heat, '
    'your ability sears the target, burning it for ' + pot_text(molten_edge_sear_206953, variant='total')
    + ' Fire damage over $206953d.' + _HEAT_LASTS,
    _ICON_LAVA_LASH,
    'Molten set, Heroism 3 piece (Plate Strength). spell_proc: done melee and ranged abilities (Thunder Clap, '
    'Avenger\'s Shield, Judgement are ranged class; never an auto attack), hit phase, 100%. '
    'spell_molten_heat: a melee- or ranged-class spell gives 1 Heat (2 on a crit), once per cast. At 10, 206953 on '
    'the target.',
    proc_type_mask=_ABILITIES,
)
_heat_proc(molten_edge_206950, _ABILITIES)

stoke_the_forge_206951 = _bonus(
    206951, 'Stoke the Forge',
    f'Using an ability with a cooldown of {COOLDOWN_HOOK_MIN_S} sec or more grants {STOKE_THE_FORGE_HEAT} Molten Edge '
    'Heat.',
    _ICON_BLOOD_FURY,
    'Molten set, Heroism 5 piece (Plate Strength). spell_proc: every cast, cast phase, 100%. '
    'spell_molten_cooldown_heat: a spell on the Cooldown Haste rule\'s list (no item cast) adds 10 Heat, so it erupts: '
    'the sear on the cast\'s enemy target, else the wearer\'s victim (none: the Heat is spent for nothing).',
    proc_type_mask=_EVERY_CAST,
)
_cooldown_proc(stoke_the_forge_206951)

# =====================================================================================================================
# Mail Agility: Beastmaster's (515)

burning_shards_melee_206965 = _payout(
    206965, 'Burning Shards', School.FIRE,
    [_dot(ap=10.0)], _ICON_IMMOLATE,
    'Molten set, Beastmaster\'s 5 piece: the burn a shard leaves, after a melee shard. Fire damage every 2 s for 6 s, '
    'attack power potency 10 a tick. Look: stock Immolate SV 46.',
    desc='Deals {pot1} Fire damage every $t1 sec for $d.', aura_desc='Burning.', duration_ms=6000,
    attributes=_ATTR0_AURA_IS_DEBUFF, visual=_SV_IMMOLATE,
)
burning_shards_ranged_206966 = _payout(
    206966, 'Burning Shards', School.FIRE,
    [_dot(ap=10.0)], _ICON_IMMOLATE,
    'Molten set, Beastmaster\'s 5 piece: the burn after a ranged shard, off ranged attack power (DefenseType RANGED '
    'and the ranged weapon subclass mask; EquippedItemClass -1 keeps the cast free of a weapon requirement).',
    desc='Deals {pot1} Fire damage every $t1 sec for $d.', aura_desc='Burning.', duration_ms=6000,
    attributes=_ATTR0_AURA_IS_DEBUFF, visual=_SV_IMMOLATE, defense=_DMG_CLASS_RANGED,
    EquippedItemSubclass=_RANGED_WEAPON_SUBCLASS_MASK,
)

obsidian_shard_melee_206963 = _payout(
    206963, 'Obsidian Shard', School.NORMAL,
    [_direct('direct', ap=70.0)], _ICON_DEADLY_THROW,
    'Molten set, Beastmaster\'s 3 piece: the shard, after a melee ability. Physical, attack power potency 70, T 1.5 '
    's, DefenseType MELEE, NO_ACTIVE_DEFENSE. spell_molten_obsidian_shard leaves 206965 with the 5 piece. Look: stock '
    'Deadly Throw SV 7929.',
    desc='Deals {pot1} Physical damage.', attributes=_ATTR0_NO_ACTIVE_DEFENSE, visual=_SV_DEADLY_THROW,
    defense=_DMG_CLASS_MELEE,
)
obsidian_shard_ranged_206964 = _payout(
    206964, 'Obsidian Shard', School.NORMAL,
    [_direct('direct', ap=70.0)], _ICON_DEADLY_THROW,
    'Molten set, Beastmaster\'s 3 piece: the shard after a ranged ability, off ranged attack power (DefenseType '
    'RANGED and the ranged weapon subclass mask, the Haunted Grasp of the Dead shape). spell_molten_obsidian_shard '
    'leaves 206966 with the 5 piece.',
    desc='Deals {pot1} Physical damage.', attributes=_ATTR0_NO_ACTIVE_DEFENSE, visual=_SV_DEADLY_THROW,
    defense=_DMG_CLASS_RANGED, EquippedItemSubclass=_RANGED_WEAPON_SUBCLASS_MASK,
)
scripted_by(obsidian_shard_melee_206963, 'spell_molten_obsidian_shard')
scripted_by(obsidian_shard_ranged_206964, 'spell_molten_obsidian_shard')

obsidian_shard_heat_206962 = _heat(206962, 'Beastmaster\'s', OBSIDIAN_SHARD_HEAT)

obsidian_shard_206960 = _bonus(
    206960, 'Obsidian Shard',
    f'Your melee and ranged abilities grant 1 Heat, or {CRIT_HEAT} when they critically strike. At '
    f'{OBSIDIAN_SHARD_HEAT} Heat, your ability also flings an obsidian shard that hits the target for '
    + pot_text(obsidian_shard_melee_206963) + ' Physical damage and bounces to 1 more enemy within '
    f'{OBSIDIAN_SHARD_BOUNCE_RADIUS} yards.' + _HEAT_LASTS,
    _ICON_DEADLY_THROW,
    'Molten set, Beastmaster\'s 3 piece (Mail Agility). spell_proc: done melee and ranged abilities, hit phase, 100%. '
    'spell_molten_heat: a melee- or ranged-class spell gives 1 Heat (2 on a crit), once per cast. At 8, the shard on '
    'the target and on the nearest other enemy in combat within 10 yd of it (206964 after a ranged ability, 206963 '
    'after a melee one).',
    proc_type_mask=_ABILITIES,
)
_heat_proc(obsidian_shard_206960, _ABILITIES)

burning_shards_206961 = _bonus(
    206961, 'Burning Shards',
    'Your obsidian shards leave their targets burning for ' + pot_text(burning_shards_melee_206965, variant='total')
    + ' Fire damage over $206965d.',
    _ICON_IMMOLATE,
    'Molten set, Beastmaster\'s 5 piece (Mail Agility): a marker read by spell_molten_obsidian_shard (the burns are '
    '206965 / 206966).',
)

# =====================================================================================================================
# Leather Agility: Darkmantle (512)

slag_burst_eruption_206973 = _payout(
    206973, 'Slag Burst', School.FIRE,
    [_area_at_target(ap=100.0, radius=5.0)], _ICON_CONFLAGRATE,
    'Molten set, Darkmantle 3 piece: the eruption. Fire, attack power potency 100, T 1.5 s, the target and every enemy '
    'within 5 yd of it (spell_molten_eruption_in_combat: only enemies already in combat, and the target), '
    'DefenseType MAGIC. Look: stock Living Bomb SV 10692.',
    desc='Deals {pot1} Fire damage to the target and every enemy within $a1 yards of it.', visual=_SV_LIVING_BOMB,
)
scripted_by(slag_burst_eruption_206973, 'spell_molten_eruption_in_combat')

rekindle_buff_206974 = _self_buff(
    206974, 'Rekindle', School.FIRE,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER)],
    _ICON_ADRENALINE_RUSH,
    'Molten set, Darkmantle 5 piece: the next combo point generator grants 1 extra combo point. 20 s, one charge. '
    'spell_proc: done melee and ranged abilities, hit phase; spell_molten_rekindle keeps a spell with an '
    'ADD_COMBO_POINTS effect (Rogue::GainComboPoints on the hit target).',
    desc='Your next combo point generator grants 1 extra combo point.',
    aura_desc='Your next combo point generator grants 1 extra combo point.', duration_ms=20000, ProcCharges=1,
)
procs_on(rekindle_buff_206974, proc_flags=_ABILITIES, spell_type_mask=_PROC_SPELL_TYPE_ALL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_HIT_OR_CRIT, chance=100.0, charges=1)
scripted_by(rekindle_buff_206974, 'spell_molten_rekindle')

slag_burst_heat_206972 = _heat(206972, 'Darkmantle', SLAG_BURST_HEAT)

slag_burst_206970 = _bonus(
    206970, 'Slag Burst',
    'Your finishing moves grant 1 Heat per combo point spent, and 1 more when they critically strike. At '
    f'{SLAG_BURST_HEAT} Heat, your finishing move erupts, dealing ' + pot_text(slag_burst_eruption_206973)
    + ' Fire damage to the target and all enemies within $206973a1 yards.' + _HEAT_LASTS,
    _ICON_CONFLAGRATE,
    'Molten set, Darkmantle 3 piece (Leather Agility). spell_proc: done melee and ranged abilities and class NONE '
    'spells (Slice and Dice and Savage Roar are class NONE), hit phase, 100%. '
    'spell_molten_heat: a spell that needs combo points gives 1 Heat per point held at its hit (the points are taken '
    'only after the hits) and 1 more on a crit, once per cast. At 10, 206973 at the target (the wearer\'s victim '
    'after a self-cast finisher), and Rekindle 206974 with the 5 piece. Serves rogues and cats.',
    proc_type_mask=_FINISHERS,
)
_heat_proc(slag_burst_206970, _FINISHERS)

rekindle_206971 = _bonus(
    206971, 'Rekindle',
    'After a Slag Burst eruption, your next combo point generator grants 1 extra combo point.',
    _ICON_ADRENALINE_RUSH,
    'Molten set, Darkmantle 5 piece (Leather Agility): a marker read by the Slag Burst eruption (the buff is 206974).',
)

# =====================================================================================================================
# Leather Tank: Guardian's (1002)

scorching_hide_eruption_206983 = _payout(
    206983, 'Scorching Hide', School.FIRE,
    [_direct('direct', ap=80.0, target=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
             radius_yards=8.0)],
    _ICON_FIRE_SHIELD,
    'Molten set, Guardian\'s 3 piece: the eruption. Fire, attack power potency 80, T 1.5 s, every enemy within 8 yd '
    'of the wearer (spell_molten_scorching_hide: only enemies already in combat), DefenseType MAGIC. High threat: '
    'spell_threat pctMod 3 [tune]. Look: stock Hellfire SV 5423.',
    desc='Deals {pot1} Fire damage to every enemy within $a1 yards.', visual=_SV_HELLFIRE,
)
scripted_by(scorching_hide_eruption_206983, 'spell_molten_scorching_hide')
spell_threat(scorching_hide_eruption_206983, pct_mod=3.0)

tempered_hide_buff_206984 = _self_buff(
    206984, 'Tempered Hide', School.FIRE,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-6,
            misc_value=_ALL_SCHOOLS, implicit_target_a=_TARGET_UNIT_CASTER)],
    _ICON_SHIELD_WALL,
    'Molten set, Guardian\'s 5 piece: damage taken -5% (base -6 + die 1, all schools), 6 s, refreshed by the next '
    'eruption.',
    desc='Damage taken reduced by $s1%.', aura_desc='Damage taken reduced.', duration_ms=6000,
)

scorching_hide_heat_206982 = _heat(206982, 'Guardian\'s', SCORCHING_HIDE_HEAT)

scorching_hide_206980 = _bonus(
    206980, 'Scorching Hide',
    f'Your melee and ranged abilities grant 1 Heat, or {CRIT_HEAT} when they critically strike. At '
    f'{SCORCHING_HIDE_HEAT} Heat, '
    'you erupt, dealing ' + pot_text(scorching_hide_eruption_206983) + ' Fire damage to all enemies within '
    '$206983a1 yards, with high threat.' + _HEAT_LASTS,
    _ICON_FIRE_SHIELD,
    'Molten set, Guardian\'s 3 piece (Leather Tank). spell_proc: done melee and ranged abilities (Thunder Clap, '
    'Avenger\'s Shield, Judgement are ranged class; never an auto attack), hit phase, 100%. '
    'spell_molten_heat: a melee- or ranged-class spell gives 1 Heat (2 on a crit), once per cast. At 10, 206983 '
    'around the wearer, and Tempered Hide 206984 with the 5 piece.',
    proc_type_mask=_ABILITIES,
)
_heat_proc(scorching_hide_206980, _ABILITIES)

tempered_hide_206981 = _bonus(
    206981, 'Tempered Hide',
    'Each Scorching Hide eruption reduces the damage you take by $206984s1% for $206984d.',
    _ICON_SHIELD_WALL,
    'Molten set, Guardian\'s 5 piece (Leather Tank): a marker read by the Scorching Hide eruption (the buff is '
    '206984).',
)

# =====================================================================================================================
# Plate Tank: Impenetrable (1003)

molten_plate_buff_206993 = _self_buff(
    206993, 'Molten Plate', School.FIRE,
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_RESISTANCE_PCT, base_points=9, misc_value=_ARMOR,
            implicit_target_a=_TARGET_UNIT_CASTER)],
    _ICON_MOLTEN_ARMOR,
    'Molten set, Impenetrable 3 piece: armor +10% (SPELL_AURA_MOD_RESISTANCE_PCT, misc 1 = armor, base 9 + die 1), '
    '8 s, refreshed by the next eruption.',
    desc='Armor increased by $s1%.', aura_desc='Armor increased.', duration_ms=8000,
)

molten_plate_heat_206992 = _heat(206992, 'Impenetrable', MOLTEN_PLATE_HEAT)

molten_plate_206990 = _bonus(
    206990, 'Molten Plate',
    f'Your melee and ranged abilities grant 1 Heat, or {CRIT_HEAT} when they critically strike. At '
    f'{MOLTEN_PLATE_HEAT} Heat, '
    'your armor is increased by $206993s1% for $206993d.' + _HEAT_LASTS,
    _ICON_MOLTEN_ARMOR,
    'Molten set, Impenetrable 3 piece (Plate Tank). spell_proc: done melee and ranged abilities (Thunder Clap, '
    'Avenger\'s Shield, Judgement are ranged class; never an auto attack), hit phase, 100%. '
    'spell_molten_heat: a melee- or ranged-class spell gives 1 Heat (2 on a crit), once per cast. At 10, 206993 on '
    'the wearer.',
    proc_type_mask=_ABILITIES,
)
_heat_proc(molten_plate_206990, _ABILITIES)

banked_coals_206991 = _bonus(
    206991, 'Banked Coals',
    f'Using an ability with a cooldown of {COOLDOWN_HOOK_MIN_S} sec or more grants {BANKED_COALS_HEAT} Molten Plate '
    'Heat.',
    _ICON_BLOODRAGE,
    'Molten set, Impenetrable 5 piece (Plate Tank). spell_proc: every cast, cast phase, 100%. '
    'spell_molten_cooldown_heat: a spell on the Cooldown Haste rule\'s list (no item cast) adds 10 Heat, so it erupts '
    '(206993 on the wearer).',
    proc_type_mask=_EVERY_CAST,
)
_cooldown_proc(banked_coals_206991)

# The set bonuses by ItemSet id: (3 piece, 5 piece). source/items/molten_set.py builds the ItemSet rows from it.
SET_BONUSES = {
    517: (stoked_flame_206900, flare_up_206901),
    514: (cauterize_206910, mending_flame_206911),
    513: (ember_bloom_206920, fanned_embers_206921),
    519: (molten_thunder_206930, thunderhead_206931),
    516: (hallowed_flame_206940, tended_flame_206941),
    511: (molten_edge_206950, stoke_the_forge_206951),
    515: (obsidian_shard_206960, burning_shards_206961),
    512: (slag_burst_206970, rekindle_206971),
    1002: (scorching_hide_206980, tempered_hide_206981),
    1003: (molten_plate_206990, banked_coals_206991),
}
