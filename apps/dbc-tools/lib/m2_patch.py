"""
Byte-level patcher for the one Ascension M2 the boss-mechanics markers are built from
(`SPELLS\\red_circle_filled.M2`, v264, a single textured quad), plus its `.skin` companion.

Everything here edits the file in place at fixed offsets and returns new bytes; nothing is
re-serialised, so the model is unchanged outside the patched ranges (tested byte-for-byte). The
input is untrusted data from another server's client, so every offset read from it is bounds
checked and `check_source` pins the exact shape this patcher was written against.

What gets patched (handoff §3.9):
  - the four vertices become a flat quad at z = 0 (x, y given by the caller), and the header
    bounding box and sphere radius, the three animation bounds and the skin submesh bounds follow;
  - the render-flags entry keeps its flags (0x15: unlit, two-sided, no depth write) and gets blend
    mode 2 (alpha) instead of 4 (additive);
  - the colour track must be white and the colour alpha / transparency tracks opaque (the source
    fades in over 534 ms and is half transparent), so the texture alpha is the on-screen alpha;
  - the texture entry becomes either type 11 with an empty name (creature skin 1, so
    `CreatureDisplayInfo.TextureVariation_1` supplies the texture) or stays type 0 with a new
    hard-coded path (`--no-skins`).

M2 header offsets used (WotLK, v264): animations 0x1C, vertices 0x3C, colours 0x48, textures 0x50,
transparency 0x58, render flags 0x70, bounding box 0xA0 (6 floats), bounding sphere radius 0xB8.
"""

from __future__ import annotations

import math
import struct

OFS_ANIMATIONS = 0x1C
OFS_VERTICES = 0x3C
OFS_COLORS = 0x48
OFS_TEXTURES = 0x50
OFS_TRANSPARENCY = 0x58
OFS_RENDER_FLAGS = 0x70
OFS_BBOX = 0xA0
OFS_SPHERE = 0xB8

VERTEX_SIZE = 48
ANIM_SIZE = 64
ANIM_BOUNDS = 32          # bmin(3f) bmax(3f) radius(f) inside an animation entry
TEXTURE_SIZE = 16
TRACK_SIZE = 20
COLOR_SIZE = 2 * TRACK_SIZE
OPAQUE = 0x7FFF           # fixed16 1.0

BLEND_ALPHA = 2
TEXTURE_TYPE_SKIN1 = 11


class M2Error(ValueError):
    """The input is not the model this patcher was written for."""


def _u32(data: bytes, off: int) -> int:
    if off < 0 or off + 4 > len(data):
        raise M2Error(f"read at {off:#x} past end of file ({len(data)} bytes)")
    return struct.unpack_from("<I", data, off)[0]


def _span(data: bytes, off: int, size: int, what: str) -> None:
    if off < 0 or size < 0 or off + size > len(data):
        raise M2Error(f"{what}: {size} bytes at {off:#x} outside the file ({len(data)} bytes)")


def _array(data: bytes, header_off: int, entry_size: int, what: str) -> tuple[int, int]:
    count, ofs = _u32(data, header_off), _u32(data, header_off + 4)
    _span(data, ofs, count * entry_size, what)
    return count, ofs


def check_source(data: bytes, *, patched: bool = False) -> dict:
    """Validate the shape this patcher assumes and return the facts later steps need.

    `patched=True` accepts the patcher's own output too (texture type 0 or 11)."""
    if data[:4] != b"MD20":
        raise M2Error("not an MD20 model")
    if _u32(data, 4) != 264:
        raise M2Error(f"version {_u32(data, 4)}, expected 264")
    n_vert, o_vert = _array(data, OFS_VERTICES, VERTEX_SIZE, "vertices")
    if n_vert != 4:
        raise M2Error(f"{n_vert} vertices, expected 4")
    n_flags, o_flags = _array(data, OFS_RENDER_FLAGS, 4, "render flags")
    if n_flags != 1:
        raise M2Error(f"{n_flags} render-flag entries, expected 1")
    n_tex, o_tex = _array(data, OFS_TEXTURES, TEXTURE_SIZE, "textures")
    if n_tex != 1:
        raise M2Error(f"{n_tex} textures, expected 1")
    tex_type, _tex_flags, name_len, name_ofs = struct.unpack_from("<IIII", data, o_tex)
    if tex_type != 0 and not (patched and tex_type == TEXTURE_TYPE_SKIN1):
        raise M2Error(f"texture type {tex_type}, expected 0 (hard-coded path)")
    _span(data, name_ofs, name_len, "texture name")
    n_col, o_col = _array(data, OFS_COLORS, COLOR_SIZE, "colours")
    n_tr, o_tr = _array(data, OFS_TRANSPARENCY, TRACK_SIZE, "transparency")
    if n_col != 1 or n_tr != 1:
        raise M2Error(f"{n_col} colour / {n_tr} transparency tracks, expected 1 / 1")
    n_anim, o_anim = _array(data, OFS_ANIMATIONS, ANIM_SIZE, "animations")
    return {
        "vertices": o_vert, "render_flags": o_flags, "texture": o_tex, "name_len": name_len,
        "name_ofs": name_ofs, "colors": o_col, "transparency": o_tr, "animations": (n_anim, o_anim),
    }


def _track(data: bytes, off: int) -> dict:
    """Decode one M2 animation track header into its per-animation key lists."""
    _span(data, off, TRACK_SIZE, "track")
    n_ts, o_ts, n_keys, o_keys = struct.unpack_from("<4xIIII", data, off)
    _span(data, o_keys, n_keys * 8, "track key headers")
    keys = []
    for i in range(n_keys):
        count, ofs = struct.unpack_from("<II", data, o_keys + 8 * i)
        keys.append((count, ofs))
    return {"n_ts": n_ts, "keys": keys}


def inspect(data: bytes) -> dict:
    """The colour / alpha / transparency facts the handoff says to check before patching."""
    facts = check_source(data, patched=True)
    color = facts["colors"]
    rgb = _track(data, color)
    alpha = _track(data, color + TRACK_SIZE)
    transp = _track(data, facts["transparency"])
    rgb_values = []
    for count, ofs in rgb["keys"]:
        _span(data, ofs, count * 12, "colour keys")
        rgb_values += [struct.unpack_from("<3f", data, ofs + 12 * i) for i in range(count)]
    alpha_values = []
    for count, ofs in alpha["keys"]:
        _span(data, ofs, count * 2, "colour alpha keys")
        alpha_values.append([struct.unpack_from("<h", data, ofs + 2 * i)[0] for i in range(count)])
    transp_values = []
    for count, ofs in transp["keys"]:
        _span(data, ofs, count * 2, "transparency keys")
        transp_values.append([struct.unpack_from("<h", data, ofs + 2 * i)[0] for i in range(count)])
    return {"rgb": rgb_values, "alpha": alpha_values, "transparency": transp_values,
            "rgb_track": rgb, "alpha_track": alpha, "transp_track": transp}


def vertex_positions(data: bytes) -> list[tuple[float, float, float]]:
    ofs = check_source(data, patched=True)["vertices"]
    return [struct.unpack_from("<3f", data, ofs + VERTEX_SIZE * i) for i in range(4)]


def vertex_uvs(data: bytes) -> list[tuple[float, float]]:
    ofs = check_source(data, patched=True)["vertices"]
    return [struct.unpack_from("<2f", data, ofs + VERTEX_SIZE * i + 32) for i in range(4)]


def bounds_of(verts: list[tuple[float, float]]) -> dict:
    """Bounding box (z = 0), its centre, the sphere radius around the model origin (the header
    convention: the source's 5.7765 is hypot(4.0846, 4.0846) with the box centred on x = y = 0) and
    the radius around the box centre (what the skin submesh stores)."""
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    lo = (min(xs), min(ys), 0.0)
    hi = (max(xs), max(ys), 0.0)
    centre = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0.0)
    return {
        "min": lo, "max": hi, "centre": centre,
        "origin_radius": max(math.hypot(x, y) for x, y in verts),
        "centre_radius": max(math.hypot(x - centre[0], y - centre[1]) for x, y in verts),
    }


def patch_model(data: bytes, verts: list[tuple[float, float]], *, skins: bool,
                texture_path: str | None = None) -> bytes:
    """Return the patched model.

    verts: four (x, y) pairs in the source vertex order (-,-), (+,-), (-,+), (+,+), z becomes 0.
    skins: True turns the texture into creature skin 1 (type 11, empty name); False keeps the
    hard-coded path and rewrites it to `texture_path` (must fit the source name's capacity).
    """
    if len(verts) != 4:
        raise M2Error("need exactly four vertices")
    facts = check_source(data)
    out = bytearray(data)

    for i, (x, y) in enumerate(verts):
        struct.pack_into("<3f", out, facts["vertices"] + VERTEX_SIZE * i, x, y, 0.0)

    b = bounds_of(verts)
    struct.pack_into("<6f", out, OFS_BBOX, *b["min"], *b["max"])
    struct.pack_into("<f", out, OFS_SPHERE, b["origin_radius"])
    n_anim, o_anim = facts["animations"]
    for i in range(n_anim):
        struct.pack_into("<7f", out, o_anim + ANIM_SIZE * i + ANIM_BOUNDS,
                         *b["min"], *b["max"], b["origin_radius"])

    # render flags entry: u16 flags (kept), u16 blend mode
    struct.pack_into("<H", out, facts["render_flags"] + 2, BLEND_ALPHA)

    # colour: white; colour alpha and transparency: opaque on every animation that has keys
    info = inspect(data)
    for count, ofs in info["rgb_track"]["keys"]:
        for i in range(count):
            struct.pack_into("<3f", out, ofs + 12 * i, 1.0, 1.0, 1.0)
    for track in (info["alpha_track"], info["transp_track"]):
        for count, ofs in track["keys"]:
            for i in range(count):
                struct.pack_into("<h", out, ofs + 2 * i, OPAQUE)

    # texture entry
    tex = facts["texture"]
    if skins:
        struct.pack_into("<IIII", out, tex, TEXTURE_TYPE_SKIN1, 0, 0, 0)
    else:
        if not texture_path:
            raise M2Error("texture_path is required without skins")
        raw = texture_path.encode("ascii") + b"\0"
        if len(raw) > facts["name_len"]:
            raise M2Error(f"texture path {texture_path!r} does not fit the source name ({facts['name_len']} bytes)")
        out[facts["name_ofs"]:facts["name_ofs"] + facts["name_len"]] = raw + bytes(facts["name_len"] - len(raw))
    return bytes(out)


# --- skin ---

SKIN_SUBMESH_COUNT = 0x1C   # u32 count, u32 offset (header: 'SKIN' then nIdx/ofs, nTri/ofs, nProp/ofs, nSub/ofs, ...)
SUBMESH_SIZE = 48
SUBMESH_CENTRES = 20        # centerMass(3f) centerBBox(3f) radius(f) after ten u16 fields


def check_skin(data: bytes) -> int:
    if data[:4] != b"SKIN":
        raise M2Error("not a SKIN file")
    count, ofs = _u32(data, SKIN_SUBMESH_COUNT), _u32(data, SKIN_SUBMESH_COUNT + 4)
    if count != 1:
        raise M2Error(f"{count} submeshes, expected 1")
    _span(data, ofs, SUBMESH_SIZE, "submesh")
    return ofs


def patch_skin(data: bytes, verts: list[tuple[float, float]]) -> bytes:
    """Move the single submesh's centre and radius to the new quad."""
    ofs = check_skin(data)
    b = bounds_of(verts)
    out = bytearray(data)
    struct.pack_into("<7f", out, ofs + SUBMESH_CENTRES, *b["centre"], *b["centre"], b["centre_radius"])
    return bytes(out)


def skin_submesh_bounds(data: bytes) -> tuple[tuple[float, float, float], tuple[float, float, float], float]:
    ofs = check_skin(data)
    v = struct.unpack_from("<7f", data, ofs + SUBMESH_CENTRES)
    return v[0:3], v[3:6], v[6]
