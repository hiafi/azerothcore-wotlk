"""
The Shadowfang Keep loot (item variants, wave 1): the 24 approved list items and the 3 Archmage Arugal hard mode items
(docs/dungeons/shadowfang-keep-rework.md ## Loot, approved 2026-10-29, copied in docs/dungeons/dungeon-loot-vanilla.md).

Normal drops Rare at the item's stock level (20-29), Heroic is 66 Epic with the Heroic flag, then the three empowered
steps (ladders.py). Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only
the primary and secondary are listed. 19 of the items are stock entries (`base=`: the stock id is the Normal tier,
only the higher tiers are minted) and 5 are new (every tier minted, the look copied from a stock `like=` entry, the
level from the boss's lowest stock item level, required level 5 below it). Weapon, shield and held-in-off-hand budgets
follow the live role medians (stage F1): no `budget_mult` on them.

The Deathsworn Captain is a rare spawn (15%); his two items are declared like the others (nothing an archetype depends
on sits on him, the dungeon doc's rule).

**Sockets** (docs/dungeons/boss-rework-systems.md section 2, Loot lists; Normal tiers carry none, ladders.py): about
one socketed standalone piece or weapon per boss, 2 sockets on a two-hander; hard mode items carry 1, trinkets never.
The first socket is red on damage and healing gear and blue on tank gear; a second socket takes the color of the item's
first secondary (yellow: Crit, Haste, Mastery, Versatility; blue: Proc Chance, Cooldown Haste, MP5, Block, Dodge,
Parry; red: Strength, Agility, Intellect, Spirit). One-handers and the shield stay unsocketed: on their halved budgets
the socket cost eats most of the stats (stage F1 designer flag). Picks, one per boss:

    Rethilgore             Rugged Spaulders                 red              +4 Haste
    Razorclaw the Butcher  Bloody Apron                     red              +4 Crit (no Versatility enchant)
    Baron Silverlaine      Silverlaine Heirloom Legplates   red              +4 Crit
    Commander Springvale   Arced War Axe (2H)               red, yellow      +4 Haste (no Mastery enchant)
    Odo the Blindwatcher   Odo's Ley Staff (2H)             red, yellow      +4 Haste (no Mastery enchant)
    Deathsworn Captain     Haunting Blade (2H)              red, yellow      +4 Crit
    Fenrus the Devourer    Wolfhide-lined Pauldrons (tank)  blue             +4 Parry
    Wolf Master Nandos     Feline Mantle                    red              +4 Haste
    Archmage Arugal        Robes of Arugal                  red              +4 Crit
    Arugal, hard mode      Arugal's Shadow Tome, Ashcrombe's Locket: red, +4 Crit / +4 Haste; the Vial none (trinket)

**Socket bonus enchants** are stock SpellItemEnchantment rows (client DBC, all +4): 2874 Critical Strike, 3267 Haste,
3359 Parry. No enchant exists for Mastery, Versatility, Cooldown Haste or Proc Chance, so those items take a stock
throughput rating instead (the Deadmines precedent).

**Effects** (shadowfang_keep_hard_mode_effects.py, the `shadowfang_items` reservation 205600-205619): the three hard
mode items carry `budget_mult` 0.7 for their effect (itemization-changes.md section 3; the Tome is a held-in-off-hand
slot, so its role cell's median times 0.7, stage F1). The Vial and the Tome scale with the tier (`scale="budget"`,
stage IV10); the Locket has no number to scale. The Meteor Shard keeps its "Chance on hit: Firebolt", rebuilt on
potency, and scales too: its declared potency is the Heroic tier's (the vanilla dungeon ladder's effect reference), the
Normal tier gets a smaller copy and the empowered tiers larger ones (wave 1 integration). Every effect item is
unique-equipped across its tiers (IV10 follow-up 1, automatic).
"""

from lib.dsl.items import Socket, equip_spell, hit_spell, item, use_spell

from .ladders import VANILLA_DUNGEON, VANILLA_HARD_MODE
from .shadowfang_keep_hard_mode_effects import (
    arugals_shadow_tome_205601,
    ashcrombes_locket_205603,
    meteor_shard_firebolt_205604,
    vial_of_the_worgens_curse_205600,
)

# Socket bonus enchants (stock SpellItemEnchantment ids, see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_PARRY_4 = 3359

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does

ARMOR_SUBCLASS_LEATHER = 2
MATERIAL_LEATHER = 8

METEOR_SHARD_PPM = 2.0  # the stock item's spellppmRate_1

# ---------------------------------------------------------------------------------------------------------------------
# Rethilgore (stock item level 20)

# Leather Agility; one red socket, Haste bonus.
item("sfk_rugged_spaulders", base=5254, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
# Mail Agility: the jailer's belt.
item("sfk_cell_keepers_girdle", name="Cell Keeper's Girdle", like=15515, ilvl=20, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Agility (Solo)", secondary="Versatility (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Razorclaw the Butcher (stock item level 23-25)

item("sfk_butchers_slicer", base=6633, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit (Solo)")
# Cloth in stock, leather now (a butcher's leather apron): the stock row's subclass and material change on every tier
# (the Normal tier's Item.dbc row is re-emitted, item_emit DBC_FIELDS). One red socket; Versatility has no enchant, so
# the bonus is Crit.
item("sfk_bloody_apron", base=6226, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Versatility (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4,
     subclass=ARMOR_SUBCLASS_LEATHER, Material=MATERIAL_LEATHER)
item("sfk_butchers_cleaver", base=1292, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Haste (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Baron Silverlaine (stock item level 25-26)

# A noble's scepter as the healer and caster one-hand.
item("sfk_barons_scepter", base=6323, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Haste (Solo)")
# A ring carries secondaries only: Mastery and Versatility evenly, no primary (share 0).
item("sfk_silverlaines_family_seal", base=6321, ladder=VANILLA_DUNGEON,
     primary=None, secondary="Mastery/Versatility", primary_share=0)
# Plate Strength: the family's armor. One red socket, Crit bonus.
item("sfk_silverlaine_heirloom_legplates", name="Silverlaine Heirloom Legplates", like=7926, ilvl=25, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)

# ---------------------------------------------------------------------------------------------------------------------
# Commander Springvale (stock item level 26-28)

# Keep: the live row (Strength / Dodge, share 6000), only the tiers are new.
item("sfk_commanders_crest", base=6320, itemization="live", ladder=VANILLA_DUNGEON)
# Strength / Mastery two-hander: the second socket is yellow (Mastery is throughput); no Mastery enchant, Haste bonus.
item("sfk_arced_war_axe", base=3191, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Mastery (Solo)",
     sockets=(Socket.RED, Socket.YELLOW), socket_bonus=BONUS_HASTE_4)
# Plate Intellect: Springvale is a fallen paladin.
item("sfk_vambraces_of_the_fallen_commander", name="Vambraces of the Fallen Commander", like=14832, ilvl=26,
     bonding=BOP, ladder=VANILLA_DUNGEON, primary="Intellect (Solo)", secondary="CDH (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Odo the Blindwatcher (stock item level 26)

# Leather Spirit (a leather Intellect piece fits no archetype).
item("sfk_girdle_of_the_blindwatcher", base=6319, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste (Solo)")
# Spirit / Mastery staff: the second socket is yellow; no Mastery enchant, Haste bonus.
item("sfk_odos_ley_staff", base=6318, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Mastery (Solo)",
     sockets=(Socket.RED, Socket.YELLOW), socket_bonus=BONUS_HASTE_4)
# Mail Intellect.
item("sfk_watchtower_coif", name="Watchtower Coif", like=15533, ilvl=26, bonding=BOP, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Versatility (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Deathsworn Captain, rare spawn (stock item level 25-26)

# The stock +28 attack power equip spell 9335 folds into the budget (absorbed): the attack power becomes the Strength
# primary. Strength / Crit two-hander, the second socket yellow (Crit), Crit bonus.
item("sfk_haunting_blade", base=6641, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED, Socket.YELLOW), socket_bonus=BONUS_CRIT_4)
# Mail Strength fits no archetype: an extra Mail Agility piece.
item("sfk_phantom_armor", base=6642, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Proc (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# Fenrus the Devourer (stock item level 26)

# A tank back.
item("sfk_fenrus_hide", base=6340, ladder=VANILLA_DUNGEON,
     primary="Strength (Solo)", secondary="Block (Solo)")
# Leather Tank: Agility, Dodge and extra Stamina (a quarter more than the baseline, paid from the item's own budget,
# the Deadmines Smelting Pants precedent).
item("sfk_black_wolf_bracers", base=3230, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Dodge (Solo)", extra_stamina=0.25)
# Plate Tank: one blue socket, Parry bonus.
item("sfk_wolfhide_lined_pauldrons", name="Wolfhide-lined Pauldrons", like=14909, ilvl=26, bonding=BOP,
     ladder=VANILLA_DUNGEON, primary="Strength (Solo)", secondary="Parry (Solo)",
     sockets=(Socket.BLUE,), socket_bonus=BONUS_PARRY_4)

# ---------------------------------------------------------------------------------------------------------------------
# Wolf Master Nandos (stock item level 26-27)

# Cloth Spirit; the stock Intellect / Spirit / Spell Power split goes. One red socket, Haste bonus.
item("sfk_feline_mantle", base=3748, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="Haste (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4)
# Keep: the live row (Agility / Dodge, share 4000), only the tiers are new.
item("sfk_wolfmaster_cape", base=6314, itemization="live", ladder=VANILLA_DUNGEON)

# ---------------------------------------------------------------------------------------------------------------------
# Archmage Arugal (stock item level 29)

# Cloth Intellect; the stock split primary goes. One red socket, Crit bonus.
item("sfk_robes_of_arugal", base=6324, ladder=VANILLA_DUNGEON,
     primary="Intellect (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4)
# Cloth Spirit.
item("sfk_belt_of_arugal", base=6392, ladder=VANILLA_DUNGEON,
     primary="Spirit (Solo)", secondary="CDH (Solo)")
# Agility / Proc Chance dagger that keeps its "Chance on hit: Firebolt" (stock 13442, rebuilt on potency as 205604;
# the stock spell slot is replaced). An effect item: unique-equipped across its tiers (the stock row is already
# unique-equipped, Flags 0x80000).
item("sfk_meteor_shard", base=6220, ladder=VANILLA_DUNGEON,
     primary="Agility (Solo)", secondary="Proc (Solo)",
     spells=(hit_spell(meteor_shard_firebolt_205604, ppm=METEOR_SHARD_PPM, scale="budget"),))

# ---------------------------------------------------------------------------------------------------------------------
# Archmage Arugal, hard mode Face Him Alone (heroic hard mode 71, then 81 / 91 / 101). New items, no stock level: the
# ladder sets every tier.

# Use (2 min): Haste rating and +30% movement speed for 15 sec. A trinket with a stat: Crit only, no primary (share 0).
item("sfk_vial_of_the_worgens_curse", name="Vial of the Worgen's Curse", like=28579, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary=None, secondary="Crit (Solo)", primary_share=0, budget_mult=0.7,
     spells=(use_spell(vial_of_the_worgens_curse_205600, scale="budget"),))
# Equip: damaging spells have a chance to call an Arugal's Voidwalker for 10 sec, which attacks the target. Held in
# off-hand, Intellect / Crit, one red socket (Crit bonus). Weapon-tier slot: the role cell's budget times 0.7.
item("sfk_arugals_shadow_tome", name="Arugal's Shadow Tome", like=19989, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Intellect (Solo)", secondary="Crit (Solo)",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(arugals_shadow_tome_205601, scale="budget"),))
# Use (2 min): removes all Curses from a friendly target and wards it against new ones for 6 sec. Neck: secondaries
# only (Haste / Mastery evenly, share 0), one red socket (Haste bonus). No number to scale: one spell on every tier.
item("sfk_ashcrombes_locket", name="Ashcrombe's Locket", like=28217, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Haste/Mastery", primary_share=0, budget_mult=0.7,
     sockets=(Socket.RED,), socket_bonus=BONUS_HASTE_4,
     spells=(use_spell(ashcrombes_locket_205603),))
