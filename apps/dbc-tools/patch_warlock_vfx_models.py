#!/usr/bin/env python3
"""
One-off DBC content patch: mints SpellVisual.dbc / SpellVisualKit.dbc / SpellVisualEffectName.dbc /
SoundEntries.dbc rows for the Warlock rework's Hand of Gul'dan (200820), mined from the Ascension
client backup - same source and shape as patch_druid_vfx_models.py.

What Ascension ships, traced from its own Spell.dbc:
- Hand of Gul'dan 954611 (target 6, summons imps, like ours) -> SpellVisual 21894: stock Shadow
  "Uber" hand flares on Precast/Cast (its kits 106818/106778 are stock kits 6818/6778 with the
  effect ID shifted by 100000), an InstantAreaKit with warlock_handofguldan_missile_01 (the falling
  fel meteor) and an ImpactAreaKit with warlock_handofguldan_state_01 (the crater, Scale 1.5).
- Our 200820 is a plain unit-target spell with no destination, so the area kits would have no
  location to play at. Both models go on one ImpactKit on the target instead - WorldEffect for the
  meteor (as Ascension's own unit-target HoG 2304611 does in its SpellVisual 30008) and BaseEffect
  for the crater. Ascension plays the two at the same moment too (its spell has no travel time).
- Ascension's crater kit carries the looping spell_wl_handofguldan_loop (23252), which on an
  ImpactKit would never stop, so the one-shot impact set (Ascension 23253) is used instead.

Assets (gitignored working copies, extracted by hand via `smpq -x`, see
docs/ascension-asset-mining.md):
- var/model-visual-dbc/SPELLS/: both models + their 00.skin (patch-N.MPQ) and
  lavaground_purple.blp. The meteor's other textures are stock except one.
- var/model-visual-dbc/EXTRA/World/Generic/Goblin/PassiveDoodads/Kezan/Items/tooncloud64b.blp:
  the meteor's smoke texture, hard-coded at that Cataclysm path (patch-Z.MPQ).
- var/model-visual-dbc/SOUND/: spell_wl_handofguldan_impact_01-10 (patch-O.MPQ), .ogg -> .wav.

Summon Infernal (200833) needs nothing here: it uses stock Inferno's SpellVisual 4859 (green
meteor on its InstantAreaKit) directly in warlock_spells.py.

Burning Rush (200738) gets a stock-kits-only SpellVisual: the speed ribbon it already had (stock SV
5926's ImpactKit 696) plus a StateKit for the flames at the feet while the toggle is on - stock kit
235 (Immolate_State_Base + body glow + burn loop), the same one Immolate's own SV 46 uses. No mining.

SoundEntries rows ship client-only; SpellVisual is server-loaded, so `--sql-out PATH` emits its
overlay, same as the Priest/Druid scripts.

Usage:
    python3 apps/dbc-tools/patch_warlock_vfx_models.py
    python3 apps/dbc-tools/patch_warlock_vfx_models.py --sql-out data/sql/updates/pending_db_world/rev_<ts>.sql
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib import dbcfmt
from lib.sql_out import _table_block
from patch_priest_vfx_models import DBC_DIR, NOFIELD, _kit_row, _merge, _row, _sound_row, model_path

# --- Stock IDs reused as-is ---

KIT_SHADOW_UBER_PRECAST_STOCK = 6818  # anim 51 + Shadow_Precast_Uber_Hand, sound 745
KIT_SHADOW_UBER_CAST_STOCK = 6778     # anim 54 + Shadow_Precast_Uber_Hand, sound 2560
KIT_RIBBON_TRAIL_STOCK = 696          # RibbonTrail chest, sound 1577 (stock SV 5926's ImpactKit)
KIT_IMMOLATE_STATE_STOCK = 235        # Immolate_State_Base + orange glow, sound 5015 (stock SV 46)
NO_ATTACHMENT = -1                    # SpellVisual's signed "none" (dbcfmt.SPELLVISUAL.signed)

# --- SoundEntries.dbc (warlock range 90011-90030) ---

SOUND_HAND_OF_GULDAN_IMPACT = 90011


def build_sound_rows() -> list[dict]:
    return [
        _sound_row(
            SOUND_HAND_OF_GULDAN_IMPACT, "spell_wl_handofguldan_impact",
            [f"spell_wl_handofguldan_impact_{i:02d}" for i in range(1, 11)],
            min_distance=10.0, cutoff=65.0,
        ),
    ]


# --- SpellVisualEffectName.dbc (warlock range 90024+) ---

EFFECT_HAND_OF_GULDAN_MISSILE = 90024
EFFECT_HAND_OF_GULDAN_STATE = 90025


def build_effect_name_rows() -> list[dict]:
    # Scales are Ascension's own (effect names 208076 / 112088), pinned by Min/MaxAllowedScale.
    return [
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_HAND_OF_GULDAN_MISSILE,
            Name="Hand of Gul'dan Missile (Custom)", FileName=model_path("Warlock_Handofguldan_Missile_01"),
            AreaEffectSize=1.0, Scale=1.0, MinAllowedScale=1.0, MaxAllowedScale=1.0,
        ),
        _row(
            dbcfmt.SPELLVISUALEFFECTNAME, EFFECT_HAND_OF_GULDAN_STATE,
            Name="Hand of Gul'dan State (Custom)", FileName=model_path("Warlock_Handofguldan_State_01"),
            AreaEffectSize=1.0, Scale=1.5, MinAllowedScale=1.5, MaxAllowedScale=1.5,
        ),
    ]


# --- SpellVisualKit.dbc (warlock range 90025+) ---

KIT_HAND_OF_GULDAN_IMPACT = 90025


def build_kit_rows() -> list[dict]:
    return [
        _kit_row(
            KIT_HAND_OF_GULDAN_IMPACT,
            AnimID=NOFIELD, WorldEffect=EFFECT_HAND_OF_GULDAN_MISSILE, BaseEffect=EFFECT_HAND_OF_GULDAN_STATE,
            SoundID=SOUND_HAND_OF_GULDAN_IMPACT,
        ),
    ]


# --- SpellVisual.dbc (warlock range 90025+) ---

SV_HAND_OF_GULDAN = 90025  # spell 200820
SV_BURNING_RUSH = 90026    # spell 200738


def build_spellvisual_rows() -> list[dict]:
    return [
        _row(
            dbcfmt.SPELLVISUAL, SV_HAND_OF_GULDAN,
            PrecastKit=KIT_SHADOW_UBER_PRECAST_STOCK, CastKit=KIT_SHADOW_UBER_CAST_STOCK,
            ImpactKit=KIT_HAND_OF_GULDAN_IMPACT, Flags=512,
            MissileDestinationAttachment=NO_ATTACHMENT, MissileAttachment=NO_ATTACHMENT,
        ),
        _row(
            dbcfmt.SPELLVISUAL, SV_BURNING_RUSH,
            ImpactKit=KIT_RIBBON_TRAIL_STOCK, StateKit=KIT_IMMOLATE_STATE_STOCK,
            MissileAttachment=NO_ATTACHMENT,
        ),
    ]


def build_pending_sql() -> str:
    """Server-side overlay for SpellVisual only - see the module docstring for SoundEntries."""
    return _table_block(
        dbcfmt.SPELLVISUAL, {"start": SV_HAND_OF_GULDAN, "end": SV_BURNING_RUSH}, build_spellvisual_rows(), []
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sql-out", type=Path, default=None,
        help="Write the matching server-side SQL migration to this path (see module docstring).",
    )
    args = parser.parse_args()

    added = 0
    added += _merge(DBC_DIR / "SoundEntries.dbc", dbcfmt.SOUNDENTRIES, build_sound_rows())
    added += _merge(DBC_DIR / "SpellVisualEffectName.dbc", dbcfmt.SPELLVISUALEFFECTNAME, build_effect_name_rows())
    added += _merge(DBC_DIR / "SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT, build_kit_rows())
    added += _merge(DBC_DIR / "SpellVisual.dbc", dbcfmt.SPELLVISUAL, build_spellvisual_rows())
    print(f"added {added} row(s) across the 4 working-copy DBCs (0 means everything already existed)")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql())
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
