"""
Warrior W0b data gate (warrior-rework W0b-HANDOFF WP-A row A4, W0b-WP-BRIEF rulings, W0b-0VERIFY items 2, 3, 6).

Loads the real warrior DSL package (source/classes/warrior/) and source/npcs/warrior_npcs.py and asserts on the BUILT
rows
(stock base + DSL + raw_overrides via `build.build_spell_row`, the way generate.py pairs them; the lookup tables are
seeded with the stock Spell*.dbc rows, so a 6 s duration is the stock index 32, not a minted one). Every check is a pure
function over built rows / package tables; the negative tests mutate a copy of the real rows and prove each check can
fail.

  1. Overpower charges (D2, D3): 7384 flag clear + CasterAuraSpell, 204403 aura, the spend and grant spell_proc rows,
     204404 passive.
  2. Charge 100 (D5), Intervene 3411 (D8), Shield Wall 871 (D25), Enraged Regeneration 55694 (D26), Recklessness 1719
     (D20), Impale (D19).
  3. Heroic Leap 204400-204402 (D9), Skull Banner 204405-204409 and its creatures (D12-D14), the spell_group.
  4. Victory Rush 34428 / Victorious 32216 / Victorious State 32215 (D14-D16), SkillLineAbility rows (D16, D18).
  5. The R1 group bit d2 b3 on exactly the 17 carriers, d2 b0 on exactly the two Heroic Leap rows.
  6. Trainer rows (D17), bindings (brief ruling 8), the D31 consts and the generated header, role-bit pins, no
     "Capstone" in any W0b text.

Not driven here: the lib/gcd_haste recompute of 201560 (melee mask (0x3e7f4666, 0x4247ed, 0x8)). It needs the merged
family-4 stock + DSL population and the learnable set (about 10 minutes of CPU in the 0-verify run), which is not a
cheap
driver from the loaded package; the inputs it reads (1719 off the GCD, the 19 carriers' d2 b3, the ranged mask rows
untouched) are asserted instead.

Run: cd apps/dbc-tools && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3 -m pytest lib/test_warrior_w0b.py -q
"""

from __future__ import annotations

import copy
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, source, spell_tables, state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402
from lib import test_warrior_w0a as w0a  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
NPC_FILE = TOOL_ROOT / "source" / "npcs" / "warrior_npcs.py"
HEADER_FILE = REPO_ROOT / "src" / "server" / "game" / "Entities" / "Unit" / "Generated" / "WarriorData.h"

# effect types / auras
SCHOOL_DAMAGE, DUMMY, APPLY_AURA, SUMMON, CHARGE, HEAL_PCT = 2, 3, 6, 28, 96, 136
AURA_DUMMY, AURA_PROC_TRIGGER_SPELL, AURA_MOD_DAMAGE_TAKEN_PCT, AURA_MOD_CRIT_PCT = 4, 42, 87, 290
AURA_MECHANIC_IMMUNITY, AURA_SAFE_FALL = 77, 144

ATTR0_PASSIVE, ATTR0_DO_NOT_DISPLAY, ATTR0_NOT_IN_COMBAT_ONLY_PEACEFUL = 0x40, 0x80, 0x10000000
ATTR1_FINISHING_MOVE, ATTR2_IGNORE_LOS, ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000, 0x4, 0x100000
CU_NEGATIVE_EFF0, CU_AURA_CANNOT_BE_SAVED = 0x1000, 0x1000000

OVERPOWER, CHARGE_ID, INTERVENE, SHIELD_WALL, RECKLESSNESS, ENRAGED_REGEN = 7384, 100, 3411, 871, 1719, 55694
VICTORY_RUSH, VICTORIOUS, VICTORIOUS_STATE, IMPALE_1, IMPALE_2 = 34428, 32216, 32215, 16493, 16494
HL_BUTTON, HL_LANDING, HL_FLIGHT = 204400, 204401, 204402
OP_CHARGE, OP_TRAINING = 204403, 204404
SB_BUTTON, SB_BUFF, SB_RALLIED, SB_HORDE, VR_HEAL = 204405, 204406, 204407, 204408, 204409
W0B_NEW_IDS = tuple(range(204400, 204410))
SB_ALLIANCE_NPC, SB_HORDE_NPC = 300370, 300371

# D19: the 17 d2 b3 carriers (+ S2 Colossus Smash, + S3 Frenzied Blows' two strikes) and their identity bits:
# id -> (SpellClassMask column, bit)
M1, M2 = "SpellClassMask_1", "SpellClassMask_2"
G_CARRIERS = {
    78: (M1, 0x40), 845: (M1, 0x400000), 1464: (M1, 0x200000), 1680: (M2, 0x4), 6572: (M1, 0x400),
    7384: (M1, 0x4), 12294: (M1, 0x2000000), 12809: (M1, 0x4000000), 20243: (M2, 0x40), 23881: (M2, 0x400),
    23922: (M2, 0x200), 34428: (M2, 0x100), 57755: (M2, 0x1), 64382: (M2, 0x400000), 20647: (M1, 0x20000000),
    44949: (M2, 0x4), 50622: (M2, 0x4),
    204490: ("SpellClassMask_3", 0x2),     # S2: Colossus Smash (d2 0xA = its own identity b1 + the group bit b3)
    # S3 (D19): Frenzied Blows' two off-hand strikes carry the parent's identity bit + d2 b3, so every Heroic Strike /
    # Cleave damage modifier and Recklessness' crit reach "the same ability's damage"
    204633: (M1, 0x40), 204634: (M1, 0x400000),
}
GROUP_BIT, HEROIC_LEAP_BIT = 0x8, 0x1

# role bits (_masks.py note): name -> (column, bit, exact set of package rows that carry it)
ROLE_BITS = {
    "d0 b7 Thunder Clap": (M1, 0x80, {6343, 200065}),
    "d0 b10 Revenge": (M1, 0x400, {6572, 25288}),
    "d1 b8 Victory Rush": (M2, 0x100, {34428}),
    "d1 b9 Shield Slam": (M2, 0x200, {23922}),
    "d1 b18 Victorious aura state": (M2, 0x40000, {32216}),
    "d1 b21 Dazed marker": (M2, 0x200000, set()),
    "d0 b23 stances": (M1, 0x800000, {71, 2457, 2458}),
}

# D17: trainer 200 rows W0b adds; trainer 201 is unchanged (W0a: Berserker Stance only)
W0B_TRAINER_ROWS = {(200, 34428): 8, (200, 3411): 30, (200, 204400): 38, (200, 55694): 56, (200, 204405): 60}
TRAINER_201 = {(201, 2458): 16}

# brief ruling 8: the bindings this package declares, and the removals W0b adds
BINDINGS = {(-100, "spell_warr_charge_rework"), (3411, "spell_warr_intervene_rework"),
            (34428, "spell_warr_victory_rush_heal"), (204400, "spell_warr_heroic_leap"),
            (204405, "spell_warr_skull_banner"),
            # S2 (Arms) bindings, pinned in test_warrior_s2.py
            (12294, "spell_warr_mortal_strike_arms"), (772, "spell_warr_rend_arms"),
            (-12834, "spell_warr_deep_wounds_rework"), (204496, "spell_warr_deep_wounds_holder"),
            (-29723, "spell_warr_sudden_death_reset"), (204401, "spell_warr_heroic_leap_landing"),
            (204495, "spell_warr_bladestorm_whirl"), (1680, "spell_warr_whirlwind_seismic"),
            (-12296, "spell_warr_anger_management"), (204514, "spell_warr_weapon_spec_sword"),
            (204517, "spell_warr_weapon_spec_sword"), (204520, "spell_warr_weapon_spec_sword"),
            (204493, "spell_warr_sweeping_strikes_rework"),
            # S1 (Protection delta) bindings, pinned in test_warrior_s1.py
            (12809, "spell_warr_concussion_blow_rework"), (50720, "spell_warr_vigilance_focused_rage"),
            (50725, "spell_warr_vigilance_trigger_growl"), (200030, "spell_warr_bloodstorm"),
            (200065, "spell_warr_thunder_clap_echo"), (200066, "spell_warr_thunderstruck_echo_holder"),
            # S3 (Fury) bindings, pinned in test_warrior_s3.py
            (23881, "spell_warr_bloodthirst_fury"), (-5308, "spell_warr_execute_fury"),
            (204630, "spell_warr_rampage_fury"), (204636, "spell_warr_enrage_fury"),
            (12292, "spell_warr_death_wish_fury"), (1719, "spell_warr_recklessness_fury"),
            (78, "spell_warr_hs_cleave_fury"), (845, "spell_warr_hs_cleave_fury"),
            (49152, "spell_warr_titans_grip_hardcode"), (-204524, "spell_warr_two_handed_weapon_mastery_gate"),
            (6552, "spell_warr_pummel_fury"), (-204653, "spell_warr_dance_of_death"),
            (6673, "spell_warr_commanding_presence"), (469, "spell_warr_commanding_presence"),
            (-204671, "spell_warr_deathmaker")}
W0B_UNBINDINGS = {(-100, "spell_warr_charge"), (3411, "spell_warr_intervene")}

# D31 consts
W0B_CONSTS = {"HEROIC_LEAP_AIR_MS": (1000, "uint32"), "HEROIC_LEAP_APEX_YD": (5.0, "float"),
              "CHARGE_COMBAT_MIN_YD": (8.0, "float"), "CHARGE_COMBAT_MAX_YD": (25.0, "float")}
# generated header names (brief ruling 2), checked once the orchestrator has regenerated the header
HEADER_SPELL_NAMES = {
    "SPELL_HEROIC_LEAP": 204400, "SPELL_HEROIC_LEAP_204401": 204401, "SPELL_LEAPING": 204402,
    "SPELL_OVERPOWER_204403": 204403, "SPELL_OVERPOWER_TRAINING": 204404, "SPELL_SKULL_BANNER": 204405,
    "SPELL_SKULL_BANNER_204406": 204406, "SPELL_RALLIED": 204407, "SPELL_SKULL_BANNER_204408": 204408,
    "SPELL_VICTORY_RUSH_204409": 204409,
}
HEADER_NPC_NAMES = {"NPC_SKULL_BANNER_ALLIANCE": 300370, "NPC_SKULL_BANNER_HORDE": 300371}

# the Overpower proc flags: the four TAKEN bits (melee auto 0x8, melee spell 0x20, ranged auto 0x80, ranged spell 0x200)
TAKEN_ONLY_FLAGS = 0x2A8


def _i(row: dict, col: str) -> int:
    return int(row.get(col) or 0)


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def _mask(row: dict, prefix: str) -> tuple[int, int, int]:
    return tuple(_u32(row.get(f"{prefix}_{n}")) for n in (1, 2, 3))


def _eff_mask(row: dict, letter: str = "A") -> tuple[int, int, int]:
    return _mask(row, f"EffectSpellClassMask{letter}")


def _potency(entries: dict, sid: int, effect: int) -> dict:
    return ((entries.get(sid) or {}).get(f"effect{effect}") or {}).get("_potency") or {}


def _missing(rows: dict, *ids: int) -> list[str]:
    return [f"{sid}: not built" for sid in ids if sid not in rows]


# ---- checks (pure: take built rows / package tables, return problem strings) ------------------------------------

def check_overpower(rows: dict, procs: list[dict], dur20: int) -> list[str]:
    bad = _missing(rows, OVERPOWER, OP_CHARGE, OP_TRAINING)
    if bad:
        return bad
    op, ch, tr = rows[OVERPOWER], rows[OP_CHARGE], rows[OP_TRAINING]
    if _u32(op.get("AttributesEx")) & ATTR1_FINISHING_MOVE:
        bad.append(f"7384: AttributesEx {_u32(op.get('AttributesEx')):#x} still has FINISHING_MOVE 0x100000 (D3)")
    if _i(op, "CasterAuraSpell") != OP_CHARGE:
        bad.append(f"7384: CasterAuraSpell {op.get('CasterAuraSpell')!r}, expected {OP_CHARGE}")
    if _u32(op.get("SpellClassMask_3")) & GROUP_BIT == 0 or _u32(op.get(M1)) & 0x4 == 0:
        bad.append("7384: lost d2 b3 or its identity bit d0 b2")
    # 204403: the visible five-stack aura
    if _i(ch, "CumulativeAura") != 5:
        bad.append(f"204403: CumulativeAura {ch.get('CumulativeAura')!r}, expected 5")
    if _i(ch, "DurationIndex") != dur20:
        bad.append(f"204403: DurationIndex {ch.get('DurationIndex')!r}, expected the 20 s row {dur20}")
    if _u32(ch.get("Attributes")) & (ATTR0_PASSIVE | ATTR0_DO_NOT_DISPLAY):
        bad.append(f"204403: Attributes {_u32(ch.get('Attributes')):#x} is passive / hidden, expected visible")
    if (_i(ch, "Effect_1"), _i(ch, "EffectAura_1")) != (APPLY_AURA, AURA_DUMMY):
        bad.append("204403: effect 1 is not APPLY_AURA DUMMY (4)")
    if ch.get("AuraDescription_Lang_enUS") != "Overpower is usable.":
        bad.append(f"204403: aura text {ch.get('AuraDescription_Lang_enUS')!r}, expected 'Overpower is usable.'")
    # 204404: the hidden parry passive
    if (_i(tr, "Effect_1"), _i(tr, "EffectAura_1"), _i(tr, "EffectTriggerSpell_1")) != \
            (APPLY_AURA, AURA_PROC_TRIGGER_SPELL, OP_CHARGE):
        bad.append("204404: effect 1 is not PROC_TRIGGER_SPELL -> 204403")
    if _i(tr, "ProcTypeMask") != 0x2A8:
        bad.append(f"204404: DBC ProcTypeMask {tr.get('ProcTypeMask')!r}, expected 0x2A8")
    if _u32(tr.get("Attributes")) & (ATTR0_PASSIVE | ATTR0_DO_NOT_DISPLAY) != (ATTR0_PASSIVE | ATTR0_DO_NOT_DISPLAY):
        bad.append("204404: not a hidden passive (0x40 | 0x80)")
    by_id = {int(p["SpellId"]): p for p in procs}
    spend, grant = by_id.get(OP_CHARGE), by_id.get(OP_TRAINING)
    if spend is None:
        bad.append("204403: no spell_proc row (the spend row)")
    else:
        got = (int(spend["ProcFlags"]), int(spend["SpellFamilyName"]), int(spend["SpellFamilyMask0"]),
               int(spend["SpellFamilyMask1"]), int(spend["SpellFamilyMask2"]), int(spend["SpellPhaseMask"]),
               int(spend["AttributesMask"]), int(spend["Charges"]))
        if got != (0x10, 4, 0x4, 0, 0, 1, 0x10, 0):
            bad.append(f"204403 spend row (flags, family, mask0-2, phase, attrs, charges) {got}, expected "
                       "(0x10, 4, 0x4, 0, 0, 1, 0x10, 0)")
        if float(spend.get("Chance") or 0) != 100:
            bad.append(f"204403 spend row Chance {spend.get('Chance')!r}, expected 100 (0 would use the DBC's 0)")
    if grant is None:
        bad.append("204404: no spell_proc row (the grant row)")
    else:
        flags = int(grant["ProcFlags"])
        if flags != 0x2A8 or flags & ~TAKEN_ONLY_FLAGS:
            bad.append(f"204404 grant row ProcFlags {flags:#x}, expected 0x2A8 (TAKEN bits only, no DONE bit)")
        if (int(grant["HitMask"]), int(grant["SpellPhaseMask"])) != (0x20, 0):
            bad.append(f"204404 grant row HitMask/phase {grant['HitMask']}/{grant['SpellPhaseMask']}, expected 32 / 0")
        if float(grant.get("Chance") or 0) != 100:
            bad.append(f"204404 grant row Chance {grant.get('Chance')!r}, expected 100")
    return bad


def check_charge(rows: dict) -> list[str]:
    bad = _missing(rows, CHARGE_ID)
    if bad:
        return bad
    r = rows[CHARGE_ID]
    attrs = _u32(r.get("Attributes"))
    if attrs != 0x20050010:
        bad.append(f"100: Attributes {attrs:#x}, expected 0x20050010")
    if attrs & ATTR0_NOT_IN_COMBAT_ONLY_PEACEFUL:
        bad.append("100: NOT_IN_COMBAT_ONLY_PEACEFUL 0x10000000 still set (Charge not usable in combat)")
    if _i(r, "Category") != 1219 or _i(r, "CategoryRecoveryTime") != 15000:
        bad.append(f"100: Category/CategoryRecoveryTime {r.get('Category')}/{r.get('CategoryRecoveryTime')}, "
                   "expected 1219 / 15000")
    text = str(r.get("Description_Lang_enUS") or "")
    for frag in ("Out of combat you generate $/10;s2 rage",
                 "in combat you generate 5 to 10 rage, more the farther you charge",
                 "Usable in combat."):
        if frag not in text:
            bad.append(f"100: tooltip lacks {frag!r}")
    return bad


def check_intervene(rows: dict, dur6: int) -> list[str]:
    bad = _missing(rows, INTERVENE)
    if bad:
        return bad
    r = rows[INTERVENE]
    if _i(r, "Effect_1") != CHARGE or _i(r, "RangeIndex") != 95:
        bad.append("3411: effect 1 is not CHARGE / RangeIndex not 95")
    if (_i(r, "Effect_2"), _i(r, "EffectAura_2"), _i(r, "EffectMiscValue_2")) != \
            (APPLY_AURA, AURA_MOD_DAMAGE_TAKEN_PCT, 127):
        bad.append("3411: effect 2 is not APPLY_AURA 87 misc 127")
    if _i(r, "EffectBasePoints_2") != -11 or w0a.calc_value(r, 2, 60) != -10:
        bad.append(f"3411: effect 2 bp {r.get('EffectBasePoints_2')!r} (value {w0a.calc_value(r, 2, 60)}), "
                   "expected -11 (= -10%)")
    if _i(r, "DurationIndex") != dur6 or dur6 != 32:
        bad.append(f"3411: DurationIndex {r.get('DurationIndex')!r}, expected the stock 6 s row 32")
    if (_i(r, "SpellLevel"), _i(r, "BaseLevel")) != (30, 30):
        bad.append(f"3411: SpellLevel/BaseLevel {r.get('SpellLevel')}/{r.get('BaseLevel')}, expected 30/30")
    for col in ("ProcChance", "ProcCharges", "ProcTypeMask"):
        if _i(r, col) != 0:
            bad.append(f"3411: {col} {r.get(col)!r}, expected 0 (the old intercept aura's proc fields)")
    if r.get("Description_Lang_enUS") != \
            "Run at a party or raid member, reducing their damage taken by $s2% for $d.":
        bad.append(f"3411: tooltip {r.get('Description_Lang_enUS')!r}")
    if r.get("AuraDescription_Lang_enUS") != "Damage taken reduced.":
        bad.append(f"3411: aura text {r.get('AuraDescription_Lang_enUS')!r}")
    return bad


def check_shield_wall_and_regen(rows: dict) -> list[str]:
    bad = _missing(rows, SHIELD_WALL, ENRAGED_REGEN)
    if bad:
        return bad
    sw, er = rows[SHIELD_WALL], rows[ENRAGED_REGEN]
    if sw.get("Description_Lang_enUS") != "Reduces all damage taken by $s1% for $d.":
        bad.append(f"871: tooltip {sw.get('Description_Lang_enUS')!r}")
    if sw.get("AuraDescription_Lang_enUS") != "Damage taken reduced.":
        bad.append(f"871: aura text {sw.get('AuraDescription_Lang_enUS')!r}")
    if _i(sw, "Category") != 132 or (_i(sw, "StartRecoveryCategory"), _i(sw, "StartRecoveryTime")) != (0, 0):
        bad.append("871: Category not 132 or no longer off the GCD")
    if _i(er, "CasterAuraState") != 0:
        bad.append(f"55694: CasterAuraState {er.get('CasterAuraState')!r}, expected 0")
    if [i for i in (1, 2, 3) if _i(er, f"Effect_{i}")] != [1]:
        bad.append("55694: expected exactly one effect (eff1 immunity dropped)")
    if _i(er, "EffectAura_2") == 77 or _i(er, "EffectMiscValue_2"):
        bad.append("55694: the Enrage-immunity effect (aura 77 misc 31) is still there")
    if (_i(er, "SpellLevel"), _i(er, "BaseLevel")) != (56, 56):
        bad.append(f"55694: SpellLevel/BaseLevel {er.get('SpellLevel')}/{er.get('BaseLevel')}, expected 56/56")
    if er.get("Description_Lang_enUS") != "You regenerate $o1% of your maximum health over $d.":
        bad.append(f"55694: tooltip {er.get('Description_Lang_enUS')!r}")
    if er.get("AuraDescription_Lang_enUS") != "Regenerating health.":
        bad.append(f"55694: aura text {er.get('AuraDescription_Lang_enUS')!r}")
    return bad


def check_recklessness_impale(rows: dict, procs: list[dict]) -> list[str]:
    bad = _missing(rows, RECKLESSNESS, IMPALE_1, IMPALE_2)
    if bad:
        return bad
    r = rows[RECKLESSNESS]
    if (_i(r, "StartRecoveryCategory"), _i(r, "StartRecoveryTime")) != (0, 0):
        bad.append(f"1719: GCD {r.get('StartRecoveryCategory')}/{r.get('StartRecoveryTime')}, expected 0/0")
    if _i(r, "Category") != 132 or _i(r, "CategoryRecoveryTime") != 12000:
        bad.append("1719: Category 132 / 12 s lockout with Shield Wall not kept")
    if _eff_mask(r) != (0, 0, GROUP_BIT):
        bad.append(f"1719: eff0 mask {tuple(hex(x) for x in _eff_mask(r))}, expected (0, 0, 0x8)")
    if _u32(r.get(M1)) & 0x10 == 0:
        bad.append("1719: lost its identity bit d0 b4")
    # S3 B-R1: Recklessness has NO spell_proc row (Player::RemoveSpellMods spends one charge per Spell at finish, after
    # every target and synchronous child) and raw ProcTypeMask 0 so none is auto-generated; the old W0b / S3-D6 phase
    # rows are gone (remove_spell_proc(1719) is pinned in test_warrior_s3.py)
    if any(int(p["SpellId"]) == RECKLESSNESS for p in procs):
        bad.append("1719: a spell_proc row is declared (S3 B-R1: none, ProcTypeMask 0)")
    if _i(r, "ProcTypeMask") != 0:
        bad.append(f"1719: ProcTypeMask {r.get('ProcTypeMask')!r}, expected 0 (no auto-generated proc row)")
    for sid in (IMPALE_1, IMPALE_2):
        # S2 (D24) adds Heroic Leap (d2 b0) and Colossus Smash (d2 b1) to the group bit: 0x8 -> 0xB; S3 (D35) adds
        # Rampage (d2 b2: its strikes are abilities): 0xB -> 0xF
        if _eff_mask(rows[sid]) != (0x26604CEE, 0xC745, 0xF):
            bad.append(f"{sid}: Impale mask {tuple(hex(x) for x in _eff_mask(rows[sid]))}, "
                       "expected (0x26604cee, 0xc745, 0xf)")
    return bad


def check_heroic_leap(rows: dict, entries: dict, custom_attrs: dict, range_50000: int) -> list[str]:
    bad = _missing(rows, HL_BUTTON, HL_LANDING, HL_FLIGHT)
    if bad:
        return bad
    b, l, f = rows[HL_BUTTON], rows[HL_LANDING], rows[HL_FLIGHT]
    if _i(b, "Targets") != 0x40:
        bad.append(f"204400: Targets {b.get('Targets')!r}, expected 0x40 (dest location)")
    if (_i(b, "Effect_1"), _i(b, "ImplicitTargetA_1")) != (DUMMY, 28):
        bad.append("204400: effect 1 is not DUMMY at A 28 (the ground cursor)")
    if _i(b, "RangeIndex") != 94:
        bad.append(f"204400: RangeIndex {b.get('RangeIndex')!r}, expected 94 (8-40 yd)")
    if (_i(b, "StartRecoveryCategory"), _i(b, "StartRecoveryTime")) != (0, 0):
        bad.append("204400: not off the GCD (StartRecovery 0/0)")
    if _i(b, "RecoveryTime") != 60000 or _i(b, "Category") != 0:
        bad.append(f"204400: RecoveryTime/Category {b.get('RecoveryTime')}/{b.get('Category')}, expected 60000 / 0")
    if _i(b, "ManaCost") != 0 or _i(b, "PowerType") not in (0, 1):
        bad.append("204400: carries a cost")
    if _u32(b.get("AttributesEx2")) & ATTR2_IGNORE_LOS:
        bad.append("204400: carries the ignore-line-of-sight bit (6544's, not copied)")
    if _i(b, "SpellIconID") != 3149:
        bad.append(f"204400: SpellIconID {b.get('SpellIconID')!r}, expected 3149")
    if _i(b, "DefenseType") != 2:
        bad.append("204400: DmgClass is not melee")
    if _mask(b, "SpellClassMask")[2] != HEROIC_LEAP_BIT or _mask(l, "SpellClassMask")[2] != HEROIC_LEAP_BIT:
        bad.append("204400/204401: SpellClassMask_3 is not exactly d2 b0")
    if (_i(l, "Effect_1"), _i(l, "ImplicitTargetA_1"), _i(l, "ImplicitTargetB_1")) != (SCHOOL_DAMAGE, 87, 16):
        bad.append("204401: effect 1 is not SCHOOL_DAMAGE at A 87 / B 16")
    pot = _potency(entries, HL_LANDING, 1)
    if (pot.get("kind"), pot.get("total_potency")) != ("direct", 117.0):
        bad.append(f"204401: potency {pot.get('kind')}/{pot.get('total_potency')}, expected direct/117")
    if _i(l, "EffectRadiusIndex_1") != 14:
        bad.append(f"204401: EffectRadiusIndex_1 {l.get('EffectRadiusIndex_1')!r}, expected 14 (8 yd)")
    if (_i(l, "SpellLevel"), _i(l, "BaseLevel")) != (38, 38) or (_i(b, "SpellLevel"), _i(b, "BaseLevel")) != (38, 38):
        bad.append("204400/204401: SpellLevel/BaseLevel is not 38/38")
    if _i(l, "RangeIndex") != range_50000 or range_50000 in (0, 1):
        bad.append(f"204401: RangeIndex {l.get('RangeIndex')!r}, expected the 50000 yd row {range_50000}")
    # 204402: the flight aura
    if (_i(f, "Effect_1"), _i(f, "EffectAura_1"), _i(f, "EffectMiscValue_1")) != \
            (APPLY_AURA, AURA_MECHANIC_IMMUNITY, 7):
        bad.append("204402: effect 1 is not root immunity (aura 77 misc 7)")
    if (_i(f, "Effect_2"), _i(f, "EffectAura_2")) != (APPLY_AURA, AURA_SAFE_FALL):
        bad.append("204402: effect 2 is not SAFE_FALL (144)")
    if _i(f, "DurationIndex") != 27:
        bad.append(f"204402: DurationIndex {f.get('DurationIndex')!r}, expected the 3 s row 27")
    if not custom_attrs.get(HL_FLIGHT, 0) & CU_AURA_CANNOT_BE_SAVED:
        bad.append("204402: no CU_AURA_CANNOT_BE_SAVED custom attribute")
    if _mask(f, "SpellClassMask")[2]:
        bad.append("204402: carries a family bit")
    if _u32(f.get("Attributes")) & 0x80000080 != 0x80000080:
        bad.append("204402: Attributes lacks DO_NOT_DISPLAY 0x80 (hidden, user 2026-10-29) or NO_AURA_CANCEL "
                   "0x80000000 (review R2)")
    return bad


def check_skull_banner(rows: dict, groups: list[dict], group_rules: list[dict], custom_attrs: dict, dur20: int,
                       dur2min: int) -> list[str]:
    bad = _missing(rows, SB_BUTTON, SB_BUFF, SB_RALLIED, SB_HORDE, VR_HEAL)
    if bad:
        return bad
    b, buff, ral, hor, heal = (rows[s] for s in (SB_BUTTON, SB_BUFF, SB_RALLIED, SB_HORDE, VR_HEAL))
    if _i(b, "RecoveryTime") != 180000 or _i(b, "Category") != 0:
        bad.append(f"204405: RecoveryTime/Category {b.get('RecoveryTime')}/{b.get('Category')}, expected 180000 / 0")
    if (_i(b, "StartRecoveryCategory"), _i(b, "StartRecoveryTime"), _i(b, "ManaCost")) != (0, 0, 0):
        bad.append("204405: not off the GCD or carries a cost")
    if (_i(b, "Effect_1"), _i(b, "ImplicitTargetA_1"), _i(b, "EffectMiscValue_1")) != (SUMMON, 47, SB_ALLIANCE_NPC):
        bad.append("204405: effect 1 is not SUMMON at A 47 misc 300370")
    if (_i(b, "Effect_2"), _i(b, "ImplicitTargetA_2"), _i(b, "EffectRadiusIndex_2")) != (DUMMY, 56, 23):
        bad.append("204405: effect 2 is not DUMMY at A 56 with radius index 23 (40 yd)")
    if (_i(b, "SpellLevel"), _i(b, "BaseLevel")) != (60, 60):
        bad.append(f"204405: SpellLevel/BaseLevel {b.get('SpellLevel')}/{b.get('BaseLevel')}, expected 60/60")
    if (_i(buff, "Effect_1"), _i(buff, "EffectAura_1")) != (APPLY_AURA, AURA_MOD_CRIT_PCT) or \
            w0a.calc_value(buff, 1, 60) != 10:
        bad.append(f"204406: not MOD_CRIT_PCT (290) +10 (value {w0a.calc_value(buff, 1, 60)})")
    if _i(buff, "DurationIndex") != dur20:
        bad.append(f"204406: DurationIndex {buff.get('DurationIndex')!r}, expected the 20 s row {dur20}")
    if not any(int(g["id"]) == 1296 and int(g["spell_id"]) == SB_BUFF for g in groups):
        bad.append("spell_group 1296 does not contain 204406")
    if sum(1 for g in groups if int(g["id"]) == 1296) != 1:
        bad.append("spell_group 1296 holds more than 204406")
    if not any(int(g["group_id"]) == 1296 and int(g["stack_rule"]) == 1 for g in group_rules):
        bad.append("spell_group 1296 has no stack_rule 1 (exclusive) row")
    if _i(ral, "DurationIndex") != dur2min:
        bad.append(f"204407: DurationIndex {ral.get('DurationIndex')!r}, expected the 2 min row {dur2min}")
    if not _u32(ral.get("AttributesEx3")) & ATTR3_ALLOW_AURA_WHILE_DEAD:
        bad.append("204407: AttributesEx3 0x100000 (persists through death) missing")
    if not custom_attrs.get(SB_RALLIED, 0) & CU_NEGATIVE_EFF0:
        bad.append("204407: CU_NEGATIVE_EFF0 custom attribute missing")
    if custom_attrs.get(SB_RALLIED, 0) & CU_AURA_CANNOT_BE_SAVED:
        bad.append("204407: marked unsaveable (it must be saved across logout)")
    if not _u32(ral.get("Attributes")) & 0x20000000:
        bad.append("204407: Attributes lacks NO_IMMUNITIES 0x20000000 (review R1: bubbles must not purge Rallied)")
    if _i(hor, "Effect_1") != SUMMON or _i(hor, "EffectMiscValue_1") != SB_HORDE_NPC:
        bad.append("204408: effect 1 is not SUMMON misc 300371")
    if (_i(heal, "Effect_1"), _i(heal, "ImplicitTargetA_1")) != (HEAL_PCT, 1) or w0a.calc_value(heal, 1, 60) != 20:
        bad.append(f"204409: not HEAL_PCT 20 at A 1 (value {w0a.calc_value(heal, 1, 60)})")
    return bad


def check_creatures(creatures: list[dict], models: list[dict]) -> list[str]:
    bad = []
    want = {SB_ALLIANCE_NPC: 14541, SB_HORDE_NPC: 14542}
    have = {int(c["entry"]): c for c in creatures}
    for entry, display in want.items():
        c = have.get(entry)
        if c is None:
            bad.append(f"creature {entry} is not declared")
            continue
        if int(c["faction"]) != 35 or int(c["unit_flags"]) != 0x2:
            bad.append(f"creature {entry}: faction/unit_flags {c['faction']}/{c['unit_flags']}, expected 35 / 0x2")
        mine = [m for m in models if int(m["CreatureID"]) == entry]
        if [int(m["CreatureDisplayID"]) for m in mine] != [display]:
            bad.append(f"creature {entry}: models {[m['CreatureDisplayID'] for m in mine]}, expected [{display}]")
    extra = set(have) - set(want)
    if extra:
        bad.append(f"unexpected creatures {sorted(extra)}")
    return bad


def check_victory_rush(rows: dict, entries: dict, dur20: int) -> list[str]:
    bad = _missing(rows, VICTORY_RUSH, VICTORIOUS)
    if bad:
        return bad
    vr, v = rows[VICTORY_RUSH], rows[VICTORIOUS]
    if (_i(vr, "SpellLevel"), _i(vr, "BaseLevel")) != (8, 8):
        bad.append(f"34428: SpellLevel/BaseLevel {vr.get('SpellLevel')}/{vr.get('BaseLevel')}, expected 8/8")
    pot = _potency(entries, VICTORY_RUSH, 1)
    if (pot.get("kind"), pot.get("total_potency")) != ("direct", 64.6):
        bad.append(f"34428: potency {pot.get('kind')}/{pot.get('total_potency')}, expected direct/64.6")
    if _u32(vr.get("SpellClassMask_3")) & GROUP_BIT == 0 or _u32(vr.get(M2)) & 0x100 == 0:
        bad.append("34428: lost d2 b3 or its identity bit d1 b8")
    if _i(vr, "CasterAuraState") != 10:
        bad.append(f"34428: CasterAuraState {vr.get('CasterAuraState')!r}, expected 10 (Victorious)")
    text = str(vr.get("Description_Lang_enUS") or "")
    if "$204409s1%" not in text or "of your maximum health" not in text:
        bad.append(f"34428: tooltip does not read the heal from 204409: {text!r}")
    # Victorious: visible buff
    attrs = _u32(v.get("Attributes"))
    if attrs & ATTR0_DO_NOT_DISPLAY or attrs != 256:
        bad.append(f"32216: Attributes {attrs:#x}, expected 256 (visible: 0x80 clear, 0x100 kept)")
    if v.get("AuraDescription_Lang_enUS") != "Victory Rush is usable.":
        bad.append(f"32216: aura text {v.get('AuraDescription_Lang_enUS')!r}")
    if _u32(v.get(M2)) != 0x40000:
        bad.append(f"32216: SpellClassMask_2 {_u32(v.get(M2)):#x}, expected d1 b18 (0x40000)")
    if _i(v, "DurationIndex") != dur20:
        bad.append(f"32216: DurationIndex {v.get('DurationIndex')!r}, expected the 20 s row {dur20}")
    return bad


def check_slas(slas: list[dict]) -> list[str]:
    want = {15058: (32215, 26, 2), 30840: (204400, 26, 0), 30841: (204405, 256, 0), 30842: (204404, 26, 2)}
    by_id = {int(s["id"]): s for s in slas}
    bad = []
    for sid, (spell, skill, acquire) in want.items():
        s = by_id.get(sid)
        if s is None:
            bad.append(f"SkillLineAbility {sid} is not declared")
            continue
        got = (int(s["spell_id"]), int(s["skill_line"]), int(s.get("acquire_method") or 0),
               int(s.get("class_mask") or 0))
        if got != (spell, skill, acquire, 1):
            bad.append(f"SkillLineAbility {sid}: (spell, skill, acquire, class) {got}, expected "
                       f"{(spell, skill, acquire, 1)}")
    return bad


def check_group_bits(rows: dict) -> list[str]:
    bad = _missing(rows, *G_CARRIERS)
    for sid, (col, bit) in G_CARRIERS.items():
        r = rows.get(sid)
        if r is None:
            continue
        if _u32(r.get("SpellClassMask_3")) & GROUP_BIT == 0:
            bad.append(f"{sid}: lacks d2 b3")
        if _u32(r.get(col)) & bit == 0:
            bad.append(f"{sid}: lost its identity bit {col} {bit:#x}")
    holders = {sid for sid, r in rows.items() if _u32(r.get("SpellClassMask_3")) & GROUP_BIT}
    for sid in sorted(holders - set(G_CARRIERS)):
        bad.append(f"{sid}: carries d2 b3 but is not a G carrier")
    leap = {sid for sid, r in rows.items() if _u32(r.get("SpellClassMask_3")) & HEROIC_LEAP_BIT}
    if leap != {HL_BUTTON, HL_LANDING}:
        bad.append(f"d2 b0 holders {sorted(leap)}, expected only [204400, 204401]")
    for sid in (HL_BUTTON, HL_LANDING):
        if sid in rows and _u32(rows[sid].get("SpellClassMask_3")) & GROUP_BIT:
            bad.append(f"{sid}: Heroic Leap carries d2 b3 (not in G)")
    return bad


def check_role_bits(rows: dict) -> list[str]:
    bad = []
    for name, (col, bit, owners) in ROLE_BITS.items():
        got = {sid for sid, r in rows.items() if _u32(r.get(col)) & bit}
        if got != owners:
            bad.append(f"{name}: carriers {sorted(got)}, expected exactly {sorted(owners)}")
        extra = got & set(W0B_NEW_IDS)
        if extra:
            bad.append(f"{name}: W0b rows {sorted(extra)} carry the bit")
    return bad


def check_trainers(trainers: list[dict]) -> list[str]:
    have = {(int(t["TrainerId"]), int(t["SpellId"])): int(t["ReqLevel"]) for t in trainers}
    bad = []
    for key, level in W0B_TRAINER_ROWS.items():
        if key not in have:
            bad.append(f"trainer {key[0]} has no row for {key[1]}")
        elif have[key] != level:
            bad.append(f"trainer {key[0]} spell {key[1]}: ReqLevel {have[key]}, expected {level}")
    got201 = {k: v for k, v in have.items() if k[0] == 201}
    if got201 != TRAINER_201:
        bad.append(f"trainer 201 rows {got201}, expected unchanged {TRAINER_201}")
    return bad


def check_bindings(names: list[dict], removals: list[dict]) -> list[str]:
    bad = []
    have = {(int(n["spell_id"]), n["ScriptName"]) for n in names}
    for b in sorted(BINDINGS - have):
        bad.append(f"binding {b} is not declared")
    for b in sorted(have - BINDINGS):
        bad.append(f"unexpected binding {b}")
    gone = {(int(n["spell_id"]), n["ScriptName"]) for n in removals}
    for b in sorted(W0B_UNBINDINGS - gone):
        bad.append(f"unbind {b} is not declared")
    return bad


def check_consts(consts: list[dict]) -> list[str]:
    have = {c["name"]: (c["value"], c["cpp_type"]) for c in consts}
    return [f"const {n}: {have.get(n)!r}, expected {v!r}" for n, v in W0B_CONSTS.items() if have.get(n) != v]


def check_header(text: str) -> list[str]:
    """The generated header's D31 constants; the SPELL_ / NPC_ names only once the header has been regenerated for
W0b."""
    bad = []
    cpp = {"uint32": "uint32", "float": "float"}
    for name, (value, kind) in W0B_CONSTS.items():
        literal = f"{value}f" if kind == "float" else str(value)
        if not re.search(rf"constexpr {cpp[kind]} {name} = {re.escape(literal)};", text):
            bad.append(f"header: constexpr {cpp[kind]} {name} = {literal}; not found")
    if "SPELL_SKULL_BANNER_204408" in text:     # the header has been regenerated for W0b
        for name, sid in HEADER_SPELL_NAMES.items():
            if not re.search(rf"constexpr uint32 {name} = {sid};", text):
                bad.append(f"header: {name} = {sid} not found")
    return bad


def check_header_npcs(text: str) -> list[str]:
    """Brief ruling 2: the two banner creatures' NPC_ names (header_gen only names creatures whose `_source_class` is
the
    class, so creatures declared under source/npcs/ are not in WarriorData.h unless the generator is taught)."""
    return [f"header: {name} = {entry} not found" for name, entry in HEADER_NPC_NAMES.items()
            if not re.search(rf"constexpr uint32 {name} = {entry};", text)]


def check_no_capstone(rows: dict) -> list[str]:
    ids = set(W0B_NEW_IDS) | {CHARGE_ID, INTERVENE, SHIELD_WALL, RECKLESSNESS, ENRAGED_REGEN, VICTORY_RUSH,
                              VICTORIOUS, OVERPOWER}
    return [f"{sid}: {col} contains 'Capstone'" for sid in sorted(ids) if sid in rows
            for col in ("Description_Lang_enUS", "AuraDescription_Lang_enUS")
            if "capstone" in str(rows[sid].get(col) or "").lower()]


# ---- real data ----------------------------------------------------------------------------------------------------

_CACHE: dict = {}


def _data() -> dict:
    if not _CACHE:
        base = w0a._data()
        package = base["package"]
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        stock = {name: list(state.load_stock_rows(table).values()) for name, table in {
            "spellcasttimes": dbcfmt.SPELLCASTTIMES, "spellduration": dbcfmt.SPELLDURATION,
            "spellrange": dbcfmt.SPELLRANGE, "spellradius": dbcfmt.SPELLRADIUS}.items()}
        reuse = ReuseContext(stock, ids_cfg)
        rows = {int(e["id"]): build.build_spell_row(e, reuse) for e in package.spells}
        npcs = registry.load_class_file(
            NPC_FILE, ids_cfg=ids_cfg, existing_creature_rows={},
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS)
        _CACHE.update(
            package=package, rows=rows, entries={int(e["id"]): e for e in package.spells}, npcs=npcs,
            custom_attrs={int(c["spell_id"]): int(c["attributes"]) for c in package.custom_attrs},
            dur20=reuse.duration_index(20000), dur6=reuse.duration_index(6000), dur2min=reuse.duration_index(120000),
            range_50000=reuse.range_index(50000.0),
        )
    return _CACHE


class WarriorW0bDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_overpower_charges(self):
        d = _data()
        self.assertClean(check_overpower(d["rows"], d["package"].spell_procs, d["dur20"]))

    def test_charge(self):
        self.assertClean(check_charge(_data()["rows"]))

    def test_intervene(self):
        d = _data()
        self.assertClean(check_intervene(d["rows"], d["dur6"]))

    def test_shield_wall_and_enraged_regeneration(self):
        self.assertClean(check_shield_wall_and_regen(_data()["rows"]))

    def test_recklessness_and_impale(self):
        d = _data()
        self.assertClean(check_recklessness_impale(d["rows"], d["package"].spell_procs))

    def test_heroic_leap(self):
        d = _data()
        self.assertClean(check_heroic_leap(d["rows"], d["entries"], d["custom_attrs"], d["range_50000"]))

    def test_skull_banner(self):
        d = _data()
        p = d["package"]
        self.assertClean(check_skull_banner(d["rows"], p.spell_groups, p.spell_group_rules, d["custom_attrs"],
                                            d["dur20"], d["dur2min"]))

    def test_banner_creatures(self):
        n = _data()["npcs"]
        self.assertClean(check_creatures(n.creature_templates, n.creature_template_models))

    def test_victory_rush_and_victorious(self):
        d = _data()
        self.assertClean(check_victory_rush(d["rows"], d["entries"], d["dur20"]))

    def test_skill_line_abilities(self):
        self.assertClean(check_slas(_data()["package"].skill_line_abilities))

    def test_group_bit_carriers(self):
        self.assertClean(check_group_bits(_data()["rows"]))

    def test_role_bit_pins(self):
        self.assertClean(check_role_bits(_data()["rows"]))

    def test_trainers(self):
        self.assertClean(check_trainers(_data()["package"].trainer_spells))

    def test_bindings(self):
        p = _data()["package"]
        self.assertClean(check_bindings(p.spell_script_names, p.script_removals))

    def test_consts(self):
        self.assertClean(check_consts(_data()["package"].consts))

    def test_generated_header(self):
        if not HEADER_FILE.is_file():
            self.skipTest("Generated/WarriorData.h does not exist")
        self.assertClean(check_header(HEADER_FILE.read_text(encoding="utf-8")))

    # NPC_SKULL_BANNER_* are not asserted against WarriorData.h: header_gen emits only creatures declared in the warrior
    # package, and the banners live in source/npcs/warrior_npcs.py (no C++ reads them; the summon is by data).

    def test_no_capstone_text(self):
        self.assertClean(check_no_capstone(_data()["rows"]))

    def test_w0b_ids_are_inside_the_frozen_block(self):
        rows = _data()["rows"]
        self.assertEqual([sid for sid in W0B_NEW_IDS if sid not in rows], [])
        # S1 adds exactly 204770 (Empowered Revenge), 204774 (Improved Bloodrage buff), 204775 (Bloodstorm tick)
        s1_ids = [204770, 204774, 204775]
        # S2 adds the contiguous run 204490-204544 (test_warrior_s2.py pins it)
        s2_ids = list(range(204490, 204545))
        # S3 adds the contiguous run 204630-204680 (test_warrior_s3.py pins it)
        s3_ids = list(range(204630, 204681))
        self.assertEqual(sorted(sid for sid in rows if 204400 <= sid <= 204899),
                         list(W0B_NEW_IDS) + s2_ids + s3_ids + s1_ids)


# ---- negative fixtures: every check must fire on a minimal bad mutation of the real built rows -------------------

def _mut(rows: dict, sid: int, **cols) -> dict:
    return {**rows, sid: {**rows[sid], **cols}}


def _only(rows: dict, *ids: int) -> dict:
    return {sid: rows[sid] for sid in ids}


class WarriorW0bNegativeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = _data()
        cls.rows = cls.d["rows"]

    def test_overpower_charges(self):
        rows, procs, dur = self.rows, self.d["package"].spell_procs, self.d["dur20"]
        self.assertEqual(check_overpower(rows, procs, dur), [])
        for sid, col, val in (
                (OVERPOWER, "AttributesEx", _u32(rows[OVERPOWER].get("AttributesEx")) | ATTR1_FINISHING_MOVE),
                (OVERPOWER, "CasterAuraSpell", 0), (OVERPOWER, "SpellClassMask_3", 0),
                (OP_CHARGE, "CumulativeAura", 1), (OP_CHARGE, "DurationIndex", 21), (OP_CHARGE, "Attributes", 0x40),
                (OP_CHARGE, "Attributes", 0x80), (OP_CHARGE, "EffectAura_1", 3),
                (OP_CHARGE, "AuraDescription_Lang_enUS", ""), (OP_TRAINING, "ProcTypeMask", 0),
                (OP_TRAINING, "EffectTriggerSpell_1", 0), (OP_TRAINING, "Attributes", 0x40),
                (OP_TRAINING, "EffectAura_1", AURA_DUMMY)):
            self.assertGreaterEqual(len(check_overpower(_mut(rows, sid, **{col: val}), procs, dur)), 1, (sid, col))
        self.assertGreaterEqual(len(check_overpower({k: v for k, v in rows.items() if k != OP_CHARGE}, procs, dur)), 1)
        for sid, col, val in ((OP_CHARGE, "ProcFlags", 0x14), (OP_CHARGE, "SpellFamilyMask0", 0x8),
                              (OP_CHARGE, "SpellPhaseMask", 2), (OP_CHARGE, "AttributesMask", 0),
                              (OP_CHARGE, "Charges", 1), (OP_CHARGE, "SpellFamilyName", 0), (OP_CHARGE, "Chance", 0.0),
                              (OP_TRAINING, "ProcFlags", 0x2A8 | 0x4), (OP_TRAINING, "ProcFlags", 0x28),
                              (OP_TRAINING, "HitMask", 0), (OP_TRAINING, "HitMask", 0x70),
                              (OP_TRAINING, "SpellPhaseMask", 2), (OP_TRAINING, "Chance", 50.0)):
            bad = [{**p, col: val} if int(p["SpellId"]) == sid else p for p in procs]
            self.assertGreaterEqual(len(check_overpower(rows, bad, dur)), 1, (sid, col))
        rest = [p for p in procs if int(p["SpellId"]) != OP_CHARGE]
        self.assertGreaterEqual(len(check_overpower(rows, rest, dur)), 1)
        rest = [p for p in procs if int(p["SpellId"]) != OP_TRAINING]
        self.assertGreaterEqual(len(check_overpower(rows, rest, dur)), 1)
        self.assertGreaterEqual(len(check_overpower(rows, procs, dur + 1)), 1)

    def test_charge(self):
        # the built Attributes is checked on the real row in WarriorW0bDataTest; the negatives start from a clean copy
        rows = _mut(self.rows, CHARGE_ID, Attributes=0x20050010)
        self.assertEqual(check_charge(rows), [])
        for col, val in (("Attributes", 0x30050010), ("Attributes", 0x20050011), ("Category", 0),
                         ("CategoryRecoveryTime", 20000),
                         ("Description_Lang_enUS", "Charge an enemy, stunning it briefly. You generate 15 rage."),
                         ("Description_Lang_enUS", "Charge an enemy. Out of combat you generate $/10;s2 rage; "
                                                   "in combat you generate 5 to 10 rage, "
                                                   "more the farther you charge.")):
            self.assertGreaterEqual(len(check_charge(_mut(rows, CHARGE_ID, **{col: val}))), 1, (col, val))
        self.assertEqual(len(check_charge({})), 1)

    def test_intervene(self):
        rows, dur6 = self.rows, self.d["dur6"]
        self.assertEqual(check_intervene(rows, dur6), [])
        for col, val in (("EffectAura_2", 111), ("EffectMiscValue_2", 1), ("EffectBasePoints_2", -6),
                         ("EffectBasePoints_2", 9), ("DurationIndex", 1), ("SpellLevel", 70), ("BaseLevel", 70),
                         ("ProcChance", 100), ("ProcCharges", 1), ("ProcTypeMask", 680), ("Effect_1", APPLY_AURA),
                         ("RangeIndex", 1), ("Description_Lang_enUS", "Run at a party member."),
                         ("AuraDescription_Lang_enUS", "")):
            self.assertGreaterEqual(len(check_intervene(_mut(rows, INTERVENE, **{col: val}), dur6)), 1, (col, val))
        self.assertGreaterEqual(len(check_intervene(rows, dur6 + 1)), 1)       # a minted 6 s row instead of stock 32
        self.assertEqual(len(check_intervene({}, dur6)), 1)

    def test_shield_wall_and_enraged_regeneration(self):
        rows = self.rows
        self.assertEqual(check_shield_wall_and_regen(rows), [])
        for sid, col, val in (
                (SHIELD_WALL, "Description_Lang_enUS", "Reduces damage taken."),
                (SHIELD_WALL, "AuraDescription_Lang_enUS", ""),
                (SHIELD_WALL, "Category", 0), (SHIELD_WALL, "StartRecoveryTime", 1500),
                (ENRAGED_REGEN, "CasterAuraState", 17), (ENRAGED_REGEN, "Effect_2", APPLY_AURA),
                (ENRAGED_REGEN, "Effect_3", APPLY_AURA), (ENRAGED_REGEN, "SpellLevel", 75),
                (ENRAGED_REGEN, "BaseLevel", 75), (ENRAGED_REGEN, "Description_Lang_enUS", ""),
                (ENRAGED_REGEN, "AuraDescription_Lang_enUS", "")):
            self.assertGreaterEqual(len(check_shield_wall_and_regen(_mut(rows, sid, **{col: val}))), 1, (sid, col))
        bad = _mut(rows, ENRAGED_REGEN, Effect_2=APPLY_AURA, EffectAura_2=77, EffectMiscValue_2=31)
        self.assertGreaterEqual(len(check_shield_wall_and_regen(bad)), 2)

    def test_recklessness_and_impale(self):
        rows, procs = self.rows, self.d["package"].spell_procs
        self.assertEqual(check_recklessness_impale(rows, procs), [])
        for sid, col, val in (
                (RECKLESSNESS, "StartRecoveryCategory", 133), (RECKLESSNESS, "StartRecoveryTime", 1500),
                (RECKLESSNESS, "Category", 0), (RECKLESSNESS, "CategoryRecoveryTime", 0),
                (RECKLESSNESS, "EffectSpellClassMaskA_1", 0x2E600444),
                (RECKLESSNESS, "EffectSpellClassMaskA_2", 0x404745),
                (RECKLESSNESS, "EffectSpellClassMaskA_3", 0), (RECKLESSNESS, "EffectSpellClassMaskA_3", 0x80000008),
                (RECKLESSNESS, "SpellClassMask_1", 0),
                (IMPALE_1, "EffectSpellClassMaskA_1", 0xEE604CEE), (IMPALE_1, "EffectSpellClassMaskA_3", 0),
                (IMPALE_2, "EffectSpellClassMaskA_2", 0xC744), (IMPALE_2, "EffectSpellClassMaskA_3", 0x10)):
            self.assertGreaterEqual(len(check_recklessness_impale(_mut(rows, sid, **{col: val}), procs)), 1, (sid, col))
        # S3 B-R1: a spell_proc row for 1719 (the old live phase-2 row or an S3-D6 CAST row) is a problem, and so is a
        # non-zero ProcTypeMask (it would auto-generate one)
        for row in ({"SpellId": RECKLESSNESS, "SpellFamilyName": 4, "SpellFamilyMask2": 8, "SpellTypeMask": 1,
                     "SpellPhaseMask": 2, "AttributesMask": 8},
                    {"SpellId": RECKLESSNESS, "SpellPhaseMask": 1}):
            self.assertGreaterEqual(len(check_recklessness_impale(rows, [*procs, row])), 1, row)
        self.assertGreaterEqual(len(check_recklessness_impale(_mut(rows, RECKLESSNESS, ProcTypeMask=4368), procs)), 1)
        self.assertGreaterEqual(len(check_recklessness_impale(_mut(rows, RECKLESSNESS, ProcTypeMask=16), procs)), 1)
        for sid in (IMPALE_1, IMPALE_2):                       # S2's 0xB pin moved to 0xF (S3 D35)
            for bad in (0xB, 0x7, 0xE, 0x8):
                self.assertGreaterEqual(len(check_recklessness_impale(
                    _mut(rows, sid, EffectSpellClassMaskA_3=bad), procs)), 1, (sid, bad))

    def test_heroic_leap(self):
        rows, ents, ca, r50 = self.rows, self.d["entries"], self.d["custom_attrs"], self.d["range_50000"]
        self.assertEqual(check_heroic_leap(rows, ents, ca, r50), [])
        for sid, col, val in (
                (HL_BUTTON, "Targets", 0), (HL_BUTTON, "ImplicitTargetA_1", 89), (HL_BUTTON, "Effect_1", SCHOOL_DAMAGE),
                (HL_BUTTON, "RangeIndex", 95), (HL_BUTTON, "StartRecoveryTime", 1500),
                (HL_BUTTON, "StartRecoveryCategory", 133),
                (HL_BUTTON, "RecoveryTime", 30000), (HL_BUTTON, "Category", 1219), (HL_BUTTON, "ManaCost", 100),
                (HL_BUTTON, "AttributesEx2", 0x4), (HL_BUTTON, "SpellIconID", 1), (HL_BUTTON, "DefenseType", 0),
                (HL_BUTTON, "SpellClassMask_3", 0), (HL_BUTTON, "SpellClassMask_3", 9), (HL_BUTTON, "SpellLevel", 40),
                (HL_LANDING, "SpellClassMask_3", 8), (HL_LANDING, "ImplicitTargetB_1", 15),
                (HL_LANDING, "ImplicitTargetA_1", 6), (HL_LANDING, "EffectRadiusIndex_1", 13),
                (HL_LANDING, "Effect_1", DUMMY), (HL_LANDING, "BaseLevel", 1), (HL_LANDING, "RangeIndex", 1),
                (HL_FLIGHT, "EffectAura_1", 4), (HL_FLIGHT, "EffectMiscValue_1", 0), (HL_FLIGHT, "EffectAura_2", 4),
                (HL_FLIGHT, "DurationIndex", 18), (HL_FLIGHT, "SpellClassMask_3", 1)):
            self.assertGreaterEqual(len(check_heroic_leap(_mut(rows, sid, **{col: val}), ents, ca, r50)), 1, (sid, col))
        for key, val in (("total_potency", 100.0), ("kind", "periodic")):
            e2 = copy.deepcopy(ents)
            e2[HL_LANDING]["effect1"]["_potency"][key] = val
            self.assertGreaterEqual(len(check_heroic_leap(rows, e2, ca, r50)), 1, key)
        self.assertGreaterEqual(len(check_heroic_leap(rows, ents, {}, r50)), 1)      # the flight aura could be saved
        self.assertGreaterEqual(len(check_heroic_leap(rows, ents, ca, r50 + 1)), 1)

    def test_skull_banner(self):
        rows, p = self.rows, self.d["package"]
        groups, rules, ca, d20, d2m = p.spell_groups, p.spell_group_rules, self.d["custom_attrs"], self.d["dur20"], \
            self.d["dur2min"]
        self.assertEqual(check_skull_banner(rows, groups, rules, ca, d20, d2m), [])
        for sid, col, val in (
                (SB_BUTTON, "RecoveryTime", 120000), (SB_BUTTON, "Category", 1), (SB_BUTTON, "StartRecoveryTime", 1500),
                (SB_BUTTON, "ManaCost", 50), (SB_BUTTON, "Effect_1", DUMMY), (SB_BUTTON, "ImplicitTargetA_1", 1),
                (SB_BUTTON, "EffectMiscValue_1", 300371), (SB_BUTTON, "ImplicitTargetA_2", 57),
                (SB_BUTTON, "EffectRadiusIndex_2", 22), (SB_BUTTON, "SpellLevel", 30), (SB_BUTTON, "BaseLevel", 30),
                (SB_BUFF, "EffectAura_1", 52), (SB_BUFF, "EffectBasePoints_1", 4), (SB_BUFF, "DurationIndex", 21),
                (SB_RALLIED, "DurationIndex", 21), (SB_RALLIED, "AttributesEx3", 0),
                (SB_HORDE, "EffectMiscValue_1", 300370),
                (SB_HORDE, "Effect_1", DUMMY), (VR_HEAL, "Effect_1", 10), (VR_HEAL, "EffectBasePoints_1", 9),
                (VR_HEAL, "ImplicitTargetA_1", 6)):
            self.assertGreaterEqual(
                len(check_skull_banner(_mut(rows, sid, **{col: val}), groups, rules, ca, d20, d2m)), 1, (sid, col))
        self.assertGreaterEqual(len(check_skull_banner(rows, [], rules, ca, d20, d2m)), 1)
        self.assertGreaterEqual(len(check_skull_banner(
            rows, groups + [{"id": 1296, "spell_id": 1}], rules, ca, d20, d2m)), 1)
        self.assertGreaterEqual(len(check_skull_banner(rows, groups, [], ca, d20, d2m)), 1)
        self.assertGreaterEqual(len(check_skull_banner(rows, groups, [{**rules[0], "stack_rule": 4}], ca, d20, d2m)), 1)
        self.assertGreaterEqual(len(check_skull_banner(rows, groups, rules, {}, d20, d2m)), 1)
        saved = {**ca, SB_RALLIED: 0x1001000}
        self.assertGreaterEqual(len(check_skull_banner(rows, groups, rules, saved, d20, d2m)), 1)
        self.assertGreaterEqual(len(check_skull_banner(rows, groups, rules, ca, d20 + 1, d2m)), 1)
        self.assertGreaterEqual(len(check_skull_banner(rows, groups, rules, ca, d20, d2m + 1)), 1)

    def test_creatures(self):
        n = self.d["npcs"]
        cs, ms = n.creature_templates, n.creature_template_models
        self.assertEqual(check_creatures(cs, ms), [])
        for col, val in (("faction", 14), ("unit_flags", 0)):
            bad = [{**c, col: val} if int(c["entry"]) == SB_HORDE_NPC else c for c in cs]
            self.assertEqual(len(check_creatures(bad, ms)), 1, col)
        bad_models = [{**m, "CreatureDisplayID": 14541} if int(m["CreatureID"]) == SB_HORDE_NPC else m for m in ms]
        self.assertEqual(len(check_creatures(cs, bad_models)), 1)
        self.assertEqual(len(check_creatures(cs[:1], ms)), 1)
        self.assertEqual(len(check_creatures(cs, [m for m in ms if int(m["CreatureID"]) != SB_ALLIANCE_NPC])), 1)
        self.assertEqual(len(check_creatures(cs + [{**cs[0], "entry": 300372}], ms)), 1)

    def test_victory_rush_and_victorious(self):
        rows, ents, d20 = self.rows, self.d["entries"], self.d["dur20"]
        self.assertEqual(check_victory_rush(rows, ents, d20), [])
        for sid, col, val in (
                (VICTORY_RUSH, "SpellLevel", 6), (VICTORY_RUSH, "BaseLevel", 6), (VICTORY_RUSH, "SpellClassMask_3", 0),
                (VICTORY_RUSH, "CasterAuraState", 0), (VICTORY_RUSH, "Description_Lang_enUS", "Heal for 20%."),
                (VICTORIOUS, "Attributes", 384), (VICTORIOUS, "Attributes", 257), (VICTORIOUS, "Attributes", 0x80),
                (VICTORIOUS, "AuraDescription_Lang_enUS", ""), (VICTORIOUS, "SpellClassMask_2", 0x100),
                (VICTORIOUS, "DurationIndex", d20 + 1)):
            self.assertGreaterEqual(len(check_victory_rush(_mut(rows, sid, **{col: val}), ents, d20)), 1, (sid, col))
        e2 = copy.deepcopy(ents)
        e2[VICTORY_RUSH]["effect1"]["_potency"]["total_potency"] = 45.0
        self.assertGreaterEqual(len(check_victory_rush(rows, e2, d20)), 1)

    def test_slas(self):
        slas = self.d["package"].skill_line_abilities
        self.assertEqual(check_slas(slas), [])
        for sid in (15058, 30840, 30841, 30842):
            self.assertEqual(len(check_slas([s for s in slas if int(s["id"]) != sid])), 1, sid)
            for col, val in (("skill_line", 257), ("acquire_method", 5), ("class_mask", 2), ("spell_id", 78)):
                bad = [{**s, col: val} if int(s["id"]) == sid else s for s in slas]
                self.assertGreaterEqual(len(check_slas(bad)), 1, (sid, col))

    def test_group_bits(self):
        rows = self.rows
        self.assertEqual(check_group_bits(rows), [])
        for sid in G_CARRIERS:                                       # a carrier loses d2 b3
            self.assertGreaterEqual(len(check_group_bits(_mut(rows, sid, SpellClassMask_3=0))), 1, sid)
            col, bit = G_CARRIERS[sid]                               # ... or its identity bit
            self.assertGreaterEqual(len(check_group_bits(_mut(rows, sid, **{col: 0}))), 1, sid)
        # a non-carrier gains d2 b3
        for sid in (694, 5308, 46924, 6343, 772, 46968, 64380, HL_BUTTON, HL_LANDING, CHARGE_ID):
            if sid in rows:
                self.assertGreaterEqual(len(check_group_bits(_mut(rows, sid, SpellClassMask_3=8))), 1, sid)
        self.assertGreaterEqual(len(check_group_bits(_mut(rows, 5308, SpellClassMask_3=1))), 1)        # a stray d2 b0
        self.assertGreaterEqual(len(check_group_bits(_mut(rows, HL_BUTTON, SpellClassMask_3=0))), 1)
        self.assertGreaterEqual(len(check_group_bits({k: v for k, v in rows.items() if k != 20647})), 1)

    def test_role_bits(self):
        rows = self.rows
        self.assertEqual(check_role_bits(rows), [])
        for name, (col, bit, owners) in ROLE_BITS.items():
            self.assertGreaterEqual(len(check_role_bits(_mut(rows, HL_BUTTON, **{col: bit}))), 1, name)   # a W0b row
            self.assertGreaterEqual(len(check_role_bits(_mut(rows, 78, **{col: bit}))), 1, name)           # a stranger
            if owners:
                owner = min(owners)
                # an owner loses it
                self.assertGreaterEqual(len(check_role_bits(_mut(rows, owner, **{col: 0}))), 1, name)

    def test_trainers(self):
        good = [{"TrainerId": t, "SpellId": s, "ReqLevel": lv}
                for (t, s), lv in {**W0B_TRAINER_ROWS, **TRAINER_201}.items()]
        self.assertEqual(check_trainers(good), [])
        self.assertEqual(check_trainers(self.d["package"].trainer_spells), [])
        for i, row in enumerate(good):
            self.assertGreaterEqual(len(check_trainers(good[:i] + good[i + 1:])), 1, row)
            later = good[:i] + [{**row, "ReqLevel": row["ReqLevel"] + 1}] + good[i + 1:]
            self.assertGreaterEqual(len(check_trainers(later)), 1, row)
        self.assertEqual(len(check_trainers(good + [{"TrainerId": 201, "SpellId": 34428, "ReqLevel": 8}])), 1)

    def test_bindings(self):
        p = self.d["package"]
        names, rem = p.spell_script_names, p.script_removals
        self.assertEqual(check_bindings(names, rem), [])
        for i in range(len(names)):
            self.assertEqual(len(check_bindings(names[:i] + names[i + 1:], rem)), 1, i)
        extra = {"spell_id": 7384, "ScriptName": "spell_warr_overpower_x"}
        self.assertEqual(len(check_bindings(names + [extra], rem)), 1)
        self.assertEqual(len(check_bindings(
            [{**n, "ScriptName": "spell_warr_charge"} if int(n["spell_id"]) == -100 else n for n in names], rem)), 2)
        for gone in (-100, 3411):
            self.assertEqual(len(check_bindings(names, [r for r in rem if int(r["spell_id"]) != gone])), 1, gone)

    def test_consts(self):
        consts = self.d["package"].consts
        self.assertEqual(check_consts(consts), [])
        for i, n in enumerate(W0B_CONSTS):
            bad = [{**c, "value": 7} if c["name"] == n else c for c in consts]
            self.assertEqual(len(check_consts(bad)), 1, n)
            self.assertEqual(len(check_consts([c for c in consts if c["name"] != n])), 1, n)
        self.assertEqual(len(check_consts([{**c, "cpp_type": "int32"} if c["name"] == "HEROIC_LEAP_AIR_MS" else c
                                           for c in consts])), 1)

    def test_header(self):
        good = "\n".join(
            [f"constexpr {kind} {n} = {f'{v}f' if kind == 'float' else v};" for n, (v, kind) in W0B_CONSTS.items()])
        self.assertEqual(check_header(good), [])
        self.assertEqual(len(check_header(good.replace("= 1000;", "= 900;"))), 1)
        self.assertEqual(len(check_header(good.replace("constexpr float CHARGE_COMBAT_MAX_YD = 25.0f;", ""))), 1)
        self.assertEqual(len(check_header(good.replace("uint32", "int32"))), 1)
        names = "\n".join(f"constexpr uint32 {n} = {i};" for n, i in HEADER_SPELL_NAMES.items())
        npcs = "\n".join(f"constexpr uint32 {n} = {i};" for n, i in HEADER_NPC_NAMES.items())
        self.assertEqual(check_header(good + "\n" + names), [])
        bad = names.replace("SPELL_RALLIED = 204407", "SPELL_RALLIED = 1")
        self.assertEqual(len(check_header(good + "\n" + bad)), 1)
        self.assertEqual(len(check_header(good + "\n" + names.replace("SPELL_LEAPING", "SPELL_X"))), 1)
        self.assertEqual(check_header_npcs(npcs), [])
        self.assertEqual(len(check_header_npcs(npcs.replace("NPC_SKULL_BANNER_HORDE", "NPC_X"))), 1)
        self.assertEqual(len(check_header_npcs(npcs.replace("300370", "1"))), 1)
        self.assertEqual(len(check_header_npcs(good)), 2)

    def test_no_capstone(self):
        rows = self.rows
        self.assertEqual(check_no_capstone(rows), [])
        for sid in (CHARGE_ID, HL_BUTTON, SB_BUFF):
            self.assertEqual(len(check_no_capstone(_mut(rows, sid, Description_Lang_enUS="Capstone Bonus: x"))), 1, sid)
        self.assertEqual(len(check_no_capstone(_mut(rows, SB_RALLIED, AuraDescription_Lang_enUS="capstone"))), 1)
        self.assertEqual(check_no_capstone(_mut(rows, 78, Description_Lang_enUS="Capstone")), [])   # not a W0b row

    def test_checks_see_only_real_rows(self):
        # a fixture of just the needed rows still passes: the checks read nothing outside their ids
        d = self.d
        self.assertEqual(check_charge(_only(_mut(self.rows, CHARGE_ID, Attributes=0x20050010), CHARGE_ID)), [])
        self.assertEqual(check_intervene(_only(self.rows, INTERVENE), d["dur6"]), [])


if __name__ == "__main__":
    unittest.main()
