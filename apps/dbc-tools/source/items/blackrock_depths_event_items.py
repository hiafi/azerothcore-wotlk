"""
Blackrock Depths build WP-IT: the dungeon's event items (.agents/plans/blackrock-depths-build/
blackrock-depths-build.HANDOFF.md s3.3, s3.7, s7 #15 / #17; designer text
docs/dungeons/blackrock-depths-2-shadowforge-city.md "Loot" (Vault Treasure Bag, Cinder of the Firelord), "Fineous
Darkvire" (the Guzzler rope), "Lord Incendius" Hard mode, and docs/dungeons/blackrock-depths-rework.md rulings 32-36,
43-45, 67, 81-84). WP-IT owns this file. In the `blackrock_depths` scope by its name (source/scopes.yaml convention
items/N_*.py).

The items (the `item` slice 70620-70629 of the `blackrock_depths` reservation, source/ids.yaml):

  70620  Vault Treasure Bag            green, rolled on; opens like the stock Fat Sack of Coins 11937 / Sack of Gems
                                       11938 (Flags 4, a loot item): 20-60 gold and 1 cut rare gem. The Secret Safe
                                       holds two (the loot clock seals them, D9). Normal Vault.
  70623  Vault Treasure Bag (heroic)   the same bag with 2 cut rare gems (the spec's "heroic 2"). An item's loot cannot
                                       know the difficulty it dropped on, so the heroic Vault's bags are this second
                                       entry (D9 fills the Safe with 70620 on normal and 70623 on heroic).
  70621  Cinder of the Firelord        green, rolled on, unique, no bind, non-equippable, consumed on use. Use spell
                                       211260 (spell_brd_cinder_of_the_firelord, D12). Not map-limited: a group may keep
                                       it for a later run (ruling 84).
  70622  Guzzler Rope                  white, non-equippable, consumed on use, Map 230 (it leaves with its owner).
                                       Dropped by Fineous at 100% once per instance (D10). Use spell 211261
                                       (spell_brd_guzzler_rope, D10).

The use spells are declared in source/npcs/blackrock_depths/event_items.py (spells 211260-211269, the event items' slice
of the `blackrock_depths` reservation); every boss script that checks them is the boss WP's (D9 Safe fill and loot
clock, D10 the rope, D12 the Cinder). Where the rows live (memory note dbc-tools-item-support: a custom item above
56806 needs both a server item_dbc row and a client Item.dbc row, or it shows a blank bag icon and cannot be used):
  - the client Item.dbc and the server item_dbc rows: source/items.csv (70620-70623; the item block of a run and the
    patch-Z merge carry them; a scoped run owns them through the `blackrock_depths` reservation's `item` range);
  - the item_template rows, the bags' item_loot_template rows and the stock key edits (Relic Coffer Key 11078 and Dark
    Keeper Key 11197 to green; Relic Coffer Key drop chance 1%): data/sql/updates/pending_db_world/
    rev_event_items_blackrock_depths.sql. Quality is not an Item.dbc field, so the keys need no client patch.

This file declares nothing: it holds EVENT_ITEMS, the one table the SQL rev, source/items.csv and the spells are
checked against (lib/test_blackrock_depths_event_items.py).
"""

# item entry -> column values. `display` is the client display id (the Item.dbc DisplayInfoID); the stock look each
# copies is in `look`. `money` is the item_template min / max money loot in copper (a bag's gold). `gems` is how many
# cut rare gems a bag rolls (each its own roll over the 37 C5 rare cuts, lib/crafting_gems_data.py).
EVENT_ITEMS = {
    70620: dict(
        name='Vault Treasure Bag', klass=15, subclass=0, material=3, display=1168, look='Fat Sack of Coins 11937',
        inventory_type=0, sheath=0, quality=2, flags=4, bonding=0, maxcount=0, stackable=1, item_level=55,
        sell_price=100, map=0, spell=0, charges=0, money=(200000, 600000), gems=1,
        description='The Black Vault\'s spoils, heavy and sealed. Open it for gold and a cut gem.',
    ),
    70621: dict(
        name='Cinder of the Firelord', klass=15, subclass=4, material=-1, display=12736, look='Glowing Ember 6655',
        inventory_type=0, sheath=0, quality=2, flags=0, bonding=0, maxcount=1, stackable=1, item_level=60,
        sell_price=0, map=0, spell=211260, charges=-1, money=(0, 0), gems=0,
        description='A coal of the fire that will not die. Cast it into the lava at Lord Incendius\'s island.',
    ),
    70622: dict(
        name='Guzzler Rope', klass=15, subclass=4, material=-1, display=10301, look='Logging Rope 16743',
        inventory_type=0, sheath=0, quality=1, flags=0, bonding=0, maxcount=1, stackable=1, item_level=55,
        sell_price=0, map=230, spell=211261, charges=-1, money=(0, 0), gems=0,
        description='A coil of climbing rope from the Grim Guzzler\'s supplies. It needs a place to hang.',
    ),
    70623: dict(
        name='Vault Treasure Bag', klass=15, subclass=0, material=3, display=4056, look='Sack of Gems 11938',
        inventory_type=0, sheath=0, quality=2, flags=4, bonding=0, maxcount=0, stackable=1, item_level=60,
        sell_price=100, map=0, spell=0, charges=0, money=(200000, 600000), gems=2,
        description='The Black Vault\'s spoils, heavy and sealed. Open it for gold and two cut gems.',
    ),
}

SPELL_CINDER = 211260   # Cinder of the Firelord's use (D12: spell_brd_cinder_of_the_firelord)
SPELL_ROPE = 211261     # Guzzler Rope's use (D10: spell_brd_guzzler_rope)

# The stock keys (hand SQL only: dbc-tools' item_template() edits stock rows through the item pipeline, and these two
# are no part of it). Quality 2 (green) so the group rolls on them; they still do not bind and stack as before.
STOCK_KEYS = {11078: 'Relic Coffer Key', 11197: 'Dark Keeper Key'}
RELIC_COFFER_KEY_DROP_PCT = 1       # every stock source (ruling 35); the six Dark Keepers drop it at 100 (ruling 36)
DARK_KEEPERS = (9437, 9438, 9439, 9441, 9442, 9443)

# The 37 C5 rare cuts (lib/crafting_gems_data.py RARE_ITEM + index): the bags' gem pool.
RARE_CUT_FIRST, RARE_CUT_LAST = 70720, 70756
