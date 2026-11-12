"""
Crafting rework C7: the crafted sets (`.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md` decisions 2 and
3, ruled 2026-11-12). Pure data plus the derived rows; declared by `source/items/crafting_sets.py` (the items) and
`source/world/crafting_sets.py` (the recipes), the raid recipe items written by `write_crafting_set_items.py`.

**Sets.** Leveling sets at levels 15, 30 and 45 (item levels 20, 35, 50, Rare), a level-60 set (item level 60, Rare)
and one raid set per vanilla tier at its heroic item level (T1 76, T2 86, T3 96, Epic). Every set is the same
catalog (decisions 2a B, 2b A, 2c A, 3a):

- the eight armor slots of the ten dungeon archetypes: the six main slots from the armor type's profession (Tailoring
  cloth, Leatherworking leather and mail, Blacksmithing plate), Waist from Leatherworking and Wrist from Blacksmithing
  for every armor type (R23);
- six backs from Tailoring, one per primary plus two tank backs (Strength and Agility);
- Blacksmithing weapons and shields, an Enchanting staff and wand, an Engineering rifle, two Inscription off-hands and
  four Jewelcrafting rings and necks (throughput and tank; secondary stats only, the loot rule for jewelry).

**Stats.** The base item is primary + Stamina at `primary_share` 6000 (C4 B1), the secondaries a random suffix from
the C4 pools (9000 throughput, 9001 tank; `item(..., suffix_pool=)`), so Missives choose them. Tank pieces take +25%
Stamina (the dungeon tank items' `extra_stamina`). Rings and necks have no primary: the whole budget is the suffix.

**Sockets** (2d, 3b): none below the raid sets. A raid piece has one socket, red on damage and healing gear and blue
on tank gear; a head has a meta socket plus that one. The socket bonus is a flat +4 secondary of the role: Haste on
damage and healing gear, Parry on tank gear.

**Recipes** (2e A, 3e A). Every item has one recipe spell on its profession's skill line. The leveling and level-60
recipes are taught by the profession's Azeroth trainer. The raid recipes are learned from recipe items that drop from
the tier's raid bosses: one recipe item per armor type and slot teaches every archetype of it (a learn spell with up
to three learn effects), the backs, weapons and jewelry in groups of up to three.

**Materials.** Per set, the profession's material of the level band; raid sets add the level-60 fine material
(Mooncloth, Enchanted Leather, Arcanite Bar) and the tier material (3d A: Fiery Core, Elementium Ore, Large Obsidian
Shard). Counts scale with the slot (major 1.0, medium 0.75, minor 0.5625, two-hand 1.0). Per-tier data, so the later
scarcity stage can retune it.

**Ids** (decision 10): recipe spells 207600 + n, raid learn spells 208600 + n, SkillLineAbility 31200 + n, raid recipe
items 78000 + n (hand-picked, carved off the top of `item_minted`); the set items are minted by `item()`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# --- Professions and trainers (C6 section 1.8) ------------------------------------------------------------------------
BLACKSMITHING, LEATHERWORKING, TAILORING, ENGINEERING = 164, 165, 197, 202
ENCHANTING, JEWELCRAFTING, INSCRIPTION = 333, 755, 773
TRAINER = {BLACKSMITHING: 60, LEATHERWORKING: 61, TAILORING: 74, ENGINEERING: 92, ENCHANTING: 96,
           JEWELCRAFTING: 113, INSCRIPTION: 121}
# Recipe item subclasses (ItemSubclassRecipe) and their stock icon displays (a stock recipe of the profession).
RECIPE_SUBCLASS = {LEATHERWORKING: 1, TAILORING: 2, ENGINEERING: 3, BLACKSMITHING: 4, ENCHANTING: 8,
                   JEWELCRAFTING: 10, INSCRIPTION: 11}
# Trainer price per set (user 2026-11-12): 10 copper, 1 silver, 10 silver, 1 gold.
TRAIN_COST = {"s15": 10, "s30": 100, "s45": 1000, "s60": 10000}

# --- Ids --------------------------------------------------------------------------------------------------------------
RECIPE_SPELL_BASE = 207600
LEARN_SPELL_BASE = 208600
SLA_BASE = 31200
RECIPE_ITEM_BASE = 78000

# --- Suffix pools (C4) and socket bonuses -----------------------------------------------------------------------------
POOL_THROUGHPUT, POOL_TANK = 9000, 9001
TANK_EXTRA_STAMINA = 0.25
BONUS_HASTE_4, BONUS_PARRY_4 = 3267, 3359  # stock +4 Haste Rating / +4 Parry Rating socket bonuses
SOCKET_META, SOCKET_RED, SOCKET_BLUE = 1, 2, 8

# --- Reagent items ----------------------------------------------------------------------------------------------------
BOLT = {"s15": 2997, "s30": 4305, "s45": 4339, "s60": 14048}  # Woolen, Silk, Mageweave, Runecloth
THREAD = {"s15": 2321, "s30": 4291, "s45": 8343, "s60": 14341}  # Fine, Silken, Heavy Silken, Rune
LEATHER = {"s15": 2319, "s30": 4234, "s45": 4304, "s60": 8170}  # Medium, Heavy, Thick, Rugged
METAL = {"s15": 2841, "s30": 3859, "s45": 3860, "s60": 12359}  # Bronze, Steel, Mithril, Thorium
GEM = {"s15": 1206, "s30": 1529, "s45": 7909, "s60": 7910}  # Moss Agate, Jade, Aquamarine, Star Ruby
TUBE = {"s15": 4371, "s30": 4389, "s45": 10559, "s60": 16000}  # Bronze Tube, Gyrochronatom, Mithril / Thorium Tube
INK = {"s15": 43116, "s30": 43123, "s45": 43121, "s60": 43118}  # Lion's, Sky, Fiery, Jadefire
PARCHMENT = 39354  # Light Parchment
ILLUSION_DUST, LESSER_ETERNAL, GREATER_ETERNAL = 16204, 16202, 16203
SMALL_BRILLIANT, LARGE_BRILLIANT = 14343, 14344
MOONCLOTH, ENCHANTED_LEATHER, ARCANITE_BAR, ROYAL_INK = 14342, 12810, 12360, 43119
TIER_MATERIAL = {"t1": 17010, "t2": 18562, "t3": 22203}  # Fiery Core, Elementium Ore, Large Obsidian Shard


@dataclass(frozen=True)
class CraftSet:
    key: str
    level: int  # RequiredLevel
    ilvl: int
    quality: int
    raid: bool
    mats: str  # the level band whose materials it uses
    label: str


RARE, EPIC = 3, 4
SETS = (
    CraftSet("s15", 15, 20, RARE, False, "s15", "level 15"),
    CraftSet("s30", 30, 35, RARE, False, "s30", "level 30"),
    CraftSet("s45", 45, 50, RARE, False, "s45", "level 45"),
    CraftSet("s60", 60, 60, RARE, False, "s60", "level 60"),
    CraftSet("t1", 60, 76, EPIC, True, "s60", "T1 raid"),
    CraftSet("t2", 60, 86, EPIC, True, "s60", "T2 raid"),
    CraftSet("t3", 60, 96, EPIC, True, "s60", "T3 raid"),
)
SET_BY_KEY = {s.key: s for s in SETS}

# Name words per set: armor type material, then the raid tier names (the empowered labels).
RAID_WORD = {"t1": "Molten", "t2": "Draconic", "t3": "Chthonic"}
ARMOR_WORD = {
    "cloth": {"s15": "Woolen", "s30": "Silken", "s45": "Mageweave", "s60": "Runecloth"},
    "leather": {"s15": "Tanned", "s30": "Hardened", "s45": "Thick", "s60": "Rugged"},
    "mail": {"s15": "Riveted", "s30": "Linked", "s45": "Scaled", "s60": "Wyrmscale"},
    "plate": {"s15": "Bronze", "s30": "Steel", "s45": "Mithril", "s60": "Thorium"},
}
WEAPON_WORD = {"s15": "Bronze", "s30": "Steel", "s45": "Mithril", "s60": "Thorium"}
ENCHANTED_WORD = {"s15": "Runed", "s30": "Mystic", "s45": "Arcane", "s60": "Enchanted"}
SCRIBE_WORD = {"s15": "Inscribed", "s30": "Illuminated", "s45": "Gilded", "s60": "Runebound"}
GEM_WORD = {"s15": "Moss Agate", "s30": "Jade", "s45": "Aquamarine", "s60": "Star Ruby"}


def set_word(table: dict, craft_set: CraftSet) -> str:
    return RAID_WORD[craft_set.key] if craft_set.raid else table[craft_set.key]


# --- Archetypes (boss-rework-systems.md section 2, Archetypes) --------------------------------------------------------
@dataclass(frozen=True)
class Archetype:
    key: str
    armor: str
    primary: str
    tank: bool
    word: str  # the name word


STRENGTH, AGILITY, INTELLECT, SPIRIT = "Strength (Solo)", "Agility (Solo)", "Intellect (Solo)", "Spirit (Solo)"
ARCHETYPES = (
    Archetype("plate_str", "plate", STRENGTH, False, "Battle"),
    Archetype("plate_tank", "plate", STRENGTH, True, "Guardian"),
    Archetype("plate_int", "plate", INTELLECT, False, "Templar"),
    Archetype("mail_agi", "mail", AGILITY, False, "Stalker"),
    Archetype("mail_int", "mail", INTELLECT, False, "Seer"),
    Archetype("leather_agi", "leather", AGILITY, False, "Prowler"),
    Archetype("leather_tank", "leather", AGILITY, True, "Bruin"),
    Archetype("leather_spirit", "leather", SPIRIT, False, "Wildheart"),
    Archetype("cloth_int", "cloth", INTELLECT, False, "Arcanist"),
    Archetype("cloth_spirit", "cloth", SPIRIT, False, "Devout"),
)
ARMOR_PROFESSION = {"cloth": TAILORING, "leather": LEATHERWORKING, "mail": LEATHERWORKING, "plate": BLACKSMITHING}

# Slot -> (slot weight for reagents, owner: None = the armor type's profession).
MAJOR, MEDIUM, MINOR = 1.0, 0.75, 0.5625
ARMOR_SLOTS = {
    "head": (MAJOR, None), "shoulder": (MEDIUM, None), "chest": (MAJOR, None), "legs": (MAJOR, None),
    "hands": (MEDIUM, None), "feet": (MEDIUM, None), "waist": (MEDIUM, LEATHERWORKING), "wrist": (MINOR, BLACKSMITHING),
}
SLOT_NOUN = {
    "cloth": {"head": "Hood", "shoulder": "Mantle", "chest": "Robe", "legs": "Trousers", "hands": "Gloves",
              "feet": "Slippers", "waist": "Sash", "wrist": "Cuffs"},
    "leather": {"head": "Cap", "shoulder": "Shoulders", "chest": "Tunic", "legs": "Leggings", "hands": "Gloves",
                "feet": "Boots", "waist": "Belt", "wrist": "Bracers"},
    "mail": {"head": "Coif", "shoulder": "Spaulders", "chest": "Hauberk", "legs": "Legguards", "hands": "Gauntlets",
             "feet": "Greaves", "waist": "Girdle", "wrist": "Wristguards"},
    "plate": {"head": "Helm", "shoulder": "Pauldrons", "chest": "Breastplate", "legs": "Legplates",
              "hands": "Handguards", "feet": "Sabatons", "waist": "Waistguard", "wrist": "Vambraces"},
}


@dataclass(frozen=True)
class Other:
    """A non-armor-slot item of every set (backs, weapons, shields, off-hands, jewelry)."""
    key: str
    profession: int
    look: str  # the LOOKS group
    noun: str
    word: dict  # the per-set name word table (raid sets use the tier word)
    primary: str | None
    tank: bool
    weight: float
    weapon_role: str | None = None


OTHERS = (
    Other("back_str", TAILORING, "back", "Battle Cloak", ARMOR_WORD["cloth"], STRENGTH, False, MINOR),
    Other("back_agi", TAILORING, "back", "Prowler Cloak", ARMOR_WORD["cloth"], AGILITY, False, MINOR),
    Other("back_int", TAILORING, "back", "Arcanist Cloak", ARMOR_WORD["cloth"], INTELLECT, False, MINOR),
    Other("back_spi", TAILORING, "back", "Devout Cloak", ARMOR_WORD["cloth"], SPIRIT, False, MINOR),
    Other("back_tank_str", TAILORING, "back", "Guardian Cloak", ARMOR_WORD["cloth"], STRENGTH, True, MINOR),
    Other("back_tank_agi", TAILORING, "back", "Bruin Cloak", ARMOR_WORD["cloth"], AGILITY, True, MINOR),
    Other("bs_sword", BLACKSMITHING, "sword_1h", "Broadsword", WEAPON_WORD, STRENGTH, False, MINOR, "physical"),
    Other("bs_greataxe", BLACKSMITHING, "axe_2h", "Greataxe", WEAPON_WORD, STRENGTH, False, MAJOR, "physical"),
    Other("bs_dirk", BLACKSMITHING, "dagger", "Dirk", WEAPON_WORD, AGILITY, False, MINOR, "physical"),
    Other("bs_warmace", BLACKSMITHING, "mace_1h", "Warmace", WEAPON_WORD, STRENGTH, True, MINOR, "tank"),
    Other("bs_scepter", BLACKSMITHING, "mace_1h", "Scepter", WEAPON_WORD, INTELLECT, False, MINOR, "caster"),
    Other("bs_bulwark", BLACKSMITHING, "shield", "Bulwark", WEAPON_WORD, STRENGTH, True, MINOR, "tank"),
    Other("bs_aegis", BLACKSMITHING, "shield", "Aegis", WEAPON_WORD, INTELLECT, False, MINOR, "caster"),
    Other("ench_staff", ENCHANTING, "staff", "Staff", ENCHANTED_WORD, INTELLECT, False, MAJOR, "caster"),
    Other("ench_wand", ENCHANTING, "wand", "Wand", ENCHANTED_WORD, INTELLECT, False, MINOR, "caster"),
    Other("eng_rifle", ENGINEERING, "gun", "Rifle", WEAPON_WORD, AGILITY, False, MINOR, "physical"),
    Other("insc_tome", INSCRIPTION, "offhand", "Tome", SCRIBE_WORD, INTELLECT, False, MINOR),
    Other("insc_codex", INSCRIPTION, "offhand", "Codex", SCRIBE_WORD, SPIRIT, False, MINOR),
    Other("jc_band", JEWELCRAFTING, "ring", "Band", GEM_WORD, None, False, MINOR),
    Other("jc_signet", JEWELCRAFTING, "ring", "Signet", GEM_WORD, None, True, MINOR),
    Other("jc_pendant", JEWELCRAFTING, "neck", "Pendant", GEM_WORD, None, False, MINOR),
    Other("jc_choker", JEWELCRAFTING, "neck", "Choker", GEM_WORD, None, True, MINOR),
)


@dataclass(frozen=True)
class CraftedItem:
    key: str
    set: CraftSet
    name: str
    like: int
    profession: int
    primary: str | None
    pool: int
    tank: bool
    weight: float
    slot: str
    group: str  # the raid recipe group (armor type + slot, or the Other's recipe group)
    weapon_role: str | None = None
    head: bool = False
    armor: str | None = None

    @property
    def sockets(self) -> tuple[int, ...]:
        if not self.set.raid:
            return ()
        color = SOCKET_BLUE if self.tank else SOCKET_RED
        return (SOCKET_META, color) if self.head else (color,)

    @property
    def socket_bonus(self) -> int | None:
        if not self.set.raid:
            return None
        return BONUS_PARRY_4 if self.tank else BONUS_HASTE_4

    @property
    def extra_stamina(self) -> float:
        return TANK_EXTRA_STAMINA if self.tank else 0.0


# Raid recipe groups for the non-armor items: one recipe item teaches every key of a group (at most three).
OTHER_GROUPS = {
    "back_str": "backs_a", "back_agi": "backs_a", "back_int": "backs_a",
    "back_spi": "backs_b", "back_tank_str": "backs_b", "back_tank_agi": "backs_b",
    "bs_sword": "bs_melee", "bs_greataxe": "bs_melee", "bs_dirk": "bs_melee",
    "bs_warmace": "bs_tank", "bs_bulwark": "bs_tank",
    "bs_scepter": "bs_caster", "bs_aegis": "bs_caster",
    "ench_staff": "ench", "ench_wand": "ench", "eng_rifle": "eng",
    "insc_tome": "insc", "insc_codex": "insc",
    "jc_band": "jc_rings", "jc_signet": "jc_rings", "jc_pendant": "jc_necks", "jc_choker": "jc_necks",
}
GROUP_NAME = {
    "backs_a": "Cloaks", "backs_b": "Cloaks of Devotion and Guarding", "bs_melee": "Weapons", "bs_tank": "Bulwark",
    "bs_caster": "Scepter and Aegis", "ench": "Staff and Wand", "eng": "Rifle", "insc": "Tome and Codex",
    "jc_rings": "Rings", "jc_necks": "Necklaces",
}
GROUP_PROFESSION = {
    "backs_a": TAILORING, "backs_b": TAILORING, "bs_melee": BLACKSMITHING, "bs_tank": BLACKSMITHING,
    "bs_caster": BLACKSMITHING, "ench": ENCHANTING, "eng": ENGINEERING, "insc": INSCRIPTION,
    "jc_rings": JEWELCRAFTING, "jc_necks": JEWELCRAFTING,
}


def _look(group: str, craft_set: CraftSet, index: int) -> int:
    looks = LOOKS[f"{group}:{craft_set.key}"]
    return looks[index % len(looks)]


def items() -> list[CraftedItem]:
    """Every crafted set item, in a fixed order (set, then armor by archetype and slot, then the others)."""
    out = []
    for craft_set in SETS:
        armor_index: dict[str, int] = {}
        for arch in ARCHETYPES:
            index = armor_index.setdefault(arch.armor, 0)
            armor_index[arch.armor] = index + 1
            for slot, (weight, owner) in ARMOR_SLOTS.items():
                word = set_word(ARMOR_WORD[arch.armor], craft_set)
                out.append(CraftedItem(
                    key=f"craft_{craft_set.key}_{arch.key}_{slot}", set=craft_set,
                    name=f"{word} {arch.word} {SLOT_NOUN[arch.armor][slot]}",
                    like=_look(f"{arch.armor}_{slot}", craft_set, index),
                    profession=owner or ARMOR_PROFESSION[arch.armor], primary=arch.primary,
                    pool=POOL_TANK if arch.tank else POOL_THROUGHPUT, tank=arch.tank, weight=weight, slot=slot,
                    group=f"{arch.armor}_{slot}", head=slot == "head", armor=arch.armor,
                ))
        for index, other in enumerate(OTHERS):
            out.append(CraftedItem(
                key=f"craft_{craft_set.key}_{other.key}", set=craft_set,
                name=f"{set_word(other.word, craft_set)} {other.noun}", like=_look(other.look, craft_set, index),
                profession=other.profession, primary=other.primary,
                pool=POOL_TANK if other.tank else POOL_THROUGHPUT, tank=other.tank, weight=other.weight,
                slot=other.key, group=OTHER_GROUPS[other.key], weapon_role=other.weapon_role,
            ))
    return out


def _count(base: int, weight: float) -> int:
    return max(1, math.ceil(base * weight))


def reagents(item: CraftedItem) -> tuple[tuple[int, int], ...]:
    """(item, count) pairs for the item's recipe."""
    band, w, prof = item.set.mats, item.weight, item.profession
    out: list[tuple[int, int]] = []
    if prof == TAILORING:
        out = [(BOLT[band], _count(8, w)), (THREAD[band], _count(2, w))]
        fine = MOONCLOTH
    elif prof == LEATHERWORKING:
        out = [(LEATHER[band], _count(10, w)), (THREAD[band], _count(2, w))]
        if item.armor == "mail":
            out.append((METAL[band], _count(4, w)))
        fine = ENCHANTED_LEATHER
    elif prof == BLACKSMITHING:
        out = [(METAL[band], _count(10, w))]
        fine = ARCANITE_BAR
    elif prof == ENGINEERING:
        out = [(METAL[band], _count(10, w)), (TUBE[band], 1)]
        fine = ARCANITE_BAR
    elif prof == JEWELCRAFTING:
        out = [(METAL[band], _count(6, w)), (GEM[band], _count(4, w))]
        fine = ARCANITE_BAR
    elif prof == ENCHANTING:
        essence = GREATER_ETERNAL if band == "s60" else LESSER_ETERNAL
        shard = LARGE_BRILLIANT if band == "s60" else SMALL_BRILLIANT
        out = [(ILLUSION_DUST, _count(8, w)), (essence, _count(3, w)), (shard, _count(2, w))]
        fine = LARGE_BRILLIANT
    elif prof == INSCRIPTION:
        out = [(INK[band], _count(8, w)), (PARCHMENT, _count(4, w))]
        fine = ROYAL_INK
    else:
        raise ValueError(f"{item.key}: no reagents for profession {prof}")
    # A Waist (Leatherworking) or Wrist (Blacksmithing) of another armor type also takes that armor type's material.
    if item.armor is not None and prof != ARMOR_PROFESSION[item.armor]:
        out.append(_armor_material(item.armor, band, w))
    if item.set.key == "s60":  # the level-60 set takes the fine material too (ruling 2e table)
        out.append((fine, _count(2, w)))
    if item.set.raid:
        out = [(reagent, count * 2) for reagent, count in out]
        out.append((fine, _count(4, w)))
        out.append((TIER_MATERIAL[item.set.key], _count(4, w)))
    merged: dict[int, int] = {}
    for reagent, count in out:
        merged[reagent] = merged.get(reagent, 0) + count
    return tuple(merged.items())


def _armor_material(armor: str, band: str, weight: float) -> tuple[int, int]:
    if armor == "cloth":
        return BOLT[band], _count(6, weight)
    if armor == "plate":
        return METAL[band], _count(6, weight)
    return LEATHER[band], _count(6, weight)


@dataclass(frozen=True)
class RecipeRow:
    item: CraftedItem
    spell: int
    sla: int


def recipes() -> list[RecipeRow]:
    """One recipe per item, ids in item order."""
    return [RecipeRow(item, RECIPE_SPELL_BASE + n, SLA_BASE + n) for n, item in enumerate(items())]


@dataclass(frozen=True)
class RaidRecipeItem:
    entry: int
    learn_spell: int
    set: CraftSet
    profession: int
    name: str
    title: str  # what it teaches, e.g. "Molten Plate Helms"
    teaches: tuple[RecipeRow, ...]

    @property
    def description(self) -> str:
        """The item's and the learn spell's tooltip text."""
        first = self.teaches[0].item
        if first.armor is not None:
            words = [next(a.word for a in ARCHETYPES if row.item.key.endswith(f"_{a.key}_{row.item.slot}"))
                     for row in self.teaches]
        else:
            words = [row.item.name.removeprefix(RAID_WORD[self.set.key] + " ") for row in self.teaches]
        return f"Teaches you how to craft the {self.title}: {', '.join(words)}."


def _plural(noun: str) -> str:
    if noun.endswith("s"):
        return noun
    return noun + ("es" if noun.endswith("sh") else "s")


def raid_recipe_items() -> list[RaidRecipeItem]:
    """The raid recipe items: per raid set, one per recipe group (armor type + slot, or an OTHER_GROUPS group)."""
    out = []
    for craft_set in (s for s in SETS if s.raid):
        groups: dict[str, list[RecipeRow]] = {}
        for row in recipes():
            if row.item.set is craft_set:
                groups.setdefault(row.item.group, []).append(row)
        for group, rows in groups.items():
            for start in range(0, len(rows), 3):
                chunk = tuple(rows[start:start + 3])
                first = chunk[0].item
                if first.armor is not None:
                    title = (f"{RAID_WORD[craft_set.key]} {first.armor.capitalize()} "
                             f"{_plural(SLOT_NOUN[first.armor][first.slot])}")
                else:
                    title = f"{RAID_WORD[craft_set.key]} {GROUP_NAME[group]}"
                kind = {TAILORING: "Pattern", LEATHERWORKING: "Pattern", BLACKSMITHING: "Plans",
                        ENGINEERING: "Schematic", ENCHANTING: "Formula", JEWELCRAFTING: "Design",
                        INSCRIPTION: "Technique"}[first.profession]
                n = len(out)
                out.append(RaidRecipeItem(RECIPE_ITEM_BASE + n, LEARN_SPELL_BASE + n, craft_set, first.profession,
                                          f"{kind}: {title}", title, chunk))
    return out


# --- Raid drops (decisions 3d and 3e) ---------------------------------------------------------------------------------
# Each tier's raid recipe items are one reference pool (equal chance, one item per roll); every boss of the tier rolls
# it in its own row (it rolls on top of the boss's list). The tier material drops from every boss and, rarely, from the
# elite trash. Rates are first-pass data for the later scarcity stage. Raids have no heroic difficulty yet, so the
# ruled heroic rate (40%) waits for the raid rework; the bosses roll the normal rate.
RECIPE_REFERENCE = {"t1": 1701001, "t2": 1701002, "t3": 1701003}  # ids.yaml crafting_loot_reference
RECIPE_CHANCE = 20.0
MATERIAL_BOSS_CHANCE, MATERIAL_BOSS_MAX = 50.0, 2
MATERIAL_TRASH_CHANCE = 3.0
# Boss lootids (creature_loot_template Entry) per tier, with the boss names for the comments.
RAID_BOSSES = {
    "t1": {  # Molten Core, Zul'Gurub, Onyxia's Lair, Azuregos, Lord Kazzak
        12118: "Lucifron", 11982: "Magmadar", 12259: "Gehennas", 12057: "Garr", 12056: "Baron Geddon",
        12264: "Shazzrah", 12098: "Sulfuron Harbinger", 11988: "Golemagg the Incinerator", 11502: "Ragnaros",
        14517: "High Priestess Jeklik", 14507: "High Priest Venoxis", 14510: "High Priestess Mar'li",
        14509: "High Priest Thekal", 14515: "High Priestess Arlokk", 11382: "Bloodlord Mandokir",
        15114: "Gahz'ranka", 15082: "Gri'lek", 15083: "Hazza'rah", 15084: "Renataki", 15085: "Wushoolay",
        11380: "Jin'do the Hexxer", 14834: "Hakkar", 46000: "Onyxia", 6109: "Azuregos", 12397: "Lord Kazzak",
    },
    "t2": {  # Blackwing Lair, the world dragons
        12435: "Razorgore the Untamed", 13020: "Vaelastrasz the Corrupt", 12017: "Broodlord Lashlayer",
        11983: "Firemaw", 14601: "Ebonroc", 11981: "Flamegor", 14020: "Chromaggus", 11583: "Nefarian",
        14887: "Ysondre", 14888: "Lethon", 14889: "Emeriss", 14890: "Taerar",
    },
    "t3": {  # Ruins and Temple of Ahn'Qiraj
        15348: "Kurinnaxx", 15341: "General Rajaxx", 15340: "Moam", 15370: "Buru the Gorger",
        15369: "Ayamiss the Hunter", 15339: "Ossirian the Unscarred", 15263: "The Prophet Skeram",
        15543: "Princess Yauj", 15544: "Vem", 15511: "Lord Kri", 15516: "Battleguard Sartura",
        15510: "Fankriss the Unyielding", 15299: "Viscidus", 15509: "Princess Huhuran", 15275: "Emperor Vek'nilash",
        15276: "Emperor Vek'lor", 15517: "Ouro", 15727: "C'Thun",
    },
}
# Majordomo Executus's loot is the Cache of the Firelord (gameobject_loot_template Entry).
RAID_CHESTS = {"t1": {16719: "Cache of the Firelord (Majordomo Executus)"}}
# Elite raid trash lootids per tier (rank 1 and 2 creatures spawned in the tier's raid maps, 2026-11-12).
RAID_TRASH = {
    "t1": (11338, 11339, 11340, 11350, 11351, 11352, 11353, 11356, 11357, 11359, 11361, 11365, 11370, 11371, 11372,
           11373, 11830, 11831, 14532, 14750, 14821, 14825, 14880, 14882, 14883, 15043, 15067, 15111, 11658, 11659,
           11661, 11662, 11665, 11666, 11667, 11668, 11673, 12076, 12100, 12101, 12119),
    "t2": (12457, 12459, 12460, 12461, 12463, 12464, 12465, 12467, 12468, 13996, 14401),
    "t3": (15318, 15319, 15320, 15323, 15324, 15325, 15327, 15335, 15336, 15338, 15343, 15355, 15385, 15386, 15388,
           15389, 15390, 15391, 15392, 15461, 15462, 15505, 15229, 15230, 15233, 15235, 15236, 15240, 15247, 15249,
           15250, 15252, 15262, 15264, 15277, 15311, 15312),
}
# Trash that already drops its tier material above the trash rate keeps the stock row (review S2): Molten Destroyer,
# Firewalker, Flameguard and Firelord (Fiery Core 15-42%), Blackwing Technician (Elementium Ore 7.7%).
MATERIAL_STOCK_TRASH = {"t1": (11659, 11666, 11667, 11668), "t2": (13996,)}
RECIPE_ITEM_DISPLAY = 6270  # the stock Molten Core recipes' scroll
RECIPE_ITEM_LEVEL = 60


# Stock looks per (group, set), picked by `.agents/plans/crafting-rework/c7-audit/pick_looks.py` (stock crafted items
# first, then non-set stock items of the slot, nearest item level, distinct displays; vanilla entries only). Each
# archetype of an armor type takes the next look of its group.
LOOKS = {
    'axe_2h:s15': (3487, 7957, 3488, 7958),
    'axe_2h:s30': (3853, 3855, 3854, 3856),
    'axe_2h:s45': (7960, 12764, 12769, 12775),
    'axe_2h:s60': (12782, 11607, 12784, 12790),
    'axe_2h:t1': (19169, 12784, 12790, 19354),
    'axe_2h:t2': (19169, 19364, 21679, 22813),
    'axe_2h:t3': (19169, 22691, 21134, 19364),
    'back:s15': (7283, 4311, 5542, 2316),
    'back:s30': (7053, 7056, 7377, 4326),
    'back:s45': (8215, 8216, 13860, 8195),
    'back:s60': (15138, 18413, 18509, 18510),
    'back:t1': (22660, 18413, 18509, 18510),
    'back:t2': (22658, 22660, 19386, 19398),
    'back:t3': (22658, 22660, 23045, 23050),
    'cloth_chest:s15': (6263, 2585, 6243, 2582),
    'cloth_chest:s30': (7058, 7051, 7065, 7054),
    'cloth_chest:s45': (13868, 13869, 13857, 13858),
    'cloth_chest:s60': (14128, 14138, 14106, 18486),
    'cloth_chest:t1': (22756, 19156, 19682, 14152),
    'cloth_chest:t2': (22652, 22756, 19156, 21527),
    'cloth_chest:t3': (22652, 22756, 23069, 23220),
    'cloth_feet:s15': (4313, 2583, 4312, 4320),
    'cloth_feet:s30': (4325, 4321, 7027, 9845),
    'cloth_feet:s45': (10039, 10044, 10031, 10026),
    'cloth_feet:s60': (19056, 14108, 20537, 13864),
    'cloth_feet:t1': (19684, 20537, 19438, 20631),
    'cloth_feet:t2': (21600, 19391, 21648, 21489),
    'cloth_feet:t3': (21600, 19391, 21648, 21489),
    'cloth_hands:s15': (4310, 4331, 4318, 10637),
    'cloth_hands:s30': (7049, 4319, 7047, 7064),
    'cloth_hands:s45': (13870, 14043, 14101, 14142),
    'cloth_hands:s60': (18409, 14146, 16979, 18407),
    'cloth_hands:t1': (14146, 16979, 18407, 18408),
    'cloth_hands:t2': (22654, 21619, 19407, 19369),
    'cloth_hands:t3': (22654, 21585, 21619, 19407),
    'cloth_head:s15': (4368, 4373),
    'cloth_head:s30': (10499, 4323, 4322, 4393),
    'cloth_head:s45': (10041, 10025, 10504, 10030),
    'cloth_head:s60': (13866, 14130, 14111, 14140),
    'cloth_head:t1': (22757, 19999, 21780, 14140),
    'cloth_head:t2': (22757, 21615, 21517, 19886),
    'cloth_head:t3': (22757, 23828, 23838, 23587),
    'cloth_legs:s15': (4316, 10048, 4317, 10047),
    'cloth_legs:s30': (7062, 9999, 7046, 10002),
    'cloth_legs:s45': (14107, 14132, 10010, 13871),
    'cloth_legs:s60': (14104, 14137, 14144, 13865),
    'cloth_legs:t1': (19165, 19683, 20538, 21461),
    'cloth_legs:t2': (19165, 22700, 19385, 21676),
    'cloth_legs:t3': (19165, 23070, 22700, 19385),
    'cloth_shoulder:s15': (4314, 4315, 12998, 3748),
    'cloth_shoulder:s30': (7057, 7059, 7060, 3560),
    'cloth_shoulder:s45': (10038, 10028, 10029, 10027),
    'cloth_shoulder:s60': (13867, 14139, 16980, 14112),
    'cloth_shoulder:t1': (22758, 19050, 19059, 14112),
    'cloth_shoulder:t2': (22758, 21686, 21694, 21468),
    'cloth_shoulder:t3': (22758, 22968, 22983, 21686),
    'cloth_waist:s15': (3217, 4786, 10820, 14173),
    'cloth_waist:s30': (7052, 7055, 4328, 7061),
    'cloth_waist:s45': (13856, 14143, 9636, 14286),
    'cloth_waist:s60': (18405, 19047, 20539, 10144),
    'cloth_waist:t1': (20539, 18405, 18809, 19136),
    'cloth_waist:t2': (19388, 19400, 18809, 19136),
    'cloth_waist:t3': (22730, 19388, 19400, 18809),
    'cloth_wrist:s15': (4308, 6563, 9768, 14160),
    'cloth_wrist:s30': (9846, 14221, 7437, 14416),
    'cloth_wrist:s45': (4990, 10059, 14291, 18437),
    'cloth_wrist:s60': (18263, 10136, 13958, 16370),
    'cloth_wrist:t1': (18263, 21464, 20626, 21496),
    'cloth_wrist:t2': (22655, 21604, 21611, 19374),
    'cloth_wrist:t3': (22655, 23021, 21604, 21611),
    'dagger:s15': (3848, 5540, 3490, 3184),
    'dagger:s30': (12259, 6691, 23168, 6331),
    'dagger:s45': (7947, 10703, 15245, 17752),
    'dagger:s60': (12783, 10697, 12062, 12582),
    'dagger:t1': (19166, 12783, 20578, 17070),
    'dagger:t2': (19166, 22803, 21244, 18838),
    'dagger:t3': (22802, 21126, 22804, 23044),
    'gun:s15': (4369, 4372, 4379, 2904),
    'gun:s30': (4383, 10508, 10510, 9456),
    'gun:s45': (15995, 16004, 10510, 13139),
    'gun:s60': (16007, 15325, 16992, 18460),
    'gun:t1': (18282, 16007, 17072, 19853),
    'gun:t2': (22810, 23557, 21272, 18855),
    'gun:t3': (22810, 23557, 21272, 18855),
    'leather_chest:s15': (2317, 4244, 20575, 5781),
    'leather_chest:s30': (4256, 7374, 7375, 5782),
    'leather_chest:s45': (8349, 8211, 15064, 8200),
    'leather_chest:s60': (15059, 15085, 15066, 15068),
    'leather_chest:t1': (19685, 19688, 15068, 15090),
    'leather_chest:t2': (22661, 21680, 19405, 19439),
    'leather_chest:t3': (22661, 23226, 21680, 19405),
    'leather_feet:s15': (2315, 2307, 2309, 4788),
    'leather_feet:s30': (7390, 7391, 6752, 15142),
    'leather_feet:s45': (8213, 8197, 15071, 15073),
    'leather_feet:s60': (18506, 16982, 19052, 13210),
    'leather_feet:t1': (22760, 18506, 20634, 19892),
    'leather_feet:t2': (22760, 21613, 21532, 21645),
    'leather_feet:t3': (22760, 19381, 23073, 21613),
    'leather_hands:s15': (6467, 7284, 7285, 2312),
    'leather_hands:s30': (5966, 17721, 4254, 18238),
    'leather_hands:s45': (15083, 15074, 8346, 15091),
    'leather_hands:s60': (15070, 15063, 19049, 15192),
    'leather_hands:t1': (19686, 19049, 21458, 18544),
    'leather_hands:t2': (22662, 21605, 21617, 21682),
    'leather_hands:t3': (22662, 21605, 21617, 21682),
    'leather_head:s15': (8174, 8176, 8201, 4052),
    'leather_head:s30': (8174, 8176, 8201, 4052),
    'leather_head:s45': (8348, 8214, 8345, 8201),
    'leather_head:s60': (16983, 15094, 15086, 12960),
    'leather_head:t1': (22759, 19998, 16983, 20623),
    'leather_head:t2': (22759, 21614, 21669, 21693),
    'leather_head:t3': (22759, 23829, 23020, 21614),
    'leather_legs:s15': (5958, 7282, 5961, 4242),
    'leather_legs:s30': (5963, 7373, 5962, 4054),
    'leather_legs:s45': (8212, 8202, 8193, 15054),
    'leather_legs:s60': (15062, 15095, 15087, 15060),
    'leather_legs:t1': (15062, 15095, 19877, 19889),
    'leather_legs:t2': (22701, 21698, 19877, 19889),
    'leather_legs:t3': (23071, 22701, 21698, 19877),
    'leather_shoulder:s15': (4251, 7352, 4252, 5254),
    'leather_shoulder:s30': (5964, 4252, 8192, 8210),
    'leather_shoulder:s45': (15061, 15067, 8210, 9647),
    'leather_shoulder:s60': (15055, 15058, 15096, 10228),
    'leather_shoulder:t1': (19689, 15096, 15055, 20633),
    'leather_shoulder:t2': (19389, 21665, 21474, 20633),
    'leather_shoulder:t3': (22941, 19389, 21665, 21474),
    'leather_waist:s15': (5780, 6468, 4246, 4249),
    'leather_waist:s30': (4258, 4262, 4456, 4257),
    'leather_waist:s45': (15093, 10721, 8255, 4131),
    'leather_waist:s60': (15088, 18504, 19044, 15093),
    'leather_waist:t1': (19162, 19163, 22761, 19149),
    'leather_waist:t2': (19162, 19163, 22761, 19149),
    'leather_waist:t3': (19162, 19163, 22761, 21586),
    'leather_wrist:s15': (7281, 15112, 6583, 9777),
    'leather_wrist:s30': (4259, 7378, 5783, 7386),
    'leather_wrist:s45': (15084, 15092, 8257, 15387),
    'leather_wrist:s60': (10147, 13537, 15436, 16394),
    'leather_wrist:t1': (19687, 20615, 20681, 16445),
    'leather_wrist:t2': (22663, 21602, 21491, 21708),
    'leather_wrist:t3': (22663, 21594, 21602, 21491),
    'mace_1h:s15': (2848, 3491, 5541, 3570),
    'mace_1h:s30': (3492, 5541, 5256, 7687),
    'mace_1h:s45': (7946, 7954, 7945, 12781),
    'mace_1h:s60': (12792, 12781, 12794, 22384),
    'mace_1h:t1': (19170, 12794, 22384, 21715),
    'mace_1h:t2': (19170, 19360, 22942, 21268),
    'mace_1h:t3': (19170, 23362, 23056, 21839),
    'mail_chest:s15': (6731, 2864, 2866, 6730),
    'mail_chest:s30': (3844, 7914, 7963, 2870),
    'mail_chest:s45': (8367, 15045, 15076, 12415),
    'mail_chest:s60': (15047, 15050, 20478, 20479),
    'mail_chest:t1': (22191, 20380, 19690, 12641),
    'mail_chest:t2': (22664, 22191, 20380),
    'mail_chest:t3': (22664, 22191),
    'mail_feet:s15': (6350, 3482, 5944, 6188),
    'mail_feet:s30': (7916, 3846, 3484, 4076),
    'mail_feet:s45': (8209, 13125, 14794, 8130),
    'mail_feet:s60': (16984, 12419, 19048, 8307),
    'mail_feet:t1': (19048, 16984, 20629, 20621),
    'mail_feet:t2': (21612, 21482, 21705, 20629),
    'mail_feet:t3': (21612, 21482, 21705, 20629),
    'mail_hands:s15': (3474, 3483, 3472, 6733),
    'mail_hands:s30': (7917, 3485, 8187, 6733),
    'mail_hands:s45': (20296, 8204, 8347, 15078),
    'mail_hands:s60': (12632, 20477, 20480, 12418),
    'mail_hands:t1': (19157, 22194, 19692, 20477),
    'mail_hands:t2': (22666, 19157, 22194, 21599),
    'mail_hands:t3': (22666, 19157, 22194, 21599),
    'mail_head:s15': (7915, 3836, 10542, 4077),
    'mail_head:s30': (7915, 3836, 10542, 4077),
    'mail_head:s45': (8208, 7931, 8191, 8131),
    'mail_head:s60': (12417, 12636, 15080, 8308),
    'mail_head:t1': (12636, 19875, 18546, 21804),
    'mail_head:t2': (18817, 19875, 18546, 21804),
    'mail_head:t3': (23493, 23839, 23033, 18817),
    'mail_legs:s15': (2865, 3473, 2166, 1943),
    'mail_legs:s30': (3842, 10423, 7920, 7929),
    'mail_legs:s45': (8206, 8185, 15046, 15079),
    'mail_legs:s60': (15052, 20295, 12420, 15079),
    'mail_legs:t1': (12420, 15052, 20295, 20617),
    'mail_legs:t2': (22702, 21626, 21530, 21651),
    'mail_legs:t3': (23665, 22702, 21626, 21530),
    'mail_shoulder:s15': (3480, 3481, 6189, 3231),
    'mail_shoulder:s30': (3840, 7913, 6404, 15553),
    'mail_shoulder:s45': (8207, 7932, 8133, 9965),
    'mail_shoulder:s60': (15051, 15049, 15081, 16988),
    'mail_shoulder:t1': (19691, 16988, 15081, 15051),
    'mail_shoulder:t2': (21684, 19373, 21699, 21454),
    'mail_shoulder:t3': (23664, 22967, 21684, 19373),
    'mail_waist:s15': (2857, 4697, 5328, 5425),
    'mail_waist:s30': (7107, 9869, 15571, 4717),
    'mail_waist:s45': (12416, 15082, 10081, 14793),
    'mail_waist:s60': (16989, 19043, 15082, 12634),
    'mail_waist:t1': (22195, 21463, 20215, 16464),
    'mail_waist:t2': (22195, 21607, 19393, 21463),
    'mail_waist:t3': (23663, 19380, 19393, 21463),
    'mail_wrist:s15': (2854, 2867, 2868, 3211),
    'mail_wrist:s30': (3835, 8198, 7924, 8205),
    'mail_wrist:s45': (15077, 8205, 7924, 4118),
    'mail_wrist:s60': (18508, 20476, 20481, 10156),
    'mail_wrist:t1': (18508, 20476, 20481, 18812),
    'mail_wrist:t2': (22665, 18812, 21502, 20684),
    'mail_wrist:t3': (22665, 21584, 21588, 18812),
    'neck:s15': (21934, 21933, 20442, 20444),
    'neck:s30': (20956, 20966, 20950, 20830),
    'neck:s45': (21766, 21764, 21755, 21790),
    'neck:s60': (16009, 21791, 21793, 21790),
    'neck:t1': (21793, 18205, 20622, 21809),
    'neck:t2': (21608, 18814, 21529, 21531),
    'neck:t3': (23053, 23057, 23058, 21712),
    'offhand:s15': (5183, 15971, 5611, 6341),
    'offhand:s30': (2565, 2943, 7609, 15935),
    'offhand:s45': (7557, 11859, 4125, 13030),
    'offhand:s60': (11928, 15857, 15986, 18425),
    'offhand:t1': (20582, 19142, 21471, 19922),
    'offhand:t2': (21597, 23452, 23453, 23462),
    'offhand:t3': (23048, 23049, 19366, 22937),
    'plate_chest:s15': (14895, 8157, 10775, 14821),
    'plate_chest:s30': (14895, 8157, 10775, 14821),
    'plate_chest:s45': (12405, 7939, 7935, 7930),
    'plate_chest:s60': (12422, 12618, 11604, 12613),
    'plate_chest:t1': (22196, 22762, 19693, 20550),
    'plate_chest:t2': (22669, 22196, 22762, 21652),
    'plate_chest:t3': (22669, 22196, 22762, 23363),
    'plate_feet:s15': (8160, 14896, 9289, 9387),
    'plate_feet:s30': (8160, 14896, 9289, 9387),
    'plate_feet:s45': (7936, 7933, 12409, 9637),
    'plate_feet:s60': (12611, 12426, 12409, 10376),
    'plate_feet:t1': (20039, 12611, 20619, 18806),
    'plate_feet:t2': (20039, 19387, 21688, 21481),
    'plate_feet:t3': (20039, 19387, 21688, 21481),
    'plate_hands:s15': (8158, 14897, 9287, 14826),
    'plate_hands:s30': (8158, 14897, 9287, 14826),
    'plate_hands:s45': (7919, 7927, 7938, 10129),
    'plate_hands:s60': (12631, 19057, 20549, 10380),
    'plate_hands:t1': (19164, 22763, 20549, 12631),
    'plate_hands:t2': (22670, 19164, 22763, 21623),
    'plate_hands:t3': (23482, 22670, 19164, 22763),
    'plate_head:s15': (7922, 8161, 14899, 9290),
    'plate_head:s30': (7922, 8161, 14899, 9290),
    'plate_head:s45': (7937, 7934, 12410, 7922),
    'plate_head:s60': (12633, 12427, 12612, 12640),
    'plate_head:t1': (19148, 20551, 12620, 12612),
    'plate_head:t2': (19148, 19372, 21460, 21803),
    'plate_head:t3': (23019, 19372, 21460),
    'plate_legs:s15': (14900, 8162, 14829, 9291),
    'plate_legs:s30': (14900, 8162, 14829, 9291),
    'plate_legs:s45': (7921, 7926, 10208, 8280),
    'plate_legs:s60': (12414, 17013, 22385, 12429),
    'plate_legs:t1': (19694, 12619, 12614, 12429),
    'plate_legs:t2': (22699, 21667, 19402, 21475),
    'plate_legs:t3': (23668, 23068, 22699, 21667),
    'plate_shoulder:s15': (8163, 14901, 9292, 14830),
    'plate_shoulder:s30': (8163, 14901, 9292, 14830),
    'plate_shoulder:s45': (12428, 7918, 7928, 9476),
    'plate_shoulder:s60': (12610, 11605, 12625, 13166),
    'plate_shoulder:t1': (19695, 12610, 20637, 21453),
    'plate_shoulder:t2': (21639, 21683, 19394, 20637),
    'plate_shoulder:t3': (23667, 22940, 23034, 21639),
    'plate_waist:s15': (8159, 13145, 14898, 9288),
    'plate_waist:s30': (8159, 13145, 14898, 9288),
    'plate_waist:s45': (12406, 12424, 10130, 10243),
    'plate_waist:s60': (19051, 13959, 14977, 16407),
    'plate_waist:t1': (22764, 22197, 18547, 21503),
    'plate_waist:t2': (22764, 22197, 21598, 21606),
    'plate_waist:t3': (22764, 23219, 23666, 21598),
    'plate_wrist:s15': (8156, 14903, 9285, 14832),
    'plate_wrist:s30': (8156, 14903, 9285, 14832),
    'plate_wrist:s45': (12408, 12425, 14923, 18430),
    'plate_wrist:s60': (17014, 10391, 15860, 16404),
    'plate_wrist:t1': (21457, 20616, 20687, 16469),
    'plate_wrist:t2': (22671, 21618, 21457, 20616),
    'plate_wrist:t3': (22671, 21587, 22936, 21618),
    'ring:s15': (20821, 20818, 20820, 20907),
    'ring:s30': (20958, 20959, 20960, 20833),
    'ring:s45': (21753, 21754, 21765, 21767),
    'ring:s60': (21778, 21775, 12057, 12543),
    'ring:t1': (20600, 20624, 19140, 20632),
    'ring:t2': (21601, 21200, 22707, 17063),
    'ring:t3': (21596, 21709, 23025, 23037),
    'shield:s15': (3160, 3450, 6447, 9778),
    'shield:s30': (4066, 6223, 1547, 4065),
    'shield:s45': (1979, 9958, 14912, 4129),
    'shield:s60': (10363, 10686, 13375, 14973),
    'shield:t1': (22198, 18168, 19862, 19915),
    'shield:t2': (22198, 21610, 21269, 18825),
    'shield:t3': (22198, 22819, 23043, 22818),
    'staff:s15': (1300, 4437, 5340, 1473),
    'staff:s30': (3185, 7710, 1998, 7757),
    'staff:s45': (9477, 4134, 9527, 11857),
    'staff:s60': (10698, 13372, 15278, 15854),
    'staff:t1': (21452, 20581, 18842, 17113),
    'staff:t2': (19356, 21276, 21273, 21275),
    'staff:t3': (22799, 22800, 22801, 19356),
    'sword_1h:s15': (2850, 935, 12976, 1469),
    'sword_1h:s30': (3850, 3849, 8224, 8225),
    'sword_1h:s45': (7961, 7944, 7943, 12777),
    'sword_1h:s60': (12797, 12777, 22383, 10696),
    'sword_1h:t1': (19168, 17015, 22383, 12797),
    'sword_1h:t2': (19168, 22806, 23014, 12584),
    'sword_1h:t3': (19168, 23054, 22807, 22806),
    'wand:s15': (11288, 11287, 5207, 5242),
    'wand:s30': (11290, 11289, 5213, 5818),
    'wand:s45': (10704, 13065, 9483, 11860),
    'wand:s60': (13534, 15282, 16993, 18338),
    'wand:t1': (19435, 19861, 19967, 21801),
    'wand:t2': (21603, 19367, 19435, 19861),
    'wand:t3': (22821, 22820, 21603, 19367),
}
