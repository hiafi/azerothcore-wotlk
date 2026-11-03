#!/usr/bin/env python3
"""
Boss-mechanics telegraph marker assets (dungeon mechanics stage M1, WP-A): 1,332 creature displays
that are flat, colored, alpha-blended floor shapes a stalker creature wears and `SetObjectScale`s
to any size. Every telegraph draws two layers (M1-FIX-TELEGRAPH-FILL-REPORT.md): a static OUTLINE
(rim + faint interior, the full hitbox from the first frame) and a FILL (rim + solid interior) that
the server grows into the outline over the warning time. An armed mine draws a DASHED RING instead.

Source model: Ascension's `SPELLS\\red_circle_filled.M2` (a 4-vertex quad) from its client backup.
The model is patched (lib/m2_patch.py) into a quad (x, y in [-QUAD_HALF, QUAD_HALF], z = 0) and 57
line models of two quads each (M1-FIX-LINE-FILL-REPORT.md): x in [-k, 0] and [0, k], y in
[-LINE_HALF, LINE_HALF], k = line_aspect(i), scale = width. The client draws a creature model centred
on its bounds (round-3 check L1), so the line stays symmetric about its origin; the back quad samples
a transparent texel region (LINE_BACK_V) and the front quad a body band that is the same in every row
(LINE_FRONT_V). The visible line runs x in [0, k], from the stalker forward, its start and far end
hard geometric edges (no texture edge to blur across a joint), and every aspect shares one texture.
Textures are generated here, not mined (lib/blp_write.py, DXT5): WHITE, with the shape in the alpha
channel, one per shape step and shared by every color. The color is the model's own: its M2Color
track (the one the skin batch's color index 0 points at) holds the color's RGB, and the client
multiplies the texture by it (M1-FIX-COLORS-REPORT.md). So each display is a small model + skin,
and the 36 textures are shared. The shape stops MARGIN_FRAC of the side short of every texture edge
it would otherwise touch, and the quad is that much bigger (QUAD_HALF = 8/7), so scale 1 is still
exactly a 1-yard radius / length / width; the edge texels are transparent at every mip level
(`encode_blp(clear_cols=..., clear_rows=...)`). The first build drew the shapes edge to edge, and
the clamped edge texels of the lower mips drew straight lines along the quad edge where the disc
touches it (N/E/S/W).

Rows written: CreatureModelData + CreatureDisplayInfo ids 91000-91833, 92000-92856 and 93000-93856
(one pair per display, the same id in both tables), into the working copy
`var/model-visual-dbc/DBFilesClient/`, with any other row of the reserved block 91000-93999 or of
the old slice 90500-90699 removed; model, skin and texture files into `var/model-visual-dbc/SPELLS/`
(packed by build_patch_m.py); `--sql-out` emits the matching server rows (DELETE of both ranges +
INSERT). Deliberately not named `patch_*_vfx_models.py`, so lib/test_id_blocks.py's constant scan of
those scripts is unaffected.

Display ids (CreatureDisplayInfo id = CreatureModelData id): one block of 100 ids per color in each
of three ranges,

    id = 91000 + 100 * c + SHAPE_OFFSET[shape] + step       the quad shapes
    id = 92000 + 100 * c + i                                 line (F), i = 0..56
    id = 93000 + 100 * c + i                                 line (O)

c = color index (COLORS: red 0, yellow 1, blue 2, purple 3, orange 4, green 5, teal 6, white 7,
black 8). Within a color's 91000 block (F = fill layer, O = outline layer):

    +0          disc (F)                    +1        ring (O)
    +2          timer ring (rim only; a donut's timer)
    +3..+9      donut (F), rho_j in (0.25 0.33 0.40 0.50 0.60 0.67 0.75)
    +10..+16    donut (O)
    +17..+24    cone (F), angle_j in (30 45 60 90 120 150 180 270) degrees
    +25..+32    cone (O)
    +33         dashed ring (rim dashes only; an armed mine)
    +34..+99    spare (+33..+98 were the line ladders before M1-FIX-LINE-FILL)

Line ladder: k_i = line_aspect(i), i = 0..56 (aspect 1/4 to 64; i = 8 is aspect 1), the same for
both layers; +57..+99 of each line block are spare. 91834-91989 are spare; 91990-91995 are the
diagnostic displays, only with --diagnostics (DIAGNOSTICS below). The line-direction probe 91996 of
round 3 is gone (L1 answered it); the block clear removes its rows. mod-boss-mechanics
`src/BossMechanicsIds.h` (`MarkerDisplay`) computes the same ids; keep both in sync.

Orientation: model +X is forward and carries v, model +Y carries u, so a cone's wedge opens toward
increasing v (down the image rows) and its apex is the texture centre. Spike S5 checked it in game
(a cone points the way the GM faces). Retail's off-centre cones (Spell-Shadow-Cone, x in [0, 100])
agree: v = 0 at their far end, and their wide end is texture row 0. Lines keep the mapping (v grows
with +X) inside each of their quads.

Texture binding (fix 2026-11-02, M1-FIX-MARKERS-REPORT.md): by default every display gets its own
model copy whose texture path is hard-coded (type 0, how the source model binds its texture; texture
flags 0 = clamp in both directions). The first build used one shared model with a type-11 skin
texture, which drew green boxes: the source's replaceable-texture lookup only maps type 0. `--skins`
restores a shared-model layout (one model per geometry and color, the texture through
TextureVariation_1) with that lookup fixed (lib/m2_patch.py); ids are the same either way.

Usage (untrusted input rule: the extracted Ascension files get their own new, empty directory):
    python3 -I apps/dbc-tools/patch_bossmechanics_markers.py --extract <patch-N.MPQ>
    python3 -I apps/dbc-tools/patch_bossmechanics_markers.py --dry-run
    python3 -I apps/dbc-tools/patch_bossmechanics_markers.py --sql-out data/sql/updates/pending_db_world/rev_<ns>.sql
`--extract` also takes the source's own texture (for the diagnostic displays 91990 and 91994).
Then run build_patch_m.py to pack SPELLS/ and the DBCs into patch-M.mpq.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfile, dbcfmt  # noqa: E402
from lib.blp_write import encode_blp, encode_blp_palette  # noqa: E402
from lib.m2_patch import patch_model, patch_skin, set_texture_path  # noqa: E402
from lib.sql_out import _table_block  # noqa: E402
from patch_priest_vfx_models import _merge, _row, model_path  # noqa: E402

DEFAULT_VAR = TOOL_ROOT / "var"
SOURCE_MODEL = "red_circle_filled.M2"
SOURCE_SKIN = "red_circle_filled00.skin"
SOURCE_TEXTURE = "red_circle_filled_editeda_circle_solid_red.blp"   # Ascension's DXT5, known good
SOURCE_ARCHIVE_PATHS = (f"SPELLS/{SOURCE_MODEL}", f"SPELLS/{SOURCE_SKIN}", f"SPELLS/{SOURCE_TEXTURE}")
PREFIX = "bm_"

# --- ids (handoff §3.1; reservations.bossmechanics in source/ids.yaml; moved to 91000-91999 by the colors fix,
# widened to 93999 by the line-fill fix for the line ladders) ---

FIRST_ID = 91000
COLOR_STRIDE = 100           # ids per color block
LINE_FIRST_ID = {"line": 92000, "line_outline": 93000}      # the line ladders' own ranges, one block per color
BLOCK_LAST_ID = 93999        # the reservation's end: the SQL and the DBC merge clear the whole block
OLD_FIRST_ID = 90500         # the slice the markers used before the colors fix (free again: see _owned)
OLD_LAST_ID = 90699
DIAG_FIRST_ID = 91990
DIAG_LAST_ID = 91995

# Color index c = position in COLORS (BossMechanics::Color in the module). RGB tuned 2026-11-02 for dark floors,
# snow and sand (M1-FIX-COLORS-REPORT.md): red and yellow unchanged (playtested), blue brighter and more saturated
# (was 40, 120, 240 and the hardest to read), purple brighter (was 160, 70, 220). Black darkens the floor (alpha
# blend of a black texel): it reads on light floors only; white is the reverse.
COLORS = ("red", "yellow", "blue", "purple", "orange", "green", "teal", "white", "black")
COLOR_RGB = {
    "red": (230, 40, 30), "yellow": (245, 200, 40), "blue": (30, 140, 255), "purple": (185, 90, 250),
    "orange": (255, 130, 20), "green": (80, 225, 60), "teal": (20, 215, 200), "white": (245, 245, 245),
    "black": (0, 0, 0),
}
WHITE = (255, 255, 255)      # every marker texture's RGB: the model's M2Color supplies the color

DONUT_RATIOS = (0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75)
CONE_ANGLES = (30, 45, 60, 90, 120, 150, 180, 270)
LINE_STEPS = 57                                  # i = 0..56, aspect 1/4 to 64
LINE_UNIT_STEP = 8                               # the step of aspect 1

# (shape, steps) in id order inside one color block: fill disc, outline ring, timer ring, then fill / outline donut
# and cone ladders and the dashed ring. SHAPE_OFFSET[shape] is the first id offset of that shape in the block. The
# two line ladders follow in LINE_FIRST_ID's ranges.
QUAD_SHAPES = (
    ("disc", 1), ("ring", 1), ("timer", 1),
    ("donut", len(DONUT_RATIOS)), ("donut_outline", len(DONUT_RATIOS)),
    ("cone", len(CONE_ANGLES)), ("cone_outline", len(CONE_ANGLES)),
    ("dashed", 1),
)
SHAPES = QUAD_SHAPES + (("line", LINE_STEPS), ("line_outline", LINE_STEPS))
SHAPE_OFFSET: dict[str, int] = {}
_next = 0
for _shape, _steps in QUAD_SHAPES:
    SHAPE_OFFSET[_shape] = _next
    _next += _steps
PER_COLOR = _next                                # 34
del _next, _shape, _steps
QUAD_LAST_ID = FIRST_ID + COLOR_STRIDE * (len(COLORS) - 1) + PER_COLOR - 1                  # 91833
LAST_ID = LINE_FIRST_ID["line_outline"] + COLOR_STRIDE * (len(COLORS) - 1) + LINE_STEPS - 1  # 93856
DISPLAY_COUNT = len(COLORS) * (PER_COLOR + 2 * LINE_STEPS)                                   # 1332


def display_id(color: int, shape: str, step: int = 0) -> int:
    """The display id of one shape step in one color (BossMechanicsIds.h `MarkerDisplay`)."""
    steps = dict(SHAPES)[shape]
    if not 0 <= color < len(COLORS) or not 0 <= step < steps:
        raise ValueError(f"no display for color {color}, {shape} step {step}")
    if shape in LINE_FIRST_ID:
        return LINE_FIRST_ID[shape] + COLOR_STRIDE * color + step
    return FIRST_ID + COLOR_STRIDE * color + SHAPE_OFFSET[shape] + step


def line_aspect(i: int) -> float:
    """k_i: the visible line is k_i long and 1 wide (scale = width). Quarter-octave steps below aspect 1
    (1/4 .. 0.84: a line shorter than wide), eighth-octave steps from 1 to 64 (MechanicMath.h LineAspect)."""
    d = i - LINE_UNIT_STEP
    return 2.0 ** (d / 4.0 if d < 0 else d / 8.0)


# --- texture look (handoff §3.9; two layers since the telegraph-fill fix) ---

FILL_ALPHA = 90             # fill layer interior (0.35)
OUTLINE_FILL_ALPHA = 50     # outline layer interior (0.2)
RIM_ALPHA = 230             # both layers' rim (0.9)
RIM_FRAC = 0.025            # rim width as a fraction of the outer radius
LINE_RIM_FRAC = 0.03        # line rim width as a fraction of the line width
TIMER_RIM_FRAC = 0.04       # the donut timer ring's band, as a fraction of its radius
DASH_COUNT = 20             # the armed-mine ring's dashes (and as many gaps)
DASH_DUTY = 0.5             # the dash's share of one dash + gap period
BIG = 512                   # disc, ring and timer ring
SMALL = 256                 # everything else

# Transparent margin: the shape stops this fraction of the side short of each texture edge it would
# touch; the geometry grows by the same factor, so a scale of 1 is still exactly 1 yd.
MARGIN_FRAC = 1.0 / 16.0
QUAD_HALF = 0.5 / (0.5 - MARGIN_FRAC)           # 8/7: quad half-size per yard of radius
LINE_HALF = 0.5 * QUAD_HALF                      # 4/7: line model half-width per yard of width


def shape_radius(size: int) -> float:
    """Radius in pixels of a disc / ring / donut / cone shape (the hitbox edge) in a size x size texture."""
    return size * (0.5 - MARGIN_FRAC)


def _cov(sd: float) -> float:
    """Pixel coverage from a signed distance in pixels (positive = outside), linear over one pixel."""
    return min(1.0, max(0.0, 0.5 - sd))


def _byte(value: float) -> int:
    return min(255, max(0, int(round(value))))


def _plane(size: int, fn) -> bytes:
    out = bytearray(size * size)
    i = 0
    for r in range(size):
        for c in range(size):
            out[i] = _byte(fn(r + 0.5 - size / 2.0, c + 0.5 - size / 2.0))
            i += 1
    return bytes(out)


def _shaded(fill: float, sd_out: float, rim: float) -> float:
    """Alpha for a shape with a rim: fill inside the rim, rim alpha in the rim, antialiased edges."""
    c_out = _cov(sd_out)
    c_in = _cov(sd_out + rim)
    return fill * c_in + RIM_ALPHA * (c_out - c_in)


def disc_alpha(size: int, fill: int, rim_frac: float = RIM_FRAC) -> bytes:
    """A disc of shape_radius with a rim (fill 0 = a rim-only ring)."""
    radius = shape_radius(size)
    rim = rim_frac * radius
    return _plane(size, lambda x, y: _shaded(fill, math.hypot(x, y) - radius, rim))


def donut_alpha(size: int, ratio: float, fill: int = FILL_ALPHA) -> bytes:
    radius = shape_radius(size)
    rim = RIM_FRAC * radius

    def alpha(x: float, y: float) -> float:
        d = math.hypot(x, y)
        return _shaded(fill, max(d - radius, ratio * radius - d), rim)

    return _plane(size, alpha)


def cone_alpha(size: int, angle_deg: float, fill: int = FILL_ALPHA) -> bytes:
    """Apex at the texture centre, wedge opening toward +x (increasing row = increasing v)."""
    radius = shape_radius(size)
    rim = RIM_FRAC * radius
    half = math.radians(angle_deg / 2.0)
    s, c = math.sin(half), math.cos(half)
    concave = angle_deg > 180.0

    def alpha(x: float, y: float) -> float:
        d1 = -x * s + y * c          # outward normal of the +half side
        d2 = -x * s - y * c          # outward normal of the -half side
        sd_ang = min(d1, d2) if concave else max(d1, d2)
        return _shaded(fill, max(math.hypot(x, y) - radius, sd_ang), rim)

    return _plane(size, alpha)


def dashed_alpha(size: int, dashes: int = DASH_COUNT, duty: float = DASH_DUTY) -> bytes:
    """The armed mine's ring: the outline's rim (RIM_FRAC of the radius, RIM_ALPHA) cut into `dashes` dashes,
    one centred on +X (model forward), with an empty interior. Antialiased along the band and at the dash ends."""
    radius = shape_radius(size)
    rim = RIM_FRAC * radius

    def alpha(x: float, y: float) -> float:
        d = math.hypot(x, y)
        sd_band = max(d - radius, (radius - rim) - d)
        phase = (math.atan2(y, x) / (2 * math.pi) * dashes + duty / 2) % 1.0
        period = 2 * math.pi * max(d, 1e-6) / dashes          # pixels along the arc per dash + gap
        inside = min(phase, duty - phase) if phase < duty else -min(phase - duty, 1.0 - phase)
        return RIM_ALPHA * _cov(max(sd_band, -inside * period))

    return _plane(size, alpha)


# Line UVs (M1-FIX-LINE-FILL): v of the back quad (x in [-k, 0]) and the front quad (x in [0, k]), each from its -X to
# its +X end. The line texture is transparent on rows v < 1/2 and the body row on rows v >= 1/2. The back quad samples
# the first quarter of the rows: at every level down to 4 x 4 its bilinear footprint stays in rows that are all 0
# (a 4-row level: rows 0..1 of the transparent 0..1), and the 2 x 2 and 1 x 1 levels are all 0 anyway (both columns
# are long edges, cleared). The front quad samples the middle of the body rows, where every row is the same, so the
# drawn line has no start or end in the texture: its ends are the quad's own edges.
LINE_BACK_V = (0.0, 0.25)
LINE_FRONT_V = (0.625, 0.875)


def line_alpha(size: int, fill: int = FILL_ALPHA) -> bytes:
    """Rows v < 1/2: transparent (the back quad's region). Rows v >= 1/2: the body, the same in every row: fill
    with rims on the two long edges (columns), MARGIN_FRAC in from the texture edge."""
    margin = size * MARGIN_FRAC
    rim = LINE_RIM_FRAC * (size - 2 * margin)
    row = bytearray(size)
    for col in range(size):
        inside = min(col + 0.5 - margin, size - margin - col - 0.5)     # distance in from the nearer edge
        row[col] = _byte(_shaded(fill, -inside, rim))
    return bytes(size) * (size // 2) + bytes(row) * (size - size // 2)


# --- display table ---

class Display:
    """One CreatureDisplayInfo + CreatureModelData pair.

    shape: disc, ring, timer, donut, cone, line (fill layer: disc, donut, cone, line; outline layer: ring,
    donut_outline, cone_outline, line_outline; timer: the donut's rim-only timer ring) or diag; step: the ladder
    index (0 for disc, ring and timer); param: the donut ratio or cone angle. texture: the texture file stem (shared
    by every color); tex_rgb: that texture's RGB (white for the markers); tint: the RGB the model's M2Color
    multiplies it by (the display's color). binding: how the model gets its texture: "path" (type 0, hard-coded
    `spells\\<texture>.blp`), "skin" (type 11 + fixed replaceable lookup, TextureVariation_1 = texture),
    "skin_broken" (type 11 with the source's one-entry lookup: the first M1 build, a diagnostic only) or "source"
    (the untouched source model, only its texture path rewritten: a diagnostic only)."""
    __slots__ = ("id", "shape", "step", "texture", "color", "model", "verts", "size", "binding", "param",
                 "tex_rgb", "tint", "uvs")

    def __init__(self, id_: int, shape: str, texture: str, color: str, model: str, verts, size: int,
                 binding: str = "path", param: float = 0.0, step: int = 0, tex_rgb=WHITE, tint=None, uvs=None):
        self.id, self.shape, self.step, self.texture, self.color = id_, shape, step, texture, color
        self.model, self.verts, self.size, self.binding, self.param = model, verts, size, binding, param
        self.tex_rgb = tex_rgb
        self.tint = COLOR_RGB[color] if tint is None else tint
        self.uvs = uvs          # one (u, v) per vertex; None = the source quad's


QUAD = [(-QUAD_HALF, -QUAD_HALF), (QUAD_HALF, -QUAD_HALF), (-QUAD_HALF, QUAD_HALF), (QUAD_HALF, QUAD_HALF)]


def line_verts(i: int) -> list[tuple[float, float]]:
    """The symmetric two-quad line model: the back quad x in [-k, 0], then the front quad x in [0, k], each in the
    source vertex order (-,-), (+,-), (-,+), (+,+)."""
    k = line_aspect(i)
    h = LINE_HALF
    return [(-k, -h), (0.0, -h), (-k, h), (0.0, h),
            (0.0, -h), (k, -h), (0.0, h), (k, h)]


def line_uvs() -> list[tuple[float, float]]:
    """The UVs of line_verts: u follows +Y (0 at -Y), v follows +X inside each quad (LINE_BACK_V, LINE_FRONT_V)."""
    out = []
    for v0, v1 in (LINE_BACK_V, LINE_FRONT_V):
        out += [(0.0, v0), (0.0, v1), (1.0, v0), (1.0, v1)]
    return out


# Diagnostic displays (91990-91995, only with --diagnostics): which half of a broken marker is at fault.
# (id, model file, texture file stem, binding). Every one is a red disc; view with `.morph target <id>`. They predate
# the tint: a red texture under a white M2Color, except 91992, 91993 and 91995, which use the production white disc
# under a red M2Color (91993 is byte for byte the red production disc 91000).
DIAG_ASC_TEXTURE = f"{PREFIX}diag_asc_red"      # SOURCE_TEXTURE, copied verbatim
DIAG_PAL_TEXTURE = f"{PREFIX}diag_pal_red"      # the disc in the first build's palette format
DIAGNOSTICS = (
    (91990, f"{PREFIX}diag_src", DIAG_ASC_TEXTURE, "source"),       # untouched model + Ascension texture
    (91991, f"{PREFIX}diag_pal", DIAG_PAL_TEXTURE, "path"),         # our model + palette BLP
    (91992, f"{PREFIX}diag_skin", f"{PREFIX}disc", "skin"),         # type 11, fixed lookup + DXT5
    (91993, f"{PREFIX}diag_dxt", f"{PREFIX}disc", "path"),          # type 0 + DXT5 (= 91000)
    (91994, f"{PREFIX}diag_ascpatch", DIAG_ASC_TEXTURE, "path"),    # our model + Ascension texture
    (91995, f"{PREFIX}diag_oldskin", f"{PREFIX}disc", "skin_broken"),  # the first build's binding
)


def build_diagnostics() -> list[Display]:
    out = []
    for id_, model, texture, binding in DIAGNOSTICS:
        tinted = texture == f"{PREFIX}disc"
        out.append(Display(id_, "diag", texture, "red", model, QUAD, BIG, binding,
                           tex_rgb=WHITE if tinted else COLOR_RGB["red"], tint=None if tinted else WHITE))
    return out


def texture_stem(shape: str, step: int) -> str:
    """The shared (white) texture of one shape step: bm_disc, bm_cone_090, bm_outline_donut_33, bm_line, ..."""
    if shape in ("disc", "ring", "timer", "dashed", "line"):
        return f"{PREFIX}{shape}"
    if shape == "line_outline":
        return f"{PREFIX}outline_line"
    outline = shape.endswith("_outline")
    base = shape.removesuffix("_outline")
    tag = f"{round(DONUT_RATIOS[step] * 100):02d}" if base == "donut" else f"{CONE_ANGLES[step]:03d}"
    return f"{PREFIX}{'outline_' if outline else ''}{base}_{tag}"


def build_displays(skins: bool) -> list[Display]:
    """Every color x every shape step, in id order."""
    out: list[Display] = []
    binding = "skin" if skins else "path"
    for c, color in enumerate(COLORS):
        for shape, steps in SHAPES:
            for step in range(steps):
                line = shape in ("line", "line_outline")
                texture = texture_stem(shape, step)
                if line:
                    verts, uvs = line_verts(step), line_uvs()
                    own = f"{texture}_{step:02d}_{color}"
                    shared = f"{PREFIX}line_{step:02d}_{color}"
                else:
                    verts, uvs = QUAD, None
                    own = f"{texture}_{color}"
                    shared = f"{PREFIX}quad_{color}"
                if shape in ("donut", "donut_outline"):
                    param = DONUT_RATIOS[step]
                elif shape in ("cone", "cone_outline"):
                    param = CONE_ANGLES[step]
                else:
                    param = step if line else 0.0
                size = BIG if shape in ("disc", "ring", "timer", "dashed") else SMALL
                out.append(Display(display_id(c, shape, step), shape, texture, color, shared if skins else own,
                                   verts, size, binding, param, step, uvs=uvs))
    return out


def alpha_for(display: Display) -> bytes:
    """The alpha plane of a display's texture (color-independent; callers cache it per texture)."""
    shape, size, param = display.shape, display.size, display.param
    if shape in ("disc", "diag"):
        return disc_alpha(size, FILL_ALPHA)
    if shape == "ring":
        return disc_alpha(size, OUTLINE_FILL_ALPHA)
    if shape == "timer":
        return disc_alpha(size, 0, TIMER_RIM_FRAC)
    if shape == "dashed":
        return dashed_alpha(size)
    if shape in ("donut", "donut_outline"):
        return donut_alpha(size, param, FILL_ALPHA if shape == "donut" else OUTLINE_FILL_ALPHA)
    if shape in ("cone", "cone_outline"):
        return cone_alpha(size, param, FILL_ALPHA if shape == "cone" else OUTLINE_FILL_ALPHA)
    if shape in ("line", "line_outline"):
        return line_alpha(size, FILL_ALPHA if shape == "line" else OUTLINE_FILL_ALPHA)
    raise ValueError(shape)


def edge_clearing(display: Display) -> dict:
    """encode_blp's edge flags: every shape keeps all four edges clear except a line, whose body rows must stay
    the same down to the last one (the front quad samples them up to LINE_FRONT_V[1]; its first rows are
    transparent anyway), so only its long edges (columns) are cleared. That also clears the whole 2 x 2 and
    1 x 1 levels of a line texture."""
    if display.shape in ("line", "line_outline"):
        return {"clear_cols": True, "clear_rows": False}
    return {"clear_cols": True, "clear_rows": True}


def build_textures(displays: list[Display], fmt: str = "dxt5", source_texture: bytes | None = None) -> dict[str, bytes]:
    """{texture file name: BLP bytes}, one per distinct texture (fmt: "dxt5" or "palette").

    The diagnostic textures ignore `fmt`: bm_diag_pal_* is always the palette format and
    bm_diag_asc_red is `source_texture` (the Ascension file) verbatim."""
    textures: dict[str, bytes] = {}
    for d in displays:
        name = f"{d.texture}.blp"
        if name in textures:
            continue
        if d.texture == DIAG_ASC_TEXTURE:
            if source_texture is None:
                raise SystemExit(f"diagnostic {d.id} needs {SOURCE_TEXTURE}; run --extract into a fresh --src "
                                 "or leave out --diagnostics")
            textures[name] = source_texture
            continue
        plane = alpha_for(d)
        if d.texture == DIAG_PAL_TEXTURE or fmt == "palette":
            textures[name] = encode_blp_palette(d.size, d.size, d.tex_rgb, plane)
        else:
            textures[name] = encode_blp(d.size, d.size, d.tex_rgb, plane, **edge_clearing(d))
    return textures


def tint_floats(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """An 8-bit RGB as the M2Color track's float RGB (0..1)."""
    return tuple(v / 255.0 for v in rgb)


def build_models(displays: list[Display], src_model: bytes, src_skin: bytes) -> dict[str, bytes]:
    """{file name: bytes} for every model and skin file the displays use (per each display's binding)."""
    files: dict[str, bytes] = {}
    for d in displays:
        if f"{d.model}.m2" in files:
            continue
        path = f"spells\\{d.texture}.blp"
        if d.binding == "source":
            files[f"{d.model}.m2"] = set_texture_path(src_model, path)
            files[f"{d.model}00.skin"] = src_skin
            continue
        rgb = tint_floats(d.tint)
        if d.binding == "path":
            model = patch_model(src_model, d.verts, skins=False, texture_path=path, rgb=rgb, uvs=d.uvs)
        elif d.binding in ("skin", "skin_broken"):
            model = patch_model(src_model, d.verts, skins=True, skin_lookup=d.binding == "skin", rgb=rgb, uvs=d.uvs)
        else:
            raise ValueError(d.binding)
        files[f"{d.model}.m2"] = model
        files[f"{d.model}00.skin"] = patch_skin(src_skin, d.verts)
    return files


def model_row(d: Display) -> dict:
    return _row(
        dbcfmt.CREATUREMODELDATA, d.id,
        Flags=0, ModelName=model_path(d.model), ModelScale=1.0,
        SizeClass=1, BloodID=1, FootprintParticleScale=1.0,
        WorldEffectScale=1.0, AttachedEffectScale=1.0,
    )


def display_row(d: Display) -> dict:
    return _row(
        dbcfmt.CREATUREDISPLAYINFO, d.id,
        ModelID=d.id, CreatureModelScale=1.0, CreatureModelAlpha=255,
        TextureVariation_1=d.texture, BloodLevel=1,
    )


# The slice the markers used before the colors fix (90500-90699) is free again for other owners, so its cleanup
# only ever touches rows that are ours by name: a CreatureModelData row whose model is SPELLS\\bm_*, a
# CreatureDisplayInfo row whose texture is bm_*. The block 91000-93999 is cleared outright.


def _is_marker_row(table, row: dict) -> bool:
    if table is dbcfmt.CREATUREMODELDATA:
        return str(row.get("ModelName", "")).lower().startswith(f"spells\\{PREFIX}")
    return str(row.get("TextureVariation_1", "")).lower().startswith(PREFIX)


def _owned(table, row: dict) -> bool:
    if FIRST_ID <= row["ID"] <= BLOCK_LAST_ID:
        return True
    return OLD_FIRST_ID <= row["ID"] <= OLD_LAST_ID and _is_marker_row(table, row)


def build_pending_sql(displays: list[Display]) -> str:
    """DELETE our rows of the old slice and the whole reserved block (stale rows of every earlier layout included)
    and INSERT `displays`."""
    blocks = []
    guards = {dbcfmt.CREATUREMODELDATA: "`ModelName` LIKE 'SPELLS_bm\\_%'",
              dbcfmt.CREATUREDISPLAYINFO: "`TextureVariation_1` LIKE 'bm\\_%'"}
    for table, rows in ((dbcfmt.CREATUREMODELDATA, [model_row(d) for d in displays]),
                        (dbcfmt.CREATUREDISPLAYINFO, [display_row(d) for d in displays])):
        old = (f"DELETE FROM `{table.sql_table}` WHERE `{table.index_column}` "
               f"BETWEEN {OLD_FIRST_ID} AND {OLD_LAST_ID} AND {guards[table]};")
        blocks.append(old + "\n" + _table_block(table, {"start": FIRST_ID, "end": BLOCK_LAST_ID}, rows, []))
    return "\n\n".join(blocks) + "\n"


def merge_block(path: Path, table, rows: list[dict]) -> tuple[int, int]:
    """Write `rows` into a DBC and drop every other row we own (an earlier layout's ids; see _owned).
    Returns (rows added or changed, rows removed)."""
    keep = {r["ID"] for r in rows}
    existing = dbcfile.read_dbc(path, table)
    stale = [r for r in existing if _owned(table, r) and r["ID"] not in keep]
    if stale:
        dbcfile.write_dbc(path, table, [r for r in existing if r not in stale])
    return _merge(path, table, rows), len(stale)


# --- IO ---

def extract_source(mpq: Path, dest: Path) -> None:
    """smpq -x the two source files into `dest`, which must be new or empty (untrusted data)."""
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise SystemExit(f"--src {dest} must be a new or empty directory")
    dest.mkdir(parents=True, exist_ok=True)
    cmd = ["smpq", "-x", str(mpq), *SOURCE_ARCHIVE_PATHS]
    result = subprocess.run(cmd, cwd=dest, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"smpq failed ({result.returncode}): {result.stderr.strip()}")
    for rel in SOURCE_ARCHIVE_PATHS:
        if not (dest / rel).is_file():
            raise SystemExit(f"smpq did not produce {dest / rel}")
    print(f"extracted {len(SOURCE_ARCHIVE_PATHS)} file(s) into {dest}")


def read_source(src: Path) -> tuple[bytes, bytes, bytes | None]:
    """(model, skin, texture or None): the texture is only needed by the diagnostic displays."""
    model, skin, texture = (src / "SPELLS" / n for n in (SOURCE_MODEL, SOURCE_SKIN, SOURCE_TEXTURE))
    for p in (model, skin):
        if not p.is_file():
            raise SystemExit(f"{p} not found; run with --extract <patch-N.MPQ> first")
    return model.read_bytes(), skin.read_bytes(), texture.read_bytes() if texture.is_file() else None


def write_assets(spells_dir: Path, files: dict[str, bytes]) -> tuple[int, int]:
    """Write `files`, and drop stale bm_ files of an earlier run (for example the other skin mode)."""
    spells_dir.mkdir(parents=True, exist_ok=True)
    removed = 0
    for p in spells_dir.iterdir():
        if p.is_file() and p.name.lower().startswith(PREFIX) and p.name not in files:
            p.unlink()
            removed += 1
    written = 0
    for name, data in files.items():
        p = spells_dir / name
        if not p.exists() or p.read_bytes() != data:
            p.write_bytes(data)
            written += 1
    return written, removed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--var", type=Path, default=DEFAULT_VAR,
                        help="working-data root (default: the tool's own var/); DBCs and SPELLS/ live under "
                             "<var>/model-visual-dbc/")
    parser.add_argument("--src", type=Path, default=None,
                        help="directory holding the extracted source files (default: <var>/bossmech-src)")
    parser.add_argument("--extract", type=Path, default=None, metavar="MPQ",
                        help="first smpq -x the source model and skin out of this Ascension patch-N.MPQ "
                             "into --src, which must be new or empty")
    parser.add_argument("--sql-out", type=Path, default=None, help="write the server-side SQL migration here")
    parser.add_argument("--dry-run", action="store_true", help="build everything in memory, write nothing")
    parser.add_argument("--skins", action="store_true",
                        help="one shared model per shape with a type-11 skin texture (TextureVariation_1) instead "
                             "of the default one model copy per display with a hard-coded texture path")
    parser.add_argument("--no-skins", action="store_true", help=argparse.SUPPRESS)  # the old flag; now the default
    parser.add_argument("--texture-format", choices=("dxt5", "palette"), default="dxt5",
                        help="BLP2 encoding of the marker textures (default dxt5; palette = the first M1 build)")
    parser.add_argument("--diagnostics", action="store_true",
                        help="also build the diagnostic displays 91990-91995 (red discs in the bindings and texture "
                             "formats the first fixes tested)")
    parser.add_argument("--no-diagnostics", action="store_true", help=argparse.SUPPRESS)  # the old default
    args = parser.parse_args()

    skins = args.skins
    src = args.src or (args.var / "bossmech-src")
    if args.extract:
        extract_source(args.extract, src)
    src_model, src_skin, src_texture = read_source(src)

    displays = build_displays(skins)
    if args.diagnostics:
        displays += build_diagnostics()
    models = build_models(displays, src_model, src_skin)
    textures = build_textures(displays, args.texture_format, src_texture)
    files = {**models, **textures}
    sql = build_pending_sql(displays)

    n_models = sum(1 for n in files if n.endswith(".m2"))
    print(f"{len(displays)} displays (ids {FIRST_ID}-{QUAD_LAST_ID}, {LINE_FIRST_ID['line']}-..., "
          f"{LINE_FIRST_ID['line_outline']}-{max(d.id for d in displays)}), {n_models} model(s) + skin(s), "
          f"{len(textures)} {args.texture_format} texture(s), "
          f"skins={'yes (type 11)' if skins else 'no (hard-coded paths)'}")
    print(f"shape radius at scale 1: 1.0 yd (scale = radius; quad half-size {QUAD_HALF:.4f}, margin "
          f"{MARGIN_FRAC:.4f} of the side); line models two quads x in [-k, 0] (transparent) + [0, k], y in "
          f"[-{LINE_HALF:.4f}, {LINE_HALF:.4f}] (width 1 yd inside the margin), k = {line_aspect(0):.4f} .. "
          f"{line_aspect(LINE_STEPS - 1):.4f}")
    if args.dry_run:
        print("dry run: nothing written")
        return

    dbc_dir = args.var / "model-visual-dbc" / "DBFilesClient"
    spells_dir = args.var / "model-visual-dbc" / "SPELLS"
    written, removed = write_assets(spells_dir, files)
    print(f"{written} asset file(s) written, {removed} stale removed -> {spells_dir}")
    changed, removed = merge_block(dbc_dir / "CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA,
                                   [model_row(d) for d in displays])
    changed_d, removed_d = merge_block(dbc_dir / "CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO,
                                       [display_row(d) for d in displays])
    print(f"{changed + changed_d} DBC row(s) added or changed, {removed + removed_d} stale row(s) of "
          f"{OLD_FIRST_ID}-{OLD_LAST_ID} / {FIRST_ID}-{BLOCK_LAST_ID} removed (0 / 0 means everything already "
          "matched)")
    if args.sql_out:
        args.sql_out.write_text(sql)
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
