"""
Blackrock Spire visuals (Blackrock Spire build, WP V-1 wave 1, V-2 wave 2): patch_blackrock_spire_vfx_models.py and
source/npcs/blackrock_spire/_visuals.py.

Covered: every minted id sits inside the `blackrock_spire` reservation, the row builders (wave 1: the Ascension spit
patch as an AREA and a STATE look, the war horn burst on the stock horn cast; wave 2: the held torch, the 6 yd
shadowflame pool, the magma pool ladder, the two brands, the 12 yd ring of fire, the ice wall creature display), the
constants module agreeing with the patch script, none of the wrong looks (handoff s3.10) coming back as a wired id, the
stock and shipped ids existing in the working-copy DBCs, and the SQL overlay.

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
    12075: "Torch 55049 (flames at the holder's feet, not the hand)",
    6801: "Battle Standard 22996 (animation only)",
    12037: "Lava Burn 54249 (a missile, no ground piece)",
    11497: "Scorched Earth 52393 (a white mist jet, not lava)",
}
# Looks that are right for one named use and wrong as anything else: every constant that carries the id must be one of
# the allowed names (the wave 1 Haymaker hit flash; wave 2: Gyth's breath cast is not a wall, Mark of Flames is a 3 s
# impact not a 12 s brand, Lava Shield is a 1.5 s flash not the Heat look).
ALLOWED_ONLY_AS = {
    9766: {"OM_HAYMAKER_FLASH"},
    10569: {"RG_FREEZING_BREATH_CAST"},
    3479: {"DR_COLLAPSING_FLASH"},
    1465: {"BE_HEAT_STACK_FLASH"},
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

    def test_waves_1_and_2_mint_only_the_ice_wall_display_and_no_gameobject_or_sound_row(self):
        minted = sorted(name for name in dir(patch)
                        if name.startswith(("CDI_", "CMD_", "GODI_", "SOUND_")) and not name.endswith("_BLOCK"))
        self.assertEqual(minted, ["CDI_ICE_WALL", "CMD_ICE_WALL"])
        for row in patch.build_creature_model_rows() + patch.build_creature_display_rows():
            self.assertTrue(patch.CREATURE_DISPLAY_BLOCK["start"] <= row["ID"] <= patch.CREATURE_DISPLAY_BLOCK["end"])

    def test_waves_1_and_2_use_visual_ids_90600_to_90616(self):
        self.assertEqual({r["ID"] for r in patch.build_spellvisual_rows()}, set(range(90600, 90617)))
        self.assertEqual({r["ID"] for r in patch.build_kit_rows()}, set(range(90600, 90617)))
        self.assertEqual({r["ID"] for r in patch.build_effect_name_rows()}, set(range(90600, 90613)))


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
            if stem == "flamecircleeffect":         # the stock ring model: nothing to pack
                self.assertEqual(effect["FileName"], patch.STOCK_FLAME_CIRCLE_FILE)
                continue
            self.assertIn(f"{stem}.m2", packed)
            self.assertIn(f"{stem}00.skin", packed)
        self.assertEqual(len(packed), len(patch.SPELLS_ASSETS))
        self.assertNotIn("t_vfx_hero_explosion_blur.blp", packed)       # stock, not repacked

    def test_the_pending_sql_deletes_exactly_the_minted_ids(self):
        sql = patch.build_pending_sql()
        self.assertIn("DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90600 AND 90616;", sql)
        self.assertIn("DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90740 AND 90740;", sql)
        self.assertIn("DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90740 AND 90740;", sql)
        for table in ("gameobjectdisplayinfo", "soundentries"):
            self.assertNotIn(table, sql)

    def test_the_asset_list_has_no_duplicates(self):
        names = [Path(p).name.lower() for _, p in patch.SPELLS_ASSETS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 27)        # wave 1: 2 models + 2 skins + 6 textures; wave 2: 4 + 4 + 9


class Wave2RowTest(unittest.TestCase):
    def setUp(self):
        self.effects = {r["ID"]: r for r in patch.build_effect_name_rows()}
        self.kits = {r["ID"]: r for r in patch.build_kit_rows()}
        self.visuals = {r["ID"]: r for r in patch.build_spellvisual_rows()}

    def _kits(self, sv_id):
        row = self.visuals[sv_id]
        self.assertEqual(row["HasMissile"], 0)
        self.assertEqual(row["MissileAttachment"], -1)
        used = [k for k in ("PrecastKit", "CastKit", "ImpactKit", "StateKit", "ChannelKit", "PersistentAreaKit",
                            "InstantAreaKit") if row[k]]
        self.assertEqual(len(used), 1, used)
        return used[0], self.kits[row[used[0]]]

    def test_the_held_torch_is_the_stock_torch_in_the_right_weapon_slot_of_a_state_kit(self):
        which, kit = self._kits(patch.SV_TORCH_HELD)
        self.assertEqual(which, "StateKit")
        self.assertEqual(kit["RightWeaponEffect"], patch.STOCK_TORCH_EFFECT)
        self.assertEqual(patch.STOCK_TORCH_EFFECT, 3032)
        self.assertEqual({k for k, v in kit.items() if k.endswith("Effect") and v}, {"RightWeaponEffect"})

    def test_the_shadowflame_pool_is_the_wave_1_quad_at_the_6_yd_scale_as_area_and_state(self):
        effect = self.effects[patch.EFFECT_SHADOWFLAME_POOL]
        self.assertEqual(effect["FileName"], "SPELLS\\mannoroth_gooflowshadow_state_projected.mdx")
        self.assertEqual(effect["AreaEffectSize"], 0.0)
        self.assertAlmostEqual(effect["Scale"] * patch.SPIT_PATCH_YARDS, 2 * patch.SHADOWFLAME_POOL_RADIUS, delta=1.0)
        which, kit = self._kits(patch.SV_SHADOWFLAME_POOL_AREA)
        self.assertEqual((which, kit["WorldEffect"]), ("PersistentAreaKit", patch.EFFECT_SHADOWFLAME_POOL))
        which, kit = self._kits(patch.SV_SHADOWFLAME_POOL_STATE)
        self.assertEqual((which, kit["BaseEffect"]), ("StateKit", patch.EFFECT_SHADOWFLAME_POOL))
        self.assertGreater(effect["Scale"], self.effects[patch.EFFECT_SPIT_PATCH]["Scale"])     # 6 yd > the 4 yd spit

    def test_the_magma_pool_ladder_has_a_rung_per_yard_from_4_to_10(self):
        self.assertEqual(patch.MAGMA_POOL_RADII, (4, 5, 6, 7, 8, 9, 10))
        self.assertEqual(set(patch.SV_MAGMA_POOL_STATE), set(patch.MAGMA_POOL_RADII))
        previous = 0.0
        for i, radius in enumerate(patch.MAGMA_POOL_RADII):
            with self.subTest(radius=radius):
                effect = self.effects[patch.EFFECT_MAGMA_POOL_FIRST + i]
                self.assertEqual(effect["FileName"], "SPELLS\\magmazone.mdx")
                self.assertEqual(effect["AreaEffectSize"], 0.0)
                self.assertAlmostEqual(effect["Scale"] * patch.MAGMA_DISC_RADIUS, radius, delta=0.01)
                self.assertGreater(effect["Scale"], previous)
                previous = effect["Scale"]
                which, kit = self._kits(patch.SV_MAGMA_POOL_STATE[radius])
                self.assertEqual((which, kit["BaseEffect"]), ("StateKit", effect["ID"]))

    def test_the_ladder_covers_the_beasts_pool_radii_normal_and_heroic_with_heat(self):
        # N 5 yd, H 4.5 yd, plus 0.5 yd per Heat stack (SP, The Beast mechanic 2); a pool past 10 yd keeps rung 10.
        for base in (5.0, 4.5):
            for heat in range(0, 12):
                radius = base + 0.5 * heat
                with self.subTest(base=base, heat=heat):
                    if radius <= patch.MAGMA_POOL_RADII[-1]:
                        rung = min(r for r in patch.MAGMA_POOL_RADII if r >= radius)
                        self.assertLess(rung - radius, 1.0)      # never more than a yard of overdraw

    def test_the_brands_are_the_two_odyn_runes_as_base_states(self):
        for sv_id, effect_id, model in ((patch.SV_BRAND_SEARING, patch.EFFECT_BRAND_SEARING,
                                         "7fx_odyn_runicbrandorange_state"),
                                        (patch.SV_BRAND_COLLAPSING, patch.EFFECT_BRAND_COLLAPSING,
                                         "7fx_odyn_runicbrandyellow_state")):
            with self.subTest(model=model):
                self.assertEqual(self.effects[effect_id]["FileName"], f"SPELLS\\{model}.mdx")
                self.assertEqual(self.effects[effect_id]["Scale"], patch.BRAND_SCALE)
                which, kit = self._kits(sv_id)
                self.assertEqual((which, kit["BaseEffect"]), ("StateKit", effect_id))
        self.assertNotEqual(patch.SV_BRAND_SEARING, patch.SV_BRAND_COLLAPSING)

    def test_the_ring_of_fire_is_the_stock_flame_circle_scaled_to_12_yd(self):
        effect = self.effects[patch.EFFECT_RING_OF_FIRE]
        self.assertEqual(effect["FileName"], "Spells\\FlameCircleEffect.mdx")
        self.assertEqual(effect["AreaEffectSize"], 0.0)
        self.assertAlmostEqual(effect["Scale"], 3.0 * 12 / 7, places=5)     # stock: scale 3.0 for radius 7
        which, kit = self._kits(patch.SV_RING_OF_FIRE_AREA)
        self.assertEqual((which, kit["WorldEffect"]), ("PersistentAreaKit", patch.EFFECT_RING_OF_FIRE))
        which, kit = self._kits(patch.SV_RING_OF_FIRE_STATE)
        self.assertEqual((which, kit["BaseEffect"]), ("StateKit", patch.EFFECT_RING_OF_FIRE))

    def test_the_ice_wall_is_the_ascension_icewall_at_0_6(self):
        (model,) = patch.build_creature_model_rows()
        (display,) = patch.build_creature_display_rows()
        self.assertEqual(model["ID"], display["ModelID"])
        self.assertEqual(display["ID"], patch.CDI_ICE_WALL)
        self.assertEqual(model["ModelName"], "SPELLS\\Frostwhisper_Icewall_Base.mdx")
        self.assertEqual(model["ModelScale"], 0.6)
        self.assertEqual(display["CreatureModelScale"], 1.0)
        self.assertEqual(display["CreatureModelAlpha"], 255)
        # two pieces of about 16 yd with an 8 yd gap fill a 40 yd arena (SP RG6: the arena's full width, one 8 yd gap)
        self.assertAlmostEqual(26.9 * model["ModelScale"], 16.1, delta=0.1)

    def test_every_wave_2_kit_points_at_effects_that_exist(self):
        for kit in self.kits.values():
            for field, value in kit.items():
                if field.endswith("Effect") and value:
                    with self.subTest(kit=kit["ID"], field=field):
                        self.assertTrue(value in self.effects or value == patch.STOCK_TORCH_EFFECT, value)


class VisualsModuleTest(unittest.TestCase):
    def setUp(self):
        self.v = _visuals()

    def test_the_minted_ids_match_the_patch_script(self):
        for name in ("SV_SPIT_PATCH_AREA", "SV_SPIT_PATCH_STATE", "SV_HORN_BLOWN", "SV_TORCH_HELD",
                     "SV_SHADOWFLAME_POOL_AREA", "SV_SHADOWFLAME_POOL_STATE", "SV_MAGMA_POOL_STATE",
                     "SV_BRAND_SEARING", "SV_BRAND_COLLAPSING", "SV_RING_OF_FIRE_AREA", "SV_RING_OF_FIRE_STATE"):
            with self.subTest(name=name):
                self.assertEqual(getattr(self.v, name), getattr(patch, name))
        self.assertEqual(set(self.v.MINTED_SPELL_VISUALS), {r["ID"] for r in patch.build_spellvisual_rows()})
        self.assertEqual(self.v.MINTED_CREATURE_DISPLAYS, (patch.CDI_ICE_WALL,))
        self.assertEqual(self.v.DISPLAY_ICE_WALL, patch.CDI_ICE_WALL)
        self.assertEqual(self.v.MAGMA_POOL_RADII, patch.MAGMA_POOL_RADII)
        self.assertEqual(len(self.v.MINTED_SPELL_VISUALS), len(set(self.v.MINTED_SPELL_VISUALS)))

    def test_the_wave_2_gap_picks(self):
        v = self.v
        self.assertEqual((v.EM_RING_LAUNCH, v.EM_SMOLDER, v.EM_FLARE_COLUMN, v.EM_SEARING_BOND, v.EM_SEARED),
                         (13372, 10775, 9727, 1946, 6764))                                              # gap 16
        self.assertEqual((v.SK_SPEAR_THROW, v.SK_TORCH_TOSS, v.SK_TORCH_CATCH, v.SK_FLAME_WREATH),
                         (11993, 10211, 10302, 4101))                                                   # gap 17
        self.assertEqual(v.SK_SPEAR_THROW, v.WT_SPEAR_THROW)
        self.assertEqual((v.RG_SHADOWFLAME_RAIN, v.DISPLAY_BATTLE_STANDARD, v.RG_THUMBS_DOWN_SKULL,
                          v.RG_THUMBS_DOWN_HIT), (6700, 14542, 90506, 13549))                           # gap 18
        self.assertEqual((v.BE_HEAT, v.BE_MAGMA_SPLIT, v.BE_ROAR), (8581, 4321, 247))                   # gap 19
        self.assertEqual((v.DR_RING_OF_FIRE, v.DR_FINESSE, v.DR_HUMBLED, v.DISPLAY_BLACK_DRAKONID,
                          v.DR_SEARED_FLESH), (8386, 8996, 210, 14885, 9112))                           # gap 20
        self.assertEqual(v.EMOTE_STATE_KNEEL, 68)

    def test_the_held_flame_is_the_torch_state_not_the_stock_torch(self):
        v = self.v
        self.assertEqual(v.SV_TORCH_HELD, 90603)
        self.assertNotEqual(v.SK_HELD_FLAME_ALT, 12075)
        self.assertEqual(v.SK_HELD_FLAME_ALT, v.BE_HEAT)         # Fire Shield, the lasting flame whirl

    def test_lasting_looks_use_lasting_states(self):
        v = self.v
        self.assertEqual(v.EM_SEARING_BOND, 1946)               # Burning Brand's state kit, not Searing Pain's 1.1 s
        self.assertEqual(v.EM_SEARED, v.DR_COLLAPSING_BRAND_ALT)
        self.assertNotEqual(v.EM_SEARING_BOND, v.EM_SEARING_BOND_ALT)
        self.assertNotIn(v.DR_COLLAPSING_FLASH, (v.SV_BRAND_COLLAPSING, v.DR_COLLAPSING_BRAND_ALT))

    def test_the_magma_pool_states_are_the_minted_ladder(self):
        self.assertEqual(sorted(self.v.SV_MAGMA_POOL_STATE.values()), list(range(90606, 90613)))

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
                if sv in ALLOWED_ONLY_AS:
                    continue
                self.assertNotIn(sv, wired, why)

    def test_the_looks_that_are_right_for_one_use_only_are_wired_to_that_use_only(self):
        self.assertEqual(self.v.OM_HAYMAKER_FLASH, 9766)
        self.assertNotEqual(self.v.VO_AXE_RAIN, 9766)
        for sv, allowed in ALLOWED_ONLY_AS.items():
            carriers = {name for name, value in vars(self.v).items()
                        if name.isupper() and type(value) is int and value == sv}
            with self.subTest(sv=sv):
                self.assertEqual(carriers, allowed)

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
