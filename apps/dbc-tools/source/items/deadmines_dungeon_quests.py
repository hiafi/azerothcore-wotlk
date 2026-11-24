"""
The Deadmines dungeon quest rewards (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 2, stage Q1): seven
new items on the one-tier `quest_reward` ladder (ladders.py), the same item stat system and rules as the stock quest
rewards of quest_rewards.py (docs/plans/quest-reward-itemization/ rulings 2, 6, 10, 11, 19):

- item level = quest level + 5 = 25 (both quests are level 20, under the green and blue caps);
- no required level (ruling 10: the quest already gates by level);
- a green carries one secondary stat and an 80% primary share, a blue two secondaries (a pair shape) and, as a ring
  or neck, no primary at all (ruling 18: rings and necks are all secondary).

Quest B, The Juggernaut's Casting Plans (90100, Gilnid; XP difficulty 5): three greens that fill the gaps the stock
rewards of Underground Assault (7606 Str mail gloves, 7607 Int wand), Red Silk Bandanas (2074, 2089, 6094 Str / Agi
weapons) and The Defias Brotherhood (6087 Str mail legs, 2041 Agi leather chest, 2042 staff) leave: a cloth caster
piece, a (cloth) healer piece and a tank piece, three different slots. One choice of three.

Quest A, The Kingpin's Ledger (90101, Edwin VanCleef; XP difficulty 7): four blues, one per role (tank, physical DPS,
caster DPS, healer), a ring or a neck each (the designer's lean). One choice of four.

The two quest items themselves (70900 Juggernaut Casting Plans, 70901 Edwin VanCleef's Ledger) are not equipment:
source/items.csv rows plus the item_template upsert in pending rev_dungeon_quests_deadmines.sql, like the Blackrock
Depths event items. Quest SQL, the two givers' spawns and the loot rows are in that file too.

Each item looks like a stock item of the same slot and level range (`like=`: class, subclass, display, material,
inventory type, sheath). Bind on Pickup: a quest reward is earned once, by its own character. Keys are `dmq_<name>`.
"""

from lib.dsl.items import item

from .ladders import QUEST_REWARD

ILEVEL = 25          # quest level 20 + 5
REQUIRED_LEVEL = 0   # ruling 10
BOP = 1              # ITEM_BIND_ON_ACQUIRE
GREEN, BLUE = 2, 3
GREEN_SHARE = 8000   # ruling 19
NO_PRIMARY = 0       # a ring or neck: secondary stats only

# ---------------------------------------------------------------------------------------------------------------------
# Quest B: The Juggernaut's Casting Plans (Gilnid). Greens, one secondary each.

# Cloth caster: boots (the stock rewards hold no cloth). Intellect / Crit.
item("dmq_soot_stained_slippers", name="Soot-stained Slippers", like=3065, ilvl=ILEVEL, quality=GREEN,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Intellect (Solo)",
     secondary="Crit (Solo)", primary_share=GREEN_SHARE, unique_equip=False)
# Healer: a cloth belt (priests cannot wear leather; the look is Silver-thread Sash). Spirit / Haste, the Deadmines
# healer pairing (Cookie's Tenderizer).
item("dmq_forgehands_girdle", name="Forgehand's Girdle", like=4714, ilvl=ILEVEL, quality=GREEN,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Spirit (Solo)",
     secondary="Haste (Solo)", primary_share=GREEN_SHARE, unique_equip=False)
# Tank: a shield. Strength / Block, the Deadmines tank pairing (Gold-plated Buckler).
item("dmq_ironclad_foundry_shield", name="Ironclad Foundry Shield", like=3450, ilvl=ILEVEL, quality=GREEN,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Strength (Solo)",
     secondary="Block (Solo)", primary_share=GREEN_SHARE, unique_equip=False)

# ---------------------------------------------------------------------------------------------------------------------
# Quest A: The Kingpin's Ledger (Edwin VanCleef). Blues, two secondaries each (a pair shape), no primary.

# Tank: a neck. Mastery / Versatility: quest reward ruling 24 (a neck cannot take a Dodge pair, so the tank stat is
# dropped for a Versatility pair), the shape the stock tank jewelry gets (19383 Master Dragonslayer's Medallion).
item("dmq_wardens_iron_collar", name="Warden's Iron Collar", like=20909, ilvl=ILEVEL, quality=BLUE,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary=None,
     secondary="Mastery/Versatility", primary_share=NO_PRIMARY, unique_equip=False)
# Physical DPS: a ring. Crit / Proc Chance (Armor Penetration needs a Str or Agi primary).
item("dmq_brigade_bounty_band", name="Brigade Bounty Band", like=5351, ilvl=ILEVEL, quality=BLUE,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary=None,
     secondary="Crit/Proc", primary_share=NO_PRIMARY, unique_equip=False)
# Caster DPS: a ring. Crit / Haste.
item("dmq_scriveners_signet", name="Scrivener's Signet", like=20426, ilvl=ILEVEL, quality=BLUE,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary=None,
     secondary="Crit/Haste", primary_share=NO_PRIMARY, unique_equip=False)
# Healer: a neck. MP5 / Haste.
item("dmq_chaplains_gold_amulet", name="Chaplain's Gold Amulet", like=20830, ilvl=ILEVEL, quality=BLUE,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary=None,
     secondary="MP5/Haste", primary_share=NO_PRIMARY, unique_equip=False)
