"""
Zul'Farrak build WP-D7Ha: the crew at the pool, the main half of the hard mode "The Crew at the Pool" (heroic only,
armed by Bly's Test with all five crew at the pool) (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5
row D7Ha, s3.7, s3.9 rows 9 and 13, s7 #16, #17, #39, #43, #58, s10; build spec docs/dungeons/zul-farrak-rework.md
"Hard mode: the crew at the pool", GZ15-GZ21, rulings 41-43). WP-D7Ha owns this file (its spells: kSpellsPoolCrew
214150-214189 of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h only; GahzrillaCrewHardModeLogic.h names
the same ids; Gahz'rilla's emote line 2 is the core SQL rev rev_gahzrilla_crew_hard_mode_zul_farrak.sql; Bly's line 5
and Weegli's line 4 are CR's rev). The C++ is src/ZulFarrak/gahzrilla_crew_hard_mode.cpp, a package of D7's
PoolFight.h and a PoolAlly handler on CR's crew.

- 301031 the Wellspring (npc_zf_wellspring), GZ15: a spring that feeds its own puddle (the 6 yd water sheet that
  cannot freeze and grows 2 yd every 5 s is D7's water field's; its disc is D7's water display). Attackable, hostile
  (Gahz'rilla's beast faction 107), passive, never moves, no loot, no XP. 40,000 health on heroic (WP-H's kit
  override; the hard mode is heroic only, the normal row is the same 40,012 at 13.11 on the level 60 warrior base
  3,052). It wears the invisible stalker display 11686 (no lasting geyser model exists, VISUALS C4 #4): the one-shot
  geyser 214150 repeats on it every 4 s over its water disc, and its nameplate shows it. Its heroic template is
  WP-H's predicted 310542 (difficulty_entry_1, the lock's next kit line after the Pyramid's three specialists).
- 301032 the second head of Gahz'rilla (npc_zf_second_head), GZ20: Twin Call's second caster (one unit cannot cast
  twice). Hostile (faction 107), selectable and attackable so it can be kicked, but the script takes all its damage
  away and it is no kill target; the script gives it Gahz'rilla's combat reach, so his melee reach is its. Invisible
  stalker display 11686 (a head of the hydra; its nameplate and cast bar show). No heroic template (it runs on its
  normal entry in the heroic, as the stalkers).

Spells. The player hits take the script's base point (DieSides 0) or are the registry's resolve copy, ignore the
caster's modifiers and are never reflected or redirected (rule 2, LESSONS L7). Looks are V's _visuals.py constants:

  214150  Wellspring        GZ15: the geyser on the spring (look; Geyser 10987's SV 7680, a one-shot, repeated)
  214151  Blasting Charge   GZ16: the registry's resolve copy (Fire): 60% to the players within 10 yd of the spring
  214152  Blasting Charge   GZ16: the blast on the spring (look; SV 889)
  214153  Blasting Charge   GZ16: Weegli's 5 s plant (his bar; a stun starts it over)
  214154  Storm's Chosen    GZ17: the marked player's 4 s debuff (look; Hunter's Mark SV 3239)
  214155  Storm's Chosen    GZ17: the bolt, 150% Nature (script base point; V's SV 90702)
  214156  Storm's Chosen    GZ17: the bolt striking Bly (look; SV 90702)
  214157  Bodyguard         GZ17: Bly takes the bolt (look; Intervene SV 9107)
  214158  Overcharge        GZ18: the player's 8 s debuff, then 5 Charged (script; Lightning Shield SV 37)
  214159  Siphon Charge     GZ18: Oro's 3 s channel on that player (look; V's SV 8647)
  214160  Mass Dispel       GZ19: Murta's 2 s cast after each Discharge (her bar; SV 8140)
  214161  Greater Heal      GZ21: Murta's 2.5 s heal on the crew member lowest on health (her bar; SV 57)
  214162  Call the Waters   GZ20: the second head's copy of D7's heroic 214118: 2 s, Arcane, kickable
  214163-214189 spare.

Kicks and schools (s3.5 kick table, rule 24): the second head's only cast is its kickable Arcane Call the Waters (a
kick locks only its Arcane); the crew's bars are friendly casts players cannot kick. Nothing here is dispellable:
Storm's Chosen and Overcharge are timers whose answers are positions (Charged and Overcharge are not dispellable, the
kick table), Conductive is D7's (its dispel list). The crew's other hits (the Discharge, Conductive's arcs) and their
own damage are script on their health (rule 29), no spell.
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
)
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_BEAST,
    FLAGS_EXTRA_DONT_CALL_ASSISTANCE,
    FLAGS_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BC_GREATER_HEAL,
    BC_INTERVENE,
    BC_MARK,
    DISPLAY_INVISIBLE_STALKER,
    GZ_BLAST,
    GZ_CONDUCTIVE,
    GZ_GEYSER,
    GZ_MASS_DISPEL,
    GZ_OVERCHARGE,
    GZ_STORM_STRIKE,
    GZ_TIDAL_CHARM,
)

_D7HA = "Zul'Farrak build WP-D7Ha (the crew at the pool)"
_SCRIPT_BP = ("Zul'Farrak pool hard mode: the script's base point (a percent of reference health, "
              "DungeonKit::RefFlatOn with the boss as the owner)")

# --- constants (GahzrillaCrewHardModeLogic.h; lib/test_zul_farrak_crew_hard_mode.py pins each) ------------------------

WELLSPRING_HEALTH = 40_000          # SP Build spec; WP-H's kit override on the heroic copy (zul_farrak.py)
WELLSPRING_HEROIC = 310542          # WP-H's predicted heroic entry (s4 "kit adds' difficulty_entry_1")
PLANT_MS = 5000                     # Tune::kPlantMs
CHOSEN_MARK_MS = 4000               # Tune::kChosenMarkMs
OVERCHARGE_MS = 8000                # Tune::kOverchargeMs
SIPHON_MS = 3000                    # Tune::kSiphonMs
MASS_DISPEL_CAST_MS = 2000          # Tune::kMassDispelCastMs
GREATER_HEAL_CAST_MS = 2500         # Tune::kGreaterHealCastMs
TWIN_CALL_CAST_MS = 2000            # Tune::kTwinCallCastMs (D7's heroic Call the Waters)

_WARRIOR_60_BASE = 3052             # creature_classlevelstats class 1 level 60 (handoff s3.6)
_FLAGS_EXTRA_NO_XP = 0x40

# Stock icons (Spell.dbc SpellIconID of the named spell; as gahzrilla.py, read from the stock DBC 2026-11-25).
_ICON_TIDAL_CHARM = 94              # Tidal Charm 835
_ICON_LIGHTNING = 19                # Static Electricity 3742, Lightning Shield 324
_ICON_GENERIC = 1

_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15              # movement, pushback, interrupt, auto-attack (gahzrilla.py's recipe)
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP
_ATTR1_IS_CHANNELED = 0x00000004            # SPELL_ATTR1_IS_CHANNELED (gerstahn.py's Mind Flay)
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000

# --- the Wellspring and the second head -------------------------------------------------------------------------------

wellspring_301031 = creature_template(
    301031, 'Wellspring', **{
        **KIT_CREATURE, 'faction': FACTION_BEAST, 'type': 4, 'minlevel': 60, 'maxlevel': 60, 'rank': 0,
        'unit_class': 1, 'unit_flags': 0, 'HealthModifier': round(WELLSPRING_HEALTH / _WARRIOR_60_BASE, 2),
        'DamageModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
        'RegenHealth': 0, 'detection_range': 0.0, 'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        'flags_extra': _FLAGS_EXTRA_NO_XP | FLAGS_EXTRA_DONT_CALL_ASSISTANCE | FLAGS_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS,
        'difficulty_entry_1': WELLSPRING_HEROIC, 'ScriptName': 'npc_zf_wellspring',
    },
)
creature_model(301031, display_id=DISPLAY_INVISIBLE_STALKER)

second_head_301032 = creature_template(
    301032, "Gahz'rilla", **{
        **KIT_CREATURE, 'subname': 'Second Head', 'faction': FACTION_BEAST, 'type': 1, 'minlevel': 60,
        'maxlevel': 60, 'rank': 1, 'unit_class': 1, 'unit_flags': 0, 'HealthModifier': 10.0, 'DamageModifier': 0.0,
        'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'detection_range': 0.0,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        'flags_extra': _FLAGS_EXTRA_NO_XP | FLAGS_EXTRA_DONT_CALL_ASSISTANCE | FLAGS_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS,
        'ScriptName': 'npc_zf_second_head',
    },
)
creature_model(301032, display_id=DISPLAY_INVISIBLE_STALKER)

# --- GZ15 Wellspring, GZ16 Blasting Charge ----------------------------------------------------------------------------

wellspring_look_214150 = self_visual(
    214150, 'Wellspring', GZ_GEYSER,
    f'{_D7HA}, GZ15: the spring (301031) casts it on itself as it bursts and again every 4 s: Geyser 10987\'s SV 7680, '
    'a one-shot impact (no lasting geyser exists, VISUALS C4 #4); the water disc under it is D7\'s. Look only.',
    icon=_ICON_TIDAL_CHARM, school=School.FROST,
)

blasting_charge_214151 = resolve_copy(
    214151, 'Blasting Charge', School.FIRE, "Weegli's charge goes off.",
    f'{_D7HA}, GZ16: Weegli runs to the newest spring, plants for 5 s (214153), yells line 4 and steps away: a 3 s '
    'fuse (the registry Circle, 10 yd on the spring, tag 40), then 60% of the reference row to every player in it, '
    'the tank row on the tank. No Weakened (60% is its own penalty, SP). The spring and its puddle are gone (the '
    'script). Copy of the resolve spell 205001 (Fire).',
    icon=_ICON_GENERIC,
)

blast_look_214152 = self_visual(
    214152, 'Blasting Charge', GZ_BLAST,
    f'{_D7HA}, GZ16: the blast on the spring as the fuse ends (SV 889, the Pyramid\'s barrel blast). Look only.',
    icon=_ICON_GENERIC, school=School.FIRE,
)

plant_charge_214153 = cast_bar(
    214153, 'Blasting Charge', PLANT_MS, 'Plants a charge on the spring.',
    f'{_D7HA}, GZ16: Weegli\'s 5 s bar at the newest spring (a friendly cast: nobody kicks it; a stun from a Discharge '
    'starts it over). At its end his stock barrel (10772, GO 141612) stands on the spring and the 3 s fuse burns.',
    school=School.FIRE,
)

# --- GZ17 Storm's Chosen ----------------------------------------------------------------------------------------------

storms_chosen_214154 = spell(
    id=214154, name="Storm's Chosen", school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=CHOSEN_MARK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_LIGHTNING,
    notes=f'{_D7HA}, GZ17: 15 s after Velratha\'s pull, then every 30 s: a random player, the tank included, marked '
          'for 4 s (Bly yells line 5); then the bolt (214155). Not dispellable (the answer is Bly: stand within 5 yd '
          'of him). Hunter\'s Mark\'s SV 3239 (a head glow, readable at range).',
    raw_overrides=kit_raw("Marked by the storm.", "A bolt strikes you in 4 sec. Stand behind Sergeant Bly!",
                          instant=True, SpellVisualID_1=BC_MARK, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

storms_chosen_bolt_214155 = spell(
    id=214155, name="Storm's Chosen", school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_BP)],
    spell_icon_id=_ICON_LIGHTNING,
    notes=f'{_D7HA}, GZ17: the bolt 4 s after the mark: 150% of the reference row on the marked player (lethal alone, '
          'on purpose, SP), the tank row on the tank; nothing when the marked player stood within 5 yd of a dry, '
          'unstunned Bly (he takes it, 2 Charged); Bly dead: 150% split among the players within 5 yd of the mark, '
          '1 Charged each. Cast by the boss in play. V\'s SV 90702 (the storm strike).',
    raw_overrides=kit_raw('A bolt from the storm.', instant=True, InterruptFlags=0, PreventionType=0,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=GZ_STORM_STRIKE,
                          AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

storm_bolt_look_214156 = self_visual(
    214156, "Storm's Chosen", GZ_STORM_STRIKE,
    f'{_D7HA}, GZ17: the bolt striking Bly as he takes it for the marked player (V\'s SV 90702). Look only.',
    icon=_ICON_LIGHTNING, school=School.NATURE,
)

bodyguard_214157 = self_visual(
    214157, 'Bodyguard', BC_INTERVENE,
    f'{_D7HA}, GZ17: Bly steps in front of the marked player (Intervene\'s SV 9107, VISUALS "Storm\'s Chosen '
    'Bodyguard"). Look only.',
    icon=_ICON_GENERIC,
)

# --- GZ18 Overcharge --------------------------------------------------------------------------------------------------

overcharge_214158 = spell(
    id=214158, name='Overcharge', school=School.NATURE, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=OVERCHARGE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_LIGHTNING,
    notes=f'{_D7HA}, GZ18: 25 s after Velratha\'s pull, then every 25 s: a random player, the tank included, 8 s; '
          'when it runs out the script adds 5 stacks of Charged (D7\'s 214126) for good, unless Oro drained it first '
          '(214159, within 10 yd, dry and not stunned). Not dispellable (the kick table: Overcharge). Lightning '
          'Shield\'s SV 37 (SP: "Conductive, Overcharge").',
    raw_overrides=kit_raw('Overcharged by the storm.', 'At the end you gain 5 Charged. Stand near Oro Eyegouge!',
                          instant=True, SpellVisualID_1=GZ_CONDUCTIVE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

siphon_charge_214159 = spell(
    id=214159, name='Siphon Charge', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=SIPHON_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_LIGHTNING,
    notes=f'{_D7HA}, GZ18: Oro\'s 3 s channel on the Overcharged player within 10 yd (a friendly channel: nobody kicks '
          'it; a stun breaks it): at its end the script removes Overcharge and gives Oro 1 Charged. V\'s SV 8647 '
          '(Channel Air Shield\'s lightning chain, "the Oro tether"). Look only.',
    raw_overrides=kit_raw('Siphons the storm away.', 'Oro is draining your charge.', CastingTimeIndex=1,
                          SpellVisualID_1=GZ_OVERCHARGE, AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          InterruptFlags=0, ChannelInterruptFlags=0, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- GZ19 Mass Dispel, GZ21 Greater Heal ------------------------------------------------------------------------------

mass_dispel_214160 = cast_bar(
    214160, 'Mass Dispel', MASS_DISPEL_CAST_MS, 'Cleanses the storm from everyone nearby.',
    f'{_D7HA}, GZ19: Murta\'s 2 s cast after each Discharge (every Discharge leaves Conductive on everyone in the hard '
    'mode), if she stands dry and is not stunned: at its end the script removes Conductive (D7\'s 214127) from every '
    'player and crew member within 15 yd of her. A friendly cast (nobody kicks it). SV 8140 (Mass Dispel 32375).',
    visual=GZ_MASS_DISPEL, school=School.HOLY,
)

greater_heal_214161 = spell(
    id=214161, name='Greater Heal', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=GREATER_HEAL_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_D7HA}, GZ21: Murta\'s 2.5 s cast on the crew member lowest on health under 80%, 6 s apart, never into '
          'a Discharge: the script heals 30% of the target\'s health at its end (rule 29: NPC healing at the pool is '
          'script). A friendly cast (nobody kicks it). SV 57 (BC_GREATER_HEAL).',
    raw_overrides=kit_raw('Heals a friend.', InterruptFlags=0, PreventionType=0, SpellVisualID_1=BC_GREATER_HEAL,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- GZ20 Twin Call ---------------------------------------------------------------------------------------------------

twin_call_214162 = spell(
    id=214162, name='Call the Waters', school=School.ARCANE, dispel=0, mechanic=0, cast_time_ms=TWIN_CALL_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_TIDAL_CHARM,
    notes=f'{_D7HA}, GZ20: the second head (301032) casts it whenever Gahz\'rilla casts his own Call the Waters (D7\'s '
          '214118): 2 s on itself, kickable (InterruptFlags 15, PreventionType silence). Raven kicks it 0.8 s in when '
          'she stands in his melee, dry and not stunned; Raven dead, it joins the bots\' interrupt list. Completed '
          '(OnSpellCast), it lands as his own (D7\'s LandCallTheWaters: puddles under three players, every water '
          'puddle 2 yd). A kick locks Arcane only. Tidal Charm\'s SV 657 (VISUALS: Call the Waters\' cast cue).',
    raw_overrides=kit_raw('Calls the sacred waters onto the shore.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                          PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=GZ_TIDAL_CHARM,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
