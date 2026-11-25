"""
The Ragefire Chasm boss loot (item variants plan v2 section 7.3, WP L-1 of the Ragefire Chasm build): each boss's
approved list (docs/dungeons/ragefire-chasm-rework.md ## Loot "Final list", ruling 13, copied in
docs/dungeons/dungeon-loot-vanilla.md "### Ragefire Chasm") as one loot group of equal-chance entries, on the stock
lootid at the Normal tier and on the heroic body's own lootid at the Heroic tier (lib/dsl/loot.py,
lib/loot_tables.py). The items are declared in ragefire_chasm.py, the three hard mode items in
ragefire_chasm_hard_mode.py. The shape is the Deadmines / Shadowfang Keep one (deadmines_loot.py); the gear stage is
folded into this build, so the items and the loot are one core PR.

- **Lists** (one item per kill, as every list): Oggleflint 6, Jergosh the Invoker 6, Bazzalan 6, Taragaman the
  Hungerer 7 (25 in all). The stock group 1 of Jergosh (Robe of Evocation, Cavedweller Bracers, Chanting Blade at 40,
  40 and 20%) and of Taragaman (Crystalline Cuffs, Subterranean Cape at 40%, Cursed Felblade at 20%) held the same
  boss's stock items; all six are `item(base=)` declarations, so their stock entry is the Normal tier and the rows are
  replaced in place (the declared group owns nothing foreign, no `replaces_items` is needed: the loot check counts a
  declared item's entry as owned). Group 1 of those two bosses is the list.
- **Oggleflint and Bazzalan** have no rare of their own: their stock group 1 holds six generic world drop references
  (24060, 24070, 24075-24078: the level 7 to 21 greens, gems and patterns, chances 1, 5, 1, 1, 1, 1). They stay
  exactly where they are, in group 1, and the list is **group 2** (the Stratholme Malor shape): a generic pool rolls
  on top of the list, never instead (docs/dungeons/boss-rework-systems.md section 2). Their group 0 (cloth, food,
  potions, scrolls, patterns) stays untouched too. A reference row is not an item the list could duplicate.
- **Heroic bodies** (source/world/heroic_ids.lock; 310496-310499) drop from their own lootid, set in
  source/world/dungeons/ragefire_chasm.py (`_HEROIC_BOSS_OWN_LOOT = True`, flipped by this WP). Besides the list (and
  the hard mode group) they keep everything the normal boss drops, copied unchanged in the same groups
  (lib/loot_tables.py derive_heroic_copies): group 0's cloth, food, consumables and the quest item, and the two
  bosses' world drop references in group 1.
- **Taragaman's Heart** (14540, "Slaying the Beast", `QuestRequired`, 100%) is a stock group 0 row of 11520. It is
  kept as it is and copied to the heroic body (handoff section 7 #38 A: an objective done on heroic is turned in on
  normal; the entrance orc is normal only). Nothing in this file names it. Maur's satchel is not boss loot.
- **Hard mode** (Taragaman the Hungerer, Starving, heroic only): group 2 of 310499 holds the three hard mode items
  (Taragaman's Fang, Heart of the Starving, Felstorm Greatblade) at Heroic Hard Mode (71) with `LootMode` 2
  (`LOOT_MODE_HARD_MODE_1`). The instance script adds the bit to his loot mode at the pour (STAGE-S0 / STAGE-D4H), so a
  lit kill drops one of them on top of his heroic item. The normal lootid gets no hard mode group.
- **No tokens**: Ragefire Chasm has no Haunted or Zealot set. No flex copies (a 5 player dungeon).
"""

from lib.dsl.loot import LOOT_MODE_HARD_MODE_1, boss_loot

# Oggleflint's and Bazzalan's group 1 is the world drop references (stay); Jergosh's and Taragaman's group 1 is their
# stock list (replaced in place).
LIST_GROUP = 1
REFERENCE_KEEPER_LIST_GROUP = 2
HARD_MODE_GROUP = 2

# Normal lootid, heroic lootid (the heroic body's own entry: the mint order of heroic_ids.lock, ragefire_chasm.py's
# `_HEROIC_LOOTID`), the list's group, the list (item() keys).
BOSS_LISTS = (
    (11517, 310496, REFERENCE_KEEPER_LIST_GROUP, (  # Oggleflint
        "rfc_tunnelers_hide_cap", "rfc_chieftains_rockplate_pauldrons", "rfc_borer_chased_treads",
        "rfc_ring_of_the_cleft", "rfc_eye_of_the_earthborer", "rfc_oggleflints_skullthumper",
    )),
    (11518, 310497, LIST_GROUP, (  # Jergosh the Invoker
        "rfc_robe_of_evocation", "rfc_cavedweller_bracers", "rfc_searing_blade_ritual_leggings",
        "rfc_shard_of_the_blood_filled_orb", "rfc_chanting_blade", "rfc_invokers_staff_of_embers",
    )),
    (11519, 310498, REFERENCE_KEEPER_LIST_GROUP, (  # Bazzalan
        "rfc_satyrhide_mantle", "rfc_cleft_of_shadow_grips", "rfc_felhoof_kilt", "rfc_shadowstep_slippers",
        "rfc_satyrs_kris", "rfc_idol_of_the_corrupted_grove",
    )),
    (11520, 310499, LIST_GROUP, (  # Taragaman the Hungerer
        "rfc_crested_helm_of_the_beast", "rfc_crystalline_cuffs", "rfc_hungerers_legplates",
        "rfc_subterranean_cape", "rfc_searing_blade_talisman", "rfc_cursed_felblade", "rfc_libram_of_the_hungerer",
    )),
)
for _normal, _heroic, _group, _items in BOSS_LISTS:
    boss_loot(_normal, _items, tier="normal", group=_group)
    boss_loot(_heroic, _items, tier="heroic", group=_group)

# Taragaman's hard mode list (heroic only): one item on a lit kill, on top of his heroic item.
TARAGAMAN_HEROIC = 310499
TARAGAMAN_HARD_MODE = ("rfc_taragamans_fang", "rfc_heart_of_the_starving", "rfc_felstorm_greatblade")
boss_loot(TARAGAMAN_HEROIC, TARAGAMAN_HARD_MODE, tier="heroic_hm", group=HARD_MODE_GROUP,
          loot_mode=LOOT_MODE_HARD_MODE_1)
