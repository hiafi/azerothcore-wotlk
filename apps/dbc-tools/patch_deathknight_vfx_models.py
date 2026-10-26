#!/usr/bin/env python3
"""
One-off DBC content patch: Death Knight spell visuals that need new SpellVisual / SpellVisualKit /
SpellVisualEffectName rows. Same shape as patch_druid_vfx_models.py (whose row helpers this reuses).

ID block (ids.yaml reservation `deathknight`): SpellVisual / SpellVisualKit / SpellVisualEffectName 90180-90249.

Hungering Cold storm (Frost S2a): aura 203315 on the Death Knight for 10 s, ticking 203316 every 2 s (8 yd around the
Death Knight). History and root cause (.agents/plans/death-knight-rework/death-knight-rework.HC-VISUAL-REPORT.md):
- Stock SpellVisual 14540 (Snow Tempest State) was a 145 yd plane, far too big.
- The first fix put the mage's Blizzard_Spawn.mdx on the aura's StateKit. Playtest: "one effect per monster per tick,
  more like Starfall". Blizzard_Spawn is not what makes mage Blizzard look like Blizzard. It is a faint ground mist
  (NEXUS_ICEBEAM_FAINT particles, ~5.5 yd, plus three ring flares on birth). The ice that rains across the area comes
  from mage Blizzard's PersistentAreaKit 9350: CharProc 9 is the client's "area model" proc. CharParamZero_1 is an
  EnumID in SpellVisualKitAreaModel.dbc, where 0 = Spells\\Blizzard_Impact_Base.mdx (the big falling ice shard), and
  CharParamOne_1 (5.0) is the density. With that proc missing, only the tick's TargetImpactKit 413 showed: the same
  shard, once per enemy per tick.

Now:
- The storm (SpellVisual 90180 on 203315): the StateKit wears Ascension's DeathKnight_RemorselessWinter_State.m2, the
  retail Remorseless Winter storm built to sit on and follow its caster. Ascension wires it the same way on Ward of
  Winter 2140155 (a self aura with a periodic trigger -> SpellVisual 220056 -> StateKit BaseEffect). It has the
  Stand (birth) / Hold (loop) / Decay sequences that stock state models such as Snow_Tempest_State use. At Scale 1.0
  its Hold ground disk is ~7.9 yd across the radius (bone 0 at 53.77 x a 0.146 yd quad), a ring pulses out to ~8.6 yd
  every 0.83 s, and a snow column ~2.8 yd wide swirls round the Death Knight. HUNGERING_COLD_STORM_SCALE sizes it.
  Loop sound 1136 is the mage Blizzard channel's (the same wav as Ascension's 17456, at 8 / 45 yd distances).
- The tick (SpellVisual 90181 on 203316): stock Blizzard tick 9487 (TargetImpactKit 413, the per-target shard) plus
  an InstantAreaKit 90181 that copies stock kit 609 / 9350: CharProc 9, EnumID 0, density
  HUNGERING_COLD_SHARD_DENSITY, sound 7. Stock precedent: Summon Blizzard 29969 (TARGET_SRC_CASTER area) uses
  InstantAreaKit 609, and the Rain of Fire tick 42223 uses InstantAreaKit 9160. The tick is TARGET_UNIT_SRC_AREA_ENEMY
  with the Death Knight as the source, so every tick showers shards across the area wherever the Death Knight stands.

Assets (gitignored working copies in var/model-visual-dbc/SPELLS/, extracted with `smpq -x` from the Ascension
backup's patch-N.MPQ, docs/ascension-asset-mining.md Part 3): the model + its skin (M2 version 264, every sequence
inline, no .anim) and the 3 of its 7 textures stock 3.3.5a lacks. snow_shield3, frost128coneofcold,
textures\\beam_smokegrey and world\\expansion01\\...\\shockwavewater1extreme are stock (common.MPQ / patch.MPQ).

SpellVisual is server-loaded, so `--sql-out PATH` emits its overlay. SpellVisualKit and SpellVisualEffectName are
client-only.

Usage:
    python3 apps/dbc-tools/patch_deathknight_vfx_models.py
    python3 apps/dbc-tools/patch_deathknight_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
    python3 apps/dbc-tools/patch_deathknight_vfx_models.py --dry-run   # print rows + asset check, write nothing
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib import dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, NOFIELD, _kit_row, _merge, _row, model_path

SPELLS_DIR = DBC_DIR.parent / "SPELLS"

# Death Knight block for SpellVisual / SpellVisualKit / SpellVisualEffectName: 90180-90249 (ids.yaml).
DEATHKNIGHT_VISUAL_BLOCK = {"start": 90180, "end": 90249}

EFFECT_HUNGERING_COLD_STORM = 90180
KIT_HUNGERING_COLD_STORM = 90180
KIT_HUNGERING_COLD_SHARDS = 90181
SV_HUNGERING_COLD_STORM = 90180  # spell 203315 (the storm aura on the Death Knight)
SV_HUNGERING_COLD_TICK = 90181   # spell 203316 (the 2 s tick, 8 yd around the Death Knight)

# The storm model's Hold ground disk reaches ~7.9 yd at Scale 1.0; the storm radius is 8 yd.
HUNGERING_COLD_STORM_SCALE = 1.0
# Shards per tick shower: CharParamOne_1 of the area-model proc, 5.0 as in mage Blizzard (kit 9350) and kit 609.
HUNGERING_COLD_SHARD_DENSITY = 5.0

# --- Stock IDs reused as-is ---
KIT_BLIZZARD_SHARD_ON_TARGET_STOCK = 413  # Blizzard tick 9487's TargetImpactKit: Blizzard Impact Base + sound 7
SOUND_BLIZZARD_CHANNEL_LOOP_STOCK = 1136  # "Precast Frost High", looping (Flags 512), mage Blizzard ChannelKit 717
SOUND_BLIZZARD_IMPACTS_STOCK = 7          # "BlizzardImpactVariations", kits 413 / 609 / 9350
CHAR_PROC_AREA_MODEL = 9                  # spawns SpellVisualKitAreaModel models across the spell's area
AREA_MODEL_BLIZZARD_SHARD = 0.0           # SpellVisualKitAreaModel EnumID 0 = Spells\\Blizzard_Impact_Base.mdx
MISSILE_DESTINATION_CHEST = 1             # as stock 9487
NO_ATTACHMENT = -1                        # SpellVisual's signed "none" (dbcfmt.SPELLVISUAL.signed)

MODEL_HUNGERING_COLD_STORM = "deathknight_remorselesswinter_state"
ASSET_FILES = [
    f"{MODEL_HUNGERING_COLD_STORM}.m2",
    f"{MODEL_HUNGERING_COLD_STORM}00.skin",
    "t_vfx_flare05b.blp",
    "snow_shield4.blp",
    "gradient_03.blp",
]


def build_effect_name_rows() -> list[dict]:
    return [
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_HUNGERING_COLD_STORM,
            Name="Hungering Cold Storm (Remorseless Winter State, Custom)",
            FileName=model_path(MODEL_HUNGERING_COLD_STORM),
            AreaEffectSize=1.0, Scale=HUNGERING_COLD_STORM_SCALE,
            MinAllowedScale=HUNGERING_COLD_STORM_SCALE, MaxAllowedScale=HUNGERING_COLD_STORM_SCALE,
        ),
    ]


def build_kit_rows() -> list[dict]:
    return [
        _kit_row(
            KIT_HUNGERING_COLD_STORM,
            AnimID=NOFIELD, BaseEffect=EFFECT_HUNGERING_COLD_STORM, SoundID=SOUND_BLIZZARD_CHANNEL_LOOP_STOCK,
        ),
        _kit_row(
            KIT_HUNGERING_COLD_SHARDS,
            AnimID=NOFIELD, SoundID=SOUND_BLIZZARD_IMPACTS_STOCK,
            CharProc_1=CHAR_PROC_AREA_MODEL, CharParamZero_1=AREA_MODEL_BLIZZARD_SHARD,
            CharParamOne_1=HUNGERING_COLD_SHARD_DENSITY,
        ),
    ]


def build_spellvisual_rows() -> list[dict]:
    return [
        _row(
            dbcfmt.SPELLVISUAL, SV_HUNGERING_COLD_STORM,
            StateKit=KIT_HUNGERING_COLD_STORM,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_HUNGERING_COLD_TICK,
            TargetImpactKit=KIT_BLIZZARD_SHARD_ON_TARGET_STOCK, InstantAreaKit=KIT_HUNGERING_COLD_SHARDS,
            MissileDestinationAttachment=MISSILE_DESTINATION_CHEST, MissileAttachment=NO_ATTACHMENT,
        ),
    ]


def build_pending_sql() -> str:
    """Server-side overlay for SpellVisual only (SpellVisualKit / SpellVisualEffectName are client-only). Range-deletes
    exactly the ids this script mints, so a rerun is idempotent."""
    return _table_block(
        dbcfmt.SPELLVISUAL, {"start": SV_HUNGERING_COLD_STORM, "end": SV_HUNGERING_COLD_TICK},
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
        for row in effect_rows:
            print("SpellVisualEffectName:", row)
        for row in kit_rows:
            print("SpellVisualKit (non-zero fields):", {k: v for k, v in row.items() if v})
        for row in visual_rows:
            print("SpellVisual (non-zero fields):", {k: v for k, v in row.items() if v})
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
