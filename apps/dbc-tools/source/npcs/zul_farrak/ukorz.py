"""
Zul'Farrak build WP-D6: Chief Ukorz Sandscalp (7267) and Ruuzlu (7797), the Dungeon Finder end
(.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D6, s3.6, s3.8, s7 #10, #34, #41, #42; build spec
docs/dungeons/zul-farrak-rework.md "Chief Ukorz Sandscalp and Ruuzlu", UK1-UK14, Build spec). WP-D6 owns this file.

- 7267: bound to boss_ukorz_rework (modules/mod-dungeon-bosses src/ZulFarrak/boss_ukorz_rework.cpp), 7797 to
  boss_ruuzlu_rework (same file); SmartAI off (rev_skeleton_zul_farrak.sql drops their rows), the normal health of s3.6
  (s7 #1 A: x1.6): Ukorz 143,925 = 75.0 on the level 46 warrior base 1,919, Ruuzlu 128,067 = 69.3 on the level 45 base
  1,848; the stock DamageModifier (until T), stun immunity 1972 (Battle Roar is interruptible), INSTANCE_BIND with both
  assist flags, detection range 12. Heroic health and its overrides are WP-H's (source/world/dungeons/zul_farrak.py).
- 301025 Quicksand (npc_zf_quicksand): the stalker under a pit (UK5, 6 yd) or a Bladestorm trail circle (UK4, 4 yd);
  301026 Creeping Sands (npc_zf_creeping_sands): the heroic donut's anchor at the mesa's middle (UK13, s7 #34 A). Both
  KIT_HELPER (not selectable, not attackable), the invisible stalker display, no heroic copy.
- Texts 7267 4-7 and 7797 0-2 are hand SQL: data/sql/updates/pending_db_world/rev_ukorz_zul_farrak.sql.

Spells (kSpellsUkorz 214070-214109; UkorzLogic.h names the same ids; looks from ._visuals, unconfirmed until seen in
game). Battle Roar is the only kickable cast: Fire, PreventionType 1, InterruptFlags 15 (handoff s3.5 kick table). A
kick locks the caster's Fire school (rule 24), so every bar that must land is Physical and not interruptible: the
stamp, the wind-up, the Execute bar, Call of Sul'thraze, the Lash's bar. Sunk, the quicksand slow and the Lash's debuff
are not dispellable (rule 25: a cure would delete the rescue). Bars cast often carry DO_NOT_RESET_COMBAT_TIMERS (LESSONS
L3: a finished cast resets the swing timer).

  214070  Fury of the Sands      UK1 the meter, +3% damage done a stack, 10 at most (normal)
  214071  Fury of the Sands      UK1 +4% a stack (heroic)
  214072  Fury of the Sands      UK1 the full meter's look, with the yell (Frenzy 3019's SV 578)
  214073  Battle Roar            UK2 2.5 s, kickable, Fire (normal)
  214074  Battle Roar            UK2 2 s (heroic)
  214075  Bladestorm             UK3 the 2 s wind-up bar
  214076  Bladestorm             UK3 the spin's look on the boss
  214077  Bladestorm             UK3 the ring's tick (resolve copy, Physical)
  214078  Sinking Sands          UK5 the stamp's 2 s bar (normal)
  214079  Sinking Sands          UK5 1.5 s (heroic)
  214080  Quicksand              UK5 the pit's look on its stalker
  214081  Quicksand              UK4 the trail's look on its stalker
  214082  Quicksand              UK4, UK5, UK13 the 50% slow rider
  214083  Sunk                   UK6 the root, 8 s
  214084  Execute                UK7 the 4 s bar on the sunk
  214085  Execute                UK7 the hit (the script's base point, Physical)
  214086  Call of Sul'thraze     UK10 the 10 s bar
  214087  Lash of Sul'thraze     UK12 the 2 s bar
  214088  Lash of Sul'thraze     UK12 the mark on the first target
  214089  Lash of Sul'thraze     UK12 a lash (the script's base point, Shadow)
  214090  Sul'thraze's Bite      UK12 15% less of every stat, 15 s
  214091  Creeping Sands         UK13 the donut's tick (resolve copy, Shadow)
  214092  Not Yet                UK9 heroic: the 30% hold's state
  214093  Vengeance              UK9 normal: the survivor's state
  214094-214109 spare.

Kept as cast (ruling 33): Berserker Stance 7366, Cleave 15496, Frenzy 8269. Retired: Execute 38959 on targets under 20%.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
    standing_in_it,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    UK_BLADESTORM,
    UK_CALL,
    UK_EXECUTE,
    UK_FURY,
    UK_LASH,
    UK_PIT,
    UK_ROAR,
    UK_STALKER_DISPLAY,
    UK_STAMP,
    UK_SUNK,
    UK_TRAIL,
)

_D6 = 'Zul\'Farrak build WP-D6 (Chief Ukorz Sandscalp and Ruuzlu)'
_SCRIPT_BP = ('Zul\'Farrak Ukorz: a percent of reference health the script sets as the base point '
              '(DungeonKit::RefFlatOn, the tank row on the tank, owner Ukorz)')

creature_template_columns(7267, **boss_columns(
    'boss_ukorz_rework', 75.0, damage_modifier=2.4,
))

creature_template_columns(7797, **boss_columns(
    'boss_ruuzlu_rework', 69.3, damage_modifier=2.4,
))

# --- constants (UkorzLogic.h namespace Tune; lib/test_zul_farrak_ukorz.py pins each) ----------------------------------

FURY_MAX_STACKS = 10            # kFuryMaxStacks
FURY_PCT = (3, 4)               # kFuryDamagePctPerStack: normal, heroic
ROAR_CAST_MS = (2500, 2000)     # kRoarCastMs
STORM_WINDUP_MS = 2000          # kStormWindupMs
STORM_SPIN_MS = 9000            # the longest spin (kStormRoaredSpinMs; the script cuts it to 6 s / 8 s)
STAMP_CAST_MS = (2000, 1500)    # kStampCastMs
SUNK_MS = 8000                  # kSunkMs (the script holds it to the Execute bar's end)
EXECUTE_CAST_MS = 4000          # kExecuteCastMs
CALL_CAST_MS = 10000            # kCallCastMs
LASH_WARN_MS = 2000             # kLashWarnMs
LASH_DEBUFF_MS = 15000          # kLashDebuffMs
LASH_STAT_PCT = 15              # kLashStatPct
TRAIL_LIFE_MS = 15000           # kTrailLifeMs
QUICKSAND_SLOW_PCT = 50

_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_INTERRUPT_FLAGS_KICKABLE = 15      # movement, pushback, interrupt (the stock war cries have none: FF 2.0)
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_SCHOOL_MASK_ALL = 127
_STAT_ALL = -1                      # MOD_TOTAL_STAT_PERCENTAGE misc value: every stat

# Stock icons (Spell.dbc SpellIconID of the named spell; read from the stock client 2026-11-25)
_ICON_FURY = 95                     # Frenzy 3019
_ICON_ROAR = 86                     # Battle Roar 6507
_ICON_STORM = 83                    # Bladestorm 9632
_ICON_STAMP = 129                   # Ground Stomp 19364
_ICON_SAND = 27                     # the kit's slow icon (Slow 246)
_ICON_SUNK = 20                     # Entangling Roots 339
_ICON_EXECUTE = 1648                # Execute 5308
_ICON_SULTHRAZE = 88                # Sul'thraze 11658
_ICON_CALL = 2667                   # Call of Sul'thraze 11654
_ICON_HOLD = 177                    # Last Stand 12975


def _bar(spell_id: int, name: str, cast_ms: int, desc: str, notes: str, *, icon: int, visual: int = 0,
         target: int = TARGET_UNIT_CASTER, range_yards: float = RANGE_SELF):
    """A named no-effect cast the players read while the script or the registry owns the hit (the kit's cast_bar with
    DO_NOT_RESET_COMBAT_TIMERS, and optionally aimed at a unit): Physical, not interruptible (InterruptFlags 0,
    PreventionType 0), so a kick on Battle Roar (Fire) never locks it."""
    raw = kit_raw(desc, InterruptFlags=0, PreventionType=0, AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                  AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=cast_ms, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=range_yards, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=target)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _script_hit(spell_id: int, name: str, school: School, desc: str, notes: str, *, icon: int, visual: int = 0):
    """A hit whose amount the script sets as the base point (CastSpellExtraArgs::AddSpellBP0; DieSides 0, so the amount
    is exact): triggered, always hits, cannot crit, is not reflected or redirected (LESSONS L7), ignores LoS and the
    caster's modifiers (Fury is the script's factor). Physical ones are reduced by the target's armor."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_BP)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, DefenseType=_DEFENSE_MAGIC,
                              AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG, **({'SpellVisualID_1': visual} if visual else {})),
    )


def _self_state(spell_id: int, name: str, duration_ms: int, desc: str, aura_desc: str, notes: str, *, icon: int,
                visual: int = 0):
    """A DUMMY aura the unit casts (triggered) on itself: a visible state or a look on a stalker. Not dispellable."""
    raw = kit_raw(desc, aura_desc, instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _fury(spell_id: int, pct: int, which: str):
    return spell(
        id=spell_id, name='Fury of the Sands', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=pct,
                        die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_FURY,
        notes=f'{_D6}, UK1 ({which}): the meter on each boss, +{pct}% damage dealt a stack, {FURY_MAX_STACKS} '
              'stacks at most (DungeonKit::AddStacks from the script, which counts a stack per 4% (heroic 3%) of the '
              'partner\'s health lost and takes one off every 4 s (5 s) once the partner lost under 1% in the last 4 '
              's, s7 #41 A). The aura raises his melee and Cleave; the script\'s own hits ignore caster modifiers and '
              'take the same factor from the script. At 5 stacks he roars (UK2), at 10 he Bladestorms (UK3) and the '
              'meter empties. No look (the full meter\'s is 214072). Not dispellable; removed on a wipe and at UK10.',
        raw_overrides=kit_raw('The Sandfury avenge each other.', 'Damage dealt increased by $s1%.', instant=True,
                              CumulativeAura=FURY_MAX_STACKS, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _roar(spell_id: int, cast_ms: int, which: str):
    return spell(
        id=spell_id, name='Battle Roar', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=cast_ms,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_ROAR,
        notes=f'{_D6}, UK2 ({which}): at 5 Fury, once per fill, a {cast_ms / 1000:g} s cast. Kickable: InterruptFlags '
              '15 and PreventionType 1 (a kick or a silence), on the descriptor\'s interrupt list (priority 3) for '
              'both bosses. Landed (CreatureAI::OnSpellCast), the meter fills to 10: an early Bladestorm (heroic: that '
              'spin lasts 9 s). FIRE school, so a kick locks Fire alone and every bar that must land (Physical, not '
              'interruptible) stays castable (rule 24). No effect of its own. Battle Roar 6507\'s SV 246.',
        raw_overrides=kit_raw('Roars to fill the Sandfury\'s fury.', SpellVisualID_1=UK_ROAR,
                              InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- UK1 Fury of the Sands, UK2 Battle Roar ---------------------------------------------------------------------------

fury_214070 = _fury(214070, FURY_PCT[0], 'normal')
fury_heroic_214071 = _fury(214071, FURY_PCT[1], 'heroic')

fury_full_214072 = self_visual(
    214072, 'Fury of the Sands', UK_FURY,
    f'{_D6}, UK1 and UK3: the full meter\'s look, cast (triggered) on himself with the yell as the Bladestorm\'s '
    'wind-up starts: Frenzy 3019\'s SV 578. Look only.',
    icon=_ICON_FURY,
)

roar_214073 = _roar(214073, ROAR_CAST_MS[0], 'normal')
roar_heroic_214074 = _roar(214074, ROAR_CAST_MS[1], 'heroic')

# --- UK3 Bladestorm, UK4 the trail ------------------------------------------------------------------------------------

storm_windup_214075 = _bar(
    214075, 'Bladestorm', STORM_WINDUP_MS, 'Raises his blade. Get away from him.',
    f'{_D6}, UK3: the 2 s wind-up after the yell (Ukorz line 4, Ruuzlu line 0); the registry\'s 8 yd ring on him (tag '
    '1) goes live as it ends. Not interruptible; Physical (rule 24).',
    icon=_ICON_STORM,
)

storm_spin_214076 = spell(
    id=214076, name='Bladestorm', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=STORM_SPIN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_STORM,
    notes=f'{_D6}, UK3: the spin\'s look, a DUMMY aura the boss casts (triggered) on himself as the wind-up ends: 9 s, '
          'cut by the script to the spin (6 s normal, 8 s heroic, 9 s after a heroic roar). The minted SpellVisual '
          '90703 (the shipped blades, anim 126); fallback Bladestorm 6044. He walks at 5 yd/s at a new player every '
          '2 s meanwhile; the ring marker carries the radius.',
    raw_overrides=kit_raw('Spins with his blade out.', 'Spinning.', instant=True, SpellVisualID_1=UK_BLADESTORM,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

storm_214077 = resolve_copy(
    214077, 'Bladestorm', School.NORMAL, 'Caught in the Sandfury\'s Bladestorm.',
    f'{_D6}, UK3: the ring\'s tick, once a second for the spin on everyone within 8 yd of the walking boss, the tank '
    'included: 12% (heroic 15%) of the reference row (the tank row on the tank). Damage over time, so no Weakened '
    '(registry tag 1). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_STORM,
)

# --- UK5 Sinking Sands, UK4 / UK5 / UK13 the quicksand, UK6 Sunk ------------------------------------------------------

stamp_214078 = _bar(
    214078, 'Sinking Sands', STAMP_CAST_MS[0], 'Stamps, and the sand opens.',
    f'{_D6}, UK5 (normal): the stamp\'s 2 s bar (emote line 7, at most once every 10 s); the 6 yd pit under one random '
    'player (registry tag 3) resolves as it ends. Ground Slam\'s SV 8083 (the stamp); not interruptible, Physical.',
    icon=_ICON_STAMP, visual=UK_STAMP,
)

stamp_heroic_214079 = _bar(
    214079, 'Sinking Sands', STAMP_CAST_MS[1], 'Stamps, and the sand opens.',
    f'{_D6}, UK5 (heroic, phase 3): the stamp\'s 1.5 s bar; two pits under two random players. Ground Slam\'s SV '
    '8083; not interruptible, Physical.',
    icon=_ICON_STAMP, visual=UK_STAMP,
)

pit_look_214080 = _self_state(
    214080, 'Quicksand', -1, 'Quicksand.', 'Quicksand.',
    f'{_D6}, UK5: the pit\'s look, cast (triggered) by its stalker 301025 on itself as the pit opens: the minted '
    'SpellVisual 90700 (Ascension sand trap at scale 1.1, about 12 yd across); fallback stock Sand Storm 7437 plus the '
    'marker. Lasts until the stalker despawns (30 s, or the fight after a normal Frenzy).',
    icon=_ICON_SAND, visual=UK_PIT,
)

trail_look_214081 = _self_state(
    214081, 'Quicksand', TRAIL_LIFE_MS + 1000, 'Quicksand.', 'Quicksand.',
    f'{_D6}, UK4 (heroic): the trail\'s look, cast (triggered) by a trail stalker 301025 on itself: the minted '
    'SpellVisual 90701 (the same sand trap at scale 0.73, about 8 yd across); fallback the marker alone. 15 s.',
    icon=_ICON_SAND, visual=UK_TRAIL,
)

quicksand_214082 = standing_in_it(
    214082,
    f'{_D6}, UK4, UK5 and UK13: the quicksand\'s slow, re-applied by every tick of a pit (6 yd, 30 s), a trail circle '
    '(4 yd, 15 s) or the Creeping Sands donut: 50% slower, ending shortly after the player steps out. No damage of its '
    'own (the donut\'s tick is 214091), no Weakened.',
    name='Quicksand', slow_pct=QUICKSAND_SLOW_PCT, desc='Quicksand drags at your legs. Lasts $d.',
    aura_desc='Movement speed reduced by 50%.', icon=_ICON_SAND,
)

sunk_214083 = spell(
    id=214083, name='Sunk', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=SUNK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SUNK,
    notes=f'{_D6}, UK6: anyone inside a pit as it resolves sinks: rooted for 8 s (they can still cast and attack). '
          'Another player standing within 3 yd of them for 2 s pulls them out (DungeonKit::DwellSoaks, registry tag 5) '
          'and the script removes it. Ruuzlu (Ukorz once Ruuzlu is gone) walks over and casts the 4 s Execute bar '
          '(214084); the script holds the root until the bar ends. Mechanic none and not dispellable (rule 25: the '
          'rescue is the answer; no freedom effect breaks it); lands through immunities; dropped on a map change. Sand '
          'Storm 7437 (the alternate Entangling Roots 38).',
    raw_overrides=kit_raw('Sinking into the sand.',
                          'Sunk in the sand. Another player must stand on you to pull you out.', instant=True,
                          SpellVisualID_1=UK_SUNK, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- UK7 Execute of the sunk ------------------------------------------------------------------------------------------

execute_bar_214084 = _bar(
    214084, 'Execute', EXECUTE_CAST_MS, 'Raises his axe over the sunk.',
    f'{_D6}, UK7: the 4 s bar the executioner casts on a sunk player once he reaches them (5 yd). Landed '
    '(CreatureAI::OnSpellCast), the script deals 214085; a rescue stops it (the script\'s own interrupt). Not '
    'interruptible, Physical (rule 24: never locked by a kick on Battle Roar). Execute 38959\'s SV 250.',
    icon=_ICON_EXECUTE, visual=UK_EXECUTE, target=TARGET_UNIT_TARGET_ANY, range_yards=10.0,
)

execute_214085 = _script_hit(
    214085, 'Execute', School.NORMAL, 'Executes a sunk outsider.',
    f'{_D6}, UK7: the Execute on a sunk player nobody came back for: 50% (heroic 75%) of the reference row (the tank '
    'row on the tank), times the executioner\'s Fury factor in phase 1. A rescue failure, so no Weakened. Execute '
    '38959\'s SV 250.',
    icon=_ICON_EXECUTE, visual=UK_EXECUTE,
)

# --- UK10 Call of Sul'thraze, UK12 Lash of Sul'thraze, UK13 Creeping Sands (heroic) ----------------------------------

call_214086 = _bar(
    214086, 'Call of Sul\'thraze', CALL_CAST_MS, 'Joins the twin blade.',
    f'{_D6}, UK10 (heroic): Ruuzlu throws Sang\'thraze to his chief and falls (Ruuzlu line 2), Ukorz takes his '
    'remaining health and casts this 10 s bar (Ukorz line 6). Visual only, not interruptible, Physical; he takes '
    'damage freely meanwhile. A pit opens under every player (UK11) and the Creeping Sands donut forms (UK13). '
    'Landed, phase 3 starts (his Frenzy). Call of Sul\'thraze 11654\'s look (the minted pick SV 14508, alternate 76).',
    icon=_ICON_CALL, visual=UK_CALL,
)

lash_bar_214087 = _bar(
    214087, 'Lash of Sul\'thraze', LASH_WARN_MS, 'The blade glows.',
    f'{_D6}, UK12 (heroic phase 3): the 2 s warning: the blade glows on Ukorz while the mark (214088) sits on a random '
    'player, the tank included; the registry Spread of 8 yd (tag 6) tells the bots to part. Not interruptible, '
    'Physical (phase 3 has no interrupt, on purpose). Sul\'thraze 11658\'s SV 2357.',
    icon=_ICON_SULTHRAZE, visual=UK_LASH,
)

lash_mark_214088 = spell(
    id=214088, name='Lash of Sul\'thraze', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=LASH_WARN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SULTHRAZE,
    notes=f'{_D6}, UK12: the mark on the lash\'s first target for its 2 s warning. DUMMY, not dispellable, dropped '
          'on a map change.',
    raw_overrides=kit_raw('Marked by Sul\'thraze.', 'The Lash strikes you first. Stand 8 yards from everyone.',
                          instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

lash_214089 = _script_hit(
    214089, 'Lash of Sul\'thraze', School.SHADOW, 'The Lash of Sul\'thraze.',
    f'{_D6}, UK12: a lash, on the marked player and then on every other player within 8 yd of a struck one (4 jumps at '
    'most): 25% of the reference row (the tank row on the tank). A spread failure, so no Weakened. Sul\'thraze '
    '11658\'s SV 2357.',
    icon=_ICON_SULTHRAZE, visual=UK_LASH,
)

lash_debuff_214090 = spell(
    id=214090, name='Sul\'thraze\'s Bite', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=LASH_DEBUFF_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_TOTAL_STAT_PERCENTAGE,
                    base_points=-LASH_STAT_PCT, die_sides=0, misc_value=_STAT_ALL,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SULTHRAZE,
    notes=f'{_D6}, UK12: the blade\'s own debuff on everyone the lash strikes: 15% less of every stat for 15 s (the '
          'Lasher\'s stat theft, Sul\'thraze 11658\'s look by the hit). Not dispellable (s3.5 kick and dispel table); '
          'a new lash refreshes it; dropped on a map change.',
    raw_overrides=kit_raw('Sul\'thraze drinks your strength.', 'All stats reduced by 15%.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

creeping_214091 = resolve_copy(
    214091, 'Creeping Sands', School.SHADOW, 'The sands rise.',
    f'{_D6}, UK13 (heroic): the donut\'s tick, once a second on everyone in the quicksand round the mesa\'s middle '
    '(1736.2, 1033.2; s7 #34 A): 8% of the reference row (the tank row on the tank), with the 50% slow (214082). The '
    'safe circle is 30 yd at the Call and closes 5 yd every 20 s of phase 3 to nothing (ruling 45: the enrage, no '
    'floor, uncapped at 60). Lingering, so no Weakened (registry tag 7). Copy of the resolve spell 205006 (Shadow).',
    icon=_ICON_SAND,
)

# --- UK9 the states ---------------------------------------------------------------------------------------------------

held_214092 = _self_state(
    214092, 'Not Yet', -1, 'Holds on until the other is ready.', 'Holding on. Bring the other down too.',
    f'{_D6}, UK9 (heroic): the 30% hold\'s state on a boss at the line (Ukorz line 5, Ruuzlu line 1); the script keeps '
    'him there (no damage gets through) until both are at 30%, then the Call (UK10) removes it. No look.',
    icon=_ICON_HOLD,
)

vengeance_214093 = _self_state(
    214093, 'Vengeance', -1, 'Avenges the fallen.', 'Fury fills every 3 sec and never fades.',
    f'{_D6}, UK9 (normal): the survivor\'s state once the other is down: his Fury no longer fades and fills a stack '
    'every 3 s (a Bladestorm every 30 s). No look.',
    icon=_ICON_FURY,
)

# --- the stalkers -----------------------------------------------------------------------------------------------------

quicksand_301025 = creature_template(
    301025, 'Quicksand', **{**KIT_HELPER, 'minlevel': 46, 'maxlevel': 46, 'rank': 0, 'unit_class': 1,
                            'ScriptName': 'npc_zf_quicksand'},
)
creature_model(301025, display_id=UK_STALKER_DISPLAY, scale=1.0)

creeping_sands_301026 = creature_template(
    301026, 'Creeping Sands', **{**KIT_HELPER, 'minlevel': 46, 'maxlevel': 46, 'rank': 0, 'unit_class': 1,
                                 'ScriptName': 'npc_zf_creeping_sands'},
)
creature_model(301026, display_id=UK_STALKER_DISPLAY, scale=1.0)
