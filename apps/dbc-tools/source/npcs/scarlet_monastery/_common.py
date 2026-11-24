"""
Scarlet Monastery build: shared constants for the per-boss declaration files of this package (not loaded on its own:
the leading underscore keeps the package loader from treating it as a declaration file; siblings import it with
`from ._common import ...`). Owned by WP-S0 (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md
s3.2, s4.1 row S0) until it reports, then by the orchestrator; a boss WP asks for a change here in its report. The
visual ids are WP-V's ._visuals.

The generic part (text masks, attribute bits, targets, the stun immunity set, the boss-kit creature and helper
columns, the spell builders) is the shared dungeon kit, lib/dsl/dungeon_kit.py; this file keeps Scarlet Monastery's own
values and the names the boss files import.

Files and owners (one per boss WP; spell slices in modules/mod-dungeon-bosses
src/ScarletMonastery/ScarletMonasteryRework.h, creature ids in its SmCreatures enum, gameobject ids in SmGameObjects;
ids.yaml reservation `scarlet_monastery`):

  wave 1, sections 1-2 (bound now; Kell and Hollis Grey once their WPs declare them):
  instance.py                 S0   spells 212300-212319 (the council's and the Last Stand's credit spells)
  vishas.py                   D1   spells 212320-212349
  ironspine.py                D2   spells 212350-212389, creatures 300900-300902
  council.py                  D3   spells 212390-212439
  thalnos.py                  D4   spells 212440-212479
  thalnos_hard_mode.py        D4H  spells 212480-212539, creatures 300903-300907, gameobjects 301310-301314
  loksey.py                   D5   spells 212540-212569, creatures 300908, 300909
  kell.py                     D6   spells 212570-212609, creatures 300910-300912, gameobjects 301315-301318
  hollis_grey.py              D7   spells 212610-212669, creatures 300913-300918
  doan.py                     D8   spells 212670-212709, creature 300919, gameobject 301319
  doan_hard_mode.py           D8H  spells 212710-212749, creatures 300920, 300921, gameobjects 301320-301323
  wave 2, sections 3-4 (behind BIND_WAVE_2):
  crell.py                    D9   spells 212900-212949, creatures 300940, 300941, gameobjects 301325-301327
  halden.py                   D10  spells 212950-212979, creatures 300942, 300943
  herod.py                    D11  spells 212980-213019
  herod_hard_mode.py          D11H spells 213020-213059, creatures 300944, 300945, gameobjects 301328, 301329
  thorne.py                   D12  spells 213060-213099, creatures 300946-300949
  last_stand.py               D13  spells 213100-213149, creatures 300950-300955, gameobjects 301330, 301331
  whitemane.py                D14  spells 213150-213189
  whitemane_hard_mode.py      D14H spells 213190-213239, creatures 300956, 300957
  the wing portal gameobject 301324 is S0's (hand SQL: rev_skeleton_scarlet_monastery.sql); spare spells
  212750-212899 (wave 1) and 213240-213499, the generic stalkers 300922 (wave 1) and 300958 (wave 2), spare
  creatures 300923-300939 and 300959-300979, gameobjects 301332-301339: ask the orchestrator. The gear's
  `scarlet_monastery_items` reservation (212000-212099, 300880-300889) is source/items/scarlet_monastery_hard_mode_*.py
  and hard_mode_items.py; `zealot_set` (212100-212299, 300890-300899) is source/items/zealot_set*.py.

A boss-kit combat add listed in source/world/dungeons/scarlet_monastery.py's `extra=` (WP-H) gets its heroic template
in the same run (lib/dungeon_heroic.py with_declared_templates), and its full creature_template() row must name that
heroic entry itself: `difficulty_entry_1` = its id in source/world/heroic_ids.lock (generate.py --check prints it when
missing). Wave 1 adds mint before wave 2 adds (the creature slices above keep every wave 1 id below every wave 2 id).

Not flex (HUB summary): the 5-player values are the template values here (HealthModifier on the normal rows, WP-H's
heroic overrides); nothing scales them at the pull.
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

# Scarlet Monastery's factions (read-only SELECTs 2026-11-20): the Scarlet Crusade 67 (Vishas, Loksey, Doan, Herod,
# Mograine, Whitemane, Fairbanks and the trash), the Graveyard's undead 21 (Ironspine, Azshir, the Fallen Champion,
# Thalnos).
FACTION_SCARLET_CRUSADE = 67
FACTION_UNDEAD = 21

# The boss-kit creature columns every new Scarlet creature shares: faction 67, unit_flags2 2048, humanoid, exp 0,
# standing still (MovementType 0: the scripts place and move them), no SmartAI. An undead or beast add sets its own
# faction and type (kit_creature(faction=FACTION_UNDEAD, type=6) and so on).
KIT_CREATURE = kit_creature(faction=FACTION_SCARLET_CRUSADE, type=7)

# Summoned helpers the players never target (stalkers, triggers, markers): not selectable and not attackable, hostile
# faction 14, no loot, no XP (flags_extra 0x40), no melee (lib/dsl/dungeon_kit.py kit_helper).
KIT_HELPER = kit_helper(KIT_CREATURE)

# The wave switch (handoff s3.2, s4.2 row W2-SETUP: wave 1 is the Graveyard and the Library, wave 2 the Armory and the
# Cathedral; the user rules both waves are built before one deploy, and the gate stays so wave 1 can be checked
# alone). Until it flips, the section 3-4 boss files declare nothing: Herod, Mograine and Whitemane keep their stock
# ScriptName, AIName, SmartAI and health, and source/world/dungeons/scarlet_monastery.py holds their heroic overrides
# back too (it reads this line). The C++ twin is kWave2Bound in modules/mod-dungeon-bosses
# src/ScarletMonastery/ScarletMonasteryRework.h; both sides must agree (lib/test_scarlet_monastery_kit.py). W2-SETUP
# flipped both in one commit.
BIND_WAVE_2 = True

# creature_template.flags_extra bits (CreatureData.h): every reworked boss that carries its own encounter credit gets
# INSTANCE_BIND (handoff s3.2 item 2).
FLAGS_EXTRA_INSTANCE_BIND = 0x1

# The encounter credits the instance sends (ScarletMonasteryRework.h kSpellCouncilCredit / kSpellLastStandCredit;
# handoff s3.11 #3): FD-SM's rows name them (creditType 1): the council's new row 1074-1080 block entry and the stock
# row 449 re-pointed to the Last Stand. Declared in instance.py (server-side dummies, never cast).
SPELL_COUNCIL_CREDIT = 212300
SPELL_LAST_STAND_CREDIT = 212301

# Units that must NOT carry INSTANCE_BIND (handoff s3.2 item 2, the BRD ruling: only a unit that carries an
# instance_encounters credit of its own binds): the council's pair (their row is a spell credit the instance sends
# once both are dead) and Mograine (the Last Stand's row 449 is a spell credit sent at his fall; his real death in
# Whitemane's fight gives none). A caller passes `instance_bind=False` to boss_columns() for these entries;
# lib/test_scarlet_monastery_kit.py pins the set against the rows.
NO_INSTANCE_BIND = frozenset({
    6490, 6488,                                 # Azshir the Sleepless, the Fallen Champion
    3976,                                       # Scarlet Commander Mograine
})


def boss_columns(script_name: str, health_modifier: float, *, damage_modifier: float, instance_bind: bool = True,
                 **more) -> dict:
    """The normal-row columns WP-S0's skeleton sets on every reworked stock boss (handoff s3.2 item 4): the C++ script,
    SmartAI off (the S0 SQL rev drops the wave 1 bosses' stock smart_scripts rows; W2-SETUP's rev the wave 2 ones),
    the build spec's normal HealthModifier at 5 players (s3.6), the boss's own DamageModifier (the stock base value:
    the live values on the Fallen Champion are mod-progression leftovers with no upstream update behind them), the
    kit's stun immunity set 1972 (s7 #10: stun, no silence, no interrupt) and INSTANCE_BIND (flags_extra 1;
    `instance_bind=False` for a unit of NO_INSTANCE_BIND: flags_extra 0). `more` adds or overrides columns."""
    return {
        'ScriptName': script_name,
        'AIName': '',
        'HealthModifier': health_modifier,
        'DamageModifier': damage_modifier,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        'flags_extra': FLAGS_EXTRA_INSTANCE_BIND if instance_bind else 0,
        **more,
    }
