#!/usr/bin/env python3
"""
One-off DBC content patch: Warrior spell visuals that need new SpellVisual rows. Same shape as
patch_hunter_vfx_models.py (a stock row copied from the working-copy SpellVisual.dbc and edited), whose row helpers
this reuses.

ID block (ids.yaml reservation `warrior`): SpellVisual / SpellVisualKit / SpellVisualEffectName 90300-90339.

Thunder Clap Echo (Thunderstruck capstone, 200065; user ruling 2026-10-30, S1 playtest): the echo strikes where the
Thunder Clap was cast, and Thunder Clap's visual must play there, not on the warrior. Thunder Clap 6343 wears stock
SpellVisual 145:
- CastKit 356: stomp animation 181, Lightning_Cast_Hand on both hands, Spells\\ThunderClap_Cast_Base.mdx (the ring) as
  WorldEffect, sound 3090, camera shake 3. A CastKit always plays on the caster, so with 145 the echo replayed the
  whole Thunder Clap on the warrior, wherever the spell's area was.
- ImpactKit 283 (LightningBolt_Impact_Chest + sound 1506 on each target hit) and StateKit 360 (Slow_Impact_Base on
  the slowed targets).
- No area kit, so nothing of 145 can play at a destination.

SV_THUNDER_CLAP_ECHO is 145 with the CastKit cleared and InstantAreaKit = stock kit 7397: ThunderClap_Cast_Base as
WorldEffect, sound 3090, shake 3, i.e. kit 356 without the stomp animation and the hand lightning (an area kit has no
body to animate). The InstantAreaKit plays at the spell's destination, which 200065 (targets 87/16, cast by
spell_warr_thunderstruck_echo_holder at the stored spot) sends in SMSG_SPELL_GO. Stock precedent for a
ThunderClap_Cast_Base InstantAreaKit at a destination: Air Burst 32014 (targets 53/16) and Concussive Shock 71337 /
71338 (18/16) use kit 9208 (the same WorldEffect, no sound); Ball Lightning 52779 (87/16, the echo's target pair)
wears an InstantAreaKit with no CastKit. ImpactKit 283 and StateKit 360 are 145's. No new kit or model.

SpellVisual is server-loaded, so `--sql-out PATH` emits its overlay. Nothing here is a new asset.

Usage:
    python3 apps/dbc-tools/patch_warrior_vfx_models.py --dry-run   # print the row, its diff and the SQL, write nothing
    python3 apps/dbc-tools/patch_warrior_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
then build_patch_m.py (the client needs the row in patch-M as well as Spell.dbc's SpellVisualID_1 in patch-Z).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, _merge

# Warrior block for SpellVisual / SpellVisualKit / SpellVisualEffectName: 90300-90339 (ids.yaml).
SV_THUNDER_CLAP_ECHO = 90300  # spell 200065

# --- Stock IDs reused as-is ---
STOCK_THUNDER_CLAP_SV = 145        # Thunder Clap 6343: CastKit 356, ImpactKit 283, StateKit 360
KIT_THUNDER_CLAP_AREA_STOCK = 7397  # WorldEffect 349 ThunderClap_Cast_Base, sound 3090, shake 3 (kit 356 minus body)


def _stock_spellvisual(sv_id: int) -> dict:
    return next(r for r in dbcfile.read_dbc(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL) if r["ID"] == sv_id)


def build_spellvisual_rows() -> list[dict]:
    echo = dict(_stock_spellvisual(STOCK_THUNDER_CLAP_SV))
    echo["ID"] = SV_THUNDER_CLAP_ECHO
    echo["CastKit"] = 0
    echo["InstantAreaKit"] = KIT_THUNDER_CLAP_AREA_STOCK
    return [echo]


def build_pending_sql() -> str:
    """Server-side overlay for SpellVisual only."""
    return _table_block(
        dbcfmt.SPELLVISUAL, {"start": SV_THUNDER_CLAP_ECHO, "end": SV_THUNDER_CLAP_ECHO}, build_spellvisual_rows(), []
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-out", type=Path, default=None,
                        help="Write the matching server-side SQL migration to this path (see module docstring).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the row, its diff against SpellVisual 145 and the SQL; write nothing.")
    args = parser.parse_args()

    kits = {r["ID"] for r in dbcfile.read_dbc(DBC_DIR / "SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT)}
    if KIT_THUNDER_CLAP_AREA_STOCK not in kits:
        raise SystemExit(f"stock kit {KIT_THUNDER_CLAP_AREA_STOCK} missing from the working-copy SpellVisualKit.dbc")

    if args.dry_run:
        stock = _stock_spellvisual(STOCK_THUNDER_CLAP_SV)
        new_sv = build_spellvisual_rows()[0]
        print(f"SpellVisual {SV_THUNDER_CLAP_ECHO} vs stock {STOCK_THUNDER_CLAP_SV}, differing fields:")
        for k in stock:
            if stock[k] != new_sv[k]:
                print(f"  {k}: {stock[k]} -> {new_sv[k]}")
        print(build_pending_sql())
        return

    added = _merge(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL, build_spellvisual_rows())
    print(f"added {added} row(s) to the working-copy SpellVisual.dbc (0 means it already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
