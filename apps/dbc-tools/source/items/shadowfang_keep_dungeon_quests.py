"""
The Shadowfang Keep dungeon quest rewards (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 3, stage Q2):
two new greens on the one-tier `quest_reward` ladder (ladders.py), the same item stat system and rules as the stock
quest rewards of quest_rewards.py (docs/plans/quest-reward-itemization/ rulings 2, 6, 10, 11, 19) and the Deadmines
quest rewards (deadmines_dungeon_quests.py):

- item level = quest level + 5 = 30 (The Baron's Rest is quest level 25, under the green cap; designer 2026-11-24:
  first drafted as 24 / 29);
- no required level (ruling 10: the quest already gates by level);
- a green carries one secondary stat and an 80% primary share.

The Baron's Rest (90110, Baron Silverlaine; XP difficulty 7) offers one choice of two: an Agility piece and a tank
piece, the gap in the stock rewards of the three other quests (3324 Ghostly Mantle, cloth caster shoulders; 4534
Steel-clasped Bracers, mail Spirit wrists; 6335 Grizzled Boots, mail Strength boots; 6414 Seal of Sylvanas, a ring).
Both take a slot the other quest rewards leave open: leather gloves for Agility (no gloves anywhere in the dungeon's
rewards or drops) and a plate helm for the tank (the only other head piece is the Watchtower Coif, mail Intellect).
The tank piece is plate Strength / Parry, as the Wolfhide-lined Pauldrons.

The quest item (70910 Silverlaine Signet) is not equipment: the source/items.csv row plus the item_template upsert in
pending rev_dungeon_quests_shadowfang_keep.sql, like the Deadmines quest items. Quest SQL, the giver's spawn and the
loot row are in that file too.

Each item looks like a stock item of the same slot and level range (`like=`: class, subclass, display, material,
inventory type, sheath). Bind on Pickup: a quest reward is earned once, by its own character, as the four stock
rewards of the other quests are. Keys are `sfkq_<name>`.
"""

from lib.dsl.items import item

from .ladders import QUEST_REWARD

ILEVEL = 30          # quest level 25 + 5
REQUIRED_LEVEL = 0   # ruling 10
BOP = 1              # ITEM_BIND_ON_ACQUIRE
GREEN = 2
GREEN_SHARE = 8000   # ruling 19

# Agility: leather gloves (the look is Emblazoned Gloves, a heraldic leather glove). Agility / Crit: the Agility pieces
# of the dungeon's loot take Haste, Versatility, Proc Chance and Dodge, none Crit.
item("sfkq_silverlaine_retainers_gloves", name="Silverlaine Retainer's Gloves", like=6397, ilvl=ILEVEL, quality=GREEN,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Agility (Solo)",
     secondary="Crit (Solo)", primary_share=GREEN_SHARE, unique_equip=False)
# Tank: a plate helm (the look is Field Plate Helmet). Strength / Parry: a plate tank takes Parry (ruling 12), the
# pairing of the Wolfhide-lined Pauldrons; the Deadmines quest tank piece is a Block shield.
item("sfkq_silverlaine_houseguards_helm", name="Silverlaine Houseguard's Helm", like=9290, ilvl=ILEVEL, quality=GREEN,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Strength (Solo)",
     secondary="Parry (Solo)", primary_share=GREEN_SHARE, unique_equip=False)
