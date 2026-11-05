#!/usr/bin/env python3
"""Builds the reference health gear lists, profiles and manifest (dungeon difficulties E3, WP-3G).

Reference health (boss rules section 4, handoff section 3.7) is a character sheet's max health at a row's gear.
Max health depends on the class, level, race and the gear's Stamina and Health stats only, so a refhealth profile
is a minimal profile: Class, Gear, no talents, no flat stats. This tool picks that gear.

Rows (keys used in file names and the manifest):
  n20  level 20 normal      blues of item level 12-30, required level 20 or less (greens fill slots without a blue)
  n60  level 60 normal      the Gear line of the class's normalized DPS / tank sim profile (item level 55-65 blues)
  h60  level 60 heroic      item level 66 (tier 1); band 60-71 when a slot has no 66 item
  e1   empowered 1          item level 76 (tier 2); band 70-81
  e2   empowered 2          item level 86-92 (AQ40 and classic tier 3 pieces are 86-92); band 80-92
  (empowered 3 is extrapolated by tools/refhealth.py from e1 -> e2 and has no gear until item variants exist)

Each class has one DPS profile and, where a tank profile exists, one tank profile. The slot shape (armor type, weapon
kind, ranged type) comes from the class's n60 sim profile, so a row differs from n60 only in item level. Per slot the
tool takes the highest scoring item of the band: DPS score = primary stat + Stamina (+ weapon DPS); tank score =
2 x Stamina + primary / 2 (+ weapon DPS). Items with random properties, a honor rank or skill requirement, custom ids
(above 56806) and scaling stats are skipped.

Reads the world DB through `docker exec ... mysql` (read-only SELECT). Writes conf/profiles/refhealth/*.conf, gear.tsv,
manifest.json. Usage: refhealth_gear.py [--write] [--mysql "<command>"]   (without --write it only prints the picks)
"""

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = os.path.dirname(HERE)
PROFILES = os.path.join(MODULE, "conf", "profiles")
OUT_DIR = os.path.join(PROFILES, "refhealth")
DEFAULT_MYSQL = "docker exec d4359d4b8cbb_ac-database mysql -uroot -ppassword acore_world -B -N"

CLASS_NAMES = {1: "Warrior", 2: "Paladin", 3: "Hunter", 4: "Rogue", 5: "Priest", 6: "DeathKnight", 7: "Shaman",
               8: "Mage", 9: "Warlock", 11: "Druid"}

# class -> role -> (base sim profile, race, primary stat). Races are the ones the base profiles are run with (a hunter
# cannot be Human, a druid either); the primary stat is ITEM_MOD_STRENGTH 4, AGILITY 3 or INTELLECT 5.
SETUPS = {
    1: {"dps": ("ArmsWarriorSim", 1, 4), "tank": ("ProtWarriorTankSim", 1, 4)},
    2: {"dps": ("RetPaladinSim", 1, 4), "tank": ("ProtPaladinTankSim", 1, 4)},
    3: {"dps": ("BmHunterSim", 6, 3)},
    4: {"dps": ("CombatRogueSim", 2, 3), "tank": ("CombatRogueTankSim", 2, 3)},
    5: {"dps": ("ShadowPriestSim", 8, 5)},
    6: {"dps": ("FrostDk2hSim", 1, 4), "tank": ("BloodDkTankSim", 1, 4)},
    7: {"dps": ("ShamanEleSim", 2, 5), "tank": ("EnhShamanTankSim", 2, 3)},
    8: {"dps": ("FrostMageSim", 8, 5)},
    9: {"dps": ("DestructionWarlockSim", 2, 5)},
    11: {"dps": ("FeralCatSim", 6, 3), "tank": ("BearTankSim", 6, 3)},
}

ROWS = ["n20", "n60", "h60", "e1", "e2"]
ROW_LEVEL = {"n20": 20, "n60": 60, "h60": 60, "e1": 60, "e2": 60}
# item level bands tried in order for a slot; n20 is by required level instead
ROW_BANDS = {"h60": [(66, 66), (60, 71)], "e1": [(76, 76), (70, 81)], "e2": [(86, 92), (80, 92)]}
ROW_TEXT = {
    "n20": "level 20 normal: blues of item level 12-30, required level 20 or less, greens where no blue fits",
    "n60": "level 60 normal: the base sim profile's Gear line (item level 55-65 blues)",
    "h60": "level 60 heroic: tier 1, item level 66",
    "e1": "empowered 1: tier 2, item level 76",
    "e2": "empowered 2: AQ40 and classic tier 3, item level 86-92",
}

INV_GROUP = {1: "head", 2: "neck", 3: "shoulder", 5: "chest", 20: "chest", 6: "waist", 7: "legs", 8: "feet", 9: "wrist",
             10: "hands", 11: "finger", 16: "back", 13: "1h", 21: "1h", 22: "1h", 17: "2h", 14: "shield",
             23: "holdable", 15: "ranged", 26: "ranged", 25: "ranged", 28: "relic"}
ARMOR_SLOTS = {"head", "shoulder", "chest", "waist", "legs", "feet", "wrist", "hands"}
# armor subclass worn per class: cloth 1, leather 2, mail 3, plate 4. At level 20 a warrior and a paladin wear mail
# (plate comes at 40), a hunter and a shaman leather (mail comes at 40); a death knight is never level 20.
ARMOR_AT_60 = {1: 4, 2: 4, 3: 3, 4: 2, 5: 1, 6: 4, 7: 3, 8: 1, 9: 1, 11: 2}
ARMOR_AT_20 = {1: 3, 2: 3, 3: 2, 4: 2, 5: 1, 7: 2, 8: 1, 9: 1, 11: 2}
RANGED_WEAPONS = (2, 3, 16, 18)     # bow, gun, thrown, crossbow
WAND = 19
STAT_STAMINA, STAT_HEALTH = 7, 1
DUAL_WIELD_AT_START = {4, 6}

COLS = ("entry name class subclass InventoryType ItemLevel Quality RequiredLevel AllowableClass AllowableRace "
        "RequiredSkill requiredspell requiredhonorrank RandomProperty RandomSuffix ScalingStatDistribution "
        "dmg_min1 dmg_max1 delay " + " ".join(f"stat_type{i} stat_value{i}" for i in range(1, 11))).split()


def mysql_rows(command, sql):
    out = subprocess.run(command.split() + ["-e", sql], check=True, capture_output=True, text=True).stdout
    return [line.split("\t") for line in out.splitlines() if line]


def to_item(cols):
    raw = dict(zip(COLS, cols))
    item = {}
    for key, value in raw.items():
        if key == "name":
            item[key] = value
        else:
            try:
                item[key] = int(value)
            except ValueError:
                item[key] = float(value)
    item["stats"] = {}
    for i in range(1, 11):
        stat_type, value = item[f"stat_type{i}"], item[f"stat_value{i}"]
        if stat_type or value:
            item["stats"][stat_type] = item["stats"].get(stat_type, 0) + value
    delay = item["delay"]
    item["wdps"] = (item["dmg_min1"] + item["dmg_max1"]) / 2 / (delay / 1000) if delay else 0.0
    item["group"] = INV_GROUP.get(item["InventoryType"])
    return item


def load_items(command):
    sql = (f"select {','.join(COLS)} from item_template where class in (2, 4) and Quality >= 2 "
           "and ItemLevel between 10 and 110 and entry <= 56806")
    return {item["entry"]: item for item in (to_item(r) for r in mysql_rows(command, sql))}


def load_base_items(command, ids):
    sql = f"select {','.join(COLS)} from item_template where entry in ({','.join(str(i) for i in ids)})"
    return {item["entry"]: item for item in (to_item(r) for r in mysql_rows(command, sql))}


def profile_gear(name):
    path = os.path.join(PROFILES, name + ".conf")
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            match = re.match(r"\s*Gear\s*=\s*([0-9, ]+)", line)
            if match:
                return [int(x) for x in match.group(1).replace(" ", "").split(",") if x]
    raise SystemExit(f"{path}: no Gear line")


def usable(item, cls, race, level):
    allow_class, allow_race = item["AllowableClass"], item["AllowableRace"]
    if allow_class > 0 and not allow_class & (1 << (cls - 1)):
        return False
    if allow_race > 0 and not allow_race & (1 << (race - 1)):
        return False
    return (item["RequiredLevel"] <= level and item["RequiredSkill"] == 0 and item["requiredspell"] == 0
            and item["requiredhonorrank"] == 0 and item["RandomProperty"] == 0 and item["RandomSuffix"] == 0
            and item["ScalingStatDistribution"] == 0 and item["group"] is not None
            and not re.search(r"\b(test|deprecated|monster|qa|unused)\b", item["name"], re.I))


def score(item, role, primary):
    stamina = item["stats"].get(STAT_STAMINA, 0) + item["stats"].get(STAT_HEALTH, 0) / 10
    main = item["stats"].get(primary, 0)
    value = (2 * stamina + main / 2) if role == "tank" else (main + stamina)
    return value + item["wdps"]


def candidates(pool, base, cls, race, level, row, taken, weapon_index):
    group, subclass = base["group"], base["subclass"]
    result = []
    for item in pool:
        if item["entry"] in taken or not usable(item, cls, race, level):
            continue
        if group == "1h":
            # the first one-hand weapon is a main hand, a second one an off-hand
            if item["group"] != "1h" or item["class"] != 2:
                continue
            allowed = (13, 21) if weapon_index == 0 else (13, 22)
            if item["InventoryType"] not in allowed:
                continue
        elif item["group"] != group:
            continue
        elif group in ARMOR_SLOTS:
            want = ARMOR_AT_20[cls] if row == "n20" else ARMOR_AT_60[cls]
            if item["class"] != 4 or item["subclass"] != want:
                continue
        elif group == "back":
            if item["class"] != 4 or item["subclass"] != 1:
                continue
        elif group in ("neck", "finger", "holdable"):
            if item["class"] != 4 or item["subclass"] != 0:
                continue
        elif group == "shield":
            if item["class"] != 4 or item["subclass"] != 6:
                continue
        elif group == "ranged":
            if item["class"] != 2 or (item["subclass"] == WAND) != (subclass == WAND) or (
                    subclass != WAND and item["subclass"] not in RANGED_WEAPONS):
                continue
        elif group == "relic":
            if item["class"] != base["class"] or item["subclass"] != subclass:
                continue
        elif group == "2h":
            if item["class"] != 2:
                continue
        result.append(item)
    return result


def pick_row(pool, bases, cls, race, row, role, primary):
    """Picks the gear of one row. Returns (entries, notes)."""
    level = ROW_LEVEL[row]
    taken, picks, notes = set(), [], []
    weapon_index = 0
    for base in bases:
        group = base["group"]
        best, how = None, ""
        if row == "n20":
            tiers = [("blue", [i for i in pool if i["Quality"] == 3 and 12 <= i["ItemLevel"] <= 30]),
                     ("green", [i for i in pool if i["Quality"] == 2 and 12 <= i["ItemLevel"] <= 30])]
        else:
            tiers = [(f"ilvl {lo}-{hi}" if lo != hi else f"ilvl {lo}",
                      [i for i in pool if lo <= i["ItemLevel"] <= hi and i["Quality"] >= 3])
                     for lo, hi in ROW_BANDS[row]]
        for label, sub in tiers:
            found = candidates(sub, base, cls, race, level, row, taken, weapon_index)
            if found:
                best = max(found, key=lambda i: (score(i, role, primary), -i["entry"]))
                how = label
                break
        if group == "1h":
            weapon_index += 1
        if best is None:
            notes.append(f"{group} ({base['name']}): no item, slot left empty")
            continue
        taken.add(best["entry"])
        picks.append(best)
        if how not in ("blue", "ilvl 66", "ilvl 76", "ilvl 86-92"):
            notes.append(f"{group} {best['entry']} {best['name']}: fallback {how}")
    return picks, notes


def build(command):
    pool_all = list(load_items(command).values())
    result = {}
    for cls, roles in SETUPS.items():
        for role, (base_name, race, primary) in roles.items():
            base_ids = profile_gear(base_name)
            base_map = load_base_items(command, base_ids)
            bases = [base_map[i] for i in base_ids]
            entry = {"class": cls, "role": role, "base": base_name, "race": race, "rows": {}}
            second_weapons = [b for b in bases if b["group"] == "1h"]
            entry["deferred_offhand"] = len(second_weapons) > 1 and cls not in DUAL_WIELD_AT_START
            for row in ROWS:
                if row == "n60":
                    picks, notes = [base_map[i] for i in base_ids], []
                elif row == "n20" and cls == 6:
                    continue   # a death knight is never level 20
                else:
                    picks, notes = pick_row(pool_all, bases, cls, race, row, role, primary)
                entry["rows"][row] = {"gear": [p["entry"] for p in picks], "notes": notes,
                                      "items": [{"entry": p["entry"], "name": p["name"], "ilvl": p["ItemLevel"],
                                                 "slot": p["group"], "stamina": p["stats"].get(STAT_STAMINA, 0),
                                                 "primary": p["stats"].get(primary, 0)} for p in picks]}
            result[(cls, role)] = entry
    return result


def profile_text(entry, row, name):
    cls = entry["class"]
    gear = ",".join(str(i) for i in entry["rows"][row]["gear"])
    lines = [
        "#",
        f"# DpsSim profile: {name}",
        "#",
        "# Reference health profile (dungeon difficulties E3). tools/refhealth_gear.py writes it; do not edit by hand.",
        f"# {CLASS_NAMES[cls]} {entry['role']}, row {row} ({ROW_TEXT[row]}).",
        "# Only the character sheet matters: max health depends on class, level, race and the gear's Stamina, and the",
        "# sim logs the sheet (\"SimActor sheet ... max health\") before talents and buffs: no talents, no flat stats,",
        "# no pre-pull buff phase.",
        f"# Run: DPSSIM_KEEP_LOG=1 modules/mod-dpssim/tools/run-sim.sh {name} 5 {ROW_LEVEL[row]} {entry['race']} 1",
        "#",
        f"Class = {cls}",
        "PlayerbotGlyphs = false",
        "PrePullBuffMs = 0",
        "StatWeightsEnabled = false",
        f"Gear = {gear}",
        "",
    ]
    return "\n".join(lines)


def profile_name(entry, row):
    return f"RefHealth_{CLASS_NAMES[entry['class']]}_{entry['role']}_{row}"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="write the profiles, gear.tsv and manifest.json")
    parser.add_argument("--mysql", default=DEFAULT_MYSQL, help="command that runs mysql against the world DB, -B -N")
    args = parser.parse_args()

    built = build(args.mysql)
    manifest = {"rows": ROWS, "row_text": ROW_TEXT, "profiles": []}
    tsv = ["profile\trow\tslot\tentry\tname\titem level\tstamina\tprimary"]
    for (cls, role), entry in sorted(built.items()):
        for row, data in entry["rows"].items():
            name = profile_name(entry, row)
            manifest["profiles"].append({
                "name": name, "class": cls, "class_name": CLASS_NAMES[cls], "role": role, "row": row,
                "level": ROW_LEVEL[row], "race": entry["race"], "base": entry["base"], "gear": data["gear"],
                "deferred_offhand": entry["deferred_offhand"]})
            for item in data["items"]:
                tsv.append(f"{name}\t{row}\t{item['slot']}\t{item['entry']}\t{item['name']}\t{item['ilvl']}\t"
                           f"{item['stamina']}\t{item['primary']}")
            total = sum(i["stamina"] for i in data["items"])
            print(f"{name}: {len(data['gear'])} items, item stamina {total}"
                  + ("  [off-hand equipped after the sheet line]" if entry["deferred_offhand"] else ""))
            for note in data["notes"]:
                print(f"    {note}")
            if args.write:
                with open(os.path.join(OUT_DIR, name + ".conf"), "w", encoding="utf-8", newline="\n") as handle:
                    handle.write(profile_text(entry, row, name))
    if args.write:
        with open(os.path.join(OUT_DIR, "gear.tsv"), "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(tsv) + "\n")
        with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, indent=2)
            handle.write("\n")
        print(f"wrote {len(manifest['profiles'])} profiles to {OUT_DIR}")


if __name__ == "__main__":
    sys.exit(main())
