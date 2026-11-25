"""
The three Ragefire Chasm hard mode items (docs/dungeons/ragefire-chasm-rework.md ## Loot, "Hard mode: Taragaman the
Hungerer, Starving", approved 2026-11-21, ruling 13): one drops on every hard mode kill of Taragaman the Hungerer, on
top of the heroic list item. The loot tables are ragefire_chasm_loot.py, the 25 boss list items ragefire_chasm.py.

All three are new items on the hard mode ladder (`vanilla_hard_mode`: 71 / 81 / 91 / 101 Epic, required level 60,
ladders.py), Bind on Pickup, unique-equipped across their tiers (automatic for an effect item), and pay 0.7 of the
budget (the effect discount, the default). Keys `rfc_`. The look of each is a stock item (`like=`, look only, a
designer question).

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and the
secondaries are listed (the two-stat shape is Even, so the order does not matter). No new shape is needed.

**Effects**: ragefire_chasm_hard_mode_effects.py (the `ragefire_chasm_items` reservation 213500-213539). All three grow
with the item level, so all three are `scale="budget"` (every tier above 71 carries its own copies): the Fang's bite,
the Heart's Bloodward share and the Greatblade's spin.

**Sockets** (the doc names none; the shared rule, boss-rework-systems section 2): every hard mode item carries 1,
trinkets none. The Greatblade's is red (damage gear) with the stock +4 Crit bonus (its first secondary).

**Declared multipliers** (the Blackrock gear fix pass, REVIEW S1 and S3; Father's Verdict's numbers): the two-hand sword
takes its 60-100 cell times the 0.7 effect discount on every tier, so the 101 tier does not step onto the 101-200 cell.
"""

from lib.dsl.items import Socket, equip_spell, item, use_spell

from .ladders import VANILLA_HARD_MODE
from .ragefire_chasm_hard_mode_effects import (
    felstorm_greatblade_213505,
    heart_of_the_starving_213503,
    taragamans_fang_213500,
)

BONUS_CRIT_4 = 2874  # stock SpellItemEnchantment, +4 Crit

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does

# Declared multipliers (module docstring), the same numbers as scarlet_monastery_hard_mode.py's
HM_PHYSICAL_TWO_HAND_MULT = 0.5537       # physical InventoryType 17 Quality 4 ilvl 60-100 0.791 x 0.7
HM_PHYSICAL_TWO_HAND_DPS = 0.0695        # ... and its DPS fraction

# Use (2 min): leap to an enemy within 25 yd and bite it, healing for the damage dealt (scaled). A trinket: no socket.
item("rfc_taragamans_fang", name="Taragaman's Fang", like=19406, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Agility (Solo)", secondary="Haste (Solo)",
     spells=(use_spell(taragamans_fang_213500, scale="budget"),))
# Equip: direct heals on a target below 30% health leave a Bloodward, a share of the heal (scaled). A trinket: no
# socket.
item("rfc_heart_of_the_starving", name="Heart of the Starving", like=13164, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Spirit (Solo)", secondary="Mastery (Solo)",
     spells=(equip_spell(heart_of_the_starving_213503, scale="budget"),))
# Two-hand sword, Equip: melee hits may start a 3 sec Felstorm around the wearer (scaled). One red socket.
item("rfc_felstorm_greatblade", name="Felstorm Greatblade", like=25169, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Strength (Solo)", secondary="Crit/Haste", budget_mult=HM_PHYSICAL_TWO_HAND_MULT,
     extra_dps=HM_PHYSICAL_TWO_HAND_DPS, sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(felstorm_greatblade_213505, scale="budget"),))
