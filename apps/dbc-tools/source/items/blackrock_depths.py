"""
The Blackrock Depths loot (wave 2 dungeon items, after the Stratholme precedent stratholme.py): the 75 approved list
items and the 12 hard mode items of the Ring of Law Encore, Lord Incendius, Golem Lord Argelmach and Emperor Dagran
Thaurissan (docs/dungeons/blackrock-depths-rework.md ## Loot, approved 2026-11-14, rulings 85-92; the Vault's four in
blackrock-depths-2-shadowforge-city.md "Loot", rulings 44 and 45; copied in docs/dungeons/dungeon-loot-vanilla.md).
Out of scope here: the Molten tokens and set pieces (molten_set.py), the Vault Treasure Bag, the Cinder of the
Firelord, quest items, keys and the kept pools; no loot tables yet (the dungeon build's blackrock_depths_loot.py).

Blackrock Depths is a level 60 dungeon, so Normal drops Rare at the item's stock level (52-60; the shared doc Loot
ladder: "Normal, level 60 dungeons: stock, about 60"), Heroic is 66 Epic with the Heroic flag, then the three
empowered steps (ladders.py). Stock items keep their id as the Normal tier (`base=`); the one stock epic on the list
(Savage Gladiator Chain) is lowered to Rare on Normal (normal drops rare, heroic drops epic). A new item takes the
lowest stock item level of its boss's list (Eviscerator 57, Bael'Gar 56, the Emperor 58) and Lord Incendius, whose
list has no stock item (his four Fire resistance bracers leave), takes 60 (the ladder's "about 60"); required level =
item level - 5, the stock pattern.

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and the
secondaries are listed. The list's two-secondary lines take the two-stat Even shapes (the order of the doc's two
secondaries does not matter to an Even shape); Savage Gladiator Chain's three take "Crit/Haste/Versatility". Rings,
necks and the primary-less trinkets carry secondaries only (`primary=None`, share 0). Coal Miner Boots, the
dungeon's Leather Tank piece, take a quarter more Stamina (`extra_stamina=0.25`, the Deadmines Smelting Pants pick).

**Shapes this file needs that do not exist yet** (STAGE-BRD report, "New shapes"; the integration adds them):
"Dodge/Versatility" (Blackveil Cape, Ebonsteel Spaulders), "Mastery/CDH" (Spell Eater's Choker, Magma Forged Band),
"Proc/CDH" (Cyclopean Band), "Versatility/Proc" (Graverot Cape), "Parry/Haste" (Libram of Truth), "Block/Mastery"
(Black Steel Bindings, Rock Golem Bulwark), "Block/Haste" (Black Anvil Bulwark) and "Dodge/Mastery (Any)" (Volcanic
Heartstone, the "Dodge (Solo, Any)" precedent: the stock Dodge shapes refuse a Null primary).

**Kept stock effects** (the list's "keeps ..."): Hookfang Shanker (Corrosive Poison 13526), Force of Magma (Firebolt
18086), Lord General's Sword (15602), Naglering (Thorns 15438), Bloodfist (Wound 16433), Flame Wrath (16559), Totem of
Rage (Increased Shock Damage 27859), Libram of Truth (Devotion Aura armor 27850), Wraith Scythe (Drain Life 16414) and
Barman Shanker (Rend 13318) keep every stock slot (`keep_spells=True`, their only slot is the effect). Second Wind,
Burst of Knowledge and Hand of Justice also carry a flat spell power or attack power Equip, which the list folds away
("Spell Power ... lost it"): they name the kept slot with `spells=` (its stock cooldown) and drop the stat Equip.
Ironfoe moves to the Emperor's hard mode list as a new item with the stock Fury of Forgewright (15494, 1.5 procs per
minute): the hard mode ladder has no stock-level first tier, so a `base=` cannot sit on it. Stock spells are the same
on every tier (they are not declared in source/items, so they cannot scale). Every effect item pays 0.7 of the budget
(itemization-changes.md section 3). Every other stock spell slot (+attack power, +spell power, Beast Slaying, the
relics' class equips) folds into the budget (`absorbed_spell_slots`), as the list's stats-only lines ask.

**Totem of Rage's "moved onto potency"**: its stock spell 27859 (the shock spell power Equip) is declared by
blackrock_depths_hard_mode_effects.py with a potency line (30 at level 60, the stock value, level-scaled below it); the
npc.csv row is gone (one owner per spell). The item keeps slot 27859 and is not `scale="budget"`.

**Unpriced stock extras are cleared on every tier** (the Scholomance precedent): the Nature and Arcane resistance of
Rock Golem Bulwark. **The Savage Gladiator set is dissolved** (ruling 85): the Chain and the Grips clear `itemset`
on every tier (the cut Helm, Leggings and Greaves stay stock).

**Type and slot changes**: Deathdealer Breastplate mail -> plate (`subclass=4`, `Material=6`, display unchanged; the
dungeon's Plate Intellect piece, as Darkspinner Claws in Stratholme). Black Steel Bindings plate wrist -> plate hands
(wrist is a Molten token slot here): `InventoryType=10` and the Dark Iron Gauntlets look (19164, display 31683).

**Sockets.** The Blackrock Depths doc names one pick (Mana Shaping Handwraps, 1 socket); every other pick here applies
the shared rule (boss-rework-systems section 2: about one standalone armor piece or weapon per boss carries 1 or 2;
hard mode items 1; trinkets never) and is a designer question (STAGE-BRD report). The first socket is red on damage and
healing gear and blue on tank gear; a second takes the color of the item's first secondary (docs/Systems.md "Sockets
and gems"). Socket bonuses are the stock +4 ratings (2874 Crit, 3267 Haste, 2871 Dodge, 2972 Block): Mastery and
Cooldown Haste items take Haste, Versatility and Proc Chance items take Crit (no enchant exists for the custom stats),
by the item's first secondary. Sockets start at Heroic (ladders.py).

**Hard mode items** (ladder `vanilla_hard_mode`, 71 / 81 / 91 / 101) carry the effects of
blackrock_depths_hard_mode_effects.py (the `blackrock_depths_items` reservation 206830-206899). Effects the designer
scales by item level are `scale="budget"`: every tier above 71 carries its own copies. Theldren's Executioner (a
percent) and Korv's Spirit Fetish (half the heal) have nothing to scale. All twelve are unique-equipped across their
tiers (automatic for an effect item).
"""

from lib.dsl.items import Quality, Socket, equip_spell, hit_spell, item, use_spell

from .blackrock_depths_hard_mode_effects import (
    black_anvil_bulwark_206835,
    electrons_lethal_coil_206847,
    fist_of_the_lake_lord_206837,
    golemwrights_mending_rod_206844,
    korvs_spirit_fetish_206833,
    leftys_shiv_206831,
    orb_of_the_sorcerer_thane_206852,
    prototype_power_core_206842,
    scepter_of_the_molten_lake_206839,
    theldrens_executioner_206830,
    volcanic_heartstone_206850,
)
from .ladders import VANILLA_DUNGEON, VANILLA_HARD_MODE

# Socket bonus enchants (stock SpellItemEnchantment ids, +4 each; see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_DODGE_4 = 2871
BONUS_BLOCK_4 = 2972

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does
RARE = Quality.RARE
EXTRA_STAMINA = 0.25  # "extra Stamina" on a tank piece: a quarter more than the tier's baseline
NO_SET = {"itemset": 0}  # the dissolved Savage Gladiator set (ruling 85): no set bonus on any tier

# Blackrock gear fix pass (REVIEW S1-S3), declared multipliers that replace a weapon-tier role cell:
# - a caster main-hand or bow whose stock level is below 60 takes the 60-100 cell (0.445, 0.405) on its Normal tier;
#   the 1-59 cell (0.8, five live items; bows 0.269) is a third (two thirds) of it (S2; the bucket step check);
# - a hard mode weapon whose 101 tier would fall in the 101-200 bucket keeps its 60-100 cell times the effect discount
#   on every tier: that bucket was fit on TBC items (caster two-hand 2.455, caster main-hand 3.429, shield 0.758), a
#   2x to 2.7x step from 91 to 101 instead of the budget curve's 1.13x (S1; the physical two-hand also keeps its
#   60-100 DPS fraction);
# - a socketed hard mode one-hander or shield pays the socket out of a thin cell budget (0.311 / 0.295 left 1 point of
#   the primary and 0 or 1 of each secondary): 0.6 gives every doc stat a few points (S3). The caster one-hander
#   (Golemwright's Mending Rod) too: its physical cell x 0.7 (0.3115, level60-stat-curve 1.8) is that thin budget.
# physical InventoryType 13 ilvl 60-100: caster weapons take the physical budget (level60-stat-curve 1.8)
CASTER_MAIN_HAND_MULT = 0.445
# physical InventoryType 17 ilvl 60-100 0.791 x the effect discount 0.7 (level60-stat-curve 1.8)
HM_CASTER_TWO_HAND_MULT = 0.5537
# physical InventoryType 17 Quality 4 ilvl 60-100: 0.791 x 0.7 and its DPS fraction. The 101-200 cell's multiplier is
# close (0.885) but its DPS fraction (0.0002) moves the DPS budget into stats: 13 to 21 Strength from 91 to 101.
HM_PHYSICAL_TWO_HAND_MULT = 0.5537
HM_PHYSICAL_TWO_HAND_DPS = 0.0695
HM_SOCKETED_THIN_MULT = 0.6              # socketed hard mode one-hander or shield with an effect
BOW_MULT = 0.405                         # physical InventoryType 15 ilvl 60-100: a bow below level 60 (S2, the same)

# Bows need no ammo (source/world/ranged_weapons.py, hunter-rework Q3); an item() declaration owns its entry, so it
# sets the column itself and the minted tiers copy it (ranged_weapons.py skips item-owned entries).
NO_AMMO = 0

ARMOR_SUBCLASS_PLATE = 4
MATERIAL_PLATE = 6
INVTYPE_HANDS = 10
DISPLAY_DARK_IRON_GAUNTLETS = 31683  # Dark Iron Gauntlets 19164

# Stock spells the list keeps on items whose other stock slot folds away (stock cooldowns, item_template).
SPELL_SECOND_WIND = 15604            # Use: mana over 10 sec, 15 min cooldown
SPELL_BURST_OF_KNOWLEDGE = 15646     # Use: mana cost reduced, 15 min cooldown
SPELL_HAND_OF_JUSTICE = 15600        # Equip: a chance on hit of an extra attack
SPELL_FURY_OF_FORGEWRIGHT = 15494    # Ironfoe, chance on hit: two extra attacks
STOCK_TRINKET_USE_COOLDOWN_MS = 900000

R, Y, B = Socket.RED, Socket.YELLOW, Socket.BLUE

# ---------------------------------------------------------------------------------------------------------------------
# Section 1: the Detention Block and the Ring of Law

# High Interrogator Gerstahn (stock item level 52-53)
item("brd_kentic_amice", base=11624, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("brd_greaves_of_withering_despair", base=22240, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Mastery")
# The wave's Agility tank back.
item("brd_blackveil_cape", base=11626, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge/Versatility")

# Lord Roccor (stock item level 52-57)
item("brd_stoneshell_guard", base=11631, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Parry/Crit")
item("brd_earthslag_shoulders", base=11632, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Mastery",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
# Bear relic: stats only, the stock Claw and Rake equip folds away.
item("brd_idol_of_ferocity", base=22397, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge/Proc")

# Houndmaster Grebmar (stock item level 52-53)
# Stock level 53: BOW_MULT (the 60-100 bow cell) on the Normal tier too (fix S2).
item("brd_houndmasters_bow", base=11628, ammo_type=NO_AMMO, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)", budget_mult=BOW_MULT)
item("brd_fleetfoot_greaves", base=11627, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("brd_spritecaster_cape", base=11623, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Mastery")

# Gorosh the Dervish (stock item level 57)
# Stock epic: Rare on Normal. The list's one three-secondary item; the dissolved set's chest. Red, then yellow (Crit).
item("brd_savage_gladiator_chain", base=11726, quality=RARE, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Haste/Versatility",
     sockets=(R, Y), socket_bonus=BONUS_CRIT_4, **NO_SET)
item("brd_bloodclot_band", base=22257, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Haste/CDH", primary_share=0)

# Grizzle (stock item level 55)
item("brd_entrenching_boots", base=22270, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("brd_grizzles_skinner", base=11702, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Mastery (Solo)")

# Eviscerator (stock item level 57)
item("brd_savage_gladiator_grips", base=11730, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4, **NO_SET)
# New: neck, secondaries only.
item("brd_spell_eaters_choker", name="Spell Eater's Choker", like=13085, ilvl=57, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary=None, secondary="Mastery/CDH", primary_share=0)

# Ok'thor the Breaker (stock item level 54)
item("brd_cyclopean_band", base=11824, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Proc/CDH", primary_share=0)
item("brd_ogreseer_fists", base=11665, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Haste",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)

# Anub'shiah (stock item level 55)
# Plate Tank chest: two blue sockets (tank gear, and Dodge is a blue stat), Dodge bonus.
item("brd_carapace_of_anubshiah", base=11678, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Dodge/Mastery",
     sockets=(B, B), socket_bonus=BONUS_DODGE_4)
item("brd_graverot_cape", base=11677, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Versatility/Proc")

# Hedrum the Creeper (stock item level 54)
# Keeps Corrosive Poison on hit (13526).
item("brd_hookfang_shanker", base=11635, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Agility (Solo)", secondary="Crit/Versatility")
item("brd_spiderfang_carapace", base=11633, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Versatility",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)

# ---------------------------------------------------------------------------------------------------------------------
# Section 2: Shadowforge City

# Pyromancer Loregrain (stock item level 53-55)
item("brd_kindling_stave", base=11750, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Mastery")
# Intellect, was Spirit (2026-11-21, level60-stat-curve healer mana pass, user ruling: half the Spirit-only leather
# caster drops become Intellect, at least one Spirit piece kept per slot).
item("brd_flamestrider_robes", base=11747, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Versatility",
     sockets=(R, Y), socket_bonus=BONUS_HASTE_4)
# Moved from Grizzle (the Mail Intellect shoulder).
item("brd_dregmetal_spaulders", base=11722, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Mastery")

# Warder Stilgiss and Verek (stock item level 53-57)
item("brd_boreal_mantle", base=11782, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Versatility",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
# Stock level 53: CASTER_MAIN_HAND_MULT (the 60-100 cell) on the Normal tier too (fix S2).
item("brd_arbiters_blade", base=11784, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)", budget_mult=CASTER_MAIN_HAND_MULT)
item("brd_dark_warders_pauldrons", base=22241, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Mastery")
item("brd_vereks_collar", base=11755, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/Proc", primary_share=0)

# Watchman Doomgrip and the Secret Safe, the Vault (stock item level 57; rulings 44 and 45)
# Was plate wrist: now plate hands (wrist is a Molten token slot here), the Dark Iron Gauntlets look.
item("brd_black_steel_bindings", base=22205, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block/Mastery",
     InventoryType=INVTYPE_HANDS, displayid=DISPLAY_DARK_IRON_GAUNTLETS)
item("brd_wand_of_eternal_light", base=22254, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Versatility (Solo)")
item("brd_magma_forged_band", base=22255, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Mastery/CDH", primary_share=0)
# The doc's one socket pick ("1 socket").
item("brd_mana_shaping_handwraps", base=22256, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)

# Lord Incendius (no stock item on his list: item level 60). Also drops the Molten wrist token (not here).
# New: the second healer trinket (was Everburning Ember, renamed: a stock quest item has that name).
item("brd_undying_ember", name="Undying Ember", like=11811, ilvl=60, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Haste")
item("brd_anvilfire_grips", name="Anvilfire Grips", like=12464, ilvl=60, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Mastery")
item("brd_robe_of_the_elemental_lord", name="Robe of the Elemental Lord", like=8252, ilvl=60, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Mastery/Versatility",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)

# Bael'Gar (stock item level 56)
item("brd_rubidium_hammer", base=11805, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Versatility (Solo)")
# Keeps Firebolt on hit (18086).
item("brd_force_of_magma", base=11803, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Proc (Solo)")
item("brd_magmaheart_mantle", name="Magmaheart Mantle", like=18374, ilvl=56, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Haste",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)

# ---------------------------------------------------------------------------------------------------------------------
# Section 3: the Manufactory

# General Angerforge (stock item level 56-58)
item("brd_angerforges_battle_axe", base=11816, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste (Solo)")
# Tank sword; keeps its attack power proc (15602).
item("brd_lord_generals_sword", base=11817, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Parry (Solo)")
item("brd_royal_decorated_armor", base=11820, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Versatility",
     sockets=(R, Y), socket_bonus=BONUS_CRIT_4)

# Golem Lord Argelmach (stock item level 59). Also drops the Molten waist token (not here).
# Healer trinket: keeps its mana Use (15604, stock 15 min cooldown); the stock +spell power Equip folds away.
item("brd_second_wind", base=11819, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Mastery/Versatility",
     spells=(use_spell(SPELL_SECOND_WIND, cooldown=STOCK_TRINKET_USE_COOLDOWN_MS, category_cooldown=0),))
# Keeps Thorns (15438); one secondary (every two-stat ring pair is taken, ruling 92 BD9).
item("brd_naglering", base=11669, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary=None, secondary="Versatility (Solo)", primary_share=0)
item("brd_omnicast_boots", base=11822, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Mastery",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)

# ---------------------------------------------------------------------------------------------------------------------
# Section 4: the Imperial Seat

# Phalanx (stock item level 56)
# Keeps Wound on hit (16433).
item("brd_bloodfist", base=11744, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Agility (Solo)", secondary="Crit (Solo)")
item("brd_fists_of_phalanx", base=11745, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Haste",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("brd_golem_fitted_pauldrons", base=22212, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Versatility")

# Ambassador Flamelash (stock item level 56-58)
# Keeps Flame Wrath on hit (16559).
item("brd_flame_wrath", base=11809, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Agility (Solo)", secondary="Crit (Solo)")
# Caster trinket: keeps its Use (15646, stock 15 min cooldown); the stock +spell power Equip folds away.
item("brd_burst_of_knowledge", base=11832, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Haste",
     spells=(use_spell(SPELL_BURST_OF_KNOWLEDGE, cooldown=STOCK_TRINKET_USE_COOLDOWN_MS, category_cooldown=0),))
item("brd_molten_fists", base=11814, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)

# Magmus (stock item level 57-58)
item("brd_magmus_stone", base=11935, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Mastery",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
# Elemental relic: keeps its Shock equip (27859; see the module docstring for the potency move).
item("brd_totem_of_rage", base=22395, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Intellect (Solo)", secondary="Haste/Mastery")
# Protection relic: keeps its Devotion Aura equip (27850).
item("brd_libram_of_truth", base=22400, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Parry/Haste")

# The Chest of The Seven (stock item level 57-59, two drops per chest)
# Keeps Drain Life on hit (16414).
item("brd_wraith_scythe", base=11920, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Haste (Solo)")
# Stock level 57 (both): CASTER_MAIN_HAND_MULT on the Normal tier too (fix S2).
item("brd_blood_etched_blade", base=11922, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery (Solo)", budget_mult=CASTER_MAIN_HAND_MULT)
item("brd_the_hammer_of_grace", base=11923, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste (Solo)", budget_mult=CASTER_MAIN_HAND_MULT)
# Was mail: now plate (the list's "Plate (was mail)"), the dungeon's one Plate Intellect piece. The display stays the
# stock one; the armor comes from the plate curve.
item("brd_deathdealer_breastplate", base=11926, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Versatility",
     sockets=(R, Y), socket_bonus=BONUS_CRIT_4,
     subclass=ARMOR_SUBCLASS_PLATE, Material=MATERIAL_PLATE)
# Moved from Princess Moira.
item("brd_ebonsteel_spaulders", base=12557, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Dodge/Versatility")
item("brd_swiftwalker_boots", base=12553, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Versatility")

# Emperor Dagran Thaurissan (stock item level 58-60, two drops per kill; Princess Moira's items fold in). Also drops
# the Molten head token (not here).
# Keeps its extra attack Equip (15600); the stock +attack power Equip folds away.
item("brd_hand_of_justice", base=11815, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Haste/Proc", primary_share=0,
     spells=(equip_spell(SPELL_HAND_OF_JUSTICE),))
item("brd_robes_of_the_royal_crown", base=11924, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Mastery",
     sockets=(R, Y), socket_bonus=BONUS_HASTE_4)
item("brd_thaurissans_royal_scepter", base=11928, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Versatility")
item("brd_the_emperors_new_cape", base=11930, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Haste")
item("brd_imperial_jewel", base=11933, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Mastery/Proc", primary_share=0)
item("brd_hands_of_the_exalted_herald", base=12554, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Mastery")
item("brd_high_priestess_boots", base=12556, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Versatility")
# New (from Moira): the Restoration idol, the Emperor's lowest stock item level (58).
item("brd_idol_of_the_wayward_princess", name="Idol of the Wayward Princess", like=22398, ilvl=58, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Crit/Haste")

# The minor pool (Panzor the Invincible, Hurley Blackbreath, Fineous Darkvire, Ribbly Screwspigot, Plugger Spazzring;
# stock item level 55-58)
item("brd_hurleys_tankard", base=18044, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Versatility (Solo)")
# The dungeon's one Leather Tank piece: Agility, Dodge and Mastery, extra Stamina.
item("brd_coal_miner_boots", base=18043, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge/Mastery", extra_stamina=EXTRA_STAMINA)
item("brd_firemoss_boots", base=22275, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Mastery")
item("brd_mixologists_tunic", base=12793, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
# Keeps Rend on hit (13318).
item("brd_barman_shanker", base=12791, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Agility (Solo)", secondary="Crit/Haste")
item("brd_rock_golem_bulwark", base=11785, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block/Mastery",
     nature_res=0, arcane_res=0)
item("brd_stone_of_the_earth", base=11786, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste/Mastery")
item("brd_shalehusk_boots", base=11787, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Dodge/Mastery")

# ---------------------------------------------------------------------------------------------------------------------
# The Ring of Law, the Encore: hard mode (heroic hard mode 71, then 81 / 91 / 101). New items, the ladder sets every
# tier.

# Equip: +10% melee damage to enemies below 30% health (a percent: unscaled). One red socket.
item("brd_theldrens_executioner", name="Theldren's Executioner", like=11931, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Strength (Solo)", secondary="Crit (Solo)", budget_mult=HM_PHYSICAL_TWO_HAND_MULT,
     extra_dps=HM_PHYSICAL_TWO_HAND_DPS,
     sockets=(R,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(theldrens_executioner_206830),))
# Equip: melee hits open a stacking bleed (scaled by item level). One red socket.
item("brd_leftys_shiv", name="Lefty's Shiv", like=22266, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Agility (Solo)", secondary="Mastery/Versatility", budget_mult=HM_SOCKETED_THIN_MULT,
     sockets=(R,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(leftys_shiv_206831, scale="budget"),))
# Equip: direct heals may chain half the amount to the most injured party member (a share: unscaled). One red socket.
item("brd_korvs_spirit_fetish", name="Korv's Spirit Fetish", like=4984, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Spirit (Solo)", secondary="Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(korvs_spirit_fetish_206833),))

# ---------------------------------------------------------------------------------------------------------------------
# Lord Incendius, Lord of the Lake: hard mode.

# Strength tank shield, Equip: blocks may erupt in flame (scaled). One blue socket (tank gear), Block bonus.
item("brd_black_anvil_bulwark", name="Black Anvil Bulwark", like=4069, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Strength (Solo)", secondary="Block/Haste", budget_mult=HM_SOCKETED_THIN_MULT,
     sockets=(B,), socket_bonus=BONUS_BLOCK_4,
     spells=(equip_spell(black_anvil_bulwark_206835, scale="budget"),))
# Equip: melee hits may slam the ground under the target (scaled). One red socket.
item("brd_fist_of_the_lake_lord", name="Fist of the Lake Lord", like=11743, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Agility (Solo)", secondary="Versatility (Solo)", budget_mult=HM_SOCKETED_THIN_MULT,
     sockets=(R,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(fist_of_the_lake_lord_206837, scale="budget"),))
# Equip: damaging spells may call a Lava Spawn (scaled). One red socket.
item("brd_scepter_of_the_molten_lake", name="Scepter of the Molten Lake", like=11932, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Intellect (Solo)", secondary="Haste/Mastery",
     budget_mult=HM_CASTER_TWO_HAND_MULT, sockets=(R,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(scepter_of_the_molten_lake_206839, scale="budget"),))

# ---------------------------------------------------------------------------------------------------------------------
# Golem Lord Argelmach, the Prototype: hard mode.

# Use (2 min): three arcane orbs strike nearby enemies for 12 sec (scaled). A trinket: no socket.
item("brd_prototype_power_core", name="Prototype Power Core", like=18638, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Haste/CDH", primary_share=0,
     spells=(use_spell(prototype_power_core_206842, scale="budget"),))
# Equip: heals may deploy a Mending Servo (scaled). One red socket.
item("brd_golemwrights_mending_rod", name="Golemwright's Mending Rod", like=18321, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Spirit (Solo)", secondary="Crit/Versatility",
     budget_mult=HM_SOCKETED_THIN_MULT, sockets=(R,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(golemwrights_mending_rod_206844, scale="budget"),))
# Ring, Equip: Lethal Attraction (scaled). One secondary and an effect (ruling 92 BD9). One red socket.
item("brd_electrons_lethal_coil", name="Electron's Lethal Coil", like=11934, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Mastery (Solo)", primary_share=0,
     sockets=(R,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(electrons_lethal_coil_206847, scale="budget"),))

# ---------------------------------------------------------------------------------------------------------------------
# Emperor Dagran Thaurissan, the Avatar of Ragnaros: hard mode.

# Moved from the Emperor's normal list (1% stock): keeps Fury of Forgewright on hit (stock 15494, 1.5 procs per
# minute). A new item with Ironfoe's look: the hard mode ladder's first tier is 71, so the stock row cannot be its
# base. One red socket.
item("brd_ironfoe", name="Ironfoe", like=11684, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Strength (Solo)", secondary="Crit (Solo)", budget_mult=HM_SOCKETED_THIN_MULT,
     sockets=(R,), socket_bonus=BONUS_CRIT_4,
     spells=(hit_spell(SPELL_FURY_OF_FORGEWRIGHT, ppm=1.5),))
# Tank trinket, Use (2 min): -20% damage taken for 8 sec, then a Fire burst (scaled). No primary: the
# "Dodge/Mastery (Any)" shape (new). A trinket: no socket.
item("brd_volcanic_heartstone", name="Volcanic Heartstone", like=11810, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Dodge/Mastery (Any)", primary_share=0,
     spells=(use_spell(volcanic_heartstone_206850, scale="budget"),))
# Equip: damaging spells may loose a shadow beam along the line to the target (scaled). One red socket.
item("brd_orb_of_the_sorcerer_thane", name="Orb of the Sorcerer-Thane", like=20694, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Intellect (Solo)", secondary="Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(orb_of_the_sorcerer_thane_206852, scale="budget"),))
