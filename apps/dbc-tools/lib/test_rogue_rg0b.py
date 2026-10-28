"""
Rogue RG0b data gate (rogue-rework RG0b-HANDOFF WP-A/B table row A4, RG0b-WP-BRIEF).

Loads the real rogue DSL package (source/classes/rogue/) and asserts on the BUILT rows (stock base + DSL +
raw_overrides via `build.build_spell_row`, the way generate.py pairs them), like test_rogue_rg0a.py. Every check is a
pure function over built rows / package tables; the negative tests prove each can fail (the row-level expectations
are mutated one by one, so every single expectation has its own negative).

  1. Row expectations (EXPECT / MUST_SET / MUST_CLEAR): the seven new rows 203720-203726 and the reworked stock rows
     1752 / 53 / 8676 / 14278 / 51723 / 26679 / 1943 / 1966 (attributes, GCD, cost, cooldown, category, duration,
     range, SpellLevel, effect order and amounts, family bits). Stock masks are wider than the handoff table
     (brief C2), so stock rows use `mask & CONST`; Ghostly Strike d0 and the new rows' masks are exact.
  2. Enforcer links (3) + custom attrs (Enforcer 0x08000000, Ambush 0), Ghostly Veil proc row, SkillLineAbility
     30790-30793, trainer 206 rows (SpellLevel = trainer level), script bindings (5938 unbound, Shiv/Ambush bound),
     talent 303 retired to tab 60800.
  3. No FORBIDDEN_* bit and no dagger-hardcode bit (d0 b25 / b26, d1 b18) on any new row or on Ghostly Strike.
  4. Deadly Throw / Rupture `${...}` tooltips evaluated against `potency.simulate_value` (+ the 0-verify anchors).

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_rogue_rg0b.py -q
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, potency, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402
from lib.test_rogue_rg0a import (  # noqa: E402,F401
    ATTR0_HIDDEN, ATTR0_PASSIVE, TOOL_ROOT, ROGUE_DIR, _i, _u32, effect_mask, m, spell_mask)

NEW_IDS = (203720, 203721, 203722, 203723, 203724, 203725, 203726)
ENFORCER, ENFORCER_CRIT, INSULT, VEIL, SHROUD, SHIV, TELEPORT = NEW_IDS
SS, BS, AMBUSH, GARROTE, CHEAP_SHOT, GS, FOK, DT, RUPTURE, FEINT, OLD_SHIV = (
    1752, 53, 8676, 703, 1833, 14278, 51723, 26679, 1943, 1966, 5938)
TRAINER = 206
TRAINER_ROWS = {ENFORCER: 10, INSULT: 10, GS: 10, FOK: 24, SHROUD: 28, DT: 36, SHIV: 50}
SLA_ROWS = {30790: (38, ENFORCER), 30791: (38, INSULT), 30792: (39, SHROUD), 30793: (38, SHIV)}
LINKS = {(ENFORCER, ENFORCER_CRIT, 2), (ENFORCER, 57340, 2), (-ENFORCER, -57340, 0)}
SHIV_BAD_EX3 = 0x10000 | 0x20000 | 0x40000 | 0x1000000
SHIV_BAD_EX2 = 0x20000000
# d0 b11 / b22 / b25, d0 b16 / b17 / b20, d1 b1-b3, d1 b18, d1 b19: never on a new RG0b row
NEVER_D0 = m.FORBIDDEN_D0 | m.FORBIDDEN_DAGGER_D0 | 0x10000 | 0x20000 | 0x100000
NEVER_D1 = m.FORBIDDEN_D1 | m.FORBIDDEN_DAGGER_D1 | 0x80000
ATTR1_ALLOW_WHILE_STEALTHED = 0x20
ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000


# ---- expectations ------------------------------------------------------------------------------------------------

def expectations(idx: dict) -> tuple[dict, dict, dict]:
    """(EXPECT {id: {col: exact value}}, MUST_SET {id: {col: bits}}, MUST_CLEAR {id: {col: bits}}). `idx` carries the
    reuse-minted indices (infinite duration, 3 / 6 / 15 s and Rupture's 4-24 s durations, 20 / 25 yd ranges)."""
    inf = idx["infinite"]
    exact = {
        ENFORCER: {
            "Attributes": 0x29050010, "SpellLevel": 10, "BaseLevel": 10, "EquippedItemClass": -1, "DurationIndex": inf,
            "RecoveryTime": 1000, "Category": 0, "CategoryRecoveryTime": 0, "StartRecoveryCategory": 0,
            "StartRecoveryTime": 0, "ManaCost": 0, "RangeIndex": 1, "CastingTimeIndex": 1,
            "Effect_1": 6, "EffectAura_1": 142, "EffectMiscValue_1": 1, "EffectBasePoints_1": 79,
            "Effect_2": 6, "EffectAura_2": 10, "EffectMiscValue_2": 127, "EffectBasePoints_2": 104,
            "Effect_3": 6, "EffectAura_3": 79, "EffectMiscValue_3": 127, "EffectBasePoints_3": -11,
            "SpellIconID": 276, "SpellVisualID_1": 0,
            "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0,
        },
        ENFORCER_CRIT: {
            "Attributes": 0xC0, "AttributesEx2": 0x1, "AttributesEx3": ATTR3_ALLOW_AURA_WHILE_DEAD, "SpellLevel": 1,
            "EquippedItemClass": -1, "DurationIndex": inf,
            "Effect_1": 6, "EffectAura_1": 187, "EffectBasePoints_1": -1001,
            "Effect_2": 6, "EffectAura_2": 188, "EffectBasePoints_2": -1001, "Effect_3": 0,
            "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0,
        },
        INSULT: {
            "Attributes": 327696, "Category": 82, "CategoryRecoveryTime": 8000, "RecoveryTime": 0,
            "CasterAuraSpell": ENFORCER, "StartRecoveryCategory": 0, "StartRecoveryTime": 0, "ManaCost": 0,
            "SpellLevel": 10, "BaseLevel": 10, "EquippedItemClass": -1, "DurationIndex": idx["d3000"],
            "RangeIndex": idx["r20"], "SpellIconID": 24, "SpellVisualID_1": 34,
            "Effect_1": 114, "Effect_2": 6, "EffectAura_2": 11, "Effect_3": 0,
            "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0,
        },
        VEIL: {
            "ProcCharges": 5, "DurationIndex": inf, "RangeIndex": 1, "SpellLevel": 10, "EquippedItemClass": -1,
            "Attributes": 0, "Category": 0, "RecoveryTime": 0, "SpellIconID": 596,
            "Effect_1": 6, "EffectAura_1": 49, "EffectBasePoints_1": 9, "Effect_2": 0,
            "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0,
        },
        SHROUD: {
            "RecoveryTime": 360000, "Category": 0, "CategoryRecoveryTime": 0, "StartRecoveryCategory": 133,
            "StartRecoveryTime": 1000, "DurationIndex": idx["d15000"], "SpellLevel": 28, "BaseLevel": 28,
            "EquippedItemClass": -1, "RangeIndex": 1, "ManaCost": 0, "ShapeshiftMask": 0x20000000,
            "AuraInterruptFlags": 0x23C04, "SpellIconID": 250, "SpellVisualID_1": 184,
            "Effect_1": 6, "EffectAura_1": 16, "EffectBasePoints_1": 139, "ImplicitTargetA_1": 56,
            "Effect_2": 0, "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0,
        },
        SHIV: {
            "Attributes": 327696, "AttributesEx": 134218240, "AttributesEx3": 0x400, "DefenseType": 2,
            "PreventionType": 2, "FacingCasterFlags": 1, "EquippedItemClass": 2, "EquippedItemSubclass": 0x2A5F3,
            "ManaCost": 20, "RecoveryTime": 30000, "Category": 0, "StartRecoveryCategory": 133,
            "StartRecoveryTime": 1000, "SpellLevel": 50, "BaseLevel": 50, "RangeIndex": idx["melee"],
            "SpellIconID": 1834, "SpellVisualID_1": 8056, "DurationIndex": inf,
            "Effect_1": 31, "EffectBasePoints_1": 99, "Effect_2": 80, "Effect_3": 0,
            "SpellClassMask_1": 0x20000000, "SpellClassMask_2": 0, "SpellClassMask_3": 0x80000,   # S1: d2 b19
        },
        TELEPORT: {
            "Attributes": 0x80, "AttributesEx": 0x420, "StartRecoveryCategory": 0, "StartRecoveryTime": 0,
            "ManaCost": 0, "RecoveryTime": 0, "SpellVisualID_1": 8262, "EquippedItemClass": -1,
            "Effect_1": 5, "ImplicitTargetA_1": 1, "ImplicitTargetB_1": 65, "EffectRadiusIndex_1": 7, "Effect_2": 0,
            "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0,
        },
        # ---- reworked stock rows: costs, effect order (percent first), levels
        SS: {"ManaCost": 40, "SpellLevel": 1, "BaseLevel": 1, "Effect_1": 31, "EffectBasePoints_1": 99,
             "Effect_2": 121, "Effect_3": 80, "MaxLevel": 0, "StartRecoveryCategory": 133, "StartRecoveryTime": 1000},
        BS: {"ManaCost": 45, "SpellLevel": 4, "BaseLevel": 4, "Effect_1": 31, "EffectBasePoints_1": 149,
             "Effect_2": 121, "Effect_3": 80},
        AMBUSH: {"ManaCost": 45, "SpellLevel": 18, "BaseLevel": 18, "Effect_1": 31, "EffectBasePoints_1": 174,
                 "Effect_2": 121, "Effect_3": 80, "EffectBasePoints_3": 1, "RangeIndex": idx["r25"],
                 "EquippedItemClass": 2, "EquippedItemSubclass": 0x2A5F3},
        GS: {"RecoveryTime": 0, "Category": 0, "CategoryRecoveryTime": 0, "DurationIndex": inf, "SpellLevel": 10,
             "BaseLevel": 10, "SpellClassMask_1": 0x40000000, "Effect_1": 31, "EffectBasePoints_1": 99,
             "Effect_2": 64, "EffectTriggerSpell_2": VEIL, "ImplicitTargetA_2": 1, "Effect_3": 80},
        FOK: {"SpellLevel": 24, "BaseLevel": 24, "Effect_1": 31, "EffectBasePoints_1": 69, "Effect_2": 80,
              "Effect_3": 0},
        DT: {"Effect_1": 2, "EffectPointsPerCombo_1": 0, "SpellLevel": 36, "BaseLevel": 36, "Effect_2": 6,
             "EffectAura_2": 33},
        RUPTURE: {"DurationIndex": idx["d4000_24000"], "SpellLevel": 20},
        FEINT: {"Effect_1": 6, "EffectAura_1": 229, "EffectMiscValue_1": 127, "EffectBasePoints_1": -41,
                "Effect_2": 0, "Effect_3": 0, "DurationIndex": idx["d6000"], "ManaCost": 35, "RecoveryTime": 15000,
                "Category": 0, "CategoryRecoveryTime": 0, "FacingCasterFlags": 0, "RangeIndex": 1},
    }
    must_set = {
        ENFORCER: {"AttributesEx": ATTR1_ALLOW_WHILE_STEALTHED, "AttributesEx3": ATTR3_ALLOW_AURA_WHILE_DEAD},
        SHROUD: {"Attributes": 0x20000, "AttributesEx": ATTR1_ALLOW_WHILE_STEALTHED},
        SS: {"SpellClassMask_1": m.SINISTER_STRIKE},
        BS: {"SpellClassMask_1": m.BACKSTAB},
        AMBUSH: {"SpellClassMask_1": m.AMBUSH, "Attributes": 0x20000},   # ONLY_STEALTHED stays
        DT: {"SpellClassMask_2": m.DEADLY_THROW_D1},
        FOK: {"SpellClassMask_2": m.FAN_OF_KNIVES_D1},
        FEINT: {"SpellClassMask_1": m.FEINT},
        GS: {"SpellClassMask_1": m.GHOSTLY_STRIKE},
    }
    must_clear = {
        ENFORCER: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},   # a visible, non-passive buff
        VEIL: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        SHROUD: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        FEINT: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        SHIV: {"AttributesEx3": SHIV_BAD_EX3, "AttributesEx2": SHIV_BAD_EX2},
        GS: {"SpellClassMask_1": m.GHOSTLY_STRIKE_DAGGER},
        SS: {"SpellClassMask_1": m.FORBIDDEN_DAGGER_D0},
        BS: {"SpellClassMask_1": m.FORBIDDEN_DAGGER_D0},
        AMBUSH: {"SpellClassMask_1": m.FORBIDDEN_DAGGER_D0},
    }
    return exact, must_set, must_clear


def check_rows(rows: dict, exact: dict, must_set: dict, must_clear: dict) -> list[str]:
    bad = []
    for sid in sorted(set(exact) | set(must_set) | set(must_clear)):
        row = rows.get(sid)
        if row is None:
            bad.append(f"{sid}: not built")
            continue
        for col, want in exact.get(sid, {}).items():
            if _u32(row.get(col)) != _u32(want):
                bad.append(f"{sid}: {col} = {row.get(col)!r}, expected {want!r}")
        for col, bits in must_set.get(sid, {}).items():
            if not _u32(row.get(col)) & bits:
                bad.append(f"{sid}: {col} {_u32(row.get(col)):#x} lacks {bits:#x}")
        for col, bits in must_clear.get(sid, {}).items():
            if _u32(row.get(col)) & bits:
                bad.append(f"{sid}: {col} {_u32(row.get(col)):#x} carries {_u32(row.get(col)) & bits:#x}")
    return bad


def check_fok_combo(rows: dict) -> list[str]:
    """Fan of Knives' combo-point effect hits the same targets as the damage effect (same A / B / radius)."""
    r = rows.get(FOK)
    if r is None:
        return [f"{FOK}: not built"]
    bad = []
    for col in ("ImplicitTargetA", "ImplicitTargetB", "EffectRadiusIndex"):
        if _i(r, f"{col}_1") != _i(r, f"{col}_2"):
            bad.append(f"{FOK}: {col} differs between the damage and combo-point effects "
                       f"({r.get(f'{col}_1')!r} vs {r.get(f'{col}_2')!r})")
    if not _i(r, "EffectRadiusIndex_1"):
        bad.append(f"{FOK}: area effect has no radius")
    return bad


def check_no_never_bits(rows: dict) -> list[str]:
    """New rows (any effect mask too) and Ghostly Strike's d0 hold none of the 'never' bits."""
    bad = []
    for sid in NEW_IDS + (GS,):
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
            continue
        d0, d1, _d2 = spell_mask(r)
        if d0 & NEVER_D0:
            bad.append(f"{sid}: SpellClassMask_1 {d0:#x} holds never-bits {d0 & NEVER_D0:#x}")
        if sid in NEW_IDS and d1 & NEVER_D1:
            bad.append(f"{sid}: SpellClassMask_2 {d1:#x} holds never-bits {d1 & NEVER_D1:#x}")
        for i in (1, 2, 3):
            em = effect_mask(r, i)
            if em[0] & NEVER_D0 or (sid in NEW_IDS and em[1] & NEVER_D1):
                bad.append(f"{sid}: effect {i} mask holds never-bits")
    return bad


def check_texts(rows: dict) -> list[str]:
    bad = []
    for sid in (AMBUSH, GARROTE, CHEAP_SHOT):
        if "Must be Hidden" not in str(rows.get(sid, {}).get("Description_Lang_enUS")):
            bad.append(f"{sid}: description lacks 'Must be Hidden'")
    for sid, text in ((DT, "Movement slowed."), (RUPTURE, "Bleeding."), (GARROTE, "Bleeding."),
                      (INSULT, "Taunted."), (VEIL, "Dodge chance increased."), (SHROUD, "Hidden in shadows.")):
        if rows.get(sid, {}).get("AuraDescription_Lang_enUS") != text:
            bad.append(f"{sid}: aura text {rows.get(sid, {}).get('AuraDescription_Lang_enUS')!r}, expected {text!r}")
    return bad


def check_links_and_attrs(links: list[dict], custom_attrs: list[dict]) -> list[str]:
    bad = []
    got = [(int(x["spell_trigger"]), int(x["spell_effect"]), int(x["type"])) for x in links
           if abs(int(x["spell_trigger"])) == ENFORCER]
    if sorted(got) != sorted(LINKS):
        bad.append(f"Enforcer links {sorted(got)}, expected {sorted(LINKS)}")
    attrs = {int(a["spell_id"]): int(a["attributes"]) for a in custom_attrs}
    if attrs.get(ENFORCER) != 0x08000000:
        bad.append(f"{ENFORCER}: custom attr {attrs.get(ENFORCER)!r}, expected 0x08000000")
    if attrs.get(AMBUSH) != 0:
        bad.append(f"{AMBUSH}: custom attr {attrs.get(AMBUSH)!r}, expected 0 (behind flag cleared)")
    for sid in (FEINT, SHIV, INSULT):
        if sid in attrs:
            bad.append(f"{sid}: unexpected custom attr {attrs[sid]:#x}")
    return bad


def check_veil_proc(procs: list[dict]) -> list[str]:
    rows = [p for p in procs if int(p["SpellId"]) == VEIL]
    if len(rows) != 1:
        return [f"{VEIL}: {len(rows)} spell_proc rows, expected 1"]
    p = rows[0]
    want = {"ProcFlags": 0x28, "SpellTypeMask": 0, "SpellPhaseMask": 0, "HitMask": 0x2477, "AttributesMask": 0,
            "Cooldown": 0, "Charges": 5, "SpellFamilyName": 0, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0,
            "SpellFamilyMask2": 0}
    bad = [f"{VEIL}: spell_proc {k} = {p.get(k)!r}, expected {v}" for k, v in want.items() if int(p.get(k) or 0) != v]
    if float(p.get("Chance") or 0) != 100.0:
        bad.append(f"{VEIL}: spell_proc Chance {p.get('Chance')!r}, expected 100")
    return bad


def check_slas(slas: list[dict]) -> list[str]:
    by_id = {int(s["id"]): s for s in slas if 30790 <= int(s["id"]) <= 30799}
    bad = []
    if sorted(by_id) != sorted(SLA_ROWS):
        bad.append(f"SkillLineAbility ids {sorted(by_id)}, expected {sorted(SLA_ROWS)}")
    for sid, (line, spell_id) in SLA_ROWS.items():
        s = by_id.get(sid)
        if s is None:
            continue
        got = (int(s["skill_line"]), int(s["spell_id"]), int(s.get("class_mask") or 0),
               int(s.get("acquire_method") or 0))
        if got != (line, spell_id, 8, 0):
            bad.append(f"SLA {sid}: {got}, expected {(line, spell_id, 8, 0)}")
    return bad


def check_trainers(trainers: list[dict], rows: dict) -> list[str]:
    bad = []
    mine = {int(t["SpellId"]): t for t in trainers
            if int(t["TrainerId"]) == TRAINER and int(t["SpellId"]) in TRAINER_ROWS}
    for sid, level in TRAINER_ROWS.items():
        t = mine.get(sid)
        if t is None:
            bad.append(f"{sid}: no trainer {TRAINER} row")
            continue
        if int(t["ReqLevel"]) != level:
            bad.append(f"{sid}: trainer ReqLevel {t['ReqLevel']}, expected {level}")
        r = rows.get(sid)
        if r is not None and _i(r, "SpellLevel") != int(t["ReqLevel"]):
            bad.append(f"{sid}: SpellLevel {r.get('SpellLevel')!r} != trainer ReqLevel {t['ReqLevel']}")
    for t in trainers:
        if int(t["SpellId"]) in TRAINER_ROWS and int(t["TrainerId"]) != TRAINER:
            bad.append(f"{t['SpellId']}: taught by trainer {t['TrainerId']}, only {TRAINER} allowed")
    return bad


def check_scripts(names: list[dict], removals: list[dict]) -> list[str]:
    bound = {(int(n["spell_id"]), n["ScriptName"]) for n in names}
    bad = []
    for want in ((SHIV, "spell_rog_shiv_rework"), (AMBUSH, "spell_rog_ambush"),
                 (203723, "spell_rog_ghostly_veil"), (51723, "spell_rog_fan_of_knives")):
        if want not in bound:
            bad.append(f"script {want[1]} not bound to {want[0]}")
    if not any(int(r["spell_id"]) == OLD_SHIV and r["ScriptName"] == "spell_rog_shiv" for r in removals):
        bad.append(f"{OLD_SHIV}: spell_rog_shiv is not unbound")
    if any(sid == OLD_SHIV for sid, _n in bound):
        bad.append(f"{OLD_SHIV}: still bound to a script by the rogue package")
    return bad


def check_talent_303(retired: list[dict], talents: list[dict]) -> list[str]:
    bad = []
    if not any(int(r["id"]) == 303 for r in retired):
        bad.append("talent 303 is not retired")
    rows = [t for t in talents if int(t["id"]) == 303]
    if len(rows) != 1:
        bad.append(f"talent 303 emitted {len(rows)} times, expected once")
    for t in rows:
        if int(t["tab_id"]) != 60800:
            bad.append(f"talent 303 on tab {t['tab_id']}, expected 60800")
        if t.get("rank_spell_ids"):
            bad.append(f"talent 303 still ranks {t['rank_spell_ids']}")
    return bad


def check_potency_rows(rows: dict, bonus: list[dict], corrections: list[dict]) -> list[str]:
    """DT is on potency: it has a spell_bonus_data row (RAP coefficient) and a correction row (the DBC eff0
    per-combo-point points are checked in the row expectations). SS / BS / Ambush / Rupture are weapon or
    AP-less, so no bonus row."""
    bad = []
    keyed = {int(b.get("entry", b.get("spell_id", 0))): b for b in bonus}
    if DT not in keyed:
        bad.append(f"{DT}: no spell_bonus_data row (not on potency)")
    if DT in keyed and not float(keyed[DT].get("ap_bonus") or 0) > 0:
        bad.append(f"{DT}: spell_bonus_data ap_bonus {keyed[DT].get('ap_bonus')!r} is not positive")
    if not any(int(c.get("spell_id", c.get("entry", 0))) == DT for c in corrections):
        bad.append(f"{DT}: no potency correction row")
    return bad


def check_spelldurations(durations: list[dict], rows: dict) -> list[str]:
    """Rupture's DurationIndex row is 4000 / 24000 (min + (max - min) x cp / 5 = 8 / 12 / 16 / 20 / 24 s)."""
    index = _i(rows.get(RUPTURE, {}), "DurationIndex")
    mine = [d for d in durations if int(d["ID"]) == index]
    if len(mine) != 1:
        return [f"{RUPTURE}: DurationIndex {index} has {len(mine)} SpellDuration rows"]
    d = mine[0]
    if (int(d["Duration"]), int(d["MaxDuration"])) != (4000, 24000):
        return [f"{RUPTURE}: SpellDuration {index} is {d['Duration']}/{d['MaxDuration']}, expected 4000/24000"]
    return []


# ---- tooltips vs simulate_value -------------------------------------------------------------------------------------

def tooltip_expr(description: str) -> str | None:
    """The inside of the (single) `${...}` block of a description, brace-balanced."""
    start = (description or "").find("${")
    if start < 0:
        return None
    depth = 0
    for pos in range(start + 1, len(description)):
        ch = description[pos]
        depth += ch == "{"
        depth -= ch == "}"
        if depth == 0:
            return description[start + 2:pos]
    return None


def eval_tooltip(expr: str, level: float, ap: float = 0.0, rap: float = 0.0) -> float:
    py = expr.replace("$max", "max").replace("$PL", "L").replace("$AP", "AP").replace("$RAP", "RAP")
    return float(eval(py, {"__builtins__": {}, "max": max}, {"L": level, "AP": ap, "RAP": rap}))  # noqa: S307


_SDV_TAIL = re.compile(r"\*\$<\w+>$")


def _strip_sdv(expr: str) -> str:
    """S1a attaches tooltip_vars (SDV 1322 / 1323: Blood Spatter / Seal Fate multipliers) to Rupture and Deadly Throw:
    `${$max(...)*$<name>}`. The variable is 1 with no talent, so the oracle evaluates the bare `$max(...)`."""
    return _SDV_TAIL.sub("", expr)


def _balanced_single_max(expr: str) -> bool:
    """The client drops a top-level `+` outside every `$max()`: the whole expression is one `$max( ... )` call."""
    if not expr.startswith("$max(") or not expr.endswith(")"):
        return False
    depth = 0
    for pos, ch in enumerate(expr):
        depth += ch == "("
        depth -= ch == ")"
        if ch == ")" and depth == 0 and pos != len(expr) - 1:
            return False
    return depth == 0


_DT_FLAT = potency.resolve(
    potency.PotencyEffect(ap_potency=14.625, kind=potency.KIND_DIRECT, t_ms=1500.0), spell_level=36)
_RUPTURE_TICK = potency.resolve(
    potency.PotencyEffect(base_potency=19.605, kind=potency.KIND_PERIODIC, t_ms=2000.0), spell_level=20)
_DT_CP_LINE = 5 * 61.7925          # 0-verify item 7: cp_line 61.7925 per point, 5 points
_DT_CP_AP = 0.495                  # cp AP 0.099 x 5, token $AP (melee)
_DT_FLAT_AP = 0.06268              # spell_bonus_data.ap_bonus of ap_potency 14.625, token $RAP
_RUP_AP_TICK = 0.0375             # ap_potency 6.5625 per 2 s tick (the old 5-point AP part, user 2026-10-27)


def dt_oracle(level: int, ap: float, rap: float) -> float:
    """Mid-roll (+5%) 5-combo-point average: flat via simulate_value, the cp line and both AP terms from the potency "
    "table."""
    flat = potency.simulate_value(_DT_FLAT, level, 36) * (1.0 + _DT_FLAT.variance_pct / 200.0)
    return flat + _DT_CP_LINE + _DT_FLAT_AP * rap + _DT_CP_AP * ap


def rupture_oracle(level: int, ap: float) -> float:
    """One tick, whatever the combo points (only the duration grows with them)."""
    return potency.simulate_value(_RUPTURE_TICK, level, 20) + _RUP_AP_TICK * ap


def check_tooltips(dt_desc: str, rupture_desc: str) -> list[str]:
    bad = []
    dt, ru = tooltip_expr(dt_desc), tooltip_expr(rupture_desc)
    dt = _strip_sdv(dt) if dt is not None else None
    ru = _strip_sdv(ru) if ru is not None else None
    if dt is None:
        bad.append(f"{DT}: no ${{...}} block in the description")
    else:
        if not _balanced_single_max(dt):
            bad.append(f"{DT}: tooltip is not a single top-level $max()")
        if "$RAP" not in dt or "$AP" not in dt.replace("$RAP", ""):
            bad.append(f"{DT}: tooltip must read $RAP (flat) and $AP (combo-point term)")
        try:
            for level in (36, 40, 50, 60, 70, 80):
                got, want = eval_tooltip(dt, level, 100, 200), dt_oracle(level, 100, 200)
                if abs(got - want) > 1.5:
                    bad.append(f"{DT}: tooltip at L{level} = {got:.2f}, simulate_value says {want:.2f}")
            if abs(eval_tooltip(dt, 60) - 347.81) > 0.5:
                bad.append(f"{DT}: L60 5-cp value {eval_tooltip(dt, 60):.2f}, "
                           "expected 347.81 (345.96 min + 5% mid-roll)")
            ap_term = eval_tooltip(dt, 60, ap=100) - eval_tooltip(dt, 60)
            rap_term = eval_tooltip(dt, 60, rap=100) - eval_tooltip(dt, 60)
            if abs(ap_term - 49.5) > 0.05 or abs(rap_term - 6.27) > 0.05:
                bad.append(f"{DT}: AP/RAP terms per 100 are {ap_term:.2f}/{rap_term:.2f}, expected 49.50/6.27")
        except Exception as exc:   # a malformed expression is a failure, not a crash
            bad.append(f"{DT}: tooltip does not evaluate: {exc!r}")
    if ru is None:
        bad.append(f"{RUPTURE}: no ${{...}} block in the description")
    else:
        if not _balanced_single_max(ru):
            bad.append(f"{RUPTURE}: tooltip is not a single top-level $max()")
        if "$AP" not in ru or "$RAP" in ru:
            bad.append(f"{RUPTURE}: tooltip must read $AP (melee) only")
        try:
            for level in (20, 24, 25, 40, 60, 80):
                got, want = eval_tooltip(ru, level, 100), rupture_oracle(level, 100)
                if abs(got - want) > 1.0:
                    bad.append(f"{RUPTURE}: tooltip at L{level} = {got:.2f}, simulate_value says {want:.2f}")
            if abs(eval_tooltip(ru, 60) - 70.0) > 0.3:
                bad.append(f"{RUPTURE}: L60 tick {eval_tooltip(ru, 60):.2f}, expected 70.0 (12 ticks = 840.1)")
            if abs(eval_tooltip(ru, 60, ap=100) - eval_tooltip(ru, 60) - 3.75) > 0.05:
                bad.append(f"{RUPTURE}: AP term per 100 is not 3.75 (0.0375 x AP per tick)")
        except Exception as exc:
            bad.append(f"{RUPTURE}: tooltip does not evaluate: {exc!r}")
        if "every 2 sec" not in rupture_desc:
            bad.append(f"{RUPTURE}: description does not state the tick (every 2 sec)")
        if "1 point: 8 sec" not in rupture_desc or "5 points: 24 sec" not in rupture_desc:
            bad.append(f"{RUPTURE}: description lacks the 8..24 sec duration ladder")
    return bad


# ---- real data ----------------------------------------------------------------------------------------------------

_CACHE: dict = {}


def _data():
    if not _CACHE:
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        spell_table_index = spell_tables.load_spell_table_index()
        creature_table_index = spell_tables.load_creature_table_index()
        package = registry.load_class_package(
            ROGUE_DIR, ids_cfg=ids_cfg, trainer_index=trainer_state.load_trainer_index(),
            existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
            shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
            existing_creature_rows={int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")},
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.load_dsl_live_data(),
        )
        reuse = ReuseContext({}, ids_cfg)
        rows = [build.build_spell_row(e, reuse) for e in package.spells]
        by_id = {int(r["ID"]): r for r in rows}
        idx = {
            "infinite": reuse.duration_index(0), "d3000": reuse.duration_index(3000),
            "d6000": reuse.duration_index(6000), "d15000": reuse.duration_index(15000),
            "d4000_24000": reuse.duration_index(4000, 24000), "r20": reuse.range_index(20.0),
            "r25": reuse.range_index(25.0), "melee": _i(by_id[SS], "RangeIndex"),
        }
        _CACHE.update(package=package, rows=by_id, idx=idx,
                      durations=list(reuse.reserved_rows.get("spellduration", [])))
    return _CACHE


class RogueRG0bDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_new_and_reworked_rows(self):
        d = _data()
        self.assertClean(check_rows(d["rows"], *expectations(d["idx"])))

    def test_no_never_bits(self):
        self.assertClean(check_no_never_bits(_data()["rows"]))

    def test_fok_combo_effect_targets(self):
        self.assertClean(check_fok_combo(_data()["rows"]))

    def test_texts(self):
        self.assertClean(check_texts(_data()["rows"]))

    def test_links_and_custom_attrs(self):
        p = _data()["package"]
        self.assertClean(check_links_and_attrs(p.linked_spells, p.custom_attrs))

    def test_veil_proc(self):
        self.assertClean(check_veil_proc(_data()["package"].spell_procs))

    def test_skill_line_abilities(self):
        self.assertClean(check_slas(_data()["package"].skill_line_abilities))

    def test_trainers(self):
        d = _data()
        self.assertClean(check_trainers(d["package"].trainer_spells, d["rows"]))

    def test_scripts(self):
        p = _data()["package"]
        self.assertClean(check_scripts(p.spell_script_names, p.script_removals))

    def test_talent_303_retired(self):
        p = _data()["package"]
        self.assertClean(check_talent_303(p.retired_talents, p.talents))

    def test_potency_rows(self):
        d = _data()
        self.assertClean(check_potency_rows(d["rows"], d["package"].spell_bonus_data, d["package"].potency_corrections))

    def test_rupture_duration_row(self):
        d = _data()
        self.assertClean(check_spelldurations(d["durations"], d["rows"]))

    def test_tooltips_vs_simulate_value(self):
        rows = _data()["rows"]
        self.assertClean(check_tooltips(rows[DT]["Description_Lang_enUS"], rows[RUPTURE]["Description_Lang_enUS"]))


# ---- negative fixtures: every check must fire on a minimal bad input -----------------------------------------------

IDX = {"infinite": 21, "d3000": 31, "d6000": 32, "d15000": 33, "d4000_24000": 34, "r20": 41, "r25": 42, "melee": 2}


def _good_rows() -> dict:
    """A built-rows fixture that satisfies every row expectation (exact values, set bits; clear bits stay 0)."""
    exact, must_set, _clear = expectations(IDX)
    rows: dict[int, dict] = {}
    for sid, cols in exact.items():
        rows.setdefault(sid, {"ID": sid}).update({c: (v & 0xFFFFFFFF if v < 0 else v) for c, v in cols.items()})
    for sid, cols in must_set.items():
        row = rows.setdefault(sid, {"ID": sid})
        for col, bits in cols.items():
            row[col] = _u32(row.get(col)) | bits
    return rows


def _good_descs() -> tuple[str, str]:
    dt = ("causing ${$max($max(0.0627*$RAP+308.9625+0.495*$AP,2.4223+0.2395*$PL+0.0627*$RAP+308.9625+0.495*$AP),"
          "0.8775*$max(0,$PL-15.7265)+0.0627*$RAP+308.9625+0.495*$AP)} Physical damage.")
    ru = ("causes ${$max($max(0.0375*$AP,4.3294+0.428*$PL+0.0375*$AP),1.5684*$max(0,$PL-15.3685)+0.0375*$AP)} "
          "Physical damage every 2 sec. Lasts longer per combo point: 1 point: 8 sec, 5 points: 24 sec.")
    return dt, ru


class RogueRG0bNegativeTest(unittest.TestCase):
    def test_rows_clean_fixture(self):
        self.assertEqual(check_rows(_good_rows(), *expectations(IDX)), [])

    def test_every_exact_expectation_can_fail(self):
        exact, ms, mc = expectations(IDX)
        for sid, cols in exact.items():
            for col, want in cols.items():
                rows = _good_rows()
                rows[sid][col] = (_u32(want) ^ 0x4) if want else 0x4
                self.assertGreaterEqual(len(check_rows(rows, exact, ms, mc)), 1, (sid, col))

    def test_every_set_bit_expectation_can_fail(self):
        exact, ms, mc = expectations(IDX)
        for sid, cols in ms.items():
            for col, bits in cols.items():
                rows = _good_rows()
                rows[sid][col] = _u32(rows[sid].get(col)) & ~bits
                self.assertGreaterEqual(len(check_rows(rows, exact, ms, mc)), 1, (sid, col))

    def test_every_clear_bit_expectation_can_fail(self):
        exact, ms, mc = expectations(IDX)
        for sid, cols in mc.items():
            for col, bits in cols.items():
                rows = _good_rows()
                rows[sid][col] = _u32(rows[sid].get(col)) | bits
                self.assertGreaterEqual(len(check_rows(rows, exact, ms, mc)), 1, (sid, col))

    def test_missing_row(self):
        rows = _good_rows()
        del rows[DT]
        self.assertEqual(len(check_rows(rows, *expectations(IDX))), 1)

    def test_specific_hazards(self):
        """The named hazards in the handoff, each by itself."""
        exact, ms, mc = expectations(IDX)
        for sid, col, val in ((SHIV, "AttributesEx3", 0x400 | 0x10000), (SHIV, "AttributesEx3", 0x400 | 0x1000000),
                              (SHIV, "AttributesEx2", 0x20000000), (SS, "MaxLevel", 80), (GS, "RecoveryTime", 20000),
                              (GS, "SpellClassMask_1", 0x44000000), (AMBUSH, "RangeIndex", 2),
                              (DT, "Effect_1", 3), (DT, "EffectPointsPerCombo_1", 105), (FEINT, "Category", 82),
                              (FEINT, "Effect_2", 6), (FEINT, "DurationIndex", 30101), (RUPTURE, "DurationIndex", 553),
                              (ENFORCER, "RecoveryTime", 0), (INSULT, "CategoryRecoveryTime", 10000),
                              (SHROUD, "RecoveryTime", 300000), (VEIL, "ProcCharges", 3)):
            rows = _good_rows()
            rows[sid][col] = val
            self.assertGreaterEqual(len(check_rows(rows, exact, ms, mc)), 1, (sid, col, val))

    def test_never_bits(self):
        rows = {sid: {"ID": sid} for sid in NEW_IDS + (GS,)}
        rows[SHIV]["SpellClassMask_1"] = 0x20000000
        rows[GS]["SpellClassMask_1"] = 0x40000000
        self.assertEqual(check_no_never_bits(rows), [])
        for sid, col, bit in ((SHIV, "SpellClassMask_1", 0x800), (SHIV, "SpellClassMask_1", 0x400000),
                              (SHIV, "SpellClassMask_1", 0x2000000), (SHIV, "SpellClassMask_1", 0x4000000),
                              (SHIV, "SpellClassMask_1", 0x10000), (SHIV, "SpellClassMask_1", 0x20000),
                              (SHIV, "SpellClassMask_1", 0x100000), (SHIV, "SpellClassMask_2", 0x2),
                              (SHIV, "SpellClassMask_2", 0x4), (SHIV, "SpellClassMask_2", 0x8),
                              (SHIV, "SpellClassMask_2", 0x40000), (ENFORCER, "SpellClassMask_2", 0x80000),
                              (GS, "SpellClassMask_1", 0x4000000), (GS, "SpellClassMask_1", 0x10000),
                              (TELEPORT, "EffectSpellClassMaskA_1", 0x800)):
            bad = {k: dict(v) for k, v in rows.items()}
            bad[sid][col] = _u32(bad[sid].get(col)) | bit
            self.assertEqual(len(check_no_never_bits(bad)), 1, (sid, col, bit))
        self.assertEqual(len(check_no_never_bits({k: v for k, v in rows.items() if k != INSULT})), 1)

    def test_fok_combo(self):
        good = {FOK: {"ImplicitTargetA_1": 18, "ImplicitTargetA_2": 18, "ImplicitTargetB_1": 16,
                      "ImplicitTargetB_2": 16, "EffectRadiusIndex_1": 8, "EffectRadiusIndex_2": 8}}
        self.assertEqual(check_fok_combo(good), [])
        self.assertEqual(len(check_fok_combo({})), 1)
        for col, val in (("ImplicitTargetA_2", 6), ("ImplicitTargetB_2", 0), ("EffectRadiusIndex_2", 0)):
            self.assertGreaterEqual(len(check_fok_combo({FOK: {**good[FOK], col: val}})), 1, col)
        zeroed = {**good[FOK], "EffectRadiusIndex_1": 0, "EffectRadiusIndex_2": 0}
        self.assertEqual(len(check_fok_combo({FOK: zeroed})), 1)

    def test_texts(self):
        rows = {AMBUSH: {"Description_Lang_enUS": "x Must be Hidden."},
                GARROTE: {"Description_Lang_enUS": "Must be Hidden",
                          "AuraDescription_Lang_enUS": "Bleeding."},
                CHEAP_SHOT: {"Description_Lang_enUS": "Must be Hidden."},
                DT: {"AuraDescription_Lang_enUS": "Movement slowed."},
                RUPTURE: {"AuraDescription_Lang_enUS": "Bleeding."},
                INSULT: {"AuraDescription_Lang_enUS": "Taunted."},
                VEIL: {"AuraDescription_Lang_enUS": "Dodge chance increased."},
                SHROUD: {"AuraDescription_Lang_enUS": "Hidden in shadows."}}
        self.assertEqual(check_texts(rows), [])
        self.assertEqual(len(check_texts({**rows, AMBUSH: {"Description_Lang_enUS": "Ambush."}})), 1)
        self.assertEqual(len(check_texts({**rows, DT: {"AuraDescription_Lang_enUS": ""}})), 1)
        self.assertEqual(len(check_texts({**rows, SHROUD: {"AuraDescription_Lang_enUS": "Hidden in shadows"}})), 1)

    def test_links_and_attrs(self):
        links = [{"spell_trigger": a, "spell_effect": b, "type": t} for a, b, t in sorted(LINKS)]
        attrs = [{"spell_id": ENFORCER, "attributes": 0x08000000}, {"spell_id": AMBUSH, "attributes": 0}]
        self.assertEqual(check_links_and_attrs(links, attrs), [])
        self.assertEqual(len(check_links_and_attrs(links[1:], attrs)), 1)
        extra = [{"spell_trigger": ENFORCER, "spell_effect": 1, "type": 2}]
        self.assertEqual(len(check_links_and_attrs(links + extra, attrs)), 1)
        self.assertEqual(len(check_links_and_attrs(links[:-1] + [{**links[-1], "type": 0}], attrs)), 1)
        self.assertEqual(len(check_links_and_attrs(links, attrs[1:])), 1)
        self.assertEqual(len(check_links_and_attrs(links, [{**attrs[0], "attributes": 0x06000000}, attrs[1]])), 1)
        self.assertEqual(len(check_links_and_attrs(links, [attrs[0], {**attrs[1], "attributes": 0x20000}])), 1)
        self.assertEqual(len(check_links_and_attrs(links, attrs + [{"spell_id": FEINT, "attributes": 1}])), 1)

    def test_veil_proc(self):
        good = {"SpellId": VEIL, "ProcFlags": 0x28, "SpellTypeMask": 0, "SpellPhaseMask": 0, "HitMask": 0x2477,
                "AttributesMask": 0, "Cooldown": 0, "Charges": 5, "Chance": 100.0, "SpellFamilyName": 0,
                "SpellFamilyMask0": 0, "SpellFamilyMask1": 0, "SpellFamilyMask2": 0}
        self.assertEqual(check_veil_proc([good]), [])
        self.assertEqual(len(check_veil_proc([])), 1)
        self.assertEqual(len(check_veil_proc([good, good])), 1)
        for col, val in (("ProcFlags", 0x2A), ("SpellTypeMask", 1), ("SpellPhaseMask", 2), ("HitMask", 0x3),
                         ("AttributesMask", 1), ("Cooldown", 1000), ("Charges", 3), ("Chance", 50.0),
                         ("SpellFamilyName", 8), ("SpellFamilyMask0", 2)):
            self.assertEqual(len(check_veil_proc([{**good, col: val}])), 1, col)

    def test_slas(self):
        good = [{"id": i, "skill_line": line, "spell_id": s, "class_mask": 8, "acquire_method": 0}
                for i, (line, s) in SLA_ROWS.items()]
        self.assertEqual(check_slas(good), [])
        self.assertGreaterEqual(len(check_slas(good[1:])), 1)
        self.assertGreaterEqual(len(check_slas(good + [{**good[0], "id": 30794}])), 1)
        for col, val in (("skill_line", 40), ("spell_id", 5), ("class_mask", 0), ("acquire_method", 1)):
            self.assertEqual(len(check_slas([{**good[0], col: val}] + good[1:])), 1, col)

    def test_trainers(self):
        rows = {sid: {"ID": sid, "SpellLevel": lv} for sid, lv in TRAINER_ROWS.items()}
        good = [{"TrainerId": TRAINER, "SpellId": s, "ReqLevel": lv} for s, lv in TRAINER_ROWS.items()]
        self.assertEqual(check_trainers(good, rows), [])
        self.assertEqual(len(check_trainers(good[1:], rows)), 1)
        self.assertEqual(len(check_trainers([{**good[0], "ReqLevel": 11}] + good[1:], rows)), 2)  # level + SpellLevel
        self.assertEqual(len(check_trainers(good + [{"TrainerId": 9, "SpellId": GS, "ReqLevel": 10}], rows)), 1)
        self.assertEqual(len(check_trainers(good, {**rows, DT: {"ID": DT, "SpellLevel": 64}})), 1)
        self.assertEqual(len(check_trainers(good, {**rows, SHIV: {"ID": SHIV, "SpellLevel": 1}})), 1)

    def test_scripts(self):
        names = [{"spell_id": SHIV, "ScriptName": "spell_rog_shiv_rework"},
                 {"spell_id": AMBUSH, "ScriptName": "spell_rog_ambush"},
                 {"spell_id": 203723, "ScriptName": "spell_rog_ghostly_veil"},
                 {"spell_id": 51723, "ScriptName": "spell_rog_fan_of_knives"}]
        rem = [{"spell_id": OLD_SHIV, "ScriptName": "spell_rog_shiv"}]
        self.assertEqual(check_scripts(names, rem), [])
        self.assertEqual(len(check_scripts(names[1:], rem)), 1)
        self.assertEqual(len(check_scripts(names[:2] + names[3:], rem)), 1)
        self.assertEqual(len(check_scripts(names[:3], rem)), 1)
        self.assertEqual(len(check_scripts(names, [])), 1)
        self.assertEqual(len(check_scripts(names, [{"spell_id": OLD_SHIV, "ScriptName": "other"}])), 1)
        self.assertEqual(len(check_scripts(names + [{"spell_id": OLD_SHIV, "ScriptName": "spell_rog_shiv"}], rem)), 1)

    def test_talent_303(self):
        talents = [{"id": 303, "tab_id": 60800, "rank_spell_ids": []}]
        self.assertEqual(check_talent_303([{"id": 303}], talents), [])
        self.assertEqual(len(check_talent_303([], talents)), 1)
        self.assertEqual(len(check_talent_303([{"id": 303}], [{**talents[0], "tab_id": 183}])), 1)
        self.assertEqual(len(check_talent_303([{"id": 303}], [{**talents[0], "rank_spell_ids": [14278]}])), 1)
        self.assertEqual(len(check_talent_303([{"id": 303}], talents + talents)), 1)
        self.assertEqual(len(check_talent_303([{"id": 303}], [])), 1)

    def test_potency_rows(self):
        bonus = [{"entry": DT, "ap_bonus": 0.06}, {"entry": 1, "ap_bonus": 0.1}]
        corr = [{"spell_id": DT}]
        self.assertEqual(check_potency_rows({}, bonus, corr), [])
        self.assertEqual(len(check_potency_rows({}, bonus[1:], corr)), 1)
        self.assertEqual(len(check_potency_rows({}, [{**bonus[0], "ap_bonus": 0.0}] + bonus[1:], corr)), 1)
        self.assertEqual(len(check_potency_rows({}, bonus, [])), 1)

    def test_rupture_duration_row(self):
        rows = {RUPTURE: {"DurationIndex": 34}}
        self.assertEqual(check_spelldurations([{"ID": 34, "Duration": 4000, "MaxDuration": 24000}], rows), [])
        self.assertEqual(len(check_spelldurations([{"ID": 34, "Duration": 6000, "MaxDuration": 16000}], rows)), 1)
        self.assertEqual(len(check_spelldurations([{"ID": 34, "Duration": 4000, "MaxDuration": 4000}], rows)), 1)
        self.assertEqual(len(check_spelldurations([], rows)), 1)

    def test_tooltips(self):
        dt, ru = _good_descs()
        self.assertEqual(check_tooltips(dt, ru), [])
        self.assertEqual(tooltip_expr("no block"), None)
        for old, new in (("308.9625", "300"), ("0.495*$AP", "0.5*$AP"), ("0.0627*$RAP", "0.0627*$AP"),
                         ("0.8775*$max", "1.9*$max")):
            self.assertGreaterEqual(len(check_tooltips(dt.replace(old, new), ru)), 1, old)
        for old, new in (("1.5684", "1.2"), ("0.0375*$AP", "0.03*$AP"), ("0.0375*$AP", "0.0375*$RAP"),
                         ("4.3294+0.428", "24.3294+0.428"), ("every 2 sec", "over time")):
            self.assertGreaterEqual(len(check_tooltips(dt, ru.replace(old, new))), 1, old)
        self.assertGreaterEqual(len(check_tooltips("no block", ru)), 1)
        self.assertGreaterEqual(len(check_tooltips(dt, "no block")), 1)
        # a top-level `+` outside the $max() is dropped by the client
        self.assertGreaterEqual(len(check_tooltips(dt.replace("${$max(", "${5+$max(", 1), ru)), 1)
        self.assertGreaterEqual(len(check_tooltips(dt, ru.replace("1 point: 8 sec, ", ""))), 1)
        self.assertGreaterEqual(len(check_tooltips(dt.replace("$max($max(", "$max($max(garbage", 1), ru)), 1)
        # S1a: a trailing `*$<var>` talent multiplier is allowed (and only that), on both tooltips
        mult_dt, mult_ru = dt.replace("}", "*$<seal>}"), ru.replace("} Physical", "*$<mult>} Physical")
        self.assertEqual(check_tooltips(mult_dt, mult_ru), [])
        self.assertGreaterEqual(len(check_tooltips(dt.replace("}", "*$<seal>+1}"), ru)), 1)
        self.assertGreaterEqual(len(check_tooltips(dt.replace("}", "*2}"), ru)), 1)
        self.assertGreaterEqual(len(check_tooltips(dt, ru.replace("} Physical", "*$<mult>*$<x>} Physical"))), 1)


if __name__ == "__main__":
    unittest.main()
