"""
The Zul'Farrak boss list items (wave 5 dungeon items, after the Deadmines, Shadowfang Keep, Scarlet Monastery and
Ragefire Chasm precedents): the 62 approved list items of the seven encounters and the rares (docs/dungeons/
zul-farrak-rework.md ## Loot "Loot list", approved 2026-11-24, ruling 47; copied in docs/dungeons/
dungeon-loot-vanilla.md "### Zul'Farrak"). Out of scope here: the 3 Gahz'rilla hard mode items
(zul_farrak_hard_mode.py), the quest items (Troll Temper, Gahz'rilla's Electrified Scale, the OOX beacon) and the loot
tables (the dungeon build's L-1 wires them).

Zul'Farrak is a leveling dungeon (levels 44-50), so Normal drops Rare at the boss's item level (handoff section 1.2;
required level = item level - 5), Heroic is 66 Epic with the Heroic flag, then the three empowered steps (ladders.py
`VANILLA_DUNGEON`). Bosses' item levels: Theka 46, Antu'sul 48, Zum'rah 47, the Pyramid (Sezz'ziz) 49, Bly's crew 49,
Chief Ukorz Sandscalp and Ruuzlu 50, Hydromancer Velratha and Gahz'rilla 50; the rares keep each stock level. A stock
item keeps its stock level and required level (`base=`: the stock id is the Normal tier); a stock item moved to
another boss takes that boss's level (four moves change it: Gutwrencher 47 -> 46, Brainlash 48 -> 47, Troll Protector
and Eyegouger 48 -> 49; the other moved ones already sit on the level of their new boss, or on the rares, which keep
theirs). Items that drop from two bosses in stock (Runed Ring 862 on Antu'sul and Ukorz, Spellshock Leggings 9484 on
the shared list) keep their stock level (50 / 45). Sul'thraze the Lasher (9372) is a join of the two sword halves, not
a drop: its Normal tier keeps its stock Epic quality and item level 55 / required 50 (handoff section 1.4). New items
copy a stock look (`like=`, look only) and are Bind on Pickup. The 11 stock Bind on Equip entries (the ones the
stock shared rare list dropped, and Runed Ring) keep that on Normal and are Bind on Pickup from Heroic up
(`BOP_ABOVE_NORMAL`).

Bosses (counts): Theka 8, Antu'sul 7, Zum'rah 7, the Pyramid 8, Bly's crew 9, Ukorz 9, Gahz'rilla 9, the rares 4, and
the join Sul'thraze 1 (62 in all; 31 altered stock entries, 31 new items). The rares' pool and Bly's crew drop from one
list each.

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and the
secondaries are listed (the doc's order of secondaries does not matter to an Even shape). Rings and the neck (Runed
Ring, Brainlash, Coil of the Electrified Scale, Lifeblood Amulet) carry secondaries only (`primary=None`, share 0).
Stonegaze Girdle, the dungeon's Leather Tank piece, takes a quarter more Stamina (`extra_stamina=0.25`, the Deadmines
Smelting Pants pick). Relics are told apart by name: Libram of the Persecuted (paladin Protection, Strength) and Libram
of the Sacred Pool (Holy, Intellect); Totem of the Stone Servant (Elemental, Intellect) and Totem of the Blood Altar
(Enhancement, Agility); Idol of the Restless Grave (Balance, Intellect) and Idol of the Lycan (feral, Agility). They are
stats only, like the earlier dungeons' relics.

**Shape this list needs that does not exist yet** (the integration adds it in the one pending itemization file; it
models Dodge/Parry/Block 64 with Mastery in the third place, an Even trio, requires a Strength primary like 64):
  - "Dodge/Parry/Mastery"   secondary, Even trio (13, 14, 22), requires a Strength primary:
                            Sergeant's Dented Breastplate
Every other shape exists (Crit/Haste/Versatility 44, Crit/Mastery/Versatility 45, Dodge/Versatility 87, Dodge/Mastery
59, Block/Mastery 93, Mastery/Proc 75, Crit/Proc 39, Parry/Versatility (Any) 83 and the Even pairs and Solo shapes).

**Kept stock effects** (`keep_spells=True`, the Ravager precedent; each is the stock row's only spell slot;
Jang'thraze declares its two slots instead). The stock spells are the same on every tier (a stock spell cannot scale)
and each effect item pays 0.7 of the budget (itemization-changes.md section 3):
  - The Hand of Antu'sul 9639: Chance on hit, Thunder Clap 13532 (ppm 1.1)
  - Gutwrencher 5616: Chance on hit, Rend 16406 (ppm 1.5)
  - Bloodletter Scalpel 9511: Chance on hit, Wound 13486 (ppm 1.5)
  - Gahz'rilla Fang 9467: Chance on hit, Static Electricity 3742 (ppm 1)
  - Diabolic Skiver 9475: Chance on hit, Fatal Wound 18206 (ppm 1)
  - Ripsaw 9478: Chance on hit, Wound 16405 (ppm 1)
  - The Chief's Enforcer 9477: Chance on hit, Stun 56 (3 sec; ppm 0 and ProcChance 101, so the weapon speed chance)
  - Jang'thraze the Protector 11086 (`spells=`): slot 1 Use, the join Call of Sul'thraze 213808 (charges -1, so the item
    is used up; the stock slot held 11654), slot 2 Chance on hit, the 54 point absorb Jang'thraze 11657 (ppm 1.2, the
    stock slot)
  - Sul'thraze the Lasher 9372: Chance on hit, Sul'thraze 11658 (ppm 2.2)
Every stock stat spell slot folds into the budget (`absorbed_spell_slots`, the default): Embrace of the Lycan's and Vice
Grips' Attack Power (15807, 9142) and Gahz'rilla Scale Armor's Increased Mana Regen (21631, the dead MP5). None of
the other stock rows carries a spell slot.

**Sul'thraze join** (user ruling 2026-11-25, option A: tier matched, mixed tiers refused). Stock: Jang'thraze's Use
(Call of Sul'thraze 11654) is a Create Item spell (effect 24, item 9372, reagent 9379 Sang'thraze the Deflector x1, cast
time 10 sec); the Use slot's charge count -1 uses Jang'thraze up. It names the Normal ids, so here every tier of
Jang'thraze carries 213808 instead (zul_farrak_effects.py: the same look and cast, no reagent) and
spell_zf_call_of_sulthraze (modules/mod-dungeon-bosses src/ZulFarrak/sulthraze_join.cpp) joins it with a Sang'thraze of
the same tier into that tier's Sul'thraze: the Normal halves make the Normal one, the Heroic halves the Heroic one, up
to the last tier. Mixed tiers are refused with a message and nothing is used up. The script reads the tiers from
`item_budget_variant`, so it needs no minted id. Stock 11654 is unchanged (only 9380, a second
stock Jang'thraze entry that nothing hands out, still casts it).

**Moves and stat changes.** Every doc stat has a point on every tier (tested on the materialized rows). The stock rows
lose their dead stats (Spell Power, Attack Power, Hit, MP5, Brainlash's negative Spirit and Strength lines: the shape
replaces them), Runed Ring's and Vice Grips' random suffix (`RandomProperty=0`: 3253 and 783) and Flaming Incinerator's
8 fire resistance (`fire_res=0`; the wand keeps its fire damage type). Troll Protector, Eyegouger, Gutwrencher and
Brainlash get `ilvl=` and `required_level=` for their new boss. Three stock entries are Unique (`maxcount` 1: Zum'rah's
Vexing Cane 18082, Jumanza Grips 18083 and Sul'thraze 9372): every minted tier copies the column, which is one per
entry, so it limits one copy of each tier, not of the item.

**Caster main-hand cell.** Hydromancer's Scepter (Spirit, a caster one-hand mace) declares the 60-100 physical role
cell (0.445) on every tier, like the earlier dungeons' caster main-hands (blackrock_depths.py, scarlet_monastery.py,
ragefire_chasm.py; the Blackrock gear review's S2): its level is below 60, so without it the Normal tier would read the
1-59 caster cell and the Heroic tier the 60-100 one, two different curves for one item (designer question 4). The
two-handers keep their own caster cell, as Illusionary Rod does.

**Sockets.** The doc names no per-item pick, so every pick is a designer question (STAGE-ZG-LIST report). The shared
rule (boss-rework-systems.md section 2; deadmines.py): about one standalone armor piece or weapon per boss carries 1,
a two-hander 2 (none here: see designer question 1), trinkets and jewelry never, Normal tiers none (ladders.py). The
first socket is red on damage and healing gear and blue on tank gear; a second takes the color of the item's first
secondary (docs/Systems.md "Sockets and gems"): Crit, Haste, Mastery and Versatility are yellow. The socket bonus is a
stock +4 rating (2874 Crit, 3267 Haste, 3359 Parry): no enchant exists for Mastery, Versatility, Cooldown Haste or Proc
Chance, so a first secondary of those takes Haste or Crit. Picks, one per boss (the rares' pool holds none: it is not a
boss):

    Theka                  Carapace of the Martyr (Plate Strength chest)       red          +4 Crit
    Antu'sul               Sul'lithuz Scale Coif (Mail Agility head)           red          +4 Crit
    Zum'rah                Soulbinder's Mantle (Cloth Intellect shoulder)      red          +4 Crit
    The Pyramid            Gutchewer's Girdle (Mail Agility waist)             red          +4 Haste
    Bly's crew             Sergeant's Dented Breastplate (Plate Tank chest)    blue         +4 Parry
    Chief Ukorz            Sandscalp's War Kilt (Mail Agility legs)            red          +4 Crit
    Gahz'rilla             Gauntlets of the Sacred Pool (Plate Intellect)      red          +4 Haste
"""

from lib.dsl.items import Socket, hit_spell, item, use_spell

from .ladders import VANILLA_DUNGEON
from .zul_farrak_effects import call_of_sulthraze_213808

# Socket bonus enchants (stock SpellItemEnchantment ids, +4 each; see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_PARRY_4 = 3359

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does
# A stock Bind on Equip entry stays so on Normal and is Bind on Pickup from Heroic up (user 2026-11-06, R1 N5; the
# Stratholme list): every minted tier would otherwise copy the stock column.
HIGHER_TIERS = ("heroic", "empowered_1", "empowered_2", "empowered_3")
BOP_ABOVE_NORMAL = {name: {"bonding": BOP} for name in HIGHER_TIERS}
EXTRA_STAMINA = 0.25  # "extra Stamina" on a tank piece: a quarter more than the tier's baseline

# Item level per boss (handoff section 1.2); required level defaults to the item level - 5.
THEKA = 46
ANTUSUL = 48
ZUMRAH = 47
PYRAMID = 49
BLY = 49
UKORZ = 50
GAHZRILLA = 50

# Bows, guns and crossbows need no ammo (source/world/ranged_weapons.py, hunter-rework Q3). An item() declaration owns
# its entry, so it sets the column itself and the minted tiers copy it (a new gun `like=` a gun sets it too).
NO_AMMO = 0

# Weapon-tier role cell (scarlet_monastery.py, the Blackrock gear review's S2): a caster main-hand below level 60 would
# take the 1-59 cell on its Normal tier and the 60-100 cell from Heroic up, a 2.4x step (the ladder check refuses over
# 1.5x). The 60-100 cell is declared on every tier instead, so the step is the budget curve's alone.
# physical InventoryType 13 ilvl 60-100: caster weapons take the physical budget (level60-stat-curve 1.8)
CASTER_MAIN_HAND_MULT = 0.445

JANGTHRAZE_ABSORB = 11657  # stock: Jang'thraze's Chance on hit, a 54 point absorb

R, Y, B = Socket.RED, Socket.YELLOW, Socket.BLUE

# ---------------------------------------------------------------------------------------------------------------------
# Theka the Martyr (item level 46)

item("zf_carapace_of_the_martyr", name="Carapace of the Martyr", like=10775, ilvl=THEKA, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Crit/Mastery",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("zf_scarab_shell_bracers", name="Scarab-shell Bracers", like=8205, ilvl=THEKA, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Mastery/Versatility")
item("zf_penitents_cord", name="Penitent's Cord", like=14258, ilvl=THEKA, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Versatility")
# Moved from the shared rare list: stock 46 / 41, the level of Theka.
item("zf_blackmetal_cape", base=9512, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Versatility", overrides=BOP_ABOVE_NORMAL)
# Moved from the shared rare list (stock 47 / 42): level 46 here, required level 41. Keeps Rend on hit (16406).
item("zf_gutwrencher", base=5616, ilvl=THEKA, required_level=THEKA - 5, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)", overrides=BOP_ABOVE_NORMAL)
# Moved from the shared rare list (stock 46 / 41). Keeps Wound on hit (13486).
item("zf_bloodletter_scalpel", base=9511, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)", overrides=BOP_ABOVE_NORMAL)
item("zf_libram_of_the_persecuted", name="Libram of the Persecuted", like=23201, ilvl=THEKA, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Parry/Versatility (Any)")
item("zf_martyrs_reliquary", name="Martyr's Reliquary", like=1713, ilvl=THEKA, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Versatility (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Antu'sul (item level 48; the stock items keep their own level 48-49)

# Keeps Thunder Clap on hit (13532).
item("zf_hand_of_antusul", base=9639, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Mastery (Solo)")
# The other half of Sul'thraze: the join takes the one of Jang'thraze's own tier. The stock level is 49 / 44.
item("zf_sangthraze_the_deflector", base=9379, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Parry (Solo)")
# The stock Equip (Attack Power 9142) folds into the budget; the random suffix (783) is cleared.
item("zf_vice_grips", base=9640, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Mastery/Versatility", RandomProperty=0)
item("zf_lifeblood_amulet", base=9641, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Mastery/Versatility", primary_share=0)
# The Leather Tank piece: Agility, Dodge and a quarter more Stamina.
item("zf_stonegaze_girdle", name="Stonegaze Girdle", like=8255, ilvl=ANTUSUL, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge/Versatility", extra_stamina=EXTRA_STAMINA)
item("zf_sullithuz_scale_coif", name="Sul'lithuz Scale Coif", like=8191, ilvl=ANTUSUL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit/Versatility",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("zf_totem_of_the_stone_servant", name="Totem of the Stone Servant", like=23199, ilvl=ANTUSUL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Mastery")

# ---------------------------------------------------------------------------------------------------------------------
# Witch Doctor Zum'rah (item level 47)

item("zf_jumanza_grips", base=18083, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Mastery")
item("zf_zumrahs_vexing_cane", base=18082, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery/Versatility")
# Moved from the shared rare list (stock 48 / 43): level 47 here, required level 42. A ring: secondaries only (the stock
# row has Intellect, Spirit and a negative Strength line).
item("zf_brainlash", base=6440, ilvl=ZUMRAH, required_level=ZUMRAH - 5, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Mastery/Proc", primary_share=0, overrides=BOP_ABOVE_NORMAL)
item("zf_soulbinders_mantle", name="Soulbinder's Mantle", like=7435, ilvl=ZUMRAH, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("zf_gravewalker_treads", name="Gravewalker Treads", like=10701, ilvl=ZUMRAH, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste/Versatility")
item("zf_idol_of_the_restless_grave", name="Idol of the Restless Grave", like=23198, ilvl=ZUMRAH, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste/Versatility")
item("zf_vessel_of_lost_souls", name="Vessel of Lost Souls", like=7734, ilvl=ZUMRAH, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Mastery/Versatility")

# ---------------------------------------------------------------------------------------------------------------------
# The Pyramid, one list on Sezz'ziz (item level 49)

item("zf_bad_mojo_mask", base=9470, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Versatility")
item("zf_jinxed_hoodoo_skin", base=9473, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery/Versatility")
item("zf_jinxed_hoodoo_kilt", base=9474, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Versatility")
# Keeps Fatal Wound on hit (18206).
item("zf_diabolic_skiver", base=9475, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Versatility (Solo)")
# Moved from the shared rare list (stock 49 / 44, the Pyramid's level). No socket: two sockets on a three-secondary
# two-hander took its Heroic Strength below its Normal one (designer question 1).
item("zf_the_minotaur", base=9481, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Mastery/Versatility", overrides=BOP_ABOVE_NORMAL)
item("zf_executioners_vambraces", name="Executioner's Vambraces", like=9432, ilvl=PYRAMID, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Parry/Versatility (Any)")
item("zf_gutchewers_girdle", name="Gutchewer's Girdle", like=12257, ilvl=PYRAMID, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste/Mastery",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("zf_totem_of_the_blood_altar", name="Totem of the Blood Altar", like=23200, ilvl=PYRAMID, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste/Mastery")

# ---------------------------------------------------------------------------------------------------------------------
# Sergeant Bly's crew, one list (item level 49)

# Moved from the shared rare list (stock 48 / 43): level 49 here, required level 44.
item("zf_troll_protector", base=2040, ilvl=BLY, required_level=BLY - 5, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block/Mastery", overrides=BOP_ABOVE_NORMAL)
# Moved from the shared rare list (stock 48 / 43): level 49 here, required level 44.
item("zf_eyegouger", base=9480, ilvl=BLY, required_level=BLY - 5, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge/Mastery", overrides=BOP_ABOVE_NORMAL)
# Moved from the shared rare list (stock 49 / 44, Bly's level). The 8 fire resistance is cleared.
item("zf_flaming_incinerator", base=9483, fire_res=0, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Versatility", overrides=BOP_ABOVE_NORMAL)
# Plate Tank chest: Strength, Dodge, Parry, Mastery (a new three-secondary shape); one blue socket, Parry bonus.
item("zf_sergeants_dented_breastplate", name="Sergeant's Dented Breastplate", like=9286, ilvl=BLY, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Dodge/Parry/Mastery",
     sockets=(B,), socket_bonus=BONUS_PARRY_4)
item("zf_ravens_soft_step_gloves", name="Raven's Soft-step Gloves", like=9920, ilvl=BLY, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit/Versatility")
item("zf_murtas_mending_wraps", name="Murta's Mending Wraps", like=4133, ilvl=BLY, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Mastery/Versatility")
item("zf_blastfuse_bandolier", name="Blastfuse Bandolier", like=15617, ilvl=BLY, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste/Versatility")
item("zf_ill_gotten_coin", name="Ill-gotten Coin", like=17774, ilvl=BLY, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery/Versatility")
# A Hunter gun, no ammo.
item("zf_weeglis_blunderbuss", name="Weegli's Blunderbuss", like=10508, ilvl=BLY, bonding=BOP, ammo_type=NO_AMMO,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Mastery (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Chief Ukorz Sandscalp and Ruuzlu (item level 50)

item("zf_big_bad_pauldrons", base=9476, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Dodge/Versatility")
# Keeps its absorb on hit (Jang'thraze 11657, the stock proc data); the Use is the tier-matched join (213808), same
# charge rule as the stock one.
item("zf_jangthraze_the_protector", base=11086, ladder=VANILLA_DUNGEON,
     spells=(use_spell(call_of_sulthraze_213808, charges=-1), hit_spell(JANGTHRAZE_ABSORB, ppm=1.2)),
     primary="Strength (Solo)", secondary="Versatility (Solo)")
# Keeps its 3 sec stun on hit (Stun 56).
item("zf_the_chiefs_enforcer", base=9477, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)")
# Keeps Wound on hit (16405).
item("zf_ripsaw", base=9478, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste (Solo)")
# The stock Equip (Attack Power 15807) folds into the budget.
item("zf_embrace_of_the_lycan", base=9479, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Mastery")
# Stock level 50 / 45 (it drops from Antu'sul and Ukorz in stock); a ring: secondaries only, the random suffix (3253)
# is cleared.
item("zf_runed_ring", base=862, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Haste/Mastery", primary_share=0, RandomProperty=0, overrides=BOP_ABOVE_NORMAL)
item("zf_sandscalps_war_kilt", name="Sandscalp's War Kilt", like=14786, ilvl=UKORZ, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit/Mastery/Versatility",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("zf_ruuzlus_bloodied_greaves", name="Ruuzlu's Bloodied Greaves", like=14951, ilvl=UKORZ, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Haste/Mastery")
item("zf_idol_of_the_lycan", name="Idol of the Lycan", like=22399, ilvl=UKORZ, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge/Mastery")
# Not a drop: the join of a Jang'thraze and a Sang'thraze of the same tier (Call of Sul'thraze 213808), on every tier.
# Its Normal tier keeps the stock Epic quality and level 55 / 50; keeps Sul'thraze on hit (11658).
item("zf_sulthraze_the_lasher", base=9372, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Mastery/Versatility")

# ---------------------------------------------------------------------------------------------------------------------
# Hydromancer Velratha and Gahz'rilla (item level 50; the stock items keep their own level 47-48)

# Keeps Static Electricity on hit (3742).
item("zf_gahzrilla_fang", base=9467, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Versatility (Solo)")
# The stock Equip (Increased Mana Regen 21631, the dead MP5) folds into the budget.
item("zf_gahzrilla_scale_armor", base=9469, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery/Versatility")
item("zf_stormscale_spaulders", name="Stormscale Spaulders", like=15628, ilvl=GAHZRILLA, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Haste")
# Plate Intellect hands (the single-spec Holy piece): one red socket, Haste bonus (its first secondary is Mastery).
item("zf_gauntlets_of_the_sacred_pool", name="Gauntlets of the Sacred Pool", like=7938, ilvl=GAHZRILLA,
     bonding=BOP, ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Mastery/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("zf_hydromancers_scepter", name="Hydromancer's Scepter", like=4122, ilvl=GAHZRILLA, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Mastery/Versatility",
     budget_mult=CASTER_MAIN_HAND_MULT)
item("zf_robes_of_the_rising_water", name="Robes of the Rising Water", like=4120, ilvl=GAHZRILLA, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Crit/Mastery/Versatility")
item("zf_stillwater_drape", name="Stillwater Drape", like=4114, ilvl=GAHZRILLA, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Mastery/Versatility")
item("zf_libram_of_the_sacred_pool", name="Libram of the Sacred Pool", like=22402, ilvl=GAHZRILLA, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste/Mastery")
item("zf_coil_of_the_electrified_scale", name="Coil of the Electrified Scale", like=11977, ilvl=GAHZRILLA,
     bonding=BOP, ladder=VANILLA_DUNGEON, primary=None, secondary="Crit/Proc", primary_share=0)

# ---------------------------------------------------------------------------------------------------------------------
# The rares, one pool (each keeps its stock level: 47 / 42, Spellshock Leggings 50 / 45)

item("zf_desertwalker_cane", base=12471, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Mastery")
item("zf_sandstalker_ankleguards", base=12470, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Versatility")
# Moved from the shared rare list.
item("zf_witch_doctors_cane", base=9482, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Mastery", overrides=BOP_ABOVE_NORMAL)
# Moved from the shared rare list (it drops from two bosses in stock): keeps stock 50 / 45.
item("zf_spellshock_leggings", base=9484, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Mastery", overrides=BOP_ABOVE_NORMAL)
