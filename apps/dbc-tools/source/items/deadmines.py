"""
The Deadmines loot (item variants plan v2 section 7, stage IV5): the 29 approved list items and the 3 Edwin VanCleef
hard mode items (docs/dungeons/deadmines-rework.md ## Loot, copied in docs/dungeons/dungeon-loot-vanilla.md).

Normal drops Rare at the item's stock level (19-25), Heroic is 66 Epic with the Heroic flag, then the three empowered
steps (ladders.py). Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only
the primary and secondary are listed. 22 of the items are stock entries (`base=`: the stock id is the Normal tier,
only the higher tiers are minted) and 7 are new (every tier minted, the look copied from a stock `like=` entry and the
level from the boss's lowest stock item level).

**Sockets** (docs/dungeons/boss-rework-systems.md, approved 2026-11-02; the Deadmines picks are plan section 7.1): one
socketed standalone piece per boss, 2 sockets on a two-hander. The first socket is red on damage and healing gear and
blue on tank gear; a second socket takes the color of the item's first secondary. The stat to color map is
docs/Systems.md "Sockets and gems":
    yellow (throughput)   Crit, Haste, Mastery, Versatility
    blue (utility)        Proc Chance, Cooldown Haste, MP5, Block, Dodge, Parry
    red (primary)         Strength, Agility, Intellect, Spirit
A socket bonus is a secondary rating, never Stamina or a primary. Sockets are the same on every tier.

**Socket bonus enchants.** The enchants below are stock SpellItemEnchantment rows (client DBC; all +4 at this level
range): 2874 +4 Critical Strike Rating, 3267 +4 Haste Rating, 2871 +4 Dodge Rating, 2972 +4 Block Rating. No
enchant exists for Mastery, Versatility, Cooldown Haste or Proc Chance (the custom stats have no
SpellItemEnchantment rows yet), so Rockslicer (Versatility) and Impaling Harpoon (Mastery) take a stock throughput
rating instead (Crit and Haste). The bonus is one enchant per item, so it does not scale with the tier.

**Hard mode items** (VanCleef, ladder `vanilla_hard_mode`, 71 / 81 / 91 / 101) are declared without their spells:
the three effects are stage IV6 (spells from the `items` reservation 205400-205599 in source/ids.yaml). Each carries
`budget_mult` 0.7 for the effect it will have (itemization-changes.md section 3). Only the Signet is socketed (one
red, plan section 7.1); trinkets never are.
"""

from lib.dsl.items import Socket, item

from .ladders import VANILLA_DUNGEON, VANILLA_HARD_MODE

# Socket bonus enchants (stock SpellItemEnchantment ids, see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_DODGE_4 = 2871
BONUS_BLOCK_4 = 2972

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does

# ---------------------------------------------------------------------------------------------------------------------
# Rhahk'Zor (stock item level 20-21)

item("dm_rhahkzors_hammer", base=5187, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit (Solo)")
# Strength / Versatility: the second socket is yellow (Versatility is throughput).
item("dm_rockslicer", base=872, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Versatility (Solo)",
     sockets=(Socket.RED, Socket.YELLOW), socket_bonus=BONUS_CRIT_4)
item("dm_doormans_girdle", name="Doorman's Girdle", like=9288, ilvl=20, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Parry (Solo)")
item("dm_evokers_boots", name="Evoker's Boots", like=3076, ilvl=20, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Miner Johnson (stock item level 19-20)

item("dm_miners_cape", base=5444, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)")
# The dungeon's tank item: one blue socket, Block bonus.
item("dm_gold_plated_buckler", base=5443, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block (Solo)",
     sockets=(Socket.BLUE,), socket_bonus=BONUS_BLOCK_4)

# ---------------------------------------------------------------------------------------------------------------------
# Sneed and Sneed's Shredder, one pool (stock item level 21-23)

item("dm_buzzer_blade", base=2169, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)")
item("dm_buzz_saw", base=1937, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
# The designer removed Spell Power from the Gloves (2026-11-02): Intellect and Cooldown Haste only.
item("dm_gold_flecked_gloves", base=5195, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="CDH (Solo)")
item("dm_taskmaster_axe", base=5194, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit (Solo)")
item("dm_insulated_tazer_bracers", name="Insulated Tazer Bracers", like=2868, ilvl=21, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Gilnid (stock item level 21-22)

# Leather Tank: Agility, Dodge and extra Stamina (a quarter more Stamina than the baseline, paid from the item's own
# budget), one blue socket with a Dodge bonus.
item("dm_smelting_pants", base=5199, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge (Solo)", extra_stamina=0.25,
     sockets=(Socket.BLUE,), socket_bonus=BONUS_DODGE_4)
# A ring carries secondaries only: Cooldown Haste and Crit evenly, no primary (share 0).
item("dm_lavishly_jeweled_ring", base=1156, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/CDH", primary_share=0)
item("dm_forge_scarred_sabatons", name="Forge-scarred Sabatons", like=13068, ilvl=21, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Crit (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Mr. Smite (stock item level 22-23)

item("dm_smites_reaver", base=5196, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Versatility (Solo)")
# Keep: the live row (Agility, share 10000), only the tiers are new.
item("dm_thiefs_blade", base=5192, itemization="live", ladder=VANILLA_DUNGEON)
item("dm_smites_mighty_hammer", base=7230, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Parry (Solo)")
item("dm_first_mates_pauldrons", name="First Mate's Pauldrons", like=9292, ilvl=22, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)

# ---------------------------------------------------------------------------------------------------------------------
# Cookie (stock item level 21-22)

# Spirit / Haste healer mace, one red socket.
item("dm_cookies_tenderizer", base=5197, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
item("dm_cookies_stirring_rod", base=5198, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit (Solo)")
item("dm_rubbery_helmet", name="Rubbery Helmet", like=9420, ilvl=21, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Mastery (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Captain Greenskin (stock item level 22-23)

# Keep: the live row (Intellect / Spirit / Spell Power, Intellect lead), only the tiers are new.
item("dm_emberstone_staff", base=5201, itemization="live", ladder=VANILLA_DUNGEON)
# Defias Leather set 161: Normal keeps the stock itemset, every higher tier clears it (a level 20 set bonus at item
# level 66 and up would only cost budget). The stock +AP equip spell 9330 folds into the budget (absorbed).
item("dm_blackened_defias_belt", base=10403, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)",
     overrides={name: {"itemset": 0} for name in ("heroic", "empowered_1", "empowered_2", "empowered_3")})
# Agility / Mastery polearm: the second socket is yellow (Mastery is throughput).
item("dm_impaling_harpoon", base=5200, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)",
     sockets=(Socket.RED, Socket.YELLOW), socket_bonus=BONUS_HASTE_4)
item("dm_harpooneers_coif", name="Harpooneer's Coif", like=6971, ilvl=22, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Edwin VanCleef (stock item level 24-25)

# Keep: the live row (Agility, share 10000), only the tiers are new.
item("dm_cape_of_the_brotherhood", base=5193, itemization="live", ladder=VANILLA_DUNGEON)
item("dm_corsairs_overshirt", base=5202, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Versatility (Solo)")
# The stock +AP equip spell 9141 folds into the budget (absorbed).
item("dm_cruel_barb", base=5191, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)
# Defias Leather set 161, as the Belt.
item("dm_blackened_defias_armor", base=10399, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Proc (Solo)",
     overrides={name: {"itemset": 0} for name in ("heroic", "empowered_1", "empowered_2", "empowered_3")})

# ---------------------------------------------------------------------------------------------------------------------
# Edwin VanCleef, hard mode (heroic hard mode 71, then 81 / 91 / 101). New items, no stock level: the ladder sets
# every tier. TODO(IV6): add `spells=(use_spell(...))` / `equip_spell(...)` once the three effect spells exist (ids
# from the `items` reservation 205400-205599); `budget_mult` 0.7 is already set for them. Until then the items have
# no effect line.

# Use: lob a lit keg at the target's position, a 6 yd Fire explosion 2 sec later. TODO(IV6): use_spell(keg).
item("dm_powder_keg_fuse", name="Powder Keg Fuse", like=10587, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Crit (Solo)", primary_share=0, budget_mult=0.7)
# Equip: melee hits have a chance to call a Defias Blackguard, who strikes once. Ring: secondaries only. One red
# socket (plan section 7.1), Haste bonus. TODO(IV6): equip_spell(signet).
item("dm_blackguards_signet", name="Blackguard's Signet", like=1076, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Haste/Proc", primary_share=0, budget_mult=0.7,
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
# Use (90 sec): the next direct heal leaves a 10 sec zone, -10% damage taken. TODO(IV6): use_spell(lantern).
item("dm_lantern_of_the_roaring_flame", name="Lantern of the Roaring Flame", like=3791, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Spirit (Solo)", secondary="Versatility (Solo)", budget_mult=0.7)
