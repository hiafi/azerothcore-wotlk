"""
Gnomeregan build: shared constants for the per-boss declaration files of this package (not loaded on its own: the
leading underscore keeps the package loader from treating it as a declaration file; siblings import it with
`from ._common import ...`). Owned by WP-S0 (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.2 item 8,
s4.1 row S0) until it reports, then by the orchestrator; a boss WP asks for a change here in its report. The visual
ids are WP-V's ._visuals.

The generic part (text masks, attribute bits, targets, the stun immunity set, the boss-kit creature and helper
columns, the spell builders) is the shared dungeon kit, lib/dsl/dungeon_kit.py; this file keeps Gnomeregan's own
values and the names the boss files import.

Files and owners (one per WP; spell slices in modules/mod-dungeon-bosses src/Gnomeregan/GnomereganRework.h, creature
ids in its GnomereganCreatures enum, gameobject ids in GnomereganGameObjects; ids.yaml reservation `gnomeregan`):

  instance.py                          S0    the shared slice 214280-214299 (214280 reserved: a Weakened copy)
  techbot.py                           D1    spells 214300-214339, creatures 301105-301107 (S0 declared 301105)
  viscous_fallout.py                   D2    spells 214340-214379, creature 301130
  electrocutioner.py                   D3    spells 214380-214419, creature 301132
  mobile_alert_system.py               D4    spells 214420-214459, creatures 301110-301113 (S0 declared 301110)
  crowd_pummeler.py                    D5    spells 214460-214489, creature 301115 (gameobjects 301380, 301381:
                                             hand SQL in D5's rev)
  thermaplugg.py                       D6    spells 214490-214539, creatures 301120-301127
  thermaplugg_hard_mode.py             D6Ha  spells 214540-214579 and the console's 214620-214639, creatures 301135,
                                             301137, 301138 (gameobject 301382: hand SQL in D6Ha's rev)
  thermaplugg_hard_mode_machines.py    D6Hb  spells 214580-214619, creature 301136
  dungeon_quests.py                    Q     creature 301190 (the exile)
  The gear's `gnomeregan_items` reservation (214240-214279, 301100-301104) is source/items/gnomeregan*.py and
  npcs/gnomeregan/hard_mode_items.py; its spell script names `spell_gnomer_item_*` and its namespace
  GnomereganHardModeItems are taken. Spare spells 214640-214679, spare creatures (301108-301109, 301114,
  301116-301119, 301128-301129, 301131, 301133-301134, 301139-301189, 301191-301199), spare gameobjects
  301383-301399: ask the orchestrator.

A new boss or boss-kit combat add listed in source/world/dungeons/gnomeregan.py's `extra=` (301105, 301106, 301110,
301111, 301112, 301120-301124: `HEROIC_PREDICTED` below) gets its heroic template in the same run (lib/dungeon_heroic.py
with_declared_templates), and its full creature_template() row must name that heroic entry itself:
`difficulty_entry_1` = heroic_entry(<entry>) (generate.py --check prints it when missing). Stalkers, helpers nobody
targets (the Lag Echo, the puddles, the fist, the room alarm) and the exile get none: they run on their normal entry.

Not flex: the 5-player values are the template values (HealthModifier on the normal rows, WP-H's heroic overrides).
"""

from pathlib import Path

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

# Gnomeregan's factions (read-only SELECTs 2026-11-26): 63 the stock mechanical bosses and trash (Techbot 6231,
# Electrocutioner, Pummeler, Thermaplugg, the Mobile Alert System, the Walking Bomb), 91 Viscous Fallout. Never 494 on
# a Dupe Bug: it is hostile to Techbot's own faction (FACTS-STOCK flag 20). The exile is 35 (Q).
FACTION_GNOMEREGAN_MECHANICAL = 63
FACTION_VISCOUS_FALLOUT = 91
FACTION_FRIENDLY = 35

TYPE_ELEMENTAL = 4
TYPE_MECHANICAL = 9

# The boss-kit creature columns every new Gnomeregan creature shares: faction 63, mechanical, unit_flags2 2048, exp 0,
# standing still (MovementType 0: the scripts place and move them), no SmartAI. An add sets its own faction and type.
KIT_CREATURE = kit_creature(faction=FACTION_GNOMEREGAN_MECHANICAL, type=TYPE_MECHANICAL)

# Summoned helpers the players never target (stalkers, the puddles, the fist): not selectable and not attackable,
# hostile faction 14, no loot, no XP (flags_extra 0x40), no melee (lib/dsl/dungeon_kit.py kit_helper).
KIT_HELPER = kit_helper(KIT_CREATURE)

# creature_template.flags_extra bits (CreatureData.h). Section 3.2 item 8: the bosses neither make nor answer assist
# calls, so nothing near them is pulled with them (trash close to them is pre-cleared by the bots). The flags are half
# of it: DONT_CALL_ASSISTANCE stops only the first call (Unit::Attack), and the engine calls again every
# CreatureFamilyAssistancePeriod (3 s) whatever the flag says, so every boss's UpdateAI runs
# GnomereganRework::NoAssist(me) before UpdateVictim() (LESSONS L1; tests/gnomeregan_test.cpp checks every boss file).
FLAGS_EXTRA_INSTANCE_BIND = 0x00000001
FLAGS_EXTRA_DONT_CALL_ASSISTANCE = 0x02000000
FLAGS_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS = 0x04000000
BOSS_FLAGS_EXTRA = (FLAGS_EXTRA_INSTANCE_BIND | FLAGS_EXTRA_DONT_CALL_ASSISTANCE
                    | FLAGS_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS)

# The aggro radius of every reworked boss (stock 20; the Ragefire and Zul'Farrak precedent 12). A boss WP that needs
# another passes `detection_range=` to boss_columns.
BOSS_DETECTION_RANGE = 12.0

# The stock boss melee multiplier at level 28 (section 3.6: unchanged by the spec until T).
BOSS_DAMAGE_MODIFIER = 1.7

# The heroic entries the first write run mints for the build's units (source/world/dungeons/gnomeregan.py `_HEROIC_ID`,
# the lock's mint order: the 32 stock entries 310543-310574, then these in entry order; INT reconcile 2026-11-26).
# lib/test_gnomeregan_heroic.py pins the two tables together and every row to its id. Never move one once shipped.
HEROIC_PREDICTED = {
    301105: 310575,     # Techbot
    301106: 310576,     # Dupe Bug
    301110: 310577,     # The Mobile Alert System
    301111: 310578,     # Security Assistant
    301112: 310579,     # Security Defender
    301120: 310580,     # Walking Bomb
    301121: 310581,     # Incendiary Bomb
    301122: 310582,     # Frost Bomb
    301123: 310583,     # Radioactive Bomb
    301124: 310584,     # The Big One (not attackable but selectable: a level 60 copy reads right on mouseover)
}


def heroic_entry(entry: int) -> int:
    """The heroic entry of a build unit for its `difficulty_entry_1`: its line in source/world/heroic_ids.lock
    ("<normal> <heroic> <map> <name>") once a write run has minted it, else `HEROIC_PREDICTED`."""
    lock = Path(__file__).resolve().parents[2] / 'world' / 'heroic_ids.lock'
    if lock.exists():
        for line in lock.read_text(encoding='utf-8').splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == str(entry) and parts[1].isdigit():
                return int(parts[1])
    return HEROIC_PREDICTED[entry]


def boss_columns(script_name: str, health_modifier: float, *, damage_modifier: float = BOSS_DAMAGE_MODIFIER,
                 **more) -> dict:
    """The normal-row columns WP-S0's skeleton sets on every reworked boss (handoff s3.2 item 8): the C++ script,
    SmartAI off (rev_skeleton_gnomeregan.sql drops the stock smart_scripts rows), the normal HealthModifier of s3.6
    (s7 #1 A: the spec x2.0 on the level 28 warrior base 853), the boss's DamageModifier (stock 1.7 until T), the kit's
    stun immunity set 1972 (stun, no silence, no interrupt; section 7 #11 A), INSTANCE_BIND with both assist flags,
    and detection range 12. `more` adds or overrides columns."""
    return {
        'ScriptName': script_name,
        'AIName': '',
        'HealthModifier': health_modifier,
        'DamageModifier': damage_modifier,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        'flags_extra': BOSS_FLAGS_EXTRA,
        'detection_range': BOSS_DETECTION_RANGE,
        **more,
    }
