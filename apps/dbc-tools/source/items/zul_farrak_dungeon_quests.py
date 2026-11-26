"""
The Zul'Farrak dungeon quest rewards (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 7, the Zul'Farrak
build's quests WP, handoff 4.Q and section 7 #54 A): sixteen new items on the one-tier `quest_reward` ladder
(ladders.py), the same item stat system and rules as the stock quest rewards of quest_rewards.py
(docs/plans/quest-reward-itemization/ rulings 2, 6, 10, 11, 18, 19, 24) and the earlier dungeon quest rewards
(ragefire_chasm_dungeon_quests.py, blackrock_depths_dungeon_quests.py):

- item level = quest level + 5, under the green cap 55 and the blue cap 60 (ruling 2): 50 for the level 45 quests, 52
  for the level 47 ones; by the user's ruling (2026-11-26) the epics take 57 (5 above the dungeon's blues) and the
  Horde wrists 52 (even with the Alliance's);
- no required level (ruling 10: the quest already gates by level);
- a green carries one secondary stat and an 80% primary share, a blue and an epic two secondaries (a pair shape) and
  a 60% share (ruling 19);
- no weapon: the epic weapon DPS curve is flat below item level 50 (the Staff of Westfall, Dancing Flame jumps), and
  the stock rewards of this dungeon (Spellshifter Rod, the Masons Fraternity Ring, the Engineer's Guild Headpiece,
  Carrot on a Stick) already cover the weapon, ring, head and trinket slots;
- ruling 24 (a ring, neck, trinket or Intellect item takes no Dodge pair): no item here has one; plate tank pieces
  take Parry (ruling 12), and every healer piece is cloth.

**3527 The Prophecy of Mosh'aru** (open world, both factions, XP difficulty 9; the stock reward is nothing): an epic
choice of three **shoulders** at item level 57, one per primary the designer named: Strength plate (Crit / Mastery),
Agility leather (Crit / Proc Chance), Intellect cloth (Crit / Haste), the pairs of the Ragefire Chasm epics.

**2936 The Spider God** (Horde, level 45, XP difficulty 8) and **2991 Nekrum's Medallion** (Alliance, level 47, XP
difficulty 8): a blue choice of three **wrists** each, Strength plate, Agility leather and Intellect cloth, item level
52 both. The two sides get the same pairs (Strength Haste / Mastery, Agility Crit / Haste, Intellect Haste /
Mastery: the wrist slot's role pairs that the epic shoulders leave out) and different looks and names.

**2865 Scarab Shells** (level 45, green, item level 50): a choice of two **belts**, Agility leather (Haste) and
Strength plate (Crit).

**3042 Troll Temper** (level 45, green, item level 50): a choice of two **cloth boots**, Intellect (Crit) and Spirit
(Mastery, the healer pairing of Oralius's Lucky Sash and the Ragefire healer gloves).

**2768 Divino-matic Rod** (level 47, item level 52): beside the stock blues 9533 (a ring, Haste / Proc Chance, no
primary) and 9534 (an Intellect cloth headpiece), three more blues for the roles they leave out: **Strength plate
legs** (Crit / Haste), **Agility leather shoulders** (Haste / Proc Chance) and **tank plate boots** (Strength,
Parry / Mastery). Quest 2846 keeps the Spellshifter Rod and 2770 the Carrot on a Stick (stock, quest_rewards.lock).

Each item looks like a stock item of the same slot and level range (`like=`: class, subclass, display, material,
inventory type, sheath). Bind on Pickup: a quest reward is earned once, by its own character. Keys are `zfq_<name>`;
the names are used by nothing in SQL (rev_quests_zul_farrak.sql sets the minted ids, the test pins them).
"""

from lib.dsl.items import item

from .ladders import QUEST_REWARD

REQUIRED_LEVEL = 0   # ruling 10
BOP = 1              # ITEM_BIND_ON_ACQUIRE
GREEN, BLUE, EPIC = 2, 3, 4
GREEN_SHARE = 8000   # ruling 19
PAIR_SHARE = 6000    # ruling 19: a blue or epic with two secondaries

ILEVEL_EPIC = 57     # 3527: 5 above the dungeon's blues (user 2026-11-26, R-Q DQ2 B)
ILEVEL_HORDE = 52    # 2936: even with Alliance's 2991 (user 2026-11-26, R-Q DQ3 B)
ILEVEL_ALLIANCE = 52  # 2991, quest level 47 + 5
ILEVEL_GREEN = 50    # 2865 and 3042, quest level 45 + 5
ILEVEL_ROD = 52      # 2768, quest level 47 + 5


def _gear(key, name, like, ilvl, quality, primary, secondary, share):
    item(key, name=name, like=like, ilvl=ilvl, quality=quality, required_level=REQUIRED_LEVEL, bonding=BOP,
         ladder=QUEST_REWARD, primary=primary, secondary=secondary, primary_share=share, unique_equip=False)


# ---------------------------------------------------------------------------------------------------------------------
# 3527 The Prophecy of Mosh'aru: three shoulder epics, one per primary.

# Strength plate (the look is Earthslag Shoulders). Crit / Mastery.
_gear("zfq_pauldrons_of_mosharu", "Pauldrons of Mosh'aru", 11632, ILEVEL_EPIC, EPIC,
      "Strength (Solo)", "Crit/Mastery", PAIR_SHARE)
# Agility leather (the look is Atal'ai Spaulders, the Sunken Temple's trolls). Crit / Proc Chance.
_gear("zfq_spaulders_of_mosharu", "Spaulders of Mosh'aru", 10783, ILEVEL_EPIC, EPIC,
      "Agility (Solo)", "Crit/Proc", PAIR_SHARE)
# Intellect cloth (the look is Kentic Amice). Crit / Haste.
_gear("zfq_amice_of_mosharu", "Amice of Mosh'aru", 11624, ILEVEL_EPIC, EPIC,
      "Intellect (Solo)", "Crit/Haste", PAIR_SHARE)

# ---------------------------------------------------------------------------------------------------------------------
# 2936 The Spider God (Horde): three wrist blues, item level 50.

# Strength plate (the look is Noxxion's Shackles). Haste / Mastery.
_gear("zfq_shadras_chitin_vambraces", "Shadra's Chitin Vambraces", 17746, ILEVEL_HORDE, BLUE,
      "Strength (Solo)", "Haste/Mastery", PAIR_SHARE)
# Agility leather (the look is Darkwater Bracers). Crit / Haste.
_gear("zfq_shadras_chitin_bracers", "Shadra's Chitin Bracers", 10800, ILEVEL_HORDE, BLUE,
      "Agility (Solo)", "Crit/Haste", PAIR_SHARE)
# Intellect cloth (the look is Forgotten Wraps). Haste / Mastery.
_gear("zfq_shadras_silken_cuffs", "Shadra's Silken Cuffs", 9433, ILEVEL_HORDE, BLUE,
      "Intellect (Solo)", "Haste/Mastery", PAIR_SHARE)

# ---------------------------------------------------------------------------------------------------------------------
# 2991 Nekrum's Medallion (Alliance): three wrist blues, item level 52, the same pairs.

# Strength plate (the look is Runed Golem Shackles). Haste / Mastery.
_gear("zfq_gutchewers_vambraces", "Gutchewer's Vambraces", 12550, ILEVEL_ALLIANCE, BLUE,
      "Strength (Solo)", "Haste/Mastery", PAIR_SHARE)
# Agility leather (the look is Deepfury Bracers). Crit / Haste.
_gear("zfq_gutchewers_bracers", "Gutchewer's Bracers", 13120, ILEVEL_ALLIANCE, BLUE,
      "Agility (Solo)", "Crit/Haste", PAIR_SHARE)
# Intellect cloth (the look is Aristocratic Cuffs). Haste / Mastery.
_gear("zfq_gutchewers_cuffs", "Gutchewer's Cuffs", 12546, ILEVEL_ALLIANCE, BLUE,
      "Intellect (Solo)", "Haste/Mastery", PAIR_SHARE)

# ---------------------------------------------------------------------------------------------------------------------
# 2865 Scarab Shells: the two belt greens, item level 50.

# Agility leather (the look is Sagebrush Girdle, a desert belt). Haste.
_gear("zfq_scarabhide_belt", "Scarabhide Belt", 17778, ILEVEL_GREEN, GREEN,
      "Agility (Solo)", "Haste (Solo)", GREEN_SHARE)
# Strength plate (the look is Atal'ai Girdle). Crit.
_gear("zfq_scarabplate_girdle", "Scarabplate Girdle", 10788, ILEVEL_GREEN, GREEN,
      "Strength (Solo)", "Crit (Solo)", GREEN_SHARE)

# ---------------------------------------------------------------------------------------------------------------------
# 3042 Troll Temper: the two cloth boot greens, item level 50.

# Intellect cloth (the look is Mistwalker Boots). Crit.
_gear("zfq_sandtempered_slippers", "Sandtempered Slippers", 10629, ILEVEL_GREEN, GREEN,
      "Intellect (Solo)", "Crit (Solo)", GREEN_SHARE)
# Healer cloth (the look is Vinerot Sandals). Spirit / Mastery.
_gear("zfq_sandtempered_sandals", "Sandtempered Sandals", 17748, ILEVEL_GREEN, GREEN,
      "Spirit (Solo)", "Mastery (Solo)", GREEN_SHARE)

# ---------------------------------------------------------------------------------------------------------------------
# 2768 Divino-matic Rod: the Strength, Agility and tank blues beside the stock ring and headpiece, item level 52.

# Strength plate legs (the look is Silvershell Leggings). Crit / Haste.
_gear("zfq_dowsers_legplates", "Dowser's Legplates", 10633, ILEVEL_ROD, BLUE,
      "Strength (Solo)", "Crit/Haste", PAIR_SHARE)
# Agility leather shoulders (the look is Phytoskin Spaulders). Haste / Proc Chance.
_gear("zfq_dowsers_spaulders", "Dowser's Spaulders", 17749, ILEVEL_ROD, BLUE,
      "Agility (Solo)", "Haste/Proc", PAIR_SHARE)
# Tank plate boots (the look is Battlechaser's Greaves). Strength / Parry + Mastery (ruling 12).
_gear("zfq_dowsers_greaves", "Dowser's Greaves", 12555, ILEVEL_ROD, BLUE,
      "Strength (Solo)", "Parry/Mastery", PAIR_SHARE)
