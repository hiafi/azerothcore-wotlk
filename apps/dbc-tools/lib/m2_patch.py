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
  - the color track (M2Color 0, which the skin's one batch points at with color index 0) holds the
    marker's color: every key is set to `rgb` (white by default). The client multiplies the texture
    by it (the batch is unlit, render flag 0x01), so one white texture serves every color. The source
    track has one key list (Stand) and interpolation none; it is left that way: markers only ever play
    Stand (M1-FIX-COLORS-REPORT.md);
  - the color alpha / transparency tracks are opaque and static (the source fades in over 534 ms on
    Stand, out over 534 ms on Decay, and is half transparent): every per-animation key list of those
    tracks is cut to one opaque key, and an animation with no keys (Hold, 158) borrows that key, so
    no sequence can fade, grow or fall back to a default;
  - the texture entry stays type 0 with a new hard-coded path (the default), or becomes type 11
    with an empty name (creature skin 1, so `CreatureDisplayInfo.TextureVariation_1` supplies the
    texture). Type 11 also needs the replaceable-texture lookup to map 11 to texture 0: the source's
    lookup has one entry ([0], type 0 only), so the client finds no slot for skin 1 and draws the
    empty texture (the first M1 build's green boxes). `skin_lookup=True` appends a 12-entry lookup
    ([-1] * 11 + [0], the layout stock creature models such as Skunk.m2 carry) at the end of the file
    and repoints the header; that is the one place the file grows.

M2 header offsets used (WotLK, v264): animations 0x1C, vertices 0x3C, colors 0x48, textures 0x50,
transparency 0x58, replaceable texture lookup 0x68, render flags 0x70, bounding box 0xA0 (6 floats),
bounding sphere radius 0xB8.
"""

from __future__ import annotations

import math
import struct

OFS_ANIMATIONS = 0x1C
OFS_VERTICES = 0x3C
OFS_COLORS = 0x48
OFS_TEXTURES = 0x50
OFS_TRANSPARENCY = 0x58
OFS_REPLACEABLE_LOOKUP = 0x68
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
SKIN1_LOOKUP = [-1] * TEXTURE_TYPE_SKIN1 + [0]     # replaceable type -> texture index


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
    n_col, o_col = _array(data, OFS_COLORS, COLOR_SIZE, "colors")
    n_tr, o_tr = _array(data, OFS_TRANSPARENCY, TRACK_SIZE, "transparency")
    if n_col != 1 or n_tr != 1:
        raise M2Error(f"{n_col} color / {n_tr} transparency tracks, expected 1 / 1")
    n_anim, o_anim = _array(data, OFS_ANIMATIONS, ANIM_SIZE, "animations")
    return {
        "vertices": o_vert, "render_flags": o_flags, "texture": o_tex, "name_len": name_len,
        "name_ofs": name_ofs, "colors": o_col, "transparency": o_tr, "animations": (n_anim, o_anim),
    }


def _track(data: bytes, off: int) -> dict:
    """Decode one M2 animation track header into its per-animation key lists."""
    _span(data, off, TRACK_SIZE, "track")
    n_ts, o_ts, n_keys, o_keys = struct.unpack_from("<4xIIII", data, off)
    _span(data, o_ts, n_ts * 8, "track timestamp headers")
    _span(data, o_keys, n_keys * 8, "track key headers")
    if n_ts != n_keys:
        raise M2Error(f"track at {off:#x}: {n_ts} timestamp lists but {n_keys} key lists")
    keys = []
    stamps = []
    for i in range(n_keys):
        count, ofs = struct.unpack_from("<II", data, o_keys + 8 * i)
        keys.append((count, ofs))
        t_count, t_ofs = struct.unpack_from("<II", data, o_ts + 8 * i)
        if t_count != count:
            raise M2Error(f"track at {off:#x}, animation {i}: {t_count} timestamps but {count} keys")
        _span(data, t_ofs, 4 * t_count, "timestamps")
        stamps.append((t_count, t_ofs))
    return {"n_ts": n_ts, "keys": keys, "stamps": stamps, "ts_headers": o_ts, "key_headers": o_keys}


def inspect(data: bytes) -> dict:
    """The color / alpha / transparency facts the handoff says to check before patching."""
    facts = check_source(data, patched=True)
    color = facts["colors"]
    rgb = _track(data, color)
    alpha = _track(data, color + TRACK_SIZE)
    transp = _track(data, facts["transparency"])
    rgb_values = []
    for count, ofs in rgb["keys"]:
        _span(data, ofs, count * 12, "color keys")
        rgb_values += [struct.unpack_from("<3f", data, ofs + 12 * i) for i in range(count)]
    alpha_values = []
    for count, ofs in alpha["keys"]:
        _span(data, ofs, count * 2, "color alpha keys")
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


def replaceable_lookup(data: bytes) -> list[int]:
    count, ofs = _u32(data, OFS_REPLACEABLE_LOOKUP), _u32(data, OFS_REPLACEABLE_LOOKUP + 4)
    _span(data, ofs, 2 * count, "replaceable texture lookup")
    return list(struct.unpack_from(f"<{count}h", data, ofs))


def set_texture_path(data: bytes, texture_path: str) -> bytes:
    """Only rewrite the type-0 texture's hard-coded path, in place (it must fit the source name's bytes)."""
    facts = check_source(data)
    raw = texture_path.encode("ascii") + b"\0"
    if len(raw) > facts["name_len"]:
        raise M2Error(f"texture path {texture_path!r} does not fit the source name ({facts['name_len']} bytes)")
    out = bytearray(data)
    out[facts["name_ofs"]:facts["name_ofs"] + facts["name_len"]] = raw + bytes(facts["name_len"] - len(raw))
    # the entry's length counts the new name and its terminator, as Blizzard's files do (no stray NULs)
    struct.pack_into("<I", out, facts["texture"] + 8, len(raw))
    return bytes(out)


def _static_opaque(out: bytearray, track: dict) -> None:
    """Every animation's key list -> one opaque key at t = 0; an empty list borrows the first real one."""
    donor = next(((t, k) for t, k in zip(track["stamps"], track["keys"]) if k[0] > 0), None)
    if donor is None:
        raise M2Error("an alpha track with no keys at all")
    for i, ((t_count, t_ofs), (count, ofs)) in enumerate(zip(track["stamps"], track["keys"])):
        if count == 0:
            (_, t_ofs), (_, ofs) = donor
        struct.pack_into("<I", out, t_ofs, 0)
        struct.pack_into("<h", out, ofs, OPAQUE)
        struct.pack_into("<II", out, track["ts_headers"] + 8 * i, 1, t_ofs)
        struct.pack_into("<II", out, track["key_headers"] + 8 * i, 1, ofs)


def patch_model(data: bytes, verts: list[tuple[float, float]], *, skins: bool,
                texture_path: str | None = None, skin_lookup: bool = True,
                rgb: tuple[float, float, float] = (1.0, 1.0, 1.0)) -> bytes:
    """Return the patched model.

    verts: four (x, y) pairs in the source vertex order (-,-), (+,-), (-,+), (+,+), z becomes 0.
    skins: True turns the texture into creature skin 1 (type 11, empty name) and, with
    `skin_lookup`, appends the replaceable-texture lookup that type needs (False reproduces the
    first M1 build, for the 90625 diagnostic only); False keeps the hard-coded path and rewrites it
    to `texture_path` (must fit the source name's capacity).
    rgb: the color track's value (0..1 per channel), the tint the client multiplies the texture by.
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

    # color: the tint; color alpha and transparency: one opaque key per animation (static)
    if len(rgb) != 3 or not all(0.0 <= v <= 1.0 for v in rgb):
        raise M2Error(f"color {rgb!r}: three floats in 0..1")
    info = inspect(data)
    if not any(count for count, _ofs in info["rgb_track"]["keys"]):
        raise M2Error("the color track has no keys to hold the tint")
    for count, ofs in info["rgb_track"]["keys"]:
        for i in range(count):
            struct.pack_into("<3f", out, ofs + 12 * i, *rgb)
    for track in (info["alpha_track"], info["transp_track"]):
        _static_opaque(out, track)

    # texture entry
    tex = facts["texture"]
    if skins:
        struct.pack_into("<IIII", out, tex, TEXTURE_TYPE_SKIN1, 0, 0, 0)
        if skin_lookup:
            out += bytes(-len(out) % 16)
            struct.pack_into("<II", out, OFS_REPLACEABLE_LOOKUP, len(SKIN1_LOOKUP), len(out))
            out += struct.pack(f"<{len(SKIN1_LOOKUP)}h", *SKIN1_LOOKUP)
            out += bytes(-len(out) % 16)
        return bytes(out)
    if not texture_path:
        raise M2Error("texture_path is required without skins")
    return set_texture_path(bytes(out), texture_path)


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
