"""
source/ids.yaml's tool-wide client-patch blocks and per-class reservations (shaman-rework T1, step 1).

Checks, from the file itself and from the class sources:
  - every block is a {start, end} pair, and blocks that feed the same table do not overlap;
  - every per-class reservation sits inside the block of the same name, and no two classes' reservations overlap;
  - every custom id a class declares (spell, talent, SkillLineAbility, spell_group, tooltip variable, creature)
    that falls inside a tool-wide block is inside that class's reservation. Shaman and Death Knight reserve slices
    (the shaman spike's 202760-202779, 300298/300299 and 1270, and the Death Knight P0 spike's 203680-203699, 1285,
    30779 and 300339, are inside theirs);
  - a non-class owner reserves under its project name (`healsim`: spells 202900-202909, declared from source/npcs),
    so the overlap test keeps every class out of its ids.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_id_blocks.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfmt, source, spell_tables, state  # noqa: E402
from lib.dsl import registry  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
RESERVATIONS = IDS.get("reservations") or {}
BLOCKS = {name: cfg for name, cfg in IDS.items() if name != "reservations"}

# Blocks that hold ids of one underlying table. Everything else in the file is a table of its own.
SAME_TABLE_BLOCKS = {
    "creature_template": ("creature", "npc_tools"),
    "talent_dbc": ("talent",),
    "talenttab_dbc": ("talenttab",),
}

# Ids the display tables already use, from the shaman T0a report s1 (2026-10-18): build_patch_f.py writes its rows from
# a dict, not named constants, so they cannot be scanned like the rest.
USED_DISPLAY_IDS = {
    "creaturedisplayinfo": (90001, 90321),
    "creaturemodeldata": (90001, 90310),
    "gameobjectdisplayinfo": (90001, 90001),
}
# name prefix of a module-level int constant -> the ids.yaml block it mints from. SOUND_* in the druid / priest
# scripts also names stock sound ids (3087, ...), so only values in the custom 90000s count.
CONSTANT_BLOCKS = {"ICON": "spellicon", "SOUND": "soundentries", "EFFECT": "spellvisual", "KIT": "spellvisual",
                   "SV": "spellvisual"}


def scanned_used_ids() -> dict[str, list[tuple[int, str]]]:
    """Every custom (90000-90999) id the patch scripts name as a module-level constant, by block: the scan keeps the
    test from going stale when a script mints a new id (a hard-coded maximum would not notice)."""
    import ast

    found: dict[str, list[tuple[int, str]]] = {}
    scripts = [TOOL_ROOT / "build_patch_i.py", *sorted(TOOL_ROOT.glob("patch_*_vfx_models.py"))]
    for path in scripts:
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if not (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
                continue
            name, value = node.targets[0].id, node.value
            block = CONSTANT_BLOCKS.get(name.split("_")[0])
            is_int = isinstance(value, ast.Constant) and isinstance(value.value, int)
            if block and is_int and 90000 <= value.value < 91000:
                found.setdefault(block, []).append((value.value, f"{path.name}:{name}"))
    return found


def _overlap(a: dict, b: dict) -> bool:
    return a["start"] <= b["end"] and b["start"] <= a["end"]


class BlockShapeTest(unittest.TestCase):
    def test_every_block_is_an_ordered_start_end_pair(self):
        for name, cfg in BLOCKS.items():
            with self.subTest(block=name):
                self.assertEqual(set(cfg), {"start", "end"})
                self.assertIsInstance(cfg["start"], int)
                self.assertIsInstance(cfg["end"], int)
                self.assertLessEqual(cfg["start"], cfg["end"])

    def test_the_client_patch_blocks_exist(self):
        for name in (
            "spellicon", "soundentries", "spellvisual", "creaturedisplayinfo", "creaturemodeldata",
            "gameobjectdisplayinfo", "summonproperties",
        ):
            self.assertIn(name, BLOCKS)

    def test_blocks_of_one_table_do_not_overlap(self):
        for table, names in SAME_TABLE_BLOCKS.items():
            for i, a in enumerate(names):
                for b in names[i + 1:]:
                    with self.subTest(table=table, blocks=(a, b)):
                        self.assertFalse(_overlap(BLOCKS[a], BLOCKS[b]), f"{a} overlaps {b}")

    def test_talent_tab_and_spell_blocks_are_unchanged(self):
        # The earlier blocks keep their numbers: a reader that hardcodes one must keep working.
        self.assertEqual(BLOCKS["spell"], {"start": 200000, "end": 209999})
        self.assertEqual(BLOCKS["creature"], {"start": 300000, "end": 300999})
        self.assertEqual(BLOCKS["spell_group"], {"start": 1200, "end": 1299})

    def test_summonproperties_clears_the_stock_maximum(self):
        self.assertGreater(BLOCKS["summonproperties"]["start"], 2935)  # SummonProperties.dbc tops out at 2935

    def test_spellrunecost_clears_the_stock_maximum(self):
        # SpellRuneCost.dbc has 475 rows with a maximum id of 2513; spell_dbc.RuneCostID tops out at 2467 (T0 s1.1)
        self.assertEqual(BLOCKS["spellrunecost"], {"start": 2600, "end": 2629})
        self.assertGreater(BLOCKS["spellrunecost"]["start"], 2513)

    def test_death_knight_t1_widened_the_sound_and_visual_blocks(self):
        # shaman's slices filled the old ends (90100 / 90199); the widened ends hold Death Knight's slices
        self.assertEqual(BLOCKS["soundentries"], {"start": 90001, "end": 90199})
        self.assertEqual(BLOCKS["spellvisual"], {"start": 90001, "end": 90299})

    def test_every_id_already_used_is_inside_its_block(self):
        for name, (low, high) in USED_DISPLAY_IDS.items():
            with self.subTest(block=name):
                self.assertGreaterEqual(low, BLOCKS[name]["start"])
                self.assertLessEqual(high, BLOCKS[name]["end"])

    def test_every_constant_the_patch_scripts_mint_is_inside_its_block(self):
        scanned = scanned_used_ids()
        self.assertEqual(set(scanned), {"spellicon", "soundentries", "spellvisual"})  # the scan found the scripts
        for block, found in scanned.items():
            for value, where in found:
                with self.subTest(block=block, constant=where):
                    self.assertTrue(BLOCKS[block]["start"] <= value <= BLOCKS[block]["end"], f"{where} = {value}")

    def test_the_scan_sees_a_known_extreme(self):
        scanned = scanned_used_ids()
        self.assertIn(90239, [v for v, _ in scanned["spellicon"]])
        self.assertIn(90091, [v for v, _ in scanned["spellvisual"]])


class ReservationTest(unittest.TestCase):
    def test_a_reservation_exists_for_shaman_death_knight_and_the_healing_sim(self):
        for owner in ("shaman", "deathknight", "healsim"):
            self.assertIn(owner, RESERVATIONS)

    def test_reservations_sit_inside_their_block(self):
        for class_name, tables in RESERVATIONS.items():
            for table, cfg in tables.items():
                with self.subTest(cls=class_name, table=table):
                    self.assertIn(table, BLOCKS, f"{table} has no tool-wide block")
                    self.assertGreaterEqual(cfg["start"], BLOCKS[table]["start"])
                    self.assertLessEqual(cfg["end"], BLOCKS[table]["end"])
                    self.assertLessEqual(cfg["start"], cfg["end"])

    def test_no_two_classes_overlap_in_a_table(self):
        names = sorted(RESERVATIONS)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                for table in set(RESERVATIONS[a]) & set(RESERVATIONS[b]):
                    with self.subTest(table=table, classes=(a, b)):
                        self.assertFalse(_overlap(RESERVATIONS[a][table], RESERVATIONS[b][table]))

    def test_shaman_reservations_are_the_plan_section_4_rows(self):
        shaman = {table: (cfg["start"], cfg["end"]) for table, cfg in RESERVATIONS["shaman"].items()}
        self.assertEqual(shaman["spell"], (202200, 202799))
        self.assertEqual(shaman["talent"], (60280, 60329))
        self.assertEqual(shaman["skilllineability"], (30640, 30719))
        self.assertEqual(shaman["spell_group"], (1251, 1270))
        self.assertEqual(shaman["spelldescriptionvariables"], (1190, 1229))
        self.assertEqual(shaman["creature"], (300260, 300299))
        self.assertEqual(shaman["spellicon"], (90270, 90309))
        self.assertEqual(shaman["soundentries"], (90081, 90100))
        self.assertEqual(shaman["spellvisual"], (90130, 90179))
        self.assertEqual(shaman["creaturedisplayinfo"], (90440, 90469))
        self.assertEqual(shaman["gameobjectdisplayinfo"], (90010, 90014))
        self.assertEqual(shaman["summonproperties"], (3000, 3009))

    def test_deathknight_reservations_are_the_plan_section_4_rows(self):
        dk = {table: (cfg["start"], cfg["end"]) for table, cfg in RESERVATIONS["deathknight"].items()}
        self.assertEqual(dk["spell"], (203000, 203699))
        self.assertEqual(dk["talent"], (60330, 60389))
        self.assertEqual(dk["skilllineability"], (30720, 30779))
        self.assertEqual(dk["spell_group"], (1271, 1285))
        self.assertEqual(dk["spelldescriptionvariables"], (1230, 1299))
        self.assertEqual(dk["creature"], (300300, 300339))
        self.assertEqual(dk["spellicon"], (90310, 90369))
        self.assertEqual(dk["soundentries"], (90101, 90120))
        self.assertEqual(dk["spellvisual"], (90180, 90249))
        self.assertEqual(dk["creaturedisplayinfo"], (90470, 90489))
        self.assertEqual(dk["creaturemodeldata"], (90470, 90489))
        self.assertEqual(dk["gameobjectdisplayinfo"], (90015, 90019))
        self.assertEqual(dk["summonproperties"], (3010, 3024))
        self.assertEqual(dk["spellcategory"], (1307, 1309))
        self.assertEqual(dk["spellrunecost"], (2600, 2609))
        self.assertEqual(len(dk), 15)

    def test_healsim_reserves_its_spells_and_nothing_else(self):
        healsim = {table: (cfg["start"], cfg["end"]) for table, cfg in RESERVATIONS["healsim"].items()}
        self.assertEqual(healsim, {"spell": (202900, 202909)})

    def test_death_knights_spell_slice_does_not_overlap_the_healing_sims(self):
        # the T0 collision: DK's first spell block was 202900-203599 and swallowed 202900-202909
        self.assertFalse(_overlap(RESERVATIONS["deathknight"]["spell"], RESERVATIONS["healsim"]["spell"]))
        self.assertFalse(_overlap(RESERVATIONS["shaman"]["spell"], RESERVATIONS["healsim"]["spell"]))

    def test_the_spellcategory_and_runecost_slices_fit_the_blocks_they_are_cut_from(self):
        self.assertTrue(
            BLOCKS["spellcategory"]["start"] <= RESERVATIONS["deathknight"]["spellcategory"]["start"]
            and RESERVATIONS["deathknight"]["spellcategory"]["end"] <= BLOCKS["spellcategory"]["end"]
        )
        self.assertLessEqual(RESERVATIONS["deathknight"]["spellrunecost"]["end"], BLOCKS["spellrunecost"]["end"])

    def test_a_deliberately_out_of_block_reservation_would_fail(self):
        # The check above is not vacuous: a reservation poking out of its block is detected by the same comparison.
        out = {"start": 209990, "end": 210010}
        self.assertFalse(
            BLOCKS["spell"]["start"] <= out["start"] and out["end"] <= BLOCKS["spell"]["end"],
        )


class _AnyRows(dict):
    """Accepts every creature entry / spell group id: this test collects ids, it does not validate them."""

    def __contains__(self, key):
        return True


class _AnySet(set):
    def __contains__(self, key):
        return True


class _AnyTrainer:
    def trainer_problems(self, trainer_id):
        return []


def declared_ids(class_dir: Path) -> dict[str, list[int]]:
    """Every id the class package declares, by id kind (the ids.yaml block names)."""
    stock_talents = (
        state.load_stock_rows(dbcfmt.TALENT) if (state.BASE_DBC_DIR / dbcfmt.TALENT.dbc_filename).is_file() else {}
    )
    reg = registry.load_class_package(
        class_dir, ids_cfg=IDS, trainer_index=_AnyTrainer(), existing_group_ids=_AnySet(), shapeshift_index={},
        existing_creature_rows=_AnyRows(), creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        live_data=spell_tables.dsl_live_data(
            stock_talents, {},
            lambda: state.load_existing_rows(dbcfmt.SKILLLINEABILITY),
            lambda: state.load_stock_rows(dbcfmt.CHRCLASSES),
            lambda: state.load_stock_rows(dbcfmt.SKILLLINEABILITY),
        ),
    )
    return {
        "spell": [int(e["id"]) for e in reg.spells],
        "talent": [int(e["id"]) for e in reg.talents],
        "skilllineability": [int(e["id"]) for e in reg.skill_line_abilities],
        "spellrunecost": [int(r["ID"]) for r in reg.spell_rune_costs],
        "spellcategory": [int(r["ID"]) for r in reg.spell_categories],
        "spell_group": [int(r["id"]) for r in reg.spell_groups] + [int(r["group_id"]) for r in reg.spell_group_rules],
        "spelldescriptionvariables": [int(r["id"]) for r in reg.tooltip_vars],
        "creature": [int(r["entry"]) for r in reg.creature_templates]
        + [int(r["CreatureID"]) for r in reg.creature_template_models]
        + [int(r["CreatureID"]) for r in reg.creature_template_spells],
    }


def out_of_reservation(class_name: str, ids_by_kind: dict[str, list[int]]) -> list[str]:
    """Ids the class declared inside a tool-wide block but outside its own reservation."""
    problems = []
    for kind, ids in ids_by_kind.items():
        block = BLOCKS[kind]
        reservation = RESERVATIONS[class_name].get(kind)
        for value in sorted(set(ids)):
            if not block["start"] <= value <= block["end"]:
                continue  # a stock id the class file references, not a minted one
            if reservation is None or not reservation["start"] <= value <= reservation["end"]:
                problems.append(f"{kind} {value}")
    return problems


class ClassDeclarationsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shaman = declared_ids(TOOL_ROOT / "source" / "classes" / "shaman")
        cls.deathknight = declared_ids(TOOL_ROOT / "source" / "classes" / "deathknight")
        cls.npcs = declared_ids(TOOL_ROOT / "source" / "npcs")

    def test_shaman_declares_only_inside_its_reservation(self):
        self.assertEqual(out_of_reservation("shaman", self.shaman), [])

    def test_the_spike_ids_are_inside_it(self):
        spike_spells = {i for i in self.shaman["spell"] if 202760 <= i <= 202779}
        if spike_spells:  # the spike file is deleted at SH0 start
            self.assertEqual(spike_spells, set(range(202760, 202780)) - {202774})
            self.assertEqual(out_of_reservation("shaman", {"spell": sorted(spike_spells)}), [])
            self.assertIn(1270, self.shaman["spell_group"])
            self.assertTrue({300298, 300299} <= set(self.shaman["creature"]))

    def test_death_knight_declares_only_inside_its_reservation(self):
        # declared_ids loads the package with the stock Talent.dbc present; if that load failed this would raise
        self.assertEqual(out_of_reservation("deathknight", self.deathknight), [])

    def test_the_death_knight_spike_ids_are_inside_it(self):
        spike_spells = {i for i in self.deathknight["spell"] if 203680 <= i <= 203699}
        if spike_spells:  # the spike file is deleted at DK0a start
            self.assertEqual(out_of_reservation("deathknight", {"spell": sorted(spike_spells)}), [])
            self.assertIn(1285, self.deathknight["spell_group"])
            self.assertIn(30779, self.deathknight["skilllineability"])
            self.assertIn(300339, self.deathknight["creature"])
            for kind, probe in (("spell_group", 1285), ("skilllineability", 30779), ("creature", 300339)):
                self.assertEqual(out_of_reservation("deathknight", {kind: [probe]}), [])

    def test_death_knight_out_of_reservation_probes_fail(self):
        # one past the end of each slice, plus 202950: inside the spell block, outside every reservation
        probes = {"spell": [203700, 202950], "talent": [60390], "skilllineability": [30780], "spell_group": [1286],
                  "creature": [300340], "spelldescriptionvariables": [1300],
                  "spellrunecost": [2610], "spellcategory": [1306]}
        self.assertEqual(
            out_of_reservation("deathknight", probes),
            ["spell 202950", "spell 203700", "talent 60390", "skilllineability 30780", "spell_group 1286",
             "creature 300340", "spelldescriptionvariables 1300", "spellrunecost 2610", "spellcategory 1306"],
        )
        self.assertEqual(out_of_reservation("deathknight", {"spell": [202900]}), ["spell 202900"])  # the sim's spell

    def test_the_healing_sims_spells_are_inside_the_healsim_reservation(self):
        sim_spells = [i for i in self.npcs["spell"] if BLOCKS["spell"]["start"] <= i <= BLOCKS["spell"]["end"]]
        self.assertTrue(sim_spells)  # source/npcs/healsim_spells.py declares 202900 and 202901
        self.assertEqual(out_of_reservation("healsim", {"spell": sim_spells}), [])
        self.assertTrue({202900, 202901} <= set(sim_spells))
        self.assertEqual(out_of_reservation("healsim", {"spell": [202910]}), ["spell 202910"])
        self.assertEqual(out_of_reservation("healsim", {"spell": [203000]}), ["spell 203000"])

    def test_a_deliberately_out_of_block_id_fails(self):
        ids = {"spell": [202800], "talent": [60330], "skilllineability": [30720], "spell_group": [1271],
               "spelldescriptionvariables": [1230], "creature": [300300]}
        # 202800 / 60330 / 30720 / 1271 / 1230 / 300300 are out of *shaman's* slice (past its reservation, inside the
        # tool-wide block); 60330 / 30720 / 1271 / 1230 / 300300 are now Death Knight ids, which is fine.
        self.assertEqual(
            out_of_reservation("shaman", ids),
            ["spell 202800", "talent 60330", "skilllineability 30720", "spell_group 1271",
             "spelldescriptionvariables 1230", "creature 300300"],
        )

    def test_a_stock_id_the_class_references_is_not_judged(self):
        self.assertEqual(out_of_reservation("shaman", {"spell": [8042], "talent": [1], "creature": [15439]}), [])

    def test_an_id_in_another_classes_range_fails(self):
        # hunter owns 202100-202159 and creature 300219: both are in shaman's tool-wide block, outside its slice
        self.assertEqual(
            out_of_reservation("shaman", {"spell": [202106], "creature": [300219]}),
            ["spell 202106", "creature 300219"],
        )


if __name__ == "__main__":
    unittest.main()
