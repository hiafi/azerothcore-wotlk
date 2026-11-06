#!/usr/bin/env python3
"""Tests for refhealth.py on synthetic run logs. Run: python3 -I modules/mod-dpssim/tools/test_refhealth.py"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import refhealth  # noqa: E402

# A real sheet line (kept run log of a mechanics run), with its ANSI colors
REAL_SHEET = ("\x1b[0m\x1b[36mmod-dpssim: SimActor sheet - 'SimMech0': Strength 264, Agility 77, Stamina 248, "
              "Intellect 43, Spirit 47, flat spell power 19, healing power 63, armor 6294; ratings: crit 37, haste 32, "
              "mastery 15, versatility 25, cooldown haste 8, proc chance 19; max health 3989, max mana 0.\n")


def created(profile, name="SimBot"):
    return (f"mod-dpssim: SimActor created - '{name}' (race {profile['race']}, class {profile['class']}, level "
            f"{profile['level']}), map 0, spellPower 0, attackPower 0, 13 gear item(s), 0 synthetic rating(s).\n")


def sheet(health, name="SimBot"):
    return (f"mod-dpssim: SimActor sheet - '{name}': Strength 1, Agility 1, Stamina 1, Intellect 1, Spirit 1, "
            f"flat spell power 0, healing power 0, armor 0; ratings: crit 0, haste 0, mastery 0, versatility 0, "
            f"cooldown haste 0, proc chance 0; max health {health}, max mana 0.\n")


class RefHealthTests(unittest.TestCase):
    def setUp(self):
        self.manifest = refhealth.load_manifest()
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def write_logs(self, health_of, extra=None):
        for profile in self.manifest["profiles"]:
            health = health_of(profile)
            if health is None:
                continue
            path = os.path.join(self.dir.name, f"{profile['name']}.20261105-120000.run.log")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("unrelated line\n" + created(profile) + sheet(health) + (extra or ""))

    def test_parse_real_ansi_line(self):
        path = os.path.join(self.dir.name, "x.20261105-000000.run.log")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(REAL_SHEET)
        data = refhealth.read_log(path)
        self.assertEqual(data["health"], 3989)
        self.assertEqual(data["problems"], [])

    def test_medians_and_rows_string(self):
        base = {"n20": 1000, "n60": 3000, "h60": 4000, "e1": 5000, "e2": 6000}
        # class offset makes the median the middle class; tanks get +500
        def health(profile):
            return base[profile["row"]] + (500 if profile["role"] == "tank" else 0) + profile["class"] * 10
        self.write_logs(health)
        measurements, problems = refhealth.collect(self.manifest, self.dir.name)
        self.assertEqual(problems, [])
        rows = refhealth.aggregate(self.manifest, measurements)
        # n60 non-tank: classes 1,2,3,4,5,6,7,8,9,11 -> median of 10 values is (50+60)/2 = 55 above base
        self.assertEqual(rows["n60"]["dps"]["median"], 3055)
        self.assertEqual(rows["n60"]["dps"]["n"], 10)
        # level 20 has no death knight
        self.assertEqual(rows["n20"]["dps"]["n"], 9)
        self.assertEqual(rows["n20"]["tank"]["n"], 5)
        # tanks: warrior, paladin, rogue, death knight, shaman, druid -> classes 1,2,4,6,7,11, median (40+60)/2 = 50
        self.assertEqual(rows["n60"]["tank"]["median"], 3550)
        # empowered 3 = e2 + (e2 - e1)
        self.assertEqual(rows["e3"]["dps"]["median"], 2 * rows["e2"]["dps"]["median"] - rows["e1"]["dps"]["median"])
        text = refhealth.rows_string(rows)
        keys = [part.split(":")[0] for part in text.split()]
        self.assertEqual(keys, ["20", "60", "60h", "60e1", "60e2", "60e3"])
        self.assertIn("60h:4055:4550", text)
        report = refhealth.format_report(rows, problems)
        self.assertIn("BossMechanics.ReferenceHealth.Rows", report)

    def test_rounding(self):
        self.write_logs(lambda p: 3001 if p["row"] == "n60" else 4000)
        measurements, _ = refhealth.collect(self.manifest, self.dir.name)
        rows = refhealth.aggregate(self.manifest, measurements, rounding=10)
        self.assertEqual(rows["n60"]["dps"]["value"], 3000)

    def test_missing_log_and_wrong_level_are_problems(self):
        self.write_logs(lambda p: None if p["name"].endswith("Mage_dps_h60") else 3000)
        # a level 60 log for a level 20 profile
        wrong = next(p for p in self.manifest["profiles"] if p["row"] == "n20")
        path = os.path.join(self.dir.name, f"{wrong['name']}.20261105-130000.run.log")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(created(dict(wrong, level=60)) + sheet(4000))
        measurements, problems = refhealth.collect(self.manifest, self.dir.name)
        self.assertTrue(any("Mage_dps_h60: no kept run log" in p for p in problems))
        self.assertTrue(any(wrong["name"] in p and "ran as" in p for p in problems))

    def test_equip_failure_is_reported(self):
        self.write_logs(lambda p: 3000,
                        extra="mod-dpssim: SimActor::Create() - could not equip item 123 (InventoryResult 1).\n")
        _, problems = refhealth.collect(self.manifest, self.dir.name)
        self.assertTrue(any("could not equip item 123" in p for p in problems))

    def test_newest_log_wins(self):
        profile = self.manifest["profiles"][0]
        for stamp, health in (("20261105-100000", 1111), ("20261105-110000", 2222)):
            with open(os.path.join(self.dir.name, f"{profile['name']}.{stamp}.run.log"), "w") as handle:
                handle.write(created(profile) + sheet(health))
        measurements, _ = refhealth.collect(self.manifest, self.dir.name)
        self.assertEqual(measurements[profile["name"]], 2222)

    def test_manifest_matches_profile_files(self):
        self.assertEqual(refhealth.main(["check"]), 0)

    def test_plan_has_one_command_per_profile(self):
        # the profile name never appears in another profile's command
        names = [p["name"] for p in self.manifest["profiles"]]
        self.assertEqual(len(names), len(set(names)))
        for profile in self.manifest["profiles"]:
            self.assertRegex(profile["name"], r"^[A-Za-z0-9_]+$")   # run-sim.sh batch names cannot hold dots


if __name__ == "__main__":
    unittest.main()
