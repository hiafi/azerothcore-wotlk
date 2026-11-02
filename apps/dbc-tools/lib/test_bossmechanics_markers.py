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
    """The palette writer (kept for the 91991 diagnostic and --texture-format palette)."""

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
        data = blp_write.encode_blp(512, 512, pbm.COLOR_RGB["red"], disc)
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

    def test_flat_color_block(self):
        for rgb in (*pbm.COLOR_RGB.values(), pbm.WHITE):
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
            for row in (size // 2, size // 2 + 37, size - 1):
                self.assertGreaterEqual(_alpha_at(plane, size, row, margin), pbm.RIM_ALPHA - 1)
                self.assertGreaterEqual(_alpha_at(plane, size, row, size - 1 - margin), pbm.RIM_ALPHA - 1)
                self.assertEqual(_alpha_at(plane, size, row, margin - 1), 0)         # the margin
                self.assertEqual(_alpha_at(plane, size, row, size - margin), 0)
                self.assertEqual(_alpha_at(plane, size, row, size // 2), fill)
            self.assertEqual(plane[size * (size // 2):size * (size // 2 + 1)], plane[size * (size - 1):])  # no end rim
            full = pbm.line_alpha(size, fill, half=False)                           # the probe: the whole strip
            self.assertEqual(full[:size], full[size * (size - 1):])
            self.assertEqual(full[size * (size // 2):], plane[size * (size // 2):])

    def test_line_draws_only_its_forward_half(self):
        """M1-FIX-LINES: the line model is symmetric (x in [-k, k]); the texture draws only v >= 1/2, which
        model +X carries (the cone's mapping), so the line runs from the stalker forward whatever the client
        does with an off-centre origin."""
        size = pbm.SMALL
        plane = pbm.line_alpha(size)
        self.assertEqual(set(plane[:size * (size // 2)]), {0})                      # rows v < 1/2: nothing
        self.assertEqual(_alpha_at(plane, size, size // 2, size // 2), pbm.FILL_ALPHA)  # the first drawn row
        verts = pbm.line_verts(pbm.LINE_UNIT_STEP)
        self.assertEqual({v[0] for v in verts}, {-1.0, 1.0})
        # The same direction as a cone: the cone opens toward increasing rows too.
        cone = pbm.cone_alpha(size, 60)
        self.assertGreater(_alpha_at(cone, size, size // 2 + 40, size // 2), 0)


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
            line = d.shape in ("line", "line_outline", "probe_line")
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
        """The far end (last row) is drawn up to the edge; the start sits on the texel boundary at v = 1/2 at
        every mip down to four rows (below that the cleared long edges are the whole texture)."""
        b = blp_write.read_blp(self.textures["bm_line.blp"])
        for mip in b["mips"]:
            w, h, a = mip["width"], mip["height"], mip["alpha"]
            if w < 4:
                break
            self.assertGreater(a[(h - 1) * w + w // 2], 0)                      # the far end is drawn
            self.assertEqual(a[(h // 2) * w:(h // 2 + 1) * w], a[(h - 1) * w:])  # first drawn row = last row
            self.assertEqual(set(a[:(h // 2) * w]), {0})                        # the back half stays empty

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
        self.assertEqual(m2_patch.replaceable_lookup(broken), [0])   # diagnostic 91995 only
        plain = m2_patch.patch_model(self.model, pbm.QUAD, skins=False, texture_path="spells\\bm_disc_red.blp")
        self.assertEqual(m2_patch.replaceable_lookup(plain), [0])    # type 0 needs none

    def test_color_is_the_tint_and_transparency_is_opaque(self):
        before = m2_patch.inspect(self.model)
        self.assertTrue(any(v != 0x7FFF for vals in before["alpha"] + before["transparency"] for v in vals),
                        "the source is not opaque, which is why it is patched")
        self.assertEqual(before["rgb"], [(1.0, 1.0, 1.0)])                   # one RGB key, white, Stand only
        self.assertEqual(len(before["rgb_track"]["keys"]), 1)
        for skins in (True, False):
            out = m2_patch.patch_model(self.model, pbm.QUAD, skins=skins, texture_path="spells\\bm_disc.blp")
            after = m2_patch.inspect(out)
            self.assertTrue(all(rgb == (1.0, 1.0, 1.0) for rgb in after["rgb"]))     # the default tint is white
            blue = pbm.tint_floats(pbm.COLOR_RGB["blue"])
            tinted = m2_patch.inspect(m2_patch.patch_model(self.model, pbm.QUAD, skins=skins,
                                                           texture_path="spells\\bm_disc.blp", rgb=blue))
            self.assertEqual(len(tinted["rgb"]), 1)
            for got, want in zip(tinted["rgb"][0], blue):
                self.assertAlmostEqual(got, want, places=6)
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
            out = m2_patch.patch_model(self.model, verts, skins=skins, texture_path="spells\\bm_disc.blp",
                                       rgb=pbm.tint_floats(pbm.COLOR_RGB["teal"]))
            if skins:   # the appended replaceable lookup, and the header entry that points at it
                self.assertGreater(len(out), len(self.model))
                out = out[:m2_patch.OFS_REPLACEABLE_LOOKUP] + self.model[m2_patch.OFS_REPLACEABLE_LOOKUP:
                                                                         m2_patch.OFS_REPLACEABLE_LOOKUP + 8] \
                    + out[m2_patch.OFS_REPLACEABLE_LOOKUP + 8:len(self.model)]
            self.assertEqual(len(out), len(self.model))
            stray = [i for i in _diff_offsets(self.model, out) if not any(lo <= i < hi for lo, hi in allowed)]
            self.assertEqual(stray, [], f"bytes changed outside the patched ranges: {stray[:8]}")

    def test_line_model_is_symmetric_and_v_runs_forward(self):
        """M1-FIX-LINES: x in [-k, k], centred on the stalker, with v = 1 at +X (the cone's mapping), so the
        texture's drawn half (v >= 1/2) is x in [0, k], ahead of the stalker."""
        half = struct.unpack("<f", struct.pack("<f", pbm.LINE_HALF))[0]
        for i in (0, 8, 16, pbm.LINE_STEPS - 1):
            k = struct.unpack("<f", struct.pack("<f", pbm.line_aspect(i)))[0]
            out = m2_patch.patch_model(self.model, pbm.line_verts(i), skins=True)
            verts = m2_patch.vertex_positions(out)
            self.assertEqual({v[0] for v in verts}, {-k, k})
            self.assertEqual({v[1] for v in verts}, {-half, half})
            for (x, _y, _z), (_u, v) in zip(verts, m2_patch.vertex_uvs(out)):
                self.assertEqual(v, 1.0 if x > 0 else 0.0)                     # v follows +X
            box = struct.unpack_from("<6f", out, m2_patch.OFS_BBOX)
            self.assertEqual((box[0], box[3]), (-k, k))
            self.assertAlmostEqual(struct.unpack_from("<f", out, m2_patch.OFS_SPHERE)[0], math.hypot(k, half),
                                   places=4)
        cone = m2_patch.patch_model(self.model, pbm.QUAD, skins=True)
        for (x, _y, _z), (_u, v) in zip(m2_patch.vertex_positions(cone), m2_patch.vertex_uvs(cone)):
            self.assertEqual(v, 1.0 if x > 0 else 0.0)                         # the same mapping as the cone

    def test_line_ladder(self):
        self.assertEqual(pbm.LINE_STEPS, 33)
        self.assertAlmostEqual(pbm.line_aspect(0), 0.25)
        self.assertAlmostEqual(pbm.line_aspect(4), 0.5)
        self.assertAlmostEqual(pbm.line_aspect(pbm.LINE_UNIT_STEP), 1.0)
        self.assertAlmostEqual(pbm.line_aspect(16), 2.0)
        self.assertAlmostEqual(pbm.line_aspect(pbm.LINE_STEPS - 1), 8.0)
        for i in range(1, pbm.LINE_STEPS):
            self.assertGreater(pbm.line_aspect(i), pbm.line_aspect(i - 1))
            self.assertLessEqual(pbm.line_aspect(i) / pbm.line_aspect(i - 1), 2 ** 0.25 + 1e-9)

    def test_probe_is_the_live_line_model(self):
        (probe,) = pbm.build_probe()
        self.assertEqual((probe.id, probe.color, probe.shape), (91996, "red", "probe_line"))
        self.assertEqual({v[0] for v in probe.verts}, {0.0, pbm.PROBE_ASPECT})
        self.assertGreater(probe.id, pbm.LAST_ID)
        self.assertLessEqual(probe.id, pbm.BLOCK_LAST_ID)
        self.assertFalse(pbm.DIAG_FIRST_ID <= probe.id <= pbm.DIAG_LAST_ID)
        plane = pbm.alpha_for(probe)
        size = probe.size
        self.assertEqual(plane[:size], plane[size * (size - 1):])               # the whole strip draws
        self.assertGreater(_alpha_at(plane, size, 0, size // 2), 0)

    def test_hard_coded_texture_path_without_skins(self):
        out = m2_patch.patch_model(self.model, pbm.QUAD, skins=False, texture_path="spells\\bm_cone_090_red.blp")
        ttype, _flags, length, ofs = _texture_entry(out)
        self.assertEqual(ttype, 0)
        self.assertEqual(out[ofs:ofs + length], b"spells\\bm_cone_090_red.blp\0")   # length counts the NUL only
        with self.assertRaises(m2_patch.M2Error):
            m2_patch.patch_model(self.model, pbm.QUAD, skins=False, texture_path="spells\\" + "x" * 80 + ".blp")
        for bad in ((1.5, 0.0, 0.0), (-0.1, 0.0, 0.0), (1.0, 1.0)):
            with self.assertRaises(m2_patch.M2Error):
                m2_patch.patch_model(self.model, pbm.QUAD, skins=False, texture_path="spells\\bm_disc.blp", rgb=bad)

    def test_skin_only_changes_the_submesh_bounds(self):
        out = m2_patch.patch_skin(self.skin, pbm.probe_verts())         # x in [0, 8]
        ofs = m2_patch.check_skin(self.skin)
        stray = [i for i in _diff_offsets(self.skin, out)
                 if not ofs + m2_patch.SUBMESH_CENTRES <= i < ofs + m2_patch.SUBMESH_CENTRES + 28]
        self.assertEqual(stray, [])
        mass, centre, radius = m2_patch.skin_submesh_bounds(out)
        self.assertEqual((mass, centre), ((4.0, 0.0, 0.0), (4.0, 0.0, 0.0)))
        self.assertAlmostEqual(radius, math.hypot(4.0, pbm.LINE_HALF), places=5)
        mass, centre, _radius = m2_patch.skin_submesh_bounds(m2_patch.patch_skin(self.skin, pbm.line_verts(16)))
        self.assertEqual((mass, centre), ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))   # the symmetric line

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
        _TEXTURE_CACHE[0] = pbm.build_textures(pbm.build_displays(True) + pbm.build_probe())
    wanted = {f"{d.texture}.blp" for d in displays}
    return {name: data for name, data in _TEXTURE_CACHE[0].items() if name in wanted}

def _expected_ids() -> dict[int, tuple[str, int, str]]:
    """{display id: (shape, step, color)} written out independently (the colors-fix layout: one block of 100 ids per
    color from 91000; inside it disc, ring, timer ring, donut F/O, cone F/O, line F/O)."""
    exp = {}
    colors = ["red", "yellow", "blue", "purple", "orange", "green", "teal", "white", "black"]
    for c, color in enumerate(colors):
        base = 91000 + 100 * c
        exp[base + 0] = ("disc", 0, color)
        exp[base + 1] = ("ring", 0, color)
        exp[base + 2] = ("timer", 0, color)
        for j in range(7):
            exp[base + 3 + j] = ("donut", j, color)
            exp[base + 10 + j] = ("donut_outline", j, color)
        for j in range(8):
            exp[base + 17 + j] = ("cone", j, color)
            exp[base + 25 + j] = ("cone_outline", j, color)
        for i in range(33):
            exp[base + 33 + i] = ("line", i, color)
            exp[base + 66 + i] = ("line_outline", i, color)
    return exp


class DisplayTableTest(unittest.TestCase):
    def test_id_table_equals_the_layout(self):
        for skins in (True, False):
            got = {d.id: (d.shape, d.step, d.color) for d in pbm.build_displays(skins)}
            self.assertEqual(got, _expected_ids())
        exp = _expected_ids()
        self.assertEqual((min(exp), max(exp), len(exp)), (91000, 91898, 891))
        for c in range(9):                                      # each color block is dense: +0 .. +98, spare +99
            self.assertEqual(sorted(i for i in exp if 91000 + 100 * c <= i < 91100 + 100 * c),
                             list(range(91000 + 100 * c, 91099 + 100 * c)))
        self.assertEqual((pbm.FIRST_ID, pbm.LAST_ID, pbm.BLOCK_LAST_ID), (91000, 91898, 91999))
        self.assertEqual((pbm.OLD_FIRST_ID, pbm.OLD_LAST_ID), (90500, 90699))
        self.assertEqual((pbm.COLOR_STRIDE, pbm.PER_COLOR), (100, 99))

    def test_display_id_is_the_module_formula(self):
        """mod-boss-mechanics BossMechanicsIds.h MarkerDisplay(color, shape, step): the same numbers."""
        self.assertEqual(pbm.SHAPE_OFFSET, {"disc": 0, "ring": 1, "timer": 2, "donut": 3, "donut_outline": 10,
                                            "cone": 17, "cone_outline": 25, "line": 33, "line_outline": 66})
        self.assertEqual(pbm.display_id(0, "disc"), 91000)
        self.assertEqual(pbm.display_id(2, "ring"), 91201)
        self.assertEqual(pbm.display_id(1, "donut", 3), 91106)
        self.assertEqual(pbm.display_id(0, "cone", 3), 91020)
        self.assertEqual(pbm.display_id(3, "line_outline", 8), 91374)
        self.assertEqual(pbm.display_id(4, "line", 0), 91433)
        self.assertEqual(pbm.display_id(8, "line_outline", 32), 91898)
        for bad in ((9, "disc", 0), (-1, "disc", 0), (0, "ring", 1), (0, "cone", 8), (0, "line", 33)):
            with self.assertRaises(ValueError):
                pbm.display_id(*bad)

    def test_layer_params(self):
        by_id = {d.id: d for d in pbm.build_displays(False)}
        for c in range(len(pbm.COLORS)):
            for j, ratio in enumerate(pbm.DONUT_RATIOS):
                self.assertEqual(by_id[pbm.display_id(c, "donut", j)].param, ratio)
                self.assertEqual(by_id[pbm.display_id(c, "donut_outline", j)].param, ratio)
            for j, angle in enumerate(pbm.CONE_ANGLES):
                self.assertEqual(by_id[pbm.display_id(c, "cone", j)].param, angle)
                self.assertEqual(by_id[pbm.display_id(c, "cone_outline", j)].param, angle)
            for i in range(pbm.LINE_STEPS):
                fill, outline = by_id[pbm.display_id(c, "line", i)], by_id[pbm.display_id(c, "line_outline", i)]
                self.assertEqual(fill.verts, outline.verts)                                 # same geometry
                self.assertEqual(outline.model, f"bm_outline_line_{i:02d}_{pbm.COLORS[c]}")
                self.assertEqual(fill.model, f"bm_line_{i:02d}_{pbm.COLORS[c]}")

    def test_ladders_and_colors(self):
        self.assertEqual(pbm.DONUT_RATIOS, (0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75))
        self.assertEqual(pbm.CONE_ANGLES, (30, 45, 60, 90, 120, 150, 180, 270))
        self.assertEqual(pbm.LINE_STEPS, 33)
        self.assertEqual(pbm.COLORS, ("red", "yellow", "blue", "purple", "orange", "green", "teal", "white", "black"))
        self.assertEqual(pbm.COLOR_RGB, {
            "red": (230, 40, 30), "yellow": (245, 200, 40), "blue": (30, 140, 255), "purple": (185, 90, 250),
            "orange": (255, 130, 20), "green": (80, 225, 60), "teal": (20, 215, 200), "white": (245, 245, 245),
            "black": (0, 0, 0)})
        self.assertEqual(pbm.WHITE, (255, 255, 255))

    def test_ids_sit_in_the_bossmechanics_reservation(self):
        from lib import source  # lazy: needs ruamel, which the system python lacks (Pillow test runs there)
        ids = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        reservation = (ids.get("reservations") or {}).get("bossmechanics")
        self.assertIsNotNone(reservation, "reservations.bossmechanics is missing from source/ids.yaml (WP-B)")
        for table in ("creaturedisplayinfo", "creaturemodeldata"):
            slice_ = reservation[table]
            self.assertEqual((slice_["start"], slice_["end"]), (pbm.FIRST_ID, pbm.BLOCK_LAST_ID), table)
            self.assertLessEqual(slice_["end"], ids[table]["end"], table)
            # the old slice is free again: no reservation of any owner covers it
            for owner, tables in ids["reservations"].items():
                if table in tables:
                    self.assertFalse(tables[table]["start"] <= pbm.OLD_LAST_ID
                                     and pbm.OLD_FIRST_ID <= tables[table]["end"], (owner, table))

    def test_diagnostic_displays(self):
        diags = pbm.build_diagnostics()
        self.assertEqual([d.id for d in diags], list(range(91990, 91996)))
        self.assertEqual({d.binding for d in diags}, {"source", "path", "skin", "skin_broken"})
        self.assertTrue(all(pbm.DIAG_FIRST_ID <= d.id <= pbm.DIAG_LAST_ID for d in diags))
        self.assertGreater(pbm.DIAG_FIRST_ID, pbm.LAST_ID)
        self.assertEqual(len({d.model for d in diags}), len(diags))
        production = {d.model for skins in (True, False) for d in pbm.build_displays(skins)}
        self.assertFalse(production & {d.model for d in diags})
        for d in diags:                                          # every one draws red: in the texture or the tint
            self.assertIn(pbm.COLOR_RGB["red"], (d.tex_rgb, d.tint), d.id)
            self.assertIn(pbm.WHITE, (d.tex_rgb, d.tint), d.id)
        from lib import source  # lazy: needs ruamel
        reservation = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")["reservations"]["bossmechanics"]
        for table in ("creaturedisplayinfo", "creaturemodeldata"):
            self.assertGreaterEqual(reservation[table]["end"], pbm.DIAG_LAST_ID, table)

    @unittest.skipUnless((TOOL_ROOT / "var" / "model-visual-dbc" / "DBFilesClient" / "CreatureModelData.dbc").is_file(),
                         "no working-copy CreatureModelData.dbc")
    def test_dbc_merge_drops_our_stale_rows_only(self):
        from lib import dbcfile, dbcfmt
        displays = pbm.build_displays(False)
        for name, table, row_of, ours, foreign in (
                ("CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA, pbm.model_row,
                 {"ModelName": "SPELLS\\bm_disc_red.mdx"}, {"ModelName": "Creature\\Other\\Other.mdx"}),
                ("CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, pbm.display_row,
                 {"TextureVariation_1": "bm_disc_red"}, {"TextureVariation_1": "OtherSkin"})):
            src = TOOL_ROOT / "var" / "model-visual-dbc" / "DBFilesClient" / name
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / name
                path.write_bytes(src.read_bytes())
                rows = dbcfile.read_dbc(path, table)
                probe = {90499, 90500, 90695, 90699, 91899, 91999}
                extra = [dict(rows[0], ID=90695, **ours),            # an old diagnostic of ours: dropped
                         dict(rows[0], ID=90500, **ours),            # the old fill disc: dropped
                         dict(rows[0], ID=90699, **foreign),         # another owner in the freed slice: kept
                         dict(rows[0], ID=90499, **foreign),         # the rogue's slice: never touched
                         dict(rows[0], ID=91899, **foreign),         # a spare id of our block: cleared outright
                         dict(rows[0], ID=91999, **ours)]
                dbcfile.write_dbc(path, table, [r for r in rows if r["ID"] not in probe] + extra)
                pbm.merge_block(path, table, [row_of(d) for d in displays])
                ids = {r["ID"] for r in dbcfile.read_dbc(path, table)}
                self.assertEqual(ids & probe, {90499, 90699}, name)
                self.assertEqual({i for i in ids if 91000 <= i <= 91999}, set(_expected_ids()), name)
                self.assertFalse({i for i in ids if 90500 <= i <= 90698}, name)
                changed, removed = pbm.merge_block(path, table, [row_of(d) for d in displays])
                self.assertEqual((changed, removed), (0, 0), name)      # idempotent

    def test_rows_use_one_id_for_model_and_display(self):
        for d in pbm.build_displays(True):
            m, row = pbm.model_row(d), pbm.display_row(d)
            self.assertEqual((m["ID"], row["ID"], row["ModelID"]), (d.id, d.id, d.id))
            self.assertEqual(m["ModelScale"], 1.0)
            self.assertEqual(row["CreatureModelScale"], 1.0)
            self.assertEqual(row["CreatureModelAlpha"], 255)
            self.assertEqual(row["TextureVariation_1"], d.texture)
            self.assertTrue(m["ModelName"].startswith("SPELLS\\bm_") and m["ModelName"].endswith(".mdx"))

    def test_every_shape_step_exists_in_every_color_and_shares_one_texture(self):
        by_key: dict[tuple[str, int], list] = {}
        for d in pbm.build_displays(False):
            by_key.setdefault((d.shape, d.step), []).append(d)
            self.assertEqual(d.tex_rgb, pbm.WHITE)
            self.assertEqual(d.tint, pbm.COLOR_RGB[d.color])
            self.assertTrue(d.model.endswith("_" + d.color))
            self.assertFalse(any(d.texture.endswith("_" + c) for c in pbm.COLORS), d.texture)
        self.assertEqual(len(by_key), 99)
        for key, group in by_key.items():
            self.assertEqual([d.color for d in group], list(pbm.COLORS), key)
            self.assertEqual(len({d.texture for d in group}), 1, key)

    def test_textures_are_decodable_white_and_the_right_size(self):
        displays = pbm.build_displays(True)
        textures = _textures(displays)
        self.assertEqual(len(textures), 35)          # disc, ring, timer + 7 + 7 donuts + 8 + 8 cones + 2 lines
        self.assertEqual(len(_textures(displays + pbm.build_probe())), 36)          # + the probe's full strip
        white = blp_write.expand565(blp_write.rgb565(pbm.WHITE))
        self.assertEqual(white, (255, 255, 255))
        for d in displays:
            b = blp_write.read_blp(textures[f"{d.texture}.blp"])
            self.assertEqual((b["width"], b["height"]), (d.size, d.size))
            self.assertEqual((b["encoding"], b["alpha_depth"], b["alpha_encoding"]), (2, 8, 7))
            self.assertEqual(b["mips"][0]["rgb0"], white)
            self.assertEqual(d.size, 512 if d.shape in ("disc", "ring", "timer") else 256)
            self.assertEqual(b["mip_count"], 10 if d.size == 512 else 9)

    def test_sql_passes_the_codestyle_checks(self):
        script = REPO_ROOT / "apps" / "codestyle" / "codestyle-sql.py"
        text = script.read_text(encoding="utf-8").split("# Collect all files from matching directories")[0]
        ns: dict = {"__name__": "codestyle_sql_under_test"}
        exec(compile(text, str(script), "exec"), ns)
        self.assertIn("BETWEEN 91000 AND 91999;", pbm.build_pending_sql(pbm.build_displays(True)))
        sql = pbm.build_pending_sql(pbm.build_displays(False) + pbm.build_probe() + pbm.build_diagnostics())
        self.assertIn("DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 90500 AND 90699 AND `ModelName` LIKE "
                      "'SPELLS_bm\\_%';", sql)
        self.assertIn("DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 90500 AND 90699 AND "
                      "`TextureVariation_1` LIKE 'bm\\_%';", sql)
        self.assertIn("DELETE FROM `creaturemodeldata_dbc` WHERE `ID` BETWEEN 91000 AND 91999;", sql)
        self.assertIn("DELETE FROM `creaturedisplayinfo_dbc` WHERE `ID` BETWEEN 91000 AND 91999;", sql)
        self.assertEqual(sql.count("\n(9"), 2 * (891 + 1 + 6))  # every row, both tables
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
        displays = pbm.build_displays(skins) + pbm.build_probe()
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
        self.assertEqual(blp_write.read_blp(files["bm_disc.blp"])["encoding"], 2)
        src = files["bm_diag_src.m2"]                            # the untouched source apart from its path
        self.assertEqual(m2_patch.vertex_positions(src), m2_patch.vertex_positions(self.model))
        self.assertEqual(files["bm_diag_src00.skin"], self.skin)
        self.assertEqual(m2_patch.replaceable_lookup(files["bm_diag_skin.m2"])[11], 0)
        self.assertEqual(m2_patch.replaceable_lookup(files["bm_diag_oldskin.m2"]), [0])
        self.assertEqual(by_id[91993].texture, "bm_disc")
        self.assertEqual(files["bm_diag_dxt.m2"], files["bm_disc_red.m2"])   # 91993 is exactly 91000
        self.assertEqual(m2_patch.inspect(files["bm_diag_pal.m2"])["rgb"], [(1.0, 1.0, 1.0)])  # red texture, white

    def test_skins_mode_shares_models(self):
        displays, files = self._files(True)
        models = {n for n in files if n.endswith(".m2")}
        self.assertEqual(len(models), 34 * 9 + 1)               # one quad + 33 line lengths, per color; the probe
        for name in models - {"bm_probe_line.m2"}:
            self.assertEqual(_texture_entry(files[name])[0], 11, name)
            self.assertEqual(m2_patch.replaceable_lookup(files[name])[11], 0, name)

    def test_no_skins_gives_892_models_with_hard_coded_paths(self):
        displays, files = self._files(False)
        models = {n for n in files if n.endswith(".m2")}
        self.assertEqual(len(models), 892)                      # 891 markers + the probe
        self.assertEqual(len({n for n in files if n.endswith(".skin")}), 892)
        for d in displays:
            data = files[f"{d.model}.m2"]
            ttype, _flags, length, ofs = _texture_entry(data)
            self.assertEqual(ttype, 0)
            self.assertEqual(data[ofs:ofs + length], f"spells\\{d.texture}.blp\0".encode())
            self.assertIn(f"{d.texture}.blp", files)
            for got, want in zip(m2_patch.inspect(data)["rgb"][0], pbm.tint_floats(d.tint)):   # the color
                self.assertAlmostEqual(got, want, places=6)

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

    def test_weakened_is_ten_percent_per_stack_and_says_so(self):
        row = self.rows[205000]
        # the core adds one to BasePoints when DieSides is 1 (SpellEffectInfo::CalcValue): -11 + 1 = -10 per stack
        self.assertEqual((row["EffectBasePoints_1"], row["EffectDieSides_1"]), (-11, 1))
        self.assertEqual(row["EffectBasePoints_1"] + row["EffectDieSides_1"], -10)
        self.assertEqual(row["CumulativeAura"], 7)
        self.assertEqual(row["AuraDescription_Lang_enUS"], "Damage done reduced by $s1% per stack.")
        self.assertEqual(row["Description_Lang_enUS"],
                         "Damage done reduced by $s1% per stack, stacking up to $u times. Lasts $d.")
        self.assertEqual(row["AuraDescription_Lang_Mask"], 16712190)


if __name__ == "__main__":
    unittest.main()
