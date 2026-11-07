"""
The Deadmines boss loot (item variants plan v2 section 7.3, stage IV7): each boss's approved list
(docs/dungeons/deadmines-rework.md ## Loot, copied in docs/dungeons/dungeon-loot-vanilla.md) as one loot group of
equal-chance entries, on the normal lootid at the Normal tier and on the heroic body's own lootid at the Heroic tier
(lib/dsl/loot.py, lib/loot_tables.py). The items themselves are declared in deadmines.py.

- **Group 1** of each boss is the list (stock group 1 held the same boss's stock items at explicit chances). Group 0
  (cloth, food, the quest items) and Miner Johnson's generic world loot reference (group 5) stay on the normal
  lootids untouched: a generic pool rolls on top, never instead (docs/dungeons/boss-rework-systems.md section 2).
- **Sneed's pool** (designer 2026-10-29): the Shredder's and Sneed's items are one pool, two distinct items dropped
  when Sneed dies; the Shredder keeps only its quest item (its group 0). The pool is a reference row in Sneed's group
  1 (`MaxCount` 2) into `reference_loot_template` 1700000 (normal) / 1700001 (heroic).
- **Heroic bodies** (source/world/heroic_ids.lock) drop from their own lootid, set in
  source/world/dungeons/deadmines.py's heroic overrides. Besides the list (and the hard mode group) they keep everything
  the normal boss drops, copied unchanged in the same groups (lib/loot_tables.py derive_heroic_copies): group 0's
  cloth, food and quest items (An Unsent Letter, Head of VanCleef) and Miner Johnson's world loot reference in group
  5. The heroic Shredder (310006) keeps the normal lootid 642 (group 0 only once group 1 is removed).
- **Hard mode** (Edwin VanCleef, heroic only: the powder keg spawns on heroic alone): group 2 of 310004 holds the 3
  hard mode items at Heroic Hard Mode (71) with `LootMode` 2 (`LOOT_MODE_HARD_MODE_1`). The Pilot's instance script
  adds the bit to VanCleef's loot mode while `DATA_HARD_MODE` is lit (and resets it when it clears), so a lit kill
  drops one of them on top of his heroic item.

Reference ids are the first of source/ids.yaml's `loot_reference` block; never move a shipped one.
"""

from lib.dsl.loot import LOOT_MODE_HARD_MODE_1, boss_loot, remove_loot_group

# Normal lootid, heroic lootid (the heroic body's own entry), list.
BOSS_LISTS = (
    (644, 310008, ("dm_rhahkzors_hammer", "dm_rockslicer", "dm_doormans_girdle", "dm_evokers_boots")),  # Rhahk'Zor
    (3586, 310020, ("dm_miners_cape", "dm_gold_plated_buckler")),  # Miner Johnson
    (1763, 310017, ("dm_smelting_pants", "dm_lavishly_jeweled_ring", "dm_forge_scarred_sabatons")),  # Gilnid
    (646, 310010, (  # Mr. Smite
        "dm_smites_reaver", "dm_thiefs_blade", "dm_smites_mighty_hammer", "dm_first_mates_pauldrons",
    )),
    (645, 310009, ("dm_cookies_tenderizer", "dm_cookies_stirring_rod", "dm_rubbery_helmet")),  # Cookie
    (647, 310011, (  # Captain Greenskin
        "dm_emberstone_staff", "dm_blackened_defias_belt", "dm_impaling_harpoon", "dm_harpooneers_coif",
    )),
    (639, 310004, (  # Edwin VanCleef
        "dm_cape_of_the_brotherhood", "dm_corsairs_overshirt", "dm_cruel_barb", "dm_blackened_defias_armor",
    )),
)
for normal_lootid, heroic_lootid, items in BOSS_LISTS:
    boss_loot(normal_lootid, items, tier="normal")
    boss_loot(heroic_lootid, items, tier="heroic")

# Sneed (643, heroic 310007): two distinct items from the encounter's one pool.
SNEED_POOL = (
    "dm_buzzer_blade", "dm_buzz_saw", "dm_gold_flecked_gloves", "dm_taskmaster_axe", "dm_insulated_tazer_bracers",
)
SNEED_PICKS = 2
boss_loot(643, SNEED_POOL, tier="normal", picks=SNEED_PICKS, reference=1700000)
boss_loot(310007, SNEED_POOL, tier="heroic", picks=SNEED_PICKS, reference=1700001)
remove_loot_group(642, group=1, why="Sneed's Shredder: Buzzer Blade and Buzz Saw moved into Sneed's pool")

# Edwin VanCleef's hard mode list (heroic only): one item on a lit kill, on top of his heroic item.
VANCLEEF_HARD_MODE = ("dm_powder_keg_fuse", "dm_blackguards_signet", "dm_lantern_of_the_roaring_flame")
boss_loot(310004, VANCLEEF_HARD_MODE, tier="heroic_hm", group=2, loot_mode=LOOT_MODE_HARD_MODE_1)
