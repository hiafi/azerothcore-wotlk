#!/usr/bin/env python3
"""
One-off DBC content patch: Shaman rework spell visuals, mined from the Ascension client backup - same source and
shape as patch_hunter_vfx_models.py, with the PersistentAreaKit pattern of patch_priest_vfx_models.py (Power Word:
Barrier, SpellVisual 90017).

ID block (shaman-rework PLAN section 4): SpellVisual / SpellVisualKit / SpellVisualEffectName 90130-90179 belong to
the Shaman rework. Sounds (SoundEntries 90081-90100) and creature displays (90440-90469) are reserved there too and
join this script when the V stage needs them.

First row set (P0 spike, kept for the V stage and the real Healing Rain): the Healing Rain ground ring.
- Ascension's live Healing Rain (SpellVisual 116162 -> PersistentAreaKit 116301 -> SpellVisualEffectName 107442)
  draws `spells\\shaman_healing_rain_proj.mdx` as the kit's WorldEffect
  (.agents/plans/shaman-rework/shaman-rework.HEALING-RAIN-VFX.md, candidate 1).
- SpellVisualEffectName 90130 "Healing Rain Ring (Custom)": the model at Scale 0.9, Min/Max pinned to the same value
  (the model is a flat ring about 23 yd across; the spell's radius is 10 yd).
- SpellVisualKit 90130: WorldEffect = SVE 90130, no sound yet (the V stage adds the loop), every "none" sentinel as
  patch_priest_vfx_models._kit_row sets it and AnimID none, as stock persistent-area kits have (Barrier 12286, Rain of
  Fire 9352).
- SpellVisual 90130: PersistentAreaKit = 90130, every other field default (Barrier SpellVisual 90017 precedent). The
  kit is read from the SpellVisual of the spell carrying the PERSISTENT_AREA_AURA effect (P0 Healing Rain 202775).

Assets (gitignored working copies in var/model-visual-dbc/SPELLS/, extracted with `smpq -x` from the Ascension
backup's patch-N.MPQ, see docs/ascension-asset-mining.md):
- shaman_healing_rain_proj.m2 + shaman_healing_rain_proj00.skin (M2 version 264, loadable by 3.3.5a). One bone, no
  particles. Its only texture, spells\\waterwake3.blp, is stock (common.MPQ SPELLS\\WATERWAKE3.BLP), so no texture
  ships.

SpellVisual is server-loaded, so `--sql-out PATH` emits its overlay. SpellVisualKit and SpellVisualEffectName are
client-only.

Usage:
    python3 apps/dbc-tools/patch_shaman_vfx_models.py
    python3 apps/dbc-tools/patch_shaman_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
    python3 apps/dbc-tools/patch_shaman_vfx_models.py --dry-run   # print rows + file list, write nothing
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib import dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, NOFIELD, _kit_row, _merge, _row, model_path

SPELLS_DIR = DBC_DIR.parent / "SPELLS"

# Shaman block for SpellVisual / SpellVisualKit / SpellVisualEffectName: 90130-90179 (PLAN section 4).
SHAMAN_VISUAL_BLOCK = {"start": 90130, "end": 90179}

EFFECT_HEALING_RAIN_RING = 90130
KIT_HEALING_RAIN_GROUND = 90130
SV_HEALING_RAIN = 90130  # spell 202775 (P0 Healing Rain); the real Healing Rain reuses it

# The model is a flat ring of radius ~11.6 yd at Scale 1.0; 0.9 puts its edge near the 10 yd spell radius.
HEALING_RAIN_RING_SCALE = 0.9

MODEL_HEALING_RAIN_RING = "shaman_healing_rain_proj"
ASSET_FILES = [
    f"{MODEL_HEALING_RAIN_RING}.m2",
    f"{MODEL_HEALING_RAIN_RING}00.skin",
]


def build_effect_name_rows() -> list[dict]:
    return [
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_HEALING_RAIN_RING,
            Name="Healing Rain Ring (Custom)", FileName=model_path(MODEL_HEALING_RAIN_RING),
            AreaEffectSize=1.0, Scale=HEALING_RAIN_RING_SCALE,
            MinAllowedScale=HEALING_RAIN_RING_SCALE, MaxAllowedScale=HEALING_RAIN_RING_SCALE,
        ),
    ]


def build_kit_rows() -> list[dict]:
    return [
        _kit_row(KIT_HEALING_RAIN_GROUND, AnimID=NOFIELD, WorldEffect=EFFECT_HEALING_RAIN_RING),
    ]


def build_spellvisual_rows() -> list[dict]:
    return [
        _row(dbcfmt.SPELLVISUAL, SV_HEALING_RAIN, PersistentAreaKit=KIT_HEALING_RAIN_GROUND),
    ]


def build_pending_sql() -> str:
    """Server-side overlay for SpellVisual only (SpellVisualKit / SpellVisualEffectName are client-only). Range-deletes
    exactly the ids this script mints, so a rerun is idempotent."""
    return _table_block(
        dbcfmt.SPELLVISUAL, {"start": SV_HEALING_RAIN, "end": SV_HEALING_RAIN}, build_spellvisual_rows(), []
    ) + "\n"


def _check_block(rows: list[dict]) -> None:
    for row in rows:
        if not SHAMAN_VISUAL_BLOCK["start"] <= row["ID"] <= SHAMAN_VISUAL_BLOCK["end"]:
            raise SystemExit(f"id {row['ID']} is outside the shaman visual block {SHAMAN_VISUAL_BLOCK}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-out", type=Path, default=None,
                        help="Write the matching server-side SQL migration to this path (see module docstring).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the rows, the asset check and the SpellVisual SQL; write nothing.")
    args = parser.parse_args()

    missing = [f for f in ASSET_FILES if not (SPELLS_DIR / f).is_file()]
    if missing:
        raise SystemExit(f"missing from {SPELLS_DIR}: {missing} - extract them from patch-N.MPQ (see docstring)")

    effect_rows = build_effect_name_rows()
    kit_rows = build_kit_rows()
    visual_rows = build_spellvisual_rows()
    for rows in (effect_rows, kit_rows, visual_rows):
        _check_block(rows)

    if args.dry_run:
        print("SpellVisualEffectName:", effect_rows[0])
        print("SpellVisualKit (non-zero fields):", {k: v for k, v in kit_rows[0].items() if v})
        print("SpellVisual (non-zero fields):", {k: v for k, v in visual_rows[0].items() if v})
        print("assets packed by build_patch_m.py at SPELLS\\:")
        for f in ASSET_FILES:
            print(f"  SPELLS\\{f} ({(SPELLS_DIR / f).stat().st_size} bytes)")
        print(build_pending_sql())
        return

    added = 0
    added += _merge(DBC_DIR / "SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME, effect_rows)
    added += _merge(DBC_DIR / "SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, kit_rows)
    added += _merge(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL, visual_rows)
    print(f"added {added} row(s) across the 3 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
