"""
The Blackrock Spire boss loot, wave 1 (the Lower Spire; Blackrock Spire build, WP-L-1): each boss's approved list
(docs/dungeons/blackrock-spire-rework.md ## Loot, rulings 76-79, copied in docs/dungeons/dungeon-loot-vanilla.md) as one
loot group of equal-chance entries, on the stock lootid at the Normal tier and on the heroic body's own lootid at the
Heroic tier (lib/dsl/loot.py, lib/loot_tables.py). The items are declared in blackrock_spire.py (and the hard mode
effects in blackrock_spire_hard_mode_effects.py), the Molten tokens in molten_set.py. The shape is the Stratholme one
(stratholme_loot.py). Wave 2 (the Upper Spire, WP-L-2) appends its own section at the end of this file; nothing in
wave 1's declarations touches the Upper Spire bosses' stock rows.

- **Group 1** of each boss is the list: one item per kill, two for Halycon and Gizrul (one per wolf, below). Omokk 3
  items, Vosh'gajin 4, Voone 5, Smolderweb 3, Urok 3, Zigris 3, Halycon and Gizrul 6 (shared), Wyrmthalak 6. The stock
  group 1 held the boss's items, one Tier 0 piece (cut; Voone's and Wyrmthalak's give way to a Molten token) and the
  pieces cut by the slot rule (standalone shoulder, chest, hands and feet): the declarations name those rows
  (`replaces_items`). Every stock row of a declared group that the list does not carry is named; an unnamed one stops
  the run.
- **Halycon and Gizrul** keep the stock two lootids (one per wolf, "one per wolf, stock", SP Loot, Structure 3): both
  declare the same six-item list, so each wolf drops one item of it and the pair two. The two rolls are independent
  (different corpses), so the pair can drop the same item twice (a designer question in the STAGE-L-1 report).
- **Molten tokens** (Structure 1): Voone the Molten Gloves, Wyrmthalak the Molten Shoulders. Each is a group of its own
  (group 3, one entry, so it always drops) on top of the list item: the token of the kill's tier (Normal on a normal
  lootid, Heroic on a heroic one). The Upper Spire's two (Rend and Gyth the boots, Drakkisath the chest) are L-2's.
- **Group 0** (grays, reagents, runecloth, Dark Iron Scraps, the Unadorned Seal of Ascension, the Gemstones, Snakestone,
  Blackrock Bracer, Warosh's Mojo, Ogre Warbeads, Black Dragonspawn Eye, the plans and the spider reagents) stays on the
  normal lootids untouched: a generic pool rolls on top, never instead. Heroic bodies keep them as copies, with their
  loot conditions (lib/loot_tables.py derive_heroic_copies). The rows that go are group 0 rows: Omokk's Head (ruling
  39), Doomshot (no ammo on this server), Voone's Twitchbow and his 100% Flightblade Throwing Axe row (the axe is on his
  list now), Wyrmthalak's three explicit-chance rares (Mark of the Dragon Lord 2%, Chillpike 1%, Heart of the Scale 1%:
  they join his equal-chance list, SP Structure 4).
- **Roughshod Pike** (ruling 39) is not a creature drop: it is the loot of the Scarshield camp object 175886
  (`gameobject_loot_template` 13340), which the DSL cannot declare; pending SQL
  `rev_blackrock_spire_loot_cuts.sql` deletes the row.
- **Hard mode** (heroic only): group 2 of Wyrmthalak's heroic lootid 310228 holds the three war horn items at Heroic
  Hard Mode (71) with `LootMode` 2 (`LOOT_MODE_HARD_MODE_1`), on top of the heroic list, exactly as Stratholme's Baron
  (DungeonKit::SetHardModeLoot adds the bit while the hard mode is lit).
- **The flex second roll** (handoff 7.1 #6, A): at 10 players every count doubles, tokens and hard mode items
  included. Every list, token and hard mode group has a copy in a group of its own at `LootMode` 4 (the hard mode list
  at 8): FLEX_LIST_GROUP 11, FLEX_HARD_MODE_GROUP 12, FLEX_TOKEN_GROUP 13. The boss script lights the bits at the pull
  (`DungeonKit::Flex::SetFlexLoot`, held count 10: 4, and 8 with the hard mode), so a 10 player kill rolls the list
  twice (group 1 at bit 1, group 11 at bit 4), the token twice, the hard mode list twice; at 5 players the copies sit
  out (`LootGroupInvalidSelector`). A group is a table key (Entry, GroupId), which is why the copy is a group of its
  own, and the two rolls are independent, so the same item can drop twice. The copies are on both difficulties'
  lootids, the hard mode copy on the heroic one.
"""

from lib.dsl.loot import (
    LOOT_MODE_HARD_MODE_1,
    boss_loot,
    remove_loot_rows,
)

LIST_GROUP = 1  # the boss's list: one equal-chance entry per item
HARD_MODE_GROUP = 2  # the heroic lootid's hard mode list at LootMode 2
TOKEN_GROUP = 3  # a Molten token: one entry, always drops, apart from the list (group 1)
FLEX_LIST_GROUP = 11  # the second roll of the list at 10 players (LootMode 4)
FLEX_HARD_MODE_GROUP = 12  # the second roll of the hard mode list at 10 players (LootMode 8)
FLEX_TOKEN_GROUP = 13  # the second roll of the token at 10 players (LootMode 4)
LOOT_MODE_FLEX = 0x4  # DungeonKit::Flex::kLootModeFlex (LOOT_MODE_HARD_MODE_2)
LOOT_MODE_FLEX_HARD_MODE = 0x8  # DungeonKit::Flex::kLootModeFlexHardMode (LOOT_MODE_HARD_MODE_3)


def _boss_lists(normal_lootid, heroic_lootid, items, token, replaced_items):
    """One boss: the list and the token (when it has one) at the Normal and the Heroic tier on the two lootids, then
    their flex copies. Only the normal list names the stock rows it replaces."""
    boss_loot(normal_lootid, items, tier="normal", replaces_items=replaced_items)
    boss_loot(heroic_lootid, items, tier="heroic")
    boss_loot(normal_lootid, items, tier="normal", group=FLEX_LIST_GROUP, loot_mode=LOOT_MODE_FLEX)
    boss_loot(heroic_lootid, items, tier="heroic", group=FLEX_LIST_GROUP, loot_mode=LOOT_MODE_FLEX)
    if token is not None:
        boss_loot(normal_lootid, (token,), tier="normal", group=TOKEN_GROUP)
        boss_loot(heroic_lootid, (token,), tier="heroic", group=TOKEN_GROUP)
        boss_loot(normal_lootid, (token,), tier="normal", group=FLEX_TOKEN_GROUP, loot_mode=LOOT_MODE_FLEX)
        boss_loot(heroic_lootid, (token,), tier="heroic", group=FLEX_TOKEN_GROUP, loot_mode=LOOT_MODE_FLEX)


# Halycon and Gizrul share one list; each wolf's own lootid drops one item of it (see the module docstring).
HALYCON_GIZRUL_LIST = (
    "brs_slashclaw_bracers", "brs_halycons_spiked_collar", "brs_rhombeard_protector", "brs_wolfshear_leggings",
    "brs_bleak_howler_armguards", "brs_packleaders_hide_belt",
)

# WARNING: the heroic lootids below are PREDICTIONS of the first write run's mint (310195 on, normal-entry order,
# source/world/heroic_ids.lock), copied by hand into source/world/dungeons/blackrock_spire.py's `_boss(...)` overrides
# and lib/test_blackrock_spire_loot.py's BOSSES. If another branch appends lock lines first, every number shifts: then
# `test_the_predicted_heroic_lootids_still_hold` (lib/test_blackrock_spire_loot.py) fails with the exact fix, and so
# does test_blackrock_spire_heroic.py::test_the_predicted_lock_lines. Run both before the write run.
#
# Normal lootid, heroic lootid (the heroic body's own entry, heroic_ids.lock; source/world/dungeons/
# blackrock_spire.py), list (item() keys), Molten token key (None: no token), the stock group 1 rows the list replaces
# (item_template entries: the Tier 0 piece and the cut pieces of the token slots).
BOSS_LISTS = (
    (9196, 310199, (  # Highlord Omokk
        "brs_fist_of_omokk", "brs_tressermane_leggings", "brs_skyshroud_leggings",
    ), None, (
        13166,  # Slamshot Shoulders
        13168,  # Plate of the Shaman King
        16670,  # Boots of Elements (Tier 0)
    )),
    (9236, 310209, (  # Shadow Hunter Vosh'gajin
        "brs_funeral_cuffs", "brs_blackcrow", "brs_riphook", "brs_totem_of_hexed_blood",
    ), None, (
        13255,  # Trueaim Gauntlets
        13257,  # Demonic Runed Spaulders
        16712,  # Shadowcraft Gloves (Tier 0)
    )),
    (9237, 310210, (  # War Master Voone
        "brs_keris_of_zulserak", "brs_talisman_of_evasion", "brs_brazecore_armguards",
        "brs_flightblade_throwing_axe", "brs_war_masters_hatchet",
    ), "molten_token_hands", (
        16676,  # Beaststalker's Gloves (Tier 0; the Molten Gloves token replaces it)
        22231,  # Kayser's Boots of Precision
    )),
    (10596, 310276, (  # Mother Smolderweb
        "brs_venomspitter", "brs_smolderwebs_eye", "brs_smolderweb_silk_sash",
    ), None, (
        13244,  # Gilded Gauntlets
        16715,  # Wildheart Boots (Tier 0)
    )),
    (10584, 310275, (  # Urok Doomhowl
        "brs_rosewine_circle", "brs_marksmans_girdle", "brs_shardlinked_coif",
    ), None, (
        13258,  # Slaghide Gauntlets
        13259,  # Ribsteel Footguards
    )),
    (9736, 310240, (  # Quartermaster Zigris
        "brs_cloudrunner_girdle", "brs_quartermasters_blunderbuss", "brs_supply_sergeants_girdle",
    ), None, (
        13253,  # Hands of Power
        16716,  # Wildheart Belt (Tier 0)
    )),
    (10220, 310250, HALYCON_GIZRUL_LIST, None, (  # Halycon
        13210,  # Pads of the Dread Wolf
        22313,  # Ironweave Bracers
    )),
    (10268, 310256, HALYCON_GIZRUL_LIST, None, (  # Gizrul the Slavener
        16718,  # Wildheart Spaulders (Tier 0)
    )),
    (9568, 310228, (  # Overlord Wyrmthalak
        "brs_trindlehaven_staff", "brs_relentless_scythe", "brs_chillpike", "brs_heart_of_wyrmthalak",
        "brs_mark_of_the_dragon_lord", "brs_heart_of_the_scale",
    ), "molten_token_shoulders", (
        13162,  # Reiver Claws
        16679,  # Beaststalker's Mantle (Tier 0; the Molten Shoulders token replaces it)
    )),
)
for _normal, _heroic, _items, _token, _replaced in BOSS_LISTS:
    _boss_lists(_normal, _heroic, _items, _token, _replaced)

# Wyrmthalak's hard mode list (the war horn; heroic only): one item on a lit kill, on top of the heroic items, and its
# second roll at 10 players.
WYRMTHALAK_HEROIC = 310228
WYRMTHALAK_HARD_MODE = ("brs_bloodaxe_war_horn", "brs_ward_of_the_three_tribes", "brs_shardstaff_of_stolen_power")
boss_loot(WYRMTHALAK_HEROIC, WYRMTHALAK_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP,
          loot_mode=LOOT_MODE_HARD_MODE_1)
boss_loot(WYRMTHALAK_HEROIC, WYRMTHALAK_HARD_MODE, tier="heroic_hm", group=FLEX_HARD_MODE_GROUP,
          loot_mode=LOOT_MODE_FLEX_HARD_MODE)

# The stock group 0 rows that go (cut, or on a list now): lootid -> (items, why). The heroic copies are made without
# them. Quest items, reagents, the Gemstones, runecloth and the rest of group 0 stay.
GROUP_0_CUTS = (
    (9196, (12534,), "Omokk's Head: the skull pile works once Omokk is dead, no item needed (SP ruling 39)"),
    (9236, (12654,), "Doomshot: the server has no ammo (SP ruling 76)"),
    (9237, (13175, 28972),
     "Voone's Twitchbow is cut (a green, no stats); the Flightblade Throwing Axe leaves its 100% row for his list "
     "(SP ruling 77)"),
    (9568, (13143, 13148, 13164),
     "Mark of the Dragon Lord, Chillpike and Heart of the Scale join his equal-chance list (SP Structure 4)"),
)
for _lootid, _items, _why in GROUP_0_CUTS:
    remove_loot_rows(_lootid, _items, group=0, why=_why)
