"""
Zul'Farrak build WP-D1: Theka the Martyr (7272) (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row
D1, s3.6, s3.8, s3.10, s7 #21, #22, #27; build spec docs/dungeons/zul-farrak-rework.md "Theka the Martyr", TK1-TK9,
rulings 10 to 12, 25, 45). WP-D1 owns this file (its spells: kSpellsTheka 213860-213889 of modules/mod-dungeon-bosses
src/ZulFarrak/ZulFarrakRework.h only; ThekaLogic.h names the same ids and holds every number; the texts and the stopped
patrol are the core SQL rev rev_theka_zul_farrak.sql).

- 7272 Theka the Martyr: boss_theka_rework (SmartAI off: rev_skeleton_zul_farrak.sql drops his rows, Fevered Plague
  8600 and Theka Transform 11089), the normal health of s3.6 (175,973 = HealthModifier 91.7 on the level 46 warrior
  base 1,919, s7 #1 A), the stock DamageModifier 2.4, stun immunity 1972 (no interrupt or silence immunity, so the
  plague can be kicked; it holds root immunity, so his hold under the swarm is the script's), INSTANCE_BIND with both
  assist flags, detection range 12. Heroic 373,260 is WP-H's override (source/world/dungeons/zul_farrak.py).
- 301005 Persecutor Swarm (TK1, TK2) and 301006 Penitent Swarm (TK6, TK7): npc_zf_persecutor_swarm and
  npc_zf_penitent_swarm, the stock Scarab's model (display 7470) at object scale 1.3 wearing the swarm cloud 213870,
  not selectable, not attackable (the swarms cannot be fought, designer 2026-11-22); Theka's script moves them. No
  heroic templates. Display 7470's creature_model_info row is stock (bounding 0.15, reach 0.45; SELECT 2026-11-25).
- 301007 (the stalker of the stub's list) is not declared: the swarms cast their own bursts. Spare.

Spells. The registry's hits are dungeon copies of the mod-boss-mechanics resolve spell; the plague's values are the
kit's generic percent scripts (spell_dungeon_refflat_damage, spell_dungeon_refflat_periodic: hundredths of a percent of
the reference row, the tank row on a tank); every damage spell ignores the caster's modifiers (rule 2):

  213860  Persecutors' Bite     TK1 the swarm body's hit: resolve copy, Nature, 30% / 45% and Weakened
  213861  Devouring Swarm       TK2 the 6 yd circle on him at the arrival: resolve copy, Nature, 40% / 60% and Weakened
  213862  Hallowed Suffering    TK3 his stacking buff (no effect; the script counts it), CumulativeAura 99
  213863  Fevered Plague        TK4 normal: 4 s kickable Nature cast, 10% and 15% over 12 s, Disease
  213864  Fevered Plague        TK4 heroic: 2 s kickable Nature cast, 20% and 40% over 10 s, Disease (it spreads)
  213865  Fevered Plague        TK4 heroic: the copy the spread gives, 40% over 10 s, Disease (never spreads)
  213866  Fevered Plague        TK4 the lasting look on a carrier (hidden aura, SV 14987)
  213867  Martyr's Rising       TK5 the flash (SV 4341)
  213868  Penitent Eruption     TK7 the 5 yd circle where a hunt stopped: resolve copy, Nature, 30% / 45% and Weakened
  213869  Martyr's Lament       TK8 heroic: a Holy hit of the script's amount (1.5% a stack)
  213870  Persecutor Swarm      the swarms' cloud (hidden aura, SV 10986)
  213871  Persecutor Swarm      TK1 the rise burst at a point (SV 7443)
  213872  Penitent Eruption     TK7 the burst where a hunt stopped (SV 7443)
  213873  Persecutors' Swarm    TK2 the swarm boiling on him for 2.5 s (SV 7620)
  213874  Burrowing             TK6 the Penitent Swarm's trail while it hunts (hidden aura, SV 14013)
  213875-213889 spare.

Retired as casts: Fevered Plague 8600 and Theka Transform 11089. Looks are copies (s3.10: SV 8325, 7621 and 11778 are
never wired). He casts one kickable spell, Nature; nothing that must land is a non-triggered Nature cast (rule 24).
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
    TARGET_UNIT_TARGET_ENEMY,
)
from lib.dsl.registry import (
    creature_model,
    creature_template,
    creature_template_columns,
    scripted_by,
    spell,
)

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
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
    DISPLAY_SWARM,
    SWARM_SCALE_RANGE,
    TK_HUNT_ERUPTION,
    TK_HUNT_TRAIL,
    TK_PLAGUE_CAST,
    TK_PLAGUE_SPREAD,
    TK_PLAGUE_STATE,
    TK_RISE_BURST,
    TK_RISING,
    TK_SWARM_AURA,
    TK_SWARM_ON_THEKA,
)

_D1 = "Zul'Farrak build WP-D1 (Theka the Martyr)"

# --- constants (ThekaLogic.h; lib/test_zul_farrak_theka.py pins each against the header) -----------------------------

SWARM_SCALE = 1.3                   # kSwarmScale: the low end of SWARM_SCALE_RANGE
assert SWARM_SCALE_RANGE[0] <= SWARM_SCALE <= SWARM_SCALE_RANGE[1]
HALLOWED_MAX_STACKS = 99            # Tune::kStackCapHeroic (normal's cap 5 is the script's)
PLAGUE_CAST_MS = (4000, 2000)       # Tune::kPlagueCastMs
PLAGUE_MS = (12000, 10000)          # Tune::kPlagueMs
PLAGUE_TICK_MS = (3000, 2000)       # Tune::kPlagueTickMs
PLAGUE_HIT = (1000, 2000)           # Tune::kPlagueHitPct 10 / 20, in hundredths
PLAGUE_TICK = (375, 800)            # PlagueTickHundredths: 15% over 4 ticks, 40% over 5
HOLD_MS = 2500                      # Tune::kHoldMs: the swarm boils on him

_SCRIPT_REFFLAT = ("Zul'Farrak Theka: a percent of reference health in hundredths, set by the kit's "
                   'spell_dungeon_refflat_damage / spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn: the tank '
                   'row on a tank)')
_SCRIPT_BP = ("Zul'Farrak Theka: the script's base point (a percent of reference health, DungeonKit::RefFlatOn, "
              'times his Hallowed Suffering stacks)')

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_DEFENSE_MAGIC = 1
_DISPEL_DISEASE = 3
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15              # the whitemane.py / jergosh.py recipe
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000  # SharedDefines.h: the cast leaves his swing timer alone
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_TYPE_BEAST = 1

# Stock icons (Spell.dbc SpellIconID of the named spell, read from the stock DBC 2026-11-25)
_ICON_FEVERED_PLAGUE = 264          # Fevered Plague 8600
_ICON_THEKA_TRANSFORM = 207         # Theka Transform 11089
_ICON_LOCUST_SWARM = 1771           # Locust Swarm 28785
_ICON_CRYPT_SCARABS = 116           # Crypt Scarabs 31600
_ICON_CARRION_BEETLES = 1932        # Carrion Beetles 53520
_ICON_BURROW = 252                  # Burrow 26381

# --- the creatures ---------------------------------------------------------------------------------------------------

creature_template_columns(7272, **boss_columns(
    'boss_theka_rework', 91.7, damage_modifier=2.4,
))

persecutor_swarm_301005 = creature_template(301005, 'Persecutor Swarm', **{
    **KIT_HELPER, 'minlevel': 46, 'maxlevel': 46, 'rank': 0, 'unit_class': 1, 'type': _TYPE_BEAST,
    'ScriptName': 'npc_zf_persecutor_swarm',
})
creature_model(301005, display_id=DISPLAY_SWARM, scale=SWARM_SCALE)

penitent_swarm_301006 = creature_template(301006, 'Penitent Swarm', **{
    **KIT_HELPER, 'minlevel': 46, 'maxlevel': 46, 'rank': 0, 'unit_class': 1, 'type': _TYPE_BEAST,
    'ScriptName': 'npc_zf_penitent_swarm',
})
creature_model(301006, display_id=DISPLAY_SWARM, scale=SWARM_SCALE)


# --- helpers ---------------------------------------------------------------------------------------------------------

def _look_at_point(*, spell_id: int, name: str, visual: int, notes: str, icon: int):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), triggered: the
    cast kit on the caster, the area kit at the point (the Oggleflint eruption look's shape)."""
    return spell(
        id=spell_id, name=name, school=School.NATURE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _state(*, spell_id: int, name: str, visual: int, notes: str, icon: int, duration_ms: int = -1,
           hidden: bool = True, target: int = TARGET_UNIT_CASTER, desc: str = '', aura_desc: str = ''):
    """A look-only DUMMY aura (the state kit of `visual` on its bearer), not dispellable; `hidden` keeps it off the
    aura bar (DO_NOT_DISPLAY)."""
    return spell(
        id=spell_id, name=name, school=School.NATURE, dispel=0, mechanic=0,
        attributes=(ATTR0_DO_NOT_DISPLAY if hidden else 0), cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=(RANGE_SELF if target == TARGET_UNIT_CASTER else 100.0),
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=target)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


def _plague(*, spell_id: int, heroic: bool, notes: str):
    """TK4 Fevered Plague: a kickable Nature cast (InterruptFlags 15, silence), a direct hit and a DoT, a Disease."""
    i = 1 if heroic else 0
    s = spell(
        id=spell_id, name='Fevered Plague', school=School.NATURE, dispel=_DISPEL_DISEASE, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=PLAGUE_CAST_MS[i], cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=PLAGUE_MS[i],
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=PLAGUE_HIT[i] - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
                 Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                        base_points=PLAGUE_TICK[i] - 1, die_sides=1, amplitude=PLAGUE_TICK_MS[i],
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
        spell_icon_id=_ICON_FEVERED_PLAGUE, notes=notes,
        raw_overrides=kit_raw('Inflicts Nature damage, then more every $t2 sec. for $d.',
                              'Nature damage every $t2 sec.',
                              InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                              DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=TK_PLAGUE_CAST,
                              AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                              AttributesEx2=(ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT
                                             | _ATTR2_DO_NOT_RESET_COMBAT_TIMERS),
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )
    scripted_by(s, 'spell_dungeon_refflat_damage', 'spell_dungeon_refflat_periodic')
    return s


# --- TK1 Persecutors' Swarm, TK2 the arrival, TK3 Hallowed Suffering -------------------------------------------------

persecutors_bite_213860 = resolve_copy(
    213860, "Persecutors' Bite", School.NATURE, 'The swarm gnaws everything in its path.',
    f'{_D1}, TK1: the swarm body\'s 4 yd line (a registry Line with Projectile + ProjectileUnit on the swarm, 4 yd/s, '
    'heroic 5): 30% (heroic 45%) of the reference row and 1 Weakened on whoever it passes over, the tank row on the '
    'tank (registry tags 4 / 1, a turn 2). Copy of the resolve spell 205001 (Nature).',
    icon=_ICON_LOCUST_SWARM,
)

devouring_swarm_213861 = resolve_copy(
    213861, 'Devouring Swarm', School.NATURE, 'The persecutors swarm over Theka and everyone beside him.',
    f'{_D1}, TK2: the 6 yd circle on Theka drawn 2.5 s before a swarm lands on him: 40% (heroic 60%) of the reference '
    'row and 1 Weakened on both difficulties (ruling 25), the tank included, the tank row on the tank (registry tags '
    '5 / 3). Copy of the resolve spell 205001 (Nature).',
    icon=_ICON_LOCUST_SWARM,
)

hallowed_suffering_213862 = spell(
    id=213862, name='Hallowed Suffering', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_THEKA_TRANSFORM,
    notes=f'{_D1}, TK3: a stack for every swarm that reaches him (the script sets the count: normal cap 5, heroic '
          'none, ruling 45; CumulativeAura 99 is out of reach at a pair every 20 s). No effect in phase 1; at 30% '
          'the stacks set the Penitent Swarms (TK6) and, heroic, the Lament (TK8). Not dispellable, not stealable; '
          'gone on his reset, evade or death.',
    raw_overrides=kit_raw('Sanctified by his persecutors\' bites.', 'Sanctified by his persecutors\' bites.',
                          instant=True, CumulativeAura=HALLOWED_MAX_STACKS, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- TK4 Fevered Plague ----------------------------------------------------------------------------------------------

fevered_plague_213863 = _plague(spell_id=213863, heroic=False, notes=(
    f'{_D1}, TK4 normal: at 8 s, then every 12 to 16 s in both phases, a 4 s cast on a random player within 30 yd '
    '(the script picks; the row\'s range 100 keeps a target that walks off), the tank included: 10% of the reference '
    'row, then 15% over 12 s (4 ticks of 375 hundredths), the tank row on a tank. Interruptible and silence-'
    'preventable (his immunity set 1972 holds neither): the fight\'s kick (the descriptor\'s interrupt list). A '
    'Disease: a cure is the reward. Does not reset his swing; dropped on a map change; removed from everyone on his '
    'reset, evade or death. Fevered Plague 8600\'s SV 1004 (cast and burst).'))

fevered_plague_heroic_213864 = _plague(spell_id=213864, heroic=True, notes=(
    f'{_D1}, TK4 heroic: as 213863 with a 2 s cast, 20% and 40% over 10 s (5 ticks of 800 hundredths). While it '
    'lasts the script gives a copy (213865) every 2 s to anyone within 6 yd of the carrier (a registry RunOut 6 yd on '
    'the carrier, tag 43, telegraph only); a cure stops it.'))

fevered_plague_spread_213865 = spell(
    id=213865, name='Fevered Plague', school=School.NATURE, dispel=_DISPEL_DISEASE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=PLAGUE_MS[1],
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=PLAGUE_TICK[1] - 1,
                    die_sides=1, amplitude=PLAGUE_TICK_MS[1], implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_FEVERED_PLAGUE,
    notes=f'{_D1}, TK4 heroic: the copy the spread gives (cast by Theka, triggered): 40% over 10 s (5 ticks of 800 '
          'hundredths), the tank row on a tank; a new copy refreshes an old one. Copies never spread. A Disease (a '
          'reward). Wandering Plague\'s impact SV 3138.',
    raw_overrides=kit_raw('Nature damage every $t1 sec. for $d.', 'Nature damage every $t1 sec.',
                          CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=TK_PLAGUE_SPREAD,
                          AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(fevered_plague_spread_213865, 'spell_dungeon_refflat_periodic')

fevered_plague_look_213866 = _state(
    spell_id=213866, name='Fevered Plague', visual=TK_PLAGUE_STATE, icon=_ICON_FEVERED_PLAGUE,
    duration_ms=PLAGUE_MS[0], target=TARGET_UNIT_TARGET_ANY,
    notes=f'{_D1}, TK4: the plague\'s lasting look on its carrier (Corrosion\'s state SV 14987; the plague\'s own SV '
          '1004 is a one-shot), cast by Theka (triggered) as the plague lands, removed by the script as soon as the '
          'plague is gone (a cure). Hidden, not dispellable, no effect.',
)

# --- TK5 Martyr's Rising ---------------------------------------------------------------------------------------------

martyrs_rising_213867 = spell(
    id=213867, name="Martyr's Rising", school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_THEKA_TRANSFORM,
    notes=f'{_D1}, TK5: the flash of his rising at 30% (cast on himself, triggered; the script roots him 2 s, then '
          'sets display 6697 at object scale 1: the model\'s own 1.2 is in CreatureDisplayInfo). No immunity (Theka '
          'Transform 11089\'s school immunity is retired). Dark Martyrdom 70897\'s SV 4341. Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=TK_RISING, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- TK6 / TK7 Penitent Hunt, TK8 Martyr's Lament --------------------------------------------------------------------

penitent_eruption_213868 = resolve_copy(
    213868, 'Penitent Eruption', School.NATURE, 'A penitent swarm bursts out of the sand.',
    f'{_D1}, TK7: the 5 yd circle where a Penitent Swarm stopped after its 5 s chase, 1.5 s: 30% (heroic 45%) of the '
    'reference row and 1 Weakened, the tank included, the tank row on the tank (registry tag 42). Copy of the '
    'resolve spell 205001 (Nature).',
    icon=_ICON_CARRION_BEETLES,
)

martyrs_lament_213869 = spell(
    id=213869, name="Martyr's Lament", school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_BP)],
    spell_icon_id=_ICON_THEKA_TRANSFORM,
    notes=f'{_D1}, TK8 (heroic, phase 2): every 3 s, cast by Theka (triggered) on everyone in his fight: 1.5% of the '
          'reference row a Hallowed Suffering stack (the script\'s base point, the tank row on a tank; no cap, ruling '
          '45). Holy, always hits, cannot crit, ignores line of sight and his modifiers. Healer work.',
    raw_overrides=kit_raw('The martyr\'s lament burns everyone near him.', instant=True, InterruptFlags=0,
                          PreventionType=0, DefenseType=_DEFENSE_MAGIC,
                          AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- the looks -------------------------------------------------------------------------------------------------------

swarm_cloud_213870 = _state(
    spell_id=213870, name='Persecutor Swarm', visual=TK_SWARM_AURA, icon=_ICON_CRYPT_SCARABS,
    notes=f'{_D1}: the swarms\' cloud, on both swarms (cast on itself, triggered) for their life: Honey Touched '
          '49750\'s SV 10986 (the swarm model at a tenth, 4.3 x 4.7 x 1.9 yd at scale 1; never SV 8325). Hidden. '
          'Look only.',
)

rise_burst_213871 = _look_at_point(
    spell_id=213871, name='Persecutor Swarm', visual=TK_RISE_BURST, icon=_ICON_BURROW,
    notes=f'{_D1}, TK1: the 2 s rise\'s burst, cast by the swarm (triggered) at its own spot as it rises, and again '
          'where it sinks: SV 7443 (BurrowEarth_Brown_Missile area kit; the stock aims its spells at a destination '
          'too). Look only.',
)

eruption_look_213872 = _look_at_point(
    spell_id=213872, name='Penitent Eruption', visual=TK_HUNT_ERUPTION, icon=_ICON_CARRION_BEETLES,
    notes=f'{_D1}, TK7: the burst where a Penitent Swarm stopped, cast by it (triggered) as the circle lands: SV 7443 '
          '(SV 11778 has no model and is never wired). Look only.',
)

swarm_on_theka_213873 = _state(
    spell_id=213873, name="Persecutors' Swarm", visual=TK_SWARM_ON_THEKA, icon=_ICON_LOCUST_SWARM,
    duration_ms=HOLD_MS, hidden=False, desc='The persecutors swarm over Theka.',
    aura_desc='Held in place by his persecutors.',
    notes=f'{_D1}, TK2: the swarm boiling on him for 2.5 s after it lands (cast on himself, triggered), shown on his '
          'aura bar while the script holds him in place (rooted by the script: 1972 holds root immunity). Locust '
          'Swarm 28786\'s chest state SV 7620 (never SV 7621). No effect.',
)

hunt_trail_213874 = _state(
    spell_id=213874, name='Burrowing', visual=TK_HUNT_TRAIL, icon=_ICON_BURROW,
    notes=f'{_D1}, TK6: a Penitent Swarm\'s trail while it hunts (cast on itself, triggered; the script removes it '
          'when the chase stops): Pursuing Spikes 65921\'s SV 14013. Hidden. Look only.',
)
