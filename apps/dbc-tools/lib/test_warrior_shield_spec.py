"""
Shield Specialization proc guard (tank-sim STAGE SHIELDSPEC; bugs-and-fixes "Shield Specialization never generated rage").

Ranks 200031 / 200032 / 200033 shipped with `ProcTypeMask 87376` (0x15550: DONE bits only) and no `spell_proc` row, so the
aura procced off the warrior's own casts and never off a block, dodge or parry. This loads the real warrior DSL
(source/classes/warrior/) and asserts the fix stays:

- the DBC ProcTypeMask holds only TAKEN melee / ranged bits (0x2A8, the stock 12298 mask), no DONE bit;
- each rank declares a positive-key `spell_proc` row: TAKEN melee / ranged flags, HitMask dodge | parry | block (0x70, the
  stock -12298 / Iron Temper -29593 value), no phase / family / school restriction, Chance 0 (= the rank's DBC ProcChance,
  33 / 66 / 100), no ICD;
- the aura still triggers 23602 (the 5-rage energize) and ProcChance is 33 / 66 / 100.

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_warrior_shield_spec.py -q
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import dbcfmt, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
WARRIOR_DIR = TOOL_ROOT / "source" / "classes" / "warrior"

SHIELD_SPEC_RANKS = {200031: 33, 200032: 66, 200033: 100}   # id -> ProcChance
ENERGIZE_RAGE_TRIGGER = 23602
AURA_PROC_TRIGGER_SPELL = 42

PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK = 0x8
PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS = 0x20
PROC_FLAG_TAKEN_RANGED_AUTO_ATTACK = 0x80
PROC_FLAG_TAKEN_SPELL_RANGED_DMG_CLASS = 0x200
TAKEN_ATTACK_MASK = (
    PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK | PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS
    | PROC_FLAG_TAKEN_RANGED_AUTO_ATTACK | PROC_FLAG_TAKEN_SPELL_RANGED_DMG_CLASS
)   # 0x2A8, also the stock Shield Specialization 12298 ProcTypeMask
PROC_HIT_DODGE = 0x10
PROC_HIT_PARRY = 0x20
PROC_HIT_BLOCK = 0x40   # partial or full block (DamageInfo sets it whenever blocked_amount > 0)
DEFENSIVE_HIT_MASK = PROC_HIT_DODGE | PROC_HIT_PARRY | PROC_HIT_BLOCK   # 112

_CACHE: dict = {}


def warrior_package():
    if not _CACHE:
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        spell_table_index = spell_tables.load_spell_table_index()
        _CACHE["reg"] = registry.load_class_package(
            WARRIOR_DIR, ids_cfg=ids_cfg, trainer_index=trainer_state.load_trainer_index(),
            existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
            shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
            live_data=spell_tables.load_dsl_live_data(),  # W0a: warrior_shared.py overrides a live SLA row
        )
    return _CACHE["reg"]


def check_shield_spec(entries: list[dict], procs: list[dict]) -> list[str]:
    """Problems with the Shield Specialization ranks, as strings (empty = fine)."""
    by_id = {e["id"]: e for e in entries}
    procs_by_id: dict[int, list[dict]] = {}
    for row in procs:
        procs_by_id.setdefault(int(row["SpellId"]), []).append(row)
    problems = []
    for spell_id, chance in SHIELD_SPEC_RANKS.items():
        entry = by_id.get(spell_id)
        if entry is None:
            problems.append(f"{spell_id}: not declared")
            continue
        raw = entry.get("raw_overrides") or {}
        mask = int(raw.get("ProcTypeMask", 0))
        if mask == 0 or mask & ~TAKEN_ATTACK_MASK:
            problems.append(f"{spell_id}: ProcTypeMask {mask:#x} must be a non-empty subset of the TAKEN attack bits "
                            f"{TAKEN_ATTACK_MASK:#x} (a DONE bit procs off the warrior's own casts)")
        if int(raw.get("ProcChance", 0)) != chance:
            problems.append(f"{spell_id}: ProcChance {raw.get('ProcChance')} != {chance}")
        triggers = [
            eff for key in ("effect1", "effect2", "effect3")
            if (eff := entry.get(key)) is not None and eff.get("apply_aura") == AURA_PROC_TRIGGER_SPELL
        ]
        if [eff.get("trigger_spell") for eff in triggers] != [ENERGIZE_RAGE_TRIGGER]:
            problems.append(f"{spell_id}: must have one PROC_TRIGGER_SPELL effect for {ENERGIZE_RAGE_TRIGGER}")
        rows = procs_by_id.get(spell_id, [])
        if len(rows) != 1:
            problems.append(f"{spell_id}: expected exactly one spell_proc row, found {len(rows)}")
            continue
        row = rows[0]
        flags = int(row["ProcFlags"])
        if flags == 0 or flags & ~TAKEN_ATTACK_MASK:
            problems.append(f"{spell_id}: spell_proc ProcFlags {flags:#x} must be a non-empty subset of {TAKEN_ATTACK_MASK:#x}")
        if int(row["HitMask"]) != DEFENSIVE_HIT_MASK:
            problems.append(f"{spell_id}: spell_proc HitMask {int(row['HitMask']):#x} != dodge|parry|block "
                            f"{DEFENSIVE_HIT_MASK:#x}")
        for field in ("SchoolMask", "SpellFamilyName", "SpellFamilyMask0", "SpellFamilyMask1", "SpellFamilyMask2",
                      "SpellTypeMask", "AttributesMask", "DisableEffectsMask", "Cooldown", "Charges"):
            if int(row[field]):
                problems.append(f"{spell_id}: spell_proc {field} {int(row[field]):#x} should be 0")
        if float(row["Chance"]) or float(row["ProcsPerMinute"]):
            problems.append(f"{spell_id}: spell_proc Chance/ProcsPerMinute must be 0 (use the DBC ProcChance {chance})")
    return problems


class ShieldSpecProcTest(unittest.TestCase):
    def test_real_package_is_clean(self):
        reg = warrior_package()
        self.assertEqual(check_shield_spec(reg.spells, reg.spell_procs), [])

    def test_gate_catches_the_original_bug(self):
        # Pre-fix shape: DONE-bit ProcTypeMask 87376 and no spell_proc row.
        entries = [
            {"id": sid, "raw_overrides": {"ProcTypeMask": 87376, "ProcChance": chance},
             "effect1": {"apply_aura": 51},
             "effect2": {"apply_aura": AURA_PROC_TRIGGER_SPELL, "trigger_spell": ENERGIZE_RAGE_TRIGGER}}
            for sid, chance in SHIELD_SPEC_RANKS.items()
        ]
        problems = check_shield_spec(entries, [])
        self.assertEqual(len(problems), 2 * len(SHIELD_SPEC_RANKS))
        self.assertTrue(all("ProcTypeMask" in p or "spell_proc row" in p for p in problems))

    def test_gate_catches_a_wrong_hit_mask(self):
        entries = [
            {"id": sid, "raw_overrides": {"ProcTypeMask": TAKEN_ATTACK_MASK, "ProcChance": chance},
             "effect2": {"apply_aura": AURA_PROC_TRIGGER_SPELL, "trigger_spell": ENERGIZE_RAGE_TRIGGER}}
            for sid, chance in SHIELD_SPEC_RANKS.items()
        ]
        procs = [
            {"SpellId": sid, "ProcFlags": TAKEN_ATTACK_MASK, "HitMask": PROC_HIT_BLOCK, "SchoolMask": 0,
             "SpellFamilyName": 0, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0, "SpellFamilyMask2": 0,
             "SpellTypeMask": 0, "AttributesMask": 0, "DisableEffectsMask": 0, "Cooldown": 0, "Charges": 0,
             "Chance": 0.0, "ProcsPerMinute": 0.0}
            for sid in SHIELD_SPEC_RANKS
        ]
        problems = check_shield_spec(entries, procs)
        self.assertEqual(len(problems), len(SHIELD_SPEC_RANKS))
        self.assertTrue(all("HitMask" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
