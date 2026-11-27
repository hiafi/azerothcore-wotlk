"""
The Gnomeregan dungeon quest rewards (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md 4.Q and section 7
#46 A, ruled "as recommended" 2026-11-26; the dungeon doc's Dungeon quests section, ruling 24 of
docs/plans/quest-reward-itemization/): eleven new items on the one-tier `quest_reward` ladder (ladders.py), the same
item stat system and rules as the stock quest rewards of quest_rewards.py (rulings 2, 6, 10, 11, 18, 19, 24) and the
earlier dungeon quest rewards (zul_farrak_dungeon_quests.py, ragefire_chasm_dungeon_quests.py):

- item level = quest level + 5, under the green cap 55 and the blue cap 60: 31 for 2922 (level 26), 35 for 2924 (level
  30), 39 for 2945 (level 34), 40 for 2841 and 2929 (level 35);
- no required level (ruling 10: the quest already gates by level);
- a green carries one secondary stat and an 80% primary share, a blue two secondaries (a pair shape) and a 60% share
  (ruling 19); a ring carries no primary (ruling 18);
- ruling 24: a ring, neck, trinket or Intellect item takes no Dodge pair. The ring has Haste / Versatility, and the
  Intellect pieces Haste, Haste / Mastery and Crit / Versatility. Tank stats (Dodge, Parry) sit only on Strength and
  Agility pieces;
- every healer piece is cloth (ruling 11 of the dungeon rules: priests cannot wear leather).

**2922 Save Techbot's Brain!** (level 26, green, item level 31; the stock reward is 20 silver only): a choice of three
**wrists**, one per primary the handoff named: Intellect cloth (Haste), Agility leather (Crit) and Strength plate with
Dodge (the tank pick). Plate is rare at this level, so the Strength wrist is the dungeon's cheapest way into plate.

**2924 Essential Artificials** (level 30, green, item level 35; the stock reward is 55 silver only): one **Spirit cloth
cloak** for healers (Spirit, Haste). The dungeon's list already has a Spirit cloak, Hazmat Drape (`gnomer_hazmat_drape`,
Viscous Fallout, blue, item level 32, Spirit with Mastery / Cooldown Haste); the quest cloak differs in quality, level
and stats and no wave 5 item shares its type, slot and stats. Kept as ruled (#46 A names the Spirit cloak; DQ2 A,
orchestrator ruling 2026-11-26).

**2945 Grime-Encrusted Ring** (level 34, blue, item level 39; the stock reward is nothing, the follow-up quest paid the
rings): one **ring**, Haste / Versatility, no primary. The ring is every role's slot; Haste / Versatility is the pair
the dungeon's loot rings leave out (the Crit pairs are taken).

**2841 Rig Wars** (level 35, blue, item level 40; the three shared blues are dropped): a choice of three, the roles the
dungeon's 48 gear items cover least: an Agility **bow** (the wave's missing one), **Intellect cloth gloves** (Plate
Intellect has one piece, so the Intellect picks are cloth) and **Strength plate gloves with Parry** (the tank pick).

**2929 The Grand Betrayal** (level 35, blue, item level 40; the three shared blues are dropped): a choice of three
**legs**, different slots from Rig Wars: Strength plate (Crit / Mastery), Agility leather with Dodge (the Leather Tank
pick: the dungeon has one) and Intellect cloth (Crit / Versatility).

Each item looks like a stock item of the same slot and level range (`like=`: class, subclass, display, material,
inventory type, sheath). Bind on Pickup: a quest reward is earned once, by its own character. Keys are `gnq_<name>`;
the SQL sets the minted ids literally (rev_quests_gnomeregan.sql) and guards each reward UPDATE on the expected item
name, and lib/test_gnomeregan_dungeon_quests.py pins the ids and the names against item_ids.lock and the declarations
once the write run has minted them (the deploy gate between the write run and db-import). The names and the looks are
placeholders until the designer says otherwise.
"""

from lib.dsl.items import item

from .ladders import QUEST_REWARD

REQUIRED_LEVEL = 0   # ruling 10
BOP = 1              # ITEM_BIND_ON_ACQUIRE
NO_AMMO = 0          # ranged weapons need no ammo (hunter rework Q3), stated like every other new ranged item
GREEN, BLUE = 2, 3
GREEN_SHARE = 8000   # ruling 19
PAIR_SHARE = 6000    # ruling 19: a blue with two secondaries
NO_PRIMARY = 0       # a ring: secondary stats only (ruling 18)

ILEVEL_TECHBOT = 31   # 2922, quest level 26 + 5
ILEVEL_ARTIFICIALS = 35   # 2924, quest level 30 + 5
ILEVEL_RING = 39      # 2945, quest level 34 + 5
ILEVEL_BLUE = 40      # 2841 and 2929, quest level 35 + 5


def _green(key, name, like, ilvl, primary, secondary):
    item(key, name=name, like=like, ilvl=ilvl, quality=GREEN, required_level=REQUIRED_LEVEL, bonding=BOP,
         ladder=QUEST_REWARD, primary=primary, secondary=secondary, primary_share=GREEN_SHARE, unique_equip=False)


def _blue(key, name, like, ilvl, primary, secondary):
    item(key, name=name, like=like, ilvl=ilvl, quality=BLUE, required_level=REQUIRED_LEVEL, bonding=BOP,
         ladder=QUEST_REWARD, primary=primary, secondary=secondary, primary_share=PAIR_SHARE, unique_equip=False)


# ---------------------------------------------------------------------------------------------------------------------
# 2922 Save Techbot's Brain!: three wrist greens, one per primary.

# Intellect cloth (the look is Elder's Bracers). Haste.
_green("gnq_memory_keepers_wraps", "Memory Keeper's Wraps", 7355, ILEVEL_TECHBOT, "Intellect (Solo)", "Haste (Solo)")
# Agility leather (the look is Infiltrator Bracers). Crit.
_green("gnq_memory_keepers_bracers", "Memory Keeper's Bracers", 7410, ILEVEL_TECHBOT, "Agility (Solo)", "Crit (Solo)")
# Strength plate with Dodge (the look is Jouster's Wristguards). Dodge: the tank pick.
_green("gnq_memory_keepers_vambraces", "Memory Keeper's Vambraces", 8156, ILEVEL_TECHBOT, "Strength (Solo)",
       "Dodge (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# 2924 Essential Artificials: one healer cloak.

# Spirit cloth cloak (the look is Prelacy Cape, a priest's). Spirit / Haste, the healer pairing of the Deadmines belt.
_green("gnq_extrapolators_cloak", "Extrapolator's Cloak", 7004, ILEVEL_ARTIFICIALS, "Spirit (Solo)", "Haste (Solo)")

# ---------------------------------------------------------------------------------------------------------------------
# 2945 Grime-Encrusted Ring: one blue ring, no primary.

# The look is Talvash's Gold Ring, the reward this quest replaces. Haste / Versatility.
item("gnq_sparklematic_signet", name="Sparklematic Signet", like=9538, ilvl=ILEVEL_RING, quality=BLUE,
     required_level=REQUIRED_LEVEL, bonding=BOP, ladder=QUEST_REWARD, primary=None,
     secondary="Haste/Versatility", primary_share=NO_PRIMARY, unique_equip=False)

# ---------------------------------------------------------------------------------------------------------------------
# 2841 Rig Wars: a bow, cloth Intellect gloves and tank plate gloves.

# Agility bow (the look is Long Redwood Bow). Crit / Haste.
item("gnq_rigrunners_longbow", name="Rigrunner's Longbow", like=15286, ilvl=ILEVEL_BLUE, quality=BLUE,
     required_level=REQUIRED_LEVEL, bonding=BOP, ammo_type=NO_AMMO, ladder=QUEST_REWARD, primary="Agility (Solo)",
     secondary="Crit/Haste", primary_share=PAIR_SHARE, unique_equip=False)
# Intellect cloth gloves (the look is Stonecloth Gloves). Haste / Mastery.
_blue("gnq_blueprint_readers_mitts", "Blueprint Reader's Mitts", 14411, ILEVEL_BLUE, "Intellect (Solo)",
      "Haste/Mastery")
# Strength plate tank gloves (the look is Field Plate Gauntlets). Parry / Mastery (ruling 12: plate takes Parry).
_blue("gnq_rigbreaker_gauntlets", "Rigbreaker Gauntlets", 9287, ILEVEL_BLUE, "Strength (Solo)", "Parry/Mastery")

# ---------------------------------------------------------------------------------------------------------------------
# 2929 The Grand Betrayal: legs, one per primary.

# Strength plate (the look is Jouster's Legplates). Crit / Mastery.
_blue("gnq_retakers_legplates", "Retaker's Legplates", 8162, ILEVEL_BLUE, "Strength (Solo)", "Crit/Mastery")
# Agility leather tank legs (the look is Cutthroat's Pants). Dodge / Mastery (the Leather Tank pick).
_blue("gnq_retakers_leggings", "Retaker's Leggings", 15139, ILEVEL_BLUE, "Agility (Solo)", "Dodge/Mastery")
# Intellect cloth (the look is Elder's Pants). Crit / Versatility.
_blue("gnq_retakers_pants", "Retaker's Pants", 7368, ILEVEL_BLUE, "Intellect (Solo)", "Crit/Versatility")
