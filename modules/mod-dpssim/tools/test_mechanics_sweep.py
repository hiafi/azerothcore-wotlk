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

    def test_brd_shapes_leash_and_ward(self):
        # the leashes post OffSpot failures under Zone/<tag>; the ward's Stack misses are reported
        e = self.entry("blackrock-depths-shapes:2", actor_failures={"OffSpot": {"Zone/2": 2, "Zone/3": 1},
                                                                    "MissedStack": {"Stack/11": 3}})
        self.assertEqual(self.bar_problems(e), ["bar: Zone/2 x2 (bar 1)"])
        self.assertEqual(e["reportedHits"], {"Stack/11": 3})
        self.assertEqual(ms.program_length_ms("blackrock-depths-shapes:2"), (120000, [("blackrock-depths-shapes", 0)]))
        self.assertEqual(ms.program_warnings("blackrock-depths-shapes:2", 120000), [])

    def test_brd_shapes_2_beam_loner_and_crossfire(self):
        # wave 2: the beam's MissedSoak is a group failure, the loner's MissedStack the member's, Livewire reported
        e = self.entry("blackrock-depths-shapes-2:2",
                       actor_failures={"MissedStack": {"Stack/22": 2}, "Hit": {"Zone/23": 4, "Zone/26": 1}},
                       group={"MissedSoak": {"Soak/21": 3}})
        self.assertEqual(self.bar_problems(e), ["bar: Stack/22 x2 (bar 1)", "group bar: Soak/21 x3 (bar 2)"])
        self.assertEqual(e["reportedHits"], {"Zone/23": 4})
        ok = self.entry("blackrock-depths-shapes-2", actor_failures={"Hit": {"Zone/25": 1, "Zone/24": 2}},
                        group={"MissedSoak": {"Soak/21": 2}})
        self.assertEqual(self.bar_problems(ok), [])
        self.assertEqual(ms.program_length_ms("blackrock-depths-shapes-2:2"),
                         (120000, [("blackrock-depths-shapes-2", 0)]))
        self.assertEqual(ms.program_warnings("blackrock-depths-shapes-2:2", 120000), [])
        # one drill per sweep: the two Blackrock Depths drills never share a tag
        one, two = ms.DRILL_BARS["blackrock-depths-shapes"], ms.DRILL_BARS["blackrock-depths-shapes-2"]
        tags = [set(b["gated"]) | b["reported"] | set(b["group"]) for b in (one, two)]
        self.assertEqual(tags[0] & tags[1], set())

    def test_scarlet_shapes_tank_rows_and_torment(self):
        # Scarlet Monastery WP-G1: the tank-only tags bar the reference tank too; the Torment's short passes are a
        # group failure; the scent's landing is reported
        e = self.entry("scarlet-monastery-shapes:3",
                       actor_failures={"Hit": {"Zone/4": 2, "Zone/3": 4, "Gaze/9": 1, "Zone/12": 3}},
                       ref_failures={"ProtWarriorTankSim": {"OffSpot": {"Zone/2": 2}, "Hit": {"Zone/6": 1}},
                                     "ArmsWarriorSim": {"Hit": {"Zone/5": 1, "Zone/8": 4}},
                                     "FireMageSim": {"Hit": {"Zone/4": 3}}},
                       group={"MissedSoak": {"Soak/1": 6}}, config={"durationMs": 180000})
        self.assertEqual(self.bar_problems(e), ["bar: Zone/4 x2 (bar 1)",
                                                "reference ProtWarriorTankSim bar: Zone/2 x2 (bar 1)",
                                                "reference FireMageSim bar: Zone/4 x3 (bar 1)",
                                                "group bar: Soak/1 x6 (bar 5)"])
        self.assertEqual(e["reportedHits"], {"Zone/3": 4, "Zone/12": 3})
        ok = self.entry("scarlet-monastery-shapes", actor_failures={"Hit": {"Zone/7": 1, "Zone/10": 1, "Zone/13": 1}},
                        ref_failures={"ProtWarriorTankSim": {"OffSpot": {"Zone/2": 1}, "Hit": {"Zone/6": 1}},
                                      "ArmsWarriorSim": {"Hit": {"Zone/13": 1}}},
                        group={"MissedSoak": {"Soak/1": 5}}, config={"durationMs": 180000})
        self.assertEqual(self.bar_problems(ok), [])
        # the Flame Spike's pillar on a reference member twice is a problem (a random carrier: the group's signal)
        two = self.entry("scarlet-monastery-shapes:3", ref_failures={"ArmsWarriorSim": {"Hit": {"Zone/13": 2}}},
                         config={"durationMs": 180000})
        self.assertEqual(self.bar_problems(two), ["reference ArmsWarriorSim bar: Zone/13 x2 (bar 1)"])
        self.assertEqual(ms.program_length_ms("scarlet-monastery-shapes:3"),
                         (180000, [("scarlet-monastery-shapes", 0)]))
        self.assertEqual(ms.program_length_ms("scarlet-monastery-shapes"),
                         (180000, [("scarlet-monastery-shapes", 0)]))
        self.assertEqual(ms.program_warnings("scarlet-monastery-shapes:3", 180000), [])
        # a 120 s fight would cut Thalnos's cycle: the launch warns
        self.assertEqual(len(ms.program_warnings("scarlet-monastery-shapes:3", 120000)), 1)
        # every tag the reference bar names is also gated for the member under test
        bar = ms.DRILL_BARS["scarlet-monastery-shapes"]
        self.assertTrue(set(bar["references"]) <= set(bar["gated"]))

    def test_scarlet_shapes_2_three_cycles_and_flame(self):
        # Scarlet Monastery WP-G2: three 60 s cycles (180 s); the Vigil Flame's unshared flares are a group failure
        # (at most 2); the tank-only and random-carrier tags bar the reference members; the Blade spread is reported
        e = self.entry("scarlet-monastery-shapes-2:3",
                       actor_failures={"Hit": {"Zone/39": 2, "Spread/32": 9, "Zone/36": 1}},
                       ref_failures={"ProtWarriorTankSim": {"OffSpot": {"Zone/23": 3, "Zone/31": 1},
                                                            "Hit": {"Zone/25": 2}},
                                     "RestoShamanHealSim": {"Hit": {"Zone/30": 2, "Zone/37": 4}},
                                     "ArmsWarriorSim": {"Hit": {"Zone/26": 1}}},
                       group={"MissedSoak": {"Soak/29": 3}},
                       config={"durationMs": 180000})
        self.assertEqual(self.bar_problems(e), ["bar: Zone/39 x2 (bar 1)",
                                                "reference ProtWarriorTankSim bar: Zone/23 x3 (bar 1), Zone/25 x2 "
                                                "(bar 1)",
                                                "reference RestoShamanHealSim bar: Zone/30 x2 (bar 1)",
                                                "group bar: Soak/29 x3 (bar 2)"])
        self.assertEqual(e["reportedHits"], {"Spread/32": 9})
        ok = self.entry("scarlet-monastery-shapes-2:3",
                        actor_failures={"Hit": {"Zone/22": 1, "Zone/40": 1}, "OffSpot": {"Spot/21": 1}},
                        ref_failures={"ProtWarriorTankSim": {"OffSpot": {"Zone/23": 1}}},
                        group={"MissedSoak": {"Soak/29": 2}}, config={"durationMs": 180000})
        self.assertEqual(self.bar_problems(ok), [])
        self.assertEqual(ms.program_length_ms("scarlet-monastery-shapes-2:3"),
                         (180000, [("scarlet-monastery-shapes-2", 0)]))
        self.assertEqual(ms.program_length_ms("scarlet-monastery-shapes-2"),
                         (180000, [("scarlet-monastery-shapes-2", 0)]))
        self.assertEqual(ms.program_warnings("scarlet-monastery-shapes-2:3", 180000), [])
        # a 120 s fight would cut the Herod cycle: the launch warns
        self.assertEqual(len(ms.program_warnings("scarlet-monastery-shapes-2:3", 120000)), 1)
        bar = ms.DRILL_BARS["scarlet-monastery-shapes-2"]
        self.assertTrue(set(bar["references"]) <= set(bar["gated"]))
        # wave 1 and wave 2 tags never meet (one sweep per drill; a ';' rotation would still be unambiguous)
        wave1 = ms.DRILL_BARS["scarlet-monastery-shapes"]
        tags1 = set(wave1["gated"]) | wave1["reported"] | set(wave1["group"])
        tags2 = set(bar["gated"]) | bar["reported"] | set(bar["group"])
        self.assertEqual(tags1 & tags2, set())

    # ---- D2: a program longer than the fight ----
    def test_ragefire_shapes_bars_and_groups(self):
        # Ragefire Chasm WP-G1: the pools take every member (reference bars), three group tags, the chase circles, the
        # kicked school's bar and the hard mode bursts reported, three 60 s cycles
        e = self.entry("ragefire-chasm-shapes:3",
                       actor_failures={"Hit": {"Zone/1": 6, "Zone/2": 2, "Zone/11": 2, "Hide/12": 1, "Hide/13": 1,
                                               "Zone/17": 4, "Zone/19": 3, "Spread/6": 1}},
                       ref_failures={"ProtWarriorTankSim": {"Hit": {"Zone/10": 2, "Zone/8": 5}},
                                     "FireMageSim": {"Hit": {"Zone/11": 3, "Zone/5": 1}}},
                       group={"MissedSoak": {"Soak/7": 2, "Soak/14": 2, "Soak/15": 15, "Soak/16": 1,
                                             "Soak/20": 2, "Soak/21": 2}},
                       config={"durationMs": 180000})
        self.assertEqual(self.bar_problems(e), ["bar: Hide/12 x1 (bar 0), Hide/13 x1 (bar 0), Zone/2 x2 (bar 1)",
                                                "reference ProtWarriorTankSim bar: Zone/10 x2 (bar 1)",
                                                "reference FireMageSim bar: Zone/11 x3 (bar 2)",
                                                "group bar: Soak/16 x1 (bar 0), Soak/20 x2 (bar 1), Soak/7 x2 (bar 1)"])
        self.assertEqual(e["reportedHits"], {"Zone/1": 6, "Zone/17": 4, "Zone/19": 3})
        self.assertEqual(ms.program_length_ms("ragefire-chasm-shapes"), (180000, [("ragefire-chasm-shapes", 0)]))
        self.assertEqual(ms.program_warnings("ragefire-chasm-shapes:3", 180000), [])
        self.assertEqual(len(ms.program_warnings("ragefire-chasm-shapes:3", 120000)), 1)
        bar = ms.DRILL_BARS["ragefire-chasm-shapes"]
        self.assertTrue(set(bar["references"]) <= set(bar["gated"]))
        self.assertFalse(set(bar["group"]) & (set(bar["gated"]) | bar["reported"]))

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
                             ("stratholme-followups", "kStratBarTags"), ("stratholme-drops", "kDropBarTags"),
                             ("blackrock-spire-followups", "kBrsBarTags"), ("rolling-fronts", "kFrontBarTags"),
                             ("blackrock-depths-shapes", "kBrdBarTags"),
                             ("blackrock-depths-shapes-2", "kBrd2BarTags"),
                             ("scarlet-monastery-shapes", "kSmBarTags"),
                             ("scarlet-monastery-shapes-2", "kSm2BarTags"),
                             ("ragefire-chasm-shapes", "kRfcBarTags")):
            self.assertEqual(set(ms.DRILL_BARS[drill]["gated"]), self.array(array), drill)
        self.assertEqual(set(ms.DRILL_BARS["blackrock-depths-shapes-2"]["group"]), self.array("kBrd2GroupTags"))
        self.assertEqual(set(ms.DRILL_BARS["scarlet-monastery-shapes"]["group"]), self.array("kSmGroupTags"))
        self.assertEqual(set(ms.DRILL_BARS["scarlet-monastery-shapes"]["references"]),
                         self.array("kSmReferenceTags"))
        self.assertEqual(set(ms.DRILL_BARS["scarlet-monastery-shapes-2"]["group"]), self.array("kSm2GroupTags"))
        self.assertEqual(set(ms.DRILL_BARS["scarlet-monastery-shapes-2"]["references"]),
                         self.array("kSm2ReferenceTags"))
        self.assertEqual(set(ms.DRILL_BARS["ragefire-chasm-shapes"]["group"]), self.array("kRfcGroupTags"))
        self.assertEqual(set(ms.DRILL_BARS["ragefire-chasm-shapes"]["references"]), self.array("kRfcReferenceTags"))

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
            # a mound's eruption counts under its tag + 1 (MoundEruptTag)
            used |= {int(t) + 1 for t in re.findall(r"\bmound [^;]*?\btag=(\d+)", block)}
            known = set(bar["gated"]) | bar["reported"] | set(bar["group"])
            self.assertEqual(used - known, set(), name)
        self.assertEqual(seen, set(ms.DRILL_BARS))


if __name__ == "__main__":
    unittest.main()
