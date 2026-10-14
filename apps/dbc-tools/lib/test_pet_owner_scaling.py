"""
Spell.pet_owner_scaling (hunter-rework SHARED §C7.11, PLAN §3 #26, PET §4.3a; T1 step 8b): a pet ability's
tooltip scales by the owner's RAP and SP instead of the client's `$AP` (the hunter's melee AP). Fixtures only.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_pet_owner_scaling.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import potency  # noqa: E402
from lib.dsl import model, registry  # noqa: E402

PET_BIT = 0x10000000
SPELL_FAMILY_HUNTER = 9


def _bite(**overrides) -> model.Spell:
    """A Bite-shaped pet spell: ap_potency 25.5, instant (T = 1.5), pet bit d1 b28."""
    raw = {"SpellLevel": 1, "SpellClassSet": SPELL_FAMILY_HUNTER, "SpellClassMask_2": PET_BIT,
           "SpellClassMask_3": 0x800000,
           "Description_Lang_enUS": "Bite the target for {pot1} damage."}
    raw.update(overrides.pop("raw_overrides", {}))
    kwargs = dict(
        id=200990, name="Test Bite", cast_time_ms=0, raw_overrides=raw,
        effects=[model.Effect(type=2, ap_potency=25.5, potency_kind=potency.KIND_DIRECT)],
    )
    kwargs.update(overrides)
    return model.Spell(**kwargs)


def _description(spell: model.Spell) -> str:
    return spell.to_entry()["raw_overrides"]["Description_Lang_enUS"]


def _ends(text: str) -> tuple[str, str]:
    lo, hi = re.match(r"Bite the target for (\$\{.*\}) to (\$\{.*\}) damage\.$", text).groups()
    return lo, hi


class PetOwnerScalingTest(unittest.TestCase):
    def test_none_is_byte_identical_to_today(self):
        entry = _bite().to_entry()
        explicit = _bite(pet_owner_scaling=None).to_entry()
        self.assertEqual(entry, explicit)
        self.assertNotIn("owner_scaling", entry["effect1"]["_potency"])
        # A pet-bit spell is not a "ranged" one for the token (uses_ranged_attack_power), so it reads $AP today.
        self.assertIn("0.1093*$AP", entry["raw_overrides"]["Description_Lang_enUS"])
        self.assertNotIn("$RAP", entry["raw_overrides"]["Description_Lang_enUS"])

    def test_full_shares_put_both_terms_in_every_branch_of_both_range_ends(self):
        text = _description(_bite(pet_owner_scaling=(100, 100)))
        low, high = _ends(text)
        for end in (low, high):
            self.assertEqual(end.count("0.1093*$RAP+0.1093*$SP"), 3, end)   # the 3 places c*$AP sits today
            self.assertNotIn("$AP", end)
            self.assertTrue(end.startswith("${$max($max(0.1093*$RAP+0.1093*$SP,"), end)

    def test_shares_scale_the_coefficient(self):
        text = _description(_bite(pet_owner_scaling=(100, 50)))
        self.assertIn("0.1093*$RAP+0.0546*$SP", text)   # 0.10929 * 0.5 = 0.05464

    def test_zero_share_drops_its_term(self):
        only_rap = _description(_bite(pet_owner_scaling=(100, 0)))
        self.assertIn("+0.1093*$RAP", only_rap)
        self.assertNotIn("$SP", only_rap)
        only_sp = _description(_bite(pet_owner_scaling=(0, 100)))
        self.assertNotIn("$RAP", only_sp)
        self.assertIn("0.1093*$SP", only_sp)

    def test_zero_zero_renders_the_base_line_only(self):
        text = _description(_bite(pet_owner_scaling=(0, 0)))
        for token in ("$AP", "$RAP", "$SP"):
            self.assertNotIn(token, text)
        low, _ = _ends(text)
        self.assertTrue(low.startswith("${$max($max(0,"), low)

    def test_pot_text_carries_the_same_terms(self):
        spell = _bite(pet_owner_scaling=(100, 100))
        from_text = registry.pot_text(spell)
        low, high = _ends(_description(spell))
        self.assertEqual(from_text, f"{low} to {high}")
        self.assertEqual(registry.pot_text(_bite()).count("$AP"), 6)

    def test_periodic_total_scales_the_terms_by_the_tick_count(self):
        spell = model.Spell(
            id=200991, name="Test Venom", duration_ms=10000,
            raw_overrides={"SpellLevel": 1, "SpellClassSet": SPELL_FAMILY_HUNTER, "SpellClassMask_2": PET_BIT,
                           "Description_Lang_enUS": "{pot1.total}"},
            effects=[model.Effect(type=6, apply_aura=3, amplitude=2000, ap_potency=20,
                                  potency_kind=potency.KIND_PERIODIC)],
            pet_owner_scaling=(100, 100),
        )
        text = spell.to_entry()["raw_overrides"]["Description_Lang_enUS"]
        per_tick = 0.2 * (2.0 / 3.5)
        self.assertIn(f"{per_tick * 5:.4f}".rstrip("0") + "*$RAP", text)
        self.assertIn(f"{per_tick * 5:.4f}".rstrip("0") + "*$SP", text)

    def test_option_without_the_pet_bit_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "pet bit"):
            _bite(raw_overrides={"SpellClassMask_2": 0x1}, pet_owner_scaling=(100, 100)).to_entry()
        with self.assertRaisesRegex(ValueError, "pet bit"):
            _bite(raw_overrides={"SpellClassMask_2": 0}, pet_owner_scaling=(100, 100)).to_entry()

    def test_option_together_with_sp_potency_is_an_error(self):
        spell = _bite(
            effects=[model.Effect(type=2, ap_potency=25.5, sp_potency=10, potency_kind=potency.KIND_DIRECT)],
            pet_owner_scaling=(100, 100),
        )
        with self.assertRaisesRegex(ValueError, "sp_potency"):
            spell.to_entry()

    def test_bad_shares_are_an_error(self):
        for shares in ((100,), (-1, 0), ("a", 1)):
            with self.assertRaises(ValueError, msg=str(shares)):
                _bite(pet_owner_scaling=shares).to_entry()

    def test_resolved_potency_default_leaves_the_stat_term_alone(self):
        resolved = potency.resolve(potency.PotencyEffect(ap_potency=25.5, t_ms=1500), spell_level=1)
        self.assertIsNone(resolved.owner_scaling)
        self.assertIn("*$AP", potency.tooltip_expression(resolved))


if __name__ == "__main__":
    unittest.main()
