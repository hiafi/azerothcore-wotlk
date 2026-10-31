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
     src/server/game/Entities/Unit/Generated/WarriorData.h when that file is found, else 0.43 and 1.35),
  3. D15's suggested solve for k and m (a SUGGESTION only: the user picks k and m; the W0a solve, kept as is),
  4. the dual-wield advantage, stock against the new formula (the doc says "about halved"),
  5. the 15% haste check (W0b D23): two rows per profile, +15% SPELL haste (rage per second x1.15) and +15% ATTACK
     SPEED only (about x1.03: only the damage term moves with the swing rate),
  6. D36's Arms budget table (white-swing income with Battle Stance and Two-Handed Weapon Mastery, Anger Management 3
     and Bloodrage against the Arms rotation's spend at the built costs).

The formula (D12 + W0b D21, mirrored in src/server/game/Entities/Unit/WarriorMechanics.cpp):
    c(L)      = 0.0091107836 L^2 + 3.225598133 L + 4.2652911          (+13.27 per level above 70)
    stock     : f = int(unhasted swing * 3.5)  main hand, int(unhasted swing * 1.75) off hand
                dealt = (7.5 d / c + f) / 2, capped at 2 * 7.5 d / c, x rate
    new       : speed = lround(hasted swing * max(1, 1 / UNIT_MOD_CAST_SPEED) * 3.5 * m * 100) main hand,
                lround(hasted swing * max(1, 1 / UNIT_MOD_CAST_SPEED) * 0.875 * 100) off hand
                (hundredths); both are doubled on a crit, like the stock factor.
                1 / UNIT_MOD_CAST_SPEED is the spell-haste factor: a spell haste of h (0.15 = +15%) is 1 + h. The
                hasted swing is already shortened by attack speed, so a haste that is BOTH spell and attack speed
                (haste rating, Bloodlust) cancels in the swing: rage per swing is the unhasted figure and rage per
                second scales 1:1 with the haste; attack speed alone shortens the swing and only the damage term
                moves. A net slow (cast speed above 1) never lowers rage: the factor floors at 1.
                dealt = (k * 7.5 d / c + speed / 100) / 2, capped at the STOCK cap 15 d / c, then x 1.10 in Battle
                Stance (aura 213), then x rate
A new hit's damage d is the report's "damage" (the dummy has no absorb, so damage + absorbed is the same number).
The profiles' gear haste comes only from haste rating, which fans out to melee, ranged AND spell haste, so it is taken
as SPELL haste too: the profile's HasteRating (conf/profiles/<Name>.conf) / 10 percent at level 60 (gtCombatRatings
CR_HASTE_MELEE / CR_HASTE_SPELL level 60 = 10 rating per 1%; warrior class scalar 1), overridable with --haste. The true
hasted swing is then weapon speed / (1 + h): the report's own swing gaps are multiples of the 100 ms sim step (the
W0a reports read 3.600 s on a 3.6 s weapon at 2.2% haste), so they are not used for the speed term when the haste is
known. NOTE: the existing W0a reports were produced by the pre-W0b build (hasted swing, no spell factor); this
reference is the W0b formula, so their reference rows differ from the old output by the haste term.

WHAT THE REPORT CAN AND CANNOT TELL US (find: SimReport.h / EventRecorder.h):
  - A white swing is a "hits" row, isPet false, sourceEntry 0: {timestampMs, spellId, damage, crit, isPet,
    sourceEntry, target}. Since S3 the recorder tags the hand: spellId 0 (EventRecorder::MELEE_SPELL_ID) is the main
    hand, 0xFFFF0001 (EventRecorder::OFFHAND_MELEE_SPELL_ID, "Melee (off-hand)" in the HTML report) the off hand; a
    pre-S3 report has only spellId 0. There is no swing speed in the report, and a swing that missed or was dodged
    leaves no row at all (PvE is always-hit here).
  - The aggregate report keeps "hits" only from ONE representative iteration (the per-spell "spells" row has the
    averaged hitCount / critCount / totalDamage but no hands). So this script reads the per-iteration files
    (<stamp>.iterN.report.json, written next to the aggregate by run-sim.sh) whenever they exist and falls back to
    the aggregate's single run with a note (--aggregate-only forces that).
  - Hands: a two-hander has only the main hand. For dual wield the script splits by the recorder's tag when the
    report has it (any 0xFFFF0001 row). On a pre-S3 (untagged) report it falls back to two clusters of
    crit-normalised damage (1-D 2-means; the off hand hits for about half the main hand) and calls the lower cluster
    the off hand, warning when the clusters are not clearly apart or when the counts do not match the swing speeds.
  - Swing speed: the mean gap between one hand's consecutive hits in the run (the hasted swing time the new formula
    uses when no gear haste is known, exact on average even when Flurry-style haste comes and goes). The UNHASTED
    weapon speed the stock formula uses is not in the report either: it is a per-profile default below (the
    reference weapons of the profiles), overridable with --speed.
  - Gear haste: not in the report. It is the profile conf's HasteRating at 10 rating per 1% (level 60 only), or
    --haste KEY=PCT. The measured gaps are multiples of the sim step (100 ms), so a 2.2% haste on a 3.6 s weapon still
    reads 3.6 s; the speed term therefore uses weapon speed / (1 + haste), not the measured gap, when the haste is
    known.
  - powerSamples (--measured): the actor's rage every 500 ms (modules/mod-dpssim/README.md "Power and rune samples"),
    rage divided by ten, powerType 1. A window that also spends rage nets the spend against the swing's gain, so the
    sum of positive steps is only a LOWER BOUND of income there; --measured says so and prints the reference only.

Usage:
    python3 -I tools/rage_sweep.py [--2h-start SRC] [--2h-end SRC] [--dw-start SRC] [--dw-end SRC]
                                   [--2h-start-haste SRC] [--k 0.43] [--m 1.35] [--rate 1.0] [--level 60]
                                   [--crit-mult 2.0] [--header PATH] [--speed KEY=MH[/OH]]
                                   [--stance KEY=battle|berserker] [--haste KEY=PCT] [--aggregate-only]
                                   [--reports-dir DIR]
    python3 -I tools/rage_sweep.py [--tg-start SRC] [--tg-end SRC] [--fury]   (S3 D46: the FURY BUDGET section)
    python3 -I tools/rage_sweep.py --measured [same options]
    python3 -I tools/rage_sweep.py --self-test

SRC (a profile whose SRC is omitted is looked up in the reports dir: the newest <Profile>.<stamp>.report.json):
    a *.report.json aggregate (its sibling *.iterN.report.json are used when present), a stamp prefix such as
    reports/WarriorRage2HStartSim.20261030-120000, or a glob. Any subset of the four profiles works; the solve
    needs 2h-start and 2h-end, the dual-wield advantage needs all four, the Arms budget needs a 2h profile.
KEY is 2h-start, 2h-end, dw-start, dw-end or 2h-start-haste (WarriorRage2HStartHasteSim, W0b: the 2h-start profile
plus a haste top-up; optional, the tables and --measured use it when its report exists).

--measured (W0b D23): sources table, then per profile the rage income per second read from the report's powerSamples
(sum of positive steps over the series, all iterations) next to the white-swing REFERENCE this script computes, and the
hasted / unhasted ratio (2h-start-haste over 2h-start) of both. Acceptance: the measured ratio within 5% of the
reference ratio. If a profile's samples cannot show its income (a spend, a rage-cap sample, no rage series), the tool
says why and prints the reference only for it, with no ratio verdict.

Exit status: 0 ok, 1 usage / missing data, 2 the D15 solve is not usable (k <= 0 or m <= 0, or a singular system:
REPORT AND STOP, nothing is suggested), 3 self-test failure, 4 --measured ratio outside 5% of the reference.

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
DEFAULT_M = 1.35               # WarriorData::RAGE_M_60 (user pick 2026-10-29)
MH_SPEED_FACTOR = 3.5          # WarriorData::RAGE_MH_SPEED_FACTOR
OH_SPEED_FACTOR = 0.875        # WarriorData::RAGE_OH_SPEED_FACTOR
SPEED_FIXED_POINT = 100        # WarriorData::RAGE_SPEED_FIXED_POINT
STOCK_MH_FACTOR = 3.5          # Unit::GetRageWeaponSpeedHitFactor, main hand
STOCK_OH_FACTOR = 1.75         # ... off hand
BATTLE_STANCE_PCT = 10.0       # aura 213 (MOD_RAGE_FROM_DAMAGE_DEALT) on Battle Stance 2457
LEVEL = 60
CRIT_MULT = 2.0                # physical crit damage multiplier, used only to normalise damage for the hand split
HASTE_CHECK = 0.15             # D15/D23: the "+15%" of the haste check
GROWTH_TARGET = 1.25           # D15 (b), the W0a solve's bracket-growth target (the doc now measures about 8%)
RATING_PER_HASTE_PCT_60 = 10.0  # gtCombatRatings CR_HASTE_MELEE (id 1759) / CR_HASTE_SPELL (id 1959) at level 60 = 10
MEASURED_TOLERANCE = 0.05      # D23: measured hasted/unhasted ratio within 5% of the reference ratio
OFFHAND_WHITE_SPELL_ID = 0xFFFF0001  # EventRecorder::OFFHAND_MELEE_SPELL_ID: off-hand white swings (S3, D43)
RAGE_POWER_TYPE = 1            # Powers::POWER_RAGE

HEADER_NAMES = {
    "RAGE_K_60": "k",
    "RAGE_M_60": "m",
    "RAGE_MH_SPEED_FACTOR": "mh",
    "RAGE_OH_SPEED_FACTOR": "oh",
    "RAGE_SPEED_FIXED_POINT": "fp",
}

# Profiles that need not have a report (no "(no report found ...)" line when missing).
OPTIONAL_PROFILES = {"2h-start-haste", "tg-start", "tg-end"}

# The four sweep profiles: key -> (profile name, hands, default stance, default unhasted weapon speeds MH / OH).
# Speeds are the reference weapons of the profiles (see each conf's header).
PROFILES = {
    "2h-start": ("WarriorRage2HStartSim", 1, "battle", 3.6, None),     # Seeping Willow 12969
    "2h-end": ("WarriorRage2HEndSim", 1, "battle", 3.7, None),         # Barb of the Sand Reaver 21635
    # 2h-start + a HasteRating top-up (W0b D23), same Seeping Willow 12969
    "2h-start-haste": ("WarriorRage2HStartHasteSim", 1, "battle", 3.6, None),
    # Willey's Back Scratcher 22404 + Skullforge Reaver 13361
    "dw-start": ("WarriorRageDwStartSim", 2, "berserker", 2.6, 2.5),
    # Sand Polished Hammer 21715 + Ancient Qiraji Ripper 21650
    "dw-end": ("WarriorRageDwEndSim", 2, "berserker", 2.6, 2.8),
    # S3 (D43): Titan's Grip, two 2H axes 19200 / two Manslayer of the Qiraji 21492, 1.3 link; optional
    "tg-start": ("WarriorRageTgStartSim", 2, "berserker", 3.6, 3.6),
    "tg-end": ("WarriorRageTgEndSim", 2, "berserker", 3.6, 3.6),
}

# D36 (warrior-rework.S2-HANDOFF.md, "The Arms rage budget"): the doc's 40-press minute at the BUILT costs
# (Mortal Strike 25, Colossus Smash 20, Overpower 5, Rend 10, Slam 15). Momentum makes ~3.6 of the 10 Slams free, so
# 6.4 are paid. Mortal Strike counts ~2 Sudden Death resets in its 12 presses.
ARMS_SPEND = [
    ("Mortal Strike", 12, 25),
    ("Colossus Smash", 4, 20),
    ("Overpower", 12, 5),
    ("Rend", 2, 10),
    ("Slam (6.4 paid)", 6.4, 15),
]
ARMS_FREE_SLAMS_PER_MIN = 3.6   # Momentum's free Slams (informational: the paid count above already excludes them)
# Income beyond the white swings (D36): Anger Management 3/3 (6 rage per 3 s in combat) and Bloodrage (20 + 10 over
# 10 s, once a minute). Two-Handed Weapon Mastery 2/2's +30% white rage (aura 213) is additive with Battle Stance's
# +10% on the unmodified white rage.
ANGER_MANAGEMENT_3_PER_MIN = 120.0
BLOODRAGE_PER_MIN = 30.0
THWM_WHITE_RAGE_PCT = 30.0
MORTAL_STRIKE_ALT_COST = 20    # D36 lever: "Mortal Strike 25 -> 20 saves 60" (costs are [fixed]; doc change, not built)


# D46 (warrior-rework.S3-HANDOFF.md, "The Fury rage budget"): level 60, Berserker Stance (no rage bonus), build 1.3,
# single target, 100% melee uptime, no rage from damage taken. Spend of the guide's minute at the BUILT costs, per
# ability: (name, T0 presses, T0 paid presses, T3 presses, T3 paid presses, cost). Blood Rush 2/2 makes ~40% of the
# Rampages free (3 of 5 paid), Bloodsurge ~4.5 free Slams at T0 (6 of 10 paid; T3 4 of 8 paid). Presses total 40.5 /
# 45.5 (the D46 table rounds them to 40 / 46); rage total 550 / 650.
FURY_SPEND_13 = [
    ("Bloodthirst", 10, 10, 9, 9, 0),
    ("Rampage", 5, 3, 5, 3, 60),
    ("Whirlwind", 5, 5, 6, 6, 25),
    ("Slam", 10, 6, 8, 4, 15),
    ("Heroic Strike", 10, 10, 17, 17, 15),
    ("Death Wish", 0.5, 0.5, 0.5, 0.5, 10),
]
# Build 1.4 (packs; D46 / fury-bots-sims section 6.3): no Blood Rush, so every Rampage is paid; Whirlwind 8.5 a minute
# (8 s cooldown with Cleave cuts); the rage-limited allocation leaves nothing for paid Cleave (Cleave ~5.6 a minute
# is Bloodsurge-free, powerCost 0), ~11-12 GCDs idle. T0 / T3 columns follow the 1.3 bracket labels: Rampage 4.9 / 5.4
# presses (293 / 324 rage in D46's text; 294 / 324 here), Whirlwind 8.5 (214 in the text; 212.5 here).
FURY_SPEND_14 = [
    ("Bloodthirst", 10, 10, 10, 10, 0),
    ("Rampage", 4.9, 4.9, 5.4, 5.4, 60),
    ("Whirlwind", 8.5, 8.5, 8.5, 8.5, 25),
    ("Cleave (Bloodsurge-free)", 5.6, 0, 5.6, 0, 20),
    ("Death Wish", 0.5, 0.5, 0.5, 0.5, 10),
]
FURY_WHITE_DOC = (261.0, 305.0)         # D46: white swings MH + OH with Dual Wield Specialization 5 and Cruelty 3
FURY_WHITE_FACTOR = 1.06                # D46: Enrage haste + Flurry only grow the damage term: x1.06 over the uptime
FURY_WHITE_FACTOR_MEASURED = 1.0        # the tg-* sims play the full 1.3 build: Enrage / Flurry already in the white
FURY_BLOODTHIRST_RAGE = 10.0
FURY_IMPROVED_BLOODTHIRST_RAGE = 6.0    # Improved Bloodthirst 2/2
FURY_BLOODTHIRST_CASTS = 10             # 6 s cooldown, not hasted
FURY_UNBRIDLED_WRATH = (45.0, 44.0)     # Unbridled Wrath 2/2: 20% x 4 rage on ~48 swings + ~8 Heroic Strikes
FURY_METER = 190                        # Enrage meter size (D46: no change; the lever is 170)
FURY_METER_LEVER = 170


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


def new_speed_fixed(swing_s: float, off_hand: bool, m: float, crit: bool, spell_factor: float = 1.0) -> int:
    """Warrior::RageSpeedFactor for a player (hundredths), then the caller's crit doubling.

    swing_s is the HASTED swing; spell_factor is 1 / UNIT_MOD_CAST_SPEED (a spell haste of h is 1 + h). A net slow
    (spell_factor < 1) never lowers rage: the factor floors at 1 (W0b D21, the rogue energy rule)."""
    factor = lround(swing_s * max(1.0, spell_factor) * (OH_SPEED_FACTOR if off_hand else MH_SPEED_FACTOR * m)
                    * SPEED_FIXED_POINT)
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
class PowerRun:
    """One report file's powerSamples: (timestampMs, power, maxPower, powerType) in report order."""
    samples: list[tuple[int, float, float, int]]
    duration_s: float = 0.0


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
    haste: float = 0.0                 # the profile's gear haste as a fraction (0.15 = +15%), spell AND attack speed
    haste_known: bool = False          # True when `haste` comes from the conf's HasteRating or --haste
    power_runs: list[PowerRun] = field(default_factory=list)

    @property
    def battle(self) -> bool:
        return self.stance == "battle"

    def swing_terms(self, h: Hit) -> tuple[float, float]:
        """(true hasted swing seconds, spell-haste factor) for one hit, as the C++ sees them. With a known gear haste
        the swing is weapon speed / (1 + haste) (the report's gaps are quantised to the sim step); without one it is
        the measured gap and the spell factor is 1."""
        base = self.base_oh if h.off_hand else self.base_mh
        if self.haste_known and base:
            return base / (1.0 + self.haste), 1.0 + self.haste
        return h.swing_s, 1.0 + self.haste


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
            if h.get("spellId") in (0, OFFHAND_WHITE_SPELL_ID) and not h.get("isPet") and not h.get("sourceEntry")]
    if not rows:
        pd.notes.append(f"WARNING: {Path(path).name}: no white swings (spellId 0 / 0xFFFF0001) in 'hits'")
    tagged = any(h.get("spellId") == OFFHAND_WHITE_SPELL_ID for h in rows)
    if pd.hands == 2 and tagged:
        # the recorder tags the hand (S3): 0 = main hand, 0xFFFF0001 = off hand; no damage-cluster guess needed
        mh_rows = [h for h in rows if h.get("spellId") == 0]
        oh_rows = [h for h in rows if h.get("spellId") == OFFHAND_WHITE_SPELL_ID]
        if path == pd.files[0]:
            pd.notes.append(f"hand split by the recorder's tag: main hand {len(mh_rows)} swings, off hand "
                            f"{len(oh_rows)} swings")
    elif pd.hands == 2:
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
    power = report.get("powerSamples")
    if power:
        pd.power_runs.append(PowerRun([
            (int(p["timestampMs"]), float(p["power"]), float(p.get("maxPower", 0)), int(p.get("powerType", -1)))
            for p in power], duration_ms / 1000.0))


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


def conf_haste_pct(profile_name: str, level: int, conf_dir: Path) -> float | None:
    """The profile conf's HasteRating as percent haste at level 60 (10 rating per 1%), or None when the conf is
    missing, has no HasteRating, or the level is not 60 (the rating table differs per level)."""
    path = conf_dir / f"{profile_name}.conf"
    if level != 60 or not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*HasteRating\s*=\s*([0-9.]+)\s*(?:#.*)?$", line)
        if m:
            return float(m.group(1)) / RATING_PER_HASTE_PCT_60
    return None


def load_profile(key: str, files: list[Path], stance: str | None, speeds: tuple[float, float | None] | None,
                 crit_mult: float, haste_pct: float | None = None) -> ProfileData:
    name, hands, def_stance, base_mh, base_oh = PROFILES[key]
    if speeds:
        base_mh, base_oh = speeds[0], speeds[1] if speeds[1] is not None else base_oh
    pd = ProfileData(key, name, hands, stance or def_stance, base_mh, base_oh)
    if haste_pct is not None:
        pd.haste, pd.haste_known = haste_pct / 100.0, True
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


def new_rates(pd: ProfileData, k: float, m: float, level: int, rate: float, scale: float = 1.0,
              spell_scale: float = 1.0) -> Rates:
    """Rage per second under the new formula. `scale` > 1 models extra ATTACK SPEED: more swings per second, a
    shorter hasted swing time per swing (damage per swing unchanged). `spell_scale` > 1 models extra SPELL haste on
    top of the profile's own: it multiplies the speed part per swing (W0b D21). Haste rating is both, so +15% haste
    is scale = spell_scale = 1.15; Bloodlust likewise; Slice and Dice is `scale` alone."""
    r = Rates()
    if pd.duration_s <= 0:
        return r
    c = rage_conversion(level)
    for h in pd.hits:
        swing, spell = pd.swing_terms(h)
        speed = new_speed_fixed(swing / scale, h.off_hand, m, h.crit, spell * spell_scale)
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


def linear_terms(pd: ProfileData, level: int, rate: float, scale: float = 1.0,
                 spell_scale: float = 1.0) -> tuple[float, float, float, float]:
    """(A, X, S_mh, S_oh) so that the uncapped new rage per second is A * (k * X + m * S_mh + S_oh), with
    A = stance multiplier * rate / (2 T), X = sum 7.5 d / c, S_mh = sum swing * spell factor * 3.5 (x2 on a crit) per
    main-hand hit, S_oh = sum swing * spell factor * 0.875 (x2 on a crit) per off-hand hit. `scale` / `spell_scale`
    as in new_rates: the hit counts per second grow with `scale`, the swing shrinks with it, the spell factor
    multiplies the speed part."""
    c = rage_conversion(level)
    x = s_mh = s_oh = 0.0
    for h in pd.hits:
        swing, spell = pd.swing_terms(h)
        x += 7.5 * h.damage / c * scale
        crit = 2.0 if h.crit else 1.0
        eff = swing * max(1.0, spell * spell_scale)         # (swing / scale) x (scale x more swings) cancels
        if h.off_hand:
            s_oh += eff * OH_SPEED_FACTOR * crit
        else:
            s_mh += eff * MH_SPEED_FACTOR * crit
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
    print("== SOURCES (white swings: spellId 0 main hand, 0xFFFF0001 off hand, not pet) ==")
    print(f"{'profile':<26} {'files':>5} {'sec':>6} {'stance':<9} {'hand':<4} {'hits':>5} {'crit%':>6} "
          f"{'avg d':>7} {'avg d(nc)':>9} {'swing s':>8} {'base s':>7} {'meas.h%':>7} {'gear h%':>7}")
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
            gear = fmt(100.0 * pd.haste, 1) if pd.haste_known else "-"
            print(f"{pd.name:<26} {len(pd.files):>5} {fmt(pd.duration_s, 0):>6} {pd.stance:<9} {label:<4} {len(hs):>5} "
                  f"{fmt(100.0 * len(crits) / len(hs), 1):>6} {fmt(statistics.mean(h.damage for h in hs), 1):>7} "
                  f"{fmt(statistics.mean(noncrit), 1) if noncrit else '-':>9} {fmt(swing, 3):>8} "
                  f"{fmt(base, 2) if base else '-':>7} {fmt(haste, 1):>7} {gear:>7}")
        for note in pd.notes:
            print(f"  {pd.name}: {note}")
    print("  (meas.h% = unhasted weapon speed / measured swing - 1, quantised by the 100 ms sim step; gear h% = the "
          "profile's HasteRating at 10 rating per 1%, taken as spell AND attack-speed haste, override with --haste; "
          "the unhasted speed is the profile's reference weapon, override with --speed)")
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
                  f"new x{fmt(nw_e.total / nw_s.total, 3)} (the doc: stock about +58%; its measured "
                  f"growth for the new formula is about +8%)")
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


def haste_check_rows(pd: ProfileData, k: float, m: float, level: int, rate: float) -> dict[str, float]:
    """The numbers of one profile's +15% haste check (W0b D23)."""
    s = 1.0 + HASTE_CHECK
    n0 = new_rates(pd, k, m, level, rate).total
    spell = new_rates(pd, k, m, level, rate, s, s).total       # haste rating / Bloodlust: attack speed AND spell haste
    atk = new_rates(pd, k, m, level, rate, s).total            # Slice and Dice / Icy Talons: attack speed only
    a, x, s_mh, s_oh = linear_terms(pd, level, rate)
    dmg_part, spd_part = a * k * x, a * (m * s_mh + s_oh)
    # expected from the formula: the damage part follows the swing rate, the speed part only the spell factor
    # (the swing shortens by attack speed, the spell factor lengthens it back), so attack speed alone leaves it alone
    exp_atk = (dmg_part * s + spd_part) / (dmg_part + spd_part) if dmg_part + spd_part else float("nan")
    return {"n0": n0, "spell": spell, "atk": atk, "exp_spell": s, "exp_atk": exp_atk,
            "dmg": dmg_part, "spd": spd_part}


def print_haste_check(profiles: dict[str, ProfileData], k: float, m: float, level: int, rate: float,
                      title: str) -> None:
    print(f"== HASTE CHECK ({title}, k={k:g} m={m:g}): +{int(HASTE_CHECK * 100)}% on top of each profile's own ==")
    print(f"{'profile':<26} {'stock':>6} {'new rage/s':>10} | {'+15% SPELL haste':^25} | "
          f"{'+15% ATTACK SPEED only':^25} | {'damage':>7} {'speed':>7}")
    print(f"{'':<26} {'x':>6} {'':>10} | {'rage/s':>8} {'x':>7} {'expect':>8} | {'rage/s':>8} {'x':>7} {'expect':>8} "
          f"| {'part':>7} {'part':>7}")
    s = 1.0 + HASTE_CHECK
    for pd in profiles.values():
        st0, st1 = stock_rates(pd, level, rate).total, stock_rates(pd, level, rate, s).total
        r = haste_check_rows(pd, k, m, level, rate)
        print(f"{pd.name:<26} {fmt(st1 / st0, 3):>6} {fmt(r['n0']):>10} | {fmt(r['spell']):>8} "
              f"{fmt(r['spell'] / r['n0'], 3):>7} {fmt(r['exp_spell'], 3):>8} | {fmt(r['atk']):>8} "
              f"{fmt(r['atk'] / r['n0'], 3):>7} {fmt(r['exp_atk'], 3):>8} | {fmt(r['dmg']):>7} {fmt(r['spd']):>7}")
    print("  (new: rage scales 1:1 with SPELL haste; attack speed alone only speeds the swings, so only the damage "
          "part per second moves and the speed part is flat. 'expect' is computed from the uncapped formula; the "
          "x column is the rounded per-hit sum. Stock: the factor uses the unhasted swing, so any attack speed "
          "scales everything.)")
    print()


@dataclass
class Measured:
    """Rage income read off one profile's powerSamples."""
    ok: bool = False                  # False: the samples cannot show the income, `reason` says why
    reason: str = ""
    per_second: float = 0.0           # sum of positive steps / run seconds, all iterations (a lower bound unless ok)
    interval_ms: float = 0.0          # median spacing of the samples
    windows: int = 0
    spend_windows: int = 0            # windows where the power went DOWN (a spend or decay nets against a gain there)
    cap_windows: int = 0              # samples sitting at the rage cap (overflow is lost)


def measured_income(pd: ProfileData) -> Measured:
    """Rage per second from the report's powerSamples: the sum of the positive steps between consecutive samples."""
    out = Measured()
    if not pd.power_runs:
        out.reason = "no powerSamples in the report (the playerbot DPS run writes them; older reports do not)"
        return out
    if len(pd.power_runs) != len(pd.files):
        out.reason = f"powerSamples missing in {len(pd.files) - len(pd.power_runs)} of {len(pd.files)} report file(s)"
        return out
    gaps: list[int] = []
    total_pos = seconds = 0.0
    for run in pd.power_runs:
        if any(t != RAGE_POWER_TYPE for _, _, _, t in run.samples):
            out.reason = "the powerSamples are not rage (powerType != 1)"
            return out
        if len(run.samples) < 2:
            out.reason = "fewer than two powerSamples in a run"
            return out
        for (t0, p0, _, _), (t1, p1, mx1, _) in zip(run.samples, run.samples[1:]):
            gaps.append(t1 - t0)
            out.windows += 1
            if p1 > p0:
                total_pos += p1 - p0
            elif p1 < p0:
                out.spend_windows += 1
            if mx1 > 0 and p1 >= mx1 - 1e-9:
                out.cap_windows += 1
        seconds += run.duration_s
    out.interval_ms = statistics.median(gaps) if gaps else 0.0
    out.per_second = total_pos / seconds if seconds > 0 else 0.0
    problems = []
    if out.spend_windows:
        problems.append(f"{out.spend_windows} of {out.windows} {out.interval_ms:g} ms windows lose rage (a spend or "
                        f"decay nets against the gain in the same window)")
    if out.cap_windows:
        problems.append(f"{out.cap_windows} sample(s) at the rage cap (overflow is lost)")
    if problems:
        out.reason = "income hidden: " + "; ".join(problems)
        return out
    out.ok = True
    return out


def print_measured(profiles: dict[str, ProfileData], k: float, m: float, level: int, rate: float) -> int:
    """W0b D23's --measured table; returns the exit status contribution (0, or 4 when the ratio check fails)."""
    print(f"== MEASURED RAGE INCOME (report powerSamples, k={k:g} m={m:g}, level {level}) ==")
    print(f"{'profile':<26} {'runs':>4} {'ms':>5} {'windows':>8} {'spend':>6} {'capped':>6} {'measured/s':>11} "
          f"{'reference/s':>12} {'meas/ref':>9}")
    ref: dict[str, float] = {}
    got: dict[str, Measured] = {}
    for key, pd in profiles.items():
        ref[key] = new_rates(pd, k, m, level, rate).total
        mi = got[key] = measured_income(pd)
        if mi.ok:
            print(f"{pd.name:<26} {len(pd.power_runs):>4} {mi.interval_ms:>5g} {mi.windows:>8} {mi.spend_windows:>6} "
                  f"{mi.cap_windows:>6} {fmt(mi.per_second, 3):>11} {fmt(ref[key], 3):>12} "
                  f"{fmt(mi.per_second / ref[key], 3) if ref[key] else '-':>9}")
        else:
            print(f"{pd.name:<26} {len(pd.power_runs):>4} {mi.interval_ms:>5g} {mi.windows:>8} {mi.spend_windows:>6} "
                  f"{mi.cap_windows:>6} {'hidden':>11} {fmt(ref[key], 3):>12} {'-':>9}")
            print(f"  {pd.name}: {mi.reason}; reference only (the positive-step sum, a lower bound, is "
                  f"{fmt(mi.per_second, 3)} rage/s)" if mi.windows else f"  {pd.name}: {mi.reason}; reference only")
    status = 0
    base, hasted = profiles.get("2h-start"), profiles.get("2h-start-haste")
    print()
    if not base or not hasted:
        print("  hasted / unhasted ratio: needs both a WarriorRage2HStartSim and a WarriorRage2HStartHasteSim report")
        print()
        return status
    ref_ratio = ref["2h-start-haste"] / ref["2h-start"] if ref["2h-start"] else float("nan")
    # what the haste step is worth by the formula alone: the spell-haste ratio of the two gear hastes
    ideal = (1.0 + hasted.haste) / (1.0 + base.haste)
    print(f"  hasted / unhasted reference ratio {fmt(ref_ratio, 3)} (gear haste {fmt(100 * base.haste, 1)}% -> "
          f"{fmt(100 * hasted.haste, 1)}%: spell haste alone would give x{fmt(ideal, 3)})")
    if got["2h-start"].ok and got["2h-start-haste"].ok:
        meas_ratio = got["2h-start-haste"].per_second / got["2h-start"].per_second
        dev = meas_ratio / ref_ratio - 1.0
        verdict = "PASS" if abs(dev) <= MEASURED_TOLERANCE else "FAIL"
        print(f"  measured ratio {fmt(meas_ratio, 3)} vs reference {fmt(ref_ratio, 3)}: {100 * dev:+.1f}% "
              f"(tolerance {100 * MEASURED_TOLERANCE:g}%): {verdict}")
        if verdict == "FAIL":
            status = 4
    else:
        hidden = [profiles[key].name for key in ("2h-start", "2h-start-haste") if not got[key].ok]
        print(f"  measured ratio: not available, income hidden in {', '.join(hidden)}; reference only")
    print()
    return status


def arms_income(white_stance: float, stance_pct: float) -> tuple[float, float, float]:
    """D36 income per minute from the white-swing rage that already includes the stance bonus: (white base, white with
    the stance and Two-Handed Weapon Mastery bonuses added together, total with Anger Management and Bloodrage)."""
    base = white_stance / (1.0 + stance_pct / 100.0)
    white = base * (1.0 + (stance_pct + THWM_WHITE_RAGE_PCT) / 100.0)
    return base, white, white + ANGER_MANAGEMENT_3_PER_MIN + BLOODRAGE_PER_MIN


def print_arms_budget(profiles: dict[str, ProfileData], k: float, m: float, level: int, rate: float,
                      title: str) -> None:
    spend = sum(n * c for _, n, c in ARMS_SPEND)
    print(f"== ARMS BUDGET (D36, {title}, k={k:g} m={m:g}) ==")
    print("  spend per minute (Arms doc, ~40 presses at 0 haste, built costs; Momentum's "
          f"~{ARMS_FREE_SLAMS_PER_MIN:g} free Slams per minute are not paid):")
    for name, n, c in ARMS_SPEND:
        print(f"    {name:<16} {n:>4g} x {c:>3} = {n * c:>5g}")
    print(f"    {'total':<16} {'':>10} {spend:>5g}")
    ms_n, ms_c = ARMS_SPEND[0][1], ARMS_SPEND[0][2]
    spend_alt = spend - ms_n * (ms_c - MORTAL_STRIKE_ALT_COST)
    shown = False
    for key in ("2h-start", "2h-end"):
        if key not in profiles:
            continue
        shown = True
        pd = profiles[key]
        # new_rates() includes Battle Stance's +10% (additive aura 213); THWM's +30% is additive with it on the base
        # white rage: base * (1 + 0.10 + 0.30).
        white_stance = new_rates(pd, k, m, level, rate).total * 60.0
        stance_pct = BATTLE_STANCE_PCT if pd.battle else 0.0
        white_base, white, income = arms_income(white_stance, stance_pct)
        verdict = "SHORT" if income < spend else "enough"
        print(f"  {pd.name:<22} white {fmt(white_base, 0):>4} base -> {fmt(white, 0):>4} with stance "
              f"+{stance_pct:g}% and THWM +{THWM_WHITE_RAGE_PCT:g}%, + Anger Management 3 "
              f"{fmt(ANGER_MANAGEMENT_3_PER_MIN, 0)} + "
              f"Bloodrage {fmt(BLOODRAGE_PER_MIN, 0)} = {fmt(income, 0):>4}/min vs spend {spend:g}/min: "
              f"{fmt(income - spend, 0):>5} ({verdict}); with Mortal Strike at {MORTAL_STRIKE_ALT_COST} the spend is "
              f"{spend_alt:g} ({fmt(income - spend_alt, 0)})")
    if not shown:
        print("  needs a 2h profile")
    print("  (white swings only, 100% melee uptime; no rage from damage taken, Charge or Execute; a SHORT minute "
          "is covered by the bot's pooling, the lever sizes are doc-level changes and are NOT built)")
    print()


def fury_spend(table: list[tuple[str, float, float, float, float, int]], bracket: int) -> float:
    """D46 paid rage per minute of one spend table; bracket 0 = T0 (bracket start), 3 = T3 (bracket end)."""
    return sum((paid0 if bracket == 0 else paid3) * cost for _n, _p0, paid0, _p3, paid3, cost in table)


def fury_income(white: float, unbridled_wrath: float = FURY_UNBRIDLED_WRATH[0],
                white_factor: float = FURY_WHITE_FACTOR) -> dict[str, float]:
    """D46 Fury income per minute: white swings (MH + OH) x `white_factor` + Bloodthirst (10 + Improved Bloodthirst 6)
    x 10 casts + Unbridled Wrath + Bloodrage 30. `white` is the white-swing rage per minute. The factor is 1.06 (Enrage
    haste + Flurry over their uptime) for the doc figures, which exclude them, and FURY_WHITE_FACTOR_MEASURED (1.0) for
    a measured tg-* sim, whose bot plays the full 1.3 build so its white already includes them."""
    parts = {
        "white": white * white_factor,
        "bloodthirst": (FURY_BLOODTHIRST_RAGE + FURY_IMPROVED_BLOODTHIRST_RAGE) * FURY_BLOODTHIRST_CASTS,
        "unbridled wrath": unbridled_wrath,
        "bloodrage": BLOODRAGE_PER_MIN,
    }
    parts["total"] = sum(parts.values())
    return parts


def print_fury_budget(profiles: dict[str, ProfileData], k: float, m: float, level: int, rate: float,
                      title: str) -> None:
    print(f"== FURY BUDGET (D46, {title}, k={k:g} m={m:g}) ==")
    for label, table in (("build 1.3 (guide minute, Titan's Grip or dual wield)", FURY_SPEND_13),
                         ("build 1.4 (packs, rage-limited minute; no Blood Rush)", FURY_SPEND_14)):
        print(f"  spend per minute, {label}: presses and paid rage at bracket start T0 / end T3")
        for name, p0, paid0, p3, paid3, cost in table:
            print(f"    {name:<26} T0 {p0:>5g} presses {paid0 * cost:>5g} rage   T3 {p3:>5g} presses "
                  f"{paid3 * cost:>5g} rage   (cost {cost})")
        print(f"    {'total':<26} T0 {sum(r[1] for r in table):>5g} presses {fury_spend(table, 0):>5g} rage   "
              f"T3 {sum(r[3] for r in table):>5g} presses {fury_spend(table, 3):>5g} rage")
    spend = (fury_spend(FURY_SPEND_13, 0), fury_spend(FURY_SPEND_13, 3))
    rows = []   # (label, white per minute, unbridled wrath, bracket index, white factor)
    for i, (label, uw, key_tg, key_dw) in enumerate((("start", FURY_UNBRIDLED_WRATH[0], "tg-start", "dw-start"),
                                                     ("end", FURY_UNBRIDLED_WRATH[1], "tg-end", "dw-end"))):
        rows.append((f"doc white, bracket {label}", FURY_WHITE_DOC[i], uw, i, FURY_WHITE_FACTOR))
        if key_tg in profiles:
            white = new_rates(profiles[key_tg], k, m, level, rate).total * 60.0
            rows.append((f"measured {profiles[key_tg].name}", white, uw, i, FURY_WHITE_FACTOR_MEASURED))
        if key_dw in profiles:
            white = new_rates(profiles[key_dw], k, m, level, rate).total * 60.0
            print(f"  (sweep {profiles[key_dw].name}: white {fmt(white, 0)}/min BEFORE Dual Wield Specialization 5 and "
                  f"Cruelty 3; the doc figure {fmt(FURY_WHITE_DOC[i], 0)} includes them)")
    print("  income per minute (white x 1.06 on the doc rows, x 1.0 on the measured ones: their sims already play "
          "Enrage and Flurry; + Bloodthirst 16 x 10 + Unbridled Wrath + Bloodrage 30; spell haste adds 1:1 to the "
          "white part) against the 1.3 guide-minute spend:")
    for label, white, uw, i, factor in rows:
        inc = fury_income(white, uw, factor)
        gap = inc["total"] - spend[i]
        print(f"    {label:<34} white {fmt(white, 0):>4} x {factor:g} = {fmt(inc['white'], 0):>4} + "
              f"Bloodthirst {fmt(inc['bloodthirst'], 0)} + Unbridled Wrath {fmt(uw, 0)} + Bloodrage "
              f"{fmt(inc['bloodrage'], 0)} = {fmt(inc['total'], 0):>4} vs spend {spend[i]:g}: {fmt(gap, 0):>5} "
              f"({'SHORT' if gap < 0 else 'enough'})")
    # lever sizes (D46: for M / the user, NOT built), computed on the doc start / end bracket
    print("  levers (per minute, NOT built; costs are [fixed], a doc change):")
    for i, label in ((0, "T0"), (1, "T3")):
        inc = fury_income(FURY_WHITE_DOC[i], FURY_UNBRIDLED_WRATH[i])
        paid = {n: (paid0 if i == 0 else paid3) for n, _p0, paid0, _p3, paid3, _c in FURY_SPEND_13}
        paid_total = fury_spend(FURY_SPEND_13, 0 if i == 0 else 3)
        small = paid["Heroic Strike"] + paid["Slam"]
        print(f"    {label}: Enrage meter {FURY_METER} -> {FURY_METER_LEVER}: fills "
              f"{fmt(paid_total / FURY_METER, 2)} -> {fmt(paid_total / FURY_METER_LEVER, 2)} a minute (about +6 points "
              f"of Enrage uptime); Bloodthirst +3 rage: +{3 * FURY_BLOODTHIRST_CASTS}; Heroic Strike / Cleave / Slam "
              f"-5 each: -{fmt(5 * small, 0)} spend ({fmt(paid['Heroic Strike'], 0)} HS + {fmt(paid['Slam'], 0)} paid "
              f"Slam presses; D46 text 35-50 on the rage-limited minute); Rampage 60 -> 50: "
              f"-{fmt(10 * paid['Rampage'], 0)} (D46 text ~32 at 5.4 presses); Unbridled Wrath 20% -> 30%: "
              f"+{fmt(FURY_UNBRIDLED_WRATH[i] / 2, 0)}; Bloodrage 30 -> 40: +10; k/m +10% white: "
              f"+{fmt(0.10 * inc['white'], 0)}; Quick Execution (cover) raises spell haste = rage/s 1:1")
    print("  (100% melee uptime, no rage from damage taken, Charge or Execute; the sims measure it: rage paid = "
          "powerCost + Execute's extra, fills = paid / 190, uptime, starvation, seconds at cap)")
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

    print("rage_sweep self-test: the W0b worked example (D22: level 60, k 0.43, m 1.35, 3.6 s two-hander, Battle "
          "Stance)")
    print(f"  c(60) = {rage_conversion(60):.4f} (doc: 230.60)")
    k, m = 0.43, 1.35
    # 3.6 s two-hander, non-crit white hit 450, Battle Stance
    sp = new_speed_fixed(3.6, False, m, False)
    truth("speed factor 3.6 s x 3.5 x 1.35 = 17.01 in hundredths", sp == 1701, str(sp))
    check("damage term k x 7.5 x 450 / c", k * 7.5 * 450 / rage_conversion(60), 6.29)
    check("main hand 3.6 s, hit 450, Battle Stance", new_rage_dealt(450, sp, k, 60, True), 12.82)
    # crit 900: the caller doubles the factor
    check("crit 900 (factor doubled)", new_rage_dealt(900, new_speed_fixed(3.6, False, m, True), k, 60, True), 25.63)

    # Bloodlust: 30% attack speed AND 30% spell haste. Swing 2.77 s, spell factor 1.30: per swing the unhasted figure
    sp_bl = new_speed_fixed(2.77, False, m, False, 1.30)
    truth("Bloodlust speed factor 2.77 s x 1.30 x 3.5 x 1.35 = 17.01", sp_bl == 1701, str(sp_bl))
    per_swing_bl = new_rage_dealt(450, sp_bl, k, 60, True)
    check("Bloodlust (30% melee and spell, swing 2.77 s) per swing", per_swing_bl, 12.82)
    per_sec_unhasted = new_rage_dealt(450, sp, k, 60, True) / 3.6
    check("Bloodlust rage per second over unhasted", (per_swing_bl / 2.77) / per_sec_unhasted, 1.30)
    # attack speed alone (30%): swing 2.77 s, spell factor 1
    sp_as = new_speed_fixed(2.77, False, m, False)
    truth("attack-speed-only speed factor 2.77 s x 3.5 x 1.35 = 13.09", sp_as == 1309, str(sp_as))
    per_swing_as = new_rage_dealt(450, sp_as, k, 60, True)
    check("attack speed only 30% (swing 2.77 s) per swing", per_swing_as, 10.66)
    check("attack speed only 30% rage per second over unhasted", (per_swing_as / 2.77) / per_sec_unhasted, 1.08)
    # a net slow never lowers rage: cast speed 1.25 -> factor 0.8 floors at 1; a cast speed 0 or less is not a factor
    truth("a net slow (spell factor 0.8) floors at 1: same speed factor as unhasted",
          new_speed_fixed(3.6, False, m, False, 0.8) == sp and new_speed_fixed(3.6, False, m, False, 1 / 1.25) == sp)
    truth("a spell haste factor of exactly 1 is the unhasted factor", new_speed_fixed(3.6, False, m, False, 1.0) == sp)
    truth("a bigger slow does not go below it either (factor 0.5)", new_speed_fixed(3.6, False, m, False, 0.5) == sp)
    truth("an extra +15% spell haste on top of Bloodlust multiplies the speed factor by 1.15 (factor 1.495)",
          new_speed_fixed(2.77, False, m, False, 1.15 * 1.30) == lround(2.77 * 1.495 * 3.5 * 1.35 * 100))
    # off hand 2.6 s, hit 200, no stance bonus and no spell haste
    check("off hand 2.6 s, hit 200", new_rage_dealt(200, new_speed_fixed(2.6, True, m, False), k, 60, False), 2.54)
    # stock
    check("stock main hand, hit 450", stock_rage_dealt(450, stock_factor(3.6, False, False)), 13.32)
    truth("stock off-hand factor int(2.6 x 1.75) = int(4.55) = 4", stock_factor(2.6, True, False) == 4)
    check("stock off hand 2.6 s, hit 200", stock_rage_dealt(200, stock_factor(2.6, True, False)), 5.25)
    # Bear Form 2.5 s: speed part 3.5 x 1.35 x 2.5 = 11.81
    truth("Bear Form 2.5 s speed part 11.81", new_speed_fixed(2.5, False, m, False) == 1181)
    # the stock cap binds on tiny hits
    tiny = new_rage_dealt(10, new_speed_fixed(3.6, False, m, False), k, 60, False)
    truth("the stock cap 15 d / c binds on a 10-damage hit", abs(tiny - 15 * 10 / rage_conversion(60)) < 1e-9,
          f"{tiny:.4f}")

    # D36 Arms budget: spend 556 a minute at the built costs; income 430 / 472 at the sweep's white 220 / 253 (Battle
    # Stance included): base 200 / 230, x (1 + 0.10 + 0.30), + Anger Management 120 + Bloodrage 30
    truth("D36 Arms spend is 556 a minute", abs(sum(n * c for _, n, c in ARMS_SPEND) - 556) < 1e-9,
          str(sum(n * c for _, n, c in ARMS_SPEND)))
    truth("D36 Arms income is 430 at white 220 and 472 at white 253",
          round(arms_income(220.0, BATTLE_STANCE_PCT)[2]) == 430
          and round(arms_income(253.0, BATTLE_STANCE_PCT)[2]) == 472,
          f"{arms_income(220.0, BATTLE_STANCE_PCT)[2]:.1f} / {arms_income(253.0, BATTLE_STANCE_PCT)[2]:.1f}")

    # D46 Fury budget: income 512 / 557 at white 261 / 305 (x1.06 + 160 + Unbridled Wrath 45 / 44 + Bloodrage 30),
    # spend 550 / 650 of the 1.3 guide minute
    inc_start, inc_end = fury_income(261.0, 45.0)["total"], fury_income(305.0, 44.0)["total"]
    truth("D46 Fury income is 512 at white 261 and 557 at white 305",
          round(inc_start) == 512 and round(inc_end) == 557, f"{inc_start:.1f} / {inc_end:.1f}")
    truth("D46 Fury Bloodthirst income is 160 a minute", fury_income(261.0)["bloodthirst"] == 160.0)
    truth("a measured tg-* row counts its white once (factor 1.0, not 1.06)",
          fury_income(300.0, 45.0, FURY_WHITE_FACTOR_MEASURED)["white"] == 300.0
          and abs(fury_income(300.0, 45.0)["white"] - 318.0) < 1e-9)
    truth("D46 Fury spend is 550 at T0 and 650 at T3",
          fury_spend(FURY_SPEND_13, 0) == 550 and fury_spend(FURY_SPEND_13, 3) == 650,
          f"{fury_spend(FURY_SPEND_13, 0):g} / {fury_spend(FURY_SPEND_13, 3):g}")
    truth("D46 Fury gap is -38 at T0 and -93 at T3",
          round(inc_start - 550) == -38 and round(inc_end - 650) == -93, f"{inc_start - 550:.1f} / {inc_end - 650:.1f}")
    # 511.5 / 541.5 exactly: a tolerance, not round() (round-half-even would hide a 0.5 shift)
    truth("D46 pack (1.4) spend is about 512 at T0 and 542 at T3 (no Blood Rush, Cleave Bloodsurge-free)",
          abs(fury_spend(FURY_SPEND_14, 0) - 511.5) < 0.01 and abs(fury_spend(FURY_SPEND_14, 3) - 541.5) < 0.01,
          f"{fury_spend(FURY_SPEND_14, 0):g} / {fury_spend(FURY_SPEND_14, 3):g}")

    print("pipeline: synthetic reports (hand split, rates, spell-haste and attack-speed checks, measured, D15 solve)")
    _self_test_pipeline(truth, check)
    if failures:
        print(f"SELF-TEST FAILED ({len(failures)}): " + ", ".join(failures))
        return 3
    print("SELF-TEST PASSED")
    return 0


def _synthetic_report(duration_ms: int, mh: tuple[float, float], oh: tuple[float, float] | None, step_ms: int = 100,
                      crit_every: int = 5, crit_mult: float = 2.0, tag_oh: bool = False) -> dict:
    """White swings for one run: MH every mh[1] seconds at damage mh[0] (+- a small wobble), OH likewise."""
    hits = []

    def add(dmg: float, swing_s: float, phase_ms: int, tag: int, spell_id: int = 0) -> None:
        t, n = float(phase_ms), 0
        while t < duration_ms:
            n += 1
            crit = (n % crit_every == 0)
            wobble = 1.0 + 0.04 * ((n * 7 + tag) % 5 - 2) / 2.0
            d = dmg * wobble * (crit_mult if crit else 1.0)
            ts = int(round(t / step_ms) * step_ms)
            hits.append({"timestampMs": ts, "spellId": spell_id, "damage": int(round(d)), "crit": crit, "isPet": False,
                         "sourceEntry": 0, "target": 0})
            t += swing_s * 1000.0

    add(mh[0], mh[1], 1000, 0)
    if oh:
        add(oh[0], oh[1], 1500, 3, OFFHAND_WHITE_SPELL_ID if tag_oh else 0)
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

    # attack speed alone: the speed part per second is flat (a shorter swing, more of them), the damage part grows
    n0 = new_rates(s_pd, 0.0, 1.35, level, rate).total      # k = 0: speed part only
    n1 = new_rates(s_pd, 0.0, 1.35, level, rate, 1.15).total
    truth("attack speed alone leaves the speed part per second flat (k = 0, +15% attack speed)",
          abs(n1 / n0 - 1.0) < 0.01, f"x{n1 / n0:.4f}")
    # spell haste (haste rating / Bloodlust: attack speed AND spell haste): the speed part follows 1:1
    n1s = new_rates(s_pd, 0.0, 1.35, level, rate, 1.15, 1.15).total
    truth("+15% spell haste lifts the speed part per second x1.15 (k = 0)", abs(n1s / n0 - 1.15) < 0.01,
          f"x{n1s / n0:.4f}")
    n_slow = new_rates(s_pd, 0.0, 1.35, level, rate, 1.0, 0.8).total
    truth("a net slow (spell factor 0.8, cast speed 1.25) never lowers rage", abs(n_slow / n0 - 1.0) < 1e-9,
          f"x{n_slow / n0:.4f}")
    d0 = new_rates(s_pd, 1.0, 0.0, level, rate).total       # m = 0: damage term + the rounded-to-0 speed part
    d1 = new_rates(s_pd, 1.0, 0.0, level, rate, 1.15).total
    truth("damage part per second grows with the swing rate (m = 0)", abs(d1 / d0 - 1.15) < 0.01, f"x{d1 / d0:.4f}")
    # the haste check rows, both the whole-formula figure and the expectation computed from the uncapped formula
    row = haste_check_rows(s_pd, 0.43, 1.35, level, rate)
    truth("haste check: +15% spell haste gives rage/s x1.15", abs(row["spell"] / row["n0"] - 1.15) < 0.01,
          f"x{row['spell'] / row['n0']:.4f}")
    truth("haste check: +15% attack speed only gives about x1.03 (expected from the formula)",
          1.02 < row["exp_atk"] < 1.04 and abs(row["atk"] / row["n0"] - row["exp_atk"]) < 0.01,
          f"sim x{row['atk'] / row['n0']:.4f}, expected x{row['exp_atk']:.4f}")
    # a known gear haste (haste rating is spell AND attack speed): the speed part per swing is the unhasted figure
    g_pd = ProfileData("2h-start", "synthetic-haste", 1, "battle", 3.6, None, haste=0.15, haste_known=True)
    g_hit = Hit(450.0, False, False, 3.1)
    g_swing, g_spell = g_pd.swing_terms(g_hit)
    truth("gear haste 15%: true swing 3.6 / 1.15, spell factor 1.15, speed factor = the unhasted 1701",
          abs(g_swing - 3.6 / 1.15) < 1e-9 and new_speed_fixed(g_swing, False, 1.35, False, g_spell) == 1701,
          f"swing {g_swing:.4f} spell {g_spell:.2f}")
    # the profile conf's HasteRating at 10 rating per 1% (level 60)
    conf_dir = Path(__file__).resolve().parent.parent / "conf" / "profiles"
    truth("WarriorRage2HStartSim HasteRating 22 -> 2.2% haste",
          conf_haste_pct("WarriorRage2HStartSim", 60, conf_dir) == 2.2)
    if (conf_dir / "WarriorRage2HStartHasteSim.conf").is_file():
        hp = conf_haste_pct("WarriorRage2HStartHasteSim", 60, conf_dir)
        truth("WarriorRage2HStartHasteSim is about +15% over WarriorRage2HStartSim", hp is not None and
              abs((1 + hp / 100) / 1.022 - 1.15) < 0.01, f"{hp}%")
    truth("no conf haste at another level (the rating table differs)",
          conf_haste_pct("WarriorRage2HStartSim", 70, conf_dir) is None)

    _self_test_measured(truth)

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
    # tagged report (S3 recorder: off hand = spellId 0xFFFF0001): split by the tag, even when the hands hit alike
    tg = ProfileData("tg-start", "synthetic-tg-start", 2, "berserker", 3.6, 3.6)
    tg.files.append("synthetic-tagged")
    tagged_report = _synthetic_report(60000, (200, 3.55), (190, 3.45), tag_oh=True)
    add_report(tg, tagged_report, tg.files[-1], CRIT_MULT)
    want_oh = sum(1 for h in tagged_report["hits"] if h["spellId"] == OFFHAND_WHITE_SPELL_ID)
    want_mh = sum(1 for h in tagged_report["hits"] if h["spellId"] == 0)
    got_oh = sum(1 for h in tg.hits if h.off_hand)
    got_mh = sum(1 for h in tg.hits if not h.off_hand)
    truth("tagged report split by the spellId tag", (got_mh, got_oh) == (want_mh, want_oh) and got_oh > 0,
          f"MH {got_mh}/{want_mh} OH {got_oh}/{want_oh}")
    # stock gives the off hand int(2.5 x 1.75) = int(4.375) = 4
    truth("stock off-hand factor from the base speed", stock_factor(2.5, True, False) == 4)

    # a lone singular system is reported, not solved
    _, _, problem = solve_km(s_pd, s_pd, level, rate)
    truth("a singular system is refused", problem is not None, str(problem))


def _rage_series_report(duration_ms: int, swing_s: float, dmg: float, base: float, haste: float, scale: float = 1.0,
                       spend_at_ms: int | None = None, phase_ms: int = 1000, samples: bool = True) -> dict:
    """A synthetic WarriorRage report whose powerSamples are the rage the C++ formula would grant (k 0.43, m 1.35,
    Battle Stance, true swing base / (1 + haste), spell factor 1 + haste), quantised to 0.1 like the report.
    `scale` multiplies the granted rage (a broken C++ would be scale != 1); `spend_at_ms` drops 15 rage there."""
    report = _synthetic_report(duration_ms, (dmg, swing_s), None, crit_every=1000)
    report["hits"] = [h for h in report["hits"] if h["spellId"] == 0 and h["timestampMs"] >= phase_ms]
    gains = []
    for h in report["hits"]:
        factor = new_speed_fixed(base / (1.0 + haste), False, 1.35, h["crit"], 1.0 + haste)
        gains.append((h["timestampMs"], math.floor(new_rage_dealt(h["damage"], factor, 0.43, 60, True) * scale * 10)
                      / 10.0))
    if samples:
        series, power = [], 0.0
        for t in range(100, duration_ms + 1, 500):
            power += sum(g for ts, g in gains if t - 500 < ts <= t) if t > 100 else sum(g for ts, g in gains if ts <= t)
            if spend_at_ms is not None and t - 500 < spend_at_ms <= t:
                power = max(0.0, power - 15.0)
            series.append({"timestampMs": t, "powerType": 1, "power": round(power, 1), "maxPower": 100})
        report["powerSamples"] = series
    return report


def _self_test_measured(truth) -> None:
    """--measured: positive-step income, the hidden-income cases and the 5% ratio check, on synthetic fixtures."""
    def build(key: str, name: str, haste: float, swing: float, **kw) -> ProfileData:
        pd = ProfileData(key, name, 1, "battle", 3.6, None, haste=haste, haste_known=True)
        for i in range(5):
            pd.files.append(f"synthetic-{name}-{i}")
            add_report(pd, _rage_series_report(20000, swing, 300, 3.6, haste, phase_ms=1000 + 300 * i, **kw),
                       pd.files[-1], CRIT_MULT)
        return pd

    # the sim quantises swings to its 100 ms step: 3.6 / 1.022 = 3.52 s shows as 3.6, 3.6 / 1.172 = 3.07 s as 3.1
    base_pd = build("2h-start", "synthetic-start", 0.022, 3.6)
    fast_pd = build("2h-start-haste", "synthetic-haste", 0.172, 3.1)
    mi = measured_income(base_pd)
    ref = new_rates(base_pd, 0.43, 1.35, 60, 1.0).total
    truth("measured income: clean series, 500 ms windows, no spend",
          mi.ok and mi.interval_ms == 500 and mi.spend_windows == 0, mi.reason or f"{mi.per_second:.3f} rage/s")
    truth("measured income matches the reference within 3% (the 0.1 rage quantisation)",
          mi.ok and abs(mi.per_second / ref - 1.0) < 0.03, f"{mi.per_second:.3f} vs {ref:.3f}")
    profiles = {"2h-start": base_pd, "2h-start-haste": fast_pd}
    print("  -- print_measured on the clean fixtures --")
    status = print_measured(profiles, 0.43, 1.35, 60, 1.0)
    truth("hasted / unhasted measured ratio within 5% of the reference ratio (exit 0)", status == 0, f"status {status}")

    # negative fixture: the hasted run grants 15% too little rage (a broken C++ line) -> outside 5% -> exit 4
    weak_pd = build("2h-start-haste", "synthetic-haste-weak", 0.172, 3.1, scale=0.85)
    print("  -- print_measured with a hasted run 15% short (must fail) --")
    status = print_measured({"2h-start": base_pd, "2h-start-haste": weak_pd}, 0.43, 1.35, 60, 1.0)
    truth("a hasted run 15% short of the reference ratio fails the 5% check (exit 4)", status == 4, f"status {status}")

    # hidden income: a spend inside the series
    spend_pd = build("2h-start-haste", "synthetic-haste-spend", 0.172, 3.1, spend_at_ms=10250)
    mi = measured_income(spend_pd)
    truth("a spend in the series is reported as hidden income", not mi.ok and "lose rage" in mi.reason, mi.reason)
    print("  -- print_measured with a spender in the hasted run (reference only) --")
    status = print_measured({"2h-start": base_pd, "2h-start-haste": spend_pd}, 0.43, 1.35, 60, 1.0)
    truth("hidden income prints the reference only and does not fail", status == 0, f"status {status}")

    # no samples at all (an older report)
    bare = ProfileData("2h-start", "synthetic-bare", 1, "battle", 3.6, None)
    bare.files.append("synthetic-bare")
    add_report(bare, _rage_series_report(20000, 3.6, 300, 3.6, 0.0, samples=False), "synthetic-bare", CRIT_MULT)
    mi = measured_income(bare)
    truth("a report without powerSamples is reported as such", not mi.ok and "no powerSamples" in mi.reason, mi.reason)


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
    ap = argparse.ArgumentParser(description="Warrior rage sweep (W0a/W0b): stock vs dampened rage per second, "
                                             "spell-haste check, measured income.")
    for key in PROFILES:
        ap.add_argument(f"--{key}", metavar="SRC", help=f"{PROFILES[key][0]} report(s)")
    ap.add_argument("--k", type=float, help="k for the raw tables (default: WarriorData.h, else 0.43)")
    ap.add_argument("--m", type=float, help="m for the raw tables (default: WarriorData.h, else 1.35)")
    ap.add_argument("--rate", type=float, default=1.0, help="Rate.Rage.Income (default 1)")
    ap.add_argument("--level", type=int, default=LEVEL, help="character level of the reports (default 60)")
    ap.add_argument("--crit-mult", type=float, default=CRIT_MULT, help="crit damage multiplier for the hand split")
    ap.add_argument("--header", type=Path, default=repo / "src/server/game/Entities/Unit/Generated/WarriorData.h",
                    help="generated WarriorData.h to read the constants from")
    ap.add_argument("--speed", action="append", metavar="KEY=MH[/OH]",
                    help="unhasted weapon speeds in seconds for a profile, e.g. dw-end=2.6/2.8")
    ap.add_argument("--stance", action="append", metavar="KEY=battle|berserker",
                    help="the stance the bot held in a profile (default: battle for 2h, berserker for dw)")
    ap.add_argument("--haste", action="append", metavar="KEY=PCT",
                    help="gear haste in percent for a profile, taken as spell AND attack-speed haste (default: the "
                         "profile conf's HasteRating / 10 at level 60)")
    ap.add_argument("--conf-dir", type=Path, default=here.parent / "conf" / "profiles",
                    help="where the WarriorRage*Sim.conf profiles are read for their HasteRating")
    ap.add_argument("--measured", action="store_true",
                    help="rage income per second from the reports' powerSamples beside the reference, and the "
                         "hasted / unhasted ratio check (W0b D23); skips the other tables")
    ap.add_argument("--aggregate-only", action="store_true", help="use the aggregate's representative run only")
    ap.add_argument("--reports-dir", type=Path, default=here.parent / "reports")
    ap.add_argument("--fury", action="store_true", help="also print the D46 FURY BUDGET (always printed when a "
                    "tg-start / tg-end report exists)")
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

    hastes: dict[str, float] = {}
    for key, value in parse_kv(args.haste, "haste").items():
        hastes[key] = float(value)

    profiles: dict[str, ProfileData] = {}
    for key, (name, _hands, _stance, _mh, _oh) in PROFILES.items():
        files = resolve_sources(getattr(args, key.replace("-", "_")), name, args.reports_dir, args.aggregate_only)
        if not files:
            if key not in OPTIONAL_PROFILES:
                print(f"(no report found for {name} in {args.reports_dir}; skipped)")
            continue
        haste_pct = hastes.get(key, conf_haste_pct(name, args.level, args.conf_dir))
        try:
            profiles[key] = load_profile(key, files, stances.get(key), speeds.get(key), args.crit_mult, haste_pct)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"error reading {name}: {exc}", file=sys.stderr)
            return 1
    if not profiles:
        print("no reports found; run the four WarriorRage*Sim profiles first (see their headers)", file=sys.stderr)
        return 1
    print()

    print_sources(profiles)
    if args.measured:
        return print_measured(profiles, k_flag, m_flag, args.level, args.rate)
    print_raw_table(profiles, k_flag, m_flag, args.level, args.rate, "RAW RAGE TABLE at the flag constants")
    print_dw_advantage(profiles, k_flag, m_flag, args.level, args.rate, "flag constants")
    print_haste_check(profiles, k_flag, m_flag, args.level, args.rate, "flag constants")
    print_arms_budget(profiles, k_flag, m_flag, args.level, args.rate, "flag constants")
    if args.fury or "tg-start" in profiles or "tg-end" in profiles:
        print_fury_budget(profiles, k_flag, m_flag, args.level, args.rate, "flag constants")

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
    if args.fury or "tg-start" in profiles or "tg-end" in profiles:
        print_fury_budget(profiles, k_s, m_s, args.level, args.rate, "suggested constants")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
