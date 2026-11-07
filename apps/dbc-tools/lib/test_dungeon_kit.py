"""
The shared dungeon kit's declaration helpers, lib/dsl/dungeon_kit.py (WP-K0):

  - the builders reproduce the Deadmines Pilot's per-file helpers exactly: a resolve copy (Greenskin 205340), a named
    cast bar (Greenskin 205343), a self visual (VanCleef 205360), and the three shared spells 205200-205202 that
    source/npcs/deadmines/shared.py now builds with them;
  - kit_creature / kit_helper give the Pilot's KIT_CREATURE / KIT_HELPER columns (pinned literally below);
  - kit_raw's shape.

The Deadmines package is loaded the way generate.py loads it; each builder runs in a throwaway package with the
arguments read back from the real declaration, and the two entries (and script bindings) must be equal.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_dungeon_kit.py
"""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import source, spell_tables  # noqa: E402
from lib.dsl import dungeon_kit, registry  # noqa: E402

DEADMINES = TOOL_ROOT / "source" / "npcs" / "deadmines"

# The Pilot's literal columns (source/npcs/deadmines/_common.py before WP-K0).
PILOT_KIT_CREATURE = dict(
    subname='', IconName='', exp=0, faction=17, npcflag=0, speed_walk=1.0, speed_run=1.14286, speed_swim=1.0,
    speed_flight=1.0, detection_range=20.0, dmgschool=0, BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0,
    RangeVariance=1.0, unit_flags2=2048, dynamicflags=0, family=0, type=7, type_flags=0, PetSpellDataId=0,
    VehicleId=0, MovementType=0, HoverHeight=1.0, ManaModifier=1.0, ArmorModifier=1.0, ExperienceModifier=1.0,
    RacialLeader=0, movementId=0, RegenHealth=1, CreatureImmunitiesId=0, flags_extra=0, AIName='', VerifiedBuild=0,
)
PILOT_KIT_HELPER = dict(
    PILOT_KIT_CREATURE, faction=14, unit_flags=0x2 | 0x02000000, DamageModifier=0.0, HealthModifier=1.0, lootid=0,
    pickpocketloot=0, skinloot=0, mingold=0, maxgold=0, flags_extra=0x40, detection_range=0.0,
)


def _load_package(path: Path, **kwargs) -> registry.Registry:
    ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
    return registry.load_class_package(path, ids_cfg=ids_cfg, **kwargs)


def _spells(reg: registry.Registry) -> dict[int, dict]:
    """Spell entries by id (each holds its model.Spell under `_spell`)."""
    return {int(e["id"]): e for e in reg.spells}


def _scripts(reg: registry.Registry, spell_id: int) -> list[str]:
    return sorted(row["ScriptName"] for row in reg.spell_script_names if int(row["spell_id"]) == spell_id)


class DungeonKitBuildersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        creature_index = spell_tables.load_creature_table_index()
        existing = {int(r["entry"]): r for r in creature_index.live_rows("creature_template")}
        cls.dm = _load_package(
            DEADMINES, existing_creature_rows=existing, creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
        )
        cls.dm_spells = {i: e["_spell"] for i, e in _spells(cls.dm).items()}

    def _build(self, body: str) -> registry.Registry:
        """Runs `body` (a declaration file using the kit builders) in a throwaway package."""
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "kit_probe"
            pkg.mkdir()
            (pkg / "probe.py").write_text(textwrap.dedent(body), encoding="utf-8")
            return _load_package(pkg)

    def _assert_same(self, spell_id: int, built: registry.Registry):
        self.assertEqual(_spells(built)[spell_id], _spells(self.dm)[spell_id])
        self.assertEqual(_scripts(built, spell_id), _scripts(self.dm, spell_id))

    def test_resolve_copy_is_greenskins(self):
        s = self.dm_spells[205340]
        raw = s.raw_overrides
        built = self._build(f"""
            from lib.dsl.dungeon_kit import resolve_copy
            x = resolve_copy({s.id}, {s.name!r}, {int(s.school)}, {raw['Description_Lang_enUS']!r}, {s.notes!r},
                             icon={s.spell_icon_id}, visual={raw['SpellVisualID_1']},
                             scripts=('spell_dm_greenskin_lane_hit',), excluded={s.effects[0].potency_excluded!r})
        """)
        self._assert_same(205340, built)
        self.assertEqual(_scripts(built, 205340), ["spell_boss_mechanics_resolve", "spell_dm_greenskin_lane_hit"])

    def test_cast_bar_is_greenskins(self):
        s = self.dm_spells[205343]
        built = self._build(f"""
            from lib.dsl.dungeon_kit import cast_bar
            x = cast_bar({s.id}, {s.name!r}, {s.cast_time_ms}, {s.raw_overrides['Description_Lang_enUS']!r},
                         {s.notes!r}, icon={s.spell_icon_id})
        """)
        self._assert_same(205343, built)

    def test_self_visual_is_vancleefs(self):
        s = self.dm_spells[205360]
        built = self._build(f"""
            from lib.dsl.dungeon_kit import self_visual
            x = self_visual({s.id}, {s.name!r}, {s.raw_overrides['SpellVisualID_1']}, {s.notes!r},
                            icon={s.spell_icon_id})
        """)
        self._assert_same(205360, built)

    def test_the_shared_spells_keep_their_shape(self):
        # 205200 Preparing: 2 s DUMMY on the caster, not interruptible; 205201 the -30% / 2 s snare rider
        bar = self.dm_spells[205200]
        self.assertEqual((bar.name, bar.cast_time_ms), ("Preparing", 2000))
        self.assertEqual(bar.raw_overrides["InterruptFlags"], 0)
        self.assertEqual(bar.raw_overrides["PreventionType"], 0)
        slow = self.dm_spells[205201]
        self.assertEqual((slow.name, slow.duration_ms, slow.mechanic), ("Standing in It", 2000, 11))
        self.assertEqual(slow.effects[0].base_points, -31)
        self.assertEqual(slow.raw_overrides["CastingTimeIndex"], 1)
        timer = self.dm_spells[205202]
        self.assertEqual((timer.name, timer.duration_ms, timer.spell_icon_id), ("Burn It Down", 180000, 37))

    def test_kit_creature_and_helper_are_the_pilots_columns(self):
        self.assertEqual(dungeon_kit.kit_creature(faction=17), PILOT_KIT_CREATURE)
        self.assertEqual(dungeon_kit.kit_helper(dungeon_kit.kit_creature(faction=17)), PILOT_KIT_HELPER)
        # another dungeon's faction and creature type
        undead = dungeon_kit.kit_creature(faction=21, type=6)
        self.assertEqual((undead["faction"], undead["type"]), (21, 6))
        self.assertEqual(dungeon_kit.kit_creature(faction=21, MovementType=1)["MovementType"], 1)


class KitRawTest(unittest.TestCase):
    def test_shape(self):
        raw = dungeon_kit.kit_raw("d", "a", SpellVisualID_1=5)
        self.assertEqual(raw["SpellClassSet"], 0)
        self.assertEqual(raw["EquippedItemClass"], -1)
        self.assertEqual(raw["Description_Lang_enUS"], "d")
        self.assertEqual(raw["AuraDescription_Lang_enUS"], "a")
        self.assertEqual(raw["SpellVisualID_1"], 5)
        self.assertNotIn("CastingTimeIndex", raw)
        self.assertEqual(dungeon_kit.kit_raw(instant=True)["CastingTimeIndex"], 1)
        for key, value in dungeon_kit.TEXT_MASKS.items():
            self.assertEqual(raw[key], value)

    def test_resolve_raw_matches_the_boss_mechanics_resolve_set(self):
        # the attribute set of source/npcs/boss_mechanics.py's resolve spells (205001-205007), as the Pilot copied it
        self.assertEqual(dungeon_kit.RESOLVE_RAW["AttributesEx3"], 0x00000200 | 0x00040000 | 0x20000000)
        self.assertEqual(dungeon_kit.RESOLVE_RAW["DefenseType"], 1)
        self.assertEqual(dungeon_kit.IMMUNITY_BOSS_STUN, 1972)


if __name__ == "__main__":
    unittest.main()
