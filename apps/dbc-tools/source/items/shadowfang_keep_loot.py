"""
The Shadowfang Keep boss loot (item variants plan v2 section 7.3, WP-L of the SFK build): each boss's approved list
(docs/dungeons/shadowfang-keep-rework.md ## Loot, copied in docs/dungeons/dungeon-loot-vanilla.md) as one loot group of
equal-chance entries, on the stock lootid at the Normal tier and on the heroic body's own lootid at the Heroic tier
(lib/dsl/loot.py, lib/loot_tables.py). The items themselves are declared in shadowfang_keep.py. The shape is the
Deadmines one (deadmines_loot.py).

- **Group 1** of each boss is the list (the stock group 1 held the same boss's stock items at explicit chances; the
  stock items are all in the list, so the declared group owns nothing foreign). Group 0 (cloth, food, the quest items,
  Archmage Arugal's Head of Arugal) and the Deathsworn Captain's reference rows (the dungeon's rare pool 1033000 in
  group 0, the world drop reference 1000321 in group 5) stay on the normal lootids untouched: a generic pool rolls on
  top, never instead (docs/dungeons/boss-rework-systems.md section 2). The reference rows keep MinCount == MaxCount.
- **Heroic bodies** (source/world/heroic_ids.lock) drop from their own lootid, set in
  source/world/dungeons/shadowfang_keep.py's heroic overrides (`columns={"lootid": <heroic id>}`). Besides the list
  (and the hard mode group) they keep everything the normal boss drops, copied unchanged in the same groups
  (lib/loot_tables.py derive_heroic_copies): group 0, the Captain's references in groups 0 and 5, Arugal's Head.
  The heroic ids are the ones the WP-H report lists (first free id 310029, in normal-entry order).
- **Hard mode** (Archmage Arugal, Face Him Alone, heroic only): group 2 of 310051 holds the 3 hard mode items at Heroic
  Hard Mode (71) with `LootMode` 2 (`LOOT_MODE_HARD_MODE_1`). The instance script adds the bit to Arugal's loot mode
  while `DATA_HARD_MODE` is lit, so a lit kill drops one of them on top of his heroic item.
- **Haunted set tokens** are not part of Shadowfang Keep (the set drops in Scholomance and Stratholme).
"""

from lib.dsl.loot import LOOT_MODE_HARD_MODE_1, boss_loot

# Normal lootid, heroic lootid (the heroic body's own entry), list.
BOSS_LISTS = (
    (3914, 310048, ("sfk_rugged_spaulders", "sfk_cell_keepers_girdle")),  # Rethilgore
    (3886, 310046, ("sfk_butchers_slicer", "sfk_bloody_apron", "sfk_butchers_cleaver")),  # Razorclaw the Butcher
    (3887, 310047, (  # Baron Silverlaine
        "sfk_barons_scepter", "sfk_silverlaines_family_seal", "sfk_silverlaine_heirloom_legplates",
    )),
    (4278, 310052, (  # Commander Springvale
        "sfk_commanders_crest", "sfk_arced_war_axe", "sfk_vambraces_of_the_fallen_commander",
    )),
    (4279, 310053, ("sfk_girdle_of_the_blindwatcher", "sfk_odos_ley_staff", "sfk_watchtower_coif")),  # Odo
    (3872, 310042, ("sfk_haunting_blade", "sfk_phantom_armor")),  # Deathsworn Captain (rare spawn)
    (4274, 310050, (  # Fenrus the Devourer
        "sfk_fenrus_hide", "sfk_black_wolf_bracers", "sfk_wolfhide_lined_pauldrons",
    )),
    (3927, 310049, ("sfk_feline_mantle", "sfk_wolfmaster_cape")),  # Wolf Master Nandos
    (4275, 310051, ("sfk_robes_of_arugal", "sfk_belt_of_arugal", "sfk_meteor_shard")),  # Archmage Arugal
)
for normal_lootid, heroic_lootid, items in BOSS_LISTS:
    boss_loot(normal_lootid, items, tier="normal")
    boss_loot(heroic_lootid, items, tier="heroic")

# Archmage Arugal's hard mode list (heroic only): one item on a lit kill, on top of his heroic item.
ARUGAL_HARD_MODE = ("sfk_vial_of_the_worgens_curse", "sfk_arugals_shadow_tome", "sfk_ashcrombes_locket")
boss_loot(310051, ARUGAL_HARD_MODE, tier="heroic_hm", group=2, loot_mode=LOOT_MODE_HARD_MODE_1)
