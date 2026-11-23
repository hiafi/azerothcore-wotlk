"""
The Scarlet Monastery boss list items (wave 3 dungeon items, after the Deadmines and Blackrock precedents): the 64
approved list items of the fourteen encounters (docs/dungeons/scarlet-monastery-rework.md ## Loot "Boss lists",
approved 2026-11-19, ruling 58; copied in docs/dungeons/dungeon-loot-vanilla.md "### Scarlet Monastery"). Out of scope
here: the 12 hard mode items (scarlet_monastery_hard_mode.py), the Zealot's pieces, tokens and vendors (zealot_set.py),
Heart of Zeal and the other quest items, the Scarlet Key and the stock Scarlet set pieces that stay trash drops; no
loot tables (map 189 has no heroic creature bodies yet: the dungeon build's loot stages wire them).

The Scarlet Monastery is a leveling dungeon (levels 34-44), so Normal drops Rare at the boss's item level (handoff
section 1.3; required level = item level - 5), Heroic is 66 Epic with the Heroic flag, then the three empowered steps
(ladders.py `VANILLA_DUNGEON`). Bosses' item levels: Vishas 34, Ironspine 35, Azshir and the Fallen Champion 35, Thalnos
38, Loksey 34, Kell 37, Hollis Grey 37, Doan 38, Crell 41, Halden 41, Herod 42, Thorne 43, the Last Stand 44,
Whitemane 44. A stock item keeps its stock level and required level (`base=`: the stock id is the Normal tier); a stock
item moved to another boss and every new item takes that boss's level. The three moved ones are Branded Leather Bracers
(41, to Vishas at 34) and Dusty Mail Boots (41, to Kell at 37); Deadman's Hand (stock Epic) is lowered to Rare on
Normal. New items copy a stock look (`like=`, look only) and are Bind on Pickup.

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and the
secondaries are listed (the doc's order of secondaries does not matter to an Even shape). Rings, necks, the
primary-less trinket and Ironspine's Eye (a ring now) carry secondaries only (`primary=None`, share 0). Dog Training
Gloves, the dungeon's Leather Tank piece, take a quarter more Stamina (`extra_stamina=0.25`, the Deadmines Smelting
Pants pick). Relics: Totem of Righteous Fire (shaman), Idol of the Harvest (druid), Libram of the Last Stand (paladin);
they are stats only, like the earlier dungeons' relics.

**Shapes this list needs that do not exist yet** (the integration adds them in the one pending itemization file; each
models an existing shape, name order as below, stat types in parentheses):
  - "Block/Parry/Versatility"   secondary, Even trio (15, 14, 23), requires a Strength primary (as Block/Crit 61):
                                Aegis of the Scarlet Commander
  - "Block/Mastery/Versatility" secondary, Even trio (15, 22, 23), requires a Strength primary: Captain's Legguards
  - "Dodge/Versatility (Any)"   secondary, Even pair (13, 23), no rule (the rule-free copy of 87, like 89
                                Dodge/Mastery (Any)): Deadman's Hand, which has no primary

**Kept stock effects**: Ravager's Chance on hit (Bladestorm 9632, `keep_spells=True`: its only slot) and Deadman's
Hand's Equip (27867, `keep_spells=True`: its only slot). The Dog Whistle's Use (9515) is named with `spells=` instead:
the stock row carries `spellcharges -3` (a consumable that is used up) and the trinket must not be, so the slot is
rewritten with a 2 minute cooldown (designer ruling A3, 2026-11-20; stock 10 minutes), the stock 1 minute category
cooldown (24) and no charges. Every other stock
spell slot (Loksey's Training Stick Attack Power 14049, Gauntlets of Divinity Attack Power 15807, Branded Leather
Bracers' flat slot) folds into the budget (`absorbed_spell_slots`), as the list's stats-only lines ask. The stock
spells are the same on every tier (they are not declared in source/items, so they cannot scale); each effect item pays
0.7 of the budget (itemization-changes.md section 3), the default for an item with an effect.

**Type and slot changes**: Gauntlets of Divinity mail -> plate (`subclass=4`, `Material=6`, display unchanged, the
Deathdealer Breastplate precedent: the dungeon's Plate Intellect piece). The Dog Whistle becomes a trinket (class 4,
subclass 0, InventoryType 12, Material -1; its display stays). Deadman's Hand, a ring in the stock data, becomes the
trinket the doc lists (InventoryType 12 on every tier; review M1, designer 2026-11-20). Ironspine's Eye is already a
ring.

**Sockets.** The doc names no per-item pick, so every pick is a designer question (STAGE-SM-LIST report). The shared
rule (boss-rework-systems.md section 2; deadmines.py): about one standalone armor piece or weapon per boss carries 1,
a two-hander 2, trinkets never, Normal tiers none (ladders.py). The first socket is red on damage and healing gear and
blue on tank gear; a second takes the color of the item's first secondary (docs/Systems.md "Sockets and gems"):
Crit, Haste, Mastery and Versatility are yellow. The socket bonus is a stock +4 rating (2874 Crit, 3267 Haste, 2972
Block): no enchant exists for Mastery, Versatility, Cooldown Haste or Proc Chance, so those items take Haste (Mastery,
Cooldown Haste) or Crit (Versatility, Proc Chance), by the item's first secondary.

Stock resistances and random properties: none of the stock items on this list carries one, so nothing is cleared.
"""

from lib.dsl.items import Quality, Socket, item, use_spell

from .ladders import VANILLA_DUNGEON

# Socket bonus enchants (stock SpellItemEnchantment ids, +4 each; see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_BLOCK_4 = 2972

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does
RARE = Quality.RARE
EXTRA_STAMINA = 0.25  # "extra Stamina" on a tank piece: a quarter more than the tier's baseline

# Bows and crossbows need no ammo (source/world/ranged_weapons.py, hunter-rework Q3). An item() declaration owns its
# entry, so it sets the column itself and the minted tiers copy it.
NO_AMMO = 0

ARMOR_SUBCLASS_PLATE = 4
MATERIAL_PLATE = 6
ITEM_CLASS_ARMOR = 4
INVTYPE_TRINKET = 12
MATERIAL_NONE = -1

# The Dog Whistle's stock Use (Summon Tracking Hound; stock cooldown 10 minutes, category 24 for 1 minute). The trinket
# takes 2 minutes (designer ruling A3, 2026-11-20).
SPELL_DOG_WHISTLE = 9515
DOG_WHISTLE_COOLDOWN_MS = 120000
DOG_WHISTLE_CATEGORY = 24
DOG_WHISTLE_CATEGORY_COOLDOWN_MS = 60000

# Weapon-tier role cells (blackrock_depths.py, the review's S2): a caster main-hand or a bow whose stock level is below
# 60 would take the 1-59 cell on its Normal tier and the 60-100 cell from Heroic up, a 2.4x step (the ladder check
# refuses over 1.5x). The 60-100 cell is declared on every tier instead, so the Normal tier is that cell at its own
# (lower) item level and the step is the budget curve's alone.
# physical InventoryType 13 ilvl 60-100: caster weapons take the physical budget (level60-stat-curve 1.8)
CASTER_MAIN_HAND_MULT = 0.445
BOW_MULT = 0.405                # physical InventoryType 15 ilvl 60-100

R, Y, B = Socket.RED, Socket.YELLOW, Socket.BLUE

# ---------------------------------------------------------------------------------------------------------------------
# Interrogator Vishas (item level 34)

item("sm_bloody_brass_knuckles", base=7683, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)")
item("sm_torturing_poker", base=7682, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)")
# Moved from Fairbanks (stock 41): level 34 here, required level 29.
item("sm_branded_leather_bracers", base=19508, ilvl=34, required_level=29, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Versatility")
item("sm_confessors_gloves", name="Confessor's Gloves", like=7433, ilvl=34, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Versatility",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("sm_interrogators_thumbscrews", name="Interrogator's Thumbscrews", like=3739, ilvl=34, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary=None, secondary="Crit/Proc", primary_share=0)

# ---------------------------------------------------------------------------------------------------------------------
# Ironspine (item level 35)

# A ring since the stock row: secondaries only (the stock row has Agility and Strength on it).
item("sm_ironspines_eye", base=7686, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Haste/Mastery", primary_share=0)
item("sm_ironspines_fist", base=7687, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Parry (Solo)")
item("sm_bonecrawler_boots", name="Bonecrawler Boots", like=9387, ilvl=35, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Mastery",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("sm_bone_link_legguards", name="Bone-link Legguards", like=7132, ilvl=35, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Versatility")
item("sm_cloak_of_knitted_bone", name="Cloak of Knitted Bone", like=4462, ilvl=35, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste/Mastery")

# ---------------------------------------------------------------------------------------------------------------------
# Azshir the Sleepless and the Fallen Champion, one pool (item level 35)

item("sm_necrotic_wand", base=7708, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery (Solo)")
item("sm_blighted_leggings", base=7709, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Mastery/Versatility")
item("sm_ghostshard_talisman", base=7731, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Haste/Versatility", primary_share=0)
# Two-hander: two sockets, red then yellow (Crit is throughput).
item("sm_morbid_dawn", base=7689, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Mastery",
     sockets=(R, Y), socket_bonus=BONUS_CRIT_4)
item("sm_ebon_vise", base=7690, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Mastery")
# Plate Tank gauntlets (Strength, Parry, Versatility).
item("sm_vigil_keepers_gauntlets", name="Vigil-keeper's Gauntlets", like=14826, ilvl=35, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Parry/Versatility (Any)")

# ---------------------------------------------------------------------------------------------------------------------
# Bloodmage Thalnos (item level 38)

item("sm_orb_of_the_forgotten_seer", base=7685, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Proc")
item("sm_bloodmages_handwraps", name="Bloodmage's Handwraps", like=14231, ilvl=38, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste/Proc",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("sm_bloodstained_cloak", name="Bloodstained Cloak", like=7056, ilvl=38, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Versatility")
item("sm_bloodletting_kris", name="Bloodletting Kris", like=21802, ilvl=38, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste (Solo)", budget_mult=CASTER_MAIN_HAND_MULT)
item("sm_sanguine_signet", name="Sanguine Signet", like=13093, ilvl=38, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Versatility/Proc", primary_share=0)

# ---------------------------------------------------------------------------------------------------------------------
# Houndmaster Loksey (item level 34)

# Leather Tank gloves: Agility, Dodge and a quarter more Stamina.
item("sm_dog_training_gloves", base=7756, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge (Solo)", extra_stamina=EXTRA_STAMINA)
# The stock Equip (Attack Power) folds into the budget.
item("sm_loksey_training_stick", base=7710, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery/Versatility")
# Now a trinket (the stock row is a consumable) that keeps its Use. The stock row is level 30 / required 25.
item("sm_dog_whistle", base=3456, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Haste",
     spells=(use_spell(SPELL_DOG_WHISTLE, cooldown=DOG_WHISTLE_COOLDOWN_MS, category=DOG_WHISTLE_CATEGORY,
                       category_cooldown=DOG_WHISTLE_CATEGORY_COOLDOWN_MS),),
     **{"class": ITEM_CLASS_ARMOR}, subclass=0, InventoryType=INVTYPE_TRINKET, Material=MATERIAL_NONE)
item("sm_kennelmasters_crossbow", name="Kennelmaster's Crossbow", like=13037, ilvl=34, bonding=BOP,
     ammo_type=NO_AMMO, ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit (Solo)")
item("sm_leash_scarred_gauntlets", name="Leash-scarred Gauntlets", like=7421, ilvl=34, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)

# ---------------------------------------------------------------------------------------------------------------------
# Ambrose Kell (item level 37)

# Moved from Fairbanks (stock 41): level 37 here, required level 32. Red socket, Crit bonus.
item("sm_dusty_mail_boots", base=19509, ilvl=37, required_level=32, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Versatility",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("sm_antiquarians_signet", name="Antiquarian's Signet", like=24118, ilvl=37, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary=None, secondary="Mastery/Versatility", primary_share=0)
item("sm_kirin_tor_spellblade", name="Kirin Tor Spellblade", like=18396, ilvl=37, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Mastery (Solo)",
     budget_mult=CASTER_MAIN_HAND_MULT)
item("sm_necromancers_skull", name="Necromancer's Skull", like=10770, ilvl=37, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Mastery/Proc")

# ---------------------------------------------------------------------------------------------------------------------
# Lector Hollis Grey (item level 37)

item("sm_index_keepers_bindings", name="Index-keeper's Bindings", like=14226, ilvl=37, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Mastery")
item("sm_lectors_sash", name="Lector's Sash", like=3747, ilvl=37, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Mastery/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("sm_forbidden_tome", name="Forbidden Tome", like=33266, ilvl=37, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Versatility")
item("sm_burning_page", name="Burning Page", like=2802, ilvl=37, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Haste")

# ---------------------------------------------------------------------------------------------------------------------
# Arcanist Doan (item level 38; the stock items keep their own level 36-39)

# Keep: the stock entry with the doc's stats (the live row is Intellect, MP5 and Mastery). Two-hander: two sockets,
# red then yellow (Crit).
item("sm_illusionary_rod", base=7713, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit (Solo)",
     sockets=(R, Y), socket_bonus=BONUS_CRIT_4)
item("sm_hypnotic_blade", base=7714, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)", budget_mult=CASTER_MAIN_HAND_MULT)
# Stock Epic: Rare on Normal. The stock row is a ring; the doc lists a trinket (review M1, designer 2026-11-20), so
# every tier is InventoryType 12. Dodge and Versatility and no primary; keeps its Equip (Freeze, 27867: a chance to freeze
# the attacker).
item("sm_deadmans_hand", base=34227, quality=RARE, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Dodge/Versatility (Any)", primary_share=0, InventoryType=INVTYPE_TRINKET)
item("sm_arcanists_cord", name="Arcanist's Cord", like=14217, ilvl=38, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Versatility")
item("sm_totem_of_righteous_fire", name="Totem of Righteous Fire", like=22395, ilvl=38, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Haste")

# ---------------------------------------------------------------------------------------------------------------------
# Forgemaster Gideon Crell (item level 41)

item("sm_proving_blade", name="Proving Blade", like=864, ilvl=41, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Mastery (Solo)")
item("sm_red_hot_gauntlets", name="Red-Hot Gauntlets", like=14897, ilvl=41, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Haste")
# The dungeon's tank waist: one blue socket (tank gear), Block bonus.
item("sm_tempered_girdle", name="Tempered Girdle", like=8140, ilvl=41, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block/Versatility",
     sockets=(B,), socket_bonus=BONUS_BLOCK_4)
# A caster shield (Intellect, Haste, Mastery).
item("sm_forge_tempered_buckler", name="Forge-tempered Buckler", like=4067, ilvl=41, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste/Mastery")

# ---------------------------------------------------------------------------------------------------------------------
# Drillmaster Corin Halden (item level 41)

item("sm_drillmasters_girdle", name="Drillmaster's Girdle", like=9968, ilvl=41, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("sm_drillmasters_longbow", name="Drillmaster's Longbow", like=4087, ilvl=41, bonding=BOP, ammo_type=NO_AMMO,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste (Solo)", budget_mult=BOW_MULT)
item("sm_drillfield_cape", name="Drillfield Cape", like=7460, ilvl=41, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Mastery")
item("sm_medal_of_the_proving_ground", name="Medal of the Proving Ground", like=18438, ilvl=41, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Crit/Versatility")

# ---------------------------------------------------------------------------------------------------------------------
# Herod (item level 42)

# Keeps Bladestorm on hit (9632).
item("sm_ravager", base=7717, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit (Solo)")
item("sm_whirlwind_legplates", name="Whirlwind Legplates", like=14945, ilvl=42, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste/Mastery",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("sm_blade_dancers_treads", name="Blade-dancer's Treads", like=15362, ilvl=42, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste/Proc")
item("sm_pendant_of_the_scarlet_champion", name="Pendant of the Scarlet Champion", like=5005, ilvl=42,
     bonding=BOP, ladder=VANILLA_DUNGEON, primary=None, secondary="Crit/Mastery", primary_share=0)

# ---------------------------------------------------------------------------------------------------------------------
# Brother Aldous Thorne (item level 43)

item("sm_furrowed_boots", name="Furrowed Boots", like=2276, ilvl=43, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Versatility")
item("sm_waterbearers_girdle", name="Waterbearer's Girdle", like=11229, ilvl=43, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste/Mastery",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("sm_idol_of_the_harvest", name="Idol of the Harvest", like=22398, ilvl=43, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Haste/Mastery")
item("sm_pruning_scythe", name="Pruning Scythe", like=13054, ilvl=43, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Haste")

# ---------------------------------------------------------------------------------------------------------------------
# The Last Stand, Mograine (item level 44)

# Tank shield: Strength, Block, Parry and Versatility (a new three-secondary shape).
item("sm_aegis_of_the_scarlet_commander", base=7726, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block/Parry/Versatility")
item("sm_mograines_might", base=7723, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste/Versatility")
# Mail -> plate (the stock Equip, Attack Power, folds into the budget).
item("sm_gauntlets_of_divinity", base=7724, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Haste/Versatility",
     subclass=ARMOR_SUBCLASS_PLATE, Material=MATERIAL_PLATE)
# Plate Tank legs: one blue socket, Block bonus.
item("sm_captains_legguards", name="Captain's Legguards", like=9291, ilvl=44, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block/Mastery/Versatility",
     sockets=(B,), socket_bonus=BONUS_BLOCK_4)
item("sm_libram_of_the_last_stand", name="Libram of the Last Stand", like=22401, ilvl=44, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Parry/Versatility (Any)")

# ---------------------------------------------------------------------------------------------------------------------
# High Inquisitor Whitemane, with Mograine risen (item level 44)

item("sm_triune_amulet", base=7722, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/Haste", primary_share=0)
item("sm_hand_of_righteousness", base=7721, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit (Solo)", budget_mult=CASTER_MAIN_HAND_MULT)
item("sm_cinch_of_the_faithful", name="Cinch of the Faithful", like=9853, ilvl=44, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Haste/Mastery",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("sm_whitemanes_vigil_candle", name="Whitemane's Vigil Candle", like=21119, ilvl=44, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Haste/Mastery/Versatility")
