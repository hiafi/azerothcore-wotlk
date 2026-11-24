"""
Scarlet Monastery build WP-D11: Herod, "Blades of Light" (3975; the Scarlet Trainee 6575, his stock summon group 1)
(.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D11, s3.6, s3.8, s7 #22 A, s7 #31 A;
build spec docs/dungeons/scarlet-monastery-3-armory.md "Herod", HB0-HB5). WP-D11 owns this file; WP-S0 wrote the
skeleton. The hard mode (Call to Arms) is WP-D11H's herod_hard_mode.py (its own slice 213020-213059, the Garrison
Trainee 300944, the planted Ravager 300945).

Wave 2: the spells are declared now (they are only cast by his C++ AI, which registers once kWave2Bound flips); his
columns and the trainee's health wait for the wave switch (BIND_WAVE_2, flipped with kWave2Bound by W2-SETUP), so until
then both keep their stock rows and SmartAI (W2-SETUP's rev drops SmartAI 3975 rows 0-9; the trainee's own SmartAI
"Set In Combat With Zone" stays).

- 3975 Herod: boss_herod_rework (modules/mod-dungeon-bosses src/ScarletMonastery/boss_herod_rework.cpp), SmartAI off,
  the build spec's normal health (66k = HealthModifier 49.401 on the level 37 warrior base 1,336), his stock
  DamageModifier 3.8, stun immunity 1972 (s7 #10: the stock set -273 and the stock Whirlwind's magic immunity are gone),
  INSTANCE_BIND (his stock encounter 448 credits him). Heroic 320k is WP-H's override; the hard mode's 400k is D11H's
  (at the pull, by script).
- 6575 Scarlet Trainee (stock, boss-kit only: no spawns of its own): 20 x 400 on normal = HealthModifier 0.5427 on the
  level 30 mage base 737 (stock 0.15, about 111). Its heroic copy (2.5k, level 60) is WP-H's (`extra=`).

Spells (kSpellsHerod 212980-213019; HerodLogic.h names the same ids; looks from ._visuals, WP-V's HB_* picks, every
look unconfirmed until seen in game). His damage is a percent of the reference row (the tank row on the tank): the
registry lands the lanes, the blades, the throw, the return line and the cleave on others through resolve copies, and
his spin's and the whirling axe's passes through RegistryHit with the same copies; the cleave's tank hit binds the
kit's spell_dungeon_refflat_damage (the percent in hundredths in the effect, EffectMiscValueB on heroic):

  212980  Blades of Light   HB1 the cyclone on him from the yell to his return (Whirlwind 26083's SV 7428; no
                            immunity: the stock Whirlwind's is gone)
  212981  Blades of Light   HB1a the out lane's hit: resolve copy, Physical, 30% / 45% and Weakened
  212982  Blades of Light   HB1b his spin passing a player on the lap: resolve copy, Physical, once per player a lap
  212983  Blade of Light    HB1c a blade's hit: resolve copy, Holy, 30% / 45% and Weakened
  212984  Blade of Light    HB1c the blade's flight (Fury of the Ashbringer's SV 8618, a missile to a point)
  212985  Blades of Light   HB1d the home lane's hit: resolve copy, Physical
  212986  Ravager's Throw   HB2 the throw's circle: resolve copy, Physical
  212987  Ravager's Throw   HB2 the axe's flight (Throw Axe 16075's SV 3962, a missile to a point; also its flight home)
  212988  Ravager           HB2 the axe spinning on the floor and whirling (Bladestorm's SV 6044 on a stalker)
  212989  Ravager's Return  HB2a the return line's hit: resolve copy, Physical
  212990  Ravager Whirls    HB2w the whirling axe passing a player (heroic): resolve copy, Physical, once per whirl
  212991  Champion's Cleave HB3 the cleave on others: resolve copy, Physical (Cleave 15496's SV 219)
  212992  Champion's Cleave HB3 the cleave on the tank: 15% / 25% of the tank row (kit percent script)
  212993  Frenzy            HB4 +30% attack speed, +20% Physical damage, +15% size (the stock look), the rest of the
                            fight
  212994-213019 spare.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_NO_ACTIVE_DEFENSE,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
    TARGET_UNIT_TARGET_ENEMY,
)
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    TARGET_UNIT_CASTER,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import HB_BLADE, HB_CLEAVE, HB_CYCLONE, HB_FLOOR_SPIN, HB_THROW

_D11 = 'Scarlet Monastery build WP-D11 (Herod)'

HEROD = 3975
SCARLET_TRAINEE = 6575
SCRIPT_NAME = 'boss_herod_rework'

# --- the creatures (held back until wave 2 binds: _common.py BIND_WAVE_2) -------------------------------------------

# The build spec's normal health at 5 players (S0's table): 66k = 49.401 x 1,336 (the level 37 warrior);
# creature_classlevelstats basehp0, live 2026-11-20. His stock DamageModifier (base SQL).
HEROD_HEALTH_MODIFIER = 49.401
HEROD_DAMAGE_MODIFIER = 3.8

# HB5: 20 x 400 = 0.5427 x 737 (the level 30 mage).
TRAINEE_HEALTH_MODIFIER = 0.5427

if BIND_WAVE_2:
    creature_template_columns(HEROD, **boss_columns(
        SCRIPT_NAME, HEROD_HEALTH_MODIFIER, damage_modifier=HEROD_DAMAGE_MODIFIER,
    ))
    creature_template_columns(SCARLET_TRAINEE, HealthModifier=TRAINEE_HEALTH_MODIFIER)

# --- constants (HerodLogic.h; lib/test_scarlet_monastery_herod.py pins each against the header) -----------------------

CLEAVE_TANK_PCT = (1500, 2500)      # kCleaveTankPct 15 / 25 (hundredths: normal in the effect, heroic in MiscValueB)
FRENZY_HASTE_PCT = 30               # kFrenzyHastePct
FRENZY_DAMAGE_PCT = 20              # kFrenzyDamagePct
FRENZY_SCALE_PCT = 15               # the stock Frenzy 8269's size (the look players know)
MISSILE_SPEED = 20.0                # yd/s: a blade or the axe crossing the pit lands about its marker's 1.5-2 s

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_DEFENSE_MELEE = 2
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_MISC_SCHOOL_MASK_PHYSICAL = 1

_SCRIPT_REFFLAT = ('Scarlet Monastery D11: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn: the tank row on the tank)')

# Stock icons (Spell.dbc SpellIconID of the named spell, read from the stock client 2026-11-20)
_ICON_WHIRLWIND = 83                    # Whirlwind 8989 / 26083, Bladestorm 9632
_ICON_ASHBRINGER = 108                  # Fury of the Ashbringer 43225
_ICON_THROW_AXE = 1529                  # Throw Axe 16075
_ICON_CLEAVE = 277                      # Cleave 15496
_ICON_FRENZY = 95                       # Frenzy 8269


def _look_at_point(spell_id: int, name: str, visual: int, notes: str, icon: int, speed: float = 0.0):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), triggered (the
    Crell / Kell look shape). `speed` (yd/s) makes it a missile from the caster."""
    raw = kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                  AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                  AttributesEx4=ATTR4_NO_CAST_LOG)
    if speed:
        raw['Speed'] = speed
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _lasting_look(spell_id: int, name: str, visual: int, desc: str, notes: str, icon: int):
    """A lasting look: a DUMMY aura (no duration, no effect) cast on the caster itself (triggered); the script removes
    it (or the stalker carrying it despawns). Not dispellable."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, desc, CastingTimeIndex=1, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- HB1 Blades of Light ----------------------------------------------------------------------------------------------

cyclone_212980 = _lasting_look(
    212980, 'Blades of Light', HB_CYCLONE, 'Herod spins as a cyclone of blades.',
    f'{_D11}, HB1: the cyclone on Herod from the "Blades of light!" yell to his return to the pit\'s center (the '
    'script removes it): Whirlwind 26083\'s SpellVisual 7428 (never Whirlwind 8989\'s SV 6664, a dust cloud). No '
    'effect: the stock Whirlwind\'s magic immunity is gone (s7 #10: he is the only target), his spin\'s hits are '
    '212982.',
    icon=_ICON_WHIRLWIND,
)

out_lane_212981 = resolve_copy(
    212981, 'Blades of Light', School.NORMAL, 'Herod spins out of the pit.',
    f'{_D11}, HB1a: the out lane, 10 yd wide from his spot to a random point of the ledge, a 2.5 s marker from the '
    'yell; he dashes it as it resolves: 30% (heroic 45%) of the reference row and 1 Weakened, the tank row on the tank '
    '(registry tag 11). Copy of the mod-boss-mechanics resolve spell 205001 (Physical).',
    icon=_ICON_WHIRLWIND,
)

lap_212982 = resolve_copy(
    212982, 'Blades of Light', School.NORMAL, 'The cyclone passes.',
    f'{_D11}, HB1b: his 5 yd spin passing a player as he laps the ledge (the band from the pit\'s edge to the walls, '
    'the door spur included, is marked from the yell: everyone goes down into the pit), once per player a lap: 30% '
    '(heroic 45%) and 1 Weakened, the tank row on the tank (DungeonKit::RegistryHit, registry tag 12). Copy of the '
    'resolve spell 205001 (Physical).',
    icon=_ICON_WHIRLWIND,
)

blade_212983 = resolve_copy(
    212983, 'Blade of Light', School.HOLY, 'A blade of light flies across the pit.',
    f'{_D11}, HB1c: a blade of light, a lane 4 yd wide from Herod on the ledge across the pit to its far edge toward a '
    'random player (the tank included), a 1.5 s marker: normal one every 2 s of the lap (after Frenzy every 1.5 s), '
    'heroic one every 1.5 s (after Frenzy two at once every 1 s): 30% (heroic 45%) and 1 Weakened, the tank row on the '
    'tank (registry tag 13). Copy of the resolve spell 205002 (Holy).',
    icon=_ICON_ASHBRINGER,
)

blade_look_212984 = _look_at_point(
    212984, 'Blade of Light', HB_BLADE,
    f'{_D11}, HB1c: the blade\'s flight, a missile from Herod to the lane\'s far end (triggered) as its marker starts, '
    f'at {MISSILE_SPEED:.0f} yd/s: Fury of the Ashbringer 43225\'s SpellVisual 8618 (a flying Sword_2H_Ashbringer; '
    'never SV 7582). Look only.',
    icon=_ICON_ASHBRINGER, speed=MISSILE_SPEED,
)

home_lane_212985 = resolve_copy(
    212985, 'Blades of Light', School.NORMAL, 'Herod spins home.',
    f'{_D11}, HB1d: the home lane, 10 yd wide from his spot on the ledge to the pit\'s center, a 1.5 s marker after '
    'the lap (a chained follow-up); he dashes it as it resolves and the tank picks him up: 30% (heroic 45%) and 1 '
    'Weakened, the tank row on the tank (registry tag 14). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_WHIRLWIND,
)

# --- HB2 Ravager's Throw, HB2w Ravager Whirls -------------------------------------------------------------------------

throw_212986 = resolve_copy(
    212986, 'Ravager\'s Throw', School.NORMAL, 'Herod hurls Ravager.',
    f'{_D11}, HB2: the throw, a 5 yd circle at a random player\'s spot (the tank included), a 2 s marker, at 6 s then '
    'every 30 s (heroic 32 s), never during a spin: 30% (heroic 45%) and 1 Weakened, the tank row on the tank '
    '(registry tag 2). Ravager leaves his hand until it comes back (he punches the tank and never cleaves). Copy of '
    'the resolve spell 205001 (Physical).',
    icon=_ICON_THROW_AXE,
)

throw_look_212987 = _look_at_point(
    212987, 'Ravager\'s Throw', HB_THROW,
    f'{_D11}, HB2: the axe\'s flight, a missile from Herod to the throw\'s spot as its marker starts, and from the axe '
    f'back to Herod as it flies home, at {MISSILE_SPEED:.0f} yd/s: Throw Axe 16075\'s SpellVisual 3962 (never Throw '
    'Axe 40563\'s SV 9220: no axe in flight). Look only.',
    icon=_ICON_THROW_AXE, speed=MISSILE_SPEED,
)

axe_spin_212988 = _lasting_look(
    212988, 'Ravager', HB_FLOOR_SPIN, 'Ravager whirls on its own.',
    f'{_D11}, HB2 / HB2w: the axe where it lands, spinning on the floor (normal) or whirling toward a player (heroic): '
    'a DUMMY aura the wave 2 generic stalker 300958 at the axe casts on itself, Bladestorm 9632\'s SpellVisual 6044. '
    'The stalker goes with the axe\'s flight home.',
    icon=_ICON_WHIRLWIND,
)

return_212989 = resolve_copy(
    212989, 'Ravager\'s Return', School.NORMAL, 'Ravager flies back to Herod\'s hand.',
    f'{_D11}, HB2a: the axe\'s way home, a line 3 yd wide from where it is to his hand, a 1.5 s marker (normal: as it '
    'lands; heroic: after the whirl): 30% (heroic 45%) and 1 Weakened, the tank row on the tank (registry tag 21). '
    'Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_THROW_AXE,
)

whirl_212990 = resolve_copy(
    212990, 'Ravager Whirls', School.NORMAL, 'Ravager whirls on its own.',
    f'{_D11}, HB2w (heroic): the thrown axe whirls for 5 s along a short path toward a random player, a 4 yd spin at '
    '5 yd/s, its path shown 1.5 s ahead: 45% and 1 Weakened to each player it passes, once per whirl, the tank row on '
    'the tank (DungeonKit::RegistryHit, registry tag 22). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_WHIRLWIND,
)

# --- HB3 Champion's Cleave --------------------------------------------------------------------------------------------

cleave_212991 = resolve_copy(
    212991, 'Champion\'s Cleave', School.NORMAL, 'Herod cleaves in front of him.',
    f'{_D11}, HB3: the cleave on others, a registry Frontal (90 degrees, 8 yd, a 1.5 s marker, the tank exempt) every '
    '6 s while he holds a weapon in melee (never while he spins or the axe is out): 30% (heroic 45%) of the reference '
    'row and 1 Weakened (registry tag 3). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_CLEAVE, visual=HB_CLEAVE,
)

cleave_tank_212992 = spell(
    id=212992, name='Champion\'s Cleave', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=CLEAVE_TANK_PCT[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CLEAVE,
    notes=f'{_D11}, HB3: the cleave on the tank as the Frontal lands (his victim inside the cone): 15% (heroic 25%: '
          'EffectMiscValueB) of the tank\'s row, Physical, instant, never missed (always hits, no active defense, '
          'cannot crit) and ignoring his modifiers. Tank work: no Weakened. Binds the kit\'s '
          'spell_dungeon_refflat_damage. Cleave 15496\'s SV 219.',
    raw_overrides=kit_raw('Herod cleaves in front of him.', instant=True, EffectMiscValueB_1=CLEAVE_TANK_PCT[1],
                          DefenseType=_DEFENSE_MELEE, SpellVisualID_1=HB_CLEAVE,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(cleave_tank_212992, 'spell_dungeon_refflat_damage')

# --- HB4 Frenzy -------------------------------------------------------------------------------------------------------

frenzy_212993 = spell(
    id=212993, name='Frenzy', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=FRENZY_HASTE_PCT - 1,
               die_sides=1, implicit_target_a=TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
               base_points=FRENZY_DAMAGE_PCT - 1, die_sides=1, misc_value=_MISC_SCHOOL_MASK_PHYSICAL,
               implicit_target_a=TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_SCALE, base_points=FRENZY_SCALE_PCT - 1,
               die_sides=1, implicit_target_a=TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_FRENZY,
    notes=f'{_D11}, HB4 Frenzy (the stock Frenzy 8269 softened): once at 50% ("Light, give me strength!", "%s becomes '
          'enraged!"; the hard mode: at his rising instead), for the rest of the fight: +30% attack speed, +20% '
          'Physical damage done, +15% size (the stock look). The blades quicken (the script). Not dispellable or '
          'stealable (no Enrage dispel type: Tranquilizing Shot never removes it; the boss data has no purge). The '
          'stock 8269 (+50% damage, +60% speed, 2 min) is no longer cast.',
    raw_overrides=kit_raw('Herod becomes enraged.', 'Attack speed increased by 30%. Physical damage increased by 20%.',
                          CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
