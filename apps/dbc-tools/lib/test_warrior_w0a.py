"""
Warrior W0a data gate (warrior-rework W0a-HANDOFF WP-A/B table row A4, W0a-WP-BRIEF rulings, W0a-0VERIFY items 2e / 3).

Loads the real warrior DSL package (source/classes/warrior/) plus the legacy CSV rows W0a touches (npc.csv) and asserts
on the BUILT rows (stock base + DSL + raw_overrides via `build.build_spell_row`, the way generate.py pairs them), so a
stale raw twin that wins fails here too. Every check is a pure function over built rows / package tables; the negative
tests prove each one can fail.

  1. Heroic Strike / Cleave / Slam: attr0 0x4 clear, GCD 133/1500, percent effect (31) before the flat effect (58),
     flat part = sp_potency 12/12/18/17/18 direct T 1500 (31/31/46/43/46 at level 60, balance 2026-10-30),
     Cleave chain 2 on both effects; the D4 percents.
  2. Slam: instant, RecoveryTime 6000, no DUMMY effect, no -1464 binding (unbind declared).
  3. Mortal Strike effect order, Category 0 / 6000 / SpellLevel 20; Bloodthirst 0 / 6000 (S3 D9: was 4000);
     Overpower 0 / no cooldown and
     FINISHING_MOVE (AttributesEx 0x100000) CLEAR (W0b D3: the charge aura replaces the combo-point need);
     Revenge 0 / 3000.
  4. D9 stance zero list (22 ids) and the untouched ids (28880, the removed three, talent passives, ranks).
  5. Battle Stance aura 213 (+10), no aura 280; Stance Mastery 12678 (149 / icon 139 / family 4 / SLA skill 26
     acquire 2); 8616 teaches 2458 only.
  6. Rend (9 potency / 3 s tick, -772 unbound), Thunder Clap 30 s, Commanding Shout (113 at 22, 297 at 60, MaxLevel 60).
  7. Moved learn levels and level-60 values; trainer rows (D3); the consts; no FORBIDDEN_* bit; no "Capstone"; the spike
     ids declared nowhere.
  8. The rage worked example (D12, D22) as a pure-Python reference at the live m 1.35, with the spell-haste factor.

Run: cd apps/dbc-tools && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3 -m pytest lib/test_warrior_w0a.py -q
"""

from __future__ import annotations

import copy
import importlib.util
import math
import re
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
WARRIOR_DIR = TOOL_ROOT / "source" / "classes" / "warrior"
sys.path.insert(0, str(TOOL_ROOT / "source" / "classes"))
_masks_spec = importlib.util.spec_from_file_location("_warrior_masks", WARRIOR_DIR / "_masks.py")
m = importlib.util.module_from_spec(_masks_spec)
_masks_spec.loader.exec_module(m)

# effect types
SCHOOL_DAMAGE, DUMMY, APPLY_AURA, WEAPON_PERCENT, WEAPON_DAMAGE, NORMALIZED_WEAPON = 2, 3, 6, 31, 58, 121
ATTR0_NEXT_SWING = 0x4
ATTR1_FINISHING_MOVE = 0x100000
ATTR3_SUPPRESS_PROCS = 0x30000
SPELLS_ONLY_CSV = {355, 7922, 64380, 28880, 7887, 11584, 50783}

HS, CLEAVE, SLAM, OVERPOWER, MS, BT, REVENGE = 78, 845, 1464, 7384, 12294, 23881, 6572
REND, THUNDER_CLAP, COMMANDING_SHOUT, PUMMEL, SPELL_REFLECTION = 772, 6343, 469, 6552, 23920
SHATTERING_THROW, HEROIC_THROW = 64382, 57755
DEFENSIVE, BATTLE, BERSERKER, BERSERKER_PASSIVE, STANCE_MASTERY, PATH = 71, 2457, 2458, 7381, 12678, 8616
W0A_IDS = (HS, CLEAVE, SLAM, OVERPOWER, MS, BT, REVENGE, REND, THUNDER_CLAP, COMMANDING_SHOUT, PUMMEL, SPELL_REFLECTION,
           SHATTERING_THROW, HEROIC_THROW, DEFENSIVE, BATTLE, BERSERKER, BERSERKER_PASSIVE, STANCE_MASTERY, PATH)

# D4 percents (WP-BRIEF ruling 1): weapon_potency P -> stored bp P - 1 (die 1 adds the 1 back)
# Warrior balance 2026-10-30 (user, five rounds compounded): HS x1.3 x1.3 x0.9 x0.8, Cleave x1.2, Slam to 200%,
# MS x1.5 x1.4 x0.8 x1.1 x0.95, Overpower x1.5 x1.4 x0.8, on both parts
PERCENTS = {HS: 183, CLEAVE: 144, SLAM: 200, MS: 228, OVERPOWER: 168}
# strike -> (percent effect index, flat effect index, flat carrier type)
STRIKE_SHAPE = {HS: (1, 2, WEAPON_DAMAGE), CLEAVE: (1, 2, WEAPON_DAMAGE), SLAM: (1, 2, WEAPON_DAMAGE),
                MS: (2, 3, NORMALIZED_WEAPON), OVERPOWER: (1, 2, NORMALIZED_WEAPON)}
FLAT_POT = {HS: 12, CLEAVE: 12, SLAM: 18, OVERPOWER: 17, MS: 18}
FLAT_L60 = {HS: 31, CLEAVE: 31, SLAM: 46, OVERPOWER: 43, MS: 46}
FLAT_L22 = {HS: 5, CLEAVE: 5, SLAM: 16, OVERPOWER: 6, MS: 7}

# WP-BRIEF ruling 2 / 0VERIFY 2e: ShapeshiftMask -> 0
ZERO_LIST = (72, 100, 355, 676, 772, 871, 1680, 1715, 1719, 2565, 3411, 5308, 6343, 6552, 6572, 7384, 7922, 12328,
             23920, 34428, 64380, 64382)
# left alone: id -> stock mask (built value today)
UNTOUCHED = {28880: 2164260864, 694: 196608, 20230: 65536, 20252: 262144, 12295: 131072, 7887: 65536, 11584: 65536,
             11585: 65536, 12301: 0, 29759: 262144}
# 12301 (Improved Bloodrage r1) is 0 since S1 D19 (12818 too): 204774 carries the stance gate for its damage-taken half

# D3 trainer rows: (trainer, spell) -> ReqLevel; the last five are W0b's (D17: Victory Rush, Intervene, Heroic Leap,
# Enraged Regeneration, Skull Banner, trainer 200 only; test_warrior_w0b.py pins them too)
TRAINER_ROWS = {(200, 469): 22, (200, 23920): 44, (200, 64382): 52, (200, 57755): 60, (200, 674): 10, (200, 845): 14,
                (200, 6552): 16, (200, 2458): 16, (201, 2458): 16,
                (200, 34428): 8, (200, 3411): 30, (200, 204400): 38, (200, 55694): 56, (200, 204405): 60}
UNTRAINED = {(200, 694), (200, 20230), (200, 20252), (201, 20252)}
# moved SpellLevel (== BaseLevel for the potency / modified rows)
MOVED_LEVELS = {845: 14, 6552: 16, 23920: 44, 64382: 52, 57755: 60, 469: 22, 2458: 16, 12294: 20}

CONSTS = {"RAGE_K_60": (0.43, "float"), "RAGE_M_60": (1.35, "float"), "RAGE_MH_SPEED_FACTOR": (3.5, "float"),
          "RAGE_OH_SPEED_FACTOR": (0.875, "float"), "RAGE_SPEED_FIXED_POINT": (100, "uint32"),
          "RAGE_STANCE_MASTERY_POINTS": (149, "int32")}
# declarations only (`id=204880`, `spell_id=`, `entry=`): a comment such as "the P0 204875 shape" is not a declaration
SPIKE_RE = re.compile(r"\b(?:spell_)?id\s*=\s*(20(?:4869|487\d|488\d|489\d))\b")
SPIKE_OTHER = {"spell_group": (1305,), "sla": (30868, 30869), "creature": (300388, 300389), "talent": (60488, 60489)}


def _i(row: dict, col: str) -> int:
    return int(row.get(col) or 0)


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def f32(x: float) -> float:
    return struct.unpack("f", struct.pack("f", x))[0]


def calc_value(row: dict, effect: int, level: int) -> int:
    """SpellInfo::CalcValue for a die-sides-0/1 effect (0VERIFY item 3): bp + int(levels x ppl) + (1 when die 1)."""
    base, spell_level, max_level = _i(row, "BaseLevel"), _i(row, "SpellLevel"), _i(row, "MaxLevel")
    lvl = level
    if max_level > 0 and lvl > max_level:
        lvl = max_level
    if lvl < base:
        lvl = base
    ppl = f32(float(row.get(f"EffectRealPointsPerLevel_{effect}") or 0.0))
    die = _i(row, f"EffectDieSides_{effect}")
    scaled = int(f32((lvl - max(base, spell_level)) * ppl))
    return _i(row, f"EffectBasePoints_{effect}") + scaled + (1 if die == 1 else 0)


# ---- checks (pure: take built rows / package tables, return problem strings) ------------------------------------

def check_instant_gcd(rows: dict[int, dict]) -> list[str]:
    bad = []
    for sid in (HS, CLEAVE, SLAM):
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
            continue
        if _u32(r.get("Attributes")) & ATTR0_NEXT_SWING:
            bad.append(f"{sid}: Attributes {_u32(r.get('Attributes')):#x} still has attr0 0x4 (on next swing)")
        if (_i(r, "StartRecoveryCategory"), _i(r, "StartRecoveryTime")) != (133, 1500):
            bad.append(f"{sid}: GCD {r.get('StartRecoveryCategory')}/{r.get('StartRecoveryTime')}, expected 133/1500")
        if _i(r, "CastingTimeIndex") != 1:
            bad.append(f"{sid}: CastingTimeIndex {r.get('CastingTimeIndex')!r}, expected 1 (instant)")
    return bad


def check_strike_shape(rows: dict[int, dict], entries: dict[int, dict]) -> list[str]:
    bad = []
    for sid, (pe, fe, carrier) in STRIKE_SHAPE.items():
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
            continue
        if _i(r, f"Effect_{pe}") != WEAPON_PERCENT:
            bad.append(f"{sid}: effect {pe} type {r.get(f'Effect_{pe}')!r}, "
                       f"expected {WEAPON_PERCENT} (weapon percent first)")
        if _i(r, f"Effect_{fe}") != carrier:
            bad.append(f"{sid}: effect {fe} type {r.get(f'Effect_{fe}')!r}, expected the flat carrier {carrier}")
        if pe >= fe:
            bad.append(f"{sid}: percent effect {pe} is not before the flat effect {fe}")
        if _i(r, f"EffectBasePoints_{pe}") + 1 != PERCENTS[sid]:
            bad.append(f"{sid}: percent {_i(r, f'EffectBasePoints_{pe}') + 1}, expected {PERCENTS[sid]}")
        if float(r.get(f"EffectRealPointsPerLevel_{pe}") or 0) != 0:
            bad.append(f"{sid}: percent effect {pe} carries a per-level slope")
        if calc_value(r, fe, 60) != FLAT_L60[sid]:
            bad.append(f"{sid}: flat part at level 60 is {calc_value(r, fe, 60)}, expected {FLAT_L60[sid]}")
        if calc_value(r, fe, 22) != FLAT_L22[sid]:
            bad.append(f"{sid}: flat part at level 22 is {calc_value(r, fe, 22)}, expected {FLAT_L22[sid]}")
        e = entries.get(sid)
        pot = (e or {}).get(f"effect{fe}", {}) and e[f"effect{fe}"].get("_potency")
        if not pot:
            bad.append(f"{sid}: flat effect {fe} is not a potency effect")
        else:
            if pot.get("kind") != "direct" or pot.get("total_potency") != FLAT_POT[sid] or pot.get("t_seconds") != 1.5:
                bad.append(f"{sid}: flat potency {pot.get('kind')}/{pot.get('total_potency')}/"
                           f"T {pot.get('t_seconds')}, expected direct/{FLAT_POT[sid]}/T 1.5")
            if float(pot.get("ap_coefficient") or 0) != 0:
                bad.append(f"{sid}: flat potency carries an attack-power coefficient")
        if _i(r, f"Effect_{fe + 1}") != 0 and fe < 3:
            bad.append(f"{sid}: effect {fe + 1} should be empty")
    return bad


def check_cleave_chain(rows: dict[int, dict]) -> list[str]:
    r = rows.get(CLEAVE)
    if r is None:
        return [f"{CLEAVE}: not built"]
    bad = [f"{CLEAVE}: effect {i} EffectChainTargets {r.get(f'EffectChainTargets_{i}')!r}, expected 2" for i in (1, 2)
           if _i(r, f"EffectChainTargets_{i}") != 2]
    for sid in (HS, SLAM):
        if rows.get(sid) and any(_i(rows[sid], f"EffectChainTargets_{i}") for i in (1, 2)):
            bad.append(f"{sid}: carries chain targets")
    return bad


IMPROVED_CLEAVE = {12329: 4, 12950: 9, 20496: 14}  # Fury Q17 (PLAN 1E): 5/10/15% total Cleave damage
SPELLMOD_DAMAGE, CLEAVE_MASK_A = 0, 0x400000


def check_improved_cleave(rows: dict[int, dict]) -> list[str]:
    """W0a CODE-REVIEW M1: SPELLMOD_ALL_EFFECTS would also scale Cleave's weapon percent (effect 1)."""
    bad = []
    for sid, bp in IMPROVED_CLEAVE.items():
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
            continue
        got = (_i(r, "EffectAura_1"), _i(r, "EffectMiscValue_1"), _i(r, "EffectBasePoints_1"),
               _u32(r.get("EffectSpellClassMaskA_1")))
        if got != (108, SPELLMOD_DAMAGE, bp, CLEAVE_MASK_A):
            bad.append(f"{sid}: (aura, misc, bp, mask A) {got}, expected (108, 0, {bp}, {CLEAVE_MASK_A:#x})")
    return bad

def check_slam(rows: dict[int, dict], script_removals: list[dict], script_names: list[dict]) -> list[str]:
    r = rows.get(SLAM)
    if r is None:
        return [f"{SLAM}: not built"]
    bad = []
    if _i(r, "CastingTimeIndex") != 1:
        bad.append(f"CastingTimeIndex {r.get('CastingTimeIndex')!r}, expected 1 (instant)")
    if _i(r, "RecoveryTime") != 6000:
        bad.append(f"RecoveryTime {r.get('RecoveryTime')!r}, expected 6000")
    if _i(r, "InterruptFlags") != 0:
        bad.append(f"InterruptFlags {r.get('InterruptFlags')!r}, expected 0")
    if _u32(r.get("AttributesEx3")) & ATTR3_SUPPRESS_PROCS:
        bad.append(f"AttributesEx3 {_u32(r.get('AttributesEx3')):#x} keeps the dummy's suppress-procs bits (0x30000)")
    for i in (1, 2, 3):
        if _i(r, f"Effect_{i}") == DUMMY or _i(r, f"EffectAura_{i}") == 4:
            bad.append(f"effect {i} is a DUMMY")
    if not any(int(x["spell_id"]) == -SLAM and x["ScriptName"] == "spell_warr_slam" for x in script_removals):
        bad.append("unbind_script(-1464, 'spell_warr_slam') is not declared")
    if any(int(x["spell_id"]) == -SLAM for x in script_names):
        bad.append("a -1464 spell_script_names binding is still declared")
    return [f"{SLAM}: {b}" for b in bad]


def check_categories(rows: dict[int, dict]) -> list[str]:
    bad = []
    want = {MS: (0, 6000, 0), BT: (0, 6000, 0), OVERPOWER: (0, 0, 0), REVENGE: (0, 3000, 0)}
    for sid, (cat, rec, crec) in want.items():
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
            continue
        got = (_i(r, "Category"), _i(r, "RecoveryTime"), _i(r, "CategoryRecoveryTime"))
        if got != (cat, rec, crec):
            bad.append(f"{sid}: Category/RecoveryTime/CategoryRecoveryTime {got}, expected {(cat, rec, crec)}")
    op = rows.get(OVERPOWER)
    if op is not None and _u32(op.get("AttributesEx")) & ATTR1_FINISHING_MOVE:
        bad.append(f"{OVERPOWER}: AttributesEx {_u32(op.get('AttributesEx')):#x} still has FINISHING_MOVE 0x100000 "
                   "(W0b D3: Overpower needs a charge, not combo points)")
    ms = rows.get(MS)
    if ms is not None:
        if _i(ms, "ManaCost") != 250:
            bad.append(f"{MS}: ManaCost {ms.get('ManaCost')!r}, expected 250 (25 rage, Arms Q3 fallback)")
        if (_i(ms, "SpellLevel"), _i(ms, "BaseLevel")) != (20, 20):
            bad.append(f"{MS}: SpellLevel/BaseLevel {ms.get('SpellLevel')}/{ms.get('BaseLevel')}, expected 20/20")
        if (_i(ms, "Effect_1"), _i(ms, "EffectAura_1")) != (APPLY_AURA, 118):
            bad.append(f"{MS}: effect 1 is not APPLY_AURA 118 (healing taken)")
        if (_i(ms, "Effect_2"), _i(ms, "Effect_3")) != (WEAPON_PERCENT, NORMALIZED_WEAPON):
            bad.append(f"{MS}: effects 2/3 are {ms.get('Effect_2')}/{ms.get('Effect_3')}, "
                       "expected percent 31 then flat 121")
    return bad


def check_zero_list(rows: dict[int, dict]) -> list[str]:
    bad = []
    for sid in ZERO_LIST:
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
        elif _u32(r.get("ShapeshiftMask")) != 0:
            bad.append(f"{sid}: ShapeshiftMask {_u32(r.get('ShapeshiftMask')):#x}, expected 0")
    for sid, mask in UNTOUCHED.items():
        r = rows.get(sid)
        if r is not None and _u32(r.get("ShapeshiftMask")) != mask:
            bad.append(f"{sid}: ShapeshiftMask {_u32(r.get('ShapeshiftMask')):#x}, expected the untouched {mask:#x}")
    r = rows.get(28880)
    if r is not None and _u32(r.get("ShapeshiftExclude")) != 0x8000000:
        bad.append(f"28880: ShapeshiftExclude {_u32(r.get('ShapeshiftExclude')):#x}, expected 0x8000000")
    return bad


def check_battle_stance(rows: dict[int, dict]) -> list[str]:
    r = rows.get(BATTLE)
    if r is None:
        return [f"{BATTLE}: not built"]
    bad = []
    auras = [(i, _i(r, f"EffectAura_{i}")) for i in (1, 2, 3)]
    if any(a == 280 for _i_, a in auras):
        bad.append("still carries aura 280 (armor penetration)")
    e213 = [i for i, a in auras if a == 213]
    if len(e213) != 1:
        bad.append(f"expected one aura 213 effect, found {len(e213)}")
    else:
        i = e213[0]
        if _i(r, f"Effect_{i}") != APPLY_AURA:
            bad.append("aura 213 effect is not APPLY_AURA")
        if calc_value(r, i, 60) != 10:
            bad.append(f"aura 213 built amount {calc_value(r, i, 60)}, expected +10")
    if _i(r, "EffectAura_1") != 36:
        bad.append("effect 1 is not the shapeshift aura 36")
    return [f"{BATTLE}: {b}" for b in bad]


def check_stance_mastery(rows: dict[int, dict], slas: list[dict], consts: list[dict]) -> list[str]:
    r = rows.get(STANCE_MASTERY)
    if r is None:
        return [f"{STANCE_MASTERY}: not built"]
    bad = []
    pts = {c["name"]: c["value"] for c in consts}.get("RAGE_STANCE_MASTERY_POINTS")
    if _i(r, "EffectBasePoints_1") != pts or pts != 149:
        bad.append(f"EffectBasePoints_1 {r.get('EffectBasePoints_1')!r} vs RAGE_STANCE_MASTERY_POINTS {pts!r} (149)")
    if _i(r, "SpellIconID") != 139:
        bad.append(f"SpellIconID {r.get('SpellIconID')!r}, expected 139 (the shapeshift rage clamp keys on it)")
    if _i(r, "SpellClassSet") != 4:
        bad.append(f"SpellClassSet {r.get('SpellClassSet')!r}, expected 4")
    mine = [s for s in slas if int(s["spell_id"]) == STANCE_MASTERY]
    if len(mine) != 1:
        bad.append(f"{len(mine)} SkillLineAbility rows, expected 1")
    else:
        s = mine[0]
        if (int(s["id"]), int(s["skill_line"]), int(s.get("acquire_method") or 0), int(s.get("class_mask") or 0)) != \
                (15513, 26, 2, 1):
            bad.append(f"SLA id/skill/acquire/class = {s['id']}/{s['skill_line']}/{s.get('acquire_method')}/"
                       f"{s.get('class_mask')}, expected 15513/26/2/1")
    return [f"{STANCE_MASTERY}: {b}" for b in bad]


def check_path_of_the_berserker(rows: dict[int, dict]) -> list[str]:
    r = rows.get(PATH)
    if r is None:
        return [f"{PATH}: not built"]
    learned = [(_i(r, f"Effect_{i}"), _i(r, f"EffectTriggerSpell_{i}")) for i in (1, 2, 3) if _i(r, f"Effect_{i}")]
    bad = []
    if learned != [(36, BERSERKER)]:
        bad.append(f"effects {learned}, expected only LEARN_SPELL 2458")
    if "Intercept" in str(r.get("Description_Lang_enUS") or ""):
        bad.append("Description still mentions Intercept")
    return [f"{PATH}: {b}" for b in bad]


def check_rend(rows: dict[int, dict], entries: dict[int, dict], script_removals: list[dict],
               script_names: list[dict]) -> list[str]:
    r, e = rows.get(REND), entries.get(REND)
    if r is None or e is None:
        return [f"{REND}: not built"]
    bad = []
    pot = (e.get("effect1") or {}).get("_potency") or {}
    if (pot.get("kind"), pot.get("total_potency"), pot.get("t_seconds")) != ("periodic", 11.23, 3.0):
        bad.append(f"potency {pot.get('kind')}/{pot.get('total_potency')}/T {pot.get('t_seconds')}, "
                   "expected periodic/11.23/T 3")
    if not float(pot.get("ap_coefficient") or 0):
        bad.append("no attack-power coefficient")
    if (_i(r, "EffectAura_1"), _i(r, "EffectAuraPeriod_1")) != (3, 3000):
        bad.append(f"aura/period {r.get('EffectAura_1')}/{r.get('EffectAuraPeriod_1')}, expected 3 / 3000")
    if calc_value(r, 1, 60) != 60 or calc_value(r, 1, 22) != 9:
        bad.append(f"per-tick value {calc_value(r, 1, 22)} at 22 / {calc_value(r, 1, 60)} at 60, expected 9 / 60")
    if not any(int(x["spell_id"]) == -REND and x["ScriptName"] == "spell_warr_rend" for x in script_removals):
        bad.append("unbind_script(-772, 'spell_warr_rend') is not declared")
    if any(int(x["spell_id"]) == -REND for x in script_names):
        bad.append("a -772 spell_script_names binding is still declared")
    return [f"{REND}: {b}" for b in bad]


def check_thunder_clap(rows: dict[int, dict], entries: dict[int, dict], index_30s: int) -> list[str]:
    r, e = rows.get(THUNDER_CLAP), entries.get(THUNDER_CLAP)
    if r is None or e is None:
        return [f"{THUNDER_CLAP}: not built"]
    bad = []
    if e.get("duration_ms") != 30000:
        bad.append(f"duration_ms {e.get('duration_ms')!r}, expected 30000")
    if _i(r, "DurationIndex") != index_30s:
        bad.append(f"DurationIndex {r.get('DurationIndex')!r}, expected the 30 s row {index_30s}")
    return [f"{THUNDER_CLAP}: {b}" for b in bad]


def check_commanding_shout(rows: dict[int, dict]) -> list[str]:
    r = rows.get(COMMANDING_SHOUT)
    if r is None:
        return [f"{COMMANDING_SHOUT}: not built"]
    bad = []
    for lvl, want in ((22, 113), (60, 297)):
        if calc_value(r, 1, lvl) != want:
            bad.append(f"value at level {lvl} is {calc_value(r, 1, lvl)}, expected {want}")
    if calc_value(r, 1, 70) != calc_value(r, 1, 60):
        bad.append("value keeps growing above MaxLevel 60")
    if _i(r, "MaxLevel") != 60:
        bad.append(f"MaxLevel {r.get('MaxLevel')!r}, expected 60")
    if (_i(r, "SpellLevel"), _i(r, "BaseLevel")) != (22, 22):
        bad.append(f"SpellLevel/BaseLevel {r.get('SpellLevel')}/{r.get('BaseLevel')}, expected 22/22")
    return [f"{COMMANDING_SHOUT}: {b}" for b in bad]


def check_moved_levels(rows: dict[int, dict]) -> list[str]:
    bad = []
    for sid, level in MOVED_LEVELS.items():
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
        elif (_i(r, "SpellLevel"), _i(r, "BaseLevel")) != (level, level):
            bad.append(f"{sid}: SpellLevel/BaseLevel {r.get('SpellLevel')}/{r.get('BaseLevel')}, "
                       f"expected {level}/{level}")
    # 0VERIFY item 3: non-potency moves change nothing; the two potency moves lower the flat to 11
    p, sr = rows.get(PUMMEL), rows.get(SPELL_REFLECTION)
    if p is not None and (float(p.get("EffectRealPointsPerLevel_1") or 0) != 0 or calc_value(p, 1, 60) != 0
                          or _i(p, "Effect_1") != 68):
        bad.append(f"{PUMMEL}: no longer a plain level-less effect 68 value 0")
    if sr is not None and (float(sr.get("EffectRealPointsPerLevel_1") or 0) != 0 or calc_value(sr, 1, 60) != 100
                           or _i(sr, "EffectAura_1") != 28):
        bad.append(f"{SPELL_REFLECTION}: level-60 value {calc_value(sr, 1, 60)}, expected 100 (aura 28, no slope)")
    for sid in (SHATTERING_THROW, HEROIC_THROW):
        r = rows.get(sid)
        if r is not None and calc_value(r, 1, 60) != 11:
            bad.append(f"{sid}: flat at level 60 is {calc_value(r, 1, 60)}, expected 11 (0VERIFY item 3)")
    return bad


def check_trainers(trainers: list[dict], removals: list[dict]) -> list[str]:
    bad = []
    have = {(int(t["TrainerId"]), int(t["SpellId"])): int(t["ReqLevel"]) for t in trainers}
    for key, level in TRAINER_ROWS.items():
        if key not in have:
            bad.append(f"trainer {key[0]} has no row for {key[1]}")
        elif have[key] != level:
            bad.append(f"trainer {key[0]} spell {key[1]}: ReqLevel {have[key]}, expected {level}")
    extra = set(have) - set(TRAINER_ROWS)
    if extra:
        bad.append(f"unexpected trainer rows {sorted(extra)}")
    for key in UNTRAINED:
        if key in have:
            bad.append(f"trainer {key[0]} still teaches removed spell {key[1]}")
    got = {(int(r["TrainerId"]), int(r["SpellId"])) for r in removals}
    if got != UNTRAINED:
        bad.append(f"untrain rows {sorted(got)}, expected {sorted(UNTRAINED)}")
    return bad


def check_consts(consts: list[dict]) -> list[str]:
    have = {c["name"]: (c["value"], c["cpp_type"]) for c in consts}
    return [f"const {n}: {have.get(n)!r}, expected {v!r}" for n, v in CONSTS.items() if have.get(n) != v]


def check_forbidden(rows: dict[int, dict]) -> list[str]:
    bad = []
    for sid, r in rows.items():
        if sid not in W0A_IDS:
            continue
        masks = [("SpellClassMask", tuple(_u32(r.get(f"SpellClassMask_{n}")) for n in (1, 2, 3)))]
        for i, letter in ((1, "A"), (2, "B"), (3, "C")):
            masks.append((f"effect {i}", tuple(_u32(r.get(f"EffectSpellClassMask{letter}_{n}")) for n in (1, 2, 3))))
        for label, (d0, d1, d2) in masks:
            hit = (d0 & m.FORBIDDEN_D0, d1 & m.FORBIDDEN_D1, d2 & m.FORBIDDEN_D2)
            if any(hit):
                bad.append(f"{sid}: {label} holds forbidden bits {tuple(hex(h) for h in hit)}")
    return bad


def check_no_capstone(rows: dict[int, dict]) -> list[str]:
    return [f"{sid}: {col} contains 'Capstone'" for sid, r in rows.items() if sid in W0A_IDS
            for col in ("Description_Lang_enUS", "AuraDescription_Lang_enUS")
            if "capstone" in str(r.get(col) or "").lower()]


def check_spike_ids(texts: dict[str, str], spell_ids, group_ids, sla_ids, creature_ids, talent_ids) -> list[str]:
    bad = [f"spell {sid} (spike) is declared" for sid in spell_ids if 204869 <= sid <= 204899]
    bad += [f"{name}: mentions a spike spell id {mt}" for name, t in texts.items() for mt in SPIKE_RE.findall(t)]
    bad += [f"spell_group {g} is declared" for g in group_ids if g in SPIKE_OTHER["spell_group"]]
    bad += [f"SkillLineAbility {g} is declared" for g in sla_ids if g in SPIKE_OTHER["sla"]]
    bad += [f"creature {g} is declared" for g in creature_ids if g in SPIKE_OTHER["creature"]]
    bad += [f"talent {g} is declared" for g in talent_ids if g in SPIKE_OTHER["talent"]]
    return bad


# ---- the D12 / D22 rage reference (pure Python; the C++ rounds the speed factor to hundredths) -------------------

def rage_conversion(level: int) -> float:
    """The stock `c` (Unit::RewardRage / Warrior::RageConversion), level <= 70 branch."""
    return 0.0091107836 * level * level + 3.225598133 * level + 4.2652911


def rage_speed_factor(swing_s: float, main_hand: bool, m_: float = 1.35, spell_haste: float = 0.0) -> int:
    """Hundredths, lround (half away from zero). `swing_s` is the HASTED swing time; D21/D22 multiply it by the
    spell-haste factor max(1, 1 + spell_haste) (the C++ reads 1 / UNIT_MOD_CAST_SPEED), so rage per second scales 1:1
    with spell haste (Bloodlust, haste rating) while an attack-speed-only haste does not. A slow never lowers it."""
    factor = swing_s * max(1.0, 1.0 + spell_haste) * (3.5 * m_ if main_hand else 0.875) * 100
    return math.floor(factor + 0.5)


def rage_dealt(level: int, damage: float, swing_s: float, *, main_hand: bool = True, crit: bool = False,
               stance_pct: float = 10.0, k: float = 0.43, m_: float = 1.35, fixed_point: int = 100,
               spell_haste: float = 0.0) -> float:
    factor = rage_speed_factor(swing_s, main_hand, m_, spell_haste) * (2 if crit else 1)
    c = rage_conversion(level)
    dealt = (k * 7.5 * damage / c + factor / fixed_point) / 2
    dealt = min(dealt, 15 * damage / c)
    return dealt * (1 + stance_pct / 100)


def rage_dealt_stock(level: int, damage: float, swing_s: float, *, main_hand: bool = True) -> float:
    factor = int(swing_s * (3.5 if main_hand else 1.75))
    c = rage_conversion(level)
    return min((7.5 * damage / c + factor) / 2, 15 * damage / c)


# ---- real data ----------------------------------------------------------------------------------------------

_CACHE: dict = {}


def _data():
    if not _CACHE:
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        spell_table_index = spell_tables.load_spell_table_index()
        creature_table_index = spell_tables.load_creature_table_index()
        package = registry.load_class_package(
            WARRIOR_DIR, ids_cfg=ids_cfg, trainer_index=trainer_state.load_trainer_index(),
            existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
            shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
            existing_creature_rows={int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")},
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.load_dsl_live_data(),
        )
        reuse = ReuseContext({}, ids_cfg)
        rows = {int(r["ID"]): r for r in (build.build_spell_row(e, reuse) for e in package.spells)}
        csv_entries = source.load_spells_csv(TOOL_ROOT / "source" / "spells")
        csv_rows = {}
        csv_ids = set()
        for e in csv_entries:
            sid = int(e.get("id", e.get("ID", 0)))
            csv_ids.add(sid)
            if sid in SPELLS_ONLY_CSV and sid not in rows:
                csv_rows[sid] = build.build_spell_row(e, reuse)
        texts = {}
        for pat in ("classes/**/*.py", "npcs/*.py", "spells/*.csv"):
            for p in sorted((TOOL_ROOT / "source").glob(pat)):
                texts[str(p.relative_to(TOOL_ROOT))] = p.read_text(encoding="utf-8", errors="replace")
        _CACHE.update(
            package=package, rows={**csv_rows, **rows}, dsl_rows=rows,
            entries={int(e["id"]): e for e in package.spells}, csv_ids=csv_ids, texts=texts,
            index_30s=reuse.duration_index(30000),
        )
    return _CACHE


class WarriorW0aDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_instant_gcd_strikes(self):
        self.assertClean(check_instant_gcd(_data()["rows"]))

    def test_strike_shape_and_percents(self):
        d = _data()
        self.assertClean(check_strike_shape(d["rows"], d["entries"]))

    def test_cleave_chain(self):
        self.assertClean(check_cleave_chain(_data()["rows"]))

    def test_improved_cleave(self):
        self.assertClean(check_improved_cleave(_data()["rows"]))

    def test_slam(self):
        p = _data()["package"]
        self.assertClean(check_slam(_data()["rows"], p.script_removals, p.spell_script_names))

    def test_categories_and_mortal_strike(self):
        self.assertClean(check_categories(_data()["rows"]))

    def test_stance_zero_list(self):
        self.assertClean(check_zero_list(_data()["rows"]))

    def test_battle_stance(self):
        self.assertClean(check_battle_stance(_data()["rows"]))

    def test_stance_mastery(self):
        d = _data()
        self.assertClean(check_stance_mastery(d["rows"], d["package"].skill_line_abilities, d["package"].consts))

    def test_path_of_the_berserker(self):
        self.assertClean(check_path_of_the_berserker(_data()["rows"]))

    def test_rend(self):
        d = _data()
        p = d["package"]
        self.assertClean(check_rend(d["rows"], d["entries"], p.script_removals, p.spell_script_names))

    def test_thunder_clap(self):
        d = _data()
        self.assertClean(check_thunder_clap(d["rows"], d["entries"], d["index_30s"]))

    def test_commanding_shout(self):
        self.assertClean(check_commanding_shout(_data()["rows"]))

    def test_moved_levels_and_values(self):
        self.assertClean(check_moved_levels(_data()["rows"]))

    def test_trainers(self):
        p = _data()["package"]
        self.assertClean(check_trainers(p.trainer_spells, p.trainer_removals))

    def test_consts(self):
        self.assertClean(check_consts(_data()["package"].consts))

    def test_no_forbidden_bits(self):
        self.assertClean(check_forbidden(_data()["rows"]))

    def test_no_capstone_text(self):
        self.assertClean(check_no_capstone(_data()["rows"]))

    def test_spike_ids_declared_nowhere(self):
        d = _data()
        p = d["package"]
        self.assertClean(check_spike_ids(
            d["texts"], list(d["dsl_rows"]) + list(d["csv_ids"]), [int(g["id"]) for g in p.spell_groups],
            [int(s["id"]) for s in p.skill_line_abilities], [int(c["entry"]) for c in p.creature_templates],
            [int(t.get("id", 0)) for t in p.talents]))


class WarriorW0aRageReferenceTest(unittest.TestCase):
    """D22: the worked example at the live k 0.43 / m 1.35 (level 60, 3.6 s two-hander, Battle Stance +10%)."""

    def test_worked_example(self):
        self.assertAlmostEqual(rage_dealt(60, 450, 3.6), 12.82, delta=0.01)             # 6.29 + 17.01 -> 12.82
        self.assertAlmostEqual(rage_dealt(60, 900, 3.6, crit=True), 25.63, delta=0.01)   # speed part doubles on a crit
        self.assertAlmostEqual(rage_dealt(60, 200, 2.6, main_hand=False, stance_pct=0), 2.54, delta=0.01)
        self.assertAlmostEqual(rage_dealt_stock(60, 450, 3.6), 13.32, delta=0.01)

    def test_worked_example_rederived_from_the_formula(self):
        c = 0.0091107836 * 60 * 60 + 3.225598133 * 60 + 4.2652911
        self.assertAlmostEqual(c, 230.60, delta=0.01)
        damage_part, speed_part = 0.43 * 7.5 * 450 / c, 3.6 * 3.5 * 1.35
        self.assertAlmostEqual(damage_part, 6.29, delta=0.01)
        self.assertAlmostEqual(speed_part, 17.01, delta=0.01)
        self.assertAlmostEqual((damage_part + speed_part) / 2 * 1.10, 12.82, delta=0.01)
        self.assertAlmostEqual((0.43 * 7.5 * 900 / c + 2 * speed_part) / 2 * 1.10, 25.63, delta=0.01)

    def test_conversion_and_cap(self):
        self.assertAlmostEqual(rage_conversion(60), 230.60, delta=0.01)
        # a tiny hit with a long swing is capped at the stock 15 x d / c, before the stance bonus
        self.assertAlmostEqual(rage_dealt(60, 10, 3.6, stance_pct=0), 15 * 10 / rage_conversion(60), places=6)

    def test_bloodlust_spell_haste_scales_rage_per_second(self):
        # Bloodlust: 30% melee AND spell haste -> swing 3.6 / 1.3 = 2.77 s; the spell-haste factor restores the speed
        # part of the 3.6 s swing, so every swing pays the unhasted 12.82 and rage per second grows 1.30x
        swing = 3.6 / 1.3
        per_swing = rage_dealt(60, 450, swing, spell_haste=0.30)
        self.assertAlmostEqual(per_swing, 12.82, delta=0.01)
        self.assertAlmostEqual((per_swing / swing) / (rage_dealt(60, 450, 3.6) / 3.6), 1.30, delta=0.01)

    def test_attack_speed_only_haste_is_not_rage_neutral_or_one_to_one(self):
        # an attack-speed-only 30% (no spell haste): per swing 10.66 (the speed part shrinks), per second only x1.08
        swing = 3.6 / 1.3
        per_swing = rage_dealt(60, 450, swing)
        self.assertAlmostEqual(per_swing, 10.66, delta=0.01)
        self.assertAlmostEqual((per_swing / swing) / (rage_dealt(60, 450, 3.6) / 3.6), 1.08, delta=0.01)

    def test_slow_never_lowers_rage(self):
        base = rage_dealt(60, 450, 3.6)
        self.assertEqual(rage_dealt(60, 450, 3.6, spell_haste=-0.30), base)             # max(1, 1 + haste)
        self.assertEqual(rage_dealt(60, 450, 3.6, spell_haste=-0.99), base)
        self.assertGreater(rage_dealt(60, 450, 3.6, spell_haste=0.01), base)

    def test_off_hand_takes_the_spell_haste_factor_too(self):
        self.assertAlmostEqual(rage_dealt(60, 200, 2.6 / 1.3, main_hand=False, stance_pct=0, spell_haste=0.30),
                               rage_dealt(60, 200, 2.6, main_hand=False, stance_pct=0), delta=0.01)

    def test_built_constants(self):
        # the built pair is the user's pick from the W0a sweep (k 0.43, m 1.35)
        self.assertEqual((CONSTS["RAGE_K_60"][0], CONSTS["RAGE_M_60"][0]), (0.43, 1.35))


# ---- negative fixtures: every check must fire on a minimal bad mutation of a built-row shape -----------------------

def _strike_rows() -> dict[int, dict]:
    def strike(sid, p_idx, f_idx, carrier, percent, sl, flat_bp, rppl, attrs=0x50010, **extra):
        r = {"ID": sid, "Attributes": attrs, "StartRecoveryCategory": 133, "StartRecoveryTime": 1500,
             "CastingTimeIndex": 1, "BaseLevel": sl, "SpellLevel": sl, f"Effect_{p_idx}": WEAPON_PERCENT,
             f"EffectBasePoints_{p_idx}": percent - 1, f"EffectDieSides_{p_idx}": 1,
             f"Effect_{f_idx}": carrier, f"EffectBasePoints_{f_idx}": flat_bp, f"EffectDieSides_{f_idx}": 1,
             f"EffectRealPointsPerLevel_{f_idx}": rppl}
        r.update(extra)
        return r
    return {
        HS: strike(HS, 1, 2, WEAPON_DAMAGE, 183, 1, -10, 4.8 / 7),
        CLEAVE: strike(CLEAVE, 1, 2, WEAPON_DAMAGE, 144, 14, -1, 4.8 / 7, EffectChainTargets_1=2,
                       EffectChainTargets_2=2),
        SLAM: strike(SLAM, 1, 2, WEAPON_DAMAGE, 200, 30, 15, 7.2 / 7),
        OVERPOWER: strike(OVERPOWER, 1, 2, NORMALIZED_WEAPON, 168, 12, -4, 6.8 / 7),
        MS: strike(MS, 2, 3, NORMALIZED_WEAPON, 228, 20, 4, 7.2 / 7, Effect_1=APPLY_AURA, EffectAura_1=118),
    }


def _entries() -> dict[int, dict]:
    out = {}
    for sid, (_p, fe, _c) in STRIKE_SHAPE.items():
        pot = {"kind": "direct", "total_potency": FLAT_POT[sid], "t_seconds": 1.5, "ap_coefficient": 0.0}
        out[sid] = {"id": sid, f"effect{fe}": {"_potency": pot}}
    return out


class WarriorW0aNegativeTest(unittest.TestCase):
    def test_improved_cleave(self):
        rows = {sid: {"ID": sid, "EffectAura_1": 108, "EffectMiscValue_1": 0, "EffectBasePoints_1": bp,
                      "EffectSpellClassMaskA_1": CLEAVE_MASK_A} for sid, bp in IMPROVED_CLEAVE.items()}
        self.assertEqual(check_improved_cleave(rows), [])
        for col, val in (("EffectMiscValue_1", 8), ("EffectBasePoints_1", 39), ("EffectSpellClassMaskA_1", 0)):
            for sid in IMPROVED_CLEAVE:
                self.assertEqual(len(check_improved_cleave({**rows, sid: {**rows[sid], col: val}})), 1, (sid, col))

    def test_instant_gcd(self):
        rows = _strike_rows()
        self.assertEqual(check_instant_gcd(rows), [])
        for col, val in (("Attributes", 0x50014), ("StartRecoveryTime", 0), ("StartRecoveryCategory", 0),
                         ("CastingTimeIndex", 16)):
            for sid in (HS, CLEAVE, SLAM):
                self.assertEqual(len(check_instant_gcd({**rows, sid: {**rows[sid], col: val}})), 1, (sid, col))
        self.assertEqual(len(check_instant_gcd({k: v for k, v in rows.items() if k != HS})), 1)

    def test_strike_shape(self):
        rows, ents = _strike_rows(), _entries()
        self.assertEqual(check_strike_shape(rows, ents), [])
        for sid, (pe, fe, carrier) in STRIKE_SHAPE.items():
            # percent after the flat part (swap the two effects' types)
            bad = copy.deepcopy(rows[sid])
            bad[f"Effect_{pe}"], bad[f"Effect_{fe}"] = bad[f"Effect_{fe}"], bad[f"Effect_{pe}"]
            self.assertGreaterEqual(len(check_strike_shape({**rows, sid: bad}, ents)), 1, (sid, "order"))
            # wrong flat carrier
            self.assertGreaterEqual(len(check_strike_shape(
                {**rows, sid: {**rows[sid], f"Effect_{fe}": 2}}, ents)), 1, (sid, "carrier"))
            # wrong percent
            self.assertGreaterEqual(len(check_strike_shape(
                {**rows, sid: {**rows[sid], f"EffectBasePoints_{pe}": PERCENTS[sid]}}, ents)), 1, (sid, "percent"))
            # percent carrying a slope
            self.assertGreaterEqual(len(check_strike_shape(
                {**rows, sid: {**rows[sid], f"EffectRealPointsPerLevel_{pe}": 1.0}}, ents)), 1, (sid, "slope"))
            # flat part off (wrong level-60 value)
            self.assertGreaterEqual(len(check_strike_shape(
                {**rows, sid: {**rows[sid], f"EffectBasePoints_{fe}": rows[sid][f"EffectBasePoints_{fe}"] + 5}},
                ents)), 1, (sid, "flat value"))
            # flat sp_potency wrong / not direct / not T 1500 / missing
            for key, val in (("total_potency", 99), ("kind", "periodic"), ("t_seconds", 3.0), ("ap_coefficient", 0.1)):
                e2 = copy.deepcopy(ents)
                e2[sid][f"effect{fe}"]["_potency"][key] = val
                self.assertGreaterEqual(len(check_strike_shape(rows, e2)), 1, (sid, key))
            e3 = copy.deepcopy(ents)
            e3[sid][f"effect{fe}"] = {}
            self.assertGreaterEqual(len(check_strike_shape(rows, e3)), 1, (sid, "no potency"))
        self.assertGreaterEqual(len(check_strike_shape({k: v for k, v in rows.items() if k != MS}, ents)), 1)

    def test_cleave_chain(self):
        rows = _strike_rows()
        self.assertEqual(check_cleave_chain(rows), [])
        for col in ("EffectChainTargets_1", "EffectChainTargets_2"):
            self.assertEqual(len(check_cleave_chain({**rows, CLEAVE: {**rows[CLEAVE], col: 0}})), 1, col)
        self.assertEqual(len(check_cleave_chain({**rows, HS: {**rows[HS], "EffectChainTargets_1": 2}})), 1)

    def test_slam(self):
        row = {"ID": SLAM, "CastingTimeIndex": 1, "RecoveryTime": 6000, "InterruptFlags": 0, "AttributesEx3": 0x400,
               "Effect_1": WEAPON_PERCENT, "Effect_2": WEAPON_DAMAGE}
        rem = [{"spell_id": -SLAM, "ScriptName": "spell_warr_slam"}]
        self.assertEqual(check_slam({SLAM: row}, rem, []), [])
        for col, val in (("CastingTimeIndex", 16), ("RecoveryTime", 0), ("InterruptFlags", 13),
                         ("AttributesEx3", 0x30400), ("Effect_1", DUMMY)):
            self.assertEqual(len(check_slam({SLAM: {**row, col: val}}, rem, [])), 1, col)
        self.assertEqual(len(check_slam({SLAM: {**row, "Effect_2": APPLY_AURA, "EffectAura_2": 4}}, rem, [])), 1)
        self.assertEqual(len(check_slam({SLAM: row}, [], [])), 1)                                    # no unbind
        self.assertEqual(len(check_slam({SLAM: row}, rem, [{"spell_id": -SLAM, "ScriptName": "spell_warr_slam"}])), 1)
        self.assertEqual(len(check_slam({}, rem, [])), 1)

    def test_categories(self):
        rows = {MS: {"ID": MS, "Category": 0, "RecoveryTime": 6000, "SpellLevel": 20, "BaseLevel": 20, "ManaCost": 250,
                     "Effect_1": APPLY_AURA, "EffectAura_1": 118, "Effect_2": WEAPON_PERCENT,
                     "Effect_3": NORMALIZED_WEAPON},
                BT: {"ID": BT, "Category": 0, "RecoveryTime": 6000},
                OVERPOWER: {"ID": OVERPOWER, "Category": 0, "AttributesEx": 0x58000200},
                REVENGE: {"ID": REVENGE, "Category": 0, "RecoveryTime": 3000}}
        self.assertEqual(check_categories(rows), [])
        mutations = (
            (MS, "Category", 971), (MS, "RecoveryTime", 0), (MS, "CategoryRecoveryTime", 6000), (MS, "SpellLevel", 40),
            (MS, "BaseLevel", 40), (MS, "EffectAura_1", 0), (MS, "Effect_2", NORMALIZED_WEAPON),
            (MS, "Effect_3", WEAPON_PERCENT), (BT, "Category", 971), (BT, "RecoveryTime", 0),
            (BT, "CategoryRecoveryTime", 6000), (BT, "RecoveryTime", 4000), (OVERPOWER, "Category", 65),
            (OVERPOWER, "CategoryRecoveryTime", 5000),
            (OVERPOWER, "RecoveryTime", 6000), (OVERPOWER, "AttributesEx", 0x58100200), (REVENGE, "Category", 65),
            (REVENGE, "RecoveryTime", 0), (REVENGE, "CategoryRecoveryTime", 3000), (MS, "ManaCost", 300))
        for sid, col, val in mutations:
            self.assertGreaterEqual(len(check_categories({**rows, sid: {**rows[sid], col: val}})), 1, (sid, col))
        self.assertGreaterEqual(len(check_categories({k: v for k, v in rows.items() if k != BT})), 1)

    def test_zero_list(self):
        rows = {sid: {"ID": sid, "ShapeshiftMask": 0} for sid in ZERO_LIST}
        rows.update({sid: {"ID": sid, "ShapeshiftMask": mask} for sid, mask in UNTOUCHED.items()})
        rows[28880]["ShapeshiftExclude"] = 0x8000000
        self.assertEqual(check_zero_list(rows), [])
        for sid in ZERO_LIST:
            self.assertEqual(len(check_zero_list({**rows, sid: {"ID": sid, "ShapeshiftMask": 65536}})), 1, sid)
        self.assertEqual(len(check_zero_list({k: v for k, v in rows.items() if k != 72})), 1)
        for sid in (28880, 694, 20230, 20252, 12295, 7887, 11584):   # zeroed by mistake
            self.assertGreaterEqual(len(check_zero_list({**rows, sid: {"ID": sid, "ShapeshiftMask": 0}})), 1, sid)
        self.assertEqual(len(check_zero_list({**rows, 28880: {**rows[28880], "ShapeshiftExclude": 0}})), 1)
        self.assertEqual(len(ZERO_LIST), 22)

    def test_battle_stance(self):
        row = {"ID": BATTLE, "Effect_1": APPLY_AURA, "EffectAura_1": 36, "Effect_2": APPLY_AURA, "EffectAura_2": 213,
               "EffectBasePoints_2": 9, "EffectDieSides_2": 1}
        self.assertEqual(check_battle_stance({BATTLE: row}), [])
        for col, val in (("EffectAura_2", 280), ("EffectBasePoints_2", 8), ("EffectBasePoints_2", 4), ("Effect_2", 2),
                         ("EffectAura_1", 4)):
            self.assertGreaterEqual(len(check_battle_stance({BATTLE: {**row, col: val}})), 1, col)
        # 213 present but a leftover aura 280 on the third effect
        self.assertEqual(len(check_battle_stance({BATTLE: {**row, "EffectAura_3": 280}})), 1)
        self.assertEqual(len(check_battle_stance({BATTLE: {**row, "EffectAura_2": 0}})), 1)   # no aura 213 at all
        self.assertEqual(len(check_battle_stance({})), 1)

    def test_stance_mastery(self):
        row = {"ID": STANCE_MASTERY, "EffectBasePoints_1": 149, "SpellIconID": 139, "SpellClassSet": 4}
        sla = [{"id": 15513, "spell_id": STANCE_MASTERY, "skill_line": 26, "acquire_method": 2, "class_mask": 1}]
        consts = [{"name": "RAGE_STANCE_MASTERY_POINTS", "value": 149}]
        self.assertEqual(check_stance_mastery({STANCE_MASTERY: row}, sla, consts), [])
        for col, val in (("EffectBasePoints_1", 9), ("SpellIconID", 140), ("SpellClassSet", 0)):
            self.assertEqual(len(check_stance_mastery({STANCE_MASTERY: {**row, col: val}}, sla, consts)), 1, col)
        for col, val in (("skill_line", 257), ("acquire_method", 0), ("class_mask", 2), ("id", 15514)):
            self.assertEqual(len(check_stance_mastery({STANCE_MASTERY: row}, [{**sla[0], col: val}], consts)), 1, col)
        self.assertEqual(len(check_stance_mastery({STANCE_MASTERY: row}, [], consts)), 1)
        self.assertGreaterEqual(len(check_stance_mastery({STANCE_MASTERY: row}, sla,
                                                         [{"name": "RAGE_STANCE_MASTERY_POINTS", "value": 99}])), 1)
        self.assertEqual(len(check_stance_mastery({}, sla, consts)), 1)

    def test_path(self):
        row = {"ID": PATH, "Effect_1": 36, "EffectTriggerSpell_1": BERSERKER,
               "Description_Lang_enUS": "Teaches Berserker Stance."}
        self.assertEqual(check_path_of_the_berserker({PATH: row}), [])
        for mut in ({"Effect_2": 36, "EffectTriggerSpell_2": 20252}, {"EffectTriggerSpell_1": 20252},
                    {"Description_Lang_enUS": "Teaches Intercept."}, {"Effect_1": 6}):
            self.assertGreaterEqual(len(check_path_of_the_berserker({PATH: {**row, **mut}})), 1, mut)
        self.assertEqual(len(check_path_of_the_berserker({})), 1)

    def test_rend(self):
        row = {"ID": REND, "EffectAura_1": 3, "EffectAuraPeriod_1": 3000, "BaseLevel": 4, "SpellLevel": 4,
               "EffectBasePoints_1": -16, "EffectRealPointsPerLevel_1": 1.3476, "EffectDieSides_1": 1}
        ent = {"id": REND, "effect1": {"_potency": {"kind": "periodic", "total_potency": 11.23, "t_seconds": 3.0,
                                                    "ap_coefficient": 0.0771}}}
        rem = [{"spell_id": -REND, "ScriptName": "spell_warr_rend"}]
        self.assertEqual(check_rend({REND: row}, {REND: ent}, rem, []), [])
        for key, val in (("total_potency", 10.7), ("kind", "direct"), ("t_seconds", 1.5)):
            e2 = copy.deepcopy(ent)
            e2["effect1"]["_potency"][key] = val
            self.assertGreaterEqual(len(check_rend({REND: row}, {REND: e2}, rem, [])), 1, key)
        e0 = copy.deepcopy(ent)
        e0["effect1"]["_potency"]["ap_coefficient"] = 0.0
        self.assertGreaterEqual(len(check_rend({REND: row}, {REND: e0}, rem, [])), 1)
        for col, val in (("EffectAuraPeriod_1", 1000), ("EffectAura_1", 4), ("EffectBasePoints_1", -21)):
            self.assertGreaterEqual(len(check_rend({REND: {**row, col: val}}, {REND: ent}, rem, [])), 1, col)
        self.assertEqual(len(check_rend({REND: row}, {REND: ent}, [], [])), 1)
        self.assertEqual(len(check_rend({REND: row}, {REND: ent}, rem, [{"spell_id": -REND}])), 1)
        self.assertEqual(len(check_rend({}, {}, rem, [])), 1)

    def test_thunder_clap(self):
        row, ent = {"ID": THUNDER_CLAP, "DurationIndex": 9}, {"id": THUNDER_CLAP, "duration_ms": 30000}
        self.assertEqual(check_thunder_clap({THUNDER_CLAP: row}, {THUNDER_CLAP: ent}, 9), [])
        self.assertEqual(
            len(check_thunder_clap({THUNDER_CLAP: {**row, "DurationIndex": 1}}, {THUNDER_CLAP: ent}, 9)), 1)
        self.assertGreaterEqual(
            len(check_thunder_clap({THUNDER_CLAP: row}, {THUNDER_CLAP: {**ent, "duration_ms": 10000}}, 9)), 1)
        self.assertEqual(len(check_thunder_clap({}, {}, 9)), 1)

    def test_commanding_shout(self):
        row = {"ID": COMMANDING_SHOUT, "BaseLevel": 22, "SpellLevel": 22, "MaxLevel": 60, "EffectBasePoints_1": 112,
               "EffectRealPointsPerLevel_1": 4.8422, "EffectDieSides_1": 1}
        self.assertEqual(check_commanding_shout({COMMANDING_SHOUT: row}), [])
        self.assertEqual(calc_value(row, 1, 22), 113)
        self.assertEqual(calc_value(row, 1, 60), 297)
        for col, val in (("EffectBasePoints_1", 1079), ("EffectRealPointsPerLevel_1", 3.0), ("MaxLevel", 80),
                         ("SpellLevel", 68), ("BaseLevel", 68), ("EffectBasePoints_1", 111)):
            self.assertGreaterEqual(len(check_commanding_shout({COMMANDING_SHOUT: {**row, col: val}})), 1, col)
        self.assertEqual(len(check_commanding_shout({})), 1)

    def test_moved_levels(self):
        rows = {sid: {"ID": sid, "SpellLevel": lv, "BaseLevel": lv} for sid, lv in MOVED_LEVELS.items()}
        rows[PUMMEL].update(Effect_1=68)
        rows[SPELL_REFLECTION].update(EffectAura_1=28, EffectBasePoints_1=99, EffectDieSides_1=1)
        rows[SHATTERING_THROW].update(EffectBasePoints_1=8, EffectRealPointsPerLevel_1=0.25714, EffectDieSides_1=1)
        rows[HEROIC_THROW].update(EffectBasePoints_1=10, EffectRealPointsPerLevel_1=0.25714, EffectDieSides_1=1)
        self.assertEqual(check_moved_levels(rows), [])
        for sid in MOVED_LEVELS:
            self.assertGreaterEqual(len(check_moved_levels({**rows, sid: {**rows[sid], "SpellLevel": 99}})), 1, sid)
        for sid, mut in ((PUMMEL, {"EffectRealPointsPerLevel_1": 1.0}), (SPELL_REFLECTION, {"EffectBasePoints_1": 49}),
                         (SHATTERING_THROW, {"EffectBasePoints_1": 12}), (HEROIC_THROW, {"EffectBasePoints_1": 15})):
            self.assertGreaterEqual(len(check_moved_levels({**rows, sid: {**rows[sid], **mut}})), 1, sid)

    def test_trainers(self):
        good = [{"TrainerId": t, "SpellId": s, "ReqLevel": lv} for (t, s), lv in TRAINER_ROWS.items()]
        rem = [{"TrainerId": t, "SpellId": s} for t, s in UNTRAINED]
        self.assertEqual(check_trainers(good, rem), [])
        self.assertEqual(len(check_trainers(good[1:], rem)), 1)
        self.assertEqual(len(check_trainers([{**good[0], "ReqLevel": 23}] + good[1:], rem)), 1)
        moved = [{**g, "ReqLevel": 30} if g["SpellId"] == 2458 and g["TrainerId"] == 201 else g for g in good]
        self.assertEqual(len(check_trainers(moved, rem)), 1)
        for t, s in UNTRAINED:
            extra = [{"TrainerId": t, "SpellId": s, "ReqLevel": 20}]
            self.assertEqual(len(check_trainers(good + extra, rem)), 2, (t, s))
        self.assertEqual(len(check_trainers(good, rem[1:])), 1)
        self.assertEqual(len(check_trainers(good + [{"TrainerId": 200, "SpellId": 12294, "ReqLevel": 20}], rem)), 1)

    def test_consts(self):
        good = [{"name": n, "value": v, "cpp_type": t} for n, (v, t) in CONSTS.items()]
        self.assertEqual(check_consts(good), [])
        self.assertEqual(len(check_consts(good[1:])), 1)
        for i, value in ((0, 0.5), (1, 1.0), (2, 1.75), (3, 1.75), (4, 1000), (5, 9)):
            bad = [{**g, "value": value} if j == i else g for j, g in enumerate(good)]
            self.assertEqual(len(check_consts(bad)), 1, i)
        self.assertEqual(len(check_consts([{**good[4], "cpp_type": "int32"}] + good[:4] + good[5:])), 1)

    def test_forbidden(self):
        ok = {HS: {"ID": HS, "SpellClassMask_1": 0x40}, STANCE_MASTERY: {"ID": STANCE_MASTERY,
                                                                          "EffectSpellClassMaskA_1": 0x800000}}
        self.assertEqual(check_forbidden(ok), [])
        for col, bit in (("SpellClassMask_1", 0x1), ("SpellClassMask_1", 0x2), ("SpellClassMask_1", 0x20000),
                         ("SpellClassMask_1", 0x1000000), ("SpellClassMask_2", 0x20), ("SpellClassMask_2", 0x40),
                         ("SpellClassMask_3", 0x80000000), ("EffectSpellClassMaskA_1", 0x1),
                         ("EffectSpellClassMaskB_2", 0x40), ("EffectSpellClassMaskC_3", 0x80000000)):
            self.assertEqual(len(check_forbidden({HS: {**ok[HS], col: bit}})), 1, (col, bit))
        self.assertEqual(check_forbidden({100: {"ID": 100, "SpellClassMask_1": 0x1}}), [])   # not a W0a row

    def test_no_capstone(self):
        ok = {HS: {"ID": HS, "Description_Lang_enUS": "An instant strike."}}
        self.assertEqual(check_no_capstone(ok), [])
        self.assertEqual(len(check_no_capstone({HS: {"ID": HS, "Description_Lang_enUS": "Capstone Bonus: x"}})), 1)
        self.assertEqual(len(check_no_capstone({HS: {"ID": HS, "AuraDescription_Lang_enUS": "capstone"}})), 1)
        self.assertEqual(check_no_capstone({999: {"ID": 999, "Description_Lang_enUS": "Capstone"}}), [])

    def test_spike_ids(self):
        self.assertEqual(check_spike_ids({"a.py": "id=12345"}, [78], [1003], [15513], [300369], [60400]), [])
        self.assertEqual(len(check_spike_ids({}, [204869], [], [], [], [])), 1)
        self.assertEqual(len(check_spike_ids({}, [204899], [], [], [], [])), 1)
        self.assertEqual(check_spike_ids({}, [204868, 204900], [], [], [], []), [])
        self.assertEqual(len(check_spike_ids({"a.py": "spell(id=204880,"}, [], [], [], [], [])), 1)
        self.assertEqual(len(check_spike_ids({"a.py": "spell(spell_id = 204899)"}, [], [], [], [], [])), 1)
        self.assertEqual(check_spike_ids({"a.py": "# the P0 204875 shape"}, [], [], [], [], []), [])   # a comment
        self.assertEqual(len(check_spike_ids({}, [], [1305], [], [], [])), 1)
        self.assertEqual(len(check_spike_ids({}, [], [], [30868], [], [])), 1)
        self.assertEqual(len(check_spike_ids({}, [], [], [], [300388], [])), 1)
        self.assertEqual(len(check_spike_ids({}, [], [], [], [], [60489])), 1)

    def test_rage_reference_rejects_wrong_constants(self):
        self.assertGreater(abs(rage_dealt(60, 450, 3.6, k=0.5) - 12.82), 0.01)
        self.assertGreater(abs(rage_dealt(60, 450, 3.6, m_=1.8) - 12.82), 0.01)          # the retired placeholder m
        self.assertGreater(abs(rage_dealt(60, 450, 3.6, m_=1.0) - 12.82), 0.01)
        self.assertGreater(abs(rage_dealt(60, 450, 3.6, stance_pct=0) - 12.82), 0.01)
        self.assertGreater(abs(rage_dealt(60, 450, 3.6, fixed_point=1000) - 12.82), 0.01)
        self.assertGreater(abs(rage_dealt(60, 450, 3.6, crit=True) - 12.82), 0.01)
        self.assertGreater(abs(rage_dealt(60, 200, 2.6, main_hand=True, stance_pct=0) - 2.54), 0.01)

    def test_rage_reference_rejects_haste_neutral_and_wrong_haste(self):
        swing = 3.6 / 1.3
        # a haste-neutral reference (spell haste ignored) cannot reproduce the Bloodlust per-swing number ...
        self.assertGreater(abs(rage_dealt(60, 450, swing, spell_haste=0.0) - 12.82), 0.01)
        # ... nor does a half-strength or an inverted factor
        self.assertGreater(abs(rage_dealt(60, 450, swing, spell_haste=0.15) - 12.82), 0.01)
        self.assertGreater(abs(rage_dealt(60, 450, swing, spell_haste=-0.30) - 12.82), 0.01)
        # the attack-speed-only number is not the spell-haste number
        self.assertGreater(abs(rage_dealt(60, 450, swing) - rage_dealt(60, 450, swing, spell_haste=0.30)), 1.0)
        # per second: the attack-speed-only gain (x1.08) is nowhere near x1.30
        ratio = (rage_dealt(60, 450, swing) / swing) / (rage_dealt(60, 450, 3.6) / 3.6)
        self.assertLess(ratio, 1.1)

    def test_calc_value_matches_known_rows(self):
        # 0VERIFY item 3: Battle Shout 14 / 6.77215 / SL 1 -> 157 at 22, 414 at 60 (the curve Commanding Shout follows)
        bs = {"BaseLevel": 1, "SpellLevel": 1, "MaxLevel": 80, "EffectBasePoints_1": 14,
              "EffectRealPointsPerLevel_1": 6.77215, "EffectDieSides_1": 1}
        self.assertEqual((calc_value(bs, 1, 22), calc_value(bs, 1, 60)), (157, 414))
        self.assertNotEqual(calc_value({**bs, "EffectBasePoints_1": 15}, 1, 60), 414)


if __name__ == "__main__":
    unittest.main()
