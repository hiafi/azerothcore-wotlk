"""
The three Gnomeregan hard mode items (docs/dungeons/gnomeregan-rework.md ## Loot, "Hard mode: Mekgineer Thermaplugg,
the Whole Workshop", approved 2026-11-24, rulings 56 to 58): one drops on every hard mode kill of Mekgineer
Thermaplugg, on top of the heroic list item. No loot tables here (the dungeon build's loot stage wires them); the 48
boss list items are gnomeregan.py.

All three are new items on the hard mode ladder (`vanilla_hard_mode`: 71 / 81 / 91 / 101 Epic, required level 60,
ladders.py), Bind on Pickup, unique-equipped across their tiers (automatic for an effect item), and pay 0.7 of the
budget (the effect discount, the default). Keys `gnomer_`. The look of each is a stock item (`like=`, look only, a
designer question); the Card wears the Prismatic Punch Card's own look (displayid 40633, item 9316).

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and the
secondaries are listed (the two-stat shapes are Even, so the order does not matter). No new shape is needed: Crit/
Mastery (30), Crit/Proc (39, the 6000 Volt Capacitor's) and Haste/Versatility (35).

**Effects**: gnomeregan_hard_mode_effects.py (the `gnomeregan_items` reservation 214240-214279). All three grow with
the item level, so all three are `scale="budget"` (every tier above 71 carries its own copies): Meltdown's damage bonus
and pulse, the Walking Bomb's blast, and Clearance's ratings.

**Sockets** (the doc names none; the shared rule, boss-rework-systems section 2): every hard mode item carries 1,
trinkets none. The Launcher's is red (damage gear) with the stock +4 Crit bonus (its first secondary).

**Declared multiplier** (the Scarlet Monastery precedent, the Scarlet Garrison Rifle): the gun takes the 0.6 floor of
the thin socketed hard mode weapons on every tier and declares no DPS fraction (a bow, gun or crossbow takes
dps_delta 0 on every tier, the hunter ranged rule). No ammo (source/world/ranged_weapons.py, hunter-rework Q3).
"""

from lib.dsl.items import Socket, equip_spell, item, use_spell

from .gnomeregan_hard_mode_effects import (
    master_punch_card_214245,
    meltdown_214240,
    walking_bomb_launcher_214242,
)
from .ladders import VANILLA_HARD_MODE

BONUS_CRIT_4 = 2874  # stock SpellItemEnchantment, +4 Crit

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does

HM_SOCKETED_THIN_MULT = 0.6  # socketed hard mode ranged weapon with an effect (module docstring)
NO_AMMO = 0

DISPLAY_PRISMATIC_PUNCH_CARD = 40633  # item 9316, the hard mode's trigger card

# Use (2 min): Meltdown for 15 sec, more damage dealt, a Nature pulse around the wearer, more damage taken (scaled).
# A trinket: no socket.
item("gnomer_leaking_reactor_core", name="Leaking Reactor Core", like=29776, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Strength (Solo)", secondary="Crit/Mastery",
     spells=(use_spell(meltdown_214240, scale="budget"),))
# Gun, Equip: ranged critical strikes may launch a Walking Bomb at the target (scaled). One red socket. No ammo.
item("gnomer_walking_bomb_launcher", name="Walking Bomb Launcher", like=13146, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Agility (Solo)", secondary="Crit/Proc", budget_mult=HM_SOCKETED_THIN_MULT,
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4, ammo_type=NO_AMMO,
     spells=(equip_spell(walking_bomb_launcher_214242, scale="budget"),))
# Equip: five different spells punch the card, then Clearance: PRISMATIC, haste and crit for 10 sec (scaled). A
# trinket: no socket.
item("gnomer_master_punch_card", name="Master Punch Card", like=19287, displayid=DISPLAY_PRISMATIC_PUNCH_CARD,
     bonding=BOP, ladder=VANILLA_HARD_MODE, primary="Intellect (Solo)", secondary="Haste/Versatility",
     spells=(equip_spell(master_punch_card_214245, scale="budget"),))
