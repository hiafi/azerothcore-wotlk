"""
The Zealot's dungeon set family (the Scarlet Monastery heroic's sets; designer source docs/dungeons/
scarlet-monastery-rework.md ## Loot: Structure ruling 56, Sets ruling 57, the Zealot's family rulings 57 and 58, 3
piece bonuses ruling 59; copied into dungeon-loot-vanilla.md "Zealot's set bonuses (approved 2026-11-19)"): ten
archetype sets of 3 pieces (head, shoulders, chest), one token per slot, and four vendors (one per tier) outside the
Monastery's outer gate that trade a token for a piece. The bonus spells are zealot_set_bonuses.py, the vendor and hound
creatures source/npcs/zealot_set/.

**Heroic only** (user ruling 2026-11-19, scarlet-gear handoff section 1). The tokens drop only on heroic, so every
piece and token climbs ladders.py VANILLA_HEROIC_SET: Heroic 66 Epic with the Heroic flag, then Molten / Draconic /
Chthonic Empowered 76 / 86 / 96, no Normal tier. Every piece is a new item, the seven stock pieces the doc reuses
included: they are copies with the stock name and look (`like=`), and the stock entries stay as they are (leveling
items no list drops any more). Every tier keeps its set's `itemset` (1004-1013, ids.yaml `item_set`), so every tier
counts toward the set and pays the budget's set discount. Bind on Pickup on every tier.

**Stats** (ruling 58). The archetype's primary (Leather Tank: Agility and extra Stamina, a quarter more) and two of
Haste, Versatility and Cooldown Haste by slot; tanks swap Haste for their avoidance (Plate Tank Parry, Death Knights
carry no shield; Leather Tank Dodge), so the chest keeps Versatility/CDH:

    head        Haste/Versatility   Plate Tank Parry/Versatility (Any)   Leather Tank Dodge/Versatility
    shoulders   Haste/CDH           Plate Tank Parry/CDH (a new shape)   Leather Tank Dodge/CDH
    chest       CDH/Versatility     (every archetype)

"CDH/Versatility" is the stock even-split shape (the doc's Versatility/CDH: an even split, so the order changes
nothing). Parry/CDH has no item_shape yet (the integration's pending itemization SQL). Every piece also gets the
budget's baseline Stamina.

**Sockets** (as Haunted and Molten: 1 socket, heads a meta plus 1, on every tier; there is no Normal tier). The first
socket is red on damage and healing pieces, blue on tank pieces. The socket bonus is the stock +4 rating of the
piece's first secondary: Haste 3267, Parry 3359, Dodge 2871; the chest leads with Cooldown Haste, which has no stock
enchant, so it takes Molten's substitute, Crit 2874 (designer question).

**Type changes** the doc names: Raging Berserker's Helm and Herod's Shoulder mail to plate, Ironspine's Ribcage mail to
leather (`subclass=` and `Material=`, the stock display kept; Blackrock Depths' Deathdealer Breastplate shape).
Ironspine's Shoulderblades borrows a mail look (Bone Golem Shoulders) as leather the same way.

**Tokens** (one per slot, Bind on Pickup, never stackable; the third Naxxramas Desecrated group's look: Circlet,
Shoulderpads, Robe, the plate group being Haunted's and the second Molten's). Arcanist Doan drops the Zealot's Helm,
Herod the Zealot's Mantle, Whitemane the Zealot's Chestguard (ruling 56; the dungeon build's loot stage wires them).
The token a boss drops is the tier of the kill; one token of a tier buys any piece of its slot at the same tier.
Token `i` (head 0, shoulders 1, chest 2) at tier `t` (0 Heroic .. 3 Chthonic) is entry 70580 + 4i + t with
ItemExtendedCost 3080 + 4i + t (source/ids.yaml `item_set_token`, `item_extended_cost`).

**Vendors** (user ruling 2026-11-19): four, one per tier, each selling the 30 pieces of its tier: 300890 Heroic,
300891 Molten Empowered, 300892 Draconic Empowered, 300893 Chthonic Empowered (source/npcs/zealot_set/vendors.py),
spawned side by side outside the Monastery's outer gate in Tirisfal Glades (hand SQL, faction 35).
"""

from lib.dsl.items import Socket, item
from lib.dsl.sets import item_set, set_token, set_vendor

from .ladders import VANILLA_HEROIC_SET
from .zealot_set_bonuses import SET_BONUSES

R, B, M = Socket.RED, Socket.BLUE, Socket.META
BONUS_HASTE_4 = 3267
BONUS_PARRY_4 = 3359
BONUS_DODGE_4 = 2871
BONUS_CRIT_4 = 2874  # Molten's substitute for a stat with no stock enchant (Versatility, Cooldown Haste)
EXTRA_STAMINA = 0.25  # Leather Tank: "Agility and extra Stamina" (the wave 1 tank items' quarter)
BIND_ON_PICKUP = 1
ARMOR_SUBCLASS_LEATHER, ARMOR_SUBCLASS_PLATE = 2, 4
MATERIAL_LEATHER, MATERIAL_PLATE = 8, 6

# Slot order (tokens, ids, vendor lists): (slot key, token name, InventoryTypes, stock token look).
SLOTS = (
    ("head", "Zealot's Helm", (1,), 22367),  # Desecrated Circlet
    ("shoulders", "Zealot's Mantle", (3,), 22368),  # Desecrated Shoulderpads
    ("chest", "Zealot's Chestguard", (5, 20), 22351),  # Desecrated Robe
)
SLOT_KEYS = tuple(s[0] for s in SLOTS)
TOKEN_ENTRY_BASE = 70580
TOKEN_COST_BASE = 3080
TOKEN_DESCRIPTION = ("The Zealot's quartermasters outside the Scarlet Monastery trade it for the {noun} of any "
                     "Zealot's set.")
TOKEN_NOUNS = {"head": "helm", "shoulders": "shoulders", "chest": "chestpiece"}


def _secondaries(kind: str, slot: str) -> tuple[str, int]:
    """(secondary shape, socket bonus) of an archetype kind ('dps', 'plate_tank', 'leather_tank') in a slot."""
    if slot == "chest":
        return "CDH/Versatility", BONUS_CRIT_4  # Cooldown Haste first: no stock enchant, Molten's substitute
    if kind == "plate_tank":
        return ("Parry/Versatility (Any)" if slot == "head" else "Parry/CDH"), BONUS_PARRY_4
    if kind == "leather_tank":
        return ("Dodge/Versatility" if slot == "head" else "Dodge/CDH"), BONUS_DODGE_4
    return ("Haste/Versatility" if slot == "head" else "Haste/CDH"), BONUS_HASTE_4


def _sockets(slot: str, kind: str) -> tuple[int, ...]:
    first = R if kind == "dps" else B
    return (M, first) if slot == "head" else (first,)


# (ItemSet id, key prefix, set name, archetype, primary shape, kind, {slot: (name, like, extra columns)}), the hub's
# "Sets" table order (ItemSet 1004-1013). A stock piece the doc reuses is a copy: its stock name and `like=` its entry.
_PLATE = {"subclass": ARMOR_SUBCLASS_PLATE, "Material": MATERIAL_PLATE}
_LEATHER = {"subclass": ARMOR_SUBCLASS_LEATHER, "Material": MATERIAL_LEATHER}
ARCHETYPES = (
    (1004, "scarlet_champion", "Battlegear of the Scarlet Champion", "Plate Strength", "Strength (Solo)", "dps", dict(
        head=("Raging Berserker's Helm", 7719, _PLATE), shoulders=("Herod's Shoulder", 7718, _PLATE),
        chest=("Herod's Breastplate", 14948, {}))),  # Bloodforged Chestpiece
    (1005, "last_stand", "Bulwark of the Last Stand", "Plate Tank", "Strength (Solo)", "plate_tank", dict(
        head=("Last Stand Helm", 10168, {}), shoulders=("Last Stand Pauldrons", 10170, {}),
        chest=("Last Stand Breastplate", 10164, {}))),  # the Templar plate
    (1006, "vigil", "Vigil of the Fallen Champion", "Plate Intellect", "Intellect (Solo)", "dps", dict(
        head=("Vigilant Helm", 14979, {}), shoulders=("Vigilant Pauldrons", 14981, {}),
        chest=("Vigilant Breastplate", 14975, {}))),  # the Exalted plate
    (1007, "houndmaster", "Houndmaster's Harness", "Mail Agility", "Agility (Solo)", "dps", dict(
        head=("Houndmaster's Coif", 7456, {}), shoulders=("Houndmaster's Mantle", 7459, {}),
        chest=("Houndmaster's Hauberk", 7454, {}))),  # the Knight's mail
    (1008, "curator", "Curator's Regalia", "Mail Intellect", "Intellect (Solo)", "dps", dict(
        head=("Curator's Coif", 14804, {}), shoulders=("Curator's Mantle", 14806, {}),
        chest=("Curator's Hauberk", 14798, {}))),  # the Bloodlust mail
    (1009, "interrogator", "Interrogator's Garb", "Leather Agility", "Agility (Solo)", "dps", dict(
        head=("Interrogator's Hood", 8176, {}), shoulders=("Interrogator's Mantle", 8192, {}),
        chest=("Interrogator's Jerkin", 8175, {}))),  # the Nightscape leather
    (1010, "ironspine", "Ironspine's Bones", "Leather Tank", "Agility (Solo)", "leather_tank", dict(
        head=("Ironspine's Skull", 14539, {}),  # Bone Ring Helm
        shoulders=("Ironspine's Shoulderblades", 18686, _LEATHER),  # Bone Golem Shoulders, mail made leather
        chest=("Ironspine's Ribcage", 7688, _LEATHER))),
    (1011, "gardener", "Gardener's Vestments", "Leather Spirit", "Spirit (Solo)", "dps", dict(
        head=("Gardener's Hat", 8214, {}), shoulders=("Gardener's Mantle", 8210, {}),
        chest=("Gardener's Smock", 8211, {}))),  # the Wild Leather set
    (1012, "arcanist", "Regalia of the Arcanist", "Cloth Intellect", "Intellect (Solo)", "dps", dict(
        head=("Doan's Cowl", 12752, {}),  # Cap of the Scarlet Savant
        shoulders=("Mantle of Doan", 7712, {}), chest=("Robe of Doan", 7711, {}))),
    (1013, "high_inquisitor", "Vestments of the High Inquisitor", "Cloth Spirit", "Spirit (Solo)", "dps", dict(
        head=("Whitemane's Chapeau", 7720, {}), shoulders=("Inquisitor's Shawl", 19507, {}),
        chest=("Whitemane's Vestments", 3260, {}))),  # Scarlet Initiate Robes
)
# The seven stock pieces reused as copies (scarlet-gear handoff 1.2): stock entry -> the set and slot.
STOCK_COPIES = {7719: (1004, "head"), 7718: (1004, "shoulders"), 7688: (1010, "chest"), 7712: (1012, "shoulders"),
                7711: (1012, "chest"), 7720: (1013, "head"), 19507: (1013, "shoulders")}
TANK_KINDS = {"Plate Tank": "plate_tank", "Leather Tank": "leather_tank"}


def piece_key(prefix: str, slot: str) -> str:
    return f"zealot_{prefix}_{slot}"


SET_ITEMS: dict[int, tuple[str, ...]] = {}

for _set_id, _prefix, _set_name, _archetype, _primary, _kind, _pieces in ARCHETYPES:
    for _slot in SLOT_KEYS:
        _name, _like, _columns = _pieces[_slot]
        _secondary, _bonus = _secondaries(_kind, _slot)
        item(piece_key(_prefix, _slot), name=_name, like=_like, primary=_primary, secondary=_secondary,
             extra_stamina=EXTRA_STAMINA if _kind == "leather_tank" else 0.0,
             sockets=_sockets(_slot, _kind), socket_bonus=_bonus, ladder=VANILLA_HEROIC_SET,
             bonding=BIND_ON_PICKUP, itemset=_set_id, **_columns)
    SET_ITEMS[_set_id] = tuple(piece_key(_prefix, s) for s in SLOT_KEYS)

# --- Sets: pieces and bonuses ----------------------------------------------------------------------------------------

for _set_id, _prefix, _set_name, *_rest in ARCHETYPES:
    _two, _three = SET_BONUSES[_set_id]
    item_set(_set_id, name=_set_name, items=SET_ITEMS[_set_id], bonuses=((2, _two), (3, _three)))

# --- Tokens ----------------------------------------------------------------------------------------------------------

_TIERS = tuple(t.name for t in VANILLA_HEROIC_SET.tiers)
TOKEN_KEYS = tuple(f"zealot_token_{s[0]}" for s in SLOTS)

for _i, (_slot, _token_name, _inv_types, _look) in enumerate(SLOTS):
    set_token(
        f"zealot_token_{_slot}", name=_token_name, slots=_inv_types, ladder=VANILLA_HEROIC_SET, like=_look,
        description=TOKEN_DESCRIPTION.format(noun=TOKEN_NOUNS[_slot]),
        entries={t: TOKEN_ENTRY_BASE + 4 * _i + n for n, t in enumerate(_TIERS)},
        costs={t: TOKEN_COST_BASE + 4 * _i + n for n, t in enumerate(_TIERS)},
    )

# --- Vendors (source/npcs/zealot_set/vendors.py): one per tier, each selling the 30 pieces of its tier ---------------

VENDOR_ENTRY_BASE = 300890
VENDORS = {_tier: VENDOR_ENTRY_BASE + _n for _n, _tier in enumerate(_TIERS)}

for _tier, _entry in VENDORS.items():
    set_vendor(_entry, sets=tuple(s[0] for s in ARCHETYPES), tokens=TOKEN_KEYS, tiers=(_tier,))
