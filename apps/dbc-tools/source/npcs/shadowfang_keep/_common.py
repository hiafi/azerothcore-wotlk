"""
Shadowfang Keep build: shared constants for the per-boss declaration files of this package (not loaded on its own: the
leading underscore keeps the package loader from treating it as a declaration file; siblings import it with
`from ._common import ...`). Owned by WP-K (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.3 item 4); a boss WP asks the orchestrator for a change here.

The generic part (text masks, attribute bits, targets, the stun immunity set, the boss-kit creature and helper
columns, the spell builders) is the shared dungeon kit, lib/dsl/dungeon_kit.py; this file keeps Shadowfang Keep's own
values and the names the boss files import.

Files and owners (one per boss WP; spell slices in modules/mod-dungeon-bosses src/ShadowfangKeep/
ShadowfangKeepRework.h, creature ids in its ShadowfangKeepCreatures enum):

  rethilgore.py            S1   spells 205910-205929, creatures 300500-300502
  razorclaw.py             S2   spells 205930-205944
  baron_silverlaine.py     S3   spells 205945-205964, creatures 300503-300505
  commander_springvale.py  S4   spells 205965-205989, creatures 300506-300508
  odo_the_blindwatcher.py  S5   spells 205990-206009
  deathsworn_captain.py    S6   spells 206010-206019
  fenrus_the_devourer.py   S7   spells 206020-206039 (and the stock 4627's columns)
  wolf_master_nandos.py    S8   spells 206040-206059, creatures 300509-300512
  archmage_arugal.py       S9   spells 206060-206084, creature 300515; the lair prisoners 300513 / 300514
                                (declared by K)
  face_him_alone.py        S10  spells 206085-206089
  hard_mode_items.py       W1   (item variants) creature 300460, the `shadowfang_items` reservation
  shared spells 205900-205909 (K, none declared yet), 300516 strike / visual stalker and the spare 300517-300529:
  ask the orchestrator.

A boss-kit combat add listed in source/world/dungeons/shadowfang_keep.py's `extra=` (WP-H) gets its heroic template in
the same run (lib/dungeon_heroic.py with_declared_templates), and its full creature_template() row must name that heroic
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

# Shadowfang Keep's hostile faction: the worgen and the Shadowfang guards (faction 24 on every boss except the
# Deathsworn Captain and Fenrus, 16; read-only SELECTs 2026-11-06, DB-FACTS s1). Humanoid by default; a boss WP passes
# type= for its beasts (1) and spirits (6).
FACTION_SHADOWFANG = 24

# The boss-kit creature columns every new Shadowfang Keep creature shares: faction 24, unit_flags2 2048, humanoid,
# exp 0, standing still (MovementType 0: the scripts place and move them), no SmartAI.
KIT_CREATURE = kit_creature(faction=FACTION_SHADOWFANG, type=7)

# Summoned helpers the players never target (stalkers, fragments' looks): not selectable and not attackable, hostile
# faction 14, no loot, no XP (flags_extra 0x40), no melee (lib/dsl/dungeon_kit.py kit_helper).
KIT_HELPER = kit_helper(KIT_CREATURE)


def boss_columns(script_name: str, health_modifier: float, **more) -> dict:
    """The normal-row columns WP-K's skeleton sets on every reworked boss (handoff s3.3 item 4): the C++ script, SmartAI
    off (the boss WP's SQL rev drops the stock smart_scripts rows), the build spec's normal HealthModifier (s3.7) and
    the kit's stun immunity set 1972 (s7 #8). `more` adds or overrides columns (Razorclaw's DamageModifier 2.0)."""
    return {
        'ScriptName': script_name,
        'AIName': '',
        'HealthModifier': health_modifier,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        **more,
    }
