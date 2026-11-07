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

`step=` is each tier's `item_budget_variant.tier` (R1 N1), the same number for the same step on every ladder:
0 Normal, 1 Heroic, 2 / 3 / 4 the Molten / Draconic / Chthonic Empowered tiers. The hard mode ladder starts at Heroic,
so its steps are 1-4 too, and the empowered module (E5) looks both ladders up as (base entry, step).
"""

from lib.dsl.items import Quality, ladder, tier

REQUIRED_LEVEL = 60  # every Heroic and Empowered tier needs level 60 (the dungeon is a level 60 heroic)
HARD_MODE_SUFFIX = " Hard Mode"

EPIC = Quality.EPIC
HM = HARD_MODE_SUFFIX

# Effect scaling (IV10 per-tier copies, wave 1 integration 2026-11-06; user intent: effects scale with item level like the
# item's stats): a `scale="budget"` effect's declared numbers are the Heroic tier's (66 Epic). The Normal tier, at each
# item's own stock level, gets a copy scaled down by budget(normal) / budget(66), the empowered tiers copies scaled up.
VANILLA_DUNGEON = ladder(
    "vanilla_dungeon",
    effect_reference="heroic",
    # Normal: the dungeon at its stock level range. Level, quality (Rare) and required level are the item's own.
    normal=tier(step=0, label="Normal", sockets=False),  # user 2026-11-06: sockets from heroic up
    heroic=tier(step=1, ilvl=66, quality=EPIC, required_level=REQUIRED_LEVEL, heroic_flag=True, label="Heroic"),
    empowered_1=tier(step=2, ilvl=76, quality=EPIC, required_level=REQUIRED_LEVEL, label="Molten Empowered"),
    empowered_2=tier(step=3, ilvl=86, quality=EPIC, required_level=REQUIRED_LEVEL, label="Draconic Empowered"),
    empowered_3=tier(step=4, ilvl=96, quality=EPIC, required_level=REQUIRED_LEVEL, label="Chthonic Empowered"),
)

# Hard mode bonus list: separate items (not variants of the heroic list), no Heroic flag (decision 2), so every tier
# gets a label of its own. It starts at Heroic, so its first step is 1. Effects are declared at its 71 tier.
VANILLA_HARD_MODE = ladder(
    "vanilla_hard_mode",
    effect_reference="heroic_hm",
    heroic_hm=tier(step=1, ilvl=71, quality=EPIC, required_level=REQUIRED_LEVEL, label="Heroic" + HM),
    empowered_1_hm=tier(step=2, ilvl=81, quality=EPIC, required_level=REQUIRED_LEVEL, label="Molten Empowered" + HM),
    empowered_2_hm=tier(step=3, ilvl=91, quality=EPIC, required_level=REQUIRED_LEVEL, label="Draconic Empowered" + HM),
    empowered_3_hm=tier(step=4, ilvl=101, quality=EPIC, required_level=REQUIRED_LEVEL, label="Chthonic Empowered" + HM),
)
