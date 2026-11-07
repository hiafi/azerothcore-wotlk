"""
Deadmines Pilot: shared constants for the per-boss declaration files of this package (not loaded on its own: the
leading underscore keeps the package loader from treating it as a declaration file; siblings import it with
`from ._common import ...`). Owned by WP-K (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.2); a boss
WP asks the orchestrator for a change here.

Since WP-K0 the generic part (text masks, attribute bits, targets, the stun immunity set, the boss-kit creature and
helper columns) comes from the shared dungeon kit, lib/dsl/dungeon_kit.py; this file keeps Deadmines' own values
(faction 17, Rhahk'Zor's immunity set) and the names the boss files import. The output is unchanged.

A boss-kit combat add listed in source/world/dungeons/deadmines.py's `extra=` gets its heroic template in the same run
(lib/dungeon_heroic.py with_declared_templates), and its full creature_template() row must name that heroic entry
itself: `difficulty_entry_1` = its id in source/world/heroic_ids.lock (generate.py --check prints it when missing).
"""

from lib.dsl.dungeon_kit import (  # noqa: F401 - re-exported for the boss files
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TEXT_MASKS,
    kit_creature,
    kit_helper,
)

# creature_immunities: every reworked Deadmines boss uses the kit's "-229 + STUN" set (IMMUNITY_BOSS_STUN 1972,
# inserted by WP-K's core rev) except Rhahk'Zor, who keeps -159 (handoff s7 #5).
IMMUNITY_RHAHKZOR = -159

# The boss-kit creature columns every new Deadmines creature shares (the stock Defias rows' values; read-only
# SELECTs 2026-11-06): faction 17 (Defias), unit_flags2 2048, humanoid, exp 0, standing still (MovementType 0: the
# scripts place and move them), no SmartAI.
KIT_CREATURE = kit_creature(faction=17, type=7)

# Summoned helpers the players never target (iron shot, land mine, shadow image, the powder stalker): not selectable
# and not attackable (UNIT_FLAG_NON_ATTACKABLE 0x2 | UNIT_FLAG_NOT_SELECTABLE 0x02000000, the mod-boss-mechanics marker
# precedent), hostile faction 14, no loot, no XP (flags_extra 0x40), no melee (DamageModifier 0).
KIT_HELPER = kit_helper(KIT_CREATURE)
