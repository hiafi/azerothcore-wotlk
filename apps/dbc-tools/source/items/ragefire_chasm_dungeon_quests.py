"""
The Ragefire Chasm dungeon quest rewards (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 1, the Ragefire
Chasm build's quests WP, handoff 4.Q and section 7 #39 A): seven new items on the one-tier `quest_reward` ladder
(ladders.py), the same item stat system and rules as the stock quest rewards of quest_rewards.py
(docs/plans/quest-reward-itemization/ rulings 2, 6, 10, 11, 18, 19, 24) and the earlier dungeon quest rewards
(deadmines_dungeon_quests.py, scarlet_monastery_dungeon_quests.py, blackrock_depths_dungeon_quests.py):

- item level = quest level + 5 (20 for the level 15 quest, 21 for the level 16 one; both under the green and blue
  caps); the epics take 26, the designer's number for Hidden Enemies;
- no required level (ruling 10: the quest already gates by level);
- a green carries one secondary stat and an 80% primary share, a blue and an epic two secondaries (a pair shape) and a
  60% share (ruling 19).

**5728 Hidden Enemies** (open world, stays Horde, XP difficulty 9; the stock reward is 8 silver only): a choice of
three **waist** epics, item level 26, one per primary the designer named (Strength, Agility, Intellect). A belt, not a
weapon: the epic weapon DPS curve is flat below item level 50, so an epic weapon would jump far past the dungeon's
blues (Staff of Westfall +56%, Q1), and none of the four bosses' loot lists has a waist piece, so the slot is open.
Each belt takes the armor type that primary wears at this level: Strength mail (Lambent Scale Girdle's look), Agility
leather (Blackened Defias Belt's), Intellect cloth (Brimstone Belt's). Pairs: Strength Crit / Mastery, Agility
Crit / Proc Chance, Intellect Crit / Haste.

**5761 Slaying the Beast** (quest level 16, XP difficulty 7; the stock reward is 8 silver only): a choice of two blues,
item level 21, the designer's "Agility or tank". Agility leather boots (Haste / Proc Chance: the Deadmines physical
pair is Crit / Proc, which the Agility epic takes) and a plate-tank shield (Strength, Parry / Block, ruling 12 and the
Jailbreaker's Bulwark's pair).

**5723 Testing an Enemy's Strength** (quest level 15, XP difficulty 7; the stock reward is 7 silver only): a choice of
two greens, item level 20, the designer's "Strength or healer". Strength mail gloves (Crit) and healer cloth gloves
(priests cannot wear leather; Spirit / Mastery, the healer pairing of Oralius's Lucky Sash).

The Satchel pair's rewards are the stock greens 15452 and 15453 (item level 21 already), untouched; The Power to
Destroy...'s stock choices 15449, 15450 and 15451 go from green to blue in quest_rewards.lock (not here: one owner per
entry).

Each item looks like a stock item of the same slot and level range (`like=`: class, subclass, display, material,
inventory type, sheath). Bind on Pickup: a quest reward is earned once, by its own character. Keys are `rfcq_<name>`.
"""

from lib.dsl.items import item

from .ladders import QUEST_REWARD

REQUIRED_LEVEL = 0   # ruling 10
BOP = 1              # ITEM_BIND_ON_ACQUIRE
GREEN, BLUE, EPIC = 2, 3, 4
GREEN_SHARE = 8000   # ruling 19
PAIR_SHARE = 6000    # ruling 19: a blue or epic with two secondaries

ILEVEL_EPIC = 26     # the designer's number for Hidden Enemies
ILEVEL_BLUE = 21     # 5761 Slaying the Beast, quest level 16 + 5
ILEVEL_GREEN = 20    # 5723 Testing an Enemy's Strength, quest level 15 + 5

# ---------------------------------------------------------------------------------------------------------------------
# 5728 Hidden Enemies: three waist epics, one per primary.

# Strength mail (the look is Lambent Scale Girdle). Crit / Mastery.
# Its name is used by rev_dungeon_quests_ragefire_chasm.sql: rename both.
item("rfcq_embersworn_girdle", name="Embersworn Girdle", like=4707, ilvl=ILEVEL_EPIC, quality=EPIC,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Strength (Solo)",
     secondary="Crit/Mastery", primary_share=PAIR_SHARE, unique_equip=False)
# Agility leather (the look is Blackened Defias Belt). Crit / Proc Chance.
# Its name is used by rev_dungeon_quests_ragefire_chasm.sql: rename both.
item("rfcq_cinderstalkers_belt", name="Cinderstalker's Belt", like=10403, ilvl=ILEVEL_EPIC, quality=EPIC,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Agility (Solo)",
     secondary="Crit/Proc", primary_share=PAIR_SHARE, unique_equip=False)
# Intellect cloth (the look is Brimstone Belt). Crit / Haste.
# Its name is used by rev_dungeon_quests_ragefire_chasm.sql: rename both.
item("rfcq_ashcallers_sash", name="Ashcaller's Sash", like=4785, ilvl=ILEVEL_EPIC, quality=EPIC,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Intellect (Solo)",
     secondary="Crit/Haste", primary_share=PAIR_SHARE, unique_equip=False)

# ---------------------------------------------------------------------------------------------------------------------
# 5761 Slaying the Beast: the Agility and tank blues.

# Agility leather boots (the look is Scouting Boots). Haste / Proc Chance.
# Its name is used by rev_dungeon_quests_ragefire_chasm.sql: rename both.
item("rfcq_beastslayers_treads", name="Beastslayer's Treads", like=6582, ilvl=ILEVEL_BLUE, quality=BLUE,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Agility (Solo)",
     secondary="Haste/Proc", primary_share=PAIR_SHARE, unique_equip=False)
# Tank shield (the look is Outrunner's Shield). Strength / Parry + Block.
# Its name is used by rev_dungeon_quests_ragefire_chasm.sql: rename both.
item("rfcq_beastslayers_bulwark", name="Beastslayer's Bulwark", like=15504, ilvl=ILEVEL_BLUE, quality=BLUE,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Strength (Solo)",
     secondary="Parry/Block", primary_share=PAIR_SHARE, unique_equip=False)

# ---------------------------------------------------------------------------------------------------------------------
# 5723 Testing an Enemy's Strength: the Strength and healer greens.

# Strength mail gloves (the look is Grunt's Handwraps). Strength / Crit.
# Its name is used by rev_dungeon_quests_ragefire_chasm.sql: rename both.
item("rfcq_troggbane_gauntlets", name="Troggbane Gauntlets", like=15509, ilvl=ILEVEL_GREEN, quality=GREEN,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Strength (Solo)",
     secondary="Crit (Solo)", primary_share=GREEN_SHARE, unique_equip=False)
# Healer cloth gloves (priests cannot wear leather; the look is Ritual Gloves). Spirit / Mastery.
# Its name is used by rev_dungeon_quests_ragefire_chasm.sql: rename both.
item("rfcq_chasm_tenders_gloves", name="Chasm Tender's Gloves", like=14124, ilvl=ILEVEL_GREEN, quality=GREEN,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Spirit (Solo)",
     secondary="Mastery (Solo)", primary_share=GREEN_SHARE, unique_equip=False)
