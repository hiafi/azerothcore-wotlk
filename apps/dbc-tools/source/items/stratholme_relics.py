"""
Stratholme build WP-S8: Balnazzar's hard mode, the Grand Lie: the Letter of Proof and the three relics
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.7, s7 #7, #9, #10; build spec
docs/dungeons/stratholme-rework.md ST 1920-1999 "The relics", ST 2117 HM9). WP-S8 owns this file. In the `stratholme`
scope by its name (source/scopes.yaml convention items/N_*.py).

The four items (hand-picked ids 70600-70603, the `item` block after the Haunted tokens; StratholmeRework.h
StratholmeItems) and their use spells (kSpellsGrandLie 206585-206588, the boss slice: declared in
source/npcs/stratholme/balnazzar_hard_mode.py, since every spell of source/items must sit in an item reservation and
these sit in the boss's; GrandLieLogic.h names the same ids):

  70600  Letter of Proof         206585  Read it to Dathrohan within 30 yd, out of combat, on heroic: the hard mode
                                         (spell_strat_grand_lie_letter). Not consumed (handoff s7 #10).
  70601  Scarlet Standard        206587  A 6 yd ring of light around the user for 5 s; allies inside carry the ward
                                         (its own aura): the Carrion Swarm cones and the moving swarms pass them over;
                                         the bots get a Stack on the ring (spell_strat_grand_lie_standard). 20 s
                                         cooldown.
  70602  Blessed Holy Water      206586  Thrown at a spot within 10 yd: a moving swarm in its 5 yd splash disperses
                                         (spell_strat_grand_lie_holy_water). 3 min cooldown.
  70603  Relic of the Medallion  206588  A 30 yd pulse of faith: wakes every sleeping ally and wards them from sleep
                                         for 4 s (a mechanic immunity; spell_strat_grand_lie_medallion wakes them).
                                         25 s cooldown.

Where the rows live (memory note dbc-tools-item-support: a custom item above 56806 needs both a server item_dbc row
and a client Item.dbc row, or it shows a blank icon and cannot be used):
  - the client Item.dbc and the server item_dbc rows: source/items.csv (70600-70603; the item block of a run and the
    patch-Z merge carry them; a scoped run owns them through the `stratholme` reservation's `item` range);
  - the item_template rows: WP-S8's SQL rev (rev_balnazzar_hard_mode_stratholme.sql: class 15 / 4, Bind on Pickup,
    unique, Map 329 so they work and live in Stratholme only, the use spell with its per-copy cooldown);
  - the dispensers: gameobjects 301203-301206 (go_st_grand_lie_relic, KT-2's RelicDispenserAI), heroic spawns in the
    same rev; a click gives every group member on the map one copy (bots too: they never use them, s7 #9).

This file declares nothing: it holds RELICS, the one table the SQL rev's item_template rows, source/items.csv's Item.dbc
rows and the C++ (GrandLieLogic.h RelicItem) are checked against (lib/test_stratholme_grand_lie.py).

Each copy keeps its own cooldown (ruling 33): the cooldown is the item's (spellcooldown_1), so five players have five
uses of each. Tooltips are number-free (ST checklist item 8).
"""

# The relics: item entry -> (name, client display, use spell, per-copy cooldown ms (-1: none), dispensing gameobject).
# The SQL rev's item_template rows and source/items.csv's Item.dbc rows carry the same values
# (lib/test_stratholme_grand_lie.py).
RELICS = {
    70600: ('Letter of Proof', 3093, 206585, -1, 301203),            # Singed Letter 10443's look
    70601: ('Scarlet Standard', 31257, 206587, 20000, 301204),       # Horde Battle Standard 18607's look (red)
    70602: ('Blessed Holy Water', 23731, 206586, 180000, 301206),    # Stratholme Holy Water 13180's look
    70603: ('Relic of the Medallion', 9857, 206588, 25000, 301205),  # Medallion of Faith 12845's look
}
