"""
Repack the deployed client patch with a few files replaced (item variants IV3, plan section 5.4).

patch-Z is one archive for every DBC. A build from source would ship in-flight spell rows to the client without
their SQL, so `generate.py --only items` takes the archive that is already deployed (patch_out.DEPLOY_MPQ), keeps
every file in it byte for byte and swaps in only `DBFilesClient\\Item.dbc`. This module has no knowledge of items: it
reads an archive through `smpq` (like lib/mpq_writer.py), replaces the named files and writes a new archive.

The base is the deployed archive only. Without lib/local_config.py (no DEPLOY_ROOT), or without a patch-Z.mpq in
`DEPLOY_ROOT/Data`, `deployed_base()` raises `PatchBaseError` with a message `generate.py` prints before it
renders or writes anything.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from . import mpq_writer, patch_out

# The archive's own spelling of a member is "DBFilesClient/Item.dbc" in `smpq -l` and "DBFilesClient\\Item.dbc" in
# mpq_writer's write calls; both are the same file. Names compare case-insensitively (MPQ lookups ignore case).
ITEM_DBC = "DBFilesClient\\Item.dbc"


class PatchBaseError(Exception):
    """There is nothing to repack: no deployed patch-Z, or no `smpq` to read it with."""


class RepackError(Exception):
    """The repacked archive does not hold what it should (nothing was written to the destinations)."""


def _norm(name: str) -> str:
    return name.replace("\\", "/").lower()


def deployed_base() -> Path:
    """The deployed patch-Z.mpq, or `PatchBaseError` saying exactly what is missing."""
    try:
        mpq_writer._find_smpq()
    except RuntimeError as error:
        raise PatchBaseError(str(error)) from error
    if patch_out.DEPLOY_ROOT is None:
        raise PatchBaseError(
            "no lib/local_config.py (DEPLOY_ROOT), so there is no deployed patch-Z.mpq to repack; --only items "
            "only replaces Item.dbc inside the deployed archive and never builds one from source "
            "(copy lib/local_config.py.example to lib/local_config.py and set DEPLOY_ROOT)"
        )
    path = patch_out.DEPLOY_ROOT / "Data" / "patch-Z.mpq"
    if not path.is_file():
        raise PatchBaseError(
            f"no deployed patch-Z.mpq at {path}; --only items only replaces Item.dbc inside the deployed archive, "
            f"so run a full generate.py (or deploy a patch-Z) first"
        )
    return path


def list_members(archive: Path) -> list[tuple[int, str, str]]:
    """`(size, date, name)` for every member of `archive`, in archive order, via `smpq -l`."""
    result = subprocess.run(
        [mpq_writer._find_smpq(), "-l", str(Path(archive).resolve())], capture_output=True, text=True, check=True,
    )
    members = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0].isdigit():
            members.append((int(parts[0]), f"{parts[1]} {parts[2]}", parts[-1].replace("\\", "/")))
    return members


def describe(archive: Path) -> list[str]:
    """The lines `--only items` prints about the base: path, file date, and every member with size and date."""
    stat = Path(archive).stat()
    stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
    lines = [f"patch base: {archive} ({stat.st_size} bytes, modified {stamp})"]
    lines += [f"patch base:   {name} {size} bytes {date}" for size, date, name in list_members(archive)]
    return lines


def extract_all(archive: Path, dest: Path) -> dict[str, bytes]:
    """Every member of `archive` as `{archive name with forward slashes: bytes}`, in archive order. `dest` must be
    an empty directory (untrusted data: nothing in it is executed)."""
    members = list_members(archive)
    if not members:
        raise RepackError(f"{archive} lists no files")
    subprocess.run(
        [mpq_writer._find_smpq(), "-x", str(Path(archive).resolve())], cwd=dest, check=True, capture_output=True,
    )
    on_disk = {p.relative_to(dest).as_posix().lower(): p for p in dest.rglob("*") if p.is_file()}
    files: dict[str, bytes] = {}
    for _size, _date, name in members:
        path = on_disk.get(name.lower())
        if path is None:
            raise RepackError(f"smpq did not extract {name} from {archive}")
        files[name] = path.read_bytes()
    return files


def read_members(archive: Path) -> dict[str, bytes]:
    """Every member of `archive` (`extract_all` into a temporary directory), cached per path and file stamp, so the
    guards below and `repack` read a deployed archive once per run."""
    archive = Path(archive)
    stat = archive.stat()
    key = (str(archive.resolve()), stat.st_mtime_ns, stat.st_size)
    if key not in _members_cache:
        with tempfile.TemporaryDirectory(prefix="dbc-repack-read-") as tmp:
            _members_cache[key] = extract_all(archive, Path(tmp))
    return _members_cache[key]


_members_cache: dict[tuple, dict[str, bytes]] = {}


def item_dbc_ids(dbc_bytes: bytes) -> set[int]:
    """The row ids of an Item.dbc image (Item.dbc has no strings, so the header and a fixed-size body)."""
    from . import dbcfile, dbcfmt  # noqa: PLC0415

    with tempfile.TemporaryDirectory(prefix="dbc-item-ids-") as tmp:
        path = Path(tmp) / "Item.dbc"
        path.write_bytes(dbc_bytes)
        rows = dbcfile.read_dbc(path, dbcfmt.ITEM)
    return {int(row[dbcfmt.ITEM.index_column]) for row in rows}


def dropped_item_ids(archive: Path, new_ids, block: dict) -> list[int] | None:
    """B1 / S5 guard: the ids in `block` (`{start, end}`, the custom item block 70000-79999) that the Item.dbc inside
    the deployed `archive` holds but `new_ids` (the Item.dbc this run builds) lacks. Shipping the new build would
    give every client those items' blank icon (and they would not equip): typically another checkout, without the
    newer item declarations, about to replace a patch-Z deployed from a branch that had them. None when the archive
    has no Item.dbc (nothing to lose)."""
    member = next((blob for name, blob in read_members(archive).items() if _norm(name) == _norm(ITEM_DBC)), None)
    if member is None:
        return None
    new = {int(i) for i in new_ids}
    return sorted(i for i in item_dbc_ids(member) if block["start"] <= i <= block["end"] and i not in new)


def foreign_members(archive: Path, loose_dir: Path, skip=(ITEM_DBC,)) -> list[str]:
    """S5: the members of `archive` (except `skip`) whose bytes differ from this checkout's last full build of the
    same file (`loose_dir/<file name>`, var/dbc-patch/DBFilesClient). A difference means the deployed base is stale
    or came from another checkout; `--only items` would ship it again with only Item.dbc replaced. Members with no
    local copy are not compared."""
    skipped = {_norm(name) for name in skip}
    out = []
    for name, blob in read_members(archive).items():
        if _norm(name) in skipped:
            continue
        local = Path(loose_dir) / name.replace("\\", "/").split("/")[-1]
        if local.is_file() and local.read_bytes() != blob:
            out.append(name)
    return out


def repack(base: Path, replacements: dict[str, bytes], out_path: Path) -> list[str]:
    """Write `out_path` = every member of `base` unchanged, except that each of `replacements`
    (`{"DBFilesClient\\\\Item.dbc": bytes}`) takes the place of the member of the same name. A replacement that `base`
    does not hold is added at the end. Verified before returning: the new archive holds the same names, the
    replaced files carry the new bytes and every other file is byte-identical to the base. Returns the member names
    that changed (replaced with different bytes, or added); when that is empty nothing is written (the base already
    holds them). `out_path` is written whole or not at all (a temp file next to it, then a rename)."""
    wanted = {_norm(name): (name, blob) for name, blob in replacements.items()}
    before = read_members(base)
    after: dict[str, bytes] = {}
    replaced: list[str] = []
    for name, blob in before.items():
        if _norm(name) in wanted:
            after[name] = wanted.pop(_norm(name))[1]
            if after[name] != blob:
                replaced.append(name)
        else:
            after[name] = blob
    for name, blob in wanted.values():
        after[name.replace("\\", "/")] = blob
        replaced.append(name.replace("\\", "/"))

    if not replaced:
        return []
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    staging = out_path.with_name(out_path.name + ".repack-tmp")
    try:
        mpq_writer.write_mpq(staging, after)
        with tempfile.TemporaryDirectory(prefix="dbc-repack-check-") as tmp:
            written = extract_all(staging, Path(tmp))
        problems = []
        if {n.lower() for n in written} != {n.lower() for n in after}:
            problems.append(f"members differ: expected {sorted(after)}, got {sorted(written)}")
        else:
            for name, blob in after.items():
                if hashlib.sha256(written[name]).digest() != hashlib.sha256(blob).digest():
                    problems.append(f"{name} differs from what was packed")
        if problems:
            raise RepackError(f"repacked archive failed verification: {'; '.join(problems)}")
        os.replace(staging, out_path)
    finally:
        if staging.exists():
            staging.unlink()
    return replaced


def install(archive: Path, dbc_files: dict[str, bytes]) -> dict:
    """Put a repacked archive where `patch_out.write_patch` puts a full one, touching only what changed: the local
    `var/dbc-patch/patch-Z.mpq`, the loose copies of `dbc_files` (`{"Item.dbc": bytes}`, in LOOSE_DIR and, when that
    directory exists, ENV_DBC_DIR) and the deployed archive (replaced atomically, like a copy then a rename). The
    other loose files are left as the last full run wrote them. Reads the `patch_out` paths at call time."""
    report = {"loose": [], "mpq": None, "env_dbc": [], "deploy_mpq": None}
    for filename, blob in dbc_files.items():
        out = patch_out.LOOSE_DIR / filename
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(blob)
        report["loose"].append(str(out))
    patch_out.MPQ_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(archive, patch_out.MPQ_PATH)
    report["mpq"] = str(patch_out.MPQ_PATH)
    if patch_out.ENV_DBC_DIR.is_dir():
        for filename, blob in dbc_files.items():
            out = patch_out.ENV_DBC_DIR / filename
            out.write_bytes(blob)
            report["env_dbc"].append(str(out))
    if patch_out.DEPLOY_ROOT and patch_out.DEPLOY_ROOT.is_dir():
        deploy = patch_out.DEPLOY_ROOT / "Data" / "patch-Z.mpq"
        deploy.parent.mkdir(parents=True, exist_ok=True)
        staging = deploy.with_name(deploy.name + ".repack-tmp")
        try:
            shutil.copyfile(archive, staging)
            os.replace(staging, deploy)
        finally:
            if staging.exists():
                staging.unlink()
        report["deploy_mpq"] = str(deploy)
    return report
