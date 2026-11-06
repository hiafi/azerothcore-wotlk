"""
Loot ladders for dungeon items (item variants plan v2, sections 3 and 8, stage IV5).

A ladder is the tiers one item climbs. The first tier of a ladder takes the item's own level: the stock row of a
`base=` item, or the `ilvl=` / `quality=` / `required_level=` of a new one. Every other tier gives all three.
Tier names are the lock file's tier column (`item_ids.lock`): a shipped name never changes. Labels are the green
tooltip line under the item name; the Heroic tier carries the stock Heroic flag (0x8), which the client prints
itself, so it has no label table entry.

Tier item levels (user ruling 2026-11-06): the vanilla dungeon ladder is Normal at the item's stock level (Rare),
Heroic 66 (Epic), then three empowered steps at 76, 86 and 96. Hard mode items are a separate list with their own
ladder one half step above: 71, 81, 91, 101. The empowered tiers are minted now, not deferred (decision 3); their loot
wiring belongs to the empowered stage (dungeon-difficulties E4/E5).

"Chthonic" spelling confirmed by the user 2026-11-06. Normal tiers carry no sockets (user 2026-11-06).
"""

from lib.dsl.items import Quality, ladder, tier

REQUIRED_LEVEL = 60  # every Heroic and Empowered tier needs level 60 (the dungeon is a level 60 heroic)
HARD_MODE_SUFFIX = " Hard Mode"

VANILLA_DUNGEON = ladder(
    "vanilla_dungeon",
    # Normal: the dungeon at its stock level range. Level, quality (Rare) and required level are the item's own.
    normal=tier(label="Normal", sockets=False),  # user 2026-11-06: sockets from heroic up
    heroic=tier(ilvl=66, quality=Quality.EPIC, required_level=REQUIRED_LEVEL, heroic_flag=True, label="Heroic"),
    empowered_1=tier(ilvl=76, quality=Quality.EPIC, required_level=REQUIRED_LEVEL, label="Molten Empowered"),
    empowered_2=tier(ilvl=86, quality=Quality.EPIC, required_level=REQUIRED_LEVEL, label="Draconic Empowered"),
    empowered_3=tier(ilvl=96, quality=Quality.EPIC, required_level=REQUIRED_LEVEL, label="Chthonic Empowered"),
)

# Hard mode bonus list: separate items (not variants of the heroic list), no Heroic flag (decision 2), so every tier
# gets a label of its own.
VANILLA_HARD_MODE = ladder(
    "vanilla_hard_mode",
    heroic_hm=tier(ilvl=71, quality=Quality.EPIC, required_level=REQUIRED_LEVEL, label="Heroic" + HARD_MODE_SUFFIX),
    empowered_1_hm=tier(
        ilvl=81, quality=Quality.EPIC, required_level=REQUIRED_LEVEL, label="Molten Empowered" + HARD_MODE_SUFFIX,
    ),
    empowered_2_hm=tier(
        ilvl=91, quality=Quality.EPIC, required_level=REQUIRED_LEVEL, label="Draconic Empowered" + HARD_MODE_SUFFIX,
    ),
    empowered_3_hm=tier(
        ilvl=101, quality=Quality.EPIC, required_level=REQUIRED_LEVEL, label="Chthonic Empowered" + HARD_MODE_SUFFIX,
    ),
)
