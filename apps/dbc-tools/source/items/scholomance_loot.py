"""
The Scholomance boss loot (item variants plan v2 section 7.3, WP-L of the Scholomance build): each boss's approved list
(docs/dungeons/scholomance-rework.md ## Loot, copied in docs/dungeons/dungeon-loot-vanilla.md) as one loot group of
equal-chance entries, on the stock lootid at the Normal tier and on the heroic body's own lootid at the Heroic tier
(lib/dsl/loot.py, lib/loot_tables.py). The items are declared in scholomance.py, the Haunted tokens in
haunted_set.py. The shape is the Deadmines and Shadowfang Keep one (deadmines_loot.py, shadowfang_keep_loot.py).

- **Group 1** of each boss is the list. The stock group 1 held the instructors' 30% roll on the shared pool (reference
  35031; Alexei's own copy 35095, Ras's 35030 with two rolls), each boss's Tier 0 piece and the boss's own stock items.
  The per-boss lists replace all of it (build spec, Structure 1: "Per-boss lists replace the shared pool"), so the
  declarations name the stock rows they drop (`replaces_items`, `replaces_references`). The references stay in
  `reference_loot_template`: Kirtonos (10506, stock, out of scope) and other creatures still use them.
- **Two drops** (Ras, Gandling): a reference row (`MaxCount` 2) into a pool of the boss's list, ids 1700002-1700005 of
  source/ids.yaml's `loot_reference` block (Deadmines took 1700000-1700001). The two items are distinct.
- **Haunted tokens** (build spec, Scholomance's Haunted tokens): Jandice the belt, Vectus the gloves (the Marduk and
  Vectus encounter drops once, from Vectus), Ras the shoulders, Gandling the helmet. Each is a group of its own (group
  3, one entry, so it always drops) on top of the list item: the token of the kill's tier (Normal on a normal lootid,
  Heroic on a heroic one; the empowered tiers belong to the empowered stage).
- **Marduk and Vectus** are one encounter with one shared pool (Vectus owns it): the merged list of four, one item per
  kill, is on Vectus (10432, heroic 310069). Marduk (10433, heroic 310070) has no loot table (`lootid` 0, set with his
  gold in marduk_and_vectus.py and the heroic overrides of source/world/dungeons/scholomance.py): his stock rows go,
  and Vectus carries the encounter's one purse (the sum of the two stock purses).
- **Group 0** (cloth, the quest items, Scourgestones, recipes, the Viewing Room Key, Blood of Innocents, Ras's head)
  and the green pools (Jandice's reference 24016 in group 0, Alexei's world loot reference 1000360 in group 5) stay on
  the normal lootids untouched: a generic pool rolls on top, never instead (docs/dungeons/boss-rework-systems.md
  section 2). Heroic bodies keep them as copies (lib/loot_tables.py derive_heroic_copies). The two Remove-listed
  ungrouped rows (Jandice's Darkshade Gloves, Gandling's Detention Strap, now in his list) are deleted.
- **Tier 0 trash drops** (build spec: "Stock trash rows for Tier 0 pieces are removed, since the entries now come from
  the vendor"): the 12 trash lootids below lose their Tier 0 rows. Heroic trash shares the normal lootid.
- **Hard mode** (heroic only): group 2 of Ras's heroic lootid 310098 (the Torn Keepsake) and Gandling's 310068 (the
  honors program) hold three hard mode items at Heroic Hard Mode (71) with `LootMode` 2 (`LOOT_MODE_HARD_MODE_1`).
  The instance script adds the bit while the boss's hard mode is lit (WP-S12, S13), so a lit kill drops one of the
  three on top of the heroic items. Gandling's stock group 2 (his list, on the normal lootid) is removed, so the
  heroic lootid's group 2 is free for the hard mode group.
- **Examiners** (300548-300554), the Graduate and the other adds drop nothing (lootid 0), and Kirtonos (10506) keeps his
  stock loot.
"""

from lib.dsl.loot import LOOT_MODE_HARD_MODE_1, boss_loot, remove_loot_group, remove_loot_rows

TOKEN_GROUP = 3  # a Haunted token: one entry, always drops, apart from the list (group 1) and the hard mode (group 2)

# Normal lootid, heroic lootid (the heroic body's own entry), list, Haunted token (None: no token), the stock rows
# (items, references) of group 1 the list replaces.
BOSS_LISTS = (
    (10503, 310093, (  # Jandice Barov
        "scholo_barovian_family_sword", "scholo_phantasmal_cloak", "scholo_wraithplate_leggings",
        "scholo_staff_of_metanoia", "scholo_ghostloom_leggings",
    ), "haunted_token_waist", ((14548, 16701), ())),  # Royal Cap Spaulders, Dreadmist Mantle
    (11622, 310110, (  # Rattlegore
        "scholo_rattlecage_buckler", "scholo_frightskull_shaft", "scholo_corpselight_greaves", "scholo_spare_rib",
    ), None, ((14538, 14539, 16711, 18686), ())),  # Deadwalker Mantle, Bone Ring Helm, Shadowcraft Boots, Bone Golem
    (10432, 310069, (  # Vectus (the Marduk and Vectus encounter: one merged list)
        "scholo_ebon_hilt_of_marduk", "scholo_death_knight_sabatons", "scholo_skullsmoke_pants",
        "scholo_dark_advisors_pendant",
    ), "haunted_token_hands", ((), ())),
    (10505, 310095, (  # Instructor Malicia
        "scholo_necropile_robe", "scholo_cadaverous_leggings", "scholo_dimly_opalescent_ring",
        "scholo_jar_of_torn_souls",
    ), None, ((16710,), (35031,))),  # Shadowcraft Bracers, the shared pool
    (11261, 310103, (  # Doctor Theolen Krastinov
        "scholo_cadaverous_armor", "scholo_deathbone_sabatons", "scholo_hammer_of_the_vesper",
        "scholo_krastinovs_suture_kit", "scholo_rib_spreader",
    ), None, ((16684,), (35031,))),  # Magister's Gloves, the shared pool
    (10901, 310100, (  # Lorekeeper Polkelt
        "scholo_cadaverous_walkers", "scholo_bloodmail_bracers", "scholo_ghoul_skin_leggings",
        "scholo_polkelts_specimen_launcher",
    ), None, ((16705,), (35031,))),  # Dreadmist Wraps, the shared pool
    (10507, 310097, (  # The Ravenian
        "scholo_deathbone_chestplate", "scholo_necropile_boots", "scholo_ancient_bone_bow", "scholo_corvanes_goad",
    ), None, ((16716,), (35031,))),  # Wildheart Belt, the shared pool
    (10504, 310094, (  # Lord Alexei Barov
        "scholo_bloodmail_hauberk", "scholo_libram_of_divinity", "scholo_barov_heirs_breastplate",
        "scholo_the_deans_rod",
    ), None, ((), (35095,))),  # his own copy of the shared pool
    (10502, 310092, (  # Lady Illucia Barov
        "scholo_necropile_cuffs", "scholo_bloodmail_legguards", "scholo_totem_of_sustaining",
        "scholo_shroud_of_foresight",
    ), None, ((), (35031,))),  # the shared pool
)
for normal_lootid, heroic_lootid, items, token, (replaced_items, replaced_references) in BOSS_LISTS:
    boss_loot(normal_lootid, items, tier="normal", replaces_items=replaced_items,
              replaces_references=replaced_references)
    boss_loot(heroic_lootid, items, tier="heroic")
    if token is not None:
        boss_loot(normal_lootid, (token,), tier="normal", group=TOKEN_GROUP)
        boss_loot(heroic_lootid, (token,), tier="heroic", group=TOKEN_GROUP)

# Marduk: one encounter, one list (Vectus's). His corpse drops nothing (lootid 0): the stock rows go. Both bosses
# dropped a Scourgestone and Runecloth at 100% / 20%; the encounter now drops Vectus's.
remove_loot_group(10433, group=1, why="Ebon Hilt of Marduk and Death Knight Sabatons moved into Vectus's list (one "
                                      "item per encounter)")
remove_loot_rows(10433, (12843, 14047), group=0, why="Marduk has no loot table (lootid 0); Vectus drops the "
                                                      "encounter's Scourgestone and Runecloth")

# Ras (10508, heroic 310098) and Gandling (1853, heroic 310068): two distinct items of the list.
RAS_POOL = (
    "scholo_alannas_embrace", "scholo_iceblade_hacker", "scholo_maelstrom_leggings", "scholo_shadowy_mail_greaves",
    "scholo_spellbound_tome", "scholo_intricately_runed_shield",
)
GANDLING_POOL = (
    "scholo_headmasters_charge", "scholo_don_mauricios_band", "scholo_witchblade", "scholo_silent_fang",
    "scholo_vigorsteel_vambraces", "scholo_bonecreeper_stylus", "scholo_boots_of_the_shrieker",
    "scholo_detention_strap",
)
PICKS = 2
# Gandling's stock group 1: the nine Tier 0 helms at 100% (Coif of Elements, Beaststalker's Cap, Magister's Crown,
# Devout Crown, Dreadmist Mask, Shadowcraft Cap, Wildheart Cowl, Lightforge Helm, Helm of Valor); the Haunted Helmet
# replaces them.
STOCK_HELMS = (16667, 16677, 16686, 16693, 16698, 16707, 16720, 16727, 16731)

boss_loot(10508, RAS_POOL, tier="normal", picks=PICKS, reference=1700002, replaces_references=(35030,))
boss_loot(310098, RAS_POOL, tier="heroic", picks=PICKS, reference=1700003)
boss_loot(10508, ("haunted_token_shoulders",), tier="normal", group=TOKEN_GROUP)
boss_loot(310098, ("haunted_token_shoulders",), tier="heroic", group=TOKEN_GROUP)

boss_loot(1853, GANDLING_POOL, tier="normal", picks=PICKS, reference=1700004, replaces_items=STOCK_HELMS)
boss_loot(310068, GANDLING_POOL, tier="heroic", picks=PICKS, reference=1700005)
boss_loot(1853, ("haunted_token_head",), tier="normal", group=TOKEN_GROUP)
boss_loot(310068, ("haunted_token_head",), tier="heroic", group=TOKEN_GROUP)
remove_loot_group(1853, group=2, why="Gandling's stock list moved into his two-drop pool (group 1); the group id "
                                     "belongs to the heroic hard mode list", replaces_items=(13944,))  # Tombstone Br.
remove_loot_rows(1853, (13950,), group=0, why="Detention Strap is in Gandling's list now (no longer a 1% roll)")
remove_loot_rows(10503, (14543,), group=0, why="Darkshade Gloves are cut (a Haunted token slot)")

# The hard mode lists (heroic only): one item on a lit kill, on top of the heroic items.
RAS_HARD_MODE = ("scholo_phylactery_shard", "scholo_frostwhispers_chillband", "scholo_bonechill_blade")
GANDLING_HARD_MODE = ("scholo_transfer_papers", "scholo_honor_roll_ribbon", "scholo_darkmasters_portal_rod")
boss_loot(310098, RAS_HARD_MODE, tier="heroic_hm", group=2, loot_mode=LOOT_MODE_HARD_MODE_1)
boss_loot(310068, GANDLING_HARD_MODE, tier="heroic_hm", group=2, loot_mode=LOOT_MODE_HARD_MODE_1)

# The stock Tier 0 trash drops (sets 181-189), group 0 rows: lootid -> (Tier 0 items, names). Heroic trash shares the
# normal lootid, so one DELETE serves both difficulties.
TIER_0_TRASH = (
    (10469, (16684, 16685), "Scholomance Adept: Magister's Gloves and Belt"),
    (10472, (16710,), "Scholomance Occultist: Shadowcraft Bracers"),
    (10477, (16702, 16705), "Scholomance Necromancer: Dreadmist Belt and Wraps"),
    (10478, (16671,), "Splintered Skeleton: Bindings of Elements"),
    (10486, (16722,), "Risen Warrior: Lightforge Bracers"),
    (10487, (16722,), "Risen Protector: Lightforge Bracers"),
    (10488, (16710,), "Risen Construct: Shadowcraft Bracers"),
    (10495, (16714,), "Diseased Ghoul: Wildheart Bracers"),
    (10499, (16716,), "Spectral Researcher: Wildheart Belt"),
    (10500, (16716,), "Spectral Teacher: Wildheart Belt"),
    (11257, (16716,), "Scholomance Handler: Wildheart Belt"),
    (11284, (16710,), "Dark Shade: Shadowcraft Bracers"),
)
for _lootid, _items, _what in TIER_0_TRASH:
    remove_loot_rows(_lootid, _items, group=0, why=f"{_what} (Tier 0 pieces come from the Haunted vendors)")
