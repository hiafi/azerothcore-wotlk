"""
Quest reward itemization QR0/QR1/QR1b (docs/plans/quest-reward-itemization/): the rules of lib/quest_rewards.py over
hand-built tables, the lock, and the `label=None` tier of the item DSL.

Covered: scope (zone, dungeon and class quests; repeatable, daily, weekly, raid, PvP and out-of-range quests; scaled
(-1) class quests at their MinLevel, other scaled quests and scaled class quests above 60 out; an item an
out-of-scope quest also rewards; shirts, tabards and non-equippable items; fishing poles and Torch of Retribution
stay stock; Legendary and Poor skipped; an entry owned by another declaration skipped with its owner); the quest
level of a multi-quest item (the lowest); every
quality path (white to green, green, blue, epic) with the caps and never-lower; the stock stat read (base dump
columns plus Equip spells through the classifier, never the live row); the white main stat of ruling 18 (each type,
alternating by entry, no main stat on cloaks, rings and necks), held-in-off-hand items Intellect, relics and
primary-less trinkets Null (rulings 22, 25); the nearest primary shape; the generic secondary
pools (green one stat, blue two, epic two or three) and the shares of ruling 19; each tank stat and the Defense
conversion (shield Block, plate Parry, else Dodge; Parry and Block fall back to Dodge without a Strength primary;
without Strength or Agility the tank stat is dropped for Versatility, ruling 24); MP5 on blues and its Spirit
fallback, MP5 dropped on greens and epics;
absorbed and kept spell slots; owned_elsewhere() over a temporary source tree; the lock (parse, render, append-only
seed that keeps hand edits); `tier(label=None)` (no label row) and int shape ids in item(). Round 6 (QR1c): ruling 28
(same name and quest share the lowest entry's shapes; role variants keep their primary), the Argent Dawn gloves at
MinLevel, Parry/Versatility (Any) kept out of the rules, and the lock edit helpers (`replace_lines`, `lock_comments`,
`step_down`). Round 7 (QR1d): ruling 32 (Warrior gear: a Strength primary, Agility comes back as Crit and Intellect
as Proc Chance), ruling 33 (Spell Power (Solo) for caster items, Attack Power (Solo) for Attack Power only items) and
ruling 35 (`step_down_zero`: share 8000 -> 6000 only, no main stat guard).

Optional (slow, real data): QUEST_REWARDS_REAL=1 also expands every real quest_rewards.lock line against the replayed
tables and checks the emitted stats equal `compute_breakdown`.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_quest_rewards.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import quest_rewards as qr  # noqa: E402
from lib.dsl import items as D  # noqa: E402

STR, AGI, INT, SPI, STA = 4, 3, 5, 6, 7
DEF, DODGE, PARRY, BLOCK = 12, 13, 14, 15
CRIT, HASTE, MASTERY, VERS, CDH, PROC, MP5, AP, SP = 32, 36, 22, 23, 24, 33, 43, 38, 45

# The real catalog's ids, names, stats, allocations and rules (item_shape, 2026-11-09), the shapes the rules use.
_SHAPES = [
    (0, 0, "Null (jewelry, 100% secondary)", [], [], []),
    (2, 0, "Int/SpellPower, SpellPower lead", [SP, INT], [6667, 3333], []),
    (6, 0, "Spirit/SpellPower, Spirit lead", [SPI, SP], [6667, 3333], []),
    (12, 0, "Str/AttackPower, Str lead", [STR, AP], [6667, 3333], []),
    (17, 0, "Str/Int/SpellPower, Str lead", [STR, INT, SP], [5000, 2500, 2500], []),
    (22, 0, "Strength (Solo)", [STR], [10000], []),
    (23, 0, "Agility (Solo)", [AGI], [10000], []),
    (24, 0, "Intellect (Solo)", [INT], [10000], []),
    (71, 0, "Spirit (Solo)", [SPI], [10000], []),
    (25, 1, "Crit (Solo)", [CRIT], [10000], []),
    (26, 1, "Haste (Solo)", [HASTE], [10000], []),
    (27, 1, "Mastery (Solo)", [MASTERY], [10000], []),
    (28, 1, "Versatility (Solo)", [VERS], [10000], []),
    (72, 1, "CDH (Solo)", [CDH], [10000], []),
    (73, 1, "Proc (Solo)", [PROC], [10000], []),
    (29, 1, "Crit/Haste", [CRIT, HASTE], [5000, 5000], []),
    (32, 1, "Crit/Versatility", [CRIT, VERS], [5000, 5000], []),
    (35, 1, "Haste/Versatility", [HASTE, VERS], [5000, 5000], []),
    (36, 1, "Mastery/Versatility", [MASTERY, VERS], [5000, 5000], []),
    (67, 1, "Mastery/Versatility, Mastery lead", [MASTERY, VERS], [6667, 3333], []),
    (74, 1, "CDH/Versatility", [CDH, VERS], [5000, 5000], []),
    (42, 1, "Crit/Haste/Mastery", [CRIT, HASTE, MASTERY], [3334, 3333, 3333], []),
    (48, 1, "MP5/Crit", [MP5, CRIT], [5000, 5000], [(2, SPI)]),
    (49, 1, "MP5/Haste", [MP5, HASTE], [5000, 5000], [(2, SPI)]),
    (47, 1, "MP5 (Solo)", [MP5], [10000], [(2, SPI)]),
    (54, 1, "Dodge (Solo)", [DODGE], [10000], [(1, STR), (1, AGI)]),
    (55, 1, "Parry (Solo)", [PARRY], [10000], [(1, STR)]),
    (56, 1, "Block (Solo)", [BLOCK], [10000], [(1, STR)]),
    (57, 1, "Dodge/Crit", [DODGE, CRIT], [5000, 5000], [(1, STR), (1, AGI)]),
    (58, 1, "Dodge/Haste", [DODGE, HASTE], [5000, 5000], [(1, STR), (1, AGI)]),
    (60, 1, "Parry/Crit", [PARRY, CRIT], [5000, 5000], [(1, STR)]),
    (61, 1, "Block/Crit", [BLOCK, CRIT], [5000, 5000], [(1, STR)]),
    (62, 1, "Dodge/Parry", [DODGE, PARRY], [5000, 5000], [(1, STR)]),
    (80, 1, "Dodge (Solo, Any)", [DODGE], [10000], []),
]
COSTS = {STR: 1.0, AGI: 1.0, INT: 1.0, SPI: 1.0, AP: 0.5, SP: 0.855}
GREEN_POOL = [25, 26, 27, 28, 72, 73]
BLUE_POOL = [29, 32, 35, 36, 67, 74]
EPIC_POOL = [29, 32, 35, 36, 42, 67, 74]
VERS_PAIRS = [32, 35, 36, 67, 74]


# Round 6: the three new shapes, the pairs ruling 32 reaches and an Agi/AttackPower primary (kept out of the default
# catalog so the generic pools of the older tests stay as they are).
_ROUND6_SHAPES = [
    (81, 0, "Spell Power (Solo)", [SP], [10000], []),
    (82, 0, "Attack Power (Solo)", [AP], [10000], []),
    (83, 1, "Parry/Versatility (Any)", [PARRY, VERS], [5000, 5000], []),
    (30, 1, "Crit/Mastery", [CRIT, MASTERY], [5000, 5000], []),
    (39, 1, "Crit/Proc", [CRIT, PROC], [5000, 5000], []),
    (40, 1, "Haste/Proc", [HASTE, PROC], [5000, 5000], []),
    (41, 1, "Crit/Haste, Crit lead", [CRIT, HASTE], [6667, 3333], []),
    (15, 0, "Agi/AttackPower, Agi lead", [AGI, AP], [6667, 3333], []),
]


def catalog(round6: bool = False) -> qr.Catalog:
    shapes = {sid: {"shape_id": sid, "kind": kind, "name": name, "stats": stats, "alloc": alloc, "rules": rules}
              for sid, kind, name, stats, alloc, rules in _SHAPES + (_ROUND6_SHAPES if round6 else [])}
    return qr.Catalog(shapes, COSTS)


def item_row(entry, quality=2, ilvl=10, cls=4, subclass=1, inv=5, name=None, **cols) -> dict:
    row = {"entry": entry, "name": name or f"Item {entry}", "Quality": quality, "ItemLevel": ilvl, "class": cls,
           "subclass": subclass, "InventoryType": inv}
    for n in range(1, 11):
        row.setdefault(f"stat_type{n}", 0)
        row.setdefault(f"stat_value{n}", 0)
    for n in range(1, 6):
        row.setdefault(f"spellid_{n}", 0)
        row.setdefault(f"spelltrigger_{n}", 0)
    row.update(cols)
    return row


def with_stats(row: dict, *stats: tuple[int, int]) -> dict:
    row = dict(row)
    for n, (stat, value) in enumerate(stats, 1):
        row[f"stat_type{n}"], row[f"stat_value{n}"] = stat, value
    return row


def spell(spell_id, *effects) -> dict:
    """effects: (effect, aura, misc, base points)"""
    row = {"ID": spell_id}
    for n in (1, 2, 3):
        effect, aura, misc, bp = effects[n - 1] if n <= len(effects) else (0, 0, 0, 0)
        row.update({f"Effect_{n}": effect, f"EffectAura_{n}": aura, f"EffectMiscValue_{n}": misc,
                    f"EffectBasePoints_{n}": bp})
    return row


AURA = qr.EFFECT_APPLY_AURA
SPELLS = {
    9416: spell(9416, (AURA, 13, 126, 10), (AURA, 135, 126, 10)),  # +11 spell power (damage + healing companion)
    9331: spell(9331, (AURA, 99, 0, 19), (AURA, 124, 0, 19)),  # +20 attack power
    13669: spell(13669, (AURA, 189, 4, 11)),  # +12 Dodge rating (CR_DODGE bit 2)
    13674: spell(13674, (AURA, 189, 16, 4)),  # +5 Block rating (bit 4)
    13387: spell(13387, (AURA, 189, 2, 6)),  # +7 Defense rating (bit 1)
    21625: spell(21625, (AURA, 85, 0, 2)),  # +3 MP5
    7617: spell(7617, (AURA, 42, 0, -1)),  # a proc: kept
    19691: spell(19691, (AURA, 102, 1, 17), (AURA, 131, 1, 17)),  # Beast Slaying: kept
    21189: spell(21189, (AURA, 13, 1, 3)),  # physical damage done: not spell power, kept
    26283: spell(26283, (AURA, 123, 124, -21)),  # +20 spell penetration (absorbed, the stat is excluded)
    9395: spell(9395, (AURA, 29, -1, 2)),  # +3 all stats
    14119: spell(14119, (2, 0, 0, 34)),  # a damage spell (Chance on hit)
}


def quest(qid, level, title=None, sort=12, info=0, flags=0, min_level=0, **cols) -> dict:
    row = {"ID": qid, "QuestLevel": level, "LogTitle": title or f"Quest {qid}", "QuestSortID": sort,
           "QuestInfoID": info, "Flags": flags, "MinLevel": min_level}
    for c in qr.REWARD_COLUMNS:
        row[c] = 0
    row.update(cols)
    return row


def decide(row, base=None, quest_level=10, spells=SPELLS, classes=frozenset(), cat=None):
    quests = [qr.Quest(1, quest_level, "Q", "class" if classes else "zone", classes=frozenset(classes))]
    return qr.decide(row["entry"], quests, row, base or row, spells, cat or catalog())


class ScopeTest(unittest.TestCase):
    def setUp(self):
        self.rows = {e: item_row(e) for e in range(100, 126)}
        self.rows[121] = item_row(121, quality=1, cls=2, subclass=20, inv=17)  # a fishing pole
        self.rows[10515] = item_row(10515, quality=1, cls=4, subclass=0, inv=17)  # Torch of Retribution
        self.rows[3567] = item_row(3567, quality=2, cls=2, subclass=3, inv=26)  # Dwarven Fishing Pole (a gun)
        self.rows[864] = item_row(864, quality=2, cls=2, subclass=7, inv=13)  # Knightly Longsword
        self.rows[110] = item_row(110, inv=4)  # shirt
        self.rows[111] = item_row(111, inv=19)  # tabard
        self.rows[112] = item_row(112, cls=12, inv=0)  # a quest item
        self.rows[113] = item_row(113, quality=5)  # legendary
        self.rows[114] = item_row(114, quality=0)  # poor
        self.quests = {
            1: quest(1, 12, RewardItem1=100, RewardChoiceItemID1=101),  # zone
            2: quest(2, 25, info=qr.QUEST_INFO_DUNGEON, RewardChoiceItemID2=102),  # dungeon
            3: quest(3, 30, sort=-81, RewardItem2=103),  # class (QuestSortID < 0)
            4: quest(4, 20, RewardItem1=104),  # class by AllowableClasses (addon)
            5: quest(5, 20, RewardItem1=105),  # repeatable (addon)
            6: quest(6, 20, flags=qr.QUEST_FLAGS_DAILY, RewardItem1=106),
            7: quest(7, 20, flags=qr.QUEST_FLAGS_WEEKLY, RewardItem1=107),
            8: quest(8, 60, info=qr.QUEST_INFO_RAID, RewardItem1=108),
            9: quest(9, 20, info=qr.QUEST_INFO_PVP, RewardItem1=109),
            10: quest(10, 20, RewardItem1=110, RewardItem2=111, RewardItem3=112, RewardItem4=113,
                      RewardChoiceItemID1=114),
            11: quest(11, 70, RewardItem1=115),  # above 60
            12: quest(12, -1, RewardItem1=116),  # scaled: no quest level
            13: quest(13, 22, RewardItem1=100),  # 100 again, from a higher quest
            14: quest(14, 15, RewardItem1=117),
            15: quest(15, 15, RewardItem1=101, flags=qr.QUEST_FLAGS_DAILY),  # 101 is also a daily reward
            16: quest(16, 30, RewardItem1=118),
            17: quest(17, -1, sort=-263, min_level=16, RewardItem1=119),  # scaled druid quest: MinLevel 16
            18: quest(18, -1, sort=12, min_level=20, RewardItem1=120),  # scaled, class by AllowableClasses
            19: quest(19, -1, sort=-263, min_level=70, RewardItem1=122),  # scaled class quest above 60
            20: quest(20, -1, sort=-101, min_level=10, RewardItem1=123),  # scaled fishing quest: not a class quest
            21: quest(21, 10, RewardItem1=121, RewardItem2=10515, RewardItem3=3567, RewardItem4=864),
            22: quest(22, 8, RewardItem1=124),  # 124 also from scaled quest 23 at MinLevel 5: the lowest
            23: quest(23, -1, sort=-61, min_level=5, RewardItem1=124),
        }
        self.addons = {4: {"AllowableClasses": 1}, 5: {"SpecialFlags": 1}, 18: {"AllowableClasses": 2}}

    def test_scope_and_kinds(self):
        s = qr.scope(self.quests, self.addons, self.rows, owned={118: "source/items/deadmines.py"})
        self.assertEqual(sorted(s.items), [100, 102, 103, 104, 117, 119, 120, 124])
        self.assertEqual(s.items[102][0].kind, "dungeon")
        self.assertEqual(s.items[103][0].kind, "class")
        self.assertEqual(s.items[104][0].kind, "class")
        self.assertEqual(s.items[117][0].kind, "zone")
        for entry, word in ((105, "repeatable"), (106, "daily"), (107, "weekly"), (108, "raid"), (109, "PvP"),
                            (115, "quest level 70"), (116, "quest level -1"), (101, "daily"),
                            (122, "scaled class quest, MinLevel 70"), (123, "quest level -1"),
                            (121, "fishing pole (ruling 25)"), (10515, "Torch of Retribution (ruling 25)"),
                            (3567, "Dwarven Fishing Pole"), (864, "Knightly Longsword")):
            self.assertIn(word, s.skipped[entry], entry)
        self.assertIn("ruling 16", s.skipped[113])
        self.assertIn("ruling 17", s.skipped[114])
        self.assertEqual(s.skipped[118], "owned by source/items/deadmines.py")
        for entry in (110, 111, 112):  # not equippable rewards: neither in scope nor listed
            self.assertNotIn(entry, s.items)
            self.assertNotIn(entry, s.skipped)

    def test_scaled_class_quests_count_at_their_min_level(self):
        s = qr.scope(self.quests, self.addons, self.rows)
        self.assertEqual([(q.level, q.kind, q.scaled) for q in s.items[119]], [(16, "class", True)])
        self.assertEqual([(q.level, q.scaled) for q in s.items[120]], [(20, True)])
        self.assertEqual([(q.id, q.level) for q in s.items[124]], [(23, 5), (22, 8)])
        self.assertTrue(qr.is_class_quest(self.quests[17], None))
        self.assertFalse(qr.is_class_quest(self.quests[20], None))
        self.assertEqual(qr.quest_level(self.quests[20], None), (-1, False))

    def test_multi_quest_item_takes_the_lowest_quest_level(self):
        s = qr.scope(self.quests, self.addons, self.rows)
        self.assertEqual([q.level for q in s.items[100]], [12, 22])
        d = qr.decide_all(s, self.rows, self.rows, SPELLS, catalog())
        self.assertEqual(next(x for x in d if x.entry == 100).quest_level, 12)


class LevelTest(unittest.TestCase):
    def test_targets(self):
        self.assertEqual(qr.target(1, 5, 10)[:2], (2, 12))  # white -> green at quest level + 2
        self.assertEqual(qr.target(1, 5, 58)[:2], (2, 55))  # green cap
        self.assertEqual(qr.target(2, 10, 10)[:2], (2, 15))  # green + 5
        self.assertEqual(qr.target(2, 20, 52)[:2], (2, 55))  # capped
        self.assertEqual(qr.target(3, 20, 10)[:2], (3, 20))  # never lower: already above quest level + 5
        self.assertEqual(qr.target(3, 20, 10)[2], "ilvl 20 kept (target 15)")  # never lower
        self.assertEqual(qr.target(3, 30, 58)[:2], (3, 60))  # blue cap 60
        self.assertEqual(qr.target(3, 63, 58)[:2], (3, 63))  # never lower above the cap
        self.assertEqual(qr.target(2, 58, 55)[:2], (2, 58))
        self.assertEqual(qr.target(4, 70, 60)[:2], (4, 70))  # epic keeps its level
        self.assertEqual(qr.target(1, 9, 3)[:2], (2, 9))  # a white above its target keeps its level, turns green


class StockReadTest(unittest.TestCase):
    def test_columns_plus_equip_spells_from_the_base_row(self):
        base = with_stats(item_row(1, spellid_1=9416, spelltrigger_1=1, spellid_2=13669, spelltrigger_2=1,
                                   spellid_3=7617, spelltrigger_3=1, spellid_4=9331, spelltrigger_4=0),
                          (INT, 5), (STA, 4), (DEF, 3))
        self.assertEqual(qr.stock_read(base, SPELLS), {INT: 5, STA: 4, DEF: 3, SP: 11, DODGE: 12})

    def test_classifier(self):
        self.assertEqual(qr.spell_stat_effects(SPELLS[9331]), {AP: 20})  # 124 is 99's companion
        self.assertEqual(qr.spell_stat_effects(SPELLS[21625]), {MP5: 3})
        self.assertEqual(qr.spell_stat_effects(SPELLS[26283]), {47: 20})
        self.assertEqual(qr.spell_stat_effects(SPELLS[9395]), {STR: 3, AGI: 3, STA: 3, INT: 3, SPI: 3})
        self.assertEqual(qr.spell_stat_effects(SPELLS[13387]), {DEF: 7})
        for kept in (7617, 19691, 21189, 14119):
            self.assertIsNone(qr.spell_stat_effects(SPELLS[kept]), kept)
        self.assertIsNone(qr.spell_stat_effects(None))

    def test_the_live_row_is_never_read_for_stats(self):
        # A converted item: the live row lost its Defense and its spell; the base dump still has them.
        base = with_stats(item_row(2, quality=3, ilvl=30, subclass=4, spellid_1=13387, spelltrigger_1=1),
                          (STR, 8), (DEF, 5))
        live = with_stats(item_row(2, quality=3, ilvl=30, subclass=4), (STR, 9), (STA, 9))
        d = decide(live, base, quest_level=25)
        self.assertEqual(d.stock, {STR: 8, DEF: 12})
        self.assertEqual(catalog().stats(d.secondary)[0], PARRY)  # plate: Defense -> Parry
        self.assertEqual((d.kept, d.absorbed), ((), ()))  # the live row has no spell left to absorb


class SpellSlotTest(unittest.TestCase):
    def test_absorbed_and_kept(self):
        row = item_row(3, spellid_1=9416, spelltrigger_1=1, spellid_2=7617, spelltrigger_2=1,
                       spellid_3=9331, spelltrigger_3=0, spellid_4=14119, spelltrigger_4=2,
                       spellid_5=999999, spelltrigger_5=1)
        self.assertEqual(qr.spell_slots(row, SPELLS), ((2, 3, 4, 5), (1,)))
        d = decide(row)
        self.assertEqual(d.spells_field, "2,3,4,5")
        self.assertEqual(decide(item_row(4, spellid_1=9416, spelltrigger_1=1)).spells_field, "-")
        self.assertEqual(decide(item_row(5, spellid_2=7617, spelltrigger_2=1)).spells_field, "all")
        self.assertEqual(decide(item_row(6)).spells_field, "-")


class PrimaryTest(unittest.TestCase):
    def white(self, entry, cls, subclass, inv):
        return decide(item_row(entry, quality=1, ilvl=5, cls=cls, subclass=subclass, inv=inv), quest_level=8)

    def test_white_main_stat_by_type(self):
        cat = catalog()
        cases = [
            ((4, 1, 5), "Intellect (Solo)"), ((4, 2, 7), "Agility (Solo)"), ((4, 4, 10), "Strength (Solo)"),
            ((4, 6, 14), "Strength (Solo)"), ((2, 15, 13), "Agility (Solo)"), ((2, 13, 13), "Agility (Solo)"),
            ((2, 6, 17), "Agility (Solo)"), ((2, 2, 15), "Agility (Solo)"), ((2, 3, 26), "Agility (Solo)"),
            ((2, 18, 26), "Agility (Solo)"), ((2, 16, 25), "Agility (Solo)"), ((2, 10, 17), "Intellect (Solo)"),
            ((2, 19, 26), "Intellect (Solo)"), ((2, 0, 13), "Strength (Solo)"), ((2, 1, 17), "Strength (Solo)"),
            ((2, 8, 17), "Strength (Solo)"), ((2, 5, 17), "Strength (Solo)"),
        ]
        for n, ((cls, subclass, inv), want) in enumerate(cases):
            d = self.white(1000 + 2 * n, cls, subclass, inv)
            self.assertEqual(cat.shapes[d.primary]["name"], want, (cls, subclass, inv))
            self.assertEqual((d.quality, d.share), (2, 8000))
            self.assertIn("white->green", d.paths)

    def test_alternating_by_entry(self):
        cat = catalog()
        for (subclass, cls, inv), (even, odd) in (((3, 4, 5), ("Agility (Solo)", "Intellect (Solo)")),
                                                  ((7, 2, 13), ("Strength (Solo)", "Agility (Solo)")),
                                                  ((4, 2, 13), ("Strength (Solo)", "Intellect (Solo)"))):
            self.assertEqual(cat.shapes[self.white(2000, cls, subclass, inv).primary]["name"], even)
            self.assertEqual(cat.shapes[self.white(2001, cls, subclass, inv).primary]["name"], odd)

    def test_cloaks_rings_and_necks_have_no_primary(self):
        for inv, subclass in ((16, 1), (11, 0), (2, 0)):
            for quality in (1, 2, 3, 4):
                d = decide(with_stats(item_row(3000 + inv, quality=quality, ilvl=30, subclass=subclass, inv=inv),
                                      (STR, 5)), quest_level=25)
                self.assertEqual((d.primary, d.share), (0, 0), (inv, quality))

    def test_nearest_primary(self):
        cat = catalog()
        d = decide(with_stats(item_row(5, quality=2), (STR, 8), (AGI, 2), (STA, 5)))
        self.assertEqual(cat.shapes[d.primary]["name"], "Strength (Solo)")
        # Least squares, as the stock conversion: Str 60 / Agi 40 is nearer Str 67 / AP 33 than Str 100.
        d = decide(with_stats(item_row(5, quality=2), (STR, 6), (AGI, 4), (STA, 5)))
        self.assertEqual(cat.shapes[d.primary]["name"], "Str/AttackPower, Str lead")
        d = decide(with_stats(item_row(5, quality=2, spellid_1=9416, spelltrigger_1=1), (INT, 4)))
        self.assertEqual(cat.shapes[d.primary]["name"], "Int/SpellPower, SpellPower lead")
        d = decide(with_stats(item_row(5, quality=2), (SPI, 7)))
        self.assertEqual(cat.shapes[d.primary]["name"], "Spirit (Solo)")
        # Str 50 / Agi 50: plain least squares picks the Str/Int/SpellPower trio; the role rule keeps it physical.
        even = {STR: 9, AGI: 9}
        self.assertEqual(cat.shapes[qr.nearest_primary(even, cat, keep_role=False)]["name"],
                         "Str/Int/SpellPower, Str lead")
        self.assertEqual(cat.shapes[qr.nearest_primary(even, cat)]["name"], "Str/AttackPower, Str lead")
        self.assertEqual(qr.allowed_primary_stats({STR: 1, SPI: 1, STA: 3}), {STR, SPI, AP, SP})

    def test_no_stock_primary_falls_back_to_the_type(self):
        d = decide(with_stats(item_row(6, quality=2, cls=2, subclass=15, inv=13), (STA, 5)))
        self.assertEqual(catalog().shapes[d.primary]["name"], "Agility (Solo)")
        self.assertTrue(any("type Agi (dagger)" in f for f in d.fallbacks))
        # A tank item with no stock primary takes Agility where the type would give it Intellect (odd mail entry).
        d = decide(with_stats(item_row(9625, quality=3, ilvl=37, subclass=3, inv=7), (DEF, 7)), quest_level=35)
        self.assertEqual(catalog().shapes[d.primary]["name"], "Agility (Solo)")
        self.assertEqual(catalog().stats(d.secondary)[0], DODGE)
        d = decide(with_stats(item_row(7, quality=2, subclass=0, inv=12), (STA, 5)))  # a trinket: ruling 22
        self.assertEqual((d.primary, d.share, d.fallbacks), (0, 0, []))
        self.assertIn("no primary (trinket, ruling 22)", d.paths)
        d = decide(with_stats(item_row(8, quality=3, ilvl=30, subclass=0, inv=12), (AGI, 5)))  # a trinket with Agi
        self.assertEqual(catalog().shapes[d.primary]["name"], "Agility (Solo)")

    def test_held_in_off_hand_and_relics(self):
        cat = catalog()
        for quality in (1, 2, 3):  # ruling 25: Intellect, white or not, when there is no stock main stat
            d = decide(item_row(9, quality=quality, ilvl=20, subclass=0, inv=23), quest_level=18)
            self.assertEqual(cat.shapes[d.primary]["name"], "Intellect (Solo)", quality)
            self.assertEqual(d.fallbacks, [])
            self.assertIn("type Int (held in off-hand, ruling 25)", d.paths)
        d = decide(with_stats(item_row(9, quality=3, ilvl=20, subclass=0, inv=23), (SPI, 7)))
        self.assertEqual(cat.shapes[d.primary]["name"], "Spirit (Solo)")  # a stock main stat: the nearest shape
        for quality in (1, 2, 3, 4):  # relics: Null, all secondary, even with a stock main stat
            d = decide(with_stats(item_row(10, quality=quality, ilvl=62, subclass=8, inv=28), (STR, 5)),
                       quest_level=60)
            self.assertEqual((d.primary, d.share, d.fallbacks), (0, 0, []), quality)
            self.assertIn("no primary (relic)", d.paths)


class SecondaryTest(unittest.TestCase):
    def test_generic_pools_and_shares(self):
        for entry in range(20):
            green = decide(with_stats(item_row(entry, quality=2), (STR, 5)))
            self.assertEqual(green.secondary, GREEN_POOL[entry % 6])
            self.assertEqual(green.share, 8000)
            blue = decide(with_stats(item_row(entry, quality=3, ilvl=20), (STR, 5)))
            self.assertEqual(blue.secondary, BLUE_POOL[entry % len(BLUE_POOL)])
            self.assertEqual(blue.share, 6000)
            epic = decide(with_stats(item_row(entry, quality=4, ilvl=62), (STR, 5)), quest_level=60)
            self.assertEqual(epic.secondary, EPIC_POOL[entry % len(EPIC_POOL)])
            self.assertEqual(epic.share, 4000 if epic.secondary == 42 else 6000)
            self.assertEqual(epic.ilvl, 62)

    def test_tank_stats_kept(self):
        cat = catalog()
        for stat, spell_id in ((DODGE, 13669), (BLOCK, 13674)):
            for quality, size in ((2, 1), (3, 2), (4, 2)):
                row = with_stats(item_row(40, quality=quality, ilvl=30, subclass=4, inv=10,
                                          spellid_1=spell_id, spelltrigger_1=1), (STR, 6))
                d = decide(row, quest_level=28)
                stats = cat.stats(d.secondary)
                self.assertEqual((stats[0], len(stats)), (stat, size), (stat, quality))
                self.assertEqual(d.absorbed, (1,))
        d = decide(with_stats(item_row(41, quality=3, ilvl=30, subclass=4, inv=10), (STR, 6), (PARRY, 5)))
        self.assertEqual(cat.stats(d.secondary)[0], PARRY)

    def test_defense_conversion(self):
        cat = catalog()
        for subclass, inv, want in ((6, 14, BLOCK), (4, 10, PARRY), (3, 10, DODGE), (2, 10, DODGE), (1, 10, DODGE)):
            d = decide(with_stats(item_row(50, quality=2, ilvl=20, subclass=subclass, inv=inv), (STR, 4), (DEF, 5)))
            self.assertEqual(cat.stats(d.secondary), [want], subclass)
            self.assertIn(f"Defense->{qr.STAT_NAMES[want]}", d.paths)
        d = decide(with_stats(item_row(51, quality=2, ilvl=20, cls=2, subclass=10, inv=17), (STR, 4), (DEF, 5)))
        self.assertEqual(cat.stats(d.secondary), [DODGE])  # a weapon: Dodge

    def test_parry_and_block_need_strength(self):
        cat = catalog()
        d = decide(with_stats(item_row(53, quality=3, ilvl=30, subclass=6, inv=14), (AGI, 6), (DEF, 5)))
        self.assertEqual(cat.stats(d.secondary)[0], DODGE)  # a shield with an Agility primary: Dodge pair
        self.assertEqual(len(cat.stats(d.secondary)), 2)
        d = decide(with_stats(item_row(55, quality=4, ilvl=62, subclass=2, inv=5), (AGI, 6), (PARRY, 5)),
                   quest_level=60)
        self.assertEqual(cat.stats(d.secondary)[0], DODGE)  # Parry without Str, but Agility: a Dodge pair
        self.assertTrue(any("Parry needs Str" in f for f in d.fallbacks))

    def test_no_dodge_shape_drops_the_tank_stat_for_versatility(self):
        cat = catalog()
        # Ruling 24: an Intellect item, a ring, a trinket, a cloak cannot take a Dodge shape.
        d = decide(with_stats(item_row(52, quality=3, ilvl=30, subclass=4, inv=10), (INT, 6), (DEF, 5)))
        self.assertEqual(d.primary, 24)
        self.assertEqual(d.secondary, VERS_PAIRS[52 % len(VERS_PAIRS)])
        self.assertIn(VERS, cat.stats(d.secondary))
        self.assertTrue(any("Parry needs Str" in f for f in d.fallbacks))  # plate Defense -> Parry -> Dodge -> Vers
        self.assertIn("tank Dodge dropped, no Str/Agi (ruling 24): Vers", d.paths)
        for entry, inv, quality in ((60, 11, 4), (61, 12, 4), (62, 2, 3), (63, 11, 3), (64, 16, 4)):
            d = decide(with_stats(item_row(entry, quality=quality, ilvl=62, subclass=0, inv=inv), (DODGE, 9)),
                       quest_level=60)
            self.assertEqual(d.secondary, VERS_PAIRS[entry % len(VERS_PAIRS)], (entry, inv))
            self.assertEqual((d.primary, d.share), (0, 0))
            self.assertFalse(set(cat.stats(d.secondary)) & {DODGE, PARRY, BLOCK, DEF})
        d = decide(with_stats(item_row(54, quality=2, ilvl=30, inv=16), (DEF, 5)))  # a green cloak: Vers alone
        self.assertEqual(cat.shapes[d.secondary]["name"], "Versatility (Solo)")
        d = decide(with_stats(item_row(56, quality=2, ilvl=30, subclass=0, inv=12), (PARRY, 5)))  # a green trinket
        self.assertEqual(cat.shapes[d.secondary]["name"], "Versatility (Solo)")
        for d in (decide(with_stats(item_row(n, quality=q, ilvl=62, inv=11), (DODGE, 9)), quest_level=60)
                  for n in range(70, 80) for q in (2, 3, 4)):
            self.assertNotEqual(cat.shapes[d.secondary]["name"], "Dodge (Solo, Any)")
        # An item that can take a Dodge pair keeps it (9625: no stock primary, odd mail: Agility + Dodge pair).
        d = decide(with_stats(item_row(9625, quality=3, ilvl=37, subclass=3, inv=7), (DEF, 7)), quest_level=35)
        self.assertEqual(catalog().shapes[d.primary]["name"], "Agility (Solo)")
        self.assertEqual(cat.stats(d.secondary)[0], DODGE)

    def test_mp5(self):
        cat = catalog()
        blue = with_stats(item_row(60, quality=3, ilvl=30, spellid_1=21625, spelltrigger_1=1), (INT, 6))
        d = decide(blue, quest_level=25)
        self.assertEqual(cat.stats(d.secondary)[0], MP5)
        self.assertIn(d.secondary, (48, 49))
        self.assertIn("MP5 kept", d.paths)
        spirit = with_stats(item_row(61, quality=3, ilvl=30, spellid_1=21625, spelltrigger_1=1), (SPI, 6))
        d = decide(spirit, quest_level=25)
        self.assertEqual(cat.shapes[d.primary]["name"], "Spirit (Solo)")
        self.assertIn(d.secondary, BLUE_POOL)
        self.assertTrue(any("Spirit primary kept" in f for f in d.fallbacks))
        for quality in (2, 4):
            row = with_stats(item_row(62, quality=quality, ilvl=62, spellid_1=21625, spelltrigger_1=1), (INT, 6))
            d = decide(row, quest_level=60)
            self.assertNotIn(MP5, cat.stats(d.secondary))
            self.assertTrue(any("blues only" in f for f in d.fallbacks))


class OwnedElsewhereTest(unittest.TestCase):
    def test_owners(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            items = root / "source" / "items"
            world = root / "source" / "world"
            items.mkdir(parents=True)
            world.mkdir()
            (items / "deadmines.py").write_text("item('dm_x', base=5187, ladder=L)\n")
            (items / "quest_rewards.py").write_text("item('qr_1', base=4975, ladder=L)\n")
            (items / "item_ids.lock").write_text("5443 dm_buckler normal base\n71000 dm_x heroic\n"
                                                 "4975 qr_4975 normal base\n")
            (root / "source" / "items.csv").write_text("id,class_id\n70100,4\n")
            (world / "quivers.py").write_text("item_template(2101, **{'class': 1})\n")
            (world / "ranged_weapons.py").write_text("item_template(2504, ammo_type=0)\n")
            owned = qr.owned_elsewhere(root)
        self.assertEqual(owned, {
            5187: "source/items/deadmines.py", 5443: "item_ids.lock (dm_buckler)", 71000: "item_ids.lock (dm_x)",
            70100: "source/items.csv", 2101: "source/world/quivers.py item_template()",
        })


class LockTest(unittest.TestCase):
    def decisions(self):
        rows = [with_stats(item_row(e, quality=2, name=f"Thing {e}"), (STR, 5)) for e in (300, 301)]
        return [decide(r) for r in rows]

    def test_render_parse_round_trip(self):
        cat = catalog()
        text, appended, stale = qr.seed("", self.decisions(), cat)
        self.assertTrue(text.startswith(qr.LOCK_HEADER))
        self.assertEqual(len(appended), 2)
        self.assertEqual(stale, [])
        lines = qr.parse_lock(text)
        self.assertEqual(sorted(lines), [300, 301])
        line = lines[300]
        self.assertEqual((line.quest_level, line.quality, line.ilvl, line.primary, line.share, line.spells),
                         (10, 2, 15, 22, 8000, "-"))
        self.assertEqual(line.key, "qr_300")
        self.assertTrue(line.comment.startswith("Thing 300 -- Str / "))
        self.assertEqual(qr.LockLine(1, 1, 2, 5, 0, 25, 0, "all").kept_slots, None)
        self.assertEqual(qr.LockLine(1, 1, 2, 5, 0, 25, 0, "1,3").kept_slots, (1, 3))

    def test_append_only_keeps_hand_edits(self):
        cat = catalog()
        first, _, _ = qr.seed("", self.decisions()[:1], cat)
        edited = first.replace("300 10 2 15 22", "300 10 2 17 23")
        text, appended, stale = qr.seed(edited, self.decisions(), cat)
        self.assertIn("300 10 2 17 23", text)  # the hand edit stays
        self.assertEqual([a.split()[0] for a in appended], ["301"])
        again, appended_again, _ = qr.seed(text, self.decisions(), cat)
        self.assertEqual((again, appended_again), (text, []))
        _, _, stale = qr.seed(text, self.decisions()[1:], cat)
        self.assertEqual(stale, [300])  # reported, never removed

    def test_a_long_comment_wraps_under_its_entry(self):
        row = with_stats(item_row(302, quality=2, cls=2, subclass=15, inv=13, name="A Very Long Item Name " * 3),
                         (STA, 5))
        text, _, _ = qr.seed("", [decide(row)], catalog())
        body = text[len(qr.LOCK_HEADER):].splitlines()
        self.assertGreater(len(body), 1)
        self.assertTrue(all(len(line) <= qr.MAX_LINE for line in body))
        self.assertTrue(all(line.startswith(qr.CONTINUATION) for line in body[1:]))
        self.assertEqual(sorted(qr.parse_lock(text)), [302])

    def test_malformed_lines(self):
        for bad in ("300 10 2 15 22 25 8000", "300 10 2 15 22 25 8000 6", "x 10 2 15 22 25 8000 -",
                    "300 10 2 15 22 25 8000 -\n300 10 2 15 22 25 8000 -"):
            with self.assertRaises(qr.LockError, msg=bad):
                qr.parse_lock(bad)
        self.assertEqual(qr.parse_lock("# only a comment\n\n"), {})


class DslTest(unittest.TestCase):
    def test_tier_without_label(self):
        lad = D.ladder("quest_reward", normal=D.tier(step=0, label=None))
        self.assertIsNone(lad.tiers[0].label)
        with self.assertRaises(D.ItemDeclarationError):
            D.tier(step=0, label="")
        two = D.ladder("two", a=D.tier(step=0, label=None),
                       b=D.tier(step=1, label=None, ilvl=30, quality=3, required_level=0))
        self.assertEqual([t.label for t in two.tiers], [None, None])  # two unlabelled tiers do not clash
        decl = D.item("qr_5", base=5, ladder=lad, ilvl=20, quality=2, required_level=0, primary=22, secondary=25,
                      primary_share=8000, unique_equip=False)
        self.assertEqual((decl.primary, decl.secondary), (22, 25))
        for bad in (-1, 0, True):
            with self.assertRaises(D.ItemDeclarationError):
                D.item("qr_6", base=6, ladder=lad, primary=bad, secondary=25)


class RoundSixTest(unittest.TestCase):
    """Round 6 (QR1c): rulings 28 and 30, the Argent Dawn gloves at MinLevel, the hand-only shapes, the lock edit
    helpers."""

    def test_quest_classes(self):
        self.assertEqual(qr.quest_classes(quest(1, 10, sort=-81), None), {"Warrior"})
        self.assertEqual(qr.quest_classes(quest(1, 10), {"AllowableClasses": 1 | 2}), {"Warrior", "Paladin"})
        self.assertEqual(qr.quest_classes(quest(1, 10, sort=-101), None), frozenset())  # fishing: no class
        self.assertEqual(qr.quest_classes(quest(1, 10), None), frozenset())

    def test_ruling_32_warrior_agility_becomes_strength_and_crit(self):
        cat = catalog(round6=True)
        dagger = item_row(6001, quality=1, ilvl=10, cls=2, subclass=15, inv=13)  # white dagger: Agi; 6001 % 6 -> Haste
        plain = decide(dagger, quest_level=10, cat=cat)
        self.assertEqual((cat.shapes[plain.primary]["name"], cat.stats(plain.secondary)), ("Agility (Solo)", [HASTE]))
        d = decide(dagger, quest_level=10, classes={"Warrior"}, cat=cat)
        self.assertEqual((cat.shapes[d.primary]["name"], d.share, cat.shapes[d.secondary]["name"]),
                         ("Strength (Solo)", 8000, "Crit/Haste"))
        self.assertTrue(any("ruling 32" in p for p in d.paths))
        crit = decide(item_row(6000, quality=1, ilvl=10, cls=2, subclass=15, inv=13), classes={"Warrior"}, cat=cat)
        self.assertEqual(cat.shapes[crit.secondary]["name"], "Crit (Solo)")  # already Crit: Crit alone
        # An Agi/AttackPower primary keeps its Attack Power: the nearest Strength shape is Str/AttackPower; a blue
        # keeps the blue share.
        helm = with_stats(item_row(6010, quality=3, ilvl=30, subclass=4, inv=1), (AGI, 10), (AP, 10))
        self.assertEqual(cat.shapes[decide(helm, quest_level=25, cat=cat).primary]["name"],
                         "Agi/AttackPower, Agi lead")
        d = decide(helm, quest_level=25, classes={"Warrior"}, cat=cat)
        self.assertEqual((cat.shapes[d.primary]["name"], d.share), ("Str/AttackPower, Str lead", 6000))
        self.assertIn(CRIT, cat.stats(d.secondary))
        # Another class, or a quest for several classes: unchanged.
        for classes in ({"Rogue"}, {"Warrior", "Paladin"}):
            self.assertEqual(decide(dagger, classes=classes, cat=cat).primary, plain.primary, classes)

    def test_ruling_32_warrior_intellect_becomes_strength_and_proc(self):
        cat = catalog(round6=True)
        mace = item_row(6005, quality=1, ilvl=10, cls=2, subclass=4, inv=13)  # odd one-handed mace: Int; % 6 -> Proc
        d = decide(mace, classes={"Warrior"}, cat=cat)
        self.assertEqual((cat.shapes[d.primary]["name"], d.share, cat.shapes[d.secondary]["name"]),
                         ("Strength (Solo)", 8000, "Proc (Solo)"))
        mace = item_row(6007, quality=1, ilvl=10, cls=2, subclass=4, inv=13)  # % 6 -> Haste
        d = decide(mace, classes={"Warrior"}, cat=cat)
        self.assertEqual(cat.shapes[d.secondary]["name"], "Haste/Proc")
        # Strength gear is untouched.
        axe = item_row(6002, quality=1, ilvl=10, cls=2, subclass=0, inv=13)
        warrior, plain = decide(axe, classes={"Warrior"}, cat=cat), decide(axe, cat=cat)
        self.assertEqual((warrior.primary, warrior.secondary, warrior.share), (plain.primary, plain.secondary, 8000))
        self.assertEqual(cat.shapes[warrior.primary]["name"], "Strength (Solo)")

    def test_ruling_28_same_name_and_quest_share_the_lowest_entry(self):
        cat = catalog()
        rows = {
            7000: with_stats(item_row(7000, quality=3, ilvl=60, inv=11, subclass=0, name="Signet"), (STA, 5)),
            7001: with_stats(item_row(7001, quality=3, ilvl=65, inv=11, subclass=0, name="Signet"), (STA, 5)),
            7002: with_stats(item_row(7002, quality=3, ilvl=70, inv=11, subclass=0, name="Signet"), (STA, 5)),
            7003: with_stats(item_row(7003, quality=3, ilvl=60, inv=11, subclass=0, name="Signet"), (STA, 5)),
            7010: with_stats(item_row(7010, quality=2, ilvl=20, subclass=4, inv=8, name="Kickers"), (STR, 5)),
            7011: with_stats(item_row(7011, quality=2, ilvl=20, subclass=2, inv=8, name="Kickers"), (AGI, 5)),
            7012: with_stats(item_row(7012, quality=2, ilvl=20, subclass=4, inv=8, name="Kickers"), (STR, 5)),
        }
        path = [qr.Quest(1, 60, "The Path", "zone")]
        other = [qr.Quest(2, 60, "Another Path", "zone")]
        kick = [qr.Quest(3, 17, "Escape", "zone")]
        s = qr.Scope(items={7000: path, 7001: path, 7002: path, 7003: other, 7010: kick, 7011: kick, 7012: kick})
        alone = {e: decide(rows[e]) for e in rows}
        self.assertNotEqual(alone[7000].secondary, alone[7001].secondary)  # entry MOD pool: different picks
        d = {x.entry: x for x in qr.decide_all(s, rows, rows, SPELLS, cat)}
        for e in (7001, 7002):
            self.assertEqual((d[e].primary, d[e].secondary, d[e].share),
                             (d[7000].primary, d[7000].secondary, d[7000].share), e)
            self.assertTrue(any("ruling 28" in p for p in d[e].paths))
        self.assertEqual([d[e].ilvl for e in (7000, 7001, 7002)], [60, 65, 70])  # item level stays its own
        self.assertEqual(d[7003].secondary, alone[7003].secondary)  # another quest: not grouped
        # Role variants (a choice of Str / Agi boots) keep their own primary and take only the secondary.
        self.assertEqual(cat.shapes[d[7011].primary]["name"], "Agility (Solo)")
        self.assertEqual(d[7011].secondary, d[7010].secondary)
        self.assertEqual((d[7012].primary, d[7012].secondary), (d[7010].primary, d[7010].secondary))
        groups = qr.same_name_groups(list(d.values()))
        self.assertEqual(sorted([x.entry for x in g] for g in groups), [[7000, 7001, 7002], [7010, 7011, 7012]])

    def test_argent_dawn_gloves_at_min_level(self):
        rows = {23078: item_row(23078, quality=3, ilvl=63, subclass=4, inv=10)}
        quests = {9094: quest(9094, -1, title="Argent Dawn Gloves", sort=0, min_level=50, RewardChoiceItemID1=23078),
                  9333: quest(9333, -1, title="Argent Dawn Gloves", sort=0, min_level=50, RewardChoiceItemID1=23078)}
        s = qr.scope(quests, {9094: {"SpecialFlags": 1}}, rows)  # 9094 is the repeatable copy
        self.assertEqual([(q.id, q.level, q.scaled, q.kind) for q in s.items[23078]],
                         [(9094, 50, True, "zone"), (9333, 50, True, "zone")])

    def test_ruling_33_spell_power_and_attack_power_solo(self):
        cat = catalog(round6=True)

        def primary(*stats, spell=0, cat=cat):
            row = with_stats(item_row(8000, quality=3, ilvl=60, spellid_1=spell, spelltrigger_1=1 if spell else 0),
                             *stats)
            return cat.shapes[decide(row, quest_level=55, cat=cat).primary]["name"]

        self.assertEqual(primary(spell=9416), "Spell Power (Solo)")  # stock Spell Power only
        self.assertEqual(primary(spell=9416, cat=catalog()), "Int/SpellPower, SpellPower lead")  # no shape 81
        self.assertEqual(primary((INT, 1), spell=9416), "Spell Power (Solo)")  # a caster, Spell Power 90%
        self.assertEqual(primary((INT, 4), spell=9416), "Int/SpellPower, SpellPower lead")  # Spell Power 70%
        self.assertNotEqual(primary((STR, 1), spell=9416), "Spell Power (Solo)")  # Strength: not a caster item
        self.assertEqual(primary(spell=9331), "Attack Power (Solo)")  # stock Attack Power only
        self.assertEqual(primary((STR, 1), spell=9331), "Str/AttackPower, Str lead")  # not Attack Power only
        self.assertTrue(qr.solo_power_ok("Spell Power (Solo)", {INT, SP}))
        self.assertFalse(qr.solo_power_ok("Spell Power (Solo)", {INT}))
        self.assertFalse(qr.solo_power_ok("Attack Power (Solo)", {AGI, AP}))

    def test_parry_versatility_any_stays_out_of_the_rules(self):
        cat = catalog(round6=True)
        for entry in range(8100, 8110):  # a Parry tank item never draws Parry/Versatility (Any)
            d = decide(with_stats(item_row(entry, quality=3, ilvl=60, subclass=4), (STR, 10), (PARRY, 5)),
                       quest_level=55, cat=cat)
            self.assertEqual(cat.stats(d.secondary)[0], PARRY)
            self.assertNotIn(cat.shapes[d.secondary]["name"], qr.HAND_ONLY_SECONDARIES)

    def test_ruling_35_step_down_zero(self):
        """`step_down_zero` with a stand-in materializer: {(entry, share): stats}."""
        cat = catalog(round6=True)
        text = (qr.LOCK_HEADER
                + "1 10 2 15 22 25 8000 -  # Fixed\n"  # Crit 0 at 8000, 1 at 6000 (Str to 0: no guard any more)
                + "2 10 2 15 22 29 8000 -  # Partial\n"  # Crit/Haste: Haste comes up at 6000, Crit still 0
                + "3 10 2 15 22 25 8000 -  # Unchanged\n"  # still 0 at 6000, nothing comes up: 8000 kept
                + "4 10 3 15 22 25 6000 -  # Blue\n"  # 0 at 6000 (not a share-8000 line): not touched
                + "5 10 2 15 22 26 8000 -  # Fine\n")
        stats = {(1, 8000): {STR: 1}, (1, 6000): {CRIT: 1}, (2, 8000): {STR: 2}, (2, 6000): {STR: 1, HASTE: 1},
                 (3, 8000): {STR: 1}, (3, 6000): {STR: 1}, (4, 6000): {STR: 1}, (5, 8000): {STR: 3, HASTE: 1}}

        def fake(lock, rows, tables, shape_catalog):
            out = {}
            for e, line in lock.items():
                row = {}
                for n, (stat, value) in enumerate(stats[(e, line.share)].items(), 1):
                    row[f"stat_type{n}"], row[f"stat_value{n}"] = stat, value
                out[e] = row
            return qr.Materialized(out, {}, [], {})

        real, qr.materialize = qr.materialize, fake
        try:
            r = qr.step_down_zero(text, {}, {}, {}, cat)
        finally:
            qr.materialize = real
        self.assertEqual((r.fixed, r.partial, r.unchanged, r.other_share),
                         ({1: [CRIT]}, {2: [CRIT]}, {3: [CRIT]}, {4: [CRIT]}))
        lines = qr.parse_lock(r.text)
        self.assertEqual([lines[e].share for e in range(1, 6)], [6000, 6000, 8000, 6000, 8000])
        self.assertIn("round 7 step-down (ruling 35): share 8000->6000 so Crit is at least 1", lines[1].comment)
        self.assertIn("so Haste is at least 1 (Crit still 0)", lines[2].comment)
        self.assertEqual(lines[3].comment, "Unchanged")

    def test_lock_edit_helpers(self):
        text = (qr.LOCK_HEADER + "10 5 2 7 23 25 8000 -  # Short\n"
                "11 5 2 7 23 26 8000 -  # " + "word " * 30 + "\n" + "#   tail of 11\n"
                "12 5 2 7 23 27 8000 -  # Last\n")
        comments = qr.lock_comments(text)
        self.assertTrue(comments[11].endswith("tail of 11"))
        hyphen = qr.lock_comments("13 5 2 7 23 27 8000 -  # Mace -- type Int (one-\n#   handed mace)\n")
        self.assertEqual(hyphen[13], "Mace -- type Int (one-handed mace)")  # an old hyphen break rejoins
        self.assertEqual(comments[12], "Last")
        edited = qr.replace_lines(text, {11: qr.LockLine(11, 5, 2, 7, 24, 25, 6000, "-", "Edited -- designer: x")})
        lines = qr.parse_lock(edited)
        self.assertEqual((lines[11].primary, lines[11].share, lines[11].comment), (24, 6000, "Edited -- designer: x"))
        self.assertNotIn("tail of 11", edited)  # its continuation lines go with it
        self.assertEqual((lines[10].comment, lines[12].comment), ("Short", "Last"))
        with self.assertRaises(qr.LockError):
            qr.replace_lines(text, {99: lines[10]})
        line, shares = lines[10], []
        while (line := qr.step_down(line)) is not None:
            shares.append(line.share)
        self.assertEqual(shares, [6000, 4000, 0])


@unittest.skipUnless(os.environ.get("QUEST_REWARDS_REAL"), "set QUEST_REWARDS_REAL=1 (replays the world DB, ~2 min)")
class RealDataTest(unittest.TestCase):
    """Every real lock line expands, emits no error, and its stats equal compute_breakdown (the IV2 test, on the real
    tables and rows)."""

    def test_real_lock_expands_and_stats_equal_compute_breakdown(self):
        from lib import item_variants  # noqa: PLC0415

        item_variants._item_lib()
        from item_lib import budget, overlay  # noqa: PLC0415

        rows = overlay.resolve_current_rows(cache=True)
        tables, shape_catalog = item_variants.load_itemization_tables()
        lock = qr.parse_lock(qr.LOCK_PATH.read_text(encoding="utf-8"))
        # Ruling 21: green weapons resolve against the Quality 2 rows of item_weapon_dps_curve (pending SQL).
        self.assertTrue(any(key[1] == 2 for key in tables["item_weapon_dps_curve"]))
        self.assertTrue(any(rows[e]["class"] == 2 and line.quality == 2 for e, line in lock.items()))
        # Round 6: the green curve's low end follows the first fitted segment (option B), the three new shapes.
        curve = tables["item_weapon_dps_curve"]
        self.assertAlmostEqual(float(curve[(5, 2, 0)]["dps"]), 3.4284, places=3)
        self.assertAlmostEqual(float(curve[(5, 2, 1)]["dps"]), 4.3684, places=3)
        self.assertEqual({shape_catalog[s]["name"] for s in (81, 82, 83)},
                         {"Spell Power (Solo)", "Attack Power (Solo)", "Parry/Versatility (Any)"})
        mat = qr.materialize(lock, rows, tables, shape_catalog)
        self.assertEqual(mat.errors, [], "\n".join(mat.errors))
        self.assertEqual(mat.labels, {})  # ruling 20: no tooltip line
        self.assertEqual(sorted(mat.rows), sorted(lock))
        for entry, row in mat.rows.items():
            b = budget.compute_breakdown(row, mat.itemization[entry], tables, shape_catalog)
            want = [(a["stat_type"], a["rounded"]) for a in b["allocations"]] + [(STA, b["final_stamina"])]
            got = [(row[f"stat_type{n}"], row[f"stat_value{n}"]) for n in range(1, 11) if row[f"stat_type{n}"]]
            self.assertEqual(got, [w for w in want if w[1]], entry)
            self.assertEqual((row["ItemLevel"], row["Quality"], row["RequiredLevel"]),
                             (lock[entry].ilvl, lock[entry].quality, 0))
            if row["class"] == 2:  # every weapon resolves a curve DPS (none left at zero damage)
                self.assertGreater(b["final_dps"], 0, entry)

if __name__ == "__main__":
    unittest.main()
