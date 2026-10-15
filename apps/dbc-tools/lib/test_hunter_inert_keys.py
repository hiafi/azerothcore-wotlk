"""
Hunter inert-key pytest (PET.md 2.1 P4; H0-P1-HANDOFF WP-A4 (1); `test_paladin_ret_inert_keys.py` shape).

`header_gen` hands the short constant (`SPELL_RAKE`) to the lowest id with that Name, and suppresses its warning for
same-Name pairs, so a commanded spell named `rake_201722` would silently lose `SPELL_RAKE` to the retired stock
special `rake_59881` and C++ casting it would cast the retired spell. Today's header already has `SPELL_RAKE = 59881`,
`SPELL_SWIPE = 50256` and `SPELL_SAVAGE_REND = 50498`, and keeps them (their rows stay declared, PET 4.6), so the
guard is on the code and the reserved stems, not on the header:

  (a) no `SPELL_[A-Z0-9_]+` token in the hunter fork C++ resolves, through `Generated/HunterData.h` (the checked-in
      header and the names the package would regenerate), to a spell id a `retire_pet_spell` call retires;
  (b) every declared spell in 201720-201749 has a `_command_` stem, or is `venomous_cloud_splash_201736`, and its
      header name has no `_<id>` suffix (vacuous until S1 declares them; S1 re-runs it).

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_hunter_inert_keys.py -q
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import header_gen  # noqa: E402
from lib.test_hunter_pet_data import package_data  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
HEADER_PATH = REPO_ROOT / "src/server/game/Entities/Unit/Generated/HunterData.h"
UNIT_DIR = REPO_ROOT / "src/server/game/Entities/Unit"
SPELLS_DIR = REPO_ROOT / "src/server/scripts/Spells"
PET_DIR = REPO_ROOT / "src/server/scripts/Pet"

SPELL_TOKEN = re.compile(r"\bSPELL_[A-Z0-9_]+\b")
HEADER_LINE = re.compile(r"constexpr\s+uint32\s+(SPELL_[A-Z0-9_]+)\s*=\s*(\d+)\s*;")
TRAILING_ID = re.compile(r"_\d+$")
COMMAND_RANGE = range(201720, 201750)
SPLASH_STEM = "venomous_cloud_splash_201736"


def hunter_cpp_files() -> list[Path]:
    """The hunter fork C++ (PET.md 2.1 P4). The stock spell_hunter.cpp is upstream-owned and not scanned."""
    files = [UNIT_DIR / "HunterMechanics.h", UNIT_DIR / "HunterMechanics.cpp", SPELLS_DIR / "hunter_hooks.cpp",
             PET_DIR / "pet_hunter_rework.cpp", *sorted(SPELLS_DIR.glob("spell_hunter_*.cpp"))]
    return [f for f in files if f.is_file()]


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def parse_header_names(text: str) -> dict[str, int]:
    return {m.group(1): int(m.group(2)) for m in HEADER_LINE.finditer(text)}


def regenerated_header_names(package) -> dict[str, int]:
    """The names `header_gen` would give the package's spells (the header on disk may be stale mid-stage)."""
    ids = sorted(e["id"] for e in package.spells)
    names = {e["id"]: e.get("name") for e in package.spells}
    lines = header_gen._render_id_section(ids, package.spell_var_names, "SPELL_", names, None)
    return parse_header_names("\n".join(lines))


# Bite 17253, Claw 16827 and Smack 49966 are retired only from the Cunning lines (family-scoped retire_pet_spell) and stay
# the real per-type basics. The exemption is derived from the data: a spell is exempt only when EVERY retirement of it
# names families, so turning one into a global retirement makes the guard fire on the kit table again (RD-3).
EXPECTED_SCOPED_BASICS = frozenset({17253, 16827, 49966})


def scoped_only_retirements(retirements: list[dict]) -> set[int]:
    """Spell ids whose every `retire_pet_spell` entry is family-scoped (`families` is not None)."""
    ids = {int(r["spell_id"]) for r in retirements}
    return {i for i in ids if all(r["families"] is not None for r in retirements if int(r["spell_id"]) == i)}


# ---- checks (pure) ---------------------------------------------------------------------------------------------

def check_no_retired_spell_in_code(sources: dict[str, str], names: dict[str, int], retired: set[int]) -> list[str]:
    """(a) a SPELL_ token in `sources` (file name -> text) that resolves through `names` to a retired spell id."""
    bad = []
    for name, text in sources.items():
        for line_no, line in enumerate(strip_comments(text).splitlines(), 1):
            for token in dict.fromkeys(SPELL_TOKEN.findall(line)):
                if names.get(token) in retired:
                    bad.append(f"{name}:{line_no}: {token} resolves to {names[token]}, a spell retire_pet_spell retires")
    return bad


def check_command_stems(var_names: dict[int, str], header_names_by_id: dict[int, str],
                        id_range=COMMAND_RANGE) -> list[str]:
    """(b) every declared id in 201720-201749: a `_command_` stem (or the splash stem) and a header name that is
    not the `_<id>`-suffixed fallback."""
    bad = []
    for spell_id in id_range:
        stem = var_names.get(spell_id)
        if stem is None:
            continue
        if "_command_" not in stem and stem != SPLASH_STEM:
            bad.append(f"{spell_id}: stem {stem!r} has no '_command_' (a short stem a retired special owns would "
                       f"cast the retired spell)")
        header = header_names_by_id.get(spell_id)
        if header is not None and TRAILING_ID.search(header):
            bad.append(f"{spell_id}: header name {header} has an _<id> suffix, so it lost its short name to a lower id")
    return bad


# ---- real data -------------------------------------------------------------------------------------------------

class HunterInertKeyTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_hunter_cpp_files_were_found(self):
        names = {f.name for f in hunter_cpp_files()}
        for expected in ("HunterMechanics.h", "HunterMechanics.cpp", "hunter_hooks.cpp"):
            self.assertIn(expected, names)

    def test_no_code_uses_a_name_that_resolves_to_a_retired_spell(self):
        package = package_data()["package"]
        retired = {int(r["spell_id"]) for r in package.pet_spell_retirements}
        self.assertTrue(retired, "no retire_pet_spell declared yet (hunter_pet.py WP-A1 item 5)")
        # Bite, Claw and Smack are retired only from the Cunning lines (scoped retire_pet_spell); they remain the
        # real per-type basics, so the pet kit table may name them.
        scoped = scoped_only_retirements(package.pet_spell_retirements)
        self.assertLessEqual(EXPECTED_SCOPED_BASICS, scoped,
                             "Bite/Claw/Smack must stay family-scoped retirements (a global one strands the kit basics)")
        retired -= scoped
        names = {**parse_header_names(HEADER_PATH.read_text()), **regenerated_header_names(package)}
        sources = {str(f.relative_to(REPO_ROOT)): f.read_text() for f in hunter_cpp_files()}
        self.assertClean(check_no_retired_spell_in_code(sources, names, retired))

    def test_commanded_spells_use_command_stems_and_keep_their_header_names(self):
        package = package_data()["package"]
        header_by_id = {i: n for n, i in regenerated_header_names(package).items()}
        self.assertClean(check_command_stems(package.spell_var_names, header_by_id))


# ---- the 34026 guard (PET.md 6.1; `test_paladin_ret_inert_keys.py` shape) ------------------------------------------
# Two stock core lines key on an Aura whose id is 34026 (SpellAuraEffects.cpp:5204 HandleAuraDummy, SpellAuras.cpp:1863
# HandleAuraSpecificMods). The rewritten Kill Command is a plain instant cast, so no Aura object with that id can ever
# exist; the guard fails if the built row gains an aura-creating effect or a duration. S1 extends it.

KILL_COMMAND = 34026
AURA_CREATING_EFFECTS = (6, 27, 35, 65, 119, 128, 129, 143, 174)


def check_34026_inert(row: dict | None, entry: dict | None = None) -> list[str]:
    """No effect of an aura-creating type on any of the three effects, and no duration.

    Asserted on the BUILT row: DurationIndex must be 0 (the raw `'DurationIndex': 0` key builds 0; without it
    `reuse.duration_index(falsy)` mints the permanent -1 row, reuse.py:127-145, so deleting the "redundant" key
    must fail here). With the declaration `entry`, a truthy `duration_ms` is flagged too."""
    if row is None:
        return [f"{KILL_COMMAND}: not declared in the hunter package"]
    bad = []
    for index in (1, 2, 3):
        effect = int(row.get(f"Effect_{index}") or 0)
        if effect in AURA_CREATING_EFFECTS:
            bad.append(f"{KILL_COMMAND}: effect {index} has aura-creating type {effect}; an Aura with id {KILL_COMMAND} "
                       f"would reach the stock 34026 core cases (PET 6.1)")
    if int(row.get("DurationIndex") or 0) != 0:
        bad.append(f"{KILL_COMMAND}: built DurationIndex {row.get('DurationIndex')}, expected 0")
    if entry is not None and entry.get("duration_ms"):
        bad.append(f"{KILL_COMMAND}: duration_ms {entry['duration_ms']}, expected none")
    return bad


class Hunter34026GuardSlotTest(unittest.TestCase):
    def test_built_kill_command_row_is_inert(self):
        data = package_data()
        entry = next((e for e in data["package"].spells if e["id"] == KILL_COMMAND), None)
        self.assertIsNotNone(entry, "34026 is not declared")
        problems = check_34026_inert(data["rows_by_id"].get(KILL_COMMAND), entry)
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_guard_fires_on_an_apply_aura_effect(self):
        for effect_type in AURA_CREATING_EFFECTS:
            row = {"ID": KILL_COMMAND, "Effect_1": 2, "Effect_2": effect_type, "DurationIndex": 0}
            self.assertEqual(len(check_34026_inert(row)), 1, effect_type)
        # the stock row shape: eff0 APPLY_AURA DUMMY, 30 s
        stock = {"ID": KILL_COMMAND, "Effect_1": 6, "EffectAura_1": 4, "DurationIndex": 9}
        self.assertEqual(len(check_34026_inert(stock)), 2)

    def test_guard_fires_on_a_duration(self):
        row = {"ID": KILL_COMMAND, "Effect_1": 2, "Effect_2": 3, "DurationIndex": 1}
        self.assertEqual(len(check_34026_inert(row)), 1)
        self.assertEqual(len(check_34026_inert(row, {"duration_ms": 0})), 1)         # built index 1, clean entry: fails
        # the permanent (-1) row a deleted raw key would mint is also a non-zero built index
        self.assertEqual(len(check_34026_inert({**row, "DurationIndex": 30100}, {"duration_ms": None})), 1)
        self.assertEqual(len(check_34026_inert({**row, "DurationIndex": 0}, {"duration_ms": 30000})), 1)
        self.assertEqual(check_34026_inert({**row, "DurationIndex": 0}, {"duration_ms": 0}), [])

    def test_guard_passes_the_rewritten_shape_and_fires_on_a_missing_row(self):
        self.assertEqual(check_34026_inert({"ID": KILL_COMMAND, "Effect_1": 2, "Effect_2": 3, "DurationIndex": 0}), [])
        self.assertEqual(len(check_34026_inert(None)), 1)


# ---- negative fixtures: every check must fire on a minimal bad input -------------------------------------------

class HunterInertKeyNegativeTest(unittest.TestCase):
    NAMES = {"SPELL_RAKE": 59881, "SPELL_RAKE_COMMAND": 201722, "SPELL_BITE": 17253}
    RETIRED = {59881}

    def test_retired_name_in_code_is_caught(self):
        src = {"a.cpp": "void f() { caster->CastSpell(target, HunterData::SPELL_RAKE, true); }\n"}
        bad = check_no_retired_spell_in_code(src, self.NAMES, self.RETIRED)
        self.assertEqual(len(bad), 1)
        self.assertIn("a.cpp:1", bad[0])
        self.assertIn("SPELL_RAKE", bad[0])

    def test_scoped_only_retirements_derivation(self):
        scoped = [{"spell_id": 1, "families": (1,)}, {"spell_id": 2, "families": None},
                  {"spell_id": 3, "families": (1,)}, {"spell_id": 3, "families": None}]
        self.assertEqual(scoped_only_retirements(scoped), {1})     # a global entry for 3 un-exempts it
        self.assertEqual(scoped_only_retirements([]), set())

    def test_command_name_comments_and_unknown_tokens_pass(self):
        src = {"a.cpp": "// SPELL_RAKE used to be here\n/* SPELL_RAKE */ cast(SPELL_RAKE_COMMAND); cast(SPELL_UNKNOWN);\n"}
        self.assertEqual(check_no_retired_spell_in_code(src, self.NAMES, self.RETIRED), [])

    def test_alias_line_naming_a_retired_name_is_caught(self):
        src = {"HunterMechanics.h": "constexpr uint32 SPELL_PET_BLEED = HunterData::SPELL_RAKE;\n"}
        self.assertEqual(len(check_no_retired_spell_in_code(src, self.NAMES, self.RETIRED)), 1)

    def test_short_stem_on_a_commanded_spell_is_caught(self):
        bad = check_command_stems({201722: "rake_201722"}, {201722: "SPELL_RAKE_201722"})
        self.assertEqual(len(bad), 2)   # no '_command_' stem, and the _<id> fallback header name
        self.assertEqual(check_command_stems({201722: "rake_command_201722"}, {201722: "SPELL_RAKE_COMMAND"}), [])

    def test_suffixed_header_name_alone_is_caught(self):
        bad = check_command_stems({201722: "rake_command_201722"}, {201722: "SPELL_RAKE_COMMAND_201722"})
        self.assertEqual(len(bad), 1)

    def test_splash_stem_is_allowed_and_other_ranges_are_ignored(self):
        self.assertEqual(check_command_stems({201736: SPLASH_STEM}, {201736: "SPELL_VENOMOUS_CLOUD_SPLASH"}), [])
        self.assertEqual(check_command_stems({201710: "venom_spit_201710", 201750: "boar_s_speed_201750"}, {}), [])
        self.assertEqual(len(check_command_stems({201738: "spare_201738"}, {})), 1)

    def test_token_regex_and_header_parse(self):
        self.assertEqual(parse_header_names("constexpr uint32 SPELL_X_1 = 5; // x_1\n"), {"SPELL_X_1": 5})
        self.assertEqual(SPELL_TOKEN.findall("HunterData::SPELL_A1 + SPELL_B"), ["SPELL_A1", "SPELL_B"])


if __name__ == "__main__":
    unittest.main()
