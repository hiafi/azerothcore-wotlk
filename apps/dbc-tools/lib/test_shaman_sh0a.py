"""
Shaman SH0a data gate (shaman-rework SH0a-HANDOFF row A6, SH0a-WP-BRIEF).

Loads the real shaman DSL package (source/classes/shaman/) and asserts on the BUILT rows (stock base + DSL +
raw_overrides via `build.build_spell_row`, the way generate.py pairs them), so a stale raw twin that wins fails here
too. Ids not declared yet are skipped, so the file runs at any point of the stage.

  1. EquippedItemClass -1 on every A1-A4 id.
  2. No FORBIDDEN_D0/D1/D2 bit (_masks.py) in the own SpellClassMask of a new SH0a spell or an imbue; SpellMod effect
     masks only non-zero.
  3. Imbue auras lack d1 b11; no DUMMY at effect index 0 with own SpellIconID 688; no DUMMY on a spell whose own SpellClassMask_1 has 0x200000.
  4. Attunements (202207-202210) and children (202211/202212): no family bits, AttributesEx3 0x100000.
  5. Shocks: Category 0, RecoveryTime 6000 (8042/8050/8056/421), 1535 RecoveryTime 10000.
  6. Rockbiter AP at L20/24/42/52/60 = 10/21/70/98/120 (T0a-REPORT section 4 engine formula).
  7. spell_group 1252 id is lower than every other declared group shared by two attunement parents.
  8. No SH0a spell a player learns has Attributes 0x80 (DO_NOT_DISPLAY).

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_shaman_sh0a.py -q
"""

from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
SHAMAN_DIR = TOOL_ROOT / "source" / "classes" / "shaman"
sys.path.insert(0, str(TOOL_ROOT / "source" / "classes"))
_masks_spec = __import__("importlib.util").util.spec_from_file_location("_shaman_masks", SHAMAN_DIR / "_masks.py")
m = __import__("importlib.util").util.module_from_spec(_masks_spec)
_masks_spec.loader.exec_module(m)

LETTERS = ("A", "B", "C")
IMBUES = (8017, 8024, 8033, 8232, 51730)
NEW_SPELLS = tuple(range(202200, 202213))
ATTUNEMENT_PARENTS = (202207, 202208, 202209, 202210)
ATTUNEMENT_CHILDREN = (202211, 202212)
EQUIPPED_IDS = (8017, 8024, 8033, 8232, 51730, 8042, 8050, 8056, 421, 1535, 57994, 51514, 51505, 2825, 32182, 974,
                51886, 20608, 21169, 52127, 51945, 55455) + NEW_SPELLS
SHOCKS_6S = (8042, 8050, 8056, 421)
SHOCK_10S = (1535,)
ROCKBITER = 8017
ROCKBITER_AP = {20: 10, 24: 21, 42: 70, 52: 98, 60: 120}
ATTUNEMENT_GROUP = 1252
DUMMY_AURA = 4
ICON_688 = 688
FLAMETONGUE_ATTACK_D0 = 0x200000
D1_B11 = 0x800
ATTR0_DO_NOT_DISPLAY = 0x80
ATTR3_DEATH_PERSISTENT = 0x100000
PET_SKILL_LINE = 270
SH0A_LEARNABLE = tuple(EQUIPPED_IDS)


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def effect_mask(row: dict, effect: int) -> tuple[int, int, int]:
    letter = LETTERS[effect - 1]
    return tuple(_u32(row.get(f"EffectSpellClassMask{letter}_{n}")) for n in (1, 2, 3))


def spell_mask(row: dict) -> tuple[int, int, int]:
    return tuple(_u32(row.get(f"SpellClassMask_{n}")) for n in (1, 2, 3))


def all_masks(row: dict) -> list[tuple[str, tuple[int, int, int]]]:
    return [("SpellClassMask", spell_mask(row))] + [(f"effect {i}", effect_mask(row, i)) for i in (1, 2, 3)]


def _hex(mask) -> str:
    return "(" + ", ".join(f"0x{w:X}" for w in mask) + ")"


def _f32(value) -> float:
    return struct.unpack("f", struct.pack("f", float(value or 0)))[0]


def engine_value(row: dict, effect: int, level: int) -> int:
    """SpellEffectInfo::CalcValue for a player-cast spell with die sides 1 (T0a-REPORT section 4)."""
    bp = int(row.get(f"EffectBasePoints_{effect}") or 0)
    ppl = _f32(row.get(f"EffectRealPointsPerLevel_{effect}"))
    base, spell_level, max_level = (int(row.get(k) or 0) for k in ("BaseLevel", "SpellLevel", "MaxLevel"))
    clamped = level
    if max_level and clamped > max_level:
        clamped = max_level
    if base and clamped < base:
        clamped = base
    return (bp + 1) + int((clamped - max(base, spell_level)) * ppl)


# ---- checks (pure: take built rows, return problem strings) ------------------------------------------------

def check_equipped_item_class(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for spell_id in EQUIPPED_IDS:
        row = rows_by_id.get(spell_id)
        if row is None:
            continue
        value = row.get("EquippedItemClass")
        if value is None or _u32(value) != 0xFFFFFFFF:
            bad.append(f"{spell_id}: EquippedItemClass {value!r}, expected -1")
    return bad


SPELLMOD_AURAS = {107, 108}


def check_forbidden_bits(rows_by_id: dict[int, dict]) -> list[str]:
    """FORBIDDEN_* applies to a spell's OWN identity mask only; effect masks of SpellMod auras may target them.
    Effect masks are only required to be non-zero on a SpellMod aura (all-zero matches the whole family)."""
    bad = []
    for spell_id in NEW_SPELLS + IMBUES:
        row = rows_by_id.get(spell_id)
        if row is None:
            continue
        mask = spell_mask(row)
        hit = (mask[0] & m.FORBIDDEN_D0, mask[1] & m.FORBIDDEN_D1, mask[2] & m.FORBIDDEN_D2)
        if any(hit):
            bad.append(f"{spell_id}: SpellClassMask {_hex(mask)} holds forbidden bits {_hex(hit)}")
        for i in (1, 2, 3):
            if int(row.get(f"EffectAura_{i}") or 0) in SPELLMOD_AURAS and not any(effect_mask(row, i)):
                bad.append(f"{spell_id}: SpellMod effect {i} has an all-zero mask (matches the whole family)")
    return bad


def check_imbue_aura_masks(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for spell_id in IMBUES:
        row = rows_by_id.get(spell_id)
        if row is None:
            continue
        for label, mask in all_masks(row):
            if mask[1] & D1_B11:
                bad.append(f"{spell_id}: {label} {_hex(mask)} carries d1 b11")
        for i in (1, 2, 3):
            if int(row.get(f"EffectAura_{i}") or 0) != DUMMY_AURA:
                continue
            # Unit.cpp:5642 reads the aura's own SpellIconID, :5656 its own SpellFamilyFlags d0
            if i == 1 and int(row.get("SpellIconID") or 0) == ICON_688:
                bad.append(f"{spell_id}: DUMMY at effect index 0 with SpellIconID 688")
            if spell_mask(row)[0] & FLAMETONGUE_ATTACK_D0:
                bad.append(f"{spell_id}: DUMMY effect {i} on a spell whose own SpellClassMask_1 has d0 0x200000")
    return bad


def check_attunements(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for spell_id in ATTUNEMENT_PARENTS + ATTUNEMENT_CHILDREN:
        row = rows_by_id.get(spell_id)
        if row is None:
            continue
        for label, mask in all_masks(row):
            if any(mask):
                bad.append(f"{spell_id}: {label} {_hex(mask)} carries family bits")
        if not _u32(row.get("AttributesEx3")) & ATTR3_DEATH_PERSISTENT:
            bad.append(f"{spell_id}: AttributesEx3 lacks 0x100000")
    return bad


def check_shocks(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for spell_id, want in [(i, 6000) for i in SHOCKS_6S] + [(i, 10000) for i in SHOCK_10S]:
        row = rows_by_id.get(spell_id)
        if row is None:
            continue
        if int(row.get("Category") or 0) != 0:
            bad.append(f"{spell_id}: Category {row.get('Category')}, expected 0")
        if int(row.get("RecoveryTime") or 0) != want:
            bad.append(f"{spell_id}: RecoveryTime {row.get('RecoveryTime')}, expected {want}")
        if int(row.get("CategoryRecoveryTime") or 0) != 0:
            bad.append(f"{spell_id}: CategoryRecoveryTime {row.get('CategoryRecoveryTime')}, expected 0")
    return bad


def check_rockbiter_ap(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(ROCKBITER)
    if row is None:
        return []
    if int(row.get("EffectAura_1") or 0) != 99:
        return [f"{ROCKBITER}: effect 1 aura {row.get('EffectAura_1')}, expected 99 (MOD_ATTACK_POWER)"]
    return [f"{ROCKBITER}: AP at L{lvl} = {engine_value(row, 1, lvl)}, expected {want}"
            for lvl, want in ROCKBITER_AP.items() if engine_value(row, 1, lvl) != want]


def check_attunement_group_order(groups: list[dict]) -> list[str]:
    members: dict[int, set[int]] = {}
    for g in groups:
        if int(g["spell_id"]) in ATTUNEMENT_PARENTS:
            members.setdefault(int(g["id"]), set()).add(int(g["spell_id"]))
    if not members:
        return []
    bad = []
    if ATTUNEMENT_GROUP not in members:
        bad.append(f"group {ATTUNEMENT_GROUP} holds no attunement parent")
    elif len(members[ATTUNEMENT_GROUP]) != len(ATTUNEMENT_PARENTS):
        bad.append(f"group {ATTUNEMENT_GROUP} holds {sorted(members[ATTUNEMENT_GROUP])}, expected all four parents")
    for gid, spells in members.items():
        if gid != ATTUNEMENT_GROUP and len(spells) >= 2 and gid < ATTUNEMENT_GROUP:
            bad.append(f"group {gid} shares {sorted(spells)} but its id is lower than {ATTUNEMENT_GROUP}")
    return bad


def check_learned_not_hidden(rows_by_id: dict[int, dict], learned: set[int]) -> list[str]:
    return [f"{i}: learned by a player but Attributes {int(rows_by_id[i].get('Attributes') or 0):#x} has 0x80"
            for i in sorted(learned) if i in rows_by_id and i in SH0A_LEARNABLE
            and int(rows_by_id[i].get("Attributes") or 0) & ATTR0_DO_NOT_DISPLAY]


# ---- real data ----------------------------------------------------------------------------------------------

_CACHE: dict = {}


def _data():
    if not _CACHE:
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        spell_table_index = spell_tables.load_spell_table_index()
        creature_table_index = spell_tables.load_creature_table_index()
        package = registry.load_class_package(
            SHAMAN_DIR, ids_cfg=ids_cfg, trainer_index=trainer_state.load_trainer_index(),
            existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
            shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
            existing_creature_rows={int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")},
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.load_dsl_live_data(),
        )
        reuse = ReuseContext({}, ids_cfg)
        rows = [build.build_spell_row(e, reuse) for e in package.spells]
        learned = {int(t["SpellId"]) for t in package.trainer_spells}
        learned |= {int(s["spell_id"]) for s in package.skill_line_abilities if int(s["skill_line"]) != PET_SKILL_LINE}
        _CACHE.update(rows_by_id={int(r["ID"]): r for r in rows}, groups=package.spell_groups, learned=learned)
    return _CACHE


class ShamanSH0aDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_equipped_item_class(self):
        self.assertClean(check_equipped_item_class(_data()["rows_by_id"]))

    def test_no_forbidden_bits(self):
        self.assertClean(check_forbidden_bits(_data()["rows_by_id"]))

    def test_imbue_aura_masks(self):
        self.assertClean(check_imbue_aura_masks(_data()["rows_by_id"]))

    def test_attunements_and_children(self):
        self.assertClean(check_attunements(_data()["rows_by_id"]))

    def test_shocks(self):
        self.assertClean(check_shocks(_data()["rows_by_id"]))

    def test_rockbiter_ap(self):
        self.assertClean(check_rockbiter_ap(_data()["rows_by_id"]))

    def test_attunement_group_order(self):
        self.assertClean(check_attunement_group_order(_data()["groups"]))

    def test_learned_spells_not_hidden(self):
        self.assertClean(check_learned_not_hidden(_data()["rows_by_id"], _data()["learned"]))


# ---- negative fixtures: every check must fire on a minimal bad input ---------------------------------------

def _row(spell_id=1, **cols) -> dict:
    return {"ID": spell_id, **cols}


class ShamanSH0aNegativeTest(unittest.TestCase):
    def test_equipped_item_class(self):
        self.assertEqual(len(check_equipped_item_class({8017: _row(8017, EquippedItemClass=2)})), 1)
        self.assertEqual(len(check_equipped_item_class({8017: _row(8017)})), 1)
        self.assertEqual(check_equipped_item_class({8017: _row(8017, EquippedItemClass=-1)}), [])
        self.assertEqual(check_equipped_item_class({8017: _row(8017, EquippedItemClass=0xFFFFFFFF)}), [])

    def test_forbidden_bits(self):
        for col, bit in (("SpellClassMask_1", 0x1), ("SpellClassMask_2", 0x800), ("SpellClassMask_3", 0x4),
                         ("SpellClassMask_2", 0x20)):
            self.assertEqual(len(check_forbidden_bits({202202: _row(202202, **{col: bit})})), 1, col)
        self.assertEqual(len(check_forbidden_bits({8024: _row(8024, SpellClassMask_2=0x800)})), 1)
        self.assertEqual(check_forbidden_bits({202202: _row(202202, SpellClassMask_1=m.FLAMETONGUE_ATTACK)}), [])
        self.assertEqual(check_forbidden_bits({52127: _row(52127, SpellClassMask_2=0x20)}), [])  # stock shield
        # effect masks may legitimately target forbidden bits
        self.assertEqual(check_forbidden_bits({8033: _row(8033, EffectAura_1=107, EffectSpellClassMaskA_1=1)}), [])

    def test_spellmod_all_zero_mask(self):
        self.assertEqual(len(check_forbidden_bits({8017: _row(8017, EffectAura_2=108)})), 1)

    def test_imbue_d1_b11(self):
        self.assertEqual(len(check_imbue_aura_masks({8033: _row(8033, SpellClassMask_2=0x800)})), 1)
        self.assertEqual(len(check_imbue_aura_masks({8033: _row(8033, EffectSpellClassMaskC_2=0x800)})), 1)

    def test_imbue_icon_688_dummy(self):
        row = _row(8024, EffectAura_1=4, SpellIconID=688)
        self.assertEqual(len(check_imbue_aura_masks({8024: row})), 1)
        self.assertEqual(check_imbue_aura_masks({8024: _row(8024, EffectAura_2=4, SpellIconID=688)}), [])  # not eff 0
        self.assertEqual(check_imbue_aura_masks({8024: _row(8024, EffectAura_1=4, EffectMiscValue_1=688)}), [])

    def test_imbue_dummy_with_flametongue_bit(self):
        row = _row(8024, EffectAura_2=4, SpellClassMask_1=0x200000)
        self.assertEqual(len(check_imbue_aura_masks({8024: row})), 1)
        self.assertEqual(check_imbue_aura_masks({8024: _row(8024, EffectAura_2=6, SpellClassMask_1=0x200000)}), [])

    def test_attunement_family_bits_and_ex3(self):
        good = _row(202207, AttributesEx3=0x100000)
        self.assertEqual(check_attunements({202207: good}), [])
        self.assertEqual(len(check_attunements({202207: {**good, "SpellClassMask_1": 1}})), 1)
        self.assertEqual(len(check_attunements({202211: {**good, "ID": 202211, "EffectSpellClassMaskC_3": 4}})), 1)
        self.assertEqual(len(check_attunements({202207: _row(202207)})), 1)

    def test_shocks(self):
        good = _row(8042, Category=0, RecoveryTime=6000)
        self.assertEqual(check_shocks({8042: good}), [])
        self.assertEqual(len(check_shocks({8042: {**good, "Category": 19}})), 1)
        self.assertEqual(len(check_shocks({8042: _row(8042, Category=0, CategoryRecoveryTime=6000)})), 2)
        self.assertEqual(len(check_shocks({1535: _row(1535, Category=0, RecoveryTime=6000)})), 1)

    def test_rockbiter_ap(self):
        row = _row(8017, EffectAura_1=99, EffectBasePoints_1=9, EffectRealPointsPerLevel_1=2.75, BaseLevel=20,
                   SpellLevel=1, MaxLevel=60)
        self.assertEqual(check_rockbiter_ap({8017: row}), [])
        self.assertEqual(len(check_rockbiter_ap({8017: {**row, "EffectRealPointsPerLevel_1": 3.0}})), 4)
        self.assertEqual(len(check_rockbiter_ap({8017: {**row, "BaseLevel": 15}})), 5)
        self.assertEqual(len(check_rockbiter_ap({8017: {**row, "EffectAura_1": 4}})), 1)

    def test_group_order(self):
        def g(gid, *spells):
            return [{"id": gid, "spell_id": s} for s in spells]
        ok = g(1252, *ATTUNEMENT_PARENTS) + g(1253, 57330, 202207, 202210) + g(1022, 202210)
        self.assertEqual(check_attunement_group_order(ok), [])
        bad = g(1252, *ATTUNEMENT_PARENTS) + g(1251, 202207, 202210)
        self.assertEqual(len(check_attunement_group_order(bad)), 1)
        self.assertEqual(len(check_attunement_group_order(g(1252, 202207, 202208))), 1)  # missing parents
        self.assertEqual(len(check_attunement_group_order(g(1253, 202207, 202210))), 1)  # no 1252

    def test_learned_hidden(self):
        rows = {202207: _row(202207, Attributes=0x80)}
        self.assertEqual(len(check_learned_not_hidden(rows, {202207})), 1)
        self.assertEqual(check_learned_not_hidden(rows, set()), [])  # hidden helper nobody learns
        self.assertEqual(check_learned_not_hidden({202207: _row(202207, Attributes=0x40)}, {202207}), [])

    def test_engine_formula_matches_report(self):
        row = _row(8017, EffectBasePoints_1=9, EffectRealPointsPerLevel_1=2.75, BaseLevel=20, SpellLevel=1, MaxLevel=60)
        self.assertEqual([engine_value(row, 1, lv) for lv in (10, 24, 42, 52, 60, 70)], [10, 21, 70, 98, 120, 120])


if __name__ == "__main__":
    unittest.main()
