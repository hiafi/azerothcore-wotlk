"""
Minimal MPQ v1 archive writer — store-only (no compression), no encryption of
file data, single-unit files only. Enough to package a handful of small DBC
files as a release-style client patch archive; see
`docs/dbc-build-pipeline.md` ("Client patch delivery decision").

The MPQ format itself is public and has been documented and re-implemented
many times over (e.g. http://www.zezula.net/en/mpq/mpqformat.html); this is a
from-scratch, deliberately small implementation of just the parts a WoW
3.3.5a client needs to find files in a patch archive by exact path:
  - the classic MPQ hash table (open-addressed, 3-hash scheme)
  - the block table
  - "single unit" file storage (the whole file is one block, no sector table)

No `(listfile)` is written — the client looks files up by hash, it doesn't
need a directory listing, so this only matters to external MPQ browsers.
"""

from __future__ import annotations

import struct
from pathlib import Path

MPQ_HASH_TABLE_INDEX = 0
MPQ_HASH_NAME_A = 1
MPQ_HASH_NAME_B = 2
MPQ_HASH_FILE_KEY = 3

MPQ_FILE_EXISTS = 0x80000000
MPQ_FILE_SINGLE_UNIT = 0x01000000

HASH_TABLE_EMPTY = 0xFFFFFFFF
HASH_TABLE_DELETED = 0xFFFFFFFE


def _build_crypt_table() -> list[int]:
    """The standard MPQ encryption table (StormLib's `PrepareCryptTable`)."""
    table = [0] * 0x500
    seed = 0x00100001
    for index1 in range(0x100):
        index2 = index1
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            temp1 = (seed & 0xFFFF) << 0x10
            seed = (seed * 125 + 3) % 0x2AAAAB
            temp2 = seed & 0xFFFF
            table[index2] = temp1 | temp2
            index2 += 0x100
    return table


_CRYPT_TABLE = _build_crypt_table()


def _mpq_path(name: str) -> str:
    return name.replace("/", "\\").upper()


def hash_string(name: str, hash_type: int) -> int:
    seed1 = 0x7FED7FED
    seed2 = 0xEEEEEEEE
    for ch in _mpq_path(name):
        seed1 = (_CRYPT_TABLE[(hash_type << 8) + ord(ch)] ^ (seed1 + seed2)) & 0xFFFFFFFF
        seed2 = (ord(ch) + seed1 + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return seed1


def _encrypt_block(data: bytes, key: int) -> bytes:
    assert len(data) % 4 == 0
    values = list(struct.unpack(f"<{len(data) // 4}I", data))
    seed2 = 0xEEEEEEEE
    out = []
    for value in values:
        seed2 = (seed2 + _CRYPT_TABLE[0x400 + (key & 0xFF)]) & 0xFFFFFFFF
        encrypted = (value ^ ((key + seed2) & 0xFFFFFFFF)) & 0xFFFFFFFF
        seed2 = (seed2 + value + (seed2 << 5) + 3) & 0xFFFFFFFF
        key = ((~key << 0x15) + 0x11111111) | (key >> 0x0B)
        key &= 0xFFFFFFFF
        out.append(encrypted)
    return struct.pack(f"<{len(out)}I", *out)


def _next_pow2(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p


def write_mpq(path: Path, files: dict[str, bytes]) -> None:
    """Write `files` (archive-relative-path -> bytes) as a v1 MPQ to `path`."""
    names = list(files.keys())
    hash_table_size = max(4, _next_pow2(len(names) * 4))

    # -- hash table: open-addressed by MPQ_HASH_TABLE_INDEX, linear probe --
    hash_table = [
        {"Name1": HASH_TABLE_EMPTY, "Name2": HASH_TABLE_EMPTY, "Locale": 0,
         "Platform": 0, "BlockIndex": HASH_TABLE_EMPTY}
        for _ in range(hash_table_size)
    ]
    for block_index, name in enumerate(names):
        start = hash_string(name, MPQ_HASH_TABLE_INDEX) % hash_table_size
        name1 = hash_string(name, MPQ_HASH_NAME_A)
        name2 = hash_string(name, MPQ_HASH_NAME_B)
        i = start
        while hash_table[i]["BlockIndex"] != HASH_TABLE_EMPTY:
            i = (i + 1) % hash_table_size
            if i == start:
                raise RuntimeError("MPQ hash table full")
        hash_table[i] = {
            "Name1": name1, "Name2": name2, "Locale": 0, "Platform": 0,
            "BlockIndex": block_index,
        }

    # -- file data + block table (single-unit, stored uncompressed) --
    header_size = 32
    file_data = bytearray()
    block_table = []
    data_offset_base = header_size  # files start right after the header
    for name in names:
        blob = files[name]
        block_table.append({
            "BlockOffset": data_offset_base + len(file_data),
            "BlockSize": len(blob),
            "FileSize": len(blob),
            "Flags": MPQ_FILE_EXISTS | MPQ_FILE_SINGLE_UNIT,
        })
        file_data += blob

    hash_table_offset = header_size + len(file_data)
    block_table_offset = hash_table_offset + hash_table_size * 16

    def pack_hash_entry(e):
        return struct.pack(
            "<IIHHI", e["Name1"], e["Name2"], e["Locale"], e["Platform"], e["BlockIndex"]
        )

    def pack_block_entry(e):
        return struct.pack(
            "<IIII", e["BlockOffset"], e["BlockSize"], e["FileSize"], e["Flags"]
        )

    hash_table_raw = b"".join(pack_hash_entry(e) for e in hash_table)
    block_table_raw = b"".join(pack_block_entry(e) for e in block_table)

    hash_key = hash_string("(hash table)", MPQ_HASH_FILE_KEY)
    block_key = hash_string("(block table)", MPQ_HASH_FILE_KEY)
    hash_table_enc = _encrypt_block(hash_table_raw, hash_key)
    block_table_enc = _encrypt_block(block_table_raw, block_key)

    archive_size = block_table_offset + len(block_table_enc)
    header = struct.pack(
        "<4sIIHHIIII",
        b"MPQ\x1a",
        header_size,
        archive_size,
        0,          # format version 0 (v1)
        3,          # sector size shift (unused: every file is single-unit)
        hash_table_offset,
        block_table_offset,
        hash_table_size,
        len(block_table),
    )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + bytes(file_data) + hash_table_enc + block_table_enc)
