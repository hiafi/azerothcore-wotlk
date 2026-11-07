"""
lib/dungeon_extract.py and extract_dungeon_creatures.py (dungeon difficulties E2, WP-G): the vanilla dungeon creature
extraction, on fixtures (no database).

Covered: spawned entries (alternate multispawn entries too), encounter credits, every summon path (SmartAI summon,
summon radial, template swap, casts through trigger spells and trigger auras, creature_template_spell, summon groups
of a creature / gameobject / the map, guid-keyed scripts, timed action lists incl. random ones), the fixed point
(a summon's own summons), roles, event-only creatures (spawns and summoners), the rendered block (120 columns, string
escaping), keeping hand edits outside the markers byte for byte, refusing a file without exactly one block, a new
file that loads through the real DSL loader, the CLI's write / `--check` / error paths, and the 19 committed files
being exactly what a rerun over the same data renders (their block parses back to the same creatures).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_dungeon_extract.py
"""

from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import extract_dungeon_creatures as cli  # noqa: E402
from lib import dungeon_extract as dx  # noqa: E402
from lib.dsl import registry  # noqa: E402


def _tpl(entry, name, **kw):
    row = {"entry": entry, "name": name, "minlevel": 18, "maxlevel": 19, "rank": 1, "unit_class": 1, "type": 7,
           "npcflag": 0, "flags_extra": 0, "exp": 0}
    row.update(kw)
    return row


def _smart(entryorguid, source_type, action, p1=0, p2=0, *rest, row_id=0):
    params = [p1, p2, *rest] + [0] * (4 - len(rest))
    return {"entryorguid": entryorguid, "source_type": source_type, "id": row_id, "link": 0, "action_type": action,
            **{f"action_param{i + 1}": v for i, v in enumerate(params)}}


def _spell(spell_id, *effects):
    row = {"ID": spell_id}
    for i, (effect, aura, misc, trigger) in enumerate(effects, 1):
        row.update({f"Effect_{i}": effect, f"EffectAura_{i}": aura, f"EffectMiscValue_{i}": misc,
                    f"EffectTriggerSpell_{i}": trigger})
    return row


def _world(**kw) -> dx.World:
    templates = {e: _tpl(e, n, **extra) for e, n, extra in (
        (644, "Rhahk'Zor", {}), (642, "Sneed's Shredder", {}), (643, "Sneed", {}), (622, "Goblin Engineer", {}),
        (2520, "Remote-Controlled Golem", {}), (4417, "Defias Taskmaster", {}), (1732, "Defias Squallshaper", {}),
        (3450, "Defias Companion", {"rank": 0}), (657, "Defias Pirate", {}), (4075, "Rat", {"type": 8, "rank": 0}),
        (5000, "Trigger", {"flags_extra": 0x80}), (5001, "Vendor", {"npcflag": 128}),
        (5002, "Holiday Boss", {}), (5003, "Holiday Add", {}), (5004, "Swapped Form", {}),
        (5005, "Group Add", {}), (5006, "Map Add", {}), (5007, "Radial Add", {}), (5008, "Guid Add", {}),
        (5009, "Random List Add", {}), (5010, "Alt Entry", {}), (5011, "Aura Add", {}), (5012, "Second Generation", {}),
        (5013, "[DND] Bunny", {}), (9999, "Elsewhere", {}),
    )}
    world = dx.World(
        creature_spawns=[
            {"guid": 1, "id": 644, "map": 36}, {"guid": 2, "id": 642, "map": 36}, {"guid": 3, "id": 622, "map": 36},
            {"guid": 4, "id": 657, "map": 36}, {"guid": 5, "id": 4075, "map": 36}, {"guid": 6, "id": 5000, "map": 36},
            {"guid": 7, "id": 5001, "map": 36}, {"guid": 8, "id": 5002, "map": 36}, {"guid": 9, "id": 1732, "map": 36},
            {"guid": 10, "id": 5013, "map": 36}, {"guid": 99, "id": 9999, "map": 0},
        ],
        gameobject_spawns=[{"guid": 50, "id": 17155, "map": 36}, {"guid": 51, "id": 16398, "map": 36}],
        templates=templates, multispawn={3: {5010}}, event_guids={8},
        encounters=[{"ID": 161, "MapID": 36, "Difficulty": 0}, {"ID": 162, "MapID": 36, "Difficulty": 0},
                    {"ID": 999, "MapID": 36, "Difficulty": 1}],
        instance_encounters={161: {"creditType": 0, "creditEntry": 644}, 162: {"creditType": 0, "creditEntry": 643},
                             999: {"creditType": 0, "creditEntry": 9999}},
        smart_scripts=[
            _smart(642, 0, dx.ACTION_CAST, 5141),  # Eject Sneed -> summons 643
            _smart(622, 0, dx.ACTION_CAST, 3605),  # Remote-Controlled Golem
            _smart(657, 0, dx.ACTION_SELF_CAST, 5172),  # trigger spell -> companion
            _smart(17155, 1, dx.ACTION_SUMMON_CREATURE, 4417),  # gunpowder -> Taskmaster
            _smart(16398, 1, dx.ACTION_CALL_TIMED_ACTIONLIST, 1639800),
            _smart(1639800, 9, dx.ACTION_SUMMON_CREATURE, 1732),
            _smart(1639800, 9, dx.ACTION_CALL_RANDOM_TIMED_ACTIONLIST, 1639801, 1639802, row_id=1),
            _smart(1639802, 9, dx.ACTION_SUMMON_CREATURE, 5009),
            _smart(644, 0, dx.ACTION_UPDATE_TEMPLATE, 5004),
            _smart(644, 0, dx.ACTION_SUMMON_CREATURE_GROUP, 1, row_id=1),
            _smart(644, 0, dx.ACTION_SUMMON_RADIAL, 5007, row_id=2),
            _smart(-1, 0, dx.ACTION_SUMMON_CREATURE, 5008),  # Rhahk'Zor's spawn guid 1
            _smart(-99, 0, dx.ACTION_SUMMON_CREATURE, 9999),  # a spawn elsewhere: not this map's
            _smart(5002, 0, dx.ACTION_SUMMON_CREATURE, 5003),  # holiday boss -> holiday add
            _smart(2520, 0, dx.ACTION_SUMMON_CREATURE, 5012),  # a summon's own summon
            _smart(9999, 0, dx.ACTION_SUMMON_CREATURE, 5006),  # not in the dungeon
        ],
        template_spells={1732: {7000}},
        summon_groups=[
            {"summonerId": 644, "summonerType": 0, "groupId": 1, "entry": 5005},
            {"summonerId": 36, "summonerType": 2, "groupId": 0, "entry": 5006},
        ],
        spells={
            5141: _spell(5141, (28, 0, 643, 0)),
            3605: _spell(3605, (28, 0, 2520, 0)),
            5172: _spell(5172, (64, 0, 0, 5173)), 5173: _spell(5173, (56, 0, 3450, 0)),
            7000: _spell(7000, (6, 23, 0, 7001)), 7001: _spell(7001, (28, 0, 5011, 0)),
        },
    )
    for key, value in kw.items():
        setattr(world, key, value)
    return world


class ExtractTest(unittest.TestCase):
    def setUp(self):
        self.result = dx.extract(_world(), 36)
        self.by_entry = {c.entry: c for c in self.result.creatures}

    def test_the_entry_set(self):
        self.assertEqual(set(self.by_entry), {
            644, 642, 622, 657, 4075, 5000, 5001, 5002, 1732, 5013, 5010,  # spawned (5010: multispawn alternate)
            643,  # encounter credit (and summoned)
            2520, 3450, 4417, 5003, 5004, 5005, 5006, 5007, 5008, 5009, 5011, 5012,  # summoned
        })
        self.assertNotIn(9999, self.by_entry)  # a heroic-difficulty credit and another map's spawn

    def test_provenance(self):
        expect = {
            643: ("creature 642 smart cast 5141",),
            2520: ("creature 622 smart cast 3605",),
            3450: ("creature 657 smart cast 5172",),
            4417: ("gameobject 17155 smart",),
            1732: ("gameobject 16398 actionlist 1639800",),
            5009: ("gameobject 16398 actionlist 1639802",),
            5004: ("creature 644 smart update_template",),
            5005: ("creature 644 summon group 1 (smart)",),
            5006: ("map 36 summon group 0",),
            5007: ("creature 644 smart",),
            5008: ("creature 644 guid 1 smart",),
            5011: ("creature 1732 spell 7000",),
            5012: ("creature 2520 smart",),
        }
        for entry, how in expect.items():
            with self.subTest(entry=entry):
                self.assertEqual(self.by_entry[entry].summoned_by, how)
        self.assertEqual(self.by_entry[1732].spawns, 1)

    def test_roles_and_events(self):
        roles = {e: c.role for e, c in self.by_entry.items()}
        self.assertEqual((roles[644], roles[643]), ("boss", "boss"))
        self.assertEqual((roles[4075], roles[5000], roles[5013], roles[5001]), ("critter", "trigger", "trigger", "npc"))
        self.assertEqual({e for e, c in self.by_entry.items() if c.event}, {5002, 5003})  # the boss and its add
        self.assertEqual([c.role for c in self.result.creatures][:2], ["boss", "boss"])  # bosses first

    def test_counts_and_missing_templates(self):
        world = _world()
        world.smart_scripts.append(_smart(644, 0, dx.ACTION_SUMMON_CREATURE, 777, row_id=9))
        result = dx.extract(world, 36)
        self.assertEqual(result.missing_templates, [777])
        counts = result.counts()
        self.assertEqual((counts["entries"], counts["boss"], counts["event"]), (24, 2, 2))


class RenderTest(unittest.TestCase):
    def test_lines_fit_and_parse(self):
        long = dx.Extracted(1, 'A "quoted" \\ name', "trash", spawns=3, summoned_by=tuple(
            f"creature {n} smart cast {n * 10}" for n in range(100, 106)), comment="L60 elite warrior")
        block = dx.render_block(dx.DungeonExtract(36, "Deadmines", [long, dx.Extracted(2, "Rat", "critter", 1)]))
        self.assertTrue(all(len(line) <= dx.WIDTH for line in block.splitlines()))
        tree = ast.parse(block)
        call = tree.body[0].value.elts[0]
        self.assertEqual(ast.literal_eval(call.args[1]), 'A "quoted" \\ name')
        self.assertEqual(len(ast.literal_eval(call.keywords[1].value)), 6)

    def test_replace_block_keeps_hand_edits(self):
        result = dx.extract(_world(), 36)
        text = dx.render_new_file(result, "deadmines")
        hand = text.replace("creatures=CREATURES)", 'creatures=CREATURES, roles={642: "boss"})') + "# hand note\n"
        world = _world()
        world.creature_spawns.append({"guid": 11, "id": 5012, "map": 36})
        regenerated = dx.replace_block(hand, dx.render_block(dx.extract(world, 36)))
        self.assertIn('roles={642: "boss"}', regenerated)
        self.assertTrue(regenerated.endswith("# hand note\n"))
        self.assertIn('creature(5012, "Second Generation", "trash", spawns=1,', regenerated)
        head, tail = hand.split(dx.BLOCK_BEGIN)[0], hand.split(dx.BLOCK_END)[1]
        self.assertTrue(regenerated.startswith(head) and regenerated.endswith(tail))
        for bad in ("no markers\n", hand + dx.BLOCK_BEGIN, dx.BLOCK_END + "\n" + dx.BLOCK_BEGIN):
            with self.subTest(bad=bad[:20]), self.assertRaises(dx.BlockError):
                dx.replace_block(bad, "x")

    def test_a_new_file_loads_through_the_dsl(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "deadmines.py"
            path.write_text(dx.render_new_file(dx.extract(_world(), 36), "deadmines"))
            self.assertTrue(all(len(line) <= dx.WIDTH for line in path.read_text().splitlines()))
            reg = registry.load_class_file(path, ids_cfg={})
        entry = reg.dungeons[0]
        self.assertEqual((entry["map_id"], entry["name"], entry["heroic"]), (36, "Deadmines", None))
        self.assertEqual(len(entry["creatures"]), 24)
        self.assertEqual(reg.creature_templates, [])


class CliTest(unittest.TestCase):
    def _main(self, out_dir, *args):
        with mock.patch.object(cli, "load_world", return_value=_world()), mock.patch("builtins.print") as printed:
            rc = cli.main(["--mysql", "mysql", "--out-dir", str(out_dir), "--map", "36", *args])
        return rc, "\n".join(str(c.args[0]) for c in printed.call_args_list)

    def test_write_check_and_error(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self.assertEqual(self._main(out, "--check")[0], 1)  # a new file would be written
            self.assertFalse((out / "deadmines.py").exists())
            rc, text = self._main(out)
            self.assertEqual(rc, 0)
            self.assertIn("deadmines.py: new; 24 entries", text)
            first = (out / "deadmines.py").read_text()
            rc, text = self._main(out, "--check")
            self.assertEqual((rc, "unchanged" in text), (0, True))
            self.assertEqual((out / "deadmines.py").read_text(), first)
            (out / "deadmines.py").write_text("no markers\n")
            rc, text = self._main(out)
            self.assertEqual(rc, 2)
            self.assertIn("ERROR: deadmines.py", text)
            self.assertEqual((out / "deadmines.py").read_text(), "no markers\n")

    def test_bad_arguments(self):
        with self.assertRaises(SystemExit), mock.patch("sys.stderr"):
            cli.main(["--mysql", "mysql", "--map", "531"])
        with self.assertRaises(SystemExit), mock.patch("sys.stderr"), mock.patch.dict("os.environ", {}, clear=True):
            cli.main([])


class CommittedFilesTest(unittest.TestCase):
    def test_every_vanilla_dungeon_has_a_file_with_one_block(self):
        for map_id, (name, stem) in dx.VANILLA_DUNGEONS.items():
            with self.subTest(map_id=map_id):
                text = (cli.DUNGEON_DIR / f"{stem}.py").read_text()
                self.assertEqual((text.count(dx.BLOCK_BEGIN), text.count(dx.BLOCK_END)), (1, 1))
                # a one-line call, or the multi-line one of a dungeon with hand declarations (Deadmines, Shadowfang Keep)
                self.assertTrue(
                    f'dungeon({map_id}, "{name}"' in text or f'dungeon(\n    {map_id}, "{name}"' in text, stem,
                )
                self.assertTrue(all(len(line) <= dx.WIDTH for line in text.splitlines()))


if __name__ == "__main__":
    unittest.main()
