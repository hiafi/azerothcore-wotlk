"""
Scholomance visuals (Scholomance build, WP-V): source/npcs/scholomance/_visuals.py.

Covered: the pinned top-pick ids (handoff s3.10, s7 #19 and #20), none of the build spec's looks that draw nothing or
something else coming back as a wired id, no minted id (the picks are all stock; 90342 is the Deadmines puddle), the
constants module staying out of the package loader, and every id existing in the hand-maintained working-copy DBCs
(skipped when this checkout has none: var/ is gitignored).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_vfx.py
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfile, dbcfmt  # noqa: E402

VISUALS_FILE = TOOL_ROOT / "source" / "npcs" / "scholomance" / "_visuals.py"
# A worktree has no var/; fall back to the shared checkout's working copy (read-only here).
DBC_DIRS = (
    TOOL_ROOT / "var" / "model-visual-dbc" / "DBFilesClient",
    Path("/home/plex/wow_server/azerothcore-wotlk/apps/dbc-tools/var/model-visual-dbc/DBFilesClient"),
)

# SpellVisuals the build spec names that draw nothing or something other than the doc says (VISUALS-REPORT s2). None
# may be wired. (14726 as the tomb thaw burst, 11806/10150 never, 2046 as the mirror poof and 14509 as the Soulstorm
# hands are real looks and are pinned below instead.)
WRONG_SPELL_VISUALS = {
    7606: "Frost Aura: empty row",
    15489: "Shadow Trap: empty state kit",
    808: "Lash: no models",
    7264: "Stolen Soul Visual: empty",
    15339: "Bone Spike Graveyard: animations only",
    10719: "Grab Skeleton: animation and sound only",
    3960: "Ice Tomb 70157: a freeze pose, no block",
    8796: "Mystic Buffet: a one-shot arcane burst",
    8097: "Shatter: stone chips",
    289: "Fire Shield: a flash, nothing persists",
    12640: "Heat: a flash, nothing persists",
    93: "Salvage Corpse: the mining pick",
    14287: "Slime Pool: a hand burst, no pool",
    9709: "Plague Cloud: an orange fog",
    14527: "Unleashed Souls: an icy ground state",
    10150: "Shadow Portal Visual: the Shadowform look",
    11806: "Open Shadow Portal: a hand precast",
    262: "Arcane Missiles: channel hands only",
    8251: "Displacement: a cyclone",
    12794: "Coin Toss: a yellow crystal",
    10386: "NPC Blizzard: no persistent model",
}


def _visuals():
    spec = importlib.util.spec_from_file_location("sc_visuals_under_test", VISUALS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _dbc_dir():
    for path in DBC_DIRS:
        if (path / "SpellVisual.dbc").is_file():
            return path
    return None


def _ids(dbc_dir, filename, table):
    return {row["ID"] for row in dbcfile.read_dbc(dbc_dir / filename, table)}


class PinnedPicksTest(unittest.TestCase):
    def setUp(self):
        self.v = _visuals()

    def test_gap_picks(self):
        v = self.v
        self.assertEqual((v.GODI_TORN_PAGE, v.GODI_EMPTY_BOOK), (7752, 4431))                       # 4
        self.assertEqual((v.DISPLAY_BONE_PILE_PART, v.GODI_BONE_PILE_LANDING), (27976, 6998))       # 6
        self.assertEqual((v.DISPLAY_UNFINISHED_CONSTRUCT, v.AURA_PERMANENT_FEIGN_DEATH), (12074, 29266))
        self.assertEqual(v.DISPLAY_CORVANE, 23277)                                                   # 12
        self.assertEqual((v.GODI_FORTUNE_PILE, v.AX_ILL_GOTTEN_GAINS), (2614, 12473))                # 13
        self.assertEqual((v.GD_HONOR_ROLL, v.GODI_HONORS_PAPER, v.GD_EXAMINER_TINT), (7553, 210, 886))   # 16
        self.assertEqual(v.PASSING_GRADE_ICONS, (92, 2741, 339, 221, 2319, 48))
        self.assertEqual((v.KR_WRENCH_FREE, v.DISPLAY_WORK_BENCH, v.KR_STITCHED_WOUND), (12608, 30297, 15205))  # 17
        self.assertEqual((v.KR_GRAFT_HANDS, v.KR_GRAFT_EYES, v.KR_GRAFT_HEART), (47, 9188, 10883))
        self.assertEqual((v.PK_ROOTED, v.PK_HARDENED, v.PK_ACID_POOL), (38, 6662, 90342))            # 18

    def test_ras_malicia_gandling_picks(self):
        v = self.v
        self.assertEqual((v.RF_CHILL, v.RF_CHILL_12_STACKS, v.RF_WARMTH), (675, 6778, 6591))
        self.assertEqual((v.RF_FROST_MARK, v.RF_BLIZZARD, v.RF_MORTAL_DECAY), (15254, 13698, 11624))
        self.assertEqual(v.DISPLAY_ICE_TOMB, 30890)
        self.assertEqual(v.DISPLAY_LOOSE_SOUL, 1825)                                                 # s7 #20
        self.assertEqual(v.DISPLAY_DARK_SHADE, 4629)
        self.assertEqual((v.DISPLAY_PORTAL, v.DISPLAY_EXPELLED_STUDENT), (27735, 9784))
        self.assertEqual((v.GD_PORTAL_VOLLEY, v.GD_PORTAL_VOLLEY_2), (269, 270))
        self.assertEqual((v.GD_TRANSFER_FLASH, v.GD_TRANSFER_LINK), (9343, 7597))

    def test_boss_wp_additions(self):
        # Filed by F-A from the S3 and S4 reports: the Marduk and Vectus looks the boss file wired by hand, and Ras's
        # Blizzard anchor's invisible stalker.
        v = self.v
        self.assertEqual((v.MV_DRILL_IMPACT, v.MV_GROUP_EXERCISE_MARK, v.MV_FIREBALL, v.MV_WHIRLWIND_IMPACT),
                         (796, 3239, 67, 3362))
        self.assertEqual(v.DISPLAY_INVISIBLE_STALKER, 11686)
        for sv in (v.MV_DRILL_IMPACT, v.MV_GROUP_EXERCISE_MARK, v.MV_FIREBALL, v.MV_WHIRLWIND_IMPACT):
            self.assertIn(sv, v.STOCK_SPELL_VISUALS)
        self.assertIn(v.DISPLAY_INVISIBLE_STALKER, v.STOCK_CREATURE_DISPLAYS)

    def test_the_corrected_looks_replace_the_wrong_ones(self):
        v = self.v
        wired = set(v.STOCK_SPELL_VISUALS)
        for sv, why in WRONG_SPELL_VISUALS.items():
            with self.subTest(sv=sv):
                self.assertNotIn(sv, wired, why)
        self.assertEqual(v.RG_ERUPTION_RING, 11766)       # Impale, not Bone Spike Graveyard
        self.assertEqual(v.AX_DEANS_ROD, 792)             # Chastise, not Lash
        self.assertEqual(v.IL_MEMORY_TRAIL, 12121)        # Mind Sear, not Shadow Trap
        self.assertEqual(v.ML_FALLING_SOULS, 14512)       # Soulstorm missile, not Unleashed Souls
        self.assertEqual(v.RF_TOMB_THAW, 14726)           # the nova burst is right for the thaw, wrong for the tomb
        self.assertNotEqual(v.RF_ENTOMBED, v.RF_TOMB_THAW)
        self.assertEqual(v.JB_REFLECTION_POOF, 2046)
        self.assertEqual(v.ML_SOULSTORM_HANDS, 14509)

    def test_the_invisible_soul_display_is_never_wired(self):
        v = self.v
        self.assertEqual(v.DISPLAY_LOOSE_SOUL_INVISIBLE_DO_NOT_USE, 30233)
        for name in ("STOCK_CREATURE_DISPLAYS",):
            self.assertNotIn(30233, getattr(v, name))
        self.assertNotEqual(v.DISPLAY_LOOSE_SOUL, 30233)

    def test_only_the_deadmines_puddle_is_above_the_stock_range(self):
        v = self.v
        for name in ("STOCK_SPELL_VISUALS", "STOCK_CREATURE_DISPLAYS", "STOCK_GAMEOBJECT_DISPLAYS",
                     "STOCK_SPELL_ICONS"):
            ids = getattr(v, name)
            with self.subTest(name=name):
                self.assertTrue(all(isinstance(i, int) for i in ids))
                self.assertFalse([i for i in ids if i >= 90000])
        self.assertEqual(v.MINTED_ELSEWHERE_SPELL_VISUALS, (90342,))

    def test_the_constants_module_is_skipped_by_the_package_loader(self):
        self.assertTrue(VISUALS_FILE.name.startswith("_"))


class ExistsInWorkingCopyTest(unittest.TestCase):
    """Against the hand-maintained working-copy DBCs (stock rows plus our custom ranges)."""

    @classmethod
    def setUpClass(cls):
        cls.dir = _dbc_dir()
        cls.v = _visuals()

    def setUp(self):
        if self.dir is None:
            self.skipTest("no model-visual-dbc working copy in this checkout")

    def _missing(self, ids, filename, table):
        return sorted(set(ids) - _ids(self.dir, filename, table))

    def test_spell_visuals_exist(self):
        wanted = set(self.v.STOCK_SPELL_VISUALS) | set(self.v.MINTED_ELSEWHERE_SPELL_VISUALS)
        self.assertEqual(self._missing(wanted, "SpellVisual.dbc", dbcfmt.SPELLVISUAL), [])

    def test_creature_displays_exist(self):
        self.assertEqual(self._missing(self.v.STOCK_CREATURE_DISPLAYS, "CreatureDisplayInfo.dbc",
                                       dbcfmt.CREATUREDISPLAYINFO), [])

    def test_gameobject_displays_exist(self):
        self.assertEqual(self._missing(self.v.STOCK_GAMEOBJECT_DISPLAYS, "GameObjectDisplayInfo.dbc",
                                       dbcfmt.GAMEOBJECTDISPLAYINFO), [])

    def test_spell_icons_exist(self):
        self.assertEqual(self._missing(self.v.STOCK_SPELL_ICONS, "SpellIcon.dbc", dbcfmt.SPELLICON), [])

    def test_the_acid_pool_chain_is_complete(self):
        rows = {r["ID"]: r for r in dbcfile.read_dbc(self.dir / "SpellVisual.dbc", dbcfmt.SPELLVISUAL)}
        kit_id = rows[self.v.SV_ACID_POOL]["PersistentAreaKit"]
        self.assertEqual(kit_id, 90342)
        kits = {r["ID"]: r for r in dbcfile.read_dbc(self.dir / "SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT)}
        effect_id = kits[kit_id]["WorldEffect"]
        effects = {r["ID"]: r for r in dbcfile.read_dbc(self.dir / "SpellVisualEffectName.dbc",
                                                        dbcfmt.SPELLVISUALEFFECTNAME)}
        self.assertIn("goo_flow_state", effects[effect_id]["FileName"])

    def test_the_invisible_soul_display_is_a_stalker(self):
        # the reason s7 #20 picked the wisp: 30233 exists but draws nothing
        self.assertIn(30233, _ids(self.dir, "CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO))


if __name__ == "__main__":
    unittest.main()
