"""
retire_pet_spell() (hunter-rework SHARED §C7.8, T1 step 6): the SkillLineAbility AcquireMethod 0 overrides,
the CreatureSpellData strip, and how both combine with the pet-stale-ranks superseded-rank pass. Fixtures only.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_retire_pet_spell.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfile, dbcfmt, superseded_ranks as sr  # noqa: E402
from lib.dsl import registry  # noqa: E402

LEARN = sr.SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN
BITE, GROWL = 17253, 2649
SPIDER, CAT, IMP = 3, 2, 23
SPIDER_LINE, CAT_LINE, SHARED, IMP_LINE = 203, 209, 270, 188

LINES = {SPIDER: (SPIDER_LINE, SHARED), CAT: (CAT_LINE, SHARED), IMP: (IMP_LINE,)}


def _sla(row_id: int, spell: int, line: int, acquire: int = LEARN) -> dict:
    row = dbcfile.empty_row(dbcfmt.SKILLLINEABILITY)
    row.update(ID=row_id, SkillLine=line, Spell=spell, MinSkillLineRank=1, AcquireMethod=acquire,
               TrivialSkillLineRankHigh=5, TrivialSkillLineRankLow=3)
    return row


def _stock() -> dict[int, dict]:
    rows = [
        _sla(1, BITE, SPIDER_LINE), _sla(2, BITE, CAT_LINE), _sla(3, BITE, SHARED), _sla(4, GROWL, SHARED),
        _sla(5, BITE, 26, acquire=1),            # a player skill line: never a pet row
        _sla(6, BITE, IMP_LINE, acquire=0),      # already not learned
    ]
    return {r["ID"]: r for r in rows}


def _ret(spell: int, families=None) -> dict:
    return {"id": f"{spell}", "spell_id": spell, "families": None if families is None else tuple(families)}


class FamilySkillLinesTest(unittest.TestCase):
    def test_non_zero_lines_per_family(self):
        rows = {3: {"SkillLine_1": 203, "SkillLine_2": 270}, 23: {"SkillLine_1": 188, "SkillLine_2": 0}}
        self.assertEqual(sr.family_skill_lines(rows), {3: (203, 270), 23: (188,)})


class RetiredSkillLineAbilityTest(unittest.TestCase):
    def _ids(self, result: sr.Overrides) -> list[int]:
        return [e["id"] for e in result.entries]

    def test_shared_lines_opt_in_retires_the_shared_row_too(self):
        # PET 4.6's Cower: a 270-only row, retired for everyone while the record strip stays scoped.
        stock = {7: _sla(7, GROWL, SHARED)}
        plain = sr.retired_skilllineability_overrides([_ret(GROWL, [SPIDER])], stock, LINES, [])
        self.assertEqual((plain.entries, len(plain.warnings)), ([], 1))
        opted = sr.retired_skilllineability_overrides(
            [{**_ret(GROWL, [SPIDER]), "shared_lines": True}], stock, LINES, [],
        )
        self.assertEqual(self._ids(opted), [7])
        self.assertEqual(opted.warnings, [])

    def test_opt_in_still_leaves_a_declared_shared_row_to_its_declaration(self):
        stock = {7: _sla(7, GROWL, SHARED)}
        declared = [{"id": 7, "skill_line": SHARED, "spell_id": GROWL}]
        opted = sr.retired_skilllineability_overrides(
            [{**_ret(GROWL, [SPIDER]), "shared_lines": True}], stock, LINES, declared,
        )
        self.assertEqual(opted.entries, [])
        self.assertEqual(len(opted.collisions), 1)

    def test_a_declared_shared_row_silences_the_shared_line_warning(self):
        stock = {7: _sla(7, GROWL, SHARED)}
        declared = [{"id": 7, "skill_line": SHARED, "spell_id": GROWL}]
        result = sr.retired_skilllineability_overrides([_ret(GROWL, [SPIDER])], stock, LINES, declared)
        self.assertEqual((result.entries, result.warnings, result.collisions), ([], [], []))

    def test_matched_records_the_spells_that_found_a_row_in_scope(self):
        stock = _stock()
        self.assertEqual(sr.retired_skilllineability_overrides([_ret(BITE, [SPIDER])], stock, LINES, []).matched, {BITE})
        # Growl is taught only on 270 (shared with Cat): scoped to Imp's own line it matches nothing.
        self.assertEqual(sr.retired_skilllineability_overrides([_ret(GROWL, [IMP])], stock, LINES, []).matched, set())

    def test_family_scoped_retirement_hits_that_familys_own_row_only(self):
        result = sr.retired_skilllineability_overrides([_ret(BITE, [SPIDER])], _stock(), LINES, [])
        self.assertEqual(self._ids(result), [1])
        # The shared 270 row would take Bite from every family: left alone and reported, not silently kept.
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("SkillLineAbility 3", result.warnings[0])
        self.assertIn("skill line 270", result.warnings[0])

    def test_override_is_the_stock_row_with_acquire_method_zero(self):
        stock = _stock()
        result = sr.retired_skilllineability_overrides([_ret(BITE, [SPIDER])], stock, LINES, [])
        self.assertEqual(build.build_skilllineability_row(result.entries[0]), {**stock[1], "AcquireMethod": 0})
        self.assertIn("retire_pet_spell", result.entries[0]["notes"])

    def test_all_family_retirement_hits_every_pet_row_of_the_spell(self):
        result = sr.retired_skilllineability_overrides([_ret(BITE)], _stock(), LINES, [])
        self.assertEqual(self._ids(result), [1, 2, 3])
        self.assertEqual(result.warnings, [])

    def test_player_rows_and_other_spells_are_untouched(self):
        result = sr.retired_skilllineability_overrides([_ret(BITE)], _stock(), LINES, [])
        self.assertNotIn(4, self._ids(result))   # Growl
        self.assertNotIn(5, self._ids(result))   # a player skill line
        self.assertNotIn(6, self._ids(result))   # already AcquireMethod 0

    def test_unknown_family_is_reported(self):
        result = sr.retired_skilllineability_overrides([_ret(BITE, [999])], _stock(), LINES, [])
        self.assertEqual(result.entries, [])
        self.assertIn("family 999", result.warnings[0])

    def test_declared_row_wins_and_is_reported(self):
        declared = [{"id": 1, "skill_line": SPIDER_LINE, "spell_id": BITE}]
        result = sr.retired_skilllineability_overrides([_ret(BITE, [SPIDER])], _stock(), LINES, declared)
        self.assertEqual(result.entries, [])
        self.assertEqual(len(result.collisions), 1)
        self.assertIn("declared row wins", result.collisions[0])

    def test_row_the_rank_pass_already_overrides_is_not_emitted_twice(self):
        result = sr.retired_skilllineability_overrides([_ret(BITE, [SPIDER])], _stock(), LINES, [], taken_ids={1})
        self.assertEqual(result.entries, [])

    def test_two_retirements_of_one_row_emit_it_once(self):
        result = sr.retired_skilllineability_overrides(
            [_ret(BITE, [SPIDER]), _ret(BITE)], _stock(), LINES, [],
        )
        self.assertEqual(self._ids(result), [1, 2, 3])

    def test_promoted_change_is_warned(self):
        stock = _stock()
        existing = {**stock, 1: {**stock[1], "MinSkillLineRank": 7}}
        result = sr.retired_skilllineability_overrides([_ret(BITE, [SPIDER])], stock, LINES, [], existing_rows=existing)
        self.assertEqual(self._ids(result), [1])
        self.assertIn("promoted migration", result.warnings[0])

    def test_promoted_override_is_silent(self):
        stock = _stock()
        existing = {**stock, 1: {**stock[1], "AcquireMethod": 0}}
        result = sr.retired_skilllineability_overrides([_ret(BITE, [SPIDER])], stock, LINES, [], existing_rows=existing)
        self.assertEqual(self._ids(result), [1])
        self.assertTrue(all("promoted" not in w for w in result.warnings))


def _csd(row_id: int, *spells: int) -> dict:
    row = dbcfile.empty_row(dbcfmt.CREATURESPELLDATA)
    for i, spell in enumerate(spells, start=1):
        row[f"Spells_{i}"] = spell
        row[f"Availability_{i}"] = 100
    row["ID"] = row_id
    return row


CREATURES = {
    1: {"family": SPIDER, "PetSpellDataId": 100},
    2: {"family": CAT, "PetSpellDataId": 101},
    3: {"family": SPIDER, "PetSpellDataId": 102},   # 102 is shared by a Spider and a Cat
    4: {"family": CAT, "PetSpellDataId": 102},
    5: {"family": SPIDER, "PetSpellDataId": 0},     # no record
}


def _csd_stock() -> dict[int, dict]:
    rows = [_csd(100, BITE, GROWL), _csd(101, BITE), _csd(102, BITE, GROWL), _csd(103, GROWL), _csd(104, BITE)]
    return {r["ID"]: r for r in rows}   # 104: holds Bite but no creature names it


class SpellDataStripsTest(unittest.TestCase):
    def test_all_family_strips_every_named_record_that_holds_the_spell(self):
        strips, warnings = sr.spell_data_strips([_ret(BITE)], CREATURES, _csd_stock())
        self.assertEqual(strips, {100: {BITE}, 101: {BITE}, 102: {BITE}})   # 104 is named by nobody
        self.assertEqual(warnings, [])

    def test_family_scoped_strips_only_that_familys_records(self):
        strips, warnings = sr.spell_data_strips([_ret(BITE, [SPIDER])], CREATURES, _csd_stock())
        self.assertEqual(strips, {100: {BITE}})
        # 102 holds Bite but a Cat names it too: a record cannot be split, so it stays and is reported.
        self.assertEqual(len(warnings), 1)
        self.assertIn("CreatureSpellData 102", warnings[0])

    def test_record_holding_only_a_superseded_rank_is_stripped(self):
        # 104 names rank 17255 of a Bite chain collapsed onto 17253: after the mapping it holds the retired survivor.
        stock = {**_csd_stock(), 105: _csd(105, 17255)}
        creatures = {**CREATURES, 6: {"family": SPIDER, "PetSpellDataId": 105}}
        superseded = {17255: BITE}
        strips, _ = sr.spell_data_strips([_ret(BITE, [SPIDER])], creatures, stock, superseded)
        self.assertEqual(strips[105], {BITE})
        strips, _ = sr.spell_data_strips([_ret(BITE)], creatures, stock, superseded)
        self.assertEqual(strips[105], {BITE})
        # Without the mapping the record is missed (the bug).
        self.assertNotIn(105, sr.spell_data_strips([_ret(BITE)], creatures, stock)[0])
        applied = sr.creaturespelldata_overrides(superseded, stock, strips=strips).rows
        self.assertEqual([r for r in applied if r["ID"] == 105][0]["Spells_1"], 0)

    def test_superseded_rank_record_named_by_another_family_is_reported(self):
        stock = {105: _csd(105, 17255)}
        creatures = {1: {"family": SPIDER, "PetSpellDataId": 105}, 2: {"family": CAT, "PetSpellDataId": 105}}
        strips, warnings = sr.spell_data_strips([_ret(BITE, [SPIDER])], creatures, stock, {17255: BITE})
        self.assertEqual((strips, len(warnings)), ({}, 1))

    def test_record_without_the_spell_is_not_touched(self):
        strips, _ = sr.spell_data_strips([_ret(GROWL, [CAT])], CREATURES, _csd_stock())
        self.assertNotIn(101, strips)   # the Cat's own record holds only Bite


class CreatureSpellDataStripApplicationTest(unittest.TestCase):
    def test_strip_zeroes_the_slot_and_its_availability(self):
        stock = _csd_stock()
        result = sr.creaturespelldata_overrides({}, stock, strips={100: frozenset({BITE})})
        self.assertEqual([r["ID"] for r in result.rows], [100])
        self.assertEqual(result.rows[0], {**stock[100], "Spells_1": 0, "Availability_1": 0})

    def test_record_both_rules_touch_is_mapped_first_then_stripped(self):
        # 7799 (superseded -> survivor 3110) and 16829 (-> 16827) share a record; retiring 3110 strips the
        # slot the first rank mapped onto, and the second mapping still happens.
        stock = {200: _csd(200, 7799, 16829, GROWL)}
        superseded = {7799: 3110, 16829: 16827}
        result = sr.creaturespelldata_overrides(superseded, stock, strips={200: frozenset({3110})})
        self.assertEqual(len(result.rows), 1)
        row = result.rows[0]
        self.assertEqual((row["Spells_1"], row["Spells_2"], row["Spells_3"]), (0, 16827, GROWL))
        self.assertEqual((row["Availability_1"], row["Availability_2"]), (0, 100))

    def test_retiring_the_superseded_rank_itself_strips_its_stock_slot(self):
        stock = {200: _csd(200, 7799)}
        row = sr.creaturespelldata_overrides({7799: 3110}, stock, strips={200: frozenset({7799})}).rows[0]
        self.assertEqual(row["Spells_1"], 0)

    def test_record_neither_rule_touches_is_not_emitted(self):
        stock = _csd_stock()
        result = sr.creaturespelldata_overrides({7799: 3110}, stock, strips={100: frozenset({BITE})})
        self.assertNotIn(103, [r["ID"] for r in result.rows])
        self.assertNotIn(101, [r["ID"] for r in result.rows])

    def test_without_strips_the_result_is_what_it_was(self):
        stock = {9477: _csd(9477, 16829, 24450)}
        with_none = sr.creaturespelldata_overrides({16829: 16827}, stock)
        explicit = sr.creaturespelldata_overrides({16829: 16827}, stock, strips={})
        self.assertEqual(with_none.rows, explicit.rows)
        self.assertEqual(with_none.rows[0], {**stock[9477], "Spells_1": 16827})

    def test_already_live_strip_emits_nothing(self):
        stock = _csd_stock()
        first = sr.creaturespelldata_overrides({}, stock, dict(stock), strips={100: frozenset({BITE})})
        promoted = {**stock, 100: first.rows[0]}
        rerun = sr.creaturespelldata_overrides({}, stock, promoted, strips={100: frozenset({BITE})})
        self.assertEqual(rerun.to_emit, [])
        self.assertEqual(rerun.warnings, [])


def _real_pet_data():
    from lib import spell_tables, state  # noqa: PLC0415
    from bootstrap import load_spell_ranks_chains  # noqa: PLC0415

    creatures = {int(r["entry"]): r for r in spell_tables.load_creature_table_index().live_rows("creature_template")}
    return creatures, state.load_stock_rows(dbcfmt.CREATURESPELLDATA), load_spell_ranks_chains()


@unittest.skipUnless((TOOL_ROOT.parents[1] / "var" / "extractors" / "dbc" / "CreatureSpellData.dbc").is_file(),
                     "needs var/extractors/dbc/CreatureSpellData.dbc")
class RealDataStripTest(unittest.TestCase):
    """T-FIX T1-2 on real data: Spider Bite 17253 and Gore 35290 are collapsed-chain survivors that a lot of
    records name only through an older rank. After the strip + the survivor mapping nothing may still hold them."""

    @classmethod
    def setUpClass(cls):
        cls.creatures, cls.stock, chains = _real_pet_data()
        cls.superseded = sr.superseded_ranks(chains, {17253, 35290})
        cls.columns = [c for c in dbcfmt.CREATURESPELLDATA.columns if c.startswith("Spells_")]

    def _leftovers(self, spell, families):
        retirement = _ret(spell, families)
        strips, _ = sr.spell_data_strips([retirement], self.creatures, self.stock, self.superseded)
        final = {r["ID"]: r for r in sr.creaturespelldata_overrides(self.superseded, self.stock, strips=strips).rows}
        named_by: dict[int, set[int]] = {}
        for row in self.creatures.values():
            if int(row.get("PetSpellDataId") or 0):
                named_by.setdefault(int(row["PetSpellDataId"]), set()).add(int(row.get("family") or 0))
        left = []
        for record, fams in named_by.items():
            if record not in self.stock or (families is not None and (fams - set(families) or not fams & set(families))):
                continue
            row = final.get(record, self.stock[record])
            if any(row[c] == spell for c in self.columns):
                left.append(record)
        return left, strips

    def test_spider_bite_scoped_to_spiders_leaves_no_spider_only_record(self):
        left, strips = self._leftovers(17253, [SPIDER])
        self.assertEqual(left, [])
        self.assertGreater(len(strips), 8)   # the stock-slot-only rule found 8

    def test_gore_for_every_family_leaves_no_record(self):
        left, strips = self._leftovers(35290, None)
        self.assertEqual(left, [])
        self.assertGreater(len(strips), 15)


class RegistryDeclarationTest(unittest.TestCase):
    def _load(self, source: str) -> registry.Registry:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "hunter.py"
            path.write_text(source)
            return registry.load_class_file(path)

    def test_records_spell_and_families(self):
        reg = self._load(
            "from lib.dsl.registry import retire_pet_spell, spell\n"
            "bite = spell(id=17253, name='Bite', school=1)\n"
            "retire_pet_spell(bite, families=[3, 2, 3])\n"
            "retire_pet_spell(2649)\n"
        )
        self.assertEqual(
            [(r["spell_id"], r["families"]) for r in reg.pet_spell_retirements], [(17253, (2, 3)), (2649, None)],
        )

    def test_duplicate_retirement_is_a_duplicate_id_error(self):
        # Same (spell, families) declared in two files merges as a DuplicateIdError in load_classes_dir.
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text("from lib.dsl.registry import retire_pet_spell\nretire_pet_spell(2649)\n")
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d))

    def test_shared_lines_flag_is_recorded_and_part_of_the_id(self):
        reg = self._load(
            "from lib.dsl.registry import retire_pet_spell\n"
            "retire_pet_spell(1742, families=[2, 3], shared_lines=True)\n"
            "retire_pet_spell(2649, shared_lines=True)\n"
        )
        self.assertEqual([(r["families"], r["shared_lines"]) for r in reg.pet_spell_retirements],
                         [((2, 3), True), (None, False)])
        self.assertEqual(reg.pet_spell_retirements[0]["id"], "1742:2,3+shared")

    def test_empty_family_list_is_an_error(self):
        with self.assertRaises(ValueError):
            self._load("from lib.dsl.registry import retire_pet_spell\nretire_pet_spell(2649, families=[])\n")


if __name__ == "__main__":
    unittest.main()
