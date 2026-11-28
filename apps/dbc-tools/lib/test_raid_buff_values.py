"""
Raid buff values (raid-buff-sets fix pass, user ruling 2026-11-25: baseline buffs at the stock level 60 value).

Loads the real class DSL packages, builds the spell rows the way generate.py does, and evaluates every raid buff and
debuff row this pass fixed with the core formula (SpellEffectInfo::CalcValue) at caster levels 20 / 40 / 60:

    BasePoints + int(float32((clamp(L, BaseLevel, MaxLevel) - max(BaseLevel, SpellLevel)) x RealPointsPerLevel)) + 1

The rounding check (audit "Rounding: a check worth adding"): a per-level value chosen as an "exact" quotient (0.8644,
0.4915, 1.4615, 0.0333) can land a hair under the integer in float32 and truncate one short at level 60. Every row
here must give the same level 60 amount in float32 and in float64.

Run: cd apps/dbc-tools && PYTHONDONTWRITEBYTECODE=1 python3 -m pytest lib/test_raid_buff_values.py -q
"""

from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.replay_cache import under_replay_cache  # noqa: E402
from lib import build, dbcfmt, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
CLASSES = ("warrior", "paladin", "druid", "priest", "mage", "shaman", "warlock", "hunter", "deathknight")

# (spell id, effect index 1-based) -> {caster level: amount}. Values are the stock level 60 amounts (audit 2026-11-25);
# the shaman attunements are the design's stock +20%; Fire Attunement 202212 and Arcane Resonance 201779 are 120 at 60
# (stock Totem of Wrath, user ruling). Levels below a row's learn level are left out.
EXPECTED = {
    (6673, 1): {20: 84, 40: 158, 60: 232},          # Battle Shout
    (19740, 1): {20: 80, 40: 156, 60: 232},         # Blessing of Might
    (19740, 2): {20: 80, 40: 156, 60: 232},
    (25782, 1): {20: 80, 40: 156, 60: 232},         # Greater Blessing of Might: Blessing of Might's curve
    (25782, 2): {20: 80, 40: 156, 60: 232},
    (1126, 1): {20: 108, 40: 196, 60: 285},         # Mark of the Wild: armor, all stats, all resistances
    (1126, 2): {20: 5, 40: 8, 60: 12},
    (1126, 3): {20: 9, 40: 14, 60: 20},
    (21849, 1): {50: 240, 60: 285},                 # Gift of the Wild
    (21849, 2): {50: 10, 60: 12},
    (21849, 3): {50: 17, 60: 20},
    (54424, 1): {40: 15, 60: 25},                   # Fel Intelligence: Intellect, Spirit
    (54424, 2): {40: 22, 60: 32},
    (202210, 3): {40: 59, 60: 92},                  # Air Attunement Agility
    (202207, 1): {20: 28, 40: 60, 60: 92},          # Earth Attunement Strength
    (202211, 1): {20: 307, 40: 537, 60: 768},       # Earth Attunement Armor
    (202208, 1): {20: 19, 40: 26, 60: 37},          # Water Attunement mp5
    (202212, 1): {20: 30, 40: 63, 60: 120},         # Fire Attunement spell power
    (202212, 2): {20: 30, 40: 63, 60: 120},
    (201779, 1): {20: 30, 40: 63, 60: 120},         # Arcane Resonance
    (201779, 2): {20: 30, 40: 63, 60: 120},
    (205102, 1): {26: 30, 40: 63, 60: 120},         # Arcane Infusion (mage, learned at 26): 202212's curve
    (205102, 2): {26: 30, 40: 63, 60: 120},
    (57330, 1): {20: 27, 40: 56, 60: 86},           # Horn of Winter
    (57330, 2): {20: 27, 40: 56, 60: 86},
    (1459, 1): {20: 11, 40: 21, 60: 31},            # Arcane Intellect
    (1243, 1): {20: 19, 40: 36, 60: 54},            # Power Word: Fortitude
    (469, 1): {22: 293, 40: 503, 60: 738},          # Commanding Shout, option B
    (6307, 1): {20: 122, 40: 251, 60: 380},         # Blood Pact
    (465, 1): {20: 273, 40: 504, 60: 735},          # Devotion Aura
    (201764, 1): {20: 273, 40: 504, 60: 735},       # Hardened Shell
    (201715, 1): {20: 23, 40: 50, 60: 77},          # Roar of Courage
    (201715, 2): {20: 23, 40: 50, 60: 77},
    (201767, 1): {20: 23, 40: 50, 60: 77},          # Primal Might
    (201767, 2): {20: 23, 40: 50, 60: 77},
    (19742, 1): {20: 13, 40: 23, 60: 33},           # Blessing of Wisdom
    (25894, 1): {54: 30, 60: 33},                   # Greater Blessing of Wisdom
    (201757, 1): {20: 16, 40: 22, 60: 31},          # Moonglow Dust
    (1160, 1): {20: -49, 40: -97, 60: -146},        # Demoralizing Shout and the pet copies
    (201717, 1): {20: -49, 40: -97, 60: -146},
    (201754, 1): {20: -49, 40: -97, 60: -146},
    (201771, 1): {20: -49, 40: -97, 60: -146},
    (99, 1): {20: -54, 40: -100, 60: -146},         # Demoralizing Roar
    (702, 1): {20: -61, 40: -112, 60: -163},        # Curse of Weakness
    (24423, 2): {20: -68, 40: -104, 60: -140},      # Demoralizing Screech
    (1490, 1): {40: -53, 60: -75},                  # Curse of the Elements resistances
    (50170, 1): {20: 1, 40: 1, 60: 1},              # Improved Moonkin Form rank 1: a flat 1%
}


def f32(x: float) -> float:
    return struct.unpack("f", struct.pack("f", x))[0]


def _i(row: dict, col: str) -> int:
    return int(row.get(col) or 0)


def calc_value(row: dict, effect: int, level: int, *, single: bool = True) -> int:
    base, spell_level, max_level = _i(row, "BaseLevel"), _i(row, "SpellLevel"), _i(row, "MaxLevel")
    if max_level > 0 and level > max_level:
        level = max_level
    if level < base:
        level = base
    ppl = float(row.get(f"EffectRealPointsPerLevel_{effect}") or 0.0)
    levels = level - max(base, spell_level)
    scaled = int(f32(levels * f32(ppl))) if single else int(levels * ppl)
    return _i(row, f"EffectBasePoints_{effect}") + scaled + (1 if _i(row, f"EffectDieSides_{effect}") == 1 else 0)


_CACHE: dict = {}


@under_replay_cache
def _rows() -> dict[int, dict]:
    if not _CACHE:
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        spell_table_index = spell_tables.load_spell_table_index()
        creature_table_index = spell_tables.load_creature_table_index()
        reuse = ReuseContext({}, ids_cfg)
        wanted = {sid for sid, _ in EXPECTED}
        for name in CLASSES:
            package = registry.load_class_package(
                TOOL_ROOT / "source" / "classes" / name, ids_cfg=ids_cfg, trainer_index=trainer_state.load_trainer_index(),
                existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
                shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
                existing_creature_rows={int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")},
                creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
                creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
                live_data=spell_tables.load_dsl_live_data(),
            )
            for entry in package.spells:
                if int(entry["id"]) in wanted:
                    _CACHE[int(entry["id"])] = build.build_spell_row(entry, reuse)
    return _CACHE


class RaidBuffValuesTest(unittest.TestCase):
    def test_every_row_is_built(self):
        rows = _rows()
        self.assertEqual(sorted({sid for sid, _ in EXPECTED} - set(rows)), [])

    def test_values_at_20_40_60(self):
        rows = _rows()
        bad = []
        for (sid, eff), levels in sorted(EXPECTED.items()):
            for level, want in levels.items():
                got = calc_value(rows[sid], eff, level)
                if got != want:
                    bad.append(f"{sid} effect {eff} at {level}: {got}, expected {want}")
        self.assertEqual(bad, [], "\n" + "\n".join(bad))

    def test_float32_rounding_does_not_cost_a_point(self):
        rows = _rows()
        bad = []
        for (sid, eff), levels in sorted(EXPECTED.items()):
            for level in levels:
                single, double = calc_value(rows[sid], eff, level), calc_value(rows[sid], eff, level, single=False)
                if single != double:
                    bad.append(f"{sid} effect {eff} at {level}: float32 {single}, float64 {double}")
        self.assertEqual(bad, [], "\n" + "\n".join(bad))

    def test_arcane_infusion_is_the_fire_attunement_spell_power_curve(self):
        # one spell, both effects on the 202212 columns: aura 13 school mask 126 and aura 135 mask 127, raid target 56
        rows = _rows()
        ai, fire = rows[205102], rows[202212]
        for col in ("BaseLevel", "SpellLevel", "MaxLevel"):
            self.assertEqual(ai[col], fire[col], col)
        for eff in (1, 2):
            for col in ("EffectBasePoints", "EffectRealPointsPerLevel", "EffectAura", "EffectMiscValue"):
                self.assertEqual(ai[f"{col}_{eff}"], fire[f"{col}_{eff}"], f"{col}_{eff}")
            self.assertEqual(_i(ai, f"ImplicitTargetA_{eff}"), 56)
        self.assertEqual((_i(ai, "EffectAura_1"), _i(ai, "EffectMiscValue_1")), (13, 126))
        self.assertEqual((_i(ai, "EffectAura_2"), _i(ai, "EffectMiscValue_2")), (135, 127))
        self.assertEqual(_i(ai, "EffectAura_3"), 0)
        # not Arcane Intellect's family bit, icon, visual or consolidated-buffs flag
        arcane_intellect = rows.get(1459) or {}
        self.assertEqual(_i(ai, "SpellClassMask_1"), 0)
        self.assertNotEqual(_i(ai, "SpellIconID"), 125)
        self.assertNotEqual(_i(ai, "SpellIconID"), 1694)
        self.assertNotEqual(_i(ai, "SpellVisualID_1"), _i(arcane_intellect, "SpellVisualID_1"))
        self.assertEqual(_i(ai, "AttributesEx7") & 0x10000000, 0)

    def test_the_check_can_fail(self):
        # 59 x 0.8644 = 51.0 - 0.0004: the old Power Word: Fortitude slope truncates one short in float32
        row = {"BaseLevel": 1, "SpellLevel": 1, "MaxLevel": 80, "EffectBasePoints_1": 2,
               "EffectRealPointsPerLevel_1": 0.8644, "EffectDieSides_1": 1}
        self.assertEqual(calc_value(row, 1, 60), 53)
        self.assertEqual(calc_value({**row, "EffectRealPointsPerLevel_1": 0.865}, 1, 60), 54)


if __name__ == "__main__":
    unittest.main()
