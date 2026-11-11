"""
enchant() / suffix() / gem() / enchant_condition() and their override_*() forms (crafting rework C1,
lib/dsl/enchants.py): the four DBC formats (SpellItemEnchantment, ItemRandomSuffix, GemProperties,
SpellItemEnchantmentCondition), the `*_dbc` SPELL_TABLES entries they feed, the patch-Z client rows
(lib/enchant_tables.py), the cross-reference check and the drop guard's knowledge of the files. No test declares real
content: every declaration here is a fixture.

The tests that need the stock client files (var/extractors/dbc/<name>.dbc, copied from the worldserver's DBC directory)
are skipped when they are missing; the rest run on fixture rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_enchant_tables.py
"""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402,F401  (the module generate.py wires these tables through must import)
from lib import dbcfile, dbcfmt, drop_guard, enchant_tables, source, spell_tables, state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.dsl.constants import GemColor  # noqa: E402
from lib.table_testkit import (  # noqa: E402
    codestyle_sql, generated_file, index_for, load_dsl, read_back, render, spec_for,
)

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")

HEAD = (
    "from lib.dsl.enchants import (\n"
    "    enchant, stat_enchant, stat_effect, resistance_effect, spell_effect, socket_effect, suffix, gem,\n"
    "    enchant_condition, gems_at_least, gems_more_than, gems_fewer_than, override_enchant, override_suffix,\n"
    "    override_gem, override_enchant_condition,\n"
    ")\n"
    "from lib.dsl.registry import EnchantType, GemColor, ItemMod\n"
)
# One fixture declaration of every kind: two suffix parts, the suffix, a meta-style condition, a gem bonus that names it
# (an apostrophe in a name checks the SQL escaping) and the gem.
FIXTURE = HEAD + (
    "crit = stat_enchant(5000, ItemMod.CRIT_RATING)\n"
    "mastery = stat_enchant(5001, ItemMod.MASTERY_RATING)\n"
    "suffix(1000, \"of the Tiger's Claw\", 'Tiger', (crit, 6666), (mastery, 10000))\n"
    "need = enchant_condition(1000, gems_at_least(GemColor.RED, 2), gems_at_least(GemColor.BLUE, GemColor.YELLOW))\n"
    "ruby = stat_enchant(5100, ItemMod.STRENGTH, 12, src_item=71234, condition=need)\n"
    "gem(2000, ruby, GemColor.RED)\n"
)

# (the DbcTable, the SQL table, the Registry list)
TABLES = (
    (dbcfmt.SPELLITEMENCHANTMENT, "spellitemenchantment_dbc", "spell_item_enchantments"),
    (dbcfmt.ITEMRANDOMSUFFIX, "itemrandomsuffix_dbc", "item_random_suffixes"),
    (dbcfmt.GEMPROPERTIES, "gemproperties_dbc", "gem_properties"),
    (dbcfmt.SPELLITEMENCHANTMENTCONDITION, "spellitemenchantmentcondition_dbc", "enchant_conditions"),
)
BLOCK_NAMES = {"SpellItemEnchantment": "spellitemenchantment", "ItemRandomSuffix": "itemrandomsuffix",
               "GemProperties": "gemproperties", "SpellItemEnchantmentCondition": "spellitemenchantmentcondition"}


def _stock_files_present() -> bool:
    return all((state.BASE_DBC_DIR / t.dbc_filename).is_file() for t, _s, _k in TABLES)


def _empty_stock(table):
    return {}


def _bundle(**rows) -> dict:
    """A live-data bundle with fixture stock rows per table (keyword = the bundle key)."""
    return spell_tables.dsl_live_data({}, {}, **rows)


def _load(text: str, **live) -> dict:
    return load_dsl(text, ids_cfg=IDS, live_data=_bundle(**live))


# One stock row per table, shaped like the real ones (for the override tests that must not need the client files).
def _row(table, **columns):
    row = dbcfile.empty_row(table)
    row.update(columns)
    return row


FIXTURE_STOCK = {
    "spellitemenchantment_rows": {2686: _row(dbcfmt.SPELLITEMENCHANTMENT, ID=2686, Effect_1=5, EffectPointsMin_1=8,
                                             EffectPointsMax_1=8, EffectArg_1=4, Name_Lang_enUS="+8 Strength",
                                             Name_Lang_Mask=16712190, Src_ItemID=23233)},
    "itemrandomsuffix_rows": {5: _row(dbcfmt.ITEMRANDOMSUFFIX, ID=5, Name_Lang_enUS="of the Monkey",
                                      Name_Lang_Mask=16712190, InternalName="Monkey", Enchantment_1=2802,
                                      Enchantment_2=2803, AllocationPct_1=6666, AllocationPct_2=10000)},
    "gemproperties_rows": {2: _row(dbcfmt.GEMPROPERTIES, ID=2, Enchant_Id=2686, Type=2)},
    "spellitemenchantmentcondition_rows": {3: _row(dbcfmt.SPELLITEMENCHANTMENTCONDITION, ID=3, Lt_OperandType_1=4,
                                                   Operator_1=5, Rt_Operand_1=4)},
}


class FormatTest(unittest.TestCase):
    def test_every_fmt_is_dbcfmt_h(self):
        self.assertEqual(dbcfmt.SPELLITEMENCHANTMENT.fmt, "niiiiiiixxxiiissssssssssssssssxiiiiiii")
        self.assertEqual(dbcfmt.ITEMRANDOMSUFFIX.fmt, "nssssssssssssssssxxiiiiiiiiii")
        self.assertEqual(dbcfmt.GEMPROPERTIES.fmt, "nixxi")
        self.assertEqual(dbcfmt.SPELLITEMENCHANTMENTCONDITION.fmt, "nbbbbbxxxxxbbbbbbbbbbiiiiiXXXXX")

    def test_the_columns_are_the_base_create_table(self):
        for table, sql_table, _key in TABLES:
            with self.subTest(table=table.name):
                created = spell_tables.sql_dump.parse_create_table_columns(
                    spell_tables.trainer_state.BASE_SQL_DIR / f"{sql_table}.sql", sql_table,
                )
                self.assertEqual(tuple(created), table.columns)

    def test_the_condition_record_is_64_unaligned_bytes(self):
        table = dbcfmt.SPELLITEMENCHANTMENTCONDITION
        self.assertEqual(dbcfile.record_size(table), 64)
        row = _row(table, ID=7, Lt_OperandType_1=2, Lt_OperandType_5=4, Operator_1=5, Operator_5=3, Rt_OperandType_5=3,
                   Rt_Operand_1=9, Rt_Operand_5=0x01020304, Logic_1=1, Logic_4=1)
        blob = dbcfile.pack_dbc_bytes(table, [row])
        self.assertEqual(struct.unpack_from("<4sIIII", blob, 0), (b"WDBC", 1, 31, 64, 1))
        record = blob[20:84]
        self.assertEqual(struct.unpack_from("<I", record, 0)[0], 7)
        self.assertEqual(list(record[4:9]), [2, 0, 0, 0, 4])  # Lt_OperandType[5]
        self.assertEqual(record[9:29], bytes(20))  # Lt_Operand[5], uint32 and unused
        self.assertEqual(list(record[29:34]), [5, 0, 0, 0, 3])  # Operator[5]
        self.assertEqual(list(record[34:39]), [0, 0, 0, 0, 3])  # Rt_OperandType[5]
        self.assertEqual(struct.unpack_from("<5I", record, 39), (9, 0, 0, 0, 0x01020304))  # Rt_Operand[5]
        self.assertEqual(list(record[59:64]), [1, 0, 0, 1, 0])  # Logic[5]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / table.dbc_filename
            path.write_bytes(blob)
            self.assertEqual(dbcfile.read_dbc(path, table), [row])

    def test_a_byte_column_wraps_at_8_bits_not_32(self):
        table = dbcfmt.SPELLITEMENCHANTMENTCONDITION
        blob = dbcfile.pack_dbc_bytes(table, [_row(table, ID=1, Operator_1=300, Logic_1="2")])
        self.assertEqual(blob[20 + 29], 300 & 0xFF)
        self.assertEqual(blob[20 + 59], 2)

    def test_the_string_tables_keep_their_strings(self):
        for table in (dbcfmt.SPELLITEMENCHANTMENT, dbcfmt.ITEMRANDOMSUFFIX):
            row = _row(table, ID=9, Name_Lang_enUS="of the Tiger", Name_Lang_Mask=16712190)
            if table is dbcfmt.ITEMRANDOMSUFFIX:
                row["InternalName"] = "Tiger"
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / table.dbc_filename
                path.write_bytes(dbcfile.pack_dbc_bytes(table, [row]))
                self.assertEqual(dbcfile.read_dbc(path, table), [row])


@unittest.skipUnless(_stock_files_present(), "the four stock client DBCs are not extracted into var/extractors/dbc")
class StockFileTest(unittest.TestCase):
    def test_every_stock_file_repacks_byte_identical(self):
        for table, _sql, _key in TABLES:
            with self.subTest(table=table.name):
                path = state.BASE_DBC_DIR / table.dbc_filename
                rows = dbcfile.read_dbc(path, table)
                self.assertEqual(dbcfile.pack_client_dbc(table, rows, rows), path.read_bytes())

    def test_known_stock_rows(self):
        enchants = state.load_stock_rows(dbcfmt.SPELLITEMENCHANTMENT)
        self.assertEqual((len(enchants), max(enchants)), (2656, 3883))
        self.assertEqual(enchants[2686]["Name_Lang_enUS"], "+8 Strength")
        self.assertEqual(enchants[3726]["Name_Lang_enUS"], "+$i Haste Rating")  # a suffix part: $i, amount 0
        self.assertEqual(enchants[27]["EffectPointsMin_1"], -10)  # a negative amount reads signed
        self.assertEqual(enchants[2605]["ItemVisual"], -1)
        suffixes = state.load_stock_rows(dbcfmt.ITEMRANDOMSUFFIX)
        self.assertEqual((len(suffixes), max(suffixes)), (95, 99))
        self.assertEqual(suffixes[5]["Name_Lang_enUS"], "of the Monkey")
        self.assertEqual(suffixes[5]["InternalName"], "Monkey")
        self.assertEqual((suffixes[5]["Enchantment_1"], suffixes[5]["AllocationPct_1"]), (2802, 6666))
        gems = state.load_stock_rows(dbcfmt.GEMPROPERTIES)
        self.assertEqual((len(gems), max(gems)), (626, 1629))
        self.assertEqual((gems[2]["Enchant_Id"], gems[2]["Type"]), (2686, 2))
        conditions = state.load_stock_rows(dbcfmt.SPELLITEMENCHANTMENTCONDITION)
        self.assertEqual((len(conditions), max(conditions)), (49, 194))

    def test_the_proposed_blocks_are_clear_of_every_stock_id(self):
        for table, _sql, _key in TABLES:
            block = IDS[BLOCK_NAMES[table.name]]
            with self.subTest(table=table.name):
                stock = state.load_stock_rows(table)
                self.assertFalse([i for i in stock if block["start"] <= i <= block["end"]])

    def test_a_suffix_id_fits_the_smallint_item_instance_stores_it_in(self):
        self.assertLess(IDS["itemrandomsuffix"]["end"], 32768)  # item_instance.randomPropertyId is smallint (-id)

    def test_the_hand_built_conditions_equal_stock_rows(self):
        stock = state.load_stock_rows(dbcfmt.SPELLITEMENCHANTMENTCONDITION)
        cases = {
            3: "gems_at_least(GemColor.BLUE, 4)",
            36: "gems_at_least(GemColor.RED, 2), gems_at_least(GemColor.YELLOW, 2), gems_at_least(GemColor.BLUE, 2)",
            28: "gems_fewer_than(GemColor.META, GemColor.RED), gems_fewer_than(GemColor.RED, GemColor.YELLOW)",
        }
        for stock_id, clauses in cases.items():
            with self.subTest(stock_id=stock_id):
                (built,) = _load(HEAD + f"enchant_condition(1000, {clauses})\n")["enchant_conditions"]
                self.assertEqual({c: v for c, v in built.items() if c in dbcfmt.SPELLITEMENCHANTMENTCONDITION.columns
                                  and c != "ID"},
                                 {c: v for c, v in stock[stock_id].items() if c != "ID"})

    def test_stock_names_for_the_stat_defaults(self):
        stock = state.load_stock_rows(dbcfmt.SPELLITEMENCHANTMENT)
        # the generated "+N <stat>" text reads like the stock text for the stats stock enchants carry
        self.assertEqual(stock[2687]["Name_Lang_enUS"], "+8 Agility")
        self.assertEqual(stock[3865]["Name_Lang_enUS"], "+20 Intellect")
        (row,) = _load(HEAD + "stat_enchant(5000, ItemMod.AGILITY, 8)\n")["spell_item_enchantments"]
        self.assertEqual(row["Name_Lang_enUS"], stock[2687]["Name_Lang_enUS"])


class DeclarationTest(unittest.TestCase):
    def test_the_fixture_builds_full_rows(self):
        dsl = _load(FIXTURE)
        enchants = {r["ID"]: r for r in dsl["spell_item_enchantments"]}
        self.assertEqual(set(enchants), {5000, 5001, 5100})
        crit = enchants[5000]
        self.assertEqual((crit["Effect_1"], crit["EffectArg_1"], crit["EffectPointsMin_1"], crit["EffectPointsMax_1"]),
                         (5, 32, 0, 0))
        self.assertEqual(crit["Name_Lang_enUS"], "+$i Critical Strike Rating")
        self.assertEqual(crit["Name_Lang_Mask"], 16712190)
        self.assertEqual(enchants[5001]["EffectArg_1"], 22)  # Mastery Rating
        ruby = enchants[5100]
        self.assertEqual((ruby["Name_Lang_enUS"], ruby["EffectPointsMin_1"], ruby["EffectPointsMax_1"]),
                         ("+12 Strength", 12, 12))
        self.assertEqual((ruby["Src_ItemID"], ruby["Condition_Id"]), (71234, 1000))
        for row in dsl["spell_item_enchantments"]:
            self.assertEqual(set(dbcfmt.SPELLITEMENCHANTMENT.columns) - set(row), set())
            self.assertIs(type(row["Effect_1"]), int)  # an IntEnum is stored as a plain int
        (suf,) = dsl["item_random_suffixes"]
        self.assertEqual((suf["ID"], suf["Name_Lang_enUS"], suf["InternalName"]),
                         (1000, "of the Tiger's Claw", "Tiger"))
        self.assertEqual([suf[f"Enchantment_{i}"] for i in range(1, 6)], [5000, 5001, 0, 0, 0])
        self.assertEqual([suf[f"AllocationPct_{i}"] for i in range(1, 6)], [6666, 10000, 0, 0, 0])
        (gp,) = dsl["gem_properties"]
        self.assertEqual({c: gp[c] for c in dbcfmt.GEMPROPERTIES.columns},
                         {"ID": 2000, "Enchant_Id": 5100, "Maxcount_Inv": 0, "Maxcount_Item": 0, "Type": 2})
        (cond,) = dsl["enchant_conditions"]
        self.assertEqual([cond[f"Lt_OperandType_{i}"] for i in range(1, 6)], [2, 4, 0, 0, 0])
        self.assertEqual([cond[f"Operator_{i}"] for i in range(1, 6)], [5, 5, 0, 0, 0])
        self.assertEqual([cond[f"Rt_OperandType_{i}"] for i in range(1, 6)], [0, 3, 0, 0, 0])
        self.assertEqual([cond[f"Rt_Operand_{i}"] for i in range(1, 6)], [2, 0, 0, 0, 0])
        self.assertEqual([cond[f"Logic_{i}"] for i in range(1, 6)], [1, 0, 0, 0, 0])

    def test_other_effect_kinds_and_names(self):
        dsl = _load(HEAD + (
            "enchant(5200, 'Fiery Weapon', spell_effect(EnchantType.COMBAT_SPELL, 13897, 6), item_visual=563,"
            " flags=1)\n"
            "enchant(5201, '+30 Arcane Resistance', resistance_effect(6, 30))\n"
            "enchant(5202, 'Eternal Belt Buckle', socket_effect())\n"
            "enchant(5203, 'Two Stats', stat_effect(ItemMod.SPELL_POWER, 70),"
            " stat_effect(ItemMod.MANA_REGENERATION, 8), min_level=20, required_skill=773, required_skill_rank=400)\n"
            "stat_enchant(5204, ItemMod.VERSATILITY_RATING, 9, name='Custom text')\n"
            "stat_enchant(5205, ItemMod.COOLDOWN_RATING, -3)\n"
            "stat_enchant(5206, ItemMod.PROC_RATING)\n"
        ))
        rows = {r["ID"]: r for r in dsl["spell_item_enchantments"]}
        fiery = rows[5200]
        self.assertEqual((fiery["Effect_1"], fiery["EffectArg_1"], fiery["EffectPointsMin_1"], fiery["ItemVisual"],
                          fiery["Flags"]), (1, 13897, 6, 563, 1))
        self.assertEqual((rows[5201]["Effect_1"], rows[5201]["EffectArg_1"]), (4, 6))
        self.assertEqual((rows[5202]["Effect_1"], rows[5202]["EffectPointsMin_1"]), (8, 1))
        two = rows[5203]
        self.assertEqual((two["Effect_2"], two["EffectArg_2"], two["EffectPointsMax_2"], two["Effect_3"]),
                         (5, 43, 8, 0))
        self.assertEqual((two["MinLevel"], two["RequiredSkillID"], two["RequiredSkillRank"]), (20, 773, 400))
        self.assertEqual(rows[5204]["Name_Lang_enUS"], "Custom text")
        self.assertEqual(rows[5205]["Name_Lang_enUS"], "-3 Cooldown Haste Rating")
        self.assertEqual(rows[5206]["Name_Lang_enUS"], "+$i Proc Chance Rating")

    def test_the_four_custom_stats_are_named(self):
        from lib.dsl.enchants import STAT_NAMES  # noqa: PLC0415

        self.assertEqual({k: STAT_NAMES[k] for k in (22, 23, 24, 33)},
                         {22: "Mastery Rating", 23: "Versatility Rating", 24: "Cooldown Haste Rating",
                          33: "Proc Chance Rating"})

    def test_a_declaration_accepts_ids_where_it_would_take_a_row(self):
        dsl = _load(HEAD + (
            "stat_enchant(5000, ItemMod.CRIT_RATING)\nsuffix(1000, 'of X', 'X', (5000, 10000))\n"
            "gem(2000, 5000, GemColor.META)\nenchant(5001, 'Needs', stat_effect(ItemMod.STAMINA, 1), condition=1000)\n"
        ))
        self.assertEqual(dsl["item_random_suffixes"][0]["Enchantment_1"], 5000)
        self.assertEqual(dsl["gem_properties"][0]["Type"], 1)
        self.assertEqual(dsl["spell_item_enchantments"][1]["Condition_Id"], 1000)

    def test_gem_colors(self):
        for color, ok in ((1, True), (2, True), (4, True), (6, True), (8, True), (10, True), (12, True), (14, True),
                          (0, False), (3, False), (5, False), (7, False), (9, False), (15, False), (16, False)):
            with self.subTest(color=color):
                text = HEAD + f"gem(2000, 5000, {color})\n"
                if ok:
                    self.assertEqual(_load(text)["gem_properties"][0]["Type"], color)
                else:
                    with self.assertRaisesRegex(ValueError, "color"):
                        _load(text)

    def test_errors(self):
        def bad(body: str, pattern: str, error=ValueError, **live):
            with self.subTest(body=body), self.assertRaisesRegex(error, pattern):
                _load(HEAD + body, **live)

        bad("enchant(4999, 'x', stat_effect(ItemMod.STAMINA, 1))\n", "outside source/ids.yaml's spellitemenchantment")
        bad("enchant(3883, 'x', stat_effect(ItemMod.STAMINA, 1))\n", "outside source/ids.yaml's spellitemenchantment")
        bad("enchant(5000, 'x')\n", "needs 1 to 3 effects")
        bad("enchant(5000, 'x', *[stat_effect(ItemMod.STAMINA, 1)] * 4)\n", "needs 1 to 3 effects")
        bad("enchant(5000, 'x', (5, 7, 1))\n", "effect 1 must come from")
        bad("enchant(5000, 'a\\nb', stat_effect(ItemMod.STAMINA, 1))\n", "one-line")
        bad("enchant(5000, '', stat_effect(ItemMod.STAMINA, 1))\n", "one-line")
        bad("enchant(5000, 'x' * 101, stat_effect(ItemMod.STAMINA, 1))\n", "at most 100")
        bad("enchant(5000, 'x', stat_effect(ItemMod.STAMINA, 1), condition=-4)\n", "positive id")
        bad("enchant(5000, 'x', stat_effect(ItemMod.STAMINA, 1), min_level=-1)\n", "min_level")
        bad("enchant(5000, 'x', stat_effect(ItemMod.STAMINA, 1), flags=True)\n", "flags")
        bad("stat_effect(2, 1)\n", "not a stat an enchant can carry")
        bad("stat_effect(ItemMod.STAMINA, 1.5)\n", "amount")
        bad("resistance_effect(7, 1)\n", "school")
        bad("spell_effect(EnchantType.STAT, 1)\n", "EQUIP_SPELL")
        bad("spell_effect(EnchantType.USE_SPELL, 0)\n", "spell id")
        bad("suffix(999, 'of X', 'X', (1, 10000))\n", "outside source/ids.yaml's itemrandomsuffix")
        bad("suffix(1000, 'of X', 'X')\n", "needs 1 to 5")
        bad("suffix(1000, 'of X', 'X', *[(i, 100) for i in range(1, 7)])\n", "needs 1 to 5")
        bad("suffix(1000, 'of X', 'X', (5000, 0))\n", "allocation_pct")
        bad("suffix(1000, 'of X', 'X', (5000, 20001))\n", "allocation_pct")
        bad("suffix(1000, 'of X', 'X', (5000, 5000), (5000, 5000))\n", "listed twice")
        bad("suffix(1000, 'of X', 'X', 5000)\n", "pair")
        bad("suffix(1000, 'of X', '', (5000, 100))\n", "internal_name")
        bad("gem(1999, 5000, GemColor.RED)\n", "outside source/ids.yaml's gemproperties")
        bad("gem(2000, 0, GemColor.RED)\n", "positive id")
        bad("gem(2000, 5000, GemColor.RED, max_count_inv=-1)\n", "max_count_inv")
        bad("enchant_condition(1100, gems_at_least(GemColor.RED, 1))\n", "outside source/ids.yaml's spellitem")
        bad("enchant_condition(1000)\n", "needs 1 to 5 clauses")
        bad("enchant_condition(1000, *[gems_at_least(GemColor.RED, 1)] * 6)\n", "needs 1 to 5 clauses")
        bad("enchant_condition(1000, (2, 5, 0, 1))\n", "clause 1 must come from")
        bad("gems_at_least(GemColor.ORANGE, 1)\n", "pure color|one of GemColor.META")
        bad("gems_at_least(GemColor.RED, GemColor.GREEN)\n", "pure color")
        bad("gems_at_least(GemColor.RED, 256)\n", "count")
        bad("gems_at_least(GemColor.RED, -1)\n", "count")

    def test_a_missing_block_in_ids_raises(self):
        with self.assertRaisesRegex(ValueError, "needs source/ids.yaml's `spellitemenchantment` block"):
            load_dsl(HEAD + "enchant(5000, 'x', stat_effect(ItemMod.STAMINA, 1))\n", ids_cfg={}, live_data=_bundle())

    def test_the_same_id_twice_is_a_duplicate(self):
        for body in ("enchant(5000, 'a', stat_effect(ItemMod.STAMINA, 1))\n" * 2,
                     "suffix(1000, 'of X', 'X', (5000, 100))\n" * 2,
                     "gem(2000, 5000, GemColor.RED)\n" * 2,
                     "enchant_condition(1000, gems_at_least(GemColor.RED, 1))\n" * 2):
            with self.subTest(body=body), self.assertRaises(registry.DuplicateIdError):
                _load(HEAD + body)

    def test_the_same_id_in_two_files_is_a_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text(HEAD + "gem(2000, 5000, GemColor.RED)\n")
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d), ids_cfg=IDS, live_data=_bundle())

    def test_outside_a_load_the_helpers_raise(self):
        from lib.dsl import enchants  # noqa: PLC0415

        with self.assertRaises(RuntimeError):
            enchants.gem(2000, 5000, GemColor.RED)

    def test_registry_reexports(self):
        for name in ("ItemMod", "EnchantType", "GemColor", "GemCompare"):
            self.assertTrue(hasattr(registry, name), name)


class OverrideTest(unittest.TestCase):
    def test_each_override_starts_from_the_stock_row(self):
        dsl = _load(HEAD + (
            "override_enchant(2686, Name_Lang_enUS='+8 Might', EffectArg_1=ItemMod.MASTERY_RATING)\n"
            "override_suffix(5, AllocationPct_1=5000)\n"
            "override_gem(2, Type=GemColor.BLUE)\n"
            "override_enchant_condition(3, Rt_Operand_1=3)\n"
        ), **FIXTURE_STOCK)
        (e,) = dsl["spell_item_enchantments"]
        self.assertEqual(e, dict(FIXTURE_STOCK["spellitemenchantment_rows"][2686], Name_Lang_enUS="+8 Might",
                                 EffectArg_1=22, id=2686))
        (s,) = dsl["item_random_suffixes"]
        self.assertEqual(s, dict(FIXTURE_STOCK["itemrandomsuffix_rows"][5], AllocationPct_1=5000, id=5))
        (g,) = dsl["gem_properties"]
        self.assertEqual(g, dict(FIXTURE_STOCK["gemproperties_rows"][2], Type=8, id=2))
        self.assertIs(type(g["Type"]), int)
        (c,) = dsl["enchant_conditions"]
        self.assertEqual(c, dict(FIXTURE_STOCK["spellitemenchantmentcondition_rows"][3], Rt_Operand_1=3, id=3))

    def test_errors(self):
        head = HEAD

        def bad(body, pattern, error=ValueError, **live):
            with self.subTest(body=body), self.assertRaisesRegex(error, pattern):
                _load(head + body, **(live or FIXTURE_STOCK))

        bad("override_enchant(2686, Nope=1)\n", "no such column", KeyError)
        bad("override_enchant(999, Name_Lang_enUS='x')\n", "no stock SpellItemEnchantment row for id 999")
        bad("override_suffix(999, InternalName='x')\n", "no stock ItemRandomSuffix row")
        bad("override_gem(999, Type=2)\n", "no stock GemProperties row")
        bad("override_enchant_condition(999, Operator_1=2)\n", "no stock SpellItemEnchantmentCondition row")
        bad("override_enchant(2686, ID=2687)\n", "ID column is the key")
        bad("override_enchant(2686, Name_Lang_enUS=5)\n", "must be a str")
        bad("override_enchant(2686, EffectArg_1='4')\n", "must be an int")
        bad("override_enchant(2686, EffectArg_1=True)\n", "must be an int")
        bad("override_enchant(2686, EffectArg_1=None)\n", "must be an int")
        bad("override_enchant(2686, Flags=1)\noverride_enchant(2686, Flags=2)\n", "declared twice",
            registry.DuplicateIdError)

    def test_a_missing_stock_file_raises_the_error_generate_prints(self):
        with self.assertRaisesRegex(registry.MissingStockFileError, "SpellItemEnchantment.dbc is missing"):
            _load(HEAD + "override_enchant(2686, Flags=1)\n", spellitemenchantment_rows={})
        with self.assertRaisesRegex(registry.MissingStockFileError, "GemProperties.dbc is missing"):
            _load(HEAD + "override_gem(2, Type=4)\n", gemproperties_rows={})

    def test_a_missing_bundle_raises(self):
        with self.assertRaisesRegex(RuntimeError, "override_enchant\\(\\) needs the live spellitemenchantment rows"):
            _load(HEAD + "override_enchant(2686, Flags=1)\n")

    def test_the_lazy_bundle_entries_are_not_loaded_unless_a_helper_runs(self):
        def boom():
            raise AssertionError("a stock enchant table must not load when no file overrides a row")

        live = {f"{k}": boom for k in ("spellitemenchantment_rows", "itemrandomsuffix_rows", "gemproperties_rows",
                                       "spellitemenchantmentcondition_rows")}
        _load(FIXTURE, **live)  # declaring new rows never reads the stock files

    @unittest.skipUnless(_stock_files_present(), "the four stock client DBCs are not extracted")
    def test_real_stock_overrides_keep_every_other_column(self):
        live = {key: (lambda t=t: state.load_stock_rows(t)) for key, t in (
            ("spellitemenchantment_rows", dbcfmt.SPELLITEMENCHANTMENT),
            ("itemrandomsuffix_rows", dbcfmt.ITEMRANDOMSUFFIX),
            ("gemproperties_rows", dbcfmt.GEMPROPERTIES),
            ("spellitemenchantmentcondition_rows", dbcfmt.SPELLITEMENCHANTMENTCONDITION))}
        # 27 is the one stock enchant with a negative amount: the override must keep it signed
        dsl = _load(HEAD + "override_enchant(27, Flags=9)\noverride_gem(2, Type=GemColor.GREEN)\n"
                    "override_suffix(10, AllocationPct_2=5000)\noverride_enchant_condition(28, Logic_1=0)\n", **live)
        stock = state.load_stock_rows(dbcfmt.SPELLITEMENCHANTMENT)[27]
        (e,) = dsl["spell_item_enchantments"]
        self.assertEqual(e["EffectPointsMin_1"], -10)
        self.assertEqual({c for c in e if c != "id" and e[c] != stock[c]}, {"Flags"})


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load(FIXTURE)

    def blocks(self):
        return {sql: render(sql, index_for(sql, []), self.dsl[key]) for _t, sql, key in TABLES}

    def test_every_table_renders_the_full_row_in_column_order(self):
        for table, sql_table, key in TABLES:
            block = self.blocks()[sql_table]
            ids = ", ".join(f"({r['ID']})" for r in sorted(self.dsl[key], key=lambda r: r["ID"]))
            cols = ", ".join(f"`{c}`" for c in table.columns)
            with self.subTest(table=sql_table):
                self.assertTrue(block.startswith(f"DELETE FROM `{sql_table}` WHERE (`ID`) IN ({ids});"), block[:120])
                self.assertIn(f"INSERT INTO `{sql_table}` ({cols}) VALUES", block)

    def test_the_apostrophe_is_escaped(self):
        self.assertIn("of the Tiger''s Claw", self.blocks()["itemrandomsuffix_dbc"].replace("\\'", "''"))

    def test_the_blocks_pass_the_real_sql_codestyle_check(self):
        for sql_table, block in self.blocks().items():
            with self.subTest(table=sql_table):
                done = codestyle_sql(block)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_a_rerun_over_the_read_back_rows_emits_nothing(self):
        for table, sql_table, key in TABLES:
            block = self.blocks()[sql_table]
            live = read_back(block, sql_table, table.columns)
            with self.subTest(table=sql_table):
                self.assertEqual(len(live), len(self.dsl[key]))
                self.assertEqual(render(sql_table, index_for(sql_table, live), self.dsl[key]), "")

    def test_a_changed_declaration_re_emits_only_that_row(self):
        block = self.blocks()["spellitemenchantment_dbc"]
        live = read_back(block, "spellitemenchantment_dbc", dbcfmt.SPELLITEMENCHANTMENT.columns)
        changed = _load(FIXTURE.replace("ItemMod.STRENGTH, 12", "ItemMod.STRENGTH, 14"))
        again = render("spellitemenchantment_dbc", index_for("spellitemenchantment_dbc", live),
                       changed["spell_item_enchantments"])
        self.assertTrue(again.startswith("DELETE FROM `spellitemenchantment_dbc` WHERE (`ID`) IN ((5100));"), again)
        self.assertIn("+14 Strength", again)
        self.assertNotIn("+$i", again)

    def test_a_dropped_declaration_is_pruned(self):
        for table, sql_table, key in TABLES:
            block = self.blocks()[sql_table]
            with self.subTest(table=sql_table), generated_file(block):
                emitted = spell_tables.load_generated_table_rows(sql_table, spec_for(sql_table).key_columns)
                self.assertEqual(sorted(int(r["ID"]) for r in emitted), sorted(r["ID"] for r in self.dsl[key]))
                result = index_for(sql_table, emitted, emitted=emitted).rows_to_prune(spec_for(sql_table), [])
                self.assertEqual(sorted(k[0] for k in result.keys), sorted(float(r["ID"]) for r in self.dsl[key]))
                self.assertFalse(result.breaker_tripped)

    def test_the_last_dropped_declaration_still_prunes(self):
        for _t, sql_table, _k in TABLES:
            self.assertTrue(spec_for(sql_table).prune_when_empty, sql_table)

    def test_the_prune_says_why(self):
        for _t, sql_table, _k in TABLES:
            self.assertIn(sql_table, spell_tables._PRUNE_WHY)

    def test_the_tables_are_registered_for_the_replay_check(self):
        from lib import replay_diff  # noqa: PLC0415

        for _t, sql_table, _k in TABLES:
            self.assertIn(sql_table, replay_diff.REPLAYED_TABLES)

    def test_declaring_nothing_emits_nothing(self):
        empty = _load("x = 1\n")
        for _t, sql_table, key in TABLES:
            self.assertEqual(empty[key], [])
            self.assertEqual(render(sql_table, index_for(sql_table, []), empty[key]), "")


class ClientRowsTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load(FIXTURE)

    def test_the_client_rows_are_the_dbc_shape(self):
        for table, _sql, key in TABLES:
            rows = enchant_tables.client_rows(table, self.dsl[key])
            with self.subTest(table=table.name):
                self.assertEqual(set(rows), {r["ID"] for r in self.dsl[key]})
                for row in rows.values():
                    self.assertEqual(tuple(row), table.columns)  # no bookkeeping key ("id") leaks in

    def test_generate_ships_all_four(self):
        self.assertEqual([t for t, _k in enchant_tables.TABLES], [t for t, _s, _k in TABLES])
        self.assertTrue(enchant_tables.declared_any(self.dsl))
        self.assertFalse(enchant_tables.declared_any(_load("x = 1\n")))

    @unittest.skipUnless(_stock_files_present(), "the four stock client DBCs are not extracted")
    def test_the_merged_files_round_trip_and_keep_every_stock_row(self):
        for table, _sql, key in TABLES:
            path = state.BASE_DBC_DIR / table.dbc_filename
            base_rows = dbcfile.read_dbc(path, table)
            merged = {row[table.index_column]: row for row in base_rows}
            new = enchant_tables.client_rows(table, self.dsl[key])
            merged.update(new)
            packed = dbcfile.pack_client_dbc(table, list(merged.values()), base_rows)
            with tempfile.TemporaryDirectory() as d:
                copy = Path(d) / table.dbc_filename
                copy.write_bytes(packed)
                back = {r["ID"]: r for r in dbcfile.read_dbc(copy, table)}
            with self.subTest(table=table.name):
                self.assertEqual(len(back), len(base_rows) + len(new))
                for row_id, row in new.items():
                    self.assertEqual(back[row_id], row)
                for row in base_rows:
                    self.assertEqual(back[row["ID"]], row)

    @unittest.skipUnless(_stock_files_present(), "the four stock client DBCs are not extracted")
    def test_an_override_replaces_the_stock_row_and_nothing_else(self):
        table = dbcfmt.SPELLITEMENCHANTMENT
        path = state.BASE_DBC_DIR / table.dbc_filename
        base_rows = dbcfile.read_dbc(path, table)
        live = {"spellitemenchantment_rows": state.load_stock_rows(table)}
        dsl = _load(HEAD + "override_enchant(3726, Name_Lang_enUS='+$i Haste')\n", **live)
        merged = {row["ID"]: row for row in base_rows}
        merged.update(enchant_tables.client_rows(table, dsl["spell_item_enchantments"]))
        self.assertEqual(len(merged), len(base_rows))
        changed = [i for i, r in merged.items() if r != next(b for b in base_rows if b["ID"] == i)]
        self.assertEqual(changed, [3726])


def _stock(**tables):
    """A `load_stock` for `enchant_tables.check`: `{table name: {id: row}}`; a table not given is a missing file."""
    def load(table):
        if table.name not in tables:
            raise enchant_tables.MissingStockFile(table)
        return tables[table.name]

    return load


def _enchant_stock(*rows):
    return {r["ID"]: r for r in rows}


class CheckTest(unittest.TestCase):
    """Dangling references, the gem and suffix part gotchas, and what a missing stock file does."""

    FULL = {"SpellItemEnchantment": {}, "SpellItemEnchantmentCondition": {}, "ItemRandomSuffix": {}}

    def run_check(self, text: str, stock=None, items=None, pool=()):
        dsl = _load(text)
        return enchant_tables.check(dsl, pool_rows=list(pool), items=items or {},
                                    load_stock=_stock(**(self.FULL if stock is None else stock)))

    def test_the_fixture_is_closed(self):
        self.assertEqual(self.run_check(FIXTURE), ([], []))

    def test_a_suffix_part_naming_nothing(self):
        (problem,), _w = self.run_check(HEAD + "suffix(1000, 'of X', 'X', (5000, 10000))\n")
        self.assertIn("suffix 1000", problem)
        self.assertIn("enchant 5000", problem)

    def test_a_stock_enchant_is_fine_and_a_missing_one_is_not(self):
        text = HEAD + "suffix(1000, 'of X', 'X', (2802, 10000))\n"
        stat = _row(dbcfmt.SPELLITEMENCHANTMENT, ID=2802, Effect_1=5, EffectArg_1=3)
        stock = dict(self.FULL, SpellItemEnchantment=_enchant_stock(stat))
        self.assertEqual(self.run_check(text, stock), ([], []))
        errors, _w = self.run_check(text)
        self.assertEqual(len(errors), 1)
        self.assertIn("enchant 2802", errors[0])

    def test_a_gem_naming_nothing(self):
        (problem,), _w = self.run_check(HEAD + "gem(2000, 5000, GemColor.RED)\n")
        self.assertIn("gem 2000", problem)

    def test_an_enchant_naming_a_missing_condition(self):
        text = HEAD + "enchant(5000, 'Needs', stat_effect(ItemMod.STAMINA, 1), condition=1000)\n"
        (problem,), _w = self.run_check(text)
        self.assertIn("condition 1000", problem)
        stock = dict(self.FULL, SpellItemEnchantmentCondition={1000: {}})
        self.assertEqual(self.run_check(text, stock), ([], []))
        self.assertEqual(self.run_check(text + "enchant_condition(1000, gems_at_least(GemColor.RED, 1))\n"), ([], []))

    # --- S3: the gem and suffix part gotchas
    def test_a_gem_enchant_without_a_source_item_is_an_error(self):
        errors, _w = self.run_check(HEAD + "stat_enchant(5100, ItemMod.STRENGTH, 12)\ngem(2000, 5100, GemColor.RED)\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("Src_ItemID 0", errors[0])
        self.assertIn("meta gem", errors[0])

    def test_a_source_item_that_points_at_another_gem_is_an_error(self):
        text = HEAD + "stat_enchant(5100, ItemMod.STRENGTH, 12, src_item=71234)\ngem(2000, 5100, GemColor.RED)\n"
        self.assertEqual(self.run_check(text, items={71234: (0, 2000)}), ([], []))
        errors, _w = self.run_check(text, items={71234: (0, 2001)})
        self.assertEqual(len(errors), 1)
        self.assertIn("item 71234 has GemProperties 2001", errors[0])
        errors, _w = self.run_check(text, items={71234: (0, 0)})  # the item is a plain row that names no gem
        self.assertEqual(len(errors), 1)
        self.assertEqual(self.run_check(text, items={}), ([], []))  # an item nothing knows about is not judged

    def test_a_stock_gem_enchant_is_judged_too(self):
        stock = dict(self.FULL, SpellItemEnchantment=_enchant_stock(
            _row(dbcfmt.SPELLITEMENCHANTMENT, ID=2686, Effect_1=5, EffectArg_1=4, EffectPointsMin_1=8)))
        errors, _w = self.run_check(HEAD + "gem(2000, 2686, GemColor.RED)\n", stock)
        self.assertIn("Src_ItemID 0", errors[0])

    def test_a_suffix_part_with_a_flat_amount_is_an_error(self):
        errors, _w = self.run_check(
            HEAD + "stat_enchant(5000, ItemMod.CRIT_RATING, 12)\nsuffix(1000, 'of X', 'X', (5000, 10000))\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("flat amount 12", errors[0])
        self.assertIn("AllocationPct", errors[0])

    def test_a_suffix_part_with_an_effect_the_factor_cannot_scale_is_an_error(self):
        text = (HEAD + "enchant(5000, 'Fiery', spell_effect(EnchantType.COMBAT_SPELL, 13897, 6))\n"
                "enchant(5001, 'Slay', stat_effect(ItemMod.CRIT_RATING), spell_effect(EnchantType.USE_SPELL, 1))\n"
                "suffix(1000, 'of X', 'X', (5000, 5000), (5001, 5000))\n")
        errors, _w = self.run_check(text)
        self.assertEqual(len(errors), 2)
        self.assertTrue(all("cannot scale" in e for e in errors))

    def test_resistance_and_equip_spell_parts_are_allowed(self):
        text = HEAD + "enchant(5000, '+$i Fire Resistance', resistance_effect(2, 0))\n" \
                      "enchant(5001, 'Proc', spell_effect(EnchantType.EQUIP_SPELL, 13897))\n" \
                      "suffix(1000, 'of X', 'X', (5000, 5000), (5001, 5000))\n"
        self.assertEqual(self.run_check(text), ([], []))

    # --- B1: a missing stock file
    def test_nothing_declared_and_no_stock_files_is_clean_but_for_one_warning(self):
        errors, warnings = enchant_tables.check(_load("x = 1\n"), pool_rows=[{"entry": 61, "ench": 6}],
                                                items={5000: (61, 0)}, load_stock=_stock())
        self.assertEqual(errors, [])  # 715 live stock pool rows must not become 715 errors
        (warning,) = warnings
        self.assertIn("ItemRandomSuffix.dbc is missing", warning)
        self.assertIn("docker cp ac-worldserver:/azerothcore/env/dist/data/dbc/ItemRandomSuffix.dbc", warning)

    def test_a_declared_suffix_with_the_stock_file_missing_is_an_error_naming_the_file(self):
        errors, warnings = self.run_check(FIXTURE, {"SpellItemEnchantment": {}, "SpellItemEnchantmentCondition": {}})
        self.assertEqual(warnings, [])
        (error,) = errors
        self.assertIn("ItemRandomSuffix.dbc is missing", error)
        self.assertIn("docker cp", error)

    def test_a_reference_that_needs_a_missing_stock_file_names_the_file_once(self):
        text = HEAD + "suffix(1000, 'of X', 'X', (2802, 5000), (2803, 5000))\ngem(2000, 2686, GemColor.RED)\n"
        errors, _w = self.run_check(text, {"ItemRandomSuffix": {}})
        missing = [e for e in errors if "SpellItemEnchantment.dbc is missing" in e]
        self.assertEqual(len(missing), 1)
        self.assertFalse([e for e in errors if "neither declared nor" in e])  # no blame on the declarations

    def test_a_closed_declaration_set_needs_no_stock_file_but_the_suffix_one(self):
        errors, warnings = self.run_check(
            HEAD + "stat_enchant(5000, ItemMod.CRIT_RATING)\nsuffix(1000, 'of X', 'X', (5000, 10000))\n",
            {"ItemRandomSuffix": {}})
        self.assertEqual((errors, warnings), ([], []))

    def test_the_real_stock_loader_raises_for_an_absent_file(self):
        with tempfile.TemporaryDirectory() as d:
            load = enchant_tables.stock_loader(Path(d))
            with self.assertRaises(enchant_tables.MissingStockFile):
                load(dbcfmt.GEMPROPERTIES)

    def test_the_pool_check_through_the_real_loader_with_the_files_absent(self):
        with tempfile.TemporaryDirectory() as d:
            errors, warnings = enchant_tables.check(
                _load("x = 1\n"), pool_rows=[{"entry": 61, "ench": 6}], items={5000: (61, 0)},
                load_stock=enchant_tables.stock_loader(Path(d)),
            )
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)

    # --- the pool check proper (with the stock ids present)
    POOL = [{"entry": 900, "ench": 5}, {"entry": 900, "ench": 1000}, {"entry": 901, "ench": 9999}]

    def test_a_pool_ench_that_is_no_suffix_is_reported(self):
        stock = dict(self.FULL, ItemRandomSuffix={5: {}})
        errors, _w = self.run_check("x = 1\n", stock, items={1: (900, 0)}, pool=self.POOL)
        self.assertEqual(len(errors), 1)
        self.assertIn("pool 900: ench 1000", errors[0])

    def test_a_declared_suffix_satisfies_the_pool(self):
        text = HEAD + "stat_enchant(5000, ItemMod.CRIT_RATING)\nsuffix(1000, 'of X', 'X', (5000, 10000))\n"
        stock = dict(self.FULL, ItemRandomSuffix={5: {}})
        self.assertEqual(self.run_check(text, stock, items={1: (900, 0)}, pool=self.POOL), ([], []))

    def test_a_declared_item_names_its_pool(self):
        stock = dict(self.FULL, ItemRandomSuffix={5: {}})
        dsl = _load("x = 1\n")
        # a minted item (full row) and an item_template() edit that only touches RandomSuffix
        emission = type("E", (), {"template_rows": [{"entry": 71000, "RandomSuffix": 901, "GemProperties": 0}],
                                  "template_edits": [{"entry": 2000, "RandomSuffix": 900, "Name": "x",
                                                      "_update_columns": ("RandomSuffix",)}]})()
        items = enchant_tables.item_columns({2000: {"RandomSuffix": 0, "GemProperties": 5}}, emission,
                                            [{"entry": 3000, "RandomSuffix": 0, "_update_columns": ("Name",)}])
        self.assertEqual(items, {2000: (900, 5), 71000: (901, 0)})  # the edit keeps the live GemProperties
        errors, _w = enchant_tables.check(dsl, pool_rows=self.POOL, items=items, load_stock=_stock(**stock))
        self.assertEqual(len(errors), 2)  # pool 900 ench 1000 and pool 901 ench 9999
        self.assertIn("pool 901", errors[1])

    def test_item_columns_leaves_untouched_columns_alone(self):
        items = enchant_tables.item_columns(
            {1: {"RandomSuffix": 7, "GemProperties": 0}},
            None, [{"entry": 1, "RandomSuffix": 9, "GemProperties": 4, "_update_columns": ("GemProperties",)}])
        self.assertEqual(items, {1: (7, 4)})


class SuffixIdLimitTest(unittest.TestCase):
    """item_instance.randomPropertyId is a smallint holding -suffix id: no suffix id may exceed 32767."""

    def test_the_block_stays_inside_the_limit(self):
        self.assertLessEqual(IDS["itemrandomsuffix"]["end"], 32767)

    def test_a_declared_suffix_above_the_limit_is_refused_even_in_a_widened_block(self):
        widened = dict(IDS, itemrandomsuffix={"start": 32000, "end": 40000})
        ok = HEAD + "suffix(32767, 'of X', 'X', (5000, 100))\n"
        self.assertEqual(load_dsl(ok, ids_cfg=widened, live_data=_bundle())["item_random_suffixes"][0]["ID"], 32767)
        with self.assertRaisesRegex(ValueError, "32767"):
            load_dsl(HEAD + "suffix(32768, 'of X', 'X', (5000, 100))\n", ids_cfg=widened, live_data=_bundle())

    def test_every_declared_suffix_id_is_within_the_limit(self):
        for row in _load(FIXTURE)["item_random_suffixes"]:
            self.assertLessEqual(row["ID"], 32767)


class SuffixPoolTest(unittest.TestCase):
    POOL = [{"entry": 900, "ench": 5}, {"entry": 900, "ench": 1000}, {"entry": 901, "ench": 9999}]

    def test_a_pool_ench_that_is_no_suffix_is_reported(self):
        problems = enchant_tables.suffix_pool_problems(self.POOL, {900}, {5})
        self.assertEqual(len(problems), 1)
        self.assertIn("pool 900: ench 1000", problems[0])

    def test_a_declared_suffix_satisfies_the_pool(self):
        self.assertEqual(enchant_tables.suffix_pool_problems(self.POOL, {900}, {5, 1000}), [])

    def test_only_suffix_pools_are_checked(self):
        # 901 is a RandomProperty pool (its ench are ItemRandomProperties ids), not named by any RandomSuffix
        self.assertEqual(enchant_tables.suffix_pool_problems(self.POOL, {900}, {5, 1000}), [])
        self.assertEqual(len(enchant_tables.suffix_pool_problems(self.POOL, {900, 901}, {5, 1000})), 1)

    def test_an_ench_above_the_smallint_limit_is_reported(self):
        pool = [{"entry": 900, "ench": 40000}]
        (problem,) = enchant_tables.suffix_pool_problems(pool, {900}, {40000})
        self.assertIn("32767", problem)

    def test_values_read_from_sql_text_are_accepted(self):
        pool = [{"entry": "900", "ench": 5.0}]
        self.assertEqual(enchant_tables.suffix_pool_problems(pool, {900}, {5}), [])


class DropGuardTest(unittest.TestCase):
    def test_the_files_and_tables_are_known(self):
        defs = drop_guard.client_table_defs()
        for table, sql_table, _key in TABLES:
            block = BLOCK_NAMES[table.name]
            self.assertEqual(drop_guard.CLIENT_TABLES[table.dbc_filename], (sql_table, (block,)))
            self.assertIn(table.dbc_filename, defs)
            # the server half guards every row of the overlay table: custom ids and stock-id overrides alike
            self.assertEqual(drop_guard.GUARDED_TABLES[sql_table], ("ID", (drop_guard.ALL_IDS,)))
            (low, high), = drop_guard.custom_ranges(sql_table, IDS)
            self.assertTrue(low < 0 < IDS[block]["start"] < IDS[block]["end"] < high)
            self.assertIn(table.dbc_filename, drop_guard.OVERRIDE_FILES)

    def test_a_live_row_the_sql_deletes_is_a_drop_for_a_custom_id_and_a_stock_override_alike(self):
        sql = ("DELETE FROM `spellitemenchantment_dbc` WHERE (`ID`) IN ((5000), (5001), (2686));\n"
               "INSERT INTO `spellitemenchantment_dbc` (`ID`) VALUES\n(5001);\n")
        live = {"spellitemenchantment_dbc": {5000, 5001, 2686}}
        self.assertEqual(drop_guard.sql_drops(sql, live), {"spellitemenchantment_dbc": [2686, 5000]})

    def test_the_live_query_covers_every_row_of_the_overlay_tables(self):
        seen = []
        original = drop_guard.run_sql
        drop_guard.run_sql = lambda command, sql, database=None, header=False: seen.append(sql) or ""
        try:
            drop_guard.live_ids(["mysql"], ["gemproperties_dbc"], IDS)
        finally:
            drop_guard.run_sql = original
        self.assertIn("BETWEEN -2147483648 AND 2147483647", seen[0])

    def test_a_branch_that_never_wrote_a_live_stock_override_cannot_rewrite_it(self):
        # the live DB holds branch A's override of stock enchant 2686; this checkout's SQL re-inserts it with other
        # content and no SQL file here ever wrote the live content
        sql = ("DELETE FROM `spellitemenchantment_dbc` WHERE (`ID`) IN ((2686));\n"
               "INSERT INTO `spellitemenchantment_dbc` (`ID`, `Name_Lang_enUS`) VALUES\n(2686, '+8 Strength');\n")
        live = {"spellitemenchantment_dbc": {2686}}
        with tempfile.TemporaryDirectory() as d:
            result = drop_guard.rewrite_findings(
                sql, live, ["mysql"], Path(d),
                rows_reader=lambda command, table, ids: {2686: {"ID": "2686", "Name_Lang_enUS": "+8 Might"}},
            )
        self.assertEqual(result, {"spellitemenchantment_dbc": [2686]})

    def test_a_deployed_custom_row_the_shipped_file_lacks_is_a_drop(self):
        table = dbcfmt.SPELLITEMENCHANTMENT
        deployed_rows = [_row(table, ID=i) for i in (3883, 5000, 5100)]
        shipped_rows = [_row(table, ID=i) for i in (3883, 5100)]
        deployed = {"DBFilesClient/SpellItemEnchantment.dbc": dbcfile.pack_dbc_bytes(table, deployed_rows)}
        shipped = {"SpellItemEnchantment.dbc": dbcfile.pack_dbc_bytes(table, shipped_rows)}
        self.assertEqual(drop_guard.client_drops(deployed, shipped, None, IDS, True),
                         ({"SpellItemEnchantment.dbc": [5000]}, []))

    def test_the_condition_file_is_readable_by_the_guard(self):
        table = dbcfmt.SPELLITEMENCHANTMENTCONDITION
        deployed = {"DBFilesClient/SpellItemEnchantmentCondition.dbc": dbcfile.pack_dbc_bytes(
            table, [_row(table, ID=i) for i in (194, 1000)])}
        self.assertEqual(drop_guard.client_drops(deployed, {}, None, IDS, True),
                         ({"SpellItemEnchantmentCondition.dbc": [1000]}, []))


class OverrideGuardTest(unittest.TestCase):
    """S2: a deployed override of a stock row must not be reverted by a run from a branch that never wrote it."""

    TABLE = dbcfmt.SPELLITEMENCHANTMENT

    def rows(self, *specs):
        """Rows (ID, EffectArg_1) -> bytes."""
        return dbcfile.pack_dbc_bytes(self.TABLE, [_row(self.TABLE, ID=i, EffectArg_1=arg) for i, arg in specs])

    def stock(self, table):
        return {i: _row(table, ID=i, EffectArg_1=arg) for i, arg in ((2686, 4), (2687, 3))}

    def lost(self, deployed, shipped, replaces=True):
        return drop_guard.client_overrides_lost(
            {"DBFilesClient/SpellItemEnchantment.dbc": deployed},
            {} if shipped is None else {"SpellItemEnchantment.dbc": shipped}, None, replaces, self.stock)

    def test_a_reverted_override_is_found(self):
        deployed = self.rows((2686, 22), (2687, 3))  # 2686 overridden to Mastery
        self.assertEqual(self.lost(deployed, self.rows((2686, 4), (2687, 3))), {"SpellItemEnchantment.dbc": [2686]})

    def test_a_changed_override_and_a_dropped_file_are_found(self):
        deployed = self.rows((2686, 22), (2687, 3))
        self.assertEqual(self.lost(deployed, self.rows((2686, 23), (2687, 3))), {"SpellItemEnchantment.dbc": [2686]})
        self.assertEqual(self.lost(deployed, None), {"SpellItemEnchantment.dbc": [2686]})  # a full run, file not built

    def test_an_unchanged_override_a_repack_and_stock_rows_are_not_found(self):
        deployed = self.rows((2686, 22), (2687, 3))
        self.assertEqual(self.lost(deployed, deployed), {})
        self.assertEqual(self.lost(deployed, None, replaces=False), {})  # a repack leaves the member alone
        self.assertEqual(self.lost(self.rows((2686, 4), (2687, 3)), None), {})  # nothing overridden to lose

    def test_a_custom_id_is_the_other_guards_business(self):
        deployed = self.rows((2686, 4), (5000, 9))
        self.assertEqual(self.lost(deployed, self.rows((2686, 4))), {})

    def test_a_missing_stock_file_skips_the_comparison(self):
        deployed = self.rows((2686, 22))
        self.assertEqual(drop_guard.client_overrides_lost(
            {"SpellItemEnchantment.dbc": deployed}, {}, None, True, lambda table: {}), {})

    def test_check_refuses_a_revert_this_checkout_never_wrote_and_notes_its_own(self):
        deployed = self.rows((2686, 22), (2687, 3))
        shipped = {"SpellItemEnchantment.dbc": self.rows((2686, 4), (2687, 3))}
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            archive = tmp / "patch-Z.mpq"
            try:
                from lib import mpq_writer  # noqa: PLC0415

                mpq_writer.write_mpq(archive, {"DBFilesClient\\SpellItemEnchantment.dbc": deployed})
            except RuntimeError as error:  # no smpq on this machine
                self.skipTest(str(error))
            from unittest import mock  # noqa: PLC0415

            def run(known):
                with mock.patch.object(drop_guard, "known_ids", lambda table, ids, pending: set(ids) & set(known)):
                    return drop_guard.check(
                        sql_text=None, shipped=shipped, replaces_archive=True, deployed_archive=archive,
                        tables={"SpellItemEnchantment.dbc": self.TABLE}, ids_cfg=IDS, pending_dir=tmp, allow=False,
                        stock_rows_reader=self.stock,
                    )

            refused = run(known=())
            self.assertTrue(refused.refused)
            self.assertIn("2686", "\n".join(refused.lines))
            self.assertFalse(run(known=(2686,)).refused)  # this checkout wrote the override: its own removal


class ScopeTest(unittest.TestCase):
    """S1: a scope that declares a row owns it in both halves."""

    def ownership(self, text: str):
        from lib import scope  # noqa: PLC0415

        scopes = scope.Scopes({"stratholme": scope.ScopeDef("stratholme", (), ())}, ())
        dsl = _load(text, **FIXTURE_STOCK)
        registry.record_provenance()
        self.addCleanup(registry.stop_provenance)
        for key in ("spell_item_enchantments", "item_random_suffixes", "gem_properties", "enchant_conditions"):
            for row in dsl[key]:
                registry.set_declared_in(row, scope.SOURCE_DIR / "items" / "stratholme.py")
        specs = tuple(spec_for(sql) for _t, sql, _k in TABLES)
        return scope.build_ownership(scopes, IDS, ["stratholme"], dsl_classes=dsl, spell_entries=[], talents={},
                                     table_specs=specs), dsl

    def test_a_scoped_file_owns_its_declared_and_overridden_ids(self):
        own, _dsl = self.ownership(FIXTURE + "override_enchant(2686, Flags=1)\noverride_gem(2, Type=GemColor.BLUE)\n")
        for space, entry_id in (("spellitemenchantment", 5100), ("spellitemenchantment", 2686),
                                ("itemrandomsuffix", 1000), ("gemproperties", 2000), ("gemproperties", 2),
                                ("spellitemenchantmentcondition", 1000)):
            with self.subTest(space=space, id=entry_id):
                self.assertEqual(own.owners(space, entry_id), {"stratholme"})
        self.assertEqual(own.owners("spellitemenchantment", 2687), frozenset())  # a stock row nobody overrides

    def test_the_scoped_sql_keeps_the_rows_of_its_scope(self):
        from lib import scope  # noqa: PLC0415

        own, dsl = self.ownership(FIXTURE)
        block = render("gemproperties_dbc", index_for("gemproperties_dbc", []), dsl["gem_properties"])
        stmt = scope.parse_statement(scope.split_statements(block)[1])
        report = scope.FilterReport()
        self.assertIsNotNone(scope.filter_statement(stmt, own, report))
        self.assertEqual(report.kept["gemproperties_dbc"], 1)
        self.assertEqual(dict(report.left_out), {})

    def test_the_scoped_client_patch_carries_the_rows_of_its_scope(self):
        from lib import scope  # noqa: PLC0415

        own, dsl = self.ownership(FIXTURE)
        table = dbcfmt.GEMPROPERTIES
        stock = [_row(table, ID=2, Enchant_Id=2686, Type=2)]
        base = {"DBFilesClient/GemProperties.dbc": dbcfile.pack_dbc_bytes(table, stock)}
        full = {"GemProperties.dbc": dbcfile.pack_dbc_bytes(
            table, stock + list(enchant_tables.client_rows(table, dsl["gem_properties"]).values()))}
        result = scope.scoped_client_files(base, full, {"GemProperties.dbc": table}, own, {"GemProperties.dbc": stock},
                                           {}, IDS)
        self.assertEqual(result.errors, [])
        rows = {r["ID"]: r for r in scope.read_dbc_bytes(result.loose["GemProperties.dbc"], table)}
        self.assertEqual(set(rows), {2, 2000})
        self.assertEqual(rows[2000]["Enchant_Id"], 5100)

    def test_the_spaces_exist_in_ids_yaml(self):
        from lib import scope  # noqa: PLC0415

        for table, sql, key in TABLES:
            self.assertEqual(scope.DBC_SPACES[table.name], BLOCK_NAMES[table.name])
            self.assertEqual(scope.TABLE_IDS[sql], ("ID", BLOCK_NAMES[table.name]))
            self.assertIn(BLOCK_NAMES[table.name], IDS)
        self.assertIn(("spell_item_enchantments", "ID", "spellitemenchantment"), scope._DECLARED_ID_LISTS)


class OverrideRangeTest(unittest.TestCase):
    """N1: an override value is checked against the column it lands in (byte, int32, signed)."""

    def bad(self, call: str, pattern: str):
        with self.assertRaisesRegex(ValueError, pattern):
            _load(HEAD + call, **FIXTURE_STOCK)

    def test_byte_columns_take_0_to_255(self):
        self.bad("override_enchant_condition(3, Operator_1=300)\n", "0..255")
        self.bad("override_enchant_condition(3, Logic_1=-1)\n", "0..255")
        dsl = _load(HEAD + "override_enchant_condition(3, Operator_1=255)\n", **FIXTURE_STOCK)
        self.assertEqual(dsl["enchant_conditions"][0]["Operator_1"], 255)

    def test_int_columns_take_the_sql_signed_range(self):
        self.bad("override_enchant(2686, Flags=2147483648)\n", "0..2147483647")
        self.bad("override_enchant(2686, Flags=-1)\n", "0..2147483647")
        self.bad("override_gem(2, Enchant_Id=4294967295)\n", "0..2147483647")

    def test_signed_columns_take_int32_and_the_mask_takes_uint32(self):
        dsl = _load(HEAD + "override_enchant(2686, EffectPointsMin_1=-10, ItemVisual=-1, Name_Lang_Mask=4294967295)\n",
                    **FIXTURE_STOCK)
        self.assertEqual(dsl["spell_item_enchantments"][0]["EffectPointsMin_1"], -10)
        self.bad("override_enchant(2686, EffectPointsMin_1=-2147483649)\n", "-2147483648")
        self.bad("override_enchant(2686, Name_Lang_Mask=4294967296)\n", "4294967295")


if __name__ == "__main__":
    unittest.main()
