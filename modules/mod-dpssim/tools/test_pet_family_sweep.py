#!/usr/bin/env python3
"""Tests for pet_family_sweep.py: the family table, the job plan (1-target runs first, the env run-sim.sh reads), the
report numbers (pet share) and the summary (median, spread, the 50 DPS flag) on synthetic reports.
Run: python3 -I modules/mod-dpssim/tools/test_pet_family_sweep.py"""

import argparse
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pet_family_sweep as pfs  # noqa: E402

# Pet family numbers of CreatureFamily.dbc that a hunter can have (hunter-pet-families DATA-INVENTORY 3)
HUNTER_FAMILIES = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 20, 21, 24, 25, 26, 27, 30, 31, 32, 33, 34, 35, 37, 38, 39,
                   41, 42, 43, 44, 45, 46}


def report(dps, pet_damage, total, entry, per_iteration=None, disabled=None):
    return {
        "config": {"petCreatureEntry": entry, "buffSet": "full_raid", "disabledSpells": disabled or []},
        "summary": {"dps": dps, "totalDamage": total},
        "spells": [{"spellId": 1, "isPet": True, "totalDamage": pet_damage},
                   {"spellId": 2, "isPet": False, "totalDamage": total - pet_damage}],
        "aggregate": {"iterations": len(per_iteration or [dps]), "perIteration": {"dps": per_iteration or [dps]}},
    }


def run_args(**overrides):
    values = dict(buff_set="full_raid", disable_spells=None, run_sim=pfs.RUN_SIM, profile="BmHunterSim", duration=120,
                  level=60, race=6, iterations=5, step=100)
    values.update(overrides)
    return argparse.Namespace(**values)


class FamilyTableTests(unittest.TestCase):
    def test_every_hunter_family_once(self):
        families = pfs.load_families()
        self.assertEqual({f["family"] for f in families}, HUNTER_FAMILIES)
        self.assertEqual(len(families), len(HUNTER_FAMILIES))
        self.assertEqual(len({f["key"] for f in families}), len(families))
        self.assertEqual(len({f["entry"] for f in families}), len(families))
        for f in families:
            self.assertIn(f["tree"], ("Ferocity", "Tenacity", "Cunning"))
            self.assertTrue(f["creature"].startswith("Tamable "), f)

    def test_profile_wolf_is_in_the_table(self):
        # BmHunterSim.conf's own pet, so a full_raid sweep's wolf matches the profile
        wolf = pfs.select_families(pfs.load_families(), "wolf")[0]
        self.assertEqual(wolf["entry"], 26016)

    def test_select_by_key_name_or_number(self):
        families = pfs.load_families()
        chosen = pfs.select_families(families, "cat, Bird of Prey,26, 33")
        self.assertEqual([f["key"] for f in chosen], ["cat", "bird-of-prey", "sporebat"])
        self.assertEqual(len(pfs.select_families(families, "")), len(families))
        with self.assertRaises(ValueError):
            pfs.select_families(families, "dragon")

    def test_targets(self):
        self.assertEqual(pfs.parse_targets("1,3,5"), [1, 3, 5])
        self.assertEqual(pfs.parse_targets(" 3, 1,3"), [3, 1])
        for bad in ("0", "11", ""):
            with self.assertRaises(ValueError):
                pfs.parse_targets(bad)


class PlanTests(unittest.TestCase):
    def test_single_target_runs_first_and_env(self):
        families = pfs.select_families(pfs.load_families(), "wolf,cat")
        jobs = pfs.plan_jobs(run_args(), families, [1, 3], "s1")
        self.assertEqual([(j["key"], j["targets"]) for j in jobs], [("wolf", 1), ("cat", 1), ("wolf", 3), ("cat", 3)])
        env = jobs[3]["env"]
        self.assertEqual(env["DPSSIM_PET_FAMILY"], "cat")
        self.assertEqual(env["DPSSIM_BUFF_SET"], "full_raid")
        self.assertEqual(env["DPSSIM_BATCH_TAG"], "s1-cat-t3")
        self.assertEqual(env["DPSSIM_NO_HTML"], "1")
        self.assertNotIn("DPSSIM_DISABLE_SPELLS", env)
        # <profile> [durationSeconds] [level] [race] [iterations] [stepMs] [targets]
        self.assertEqual(jobs[3]["cmd"][1:], ["BmHunterSim", "120", "60", "6", "5", "100", "3"])

    def test_disable_spells_passes_through(self):
        jobs = pfs.plan_jobs(run_args(disable_spells="24604"), pfs.load_families()[:1], [1], "s")
        self.assertEqual(jobs[0]["env"]["DPSSIM_DISABLE_SPELLS"], "24604")

    def test_disable_family_spells_only_for_that_family(self):
        fams = pfs.select_families(pfs.load_families(), "wolf,raptor")
        jobs = pfs.plan_jobs(run_args(disable_spells="24604", disable_family_spells=[("raptor", "201985")]),
                             fams, [1], "s")
        by_key = {j["key"]: j["env"]["DPSSIM_DISABLE_SPELLS"] for j in jobs}
        self.assertEqual(by_key, {"wolf": "24604", "raptor": "24604,201985"})

    def test_parse_family_spells(self):
        self.assertEqual(pfs.parse_family_spells("Raptor=201985, 24604"), ("raptor", "201985,24604"))
        with self.assertRaises(argparse.ArgumentTypeError):
            pfs.parse_family_spells("raptor")

    def test_unknown_family_in_disable_family_spells_is_an_error(self):
        with self.assertRaises(ValueError) as ctx:
            pfs.plan_jobs(run_args(disable_family_spells=[("raptr", "201985")]), pfs.load_families()[:1], [1], "s")
        self.assertIn("raptr", str(ctx.exception))

    def test_repeated_family_spells_are_merged(self):
        merged = pfs.family_spell_map([("raptor", "201985"), ("raptor", "201985,24604"), ("wolf", "24604")])
        self.assertEqual(merged, {"raptor": [201985, 24604], "wolf": [24604]})

    def test_jobs_record_what_the_report_must_show(self):
        fams = pfs.select_families(pfs.load_families(), "wolf,raptor")
        jobs = pfs.plan_jobs(run_args(disable_family_spells=[("raptor", "201985")]), fams, [1], "s")
        self.assertEqual({j["key"]: (j["buffSet"], j["disabled"]) for j in jobs},
                         {"wolf": ("full_raid", []), "raptor": ("full_raid", [201985])})

    def test_bad_spell_ids_are_errors(self):
        with self.assertRaises(ValueError):
            pfs.plan_jobs(run_args(disable_spells="24604,x"), pfs.load_families()[:1], [1], "s")
        with self.assertRaises(Exception):
            pfs.parse_family_spells("raptor=")

    def test_jobs_clamp_is_six(self):
        self.assertEqual([pfs.clamp_jobs(n) for n in (0, 1, 6, 10)], [1, 1, 6, 6])

    def test_batch_tags_are_valid_and_unique(self):
        jobs = pfs.plan_jobs(run_args(), pfs.load_families(), [1, 3, 5], "pf20261112-120000")
        tags = [j["env"]["DPSSIM_BATCH_TAG"] for j in jobs]
        self.assertEqual(len(tags), len(set(tags)))
        for tag in tags:
            # run-sim.sh's DPSSIM_BATCH_TAG rule
            self.assertRegex(tag, r"^[A-Za-z0-9_-]+$")


class IndexTests(unittest.TestCase):
    def test_pet_share(self):
        numbers = pfs.report_numbers(report(1000.0, 30000.0, 120000.0, 26016, [990.0, 1010.0]))
        self.assertAlmostEqual(numbers["petSharePct"], 25.0)
        self.assertEqual((numbers["dpsMin"], numbers["dpsMax"]), (990.0, 1010.0))
        self.assertEqual(numbers["buffSet"], "full_raid")

    def manifest(self, results):
        """results: (key, targets, dps or None for a failed run)"""
        families = {f["key"]: f for f in pfs.load_families()}
        runs, reports = [], {}
        for key, n, dps in results:
            fam = families[key]
            path = f"/r/{key}.t{n}.json"
            runs.append({"family": fam["family"], "key": key, "name": fam["name"], "tree": fam["tree"],
                         "entry": fam["entry"], "targets": n, "exitCode": 0 if dps is not None else 1,
                         "report": path if dps is not None else None, "log": f"/l/{key}.log",
                         "buffSet": "full_raid", "disabled": []})
            if dps is not None:
                reports[path] = report(dps, dps * 30.0, dps * 120.0, fam["entry"])
        return {"sweep": "t", "settings": {}, "runs": runs}, reports

    def test_median_spread_and_flag(self):
        manifest, reports = self.manifest([
            ("wolf", 1, 1000.0), ("cat", 1, 1040.0), ("bear", 1, 960.0), ("boar", 1, 1100.0), ("spider", 1, 1010.0),
            ("wolf", 3, 1500.0), ("cat", 3, 1400.0)])
        rows = pfs.build_rows(manifest, load=reports.__getitem__)
        summary = pfs.summarize(rows, 50.0)
        self.assertEqual(summary["medians"][1], 1010.0)
        self.assertEqual(summary["medians"][3], 1450.0)
        self.assertEqual(summary["spread1t"], 140.0)
        # boar is 90 over the median, bear 50 under (not above the threshold)
        self.assertEqual(summary["flagged"], ["boar"])
        by_key = {f["key"]: f for f in summary["families"]}
        self.assertAlmostEqual(by_key["bear"]["byTargets"][1]["vsMedian"], -50.0)
        self.assertAlmostEqual(by_key["wolf"]["byTargets"][3]["vsMedian"], 50.0)
        self.assertAlmostEqual(by_key["wolf"]["byTargets"][1]["petSharePct"], 25.0)
        # ranked by 1-target DPS
        self.assertEqual([f["key"] for f in summary["families"]], ["boar", "cat", "spider", "wolf", "bear"])

    def test_failed_and_mismatched_runs_are_errors(self):
        manifest, reports = self.manifest([("wolf", 1, 1000.0), ("cat", 1, None), ("bear", 1, 990.0)])
        reports["/r/bear.t1.json"]["config"]["petCreatureEntry"] = 26016
        rows = pfs.build_rows(manifest, load=reports.__getitem__)
        errors = {r["key"]: r["error"] for r in rows if r["error"]}
        self.assertEqual(set(errors), {"cat", "bear"})
        self.assertIn("not 34025", errors["bear"])
        summary = pfs.summarize(rows)
        self.assertEqual(summary["medians"][1], 1000.0)
        self.assertEqual(summary["flagged"], [])
        markdown = pfs.summary_markdown(manifest, summary)
        self.assertIn("## Failed runs", markdown)
        self.assertIn("| Wolf | Ferocity | 26016 | 1,000.0 |", markdown)

    def test_report_from_an_image_before_sim1_is_an_error(self):
        manifest, reports = self.manifest([("wolf", 1, 1000.0), ("cat", 1, 1010.0), ("bear", 1, 1020.0)])
        del reports["/r/wolf.t1.json"]["config"]["petCreatureEntry"]
        reports["/r/cat.t1.json"]["config"] = {}
        del reports["/r/bear.t1.json"]["config"]["disabledSpells"]
        rows = pfs.build_rows(manifest, load=reports.__getitem__)
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertIn("predates SIM1", row["error"])

    def test_buff_set_and_disabled_spells_must_match_the_job(self):
        manifest, reports = self.manifest([("wolf", 1, 1000.0), ("cat", 1, 1010.0), ("raptor", 1, 1020.0)])
        reports["/r/wolf.t1.json"]["config"]["buffSet"] = "self_only"
        reports["/r/cat.t1.json"]["config"]["disabledSpells"] = [24604]
        manifest["runs"][2]["disabled"] = [201985]
        rows = {r["key"]: r for r in pfs.build_rows(manifest, load=reports.__getitem__)}
        self.assertIn("buff set self_only, not full_raid", rows["wolf"]["error"])
        self.assertIn("disabled spells [24604], not []", rows["cat"]["error"])
        self.assertIn("disabled spells [], not [201985]", rows["raptor"]["error"])
        reports["/r/raptor.t1.json"]["config"]["disabledSpells"] = [201985]
        rows = {r["key"]: r for r in pfs.build_rows(manifest, load=reports.__getitem__)}
        self.assertIsNone(rows["raptor"]["error"])
        self.assertEqual(rows["raptor"]["disabledSpells"], [201985])

    def test_flag_direction_and_disabled_marker_in_the_summary(self):
        manifest, reports = self.manifest([("wolf", 1, 1000.0), ("cat", 1, 1000.0), ("bear", 1, 1000.0),
                                           ("boar", 1, 1100.0), ("spider", 1, 900.0)])
        manifest["runs"][4]["disabled"] = [201753]
        reports["/r/spider.t1.json"]["config"]["disabledSpells"] = [201753]
        manifest["settings"] = {"disableFamilySpells": {"spider": [201753]}}
        summary = pfs.summarize(pfs.build_rows(manifest, load=reports.__getitem__), 50.0)
        directions = {f["key"]: f["direction"] for f in summary["families"]}
        self.assertEqual(directions["boar"], "over")
        self.assertEqual(directions["spider"], "under")
        self.assertEqual(directions["wolf"], "")
        markdown = pfs.summary_markdown(manifest, summary)
        self.assertIn("**over**", markdown)
        self.assertIn("**under** (no 201753)", markdown)
        self.assertIn("disabled for spider 201753", markdown)

    def test_write_index_files(self):
        manifest, reports = self.manifest([("wolf", 1, 1000.0), ("cat", 1, 1020.0)])
        with tempfile.TemporaryDirectory() as tmp:
            for run in manifest["runs"]:
                path = Path(tmp) / Path(run["report"]).name
                path.write_text(json.dumps(reports[run["report"]]))
                run["report"] = str(path)
            self.assertEqual(pfs.write_index(manifest, Path(tmp)), 0)
            csv_lines = (Path(tmp) / "sweep.csv").read_text().splitlines()
            self.assertEqual(csv_lines[0].split(",")[:7], ["family", "key", "name", "tree", "entry", "targets", "dps"])
            self.assertEqual(len(csv_lines), 3)
            self.assertTrue((Path(tmp) / "summary.md").read_text().startswith("# Pet family sweep t"))
            self.assertEqual(json.loads((Path(tmp) / "summary.json").read_text())["flagged"], [])


if __name__ == "__main__":
    unittest.main()
