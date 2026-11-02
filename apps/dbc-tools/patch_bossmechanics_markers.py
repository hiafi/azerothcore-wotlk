#!/usr/bin/env python3
"""
Boss-mechanics telegraph marker assets (dungeon mechanics stage M1, WP-A): 120 creature displays
that are flat, coloured, alpha-blended floor shapes (discs, rings, donuts, cones, lines) a stalker
creature wears and `SetObjectScale`s to any size.

Source model: Ascension's `SPELLS\\red_circle_filled.M2` (a 4-vertex quad) from its client backup.
The model is patched (lib/m2_patch.py) into a unit quad (x, y in [-1, 1], z = 0, so a scale of r is
exactly an r-yard radius) and 41 line models (x in [0, k], y in [-0.5, 0.5], k = 2^(i/8), so scale =
width and the model starts at the stalker). Textures are generated here, not mined
(lib/blp_write.py, DXT5): one flat colour per file with the shape in the alpha channel, so the
geometry is exact and nothing needs in-game calibration beyond the S1-S7 spike checks in the handoff.

Rows written: CreatureModelData + CreatureDisplayInfo ids 90500-90619 (one pair per display, the
same id in both tables), into the working copy `var/model-visual-dbc/DBFilesClient/`; model, skin
and texture files into `var/model-visual-dbc/SPELLS/` (packed by build_patch_m.py); `--sql-out`
emits the matching server rows. Deliberately not named `patch_*_vfx_models.py`, so
lib/test_id_blocks.py's constant scan of those scripts is unaffected.

Display ids (CreatureDisplayInfo id = CreatureModelData id; colour index c: red 0, yellow 1, blue
2, purple 3; get-out shapes ship red and yellow only):

    90500-90503  disc, 90500 + c               90504-90507  ring, 90504 + c
    90508-90521  donut, 90508 + 2j + c, rho_j in (0.25 0.33 0.40 0.50 0.60 0.67 0.75)
    90522-90537  cone, 90522 + 2j + c, angle_j in (30 45 60 90 120 150 180 270) degrees
    90538-90619  line, 90538 + 2i + c, k_i = 2^(i/8), i = 0..40 (aspect 1 to 32)
    90620-90629  diagnostic displays (DIAGNOSTICS below; `.morph target <id>` on yourself)
    90630-90649  spare

Orientation: model +X is forward and carries v, model +Y carries u, so a cone's wedge opens toward
increasing v (down the image rows) and its apex is the texture centre. Spike S5 checks it in game.

Texture binding (fix 2026-11-02, M1-FIX-MARKERS-REPORT.md): by default every display gets its own
model copy whose texture path is hard-coded (type 0, how the source model binds its texture). The
first build used one shared model with a type-11 skin texture, which drew green boxes: the source's
replaceable-texture lookup only maps type 0. `--skins` restores the shared-model layout with that
lookup fixed (lib/m2_patch.py); ids are the same either way.

Usage (untrusted input rule: the extracted Ascension files get their own new, empty directory):
    python3 -I apps/dbc-tools/patch_bossmechanics_markers.py --extract <patch-N.MPQ>
    python3 -I apps/dbc-tools/patch_bossmechanics_markers.py --dry-run
    python3 -I apps/dbc-tools/patch_bossmechanics_markers.py --sql-out data/sql/updates/pending_db_world/rev_<ns>.sql
`--extract` also takes the source's own texture (for the diagnostic displays 90620 and 90624).
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

from lib import dbcfmt  # noqa: E402
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
LAST_ID = 90619
DIAG_FIRST_ID = 90620
DIAG_LAST_ID = 90629         # the SQL deletes the whole diagnostic block, used or not

COLOURS = ("red", "yellow", "blue", "purple")
COLOUR_RGB = {"red": (230, 40, 30), "yellow": (245, 200, 40), "blue": (40, 120, 240), "purple": (160, 70, 220)}
GET_OUT_COLOURS = COLOURS[:2]

DISC_BASE = 90500
RING_BASE = 90504
DONUT_BASE = 90508
CONE_BASE = 90522
LINE_BASE = 90538

DONUT_RATIOS = (0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75)
CONE_ANGLES = (30, 45, 60, 90, 120, 150, 180, 270)
LINE_STEPS = 41                                  # i = 0..40


def line_aspect(i: int) -> float:
    """k_i = 2^(i/8): the line model is k_i long and 1 wide (scale = width)."""
    return 2.0 ** (i / 8.0)


# --- texture look (handoff §3.9) ---

FILL_ALPHA = 90
RING_FILL_ALPHA = 25
RIM_ALPHA = 230
RIM_FRAC = 0.025            # rim width as a fraction of the outer radius
LINE_RIM_FRAC = 0.03        # line rim width as a fraction of the line width
BIG = 512                   # disc and ring
SMALL = 256                 # everything else


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


def disc_alpha(size: int, fill: int) -> bytes:
    radius = size / 2.0
    rim = RIM_FRAC * radius
    return _plane(size, lambda x, y: _shaded(fill, math.hypot(x, y) - radius, rim))


def donut_alpha(size: int, ratio: float) -> bytes:
    radius = size / 2.0
    rim = RIM_FRAC * radius

    def alpha(x: float, y: float) -> float:
        d = math.hypot(x, y)
        return _shaded(FILL_ALPHA, max(d - radius, ratio * radius - d), rim)

    return _plane(size, alpha)


def cone_alpha(size: int, angle_deg: float) -> bytes:
    """Apex at the texture centre, wedge opening toward +x (increasing row = increasing v)."""
    radius = size / 2.0
    rim = RIM_FRAC * radius
    half = math.radians(angle_deg / 2.0)
    s, c = math.sin(half), math.cos(half)
    concave = angle_deg > 180.0

    def alpha(x: float, y: float) -> float:
        d1 = -x * s + y * c          # outward normal of the +half side
        d2 = -x * s - y * c          # outward normal of the -half side
        sd_ang = min(d1, d2) if concave else max(d1, d2)
        return _shaded(FILL_ALPHA, max(math.hypot(x, y) - radius, sd_ang), rim)

    return _plane(size, alpha)


def line_alpha(size: int) -> bytes:
    """Fill with rims on the two long edges (columns); the ends are open."""
    rim = LINE_RIM_FRAC * size
    out = bytearray(size * size)
    row = bytearray(size)
    for col in range(size):
        edge = min(col + 0.5, size - col - 0.5)
        inner = _cov(rim - edge)         # 1 once past the rim
        row[col] = _byte(RIM_ALPHA * (1.0 - inner) + FILL_ALPHA * inner)
    for r in range(size):
        out[r * size:(r + 1) * size] = row
    return bytes(out)


# --- display table ---

class Display:
    """One CreatureDisplayInfo + CreatureModelData pair.

    binding: how the model gets its texture: "path" (type 0, hard-coded `spells\\<texture>.blp`),
    "skin" (type 11 + fixed replaceable lookup, TextureVariation_1 = texture), "skin_broken"
    (type 11 with the source's one-entry lookup: the first M1 build, diagnostic 90625 only) or
    "source" (the untouched source model, only its texture path rewritten: diagnostic 90620)."""
    __slots__ = ("id", "shape", "texture", "colour", "model", "verts", "size", "binding")

    def __init__(self, id_: int, shape: str, texture: str, colour: str, model: str, verts, size: int,
                 binding: str = "path"):
        self.id, self.shape, self.texture, self.colour = id_, shape, texture, colour
        self.model, self.verts, self.size, self.binding = model, verts, size, binding


QUAD = [(-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)]


def line_verts(i: int) -> list[tuple[float, float]]:
    k = line_aspect(i)
    return [(0.0, -0.5), (k, -0.5), (0.0, 0.5), (k, 0.5)]


# Diagnostic displays (90620-90629): one login tells which half of a still-broken marker is at fault.
# (id, model file, texture file stem, binding). Every one is a red disc; view with `.morph target <id>`.
DIAG_ASC_TEXTURE = f"{PREFIX}diag_asc_red"      # SOURCE_TEXTURE, copied verbatim
DIAG_PAL_TEXTURE = f"{PREFIX}diag_pal_red"      # the disc in the first build's palette format
DIAGNOSTICS = (
    (90620, f"{PREFIX}diag_src", DIAG_ASC_TEXTURE, "source"),       # untouched model + Ascension texture
    (90621, f"{PREFIX}diag_pal", DIAG_PAL_TEXTURE, "path"),         # our model + palette BLP
    (90622, f"{PREFIX}diag_skin", f"{PREFIX}disc_red", "skin"),     # type 11, fixed lookup + DXT5
    (90623, f"{PREFIX}diag_dxt", f"{PREFIX}disc_red", "path"),      # type 0 + DXT5 (= the new 90500)
    (90624, f"{PREFIX}diag_ascpatch", DIAG_ASC_TEXTURE, "path"),    # our model + Ascension texture
    (90625, f"{PREFIX}diag_oldskin", f"{PREFIX}disc_red", "skin_broken"),  # the first build's binding
)


def build_diagnostics() -> list[Display]:
    return [Display(id_, "diag", texture, "red", model, QUAD, BIG, binding)
            for id_, model, texture, binding in DIAGNOSTICS]


def build_displays(skins: bool) -> list[Display]:
    out: list[Display] = []
    binding = "skin" if skins else "path"

    def add(id_: int, shape: str, tex_stem: str, colour: str, size: int, model: str, verts) -> None:
        texture = f"{PREFIX}{tex_stem}_{colour}"
        out.append(Display(id_, shape, texture, colour, model if skins else texture, verts, size, binding))

    for c, colour in enumerate(COLOURS):
        add(DISC_BASE + c, "disc", "disc", colour, BIG, f"{PREFIX}quad", QUAD)
        add(RING_BASE + c, "ring", "ring", colour, BIG, f"{PREFIX}quad", QUAD)
    for j, ratio in enumerate(DONUT_RATIOS):
        for c, colour in enumerate(GET_OUT_COLOURS):
            add(DONUT_BASE + 2 * j + c, "donut", f"donut_{round(ratio * 100):02d}", colour, SMALL,
                f"{PREFIX}quad", QUAD)
    for j, angle in enumerate(CONE_ANGLES):
        for c, colour in enumerate(GET_OUT_COLOURS):
            add(CONE_BASE + 2 * j + c, "cone", f"cone_{angle:03d}", colour, SMALL, f"{PREFIX}quad", QUAD)
    for i in range(LINE_STEPS):
        for c, colour in enumerate(GET_OUT_COLOURS):
            texture = f"{PREFIX}line_{colour}"
            model = f"{PREFIX}line_{i:02d}"
            out.append(Display(LINE_BASE + 2 * i + c, "line", texture, colour,
                               model if skins else f"{model}_{colour}", line_verts(i), SMALL, binding))
    return out


def alpha_for(display: Display) -> bytes:
    """The alpha plane of a display's texture (colour-independent; callers cache it per stem)."""
    stem = display.texture.removeprefix(PREFIX).rsplit("_", 1)[0]
    if stem == "disc":
        return disc_alpha(display.size, FILL_ALPHA)
    if stem == "ring":
        return disc_alpha(display.size, RING_FILL_ALPHA)
    if stem.startswith("donut_"):
        return donut_alpha(display.size, int(stem.split("_")[1]) / 100.0)
    if stem.startswith("cone_"):
        return cone_alpha(display.size, int(stem.split("_")[1]))
    if stem == "line":
        return line_alpha(display.size)
    raise ValueError(stem)


def build_textures(displays: list[Display], fmt: str = "dxt5", source_texture: bytes | None = None) -> dict[str, bytes]:
    """{texture file name: BLP bytes}, one per distinct texture (fmt: "dxt5" or "palette").

    The diagnostic textures ignore `fmt`: bm_diag_pal_* is always the palette format and
    bm_diag_asc_red is `source_texture` (the Ascension file) verbatim."""
    encoders = {"dxt5": encode_blp, "palette": encode_blp_palette}
    textures: dict[str, bytes] = {}
    planes: dict[str, bytes] = {}
    for d in displays:
        if f"{d.texture}.blp" in textures:
            continue
        if d.texture == DIAG_ASC_TEXTURE:
            if source_texture is None:
                raise SystemExit(f"diagnostic {d.id} needs {SOURCE_TEXTURE}; run --extract into a fresh --src "
                                 "or pass --no-diagnostics")
            textures[f"{d.texture}.blp"] = source_texture
            continue
        encoder = encode_blp_palette if d.texture == DIAG_PAL_TEXTURE else encoders[fmt]
        stem = "disc" if d.shape == "diag" else d.texture.removeprefix(PREFIX).rsplit("_", 1)[0]
        if stem not in planes:
            planes[stem] = disc_alpha(d.size, FILL_ALPHA) if stem == "disc" else alpha_for(d)
        textures[f"{d.texture}.blp"] = encoder(d.size, d.size, COLOUR_RGB[d.colour], planes[stem])
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
    rng = {"start": FIRST_ID, "end": DIAG_LAST_ID if any(d.id > LAST_ID for d in displays) else LAST_ID}
    blocks = [
        _table_block(dbcfmt.CREATUREMODELDATA, rng, [model_row(d) for d in displays], []),
        _table_block(dbcfmt.CREATUREDISPLAYINFO, rng, [display_row(d) for d in displays], []),
    ]
    return "\n\n".join(blocks) + "\n"


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
    parser.add_argument("--no-diagnostics", action="store_true",
                        help="leave out the diagnostic displays 90620-90625")
    args = parser.parse_args()

    skins = args.skins
    src = args.src or (args.var / "bossmech-src")
    if args.extract:
        extract_source(args.extract, src)
    src_model, src_skin, src_texture = read_source(src)

    displays = build_displays(skins)
    if not args.no_diagnostics:
        displays += build_diagnostics()
    models = build_models(displays, src_model, src_skin)
    textures = build_textures(displays, args.texture_format, src_texture)
    files = {**models, **textures}
    sql = build_pending_sql(displays)

    n_models = sum(1 for n in files if n.endswith(".m2"))
    print(f"{len(displays)} displays (ids {FIRST_ID}-{max(d.id for d in displays)}), {n_models} model(s) + skin(s), "
          f"{len(textures)} {args.texture_format} texture(s), "
          f"skins={'yes (type 11)' if skins else 'no (hard-coded paths)'}")
    print("model radius at scale 1: quad half-size 1.0 yd (scale = radius); line models "
          f"x in [0, k], y in [-0.5, 0.5], k = {line_aspect(0):.4f} .. {line_aspect(LINE_STEPS - 1):.4f}")
    if args.dry_run:
        print("dry run: nothing written")
        return

    dbc_dir = args.var / "model-visual-dbc" / "DBFilesClient"
    spells_dir = args.var / "model-visual-dbc" / "SPELLS"
    written, removed = write_assets(spells_dir, files)
    print(f"{written} asset file(s) written, {removed} stale removed -> {spells_dir}")
    changed = _merge(dbc_dir / "CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA, [model_row(d) for d in displays])
    changed += _merge(dbc_dir / "CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO,
                      [display_row(d) for d in displays])
    print(f"{changed} DBC row(s) added or changed (0 means everything already existed)")
    if args.sql_out:
        args.sql_out.write_text(sql)
        print(f"wrote server-side SQL -> {args.sql_out}")


if __name__ == "__main__":
    main()
