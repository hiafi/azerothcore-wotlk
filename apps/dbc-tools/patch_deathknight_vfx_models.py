#!/usr/bin/env python3
"""
One-off DBC content patch: Death Knight spell visuals that need new SpellVisual / SpellVisualKit /
SpellVisualEffectName rows. Same shape as patch_druid_vfx_models.py (whose row helpers this reuses).

ID block (ids.yaml reservation `deathknight`): SpellVisual / SpellVisualKit / SpellVisualEffectName 90180-90249.

Hungering Cold storm (Frost S2a, aura 203315). Playtest: the stock SpellVisual 14540 (Cyclone Caster State Scaled +
Snow Tempest State) was far too big. Snow_Tempest_State.m2 is a 145 yd wide blizzard plane (vertices out to +-72 yd);
it was meant for a boss arena, not an 8 yd storm. It now wears the mage's Blizzard look instead.

What Blizzard does (stock Spell.dbc, spell 10 -> SpellVisual 9490, tick 42208 -> SpellVisual 9487):
- 9490 draws the storm with ImpactAreaKit 13152, a WorldEffect of SpellVisualEffectName 5721 "Blizzard Spawn"
  (Spells\\Blizzard_Spawn.mdx): the cloud and its falling ice. An ImpactAreaKit only plays where a ground-targeted
  spell lands, and the PersistentAreaKit (9350) carries only a sound, so the cloud cannot ride on a self aura as is.
- 9487 (the tick) gives each damaged target the "Blizzard Impact Base" ice burst (TargetImpactKit 413).
The workaround is the one Fury of Elune uses (patch_druid_vfx_models.py): the same model goes on the aura's StateKit
as a BaseEffect, so the cloud sits on the Death Knight for the aura's life and follows it. The tick 203316 takes the
stock Blizzard tick visual 9487 as is.

Blizzard_Spawn.m2 (patch-2.MPQ) is stock, no asset ships. Its header bounding box is about +-10 yd wide and 10-18 yd
above the origin at Scale 1.0, which is what the 8 yd Blizzard looks like in game. EffectName 90180 re-points the same
file at HUNGERING_COLD_STORM_SCALE (0.8 = 8 yd / ~10 yd) so the size is one constant to retune.

SpellVisual is server-loaded, so `--sql-out PATH` emits its overlay. SpellVisualKit and SpellVisualEffectName are
client-only. Nothing else in the Death Knight kit needs a row yet.

Usage:
    python3 apps/dbc-tools/patch_deathknight_vfx_models.py
    python3 apps/dbc-tools/patch_deathknight_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
    python3 apps/dbc-tools/patch_deathknight_vfx_models.py --dry-run   # print rows, write nothing
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib import dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, NOFIELD, _kit_row, _merge, _row

# Death Knight block for SpellVisual / SpellVisualKit / SpellVisualEffectName: 90180-90249 (ids.yaml).
DEATHKNIGHT_VISUAL_BLOCK = {"start": 90180, "end": 90249}

NO_ATTACHMENT = -1  # SpellVisual's signed "none" (dbcfmt.SPELLVISUAL.signed)

EFFECT_HUNGERING_COLD_STORM = 90180
KIT_HUNGERING_COLD_STORM = 90180
SV_HUNGERING_COLD_STORM = 90180  # spell 203315 (the storm aura on the Death Knight)

# Blizzard Spawn's own EffectName 5721 draws it at Scale 1.0, about +-10 yd; the storm radius is 8 yd.
HUNGERING_COLD_STORM_SCALE = 0.8
BLIZZARD_SPAWN_FILE = "Spells\\Blizzard_Spawn.mdx"  # stock path as SpellVisualEffectName 5721 spells it


def build_effect_name_rows() -> list[dict]:
    return [
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_HUNGERING_COLD_STORM,
            Name="Hungering Cold Storm (Blizzard Spawn, Custom)", FileName=BLIZZARD_SPAWN_FILE,
            AreaEffectSize=1.0, Scale=HUNGERING_COLD_STORM_SCALE,
            MinAllowedScale=HUNGERING_COLD_STORM_SCALE, MaxAllowedScale=HUNGERING_COLD_STORM_SCALE,
        ),
    ]


def build_kit_rows() -> list[dict]:
    return [
        _kit_row(KIT_HUNGERING_COLD_STORM, AnimID=NOFIELD, BaseEffect=EFFECT_HUNGERING_COLD_STORM),
    ]


def build_spellvisual_rows() -> list[dict]:
    return [
        _row(
            dbcfmt.SPELLVISUAL, SV_HUNGERING_COLD_STORM,
            StateKit=KIT_HUNGERING_COLD_STORM,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
    ]


def build_pending_sql() -> str:
    """Server-side overlay for SpellVisual only (SpellVisualKit / SpellVisualEffectName are client-only). Range-deletes
    exactly the ids this script mints, so a rerun is idempotent."""
    return _table_block(
        dbcfmt.SPELLVISUAL, {"start": SV_HUNGERING_COLD_STORM, "end": SV_HUNGERING_COLD_STORM},
        build_spellvisual_rows(), [],
    ) + "\n"


def _check_block(rows: list[dict]) -> None:
    for row in rows:
        if not DEATHKNIGHT_VISUAL_BLOCK["start"] <= row["ID"] <= DEATHKNIGHT_VISUAL_BLOCK["end"]:
            raise SystemExit(f"id {row['ID']} is outside the Death Knight visual block {DEATHKNIGHT_VISUAL_BLOCK}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-out", type=Path, default=None,
                        help="Write the matching server-side SQL migration to this path (see module docstring).")
    parser.add_argument("--dry-run", action="store_true", help="Print the rows and the SQL; write nothing.")
    args = parser.parse_args()

    effect_rows = build_effect_name_rows()
    kit_rows = build_kit_rows()
    visual_rows = build_spellvisual_rows()
    for rows in (effect_rows, kit_rows, visual_rows):
        _check_block(rows)

    if args.dry_run:
        print("SpellVisualEffectName:", effect_rows[0])
        print("SpellVisualKit (non-zero fields):", {k: v for k, v in kit_rows[0].items() if v})
        print("SpellVisual (non-zero fields):", {k: v for k, v in visual_rows[0].items() if v})
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
