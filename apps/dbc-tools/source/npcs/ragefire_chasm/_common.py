"""
Ragefire Chasm build: shared constants for the per-boss declaration files of this package (not loaded on its own: the
leading underscore keeps the package loader from treating it as a declaration file; siblings import it with
`from ._common import ...`). Owned by WP-S0 (.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.2
item 5, s4.1 row S0) until it reports, then by the orchestrator; a boss WP asks for a change here in its report. The
visual ids are WP-V's ._visuals.

The generic part (text masks, attribute bits, targets, the stun immunity set, the boss-kit creature and helper
columns, the spell builders) is the shared dungeon kit, lib/dsl/dungeon_kit.py; this file keeps Ragefire Chasm's own
values and the names the boss files import.

Files and owners (one per boss WP; spell slices in modules/mod-dungeon-bosses src/RagefireChasm/RagefireChasmRework.h,
creature ids in its RfcCreatures enum, gameobject ids in RfcGameObjects; ids.yaml reservation `ragefire_chasm`):

  oggleflint.py               D1   spells 213550-213579, creature 300985 (the Borer)
  jergosh.py                  D2   spells 213580-213609, creature 300986 (the Soul Wisp)
  bazzalan.py                 D3   spells 213610-213649
  taragaman.py                D4   spells 213650-213689 (gameobject 301342, the Searing Spike: hand SQL in D4's rev)
  taragaman_hard_mode.py      D4H  spells 213690-213719, creature 300987 (the Blood Globule; gameobjects 301340 and
                                   301341: hand SQL in D4H's rev)
  kit_helpers.py              S0   creature 300988 (the generic visual stalker)
  dungeon_quests.py           Q    creature 300989 (the entrance orc)
  shared spells 213540-213549 (none declared yet), spare spells 213720-213799, spare creatures 300990-300999, spare
  gameobjects 301343-301359: ask the orchestrator. The gear's `ragefire_chasm_items` reservation (213500-213539,
  300980-300984) is source/items/ragefire_chasm*.py; its spell script names `spell_rfc_*` are taken.

A boss-kit combat add listed in source/world/dungeons/ragefire_chasm.py's `extra=` (WP-H: the Blood Globule only) gets
its heroic template in the same run (lib/dungeon_heroic.py with_declared_templates), and its full creature_template()
row must name that heroic entry itself: `difficulty_entry_1` = its id in source/world/heroic_ids.lock (generate.py
--check prints it when missing). The Borer, the wisp, the stalker and the orc get none.

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

# Ragefire Chasm's factions (read-only SELECTs 2026-11-24): the Searing Blade 554 (Jergosh, Bazzalan, Taragaman and the
# cultists), the Ragefire troggs 59 (Oggleflint and his trash), the Earthborers 16.
FACTION_SEARING_BLADE = 554
FACTION_RAGEFIRE_TROGG = 59
FACTION_EARTHBORER = 16

# The boss-kit creature columns every new Ragefire Chasm creature shares: faction 554, unit_flags2 2048, humanoid, exp
# 0, standing still (MovementType 0: the scripts place and move them), no SmartAI. An add sets its own faction and type.
KIT_CREATURE = kit_creature(faction=FACTION_SEARING_BLADE, type=7)

# Summoned helpers the players never target (the Borer, the wisp, stalkers): not selectable and not attackable, hostile
# faction 14, no loot, no XP (flags_extra 0x40), no melee (lib/dsl/dungeon_kit.py kit_helper).
KIT_HELPER = kit_helper(KIT_CREATURE)

# creature_template.flags_extra bits (CreatureData.h). Section 7 #12 A: the four bosses neither make nor answer assist
# calls (cultists at 7.7 to 12.4 yd, the den's trash at 11.5 yd), so nothing near them is pulled with them. The flags
# are half of it: DONT_CALL_ASSISTANCE stops only the first call (Unit::Attack), and the engine calls again every
# CreatureFamilyAssistancePeriod (3 s) whatever the flag says, so every boss's UpdateAI runs
# `me->SetAssistanceTimer(0)` before UpdateVictim() (R-1-FW MAJ-1; lib/test_ragefire_chasm_npcs.py checks the line).
FLAGS_EXTRA_INSTANCE_BIND = 0x00000001
FLAGS_EXTRA_DONT_CALL_ASSISTANCE = 0x02000000
FLAGS_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS = 0x04000000
BOSS_FLAGS_EXTRA = (FLAGS_EXTRA_INSTANCE_BIND | FLAGS_EXTRA_DONT_CALL_ASSISTANCE
                    | FLAGS_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS)

# Section 7 #12 A (stock 20; the Scarlet Monastery precedents are Crell 9 and Halden 10).
BOSS_DETECTION_RANGE = 12.0


def boss_columns(script_name: str, health_modifier: float, *, damage_modifier: float, **more) -> dict:
    """The normal-row columns WP-S0's skeleton sets on every reworked boss (handoff s3.2 item 5): the C++ script,
    SmartAI off (rev_skeleton_ragefire_chasm.sql drops the stock smart_scripts rows), the build spec's normal
    HealthModifier (s3.6), the boss's own DamageModifier (the stock value until T), the kit's stun immunity set 1972
    (stun, no silence, no interrupt), INSTANCE_BIND with both assist flags, and detection range 12. `more` adds or
    overrides columns."""
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
