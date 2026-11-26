"""
Zul'Farrak build, the quests WP (handoff 4.Q, section 7 #50-#55): the entrance giver, the sixteen reward items and the
hand SQL rev_quests_zul_farrak.sql.

Checks:
  - Kizzi Fuseboot 301090: a civilian quest giver (npcflag 2, flags_extra 2), faction 35, level 46, subname
    "Steamwheedle Cartel", no AI, Tran'rek's display 11379, in the `zul_farrak` creature reservation, named in the
    heroic call's `normal_only_creatures`;
  - the SQL: her spawn is exactly (1219.16, 848.49, 10.05, o 4.71) on map 209 with spawnMask 1; she starts and ends
    2865, 3042, 2846, 2768 and 2770 and none of the three open-world quests; XP difficulty 9 on 3527 and 8 on 2936 and
    2991; the stock money, reputation, races, chains and rewards of 2846 and 2770 stay (the file touches none of them);
    no quest id is inserted; every UPDATE is guarded; the log lines name her and the stock ender; no reward is looked
    up by name (Ragefire Chasm R-Q-m1);
  - the items: sixteen `zfq_` declarations on the one-tier quest ladder with the handoff's qualities, item levels,
    armor types and roles (ruling 24, no weapon, no leather healer, every healer cloth), every shape stat rounds to a
    point on the tier, and each quest's choices are its own items in order: the ids of item_ids.lock once the write
    run minted them, before that the next sixteen ids in declaration order;
  - quest_rewards.lock: the four stock rewards this dungeon keeps (9527, 9533, 9534, 11122) are untouched.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_dungeon_quests.py
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

GOBLIN = 301090
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_quests_zul_farrak.sql"
LOCK = TOOL_ROOT / "source" / "items" / "quest_rewards.lock"
ID_LOCK = TOOL_ROOT / "source" / "items" / "item_ids.lock"
NPC_DIR = TOOL_ROOT / "source" / "npcs" / "zul_farrak"
DUNGEON_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "zul_farrak.py"

DUNGEON_QUESTS = (2865, 3042, 2846, 2768, 2770)
OPEN_WORLD = (3527, 2936, 2991)
GREEN, BLUE, EPIC = 2, 3, 4

# key: (name, quality, item level, like, primary shape, secondary shape, share)
ITEMS = {
    "zfq_pauldrons_of_mosharu": ("Pauldrons of Mosh'aru", EPIC, 57, 11632, "Strength (Solo)", "Crit/Mastery", 6000),
    "zfq_spaulders_of_mosharu": ("Spaulders of Mosh'aru", EPIC, 57, 10783, "Agility (Solo)", "Crit/Proc", 6000),
    "zfq_amice_of_mosharu": ("Amice of Mosh'aru", EPIC, 57, 11624, "Intellect (Solo)", "Crit/Haste", 6000),
    "zfq_shadras_chitin_vambraces": ("Shadra's Chitin Vambraces", BLUE, 52, 17746, "Strength (Solo)",
                                     "Haste/Mastery", 6000),
    "zfq_shadras_chitin_bracers": ("Shadra's Chitin Bracers", BLUE, 52, 10800, "Agility (Solo)", "Crit/Haste", 6000),
    "zfq_shadras_silken_cuffs": ("Shadra's Silken Cuffs", BLUE, 52, 9433, "Intellect (Solo)", "Haste/Mastery", 6000),
    "zfq_gutchewers_vambraces": ("Gutchewer's Vambraces", BLUE, 52, 12550, "Strength (Solo)", "Haste/Mastery", 6000),
    "zfq_gutchewers_bracers": ("Gutchewer's Bracers", BLUE, 52, 13120, "Agility (Solo)", "Crit/Haste", 6000),
    "zfq_gutchewers_cuffs": ("Gutchewer's Cuffs", BLUE, 52, 12546, "Intellect (Solo)", "Haste/Mastery", 6000),
    "zfq_scarabhide_belt": ("Scarabhide Belt", GREEN, 50, 17778, "Agility (Solo)", "Haste (Solo)", 8000),
    "zfq_scarabplate_girdle": ("Scarabplate Girdle", GREEN, 50, 10788, "Strength (Solo)", "Crit (Solo)", 8000),
    "zfq_sandtempered_slippers": ("Sandtempered Slippers", GREEN, 50, 10629, "Intellect (Solo)", "Crit (Solo)", 8000),
    "zfq_sandtempered_sandals": ("Sandtempered Sandals", GREEN, 50, 17748, "Spirit (Solo)", "Mastery (Solo)", 8000),
    "zfq_dowsers_legplates": ("Dowser's Legplates", BLUE, 52, 10633, "Strength (Solo)", "Crit/Haste", 6000),
    "zfq_dowsers_spaulders": ("Dowser's Spaulders", BLUE, 52, 17749, "Agility (Solo)", "Haste/Proc", 6000),
    "zfq_dowsers_greaves": ("Dowser's Greaves", BLUE, 52, 12555, "Strength (Solo)", "Parry/Mastery", 6000),
}
# quest -> its new choice items in slot order, and the slot the first one takes (2768 keeps 9533 and 9534 in 1 and 2)
CHOICES = {
    3527: (1, ("zfq_pauldrons_of_mosharu", "zfq_spaulders_of_mosharu", "zfq_amice_of_mosharu")),
    2936: (1, ("zfq_shadras_chitin_vambraces", "zfq_shadras_chitin_bracers", "zfq_shadras_silken_cuffs")),
    2991: (1, ("zfq_gutchewers_vambraces", "zfq_gutchewers_bracers", "zfq_gutchewers_cuffs")),
    2865: (1, ("zfq_scarabhide_belt", "zfq_scarabplate_girdle")),
    3042: (1, ("zfq_sandtempered_slippers", "zfq_sandtempered_sandals")),
    2768: (3, ("zfq_dowsers_legplates", "zfq_dowsers_spaulders", "zfq_dowsers_greaves")),
}
# quest -> the item level its choices take (quest level + 5)
QUEST_ILEVEL = {3527: 57, 2936: 52, 2991: 52, 2865: 50, 3042: 50, 2768: 52}  # 3527 and 2936 by the user's ruling
# stock reward entry -> the lock line fields the dungeon keeps as they are: quality, item level
LOCK_KEPT = {9527: (GREEN, 51), 9533: (BLUE, 52), 9534: (BLUE, 52), 11122: (GREEN, 55)}

# the armor type each `like` item has (class 4: subclass 1 cloth, 2 leather, 3 mail, 4 plate) and its slot
LIKE_SLOT = {
    11632: ("plate", "shoulders"), 10783: ("leather", "shoulders"), 11624: ("cloth", "shoulders"),
    17746: ("plate", "wrist"), 10800: ("leather", "wrist"), 9433: ("cloth", "wrist"),
    12550: ("plate", "wrist"), 13120: ("leather", "wrist"), 12546: ("cloth", "wrist"),
    17778: ("leather", "belt"), 10788: ("plate", "belt"), 10629: ("cloth", "boots"), 17748: ("cloth", "boots"),
    10633: ("plate", "legs"), 17749: ("leather", "shoulders"), 12555: ("plate", "boots"),
}
FACTION_VOICE = ("Horde", "Alliance", "Thrall", "Warchief", "Forsaken", "Stormwind", "Orgrimmar", "Ironforge")


def _sql() -> str:
    return SQL.read_text(encoding="utf-8")


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("--"))


def _statements(text: str) -> list[str]:
    return [s.strip() for s in re.split(r";\s*\n", _code(text) + "\n") if s.strip()]


def _minted() -> dict[str, int]:
    minted: dict[str, int] = {}
    for line in ID_LOCK.read_text(encoding="utf-8").splitlines():
        m = re.match(r"(\d+) (zfq_\w+) normal\b", line)
        if m:
            assert m.group(2) not in minted, m.group(2)
            minted[m.group(2)] = int(m.group(1))
    return minted


class TestEntranceGoblin(unittest.TestCase):
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
        cls.row = next(r for r in cls.reg.creature_templates if int(r["entry"]) == GOBLIN)

    def test_a_civilian_quest_giver_friendly_to_both_factions(self):
        row = self.row
        self.assertEqual(row["name"], "Kizzi Fuseboot")
        self.assertEqual(row["subname"], "Steamwheedle Cartel")
        self.assertEqual(int(row["faction"]), 35)
        self.assertEqual(int(row["npcflag"]), 2)
        self.assertEqual(int(row["flags_extra"]), 2)
        self.assertEqual((int(row["minlevel"]), int(row["maxlevel"])), (46, 46))
        self.assertEqual(row["AIName"], "")
        self.assertEqual(row["ScriptName"], "")
        self.assertEqual(int(row["lootid"]), 0)
        self.assertEqual(int(row["gossip_menu_id"]), 0)
        self.assertEqual(int(row["difficulty_entry_1"] or 0), 0, "no heroic body: she is normal only")

    def test_the_look_is_trannreks_goblin(self):
        models = [m for m in self.reg.creature_template_models if int(m["CreatureID"]) == GOBLIN]
        self.assertEqual([int(m["CreatureDisplayID"]) for m in models], [11379])

    def test_the_heroic_call_keeps_her_normal_only(self):
        self.assertRegex(DUNGEON_FILE.read_text(encoding="utf-8"), r"normal_only_creatures=\(301090,\)")

    def test_she_sits_in_the_dungeons_creature_reservation(self):
        self.assertEqual(id_blocks.out_of_reservation("zul_farrak", {"creature": [GOBLIN]}), [])

    def test_the_quests_file_declares_only_her(self):
        declared = {int(r["entry"]) for r in self.reg.creature_templates}
        self.assertIn(GOBLIN, declared)
        file_text = (NPC_DIR / "dungeon_quests.py").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"creature_template\(\s*(\d+)", file_text), [str(GOBLIN)])


class TestSql(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = _sql()
        cls.code = _code(cls.text)
        cls.stmts = _statements(cls.text)

    def test_the_spawn_is_the_designers_spot(self):
        m = re.search(r"INSERT INTO `creature`.*?VALUES\s*\((.*?)\);", self.text, re.S)
        self.assertIsNotNone(m)
        fields = [f.strip() for f in m.group(1).split(",")]
        # guid, id, map, zoneId, areaId, spawnMask, phaseMask, equipment_id, x, y, z, o, respawn, MovementType
        self.assertEqual(fields[0:3], ["3010900", "301090", "209"])
        self.assertEqual(fields[5], "1", "spawnMask 1: normal only")
        self.assertEqual([float(v) for v in fields[8:12]], [1219.16, 848.49, 10.05, 4.71])
        self.assertEqual(fields[13], "0", "standing still")

    def test_starters_and_enders(self):
        def rows(table):
            m = re.search(rf"INSERT INTO `{table}` \(`id`, `quest`\) VALUES\s*(.*?);", self.text, re.S)
            self.assertIsNotNone(m, table)
            return {(int(a), int(b)) for a, b in re.findall(r"\((\d+),\s*(\d+)\)", m.group(1))}
        self.assertEqual(rows("creature_queststarter"), {(GOBLIN, q) for q in DUNGEON_QUESTS})
        self.assertEqual(rows("creature_questender"), {(GOBLIN, q) for q in DUNGEON_QUESTS})
        for quest in OPEN_WORLD:
            self.assertNotIn(f"({GOBLIN}, {quest})", self.code, "the open-world quests keep their stock enders")

    def test_xp_difficulty(self):
        self.assertIn("UPDATE `quest_template` SET `RewardXPDifficulty` = 9 WHERE `ID` = 3527 "
                      "AND `RewardXPDifficulty` = 7", self.text)
        self.assertIn("UPDATE `quest_template` SET `RewardXPDifficulty` = 8 WHERE `ID` IN (2936, 2991) "
                      "AND `RewardXPDifficulty` = 7", self.text)
        for quest in DUNGEON_QUESTS:
            self.assertNotRegex(self.code, rf"RewardXPDifficulty` = \d+ WHERE `ID` (?:= {quest}|IN \([^)]*\b{quest}\b)")

    def test_no_money_reputation_race_or_chain_field_is_touched(self):
        """The stock copper, Gadgetzan reputation (#52 A), races and chains stay (#50 A): the file sets only the XP
        difficulty, the reward choices and the log text of `quest_template`."""
        allowed = {"RewardXPDifficulty", "LogDescription", "QuestCompletionLog"}
        for s in self.stmts:
            if not s.startswith("UPDATE `quest_template`"):
                continue
            new = s[:s.rindex("WHERE")]
            fields = set(re.findall(r"`(\w+)` = ", new))
            extra = {f for f in fields if f not in allowed and not f.startswith("RewardChoiceItem")}
            self.assertEqual(extra, set(), s[:90])
        self.assertNotIn("quest_template_addon", self.code)
        self.assertNotRegex(self.code, r"RewardMoney|RewardFaction|AllowableRaces|PrevQuestID|ExclusiveGroup")

    def test_no_quest_is_added_and_the_stock_rewards_are_not_overwritten(self):
        self.assertNotIn("INSERT INTO `quest_template`", self.text)
        self.assertEqual(re.findall(r"\b9010\d\b|\b901[1-9]\d\b", self.code), [])
        for s in self.stmts:
            m = re.search(r"WHERE `ID` = (2846|2770)\b", s)
            if m:
                self.assertNotRegex(s[:s.rindex("WHERE")], r"RewardChoiceItem|RewardItem",
                                    f"{m.group(1)} keeps its reward")

    def test_every_update_is_guarded(self):
        for s in self.stmts:
            if s.startswith("UPDATE"):
                self.assertRegex(s, r"\bWHERE `ID`", s[:80])
                self.assertRegex(s[s.rindex("WHERE"):], r"`\w+` (?:=|IN) ", s[:80])
                self.assertIn(" AND `", s[s.rindex("WHERE"):], "needs a stock-value guard")

    def test_the_new_text_has_no_faction_voice(self):
        for s in self.stmts:
            if not s.startswith("UPDATE `quest_template` SET `LogDescription`"):
                continue
            new = s[:s.rindex("WHERE")]
            for word in FACTION_VOICE:
                self.assertNotIn(word, new, f"{word!r} in the new text of {s[:70]!r}")

    def test_log_lines_name_her_and_the_stock_ender(self):
        wanted = {
            2865: "Tran''rek", 3042: "Trenton Lighthammer", 2846: "Tabetha",
            2768: "Chief Engineer Bilgewhizzle", 2770: "Wizzle Brassbolts",
        }
        texts = {}
        for quest, ender in wanted.items():
            stmt = next(s for s in self.stmts if s.startswith("UPDATE `quest_template` SET `LogDescription`")
                        and re.search(rf"WHERE `ID` = {quest}\b", s))
            new = stmt[:stmt.rindex("WHERE")]
            log, completion = re.search(r"`LogDescription` = '((?:[^']|'')*)'", new), \
                re.search(r"`QuestCompletionLog` = '((?:[^']|'')*)'", new)
            self.assertIsNotNone(log, quest)
            self.assertIsNotNone(completion, quest)
            for line in (log.group(1), completion.group(1)):
                self.assertIn("Kizzi Fuseboot at the entrance to Zul''Farrak", line, quest)
                self.assertIn(ender, line, quest)
                self.assertLess(line.index("Kizzi"), line.index(ender), "the entrance giver is named first")
            texts[quest] = (log.group(1), completion.group(1))
        self.assertEqual(set(texts), set(DUNGEON_QUESTS))

    def test_only_the_five_dungeon_quests_get_new_text(self):
        for s in self.stmts:
            if "`LogDescription`" in s[:s.rindex("WHERE")] if "WHERE" in s else False:
                self.assertIn(int(re.search(r"WHERE `ID` = (\d+)\b", s).group(1)), DUNGEON_QUESTS)
        self.assertNotRegex(self.code, r"quest_offer_reward|quest_request_items")

    def _choices(self) -> dict[int, dict[int, int]]:
        """quest -> {slot: item id}; a name lookup is a failure (Ragefire Chasm R-Q-m1)."""
        found = {}
        for s in self.stmts:
            if not s.startswith("UPDATE `quest_template`") or "`RewardChoiceItemID" not in s[:s.rindex("WHERE")]:
                continue
            quest = int(re.search(r"WHERE `ID` = (\d+)\b", s).group(1))
            self.assertNotIn(quest, found)
            new = s[:s.rindex("WHERE")]
            self.assertNotIn("SELECT", new, "reward ids are literal, never looked up by name (R-Q-m1)")
            found[quest] = {int(slot): int(item) for slot, item in re.findall(r"`RewardChoiceItemID(\d)` = (\d+)", new)}
            quantities = re.findall(r"`RewardChoiceItemQuantity(\d)` = (\d+)", new)
            self.assertEqual({int(a) for a, _ in quantities}, set(found[quest]), quest)
            self.assertEqual({int(b) for _, b in quantities}, {1}, quest)
        return found

    def test_no_reward_is_looked_up_by_name(self):
        self.assertNotIn("SELECT", self.code)
        self.assertNotIn("LIMIT 1", self.code)
        self.assertNotRegex(self.code, r"`name` = ")

    def test_each_quest_gives_its_own_slots(self):
        choices = self._choices()
        self.assertEqual(set(choices), set(CHOICES))
        for quest, (first, keys) in CHOICES.items():
            self.assertEqual(sorted(choices[quest]), list(range(first, first + len(keys))), quest)
        # 2768 keeps the stock ring and headpiece in slots 1 and 2: the UPDATE is guarded on them
        stmt = next(s for s in self.stmts if re.search(r"WHERE `ID` = 2768\b", s) and "RewardChoiceItemID3" in s)
        self.assertRegex(stmt[stmt.rindex("WHERE"):], r"`RewardChoiceItemID1` = 9533 AND `RewardChoiceItemID2` = 9534")

    def test_the_choice_ids_follow_the_declaration_order(self):
        choices = self._choices()
        ids = [choices[quest][slot] for quest, (first, keys) in CHOICES.items()
               for slot in range(first, first + len(keys))]
        self.assertEqual(len(ids), len(ITEMS))
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(ids, list(range(ids[0], ids[0] + len(ids))), "the write run mints in declaration order")
        # the quests run in the declaration order of the item file, so ids[i] is key i
        keys = [key for _quest, (_first, ks) in CHOICES.items() for key in ks]
        self.assertEqual(keys, list(ITEMS))

    def test_the_choices_are_the_minted_ids(self):
        minted = _minted()
        if not minted:
            self.skipTest("item_ids.lock has no zfq_ line yet: the write run has not minted the quest rewards")
        self.assertEqual(sorted(minted), sorted(ITEMS))
        choices = self._choices()
        for quest, (first, keys) in CHOICES.items():
            self.assertEqual([choices[quest][first + i] for i in range(len(keys))], [minted[k] for k in keys], quest,
                             "deploy step: set the ids of item_ids.lock into the SQL")


class TestItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"].startswith("zfq_")}

    def test_the_sixteen_items(self):
        self.assertEqual(list(self.decls), list(ITEMS), "declaration order is the mint order")
        for key, (name, quality, ilvl, like, primary, secondary, share) in ITEMS.items():
            d = self.decls[key]
            self.assertEqual((d.name, d.quality, d.ilvl, d.like, d.primary, d.secondary, d.primary_share),
                             (name, quality, ilvl, like, primary, secondary, share), key)
            self.assertEqual(d.required_level, 0, key)
            self.assertEqual(d.ladder.name, "quest_reward", key)

    def test_levels_follow_the_quest_levels(self):
        for quest, (first, keys) in CHOICES.items():
            for key in keys:
                self.assertEqual(self.decls[key].ilvl, QUEST_ILEVEL[quest],
                                 f"{quest} {key}: quest level + 5, or the ruled level")
        self.assertTrue(all(d.ilvl <= 55 for d in self.decls.values() if d.quality == GREEN))
        self.assertTrue(all(d.ilvl <= 60 for d in self.decls.values()))

    def test_qualities_follow_the_quests(self):
        quality = {3527: EPIC, 2936: BLUE, 2991: BLUE, 2865: GREEN, 3042: GREEN, 2768: BLUE}
        for quest, (_first, keys) in CHOICES.items():
            for key in keys:
                self.assertEqual(self.decls[key].quality, quality[quest], f"{quest} {key}")

    def test_one_choice_per_primary_and_role_where_the_handoff_says_so(self):
        def primaries(quest):
            return [self.decls[k].primary.split()[0] for k in CHOICES[quest][1]]
        for quest in (3527, 2936, 2991):
            self.assertEqual(primaries(quest), ["Strength", "Agility", "Intellect"], quest)
        self.assertEqual(primaries(2865), ["Agility", "Strength"])
        self.assertEqual(primaries(3042), ["Intellect", "Spirit"])
        self.assertEqual(primaries(2768), ["Strength", "Agility", "Strength"])
        self.assertEqual(self.decls["zfq_dowsers_greaves"].secondary, "Parry/Mastery")  # ruling 12: the plate tank

    def test_slots_and_armor_types(self):
        want = {
            3527: "shoulders", 2936: "wrist", 2991: "wrist", 2865: "belt", 3042: "boots",
        }
        for quest, slot in want.items():
            for key in CHOICES[quest][1]:
                self.assertEqual(LIKE_SLOT[self.decls[key].like][1], slot, key)
        self.assertEqual([LIKE_SLOT[self.decls[k].like] for k in CHOICES[2768][1]],
                         [("plate", "legs"), ("leather", "shoulders"), ("plate", "boots")])
        by_primary = {"Strength": "plate", "Agility": "leather", "Intellect": "cloth", "Spirit": "cloth"}
        for key, d in self.decls.items():
            self.assertEqual(LIKE_SLOT[d.like][0], by_primary[d.primary.split()[0]], f"{key}: the armor type")
        for key in ("zfq_sandtempered_sandals", "zfq_shadras_silken_cuffs", "zfq_gutchewers_cuffs",
                    "zfq_amice_of_mosharu", "zfq_sandtempered_slippers"):
            self.assertEqual(LIKE_SLOT[self.decls[key].like][0], "cloth", f"{key}: no leather healer piece")

    def test_no_weapon_no_ring_and_no_dodge(self):
        for key, d in self.decls.items():
            self.assertNotIn("Dodge", d.secondary, f"{key}: ruling 24")
            self.assertIn(LIKE_SLOT[d.like][1], {"shoulders", "wrist", "belt", "boots", "legs"}, key)

    def test_roles_are_distinct_within_each_quest(self):
        for quest, (_first, keys) in CHOICES.items():
            pairs = [(self.decls[k].primary, self.decls[k].secondary) for k in keys]
            self.assertEqual(len(set(pairs)), len(pairs), quest)

    def test_blues_and_epics_take_a_pair_and_greens_a_single(self):
        for key, d in self.decls.items():
            if d.quality == GREEN:
                self.assertIn("(Solo)", d.secondary, key)
                self.assertEqual(d.primary_share, 8000, key)
            else:
                self.assertNotIn("(Solo)", d.secondary, key)
                self.assertEqual(d.primary_share, 6000, key)

    def test_every_shape_stat_rounds_to_a_point(self):
        stats = materialized_tier_stats(self.decls)
        self.assertEqual(sorted(stats), sorted(ITEMS))
        for key, tiers in stats.items():
            for tier, got in tiers.items():
                for stat, value in got.items():
                    self.assertGreaterEqual(value, 1, f"{key} {tier}: stat {stat} rounds to 0 ({got})")
                want = 2 if self.decls[key].quality == GREEN else 3
                self.assertEqual(len(got), want, f"{key} {tier}: {got}")

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
        ids = set(self.lines)
        minted = _minted()
        self.assertEqual(ids & set(minted.values()), set())


if __name__ == "__main__":
    unittest.main()
