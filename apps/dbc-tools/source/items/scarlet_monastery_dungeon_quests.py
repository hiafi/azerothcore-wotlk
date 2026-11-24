"""
The Scarlet Monastery dungeon quest rewards (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 5, stage Q3):
four new items on the one-tier `quest_reward` ladder (ladders.py), the same item stat system and rules as the stock
quest rewards of quest_rewards.py (docs/plans/quest-reward-itemization/ rulings 2, 6, 10, 11, 19) and the Deadmines
and Shadowfang Keep quest rewards (deadmines_dungeon_quests.py, shadowfang_keep_dungeon_quests.py):

- no required level (ruling 10: the quest already gates by level);
- a green carries one secondary stat and an 80% primary share, an epic two secondaries and a 60% share (ruling 19).

**1394 Final Passage** (the Test of Lore chain's last quest, open world, stays Horde): the two stock blue choices,
6804 Windstorm Hammer (Str, a one-hand mace) and 6806 Dancing Flame (Int, a wand), go to epic in quest_rewards.lock
(item level 41 stays), and this file adds the third choice, an **Agility epic at item level 41**: a one-hand dagger.
It fits the other two: a one-hand melee weapon like the hammer (the wand is the caster's ranged slot), and a dagger is
the Agility one-hand every Agility class can wield (rogue, enhancement shaman, feral druid, hunter's melee slot,
warrior). A bow would serve only the hunter. The look is the stock Howling Blade (a wind-streaked dagger, in the same
elemental vein as the Windstorm Hammer and Dancing Flame). Crit / Proc Chance: the physical DPS pair of the
Deadmines quest rings, and the Agility pair the Black Menace (1053) leaves out (it takes Haste and Cooldown Haste).

**1113 Hearts of Zeal** (quest level 33, XP difficulty 7): item level 38 = quest level 33 + 5, a choice of three greens,
one secondary each. The Scarlet Monastery's other quest rewards are weapons, shields, an orb and jewelry, with no
armor piece at all, and they cover Strength melee, Intellect casters and (with a sword, a buckler and an orb) healers
well; Agility has one dagger (Black Menace) and tank has one shield (Vile Protector, 1049). So the three greens fill
the thinnest roles with a body-armor slot each: Agility (leather legs), tank (plate boots) and healer (cloth gloves).
Tank takes Parry (ruling 12: plate takes Parry or Block), as the Shadowfang Keep Houseguard's Helm.

Each item looks like a stock item of the same slot and level range (`like=`: class, subclass, display, material,
inventory type, sheath). Bind on Pickup: a quest reward is earned once, by its own character. Keys are `smq_<name>`.
"""

from lib.dsl.items import item

from .ladders import QUEST_REWARD

REQUIRED_LEVEL = 0   # ruling 10
BOP = 1              # ITEM_BIND_ON_ACQUIRE
GREEN, EPIC = 2, 4
GREEN_SHARE = 8000   # ruling 19
EPIC_SHARE = 6000    # ruling 19: epic 60% with two secondaries

# ---------------------------------------------------------------------------------------------------------------------
# 1394 Final Passage: the Agility epic (item level 41, as the Windstorm Hammer and Dancing Flame).

# Agility / Crit + Proc Chance dagger. The weapon's DPS and budget come from the epic role cell of its slot.
item("smq_galewhisper_dirk", name="Galewhisper Dirk", like=6331, ilvl=41, quality=EPIC,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Agility (Solo)",
     secondary="Crit/Proc", primary_share=EPIC_SHARE, unique_equip=False)

# ---------------------------------------------------------------------------------------------------------------------
# 1113 Hearts of Zeal: item level 38 (quest level 33 + 5), greens.

ILEVEL_HEARTS = 38

# Agility: leather legs (the look is Emblazoned Leggings, a heraldic leather pair). Agility / Haste.
item("smq_argent_skirmishers_leggings", name="Argent Skirmisher's Leggings", like=4050, ilvl=ILEVEL_HEARTS,
     quality=GREEN, required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Agility (Solo)",
     secondary="Haste (Solo)", primary_share=GREEN_SHARE, unique_equip=False)
# Tank: plate boots (the look is Jouster's Greaves). Strength / Parry.
item("smq_argent_vanguards_greaves", name="Argent Vanguard's Greaves", like=8160, ilvl=ILEVEL_HEARTS,
     quality=GREEN, required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Strength (Solo)",
     secondary="Parry (Solo)", primary_share=GREEN_SHARE, unique_equip=False)
# Healer: cloth gloves (priests cannot wear leather; the look is Truefaith Gloves). Spirit / Haste, the healer pairing
# of the Deadmines Forgehand's Girdle.
item("smq_argent_menders_gloves", name="Argent Mender's Gloves", like=7049, ilvl=ILEVEL_HEARTS,
     quality=GREEN, required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Spirit (Solo)",
     secondary="Haste (Solo)", primary_share=GREEN_SHARE, unique_equip=False)
