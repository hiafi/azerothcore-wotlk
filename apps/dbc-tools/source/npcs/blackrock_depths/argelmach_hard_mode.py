"""
Blackrock Depths build WP-D16: Golem Lord Argelmach's hard mode, the Prototype (heroic only;
.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.6, s3.7 row D16, s3.8, s7 #15; build spec
docs/dungeons/blackrock-depths-3-manufactory.md "Hard mode" and "Build spec" AR4, AR11-AR13, rulings 57, 58, 88). WP-D16
owns this file (its spells: kSpellsPrototype 211370-211409 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h only; ArgelmachHardModeLogic.h names the same ids; its creatures: 300836,
300838). The engine side is src/BlackrockDepths/argelmach_hard_mode.cpp (on D15's boss_golem_lord_argelmach_rework
through ArgelmachFight.h); the console line (text group 4), the Activation Console (GO 301284) and the fourth pedestal
(GO 301288) are data/sql/updates/pending_db_world/rev_argelmach_hard_mode_blackrock_depths.sql.

- 300836 Magmatron (AR11, AR12): a boss-kit add like D15's three golems (level 55 elite mechanical of his faction on the
  normal row, stun immunity 1972, no loot or XP, bound to D15's npc_brd_argelmach_golem: it never moves or melees). The
  hard mode is heroic only, so the heroic template is the one that fights: 100,000 health (WP-H's `extra=`,
  difficulty_entry_1 310413, STAGE-H-REPORT section 3; the script sets 100k at the wake too). The normal row carries
  100,000 as well (HealthModifier 38.2555 on the warrior base 2,614). Display 8179 (GolemStone molten, V-1). Dormant
  (Stoned, not selectable) on the fourth pedestal while he is idle on heroic; awake from the pull of a hard mode.
- 300838 Salvaged Core (AR13): a helper on a dead golem's pedestal (not selectable, not attackable, no loot or XP, the
  invisible stalker skin), the source of the wreck's half-rate signature; no heroic template (handoff s7 #2), bound to
  npc_brd_argelmach_golem (passive, never evades: it stays in the fight at 0 threat).

Spells. The registry hits (Incineration's 15% on everyone, the ignited clouds' bursts, the Flamethrower's cone) deal
their damage through dungeon copies of the mod-boss-mechanics resolve spell (Fire). The two bars are the kit's named
no-effect casts (Fire: Chain Lightning, the fight's kick, is Nature; rule 5). The rest are looks:

  211370  Incineration     AR11 the 3 s bar (Magmatron, or its wreck's core); not kickable
  211371  Incineration     AR11 15% to everyone as the bar ends: resolve copy, Fire
  211372  Incineration     AR11 the fire ring on the caster and on each ignited cloud (look)
  211373  Ignited Cloud    AR11 30% + Weakened within 8 yd of an ignited Chemical Bomb cloud: resolve copy, Fire
  211374  Flamethrower     AR12 the 2 s bar (Magmatron); not kickable
  211375  Flamethrower     AR12 the 60 degree, 25 yd cone: resolve copy, Fire, 35% + Weakened (burns Poison Mist off)
  211376  Flamethrower     AR12 the breath as the cone lands (look)
  211377  Salvaged Core    AR13 the running core on a wreck's pedestal (look, a state on the core)
  211378-211409 spare

Visual ids are V-1's (._visuals AR_*); every look is unconfirmed until seen in game. Magmatron's fire is molten orange:
Heat Wave SV 3119 and Fire Nova SV 6899, never Chemical Flames SV 10407 (fel green; VISUALS and
lib/test_blackrock_depths_vfx.py). The core's look is AR_SALVAGED_CORE (SV 37, Lightning Shield's lasting electric
state).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR0_DO_NOT_DISPLAY, ATTR0_DO_NOT_LOG, ATTR1_NO_THREAT, self_visual
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR4_NO_CAST_LOG,
    FACTION_DARK_IRON,
    IMMUNITY_BOSS_STUN,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    cast_bar,
    kit_creature,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    AR_FLAMETHROWER,
    AR_INCINERATION,
    AR_SALVAGED_CORE,
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_MAGMATRON,
)

_PT = 'Blackrock Depths build WP-D16 (Argelmach\'s hard mode, the Prototype)'

_TYPE_MECHANICAL = 9

# Icons (the client Spell.dbc, as WP-D12 reads them).
_ICON_FIERY_BURST = 18              # Fiery Burst 13900
_ICON_FIRE_STORM = 37               # Fire Storm 13899
_ICON_GENERIC = 1

# Numbers (ArgelmachHardModeLogic.h).
_INCINERATION_CAST_MS = 3000        # kIncinerationCastMs
_FLAME_WARN_MS = 2000               # kFlameWarnMs

_MAGMATRON_HEALTH_MODIFIER = 38.2555    # ceil(2,614 x 38.2555) = 100,000 at level 55 (kMagmatronHealth)
MAGMATRON_HEROIC_ENTRY = 310413         # heroic_ids.lock (STAGE-H-REPORT s3)

# --- 300836 Magmatron, 300838 the Salvaged Core ----------------------------------------------------------------------

magmatron_300836 = creature_template(
    300836, 'Magmatron', **{
        **kit_creature(faction=FACTION_DARK_IRON, type=_TYPE_MECHANICAL), 'minlevel': 55, 'maxlevel': 55, 'rank': 1,
        'unit_class': 1, 'unit_flags': 0, 'HealthModifier': _MAGMATRON_HEALTH_MODIFIER, 'DamageModifier': 1.0,
        'BaseAttackTime': 2000, 'ExperienceModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
        'mingold': 0, 'maxgold': 0, 'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        'ScriptName': 'npc_brd_argelmach_golem', 'difficulty_entry_1': MAGMATRON_HEROIC_ENTRY,
    },
)
creature_model(300836, display_id=DISPLAY_MAGMATRON)

salvaged_core_300838 = creature_template(
    300838, 'Salvaged Core', **{**KIT_HELPER, 'minlevel': 55, 'maxlevel': 55, 'rank': 0, 'unit_class': 1,
                                'ScriptName': 'npc_brd_argelmach_golem'},
)
creature_model(300838, display_id=DISPLAY_INVISIBLE_STALKER)

# --- AR11 Incineration -----------------------------------------------------------------------------------------------

incineration_bar_211370 = cast_bar(
    211370, 'Incineration', _INCINERATION_CAST_MS, 'Incinerates every enemy in the chamber.',
    f'{_PT}, AR11: Magmatron\'s bar, 10 s after the pull, then every 25 s (its wreck\'s Salvaged Core: every 50 s, '
    'from the core), with his boss emote (line 5). At its start every Chemical Bomb cloud on the floor ignites (D15\'s '
    'TakeClouds: the cloud goes, an 8 yd registry circle shows); as it ends 15% to everyone (211371) and the circles '
    'burst (211373). Fire, not interruptible (rule 5: the fight\'s kick, Chain Lightning, is Nature); Magmatron dying '
    'mid-bar puts it out.',
    icon=_ICON_FIERY_BURST, school=School.FIRE,
)

incineration_hit_211371 = resolve_copy(
    211371, 'Incineration', School.FIRE, 'Flames wash over the chamber.',
    f'{_PT}, AR11: the bar\'s end: 15% of the row to every player in the fight, through the registry (DungeonKit::'
    'RegistryHit, no Weakened). Copy of the resolve spell 205001 with the Fire school.',
    icon=_ICON_FIERY_BURST,
)

incineration_look_211372 = self_visual(
    211372, 'Incineration', AR_INCINERATION,
    f'{_PT}, AR11: the fire ring as the bar ends: the caster (Magmatron or the core) casts it on itself, and a generic '
    'stalker (300796, 2 s) on each ignited cloud. Fire Nova 23462\'s SV 6899 (V-1; never Chemical Flames SV 10407, fel '
    'green). Look only.',
    icon=_ICON_FIERY_BURST, school=School.FIRE,
)

ignited_cloud_211373 = resolve_copy(
    211373, 'Ignited Cloud', School.FIRE, 'The chemical cloud bursts into flame.',
    f'{_PT}, AR11: each Chemical Bomb cloud lit at the bar\'s start bursts as it ends: 30% of the row and Weakened to '
    'everyone within 8 yd of its spot (a registry circle with the bar\'s 3 s warning; the bots step out). Copy of the '
    'resolve spell 205001 with the Fire school.',
    icon=_ICON_FIERY_BURST,
)

# --- AR12 Flamethrower -----------------------------------------------------------------------------------------------

flamethrower_bar_211374 = cast_bar(
    211374, 'Flamethrower', _FLAME_WARN_MS, 'Turns a stream of fire on an enemy.',
    f'{_PT}, AR12: Magmatron\'s bar, 6 s after the pull, then every 15 s, beside the registry cone (60 degrees, 25 yd) '
    'fixed toward a random player (the tank too, ruling 88) for the 2 s marker. Fire, not interruptible (rule 5).',
    icon=_ICON_FIRE_STORM, school=School.FIRE,
)

flamethrower_hit_211375 = resolve_copy(
    211375, 'Flamethrower', School.FIRE, 'A stream of fire scorches everything in front of Magmatron.',
    f'{_PT}, AR12: the cone\'s hit: 35% of the row and Weakened to everyone inside as the marker ends; the script\'s '
    'OnHit removes Poison Mist (211337, D15) from each player hit (S3: "it burns off Poison Mist\'s debuff"). Copy of '
    'the resolve spell 205001 with the Fire school.',
    icon=_ICON_FIRE_STORM,
)

flamethrower_look_211376 = self_visual(
    211376, 'Flamethrower', AR_FLAMETHROWER,
    f'{_PT}, AR12: the breath as the cone lands: Magmatron (turned to the cone) casts it on itself. Heat Wave 35236\'s '
    'SV 3119, FlameBreath at the breath attach (V-1; never Chemical Flames SV 10407, fel green). Look only.',
    icon=_ICON_FIRE_STORM, school=School.FIRE,
)

# --- AR13 the Salvaged Core ------------------------------------------------------------------------------------------

salvaged_core_look_211377 = spell(
    id=211377, name='Salvaged Core', school=School.NATURE, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_PT}, AR13: the running core\'s look: a Salvaged Core (300838) on a dead golem\'s (or Magmatron\'s) '
          'pedestal casts it on itself (triggered) as it starts, with his boss emote (line 6), and keeps it until '
          'the fight ends (the core despawns with his summons). A hidden DUMMY aura for its state look: Lightning '
          'Shield 15507\'s lasting SV 37 (sparks), borrowed from ._visuals AR_LIGHTNING_SHIELD until V-2 names the '
          'core\'s look. No effect.',
    raw_overrides=kit_raw(CastingTimeIndex=1, SpellVisualID_1=AR_SALVAGED_CORE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
