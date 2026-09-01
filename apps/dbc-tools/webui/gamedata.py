"""Lookups that make the raw integer/ID fields in source/spells/*.csv and
source/talents/*.yaml legible in the webui: named dropdown options instead of
bare numbers, and a couple of read-only previews pulled from data that
already exists elsewhere (an icon texture name, another spell's name/tooltip
text). Nothing here is written back to source/ — display-only.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
SHARED_DEFINES = REPO_ROOT / "src" / "server" / "shared" / "SharedDefines.h"
SPELL_ICON_NAMES_CSV = TOOL_ROOT / "var" / "spell_icon_names.csv"

# Spell.dbc's "school" column is actually a SchoolMask bitmask, not the plain
# SpellSchools ordinal (src/server/shared/SharedDefines.h) — 1 << ordinal for
# each of the 7 schools. Almost every real spell sets exactly one bit, hence
# a plain dropdown; a rarer multi-school mask still round-trips (see
# view_models.enum_options' "unknown value" fallback), it just won't have a
# name of its own.
SCHOOL_MASK_NAMES = {
    1: "Physical", 2: "Holy", 4: "Fire", 8: "Nature",
    16: "Frost", 32: "Shadow", 64: "Arcane",
}

# Powers enum, src/server/shared/SharedDefines.h. Small and stable enough
# (unlike SpellEffects below) that hand-keeping it here is simpler than
# parsing the enum's one hex/negative special case (POWER_HEALTH).
POWER_TYPE_NAMES = {
    0: "Mana", 1: "Rage", 2: "Focus", 3: "Energy", 4: "Happiness",
    5: "Rune", 6: "Runic Power", -2: "Health",
}

_SPELL_EFFECT_RE = re.compile(r"^\s*(SPELL_EFFECT_\w+)\s*=\s*(\d+),?\s*$")


@lru_cache(maxsize=1)
def spell_effect_names() -> dict[int, str]:
    """{effect type int: display name}, parsed straight out of
    src/server/shared/SharedDefines.h's `enum SpellEffects` — 165 entries,
    too many (and too easy to typo) to hand-transcribe and keep in sync by
    hand, so this reads the same source of truth the server itself builds
    from. Falls back to an empty dict (dropdown degrades to a plain number
    input) if the header isn't where expected."""
    if not SHARED_DEFINES.is_file():
        return {}
    text = SHARED_DEFINES.read_text(encoding="utf-8")
    start = text.find("enum SpellEffects")
    if start == -1:
        return {}
    end = text.find("};", start)
    names = {}
    for line in text[start:end].splitlines():
        m = _SPELL_EFFECT_RE.match(line)
        if m and m.group(1) != "TOTAL_SPELL_EFFECTS":
            names[int(m.group(2))] = m.group(1)
    return names


@lru_cache(maxsize=1)
def _spell_icon_paths() -> dict[int, str]:
    """{SpellIconID: raw "Interface\\Icons\\..." path}, from var/spell_icon_names.csv
    (a SpellIcon.dbc dump the server itself never loads — see the README's
    "Known limitations" — pulled in just for this)."""
    if not SPELL_ICON_NAMES_CSV.is_file():
        return {}
    with open(SPELL_ICON_NAMES_CSV, newline="", encoding="utf-8") as f:
        return {int(row["id"]): row["path"] for row in csv.DictReader(f)}


def icon_url(icon_id: int | None) -> str | None:
    """wow.zamimg.com's icon CDN keys images by lowercased texture filename
    (no path, no extension in the source data) at a fixed URL shape — e.g.
    "Interface\\Icons\\Spell_Fire_Fireball" -> .../spell_fire_fireball.jpg.
    Returns None if icon_id is unset or not in the local SpellIcon.dbc dump."""
    if not icon_id:
        return None
    path = _spell_icon_paths().get(icon_id)
    if not path:
        return None
    slug = path.rsplit("\\", 1)[-1].lower()
    return f"https://wow.zamimg.com/images/wow/icons/large/{slug}.jpg"


def spell_summary(spell_id: int, spell_entries: list[dict]) -> dict | None:
    """{"name", "description"} for one spell ID, read from whichever
    source/spells/*.csv already has it — used for a talent's read-only
    "what does the last rank actually do" preview. `spell_entries` is
    whatever the caller already loaded (source.load_spells_csv's merged
    list), passed in rather than reloaded here so this stays a pure lookup."""
    entry = next((e for e in spell_entries if e["id"] == spell_id), None)
    if entry is None:
        return None
    overrides = entry.get("raw_overrides") or {}
    return {
        "name": entry.get("name") or "",
        "description": overrides.get("Description_Lang_enUS") or "",
    }
