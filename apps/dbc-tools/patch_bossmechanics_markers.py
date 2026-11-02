#!/usr/bin/env python3
"""
Boss-mechanics telegraph marker assets (dungeon mechanics stage M1, WP-A): 170 creature displays
that are flat, coloured, alpha-blended floor shapes a stalker creature wears and `SetObjectScale`s
to any size. Every telegraph draws two layers (M1-FIX-TELEGRAPH-FILL-REPORT.md): a static OUTLINE
(rim + faint interior, the full hitbox from the first frame) and a FILL (rim + solid interior) that
the server grows into the outline over the warning time.

Source model: Ascension's `SPELLS\\red_circle_filled.M2` (a 4-vertex quad) from its client backup.
The model is patched (lib/m2_patch.py) into a quad (x, y in [-QUAD_HALF, QUAD_HALF], z = 0) and 25
line models (x in [0, k], y in [-LINE_HALF, LINE_HALF], k = 2^(i/8), so scale = width and the model
starts at the stalker). Textures are generated here, not mined (lib/blp_write.py, DXT5): one flat
colour per file with the shape in the alpha channel. The shape stops MARGIN_FRAC of the side short
of every texture edge it would otherwise touch, and the quad is that much bigger (QUAD_HALF = 8/7),
so scale 1 is still exactly a 1-yard radius / length / width; the edge texels are transparent at
every mip level (`encode_blp(clear_cols=..., clear_rows=...)`). The first build drew the shapes
edge to edge, and the clamped edge texels of the lower mips drew straight lines along the quad edge
where the disc touches it (N/E/S/W).

Rows written: CreatureModelData + CreatureDisplayInfo ids 90500-90669 (one pair per display, the
same id in both tables), into the working copy `var/model-visual-dbc/DBFilesClient/`, with any other
row of the reserved block 90500-90699 removed; model, skin and texture files into
`var/model-visual-dbc/SPELLS/` (packed by build_patch_m.py); `--sql-out` emits the matching server
rows (DELETE + INSERT of the whole block). Deliberately not named `patch_*_vfx_models.py`, so
lib/test_id_blocks.py's constant scan of those scripts is unaffected.

Display ids (CreatureDisplayInfo id = CreatureModelData id; colour index c: red 0, yellow 1, blue
2, purple 3; get-out shapes ship red and yellow only). F = fill layer, O = outline layer:

    90500-90503  disc (F), 90500 + c            90504-90507  ring (O), 90504 + c
    90508-90521  donut (F), 90508 + 2j + c, rho_j in (0.25 0.33 0.40 0.50 0.60 0.67 0.75)
    90522-90537  cone (F), 90522 + 2j + c, angle_j in (30 45 60 90 120 150 180 270) degrees
    90538-90587  line (F), 90538 + 2i + c, k_i = 2^(i/8), i = 0..24 (aspect 1 to 8)
    90588-90637  line (O), 90588 + 2i + c
    90638-90653  cone (O), 90638 + 2j + c
    90654-90667  donut (O), 90654 + 2j + c
    90668-90669  timer ring (rim only; a donut's timer), 90668 + c
    90670-90689  spare
    90690-90695  diagnostic displays, only with --diagnostics (DIAGNOSTICS below)
    90696-90699  spare

Orientation: model +X is forward and carries v, model +Y carries u, so a cone's wedge opens toward
increasing v (down the image rows) and its apex is the texture centre. Spike S5 checks it in game.

Texture binding (fix 2026-11-02, M1-FIX-MARKERS-REPORT.md): by default every display gets its own
model copy whose texture path is hard-coded (type 0, how the source model binds its texture; texture
flags 0 = clamp in both directions). The first build used one shared model with a type-11 skin
texture, which drew green boxes: the source's replaceable-texture lookup only maps type 0. `--skins`
restores the shared-model layout with that lookup fixed (lib/m2_patch.py); ids are the same either way.

Usage (untrusted input rule: the extracted Ascension files get their own new, empty directory):
    python3 -I apps/dbc-tools/patch_bossmechanics_markers.py --extract <patch-N.MPQ>
    python3 -I apps/dbc-tools/patch_bossmechanics_markers.py --dry-run
    python3 -I apps/dbc-tools/patch_bossmechanics_markers.py --sql-out data/sql/updates/pending_db_world/rev_<ns>.sql
`--extract` also takes the source's own texture (for the diagnostic displays 90690 and 90694).
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

# --- ids (handoff §3.1; reservations.bossmechanics in source/ids.yaml) ---

FIRST_ID = 90500
LAST_ID = 90669
BLOCK_LAST_ID = 90699        # the reservation's end: the SQL and the DBC merge clear the whole block
DIAG_FIRST_ID = 90690
DIAG_LAST_ID = 90695

COLOURS = ("red", "yellow", "blue", "purple")
COLOUR_RGB = {"red": (230, 40, 30), "yellow": (245, 200, 40), "blue": (40, 120, 240), "purple": (160, 70, 220)}
GET_OUT_COLOURS = COLOURS[:2]

DISC_BASE = 90500            # fill
RING_BASE = 90504            # outline
DONUT_BASE = 90508           # fill
CONE_BASE = 90522            # fill
LINE_BASE = 90538            # fill
LINE_OUTLINE_BASE = 90588
CONE_OUTLINE_BASE = 90638
DONUT_OUTLINE_BASE = 90654
TIMER_RING_BASE = 90668

DONUT_RATIOS = (0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75)
CONE_ANGLES = (30, 45, 60, 90, 120, 150, 180, 270)
LINE_STEPS = 25                                  # i = 0..24, aspect 1 to 8


def line_aspect(i: int) -> float:
    """k_i = 2^(i/8): the line model is k_i long and 1 wide (scale = width)."""
    return 2.0 ** (i / 8.0)


# --- texture look (handoff §3.9; two layers since the telegraph-fill fix) ---

FILL_ALPHA = 90             # fill layer interior (0.35)
OUTLINE_FILL_ALPHA = 50     # outline layer interior (0.2)
RIM_ALPHA = 230             # both layers' rim (0.9)
RIM_FRAC = 0.025            # rim width as a fraction of the outer radius
LINE_RIM_FRAC = 0.03        # line rim width as a fraction of the line width
TIMER_RIM_FRAC = 0.04       # the donut timer ring's band, as a fraction of its radius
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


def line_alpha(size: int, fill: int = FILL_ALPHA) -> bytes:
    """Fill with rims on the two long edges (columns), MARGIN_FRAC in from the texture edge; the ends
    (rows) are open and run edge to edge, so abutting pieces join without a seam."""
    margin = size * MARGIN_FRAC
    rim = LINE_RIM_FRAC * (size - 2 * margin)
    row = bytearray(size)
    for col in range(size):
        inside = min(col + 0.5 - margin, size - margin - col - 0.5)     # distance in from the nearer edge
        row[col] = _byte(_shaded(fill, -inside, rim))
    return bytes(row) * size


# --- display table ---

class Display:
    """One CreatureDisplayInfo + CreatureModelData pair.

    shape: disc, ring, timer, donut, cone, line (fill layer: disc, donut, cone, line; outline layer: ring,
    donut_outline, cone_outline, line_outline; timer: the donut's rim-only timer ring) or diag; param: the
    donut ratio or cone angle. binding: how the model gets its texture: "path" (type 0, hard-coded
    `spells\\<texture>.blp`), "skin" (type 11 + fixed replaceable lookup, TextureVariation_1 = texture),
    "skin_broken" (type 11 with the source's one-entry lookup: the first M1 build, a diagnostic only) or
    "source" (the untouched source model, only its texture path rewritten: a diagnostic only)."""
    __slots__ = ("id", "shape", "texture", "colour", "model", "verts", "size", "binding", "param")

    def __init__(self, id_: int, shape: str, texture: str, colour: str, model: str, verts, size: int,
                 binding: str = "path", param: float = 0.0):
        self.id, self.shape, self.texture, self.colour = id_, shape, texture, colour
        self.model, self.verts, self.size, self.binding, self.param = model, verts, size, binding, param


QUAD = [(-QUAD_HALF, -QUAD_HALF), (QUAD_HALF, -QUAD_HALF), (-QUAD_HALF, QUAD_HALF), (QUAD_HALF, QUAD_HALF)]


def line_verts(i: int) -> list[tuple[float, float]]:
    k = line_aspect(i)
    return [(0.0, -LINE_HALF), (k, -LINE_HALF), (0.0, LINE_HALF), (k, LINE_HALF)]


# Diagnostic displays (90690-90695, only with --diagnostics): which half of a broken marker is at fault.
# (id, model file, texture file stem, binding). Every one is a red disc; view with `.morph target <id>`.
DIAG_ASC_TEXTURE = f"{PREFIX}diag_asc_red"      # SOURCE_TEXTURE, copied verbatim
DIAG_PAL_TEXTURE = f"{PREFIX}diag_pal_red"      # the disc in the first build's palette format
DIAGNOSTICS = (
    (90690, f"{PREFIX}diag_src", DIAG_ASC_TEXTURE, "source"),       # untouched model + Ascension texture
    (90691, f"{PREFIX}diag_pal", DIAG_PAL_TEXTURE, "path"),         # our model + palette BLP
    (90692, f"{PREFIX}diag_skin", f"{PREFIX}disc_red", "skin"),     # type 11, fixed lookup + DXT5
    (90693, f"{PREFIX}diag_dxt", f"{PREFIX}disc_red", "path"),      # type 0 + DXT5 (= 90500)
    (90694, f"{PREFIX}diag_ascpatch", DIAG_ASC_TEXTURE, "path"),    # our model + Ascension texture
    (90695, f"{PREFIX}diag_oldskin", f"{PREFIX}disc_red", "skin_broken"),  # the first build's binding
)


def build_diagnostics() -> list[Display]:
    return [Display(id_, "diag", texture, "red", model, QUAD, BIG, binding)
            for id_, model, texture, binding in DIAGNOSTICS]


def build_displays(skins: bool) -> list[Display]:
    out: list[Display] = []
    binding = "skin" if skins else "path"

    def add(id_: int, shape: str, tex_stem: str, colour: str, size: int, shared_model: str, verts,
            param: float = 0.0, model: str | None = None) -> None:
        texture = f"{PREFIX}{tex_stem}_{colour}"
        own = model or texture
        out.append(Display(id_, shape, texture, colour, shared_model if skins else own, verts, size, binding, param))

    quad = f"{PREFIX}quad"
    for c, colour in enumerate(COLOURS):
        add(DISC_BASE + c, "disc", "disc", colour, BIG, quad, QUAD)
        add(RING_BASE + c, "ring", "ring", colour, BIG, quad, QUAD)
    for j, ratio in enumerate(DONUT_RATIOS):
        for c, colour in enumerate(GET_OUT_COLOURS):
            add(DONUT_BASE + 2 * j + c, "donut", f"donut_{round(ratio * 100):02d}", colour, SMALL, quad, QUAD, ratio)
    for j, angle in enumerate(CONE_ANGLES):
        for c, colour in enumerate(GET_OUT_COLOURS):
            add(CONE_BASE + 2 * j + c, "cone", f"cone_{angle:03d}", colour, SMALL, quad, QUAD, angle)
    for base, shape, stem in ((LINE_BASE, "line", "line"), (LINE_OUTLINE_BASE, "line_outline", "outline_line")):
        for i in range(LINE_STEPS):
            for c, colour in enumerate(GET_OUT_COLOURS):
                add(base + 2 * i + c, shape, stem, colour, SMALL, f"{PREFIX}line_{i:02d}", line_verts(i), i,
                    model=f"{PREFIX}{stem}_{i:02d}_{colour}")
    for j, angle in enumerate(CONE_ANGLES):
        for c, colour in enumerate(GET_OUT_COLOURS):
            add(CONE_OUTLINE_BASE + 2 * j + c, "cone_outline", f"outline_cone_{angle:03d}", colour, SMALL, quad,
                QUAD, angle)
    for j, ratio in enumerate(DONUT_RATIOS):
        for c, colour in enumerate(GET_OUT_COLOURS):
            add(DONUT_OUTLINE_BASE + 2 * j + c, "donut_outline", f"outline_donut_{round(ratio * 100):02d}", colour,
                SMALL, quad, QUAD, ratio)
    for c, colour in enumerate(GET_OUT_COLOURS):
        add(TIMER_RING_BASE + c, "timer", "timer", colour, BIG, quad, QUAD)
    return out


def alpha_for(display: Display) -> bytes:
    """The alpha plane of a display's texture (colour-independent; callers cache it per texture stem)."""
    shape, size, param = display.shape, display.size, display.param
    if shape in ("disc", "diag"):
        return disc_alpha(size, FILL_ALPHA)
    if shape == "ring":
        return disc_alpha(size, OUTLINE_FILL_ALPHA)
    if shape == "timer":
        return disc_alpha(size, 0, TIMER_RIM_FRAC)
    if shape in ("donut", "donut_outline"):
        return donut_alpha(size, param, FILL_ALPHA if shape == "donut" else OUTLINE_FILL_ALPHA)
    if shape in ("cone", "cone_outline"):
        return cone_alpha(size, param, FILL_ALPHA if shape == "cone" else OUTLINE_FILL_ALPHA)
    if shape in ("line", "line_outline"):
        return line_alpha(size, FILL_ALPHA if shape == "line" else OUTLINE_FILL_ALPHA)
    raise ValueError(shape)


def edge_clearing(display: Display) -> dict:
    """encode_blp's edge flags: every shape keeps all four edges clear except a line, whose ends are open on
    purpose (rows run edge to edge so pieces abut), so only its long edges (columns) are cleared."""
    if display.shape in ("line", "line_outline"):
        return {"clear_cols": True, "clear_rows": False}
    return {"clear_cols": True, "clear_rows": True}


def texture_stem(display: Display) -> str:
    return display.texture.removeprefix(PREFIX).rsplit("_", 1)[0]


def build_textures(displays: list[Display], fmt: str = "dxt5", source_texture: bytes | None = None) -> dict[str, bytes]:
    """{texture file name: BLP bytes}, one per distinct texture (fmt: "dxt5" or "palette").

    The diagnostic textures ignore `fmt`: bm_diag_pal_* is always the palette format and
    bm_diag_asc_red is `source_texture` (the Ascension file) verbatim."""
    textures: dict[str, bytes] = {}
    planes: dict[str, bytes] = {}
    for d in displays:
        if f"{d.texture}.blp" in textures:
            continue
        if d.texture == DIAG_ASC_TEXTURE:
            if source_texture is None:
                raise SystemExit(f"diagnostic {d.id} needs {SOURCE_TEXTURE}; run --extract into a fresh --src "
                                 "or leave out --diagnostics")
            textures[f"{d.texture}.blp"] = source_texture
            continue
        stem = "disc" if d.shape == "diag" else texture_stem(d)
        if stem not in planes:
            planes[stem] = alpha_for(d)
        if d.texture == DIAG_PAL_TEXTURE or fmt == "palette":
            textures[f"{d.texture}.blp"] = encode_blp_palette(d.size, d.size, COLOUR_RGB[d.colour], planes[stem])
        else:
            textures[f"{d.texture}.blp"] = encode_blp(d.size, d.size, COLOUR_RGB[d.colour], planes[stem],
                                                      **edge_clearing(d))
    return textures


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
        if d.binding == "path":
            model = patch_model(src_model, d.verts, skins=False, texture_path=path)
        elif d.binding in ("skin", "skin_broken"):
            model = patch_model(src_model, d.verts, skins=True, skin_lookup=d.binding == "skin")
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


def build_pending_sql(displays: list[Display]) -> str:
    """DELETE the whole reserved block (stale rows of an earlier layout included) and INSERT `displays`."""
    rng = {"start": FIRST_ID, "end": BLOCK_LAST_ID}
    blocks = [
        _table_block(dbcfmt.CREATUREMODELDATA, rng, [model_row(d) for d in displays], []),
        _table_block(dbcfmt.CREATUREDISPLAYINFO, rng, [display_row(d) for d in displays], []),
    ]
    return "\n\n".join(blocks) + "\n"


def merge_block(path: Path, table, rows: list[dict]) -> tuple[int, int]:
    """Write `rows` into a DBC and drop every other row of FIRST_ID..BLOCK_LAST_ID (an earlier layout's ids).
    Returns (rows added or changed, rows removed)."""
    keep = {r["ID"] for r in rows}
    existing = dbcfile.read_dbc(path, table)
    stale = [r for r in existing if FIRST_ID <= r["ID"] <= BLOCK_LAST_ID and r["ID"] not in keep]
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
                        help="also build the diagnostic displays 90690-90695 (red discs in the bindings and texture "
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
    print(f"{len(displays)} displays (ids {FIRST_ID}-{max(d.id for d in displays)}), {n_models} model(s) + skin(s), "
          f"{len(textures)} {args.texture_format} texture(s), "
          f"skins={'yes (type 11)' if skins else 'no (hard-coded paths)'}")
    print(f"shape radius at scale 1: 1.0 yd (scale = radius; quad half-size {QUAD_HALF:.4f}, margin "
          f"{MARGIN_FRAC:.4f} of the side); line models x in [0, k], y in [-{LINE_HALF:.4f}, {LINE_HALF:.4f}] "
          f"(width 1 yd inside the margin), k = {line_aspect(0):.4f} .. {line_aspect(LINE_STEPS - 1):.4f}")
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
          f"{FIRST_ID}-{BLOCK_LAST_ID} removed (0 / 0 means everything already matched)")
    if args.sql_out:
        args.sql_out.write_text(sql)
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
