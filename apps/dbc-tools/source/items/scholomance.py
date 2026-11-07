"""
The Scholomance loot (wave 1 dungeon items): the 52 approved list items and the 6 hard mode items of Ras Frostwhisper
and Darkmaster Gandling (docs/dungeons/scholomance-rework.md ## Loot, approved 2026-11-02, copied in
docs/dungeons/dungeon-loot-vanilla.md). The Haunted set tokens and set pieces are their own track and not declared here.

Normal drops Rare at the item's stock level (Scholomance is a level 60 dungeon: the stock items sit at 59-65, the
loot ladder's "Normal, level 60 dungeons: stock, about 60"), Heroic is 66 Epic with the Heroic flag, then the three
empowered steps (ladders.py). Shapes are `item_shape.name` strings; every item also gets the budget's baseline
Stamina, so only the primary and secondary are listed. 42 of the list items are stock entries (`base=`: the stock id
is the Normal tier, only the higher tiers are minted) and 10 are new (every tier minted, the look copied from a stock
`like=` entry, the level from the boss's lowest stock item level on the list, required level 5 below).

**Normal tier quality.** Alanna's Embrace and Headmaster's Charge are stock Epics; the Normal tier is Rare like every
other list item (normal drops rare, boss-rework-systems section 2), so both take quality=Rare.

**Former sets** (Structure 3, approved 2026-11-01): Necropile (122), Cadaverous (121), Deathbone (124) and Bloodmail
(123) lose their set bonus, so the kept pieces clear `itemset` on every tier, the Normal tier included.

**Look changes on stock entries.** Ghostloom Leggings come back as Cloth Spirit legs (stock leather): cloth subclass,
cloth material and the Haunting Specter Leggings' look (11929). Detention Strap becomes a mail wrist strap (stock
waist): wrist slot and the Loomguard Armbraces' look (13969). The new look ships through item_dbc and the client
Item.dbc like any minted row.

**Unpriced stock extras are cleared on every tier**: the stock resistances (Rattlecage Buckler, Corpselight Greaves,
Skullsmoke Pants, Shadowy Mail Greaves, Boots of the Shrieker) and the Dimly Opalescent Ring's random property
(3306, a random "of the ..." suffix). The budget neither prices nor scales them, so a minted tier would copy them for
free, and the list names only the primary and secondary.

**Kept stock effects** (`keep_spells=True`, the designer's "keeps ..."): Barovian Family Sword (Siphon Health 18652 on
hit), Frightskull Shaft (Weakening Disease 18633), Ebon Hilt of Marduk (Corruption 18656), Silent Fang (Silence 18278),
Headmaster's Charge (Use: party Intellect 18264). They are stock spells, the same on every tier (not potency). Every
other stock equip spell (the old +AP / Defense / block / healing equip lines, the two relics' class effects) folds into
the budget through `absorbed_spell_slots` (the item() default), so the item carries only its list stats.

**New effects** (scholomance_hard_mode_effects.py, the `scholomance_items` spell reservation 205620-205659): Spare Rib,
Jar of Torn Souls, Rib Spreader, Polkelt's Specimen Launcher, The Dean's Rod and Krastinov's Suture Kit on the normal
list, and all six hard mode items. An effect with damage, healing, an absorb or a stat aura (Spare Rib's armor, the
Jar's Intellect) is declared with scale="budget" (stage IV10): the declared numbers are the ladder's effect reference
tier's (Heroic 66 on the list, 71 in hard mode), every other tier carries its own copies, potency and stat aura amounts
times its stat budget over the reference's (wave 1 integration). The Phylactery Shard's armor stays one number (its
script casts the heal by id; see the STAGE-W1-INTEGRATION report). Every effect item is unique-equipped across its
tiers (IV10 follow-up 1, automatic).

**Sockets** (scholomance-rework.md Loot, Sockets, approved 2026-11-02; from Heroic up, the Normal tier has none, user
2026-11-06). The first socket is red on damage and healing gear and blue on tank gear; a second socket takes the color
of the item's first secondary (docs/Systems.md "Sockets and gems"):
    yellow (throughput)   Crit, Haste, Mastery, Versatility
    blue (utility)        Proc Chance, Cooldown Haste, MP5, Block, Dodge, Parry
    red (primary)         Strength, Agility, Intellect, Spirit
The socket bonus is a stock +4 secondary rating (the Deadmines precedent; one enchant per item, so it does not scale):
2874 Crit, 3267 Haste, 2972 Block, 3359 Parry, 2371 MP5. No enchant exists for Mastery or Versatility, so a Mastery
item takes Haste and a Versatility item takes Crit, as in Deadmines.

**Hard mode items** (ladder `vanilla_hard_mode`, 71 / 81 / 91 / 101): one item on every hard mode kill, on top of the
heroic loot. Effect items carry `budget_mult` 0.7 for the effect (itemization-changes.md section 3), except Transfer
Papers (1.0: its Use adds no throughput, approved 2026-11-02). One socket on the Chillband, the Bonechill Blade, the
Honor Roll Ribbon and the Portal Rod; trinkets never.
"""

from lib.dsl.items import Quality, Socket, equip_spell, item, use_spell

from .ladders import VANILLA_DUNGEON, VANILLA_HARD_MODE
from .scholomance_hard_mode_effects import (
    bonechill_blade_205635,
    darkmasters_portal_rod_205640,
    frostwhispers_chillband_205633,
    honor_roll_ribbon_205638,
    jar_of_torn_souls_205621,
    krastinovs_suture_kit_205629,
    phylactery_shard_205631,
    polkelts_specimen_launcher_205625,
    rib_spreader_205623,
    spare_rib_205620,
    the_deans_rod_205627,
    transfer_papers_205637,
)

# Socket bonus enchants (stock SpellItemEnchantment ids, +4 each; see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_BLOCK_4 = 2972
BONUS_PARRY_4 = 3359
BONUS_MP5_4 = 2371

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does
RARE = Quality.RARE
NO_SET = {"itemset": 0}  # a former Scholomance set piece: no set bonus on any tier (Structure 3)

R, Y, B = Socket.RED, Socket.YELLOW, Socket.BLUE

# ---------------------------------------------------------------------------------------------------------------------
# Jandice Barov (stock item level 61-62). Also drops the Haunted belt token (not here).

# Keeps Siphon Health on hit (stock 18652).
item("scholo_barovian_family_sword", base=14541, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Versatility (Solo)", keep_spells=True)
item("scholo_phantasmal_cloak", base=18689, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit (Solo)")
# Plate Tank legs: two blue sockets (Parry is blue), Parry bonus.
item("scholo_wraithplate_leggings", base=18690, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Parry (Solo)",
     sockets=(B, B), socket_bonus=BONUS_PARRY_4)
item("scholo_staff_of_metanoia", base=22394, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery (Solo)")
# Back as Cloth Spirit legs (stock leather, 2026-11-02): cloth, and a cloth look (Haunting Specter Leggings 11929).
item("scholo_ghostloom_leggings", base=14545, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Versatility (Solo)",
     subclass=1, Material=7, displayid=28736)

# ---------------------------------------------------------------------------------------------------------------------
# Rattlegore (stock item level 59-62). Also drops the Viewing Room Key (kept, not here).

item("scholo_rattlecage_buckler", base=14528, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery (Solo)", shadow_res=0)
# Keeps Weakening Disease on hit (stock 18633).
item("scholo_frightskull_shaft", base=14531, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste (Solo)", keep_spells=True)
# The dungeon's one Plate Intellect piece: one red socket, Haste bonus.
item("scholo_corpselight_greaves", base=14537, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)", shadow_res=0,
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
# New tank trinket: Dodge only, Use: +armor (205620). Rattlegore's lowest stock item level on the list is 59
# (Frightskull Shaft). Workaround: the Dodge shapes require a Strength or Agility primary (item_shape_rule), so the
# Null primary is refused; Agility (Solo) at primary_share 0 satisfies the rule and puts the whole budget on Dodge,
# which is the list's "Dodge" (the primary line rounds to nothing and is not written).
item("scholo_spare_rib", name="Spare Rib", like=19992, ilvl=59, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge (Solo)", primary_share=0,
     spells=(use_spell(spare_rib_205620, scale="budget"),))

# ---------------------------------------------------------------------------------------------------------------------
# Marduk Blackpool and Vectus (stock item level 59-61). Marduk also drops the Haunted gloves token (not here).

# Keeps Corruption on hit (stock 18656).
item("scholo_ebon_hilt_of_marduk", base=14576, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Proc (Solo)", keep_spells=True)
item("scholo_death_knight_sabatons", base=18692, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Mastery (Solo)")
# Intellect / Haste legs: red, then yellow (Haste), Haste bonus.
item("scholo_skullsmoke_pants", base=14577, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)", fire_res=0, shadow_res=0,
     sockets=(R, Y), socket_bonus=BONUS_HASTE_4)
# The wave's first normal neck: secondaries only.
item("scholo_dark_advisors_pendant", base=18691, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/Versatility", primary_share=0)

# ---------------------------------------------------------------------------------------------------------------------
# Ras Frostwhisper (stock item level 62): two items per kill. Also drops the Haunted shoulders token (not here).

# Stock Epic: Rare on the Normal tier. Spirit / Mastery: red, then yellow (Mastery), Haste bonus.
item("scholo_alannas_embrace", base=13314, quality=RARE, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Mastery (Solo)",
     sockets=(R, Y), socket_bonus=BONUS_HASTE_4)
item("scholo_iceblade_hacker", base=13952, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)")
item("scholo_maelstrom_leggings", base=14522, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Mastery (Solo)",
     sockets=(R, Y), socket_bonus=BONUS_HASTE_4)
item("scholo_shadowy_mail_greaves", base=18694, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Versatility (Solo)", shadow_res=0)
item("scholo_spellbound_tome", base=18695, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste (Solo)")
item("scholo_intricately_runed_shield", base=18696, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Versatility (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Instructor Malicia (stock item level 61)

item("scholo_necropile_robe", base=14626, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Versatility (Solo)",
     sockets=(R, Y), socket_bonus=BONUS_CRIT_4, **NO_SET)
item("scholo_cadaverous_leggings", base=14638, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)", **NO_SET)
item("scholo_dimly_opalescent_ring", base=18684, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Haste/Versatility", primary_share=0, RandomProperty=0)
# New caster trinket, Equip: stacking Intellect (205621).
item("scholo_jar_of_torn_souls", name="Jar of Torn Souls", like=13544, ilvl=61, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)",
     spells=(equip_spell(jar_of_torn_souls_205621, scale="budget"),))

# ---------------------------------------------------------------------------------------------------------------------
# Doctor Theolen Krastinov (stock item level 61)

item("scholo_cadaverous_armor", base=14637, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)",
     sockets=(R, Y), socket_bonus=BONUS_HASTE_4, **NO_SET)
# Stock set piece restored in place of the Gauntlets (2026-11-02).
item("scholo_deathbone_sabatons", base=14621, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block (Solo)", **NO_SET)
item("scholo_hammer_of_the_vesper", base=18683, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste (Solo)")
# New healer trinket: Haste and MP5, no primary, Use: stitch the next 3 direct heals' targets (205629, heal potency).
item("scholo_krastinovs_suture_kit", name="Krastinov's Suture Kit", like=11819, ilvl=61, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary=None, secondary="MP5/Haste", primary_share=0,
     spells=(use_spell(krastinovs_suture_kit_205629, scale="budget"),))
# New fist weapon, Equip: a bleed on melee hits (205623, attack power potency).
item("scholo_rib_spreader", name="Rib Spreader", like=18462, ilvl=61, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)",
     spells=(equip_spell(rib_spreader_205623, scale="budget"),))

# ---------------------------------------------------------------------------------------------------------------------
# Lorekeeper Polkelt (stock item level 61)

# Stock set piece restored in place of the Gloves (2026-11-02).
item("scholo_cadaverous_walkers", base=14641, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Mastery (Solo)", **NO_SET)
# New name, replaces the Bloodmail Gauntlets (2026-11-02); a mail wrist look (Demon Howl Wristguards 18394).
item("scholo_bloodmail_bracers", name="Bloodmail Bracers", like=18394, ilvl=61, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)")
# The list says Spirit and MP5, but every MP5 shape forbids a Spirit primary (item_shape_rule): provisional Haste
# secondary (designer question), red then yellow (Haste); the MP5 stays as the socket bonus.
item("scholo_ghoul_skin_leggings", base=18682, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste (Solo)",
     sockets=(R, Y), socket_bonus=BONUS_MP5_4)
# New gun, Equip: an acid pool on ranged hits (205625, ranged attack power potency).
item("scholo_polkelts_specimen_launcher", name="Polkelt's Specimen Launcher", like=16992, ilvl=61, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Haste (Solo)", ammo_type=0,
     spells=(equip_spell(polkelts_specimen_launcher_205625, scale="budget"),))

# ---------------------------------------------------------------------------------------------------------------------
# The Ravenian and Master Corvane (stock item level 61)

# Plate Tank chest: two blue sockets (Block is blue), Block bonus.
item("scholo_deathbone_chestplate", base=14624, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block (Solo)",
     sockets=(B, B), socket_bonus=BONUS_BLOCK_4, **NO_SET)
# Stock set piece restored in place of the Leggings (2026-11-02).
item("scholo_necropile_boots", base=14631, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Versatility (Solo)", **NO_SET)
# ammo_type 0 (no ammo, hunter rework Q3): stated here so every minted tier keeps it. source/world/ranged_weapons.py
# also declares item_template(18680, ammo_type=0) and must skip item()-owned entries (one owner per entry).
item("scholo_ancient_bone_bow", base=18680, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)", ammo_type=0)
# New Agility tank staff (the Leather Tank archetype's one item): Agility, Dodge and extra Stamina (a quarter more than
# the baseline, paid from the item's own budget, the Deadmines Smelting Pants' value).
item("scholo_corvanes_goad", name="Corvane's Goad", like=13372, ilvl=61, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge (Solo)", extra_stamina=0.25)

# ---------------------------------------------------------------------------------------------------------------------
# Lord Alexei Barov (stock item level 61-65)

item("scholo_bloodmail_hauberk", base=14611, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)",
     sockets=(R, Y), socket_bonus=BONUS_CRIT_4, **NO_SET)
# Gains Stamina; the stock class effect (28853) folds into the budget.
item("scholo_libram_of_divinity", base=23201, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)")
# New Plate Strength chest (approved 2026-11-02).
item("scholo_barov_heirs_breastplate", name="Barov Heir's Breastplate", like=12970, ilvl=61, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Crit (Solo)")
# New Strength tank mace, Equip: parries give the attacker a Demerit (205627).
item("scholo_the_deans_rod", name="The Dean's Rod", like=13349, ilvl=61, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Parry (Solo)",
     spells=(equip_spell(the_deans_rod_205627),))

# ---------------------------------------------------------------------------------------------------------------------
# Lady Illucia Barov (stock item level 61-65)

item("scholo_necropile_cuffs", base=14629, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Versatility (Solo)", **NO_SET)
item("scholo_bloodmail_legguards", base=14612, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Crit (Solo)",
     sockets=(R, Y), socket_bonus=BONUS_CRIT_4, **NO_SET)
# Gains Stamina; resto shaman (2026-11-02); the stock class effect (28856) folds into the budget.
item("scholo_totem_of_sustaining", base=23200, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="MP5 (Solo)")
# New Spirit cloak (approved 2026-11-02).
item("scholo_shroud_of_foresight", name="Shroud of Foresight", like=13386, ilvl=61, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Spirit (Solo)", secondary="Haste (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Darkmaster Gandling (stock item level 62-63): two items per kill. Also drops the Haunted helmet token (not here).

# Stock Epic: Rare on the Normal tier. Keeps Use: party Intellect (stock 18264).
item("scholo_headmasters_charge", base=13937, quality=RARE, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste (Solo)", keep_spells=True)
item("scholo_don_mauricios_band", base=22433, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Crit/Mastery", primary_share=0)
item("scholo_witchblade", base=13964, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)")
# Keeps Silence on hit (stock 18278).
item("scholo_silent_fang", base=13953, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Proc (Solo)", keep_spells=True)
item("scholo_vigorsteel_vambraces", base=13951, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Haste (Solo)",
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
item("scholo_bonecreeper_stylus", base=13938, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste (Solo)")
item("scholo_boots_of_the_shrieker", base=13398, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste (Solo)", shadow_res=0,
     sockets=(R,), socket_bonus=BONUS_HASTE_4)
# Becomes a wrist strap (stock waist, 2026-11-02): wrist slot and a mail wrist look (Loomguard Armbraces 13969).
item("scholo_detention_strap", base=13950, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Versatility (Solo)",
     InventoryType=9, displayid=24793)

# ---------------------------------------------------------------------------------------------------------------------
# Ras Frostwhisper, hard mode (the Torn Keepsake): heroic hard mode 71, then 81 / 91 / 101. New items, no stock level.

# Tank trinket, Use: armor, then a heal for 30% of the damage taken meanwhile (205631, scripted; no potency, so one
# spell serves every tier).
item("scholo_phylactery_shard", name="Phylactery Shard", like=10659, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Versatility (Solo)", primary_share=0, budget_mult=0.7,
     spells=(use_spell(phylactery_shard_205631),))
# Ring, Equip: Chill on damaging hits (205633). Secondaries only; one red socket, Haste bonus (Mastery leads).
item("scholo_frostwhispers_chillband", name="Frostwhisper's Chillband", like=18760, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary=None, secondary="Haste/Mastery", primary_share=0, budget_mult=0.7,
     sockets=(R,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(frostwhispers_chillband_205633),))
# Caster sword (the stock Bonechill Hammer moved here as a sword), Equip: Frost Blast on harmful spells (205635,
# spell power potency). One red socket, Crit bonus.
item("scholo_bonechill_blade", name="Bonechill Blade", like=12797, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Intellect (Solo)", secondary="Crit (Solo)",
     sockets=(R,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(bonechill_blade_205635, scale="budget"),))

# ---------------------------------------------------------------------------------------------------------------------
# Darkmaster Gandling, hard mode (the honors program): heroic hard mode 71, then 81 / 91 / 101.

# Trinket, Use: swap places with a party member (205637, scripted). Full stat budget (budget_mult 1.0, approved
# 2026-11-02): the Use adds no damage or healing.
item("scholo_transfer_papers", name="Transfer Papers", like=19343, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Crit/Haste", primary_share=0, budget_mult=1.0,
     spells=(use_spell(transfer_papers_205637),))
# Neck, Equip: the Honor Roll shield every 30 sec (205638, absorb potency). One red socket, Haste bonus (Mastery leads).
item("scholo_honor_roll_ribbon", name="Honor Roll Ribbon", like=15799, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Mastery/Versatility", primary_share=0, budget_mult=0.7,
     sockets=(R,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(honor_roll_ribbon_205638, scale="budget"),))
# Held in off-hand, Equip: a portal fires arcane missiles on damaging spells (205640, spell power potency). One red
# socket, Haste bonus.
item("scholo_darkmasters_portal_rod", name="Darkmaster's Portal Rod", like=22329, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Intellect (Solo)", secondary="Haste (Solo)",
     sockets=(R,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(darkmasters_portal_rod_205640, scale="budget"),))
