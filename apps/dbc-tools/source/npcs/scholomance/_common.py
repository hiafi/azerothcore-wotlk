"""
Scholomance build: shared constants for the per-boss declaration files of this package (not loaded on its own: the
leading underscore keeps the package loader from treating it as a declaration file; siblings import it with
`from ._common import ...`). Owned by WP-KS (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.2, s4 row
KS); a boss WP asks the orchestrator for a change here. The visual ids are WP-V's ._visuals.

The generic part (text masks, attribute bits, targets, the stun immunity set, the boss-kit creature and helper
columns, the spell builders) is the shared dungeon kit, lib/dsl/dungeon_kit.py; this file keeps Scholomance's own
values and the names the boss files import.

Files and owners (one per boss WP; spell slices in modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h,
creature ids in its ScholomanceCreatures enum, gameobject ids in ScholomanceGameObjects):

  jandice_barov.py             S1   spells 206110-206129, creature 300530 (and the stock copy 11439's columns)
  rattlegore.py                S2   spells 206130-206149, creatures 300531-300532
  marduk_and_vectus.py         S3   spells 206150-206169, creature 300533 (and the students 10475's columns)
  ras_frostwhisper.py          S4   spells 206170-206189, creature 300534
  instructor_malicia.py        S5   spells 206205-206224, creatures 300536-300537
  doctor_theolen_krastinov.py  S6   spells 206225-206249, creatures 300538-300539
  lorekeeper_polkelt.py        S7   spells 206250-206269, creatures 300540-300541
  the_ravenian.py              S8   spells 206270-206289, creature 300542
  lord_alexei_barov.py         S9   spells 206290-206314, creature 300543
  lady_illucia_barov.py        S10  spells 206315-206329
  darkmaster_gandling.py       S11  spells 206330-206364, creatures 300544-300547
  ras_hard_mode.py             S12  spells 206190-206204, creature 300535, gameobjects 301150-301152, 301154
  graduate_exam.py             S13  spells 206365-206384, creatures 300548-300554, gameobject 301153
  hard_mode_items.py           W1   (item variants) creature 300465, the `scholomance_items` reservation
  shared spells 206100-206109 (KS / S11, none declared yet), spare spells 206385-206399, creatures 300555-300579,
  gameobjects 301155-301199: ask the orchestrator.

A boss-kit combat add listed in source/world/dungeons/scholomance.py's `extra=` (WP-H) gets its heroic template in the
same run (lib/dungeon_heroic.py with_declared_templates), and its full creature_template() row must name that heroic
entry itself: `difficulty_entry_1` = its id in source/world/heroic_ids.lock (generate.py --check prints it when
missing).
"""

from lib.dsl.dungeon_kit import (  # noqa: F401 - re-exported for the boss files
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TEXT_MASKS,
    cast_bar,
    kit_creature,
    kit_helper,
    kit_raw,
    resolve_copy,
)

# Scholomance's hostile faction: the Scourge of the school (faction 233 on every boss except Krastinov and Gandling,
# 21, and Marduk and Vectus, 15; read-only SELECTs 2026-11-08). Undead by default; a boss WP passes type= for its
# humanoids (7).
FACTION_SCHOLOMANCE = 233

# The boss-kit creature columns every new Scholomance creature shares: faction 233, unit_flags2 2048, undead, exp 0,
# standing still (MovementType 0: the scripts place and move them), no SmartAI.
KIT_CREATURE = kit_creature(faction=FACTION_SCHOLOMANCE, type=6)

# Summoned helpers the players never target (stalkers, anchors, markers): not selectable and not attackable, hostile
# faction 14, no loot, no XP (flags_extra 0x40), no melee (lib/dsl/dungeon_kit.py kit_helper).
KIT_HELPER = kit_helper(KIT_CREATURE)

# creature_template.flags_extra bits (SharedDefines / CreatureData.h): no stock Scholomance boss has INSTANCE_BIND
# (DB-REPORT 0.2); Krastinov keeps CIVILIAN (he only fights when attacked).
FLAGS_EXTRA_INSTANCE_BIND = 0x1
FLAGS_EXTRA_CIVILIAN = 0x2


def boss_columns(script_name: str, health_modifier: float, **more) -> dict:
    """The normal-row columns WP-KS's skeleton sets on every reworked boss (handoff s4 row KS): the C++ script, SmartAI
    off (the boss WP's SQL rev drops the stock smart_scripts rows), the build spec's normal HealthModifier (s3.6), the
    kit's stun immunity set 1972 (s7 #9) and INSTANCE_BIND (flags_extra 1; s8 #11). `more` adds or overrides columns
    (Krastinov's flags_extra 3 = INSTANCE_BIND | CIVILIAN)."""
    return {
        'ScriptName': script_name,
        'AIName': '',
        'HealthModifier': health_modifier,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        'flags_extra': FLAGS_EXTRA_INSTANCE_BIND,
        **more,
    }
