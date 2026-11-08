"""
Shadowfang Keep visuals (Shadowfang Keep build, WP-V): patch_shadowfang_keep_vfx_models.py and
source/npcs/shadowfang_keep/_visuals.py.

Covered: every minted id sits inside the `shadowfang_keep` reservation and nowhere else, the row builders (the effect
name, the kit that keeps the stock thunder sound, the SpellVisual, the key ring display), the constants module agreeing
with the patch script, none of the nine corrected looks (handoff s3.10) coming back as a wrong id, and the SQL overlay.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_shadowfang_keep_vfx.py
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import patch_shadowfang_keep_vfx_models as patch  # noqa: E402
from lib import source  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
SFK = IDS["reservations"]["shadowfang_keep"]
VISUALS_FILE = TOOL_ROOT / "source" / "npcs" / "shadowfang_keep" / "_visuals.py"

# The nine looks SK got wrong (handoff s3.10 corrections) and the stock SpellVisual each one has: none may be wired.
# Rune of Power cast's SV 13072 (correction 3: hands, no rune) is pinned below as "never the rune" instead: S9 wires it
# as the prisoner's casting hands (AR_WARD_HANDS), which is the look it has.
WRONG_SPELL_VISUALS = {
    6941: "Lightning Strike (a blue ball at the feet)",
    14495: "Throw Vial A (a blood spurt)",
    11612: "Lunge (Frost Strike's blade)",
    854: "Acid Spit (a one-target missile)",
    7966: "Shadow Nova (an orange ring)",
    12058: "Hookshot (an instant grab)",
}


def _visuals():
    spec = importlib.util.spec_from_file_location("sfk_visuals_under_test", VISUALS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IdBlockTest(unittest.TestCase):
    def test_the_script_blocks_are_the_reservation(self):
        self.assertEqual(patch.VISUAL_BLOCK, SFK["spellvisual"])
        self.assertEqual(patch.GODI_BLOCK, SFK["gameobjectdisplayinfo"])

    def test_every_minted_id_is_inside_its_block(self):
        rows = (patch.build_effect_name_rows() + patch.build_kit_rows({"SoundID": 30}) + patch.build_spellvisual_rows())
        for row in rows:
            with self.subTest(id=row["ID"]):
                self.assertTrue(patch.VISUAL_BLOCK["start"] <= row["ID"] <= patch.VISUAL_BLOCK["end"])
        godi = patch.build_gameobject_display_row()
        self.assertTrue(patch.GODI_BLOCK["start"] <= godi["ID"] <= patch.GODI_BLOCK["end"])

    def test_no_creature_display_is_minted(self):
        # the fragments, echoes and door stand-in are stock displays (s7 #16); 90720-90729 stays free
        self.assertFalse([name for name in dir(patch) if name.startswith("CDI_")])


class RowTest(unittest.TestCase):
    def test_the_strike_is_the_purple_model_at_the_fixed_scale(self):
        (effect,) = patch.build_effect_name_rows()
        self.assertEqual(effect["ID"], patch.EFFECT_SHADOW_LIGHTNING)
        self.assertEqual(effect["FileName"], "SPELLS\\purple_leishen_lightningcall_projected.mdx")
        self.assertEqual(effect["Scale"], patch.SHADOW_LIGHTNING_SCALE)
        self.assertEqual(effect["AreaEffectSize"], 0.0)  # a fixed size, not the spell radius

    def test_the_kit_keeps_the_stock_thunder_sound(self):
        (kit,) = patch.build_kit_rows({"SoundID": 30})
        self.assertEqual(kit["BaseEffect"], patch.EFFECT_SHADOW_LIGHTNING)    # 318's slot (R2 N-5)
        self.assertEqual(kit.get("WorldEffect", 0), 0)
        self.assertEqual(kit["SoundID"], 30)
        self.assertEqual(kit["ID"], patch.KIT_SHADOW_LIGHTNING)

    def test_the_spellvisual_is_an_impact_only_look(self):
        (sv,) = patch.build_spellvisual_rows()
        self.assertEqual(sv["ID"], patch.SV_SHADOW_LIGHTNING)
        self.assertEqual(sv["ImpactKit"], patch.KIT_SHADOW_LIGHTNING)
        self.assertEqual(sv["MissileAttachment"], -1)
        for field in ("PrecastKit", "CastKit", "StateKit", "ChannelKit", "PersistentAreaKit", "HasMissile"):
            self.assertEqual(sv[field], 0, field)

    def test_the_key_ring_display_points_at_the_packed_model(self):
        row = patch.build_gameobject_display_row()
        self.assertEqual(row["ID"], patch.GODI_CELL_KEY)
        packed = {dest.lower().replace("/", "\\") for _, _, dest in patch.EXTRA_ASSETS}
        self.assertIn(row["ModelName"].lower(), packed)
        # a flat 0.38 x 0.58 x 0.14 yd ring
        self.assertAlmostEqual(row["GeoBoxMaxX"] - row["GeoBoxMinX"], 0.38, places=2)
        self.assertAlmostEqual(row["GeoBoxMaxY"] - row["GeoBoxMinY"], 0.58, places=2)

    def test_the_lightning_assets_are_the_model_its_skin_and_nine_textures(self):
        names = [Path(p).name for _, p in patch.SPELLS_ASSETS]
        self.assertIn("purple_leishen_lightningcall_projected.m2", names)
        self.assertIn("purple_leishen_lightningcall_projected00.skin", names)
        self.assertEqual(sum(n.endswith(".blp") for n in names), 9)
        self.assertNotIn("firering1a.blp", names)  # stock: repacking it would shadow the stock texture

    def test_the_pending_sql_deletes_exactly_the_minted_ids(self):
        sql = patch.build_pending_sql()
        self.assertIn("DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90400 AND 90400;", sql)
        self.assertIn("DELETE FROM `gameobjectdisplayinfo_dbc` WHERE `ID` BETWEEN 90030 AND 90030;", sql)
        self.assertNotIn("creaturedisplayinfo", sql)


class VisualsModuleTest(unittest.TestCase):
    def setUp(self):
        self.v = _visuals()

    def test_the_minted_ids_match_the_patch_script(self):
        self.assertEqual(self.v.SV_SHADOW_LIGHTNING, patch.SV_SHADOW_LIGHTNING)
        self.assertEqual(self.v.GODI_CELL_KEY, patch.GODI_CELL_KEY)
        self.assertEqual(self.v.CELL_KEY_SIZE, patch.CELL_KEY_SIZE)
        self.assertEqual(self.v.FN_SHADOW_LIGHTNING, patch.SV_SHADOW_LIGHTNING)

    def test_the_corrected_looks_replace_the_wrong_ones(self):
        wired = set(self.v.STOCK_SPELL_VISUALS) | {self.v.SV_SHADOW_LIGHTNING}
        for sv, why in WRONG_SPELL_VISUALS.items():
            with self.subTest(sv=sv):
                self.assertNotIn(sv, wired, why)
        self.assertEqual(self.v.FN_LIGHTNING, 986)            # 2: the sky bolt
        self.assertEqual(self.v.AR_WARD_RUNE, 13069)          # 3: the 11 yd rune
        self.assertEqual(self.v.AR_WARD_HANDS, 13072)         # 3: 13072 only as the casting hands, never the rune
        self.assertNotEqual(self.v.AR_WARD_RUNE, self.v.AR_WARD_HANDS)
        self.assertEqual(self.v.AR_VIAL_THROW, 12483)         # 4: Sprinkle Holy Water
        self.assertIn(self.v.NA_LUNGE, (3941, 2275))          # 5: Rip or Ravage
        self.assertEqual(self.v.NA_ACID_SLAVER, 2619)         # 6: Acid Breath
        self.assertIn(self.v.FN_VOID_PULSE, (45, 12835))      # 7: Shadow Burst or Shadow Crash
        self.assertEqual(self.v.RC_MEAT_HOOK, 11055)          # 8: Scourge Hook
        self.assertEqual(self.v.RG_SOUL_DRAIN_CHANNEL, 680)   # 9: the channel beam
        self.assertEqual(self.v.DISPLAY_INVISIBLE_STALKER, 11686)  # 1: not display 411

    def test_the_stock_tuples_hold_ints_and_no_minted_ids(self):
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS"):
            ids = getattr(self.v, name)
            with self.subTest(name=name):
                self.assertTrue(all(isinstance(i, int) for i in ids))
                self.assertFalse([i for i in ids if i >= 90000])

    def test_the_constants_module_is_skipped_by_the_package_loader(self):
        self.assertTrue(VISUALS_FILE.name.startswith("_"))


class StockExistsTest(unittest.TestCase):
    """Against the hand-maintained working copy, when this checkout has one (var/ is gitignored)."""

    def test_every_stock_id_exists(self):
        if not (patch.DBC_DIR / "SpellVisual.dbc").is_file():
            self.skipTest("no model-visual-dbc working copy in this checkout")
        self.assertTrue(patch.check_stock_ids())


if __name__ == "__main__":
    unittest.main()
