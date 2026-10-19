#!/usr/bin/env python3
"""
One-off DBC content patch: mints a SpellVisualEffectName row and a SpellVisual row for the Hunter
rework's Glaive Toss (201600), mined from the Ascension client backup - same source and shape as
patch_warlock_vfx_models.py. Every other hunter visual waits for the visuals stage (PLAN V1-V3).

Glaive Toss used stock SpellVisual 9044 (spell 39635 "Throw Glaive"): HasMissile, MissileModel 3538
(SpellVisualEffectName "Missile: Illidan's Glaive", Scale 1.35), MissileMotion 221, MissileAttachment 3,
MissileDestinationAttachment 1, MissileSound 11649, and no kits. The new SpellVisual is a copy of that
row read from the working-copy SpellVisual.dbc, with only MissileModel swapped for the Council of
Ascension's twilight glaive, so the flight path, attachments and sound are exactly what Speed 40
already gave Throw Glaive.

Assets (gitignored working copies in var/model-visual-dbc/SPELLS/, extracted from patch-N.MPQ with
`smpq -x`, see docs/ascension-asset-mining.md):
- 7fx_necouncil_twilightglaive_state.m2 + 7fx_necouncil_twilightglaive_state00.skin (M2 version 264,
  loadable by 3.3.5a). One bone, no particles or ribbons; bounds 1.48 x 1.48 x 0.14 yd (a flat disc).
  Its name says "state", but as a missile model it just plays its stand animation along the path.
- glaive_1h_councilsentinel_c_01.blp and armorreflect4.blp: its two textures, both hard-coded to
  spells\\ paths. Neither exists under SPELLS\\ in the stock 3.3.5a client (armorreflect4 only exists
  under ITEM\\OBJECTCOMPONENTS\\WEAPON\\ etc.), so both ship in patch-M.

SpellVisual is server-loaded, so `--sql-out PATH` emits its overlay, same as the Warlock script.
SpellVisualEffectName is client-only.

Usage:
    python3 apps/dbc-tools/patch_hunter_vfx_models.py
    python3 apps/dbc-tools/patch_hunter_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
    python3 apps/dbc-tools/patch_hunter_vfx_models.py --dry-run   # print rows + file list, write nothing
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib import dbcfmt, dbcfile
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, _merge, _row, model_path

SPELLS_DIR = DBC_DIR.parent / "SPELLS"

# Hunter block for SpellVisual / SpellVisualKit / SpellVisualEffectName: 90090-90129.
STOCK_THROW_GLAIVE_SV = 9044

EFFECT_GLAIVE_TOSS_MISSILE = 90090
SV_GLAIVE_TOSS = 90090  # spell 201600

# Cluster Bombs (202051 first blast + 202052 follow-ups): stock SV 148 ("Rough Dynamite", a ground-thrown bomb) with the
# missile and the precast/cast kits stripped, leaving its ImpactKit 213 and ImpactAreaKit 9318 (the dynamite explosion on the units and on the ground). Each of the five
# blasts is its own cast at its own destination, so each plays one explosion at its point.
STOCK_DYNAMITE_SV = 148
SV_CLUSTER_BOMB_BLAST = 90091  # spells 202051, 202052

# Scale 1.0 = a ~1.5 yd flat disc; stock Illidan's glaive (the old missile) uses 1.35. Pinned by Min/Max.
GLAIVE_SCALE = 1.0

MODEL = "7fx_necouncil_twilightglaive_state"
ASSET_FILES = [
    f"{MODEL}.m2",
    f"{MODEL}00.skin",
    "glaive_1h_councilsentinel_c_01.blp",
    "armorreflect4.blp",
]


def build_effect_name_rows() -> list[dict]:
    return [
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_GLAIVE_TOSS_MISSILE,
            Name="Glaive Toss Missile (Custom)", FileName=model_path(MODEL),
            AreaEffectSize=1.0, Scale=GLAIVE_SCALE, MinAllowedScale=GLAIVE_SCALE, MaxAllowedScale=GLAIVE_SCALE,
        ),
    ]


def build_spellvisual_rows() -> list[dict]:
    stock = next(r for r in dbcfile.read_dbc(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL)
                 if r["ID"] == STOCK_THROW_GLAIVE_SV)
    row = dict(stock)
    row["ID"] = SV_GLAIVE_TOSS
    row["MissileModel"] = EFFECT_GLAIVE_TOSS_MISSILE

    dynamite = next(r for r in dbcfile.read_dbc(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL)
                    if r["ID"] == STOCK_DYNAMITE_SV)
    blast = dict(dynamite)
    blast["ID"] = SV_CLUSTER_BOMB_BLAST
    for field in ("PrecastKit", "CastKit", "StateKit", "HasMissile", "MissileModel"):
        blast[field] = 0
    return [row, blast]


def build_pending_sql() -> str:
    """Server-side overlay for SpellVisual only (SpellVisualEffectName is client-only)."""
    return _table_block(
        dbcfmt.SPELLVISUAL, {"start": SV_GLAIVE_TOSS, "end": SV_CLUSTER_BOMB_BLAST}, build_spellvisual_rows(), []
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-out", type=Path, default=None,
                        help="Write the matching server-side SQL migration to this path (see module docstring).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the rows, the diff against SpellVisual 9044 and the asset check; write nothing.")
    args = parser.parse_args()

    missing = [f for f in ASSET_FILES if not (SPELLS_DIR / f).is_file()]
    if missing:
        raise SystemExit(f"missing from {SPELLS_DIR}: {missing} - extract them from patch-N.MPQ (see docstring)")

    if args.dry_run:
        stock = next(r for r in dbcfile.read_dbc(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL)
                     if r["ID"] == STOCK_THROW_GLAIVE_SV)
        new_sv = build_spellvisual_rows()[0]
        print("SpellVisualEffectName:", build_effect_name_rows()[0])
        print(f"SpellVisual {SV_GLAIVE_TOSS} vs stock {STOCK_THROW_GLAIVE_SV}, differing fields:")
        for k in stock:
            if stock[k] != new_sv[k]:
                print(f"  {k}: {stock[k]} -> {new_sv[k]}")
        print("assets packed by build_patch_m.py at SPELLS\\:")
        for f in ASSET_FILES:
            print(f"  SPELLS\\{f} ({(SPELLS_DIR / f).stat().st_size} bytes)")
        print(build_pending_sql())
        return

    added = 0
    added += _merge(DBC_DIR / "SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME, build_effect_name_rows())
    added += _merge(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL, build_spellvisual_rows())
    print(f"added {added} row(s) across the 2 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
