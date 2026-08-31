#!/usr/bin/env python3
"""
dump_talents.py

Reads Talent.dbc, TalentTab.dbc and Spell.dbc from a WotLK 3.3.5a client
(or from a private-server DBC folder, including a modified one) and emits
talent trees as Python tuples in the form:

    (row, column, "Talent Name")

Row and column are 0-based, exactly as stored in Talent.dbc.

Usage:
    python dump_talents.py /path/to/dbc                      # all trees
    python dump_talents.py /path/to/dbc --class Druid        # one class
    python dump_talents.py /path/to/dbc --format flat        # single list
    python dump_talents.py /path/to/dbc -o talents.py        # write to file

    # Markdown doc: "### Talent Name (ranks)" + final-rank description
    python dump_talents.py /path/to/dbc --class Druid --format markdown -o talents.md

If your Spell.dbc is a non-standard build, override the name column:
    python dump_talents.py /path/to/dbc --spell-name-field 136
"""

import argparse
import os
import re
import struct
import sys

# ---------------------------------------------------------------------------
# DBC field layouts (WotLK 3.3.5a / build 12340)
# ---------------------------------------------------------------------------

TALENT_FIELDS = 23          # record_size 92
TALENT_TAB_FIELDS = 24      # record_size 96
SPELL_FIELDS = 234          # record_size 936

# Talent.dbc column indices
T_ID = 0
T_TAB_ID = 1
T_ROW = 2
T_COLUMN = 3
T_SPELL_RANK_0 = 4          # 9 ranks, fields 4..12

# TalentTab.dbc column indices
TT_ID = 0
TT_NAME_ENUS = 1            # localized block is fields 1..17 (16 locales + flags)
TT_CLASS_MASK = 20
TT_PET_MASK = 21
TT_ORDER_INDEX = 22

# Spell.dbc column index for SpellName_Lang[0] (enUS) in 3.3.5a
SPELL_NAME_ENUS_DEFAULT = 136

# Spell.dbc column index for Description_Lang[0] (enUS) in 3.3.5a
SPELL_DESC_ENUS_DEFAULT = 170

# Spell.dbc column indices needed to resolve $s/$m/$M/$h/$t/$x/$o/$d/$b/$c
# description tokens. See src/server/shared/DataStores/DBCStructure.h (SpellEntry)
# for the authoritative field-by-field layout this is derived from.
SPELL_CASTING_TIME_INDEX = 28
SPELL_PROC_CHANCE = 35
SPELL_DURATION_INDEX = 40
SPELL_RANGE_INDEX = 46
SPELL_EFFECT_DIE_SIDES = 74        # +0..2
SPELL_EFFECT_BASE_POINTS = 80      # +0..2
SPELL_EFFECT_RADIUS_INDEX = 92     # +0..2
SPELL_EFFECT_AMPLITUDE = 98        # +0..2 (ms)
SPELL_EFFECT_CHAIN_TARGET = 104    # +0..2

# Letters resolvable straight from Spell.dbc's own effect columns (no companion
# DBC needed). 'd'/'b'/'c' need SpellDuration/SpellRadius/SpellCastTimes.dbc.
# Uppercase S/T/O are the "ignore per-level scaling" variants of s/t/o; since
# we never apply per-level scaling anyway, they resolve identically here.
SELF_CONTAINED_TOKEN_LETTERS = "smMhtxoSTO"
ALL_TOKEN_LETTERS = SELF_CONTAINED_TOKEN_LETTERS + "dbc"

CLASS_MASKS = {
    1: "Warrior",
    2: "Paladin",
    4: "Hunter",
    8: "Rogue",
    16: "Priest",
    32: "DeathKnight",
    64: "Shaman",
    128: "Mage",
    256: "Warlock",
    1024: "Druid",
}


# ---------------------------------------------------------------------------
# DBC reader
# ---------------------------------------------------------------------------

class Dbc:
    """Minimal WDBC reader. Records are exposed as tuples of uint32."""

    def __init__(self, path):
        self.path = path
        with open(path, "rb") as fh:
            blob = fh.read()

        if blob[:4] != b"WDBC":
            raise ValueError(f"{path} is not a WDBC file (bad magic)")

        rec_count, field_count, rec_size, string_size = struct.unpack_from("<4I", blob, 4)
        self.record_count = rec_count
        self.field_count = field_count
        self.record_size = rec_size

        data_start = 20
        data_end = data_start + rec_count * rec_size
        self._string_block = blob[data_end:data_end + string_size]

        if rec_size != field_count * 4:
            raise ValueError(
                f"{path}: record_size {rec_size} does not match "
                f"field_count {field_count} (expected {field_count * 4})"
            )

        fmt = "<" + "I" * field_count
        unpack = struct.Struct(fmt).unpack_from
        self.records = [unpack(blob, data_start + i * rec_size) for i in range(rec_count)]

    def string(self, offset):
        """Resolve a string-block offset to a str."""
        if offset == 0 or offset >= len(self._string_block):
            return ""
        end = self._string_block.find(b"\x00", offset)
        if end == -1:
            end = len(self._string_block)
        return self._string_block[offset:end].decode("utf-8", errors="replace")


def to_signed32(value):
    """Dbc.records are unpacked as uint32; several Spell.dbc fields (base
    points, duration, cast time) are actually int32 and can be negative."""
    return value - 0x1_0000_0000 if value >= 0x8000_0000 else value


def raw_to_float(value):
    """Reinterpret a uint32's raw bits as a float32 (radius/range fields)."""
    return struct.unpack("<f", struct.pack("<I", value & 0xFFFF_FFFF))[0]


def find_dbc(folder, name):
    """Case-insensitive lookup so this works on Linux with Windows-cased files."""
    target = name.lower()
    for entry in os.listdir(folder):
        if entry.lower() == target:
            return os.path.join(folder, entry)
    raise FileNotFoundError(f"{name} not found in {folder}")


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def load_spell_field(path, field, flag_name):
    dbc = Dbc(path)
    if field >= dbc.field_count:
        raise ValueError(
            f"--{flag_name} {field} is out of range; "
            f"Spell.dbc has {dbc.field_count} fields"
        )
    return {rec[0]: dbc.string(rec[field]) for rec in dbc.records}


def load_spell_names(path, name_field):
    return load_spell_field(path, name_field, "spell-name-field")


def load_spell_descriptions(path, desc_field):
    return load_spell_field(path, desc_field, "spell-desc-field")


def clean_description(text):
    """Collapse whitespace; $-tokens (e.g. $s1, $m1) are resolved separately
    by resolve_tokens(), once talent/spell data has been loaded."""
    return re.sub(r"\s+", " ", text).strip()


def load_spell_records(path):
    """Full raw Spell.dbc records keyed by spell id, for token resolution."""
    dbc = Dbc(path)
    return {rec[0]: rec for rec in dbc.records}


def load_spell_duration(path):
    dbc = Dbc(path)
    return {rec[0]: to_signed32(rec[1]) for rec in dbc.records}


def load_spell_radius(path):
    dbc = Dbc(path)
    return {rec[0]: raw_to_float(rec[3]) for rec in dbc.records}  # RadiusMax


def load_spell_cast_times(path):
    dbc = Dbc(path)
    return {rec[0]: to_signed32(rec[1]) for rec in dbc.records}


def format_number(value):
    """Render an int/float as compactly as a tooltip would: no '.0', at
    most 2 decimals otherwise."""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def format_duration(ms):
    if ms is None:
        return None
    if ms < 0:
        return "until cancelled"
    secs = ms / 1000.0
    if secs >= 3600 and secs % 3600 == 0:
        return f"{int(secs // 3600)} hr"
    if secs >= 60 and secs % 60 == 0:
        return f"{int(secs // 60)} min"
    return f"{format_number(secs)} sec"


TOKEN_RE = re.compile(r"\$(\d*)([" + ALL_TOKEN_LETTERS + r"])(\d)?")
DIVIDE_TOKEN_RE = re.compile(r"\$/(\d+);(\d*)([" + ALL_TOKEN_LETTERS + r"])(\d)?")


def resolve_tokens(text, spell_id, spell_records, durations=None, radii=None, cast_times=None):
    """Best-effort resolution of WoW spell-description escape tokens
    ($s1, $m1, $M1, $h, $t1, $x1, $o1, $d, $b1, $c) using only static DBC
    data. Tokens that need data we don't have (missing companion DBC), or
    that reference live game state ($?a12345[...][...] conditionals), are
    left untouched rather than guessed at.
    """
    if not text or "$" not in text:
        return text

    def effect_value(sid, letter, eff_idx):
        rec = spell_records.get(sid)
        if rec is None:
            return None
        i = (eff_idx or 1) - 1

        if letter in ("s", "S", "m", "M"):
            if not 0 <= i <= 2:
                return None
            base = to_signed32(rec[SPELL_EFFECT_BASE_POINTS + i])
            dice = to_signed32(rec[SPELL_EFFECT_DIE_SIDES + i])
            minimum = base + 1
            value = (base + dice) if (letter == "M" and dice > 1) else minimum
            # "Reduces X by $s1%"-style talents store a negative BasePoints;
            # the wording already carries the sign, so display the magnitude.
            return abs(value)

        if letter == "h":
            return rec[SPELL_PROC_CHANCE]

        if letter in ("t", "T"):
            if not 0 <= i <= 2:
                return None
            return rec[SPELL_EFFECT_AMPLITUDE + i] / 1000.0

        if letter == "x":
            if not 0 <= i <= 2:
                return None
            return rec[SPELL_EFFECT_CHAIN_TARGET + i]

        if letter in ("o", "O"):
            if not 0 <= i <= 2 or durations is None:
                return None
            base = to_signed32(rec[SPELL_EFFECT_BASE_POINTS + i])
            amp = rec[SPELL_EFFECT_AMPLITUDE + i]
            dur_ms = durations.get(rec[SPELL_DURATION_INDEX])
            if not dur_ms or amp <= 0:
                return None
            ticks = max(1, round(dur_ms / amp))
            return (base + 1) * ticks

        if letter == "d":
            if durations is None:
                return None
            return format_duration(durations.get(rec[SPELL_DURATION_INDEX]))

        if letter == "b":
            if not 0 <= i <= 2 or radii is None:
                return None
            return radii.get(rec[SPELL_EFFECT_RADIUS_INDEX + i])

        if letter == "c":
            if cast_times is None:
                return None
            ms = cast_times.get(rec[SPELL_CASTING_TIME_INDEX])
            return ms / 1000.0 if ms is not None else None

        return None

    def format_value(letter, value):
        if value is None:
            return None
        if letter == "d":
            return value  # already formatted by format_duration above
        return format_number(value)

    def sub_divide(m):
        divisor, prefix_digits, letter, eff_digit = m.groups()
        sid = int(prefix_digits) if prefix_digits else spell_id
        eff_idx = int(eff_digit) if eff_digit else None
        value = effect_value(sid, letter, eff_idx)
        if value is None or letter == "d":
            return m.group(0)
        return format_number(abs(value / int(divisor)))

    def sub_plain(m):
        prefix_digits, letter, eff_digit = m.groups()
        sid = int(prefix_digits) if prefix_digits else spell_id
        eff_idx = int(eff_digit) if eff_digit else None
        formatted = format_value(letter, effect_value(sid, letter, eff_idx))
        return formatted if formatted is not None else m.group(0)

    text = text.replace("$$", "\x00")
    text = DIVIDE_TOKEN_RE.sub(sub_divide, text)
    text = TOKEN_RE.sub(sub_plain, text)
    return text.replace("\x00", "$")


def load_tabs(path):
    dbc = Dbc(path)
    tabs = {}
    for rec in dbc.records:
        class_mask = rec[TT_CLASS_MASK]
        tabs[rec[TT_ID]] = {
            "id": rec[TT_ID],
            "name": dbc.string(rec[TT_NAME_ENUS]),
            "class_mask": class_mask,
            "class_name": CLASS_MASKS.get(class_mask, "Pet" if rec[TT_PET_MASK] else "Unknown"),
            "order": rec[TT_ORDER_INDEX],
        }
    return tabs


def load_talents(path, spell_names, spell_descriptions=None):
    dbc = Dbc(path)
    out = []
    for rec in dbc.records:
        ranks = [rec[T_SPELL_RANK_0 + i] for i in range(9)]
        filled_ranks = [s for s in ranks if s]
        # Final rank is the highest-index non-zero entry, not necessarily
        # the first (which is only "final" when the talent has one rank).
        final_spell_id = filled_ranks[-1] if filled_ranks else 0
        name_lookup_id = next((s for s in ranks if s), 0)
        name = spell_names.get(name_lookup_id, "")
        description = ""
        if spell_descriptions is not None:
            description = clean_description(spell_descriptions.get(final_spell_id, ""))
        out.append({
            "id": rec[T_ID],
            "tab": rec[T_TAB_ID],
            "row": rec[T_ROW],
            "col": rec[T_COLUMN],
            "ranks": filled_ranks,
            "max_rank": sum(1 for s in ranks if s),
            "spell_id": name_lookup_id,
            "final_spell_id": final_spell_id,
            "name": name if name else f"UNKNOWN_SPELL_{name_lookup_id}",
            "description": description,
        })
    return out


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def to_identifier(text):
    ident = re.sub(r"[^0-9a-zA-Z]+", "_", text).strip("_").upper()
    if not ident:
        ident = "TREE"
    if ident[0].isdigit():
        ident = "T_" + ident
    return ident


def render(talents, tabs, style, class_filter=None, include_ranks=False):
    by_tab = {}
    for t in talents:
        by_tab.setdefault(t["tab"], []).append(t)

    def tab_sort_key(tab_id):
        tab = tabs.get(tab_id)
        if not tab:
            return ("zzz", 99, tab_id)
        return (tab["class_name"], tab["order"], tab_id)

    if style == "markdown":
        title = f"{class_filter} Talents" if class_filter else "Talents"
        lines = [f"# {title}", ""]
    else:
        lines = ["# Auto-generated by dump_talents.py. Format: (row, column, name)", ""]
    flat = []

    for tab_id in sorted(by_tab, key=tab_sort_key):
        tab = tabs.get(tab_id, {"name": f"Tab{tab_id}", "class_name": "Unknown", "order": 0})
        if class_filter and tab["class_name"].lower() != class_filter.lower():
            continue

        rows = sorted(by_tab[tab_id], key=lambda t: (t["row"], t["col"]))
        if style == "flat":
            flat.extend((tab["class_name"], tab["name"], r) for r in rows)
            continue

        if style == "markdown":
            lines.append(f'## {tab["class_name"]} - {tab["name"]}')
            lines.append("")
            for t in rows:
                lines.append(f'### ({t["row"]}, {t["col"]}) - {t["name"]} ({t["max_rank"]})')
                lines.append("")
                lines.append(t["description"] or "*(no description)*")
                lines.append("")
            continue

        var = f'{to_identifier(tab["class_name"])}_{to_identifier(tab["name"])}'
        lines.append(f'# {tab["class_name"]} - {tab["name"]} (TalentTab {tab_id})')
        lines.append(f"{var} = [")
        for t in rows:
            comment = f'  # {t["max_rank"]} rank(s), spell {t["spell_id"]}' if include_ranks else ""
            lines.append(f'    ({t["row"]}, {t["col"]}, "{t["name"]}"),{comment}')
        lines.append("]")
        lines.append("")

    if style == "flat":
        lines.append("Talents = [")
        for class_name, tab_name, t in flat:
            lines.append(
                f'    ({t["row"]}, {t["col"]}, "{t["name"]}"),'
                f'  # {class_name} / {tab_name}'
            )
        lines.append("]")
        lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Dump WoW talent trees as Python tuples.")
    ap.add_argument("dbc_folder", help="Folder containing Talent.dbc, TalentTab.dbc, Spell.dbc")
    ap.add_argument("--class", dest="class_filter", default=None,
                    help="Only emit trees for this class, e.g. Druid")
    ap.add_argument("--format", choices=["trees", "flat", "markdown"], default="trees",
                    help="'trees' = one list per tree (default), 'flat' = one combined list, "
                         "'markdown' = talent name + final-rank description as Markdown")
    ap.add_argument("--spell-name-field", type=int, default=SPELL_NAME_ENUS_DEFAULT,
                    help=f"Spell.dbc field index for enUS name (default {SPELL_NAME_ENUS_DEFAULT})")
    ap.add_argument("--spell-desc-field", type=int, default=SPELL_DESC_ENUS_DEFAULT,
                    help=f"Spell.dbc field index for enUS description (default {SPELL_DESC_ENUS_DEFAULT}), "
                         "only used by --format markdown")
    ap.add_argument("--ranks", action="store_true",
                    help="Append rank count and spell id as a trailing comment")
    ap.add_argument("--no-tokens", action="store_true",
                    help="Leave $s1/$m1/$h/... description tokens unresolved (markdown format only)")
    ap.add_argument("-o", "--output", default=None, help="Write to a file instead of stdout")
    args = ap.parse_args()

    try:
        spell_names = load_spell_names(find_dbc(args.dbc_folder, "Spell.dbc"), args.spell_name_field)
        spell_descriptions = None
        if args.format == "markdown":
            spell_descriptions = load_spell_descriptions(
                find_dbc(args.dbc_folder, "Spell.dbc"), args.spell_desc_field
            )
        tabs = load_tabs(find_dbc(args.dbc_folder, "TalentTab.dbc"))
        talents = load_talents(find_dbc(args.dbc_folder, "Talent.dbc"), spell_names, spell_descriptions)

        if args.format == "markdown" and not args.no_tokens:
            spell_records = load_spell_records(find_dbc(args.dbc_folder, "Spell.dbc"))
            durations = radii = cast_times = None
            missing = []
            try:
                durations = load_spell_duration(find_dbc(args.dbc_folder, "SpellDuration.dbc"))
            except FileNotFoundError:
                missing.append("SpellDuration.dbc ($d, $o)")
            try:
                radii = load_spell_radius(find_dbc(args.dbc_folder, "SpellRadius.dbc"))
            except FileNotFoundError:
                missing.append("SpellRadius.dbc ($b)")
            try:
                cast_times = load_spell_cast_times(find_dbc(args.dbc_folder, "SpellCastTimes.dbc"))
            except FileNotFoundError:
                missing.append("SpellCastTimes.dbc ($c)")
            if missing:
                print(f"note: not found, leaving tokens unresolved: {', '.join(missing)}", file=sys.stderr)

            for t in talents:
                t["description"] = resolve_tokens(
                    t["description"], t["final_spell_id"], spell_records, durations, radii, cast_times
                )
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    text = render(talents, tabs, args.format, args.class_filter, args.ranks)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {args.output} ({len(talents)} talents, {len(tabs)} tabs)", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())