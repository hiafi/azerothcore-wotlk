"""
Boss-mechanics marker assets (dungeon mechanics M1, WP-A): lib/blp_write.py, lib/m2_patch.py and
patch_bossmechanics_markers.py.

The M2 tests need the extracted Ascension source model; they read it from `var/bossmech-src/` (run
`patch_bossmechanics_markers.py --extract <patch-N.MPQ>` once) and skip with a message when it is
absent. Everything else (BLP, texture geometry, the id table, the SQL) needs no source files.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_bossmechanics_markers.py
"""

from __future__ import annotations

import contextlib
import io
import math
import struct
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import patch_bossmechanics_markers as pbm  # noqa: E402
from lib import blp_write, m2_patch  # noqa: E402

SRC_DIR = TOOL_ROOT / "var" / "bossmech-src" / "SPELLS"
HAVE_SOURCE = (SRC_DIR / pbm.SOURCE_MODEL).is_file() and (SRC_DIR / pbm.SOURCE_SKIN).is_file()
NEEDS_SOURCE = unittest.skipUnless(HAVE_SOURCE, f"extracted source model not found under {SRC_DIR}")
HAVE_SOURCE_TEXTURE = (SRC_DIR / pbm.SOURCE_TEXTURE).is_file()
NEEDS_SOURCE_TEXTURE = unittest.skipUnless(HAVE_SOURCE_TEXTURE, f"{pbm.SOURCE_TEXTURE} not found under {SRC_DIR}")

# Ascension's known-good DXT5 texture for this model family (SOURCE_TEXTURE, 512 x 512), measured 2026-11-02.
KNOWN_GOOD_512_OFFSETS = (1172, 263316, 328852, 345236, 349332, 350356, 350612, 350676, 350692, 350708)
KNOWN_GOOD_512_SIZES = (262144, 65536, 16384, 4096, 1024, 256, 64, 16, 16, 16)
KNOWN_GOOD_512_FILE_SIZE = 350724


def _src() -> tuple[bytes, bytes]:
    return (SRC_DIR / pbm.SOURCE_MODEL).read_bytes(), (SRC_DIR / pbm.SOURCE_SKIN).read_bytes()


# --- BLP ---

class BlpRoundTripTest(unittest.TestCase):
    """The palette writer (kept for the 90691 diagnostic and --texture-format palette)."""

    def test_header_mips_and_planes(self):
        w = h = 64
        alpha = bytes((x * 4) % 256 for x in range(w * h))
        data = blp_write.encode_blp_palette(w, h, (10, 20, 30), alpha)
        self.assertEqual(data[:4], b"BLP2")
        self.assertEqual(struct.unpack_from("<I", data, 4)[0], 1)
        self.assertEqual(struct.unpack_from("<4B", data, 8), (1, 8, 0, 1))  # palette, alpha 8, alpha enc 0, mips
        self.assertEqual(struct.unpack_from("<II", data, 12), (w, h))
        b = blp_write.read_blp(data)
        self.assertEqual(b["mip_count"], 7)                                  # 64, 32, 16, 8, 4, 2, 1
        self.assertEqual(b["palette0_rgb"], (10, 20, 30))
        for level, mip in enumerate(b["mips"]):
            side = max(1, w >> level)
            self.assertEqual(mip["width"], side)
            self.assertEqual(len(mip["indices"]), side * side)
            self.assertEqual(len(mip["alpha"]), side * side)                 # the 8-bit alpha plane
            self.assertEqual(b["mip_sizes"][level], 2 * side * side)
        self.assertEqual(b["mips"][0]["alpha"], alpha)
        self.assertEqual(set(b["mips"][0]["indices"]), {0})
        self.assertEqual(b["mip_offsets"][0], blp_write.DATA_START)
        self.assertEqual(b["mip_offsets"][1], blp_write.DATA_START + 2 * w * h)
        self.assertEqual(b["file_size"], blp_write.DATA_START + sum(b["mip_sizes"]))

    def test_mip_chain_averages_alpha(self):
        alpha = bytes([200, 100, 0, 0] * 2 + [0] * 8)                        # 4x4, top-left 2x2 = 200,100,0,0
        b = blp_write.read_blp(blp_write.encode_blp_palette(4, 4, (1, 2, 3), bytes(alpha)))
        self.assertEqual(b["mips"][1]["alpha"][0], (200 + 100 + 200 + 100 + 2) >> 2)
        self.assertEqual(b["mip_count"], 3)

    def test_512_has_ten_levels_and_256_nine(self):
        self.assertEqual(blp_write.mip_count(512, 512), 10)
        self.assertEqual(blp_write.mip_count(256, 256), 9)
        self.assertEqual(blp_write.mip_count(1, 1), 1)

    def test_alpha_length_is_checked(self):
        with self.assertRaises(ValueError):
            blp_write.encode_blp_palette(4, 4, (0, 0, 0), bytes(15))
        with self.assertRaises(ValueError):
            blp_write.encode_blp(4, 4, (0, 0, 0), bytes(15))

    def test_pillow_reads_the_header(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not importable")
        for data in (blp_write.encode_blp_palette(32, 32, (255, 0, 0), bytes(32 * 32)),
                     blp_write.encode_blp(32, 32, (255, 0, 0), bytes(32 * 32))):
            with tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / "x.blp"
                p.write_bytes(data)
                with Image.open(p) as im:
                    self.assertEqual(im.size, (32, 32))


def _dxt5_block_roundtrip(values: list[int]) -> list[int]:
    block = blp_write.dxt5_alpha_blocks(bytes(values), 4, 4)[0]
    data = block + struct.pack("<HHI", 0, 0, 0)
    return list(blp_write.decode_dxt5(data, 4, 4)[1])


class Dxt5Test(unittest.TestCase):
    """The DXT5 writer (the default since the 2026-11-02 fix) and the decoder the tests read it back with."""

    def test_header_matches_the_known_good_ascension_texture(self):
        disc = pbm.disc_alpha(512, pbm.FILL_ALPHA)
        data = blp_write.encode_blp(512, 512, pbm.COLOUR_RGB["red"], disc)
        self.assertEqual(data[:4], b"BLP2")
        self.assertEqual(struct.unpack_from("<I", data, 4)[0], 1)
        self.assertEqual(struct.unpack_from("<4B", data, 8), (2, 8, 7, 1))   # DXT, alpha 8, DXT5, mips
        self.assertEqual(struct.unpack_from("<II", data, 12), (512, 512))
        self.assertEqual(struct.unpack_from("<16I", data, 20), KNOWN_GOOD_512_OFFSETS + (0,) * 6)
        self.assertEqual(struct.unpack_from("<16I", data, 84), KNOWN_GOOD_512_SIZES + (0,) * 6)
        self.assertEqual(data[blp_write.HEADER_SIZE:blp_write.DATA_START], bytes(blp_write.PALETTE_SIZE))
        self.assertEqual(len(data), KNOWN_GOOD_512_FILE_SIZE)

    @NEEDS_SOURCE_TEXTURE
    def test_header_bytes_equal_the_real_file(self):
        good = (SRC_DIR / pbm.SOURCE_TEXTURE).read_bytes()
        ours = blp_write.encode_blp(512, 512, (1, 2, 3), bytes(512 * 512))
        self.assertEqual(ours[:blp_write.DATA_START], good[:blp_write.DATA_START])  # header + palette block
        self.assertEqual(len(ours), len(good))
        b = blp_write.read_blp(good)                                         # the decoder reads the real one
        self.assertEqual(b["mip_count"], 10)
        centre = 256 * 512 + 256
        self.assertEqual(b["mips"][0]["rgb"][centre][1:], (0, 0))           # a red file
        self.assertGreater(b["mips"][0]["rgb"][centre][0], 100)

    def test_256_level_sizes(self):
        b = blp_write.read_blp(blp_write.encode_blp(256, 256, (9, 9, 9), bytes(256 * 256)))
        self.assertEqual(b["mip_count"], 9)
        self.assertEqual(b["mip_sizes"][:9], (65536, 16384, 4096, 1024, 256, 64, 16, 16, 16))
        self.assertEqual(b["mip_offsets"][0], blp_write.DATA_START)
        self.assertEqual(b["file_size"], blp_write.DATA_START + sum(b["mip_sizes"]))

    def test_flat_colour_block(self):
        for rgb in pbm.COLOUR_RGB.values():
            data = blp_write.encode_blp(8, 8, rgb, bytes([200] * 64))
            b = blp_write.read_blp(data)
            want = blp_write.expand565(blp_write.rgb565(rgb))
            for mip in b["mips"]:
                self.assertEqual(set(mip["rgb"]), {want})
                self.assertEqual(set(mip["alpha"]), {200})
            for level, ofs in enumerate(b["mip_offsets"][:b["mip_count"]]):
                c0, c1, bits = struct.unpack_from("<HHI", data, ofs + 8)
                self.assertEqual((c0, c1, bits), (blp_write.rgb565(rgb), blp_write.rgb565(rgb), 0), level)
            self.assertLessEqual(max(abs(a - w) for a, w in zip(rgb, want)), 4)

    def test_alpha_blocks(self):
        self.assertEqual(_dxt5_block_roundtrip([77] * 16), [77] * 16)                     # all equal
        self.assertEqual(_dxt5_block_roundtrip([0, 255] * 8), [0, 255] * 8)               # the explicit codes
        two = [0] * 8 + [230] * 8
        self.assertEqual(_dxt5_block_roundtrip(two), two)                                  # endpoints exact
        ramp = [i * 17 for i in range(16)]
        got = _dxt5_block_roundtrip(ramp)
        self.assertLessEqual(max(abs(a - b) for a, b in zip(got, ramp)), 19)               # 8 levels over 255
        rim = [0, 0, 90, 90, 0, 230, 230, 90, 0, 0, 90, 90, 255, 0, 90, 90]
        got = _dxt5_block_roundtrip(rim)                                                   # 0, 255 + 2 inner values
        self.assertEqual(got, rim)

    def test_every_marker_plane_round_trips(self):
        for name, plane, size in (("disc", pbm.disc_alpha(pbm.BIG, pbm.FILL_ALPHA), pbm.BIG),
                                  ("timer", pbm.disc_alpha(pbm.BIG, 0, pbm.TIMER_RIM_FRAC), pbm.BIG),
                                  ("cone", pbm.cone_alpha(pbm.SMALL, 90), pbm.SMALL),
                                  ("outline cone", pbm.cone_alpha(pbm.SMALL, 90, pbm.OUTLINE_FILL_ALPHA), pbm.SMALL),
                                  ("line", pbm.line_alpha(pbm.SMALL), pbm.SMALL)):
            b = blp_write.read_blp(blp_write.encode_blp(size, size, (1, 2, 3), plane))
            got = b["mips"][0]["alpha"]
            errors = [abs(x - y) for x, y in zip(got, plane)]
            self.assertLessEqual(max(errors), 40, name)                    # worst block: a rim edge
            self.assertLess(sum(errors) / len(errors), 1.0, name)
            self.assertFalse(any(x for x, y in zip(got, plane) if y == 0),
                             f"{name}: a transparent pixel turned visible")
            self.assertTrue(all(x for x, y in zip(got, plane) if y >= 40), f"{name}: a visible pixel vanished")


# --- texture geometry ---

def _alpha_at(plane: bytes, size: int, row: int, col: int) -> int:
    return plane[row * size + col]


class TextureGeometryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.disc = pbm.disc_alpha(pbm.BIG, pbm.FILL_ALPHA)
        cls.ring = pbm.disc_alpha(pbm.BIG, pbm.OUTLINE_FILL_ALPHA)

    def test_disc_edge_sits_at_the_shape_radius(self):
        size, half, radius = pbm.BIG, pbm.BIG / 2, pbm.shape_radius(pbm.BIG)
        row = size // 2
        edge = max(c for c in range(size) if _alpha_at(self.disc, size, row, c) >= pbm.RIM_ALPHA // 2)
        self.assertLessEqual(abs((edge + 0.5 - half) - radius), 1.0)
        self.assertGreaterEqual(_alpha_at(self.disc, size, row, edge - 2), pbm.RIM_ALPHA - 1)  # the rim
        self.assertEqual(_alpha_at(self.disc, size, row, size // 2 + 100), pbm.FILL_ALPHA)      # the fill
        self.assertEqual(_alpha_at(self.disc, size, 0, 0), 0)                                  # corner outside

    def test_scale_one_is_one_yard_after_the_margin(self):
        """The shape stops MARGIN_FRAC short of the texture edge and the quad grows by the same factor, so the
        hitbox edge still lands at exactly 1 yd per unit of scale (and the line width at 1 yd)."""
        for size in (pbm.BIG, pbm.SMALL):
            self.assertAlmostEqual(pbm.shape_radius(size) / (size / 2) * pbm.QUAD_HALF, 1.0, places=9)
        self.assertAlmostEqual(pbm.QUAD_HALF, 8 / 7, places=9)
        self.assertAlmostEqual(2 * pbm.LINE_HALF * (1 - 2 * pbm.MARGIN_FRAC), 1.0, places=9)
        self.assertEqual({abs(v) for xy in pbm.QUAD for v in xy}, {pbm.QUAD_HALF})

    def test_ring_is_the_outline_faint_inside_rim_not(self):
        size = pbm.BIG
        self.assertEqual(_alpha_at(self.ring, size, size // 2, size // 2 + 100), pbm.OUTLINE_FILL_ALPHA)
        self.assertGreaterEqual(max(self.ring), pbm.RIM_ALPHA)
        self.assertLess(pbm.OUTLINE_FILL_ALPHA, pbm.FILL_ALPHA)                  # the outline reads lighter

    def test_timer_ring_is_rim_only(self):
        size, half, radius = pbm.BIG, pbm.BIG / 2, pbm.shape_radius(pbm.BIG)
        plane = pbm.disc_alpha(size, 0, pbm.TIMER_RIM_FRAC)
        row = size // 2
        cols = [c for c in range(size // 2, size) if _alpha_at(plane, size, row, c) >= pbm.RIM_ALPHA // 2]
        self.assertLessEqual(abs(max(cols) + 0.5 - half - radius), 1.0)            # outer edge at the radius
        self.assertAlmostEqual((max(cols) - min(cols) + 1) / radius, pbm.TIMER_RIM_FRAC, delta=1.5 / radius)
        self.assertEqual(_alpha_at(plane, size, row, size // 2 + 100), 0)          # empty inside the band

    def test_donut_inner_ratio(self):
        size, half, radius = pbm.SMALL, pbm.SMALL / 2, pbm.shape_radius(pbm.SMALL)
        for ratio in pbm.DONUT_RATIOS:
            for fill in (pbm.FILL_ALPHA, pbm.OUTLINE_FILL_ALPHA):
                plane = pbm.donut_alpha(size, ratio, fill)
                row = size // 2
                cols = [c for c in range(size // 2, size) if _alpha_at(plane, size, row, c) >= fill // 2]
                inner = min(cols) + 0.5 - half                   # first pixel of the ring from the centre
                outer = max(cols) + 0.5 - half
                self.assertAlmostEqual(inner / radius, ratio, delta=1.5 / radius, msg=f"ratio {ratio}")
                self.assertLessEqual(abs(outer - radius), 1.0)
                self.assertEqual(_alpha_at(plane, size, row, size // 2 + 1), 0)   # the hole is empty

    def test_cone_half_angle_and_orientation(self):
        size, half, radius = pbm.SMALL, pbm.SMALL / 2, pbm.shape_radius(pbm.SMALL)
        for angle in pbm.CONE_ANGLES:
            plane = pbm.cone_alpha(size, angle)
            for r in range(size):
                for c in range(size):
                    x, y = r + 0.5 - half, c + 0.5 - half          # x = forward (rows), y = across (columns)
                    dist = math.hypot(x, y)
                    if not 0.5 * radius <= dist <= 0.9 * radius:
                        continue
                    deg = abs(math.degrees(math.atan2(y, x)))
                    inside = _alpha_at(plane, size, r, c) >= pbm.FILL_ALPHA // 2
                    if deg < angle / 2 - 2.0:
                        self.assertTrue(inside, f"cone {angle}: ({x:.1f},{y:.1f}) {deg:.1f} deg should be inside")
                    elif deg > angle / 2 + 2.0:
                        self.assertFalse(inside, f"cone {angle}: ({x:.1f},{y:.1f}) {deg:.1f} deg should be outside")

    def test_cone_apex_is_the_centre_and_it_opens_toward_increasing_rows(self):
        plane = pbm.cone_alpha(pbm.SMALL, 60)
        size = pbm.SMALL
        self.assertGreater(_alpha_at(plane, size, size // 2 + 40, size // 2), 0)    # ahead of the apex
        self.assertEqual(_alpha_at(plane, size, size // 2 - 40, size // 2), 0)      # behind it

    def test_line_has_rims_on_the_long_edges_only(self):
        size = pbm.SMALL
        margin = int(size * pbm.MARGIN_FRAC)
        for fill in (pbm.FILL_ALPHA, pbm.OUTLINE_FILL_ALPHA):
            plane = pbm.line_alpha(size, fill)
            for row in (0, size // 2, size - 1):
                self.assertGreaterEqual(_alpha_at(plane, size, row, margin), pbm.RIM_ALPHA - 1)
                self.assertGreaterEqual(_alpha_at(plane, size, row, size - 1 - margin), pbm.RIM_ALPHA - 1)
                self.assertEqual(_alpha_at(plane, size, row, margin - 1), 0)         # the margin
                self.assertEqual(_alpha_at(plane, size, row, size - margin), 0)
                self.assertEqual(_alpha_at(plane, size, row, size // 2), fill)
            self.assertEqual(plane[:size], plane[size * (size // 2):size * (size // 2 + 1)])  # no end rim


class EdgeTexelTest(unittest.TestCase):
    """The cardinal lines: with clamp addressing an edge texel is stretched along the quad edge, so a texture
    whose shape reaches an edge at some mip draws a straight line there. Every texture keeps its edges
    transparent at every level (a line only its long edges: its open ends must reach the rows' edge)."""

    @classmethod
    def setUpClass(cls):
        cls.displays = pbm.build_displays(False)
        cls.textures = _textures(cls.displays)

    def test_edges_are_transparent_at_every_mip(self):
        seen = set()
        for d in self.displays:
            if d.texture in seen:
                continue
            seen.add(d.texture)
            b = blp_write.read_blp(self.textures[f"{d.texture}.blp"])
            line = d.shape in ("line", "line_outline")
            for level, mip in enumerate(b["mips"]):
                w, h, a = mip["width"], mip["height"], mip["alpha"]
                cols = [a[y * w] for y in range(h)] + [a[y * w + w - 1] for y in range(h)]
                self.assertEqual(set(cols), {0}, f"{d.texture} mip {level}: a long-edge texel is visible")
                if not line:
                    rows = list(a[:w]) + list(a[(h - 1) * w:])
                    self.assertEqual(set(rows), {0}, f"{d.texture} mip {level}: an edge texel is visible")
                if w >= 16:
                    self.assertGreater(max(a), 0, f"{d.texture} mip {level}: the shape vanished")

    def test_line_ends_stay_open(self):
        b = blp_write.read_blp(self.textures["bm_line_red.blp"])
        for mip in b["mips"][:5]:
            w, a = mip["width"], mip["alpha"]
            self.assertEqual(a[:w], a[(mip["height"] - 1) * w:])               # first row = last row
            self.assertGreater(a[w // 2], 0)                                    # and both are drawn

    def test_mip_edges_without_the_flags_are_kept(self):
        plane = bytes([200] * 64)
        b = blp_write.read_blp(blp_write.encode_blp(8, 8, (1, 2, 3), plane))
        self.assertEqual(set(b["mips"][0]["alpha"]), {200})
        b = blp_write.read_blp(blp_write.encode_blp(8, 8, (1, 2, 3), plane, clear_cols=True))
        a = b["mips"][0]["alpha"]
        self.assertEqual({a[y * 8] for y in range(8)} | {a[y * 8 + 7] for y in range(8)}, {0})
        self.assertEqual(a[8 + 3], 200)


# --- M2 patch ---

def _texture_entry(data: bytes) -> tuple[int, int, int, int]:
    facts = m2_patch.check_source(data, patched=True)
    return struct.unpack_from("<IIII", data, facts["texture"])


def _patched_ranges(data: bytes) -> list[tuple[int, int]]:
    """Every byte range patch_model / patch_skin may change, from the untouched source."""
    facts = m2_patch.check_source(data)
    ranges = [(facts["vertices"] + m2_patch.VERTEX_SIZE * i, facts["vertices"] + m2_patch.VERTEX_SIZE * i + 12)
              for i in range(4)]
    ranges += [(m2_patch.OFS_BBOX, m2_patch.OFS_BBOX + 24), (m2_patch.OFS_SPHERE, m2_patch.OFS_SPHERE + 4)]
    n_anim, o_anim = facts["animations"]
    ranges += [(o_anim + m2_patch.ANIM_SIZE * i + m2_patch.ANIM_BOUNDS,
                o_anim + m2_patch.ANIM_SIZE * i + m2_patch.ANIM_BOUNDS + 28) for i in range(n_anim)]
    ranges.append((facts["render_flags"] + 2, facts["render_flags"] + 4))
    info = m2_patch.inspect(data)
    for count, ofs in info["rgb_track"]["keys"]:
        ranges.append((ofs, ofs + 12 * count))
    for track in (info["alpha_track"], info["transp_track"]):
        for count, ofs in track["keys"]:
            ranges.append((ofs, ofs + 2 * count))
        for count, ofs in track["stamps"]:
            ranges.append((ofs, ofs + 4 * count))
        n = len(track["keys"])
        ranges += [(track["ts_headers"], track["ts_headers"] + 8 * n),
                   (track["key_headers"], track["key_headers"] + 8 * n)]
    ranges.append((facts["texture"], facts["texture"] + m2_patch.TEXTURE_SIZE))
    ranges.append((facts["name_ofs"], facts["name_ofs"] + facts["name_len"]))
    return ranges


def _diff_offsets(a: bytes, b: bytes) -> list[int]:
    assert len(a) == len(b)
    return [i for i in range(len(a)) if a[i] != b[i]]


@NEEDS_SOURCE
class M2PatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.skin = _src()

    def test_source_matches_what_the_handoff_measured(self):
        verts = m2_patch.vertex_positions(self.model)
        self.assertEqual(len(verts), 4)
        for x, y, z in verts:
            self.assertAlmostEqual(abs(x), 4.0846, places=3)
            self.assertAlmostEqual(abs(y), 4.0846, places=3)
            self.assertAlmostEqual(z, 0.2778, places=3)
        self.assertEqual(m2_patch.vertex_uvs(self.model), [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)])
        facts = m2_patch.check_source(self.model)
        self.assertEqual(struct.unpack_from("<HH", self.model, facts["render_flags"]), (0x15, 4))
        self.assertEqual(_texture_entry(self.model)[0], 0)

    def test_unit_quad_extents_bounds_blend_and_texture_type(self):
        out = m2_patch.patch_model(self.model, pbm.QUAD, skins=True)
        facts = m2_patch.check_source(out, patched=True)
        q = struct.unpack("<f", struct.pack("<f", pbm.QUAD_HALF))[0]        # 8/7 as the file's float32
        self.assertEqual(m2_patch.vertex_positions(out), [(-q, -q, 0.0), (q, -q, 0.0), (-q, q, 0.0), (q, q, 0.0)])
        self.assertEqual(struct.unpack_from("<6f", out, m2_patch.OFS_BBOX), (-q, -q, 0.0, q, q, 0.0))
        self.assertAlmostEqual(struct.unpack_from("<f", out, m2_patch.OFS_SPHERE)[0], math.sqrt(2) * q, places=5)
        n_anim, o_anim = facts["animations"]
        for i in range(n_anim):
            bounds = struct.unpack_from("<7f", out, o_anim + 64 * i + 32)
            self.assertEqual(bounds[:6], (-q, -q, 0.0, q, q, 0.0))
            self.assertAlmostEqual(bounds[6], math.sqrt(2) * q, places=5)
        flags, blend = struct.unpack_from("<HH", out, facts["render_flags"])
        self.assertEqual((flags, blend), (0x15, 2))                  # unlit | two-sided | no depth write, alpha
        self.assertEqual(_texture_entry(out), (11, 0, 0, 0))         # creature skin 1, empty name
        self.assertEqual(m2_patch.vertex_uvs(out), m2_patch.vertex_uvs(self.model))

    def test_texture_addressing_is_clamp(self):
        """M2 texture flags 0x1 / 0x2 are wrap X / wrap Y; the markers keep the source's 0 (clamp both), so no
        texel of the opposite edge is ever blended in at an edge."""
        self.assertEqual(_texture_entry(self.model)[1], 0)
        out = m2_patch.patch_model(self.model, pbm.QUAD, skins=False, texture_path="spells\\bm_disc_red.blp")
        self.assertEqual(_texture_entry(out)[1], 0)

    def test_skin_texture_gets_a_replaceable_lookup_entry(self):
        """The first build's green boxes: type 11 with the source's lookup [0] has no slot for skin 1."""
        self.assertEqual(m2_patch.replaceable_lookup(self.model), [0])
        out = m2_patch.patch_model(self.model, pbm.QUAD, skins=True)
        lookup = m2_patch.replaceable_lookup(out)
        self.assertEqual(len(lookup), 12)
        self.assertEqual(lookup[m2_patch.TEXTURE_TYPE_SKIN1], 0)
        self.assertEqual(set(lookup[:11]), {-1})
        self.assertEqual(len(out) % 16, 0)
        broken = m2_patch.patch_model(self.model, pbm.QUAD, skins=True, skin_lookup=False)
        self.assertEqual(m2_patch.replaceable_lookup(broken), [0])   # diagnostic 90625 only
        plain = m2_patch.patch_model(self.model, pbm.QUAD, skins=False, texture_path="spells\\bm_disc_red.blp")
        self.assertEqual(m2_patch.replaceable_lookup(plain), [0])    # type 0 needs none

    def test_colour_and_transparency_are_white_and_opaque(self):
        before = m2_patch.inspect(self.model)
        self.assertTrue(any(v != 0x7FFF for vals in before["alpha"] + before["transparency"] for v in vals),
                        "the source is not opaque, which is why it is patched")
        for skins in (True, False):
            out = m2_patch.patch_model(self.model, pbm.QUAD, skins=skins, texture_path="spells\\bm_disc_red.blp")
            after = m2_patch.inspect(out)
            self.assertTrue(all(rgb == (1.0, 1.0, 1.0) for rgb in after["rgb"]))
            # static: every animation (Stand, Hold 158, Decay 159) has exactly one opaque key at t = 0, so no
            # sequence fades in, fades out or falls back to a default value
            n_anim = m2_patch.check_source(out, patched=True)["animations"][0]
            self.assertEqual(len(after["alpha"]), n_anim)
            for vals in after["alpha"] + after["transparency"]:
                self.assertEqual(vals, [0x7FFF])
            for track in (after["alpha_track"], after["transp_track"]):
                for count, ofs in track["stamps"]:
                    self.assertEqual(count, 1)
                    self.assertEqual(struct.unpack_from("<I", out, ofs)[0], 0)

    def test_no_bone_animation_scales_or_moves_the_quad(self):
        bones = struct.unpack_from("<II", self.model, 0x2C)
        self.assertEqual(bones[0], 1)
        for track_ofs in (16, 36, 56):                                # translation, rotation, scale
            self.assertEqual(struct.unpack_from("<4xI", self.model, bones[1] + track_ofs)[0], 0)
        self.assertEqual(struct.unpack_from("<I", self.model, 0x60)[0], 0)    # no texture transforms (UV anim)
        self.assertEqual(struct.unpack_from("<I", self.model, 0x128)[0], 0)   # no particle emitters
        self.assertEqual(struct.unpack_from("<I", self.model, 0x120)[0], 0)   # no ribbons
        self.assertEqual(struct.unpack_from("<I", self.model, 0x14)[0], 0)    # no global sequences

    def test_only_the_patched_ranges_differ(self):
        allowed = _patched_ranges(self.model)
        for verts, skins in ((pbm.QUAD, True), (pbm.line_verts(17), True), (pbm.QUAD, False)):
            out = m2_patch.patch_model(self.model, verts, skins=skins, texture_path="spells\\bm_disc_red.blp")
            if skins:   # the appended replaceable lookup, and the header entry that points at it
                self.assertGreater(len(out), len(self.model))
                out = out[:m2_patch.OFS_REPLACEABLE_LOOKUP] + self.model[m2_patch.OFS_REPLACEABLE_LOOKUP:
                                                                         m2_patch.OFS_REPLACEABLE_LOOKUP + 8] \
                    + out[m2_patch.OFS_REPLACEABLE_LOOKUP + 8:len(self.model)]
            self.assertEqual(len(out), len(self.model))
            stray = [i for i in _diff_offsets(self.model, out) if not any(lo <= i < hi for lo, hi in allowed)]
            self.assertEqual(stray, [], f"bytes changed outside the patched ranges: {stray[:8]}")

    def test_line_model_runs_from_the_stalker_forward(self):
        half = struct.unpack("<f", struct.pack("<f", pbm.LINE_HALF))[0]
        for i in (0, 8, 16, pbm.LINE_STEPS - 1):
            k = pbm.line_aspect(i)
            out = m2_patch.patch_model(self.model, pbm.line_verts(i), skins=True)
            verts = m2_patch.vertex_positions(out)
            self.assertEqual({round(v[0], 5) for v in verts}, {0.0, round(k, 5)})
            self.assertEqual({v[1] for v in verts}, {-half, half})
            self.assertEqual(struct.unpack_from("<6f", out, m2_patch.OFS_BBOX)[3:5],
                             (struct.unpack_from("<f", out, m2_patch.OFS_BBOX + 12)[0], half))
            self.assertAlmostEqual(struct.unpack_from("<f", out, m2_patch.OFS_SPHERE)[0], math.hypot(k, half),
                                   places=4)
        self.assertAlmostEqual(pbm.line_aspect(pbm.LINE_STEPS - 1), 8.0)
        self.assertAlmostEqual(pbm.line_aspect(8), 2.0)

    def test_hard_coded_texture_path_without_skins(self):
        out = m2_patch.patch_model(self.model, pbm.QUAD, skins=False, texture_path="spells\\bm_cone_090_red.blp")
        ttype, _flags, length, ofs = _texture_entry(out)
        self.assertEqual(ttype, 0)
        self.assertEqual(out[ofs:ofs + length], b"spells\\bm_cone_090_red.blp\0")   # length counts the NUL only
        with self.assertRaises(m2_patch.M2Error):
            m2_patch.patch_model(self.model, pbm.QUAD, skins=False, texture_path="spells\\" + "x" * 80 + ".blp")

    def test_skin_only_changes_the_submesh_bounds(self):
        out = m2_patch.patch_skin(self.skin, pbm.line_verts(16))        # k = 4
        ofs = m2_patch.check_skin(self.skin)
        stray = [i for i in _diff_offsets(self.skin, out)
                 if not ofs + m2_patch.SUBMESH_CENTRES <= i < ofs + m2_patch.SUBMESH_CENTRES + 28]
        self.assertEqual(stray, [])
        mass, centre, radius = m2_patch.skin_submesh_bounds(out)
        self.assertEqual((mass, centre), ((2.0, 0.0, 0.0), (2.0, 0.0, 0.0)))
        self.assertAlmostEqual(radius, math.hypot(2.0, pbm.LINE_HALF), places=5)

    def test_untrusted_input_is_rejected_not_crashed_on(self):
        for bad in (b"", b"MD20", self.model[:100], b"XXXX" + self.model[4:], self.model[:4] + b"\x01\x00\x00\x00"
                    + self.model[8:]):
            with self.assertRaises(m2_patch.M2Error):
                m2_patch.check_source(bad)
        with self.assertRaises(m2_patch.M2Error):
            m2_patch.check_skin(self.skin[:40])


# --- id table, rows, files ---

_TEXTURE_CACHE: dict[int, dict[str, bytes]] = {}


def _textures(displays) -> dict[str, bytes]:
    """pbm.build_textures, built once per process (the pure-Python shapes take a few seconds)."""
    if 0 not in _TEXTURE_CACHE:
        _TEXTURE_CACHE[0] = pbm.build_textures(pbm.build_displays(True))
    wanted = {f"{d.texture}.blp" for d in displays}
    return {name: data for name, data in _TEXTURE_CACHE[0].items() if name in wanted}

def _expected_ids() -> dict[int, tuple[str, str]]:
    """{display id: (shape, colour)} written out independently (handoff §3.1 + the telegraph-fill layout)."""
    exp = {}
    colours = ["red", "yellow", "blue", "purple"]
    for c in range(4):
        exp[90500 + c] = ("disc", colours[c])
        exp[90504 + c] = ("ring", colours[c])
    for c in range(2):
        for j in range(7):
            exp[90508 + 2 * j + c] = ("donut", colours[c])
            exp[90654 + 2 * j + c] = ("donut_outline", colours[c])
        for j in range(8):
            exp[90522 + 2 * j + c] = ("cone", colours[c])
            exp[90638 + 2 * j + c] = ("cone_outline", colours[c])
        for i in range(25):
            exp[90538 + 2 * i + c] = ("line", colours[c])
            exp[90588 + 2 * i + c] = ("line_outline", colours[c])
        exp[90668 + c] = ("timer", colours[c])
    return exp


class DisplayTableTest(unittest.TestCase):
    def test_id_table_equals_the_handoff(self):
        for skins in (True, False):
            got = {d.id: (d.shape, d.colour) for d in pbm.build_displays(skins)}
            self.assertEqual(got, _expected_ids())
        self.assertEqual(min(_expected_ids()), 90500)
        self.assertEqual(max(_expected_ids()), 90669)
        self.assertEqual(len(_expected_ids()), 170)
        self.assertEqual(sorted(_expected_ids()), list(range(90500, 90670)))     # dense, no gap
        self.assertEqual((pbm.FIRST_ID, pbm.LAST_ID, pbm.BLOCK_LAST_ID), (90500, 90669, 90699))

    def test_layer_params(self):
        by_id = {d.id: d for d in pbm.build_displays(False)}
        for j, ratio in enumerate(pbm.DONUT_RATIOS):
            self.assertEqual(by_id[90508 + 2 * j].param, ratio)
            self.assertEqual(by_id[90654 + 2 * j + 1].param, ratio)
        for j, angle in enumerate(pbm.CONE_ANGLES):
            self.assertEqual(by_id[90522 + 2 * j].param, angle)
            self.assertEqual(by_id[90638 + 2 * j + 1].param, angle)
        for i in range(pbm.LINE_STEPS):
            self.assertEqual(by_id[90538 + 2 * i].verts, by_id[90588 + 2 * i + 1].verts)   # same geometry
            self.assertEqual(by_id[90588 + 2 * i].model, f"bm_outline_line_{i:02d}_red")

    def test_ladders(self):
        self.assertEqual(pbm.DONUT_RATIOS, (0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75))
        self.assertEqual(pbm.CONE_ANGLES, (30, 45, 60, 90, 120, 150, 180, 270))
        self.assertEqual(pbm.LINE_STEPS, 25)
        self.assertEqual(pbm.COLOUR_RGB["red"], (230, 40, 30))
        self.assertEqual(pbm.COLOUR_RGB["yellow"], (245, 200, 40))
        self.assertEqual(pbm.COLOUR_RGB["blue"], (40, 120, 240))
        self.assertEqual(pbm.COLOUR_RGB["purple"], (160, 70, 220))

    def test_ids_sit_in_the_bossmechanics_reservation(self):
        from lib import source  # lazy: needs ruamel, which the system python lacks (Pillow test runs there)
        ids = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        reservation = (ids.get("reservations") or {}).get("bossmechanics")
        self.assertIsNotNone(reservation, "reservations.bossmechanics is missing from source/ids.yaml (WP-B)")
        for table in ("creaturedisplayinfo", "creaturemodeldata"):
            slice_ = reservation[table]
            self.assertLessEqual(slice_["start"], 90500, table)
            self.assertGreaterEqual(slice_["end"], pbm.BLOCK_LAST_ID, table)
            self.assertLessEqual(slice_["end"], ids[table]["end"], table)

    def test_diagnostic_displays(self):
        diags = pbm.build_diagnostics()
        self.assertEqual([d.id for d in diags], list(range(90690, 90696)))
        self.assertEqual({d.binding for d in diags}, {"source", "path", "skin", "skin_broken"})
        self.assertTrue(all(pbm.DIAG_FIRST_ID <= d.id <= pbm.DIAG_LAST_ID for d in diags))
        self.assertEqual(len({d.model for d in diags}), len(diags))
        production = {d.model for skins in (True, False) for d in pbm.build_displays(skins)}
        self.assertFalse(production & {d.model for d in diags})
        from lib import source  # lazy: needs ruamel
        reservation = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")["reservations"]["bossmechanics"]
        for table in ("creaturedisplayinfo", "creaturemodeldata"):
            self.assertGreaterEqual(reservation[table]["end"], pbm.DIAG_LAST_ID, table)

    @unittest.skipUnless((TOOL_ROOT / "var" / "model-visual-dbc" / "DBFilesClient" / "CreatureModelData.dbc").is_file(),
                         "no working-copy CreatureModelData.dbc")
    def test_dbc_merge_drops_stale_rows_of_the_block_only(self):
        from lib import dbcfile, dbcfmt
        src = TOOL_ROOT / "var" / "model-visual-dbc" / "DBFilesClient" / "CreatureModelData.dbc"
        displays = pbm.build_displays(False)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CreatureModelData.dbc"
            path.write_bytes(src.read_bytes())
            rows = dbcfile.read_dbc(path, dbcfmt.CREATUREMODELDATA)
            stale = dict(rows[0], ID=90695)                           # an old diagnostic id
            outside = dict(rows[0], ID=90499)                         # the rogue's slice: never touched
            dbcfile.write_dbc(path, dbcfmt.CREATUREMODELDATA,
                              [r for r in rows if r["ID"] not in (90499, 90695)] + [stale, outside])
            pbm.merge_block(path, dbcfmt.CREATUREMODELDATA, [pbm.model_row(d) for d in displays])
            ids = {r["ID"] for r in dbcfile.read_dbc(path, dbcfmt.CREATUREMODELDATA)}
            self.assertNotIn(90695, ids)
            self.assertIn(90499, ids)
            self.assertEqual({i for i in ids if 90500 <= i <= 90699}, set(range(90500, 90670)))
            changed, removed = pbm.merge_block(path, dbcfmt.CREATUREMODELDATA, [pbm.model_row(d) for d in displays])
            self.assertEqual((changed, removed), (0, 0))              # idempotent

    def test_rows_use_one_id_for_model_and_display(self):
        for d in pbm.build_displays(True):
            m, row = pbm.model_row(d), pbm.display_row(d)
            self.assertEqual((m["ID"], row["ID"], row["ModelID"]), (d.id, d.id, d.id))
            self.assertEqual(m["ModelScale"], 1.0)
            self.assertEqual(row["CreatureModelScale"], 1.0)
            self.assertEqual(row["CreatureModelAlpha"], 255)
            self.assertEqual(row["TextureVariation_1"], d.texture)
            self.assertTrue(m["ModelName"].startswith("SPELLS\\bm_") and m["ModelName"].endswith(".mdx"))

    def test_colour_sets(self):
        for d in pbm.build_displays(True):
            if d.shape not in ("disc", "ring"):
                self.assertIn(d.colour, ("red", "yellow"))
            self.assertTrue(d.texture.endswith("_" + d.colour))

    def test_textures_are_decodable_and_the_right_size(self):
        displays = pbm.build_displays(True)
        textures = _textures(displays)
        self.assertEqual(len(textures), 74)          # 4 + 4 + 14 + 16 + 2 fill/outline circles..lines, 14 + 16 + 2 + 2
        for d in displays:
            b = blp_write.read_blp(textures[f"{d.texture}.blp"])
            self.assertEqual((b["width"], b["height"]), (d.size, d.size))
            self.assertEqual((b["encoding"], b["alpha_depth"], b["alpha_encoding"]), (2, 8, 7))
            self.assertEqual(b["mips"][0]["rgb0"], blp_write.expand565(blp_write.rgb565(pbm.COLOUR_RGB[d.colour])))
            self.assertEqual(d.size, 512 if d.shape in ("disc", "ring", "timer") else 256)
            self.assertEqual(b["mip_count"], 10 if d.size == 512 else 9)

    def test_sql_passes_the_codestyle_checks(self):
        script = REPO_ROOT / "apps" / "codestyle" / "codestyle-sql.py"
        text = script.read_text(encoding="utf-8").split("# Collect all files from matching directories")[0]
        ns: dict = {"__name__": "codestyle_sql_under_test"}
        exec(compile(text, str(script), "exec"), ns)
        self.assertIn("BETWEEN 90500 AND 90699;", pbm.build_pending_sql(pbm.build_displays(True)))
        sql = pbm.build_pending_sql(pbm.build_displays(False) + pbm.build_diagnostics())
        self.assertIn("DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90500 AND 90699;", sql)
        self.assertIn("DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90500 AND 90699;", sql)
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False, encoding="utf-8") as f:
            f.write(sql)
            path = Path(f.name)
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), path.open(encoding="utf-8") as fh:
                for name in ("multiple_blank_lines_check", "trailing_whitespace_check", "sql_check",
                             "insert_delete_safety_check", "semicolon_check", "backtick_check",
                             "non_innodb_engine_check"):
                    ns[name](fh, str(path))
        finally:
            path.unlink()
        failed = {k: v for k, v in ns["results"].items() if v != "Passed"}
        self.assertEqual(failed, {}, buf.getvalue())


@NEEDS_SOURCE
class OutputFilesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.skin = _src()

    def _files(self, skins: bool, diagnostics: bool = False):
        displays = pbm.build_displays(skins)
        files = {**pbm.build_models(displays, self.model, self.skin), **_textures(displays)}
        if diagnostics:
            diags = pbm.build_diagnostics()
            files.update(pbm.build_models(diags, self.model, self.skin))
            files.update(pbm.build_textures(diags, "dxt5", (SRC_DIR / pbm.SOURCE_TEXTURE).read_bytes()))
            displays = displays + diags
        return displays, files

    def _check_rows_resolve(self, displays, files):
        with tempfile.TemporaryDirectory() as tmp:
            pbm.write_assets(Path(tmp), files)
            on_disk = {p.name for p in Path(tmp).iterdir()}
        for d in displays:
            model = pbm.model_row(d)["ModelName"].split("\\")[-1].removesuffix(".mdx")
            self.assertIn(f"{model}.m2", on_disk)
            self.assertIn(f"{model}00.skin", on_disk)
            data = files[f"{model}.m2"]
            ttype, _flags, length, ofs = _texture_entry(data)
            if ttype == 0:      # the texture the model itself names
                path = data[ofs:ofs + length].split(b"\0")[0].decode()
                self.assertTrue(path.startswith("spells\\"), path)
                self.assertIn(path.split("\\", 1)[1], on_disk, d.id)
                self.assertEqual(path, f"spells\\{d.texture}.blp", d.id)
            else:               # the texture CreatureDisplayInfo hands the skin slot
                self.assertEqual(ttype, 11)
                self.assertIn(f"{pbm.display_row(d)['TextureVariation_1']}.blp", on_disk)

    def test_every_display_row_has_its_model_skin_and_texture(self):
        for skins in (True, False):
            self._check_rows_resolve(*self._files(skins))

    @NEEDS_SOURCE_TEXTURE
    def test_diagnostic_rows_resolve_and_bind_as_named(self):
        displays, files = self._files(False, diagnostics=True)
        self._check_rows_resolve(displays, files)
        by_id = {d.id: d for d in displays}
        self.assertEqual(files["bm_diag_asc_red.blp"], (SRC_DIR / pbm.SOURCE_TEXTURE).read_bytes())
        self.assertEqual(blp_write.read_blp(files["bm_diag_pal_red.blp"])["encoding"], 1)
        self.assertEqual(blp_write.read_blp(files["bm_disc_red.blp"])["encoding"], 2)
        src = files["bm_diag_src.m2"]                            # the untouched source apart from its path
        self.assertEqual(m2_patch.vertex_positions(src), m2_patch.vertex_positions(self.model))
        self.assertEqual(files["bm_diag_src00.skin"], self.skin)
        self.assertEqual(m2_patch.replaceable_lookup(files["bm_diag_skin.m2"])[11], 0)
        self.assertEqual(m2_patch.replaceable_lookup(files["bm_diag_oldskin.m2"]), [0])
        self.assertEqual(by_id[90693].texture, "bm_disc_red")
        self.assertEqual(files["bm_diag_dxt.m2"], files["bm_disc_red.m2"])   # 90693 is exactly 90500

    def test_skins_mode_shares_models(self):
        displays, files = self._files(True)
        models = {n for n in files if n.endswith(".m2")}
        self.assertEqual(len(models), 26)                       # one quad + 25 line lengths
        for name in models:
            self.assertEqual(_texture_entry(files[name])[0], 11, name)
            self.assertEqual(m2_patch.replaceable_lookup(files[name])[11], 0, name)

    def test_no_skins_gives_170_models_with_hard_coded_paths(self):
        displays, files = self._files(False)
        models = {n for n in files if n.endswith(".m2")}
        self.assertEqual(len(models), 170)
        self.assertEqual(len({n for n in files if n.endswith(".skin")}), 170)
        for d in displays:
            data = files[f"{d.model}.m2"]
            ttype, _flags, length, ofs = _texture_entry(data)
            self.assertEqual(ttype, 0)
            self.assertEqual(data[ofs:ofs + length], f"spells\\{d.texture}.blp\0".encode())
            self.assertIn(f"{d.texture}.blp", files)

    def test_rerun_removes_stale_files_of_the_other_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            keep = Path(tmp) / "other_model.m2"
            keep.write_bytes(b"x")
            _, skin_files = self._files(True)
            pbm.write_assets(Path(tmp), skin_files)
            _, plain_files = self._files(False)
            written, removed = pbm.write_assets(Path(tmp), plain_files)
            self.assertGreater(removed, 0)
            self.assertTrue(keep.exists(), "files without the bm_ prefix are never touched")
            self.assertFalse((Path(tmp) / "bm_quad.m2").exists())


# --- resolve spell attributes (source/npcs/boss_mechanics.py; review H1) ---

class ResolveSpellAttributesTest(unittest.TestCase):
    """The built 205001-205007 rows carry the handoff 3.6 attribute set plus SPELL_ATTR1_NO_REFLECTION.

    DefenseType 1 makes every school DmgClass MAGIC, which Spell Reflection would bounce onto the marker; ALWAYS_HIT
    does not stop the reflect roll (Object.cpp, the Spell const* SpellHitResult overload), so 0x80 is required.
    Values per src/server/shared/SharedDefines.h.
    """

    ATTR1_NO_REDIRECTION = 0x00000008
    ATTR1_NO_REFLECTION = 0x00000080
    ATTR1_NO_THREAT = 0x00000400

    @classmethod
    def setUpClass(cls):
        from lib import build, source, spell_tables  # noqa: E402
        from lib.dsl import registry  # noqa: E402
        from lib.reuse import ReuseContext  # noqa: E402

        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        reg = registry.load_class_file(
            TOOL_ROOT / "source" / "npcs" / "boss_mechanics.py", ids_cfg=ids_cfg, existing_creature_rows={},
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS)
        reuse = ReuseContext({}, ids_cfg)
        cls.rows = {int(e["id"]): build.build_spell_row(e, reuse) for e in reg.spells}

    def test_every_resolve_spell_has_the_pinned_set_and_no_reflection(self):
        resolve = [sid for sid in self.rows if 205001 <= sid <= 205007]
        self.assertEqual(sorted(resolve), list(range(205001, 205008)))
        for sid in resolve:
            row = self.rows[sid]
            self.assertEqual(row["Attributes"], 0x00200000, sid)
            self.assertEqual(row["AttributesEx"], self.ATTR1_NO_REDIRECTION | self.ATTR1_NO_REFLECTION
                             | self.ATTR1_NO_THREAT, sid)
            self.assertEqual(row["AttributesEx"], 0x488, sid)
            self.assertEqual(row["AttributesEx2"], 0x20000004, sid)
            self.assertEqual(row["AttributesEx3"], 0x20040200, sid)
            self.assertEqual(row["AttributesEx4"], 0x00000001, sid)
            self.assertEqual(row["DefenseType"], 1, sid)


if __name__ == "__main__":
    unittest.main()
