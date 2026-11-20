"""
The Blackrock Depths boss loot, wave 1 (sections 1 and 2: the Detention Block and Shadowforge City; Blackrock Depths
build, WP-L-1): each boss's approved list (docs/dungeons/blackrock-depths-rework.md ## Loot, rulings 85-87, copied in
docs/dungeons/dungeon-loot-vanilla.md) as one loot group of equal-chance entries, on the stock lootid at the Normal tier
and on the heroic body's own lootid at the Heroic tier (lib/dsl/loot.py, lib/loot_tables.py). The items are declared in
blackrock_depths.py (the hard mode effects in blackrock_depths_hard_mode_effects.py), the Molten tokens in
molten_set.py. The shape is the Blackrock Spire one (blackrock_spire_loot.py) without the flex copies: Blackrock Depths
is a 5 player dungeon (ruling 3), so groups 11-13 and loot mode bits 4 / 8 are not used for flex. Wave 2 (sections 3
and 4, WP-L-2) is the section at the end of this file (its own docstring block says what each declaration does);
nothing in wave 1's declarations touches a section 3 or 4 boss's stock rows.

- **Group 1** of each boss is the list: one item per kill. Gerstahn 3, Roccor 3, Grebmar 3, each Ring champion 2 (the
  Ring drops 2 per run, ruling 86), Loregrain 3, Stilgiss and Verek 4 (one encounter: the list is on Stilgiss's lootid
  and Verek's own group 1 goes, Collar included), Doomgrip 4 (the Vault's four), Incendius 3, Bael'Gar 3, and the minor
  pool's 8 (Fineous and Panzor the Invincible; wave 2 adds Hurley, Ribbly and Plugger). The stock group 1 held the
  boss's items and the pieces cut by the slot rule (standalone shoulder, chest, hands and feet; the Savage Gladiator
  set; Incendius's four Fire resistance bracers; Fineous's four): the declarations name those rows (`replaces_items`).
  Every stock row of a declared group that the list does not carry is named; an unnamed one stops the run.
- **Group 0** (grays, reagents, the quest and trophy rows, Prison Cell Key, Ironfel, the Shirt, runecloth, Dark Iron
  Scraps, the Notes, the potions) stays on the normal lootids untouched: a generic pool rolls on top, never instead.
  Heroic bodies keep them as copies, with their loot conditions (lib/loot_tables.py derive_heroic_copies). The rows
  that go are Watchman Doomgrip's strays (below) and Anub'shiah's stock group 2 (the Carapace, now on his list).
- **Watchman Doomgrip** (the Vault, SP rulings 44 and 45): his group 1 is the Vault's four (Black Steel Bindings, Wand
  of Eternal Light, Magma Forged Band, Mana Shaping Handwraps) at the Normal tier on 9476 and the Heroic tier on 310375;
  one always drops, and the Secret Safe's fill script (STAGE-D9 §4.4) finds whichever of the eight he dropped (it must
  keep one gear item back from the Safe). The stock lootid also held 11 generic reference rows in group 1 (the world
  pools 24024 ... 24086, `replaces_references`), the four Vault items and the four Seven chest items as group 0 rows
  and thirteen world blue drops at 0.08-0.32%: "the stray stock rows leave with it" (SP Loot, stock note); group 0 rows
  go by `remove_loot_rows`. His quest, gold, reagent, potion, green and gem rows stay.
- **Verek** (stock lootid 9042) keeps his group 0 and the group 5 world pool and loses the stock group 1 (the Collar
  moved onto Stilgiss's list, the Leash is cut): he runs the same lootid on both difficulties (no heroic copy of his
  own, STAGE-H), so the one removal covers both.
- **The Ring's Molten legs token** (SP Structure 1; D5 STAGE report 4): a group of its own (group 3, one entry, always
  drops) on every champion's normal and heroic lootid at **LootMode 4**. Only the Ring's title holder carries the bit
  (`RingChampionsLogic.h kTitleHolderLootMode`, set by `ACTION_RING_TITLE_HOLDER`), so the second champion to die drops
  it and the first does not. LootMode 2 stays the Encore's.
- **The Molten wrist token** (Lord Incendius): group 3, always, at every difficulty (the kill's tier).
- **Hard mode lists** (heroic only): group 2 of the heroic lootid at `LootMode` 2 (`LOOT_MODE_HARD_MODE_1`), three items
  at Heroic Hard Mode (71), on top of the heroic list. The Encore's on **Theldren's** heroic lootid 310390 (the last
  member to die; his corpse carries bit 2 from his summon, D6; the other four members have lootid 0); the Lord of the
  Lake's on Incendius's heroic lootid 310342 (the giant is Incendius himself; the loot bit is set at the pull, D12).
  Theldren's normal lootid 16059 gets nothing (heroic only): his stock quest row stays.
- **Keys** (rulings 35 and 36): the Dark Keeper Key (11197, green since the IT rev) at 5% on top of the loot of the six
  wave 1 Dark Iron dwarf bosses (Gerstahn, Grebmar, Loregrain, Stilgiss, Doomgrip, Fineous), a `loot_chance()` group
  of one row (group 4) on the normal and the heroic lootid. The Relic Coffer Key's 1% and the Dark Keepers' swap are
  the IT rev's (rev_event_items_blackrock_depths.sql: one UPDATE over every row of the item, heroic copies included,
  since the generated revs sort before it).
- **Minor pool** (ruling 86): eight items, each of Fineous, Panzor the Invincible (wave 1) and Hurley, Ribbly and
  Plugger (wave 2) drops one of the eight at equal chance (a group of eight on each lootid). Panzor has no heroic
  template (STAGE-H `skip=`): he runs his normal lootid on heroic and drops the Normal tier.
- **Not in this file**: the gameobject loot (the Secret Safe, the twelve Relic Coffers and the Dark Coffer) is hand
  SQL, data/sql/updates/pending_db_world/rev_loot_wave_1_blackrock_depths.sql (the DSL declares creature loot only);
  Fineous's rope is not a loot row (D10 adds it in `JustDied`). Wave 2's gameobject loot (the Chest of The Seven) is
  data/sql/updates/pending_db_world/rev_loot_wave_2_blackrock_depths.sql.
"""

from lib.dsl.loot import (
    LOOT_MODE_HARD_MODE_1,
    boss_loot,
    loot_chance,
    remove_loot_group,
    remove_loot_rows,
    remove_reference_pool,
)

LIST_GROUP = 1  # the boss's list: one equal-chance entry per item
HARD_MODE_GROUP = 2  # the heroic lootid's hard mode list at LootMode 2
TOKEN_GROUP = 3  # a Molten token: one entry, always drops, apart from the list (group 1)
KEY_GROUP = 4  # the Dark Keeper Key: one explicit-chance row, apart from the list
LOOT_MODE_TITLE_HOLDER = 0x4  # RingChampionsLogic.h kTitleHolderLootMode (AddLootMode on the Ring's title holder)

DARK_KEEPER_KEY = 11197  # stock item, green since rev_event_items_blackrock_depths.sql
DARK_KEEPER_KEY_CHANCE = 5  # ruling 35: percent, on top of the dwarf bosses' loot


# Stock group 1 reference rows (Item = Reference) a list drops on purpose: normal lootid -> reference Entries.
# Doomgrip's group 1 held eleven world reference pools (the upstream gem and blue tables); they leave with the stray
# rows (SP Loot, stock note), the list replaces them.
REPLACED_REFERENCES = {
    9476: (24024, 24025, 24027, 24029, 24030, 24031, 24033, 24036, 24043, 24045, 24086),
}


def _boss_lists(normal_lootid, heroic_lootid, items, token=None, replaced_items=(), token_loot_mode=1,
                dark_keeper_key=False, list_group=LIST_GROUP, picks=1, references=(None, None),
                replaced_references=None):
    """One boss: the list (and the token, and the 5% key) at the Normal and the Heroic tier on the two lootids. Only
    the normal list names the stock rows it replaces. `heroic_lootid` None: a boss with no heroic copy of its own
    (Panzor the Invincible, stock lootid on both difficulties). `picks=N` (with `references=(normal pool, heroic pool)`,
    ids of the `loot_reference` block) drops N distinct items of the list (the Emperor's 2 of 8); `list_group` puts the
    list in another group than 1 (Ribbly and Plugger keep their stock group 1 rows that are not gear)."""
    if replaced_references is None:
        replaced_references = REPLACED_REFERENCES.get(normal_lootid, ())
    boss_loot(normal_lootid, items, tier="normal", group=list_group, picks=picks, reference=references[0],
              replaces_items=replaced_items, replaces_references=replaced_references)
    if heroic_lootid is not None:
        boss_loot(heroic_lootid, items, tier="heroic", group=list_group, picks=picks, reference=references[1])
    if token is not None:
        boss_loot(normal_lootid, (token,), tier="normal", group=TOKEN_GROUP, loot_mode=token_loot_mode)
        boss_loot(heroic_lootid, (token,), tier="heroic", group=TOKEN_GROUP, loot_mode=token_loot_mode)
    if dark_keeper_key:
        loot_chance(normal_lootid, DARK_KEEPER_KEY, DARK_KEEPER_KEY_CHANCE, KEY_GROUP, name="Dark Keeper Key")
        loot_chance(heroic_lootid, DARK_KEEPER_KEY, DARK_KEEPER_KEY_CHANCE, KEY_GROUP, name="Dark Keeper Key")


# The minor pool of ruling 86: one list of eight shared by Fineous, Panzor the Invincible, Hurley, Ribbly and Plugger
# (the last three are wave 2's, MINOR_POOL is theirs to reuse).
MINOR_POOL = (
    "brd_hurleys_tankard", "brd_coal_miner_boots", "brd_firemoss_boots", "brd_mixologists_tunic",
    "brd_barman_shanker", "brd_rock_golem_bulwark", "brd_stone_of_the_earth", "brd_shalehusk_boots",
)

# Doomgrip's Vault four (SP rulings 44 and 45; items.csv base ids 22205 / 22254 / 22255 / 22256).
VAULT_FOUR = (
    "brd_black_steel_bindings", "brd_wand_of_eternal_light", "brd_magma_forged_band", "brd_mana_shaping_handwraps",
)

# WARNING: the heroic lootids below are the PREDICTED heroic entries of the first write run's mint (310301 on,
# normal-entry order, source/world/heroic_ids.lock), copied by hand from source/world/dungeons/blackrock_depths.py's
# `_boss(...)` overrides and from lib/test_blackrock_depths_loot.py's BOSSES. If another branch appends lock lines
# first, every number shifts: `test_the_predicted_heroic_lootids_still_hold` (lib/test_blackrock_depths_loot.py) fails
# with the exact fix, and so does lib/test_blackrock_depths_heroic.py.
#
# Normal lootid, heroic lootid (the heroic body's own entry), list (item() keys), Molten token key (None: no token),
# the stock group 1 rows the list replaces (item_template entries), token loot mode, whether the boss carries the 5%
# Dark Keeper Key.
BOSS_LISTS = (
    # --- Section 1: the Detention Block ---
    (9018, 310343, (  # High Interrogator Gerstahn
        "brd_kentic_amice", "brd_greaves_of_withering_despair", "brd_blackveil_cape",
    ), None, (
        11625,  # Enthralled Sphere
    ), 1, True),
    (9025, 310346, (  # Lord Roccor
        "brd_stoneshell_guard", "brd_earthslag_shoulders", "brd_idol_of_ferocity",
    ), None, (
        22234,  # Mantle of Lost Hope
    ), 1, False),
    (9319, 310366, (  # Houndmaster Grebmar
        "brd_houndmasters_bow", "brd_fleetfoot_greaves", "brd_spritecaster_cape",
    ), None, (
        11629,  # Houndmaster's Rifle
    ), 1, True),
    # --- The Ring of Law: each champion drops 1 of 2; the legs token on whichever carries the title ---
    (9027, 310347, (  # Gorosh the Dervish
        "brd_savage_gladiator_chain", "brd_bloodclot_band",
    ), "molten_token_legs", (
        22266,  # Flarethorn
        22271,  # Leggings of Frenzied Magic
    ), LOOT_MODE_TITLE_HOLDER, False),
    (9028, 310348, (  # Grizzle
        "brd_entrenching_boots", "brd_grizzles_skinner",
    ), "molten_token_legs", (
        11703,  # Stonewall Girdle
        11722,  # Dregmetal Spaulders (moved to Loregrain)
    ), LOOT_MODE_TITLE_HOLDER, False),
    (9029, 310349, (  # Eviscerator
        "brd_savage_gladiator_grips", "brd_spell_eaters_choker",
    ), "molten_token_legs", (
        11679,  # Rubicund Armguards
        11685,  # Splinthide Shoulders
        11686,  # Girdle of Beastial Fury
    ), LOOT_MODE_TITLE_HOLDER, False),
    (9030, 310350, (  # Ok'thor the Breaker
        "brd_cyclopean_band", "brd_ogreseer_fists",
    ), "molten_token_legs", (
        11662,  # Ban'thok Sash
        11728,  # Savage Gladiator Leggings
    ), LOOT_MODE_TITLE_HOLDER, False),
    (9031, 310351, (  # Anub'shiah (the Carapace leaves stock group 2, below)
        "brd_carapace_of_anubshiah", "brd_graverot_cape",
    ), "molten_token_legs", (
        11675,  # Shadefiend Boots
        11731,  # Savage Gladiator Greaves
    ), LOOT_MODE_TITLE_HOLDER, False),
    (9032, 310352, (  # Hedrum the Creeper
        "brd_hookfang_shanker", "brd_spiderfang_carapace",
    ), "molten_token_legs", (
        11634,  # Silkweb Gloves
        11729,  # Savage Gladiator Helm
    ), LOOT_MODE_TITLE_HOLDER, False),
    # --- Section 2: Shadowforge City ---
    (9024, 310345, (  # Pyromancer Loregrain
        "brd_kindling_stave", "brd_flamestrider_robes", "brd_dregmetal_spaulders",
    ), None, (
        11748,  # Pyric Caduceus
        11749,  # Searingscale Leggings
    ), 1, True),
    (9041, 310361, (  # Warder Stilgiss (and Verek: one encounter, one list)
        "brd_boreal_mantle", "brd_arbiters_blade", "brd_dark_warders_pauldrons", "brd_vereks_collar",
    ), None, (
        11783,  # Chillsteel Girdle
    ), 1, True),
    (9476, 310375, VAULT_FOUR, None, (), 1, True),  # Watchman Doomgrip (his replaced rows are below)
    (9017, 310342, (  # Lord Incendius
        "brd_undying_ember", "brd_anvilfire_grips", "brd_robe_of_the_elemental_lord",
    ), "molten_token_wrist", (
        11764,  # Cinderhide Armsplints
        11765,  # Pyremail Wristguards
        11766,  # Flameweave Cuffs
        11767,  # Emberplate Armguards
    ), 1, False),
    (9016, 310341, (  # Bael'Gar
        "brd_rubidium_hammer", "brd_force_of_magma", "brd_magmaheart_mantle",
    ), None, (
        11802,  # Lavacrest Leggings
        11807,  # Sash of the Burning Heart
    ), 1, False),
    (9056, 310363, MINOR_POOL, None, (  # Fineous Darkvire (the minor pool; Ironfel and the Shirt stay in group 0)
        11839,  # Chief Architect's Monocle
        11841,  # Senior Designer's Pantaloons
        11842,  # Lead Surveyor's Mantle
        22223,  # Foreman's Head Protector
    ), 1, True),
)
for _normal, _heroic, _items, _token, _replaced, _token_mode, _key in BOSS_LISTS:
    _boss_lists(_normal, _heroic, _items, _token, _replaced, _token_mode, _key)

# Panzor the Invincible (rare spawn): the minor pool at the Normal tier on his stock lootid. No heroic template.
_boss_lists(8923, None, MINOR_POOL, replaced_items=(
    22245,  # Soot Encrusted Footwear
))

# Anub'shiah's stock group 2 held the Carapace (15%, a list item now): it would drop twice.
remove_loot_rows(9031, (11678,), group=2,
                 why="the Carapace of Anub'shiah is on his list (group 1); the stock group 2 row would drop it twice")

# Verek's stock group 1 (the Collar 12%, the Leash 13%): the Collar is on Stilgiss's list, the Leash is cut. Verek keeps
# his group 0 (meat, scraps, the note) and the group 5 world pool.
remove_loot_group(9042, group=LIST_GROUP, replaces_items=(22242,),
                  why="Stilgiss and Verek are one encounter and one list of 4 (on Stilgiss); the Collar moved to it, "
                      "Verek's Leash is cut")

DOOMGRIP_STOCK = 9476

# Doomgrip's group 0 strays: the Seven chest's four stock items (2-3%), his Vault four (now the list), and thirteen
# world blues under 1% (Ribsplitter, The Judge's Gavel, Mar Alom's Grip, Runed Golem Shackles, Blisterbane Wrap, the
# Codexes, the Books, the Tome, the Elementals cards).
DOOMGRIP_GROUP_0_CUTS = (
    11920, 11923, 11926, 11929,  # Wraith Scythe, Hammer of Grace, Deathdealer Breastplate, Haunting Specter Leggings
    22205, 22254, 22255, 22256,  # the Vault's four (his list now)
    12527, 12528, 12547, 12550, 12552, 17413, 17414, 17682, 17683, 18600, 19272, 19283, 22393,  # world blues
)
remove_loot_rows(DOOMGRIP_STOCK, DOOMGRIP_GROUP_0_CUTS, group=0,
                 why="Doomgrip's stray stock rows leave with the Vault rework (SP Loot): the Seven chest items, the "
                     "Vault four (now his list) and the world blues under 1%")

# --- hard mode lists (heroic only) ------------------------------------------------------------------------------------

# The Encore: on Theldren, the last of the five to die (D6). One item on a lit kill, on top of the heroic items.
THELDREN_HEROIC = 310390
ENCORE_HARD_MODE = ("brd_theldrens_executioner", "brd_leftys_shiv", "brd_korvs_spirit_fetish")
boss_loot(THELDREN_HEROIC, ENCORE_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP, loot_mode=LOOT_MODE_HARD_MODE_1,
          hard_mode_only=True)  # Theldren drops no gear list: the Encore list is his only one

# Lord of the Lake: on Incendius's heroic lootid (the giant is Incendius). The loot bit is set at the pull (D12).
INCENDIUS_HEROIC = 310342
LAKE_LORD_HARD_MODE = ("brd_black_anvil_bulwark", "brd_fist_of_the_lake_lord", "brd_scepter_of_the_molten_lake")
boss_loot(INCENDIUS_HEROIC, LAKE_LORD_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP,
          loot_mode=LOOT_MODE_HARD_MODE_1)


# =====================================================================================================================
# Wave 2: sections 3 and 4 (Blackrock Depths build, WP-L-2)
# =====================================================================================================================
#
# The same shape as wave 1 (groups 1 list / 2 hard mode / 3 token / 4 key, the Normal tier on the stock lootid and the
# Heroic tier on the heroic body's own lootid), for the nine bosses that point at their own heroic lootid once
# BIND_WAVE_2 flips (`_wave("2", ...)` in blackrock_depths.py): every one of them is declared below, so none drops
# nothing on heroic (lib/loot_tables.py `_check_creatures` errors on a heroic boss whose own lootid has no declaration).
#
# - Angerforge, Argelmach, Phalanx, Flamelash, Magmus: their approved lists of 3 (blackrock-depths-rework.md ## Loot,
#   Sections 3 and 4); the cut stock rows are `replaces_items`. Argelmach also drops the Molten waist token
#   (group 3, every difficulty) and, on his heroic lootid, the Prototype's three items (group 2, LootMode 2: set at the
#   console, D16 / the instance's `ApplyHardModeLoot`).
# - Hurley, Ribbly and Plugger drop one of the minor pool's eight (ruling 86). Hurley's stock group 1 is all pool items
#   (his Ragefury Eyepatch is cut), so the pool takes group 1. Ribbly's and Plugger's stock group 1 also hold rows that
#   are no gear and no cut (Ribbly's two ammo bags and Wayfarer's Knapsack, Plugger's Schematic: Goblin Jumper Cables
#   XL): the pool goes in group 5 beside them, and Plugger's two pool items leave group 1 (`remove_loot_rows`).
# - The Emperor: 2 distinct items of his 8 (a `picks=2` list, pools 1700019 normal / 1700020 heroic of the
#   `loot_reference` block; the stock group 1 reference 35014, 2 of 11, goes with its pool), the Molten head token
#   (group 3), the 5% Dark Keeper Key and, at Heroic Hard Mode (the Avatar, LootMode 2), the three hard mode items
#   (group 2) and the key at 100%: the key group holds the 5% row at LootMode 1 and a 95% row at LootMode 2 (pool
#   1700021), rolled in turn, so a lit kill (mode 3) always yields exactly one key and never two. Moira's list (stock
#   lootid 8929, shared with the High Priestess; no heroic copy of her own) is emptied: her four pieces are in the
#   Emperor's list and the Chest of The Seven.
# - 5% Dark Keeper Key (ruling 36) on Angerforge, Argelmach, Hurley, Plugger and the Emperor.
# - The Chest of The Seven (gameobject loot 12260) and the Seven's section are hand SQL
#   (rev_loot_wave_2_blackrock_depths.sql); the Seven have no corpse loot.

ARGELMACH_HARD_MODE = (
    "brd_prototype_power_core", "brd_golemwrights_mending_rod", "brd_electrons_lethal_coil",
)
AVATAR_HARD_MODE = ("brd_ironfoe", "brd_volcanic_heartstone", "brd_orb_of_the_sorcerer_thane")

# The Emperor's 8 (his five stock pieces, Moira's two Cloth Spirit pieces and the Wayward Princess idol): 2 per kill.
EMPEROR_LIST = (
    "brd_hand_of_justice", "brd_robes_of_the_royal_crown", "brd_thaurissans_royal_scepter",
    "brd_the_emperors_new_cape", "brd_imperial_jewel", "brd_hands_of_the_exalted_herald",
    "brd_high_priestess_boots", "brd_idol_of_the_wayward_princess",
)
EMPEROR_PICKS = 2
# `loot_reference` block ids (source/ids.yaml; BRS ended at 1700018).
EMPEROR_POOL_NORMAL = 1700019
EMPEROR_POOL_HEROIC = 1700020
AVATAR_KEY_POOL = 1700021
EMPEROR_STOCK_REFERENCE = 35014  # stock group 1: 2 rolls of the Emperor's 11 (Ironfoe 1%, ...); replaced by the list
AVATAR_KEY_CHANCE = 100 - DARK_KEEPER_KEY_CHANCE  # the hard mode row: 5% + 95% = a key on every lit kill
MOIRA_LOOTID = 8929  # Princess Moira Bronzebeard and the High Priestess of Thaurissan
SIDE_POOL_GROUP = 5  # the minor pool on a boss whose stock group 1 keeps non-gear rows (Ribbly, Plugger)

# Normal lootid, heroic lootid (the heroic body's own entry, predicted by blackrock_depths.py `_boss(...)`), list,
# Molten token key, the stock rows the list replaces, token loot mode, the 5% Dark Keeper Key. Same shape as BOSS_LISTS.
WAVE_2_BOSS_LISTS = (
    # --- Section 3: the Manufactory ---
    (9033, 310353, (  # General Angerforge
        "brd_angerforges_battle_axe", "brd_lord_generals_sword", "brd_royal_decorated_armor",
    ), None, (
        11810,  # Force of Will
        11821,  # Warstrife Leggings
    ), 1, True),
    (8983, 310340, (  # Golem Lord Argelmach
        "brd_second_wind", "brd_naglering", "brd_omnicast_boots",
    ), "molten_token_waist", (
        11823,  # Luminary Kilt
    ), 1, True),
    # --- Section 4: the Imperial Seat ---
    (9537, 310378, MINOR_POOL, None, (  # Hurley Blackbreath (the minor pool; the Eyepatch is cut)
        11735,  # Ragefury Eyepatch
    ), 1, True),
    (9502, 310377, (  # Phalanx
        "brd_bloodfist", "brd_fists_of_phalanx", "brd_golem_fitted_pauldrons",
    ), None, (
        11743,  # Rockfist
    ), 1, False),
    (9156, 310364, (  # Ambassador Flamelash
        "brd_flame_wrath", "brd_burst_of_knowledge", "brd_molten_fists",
    ), None, (
        11808,  # Circle of Flame
        11812,  # Cape of the Fire Salamander
    ), 1, False),
    (9938, 310382, (  # Magmus
        "brd_magmus_stone", "brd_totem_of_rage", "brd_libram_of_truth",
    ), None, (
        11746,  # Golem Skull Helm
        22208,  # Lavastone Hammer
    ), 1, False),
)
for _normal, _heroic, _items, _token, _replaced, _token_mode, _key in WAVE_2_BOSS_LISTS:
    _boss_lists(_normal, _heroic, _items, _token, _replaced, _token_mode, _key)

# Argelmach's hard mode (the Prototype, D16): his heroic lootid's group 2, on top of the list.
ARGELMACH_HEROIC = 310340
boss_loot(ARGELMACH_HEROIC, ARGELMACH_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP,
          loot_mode=LOOT_MODE_HARD_MODE_1)

# Ribbly Screwspigot (9543 / 310380) and Plugger Spazzring (9499 / 310376): one of the minor pool's eight, in group 5 so
# the stock group 1 rows that are neither gear nor cut stay (Ribbly's Quiver, Bandolier and Wayfarer's Knapsack;
# Plugger's Schematic: Goblin Jumper Cables XL). Plugger's Mixologist's Tunic and Barman Shanker are pool items now.
RIBBLY_NORMAL, RIBBLY_HEROIC = 9543, 310380
PLUGGER_NORMAL, PLUGGER_HEROIC = 9499, 310376
_boss_lists(RIBBLY_NORMAL, RIBBLY_HEROIC, MINOR_POOL, list_group=SIDE_POOL_GROUP)
_boss_lists(PLUGGER_NORMAL, PLUGGER_HEROIC, MINOR_POOL, dark_keeper_key=True, list_group=SIDE_POOL_GROUP)
remove_loot_rows(PLUGGER_NORMAL, (12793, 12791), group=LIST_GROUP,
                 why="Mixologist's Tunic and Barman Shanker are in the minor pool (group 5); the Schematic stays")

# The Emperor Dagran Thaurissan (9019 / 310344): 2 of his 8, the Molten head token, the 5% Dark Keeper Key.
EMPEROR_NORMAL, EMPEROR_HEROIC = 9019, 310344
_boss_lists(EMPEROR_NORMAL, EMPEROR_HEROIC, EMPEROR_LIST, "molten_token_head", dark_keeper_key=True,
            picks=EMPEROR_PICKS, references=(EMPEROR_POOL_NORMAL, EMPEROR_POOL_HEROIC),
            replaced_references=(EMPEROR_STOCK_REFERENCE,))
remove_reference_pool(EMPEROR_STOCK_REFERENCE,
                      why="the Emperor's two rolls of the stock pool of 11 are his list of 8 (picks=2); Ironfoe is "
                          "the Avatar's, the rest are cut")
# The Avatar (D24): the hard mode list on top of the heroic list, and the key at 100% (5% + 95%, see above).
boss_loot(EMPEROR_HEROIC, AVATAR_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP, loot_mode=LOOT_MODE_HARD_MODE_1)
loot_chance(EMPEROR_HEROIC, DARK_KEEPER_KEY, AVATAR_KEY_CHANCE, KEY_GROUP, LOOT_MODE_HARD_MODE_1,
            reference=AVATAR_KEY_POOL, name="Dark Keeper Key")

# Princess Moira Bronzebeard / the High Priestess of Thaurissan: the stock list (the High Priestess Boots, Hands of the
# Exalted Herald, Swiftwalker Boots, Ebonsteel Spaulders) is emptied. Her group 0 (the Fanny Pack, the Note, the
# runecloth and Dark Iron rows, the Relic Coffer Key) stays: killing or saving her drops the Emperor's list only.
remove_loot_group(MOIRA_LOOTID, group=LIST_GROUP, replaces_items=(12556, 12554, 12553, 12557),
                  why="Moira's pieces are in the Emperor's list (the two Cloth Spirit ones) and the Chest of The "
                      "Seven (Ebonsteel Spaulders, Swiftwalker Boots)")
