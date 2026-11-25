"""
Ragefire Chasm build, the quests WP (handoff 4.Q, section 7 #38-#40): the entrance giver, the seven reward items and
the hand SQL rev_dungeon_quests_ragefire_chasm.sql.

Checks:
  - Grunt Dranok 300989: a civilian quest giver (npcflag 2, flags_extra 2), faction 35, level 18, no AI, display 4259,
    in the `ragefire_chasm` creature reservation, named in the heroic call's `normal_only_creatures`;
  - the SQL: his spawn is exactly (8.24, -22.39, -19.71, o 2.89) on map 389 with spawnMask 1; he starts 5725, 5761,
    5722, 5723 and ends 5725, 5761, 5724, 5723 (not 5722, which Maur Grimtotem's corpse ends); the five quests go
    neutral and lose their reputation rewards; 5728 gets XP difficulty 9 and no other quest field; no quest id is
    inserted (nothing in 90100-90199); 14356 is not touched; every UPDATE is guarded; the new text carries no faction
    voice (the Dark Lady, Thrall, the Horde, Forsaken, Magatha);
  - the items: seven `rfcq_` declarations on the one-tier quest ladder with the handoff's qualities, item levels, armor
    types and roles (three waist epics at 26, two blues at 21, two greens at 20, ruling 24 and no leather healer), every
    shape stat rounds to a point on the tier, and each quest's choices are its own items in order (the names the SQL
    looks up, or the ids of item_ids.lock once the deploy minted them and put them in place of the lookups);
  - quest_rewards.lock: 15449-15451 go green -> blue at item level 21 with a pair shape and share 6000; 15452 and 15453
    stay green; no other Ragefire quest reward line changed.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_dungeon_quests.py
"""

from __future__ import annotations

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

ORC = 300989
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_dungeon_quests_ragefire_chasm.sql"
LOCK = TOOL_ROOT / "source" / "items" / "quest_rewards.lock"
ID_LOCK = TOOL_ROOT / "source" / "items" / "item_ids.lock"
NPC_DIR = TOOL_ROOT / "source" / "npcs" / "ragefire_chasm"
DUNGEON_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "ragefire_chasm.py"

DUNGEON_QUESTS = (5725, 5761, 5722, 5724, 5723)
STARTS = {5725, 5761, 5722, 5723}
ENDS = {5725, 5761, 5724, 5723}
GREEN, BLUE, EPIC = 2, 3, 4

# key: (name, quality, item level, primary shape, secondary shape, share)
ITEMS = {
    "rfcq_embersworn_girdle": ("Embersworn Girdle", EPIC, 26, "Strength (Solo)", "Crit/Mastery", 6000),
    "rfcq_cinderstalkers_belt": ("Cinderstalker's Belt", EPIC, 26, "Agility (Solo)", "Crit/Proc", 6000),
    "rfcq_ashcallers_sash": ("Ashcaller's Sash", EPIC, 26, "Intellect (Solo)", "Crit/Haste", 6000),
    "rfcq_beastslayers_treads": ("Beastslayer's Treads", BLUE, 21, "Agility (Solo)", "Haste/Proc", 6000),
    "rfcq_beastslayers_bulwark": ("Beastslayer's Bulwark", BLUE, 21, "Strength (Solo)", "Parry/Block", 6000),
    "rfcq_troggbane_gauntlets": ("Troggbane Gauntlets", GREEN, 20, "Strength (Solo)", "Crit (Solo)", 8000),
    "rfcq_chasm_tenders_gloves": ("Chasm Tender's Gloves", GREEN, 20, "Spirit (Solo)", "Mastery (Solo)", 8000),
}
# quest -> its choice items in order
CHOICES = {
    5728: ("rfcq_embersworn_girdle", "rfcq_cinderstalkers_belt", "rfcq_ashcallers_sash"),
    5761: ("rfcq_beastslayers_treads", "rfcq_beastslayers_bulwark"),
    5723: ("rfcq_troggbane_gauntlets", "rfcq_chasm_tenders_gloves"),
}
# stock entry -> (quality, secondary shape id): the Power to Destroy... choices, green -> blue; the Satchel pair's stay
LOCK_BLUE = {15449: 40, 15450: 30, 15451: 35}
LOCK_GREEN = (15452, 15453)
# secondary shapes that are pairs (item_shape.shape_id: 29 Crit/Haste ... the generic and tank pairs)
PAIR_SHAPES = {29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 65, 66, 67}

BANNED_VOICE = ("Dark Lady", "Thrall", "Horde", "Forsaken", "Magatha", "Lich King")


def _sql() -> str:
    return SQL.read_text(encoding="utf-8")


def _statements(text: str) -> list[str]:
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("--"))
    return [s.strip() for s in re.split(r";\s*\n", body + "\n") if s.strip()]


class TestEntranceOrc(unittest.TestCase):
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
        cls.row = next(r for r in cls.reg.creature_templates if int(r["entry"]) == ORC)

    def test_a_civilian_quest_giver_friendly_to_both_factions(self):
        row = self.row
        self.assertEqual(row["name"], "Grunt Dranok")
        self.assertEqual(int(row["faction"]), 35)
        self.assertEqual(int(row["npcflag"]), 2)
        self.assertEqual(int(row["flags_extra"]), 2)
        self.assertEqual((int(row["minlevel"]), int(row["maxlevel"])), (18, 18))
        self.assertEqual(row["AIName"], "")
        self.assertEqual(row["ScriptName"], "")
        self.assertEqual(int(row["lootid"]), 0)
        self.assertEqual(int(row["gossip_menu_id"]), 0)
        self.assertFalse(row.get("subname"))

    def test_the_look_is_the_orgrimmar_grunts(self):
        models = [m for m in self.reg.creature_template_models if int(m["CreatureID"]) == ORC]
        self.assertEqual([int(m["CreatureDisplayID"]) for m in models], [4259])

    def test_the_heroic_call_keeps_him_normal_only(self):
        self.assertRegex(DUNGEON_FILE.read_text(encoding="utf-8"), r"normal_only_creatures=\(300989,\)")

    def test_he_sits_in_the_dungeons_creature_reservation(self):
        self.assertEqual(id_blocks.out_of_reservation("ragefire_chasm", {"creature": [ORC]}), [])


class TestSql(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = _sql()
        cls.stmts = _statements(cls.text)

    def test_the_spawn_is_the_designers_spot(self):
        m = re.search(r"INSERT INTO `creature`.*?VALUES\s*\((.*?)\);", self.text, re.S)
        self.assertIsNotNone(m)
        fields = [f.strip() for f in m.group(1).split(",")]
        # guid, id, map, zoneId, areaId, spawnMask, phaseMask, equipment_id, x, y, z, o, respawn, MovementType
        self.assertEqual(fields[0:3], ["3009890", "300989", "389"])
        self.assertEqual(fields[5], "1", "spawnMask 1: normal only")
        self.assertEqual([float(v) for v in fields[8:12]], [8.24, -22.39, -19.71, 2.89])
        self.assertEqual(fields[13], "0", "standing still")

    def test_starters_and_enders(self):
        def rows(table):
            m = re.search(rf"INSERT INTO `{table}` \(`id`, `quest`\) VALUES\s*(.*?);", self.text, re.S)
            self.assertIsNotNone(m, table)
            return {(int(a), int(b)) for a, b in re.findall(r"\((\d+),\s*(\d+)\)", m.group(1))}
        self.assertEqual(rows("creature_queststarter"), {(ORC, q) for q in STARTS})
        self.assertEqual(rows("creature_questender"), {(ORC, q) for q in ENDS})
        self.assertNotIn(5722, ENDS, "Maur Grimtotem's corpse stays 5722's ender")
        self.assertNotIn(5724, STARTS, "Maur Grimtotem's corpse starts 5724")

    def test_the_five_quests_go_neutral(self):
        self.assertIn("UPDATE `quest_template` SET `AllowableRaces` = 0 WHERE `ID` IN (5722, 5723, 5724, 5725, 5761) "
                      "AND `AllowableRaces` = 690", self.text)

    def test_reputation_cleared_on_the_neutral_quests_only(self):
        rep = [s for s in self.stmts if "`RewardFactionID1` = 0" in s]
        self.assertEqual(len(rep), 2)
        for s in rep:
            for n in range(1, 6):
                self.assertIn(f"`RewardFactionValue{n}` = 0", s)
                self.assertIn(f"`RewardFactionOverride{n}` = 0", s)
        ids = " ".join(re.findall(r"WHERE `ID` (?:IN \([^)]*\)|= \d+)", " ".join(rep)))
        self.assertNotIn("5728", ids, "Hidden Enemies stays a Horde quest with its Orgrimmar reputation")

    def test_hidden_enemies_changes_xp_and_rewards_only(self):
        mine = [s for s in self.stmts if s.startswith("UPDATE `quest_template`") and re.search(r"`ID` = 5728\b", s)]
        self.assertEqual(len(mine), 2)
        self.assertTrue(any("`RewardXPDifficulty` = 9" in s and "`RewardXPDifficulty` = 7" in s for s in mine))
        choice = next(s for s in mine if "RewardChoiceItemID1" in s)
        self.assertEqual(len(re.findall(r"`RewardChoiceItemID\d` = (?:\(SELECT|[1-9])", choice)), 3)
        for s in mine:
            self.assertNotIn("AllowableRaces", s)
            self.assertNotIn("PrevQuestID", s)
            self.assertNotIn("RewardMoney", s)

    def test_no_quest_is_added_and_14356_is_untouched(self):
        self.assertNotIn("INSERT INTO `quest_template`", self.text)
        self.assertEqual(re.findall(r"\b9010\d\b|\b901[1-9]\d\b", "\n".join(self.stmts)), [])
        code = "\n".join(line for line in self.text.splitlines() if not line.lstrip().startswith("--"))
        self.assertNotIn("14356", code)

    def test_every_update_is_guarded(self):
        for s in self.stmts:
            if s.startswith("UPDATE"):
                self.assertRegex(s, r"\bWHERE `ID`", s[:80])
                self.assertRegex(s[s.rindex("WHERE"):], r"`\w+` = ", s[:80])

    def test_the_new_text_has_no_faction_voice(self):
        for s in self.stmts:
            if not s.startswith("UPDATE") or "`LogDescription`" not in s and "RewardText" not in s \
                    and "CompletionText" not in s and "`QuestDescription`" not in s:
                continue
            new = s[:s.rindex("WHERE")]
            for word in BANNED_VOICE:
                self.assertNotIn(word, new, f"{word!r} in the new text of {s[:70]!r}")

    def test_log_lines_name_the_orc_and_the_stock_ender(self):
        wanted = {
            5725: ("Grunt Dranok", "Varimathras"), 5761: ("Grunt Dranok", "Neeru Fireblade"),
            5724: ("Grunt Dranok", "Rahauro"), 5723: ("Grunt Dranok", "Rahauro"),
        }
        for quest, names in wanted.items():
            stmt = next(s for s in self.stmts if s.startswith("UPDATE `quest_template` SET `LogDescription`")
                        and re.search(rf"WHERE `ID` = {quest}\b", s))
            new = stmt[:stmt.rindex("WHERE")]
            for name in names:
                self.assertIn(name, new)

    def test_no_text_sends_the_player_to_find_the_chasm_in_orgrimmar(self):
        for s in self.stmts:
            new = s[:s.rindex("WHERE")] if s.startswith("UPDATE") else ""
            for words in ("darkest areas of Orgrimmar", "Search Orgrimmar", "Find Ragefire Chasm"):
                self.assertNotIn(words, new, s[:80])

    def test_the_progress_text_of_the_power_to_destroy_is_plain(self):
        stmt = next(s for s in self.stmts if s.startswith("UPDATE `quest_request_items`") and "`ID` = 5725 " in s)
        self.assertNotIn("awaiting my attention", stmt[:stmt.rindex("WHERE")])

    def _choices(self) -> dict[int, list[str | int]]:
        """quest -> its choices in slot order: the name looked up, or the item id."""
        found = {}
        for s in self.stmts:
            if not s.startswith("UPDATE `quest_template`") or "`RewardChoiceItemID1` = " not in s[:s.rindex("WHERE")]:
                continue
            quest = int(re.search(r"WHERE `ID` = (\d+)\b", s).group(1))
            self.assertNotIn(quest, found)
            slots = re.findall(r"`RewardChoiceItemID(\d)` = (?:\(SELECT `entry` FROM `item_template` "
                               r"WHERE `name` = '((?:[^']|'')+)'\)|(\d+))", s[:s.rindex("WHERE")])
            self.assertEqual([int(slot) for slot, _, _ in slots], list(range(1, len(slots) + 1)), quest)
            found[quest] = [name.replace("''", "'") if name else int(item) for _, name, item in slots]
        return found

    def test_each_quest_gives_its_own_items_in_order(self):
        choices = self._choices()
        self.assertEqual(set(choices), set(CHOICES))
        for quest, keys in CHOICES.items():
            self.assertEqual(len(choices[quest]), len(keys), quest)
            if any(isinstance(c, str) for c in choices[quest]):
                self.assertEqual(choices[quest], [ITEMS[key][0] for key in keys], quest)
        self.assertNotIn("LIMIT 1", self.text, "a duplicate name must fail (error 1242), not pick a row")

    def test_the_choices_are_the_minted_ids(self):
        minted: dict[str, int] = {}
        for line in ID_LOCK.read_text(encoding="utf-8").splitlines():
            m = re.match(r"(\d+) (rfcq_\w+) normal\b", line)
            if m:
                self.assertNotIn(m.group(2), minted)
                minted[m.group(2)] = int(m.group(1))
        if not minted:
            self.skipTest("item_ids.lock has no rfcq_ line yet: the SQL looks the items up by name")
        self.assertEqual(sorted(minted), sorted(ITEMS))
        self.assertEqual(self._choices(), {quest: [minted[key] for key in keys] for quest, keys in CHOICES.items()},
                         "deploy step: replace the name lookups with the ids of item_ids.lock (R-Q-m1)")


class TestItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"].startswith("rfcq_")}

    def test_the_seven_items(self):
        self.assertEqual(sorted(self.decls), sorted(ITEMS))
        for key, (name, quality, ilvl, primary, secondary, share) in ITEMS.items():
            d = self.decls[key]
            self.assertEqual((d.name, d.quality, d.ilvl, d.primary, d.secondary, d.primary_share),
                             (name, quality, ilvl, primary, secondary, share), key)
            self.assertEqual(d.required_level, 0, key)
            self.assertEqual(d.ladder.name, "quest_reward", key)

    def test_levels_follow_the_quest_levels(self):
        # quest level + 5: 5723 is level 15, 5761 level 16; the epics are the designer's 26
        self.assertEqual({d.ilvl for d in self.decls.values() if d.quality == GREEN}, {20})
        self.assertEqual({d.ilvl for d in self.decls.values() if d.quality == BLUE}, {21})
        self.assertEqual({d.ilvl for d in self.decls.values() if d.quality == EPIC}, {26})

    def test_roles_and_armor_types(self):
        like = {k: d.like for k, d in self.decls.items()}
        # waist: Str mail 4707, Agi leather 10403, Int cloth 4785; boots 6582 leather; shield 15504; gloves 15509 mail,
        # 14124 cloth (a healer: priests cannot wear leather)
        self.assertEqual(like, {
            "rfcq_embersworn_girdle": 4707, "rfcq_cinderstalkers_belt": 10403, "rfcq_ashcallers_sash": 4785,
            "rfcq_beastslayers_treads": 6582, "rfcq_beastslayers_bulwark": 15504,
            "rfcq_troggbane_gauntlets": 15509, "rfcq_chasm_tenders_gloves": 14124,
        })
        self.assertEqual(self.decls["rfcq_beastslayers_bulwark"].secondary, "Parry/Block")  # ruling 12: plate tank
        for key, d in self.decls.items():
            self.assertNotIn("Dodge", d.secondary, f"{key}: ruling 24 (and these are not rings or necks)")

    def test_every_shape_stat_rounds_to_a_point(self):
        stats = materialized_tier_stats(self.decls)
        for key, tiers in stats.items():
            for tier, got in tiers.items():
                for stat, value in got.items():
                    self.assertGreaterEqual(value, 1, f"{key} {tier}: stat {stat} rounds to 0 ({got})")
                # a green: the primary and one secondary; a blue or an epic: the primary and a secondary pair
                want = 2 if self.decls[key].quality == GREEN else 3
                self.assertEqual(len(got), want, f"{key} {tier}: {got}")


class TestLock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = {}
        for line in LOCK.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                fields = line.split("#")[0].split()
                cls.lines[int(fields[0])] = fields

    def test_the_power_to_destroy_choices_are_blue(self):
        for entry, secondary in LOCK_BLUE.items():
            _, quest_level, quality, ilvl, primary, sec, share, spells = self.lines[entry]
            self.assertEqual((int(quest_level), int(quality), int(ilvl), int(sec), int(share), spells),
                             (16, BLUE, 21, secondary, 6000, "-"), entry)
            self.assertIn(int(sec), PAIR_SHAPES, f"{entry}: a blue takes a pair shape")

    def test_the_satchel_pair_stays_green(self):
        for entry in LOCK_GREEN:
            fields = self.lines[entry]
            self.assertEqual((int(fields[2]), int(fields[3]), int(fields[6])), (GREEN, 21, 8000), entry)


if __name__ == "__main__":
    unittest.main()
