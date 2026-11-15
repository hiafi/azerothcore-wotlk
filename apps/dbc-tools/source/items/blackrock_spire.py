"""
The Blackrock Spire loot (wave 2 dungeon items, after the Stratholme precedent stratholme.py): the 68 approved list
items and the 6 hard mode items of Overlord Wyrmthalak and General Drakkisath (docs/dungeons/blackrock-spire-rework.md
## Loot, approved 2026-11-10, rulings 76 to 79; copied in docs/dungeons/dungeon-loot-vanilla.md). Out of scope here:
the Molten tokens (molten_set.py), the 21 Tier 0 pieces and the 18 stock pieces in the token slots (cut), quest
items and the kept pools; the loot tables belong to the dungeon build (a blackrock_spire_loot.py after the
Stratholme precedent stratholme_loot.py).

Blackrock Spire normal is a level 60 dungeon, so Normal drops Rare at the item's stock level (59-63), Heroic is 66
Epic with the Heroic flag, then the three empowered steps (ladders.py). Stock items keep their id as the Normal tier
(`base=`); the three stock epics (Mark of the Dragon Lord, Felstriker, Blackblade of Shahram) are lowered to Rare on
Normal (normal drops rare, heroic drops epic). Voone's Twitchbow (a green, cut) is not declared. A new item takes the
lowest stock item level of its boss's list (Vosh'gajin 59, Voone / Smolderweb / Urok / Zigris / Halycon and Gizrul
60, Wyrmthalak / Emberseer / Solakar 61, the Beast / Drakkisath 63; the list as it stands, so a cut Tier 0 piece does
not count); required level = item level - 5, the stock pattern.

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and
secondaries are listed. Unlike Stratholme, this list names two secondaries on most items (ruling 78: 59 items with
two, 14 with one, 1 with three), so most armor takes a two-secondary Even pair shape ("Crit/Versatility", the order of
the shape name, not of the doc). Rings, necks and trinkets without a primary carry secondaries only (`primary=None`,
share 0); the trinkets that list a primary (Heart of Wyrmthalak, Draconic Infused Emblem) keep it. Tank pieces with
"extra Stamina" take a quarter more (`extra_stamina=0.25`, the Deadmines Smelting Pants pick).

**Shapes this list needs that did not exist when it was written** (WP-INT adds them in the one pending itemization
file; each models an existing Even pair, name order as below, stat types in parentheses):
  - "Mastery/CDH"           secondary, Even pair (22, 24), no rule: Smolderweb's Eye, Tome of the Lost
  - "Versatility/Proc"      secondary, Even pair (23, 33), no rule: Halycon's Spiked Collar, Painweaver Band
  - "Dodge/Versatility"     secondary, Even pair (13, 23), rules requires any of Strength, Agility (as Dodge/Crit 57):
                            Supply Sergeant's Girdle
  - "Block/Versatility"     secondary, Even pair (15, 23), rule requires Strength (as Block/Crit 61): Battleborn
                            Armbraces, Draconian Deflector, Libram of the Dragon Guard
  - "Haste/Mastery/Proc"    secondary, Even trio (36, 22, 33), no rule (as Crit/Haste/Mastery 42): Tooth of Gnarr

**Kept stock effects** (`keep_spells=True`, the list's "keeps ..."): Numbing Pain (Keris of Zul'Serak), the poison
(Venomspitter, Smolderweb's Eye), Frost Blast (Chillpike), Flame Lash (Heart of Wyrmthalak), the Mark of the Dragon
Lord and Heart of the Scale Uses, Wound (Blackhand Doomsaw), Felstriker, Seeping Willow's cloud, Shahram (Blackblade)
and Chromatic Infusion (Draconic Infused Emblem). Their effect costs 0.7 of the budget like any effect item
(itemization-changes.md section 3). The stock spells are the same on every tier (they are not declared in source/items,
so they cannot scale). Finkle's Skinner keeps only its Skinning bonus (16718): `spells=` names that one stock spell, so
its other stock line (Beast Slaying, 18067) is dropped rather than kept (`keep_spells` is all or nothing). Every other
stock spell slot (+attack power, MP5) folds into the budget (`absorbed_spell_slots`), as the list's "stats only" asks.
Dal'Rend's pair keeps its stock two piece set (itemset 41, untouched on every tier). Venomspitter keeps its stock
itemset 65 as well (a two piece set with the Fang of the Crystal Spider, not on this list): a designer question.

**Unpriced stock extras are cleared on every tier** (the Stratholme precedent): the stock resistances of three list
items (Wolfshear Leggings nature, Wildfire Cape fire, Draconian Deflector fire) and the random "of the ..." property
(3304) of Gyth's three heads.

**Sockets** (docs/dungeons/boss-rework-systems.md "Sockets", approved 2026-11-02; the BRS picks are this file's, a
designer question: the doc names none): about one standalone piece per boss, 2 on a two-hander; hard mode items 1
except the trinkets. The first socket is red on damage and healing gear and blue on tank gear; a second socket takes
the color of the item's first secondary (docs/Systems.md "Sockets and gems"). Sockets start at Heroic (ladders.py).
Socket bonuses are stock +4 SpellItemEnchantment rows (deadmines.py explains why the bonus does not scale): the bonus
follows the first secondary (the doc's order); no enchant exists for Mastery, Versatility, Cooldown Haste or Proc
Chance, so those take Haste (Mastery, Cooldown Haste) or Crit (Versatility, Proc Chance), the Deadmines substitutes.

**Bind on Pickup**: every stock item here is already Bind on Pickup, the new items are set to it.

**Hard mode items** (ladder `vanilla_hard_mode`, 71 / 81 / 91 / 101) carry the effects of
blackrock_spire_hard_mode_effects.py (the `blackrock_spire_items` reservation 206800-206829). Each socketed once
except the two trinkets. Nothing there scales by item level (every number is a percent or a time), so none is
`scale="budget"`. Effect items cost 0.7 of the budget (the default). All six are unique-equipped across their tiers.
"""

from lib.dsl.items import Quality, Socket, equip_spell, item, use_spell

from .blackrock_spire_hard_mode_effects import (
    bloodaxe_war_horn_206800,
    orders_of_the_general_206809,
    shardstaff_of_stolen_power_206804,
    the_humbler_206810,
    trophy_of_the_champion_206806,
    ward_of_the_three_tribes_206802,
)
from .ladders import VANILLA_DUNGEON, VANILLA_HARD_MODE

# Socket bonus enchants (stock SpellItemEnchantment ids, the Deadmines ones; see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_DODGE_4 = 2871
BONUS_PARRY_4 = 3359

BOP = 1  # ITEM_BIND_ON_ACQUIRE
RARE = Quality.RARE
EXTRA_STAMINA = 0.25  # "extra Stamina" on a tank piece: a quarter more than the tier's baseline

# Bows, guns and crossbows need no ammo (source/world/ranged_weapons.py, hunter-rework Q3). An item() declaration owns
# its entry, so it sets the column itself; the minted tiers copy it, and a new gun (`like=` a gun) sets it too.
NO_AMMO = 0

# ---------------------------------------------------------------------------------------------------------------------
# Highlord Omokk (stock item level 60)

# Strength two-hand mace; two sockets (a two-hander), the second yellow (Versatility, the first secondary).
item("brs_fist_of_omokk", base=13167, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Versatility",
     sockets=(Socket.RED, Socket.YELLOW), socket_bonus=BONUS_CRIT_4)
item("brs_tressermane_leggings", base=13169, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Mastery")
item("brs_skyshroud_leggings", base=13170, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Versatility")

# ---------------------------------------------------------------------------------------------------------------------
# Shadow Hunter Vosh'gajin (stock item level 59)

item("brs_funeral_cuffs", base=12626, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Mastery")
item("brs_blackcrow", base=12651, ammo_type=NO_AMMO, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Haste",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
item("brs_riphook", base=12653, ammo_type=NO_AMMO, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery/Versatility")
# New: the wave's Enhancement totem (the stat budget of a relic; no stock effect to keep).
item("brs_totem_of_hexed_blood", name="Totem of Hexed Blood", like=22395, ilvl=59, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste/Proc")

# ---------------------------------------------------------------------------------------------------------------------
# War Master Voone (stock item level 60)

# Keeps Numbing Pain on hit (16528).
item("brs_keris_of_zulserak", base=12582, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Agility (Solo)", secondary="Versatility (Solo)")
item("brs_talisman_of_evasion", base=13177, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Haste/CDH", primary_share=0)
item("brs_brazecore_armguards", base=13179, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Versatility",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)
# Stock, from its 100% row; now on Voone's list (ruling 77): the vanilla dungeons' one Strength thrown item.
item("brs_flightblade_throwing_axe", base=28972, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Mastery (Solo)")
# New: a Strength axe at level 60 normal.
item("brs_war_masters_hatchet", name="War Master's Hatchet", like=18498, ilvl=60, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Crit (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Mother Smolderweb (stock item level 60)

# Keeps its poison on hit (18203).
item("brs_venomspitter", base=13183, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Agility (Solo)", secondary="Haste (Solo)")
# Keeps its poison Use (17330); a trinket with no primary.
item("brs_smolderwebs_eye", base=13213, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary=None, secondary="Mastery/CDH", primary_share=0)
# New: the wave's Cloth Spirit waist.
item("brs_smolderweb_silk_sash", name="Smolderweb Silk Sash", like=13956, ilvl=60, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Crit/Versatility",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)

# ---------------------------------------------------------------------------------------------------------------------
# Urok Doomhowl (stock item level 60-61)

item("brs_rosewine_circle", base=13178, ladder=VANILLA_DUNGEON,
     primary=None, secondary="CDH/Versatility", primary_share=0)
item("brs_marksmans_girdle", base=22232, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Versatility")
# New: a Mail Intellect head, one red socket.
item("brs_shardlinked_coif", name="Shardlinked Coif", like=12636, ilvl=60, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery/Proc",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)

# ---------------------------------------------------------------------------------------------------------------------
# Quartermaster Zigris (stock item level 60)

item("brs_cloudrunner_girdle", base=13252, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Mastery")
# New: the wave's Agility gun (a Hunter ranged weapon, no ammo).
item("brs_quartermasters_blunderbuss", name="Quartermaster's Blunderbuss", like=13146, ilvl=60, bonding=BOP,
     ammo_type=NO_AMMO, ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste/Versatility")
# New: the Plate tank waist; tank gear takes a blue socket and a Dodge bonus.
item("brs_supply_sergeants_girdle", name="Supply Sergeant's Girdle", like=13959, ilvl=60, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Dodge/Versatility",
     sockets=(Socket.BLUE,), socket_bonus=BONUS_DODGE_4)

# ---------------------------------------------------------------------------------------------------------------------
# Halycon and Gizrul (stock item level 60-61, two drops per kill)

item("brs_slashclaw_bracers", base=13211, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Mastery")
item("brs_halycons_spiked_collar", base=13212, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Versatility/Proc", primary_share=0)
item("brs_rhombeard_protector", base=13205, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery/Versatility")
item("brs_wolfshear_leggings", base=13206, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Haste",
     nature_res=0)
item("brs_bleak_howler_armguards", base=13208, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Versatility",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
# New: the Leather tank waist, extra Stamina.
item("brs_packleaders_hide_belt", name="Packleader's Hide Belt", like=13962, ilvl=60, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Dodge/Mastery", extra_stamina=EXTRA_STAMINA)

# ---------------------------------------------------------------------------------------------------------------------
# Overlord Wyrmthalak (stock item level 61-62)

# Caster two-hand staff; two sockets (a two-hander), the second yellow (Versatility, the first secondary).
item("brs_trindlehaven_staff", base=13161, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Versatility",
     sockets=(Socket.RED, Socket.YELLOW), socket_bonus=BONUS_CRIT_4)
item("brs_relentless_scythe", base=13163, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Parry/Mastery")
# Agility tank polearm; keeps Frost Blast on hit (19260).
item("brs_chillpike", base=13148, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Agility (Solo)", secondary="Dodge/Mastery")
# Keeps Flame Lash on hit (27656).
item("brs_heart_of_wyrmthalak", base=22321, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Crit/Versatility")
# Stock epic, Rare on Normal. Keeps its mana shield Use (17252).
item("brs_mark_of_the_dragon_lord", base=13143, quality=RARE, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary=None, secondary="Mastery/Proc", primary_share=0)
# Keeps its fire shield Use (17275); a tank trinket with no primary.
item("brs_heart_of_the_scale", base=13164, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary=None, secondary="Parry/Versatility (Any)", primary_share=0)

# ---------------------------------------------------------------------------------------------------------------------
# Pyroguard Emberseer (stock item level 61)

item("brs_wildfire_cape", base=12905, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Mastery",
     fire_res=0)
item("brs_emberfury_talisman", base=12929, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/CDH", primary_share=0)
# New: a Plate Strength head, one red socket.
item("brs_helm_of_the_bound_flame", name="Helm of the Bound Flame", like=12620, ilvl=61, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Haste/Versatility",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
# New: the wave's caster wand.
item("brs_incarcerators_wand", name="Incarcerator's Wand", like=18483, ilvl=61, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Solakar Flamewreath (stock item level 61)

item("brs_dustfeather_sash", base=12589, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Proc")
item("brs_crystallized_girdle", base=12606, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Mastery")
# Stock (level 63), moved from Rend; its MP5 Equip folds away.
item("brs_feralsurge_girdle", base=18104, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Mastery")
# New: the wave's one Plate Intellect piece, one red socket.
item("brs_flamewreath_legplates", name="Flamewreath Legplates", like=13075, ilvl=61, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/CDH",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)

# ---------------------------------------------------------------------------------------------------------------------
# Warchief Rend Blackhand and Gyth (stock item level 63, Gyth's heads 60; two drops per kill)

# Keeps Wound on hit (16549).
item("brs_blackhand_doomsaw", base=12583, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Mastery (Solo)")
item("brs_eye_of_rend", base=12587, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Mastery",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
# Stock epic, Rare on Normal. Keeps its guaranteed crits on hit (16551).
item("brs_felstriker", base=12590, quality=RARE, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Agility (Solo)", secondary="Mastery (Solo)")
item("brs_warmaster_legguards", base=12935, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste/Mastery")
item("brs_battleborn_armbraces", base=12936, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block/Versatility")
# The stock two piece set 41 stays on every tier (the ruling: do not touch the set).
item("brs_dalrends_sacred_charge", base=12940, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit (Solo)")
item("brs_dalrends_tribal_guardian", base=12939, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Mastery (Solo)")
# Gyth's three heads carry the random "of the ..." property 3304: cleared.
item("brs_gyths_skull", base=12952, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Parry/Mastery",
     RandomProperty=0)
item("brs_dragoneye_coif", base=12953, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Versatility",
     RandomProperty=0)
item("brs_tribal_war_feathers", base=12960, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Versatility",
     RandomProperty=0)

# ---------------------------------------------------------------------------------------------------------------------
# The Beast (stock item level 63, two drops per kill)

# Keeps its Skinning bonus (16718) only: `spells=` replaces the stock slots (Beast Slaying, 18067, is dropped).
item("brs_finkles_skinner", base=12709, ladder=VANILLA_DUNGEON,
     spells=(equip_spell(16718),),
     primary="Intellect (Solo)", secondary="Versatility (Solo)")
item("brs_blademaster_leggings", base=12963, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Haste")
item("brs_tristam_legguards", base=12964, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery/Versatility",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)
item("brs_blackmist_armguards", base=12966, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Versatility")
item("brs_bloodmoon_cloak", base=12967, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Mastery")
# Keeps its Nature cloud on hit (17196).
item("brs_seeping_willow", base=12969, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Mastery (Solo)")
# New: the wave's cat idol.
item("brs_idol_of_the_core_hound", name="Idol of the Core Hound", like=23197, ilvl=63, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit/Mastery")

# ---------------------------------------------------------------------------------------------------------------------
# General Drakkisath (stock item level 63, two drops per kill)

# Stock epic, Rare on Normal. Keeps Shahram on hit (16602).
item("brs_blackblade_of_shahram", base=12592, quality=RARE, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Proc (Solo)")
item("brs_draconian_deflector", base=12602, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block/Versatility",
     fire_res=0)
item("brs_painweaver_band", base=13098, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Versatility/Proc", primary_share=0)
# The list's one three-secondary item.
item("brs_tooth_of_gnarr", base=13141, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Haste/Mastery/Proc", primary_share=0)
item("brs_brigam_girdle", base=13142, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Mastery",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
item("brs_tome_of_the_lost", base=22253, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery/CDH")
item("brs_spellweavers_turban", base=22267, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Mastery")
# Keeps its spell power Use (27675, Chromatic Infusion).
item("brs_draconic_infused_emblem", base=22268, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Intellect (Solo)", secondary="Crit/Mastery")
item("brs_shadow_prowlers_cloak", base=22269, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Mastery")
# New: the wave's tank libram.
item("brs_libram_of_the_dragon_guard", name="Libram of the Dragon Guard", like=22400, ilvl=63, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Block/Versatility")

# ---------------------------------------------------------------------------------------------------------------------
# Overlord Wyrmthalak, the war horn: hard mode (heroic hard mode 71, then 81 / 91 / 101). New items, the ladder sets
# every tier.

# Use (2 min): a war cry interrupts the enemies within 10 yd, who then deal 10% less damage. A trinket with no primary.
item("brs_bloodaxe_war_horn", name="Bloodaxe War Horn", like=14557, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Mastery/Versatility", primary_share=0,
     spells=(use_spell(bloodaxe_war_horn_206800),))
# Equip: 1% less damage taken for each enemy attacking you within 8 yd, up to 5. Tank shield, blue socket.
item("brs_ward_of_the_three_tribes", name="Ward of the Three Tribes", like=14002, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Strength (Solo)", secondary="Parry/Versatility (Any)",
     sockets=(Socket.BLUE,), socket_bonus=BONUS_PARRY_4,
     spells=(equip_spell(ward_of_the_three_tribes_206802),))
# Equip: your spell crits give Stolen Power (+1% spell damage and healing, 10 sec, 5 stacks). One red socket.
item("brs_shardstaff_of_stolen_power", name="Shardstaff of Stolen Power", like=20654, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Intellect (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(shardstaff_of_stolen_power_206804),))

# ---------------------------------------------------------------------------------------------------------------------
# General Drakkisath, the General's Army: hard mode.

# Equip: an enemy you damaged in the last 5 sec dies: +1% damage and healing, 30 sec, 5 stacks. A trinket, no primary.
item("brs_trophy_of_the_champion", name="Trophy of the Champion", like=28830, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary=None, secondary="Crit/Versatility", primary_share=0,
     spells=(equip_spell(trophy_of_the_champion_206806),))
# Use (2 min): party members within 30 yd take 10% less damage for 8 sec. One red socket (Mastery: a Haste bonus).
item("brs_orders_of_the_general", name="Orders of the General", like=22319, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Spirit (Solo)", secondary="Haste/Mastery",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4,
     spells=(use_spell(orders_of_the_general_206809),))
# Equip: your melee hits can Humble the target (5% less damage for 8 sec). Strength tank mace, blue socket.
item("brs_the_humbler", name="The Humbler", like=13204, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Strength (Solo)", secondary="Dodge (Solo)",
     sockets=(Socket.BLUE,), socket_bonus=BONUS_DODGE_4,
     spells=(equip_spell(the_humbler_206810),))
