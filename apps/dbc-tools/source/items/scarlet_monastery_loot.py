"""
The Scarlet Monastery boss loot, wave 1 (sections 1 and 2: the Graveyard and the Library; Scarlet Monastery build,
WP L-1): each boss's approved list (docs/dungeons/scarlet-monastery-rework.md ## Loot "Boss lists" and "Hard mode
lists", rulings 56 to 59) as one loot group of equal-chance entries, on the stock lootid at the Normal tier and on the
heroic body's own lootid at the Heroic tier (lib/dsl/loot.py, lib/loot_tables.py). The items are declared in
scarlet_monastery.py, the hard mode items in scarlet_monastery_hard_mode.py, the Zealot's tokens in zealot_set.py. The
shape is the Blackrock Depths one (blackrock_depths_loot.py): groups 1 list / 2 hard mode / 3 token, no flex copies
(the Scarlet Monastery is a 5 player dungeon, not flex). Wave 2 (sections 3 and 4, WP L-2) appends its own block at
the end of this file; nothing in wave 1's declarations touches a section 3 or 4 boss's stock rows.

- **Group 1** of each boss is the list: one item per kill (ruling 56). Vishas 5, Ironspine 5, the council 6 (one pool,
  on the Fallen Champion), Thalnos 5, Loksey 5, Kell 4, Hollis Grey 4, Doan 5. The stock group 1 held the boss's items
  and the pieces cut by the slot rule (Embalmed Shroud and Bloodmage Mantle, token-slot pieces with no set to fit;
  Ironspine's Ribcage, Robe of Doan and Mantle of Doan, which are Zealot's set pieces now and drop from the family's
  vendor, not a boss): the declarations name those rows (`replaces_items`). The stock items the list keeps are
  `item(base=)` declarations, so their stock entry is the Normal tier and the rows are replaced in place.
- **Group 0** (Silk Cloth on every stock boss, Heart of Zeal 5805 (a quest item) on the ones that have it (Vishas,
  Loksey, Herod, Mograine, Whitemane, Doan; not Fairbanks, Thalnos, Ironspine or the council), the world-drop references
  1189000 and group 5's 1000332 on Ironspine, Azshir and the Fallen Champion) stays on the normal lootids untouched
  (handoff 7 #35): a generic pool rolls on top, never instead. Heroic bodies keep them as copies
  (lib/loot_tables.py derive_heroic_copies).
- **The council** (ruling 56, handoff 7 #35): one pool on the **Fallen Champion's** lootid (6488 / 310452), the six
  items of "Azshir and the Fallen Champion (one pool)". Azshir's stock group 1 (the Wand, the Leggings, the Talisman,
  all on the pool now) is emptied (`remove_loot_group`); his silk and the world-drop rows stay, and his heroic lootid
  310454 is a `copy_normal_loot()` of them (a heroic boss on its own lootid needs a declaration, or it drops nothing).
  Whichever of the pair is the loot recipient's real kill, the Champion's corpse carries the list (STAGE-D3: the real
  kill uses the loot recipient). Embalmed Shroud (a token slot, cut) leaves the Champion's stock group.
- **The moved Fairbanks items** (SP "Who drops what"): Branded Leather Bracers (19508) are on Vishas's list and Dusty
  Mail Boots (19509) on Kell's. They keep their stock entries as the Normal tier (`item(base=19508 / 19509)`, level
  34 / 37), so the rows 19508 and 19509 of Fairbanks's stock group 1 drop the same entries: **L-2 empties Fairbanks's
  group 1** (`remove_loot_group(4542, group=1)`; his silk stays, 4542 has no Heart of Zeal row: live SELECT), this file
  never names 4542.
- **The Zealot's Helm** (`zealot_token_head`, ruling 56): a group of its own (group 3, one entry, always drops) on
  Doan's **heroic lootid only** (310451). The family is heroic-only (ladders.py `VANILLA_HEROIC_SET` has no Normal
  tier, so a normal lootid cannot drop it), and the Graveyard drops no token.
- **Hard mode lists** (heroic only): group 2 of the heroic lootid at `LootMode` 2 (`LOOT_MODE_HARD_MODE_1`), three
  items at Heroic Hard Mode (71), on top of the heroic list. Thalnos's (the Desecration) on 310448 and Doan's (the
  Kel'Thuzad Heresy) on 310451. Both bosses are the unit that dies last in their hard mode (Thalnos with the four
  risen, Doan with the phylactery adds: the adds carry lootid 0), and the loot bit is the instance's
  (`ApplyHardModeLoot`: set at the trigger and at every pull while the flag is lit and the boss is not DONE; the loot is
  filled in `Unit::Kill` before `JustDied`, STAGE-D4H / D8H). The normal lootids get no hard mode group (heroic only).
- **New bosses** (Kell 300910, Hollis Grey 300913): no stock rows. Their lootid is their own entry on normal and the
  heroic body's own lootid (310467 / 310469) on heroic; the list is all they drop (their gold is in the template).
  They carry no Silk Cloth: the doc's "every boss also drops Silk Cloth" is its "Stock loot" section's claim about the
  stock bosses (their rows are the stock ones kept above), and the approved Kell / Hollis Grey lists name none, so a
  silk row would be an invented one. Left list-only (STAGE-R-1-LOOT designer question 1 stands).
- **Wave 2** (sections 3 and 4, WP L-2) is the second half of this file; its own docstring is above that block.
- **Not in this file**: the Last Stand chest's loot (a gameobject_loot_template list, which the loot DSL cannot
  declare: pending_db_world/rev_loot_wave_2_scarlet_monastery.sql), the Rallying Standard's, the Censer's and the other
  hard mode items' effects (scarlet_monastery_hard_mode_effects.py).
"""

import re
from pathlib import Path

from lib.dsl.loot import (
    LOOT_MODE_HARD_MODE_1,
    boss_loot,
    copy_normal_loot,
    loot_chance,
    remove_loot_group,
)

LIST_GROUP = 1  # the boss's list: one equal-chance entry per item
HARD_MODE_GROUP = 2  # the heroic lootid's hard mode list at LootMode 2
TOKEN_GROUP = 3  # a Zealot's token: one entry, always drops, apart from the list (group 1)
STOCK_KEEP_GROUP = 4  # a stock row kept at its stock chance beside the list (Herod's Scarlet Leggings), normal only


def _boss_lists(normal_lootid, heroic_lootid, items, token=None, replaced_items=()):
    """One boss: the list at the Normal tier on the stock lootid (naming the stock rows it replaces) and at the Heroic
    tier on the heroic body's own lootid, plus the family token on the heroic lootid only (the Heroic tier of the
    heroic-only set ladder)."""
    boss_loot(normal_lootid, items, tier="normal", group=LIST_GROUP, replaces_items=replaced_items)
    boss_loot(heroic_lootid, items, tier="heroic", group=LIST_GROUP)
    if token is not None:
        boss_loot(heroic_lootid, (token,), tier="heroic", group=TOKEN_GROUP)


# WARNING: the heroic lootids below are the PREDICTED heroic entries of the first write run's mint (310419 on,
# normal-entry order, source/world/heroic_ids.lock), copied by hand from source/world/dungeons/scarlet_monastery.py's
# `_boss(...)` overrides and from lib/test_scarlet_monastery_loot.py's BOSSES. If another branch appends lock lines
# first, every number shifts: `test_the_predicted_heroic_lootids_still_hold` (lib/test_scarlet_monastery_loot.py) fails
# with the exact fix, and so does lib/test_scarlet_monastery_heroic.py.

THALNOS_HEROIC = 310448
DOAN_HEROIC = 310451

DESECRATION_HARD_MODE = ("sm_purebloods_rallying_standard", "sm_fairbells_censer", "sm_voss_blessed_signet")
HERESY_HARD_MODE = ("sm_shard_of_the_phylactery", "sm_heretics_wand", "sm_fissure_touched_grips")

# Normal lootid, heroic lootid (the heroic body's own entry), the list (item() keys), the family token key (None: no
# token), the stock group 1 rows the list replaces (item_template entries).
BOSS_LISTS = (
    # --- Section 1: the Graveyard ---
    (3983, 310424, (  # Interrogator Vishas (Branded Leather Bracers moved from Fairbanks)
        "sm_bloody_brass_knuckles", "sm_torturing_poker", "sm_branded_leather_bracers", "sm_confessors_gloves",
        "sm_interrogators_thumbscrews",
    ), None, ()),
    (6489, 310453, (  # Ironspine
        "sm_ironspines_eye", "sm_ironspines_fist", "sm_bonecrawler_boots", "sm_bone_link_legguards",
        "sm_cloak_of_knitted_bone",
    ), None, (
        7688,  # Ironspine's Ribcage (Leather Tank chest of the Zealot's set: the family vendor's now)
    )),
    (6488, 310452, (  # the Fallen Champion: the council's one pool (Azshir's group 1 is emptied, below)
        "sm_necrotic_wand", "sm_blighted_leggings", "sm_ghostshard_talisman", "sm_morbid_dawn", "sm_ebon_vise",
        "sm_vigil_keepers_gauntlets",
    ), None, (
        7691,  # Embalmed Shroud (a token slot with no set to fit: cut)
    )),
    (4543, THALNOS_HEROIC, (  # Bloodmage Thalnos (the Desecration's list is group 2, below)
        "sm_orb_of_the_forgotten_seer", "sm_bloodmages_handwraps", "sm_bloodstained_cloak", "sm_bloodletting_kris",
        "sm_sanguine_signet",
    ), None, (
        7684,  # Bloodmage Mantle (a token slot with no set to fit: cut)
    )),
    # --- Section 2: the Library ---
    (3974, 310420, (  # Houndmaster Loksey
        "sm_dog_training_gloves", "sm_loksey_training_stick", "sm_dog_whistle", "sm_kennelmasters_crossbow",
        "sm_leash_scarred_gauntlets",
    ), None, ()),
    (300910, 310467, (  # Ambrose Kell (new; Dusty Mail Boots moved from Fairbanks)
        "sm_dusty_mail_boots", "sm_antiquarians_signet", "sm_kirin_tor_spellblade", "sm_necromancers_skull",
    ), None, ()),
    (300913, 310469, (  # Lector Hollis Grey (new)
        "sm_index_keepers_bindings", "sm_lectors_sash", "sm_forbidden_tome", "sm_burning_page",
    ), None, ()),
    (6487, DOAN_HEROIC, (  # Arcanist Doan: the Zealot's Helm on heroic
        "sm_illusionary_rod", "sm_hypnotic_blade", "sm_deadmans_hand", "sm_arcanists_cord",
        "sm_totem_of_righteous_fire",
    ), "zealot_token_head", (
        7711,  # Robe of Doan (Cloth Intellect chest of the Zealot's set: the family vendor's now)
        7712,  # Mantle of Doan (Cloth Intellect shoulders of the set)
    )),
)
for _normal, _heroic, _items, _token, _replaced in BOSS_LISTS:
    _boss_lists(_normal, _heroic, _items, _token, _replaced)

# Azshir the Sleepless (6490 / 310454): his stock group 1 (the Wand, the Leggings, the Talisman) is the council's pool
# on the Fallen Champion now. His silk and the world-drop references stay on the normal lootid and on a heroic copy.
AZSHIR_NORMAL, AZSHIR_HEROIC = 6490, 310454
remove_loot_group(AZSHIR_NORMAL, group=LIST_GROUP, replaces_items=(7708, 7709, 7731),
                  why="the council drops one pool, on the Fallen Champion's lootid (ruling 56, handoff 7 #35): the "
                      "Necrotic Wand, Blighted Leggings and Ghostshard Talisman are on it")
copy_normal_loot(AZSHIR_HEROIC, why="Azshir drops no list: the council's pool is the Fallen Champion's (310452); his "
                                    "silk and the world-drop references copy")

# --- hard mode lists (heroic only) ------------------------------------------------------------------------------------

# Thalnos, the Desecration: group 2 of his heroic lootid (the four risen heroes have lootid 0; Thalnos is the last of
# the pack that dies, D4H). Three items on a lit kill, on top of the heroic list.
boss_loot(THALNOS_HEROIC, DESECRATION_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP,
          loot_mode=LOOT_MODE_HARD_MODE_1)

# Doan, the Kel'Thuzad Heresy: group 2 of his heroic lootid (the anchors, shards and risen purged have lootid 0).
boss_loot(DOAN_HEROIC, HERESY_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP, loot_mode=LOOT_MODE_HARD_MODE_1)


# =====================================================================================================================
# Wave 2: the Armory and the Cathedral (WP L-2)
# =====================================================================================================================
#
# Same shape as wave 1: group 1 the list (one equal-chance item per kill), group 2 the hard mode list at LootMode 2,
# group 3 the family token, on the normal lootid at the Normal tier and the heroic body's own lootid at the Heroic tier.
#
# - **Crell, Halden, Thorne** (new bosses, lootids 300940 / 300942 / 300946; their normal templates name them): no stock
#   rows, the list is all they drop (like Kell and Hollis Grey). Heroic: 310476 / 310477 / 310479.
# - **Herod** (3975 / 310421): the list is Ravager (the stock entry, the Normal tier) and three new items. Herod's
#   Shoulder (7718) and the Raging Berserker's Helm (7719) are Zealot's set pieces now (the family vendor's), and the
#   Scarlet Leggings (10330, a stock Scarlet set piece) leave his stock group 1 with it. The Leggings are not a
#   trash drop on this server (live: only Herod and Mograine drop them), so Herod stays their one source and the
#   Scarlet set (163) stays completable (handoff 10, STAGE-R-2-LOOT m-1): they come back as a row of their own, group 4
#   (`STOCK_KEEP_GROUP`, a `loot_chance()` row at the stock 25%, beside the list item), on the NORMAL lootid only: the
#   heroic body (level 60 loot) gets no copy of a stock level 30s mail piece. Mograine's copy stays cut. The
#   Zealot's Mantle (`zealot_token_shoulders`) is group 3 of the heroic lootid only; the Call to Arms list (group 2,
#   LootMode 2, three items at 71) is on the same heroic lootid: Herod is the unit that dies last in that hard mode (the
#   trainees carry lootid 0), and the instance sets the loot bit at the trigger and at every pull while the flag is lit
#   (D11H). His heroic lootid is a prediction of the mint exactly like wave 1's, and the dungeon file's override
#   (`_wave("2", ...)`) only carries it once BIND_WAVE_2 is on; see `_WAVE_2_BOUND` below.
# - **The Last Stand** (Mograine, 3976): no list on his lootid and no heroic lootid of his own (the heroic override is
#   `_boss(250_000)`: his heroic body shares 3976). The approved list is the chest's, gameobject loot of 301330 (Normal
#   tier) and 301331 (Heroic tier): pending_db_world/rev_loot_wave_2_scarlet_monastery.sql (handoff 7 #20 A). His stock
#   group 1 (Aegis, Might, Gauntlets, the Scarlet Leggings, which stay Herod's) is emptied here; the Silk Cloth and
#   Heart of Zeal rows stay and drop at his real death in Whitemane's fight (D14).
# - **Whitemane** (3977 / 310423): the list is Triune Amulet and Hand of Righteousness (stock entries) and two new
#   items; Whitemane's Chapeau (7720, the Cloth Spirit set's head) leaves her stock group 1. The Zealot's Chestguard
#   (`zealot_token_chest`) is group 3 of the heroic lootid only, the Truth (three items at 71) group 2 at LootMode 2.
#   She dies last on every path (D14), so her lootid carries the finale.
# - **Fairbanks** (4542, stock, and his heroic copy: the heroic row keeps lootid 4542): group 1 is emptied. The
#   Inquisitor's Shawl (19507) is the Cloth Spirit set's shoulders, and Branded Leather Bracers (19508) / Dusty Mail
#   Boots (19509) are Vishas's and Kell's list items, so a Fairbanks kill must not drop them too (STAGE-R-1-LOOT M-2).
#   His Silk Cloth stays (4542 has no Heart of Zeal row: live SELECT 2026-11-20; the handoff's "keeps ... Heart of Zeal"
#   is wrong for him). The vigil Fairbanks (300956) has lootid 0.
#
# The heroic lootids of Herod and Whitemane are only creature rows once BIND_WAVE_2 is on (until then they are stock
# heroic copies on their normal lootids): declaring them before that is an ERROR ("heroic creature ...'s lootid is
# 3975, not its own entry"), so they follow the same switch the dungeon file reads (`_WAVE_2_BOUND`). The Crell,
# Halden and Thorne rows are always declared (their templates and heroic overrides are not behind the switch).

_COMMON = Path(__file__).resolve().parents[1] / "npcs" / "scarlet_monastery" / "_common.py"
_WAVE_SWITCH = re.compile(r"^BIND_WAVE_2\s*=\s*(True|False)\s*$", re.MULTILINE)
_wave_value = _WAVE_SWITCH.search(_COMMON.read_text(encoding="utf-8")) if _COMMON.is_file() else None
_WAVE_2_BOUND = _wave_value is not None and _wave_value.group(1) == "True"

CRELL_NORMAL, CRELL_HEROIC = 300940, 310476
HALDEN_NORMAL, HALDEN_HEROIC = 300942, 310477
HEROD_NORMAL, HEROD_HEROIC = 3975, 310421
THORNE_NORMAL, THORNE_HEROIC = 300946, 310479
MOGRAINE_NORMAL = 3976
WHITEMANE_NORMAL, WHITEMANE_HEROIC = 3977, 310423
FAIRBANKS_NORMAL = 4542
SCARLET_LEGGINGS = 10330

CALL_TO_ARMS_HARD_MODE = ("sm_scarlet_garrison_rifle", "sm_garrison_bulwark", "sm_staff_of_the_consecrated_hall")
TRUTH_HARD_MODE = ("sm_fathers_verdict", "sm_treads_of_denial", "sm_inquisitors_rosary")

# The Last Stand chest's list (gameobject loot; see rev_loot_wave_2_scarlet_monastery.sql and its test): the doc's five
# items in the doc's order. Kept here so the test and the SQL share one source of truth for the keys.
LAST_STAND_LIST = (
    "sm_aegis_of_the_scarlet_commander", "sm_mograines_might", "sm_gauntlets_of_divinity", "sm_captains_legguards",
    "sm_libram_of_the_last_stand",
)

# Normal lootid, heroic lootid (the heroic body's own entry), the list (item() keys), the family token key (None: no
# token), the stock group 1 rows the list replaces (item_template entries), whether the heroic lootid is behind the
# BIND_WAVE_2 switch.
WAVE_2_BOSS_LISTS = (
    # --- Section 3: the Armory ---
    (CRELL_NORMAL, CRELL_HEROIC, (  # Forgemaster Gideon Crell
        "sm_proving_blade", "sm_red_hot_gauntlets", "sm_tempered_girdle", "sm_forge_tempered_buckler",
    ), None, (), False),
    (HALDEN_NORMAL, HALDEN_HEROIC, (  # Drillmaster Corin Halden
        "sm_drillmasters_girdle", "sm_drillmasters_longbow", "sm_drillfield_cape", "sm_medal_of_the_proving_ground",
    ), None, (), False),
    (HEROD_NORMAL, HEROD_HEROIC, (  # Herod: the Zealot's Mantle on heroic
        "sm_ravager", "sm_whirlwind_legplates", "sm_blade_dancers_treads", "sm_pendant_of_the_scarlet_champion",
    ), "zealot_token_shoulders", (
        7718,  # Herod's Shoulder (Plate Strength shoulders of the Zealot's set: the family vendor's now)
        7719,  # Raging Berserker's Helm (Plate Strength head of the set)
        10330,  # Scarlet Leggings (stock group 1 row: re-added below as Herod's group 4 chance row)
    ), True),
    # --- Section 4: the Cathedral ---
    (THORNE_NORMAL, THORNE_HEROIC, (  # Brother Aldous Thorne
        "sm_furrowed_boots", "sm_waterbearers_girdle", "sm_idol_of_the_harvest", "sm_pruning_scythe",
    ), None, (), False),
    (WHITEMANE_NORMAL, WHITEMANE_HEROIC, (  # Whitemane (with Mograine risen): the Zealot's Chestguard on heroic
        "sm_triune_amulet", "sm_hand_of_righteousness", "sm_cinch_of_the_faithful", "sm_whitemanes_vigil_candle",
    ), "zealot_token_chest", (
        7720,  # Whitemane's Chapeau (Cloth Spirit head of the Zealot's set: the family vendor's now)
    ), True),
)
for _normal, _heroic, _items, _token, _replaced, _switched in WAVE_2_BOSS_LISTS:
    boss_loot(_normal, _items, tier="normal", group=LIST_GROUP, replaces_items=_replaced)
    if _switched and not _WAVE_2_BOUND:
        continue  # the heroic body is still the stock heroic copy on the normal lootid; the switch brings these in
    boss_loot(_heroic, _items, tier="heroic", group=LIST_GROUP)
    if _token is not None:
        boss_loot(_heroic, (_token,), tier="heroic", group=TOKEN_GROUP)

# Herod's Scarlet Leggings (10330) keep their stock chance (group 1 held four equal rows: 25%) as a row of group 4, on
# his normal lootid only (a loot_chance() group is never copied onto the heroic lootid). It is the only source of the
# stock Scarlet set's legs (STAGE-R-2-LOOT m-1, handoff 10).
loot_chance(HEROD_NORMAL, SCARLET_LEGGINGS, 25, STOCK_KEEP_GROUP, name="Scarlet Leggings")

# The Call to Arms and the Truth (heroic only): group 2 of Herod's and Whitemane's heroic lootids at LootMode 2.
if _WAVE_2_BOUND:
    boss_loot(HEROD_HEROIC, CALL_TO_ARMS_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP,
              loot_mode=LOOT_MODE_HARD_MODE_1)
    boss_loot(WHITEMANE_HEROIC, TRUTH_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP,
              loot_mode=LOOT_MODE_HARD_MODE_1)

# Mograine (3976): the Last Stand has no corpse, so the list is the chest's (the SQL rev); his stock group 1 (Aegis of
# the Scarlet Commander 7726, Mograine's Might 7723, Gauntlets of Divinity 7724: the chest's Normal tier entries now,
# and the Scarlet Leggings 10330, which stay Herod's only) is emptied. His silk and Heart of Zeal rows stay for his
# real death in Whitemane's fight.
remove_loot_group(MOGRAINE_NORMAL, group=LIST_GROUP, replaces_items=(10330,),
                  why="the Last Stand's list is the chest's (gameobject loot 301330 / 301331, handoff 7 #20 A): the "
                      "Aegis, Mograine's Might and the Gauntlets of Divinity are on it, the Scarlet Leggings stay "
                      "Herod's alone (his group 4); his silk and Heart of Zeal stay for his real death in "
                      "Whitemane's fight")

# Fairbanks (4542), stock and his heroic copy (the heroic row keeps the lootid): the Inquisitor's Shawl is a set piece,
# the bracers are Vishas's and the boots Kell's (STAGE-R-1-LOOT M-2). His silk stays.
remove_loot_group(FAIRBANKS_NORMAL, group=LIST_GROUP, replaces_items=(19507,),
                  why="his stock items moved: the Inquisitor's Shawl is the Cloth Spirit set's shoulders, the Branded "
                      "Leather Bracers (19508) are Vishas's and the Dusty Mail Boots (19509) Kell's (ruling 44, "
                      "handoff 7 #21); his silk stays")
