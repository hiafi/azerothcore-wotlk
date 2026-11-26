"""
The Zul'Farrak boss loot (item variants plan v2 section 7.3, WP L-1 of the Zul'Farrak build): each boss's approved
list (docs/dungeons/zul-farrak-rework.md ## Loot "Loot list", ruling 47, copied in docs/dungeons/dungeon-loot-vanilla.md
"### Zul'Farrak") as one loot group of equal-chance entries, on the stock lootid at the Normal tier and on the heroic
body's own lootid at the Heroic tier (lib/dsl/loot.py, lib/loot_tables.py). The items are declared in zul_farrak.py,
the three hard mode items in zul_farrak_hard_mode.py (gear stage, merged as #161). Handoff section 7 #49 A (the loot
carriers) and #19 A (the crew's stash) rule where each list drops.

- **Lists** (one item per kill, as every list): Theka 8, Antu'sul 7, Zum'rah 7, the Pyramid 8 (carried by
  Sezz'ziz), Ukorz 9, Gahz'rilla 9 (48 on six lootids), the rares' pool 4 and Bly's crew's 9 from the stash chest: 61
  of the 62 list items. The 62nd, Sul'thraze the Lasher, is a join result no list holds. Velratha has no list of her
  own (her Tiara and tablet, the quest rows, stay as stock).
- **Theka** keeps nine world reference pools in his group 1 (24025 to 24046): they stay where they are and the list is
  **group 2** (a generic pool rolls on top of the list, never instead). The other five bosses' stock group 1 held the
  boss's own stock items, all `item(base=)` declarations, so their stock entry is the Normal tier and the rows are
  replaced in place (the declared group owns nothing foreign): group 1 is the list.
- **The shared rare list 1209000** (Troll Protector, Gutwrencher, Brainlash, Eyegouger, The Minotaur, Witch Doctor's
  Cane, Flaming Incinerator, Spellshock Leggings, Bloodletter Scalpel, Blackmetal Cape: ten items, group 1, rolled at
  0.5% by 13 trash and rare entries) is emptied (#49 A): all ten items moved onto bosses and the rares. The 13
  reference rows go (`remove_loot_rows(references=)`) and the pool with them (`remove_reference_pool`: an unused
  reference Entry is a boot ERROR). So do the 0.02% to 0.18% group 0 rows of the same items on Theka, Nekrum, Velratha
  and Ruuzlu (the crew's rows go with the crew's whole table, below): the item would drop from two places.
- **Antu'sul's and Ukorz's group 2** (Runed Ring and Spellshock Leggings at 0.25%) are the same two items now on
  Ukorz's list and the rares' pool: both groups are removed (`remove_loot_group`).
- **The rares** (Sandarr 10080, Dustwraith 10081, Zerillis 10082) are three non-boss elites with the pool of four:
  Desertwalker Cane, Sandstalker Ankleguards, Witch Doctor's Cane and Spellshock Leggings, **group 1** of each
  lootid, one `loot_chance()` row per item at 8.75%, so a kill drops one of the four 35% of the time (#49 A: "one drop
  each at 35%"; a `loot_chance()` group yields at most one of its rows). Dustwraith's 18.55% Desertwalker Cane and
  Zerillis's 18.69% Ankleguards (stock group 0) go. Their other rows (cloth, food, Troll Temper, the world level
  pools of group 5) stay. Heroic rares need their own lootid (a column override of 10080 to 10082 in the dungeon
  file, `columns={"lootid": _HEROIC_ID[entry]}`), or they would drop the Normal tier.
- **Heroic bodies** (source/world/heroic_ids.lock; the heroic ids of the first write run) drop from their own lootid,
  set in source/world/dungeons/zul_farrak.py (`_HEROIC_BOSS_OWN_LOOT = True`, flipped by the orchestrator at this
  WP's request). Besides the list they keep everything the normal boss drops, copied unchanged in the same groups
  (lib/loot_tables.py derive_heroic_copies): group 0's cloth, food, consumables and quest items (Troll Temper, the
  First Mosh'aru Tablet, the world pools of Theka's group 1).
- **Hard mode** (Gahz'rilla, The Crew at the Pool, heroic only): group 2 of 310513 holds the three hard mode items
  (Scale of the Storm God, Stormcharged Fang, Sergeant's Whistle) at Heroic Hard Mode (71) with `LootMode` 2
  (`LOOT_MODE_HARD_MODE_1`). Gahz'rilla is the unit that dies last in the hard mode (the crew's allies yield or are
  gone by then); the loot bit is set by the instance at the arming (STAGE-D7Ha), never in `JustDied`. The normal
  lootid gets no hard mode group.
- **Bly's crew** (#19 A, #49 A): the crew's list, Bly's Divino-matic Rod and the five members' own small tables drop
  from the stash chest (gameobject 301360 normal, 301361 heroic), not from the bodies. The chest is gameobject loot,
  which the DSL cannot declare: data/sql/updates/pending_db_world/rev_loot_zul_farrak.sql writes the chest rows and
  empties the five creature tables (Bly 7604, Raven 7605, Oro 7606, Weegli 7607, Murta 7608), so a body carries
  nothing: the crew's templates (and their heroic copies, through `_crew()` in the dungeon file) name `lootid` 0 and
  no gold, or a boot ERROR and a log line per kill name the deleted tables. This file names no crew lootid.
- **Sul'thraze the Lasher** is the join of Jang'thraze and Sang'thraze (Call of Sul'thraze), never a drop: no list
  holds it (gear REVIEW n6).
- **Quest and cloth rows stay**: Troll Temper, the tablets (First Mosh'aru on Theka, Second on Velratha), Nekrum's
  Medallion, the Executioner's Key, Gahz'rilla's Electrified Scale, Tiara of the Deep and every cloth, food and potion
  row are group 0 rows no declaration names. **No tokens** (no Haunted or Zealot set here), no flex copies.
"""

from lib.dsl.loot import (
    LOOT_MODE_HARD_MODE_1,
    boss_loot,
    loot_chance,
    remove_loot_group,
    remove_loot_rows,
    remove_reference_pool,
)

SHARED_RARE_LIST = 1209000  # the stock reference pool of ten items every one of which now has a boss

LIST_GROUP = 1  # the boss's list: one equal-chance entry per item
THEKA_LIST_GROUP = 2  # Theka's group 1 is nine world reference pools, which stay
RARE_GROUP = 1  # the rares' pool: explicit-chance rows (their group 5 holds the world level pool)
HARD_MODE_GROUP = 2

# Normal lootid, heroic lootid (the heroic body's own entry: the mint order of heroic_ids.lock, zul_farrak.py's
# `_HEROIC_ID` / `_HEROIC_LOOTID`), the list's group, the list (item() keys, source/items/zul_farrak.py).
BOSS_LISTS = (
    (7272, 310512, THEKA_LIST_GROUP, (  # Theka the Martyr
        "zf_carapace_of_the_martyr", "zf_scarab_shell_bracers", "zf_penitents_cord", "zf_blackmetal_cape",
        "zf_gutwrencher", "zf_bloodletter_scalpel", "zf_libram_of_the_persecuted", "zf_martyrs_reliquary",
    )),
    (8127, 310532, LIST_GROUP, (  # Antu'sul
        "zf_hand_of_antusul", "zf_sangthraze_the_deflector", "zf_vice_grips", "zf_lifeblood_amulet",
        "zf_stonegaze_girdle", "zf_sullithuz_scale_coif", "zf_totem_of_the_stone_servant",
    )),
    (7271, 310511, LIST_GROUP, (  # Witch Doctor Zum'rah
        "zf_jumanza_grips", "zf_zumrahs_vexing_cane", "zf_brainlash", "zf_soulbinders_mantle",
        "zf_gravewalker_treads", "zf_idol_of_the_restless_grave", "zf_vessel_of_lost_souls",
    )),
    (7275, 310515, LIST_GROUP, (  # Shadowpriest Sezz'ziz, who carries the Pyramid's list
        "zf_bad_mojo_mask", "zf_jinxed_hoodoo_skin", "zf_jinxed_hoodoo_kilt", "zf_diabolic_skiver",
        "zf_the_minotaur", "zf_executioners_vambraces", "zf_gutchewers_girdle", "zf_totem_of_the_blood_altar",
    )),
    (7267, 310508, LIST_GROUP, (  # Chief Ukorz Sandscalp (Sul'thraze the Lasher is a join, not a drop)
        "zf_big_bad_pauldrons", "zf_jangthraze_the_protector", "zf_the_chiefs_enforcer", "zf_ripsaw",
        "zf_embrace_of_the_lycan", "zf_runed_ring", "zf_sandscalps_war_kilt", "zf_ruuzlus_bloodied_greaves",
        "zf_idol_of_the_lycan",
    )),
    (7273, 310513, LIST_GROUP, (  # Gahz'rilla
        "zf_gahzrilla_fang", "zf_gahzrilla_scale_armor", "zf_stormscale_spaulders", "zf_gauntlets_of_the_sacred_pool",
        "zf_hydromancers_scepter", "zf_robes_of_the_rising_water", "zf_stillwater_drape",
        "zf_libram_of_the_sacred_pool", "zf_coil_of_the_electrified_scale",
    )),
)
for _normal, _heroic, _group, _items in BOSS_LISTS:
    boss_loot(_normal, _items, tier="normal", group=_group)
    boss_loot(_heroic, _items, tier="heroic", group=_group)

# Gahz'rilla's hard mode list (heroic only): one item on a lit kill, on top of his heroic item.
GAHZRILLA_HEROIC = 310513
GAHZRILLA_HARD_MODE = ("zf_scale_of_the_storm_god", "zf_stormcharged_fang", "zf_sergeants_whistle")
boss_loot(GAHZRILLA_HEROIC, GAHZRILLA_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP,
          loot_mode=LOOT_MODE_HARD_MODE_1)

# The stock group 2 of Antu'sul and Ukorz (Runed Ring and Spellshock Leggings at 0.25%): both items are on a list now.
remove_loot_group(8127, group=2, why="Runed Ring is on Ukorz's list and Spellshock Leggings in the rares' pool")
remove_loot_group(7267, group=2, why="Runed Ring is on his list now and Spellshock Leggings in the rares' pool")

# The ten items of the shared rare list as 0.02% to 0.18% group 0 rows of the bosses that had no list (the crew's
# rows leave with the crew's tables, rev_loot_zul_farrak.sql): each is on a list or in the rares' pool now.
remove_loot_rows(7272, (2040, 5616, 9480, 9482, 9483, 9511, 9512), group=0,
                 why="Troll Protector and the rare list's items are on boss lists now (Theka's own three on his)")
remove_loot_rows(7796, (9480, 9482, 9511), group=0, why="the rare list's items are on boss lists now")
remove_loot_rows(7795, (5616, 9481, 9483, 9512), group=0, why="the rare list's items are on boss lists now")
remove_loot_rows(7797, (5616, 6440, 9511, 9512), group=0, why="the rare list's items are on boss lists now")

# The shared rare list 1209000: the 0.5% reference row of its 13 users, then the pool (all ten items have a boss).
# Dustwraith and Zerillis lose their own 18.5% rows in the same call (one declaration per (lootid, group 0)): both
# items are in the rares' pool below.
SHARED_RARE_LIST_USERS = (5648, 5649, 5650, 7246, 7247, 7268, 7274, 7286, 8095, 8120, 10080, 10081, 10082)
RARE_OWN_ROWS = {10081: (12471,), 10082: (12470,)}  # Desertwalker Cane, Sandstalker Ankleguards (stock group 0)
for _lootid in SHARED_RARE_LIST_USERS:
    remove_loot_rows(_lootid, RARE_OWN_ROWS.get(_lootid, ()), references=(SHARED_RARE_LIST,), group=0,
                     why="the shared rare list's ten items moved onto bosses and the rares' pool")
remove_reference_pool(SHARED_RARE_LIST, why="all ten items moved onto bosses and the rares' pool (handoff 7 #49 A)")

# The three rares share one pool of four: one of them drops 35% of the time (8.75% each, at most one per kill). A
# `loot_chance()` row names an item_template entry, so each row carries the entry of its tier by hand: the stock entry
# is the Normal tier of a `base=` item, and the Heroic tier's entry is the line of source/items/item_ids.lock (the test
# pins both to the lock).
RARES = (  # normal lootid, heroic lootid (zul_farrak.py's `_HEROIC_ID`)
    (10080, 310536),  # Sandarr Dunereaver
    (10081, 310537),  # Dustwraith
    (10082, 310538),  # Zerillis
)
RARE_POOL = (  # item() key, Normal entry (the stock row), Heroic entry (item_ids.lock), the item's name
    ("zf_desertwalker_cane", 12471, 74745, "Desertwalker Cane"),
    ("zf_sandstalker_ankleguards", 12470, 74749, "Sandstalker Ankleguards"),
    ("zf_witch_doctors_cane", 9482, 74753, "Witch Doctor's Cane"),
    ("zf_spellshock_leggings", 9484, 74757, "Spellshock Leggings"),
)
RARE_DROP_CHANCE = 35.0
RARE_ROW_CHANCE = RARE_DROP_CHANCE / len(RARE_POOL)
for _normal, _heroic in RARES:
    for _key, _stock, _heroic_entry, _name in RARE_POOL:
        loot_chance(_normal, _stock, RARE_ROW_CHANCE, RARE_GROUP, name=_name)
        loot_chance(_heroic, _heroic_entry, RARE_ROW_CHANCE, RARE_GROUP, name=f"{_name} (Heroic)")
