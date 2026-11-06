"""
Deadmines Pilot WP-B5: Mr. Smite (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.4 rows SM, s3.5 row B5;
build spec docs/dungeons/deadmines-rework.md "Mr. Smite" SM1-SM13). WP-B5 owns this file (its spells: 205290-205319
only; C++ names in modules/mod-dungeon-bosses/src/Deadmines/MrSmiteLogic.h).

- 646 Mr. Smite: rebound from core's boss_mr_smite (untouched) to boss_mr_smite_rework, normal 17.0k
  (HealthModifier 35.1), the new stun immunity set. Heroic 472k is deadmines.py's override. The harpoon
  (creature_equip_template 646 id 4, item 44236), texts 4-5 and the Blackguard removal are WP-B5's SQL rev.

Spells. Every registry mechanic (Sweeping Slash, Backswing, Reckless Charge, Hammer Drop, debris, Shockwave,
aftershocks, Harpoon Sweep, Haft Slam, the volley's splash) deals its damage through mod-boss-mechanics' resolve spell
205001 (Physical); the spells below are what players see: a named cast bar per mechanic (no effect, not
interruptible: the build spec's interrupt list is empty and a kick must not look as if it stopped a registry hit), two
visuals, and two damage copies whose damage the script sets at cast (base point 0 = DeadminesKit::RefFlat), so DD's
heroic hook never scales them (ids >= 200000) and the heroic reference row gives the heroic number.

  205290  Sweeping Slash     SM2 cast bar, 2 s       SpellVisual 219 (Wide Slash 7342)
  205291  Backswing          SM3 cast bar, 1.5 s     SpellVisual 219 (heroic)
  205292  Reckless Charge    SM4 cast bar, 2 s       SpellVisual 3783 (Charge 22911); the follow-up dashes have no bar
  205293  Hammer Drop        SM5 cast bar, 1.5 s     SpellVisual 29 (Heroic Leap 6544); the 1 s leap fills the 2.5 s
  205294  Hammer Drop        SM5 landing, instant    SpellVisual 2355 (War Stomp 45)
  205295  Debris             SM6 at a point, instant SpellVisual 8455 (Cave In 36240), TARGET_DEST_DEST (heroic)
  205296  Shockwave          SM7 cast bar, 2 s       SpellVisual 358 (Shockwave 25425)
  205297  Aftershocks        SM8 cast bar, 1.5 s     SpellVisual 358 (heroic)
  205298  Smite Slam         SM9, 1.5 s cast on the tank, Physical, no stun. SpellVisual 205 and icon 314 of stock 6435.
  205299  Harpoon Sweep      SM10 cast bar, 2 s      SpellVisual 14170 (Sweep 26103)
  205300  Haft Slam          SM11 cast bar, 1.5 s    SpellVisual 145 (Thunderclap 8078) (heroic)
  205301  Harpoon Volley     SM12 cast bar, 2.5 s    SpellVisual 9899 (Harpoon Volley 44187)
  205302  Harpoon Volley     SM12 the carrier's own 15%, instant, unavoidable; SpellVisual 9862 (Harpoon 43993)
  205303  Sweeping Slash     SM2 / SM3 the tank's own 30% of the tank row, instant; SpellVisual 219 (Wide Slash 7342)

SM9, why a copy and not stock 6435 (handoff s7 #3: "copies only where the damage or effect changes, and those take
RefFlat"). Stock Smite Slam (Spell.dbc) is instant (CastingTimeIndex 1), effect 1 a 3 s stun aura (DurationIndex 27),
effect 2 50 Physical (BasePoints 49 + DieSides 1), and the spell-level Mechanic is 12 (stun). The build spec wants a
1.5 s cast with no stun. The stock id cannot carry the cast bar, and removing the stun would need a SpellScript bound
to a stock id (PreventHitEffect on effect 1) while the spell-level stun mechanic stays: a tank immune to stuns would
be immune to the whole hit, and the combat log would still read as a stun. Shortening the aura (ShortenAura) is no
answer either: the stun would land for a tick and interrupt the tank's cast. So 205298 is a copy (stock visual, icon,
melee defense type, PreventionType) without the stun, with a 1.5 s cast, its damage 3.9% of the tank row (50 normal,
160 heroic: the share of reference health DD would keep for stock 6435's 50).

SM1 Smite Stomp stays stock 6432 (its stun cut to 2 s by the script per target).
"""

from lib.dsl import RANGE_SELF, Effect, EffectType, School
from lib.dsl.registry import creature_template_columns, spell

from ._common import ATTR4_NO_CAST_LOG, IMMUNITY_BOSS_STUN, TARGET_UNIT_CASTER, TEXT_MASKS

creature_template_columns(
    646, ScriptName='boss_mr_smite_rework', AIName='', HealthModifier=35.1, CreatureImmunitiesId=IMMUNITY_BOSS_STUN,
)

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_DEST_DEST = 87
_RANGE_INDEX_MELEE = 2          # stock 6435's range (combat range)

_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_ALWAYS_HIT = 0x00040000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000

_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_PREVENTION_PACIFY = 2

_SCRIPT_DAMAGE = 'boss spell: the script sets the damage at cast (DeadminesKit::RefFlat, a percent of reference health)'


def _raw(desc: str, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'Description_Lang_enUS': desc,
            'AuraDescription_Lang_enUS': '', **TEXT_MASKS, **more}


def _cast_bar(spell_id: int, name: str, cast_ms: int, visual: int, icon: int, desc: str, note: str):
    """A named no-effect cast (DUMMY on the caster): the bar players read while the registry owns the hit."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=cast_ms, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B5 (Mr. Smite): {note} No-effect cast bar (DUMMY on the caster); the registry '
              'mechanic owns the hit. Not interruptible (InterruptFlags 0, PreventionType 0).',
        raw_overrides=_raw(desc, InterruptFlags=0, PreventionType=0, AttributesEx4=ATTR4_NO_CAST_LOG,
                           SpellVisualID_1=visual),
    )


def _visual(spell_id: int, name: str, visual: int, icon: int, target: int, desc: str, note: str):
    """An instant no-effect spell for its SpellVisual only (cast triggered by the script)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF if target == TARGET_UNIT_CASTER else 100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=target)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B5 (Mr. Smite): {note} Instant, no effect: the SpellVisual only.',
        raw_overrides=_raw(desc, CastingTimeIndex=1, InterruptFlags=0, PreventionType=0,
                           AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=visual),
    )


# --- Cutlasses -------------------------------------------------------------------------------------------------------
sweeping_slash_205290 = _cast_bar(
    205290, 'Sweeping Slash', 2000, 219, 277, 'Slashes everyone in front of the caster.',
    'SM2 Sweeping Slash, 2 s (registry Frontal cone 90 degrees, 8 yd). Wide Slash 7342 visual 219 and icon 277.')
backswing_205291 = _cast_bar(
    205291, 'Backswing', 1500, 219, 277, 'Slashes everyone behind the caster.',
    'SM3 Backswing (heroic), 1.5 s (the same cone behind him). Wide Slash visual 219, icon 277.')
reckless_charge_205292 = _cast_bar(
    205292, 'Reckless Charge', 2000, 3783, 457, 'Charges through everyone in a line.',
    'SM4 Reckless Charge, 2 s (registry line 3 yd to a non-tank; he charges along it). Charge 22911 visual 3783, '
    'icon 457. The heroic follow-up dashes (1.5 s) show no bar: he is still charging.')

# --- Hammer ----------------------------------------------------------------------------------------------------------
hammer_drop_205293 = _cast_bar(
    205293, 'Hammer Drop', 1500, 29, 3149, 'Leaps at an enemy and slams the ground.',
    'SM5 Hammer Drop, 1.5 s bar, then a 1 s leap: the registry circle 6 yd lands at 2.5 s. Heroic Leap 6544 '
    'visual 29, icon 3149.')
hammer_landing_205294 = _visual(
    205294, 'Hammer Drop', 2355, 50, TARGET_UNIT_CASTER, 'Slams the ground.',
    'SM5 landing, cast on himself at the circle\'s resolve. War Stomp 45 visual 2355, icon 50.')
debris_205295 = _visual(
    205295, 'Debris', 8455, 132, _TARGET_DEST_DEST, 'Rocks fall.',
    'SM6 debris (heroic), cast at each 4 yd circle\'s point when it resolves (TARGET_DEST_DEST). Cave In 36240 '
    'visual 8455, icon 132.')
shockwave_205296 = _cast_bar(
    205296, 'Shockwave', 2000, 358, 199, 'Sends a crack through the ground ahead.',
    'SM7 Shockwave, 2 s (registry line 25 x 4 yd ahead, tank exempt). Shockwave 25425 visual 358, icon 199.')
aftershocks_205297 = _cast_bar(
    205297, 'Aftershocks', 1500, 358, 199, 'Two more cracks run out to the sides.',
    'SM8 Aftershocks (heroic), 1.5 s (two lines at 30 degrees either side). Shockwave visual 358, icon 199.')

smite_slam_205298 = spell(
    id=205298, name='Smite Slam', school=School.NORMAL, cast_time_ms=1500, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=None, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=50, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_DAMAGE)],
    spell_icon_id=314,
    notes='Deadmines Pilot WP-B5 (Mr. Smite): SM9 Smite Slam, a copy of stock 6435 without its stun (module '
          'docstring: why a copy). 1.5 s cast on the tank, Physical, melee defense type and PreventionType pacify as '
          'stock, stock visual 205 and icon 314. DieSides 0: the script casts it with base point 0 = '
          'RefFlat(3.9% of the tank row), so the damage is exact; IGNORE_CASTER_MODIFIERS keeps boss buffs and the '
          'creature damage rate out of it (STAGE-X: the registry\'s numbers). Not interruptible (empty interrupt '
          'list). Base points 50 is the tooltip\'s normal value only.',
    raw_overrides=_raw('Inflicts $s1 Physical damage to an enemy.', DefenseType=_DEFENSE_MELEE,
                       PreventionType=_PREVENTION_PACIFY, InterruptFlags=0, RangeIndex=_RANGE_INDEX_MELEE,
                       AttributesEx3=_ATTR3_IGNORE_CASTER_MODIFIERS, SpellVisualID_1=205),
)

# --- Harpoon ---------------------------------------------------------------------------------------------------------
harpoon_sweep_205299 = _cast_bar(
    205299, 'Harpoon Sweep', 2000, 14170, 53, 'Sweeps a harpoon around the caster. Safe close in or far out.',
    'SM10 Harpoon Sweep, 2 s (registry donut 5 / 14 yd on him). Sweep 26103 visual 14170, icon 53.')
haft_slam_205300 = _cast_bar(
    205300, 'Haft Slam', 1500, 145, 199, 'Slams the haft down around the caster.',
    'SM11 Haft Slam (heroic), 1.5 s (registry circle 6 yd on him). Thunderclap 8078 visual 145, icon 199.')
harpoon_volley_205301 = _cast_bar(
    205301, 'Harpoon Volley', 2500, 9899, 45, 'Hurls a harpoon at every enemy but the closest. Spread out.',
    'SM12 Harpoon Volley, 2.5 s (registry Spread 6 yd, heroic 8, on every non-tank). Harpoon Volley 44187 '
    'visual 9899, icon 45.')

harpoon_impact_205302 = spell(
    id=205302, name='Harpoon Volley', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=195, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_DAMAGE)],
    spell_icon_id=185,
    notes='Deadmines Pilot WP-B5 (Mr. Smite): SM12 the carrier\'s own harpoon, 15% of the non-tank row (195 normal, '
          '618 heroic), unavoidable and never Weakened (ruling 15: a carrier\'s own hit). Cast triggered by the '
          'script on every carrier when the Spread resolves, base point 0 = RefFlat(15%). The registry resolve '
          'spells\' attribute set: no active defense, no redirection or reflection (DmgClass magic), ignores line of '
          'sight, cannot crit, always hits, ignores caster modifiers. Physical, so armor applies, as on the splash. '
          'Harpoon 43993 visual 9862, icon 185. Base points 195 is the tooltip\'s normal value only.',
    raw_overrides=_raw('Inflicts $s1 Physical damage.', CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC,
                       InterruptFlags=0, PreventionType=0,
                       Attributes=_ATTR0_NO_ACTIVE_DEFENSE,
                       AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION,
                       AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                       AttributesEx3=_ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
                       AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=9862),
)

slash_tank_205303 = spell(
    id=205303, name='Sweeping Slash', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=387, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_DAMAGE)],
    spell_icon_id=277,
    notes='Deadmines Pilot WP-F (Mr. Smite): SM2 Sweeping Slash / SM3 Backswing, the tank\'s own hit, 30% of the tank '
          'row (387 normal, 1,233 heroic). The registry cones stay TankExempt (bots read them as a Frontal, the tank '
          'gets no Weakened); when a cone resolves the script casts this on Smite\'s victim if it stands in the arc, '
          'base point 0 = RefFlat(30%, tank), as Sneed\'s Splinter Spray tank hit. 205302\'s attribute set (no '
          'active defense, no redirection or reflection, ignores line of sight, cannot crit, always hits, ignores '
          'caster modifiers). Physical, so armor applies ("30% of tank health before armor"). Wide Slash 7342 '
          'visual 219, icon 277. Base points 387 is the tooltip\'s normal value only.',
    raw_overrides=_raw('Inflicts $s1 Physical damage.', CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC,
                       InterruptFlags=0, PreventionType=0,
                       Attributes=_ATTR0_NO_ACTIVE_DEFENSE,
                       AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION,
                       AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                       AttributesEx3=_ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
                       AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=219),
)
