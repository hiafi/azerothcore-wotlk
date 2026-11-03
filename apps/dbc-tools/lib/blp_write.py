"""
Pure-Python BLP2 writers for flat-color textures with a shape in the alpha channel, plus a reader
(with a DXT5 decoder) for tests.

Two formats:

- `dxt5` (the default, `encode_blp`): compression 2, alpha depth 8, alpha type 7 (DXT5), full mip
  chain down to 1x1. Byte-for-byte the header layout of Ascension's known-good
  `SPELLS\\red_circle_filled_editeda_circle_solid_red.blp`, the texture this marker model family
  ships with: zeroed 1 KiB palette block, mip 0 at 0x494, levels packed back to back, every level
  at least one 16-byte block (2x2 and 1x1 are one padded block each).
- `palette` (`encode_blp_palette`): compression 1, alpha depth 8, alpha type 0. The format the
  first M1 build shipped; kept for the 90621 diagnostic display.

Why not Pillow: the dbc-tools venv has no Pillow, and the system Pillow 10.2 BLP writer writes no
alpha plane and no mips (`PIL/BlpImagePlugin.py`, `_save`). Its reader takes the alpha of a
palette file from the palette entry, not from the separate plane the client reads.

Header (little endian):

    0x00  'BLP2'
    0x04  u32 type = 1 (not JPEG)
    0x08  u8 compression (1 palette, 2 DXT), u8 alpha depth, u8 alpha type (0, or 7 = DXT5), u8 has mips = 1
    0x0C  u32 width, u32 height
    0x14  u32 mip offsets[16], u32 mip sizes[16]
    0x94  palette, 256 x (B, G, R, A) (all zero for DXT)
    0x494 mip 0 ... mip N-1

DXT5 block (16 bytes, one per 4x4 pixels): alpha0 u8, alpha1 u8, 16 x 3-bit alpha indices (48 bits,
little endian, pixel i = row * 4 + col at bit 3 * i), then the DXT1 color block: c0 u16, c1 u16
(RGB565), 16 x 2-bit indices. A flat color makes the color block trivial (c0 = c1, indices 0).
"""

from __future__ import annotations

import functools
import struct

HEADER_SIZE = 4 + 4 + 4 + 8 + 64 + 64
PALETTE_SIZE = 256 * 4
DATA_START = HEADER_SIZE + PALETTE_SIZE  # 1172 = 0x494

COMPRESSION_PALETTE = 1
COMPRESSION_DXT = 2
ALPHA_TYPE_DXT5 = 7


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


def clear_edges(plane: bytes, width: int, height: int, *, cols: bool, rows: bool) -> bytes:
    """Zero the outermost texel ring of one level: the first and last column (`cols`) and/or row (`rows`)."""
    out = bytearray(plane)
    if cols:
        for y in range(height):
            out[y * width] = 0
            out[y * width + width - 1] = 0
    if rows:
        out[:width] = bytes(width)
        out[(height - 1) * width:] = bytes(width)
    return bytes(out)


def hard_threshold(plane: bytes, threshold: int) -> bytes:
    """Every texel above `threshold` becomes 255, every other one 0."""
    return bytes(255 if v > threshold else 0 for v in plane)


def _mip_planes(alpha: bytes, width: int, height: int, clear_cols: bool = False,
                clear_rows: bool = False, threshold: int | None = None) -> list[tuple[int, int, bytes]]:
    """Every mip level, box filtered from the one above. `clear_cols` / `clear_rows` zero the edge texels of
    every level (after filtering, so a level never inherits a zeroed edge's average either way): with clamp
    addressing an edge texel is stretched along the whole quad edge, so a shape that reaches the edge at a low mip
    draws a straight line along it (the boss markers' "lines at the cardinals"). `threshold` (a probe only) makes
    every level hard, 0 or 255 (`hard_threshold`), before the edges are cleared."""
    if len(alpha) != width * height:
        raise ValueError(f"alpha plane is {len(alpha)} bytes, expected {width * height}")
    planes = []
    plane, w, h = alpha, width, height
    for _ in range(mip_count(width, height)):
        if threshold is not None:
            plane = hard_threshold(plane, threshold)
        if clear_cols or clear_rows:
            plane = clear_edges(plane, w, h, cols=clear_cols, rows=clear_rows)
        planes.append((w, h, plane))
        if w == 1 and h == 1:
            break
        plane, w, h = downsample(plane, w, h)
    if len(planes) > 16:
        raise ValueError("more than 16 mip levels")
    return planes


def _assemble(width: int, height: int, compression: int, alpha_depth: int, alpha_type: int,
              palette: bytes, blobs: list[bytes]) -> bytes:
    offsets = [0] * 16
    sizes = [0] * 16
    cursor = DATA_START
    for i, blob in enumerate(blobs):
        offsets[i] = cursor
        sizes[i] = len(blob)
        cursor += len(blob)
    head = (b"BLP2" + struct.pack("<I", 1) + struct.pack("<4B", compression, alpha_depth, alpha_type, 1)
            + struct.pack("<II", width, height) + struct.pack("<16I", *offsets) + struct.pack("<16I", *sizes))
    return head + palette + b"".join(blobs)


# --- palette (alpha depth 8) ---

def encode_blp_palette(width: int, height: int, rgb: tuple[int, int, int], alpha: bytes) -> bytes:
    """A paletted BLP2 with alpha depth 8 and a full mip chain (each level: index bytes, then alpha bytes).

    `alpha` is width*height bytes, row-major, row 0 = the top row of the image (v = 0).
    """
    blobs = [bytes(w * h) + plane for w, h, plane in _mip_planes(alpha, width, height)]
    r, g, b = rgb
    palette = struct.pack("<4B", b, g, r, 255) + bytes(PALETTE_SIZE - 4)
    return _assemble(width, height, COMPRESSION_PALETTE, 8, 0, palette, blobs)


# --- DXT5 ---

def rgb565(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    return ((r * 31 + 127) // 255) << 11 | ((g * 63 + 127) // 255) << 5 | ((b * 31 + 127) // 255)


def expand565(c: int) -> tuple[int, int, int]:
    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
    return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)


def dxt5_alpha_palette(a0: int, a1: int) -> list[int]:
    """The eight alpha values a DXT5 alpha block's 3-bit codes select."""
    if a0 > a1:
        return [a0, a1] + [((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)]
    return [a0, a1] + [((5 - i) * a0 + i * a1) // 5 for i in range(1, 5)] + [0, 255]


def _alpha_block_for(values: tuple[int, ...]) -> tuple[bytes, int]:
    """Best of the two DXT5 alpha modes for 16 values: (8 block bytes, squared error)."""
    lo, hi = min(values), max(values)
    if lo == hi:
        return bytes([lo, lo]) + bytes(6), 0
    candidates = [(hi, lo)]                                     # 8-value mode, a0 > a1
    inner = [v for v in values if 0 < v < 255]
    if inner:
        ilo, ihi = min(inner), max(inner)
        candidates.append((ilo, ihi))                           # 6-value mode + explicit 0 and 255
    else:
        candidates.append((0, 0))                               # only 0 and 255: codes 6 and 7 are exact
    best = None
    for a0, a1 in candidates:
        pal = dxt5_alpha_palette(a0, a1)
        bits = 0
        err = 0
        for i, v in enumerate(values):
            code = min(range(8), key=lambda k: abs(pal[k] - v))
            err += (pal[code] - v) ** 2
            bits |= code << (3 * i)
        if best is None or err < best[1]:
            best = (bytes([a0, a1]) + bits.to_bytes(6, "little"), err)
    return best


@functools.lru_cache(maxsize=4096)
def _alpha_block_cached(values: tuple[int, ...]) -> bytes:
    return _alpha_block_for(values)[0]


def dxt5_alpha_blocks(plane: bytes, width: int, height: int) -> list[bytes]:
    """Row-major list of 8-byte DXT5 alpha blocks for one level; a side under 4 pads by clamping."""
    out = []
    bw, bh = max(1, (width + 3) // 4), max(1, (height + 3) // 4)
    for by in range(bh):
        for bx in range(bw):
            vals = []
            for r in range(4):
                y = min(by * 4 + r, height - 1)
                for c in range(4):
                    x = min(bx * 4 + c, width - 1)
                    vals.append(plane[y * width + x])
            out.append(_alpha_block_cached(tuple(vals)))
    return out


@functools.lru_cache(maxsize=64)
def _dxt5_alpha_levels(alpha: bytes, width: int, height: int, clear_cols: bool = False,
                       clear_rows: bool = False, threshold: int | None = None) -> tuple[tuple[bytes, ...], ...]:
    """Alpha blocks of every mip level (color independent, so cached per plane)."""
    return tuple(tuple(dxt5_alpha_blocks(plane, w, h))
                 for w, h, plane in _mip_planes(alpha, width, height, clear_cols, clear_rows, threshold))


def encode_blp(width: int, height: int, rgb: tuple[int, int, int], alpha: bytes, *, clear_cols: bool = False,
               clear_rows: bool = False, threshold: int | None = None) -> bytes:
    """A DXT5 BLP2 (compression 2, alpha depth 8, alpha type 7) with a full mip chain.

    `alpha` is width*height bytes, row-major, row 0 = the top row of the image (v = 0). `clear_cols` /
    `clear_rows` keep the edge columns / rows transparent at every mip level (see `_mip_planes`); `threshold`
    makes every level 0 or 255.
    """
    if width % 4 or height % 4:
        raise ValueError("DXT needs sides that are a multiple of 4")
    c = rgb565(rgb)
    color = struct.pack("<HHI", c, c, 0)
    levels = _dxt5_alpha_levels(bytes(alpha), width, height, clear_cols, clear_rows, threshold)
    blobs = [b"".join(a + color for a in level) for level in levels]
    return _assemble(width, height, COMPRESSION_DXT, 8, ALPHA_TYPE_DXT5, bytes(PALETTE_SIZE), blobs)


def decode_dxt5(blob: bytes, width: int, height: int) -> tuple[list[tuple[int, int, int]], bytes]:
    """Decode one DXT5 level into (row-major RGB list, row-major alpha bytes), cropped to width x height."""
    bw, bh = max(1, (width + 3) // 4), max(1, (height + 3) // 4)
    if len(blob) != 16 * bw * bh:
        raise ValueError(f"DXT5 level is {len(blob)} bytes, expected {16 * bw * bh}")
    rgb = [(0, 0, 0)] * (width * height)
    alpha = bytearray(width * height)
    for by in range(bh):
        for bx in range(bw):
            o = 16 * (by * bw + bx)
            a0, a1 = blob[o], blob[o + 1]
            apal = dxt5_alpha_palette(a0, a1)
            abits = int.from_bytes(blob[o + 2:o + 8], "little")
            c0, c1, cbits = struct.unpack_from("<HHI", blob, o + 8)
            e0, e1 = expand565(c0), expand565(c1)
            cpal = [e0, e1,
                    tuple((2 * p + q + 1) // 3 for p, q in zip(e0, e1)),
                    tuple((p + 2 * q + 1) // 3 for p, q in zip(e0, e1))]  # DXT5: always the 4-color mode
            for i in range(16):
                y, x = by * 4 + i // 4, bx * 4 + i % 4
                if y < height and x < width:
                    alpha[y * width + x] = apal[(abits >> (3 * i)) & 7]
                    rgb[y * width + x] = cpal[(cbits >> (2 * i)) & 3]
    return rgb, bytes(alpha)


def read_blp(data: bytes) -> dict:
    """Parse a BLP2 (palette with alpha depth 8, or DXT5). Raises ValueError otherwise.

    Every mip carries "alpha" (decoded plane) and "rgb0" (the first pixel's color)."""
    if data[:4] != b"BLP2":
        raise ValueError("not a BLP2 file")
    (kind,) = struct.unpack_from("<I", data, 4)
    encoding, alpha_depth, alpha_encoding, has_mips = struct.unpack_from("<4B", data, 8)
    width, height = struct.unpack_from("<II", data, 12)
    offsets = struct.unpack_from("<16I", data, 20)
    sizes = struct.unpack_from("<16I", data, 84)
    dxt5 = encoding == COMPRESSION_DXT and alpha_depth == 8 and alpha_encoding == ALPHA_TYPE_DXT5
    palette8 = encoding == COMPRESSION_PALETTE and alpha_depth == 8
    if kind != 1 or not (dxt5 or palette8):
        raise ValueError(f"unsupported BLP2 (type {kind}, encoding {encoding}, alpha depth {alpha_depth}, "
                         f"alpha type {alpha_encoding})")
    palette = [struct.unpack_from("<4B", data, HEADER_SIZE + 4 * i) for i in range(256)]
    mips = []
    w, h = width, height
    for i in range(16):
        if sizes[i] == 0:
            break
        blob = data[offsets[i]:offsets[i] + sizes[i]]
        if len(blob) != sizes[i]:
            raise ValueError(f"mip {i}: truncated")
        if dxt5:
            rgb, alpha = decode_dxt5(blob, w, h)
            mips.append({"width": w, "height": h, "alpha": alpha, "rgb": rgb, "rgb0": rgb[0]})
        else:
            count = w * h
            if sizes[i] != 2 * count:
                raise ValueError(f"mip {i}: size {sizes[i]} != {2 * count}")
            b, g, r, _ = palette[blob[0]]
            mips.append({"width": w, "height": h, "indices": blob[:count], "alpha": blob[count:],
                         "rgb0": (r, g, b)})
        w, h = max(1, w // 2), max(1, h // 2)
    b, g, r, _ = palette[0]
    return {
        "width": width, "height": height, "encoding": encoding, "alpha_depth": alpha_depth,
        "alpha_encoding": alpha_encoding, "has_mips": has_mips, "mip_count": len(mips),
        "palette0_rgb": (r, g, b), "palette_bytes": data[HEADER_SIZE:DATA_START], "mips": mips,
        "mip_offsets": offsets, "mip_sizes": sizes, "file_size": len(data),
    }
