"""
Rogue RG0a data gate (rogue-rework RG0a-HANDOFF WP-A/B table row A5, RG0a-WP-BRIEF).

Loads the real rogue DSL package (source/classes/rogue/) and asserts on the BUILT rows (stock base + DSL +
raw_overrides via `build.build_spell_row`, the way generate.py pairs them), so a stale raw twin that wins fails here
too. Every check is a pure function over built rows / package tables; the negative tests prove each can fail.

  1. Energy Haste 203700: hidden passive, aura 110 misc 3 stored -1, aura 226 @500 ms, no family bits, no SLA/trainer.
  2. The six poison auras 203701-203706: not passive, no 0x80, Ex 0x20, Ex3 0x100000, EquippedItemClass -1, infinite,
     GCD 133/1000, eff0 aura 42 -> the payload, exactly the right d2 bit, SpellLevel = trainer level.
  3. SkillLineAbility 30780-30785 (253 / class 8 / acquire 0) and spell_proc (0x114, phase 2, chance 100, attrs 0).
  4. spell_group 1287 = the three Non-lethal auras, rule 1; no Lethal aura in any group.
  5. Payloads: range >= 100 yd, d1 b19 on all six; 13218 eff0 aura 271 stored 19 mask A_1 0x100100, no aura 118;
     3409 stored -51 icon 163; 5760 stored -51; 26688 SpellLevel 40.
  6. Envenom 42 (eff1 empty, eff2 107 misc 18 mask C_3 0x2, C_1 0, mask_2 0x80008, TargetAuraState 16), Cloak 46, Tricks 56.
  7. Trainer 206 rows at the table levels; 2842 untrained from 9/10/206/207; the 29 poison item_template rows spellid_1 0.
  8. d0 b16 on no RG0a row but 2818; no FORBIDDEN_* bit; the consts exist with the table values.

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_rogue_rg0a.py -q
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
ROGUE_DIR = TOOL_ROOT / "source" / "classes" / "rogue"
sys.path.insert(0, str(TOOL_ROOT / "source" / "classes"))
_masks_spec = __import__("importlib.util").util.spec_from_file_location("_rogue_masks", ROGUE_DIR / "_masks.py")
m = __import__("importlib.util").util.module_from_spec(_masks_spec)
_masks_spec.loader.exec_module(m)

LETTERS = ("A", "B", "C")
ENERGY_HASTE = 203700
# aura id -> (payload id, d2 bit, trainer level, SkillLineAbility id)
AURAS = {
    203701: (8680, 0x2, 20, 30780),
    203702: (2818, 0x2, 30, 30781),
    203703: (13218, 0x2, 32, 30782),
    203704: (3409, 0x4, 20, 30783),
    203705: (5760, 0x8, 24, 30784),
    203706: (26688, 0x8, 40, 30785),
}
NONLETHAL = (203704, 203705, 203706)
LETHAL = (203701, 203702, 203703)
PAYLOADS = (8680, 2818, 13218, 3409, 5760, 26688)
ENVENOM, CLOAK, TRICKS = 32645, 31224, 57934
RG0A_IDS = (ENERGY_HASTE,) + tuple(AURAS) + PAYLOADS + (ENVENOM, CLOAK, TRICKS)
TRAINER = 206
TRAINER_LEVELS = {203701: 20, 203704: 20, 203705: 24, 203702: 30, 203703: 32, 203706: 40, ENVENOM: 42, CLOAK: 46,
                  TRICKS: 56}
POISON_SPELL = 2842
UNTRAIN_FROM = {9, 10, 206, 207}
POISON_ITEMS = (6947, 6949, 6950, 8926, 8927, 8928, 21927, 43230, 43231, 2892, 2893, 8984, 8985, 20844, 22053, 22054,
                43232, 43233, 10918, 10920, 10921, 10922, 22055, 43234, 43235, 3775, 5237, 21835, 43237)
CONSTS = {"POISON_LETHAL_CHANCE_PCT": 20, "POISON_CRIPPLING_CHANCE_PCT": 30, "POISON_MIND_NUMBING_CHANCE_PCT": 50,
          "POISON_ANESTHETIC_CHANCE_PCT": 50, "POISON_REFERENCE_WEAPON_SPEED_MS": 2600, "POISON_LETHAL_SLOTS": 1,
          "POISON_GLOW_ENCHANT": 323, "ENERGY_HASTE_MAX_PCT": 100}
ATTR0_PASSIVE, ATTR0_HIDDEN = 0x40, 0x80
ATTR1_ALLOW_WHILE_STEALTHED = 0x20
ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000
D0_B16 = 0x10000
POISON_GROUP = 0x80000
APPLY_AURA = 6


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def _i(row: dict, col: str) -> int:
    return int(row.get(col) or 0)


def effect_mask(row: dict, effect: int) -> tuple[int, int, int]:
    letter = LETTERS[effect - 1]
    return tuple(_u32(row.get(f"EffectSpellClassMask{letter}_{n}")) for n in (1, 2, 3))


def spell_mask(row: dict) -> tuple[int, int, int]:
    return tuple(_u32(row.get(f"SpellClassMask_{n}")) for n in (1, 2, 3))


def _hex(mask) -> str:
    return "(" + ", ".join(f"0x{w:X}" for w in mask) + ")"


# ---- checks (pure: take built rows / package tables, return problem strings) ------------------------------------

def check_energy_haste(rows: dict[int, dict], slas: list[dict], trainers: list[dict]) -> list[str]:
    row = rows.get(ENERGY_HASTE)
    if row is None:
        return [f"{ENERGY_HASTE}: not declared"]
    bad = []
    attrs = _u32(row.get("Attributes"))
    if not attrs & ATTR0_PASSIVE or not attrs & ATTR0_HIDDEN:
        bad.append(f"Attributes {attrs:#x} is not a hidden passive (0x40 | 0x80)")
    if (_i(row, "Effect_1"), _i(row, "EffectAura_1"), _i(row, "EffectMiscValue_1")) != (APPLY_AURA, 110, 3):
        bad.append("effect 1 is not APPLY_AURA 110 misc 3")
    if _i(row, "EffectBasePoints_1") != -1:
        bad.append(f"effect 1 stored base points {row.get('EffectBasePoints_1')!r}, expected -1")
    if (_i(row, "Effect_2"), _i(row, "EffectAura_2")) != (APPLY_AURA, 226):
        bad.append("effect 2 is not APPLY_AURA 226")
    if _i(row, "EffectAuraPeriod_2") != 500:
        bad.append(f"effect 2 period {row.get('EffectAuraPeriod_2')!r}, expected 500")
    for label, mask in [("SpellClassMask", spell_mask(row))] + [(f"effect {i}", effect_mask(row, i)) for i in (1, 2, 3)]:
        if any(mask):
            bad.append(f"{label} {_hex(mask)} carries family bits")
    if any(int(s["spell_id"]) == ENERGY_HASTE for s in slas):
        bad.append("has a SkillLineAbility row (hidden passive is granted by the PlayerScript)")
    if any(int(t["SpellId"]) == ENERGY_HASTE for t in trainers):
        bad.append("has a trainer row")
    return [f"{ENERGY_HASTE}: {b}" for b in bad]


def check_poison_auras(rows: dict[int, dict], trainer_levels: dict[int, int], infinite_index: int) -> list[str]:
    bad = []
    for aid, (payload, d2, _level, _sla) in AURAS.items():
        row = rows.get(aid)
        if row is None:
            bad.append(f"{aid}: not declared")
            continue
        attrs = _u32(row.get("Attributes"))
        if attrs & ATTR0_PASSIVE:
            bad.append(f"{aid}: Attributes {attrs:#x} is passive")
        if attrs & ATTR0_HIDDEN:
            bad.append(f"{aid}: Attributes {attrs:#x} has 0x80 (hidden)")
        if not _u32(row.get("AttributesEx")) & ATTR1_ALLOW_WHILE_STEALTHED:
            bad.append(f"{aid}: AttributesEx lacks 0x20")
        if not _u32(row.get("AttributesEx3")) & ATTR3_ALLOW_AURA_WHILE_DEAD:
            bad.append(f"{aid}: AttributesEx3 lacks 0x100000")
        if _u32(row.get("EquippedItemClass")) != 0xFFFFFFFF:
            bad.append(f"{aid}: EquippedItemClass {row.get('EquippedItemClass')!r}, expected -1")
        if _i(row, "DurationIndex") != infinite_index:
            bad.append(f"{aid}: DurationIndex {row.get('DurationIndex')!r} is not the infinite row {infinite_index}")
        if (_i(row, "StartRecoveryCategory"), _i(row, "StartRecoveryTime")) != (133, 1000):
            bad.append(f"{aid}: GCD {row.get('StartRecoveryCategory')}/{row.get('StartRecoveryTime')}, expected 133/1000")
        if (_i(row, "Effect_1"), _i(row, "EffectAura_1")) != (APPLY_AURA, 42):
            bad.append(f"{aid}: effect 1 is not APPLY_AURA 42")
        if _i(row, "EffectTriggerSpell_1") != payload:
            bad.append(f"{aid}: effect 1 triggers {row.get('EffectTriggerSpell_1')!r}, expected {payload}")
        if spell_mask(row) != (0, 0, d2):
            bad.append(f"{aid}: SpellClassMask {_hex(spell_mask(row))}, expected (0x0, 0x0, {d2:#x})")
        for i in (1, 2, 3):
            if any(effect_mask(row, i)):
                bad.append(f"{aid}: effect {i} mask {_hex(effect_mask(row, i))} should be empty")
        if aid not in trainer_levels:
            bad.append(f"{aid}: no trainer row")
        elif _i(row, "SpellLevel") != trainer_levels[aid]:
            bad.append(f"{aid}: SpellLevel {row.get('SpellLevel')!r} != trainer level {trainer_levels[aid]}")
    return bad


def check_slas(slas: list[dict]) -> list[str]:
    by_spell = {int(s["spell_id"]): s for s in slas}
    bad = []
    for aid, (_p, _d2, _l, sla_id) in AURAS.items():
        s = by_spell.get(aid)
        if s is None:
            bad.append(f"{aid}: no SkillLineAbility row")
            continue
        if int(s["id"]) != sla_id:
            bad.append(f"{aid}: SkillLineAbility id {s['id']}, expected {sla_id}")
        if (int(s["skill_line"]), int(s.get("class_mask") or 0), int(s.get("acquire_method") or 0)) != (253, 8, 0):
            bad.append(f"{aid}: SLA skill/class/acquire = {s['skill_line']}/{s.get('class_mask')}/"
                       f"{s.get('acquire_method')}, expected 253/8/0")
    return bad


def check_spell_procs(procs: list[dict]) -> list[str]:
    by_spell = {int(p["SpellId"]): p for p in procs}
    bad = []
    for aid in AURAS:
        p = by_spell.get(aid)
        if p is None:
            bad.append(f"{aid}: no spell_proc row")
            continue
        if int(p["ProcFlags"]) != 0x114:
            bad.append(f"{aid}: ProcFlags {int(p['ProcFlags']):#x}, expected 0x114")
        if int(p["SpellPhaseMask"]) != 2:
            bad.append(f"{aid}: SpellPhaseMask {p['SpellPhaseMask']}, expected 2")
        if float(p["Chance"]) != 100.0:
            bad.append(f"{aid}: Chance {p['Chance']}, expected 100")
        if int(p["AttributesMask"]) != 0:
            bad.append(f"{aid}: AttributesMask {p['AttributesMask']}, expected 0")
    return bad


def check_groups(groups: list[dict], rules: list[dict]) -> list[str]:
    bad = []
    members = sorted(int(g["spell_id"]) for g in groups if int(g["id"]) == 1287)
    if members != sorted(NONLETHAL):
        bad.append(f"group 1287 holds {members}, expected {sorted(NONLETHAL)}")
    rule = [r for r in rules if int(r["group_id"]) == 1287]
    if len(rule) != 1 or int(rule[0]["stack_rule"]) != 1:
        bad.append(f"group 1287 rules {[(r['group_id'], r['stack_rule']) for r in rule]}, expected one with stack_rule 1")
    for g in groups:
        if int(g["spell_id"]) in LETHAL:
            bad.append(f"Lethal aura {g['spell_id']} is in group {g['id']}")
    return bad


def check_payloads(rows: dict[int, dict], range_index_100: int) -> list[str]:
    bad = []
    for pid in PAYLOADS:
        row = rows.get(pid)
        if row is None:
            bad.append(f"{pid}: not declared")
            continue
        if _i(row, "RangeIndex") != range_index_100:
            bad.append(f"{pid}: RangeIndex {row.get('RangeIndex')!r}, expected the 100 yd row {range_index_100}")
        if not spell_mask(row)[1] & POISON_GROUP:
            bad.append(f"{pid}: SpellClassMask_2 {_hex(spell_mask(row))} lacks d1 b19 (0x80000)")
    return bad


def check_payload_effects(rows: dict[int, dict]) -> list[str]:
    bad = []
    w, c, mn, an = rows.get(13218), rows.get(3409), rows.get(5760), rows.get(26688)
    if w is not None:
        if _i(w, "EffectAura_1") != 271 or _i(w, "EffectBasePoints_1") != 19:
            bad.append(f"13218: effect 1 aura/base {w.get('EffectAura_1')}/{w.get('EffectBasePoints_1')}, expected 271/19")
        if effect_mask(w, 1) != (0x100100, 0, 0):
            bad.append(f"13218: EffectSpellClassMaskA {_hex(effect_mask(w, 1))}, expected (0x100100, 0x0, 0x0)")
        for i in (1, 2, 3):
            if _i(w, f"EffectAura_{i}") == 118:
                bad.append(f"13218: effect {i} still carries aura 118")
    if c is not None:
        if _i(c, "EffectBasePoints_1") != -51:
            bad.append(f"3409: effect 1 stored {c.get('EffectBasePoints_1')!r}, expected -51")
        if _i(c, "SpellIconID") != 163:
            bad.append(f"3409: SpellIconID {c.get('SpellIconID')!r}, expected 163")
    if mn is not None and _i(mn, "EffectBasePoints_1") != -51:
        bad.append(f"5760: effect 1 stored {mn.get('EffectBasePoints_1')!r}, expected -51")
    if an is not None and _i(an, "SpellLevel") != 40:
        bad.append(f"26688: SpellLevel {an.get('SpellLevel')!r}, expected 40")
    return bad


def check_envenom_and_levels(rows: dict[int, dict]) -> list[str]:
    bad = []
    e = rows.get(ENVENOM)
    if e is not None:
        if _i(e, "SpellLevel") != 42:
            bad.append(f"{ENVENOM}: SpellLevel {e.get('SpellLevel')!r}, expected 42")
        if _i(e, "Effect_2") != 0 or _i(e, "EffectAura_2") != 0:
            bad.append(f"{ENVENOM}: effect 2 not empty (Effect {e.get('Effect_2')}, aura {e.get('EffectAura_2')})")
        if _i(e, "EffectAura_3") != 107 or _i(e, "EffectMiscValue_3") != 18:
            bad.append(f"{ENVENOM}: effect 3 aura/misc {e.get('EffectAura_3')}/{e.get('EffectMiscValue_3')}, expected 107/18")
        mc = effect_mask(e, 3)
        if mc[2] != 0x2 or mc[0] != 0:
            bad.append(f"{ENVENOM}: effect 3 mask {_hex(mc)}, expected d2 0x2 and d0 0x0")
        if spell_mask(e)[1] != 0x80008:
            bad.append(f"{ENVENOM}: SpellClassMask_2 0x{spell_mask(e)[1]:X}, expected 0x80008")
        if _i(e, "TargetAuraState") != 16:
            bad.append(f"{ENVENOM}: TargetAuraState {e.get('TargetAuraState')!r}, expected 16")
    for sid, level in ((CLOAK, 46), (TRICKS, 56)):
        r = rows.get(sid)
        if r is not None and (_i(r, "SpellLevel"), _i(r, "BaseLevel")) != (level, level):
            bad.append(f"{sid}: SpellLevel/BaseLevel {r.get('SpellLevel')}/{r.get('BaseLevel')}, expected {level}")
    return bad


def check_trainers(trainers: list[dict], removals: list[dict]) -> list[str]:
    bad = []
    mine = {int(t["SpellId"]): t for t in trainers if int(t["TrainerId"]) == TRAINER and int(t["SpellId"]) in TRAINER_LEVELS}
    for sid, level in TRAINER_LEVELS.items():
        t = mine.get(sid)
        if t is None:
            bad.append(f"{sid}: no trainer {TRAINER} row")
        elif int(t["ReqLevel"]) != level:
            bad.append(f"{sid}: trainer {TRAINER} ReqLevel {t['ReqLevel']}, expected {level}")
    for t in trainers:
        if int(t["SpellId"]) in AURAS and int(t["TrainerId"]) != TRAINER:
            bad.append(f"{t['SpellId']}: taught by trainer {t['TrainerId']}, only {TRAINER} allowed")
    removed = {int(r["TrainerId"]) for r in removals if int(r["SpellId"]) == POISON_SPELL}
    if removed != UNTRAIN_FROM:
        bad.append(f"{POISON_SPELL} untrained from {sorted(removed)}, expected {sorted(UNTRAIN_FROM)}")
    if any(int(t["SpellId"]) == POISON_SPELL for t in trainers):
        bad.append(f"{POISON_SPELL} still declared on a trainer")
    return bad


def check_items(items: list[dict]) -> list[str]:
    by_entry = {int(i["entry"]): i for i in items}
    bad = []
    for entry in POISON_ITEMS:
        i = by_entry.get(entry)
        if i is None:
            bad.append(f"item {entry}: no item_template declaration")
        elif int(i.get("spellid_1") or 0) != 0 or "spellid_1" not in i.get("_update_columns", ()):
            bad.append(f"item {entry}: spellid_1 {i.get('spellid_1')!r} (updated: {'spellid_1' in i.get('_update_columns', ())}), expected 0")
    return bad


def check_deadly_bit(rows: dict[int, dict]) -> list[str]:
    return [f"{sid}: SpellClassMask_1 {spell_mask(r)[0]:#x} carries d0 b16 (only 2818 may)"
            for sid, r in rows.items() if sid in RG0A_IDS and sid != 2818 and spell_mask(r)[0] & D0_B16]


def check_forbidden(rows: dict[int, dict]) -> list[str]:
    bad = []
    for sid, r in rows.items():
        if sid not in RG0A_IDS:
            continue
        d0, d1, _d2 = spell_mask(r)
        hit = (d0 & m.FORBIDDEN_D0, 0 if sid == ENVENOM else d1 & m.FORBIDDEN_D1, 0)
        if any(hit):
            bad.append(f"{sid}: SpellClassMask {_hex(spell_mask(r))} holds forbidden bits {_hex(hit)}")
        if d0 & m.RUPTURE:
            bad.append(f"{sid}: SpellClassMask_1 carries d0 b20 (Rupture only)")
        for i in (1, 2, 3):
            em = effect_mask(r, i)
            if em[0] & m.FORBIDDEN_D0:
                bad.append(f"{sid}: effect {i} mask {_hex(em)} holds forbidden d0 bits")
    return bad


def check_consts(consts: list[dict]) -> list[str]:
    have = {c["name"]: c["value"] for c in consts}
    return [f"const {n}: {have.get(n)!r}, expected {v}" for n, v in CONSTS.items() if have.get(n) != v]


# ---- real data ----------------------------------------------------------------------------------------------

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
        _CACHE.update(
            package=package, rows_by_id={int(r["ID"]): r for r in rows},
            infinite=reuse.duration_index(0), range100=reuse.range_index(100.0),
            trainer_levels={int(t["SpellId"]): int(t["ReqLevel"]) for t in package.trainer_spells
                            if int(t["TrainerId"]) == TRAINER},
        )
    return _CACHE


class RogueRG0aDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_energy_haste(self):
        d = _data()
        self.assertClean(check_energy_haste(d["rows_by_id"], d["package"].skill_line_abilities, d["package"].trainer_spells))

    def test_poison_auras(self):
        d = _data()
        self.assertClean(check_poison_auras(d["rows_by_id"], d["trainer_levels"], d["infinite"]))

    def test_skill_line_abilities(self):
        self.assertClean(check_slas(_data()["package"].skill_line_abilities))

    def test_spell_procs(self):
        self.assertClean(check_spell_procs(_data()["package"].spell_procs))

    def test_groups(self):
        p = _data()["package"]
        self.assertClean(check_groups(p.spell_groups, p.spell_group_rules))

    def test_payloads(self):
        d = _data()
        self.assertClean(check_payloads(d["rows_by_id"], d["range100"]))

    def test_payload_effects(self):
        self.assertClean(check_payload_effects(_data()["rows_by_id"]))

    def test_envenom_cloak_tricks(self):
        self.assertClean(check_envenom_and_levels(_data()["rows_by_id"]))

    def test_trainers(self):
        p = _data()["package"]
        self.assertClean(check_trainers(p.trainer_spells, p.trainer_removals))

    def test_poison_items(self):
        self.assertClean(check_items(_data()["package"].item_templates))

    def test_deadly_bit_only_2818(self):
        self.assertClean(check_deadly_bit(_data()["rows_by_id"]))

    def test_no_forbidden_bits(self):
        self.assertClean(check_forbidden(_data()["rows_by_id"]))

    def test_consts(self):
        self.assertClean(check_consts(_data()["package"].consts))


# ---- negative fixtures: every check must fire on a minimal bad input ---------------------------------------

def _good_aura(aid: int) -> dict:
    payload, d2, _l, _s = AURAS[aid]
    return {"ID": aid, "Attributes": 0, "AttributesEx": 0x20, "AttributesEx3": 0x100000, "EquippedItemClass": -1,
            "DurationIndex": 21, "StartRecoveryCategory": 133, "StartRecoveryTime": 1000, "Effect_1": 6,
            "EffectAura_1": 42, "EffectTriggerSpell_1": payload, "SpellClassMask_3": d2,
            "SpellLevel": AURAS[aid][2]}


def _good_haste() -> dict:
    return {"ID": ENERGY_HASTE, "Attributes": 0xC0, "Effect_1": 6, "EffectAura_1": 110, "EffectMiscValue_1": 3,
            "EffectBasePoints_1": -1, "Effect_2": 6, "EffectAura_2": 226, "EffectAuraPeriod_2": 500}


def _good_envenom() -> dict:
    return {"ID": ENVENOM, "SpellLevel": 42, "Effect_2": 0, "EffectAura_2": 0, "EffectAura_3": 107,
            "EffectMiscValue_3": 18, "EffectSpellClassMaskC_3": 0x2, "SpellClassMask_2": 0x80008,
            "TargetAuraState": 16}


class RogueRG0aNegativeTest(unittest.TestCase):
    def test_energy_haste(self):
        rows = {ENERGY_HASTE: _good_haste()}
        self.assertEqual(check_energy_haste(rows, [], []), [])
        for col, val in (("Attributes", 0x40), ("Attributes", 0x80), ("EffectAura_1", 109), ("EffectMiscValue_1", 0),
                         ("EffectBasePoints_1", 0), ("EffectAura_2", 4), ("EffectAuraPeriod_2", 1000),
                         ("SpellClassMask_1", 1), ("EffectSpellClassMaskB_2", 1)):
            self.assertEqual(len(check_energy_haste({ENERGY_HASTE: {**_good_haste(), col: val}}, [], [])), 1, col)
        self.assertEqual(len(check_energy_haste(rows, [{"spell_id": ENERGY_HASTE}], [])), 1)
        self.assertEqual(len(check_energy_haste(rows, [], [{"SpellId": ENERGY_HASTE}])), 1)
        self.assertEqual(len(check_energy_haste({}, [], [])), 1)

    def test_poison_auras(self):
        levels = {a: AURAS[a][2] for a in AURAS}
        good = {a: _good_aura(a) for a in AURAS}
        self.assertEqual(check_poison_auras(good, levels, 21), [])
        for col, val in (("Attributes", 0x40), ("Attributes", 0x80), ("AttributesEx", 0), ("AttributesEx3", 0),
                         ("EquippedItemClass", 2), ("DurationIndex", 5), ("StartRecoveryTime", 1500),
                         ("StartRecoveryCategory", 0), ("EffectAura_1", 4), ("EffectTriggerSpell_1", 1),
                         ("SpellClassMask_3", 0x10), ("SpellClassMask_2", 1), ("EffectSpellClassMaskA_1", 1),
                         ("SpellLevel", 1)):
            self.assertEqual(len(check_poison_auras({**good, 203701: {**good[203701], col: val}}, levels, 21)), 1, col)
        # extra bit alongside the right one
        extra = {**good, 203704: {**good[203704], "SpellClassMask_3": 0x6}}
        self.assertEqual(len(check_poison_auras(extra, levels, 21)), 1)
        self.assertEqual(len(check_poison_auras(good, {k: v for k, v in levels.items() if k != 203706}, 21)), 1)

    def test_slas(self):
        good = [{"id": s, "spell_id": a, "skill_line": 253, "class_mask": 8, "acquire_method": 0}
                for a, (_p, _d, _l, s) in AURAS.items()]
        self.assertEqual(check_slas(good), [])
        self.assertEqual(len(check_slas(good[1:])), 1)
        for col, val in (("skill_line", 40), ("class_mask", 0), ("acquire_method", 1), ("id", 30790)):
            self.assertEqual(len(check_slas([{**good[0], col: val}] + good[1:])), 1, col)

    def test_spell_procs(self):
        good = [{"SpellId": a, "ProcFlags": 0x114, "SpellPhaseMask": 2, "Chance": 100.0, "AttributesMask": 0}
                for a in AURAS]
        self.assertEqual(check_spell_procs(good), [])
        self.assertEqual(len(check_spell_procs(good[1:])), 1)
        for col, val in (("ProcFlags", 0x154), ("SpellPhaseMask", 1), ("Chance", 20.0), ("AttributesMask", 1)):
            self.assertEqual(len(check_spell_procs([{**good[0], col: val}] + good[1:])), 1, col)

    def test_groups(self):
        groups = [{"id": 1287, "spell_id": a} for a in NONLETHAL]
        rules = [{"group_id": 1287, "stack_rule": 1}]
        self.assertEqual(check_groups(groups, rules), [])
        self.assertEqual(len(check_groups(groups[:2], rules)), 1)
        self.assertEqual(len(check_groups(groups + [{"id": 1287, "spell_id": 203701}], rules)), 2)  # member + lethal
        self.assertEqual(len(check_groups(groups, [{"group_id": 1287, "stack_rule": 3}])), 1)
        self.assertEqual(len(check_groups(groups, [])), 1)
        self.assertEqual(len(check_groups(groups + [{"id": 1286, "spell_id": 203702}], rules)), 1)

    def test_payloads(self):
        good = {p: {"ID": p, "RangeIndex": 7, "SpellClassMask_2": POISON_GROUP} for p in PAYLOADS}
        self.assertEqual(check_payloads(good, 7), [])
        self.assertEqual(len(check_payloads({**good, 13218: {**good[13218], "RangeIndex": 2}}, 7)), 1)
        self.assertEqual(len(check_payloads({**good, 8680: {"ID": 8680, "RangeIndex": 7, "SpellClassMask_2": 0}}, 7)), 1)
        self.assertEqual(len(check_payloads({k: v for k, v in good.items() if k != 5760}, 7)), 1)

    def test_payload_effects(self):
        wound = {"ID": 13218, "EffectAura_1": 271, "EffectBasePoints_1": 19, "EffectSpellClassMaskA_1": 0x100100}
        c = {"ID": 3409, "EffectBasePoints_1": -51, "SpellIconID": 163}
        mn = {"ID": 5760, "EffectBasePoints_1": -51}
        an = {"ID": 26688, "SpellLevel": 40}
        good = {13218: wound, 3409: c, 5760: mn, 26688: an}
        self.assertEqual(check_payload_effects(good), [])
        for sid, col, val in ((13218, "EffectAura_1", 118), (13218, "EffectBasePoints_1", 18),
                              (13218, "EffectSpellClassMaskA_1", 0x100000), (13218, "EffectAura_3", 118),
                              (3409, "EffectBasePoints_1", -71), (3409, "SpellIconID", 1), (5760, "EffectBasePoints_1", -31),
                              (26688, "SpellLevel", 68)):
            self.assertGreaterEqual(len(check_payload_effects({**good, sid: {**good[sid], col: val}})), 1, (sid, col))

    def test_envenom_and_levels(self):
        rows = {ENVENOM: _good_envenom(), CLOAK: {"ID": CLOAK, "SpellLevel": 46, "BaseLevel": 46},
                TRICKS: {"ID": TRICKS, "SpellLevel": 56, "BaseLevel": 56}}
        self.assertEqual(check_envenom_and_levels(rows), [])
        for col, val in (("SpellLevel", 62), ("Effect_2", 6), ("EffectAura_2", 108), ("EffectAura_3", 108),
                         ("EffectMiscValue_3", 26), ("EffectSpellClassMaskC_3", 0x4), ("EffectSpellClassMaskC_1", 0x10000),
                         ("SpellClassMask_2", 0x8), ("TargetAuraState", 0)):
            self.assertGreaterEqual(len(check_envenom_and_levels({**rows, ENVENOM: {**rows[ENVENOM], col: val}})), 1, col)
        self.assertEqual(len(check_envenom_and_levels({**rows, CLOAK: {"ID": CLOAK, "SpellLevel": 66, "BaseLevel": 46}})), 1)
        self.assertEqual(len(check_envenom_and_levels({**rows, TRICKS: {"ID": TRICKS, "SpellLevel": 56, "BaseLevel": 75}})), 1)

    def test_trainers(self):
        good = [{"TrainerId": TRAINER, "SpellId": s, "ReqLevel": lv} for s, lv in TRAINER_LEVELS.items()]
        rem = [{"TrainerId": t, "SpellId": POISON_SPELL} for t in UNTRAIN_FROM]
        self.assertEqual(check_trainers(good, rem), [])
        self.assertEqual(len(check_trainers(good[1:], rem)), 1)
        self.assertEqual(len(check_trainers([{**good[0], "ReqLevel": 21}] + good[1:], rem)), 1)
        self.assertEqual(len(check_trainers(good + [{"TrainerId": 9, "SpellId": 203701, "ReqLevel": 20}], rem)), 1)
        self.assertEqual(len(check_trainers(good, rem[1:])), 1)
        self.assertEqual(len(check_trainers(good, rem + [{"TrainerId": 5, "SpellId": POISON_SPELL}])), 1)
        self.assertEqual(len(check_trainers(good + [{"TrainerId": 206, "SpellId": POISON_SPELL, "ReqLevel": 20}], rem)), 1)

    def test_items(self):
        good = [{"entry": e, "spellid_1": 0, "_update_columns": ("spellid_1", "spellcharges_1")} for e in POISON_ITEMS]
        self.assertEqual(check_items(good), [])
        self.assertEqual(len(check_items(good[1:])), 1)
        self.assertEqual(len(check_items([{**good[0], "spellid_1": 8679}] + good[1:])), 1)
        self.assertEqual(len(check_items([{**good[0], "_update_columns": ("description",)}] + good[1:])), 1)
        self.assertEqual(len(POISON_ITEMS), 29)

    def test_deadly_bit(self):
        ok = {2818: {"ID": 2818, "SpellClassMask_1": D0_B16}, 8680: {"ID": 8680, "SpellClassMask_1": 0x2000}}
        self.assertEqual(check_deadly_bit(ok), [])
        self.assertEqual(len(check_deadly_bit({**ok, 8680: {"ID": 8680, "SpellClassMask_1": 0x12000}})), 1)
        self.assertEqual(check_deadly_bit({999: {"ID": 999, "SpellClassMask_1": D0_B16}}), [])  # not an RG0a row

    def test_forbidden(self):
        ok = {ENVENOM: {"ID": ENVENOM, "SpellClassMask_1": 0x800000, "SpellClassMask_2": 0x80008}}
        self.assertEqual(check_forbidden(ok), [])
        for col, bit in (("SpellClassMask_1", 0x800), ("SpellClassMask_1", 0x400000), ("SpellClassMask_1", 0x2000000),
                         ("SpellClassMask_1", 0x100000), ("SpellClassMask_2", 0x2), ("SpellClassMask_2", 0x4),
                         ("EffectSpellClassMaskA_1", 0x800)):
            self.assertEqual(len(check_forbidden({203701: {"ID": 203701, col: bit}})), 1, (col, bit))
        self.assertEqual(len(check_forbidden({3409: {"ID": 3409, "SpellClassMask_2": 0x8}})), 1)  # d1 b3 only Envenom
        self.assertEqual(check_forbidden({999: {"ID": 999, "SpellClassMask_1": 0x800}}), [])  # not an RG0a row

    def test_consts(self):
        good = [{"name": n, "value": v} for n, v in CONSTS.items()]
        self.assertEqual(check_consts(good), [])
        self.assertEqual(len(check_consts(good[1:])), 1)
        self.assertEqual(len(check_consts([{**good[0], "value": 25}] + good[1:])), 1)


if __name__ == "__main__":
    unittest.main()
