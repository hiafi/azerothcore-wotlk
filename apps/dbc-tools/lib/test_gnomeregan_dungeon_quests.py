"""
Gnomeregan build, the quests WP (handoff 4.Q, section 7 #45-#50): the exile giver, the eleven reward items and the
hand SQL rev_quests_gnomeregan.sql.

Checks:
  - Tinkmaster Fizzbolt 301190: a civilian quest giver (npcflag 2, flags_extra 2), faction 35, level 28, subname
    "Gnomeregan Exiles", no AI, the four stock Evacuee displays, in the `gnomeregan` creature reservation, named in
    the heroic call's `normal_only_creatures`, and the id the instance summons (`NPC_EXILE` of GnomereganRework.h);
  - the SQL: the two static spawns are exactly the entrance and Workshop spots on map 90 with spawnMask 1 (the End
    spots are the instance's); he starts and ends 2922, 2924, 2928, 2930, 2841 and 2929 and not 2945 (the Sparklematic
    ends it); the Prismatic Punch Card (9316) gets 72,000 seconds of real time duration; the six quests are neutral
    with their reputation cleared; 2924 asks for 4; 2922 loses its prerequisite; the Sparklematic stops starting
    Return of the Ring; the stock rewards of 2928 and 2930 are untouched; every UPDATE is guarded; no reward is looked
    up by name (Ragefire Chasm R-Q-m1); the new text has no faction voice;
  - the items: eleven `gnq_` declarations on the one-tier `quest_reward` ladder with the handoff's qualities, item
    levels (quest level + 5), armor types and roles (ruling 24, every healer piece cloth), every shape stat rounds to a
    point on the tier, and each quest's choices are its own items in order: the ids of item_ids.lock once the write
    run minted them, before that the next eleven ids in declaration order;
  - the reward UPDATEs keep the literal ids and each also carries a fail-closed name guard (`AND EXISTS (SELECT 1 FROM
    `item_template` WHERE `entry` = N AND `name` = '...')`): the guard's id is the choice's id and its name is the
    declaration's, so a shifted id leaves the quest unchanged instead of paying another item;
  - the breadcrumbs 2923, 2925 and 2931 are cleared (DQ1 B), so an Alliance player holding one still sees 2922 /
    2924 / 2930;
  - quest_rewards.lock: the stock rewards this dungeon keeps (9604, 9605, 9608, 9609) are untouched.

THE DEPLOY GATE. CHECK runs this between the generate.py write run and db-import, from the repo root of the tree being
deployed, with the minted-ids check made mandatory (without the variable it is skipped while item_ids.lock has no
`gnq_` line, and a skip must not pass the gate):

    GNQ_REQUIRE_MINTED=1 apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_dungeon_quests.py

It must print OK with no skip. A failure in test_the_choices_are_the_minted_ids means the ids moved: put the ids of
item_ids.lock into rev_quests_gnomeregan.sql (the reward ids and the EXISTS guard ids) and run it again before
db-import.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_dungeon_quests.py
"""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.test_hard_mode_item_effects import _load_items_registry, materialized_tier_stats  # noqa: E402

EXILE = 301190
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_quests_gnomeregan.sql"
LOCK = TOOL_ROOT / "source" / "items" / "quest_rewards.lock"
ID_LOCK = TOOL_ROOT / "source" / "items" / "item_ids.lock"
NPC_DIR = TOOL_ROOT / "source" / "npcs" / "gnomeregan"
DUNGEON_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "gnomeregan.py"
HEADER = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Gnomeregan" / "GnomereganRework.h"

# the quests the exile starts and ends, and the one the Sparklematic ends
EXILE_QUESTS = (2922, 2924, 2928, 2930, 2841, 2929)
RING_QUEST = 2945
GREEN, BLUE = 2, 3

# key: (name, quality, item level, like, primary shape, secondary shape, share)
ITEMS = {
    "gnq_memory_keepers_wraps": ("Memory Keeper's Wraps", GREEN, 31, 7355, "Intellect (Solo)", "Haste (Solo)", 8000),
    "gnq_memory_keepers_bracers": ("Memory Keeper's Bracers", GREEN, 31, 7410, "Agility (Solo)", "Crit (Solo)", 8000),
    "gnq_memory_keepers_vambraces": ("Memory Keeper's Vambraces", GREEN, 31, 8156, "Strength (Solo)", "Dodge (Solo)",
                                     8000),
    "gnq_extrapolators_cloak": ("Extrapolator's Cloak", GREEN, 35, 7004, "Spirit (Solo)", "Haste (Solo)", 8000),
    "gnq_sparklematic_signet": ("Sparklematic Signet", BLUE, 39, 9538, None, "Haste/Versatility", 0),
    "gnq_rigrunners_longbow": ("Rigrunner's Longbow", BLUE, 40, 15286, "Agility (Solo)", "Crit/Haste", 6000),
    "gnq_blueprint_readers_mitts": ("Blueprint Reader's Mitts", BLUE, 40, 14411, "Intellect (Solo)", "Haste/Mastery",
                                    6000),
    "gnq_rigbreaker_gauntlets": ("Rigbreaker Gauntlets", BLUE, 40, 9287, "Strength (Solo)", "Parry/Mastery", 6000),
    "gnq_retakers_legplates": ("Retaker's Legplates", BLUE, 40, 8162, "Strength (Solo)", "Crit/Mastery", 6000),
    "gnq_retakers_leggings": ("Retaker's Leggings", BLUE, 40, 15139, "Agility (Solo)", "Dodge/Mastery", 6000),
    "gnq_retakers_pants": ("Retaker's Pants", BLUE, 40, 7368, "Intellect (Solo)", "Crit/Versatility", 6000),
}
# quest -> its new choice items in slot order (every slot starts at 1: the stock choices of 2841 and 2929 are replaced)
CHOICES = {
    2922: ("gnq_memory_keepers_wraps", "gnq_memory_keepers_bracers", "gnq_memory_keepers_vambraces"),
    2924: ("gnq_extrapolators_cloak",),
    2945: ("gnq_sparklematic_signet",),
    2841: ("gnq_rigrunners_longbow", "gnq_blueprint_readers_mitts", "gnq_rigbreaker_gauntlets"),
    2929: ("gnq_retakers_legplates", "gnq_retakers_leggings", "gnq_retakers_pants"),
}
# quest -> the item level its choices take (quest level + 5)
QUEST_ILEVEL = {2922: 31, 2924: 35, 2945: 39, 2841: 40, 2929: 40}
# stock reward entry -> (quality, item level) in quest_rewards.lock: the dungeon keeps these as they are
LOCK_KEPT = {9604: (GREEN, 35), 9605: (GREEN, 35), 9608: (GREEN, 35), 9609: (GREEN, 35)}

# the armor type and slot each `like` item has (class 4: subclass 1 cloth, 2 leather, 4 plate; weapons by kind)
LIKE_SLOT = {
    7355: ("cloth", "wrist"), 7410: ("leather", "wrist"), 8156: ("plate", "wrist"), 7004: ("cloth", "cloak"),
    9538: (None, "ring"), 15286: (None, "bow"), 14411: ("cloth", "gloves"), 9287: ("plate", "gloves"),
    8162: ("plate", "legs"), 15139: ("leather", "legs"), 7368: ("cloth", "legs"),
}
FACTION_VOICE = ("Horde", "Alliance", "Thrall", "Warchief", "Forsaken", "Stormwind", "Orgrimmar", "Ironforge",
                 "Nogg", "Mekkatorque", "Overspark", "Spannerspan", "Shoni", "Castpipe", "Dun Morogh", "goblin")

# the fail-closed name guard of a reward UPDATE
NAME_GUARD = re.compile(r"AND EXISTS \(SELECT 1 FROM `item_template` WHERE `entry` = (\d+) AND `name` = "
                        r"'((?:[^']|'')*)'\)")

# the spots (HANDOFF 4.Q, SP table; the End spots are the instance's, kEndNpc1Spot and kEndNpc2Spot)
ENTRANCE = (-338.12, -6.55, -152.85, 1.16)
WORKSHOP = (-753.00, -4.04, -252.22, 1.40)


def _sql() -> str:
    return SQL.read_text(encoding="utf-8")


def _where_at(stmt: str) -> int:
    """Index of the statement's own WHERE: the last one before any `EXISTS (SELECT` guard (its subquery has one)."""
    cut = stmt.find("EXISTS (SELECT")
    return (stmt if cut < 0 else stmt[:cut]).rindex("WHERE")


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("--"))


def _statements(text: str) -> list[str]:
    return [s.strip() for s in re.split(r";\s*\n", _code(text) + "\n") if s.strip()]


def _minted() -> dict[str, int]:
    minted: dict[str, int] = {}
    for line in ID_LOCK.read_text(encoding="utf-8").splitlines():
        m = re.match(r"(\d+) (gnq_\w+) normal\b", line)
        if m:
            assert m.group(2) not in minted, m.group(2)
            minted[m.group(2)] = int(m.group(1))
    return minted


class TestExile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t = id_blocks
        cls.reg = registry.load_class_package(
            NPC_DIR, ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(), shapeshift_index={},
            existing_creature_rows=t._AnyRows(), creature_columns=t.spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=t.spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=t.spell_tables.dsl_live_data(
                {}, t.spell_tables.load_live_item_template_rows,
                lambda: t.state.load_existing_rows(t.dbcfmt.SKILLLINEABILITY),
                lambda: t.state.load_stock_rows(t.dbcfmt.CHRCLASSES),
                lambda: t.state.load_stock_rows(t.dbcfmt.SKILLLINEABILITY),
            ),
        )
        cls.row = next(r for r in cls.reg.creature_templates if int(r["entry"]) == EXILE)

    def test_a_civilian_quest_giver_friendly_to_both_factions(self):
        row = self.row
        self.assertEqual(row["name"], "Tinkmaster Fizzbolt")
        self.assertEqual(row["subname"], "Gnomeregan Exiles")
        self.assertEqual(int(row["faction"]), 35)
        self.assertEqual(int(row["npcflag"]), 2)
        self.assertEqual(int(row["flags_extra"]), 2)
        self.assertEqual((int(row["minlevel"]), int(row["maxlevel"])), (28, 28))
        self.assertEqual(row["AIName"], "")
        self.assertEqual(row["ScriptName"], "")
        self.assertEqual(int(row["lootid"]), 0)
        self.assertEqual(int(row["gossip_menu_id"]), 0)
        self.assertEqual(int(row["MovementType"]), 0)
        self.assertEqual(int(row["difficulty_entry_1"] or 0), 0, "no heroic body: he is normal only")

    def test_the_look_is_the_stock_evacuees(self):
        models = [m for m in self.reg.creature_template_models if int(m["CreatureID"]) == EXILE]
        self.assertEqual([int(m["CreatureDisplayID"]) for m in models], [6973, 6974, 6975, 6976])
        self.assertEqual([int(m["Idx"]) for m in models], [0, 1, 2, 3])
        self.assertEqual({float(m["Probability"]) for m in models}, {1.0})

    def test_the_heroic_call_keeps_him_normal_only(self):
        self.assertRegex(DUNGEON_FILE.read_text(encoding="utf-8"), r"normal_only_creatures=\(301190,\)")

    def test_he_sits_in_the_dungeons_creature_reservation(self):
        self.assertEqual(id_blocks.out_of_reservation("gnomeregan", {"creature": [EXILE]}), [])

    def test_the_instance_summons_this_entry(self):
        self.assertRegex(HEADER.read_text(encoding="utf-8"), r"NPC_EXILE\s*=\s*301190")

    def test_the_quests_file_declares_only_him(self):
        declared = {int(r["entry"]) for r in self.reg.creature_templates}
        self.assertIn(EXILE, declared)
        file_text = (NPC_DIR / "dungeon_quests.py").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"creature_template\(\s*(\w+)", file_text), ["EXILE"])
        self.assertEqual(re.findall(r"^EXILE = (\d+)", file_text, re.M), [str(EXILE)])


class TestSql(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = _sql()
        cls.code = _code(cls.text)
        cls.stmts = _statements(cls.text)

    def _stmt(self, prefix: str, where: str) -> str:
        return next(s for s in self.stmts if s.startswith(prefix) and re.search(where, s[_where_at(s):]))

    def test_the_spawns_are_the_designers_spots(self):
        m = re.search(r"INSERT INTO `creature`.*?VALUES\s*(.*?);", self.text, re.S)
        self.assertIsNotNone(m)
        rows = re.findall(r"\(([^()]*)\)", m.group(1))
        self.assertEqual(len(rows), 2, "the entrance and the Workshop; the End spots are the instance's")
        spots = []
        for row in rows:
            fields = [f.strip() for f in row.split(",")]
            # guid, id, map, zoneId, areaId, spawnMask, phaseMask, equipment_id, x, y, z, o, respawn, MovementType
            self.assertEqual(fields[1:3], [str(EXILE), "90"])
            self.assertEqual(fields[5], "1", "spawnMask 1: normal only")
            self.assertEqual(fields[13], "0", "standing still")
            spots.append((int(fields[0]), tuple(float(v) for v in fields[8:12])))
        self.assertEqual(spots, [(3011900, ENTRANCE), (3011901, WORKSHOP)])

    def test_the_guids_are_free_of_the_builds_other_spawns(self):
        others = ""
        for path in (REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world").glob("rev_*.sql"):
            if path != SQL:
                others += path.read_text(encoding="utf-8", errors="replace")
        for guid in ("3011900", "3011901"):
            self.assertNotRegex(others, rf"\(\s*{guid}\s*,", f"guid {guid} is another file's")

    def test_starters_and_enders(self):
        def rows(table):
            m = re.search(rf"INSERT INTO `{table}` \(`id`, `quest`\) VALUES\s*(.*?);", self.text, re.S)
            self.assertIsNotNone(m, table)
            return {(int(a), int(b)) for a, b in re.findall(r"\((\d+),\s*(\d+)\)", m.group(1))}
        self.assertEqual(rows("creature_queststarter"), {(EXILE, q) for q in EXILE_QUESTS})
        self.assertEqual(rows("creature_questender"), {(EXILE, q) for q in EXILE_QUESTS})
        self.assertNotIn(f"({EXILE}, {RING_QUEST})", self.code, "the Sparklematic ends the ring quest")

    def test_the_punch_card_expires_after_twenty_real_time_hours(self):
        stmt = self._stmt("UPDATE `item_template`", r"`entry` = 9316")
        self.assertIn("`duration` = 72000", stmt)  # 20 h in seconds
        self.assertIn("`flagsCustom` = `flagsCustom` | 1", stmt)  # ITEM_FLAGS_CU_DURATION_REAL_TIME
        self.assertIn("`duration` = 0", stmt[_where_at(stmt):], "guarded on the stock duration")

    def test_the_six_quests_become_neutral_with_no_reputation(self):
        races = " ".join(s for s in self.stmts if "`AllowableRaces` = 0" in s)
        for quest in (2922, 2924, 2928, 2929, 2930, 2841):
            self.assertRegex(races, rf"\b{quest}\b")
        self.assertNotRegex(races, rf"\b{RING_QUEST}\b", "2945 is neutral already")
        cleared = [s for s in self.stmts if "`RewardFactionID1` = 0" in s]
        quests = set()
        for s in cleared:
            where = s[_where_at(s):]
            quests |= {int(q) for q in re.findall(r"\b(2\d{3})\b", where.split("AND")[0])}
            for slot in range(1, 6):
                for col in ("RewardFactionID", "RewardFactionValue", "RewardFactionOverride"):
                    self.assertIn(f"`{col}{slot}` = 0", s)
        self.assertEqual(quests, {2922, 2924, 2928, 2929, 2930, 2841})

    def test_the_finder_band_minimum_level(self):
        stmt = self._stmt("UPDATE `quest_template` SET `MinLevel`", r"`MinLevel` > 23")
        self.assertIn("`MinLevel` = 23", stmt)
        for quest in (2841, 2924, 2929, 2930, 2945):
            self.assertRegex(stmt[_where_at(stmt):], rf"\b{quest}\b")
        ring = self._stmt("UPDATE `item_template`", r"`entry` = 9326")
        self.assertIn("`RequiredLevel` = 23", ring)

    def test_the_artificials_count_and_the_prerequisite(self):
        stmt = self._stmt("UPDATE `quest_template` SET `RequiredItemCount1`", r"`ID` = 2924")
        self.assertIn("`RequiredItemCount1` = 4", stmt)
        self.assertIn("`RequiredItemId1` = 9278 AND `RequiredItemCount1` = 12", stmt)
        prereq = self._stmt("UPDATE `quest_template_addon`", r"`ID` = 2922")
        self.assertIn("`PrevQuestID` = 0", prereq)
        self.assertIn("`PrevQuestID` = 2923", prereq)

    def test_the_breadcrumbs_become_plain_lead_ins(self):
        """DQ1 B: 2923, 2925 and 2931 stop being the breadcrumbs of 2922, 2924 and 2930, or a held one hides the
        exile's quest (2925 Klockmort's Essentials -> 2924 was missed at first, RF-2 Minor-1)."""
        stmts = [s for s in self.stmts if "`BreadcrumbForQuestId`" in s]
        self.assertEqual(len(stmts), 3)
        found = {}
        for s in stmts:
            self.assertTrue(s.startswith("UPDATE `quest_template_addon` SET `BreadcrumbForQuestId` = 0"), s)
            m = re.search(r"WHERE `ID` = (\d+) AND `BreadcrumbForQuestId` = (\d+)$", s)
            self.assertIsNotNone(m, s)
            found[int(m.group(1))] = int(m.group(2))
        self.assertEqual(found, {2923: 2922, 2925: 2924, 2931: 2930},
                         "guarded on the stock value, so it runs twice safely")
        self.assertNotRegex(self.code, r"RewardNextQuest", "the stock flow still offers 2922 and 2930 next")

    def test_the_ring_text_names_the_three_silver_coins(self):
        stmt = self._stmt("UPDATE `quest_offer_reward`", r"`ID` = 2945")
        new = stmt[:_where_at(stmt)]
        self.assertIn("deposit three silver coins into the slot", new)  # RewardMoney -300
        self.assertNotIn("a silver coin", new)

    def test_the_sparklematic_stops_starting_return_of_the_ring(self):
        stmt = self._stmt("DELETE FROM `gameobject_queststarter`", r"`quest` IN")
        self.assertRegex(stmt, r"`id` = 142487 AND `quest` IN \(2947, 2949\)")
        self.assertNotRegex(self.code, r"gameobject_questender")

    def test_xp_money_chain_and_stock_rewards_are_not_touched(self):
        self.assertNotRegex(self.code, r"RewardMoney|RewardXPDifficulty|RewardNextQuest|ExclusiveGroup|RewardItem\d")
        self.assertNotRegex(self.code, r"`RewardChoiceItemID\d` = (9608|9609|9604|9605)")
        self.assertNotIn("INSERT INTO `quest_template`", self.text)
        self.assertEqual(re.findall(r"\b901[0-9]{2}\b", self.code), [], "no id of the 90100-90199 quest block")

    def test_every_update_is_guarded(self):
        for s in self.stmts:
            if s.startswith("UPDATE"):
                where = s[_where_at(s):]
                self.assertRegex(where, r"`\w+` (?:=|IN) ", s[:80])
                self.assertIn(" AND `", where, "needs a stock-value guard: " + s[:80])

    def test_the_new_text_has_no_faction_voice(self):
        for s in self.stmts:
            if not s.startswith(("UPDATE `quest_template` SET `LogDescription`", "UPDATE `quest_offer_reward`")):
                continue
            new = s[:_where_at(s)]
            for word in FACTION_VOICE:
                self.assertNotIn(word, new, f"{word!r} in the new text of {s[:70]!r}")

    def test_log_lines_name_the_exile(self):
        seen = set()
        for s in self.stmts:
            if not s.startswith("UPDATE `quest_template` SET `LogDescription`"):
                continue
            quest = int(re.search(r"WHERE `ID` = (\d+)\b", s).group(1))
            new = s[:_where_at(s)]
            log = re.search(r"`LogDescription` = '((?:[^']|'')*)'", new).group(1)
            completion = re.search(r"`QuestCompletionLog` = '((?:[^']|'')*)'", new).group(1)
            self.assertIn("Tinkmaster Fizzbolt", log, quest)
            self.assertIn("Tinkmaster Fizzbolt", completion, quest)
            seen.add(quest)
        self.assertEqual(seen, set(EXILE_QUESTS))

    def test_the_artificials_text_matches_the_count(self):
        stmt = self._stmt("UPDATE `quest_template` SET `LogDescription`", r"`ID` = 2924")
        self.assertIn("Bring 4 Essential Artificials", stmt)

    def _choices(self) -> dict[int, dict[int, int]]:
        """quest -> {slot: item id}; a name lookup is a failure (Ragefire Chasm R-Q-m1)."""
        found = {}
        for s in self.stmts:
            if not s.startswith("UPDATE `quest_template`") or "`RewardChoiceItemID" not in s[:_where_at(s)]:
                continue
            quest = int(re.search(r"WHERE `ID` = (\d+)\b", s).group(1))
            self.assertNotIn(quest, found)
            new = s[:_where_at(s)]
            self.assertNotIn("SELECT", new, "reward ids are literal, never looked up by name (R-Q-m1)")
            found[quest] = {int(slot): int(item) for slot, item in re.findall(r"`RewardChoiceItemID(\d)` = (\d+)", new)}
            quantities = re.findall(r"`RewardChoiceItemQuantity(\d)` = (\d+)", new)
            self.assertEqual({int(a) for a, _ in quantities}, set(found[quest]), quest)
            self.assertEqual({int(b) for _, b in quantities}, {1}, quest)
        return found

    def test_no_reward_is_looked_up_by_name(self):
        """The only SELECT is the fail-closed EXISTS guard: a check of the literal id, never a lookup of it."""
        rest = NAME_GUARD.sub("", self.code)
        self.assertNotIn("SELECT", rest)
        self.assertNotIn("LIMIT 1", rest)
        self.assertNotRegex(rest, r"`name` = ")
        self.assertEqual(len(NAME_GUARD.findall(self.code)), len(ITEMS))

    def test_every_reward_update_carries_its_name_guard(self):
        """Each id the SQL sets is guarded on the declaration's name (Q1: a shifted id changes nothing)."""
        choices = self._choices()
        for quest, keys in CHOICES.items():
            stmt = next(s for s in self.stmts if s.startswith("UPDATE `quest_template` SET")
                        and re.search(rf"WHERE `ID` = {quest}\b", s) and "RewardChoiceItemID" in s[:_where_at(s)])
            guards = NAME_GUARD.findall(stmt[_where_at(stmt):])
            want = [(str(choices[quest][1 + i]), ITEMS[key][0].replace("'", "''")) for i, key in enumerate(keys)]
            self.assertEqual(guards, want, f"{quest}: one guard per slot, in slot order")
            self.assertNotIn("OR ", stmt[_where_at(stmt):], f"{quest}: the guards are ANDed")
            self.assertEqual(stmt.count("SELECT"), len(keys), quest)

    def test_each_quest_gives_its_own_slots(self):
        choices = self._choices()
        self.assertEqual(set(choices), set(CHOICES))
        for quest, keys in CHOICES.items():
            self.assertEqual(sorted(choices[quest]), list(range(1, len(keys) + 1)), quest)
        # 2841 and 2929 replace the three shared blues (9623, 9624, 9625): the UPDATE is guarded on them
        for quest in (2841, 2929):
            stmt = next(s for s in self.stmts
                        if re.search(rf"WHERE `ID` = {quest}\b", s) and "RewardChoiceItemID3" in s)
            self.assertRegex(stmt[_where_at(stmt):],
                             r"`RewardChoiceItemID1` = 9623\s+AND\s+`RewardChoiceItemID2` = 9624\s+AND\s+"
                             r"`RewardChoiceItemID3` = 9625")

    def test_the_choice_ids_follow_the_declaration_order(self):
        choices = self._choices()
        ids = [choices[quest][slot] for quest, keys in CHOICES.items() for slot in range(1, len(keys) + 1)]
        self.assertEqual(len(ids), len(ITEMS))
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(ids, list(range(ids[0], ids[0] + len(ids))), "the write run mints in declaration order")
        keys = [key for ks in CHOICES.values() for key in ks]
        self.assertEqual(keys, list(ITEMS))

    def test_the_choices_are_the_minted_ids(self):
        minted = _minted()
        if not minted and os.environ.get("GNQ_REQUIRE_MINTED"):
            self.fail("GNQ_REQUIRE_MINTED is set and item_ids.lock has no gnq_ line: run the write run first")
        if not minted:
            self.skipTest("item_ids.lock has no gnq_ line yet: the write run has not minted the quest rewards")
        self.assertEqual(sorted(minted), sorted(ITEMS))
        choices = self._choices()
        for quest, keys in CHOICES.items():
            self.assertEqual([choices[quest][1 + i] for i in range(len(keys))], [minted[k] for k in keys],
                             f"{quest}: deploy step: set the ids of item_ids.lock into the SQL")


class TestItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"].startswith("gnq_")}

    def test_the_eleven_items(self):
        self.assertEqual(list(self.decls), list(ITEMS), "declaration order is the mint order")
        for key, (name, quality, ilvl, like, primary, secondary, share) in ITEMS.items():
            d = self.decls[key]
            self.assertEqual((d.name, d.quality, d.ilvl, d.like, d.primary, d.secondary, d.primary_share),
                             (name, quality, ilvl, like, primary, secondary, share), key)
            self.assertEqual(d.required_level, 0, key)
            self.assertEqual(d.ladder.name, "quest_reward", key)

    def test_levels_follow_the_quest_levels(self):
        for quest, keys in CHOICES.items():
            for key in keys:
                self.assertEqual(self.decls[key].ilvl, QUEST_ILEVEL[quest], f"{quest} {key}: quest level + 5")
        self.assertTrue(all(d.ilvl <= 55 for d in self.decls.values() if d.quality == GREEN))
        self.assertTrue(all(d.ilvl <= 60 for d in self.decls.values()))

    def test_qualities_follow_the_quests(self):
        quality = {2922: GREEN, 2924: GREEN, 2945: BLUE, 2841: BLUE, 2929: BLUE}
        for quest, keys in CHOICES.items():
            for key in keys:
                self.assertEqual(self.decls[key].quality, quality[quest], f"{quest} {key}")

    def test_the_roles_the_handoff_names(self):
        def primaries(quest):
            return [(self.decls[k].primary or "none").split()[0] for k in CHOICES[quest]]
        self.assertEqual(primaries(2922), ["Intellect", "Agility", "Strength"])
        self.assertEqual(primaries(2924), ["Spirit"], "the healer cloak")
        self.assertEqual(primaries(2945), ["none"], "a ring takes no primary (ruling 18)")
        self.assertEqual(primaries(2841), ["Agility", "Intellect", "Strength"])
        self.assertEqual(primaries(2929), ["Strength", "Agility", "Intellect"])
        self.assertEqual(self.decls["gnq_memory_keepers_vambraces"].secondary, "Dodge (Solo)")  # 2922's tank pick
        self.assertEqual(self.decls["gnq_rigbreaker_gauntlets"].secondary, "Parry/Mastery")  # ruling 12: plate Parry
        self.assertEqual(LIKE_SLOT[self.decls["gnq_rigrunners_longbow"].like][1], "bow", "the wave's missing bow")

    def test_slots_and_armor_types(self):
        slots = {2922: "wrist", 2924: "cloak", 2945: "ring", 2929: "legs"}
        for quest, slot in slots.items():
            for key in CHOICES[quest]:
                self.assertEqual(LIKE_SLOT[self.decls[key].like][1], slot, key)
        self.assertEqual([LIKE_SLOT[self.decls[k].like][1] for k in CHOICES[2841]], ["bow", "gloves", "gloves"])
        by_primary = {"Strength": "plate", "Agility": "leather", "Intellect": "cloth", "Spirit": "cloth"}
        for key, d in self.decls.items():
            if d.primary and LIKE_SLOT[d.like][1] != "bow":
                self.assertEqual(LIKE_SLOT[d.like][0], by_primary[d.primary.split()[0]], f"{key}: the armor type")
        for key in ("gnq_extrapolators_cloak", "gnq_blueprint_readers_mitts", "gnq_retakers_pants",
                    "gnq_memory_keepers_wraps"):
            self.assertEqual(LIKE_SLOT[self.decls[key].like][0], "cloth", f"{key}: no leather healer piece")

    def test_rig_wars_and_the_grand_betrayal_use_different_slots(self):
        rig = {LIKE_SLOT[self.decls[k].like][1] for k in CHOICES[2841]}
        betrayal = {LIKE_SLOT[self.decls[k].like][1] for k in CHOICES[2929]}
        self.assertEqual(rig & betrayal, set())

    def test_ruling_24_no_tank_stat_on_a_ring_or_an_intellect_item(self):
        for key, d in self.decls.items():
            tank = any(word in d.secondary for word in ("Dodge", "Parry", "Block"))
            if tank:
                self.assertIn(d.primary.split()[0], ("Strength", "Agility"), f"{key}: ruling 24")
            if LIKE_SLOT[d.like][1] == "ring":
                self.assertFalse(tank, key)
                self.assertIsNone(d.primary, key)
                self.assertIn("Versatility", d.secondary, "a ring takes Versatility plus one other")

    def test_roles_are_distinct_within_each_quest(self):
        for quest, keys in CHOICES.items():
            pairs = [(self.decls[k].primary, self.decls[k].secondary) for k in keys]
            self.assertEqual(len(set(pairs)), len(pairs), quest)

    def test_blues_take_a_pair_and_greens_a_single(self):
        for key, d in self.decls.items():
            if d.quality == GREEN:
                self.assertIn("(Solo)", d.secondary, key)
                self.assertEqual(d.primary_share, 8000, key)
            else:
                self.assertNotIn("(Solo)", d.secondary, key)
                self.assertEqual(d.primary_share, 6000 if d.primary else 0, key)

    def test_every_shape_stat_rounds_to_a_point(self):
        stats = materialized_tier_stats(self.decls)
        self.assertEqual(sorted(stats), sorted(ITEMS))
        for key, tiers in stats.items():
            d = self.decls[key]
            for tier, got in tiers.items():
                for stat, value in got.items():
                    self.assertGreaterEqual(value, 1, f"{key} {tier}: stat {stat} rounds to 0 ({got})")
                want = (1 if d.primary else 0) + (1 if d.quality == GREEN else 2)
                self.assertEqual(len(got), want, f"{key} {tier}: {got}")

    def test_the_bow_states_no_ammo(self):
        """Like every other new ranged item, the bow sets ammo_type 0 itself instead of inheriting it from the look."""
        self.assertEqual(dict(self.decls["gnq_rigrunners_longbow"].columns)["ammo_type"], 0)

    def test_names_are_unique_across_the_declarations(self):
        names = [e["_decl"].name for e in self.reg.item_declarations if e["_decl"].name]
        for key, (name, *_rest) in ITEMS.items():
            self.assertEqual(names.count(name), 1, f"{key}: the name {name!r} is declared once")


class TestLock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = {}
        for line in LOCK.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                fields = line.split("#")[0].split()
                cls.lines[int(fields[0])] = fields

    def test_the_kept_stock_rewards_are_untouched(self):
        for entry, (quality, ilvl) in LOCK_KEPT.items():
            fields = self.lines[entry]
            self.assertEqual((int(fields[2]), int(fields[3])), (quality, ilvl), entry)

    def test_the_new_items_are_not_lock_lines(self):
        """quest_rewards.lock is for stock items (`item(base=)`); the new ones are declarations."""
        self.assertEqual(set(self.lines) & set(_minted().values()), set())


if __name__ == "__main__":
    unittest.main()
