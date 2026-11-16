"""
The Blackrock Spire boss loot, wave 1 (the Lower Spire; Blackrock Spire build, WP-L-1): each boss's approved list
(docs/dungeons/blackrock-spire-rework.md ## Loot, rulings 76-79, copied in docs/dungeons/dungeon-loot-vanilla.md) as one
loot group of equal-chance entries, on the stock lootid at the Normal tier and on the heroic body's own lootid at the
Heroic tier (lib/dsl/loot.py, lib/loot_tables.py). The items are declared in blackrock_spire.py (and the hard mode
effects in blackrock_spire_hard_mode_effects.py), the Molten tokens in molten_set.py. The shape is the Stratholme one
(stratholme_loot.py). Wave 2 (the Upper Spire, WP-L-2) is the section at the end of this file; nothing in
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
    remove_reference_pool,
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


# =====================================================================================================================
# Wave 2: the Upper Spire (Blackrock Spire build, WP-L-2)
# =====================================================================================================================
#
# The same shape as wave 1 (groups 1 list, 2 hard mode, 3 token, 11 / 12 / 13 the flex copies, the heroic lootid = the
# heroic body's own entry), with two differences:
#
# - **Two-item kills.** Rend and Gyth are two creatures with a lootid each, like the wolves: each drops ONE item of the
#   one shared ten item list (the pair drops two). The Beast and Drakkisath are one creature each, so their list is a
#   `picks=2` list (a pool of its own in the `loot_reference` block, two DISTINCT items; Stratholme's Baron). A `picks`
#   list's flex copy is a `picks=2` list of its own pool (the table's key is (Entry, GroupId), and a pool belongs to
#   one declaration), so the 10 player kill rolls four distinct-within-a-roll items.
#   Reference ids 1700011-1700018 (the block's next free, source/ids.yaml): the Beast 1700011 normal / 1700012 heroic /
#   1700013 flex normal / 1700014 flex heroic, Drakkisath 1700015 / 1700016 / 1700017 / 1700018.
# - **Stock two-roll references.** Rend's 35022, the Beast's 35023 and Drakkisath's 35025 are `reference_loot_template`
#   pools (the stock two rolls, SP implementation note 12): Rend's and the Beast's sit in group 1
#   (`replaces_references`), Drakkisath's in group 0 (`remove_loot_rows(references=)`). Nothing else uses them (checked
#   over every loot table), so the pools are deleted (`remove_reference_pool`). The Tier 0 pieces on the other
#   lootids: Emberseer's Gauntlets of Elements, Solakar's Devout Mantle, Gyth's Pauldrons of Elements and Drakkisath's
#   nine chests (his stock group 1) are named in `replaces_items`, with the cut pieces of the token slots.
#
# **Molten tokens**: Rend carries the Molten Boots (one per full clear: his death is the encounter's end, the exit door;
# Gyth drops list items and no token) and Drakkisath the Molten Chestpiece. **Hard mode** (heroic only): Drakkisath's
# General's Army list, group 2 of his heroic lootid at LootMode 2 (`DungeonKit::SetHardModeLoot` while the hard mode is
# lit; the instance sets the bit), its flex copy at group 12 / LootMode 8. Emberseer's world drop tree (reference
# 1000260, group 5), the recipes, the pools and the quest rows stay: group 0 holds them, and group 5 is no declared
# group. Removed group 0 rows: Bonespike Shoulder (Rend's 1%, cut with the shoulder slot) and Drakkisath's 35025 row.

REND_GYTH_LIST = (
    "brs_blackhand_doomsaw", "brs_eye_of_rend", "brs_felstriker", "brs_warmaster_legguards",
    "brs_battleborn_armbraces", "brs_dalrends_sacred_charge", "brs_dalrends_tribal_guardian", "brs_gyths_skull",
    "brs_dragoneye_coif", "brs_tribal_war_feathers",
)
BEAST_LIST = (
    "brs_finkles_skinner", "brs_blademaster_leggings", "brs_tristam_legguards", "brs_blackmist_armguards",
    "brs_bloodmoon_cloak", "brs_seeping_willow", "brs_idol_of_the_core_hound",
)
DRAKKISATH_LIST = (
    "brs_blackblade_of_shahram", "brs_draconian_deflector", "brs_painweaver_band", "brs_tooth_of_gnarr",
    "brs_brigam_girdle", "brs_tome_of_the_lost", "brs_spellweavers_turban", "brs_draconic_infused_emblem",
    "brs_shadow_prowlers_cloak", "brs_libram_of_the_dragon_guard",
)
UPPER_PICKS = 2  # the Beast's and Drakkisath's items per kill (stock two rolls)

REND_STOCK_POOL, BEAST_STOCK_POOL, DRAKKISATH_STOCK_POOL = 35022, 35023, 35025


def _upper_boss_lists(normal_lootid, heroic_lootid, items, token, replaced_items, replaced_references=(),
                      picks=1, references=None):
    """One Upper Spire boss: the list and the token (when it has one) at the Normal and the Heroic tier on the two
    lootids, then their flex copies (as `_boss_lists`, plus the `picks=` lists' pools: `references` is the four ids of
    the normal list, the heroic list, their flex copies, in that order)."""
    def one(lootid, tier, group, loot_mode, ref, **replaces):
        extra = dict(picks=picks, reference=ref) if picks > 1 else {}
        boss_loot(lootid, items, tier=tier, group=group, loot_mode=loot_mode, **extra, **replaces)

    refs = references or (None, None, None, None)
    one(normal_lootid, "normal", LIST_GROUP, 1, refs[0], replaces_items=replaced_items,
        replaces_references=replaced_references)
    one(heroic_lootid, "heroic", LIST_GROUP, 1, refs[1])
    one(normal_lootid, "normal", FLEX_LIST_GROUP, LOOT_MODE_FLEX, refs[2])
    one(heroic_lootid, "heroic", FLEX_LIST_GROUP, LOOT_MODE_FLEX, refs[3])
    if token is not None:
        boss_loot(normal_lootid, (token,), tier="normal", group=TOKEN_GROUP)
        boss_loot(heroic_lootid, (token,), tier="heroic", group=TOKEN_GROUP)
        boss_loot(normal_lootid, (token,), tier="normal", group=FLEX_TOKEN_GROUP, loot_mode=LOOT_MODE_FLEX)
        boss_loot(heroic_lootid, (token,), tier="heroic", group=FLEX_TOKEN_GROUP, loot_mode=LOOT_MODE_FLEX)


# WARNING: the heroic lootids are PREDICTIONS, like wave 1's (see the warning above BOSS_LISTS): the wave 2 bosses are
# the lock's 310241 / 310255 / 310262 / 310263 / 310270 / 310271 (normal-entry order from 310195; wave 2 kit adds mint
# after them, 310295 on), copied by hand from source/world/dungeons/blackrock_spire.py's `_wave("2", ...)` overrides
# into this table and lib/test_blackrock_spire_loot.py's UPPER_BOSSES. `test_the_predicted_heroic_lootids_still_hold`
# and test_blackrock_spire_heroic.py::test_the_predicted_lock_lines fail with the fix if the mint shifts.
#
# Normal lootid, heroic lootid, list, Molten token key, the stock group 1 rows the list replaces (item_template
# entries), the stock pool references it replaces, picks, the four pool ids (picks lists only).
UPPER_BOSS_LISTS = (
    (9816, 310241, (  # Pyroguard Emberseer
        "brs_wildfire_cape", "brs_emberfury_talisman", "brs_helm_of_the_bound_flame", "brs_incarcerators_wand",
    ), None, (
        12926,  # Flaming Band
        12927,  # Truestrike Shoulders
        16672,  # Gauntlets of Elements (Tier 0)
    ), (), 1, None),
    (10264, 310255, (  # Solakar Flamewreath
        "brs_dustfeather_sash", "brs_crystallized_girdle", "brs_feralsurge_girdle", "brs_flamewreath_legplates",
    ), None, (
        12603,  # Nightbrace Tunic
        12609,  # Polychromatic Visionwrap
        16695,  # Devout Mantle (Tier 0)
    ), (), 1, None),
    (10429, 310270, REND_GYTH_LIST, "molten_token_feet", (), (REND_STOCK_POOL,), 1, None),  # Rend
    (10339, 310262, REND_GYTH_LIST, None, (  # Gyth
        16669,  # Pauldrons of Elements (Tier 0)
        22225,  # Dragonskin Cowl
    ), (), 1, None),
    (10430, 310271, BEAST_LIST, None, (), (BEAST_STOCK_POOL,), UPPER_PICKS,
     (1700011, 1700012, 1700013, 1700014)),  # The Beast
    (10363, 310263, DRAKKISATH_LIST, "molten_token_chest", (  # General Drakkisath: his nine Tier 0 chests
        16666,  # Vest of Elements
        16674,  # Beaststalker's Tunic
        16688,  # Magister's Robes
        16690,  # Devout Robe
        16700,  # Dreadmist Robe
        16706,  # Wildheart Vest
        16721,  # Shadowcraft Tunic
        16726,  # Lightforge Breastplate
        16730,  # Breastplate of Valor
    ), (), UPPER_PICKS, (1700015, 1700016, 1700017, 1700018)),
)
for _normal, _heroic, _items, _token, _replaced, _pools, _picks, _refs in UPPER_BOSS_LISTS:
    _upper_boss_lists(_normal, _heroic, _items, _token, _replaced, _pools, _picks, _refs)

# Drakkisath's hard mode list (the General's Army; heroic only): one item on a lit kill, on top of the heroic items, and
# its second roll at 10 players.
DRAKKISATH_HEROIC = 310263
DRAKKISATH_HARD_MODE = ("brs_trophy_of_the_champion", "brs_orders_of_the_general", "brs_the_humbler")
boss_loot(DRAKKISATH_HEROIC, DRAKKISATH_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP,
          loot_mode=LOOT_MODE_HARD_MODE_1)
boss_loot(DRAKKISATH_HEROIC, DRAKKISATH_HARD_MODE, tier="heroic_hm", group=FLEX_HARD_MODE_GROUP,
          loot_mode=LOOT_MODE_FLEX_HARD_MODE)

# The stock group 0 rows that go: Rend's Bonespike Shoulder (a shoulder, cut with the slot rule) and Drakkisath's two
# rolls on the pool 35025 (his list replaces them). The heroic copies are made without them.
remove_loot_rows(10429, (12588,), group=0,
                 why="Bonespike Shoulder: the shoulder slot is the Molten token's, so the 1% mail shoulder is cut "
                     "(SP Structure 4)")
remove_loot_rows(10363, group=0, references=(DRAKKISATH_STOCK_POOL,),
                 why="Drakkisath's list replaces his two rolls on the pool 35025")
# The three stock pools nothing uses once the lists replace them (checked over every loot table).
remove_reference_pool(REND_STOCK_POOL, why="Rend's list replaces his two rolls on it")
remove_reference_pool(BEAST_STOCK_POOL, why="The Beast's list replaces his two rolls on it")
remove_reference_pool(DRAKKISATH_STOCK_POOL, why="Drakkisath's list replaces his two rolls on it")
