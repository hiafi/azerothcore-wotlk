"""
The Gnomeregan boss list items (wave 5 dungeon items, after the Deadmines, Shadowfang Keep, Scarlet Monastery, Ragefire
Chasm and Zul'Farrak precedents): the 48 approved list items of the six encounters and the Dark Iron Ambassador rare
(docs/dungeons/gnomeregan-rework.md ## Loot "Loot list", approved 2026-11-24, ruling 56; copied in docs/dungeons/
dungeon-loot-vanilla.md "### Gnomeregan"). Out of scope here: the 3 Mekgineer Thermaplugg, the Whole Workshop hard mode
items (gnomeregan_hard_mode.py), the quest items, the keys, the schematics, Robo-mechanical Guts and the loot tables
(the dungeon build's L-1 wires them).

Gnomeregan is a leveling dungeon (levels 24-33). Normal drops Rare at the boss's item level (designer ruling G1 B,
2026-11-25: the highest stock item level among the stock items that stay on that boss; Techbot 26, Viscous Fallout 32,
Electrocutioner 6000 34, the Mobile Alert System 31 from its moved-in stock, Crowd Pummeler 9-60 34, Mekgineer
Thermaplugg 37) with required level the item level - 5, for a new item and for a stock item moved to another boss (the
nine blues of the stock shared rare list, Grubbis Paws, the Gnomeregan Amulet and the Gyromatic Icemaker); a stock item
that stays on its own boss keeps its stock level and required level, and so do the Dark Iron Ambassador's three (a
rare's own stock loot, nothing new or moved). Heroic is 66 Epic
with the Heroic flag, then the three empowered steps (ladders.py `VANILLA_DUNGEON`). A stock entry is the ladder's
Normal tier (`base=`). New items copy a stock look (`like=`, look only) and are Bind on Pickup. The stock white and
green entries (Techbot CPU Shell, Gnomeregan Amulet, Gyromatic Icemaker) become Rare (`quality=RARE`). Bind on Equip
stock entries (the nine shared rare list blues) and the unbound Techbot CPU Shell stay so on Normal and are Bind on
Pickup from Heroic up (`BOP_ABOVE_NORMAL`, the Zul'Farrak review's M1).

Bosses (counts): Techbot 7, Viscous Fallout 7, Electrocutioner 6000 7, the Mobile Alert System 7, Crowd Pummeler 9-60 8,
Mekgineer Thermaplugg 9, the Dark Iron Ambassador 3 (48 in all; 28 altered stock entries, 20 new items).

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and the
secondaries are listed (the doc's order of secondaries does not matter to an Even shape). Rings and the neck (Electro-
cutioner Lagnut, Charged Gear, Gnomeregan Amulet) carry secondaries only (`primary=None`, share 0), and so does the
Ringside Bell, the list's trinket with no primary (the Deadman's Hand precedent, "Dodge/Versatility (Any)"). The other
trinkets (Backup Drive, 6000 Volt Capacitor) are stat-only with the doc's primary, as Vessel of Lost Souls and
Ill-gotten Coin were: the doc lists no effect for them. 6000 Volt Capacitor's Proc Chance is the Crit/Proc shape (39)
like Brainlash and the Coil of the Electrified Scale: a stat on the trinket, not a spell.

**Shape this list needs that does not exist yet** (the integration adds it in the one pending itemization file; it
models Crit/Haste/Versatility 44 with Cooldown Haste in the second place, an Even trio, no rule):
  - "Crit/CDH/Versatility"   secondary, Even trio (32, 24, 23), no rule: Mechbuilder's Overalls
Every other shape exists (Block/Versatility 91, Parry/Mastery 76, Mastery/CDH 84, Haste/CDH 38, Crit/CDH 37, Crit/Proc
39, Dodge/Parry 62, Dodge/Mastery 59, Dodge/Versatility 87 and (Any) 98, Crit/Haste/Mastery 42, Crit/Mastery/Versatility
45 and the Even pairs and Solo shapes).

**Kept stock effects** (`keep_spells=True`, the Ravager precedent; each is the stock row's only spell slot). The stock
spells are the same on every tier (a stock spell cannot scale) and each effect item pays 0.7 of the budget
(itemization-changes.md section 3):
  - Hydrocane 9452: Equip, Water Breathing 11789 (the wearer, indefinite; nothing to scale)
  - Toxic Revenger 9453: Chance on hit, Poison Cloud 11790 (ppm 1.5; 5 Nature damage every 5 sec for 8 sec to enemies
    within 14 yd of the wearer)
  - Electrocutioner Leg 9446: Chance on hit, Lightning Bolt 13482 (ppm 1.75; about 9 to 20 Nature damage, one target)
  - Supercharger Battle Axe 9486: Chance on hit, Lightning Bolt 13527 (ppm 0.9; about 80 to 100 Nature damage, one
    target)
  - Vibroblade 9485: Chance on hit, Puncture Armor 11791 (ppm 3; 100 less armor for 30 sec on the target)
  - Manual Crowd Pummeler 9449: Use, Haste 13494 (500 haste rating for 30 sec), on a 3 min item cooldown (stock 60
    min)
  - Electromagnetic Gigaflux Reactivator 9492: Use, 11826 (a lightning cone, Pet Bombling's 11828, then a barrier), on
    a 5 min item cooldown (stock 30 min; the stock category 1141 and its 10 sec stay)
The two Uses are declared with `spells=(use_spell(...),)` and a shorter `cooldown=` (designer ruling G2 A, the Dog
Whistle precedent): the item's spellcooldown_1 overrides the spell's, so the stock spell rows stay untouched for every
other user of 13494 and 11826, and every tier carries the same stock spell and the same cooldown.
Every stock stat spell slot folds into the budget (`absorbed_spell_slots`, the default): Spidertank Oilrag's and
Gnomebot Operating Boots' Increased Mana Regen (21361, 21618, the dead MP5). No other stock row carries a spell slot.

**Moves and stat changes.** Every doc stat has a point on every tier (tested on the materialized rows). The stock rows
lose their dead stats (Spell Power, MP5, Spirit on a ring, a primary on a ring: the shape replaces them), the random
properties of Emissary Cuffs (1072), Charged Gear (3481) and the Gnomeregan Amulet (3506) (`RandomProperty=0`), and the
elemental resistances (Hydrocane's 15 frost, the Icemaker's 5 frost, Acidic Walkers', Charged Gear's and Mechbuilder's
Overalls' 5 nature / arcane, Emissary Cuffs' 5 arcane: `*_res=0`; the wand keeps its frost damage type). The nine moved
stock items whose stock level is not their new boss's get that level through `moved()`; Caverndeep Trudgers (32 / 27 on
Viscous Fallout), the Gnomeregan Amulet and the Gyromatic Icemaker (31 / 26 on the Alert System) already sit on it.

**Caster main-hand cell.** Royal Diplomatic Scepter (Intellect, a caster one-hand mace) and Mekgineer's Arc Welder
(Intellect, a caster dagger) declare the 60-100 physical role cell (0.445) on every tier, like the earlier dungeons'
caster main-hands (blackrock_depths.py, scarlet_monastery.py, ragefire_chasm.py, zul_farrak.py; the Blackrock gear
review's S2): their level is below 60, so without it the Normal tier would read the 1-59 caster cell and the Heroic tier
the 60-100 one, two different curves for one item (designer question 3). The staff and the two-handers keep their own
cells.

**Sockets.** The doc names no per-item pick, so every pick is a designer question (STAGE-GG-LIST report). The shared
rule (boss-rework-systems.md section 2; deadmines.py): about one standalone armor piece or weapon per boss carries 1, a
two-hander 2 (none here, as Zul'Farrak), trinkets and jewelry never, Normal tiers none (ladders.py). The first socket is
red on damage and healing gear and blue on tank gear. The socket bonus is a stock +4 rating (2874 Crit, 3267 Haste, 2871
Dodge, 3359 Parry): no enchant exists for Mastery, Versatility, Cooldown Haste or Proc Chance, so a first secondary of
those takes Haste or Crit. Picks, one per boss (the Ambassador's rare holds none: it is not a boss list):

    Techbot                 Tech Support Headset (Mail Intellect head)           red    +4 Haste
    Viscous Fallout         Lead-plated Legguards (Plate Intellect legs)         red    +4 Haste
    Electrocutioner 6000    Conductive Hauberk (Mail Agility chest)              red    +4 Haste
    The Mobile Alert System Security Chief's Girdle (Plate Tank waist)           blue   +4 Dodge
    Crowd Pummeler 9-60     Piston-driven Legplates (Plate Strength legs)        red    +4 Crit
    Mekgineer Thermaplugg   Mekgineer's Blast Visor (Plate Tank head)            blue   +4 Dodge
"""

from lib.dsl.items import NEW_ITEM_LEVEL_GAP, Quality, Socket, item, use_spell

from .ladders import VANILLA_DUNGEON

# Socket bonus enchants (stock SpellItemEnchantment ids, +4 each; see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_DODGE_4 = 2871

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does
RARE = Quality.RARE  # a stock white or green entry becomes a Rare list item
# A stock entry that is not Bind on Pickup (the Bind on Equip blues, the unbound Techbot CPU Shell) stays so on Normal
# and is Bind on Pickup from Heroic up (user 2026-11-06, R1 N5; the Zul'Farrak review's M1): every minted tier would
# otherwise copy the stock column.
HIGHER_TIERS = ("heroic", "empowered_1", "empowered_2", "empowered_3")
BOP_ABOVE_NORMAL = {name: {"bonding": BOP} for name in HIGHER_TIERS}
EXTRA_STAMINA = 0.25  # "extra Stamina" on a tank piece: a quarter more than the tier's baseline

# The Normal item level per boss (designer ruling G1 B, 2026-11-25): a new item, and a stock item moved onto another
# boss, takes the highest stock item level among the stock items that stay on that boss (live item_template
# 2026-11-25), with required level the item level - 5. The Mobile Alert System had no stock loot: its level is its
# moved-in stock's highest (the Gnomeregan Amulet and the Gyromatic Icemaker, 31). A stock item on its own boss keeps
# its stock level and required level. Heroic and up are the ladder's.
TECHBOT = 26        # Techbot CPU Shell
FALLOUT = 32        # Hydrocane, Toxic Revenger, Acidic Walkers
ELECTRO = 34        # Electrocutioner Leg, Electrocutioner Lagnut
ALERT = 31          # Gnomeregan Amulet, Gyromatic Icemaker (moved in)
PUMMELER = 34       # Manual Crowd Pummeler
THERMAPLUGG = 37    # Electromagnetic Gigaflux Reactivator, Left Arm, Central Core, Charged Gear


def moved(level: int) -> dict:
    """The Normal level columns of a stock item moved onto a boss whose level differs from its stock level."""
    return {"ilvl": level, "required_level": level - NEW_ITEM_LEVEL_GAP}  # a new item's default gap (5)


# The two stock Use effects keep their stock spell rows and get a dungeon-usable item cooldown (designer ruling G2 A,
# 2026-11-25), through the item's own spell columns (spellcooldown_1, the Dog Whistle precedent): the engine takes the
# item's cooldown over the spell's (Player::AddSpellAndCategoryCooldowns), so other users of the spells are unchanged.
SPELL_PUMMELER_HASTE = 13494            # Haste: +500 haste rating for 30 sec (stock cooldown 60 min)
PUMMELER_COOLDOWN_MS = 180000           # 3 min
SPELL_GIGAFLUX_REACTIVATOR = 11826      # the lightning cone (11828) then a barrier (stock cooldown 30 min)
GIGAFLUX_COOLDOWN_MS = 300000           # 5 min
GIGAFLUX_CATEGORY = 1141                # stock: the shared trinket Use category, 10 sec
GIGAFLUX_CATEGORY_COOLDOWN_MS = 10000

# Bows, guns and crossbows need no ammo (source/world/ranged_weapons.py, hunter-rework Q3). An item() declaration owns
# its entry, so it sets the column itself and the minted tiers copy it (a new crossbow `like=` a crossbow sets it too).
NO_AMMO = 0

# Weapon-tier role cell (scarlet_monastery.py, the Blackrock gear review's S2): a caster main-hand below level 60 would
# take the 1-59 cell on its Normal tier and the 60-100 cell from Heroic up, a 2.4x step (the ladder check refuses over
# 1.5x). The 60-100 cell is declared on every tier instead, so the step is the budget curve's alone.
# physical InventoryType 13 ilvl 60-100: caster weapons take the physical budget (level60-stat-curve 1.8)
CASTER_MAIN_HAND_MULT = 0.445

R, B = Socket.RED, Socket.BLUE

# ---------------------------------------------------------------------------------------------------------------------
# Techbot (item level 26: the stock CPU Shell's)

# A white shield made a Rare list item: Strength, Block, Versatility (a tank shield).
item("gnomer_techbot_cpu_shell", base=9444, quality=RARE, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block/Versatility", overrides=BOP_ABOVE_NORMAL)
# Moved from the shared rare list (stock 28 / 23): level 26 here.
item("gnomer_oscillating_power_hammer", base=9488, **moved(TECHBOT), ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Dodge (Solo)", overrides=BOP_ABOVE_NORMAL)
# Moved from the shared rare list (stock 29 / 24): level 26 here. A warrior gun (designer): Strength.
item("gnomer_hi_tech_supergun", base=9487, **moved(TECHBOT), ammo_type=NO_AMMO,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Haste/Versatility", overrides=BOP_ABOVE_NORMAL)
# Moved from the shared rare list (stock 32 / 27): level 26 here. The stock Spell Power folds into the budget.
item("gnomer_hotshot_pilots_gloves", base=9491, **moved(TECHBOT), ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Versatility", overrides=BOP_ABOVE_NORMAL)
item("gnomer_grounded_sabatons", name="Grounded Sabatons", like=9289, ilvl=TECHBOT, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Parry/Mastery")
item("gnomer_tech_support_headset", name="Tech Support Headset", like=1282, ilvl=TECHBOT, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Mastery/CDH",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
# A trinket with no effect in the doc: stats only, Intellect and a Haste / Cooldown Haste pair.
item("gnomer_backup_drive", name="Backup Drive", like=7506, ilvl=TECHBOT, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/CDH")

# ---------------------------------------------------------------------------------------------------------------------
# Viscous Fallout (item level 32: Hydrocane's, Toxic Revenger's, Acidic Walkers')

# Keeps its Equip, Water Breathing (11789); the 15 frost resistance is cleared.
item("gnomer_hydrocane", base=9452, keep_spells=True, frost_res=0, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Haste")
# Keeps Poison Cloud on hit (11790).
item("gnomer_toxic_revenger", base=9453, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)")
item("gnomer_acidic_walkers", base=9454, nature_res=0, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Mastery/Versatility")
# Moved from Grubbis (cut) (stock 34 / 29): level 32 here.
item("gnomer_grubbis_paws", base=9445, **moved(FALLOUT), ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Haste")
# Moved from the shared rare list (stock 32 / 27, Viscous Fallout's level).
item("gnomer_caverndeep_trudgers", base=9510, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery/Versatility", overrides=BOP_ABOVE_NORMAL)
# Plate Intellect legs (the single-spec Holy piece): one red socket, Haste bonus (its first secondary is Haste).
item("gnomer_lead_plated_legguards", name="Lead-plated Legguards", like=7921, ilvl=FALLOUT, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("gnomer_hazmat_drape", name="Hazmat Drape", like=14563, ilvl=FALLOUT, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Mastery/CDH")

# ---------------------------------------------------------------------------------------------------------------------
# Electrocutioner 6000 (item level 34: the Leg's and the Lagnut's; the Oilrag keeps its own 33 / 28)

# Keeps Lightning Bolt on hit (13482).
item("gnomer_electrocutioner_leg", base=9446, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste (Solo)")
# A ring: secondaries only (the stock row is a lone Spirit, a primary on a ring and Spirit's own stat).
item("gnomer_electrocutioner_lagnut", base=9447, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/Versatility", primary_share=0)
# The stock Equip (Increased Mana Regen 21361, the dead MP5) folds into the budget.
item("gnomer_spidertank_oilrag", base=9448, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/CDH")
# Moved from the shared rare list (stock 28 / 23): level 34 here. Keeps Lightning Bolt on hit (13527).
item("gnomer_supercharger_battle_axe", base=9486, **moved(ELECTRO), keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Versatility (Solo)", overrides=BOP_ABOVE_NORMAL)
item("gnomer_insulated_chain_leggings", name="Insulated Chain Leggings", like=2545, ilvl=ELECTRO, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Haste")
item("gnomer_conductive_hauberk", name="Conductive Hauberk", like=2869, ilvl=ELECTRO, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit/Haste/Mastery",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
# A Strength trinket with no effect in the doc: stats only (Crit and Proc Chance, the Crit/Proc shape).
item("gnomer_6000_volt_capacitor", name="6000 Volt Capacitor", like=4381, ilvl=ELECTRO, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Crit/Proc")

# ---------------------------------------------------------------------------------------------------------------------
# The Mobile Alert System (item level 31: its moved-in stock's highest, the Amulet's and the Icemaker's)

# A green neck made a Rare list item (stock 31 / 26, the Alert System's level), a neck with secondaries only. The random
# property (3506) is cleared.
item("gnomer_gnomeregan_amulet", base=10299, quality=RARE, RandomProperty=0,
     ladder=VANILLA_DUNGEON, primary=None, secondary="Crit/CDH", primary_share=0)
# A green trash wand moved onto the list (stock 31 / 26, the Alert System's level), the 5 frost resistance cleared (the
# wand keeps its frost damage type).
item("gnomer_gyromatic_icemaker", base=9489, quality=RARE, frost_res=0,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Haste (Solo)")
# Moved from the shared rare list (stock 30 / 25): level 31 here. Keeps Puncture Armor on hit (11791).
item("gnomer_vibroblade", base=9485, **moved(ALERT), keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)", overrides=BOP_ABOVE_NORMAL)
# Moved from the shared rare list (stock 30 / 25): level 31 here.
item("gnomer_petrolspill_leggings", base=9509, **moved(ALERT), ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Versatility", overrides=BOP_ABOVE_NORMAL)
# The list's crossbow, no ammo.
item("gnomer_security_repeater", name="Security Repeater", like=6315, ilvl=ALERT, bonding=BOP, ammo_type=NO_AMMO,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Versatility (Solo)")
item("gnomer_night_watch_mantle", name="Night Watch Mantle", like=7727, ilvl=ALERT, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Mastery")
# Plate Tank waist: Strength, Dodge, Mastery; one blue socket, Dodge bonus.
item("gnomer_security_chiefs_girdle", name="Security Chief's Girdle", like=14898, ilvl=ALERT, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Dodge/Mastery",
     sockets=(B,), socket_bonus=BONUS_DODGE_4)

# ---------------------------------------------------------------------------------------------------------------------
# Crowd Pummeler 9-60 (item level 34: the Pummeler's; the Boots keep their own 33 / 28)

# Keeps its Use, Haste (13494), on a 3 min item cooldown (ruling G2 A; stock 60 min, no category).
item("gnomer_manual_crowd_pummeler", base=9449, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)",
     spells=(use_spell(SPELL_PUMMELER_HASTE, cooldown=PUMMELER_COOLDOWN_MS, category_cooldown=0),))
# The stock Equip (Increased Mana Regen 21618, the dead MP5) folds into the budget.
item("gnomer_gnomebot_operating_boots", base=9450, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Versatility")
# Moved from the shared rare list (stock 29 / 24): level 34 here.
item("gnomer_gizmotron_megachopper", base=9490, **moved(PUMMELER), ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste/Mastery", overrides=BOP_ABOVE_NORMAL)
item("gnomer_piston_driven_legplates", name="Piston-driven Legplates", like=9970, ilvl=PUMMELER, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Crit/Mastery/Versatility",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
# The dungeon's Leather Tank piece: Agility, Dodge, Versatility and a quarter more Stamina.
item("gnomer_shock_absorber_pads", name="Shock Absorber Pads", like=14566, ilvl=PUMMELER, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Dodge/Versatility", extra_stamina=EXTRA_STAMINA)
item("gnomer_grease_monkeys_jerkin", name="Grease Monkey's Jerkin", like=14562, ilvl=PUMMELER, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste/CDH")
item("gnomer_piston_fist", name="Piston Fist", like=20954, ilvl=PUMMELER, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Haste")
# A tank trinket with no effect in the doc: no primary, Dodge and Versatility (the Deadman's Hand precedent).
item("gnomer_ringside_bell", name="Ringside Bell", like=21568, ilvl=PUMMELER, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Dodge/Versatility (Any)", primary_share=0)

# ---------------------------------------------------------------------------------------------------------------------
# Mekgineer Thermaplugg (item level 37: the four stock items')

# Keeps its Use, the lightning cone and barrier (11826), on a 5 min item cooldown (ruling G2 A; stock 30 min); the
# stock category (1141, 10 sec) stays.
item("gnomer_electromagnetic_gigaflux_reactivator", base=9492, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Mastery",
     spells=(use_spell(SPELL_GIGAFLUX_REACTIVATOR, cooldown=GIGAFLUX_COOLDOWN_MS, category=GIGAFLUX_CATEGORY,
                       category_cooldown=GIGAFLUX_CATEGORY_COOLDOWN_MS),))
item("gnomer_thermapluggs_left_arm", base=9459, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Haste/Mastery")
# A Spirit shield: Spirit, Haste, Mastery (a caster shield).
item("gnomer_thermapluggs_central_core", base=9458, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Mastery")
# A ring: secondaries only; the random property (3481) and the 5 nature and arcane resistances are cleared.
item("gnomer_charged_gear", base=9461, RandomProperty=0, nature_res=0, arcane_res=0, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Haste/CDH", primary_share=0)
# Moved from the shared rare list (stock 31 / 26): level 37 here, the 5 arcane resistance cleared. The only
# Crit / Cooldown Haste / Versatility item: a new shape.
item("gnomer_mechbuilders_overalls", base=9508, **moved(THERMAPLUGG), arcane_res=0,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/CDH/Versatility", overrides=BOP_ABOVE_NORMAL)
# Plate Tank head: Strength, Dodge, Parry; one blue socket, Dodge bonus.
item("gnomer_mekgineers_blast_visor", name="Mekgineer's Blast Visor", like=8161, ilvl=THERMAPLUGG, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Dodge/Parry",
     sockets=(B,), socket_bonus=BONUS_DODGE_4)
item("gnomer_girdle_of_spare_fuses", name="Girdle of Spare Fuses", like=8159, ilvl=THERMAPLUGG, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Haste/CDH")
item("gnomer_mekgineers_arc_welder", name="Mekgineer's Arc Welder", like=1936, ilvl=THERMAPLUGG, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/CDH", budget_mult=CASTER_MAIN_HAND_MULT)
# The list's one held-in-off-hand item (an Intellect caster off-hand).
item("gnomer_rolled_workshop_schematics", name="Rolled Workshop Schematics", like=11855, ilvl=THERMAPLUGG, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Mastery")

# ---------------------------------------------------------------------------------------------------------------------
# The Dark Iron Ambassador, a rare (each keeps its stock level, 33-35 / 28-30)

# The 5 arcane resistance and the random property (1072) are cleared.
item("gnomer_emissary_cuffs", base=9455, RandomProperty=0, arcane_res=0, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Mastery")
item("gnomer_glass_shooter", base=9456, ammo_type=NO_AMMO, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)")
item("gnomer_royal_diplomatic_scepter", base=9457, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Versatility", budget_mult=CASTER_MAIN_HAND_MULT)
