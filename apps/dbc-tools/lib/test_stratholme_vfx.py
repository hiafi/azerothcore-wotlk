"""
Stratholme visuals (Stratholme build, WP V-1 wave 1, V-2 wave 2): patch_stratholme_vfx_models.py and
source/npcs/stratholme/_visuals.py.

Covered: every minted id sits inside the `stratholme` reservation and nowhere else, the row builders (the Web_State
patch at both radii, the gut puddle, the lasting Keened skull), the constants module agreeing with the patch script,
none of the wrong looks (handoff s3.10) coming back as a wired id, the stock ids existing in the working-copy DBCs, and
the SQL overlay. Wave 2 adds the FlameZone / HolyZone rings, the Carrion fan, the lie judgment and the Main Gate stock
picks.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_vfx.py
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import patch_stratholme_vfx_models as patch  # noqa: E402
from lib import source  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
STRATHOLME = IDS["reservations"]["stratholme"]
VISUALS_FILE = TOOL_ROOT / "source" / "npcs" / "stratholme" / "_visuals.py"

# The wave 1 picks the doc or the build spec had wrong (handoff s3.10) and what each really plays: none may be wired.
WRONG_SPELL_VISUALS = {
    5920: "Spider Web (a beam plus a cocoon on the target, no ground patch)",
    10386: "Blizzard (an empty persistent-area kit: per-hit shard columns only)",
    2716: "Slime (a chest particle, no ground)",
    7597: "Chains of Kel'Thuzad (a missile, no beam)",
    7000: "Purple Beam (a green SoulBeam chain)",
    736: "Terrify (a color tint only)",
    2576: "Enchanting Lullaby (red hearts)",
}


def _visuals():
    spec = importlib.util.spec_from_file_location("stratholme_visuals_under_test", VISUALS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IdBlockTest(unittest.TestCase):
    def test_the_script_block_is_the_reservation(self):
        self.assertEqual(patch.VISUAL_BLOCK, STRATHOLME["spellvisual"])
        self.assertEqual(patch.VISUAL_BLOCK, {"start": 90500, "end": 90549})

    def test_every_minted_id_is_inside_the_block(self):
        rows = patch.build_effect_name_rows() + patch.build_kit_rows() + patch.build_spellvisual_rows()
        for row in rows:
            with self.subTest(id=row["ID"]):
                self.assertTrue(patch.VISUAL_BLOCK["start"] <= row["ID"] <= patch.VISUAL_BLOCK["end"])

    def test_ids_are_unique_per_table(self):
        for builder in (patch.build_effect_name_rows, patch.build_kit_rows, patch.build_spellvisual_rows):
            ids = [r["ID"] for r in builder()]
            self.assertEqual(len(ids), len(set(ids)), builder.__name__)

    def test_no_display_or_sound_row_is_minted(self):
        self.assertFalse([name for name in dir(patch)
                          if name.startswith(("CDI_", "GODI_", "SOUND_")) or "DISPLAY" in name])


class RowTest(unittest.TestCase):
    def setUp(self):
        self.effects = {r["ID"]: r for r in patch.build_effect_name_rows()}
        self.kits = {r["ID"]: r for r in patch.build_kit_rows()}
        self.visuals = {r["ID"]: r for r in patch.build_spellvisual_rows()}

    def test_the_web_patch_is_web_state_at_a_fixed_scale_for_each_radius(self):
        for effect_id, scale, radius in ((patch.EFFECT_WEB_PATCH_5, patch.WEB_PATCH_5_SCALE, 5),
                                         (patch.EFFECT_WEB_PATCH_7, patch.WEB_PATCH_7_SCALE, 7)):
            row = self.effects[effect_id]
            with self.subTest(radius=radius):
                self.assertEqual(row["FileName"], "SPELLS\\Web_State.mdx")
                self.assertEqual(row["AreaEffectSize"], 0.0)       # a fixed size, not the spell radius
                self.assertEqual(row["Scale"], scale)
                self.assertAlmostEqual(row["Scale"] * patch.WEB_STATE_YARDS, 2 * radius, delta=0.6)

    def test_the_gut_puddle_is_twelve_yards_across(self):
        row = self.effects[patch.EFFECT_GUT_PUDDLE]
        self.assertEqual(row["FileName"], "SPELLS\\goo_flow_state.mdx")
        self.assertEqual(row["AreaEffectSize"], 0.0)
        self.assertAlmostEqual(row["Scale"] * patch.GOO_FLOW_YARDS, 12.0, delta=0.5)

    def test_area_kits_use_the_world_effect_and_state_kits_the_base_effect(self):
        for kit_id, effect_id, slot in ((patch.KIT_WEB_PATCH_5_AREA, patch.EFFECT_WEB_PATCH_5, "WorldEffect"),
                                        (patch.KIT_WEB_PATCH_5_STATE, patch.EFFECT_WEB_PATCH_5, "BaseEffect"),
                                        (patch.KIT_WEB_PATCH_7_AREA, patch.EFFECT_WEB_PATCH_7, "WorldEffect"),
                                        (patch.KIT_WEB_PATCH_7_STATE, patch.EFFECT_WEB_PATCH_7, "BaseEffect"),
                                        (patch.KIT_GUT_PUDDLE_AREA, patch.EFFECT_GUT_PUDDLE, "WorldEffect"),
                                        (patch.KIT_GUT_PUDDLE_STATE, patch.EFFECT_GUT_PUDDLE, "BaseEffect")):
            with self.subTest(kit=kit_id):
                self.assertEqual(self.kits[kit_id][slot], effect_id)

    def test_the_keened_skull_is_the_stock_head_effect_with_no_sound(self):
        kit = self.kits[patch.KIT_KEENED_SKULL_STATE]
        self.assertEqual(kit["HeadEffect"], 311)
        self.assertEqual(kit.get("SoundID", 0), 0)
        sv = self.visuals[patch.SV_KEENED_SKULL_STATE]
        self.assertEqual(sv["StateKit"], patch.KIT_KEENED_SKULL_STATE)

    def test_each_spellvisual_carries_exactly_one_kit_except_the_two_composed_ones(self):
        slots = ("PrecastKit", "CastKit", "ImpactKit", "StateKit", "ChannelKit", "PersistentAreaKit")
        composed = {patch.SV_CARRION_FAN, patch.SV_LIE_JUDGMENT}
        for sv_id, row in self.visuals.items():
            with self.subTest(sv=sv_id):
                if sv_id not in composed:
                    self.assertEqual(sum(1 for s in slots if row[s]), 1)
                self.assertEqual(row["HasMissile"], 0)
                self.assertEqual(row["MissileAttachment"], -1)

    def test_the_zone_glows_are_flat_quads_at_a_fixed_scale_for_each_radius(self):
        rows = ((patch.EFFECT_FLAMEZONE_10, "flamezone", patch.FLAMEZONE_RADIUS_PER_SCALE, 10),
                (patch.EFFECT_FLAMEZONE_8, "flamezone", patch.FLAMEZONE_RADIUS_PER_SCALE, 8),
                (patch.EFFECT_HOLYZONE_4, "holyzone", patch.HOLYZONE_RADIUS_PER_SCALE, 4),
                (patch.EFFECT_HOLYZONE_5, "holyzone", patch.HOLYZONE_RADIUS_PER_SCALE, 5),
                (patch.EFFECT_HOLYZONE_6, "holyzone", patch.HOLYZONE_RADIUS_PER_SCALE, 6),
                (patch.EFFECT_HOLYZONE_8, "holyzone", patch.HOLYZONE_RADIUS_PER_SCALE, 8))
        for effect_id, model, per_scale, radius in rows:
            row = self.effects[effect_id]
            with self.subTest(model=model, radius=radius):
                self.assertEqual(row["FileName"], f"SPELLS\\{model}.mdx")
                self.assertEqual(row["AreaEffectSize"], 0.0)
                self.assertAlmostEqual(row["Scale"] * per_scale, radius, delta=0.5)

    def test_every_zone_state_look_is_a_state_kit_on_the_base_effect(self):
        for sv_id, kit_id, effect_id in (
                (patch.SV_FLAMEZONE_10_STATE, patch.KIT_FLAMEZONE_10_STATE, patch.EFFECT_FLAMEZONE_10),
                (patch.SV_FLAMEZONE_8_STATE, patch.KIT_FLAMEZONE_8_STATE, patch.EFFECT_FLAMEZONE_8),
                (patch.SV_HOLYZONE_4_STATE, patch.KIT_HOLYZONE_4_STATE, patch.EFFECT_HOLYZONE_4),
                (patch.SV_HOLYZONE_5_STATE, patch.KIT_HOLYZONE_5_STATE, patch.EFFECT_HOLYZONE_5),
                (patch.SV_HOLYZONE_6_STATE, patch.KIT_HOLYZONE_6_STATE, patch.EFFECT_HOLYZONE_6),
                (patch.SV_HOLYZONE_8_STATE, patch.KIT_HOLYZONE_8_STATE, patch.EFFECT_HOLYZONE_8)):
            with self.subTest(sv=sv_id):
                self.assertEqual(self.visuals[sv_id]["StateKit"], kit_id)
                self.assertEqual(self.kits[kit_id]["BaseEffect"], effect_id)

    def test_the_carrion_fan_plays_through_the_cast_at_the_cone_length(self):
        effect = self.effects[patch.EFFECT_CARRION_FAN]
        self.assertEqual(effect["FileName"], "SPELLS\\dreadlord_carrion_swarm_cast.mdx")
        self.assertEqual(effect["AreaEffectSize"], 0.0)
        self.assertAlmostEqual(effect["Scale"] * patch.CARRION_FAN_YARDS, 30.0, delta=0.5)   # BZ1's 30 yd cone
        sv = self.visuals[patch.SV_CARRION_FAN]
        self.assertEqual(self.kits[sv["PrecastKit"]]["BaseEffect"], patch.EFFECT_CARRION_FAN)
        # the cast kit must not replay the fan (the stock cast kit 7721 would play the 40 yd one at the cast end)
        self.assertFalse(self.kits[sv["CastKit"]]["BaseEffect"])
        self.assertFalse(sv["StateKit"])      # the stock SV 9099's stun swirl state stays out

    def test_the_lie_judgment_is_shadow_hands_with_a_red_flash(self):
        sv = self.visuals[patch.SV_LIE_JUDGMENT]
        self.assertEqual(sv["CastKit"], patch.STOCK_SHADOW_HANDS_CAST_KIT)
        self.assertEqual(self.kits[sv["ImpactKit"]]["ChestEffect"], patch.STOCK_JUDGEMENT_RED_EFFECT)
        self.assertEqual(sv["TargetImpactKit"], patch.STOCK_SHADOW_CHEST_IMPACT_KIT)
        self.assertFalse(sv["StateKit"])

    def test_area_looks_are_persistent_area_and_state_looks_are_state(self):
        for sv_id in (patch.SV_WEB_PATCH_5_AREA, patch.SV_WEB_PATCH_7_AREA, patch.SV_GUT_PUDDLE_AREA):
            self.assertTrue(self.visuals[sv_id]["PersistentAreaKit"], sv_id)
        for sv_id in (patch.SV_WEB_PATCH_5_STATE, patch.SV_WEB_PATCH_7_STATE, patch.SV_GUT_PUDDLE_STATE,
                      patch.SV_KEENED_SKULL_STATE):
            self.assertTrue(self.visuals[sv_id]["StateKit"], sv_id)

    def test_the_pending_sql_deletes_exactly_the_minted_ids(self):
        sql = patch.build_pending_sql()
        self.assertIn("DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90500 AND 90514;", sql)
        for table in ("creaturedisplayinfo", "gameobjectdisplayinfo", "soundentries"):
            self.assertNotIn(table, sql)


class VisualsModuleTest(unittest.TestCase):
    def setUp(self):
        self.v = _visuals()

    def test_the_minted_ids_match_the_patch_script(self):
        for name in ("SV_WEB_PATCH_5_AREA", "SV_WEB_PATCH_5_STATE", "SV_WEB_PATCH_7_AREA", "SV_WEB_PATCH_7_STATE",
                     "SV_GUT_PUDDLE_AREA", "SV_GUT_PUDDLE_STATE", "SV_KEENED_SKULL_STATE",
                     "SV_FLAMEZONE_10_STATE", "SV_FLAMEZONE_8_STATE", "SV_HOLYZONE_4_STATE", "SV_HOLYZONE_5_STATE",
                     "SV_HOLYZONE_6_STATE", "SV_HOLYZONE_8_STATE", "SV_CARRION_FAN", "SV_LIE_JUDGMENT"):
            with self.subTest(name=name):
                self.assertEqual(getattr(self.v, name), getattr(patch, name))
        self.assertEqual(set(self.v.MINTED_SPELL_VISUALS), {r["ID"] for r in patch.build_spellvisual_rows()})

    def test_the_gap_picks(self):
        v = self.v
        self.assertEqual((v.BT_GRAIN_SACK, v.BA_TERRIFIED, v.SOUND_KEENING), (12216, 4801, 1171))     # gaps 16, 18
        self.assertEqual((v.MK_EYE_OF_BLIZZARD, v.DISPLAY_ICE_TOMB), (8787, 30890))                    # gap 20
        self.assertEqual((v.SV_ACID_POOL, v.SV_ACID_POOL_STATE), (90342, 90343))                       # gap 21
        self.assertEqual((v.GODI_BONE_PILE, v.GODI_BONE_PILE_ALT), (6328, 6329))                       # gap 22
        self.assertEqual((v.BR_EXECUTION_BEAM, v.DISPLAY_YSIDA_RISEN, v.HM_YSIDA_RISEN_AURA),
                         (7785, 25355, 11514))
        self.assertEqual((v.BR_CONDEMNED, v.BR_PRICE_OF_DEFIANCE), (11095, 47))
        self.assertEqual((v.NE_STUCK, v.DISPLAY_WEB_COCOON), (684, 16213))                             # gap 19

    def test_the_wave_2_picks(self):
        v = self.v
        self.assertEqual((v.UF_ACCUSED_ARROW, v.UF_ACCUSED_FLASH), (10201, 11826))                     # gap 5
        self.assertEqual((v.TM_JUMP_ROPE, v.TM_SWEEP_BURST), (9275, 9612))                             # gap 8
        self.assertEqual((v.DA_TRUE_GROUND, v.DA_LIE_GROUND, v.DA_TRUE_JUDGMENT), (5600, 8506, 5651))  # gap 13
        self.assertEqual((v.DA_METEOR, v.DA_IMMOLATION, v.DA_SLEEP), (4859, 8313, 7320))
        self.assertEqual((v.BZ_SWARM_CLOUD, v.BZ_VAMPIRIC_HEAL), (7620, 9310))                         # gap 14
        self.assertEqual((v.ML_BLAZE_BEAM, v.WI_MUZZLE_BLAST, v.GODI_CANNONBALL), (11500, 612, 153))   # Added A, B
        self.assertEqual((v.GODI_HOUSE_FIRE, v.GODI_HOUSE_FIRE_ALT), (4452, 4251))                     # Added C
        self.assertEqual((v.GF_KINDLED, v.EMOTE_STATE_DANCE), (46, 10))                                # Added D
        self.assertEqual(v.DISPLAY_SPECTRAL_FOOTMAN, 30978)

    def test_the_wave_2_wrong_looks_are_not_wired(self):
        v = self.v
        wired_sv = set(v.STOCK_SPELL_VISUALS) | set(v.MINTED_SPELL_VISUALS) | set(v.MINTED_ELSEWHERE_SPELL_VISUALS)
        # Piccolo (a sound), Judgement of Light's heal 5560, Ground Smash 2643, Fire Cannon 180, Holy Channeling 11274,
        # Holy Ground 7667, Enchanting Lullaby's hearts 2576 (already above), the 40 yd stock Carrion fan 9099
        for sv, why in ((4682, "Piccolo: a sound only"), (5560, "the Judgement of Light heal sparkle"),
                        (2643, "Ground Smash: a shake"), (180, "Fire Cannon: no model"),
                        (11274, "Holy Channeling: no beam"), (7667, "Holy Ground: a one-shot"),
                        (9099, "Carrion Swarm: the 40 yd fan at the cast end plus a stun swirl")):
            with self.subTest(sv=sv):
                self.assertNotIn(sv, wired_sv, why)
        self.assertNotIn(v.GODI_INVISIBLE_TRAP_DO_NOT_USE, v.STOCK_GAMEOBJECT_DISPLAYS)
        self.assertEqual(v.GODI_INVISIBLE_TRAP_DO_NOT_USE, 1287)
        self.assertNotIn(v.FO_LULLABY_HEARTS, wired_sv)

    def test_the_corrected_looks_replace_the_wrong_ones(self):
        wired = set(self.v.STOCK_SPELL_VISUALS) | set(self.v.MINTED_SPELL_VISUALS)
        for sv, why in WRONG_SPELL_VISUALS.items():
            with self.subTest(sv=sv):
                self.assertNotIn(sv, wired, why)
        self.assertNotIn(self.v.GODI_TROLL_SKULL_PILE_DO_NOT_USE, self.v.STOCK_GAMEOBJECT_DISPLAYS)
        self.assertEqual(self.v.GODI_TROLL_SKULL_PILE_DO_NOT_USE, 293)

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

    def test_every_stock_id_exists(self):
        if not (patch.DBC_DIR / "SpellVisual.dbc").is_file():
            self.skipTest("no model-visual-dbc working copy in this checkout")
        self.assertTrue(patch.check_stock_ids())


if __name__ == "__main__":
    unittest.main()
