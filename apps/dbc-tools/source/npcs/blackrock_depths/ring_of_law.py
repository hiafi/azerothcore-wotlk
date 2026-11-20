"""
Blackrock Depths build WP-D4: the Ring of Law's frame, High Justice Grimstone (10096) and the wave mobs (8925-8928,
8932, 8933) (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D4; build spec
docs/dungeons/blackrock-depths-1-detention-block.md S1 "Ring of Law": the frame, Waves, Build spec RL1-RL6, RW1-RW6).
WP-D4 owns this file (its spells: kSpellsRingOfLaw 210810-210869 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h; RingOfLawLogic.h names the same ids; the texts and the SmartAI drop are
the core SQL rev rev_ring_of_law_blackrock_depths.sql). Binding these entries goes with BrdRingOfLaw::kBound = true in
the same change (lib/test_blackrock_depths_ring_of_law.py pins the three together).

- 10096 High Justice Grimstone: bound to npc_grimstone_rework (the stock npc_grimstone escort is unbound). Not a fight:
  his stock columns stay (level 52, faction 54, civilian, no loot); the script makes him unattackable and passive.
- The six wave mobs: bound to npc_ring_beast_rework (SmartAI off: the rev drops their 14 rows), the build spec's normal
  health at the level 51 warrior base 2,292 (3-mob waves 18,000 each, Thundersnouts 26,000, Borer Beetles 9,000; level
  50 ones 3.4% less), their stock levels, faction, DamageModifier 1 and loot. Heroic health is WP-H's
  (source/world/dungeons/blackrock_depths.py: 28k, 42k, 14k).

Spells (looks from ._visuals, WP-V-1's RL_* / RW_* picks; every look unconfirmed until seen in game):

  210810  Crowd Favor         RL1 the meter: a buff on every player, its stack count = Favor (0-10)
  210811  Crowd Gift          RL2 +10% damage done 10 s (the heal, 10% of reference health, is the script's HealBySpell)
  210812  Roar of the Crowd   RL2 at Favor 10: +10% damage done while it stays at 10
  210813  Crowd Gift          look: a spectator tosses roses at the player (a missile)
  210814  Jeer                RL3 a jeer's hit (resolve copy, Physical)
  210815-210817               looks: a bottle, a rotten apple, a rotten banana thrown from the gallery
  210818  Trial by Fire       RL4 the wedge's hit (resolve copy, Fire)
  210819  Trial by Fire       RL4 Grimstone's 3 s cast bar
  210820  Trial by Fire       look: an eruption on a stalker in the wedge
  210821  Burrow              RW1 the eruption's hit (resolve copy, Physical)
  210822-210823               looks: the worm sinks, the dirt burst
  210824  Tail Sting          RW2 the stinger's 2 s cast bar
  210825  Tail Sting          RW2 the cone's hit (resolve copy, Nature)
  210826  Tail Sting          RW2 the poison (a dispel is a reward)
  210827  Screech             RW3 2 s kickable cast: 10 yd hit + 2 s silence
  210828  Thunderclap         RW4 the 2 s wind-up bar
  210829  Thunderclap         RW4 the ring's hit (resolve copy, Nature)
  210830  Thunderclap         RW4 the slow (rider)
  210831  Venom Spit          RW5 the pool's tick (resolve copy, Nature)
  210832  Venom Spit          RW5 the pool's look (a stalker's aura)
  210833  Acid Burst          RW6 the burst's hit (resolve copy, Nature)
  210834  Acid Burst          RW6 the fallen beetle swells
  210835  Acid Burst          look: the burst at the corpse
  210836  Poison              Dredge Worm Poison 13298 rescaled (refflat DoT)
  210837  Venom Spit          Dredge Worm Venom Spit 6917 rescaled (refflat hit)
  210838  Lizard Bolt         Burrowing Thundersnout Lizard Bolt 15611 rescaled (refflat hit)
  210839-210869 spare

Kept stock (nothing to rescale): the six opening debuffs 14532-14535, 14538, 14539, Cleave 40504 (a weapon percent),
Pierce Armor 6016. Retired: Sonic Burst 8281, Web 745, the stock Thunderclap 15548 (RW4 replaces it).
"""

import math

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    TARGET_SRC_CASTER,
    TARGET_UNIT_SRC_AREA_ENEMY,
    TARGET_UNIT_TARGET_ENEMY,
    cast_bar,
    self_visual,
)
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    RL_CROWD_GIFT,
    RL_CROWD_GIFT_ALT,
    RL_ROTTEN_APPLE,
    RL_ROTTEN_BANANA,
    RL_THROW_BOTTLE,
    RL_TRIAL_BURST,
    RW_ACID_BURST,
    RW_BURROW,
    RW_BURROW_ERUPT,
    RW_SCREECH,
    RW_TAIL_STING,
    RW_THUNDERCLAP,
    SHIPPED_GOO_PUDDLE_STATE,
)

_D4 = 'Blackrock Depths build WP-D4 (the Ring of Law: the frame and the waves)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage / _periodic (DungeonKit::RefFlatOn)')

# --- constants (RingOfLawLogic.h; lib/test_blackrock_depths_ring_of_law.py pins each against the header) -------------

GRIMSTONE = 10096
WAVE_BASE_HEALTH = 2292         # kWaveBaseHealth: creature_classlevelstats level 51, class 1
# entry: (name, normal health, HealthModifier) in the stock RingMobs order (kWaveTypes)
WAVE_MOBS = {
    8925: ('Dredge Worm', 18_000, 7.853403),
    8926: ('Deep Stinger', 18_000, 7.853403),
    8927: ('Dark Screecher', 18_000, 7.853403),
    8928: ('Burrowing Thundersnout', 26_000, 11.343804),
    8933: ('Cave Creeper', 18_000, 7.853403),
    8932: ('Borer Beetle', 9_000, 3.926701),
}
GIFT_MS = 10000                 # kGiftMs
GIFT_DAMAGE_PCT = 10            # kGiftDamagePct
ROAR_DAMAGE_PCT = 10            # kRoarDamagePct
FAVOR_MAX = 10                  # kFavorMax (the buff's stack cap)
THROW_SPEED = 28.0              # kThrowMissileSpeed
TRIAL_FIRE_WARN_MS = 3000       # kTrialFireWarnMs
TRIAL_BURST_MS = 3000           # kTrialBurstMs
TAIL_STING_WARN_MS = 2000       # kTailStingWarnMs
TAIL_STING_POISON = (100, 150)  # kTailStingPoisonPct 1 / 1.5 (hundredths), per 2 s tick
TAIL_STING_POISON_TICK_MS = 2000
TAIL_STING_POISON_MS = 10000
SCREECH = (1000, 1500)          # kScreechPct 10 / 15 (hundredths)
SCREECH_CAST_MS = 2000
SCREECH_RADIUS = 10.0
SCREECH_SILENCE_MS = 2000
THUNDERCLAP_WARN_MS = 2000
THUNDERCLAP_SLOW_PCT = 41       # kThunderclapSlowPct
THUNDERCLAP_ATTACK_SLOW_PCT = 34
THUNDERCLAP_SLOW_MS = 6000
VENOM_POOL_MS = 13500           # kVenomSpitWarnMs + kVenomSpitLifeMs
ACID_SWELL_SCALE_PCT = 60       # kAcidSwellScalePct
ACID_SWELL_MS = 3000            # held by the body from its fall to its death (2.5 s), a little longer as a safety
WORM_POISON = (100, 150)        # kWormPoisonPct 1 / 1.5 (hundredths), per 3 s tick, 30 s
WORM_POISON_TICK_MS = 3000
WORM_POISON_MS = 30000
WORM_VENOM_SPIT = (300, 450)    # kWormVenomSpitPct 3 / 4.5
WORM_VENOM_SPIT_CAST_MS = 2500
LIZARD_BOLT = (500, 800)        # kLizardBoltPct 5 / 8
LIZARD_BOLT_CAST_MS = 2000

_DISPEL_POISON = 4
_MECHANIC_SNARE = 11
_MECHANIC_SILENCE = 9
_SCHOOL_MASK_ALL = 127
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SPELL_INTERRUPT_FLAGS_KICK = 15
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_STRENGTH_OF_THE_CHAMPION = 566    # Strength of the Champion 16916 (Crowd Favor)
_ICON_CASCADE_OF_ROSES = 1848           # Cascade of Roses 27571 (the gift)
_ICON_BATTLE_SHOUT = 456                # Battle Shout 6673 (Roar of the Crowd)
_ICON_MASSIVE_ERUPTION = 1137           # Massive Eruption 20483 (Trial by Fire)
_ICON_TAIL_STING = 1630                 # Tail Sting 36659
_ICON_SONIC_SCREECH = 3769              # Sonic Screech 64422
_ICON_THUNDERCLAP = 199                 # Thunderclap 15548
_ICON_POISON_CLOUD = 40                 # Poison Cloud 23861 (Venom Spit)
_ICON_ACID_BURST = 97                   # Acid Burst 70744
_ICON_POISON = 68                       # Poison 13298, Venom Spit 6917
_ICON_LIZARD_BOLT = 62                  # Lizard Bolt 15611
_ICON_GENERIC = 1

# --- the bindings -----------------------------------------------------------------------------------------------------

creature_template_columns(GRIMSTONE, ScriptName='npc_grimstone_rework', AIName='')

for _entry, (_name, _health, _modifier) in WAVE_MOBS.items():
    assert math.ceil(WAVE_BASE_HEALTH * _modifier) == _health, _name
    creature_template_columns(_entry, ScriptName='npc_ring_beast_rework', AIName='', HealthModifier=_modifier)


# --- helpers ----------------------------------------------------------------------------------------------------------

def _aura(spell_id: int, name: str, *, aura: AuraType, points: int, duration_ms: int, target: int, debuff: bool,
          icon: int, desc: str, aura_desc: str, notes: str, stacks: int = 0, visual: int = 0,
          excluded: str | None = None, school: School = School.NORMAL, misc: int | None = _SCHOOL_MASK_ALL,
          mechanic: int = 0, dispel: int = 0):
    """An aura the script applies (triggered): dropped on a map change."""
    raw = kit_raw(desc, aura_desc, CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                  AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                  AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP)
    if stacks:
        raw['CumulativeAura'] = stacks
    if visual:
        raw['SpellVisualID_1'] = visual
    effect = dict(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=points, die_sides=0,
                  implicit_target_a=target, mechanic=mechanic)
    if misc is not None and aura != AuraType.DUMMY:
        effect['misc_value'] = misc
    if excluded:
        effect['potency_excluded'] = excluded
    return spell(
        id=spell_id, name=name, school=school, dispel=dispel, mechanic=mechanic,
        attributes=(ATTR0_AURA_IS_DEBUFF if debuff else 0) | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=[Effect(**effect)], spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _throw(spell_id: int, name: str, visual: int, notes: str, icon: int = _ICON_GENERIC):
    """A crowd missile: a no-effect DUMMY a spectator in the gallery casts (triggered) at a spot on the floor."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon,
        notes=f'{_D4}: {notes} Speed {THROW_SPEED} yd/s (RingOfLawLogic.h kThrowMissileSpeed): from the gallery '
              '(about 40 yd) it lands about as the marker resolves.',
        raw_overrides=kit_raw('', SpellVisualID_1=visual, Speed=THROW_SPEED, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, CastingTimeIndex=1),
    )


def _refflat_hit(spell_id: int, name: str, school: School, pct: tuple[int, int], cast_ms: int, icon: int,
                 desc: str, notes: str):
    """A rescaled stock single-target nuke: SCHOOL_DAMAGE on the target at `pct` hundredths of the reference row
    (heroic in EffectMiscValueB) through spell_dungeon_refflat_damage, a kickable cast."""
    s = spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=cast_ms, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=pct[0] - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, EffectMiscValueB_1=pct[1], InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK,
                              PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                              AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG),
    )
    scripted_by(s, 'spell_dungeon_refflat_damage')
    return s


def _refflat_dot(spell_id: int, name: str, school: School, pct: tuple[int, int], tick_ms: int, duration_ms: int,
                 icon: int, desc: str, aura_desc: str, notes: str, dispel: int = 0):
    """A DoT at `pct` hundredths of the reference row a tick (heroic in EffectMiscValueB) through
    spell_dungeon_refflat_periodic; ignores caster modifiers."""
    s = spell(
        id=spell_id, name=name, school=school, dispel=dispel, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=pct[0],
                        die_sides=0, amplitude=tick_ms, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                        potency_excluded=_SCRIPT_REFFLAT)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, CastingTimeIndex=1, EffectMiscValueB_1=pct[1],
                              DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )
    scripted_by(s, 'spell_dungeon_refflat_periodic')
    return s


# --- RL1-RL3 Crowd Favor, the gift, the jeers ------------------------------------------------------------------------

crowd_favor_210810 = _aura(
    210810, 'Crowd Favor', aura=AuraType.DUMMY, points=0, duration_ms=-1, target=TARGET_UNIT_CASTER, debuff=False,
    icon=_ICON_STRENGTH_OF_THE_CHAMPION, stacks=FAVOR_MAX,
    desc='The crowd is watching. Dodge their champions\' blows to win them over.',
    aura_desc='The crowd\'s favor. At 8 or more they toss gifts; at 2 or less they throw things at you.',
    notes=f'{_D4}, RL1: the meter, a buff on every player whose stack count is Crowd Favor (0-10, 5 at each attempt): '
          'the script sets the stacks every second (DungeonKit::AddStacks on the player itself, CumulativeAura 10) and '
          'removes it at the credit and the wipe. +1 per dodgeable registry mechanic resolved with nobody hit, +2 for '
          'the wave dead within 30 s, -1 per player hit, -3 per death (losses x2 under Trial by the Crowd). A DUMMY, '
          'no number. Strength of the Champion\'s icon.',
)

crowd_gift_210811 = _aura(
    210811, 'Crowd Gift', aura=AuraType.MOD_DAMAGE_PERCENT_DONE, points=GIFT_DAMAGE_PCT, duration_ms=GIFT_MS,
    target=TARGET_UNIT_CASTER, debuff=False, icon=_ICON_CASCADE_OF_ROSES, visual=RL_CROWD_GIFT_ALT,
    desc='The crowd tosses you a gift.', aura_desc='Damage done increased by $s1%.',
    excluded='Crowd Gift: a flat +10% damage done, not a damage or heal value',
    notes=f'{_D4}, RL2: Favor 8-10, every 15 s, a random player on the floor: +10% damage done for 10 s, cast by the '
          'player on themself (triggered), and 10% of the reference row healed (the script\'s HealBySpell with this '
          'spell\'s name: no spell power, no potency). Flower Shower 27569\'s petals (SV 7525) as it lands; the toss '
          'is 210813.',
)

roar_of_the_crowd_210812 = _aura(
    210812, 'Roar of the Crowd', aura=AuraType.MOD_DAMAGE_PERCENT_DONE, points=ROAR_DAMAGE_PCT, duration_ms=-1,
    target=TARGET_UNIT_CASTER, debuff=False, icon=_ICON_BATTLE_SHOUT,
    desc='The crowd roars your name.', aura_desc='Damage done increased by $s1%.',
    excluded='Roar of the Crowd: a flat +10% damage done, not a damage or heal value',
    notes=f'{_D4}, RL2: at Favor 10 every player has +10% damage done while it stays at 10 (each player casts it on '
          'themself, triggered; the script removes it below 10, at the credit and at the wipe). No look: the icon.',
)

gift_toss_210813 = _throw(
    210813, 'Crowd Gift', RL_CROWD_GIFT,
    'RL2 the gift\'s toss: Cascade of Roses 27571\'s thrown flare that lands as rose petals (SV 7526, gap 16).',
    icon=_ICON_CASCADE_OF_ROSES,
)

jeer_210814 = resolve_copy(
    210814, 'Jeer', School.NORMAL, 'The crowd pelts you with bottles and rotten fruit.',
    f'{_D4}, RL3: a jeer\'s hit, a 3 yd circle at a random player\'s spot, 1.5 s: 10% (heroic 20%) of the reference '
    'row and 1 Weakened (registry tag 11). Favor 0-2 (Trial by the Crowd: every level), every 8 s, three at once; a '
    'volley with nobody hit is +1 Favor, each player hit -1. Copy of the mod-boss-mechanics resolve spell 205001 '
    '(Physical).',
)

jeer_bottle_210815 = _throw(
    210815, 'Jeer', RL_THROW_BOTTLE,
    'RL3 a jeer\'s look: Throw Bottle 43291\'s bottle and orange splat (SV 9741).',
)
jeer_apple_210816 = _throw(
    210816, 'Jeer', RL_ROTTEN_APPLE, 'RL3 a jeer\'s look: Rotten Apple Toss 58509 (SV 12567).',
)
jeer_banana_210817 = _throw(
    210817, 'Jeer', RL_ROTTEN_BANANA, 'RL3 a jeer\'s look: Rotten Banana Toss 58513 (SV 12569).',
)

# --- RL4 Trial by Fire -----------------------------------------------------------------------------------------------

trial_by_fire_210818 = resolve_copy(
    210818, 'Trial by Fire', School.FIRE, 'The floor of the Ring erupts.',
    f'{_D4}, RL4 (the Sentence): from the challenger\'s entry every 30 s, a 90 degree wedge from the ring center to '
    'the wall within it (23-45 yd: the floor is not round, NM), 3 s: 30% (heroic 45%) of the reference row and 1 '
    'Weakened (ruling 31; registry tag 12); the next wedge a quarter clockwise. Copy of the resolve spell 205003 '
    '(Fire).',
    icon=_ICON_MASSIVE_ERUPTION,
)

trial_by_fire_bar_210819 = cast_bar(
    210819, 'Trial by Fire', TRIAL_FIRE_WARN_MS, 'The Ring will burn.',
    f'{_D4}, RL4: Grimstone\'s 3 s cast bar from his corner while the wedge\'s marker fills (the registry owns the '
    'hit). Not interruptible (he is not attackable).',
    icon=_ICON_MASSIVE_ERUPTION, school=School.FIRE,
)

trial_burst_210820 = self_visual(
    210820, 'Trial by Fire', RL_TRIAL_BURST,
    f'{_D4}, RL4: an eruption, cast (triggered) by each of the 3-5 stalkers (the shared 300796, 3 s) through the '
    'wedge as it resolves: Massive Eruption 20483\'s Bomb_ExplosionA and molten chest (SV 889; never Eruption\'s SV '
    '5043, which draws nothing).',
    icon=_ICON_MASSIVE_ERUPTION, school=School.FIRE,
)

# --- RW1 Burrow ------------------------------------------------------------------------------------------------------

burrow_210821 = resolve_copy(
    210821, 'Burrow', School.NORMAL, 'A Dredge Worm bursts from the ground.',
    f'{_D4}, RW1: every 12 s one worm (Grimstone\'s clock) sinks and erupts 2 s later under a random player\'s spot, 5 '
    'yd: 25% (heroic 40%) of the reference row and 1 Weakened (registry tag 13). Copy of the resolve spell 205001 '
    '(Physical).',
)
burrow_sink_210822 = self_visual(
    210822, 'Burrow', RW_BURROW,
    f'{_D4}, RW1: the worm sinks (Submerge 37550\'s SV 8691: the burrow animation); it stays unselectable and rooted '
    'for the 2 s.',
)
burrow_erupt_210823 = self_visual(
    210823, 'Burrow', RW_BURROW_ERUPT,
    f'{_D4}, RW1: the dirt burst as the worm comes up under the spot (V-1\'s RO_LOOSED_SPAWN, shared with Roccor).',
)

# --- RW2 Tail Sting --------------------------------------------------------------------------------------------------

tail_sting_bar_210824 = cast_bar(
    210824, 'Tail Sting', TAIL_STING_WARN_MS, 'The stinger draws back its tail.',
    f'{_D4}, RW2: the stinger\'s 2 s bar while the 60 degree / 15 yd cone\'s marker fills (locked toward the player it '
    'turned on at the cast; the registry owns the hit). Tail Sting 36659\'s cast, missile and impact kit (SV 7391). '
    'Not interruptible; a stun that breaks it stops the sting (npc_ring_beast_rework OnSpellFailed).',
    icon=_ICON_TAIL_STING, visual=RW_TAIL_STING, school=School.NATURE,
)
tail_sting_210825 = resolve_copy(
    210825, 'Tail Sting', School.NATURE, 'A Deep Stinger lashes out with its tail.',
    f'{_D4}, RW2: every 10 s one stinger (Grimstone\'s clock) turns on a random player within 15 yd, the tank included '
    '(ruling 88): a 60 degree / 15 yd cone (section 7 #21\'s default: S1 sets no size), 2 s: 20% (heroic 35%) of the '
    'reference row, 1 Weakened and the poison 210826 (registry tag 14). Copy of the resolve spell 205004 (Nature).',
    icon=_ICON_TAIL_STING,
)
tail_sting_poison_210826 = _refflat_dot(
    210826, 'Tail Sting', School.NATURE, TAIL_STING_POISON, TAIL_STING_POISON_TICK_MS, TAIL_STING_POISON_MS,
    _ICON_TAIL_STING, 'Poisoned by a Deep Stinger.', 'Nature damage every 2 sec.',
    f'{_D4}, RW2: the sting\'s poison (the registry\'s rider on every player the cone hits): 1% (heroic 1.5%: '
    'EffectMiscValueB) of the reference row every 2 s for 10 s (this WP\'s default, designer question). A Poison: a '
    'dispel is a reward (the Ring\'s dispel list, priority 1).',
    dispel=_DISPEL_POISON,
)

# --- RW3 Screech -----------------------------------------------------------------------------------------------------

screech_210827 = spell(
    id=210827, name='Screech', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=SCREECH_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=SCREECH_SILENCE_MS,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=SCREECH[0] - 1, die_sides=1,
               implicit_target_a=TARGET_SRC_CASTER, implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY,
               radius_yards=SCREECH_RADIUS, potency_excluded=_SCRIPT_REFFLAT),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_SILENCE, base_points=0, die_sides=0,
               mechanic=_MECHANIC_SILENCE, implicit_target_a=TARGET_SRC_CASTER,
               implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=SCREECH_RADIUS),
    ],
    spell_icon_id=_ICON_SONIC_SCREECH,
    notes=f'{_D4}, RW3: each Dark Screecher every 18 s (4 s after the pull, staggered 1.5 s per bat): a 2 s cast, '
          'interruptible (InterruptFlags 15, silence-preventable; the Ring\'s interrupt list, priority 2: a reward). '
          'Landed, everyone within 10 yd of the bat takes 10% (heroic 15%: EffectMiscValueB) of the reference row '
          '(spell_dungeon_refflat_damage) and is silenced 2 s (the stock Sonic Burst 8281\'s 6 s silence retired). '
          'Nature: a kick locks nothing else the bat casts. Sonic Screech 64422\'s cast puff (SV 13637).',
    raw_overrides=kit_raw('A piercing screech.', 'Silenced.', EffectMiscValueB_1=SCREECH[1],
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=RW_SCREECH,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(screech_210827, 'spell_dungeon_refflat_damage')

# --- RW4 Thunderclap -------------------------------------------------------------------------------------------------

thunderclap_bar_210828 = cast_bar(
    210828, 'Thunderclap', THUNDERCLAP_WARN_MS, 'The Thundersnout rears up.',
    f'{_D4}, RW4: the stock Thunderclap\'s new 2 s wind-up while the 10 yd ring\'s marker fills (the registry owns the '
    'hit). Not interruptible; a stun that breaks it stops the clap.',
    icon=_ICON_THUNDERCLAP, school=School.NATURE,
)
thunderclap_210829 = resolve_copy(
    210829, 'Thunderclap', School.NATURE, 'The ground shakes around the Thundersnout.',
    f'{_D4}, RW4: each Burrowing Thundersnout every 8 s (stock), a 10 yd ring at the lizard, the tank included: 20% '
    '(heroic 35%) of the reference row, 1 Weakened and the slow 210830 (registry tag 15). Copy of the resolve spell '
    '205004 (Nature) with Thunderclap 15548\'s crack and shake (SV 145; the marker carries the radius).',
    icon=_ICON_THUNDERCLAP, visual=RW_THUNDERCLAP,
)
thunderclap_slow_210830 = spell(
    id=210830, name='Thunderclap', school=School.NATURE, dispel=0, mechanic=_MECHANIC_SNARE,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=THUNDERCLAP_SLOW_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED,
               base_points=-THUNDERCLAP_SLOW_PCT, die_sides=0, mechanic=_MECHANIC_SNARE,
               implicit_target_a=TARGET_UNIT_TARGET_ANY),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE,
               base_points=-THUNDERCLAP_ATTACK_SLOW_PCT, die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
               potency_excluded='Thunderclap: a flat -34% attack speed, not a damage or heal value'),
    ],
    spell_icon_id=_ICON_THUNDERCLAP,
    notes=f'{_D4}, RW4: the clap\'s slow (the registry\'s rider): the stock Thunderclap\'s -41% movement and -34% '
          'attack speed, 6 s. A snare. Not dispellable.',
    raw_overrides=kit_raw('Slowed.', 'Movement speed reduced by $s1%. Attack speed reduced by $s2%.',
                          CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- RW5 Venom Spit --------------------------------------------------------------------------------------------------

venom_spit_210831 = resolve_copy(
    210831, 'Venom Spit', School.NATURE, 'A pool of venom burns at your feet.',
    f'{_D4}, RW5: every 10 s one Cave Creeper (Grimstone\'s clock) spits at a random player\'s spot: a 4 yd pool after '
    '1.5 s for 12 s, 4% (heroic 6%) of the reference row a second (a Persistent registry Zone owned by Grimstone, so '
    'it outlives the spider; registry tag 16; one or two down at once). Copy of the resolve spell 205004 (Nature).',
    icon=_ICON_POISON_CLOUD,
)
venom_spit_pool_210832 = _aura(
    210832, 'Venom Spit', aura=AuraType.DUMMY, points=0, duration_ms=VENOM_POOL_MS, target=TARGET_UNIT_CASTER,
    debuff=False, icon=_ICON_POISON_CLOUD, visual=SHIPPED_GOO_PUDDLE_STATE, desc='', aura_desc='',
    notes=f'{_D4}, RW5: the pool\'s look, a DUMMY aura the pool\'s stalker (the shared 300796, 13.5 s) casts on '
          'itself: the shipped Deadmines goo STATE twin (SV 90343, 4 yd; V-1\'s RW_VENOM_SPIT_ALT\'s state form: '
          'Poison Cloud\'s SV 10397 is an AREA look that needs a dynamic object).',
)

# --- RW6 Acid Burst --------------------------------------------------------------------------------------------------

acid_burst_210833 = resolve_copy(
    210833, 'Acid Burst', School.NATURE, 'A dying Borer Beetle bursts.',
    f'{_D4}, RW6: a Borer Beetle\'s death: it lies swelling for 2 s (a held body, KT-D1), then bursts in a 4 yd circle '
    'at its corpse: 15% (heroic 25%) of the reference row and 1 Weakened (registry tag 17), and dies. Copy of the '
    'resolve spell 205004 (Nature).',
    icon=_ICON_ACID_BURST,
)
acid_swell_210834 = _aura(
    210834, 'Acid Burst', aura=AuraType.MOD_SCALE, points=ACID_SWELL_SCALE_PCT, duration_ms=ACID_SWELL_MS,
    target=TARGET_UNIT_CASTER, debuff=False, icon=_ICON_ACID_BURST, misc=None,
    desc='Swelling.', aura_desc='About to burst.',
    excluded='Acid Burst: a flat +60% model scale, not a damage or heal value',
    notes=f'{_D4}, RW6: the fallen beetle swells (+60% scale) for the 2 s before its burst: the held body\'s fallAura '
          '(DungeonKit::HeldBodySpec), removed as it dies.',
)
acid_burst_look_210835 = self_visual(
    210835, 'Acid Burst', RW_ACID_BURST,
    f'{_D4}, RW6: the burst at the corpse as the circle resolves: Spawn Bile Slime 16809\'s green ground burst (SV '
    '4339; never Acid Burst 70744\'s SV 14985).',
    icon=_ICON_ACID_BURST, school=School.NATURE,
)

# --- the stock casts kept, rescaled ----------------------------------------------------------------------------------

worm_poison_210836 = _refflat_dot(
    210836, 'Poison', School.NATURE, WORM_POISON, WORM_POISON_TICK_MS, WORM_POISON_MS, _ICON_POISON,
    'Poisoned by a Dredge Worm.', 'Nature damage every 3 sec.',
    f'{_D4}: the Dredge Worm\'s Poison 13298 (24 a tick) rescaled (rule 15: a copy in the slice): 1% (heroic 1.5%) of '
    'the reference row every 3 s for 30 s, on a random player (stock: 4 s, then every 8 s). A Poison (the Ring\'s '
    'dispel list, priority 1: a reward).',
    dispel=_DISPEL_POISON,
)
worm_venom_spit_210837 = _refflat_hit(
    210837, 'Venom Spit', School.NATURE, WORM_VENOM_SPIT, WORM_VENOM_SPIT_CAST_MS, _ICON_POISON,
    'Spits venom at an enemy.',
    f'{_D4}: the Dredge Worm\'s Venom Spit 6917 (30-50 and a small DoT) rescaled as a 2.5 s kickable cast on a random '
    'player: 3% (heroic 4.5%) of the reference row, no DoT; every 6 s (stock 3 s: halved so Burrow has room, designer '
    'question). The Ring\'s interrupt list, priority 1.',
)
lizard_bolt_210838 = _refflat_hit(
    210838, 'Lizard Bolt', School.NATURE, LIZARD_BOLT, LIZARD_BOLT_CAST_MS, _ICON_LIZARD_BOLT,
    'Hurls a bolt of lightning at an enemy.',
    f'{_D4}: the Burrowing Thundersnout\'s Lizard Bolt 15611 (36-40) rescaled as a 2 s kickable cast on a random '
    'player: 5% (heroic 8%) of the reference row; every 6 s (stock 3 s, designer question). The Ring\'s interrupt '
    'list, priority 1.',
)
