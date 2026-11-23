"""
Scarlet Monastery visuals (Scarlet Monastery build, WP V, both waves): patch_scarlet_monastery_vfx_models.py and
source/npcs/scarlet_monastery/_visuals.py.

Covered: every minted id sits inside the `scarlet_monastery` reservation, the row builders (the Grave Rot rungs, the red
aura, the seal glows, the dream mist, the plague cloud, the Consecrated Hall, the two pillars, the spectre and
object displays), the constants module agreeing with the patch script, none of the wrong looks (handoff s3.10, VR
"WRONG" rows) coming back as a wired id, every int constant being accounted for in a category tuple of its table, the
stock and shipped ids existing in the working-copy DBCs, the asset list, and the SQL overlay, including a
creature_model_info row for every minted display (no row = the creature cannot spawn).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_vfx.py
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import patch_scarlet_monastery_vfx_models as patch  # noqa: E402
from lib import source  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
SM = IDS["reservations"]["scarlet_monastery"]
VISUALS_FILE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery" / "_visuals.py"
PACKAGE = VISUALS_FILE.parent

# The SpellVisual picks the doc or the build spec had wrong (handoff s3.10, VISUALS-REPORT "WRONG" rows) and what each
# really plays: none may be wired, except as the named use in ALLOWED_ONLY_AS.
WRONG_SPELL_VISUALS = {
    118: "Slime Pool 66882 (a one-shot gas puff, not a lasting pool: the rot rungs are 90550-90553)",
    9364: "Soul Drain 41303 (no beam: Torment is Drain Soul SV 788)",
    6742: "Arcane Channeling 23017 (a hand glow, no beam: the anchors are Magic Barrier SV 8795)",
    15256: "Blood Link 72202 (a missile model, not a tether: Blood Siphon SV 7270)",
    8116: "Summon Spirits 72478 (two hand glows: Raise Dead SV 4582)",
    6801: "Battle Standard 23034 (an animation only: the banner is a unit display)",
    9220: "Throw Axe 40563 (HasMissile with no missile model: SV 3962)",
    9766: "Axe Volley 42357 (no axe in flight: SV 3962)",
    6664: "Whirlwind 8989 (a dust cloud: the cyclone is SV 7428)",
    14914: "Holy Zone Visual 70571 (an 8.2 yd quad: the Hall is SV 90562, the blessed ground the Strat zone)",
    12479: "Beam of Light 57772 (a 135 x 135 x 315 yd model: the pillars are 90563 / 90564)",
    7582: "Ashbringer wielder aura 28282 (an empty State kit: Fury of the Ashbringer SV 8618)",
    7671: "Heated Hammer 29652 (the silver holy hammer, not red hot: Fireball SV 67)",
    7757: "Molten Armor 30482 (a one-shot head impact: Burning Brand SV 1946)",
    289: "Fire Shield 134 (a one-shot head impact: Burning Brand SV 1946)",
    10373: "Scalding Steam 50206 (one dust puff: Scalding Water SV 8657)",
    8314: "Flame Patch 35383 (a one-shot FireNova: the lava rungs)",
    7434: "Eye's Glare 26134 (no beam: Eyebeam SV 9205)",
    761: "Plague Cask 3256 (an InstantAreaKit, one-shot: Disease Cloud SV 7184)",
    13: "Frostbolt Volley 8398 (a missile + a head state: Frostbite SV 2837)",
}
# Looks that are right for one named use and wrong as anything else: every constant that carries the id must be one of
# the allowed names.
ALLOWED_ONLY_AS = {
    11627: {"VI_INTERROGATION_CAST"},                      # the cast animation only (its impact is a gray ash puff)
    10980: {"CV_VIGIL_CHANNEL", "WM_PENANCE_CHANNEL"},     # channel hands only, never a beam or a mark
    5600: {"CV_RIGHTEOUSNESS_BURST"},                      # Consecration shares a ground model with SV 11182
    11182: {"LS_CONSECRATION"},                            # Raging Consecration: the Monks only
    322: {"CV_JUSTICE_MARK", "LS_HAMMER_STUN"},            # the fist cast + stun swirl, never the thrown hammer
    7992: {"CV_SEAL_COMMAND"},                             # one-shot seal impacts: a flash, never the held glow
    7986: {"CV_SEAL_RIGHTEOUSNESS"},
    9504: {"CV_SEAL_JUSTICE"},
    15364: {"LK_SCENT"},                                   # Scent: the flash; the lasting mark is the ring
    1585: {"DN_DETONATION"},                               # fire themed: the cast look only
    9585: {"TH_BLOOD_RITUAL"},                             # shadow-purple hands, RISKY, the alternate is red
}
# Creature displays, object displays and items that must never be wired.
WRONG_CREATURE_DISPLAYS = {21955: "Rabbit (Argent Tome 29401 hides it): the Cursed Book is CDI 28103"}
WRONG_GAMEOBJECT_DISPLAYS = {197: "DWARVENBRAZIER02, a 1.8 yd brazier, not a forge (GODI 7044)",
                             7273: "KarazahnPedestals02, 5.2 yd tall: a relic pedestal is GODI 7695"}
WRONG_ITEMS = {13163: "Relentless Scythe (display 23683 is a greatsword): Soul Harvester 20536",
               5749: "Scythe Axe (display 19291 is a war axe): Soul Harvester 20536",
               37314: "High Executor's Branding Iron (IDI 65930 has no model): Hot Iron Poker 5532"}

# Prefix -> table of a constant of `_visuals.py`.
TABLE_BY_PREFIX = (("DISPLAY_", "creature"), ("GODI_", "gameobject"), ("ITEM_", "item"), ("IDI_", "itemdisplay"))


def _visuals():
    spec = importlib.util.spec_from_file_location("scarlet_monastery_visuals_under_test", VISUALS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has_working_copy() -> bool:
    return (patch.DBC_DIR / "SpellVisual.dbc").is_file()


class IdBlockTest(unittest.TestCase):
    def test_the_script_blocks_are_the_reservation(self):
        self.assertEqual(patch.VISUAL_BLOCK, SM["spellvisual"])
        self.assertEqual(patch.VISUAL_BLOCK, {"start": 90550, "end": 90599})
        self.assertEqual(patch.GODI_BLOCK, SM["gameobjectdisplayinfo"])
        self.assertEqual(patch.CREATURE_DISPLAY_BLOCK, SM["creaturedisplayinfo"])
        self.assertEqual(patch.CREATURE_DISPLAY_BLOCK, SM["creaturemodeldata"])
        self.assertEqual(patch.CREATURE_DISPLAY_BLOCK, {"start": 90800, "end": 90829})

    def test_every_minted_id_is_inside_the_block(self):
        rows = patch.build_effect_name_rows() + patch.build_kit_rows() + patch.build_spellvisual_rows()
        for row in rows:
            with self.subTest(id=row["ID"]):
                self.assertTrue(patch.VISUAL_BLOCK["start"] <= row["ID"] <= patch.VISUAL_BLOCK["end"])
        for row in patch.build_creature_model_rows():
            self.assertTrue(patch.CREATURE_DISPLAY_BLOCK["start"] <= row["ID"] <= patch.CREATURE_DISPLAY_BLOCK["end"])
        for cdi, _, _, _, _ in patch.CREATURE_MODEL_INFO:
            self.assertTrue(patch.CREATURE_DISPLAY_BLOCK["start"] <= cdi <= patch.CREATURE_DISPLAY_BLOCK["end"])

    def test_the_visual_ids_are_90550_to_90564_and_the_spare_range_is_untouched(self):
        for builder in (patch.build_effect_name_rows, patch.build_kit_rows, patch.build_spellvisual_rows):
            ids = [r["ID"] for r in builder()]
            self.assertEqual(sorted(ids), list(range(90550, 90565)), builder.__name__)

    def test_the_creature_displays_are_90800_to_90807(self):
        self.assertEqual(sorted(cdi for cdi, *_ in patch.CREATURE_MODEL_INFO), list(range(90800, 90808)))
        self.assertEqual(sorted(cmd for cmd, *_ in patch.OBJECT_MODELS), [90805, 90806, 90807])

    def test_no_gameobject_display_or_sound_row_is_minted(self):
        minted = sorted(name for name in dir(patch)
                        if name.startswith(("GODI_", "SOUND_")) and not name.endswith("_BLOCK"))
        self.assertEqual(minted, [])


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

    def test_the_grave_rot_rungs_are_the_gut_puddle_model_scaled_to_the_radius(self):
        self.assertEqual(patch.SV_GRAVE_ROT, {7: 90550, 8: 90551, 9: 90552, 10: 90553})
        previous = 0.0
        for radius, sv_id in sorted(patch.SV_GRAVE_ROT.items()):
            with self.subTest(radius=radius):
                effect = self._state(sv_id)
                self.assertEqual(effect["FileName"], "SPELLS\\goo_flow_state.mdx")
                self.assertAlmostEqual(effect["Scale"] * patch.GOO_QUAD_YARDS / 2, radius, delta=0.6)
                self.assertGreater(effect["Scale"], previous)
                previous = effect["Scale"]
        # the shipped Strat 6 yd rung is scale 0.25: the same line
        self.assertAlmostEqual(patch.GRAVE_ROT_REFERENCE[1] * patch.GOO_QUAD_YARDS / 2, 6, delta=0.6)

    def test_the_red_aura_is_the_stock_blood_state(self):
        effect = self._state(patch.SV_RED_AURA)
        self.assertEqual(effect["FileName"].lower(), "spells\\deathknight_plaguestrikestatered.mdx")
        self.assertEqual(effect["Scale"], 1.0)

    def test_the_seal_glows_are_the_three_stock_impact_models(self):
        names = {patch.SV_SEAL_COMMAND: "sealofcommand_impact_base", patch.SV_SEAL_RIGHTEOUSNESS:
                 "sealofrighteous_impact_base", patch.SV_SEAL_JUSTICE: "sealofsalvation_impact_base"}
        for sv_id, stem in names.items():
            with self.subTest(stem=stem):
                self.assertTrue(self._state(sv_id)["FileName"].lower().endswith(f"{stem}.mdx"))

    def test_the_dream_mist_grows_6_9_12(self):
        self.assertEqual(patch.SV_DREAM_MIST, {6: 90558, 9: 90559, 12: 90560})
        scales = [self._state(patch.SV_DREAM_MIST[r])["Scale"] for r in (6, 9, 12)]
        self.assertEqual(scales, [1.5, 2.25, 3.0])
        for r in (6, 9, 12):
            self.assertEqual(self._state(patch.SV_DREAM_MIST[r])["FileName"], "Spells\\LargeGreenRadiationFog.mdx")

    def test_the_plague_cloud_is_the_stock_green_fog(self):
        effect = self._state(patch.SV_PLAGUE_CLOUD)
        self.assertEqual(effect["FileName"], "Spells\\GreenRadiationFog.mdx")
        self.assertEqual(effect["Scale"], 3.0)

    def test_the_consecrated_hall_covers_the_pit_and_the_ledge(self):
        effect = self._state(patch.SV_CONSECRATED_HALL)
        self.assertEqual(effect["FileName"], "SPELLS\\holyzone.mdx")
        self.assertEqual(effect["Scale"], patch.HALL_SCALE)
        self.assertAlmostEqual(effect["Scale"] * patch.HOLYZONE_YARDS_PER_SCALE, patch.HALL_RADIUS, delta=0.05)
        self.assertGreaterEqual(patch.HALL_RADIUS, 25.5)           # NAVMESH: the ledge ring runs out to r 25.5
        # the Strat rungs: 8 yd is scale 2.5 on the same model
        self.assertAlmostEqual(2.5 * patch.HOLYZONE_YARDS_PER_SCALE, 8.0, delta=0.05)

    def test_the_pillars_are_the_ascension_model_at_1_and_2(self):
        for sv_id, scale in ((patch.SV_PILLAR_3, 1.0), (patch.SV_PILLAR_6, 2.0)):
            with self.subTest(id=sv_id):
                effect = self._state(sv_id)
                self.assertEqual(effect["FileName"], "SPELLS\\7fx_lightforged_vindicaar_lightsjudgement_impact.mdx")
                self.assertEqual(effect["Scale"], scale)
        self.assertAlmostEqual(patch.PILLAR_WIDTH_YARDS * 1.0, 3.0, delta=0.2)
        self.assertAlmostEqual(patch.PILLAR_WIDTH_YARDS * 2.0, 6.0, delta=0.3)

    def test_every_asset_a_spells_row_points_at_is_in_the_asset_list(self):
        packed = {Path(p).name.lower() for _, p in patch.SPELLS_ASSETS}
        for effect in self.effects.values():
            if effect["FileName"].lower() in {f.lower() for f in patch.STOCK_EFFECT_FILES}:
                continue
            stem = effect["FileName"].split("\\")[-1].rsplit(".", 1)[0].lower()
            with self.subTest(stem=stem):
                self.assertIn(f"{stem}.m2", packed)
                self.assertIn(f"{stem}00.skin", packed)

    def test_the_asset_list_is_14_files_with_no_duplicates_and_no_stock_model(self):
        names = [Path(p).name.lower() for _, p in patch.SPELLS_ASSETS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 14)        # 1 model + 1 skin + 12 textures
        self.assertEqual(sum(n.endswith(".m2") for n in names), 1)
        self.assertEqual(sum(n.endswith(".skin") for n in names), 1)
        for stock in patch.STOCK_EFFECT_FILES:
            self.assertNotIn(Path(stock.replace("\\", "/")).name.lower().replace(".mdx", ".m2"), names)


@unittest.skipUnless(_has_working_copy(), "no model-visual-dbc working copy in this checkout")
class CreatureDisplayRowTest(unittest.TestCase):
    def setUp(self):
        self.displays = {r["ID"]: r for r in patch.build_creature_display_rows()}
        self.models = {r["ID"]: r for r in patch.build_creature_model_rows()}

    def test_the_spectres_copy_their_base_display_at_alpha_128_and_140(self):
        base = patch._stock_display_rows()
        for cdi, base_id, alpha in patch.SPECTRES:
            with self.subTest(display=cdi):
                row, stock = self.displays[cdi], base[base_id]
                self.assertEqual(row["CreatureModelAlpha"], alpha)
                for key in stock:
                    if key not in ("ID", "CreatureModelAlpha"):
                        self.assertEqual(row[key], stock[key], key)
        self.assertEqual([a for _, _, a in patch.SPECTRES], [128, 128, 128, 128, 140])
        self.assertEqual([b for _, b, _ in patch.SPECTRES], [25917, 25842, 10339, 25841, 16139])

    def test_the_spectres_reuse_a_stock_model_row(self):
        # CreatureModelData rows exist for every ModelID (the spectres add none).
        from lib import dbcfile, dbcfmt
        stock = {r["ID"] for r in dbcfile.read_dbc(patch.DBC_DIR / "CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA)}
        for cdi, _, _ in patch.SPECTRES:
            self.assertIn(self.displays[cdi]["ModelID"], stock)
            self.assertNotIn(cdi, self.models)

    def test_the_object_displays_are_stock_models_with_no_asset(self):
        self.assertEqual(self.models[90805]["ModelName"].lower().rsplit("\\", 1)[-1], "booklargeopen02.mdx")
        self.assertEqual(self.models[90806]["ModelName"].lower().rsplit("\\", 1)[-1], "crimsonbanner01.mdx")
        self.assertEqual(self.models[90807]["ModelName"].lower().rsplit("\\", 1)[-1], "axe_2h_war_c_01.mdx")
        for cmd in (90805, 90806, 90807):
            with self.subTest(display=cmd):
                self.assertEqual(self.displays[cmd]["ModelID"], cmd)
                self.assertEqual(self.displays[cmd]["CreatureModelScale"], 1.0)
                self.assertEqual(self.displays[cmd]["CreatureModelAlpha"], 255)
                self.assertGreater(self.models[cmd]["CollisionHeight"], 0)
        packed = " ".join(p.lower() for _, p in patch.SPELLS_ASSETS)
        for stem in ("booklargeopen", "crimsonbanner", "axe_2h_war"):
            self.assertNotIn(stem, packed)


class SqlTest(unittest.TestCase):
    def setUp(self):
        if not _has_working_copy():
            self.skipTest("no model-visual-dbc working copy in this checkout")
        self.sql = patch.build_pending_sql()

    def test_the_pending_sql_deletes_exactly_the_minted_ids(self):
        self.assertIn("DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90550 AND 90564;", self.sql)
        self.assertIn("DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90805 AND 90807;", self.sql)
        self.assertIn("DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90800 AND 90807;", self.sql)
        for table in ("gameobjectdisplayinfo", "soundentries"):
            self.assertNotIn(table, self.sql)

    def test_every_minted_display_has_a_creature_model_info_row(self):
        # Creature::InitEntry cancels the load of a creature on a display with no creature_model_info row.
        ids = ", ".join(str(i) for i in range(90800, 90808))
        self.assertIn(f"DELETE FROM `creature_model_info` WHERE `DisplayID` IN ({ids});", self.sql)
        rows = re.findall(r"^\((\d+), ([\d.]+), ([\d.]+), (\d), (\d)\)", self.sql.split("`creature_model_info`")[-1],
                          re.MULTILINE)
        self.assertEqual({int(r[0]) for r in rows}, set(range(90800, 90808)))
        for display, radius, reach, _, _ in rows:
            with self.subTest(display=display):
                self.assertGreater(float(radius), 0)
                self.assertGreaterEqual(float(reach), 0.1)       # ObjectMgr resets a combat reach below 0.1

    def test_the_model_info_rows_land_after_the_display_rows_in_the_same_file(self):
        # ObjectMgr::LoadCreatureModelInfo dereferences the creaturedisplayinfo_dbc row: one import carries both.
        self.assertLess(self.sql.index("INSERT INTO `creaturedisplayinfo_dbc`"),
                        self.sql.index("INSERT INTO `creature_model_info`"))
        self.assertLess(self.sql.index("INSERT INTO `creaturemodeldata_dbc`"),
                        self.sql.index("INSERT INTO `creaturedisplayinfo_dbc`"))


class VisualsModuleTest(unittest.TestCase):
    def setUp(self):
        self.v = _visuals()

    def _int_constants(self):
        return {name: value for name, value in vars(self.v).items()
                if name.isupper() and type(value) is int and not name.startswith("_")}

    def _table(self, name):
        for prefix, table in TABLE_BY_PREFIX:
            if name.startswith(prefix):
                return table
        return "spellvisual"

    def _spell_visual_ids(self):
        return {value for name, value in self._int_constants().items() if self._table(name) == "spellvisual"}

    def test_the_minted_ids_match_the_patch_script(self):
        for name in ("SV_GRAVE_ROT", "SV_RED_AURA", "SV_SEAL_COMMAND", "SV_SEAL_RIGHTEOUSNESS", "SV_SEAL_JUSTICE",
                     "SV_DREAM_MIST", "SV_PLAGUE_CLOUD", "SV_CONSECRATED_HALL", "SV_PILLAR_3", "SV_PILLAR_6"):
            with self.subTest(name=name):
                self.assertEqual(getattr(self.v, name), getattr(patch, name))
        self.assertEqual(set(self.v.MINTED_SPELL_VISUALS), {r["ID"] for r in patch.build_spellvisual_rows()})
        self.assertEqual(len(self.v.MINTED_SPELL_VISUALS), len(set(self.v.MINTED_SPELL_VISUALS)))
        self.assertEqual(set(self.v.MINTED_CREATURE_DISPLAYS), {cdi for cdi, *_ in patch.CREATURE_MODEL_INFO})
        for name, cdi in (("DISPLAY_SPECTRE_GALVAR", patch.CDI_SPECTRE_GALVAR),
                          ("DISPLAY_SPECTRE_FAIRBELL", patch.CDI_SPECTRE_FAIRBELL),
                          ("DISPLAY_SPECTRE_VOSS", patch.CDI_SPECTRE_VOSS),
                          ("DISPLAY_SPECTRE_GOODCHILDE", patch.CDI_SPECTRE_GOODCHILDE),
                          ("DISPLAY_SPECTRE_ALEXANDROS", patch.CDI_SPECTRE_ALEXANDROS),
                          ("DISPLAY_CURSED_BOOK_OPEN", patch.CDI_CURSED_BOOK),
                          ("DISPLAY_RALLYING_BANNER_CRIMSON", patch.CDI_RALLYING_BANNER),
                          ("DISPLAY_RAVAGER", patch.CDI_RAVAGER)):
            with self.subTest(name=name):
                self.assertEqual(getattr(self.v, name), cdi)
        self.assertEqual(self.v.HALL_RADIUS, patch.HALL_RADIUS)

    def test_the_spectres_are_the_documented_base_displays(self):
        v = self.v
        self.assertEqual((v.DISPLAY_GALVAR_BASE, v.DISPLAY_FAIRBELL_BASE, v.DISPLAY_VOSS_BASE,
                          v.DISPLAY_GOODCHILDE_BASE), (25917, 25842, 10339, 25841))
        self.assertEqual([(c, b) for c, b, _ in patch.SPECTRES][:4],
                         [(90800, 25917), (90801, 25842), (90802, 10339), (90803, 25841)])
        self.assertEqual(patch.SPECTRES[4], (90804, 16139, 140))

    def test_every_int_constant_is_in_a_category_tuple_of_its_table(self):
        known = {
            "spellvisual": (set(self.v.STOCK_SPELL_VISUALS) | set(self.v.MINTED_SPELL_VISUALS)
                            | set(self.v.SHIPPED_SPELL_VISUALS)),
            "creature": set(self.v.STOCK_CREATURE_DISPLAYS) | set(self.v.MINTED_CREATURE_DISPLAYS),
            "gameobject": set(self.v.STOCK_GAMEOBJECT_DISPLAYS),
        }
        for name, value in self._int_constants().items():
            table = self._table(name)
            if table in known:
                with self.subTest(name=name, table=table):
                    self.assertIn(value, known[table])

    def test_each_category_holds_the_right_kind_of_id(self):
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS",
                     "SHIPPED_SPELL_VISUALS"):
            ids = getattr(self.v, name)
            with self.subTest(name=name):
                self.assertTrue(all(isinstance(i, int) for i in ids))
                self.assertEqual(len(ids), len(set(ids)))
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS"):
            self.assertFalse([i for i in getattr(self.v, name) if i >= 90000], name)
        for i in self.v.SHIPPED_SPELL_VISUALS:       # Paladin 90044 / 90045; the rest below the block
            self.assertTrue(i in (90044, 90045) or 90000 <= i <= 90699 and not 90550 <= i <= 90599, i)
        self.assertTrue(all(90550 <= i <= 90599 for i in self.v.MINTED_SPELL_VISUALS))
        self.assertTrue(all(90800 <= i <= 90829 for i in self.v.MINTED_CREATURE_DISPLAYS))

    def test_the_shipped_names_are_all_in_the_shipped_tuple(self):
        for name, value in self._int_constants().items():
            if name.startswith("SHIPPED_"):
                with self.subTest(name=name):
                    self.assertIn(value, self.v.SHIPPED_SPELL_VISUALS)
        for name in ("SHIPPED_LAVA_POOL", "SHIPPED_HOLY_ZONE"):
            for value in getattr(self.v, name).values():
                self.assertIn(value, self.v.SHIPPED_SPELL_VISUALS)

    def test_the_wrong_looks_are_not_wired(self):
        wired = self._spell_visual_ids()
        for sv, why in WRONG_SPELL_VISUALS.items():
            with self.subTest(sv=sv):
                self.assertNotIn(sv, wired, why)
        for cdi, why in WRONG_CREATURE_DISPLAYS.items():
            self.assertNotIn(cdi, {v for n, v in self._int_constants().items() if n.startswith("DISPLAY_")}, why)
        for godi, why in WRONG_GAMEOBJECT_DISPLAYS.items():
            self.assertNotIn(godi, set(self.v.STOCK_GAMEOBJECT_DISPLAYS), why)
        for item, why in WRONG_ITEMS.items():
            self.assertNotIn(item, {v for n, v in self._int_constants().items() if n.startswith("ITEM_")}, why)

    def test_the_looks_that_are_right_for_one_use_only_are_wired_to_that_use_only(self):
        for sv, allowed in ALLOWED_ONLY_AS.items():
            carriers = {name for name, value in self._int_constants().items()
                        if value == sv and self._table(name) == "spellvisual"}
            with self.subTest(sv=sv):
                self.assertTrue(carriers, "the pick is not wired at all")
                self.assertTrue(carriers <= allowed, carriers)

    def test_the_corrections_of_s3_10(self):
        v = self.v
        self.assertEqual(v.DISPLAY_CURSED_BOOK, 28103)              # not the Rabbit 21955
        self.assertEqual(v.DISPLAY_CURSED_BOOK_OPEN, 90805)
        self.assertEqual((v.DISPLAY_THORNE, v.ITEM_THORNE_SCYTHE, v.IDI_THORNE_SCYTHE), (2502, 20536, 33087))
        self.assertEqual(v.VI_TORMENT, 788)                         # Drain Soul, not Soul Drain
        self.assertEqual(v.DN_ANCHOR_BEAM, 8795)                    # Magic Barrier, not Arcane Channeling
        self.assertEqual(v.TH_BLOOD_PACT_TETHER, 7270)              # Blood Siphon, not Blood Link
        self.assertEqual(v.TH_RAISE, 4582)                          # Raise Dead, not Summon Spirits
        self.assertEqual((v.HB_THROW, v.LB_AXES), (3962, 3962))     # Throw Axe 16075, not 40563 / Axe Volley
        self.assertEqual(v.HB_CYCLONE, 7428)                        # the Dervish cyclone, not Whirlwind 8989
        self.assertEqual((v.HB_BLADE, v.HM_VERDICT), (8618, 8618))  # Fury of the Ashbringer, not the aura 28282
        self.assertEqual(v.LS_HAMMER, 7250)                         # Hammer of Wrath, not Hammer of Justice
        self.assertEqual(v.IR_GLARE, 9205)                          # Eyebeam, not Eye's Glare
        self.assertEqual(v.AR_RIVET, 67)                            # Fireball, not Heated Hammer
        self.assertEqual(v.AR_STEAM, 8657)                          # Scalding Water, not Scalding Steam
        self.assertEqual(v.AR_PLATE, 1946)                          # the lasting Burning Brand state
        self.assertEqual(v.GODI_FORGE, 7044)                        # not the brazier 197
        self.assertEqual(v.GODI_RELIC_PEDESTAL, 7695)               # not the 5.2 yd Karazhan Pedestal
        self.assertEqual(v.DN_MARK_BURST, 10693)                    # Living Bomb: 44461 is the burst
        self.assertEqual(v.GD_BLESSED_GROUND, 90512)                # the Strat holy zone, 8 yd
        self.assertNotEqual(v.GD_BLESSED_GROUND, v.CV_RIGHTEOUSNESS_BURST)
        self.assertEqual(v.HM_HALL, 90562)
        self.assertEqual((v.HM_PRAYER_PILLAR, v.WM_PENANCE_PILLAR, v.HM_LIGHT_PILLAR), (90563, 90564, 90564))
        self.assertEqual(v.IR_GRAVE_ROT, 90505)                     # the 6 yd rung; 7-10 are minted

    def test_the_decisions_of_s7_34(self):
        v = self.v
        self.assertEqual((v.ITEM_VISHAS_WEAPON, v.IDI_VISHAS_WEAPON, v.ITEM_VISHAS_STARTING_TORCH), (5532, 8078, 1906))
        self.assertEqual(v.DISPLAY_CRELL, 3278)
        self.assertEqual(v.GODI_WING_PORTAL, 4711)
        self.assertEqual(v.PORTAL_GO_SIZE, 0.45)
        self.assertEqual((v.DISPLAY_AZSHIR, v.DISPLAY_FALLEN_CHAMPION, v.DISPLAY_RISEN_GALVAR), (5534, 5230, 90800))
        self.assertEqual(v.DISPLAY_SPECTRE_ALEXANDROS, 90804)
        self.assertEqual(v.DISPLAY_HALDEN, 2514)

    def test_the_boss_requests_of_the_fix_pass(self):
        # D6 / D9 / D12 / D11H / D13 (the invisible stalker), D2 (the Shatter alias), D7 (Immolation), D11 (Frenzy),
        # D5 (the dog's take-off) and D13 (the chest display): each is named so a boss file imports it instead of a
        # local copy, and lands in the category tuple of its table (the existence check reads those tuples).
        v = self.v
        self.assertEqual(v.DISPLAY_INVISIBLE_STALKER, 11686)
        self.assertIn(11686, v.STOCK_CREATURE_DISPLAYS)
        self.assertEqual(v.IR_SHATTER, v.IR_REASSEMBLED_ALT)        # Bone Shards, the burst D2 wired
        self.assertEqual(v.IR_SHATTER, 4362)
        self.assertEqual(v.LB_IMMOLATION, 2519)
        self.assertEqual(v.HB_FRENZY, 870)
        self.assertEqual(v.LK_LEAP_TRAIL, 29)
        self.assertEqual(v.GODI_LAST_STAND_CHEST, 1387)
        for sv in (v.IR_SHATTER, v.LB_IMMOLATION, v.HB_FRENZY, v.LK_LEAP_TRAIL):
            with self.subTest(sv=sv):
                self.assertIn(sv, v.STOCK_SPELL_VISUALS)
                self.assertNotIn(sv, v.MINTED_SPELL_VISUALS)
                self.assertNotIn(sv, v.SHIPPED_SPELL_VISUALS)
        self.assertIn(1387, v.STOCK_GAMEOBJECT_DISPLAYS)

    def test_the_lasting_buffs_use_the_lasting_twins(self):
        v = self.v
        self.assertEqual(v.CV_GRIEF, 6943)                          # BeastRageState head + hands, lasting
        self.assertEqual(v.VI_CONFESSION_MARK, v.SHIPPED_KEENING_SKULL)
        self.assertEqual(v.LK_SCENT_RING, v.SHIPPED_ORANGE_RING)
        self.assertEqual(v.WM_VIGIL_FLAME, v.SHIPPED_HELD_TORCH)
        self.assertEqual((v.LS_DEVOTION, v.LS_DEVOTION_APPLY), (199, 160))

    def test_the_rungs_pick_the_smallest_size_at_or_above_the_radius(self):
        v = self.v
        self.assertEqual(v.lava_pool_rung(4.0), 90606)
        self.assertEqual(v.lava_pool_rung(4.5), 90607)
        self.assertEqual(v.lava_pool_rung(12.0), 90612)             # past the top keeps the top
        self.assertEqual(v.holy_zone_rung(4.0), 90509)
        self.assertEqual(v.holy_zone_rung(7.0), 90512)
        self.assertEqual(v.holy_zone_rung(20.0), 90512)
        self.assertEqual(v.grave_rot_rung(5.0), 90505)              # the shipped 6 yd rung is the floor
        self.assertEqual(v.grave_rot_rung(6.0), 90505)
        self.assertEqual(v.grave_rot_rung(7.0), 90550)
        self.assertEqual(v.grave_rot_rung(8.5), 90552)
        self.assertEqual(v.grave_rot_rung(10.0), 90553)
        self.assertEqual(v.grave_rot_rung(14.0), 90553)
        self.assertEqual(v.dream_mist_rung(6.0), 90558)
        self.assertEqual(v.dream_mist_rung(7.5), 90559)
        self.assertEqual(v.dream_mist_rung(12.0), 90560)
        self.assertEqual(v.dream_mist_rung(15.0), 90560)

    def test_the_creature_scale_hints_fit_the_designer_picks(self):
        low, high = self.v.CURSED_BOOK_SCALE_RANGE
        self.assertTrue(3.0 <= low < high <= 4.0)
        low, high = self.v.FIST_SCALE_RANGE
        self.assertTrue(2.5 <= low < high <= 3.0)
        self.assertEqual(self.v.PUP_SCALE, 0.7)

    def test_every_boss_code_of_the_report_has_constants(self):
        names = set(self._int_constants())
        for prefix in ("VI_", "IR_", "CV_", "TH_", "RH_", "LK_", "AN_", "LB_", "DN_", "HM_", "AR_", "MA_", "HB_",
                       "GD_", "LS_", "WM_"):
            with self.subTest(prefix=prefix):
                self.assertTrue([n for n in names if n.startswith(prefix)])

    def test_the_constants_module_is_skipped_by_the_package_loader(self):
        self.assertTrue(VISUALS_FILE.name.startswith("_"))


class StockExistsTest(unittest.TestCase):
    """Against the hand-maintained working copy, when this checkout has one (var/ is gitignored)."""

    def test_every_stock_and_shipped_id_exists(self):
        if not _has_working_copy():
            self.skipTest("no model-visual-dbc working copy in this checkout")
        self.assertTrue(patch.check_stock_ids())

    def test_the_minted_ids_are_free_in_the_working_copy(self):
        if not _has_working_copy():
            self.skipTest("no model-visual-dbc working copy in this checkout")
        patch.check_no_collisions()


if __name__ == "__main__":
    unittest.main()
