"""
The Stratholme loot (wave 1 dungeon items, after the Deadmines precedent deadmines.py): the 73 approved list items and
the 6 hard mode items of Balnazzar and Baron Rivendare (docs/dungeons/stratholme-rework.md ## Loot, approved
2026-11-06, ruling 62; copied in docs/dungeons/dungeon-loot-vanilla.md). Out of scope here: the Haunted tokens and set
pieces, Deathcharger's Reins, quest items, keys and the kept pools; the loot tables wait for the bosses.

Stratholme normal is a level 60 dungeon, so Normal drops Rare at the item's stock level (57-63, relics 65; the shared
doc Loot ladder: "Normal, level 60 dungeons: stock, about 60"), Heroic is 66 Epic with the Heroic flag, then the three
empowered steps (ladders.py). Stock items keep their id as the Normal tier (`base=`); the stock greens (the resist
pieces the list turns into real items) and the two stock epics (Book of the Dead, Runeblade of Baron Rivendare) are
raised or lowered to Rare on Normal (normal drops rare, heroic drops epic). A new item takes the lowest stock item level
of its boss's list (The Unforgiven 57, Forresten 58, Timmy 59, Willey 61, Galford 61) and Malor, who has no stock item,
takes 60 (the ladder's "about 60"); required level = item level - 5, the stock pattern.

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and
secondary are listed. Rings and necks carry secondaries only (`primary=None`, share 0). Tank pieces with "extra
Stamina" take a quarter more (`extra_stamina=0.25`, the Deadmines Smelting Pants pick).

**Kept stock effects** (`keep_spells=True`, the list's "keeps ..."): Soul Breaker, Piccolo of the Flaming Fire, The
Cruel Hand of Timmy, Cannonball Runner, Demonshear, Book of the Dead, Crest of Retribution, Ramstein's Lightning
Bolts, Skullforge Reaver and the Runeblade. Their effect costs 0.7 of the budget like any effect item
(itemization-changes.md section 3), except the Piccolo, whose dance adds no throughput: "full stat budget" (designer).
The stock spells are the same on every tier (they are not declared in source/items, so they cannot scale). Every other
stock spell slot (+attack power, MP5, health regen, the relics' flat spell power or rage effects) folds into the budget
(`absorbed_spell_slots`), as the list's "stats only" asks.

**Sockets** (stratholme-rework.md "Sockets", approved 2026-11-06; colors docs/Systems.md "Sockets and gems"): the
first socket is red on damage and healing gear and blue on tank gear; a second socket takes the color of the item's
first secondary. Sockets start at Heroic (ladders.py). Socket bonuses are the Deadmines enchants (+4 ratings, stock
SpellItemEnchantment; deadmines.py explains why the bonus does not scale): no enchant exists for Mastery,
Versatility, Cooldown Haste or Proc Chance, so those items take Haste (Mastery, Cooldown Haste) or Crit
(Versatility, Proc Chance), the Deadmines substitutes.

**Bind on Pickup from Heroic up.** Four stock pieces are Bind on Equip (Plaguebat Fur Gloves from the BoE pool, the
Militia Shoulderguard, Totem of the Storm, Idol of the Moon). Their Normal tier stays the stock row; every minted tier
binds on pickup (the Deadmines Defias Belt ruling, R1 N5).

**Hard mode items** (ladder `vanilla_hard_mode`, 71 / 81 / 91 / 101) carry the effects of
stratholme_hard_mode_effects.py (the `stratholme_items` reservation 205660-205699). Each socketed once (red) except the
two trinkets. Effects whose numbers the designer scales by item level (Carrion Signet, Ysida's Locket, Deathcharger's
Spur) are `scale="budget"`: every tier above 71 carries its own copies (stage IV10). The Dust (a sleep), the Tome (a
share of the heal) and the Blade (a percent) have nothing to scale and carry their spells on every tier. Effect items
cost 0.7 of the budget, except the Dust: "full stat budget (the Use adds no throughput)" (designer). All six are
unique-equipped across their tiers (IV10 follow-up 1).

**Ysida's Locket** takes Cooldown Haste and Versatility, shape 74 "CDH/Versatility", added for it by the wave 1
integration (data/sql/updates/pending_db_world/itemization_templates_v2, modeled on the two-secondary Even shapes).
"""

from lib.dsl.items import Quality, Socket, equip_spell, item, use_spell

from .ladders import VANILLA_DUNGEON, VANILLA_HARD_MODE
from .stratholme_hard_mode_effects import (
    blade_of_the_condemned_205668,
    carrion_signet_205660,
    deathchargers_spur_205670,
    dust_of_the_nathrezim_205662,
    two_faced_tome_205663,
    ysidas_locket_205665,
)

# Socket bonus enchants (stock SpellItemEnchantment ids, the Deadmines ones; see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_BLOCK_4 = 2972

BOP = 1  # ITEM_BIND_ON_ACQUIRE
RARE = Quality.RARE
EXTRA_STAMINA = 0.25  # "extra Stamina" on a tank piece: a quarter more than the tier's baseline

# Bows, guns and crossbows need no ammo (source/world/ranged_weapons.py, hunter-rework Q3). An item() declaration owns
# its entry, so it sets the column itself; the minted tiers copy it. TODO(orchestrator): ranged_weapons.py also
# declares item_template(<entry>, ammo_type=0) for these three stock entries (13380, 18729, 18738), which the item
# checks refuse ("one owner per entry"); it should skip entries an item(base=...) declaration owns.
NO_AMMO = 0

ARMOR_SUBCLASS_LEATHER = 2
MATERIAL_LEATHER = 8

HIGHER_TIERS = ("heroic", "empowered_1", "empowered_2", "empowered_3")
BOP_ABOVE_NORMAL = {name: {"bonding": BOP} for name in HIGHER_TIERS}

# ---------------------------------------------------------------------------------------------------------------------
# The Unforgiven (stock item level 57)

item("strat_mask_of_the_unforgiven", base=13404, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)
# Plate tank shoulders: Strength and Dodge (the stock Defense is a dead stat).
item("strat_wailing_nightbane_pauldrons", base=13405, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Dodge (Solo)")
# Strength tank axe; keeps its health and mana drain on hit (17506).
item("strat_soul_breaker", base=13408, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Parry (Solo)")
# New: a hood for the soul he frees last; stats only.
item("strat_shroud_of_the_last_soul", name="Shroud of the Last Soul", like=22225, ilvl=57, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Haste (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Hearthsinger Forresten (stock item level 58)

# Keeps the dance Use (18400), which adds no throughput: the full stat budget (designer), no primary.
item("strat_piccolo_of_the_flaming_fire", base=13379, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary=None, secondary="Haste/Mastery", primary_share=0, budget_mult=1.0)
item("strat_rainbow_girdle", base=13384, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="CDH (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
# New: the wave's Spirit dagger and a Spirit one-hand at level 60 normal (ruling 4).
item("strat_hearthsingers_tuning_fork", name="Hearthsinger's Tuning Fork", like=20657, ilvl=58, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Mastery (Solo)")
# New: the Songbird Blouse's stats in a free slot.
item("strat_songbird_sash", name="Songbird Sash", like=13252, ilvl=58, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit (Solo)")
# Stock, from the Stratholme BoE pool (1329000); Bind on Pickup from Heroic up.
item("strat_plaguebat_fur_gloves", base=18744, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)", overrides=BOP_ABOVE_NORMAL)

# ---------------------------------------------------------------------------------------------------------------------
# Timmy the Cruel (stock item level 59-61)

# Keeps Curse of Timmy on hit (17505).
item("strat_the_cruel_hand_of_timmy", base=13401, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Agility (Solo)", secondary="Proc (Solo)")
item("strat_grimgore_noose", base=13403, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Versatility (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)
# New: stats only.
item("strat_freeze_tag_mittens", name="Freeze Tag Mittens", like=18309, ilvl=59, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Haste (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Malor the Zealous (no stock item of his own: item level 60)

# New: his Medallion paladin's gauntlets, one red socket.
item("strat_gauntlets_of_the_zealot", name="Gauntlets of the Zealot", like=12631, ilvl=60, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="CDH (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
# New: his Inquisitor's girdle, plate tank.
item("strat_inquisitors_girdle", name="Inquisitor's Girdle", like=13077, ilvl=60, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Block (Solo)")
# New: the wave's first Strength libram.
item("strat_libram_of_zeal", name="Libram of Zeal", like=22401, ilvl=60, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit (Solo)")
# Stock, from his 0.02% row; Bind on Pickup from Heroic up.
item("strat_stratholme_militia_shoulderguard", base=18742, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)", overrides=BOP_ABOVE_NORMAL)
# Stock, from world pool 24021 (ruling 62): stats only, the stock flat spell power Equip on one spell folds away.
item("strat_totem_of_the_storm", base=23199, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit (Solo)", overrides=BOP_ABOVE_NORMAL)
item("strat_idol_of_the_moon", base=23197, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery (Solo)", overrides=BOP_ABOVE_NORMAL)

# ---------------------------------------------------------------------------------------------------------------------
# Cannon Master Willey (stock item level 61)

item("strat_willeys_portable_howitzer", base=13380, ammo_type=NO_AMMO, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)")
# Keeps Use: Summon Crimson Cannon (6251).
item("strat_cannonball_runner", base=13382, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Agility (Solo)", secondary="Haste (Solo)")
item("strat_barrage_girdle", base=18721, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit (Solo)")
item("strat_dianas_pearl_necklace", base=22403, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Haste/Versatility", primary_share=0)
item("strat_mantle_of_the_scarlet_crusade", base=22405, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit (Solo)")
item("strat_helm_of_the_new_moon", base=22407, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
# New: the wave's first thrown weapon, a rogue item (ruling 4).
item("strat_scarlet_throwing_axes", name="Scarlet Throwing Axes", like=28972, ilvl=61, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Archivist Galford (stock item level 61)

item("strat_archivist_cape", base=13386, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit (Solo)")
item("strat_foresight_girdle", base=13387, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)")
# New: stats only, one red socket.
item("strat_pyrewatch_coif", name="Pyrewatch Coif", like=12953, ilvl=61, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)
item("strat_tome_of_knowledge", base=13385, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Balnazzar (stock item level 63, two drops per kill)

item("strat_star_of_mystaria", base=12103, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/Mastery", primary_share=0)
# Keeps Shadow Bolt on hit (17483); one red socket.
item("strat_demonshear", base=13348, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Haste (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
item("strat_wyrmtongue_shoulders", base=13358, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)")
item("strat_crown_of_tyranny", base=13359, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)")
item("strat_gift_of_the_elven_magi", base=13360, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit (Solo)")
# Agility tank two-hand mace: Dodge and extra Stamina.
item("strat_hammer_of_the_grand_crusader", base=18717, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge (Solo)", extra_stamina=EXTRA_STAMINA)
# Plate tank: two blue sockets (tank gear, and Block is a blue stat), Block bonus.
item("strat_grand_crusaders_helm", base=18718, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block (Solo)",
     sockets=(Socket.BLUE, Socket.BLUE), socket_bonus=BONUS_BLOCK_4)
item("strat_shroud_of_the_nathrezim", base=18720, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit (Solo)")
# Stock epic, Rare on Normal. Keeps Use: Summon Skeleton (17490).
item("strat_book_of_the_dead", base=13353, quality=RARE, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Spirit (Solo)", secondary="Versatility (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Magistrate Barthilas (stock item level 59-65)

item("strat_royal_tribunal_cloak", base=13376, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Parry (Solo)")
item("strat_death_grips", base=18722, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste (Solo)")
item("strat_peacemaker", base=18725, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit (Solo)")
item("strat_crimson_felt_hat", base=18727, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
# Bear relic: stats only, the stock Equip folds away.
item("strat_idol_of_brutality", base=23198, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Baroness Anastari (stock item level 60)

item("strat_banshee_finger", base=13534, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)")
# Was a resist green: Rare on Normal.
item("strat_windshrieker_pauldrons", base=13538, quality=RARE, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
item("strat_banshees_touch", base=13539, quality=RARE, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Dodge (Solo)")
item("strat_anastari_heirloom", base=18728, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/Haste", primary_share=0)
item("strat_screeching_bow", base=18729, ammo_type=NO_AMMO, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)")
item("strat_shadowy_laced_handwraps", base=18730, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Nerub'enkan (stock item level 61)

# A caster shield.
item("strat_husk_of_nerubenkan", base=13529, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)")
# Was a mail resist green: now leather (the list's "Leather (was mail)"), Leather Tank, Rare on Normal. The display
# stays the stock one.
item("strat_darkspinner_claws", base=13532, quality=RARE, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge (Solo)", extra_stamina=EXTRA_STAMINA,
     subclass=ARMOR_SUBCLASS_LEATHER, Material=MATERIAL_LEATHER)
item("strat_acid_etched_pauldrons", base=13533, quality=RARE, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Mastery (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
item("strat_carapace_spine_crossbow", base=18738, ammo_type=NO_AMMO, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)")
item("strat_thuzadin_sash", base=18740, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Versatility (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Maleki the Pallid (stock item level 62)

item("strat_skull_of_burning_shadows", base=13524, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Versatility (Solo)")
item("strat_darkbind_fingers", base=13525, quality=RARE, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)
item("strat_flamescarred_girdle", base=13526, quality=RARE, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Versatility (Solo)")
item("strat_pale_moon_cloak", base=18734, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste (Solo)")
item("strat_bone_slicing_hatchet", base=18737, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Ramstein the Gorger (stock item level 60)

item("strat_slavedrivers_cane", base=13372, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)")
item("strat_band_of_flesh", base=13373, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/Haste", primary_share=0)
# Was cloth: now leather (the list's "Leather (was cloth)"). The display stays the stock one.
item("strat_soulstealer_mantle", base=13374, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Mastery (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4,
     subclass=ARMOR_SUBCLASS_LEATHER, Material=MATERIAL_LEATHER)
# Strength tank shield; keeps its damage on block (17495).
item("strat_crest_of_retribution", base=13375, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Parry (Solo)")
# Keeps its Use (17668).
item("strat_ramsteins_lightning_bolts", base=13515, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Crit (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Baron Rivendare (stock item level 62-63, two drops per kill)

item("strat_cape_of_the_black_baron", base=13340, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)")
item("strat_dracorian_gauntlets", base=13344, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)")
item("strat_seal_of_rivendare", base=13345, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/Versatility", primary_share=0)
item("strat_scepter_of_the_unholy", base=13349, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery (Solo)")
item("strat_gauntlets_of_deftness", base=22410, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)")
item("strat_helm_of_the_executioner", base=22411, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED, Socket.YELLOW), socket_bonus=BONUS_CRIT_4)
# Keeps Skullforge Brand on hit (17484).
item("strat_skullforge_reaver", base=13361, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Versatility (Solo)")
item("strat_bonescraper", base=13368, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)")
# Stock epic, Rare on Normal. Keeps its Equip (speed and regeneration, 17625); two sockets, the second yellow (Mastery).
item("strat_runeblade_of_baron_rivendare", base=13505, quality=RARE, ladder=VANILLA_DUNGEON, keep_spells=True,
     primary="Strength (Solo)", secondary="Mastery (Solo)",
     sockets=(Socket.RED, Socket.YELLOW), socket_bonus=BONUS_HASTE_4)

# ---------------------------------------------------------------------------------------------------------------------
# Balnazzar, the Grand Lie: hard mode (heroic hard mode 71, then 81 / 91 / 101). New items, the ladder sets every tier.

# Equip: a chance on damage to loose a Carrion Swarm (a Shadow cone, scaled by item level). Ring: secondaries only,
# one red socket.
item("strat_carrion_signet", name="Carrion Signet", like=18314, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Crit/Proc", primary_share=0,
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(carrion_signet_205660, scale="budget"),))
# Use (2 min): put a non-boss enemy to sleep for up to 20 sec. Full stat budget (designer: the Use adds no throughput).
item("strat_dust_of_the_nathrezim", name="Dust of the Nathrezim", like=1973, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Haste/Versatility", primary_share=0, budget_mult=1.0,
     spells=(use_spell(dust_of_the_nathrezim_205662),))
# Equip: direct heals may also hurt the enemy nearest the healed target for a share of the heal. One red socket.
item("strat_two_faced_tome", name="Two-Faced Tome", like=18536, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Spirit (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(two_faced_tome_205663),))

# ---------------------------------------------------------------------------------------------------------------------
# Baron Rivendare, the Ultimatum: hard mode.

# Equip: wards a group member who falls below 20% health (an absorb scaled by item level), once every 60 sec. One red
# socket. Cooldown Haste and Versatility: shape 74 "CDH/Versatility" (wave 1 integration, pending
# itemization_templates_v2 SQL).
item("strat_ysidas_locket", name="Ysida's Locket", like=18023, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="CDH/Versatility", primary_share=0,
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(ysidas_locket_205665, scale="budget"),))
# Equip: melee hits Condemn the target (+1% damage taken from you per stack, up to 5). One red socket.
item("strat_blade_of_the_condemned", name="Blade of the Condemned", like=14576, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Strength (Solo)", secondary="Haste (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(blade_of_the_condemned_205668),))
# Use (2 min): ride a spectral Deathcharger for 6 sec, trampling every enemy passed (Shadow damage scaled by item
# level). The Deathcharger's Reins icon.
item("strat_deathchargers_spur", name="Deathcharger's Spur", like=11815, displayid=24011, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary=None, secondary="Crit/Mastery", primary_share=0,
     spells=(use_spell(deathchargers_spur_205670, scale="budget"),))
