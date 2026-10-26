"""
Death Knight DK0b data gate (death-knight-rework DK0b-HANDOFF row A6, DK0b-WP-BRIEF).

Same shape as lib/test_deathknight_dk0a.py: the real deathknight DSL package is loaded and every check runs on the BUILT
rows (stock base + DSL + raw_overrides via `build.build_spell_row`), so a stale pulled raw_overrides key that wins over
the DSL fails here too. Each check is a pure function that returns problem strings, with a negative fixture below.
An id no agent has declared yet is reported by `test_required_ids_declared` and skipped by the other checks.

  1. Rune frames (53344, 53343, 203040/42/44/49): Attributes exactly 0x10000000, AttributesEx3 0x100000 (no 0x80 /
     0x20 / 0x10000), no stale AttributesEx 0x400 / AttributesEx2 0x2000 / Targets 0x10 / InterruptFlags, instant cast,
     EquippedItemClass -1, RequiresSpellFocus 0, no ENCHANT_ITEM effect, SpellLevel (= BaseLevel) = the trainer level.
  2. spell_group 1271 members + rule 1.
  3. Rune spell_proc rows (flags, phase 2, chance / ppm, cooldown, boiling-blight mask) and phase 2 on every DONE row.
  4. 53365 Unholy Strength eff1 is APPLY_AURA 20 (not the instant HEAL_PCT).
  5. Obliterate 203054 (percent first, flat second, nothing in the third slot, rune cost 2600 = frost 1 / 15 RP,
     d1 b17 only, SpellLevel 20) and the guard 203055 (icon 2710, DUMMY, hidden passive).
  6. Runic Focus 61455 mask is a superset of the stock mask plus RUNIC_FOCUS_READ_ADD.
  7. Blood Plague 55078 / Frost Fever 55095 DefenseType 1.
  8. Raise Dead 48289 has no reagent, and 46584/46585/52150 tooltips do not mention Corpse Dust.
  9. Minion mirrors 203056-203058 are ALWAYS_HIT (AttributesEx3 0x40000).
 10. Frost Vulnerability 51714 reads _masks.FROST_VULN_READ_S2 (never zero); Final Roar burst 203291 is exempt with
     Razor Frost; school-switched strikes (Obliterate / Heart Strike / Plague Strike) are covered by the helper term,
     so they are NOT in the mask.
 11. No DK0b row carries a `_masks.FORBIDDEN_*` bit (stock-kept bits exempt).
 12. Annihilation 51468/51472/51473 effect 1 dummy stored 99 (live 100).
 13. Bone Shield 49222 spell_proc hit mask 0x403.

Run: cd apps/dbc-tools && .venv/bin/python3 -m pytest lib/test_deathknight_dk0b.py -q -p no:cacheprovider
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.test_deathknight_dk0a import _data, _hex, _u32, m, spell_mask  # noqa: E402

DEATH_KNIGHT_TRAINER = 13

FALLEN_CRUSADER, RAZORICE = 53344, 53343
EXSANGUINATION, BOILING_BLIGHT, APOCALYPSE, UNENDING_THIRST = 203040, 203042, 203044, 203049
RUNES = (FALLEN_CRUSADER, RAZORICE, EXSANGUINATION, BOILING_BLIGHT, APOCALYPSE, UNENDING_THIRST)
RUNE_LEVELS = {FALLEN_CRUSADER: 6, RAZORICE: 20, EXSANGUINATION: 20, BOILING_BLIGHT: 20, APOCALYPSE: 30,
               UNENDING_THIRST: 40}
UNHOLY_STRENGTH = 53365
FROST_VULNERABILITY = 51714
OBLITERATE, OBLITERATE_GUARD = 203054, 203055
OBLITERATE_LEVEL = 20
OBLITERATE_RUNE_COST = 2600
RUNIC_FOCUS = 61455
BLOOD_PLAGUE, FROST_FEVER = 55078, 55095
RAISE_DEAD = 48289
MIRRORS = (203056, 203057, 203058)
ANNIHILATION = (51468, 51472, 51473)
BONE_SHIELD = 49222
RUNE_GROUP = 1271
RUNIC_FOCUS_STOCK_MASK = (0x80040202, 0x10022, 0x9)

DK0B_IDS = (*RUNES, UNHOLY_STRENGTH, FROST_VULNERABILITY, OBLITERATE, OBLITERATE_GUARD, RUNIC_FOCUS, BLOOD_PLAGUE,
            FROST_FEVER, RAISE_DEAD, *MIRRORS, *range(203041, 203044), *range(203045, 203052), 203052, 203053)
REQUIRED_IDS = (*RUNES, UNHOLY_STRENGTH, FROST_VULNERABILITY, OBLITERATE, OBLITERATE_GUARD, RUNIC_FOCUS, BLOOD_PLAGUE,
                FROST_FEVER, RAISE_DEAD, *MIRRORS, *ANNIHILATION, BONE_SHIELD)
# Stock-kept forbidden bits (own SpellClassMask), per row: the disease DoTs keep d2 b1 and d1 b11 (stock 0x800).
FORBIDDEN_EXEMPT = {BLOOD_PLAGUE: (0, m.FORBIDDEN_D1_B11, m.FORBIDDEN_D2_B1),
                    FROST_FEVER: (0, m.FORBIDDEN_D1_B11, m.FORBIDDEN_D2_B1)}

ATTR0_RUNE_FRAME = 0x10000000
ATTR3_DEATH_PERSISTENT = 0x100000
ATTR3_ALWAYS_HIT = 0x40000
ATTR3_BURST = 0x50000  # ALWAYS_HIT | SUPPRESS_CASTER_PROCS
BOILING_BLIGHT_BURST = 203043
RAZOR_FROST = 203051
FINAL_ROAR_BURST = 203291  # S2: percent-of-damage burst, inert under Razorice
SCHOOL_SWITCHED_STRIKES = (OBLITERATE, 55050, 45462)  # Heart Strike, Plague Strike
ATTR2_IGNORE_LOS = 0x4
FAMILY_DEATHKNIGHT = 15
SCHOOL_FROST = 16
DAMAGE_EFFECT_TYPES = (2, 31, 58, 121)  # SCHOOL_DAMAGE, WEAPON_PERCENT_DAMAGE, WEAPON_DAMAGE, NORMALIZED_WEAPON_DMG
AURA_PERIODIC_DAMAGE = 3
RUNIC_FOCUS_LINKS = (203052, 203053, 203055)
AURA_DUMMY = 4
EFFECT_APPLY_AURA = 6
EFFECT_WEAPON_PERCENT_DAMAGE = 31
EFFECT_ENCHANT_ITEM = 53
EFFECT_NORMALIZED_WEAPON_DMG = 121
AURA_OBS_MOD_HEALTH = 20
POWER_RUNE = 5

PROC_MELEE = 0x4 | 0x10  # DONE_MELEE_AUTO_ATTACK | DONE_SPELL_MELEE_DMG_CLASS
PROC_PERIODIC = 0x40000
PROC_THIRST = PROC_MELEE | 0x10000 | PROC_PERIODIC
PHASE_HIT = 2
TYPE_DAMAGE = 1
HIT_CRITICAL = 2
PROC_DONE_MASK = 0x1555554  # every PROC_FLAG_DONE_* bit that a rune reads; any overlap means a DONE row

# spell_id -> (proc_flags, family_name, family_mask, spell_type_mask, hit_mask, ppm, chance, cooldown_ms)
RUNE_PROCS = {
    FALLEN_CRUSADER: (PROC_MELEE, 0, (0, 0, 0), 0, 0, 2.0, 0.0, 0),
    RAZORICE: (PROC_MELEE, 0, (0, 0, 0), 0, 0, 0.0, 100.0, 0),
    EXSANGUINATION: (PROC_MELEE, 0, (0, 0, 0), 0, 0, 0.0, 15.0, 1000),
    BOILING_BLIGHT: (PROC_PERIODIC, 15, m.DISEASES, TYPE_DAMAGE, 0, 0.0, 10.0, 1000),
    APOCALYPSE: (PROC_MELEE, 0, (0, 0, 0), 0, 0, 3.0, 0.0, 10000),
    UNENDING_THIRST: (PROC_THIRST, 0, (0, 0, 0), 0, HIT_CRITICAL, 0.0, 20.0, 30000),
}


def _fmt(value) -> str:
    return f"{value:#x}" if isinstance(value, int) else repr(value)


def _effects(row: dict) -> list[tuple[int, int, int]]:
    """(effect type, aura, stored base points) per used slot."""
    out = []
    for i in (1, 2, 3):
        effect = int(row.get(f"Effect_{i}") or 0)
        if effect:
            out.append((effect, int(row.get(f"EffectAura_{i}") or 0), int(row.get(f"EffectBasePoints_{i}") or 0)))
    return out


def _effect_mask(row: dict, n: int = 1) -> tuple[int, int, int]:
    letter = "ABC"[n - 1]
    return tuple(_u32(row.get(f"EffectSpellClassMask{letter}_{d}")) for d in (1, 2, 3))


# ---- checks (pure: take built rows / declared tables, return problem strings) ---------------------------------

def check_required_ids(rows_by_id: dict[int, dict]) -> list[str]:
    return [f"{i}: not declared by any deathknight DSL file" for i in REQUIRED_IDS if i not in rows_by_id]


def check_rune_frames(rows_by_id: dict[int, dict], trainer_levels: dict[int, int]) -> list[str]:
    bad = []
    for sid in RUNES:
        row = rows_by_id.get(sid)
        if row is None:
            continue

        def want(col: str, expected, value=None):
            got = _u32(row.get(col)) if value is None else value
            if got != expected:
                bad.append(f"{sid}: {col} {_fmt(got)}, expected {_fmt(expected)}")

        attrs = _u32(row.get("Attributes"))
        if attrs & 0x80:
            bad.append(f"{sid}: Attributes {attrs:#x} carries DO_NOT_DISPLAY 0x80")
        if attrs & 0x20:
            bad.append(f"{sid}: Attributes {attrs:#x} carries TRADESPELL 0x20")
        want("Attributes", ATTR0_RUNE_FRAME)
        want("AttributesEx3", ATTR3_DEATH_PERSISTENT)
        if _u32(row.get("AttributesEx")) & 0x400:
            bad.append(f"{sid}: AttributesEx carries stale NO_THREAT 0x400")
        if _u32(row.get("AttributesEx2")) & 0x2000:
            bad.append(f"{sid}: AttributesEx2 carries stale ENCHANT_OWN_ITEM_ONLY 0x2000")
        if _u32(row.get("Targets")) & 0x10:
            bad.append(f"{sid}: Targets carries stale ITEM 0x10")
        want("InterruptFlags", 0, int(row.get("InterruptFlags") or 0))
        if int(row.get("CastingTimeIndex") or 0) != 1:
            bad.append(f"{sid}: CastingTimeIndex {row.get('CastingTimeIndex')!r}, expected 1 (instant)")
        want("EquippedItemClass", -1, int(row.get("EquippedItemClass") or 0))
        want("EquippedItemSubclass", 0, int(row.get("EquippedItemSubclass") or 0))
        want("RequiresSpellFocus", 0, int(row.get("RequiresSpellFocus") or 0))
        if int(row.get("SpellVisualID_1") or 0) == 11759:
            bad.append(f"{sid}: SpellVisualID_1 is the stale enchant visual 11759")
        if int(row.get("EffectMiscValueB_1") or 0):
            bad.append(f"{sid}: EffectMiscValueB_1 {row.get('EffectMiscValueB_1')!r}, expected 0")
        kinds = [e[0] for e in _effects(row)]
        if EFFECT_ENCHANT_ITEM in kinds:
            bad.append(f"{sid}: still has an ENCHANT_ITEM (53) effect")
        if EFFECT_APPLY_AURA not in kinds:
            bad.append(f"{sid}: no self APPLY_AURA effect")
        level = int(row.get("SpellLevel") or 0)
        expected = trainer_levels.get(sid, RUNE_LEVELS[sid])
        if level != expected:
            bad.append(f"{sid}: SpellLevel {level}, expected {expected} (the trainer level)")
        if int(row.get("BaseLevel") or 0) != level:
            bad.append(f"{sid}: BaseLevel {row.get('BaseLevel')!r} != SpellLevel {level}")
    return bad


def check_trainer_rune_levels(trainer_spells: list[dict]) -> list[str]:
    by_spell = {int(t["SpellId"]): int(t["ReqLevel"]) for t in trainer_spells
                if int(t["TrainerId"]) == DEATH_KNIGHT_TRAINER}
    bad = []
    for sid, level in {**RUNE_LEVELS, OBLITERATE: OBLITERATE_LEVEL}.items():
        if sid not in by_spell:
            bad.append(f"{sid}: no DK trainer row (expected ReqLevel {level})")
        elif by_spell[sid] != level:
            bad.append(f"{sid}: trainer ReqLevel {by_spell[sid]}, expected {level}")
    return bad


def check_rune_group(groups: list[dict], rules: list[dict]) -> list[str]:
    bad = []
    members = {int(g["spell_id"]) for g in groups if int(g["id"]) == RUNE_GROUP}
    for sid in RUNES:
        if sid not in members:
            bad.append(f"group {RUNE_GROUP}: missing member {sid}")
    for sid in sorted(members - set(RUNES)):
        bad.append(f"group {RUNE_GROUP}: unexpected member {sid}")
    rule = [r for r in rules if int(r["group_id"]) == RUNE_GROUP]
    if not rule:
        bad.append(f"group {RUNE_GROUP}: no spell_group_stack_rules row")
    elif any(int(r["stack_rule"]) != 1 for r in rule):
        bad.append(f"group {RUNE_GROUP}: stack_rule {[r['stack_rule'] for r in rule]}, expected 1")
    return bad


def check_rune_procs(procs: list[dict]) -> list[str]:
    bad = []
    by_spell = {}
    for p in procs:
        by_spell.setdefault(int(p["SpellId"]), []).append(p)
    for sid, (flags, fam, mask, type_mask, hit, ppm, chance, cd) in RUNE_PROCS.items():
        rows = by_spell.get(sid, [])
        if len(rows) != 1:
            bad.append(f"{sid}: {len(rows)} spell_proc rows, expected 1")
            continue
        p = rows[0]
        got_mask = (int(p["SpellFamilyMask0"]), int(p["SpellFamilyMask1"]), int(p["SpellFamilyMask2"]))
        for label, got, expected in (
                ("ProcFlags", int(p["ProcFlags"]), flags), ("SpellPhaseMask", int(p["SpellPhaseMask"]), PHASE_HIT),
                ("SpellFamilyName", int(p["SpellFamilyName"]), fam), ("SpellFamilyMask", got_mask, tuple(mask)),
                ("SpellTypeMask", int(p["SpellTypeMask"]), type_mask), ("HitMask", int(p["HitMask"]), hit),
                ("ProcsPerMinute", float(p["ProcsPerMinute"]), ppm), ("Chance", float(p["Chance"]), chance),
                ("Cooldown", int(p["Cooldown"]), cd)):
            if got != expected:
                shown = (_hex(got), _hex(expected)) if label == "SpellFamilyMask" else (_fmt(got), _fmt(expected))
                bad.append(f"{sid}: spell_proc {label} {shown[0]}, expected {shown[1]}")
    return bad


def check_done_procs_phase(procs: list[dict]) -> list[str]:
    """Every DK0b DONE / DONE_PERIODIC proc row rolls on the hit phase (2) only."""
    bad = []
    for p in procs:
        sid = int(p["SpellId"])
        if sid in DK0B_IDS and int(p["ProcFlags"]) & PROC_DONE_MASK and int(p["SpellPhaseMask"]) != PHASE_HIT:
            bad.append(f"{sid}: DONE proc row has SpellPhaseMask {p['SpellPhaseMask']!r}, expected 2")
    return bad


def check_unholy_strength(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(UNHOLY_STRENGTH)
    if row is None:
        return []
    bad = []
    if int(row.get("Effect_1") or 0) != EFFECT_APPLY_AURA or int(row.get("EffectAura_1") or 0) != 137:
        bad.append(f"{UNHOLY_STRENGTH}: effect 0 is {row.get('Effect_1')!r}/aura {row.get('EffectAura_1')!r}, "
                   f"expected APPLY_AURA 137 (+Str)")
    if int(row.get("Effect_2") or 0) != EFFECT_APPLY_AURA:
        bad.append(f"{UNHOLY_STRENGTH}: effect 1 is {row.get('Effect_2')!r}, expected APPLY_AURA (6), not the "
                   f"instant HEAL_PCT 136")
    if int(row.get("EffectAura_2") or 0) != AURA_OBS_MOD_HEALTH:
        bad.append(f"{UNHOLY_STRENGTH}: effect 1 aura {row.get('EffectAura_2')!r}, expected 20 (OBS_MOD_HEALTH)")
    return bad


def check_obliterate(rows_by_id: dict[int, dict], rune_costs: list[dict]) -> list[str]:
    row = rows_by_id.get(OBLITERATE)
    if row is None:
        return []
    bad = []
    if int(row.get("Effect_1") or 0) != EFFECT_WEAPON_PERCENT_DAMAGE:
        bad.append(f"{OBLITERATE}: effect 0 is {row.get('Effect_1')!r}, expected WEAPON_PERCENT_DAMAGE (31) first")
    if int(row.get("Effect_2") or 0) != EFFECT_NORMALIZED_WEAPON_DMG:
        bad.append(f"{OBLITERATE}: effect 1 is {row.get('Effect_2')!r}, expected NORMALIZED_WEAPON_DMG (121)")
    for col in ("Effect_3", "EffectBasePoints_3", "EffectDieSides_3", "ImplicitTargetA_3", "ImplicitTargetB_3",
                "EffectAura_3", "EffectMiscValue_3"):
        if float(row.get(col) or 0) != 0:
            bad.append(f"{OBLITERATE}: EFFECT_2 column {col} = {row.get(col)!r}, expected 0 (no disease value)")
    if int(row.get("PowerType") or 0) != POWER_RUNE:
        bad.append(f"{OBLITERATE}: PowerType {row.get('PowerType')!r}, expected 5")
    if int(row.get("RuneCostID") or 0) != OBLITERATE_RUNE_COST:
        bad.append(f"{OBLITERATE}: RuneCostID {row.get('RuneCostID')!r}, expected {OBLITERATE_RUNE_COST}")
    cost = [c for c in rune_costs if int(c["ID"]) == OBLITERATE_RUNE_COST]
    if not cost:
        bad.append(f"rune cost {OBLITERATE_RUNE_COST}: not declared")
    else:
        got = tuple(int(cost[0][k]) for k in ("Blood", "Unholy", "Frost", "RunicPower"))
        if got != (0, 0, 1, 150):
            bad.append(f"rune cost {OBLITERATE_RUNE_COST}: blood/unholy/frost/RP {got}, expected (0, 0, 1, 150)")
    mask = spell_mask(row)
    if mask != (0, m.OBLITERATE, 0):
        bad.append(f"{OBLITERATE}: SpellClassMask {_hex(mask)}, expected (0x0, 0x{m.OBLITERATE:X}, 0x0) - d1 b17 only")
    if int(row.get("SpellLevel") or 0) != OBLITERATE_LEVEL:
        bad.append(f"{OBLITERATE}: SpellLevel {row.get('SpellLevel')!r}, expected {OBLITERATE_LEVEL}")
    return bad


def check_obliterate_guard(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(OBLITERATE_GUARD)
    if row is None:
        return []
    bad = []
    if int(row.get("SpellIconID") or 0) != 2710:
        bad.append(f"{OBLITERATE_GUARD}: SpellIconID {row.get('SpellIconID')!r}, expected 2710")
    if int(row.get("Effect_1") or 0) != EFFECT_APPLY_AURA or int(row.get("EffectAura_1") or 0) != AURA_DUMMY:
        bad.append(f"{OBLITERATE_GUARD}: effect 0 is {row.get('Effect_1')!r}/aura {row.get('EffectAura_1')!r}, "
                   f"expected APPLY_AURA DUMMY (the icon-2710 roll)")
    elif int(row.get("EffectBasePoints_1") or 0) != 99:
        bad.append(f"{OBLITERATE_GUARD}: effect 0 stored {row.get('EffectBasePoints_1')!r}, expected 99 (live 100)")
    if _u32(row.get("Attributes")) & 0xC0 != 0xC0:
        bad.append(f"{OBLITERATE_GUARD}: Attributes {_u32(row.get('Attributes')):#x} lacks passive 0x40 | hidden 0x80")
    return bad


def check_runic_focus(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(RUNIC_FOCUS)
    if row is None:
        return []
    mask = _effect_mask(row)
    want = tuple(a | b | c for a, b, c in zip(RUNIC_FOCUS_STOCK_MASK, m.RUNIC_FOCUS_READ_ADD, (0, 0, 0)))
    missing = tuple(w & ~g for w, g in zip(want, mask))
    if any(missing):
        return [f"{RUNIC_FOCUS}: effect mask {_hex(mask)} lacks bits {_hex(missing)} (stock | RUNIC_FOCUS_READ_ADD)"]
    return []


def check_runic_focus_links(links: list[dict]) -> list[str]:
    have = {(int(l["spell_trigger"]), int(l["spell_effect"]), int(l["type"])) for l in links}
    return [f"{RUNIC_FOCUS}: missing type-2 spell_linked_spell to {t}" for t in RUNIC_FOCUS_LINKS
            if (RUNIC_FOCUS, t, 2) not in have]


def check_boiling_blight_burst(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    row = rows_by_id.get(BOILING_BLIGHT_BURST)
    if row is not None and _u32(row.get("AttributesEx3")) != ATTR3_BURST:
        bad.append(f"{BOILING_BLIGHT_BURST}: AttributesEx3 {_u32(row.get('AttributesEx3')):#x}, "
                   f"expected {ATTR3_BURST:#x}")
    bad += _check_triggered_facing(rows_by_id, BOILING_BLIGHT_BURST)
    return bad


def check_razor_frost(rows_by_id: dict[int, dict]) -> list[str]:
    return _check_triggered_facing(rows_by_id, RAZOR_FROST)


def _check_triggered_facing(rows_by_id: dict[int, dict], sid: int) -> list[str]:
    """A triggered DONE-proc cast still runs CheckRange/CheckCast: no front-arc flag, no LoS check."""
    row = rows_by_id.get(sid)
    if row is None:
        return []
    bad = []
    if int(row.get("FacingCasterFlags") or 0) != 0:
        bad.append(f"{sid}: FacingCasterFlags {row.get('FacingCasterFlags')!r}, expected 0 (front-arc refusal)")
    if not _u32(row.get("AttributesEx2")) & ATTR2_IGNORE_LOS:
        bad.append(f"{sid}: AttributesEx2 {_u32(row.get('AttributesEx2')):#x} lacks IGNORE_LINE_OF_SIGHT 0x4")
    return bad


def check_disease_defense(rows_by_id: dict[int, dict]) -> list[str]:
    return [f"{sid}: DefenseType {rows_by_id[sid].get('DefenseType')!r}, expected 1 (magic)"
            for sid in (BLOOD_PLAGUE, FROST_FEVER)
            if sid in rows_by_id and int(rows_by_id[sid].get("DefenseType") or 0) != 1]


def check_raise_dead(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(RAISE_DEAD)
    if row is None:
        return []
    bad = []
    for i in range(1, 9):
        if int(row.get(f"Reagent_{i}") or 0) != 0:
            bad.append(f"{RAISE_DEAD}: Reagent_{i} {row.get(f'Reagent_{i}')!r}, expected 0 (Corpse Dust removed)")
        if int(row.get(f"ReagentCount_{i}") or 0) != 0:
            bad.append(f"{RAISE_DEAD}: ReagentCount_{i} {row.get(f'ReagentCount_{i}')!r}, expected 0")
    for sid in (46584, 46585, 52150):
        text = (rows_by_id.get(sid) or {}).get("Description_Lang_enUS") or ""
        if "Corpse Dust" in text:
            bad.append(f"{sid}: tooltip still mentions Corpse Dust")
    return bad


def check_mirrors(rows_by_id: dict[int, dict]) -> list[str]:
    return [f"{sid}: AttributesEx3 {_u32(rows_by_id[sid].get('AttributesEx3')):#x} lacks ALWAYS_HIT 0x40000"
            for sid in MIRRORS if sid in rows_by_id and not _u32(rows_by_id[sid].get("AttributesEx3")) & ATTR3_ALWAYS_HIT]


def check_frost_vulnerability(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(FROST_VULNERABILITY)
    if row is None:
        return []
    mask = _effect_mask(row)
    bad = []
    if not any(mask):
        bad.append(f"{FROST_VULNERABILITY}: effect 0 class mask is zero (a zero mask matches every family-15 school)")
    if mask != tuple(m.FROST_VULN_READ_S2):
        bad.append(f"{FROST_VULNERABILITY}: effect 0 class mask {_hex(mask)}, expected FROST_VULN_READ_S2 "
                   f"{_hex(m.FROST_VULN_READ_S2)}")
    return bad


def check_school_switched_not_in_mask(rows_by_id: dict[int, dict]) -> list[str]:
    """Obliterate / Heart Strike / Plague Strike become Frost only via a cast-time school switch; the helper adds the
    Razorice term, so a mask bit on them would double it (S2a-WP-BRIEF, DK0b-CODE-REVIEW m4)."""
    vuln = rows_by_id.get(FROST_VULNERABILITY)
    if vuln is None:
        return []
    read = _effect_mask(vuln)
    bad = []
    for sid in SCHOOL_SWITCHED_STRIKES:
        row = rows_by_id.get(sid)
        if row is None:
            continue
        overlap = tuple(a & b for a, b in zip(spell_mask(row), read))
        if any(overlap):
            bad.append(f"{sid}: school-switched strike matched by Frost Vulnerability on {_hex(overlap)} "
                       f"(the helper term covers it)")
    return bad


def _deals_damage(row: dict) -> bool:
    return any(effect in DAMAGE_EFFECT_TYPES or (effect == EFFECT_APPLY_AURA and aura == AURA_PERIODIC_DAMAGE)
               for effect, aura, _ in _effects(row))


def check_frost_vulnerability_scope(rows_by_id: dict[int, dict]) -> list[str]:
    """Family-15 damage rows: Frost school <=> matched by 51714's effect-0 mask (Razor Frost excepted)."""
    vuln = rows_by_id.get(FROST_VULNERABILITY)
    if vuln is None:
        return []
    read = _effect_mask(vuln)
    bad = []
    for sid, row in sorted(rows_by_id.items()):
        if sid in (FROST_VULNERABILITY, RAZOR_FROST, FINAL_ROAR_BURST) or int(row.get("SpellClassSet") or 0) != FAMILY_DEATHKNIGHT:
            continue
        if not _deals_damage(row):
            continue
        own = spell_mask(row)
        overlap = tuple(a & b for a, b in zip(own, read))
        frost = bool(int(row.get("SchoolMask") or 0) & SCHOOL_FROST)
        if frost and not any(overlap):
            bad.append(f"{sid}: Frost damage, class mask {_hex(own)} not covered by Frost Vulnerability "
                       f"{_hex(read)}")
        elif not frost and any(overlap):
            bad.append(f"{sid}: non-Frost damage (school {int(row.get('SchoolMask') or 0):#x}) matched by Frost "
                       f"Vulnerability on {_hex(overlap)}")
    return bad


def check_forbidden_bits(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid in DK0B_IDS:
        row = rows_by_id.get(sid)
        if row is None:
            continue
        mask = spell_mask(row)
        exempt = FORBIDDEN_EXEMPT.get(sid, (0, 0, 0))
        hit = (mask[0] & m.FORBIDDEN_D0 & ~exempt[0], mask[1] & m.FORBIDDEN_D1 & ~exempt[1],
               mask[2] & m.FORBIDDEN_D2 & ~exempt[2])
        if any(hit):
            bad.append(f"{sid}: SpellClassMask {_hex(mask)} holds forbidden bits {_hex(hit)}")
    return bad


def check_annihilation(rows_by_id: dict[int, dict]) -> list[str]:
    # S2 (D13): the icon-2710 DUMMY is gone on purpose (203055 alone guards Obliterate); effect 0 is the +1/2/3 crit aura 290
    bad = []
    for sid, bp in zip(ANNIHILATION, (0, 1, 2)):
        row = rows_by_id.get(sid)
        if row is None:
            continue
        if any(int(row.get(f"EffectAura_{n}") or 0) == AURA_DUMMY for n in (1, 2, 3)):
            bad.append(f"{sid}: still carries an APPLY_AURA DUMMY (icon-2710 hardcode)")
        if int(row.get("Effect_1") or 0) != EFFECT_APPLY_AURA or int(row.get("EffectAura_1") or 0) != 290:
            bad.append(f"{sid}: effect 0 is not the APPLY_AURA 290 crit effect")
        elif int(row.get("EffectBasePoints_1") or 0) != bp:
            bad.append(f"{sid}: effect 0 stored {row.get('EffectBasePoints_1')!r}, expected {bp}")
    return bad


def check_bone_shield(procs: list[dict]) -> list[str]:
    rows = [p for p in procs if int(p["SpellId"]) == BONE_SHIELD]
    if not rows:
        return [f"{BONE_SHIELD}: no spell_proc row"]
    return [f"{BONE_SHIELD}: spell_proc HitMask {int(p['HitMask']):#x}, expected 0x403"
            for p in rows if int(p["HitMask"]) != 0x403]


# ---- real data ------------------------------------------------------------------------------------------------

class DeathKnightDK0bDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def _rows(self):
        return _data()["rows_by_id"]

    def _pkg(self):
        return _data()["package"]

    def _trainer_levels(self) -> dict[int, int]:
        return {int(t["SpellId"]): int(t["ReqLevel"]) for t in self._pkg().trainer_spells
                if int(t["TrainerId"]) == DEATH_KNIGHT_TRAINER}

    def test_required_ids_declared(self):
        self.assertClean(check_required_ids(self._rows()))

    def test_rune_frames(self):
        self.assertClean(check_rune_frames(self._rows(), self._trainer_levels()))

    def test_rune_trainer_levels(self):
        self.assertClean(check_trainer_rune_levels(self._pkg().trainer_spells))

    def test_rune_group(self):
        self.assertClean(check_rune_group(self._pkg().spell_groups, self._pkg().spell_group_rules))

    def test_rune_procs(self):
        self.assertClean(check_rune_procs(self._pkg().spell_procs))

    def test_done_procs_phase(self):
        self.assertClean(check_done_procs_phase(self._pkg().spell_procs))

    def test_unholy_strength(self):
        self.assertClean(check_unholy_strength(self._rows()))

    def test_obliterate(self):
        self.assertClean(check_obliterate(self._rows(), self._pkg().spell_rune_costs))

    def test_obliterate_guard(self):
        self.assertClean(check_obliterate_guard(self._rows()))

    def test_runic_focus(self):
        self.assertClean(check_runic_focus(self._rows()))

    def test_disease_defense(self):
        self.assertClean(check_disease_defense(self._rows()))

    def test_runic_focus_links(self):
        self.assertClean(check_runic_focus_links(self._pkg().linked_spells))

    def test_boiling_blight_burst(self):
        self.assertClean(check_boiling_blight_burst(self._rows()))

    def test_raise_dead_reagent(self):
        self.assertClean(check_raise_dead(self._rows()))

    def test_minion_mirrors(self):
        self.assertClean(check_mirrors(self._rows()))

    def test_frost_vulnerability(self):
        self.assertClean(check_frost_vulnerability(self._rows()))

    def test_razor_frost_triggered_facing(self):
        self.assertClean(check_razor_frost(self._rows()))

    def test_frost_vulnerability_scope(self):
        self.assertClean(check_frost_vulnerability_scope(self._rows()))

    def test_school_switched_not_in_mask(self):
        self.assertClean(check_school_switched_not_in_mask(self._rows()))

    def test_no_forbidden_bits(self):
        self.assertClean(check_forbidden_bits(self._rows()))

    def test_annihilation(self):
        self.assertClean(check_annihilation(self._rows()))

    def test_bone_shield_hit_mask(self):
        self.assertClean(check_bone_shield(self._pkg().spell_procs))


# ---- negative fixtures: every check must fire on a minimal bad input --------------------------------------------

def _row(spell_id=1, **cols) -> dict:
    return {"ID": spell_id, **cols}


def _rune(sid=FALLEN_CRUSADER, **cols) -> dict:
    row = _row(sid, Attributes=0x10000000, AttributesEx3=0x100000, CastingTimeIndex=1, EquippedItemClass=-1,
               SpellLevel=RUNE_LEVELS[sid], BaseLevel=RUNE_LEVELS[sid], Effect_1=6, EffectAura_1=3)
    row.update(cols)
    return row


def _proc(sid, **cols) -> dict:
    flags, fam, mask, type_mask, hit, ppm, chance, cd = RUNE_PROCS[sid]
    row = {"SpellId": sid, "ProcFlags": flags, "SpellFamilyName": fam, "SpellFamilyMask0": mask[0],
           "SpellFamilyMask1": mask[1], "SpellFamilyMask2": mask[2], "SpellTypeMask": type_mask, "HitMask": hit,
           "ProcsPerMinute": ppm, "Chance": chance, "Cooldown": cd, "SpellPhaseMask": PHASE_HIT}
    row.update(cols)
    return row


def _obliterate(**cols) -> dict:
    row = _row(OBLITERATE, Effect_1=31, Effect_2=121, PowerType=5, RuneCostID=2600, SpellClassMask_2=0x20000,
               SpellLevel=20)
    row.update(cols)
    return row


class DeathKnightDK0bNegativeTest(unittest.TestCase):
    def test_required_ids(self):
        self.assertEqual(len(check_required_ids({})), len(REQUIRED_IDS))
        self.assertEqual(check_required_ids({i: _row(i) for i in REQUIRED_IDS}), [])

    def test_rune_frames(self):
        levels = {sid: lv for sid, lv in RUNE_LEVELS.items()}
        self.assertEqual(check_rune_frames({sid: _rune(sid) for sid in RUNES}, levels), [])
        cases = (
            {"Attributes": 0x10000080}, {"Attributes": 0x10000020}, {"Attributes": 0x10010000},
            {"Attributes": 0x0}, {"AttributesEx3": 0x0}, {"AttributesEx3": 0x100080},
            {"AttributesEx": 0x400}, {"AttributesEx2": 0x2000}, {"Targets": 0x10}, {"InterruptFlags": 15},
            {"CastingTimeIndex": 6}, {"EquippedItemClass": 2}, {"EquippedItemSubclass": 189939},
            {"RequiresSpellFocus": 1552}, {"SpellVisualID_1": 11759}, {"EffectMiscValueB_1": 15},
            {"Effect_2": 53}, {"Effect_1": 3, "EffectAura_1": 0}, {"SpellLevel": 40}, {"BaseLevel": 55},
        )
        for i, cols in enumerate(cases):
            problems = check_rune_frames({FALLEN_CRUSADER: _rune(**cols)}, levels)
            self.assertGreaterEqual(len(problems), 1, (i, cols))
        # the trainer level wins over the table
        self.assertEqual(len(check_rune_frames({RAZORICE: _rune(RAZORICE)}, {RAZORICE: 10})), 1)
        self.assertEqual(check_rune_frames({}, levels), [])

    def test_trainer_rune_levels(self):
        good = [{"SpellId": sid, "ReqLevel": lv, "TrainerId": 13}
                for sid, lv in {**RUNE_LEVELS, OBLITERATE: OBLITERATE_LEVEL}.items()]
        self.assertEqual(check_trainer_rune_levels(good), [])
        self.assertEqual(len(check_trainer_rune_levels(good[1:])), 1)
        self.assertEqual(len(check_trainer_rune_levels([{**good[0], "ReqLevel": 60}, *good[1:]])), 1)
        self.assertEqual(len(check_trainer_rune_levels([{**good[0], "TrainerId": 14}, *good[1:]])), 1)

    def test_rune_group(self):
        groups = [{"id": RUNE_GROUP, "spell_id": sid} for sid in RUNES]
        rules = [{"group_id": RUNE_GROUP, "stack_rule": 1}]
        self.assertEqual(check_rune_group(groups, rules), [])
        self.assertEqual(len(check_rune_group(groups[1:], rules)), 1)
        self.assertEqual(len(check_rune_group([*groups, {"id": RUNE_GROUP, "spell_id": 1}], rules)), 1)
        self.assertEqual(len(check_rune_group(groups, [])), 1)
        self.assertEqual(len(check_rune_group(groups, [{"group_id": RUNE_GROUP, "stack_rule": 2}])), 1)
        self.assertEqual(len(check_rune_group([{"id": 1000, "spell_id": RUNES[0]}], rules)), len(RUNES))

    def test_rune_procs(self):
        good = [_proc(sid) for sid in RUNE_PROCS]
        self.assertEqual(check_rune_procs(good), [])
        for sid in RUNE_PROCS:
            others = [p for p in good if p["SpellId"] != sid]
            self.assertEqual(len(check_rune_procs(others)), 1, sid)
            self.assertEqual(len(check_rune_procs([*others, _proc(sid, ProcFlags=0x1)])), 1, sid)
            self.assertEqual(len(check_rune_procs([*others, _proc(sid, SpellPhaseMask=0)])), 1, sid)
            self.assertEqual(len(check_rune_procs([*others, _proc(sid, Cooldown=1)])), 1, sid)
            self.assertEqual(len(check_rune_procs([*others, _proc(sid, Chance=99.0)])), 1, sid)
            self.assertEqual(len(check_rune_procs([*others, _proc(sid, ProcsPerMinute=9.0)])), 1, sid)
        bb = [p for p in good if p["SpellId"] != BOILING_BLIGHT]
        self.assertEqual(len(check_rune_procs([*bb, _proc(BOILING_BLIGHT, SpellFamilyMask1=0)])), 1)
        self.assertEqual(len(check_rune_procs([*good, _proc(RAZORICE)])), 1)  # duplicate row

    def test_done_procs_phase(self):
        self.assertEqual(check_done_procs_phase([_proc(RAZORICE)]), [])
        self.assertEqual(len(check_done_procs_phase([_proc(RAZORICE, SpellPhaseMask=4)])), 1)
        self.assertEqual(check_done_procs_phase([_proc(RAZORICE, SpellPhaseMask=4, SpellId=1)]), [])  # not DK0b
        self.assertEqual(check_done_procs_phase([_proc(RAZORICE, SpellPhaseMask=4, ProcFlags=0x2)]), [])  # TAKEN only

    def test_unholy_strength(self):
        good = _row(UNHOLY_STRENGTH, Effect_1=6, EffectAura_1=137, Effect_2=6, EffectAura_2=20)
        self.assertEqual(check_unholy_strength({UNHOLY_STRENGTH: good}), [])
        stock = {**good, "Effect_2": 136, "EffectAura_2": 0}
        self.assertEqual(len(check_unholy_strength({UNHOLY_STRENGTH: stock})), 2)
        self.assertEqual(len(check_unholy_strength({UNHOLY_STRENGTH: {**good, "EffectAura_2": 4}})), 1)
        self.assertEqual(len(check_unholy_strength({UNHOLY_STRENGTH: {**good, "EffectAura_1": 99}})), 1)

    def test_obliterate(self):
        cost = [{"ID": 2600, "Blood": 0, "Unholy": 0, "Frost": 1, "RunicPower": 150}]
        self.assertEqual(check_obliterate({OBLITERATE: _obliterate()}, cost), [])
        cases = (
            {"Effect_1": 121, "Effect_2": 31}, {"Effect_2": 2}, {"Effect_3": 121}, {"EffectBasePoints_3": 5},
            {"PowerType": 0}, {"RuneCostID": 1142}, {"SpellClassMask_2": 0x20004}, {"SpellClassMask_1": 0x1},
            {"SpellLevel": 36},
        )
        for cols in cases:
            self.assertGreaterEqual(len(check_obliterate({OBLITERATE: _obliterate(**cols)}, cost)), 1, cols)
        self.assertEqual(len(check_obliterate({OBLITERATE: _obliterate()}, [])), 1)
        for bad_cost in ({"Frost": 2}, {"Blood": 1}, {"Unholy": 1}, {"RunicPower": 100}):
            self.assertEqual(len(check_obliterate({OBLITERATE: _obliterate()}, [{**cost[0], **bad_cost}])), 1)

    def test_obliterate_guard(self):
        good = _row(OBLITERATE_GUARD, SpellIconID=2710, Effect_1=6, EffectAura_1=4, EffectBasePoints_1=99,
                    Attributes=0xC0)
        self.assertEqual(check_obliterate_guard({OBLITERATE_GUARD: good}), [])
        for cols in ({"SpellIconID": 2639}, {"EffectAura_1": 3}, {"EffectBasePoints_1": 32}, {"Attributes": 0x40},
                     {"Attributes": 0x80}):
            self.assertEqual(len(check_obliterate_guard({OBLITERATE_GUARD: {**good, **cols}})), 1, cols)

    def test_runic_focus(self):
        want = (0x80040202 | 0, 0x10022 | m.RUNIC_FOCUS_READ_ADD[1], m.RUNIC_FOCUS_READ_ADD[2] | 0x9)
        good = _row(RUNIC_FOCUS, EffectSpellClassMaskA_1=want[0], EffectSpellClassMaskA_2=want[1],
                    EffectSpellClassMaskA_3=want[2])
        self.assertEqual(check_runic_focus({RUNIC_FOCUS: good}), [])
        stock = {**good, "EffectSpellClassMaskA_2": 0x10022, "EffectSpellClassMaskA_3": 0x9}
        self.assertEqual(len(check_runic_focus({RUNIC_FOCUS: stock})), 1)
        self.assertEqual(len(check_runic_focus({RUNIC_FOCUS: {**good, "EffectSpellClassMaskA_1": 0x202}})), 1)
        self.assertEqual(len(check_runic_focus({RUNIC_FOCUS: {**good, "EffectSpellClassMaskA_3": m.ROT_DAMAGE | 9}})), 1)
        # extra bits are fine (superset)
        self.assertEqual(check_runic_focus({RUNIC_FOCUS: {**good, "EffectSpellClassMaskA_1": want[0] | 0x1000}}), [])

    def test_runic_focus_links(self):
        good = [{"spell_trigger": RUNIC_FOCUS, "spell_effect": t, "type": 2} for t in RUNIC_FOCUS_LINKS]
        self.assertEqual(check_runic_focus_links(good), [])
        self.assertEqual(len(check_runic_focus_links(good[1:])), 1)
        self.assertEqual(len(check_runic_focus_links([{**good[0], "type": 0}, *good[1:]])), 1)
        self.assertEqual(len(check_runic_focus_links([{**good[0], "spell_trigger": 1}, *good[1:]])), 1)
        self.assertEqual(len(check_runic_focus_links([])), 3)

    def test_boiling_blight_burst(self):
        cols = dict(AttributesEx3=0x50000, AttributesEx2=ATTR2_IGNORE_LOS, FacingCasterFlags=0)
        ok = {BOILING_BLIGHT_BURST: _row(BOILING_BLIGHT_BURST, **cols)}
        self.assertEqual(check_boiling_blight_burst(ok), [])
        for v in (0x10000, 0x40000, 0):
            bad = {BOILING_BLIGHT_BURST: _row(1, **{**cols, "AttributesEx3": v})}
            self.assertEqual(len(check_boiling_blight_burst(bad)), 1)
        for col, v in (("FacingCasterFlags", 1), ("AttributesEx2", 0), ("AttributesEx2", 0x20000000)):
            bad = {BOILING_BLIGHT_BURST: _row(1, **{**cols, col: v})}
            self.assertEqual(len(check_boiling_blight_burst(bad)), 1, (col, v))

    def test_razor_frost_triggered_facing(self):
        cols = dict(AttributesEx2=ATTR2_IGNORE_LOS | 0x20000000, FacingCasterFlags=0)
        self.assertEqual(check_razor_frost({RAZOR_FROST: _row(RAZOR_FROST, **cols)}), [])
        self.assertEqual(check_razor_frost({}), [])
        for col, v in (("FacingCasterFlags", 1), ("AttributesEx2", 0x20000000)):
            bad = {RAZOR_FROST: _row(RAZOR_FROST, **{**cols, col: v})}
            self.assertEqual(len(check_razor_frost(bad)), 1, (col, v))

    def test_disease_defense(self):
        good = {BLOOD_PLAGUE: _row(BLOOD_PLAGUE, DefenseType=1), FROST_FEVER: _row(FROST_FEVER, DefenseType=1)}
        self.assertEqual(check_disease_defense(good), [])
        self.assertEqual(len(check_disease_defense({**good, FROST_FEVER: _row(FROST_FEVER, DefenseType=0)})), 1)
        self.assertEqual(len(check_disease_defense({BLOOD_PLAGUE: _row(BLOOD_PLAGUE)})), 1)

    def test_raise_dead(self):
        self.assertEqual(check_raise_dead({RAISE_DEAD: _row(RAISE_DEAD, Reagent_1=0, ReagentCount_1=0)}), [])
        self.assertEqual(len(check_raise_dead({RAISE_DEAD: _row(RAISE_DEAD, Reagent_1=37201, ReagentCount_1=1)})), 2)
        self.assertEqual(len(check_raise_dead({RAISE_DEAD: _row(RAISE_DEAD, Reagent_8=1)})), 1)
        self.assertEqual(len(check_raise_dead({RAISE_DEAD: _row(RAISE_DEAD), 46585: _row(46585, Description_Lang_enUS='you must supply Corpse Dust')})), 1)

    def test_mirrors(self):
        good = {sid: _row(sid, AttributesEx3=0x40000) for sid in MIRRORS}
        self.assertEqual(check_mirrors(good), [])
        self.assertEqual(len(check_mirrors({**good, 203057: _row(203057, AttributesEx3=0x100000)})), 1)
        self.assertEqual(len(check_mirrors({203056: _row(203056)})), 1)

    def test_frost_vulnerability(self):
        mask = m.FROST_VULN_READ_S2
        good = _row(FROST_VULNERABILITY, EffectSpellClassMaskA_1=mask[0], EffectSpellClassMaskA_2=mask[1],
                    EffectSpellClassMaskA_3=mask[2])
        self.assertEqual(check_frost_vulnerability({FROST_VULNERABILITY: good}), [])
        self.assertEqual(len(check_frost_vulnerability({FROST_VULNERABILITY: _row(FROST_VULNERABILITY)})), 2)  # zero
        stock = {**good, "EffectSpellClassMaskA_1": 1026, "EffectSpellClassMaskA_2": 67403783}
        self.assertEqual(len(check_frost_vulnerability({FROST_VULNERABILITY: stock})), 1)
        old = {**good, "EffectSpellClassMaskA_3": 0}  # the pre-S2 FROST_VULN_READ lacks d2 0x10600
        self.assertEqual(len(check_frost_vulnerability({FROST_VULNERABILITY: old})), 1)
        self.assertEqual(len(check_frost_vulnerability({FROST_VULNERABILITY: {**good, "EffectSpellClassMaskA_3": 4}})), 1)

    def test_frost_vulnerability_scope(self):
        read = (0x2, 0x0, 0x8)
        vuln = _row(FROST_VULNERABILITY, EffectSpellClassMaskA_1=read[0], EffectSpellClassMaskA_2=read[1],
                    EffectSpellClassMaskA_3=read[2])
        dmg = dict(SpellClassSet=15, Effect_1=2)

        def run(*rows):
            return check_frost_vulnerability_scope({FROST_VULNERABILITY: vuln, **{r["ID"]: r for r in rows}})

        covered = _row(100, SchoolMask=16, SpellClassMask_1=0x2, **dmg)
        covered_word3 = _row(101, SchoolMask=16, SpellClassMask_3=0x8, **dmg)
        dot = _row(102, SchoolMask=16, SpellClassMask_1=0x2, SpellClassSet=15, Effect_1=6, EffectAura_1=3)
        self.assertEqual(run(covered, covered_word3, dot), [])
        # Frost damage on an uncovered bit (also via a periodic aura and a weapon effect)
        for effect_cols in (dict(Effect_1=2), dict(Effect_1=6, EffectAura_1=3), dict(Effect_1=121)):
            row = _row(103, SchoolMask=16, SpellClassMask_1=0x4, SpellClassSet=15, **effect_cols)
            self.assertEqual(len(run(row)), 1, effect_cols)
        # Shadow / Physical damage on a covered bit
        for school in (32, 1):
            row = _row(104, SchoolMask=school, SpellClassMask_3=0x8, **dmg)
            self.assertEqual(len(run(row)), 1, school)
        # exempt / out of scope: Razor Frost, other families, non-damage rows
        self.assertEqual(run(_row(RAZOR_FROST, SchoolMask=16, SpellClassMask_1=0x4, **dmg)), [])
        self.assertEqual(run(_row(105, SchoolMask=16, SpellClassMask_1=0x4, SpellClassSet=3, Effect_1=2)), [])
        self.assertEqual(run(_row(106, SchoolMask=32, SpellClassMask_1=0x2, SpellClassSet=15, Effect_1=6)), [])
        self.assertEqual(check_frost_vulnerability_scope({}), [])
        # Final Roar burst: Frost damage with no mask bit is exempt (inert under Razorice)
        self.assertEqual(run(_row(FINAL_ROAR_BURST, SchoolMask=16, SpellClassMask_1=0x4, **dmg)), [])

    def test_school_switched_not_in_mask(self):
        vuln = _row(FROST_VULNERABILITY, EffectSpellClassMaskA_1=0x2, EffectSpellClassMaskA_2=0x4)
        ok = {FROST_VULNERABILITY: vuln, OBLITERATE: _row(OBLITERATE, SpellClassMask_2=0x20000),
              55050: _row(55050, SpellClassMask_1=0x1000000), 45462: _row(45462, SpellClassMask_1=0x1)}
        self.assertEqual(check_school_switched_not_in_mask(ok), [])
        for sid, cols in ((OBLITERATE, dict(SpellClassMask_2=0x4)), (55050, dict(SpellClassMask_1=0x2)),
                          (45462, dict(SpellClassMask_2=0x4))):
            self.assertEqual(len(check_school_switched_not_in_mask({**ok, sid: _row(sid, **cols)})), 1, sid)
        self.assertEqual(check_school_switched_not_in_mask({}), [])

    def test_forbidden_bits(self):
        for col, bit in (("SpellClassMask_1", m.FORBIDDEN_D0_B6), ("SpellClassMask_1", m.FORBIDDEN_D0_B17),
                         ("SpellClassMask_1", m.FORBIDDEN_D0_B22), ("SpellClassMask_2", m.FORBIDDEN_D1_B10),
                         ("SpellClassMask_2", m.FORBIDDEN_D1_B11), ("SpellClassMask_2", m.FORBIDDEN_D1_B23),
                         ("SpellClassMask_2", m.FORBIDDEN_D1_B24), ("SpellClassMask_3", m.FORBIDDEN_D2_B1),
                         ("SpellClassMask_3", m.FORBIDDEN_D2_B31)):
            self.assertEqual(len(check_forbidden_bits({OBLITERATE: _row(OBLITERATE, **{col: bit})})), 1, (col, bit))
        self.assertEqual(check_forbidden_bits({OBLITERATE: _obliterate()}), [])
        # stock-kept: the disease DoTs keep d2 b1, nothing else may
        self.assertEqual(check_forbidden_bits({BLOOD_PLAGUE: _row(BLOOD_PLAGUE, SpellClassMask_3=0x2)}), [])
        self.assertEqual(len(check_forbidden_bits({OBLITERATE: _row(OBLITERATE, SpellClassMask_3=0x2)})), 1)
        self.assertEqual(check_forbidden_bits({1: _row(1, SpellClassMask_3=0x80000000)}), [])  # not a DK0b id

    def test_annihilation(self):
        good = {sid: _row(sid, Effect_1=6, EffectAura_1=290, EffectBasePoints_1=bp)
                for sid, bp in zip(ANNIHILATION, (0, 1, 2))}
        self.assertEqual(check_annihilation(good), [])
        self.assertEqual(len(check_annihilation({**good, 51468: _row(51468, Effect_1=6, EffectAura_1=4,
                                                                     EffectBasePoints_1=99)})), 2)
        self.assertEqual(len(check_annihilation({**good, 51473: _row(51473, Effect_1=6, EffectAura_1=290,
                                                                     EffectBasePoints_1=5)})), 1)

    def test_bone_shield(self):
        self.assertEqual(check_bone_shield([{"SpellId": BONE_SHIELD, "HitMask": 0x403}]), [])
        self.assertEqual(len(check_bone_shield([{"SpellId": BONE_SHIELD, "HitMask": 0x3}])), 1)
        self.assertEqual(len(check_bone_shield([])), 1)


if __name__ == "__main__":
    unittest.main()
