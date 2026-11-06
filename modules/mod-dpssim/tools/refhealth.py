#!/usr/bin/env python3
"""Reference health: run plan, aggregation and consistency check (dungeon difficulties E3, WP-3G).

Reference health is the character sheet's max health at each row's reference gear (boss rules section 4, handoff
section 3.7). tools/refhealth_gear.py writes the profiles under conf/profiles/refhealth/ and manifest.json. This tool:

  plan       prints the run-sim.sh command lines (one sim per profile, 5 s x 1 iteration, kept log), for xargs -P 6
  aggregate  reads the kept run logs (reports/<profile>.<timestamp>.run.log, newest per profile), takes max health from
             the "SimActor sheet" line, and prints the table per row (median, min, max, spread of the non-tank and tank
             profiles), the extrapolated empowered 3 row and the BossMechanics.ReferenceHealth.Rows string
  check      verifies the profile files against the manifest and the n60 rows against the base sim profiles' Gear lines

The number: SimActor::Create() logs "SimActor sheet - '<name>': ... max health <N>, max mana <M>." after
the gear is worn (and the synthetic stats and ratings applied) and before SimBot::Create() spends talents, runs the
stance or the pre-pull buff phase. It is the unbuffed sheet. Gear a class can only wear after its Dual Wield is taught
(an off-hand weapon of a warrior, hunter, shaman or paladin) is worn after that line; the manifest flags those profiles.

Empowered 3 has no gear until item variants exist: it is e2 + (e2 - e1) per role.
"""

import argparse
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = os.path.dirname(HERE)
REFHEALTH_DIR = os.path.join(MODULE, "conf", "profiles", "refhealth")
PROFILES_DIR = os.path.join(MODULE, "conf", "profiles")
MANIFEST = os.path.join(REFHEALTH_DIR, "manifest.json")
DEFAULT_REPORTS = os.path.join(MODULE, "reports")

# row -> BossMechanics.ReferenceHealth.Rows key (module read format, handoff section 3.7)
ROW_KEY = {"n20": "20", "n60": "60", "h60": "60h", "e1": "60e1", "e2": "60e2", "e3": "60e3"}
ROW_ORDER = ["n20", "n60", "h60", "e1", "e2", "e3"]
ROW_TITLE = {
    "n20": "Level 20 normal", "n60": "Level 60 normal", "h60": "Level 60 heroic (item level 66)",
    "e1": "Empowered 1 (item level 76)", "e2": "Empowered 2 (item level 86-92)",
    "e3": "Empowered 3 (extrapolated)",
}

ANSI = re.compile(r"\x1b\[[0-9;]*m")
SHEET = re.compile(r"SimActor sheet - '([^']*)':.*?max health (\d+), max mana (\d+)")
CREATED = re.compile(r"SimActor created - '([^']*)' \(race (\d+), class (\d+), level (\d+)\)")
EQUIP_FAIL = re.compile(r"(could not equip item \d+[^\n]*|gear item \d+ does not exist)")


def load_manifest(path=MANIFEST):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def find_log(reports_dir, name):
    """The newest kept run log of a profile: <name>.<yyyymmdd-hhmmss>.run.log (names are unique per profile)."""
    pattern = re.compile(re.escape(name) + r"\.(\d{8}-\d{6})\.run\.log$")
    best = None
    for entry in os.listdir(reports_dir):
        match = pattern.match(entry)
        if match and (best is None or match.group(1) > best[0]):
            best = (match.group(1), os.path.join(reports_dir, entry))
    return best[1] if best else None


def read_log(path):
    """Returns {'health': int|None, 'mana': int, 'created': tuple|None, 'sheets': [healths], 'problems': [str]}."""
    result = {"health": None, "mana": None, "created": None, "sheets": [], "problems": []}
    with open(path, encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = ANSI.sub("", raw)
            sheet = SHEET.search(line)
            if sheet:
                result["sheets"].append(int(sheet.group(2)))
                if result["health"] is None:
                    result["health"], result["mana"] = int(sheet.group(2)), int(sheet.group(3))
            created = CREATED.search(line)
            if created and result["created"] is None:
                result["created"] = tuple(int(created.group(i)) for i in (2, 3, 4))   # race, class, level
            fail = EQUIP_FAIL.search(line)
            if fail:
                result["problems"].append(fail.group(1).strip())
    if len(set(result["sheets"])) > 1:
        result["problems"].append(f"{len(result['sheets'])} sheet lines with different max health {result['sheets']}")
    return result


def collect(manifest, reports_dir):
    """Reads the newest log of every manifest profile. Returns (measurements, problems)."""
    measurements, problems = {}, []
    for profile in manifest["profiles"]:
        name = profile["name"]
        log = find_log(reports_dir, name)
        if log is None:
            problems.append(f"{name}: no kept run log in {reports_dir}")
            continue
        data = read_log(log)
        for text in data["problems"]:
            problems.append(f"{name}: {text}")
        if data["health"] is None:
            problems.append(f"{name}: no 'SimActor sheet' line in {os.path.basename(log)}")
            continue
        if data["created"] is not None and data["created"] != (profile["race"], profile["class"], profile["level"]):
            problems.append(f"{name}: ran as race/class/level {data['created']}, manifest says "
                            f"{(profile['race'], profile['class'], profile['level'])}")
        measurements[name] = data["health"]
    return measurements, problems


def role_stats(values):
    ordered = sorted(values)
    median = statistics.median(ordered)
    return {"n": len(ordered), "median": median, "min": ordered[0], "max": ordered[-1],
            "spread_pct": (ordered[-1] - ordered[0]) / median * 100 if median else 0.0}


def aggregate(manifest, measurements, rounding=1):
    """rows[row][role] = stats + 'by_class'; e3 is extrapolated from e1 and e2 per role (median based)."""
    rows = {}
    for row in manifest["rows"]:
        rows[row] = {}
        for role in ("dps", "tank"):
            by_class = {p["class_name"]: measurements[p["name"]] for p in manifest["profiles"]
                        if p["row"] == row and p["role"] == role and p["name"] in measurements}
            if by_class:
                stats = role_stats(list(by_class.values()))
                stats["by_class"] = by_class
                rows[row][role] = stats
    if "e1" in rows and "e2" in rows:
        rows["e3"] = {}
        for role in ("dps", "tank"):
            if role in rows["e1"] and role in rows["e2"]:
                median = 2 * rows["e2"][role]["median"] - rows["e1"][role]["median"]
                rows["e3"][role] = {"n": 0, "median": median, "min": None, "max": None, "spread_pct": None,
                                    "by_class": {}}
    for row_roles in rows.values():
        for stats in row_roles.values():
            stats["value"] = int(round(stats["median"] / rounding)) * rounding
    return rows


def rows_string(rows):
    parts = []
    for row in ROW_ORDER:
        roles = rows.get(row, {})
        if "dps" in roles and "tank" in roles:
            parts.append(f"{ROW_KEY[row]}:{roles['dps']['value']}:{roles['tank']['value']}")
    return " ".join(parts)


def format_report(rows, problems):
    lines = ["Reference health (max health of the unbuffed character sheet)", ""]
    header = f"{'Row':<34}{'non-tank':>10}{'tank':>8}   {'DPS min-max (spread, n)':<28}{'tank min-max (spread, n)':<28}"
    lines += [header, "-" * len(header)]

    def span(stats):
        if stats is None:
            return "-"
        if stats["min"] is None:
            return "extrapolated"
        return f"{stats['min']}-{stats['max']} ({stats['spread_pct']:.0f}%, {stats['n']})"

    for row in ROW_ORDER:
        roles = rows.get(row)
        if not roles:
            continue
        dps, tank = roles.get("dps"), roles.get("tank")
        lines.append(f"{ROW_TITLE[row]:<34}{(dps['value'] if dps else '-'):>10}{(tank['value'] if tank else '-'):>8}   "
                     f"{span(dps):<28}{span(tank):<28}")
    lines += ["", "Per class:"]
    classes = sorted({c for roles in rows.values() for stats in roles.values() for c in stats["by_class"]})
    for role in ("dps", "tank"):
        lines.append(f"  {role}")
        lines.append("    " + f"{'class':<13}" + "".join(f"{r:>7}" for r in ROW_ORDER if r in rows and r != "e3"))
        for cls in classes:
            cells = [rows[r].get(role, {}).get("by_class", {}).get(cls) for r in ROW_ORDER if r in rows and r != "e3"]
            if any(c is not None for c in cells):
                lines.append("    " + f"{cls:<13}" + "".join(f"{(c if c is not None else '-'):>7}" for c in cells))
    lines += ["", "BossMechanics.ReferenceHealth.Rows = \"" + rows_string(rows) + "\""]
    if problems:
        lines += ["", "Problems:"] + [f"  {p}" for p in problems]
    return "\n".join(lines)


def cmd_plan(args):
    manifest = load_manifest()
    reports = os.path.relpath(DEFAULT_REPORTS, os.path.dirname(os.path.dirname(MODULE)))
    commands = []
    for profile in manifest["profiles"]:
        if args.row and profile["row"] not in args.row:
            continue
        commands.append(
            f"DPSSIM_KEEP_LOG=1 DPSSIM_NO_HTML=1 modules/mod-dpssim/tools/run-sim.sh "
            f"modules/mod-dpssim/conf/profiles/refhealth/{profile['name']}.conf {args.duration} {profile['level']} "
            f"{profile['race']} 1")
    print(f"# {len(commands)} sims; from the repo root, at most 6 at once. Kept logs land in {reports}/")
    if args.xargs:
        print("# one command per line: pipe through `xargs -P 6 -I{} bash -c '{}'`")
    for command in commands:
        print(command)
    return 0


def cmd_aggregate(args):
    manifest = load_manifest(args.manifest)
    measurements, problems = collect(manifest, args.reports)
    rows = aggregate(manifest, measurements, args.round)
    print(format_report(rows, problems))
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
            json.dump({"rows": rows, "rows_string": rows_string(rows), "measurements": measurements,
                       "problems": problems}, handle, indent=2, default=float)
            handle.write("\n")
    return 1 if problems else 0


def cmd_check(args):
    manifest = load_manifest(args.manifest)
    errors = []
    for profile in manifest["profiles"]:
        path = os.path.join(os.path.dirname(args.manifest), profile["name"] + ".conf")
        if not os.path.isfile(path):
            errors.append(f"missing profile file {path}")
            continue
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        gear = re.search(r"^Gear\s*=\s*([0-9,]+)", text, re.M)
        if not gear or [int(x) for x in gear.group(1).split(",")] != profile["gear"]:
            errors.append(f"{profile['name']}: Gear line differs from the manifest")
        if not re.search(rf"^Class\s*=\s*{profile['class']}\s*$", text, re.M):
            errors.append(f"{profile['name']}: Class differs from the manifest")
        if profile["row"] == "n60":
            base = os.path.join(args.profiles, profile["base"] + ".conf")
            with open(base, encoding="utf-8") as handle:
                base_gear = re.search(r"^Gear\s*=\s*([0-9, ]+)", handle.read(), re.M)
            ids = [int(x) for x in base_gear.group(1).replace(" ", "").split(",") if x] if base_gear else None
            if ids != profile["gear"]:
                errors.append(f"{profile['name']}: the base profile {profile['base']} Gear changed since the manifest "
                              f"was built; rerun tools/refhealth_gear.py --write")
    listed = {p["name"] + ".conf" for p in manifest["profiles"]}
    for entry in sorted(os.listdir(os.path.dirname(args.manifest))):
        if entry.startswith("RefHealth_") and entry.endswith(".conf") and entry not in listed:
            errors.append(f"{entry} is not in the manifest")
    for error in errors:
        print("ERROR:", error)
    print(f"checked {len(manifest['profiles'])} profiles: {'OK' if not errors else str(len(errors)) + ' error(s)'}")
    return 1 if errors else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="print the run-sim.sh command lines")
    plan.add_argument("--duration", type=int, default=5, help="simulated seconds per run (default 5)")
    plan.add_argument("--row", action="append", choices=["n20", "n60", "h60", "e1", "e2"],
                      help="only these rows (repeatable), e.g. --row n20 for the level 20 smoke")
    plan.add_argument("--xargs", action="store_true", help="print the xargs hint")
    plan.set_defaults(func=cmd_plan)

    agg = sub.add_parser("aggregate", help="read the kept run logs and print the table")
    agg.add_argument("--reports", default=DEFAULT_REPORTS, help="directory holding the kept run logs")
    agg.add_argument("--manifest", default=MANIFEST)
    agg.add_argument("--round", type=int, default=1, help="round the medians to a multiple of N (default 1)")
    agg.add_argument("--json", help="also write the result as JSON")
    agg.set_defaults(func=cmd_aggregate)

    check = sub.add_parser("check", help="verify profiles against the manifest and the base sim profiles")
    check.add_argument("--manifest", default=MANIFEST)
    check.add_argument("--profiles", default=PROFILES_DIR)
    check.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
