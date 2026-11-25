"""
The three Zul'Farrak hard mode items (docs/dungeons/zul-farrak-rework.md ## Loot, "Hard mode: Gahz'rilla, The Crew at
the Pool", approved 2026-11-24, ruling 47): one drops on every hard mode kill of Gahz'rilla, on top of the heroic list
item. No loot tables here (the dungeon build's loot stage wires them); the 62 boss list items are zul_farrak.py.

All three are new items on the hard mode ladder (`vanilla_hard_mode`: 71 / 81 / 91 / 101 Epic, required level 60,
ladders.py), Bind on Pickup, unique-equipped across their tiers (automatic for an effect item), and pay 0.7 of the
budget (the effect discount, the default). Keys `zf_`. The look of each is a stock item (`like=`, look only, a
designer question).

Shapes are `item_shape.name` strings; every item also gets the budget's baseline Stamina, so only the primary and the
secondaries are listed (the two-stat shape is Even, so the order does not matter). No new shape is needed.

**Effects**: zul_farrak_hard_mode_effects.py (the `zul_farrak_items` reservation 213800-213839). All three grow with
the item level, so all three are `scale="budget"` (every tier above 71 carries its own copies): the Scale's discharge,
the Fang's arc and the Whistle's share.

**Sockets** (the doc names none; the shared rule, boss-rework-systems section 2): every hard mode item carries 1,
trinkets none. The Fang's is red (damage gear) with the stock +4 Crit bonus (its first secondary).

**Declared multiplier** (the Blackrock gear fix pass, REVIEW S3): the dagger takes the 0.6 floor of the thin socketed
hard mode one-handers on every tier (Golemwright's Mending Rod, a caster one-hander with two secondaries).
"""

from lib.dsl.items import Socket, equip_spell, item, use_spell

from .ladders import VANILLA_HARD_MODE
from .zul_farrak_hard_mode_effects import (
    scale_of_the_storm_god_213800,
    sergeants_whistle_213806,
    stormcharged_fang_213803,
)

BONUS_CRIT_4 = 2874  # stock SpellItemEnchantment, +4 Crit

BOP = 1  # ITEM_BIND_ON_ACQUIRE: a new boss item binds when picked up, whatever the item it looks like does

HM_SOCKETED_THIN_MULT = 0.6  # socketed hard mode one-hander with an effect (module docstring)

# Equip: hits taken build Static Charge; at 10 the next melee ability discharges (scaled). A trinket: no socket.
item("zf_scale_of_the_storm_god", name="Scale of the Storm God", like=17064, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Strength (Solo)", secondary="Mastery (Solo)",
     spells=(equip_spell(scale_of_the_storm_god_213800, scale="budget"),))
# One-hand dagger, Equip: spell crits charge the Fang; at 5 the next damaging spell arcs (scaled). One red socket.
item("zf_stormcharged_fang", name="Stormcharged Fang", like=6904, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Intellect (Solo)", secondary="Crit/Haste", budget_mult=HM_SOCKETED_THIN_MULT,
     sockets=(Socket.RED,), socket_bonus=BONUS_CRIT_4,
     spells=(equip_spell(stormcharged_fang_213803, scale="budget"),))
# Use (2 min): call the crew for 12 sec, single target heals are shared (scaled). A trinket: no socket.
item("zf_sergeants_whistle", name="Sergeant's Whistle", like=3456, bonding=BOP, ladder=VANILLA_HARD_MODE,
     primary="Spirit (Solo)", secondary="Haste (Solo)",
     spells=(use_spell(sergeants_whistle_213806, scale="budget"),))
