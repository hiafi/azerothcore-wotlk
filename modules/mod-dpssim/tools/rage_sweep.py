#!/usr/bin/env python3
"""
Rage sweep for the Warrior rework (stage W0a, decisions D12-D17 in
.agents/plans/warrior-rework/warrior-rework.W0a-HANDOFF.md): reads the white swings out of the four
WarriorRage{2H,Dw}{Start,End}Sim reports and works out, per profile, the rage per second the STOCK rage formula
gives and the rage per second the DAMPENED formula (D12) gives for a pair of constants k and m. It then prints
what the user needs to pick the level-60 constants:

  1. a SOURCE table per profile (white hits, crits, mean damage, measured swing speed against the weapon's base
     speed, i.e. the haste the gear gave),
  2. the RAW rage-per-second tables for the k and m given by --k / --m (default: the constants in
     src/server/game/Entities/Unit/Generated/WarriorData.h when that file is found, else 0.43 and 1.8),
  3. D15's suggested solve for k and m (a SUGGESTION only: the user picks k and m),
  4. the dual-wield advantage, stock against the new formula (the doc says "about halved"),
  5. the 15% haste check (haste-neutral speed part),
  6. D16's Arms budget table (white-swing income plus Anger Management 3 against the Arms rotation's spend).

The formula (D12, mirrored in src/server/game/Entities/Unit/WarriorMechanics.cpp):
    c(L)      = 0.0091107836 L^2 + 3.225598133 L + 4.2652911          (+13.27 per level above 70)
    stock     : f = int(unhasted swing * 3.5)  main hand, int(unhasted swing * 1.75) off hand
                dealt = (7.5 d / c + f) / 2, capped at 2 * 7.5 d / c, x rate
    new       : speed = lround(hasted swing * 3.5 * m * 100) main hand, lround(hasted swing * 0.875 * 100) off hand
                (hundredths); both are doubled on a crit, like the stock factor
                dealt = (k * 7.5 d / c + speed / 100) / 2, capped at the STOCK cap 15 d / c, then x 1.10 in Battle
                Stance (aura 213), then x rate
A new hit's damage d is the report's "damage" (the dummy has no absorb, so damage + absorbed is the same number).

WHAT THE REPORT CAN AND CANNOT TELL US (find: SimReport.h / EventRecorder.h):
  - A white swing is a "hits" row with spellId 0 (EventRecorder::MELEE_SPELL_ID), isPet false, sourceEntry 0:
    {timestampMs, spellId, damage, crit, isPet, sourceEntry, target}. There is NO main-hand / off-hand tag and no
    swing speed in the report, and a swing that missed or was dodged leaves no row at all (PvE is always-hit here).
  - The aggregate report keeps "hits" only from ONE representative iteration (the per-spell "spells" row has the
    averaged hitCount / critCount / totalDamage but no hands). So this script reads the per-iteration files
    (<stamp>.iterN.report.json, written next to the aggregate by run-sim.sh) whenever they exist and falls back to
    the aggregate's single run with a note (--aggregate-only forces that).
  - Hands: a two-hander has only the main hand. For dual wield the script splits the white swings into two clusters
    of crit-normalised damage (1-D 2-means; the off hand hits for about half the main hand) and calls the lower
    cluster the off hand. It warns when the clusters are not clearly apart or when the counts do not match the swing
    speeds. A hand tag in the report would remove this guess (C++ change, not done: out of this tool's scope).
  - Swing speed: the mean gap between one hand's consecutive hits in the run (the hasted swing time the new formula
    uses, exact on average even when Flurry-style haste comes and goes). The UNHASTED weapon speed the stock formula
    uses is not in the report either: it is a per-profile default below (the reference weapons of the four
    profiles), overridable with --speed.

Usage:
    python3 -I tools/rage_sweep.py [--2h-start SRC] [--2h-end SRC] [--dw-start SRC] [--dw-end SRC]
                                   [--k 0.43] [--m 1.8] [--rate 1.0] [--level 60] [--crit-mult 2.0]
                                   [--header PATH] [--speed KEY=MH[/OH]] [--stance KEY=battle|berserker]
                                   [--aggregate-only] [--reports-dir DIR]
    python3 -I tools/rage_sweep.py --self-test

SRC (a profile whose SRC is omitted is looked up in the reports dir: the newest <Profile>.<stamp>.report.json):
    a *.report.json aggregate (its sibling *.iterN.report.json are used when present), a stamp prefix such as
    reports/WarriorRage2HStartSim.20261030-120000, or a glob. Any subset of the four profiles works; the solve
    needs 2h-start and 2h-end, the dual-wield advantage needs all four, the Arms budget needs a 2h profile.
KEY is 2h-start, 2h-end, dw-start or dw-end.

Exit status: 0 ok, 1 usage / missing data, 2 the D15 solve is not usable (k <= 0 or m <= 0, or a singular system:
REPORT AND STOP, nothing is suggested), 3 self-test failure.

Stdlib only; run with `python3 -I`.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import re
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ----------------------------------------------------------------------------------------------------------------
# Constants (defaults mirror WarriorData.h; the header overrides them when it is found)
# ----------------------------------------------------------------------------------------------------------------

DEFAULT_K = 0.43
DEFAULT_M = 1.8
MH_SPEED_FACTOR = 3.5          # WarriorData::RAGE_MH_SPEED_FACTOR
OH_SPEED_FACTOR = 0.875        # WarriorData::RAGE_OH_SPEED_FACTOR
SPEED_FIXED_POINT = 100        # WarriorData::RAGE_SPEED_FIXED_POINT
STOCK_MH_FACTOR = 3.5          # Unit::GetRageWeaponSpeedHitFactor, main hand
STOCK_OH_FACTOR = 1.75         # ... off hand
BATTLE_STANCE_PCT = 10.0       # aura 213 (MOD_RAGE_FROM_DAMAGE_DEALT) on Battle Stance 2457
LEVEL = 60
CRIT_MULT = 2.0                # physical crit damage multiplier, used only to normalise damage for the hand split
HASTE_CHECK = 0.15             # D15: "15% haste"
GROWTH_TARGET = 1.25           # D15 (b): the doc's "about 25% more rage per second than at its start"

HEADER_NAMES = {
    "RAGE_K_60": "k",
    "RAGE_M_60": "m",
    "RAGE_MH_SPEED_FACTOR": "mh",
    "RAGE_OH_SPEED_FACTOR": "oh",
    "RAGE_SPEED_FIXED_POINT": "fp",
}

# The four sweep profiles: key -> (profile name, hands, default stance, default unhasted weapon speeds MH / OH).
# Speeds are the reference weapons of the profiles (see each conf's header).
PROFILES = {
    "2h-start": ("WarriorRage2HStartSim", 1, "battle", 3.6, None),     # Seeping Willow 12969
    "2h-end": ("WarriorRage2HEndSim", 1, "battle", 3.7, None),         # Barb of the Sand Reaver 21635
    # Willey's Back Scratcher 22404 + Skullforge Reaver 13361
    "dw-start": ("WarriorRageDwStartSim", 2, "berserker", 2.6, 2.5),
    # Sand Polished Hammer 21715 + Ancient Qiraji Ripper 21650
    "dw-end": ("WarriorRageDwEndSim", 2, "berserker", 2.6, 2.8),
}

# D16: Arms rotation spend per minute (docs/reworks/warrior-arms-rework.md section 9, "About 40 presses a minute at
# 0 haste") x rage cost, and Anger Management rank 3 (2/4/6 rage per 3 sec: 6 x 20 = 120 a minute).
ARMS_SPEND = [
    ("Mortal Strike", 12, 30),
    ("Overpower", 12, 5),
    ("Slam", 10, 15),
    ("Colossus Smash", 4, 20),
    ("Rend", 2, 10),
]
ANGER_MANAGEMENT_3_PER_MIN = 120.0
MORTAL_STRIKE_ALT_COST = 25    # D16's "if short, MS 30 -> 25"


# ----------------------------------------------------------------------------------------------------------------
# The formulas
# ----------------------------------------------------------------------------------------------------------------

def rage_conversion(level: int) -> float:
    """The stock rage conversion c(level) (Unit::RewardRage; Warrior::RageConversion)."""
    c = 0.0091107836 * level * level + 3.225598133 * level + 4.2652911
    if level > 70:
        c += 13.27 * (level - 70)
    return c


def add_pct(value: float, pct: float) -> float:
    return value + value * pct / 100.0


def lround(x: float) -> int:
    """C++ lround: half away from zero."""
    return int(math.floor(x + 0.5)) if x >= 0 else -int(math.floor(-x + 0.5))


def new_speed_fixed(swing_s: float, off_hand: bool, m: float, crit: bool) -> int:
    """Warrior::RageSpeedFactor for a player (hundredths), then the caller's crit doubling."""
    factor = lround(swing_s * (OH_SPEED_FACTOR if off_hand else MH_SPEED_FACTOR * m) * SPEED_FIXED_POINT)
    return factor * 2 if crit else factor


def new_rage_dealt(damage: float, speed_fixed: int, k: float, level: int = LEVEL, battle: bool = False,
                   rate: float = 1.0) -> float:
    """Warrior::RewardRage's dealt branch, in rage (not tenths)."""
    c = rage_conversion(level)
    damage_term = 7.5 * damage / c
    dealt = (k * damage_term + speed_fixed / SPEED_FIXED_POINT) / 2.0
    dealt = min(dealt, 2.0 * damage_term)                 # the STOCK cap, 15 d / c
    if battle:
        dealt = add_pct(dealt, BATTLE_STANCE_PCT)
    return dealt * rate


def stock_factor(unhasted_swing_s: float, off_hand: bool, crit: bool) -> int:
    """Unit::GetRageWeaponSpeedHitFactor (unhasted swing), then the caller's crit doubling."""
    factor = int(unhasted_swing_s * (STOCK_OH_FACTOR if off_hand else STOCK_MH_FACTOR) + 1e-9)
    return factor * 2 if crit else factor


def stock_rage_dealt(damage: float, factor: int, level: int = LEVEL, rate: float = 1.0) -> float:
    """Unit::RewardRage's stock dealt branch (no aura 213 on a stock Battle Stance)."""
    c = rage_conversion(level)
    damage_term = 7.5 * damage / c
    dealt = (damage_term + factor) / 2.0
    dealt = min(dealt, 2.0 * damage_term)
    return dealt * rate


# ----------------------------------------------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------------------------------------------

@dataclass
class Hit:
    damage: float
    crit: bool
    off_hand: bool
    swing_s: float          # the hasted swing time of this hit's hand in this run (mean gap), seconds


@dataclass
class ProfileData:
    key: str
    name: str
    hands: int
    stance: str                        # "battle" | "berserker"
    base_mh: float                     # unhasted weapon speed, seconds
    base_oh: float | None
    duration_s: float = 0.0            # summed over the files
    files: list[str] = field(default_factory=list)
    hits: list[Hit] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def battle(self) -> bool:
        return self.stance == "battle"


def mean_gap_seconds(timestamps_ms: list[int]) -> float | None:
    """Mean spacing of one hand's hits, ignoring gaps over 1.5x the median (a swing that left no row)."""
    ts = sorted(timestamps_ms)
    if len(ts) < 3:
        return None
    gaps = [b - a for a, b in zip(ts, ts[1:]) if b > a]
    if not gaps:
        return None
    med = statistics.median(gaps)
    good = [g for g in gaps if g <= 1.5 * med]
    return (sum(good) / len(good)) / 1000.0


def split_hands(rows: list[dict], crit_mult: float) -> tuple[list[dict], list[dict], list[str]]:
    """Splits dual-wield white swings into (main hand, off hand) rows by crit-normalised damage (1-D 2-means)."""
    notes: list[str] = []
    if len(rows) < 4:
        return rows, [], ["fewer than 4 white swings: cannot split the hands"]
    norm = [r["damage"] / crit_mult if r.get("crit") else float(r["damage"]) for r in rows]
    lo, hi = min(norm), max(norm)
    if hi - lo < 1e-9:
        return rows, [], ["all white swings have the same damage: cannot split the hands"]
    c_lo, c_hi = lo, hi
    for _ in range(100):
        a = [i for i, v in enumerate(norm) if abs(v - c_lo) <= abs(v - c_hi)]
        b = [i for i, v in enumerate(norm) if abs(v - c_lo) > abs(v - c_hi)]
        if not a or not b:
            break
        n_lo, n_hi = sum(norm[i] for i in a) / len(a), sum(norm[i] for i in b) / len(b)
        if abs(n_lo - c_lo) < 1e-9 and abs(n_hi - c_hi) < 1e-9:
            break
        c_lo, c_hi = n_lo, n_hi
    low = [rows[i] for i in range(len(rows)) if abs(norm[i] - c_lo) <= abs(norm[i] - c_hi)]
    high = [rows[i] for i in range(len(rows)) if abs(norm[i] - c_lo) > abs(norm[i] - c_hi)]
    if not low or not high:
        return rows, [], ["could not split the hands (one cluster is empty)"]
    ratio = c_lo / c_hi if c_hi else 1.0
    if ratio > 0.85:
        notes.append(f"WARNING: hand clusters are close (off hand / main hand mean damage {ratio:.2f}); the hand split "
                     f"is unreliable")
    notes.append(f"hand split by damage: main hand mean {c_hi:.1f} ({len(high)} swings), off hand mean {c_lo:.1f} "
                 f"({len(low)} swings), ratio {ratio:.2f}")
    return high, low, notes


def add_report(pd: ProfileData, report: dict, path: str, crit_mult: float) -> None:
    """Adds one report file's white swings to `pd`."""
    cfg = report.get("config", {})
    duration_ms = cfg.get("durationMs")
    if not duration_ms:
        duration_ms = report.get("summary", {}).get("elapsedMs", 0)
    if not duration_ms:
        raise ValueError(f"{path}: no config.durationMs / summary.elapsedMs")
    died = report.get("summary", {}).get("actorDiedAtMs")
    if died:
        pd.notes.append(f"WARNING: {Path(path).name}: the actor died at {died} ms (the rest of the run counts as zero)")
    rows = [h for h in report.get("hits", [])
            if h.get("spellId") == 0 and not h.get("isPet") and not h.get("sourceEntry")]
    if not rows:
        pd.notes.append(f"WARNING: {Path(path).name}: no white swings (spellId 0) in 'hits'")
    if pd.hands == 2:
        mh_rows, oh_rows, notes = split_hands(rows, crit_mult)
        pd.notes.extend(notes if path == pd.files[0] else [])  # the split note once, from the first file
    else:
        mh_rows, oh_rows = rows, []
    for off_hand, hand_rows, base in ((False, mh_rows, pd.base_mh), (True, oh_rows, pd.base_oh)):
        if not hand_rows:
            continue
        swing = mean_gap_seconds([int(r["timestampMs"]) for r in hand_rows])
        if swing is None:
            swing = base if base else 1.0
            pd.notes.append(f"WARNING: {Path(path).name}: too few {'off' if off_hand else 'main'}-hand swings to "
                            f"measure the speed, using the base speed {swing}")
        for r in hand_rows:
            pd.hits.append(Hit(float(r["damage"]), bool(r.get("crit")), off_hand, swing))
    pd.duration_s += duration_ms / 1000.0


def resolve_sources(spec: str | None, profile_name: str, reports_dir: Path, aggregate_only: bool) -> list[Path]:
    """Report files for one profile: explicit SRC, or the newest aggregate of the profile in the reports dir."""
    if spec is None:
        found = sorted(p for p in glob.glob(str(reports_dir / f"{profile_name}.*.report.json"))
                       if ".iter" not in Path(p).name)
        if not found:
            return []
        spec = found[-1]
    if any(ch in spec for ch in "*?["):
        return [Path(p) for p in sorted(glob.glob(spec))]
    p = Path(spec)
    if p.is_file():
        name = p.name
        if name.endswith(".report.json") and ".iter" not in name and not aggregate_only:
            stem = str(p)[:-len(".report.json")]
            iters = sorted(glob.glob(stem + ".iter*.report.json"),
                           key=lambda s: int(re.search(r"\.iter(\d+)\.", s).group(1)))
            if iters:
                return [Path(i) for i in iters]
        return [p]
    iters = sorted(glob.glob(spec + ".iter*.report.json"),
                   key=lambda s: int(re.search(r"\.iter(\d+)\.", s).group(1)))
    if iters and not aggregate_only:
        return [Path(i) for i in iters]
    agg = Path(spec + ".report.json")
    return [agg] if agg.is_file() else []


def load_profile(key: str, files: list[Path], stance: str | None, speeds: tuple[float, float | None] | None,
                 crit_mult: float) -> ProfileData:
    name, hands, def_stance, base_mh, base_oh = PROFILES[key]
    if speeds:
        base_mh, base_oh = speeds[0], speeds[1] if speeds[1] is not None else base_oh
    pd = ProfileData(key, name, hands, stance or def_stance, base_mh, base_oh)
    for f in files:
        pd.files.append(str(f))
        add_report(pd, json.loads(f.read_text(encoding="utf-8")), str(f), crit_mult)
    if len(files) == 1 and ".iter" not in files[0].name:
        pd.notes.append("NOTE: only the aggregate report's representative run is used (its 'hits' come from one "
                        "iteration); pass the .iterN.report.json files for the full sample")
    return pd


def read_header(path: Path) -> dict[str, float]:
    """RAGE_* constants out of the generated WarriorData.h, if it exists."""
    out: dict[str, float] = {}
    if not path.is_file():
        return out
    pat = re.compile(r"constexpr\s+(?:float|double|u?int\d*(?:_t)?)\s+(RAGE_[A-Z0-9_]+)\s*=\s*([0-9.]+)f?\s*;")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pat.search(line)
        if m and m.group(1) in HEADER_NAMES:
            out[HEADER_NAMES[m.group(1)]] = float(m.group(2))
    return out


# ----------------------------------------------------------------------------------------------------------------
# Rates
# ----------------------------------------------------------------------------------------------------------------

@dataclass
class Rates:
    mh: float = 0.0
    oh: float = 0.0
    capped: int = 0

    @property
    def total(self) -> float:
        return self.mh + self.oh


def new_rates(pd: ProfileData, k: float, m: float, level: int, rate: float, scale: float = 1.0) -> Rates:
    """Rage per second under the new formula. `scale` > 1 models extra haste: more swings per second, a shorter
    hasted swing time per swing (damage per swing unchanged)."""
    r = Rates()
    if pd.duration_s <= 0:
        return r
    c = rage_conversion(level)
    for h in pd.hits:
        speed = new_speed_fixed(h.swing_s / scale, h.off_hand, m, h.crit)
        gain = new_rage_dealt(h.damage, speed, k, level, pd.battle, rate)
        if (k * 7.5 * h.damage / c + speed / SPEED_FIXED_POINT) / 2.0 > 2.0 * 7.5 * h.damage / c:  # cap bound
            r.capped += 1
        if h.off_hand:
            r.oh += gain * scale
        else:
            r.mh += gain * scale
    r.mh /= pd.duration_s
    r.oh /= pd.duration_s
    return r


def stock_rates(pd: ProfileData, level: int, rate: float, scale: float = 1.0) -> Rates:
    """Rage per second under the stock formula (factor from the UNHASTED weapon speed, so haste only adds swings)."""
    r = Rates()
    if pd.duration_s <= 0:
        return r
    for h in pd.hits:
        base = (pd.base_oh if h.off_hand else pd.base_mh) or h.swing_s
        gain = stock_rage_dealt(h.damage, stock_factor(base, h.off_hand, h.crit), level, rate)
        if h.off_hand:
            r.oh += gain * scale
        else:
            r.mh += gain * scale
    r.mh /= pd.duration_s
    r.oh /= pd.duration_s
    return r


def linear_terms(pd: ProfileData, level: int, rate: float) -> tuple[float, float, float, float]:
    """(A, X, S_mh, S_oh) so that the uncapped new rage per second is A * (k * X + m * S_mh + S_oh), with
    A = stance multiplier * rate / (2 T), X = sum 7.5 d / c, S_mh = sum swing * 3.5 (x2 on a crit) per main-hand hit,
    S_oh = sum swing * 0.875 (x2 on a crit) per off-hand hit."""
    c = rage_conversion(level)
    x = s_mh = s_oh = 0.0
    for h in pd.hits:
        x += 7.5 * h.damage / c
        crit = 2.0 if h.crit else 1.0
        if h.off_hand:
            s_oh += h.swing_s * OH_SPEED_FACTOR * crit
        else:
            s_mh += h.swing_s * MH_SPEED_FACTOR * crit
    a = (1.0 + (BATTLE_STANCE_PCT / 100.0 if pd.battle else 0.0)) * rate / (2.0 * pd.duration_s)
    return a, x, s_mh, s_oh


def solve_km(start: ProfileData, end: ProfileData, level: int, rate: float,
             growth: float = GROWTH_TARGET) -> tuple[float, float, str | None]:
    """D15: (a) a two-hander's new rage per second at bracket start equals stock's at bracket start; (b) at bracket
    end it is `growth` x its bracket-start value. Returns (k, m, problem)."""
    r_stock = stock_rates(start, level, rate).total
    a1, x1, s1, o1 = linear_terms(start, level, rate)
    a2, x2, s2, o2 = linear_terms(end, level, rate)
    a11, a12, b1 = a1 * x1, a1 * s1, r_stock - a1 * o1
    a21, a22, b2 = a2 * x2, a2 * s2, growth * r_stock - a2 * o2
    det = a11 * a22 - a12 * a21
    scale = max(abs(a11 * a22), abs(a12 * a21), 1e-12)
    if abs(det) < 1e-9 * scale:
        return float("nan"), float("nan"), "singular system: the start and end damage-to-speed mix is the same"
    k = (b1 * a22 - a12 * b2) / det
    m = (a11 * b2 - b1 * a21) / det
    return k, m, None


# ----------------------------------------------------------------------------------------------------------------
# Printing
# ----------------------------------------------------------------------------------------------------------------

def fmt(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}"


def print_sources(profiles: dict[str, ProfileData]) -> None:
    print("== SOURCES (white swings: spellId 0, not pet) ==")
    print(f"{'profile':<22} {'files':>5} {'sec':>6} {'stance':<9} {'hand':<4} {'hits':>5} {'crit%':>6} "
          f"{'avg d':>7} {'avg d(nc)':>9} {'swing s':>8} {'base s':>7} {'haste%':>7}")
    for pd in profiles.values():
        for off, label in ((False, "MH"), (True, "OH")):
            hs = [h for h in pd.hits if h.off_hand == off]
            if not hs:
                continue
            crits = [h for h in hs if h.crit]
            noncrit = [h.damage for h in hs if not h.crit]
            swing = statistics.mean(h.swing_s for h in hs)
            base = pd.base_oh if off else pd.base_mh
            haste = (base / swing - 1.0) * 100.0 if base and swing else float("nan")
            print(f"{pd.name:<22} {len(pd.files):>5} {fmt(pd.duration_s, 0):>6} {pd.stance:<9} {label:<4} {len(hs):>5} "
                  f"{fmt(100.0 * len(crits) / len(hs), 1):>6} {fmt(statistics.mean(h.damage for h in hs), 1):>7} "
                  f"{fmt(statistics.mean(noncrit), 1) if noncrit else '-':>9} {fmt(swing, 3):>8} "
                  f"{fmt(base, 2) if base else '-':>7} {fmt(haste, 1):>7}")
        for note in pd.notes:
            print(f"  {pd.name}: {note}")
    print("  (haste% = unhasted weapon speed / measured swing - 1; the unhasted speed is the profile's reference "
          "weapon, override with --speed)")
    print()


def print_raw_table(profiles: dict[str, ProfileData], k: float, m: float, level: int, rate: float, title: str) -> None:
    print(f"== {title}: rage per second, k={k:g} m={m:g} level {level} rate {rate:g} ==")
    print(f"{'profile':<22} {'stance':<9} {'stock MH':>9} {'stock OH':>9} {'STOCK':>8}   {'new MH':>8} {'new OH':>8} "
          f"{'NEW':>8}   {'new/stock':>9} {'rage/swing MH':>14}")
    rows: dict[str, tuple[Rates, Rates]] = {}
    for key, pd in profiles.items():
        st, nw = stock_rates(pd, level, rate), new_rates(pd, k, m, level, rate)
        rows[key] = (st, nw)
        mh_hits = [h for h in pd.hits if not h.off_hand]
        per_swing = nw.mh * pd.duration_s / len(mh_hits) if mh_hits else float("nan")
        cap_note = f"  [{nw.capped} capped hit(s)]" if nw.capped else ""
        print(f"{pd.name:<22} {pd.stance:<9} {fmt(st.mh):>9} {fmt(st.oh):>9} {fmt(st.total):>8}   {fmt(nw.mh):>8} "
              f"{fmt(nw.oh):>8} {fmt(nw.total):>8}   {fmt(nw.total / st.total if st.total else float('nan'), 3):>9} "
              f"{fmt(per_swing):>14}{cap_note}")
    for hands, s_key, e_key in (("two-hander", "2h-start", "2h-end"), ("dual wield", "dw-start", "dw-end")):
        if s_key in rows and e_key in rows:
            st_s, nw_s = rows[s_key]
            st_e, nw_e = rows[e_key]
            print(f"  {hands} bracket growth (end / start): stock x{fmt(st_e.total / st_s.total, 3)}, "
                  f"new x{fmt(nw_e.total / nw_s.total, 3)} (the doc: stock about +58%, new about +25%)")
    print()


def print_dw_advantage(profiles: dict[str, ProfileData], k: float, m: float, level: int, rate: float,
                       title: str) -> None:
    pairs = [("start", "2h-start", "dw-start"), ("end", "2h-end", "dw-end")]
    usable = [p for p in pairs if p[1] in profiles and p[2] in profiles]
    if not usable:
        print(f"== DUAL-WIELD ADVANTAGE ({title}) == needs both a 2h and a dw profile of the same bracket\n")
        return
    print(f"== DUAL-WIELD ADVANTAGE ({title}, k={k:g} m={m:g}): dual-wield rage/s over two-hander rage/s - 1 ==")
    print(f"{'bracket':<8} {'as played (2H Battle, DW Berserker)':>44} {'stance-neutral':>32}")
    print(f"{'':<8} {'stock':>10} {'new':>10} {'new/stock':>10}   {'stock':>10} {'new':>10} {'new/stock':>10}")
    for label, k2, kd in usable:
        two, dw = profiles[k2], profiles[kd]
        st2, stw = stock_rates(two, level, rate).total, stock_rates(dw, level, rate).total
        n2, nw = new_rates(two, k, m, level, rate).total, new_rates(dw, k, m, level, rate).total
        adv_st, adv_nw = stw / st2 - 1.0, nw / n2 - 1.0
        # stance-neutral: remove the Battle Stance x1.10 from the new two-hander and from nobody else
        n2_neutral = n2 / (1.0 + BATTLE_STANCE_PCT / 100.0) if two.battle else n2
        nw_neutral = nw / (1.0 + BATTLE_STANCE_PCT / 100.0) if dw.battle else nw
        adv_nw_n = nw_neutral / n2_neutral - 1.0
        print(f"{label:<8} {fmt(100 * adv_st, 1) + '%':>10} {fmt(100 * adv_nw, 1) + '%':>10} "
              f"{(fmt(adv_nw / adv_st, 2) if adv_st else '-'):>10}   {fmt(100 * adv_st, 1) + '%':>10} "
              f"{fmt(100 * adv_nw_n, 1) + '%':>10} {(fmt(adv_nw_n / adv_st, 2) if adv_st else '-'):>10}")
    print("  (the doc: dual wield's advantage is 'about halved', i.e. new/stock near 0.5; stock never had a stance "
          "bonus in this comparison)")
    print()


def print_haste_check(profiles: dict[str, ProfileData], k: float, m: float, level: int, rate: float,
                      title: str) -> None:
    print(f"== HASTE CHECK ({title}, k={k:g} m={m:g}): +{int(HASTE_CHECK * 100)}% haste on top of each profile's own "
          f"==")
    print(f"{'profile':<22} {'stock rage/s':>13} {'stock +15%':>11} {'x':>6}   {'new rage/s':>11} {'new +15%':>9} "
          f"{'x':>6}   {'damage part':>11} {'speed part':>10}  speed part +15%")
    s = 1.0 + HASTE_CHECK
    for pd in profiles.values():
        st0, st1 = stock_rates(pd, level, rate).total, stock_rates(pd, level, rate, s).total
        n0, n1 = new_rates(pd, k, m, level, rate).total, new_rates(pd, k, m, level, rate, s).total
        a, x, s_mh, s_oh = linear_terms(pd, level, rate)
        dmg_part = a * k * x
        spd_part = a * (m * s_mh + s_oh)
        # measured, not assumed: the same hits with k = 0 (speed part only), at +15% haste
        spd_part_h = new_rates(pd, 0.0, m, level, rate, s).total
        print(f"{pd.name:<22} {fmt(st0):>13} {fmt(st1):>11} {fmt(st1 / st0, 3):>6}   {fmt(n0):>11} {fmt(n1):>9} "
              f"{fmt(n1 / n0, 3):>6}   {fmt(dmg_part):>11} {fmt(spd_part):>10}  {fmt(spd_part_h)}")
    print("  (new: only the damage part grows with haste, the speed part per second is haste-neutral; stock: the "
          "factor uses the unhasted swing, so the speed part grows with haste too)")
    print()


def print_arms_budget(profiles: dict[str, ProfileData], k: float, m: float, level: int, rate: float,
                      title: str) -> None:
    spend = sum(n * c for _, n, c in ARMS_SPEND)
    print(f"== ARMS BUDGET (D16, {title}, k={k:g} m={m:g}) ==")
    print("  spend per minute (Arms doc section 9, ~40 presses at 0 haste):")
    for name, n, c in ARMS_SPEND:
        print(f"    {name:<16} {n:>3} x {c:>3} = {n * c:>4}")
    print(f"    {'total':<16} {'':>9} {spend:>4}")
    ms_n, ms_c = ARMS_SPEND[0][1], ARMS_SPEND[0][2]
    spend_alt = spend - ms_n * (ms_c - MORTAL_STRIKE_ALT_COST)
    shown = False
    for key in ("2h-start", "2h-end"):
        if key not in profiles:
            continue
        shown = True
        pd = profiles[key]
        white = new_rates(pd, k, m, level, rate).total * 60.0
        income = white + ANGER_MANAGEMENT_3_PER_MIN
        verdict = "SHORT" if income < spend else "enough"
        print(f"  {pd.name:<22} white swings {fmt(white, 0):>5}/min + Anger Management 3 "
              f"{fmt(ANGER_MANAGEMENT_3_PER_MIN, 0)}/min = {fmt(income, 0):>5}/min vs spend {spend}/min: "
              f"{fmt(income - spend, 0):>5} ({verdict}); with Mortal Strike at {MORTAL_STRIKE_ALT_COST} the spend is "
              f"{spend_alt} ({fmt(income - spend_alt, 0)})")
    if not shown:
        print("  needs a 2h profile")
    print("  (white swings only, 100% melee uptime; no rage from damage taken, Charge, Bloodrage or Execute; "
          "'short' means the D16 follow-up: set Mortal Strike 12294's cost to 25)")
    print()


# ----------------------------------------------------------------------------------------------------------------
# Self test
# ----------------------------------------------------------------------------------------------------------------

def self_test() -> int:
    failures: list[str] = []

    def check(label: str, got: float, want: float, nd: int = 2) -> None:
        ok = round(got, nd) == round(want, nd)
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {got:.4f} -> {round(got, nd):.{nd}f} (expected {want:.{nd}f})")
        if not ok:
            failures.append(label)

    def truth(label: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(': ' + detail) if detail else ''}")
        if not ok:
            failures.append(label)

    print("rage_sweep self-test: the W0a worked example (level 60, k 0.43, m 1.8)")
    print(f"  c(60) = {rage_conversion(60):.4f} (doc: 230.60)")
    k, m = 0.43, 1.8
    # 3.6 s two-hander, non-crit white hit 450, Battle Stance
    sp = new_speed_fixed(3.6, False, m, False)
    truth("speed factor 3.6 s x 3.5 x 1.8 = 22.68 in hundredths", sp == 2268, str(sp))
    check("main hand 3.6 s, hit 450, Battle Stance", new_rage_dealt(450, sp, k, 60, True), 15.94)
    # crit 900: the caller doubles the factor
    check("crit 900 (factor doubled)", new_rage_dealt(900, new_speed_fixed(3.6, False, m, True), k, 60, True), 31.87)
    # 30% haste: swing 2.77 s
    sp_h = new_speed_fixed(2.77, False, m, False)
    truth("speed factor 2.77 s x 3.5 x 1.8 = 17.45", sp_h == 1745, str(sp_h))
    check("30% haste (2.77 s swing) per swing", new_rage_dealt(450, sp_h, k, 60, True), 13.06)
    # off hand 2.6 s, hit 200 (no stance bonus in the doc's example)
    check("off hand 2.6 s, hit 200", new_rage_dealt(200, new_speed_fixed(2.6, True, m, False), k, 60, False), 2.54)
    # stock
    check("stock main hand, hit 450", stock_rage_dealt(450, stock_factor(3.6, False, False)), 13.32)
    truth("stock off-hand factor int(2.6 x 1.75) = int(4.55) = 4", stock_factor(2.6, True, False) == 4)
    check("stock off hand 2.6 s, hit 200", stock_rage_dealt(200, stock_factor(2.6, True, False)), 5.25)
    # Bear Form 2.5 s: speed part 15.75
    truth("Bear Form 2.5 s speed part 15.75", new_speed_fixed(2.5, False, m, False) == 1575)
    # the stock cap binds on tiny hits
    tiny = new_rage_dealt(10, new_speed_fixed(3.6, False, m, False), k, 60, False)
    truth("the stock cap 15 d / c binds on a 10-damage hit", abs(tiny - 15 * 10 / rage_conversion(60)) < 1e-9,
          f"{tiny:.4f}")

    print("pipeline: synthetic reports (hand split, rates, haste neutrality, D15 solve)")
    _self_test_pipeline(truth, check)
    if failures:
        print(f"SELF-TEST FAILED ({len(failures)}): " + ", ".join(failures))
        return 3
    print("SELF-TEST PASSED")
    return 0


def _synthetic_report(duration_ms: int, mh: tuple[float, float], oh: tuple[float, float] | None, step_ms: int = 100,
                      crit_every: int = 5, crit_mult: float = 2.0) -> dict:
    """White swings for one run: MH every mh[1] seconds at damage mh[0] (+- a small wobble), OH likewise."""
    hits = []

    def add(dmg: float, swing_s: float, phase_ms: int, tag: int) -> None:
        t, n = float(phase_ms), 0
        while t < duration_ms:
            n += 1
            crit = (n % crit_every == 0)
            wobble = 1.0 + 0.04 * ((n * 7 + tag) % 5 - 2) / 2.0
            d = dmg * wobble * (crit_mult if crit else 1.0)
            ts = int(round(t / step_ms) * step_ms)
            hits.append({"timestampMs": ts, "spellId": 0, "damage": int(round(d)), "crit": crit, "isPet": False,
                         "sourceEntry": 0, "target": 0})
            t += swing_s * 1000.0

    add(mh[0], mh[1], 1000, 0)
    if oh:
        add(oh[0], oh[1], 1500, 3)
    hits.sort(key=lambda h: h["timestampMs"])
    # a distractor: a non-white row that must be ignored
    hits.append({"timestampMs": 2000, "spellId": 12294, "damage": 9999, "crit": False, "isPet": False,
                 "sourceEntry": 0, "target": 0})
    return {"config": {"durationMs": duration_ms}, "summary": {"elapsedMs": duration_ms}, "hits": hits}


def _self_test_pipeline(truth, check) -> None:
    level, rate = 60, 1.0
    # two-hander: start 209/hit every 3.5 s (haste), end 302/hit every 3.55 s
    s_pd = ProfileData("2h-start", "synthetic-2h-start", 1, "battle", 3.6, None)
    e_pd = ProfileData("2h-end", "synthetic-2h-end", 1, "battle", 3.7, None)
    for pd, dmg, swing in ((s_pd, 209, 3.5), (e_pd, 302, 3.55)):
        for i in range(5):
            pd.files.append(f"synthetic{i}")
            add_report(pd, _synthetic_report(60000, (dmg, swing), None), pd.files[-1], CRIT_MULT)
    truth("2h swing time measured from hit gaps", abs(s_pd.hits[0].swing_s - 3.5) < 0.06, f"{s_pd.hits[0].swing_s:.3f}")
    truth("distractor spell row ignored", all(h.damage < 1000 for h in s_pd.hits))
    st = stock_rates(s_pd, level, rate)
    truth("stock rage/s is positive and all main hand", st.mh > 0 and st.oh == 0, f"{st.mh:.3f}")

    # D15 solve: (a) new start == stock start, (b) new end == 1.25 x new start
    k, m, problem = solve_km(s_pd, e_pd, level, rate)
    truth("solve returns a usable pair", problem is None and k > 0 and m > 0, f"k={k:.4f} m={m:.4f}")
    nstart = new_rates(s_pd, k, m, level, rate).total
    nend = new_rates(e_pd, k, m, level, rate).total
    truth("(a) new start rage/s equals stock start rage/s", abs(nstart / st.total - 1.0) < 0.002,
          f"{nstart:.4f} vs {st.total:.4f}")
    truth("(b) new end rage/s = 1.25 x new start", abs(nend / nstart - GROWTH_TARGET) < 0.01, f"x{nend / nstart:.4f}")

    # haste neutrality of the new speed part; the damage part grows with swings
    a, x, s_mh, s_oh = linear_terms(s_pd, level, rate)
    n0 = new_rates(s_pd, 0.0, 1.8, level, rate).total      # k = 0: speed part only
    n1 = new_rates(s_pd, 0.0, 1.8, level, rate, 1.15).total
    truth("speed part per second is haste-neutral (k = 0)", abs(n1 / n0 - 1.0) < 0.01, f"x{n1 / n0:.4f}")
    d0 = new_rates(s_pd, 1.0, 0.0, level, rate).total       # m = 0: damage term + the rounded-to-0 speed part
    d1 = new_rates(s_pd, 1.0, 0.0, level, rate, 1.15).total
    truth("damage part per second grows with haste (m = 0)", abs(d1 / d0 - 1.15) < 0.01, f"x{d1 / d0:.4f}")

    # dual wield hand split
    dw = ProfileData("dw-start", "synthetic-dw-start", 2, "berserker", 2.6, 2.5)
    for i in range(3):
        dw.files.append(f"synthetic{i}")
        add_report(dw, _synthetic_report(60000, (130, 2.55), (64, 2.45)), dw.files[-1], CRIT_MULT)
    mh_n = sum(1 for h in dw.hits if not h.off_hand)
    oh_n = sum(1 for h in dw.hits if h.off_hand)
    truth("dual wield split into two hands", mh_n > 0 and oh_n > 0 and abs(mh_n - oh_n) <= 0.15 * mh_n,
          f"MH {mh_n} OH {oh_n}")
    oh_swing = statistics.mean(h.swing_s for h in dw.hits if h.off_hand)
    truth("off-hand swing time measured", abs(oh_swing - 2.45) < 0.06, f"{oh_swing:.3f}")
    # stock gives the off hand int(2.5 x 1.75) = int(4.375) = 4
    truth("stock off-hand factor from the base speed", stock_factor(2.5, True, False) == 4)

    # a lone singular system is reported, not solved
    _, _, problem = solve_km(s_pd, s_pd, level, rate)
    truth("a singular system is refused", problem is not None, str(problem))


# ----------------------------------------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------------------------------------

def parse_kv(items: list[str], what: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"--{what}: expected KEY=VALUE, got {item!r}")
        key, value = item.split("=", 1)
        if key not in PROFILES:
            raise SystemExit(f"--{what}: unknown key {key!r} (one of {', '.join(PROFILES)})")
        out[key] = value
    return out


def main(argv: list[str]) -> int:
    here = Path(__file__).resolve().parent
    repo = here.parents[2]
    ap = argparse.ArgumentParser(description="Warrior rage sweep (W0a): stock vs dampened rage per second, D15 solve.")
    for key in PROFILES:
        ap.add_argument(f"--{key}", metavar="SRC", help=f"{PROFILES[key][0]} report(s)")
    ap.add_argument("--k", type=float, help="k for the raw tables (default: WarriorData.h, else 0.43)")
    ap.add_argument("--m", type=float, help="m for the raw tables (default: WarriorData.h, else 1.8)")
    ap.add_argument("--rate", type=float, default=1.0, help="Rate.Rage.Income (default 1)")
    ap.add_argument("--level", type=int, default=LEVEL, help="character level of the reports (default 60)")
    ap.add_argument("--crit-mult", type=float, default=CRIT_MULT, help="crit damage multiplier for the hand split")
    ap.add_argument("--header", type=Path, default=repo / "src/server/game/Entities/Unit/Generated/WarriorData.h",
                    help="generated WarriorData.h to read the constants from")
    ap.add_argument("--speed", action="append", metavar="KEY=MH[/OH]",
                    help="unhasted weapon speeds in seconds for a profile, e.g. dw-end=2.6/2.8")
    ap.add_argument("--stance", action="append", metavar="KEY=battle|berserker",
                    help="the stance the bot held in a profile (default: battle for 2h, berserker for dw)")
    ap.add_argument("--aggregate-only", action="store_true", help="use the aggregate's representative run only")
    ap.add_argument("--reports-dir", type=Path, default=here.parent / "reports")
    ap.add_argument("--self-test", action="store_true", help="reproduce the worked example and the pipeline checks")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    # Constants: the generated header wins over the built-in defaults, the flags win over both.
    global MH_SPEED_FACTOR, OH_SPEED_FACTOR, SPEED_FIXED_POINT
    hdr = read_header(args.header)
    if "mh" in hdr:
        MH_SPEED_FACTOR = hdr["mh"]
    if "oh" in hdr:
        OH_SPEED_FACTOR = hdr["oh"]
    if "fp" in hdr:
        SPEED_FIXED_POINT = int(hdr["fp"])
    k_flag = args.k if args.k is not None else hdr.get("k", DEFAULT_K)
    m_flag = args.m if args.m is not None else hdr.get("m", DEFAULT_M)
    src_note = (f"{args.header} (RAGE_K_60/RAGE_M_60/speed factors)" if hdr else "built-in defaults (no WarriorData.h)")
    print(f"constants: k={k_flag:g} m={m_flag:g} (flags override), MH factor {MH_SPEED_FACTOR:g}, OH factor "
          f"{OH_SPEED_FACTOR:g}, fixed point {SPEED_FIXED_POINT}; source: {src_note}")
    print(f"level {args.level}, c = {rage_conversion(args.level):.2f}, Rate.Rage.Income {args.rate:g}, crit multiplier "
          f"{args.crit_mult:g}\n")

    stances = parse_kv(args.stance, "stance")
    for key, value in stances.items():
        if value not in ("battle", "berserker"):
            raise SystemExit(f"--stance {key}={value}: expected battle or berserker")
    speeds: dict[str, tuple[float, float | None]] = {}
    for key, value in parse_kv(args.speed, "speed").items():
        parts = value.split("/")
        speeds[key] = (float(parts[0]), float(parts[1]) if len(parts) > 1 else None)

    profiles: dict[str, ProfileData] = {}
    for key, (name, _hands, _stance, _mh, _oh) in PROFILES.items():
        files = resolve_sources(getattr(args, key.replace("-", "_")), name, args.reports_dir, args.aggregate_only)
        if not files:
            print(f"(no report found for {name} in {args.reports_dir}; skipped)")
            continue
        try:
            profiles[key] = load_profile(key, files, stances.get(key), speeds.get(key), args.crit_mult)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"error reading {name}: {exc}", file=sys.stderr)
            return 1
    if not profiles:
        print("no reports found; run the four WarriorRage*Sim profiles first (see their headers)", file=sys.stderr)
        return 1
    print()

    print_sources(profiles)
    print_raw_table(profiles, k_flag, m_flag, args.level, args.rate, "RAW RAGE TABLE at the flag constants")
    print_dw_advantage(profiles, k_flag, m_flag, args.level, args.rate, "flag constants")
    print_haste_check(profiles, k_flag, m_flag, args.level, args.rate, "flag constants")
    print_arms_budget(profiles, k_flag, m_flag, args.level, args.rate, "flag constants")

    # D15 solve (suggestion only)
    print("== D15 SOLVE (a SUGGESTION: the user picks k and m) ==")
    if "2h-start" not in profiles or "2h-end" not in profiles:
        print("  needs both 2h-start and 2h-end reports; skipped\n")
        return 0
    start, end = profiles["2h-start"], profiles["2h-end"]
    k_raw, m_raw, problem = solve_km(start, end, args.level, args.rate)
    r_stock = stock_rates(start, args.level, args.rate).total
    print(f"  (a) two-hander new rage/s at bracket start = stock rage/s at bracket start = {r_stock:.3f}")
    print(f"  (b) two-hander new rage/s at bracket end = {GROWTH_TARGET:g} x its bracket-start value = "
          f"{GROWTH_TARGET * r_stock:.3f}")
    if problem:
        print(f"  STOP: {problem}. Nothing is suggested; report this to the user.")
        return 2
    print(f"  exact solution of the two linear equations: k = {k_raw:.4f}, m = {m_raw:.4f}")
    k_s, m_s = round(k_raw, 2), round(m_raw, 2)
    if k_raw <= 0 or m_raw <= 0 or k_s <= 0 or m_s <= 0:
        print(f"  STOP: k = {k_raw:.4f} / m = {m_raw:.4f} is not positive (rounded to 0.01: {k_s:.2f} / {m_s:.2f}). "
              f"REPORT AND STOP: the user decides what to change (the damage-to-speed mix of the two brackets, the "
              f"growth target or the stock anchor); no constants are suggested.")
        return 2
    print(f"  rounded to 0.01 (suggested): k = {k_s:.2f}, m = {m_s:.2f}")
    n_start = new_rates(start, k_s, m_s, args.level, args.rate).total
    n_end = new_rates(end, k_s, m_s, args.level, args.rate).total
    print(f"  at the rounded constants: start {n_start:.3f} rage/s (stock {r_stock:.3f}, residual "
          f"{100 * (n_start / r_stock - 1):+.2f}%), end {n_end:.3f} rage/s (x{n_end / n_start:.3f} of start, "
          f"target x{GROWTH_TARGET:g})")
    capped = [(pd.name, new_rates(pd, k_s, m_s, args.level, args.rate).capped) for pd in (start, end)]
    if any(n for _, n in capped):
        print("  NOTE: the stock cap (15 d / c) binds on some hits at these constants (" +
              ", ".join(f"{name}: {n}" for name, n in capped if n) +
              "); the linear solve ignores the cap, so check the residuals above")
    print()
    print_raw_table(profiles, k_s, m_s, args.level, args.rate, "RAGE TABLE at the SUGGESTED constants")
    print_dw_advantage(profiles, k_s, m_s, args.level, args.rate, "suggested constants")
    print_haste_check(profiles, k_s, m_s, args.level, args.rate, "suggested constants")
    print_arms_budget(profiles, k_s, m_s, args.level, args.rate, "suggested constants")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
