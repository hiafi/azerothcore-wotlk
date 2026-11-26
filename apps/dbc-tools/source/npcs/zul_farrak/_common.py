"""
Zul'Farrak build: shared constants for the per-boss declaration files of this package (not loaded on its own: the
leading underscore keeps the package loader from treating it as a declaration file; siblings import it with
`from ._common import ...`). Owned by WP-S0 (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.2 item 8,
s4.1 row S0) until it reports, then by the orchestrator; a boss WP asks for a change here in its report. The visual
ids are WP-V's ._visuals.

The generic part (text masks, attribute bits, targets, the stun immunity set, the boss-kit creature and helper
columns, the spell builders) is the shared dungeon kit, lib/dsl/dungeon_kit.py; this file keeps Zul'Farrak's own
values and the names the boss files import.

Files and owners (one per WP; spell slices in modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h, creature ids
in its ZfCreatures enum, gameobject ids in ZfGameObjects; ids.yaml reservation `zul_farrak`):

  instance.py                 S0    spells 213840-213841 (the Pyramid's and the crew's encounter credits)
  theka.py                    D1    spells 213860-213889, creatures 301005-301007
  antusul.py                  D2    spells 213890-213919 (the Servant 8156 is stock)
  zumrah.py                   D3    spells 213920-213959, creatures 301010-301013
  sandfury_executioner.py     D4a   spells 213960-213989, creature 301019 (with D4b)
  pyramid_stair.py            D4b   spells 213990-214029, creatures 301015-301018 (Sezz'ziz 7275, Nekrum 7796)
  bly_crew_fight.py           D5    spells 214030-214069 (gameobjects 301360, 301361: hand SQL in D5's rev)
  ukorz.py                    D6    spells 214070-214109, creatures 301025-301026
  gahzrilla.py                D7    spells 214110-214149, creature 301030
  gahzrilla_crew_hard_mode.py D7Ha  spells 214150-214189, creature 301031
  gahzrilla_deluge.py         D7Hb  spells 214190-214209, creature 301033 (301032, the second head: D7Ha)
  dungeon_quests.py           Q     creature 301090 (the entrance goblin)
  The crew (7604-7608) are CR's: their script names and AIName are the S0 SQL rev's (rev_skeleton_zul_farrak.sql),
  their type_flags and texts CR's rev; CR's ally-kit spells 213845-213859 are in the shared slice.
  shared spells 213842-213844 (213842 reserved: a script-applied Weakened copy), spare spells 214210-214239, spare
  creatures 301008-301009, 301014, 301020-301024, 301027-301029, 301034-301089, 301091-301099, spare gameobjects
  301362-301379: ask the orchestrator. The gear's `zul_farrak_items` reservation (213800-213839, 301000-301004) is
  source/items/zul_farrak*.py and npcs/zul_farrak/hard_mode_items.py; its spell script names `spell_zf_*` are taken
  (spell_zf_static_discharge among them).

A boss-kit combat add listed in source/world/dungeons/zul_farrak.py's `extra=` (WP-H: the specialists 301015-301017
and the Wellspring 301031) gets its heroic template in the same run (lib/dungeon_heroic.py with_declared_templates),
and its full creature_template() row must name that heroic entry itself: `difficulty_entry_1` = its id in
source/world/heroic_ids.lock (generate.py --check prints it when missing). Stalkers, helpers and the goblin get none.

Not flex: the 5-player values are the template values (HealthModifier on the normal rows, WP-H's heroic overrides).
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

# Zul'Farrak's factions (read-only SELECTs 2026-11-25): the Sandfury 37 (Theka, the Executioner, Sezz'ziz, Nekrum,
# Ukorz, Ruuzlu, Velratha and the trolls), Antu'sul and Gahz'rilla 107, Zum'rah 35 until area trigger 962 (then 37),
# the crew 35 (caged), 495 (allies), 41 (hostile).
FACTION_SANDFURY = 37
FACTION_BEAST = 107
FACTION_FRIENDLY = 35
FACTION_CREW_ALLY = 495
FACTION_CREW_HOSTILE = 41

# The boss-kit creature columns every new Zul'Farrak creature shares: faction 37, unit_flags2 2048, humanoid, exp 0,
# standing still (MovementType 0: the scripts place and move them), no SmartAI. An add sets its own faction and type.
KIT_CREATURE = kit_creature(faction=FACTION_SANDFURY, type=7)

# Summoned helpers the players never target (stalkers, the puddles, the quicksand): not selectable and not attackable,
# hostile faction 14, no loot, no XP (flags_extra 0x40), no melee (lib/dsl/dungeon_kit.py kit_helper).
KIT_HELPER = kit_helper(KIT_CREATURE)

# creature_template.flags_extra bits (CreatureData.h). Section 7 #23 A: the bosses neither make nor answer assist
# calls, so nothing near them is pulled with them (trash close to them is pre-cleared by the bots). The flags are half
# of it: DONT_CALL_ASSISTANCE stops only the first call (Unit::Attack), and the engine calls again every
# CreatureFamilyAssistancePeriod (3 s) whatever the flag says, so every boss's UpdateAI runs ZulFarrak::NoAssist(me)
# before UpdateVictim() (LESSONS L1; tests/zul_farrak_test.cpp checks every boss file). No IGNORE flag on the crew:
# they help each other (s3.2 item 8), and no boss_columns() for them.
FLAGS_EXTRA_INSTANCE_BIND = 0x00000001
FLAGS_EXTRA_DONT_CALL_ASSISTANCE = 0x02000000
FLAGS_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS = 0x04000000
BOSS_FLAGS_EXTRA = (FLAGS_EXTRA_INSTANCE_BIND | FLAGS_EXTRA_DONT_CALL_ASSISTANCE
                    | FLAGS_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS)

# The aggro radius of every reworked boss (stock 20; the Ragefire precedent 12). Section 3.2 item 8 says "detection
# per boss": a boss WP that needs another passes `detection_range=` to boss_columns.
BOSS_DETECTION_RANGE = 12.0


def boss_columns(script_name: str, health_modifier: float, *, damage_modifier: float, **more) -> dict:
    """The normal-row columns WP-S0's skeleton sets on every reworked boss (handoff s3.2 item 8): the C++ script,
    SmartAI off (rev_skeleton_zul_farrak.sql drops the stock smart_scripts rows), the normal HealthModifier of s3.6
    (s7 #1 A: the spec x1.6), the boss's DamageModifier (stock until T, s7 #44 A for Nekrum and Sezz'ziz), the kit's
    stun immunity set 1972 (stun, no silence, no interrupt), INSTANCE_BIND with both assist flags, and detection range
    12. `more` adds or overrides columns."""
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
