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
    # The SQL overlay's mask columns are signed `int`; Blood's (398) stock RaceMask 0xFFFC07FF read
    # unsigned (4294707199) is rejected there (ERROR 1264 Out of range).
    signed=frozenset(("RaceMask", "ClassMask", "PetTalentMask")),
    # BackgroundFile is the talent frame's texture name ("MageFire"). Read as an int it was a
    # string-block offset, and a repack pointed it at the wrong string: every class's talent
    # background went blank (docs/bugs-and-fixes.md, 2026-10-02).
    read_as_string=frozenset(f"Name_Lang_{loc}" for loc in LOCALE_SUFFIXES) | {"BackgroundFile"},
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
    # The range text tooltips show ("Melee Range", "40 yd"). Read as ints these were string-block
    # offsets that a repack would point at the wrong string (same bug as TALENTTAB's BackgroundFile).
    read_as_string=frozenset(
        f"{base}_Lang_{loc}" for base in ("DisplayName", "DisplayNameShort") for loc in LOCALE_SUFFIXES
    ),
)

SPELLRADIUS = DbcTable(
    name="SpellRadius",
    dbc_filename="SpellRadius.dbc",
    sql_table="spellradius_dbc",
    fmt="nfff",
    columns=("ID", "Radius", "RadiusPerLevel", "RadiusMax"),
)

# Not part of ALL_TABLES / the generate.py resolve.py/build.py pipeline (no source/*.csv
# convention or reserved-ID block of its own - every row is a full-row override of an existing
# stock form, see lib/dsl/registry.py's shapeshift_form()) - handled instead through
# lib/spell_tables.py's generic declared-table path, same as spell_linked_spell/spell_group/
# spell_custom_attr.
SPELLSHAPESHIFTFORM = DbcTable(
    name="SpellShapeshiftForm",
    dbc_filename="SpellShapeshiftForm.dbc",
    sql_table="spellshapeshiftform_dbc",
    # SpellShapeshiftFormEntryfmt (DBCfmt.h). 35 fields, confirmed against a real extraction
    # (var/extractors/dbc/SpellShapeshiftForm.dbc, pulled from patch-enUS-3.MPQ same as Item.dbc -
    # see README's "Setup" list) — 140-byte records, matching DBCStructure.h's SpellShapeshiftFormEntry
    # struct exactly once the two "unused" 'x' runs are counted: bonusActionBar + Name[16] + NameFlags
    # (18 fields, columns 1-18) and attackIconID (1 field, column 21) and creatureDisplayID[2] (2
    # fields, columns 25-26) are real columns in the SQL overlay (AttackIconID, CreatureDisplayID_3/4)
    # even though the AC struct never reads them - same convention as every other table here.
    fmt="n" + "x" * 18 + "ii" + "x" + "iii" + "xx" + "i" * 8,
    columns=_cols(
        "ID", "BonusActionBar", _locale_cols("Name"), "Flags", "CreatureType",
        "AttackIconID", "CombatRoundTime", ("CreatureDisplayID", 4), ("PresetSpellID", 8),
    ),
    # creatureType is `int32` in DBCStructure.h ("<= 0 humanoid, other normal creature types") -
    # every other column here is a plain uint32.
    signed=frozenset(("CreatureType",)),
    # Name_Lang_* is 'x' in DBCfmt.h (AC's struct never reads it) but is real string-table-offset
    # data in the file (confirmed by extraction — form 5's Name_Lang_enUS offset is non-zero, i.e.
    # a real name string sits there), same TalentTab-style exception as this module's docstring
    # describes. Without this, dbcfile.py would read the raw offset as a bare integer and write it
    # straight into the varchar(100) SQL column (e.g. `53`) instead of the actual name text.
    read_as_string=frozenset(f"Name_Lang_{loc}" for loc in LOCALE_SUFFIXES),
)

ITEM = DbcTable(
    name="Item",
    dbc_filename="Item.dbc",
    sql_table="item_dbc",
    # Itemfmt in DBCfmt.h - the *class/subclass/display* index Item.dbc, not the
    # item_template overlay ItemHandler.cpp sends live (see docs/bugs-and-fixes.md,
    # "blank bag icon" entry, for why a custom item_template entry above 56806 needs
    # a row here too - ObjectMgr::LoadItemTemplates() looks every entry up against
    # this table's server-side overlay before the rest of that item's fields load).
    fmt="niiiiiii",
    columns=(
        "ID", "ClassID", "SubclassID", "Sound_Override_Subclassid", "Material",
        "DisplayInfoID", "InventoryType", "SheatheType",
    ),
    signed=frozenset(("Sound_Override_Subclassid", "Material")),
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

# Also not part of ALL_TABLES, same reasoning as CREATUREMODELDATA/CREATUREDISPLAYINFO above -
# patched directly by patch_mage_vfx_models.py. Nothing in DBCStructure.h defines a
# SpellVisualEntry/SpellVisualKitEntry/SpellVisualEffectNameEntry struct at all (grepped - only
# `Spell::SpellVisual` exists, a plain uint32[2] holding the *ID*, not a loaded row) - the AC
# server engine never reads these three tables' contents, only ships them through so the client
# has somewhere to look the ID up. SPELLVISUAL's columns/fmt are transcribed verbatim from
# data/sql/base/db_world/spellvisual_dbc.sql's CREATE TABLE (same convention as every table above);
# no equivalent *_dbc.sql exists for the other two, so SPELLVISUALKIT/SPELLVISUALEFFECTNAME below
# were instead derived by decoding real records from the working-copy binaries field-by-field and
# cross-checking against wowdev.wiki's documented semantics (both independently agreed) - see
# docs/reworks/fire-mage-meteor-vfx.md for that verification. Every column is 'x' (never 'i') since
# there is no AC struct to call any of them "used" by.
SPELLVISUAL = DbcTable(
    name="SpellVisual",
    dbc_filename="SpellVisual.dbc",
    sql_table="spellvisual_dbc",
    fmt="n" + "x" * 25 + "f" * 6,
    columns=_cols(
        "ID", "PrecastKit", "CastKit", "ImpactKit", "StateKit", "StateDoneKit",
        "ChannelKit", "HasMissile", "MissileModel", "MissilePathType",
        "MissileDestinationAttachment", "MissileSound", "AnimEventSoundID", "Flags",
        "CasterImpactKit", "TargetImpactKit", "MissileAttachment",
        "MissileFollowGroundHeight", "MissileFollowGroundDropSpeed",
        "MissileFollowGroundApproach", "MissileFollowGroundFlags", "MissileMotion",
        "MissileTargetingKit", "InstantAreaKit", "ImpactAreaKit", "PersistentAreaKit",
        "MissileCastOffsetX", "MissileCastOffsetY", "MissileCastOffsetZ",
        "MissileImpactOffsetX", "MissileImpactOffsetY", "MissileImpactOffsetZ",
    ),
    # -1 = "no attachment" in the client file; the SQL overlay's columns are signed `int`, so an
    # unsigned 4294967295 is rejected there (ERROR 1264 Out of range).
    signed=frozenset({"MissileDestinationAttachment", "MissileAttachment"}),
)

SPELLVISUALKIT = DbcTable(
    name="SpellVisualKit",
    dbc_filename="SpellVisualKit.dbc",
    sql_table="spellvisualkit_dbc",
    fmt="n" + "x" * 20 + "f" * 16 + "x",
    columns=_cols(
        "ID", "StartAnimID", "AnimID", "HeadEffect", "ChestEffect", "BaseEffect",
        "LeftHandEffect", "RightHandEffect", "BreathEffect", "LeftWeaponEffect",
        "RightWeaponEffect", ("SpecialEffect", 3), "WorldEffect", "SoundID", "ShakeID",
        ("CharProc", 4), ("CharParamZero", 4), ("CharParamOne", 4), ("CharParamTwo", 4),
        ("CharParamThree", 4), "Flags",
    ),
)

SPELLVISUALEFFECTNAME = DbcTable(
    name="SpellVisualEffectName",
    dbc_filename="SpellVisualEffectName.dbc",
    sql_table="spellvisualeffectname_dbc",
    fmt="nssffff",
    columns=_cols(
        "ID", "Name", "FileName", "AreaEffectSize", "Scale", "MinAllowedScale",
        "MaxAllowedScale",
    ),
)

# SpellIcon.dbc - not in DBCfmt.h at all (confirmed via grep: AzerothCore's DBCStores.cpp never
# loads this table server-side, so it has no LOAD_DBC call and thus no fmt string to transcribe
# from there the way every other table in this file is - see docs/ascension-asset-mining.md Part 1
# and build_patch_i.py, which is the one script that edits this). Two columns only (ID + a single
# texture path, no locale variants) - stable, well-documented WotLK-era client format. Deliberately
# excluded from ALL_TABLES below, same as SPELLVISUALEFFECTNAME/CREATUREMODELDATA/
# CREATUREDISPLAYINFO - a single-row-edit table outside generate.py's own source/*.csv pipeline,
# never round-tripped through the normal resolve/build/sql_out machinery.
SPELLICON = DbcTable(
    name="SpellIcon",
    dbc_filename="SpellIcon.dbc",
    sql_table="",  # no SQL overlay - client-only table, nothing server-side reads it
    fmt="ns",
    columns=_cols("ID", "TextureFilename"),
)

# SpellDescriptionVariables.dbc - the named tooltip variables (`$mult=$?s11151[${1.02}][${1}]`) a
# spell's SpellDescriptionVariableID points at (potency-system.PLAN.md P9). Client-only like
# SPELLICON: AC never loads it (DBCStructure.h has the field commented out, no LOAD_DBC), so there's
# no SQL overlay. Two columns, no locale variants. The stock file (patch-enUS-3.MPQ) has 30 rows,
# IDs 1-181, lines separated by "\r\n". Declared rows come from the DSL's tooltip_vars() and
# generate.py merges them over var/extractors/dbc/SpellDescriptionVariables.dbc into patch-Z.mpq.
# Not in ALL_TABLES: nothing here is diffed against SQL state.
SPELLDESCRIPTIONVARIABLES = DbcTable(
    name="SpellDescriptionVariables",
    dbc_filename="SpellDescriptionVariables.dbc",
    sql_table="",  # no SQL overlay - client-only table, nothing server-side reads it
    fmt="ns",
    columns=_cols("ID", "Variables"),
)

# Not part of ALL_TABLES, same reasoning/pattern as CREATUREMODELDATA/CREATUREDISPLAYINFO above -
# patched directly by whichever one-off script needs a new GameObjectDisplayInfo row (e.g. a
# ground-trap GO's dropped-item model), reusing read_dbc/write_dbc off this definition.
# Server-loaded (DBCStores.cpp: LOAD_DBC(sGameObjectDisplayInfoStore, "GameObjectDisplayInfo.dbc",
# "gameobjectdisplayinfo_dbc")), so a new row needs the matching SQL overlay too, same as
# CreatureModelData/CreatureDisplayInfo. fmt/columns transcribed from DBCfmt.h's
# GameObjectDisplayInfofmt ("nsxxxxxxxxxxffffffx") and DBCStructure.h's GameObjectDisplayInfoEntry -
# ModelName and the 10 Sound_N slots are 'x' in the AC struct (never read server-side) but are real
# columns in the file/SQL overlay, same string-offset convention read_as_string handles elsewhere in
# this module.
GAMEOBJECTDISPLAYINFO = DbcTable(
    name="GameObjectDisplayInfo",
    dbc_filename="GameObjectDisplayInfo.dbc",
    sql_table="gameobjectdisplayinfo_dbc",
    fmt="nsxxxxxxxxxxffffffx",
    columns=_cols(
        "ID", "ModelName", ("Sound", 10), "GeoBoxMinX", "GeoBoxMinY", "GeoBoxMinZ",
        "GeoBoxMaxX", "GeoBoxMaxY", "GeoBoxMaxZ", "ObjectEffectPackageID",
    ),
    read_as_string=frozenset({"ModelName"}),
)

# SpellCategory.dbc - one Flags column per Spell.dbc `Category` id (stock IDs up to 1253; the
# ids.yaml `spellcategory` block 1300-1319 is for custom categories). Paladin T1: spell_category()
# declares the row; the server side goes out through spell_tables.py's SPELL_TABLES
# (`spellcategory_dbc`) and generate.py merges the same declared rows over
# var/extractors/dbc/SpellCategory.dbc into patch-Z.mpq, so the client knows the category too.
# Deliberately NOT in ALL_TABLES / SECONDARY_TABLES: that would emit the SQL a second time.
SPELLCATEGORY = DbcTable(
    name="SpellCategory",
    dbc_filename="SpellCategory.dbc",
    sql_table="spellcategory_dbc",
    fmt="ni",
    columns=("ID", "Flags"),
)

# SpellRuneCost.dbc - what a rune ability costs and the Runic Power it generates (Death Knight T1).
# Columns are `ID, Blood, Unholy, Frost, RunicPower` (data/sql/base/db_world/spellrunecost_dbc.sql and
# SpellRuneCostfmt "niiii", DBCfmt.h). `SpellRuneCostEntry::RuneCost[3]` is indexed by `RuneType`
# (RUNE_BLOOD 0, RUNE_UNHOLY 1, RUNE_FROST 2, Player.h; the loops in Spell.cpp CheckRuneCost/TakeRunePower), so
# the order is **Blood, Unholy, Frost**. The comment `0=blood, 1=frost, 2=unholy` at DBCStructure.h:1843 is
# WRONG (stock proof: 241 Icy Touch = (0, 0, 1, 100), 482 Frost Presence = (0, 0, 1, 0), 797 = (0, 1, 1, 150)).
# `RunicPower` is stored x10 (100 = 10 RP; the player's maximum is 1000). Both halves only apply to a spell whose
# `PowerType` is 5 (RUNE). Deliberately NOT in ALL_TABLES / SECONDARY_TABLES (same reason as SPELLCATEGORY: the
# SQL would go out twice): the server half is spell_tables.py's `spellrunecost_dbc` entry, and generate.py merges
# the declared rows over var/extractors/dbc/SpellRuneCost.dbc into patch-Z.mpq for the client.
SPELLRUNECOST = DbcTable(
    name="SpellRuneCost",
    dbc_filename="SpellRuneCost.dbc",
    sql_table="spellrunecost_dbc",
    fmt="niiii",
    columns=("ID", "Blood", "Unholy", "Frost", "RunicPower"),
)

# ChrClasses.dbc - server-side only (Death Knight T1, lib/dsl/registry.py's chr_class()). The server picks the
# first-login cinematic from `ChrClasses.CinematicSequence` of the class, else `ChrRaces.CinematicSequence`
# (CharacterHandler.cpp HandlePlayerLogin), so a full-row override of class 6 with CinematicSequenceID 0 gives a
# new DK its race's intro. fmt from DBCfmt.h's ChrClassesEntryfmt, columns from
# data/sql/base/db_world/chrclasses_dbc.sql (60 each). An overlay row REPLACES the whole row (power type,
# SpellClassSet, Required_Expansion, names), which is why the helper starts from the stock row. The fmt reads
# powerType (2), SpellClassSet (56), CinematicSequenceID (58) and Required_Expansion (59); Flags (57) is 'x'.
# The Female / Male / neutral-gender name columns and Filename are 'x' in the fmt but are string-table offsets in the
# file, so they are in `read_as_string` (the SPELLSHAPESHIFTFORM lesson). Stock file: the server's DBC directory
# (ac-worldserver:/azerothcore/env/dist/data/dbc/), flattened into var/extractors/dbc/. Not in ALL_TABLES.
CHRCLASSES = DbcTable(
    name="ChrClasses",
    dbc_filename="ChrClasses.dbc",
    sql_table="chrclasses_dbc",
    fmt="nxixssssssssssssssssxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxixii",
    columns=_cols(
        "ID", "Field01", "DisplayPower", "PetNameToken", _locale_cols("Name"), _locale_cols("Name_Female"),
        _locale_cols("Name_Male"), "Filename", "SpellClassSet", "Flags", "CinematicSequenceID",
        "Required_Expansion",
    ),
    read_as_string=frozenset(
        {f"{base}_Lang_{loc}" for base in ("Name_Female", "Name_Male") for loc in LOCALE_SUFFIXES}
        | {"Filename"}
    ),
)

# Not part of ALL_TABLES - patched directly by the one-off VFX scripts (patch_druid_vfx_models.py
# first) when a mined SpellVisualKit.SoundID has no stock row. Server-loaded (DBCStores.cpp:
# LOAD_DBC(sSoundEntriesStore, "SoundEntries.dbc", "soundentries_dbc")), but nothing server-side
# ever looks up a sound that only a SpellVisualKit references, so these rows ship client-only.
# Column names from data/sql/base/db_world/soundentries_dbc.sql. DBCfmt.h's SoundEntriesfmt is
# all 'x' (AC reads only the ID); the 3 float columns are 'f' here and the string columns are in
# read_as_string so the rows can actually be authored - same byte layout either way.
SOUNDENTRIES = DbcTable(
    name="SoundEntries",
    dbc_filename="SoundEntries.dbc",
    sql_table="soundentries_dbc",
    fmt="n" + "x" * 23 + "f" + "x" + "ff" + "xx",
    columns=_cols(
        "ID", "SoundType", "Name", ("File", 10), ("Freq", 10), "DirectoryBase", "Volumefloat",
        "Flags", "MinDistance", "DistanceCutoff", "EAXDef", "SoundEntriesAdvancedID",
    ),
    read_as_string=frozenset({"Name", *(f"File_{i}" for i in range(1, 11)), "DirectoryBase"}),
)

# LFGDungeons.dbc - the dungeon finder entries. Read by lfg_exclude() (lib/dsl/registry.py), whose lint checks each
# declared map id against the MapID column, and written by the dungeon finder declarations of lib/dsl/lfg.py
# (lfg_random() / lfg_heroic(), rows built by lib/lfg_dungeons.py): server overlay `lfgdungeons_dbc` (DBCStores.cpp:
# LOAD_DBC(sLFGDungeonStore, "LFGDungeons.dbc", "lfgdungeons_dbc"), empty in stock) and a merge over the stock file
# into patch-Z, because the client takes the names, the "Specific Dungeons" list and its section headers from its
# own copy. fmt from DBCfmt.h's LFGDungeonEntryfmt, columns from data/sql/base/db_world/lfgdungeons_dbc.sql.
# TextureFilename and the Description locales are 'x' in the fmt but string-table offsets in the file
# (read_as_string). The stock file (max ID 294) is ordered by (TypeID, ID) - see dbcfile.pack_client_dbc.
# Stock file: patch-enUS-3.MPQ, flattened into var/extractors/dbc/ like Item.dbc. Not in ALL_TABLES (the SQL would
# go out twice, as for MAPDIFFICULTY).
LFGDUNGEONS = DbcTable(
    name="LFGDungeons",
    dbc_filename="LFGDungeons.dbc",
    sql_table="lfgdungeons_dbc",
    fmt="nssssssssssssssssxiiiiiiiiixxixixxxxxxxxxxxxxxxxx",
    columns=_cols(
        "ID", _locale_cols("Name"), "MinLevel", "MaxLevel", "Target_Level", "Target_Level_Min",
        "Target_Level_Max", "MapID", "Difficulty", "Flags", "TypeID", "Faction", "TextureFilename",
        "ExpansionLevel", "Order_Index", "Group_Id", _locale_cols("Description"),
    ),
    signed=frozenset({"Faction"}),
    read_as_string=frozenset({"TextureFilename"} | {f"Description_Lang_{loc}" for loc in LOCALE_SUFFIXES}),
)

# LFGDungeonGroup.dbc - the section headers of the dungeon finder's "Specific Dungeons" list ("Classic Dungeons",
# "Burning Crusade Heroic", ...): an LFGDungeons row's Group_Id names one. Client-only: no server table, nothing
# server-side reads it (LFGMgr groups by the LFGDungeons Group_Id number alone), so declared rows (lib/dsl/lfg.py's
# lfg_group()) only merge into patch-Z. Layout from the stock file itself (21 fields: ID, 16 name locales + mask,
# OrderIndex, ParentGroupID, TypeID; lower OrderIndex lists first, heroic sections are TypeID 5). The stock file (10
# rows, IDs 1-9 and 11) is ordered by (OrderIndex, ID) - see dbcfile.pack_client_dbc. Stock file: not in the client
# extract; copy it from the `azerothcore-wotlk_ac-client-data` docker volume (/dbc/LFGDungeonGroup.dbc) into
# var/extractors/dbc/. Not in ALL_TABLES.
LFGDUNGEONGROUP = DbcTable(
    name="LFGDungeonGroup",
    dbc_filename="LFGDungeonGroup.dbc",
    sql_table="",  # no SQL overlay - client-only table, nothing server-side reads it
    fmt="n" + "s" * 16 + "xiii",
    columns=_cols("ID", _locale_cols("Name"), "OrderIndex", "ParentGroupID", "TypeID"),
)

# MapDifficulty.dbc - one row per (map, difficulty) an instance supports: the entry-refused message, the lockout
# reset (RaidDuration, seconds; 0 = no lockout) and the group size (dungeon difficulties E1, lib/dsl/dungeon.py's
# heroic()). Server-loaded (DBCStores.cpp: LOAD_DBC(sMapDifficultyStore, "MapDifficulty.dbc", "mapdifficulty_dbc"))
# AND read by the client, which shows its own Message text when entry fails (TRANSFER_ABORT_DIFFICULTY) and names
# the save in Raid Info from Difficultystring, so a declared row goes out as both halves: the SPELL_TABLES
# `mapdifficulty_dbc` entry and a merge over var/extractors/dbc/MapDifficulty.dbc into patch-Z. fmt is DBCfmt.h's
# MapDifficultyEntryfmt ("diisxxxxxxxxxxxxxxxxiix") with the leading 'd' (index, not kept in the C++ struct) written
# 'n', the index char this module and dbcfile read; columns from data/sql/base/db_world/mapdifficulty_dbc.sql.
# The 15 non-enUS message locales and Difficultystring are 'x' in the fmt but string-table offsets in the file
# (read_as_string). The stock file (187 rows, max ID 753) is ordered by (MapID, Difficulty), not by ID - see
# dbcfile.pack_client_dbc. Stock file: the server's DBC directory (ac-worldserver:/azerothcore/env/dist/data/dbc/).
# Not in ALL_TABLES (the SQL would go out twice, as for SPELLRUNECOST).
MAPDIFFICULTY = DbcTable(
    name="MapDifficulty",
    dbc_filename="MapDifficulty.dbc",
    sql_table="mapdifficulty_dbc",
    fmt="niisxxxxxxxxxxxxxxxxiix",
    columns=_cols(
        "ID", "MapID", "Difficulty", _locale_cols("Message"), "RaidDuration", "MaxPlayers", "Difficultystring",
    ),
    read_as_string=frozenset({f"Message_Lang_{loc}" for loc in LOCALE_SUFFIXES[1:]} | {"Difficultystring"}),
)

# DungeonEncounter.dbc - one row per boss of an instance difficulty (dungeon difficulties E2, WP-T2). Server: the
# encounter index (`Bit`) of each (MapID, Difficulty) list that `instance_encounters` hangs a kill credit on
# (ObjectMgr::LoadInstanceEncounters, Map::UpdateEncounterState). Client: the boss list of the instance lock warning
# (SMSG_INSTANCE_LOCK_WARNING_QUERY carries the completed mask; GetInstanceLockTimeRemainingEncounter) and of the
# dungeon finder proposal. A declared heroic's rows go out as both halves: the SPELL_TABLES `dungeonencounter_dbc`
# entry and a merge over var/extractors/dbc/DungeonEncounter.dbc into patch-Z. fmt is DBCfmt.h's
# DungeonEncounterfmt; columns from data/sql/base/db_world/dungeonencounter_dbc.sql (OrderIndex, Name_Lang_Mask and
# SpellIconID are 'x' but real columns). OrderIndex is signed (stock -1000 rows sort first). The stock file (612
# rows, max ID 894) is ordered by (MapID, OrderIndex, ID) - see dbcfile.pack_client_dbc. Stock file: the server's DBC
# directory. Not in ALL_TABLES (the SQL would go out twice, as for MAPDIFFICULTY).
DUNGEONENCOUNTER = DbcTable(
    name="DungeonEncounter",
    dbc_filename="DungeonEncounter.dbc",
    sql_table="dungeonencounter_dbc",
    fmt="niixi" + "s" * 16 + "xx",
    columns=_cols("ID", "MapID", "Difficulty", "OrderIndex", "Bit", _locale_cols("Name"), "SpellIconID"),
    signed=frozenset({"OrderIndex"}),
)

# ItemLimitCategory.dbc - "Unique-Equipped: <name> (N)" groups (item variants IV10 follow-up 1, lib/item_limits.py:
# every tier of an item with an effect shares one category, Quantity 1, Flags 1 = equip mode). Server-loaded
# (DBCStores.cpp: LOAD_DBC(sItemLimitCategoryStore, "ItemLimitCategory.dbc", "itemlimitcategory_dbc"); ObjectMgr zeroes
# an item_template.ItemLimitCategory it cannot find) AND read by the client for the tooltip line, so a row goes out as
# both halves: the SPELL_TABLES `itemlimitcategory_dbc` entry and a merge over var/extractors/dbc/ItemLimitCategory.dbc
# into patch-Z. fmt is DBCfmt.h's ItemLimitCategoryEntryfmt ("nxxxxxxxxxxxxxxxxxii") with the 16 name locales written
# 's' (string-table offsets) and Name_Lang_Mask 'x'; columns from data/sql/base/db_world/itemlimitcategory_dbc.sql.
# Stock file (83 rows, max ID 85): the server's DBC directory (ac-worldserver:/azerothcore/env/dist/data/dbc/).
# Not in ALL_TABLES (the SQL would go out twice, as for MAPDIFFICULTY).
ITEMLIMITCATEGORY = DbcTable(
    name="ItemLimitCategory",
    dbc_filename="ItemLimitCategory.dbc",
    sql_table="itemlimitcategory_dbc",
    fmt="n" + "s" * 16 + "xii",
    columns=_cols("ID", _locale_cols("Name"), "Quantity", "Flags"),
)

# CreatureSpellData.dbc - a tamed/summoned pet's default spells, looked up by
# creature_template.PetSpellDataId (SpellMgr::LoadPetDefaultSpells). lib/superseded_ranks.py rewrites
# the records that name a superseded rank of a collapsed chain (pet-stale-ranks). Server-only: the
# rows go out as a creaturespelldata_dbc block, never into the client patch (the server alone decides
# a pet's spells and sends them in SMSG_PET_SPELLS). fmt from DBCfmt.h's CreatureSpellDatafmt, columns
# from data/sql/base/db_world/creaturespelldata_dbc.sql; Availability_* is 'x' (the AC struct never
# reads it) but is a real column. Stock file: patch-enUS.MPQ (no later patch-enUS-N.MPQ carries it,
# byte-identical to the server's extracted copy), flattened into var/extractors/dbc/. Not in ALL_TABLES.
CREATURESPELLDATA = DbcTable(
    name="CreatureSpellData",
    dbc_filename="CreatureSpellData.dbc",
    sql_table="creaturespelldata_dbc",
    fmt="niiiixxxx",
    columns=_cols("ID", ("Spells", 4), ("Availability", 4)),
)

# CreatureFamily.dbc - read-only reference for lib/superseded_ranks.py's retire_pet_spell(): a family's
# two pet skill lines (SkillLine_1 its own, SkillLine_2 usually the shared 270 "Pet - Hunter") say which
# SkillLineAbility rows teach its pets, and creature_template.family keys into ID. fmt from DBCfmt.h's
# CreatureFamilyfmt ("nfifiiiiixssssssssssssssssxx"); there is no creaturefamily SQL overlay to write
# (the base creaturefamily_dbc table is empty), so this table is never emitted. Stock file: the server's
# DBC dir (it is not in the client patch MPQs this tool extracts from), flattened into var/extractors/dbc/.
# Not in ALL_TABLES.
CREATUREFAMILY = DbcTable(
    name="CreatureFamily",
    dbc_filename="CreatureFamily.dbc",
    sql_table="creaturefamily_dbc",
    fmt="nfifiiiiix" + "s" * 16 + "xx",
    columns=_cols(
        "ID", "MinScale", "MinScaleLevel", "MaxScale", "MaxScaleLevel", ("SkillLine", 2), "PetFoodMask",
        "PetTalentType", "CategoryEnumID", _locale_cols("Name"), "IconFile",
    ),
    signed=frozenset({"PetTalentType"}),
    read_as_string=frozenset({"IconFile"}),
)

# SpellDifficulty.dbc - read-only reference for lib/heroic_templates.py's lint (dungeon difficulties E2, WP-G): the
# spell a cast becomes on each difficulty (Spell::Spell -> SpellMgr::GetSpellIdForDifficulty; DifficultySpellID_2 is the
# 5-man heroic). Never written. Server-loaded with the `spelldifficulty_dbc` overlay (DBCStores.cpp builds the
# searcher from rows with slots 1 and 2 set). fmt from DBCfmt.h's SpellDifficultyfmt, columns from
# data/sql/base/db_world/spelldifficulty_dbc.sql; SpellID[] is int32 (DBCStructure.h). Stock file: the server's DBC
# directory (ac-worldserver:/azerothcore/env/dist/data/dbc/), flattened into var/extractors/dbc/. Not in ALL_TABLES.
SPELLDIFFICULTY = DbcTable(
    name="SpellDifficulty",
    dbc_filename="SpellDifficulty.dbc",
    sql_table="spelldifficulty_dbc",
    fmt="niiii",
    columns=_cols("ID", ("DifficultySpellID", 4)),
    signed=frozenset({f"DifficultySpellID_{i}" for i in range(1, 5)}),
)

# SkillLine.dbc - one row per skill (crafting rework C2, lib/dsl/registry.py's override_skill_line()). Server-loaded
# (DBCStores.cpp: LOAD_DBC(sSkillLineStore, "SkillLine.dbc", "skillline_dbc")): `CategoryID` decides what counts as a
# primary profession (SKILL_CATEGORY_PROFESSION 11; SpellMgr.cpp IsPrimaryProfessionSkill) against
# MaxPrimaryTradeSkill. The client reads its own copy too: the Skills tab groups skills by CategoryID and shows the
# Unlearn button for category 11. So a declared row goes out as both halves: the SPELL_TABLES `skillline_dbc` entry
# and a merge over var/extractors/dbc/SkillLine.dbc into patch-Z. fmt is DBCfmt.h's SkillLinefmt, columns from
# data/sql/base/db_world/skillline_dbc.sql (56 each). SkillCostsID, the masks, Description and AlternateVerb are 'x'
# in the fmt; the two string groups are string-table offsets in the file (read_as_string). Stock file: the server's
# DBC directory (ac-worldserver:/azerothcore/env/dist/data/dbc/SkillLine.dbc), flattened into var/extractors/dbc/.
# Not in ALL_TABLES (the SQL would go out twice, as for MAPDIFFICULTY).
SKILLLINE = DbcTable(
    name="SkillLine",
    dbc_filename="SkillLine.dbc",
    sql_table="skillline_dbc",
    fmt="nix" + "s" * 16 + "x" + "x" * 17 + "i" + "x" * 17 + "i",
    columns=_cols(
        "ID", "CategoryID", "SkillCostsID", _locale_cols("DisplayName"), _locale_cols("Description"), "SpellIconID",
        _locale_cols("AlternateVerb"), "CanLink",
    ),
    read_as_string=frozenset(
        {f"{base}_Lang_{loc}" for base in ("Description", "AlternateVerb") for loc in LOCALE_SUFFIXES}
    ),
)

# --- Crafting rework C1: the four tables behind random suffixes, enchants and gems --------------------------------
#
# All four are server-loaded with a DB overlay (DBCStores.cpp LOAD_DBC(..., "<table>_dbc"), :312 / :335 / :367 / :368)
# AND read by the client from its own copy, so a declared row goes out as both halves: the SPELL_TABLES entry and a
# merge over the stock file into patch-Z. Client use: SpellItemEnchantment's Name is the enchant line in an item
# tooltip ("+8 Mastery"), ItemRandomSuffix's Name is the "of the Tiger" in an item's name, GemProperties decides a
# gem item's color (socket matching, the gem tooltip) and SpellItemEnchantmentCondition the meta gem requirement line
# (red / grey "Requires ..."). Every fmt is DBCfmt.h verbatim, every column list the base CREATE TABLE
# (data/sql/base/db_world/<table>_dbc.sql); the stock files come from the worldserver's DBC directory
# (ac-worldserver:/azerothcore/env/dist/data/dbc/), flattened into var/extractors/dbc/. None is in ALL_TABLES (the SQL
# would go out twice, as for MAPDIFFICULTY).

# SpellItemEnchantment.dbc - one row per enchant, gem bonus, socket bonus and random suffix part. `Effect_n` is the
# ItemEnchantmentType (DBCEnums.h: 1 combat spell, 2 damage, 3 equip spell, 4 resistance, 5 stat, 6 totem, 7 use spell,
# 8 prismatic socket); `EffectArg_n` is the stat / resistance / spell id and `EffectPointsMin_n` the amount (0 on a
# suffix part: the suffix factor scales it, PlayerStorage.cpp ApplyEnchantment). EffectPointsMax ('x') is a real
# column. `Name_Lang_Mask` is the client's locale mask ('x').
SPELLITEMENCHANTMENT = DbcTable(
    name="SpellItemEnchantment",
    dbc_filename="SpellItemEnchantment.dbc",
    sql_table="spellitemenchantment_dbc",
    fmt="n" + "i" * 7 + "xxx" + "iii" + "s" * 16 + "x" + "i" * 7,
    columns=_cols(
        "ID", "Charges", ("Effect", 3), ("EffectPointsMin", 3), ("EffectPointsMax", 3), ("EffectArg", 3),
        _locale_cols("Name"), "ItemVisual", "Flags", "Src_ItemID", "Condition_Id", "RequiredSkillID",
        "RequiredSkillRank", "MinLevel",
    ),
    # int32 in the SQL table (and in the file: stock enchant 27 has -10, 2605's ItemVisual is -1)
    signed=frozenset({f"EffectPoints{m}_{i}" for m in ("Min", "Max") for i in (1, 2, 3)} | {"ItemVisual"}),
)

# ItemRandomSuffix.dbc - the "of the X" suffixes. `Enchantment_n` is a SpellItemEnchantment id and `AllocationPct_n` its
# share of the item's suffix factor, in 1/10000ths (PlayerStorage.cpp ApplyEnchantment: AllocationPct * factor / 10000).
# InternalName ('x' in the fmt) is a string in the file.
ITEMRANDOMSUFFIX = DbcTable(
    name="ItemRandomSuffix",
    dbc_filename="ItemRandomSuffix.dbc",
    sql_table="itemrandomsuffix_dbc",
    fmt="n" + "s" * 16 + "xx" + "i" * 10,
    columns=_cols("ID", _locale_cols("Name"), "InternalName", ("Enchantment", 5), ("AllocationPct", 5)),
    read_as_string=frozenset({"InternalName"}),
)

# GemProperties.dbc - what a gem item (item_template.GemProperties) is: the enchant it applies and its color mask
# (`Type`: 1 meta, 2 red, 4 yellow, 8 blue; hybrids are the OR, SocketColor in SharedDefines.h). Maxcount_Inv / _Item
# are real columns ('x').
GEMPROPERTIES = DbcTable(
    name="GemProperties",
    dbc_filename="GemProperties.dbc",
    sql_table="gemproperties_dbc",
    fmt="nixxi",
    columns=_cols("ID", "Enchant_Id", "Maxcount_Inv", "Maxcount_Item", "Type"),
)

# SpellItemEnchantmentCondition.dbc - the meta gem requirement: up to five "compare the count of gem color A with gem
# color B / a value" clauses chained by `Logic_n`. The one table here with BYTE columns: the file's record is 64 bytes
# (ID, Lt_OperandType[5] bytes, Lt_Operand[5] uint32, Operator[5], Rt_OperandType[5] bytes, Rt_Operand[5] uint32,
# Logic[5] bytes), unaligned, and 'b' / 'X' are one byte each (dbcfile handles both). Lt_Operand ('x') and Logic ('X')
# are real columns even though the AC struct never reads them.
SPELLITEMENCHANTMENTCONDITION = DbcTable(
    name="SpellItemEnchantmentCondition",
    dbc_filename="SpellItemEnchantmentCondition.dbc",
    sql_table="spellitemenchantmentcondition_dbc",
    fmt="nbbbbbxxxxxbbbbbbbbbbiiiiiXXXXX",
    columns=_cols(
        "ID", ("Lt_OperandType", 5), ("Lt_Operand", 5), ("Operator", 5), ("Rt_OperandType", 5), ("Rt_Operand", 5),
        ("Logic", 5),
    ),
)

# World map tables for the vanilla dungeon maps (build_patch_w.py, patch-W.mpq). Client-only like SPELLICON: the
# server loads WorldMapArea.dbc for zone coordinate conversion only (DBCfmt.h indexes it by AreaID), and never loads
# the other two, so nothing here has a SQL overlay and the server copy stays stock. Columns are the 3.3.5a client
# layout (11 / 8 / 5 fields, checked against the stock patch-enUS-3.MPQ files). Not in ALL_TABLES.
#   WorldMapArea: one row per map the world map can show. AreaName is the art folder and tile prefix
#                 (Interface\WorldMap\<AreaName>\<AreaName><floor>_<tile>.blp); the four floats are its bounds.
#                 DisplayMapID and ParentWorldMapID are -1 for "none".
#   DungeonMap:   one row per floor of a dungeon map, with that floor's bounds; ParentWorldMapID is the outdoor
#                 zone map the "zoom out" button goes to.
#   DungeonMapChunk: ties a WMO group (the WMOGroupID of the dungeon's .wmo groups) to the DungeonMap floor the map
#                 switches to while the player stands in it; MinZ splits a group by height.
WORLDMAPAREA = DbcTable(
    name="WorldMapArea",
    dbc_filename="WorldMapArea.dbc",
    sql_table="",  # the server's worldmaparea_dbc overlay is not written: the maps are client-only
    fmt="niisffffiii",
    columns=_cols(
        "ID", "MapID", "AreaID", "AreaName", "LocLeft", "LocRight", "LocTop", "LocBottom", "DisplayMapID",
        "DefaultDungeonFloor", "ParentWorldMapID",
    ),
    signed=frozenset({"DisplayMapID", "ParentWorldMapID"}),
)

DUNGEONMAP = DbcTable(
    name="DungeonMap",
    dbc_filename="DungeonMap.dbc",
    sql_table="",
    fmt="niiffffi",
    columns=_cols("ID", "MapID", "FloorIndex", "MinX", "MaxX", "MinY", "MaxY", "ParentWorldMapID"),
    signed=frozenset({"ParentWorldMapID"}),
)

DUNGEONMAPCHUNK = DbcTable(
    name="DungeonMapChunk",
    dbc_filename="DungeonMapChunk.dbc",
    sql_table="",
    fmt="niiif",
    columns=_cols("ID", "MapID", "WMOGroupID", "DungeonMapID", "MinZ"),
)

ALL_TABLES = (
    SPELL, TALENT, TALENTTAB, SPELLCASTTIMES, SPELLDURATION, SPELLRANGE,
    SPELLRADIUS, SKILLLINEABILITY, ITEM,
)
TABLES_BY_NAME = {t.name: t for t in ALL_TABLES}

if __name__ == "__main__":
    # Self-check: every table's fmt length must match its column count
    # (this is the property the whole pipeline leans on — see module docstring).
    for t in ALL_TABLES:
        assert len(t.fmt) == len(t.columns), t.name
        print(f"{t.name}: {len(t.fmt)} columns OK")
