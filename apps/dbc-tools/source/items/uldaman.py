"""
The Uldaman boss list items (wave 5 dungeon items, after the Deadmines, Shadowfang Keep, Scarlet Monastery, Ragefire
Chasm, Zul'Farrak and Gnomeregan precedents): the 49 approved list items of the eight encounters (docs/dungeons/
uldaman-rework.md ## Loot "Proposal", approved 2026-11-21, ruling 35; copied in docs/dungeons/dungeon-loot-vanilla.md
"### Uldaman"). Out of scope here: the 3 Archaedas hard mode items (uldaman_hard_mode.py), the quest items (the Shaft
of Tsol), Baelog's Precision Arrow, the shared trash rares and the loot tables (the dungeon build's L-1 wires them).

Uldaman is a leveling dungeon (levels 35-45). Normal drops Rare at the boss's item level (the Gnomeregan G1 B rule,
2026-11-25, the default here: a new item takes the highest stock item level among the stock items that stay on that
boss, required level the item level - 5; the two new bosses take a level the doc cannot give them, designer question 1).
Heroic is 66 Epic with the Heroic flag, then the three empowered steps (ladders.py `VANILLA_DUNGEON`). A stock entry is
the ladder's Normal tier (`base=`) and keeps its stock level and required level: all 25 stock items stay on their stock
boss, so no stock item is moved or re-leveled and the Lost Dwarves, who get no new item, keep the six stock levels
(40-43 / 35-38). New items copy a stock look (`like=`, look only) and are Bind on Pickup. Every stock entry is already
Rare and Bind on Pickup, so no quality or binding override is needed.

Bosses (counts): Revelosh 5, the Lost Dwarves (one list) 6, Ironaya 5, the Obsidian Sentinel 5, the Ancient Stone Keeper
5, Galgann Firehammer 6, Grimlok 6, the Stone Keepers 5, Archaedas 6 (49 in all; 25 altered stock entries, 24 new
items). New items' Normal level: Revelosh 41 / 36, Ironaya 42 / 37, the Obsidian Sentinel 45 / 40 (default: the next
boss's), the Ancient Stone Keeper 45 / 40, Galgann 47 / 42, Grimlok 47 / 42, the Stone Keepers 47 / 42 (default: between
Grimlok and Archaedas), Archaedas 49 / 44.

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and the
secondaries are listed (the doc's order of secondaries does not matter to an Even shape). Rings and the two necks
(Reforged Splinter, Archaedic Stone, Pendant of Two Lights, Jadespine Collar) carry secondaries only (`primary=None`,
share 0). The one trinket, Directive Core, is stat-only with the doc's primary (Strength, Cooldown Haste), as Backup
Drive, 6000 Volt Capacitor, Vessel of Lost Souls and Ill-gotten Coin were: the doc lists no effect for it. The four
relics are stats only, like the earlier dungeons' relics, told apart by name: Libram of the Awakened Hall (Holy,
Intellect), Totem of the Turning Wind (Enhancement, Agility), Totem of the Trogg King (Restoration, Spirit), Idol of the
Inheritance (feral, Agility, Dodge).

**Shapes this list needs that do not exist yet** (the integration adds them in the one pending itemization file):
  - "Parry/Mastery/Versatility"  secondary, Even trio (14, 22, 23), requires a Strength primary like Dodge/Parry/
                                 Mastery 100 and Parry/Mastery 76: Glass-black Greaves
  - "Mastery/Versatility/Proc"    secondary, Even trio (22, 23, 33), no rule, modeled on Haste/Mastery/Proc 95:
                                 Stoneslayer
Every other shape exists (Haste/Versatility 35, Crit/Proc 39, Proc (Solo) 73, Crit/Mastery 30, Crit/Haste 29, Haste/
Mastery 33, Haste/Proc 40, Proc/CDH 86, CDH/Versatility 74, CDH (Solo) 72, Dodge/Versatility 87, Block/Versatility 91,
Parry/Versatility (Any) 83, Crit/Haste/Mastery 42, Crit/Mastery/Versatility 45, Crit/CDH 37, Dodge (Solo) 54 and the
Solo and Even pairs).

**Kept stock effects** (the stock rows' own spell slots; the stock spells are the same on every tier, a stock spell
cannot scale, and each effect item pays 0.7 of the budget, itemization-changes.md section 3):
  - Galgann's Fireblaster 9412 (`keep_spells=True`): Equip, Fire Blast 29633, a passive that triggers Fire Blast 29644
    (about 12 to 18 Fire damage, one target) on a ranged hit at 3 procs a minute (the stock `spell_proc` row; the doc
    calls it "chance on hit", the live row is an Equip slot)
  - Galgann's Firehammer 9419 (`keep_spells=True`): Chance on hit, Firebolt 18083 (ppm 2.2, about 80 to 112 Fire damage,
    one target)
  - Stoneslayer 9418 (`keep_spells=True`): Chance on hit, Strength of Stone 12731 (ppm 1.3; +10 Physical damage done
    for 8 sec, aura 13, a flat stock number)
  - Horned Viking Helmet 9394 and Olaf's All Purpose Shield 9404: Use, Reckless Charge 22641 (a charge at an enemy
    up to 30 yd away that triggers 13327, a 30 sec stun on the target, mechanic knockout, broken by damage; the stock
    "knocks you down" self-stun 22646 is a 1 ms DUMMY on the target with no script, so the wearer is never stunned, and
    the tooltip's "chance to fizzle" above level 60 has no code either) and Slow Fall 12438 (the wearer). Both stock
    cooldowns are 30 and 60 minutes, one use a session: the Gnomeregan G2 A ruling (a dungeon-usable item cooldown,
    the stock spell rows untouched) is applied by default, so they are declared with
    `spells=(use_spell(...cooldown=...),)` at 3 min each on every tier (designer question 3; QUESTIONS G2, ruled A).
Every stock stat spell slot folds into the budget (`absorbed_spell_slots`, the default): the Attack Power Equips of
Rockshard Pauldrons (9335) and Grimlok's Charge (9331). The Rockpounder and the other stock rows carry no spell slot.
Stoneslayer's class restriction (`AllowableClass` 1535) is the all-classes mask (every WotLK class bit), so it restricts
nothing and the item is left as stock.

**Stat changes and cleared columns.** Every doc stat has a point on every tier (tested on the materialized rows). The
stock rows lose their dead stats (Hit, Defense, Spell Power, Attack Power, Spirit on a ring, the lone Strength of the
staff: the shape replaces them) and their random properties (`RandomProperty=0`; seven rows carry one: Revelosh's four
pieces 863 / 1094 / 1157 / 716, Cragfists 782, Ironaya's Bracers 1096 and Archaedic Stone 3484, the last two with no
fixed stat at all; Zul'Farrak's Vice Grips and Runed Ring were cleared the same way, an owned copy keeps its rolled
property on top of the new shape). No stock row carries a resistance, a set or a limit category. Archaedic Stone keeps
its stock unique-equipped flag (`Flags` 0x80000): the flag is one per entry, so it limits one copy of each tier, not of
the item, and a Normal and a Heroic Stone can be worn together (the Zul'Farrak list's Unique entries, the same rule).

**Weapon-tier role cells.** Baelog's Shortbow (a bow of level 41, below 60) declares the 60-100 bow cell (0.405) on
every tier, as Scarlet Monastery's longbow and Blackrock's bows did: the 1-59 bow cell (0.269) to the 60-100 one is a
1.5x step. The three caster one-hand main-hands (Obsidian Shardblade, Hallshaper's Chisel, Galgann's Firehammer; their
level is below 60) declare the 60-100 physical cell (0.445) on every tier, like the earlier dungeons' caster main-hands
(blackrock_depths.py, scarlet_monastery.py, zul_farrak.py, gnomeregan.py); the Firehammer pays its kept proc on top
(0.445 x 0.7 = 0.3115, the Golemwright's Mending Rod precedent). The staff, the two-handers, the gun, the wand and the
two shields keep their own cells.

**Sockets.** The doc names no per-item pick, so every pick is a designer question (STAGE-UG-LIST report). The shared
rule (boss-rework-systems.md section 2; deadmines.py): about one standalone armor piece or weapon per boss carries 1,
a two-hander 2 (none here, as Zul'Farrak and Gnomeregan), trinkets and jewelry never, Normal tiers none (ladders.py).
The first socket is red on damage and healing gear and blue on tank gear. The socket bonus is a stock +4 rating (2874
Crit, 3267 Haste, 2871 Dodge, 3359 Parry): no enchant exists for Mastery, Versatility, Cooldown Haste or Proc Chance,
so a first secondary of those takes Haste or Crit. Picks, one per boss:

    Revelosh              Revelosh's Spaulders (Leather Agility shoulder)         red    +4 Crit
    The Lost Dwarves      Worn Running Boots (Leather Agility feet)               red    +4 Haste
    Ironaya               Girdle of the Makers' Hammer (Plate Intellect waist)    red    +4 Crit
    Obsidian Sentinel     Glass-black Greaves (Plate Tank legs)                   blue   +4 Parry
    Ancient Stone Keeper  Rockshard Pauldrons (Mail Intellect shoulder)           red    +4 Crit
    Galgann Firehammer    Shadowforge Blast Vest (Leather Tank chest)             blue   +4 Dodge
    Grimlok               Totemcarver's Gloves (Leather Spirit hands)             red    +4 Haste
    The Stone Keepers     Breastplate of the Restless Ring (Plate Strength chest) red    +4 Crit
    Archaedas             Disk-keeper's Helm (Mail Intellect head)                red    +4 Haste

Shadowforge Blast Vest, the dungeon's one Leather Tank armor piece, takes a quarter more Stamina (`extra_stamina=0.25`,
the Deadmines Smelting Pants, Zul'Farrak Stonegaze Girdle and Gnomeregan Shock Absorber Pads picks).
"""

from lib.dsl.items import Socket, item, use_spell

from .ladders import VANILLA_DUNGEON

# Socket bonus enchants (stock SpellItemEnchantment ids, +4 each; see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_DODGE_4 = 2871
BONUS_PARRY_4 = 3359

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does
EXTRA_STAMINA = 0.25  # "extra Stamina" on a tank piece: a quarter more than the tier's baseline

# The Normal item level of a new item per boss (the Gnomeregan G1 B rule): the highest stock item level among the stock
# items that stay on the boss (live item_template 2026-11-26). The Obsidian Sentinel and the Stone Keepers have no stock
# loot: their level is a designer question (the next boss's, and between Grimlok and Archaedas). Required level is the
# item level - 5 (the DSL default).
REVELOSH = 41           # Revelosh's Boots 41 / 40, Spaulders 41 / 36
IRONAYA = 42            # Ironshod Bludgeon and Ironaya's Bracers 42 / 37
OBSIDIAN_SENTINEL = 45  # no stock loot: the Ancient Stone Keeper's level
STONE_KEEPER = 45       # Cragfists, Rockshard Pauldrons 45 / 40
GALGANN = 47            # Galgann's Fireblaster and Flameseer Mantle 47 / 40
GRIMLOK = 47            # Grimlok's Tribal Vestments and Charge 47 / 40
STONE_KEEPERS = 47      # no stock loot: between Grimlok (47) and Archaedas (49)
ARCHAEDAS = 49          # The Rockpounder and Stoneslayer 49 / 40

# Bows, guns and crossbows need no ammo (source/world/ranged_weapons.py, hunter-rework Q3). An item() declaration owns
# its entry, so it sets the column itself and the minted tiers copy it.
NO_AMMO = 0

# Weapon-tier role cells (scarlet_monastery.py, the Blackrock gear review's S2): a caster main-hand or a bow below
# level 60 would take the 1-59 cell on its Normal tier and the 60-100 cell from Heroic up, a step the ladder check
# refuses over 1.5x. The 60-100 cell is declared on every tier instead, so the step is the budget curve's alone.
# physical InventoryType 13 ilvl 60-100: caster weapons take the physical budget (level60-stat-curve 1.8)
CASTER_MAIN_HAND_MULT = 0.445
# the same cell times the effect discount 0.7 (a caster one-hander with a kept proc: Galgann's Firehammer)
CASTER_MAIN_HAND_EFFECT_MULT = 0.3115
# physical InventoryType 15 ilvl 60-100: a bow below level 60 (scarlet_monastery.py, blackrock_depths.py)
BOW_MULT = 0.405

# The two stock Use effects keep their stock spell rows and get a dungeon-usable item cooldown (the Gnomeregan G2 A
# ruling, 2026-11-25, applied by default here: designer question 3), through the item's own spell columns
# (spellcooldown_1, the Dog Whistle precedent): the engine takes the item's cooldown over the spell's, so the stock
# spell rows stay untouched for every other user and every tier carries the same stock spell and cooldown.
SPELL_RECKLESS_CHARGE = 22641   # Horned Viking Helmet: charge, then a 30 sec stun on the target (stock cd 30 min)
SPELL_SLOW_FALL = 12438         # Olaf's All Purpose Shield: Slow Fall on the wearer (stock cooldown 60 min)
USE_COOLDOWN_MS = 180000        # 3 min

R, B = Socket.RED, Socket.BLUE

# ---------------------------------------------------------------------------------------------------------------------
# Revelosh (new items 41 / 36; the four stock pieces keep 41 / 40, 40 / 35, 41 / 36, 40 / 35)

# The four Revelosh pieces carry a Stamina line and a random property each (863, 1094, 1157, 716): cleared.
item("uldaman_reveloshs_boots", base=9387, RandomProperty=0, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste/Versatility")
item("uldaman_reveloshs_armguards", base=9388, RandomProperty=0, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Proc")
item("uldaman_reveloshs_spaulders", base=9389, RandomProperty=0, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Mastery", sockets=(R,), socket_bonus=BONUS_CRIT_4)
# Intellect and Proc Chance only (the Proc (Solo) shape).
item("uldaman_reveloshs_gloves", base=9390, RandomProperty=0, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Proc (Solo)")
item("uldaman_wand_of_the_wild_surge", name="Wand of the Wild Surge", like=11263, ilvl=REVELOSH, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Haste")

# ---------------------------------------------------------------------------------------------------------------------
# The Lost Dwarves, one list (Baelog, Eric and Olaf; no new item, the six stock items keep 40-43 / 35-38)

# Hit (a dead stat) goes; a bow below level 60 takes the 60-100 bow cell on every tier.
item("uldaman_baelogs_shortbow", base=9400, ammo_type=NO_AMMO, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)", budget_mult=BOW_MULT)
item("uldaman_nordic_longshank", base=9401, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Mastery")
# Plate with Agility becomes Strength; keeps its Use, Reckless Charge (22641), on a 3 min item cooldown.
item("uldaman_horned_viking_helmet", base=9394, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Mastery",
     spells=(use_spell(SPELL_RECKLESS_CHARGE, cooldown=USE_COOLDOWN_MS, category_cooldown=0),))
item("uldaman_worn_running_boots", base=9398, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste/Versatility", sockets=(R,), socket_bonus=BONUS_HASTE_4)
# The Strength tank shield; Defense (a dead stat) goes. Keeps its Use, Slow Fall (12438), on a 3 min item cooldown.
item("uldaman_olafs_all_purpose_shield", base=9404, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block/Versatility",
     spells=(use_spell(SPELL_SLOW_FALL, cooldown=USE_COOLDOWN_MS, category_cooldown=0),))
# The Intellect shield (a caster shield); Defense goes.
item("uldaman_battered_viking_shield", base=9403, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Mastery")

# ---------------------------------------------------------------------------------------------------------------------
# Ironaya (new items 42 / 37; the stock items keep 40-42 / 35-37)

item("uldaman_stoneweaver_leggings", base=9407, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste/Mastery")
# The Strength staff becomes the Agility tank staff (feral): Agility, Dodge, Versatility.
item("uldaman_ironshod_bludgeon", base=9408, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge/Versatility")
# No fixed stat today (a random property, 1096): fixed stats from the shape, the property cleared.
item("uldaman_ironayas_bracers", base=9409, RandomProperty=0, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Mastery")
# The archetype's one Uldaman Plate Intellect piece: one red socket, Crit bonus.
item("uldaman_girdle_of_the_makers_hammer", name="Girdle of the Makers' Hammer", like=10088, ilvl=IRONAYA,
     bonding=BOP, ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Mastery",
     sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("uldaman_pendant_of_two_lights", name="Pendant of Two Lights", like=20956, ilvl=IRONAYA, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary=None, secondary="Haste/Proc", primary_share=0)

# ---------------------------------------------------------------------------------------------------------------------
# The Obsidian Sentinel, a new boss (item level 45 / 40: designer question 1)

# Plate Tank legs: Strength, Parry, Mastery, Versatility (a new shape); one blue socket, Parry bonus.
item("uldaman_glass_black_greaves", name="Glass-black Greaves", like=13074, ilvl=OBSIDIAN_SENTINEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Parry/Mastery/Versatility",
     sockets=(B,), socket_bonus=BONUS_PARRY_4)
item("uldaman_mirrorglass_mantle", name="Mirrorglass Mantle", like=9881, ilvl=OBSIDIAN_SENTINEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste/Versatility")
item("uldaman_obsidian_shardblade", name="Obsidian Shardblade", like=6831, ilvl=OBSIDIAN_SENTINEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Mastery/Versatility",
     budget_mult=CASTER_MAIN_HAND_MULT)
# A ring: secondaries only.
item("uldaman_reforged_splinter", name="Reforged Splinter", like=11999, ilvl=OBSIDIAN_SENTINEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary=None, secondary="CDH/Versatility", primary_share=0)
# A trinket with no effect in the doc: stats only, Strength and Cooldown Haste.
item("uldaman_directive_core", name="Directive Core", like=4396, ilvl=OBSIDIAN_SENTINEL, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="CDH (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# The Ancient Stone Keeper (new items 45 / 40; the stock items are 45 / 40)

# Defense (a dead stat) goes; plate Strength tank hands.
item("uldaman_cragfists", base=9410, RandomProperty=0, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Dodge/Versatility")
# Mixed caster and melee today: Intellect only. The stock Equip (Attack Power 9335) folds into the budget.
item("uldaman_rockshard_pauldrons", base=9411, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Haste", sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("uldaman_duststorm_cloak", name="Duststorm Cloak", like=14656, ilvl=STONE_KEEPER, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit/Haste")
item("uldaman_sandscoured_wraps", name="Sandscoured Wraps", like=14654, ilvl=STONE_KEEPER, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Crit/Versatility")
# The Enhancement totem: stats only.
item("uldaman_totem_of_the_turning_wind", name="Totem of the Turning Wind", like=24413, ilvl=STONE_KEEPER,
     bonding=BOP, ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Galgann Firehammer (new items 47 / 42; the stock items are 46-47 / 40)

# A gun (no ammo); keeps its Equip, Fire Blast (29633, a passive that procs Fire Blast 29644 on a ranged hit).
item("uldaman_galganns_fireblaster", base=9412, keep_spells=True, ammo_type=NO_AMMO, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)")
# Keeps Firebolt on hit (18083); a caster main-hand below level 60 with an effect (0.445 x 0.7).
item("uldaman_galganns_firehammer", base=9419, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/Haste", budget_mult=CASTER_MAIN_HAND_EFFECT_MULT)
item("uldaman_flameseer_mantle", base=11310, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Crit/Haste")
item("uldaman_emberscale_cape", base=11311, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit/CDH")
# The dungeon's one Leather Tank armor piece: Agility, Dodge, Versatility, a quarter more Stamina, one blue socket.
item("uldaman_shadowforge_blast_vest", name="Shadowforge Blast Vest", like=15359, ilvl=GALGANN, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Dodge/Versatility", extra_stamina=EXTRA_STAMINA,
     sockets=(B,), socket_bonus=BONUS_DODGE_4)
item("uldaman_fuse_cutters_girdle", name="Fuse-cutter's Girdle", like=15588, ilvl=GALGANN, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste/Mastery")

# ---------------------------------------------------------------------------------------------------------------------
# Grimlok (new items 47 / 42; the stock items are 46-47 / 40)

item("uldaman_oilskin_leggings", base=9414, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Versatility")
item("uldaman_grimloks_tribal_vestments", base=9415, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste/Versatility")
# The stock Equip (Attack Power 9331) folds into the budget.
item("uldaman_grimloks_charge", base=9416, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit/Haste")
item("uldaman_totemcarvers_gloves", name="Totemcarver's Gloves", like=9952, ilvl=GRIMLOK, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Crit/Haste",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
# A neck: secondaries only.
item("uldaman_jadespine_collar", name="Jadespine Collar", like=12029, ilvl=GRIMLOK, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary=None, secondary="Proc/CDH", primary_share=0)
# The Restoration totem: stats only.
item("uldaman_totem_of_the_trogg_king", name="Totem of the Trogg King", like=22396, ilvl=GRIMLOK, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Haste (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# The Stone Keepers, a new boss (item level 47 / 42: designer question 1)

# Plate Strength chest: Strength, Mastery, Versatility, Crit; one red socket, Crit bonus.
item("uldaman_breastplate_of_the_restless_ring", name="Breastplate of the Restless Ring", like=8138,
     ilvl=STONE_KEEPERS, bonding=BOP, ladder=VANILLA_DUNGEON, primary="Strength (Solo)",
     secondary="Crit/Mastery/Versatility", sockets=(R,), socket_bonus=BONUS_CRIT_4)
item("uldaman_granite_shell_bracers", name="Granite-shell Bracers", like=14903, ilvl=STONE_KEEPERS, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Parry/Versatility (Any)")
item("uldaman_fault_line_sash", name="Fault Line Sash", like=4264, ilvl=STONE_KEEPERS, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Mastery/Versatility")
item("uldaman_keeper_trod_sabatons", name="Keeper-trod Sabatons", like=6423, ilvl=STONE_KEEPERS, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Crit/Versatility")
# The feral relic (Agility, Dodge): stats only.
item("uldaman_idol_of_the_inheritance", name="Idol of the Inheritance", like=25940, ilvl=STONE_KEEPERS,
     bonding=BOP, ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Dodge (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Archaedas (new items 49 / 44; the stock items are 47-49 / 40)

item("uldaman_the_rockpounder", base=9413, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit/Haste")
# Keeps Strength of Stone on hit (12731); Mastery, Versatility and Proc Chance (a new shape). The all-classes mask
# (AllowableClass 1535) restricts nothing and stays.
item("uldaman_stoneslayer", base=9418, keep_spells=True, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Mastery/Versatility/Proc")
# A ring with no fixed stat today (a random property, 3484): secondaries only, the property cleared.
item("uldaman_archaedic_stone", base=11118, RandomProperty=0, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/Mastery", primary_share=0)
item("uldaman_disk_keepers_helm", name="Disk-keeper's Helm", like=15602, ilvl=ARCHAEDAS, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Crit/Haste/Mastery",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("uldaman_hallshapers_chisel", name="Hallshaper's Chisel", like=7946, ilvl=ARCHAEDAS, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Crit/Mastery", budget_mult=CASTER_MAIN_HAND_MULT)
# The Holy relic: stats only.
item("uldaman_libram_of_the_awakened_hall", name="Libram of the Awakened Hall", like=23006, ilvl=ARCHAEDAS,
     bonding=BOP, ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="Haste (Solo)")
