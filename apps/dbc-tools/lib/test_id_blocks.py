"""
source/ids.yaml's tool-wide client-patch blocks and per-class reservations (shaman-rework T1, step 1).

Checks, from the file itself and from the class sources:
  - every block is a {start, end} pair, and blocks that feed the same table do not overlap;
  - every per-class reservation sits inside the block of the same name, and no two classes' reservations overlap;
  - every custom id a class declares (spell, talent, SkillLineAbility, spell_group, tooltip variable, creature)
    that falls inside a tool-wide block is inside that class's reservation. Shaman and Death Knight reserve slices
    (the shaman spike's 202760-202779, 300298/300299 and 1270, the Death Knight P0 spike's 203680-203699, 1285,
    30779 and 300349, and the Rogue P0 spike's 204370-204399, 1295, 30838/30839 and 300368/300369 are inside theirs;
    the Warrior's September Protection ids 200028-200066 (all but the mage's two) and talents 60003-60006 are the one
    grandfathered exception, pinned exactly in `WARRIOR_LEGACY`);
  - a non-class owner reserves under its project name (`healsim`: spells 202900-202909, declared from source/npcs),
    so the overlap test keeps every class out of its ids.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_id_blocks.py
"""

from __future__ import annotations

import sys
import tempfile
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


def scanned_used_ids(scripts: list[Path] | None = None) -> dict[str, list[tuple[int, str]]]:
    """Every custom (90000-90999) id the patch scripts name as a module-level constant, by block: the scan keeps the
    test from going stale when a script mints a new id (a hard-coded maximum would not notice). A constant that
    names a stock id (`EFFECT_POISON_BOMB_VIAL_STOCK = 5597` in patch_rogue_vfx_models.py, `SOUND_*` 3087 in the druid
    script) is below 90000 and is skipped, whatever its prefix. `scripts` replaces the real list (tests plant files)."""
    import ast

    found: dict[str, list[tuple[int, str]]] = {}
    if scripts is None:
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


ROGUE_VFX_SCRIPT = "patch_rogue_vfx_models.py"
WARRIOR_VFX_SCRIPT = "patch_warrior_vfx_models.py"  # S1 echo visual 90300 first; stage V adds the rest
# The one shared icon script: every class's Ascension SpellIcon rows are minted here (the rogue's 90370-90374 too), so a
# spellicon constant of this script may sit in the rogue slice.
ICON_SCRIPT = "build_patch_i.py"


def class_slice_problems(class_name: str, script_name: str, scanned: dict[str, list[tuple[int, str]]]) -> list[str]:
    """Scanned constants that break `class_name`'s ownership rule: a constant is inside one of the class's slices
    (`RESERVATIONS[class_name]`, e.g. the rogue's spellvisual 90250-90299, soundentries 90121-90140, spellicon
    90370-90419) if and only if the class's own VFX script (`script_name`) names it; a spellicon constant may also come
    from the shared icon script, build_patch_i.py, which mints every class's SpellIcon rows."""
    owned = RESERVATIONS[class_name]
    problems = []
    for block, found in scanned.items():
        for value, where in found:
            in_slice = block in owned and owned[block]["start"] <= value <= owned[block]["end"]
            from_script = where.startswith(script_name)
            if in_slice:
                allowed = from_script or (block == "spellicon" and where.startswith(ICON_SCRIPT))
            else:
                allowed = not from_script
            if not allowed:
                problems.append(f"{where} = {value} ({block})")
    return problems


def rogue_slice_problems(scanned: dict[str, list[tuple[int, str]]]) -> list[str]:
    return class_slice_problems("rogue", ROGUE_VFX_SCRIPT, scanned)


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
        self.assertEqual(BLOCKS["spell_group"], {"start": 1200, "end": 1399})  # widened by Rogue T1 (was 1299)
        self.assertEqual(BLOCKS["spellicon"], {"start": 90100, "end": 90499})  # widened by Rogue T1 (was 90399)

    def test_summonproperties_clears_the_stock_maximum(self):
        self.assertGreater(BLOCKS["summonproperties"]["start"], 2935)  # SummonProperties.dbc tops out at 2935

    def test_spellrunecost_clears_the_stock_maximum(self):
        # SpellRuneCost.dbc has 475 rows with a maximum id of 2513; spell_dbc.RuneCostID tops out at 2467 (T0 s1.1)
        self.assertEqual(BLOCKS["spellrunecost"], {"start": 2600, "end": 2629})
        self.assertGreater(BLOCKS["spellrunecost"]["start"], 2513)

    def test_death_knight_t1_widened_the_sound_and_visual_blocks(self):
        # shaman's slices filled the old ends (90100 / 90199); the widened ends hold Death Knight's slices. The visual
        # block was widened again by Warrior T1 (see test_warrior_t1_...): from DK T1 on it reaches at least 90299
        self.assertEqual(BLOCKS["soundentries"], {"start": 90001, "end": 90199})
        self.assertEqual(BLOCKS["spellvisual"]["start"], 90001)
        self.assertGreaterEqual(BLOCKS["spellvisual"]["end"], 90299)

    def test_rogue_t1_widened_spell_group_and_spellicon_and_left_the_rest(self):
        # spell_group 1299 -> 1399 (1296-1299 would have been all that was left), spellicon 90399 -> 90499 (the rogue
        # slice ends at 90419); the rogue reserves no spellcategory (Warrior T1 widened that block, see below), and
        # the two display-table blocks it skips stay as they were
        self.assertEqual(BLOCKS["spell_group"]["end"], 1399)
        self.assertEqual(BLOCKS["spellicon"]["end"], 90499)
        self.assertEqual(BLOCKS["gameobjectdisplayinfo"], {"start": 90001, "end": 90099})
        self.assertEqual(BLOCKS["summonproperties"], {"start": 3000, "end": 3099})

    def test_warrior_t1_widened_the_visual_and_category_blocks(self):
        # spellvisual 90299 -> 90399 (the rogue slice filled 90250-90299, the warrior takes 90300-90339) and
        # spellcategory 1309 -> 1319 (the Death Knight slice ends at 1309, the warrior takes 1313-1319); every other
        # block stays where the earlier classes left it
        self.assertEqual(BLOCKS["spellvisual"], {"start": 90001, "end": 90399})
        self.assertEqual(BLOCKS["spellcategory"], {"start": 1300, "end": 1319})
        self.assertEqual(BLOCKS["soundentries"], {"start": 90001, "end": 90199})
        self.assertEqual(BLOCKS["spellicon"], {"start": 90100, "end": 90499})
        self.assertEqual(BLOCKS["spell_group"], {"start": 1200, "end": 1399})
        self.assertEqual(BLOCKS["creaturedisplayinfo"], {"start": 90001, "end": 90499})
        self.assertEqual(BLOCKS["creaturemodeldata"], {"start": 90001, "end": 90499})
        self.assertEqual(BLOCKS["gameobjectdisplayinfo"], {"start": 90001, "end": 90099})
        self.assertEqual(BLOCKS["summonproperties"], {"start": 3000, "end": 3099})

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

    def test_the_scan_skips_stock_id_constants_and_sees_the_rogue_vfx_ones(self):
        # patch_rogue_vfx_models.py names stock ids with the same prefixes (EFFECT_*_STOCK = 5597 / 4586 / 73,
        # KIT_READY_THROWN_STOCK = 171, SOUND_*_STOCK = 10720 ...): they are below 90000, so the scan skips them and
        # never reports a stock id as out of block.
        scanned = scanned_used_ids()
        seen = {where.split(":")[1]: value for found in scanned.values() for value, where in found
                if where.startswith("patch_rogue_vfx_models.py")}
        self.assertEqual(seen["EFFECT_KINGSBANE_CHEST"], 90250)
        self.assertEqual(seen["SV_DEATH_FROM_ABOVE_LANDING"], 90256)
        self.assertEqual(seen["SOUND_KINGSBANE_CAST"], 90121)
        self.assertFalse([name for name in seen if name.endswith("_STOCK")])
        every = [value for found in scanned.values() for value, _ in found]
        self.assertFalse([v for v in every if v < 90000])

    def test_the_rogue_vfx_constants_sit_inside_the_rogue_slices(self):
        # the tool-wide check above is satisfied by any id in 90001-90299; this one pins the rogue script to the
        # rogue reservation and keeps every other script's constants out of those slices
        scanned = scanned_used_ids()
        self.assertEqual(rogue_slice_problems(scanned), [])
        mine = sum(1 for found in scanned.values() for _, where in found if where.startswith(ROGUE_VFX_SCRIPT))
        self.assertGreaterEqual(mine, 20)  # not vacuous: the script's EFFECT / KIT / SV / SOUND constants were seen

    def test_the_scan_flags_a_rogue_script_constant_outside_the_rogue_slice(self):
        # plant real scripts and run the real scanner and the real check on them (90249 is the last Death Knight
        # visual id, one below the rogue slice; 90260 is inside it)
        with tempfile.TemporaryDirectory() as d:
            rogue_script = Path(d) / ROGUE_VFX_SCRIPT
            rogue_script.write_text("SV_X = 90249\nSV_OK = 90250\nSOUND_STOCK_ONE = 3087\nSOUND_Y = 90141\n")
            other = Path(d) / "patch_other_vfx_models.py"
            other.write_text("EFFECT_Z = 90260\nICON_FINE = 90369\n")
            scanned = scanned_used_ids([rogue_script, other])
        self.assertCountEqual(
            rogue_slice_problems(scanned),
            [f"{ROGUE_VFX_SCRIPT}:SV_X = 90249 (spellvisual)", f"{ROGUE_VFX_SCRIPT}:SOUND_Y = 90141 (soundentries)",
             "patch_other_vfx_models.py:EFFECT_Z = 90260 (spellvisual)"],
        )

    def test_the_real_scan_finds_only_the_warrior_script_in_the_warrior_slices(self):
        # patch_warrior_vfx_models.py (S1 playtest, the Thunder Clap Echo's SpellVisual 90300) is the only script that
        # may name a constant in 90141-90150 (soundentries) or 90300-90339 (spellvisual); stage V adds its rows to the
        # same script. The warrior's spellicon slice 90420-90449 is minted by the shared build_patch_i.py (playtest
        # 2026-10-30: Avatar 90420, Colossus Smash 90421)
        scanned = scanned_used_ids()
        warrior = RESERVATIONS["warrior"]
        inside = [f"{where} = {value} ({block})" for block, found in scanned.items() for value, where in found
                  if block in warrior and warrior[block]["start"] <= value <= warrior[block]["end"]]
        self.assertEqual(sorted(inside), sorted([
            f"{WARRIOR_VFX_SCRIPT}:SV_THUNDER_CLAP_ECHO = 90300 (spellvisual)",
            "build_patch_i.py:ICON_ID_WARRIOR_AVATAR = 90420 (spellicon)",
            "build_patch_i.py:ICON_ID_WARRIOR_COLOSSUS_SMASH = 90421 (spellicon)"]))
        self.assertEqual(class_slice_problems("warrior", WARRIOR_VFX_SCRIPT, scanned), [])
        # not vacuous: the real scan did run over the scripts and over the other classes' slices
        self.assertGreaterEqual(sum(len(found) for found in scanned.values()), 100)

    def test_the_warrior_script_may_only_name_constants_inside_the_warrior_slices(self):
        # planted scripts through the real scanner: 90299 (the rogue's last visual id) and 90340 (one past the warrior
        # slice) are out, 90300 / 90339 / 90141 / 90150 are in; build_patch_i.py may mint inside the spellicon slice
        with tempfile.TemporaryDirectory() as d:
            warrior_script = Path(d) / WARRIOR_VFX_SCRIPT
            warrior_script.write_text(
                "SV_LOW = 90299\nSV_FIRST = 90300\nEFFECT_LAST = 90339\nSV_HIGH = 90340\nSOUND_FIRST = 90141\n"
                "SOUND_LAST = 90150\nSOUND_STOCK_ONE = 3087\nSOUND_OUT = 90151\n")
            icon_script = Path(d) / ICON_SCRIPT
            icon_script.write_text("ICON_IN_WARRIOR_SLICE = 90420\nICON_PAST = 90450\n")
            other = Path(d) / "patch_other_vfx_models.py"
            other.write_text("EFFECT_Z = 90301\nKIT_FINE = 90250\n")
            scanned = scanned_used_ids([warrior_script, icon_script, other])
        self.assertCountEqual(
            class_slice_problems("warrior", WARRIOR_VFX_SCRIPT, scanned),
            [f"{WARRIOR_VFX_SCRIPT}:SV_LOW = 90299 (spellvisual)",
             f"{WARRIOR_VFX_SCRIPT}:SV_HIGH = 90340 (spellvisual)",
             f"{WARRIOR_VFX_SCRIPT}:SOUND_OUT = 90151 (soundentries)",
             "patch_other_vfx_models.py:EFFECT_Z = 90301 (spellvisual)"],
        )

    def test_the_scan_passes_a_clean_planted_rogue_script(self):
        with tempfile.TemporaryDirectory() as d:
            script = Path(d) / ROGUE_VFX_SCRIPT
            script.write_text("SV_A = 90250\nKIT_B = 90299\nSOUND_C = 90140\nICON_D = 90370\n")
            self.assertEqual(rogue_slice_problems(scanned_used_ids([script])), [])


class ReservationTest(unittest.TestCase):
    def test_a_reservation_exists_for_shaman_death_knight_rogue_warrior_and_the_healing_sim(self):
        for owner in ("shaman", "deathknight", "rogue", "warrior", "healsim"):
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
        self.assertEqual(dk["creature"], (300300, 300349))
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

    def test_rogue_reservations_are_the_plan_section_4_rows(self):
        rogue = {table: (cfg["start"], cfg["end"]) for table, cfg in RESERVATIONS["rogue"].items()}
        self.assertEqual(rogue["spell"], (203700, 204399))
        self.assertEqual(rogue["talent"], (60390, 60449))
        self.assertEqual(rogue["skilllineability"], (30780, 30839))
        self.assertEqual(rogue["spell_group"], (1286, 1295))
        self.assertEqual(rogue["spelldescriptionvariables"], (1300, 1369))
        self.assertEqual(rogue["creature"], (300350, 300369))
        self.assertEqual(rogue["spellicon"], (90370, 90419))
        self.assertEqual(rogue["soundentries"], (90121, 90140))
        self.assertEqual(rogue["spellvisual"], (90250, 90299))
        self.assertEqual(rogue["creaturedisplayinfo"], (90490, 90499))
        self.assertEqual(rogue["creaturemodeldata"], (90490, 90499))
        self.assertEqual(len(rogue), 11)  # no gameobjectdisplayinfo, summonproperties or spellcategory (T0: not needed)

    def test_rogue_slices_follow_the_class_slices_they_were_cut_after(self):
        # each rogue slice starts right after (or clear of) the previous owner's, with no overlap in any table
        for table, rogue in RESERVATIONS["rogue"].items():
            for other in ("shaman", "deathknight", "healsim"):
                if table in RESERVATIONS[other]:
                    with self.subTest(table=table, other=other):
                        self.assertFalse(_overlap(rogue, RESERVATIONS[other][table]))
        self.assertEqual(RESERVATIONS["rogue"]["spell"]["start"], RESERVATIONS["deathknight"]["spell"]["end"] + 1)

    def test_warrior_reservations_are_the_plan_section_4_rows(self):
        warrior = {table: (cfg["start"], cfg["end"]) for table, cfg in RESERVATIONS["warrior"].items()}
        self.assertEqual(warrior["spell"], (204400, 204899))
        self.assertEqual(warrior["talent"], (60450, 60489))
        self.assertEqual(warrior["skilllineability"], (30840, 30869))
        self.assertEqual(warrior["spell_group"], (1296, 1305))
        self.assertEqual(warrior["spelldescriptionvariables"], (1370, 1429))
        self.assertEqual(warrior["creature"], (300370, 300389))
        self.assertEqual(warrior["spellicon"], (90420, 90449))
        self.assertEqual(warrior["soundentries"], (90141, 90150))
        self.assertEqual(warrior["spellvisual"], (90300, 90339))
        self.assertEqual(warrior["spellcategory"], (1313, 1319))
        # no CreatureDisplayInfo / CreatureModelData, GameObjectDisplayInfo or SummonProperties: Skull Banner borrows
        # stock displays and SummonProperties 121 (PLAN s4)
        self.assertEqual(len(warrior), 10)

    def test_warrior_slices_follow_the_class_slices_they_were_cut_after(self):
        # no overlap with any earlier owner in any table; the four tables the earlier classes cut contiguously
        # (spell, talent, SkillLineAbility, spell_group) start right after the rogue's slice
        for table, warrior in RESERVATIONS["warrior"].items():
            for other in ("shaman", "deathknight", "rogue", "healsim"):
                if table in RESERVATIONS[other]:
                    with self.subTest(table=table, other=other):
                        self.assertFalse(_overlap(warrior, RESERVATIONS[other][table]))
        for table in ("spell", "talent", "skilllineability", "spell_group"):
            with self.subTest(table=table):
                self.assertEqual(RESERVATIONS["warrior"][table]["start"], RESERVATIONS["rogue"][table]["end"] + 1)

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
            stock_talents, spell_tables.load_live_item_template_rows,
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


# The September Protection build predates the reservations: 37 spells 200028-200066 (all but the mage's 200037 /
# 200044) and talents 60003-60006 sit outside the warrior's slices (DATA-INVENTORY s7, T0 report s1.3 item 7). They
# are grandfathered exactly; the spec stages replace them and shrink this set as they go.
WARRIOR_LEGACY = {"spell": set(range(200028, 200067)) - {200037, 200044}, "talent": {60003, 60004, 60005, 60006}}


class ClassDeclarationsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shaman = declared_ids(TOOL_ROOT / "source" / "classes" / "shaman")
        cls.deathknight = declared_ids(TOOL_ROOT / "source" / "classes" / "deathknight")
        cls.rogue = declared_ids(TOOL_ROOT / "source" / "classes" / "rogue")
        cls.warrior = declared_ids(TOOL_ROOT / "source" / "classes" / "warrior")
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
            self.assertIn(300349, self.deathknight["creature"])
            for kind, probe in (("spell_group", 1285), ("skilllineability", 30779), ("creature", 300349)):
                self.assertEqual(out_of_reservation("deathknight", {kind: [probe]}), [])

    def test_rogue_declares_only_inside_its_reservation(self):
        # declared_ids loads source/classes/rogue (today the P0 spike file); if that load failed this would raise
        self.assertEqual(out_of_reservation("rogue", self.rogue), [])

    @unittest.skipUnless(
        (TOOL_ROOT / "source" / "classes" / "rogue" / "rogue_p0_spike.py").is_file(),
        "the rogue P0 spike file is deleted at RG0 start",
    )
    def test_the_rogue_spike_ids_are_inside_it(self):
        spike_spells = {i for i in self.rogue["spell"] if 204370 <= i <= 204399}
        self.assertTrue(spike_spells)  # the spike declares 204370-204396
        self.assertEqual(out_of_reservation("rogue", {"spell": sorted(spike_spells)}), [])
        self.assertIn(1295, self.rogue["spell_group"])
        self.assertIn(300369, self.rogue["creature"])
        # only ids the spike really declares: no SkillLineAbility rows, creature 300369 (300368 is reserved, unused)
        self.assertEqual(self.rogue["skilllineability"], [])
        self.assertEqual(out_of_reservation("rogue", {"spell_group": [1295], "creature": [300369]}), [])

    def test_rogue_out_of_reservation_probes_fail(self):
        # one past the end of each slice, plus 202950 (inside the spell block, outside every reservation) and 90249
        # (the last Death Knight visual id, one below the rogue slice)
        # 204400 / 60450 / 30840 / 1296 / 300370 / 1370 / 90420 / 90141 / 90300 are the warrior's first ids now. 90300
        # is past the old visual block end (Warrior T1 widened it to 90399), so it is judged here as a rogue-out id
        probes = {"spell": [204400, 202950], "talent": [60450], "skilllineability": [30840], "spell_group": [1296],
                  "creature": [300370], "spelldescriptionvariables": [1370], "spellicon": [90420],
                  "soundentries": [90141], "spellvisual": [90249, 90300]}
        self.assertEqual(
            out_of_reservation("rogue", probes),
            ["spell 202950", "spell 204400", "talent 60450", "skilllineability 30840", "spell_group 1296",
             "creature 300370", "spelldescriptionvariables 1370", "spellicon 90420", "soundentries 90141",
             "spellvisual 90249", "spellvisual 90300"],
        )

    def test_rogue_slices_that_end_at_their_block_have_no_room_past_the_end(self):
        # creaturedisplayinfo / creaturemodeldata 90500 are one past the rogue slice AND past the tool-wide block, which
        # `out_of_reservation` reads as "an id outside every block" and skips: the guard for these is the block's own
        # end (pinned below), so the next class has to widen the block before it can reserve anything. (The rogue's
        # spellvisual slice used to be in this list; Warrior T1 widened that block to 90399, so 90300 is inside the
        # block now and test_rogue_out_of_reservation_probes_fail judges it.)
        rogue = RESERVATIONS["rogue"]
        for table in ("creaturedisplayinfo", "creaturemodeldata"):
            self.assertEqual(rogue[table]["end"], BLOCKS[table]["end"])
        self.assertEqual(out_of_reservation("rogue", {"creaturedisplayinfo": [90500]}), [])
        self.assertEqual(BLOCKS["creaturedisplayinfo"], {"start": 90001, "end": 90499})
        self.assertEqual(BLOCKS["creaturemodeldata"], {"start": 90001, "end": 90499})

    def test_warrior_declares_only_inside_its_reservation_apart_from_the_legacy_ids(self):
        # exact equality, both ways: a new id outside the reservation fails this test, and a legacy id a spec stage
        # retires makes it fail too, which tells that stage to shrink WARRIOR_LEGACY (and the id counts below)
        legacy_lines = [f"spell {i}" for i in sorted(WARRIOR_LEGACY["spell"])] + [
            f"talent {i}" for i in sorted(WARRIOR_LEGACY["talent"])]
        self.assertEqual(out_of_reservation("warrior", self.warrior), legacy_lines)
        self.assertEqual((len(WARRIOR_LEGACY["spell"]), len(WARRIOR_LEGACY["talent"])), (37, 4))
        # 200037 / 200044 are the mage's: the range 200028-200066 is not all warrior
        self.assertFalse({200037, 200044} & set(self.warrior["spell"]))
        self.assertFalse({200037, 200044} & WARRIOR_LEGACY["spell"])

    @unittest.skipUnless(
        (TOOL_ROOT / "source" / "classes" / "warrior" / "warrior_p0_spike.py").is_file()
        and (TOOL_ROOT / "source" / "npcs" / "warrior_p0_spike_npcs.py").is_file(),
        "the warrior P0 spike files are deleted at W0a start",
    )
    def test_the_warrior_spike_ids_are_inside_it(self):
        # 204869 is the 31st spike id (the PLAN said 204870-204899): the spike declares exactly 204869-204899
        spike_spells = {i for i in self.warrior["spell"] if 204869 <= i <= 204899}
        self.assertEqual(spike_spells, set(range(204869, 204900)))
        self.assertEqual(out_of_reservation("warrior", {"spell": sorted(spike_spells)}), [])
        self.assertIn(1305, self.warrior["spell_group"])
        self.assertEqual(out_of_reservation("warrior", {"spell_group": [1305]}), [])
        # the spike's two creatures are declared from source/npcs, not the class package
        self.assertTrue({300388, 300389} <= set(self.npcs["creature"]))
        self.assertFalse({300388, 300389} & set(self.warrior["creature"]))
        self.assertEqual(out_of_reservation("warrior", {"creature": [300388, 300389]}), [])
        # only ids the spike really declares: no SkillLineAbility rows and no minted talent (60488-60489 and
        # 30868-30869 were reserved for it but never used); the custom talents are the September build's 60003-60006
        # (the package's other talent ids are stock copies below the block)
        self.assertEqual(self.warrior["skilllineability"], [])
        minted = [i for i in self.warrior["talent"] if BLOCKS["talent"]["start"] <= i <= BLOCKS["talent"]["end"]]
        self.assertEqual(sorted(minted), sorted(WARRIOR_LEGACY["talent"]))

    def test_warrior_out_of_reservation_probes_fail(self):
        # one past the end of each slice where that is still inside the block, else one below the start of the slice:
        # 204399 is the rogue's last spell, 1312 sits between the Death Knight's category slice and the warrior's
        probes = {"spell": [204900, 204399], "talent": [60490], "skilllineability": [30870], "spell_group": [1306],
                  "spelldescriptionvariables": [1430], "creature": [300390], "spellicon": [90450],
                  "soundentries": [90151], "spellvisual": [90340], "spellcategory": [1312]}
        self.assertEqual(
            out_of_reservation("warrior", probes),
            ["spell 204399", "spell 204900", "talent 60490", "skilllineability 30870", "spell_group 1306",
             "spelldescriptionvariables 1430", "creature 300390", "spellicon 90450", "soundentries 90151",
             "spellvisual 90340", "spellcategory 1312"],
        )

    def test_death_knight_out_of_reservation_probes_fail(self):
        # one past the end of each slice, plus 202950: inside the spell block, outside every reservation.
        # 203700 / 60390 / 30780 / 1286 / 300350 / 1300 are the rogue's first ids now: past the DK slice, so DK-out.
        probes = {"spell": [203700, 202950], "talent": [60390], "skilllineability": [30780], "spell_group": [1286],
                  "creature": [300350], "spelldescriptionvariables": [1300],
                  "spellrunecost": [2610], "spellcategory": [1306]}
        self.assertEqual(
            out_of_reservation("deathknight", probes),
            ["spell 202950", "spell 203700", "talent 60390", "skilllineability 30780", "spell_group 1286",
             "creature 300350", "spelldescriptionvariables 1300", "spellrunecost 2610", "spellcategory 1306"],
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
