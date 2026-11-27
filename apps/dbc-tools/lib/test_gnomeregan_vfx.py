"""
Gnomeregan visuals (Gnomeregan build, WP V): patch_gnomeregan_vfx_models.py and
source/npcs/gnomeregan/_visuals.py.

Covered: every minted id sits inside the `gnomeregan` reservation (SpellVisual / Kit / EffectName 90750-90799,
CreatureModelData / CreatureDisplayInfo 90850-90869, SoundEntries 90151-90160), the row builders (the arcing glob copy,
the big Voltage state, the punch pose copy with the swapped AnimID, the alarm pulse, the nature disc, the two bomb
skins, the numeral quads, the light cone, the geiger sounds), the constants module agreeing with the patch script, none
of the WRONG looks (handoff s3.10) wired as an id, every int constant being in a category tuple of its table, the stock
ids existing in the working-copy DBCs (when this checkout has one), the asset list (every file named exists in the
Ascension backup where it is readable, every texture a model names is shipped), the drawn numerals, and the SQL
overlay with its creature_model_info rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_vfx.py
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from functools import lru_cache
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import patch_gnomeregan_vfx_models as patch  # noqa: E402
from lib import source  # noqa: E402
from lib.blp_write import read_blp  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
VISUALS_FILE = TOOL_ROOT / "source" / "npcs" / "gnomeregan" / "_visuals.py"
BACKUP_ARCHIVE = patch.ASCENSION_DATA / "patch-N.MPQ"
SOUND_ARCHIVE = patch.ASCENSION_DATA / f"{patch.SOUND_ARCHIVE}.MPQ"

# The picks the doc had wrong (handoff s3.10, VISUALS-REPORT "WRONG" rows) and what each really plays: none of these
# may be wired as any constant.
WRONG_SPELL_VISUALS = {
    395: "Mobile Alarm: a crafting hammer (the alarm is sounds 5805 / 5763 and SV 90753)",
    7403: "Spotlight summon: anim 84 only, no look (the lock-on is SV 7402)",
    2048: "Supercharge: a purple soul beam, no State (Voltage is SV 37 / 7867 / 90751)",
    74: "Goblin Land Mine: a summon puff (the mine is CDI 6271)",
    354: "Remote Detonate: sound only (each blast plays its own SV)",
    1484: "Corrosive Ooze: one puff, no missile (the glob is SV 854 / 90750)",
    1485: "Slough's swell: shadow, not sludge (the swell is SV 1725 with 4202's precast)",
    1184: "Backhand: knockdown and stun, wrong for a hit",
    4229: "Lightning Strike: a 0.8 yd spark (the Discharge is SV 3)",
    7678: "Electric Justice blast: a 0.8 yd bolt (the blast is SV 3)",
}
# Looks that are right for one named use only (one-shots where a lasting look is needed, the small crescent, the
# stun-reading landing): each may only be carried by the listed names.
ALLOWED_ONLY_AS = {
    672: {"CP_STOMP_ALT"},                         # a 1.1 yd crescent: never the primary stomp
    1187: {"CP_LANDED_ALT"},                       # Knockout reads as stunned
    2956: {"TB_SAFE_START"},                       # a one-shot: the lasting look is TB_SAFE_MODE_STATE
    8314: {"MT_FIRE_PATCH_CAST"},                  # a one-shot: the lasting look is MT_FIRE_PATCH
    9446: {"VF_VOMIT"},                            # a one-shot breath
    2074: {"TB_PATCH", "MA_ALARM_PULSE_ALT", "MA_ALARM_PULSE_FALLBACK"},      # a one-shot ring
}
LASTING_TWINS = {"TB_SAFE_START": "TB_SAFE_MODE_STATE", "MT_FIRE_PATCH_CAST": "MT_FIRE_PATCH"}
TABLE_BY_PREFIX = (("DISPLAY_", "creature"), ("GODI_", "gameobject"), ("SOUND_", "sound"))
MINTED_NAMES = ("SV_ARCING_GLOB", "SV_BIG_VOLTAGE", "SV_PUNCH_POSE", "SV_ALARM_PULSE", "SOUND_GEIGER_2",
                "SOUND_GEIGER_4")
GLYPH_DIGITS = (1, 2, 3)


def _visuals():
    spec = importlib.util.spec_from_file_location("gnomeregan_visuals_under_test", VISUALS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has_working_copy() -> bool:
    return (patch.DBC_DIR / "SpellVisual.dbc").is_file()


def _has_numeral_source() -> bool:
    try:
        patch._numeral_source()
    except SystemExit:
        return False
    return True


@lru_cache(maxsize=2)
def _backup_listing(archive: str = "patch-N") -> frozenset[str] | None:
    """Lowercase paths inside a read-only Ascension archive, None when it is not readable here."""
    path = patch.ASCENSION_DATA / f"{archive}.MPQ"
    if not path.is_file():
        return None
    try:
        out = subprocess.run(["smpq", "-l", str(path)], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    names = set()
    for line in out.splitlines():
        parts = line.split()
        if parts:
            names.add(parts[-1].replace("\\", "/").lower())
    return frozenset(names)


NEEDS_DBC = unittest.skipUnless(_has_working_copy(), "no model-visual-dbc working copy in this checkout")
NEEDS_NUMERALS = unittest.skipUnless(_has_numeral_source(), "no var/bossmech-src (the BM script's --extract)")


def _model_bytes(model: str) -> bytes | None:
    """An Ascension model's bytes, from the working copy when it has it, else from the backup (None: unreadable)."""
    working = patch.SPELLS_DIR / f"{model}.m2"
    if working.is_file():
        return working.read_bytes()
    if _backup_listing() is None:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "model.m2"
        patch._extract_one("patch-N", f"SPELLS/{model}.m2", dest, Path(tmp))
        return dest.read_bytes()


def _texture_names(data: bytes) -> list[str]:
    import struct
    count, ofs = struct.unpack_from("<II", data, 0x50)
    names = []
    for i in range(count):
        tex_type, _, name_len, name_ofs = struct.unpack_from("<IIII", data, ofs + 16 * i)
        if tex_type == 0:
            names.append(data[name_ofs:name_ofs + name_len].split(b"\0", 1)[0].decode("ascii"))
    return names


class IdBlockTest(unittest.TestCase):
    def test_the_script_blocks_are_the_reservation(self):
        reservation = IDS["reservations"]["gnomeregan"]
        self.assertEqual(patch.VISUAL_BLOCK, reservation["spellvisual"])
        self.assertEqual(patch.VISUAL_BLOCK, {"start": 90750, "end": 90799})
        self.assertEqual(patch.DISPLAY_BLOCK, reservation["creaturedisplayinfo"])
        self.assertEqual(patch.DISPLAY_BLOCK, reservation["creaturemodeldata"])
        self.assertEqual(patch.DISPLAY_BLOCK, {"start": 90850, "end": 90869})
        self.assertEqual(patch.SOUND_BLOCK, reservation["soundentries"])
        self.assertEqual(patch.SOUND_BLOCK, {"start": 90151, "end": 90160})

    @NEEDS_DBC
    def test_every_minted_id_is_inside_the_reservation(self):
        for builder in (patch.build_effect_name_rows, patch.build_kit_rows, patch.build_spellvisual_rows):
            for row in builder():
                self.assertTrue(patch.VISUAL_BLOCK["start"] <= row["ID"] <= patch.VISUAL_BLOCK["end"],
                                (builder.__name__, row["ID"]))
        for builder in (patch.build_creature_model_rows, patch.build_creature_display_rows):
            for row in builder():
                self.assertTrue(patch.DISPLAY_BLOCK["start"] <= row["ID"] <= patch.DISPLAY_BLOCK["end"],
                                (builder.__name__, row["ID"]))
        for row in patch.build_sound_rows():
            self.assertTrue(patch.SOUND_BLOCK["start"] <= row["ID"] <= patch.SOUND_BLOCK["end"], row["ID"])

    @NEEDS_DBC
    def test_the_row_ids_are_the_rows_of_appendix_c2(self):
        self.assertEqual(sorted(r["ID"] for r in patch.build_spellvisual_rows()), [90750, 90751, 90752, 90753])
        self.assertEqual(sorted(r["ID"] for r in patch.build_kit_rows()), [90751, 90752, 90753])
        self.assertEqual(sorted(r["ID"] for r in patch.build_effect_name_rows()), [90751])
        self.assertEqual([r["ID"] for r in patch.build_creature_model_rows()], [90850, 90853, 90854, 90855, 90856])
        self.assertEqual([r["ID"] for r in patch.build_creature_display_rows()], list(range(90850, 90857)))
        self.assertEqual([r["ID"] for r in patch.build_sound_rows()], [90151, 90152])

    def test_the_script_names_no_gameobject_display_rows(self):
        self.assertEqual(sorted(n for n in dir(patch) if n.startswith("GODI_")), [])


@NEEDS_DBC
class RowTest(unittest.TestCase):
    def setUp(self):
        self.effects = {r["ID"]: r for r in patch.build_effect_name_rows()}
        self.kits = {r["ID"]: r for r in patch.build_kit_rows()}
        self.visuals = {r["ID"]: r for r in patch.build_spellvisual_rows()}
        self.models = {r["ID"]: r for r in patch.build_creature_model_rows()}
        self.displays = {r["ID"]: r for r in patch.build_creature_display_rows()}
        self.sounds = {r["ID"]: r for r in patch.build_sound_rows()}
        self.stock_v = patch._stock("SpellVisual.dbc", patch.dbcfmt.SPELLVISUAL, {854, 8083})

    @staticmethod
    def _slots(row):
        return [k for k in ("PrecastKit", "CastKit", "ImpactKit", "StateKit", "ChannelKit", "InstantAreaKit",
                            "ImpactAreaKit", "PersistentAreaKit", "StateDoneKit", "CasterImpactKit") if row.get(k)]

    def test_the_glob_is_acid_spit_with_an_arc_and_nothing_else_changed(self):
        stock = dict(self.stock_v[854])
        stock["ID"] = 90750
        stock["MissilePathType"] = 2
        self.assertEqual(self.visuals[90750], stock)
        self.assertEqual(self.stock_v[854]["MissilePathType"], 0)
        self.assertNotIn(90750, self.kits)

    def test_the_big_voltage_is_a_state_on_the_lightning_shield_model_with_sound_3256(self):
        row = self.visuals[90751]
        self.assertEqual(self._slots(row), ["StateKit"])
        kit = self.kits[row["StateKit"]]
        effect = self.effects[kit["BaseEffect"]]
        self.assertEqual(effect["FileName"].lower(), patch.STOCK_LIGHTNING_SHIELD_FILE)
        self.assertTrue(4.0 <= effect["Scale"] <= 6.0, effect["Scale"])
        self.assertEqual(effect["AreaEffectSize"], 0.0)
        self.assertEqual(kit["SoundID"], 3256)

    def test_the_punch_pose_is_ground_slam_with_the_unarmed_attack_anim_in_its_precast(self):
        row = self.visuals[90752]
        stock = dict(self.stock_v[8083])
        stock["ID"] = 90752
        stock["PrecastKit"] = 90752
        self.assertEqual(row, stock)
        stock_kit = patch._stock("SpellVisualKit.dbc", patch.dbcfmt.SPELLVISUALKIT, {6908})[6908]
        kit = self.kits[90752]
        self.assertEqual((stock_kit["AnimID"], kit["AnimID"]), (118, 16))
        self.assertEqual({k: v for k, v in kit.items() if k not in ("ID", "AnimID")},
                         {k: v for k, v in stock_kit.items() if k not in ("ID", "AnimID")})

    def test_the_alarm_pulse_is_the_thunderclap_ring_with_the_alert_loop_sound(self):
        row = self.visuals[90753]
        self.assertEqual(self._slots(row), ["InstantAreaKit"])
        kit = self.kits[row["InstantAreaKit"]]
        self.assertEqual((kit["WorldEffect"], kit["SoundID"]), (349, 5763))

    def test_the_nature_disc_is_a_creature_display_on_the_ascension_model(self):
        display, model = self.displays[90850], self.models[90850]
        self.assertEqual(display["ModelID"], 90850)
        self.assertEqual(model["ModelName"], "SPELLS\\target_nature_state_projected.mdx")
        self.assertEqual((display["CreatureModelScale"], model["ModelScale"], display["CreatureModelAlpha"]),
                         (1.0, 1.0, 255))

    def test_the_bombs_are_gnomebombot_skins_at_display_scale_half(self):
        stock = patch._stock("CreatureDisplayInfo.dbc", patch.dbcfmt.CREATUREDISPLAYINFO, {6977})[6977]
        for cdi, skin in ((90851, "GnomeSpiderTankSkinGreen"), (90852, "GnomeSpiderTankSkinBlue")):
            with self.subTest(cdi=cdi):
                row = self.displays[cdi]
                self.assertEqual((row["ModelID"], row["TextureVariation_1"]), (851, skin))
                self.assertAlmostEqual(row["CreatureModelScale"], 0.5, places=5)
                self.assertEqual({k: v for k, v in row.items() if k not in ("ID", "TextureVariation_1")},
                                 {k: v for k, v in stock.items() if k not in ("ID", "TextureVariation_1")})
        self.assertNotIn(90851, self.models)
        self.assertNotIn(90852, self.models)

    def test_the_numerals_and_the_cone_are_flat_models_with_their_own_texture_names(self):
        for cdi, word in ((90853, "one"), (90854, "two"), (90855, "three")):
            with self.subTest(cdi=cdi):
                self.assertEqual(self.models[cdi]["ModelName"], f"SPELLS\\gnomer_numeral_{word}.mdx")
                self.assertEqual(self.displays[cdi]["ModelID"], cdi)
                self.assertEqual(self.displays[cdi]["TextureVariation_1"], f"gnomer_numeral_{word}")
        self.assertEqual(self.models[90856]["ModelName"], "SPELLS\\custom_cone_white.mdx")
        self.assertEqual(self.displays[90856]["ModelID"], 90856)

    def test_the_geiger_rows_play_the_converted_ticks_like_stock_11757(self):
        stock = patch._stock("SoundEntries.dbc", patch.dbcfmt.SOUNDENTRIES, {11757})[11757]
        for id_, stem in ((90151, "fx_timer_tick_2click"), (90152, "fx_timer_tick_4click")):
            with self.subTest(id=id_):
                row = self.sounds[id_]
                self.assertEqual((row["File_1"], row["DirectoryBase"]), (f"{stem}.wav", "Sound\\Spells"))
                self.assertEqual(row["File_2"], "")
                for key in ("MinDistance", "DistanceCutoff", "SoundType"):
                    self.assertEqual(row[key], stock[key], key)
                self.assertAlmostEqual(row["Volumefloat"], stock["Volumefloat"], places=5)


class AssetTest(unittest.TestCase):
    def test_the_asset_list_is_two_models_two_skins_three_textures(self):
        names = [Path(p).name for _, p in patch.SPELLS_ASSETS]
        self.assertEqual(len(names), 7)
        self.assertEqual(len(names), len({n.lower() for n in names}))
        self.assertEqual(sum(n.endswith(".m2") for n in names), 2)
        self.assertEqual(sum(n.endswith(".skin") for n in names), 2)
        self.assertEqual(sum(n.endswith(".blp") for n in names), 3)
        self.assertTrue(all(a == "patch-N" for a, _ in patch.SPELLS_ASSETS))

    def test_every_ascension_model_a_row_names_is_in_the_asset_list(self):
        names = {Path(p).stem.lower() for _, p in patch.SPELLS_ASSETS}
        for model in patch.MODELS:
            self.assertIn(model, names)
            self.assertIn(f"{model}00", names)

    def test_the_geiger_files_come_from_patch_o_and_each_row_has_one_file(self):
        self.assertEqual(patch.SOUND_ARCHIVE, "patch-O")
        self.assertEqual(sorted(patch.SOUND_FILES), [90151, 90152])
        self.assertEqual([stems for _, stems in patch.SOUND_FILES.values()],
                         [["fx_timer_tick_2click"], ["fx_timer_tick_4click"]])

    @unittest.skipIf(_backup_listing() is None, "Ascension backup not readable here")
    def test_every_spells_file_named_exists_in_patch_n(self):
        listing = _backup_listing()
        missing = [p for _, p in patch.SPELLS_ASSETS if p.lower() not in listing]
        self.assertEqual(missing, [])

    @unittest.skipIf(_backup_listing("patch-O") is None, "Ascension patch-O not readable here")
    def test_every_sound_file_named_exists_in_patch_o(self):
        listing = _backup_listing("patch-O")
        missing = [f"{d}/{stem}.ogg" for d, stems in patch.SOUND_FILES.values() for stem in stems
                   if f"{d}/{stem}.ogg".lower() not in listing]
        self.assertEqual(missing, [])

    @unittest.skipIf(_backup_listing() is None, "Ascension backup not readable here")
    def test_every_texture_a_model_names_is_shipped(self):
        shipped = {f"spells\\{name}.blp".lower() for name in patch.TEXTURES}
        for model, expected in patch.MODEL_TEXTURES.items():
            with self.subTest(model=model):
                data = _model_bytes(model)
                self.assertIsNotNone(data)
                named = [n.lower() for n in _texture_names(data)]
                self.assertEqual(named, [f"spells\\{n}.blp".lower() for n in expected])
                self.assertTrue(set(named) <= shipped, set(named) - shipped)


@NEEDS_NUMERALS
class NumeralTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = patch.build_numeral_assets(*patch._numeral_source())

    def test_nine_files_three_per_digit(self):
        self.assertEqual(sorted(self.files), sorted(
            f"gnomer_numeral_{word}{suffix}" for word in ("one", "two", "three")
            for suffix in (".m2", "00.skin", ".blp")))

    def test_every_glyph_is_opaque_in_the_middle_clear_at_the_edges_and_inside_the_glyph_height(self):
        size = patch.NUMERAL_TEXTURE_SIZE
        for digit in GLYPH_DIGITS:
            with self.subTest(digit=digit):
                alpha = patch.numeral_alpha(digit)
                self.assertEqual(len(alpha), size * size)
                self.assertGreater(max(alpha), 250)
                rows = [r for r in range(size) if any(alpha[r * size:(r + 1) * size])]
                first, last = min(rows) / size, (max(rows) + 1) / size
                top, bottom = 0.5 - patch.NUMERAL_GLYPH_FRAC / 2, 0.5 + patch.NUMERAL_GLYPH_FRAC / 2
                self.assertAlmostEqual(first, top - patch.NUMERAL_STROKE_FRAC, delta=0.03)
                self.assertAlmostEqual(last, bottom + patch.NUMERAL_STROKE_FRAC, delta=0.03)
                edge = size // 16
                for r in range(size):
                    for c in (*range(edge), *range(size - edge, size)):
                        self.assertEqual(alpha[r * size + c], 0, (r, c))
                for r in (*range(edge), *range(size - edge, size)):
                    self.assertEqual(sum(alpha[r * size:(r + 1) * size]), 0, r)

    def test_the_three_glyphs_differ(self):
        planes = {digit: patch.numeral_alpha(digit, 64) for digit in GLYPH_DIGITS}
        self.assertEqual(len(set(planes.values())), 3)

    def test_each_texture_is_a_white_dxt5_blp_with_a_full_mip_chain(self):
        for word in ("one", "two", "three"):
            with self.subTest(word=word):
                info = read_blp(self.files[f"gnomer_numeral_{word}.blp"])
                self.assertEqual((info["width"], info["height"]), (256, 256))
                self.assertEqual(info["mip_count"], 9)
                self.assertEqual(info["mips"][0]["rgb0"][0], info["mips"][0]["rgb0"][1])    # white: R == G == B

    def test_each_model_binds_its_own_texture_path(self):
        for word in ("one", "two", "three"):
            with self.subTest(word=word):
                names = _texture_names(self.files[f"gnomer_numeral_{word}.m2"])
                self.assertEqual(names, [f"spells\\gnomer_numeral_{word}.blp"])

    def test_the_glyph_height_per_scale_matches_the_constants_module(self):
        v = _visuals()
        # glyph = NUMERAL_GLYPH_FRAC of the quad side; the side is 2 * QUAD_HALF yards per scale
        side = 2 * patch.bm.QUAD_HALF
        self.assertAlmostEqual(v.NUMERAL_GLYPH_HEIGHT_PER_SCALE, patch.NUMERAL_GLYPH_FRAC * side, places=6)
        self.assertAlmostEqual(v.numeral_scale(1.6), 1.0)


@NEEDS_DBC
class SqlTest(unittest.TestCase):
    def test_the_pending_sql_covers_the_spans_of_the_three_server_tables(self):
        sql = patch.build_pending_sql()
        self.assertIn("DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90750 AND 90753;", sql)
        self.assertIn("DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90850 AND 90856;", sql)
        self.assertIn("DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90850 AND 90856;", sql)
        for table in ("spellvisualkit", "spellvisualeffectname", "gameobjectdisplayinfo", "soundentries"):
            self.assertNotIn(table, sql)
        self.assertEqual(sql.count("\n(9075"), 4)

    def test_the_model_info_rows_are_flat_for_the_discs_and_bomb_sized_for_the_bombs(self):
        sql = patch.build_pending_sql()
        self.assertIn("DELETE FROM `creature_model_info` WHERE `DisplayID` IN (90850, 90851, 90852, 90853, 90854, "
                      "90855, 90856);", sql)
        for display in (90850, 90853, 90854, 90855, 90856):
            self.assertIn(f"({display}, 0.5, 0.5, 2, 0)", sql)
        for display in (90851, 90852):
            self.assertIn(f"({display}, 0.75, 1.0, 2, 0)", sql)

    def test_no_stock_display_is_edited(self):
        sql = patch.build_pending_sql()
        self.assertNotIn("UPDATE", sql)
        self.assertNotIn("`DisplayID` = 6774", sql)       # the window ruling: the shared Pummeler display stays as is

    def test_no_value_overflows_a_signed_int_column(self):
        # MissileAttachment -1 and the stock bomb's BloodLevel -1 are held as 4294967295 in the DBC
        sql = patch.build_pending_sql()
        self.assertNotIn("4294967295", sql)
        self.assertIn(", -1,", sql)


class ConstantsTest(unittest.TestCase):
    def setUp(self):
        self.v = _visuals()

    def _int_constants(self):
        return {n: v for n, v in vars(self.v).items() if n.isupper() and type(v) is int and not n.startswith("_")}

    def _table(self, name):
        if name in self.v.BOSS_CODE_DISPLAY_NAMES:
            return "creature"
        if name in self.v.BOSS_CODE_SOUND_NAMES:
            return "sound"
        if name in self.v.NOT_SPELL_VISUAL_NAMES:
            return "other"
        for prefix, table in TABLE_BY_PREFIX:
            if name.startswith(prefix):
                return table
        return "spellvisual"

    def _spell_visual_ids(self):
        return {v for n, v in self._int_constants().items() if self._table(n) == "spellvisual"}

    def test_the_minted_ids_match_the_patch_script(self):
        for name in MINTED_NAMES:
            with self.subTest(name=name):
                self.assertEqual(getattr(self.v, name), getattr(patch, name))
        v = self.v
        self.assertEqual((v.DISPLAY_NATURE_DISC, v.DISPLAY_BOMB_RADIO, v.DISPLAY_BOMB_FROST),
                         (patch.CDI_NATURE_DISC, patch.CDI_BOMB_RADIO, patch.CDI_BOMB_FROST))
        self.assertEqual((v.DISPLAY_NUMERAL_1, v.DISPLAY_NUMERAL_2, v.DISPLAY_NUMERAL_3, v.DISPLAY_LIGHT_CONE),
                         (patch.CDI_NUMERAL_1, patch.CDI_NUMERAL_2, patch.CDI_NUMERAL_3, patch.CDI_LIGHT_CONE))
        self.assertEqual(set(v.MINTED_SPELL_VISUALS), {90750, 90751, 90752, 90753})
        self.assertEqual(set(v.MINTED_CREATURE_DISPLAYS), set(range(90850, 90857)))
        self.assertEqual(set(v.MINTED_SOUNDS), {90151, 90152})
        self.assertEqual(v.BOMB_MODEL_INFO, patch.BOMB_MODEL_INFO[0][1:])

    @NEEDS_DBC
    def test_the_minted_ids_match_the_built_rows(self):
        self.assertEqual(set(self.v.MINTED_SPELL_VISUALS), {r["ID"] for r in patch.build_spellvisual_rows()})
        self.assertEqual(set(self.v.MINTED_CREATURE_DISPLAYS), {r["ID"] for r in patch.build_creature_display_rows()})
        self.assertEqual(set(self.v.MINTED_SOUNDS), {r["ID"] for r in patch.build_sound_rows()})

    def test_the_boss_names_alias_the_minted_rows_with_the_stock_fallbacks(self):
        v = self.v
        self.assertEqual((v.VF_GLOB, v.EL_VOLTAGE_ALT, v.TB_SAFE_MODE_STATE_ALT, v.CP_PUNCH_POSE, v.MA_ALARM_PULSE),
                         (90750, 90751, 90751, 90752, 90753))
        self.assertEqual((v.VF_POOL_DISC, v.MT_PUDDLE, v.MT_LEAK), (90850, 90850, 90850))
        self.assertEqual((v.DISPLAY_BOMB_RADIO, v.DISPLAY_BOMB_FROST, v.DISPLAY_BOMB_FROST_ALT), (90851, 90852, 21209))
        self.assertEqual(v.MT_NUMERALS, (90853, 90854, 90855))
        self.assertEqual((v.MA_CONE_LIGHT, v.VF_CLICK, v.VF_CLICK_ALT), (90856, 11757, 90151))
        self.assertEqual((v.VF_GLOB_FALLBACK, v.MA_ALARM_PULSE_FALLBACK, v.TB_SAFE_MODE_STATE_FALLBACK,
                          v.CP_PUNCH_POSE_FALLBACK), (854, 2074, 7867, 8083))

    def test_the_scales_follow_the_rulings(self):
        v = self.v
        self.assertAlmostEqual(v.disc_scale(4.8), 1.0)
        self.assertAlmostEqual(v.disc_scale(4.0), v.PUDDLE_DISC_SCALE, places=2)
        self.assertAlmostEqual(v.LEAK_DISC_SCALE * v.DISC_QUAD_RADIUS * 2, 100.0, delta=0.2)    # a 100 yd disc
        self.assertAlmostEqual(v.light_cone_scale(30), 0.79)
        self.assertEqual((v.ALERT_SCALE, v.PUMMELER_SCALE, v.BIG_ONE_SCALE), (3.0, 5.0, 2.0))
        # s7 #40 A: the boss bomb stays at full size, 1.67 times the gear's launched bomb
        self.assertEqual((v.BOMB_SCALE, v.GEAR_LAUNCHED_BOMB_SCALE), (1.0, 0.6))
        self.assertAlmostEqual(v.BOMB_SCALE / v.GEAR_LAUNCHED_BOMB_SCALE, 1.67, places=2)
        self.assertEqual(v.DISPLAY_BOMB, 6977)

    def test_every_int_constant_is_in_a_category_tuple_of_its_table(self):
        v = self.v
        known = {
            "spellvisual": set(v.STOCK_SPELL_VISUALS) | set(v.MINTED_SPELL_VISUALS) | set(v.SHIPPED_SPELL_VISUALS),
            "creature": set(v.STOCK_CREATURE_DISPLAYS) | set(v.MINTED_CREATURE_DISPLAYS),
            "gameobject": set(v.STOCK_GAMEOBJECT_DISPLAYS),
            "sound": set(v.STOCK_SOUNDS) | set(v.MINTED_SOUNDS),
        }
        for name, value in self._int_constants().items():
            table = self._table(name)
            if table in known:
                with self.subTest(name=name, table=table):
                    self.assertIn(value, known[table])

    def test_each_category_holds_the_right_kind_of_id(self):
        v = self.v
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS", "STOCK_SOUNDS",
                     "SHIPPED_SPELL_VISUALS", "MINTED_SPELL_VISUALS", "MINTED_CREATURE_DISPLAYS", "MINTED_SOUNDS"):
            ids = getattr(v, name)
            self.assertEqual(len(ids), len(set(ids)), name)
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS", "STOCK_SOUNDS"):
            self.assertFalse([i for i in getattr(v, name) if i >= 90000], name)
        self.assertTrue(all(patch.VISUAL_BLOCK["start"] <= i <= patch.VISUAL_BLOCK["end"]
                            for i in v.MINTED_SPELL_VISUALS))
        self.assertTrue(all(patch.DISPLAY_BLOCK["start"] <= i <= patch.DISPLAY_BLOCK["end"]
                            for i in v.MINTED_CREATURE_DISPLAYS))
        self.assertTrue(all(patch.SOUND_BLOCK["start"] <= i <= patch.SOUND_BLOCK["end"] for i in v.MINTED_SOUNDS))
        # shipped rows belong to Deadmines (90506-90509), Scarlet Monastery (90558-90561) and Zul'Farrak (90702)
        self.assertEqual(set(v.SHIPPED_SPELL_VISUALS), {90506, 90508, 90509, 90558, 90559, 90560, 90561, 90702})

    def test_no_unused_load_voice(self):
        # RF-1 Nit-5: group 9 has no voice (STAGE-R-1-C Nit-2), so its sound alias and stock id are gone, and every
        # stock sound left is named by a constant.
        v = self.v
        self.assertFalse(hasattr(v, "MT_LOAD_VOICE"))
        self.assertNotIn("MT_LOAD_VOICE", v.BOSS_CODE_SOUND_NAMES)
        named = {value for name, value in self._int_constants().items() if self._table(name) == "sound"}
        self.assertFalse(set(v.STOCK_SOUNDS) - named)

    def test_the_shipped_names_are_all_in_the_shipped_tuple(self):
        for name, value in self._int_constants().items():
            if name.startswith("SHIPPED_"):
                self.assertIn(value, self.v.SHIPPED_SPELL_VISUALS, name)

    def test_the_non_visual_boss_names_are_real_constants(self):
        for name in self.v.NOT_SPELL_VISUAL_NAMES:
            self.assertTrue(hasattr(self.v, name), name)
        self.assertTrue(self.v.BOSS_CODE_DISPLAY_NAMES <= self.v.NOT_SPELL_VISUAL_NAMES)
        self.assertTrue(self.v.BOSS_CODE_SOUND_NAMES <= self.v.NOT_SPELL_VISUAL_NAMES)

    def test_the_wrong_looks_are_not_wired(self):
        wired = self._spell_visual_ids()
        for sv, why in WRONG_SPELL_VISUALS.items():
            with self.subTest(sv=sv):
                self.assertNotIn(sv, wired, why)

    def test_the_looks_that_are_right_for_one_use_only_are_wired_to_that_use_only(self):
        for sv, allowed in ALLOWED_ONLY_AS.items():
            carriers = {n for n, v in self._int_constants().items() if v == sv and self._table(n) == "spellvisual"}
            with self.subTest(sv=sv):
                self.assertTrue(carriers, "the pick is not wired at all")
                self.assertTrue(carriers <= allowed, carriers)

    def test_a_one_shot_that_is_wired_has_its_lasting_twin(self):
        for one_shot, twin in LASTING_TWINS.items():
            self.assertTrue(hasattr(self.v, twin), twin)
            self.assertNotEqual(getattr(self.v, one_shot), getattr(self.v, twin))

    def test_the_corrections_of_s3_10_and_appendix_c4(self):
        v = self.v
        self.assertEqual((v.TB_SAFE_MODE_STATE, v.TB_SAFE_MODE_STATE_2, v.TB_SAFE_START), (37, 7867, 2956))
        self.assertEqual((v.EL_VOLTAGE, v.EL_VOLTAGE_2), (37, 7867))
        self.assertEqual((v.VF_GLOB, v.VF_GLOB_ALT), (90750, 854))
        self.assertEqual((v.MT_STICKY, v.MT_STICKY_BLAST, v.MT_BLAST, v.MT_BLAST_FLASH), (10692, 10693, 5619, 10693))
        self.assertEqual((v.MT_FROST, v.MT_RADIO, v.MT_BOMB_MARK, v.MT_LOCKED_OUT), (17, 1725, 3239, 1845))
        self.assertEqual((v.MA_LOCK_PILLAR, v.MA_SPOTTED, v.MA_SELF_DESTRUCT, v.MA_NET), (7402, 7851, 1463, 683))
        self.assertEqual((v.MA_ALARM_VOICE, v.MA_ALARM_LOOP, v.CP_BELL), (5805, 5763, 6555))
        self.assertEqual((v.CP_STOMP, v.CP_LANDED, v.CP_PUNCH_EMOTE_ANIM), (8083, 1763, 16))
        self.assertEqual((v.MT_FIRE_PATCH, v.MT_VENT, v.EL_JUSTICE_BLAST_ALT), (90508, 90559, 90702))
        self.assertEqual((v.GODI_DOOR, v.GODI_CHEST, v.GODI_CONSOLE), (907, 3014, 2091))
        self.assertEqual((v.DISPLAY_ALERT, v.DISPLAY_PUMMELER, v.DISPLAY_BIG_ONE, v.DISPLAY_MINE),
                         (6888, 6774, 19139, 6271))
        self.assertEqual(v.MINE_SCALE_RANGE, (2.0, 3.0))
        self.assertEqual(v.MT_LEAK_SCREEN_EFFECT, 282)

    def test_every_boss_code_has_constants(self):
        names = set(self._int_constants())
        for prefix in ("TB_", "VF_", "EL_", "MA_", "CP_", "MT_"):
            self.assertTrue([n for n in names if n.startswith(prefix)], prefix)
        for display in ("DISPLAY_TECHBOT", "DISPLAY_FALLOUT", "DISPLAY_ELECTROCUTIONER", "DISPLAY_THERMAPLUGG",
                        "DISPLAY_EXILE"):
            self.assertIn(display, names)

    def test_the_constants_module_is_skipped_by_the_package_loader(self):
        self.assertTrue(VISUALS_FILE.name.startswith("_"))


class StyleTest(unittest.TestCase):
    def test_no_line_is_over_120_columns_and_there_is_no_trailing_whitespace(self):
        for path in (Path(patch.__file__), Path(__file__), VISUALS_FILE):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                self.assertLessEqual(len(line), 120, f"{path.name}:{number}")
                self.assertEqual(line, line.rstrip(), f"{path.name}:{number} trailing whitespace")
                self.assertNotIn(chr(0x2014), line, f"{path.name}:{number} em dash")


class StockExistsTest(unittest.TestCase):
    """Against the hand-maintained working copy, when this checkout has one (var/ is gitignored)."""

    @unittest.skipUnless(_has_working_copy(), "no model-visual-dbc working copy in this checkout")
    def test_every_stock_and_shipped_id_exists(self):
        self.assertTrue(patch.check_stock_ids())

    @unittest.skipUnless(_has_working_copy(), "no model-visual-dbc working copy in this checkout")
    def test_the_minted_ids_are_free_in_the_working_copy(self):
        patch.check_no_collisions()


class SpellingTest(unittest.TestCase):
    def test_us_spelling(self):
        # F-1e (R-1-LOOT n-3): gray / canceled (the pattern is split so this file stays clean).
        bad = re.compile(r"\b(gr" + r"e(y|yed)|cance" + r"lled)\b", re.IGNORECASE)
        for path in (VISUALS_FILE, Path(patch.__file__), Path(__file__)):
            self.assertIsNone(bad.search(path.read_text(encoding="utf-8")), path.name)


if __name__ == "__main__":
    unittest.main()
