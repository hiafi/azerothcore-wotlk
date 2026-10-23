"""
Shaman playtest fix pass 2 (2026-10-22, .agents/plans/shaman-rework/shaman-rework.PLAYTEST-FIX2-REPORT.md).

P5  Summon Storm Elemental (202273) and its totem passive (202275) carry the custom SpellIcon 90270, which build_patch_i.py mines
    from the Ascension patch-I (inv_stormelemental.blp).
P6  Call of Thunder's capstone is "Thunderstorm restores 100% more mana": a pct SPELLMOD_EFFECT2 +100 on Thunderstorm's energize;
    the stun-castable Thunderstorm rank 202594, its SkillLineAbility 30691, the superseded edit of 17659 and the rank-sync C++ are gone.
P7  Call of the Elements puts none of the elementals on cooldown: the summons are triggered (no server cooldown) and the script tells the
    client to drop the cooldown its own SMSG_SPELL_GO prediction started (source pin on spell_shaman_totems.cpp).
P8  Elemental Ascendance (202390) carries the body-lightning state visual (SpellVisual 12914); the singles carry none.

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_shaman_playtest_fix2.py -q
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.test_shaman_sh0b import _data as _shaman_data  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
SCRIPTS = REPO_ROOT / "src" / "server" / "scripts" / "Spells"
UNIT = REPO_ROOT / "src" / "server" / "game" / "Entities" / "Unit"

# P5
STORM_ELEMENTAL_ICON = 90270
STORM_ELEMENTAL_ICON_PATH = "Interface/icons/inv_stormelemental.blp"
STORM_ELEMENTAL_SPELLS = (202273, 202275)
SHAMAN_SPELLICON_RESERVATION = (90270, 90309)

# P6
THUNDERSTORM = 51490
COT_CAPSTONE = 202534
COT_RANKS = (16041, 202533, 202534)
REMOVED_THUNDERSTORM_RANK2 = 202594
REMOVED_SLA = 30691
STUN_SUPERSEDE_SLA = 17659
THUNDERSTORM_D1 = 0x2000                  # d1 b13
ENERGIZE_PCT = 137
AURA_ADD_FLAT_MODIFIER, AURA_ADD_PCT_MODIFIER = 107, 108
SPELLMOD_EFFECT2 = 12

# P8
ELEMENTAL_ASCENDANCE = 202390
SINGLE_ASCENDANCES = (202387, 202388, 202389)
STORM_CLOUD_VISUAL = 12914                # "Arcane Surge" 61272: StateKit 11998 = Lightning_PreCast_Low_Hand ChestEffect, scale 3.0


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


# ---- checks (pure: rows / declared entries / text in, problems out) ---------------------------------------------

def check_storm_icon(rows: dict, icons: dict[int, str], spells=STORM_ELEMENTAL_SPELLS) -> list[str]:
    bad = []
    for sid in spells:
        row = rows.get(sid)
        if row is None:
            bad.append(f"{sid}: no row")
        elif int(row.get("SpellIconID") or 0) != STORM_ELEMENTAL_ICON:
            bad.append(f"{sid}: SpellIconID {row.get('SpellIconID')}, expected {STORM_ELEMENTAL_ICON}")
    if icons.get(STORM_ELEMENTAL_ICON) != STORM_ELEMENTAL_ICON_PATH:
        bad.append(f"build_patch_i.py: icon {STORM_ELEMENTAL_ICON} -> {icons.get(STORM_ELEMENTAL_ICON)!r}, "
                   f"expected {STORM_ELEMENTAL_ICON_PATH!r}")
    lo, hi = SHAMAN_SPELLICON_RESERVATION
    if not lo <= STORM_ELEMENTAL_ICON <= hi:
        bad.append(f"icon {STORM_ELEMENTAL_ICON} is outside the shaman reservation {lo}-{hi}")
    return bad


def _effect_slots(row: dict):
    for n in (1, 2, 3):
        yield n, {
            "effect": int(row.get(f"Effect_{n}") or 0),
            "aura": int(row.get(f"EffectAura_{n}") or 0),
            "misc": int(row.get(f"EffectMiscValue_{n}") or 0),
            "bp": int(row.get(f"EffectBasePoints_{n}") or 0),
            "mask": tuple(_u32(row.get(f"EffectSpellClassMask{'ABC'[n - 1]}_{d}")) for d in (1, 2, 3)),
        }


def check_cot_capstone(rows: dict) -> list[str]:
    """Rank 3 carries the energize mod (pct EFFECT2 +100, scoped to Thunderstorm only); ranks 1-2 carry none."""
    bad = []
    for sid in COT_RANKS:
        row = rows.get(sid)
        if row is None:
            bad.append(f"{sid}: no row")
            continue
        mods = [(n, s) for n, s in _effect_slots(row)
                if s["effect"] == 6 and s["aura"] in (AURA_ADD_FLAT_MODIFIER, AURA_ADD_PCT_MODIFIER) and s["misc"] == SPELLMOD_EFFECT2]
        if sid != COT_CAPSTONE:
            if mods:
                bad.append(f"{sid}: carries a SPELLMOD_EFFECT2 (only the capstone restores more mana)")
            continue
        if len(mods) != 1:
            bad.append(f"{sid}: {len(mods)} SPELLMOD_EFFECT2 effects, expected 1")
            continue
        n, s = mods[0]
        if s["aura"] != AURA_ADD_PCT_MODIFIER or s["bp"] != 99:
            bad.append(f"{sid}: effect {n} aura {s['aura']} base {s['bp']}, expected pct (108) +100% (stored 99)")
        if s["mask"] != (0, THUNDERSTORM_D1, 0):
            bad.append(f"{sid}: effect {n} mask {tuple(hex(x) for x in s['mask'])}, expected Thunderstorm d1 b13 only")
        text = str(row.get("Description_Lang_enUS") or "")
        if "Thunderstorm restores 100% more mana." not in text:
            bad.append(f"{sid}: tooltip lacks 'Thunderstorm restores 100% more mana.'")
        if "stunned" in text:
            bad.append(f"{sid}: tooltip still mentions stuns")
    r1 = rows.get(COT_RANKS[0])
    if r1 is not None and "stunned" in str(r1.get("Description_Lang_enUS") or ""):
        bad.append(f"{COT_RANKS[0]}: capstone line still mentions stuns")
    return bad


def check_thunderstorm_energize(rows: dict) -> list[str]:
    """The mod's target: Thunderstorm effect 2 must be the mana energize (ENERGIZE_PCT, mana), 10% base."""
    row = rows.get(THUNDERSTORM)
    if row is None:
        return [f"{THUNDERSTORM}: no row"]
    slot = dict(_effect_slots(row))[2]
    bad = []
    if slot["effect"] != ENERGIZE_PCT or slot["misc"] != 0:
        bad.append(f"{THUNDERSTORM}: effect 2 is {slot['effect']} misc {slot['misc']}, expected ENERGIZE_PCT on mana (the capstone mod's index)")
    if slot["bp"] != 9:
        bad.append(f"{THUNDERSTORM}: effect 2 base {slot['bp']}, expected 9 (10%); the capstone's +100% assumes it")
    return bad


def check_effect2_mod_scope(rows: dict, stock: dict) -> list[str]:
    """No other PERCENT SPELLMOD_EFFECT2 reaches Thunderstorm's bit, so the +100% cannot stack with anything else. The one FLAT
    mod that does (stock Glyph of Thunderstorm 62132, +2% mana) is added before the percent: (10 + 2) x 2 = 24%, intended."""
    bad = []
    for sid, row in {**stock, **rows}.items():
        if int(row.get("SpellClassSet") or 0) != 11 or sid == COT_CAPSTONE:
            continue
        for n, s in _effect_slots(row):
            if s["effect"] == 6 and s["aura"] == AURA_ADD_PCT_MODIFIER and s["misc"] == SPELLMOD_EFFECT2 \
                    and s["mask"][1] & THUNDERSTORM_D1:
                bad.append(f"{sid}: effect {n} percent SPELLMOD_EFFECT2 reaches Thunderstorm (d1 b13)")
    return bad


def check_second_thunderstorm_gone(rows: dict, sla: list[dict], bindings: list[dict]) -> list[str]:
    bad = []
    if REMOVED_THUNDERSTORM_RANK2 in rows:
        bad.append(f"{REMOVED_THUNDERSTORM_RANK2}: still built")
    for row in sla:
        if int(row["id"]) == REMOVED_SLA or int(row["spell_id"]) == REMOVED_THUNDERSTORM_RANK2:
            bad.append(f"SkillLineAbility {row['id']}: still declared for the removed rank")
        if int(row["id"]) == STUN_SUPERSEDE_SLA:
            bad.append(f"SkillLineAbility {STUN_SUPERSEDE_SLA}: the stock row is still overridden (it only superseded rank 1 by 202594)")
    bad += [f"spell_script_names {b['spell_id']} {b['ScriptName']}: still bound to the removed rank"
            for b in bindings if int(b["spell_id"]) == REMOVED_THUNDERSTORM_RANK2]
    return bad


def check_no_rank_sync(sources: dict[str, str]) -> list[str]:
    bad = []
    for name, text in sources.items():
        for token in ("SyncThunderstormRank", "SPELL_THUNDERSTORM_RANK2"):
            if token in text:
                bad.append(f"{name}: still references {token}")
    return bad


def check_cote_clears_client_cooldown(text: str) -> list[str]:
    """P7: after the triggered summons, the script restores the client's view of each summon spell it cast."""
    bad = []
    if "RestoreSummonCooldownDisplay" not in text:
        return ["spell_shaman_totems.cpp: no RestoreSummonCooldownDisplay"]
    body = text[text.index("RestoreSummonCooldownDisplay"):]
    for token in ("HasSpellCooldown", "ResendSpellCooldown", "RemoveSpellCooldown(spellId, true)", "AddEventAtOffset"):
        if token not in body:
            bad.append(f"RestoreSummonCooldownDisplay: no {token}")
    if "TRIGGERED_FULL_MASK" not in text or "summoned.push_back" not in text:
        bad.append("spell_sha_ele_call_of_the_elements: no longer collects its triggered summons")
    # the lockout must still skip triggered casts, so CotE itself starts no shared lockout
    lockout = text[text.index("class spell_sha_elemental_lockout"):]
    lockout = lockout[:lockout.index("Shaman::ApplyElementalLockout")]
    if "IsTriggered()" not in lockout:
        bad.append("spell_sha_elemental_lockout: no longer skips triggered casts")
    return bad


def check_ascendance_visuals(rows: dict) -> list[str]:
    bad = []
    row = rows.get(ELEMENTAL_ASCENDANCE)
    if row is None:
        return [f"{ELEMENTAL_ASCENDANCE}: no row"]
    if int(row.get("SpellVisualID_1") or 0) != STORM_CLOUD_VISUAL:
        bad.append(f"{ELEMENTAL_ASCENDANCE}: SpellVisualID_1 {row.get('SpellVisualID_1')}, expected the body-lightning visual {STORM_CLOUD_VISUAL}")
    if int(row.get("SpellVisualID_2") or 0):
        bad.append(f"{ELEMENTAL_ASCENDANCE}: SpellVisualID_2 {row.get('SpellVisualID_2')}, expected none")
    if int(row.get("Attributes") or 0) & 0x40:
        bad.append(f"{ELEMENTAL_ASCENDANCE}: passive (a passive aura is never sent to the client, so it shows nothing)")
    for sid in SINGLE_ASCENDANCES:
        single = rows.get(sid)
        if single is not None and int(single.get("SpellVisualID_1") or 0):
            bad.append(f"{sid}: a single Ascendance carries SpellVisualID_1 {single.get('SpellVisualID_1')} (singles stay unchanged)")
    return bad


# ---- real data ---------------------------------------------------------------------------------------------

def _build_patch_i_icons() -> dict[int, str]:
    spec = importlib.util.spec_from_file_location("build_patch_i_under_test", TOOL_ROOT / "build_patch_i.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {int(i): path for i, path in module.ICONS}


class ShamanPlaytestFix2Test(unittest.TestCase):
    def assertClean(self, problems):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_storm_elemental_icon(self):
        self.assertClean(check_storm_icon(_shaman_data()["rows_by_id"], _build_patch_i_icons()))

    def test_call_of_thunder_capstone(self):
        self.assertClean(check_cot_capstone(_shaman_data()["rows_by_id"]))

    def test_thunderstorm_energize_is_the_modded_effect(self):
        self.assertClean(check_thunderstorm_energize(_shaman_data()["rows_by_id"]))

    def test_no_other_effect2_mod_reaches_thunderstorm(self):
        d = _shaman_data()
        self.assertClean(check_effect2_mod_scope(d["rows_by_id"], d["stock"]))

    def test_second_thunderstorm_is_gone(self):
        d = _shaman_data()
        p = d["package"]
        self.assertClean(check_second_thunderstorm_gone(d["rows_by_id"], p.skill_line_abilities, p.spell_script_names))

    def test_rank_sync_removed_from_cpp(self):
        files = [UNIT / "ShamanMechanics.h", UNIT / "ShamanMechanics.cpp", SCRIPTS / "shaman_hooks.cpp",
                 SCRIPTS / "spell_shaman_elemental.cpp", SCRIPTS / "spell_shaman_totems.cpp"]
        self.assertClean(check_no_rank_sync({f.name: f.read_text() for f in files}))

    def test_header_has_no_removed_rank(self):
        text = (UNIT / "Generated" / "ShamanData.h").read_text()
        self.assertNotIn("SPELL_THUNDERSTORM_RANK2", text)
        self.assertIn("SPELL_CALL_OF_THUNDER_RANK3 = 202534", text)

    def test_call_of_the_elements_clears_client_cooldowns(self):
        self.assertClean(check_cote_clears_client_cooldown((SCRIPTS / "spell_shaman_totems.cpp").read_text()))

    def test_elemental_ascendance_storm_cloud(self):
        self.assertClean(check_ascendance_visuals(_shaman_data()["rows_by_id"]))


# ---- negative fixtures: every check must fire on a minimal bad input ---------------------------------------

def _cot(bp=99, aura=AURA_ADD_PCT_MODIFIER, mask=(0, THUNDERSTORM_D1, 0), text="Thunderstorm restores 100% more mana."):
    return {"Effect_1": 6, "EffectAura_1": AURA_ADD_FLAT_MODIFIER, "EffectMiscValue_1": 7,
            "Effect_2": 6, "EffectAura_2": aura, "EffectMiscValue_2": SPELLMOD_EFFECT2, "EffectBasePoints_2": bp,
            "EffectSpellClassMaskB_1": mask[0], "EffectSpellClassMaskB_2": mask[1], "EffectSpellClassMaskB_3": mask[2],
            "Description_Lang_enUS": text}


class ShamanPlaytestFix2NegativeTest(unittest.TestCase):
    def test_icon_check(self):
        rows = {202273: {"SpellIconID": 90270}, 202275: {"SpellIconID": 90270}}
        icons = {90270: STORM_ELEMENTAL_ICON_PATH}
        self.assertEqual(check_storm_icon(rows, icons), [])
        self.assertEqual(len(check_storm_icon({**rows, 202275: {"SpellIconID": 3080}}, icons)), 1)
        self.assertEqual(len(check_storm_icon(rows, {})), 1)
        self.assertEqual(len(check_storm_icon(rows, {90270: "Interface/icons/other.blp"})), 1)

    def test_capstone_check(self):
        plain = {"Effect_1": 6, "EffectAura_1": AURA_ADD_FLAT_MODIFIER, "EffectMiscValue_1": 7, "Description_Lang_enUS": ""}
        good = {16041: plain, 202533: plain, COT_CAPSTONE: _cot()}
        self.assertEqual(check_cot_capstone(good), [])
        self.assertEqual(len(check_cot_capstone({**good, COT_CAPSTONE: _cot(bp=49)})), 1)
        self.assertEqual(len(check_cot_capstone({**good, COT_CAPSTONE: _cot(aura=AURA_ADD_FLAT_MODIFIER)})), 1)
        self.assertEqual(len(check_cot_capstone({**good, COT_CAPSTONE: _cot(mask=(0, 0, 0))})), 1)       # unscoped
        self.assertEqual(len(check_cot_capstone({**good, COT_CAPSTONE: _cot(mask=(1, THUNDERSTORM_D1, 0))})), 1)
        self.assertEqual(len(check_cot_capstone({**good, COT_CAPSTONE: _cot(text="Thunderstorm can be cast while stunned.")})), 2)
        self.assertEqual(len(check_cot_capstone({**good, 202533: _cot()})), 1)
        self.assertEqual(len(check_cot_capstone({**good, 16041: dict(plain, Description_Lang_enUS="... while stunned.")})), 1)

    def test_energize_check(self):
        good = {THUNDERSTORM: {"Effect_2": ENERGIZE_PCT, "EffectMiscValue_2": 0, "EffectBasePoints_2": 9}}
        self.assertEqual(check_thunderstorm_energize(good), [])
        self.assertEqual(len(check_thunderstorm_energize({THUNDERSTORM: dict(good[THUNDERSTORM], Effect_2=6)})), 1)
        self.assertEqual(len(check_thunderstorm_energize({THUNDERSTORM: dict(good[THUNDERSTORM], EffectBasePoints_2=19)})), 1)

    def test_effect2_scope_check(self):
        leak = {"SpellClassSet": 11, **_cot()}
        self.assertEqual(check_effect2_mod_scope({}, {}), [])
        self.assertEqual(len(check_effect2_mod_scope({99999: leak}, {})), 1)
        self.assertEqual(check_effect2_mod_scope({COT_CAPSTONE: leak}, {}), [])
        glyph = {"SpellClassSet": 11, **_cot(aura=AURA_ADD_FLAT_MODIFIER, bp=1)}
        self.assertEqual(check_effect2_mod_scope({}, {62132: glyph}), [])             # a flat mod (the glyph) is fine

    def test_second_thunderstorm_check(self):
        self.assertEqual(check_second_thunderstorm_gone({}, [], []), [])
        self.assertEqual(len(check_second_thunderstorm_gone({REMOVED_THUNDERSTORM_RANK2: {}}, [], [])), 1)
        self.assertEqual(len(check_second_thunderstorm_gone({}, [{"id": REMOVED_SLA, "spell_id": 1}], [])), 1)
        self.assertEqual(len(check_second_thunderstorm_gone({}, [{"id": STUN_SUPERSEDE_SLA, "spell_id": 51490}], [])), 1)
        self.assertEqual(len(check_second_thunderstorm_gone({}, [], [{"spell_id": REMOVED_THUNDERSTORM_RANK2, "ScriptName": "x"}])), 1)

    def test_rank_sync_check(self):
        self.assertEqual(check_no_rank_sync({"a.cpp": "void Other();"}), [])
        self.assertEqual(len(check_no_rank_sync({"a.cpp": "Shaman::SyncThunderstormRank(self);"})), 1)
        self.assertEqual(len(check_no_rank_sync({"a.cpp": "ShamanData::SPELL_THUNDERSTORM_RANK2"})), 1)

    def test_cote_check(self):
        good = ("class spell_sha_elemental_lockout { if (GetSpell()->IsTriggered()) return; Shaman::ApplyElementalLockout(p, 1); }\n"
                "TRIGGERED_FULL_MASK summoned.push_back(1);\n"
                "RestoreSummonCooldownDisplay() { AddEventAtOffset; HasSpellCooldown; ResendSpellCooldown; RemoveSpellCooldown(spellId, true); }")
        self.assertEqual(check_cote_clears_client_cooldown(good), [])
        self.assertTrue(check_cote_clears_client_cooldown("class spell_sha_elemental_lockout {}"))
        self.assertTrue(check_cote_clears_client_cooldown(good.replace("ResendSpellCooldown;", "")))
        self.assertTrue(check_cote_clears_client_cooldown(good.replace("IsTriggered()", "x")))

    def test_ascendance_visual_check(self):
        rows = {ELEMENTAL_ASCENDANCE: {"SpellVisualID_1": STORM_CLOUD_VISUAL, "Attributes": 0}, 202387: {}, 202388: {}, 202389: {}}
        self.assertEqual(check_ascendance_visuals(rows), [])
        self.assertEqual(len(check_ascendance_visuals({**rows, ELEMENTAL_ASCENDANCE: {"SpellVisualID_1": 0}})), 1)
        self.assertEqual(len(check_ascendance_visuals({**rows, ELEMENTAL_ASCENDANCE: {"SpellVisualID_1": STORM_CLOUD_VISUAL, "Attributes": 0x40}})), 1)
        self.assertEqual(len(check_ascendance_visuals({**rows, 202388: {"SpellVisualID_1": 17}})), 1)
        self.assertEqual(len(check_ascendance_visuals({})), 1)


if __name__ == "__main__":
    unittest.main()
