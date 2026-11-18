"""
Blackrock Depths build WP-D12: Lord Incendius's hard mode, Lord of the Lake (heroic only;
.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D12, s3.6, s3.7, s7 #14 A, s7 #15; build
spec docs/dungeons/blackrock-depths-2-shadowforge-city.md "Hard mode" and "Build spec" IN9-IN14, rulings 81-84, 90).
WP-D12 owns this file (its spells: kSpellsLordOfTheLake 211180-211229 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h only; IncendiusHardModeLogic.h names the same ids; its creatures: 300795 and
300828).
The engine side is src/BlackrockDepths/incendius_hard_mode.cpp (on D11's boss_lord_incendius_rework through
IncendiusFight.h); its texts 8-9 are data/sql/updates/pending_db_world/rev_incendius_hard_mode_blackrock_depths.sql. The
Cinder of the Firelord (item 70621, use spell 211260) is IT's (event_items.py); this WP's C++ is its SpellScript
(spell_brd_cinder_of_the_firelord).

- 300795 Lava Spawn (IN12): a boss-kit add, a fire elemental (type 4, faction 91 like him), level 53 elite warrior class
  on the normal row (the hard mode is heroic only, so the heroic template is the one that fights: 6,000 health, WP-H's
  `extra=`, difficulty_entry_1 310406, STAGE-H-REPORT section 3); no melee worth the name (it never attacks, it walks),
  no loot, no XP, no immunities (slows, roots and stuns hold it back: a reward), the Molten Core Lava Spawn's display
  2172 on a new entry (12265 is Molten Core trash). npc_brd_lava_spawn.
- 300828 Hand of Incendius (R-1-B M2, orchestrator default after R-1): the giant's stand-in on the near rim. The giant
  keeps a small combat reach of his own (no hunter or wand is ever too close to him); the melee and the tank hit his
  Hand, which shares his health (npc_brd_lake_hand moves every hit and its threat to him and mirrors his health). Only
  ever summoned on the heroic hard mode, so it has no heroic template (the generic stalker's precedent): the normal row
  fights, at his level (the script copies it). Faction 91 and immunity set 1973 like him (the same stun and Fire
  immunity on both), passive, never attacks, no loot, no XP, his display 1204 at a small scale (a look question for the
  playtest).

Spells. The registry hits (Crushing Fist on anyone but the tank, the Arm Sweep) deal their damage through dungeon copies
of the mod-boss-mechanics resolve spell (Fire). The tank's Crushing Fist and the Breath are a percent of the target's
reference row on this WP's script spell_brd_lake_scaled_hit (the hundredths in the effect, the heroic ones in
EffectMiscValueB, the kit's refflat convention), times Firelord's Will on him (they ignore caster modifiers, so the aura
alone would not reach them). The rest are looks:

  211180  Crushing Fist          IN10 the 6 yd circle's hit on anyone but the tank: resolve copy, Fire, 45% + Weakened
  211181  Crushing Fist          IN10 the tank's own hit: 35% of the tank row (scaled hit)
  211182  Crushing Fist          IN10 the crack where the fist lands (look)
  211183  Arm Sweep              IN11 the 4 s cast bar (Physical, not kickable: rule 5, Fiery Burst is the Fire kick)
  211184  Arm Sweep              IN11 the band's hit: resolve copy, Fire, 30% (the throw over the far edge is C++)
  211185  Firelord's Breath      IN14 a second of the breath on each player: 8% (scaled hit)
  211186  Firelord's Will        IN12 +10% damage done a stack, 10 at most, for the fight (his melee)
  211187  Lava Spawn             IN12 a spawn climbs out of the lava (look, on the spawn)
  211188  Lava Eruption          IN12 / IN9 a lava burst where a spawn climbs out and under the rising giant (look)
  211189  Lava Spawn             IN12 a spawn sinks into The Black Anvil (look)
  211190  Lord of the Lake       IN9 the giant rises in the lake (look, on him)
  211191  Cinder of the Firelord IN9 the Cinder arcs from the user into the lava (look, a missile)
  211192-211229 spare

Visual ids are V-1's (._visuals IN_*, DISPLAY_*); every look is unconfirmed until seen in game. Firelord's Will has no
look of its own (._visuals has none: a shared-file request in the D12 report).
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
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

from ._common import (
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_ELEMENTAL,
    IMMUNITY_FIRE_GIANT,
    TARGET_UNIT_CASTER,
    cast_bar,
    kit_creature,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INCENDIUS_GIANT,
    DISPLAY_LAVA_SPAWN,
    IN_ARM_SWEEP,
    IN_CINDER_TOSS,
    IN_CRUSHING_FIST,
    IN_FIERY_BURST,
    IN_FIRELORDS_BREATH,
    IN_LAVA_SPAWN_CLIMB,
    IN_SHATTER_INTO_EMBERS,
)

_LAKE = 'Blackrock Depths build WP-D12 (Lord Incendius, Lord of the Lake, heroic hard mode)'
_SCRIPT_SCALED = ('Blackrock Depths Lord of the Lake: a percent of reference health in hundredths, set at launch by '
                  'spell_brd_lake_scaled_hit (DungeonKit::RefFlatOn x Firelord\'s Will)')
_SCALED_HIT_SCRIPT = 'spell_brd_lake_scaled_hit'

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_DEFENSE_MAGIC = 1
_SCHOOL_MASK_ALL = 127

# Icons (the client Spell.dbc, stock spells').
_ICON_FIRE_STORM = 37               # Fire Storm 13899
_ICON_MAGMA_FIST = 314              # Mighty Blow 14099
_ICON_FIERY_BURST = 18              # Fiery Burst 13900
_ICON_GENERIC = 1

# Numbers (IncendiusHardModeLogic.h).
_CRUSHING_TANK = 3500               # kCrushingTankPct, hundredths
_BREATH = 800                       # kBreathPct, hundredths
_WILL_PCT = 10                      # kWillPctPerStack
_WILL_MAX = 10                      # kWillMaxStacks
_SWEEP_CAST_MS = 4000               # kSweepCastMs
_CINDER_TOSS_SPEED = 20.0           # kCinderTossSpeed, yd/s (a look)
_SPAWN_HEALTH_MODIFIER = 2.4459     # ceil(2,453 x 2.4459) = 6,000 at level 53 (the normal row; heroic is WP-H's 6k)
LAVA_SPAWN_HEROIC_ENTRY = 310406    # heroic_ids.lock: Lava Spawn (STAGE-H-REPORT section 3)

# The scripted hit: no threat, no crit, always hits, ignores his modifiers (a percent of the reference row).
_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
    AttributesEx2=ATTR2_CANT_CRIT | ATTR2_IGNORE_LINE_OF_SIGHT,
    AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
)


def _scaled_hit(spell_id: int, name: str, hundredths: int, desc: str, notes: str, *, visual: int = 0,
                icon: int = _ICON_GENERIC):
    """A Fire hit on one unit (he casts it on the target, triggered): `hundredths` of the target's reference row on
    normal and heroic (EffectMiscValueB) times Firelord's Will, set at launch by spell_brd_lake_scaled_hit."""
    more = {'SpellVisualID_1': visual} if visual else {}
    s = spell(
        id=spell_id, name=name, school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=hundredths - 1, die_sides=1,
                        implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_SCALED)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=hundredths,
                              AttributesEx4=ATTR4_NO_CAST_LOG, **_HIT_ATTRS, **more),
    )
    scripted_by(s, _SCALED_HIT_SCRIPT)
    return s


def _look_at_point(spell_id: int, name: str, visual: int, notes: str, *, speed: float = 0.0):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), triggered.
    `speed` > 0: the visual flies there (a missile). A copy of D11's private helper in incendius.py."""
    more = {'Speed': speed} if speed else {}
    return spell(
        id=spell_id, name=name, school=School.FIRE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=_ICON_GENERIC, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, **more),
    )


# --- 300795 Lava Spawn ------------------------------------------------------------------------------------------------

lava_spawn_300795 = creature_template(
    300795, 'Lava Spawn', **{
        **kit_creature(faction=FACTION_ELEMENTAL, type=4), 'minlevel': 53, 'maxlevel': 53, 'rank': 1,
        'unit_class': 1, 'unit_flags': 0, 'HealthModifier': _SPAWN_HEALTH_MODIFIER, 'DamageModifier': 1.0,
        'BaseAttackTime': 2000, 'ExperienceModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
        'mingold': 0, 'maxgold': 0, 'ScriptName': 'npc_brd_lava_spawn',
        'difficulty_entry_1': LAVA_SPAWN_HEROIC_ENTRY,
    },
)
creature_model(300795, display_id=DISPLAY_LAVA_SPAWN)

# --- 300828 Hand of Incendius (R-1-B M2) ------------------------------------------------------------------------------

lake_hand_300828 = creature_template(
    300828, 'Hand of Incendius', **{
        **kit_creature(faction=FACTION_ELEMENTAL, type=4), 'minlevel': 60, 'maxlevel': 60, 'rank': 1,
        'unit_class': 1, 'unit_flags': 0, 'HealthModifier': _SPAWN_HEALTH_MODIFIER, 'DamageModifier': 0.0,
        'BaseAttackTime': 2000, 'ExperienceModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
        'mingold': 0, 'maxgold': 0, 'CreatureImmunitiesId': IMMUNITY_FIRE_GIANT, 'ScriptName': 'npc_brd_lake_hand',
    },
)
creature_model(300828, display_id=DISPLAY_INCENDIUS_GIANT)

# --- IN10 Crushing Fist -----------------------------------------------------------------------------------------------

crushing_fist_211180 = resolve_copy(
    211180, 'Crushing Fist', School.FIRE, 'The giant\'s fist crushes the ground.',
    f'{_LAKE}, IN10: from 10 s, every 15 s, a 3 s marker: a 6 yd circle on the tank\'s spot (TankExempt: the circle '
    'spares his victim, whose own hit is 211181); anyone else inside takes 45% of the row (times Firelord\'s Will) + '
    'Weakened through the registry. Copy of the resolve spell 205001 with the Fire school.',
    icon=_ICON_MAGMA_FIST,
)

crushing_fist_tank_211181 = _scaled_hit(
    211181, 'Crushing Fist', _CRUSHING_TANK, 'Crushes the target with a giant fist of magma.',
    f'{_LAKE}, IN10: the tank\'s hit to take (ruling 88: a tank job, not an exemption): as the circle lands he casts '
    'it on his victim, 35% of the tank row (hundredths 3500, the same in EffectMiscValueB) times Firelord\'s Will. '
    'Cannot crit, always hits, ignores his modifiers.',
    icon=_ICON_MAGMA_FIST,
)

crushing_fist_look_211182 = _look_at_point(
    211182, 'Crushing Fist', IN_CRUSHING_FIST,
    f'{_LAKE}, IN10: he casts it (triggered) at the circle\'s centre as the fist lands: Overhead Smash 63356\'s SV '
    '13373 (ThunderClap_Cast_Base, a 6.9 yd crack and a shake). Look only.',
)

# --- IN11 Arm Sweep ---------------------------------------------------------------------------------------------------

arm_sweep_cast_211183 = cast_bar(
    211183, 'Arm Sweep', _SWEEP_CAST_MS, 'Drags a giant arm across the island.',
    f'{_LAKE}, IN11: the 4 s cast bar (emote line 6) while the registry\'s 10 yd band across the island (211184) '
    'warns: from 20 s, every 30 s, at one of three spots (south-west, middle, north-east; never the same twice '
    'running). Physical and not kickable (InterruptFlags 0, PreventionType 0: rule 5, a kick of the Fire school '
    'Fiery Burst never locks it). Arm Sweep 63766\'s SV 13481 (Kologarn\'s animation; the band marker carries the '
    'sweep). No effect of its own.',
    icon=_ICON_GENERIC, visual=IN_ARM_SWEEP, school=School.NORMAL,
)

arm_sweep_211184 = resolve_copy(
    211184, 'Arm Sweep', School.FIRE, 'A giant arm sweeps the island.',
    f'{_LAKE}, IN11: the band\'s hit as the cast ends: 30% of the row (times Firelord\'s Will) on everyone in the 10 '
    'yd band (the tank included), then the script throws each one over the far edge (the kit\'s PushOverEdge, D11\'s '
    'ThrowOff; the FallWatch makes the fall lethal: ruling 84). A lethal registry line for the bots (tag 15, G1\'s '
    'drill). Copy of the resolve spell 205001 with the Fire school.',
    icon=_ICON_FIRE_STORM,
)

# --- IN14 Firelord's Breath -------------------------------------------------------------------------------------------

firelords_breath_211185 = _scaled_hit(
    211185, 'Firelord\'s Breath', _BREATH, 'Breathes fire across the whole island.',
    f'{_LAKE}, IN14 (ruling 90, after Kologarn\'s Petrifying Breath): when no player has stood in his reach (the 6 yd '
    'band along the current near edge) for 3 s, he casts it on every player of the fight each second (8% of the row, '
    'hundredths 800, times Firelord\'s Will; a group failure: no Weakened, no cap) until someone is back (emote line '
    '7). Heat Wave 35236\'s SV 3119 (the FlameBreath at his breath attach and the Immolate impact on each target; '
    'never Flame Breath SV 14506 or Petrifying Breath SV 13093, VISUALS).',
    visual=IN_FIRELORDS_BREATH, icon=_ICON_FIERY_BURST,
)

# --- IN12 Lava Spawn and Firelord's Will ------------------------------------------------------------------------------

firelords_will_211186 = spell(
    id=211186, name='Firelord\'s Will', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=_WILL_PCT,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Firelord\'s Will: a flat +10% damage done per stack, not a damage value')],
    spell_icon_id=_ICON_FIERY_BURST,
    notes=f'{_LAKE}, IN12: each Lava Spawn that reaches The Black Anvil heals him 5% and adds a stack (DungeonKit::'
          'AddStacks, him as caster, CumulativeAura 10): +10% damage done a stack, every school (his melee); the '
          'reference-sized hits ignore caster modifiers, so the script multiplies Crushing Fist, the Arm Sweep and the '
          'Breath (WillFactor). D11\'s Fire Storm, Magma Fist and Fiery Burst are not raised (a shared-file request '
          'in the D12 report). Not dispellable; removed on his death, evade and reset. No look of its own.',
    raw_overrides=kit_raw('The Firelord\'s will drives the lord of the lake.', 'Damage done increased by $s1%.',
                          instant=True, CumulativeAura=_WILL_MAX, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

lava_spawn_climb_211187 = self_visual(
    211187, 'Lava Spawn', IN_LAVA_SPAWN_CLIMB,
    f'{_LAKE}, IN12: from 15 s, every 20 s, two Lava Spawn 300795 climb out on the long edges (emote line 9) and walk '
    'to The Black Anvil in about 10 s; each casts this on itself (triggered) as it appears: Ragnaros Emerge 20568\'s '
    'SV 5723 (an animation: VISUALS RISKY on display 2172; the burst 211188 goes with it). Look only.',
    icon=_ICON_FIERY_BURST, school=School.FIRE,
)

lava_eruption_211188 = _look_at_point(
    211188, 'Lava Eruption', IN_SHATTER_INTO_EMBERS,
    f'{_LAKE}, IN12 / IN9: he casts it (triggered) where a Lava Spawn climbs out and under the giant as he rises: '
    'Massive Eruption 20483\'s SV 889. Look only.',
)

lava_spawn_arrives_211189 = self_visual(
    211189, 'Lava Spawn', IN_FIERY_BURST,
    f'{_LAKE}, IN12: a Lava Spawn that reaches The Black Anvil casts this on itself (triggered) and sinks in (it '
    'despawns 0.5 s later; he heals 5% and gains a Firelord\'s Will stack): Fiery Burst 13900\'s SV 516, as D11\'s '
    'Ember. Look only.',
    icon=_ICON_FIERY_BURST, school=School.FIRE,
)

# --- IN9 The Cinder and the giant -------------------------------------------------------------------------------------

lord_rises_211190 = self_visual(
    211190, 'Lord of the Lake', IN_LAVA_SPAWN_CLIMB,
    f'{_LAKE}, IN9: the Cinder\'s intro ends (and a reload or a wipe re-forms him): he stands in the lake at the '
    'giant\'s spot (kLakeLordSpot, causeway height) at creature scale 9 and casts this on himself (triggered): '
    'Ragnaros Emerge 20568\'s SV 5723 (the S2 spec\'s "Ragnaros Emerge visual"), with 211188 under him; emote line 8. '
    'Look only.',
    icon=_ICON_FIERY_BURST, school=School.FIRE,
)

cinder_toss_211191 = _look_at_point(
    211191, 'Cinder of the Firelord', IN_CINDER_TOSS,
    f'{_LAKE}, IN9: the user of the Cinder (item 70621, use spell 211260) casts it (triggered) at the lava under the '
    'giant\'s spot as the hard mode lights: Torch Toss 45732\'s SV 10211, a flaming object that arcs into the lake at '
    '20 yd/s. Look only.',
    speed=_CINDER_TOSS_SPEED,
)
