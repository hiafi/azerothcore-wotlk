"""
Blackrock Depths visuals (Blackrock Depths build, WP V-1 wave 1 + V-2 wave 2): patch_blackrock_depths_vfx_models.py and
source/npcs/blackrock_depths/_visuals.py.

Covered: every minted id sits inside the `blackrock_depths` reservation, the row builders (the Lager Puddle, the crack
piece, Moira's fire cage, the security field rungs, the purple ring, the Portal Anchor, the 6 yd web patch, the two keg
displays), the constants module agreeing with the patch script, none of the wrong looks (handoff s3.10) coming back as a
wired id, every int constant being accounted for in a category tuple, the stock and shipped ids existing in the
working-copy DBCs, the asset list, and the SQL overlay, including the keg displays' creature_model_info rows (no row =
the creature cannot spawn, review R-1-KIT M2) and the hand rev that gives the four live custom displays theirs.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_vfx.py
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import patch_blackrock_depths_vfx_models as patch  # noqa: E402
from lib import source  # noqa: E402

REPO_ROOT = TOOL_ROOT.parents[1]
MODEL_INFO_REV = (REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"
                  / "rev_creature_model_info_custom_displays.sql")

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
BRD = IDS["reservations"]["blackrock_depths"]
VISUALS_FILE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths" / "_visuals.py"
PACKAGE = VISUALS_FILE.parent

# The SpellVisual picks the doc or the build spec had wrong (handoff s3.10, VISUALS-REPORT headline findings and
# "WRONG (doc)" rows) and what each really plays: none may be wired, except as the named use in ALLOWED_ONLY_AS.
WRONG_SPELL_VISUALS = {
    5043: "Eruption 17731 (anim + sound, nothing drawn: Trial by Fire is the cone marker + Massive Eruption bursts)",
    14843: "Hurl Axe 70161 (no missile model: the axe is invisible in flight)",
    227: "Whirlwind 15589 (a cleave flash on the chest, no whirl)",
    10407: "Chemical Flames 36253 (fel green fire)",
    9466: "Volcanic Geyser 40118 (blue fire)",
    10856: "Fire Beam 49119 (blue flame and a grey smoke chain)",
    11274: "Holy Channeling 51361 (hand glows, no beam)",
    10980: "Penance 47540 (hand glows, no beam)",
    7434: "Eye Beam 26134 (no beam: the chest impact only)",
    3948: "Smash 54458 (blood and a stun swirl, not splinters)",
    11840: "Living Bomb 20475 (a fire whirl)",
    12396: "Horn of Winter 57330 (an icy breath puff, wrong for a kennel horn)",
    9379: "Flame Wave 33804 (fire hands, no ring)",
    7597: "Chains of Kel'Thuzad 28410 (no chain between the pair)",
    12479: "Beam of Light 57772 (a 63 yd tall pillar)",
    8305: "Black Blood 35331 (green blood)",
    4229: "Static Field 18147 (a one-frame flash, no field)",
    14506: "Flame Breath 18435 (anim and sound, no stream)",
    13093: "Petrifying Breath 62030 (sand, not fire)",
    8455: "Cave In 36240 (a faint particle puff)",
    3944: "Emberseer Transform 16052 (a blue arcane dome)",
    13174: "Activate Construct 62488 (a fire strike, not a stone golem rising)",
    8159: "Arcane Orb 34172 (a flight with no orb: the orb is a unit display)",
    3640: "Gout of Flame 15529 (anim only: the statue would not glow)",
    223: "Shadow Mark 27825 (a dust whirl, not a mark)",
    5019: "Curse of Doom 603 (a 3 s impact on a 6 s mark)",
    7374: "Gloom Band 25287 (anim and sound only)",
    2816: "Drunken Stupor 14870 (a stun swirl on a slowed player)",
    14985: "Acid Burst 70744 (a chest flash, not a ground burst at a corpse)",
    372: "Vicious Rend 14331 (a single blood puff on a 15 s bleed)",
    290: "Fire Ward 15041 (a one-shot chest impact on a lasting absorb)",
    757: "Garrote 703 (a single blood puff on a stacking bleed)",
}
# Looks that are right for one named use and wrong as anything else: every constant that carries the id must be one of
# the allowed names.
ALLOWED_ONLY_AS = {
    7434: {"ST_EYE_IMPACT"},                                          # the hit's chest impact, never the beam
    12714: {"GZ_WALL_IMPACT", "BG_BOULDER_LAND"},                     # shake + sound, never a falling boulder
    10917: {"BG_FISSURE_BURST"},                                      # the initial burst, never the 40 yd line
    10383: {"IN_FIRE_STORM_CAST", "FL_KINDLING_CHANNEL", "EM_FLAMESTRIKE_CAST"},   # cast hands, never the 23 yd patch
    870: {"GZ_KILLING_FRENZY_FLASH", "HU_LAGER_BUZZ_FLASH"},          # one flash per stack, never a lasting buff
    4345: {"CH_TITLE_HOLDER_FLASH"},                                  # the arrival flash, never the fight-long buff
    5319: {"GR_FRENZY_FLASH"},                                        # the application flash, never the 15 s Frenzy
}
# Creature displays and object displays that must never be wired.
WRONG_CREATURE_DISPLAYS = {24860: "InvisibleStalker x1.8: a keg unit on it draws nothing"}


def _visuals():
    spec = importlib.util.spec_from_file_location("blackrock_depths_visuals_under_test", VISUALS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IdBlockTest(unittest.TestCase):
    def test_the_script_blocks_are_the_reservation(self):
        self.assertEqual(patch.VISUAL_BLOCK, BRD["spellvisual"])
        self.assertEqual(patch.VISUAL_BLOCK, {"start": 90650, "end": 90699})
        self.assertEqual(patch.GODI_BLOCK, BRD["gameobjectdisplayinfo"])
        self.assertEqual(patch.CREATURE_DISPLAY_BLOCK, BRD["creaturedisplayinfo"])
        self.assertEqual(patch.CREATURE_DISPLAY_BLOCK, BRD["creaturemodeldata"])

    def test_every_minted_id_is_inside_the_block(self):
        rows = patch.build_effect_name_rows() + patch.build_kit_rows() + patch.build_spellvisual_rows()
        for row in rows:
            with self.subTest(id=row["ID"]):
                self.assertTrue(patch.VISUAL_BLOCK["start"] <= row["ID"] <= patch.VISUAL_BLOCK["end"])
        for row in patch.build_creature_model_rows() + patch.build_creature_display_rows():
            with self.subTest(creature_display=row["ID"]):
                self.assertTrue(patch.CREATURE_DISPLAY_BLOCK["start"] <= row["ID"]
                                <= patch.CREATURE_DISPLAY_BLOCK["end"])

    def test_ids_are_unique_per_table(self):
        for builder in (patch.build_effect_name_rows, patch.build_kit_rows, patch.build_spellvisual_rows,
                        patch.build_creature_model_rows, patch.build_creature_display_rows):
            ids = [r["ID"] for r in builder()]
            self.assertEqual(len(ids), len(set(ids)), builder.__name__)

    def test_the_visual_ids_are_90650_to_90659_and_the_spare_range_is_untouched(self):
        for builder in (patch.build_effect_name_rows, patch.build_kit_rows, patch.build_spellvisual_rows):
            self.assertEqual({r["ID"] for r in builder()}, set(range(90650, 90660)), builder.__name__)

    def test_no_gameobject_display_or_sound_row_is_minted(self):
        minted = sorted(name for name in dir(patch)
                        if name.startswith(("GODI_", "SOUND_")) and not name.endswith("_BLOCK"))
        self.assertEqual(minted, [])
        self.assertEqual(sorted(name for name in dir(patch) if name.startswith(("CDI_", "CMD_"))),
                         ["CDI_LAGER_KEG", "CDI_LAGER_KEG_ALT", "CMD_LAGER_KEG", "CMD_LAGER_KEG_ALT"])


class RowTest(unittest.TestCase):
    def setUp(self):
        self.effects = {r["ID"]: r for r in patch.build_effect_name_rows()}
        self.kits = {r["ID"]: r for r in patch.build_kit_rows()}
        self.visuals = {r["ID"]: r for r in patch.build_spellvisual_rows()}

    def _state(self, sv_id):
        """The one StateKit of a SpellVisual row and its BaseEffect row; every row is a lasting STATE look."""
        row = self.visuals[sv_id]
        self.assertEqual(row["HasMissile"], 0)
        self.assertEqual(row["MissileAttachment"], -1)
        used = [k for k in ("PrecastKit", "CastKit", "ImpactKit", "StateKit", "ChannelKit", "PersistentAreaKit",
                            "InstantAreaKit") if row[k]]
        self.assertEqual(used, ["StateKit"])
        kit = self.kits[row["StateKit"]]
        self.assertEqual({k for k, v in kit.items() if k.endswith("Effect") and v}, {"BaseEffect"})
        return self.effects[kit["BaseEffect"]]

    def test_every_look_is_a_fixed_scale_state_with_kit_equal_effect_equal_visual_id(self):
        for sv_id, row in self.visuals.items():
            with self.subTest(id=sv_id):
                self.assertEqual(row["StateKit"], sv_id)
                self.assertEqual(self.kits[sv_id]["BaseEffect"], sv_id)
                effect = self._state(sv_id)
                self.assertEqual(effect["ID"], sv_id)
                self.assertEqual(effect["AreaEffectSize"], 0.0)       # a fixed size, not the spell radius

    def test_the_lager_puddle_is_the_beer_goo_at_0_21_for_a_5_yd_radius(self):
        effect = self._state(patch.SV_LAGER_PUDDLE)
        self.assertEqual(effect["FileName"], "SPELLS\\Goo_flow_state_wheat_beer.mdx")
        self.assertEqual(effect["Scale"], patch.LAGER_PUDDLE_SCALE)
        self.assertAlmostEqual(effect["Scale"] * patch.LAGER_PUDDLE_YARDS, 2 * patch.LAGER_PUDDLE_RADIUS, delta=1.0)

    def test_the_crack_piece_is_about_10_yd_across(self):
        effect = self._state(patch.SV_CRUMBLED_EDGE_CRACK)
        self.assertEqual(effect["FileName"], "SPELLS\\groundcrack_fire_state.mdx")
        self.assertAlmostEqual(effect["Scale"] * patch.CRACK_QUAD_YARDS, 10.0, delta=0.5)

    def test_moiras_fire_cage_is_the_stock_flame_circle_at_0_64(self):
        effect = self._state(patch.SV_MOIRA_FIRE_CAGE)
        self.assertEqual(effect["FileName"], "Spells\\FlameCircleEffect.mdx")
        self.assertEqual(effect["Scale"], 0.64)
        self.assertAlmostEqual(effect["Scale"], 3.0 / 7.0 * 1.5, places=2)   # stock: 3.0 for 7 yd; a 1.5 yd ring

    def test_the_security_field_has_a_rung_per_yard_from_6_to_9(self):
        self.assertEqual(patch.SECURITY_FIELD_RADII, (6, 7, 8, 9))
        self.assertEqual(set(patch.SV_SECURITY_FIELD), set(patch.SECURITY_FIELD_RADII))
        self.assertEqual(sorted(patch.SV_SECURITY_FIELD.values()), [90653, 90654, 90655, 90656])
        previous = 0.0
        for radius in patch.SECURITY_FIELD_RADII:
            with self.subTest(radius=radius):
                effect = self._state(patch.SV_SECURITY_FIELD[radius])
                self.assertEqual(effect["FileName"], "SPELLS\\target_arcane_state_centeronly.mdx")
                self.assertAlmostEqual(effect["Scale"] * patch.FIELD_DISC_RADIUS, radius, delta=0.01)
                self.assertGreater(effect["Scale"], previous)
                previous = effect["Scale"]

    def test_the_purple_ring_is_the_ascension_purple_brand_at_the_orange_brands_scale(self):
        effect = self._state(patch.SV_PURPLE_RING)
        self.assertEqual(effect["FileName"], "SPELLS\\7fx_odyn_runicbrandpurple_state.mdx")
        self.assertEqual(effect["Scale"], 1.0)

    def test_the_portal_anchor_is_the_stock_red_portal_at_a_third_of_its_height(self):
        effect = self._state(patch.SV_PORTAL_ANCHOR)
        self.assertEqual(effect["FileName"], "Spells\\Creature_SpellPortalLarge_Red.mdx")
        self.assertEqual(effect["Scale"], 0.4)

    def test_the_6_yd_web_patch_sits_between_the_shipped_5_and_7_yd_rows(self):
        effect = self._state(patch.SV_WEB_PATCH_6)
        self.assertEqual(effect["FileName"], "SPELLS\\Web_State.mdx")
        self.assertTrue(4.3 < effect["Scale"] < 6.0)        # Stratholme: 4.3 is 5 yd, 6.0 is 7 yd

    def test_the_keg_displays_are_stock_models_with_no_asset(self):
        models = {r["ID"]: r for r in patch.build_creature_model_rows()}
        displays = {r["ID"]: r for r in patch.build_creature_display_rows()}
        self.assertEqual(models[90770]["ModelName"], "World\\Goober\\G_Keg.mdx")
        self.assertEqual(models[90771]["ModelName"], "World\\GENERIC\\HUMAN\\PASSIVE DOODADS\\BeerKegs\\BeerKeg02.mdx")
        for id_, display in displays.items():
            with self.subTest(id=id_):
                self.assertEqual(display["ModelID"], id_)
                self.assertEqual(display["CreatureModelScale"], 1.0)
                self.assertEqual(display["CreatureModelAlpha"], 255)
                self.assertEqual(models[id_]["ModelScale"], 1.0)
        packed = " ".join(p.lower() for _, p in patch.SPELLS_ASSETS)
        self.assertNotIn("g_keg", packed)
        self.assertNotIn("beerkeg", packed)

    def test_every_asset_a_spells_row_points_at_is_in_the_asset_list(self):
        packed = {Path(p).name.lower() for _, p in patch.SPELLS_ASSETS}
        stock = {"flamecircleeffect", "creature_spellportallarge_red", "web_state"}      # stock models: nothing to pack
        for effect in self.effects.values():
            stem = effect["FileName"].split("\\")[-1].rsplit(".", 1)[0].lower()
            if stem in stock:
                continue
            with self.subTest(stem=stem):
                self.assertIn(f"{stem}.m2", packed)
                self.assertIn(f"{stem}00.skin", packed)

    def test_the_asset_list_has_no_duplicates_and_no_stock_texture(self):
        names = [Path(p).name.lower() for _, p in patch.SPELLS_ASSETS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 23)        # 4 models + 4 skins + 15 textures
        for stock_texture in ("t_vfx_border3b.blp", "t_vfx_lava_green.blp", "t_vfx_lava2.blp", "lavalump2.blp",
                              "glow128.blp"):
            self.assertNotIn(stock_texture, names)

    def test_the_pending_sql_deletes_exactly_the_minted_ids(self):
        sql = patch.build_pending_sql()
        self.assertIn("DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90650 AND 90659;", sql)
        self.assertIn("DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90770 AND 90771;", sql)
        self.assertIn("DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90770 AND 90771;", sql)
        for table in ("gameobjectdisplayinfo", "soundentries"):
            self.assertNotIn(table, sql)

    def test_the_pending_sql_gives_each_keg_display_a_creature_model_info_row(self):
        # Creature::InitEntry cancels the load of a creature on a display with no creature_model_info row (R-1-KIT M2).
        sql = patch.build_pending_sql()
        self.assertIn("DELETE FROM `creature_model_info` WHERE `DisplayID` IN (90770, 90771);", sql)
        self.assertIn("(90770, 1.3, 1.5, 2, 0)", sql)
        self.assertIn("(90771, 0.7, 0.8, 2, 0)", sql)
        self.assertEqual({d for d, _, _ in patch.CREATURE_MODEL_INFO}, {patch.CDI_LAGER_KEG, patch.CDI_LAGER_KEG_ALT})
        for display, radius, reach in patch.CREATURE_MODEL_INFO:
            with self.subTest(display=display):
                self.assertGreater(radius, 0)
                self.assertGreaterEqual(reach, 0.1)       # ObjectMgr resets a combat reach below 0.1

    def test_the_model_info_rows_land_after_the_display_rows_in_the_same_file(self):
        # ObjectMgr::LoadCreatureModelInfo dereferences the creaturedisplayinfo_dbc row: one import carries both.
        sql = patch.build_pending_sql()
        self.assertLess(sql.index("INSERT INTO `creaturedisplayinfo_dbc`"),
                        sql.index("INSERT INTO `creature_model_info`"))


class ModelInfoRevTest(unittest.TestCase):
    """rev_creature_model_info_custom_displays.sql: the four live custom displays with no creature_model_info row."""

    LIVE_DISPLAYS = {90002, 90003, 90004, 90740}     # Frozen Orb, Meteor Missile, Divine Star, the BRS frost wall

    def setUp(self):
        self.sql = MODEL_INFO_REV.read_text()

    def test_it_covers_exactly_the_four_displays_and_is_idempotent(self):
        self.assertIn("DELETE FROM `creature_model_info` WHERE `DisplayID` IN (90002, 90003, 90004, 90740);", self.sql)
        rows = re.findall(r"^\((\d+), ([\d.]+), ([\d.]+), 2, 0\)", self.sql, re.MULTILINE)
        self.assertEqual({int(r[0]) for r in rows}, self.LIVE_DISPLAYS)
        self.assertEqual(len(rows), len(self.LIVE_DISPLAYS))
        for _, radius, reach in rows:
            self.assertGreater(float(radius), 0)
            self.assertGreaterEqual(float(reach), 0.1)

    def test_it_never_names_a_display_without_a_dbc_row_in_its_own_file(self):
        # A model-info row for a display the DBC lacks crashes the boot, so the keg displays (whose DBC rows come from
        # the patch script's --sql-out) are not here: they ship with that script's output.
        self.assertFalse({90770, 90771} & {int(d) for d in re.findall(r"^\((\d+),", self.sql, re.MULTILINE)})

    def test_every_custom_display_a_boss_file_names_has_a_model_info_row(self):
        visuals = _visuals()
        have = {d for d, _, _ in patch.CREATURE_MODEL_INFO}
        for path in sorted(PACKAGE.glob("*.py")):
            if path.name.startswith("_"):
                continue
            for name in set(re.findall(r"\bDISPLAY_[A-Z0-9_]+\b", path.read_text())):
                value = getattr(visuals, name, None)
                if isinstance(value, int) and value >= 90000:
                    with self.subTest(file=path.name, display=name):
                        self.assertIn(value, have)


class VisualsModuleTest(unittest.TestCase):
    def setUp(self):
        self.v = _visuals()

    def _int_constants(self):
        return {name: value for name, value in vars(self.v).items()
                if name.isupper() and type(value) is int and not name.startswith("_")}

    def test_the_minted_ids_match_the_patch_script(self):
        for name in ("SV_LAGER_PUDDLE", "SV_CRUMBLED_EDGE_CRACK", "SV_MOIRA_FIRE_CAGE", "SV_SECURITY_FIELD",
                     "SV_PURPLE_RING", "SV_PORTAL_ANCHOR", "SV_WEB_PATCH_6"):
            with self.subTest(name=name):
                self.assertEqual(getattr(self.v, name), getattr(patch, name))
        self.assertEqual(set(self.v.MINTED_SPELL_VISUALS), {r["ID"] for r in patch.build_spellvisual_rows()})
        self.assertEqual(len(self.v.MINTED_SPELL_VISUALS), len(set(self.v.MINTED_SPELL_VISUALS)))
        self.assertEqual(set(self.v.MINTED_CREATURE_DISPLAYS), {patch.CDI_LAGER_KEG, patch.CDI_LAGER_KEG_ALT})
        self.assertEqual(self.v.DISPLAY_LAGER_KEG, patch.CDI_LAGER_KEG)
        self.assertEqual(self.v.DISPLAY_LAGER_KEG_ALT, patch.CDI_LAGER_KEG_ALT)
        self.assertEqual(self.v.SECURITY_FIELD_RADII, patch.SECURITY_FIELD_RADII)

    def test_every_int_constant_is_in_a_category_tuple(self):
        known = (set(self.v.STOCK_SPELL_VISUALS) | set(self.v.MINTED_SPELL_VISUALS) | set(self.v.SHIPPED_SPELL_VISUALS)
                 | set(self.v.STOCK_CREATURE_DISPLAYS) | set(self.v.MINTED_CREATURE_DISPLAYS)
                 | set(self.v.STOCK_GAMEOBJECT_DISPLAYS))
        for name, value in self._int_constants().items():
            with self.subTest(name=name):
                self.assertIn(value, known)

    def test_each_category_holds_the_right_kind_of_id(self):
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS",
                     "SHIPPED_SPELL_VISUALS"):
            ids = getattr(self.v, name)
            with self.subTest(name=name):
                self.assertTrue(all(isinstance(i, int) for i in ids))
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS"):
            self.assertFalse([i for i in getattr(self.v, name) if i >= 90000], name)
        self.assertTrue(all(90000 <= i < 90650 for i in self.v.SHIPPED_SPELL_VISUALS))
        self.assertTrue(all(90650 <= i <= 90699 for i in self.v.MINTED_SPELL_VISUALS))

    def test_the_wrong_looks_are_not_wired(self):
        wired = set(self.v.STOCK_SPELL_VISUALS) | set(self.v.MINTED_SPELL_VISUALS) | set(self.v.SHIPPED_SPELL_VISUALS)
        for sv, why in WRONG_SPELL_VISUALS.items():
            with self.subTest(sv=sv):
                if sv in ALLOWED_ONLY_AS:
                    continue
                self.assertNotIn(sv, wired, why)
        displays = set(self.v.STOCK_CREATURE_DISPLAYS) | set(self.v.MINTED_CREATURE_DISPLAYS)
        for cdi, why in WRONG_CREATURE_DISPLAYS.items():
            self.assertNotIn(cdi, displays, why)
            self.assertNotEqual(self.v.DISPLAY_LAGER_KEG, cdi)

    def test_the_looks_that_are_right_for_one_use_only_are_wired_to_that_use_only(self):
        for sv, allowed in ALLOWED_ONLY_AS.items():
            carriers = {name for name, value in self._int_constants().items() if value == sv}
            with self.subTest(sv=sv):
                self.assertEqual(carriers, allowed)

    def test_the_lasting_buffs_use_the_lasting_twins(self):
        v = self.v
        # Berserking (SV 6943) for the lasting hand glows; Bite (376) for bleeds; Adrenaline Rush (8996) for Evasion.
        self.assertEqual((v.GR_FRENZY, v.CH_TITLE_HOLDER, v.GZ_KILLING_FRENZY, v.HU_LIQUID_COURAGE), (6943,) * 4)
        self.assertEqual((v.EV_OPEN_WOUNDS, v.LE_VICIOUS_WOUND), (376, 376))
        self.assertEqual(v.LE_EVASION, 8996)
        self.assertEqual((v.TS_DOOM_MARK, v.TS_GLOOM_HEALING_MARK), (v.SHIPPED_KEENING_SKULL,) * 2)
        self.assertEqual(v.LG_FIRE_WARD, 6764)                  # Fire Reflector, not the one-shot SV 290

    def test_the_gap_picks(self):
        v = self.v
        self.assertEqual((v.GE_DOUBT_SWIRL, v.GE_DOUBT_SWIRL_BIG, v.GE_MIND_SEAR), (7433, 9231, 12121))   # gap 6
        self.assertEqual((v.AN_WEB_PATCH, v.AN_WEB_PATCH_ALT), (90503, 90501))                             # gap 13
        self.assertEqual(v.RL_CROWD_GIFT, 7526)                                                            # gap 16
        self.assertEqual((v.GODI_SHODDY_PILLAR, v.FD_PILLAR_SPAWN_BURST, v.FD_COLLAPSE_DUST),
                         (5073, 12718, 12855))                                                             # gap 21
        self.assertEqual(v.DISPLAY_EMBER_OF_INCENDIUS, 1405)                                               # gap 24
        self.assertEqual(v.GODI_FALLEN_BOULDER, 3711)                                                      # gap 25
        self.assertEqual((v.DISPLAY_LAGER_KEG, v.HU_LAGER_PUDDLE, v.HU_BOTTLE_TOSS), (90770, 90650, 9741))  # gap 29
        self.assertEqual(v.PH_TABLE_SPLINTERS, 90344)                                                      # gap 30
        self.assertEqual((v.GODI_GUZZLER_ROPE_PICKUP, v.GODI_HANGING_ROPE), (7538, 7717))                  # gap 31
        self.assertEqual((v.FL_BURNING_TRAIL, v.MG_DRIPPING_MAGMA), (90606, 90606))                        # gaps 32, 33
        self.assertEqual((v.DISPLAY_IMPERIAL_GUARD, v.MO_FIRE_CAGE, v.DISPLAY_AVATAR_OF_RAGNAROS),
                         (8750, 90652, 11121))                                                             # gap 34
        self.assertEqual((v.IN_CRUMBLED_EDGE_CRACK, v.IN_CINDER_TOSS, v.DISPLAY_INCENDIUS_GIANT),
                         (90651, 10211, 1204))                                                             # gap 35
        self.assertEqual(v.GODI_MOLE_MACHINE, 7510)                                                        # gap 26

    def test_the_corrections_of_s3_10(self):
        v = self.v
        self.assertEqual(v.GO_RETURNING_AXE, 3962)                  # not Hurl Axe
        self.assertEqual(v.GO_DERVISH_DANCE, 7428)                  # not Whirlwind 15589
        self.assertEqual(v.IN_FIRELORDS_BREATH, v.BG_MOLTEN_FURNACE)    # Heat Wave 3119 for every flame stream
        self.assertEqual(v.AR_FLAMETHROWER, 3119)                   # not Chemical Flames
        self.assertEqual(v.EM_NEMESIS_BEAM, 11500)                  # Light Beam, not Holy Channeling or Penance
        self.assertEqual(v.EM_FIRESTORM, 889)                       # Massive Eruption, not Volcanic Geyser
        self.assertEqual(v.RL_TRIAL_BURST, 889)                     # not Eruption
        self.assertEqual(v.AR_LIVEWIRE, 37)                         # the shield state, not Living Bomb
        self.assertEqual(v.AR_CHEMICAL_BOMB, 10395)
        self.assertNotEqual(v.TS_GATHER_DOOM_CAST, v.TS_SHADE)      # one purple state per role
        self.assertNotIn(v.RL_RAISED, (v.TS_GATHER_DOOM_CAST, v.TS_GATHER_DOOM_LANDING))
        self.assertNotEqual(v.HU_TIPSY, 2816)

    def test_the_boss_wps_requested_names(self):
        # The shared-file requests of the build reports (ORCH-NOTES F-1 queue): each name is the stock spell's own look,
        # read from the client Spell.dbc (SpellVisualID_1), or a documented pick.
        v = self.v
        expected = {
            "IN_CURSE": 3959, "VA_SUNDER_ARMOR": 39, "KO_EARTH_SHIELD": 7362, "KO_SEARING_BOLT": 67,
            "MG_WAR_STOMP": 2355, "FL_FIRE_BLAST": 2996, "AR_SALVAGED_CORE": 37, "GODI_GOLEM_PEDESTAL": 3311,
            "EV_SHADOW_BOLT_VOLLEY": 2318, "RW_VENOM_POOL": 90343, "IN_FIRELORDS_WILL": 8581,
            "TS_FROSTBOLT": 13, "TS_CONE_OF_COLD": 1007, "TS_FROST_NOVA": 17, "TS_BACKSTAB": 611, "TS_RUPTURE": 250,
            "TS_GOUGE": 256, "TS_MIND_BLAST": 3057, "TS_SHADOW_BOLT": 64, "TS_SHADOW_BOLT_VOLLEY": 2318,
            "TS_IMMOLATE": 46, "TS_FURIOUS_STOMP": 2355, "TS_DOOM_BLAST": 2318,
            "EM_HAND_OF_THAURISSAN": 143, "MO_MIND_BLAST": 3057, "MO_NECROSIS": 71, "EM_AVATAR_OF_FLAME": 46,
            "EM_FLAMES": 2519, "LG_WARD_REPEL": 3643, "LG_WARD_REPEL_ALT": 126,
        }
        for name, value in expected.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(v, name), value)
        self.assertEqual(v.GODI_GOLEM_PEDESTAL, v.GODI_FOURTH_PEDESTAL)
        self.assertIn(v.GODI_GOLEM_PEDESTAL, v.STOCK_GAMEOBJECT_DISPLAYS)
        for name in ("IN_CURSE", "VA_SUNDER_ARMOR", "KO_EARTH_SHIELD", "KO_SEARING_BOLT", "FL_FIRE_BLAST",
                     "EV_SHADOW_BOLT_VOLLEY", "LG_WARD_REPEL", "LG_WARD_REPEL_ALT", "TS_CONE_OF_COLD", "TS_BACKSTAB",
                     "TS_RUPTURE", "TS_GOUGE", "TS_MIND_BLAST", "TS_IMMOLATE", "EM_HAND_OF_THAURISSAN",
                     "EM_AVATAR_OF_FLAME", "EM_FLAMES", "MO_MIND_BLAST", "MO_NECROSIS"):
            with self.subTest(stock=name):
                self.assertIn(getattr(v, name), v.STOCK_SPELL_VISUALS)

    def test_every_look_the_seven_asks_for_by_name_exists(self):
        # the_seven.py picks `TS_*` by getattr with a fallback: a name that is missing silently loses its look.
        import ast
        tree = ast.parse((PACKAGE / "the_seven.py").read_text())
        asked = set()
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_look" and node.args
                    and isinstance(node.args[0], ast.Constant)):
                asked.add(node.args[0].value)
        self.assertGreaterEqual(len(asked), 12)
        for name in sorted(asked):
            with self.subTest(name=name):
                self.assertTrue(hasattr(self.v, name))

    def test_the_rungs_pick_the_smallest_size_at_or_above_the_radius(self):
        v = self.v
        self.assertEqual(v.lava_pool_rung(4.0), 90606)
        self.assertEqual(v.lava_pool_rung(4.5), 90607)
        self.assertEqual(v.lava_pool_rung(6.0), 90608)
        self.assertEqual(v.lava_pool_rung(12.0), 90612)             # past the top keeps the top
        self.assertEqual(v.security_field_rung(6.0), 90653)
        self.assertEqual(v.security_field_rung(7.5), 90655)
        self.assertEqual(v.security_field_rung(9.0), 90656)
        self.assertEqual(v.security_field_rung(20.0), 90656)

    def test_the_creature_scale_ranges_fit_the_designer_picks(self):
        # The Avatar: 58 yd tall at 1.0 and a 21 yd dais; the giant: 3 yd tall at 1.0 and an island edge.
        low, high = self.v.AVATAR_SCALE_RANGE
        self.assertTrue(0.12 <= low < high <= 0.18)
        low, high = self.v.INCENDIUS_GIANT_SCALE_RANGE
        self.assertTrue(8.0 <= low < high <= 10.0)

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
