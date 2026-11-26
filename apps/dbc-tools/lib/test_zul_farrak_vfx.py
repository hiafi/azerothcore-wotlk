"""
Zul'Farrak visuals (Zul'Farrak build, WP V): patch_zul_farrak_vfx_models.py and
source/npcs/zul_farrak/_visuals.py.

Covered: every minted id sits inside the `zul_farrak` reservation (SpellVisual / Kit / EffectName 90700-90749,
CreatureModelData / CreatureDisplayInfo 90830-90849), the row builders (sand trap states, storm strike copy, bladestorm
state, basilisk gaze and hydra pose copies with the swapped AnimID, static charge, the three disc displays), the
constants module agreeing with the patch script, none of the WRONG looks (handoff s3.10) wired as an id, every int
constant being in a category tuple of its table, the stock ids existing in the working-copy DBCs (when this checkout has
one), the asset list (every file named exists in the Ascension backup where it is readable, every texture a model names
is shipped), the water disc's missing-texture edit, and the SQL overlay with its creature_model_info rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_vfx.py
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from functools import lru_cache
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import patch_zul_farrak_vfx_models as patch  # noqa: E402
from lib import source  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
VISUALS_FILE = TOOL_ROOT / "source" / "npcs" / "zul_farrak" / "_visuals.py"
BACKUP_ARCHIVE = patch.ASCENSION_DATA / "patch-N.MPQ"

# The picks the doc or the plan had wrong (handoff s3.10, VISUALS-REPORT "WRONG" rows) and what each really plays:
# none of these may be wired as any constant.
WRONG_SPELL_VISUALS = {
    3641: "gaze 15533: animation 124 only, no beam (the gaze is SV 8311 / 90704)",
    8325: "swarm giantinsectswarm_state_ground: a 43 x 47 yd dome (the swarm is SV 10986)",
    7621: "the same dome on Theka (the swarm on Theka is SV 7620)",
    11778: "Carrion Beetles: Roar animation only, no model (the hunt eruption is SV 7443)",
    12189: "Mojo Puddle: a purple 3.75 yd frost slick (the sheets are the disc displays)",
    14068: "Permafrost: a unit state and a one-shot nova, not a sheet",
    68: "Shackle: hand glows, no chain (the chain is SV 9275)",
    107: "Sacrifice: a gold learn glow, no beam (the blood beam is SV 7270)",
    7422: "Submerge: animations only, a player model lacks them (the pit is SV 90700)",
    4229: "Lightning Strike: a 0.8 yd spark (the strike is SV 90702)",
    6779: "Tidal Wave: a frost breath, not a flood",
}
# Looks that are right for one named use and wrong as anything else (one-shots where a lasting look is needed, a
# knockdown victim effect, a small chest puff as the only blast).
ALLOWED_ONLY_AS = {
    5285: {"UK_STAMP_ALT"},                        # Ground Stomp: Knockdown on every victim, so never the primary
    572: {"PY_BARREL_BLAST_ALT_2", "GZ_BLAST_ALT_2"},   # Barrel Explode: a small chest puff, never the only blast
    345: {"BC_GUARDED_ALT"},                       # Shield Wall: a one-shot
    121: {"PY_GRIEVOUS"},                          # a one-shot: the lasting look is PY_GRIEVOUS_STATE
    372: {"PY_BLEED"},                             # a one-shot: the lasting look is PY_BLEED_STATE
    5100: {"BC_POISON"},                           # a one-shot: the lasting look is BC_POISON_STATE
    99: {"BC_SOULSTONE"},                          # a one-shot: no standing glow exists
}
LASTING_TWINS = {"PY_GRIEVOUS": "PY_GRIEVOUS_STATE", "PY_BLEED": "PY_BLEED_STATE", "BC_POISON": "BC_POISON_STATE"}
WRONG_CREATURE_DISPLAYS = {}
TABLE_BY_PREFIX = (("DISPLAY_", "creature"), ("GODI_", "gameobject"))
NOT_IDS = {"DISC_QUAD_RADIUS", "DELUGE_DISC_SCALE", "DELUGE_DISC_START_SCALE", "THEKA_RISEN_SCALE", "BARREL_SCALE"}
MINTED_NAMES = ("SV_QUICKSAND_PIT", "SV_QUICKSAND_TRAIL", "SV_STORM_STRIKE", "SV_BLADESTORM", "SV_BASILISK_GAZE",
                "SV_HYDRA_DISCHARGE_POSE", "SV_HYDRA_SPIT_POSE", "SV_STATIC_CHARGE")


def _visuals():
    spec = importlib.util.spec_from_file_location("zul_farrak_visuals_under_test", VISUALS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has_working_copy() -> bool:
    return (patch.DBC_DIR / "SpellVisual.dbc").is_file()


@lru_cache(maxsize=1)
def _backup_listing() -> frozenset[str] | None:
    """Lowercase paths inside the read-only Ascension patch-N archive, None when it is not readable here."""
    if not BACKUP_ARCHIVE.is_file():
        return None
    try:
        out = subprocess.run(["smpq", "-l", str(BACKUP_ARCHIVE)], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    names = set()
    for line in out.splitlines():
        parts = line.split()
        if parts:
            names.add(parts[-1].replace("\\", "/").lower())
    return frozenset(names)


NEEDS_DBC = unittest.skipUnless(_has_working_copy(), "no model-visual-dbc working copy in this checkout")


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


class IdBlockTest(unittest.TestCase):
    def test_the_script_blocks_are_the_reservation(self):
        reservation = IDS["reservations"]["zul_farrak"]
        self.assertEqual(patch.VISUAL_BLOCK, reservation["spellvisual"])
        self.assertEqual(patch.VISUAL_BLOCK, {"start": 90700, "end": 90749})
        self.assertEqual(patch.DISPLAY_BLOCK, reservation["creaturedisplayinfo"])
        self.assertEqual(patch.DISPLAY_BLOCK, reservation["creaturemodeldata"])
        self.assertEqual(patch.DISPLAY_BLOCK, {"start": 90830, "end": 90849})

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

    @NEEDS_DBC
    def test_the_visual_kit_and_effect_ids_are_the_rows_of_appendix_c2(self):
        self.assertEqual(sorted(r["ID"] for r in patch.build_spellvisual_rows()), list(range(90700, 90708)))
        self.assertEqual(sorted(r["ID"] for r in patch.build_kit_rows()),
                         [90700, 90701, 90703, 90704, 90705, 90706, 90707, 90711, 90712])
        self.assertEqual(sorted(r["ID"] for r in patch.build_effect_name_rows()), [90700, 90701, 90707])
        self.assertEqual([r["ID"] for r in patch.build_creature_model_rows()], [90830, 90831, 90832])
        self.assertEqual([r["ID"] for r in patch.build_creature_display_rows()], [90830, 90831, 90832])

    def test_the_script_names_no_gameobject_or_sound_rows(self):
        self.assertEqual(sorted(n for n in dir(patch) if n.startswith(("GODI_", "SOUND_"))), [])


@NEEDS_DBC
class RowTest(unittest.TestCase):
    def setUp(self):
        self.effects = {r["ID"]: r for r in patch.build_effect_name_rows()}
        self.kits = {r["ID"]: r for r in patch.build_kit_rows()}
        self.visuals = {r["ID"]: r for r in patch.build_spellvisual_rows()}
        self.models = {r["ID"]: r for r in patch.build_creature_model_rows()}
        self.displays = {r["ID"]: r for r in patch.build_creature_display_rows()}

    @staticmethod
    def _slots(row):
        return [k for k in ("PrecastKit", "CastKit", "ImpactKit", "StateKit", "ChannelKit", "InstantAreaKit",
                            "ImpactAreaKit", "PersistentAreaKit", "StateDoneKit", "CasterImpactKit") if row.get(k)]

    def test_the_sand_trap_states_are_a_base_effect_on_the_ascension_model_at_two_scales(self):
        for sv, scale in ((90700, 1.1), (90701, 0.73)):
            with self.subTest(sv=sv):
                self.assertEqual(self._slots(self.visuals[sv]), ["StateKit"])
                kit = self.kits[self.visuals[sv]["StateKit"]]
                effect = self.effects[kit["BaseEffect"]]
                self.assertIn("8fx_toldagor_sandqueen_sandtrap_state", effect["FileName"])
                self.assertAlmostEqual(effect["Scale"], scale, places=5)
                self.assertEqual(effect["AreaEffectSize"], 0.0)
        self.assertGreater(self.effects[90700]["Scale"], self.effects[90701]["Scale"])

    def test_the_storm_strike_keeps_only_the_instant_area_kit_9161(self):
        row = self.visuals[90702]
        self.assertEqual(self._slots(row), ["InstantAreaKit"])
        self.assertEqual(row["InstantAreaKit"], 9161)
        self.assertNotIn(90702, self.kits)
        self.assertNotIn(90702, self.effects)

    def test_the_bladestorm_is_a_state_with_anim_126_on_the_rfc_blades_effect(self):
        row = self.visuals[90703]
        self.assertEqual(self._slots(row), ["StateKit"])
        kit = self.kits[row["StateKit"]]
        self.assertEqual((kit["AnimID"], kit["BaseEffect"], kit["SoundID"]), (126, 90370, 4354))

    def test_the_gaze_is_the_stock_white_beam_with_a_pose_the_basilisk_has(self):
        row = self.visuals[90704]
        self.assertEqual(self._slots(row), ["ChannelKit"])
        kit = self.kits[row["ChannelKit"]]
        self.assertEqual(kit["AnimID"], 51)
        # the beam chain (the white beam, chain 23) is the stock kit's, untouched
        self.assertEqual(kit["CharParamZero_1"], 23.0)

    def test_the_hydra_poses_use_anim_32_in_both_kits(self):
        for sv in (90705, 90706):
            with self.subTest(sv=sv):
                row = self.visuals[sv]
                for slot in ("PrecastKit", "CastKit"):
                    self.assertEqual(self.kits[row[slot]]["AnimID"], 32, slot)

    def test_the_static_charge_is_the_lightning_shield_model_big_with_sound_3256(self):
        row = self.visuals[90707]
        self.assertEqual(self._slots(row), ["StateKit"])
        kit = self.kits[row["StateKit"]]
        effect = self.effects[kit["BaseEffect"]]
        self.assertEqual(effect["FileName"].lower(), patch.STOCK_LIGHTNING_SHIELD_FILE)
        self.assertTrue(6.0 <= effect["Scale"] <= 8.0, effect["Scale"])
        self.assertEqual(kit["SoundID"], 3256)

    def test_every_effect_is_a_fixed_size_look(self):
        for row in self.effects.values():
            self.assertEqual(row["AreaEffectSize"], 0.0)
            self.assertGreater(row["Scale"], 0)

    def test_the_discs_are_creature_displays_on_the_three_ascension_models(self):
        want = {90830: "target_water_state_projected", 90831: "target_frost_state_projected",
                90832: "target_lightning_state_projected"}
        for id_, model in want.items():
            with self.subTest(id=id_):
                display = self.displays[id_]
                self.assertEqual(display["ModelID"], id_)
                self.assertEqual(self.models[id_]["ModelName"], f"SPELLS\\{model}.mdx")
                self.assertEqual((display["CreatureModelScale"], self.models[id_]["ModelScale"]), (1.0, 1.0))
                self.assertEqual(display["CreatureModelAlpha"], 255)

    def test_the_copies_differ_from_the_stock_row_in_the_named_slots_and_one_anim_only(self):
        stock_v = patch._stock("SpellVisual.dbc", patch.dbcfmt.SPELLVISUAL, {src for _, src, _ in patch.POSE_COPIES})
        stock_k = patch._stock_pose_kits()
        for new_id, src, changes in patch.POSE_COPIES:
            with self.subTest(sv=new_id):
                copy = self.visuals[new_id]
                stock = dict(stock_v[src])
                stock["ID"] = new_id
                for field, kit_id, old_anim, new_anim in changes:
                    stock[field] = kit_id
                    stock_kit = stock_k[stock_v[src][field]]
                    kit = self.kits[kit_id]
                    self.assertEqual((stock_kit["AnimID"], kit["AnimID"]), (old_anim, new_anim))
                    self.assertEqual({k: v for k, v in kit.items() if k not in ("ID", "AnimID")},
                                     {k: v for k, v in stock_kit.items() if k not in ("ID", "AnimID")})
                self.assertEqual(copy, stock)


class AssetTest(unittest.TestCase):
    def test_the_asset_list_is_four_models_four_skins_fourteen_textures_and_no_duplicate(self):
        names = [Path(p).name for _, p in patch.SPELLS_ASSETS]
        self.assertEqual(len(names), 22)
        self.assertEqual(len(names), len({n.lower() for n in names}))
        self.assertEqual(sum(n.endswith(".m2") for n in names), 4)
        self.assertEqual(sum(n.endswith(".skin") for n in names), 4)
        self.assertEqual(sum(n.endswith(".blp") for n in names), 14)
        self.assertTrue(all(a == "patch-N" for a, _ in patch.SPELLS_ASSETS))

    def test_every_ascension_effect_and_display_model_is_in_the_asset_list(self):
        names = {Path(p).stem.lower() for _, p in patch.SPELLS_ASSETS}
        rows = patch.build_effect_name_rows() + patch.build_creature_model_rows()
        for row in rows:
            file_name = row.get("FileName") or row["ModelName"]
            if file_name.startswith("SPELLS\\"):
                self.assertIn(Path(file_name.replace("\\", "/")).stem.lower(), names, file_name)
        for model in patch.MODELS:
            self.assertIn(f"{model}00".lower(), names)

    def test_the_rfc_blades_model_is_not_listed_again(self):
        names = {Path(p).stem for _, p in patch.SPELLS_ASSETS}
        self.assertNotIn("cfx_warrior_bladestorm_statebase", names)

    def test_the_water_disc_textures_after_the_edit_are_the_shipped_pair(self):
        self.assertEqual(patch.WATER_DISC_TEXTURES, ("target_water_state_4485122", "targetarea_everybase"))
        self.assertEqual(patch.WATER_FIXED_TEXTURE, "spells\\targetarea_everybase.blp")

    @unittest.skipIf(_backup_listing() is None, "Ascension backup not readable here")
    def test_every_file_named_exists_in_the_ascension_backup(self):
        listing = _backup_listing()
        missing = [p for _, p in patch.SPELLS_ASSETS if p.lower() not in listing]
        self.assertEqual(missing, [])

    @unittest.skipIf(_backup_listing() is None, "Ascension backup not readable here")
    def test_every_texture_a_model_names_is_shipped_after_the_water_edit(self):
        shipped = {f"spells\\{name}.blp".lower() for name in patch.TEXTURES}
        for model, expected in patch.MODEL_TEXTURES.items():
            with self.subTest(model=model):
                data = _model_bytes(model)
                self.assertIsNotNone(data)
                if model == patch.MODEL_WATER_DISC:
                    data = patch.fix_water_disc(data)
                named = [n.lower() for n in patch.texture_names(data)]
                self.assertEqual(named, [f"spells\\{n}.blp".lower() for n in expected])
                self.assertTrue(set(named) <= shipped, set(named) - shipped)

    @unittest.skipIf(_backup_listing() is None, "Ascension backup not readable here")
    def test_the_water_edit_changes_only_the_second_texture_and_is_idempotent(self):
        data = _model_bytes(patch.MODEL_WATER_DISC)
        if patch.WATER_MISSING_TEXTURE.lower() not in [n.lower() for n in patch.texture_names(data)]:
            self.skipTest("the working copy's water disc is already edited")
        fixed = patch.fix_water_disc(data)
        self.assertEqual(len(fixed), len(data))
        self.assertEqual(patch.fix_water_disc(fixed), fixed)
        self.assertEqual(patch.texture_names(fixed)[0], patch.texture_names(data)[0])
        self.assertEqual(patch.texture_names(fixed)[1], patch.WATER_FIXED_TEXTURE)
        changed = [i for i, (a, b) in enumerate(zip(data, fixed)) if a != b]
        self.assertTrue(changed)
        # the edit stays inside the texture records and the second name's bytes
        count_ofs = int.from_bytes(data[0x54:0x58], "little")
        self.assertGreaterEqual(min(changed), count_ofs + 16 + 8)

    def test_the_edit_refuses_a_model_that_is_not_the_one_it_was_written_for(self):
        with self.assertRaises(SystemExit):
            patch.set_texture_name(_synthetic_model(), 1, "spells\\something_else.blp", "spells\\x.blp")

    def test_the_edit_rewrites_a_hard_coded_name_in_place_with_the_new_length(self):
        data = _synthetic_model()
        out = patch.set_texture_name(data, 1, "world\\old\\name_that_is_long.blp", "spells\\new.blp")
        self.assertEqual(len(out), len(data))
        self.assertEqual(patch.texture_names(out), ["spells\\keep.blp", "spells\\new.blp"])


def _synthetic_model() -> bytes:
    """A minimal buffer with an M2 texture array of two hard-coded names (offsets 0x50 / 0x54 as in the real header)."""
    import struct
    names = [b"spells\\keep.blp\0", b"world\\old\\name_that_is_long.blp\0"]
    records_ofs = 0x100
    name_ofs = records_ofs + 16 * len(names)
    buf = bytearray(name_ofs + sum(len(n) for n in names))
    struct.pack_into("<II", buf, 0x50, len(names), records_ofs)
    for i, name in enumerate(names):
        struct.pack_into("<IIII", buf, records_ofs + 16 * i, 0, 0, len(name), name_ofs)
        buf[name_ofs:name_ofs + len(name)] = name
        name_ofs += len(name)
    return bytes(buf)


@NEEDS_DBC
class SqlTest(unittest.TestCase):
    def test_the_pending_sql_covers_the_spans_of_the_three_server_tables(self):
        sql = patch.build_pending_sql()
        self.assertIn("DELETE FROM `spellvisual_dbc` WHERE `ID` BETWEEN 90700 AND 90707;", sql)
        self.assertIn("DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90830 AND 90832;", sql)
        self.assertIn("DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90830 AND 90832;", sql)
        for table in ("spellvisualkit", "spellvisualeffectname", "gameobjectdisplayinfo"):
            self.assertNotIn(table, sql)
        self.assertEqual(sql.count("\n(9070"), 8)

    def test_the_disc_model_info_rows_are_flat_and_idempotent(self):
        sql = patch.build_pending_sql()
        self.assertIn("DELETE FROM `creature_model_info` WHERE `DisplayID` IN (90830, 90831, 90832);", sql)
        for display in (90830, 90831, 90832):
            self.assertIn(f"({display}, 0.5, 0.5, 2, 0)", sql)

    def test_the_stock_displays_with_a_zero_or_wrong_size_get_their_row_fixed(self):
        updates = {d: (r, c) for d, r, c in patch.STOCK_MODEL_INFO_UPDATES}
        self.assertEqual(set(updates), {6697, 25175, 29716, 26252})      # RB-10
        for display, (radius, reach) in updates.items():
            self.assertGreater(radius, 0, display)
            self.assertGreater(reach, 0, display)
            self.assertIn(f"WHERE `DisplayID` = {display};", patch.build_pending_sql())
        self.assertEqual(updates[6697], (0.3672, 1.8))                     # 0.306 and 1.5, both x1.2
        self.assertLess(updates[26252][1], 3.75)                           # the live reach is far too large for a keg

    def test_the_script_names_every_other_creature_the_four_updates_reach(self):
        # R-1-LOOT m-2: the UPDATEs are by display id, so they change every creature wearing the display. The module
        # docstring holds the judgement (live creature_template_model, 2026-11-25); it must name each of them.
        doc = patch.__doc__
        for entry in (7791, 35253, 300917, 28173, 29737, 29440, 29556):
            self.assertIn(str(entry), doc, entry)

    def test_no_value_overflows_a_signed_int_column(self):
        # MissileAttachment -1 is held as 4294967295 in the DBC; the overlay writes it signed
        sql = patch.build_pending_sql()
        self.assertNotIn("4294967295", sql)
        self.assertIn(", -1,", sql)


class ConstantsTest(unittest.TestCase):
    def setUp(self):
        self.v = _visuals()

    def _int_constants(self):
        return {n: v for n, v in vars(self.v).items()
                if n.isupper() and type(v) is int and not n.startswith("_") and n not in NOT_IDS}

    def _table(self, name):
        if name in self.v.BOSS_CODE_DISPLAY_NAMES:
            return "creature"
        if name in self.v.NOT_SPELL_VISUAL_NAMES:
            return "other"
        for prefix, table in TABLE_BY_PREFIX:
            if name.startswith(prefix):
                return table
        return "spellvisual"

    def _spell_visual_ids(self):
        return {v for n, v in self._int_constants().items() if self._table(n) == "spellvisual"}

    @NEEDS_DBC
    def test_the_minted_ids_match_the_patch_script(self):
        for name in MINTED_NAMES:
            with self.subTest(name=name):
                self.assertEqual(getattr(self.v, name), getattr(patch, name))
        self.assertEqual(set(self.v.MINTED_SPELL_VISUALS), {r["ID"] for r in patch.build_spellvisual_rows()})
        self.assertEqual(set(self.v.MINTED_CREATURE_DISPLAYS), {r["ID"] for r in patch.build_creature_display_rows()})
        self.assertEqual((self.v.DISPLAY_WATER_DISC, self.v.DISPLAY_ICE_DISC, self.v.DISPLAY_STORM_DISC),
                         (patch.CDI_WATER_DISC, patch.CDI_ICE_DISC, patch.CDI_STORM_DISC))

    def test_the_boss_names_alias_the_minted_rows_with_the_stock_fallbacks(self):
        v = self.v
        self.assertEqual((v.AS_GAZE_BEAM, v.UK_BLADESTORM, v.UK_PIT, v.UK_TRAIL), (90704, 90703, 90700, 90701))
        self.assertEqual((v.GZ_STATIC_CHARGE, v.GZ_DISCHARGE, v.GZ_STORM_STRIKE, v.GZ_ACID_SPIT),
                         (90707, 90705, 90702, 90706))
        self.assertEqual((v.GZ_WATER_DISC, v.GZ_ICE_DISC, v.GZ_STORM_DISC), (90830, 90831, 90832))
        self.assertEqual((v.AS_GAZE_BEAM_FALLBACK, v.UK_BLADESTORM_FALLBACK, v.UK_PIT_FALLBACK), (8311, 6044, 7437))
        self.assertEqual((v.GZ_STATIC_CHARGE_FALLBACK, v.GZ_DISCHARGE_FALLBACK, v.GZ_STORM_STRIKE_FALLBACK,
                          v.GZ_ACID_SPIT_FALLBACK), (37, 36, 3, 854))

    def test_the_disc_scale_is_radius_over_the_quad_half_width(self):
        v = self.v
        self.assertAlmostEqual(v.disc_scale(4.8), 1.0)
        self.assertAlmostEqual(v.disc_scale(23), 23 / 4.8)
        self.assertAlmostEqual(v.DELUGE_DISC_SCALE * v.DISC_QUAD_RADIUS * 2, 76.8)      # a 77 yd disc

    def test_every_int_constant_is_in_a_category_tuple_of_its_table(self):
        v = self.v
        known = {
            "spellvisual": set(v.STOCK_SPELL_VISUALS) | set(v.MINTED_SPELL_VISUALS) | set(v.SHIPPED_SPELL_VISUALS),
            "creature": set(v.STOCK_CREATURE_DISPLAYS) | set(v.MINTED_CREATURE_DISPLAYS),
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
                     "SHIPPED_SPELL_VISUALS", "MINTED_SPELL_VISUALS", "MINTED_CREATURE_DISPLAYS"):
            ids = getattr(v, name)
            self.assertEqual(len(ids), len(set(ids)), name)
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS"):
            self.assertFalse([i for i in getattr(v, name) if i >= 90000], name)
        self.assertTrue(all(patch.VISUAL_BLOCK["start"] <= i <= patch.VISUAL_BLOCK["end"]
                            for i in v.MINTED_SPELL_VISUALS))
        self.assertTrue(all(patch.DISPLAY_BLOCK["start"] <= i <= patch.DISPLAY_BLOCK["end"]
                            for i in v.MINTED_CREATURE_DISPLAYS))
        self.assertEqual(set(v.SHIPPED_SPELL_VISUALS), {90508})

    def test_the_shipped_names_are_all_in_the_shipped_tuple(self):
        for name, value in self._int_constants().items():
            if name.startswith("SHIPPED_"):
                self.assertIn(value, self.v.SHIPPED_SPELL_VISUALS, name)

    def test_the_non_visual_boss_names_are_real_constants(self):
        for name in self.v.NOT_SPELL_VISUAL_NAMES | self.v.BOSS_CODE_DISPLAY_NAMES:
            self.assertTrue(hasattr(self.v, name), name)
        self.assertTrue(self.v.BOSS_CODE_DISPLAY_NAMES <= self.v.NOT_SPELL_VISUAL_NAMES)

    def test_the_wrong_looks_are_not_wired(self):
        wired = self._spell_visual_ids()
        for sv, why in WRONG_SPELL_VISUALS.items():
            with self.subTest(sv=sv):
                self.assertNotIn(sv, wired, why)
        displays = {v for n, v in self._int_constants().items() if self._table(n) == "creature"}
        for cdi, why in WRONG_CREATURE_DISPLAYS.items():
            self.assertNotIn(cdi, displays, why)

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

    def test_the_corrections_of_s3_10_and_appendix_c3(self):
        v = self.v
        self.assertEqual((v.TK_SWARM_AURA, v.TK_SWARM_ON_THEKA, v.TK_HUNT_ERUPTION), (10986, 7620, 7443))
        self.assertEqual((v.TK_RISE_BURST, v.TK_HUNT_TRAIL), (7443, 14013))
        self.assertEqual((v.AS_GAZE_BEAM, v.AS_GAZE_BEAM_ALT), (90704, 8311))
        self.assertEqual((v.PY_CHAIN, v.PY_BLOOD_OFFERING), (9275, 7270))
        self.assertEqual((v.PY_BARREL_DISPLAY, v.PY_BARREL_BLAST), (26252, 889))
        self.assertEqual(v.BARREL_SCALE, 2.0)
        self.assertEqual((v.UK_PIT, v.UK_TRAIL, v.UK_BLADESTORM), (90700, 90701, 90703))
        self.assertEqual((v.UK_STAMP, v.UK_SUNK), (8083, 7437))
        self.assertEqual(v.DISPLAY_BOUND_DEAD, 29716)
        self.assertEqual((v.DISPLAY_THEKA_RISEN, v.THEKA_RISEN_SCALE), (6697, 1.2))
        self.assertEqual(v.ZR_INVIS_TYPE, 11)
        self.assertEqual(v.ZR_EMPTY_VESSEL_AURA, 247)
        self.assertEqual(v.PY_LAVA_TOTEM_ZONE, 90508)
        self.assertEqual(v.SWARM_SCALE_RANGE, (1.3, 2.0))
        self.assertEqual(v.LOST_SOUL_SCALE_RANGE, (1.5, 2.0))
        self.assertEqual((v.GODI_GRAVE, v.GODI_GONG, v.GODI_FLOE_ALT), (1767, 1827, 8557))

    def test_every_boss_code_has_constants(self):
        names = set(self._int_constants())
        for prefix in ("TK_", "AS_", "ZR_", "PY_", "BC_", "UK_", "GZ_"):
            self.assertTrue([n for n in names if n.startswith(prefix)], prefix)

    def test_the_constants_module_is_skipped_by_the_package_loader(self):
        self.assertTrue(VISUALS_FILE.name.startswith("_"))


class StyleTest(unittest.TestCase):
    def test_no_line_is_over_120_columns_and_there_is_no_trailing_whitespace(self):
        for path in (Path(patch.__file__), Path(__file__)):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                self.assertLessEqual(len(line), 120, f"{path.name}:{number}")
                self.assertEqual(line, line.rstrip(), f"{path.name}:{number} trailing whitespace")


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
