"""
The stock quivers and ammo pouches become plain bags (hunter-rework Q4, SHARED C7.3 step 4).

With no ammo (the no-ammo aura, SHARED C2) nobody carries arrows or bullets, so a Quiver (class 11, subclass 2)
or Ammo Pouch (class 11, subclass 3) can only hold nothing: its `BagFamily` 1/2 limits it to ammo. Each of the
33 real ones goes to class 1 (Container), subclass 0, `BagFamily` 0, a plain bag; `InventoryType` 18 and
`ContainerSlots` are unchanged.

Two halves, both needed: this file edits `item_template`, and `source/items.csv` carries the matching
`Item.dbc` rows (class 1, subclass 0, stock row otherwise) into `item_dbc` and the client patch. The server
resets `item_template` class/subclass from `Item.dbc` at boot (`DBC.EnforceItemAttributes`, default on;
ObjectMgr.cpp), so an `item_template` edit alone would be undone at the next start, and the client reads
class/subclass from its own `Item.dbc`. `lint.check_item_dbc_consistency` warns when the two disagree.

Excluded: 29889 (NPC equipment "NPC Equip 29889", 0 slots; nobody carries it).

Prices (user 2026-11-05, progression-slim PS7): as plain bags the vendor quivers undercut real bags (a 10-slot
Medium Quiver cost 10s against the Heavy Brown Bag's 2g). Every quiver or pouch a vendor sells for gold costs what the
stock vendor bag with the same slot count costs: 6 slots Small Brown Pouch 5s, 8 Brown Leather Satchel 25s, 10 Heavy
Brown Bag 2g, 14 Draenic Leather Pack 12g. SellPrice stays stock. Left alone: the Alterac Valley quivers (marks), the
Outland reputation quivers, and the crafted and dropped ones nobody sells.
"""

from lib.dsl.registry import item_template

QUIVER_ENTRIES = (
    1281, 2002, 2003, 2101, 2102, 2662, 2663, 3573, 3574, 3604, 3605, 5439, 5441, 7278, 7279, 7371, 7372,
    8217, 8218, 11362, 11363, 18714, 19319, 19320, 29118, 29143, 29144, 34099, 34100, 34105, 34106, 44447,
    44448,
)

# entry: BuyPrice in copper
VENDOR_BAG_PRICES = {
    2101: 500,      # Light Quiver, 6 slots (stock 4c)
    2102: 500,      # Small Ammo Pouch, 6 slots (stock 4c)
    5439: 2500,     # Small Quiver, 8 slots (stock 1s)
    5441: 2500,     # Small Shot Pouch, 8 slots (stock 10s)
    11362: 20000,   # Medium Quiver, 10 slots (stock 10s)
    11363: 20000,   # Medium Shot Pouch, 10 slots (stock 10s)
    7371: 120000,   # Heavy Quiver, 14 slots (stock 20s)
}

for _entry in QUIVER_ENTRIES:
    _columns = {"class": 1, "subclass": 0, "BagFamily": 0}
    if _entry in VENDOR_BAG_PRICES:
        _columns["BuyPrice"] = VENDOR_BAG_PRICES[_entry]
    item_template(_entry, **_columns)
