"""
The twelve Scarlet Monastery hard mode items (docs/dungeons/scarlet-monastery-rework.md ## Loot, "Hard mode lists",
approved 2026-11-19, ruling 59; copied in docs/dungeons/dungeon-loot-vanilla.md): one drops on every hard mode kill of
Bloodmage Thalnos (the Desecration), Arcanist Doan (the Kel'Thuzad Heresy), Herod (Call to Arms) and High Inquisitor
Whitemane (The Truth), on top of the heroic list item and the Zealot's token. No loot tables here (the dungeon build's
loot stage wires them; map 189 has no heroic creature bodies yet). The 64 boss list items are scarlet_monastery.py,
the Zealot's set zealot_set.py.

All twelve are new items on the hard mode ladder (`vanilla_hard_mode`: 71 / 81 / 91 / 101 Epic, required level 60,
ladders.py), Bind on Pickup, unique-equipped across their tiers (automatic for an effect item), and pay 0.7 of the
budget (the effect discount, the default). Keys `sm_`. The look of each is a stock item (`like=`, look only, a
designer question); none is an item of the Scarlet Monastery lists.

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and the
secondaries are listed, in the doc's order (the two-stat shapes are Even, so the order does not matter). The ring and
the neck carry secondaries only (`primary=None`, share 0). The two trinkets keep their doc primary (Strength,
Intellect). No new shape is needed.

**Effects**: scarlet_monastery_hard_mode_effects.py (the `scarlet_monastery_items` reservation 212000-212099).
Effects whose numbers grow with item level are `scale="budget"` (every tier above 71 carries its own copies):
the Censer's fire, the Signet's shield, the Shard's absorb, the Wand's Icy Death, the Grips' fissure, the Rifle's
volley, the Bulwark's and the Staff's pillars, the Verdict, and (review m5, 2026-11-20) the Rallying Standard's 5% and
Treads of Denial's 10%, percents declared `scale_amount=True` so they grow with the tier. The Rosary's Versatility is a
percent that stays one spell (the default the designer kept).

**Sockets** (the doc names none; the shared rule, boss-rework-systems section 2): every hard mode item carries 1,
trinkets none. The first socket is red on damage and healing gear and blue on tank gear (the Bulwark and the Treads);
the socket bonus is the stock +4 rating of the first secondary (Crit 2874, Haste 3267, Block 2972, Parry 3359;
Mastery takes Haste, Versatility takes Crit: no enchant exists for the custom stats). A designer question.

**Declared multipliers** (the Blackrock gear fix pass, REVIEW S1 and S3): on a weapon-tier slot the role cell times
the effect discount can leave a socketed item 1 point of a doc stat, and the 101 tier's 101-200 cell is a TBC-fit
jump (the bucket step guard). The staff and the two-hand sword take their 60-100 cell times 0.7 on every tier (the
Scepter of the Molten Lake's and Theldren's Executioner's numbers); the shield, the gun and the wand take the 0.6 floor
of the thin socketed hard mode weapons (Black Anvil Bulwark); the held-in-off-hand Censer keeps its cell (0.965 at
60-100, 0.99 at 101-200: no jump).
"""

from lib.dsl.items import Socket, equip_spell, item, use_spell

from .ladders import VANILLA_HARD_MODE
from .scarlet_monastery_hard_mode_effects import (
    fairbells_censer_212003,
    fathers_verdict_212018,
    fissure_touched_grips_212010,
    garrison_bulwark_212014,
    heretics_wand_212008,
    inquisitors_rosary_212022,
    pureblood_rallying_standard_212000,
    scarlet_garrison_rifle_212012,
    shard_of_the_phylactery_212007,
    staff_of_the_consecrated_hall_212016,
    treads_of_denial_212020,
    voss_blessed_signet_212005,
)

# Socket bonus enchants (stock SpellItemEnchantment ids, +4 each; see the module docstring).
BONUS_CRIT_4 = 2874
BONUS_HASTE_4 = 3267
BONUS_BLOCK_4 = 2972
BONUS_PARRY_4 = 3359

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does
R, B = Socket.RED, Socket.BLUE

# Declared multipliers (module docstring), the same numbers as blackrock_depths.py's:
# physical InventoryType 17 ilvl 60-100 0.791 x the effect discount 0.7 (level60-stat-curve 1.8)
HM_CASTER_TWO_HAND_MULT = 0.5537
HM_PHYSICAL_TWO_HAND_MULT = 0.5537       # physical InventoryType 17 Quality 4 ilvl 60-100 0.791 x 0.7
HM_PHYSICAL_TWO_HAND_DPS = 0.0695        # ... and its DPS fraction
HM_SOCKETED_THIN_MULT = 0.6              # socketed hard mode one-hander, ranged weapon or shield with an effect
# The wand's DPS fraction, pinned to the 60-100 cell on every tier: the 101 tier's 101-200 cell is not frozen for a
# wand, and without it the 101 tier spent its stat budget on DPS (half the 91 tier's stats). The gun declares none: a
# bow, gun or crossbow takes dps_delta 0 on every tier (level60-stat-curve 1.8, the hunter ranged rule).
HM_WAND_DPS = -0.2                       # caster InventoryType 26 Quality 4 ilvl 60-100

# Bows and guns need no ammo (source/world/ranged_weapons.py, hunter-rework Q3); an item() declaration owns its entry,
# so it sets the column itself and the minted tiers copy it.
NO_AMMO = 0

# ---------------------------------------------------------------------------------------------------------------------
# Bloodmage Thalnos, the Desecration (the four risen heroes): hard mode (heroic hard mode 71, then 81 / 91 / 101).

# Use (2 min): Galvar's banner, +5% damage to the party near it for 15 sec, a 2 min Recently Rallied lockout (a
# percent: unscaled). A trinket: no socket.
item("sm_purebloods_rallying_standard", name="Pureblood's Rallying Standard", like=12846, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Strength (Solo)", secondary="Haste/Mastery",
     spells=(use_spell(pureblood_rallying_standard_212000, scale="budget"),))
# Held in off-hand, Equip: damaging spells may set the target alight, a 3 stack Fire DoT (scaled). One red socket.
item("sm_fairbells_censer", name="Fairbell's Censer", like=7344, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Intellect (Solo)", secondary="Crit/Mastery",
     sockets=(R,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(fairbells_censer_212003, scale="budget"),))
# Ring, Equip: direct heals may shield the target (scaled). Secondaries only. One red socket.
item("sm_voss_blessed_signet", name="Voss's Blessed Signet", like=20505, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Crit/Haste", primary_share=0,
     sockets=(R,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(voss_blessed_signet_212005, scale="budget"),))

# ---------------------------------------------------------------------------------------------------------------------
# Arcanist Doan, the Kel'Thuzad Heresy: hard mode.

# Use (2 min): an absorb for 15 sec, +10% spell damage and healing while it holds (the absorb scaled). A trinket: no
# socket.
item("sm_shard_of_the_phylactery", name="Shard of the Phylactery", like=20534, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Intellect (Solo)", secondary="Haste/Versatility",
     spells=(use_spell(shard_of_the_phylactery_212007, scale="budget"),))
# Wand, Equip: damaging spells may apply Icy Death, Frost over time and a 30% slow (scaled). One red socket.
item("sm_heretics_wand", name="Heretic's Wand", like=7514, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Intellect (Solo)", secondary="Crit (Solo)", budget_mult=HM_SOCKETED_THIN_MULT,
     extra_dps=HM_WAND_DPS, sockets=(R,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(heretics_wand_212008, scale="budget"),))
# Leather hands, Equip: melee abilities may open a Shadow Fissure under the target (scaled). One red socket.
item("sm_fissure_touched_grips", name="Fissure-touched Grips", like=18238, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Agility (Solo)", secondary="Haste/Versatility",
     sockets=(R,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(fissure_touched_grips_212010, scale="budget"),))

# ---------------------------------------------------------------------------------------------------------------------
# Herod, Call to Arms: hard mode.

# Gun, Equip: ranged attacks may call a garrison volley (scaled). One red socket. No ammo.
item("sm_scarlet_garrison_rifle", name="Scarlet Garrison Rifle", like=10510, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Agility (Solo)", secondary="Crit/Haste", budget_mult=HM_SOCKETED_THIN_MULT,
     sockets=(R,), socket_bonus=BONUS_CRIT_4, ammo_type=NO_AMMO,
     spells=(equip_spell(scarlet_garrison_rifle_212012, scale="budget"),))
# Strength tank shield, Equip: blocks may call a pillar of Light that heals the wearer (scaled). One blue socket (tank
# gear), Block bonus.
item("sm_garrison_bulwark", name="Garrison Bulwark", like=10195, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Strength (Solo)", secondary="Block/Mastery", budget_mult=HM_SOCKETED_THIN_MULT,
     sockets=(B,), socket_bonus=BONUS_BLOCK_4,
     spells=(equip_spell(garrison_bulwark_212014, scale="budget"),))
# Staff, Equip: direct heals may call a pillar of Light that heals the target's party nearby (scaled). One red socket.
item("sm_staff_of_the_consecrated_hall", name="Staff of the Consecrated Hall", like=2271, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Spirit (Solo)", secondary="Crit/Versatility",
     budget_mult=HM_CASTER_TWO_HAND_MULT, sockets=(R,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(staff_of_the_consecrated_hall_212016, scale="budget"),))

# ---------------------------------------------------------------------------------------------------------------------
# High Inquisitor Whitemane, The Truth: hard mode.

# Two-hand sword, Equip: melee hits may swing the Verdict, a Holy cleave on the target and 2 more enemies in front
# (scaled). One red socket.
item("sm_fathers_verdict", name="Father's Verdict", like=20504, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Strength (Solo)", secondary="Haste/Versatility", budget_mult=HM_PHYSICAL_TWO_HAND_MULT,
     extra_dps=HM_PHYSICAL_TWO_HAND_DPS, sockets=(R,), socket_bonus=BONUS_HASTE_4,
     spells=(equip_spell(fathers_verdict_212018, scale="budget"),))
# Plate feet (tank), Equip: parries may grant Denial, 10% less damage taken (a percent: unscaled). One blue socket
# (tank gear), Parry bonus.
item("sm_treads_of_denial", name="Treads of Denial", like=20265, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Strength (Solo)", secondary="Parry/Mastery",
     sockets=(B,), socket_bonus=BONUS_PARRY_4,
     spells=(equip_spell(treads_of_denial_212020, scale="budget"),))
# Neck, Equip: heals on an ally below 50% may raise both your Versatility (a percent: unscaled). Secondaries only.
# One red socket.
item("sm_inquisitors_rosary", name="Inquisitor's Rosary", like=22657, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Crit/Versatility", primary_share=0,
     sockets=(R,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(inquisitors_rosary_212022),))
