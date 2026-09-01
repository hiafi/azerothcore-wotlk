"""
DBC column layouts for the DBCs this pipeline touches.

Each `fmt` string is transcribed verbatim from
`src/server/shared/DataStores/DBCfmt.h` and each `columns` list is transcribed
verbatim from the matching `CREATE TABLE` in `data/sql/base/db_world/*_dbc.sql`
(the same list AzerothCore's `DBCDatabaseLoader` reads via `SELECT * FROM
<table> ORDER BY ID DESC`).

Both were independently verified to be the same length for every table below,
which is the whole point of keeping them side by side here: `fmt[i]` describes
exactly `columns[i]`, in file-column order. See `docs/dbc-build-pipeline.md`
for why that isn't a coincidence — it's the *true* client column layout, not
an AzerothCore-truncated one, so it doubles as the schema for both the raw
binary DBC and the SQL overlay table.

Field format characters (from `src/common/DataStores/DBCFileLoader.h`):
    n = uint32, the index/primary-key field (always column 0 here)
    i = uint32
    f = float
    s = string (stored as a string-table offset in the binary file)
    x = uint32, unused by the C++ struct but still a real 4-byte column

A handful of 'i'/'x' columns are actually *signed* int32 in the real C++
struct (negative `EffectBasePoints`, `Duration == -1` for "infinite", etc.)
even though DBCfmt.h's format string can't distinguish that — `signed`
below lists exactly which ones, transcribed from the `int32`-typed fields in
`src/server/shared/DataStores/DBCStructure.h`. This only matters for reading
(both `dbcfile.read_dbc` and the SQL row values need the correct sign); the
2's-complement bit pattern round-trips correctly either way on write.

Separately, a few 'x' columns are genuinely *string* data in the real file
— AC's own C++ struct just never bothers exposing them (its comment says
"unused"), but the client still stores and can display them (e.g.
TalentTab's tab name — "Frost", "Fire", "Arcane" — which nothing server-side
reads but which a human very much wants to see when reversing a tab back to
source). `read_as_string` lists exactly those, so `dbcfile.py` decodes them
via the string table instead of exposing a meaningless raw offset. Same
byte layout either way (both are one 4-byte string-table offset), so this
changes nothing about what's written to the file — only how this tool reads
it back.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DbcTable:
    name: str                # friendly name, e.g. "Spell"
    dbc_filename: str        # e.g. "Spell.dbc"
    sql_table: str           # e.g. "spell_dbc"
    fmt: str                 # DBCfmt.h format string
    columns: tuple           # column names, same order/length as fmt
    signed: frozenset = field(default_factory=frozenset)  # see module docstring
    read_as_string: frozenset = field(default_factory=frozenset)  # see module docstring

    def __post_init__(self):
        if len(self.fmt) != len(self.columns):
            raise ValueError(
                f"{self.name}: fmt has {len(self.fmt)} fields but "
                f"{len(self.columns)} column names were given"
            )

    @property
    def index_column(self) -> str:
        return self.columns[self.fmt.index("n")]


def _cols(*groups) -> tuple:
    """Flatten a mix of single names, (base, count) repeat groups, and
    already-expanded tuples of column names (e.g. from `_locale_cols`)."""
    out = []
    for g in groups:
        if isinstance(g, tuple) and len(g) == 2 and isinstance(g[1], int):
            base, count = g
            out.extend(f"{base}_{i + 1}" for i in range(count))
        elif isinstance(g, tuple):
            out.extend(g)
        else:
            out.append(g)
    return tuple(out)


LOCALE_SUFFIXES = (
    "enUS", "enGB", "koKR", "frFR", "deDE", "enCN", "zhCN", "enTW",
    "zhTW", "esES", "esMX", "ruRU", "ptPT", "ptBR", "itIT", "Unk",
)


def _locale_cols(base: str) -> tuple:
    return tuple(f"{base}_Lang_{loc}" for loc in LOCALE_SUFFIXES) + (f"{base}_Lang_Mask",)


SPELL = DbcTable(
    name="Spell",
    dbc_filename="Spell.dbc",
    sql_table="spell_dbc",
    fmt=(
        "niiiiiiiiiiiixixiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiifxiiiiiiiiiiiiiiiiiiiiiiiiiii"
        "ifffiiiiiiiiiiiiiiiiiiiiifffiiiiiiiiiiiiiiifffiiiiiiiiiiiiiissssssssssssssss"
        "xssssssssssssssssxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxiiiiiiiiiiixfffxxxiiiiix"
        "xfffxx"
    ),
    columns=_cols(
        "ID", "Category", "DispelType", "Mechanic", "Attributes",
        "AttributesEx", "AttributesEx2", "AttributesEx3", "AttributesEx4",
        "AttributesEx5", "AttributesEx6", "AttributesEx7", "ShapeshiftMask",
        "unk_320_2", "ShapeshiftExclude", "unk_320_3", "Targets",
        "TargetCreatureType", "RequiresSpellFocus", "FacingCasterFlags",
        "CasterAuraState", "TargetAuraState", "ExcludeCasterAuraState",
        "ExcludeTargetAuraState", "CasterAuraSpell", "TargetAuraSpell",
        "ExcludeCasterAuraSpell", "ExcludeTargetAuraSpell",
        "CastingTimeIndex", "RecoveryTime", "CategoryRecoveryTime",
        "InterruptFlags", "AuraInterruptFlags", "ChannelInterruptFlags",
        "ProcTypeMask", "ProcChance", "ProcCharges", "MaxLevel", "BaseLevel",
        "SpellLevel", "DurationIndex", "PowerType", "ManaCost",
        "ManaCostPerLevel", "ManaPerSecond", "ManaPerSecondPerLevel",
        "RangeIndex", "Speed", "ModalNextSpell", "CumulativeAura",
        ("Totem", 2), ("Reagent", 8), ("ReagentCount", 8),
        "EquippedItemClass", "EquippedItemSubclass", "EquippedItemInvTypes",
        ("Effect", 3), ("EffectDieSides", 3), ("EffectRealPointsPerLevel", 3),
        ("EffectBasePoints", 3), ("EffectMechanic", 3),
        ("ImplicitTargetA", 3), ("ImplicitTargetB", 3),
        ("EffectRadiusIndex", 3), ("EffectAura", 3), ("EffectAuraPeriod", 3),
        ("EffectMultipleValue", 3), ("EffectChainTargets", 3),
        ("EffectItemType", 3), ("EffectMiscValue", 3), ("EffectMiscValueB", 3),
        ("EffectTriggerSpell", 3), ("EffectPointsPerCombo", 3),
        # GOTCHA (found 2026-08-27, see docs/dbc-build-pipeline.md "Bug 3"): unlike every other
        # per-effect field above, the letter here is the effect index (A=Effect_1, B=Effect_2,
        # C=Effect_3 - zero-based Effects[0..2] in the engine) and the _1/_2/_3 suffix is which of
        # that effect's 3 SpellFamilyFlags dwords - the reverse of what "_N = effect index" would
        # suggest by analogy with EffectBasePoints_1/2/3 etc. To scope Effect_2's own SpellMod (or
        # any per-effect classmask) to specific spells, the columns are EffectSpellClassMaskB_1/2/3
        # - NOT EffectSpellClassMaskA_2, which is Effect_1's second dword and leaves Effect_2's
        # actual classmask all-zero (SpellInfo::IsAffected treats all-zero as "matches every spell
        # in the family"). Got this backwards for Permafrost/Chilled to the Bone
        # (apps/dbc-tools/source/spells/mage_talents.csv) - fixed there; audit any other
        # hand-authored (non-"pulled from existing data") EffectSpellClassMask override before
        # trusting it.
        ("EffectSpellClassMaskA", 3), ("EffectSpellClassMaskB", 3),
        ("EffectSpellClassMaskC", 3), ("SpellVisualID", 2), "SpellIconID",
        "ActiveIconID", "SpellPriority",
        _locale_cols("Name"), _locale_cols("NameSubtext"),
        _locale_cols("Description"), _locale_cols("AuraDescription"),
        "ManaCostPct", "StartRecoveryCategory", "StartRecoveryTime",
        "MaxTargetLevel", "SpellClassSet", ("SpellClassMask", 3),
        "MaxTargets", "DefenseType", "PreventionType", "StanceBarOrder",
        ("EffectChainAmplitude", 3), "MinFactionID", "MinReputation",
        "RequiredAuraVision", ("RequiredTotemCategoryID", 2),
        "RequiredAreasID", "SchoolMask", "RuneCostID", "SpellMissileID",
        "PowerDisplayID", ("EffectBonusMultiplier", 3),
        "SpellDescriptionVariableID", "SpellDifficultyID",
    ),
    signed=frozenset(_cols(
        ("EffectBasePoints", 3), ("Reagent", 8), "EquippedItemClass",
        "EquippedItemSubclass", "EquippedItemInvTypes", ("EffectMiscValue", 3),
        ("EffectMiscValueB", 3), "PowerType", "RequiredAreasID", "PowerDisplayID",
    )),
    # Description/AuraDescription are 'x' in DBCfmt.h (AC's SpellEntry struct
    # never reads them), but the client does: this is the actual tooltip body
    # text. Without this, dbcfile.py treats them as plain uint32s — reading
    # the *old* string-table offset as a bare int and writing it back
    # unresolved, now pointing at an unrelated byte in the freshly-rebuilt
    # (much smaller) pool. Confirmed as the cause of the garbled/truncated
    # tooltips reported after a patch regenerate — see
    # docs/single-rank-spell-system.md's tooltip-corruption note.
    read_as_string=frozenset(
        f"{base}_Lang_{loc}"
        for base in ("Description", "AuraDescription")
        for loc in LOCALE_SUFFIXES
    ),
)

TALENT = DbcTable(
    name="Talent",
    dbc_filename="Talent.dbc",
    sql_table="talent_dbc",
    fmt="niiiiiiiixxxxixxixxixxx",
    columns=_cols(
        "ID", "TabID", "TierID", "ColumnIndex", ("SpellRank", 9),
        ("PrereqTalent", 3), ("PrereqRank", 3), "Flags", "RequiredSpellID",
        ("CategoryMask", 2),
    ),
)

TALENTTAB = DbcTable(
    name="TalentTab",
    dbc_filename="TalentTab.dbc",
    sql_table="talenttab_dbc",
    fmt="nxxxxxxxxxxxxxxxxxxxiiix",
    columns=_cols(
        "ID", _locale_cols("Name"), "SpellIconID", "RaceMask", "ClassMask",
        "PetTalentMask", "OrderIndex", "BackgroundFile",
    ),
    read_as_string=frozenset(f"Name_Lang_{loc}" for loc in LOCALE_SUFFIXES),
)

SPELLCASTTIMES = DbcTable(
    name="SpellCastTimes",
    dbc_filename="SpellCastTimes.dbc",
    sql_table="spellcasttimes_dbc",
    fmt="niii",
    columns=("ID", "Base", "PerLevel", "Minimum"),
    signed=frozenset(("Base", "PerLevel", "Minimum")),
)

SPELLDURATION = DbcTable(
    name="SpellDuration",
    dbc_filename="SpellDuration.dbc",
    sql_table="spellduration_dbc",
    fmt="niii",
    columns=("ID", "Duration", "DurationPerLevel", "MaxDuration"),
    signed=frozenset(("Duration", "DurationPerLevel", "MaxDuration")),
)

SPELLRANGE = DbcTable(
    name="SpellRange",
    dbc_filename="SpellRange.dbc",
    sql_table="spellrange_dbc",
    fmt="nffffixxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    columns=_cols(
        "ID", ("RangeMin", 2), ("RangeMax", 2), "Flags",
        _locale_cols("DisplayName"), _locale_cols("DisplayNameShort"),
    ),
)

SPELLRADIUS = DbcTable(
    name="SpellRadius",
    dbc_filename="SpellRadius.dbc",
    sql_table="spellradius_dbc",
    fmt="nfff",
    columns=("ID", "Radius", "RadiusPerLevel", "RadiusMax"),
)

SKILLLINEABILITY = DbcTable(
    name="SkillLineAbility",
    dbc_filename="SkillLineAbility.dbc",
    sql_table="skilllineability_dbc",
    fmt="niiiixxiiiiixx",
    columns=_cols(
        "ID", "SkillLine", "Spell", "RaceMask", "ClassMask", "ExcludeRace",
        "ExcludeClass", "MinSkillLineRank", "SupercededBySpell", "AcquireMethod",
        "TrivialSkillLineRankHigh", "TrivialSkillLineRankLow",
        ("CharacterPoints", 2),
    ),
)

# Not part of ALL_TABLES / the generate.py pipeline: these two have no source/*.csv convention or
# reserved ID block (ids.yaml) of their own - a single custom row is patched directly by
# patch_frozen_orb_model.py instead, reusing read_dbc/write_dbc off these definitions. ModelName
# (CreatureModelData) and the 4 texture/portrait columns (CreatureDisplayInfo) are 'x' in
# DBCfmt.h (AC's own struct never reads them) but are genuine string-table offsets in the real
# file - see dbcfile.py's read_as_string handling and this module's docstring.
CREATUREMODELDATA = DbcTable(
    name="CreatureModelData",
    dbc_filename="CreatureModelData.dbc",
    sql_table="creaturemodeldata_dbc",
    fmt="nixxfxxxxxxxxxfffxxxxxxxxxxx",
    columns=_cols(
        "ID", "Flags", "ModelName", "SizeClass", "ModelScale", "BloodID",
        "FootprintTextureID", "FootprintTextureLength", "FootprintTextureWidth",
        "FootprintParticleScale", "FoleyMaterialID", "FootstepShakeSize",
        "DeathThudShakeSize", "SoundID", "CollisionWidth", "CollisionHeight",
        "MountHeight", "GeoBoxMinX", "GeoBoxMinY", "GeoBoxMinZ", "GeoBoxMaxX",
        "GeoBoxMaxY", "GeoBoxMaxZ", "WorldEffectScale", "AttachedEffectScale",
        "MissileCollisionRadius", "MissileCollisionPush", "MissileCollisionRaise",
    ),
    read_as_string=frozenset({"ModelName"}),
)

CREATUREDISPLAYINFO = DbcTable(
    name="CreatureDisplayInfo",
    dbc_filename="CreatureDisplayInfo.dbc",
    sql_table="creaturedisplayinfo_dbc",
    fmt="nixifxxxxxxxxxxx",
    columns=_cols(
        "ID", "ModelID", "SoundID", "ExtendedDisplayInfoID", "CreatureModelScale",
        "CreatureModelAlpha", ("TextureVariation", 3), "PortraitTextureName",
        "BloodLevel", "BloodID", "NPCSoundID", "ParticleColorID",
        "CreatureGeosetData", "ObjectEffectPackageID",
    ),
    read_as_string=frozenset({"TextureVariation_1", "TextureVariation_2", "TextureVariation_3",
                               "PortraitTextureName"}),
)

ALL_TABLES = (
    SPELL, TALENT, TALENTTAB, SPELLCASTTIMES, SPELLDURATION, SPELLRANGE,
    SPELLRADIUS, SKILLLINEABILITY,
)
TABLES_BY_NAME = {t.name: t for t in ALL_TABLES}

if __name__ == "__main__":
    # Self-check: every table's fmt length must match its column count
    # (this is the property the whole pipeline leans on — see module docstring).
    for t in ALL_TABLES:
        assert len(t.fmt) == len(t.columns), t.name
        print(f"{t.name}: {len(t.fmt)} columns OK")
