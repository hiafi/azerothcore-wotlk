#!/usr/bin/env python3
"""Tests for mechanics_sweep.py's index rules (Stratholme SWEEP-1 D1-D3: each drill's own pass bar, a program longer
than the fight, a program started on a stale game clock) on synthetic aggregate reports.
Run: python3 -I modules/mod-dpssim/tools/test_mechanics_sweep.py
The bar table is checked against mod-boss-mechanics' src/MechanicDrill.h when that source is found
(BOSS_MECHANICS_SRC, else modules/mod-boss-mechanics/src next to this module); the check is skipped otherwise."""

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mechanics_sweep as ms  # noqa: E402

REFERENCES = ["ProtWarriorTankSim", "RestoShamanHealSim", "ArmsWarriorSim", "FireMageSim"]


def spread(values, with_sum=True):
    out = {"mean": sum(values) / len(values), "min": min(values), "max": max(values), "perIteration": values}
    if with_sum:
        out["sum"] = sum(values)
    return out


def member(index, profile, under_test, failures=None):
    total = sum(n for by_key in (failures or {}).values() for n in by_key.values())
    return {"index": index, "profile": profile, "role": "dps", "underTest": under_test,
            "failureTotal": spread([total]), "failures": failures or {}, "hits": spread([total]),
            "dps": spread([1000.0], False), "movingMs": spread([0.0], False), "strategyInstalledAll": True,
            "deaths": 0, "stats": {}}


class SweepIndexTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.count = 0

    def report(self, programs, actor_failures=None, ref_failures=None, group=None, config=None, summary=None):
        """A run (manifest row) whose report is an aggregate with the member under test at index 4."""
        members = [member(i, p, False, (ref_failures or {}).get(p)) for i, p in enumerate(REFERENCES)]
        members.append(member(4, "FuryWarriorSim", True, actor_failures))
        cfg = {"durationMs": 120000, "programs": ms.split_programs(programs)}
        cfg.update(config or {})
        data = {"kind": "mechanics", "config": cfg, "summary": summary or {}, "members": members,
                "groupFailures": group or {}, "aggregate": {"iterations": 5}}
        self.count += 1
        path = Path(self.dir.name) / f"r{self.count}.report.json"
        path.write_text(json.dumps(data))
        return {"class": "Warrior", "spec": f"Fury{self.count}", "profile": f"FuryWarriorSim{self.count}",
                "kind": "mech", "exitCode": 0, "report": str(path)}

    def entry(self, programs, **kw):
        bar = ms.program_bar(programs)
        return ms.spec_entry(self.report(programs, **kw), None, bar)

    @staticmethod
    def bar_problems(entry):
        return [p for p in entry["problems"] if p not in ("no base run", "no baseline: no DPS/HPS loss")]

    # ---- D1: each drill's own bar ----
    def test_reported_tag_is_not_a_problem(self):
        e = self.entry("stratholme-drops:4", actor_failures={"Hit": {"Zone/1": 7}})
        self.assertEqual(self.bar_problems(e), [])
        self.assertEqual(e["reportedHits"], {"Zone/1": 7})

    def test_gated_tag_over_the_bar_is_a_problem(self):
        e = self.entry("stratholme-drops:4", actor_failures={"Hit": {"Zone/2": 2}})
        self.assertEqual(self.bar_problems(e), ["bar: Zone/2 x2 (bar 1)"])

    def test_gated_tag_at_the_bar_passes(self):
        e = self.entry("stratholme-followups:3", actor_failures={"Hit": {"Zone/8": 1}})
        self.assertEqual(self.bar_problems(e), [])
        self.assertEqual(e["gatedHits"], {"Zone/8": 1})

    def test_tag_the_drill_does_not_use_is_a_problem(self):
        e = self.entry("stratholme-drops:4", actor_failures={"Hit": {"Zone/7": 1}})
        self.assertEqual(len(self.bar_problems(e)), 1)
        self.assertIn("not a tag of stratholme-drops", self.bar_problems(e)[0])

    def test_cross_spec_rule(self):
        bar = ms.program_bar("stratholme-followups:3")
        entries = [ms.spec_entry(self.report("stratholme-followups:3", actor_failures={"Hit": {"Zone/8": 1}}), None,
                                 bar) for _ in range(4)]
        problems = ms.cross_spec_problems(bar, entries)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("Zone/8 hits the member under test on 4 specs (bar 3)"))
        self.assertEqual(ms.cross_spec_problems(bar, entries[:3]), [])

    def test_sfk_hunt_references_and_group(self):
        e = self.entry("sfk-hunt:4", actor_failures={"Hit": {"Zone/1": 1, "Zone/5": 6}},
                       ref_failures={"ArmsWarriorSim": {"Hit": {"Zone/1": 3}}, "FireMageSim": {"Hit": {"Zone/5": 6}}},
                       group={"MissedSoak": {"Soak/2": 3}})
        self.assertEqual(self.bar_problems(e), ["reference ArmsWarriorSim bar: Zone/1 x3 (bar 1)",
                                                "group bar: Soak/2 x3 (bar 2)"])
        self.assertEqual(e["reportedHits"], {"Zone/5": 6})
        ok = self.entry("sfk-hunt:4", actor_failures={"Hit": {"Zone/5": 6}}, group={"MissedSoak": {"Soak/2": 2}})
        self.assertEqual(self.bar_problems(ok), [])

    def test_sfk_hunt_landing_is_gated_at_zero(self):
        e = self.entry("sfk-hunt:4", actor_failures={"Hit": {"Zone/3": 1}})
        self.assertEqual(self.bar_problems(e), ["bar: Zone/3 x1 (bar 0)"])

    def test_program_without_a_bar_keeps_the_legacy_rule(self):
        self.assertIsNone(ms.program_bar("smite,fenrus,ras;cookie,barrage:15"))
        self.assertIsNone(ms.program_bar(None))
        self.assertIsNone(ms.program_bar("sfk-hunt:4,barrage:30"))
        e = self.entry("smite", actor_failures={"Hit": {"Frontal/1": 2}})
        self.assertEqual(self.bar_problems(e), ["2 failure(s) of the member under test"])

    def test_several_drills_take_the_strictest_bar(self):
        bar = ms.program_bar("deadmines-followups;sfk-hunt:4")
        self.assertEqual(bar["gated"][5], 1)       # deadmines gates its aftershocks, sfk only reports tag 5
        self.assertEqual(bar["gated"][3], 0)       # sfk's landing beats deadmines' third dash
        self.assertNotIn(5, bar["reported"])
        self.assertIn(4, bar["reported"])         # both report tag 4 (Shockwave, the ringer in the landing)
        self.assertEqual(bar["cross_specs"], 3)

    # ---- D2: a program longer than the fight ----
    def test_comma_program_length_and_late_entries(self):
        length, starts = ms.program_length_ms("deadmines-followups,sfk-hunt,scholomance-shapes")
        self.assertEqual(length, 248000)
        self.assertEqual(starts, [("deadmines-followups", 0), ("sfk-hunt", 64000), ("scholomance-shapes", 128000)])
        self.assertEqual(ms.late_entries("deadmines-followups,sfk-hunt,scholomance-shapes", 120000),
                         ["scholomance-shapes at 128 s"])
        self.assertIsNone(ms.program_length_ms("smite,sfk-hunt"))

    def test_launch_warning(self):
        warnings = ms.program_warnings("deadmines-followups,sfk-hunt,scholomance-shapes", 120000)
        self.assertEqual(len(warnings), 1)
        self.assertIn("scholomance-shapes at 128 s never runs", warnings[0])
        self.assertIn("';'", warnings[0])
        self.assertEqual(ms.program_warnings("deadmines-followups;sfk-hunt:4;scholomance-shapes:3", 120000), [])
        self.assertEqual(ms.program_warnings("sfk-hunt:4", 120000), [])
        self.assertEqual(ms.program_warnings("deadmines-followups;sfk-hunt:4;scholomance-shapes:3", 120000, 6), [])
        uneven = ms.program_warnings("deadmines-followups;sfk-hunt:4;scholomance-shapes:3", 120000, 5)
        self.assertEqual(len(uneven), 1)
        self.assertIn("3 ';' programs over 5 iterations", uneven[0])

    def test_index_flags_a_program_longer_than_the_fight(self):
        e = self.entry("deadmines-followups,sfk-hunt", config={"programLengthsMs": [124000],
                                                                "programLateEntries": []})
        self.assertIn("program longer than the fight (124 s of 120 s): its last entry is cut short", e["problems"])
        # one entry longer than the fight is a choice (alexei, 156 s), not a problem
        e = self.entry("alexei", config={"programLengthsMs": [156000], "programLateEntries": []})
        self.assertFalse(any(p.startswith("program longer") for p in e["problems"]))
        e = self.entry("sfk-hunt:4", config={"programLengthsMs": [250000],
                                             "programLateEntries": ["sfk-hunt at 125 s"]})
        self.assertIn("program longer than the fight (250 s of 120 s): never runs sfk-hunt at 125 s", e["problems"])
        # a report from before the sim wrote the lengths: this table's estimate
        e = self.entry("deadmines-followups,sfk-hunt,scholomance-shapes")
        self.assertIn("program longer than the fight (248 s of 120 s): never runs scholomance-shapes at 128 s",
                      e["problems"])
        e = self.entry("sfk-hunt:4", config={"programLengthsMs": [120000], "programLateEntries": []})
        self.assertFalse(any(p.startswith("program longer") for p in e["problems"]))

    # ---- D3: the program started on a stale game clock ----
    def test_start_lag(self):
        e = self.entry("sfk-hunt:4", summary={"programStartLagMs": spread([0, -44500, 0, 0, 0], False)})
        self.assertIn("program start lag up to -44500 ms (stale game clock: its later entries run early)",
                      e["problems"])
        e = self.entry("sfk-hunt:4", summary={"programStartLagMs": spread([0, 0, 0, 0, 0], False)})
        self.assertFalse(any(p.startswith("program start lag") for p in e["problems"]))

    # ---- the index files ----
    def test_write_index(self):
        manifest = {"sweep": "t", "settings": {"programs": "stratholme-drops:4", "group": 5}, "runs": [
            self.report("stratholme-drops:4", actor_failures={"Hit": {"Zone/1": 7}}),
            self.report("stratholme-drops:4", actor_failures={"Hit": {"Zone/2": 2}}),
        ]}
        json_path, md_path = ms.write_index(manifest, Path(self.dir.name))
        index = json.loads(json_path.read_text())
        self.assertEqual(index["specsWithProblems"], 2)    # both lack a baseline; only one breaks the bar
        self.assertEqual(sum(1 for e in index["entries"] if e["barFailures"]), 1)
        self.assertEqual(index["bar"]["reported"], [1])
        self.assertIn("Bar (stratholme-drops", md_path.read_text())


def boss_mechanics_src():
    env = os.environ.get("BOSS_MECHANICS_SRC")
    if env:
        return Path(env)
    return Path(HERE).parents[1] / "mod-boss-mechanics" / "src"


@unittest.skipUnless((boss_mechanics_src() / "MechanicDrill.h").is_file(), "mod-boss-mechanics source not found")
class BarTableMatchesTheModule(unittest.TestCase):
    """DRILL_BARS mirrors MechanicDrill.h: the bar arrays, every tag a drill's steps use, and the cycle lengths."""

    @classmethod
    def setUpClass(cls):
        cls.text = (boss_mechanics_src() / "MechanicDrill.h").read_text()

    def array(self, name):
        m = re.search(r"constexpr std::uint32_t " + name + r"\[\] = \{([^}]*)\}", self.text)
        self.assertIsNotNone(m, name)
        return {int(v) for v in m.group(1).split(",")}

    def blocks(self):
        starts = list(re.finditer(r'\{ "([a-z0-9-]+)",\s*((?:"[^"]*"\s*)+),\s*(\d+),', self.text))
        for i, m in enumerate(starts):
            end = starts[i + 1].start() if i + 1 < len(starts) else len(self.text)
            yield m.group(1), int(m.group(3)), self.text[m.start():end]

    def test_bar_arrays(self):
        for drill, array in (("deadmines-followups", "kFollowupTags"), ("scholomance-shapes", "kScholoBarTags"),
                             ("stratholme-followups", "kStratBarTags"), ("stratholme-drops", "kDropBarTags")):
            self.assertEqual(set(ms.DRILL_BARS[drill]["gated"]), self.array(array), drill)

    def test_every_tag_and_cycle(self):
        seen = set()
        for name, cycle_ms, block in self.blocks():
            if name not in ms.DRILL_BARS:
                continue
            seen.add(name)
            bar = ms.DRILL_BARS[name]
            self.assertEqual(bar["cycle_ms"], cycle_ms, name)
            ends = re.findall(r"\}(?:,\s*(\d+))?\s*\},", block)
            self.assertTrue(ends, name)
            self.assertEqual(bar["default_cycles"], int(ends[-1] or 3), name)
            used = {int(t) for t in re.findall(r"\btag=(\d+)", block)}
            if "bell=" in block:    # BellLandingTag, BellRingerTag: the bell tag + 1 and + 2
                used |= {t + d for t in used for d in (1, 2) if re.search(r"bell=[^\n]*tag=" + str(t) + r"\b", block)}
            known = set(bar["gated"]) | bar["reported"] | set(bar["group"])
            self.assertEqual(used - known, set(), name)
        self.assertEqual(seen, set(ms.DRILL_BARS))


if __name__ == "__main__":
    unittest.main()
