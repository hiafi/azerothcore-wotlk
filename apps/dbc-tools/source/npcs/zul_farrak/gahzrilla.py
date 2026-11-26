"""
Zul'Farrak build WP-D7: Hydromancer Velratha (7795) and Gahz'rilla (7273), the optional encounter at the sacred pool
(.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D7, s3.6, s3.8, s7 #35-#40, s10 #40 B; build spec
docs/dungeons/zul-farrak-rework.md "Hydromancer Velratha and Gahz'rilla", GZ1-GZ14). WP-D7 owns this file (its spells:
kSpellsPool 214110-214149 of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h only; GahzrillaLogic.h names
the same ids; the texts and the stopped patrol are the core SQL rev rev_gahzrilla_zul_farrak.sql).

- 7795 boss_velratha_rework: SmartAI off (rev_skeleton_zul_farrak.sql drops its rows), normal health 112,007 = 83.4 on
  the level 46 mage base 1,343 (s3.6, s7 #1 A), the stock DamageModifier, immunity 1972, INSTANCE_BIND with both
  assist flags, detection 12. Hard mode 200,000 is set by the script at her pull. Heroic: WP-H's override.
- 7273 boss_gahzrilla_rework: the same columns, 208,020 = 108.4 on the level 46 warrior base 1,919, and MovementType 0
  (stock 1: the script moves him; he is summoned, never spawned). Hard mode 500,000 by the script as he comes ashore.
- 301030 the sacred pool's stalker (npc_zf_puddle): KIT_HELPER (not selectable, not attackable, no XP) wearing the
  invisible stalker display 11686, passive. One of them, summoned at the pool's middle at Velratha's pull, holds the
  encounter (the water field and its clocks); the others are KT's WaterField discs (the field sets the disc display
  90830-90832 and its scale = radius / 4.8). No trigger flag: a trigger creature is invisible to players, and the disc
  must show. No heroic template (stalkers run on their normal entry).

Spells. Every damage spell takes the script's base point (DieSides 0, so the amount is exact) and ignores the caster's
modifiers; the hits are never reflected or redirected (rule 2, LESSONS L7):

  214110  Spill the Pool        GZ1 normal: the 4 s Arcane bar (s10 #40 B), not kickable
  214111  Spill the Pool        GZ1 heroic: the 3 s bar
  214112  Spill the Pool        GZ1 the marked player's debuff (the look, as long as the bar)
  214113  Static Charge         GZ3 his meter, 10 stacks at the bar
  214114  Static Discharge      GZ3 the 3 s Nature bar, not kickable
  214115  Static Discharge      GZ3 the hit (Nature)
  214116  Static Shock          GZ3 the 2 s stun of anyone in water when it lands
  214117  Call the Waters       GZ5 normal: the kickable 2.5 s Arcane cast
  214118  Call the Waters       GZ5 heroic: 2 s
  214119  Icicle                GZ6 copy of 11131: 2.5 s (s10), Frost, the 51% slow, NOT interruptible
  214120  Freeze Solid          GZ7 copy of 11836: 2.5 s, a 2 s stun (Magic), NOT interruptible
  214121  Freeze                GZ8 the burst on a frozen puddle's disc (look)
  214122  Gahz'rilla Slam       GZ11 copy of 11902 without the knock up: 50% weapon damage within 20 yd
  214123  Healing Wave          GZ9 normal: Velratha's kickable 3 s self-heal
  214124  Healing Wave          GZ9 heroic: 2 s
  214125  Acid Spit             GZ11 his swing at a target out of reach (Nature)
  214126  Charged               GZ12 heroic: the personal stacks, no cap
  214127  Conductive            GZ14 heroic: Magic, 10 s (dispel list)
  214128  Conductive            GZ14 the arcs and the sheet's shock (Nature)
  214129  Gong Strike           GZ10 the look of her strike (Tidal Charm's)
  214130-214149 spare.

Kicks and schools (s3.5 kick table, rule 24): Velratha's kickable casts are Frostbolt (Frost, stock) and Healing Wave
(Nature); her must-land Spill bar is Arcane. Gahz'rilla's only kickable cast is Call the Waters (Arcane); his Discharge
bar is Nature, Icicle and Freeze Solid are Frost copies with no interrupt flags (any kick would delete the group's own
freeze). Kept as cast: Frostbolt 10180 (stock). Retired as casts: Healing Wave 12491, Icicle 11131, Freeze Solid 11836,
Gahz'rilla Slam 11902 (the copies above). Looks are copied from V's _visuals.py, never the stock spells.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_IS_ABILITY,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
)
from ._visuals import (
    AS_HEAL,
    DISPLAY_INVISIBLE_STALKER,
    GZ_ACID_SPIT,
    GZ_CONDUCTIVE,
    GZ_DISCHARGE,
    GZ_FREEZE_EVENT,
    GZ_FREEZE_SOLID,
    GZ_ICICLE,
    GZ_ICE_DISC,
    GZ_SLAM,
    GZ_STATIC_CHARGE,
    GZ_STORM_DISC,
    GZ_TIDAL_CHARM,
    GZ_WATER_DISC,
)

creature_template_columns(7795, **boss_columns(
    'boss_velratha_rework', 83.4, damage_modifier=2.4,
))

creature_template_columns(7273, **boss_columns(
    'boss_gahzrilla_rework', 108.4, damage_modifier=3.5, MovementType=0,
))

_D7 = "Zul'Farrak build WP-D7 (Velratha and Gahz'rilla)"
_SCRIPT_BP = ("Zul'Farrak pool: the script's base point (a percent of reference health, DungeonKit::RefFlatOn with the "
              "boss as the owner; normal Icicle and Freeze Solid: the stock flat values)")
_SCRIPT_HEAL = "Zul'Farrak pool: Velratha's self-heal, the script's base point (a percent of her own maximum health)"

# --- constants (GahzrillaLogic.h; lib/test_zul_farrak_gahzrilla.py pins each) -----------------------------------------

SPILL_CAST_MS = (4000, 3000)    # Tune::kSpillCastMs (normal, heroic): s10 #40 B
DISCHARGE_CAST_MS = 3000        # Tune::kDischargeCastMs
STATIC_SHOCK_MS = 2000          # Tune::kStaticShockMs
CALL_CAST_MS = (2500, 2000)     # Tune::kCallCastMs
ICICLE_CAST_MS = 2500           # Tune::kIcicleCastMs: s10 #40 B
ICICLE_SLOW_PCT = 51            # stock 11131
ICICLE_SLOW_MS = 10000          # stock 11131
FREEZE_SOLID_CAST_MS = 2500     # Tune::kFreezeSolidCastMs
FREEZE_SOLID_STUN_MS = 2000     # Tune::kFreezeSolidStunMs
SLAM_WEAPON_PCT = 50            # stock 11902
SLAM_RADIUS_YD = 20.0           # stock 11902
HEAL_CAST_MS = (3000, 2000)     # Tune::kHealCastMs
STATIC_CHARGE_MAX = 10          # Tune::kStaticChargeMax
CHARGED_MAX = 999               # Tune::kChargedMaxStacks: out of reach (no cap, ruling 38)
CONDUCTIVE_MS = 10000           # Tune::kConductiveMs
ACID_SPIT_RANGE_YD = 40.0       # Tune::kAcidSpitRangeYd

# The disc displays KT's WaterField wears (GahzrillaLogic.h kDisplayWaterDisc / kDisplayIceDisc / kDisplayStormDisc).
DISC_DISPLAYS = (GZ_WATER_DISC, GZ_ICE_DISC, GZ_STORM_DISC)

# Stock icons (Spell.dbc SpellIconID of the named spell; read from the stock DBC 2026-11-25).
_ICON_TIDAL_CHARM = 94          # Tidal Charm 835
_ICON_LIGHTNING = 19            # Static Electricity 3742, Lightning Shield 324
_ICON_CHAIN_LIGHTNING = 165     # Chain Lightning 421
_ICON_FROST = 188               # Icicle 11131, Frostbolt 10180
_ICON_FREEZE_SOLID = 35         # Freeze Solid 11836
_ICON_SLAM = 166                # Gahz'rilla Slam 11902
_ICON_HEALING_WAVE = 13         # Healing Wave 12491
_ICON_ACID_SPIT = 636           # Acid Spit 9591

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_DISPEL_MAGIC = 1
_MECHANIC_STUN = 12
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15              # movement, pushback, interrupt, auto-attack (the whitemane.py recipe)
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000  # a cast leaves the swing timer alone (LESSONS L3)
_ATTR3_NOT_A_PROC = 0x00000200


def _script_hit(spell_id: int, name: str, school: School, desc: str, notes: str, *, icon: int, visual: int):
    """A hit whose amount the script sets as the base point (CastSpellExtraArgs::AddSpellBP0; DieSides 0): triggered,
    always hits, cannot crit, ignores LoS and the caster's modifiers, never reflected or redirected, DmgClass magic."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_BP)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, DefenseType=_DEFENSE_MAGIC,
                              SpellVisualID_1=visual,
                              AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- the pool's stalker and the discs ---------------------------------------------------------------------------------

puddle_301030 = creature_template(
    301030, 'Sacred Pool', **{**KIT_HELPER, 'minlevel': 46, 'maxlevel': 46, 'rank': 0, 'unit_class': 1, 'type': 10,
                              'ScriptName': 'npc_zf_puddle'},
)
creature_model(301030, display_id=DISPLAY_INVISIBLE_STALKER)

# --- GZ1 Spill the Pool -----------------------------------------------------------------------------------------------

for _sid, _ms, _which in ((214110, SPILL_CAST_MS[0], 'normal'), (214111, SPILL_CAST_MS[1], 'heroic')):
    cast_bar(
        _sid, 'Spill the Pool', _ms, 'Spills the sacred pool where the marked enemy stands.',
        f'{_D7}, GZ1 ({_which}): 5 s, then every {10 if _which == "normal" else 8} s, Velratha\'s {_ms / 1000:g} s bar '
        '(s10 #40 B). A random player on the pool\'s arena, the tank included, is marked (214112 and an 8 yd circle '
        'that follows them; bots carry it to the shore\'s rim, away from the group); at the bar\'s end an 8 yd puddle '
        'spills where they stand. Arcane and not interruptible (InterruptFlags 0, PreventionType 0): a kicked '
        'Frostbolt (Frost) or Healing Wave (Nature) never locks it (rule 24). Tidal Charm 835\'s SV 657.',
        icon=_ICON_TIDAL_CHARM, visual=GZ_TIDAL_CHARM, school=School.ARCANE,
    )

spill_mark_214112 = spell(
    id=214112, name='Spill the Pool', school=School.ARCANE, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=SPILL_CAST_MS[0],
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_TIDAL_CHARM,
    notes=f'{_D7}, GZ1: the marked player\'s debuff for the bar (4 s; the script cuts it to 3 s on heroic and removes '
          'it as the puddle spills). Look only, not dispellable. Tidal Charm\'s SV 657.',
    raw_overrides=kit_raw('Marks an enemy for the spill.', 'The sacred pool spills where you stand. Carry it to the '
                          'edge of the shore!', instant=True, SpellVisualID_1=GZ_TIDAL_CHARM,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- GZ3 Static Discharge ---------------------------------------------------------------------------------------------

static_charge_214113 = spell(
    id=214113, name='Static Charge', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_LIGHTNING,
    notes=f'{_D7}, GZ3: his meter (DungeonKit::AddStacks by the script): 0 at a cycle\'s start, 10 when the bar '
          'starts (normal every 30 s; heroic Storm Builds: 20 s, 20 s, then 1.5 s shorter, never under the 3 s bar). '
          'Not dispellable; gone at the landing and on his reset, evade or death. V\'s SV 90707 (minted).',
    raw_overrides=kit_raw('Building charge.', 'His scales crackle. At $u stacks he discharges.', instant=True,
                          CumulativeAura=STATIC_CHARGE_MAX, SpellVisualID_1=GZ_STATIC_CHARGE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

discharge_bar_214114 = cast_bar(
    214114, 'Static Discharge', DISCHARGE_CAST_MS, 'His scales discharge into the water.',
    f'{_D7}, GZ3: the 3 s bar on himself, with emote line 0, when his meter is full; it lands exactly on Storm '
    'Builds\' clock (nothing a player does moves it). During the bar every water sheet is a one-shot registry '
    'Zone (tag 32) and its disc shows the storm display. Nature and not interruptible (his kickable Call the '
    'Waters is Arcane). The hits are 214115 and 214116. V\'s SV 90705 (the hydra pose copy of Chain '
    'Lightning\'s SV 36).',
    icon=_ICON_CHAIN_LIGHTNING, visual=GZ_DISCHARGE, school=School.NATURE,
)

discharge_214115 = _script_hit(
    214115, 'Static Discharge', School.NATURE, 'The storm discharges.',
    f'{_D7}, GZ3: the landing. Normal: 50% of the reference row on anyone in water (a puddle or the pool), nothing on '
    'dry ground or ice. Heroic: 40% on everyone plus 10% per stack of Charged (214126). The tank row on the tank '
    '(RefFlatOn). SV 90705.',
    icon=_ICON_CHAIN_LIGHTNING, visual=GZ_DISCHARGE,
)

static_shock_214116 = spell(
    id=214116, name='Static Shock', school=School.NATURE, dispel=0, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=STATIC_SHOCK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=_MECHANIC_STUN, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_LIGHTNING,
    notes=f'{_D7}, GZ3: the 2 s stun of anyone standing in water when a Discharge lands (SYS 4: 2 s at most). Not '
          'dispellable (2 s; the cost of standing in water). Stun immunities and trinkets work.',
    raw_overrides=kit_raw('Stunned by the discharge.', 'Stunned.', instant=True, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- GZ5 Call the Waters ----------------------------------------------------------------------------------------------

for _sid, _ms, _which in ((214117, CALL_CAST_MS[0], 'normal'), (214118, CALL_CAST_MS[1], 'heroic')):
    spell(
        id=_sid, name='Call the Waters', school=School.ARCANE, dispel=0, mechanic=0, cast_time_ms=_ms, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_TIDAL_CHARM,
        notes=f'{_D7}, GZ5 ({_which}): 10 s after he comes ashore, then every '
              f'{15 if _which == "normal" else 12} s: a {_ms / 1000:g} s cast on himself, kickable '
              '(InterruptFlags 15, PreventionType silence; the interrupt list). Completed (OnSpellCast): an 8 yd '
              'puddle under 2 (heroic 3) random players, the tank included; heroic, every water puddle also grows 2 '
              'yd. A kick locks Arcane only (his Discharge bar is Nature, his freezes Frost). Does not reset his '
              'swing. V\'s SV 90706 (the hydra pose, "also Call the Waters\' cast").',
        raw_overrides=kit_raw('Calls the sacred waters onto the shore.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                              PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=GZ_ACID_SPIT,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )

# --- GZ6 Icicle, GZ7 Freeze Solid, GZ8 the freeze's look --------------------------------------------------------------

icicle_214119 = spell(
    id=214119, name='Icicle', school=School.FROST, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=ICICLE_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=100.0, duration_ms=ICICLE_SLOW_MS,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_BP),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED,
                    base_points=-(ICICLE_SLOW_PCT + 1), die_sides=1, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_FROST,
    notes=f'{_D7}, GZ6: copy of Icicle 11131 (stock 1.5 s; s10 #40 B: 2.5 s) on a random player within 40 yd, the '
          'tank included, 6 s after he comes ashore, then every 10 s. NOT interruptible (InterruptFlags 0, '
          'PreventionType 0: the kick table, any kick would delete the group\'s own freeze and lock Frost). Normal: '
          'the stock 355-405 (the script rolls it); heroic 14% of the reference row; the stock 51% slow for 10 s, not '
          'dispellable as stock. Completed (OnSpellCast), the puddle its target stands in freezes (the nearest one, '
          'KT); heroic, nothing frozen: Meltwater. Does not reset his swing. Icicle\'s SV 2147.',
    raw_overrides=kit_raw('Hurls an icicle at an enemy.', 'Movement slowed by $s2%.', InterruptFlags=0,
                          PreventionType=0, DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=GZ_ICICLE,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT
                          | _ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

freeze_solid_214120 = spell(
    id=214120, name='Freeze Solid', school=School.FROST, dispel=_DISPEL_MAGIC, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=FREEZE_SOLID_CAST_MS, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=FREEZE_SOLID_STUN_MS,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_BP),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=_MECHANIC_STUN, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_FREEZE_SOLID,
    notes=f'{_D7}, GZ7: copy of Freeze Solid 11836 (stock 10 s stun, against SYS 4: 2 s now) on a random player within '
          '30 yd, the tank included, 15 s after he comes ashore, then every 22 s; a 2.5 s cast, NOT interruptible (the '
          'kick table). Normal: one stock tick (115) as the hit; heroic 4.5% of the reference row. The stun is Magic '
          '(the dispel list\'s reward). Completed, every puddle whose edge is within 8 yd of the target freezes. Does '
          'not reset his swing. Freeze Solid\'s SV 2336.',
    raw_overrides=kit_raw('Freezes an enemy solid.', 'Frozen solid.', InterruptFlags=0, PreventionType=0,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=GZ_FREEZE_SOLID,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT
                          | _ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

freeze_look_214121 = self_visual(
    214121, 'Freeze', GZ_FREEZE_EVENT,
    f'{_D7}, GZ8: cast by a puddle\'s disc on itself as the puddle freezes (the disc then wears the ice display). Ice '
    'Blast 11264\'s SV 1744. Look only.',
    icon=_ICON_FREEZE_SOLID, school=School.FROST,
)

# --- GZ11 the Slam and Acid Spit --------------------------------------------------------------------------------------

slam_214122 = spell(
    id=214122, name="Gahz'rilla Slam", school=School.NORMAL, attributes=ATTR0_IS_ABILITY, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=SLAM_WEAPON_PCT,
                    implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
                    radius_yards=SLAM_RADIUS_YD)],
    spell_icon_id=_ICON_SLAM,
    notes=f'{_D7}, GZ11: copy of Gahz\'rilla Slam 11902 without its knock up (stock rule flag 5): 50% weapon damage '
          '(WEAPON_PERCENT_DAMAGE, weapon_potency 50) on every enemy within 20 yd of him, the tank included, instant; '
          '15 s after he comes ashore, then every 25 to 35 s. His template\'s melee drives it (heroic: the heroic '
          'template\'s). Gahz\'rilla Slam\'s SV 2377.',
    raw_overrides=kit_raw('Slams the ground, hitting every enemy within $a1 yards for $s1% weapon damage.',
                          instant=True, DefenseType=_DEFENSE_MELEE, SpellVisualID_1=GZ_SLAM,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS, AttributesEx4=ATTR4_NO_CAST_LOG),
)

acid_spit_214125 = spell(
    id=214125, name='Acid Spit', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=ACID_SPIT_RANGE_YD, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_BP)],
    spell_icon_id=_ICON_ACID_SPIT,
    notes=f'{_D7}, GZ11 (every difficulty, ruling 43): when his target is out of his melee reach, each swing is a spit '
          'instead: 150% of the swing he would have dealt, as Nature (armor does not help), on his swing timer. The '
          'script\'s base point (his own swing roll, so DamageModifier and the heroic template count once). Not '
          'reflected or redirected. V\'s SV 90706 (the hydra pose copy of Acid Spit\'s SV 854).',
    raw_overrides=kit_raw('Spits acid at a distant enemy.', instant=True, InterruptFlags=0, PreventionType=0,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=GZ_ACID_SPIT,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_CANT_CRIT | _ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- GZ9 Healing Wave (Velratha) --------------------------------------------------------------------------------------

for _sid, _ms, _which, _pct in ((214123, HEAL_CAST_MS[0], 'normal', 10), (214124, HEAL_CAST_MS[1], 'heroic', 20)):
    spell(
        id=_sid, name='Healing Wave', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=_ms, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=_SCRIPT_HEAL)],
        spell_icon_id=_ICON_HEALING_WAVE,
        notes=f'{_D7}, GZ9 ({_which}): Velratha\'s self-heal, 12 s, then every 15 s: a {_ms / 1000:g} s cast for '
              f'{_pct}% of her maximum health (the script\'s base point). Kickable (InterruptFlags 15, PreventionType '
              'silence; first on her interrupt list): a kick locks Nature, never her Arcane Spill bar. Replaces the '
              'stock Healing Wave 12491 (an ally heal she had no ally for). The look is AS_HEAL (SV 135) until V adds '
              'a GZ constant (report).',
        raw_overrides=kit_raw('Heals the caster.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                              PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=AS_HEAL,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                              AttributesEx3=_ATTR3_NOT_A_PROC | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )

# --- GZ12 Charged, GZ14 Conductive (heroic) ---------------------------------------------------------------------------

charged_214126 = spell(
    id=214126, name='Charged', school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_LIGHTNING,
    notes=f'{_D7}, GZ12 (heroic): a stack a second on every player in unfrozen water (DungeonKit::AddStacks by the '
          'pool\'s stalker), for the whole fight, no cap (ruling 38; CumulativeAura 999 is out of reach); none on the '
          'Icicle target during its cast. Each stack raises the Discharge damage that player takes by 10% (the '
          'script). Not dispellable. Gone at the encounter\'s end and on a map change.',
    raw_overrides=kit_raw('Charged by the storm.', 'The storm will find you. Static Discharge deals 10% more damage '
                          'to you per stack.', instant=True, CumulativeAura=CHARGED_MAX, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

conductive_214127 = spell(
    id=214127, name='Conductive', school=School.NATURE, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=CONDUCTIVE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_LIGHTNING,
    notes=f'{_D7}, GZ14 (heroic): on anyone in water when a Discharge lands (the hard mode: everyone, D7Ha), 10 s, '
          'Magic: the answer, first on the dispel list. Every 2 s the script arcs 25% (214128) to each player within 6 '
          'yd and, while the carrier stands in water, to everyone in that sheet; bots spread 6 yd (a registry Spread '
          'on the carriers, tag 42). Lightning Shield\'s SV 37.',
    raw_overrides=kit_raw('Conducts the storm.', 'Arcs to everyone within 6 yards, and into the water you stand '
                          'in, every 2 sec.', instant=True, SpellVisualID_1=GZ_CONDUCTIVE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

conductive_arc_214128 = _script_hit(
    214128, 'Conductive', School.NATURE, 'The storm arcs.',
    f'{_D7}, GZ14 (heroic): a Conductive carrier\'s arc and its sheet\'s shock: 25% of the reference row (the tank row '
    'on the tank), one hit a player a tick. SV 90705.',
    icon=_ICON_LIGHTNING, visual=GZ_DISCHARGE,
)

# --- GZ10 the gong ----------------------------------------------------------------------------------------------------

gong_strike_214129 = self_visual(
    214129, 'Gong Strike', GZ_TIDAL_CHARM,
    f'{_D7}, GZ10: the look on Velratha as she strikes the gong 141832 (with the gong\'s own custom anim), right '
    'before the instance summons Gahz\'rilla. Tidal Charm\'s SV 657. Look only.',
    icon=_ICON_TIDAL_CHARM, school=School.ARCANE,
)
