#!/usr/bin/env python3
"""
Priest baseline rework (docs/reworks/priest-new-spells.md): mints new SpellIcon.dbc rows for the 5
new spells that needed real icon art (Power Word: Barrier already has a matching stock icon,
3837 - see priest_spells.py's own notes on that spell - so it isn't touched here), then packages
the underlying .blp files into patch-I.mpq and deploys it.

Implements docs/ascension-asset-mining.md Part 1's recommended pipeline (extract -> pack -> add
DBC rows), scoped narrowly to the 5 files this pass actually needs rather than the full 76k-icon
archive. Same "hand-edit the working-copy DBC via dbcfmt.py's table definitions, outside
generate.py's own source/*.csv pipeline" pattern patch_mage_vfx_models.py already established for
SpellVisual*/CreatureModelData/CreatureDisplayInfo - see lib/dbcfmt.py's own SPELLICON comment for
why this table needs its own bootstrap (it has no DBCfmt.h entry at all; the server never loads it,
so there's no matching SQL overlay table either, unlike those three).

Source archive: an Ascension private-server client backup at
/mnt/drive6/Permaseeds/AscensionBackup/Data/patch-I.MPQ (per docs/ascension-asset-mining.md - "I" =
Icons, 100% Interface/icons/*.blp, nothing else). Confirmed via `smpq -l` to contain real matches
for Angelic Feather/Divine Star/Halo/Leap of Faith/Void Eruption (the last shared with its own
"Voidform" buff, since no exact "voideruption" icon exists there and retail shares that icon
between the two anyway).

Custom SpellIcon.dbc ID convention established here (nothing documented it before - see
docs/ascension-asset-mining.md's own note on this gap): starts at 90100, offset from
CreatureModelData/CreatureDisplayInfo's existing 90001+/90002+ convention (a different DBC table,
so no actual collision risk either way, but a distinct round number avoids visual confusion between
the two custom ranges when reading notes/comments side by side).

Usage:
    python3 apps/dbc-tools/build_patch_i.py [--source-mpq PATH] [--deploy-root PATH]

    --source-mpq     Ascension patch-I.MPQ to extract icons from (default: the path above).
    --deploy-root    patch-service PATCH_ROOT to copy patch-I.mpq's Data/ into (default: this
                      box's DEPLOY_ROOT from lib/local_config.py, or no deployment if that file
                      doesn't exist). Pass --deploy-root '' to skip deployment and only (re)build
                      apps/dbc-tools/var/dbc-patch/patch-I.mpq locally.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.mpq_writer import write_mpq

DEFAULT_SOURCE_MPQ = Path("/mnt/drive6/Permaseeds/AscensionBackup/Data/patch-I.MPQ")
WORKING_DBC_DIR = Path(__file__).resolve().parent / "var" / "model-visual-dbc" / "DBFilesClient"
SPELLICON_DBC = WORKING_DBC_DIR / "SpellIcon.dbc"
STOCK_SPELLICON_CSV = Path(__file__).resolve().parent / "var" / "spell_icon_names.csv"
LOCAL_OUT = Path(__file__).resolve().parent / "var" / "dbc-patch" / "patch-I.mpq"

try:
    from lib.local_config import DEPLOY_ROOT as DEFAULT_DEPLOY_ROOT
except ImportError:
    DEFAULT_DEPLOY_ROOT = None

# (custom SpellIcon ID, archive-relative source path in the Ascension backup, this project's own
# spell() var name + file it lives in - for the human reading this table, not read by the script)
ICON_ID_ANGELIC_FEATHER = 90100
ICON_ID_DIVINE_STAR = 90101
ICON_ID_HALO = 90102
ICON_ID_LEAP_OF_FAITH = 90103
ICON_ID_VOID_ERUPTION = 90104  # shared by void_eruption_200139 and void_eruption_buff_200140

ICONS = (
    (ICON_ID_ANGELIC_FEATHER, "Interface/icons/ability_priest_angelicfeather.blp"),
    (ICON_ID_DIVINE_STAR, "Interface/icons/spell_priest_divinestar.blp"),
    (ICON_ID_HALO, "Interface/icons/ability_priest_halo.blp"),
    (ICON_ID_LEAP_OF_FAITH, "Interface/icons/priest_spell_leapoffaith_a.blp"),
    (ICON_ID_VOID_ERUPTION, "Interface/icons/spell_priest_voidform.blp"),
)


def _find_smpq() -> str:
    smpq = shutil.which("smpq")
    if not smpq:
        raise SystemExit("smpq not found on PATH - see lib/mpq_writer.py's docstring for setup")
    return smpq


def extract_icons(source_mpq: Path) -> dict[str, bytes]:
    """Returns {archive-relative path (forward slashes) -> file bytes} for every path in ICONS."""
    if not source_mpq.is_file():
        raise SystemExit(f"source MPQ not found: {source_mpq}")

    smpq = _find_smpq()
    paths = [p for _, p in ICONS]
    with tempfile.TemporaryDirectory(prefix="patch-i-extract-") as tmp:
        tmp_path = Path(tmp)
        subprocess.run([smpq, "-x", str(source_mpq), *paths], cwd=tmp_path, check=True,
                        capture_output=True, text=True)
        out = {}
        for _, rel in ICONS:
            extracted = tmp_path / rel
            if not extracted.is_file():
                raise SystemExit(f"expected extracted file missing: {rel} (checked {extracted})")
            out[rel] = extracted.read_bytes()
        return out


def load_or_bootstrap_spellicon_working_copy() -> list[dict]:
    """Reads the working-copy SpellIcon.dbc, bootstrapping it from var/spell_icon_names.csv (a
    full id->path dump of the real stock table, already pulled for reference - see that CSV's own
    header) on first run, since this table (unlike CreatureModelData/CreatureDisplayInfo) never had
    a binary working copy checked in yet."""
    if SPELLICON_DBC.is_file():
        return dbcfile.read_dbc(SPELLICON_DBC, dbcfmt.SPELLICON)

    if not STOCK_SPELLICON_CSV.is_file():
        raise SystemExit(f"no working-copy SpellIcon.dbc and no bootstrap CSV at {STOCK_SPELLICON_CSV}")

    rows = []
    for line in STOCK_SPELLICON_CSV.read_text().splitlines()[1:]:  # skip "id,path" header
        id_str, path = line.split(",", 1)
        rows.append({"ID": int(id_str), "TextureFilename": path})
    print(f"bootstrapped {len(rows)} stock row(s) from {STOCK_SPELLICON_CSV.name} into a new working copy")
    return rows


def build_spellicon_rows() -> list[dict]:
    return [
        {"ID": icon_id, "TextureFilename": "Interface\\Icons\\" + Path(rel).stem}
        for icon_id, rel in ICONS
    ]


def merge_spellicon_rows(existing: list[dict], new_rows: list[dict]) -> tuple[list[dict], int]:
    new_by_id = {r["ID"]: r for r in new_rows}
    changed = 0
    merged = []
    seen = set()
    for r in existing:
        if r["ID"] in new_by_id:
            replacement = new_by_id[r["ID"]]
            if replacement != r:
                changed += 1
            merged.append(replacement)
            seen.add(r["ID"])
        else:
            merged.append(r)
    for id_, r in new_by_id.items():
        if id_ not in seen:
            merged.append(r)
            changed += 1
    return merged, changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-mpq", type=Path, default=DEFAULT_SOURCE_MPQ)
    parser.add_argument("--deploy-root", type=str, default=str(DEFAULT_DEPLOY_ROOT) if DEFAULT_DEPLOY_ROOT else "")
    args = parser.parse_args()

    icon_bytes = extract_icons(args.source_mpq)
    print(f"extracted {len(icon_bytes)} icon(s) from {args.source_mpq}")

    existing_rows = load_or_bootstrap_spellicon_working_copy()
    merged_rows, changed = merge_spellicon_rows(existing_rows, build_spellicon_rows())
    if changed:
        dbcfile.write_dbc(SPELLICON_DBC, dbcfmt.SPELLICON, merged_rows)
    print(f"SpellIcon.dbc working copy: {changed} row(s) added/changed ({len(merged_rows)} total)")

    files = {f"DBFilesClient\\SpellIcon.dbc": SPELLICON_DBC.read_bytes()}
    files.update({f"Interface\\Icons\\{Path(rel).name}": blob for rel, blob in icon_bytes.items()})

    LOCAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    write_mpq(LOCAL_OUT, files)
    print(f"built {LOCAL_OUT} ({LOCAL_OUT.stat().st_size} bytes) - "
          f"1 DBC + {len(icon_bytes)} icon file(s):")
    for icon_id, rel in ICONS:
        print(f"  {icon_id} -> Interface\\Icons\\{Path(rel).name}")

    if args.deploy_root:
        deploy_path = Path(args.deploy_root) / "Data" / "patch-I.mpq"
        deploy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LOCAL_OUT, deploy_path)
        print(f"deployed -> {deploy_path}")
        print("(manifest-gen container picks this up on its next timer tick - run "
              "apps/patch-service/manifest_gen.py by hand for an immediate manifest.txt refresh)")


if __name__ == "__main__":
    main()
