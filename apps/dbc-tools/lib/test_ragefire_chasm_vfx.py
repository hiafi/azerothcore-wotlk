"""
Ragefire Chasm visuals (Ragefire Chasm build, WP V): patch_ragefire_chasm_vfx_models.py and
source/npcs/ragefire_chasm/_visuals.py.

Covered: every minted id sits inside the `ragefire_chasm` reservation and 90372 stays unshipped (s7 #37), the row
builders (Felstorm state kit, fel spot impact kit, the four Satyr swing copies with the swapped AnimID), the constants
module agreeing with the patch script, none of the WRONG looks coming back as a wired id, every int constant being in a
category tuple of its table, the stock and shipped ids existing in the working-copy DBCs, the asset list, and the SQL
overlay.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_vfx.py
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import patch_ragefire_chasm_vfx_models as patch  # noqa: E402
from lib import source  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
VISUALS_FILE = TOOL_ROOT / "source" / "npcs" / "ragefire_chasm" / "_visuals.py"

# The picks the doc or the plan had wrong (handoff s3.10, VISUALS-REPORT "WRONG" rows) and what each really plays.
WRONG_SPELL_VISUALS = {
    8719: "Borer trail 29147 (anim 202 only, no model: the trail is SV 14013)",
    7396: "Eruption 36633 (BloodyExplosion: blood, not dirt: SV 7443)",
    8143: "Fel Flames 34072 (no ground burst: the fel spot is SV 90371)",
}
# Looks that are right for one named use and wrong as anything else.
ALLOWED_ONLY_AS = {
    399: {"OG_CLUB_SWING_ALT"},                    # its victim impact is a Knockdown (121): never the primary
    8923: {"TG_BITE"},                             # the bite only, never the Devour channel (that is SV 7270)
}
WRONG_CREATURE_DISPLAYS = {17200: "Blood Globule doc pick: an invisible stalker (the globule is CDI 8573)"}
TABLE_BY_PREFIX = (("DISPLAY_", "creature"), ("GODI_", "gameobject"), ("ITEM_", "item"), ("IDI_", "itemdisplay"))
NOT_IDS = {"SOUL_WISP_SCALE", "SEARING_SPIKE_SIZE", "SEARING_SPIKE_ALT_SIZE", "TITHE_SCALE_STEP",
           "TITHE_SCALE_MAX_STEPS"}


def _visuals():
    spec = importlib.util.spec_from_file_location("ragefire_chasm_visuals_under_test", VISUALS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has_working_copy() -> bool:
    return (patch.DBC_DIR / "SpellVisual.dbc").is_file()


class IdBlockTest(unittest.TestCase):
    def test_the_script_block_is_the_reservation(self):
        self.assertEqual(patch.VISUAL_BLOCK, IDS["reservations"]["ragefire_chasm"]["spellvisual"])
        self.assertEqual(patch.VISUAL_BLOCK, {"start": 90370, "end": 90399})

    def test_row_90372_is_not_shipped(self):
        for builder in (patch.build_effect_name_rows, patch.build_kit_rows, patch.build_spellvisual_rows):
            ids = {r["ID"] for r in builder()}
            self.assertNotIn(90372, ids, builder.__name__)
            self.assertTrue(all(patch.VISUAL_BLOCK["start"] <= i <= patch.VISUAL_BLOCK["end"] for i in ids))

    def test_the_visual_and_kit_ids_are_the_six_rows_of_s7_37(self):
        want = [90370, 90371, 90373, 90374, 90375, 90376]
        self.assertEqual(sorted(r["ID"] for r in patch.build_spellvisual_rows()), want)
        self.assertEqual(sorted(r["ID"] for r in patch.build_kit_rows()), want)
        self.assertEqual(sorted(r["ID"] for r in patch.build_effect_name_rows()), [90370, 90371, 90377, 90378])

    def test_no_display_or_gameobject_row_is_minted(self):
        self.assertEqual(sorted(n for n in dir(patch) if n.startswith(("CDI_", "CMD_", "GODI_", "SOUND_"))), [])


class RowTest(unittest.TestCase):
    def setUp(self):
        self.effects = {r["ID"]: r for r in patch.build_effect_name_rows()}
        self.kits = {r["ID"]: r for r in patch.build_kit_rows()}
        self.visuals = {r["ID"]: r for r in patch.build_spellvisual_rows()}

    def test_felstorm_is_a_state_with_anim_126_blades_and_a_wreath(self):
        row = self.visuals[90370]
        self.assertEqual([k for k in ("PrecastKit", "CastKit", "ImpactKit", "StateKit", "ChannelKit") if row[k]],
                         ["StateKit"])
        kit = self.kits[row["StateKit"]]
        self.assertEqual(kit["AnimID"], 126)
        self.assertIn("cfx_warrior_bladestorm_statebase", self.effects[kit["BaseEffect"]]["FileName"])
        self.assertIn("7fx_argus_felstorm_felinfused_statebase", self.effects[kit["ChestEffect"]]["FileName"])

    def test_the_fel_spot_is_an_impact_kit_with_the_two_stock_models(self):
        row = self.visuals[90371]
        self.assertEqual([k for k in ("PrecastKit", "CastKit", "ImpactKit", "StateKit", "ChannelKit") if row[k]],
                         ["ImpactKit"])
        kit = self.kits[row["ImpactKit"]]
        self.assertEqual(self.effects[kit["BaseEffect"]]["FileName"], patch.STOCK_FEL_NOVA_FILE)
        self.assertEqual(self.effects[kit["ChestEffect"]]["FileName"], patch.STOCK_FEL_HELLFIRE_FILE)

    def test_every_effect_is_a_fixed_size_look(self):
        for row in self.effects.values():
            self.assertEqual(row["AreaEffectSize"], 0.0)
            self.assertGreater(row["Scale"], 0)

    @unittest.skipUnless(_has_working_copy(), "no model-visual-dbc working copy in this checkout")
    def test_the_swing_copies_differ_from_the_stock_row_in_one_anim_only(self):
        stock_v = patch._stock("SpellVisual.dbc", patch.dbcfmt.SPELLVISUAL, {671, 250, 8144, 12317})
        for new_id, src, field, old_anim, new_anim in patch.SWING_COPIES:
            with self.subTest(sv=new_id):
                copy = self.visuals[new_id]
                stock = dict(stock_v[src])
                stock["ID"] = new_id
                stock[field] = new_id
                self.assertEqual(copy, stock)
                stock_kit = patch._stock("SpellVisualKit.dbc", patch.dbcfmt.SPELLVISUALKIT,
                                         {stock_v[src][field]})[stock_v[src][field]]
                kit = self.kits[new_id]
                self.assertEqual((stock_kit["AnimID"], kit["AnimID"]), (old_anim, new_anim))
                self.assertEqual({k: v for k, v in kit.items() if k not in ("ID", "AnimID")},
                                 {k: v for k, v in stock_kit.items() if k not in ("ID", "AnimID")})

    def test_the_swings_use_clips_the_satyr_has(self):
        # VR: the Satyr (CDI 2007) lacks anims 57 and 126 and has 17, 51-54, 124.
        for new_id in (90373, 90374, 90375, 90376):
            self.assertIn(self.kits[new_id]["AnimID"], (17, 51, 52, 53, 54, 124))
        self.assertEqual([self.kits[i]["AnimID"] for i in (90373, 90374, 90375, 90376)], [17, 17, 17, 54])


class AssetTest(unittest.TestCase):
    def test_the_asset_list_is_two_models_two_skins_ten_textures_and_no_duplicate(self):
        names = [Path(p).name for _, p in patch.SPELLS_ASSETS]
        self.assertEqual(len(names), 14)
        self.assertEqual(len(names), len({n.lower() for n in names}))
        self.assertEqual(sum(n.endswith(".m2") for n in names), 2)
        self.assertEqual(sum(n.endswith(".skin") for n in names), 2)
        self.assertEqual(sum(n.endswith(".blp") for n in names), 10)
        self.assertTrue(all(a == "patch-N" for a, _ in patch.SPELLS_ASSETS))

    def test_the_already_shipped_textures_are_not_listed_again(self):
        names = {Path(p).stem for _, p in patch.SPELLS_ASSETS}
        self.assertFalse(names & set(patch.ALREADY_SHIPPED_TEXTURES))

    def test_every_ascension_effect_model_is_in_the_asset_list(self):
        names = {Path(p).stem.lower() for _, p in patch.SPELLS_ASSETS}
        for row in patch.build_effect_name_rows():
            if row["FileName"].lower().startswith("spells\\") and row["ID"] in (90370, 90377):
                self.assertIn(Path(row["FileName"].replace("\\", "/")).stem.lower(), names)

    @unittest.skipUnless(_has_working_copy(), "no model-visual-dbc working copy in this checkout")
    def test_the_assets_are_extracted_in_the_working_copy(self):
        missing = [p.name for p in patch._asset_paths() if not p.is_file()]
        self.assertEqual(missing, [], "run patch_ragefire_chasm_vfx_models.py --extract")


class SqlTest(unittest.TestCase):
    def test_the_pending_sql_covers_the_span_and_only_spellvisual(self):
        sql = patch.build_pending_sql()
        self.assertIn("DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90370 AND 90376;", sql)
        for table in ("spellvisualkit", "spellvisualeffectname", "creaturedisplayinfo", "creaturemodeldata"):
            self.assertNotIn(table, sql)
        self.assertEqual(sql.count("\n(9037"), 6)
        self.assertNotIn("(90372,", sql)

    def test_no_value_overflows_a_signed_int_column(self):
        for row in patch.build_spellvisual_rows():
            for key, value in row.items():
                if isinstance(value, int):
                    self.assertLess(value, 1 << 31, key)


class ConstantsTest(unittest.TestCase):
    def setUp(self):
        self.v = _visuals()

    def _int_constants(self):
        return {n: v for n, v in vars(self.v).items()
                if n.isupper() and type(v) is int and not n.startswith("_") and n not in NOT_IDS}

    def _table(self, name):
        for prefix, table in TABLE_BY_PREFIX:
            if name.startswith(prefix):
                return table
        return "spellvisual"

    def _spell_visual_ids(self):
        return {v for n, v in self._int_constants().items() if self._table(n) == "spellvisual"}

    def test_the_minted_ids_match_the_patch_script(self):
        for name in ("SV_FELSTORM", "SV_FEL_SPOT", "SV_EVISCERATE", "SV_RUPTURE", "SV_ENVENOM", "SV_FAN_OF_KNIVES"):
            with self.subTest(name=name):
                self.assertEqual(getattr(self.v, name), getattr(patch, name))
        self.assertEqual(set(self.v.MINTED_SPELL_VISUALS), {r["ID"] for r in patch.build_spellvisual_rows()})
        self.assertEqual(self.v.MINTED_CREATURE_DISPLAYS, ())

    def test_the_boss_names_alias_the_minted_rows_with_the_stock_fallbacks(self):
        v = self.v
        self.assertEqual((v.TG_FELSTORM, v.TG_FEL_SPOT), (90370, 90371))
        self.assertEqual((v.TG_FELSTORM_FALLBACK, v.TG_FEL_SPOT_FALLBACK), (6044, 9004))
        self.assertEqual((v.BZ_EVISCERATE, v.BZ_RUPTURE, v.BZ_ENVENOM, v.BZ_FAN_OF_KNIVES),
                         (90373, 90374, 90375, 90376))
        self.assertEqual((v.BZ_EVISCERATE_FALLBACK, v.BZ_RUPTURE_FALLBACK, v.BZ_ENVENOM_FALLBACK,
                          v.BZ_FAN_OF_KNIVES_FALLBACK), (671, 250, 8144, 12317))

    def test_every_int_constant_is_in_a_category_tuple_of_its_table(self):
        v = self.v
        known = {
            "spellvisual": set(v.STOCK_SPELL_VISUALS) | set(v.MINTED_SPELL_VISUALS) | set(v.SHIPPED_SPELL_VISUALS),
            "creature": set(v.STOCK_CREATURE_DISPLAYS),
            "gameobject": set(v.STOCK_GAMEOBJECT_DISPLAYS),
        }
        for name, value in self._int_constants().items():
            table = self._table(name)
            if table in known:
                with self.subTest(name=name, table=table):
                    self.assertIn(value, known[table])

    def test_each_category_holds_the_right_kind_of_id(self):
        v = self.v
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS",
                     "SHIPPED_SPELL_VISUALS"):
            ids = getattr(v, name)
            self.assertEqual(len(ids), len(set(ids)), name)
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS"):
            self.assertFalse([i for i in getattr(v, name) if i >= 90000], name)
        self.assertTrue(all(90370 <= i <= 90399 for i in v.MINTED_SPELL_VISUALS))
        self.assertEqual(set(v.SHIPPED_SPELL_VISUALS), {90554, 90601, 90657})

    def test_the_shipped_names_are_all_in_the_shipped_tuple(self):
        for name, value in self._int_constants().items():
            if name.startswith("SHIPPED_"):
                self.assertIn(value, self.v.SHIPPED_SPELL_VISUALS, name)

    def test_the_wrong_looks_are_not_wired(self):
        wired = self._spell_visual_ids()
        for sv, why in WRONG_SPELL_VISUALS.items():
            with self.subTest(sv=sv):
                self.assertNotIn(sv, wired, why)
        displays = {v for n, v in self._int_constants().items() if n.startswith("DISPLAY_")}
        for cdi, why in WRONG_CREATURE_DISPLAYS.items():
            self.assertNotIn(cdi, displays, why)

    def test_the_looks_that_are_right_for_one_use_only_are_wired_to_that_use_only(self):
        for sv, allowed in ALLOWED_ONLY_AS.items():
            carriers = {n for n, v in self._int_constants().items() if v == sv and self._table(n) == "spellvisual"}
            with self.subTest(sv=sv):
                self.assertTrue(carriers, "the pick is not wired at all")
                self.assertTrue(carriers <= allowed, carriers)

    def test_the_devour_channel_is_the_beam_not_the_bite(self):
        self.assertEqual(self.v.TG_DEVOUR_CHANNEL, 7270)
        self.assertNotEqual(self.v.TG_DEVOUR_CHANNEL, self.v.TG_BITE)

    def test_the_corrections_of_s3_10_and_s7_37(self):
        v = self.v
        self.assertEqual((v.OG_BORER_TRAIL, v.OG_BORER_ERUPTION, v.OG_CLUB_SWING), (14013, 7443, 219))
        self.assertEqual(v.DISPLAY_BORER_TUNNEL, 15294)             # the carrier, never a model
        self.assertEqual(v.DISPLAY_BLOOD_GLOBULE, 8573)             # not CDI 17200
        self.assertEqual((v.JR_SOUL_SICK, v.JR_TITHE, v.JR_SOUL_TEAR), (561, 11821, 7180))
        self.assertEqual(v.SOUL_WISP_SCALE, 1.75)
        self.assertEqual(v.GODI_SEARING_SPIKE, 5073)                # s7 #19 A
        self.assertEqual(v.SEARING_SPIKE_SIZE, 2.0)
        self.assertEqual(v.TG_HM_AURA, 90554)
        self.assertEqual(v.TG_BLOOD_LAKE, 90554)                    # row 90372 is not shipped
        self.assertEqual(v.JR_OFFERING_SPOT, 90601)
        self.assertEqual(v.TITHE_SCALE_MAX_STEPS, 5)

    def test_every_boss_code_has_constants(self):
        names = set(self._int_constants())
        for prefix in ("OG_", "JR_", "BZ_", "TG_"):
            self.assertTrue([n for n in names if n.startswith(prefix)], prefix)

    def test_the_constants_module_is_skipped_by_the_package_loader(self):
        self.assertTrue(VISUALS_FILE.name.startswith("_"))


class StockExistsTest(unittest.TestCase):
    """Against the hand-maintained working copy, when this checkout has one (var/ is gitignored)."""

    @unittest.skipUnless(_has_working_copy(), "no model-visual-dbc working copy in this checkout")
    def test_every_stock_and_shipped_id_exists(self):
        self.assertTrue(patch.check_stock_ids())

    @unittest.skipUnless(_has_working_copy(), "no model-visual-dbc working copy in this checkout")
    def test_the_minted_ids_are_free_in_the_working_copy(self):
        patch.check_no_collisions()


if __name__ == "__main__":
    unittest.main()
