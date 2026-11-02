"""
Pure-Python BLP2 writer (palette + 8-bit alpha + full mip chain) and a matching reader for tests.

Why not Pillow: the dbc-tools venv has no Pillow, and the system Pillow 10.2 BLP writer writes no
alpha plane and no mips (`PIL/BlpImagePlugin.py`, `_save`). Its reader also takes the alpha from the
palette entry, not from the separate plane the real client format carries, so it cannot read these
files back; tests use `read_blp` here and only ask Pillow for the header.

Layout written (little endian), the same one the retail client reads for a paletted texture with
8-bit alpha:

    0x00  'BLP2'
    0x04  u32 type = 1
    0x08  u8 encoding = 1 (palette), u8 alpha depth = 8, u8 alpha encoding = 0, u8 has mips = 1
    0x0C  u32 width, u32 height
    0x14  u32 mip offsets[16], u32 mip sizes[16]
    0x94  palette, 256 x (B, G, R, A)
    0x494 mip 0 ... mip N-1: width*height index bytes, then width*height alpha bytes

Every texture this project generates is one flat colour with a shape in the alpha plane, so the
palette holds that colour at index 0 and every index byte is 0.
"""

from __future__ import annotations

import struct

HEADER_SIZE = 4 + 4 + 4 + 8 + 64 + 64
PALETTE_SIZE = 256 * 4
DATA_START = HEADER_SIZE + PALETTE_SIZE  # 1172


def mip_count(width: int, height: int) -> int:
    """Levels down to 1x1 (the longest side halves each level)."""
    n = 1
    while width > 1 or height > 1:
        width = max(1, width // 2)
        height = max(1, height // 2)
        n += 1
    return n


def downsample(alpha: bytes, width: int, height: int) -> tuple[bytes, int, int]:
    """One box-filtered mip level of an 8-bit plane (odd sides reuse the last row/column)."""
    nw, nh = max(1, width // 2), max(1, height // 2)
    out = bytearray(nw * nh)
    for y in range(nh):
        y0 = min(2 * y, height - 1)
        y1 = min(2 * y + 1, height - 1)
        for x in range(nw):
            x0 = min(2 * x, width - 1)
            x1 = min(2 * x + 1, width - 1)
            s = (alpha[y0 * width + x0] + alpha[y0 * width + x1]
                 + alpha[y1 * width + x0] + alpha[y1 * width + x1])
            out[y * nw + x] = (s + 2) >> 2
    return bytes(out), nw, nh


def encode_blp(width: int, height: int, rgb: tuple[int, int, int], alpha: bytes) -> bytes:
    """A paletted BLP2 with alpha depth 8 and a full mip chain.

    `alpha` is width*height bytes, row-major, row 0 = the top row of the image (v = 0).
    """
    if len(alpha) != width * height:
        raise ValueError(f"alpha plane is {len(alpha)} bytes, expected {width * height}")
    planes = []
    plane, w, h = alpha, width, height
    for _ in range(mip_count(width, height)):
        planes.append((w, h, bytes(w * h) + plane))
        if w == 1 and h == 1:
            break
        plane, w, h = downsample(plane, w, h)
    if len(planes) > 16:
        raise ValueError("more than 16 mip levels")

    offsets = [0] * 16
    sizes = [0] * 16
    cursor = DATA_START
    for i, (_, _, blob) in enumerate(planes):
        offsets[i] = cursor
        sizes[i] = len(blob)
        cursor += len(blob)

    r, g, b = rgb
    palette = struct.pack("<4B", b, g, r, 255) + bytes(PALETTE_SIZE - 4)
    head = (b"BLP2" + struct.pack("<I", 1) + struct.pack("<4B", 1, 8, 0, 1)
            + struct.pack("<II", width, height) + struct.pack("<16I", *offsets) + struct.pack("<16I", *sizes))
    return head + palette + b"".join(blob for _, _, blob in planes)


def read_blp(data: bytes) -> dict:
    """Parse a BLP2 written by `encode_blp` (palette, alpha depth 8). Raises ValueError otherwise."""
    if data[:4] != b"BLP2":
        raise ValueError("not a BLP2 file")
    (kind,) = struct.unpack_from("<I", data, 4)
    encoding, alpha_depth, alpha_encoding, has_mips = struct.unpack_from("<4B", data, 8)
    width, height = struct.unpack_from("<II", data, 12)
    offsets = struct.unpack_from("<16I", data, 20)
    sizes = struct.unpack_from("<16I", data, 84)
    if kind != 1 or encoding != 1 or alpha_depth != 8:
        raise ValueError(f"unsupported BLP2 (type {kind}, encoding {encoding}, alpha depth {alpha_depth})")
    palette = [struct.unpack_from("<4B", data, HEADER_SIZE + 4 * i) for i in range(256)]
    mips = []
    w, h = width, height
    for i in range(16):
        if sizes[i] == 0:
            break
        count = w * h
        if sizes[i] != 2 * count:
            raise ValueError(f"mip {i}: size {sizes[i]} != {2 * count}")
        blob = data[offsets[i]:offsets[i] + sizes[i]]
        if len(blob) != sizes[i]:
            raise ValueError(f"mip {i}: truncated")
        mips.append({"width": w, "height": h, "indices": blob[:count], "alpha": blob[count:]})
        w, h = max(1, w // 2), max(1, h // 2)
    b, g, r, _ = palette[0]
    return {
        "width": width, "height": height, "encoding": encoding, "alpha_depth": alpha_depth,
        "alpha_encoding": alpha_encoding, "has_mips": has_mips, "mip_count": len(mips),
        "palette0_rgb": (r, g, b), "mips": mips, "mip_offsets": offsets, "mip_sizes": sizes,
        "file_size": len(data),
    }
