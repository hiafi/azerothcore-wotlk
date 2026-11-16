"""
Blackrock Spire build: shared constants for the per-boss declaration files of this package (not loaded on its own: the
leading underscore keeps the package loader from treating it as a declaration file; siblings import it with
`from ._common import ...`). Owned by WP-S0 (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md
s3.2, s4.1 row S0) until it reports, then by the orchestrator; a boss WP asks for a change here in its report. The
visual ids are WP-V's ._visuals.

The generic part (text masks, attribute bits, targets, the stun immunity set, the boss-kit creature and helper
columns, the spell builders) is the shared dungeon kit, lib/dsl/dungeon_kit.py; this file keeps Blackrock Spire's own
values and the names the boss files import.

Files and owners (one per boss WP; spell slices in modules/mod-dungeon-bosses src/BlackrockSpire/BlackrockSpireRework.h,
creature ids in its BrsCreatures enum, gameobject ids in BrsGameObjects; ids.yaml reservation `blackrock_spire`):

  wave 1, Lower Blackrock Spire (bound now):
  omokk.py                    B1   spells 210020-210059, creatures 300700-300702
  voshgajin.py                B2   spells 210060-210089, creature 300703
  voone.py                    B3   spells 210090-210119, creature 300704, gameobject 301250
  smolderweb.py               B4   spells 210120-210149, creature 300705, gameobject 301251
  urok.py                     B5   spells 210150-210179, creature 300706 (the shard, reused by B9)
  zigris.py                   B6   spells 210180-210209, creature 300707, gameobjects 301252-301254
  halycon_gizrul.py           B7   spells 210210-210249
  wyrmthalak.py               B8   spells 210250-210289, creatures 300708-300712
  wyrmthalak_hard_mode.py     B9   spells 210290-210339, gameobject 301255 (the Bloodaxe War Horn)
  wave 2, Upper Blackrock Spire (behind BIND_WAVE_2):
  emberseer.py                B10  spells 210350-210389, creature 300730
  solakar.py                  B11  spells 210390-210429, creature 300731 (and the item 13371 toss)
  rend_gyth.py                B12  spells 210430-210489, creatures 300732-300734 (the Nefarius copy, Banner, wall)
  the_beast.py                B13  spells 210490-210519, creature 300735
  drakkisath.py               B14  spells 210520-210559
  drakkisath_hard_mode.py     B15  spells 210560-210619, creatures 300736-300741
  shared spells 210000-210019 (kit cast bars, flex markers), spare spells 210340-210349 and 210620-210699, the generic
  stalker 300713, spare creatures 300714-300729 (wave 1) and 300742-300779 (wave 2), gameobjects 301256-301279: ask
  the orchestrator. The gear's `blackrock_spire_items` reservation (206800-206829, 300650-300654) is
  source/items/blackrock_spire_hard_mode_effects.py's.

A boss-kit combat add listed in source/world/dungeons/blackrock_spire.py's `extra=` (WP-H) gets its heroic template in
the same run (lib/dungeon_heroic.py with_declared_templates), and its full creature_template() row must name that
heroic entry itself: `difficulty_entry_1` = its id in source/world/heroic_ids.lock (generate.py --check prints it when
missing). Wave 1 adds mint before wave 2 adds (the creature slices above keep every wave 1 id below every wave 2 id).

Flex (handoff s3.12): the 5-player values are the template values here (HealthModifier on the normal rows, WP-H's
heroic overrides); the scaler in mod-dungeon-difficulties multiplies max health by the ladder at each pull. A boss-kit
add's health is its 5-player value too; FLEX_LADDER is only for the declarations' docstrings and tests.
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

# Blackrock Spire's hostile factions (read-only SELECTs 2026-11-15): the Blackrock orcs, ogres and trolls, 40 (every
# boss but the two below; humanoid), Mother Smolderweb and Solakar 16 (Smolderweb a beast, Solakar a dragonkin), the
# Beast and Nefarius 14.
FACTION_BLACKROCK = 40
FACTION_SPIRE_MONSTER = 16
FACTION_MONSTER = 14

# The boss-kit creature columns every new Blackrock Spire creature shares: faction 40, unit_flags2 2048, humanoid, exp
# 0, standing still (MovementType 0: the scripts place and move them), no SmartAI. A beast or dragonkin add sets its own
# type (kit_creature(faction=..., type=1 or 2)).
KIT_CREATURE = kit_creature(faction=FACTION_BLACKROCK, type=7)

# Summoned helpers the players never target (stalkers, anchors, markers): not selectable and not attackable, hostile
# faction 14, no loot, no XP (flags_extra 0x40), no melee (lib/dsl/dungeon_kit.py kit_helper).
KIT_HELPER = kit_helper(KIT_CREATURE)

# The wave switch (handoff s3.2, s4.2 row 0-2: wave 1 is Lower Blackrock Spire, wave 2 Upper Blackrock Spire). Until it
# flips, the UBRS boss files declare nothing: Emberseer, Solakar, Rend, Gyth, the Beast and Drakkisath keep their stock
# ScriptName, AIName, SmartAI and health, and source/world/dungeons/blackrock_spire.py holds their heroic overrides back
# too (it reads this line). The C++ twin is kWave2Bound in modules/mod-dungeon-bosses
# src/BlackrockSpire/BlackrockSpireRework.h; both sides must agree (lib/test_blackrock_spire_kit.py). The orchestrator
# flips both in one commit at wave 2's setup (WP 0-2).
BIND_WAVE_2 = True

# creature_template.flags_extra bits (CreatureData.h): only the four UBRS finals have INSTANCE_BIND today (handoff
# s2.3); every reworked boss gets it (s3.2 item 2, the Scholomance skeleton).
FLAGS_EXTRA_INSTANCE_BIND = 0x1

# Pyroguard Emberseer's immunity set (handoff s7 #16 A): the 1972 mechanics set plus the Fire school, a new
# creature_immunities row 1973 (WP-0: live max 1972; not an ids.yaml table). B10 ships the row in its SQL rev
# (data/sql/updates/pending_db_world/rev_pyroguard_emberseer_blackrock_spire.sql; dbc-tools has no creature_immunities
# declaration); lib/test_blackrock_spire_emberseer.py checks every immunity set the Blackrock Spire rows name exists.
IMMUNITY_EMBERSEER = 1973

# The flex ladder (handoff s3.12; DD FlexMath.h): max health = the 5-player value x (1 + 0.25 x (N - 5)), N clamped to
# 5..10. Documentation and tests only: the scaler applies it in game.
FLEX_LADDER = {5: 1.00, 6: 1.25, 7: 1.50, 8: 1.75, 9: 2.00, 10: 2.25}


def boss_columns(script_name: str, health_modifier: float, *, damage_modifier: float, **more) -> dict:
    """The normal-row columns WP-S0's skeleton sets on every reworked boss (handoff s3.2 item 3): the C++ script,
    SmartAI off (the S0 SQL rev drops the wave 1 bosses' stock smart_scripts rows; a wave 2 boss WP drops its own), the
    build spec's normal HealthModifier at 5 players (s3.6), the boss's own DamageModifier (the live values are
    mod-progression leftovers, s2.3; the skeleton writes the stock value), the kit's stun immunity set 1972 (s7 #16:
    stun, no silence, no interrupt) and INSTANCE_BIND (flags_extra 1). `more` adds or overrides columns (Emberseer's
    1973)."""
    return {
        'ScriptName': script_name,
        'AIName': '',
        'HealthModifier': health_modifier,
        'DamageModifier': damage_modifier,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        'flags_extra': FLAGS_EXTRA_INSTANCE_BIND,
        **more,
    }
