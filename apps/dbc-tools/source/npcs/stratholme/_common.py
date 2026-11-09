"""
Stratholme build: shared constants for the per-boss declaration files of this package (not loaded on its own: the
leading underscore keeps the package loader from treating it as a declaration file; siblings import it with
`from ._common import ...`). Owned by WP-S0 (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.2, s4.1 row
S0) until it reports, then by the orchestrator; a boss WP asks for a change here in its report. The visual ids are
WP-V's ._visuals.

The generic part (text masks, attribute bits, targets, the stun immunity set, the boss-kit creature and helper
columns, the spell builders) is the shared dungeon kit, lib/dsl/dungeon_kit.py; this file keeps Stratholme's own
values and the names the boss files import.

Files and owners (one per boss WP; spell slices in modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h,
creature ids in its StratholmeCreatures enum, gameobject ids in StratholmeGameObjects):

  wave 1, the Service Entrance (bound now):
  magistrate_barthilas.py     S9   spells 206605-206624, creatures 300580-300581
  baroness_anastari.py        S10  spells 206625-206644
  nerubenkan.py               S11  spells 206645-206664, creatures 300582-300583 (and the scarab 10876's columns)
  maleki_the_pallid.py        S12  spells 206665-206684, creatures 300584-300585
  ramstein_the_gorger.py      S13  spells 206685-206704, creatures 300586-300587 (and the meat 11030's columns)
  baron_rivendare.py          S14  spells 206705-206719, creature 300588, gameobject 301207 (and 11197's columns)
  baron_hard_mode.py          S15  spells 206720-206734, creature 300589 (Ysida, Risen)
  wave 2, the Main Gate (behind BIND_WAVE_2):
  the_unforgiven.py           S1   spells 206420-206439, creatures 300600-300601 (and the phantom 10387's columns)
  hearthsinger_forresten.py   S2   spells 206440-206459, creatures 300602-300603
  timmy_the_cruel.py          S3   spells 206460-206479, creature 300604
  malor_the_zealous.py        S4   spells 206480-206499, creature 300605
  cannon_master_willey.py     S5   spells 206500-206519, gameobjects 301200-301202 (and the rifleman 11054's columns)
  archivist_galford.py        S6   spells 206520-206544, creatures 300606-300607
  dathrohan_balnazzar.py      S7   spells 206545-206574, creature 300608
  balnazzar_hard_mode.py      S8   spells 206575-206604, creature 300609, gameobjects 301203-301206, relic items
                                   70600-70603 (source/items/stratholme_relics.py)
  shared spells 206400-206419 (shared.py: 206400 Crossed the Line, the lethal walls' strike; Terrified and shared
  cast bars spare), spare spells
  206735-206799, creatures 300590-300599 (wave 1) and 300611-300649 (wave 2; 300610 is Willey's glow stalker),
  gameobjects 301208-301249: ask the
  orchestrator. The W1 dungeon items' `stratholme_items` reservation (205660-205699, 300470-300474) is
  source/items/stratholme_hard_mode_effects.py's.

A boss-kit combat add listed in source/world/dungeons/stratholme.py's `extra=` (WP-H) gets its heroic template in the
same run (lib/dungeon_heroic.py with_declared_templates), and its full creature_template() row must name that heroic
entry itself: `difficulty_entry_1` = its id in source/world/heroic_ids.lock (generate.py --check prints it when
missing). Wave 1 adds mint before wave 2 adds (the creature slices above keep every wave 1 id below every wave 2 id).
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

# Stratholme's two hostile factions (read-only SELECTs 2026-11-09): the Scourge side, 21 (Barthilas, the ziggurat
# bosses, Ramstein, the Baron, The Unforgiven, Timmy, the meat and the skeletons; undead), and the Scarlet Crusade, 67
# (Malor, Willey, Galford, Dathrohan, the riflemen; humanoid). Forresten is 7.
FACTION_SCOURGE = 21
FACTION_SCARLET = 67

# The boss-kit creature columns every new Stratholme creature shares: faction 21, unit_flags2 2048, undead, exp 0,
# standing still (MovementType 0: the scripts place and move them), no SmartAI. A Scarlet add (a Main Gate boss's)
# takes KIT_CREATURE_SCARLET (faction 67, humanoid).
KIT_CREATURE = kit_creature(faction=FACTION_SCOURGE, type=6)
KIT_CREATURE_SCARLET = kit_creature(faction=FACTION_SCARLET, type=7)

# Summoned helpers the players never target (stalkers, anchors, markers): not selectable and not attackable, hostile
# faction 14, no loot, no XP (flags_extra 0x40), no melee (lib/dsl/dungeon_kit.py kit_helper).
KIT_HELPER = kit_helper(KIT_CREATURE)

# The wave switch (handoff s10: wave 1 is the Service Entrance, wave 2 the Main Gate; the Scholomance pattern). Until it
# flips, the Main Gate boss files declare nothing: The Unforgiven, Forresten, Timmy, Malor, Willey, Galford, Dathrohan
# and Balnazzar keep their stock ScriptName, AIName, SmartAI and health, and source/world/dungeons/stratholme.py holds
# their heroic overrides back too (it reads this line). The C++ twin is kWave2Bound in modules/mod-dungeon-bosses
# src/Stratholme/StratholmeRework.h; both sides must agree (lib/test_stratholme_kit.py). The orchestrator flips both
# in one commit at wave 2's setup (WP 0-2).
BIND_WAVE_2 = True

# creature_template.flags_extra bits (CreatureData.h): no stock Stratholme boss has INSTANCE_BIND (handoff s2.3);
# Maleki keeps his stock CREATURE_FLAG_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS.
FLAGS_EXTRA_INSTANCE_BIND = 0x1
FLAGS_EXTRA_MALEKI_STOCK = 0x4000000

# The Baron keeps his stock immunity set (stun, interrupt and silence immune; handoff s7 #3): never 1972.
IMMUNITY_BARON_STOCK = -419


def boss_columns(script_name: str, health_modifier: float, *, damage_modifier: float, **more) -> dict:
    """The normal-row columns WP-S0's skeleton sets on every reworked boss (handoff s3.2 item 3): the C++ script,
    SmartAI off (the boss WP's SQL rev drops the stock smart_scripts rows), the build spec's normal HealthModifier
    (s3.6), the boss's own DamageModifier (the live values are partly mod-progression leftovers, s2.3), the kit's stun
    immunity set 1972 (s7 #3) and INSTANCE_BIND (flags_extra 1). `more` adds or overrides columns (the Baron's -419,
    Maleki's flags_extra)."""
    return {
        'ScriptName': script_name,
        'AIName': '',
        'HealthModifier': health_modifier,
        'DamageModifier': damage_modifier,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        'flags_extra': FLAGS_EXTRA_INSTANCE_BIND,
        **more,
    }
