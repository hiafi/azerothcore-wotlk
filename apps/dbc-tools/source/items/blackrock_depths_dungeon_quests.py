"""
The Blackrock Depths dungeon quest rewards (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 8, stage Q4):
four new items on the one-tier `quest_reward` ladder (ladders.py), the same item stat system and rules as the stock
quest rewards of quest_rewards.py (docs/plans/quest-reward-itemization/ rulings 2, 6, 10, 11, 18, 19, 24) and the
earlier dungeon quest rewards (deadmines_dungeon_quests.py, scarlet_monastery_dungeon_quests.py):

- item level = quest level + 5, capped at 55 for greens and 60 for blues (ruling 2);
- no required level (ruling 10: the quest already gates by level);
- a green carries one secondary stat and an 80% primary share, a blue two secondaries (a pair shape) and a 60% share;
  a ring has no primary (ruling 18) and no tank stat (ruling 24) (ruling 19).

**4123 The Heart of the Mountain** (quest level 55, stock 8.5 gold only): a **blue ring**, item level 60. Mastery /
Versatility: a ring is every role's slot, and this pair is the one that serves all five (tank and healer included);
the other new blues of the dungeon take Crit / Haste (the caster dagger) and a tank pair (the shield). The look is the
Magma Forged Band (a ring of molten stone, the Heart's own vault).

**4286 The Good Stuff** (quest level 56): the stock Dingy Fanny Pack plus a **new green**, item level 55 (the green
cap). Healer, because the dungeon's quest rewards cover it least: one green (Splintsteel Armor, 4136) against three
Strength pieces (Swiftstrike Cudgel and Limb Cleaver from 4134, Nightfall Gloves from 4263), three Agility pieces
(Penance Spaulders, Crypt Demon Bracers, Skilled Fighting Blade), two tank pieces (Stalwart Clutch and the new shield)
and two caster pieces (Rancor Boots and the new dagger). A cloth belt (priests cannot wear leather), the pack's own
slot: Spirit / Mastery (the healer pairing; Splintsteel already takes Haste).

**4322 Jail Break!** (quest level 58): the stock greens 12061 Blade of Reckoning and 12062 Skilled Fighting Blade go to
blue in quest_rewards.lock (item level 60 kept), and this file adds the **caster** and **tank** blues, item level 60:
- caster: a main-hand dagger, Intellect / Crit + Haste (the Deadmines caster pairing; weapon scaling takes its spell
  power from the dagger's DPS). Named for the tablets Windsor's captors were decrypting. Look: Black Crystal Dagger.
- tank: a shield, Strength / Parry + Block (ruling 12: plate tank stats are Parry or Block; a shield takes both).
  Look: Rock Golem Bulwark.

Each item looks like a stock item of the same slot and level range (`like=`: class, subclass, display, material,
inventory type, sheath). Bind on Pickup: a quest reward is earned once, by its own character. Keys are `brdq_<name>`.
"""

from lib.dsl.items import item

from .ladders import QUEST_REWARD

REQUIRED_LEVEL = 0   # ruling 10
BOP = 1              # ITEM_BIND_ON_ACQUIRE
GREEN, BLUE = 2, 3
GREEN_SHARE = 8000   # ruling 19
BLUE_SHARE = 6000    # ruling 19
NO_PRIMARY = 0       # a ring: secondary stats only (ruling 18)

ILEVEL_BLUE = 60     # quest levels 55 (4123) and 58 (4322) + 5, the blue cap 60 (ruling 2)
ILEVEL_GREEN = 55    # quest level 56 (4286) + 5 = 61, the green cap 55 (ruling 2)

# ---------------------------------------------------------------------------------------------------------------------
# 4123 The Heart of the Mountain: the blue ring.

item("brdq_mountainheart_band", name="Mountainheart Band", like=22255, ilvl=ILEVEL_BLUE, quality=BLUE,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary=None,
     secondary="Mastery/Versatility", primary_share=NO_PRIMARY, unique_equip=False)

# ---------------------------------------------------------------------------------------------------------------------
# 4286 The Good Stuff: the healer green, next to the stock Dingy Fanny Pack.

item("brdq_oralius_lucky_sash", name="Oralius's Lucky Sash", like=15791, ilvl=ILEVEL_GREEN, quality=GREEN,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Spirit (Solo)",
     secondary="Mastery (Solo)", primary_share=GREEN_SHARE, unique_equip=False)

# ---------------------------------------------------------------------------------------------------------------------
# 4322 Jail Break!: the caster and tank blues beside the upgraded Blade of Reckoning and Skilled Fighting Blade.

item("brdq_cipherblade", name="Cipherblade", like=20647, ilvl=ILEVEL_BLUE, quality=BLUE,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Intellect (Solo)",
     secondary="Crit/Haste", primary_share=BLUE_SHARE, unique_equip=False)
item("brdq_jailbreakers_bulwark", name="Jailbreaker's Bulwark", like=11785, ilvl=ILEVEL_BLUE, quality=BLUE,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary="Strength (Solo)",
     secondary="Parry/Block", primary_share=BLUE_SHARE, unique_equip=False)
