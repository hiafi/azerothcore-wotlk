"""
Blackrock Spire build WP-B11 (Solakar Flamewreath, SK5), fix part F-2b (R-2 ruling 2026-11-15, review R-2-A B-1 / M-3):
Father Flame, the flame the players toss, is a NEW custom bag item, 70610 (handoff s10 "R-2 rulings"). The stock
item 13371 (an off-hand holdable: the server refuses to use an equippable item from the bags, SpellHandler.cpp
HandleUseItemOpcode) stays untouched as the loot keepsake (it still drops from the chest's loot and the Rookery trash).
WP-B11 / F-2b own this file.

Taking Father Flame 175245 (go_brs_father_flame) gives its taker item 70610 and the holder aura 210390 (the aura shows
the torch, SV_TORCH_HELD); using the item from the bags on an ally within 30 yd throws the flame to them (only the
holder can: the toss's CasterAuraSpell). Bots throw it by PlayerbotAI::ImbueItem (mod-boss-mechanics
PassEntry::WithItem). A player with no free bag slot cannot be thrown to (the toss's CheckCast: "bags full") or pick
the flame up, and the bots skip them as catchers (boss_solakar_flamewreath_rework.cpp FlameRoom).

This file declares nothing (dbc-tools' item_template() only edits existing rows; a new item is a source/items.csv row
plus a hand-written item_template row, the Stratholme relics precedent source/items/stratholme_relics.py). It holds
FATHER_FLAME, the one table the other copies are checked against (lib/test_blackrock_spire_solakar.py):
  - the client Item.dbc and the server item_dbc rows: source/items.csv (70610: class 15 / 4, the stock 13371's display
    24061 and material, InventoryType 0, no sheath; the item block of a run and the patch-Z merge carry them);
  - the item_template row: data/sql/updates/pending_db_world/rev_solakar_flamewreath_blackrock_spire.sql (Bind on
    Pickup, unique, Map 229 so it lives in Blackrock Spire only: the server takes it from anyone who leaves);
  - the C++: BlackrockSpireRework.h kItemFatherFlame.

The id: hand-picked 70610 in the `item` block's hand-picked part (70000-70999), after the Stratholme relics
(70600-70603); checked free 2026-11-15 (no item_template, item_dbc or items.csv row, no pending SQL). An ids.yaml `item`
range for it is a shared-file request (STAGE-F-2b-REPORT.md).
"""

ITEM_FATHER_FLAME = 70610           # BlackrockSpireRework.h kItemFatherFlame
ITEM_FATHER_FLAME_KEEPSAKE = 13371  # the stock off-hand, untouched (loot only)
SPELL_TOSS_FATHER_FLAME = 210391    # SolakarLogic.h SPELL_SK_TOSS
MAP_BLACKROCK_SPIRE = 229

# The item. The SQL rev's item_template row and source/items.csv's Item.dbc row carry the same values.
FATHER_FLAME = {
    'entry': ITEM_FATHER_FLAME,
    'name': 'Father Flame',
    'class': 15,            # Miscellaneous
    'subclass': 4,          # Other
    'material': -1,         # the stock 13371's
    'display': 24061,       # the stock 13371's torch icon
    'inventory_type': 0,    # INVTYPE_NON_EQUIP: used from the bags
    'sheath': 0,
    'spell': SPELL_TOSS_FATHER_FLAME,
    'map': MAP_BLACKROCK_SPIRE,
    'description': 'The stolen flame of the Rookery. It burns the hand that holds it: toss it to an ally.',
}
