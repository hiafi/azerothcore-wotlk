"""
Hunter SpellMod family gate (hunter-rework SHARED section B0 step 5, B13, B17; X24).

`SpellInfo::IsAffected` returns true for every spell when a SpellMod's `SpellFamilyName` is 0, and it
matches on ANY shared bit, so a hunter mod at `SpellClassSet 0`, an all-zero mask, a reader mask holding
the pet bit (d1 b28) or one still holding the old Steady Shot bit (d1 b0) leaks into other spells. This
loads the real hunter DSL package (source/classes/hunter/) and asserts, on the BUILT rows (stock base +
DSL + raw_overrides, i.e. `build.build_spell_row`, paired entry <-> row the way generate.py pairs them
for `check_classmask_scoping`, so a stale raw twin that wins fails here too):

  1. every aura 107/108 effect: SpellClassSet 9 and a non-zero mask on that effect; every declared
     spell_proc with a family mask has SpellFamilyName 9; no custom (>= 200000) effect mask and no
     declared spell_proc family mask contains d1 0x10000000.
  2. H0 guards: 201600-201605 carry no aspect bit and no d1 0x1; 56641 has d2 0x20000000 and no d1 0x1;
     every SHARED B13 effect has d1 0x1 clear and d2 0x20000000 set; T.N.T./3674/63066 have d2 0x40
     clear; the five re-keyed spell_proc rows carry the B13 masks; a stock row's built SpellClassSet
     equals the stock client's.

Ids not declared yet are skipped. BM and MM extend this file (PET's kits 201706-201708 join in H0-P).

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_hunter_spellmod_family.py -q
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
HUNTER_DIR = TOOL_ROOT / "source" / "classes" / "hunter"

SPELLFAMILY_HUNTER = 9
SPELLMOD_AURAS = {107, 108}  # ADD_FLAT_MODIFIER, ADD_PCT_MODIFIER
LETTERS = ("A", "B", "C")
CUSTOM_ID_START = 200000
PET_BIT = (0, 0x10000000, 0)
OLD_STEADY_BIT = 0x1                 # d1 b0
STEADY_SHOT_BIT = 0x20000000         # d2 b29
GLAIVE_TOSS_BIT = 0x40               # d2 b6
ASPECT_SPECIFIC = (0x380000, 0x440000, 0x1010)  # mirrors _masks.ASPECT_SPECIFIC

# SHARED B13: (ids, 1-based effect index). The effect's typed/raw mask must have d1 0x1 clear, d2 b29 set.
B13_REPOINTS = (
    ((1978,), 2), ((3674,), 2),
    ((19419, 19420), 1),                                    # Efficiency (orphans; S2a makes r1-r3 eff0 a DUMMY)
    ((19485, 19487, 19488, 19489, 19490), 1),               # Mortal Shots
    ((19498, 19499, 19500), 1),                             # Hawk Eye
    ((34455, 34459, 34460), 3),                             # Ferocious Inspiration
    ((34488, 34489), 2),                                    # Master Marksman (orphans; S2a drops r1-r3 eff1)
    ((34494, 34496), 2),                                    # Survival Instincts
    ((34506, 34507, 34508, 34838, 34839), 1),               # Master Tactician trigger
    ((34833, 34834, 34835, 34836, 34837), 1),               # Master Tactician buff
    ((53234, 53237, 53238), 1),                             # Piercing Shots
    ((53245, 53246), 2),                                    # Marked for Death (orphans; S2a: r1-r3 eff1 = DOT
                                                            # on d2 b28, test_hunter_mm_data.py checks it)
    ((53620, 53621, 53622), 1),                             # Focused Aim
    ((64418, 64419, 64420), 1),                             # Sniper Training
)
# d2 b6 strips: (ids, 1-based effect index)
B13_GLAIVE_STRIPS = (((56333, 56336, 56337), 2), ((3674,), 2), ((63066,), 1))
# Re-keyed spell_proc rows: key -> (family, (m0, m1, m2)) after B13.
B13_SPELL_PROCS = {
    -53290: (0x800, 0, 0x20000200),
    # Cobra Strikes: H0's (0x800, 0x800000, 0x20000000) row, edited in place by S1b B2 to Steady Shot d2 b29 only (CAST
    # phase, spell_hun_cobra_strikes_bm resets Arcane Shot); test_hunter_bm_data.py checks its other columns.
    -53256: (0, 0, 0x20000000),
    -53234: (0x20000, 0, 0x20000000),        # S2a (MM 8): narrowed to Steady + Aimed, Chimera's d2 b0 dropped
    -53221: (0, 0, 0x20000000),
    -34497: (0x60800, 0x800000, 0x20000201),
}
H0_NEW_SPELLS = range(201600, 201606)
STEADY_SHOT_ID = 56641


def _load_hunter_package() -> dict:
    ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
    spell_table_index = spell_tables.load_spell_table_index()
    creature_table_index = spell_tables.load_creature_table_index()
    return registry.load_class_package(
        HUNTER_DIR, ids_cfg=ids_cfg, trainer_index=trainer_state.load_trainer_index(),
        existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
        shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
        existing_creature_rows={int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")},
        creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        live_data=spell_tables.load_dsl_live_data(),
    ), ids_cfg


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def effect_mask(row: dict, effect: int) -> tuple[int, int, int]:
    """Effect `effect` (1-based) mask dwords: letter = effect index, number = dword (README Gotcha)."""
    letter = LETTERS[effect - 1]
    return tuple(_u32(row.get(f"EffectSpellClassMask{letter}_{n}")) for n in (1, 2, 3))


def spell_mask(row: dict) -> tuple[int, int, int]:
    return tuple(_u32(row.get(f"SpellClassMask_{n}")) for n in (1, 2, 3))


def _shares(mask, bits) -> bool:
    return any(m & b for m, b in zip(mask, bits))


def _hex(mask) -> str:
    return "(" + ", ".join(f"0x{w:X}" for w in mask) + ")"


# ---- checks (pure: take built rows / procs, return problem strings) ----------------------------------------

def check_spellmod_scoping(rows: list[dict]) -> list[str]:
    """(1a) aura 107/108 effect -> SpellClassSet 9 and a non-zero mask on that effect."""
    bad = []
    for row in rows:
        for i in (1, 2, 3):
            if row.get(f"EffectAura_{i}") not in SPELLMOD_AURAS:
                continue
            if int(row.get("SpellClassSet") or 0) != SPELLFAMILY_HUNTER:
                bad.append(f"{row['ID']}: effect {i} is a SpellMod but SpellClassSet is "
                           f"{row.get('SpellClassSet') or 0} (family 0 matches every spell)")
            if not any(effect_mask(row, i)):
                bad.append(f"{row['ID']}: effect {i} is a SpellMod with an all-zero mask")
    return bad


def check_proc_family(procs: list[dict]) -> list[str]:
    """(1b) a declared spell_proc with a family mask must have SpellFamilyName 9."""
    bad = []
    for proc in procs:
        mask = tuple(_u32(proc.get(f"SpellFamilyMask{n}")) for n in (0, 1, 2))
        if any(mask) and int(proc.get("SpellFamilyName") or 0) != SPELLFAMILY_HUNTER:
            bad.append(f"spell_proc {proc['SpellId']}: family mask {_hex(mask)} with SpellFamilyName "
                       f"{proc.get('SpellFamilyName') or 0}")
    return bad


def check_no_pet_bit_reader(rows: list[dict], procs: list[dict]) -> list[str]:
    """(1c) no custom effect mask and no declared spell_proc family mask contains d1 0x10000000."""
    bad = []
    for row in rows:
        if int(row["ID"]) < CUSTOM_ID_START:
            continue
        for i in (1, 2, 3):
            if _shares(effect_mask(row, i), PET_BIT):
                bad.append(f"{row['ID']}: effect {i} mask {_hex(effect_mask(row, i))} contains the pet bit d1 b28")
    for proc in procs:
        mask = tuple(_u32(proc.get(f"SpellFamilyMask{n}")) for n in (0, 1, 2))
        if _shares(mask, PET_BIT):
            bad.append(f"spell_proc {proc['SpellId']}: family mask {_hex(mask)} contains the pet bit d1 b28")
    return bad


def check_h0_new_spells(rows_by_id: dict[int, dict]) -> list[str]:
    """(2a) 201600-201605: no aspect bit and no d1 0x1 on the spell mask or any effect mask."""
    bad = []
    for spell_id in H0_NEW_SPELLS:
        row = rows_by_id.get(spell_id)
        if row is None:
            continue
        masks = [("SpellClassMask", spell_mask(row))] + [(f"effect {i}", effect_mask(row, i)) for i in (1, 2, 3)]
        for label, mask in masks:
            if label == "SpellClassMask" and _shares(mask, ASPECT_SPECIFIC):
                bad.append(f"{spell_id}: {label} {_hex(mask)} carries an aspect bit (SPELL_SPECIFIC_ASPECT)")
            if mask[1] & OLD_STEADY_BIT:
                bad.append(f"{spell_id}: {label} {_hex(mask)} carries d1 0x1 (old Steady Shot bit)")
    return bad


def check_steady_shot(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(STEADY_SHOT_ID)
    if row is None:
        return []
    mask = spell_mask(row)
    bad = []
    if not mask[2] & STEADY_SHOT_BIT:
        bad.append(f"{STEADY_SHOT_ID}: SpellClassMask {_hex(mask)} lacks d2 0x20000000")
    if mask[1] & OLD_STEADY_BIT:
        bad.append(f"{STEADY_SHOT_ID}: SpellClassMask {_hex(mask)} still carries d1 0x1")
    return bad


def check_b13_repoints(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for ids, effect in B13_REPOINTS:
        for spell_id in ids:
            row = rows_by_id.get(spell_id)
            if row is None:
                continue
            mask = effect_mask(row, effect)
            if mask[1] & OLD_STEADY_BIT:
                bad.append(f"{spell_id}: effect {effect} mask {_hex(mask)} still has d1 0x1")
            if not mask[2] & STEADY_SHOT_BIT:
                bad.append(f"{spell_id}: effect {effect} mask {_hex(mask)} lacks d2 0x20000000")
    return bad


def check_b13_glaive_strips(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for ids, effect in B13_GLAIVE_STRIPS:
        for spell_id in ids:
            row = rows_by_id.get(spell_id)
            if row is None:
                continue
            mask = effect_mask(row, effect)
            if mask[2] & GLAIVE_TOSS_BIT:
                bad.append(f"{spell_id}: effect {effect} mask {_hex(mask)} still has d2 b6 (Glaive Toss)")
    return bad


def check_b13_spell_procs(procs: list[dict]) -> list[str]:
    by_key = {int(p["SpellId"]): p for p in procs}
    bad = []
    for key, want in B13_SPELL_PROCS.items():
        proc = by_key.get(key)
        if proc is None:
            continue
        got = tuple(_u32(proc.get(f"SpellFamilyMask{n}")) for n in (0, 1, 2))
        if got != want:
            bad.append(f"spell_proc {key}: mask {_hex(got)}, expected {_hex(want)}")
    return bad


# Deliberate SpellClassSet changes on pulled stock rows. Bloodthirsty 53186/53187 go from family 17 to 0 on purpose
# (hunter-rework PET.md 7.1: the old family filter is dropped and spell_hun_pet_bloodthirsty does the gating); they
# are proc-trigger auras, not SpellMods, so family 0 does not leak a modifier.
# S2a (MARKSMANSHIP 6, S2-HANDOFF stale line 11): Lethal Shots 19426/19427/19429 and Ranged Weapon Specialization
# 19507-19509 go from stock family 0 to 9 on purpose: they become scoped SpellMods (a family-0 SpellMod matches every
# spell, and check_family_zero_spellmods warns on one).
INTENTIONAL_CLASS_SET_CHANGES = frozenset({53186, 53187, 19426, 19427, 19429, 19507, 19508, 19509})


def check_class_set_matches_stock(rows_by_id: dict[int, dict], stock: dict[int, dict]) -> list[str]:
    """A pulled stock row may not diverge from the stock client's SpellClassSet (a repeated or stale
    raw_overrides value would silently win)."""
    bad = []
    for spell_id, row in rows_by_id.items():
        if spell_id >= CUSTOM_ID_START or spell_id not in stock or spell_id in INTENTIONAL_CLASS_SET_CHANGES:
            continue
        built, base = int(row.get("SpellClassSet") or 0), int(stock[spell_id].get("SpellClassSet") or 0)
        if built != base:
            bad.append(f"{spell_id}: built SpellClassSet {built} differs from stock {base}")
    return bad


# ---- real data ----------------------------------------------------------------------------------------------

_CACHE: dict = {}


def _data():
    if not _CACHE:
        package, ids_cfg = _load_hunter_package()
        reuse = ReuseContext({}, ids_cfg)
        entries = package.spells
        rows = [build.build_spell_row(e, reuse) for e in entries]
        _CACHE.update(
            rows=rows, rows_by_id={int(r["ID"]): r for r in rows}, procs=package.spell_procs,
            stock=state.load_stock_rows(dbcfmt.SPELL),
        )
    return _CACHE


class HunterSpellModFamilyTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_spellmod_carriers_are_hunter_family_and_scoped(self):
        self.assertClean(check_spellmod_scoping(_data()["rows"]))

    def test_spell_proc_family_masks_have_hunter_family(self):
        self.assertClean(check_proc_family(_data()["procs"]))

    def test_no_custom_reader_holds_the_pet_bit(self):
        self.assertClean(check_no_pet_bit_reader(_data()["rows"], _data()["procs"]))

    def test_h0_new_spells_have_no_aspect_bit_or_old_steady_bit(self):
        self.assertClean(check_h0_new_spells(_data()["rows_by_id"]))

    def test_steady_shot_mask(self):
        self.assertClean(check_steady_shot(_data()["rows_by_id"]))

    def test_b13_repoints(self):
        self.assertClean(check_b13_repoints(_data()["rows_by_id"]))

    def test_b13_glaive_strips(self):
        self.assertClean(check_b13_glaive_strips(_data()["rows_by_id"]))

    def test_b13_spell_proc_rekeys(self):
        self.assertClean(check_b13_spell_procs(_data()["procs"]))

    def test_stock_rows_keep_stock_class_set(self):
        self.assertClean(check_class_set_matches_stock(_data()["rows_by_id"], _data()["stock"]))


# ---- negative fixtures: every check must fire on a minimal bad input ---------------------------------------

def _row(spell_id=1, **cols) -> dict:
    return {"ID": spell_id, **cols}


class HunterGateNegativeTest(unittest.TestCase):
    def test_family_zero_spellmod_is_caught(self):
        row = _row(EffectAura_1=107, SpellClassSet=0, EffectSpellClassMaskA_1=1)
        self.assertEqual(len(check_spellmod_scoping([row])), 1)

    def test_all_zero_spellmod_mask_is_caught(self):
        row = _row(EffectAura_2=108, SpellClassSet=9)
        self.assertEqual(len(check_spellmod_scoping([row])), 1)

    def test_scoped_hunter_spellmod_passes(self):
        row = _row(EffectAura_2=108, SpellClassSet=9, EffectSpellClassMaskB_3=0x20000000)
        self.assertEqual(check_spellmod_scoping([row, _row(2, EffectAura_1=4, SpellClassSet=0)]), [])

    def test_proc_with_wrong_family_is_caught(self):
        self.assertEqual(len(check_proc_family([{"SpellId": 5, "SpellFamilyName": 0, "SpellFamilyMask0": 4}])), 1)
        self.assertEqual(check_proc_family([{"SpellId": 5, "SpellFamilyName": 9, "SpellFamilyMask0": 4}]), [])

    def test_pet_bit_in_custom_effect_mask_is_caught(self):
        row = _row(200500, EffectSpellClassMaskA_2=0x10000000)
        self.assertEqual(len(check_no_pet_bit_reader([row], [])), 1)
        # stock ids are out of scope
        self.assertEqual(check_no_pet_bit_reader([_row(100, EffectSpellClassMaskA_2=0x10000000)], []), [])

    def test_pet_bit_in_spell_proc_mask_is_caught(self):
        self.assertEqual(len(check_no_pet_bit_reader([], [{"SpellId": 9, "SpellFamilyMask1": 0x10000000}])), 1)

    def test_aspect_bit_on_new_spell_is_caught(self):
        rows = {201600: _row(201600, SpellClassMask_1=0x80000)}
        self.assertEqual(len(check_h0_new_spells(rows)), 1)

    def test_d1_0x1_reader_on_new_spell_is_caught(self):
        # the "d1 0x1 reader" fixture: an effect mask that still reads the old Steady Shot bit
        rows = {201603: _row(201603, EffectSpellClassMaskA_2=0x1)}
        self.assertEqual(len(check_h0_new_spells(rows)), 1)

    def test_steady_shot_without_new_bit_or_with_old_bit_is_caught(self):
        self.assertEqual(len(check_steady_shot({STEADY_SHOT_ID: _row(STEADY_SHOT_ID, SpellClassMask_2=1)})), 2)
        ok = {STEADY_SHOT_ID: _row(STEADY_SHOT_ID, SpellClassMask_3=0x20000000)}
        self.assertEqual(check_steady_shot(ok), [])

    def test_unrepointed_b13_effect_is_caught(self):
        # Serpent Sting 1978 effect 2 (letter B) still reading d1 0x1, and a stale raw twin that wins
        rows = {1978: _row(1978, EffectSpellClassMaskB_2=0x88820101, EffectSpellClassMaskB_3=0x2003c201)}
        self.assertEqual(len(check_b13_repoints(rows)), 1)
        rows = {1978: _row(1978, EffectSpellClassMaskB_2=0x88820100, EffectSpellClassMaskB_3=0x3c201)}
        self.assertEqual(len(check_b13_repoints(rows)), 1)
        # right dwords on the wrong letter (effect 1 instead of 2) must still fail
        rows = {1978: _row(1978, EffectSpellClassMaskA_2=0x88820100, EffectSpellClassMaskA_3=0x2003c201)}
        self.assertEqual(len(check_b13_repoints(rows)), 1)  # B has no d2 bit

    def test_stale_raw_twin_on_built_row_is_caught(self):
        # Real build_spell_row: the raw_overrides twin is applied last and wins, so a stale one fails. (19419, an
        # orphaned Efficiency rank: S2a turns 19419-19418 eff0 into a DUMMY, so they left B13_REPOINTS.)
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        entry = {"id": 19419, "name": "x", "effect1": {"type": 6, "apply_aura": 107},
                 "raw_overrides": {"SpellClassSet": 9, "EffectSpellClassMaskA_2": 0x88801081,
                                   "EffectSpellClassMaskA_3": 0x20000001}}
        row = build.build_spell_row(entry, ReuseContext({}, ids_cfg))
        self.assertEqual(len(check_b13_repoints({19419: row})), 1)
        entry["raw_overrides"]["EffectSpellClassMaskA_2"] = 0x88801080
        row = build.build_spell_row(entry, ReuseContext({}, ids_cfg))
        self.assertEqual(check_b13_repoints({19419: row}), [])
        self.assertEqual(check_spellmod_scoping([row]), [])

    def test_glaive_bit_left_on_strip_row_is_caught(self):
        rows = {56333: _row(56333, EffectSpellClassMaskB_3=0x240)}
        self.assertEqual(len(check_b13_glaive_strips(rows)), 1)
        self.assertEqual(check_b13_glaive_strips({56333: _row(56333, EffectSpellClassMaskB_3=0x200)}), [])

    def test_wrong_rekeyed_spell_proc_is_caught(self):
        stale = {"SpellId": -53290, "SpellFamilyMask0": 0x800, "SpellFamilyMask1": 1, "SpellFamilyMask2": 0x200}
        self.assertEqual(len(check_b13_spell_procs([stale])), 1)
        good = {"SpellId": -53290, "SpellFamilyMask0": 0x800, "SpellFamilyMask1": 0, "SpellFamilyMask2": 0x20000200}
        self.assertEqual(check_b13_spell_procs([good]), [])

    def test_class_set_repeated_differently_from_stock_is_caught(self):
        rows = {1978: _row(1978, SpellClassSet=0)}
        stock = {1978: _row(1978, SpellClassSet=9)}
        self.assertEqual(len(check_class_set_matches_stock(rows, stock)), 1)
        self.assertEqual(check_class_set_matches_stock({1978: _row(1978, SpellClassSet=9)}, stock), [])


if __name__ == "__main__":
    unittest.main()
