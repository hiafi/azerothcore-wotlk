"""
Blackrock Depths build: shared constants for the per-boss declaration files of this package (not loaded on its own:
the leading underscore keeps the package loader from treating it as a declaration file; siblings import it with
`from ._common import ...`). Owned by WP-S0 (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md
s3.2, s4.1 row S0) until it reports, then by the orchestrator; a boss WP asks for a change here in its report. The
visual ids are WP-V-1 / V-2's ._visuals.

The generic part (text masks, attribute bits, targets, the stun immunity set, the boss-kit creature and helper
columns, the spell builders) is the shared dungeon kit, lib/dsl/dungeon_kit.py; this file keeps Blackrock Depths' own
values and the names the boss files import.

Files and owners (one per boss WP; spell slices in modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h, creature ids in its BrdCreatures enum, gameobject ids in BrdGameObjects;
ids.yaml reservation `blackrock_depths`):

  wave 1, sections 1-2 (bound now, except the Ring's units until D4 / D5 bind them):
  gerstahn.py                 D1   spells 210720-210749
  roccor.py                   D2   spells 210750-210779, creature 300780
  grebmar.py                  D3   spells 210780-210809, creature 300781
  ring_of_law.py              D4   spells 210810-210869 (Grimstone 10096, the wave mobs; unbound until D4)
  ring_champions.py           D5   spells 210870-210959, creatures 300782-300788 (9027-9032 unbound until D5)
  ring_encore.py              D6   spells 210960-211019, creatures 300789-300791, gameobject 301280 (if needed)
  loregrain.py                D7   spells 211020-211049, creature 300792
  stilgiss_verek.py           D8   spells 211050-211089
  vault.py                    D9   spells 211090-211119, creature 300793
  fineous.py                  D10  spells 211120-211139, gameobjects 301282, 301283
  incendius.py                D11  spells 211140-211179, creature 300794
  incendius_hard_mode.py      D12  spells 211180-211229, creature 300795
  baelgar.py                  D13  spells 211230-211259, gameobject 301281
  event_items.py              IT   spells 211260-211269 (the Cinder, the rope, the bag)
  wave 2, sections 3-4 (behind BIND_WAVE_2):
  angerforge.py               D14  spells 211300-211329, creatures 300830-300832, gameobject 301289
  argelmach.py                D15  spells 211330-211369, creatures 300833-300835, 300837, gameobjects 301285-301287
  argelmach_hard_mode.py      D16  spells 211370-211409, creatures 300836, 300838, gameobjects 301284, 301288
  guzzler.py                  D17  spells 211410-211429 (SmartAI copies; no C++)
  hurley.py                   D18  spells 211430-211459, creatures 300839, 300840
  phalanx.py                  D19  spells 211460-211489, creature 300841
  flamelash.py                D20  spells 211490-211519, creature 300842
  the_seven.py                D21  spells 211520-211579
  magmus.py                   D22  spells 211580-211609
  emperor.py                  D23  spells 211610-211659, creatures 300843, 300844
  emperor_hard_mode.py        D24  spells 211660-211709
  shared spells 210700-210719 (kit cast bars, markers), spare spells 211270-211299 (wave 1) and 211710-211999, the
  generic stalkers 300796 (wave 1) and 300845 (wave 2), spare creatures 300797-300827, 300829 and 300846-300879
  (300828 is D12's Hand of Incendius: no heroic template by design, only ever summoned on the heroic hard mode, like
  the generic stalker), gameobjects 301290-301309: ask the orchestrator. The gear's `blackrock_depths_items`
  reservation (206830-206899, 300655-300669) is source/items/blackrock_depths_hard_mode_effects.py's and
  hard_mode_items.py's.

A boss-kit combat add listed in source/world/dungeons/blackrock_depths.py's `extra=` (WP-H) gets its heroic template in
the same run (lib/dungeon_heroic.py with_declared_templates), and its full creature_template() row must name that
heroic entry itself: `difficulty_entry_1` = its id in source/world/heroic_ids.lock (generate.py --check prints it when
missing). Wave 1 adds mint before wave 2 adds (the creature slices above keep every wave 1 id below every wave 2 id).

Not flex (HUB ruling 3): the 5-player values are the template values here (HealthModifier on the normal rows, WP-H's
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

# Blackrock Depths' hostile factions (read-only SELECTs 2026-11-17): the Dark Iron dwarves 54 (most bosses: Gerstahn,
# Grebmar, Loregrain, Stilgiss, Verek, Doomgrip, Fineous, Bael'Gar, Angerforge, Argelmach, Hurley, Flamelash, Magmus,
# the Emperor, Moira), the earth and fire elementals 91 (Roccor, Incendius), the Ring's champions 14 (monster).
FACTION_DARK_IRON = 54
FACTION_ELEMENTAL = 91
FACTION_MONSTER = 14

# The boss-kit creature columns every new Blackrock Depths creature shares: faction 54, unit_flags2 2048, humanoid, exp
# 0, standing still (MovementType 0: the scripts place and move them), no SmartAI. A beast, elemental or mechanical add
# sets its own faction and type (kit_creature(faction=..., type=1, 4 or 9)).
KIT_CREATURE = kit_creature(faction=FACTION_DARK_IRON, type=7)

# Summoned helpers the players never target (stalkers, anchors, markers): not selectable and not attackable, hostile
# faction 14, no loot, no XP (flags_extra 0x40), no melee (lib/dsl/dungeon_kit.py kit_helper).
KIT_HELPER = kit_helper(KIT_CREATURE)

# The wave switch (handoff s3.2, s4.2 row 0-2: wave 1 is sections 1-2, wave 2 sections 3-4; the user rules both waves
# are built before one deploy, s10 #24, and the gate stays so wave 1 can be checked alone). Until it flips, the section
# 3-4 boss files declare nothing: Angerforge, Argelmach, Hurley, Phalanx, Flamelash, the Seven, Magmus and the Emperor
# keep their stock ScriptName, AIName, SmartAI and health, and source/world/dungeons/blackrock_depths.py holds their
# heroic overrides back too (it reads this line). The C++ twin is kWave2Bound in modules/mod-dungeon-bosses
# src/BlackrockDepths/BlackrockDepthsRework.h; both sides must agree (lib/test_blackrock_depths_kit.py). The
# orchestrator flips both in one commit (WP 0-2).
BIND_WAVE_2 = True

# creature_template.flags_extra bits (CreatureData.h): every reworked boss gets INSTANCE_BIND (handoff s3.2 item 2).
FLAGS_EXTRA_INSTANCE_BIND = 0x1

# The stock fire-immune giants' set (handoff s7 #10): the 1972 mechanics set plus the Fire school, the existing
# creature_immunities row 1973 (BRS Emberseer's, live 2026-11-17), on Lord Incendius and Bael'Gar.
IMMUNITY_FIRE_GIANT = 1973


# Units that must NOT carry INSTANCE_BIND: they have no encounter credit of their own (handoff section 10, the
# orchestrator rulings of 2026-11-17: only a unit that carries an instance_encounters credit binds). Moira and the
# High Priestess (the Emperor's list), the Seven's six ghosts besides Anger'rel 9035 (instance_encounters 243 credits
# her), Ribbly and Plugger (their credits 240 and 241 are dropped), Verek (row 233 credits Stilgiss' pair by spell
# 211066), Fineous (234 dropped), Watchman Doomgrip (the Vault has no credit row), the six Ring champions and Theldren
# (the Ring's credit 230 is Grimstone 10096). A caller passes `instance_bind=False` to boss_columns() for these
# entries (Ribbly and Plugger: no flags_extra column at all, the stock 0); lib/test_blackrock_depths_kit.py and
# test_blackrock_depths_heroic.py pin the set against the rows.
NO_INSTANCE_BIND = frozenset({
    8929, 10076,                                # Moira, the High Priestess
    9034, 9036, 9037, 9038, 9039, 9040,         # the Seven besides Anger'rel 9035
    9543, 9499,                                 # Ribbly, Plugger
    9042, 9056, 9476,                           # Verek, Fineous, Doomgrip
    9027, 9028, 9029, 9030, 9031, 9032, 16059,  # the Ring champions, Theldren
    16049, 16052, 16053, 16058,                 # the Encore's other four (R-2-FW MIN-2; their normal rows are live 0)
})


def boss_columns(script_name: str, health_modifier: float, *, damage_modifier: float, instance_bind: bool = True,
                 **more) -> dict:
    """The normal-row columns WP-S0's skeleton sets on every reworked boss (handoff s3.2 item 4): the C++ script,
    SmartAI off (the S0 SQL rev drops the wave 1 bosses' stock smart_scripts rows; WP 0-2's rev the wave 2 ones), the
    build spec's normal HealthModifier at 5 players (s3.6), the boss's own DamageModifier (the stock base value: the
    live ones on Bael'Gar, Incendius, Angerforge, Argelmach, Phalanx, Flamelash, Magmus, the Emperor and Gloom'rel are
    leftovers with no upstream update behind them), the kit's stun immunity set 1972 (s7 #10: stun, no silence, no
    interrupt) and INSTANCE_BIND (flags_extra 1; `instance_bind=False` for a unit of NO_INSTANCE_BIND: flags_extra 0).
    `more` adds or overrides columns (the fire giants' 1973)."""
    return {
        'ScriptName': script_name,
        'AIName': '',
        'HealthModifier': health_modifier,
        'DamageModifier': damage_modifier,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
        'flags_extra': FLAGS_EXTRA_INSTANCE_BIND if instance_bind else 0,
        **more,
    }
