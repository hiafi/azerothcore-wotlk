"""
The Gnomeregan boss loot (item variants plan v2 section 7.3, WP L-1 of the Gnomeregan build): each boss's approved list
(docs/dungeons/gnomeregan-rework.md ## Loot "Loot list", rulings 56 to 58, copied in docs/dungeons/
dungeon-loot-vanilla.md "### Gnomeregan") as one loot group of equal-chance entries, on the boss's normal lootid at the
Normal tier and on the heroic body's own lootid at the Heroic tier (lib/dsl/loot.py, lib/loot_tables.py). The items are
declared in gnomeregan.py, the three hard mode items in gnomeregan_hard_mode.py (the gear stage, merged as #162).
Handoff section 7 #42 A (the carriers and cuts), #43 A (the White card's droppers) and #44 A (the ring's) rule where
each list and each quest drop sits; gear ruling G27 A takes the Amulet out of the Sparklematic box.

- **Lists** (one item per kill, as every list): Techbot 7 (the new boss 301105), Viscous Fallout 7, Electrocutioner
  6000 7, the Mobile Alert System 7 (the new boss 301110), Mekgineer Thermaplugg 9 and the Dark Iron Ambassador 3 (the
  rare), 40 on six lootids; Crowd Pummeler 9-60's 8 drop from his chest (gameobject 301380 normal, 301381 heroic) and
  the three hard mode items from Thermaplugg's heroic lootid: 48 + 3. The two new bosses' lootids are their own entries
  (301105, 301110: source/npcs/gnomeregan/techbot.py and mobile_alert_system.py); the four stock bosses keep theirs.
- **The stock groups** of Fallout, Electrocutioner, Thermaplugg and the Ambassador held the boss's own stock items, all
  `item(base=)` declarations (Thermaplugg's four at 20%, 20%, 0 and 0 with the two zero rows splitting the rest), so the
  Normal tier is the stock entry and the group is replaced in place: group 1 is the list. Thermaplugg's groups 2 and 3
  (three schematics at 2% each, Pet Bombling at 90%) are not touched. The new Techbot and Alert System have no stock
  group: the hand rev (data/sql/updates/pending_db_world/rev_loot_gnomeregan.sql) writes Techbot's group 0 and 5 rows.
- **The shared rare list 1090000** (Vibroblade, Supercharger Battle Axe, Hi-tech Supergun, Oscillating Power Hammer,
  Gyromatic Icemaker, Gizmotron Megachopper, Hotshot Pilot's Gloves, Mechbuilder's Overalls, Petrolspill Leggings,
  Caverndeep Trudgers: ten items, group 1, rolled at 0.5% by 20 entries: 18 trash kinds, the Ambassador and Viscous
  Fallout) is emptied (#42 A): all ten items moved onto boss lists. The 20 reference rows go
  (`remove_loot_rows(references=)`) and the pool with them (`remove_reference_pool`: an unused reference Entry is a
  boot ERROR). The live users query (2026-11-26) is exactly those 20.
- **The cuts**, each a live row that would drop a moved item a second time (SELECT 2026-11-26):
  the outside Techbot 6231's three 0.04% rows (9486, 9487, 9488; #42 A) and Chomper 6215's three (9485, 9486, 9510;
  #42 A), the Amulet's 0.48% on the stock Alert System 7849 (#42 A), plus three rows the ruling did not name and the
  orchestrator may drop with their call: Grubbis 7361's 10% Paws (Paws is Fallout's now; Grubbis is cut with Emi's
  event), the Ambusher 6207's direct 0.02% rows of 9485, 9486, 9487, 9488, 9490 and 9509 (it was not a user of the
  shared list) and the Amulet's 0.02% to 0.05% rows on seven inside trash kinds (6206, 6207, 6211, 6212, 6224,
  6329 and 6392). The Amulet's 1.1% in the Sparklematic-Wrapped Box (`item_loot_template` 9363, G27 A) is the hand
  rev's.
  The rows of outside creatures other than 6231 (the Invaders 6208, 6210 and 6213 at 0.02%) are stock world loot and
  stay.
- **Heroic bodies** (source/world/heroic_ids.lock; the heroic ids of the first write run) drop from their own lootid,
  set in source/world/dungeons/gnomeregan.py (`_HEROIC_BOSS_OWN_LOOT = True`, flipped by this WP at the request of
  H's report). Besides the list they keep everything the normal boss drops, copied unchanged in the same groups
  (lib/loot_tables.py derive_heroic_copies): group 0's Guts, DELTA cards, cloth, keys and quest items, the generic
  world pools of group 5, Thermaplugg's schematics.
- **Hard mode** (Thermaplugg, the Whole Workshop, heroic only): group 4 of 310571 holds the three hard mode items
  (Leaking Reactor Core, Walking Bomb Launcher, Master Punch Card) at Heroic Hard Mode with `LootMode` 2
  (`LOOT_MODE_HARD_MODE_1`). The Whole Workshop is one unit, so he is the unit that dies last; the loot bit is set by
  the instance at the armed verdict (`ApplyHardModeLoot` in instance_gnomeregan_rework.cpp: it sets
  `LOOT_MODE_HARD_MODE_1` at `SetVerdict` and clears it at `IN_PROGRESS`, on a wipe and on `OnCreatureCreate`), never
  in `JustDied`: the bit is lit when `Unit::Kill` fills the loot, because the slot is still `IN_PROGRESS` then.
  The normal lootid gets no hard mode group. His heroic list (group 1) stays: a lit kill adds one of the three on top
  of it.
- **Crowd Pummeler 9-60** carries nothing (#42 A: "his body carries nothing"): the chest holds his list and the rows
  his body held (rev_loot_gnomeregan.sql), his lootid and gold are zeroed there and this file names neither his normal
  lootid 6229 nor a heroic one.
- **Kept**: the Workshop Key, the Grime-Encrusted Object, the Safe Combination, the schematics, the cloth, food and
  world pools, and every Guts and DELTA row at its stock chance (SP said "every boss"; stock never was, #42 A).
  **No tokens**, no flex copies.
"""

from lib.dsl.loot import (
    LOOT_MODE_HARD_MODE_1,
    boss_loot,
    remove_loot_rows,
    remove_reference_pool,
)

SHARED_RARE_LIST = 1090000  # the stock reference pool of ten items every one of which now has a boss

LIST_GROUP = 1  # the boss's list: one equal-chance entry per item
HARD_MODE_GROUP = 4  # Thermaplugg's groups 0 to 3 are the stock rows and their copies

# Normal lootid, heroic lootid (the heroic body's own entry: the mint order of heroic_ids.lock, gnomeregan.py's
# `_HEROIC_ID` / `_HEROIC_LOOTID`), the list (item() keys, source/items/gnomeregan.py).
BOSS_LISTS = (
    (301105, 310575, (  # Techbot (the new boss; the outside 6231 keeps its stock table)
        "gnomer_techbot_cpu_shell", "gnomer_oscillating_power_hammer", "gnomer_hi_tech_supergun",
        "gnomer_hotshot_pilots_gloves", "gnomer_grounded_sabatons", "gnomer_tech_support_headset",
        "gnomer_backup_drive",
    )),
    (7079, 310567, (  # Viscous Fallout
        "gnomer_hydrocane", "gnomer_toxic_revenger", "gnomer_acidic_walkers", "gnomer_grubbis_paws",
        "gnomer_caverndeep_trudgers", "gnomer_lead_plated_legguards", "gnomer_hazmat_drape",
    )),
    (6235, 310562, (  # Electrocutioner 6000
        "gnomer_electrocutioner_leg", "gnomer_electrocutioner_lagnut", "gnomer_spidertank_oilrag",
        "gnomer_supercharger_battle_axe", "gnomer_insulated_chain_leggings", "gnomer_conductive_hauberk",
        "gnomer_6000_volt_capacitor",
    )),
    (301110, 310577, (  # The Mobile Alert System (the new boss; the stock 7849 stays trash)
        "gnomer_gnomeregan_amulet", "gnomer_gyromatic_icemaker", "gnomer_vibroblade", "gnomer_petrolspill_leggings",
        "gnomer_security_repeater", "gnomer_night_watch_mantle", "gnomer_security_chiefs_girdle",
    )),
    (7800, 310571, (  # Mekgineer Thermaplugg
        "gnomer_electromagnetic_gigaflux_reactivator", "gnomer_thermapluggs_left_arm",
        "gnomer_thermapluggs_central_core", "gnomer_charged_gear", "gnomer_mechbuilders_overalls",
        "gnomer_mekgineers_blast_visor", "gnomer_girdle_of_spare_fuses", "gnomer_mekgineers_arc_welder",
        "gnomer_rolled_workshop_schematics",
    )),
    (6228, 310556, (  # The Dark Iron Ambassador (the rare; one of three on every kill, as stock)
        "gnomer_emissary_cuffs", "gnomer_glass_shooter", "gnomer_royal_diplomatic_scepter",
    )),
)
for _normal, _heroic, _items in BOSS_LISTS:
    boss_loot(_normal, _items, tier="normal", group=LIST_GROUP)
    boss_loot(_heroic, _items, tier="heroic", group=LIST_GROUP)

# Thermaplugg's hard mode list (heroic only): one item on a lit kill, on top of his heroic item.
THERMAPLUGG_HEROIC = 310571
THERMAPLUGG_HARD_MODE = ("gnomer_leaking_reactor_core", "gnomer_walking_bomb_launcher", "gnomer_master_punch_card")
boss_loot(THERMAPLUGG_HEROIC, THERMAPLUGG_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP,
          loot_mode=LOOT_MODE_HARD_MODE_1)

# Rows of moved items that sit in a group of their own on creatures no list replaces: each is a live row that would
# drop an item a second time. The ruled cuts first (#42 A), then the three the ruling did not name (module docstring).
remove_loot_rows(6231, (9486, 9487, 9488), group=0,
                 why="the outside Techbot's 0.04% rows: all three are on boss lists now (#42 A)")
remove_loot_rows(6215, (9485, 9486, 9510), group=0,
                 why="Chomper's 0.05% to 0.14% rows: all three are on boss lists now (#42 A)")
remove_loot_rows(7849, (10299,), group=0,
                 why="the Gnomeregan Amulet is the Alert System boss's list item now (#42 A)")
remove_loot_rows(7361, (9445,), group=0,
                 why="Grubbis Paws is on Viscous Fallout's list; Grubbis is cut with Emi's event")
remove_loot_rows(6207, (9485, 9486, 9487, 9488, 9490, 9509, 10299), group=0,
                 why="the Ambusher's 0.02% rows of seven moved items: each is on a boss list now")

# The shared rare list 1090000: the 0.5% reference row of its 20 users, then the pool (all ten items have a boss).
# Six users also carry the Amulet at 0.02% to 0.05% (one declaration per (lootid, group 0): the same call); 6224 does
# too, but it is no user.
SHARED_RARE_LIST_USERS = (
    6206, 6211, 6212, 6218, 6219, 6220, 6223, 6225, 6226, 6227, 6228, 6230, 6232, 6233, 6234, 6329, 6391, 6392, 6407,
    7079,
)
OWN_AMULET_ROWS = {6206: (10299,), 6211: (10299,), 6212: (10299,), 6329: (10299,), 6392: (10299,)}
for _lootid in SHARED_RARE_LIST_USERS:
    remove_loot_rows(_lootid, OWN_AMULET_ROWS.get(_lootid, ()), references=(SHARED_RARE_LIST,), group=0,
                     why="the shared rare list's ten items moved onto boss lists")
remove_loot_rows(6224, (10299,), group=0, why="the Amulet is the Alert System boss's list item now")
remove_reference_pool(SHARED_RARE_LIST, why="all ten items moved onto boss lists (handoff 7 #42 A)")
