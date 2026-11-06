"""
The Deadmines (map 36). Dungeon difficulties E1: the heroic proof - a level 60 heroic with the stock 5-man heroic
lockout (one day) and the Utgarde Keep message mask and difficulty name, entered at level 60 or above. E2 (WP-T2):
the heroic boss list (DungeonEncounter 1000-1006 copy the normal 161-167, Rhahk'Zor 644 .. Edwin VanCleef 639, with
their kill credit) and every spawn on heroic. E1's WP-1D SQL already set spawnMask 3 on all 213 creature and 46
gameobject spawns, so the spawnMask emitter has nothing to add here. E2 (WP-G): every creature of the dungeon (the
generated `CREATURES` block, from apps/dbc-tools/extract_dungeon_creatures.py; never edit inside the markers) and a
level 60 heroic template for each hostile one (lib/heroic_templates.py: the vanilla tier table, the overrides below),
with difficulty_entry_1 on the normal rows and the side-table copies (T2).

MapDifficulty 1000, dungeon_access_template 122 and DungeonEncounter 1000-1006 are the first ids of their blocks
(source/ids.yaml); the heroic creature ids live in source/world/heroic_ids.lock. Never move any of them once shipped.
"""

from lib.dsl.dungeon import creature, dungeon, heroic

# BEGIN GENERATED CREATURES (extract_dungeon_creatures.py) - do not edit inside this block by hand
CREATURES = (
    creature(639, "Edwin VanCleef", "boss", spawns=1),  # L20 elite warrior
    creature(643, "Sneed", "boss", summoned_by=("creature 642 smart cast 5141",)),  # L20 elite warrior
    creature(644, "Rhahk'Zor", "boss", spawns=1),  # L19 elite warrior
    creature(645, "Cookie", "boss", spawns=1),  # L20 elite warrior
    creature(646, "Mr. Smite", "boss", spawns=1),  # L20 elite warrior
    creature(647, "Captain Greenskin", "boss", spawns=1),  # L20 elite warrior
    creature(1763, "Gilnid", "boss", spawns=1),  # L20 elite warrior
    creature(598, "Defias Miner", "trash", spawns=46),  # L17-18 normal warrior
    creature(622, "Goblin Engineer", "trash", spawns=6),  # L18-19 elite warrior
    creature(634, "Defias Overseer", "trash", spawns=12),  # L17-18 elite warrior
    creature(636, "Defias Blackguard", "trash", spawns=4, summoned_by=(  # L19 elite warrior
        "creature 639 smart cast 5200",
    )),
    creature(641, "Goblin Woodcarver", "trash", spawns=13),  # L18-19 elite warrior
    creature(642, "Sneed's Shredder", "trash", spawns=1),  # L20 elite warrior
    creature(657, "Defias Pirate", "trash", spawns=21),  # L19-20 elite warrior
    creature(1725, "Defias Watchman", "trash", spawns=2),  # L15-17 normal warrior
    creature(1729, "Defias Evoker", "trash", spawns=10),  # L17-18 elite mage
    creature(1731, "Goblin Craftsman", "trash", spawns=13),  # L18-19 elite warrior
    creature(1732, "Defias Squallshaper", "trash", spawns=19, summoned_by=(  # L19 elite mage
        "gameobject 16398 actionlist 1639800",
    )),
    creature(2520, "Remote-Controlled Golem", "trash", summoned_by=(  # L18-19 elite warrior
        "creature 622 smart cast 3605",
    )),
    creature(3450, "Defias Companion", "trash", summoned_by=("creature 657 smart cast 5172",)),  # L14-15 normal warrior
    creature(3586, "Miner Johnson", "trash", spawns=1),  # L19 rare elite warrior
    creature(3947, "Goblin Shipbuilder", "trash", spawns=16),  # L19-20 elite warrior
    creature(4416, "Defias Strip Miner", "trash", spawns=27),  # L18-19 normal warrior
    creature(4417, "Defias Taskmaster", "trash", spawns=3, summoned_by=(  # L18-19 elite warrior
        "gameobject 17155 smart",
    )),
    creature(4418, "Defias Wizard", "trash", spawns=2),  # L18-19 elite mage
    creature(4075, "Rat", "critter", spawns=11),  # L1 normal warrior
)
# END GENERATED CREATURES

deadmines = dungeon(
    36, "Deadmines",
    creatures=CREATURES,
    # Sneed's Shredder (the fight's first phase; Sneed rides it) and Miner Johnson (the rare elite) have no encounter
    # row, but docs/dungeons/deadmines-rework.md builds both as bosses: the boss tier and INSTANCE_BIND on heroic.
    roles={642: "boss", 3586: "boss"},
    heroic=heroic(
        map_difficulty_id=1000, access_id=122, min_level=60,
        encounter_ids=range(1000, 1007),  # Rhahk'Zor, Sneed, Gilnid, Mr. Smite, Cookie, Captain Greenskin, VanCleef
        spawn_mask=True,
        # Heroic health from the dungeon doc's build specs (approved; its "Unit | Entry | Normal | Heroic" tables).
        # The doc names no heroic melee, so every creature takes the tier's. Its new boss-kit adds (Watchman and
        # Evoker 80k, Blackguard 40k, Working Miner 30k) are new entries, declared when those bosses are built.
        overrides={
            639: dict(health=340_000),  # Edwin VanCleef (the hard mode's 500k is set by his script)
            642: dict(health=220_000),  # Sneed's Shredder
            643: dict(health=142_000),  # Sneed
            644: dict(health=320_000),  # Rhahk'Zor
            645: dict(health=330_000),  # Cookie
            646: dict(health=472_000),  # Mr. Smite
            647: dict(health=377_000),  # Captain Greenskin
            1763: dict(health=311_000),  # Gilnid
            3586: dict(health=240_000),  # Miner Johnson
        },
    ),
)
