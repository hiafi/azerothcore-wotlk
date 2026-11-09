"""
The Stratholme boss loot, wave 1 (the Service Entrance; item variants plan v2 section 7.3, WP-L-1 of the Stratholme
build): each boss's approved list (docs/dungeons/stratholme-rework.md ## Loot, ruling 62, copied in
docs/dungeons/dungeon-loot-vanilla.md) as one loot group of equal-chance entries, on the stock lootid at the Normal tier
and on the heroic body's own lootid at the Heroic tier (lib/dsl/loot.py, lib/loot_tables.py). The items are declared in
stratholme.py, the Haunted tokens in haunted_set.py. The shape is the Scholomance one (scholomance_loot.py). Wave 2
(the Main Gate bosses, L-2) appends its own section at the end of this file (the "Wave 2" docstring below); the
section 1 bosses' stock rows are untouched by the wave 1 declarations.

- **Group 1** of each boss is the list: one item per kill, two for the Baron (a `picks=2` list, one reference row x2
  into a pool of its own, ids 1700006-1700007 of source/ids.yaml's `loot_reference` block). Barthilas 5 items,
  the Baroness 6, Nerub'enkan 5, Maleki 5, Ramstein 5, the Baron 9. The stock group 1 held the boss's items, a Tier 0
  piece (cut: the Haunted vendors sell the sets now) and, for Barthilas and Ramstein, a cut piece (Magistrate's Cuffs,
  Animated Chain Necklace, Gauntlets of Valor); the declarations name those rows (`replaces_items`).
- **The ziggurat greens** (Baroness, Nerub'enkan, Maleki): the stock group 2 held the four resist-only greens and one
  novelty item (Wail of the Banshee, Eye of Arachnida, Clutch of Foresight), 20% each. Two of the greens are list items
  now (Windshrieker Pauldrons and Banshee's Touch; Darkspinner Claws and Acid-etched Pauldrons; Darkbind Fingers and
  Flamescarred Girdle), the other six are cut (build spec, Structure 3: "all 12 resist-only greens go"). The build spec
  names none of the three novelty items, so they keep the stock rate: group 2 stays as a `loot_chance()` group of that
  one item at 20% (Question for the designer in the STAGE-L-1 report).
- **Haunted tokens** (build spec, Structure 2): Ramstein the Haunted Bracers, the Baron the Haunted Leggings. Each is a
  group of its own (group 3, one entry, so it always drops) on top of the list item: the token of the kill's tier
  (Normal on a normal lootid, Heroic on a heroic one).
- **Group 0** (grays, reagents, the quest items, Scourgestones, the heads, Key to the City, Ramstein's green pool 24016)
  stays on the normal lootids untouched: a generic pool rolls on top, never instead. Heroic bodies keep them as
  copies, with their loot conditions (lib/loot_tables.py derive_heroic_copies). The Baron's group 0 also held his
  stock two rolls on the pool 35028 (a reference row), Cape of the Black Baron (8.7%, a list item now) and the Reins
  (1%): the first two are removed rows (`remove_loot_rows`, the pool deleted), the Reins move to group 4.
- **Deathcharger's Reins** (ruling 62, handoff section 10): 1% on a normal kill, 2% on a heroic one, 10% on a heroic
  hard mode kill, never two. Group 4 of each Baron lootid is a `loot_chance()` group: the normal lootid one row at 1%,
  the heroic lootid a 2% row (LootMode 1) and an 8% row (LootMode 2) in the same group. A group rolls its explicit
  chances in turn and yields at most one row; a hard mode kill carries both loot mode bits (the instance script adds
  bit 2 to the default bit 1), so it rolls 2% + 8% = 10% and a plain heroic kill 2%. The table's key is (Entry, Item,
  Reference, GroupId), so the 8% row cannot be a second row of the item: it is a grouped reference row into a
  one-item pool (1700008). The stock 1% row moves from group 0 to group 4 (same chance, same item).
- **Hard mode** (heroic only): group 2 of the Baron's heroic lootid 310160 holds the three hard mode items at Heroic
  Hard Mode (71) with `LootMode` 2 (`LOOT_MODE_HARD_MODE_1`), on top of the heroic items, exactly as Scholomance's
  (DungeonKit::SetHardModeLoot adds the bit while the Ultimatum is lit; the Baron's stock group 2 does not exist).
- **Tier 0 trash drops** (build spec: "Stratholme's trash Tier 0 rows go"): the 24 trash lootids below lose their Tier 0
  rows (belts and bracers of the nine Tier 0 sets). Heroic trash shares the normal lootid.
- The Baron's pool 35028 (two rolls on thirteen items, three of them cut) is replaced by the list and deleted.
"""

from lib.dsl.loot import (
    LOOT_MODE_HARD_MODE_1,
    boss_loot,
    loot_chance,
    remove_loot_rows,
    remove_reference_pool,
)

TOKEN_GROUP = 3  # a Haunted token: one entry, always drops, apart from the list (group 1)
HARD_MODE_GROUP = 2  # the Baron's heroic lootid: three hard mode items at LootMode 2
NOVELTY_GROUP = 2  # the ziggurat bosses' stock group 2 (the resist greens), kept for the one novelty item
REINS_GROUP = 4  # Deathcharger's Reins on both Baron lootids
NOVELTY_CHANCE = 20  # the stock rate of one row of five equal-chance rows

# Normal lootid, heroic lootid (the heroic body's own entry, heroic_ids.lock), list (item() keys), Haunted token key
# (None: no token), the stock group 1 rows the list replaces (a Tier 0 piece or a cut item).
BOSS_LISTS = (
    (10435, 310155, (  # Magistrate Barthilas
        "strat_royal_tribunal_cloak", "strat_death_grips", "strat_peacemaker", "strat_crimson_felt_hat",
        "strat_idol_of_brutality",
    ), None, (18726,)),  # Magistrate's Cuffs
    (10436, 310156, (  # Baroness Anastari
        "strat_banshee_finger", "strat_windshrieker_pauldrons", "strat_banshees_touch", "strat_anastari_heirloom",
        "strat_screeching_bow", "strat_shadowy_laced_handwraps",
    ), None, (16704,)),  # Dreadmist Sandals
    (10437, 310157, (  # Nerub'enkan
        "strat_husk_of_nerubenkan", "strat_darkspinner_claws", "strat_acid_etched_pauldrons",
        "strat_carapace_spine_crossbow", "strat_thuzadin_sash",
    ), None, (16675, 18739)),  # Beaststalker's Boots, Chitinous Plate Legguards
    (10438, 310158, (  # Maleki the Pallid
        "strat_skull_of_burning_shadows", "strat_darkbind_fingers", "strat_flamescarred_girdle",
        "strat_pale_moon_cloak", "strat_bone_slicing_hatchet",
    ), None, (16691, 18735)),  # Devout Sandals, Maleki's Footwraps
    (10439, 310159, (  # Ramstein the Gorger
        "strat_slavedrivers_cane", "strat_band_of_flesh", "strat_soulstealer_mantle", "strat_crest_of_retribution",
        "strat_ramsteins_lightning_bolts",
    ), "haunted_token_wrist", (16737, 18723)),  # Gauntlets of Valor, Animated Chain Necklace
)
for normal_lootid, heroic_lootid, items, token, replaced_items in BOSS_LISTS:
    boss_loot(normal_lootid, items, tier="normal", replaces_items=replaced_items)
    boss_loot(heroic_lootid, items, tier="heroic")
    if token is not None:
        boss_loot(normal_lootid, (token,), tier="normal", group=TOKEN_GROUP)
        boss_loot(heroic_lootid, (token,), tier="heroic", group=TOKEN_GROUP)

# The ziggurat bosses' novelty item (stock group 2, 20%): normal and heroic lootid -> (the item, its name, the stock
# group 2 rows that go: the cut greens; the two list items in it are declared items and need no mention).
ZIGGURAT_NOVELTIES = (
    (10436, 310156, 13514, "Wail of the Banshee", (13535, 13537)),  # Coldtouch Phantom Wraps, Chillhide Bracers
    (10437, 310157, 13508, "Eye of Arachnida", (13530, 13531)),  # Fangdrip Runners, Crypt Stalker Leggings
    (10438, 310158, 13509, "Clutch of Foresight", (13527, 13528)),  # Lavawalker Greaves, Twilight Void Bracers
)
for normal_lootid, heroic_lootid, item, item_name, cut in ZIGGURAT_NOVELTIES:
    loot_chance(normal_lootid, item, NOVELTY_CHANCE, NOVELTY_GROUP, replaces_items=cut, name=item_name)
    loot_chance(heroic_lootid, item, NOVELTY_CHANCE, NOVELTY_GROUP, name=item_name)

# Baron Rivendare (10440, heroic 310160): two distinct items of the list (a pool of the nine), the Haunted Leggings, the
# Reins and the Ultimatum's hard mode items.
BARON_NORMAL, BARON_HEROIC = 10440, 310160
BARON_POOL = (
    "strat_cape_of_the_black_baron", "strat_dracorian_gauntlets", "strat_seal_of_rivendare",
    "strat_scepter_of_the_unholy", "strat_gauntlets_of_deftness", "strat_helm_of_the_executioner",
    "strat_skullforge_reaver", "strat_bonescraper", "strat_runeblade_of_baron_rivendare",
)
BARON_PICKS = 2
# The nine Tier 0 legs of his stock group 1 (Kilt of Elements, Beaststalker's Pants, Magister's Leggings, Devout Skirt,
# Dreadmist Leggings, Shadowcraft Pants, Wildheart Kilt, Lightforge Legplates, Legplates of Valor); the Haunted
# Leggings replace them.
BARON_STOCK_LEGS = (16668, 16678, 16687, 16694, 16699, 16709, 16719, 16728, 16732)
REINS = 13335
CAPE_OF_THE_BLACK_BARON = 13340
BARON_STOCK_POOL = 35028
REINS_HARD_MODE_POOL = 1700008  # the 8% hard mode row is a grouped reference row (see the module docstring)

boss_loot(BARON_NORMAL, BARON_POOL, tier="normal", picks=BARON_PICKS, reference=1700006,
          replaces_items=BARON_STOCK_LEGS)
boss_loot(BARON_HEROIC, BARON_POOL, tier="heroic", picks=BARON_PICKS, reference=1700007)
boss_loot(BARON_NORMAL, ("haunted_token_legs",), tier="normal", group=TOKEN_GROUP)
boss_loot(BARON_HEROIC, ("haunted_token_legs",), tier="heroic", group=TOKEN_GROUP)
remove_loot_rows(BARON_NORMAL, (CAPE_OF_THE_BLACK_BARON, REINS), group=0, references=(BARON_STOCK_POOL,),
                 why="the Cape is in his list, the Reins move to group 4, and his two rolls on pool 35028 are "
                     "replaced by the list")
remove_reference_pool(BARON_STOCK_POOL, why="the Baron's list replaces his two rolls on it")
loot_chance(BARON_NORMAL, REINS, 1, REINS_GROUP, name="Deathcharger's Reins")
loot_chance(BARON_HEROIC, REINS, 2, REINS_GROUP, name="Deathcharger's Reins")
loot_chance(BARON_HEROIC, REINS, 8, REINS_GROUP, LOOT_MODE_HARD_MODE_1, reference=REINS_HARD_MODE_POOL,
            name="Deathcharger's Reins")

# The hard mode list (heroic only): one item on a lit kill, on top of the heroic items.
BARON_HARD_MODE = ("strat_ysidas_locket", "strat_blade_of_the_condemned", "strat_deathchargers_spur")
boss_loot(BARON_HEROIC, BARON_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP, loot_mode=LOOT_MODE_HARD_MODE_1)

# The stock Tier 0 trash drops (belts and bracers of sets 181-189), group 0 rows: lootid -> (Tier 0 items, names).
# Heroic trash shares the normal lootid, so one DELETE serves both difficulties. Every lootid is its creature's own
# entry and no creature outside map 329 uses it (live DB, 2026-11-09).
TIER_0_TRASH = (
    (10398, (16685, 16697, 16702), "Thuzadin Shadowcaster: Magister's Belt, Devout Bracers, Dreadmist Belt"),
    (10400, (16685, 16697, 16702), "Thuzadin Necromancer: Magister's Belt, Devout Bracers, Dreadmist Belt"),
    (10405, (16710,), "Plague Ghoul: Shadowcraft Bracers"),
    (10406, (16681,), "Ghoul Ravener: Beaststalker's Bindings"),
    (10407, (16681,), "Fleshflayer Ghoul: Beaststalker's Bindings"),
    (10408, (16722, 16723), "Rockwing Gargoyle: Lightforge Bracers and Belt"),
    (10409, (16722, 16723), "Rockwing Screecher: Lightforge Bracers and Belt"),
    (10412, (16671,), "Crypt Crawler: Bindings of Elements"),
    (10413, (16671,), "Crypt Beast: Bindings of Elements"),
    (10414, (16736,), "Patchwork Horror: Belt of Valor"),
    (10416, (16716, 16736), "Bile Spewer: Wildheart Belt, Belt of Valor"),
    (10417, (16716, 16736), "Venom Belcher: Wildheart Belt, Belt of Valor"),
    (10418, (16723,), "Crimson Guardsman: Lightforge Belt"),
    (10419, (16685, 16697, 16702), "Crimson Conjuror: Magister's Belt, Devout Bracers, Dreadmist Belt"),
    (10420, (16697,), "Crimson Initiate: Devout Bracers"),
    (10421, (16681,), "Crimson Defender: Beaststalker's Bindings"),
    (10422, (16685, 16702), "Crimson Sorcerer: Magister's Belt, Dreadmist Belt"),
    (10423, (16697,), "Crimson Priest: Devout Bracers"),
    (10424, (16723,), "Crimson Gallant: Lightforge Belt"),
    (10425, (16685,), "Crimson Battle Mage: Magister's Belt"),
    (10426, (16714,), "Crimson Inquisitor: Wildheart Bracers"),
    (10463, (16714,), "Shrieking Banshee: Wildheart Bracers"),
    (10464, (16714,), "Wailing Banshee: Wildheart Bracers"),
    (11043, (16671,), "Crimson Monk: Bindings of Elements"),
)
for _lootid, _items, _what in TIER_0_TRASH:
    remove_loot_rows(_lootid, _items, group=0, why=f"{_what} (Tier 0 pieces come from the Haunted vendors)")


# =====================================================================================================================
# Wave 2 (the Main Gate, WP-L-2)
# =====================================================================================================================
# **Wave 2: the Main Gate bosses** (The Unforgiven, Hearthsinger Forresten, Timmy the Cruel, Malor the Zealous, Cannon
# Master Willey, Archivist Galford, Balnazzar; build spec ## Loot, ruling 62). The shape is the wave 1 one above.
#
# - **The lists** are group 1 (Malor: group 2, see below) at equal chance, the Normal tier on the stock lootid and the
#   Heroic tier on the heroic body's own lootid (heroic_ids.lock: 310163, 310164, 310166, 310168, 310170, 310173,
#   310175): The Unforgiven 4 items, Forresten 5, Timmy 3, Galford 4, Willey 7, Malor 5, Balnazzar 9 (two per kill).
#   Dathrohan has lootid 0 on both difficulties: Balnazzar's kill carries the encounter's loot.
#
# - **Cut rows** are named in `replaces_items`: the Tier 0 piece of each boss (Wildheart Gloves, Magister's Boots,
#   Lightforge Gauntlets, Devout Gloves) and the chest, wrist, legs and feet pieces ("standalone armor only in head,
#   shoulders, hands and waist"). Willey's and Balnazzar's stock lists are the references 35026 and 35027 (two rolls
#   each, `MaxCount` 2, group 1): the lists replace the reference rows (`replaces_references`), the pools are deleted
#   (`remove_reference_pool`; only these two bosses used them, checked over every loot table), and their cut pieces
#   (Master Cannoneer Boots, Shadowcraft Spaulders, Willey's Back Scratcher, Redemption, Fire Striders, Lightforge
#   Boots) go with them. Willey drops one item now (build spec Structure 1: two only for Balnazzar and the Baron);
#   Balnazzar's list is a `picks=2` list (pools 1700009 normal, 1700010 heroic: the next ids after the Baron's wave 1
#   pools 1700006-1700008).
#
# - **Haunted tokens** on top of the list (group 3, one entry, always drops): Forresten the Haunted Boots, Balnazzar
#   the Haunted Chestpiece, of the kill's tier.
#
# - **Forresten's tree** (reference 1000357, levels 1 to 64, group 5): his row is removed from both lootids. The pool
#   itself is a shared one (dozens of creatures roll it), so it stays. His 0.5% roll on the Stratholme BoE pool
#   (1329000, group 0) stays, with Plaguebat Fur Gloves in it; the list holds the gloves too, at the item's own tier.
#
# - **Malor** has no stock item of his own: his stock group 1 is ten rows of shared world pools (24016, 24017, ...),
#   which stay. The list goes into group 2. Totem of the Storm and Idol of the Moon leave his share of world pool
#   24021 (the pool also holds Libram of Fervor, one of three equal members at 0.5%, so 0.17% each), so his row on the
#   pool is removed and Libram of Fervor keeps its 0.17% as a row of its own (group 6, `loot_chance()`). The pool is a
#   shared one and stays as it is for every other creature. His 0.02% Stratholme Militia Shoulderguard row (group 0)
#   stays.
#
# - **Galford**'s stock group 1 had the Tome at 12% and four equal rows; the list is four equal rows (no weights in a
#   list), so the Tome rises from 12% to 25% of a kill.
#
# - **Hard mode** (heroic only): group 2 of Balnazzar's heroic lootid 310170 holds Carrion Signet, Dust of the
#   Nathrezim and Two-Faced Tome at Heroic Hard Mode (71) with `LootMode` 2 (`LOOT_MODE_HARD_MODE_1`), the Baron's
#   pattern above. The bit rides the creature's loot mode while the Grand Lie is lit (`DungeonKit::SetHardModeLoot`,
#   instance_stratholme_rework.cpp `ApplyHardModeLoot`).
#
# - **Trash**: the Tier 0 rows of the belts and bracers went from all 24 trash lootids in wave 1 (TIER_0_TRASH above);
#   nothing is left to cut on the Main Gate's trash.

# Normal lootid, heroic lootid, list (item() keys), Haunted token key (None: no token), the stock group 1 rows the list
# replaces (item_template entries).
MAIN_GATE_LISTS = (
    (10516, 310163, (  # The Unforgiven
        "strat_mask_of_the_unforgiven", "strat_wailing_nightbane_pauldrons", "strat_soul_breaker",
        "strat_shroud_of_the_last_soul",
    ), None, (13409, 16717)),  # Tearfall Bracers, Wildheart Gloves
    (10558, 310164, (  # Hearthsinger Forresten
        "strat_piccolo_of_the_flaming_fire", "strat_rainbow_girdle", "strat_hearthsingers_tuning_fork",
        "strat_songbird_sash", "strat_plaguebat_fur_gloves",
    ), "haunted_token_feet", (13378, 13383, 16682)),  # Songbird Blouse, Woollies of the Minstrel, Magister's Boots
    (10808, 310166, (  # Timmy the Cruel
        "strat_the_cruel_hand_of_timmy", "strat_grimgore_noose", "strat_freeze_tag_mittens",
    ), None, (13400, 13402, 16724)),  # Vambraces of the Sadist, Timmy's Galoshes, Lightforge Gauntlets
    (10811, 310168, (  # Archivist Galford
        "strat_archivist_cape", "strat_foresight_girdle", "strat_pyrewatch_coif", "strat_tome_of_knowledge",
    ), None, (16692, 18716)),  # Devout Gloves, Ash Covered Boots
)
for normal_lootid, heroic_lootid, items, token, replaced_items in MAIN_GATE_LISTS:
    boss_loot(normal_lootid, items, tier="normal", replaces_items=replaced_items)
    boss_loot(heroic_lootid, items, tier="heroic")
    if token is not None:
        boss_loot(normal_lootid, (token,), tier="normal", group=TOKEN_GROUP)
        boss_loot(heroic_lootid, (token,), tier="heroic", group=TOKEN_GROUP)

# Forresten's 446-item tree (group 5, a grouped reference row; the pool is shared, so it stays).
FORRESTEN_NORMAL, FORRESTEN_HEROIC = 10558, 310164
FORRESTEN_TREE = 1000357
FORRESTEN_TREE_GROUP = 5
remove_loot_rows(FORRESTEN_NORMAL, group=FORRESTEN_TREE_GROUP, references=(FORRESTEN_TREE,),
                 why="the 446-item level 1-64 tree is off level and outnumbers his list (build spec Structure 4)")

# Cannon Master Willey (10997, heroic 310173): the list replaces his two rolls on pool 35026.
WILLEY_NORMAL, WILLEY_HEROIC = 10997, 310173
WILLEY_STOCK_POOL = 35026
WILLEY_LIST = (
    "strat_willeys_portable_howitzer", "strat_cannonball_runner", "strat_barrage_girdle",
    "strat_dianas_pearl_necklace", "strat_mantle_of_the_scarlet_crusade", "strat_helm_of_the_new_moon",
    "strat_scarlet_throwing_axes",
)
boss_loot(WILLEY_NORMAL, WILLEY_LIST, tier="normal", replaces_references=(WILLEY_STOCK_POOL,))
boss_loot(WILLEY_HEROIC, WILLEY_LIST, tier="heroic")
remove_reference_pool(WILLEY_STOCK_POOL, why="Willey's list replaces his two rolls on it")

# Balnazzar (10813, heroic 310170): two distinct items of the list (a pool of the nine), the Haunted Chestpiece and the
# Grand Lie's hard mode items.
BALNAZZAR_NORMAL, BALNAZZAR_HEROIC = 10813, 310170
BALNAZZAR_STOCK_POOL = 35027
BALNAZZAR_POOL = (
    "strat_star_of_mystaria", "strat_demonshear", "strat_wyrmtongue_shoulders", "strat_crown_of_tyranny",
    "strat_gift_of_the_elven_magi", "strat_hammer_of_the_grand_crusader", "strat_grand_crusaders_helm",
    "strat_shroud_of_the_nathrezim", "strat_book_of_the_dead",
)
BALNAZZAR_HARD_MODE = ("strat_carrion_signet", "strat_dust_of_the_nathrezim", "strat_two_faced_tome")
boss_loot(BALNAZZAR_NORMAL, BALNAZZAR_POOL, tier="normal", picks=BARON_PICKS, reference=1700009,
          replaces_references=(BALNAZZAR_STOCK_POOL,))
boss_loot(BALNAZZAR_HEROIC, BALNAZZAR_POOL, tier="heroic", picks=BARON_PICKS, reference=1700010)
boss_loot(BALNAZZAR_NORMAL, ("haunted_token_chest",), tier="normal", group=TOKEN_GROUP)
boss_loot(BALNAZZAR_HEROIC, ("haunted_token_chest",), tier="heroic", group=TOKEN_GROUP)
boss_loot(BALNAZZAR_HEROIC, BALNAZZAR_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP,
          loot_mode=LOOT_MODE_HARD_MODE_1)
remove_reference_pool(BALNAZZAR_STOCK_POOL, why="Balnazzar's list replaces his two rolls on it")

# Malor the Zealous (11032, heroic 310175): the list is group 2 (his group 1 holds the shared world pools, which stay).
MALOR_NORMAL, MALOR_HEROIC = 11032, 310175
MALOR_LIST_GROUP = 2
MALOR_LIST = (
    "strat_gauntlets_of_the_zealot", "strat_inquisitors_girdle", "strat_libram_of_zeal", "strat_totem_of_the_storm",
    "strat_idol_of_the_moon",
)
RELIC_WORLD_POOL = 24021  # Idol of the Moon, Totem of the Storm, Libram of Fervor: 0.5% in group 1, a third each
LIBRAM_OF_FERVOR = 23203
LIBRAM_GROUP = 6  # a row of its own: the stock group 1 is the world pools, the list is group 2
LIBRAM_CHANCE = 0.17  # 0.5% / 3, as the build spec writes it
boss_loot(MALOR_NORMAL, MALOR_LIST, tier="normal", group=MALOR_LIST_GROUP)
boss_loot(MALOR_HEROIC, MALOR_LIST, tier="heroic", group=MALOR_LIST_GROUP)
remove_loot_rows(MALOR_NORMAL, group=1, references=(RELIC_WORLD_POOL,),
                 why="Totem of the Storm and Idol of the Moon are on his list; Libram of Fervor keeps its share "
                     "as a row of its own")
loot_chance(MALOR_NORMAL, LIBRAM_OF_FERVOR, LIBRAM_CHANCE, LIBRAM_GROUP, name="Libram of Fervor")
loot_chance(MALOR_HEROIC, LIBRAM_OF_FERVOR, LIBRAM_CHANCE, LIBRAM_GROUP, name="Libram of Fervor")
