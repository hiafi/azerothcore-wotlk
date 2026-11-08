"""
lib/heroic_templates.py and its DSL half (dungeon difficulties E2, WP-G): the heroic creature template generator.

Covered: `creature()` / `dungeon(creatures=, extra=, roles=, skip=)` / `heroic(tier=, tier_values=, overrides=)`
validation; the entry set (declared | live spawned outside events | encounter credits, minus skip=, critters,
triggers, NPCs, event-only creatures; undeclared live creatures reported); the modifier solve per class, rank and swing
against the engine's formulas; overrides; the lock file (parse errors, append-only assignment, gaps never reused, a
full block, byte-for-byte keep); the generated row (copied columns, level, exp, INSTANCE_BIND, scripts cleared,
difficulty entries 0, loot and kill credit kept); the lints (engine refusals, exp, boss without an encounter row,
normal-only SmartAI rows and their widening UPDATE, SpellDifficulty swaps, skipped creatures); expand() wiring
(heroic_entries -> T2's difficulty_entry_1 edits, a second expand() replaces its rows); render, the real
codestyle-sql.py and convergence (a second build over the read-back state emits nothing); override columns that
would undo the solve raise; a shipped creature leaving the set (ERROR) or `retired=` (guarded revert, no copies); a
heroic entry with no model row (ERROR); the real Deadmines declaration against the live replay and the committed lock
file.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_heroic_templates.py
"""

from __future__ import annotations

import math
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402
from lib import dungeon_heroic, heroic_templates, spell_tables, sql_dump, sqlcorpus  # noqa: E402
from lib.dsl import dungeon as dungeon_dsl  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.table_testkit import codestyle_sql, load_dsl, read_back  # noqa: E402

HT = heroic_templates
IDS_CFG = {
    "mapdifficulty": {"start": 1000, "end": 1099}, "dungeon_access": {"start": 122, "end": 199},
    "dungeonencounter": {"start": 1000, "end": 1199}, "creature_heroic": {"start": 310000, "end": 311999},
}
BLOCK = IDS_CFG["creature_heroic"]
# creature_classlevelstats level 60 (base dump, 2026-11-05)
STATS = {
    (60, 1): {"level": 60, "class": 1, "basehp0": 3052, "basehp1": 4979, "basemana": 0, "basearmor": 3750,
              "attackpower": 252, "damage_base": 33.9625},
    (60, 2): {"level": 60, "class": 2, "basehp0": 2442, "basehp1": 3984, "basemana": 2434, "basearmor": 3748,
              "attackpower": 238, "damage_base": 31.3842},
    (60, 8): {"level": 60, "class": 8, "basehp0": 2136, "basehp1": 3484, "basemana": 5751, "basearmor": 3025,
              "attackpower": 112, "damage_base": 28.7983},
}


def _tpl(entry: int, name: str = "", **columns) -> dict:
    row = dict(spell_tables.CREATURE_TEMPLATE_DEFAULTS)
    row.update(entry=entry, name=name or f"Creature {entry}", minlevel=18, maxlevel=19, rank=1, unit_class=1,
               BaseAttackTime=2000, faction=17, lootid=entry, KillCredit1=0, AIName="SmartAI")
    row.update(columns)
    return row


TEMPLATES = {
    644: _tpl(644, "Rhahk'Zor", BaseAttackTime=3500),
    645: _tpl(645, "Cookie", ScriptName="boss_cookie", KillCredit1=9999),
    642: _tpl(642, "Sneed's Shredder"),
    598: _tpl(598, "Defias Miner", rank=0),
    1729: _tpl(1729, "Defias Evoker", unit_class=8, ManaModifier=2),
    3586: _tpl(3586, "Miner Johnson", rank=2),
    2520: _tpl(2520, "Remote-Controlled Golem"),
    4075: _tpl(4075, "Rat", rank=0, type=8, flags_extra=2),
    5000: _tpl(5000, "Trigger", flags_extra=0x80),
    5001: _tpl(5001, "Quartermaster", npcflag=4224),
    5002: _tpl(5002, "Holiday Elder", rank=0),
    5003: _tpl(5003, "Undeclared Pirate"),
}
# One model row per creature: a heroic entry without one is an ERROR (Creature::InitEntry refuses it).
SIDE_ROWS = {"creature_template_model": [
    {"CreatureID": e, "Idx": 0, "CreatureDisplayID": 1000 + i, "DisplayScale": 1, "Probability": 1,
     "VerifiedBuild": 12340} for i, e in enumerate(sorted(TEMPLATES))
]}
SOURCE = '''
from lib.dsl.dungeon import creature, dungeon, heroic

CREATURES = (
    creature(644, "Rhahk'Zor", "boss", spawns=1),
    creature(645, "Cookie", "boss", spawns=1),
    creature(598, "Defias Miner", "trash", spawns=4),
    creature(642, "Sneed's Shredder", "trash", spawns=1),
    creature(1729, "Defias Evoker", "trash", spawns=2),
    creature(3586, "Miner Johnson", "trash", spawns=1),
    creature(2520, "Remote-Controlled Golem", "trash", summoned_by=("creature 622 smart cast 3605",)),
    creature(4075, "Rat", "critter", spawns=2),
    creature(5000, "Trigger", "trigger", spawns=1),
    creature(5001, "Quartermaster", "npc", spawns=1),
    creature(5002, "Holiday Elder", "trash", spawns=1, event=True),
)

deadmines = dungeon(
    36, "Deadmines", creatures=CREATURES, roles={642: "boss", 3586: "boss"}, skip=(2520,) if SKIP else (),
    heroic=heroic(map_difficulty_id=1000, access_id=122, min_level=60, spawn_mask=True, HEROIC_ARGS),
)
'''


def _source(skip=False, heroic_args="") -> str:
    return SOURCE.replace("SKIP", str(skip)).replace(", HEROIC_ARGS", (", " + heroic_args) if heroic_args else "")


def _spawns() -> dict:
    rows = [(1, 644), (2, 645), (3, 598), (4, 598), (5, 642), (6, 1729), (7, 3586), (8, 4075), (9, 5000), (10, 5001),
            (11, 5002), (12, 5003)]
    return {"creature": {g: {"guid": g, "id": e, "map": 36, "spawnMask": 3} for g, e in rows},
            "gameobject": {100: {"guid": 100, "id": 16398, "map": 36, "spawnMask": 3}}}


def _live(**kw) -> dungeon_heroic.LiveWorld:
    kw.setdefault("creature_templates", dict(TEMPLATES))
    kw.setdefault("spawns", _spawns())
    kw.setdefault("event_guids", {"creature": {11}, "gameobject": set()})
    kw.setdefault("stock_encounters", {161: {"ID": 161, "MapID": 36, "Difficulty": 0},
                                       165: {"ID": 165, "MapID": 36, "Difficulty": 0}})
    kw.setdefault("instance_encounters", {161: {"entry": 161, "creditType": 0, "creditEntry": 644},
                                          165: {"entry": 165, "creditType": 0, "creditEntry": 645}})
    kw.setdefault("class_level_stats", dict(STATS))
    kw.setdefault("spell_difficulty", {})
    kw.setdefault("side_rows", SIDE_ROWS)
    return dungeon_heroic.LiveWorld(**kw)


def _expand(source: str | None = None, lock: str = "", live=None, ids_cfg=IDS_CFG):
    dsl = load_dsl(source or _source(), ids_cfg=ids_cfg)
    dsl = {k: list(v) if isinstance(v, list) else v for k, v in dsl.items()}
    live = live or _live()
    out = dungeon_heroic.expand(dsl, lambda: live, ids_cfg=ids_cfg, lock=lock)
    return dsl, out


def _rows(dsl) -> dict[int, dict]:
    return {int(r["entry"]): r for r in dsl["creature_templates"]}


class DslTest(unittest.TestCase):
    def test_creature_validation(self):
        c = dungeon_dsl.creature(644, "Rhahk'Zor", "boss", spawns=1, summoned_by=("x",))
        self.assertEqual((c.entry, c.role, c.spawns, c.summoned_by, c.event), (644, "boss", 1, ("x",), False))
        for args, kw in (((0, "a", "boss"), {}), ((1, "a", "elite"), {}), ((1, "a", "boss"), {"spawns": -1}),
                         ((1, "a", "boss"), {"summoned_by": "creature 2"}), ((1, "a", "boss"), {"event": 1})):
            with self.subTest(args=args, kw=kw), self.assertRaises(ValueError):
                dungeon_dsl.creature(*args, **kw)

    def test_dungeon_creature_lists(self):
        dsl = load_dsl('''
from lib.dsl.dungeon import creature, dungeon
X = (creature(1, "A", "trash", spawns=2), creature(2, "B", "npc"))
dungeon(33, "SFK", creatures=X, extra=(creature(3, "C", "trash", summoned_by=("C++ boss_x",)),), roles={2: "trash"},
        skip=(1,))
''')
        entry = dsl["dungeons"][0]
        self.assertEqual([(c["entry"], c["role"], c["source"]) for c in entry["creatures"]],
                         [(1, "trash", "extracted"), (2, "trash", "extracted"), (3, "trash", "extra")])
        self.assertEqual(entry["skip"], (1,))
        self.assertIsNone(entry["heroic"])
        self.assertEqual(dsl["creature_templates"], [])  # a reference declaration emits nothing

    def test_dungeon_list_errors(self):
        for body in (
            'dungeon(33, "S", creatures=(creature(1, "A", "trash"),), extra=(creature(1, "A", "trash"),))',
            'dungeon(33, "S", creatures=(creature(1, "A", "trash"),), roles={2: "boss"})',
            'dungeon(33, "S", creatures=(creature(1, "A", "trash"),), roles={1: "elite"})',
            'dungeon(33, "S", creatures=((1, "A"),))',
            'dungeon(33, "S", skip=("x",))',
            'dungeon(33, "S", retired=(0,))',
            'dungeon(33, "S", retired=("3450",))',
        ):
            with self.subTest(body=body), self.assertRaises(ValueError):
                load_dsl(f"from lib.dsl.dungeon import creature, dungeon\n{body}\n")

    def test_heroic_tier_and_overrides(self):
        spec = dungeon_dsl.heroic(
            map_difficulty_id=1000, access_id=122, min_level=60, tier_values={"elite": (40_000, 600)},
            overrides={644: dict(health=320_000, columns={"speed_run": 1.4}), 598: dict(tier="rare", melee=300)},
        )
        self.assertEqual(spec.tier_values, (("elite", 40_000, 600),))
        from dataclasses import asdict  # noqa: PLC0415

        self.assertEqual(dungeon_dsl.override_dict(asdict(spec)), {
            598: {"melee": 300, "tier": "rare"}, 644: {"columns": {"speed_run": 1.4}, "health": 320_000},
        })
        base = dict(map_difficulty_id=1000, access_id=122, min_level=60)
        for kw in (dict(overrides={644: dict(hp=1)}), dict(overrides={644: dict(health=0)}),
                   dict(overrides={644: dict(tier="epic")}), dict(overrides={"644": dict(health=1)}),
                   dict(overrides={644: {}}), dict(overrides={644: dict(columns=["x"])}),
                   dict(tier_values={"elite": 40_000}), dict(tier_values={"champion": (1, 1)}),
                   dict(widen_smart_scripts=1), dict(tier="")):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                dungeon_dsl.heroic(**base, **kw)

    def test_override_columns_may_not_undo_the_solve(self):
        base = dict(map_difficulty_id=1000, access_id=122, min_level=60)
        for column in ("entry", "minlevel", "maxlevel", "exp", "HealthModifier", "DamageModifier", "BaseVariance"):
            with self.subTest(column=column), self.assertRaisesRegex(ValueError, "set by the tier solve"):
                dungeon_dsl.heroic(**base, overrides={644: dict(columns={column: 2})})
        dungeon_dsl.heroic(**base, overrides={644: dict(columns={"ArmorModifier": 2, "BaseAttackTime": 1500})})


class EntrySetTest(unittest.TestCase):
    def _entry(self, creatures, skip=()):
        return {"creatures": [{"entry": e, "role": r, "event": ev} for e, r, ev in creatures], "skip": tuple(skip)}

    def test_union_minus_skips(self):
        entry = self._entry([(644, "boss", False), (2520, "trash", False), (4075, "critter", False),
                             (5000, "trigger", False), (5001, "npc", False), (5002, "trash", True),
                             (642, "trash", False)], skip=(642,))
        chosen = HT.entry_set(entry, spawned={644, 598, 4075, 5000, 5001, 5003}, credits={645, 644},
                              templates=TEMPLATES)
        # declared (2520 summoned) | spawned (598, 5003 undeclared) | credit (645, undeclared) - skips
        self.assertEqual(chosen.included, {644: "boss", 645: "boss", 598: "trash", 2520: "trash", 5003: "trash"})
        self.assertEqual(chosen.skipped, {642: "skip=", 4075: "critter", 5000: "trigger", 5001: "npc",
                                          5002: "event only"})
        self.assertEqual(chosen.undeclared, [598, 645, 5003])

    def test_live_type_and_flags_win_over_a_trash_role(self):
        entry = self._entry([(4075, "trash", False), (5000, "trash", False)])
        chosen = HT.entry_set(entry, set(), set(), TEMPLATES)
        self.assertEqual(chosen.skipped, {4075: "critter (type 8)", 5000: "trigger (flags_extra 0x80)"})

    def test_event_creatures_join_when_the_heroic_takes_event_spawns(self):
        entry = self._entry([(5002, "trash", True)])
        self.assertEqual(HT.entry_set(entry, set(), set(), TEMPLATES).included, {})
        self.assertEqual(HT.entry_set(entry, {5002}, set(), TEMPLATES, event_spawns=True).included, {5002: "trash"})

    def test_a_missing_template_is_skipped(self):
        chosen = HT.entry_set(self._entry([(777, "trash", False)]), set(), set(), TEMPLATES)
        self.assertEqual(chosen.skipped, {777: "no live creature_template row"})


class SolveTest(unittest.TestCase):
    def _hit(self, stats, row, mod, swing):
        """Creature::CalculateMinMaxDamage for a creature with base weapon damage (SelectLevel) and no auras."""
        flat = stats["attackpower"] / 14.0 * row.get("BaseVariance", 1.0)
        mod = HT.f32(mod)
        return ((stats["damage_base"] + flat) * mod * swing, (1.5 * stats["damage_base"] + flat) * mod * swing)

    def test_tier_rows_per_class_rank_and_swing(self):
        for unit_class, swing_ms in ((1, 2000), (1, 3500), (2, 1500), (8, 2000)):
            stats = STATS[(60, unit_class)]
            row = {"BaseAttackTime": swing_ms, "BaseVariance": 1.0, "ArmorModifier": 1, "ManaModifier": 1}
            for tier_row, (health, melee) in HT.TIERS["vanilla"].rows.items():
                with self.subTest(unit_class=unit_class, swing=swing_ms, tier=tier_row):
                    solved = HT.solve(row, stats, health, melee, tier_row)
                    self.assertEqual(solved.health, health)
                    self.assertEqual(math.ceil(stats["basehp0"] * HT.f32(solved.columns["HealthModifier"])), health)
                    low, high = self._hit(stats, row, solved.columns["DamageModifier"], swing_ms / 1000)
                    self.assertAlmostEqual(low, solved.min_damage)
                    self.assertAlmostEqual(high, solved.max_damage)
                    # the tier's melee is the average hit at 2.0 sec, scaled by the template's swing
                    self.assertAlmostEqual((low + high) / 2, melee * swing_ms / 2000, delta=melee * 0.001)

    def test_elite_warrior_numbers(self):
        solved = HT.solve({"BaseAttackTime": 2000}, STATS[(60, 1)], 37_000, 550, "elite")
        self.assertEqual(solved.columns, {"HealthModifier": 12.1231, "DamageModifier": 4.549})
        self.assertEqual((round(solved.min_damage), round(solved.max_damage)), (473, 627))
        self.assertEqual((solved.armor, solved.mana), (3750, 0))

    def test_variance_and_mana(self):
        solved = HT.solve({"BaseAttackTime": 2000, "BaseVariance": 0.5, "ManaModifier": 2}, STATS[(60, 8)],
                          37_000, 550, "elite")
        self.assertEqual(solved.mana, 11_502)
        self.assertAlmostEqual((solved.min_damage + solved.max_damage) / 2, 550, delta=1)

    def test_health_modifier_lands_on_the_target(self):
        for base in (3052, 2442, 2136):
            for health in (12_000, 37_000, 74_000, 142_000, 300_000, 472_000):
                with self.subTest(base=base, health=health):
                    mod = HT.health_modifier(base, health)
                    self.assertLessEqual(abs(math.ceil(base * HT.f32(mod)) - health), 1)


class LockTest(unittest.TestCase):
    TEXT = HT.LOCK_HEADER + "644 310000 36 Rhahk'Zor\n598 310002 36 Defias Miner\n"

    def test_parse(self):
        lock = HT.parse_lock(self.TEXT, BLOCK)
        self.assertEqual(lock.pairs, {644: 310000, 598: 310002})

    def test_parse_errors(self):
        for text in ("644 310000\n", "644 310000 36 A\n644 310001 36 A\n", "644 310000 36 A\n645 310000 36 B\n",
                     "644 320000 36 A\n", "x 310000 36 A\n"):
            with self.subTest(text=text), self.assertRaises(HT.LockError):
                HT.parse_lock(text, BLOCK)

    def test_assign_keeps_ids_and_appends_after_the_highest(self):
        lock = HT.parse_lock(self.TEXT, BLOCK)
        pairs, appended = HT.assign_ids(lock, [(598, 36, "Defias Miner"), (2520, 36, "Golem"), (644, 36, "R"),
                                               (1729, 36, "Defias  Evoker")], BLOCK)
        self.assertEqual(pairs, {644: 310000, 598: 310002, 2520: 310003, 1729: 310004})  # 310001 never reused
        self.assertEqual(appended, ["2520 310003 36 Golem", "1729 310004 36 Defias Evoker"])
        text = HT.lock_text(lock, appended)
        self.assertTrue(text.startswith(self.TEXT))
        self.assertEqual(HT.parse_lock(text, BLOCK).pairs, pairs)
        # stable: a second assignment over the written file appends nothing and moves nothing
        again, more = HT.assign_ids(HT.parse_lock(text, BLOCK), [(1729, 36, "x"), (598, 36, "y")], BLOCK)
        self.assertEqual((again, more), (pairs, []))

    def test_a_new_file_gets_the_header_and_a_full_block_is_an_error(self):
        pairs, appended = HT.assign_ids(HT.Lock(), [(1, 36, "A")], BLOCK)
        self.assertEqual(pairs, {1: 310000})
        self.assertTrue(HT.lock_text(HT.Lock(), appended).startswith("# Heroic creature template ids"))
        with self.assertRaises(HT.LockError):
            HT.assign_ids(HT.Lock(), [(1, 36, "A"), (2, 36, "B")], {"start": 5, "end": 5})


class BuildTest(unittest.TestCase):
    def test_rows_heroic_entries_and_t2_edits(self):
        dsl, out = _expand()
        self.assertEqual(out.errors, [])
        rows = _rows(dsl)
        mapping = dsl["dungeons"][0]["heroic_entries"]
        # declared hostile creatures + the undeclared live spawn 5003; credit 645; critter/trigger/npc/event skipped
        self.assertEqual(mapping, {598: 310000, 642: 310001, 644: 310002, 645: 310003, 1729: 310004, 2520: 310005,
                                   3586: 310006, 5003: 310007})
        self.assertEqual(set(rows), set(mapping.values()))
        self.assertEqual(out.lock_appended[0], "598 310000 36 Defias Miner")
        edits = {r["entry"]: r["difficulty_entry_1"] for r in dsl["creature_template_edits"]}
        self.assertEqual(edits, mapping)  # T2: a one-column edit on each normal row
        self.assertTrue(all(r[dungeon_heroic.DERIVED] for r in rows.values()))
        self.assertTrue(any("missing from the declaration: 5003" in w for w in out.warnings), out.warnings)
        self.assertTrue(any("no heroic template for 1 critter, 1 event only, 1 npc, 1 trigger" in n
                            for n in out.notes), out.notes)

    def test_the_row(self):
        dsl, _ = _expand()
        rows = _rows(dsl)
        cookie, normal = rows[310003], TEMPLATES[645]
        for column in spell_tables.CREATURE_TEMPLATE_COLUMNS:
            if column in ("entry", "minlevel", "maxlevel", "exp", "HealthModifier", "DamageModifier", "flags_extra",
                          "AIName", "ScriptName"):
                continue
            self.assertEqual(cookie[column], normal[column], column)
        self.assertEqual((cookie["minlevel"], cookie["maxlevel"], cookie["exp"]), (60, 60, 0))
        self.assertEqual((cookie["AIName"], cookie["ScriptName"]), ("", ""))
        self.assertEqual((cookie["lootid"], cookie["KillCredit1"]), (645, 9999))
        self.assertEqual(cookie["flags_extra"], 1)  # boss: INSTANCE_BIND
        self.assertEqual(rows[310000]["flags_extra"], 0)  # trash
        self.assertEqual(cookie["HealthModifier"], HT.health_modifier(3052, 300_000))  # the boss row
        self.assertEqual(rows[310000]["HealthModifier"], HT.health_modifier(3052, 12_000))  # rank 0 normal
        self.assertEqual(rows[310006]["HealthModifier"], HT.health_modifier(3052, 300_000))  # roles= boss (rank 2)
        self.assertEqual(rows[310004]["HealthModifier"], HT.health_modifier(2136, 37_000))  # mage elite
        self.assertEqual(rows[310004]["ManaModifier"], 2)

    def test_overrides_and_tier_values(self):
        dsl, out = _expand(_source(heroic_args=(
            'tier_values={"elite": (40_000, 600)}, overrides={644: dict(health=320_000, melee=3_000), '
            '598: dict(tier="rare"), 1729: dict(columns={"speed_run": 1.4, "ArmorModifier": 2})}'
        )))
        self.assertEqual(out.errors, [])
        rows, mapping = _rows(dsl), dsl["dungeons"][0]["heroic_entries"]
        self.assertEqual(rows[mapping[644]]["HealthModifier"], HT.health_modifier(3052, 320_000))
        rz = next(r for r in out.heroic_reports if r.normal == 644)
        self.assertAlmostEqual((rz.solved.min_damage + rz.solved.max_damage) / 2, 3_000 * 3.5 / 2, delta=3)
        self.assertEqual(rows[mapping[598]]["HealthModifier"], HT.health_modifier(3052, 74_000))
        self.assertEqual(rows[mapping[5003]]["HealthModifier"], HT.health_modifier(3052, 40_000))
        self.assertEqual((rows[mapping[1729]]["speed_run"], rows[mapping[1729]]["ArmorModifier"]), (1.4, 2))
        self.assertEqual(rows[mapping[1729]]["HealthModifier"], HT.health_modifier(2136, 40_000))

    def test_override_errors(self):
        for args, text in (
            ("overrides={4075: dict(health=1)}", "overrides[4075] names a creature without a heroic template"),
            ("overrides={7: dict(health=1)}", "overrides[7] names a creature without a heroic template"),
            ('overrides={644: dict(columns={"nope": 1})}', "are not creature_template columns"),
            ('overrides={644: dict(columns={"ScriptName": "boss_x"})}', "ScriptName 'boss_x' is set"),
            ('overrides={644: dict(columns={"unit_class": 2})}', "unit_class 2 differs"),
            ('overrides={644: dict(columns={"npcflag": 1})}', "npcflag 1 differs"),
            ('overrides={644: dict(columns={"difficulty_entry_2": 9})}', "has difficulty entries of its own"),
            ('tier="tbc"', "unknown tier 'tbc'"),
        ):
            with self.subTest(args=args):
                _, out = _expand(_source(heroic_args=args))
                self.assertTrue(any(text in e for e in out.errors), out.errors)

    def test_skip_and_the_lock(self):
        dsl, _ = _expand(_source(skip=True))
        self.assertNotIn(2520, dsl["dungeons"][0]["heroic_entries"])
        lock = HT.LOCK_HEADER + "5003 310100 36 Undeclared Pirate\n"
        dsl, out = _expand(lock=lock)
        mapping = dsl["dungeons"][0]["heroic_entries"]
        self.assertEqual(mapping[5003], 310100)
        self.assertEqual(mapping[598], 310101)
        self.assertTrue(out.lock_text.startswith(lock))
        _, again = _expand(lock=out.lock_text)
        self.assertEqual(again.lock_appended, [])
        _, bad = _expand(lock="garbage\n")
        self.assertTrue(any("heroic_ids.lock line 1" in e for e in bad.errors), bad.errors)
        _, none = _expand(ids_cfg={k: v for k, v in IDS_CFG.items() if k != "creature_heroic"})
        self.assertTrue(any("no creature_heroic block" in e for e in none.errors), none.errors)

    def test_a_second_expand_replaces_its_rows(self):
        dsl, _ = _expand()
        count = len(dsl["creature_templates"])
        dungeon_heroic.expand(dsl, _live, ids_cfg=IDS_CFG, lock="")
        self.assertEqual(len(dsl["creature_templates"]), count)
        self.assertEqual(len(dsl["creature_template_edits"]), count)

    def test_boss_without_encounter_note_and_exp_warning(self):
        templates = dict(TEMPLATES)
        templates[598] = _tpl(598, "Defias Miner", rank=0, exp=2)
        _, out = _expand(live=_live(creature_templates=templates))
        self.assertTrue(any("boss role without an encounter row: 642 Sneed's Shredder, 3586 Miner Johnson" in n
                            for n in out.notes), out.notes)
        self.assertTrue(any("creature 598 -> 310000: the normal row's exp 2" in w for w in out.warnings),
                        out.warnings)

    def test_a_declared_full_row_on_a_heroic_id_is_an_error(self):
        dsl = load_dsl(_source(), ids_cfg=IDS_CFG)
        dsl = {k: list(v) if isinstance(v, list) else v for k, v in dsl.items()}
        dsl["creature_templates"].append({"entry": 310000, "id": 310000})
        out = dungeon_heroic.expand(dsl, _live, ids_cfg=IDS_CFG, lock="")
        self.assertTrue(any("declared by creature_template() and generated" in e for e in out.errors), out.errors)

    def test_a_dungeon_without_heroic_builds_nothing(self):
        dsl = load_dsl(
            'from lib.dsl.dungeon import creature, dungeon\n'
            'dungeon(36, "Deadmines", creatures=(creature(644, "Rhahk\'Zor", "boss", spawns=1),))\n',
            ids_cfg=IDS_CFG,
        )
        out = dungeon_heroic.expand(dsl, lambda: self.fail("no live load without a heroic"), ids_cfg=IDS_CFG,
                                    lock="")
        self.assertEqual((dsl["creature_templates"], out.errors), ([], []))


class RetireTest(unittest.TestCase):
    """A shipped heroic creature (a lock line) that leaves the entry set: an ERROR unless retired=."""

    LOCK = HT.LOCK_HEADER + "2520 310200 36 Remote-Controlled Golem\n"

    def _retired_source(self, entries="2520"):
        return _source(skip=True).replace("skip=(2520,) if True else (),", f"retired=({entries},),")

    def test_leaving_the_set_is_an_error_naming_the_reason(self):
        dsl, out = _expand(_source(skip=True), lock=self.LOCK)
        errors = [e for e in out.errors if "creature 2520" in e]
        self.assertEqual(len(errors), 1, out.errors)
        self.assertIn("shipped heroic entry 310200", errors[0])
        self.assertIn("left the heroic entry set (skip=)", errors[0])
        self.assertIn("retired=(2520,)", errors[0])
        self.assertNotIn(2520, dsl["dungeons"][0]["heroic_entries"])
        # a role change and a creature gone from the map name their own reasons
        source = _source().replace('roles={642: "boss", 3586: "boss"}',
                                   'roles={642: "boss", 3586: "boss", 2520: "npc"}')
        _, out = _expand(source, lock=self.LOCK)
        self.assertTrue(any("creature 2520" in e and "set (npc)" in e for e in out.errors), out.errors)
        _, out = _expand(lock=self.LOCK + "7777 310201 36 Gone\n")
        self.assertTrue(any("creature 7777" in e and "no longer declared, spawned on the map" in e
                            for e in out.errors), out.errors)
        # a lock line of another map (no declared heroic) is not this dungeon's business
        _, out = _expand(lock=self.LOCK.replace(" 36 ", " 33 "))
        self.assertFalse(any("creature 2520" in e for e in out.errors), out.errors)

    def test_retired_reverts_the_link_and_stops_the_copies(self):
        templates = dict(TEMPLATES)
        templates[2520] = _tpl(2520, "Remote-Controlled Golem", difficulty_entry_1=310200)
        dsl, out = _expand(self._retired_source(), lock=self.LOCK, live=_live(creature_templates=templates))
        self.assertEqual(out.errors, [])
        self.assertNotIn(2520, dsl["dungeons"][0]["heroic_entries"])
        self.assertEqual(out.retire_blocks, [
            "-- Deadmines (map 36) heroic: 1 retired heroic creature(s) lose their difficulty link "
            "(dungeon(retired=...))\n"
            "UPDATE `creature_template` SET `difficulty_entry_1` = 0 WHERE `entry` = 2520 AND "
            "`difficulty_entry_1` = 310200;"
        ])
        self.assertFalse(any(_int_of(r, "CreatureID") == 310200 for r in dsl["creature_template_models"]))
        self.assertNotIn(2520, {int(r["entry"]) for r in dsl["creature_template_edits"]})
        self.assertNotIn(310200, _rows(dsl))
        self.assertNotIn("310200", out.lock_text.replace(self.LOCK, ""))  # the line stays, nothing new for it
        self.assertTrue(out.lock_text.startswith(self.LOCK))
        done = codestyle_sql(out.retire_blocks[0])
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        # the replay applies the guard: only a row still pointing at the heroic entry is cleared
        replay = {(2520,): dict(templates[2520]), (2521,): _tpl(2521, difficulty_entry_1=310201)}
        sql = out.retire_blocks[0] + "\nUPDATE `creature_template` SET `difficulty_entry_1` = 0 WHERE `entry` = 2521 " \
            "AND `difficulty_entry_1` = 310200;"
        sql_dump.apply_composite_key_statements(replay, spell_tables.CREATURE_TEMPLATE_COLUMNS, ("entry",),
                                                "creature_template", sql)
        self.assertEqual({k: r["difficulty_entry_1"] for k, r in replay.items()}, {(2520,): 0, (2521,): 310201})
        # once the revert is live, nothing more to emit
        templates[2520] = replay[(2520,)]
        _, again = _expand(self._retired_source(), lock=self.LOCK, live=_live(creature_templates=templates))
        self.assertEqual((again.errors, again.retire_blocks), ([], []))

    def test_retired_without_a_lock_line_is_an_error(self):
        _, out = _expand(self._retired_source("2520, 598"), lock=self.LOCK)
        self.assertTrue(any("retired= names creature 598" in e and "use skip= instead" in e for e in out.errors),
                        out.errors)
        self.assertNotIn(598, _expand(self._retired_source("2520, 598"), lock=self.LOCK)[0]["dungeons"][0][
            "heroic_entries"])


class ModelLintTest(unittest.TestCase):
    def test_a_heroic_entry_without_a_model_row_is_an_error(self):
        side_rows = {"creature_template_model": [r for r in SIDE_ROWS["creature_template_model"]
                                                 if r["CreatureID"] != 1729]}
        dsl, out = _expand(live=_live(side_rows=side_rows))
        heroic_entry = dsl["dungeons"][0]["heroic_entries"][1729]
        self.assertEqual([e for e in out.errors if "creature_template_model" in e], [
            f"dungeon(36) creature 1729 -> heroic {heroic_entry}: no creature_template_model row for the heroic entry "
            f"(the normal entry has none to copy) - Creature::InitEntry refuses to load it, so its heroic spawns are "
            f"empty"
        ])


class DeclaredKitAddTest(unittest.TestCase):
    """A creature this run declares with creature_template() (a boss-kit add, Deadmines Pilot WP-K) and lists in
    `extra=` gets its heroic template, override and model copy in the same run (dungeon_heroic.with_declared_templates),
    not only once its upsert reached the SQL on disk. Its full row carries difficulty_entry_1 itself."""

    KIT = 300420
    HEROIC = 310008     # after the eight creatures of SOURCE, the lock being empty

    def _source(self):
        return _source(heroic_args="overrides={300420: dict(health=80_000)}").replace(
            "skip=(2520,) if False else (),",
            'skip=(2520,) if False else (), extra=(creature(300420, "Watchman", "trash"),),',
        )

    def _expand(self, difficulty_entry_1):
        dsl = load_dsl(self._source(), ids_cfg=IDS_CFG)
        dsl = {k: list(v) if isinstance(v, list) else v for k, v in dsl.items()}
        dsl["creature_templates"].append({**_tpl(self.KIT, "Watchman", AIName="", ScriptName="npc_dm_watchman"),
                                          "id": self.KIT, "difficulty_entry_1": difficulty_entry_1})
        dsl["creature_template_models"].append({"id": f"{self.KIT}:0", "CreatureID": self.KIT, "Idx": 0,
                                                "CreatureDisplayID": 184, "DisplayScale": 1.0, "Probability": 1.0,
                                                "VerifiedBuild": 0})
        out = dungeon_heroic.expand(dsl, _live, ids_cfg=IDS_CFG, lock="")
        return dsl, out

    def test_same_run_heroic_template(self):
        dsl, out = self._expand(self.HEROIC)
        self.assertEqual(out.errors, [])
        mapping = dsl["dungeons"][0]["heroic_entries"]
        self.assertEqual(mapping[self.KIT], self.HEROIC)
        self.assertIn(f"{self.KIT} {self.HEROIC} 36 Watchman", out.lock_appended)
        row = _rows(dsl)[self.HEROIC]
        self.assertTrue(row[dungeon_heroic.DERIVED])
        self.assertEqual((row["minlevel"], row["ScriptName"]), (60, ""))
        self.assertEqual(row["HealthModifier"], HT.health_modifier(3052, 80_000))
        models = [r for r in dsl["creature_template_models"] if r["CreatureID"] == self.HEROIC]
        self.assertEqual([(r["CreatureDisplayID"], r[dungeon_heroic.DERIVED]) for r in models], [(184, True)])
        # the declared full row owns difficulty_entry_1: no one-column edit for it
        self.assertNotIn(self.KIT, {r["entry"] for r in dsl["creature_template_edits"]})

    def test_the_full_row_must_name_its_heroic_entry(self):
        _, out = self._expand(0)
        self.assertTrue(any(f"creature {self.KIT} -> heroic {self.HEROIC}" in e and "declares the full row" in e
                            for e in out.errors), out.errors)

    def test_without_the_declaration_it_waits_for_the_live_row(self):
        dsl = load_dsl(self._source(), ids_cfg=IDS_CFG)
        dsl = {k: list(v) if isinstance(v, list) else v for k, v in dsl.items()}
        out = dungeon_heroic.expand(dsl, _live, ids_cfg=IDS_CFG, lock="")
        self.assertTrue(any("overrides[300420] names a creature without a heroic template (no live creature_template "
                            "row)" in e for e in out.errors), out.errors)

    def test_a_declared_model_row_replaces_the_replayed_one_by_key(self):
        live = dungeon_heroic.LiveWorld(creature_templates={}, side_rows={"creature_template_model": [
            {"CreatureID": 7, "Idx": 0, "CreatureDisplayID": 1, "DisplayScale": 1, "Probability": 1},
            {"CreatureID": 7, "Idx": 1, "CreatureDisplayID": 2, "DisplayScale": 1, "Probability": 1},
        ]})
        mine = {"id": "7:1", "CreatureID": 7, "Idx": 1, "CreatureDisplayID": 9, "DisplayScale": 1.0,
                "Probability": 1.0, "VerifiedBuild": 0}
        copies = dungeon_heroic.side_table_copies({36: {7: 310500}}, live, {"creature_template_models": [mine]})
        models = sorted((r["Idx"], r["CreatureDisplayID"]) for r in copies["creature_template_models"])
        self.assertEqual(models, [(0, 1), (1, 9)])


def _int_of(row: dict, column: str) -> int:
    return int(row.get(column) or 0)


class SmartAndSpellTest(unittest.TestCase):
    SMART = [
        # Rhahk'Zor: two normal-only rows (one with NOT_REPEATABLE) and an unmasked one
        {"entryorguid": 644, "source_type": 0, "id": 0, "link": 0, "event_flags": 2, "action_type": 11,
         "action_param1": 6304},
        {"entryorguid": 644, "source_type": 0, "id": 1, "link": 0, "event_flags": 3, "action_type": 1,
         "action_param1": 0},
        {"entryorguid": 644, "source_type": 0, "id": 2, "link": 0, "event_flags": 0, "action_type": 11,
         "action_param1": 12167},
        # Cookie: a per-difficulty script (normal and heroic rows) is left alone
        {"entryorguid": 645, "source_type": 0, "id": 0, "link": 0, "event_flags": 2, "action_type": 11,
         "action_param1": 1},
        {"entryorguid": 645, "source_type": 0, "id": 1, "link": 0, "event_flags": 4, "action_type": 11,
         "action_param1": 2},
        # a guid script of a spawn on the map and a gameobject script
        {"entryorguid": -3, "source_type": 0, "id": 0, "link": 0, "event_flags": 2, "action_type": 1,
         "action_param1": 0},
        {"entryorguid": 16398, "source_type": 1, "id": 0, "link": 0, "event_flags": 2, "action_type": 1,
         "action_param1": 0},
        # a creature of another dungeon
        {"entryorguid": 9016, "source_type": 0, "id": 0, "link": 0, "event_flags": 2, "action_type": 1,
         "action_param1": 0},
    ]
    DIFFICULTY = {
        1: {"ID": 1, "DifficultySpellID_1": 12167, "DifficultySpellID_2": 59863, "DifficultySpellID_3": 0,
            "DifficultySpellID_4": 0},
        2: {"ID": 2, "DifficultySpellID_1": 6304, "DifficultySpellID_2": 0, "DifficultySpellID_3": 0,
            "DifficultySpellID_4": 0},  # slot 2 empty: not in the searcher
    }

    def test_widen_and_spell_swaps(self):
        _, out = _expand(live=_live(smart_scripts=self.SMART, spell_difficulty=self.DIFFICULTY))
        self.assertEqual(len(out.smart_blocks), 1)
        block = out.smart_blocks[0]
        self.assertIn("4 normal-only SmartAI row(s)", block)
        self.assertIn("(`entryorguid` = 644 AND `source_type` = 0 AND `id` = 1 AND `link` = 0 AND `event_flags` = 3)",
                      block)
        self.assertIn("`entryorguid` = -3 AND", block)
        self.assertIn("`entryorguid` = 16398 AND `source_type` = 1", block)
        self.assertNotIn("645", block)
        self.assertNotIn("9016", block)
        self.assertTrue(any("left alone in scripts with their own heroic rows: [(645, 0)]" in n for n in out.notes))
        self.assertTrue(any("1 creature spell(s) swap to another spell on heroic" in n and "12167 -> 59863" in n
                            for n in out.notes), out.notes)
        done = codestyle_sql(block)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_the_widening_converges(self):
        widen, _ = HT.normal_only_rows(self.SMART, {(644, 0)})
        sql = HT.render_smart_widen("t", widen)
        rows = {(r["entryorguid"], r["source_type"], r["id"], r["link"]): dict(r) for r in self.SMART}
        sql_dump.apply_composite_key_statements(
            rows, tuple(self.SMART[0]), ("entryorguid", "source_type", "id", "link"), "smart_scripts", sql,
        )
        self.assertEqual([rows[(644, 0, i, 0)]["event_flags"] for i in range(3)], [6, 7, 0])
        self.assertEqual(HT.normal_only_rows(list(rows.values()), {(644, 0)}), ([], []))

    def test_widening_off_warns(self):
        _, out = _expand(_source(heroic_args="widen_smart_scripts=False"), live=_live(smart_scripts=self.SMART))
        self.assertEqual(out.smart_blocks, [])
        self.assertTrue(any("never run on heroic (widen_smart_scripts=False)" in w for w in out.warnings))

    def test_spell_difficulty_searcher(self):
        rows = {**self.DIFFICULTY, 3: {"ID": 3, "DifficultySpellID_1": 12167, "DifficultySpellID_2": 70000,
                                       "DifficultySpellID_3": 0, "DifficultySpellID_4": 0}}
        self.assertEqual(HT.heroic_swaps({12167, 6304, 59863, 1}, rows), {12167: 70000})  # later rows win
        _, out = _expand(live=_live(spell_difficulty=None))
        self.assertTrue(any("spell swap check was skipped" in n for n in out.notes))


class RenderTest(unittest.TestCase):
    def test_render_codestyle_and_convergence(self):
        dsl, _ = _expand()
        live_normal = [dict(r) for r in TEMPLATES.values()]
        # the heroic model copies as already live, so the render is the creature_template block alone
        models = [{c: r[c] for c in spell_tables.CREATURE_TEMPLATE_MODEL_COLUMNS}
                  for r in dsl["creature_template_models"]]

        def index(live):
            return spell_tables.SpellTableIndex(
                {"creature_template": live, "creature_template_model": models},
                emitted={t.name: [] for t in spell_tables.CREATURE_TABLES},
                base={t.name: [] for t in spell_tables.CREATURE_TABLES}, tables=spell_tables.CREATURE_TABLES,
            )

        blocks = spell_tables.render_creature_blocks(index(live_normal), dsl)
        self.assertEqual(len(blocks), 1)
        sql = blocks[0]
        self.assertIn("ON DUPLICATE KEY UPDATE", sql)
        updates = [line for line in sql.splitlines() if line.startswith("UPDATE")]
        self.assertEqual(len(updates), 8)
        self.assertTrue(all("SET `difficulty_entry_1` = " in line for line in updates))  # nothing else on normal rows
        done = codestyle_sql(sql)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        heroic = read_back(sql, "creature_template", spell_tables.CREATURE_TEMPLATE_COLUMNS)
        self.assertEqual(len(heroic), 8)
        rows = {(int(r["entry"]),): r for r in live_normal}
        sql_dump.apply_composite_key_statements(rows, spell_tables.CREATURE_TEMPLATE_COLUMNS, ("entry",),
                                                "creature_template", sql)
        self.assertEqual(spell_tables.render_creature_blocks(index([*rows.values(), *heroic]), dsl), [])


class DeadminesTest(unittest.TestCase):
    """The real declaration against the live replay and the committed lock file."""

    @classmethod
    def setUpClass(cls):
        sqlcorpus.activate(generate.CACHE_DIR, generate.cache_code_version())
        try:
            from lib import source  # noqa: PLC0415 - needs ruamel (the venv)

            ids_cfg = source.load_ids(generate.SOURCE_DIR / "ids.yaml")
            creature_index = spell_tables.load_creature_table_index()
            existing = {int(r["entry"]): r for r in creature_index.live_rows("creature_template")}
            cls.dsl = {
                k: list(v) if isinstance(v, list) else v for k, v in registry.load_classes_dir(
                    generate.SOURCE_DIR / "world" / "dungeons", ids_cfg=ids_cfg, existing_creature_rows=existing,
                    creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS, live_data={},
                ).items()
            }
            # The Deadmines Pilot's boss package (source/npcs/deadmines/): the boss-kit adds in deadmines.py's extra=
            kit = registry.load_class_package(
                generate.SOURCE_DIR / "npcs" / "deadmines", ids_cfg=ids_cfg, existing_creature_rows=existing,
                creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
                creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
            )
            for key in ("creature_templates", "creature_template_models", "creature_template_edits"):
                cls.dsl[key] = cls.dsl.get(key, []) + list(getattr(kit, key))
            # This class checks the Deadmines' expansion: the other dungeons' heroics (Shadowfang Keep's, WP-H) have
            # their own tests and, until their scoped write run, lock lines that are not committed yet.
            cls.declared = list(cls.dsl["dungeons"])
            cls.dsl["dungeons"] = [e if e["map_id"] == 36 else dict(e, heroic=None) for e in cls.dsl["dungeons"]]
            cls.index = spell_tables.load_spell_table_index()
            cls.out = dungeon_heroic.expand(
                cls.dsl, lambda: dungeon_heroic.load_live_world(existing, cls.index), ids_cfg=ids_cfg,
            )
            cls.creature_index = creature_index
        finally:
            sqlcorpus.deactivate()

    def test_nineteen_declarations_and_the_heroic_ones(self):
        from lib import dungeon_extract  # noqa: PLC0415

        maps = {e["map_id"]: e for e in self.declared}
        self.assertEqual(set(maps), set(dungeon_extract.VANILLA_DUNGEONS))
        # Deadmines (E1), Shadowfang Keep and Scholomance (their WP-H); Stratholme joins in its turn
        self.assertEqual(sorted(m for m, e in maps.items() if e["heroic"]), [33, 36, 289])
        self.assertTrue(all(e["creatures"] for e in maps.values()))

    def test_clean_with_the_committed_lock(self):
        self.assertEqual((self.out.errors, self.out.warnings), ([], []))
        self.assertEqual(self.out.lock_appended, [])
        lock = HT.parse_lock(HT.LOCK_PATH.read_text())
        mapping = next(e for e in self.dsl["dungeons"] if e["map_id"] == 36)["heroic_entries"]
        self.assertEqual(mapping, lock.pairs)
        self.assertEqual(len(mapping), 29)  # E2's 25 plus the Deadmines Pilot's 4 boss-kit combat adds
        self.assertEqual({e: mapping[e] for e in (300420, 300421, 300422, 300426)},
                         {300420: 310025, 300421: 310026, 300422: 310027, 300426: 310028})
        self.assertNotIn(4075, mapping)  # the rat, a critter
        self.assertTrue({643, 2520, 3450, 4417, 1732} <= set(mapping))  # summoned or summoned-and-spawned

    def test_bosses_and_overrides(self):
        reports = {r.normal: r for r in self.out.heroic_reports}
        for entry, health in ((639, 340_000), (642, 220_000), (643, 142_000), (644, 320_000), (645, 330_000),
                              (646, 472_000), (647, 377_000), (1763, 311_000), (3586, 240_000)):
            with self.subTest(entry=entry):
                self.assertEqual(reports[entry].role, "boss")
                self.assertEqual(reports[entry].solved.health, health)
        rows = _rows(self.dsl)
        self.assertEqual({e for e, r in rows.items() if int(r["flags_extra"]) & 1},
                         {reports[e].heroic for e in (639, 642, 643, 644, 645, 646, 647, 1763, 3586)})
        self.assertEqual(reports[622].solved.health, 37_000)  # elite trash
        self.assertEqual(reports[598].solved.health, 12_000)  # normal trash

    def test_normal_rows_only_get_difficulty_entry_1(self):
        # E2 writes only difficulty_entry_1 on a stock normal row. The Deadmines Pilot's boss package
        # (source/npcs/deadmines/) also owns ScriptName, AIName, HealthModifier and CreatureImmunitiesId of the reworked
        # bosses, and declares its boss-kit creatures (300420-300449) as full rows.
        pilot_columns = {"ScriptName", "AIName", "HealthModifier", "CreatureImmunitiesId"}
        bosses = {639, 642, 643, 644, 645, 646, 647, 1763, 3586}
        blocks = spell_tables.render_creature_blocks(self.creature_index, self.dsl)
        sql = "\n".join(blocks)
        for line in sql.splitlines():
            if line.startswith("UPDATE"):
                match = re.match(r"^UPDATE `creature_template` SET (.*) WHERE `entry` IN \(([\d, ]+)\);$", line)
                self.assertIsNotNone(match, line)
                columns = set(re.findall(r"`(\w+)` = ", match.group(1)))
                entries = {int(e) for e in match.group(2).split(",")}
                if columns == {"difficulty_entry_1"}:
                    self.assertRegex(line, r"`difficulty_entry_1` = 3100\d\d WHERE")
                else:
                    self.assertTrue(columns <= pilot_columns | {"difficulty_entry_1"}, line)
                    self.assertTrue(entries <= bosses, line)
            elif line.startswith("("):
                self.assertRegex(line, r"^\((3100\d\d|3004[2-4]\d), ")


if __name__ == "__main__":
    unittest.main()
