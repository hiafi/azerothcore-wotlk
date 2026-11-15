"""
Blackrock Spire visuals (Blackrock Spire build, WP V-1 wave 1): patch_blackrock_spire_vfx_models.py and
source/npcs/blackrock_spire/_visuals.py.

Covered: every minted id sits inside the `blackrock_spire` reservation, the row builders (the Ascension spit patch as an
AREA and a STATE look, the war horn burst on the stock horn cast), the constants module agreeing with the patch script,
none of the wrong looks (handoff s3.10) coming back as a wired id, the stock and shipped ids existing in the
working-copy DBCs, and the SQL overlay. Wave 2 (V-2) extends these.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_vfx.py
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import patch_blackrock_spire_vfx_models as patch  # noqa: E402
from lib import source  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
BRS = IDS["reservations"]["blackrock_spire"]
VISUALS_FILE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire" / "_visuals.py"

# The wave 1 picks the doc or the build spec had wrong (handoff s3.10) and what each really plays: none may be wired.
WRONG_SPELL_VISUALS = {
    9766: "Axe Volley (no missile, a chest flash only; allowed only as the Haymaker hit flash, never as rain)",
    12302: "Arcane Bomb (no missile, a burst at the caster)",
    8855: "Throw Spear 43413 (no spear in flight)",
    10724: "Impale 48261 (no spear in flight)",
    6719: "Shadow Flame 22992 (a stream at the mouth, no ground)",
    7278: "Bestial Wrath (a one-shot head flash on a lasting buff)",
    631: "Rabies (a 3 s impact on a 30 s debuff)",
    19: "Poison 744 (a 3 s impact)",
    8946: "a bottle missile with no impact",
    8948: "Darkfury's shadow impact, not a bottle",
}


def _visuals():
    spec = importlib.util.spec_from_file_location("blackrock_spire_visuals_under_test", VISUALS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IdBlockTest(unittest.TestCase):
    def test_the_script_blocks_are_the_reservation(self):
        self.assertEqual(patch.VISUAL_BLOCK, BRS["spellvisual"])
        self.assertEqual(patch.VISUAL_BLOCK, {"start": 90600, "end": 90649})
        self.assertEqual(patch.GODI_BLOCK, BRS["gameobjectdisplayinfo"])
        self.assertEqual(patch.CREATURE_DISPLAY_BLOCK, BRS["creaturedisplayinfo"])

    def test_every_minted_id_is_inside_the_block(self):
        rows = patch.build_effect_name_rows() + patch.build_kit_rows() + patch.build_spellvisual_rows()
        for row in rows:
            with self.subTest(id=row["ID"]):
                self.assertTrue(patch.VISUAL_BLOCK["start"] <= row["ID"] <= patch.VISUAL_BLOCK["end"])

    def test_ids_are_unique_per_table(self):
        for builder in (patch.build_effect_name_rows, patch.build_kit_rows, patch.build_spellvisual_rows):
            ids = [r["ID"] for r in builder()]
            self.assertEqual(len(ids), len(set(ids)), builder.__name__)

    def test_wave_1_mints_no_display_or_sound_row(self):
        minted = [name for name in dir(patch)
                  if name.startswith(("CDI_", "GODI_", "SOUND_")) and not name.endswith("_BLOCK")]
        self.assertFalse(minted)


class RowTest(unittest.TestCase):
    def setUp(self):
        self.effects = {r["ID"]: r for r in patch.build_effect_name_rows()}
        self.kits = {r["ID"]: r for r in patch.build_kit_rows()}
        self.visuals = {r["ID"]: r for r in patch.build_spellvisual_rows()}

    def test_the_spit_patch_is_the_ascension_quad_at_a_fixed_scale_for_a_4_yd_radius(self):
        row = self.effects[patch.EFFECT_SPIT_PATCH]
        self.assertEqual(row["FileName"], "SPELLS\\mannoroth_gooflowshadow_state_projected.mdx")
        self.assertEqual(row["AreaEffectSize"], 0.0)               # a fixed size, not the spell radius
        self.assertEqual(row["Scale"], patch.SPIT_PATCH_SCALE)
        self.assertAlmostEqual(row["Scale"] * patch.SPIT_PATCH_YARDS, 2 * 4, delta=1.5)    # WT16: a 4 yd radius

    def test_the_spit_area_look_is_a_persistent_area_and_the_state_look_a_state_kit(self):
        area = self.visuals[patch.SV_SPIT_PATCH_AREA]
        state = self.visuals[patch.SV_SPIT_PATCH_STATE]
        self.assertEqual(self.kits[area["PersistentAreaKit"]]["WorldEffect"], patch.EFFECT_SPIT_PATCH)
        self.assertEqual(self.kits[state["StateKit"]]["BaseEffect"], patch.EFFECT_SPIT_PATCH)
        for row in (area, state):
            self.assertEqual(sum(1 for s in ("PrecastKit", "CastKit", "ImpactKit", "StateKit", "ChannelKit",
                                             "PersistentAreaKit") if row[s]), 1)
            self.assertEqual(row["HasMissile"], 0)
            self.assertEqual(row["MissileAttachment"], -1)

    def test_the_horn_is_the_stock_horn_cast_with_a_burst_on_the_caster(self):
        sv = self.visuals[patch.SV_HORN_BLOWN]
        self.assertEqual(sv["CastKit"], patch.STOCK_HORN_CAST_KIT)       # sound 6423 + anim 81, kept
        self.assertEqual(self.kits[sv["ImpactKit"]]["ChestEffect"], patch.EFFECT_WARHORN_BURST)
        self.assertFalse(sv["StateKit"])
        self.assertEqual(sv["HasMissile"], 0)
        effect = self.effects[patch.EFFECT_WARHORN_BURST]
        self.assertEqual(effect["FileName"], "SPELLS\\ogre_warhorn_impact_base.mdx")
        self.assertEqual(effect["AreaEffectSize"], 0.0)

    def test_every_asset_a_row_points_at_is_in_the_asset_list(self):
        packed = {Path(p).name.lower() for _, p in patch.SPELLS_ASSETS}
        for effect in self.effects.values():
            stem = effect["FileName"].split("\\")[-1].rsplit(".", 1)[0].lower()
            self.assertIn(f"{stem}.m2", packed)
            self.assertIn(f"{stem}00.skin", packed)
        self.assertEqual(len(packed), len(patch.SPELLS_ASSETS))
        self.assertNotIn("t_vfx_hero_explosion_blur.blp", packed)       # stock, not repacked

    def test_the_pending_sql_deletes_exactly_the_minted_ids(self):
        sql = patch.build_pending_sql()
        self.assertIn("DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90600 AND 90602;", sql)
        for table in ("creaturedisplayinfo", "gameobjectdisplayinfo", "soundentries"):
            self.assertNotIn(table, sql)


class VisualsModuleTest(unittest.TestCase):
    def setUp(self):
        self.v = _visuals()

    def test_the_minted_ids_match_the_patch_script(self):
        for name in ("SV_SPIT_PATCH_AREA", "SV_SPIT_PATCH_STATE", "SV_HORN_BLOWN"):
            with self.subTest(name=name):
                self.assertEqual(getattr(self.v, name), getattr(patch, name))
        self.assertEqual(set(self.v.MINTED_SPELL_VISUALS), {r["ID"] for r in patch.build_spellvisual_rows()})

    def test_the_gap_picks(self):
        v = self.v
        self.assertEqual((v.OM_BAND_FILL_RED, v.OM_BAND_OUTLINE_RED), (92048, 93048))                   # gap 6
        self.assertEqual((v.SW_HATCH_BURST, v.SW_BROOD_CALL, v.SW_VENOM), (4339, 11329, 2617))         # gap 11
        self.assertEqual((v.DISPLAY_POWER_SPARK, v.UR_WILD_BOLT_MISSILE, v.UR_WILD_BOLT_LANDING,
                          v.UR_OVERCHARGE_HIT), (26753, 9947, 965, 8340))                               # gap 12
        self.assertEqual(v.ZG_MORTAR_SHELL, 3819)                                                       # gap 13
        self.assertEqual((v.SV_GOO_PUDDLE, v.SV_GOO_PUDDLE_STATE, v.HG_TORN_HIDE), (90342, 90343, 376))  # gap 14
        self.assertEqual((v.WT_SPIT_LANDING, v.GODI_WAR_HORN, v.DISPLAY_BLOODAXE_CHAMPION,
                          v.DISPLAY_RIDING_DIRE_WOLF), (6700, 7352, 9602, 14334))                       # gap 15
        self.assertEqual((v.VO_AXE_RAIN, v.WT_SPEAR_THROW), (3962, 11993))                              # s3.10 fixes

    def test_the_queued_boss_file_constants(self):
        """Constants the boss files define locally until they switch (the stalker display, B2's stock impacts)."""
        v = self.v
        self.assertEqual(v.DISPLAY_INVISIBLE_STALKER, 11686)
        self.assertIn(11686, v.STOCK_CREATURE_DISPLAYS)
        self.assertEqual((v.VG_FIRE_BLAST_IMPACT, v.VG_SHADOW_BURST_IMPACT, v.VG_GORE_IMPACT,
                          v.VG_CURSE_OF_BLOOD_STATE), (143, 45, 39, 876))
        for sv in (143, 45, 39, 876):
            self.assertIn(sv, v.STOCK_SPELL_VISUALS)

    def test_pelting_is_the_six_real_bottle_pairs(self):
        self.assertEqual(self.v.OM_PELTING,
                         {39154: 8943, 39147: 8944, 39148: 8945, 39149: 8947, 39146: 8949, 39155: 8950})

    def test_the_wrong_looks_are_not_wired(self):
        wired = set(self.v.STOCK_SPELL_VISUALS) | set(self.v.MINTED_SPELL_VISUALS)
        for sv, why in WRONG_SPELL_VISUALS.items():
            with self.subTest(sv=sv):
                if sv == 9766:      # kept only as the optional Haymaker hit flash, never as Voone's rain
                    self.assertEqual(self.v.OM_HAYMAKER_FLASH, 9766)
                    self.assertNotEqual(self.v.VO_AXE_RAIN, 9766)
                    continue
                self.assertNotIn(sv, wired, why)

    def test_the_lasting_buffs_use_the_lasting_twins(self):
        v = self.v
        self.assertEqual((v.HG_PACK_FURY, v.WT_OVERLORDS_FURY, v.HG_RABIES), (8581, 8581, 2617))

    def test_the_stock_tuples_hold_ints_and_no_minted_ids(self):
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS",
                     "STOCK_SOUND_ENTRIES"):
            ids = getattr(self.v, name)
            with self.subTest(name=name):
                self.assertTrue(all(isinstance(i, int) for i in ids))
                self.assertFalse([i for i in ids if i >= 90000])

    def test_the_constants_module_is_skipped_by_the_package_loader(self):
        self.assertTrue(VISUALS_FILE.name.startswith("_"))


class StockExistsTest(unittest.TestCase):
    """Against the hand-maintained working copy, when this checkout has one (var/ is gitignored)."""

    def test_every_stock_and_shipped_id_exists(self):
        if not (patch.DBC_DIR / "SpellVisual.dbc").is_file():
            self.skipTest("no model-visual-dbc working copy in this checkout")
        self.assertTrue(patch.check_stock_ids())


if __name__ == "__main__":
    unittest.main()
