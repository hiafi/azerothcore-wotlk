"""
The three Uldaman hard mode items (docs/dungeons/uldaman-rework.md ## Loot, "Hard mode: Archaedas, The Makers'
Lights", approved 2026-11-21, ruling 35; copied in docs/dungeons/dungeon-loot-vanilla.md "### Uldaman"): one drops on
every hard mode kill of Archaedas, on top of the heroic list item. No loot tables here (the dungeon build's loot stage
wires them); the 49 boss list items are uldaman.py.

All three are new items on the hard mode ladder (`vanilla_hard_mode`: 71 / 81 / 91 / 101 Epic, required level 60,
ladders.py), Bind on Pickup, unique-equipped across their tiers (automatic for an effect item), and pay 0.7 of the
budget (the effect discount, the default). Keys `uldaman_` (as the list's). The look of each is a stock item (`like=`,
look only, a designer question).

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and the
secondaries are listed (Even shapes: the doc's order of secondaries does not matter). The neck carries secondaries only
(`primary=None`, share 0, the Inquisitor's Rosary precedent). No new shape is needed: Mastery (Solo) (the Scale of the
Storm God's), Crit/Haste and Crit/Mastery/Versatility.

**Effects**: uldaman_hard_mode_effects.py (the `uldaman_items` reservation 214680-214719). All three grow with the item
level, so all three are `scale="budget"` (every tier above 71 carries its own copies): the Waking Stone's trample, the
Choker's Two Lights and the Disk's replay share.

**Sockets** (the doc names none; the shared rule, boss-rework-systems section 2): every hard mode item carries 1,
trinkets none. The Choker's and the Fragment's are red (damage and healing gear) with the stock +4 Crit bonus (the
Choker's first secondary; the Fragment's first, Versatility, takes Crit: no enchant exists for the custom stats, the
Scarlet Monastery rule).

**Declared multiplier**: none. The held-in-off-hand Fragment keeps its cell (Fairbell's Censer precedent), the neck and
the trinket are no weapon-tier slot.
"""

from lib.dsl.items import Socket, equip_spell, item, use_spell

from .ladders import VANILLA_HARD_MODE
from .uldaman_hard_mode_effects import (
    fragment_of_the_disks_214684,
    lightbound_choker_214682,
    waking_stone_214680,
)

BONUS_CRIT_4 = 2874  # stock SpellItemEnchantment, +4 Crit

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does

# Use (2 min): wake an earthen that marches 20 yd ahead, trampling and knocking back the enemies in its path (scaled).
# A trinket: no socket.
item("uldaman_waking_stone", name="Waking Stone", like=20525, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Strength (Solo)", secondary="Mastery (Solo)",
     spells=(use_spell(waking_stone_214680, scale="budget"),))
# Neck, Equip: a damaging or healing spell of another school than the last grants Two Lights, haste rating, 3 stacks
# (scaled). Secondaries only. One red socket.
item("uldaman_lightbound_choker", name="Lightbound Choker", like=17109, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary=None, secondary="Crit/Haste", primary_share=0,
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(lightbound_choker_214682, scale="budget"),))
# Held in off-hand, Use (2 min): the Disk records your healing for 6 sec, then replays a share of it on the same
# targets over 6 sec (scaled). One red socket.
item("uldaman_fragment_of_the_disks", name="Fragment of the Disks", like=18523, bonding=BOP,
     ladder=VANILLA_HARD_MODE, primary="Intellect (Solo)", secondary="Crit/Mastery/Versatility",
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4,
     spells=(use_spell(fragment_of_the_disks_214684, scale="budget"),))
