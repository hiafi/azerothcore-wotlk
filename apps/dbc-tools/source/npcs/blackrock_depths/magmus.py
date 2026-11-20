"""
Blackrock Depths build WP-D22: Magmus (9938) and the six Ironhand Guardians (8982)
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 / s3.5 row D22, s3.6, s3.8, s3.10;
build spec docs/dungeons/blackrock-depths-4-imperial-seat.md "Magmus" MG1-MG5, rulings 75, 76, 88). WP-D22 owns this
file (its spells: kSpellsMagmus 211580-211609 of modules/mod-dungeon-bosses src/BlackrockDepths/
BlackrockDepthsRework.h only; MagmusLogic.h names the same ids). The engine side is src/BlackrockDepths/
boss_magmus_rework.cpp; his three new texts are data/sql/updates/pending_db_world/rev_magmus_blackrock_depths.sql.

- 9938 Magmus: boss_magmus_rework (SmartAI off: he has none in the live DB, so no row to drop), the build spec's normal
  health (170k: HealthModifier 62.986 on the level 56 warrior class base 2,699), the kit's stun immunity set 1972 (s7
  #10; he is not a fire giant: the stock -251 set has no school immunity), INSTANCE_BIND (flags_extra 1),
  DamageModifier 3.5 (the stock base value; the live 7 is a leftover). Heroic 240k is WP-H's override
  (source/world/dungeons/blackrock_depths.py). Display 12162 (Bael'Gar wears it too) is the stock one and stays.
- 8982 Ironhand Guardian: npc_ironhand_guardian_rework (stock brd_ironhand_guardian retired: its Gout of Flame timer is
  gone, the statues breathe on his order). Template, flags and spawns stay stock (unselectable scenery, rooted).
  Both bindings are held back until wave 2 binds (_common.py BIND_WAVE_2); the spells are declared regardless (inert).

Spells. The registry hits (the ignition, the burn, the strip, the pools, the Fiery Burst circle) deal their damage
through dungeon copies of the mod-boss-mechanics resolve spell (Fire). The War Stomp is a percent of the reference row
on the kit's generic script (spell_dungeon_refflat_damage: the hundredths in the effect, the heroic ones in
EffectMiscValueB) plus the 2 s stun. The rest are looks:

  211580  War Stomp            MG1 stock 15593 rescaled (rule 15: a copy): 5 yd round him, a Physical hit of 12% /
                               15% of the row and a 2 s stun (was 8 s)
  211581  Fiery Burst          MG2 the 2 s bar, interruptible, on the random target (Fire; the circle is the registry's)
  211582  Fiery Burst          MG2 the circle's hit: 8 yd, 25% / 40% + Weakened (resolve copy, Fire)
  211583  Fiery Burst          look: the stock Fiery Burst's blast at the circle (SV 516)
  211584  Crossfire            MG3 the lane's ignition: 30% / 45% + Weakened (resolve copy, Fire)
  211585  Crossfire            MG3 the lane's burn tick: 10% / 15% a second (resolve copy, Fire)
  211586  Flame Wall           MG4 the strip's tick: 10% / 15% a second (resolve copy, Fire)
  211587  Dripping Magma       MG5 a pool's tick: 8% a second (resolve copy, Fire)
  211588  Flame Wreath         look: a statue glows 3 s (a self aura on the statue, Flame Wreath 29947's SV 4101)
  211589  Gout of Flame        look: a statue's breath at a point (a statue casts it, Gout of Flame 15538's SV 3642)
  211590  Flame Jets           look: the burst at a lane's end (he casts it at both ends, SV 13233)
  211591  Dripping Magma       look: a pool, an aura on a stalker (the shipped 4 yd lava pool state, SV 90606)
  211592-211609 spare.

Retired: the stock War Stomp 15593 and Fiery Burst 15668 are not cast any more (rule 15: copies in the slice); the
statues' Gout of Flame 15529 / 15538 timer is gone (their visuals are reused by 211588 / 211589). Visual ids are V-1's
(._visuals MG_*; the stomp's is MG_WAR_STOMP, the same stock SV 2355 as Grizzle's GZ_EARTHSHAKER_STOMP); every
look is unconfirmed until seen in game.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
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
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    TARGET_UNIT_CASTER,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    MG_WAR_STOMP,
    MG_CROSSFIRE_BREATH,
    MG_CROSSFIRE_END,
    MG_DRIPPING_MAGMA,
    MG_FIERY_BURST,
    MG_STATUE_GLOW,
)

_D22 = 'Blackrock Depths build WP-D22 (Magmus)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')

# --- the bindings (held back until wave 2 binds the section: _common.py BIND_WAVE_2) ---------------------------------

MAGMUS_COLUMNS = boss_columns('boss_magmus_rework', 62.986, damage_modifier=3.5)
IRONHAND_COLUMNS = {'ScriptName': 'npc_ironhand_guardian_rework', 'AIName': ''}

if BIND_WAVE_2:
    creature_template_columns(9938, **MAGMUS_COLUMNS)
    creature_template_columns(8982, **IRONHAND_COLUMNS)

# --- constants (MagmusLogic.h; lib/test_blackrock_depths_magmus.py pins each against the header) ----------------------

STOMP_PCT = (1200, 1500)        # kStompPct 12 / 15 (hundredths)
STOMP_STUN_MS = 2000            # kStompStunMs
STOMP_RADIUS = 5.0              # kStompRadiusYd
BURST_CAST_MS = 2000            # kBurstCastMs
BURST_RANGE = 40.0              # kBurstRangeYd
GLOW_MS = 3000                  # kGlowMs (the statue glow lasts as long as the warning)

_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_MECHANIC_STUN = 12
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15

# Icons (the client Spell.dbc, the stock spells').
_ICON_WAR_STOMP = 50            # War Stomp 15593
_ICON_FIERY_BURST = 18          # Fiery Burst 15668
_ICON_GOUT_OF_FLAME = 937       # Gout of Flame 15538 / Flame Wreath 29947
_ICON_FLAME_JETS = 37           # Flame Jets 62680

# The scripted hit: no threat redirection or reflection, no crit, always hits, ignores his modifiers (a percent of the
# reference row).
_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
    AttributesEx2=ATTR2_CANT_CRIT,
    AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
)


def _look_at_point(spell_id: int, name: str, visual: int, notes: str, icon: int, school: School = School.FIRE):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), triggered:
    Magmus's own cast, or a statue's."""
    return spell(
        id=spell_id, name=name, school=school, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _state_aura(spell_id: int, name: str, visual: int, duration_ms: int, notes: str, icon: int):
    """A hidden DUMMY aura a statue or a stalker casts on itself for its look (a state kit needs an aura to play; not
    passive: a passive aura is never sent to the client). `duration_ms` -1: until the stalker goes."""
    return spell(
        id=spell_id, name=name, school=School.FIRE, dispel=0, mechanic=0,
        attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              CastingTimeIndex=1),
    )


# --- MG1 War Stomp ----------------------------------------------------------------------------------------------------

war_stomp_211580 = spell(
    id=211580, name='War Stomp', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=STOMP_STUN_MS,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=STOMP_PCT[0] - 1, die_sides=1,
               implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
               radius_yards=STOMP_RADIUS, potency_excluded=_SCRIPT_REFFLAT),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0, die_sides=0,
               implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
               radius_yards=STOMP_RADIUS, mechanic=_MECHANIC_STUN),
    ],
    spell_icon_id=_ICON_WAR_STOMP,
    notes=f'{_D22}, MG1: the stock War Stomp 15593 (a 5 yd PBAoE, normalized weapon damage and an 8 s stun) kept and '
          'rescaled (rule 15: a copy in the slice, never the shared id): the stun drops to 2 s (ruling 76, the 2 s '
          'rule). He casts it on himself at 8-12 s and every 8-12 s (the stock timers), everyone within 5 yd takes '
          'the hit (12%, heroic 15%, of the reference row, the tank row on the tank: hundredths 1200, '
          'EffectMiscValueB 1500; the spec leaves it to "stock rescaled", gap 36, designer question 1) and the stun. '
          'It never starts while a Crossfire\'s glow is up or ends after one starts (the tank must be free to walk him '
          'out of the lane). Cannot crit, always hits, ignores his modifiers. Stock War Stomp\'s look (SV 2355). The '
          'stun is removed from every player when the fight ends.',
    raw_overrides=kit_raw('Stuns all enemies within $a1 yards for $d and deals physical damage.',
                          'Stunned.', instant=True, SpellVisualID_1=MG_WAR_STOMP,
                          EffectMiscValueB_1=STOMP_PCT[1], **_HIT_ATTRS),
)
scripted_by(war_stomp_211580, 'spell_dungeon_refflat_damage')

# --- MG2 Fiery Burst --------------------------------------------------------------------------------------------------

fiery_burst_cast_211581 = spell(
    id=211581, name='Fiery Burst', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=BURST_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=BURST_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_FIERY_BURST,
    notes=f'{_D22}, MG2: the Fiery Burst\'s 2 s bar, cast on a random player (the tank too, ruling 88). No effect: the '
          'registry\'s 8 yd circle (211582), fixed where the target stands when the bar starts, owns the hit. '
          'Interruptible (InterruptFlags 15, PreventionType silence): a reward on normal and heroic (the descriptor\'s '
          'interrupt list); a kick cancels the circle (OnSpellFailed). Fire school: the must-play warnings (Crossfire, '
          'Flame Wall) are not casts, so no interrupt lockout can stop them.',
    raw_overrides=kit_raw('Blasts enemies within 8 yards of the target with fire.',
                          InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

fiery_burst_211582 = resolve_copy(
    211582, 'Fiery Burst', School.FIRE, 'Fire blasts the ground.',
    f'{_D22}, MG2: the circle\'s hit: 8 yd, landing as the 2 s bar ends: 25% (heroic 40%) of the row and 1 Weakened '
    '(registry tag 1), the tank row on the tank. Copy of the resolve spell 205001 with the Fire school.',
    icon=_ICON_FIERY_BURST,
)

fiery_burst_look_211583 = _look_at_point(
    211583, 'Fiery Burst', MG_FIERY_BURST,
    f'{_D22}, MG2: the blast where the circle lands. Magmus casts it (triggered) at the circle\'s spot as it resolves: '
    'the stock Fiery Burst 15668\'s SpellVisual 516. Look only.',
    icon=_ICON_FIERY_BURST,
)

# --- MG3 Crossfire, MG4 Flame Wall, MG5 Dripping Magma ----------------------------------------------------------------

crossfire_ignition_211584 = resolve_copy(
    211584, 'Crossfire', School.FIRE, 'Flame sweeps across the hall.',
    f'{_D22}, MG3: the lane\'s ignition, 3 s after the fist: a 10 yd lane wall to wall at his y (locked at the fist), '
    '30% (heroic 45%) of the row and 1 Weakened (registry tag 25, G2\'s crossfire drill row). Copy of the resolve '
    'spell 205001 with the Fire school.',
    icon=_ICON_GOUT_OF_FLAME,
)

crossfire_burn_211585 = resolve_copy(
    211585, 'Crossfire', School.FIRE, 'The lane burns.',
    f'{_D22}, MG3: the lane\'s burn: a tick a second for 5 s from 1 s after the ignition, 10% (heroic 15%) of the row '
    'each (registry tag 26, G2\'s crossfire drill row; no Weakened: a lingering zone never applies it). Copy of the '
    'resolve spell 205001 with the Fire school.',
    icon=_ICON_GOUT_OF_FLAME,
)

flame_wall_211586 = resolve_copy(
    211586, 'Flame Wall', School.FIRE, 'A wall of flame burns along the hall.',
    f'{_D22}, MG4: a tick of the Flame Wall strip: 12 yd of floor along one wall (the strip is drawn 8 yd wider on the '
    'wall side, over the alcoves) for 8 s from 3 s after the row glows, 10% (heroic 15%) of the row a second '
    '(registry tag 27, G2\'s Flame Wall drill row). Copy of the resolve spell 205001 with the Fire school.',
    icon=_ICON_GOUT_OF_FLAME,
)

dripping_magma_211587 = resolve_copy(
    211587, 'Dripping Magma', School.FIRE, 'Magma burns the ground.',
    f'{_D22}, MG5 (heroic only): a tick of a pool: 4 yd, a tick a second for 30 s from 1.5 s after it drops, 8% of the '
    'row each (registry tag 2; no Weakened). At most 6 pools stand: a seventh retires the oldest. Copy of the resolve '
    'spell 205001 with the Fire school.',
    icon=_ICON_GOUT_OF_FLAME,
)

# --- looks ------------------------------------------------------------------------------------------------------------

statue_glow_211588 = _state_aura(
    211588, 'Flame Wreath', MG_STATUE_GLOW, GLOW_MS,
    f'{_D22}, MG3 / MG4: a statue (Ironhand Guardian 8982) casts it on itself (triggered) as its pair or row turns, '
    'for the 3 s warning: Flame Wreath 29947\'s SpellVisual 4101 (an Immolate state, flame licks on the statue). The '
    'stock Gout of Flame 15529\'s SV 3640 has only an animation and would show nothing. Look only.',
    _ICON_GOUT_OF_FLAME,
)

statue_breath_211589 = _look_at_point(
    211589, 'Gout of Flame', MG_CROSSFIRE_BREATH,
    f'{_D22}, MG3 / MG4: a statue breathes: it casts it (triggered) at a point: the lane\'s center for a Crossfire '
    '(the pair, so they make a V into the lane), a point down the hall for a Flame Wall (the row). Gout of Flame '
    '15538\'s SpellVisual 3642 (a particle stream from the hand). A one-shot look: the script casts it again every 2 '
    's while the lane or strip burns. The registry owns the damage. Look only.',
    icon=_ICON_GOUT_OF_FLAME,
)

crossfire_end_211590 = _look_at_point(
    211590, 'Flame Jets', MG_CROSSFIRE_END,
    f'{_D22}, MG3: Magmus casts it (triggered) at both ends of the lane as it ignites: Flame Jets 62680\'s SpellVisual '
    '13233 (a fire nova and a lava impact, shake). Look only.',
    icon=_ICON_FLAME_JETS,
)

pool_look_211591 = _state_aura(
    211591, 'Dripping Magma', MG_DRIPPING_MAGMA, -1,
    f'{_D22}, MG5 (heroic): a pool\'s look: a stalker (300796) at the spot casts it on itself as the pool drops and '
    'lives as long as the pool (30 s): the shipped 4 yd lava pool state (SV 90606, Blackrock Spire\'s ladder), under '
    'the registry\'s 4 yd marker. Look only. Fallback: the 8 yd FlameZone (SV 90508).',
    _ICON_GOUT_OF_FLAME,
)
