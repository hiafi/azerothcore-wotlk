"""
The Haunted dungeon set family (level 60 dungeon sets; designer source docs/dungeons/dungeon-loot-vanilla.md "Dungeon
sets (level 60)" and "Haunted set bonuses (approved 2026-11-06)", docs/dungeons/boss-rework-systems.md section 2 Loot
lists, scholomance-rework.md and stratholme-rework.md Loot): 10 archetype sets of 8 pieces, one token per slot, and
four vendors (one per armor type) that trade a token for a piece. The bonus spells are haunted_set_bonuses.py, the
vendor creatures source/npcs/haunted_set/vendors.py.

**Sets.** Haunted reuses the stock Tier 0 entries (item sets 181 to 189, item level 57 to 63) for eight archetypes and
adds two new tank sets, Protector's (Leather Tank, set 1000) and Shadowguard (Plate Tank, set 1001). Dreadmist (183,
the third cloth set) retires: it is not declared here, its pieces stay stock. Every piece climbs the vanilla dungeon
ladder (ladders.py): Normal is the stock Rare row at its stock level (a new piece takes the Tier 0 level of its slot),
Heroic 66 Epic with the Heroic flag, then Molten / Draconic / Chthonic Empowered 76 / 86 / 96. Every tier keeps the
set's `itemset`, so every tier counts toward the set (the server counts worn pieces by `item_template.itemset`) and
pays the budget's set discount (0.9) for its bonus. Pieces are Bind on Pickup on every tier (the stock belts, bracers
and gloves were Bind on Equip): they come from a vendor for a Bind on Pickup token.

**Stats** (approved 2026-11-06). The archetype's primary (Leather Tank: Agility and extra Stamina, a quarter more, the
wave 1 tank pick) and two of the family's three secondaries by slot; tanks swap the first stat of each pair for their
avoidance (Plate Tank Parry, Leather Tank Dodge):

    head, shoulders, chest, legs   Haste/Mastery    Plate Tank Parry/Mastery    Leather Tank Dodge/Mastery
    hands, wrist                   Haste/Proc       Plate Tank Parry/Proc       Leather Tank Dodge/Proc
    waist, feet                    Mastery/Proc     Plate Tank Parry/Proc       Leather Tank Dodge/Proc

Mastery/Proc, Parry/Mastery, Parry/Proc and Dodge/Proc are new shapes (75-78, the Haunted pending itemization SQL).
Every piece also gets the budget's baseline Stamina.

**Sockets** (boss-rework-systems section 2: set pieces carry 1 socket, heads a meta plus 1; from Heroic up, the
Normal tier has none, user 2026-11-06). The first socket is red on damage and healing pieces, blue on tank pieces.
The socket bonus is the stock +4 rating of the piece's first secondary (Haste 3267, Parry 3359, Dodge 2871); Mastery
has no stock enchant, so a Mastery-first piece takes Haste, as in the wave 1 dungeon lists.

**Tokens** (one per slot, Bind on Pickup, never stackable like the stock tier tokens; the look of the Naxxramas
Desecrated tokens). Each token climbs the same ladder as the pieces: the token a boss drops is the tier of the kill
(a Normal kill drops the Normal token, a Heroic kill the Heroic token, an empowered kill the empowered one), and one
token of a tier buys any piece of its slot at the same tier. Scholomance drops the helmet, shoulders, gloves and belt,
Stratholme the chestpiece, leggings, bracers and boots (the boss loot tables are the dungeons' loot stage, not here).
Ids are explicit and never move: token `i` (the slot order below) at tier `t` (ladder order) is entry
70500 + 5i + t with ItemExtendedCost 3000 + 5i + t (source/ids.yaml `item_set_token`, `item_extended_cost`).

**Vendors** (user rulings 2026-11-06): four per armor type, split by tier, in Darnassus for the Alliance (Horde spots
to come: the same creatures, new spawns only). Each trades the tokens for its armor type's archetype pieces of its
tiers only: "Normal & Heroic" (both tiers: cloth and mail 32 rows, leather and plate 48), "Molten Empowered",
"Draconic Empowered" and "Chthonic Empowered" (16 or 24 rows each). 16 creatures, 300480-300495.
"""

from lib.dsl.items import Quality, Socket, item
from lib.dsl.sets import item_set, set_token, set_vendor

from .haunted_set_bonuses import SET_BONUSES
from .ladders import VANILLA_DUNGEON

R, B, M = Socket.RED, Socket.BLUE, Socket.META
BONUS_HASTE_4 = 3267
BONUS_PARRY_4 = 3359
BONUS_DODGE_4 = 2871
EXTRA_STAMINA = 0.25  # Leather Tank: "Agility and extra Stamina" (the wave 1 tank items' quarter)
BIND_ON_PICKUP = 1

# Slot order (tokens, ids, vendor lists): (slot key, token name, InventoryTypes, stock Desecrated token look).
SLOTS = (
    ("head", "Haunted Helmet", (1,), 22353),
    ("shoulders", "Haunted Shoulders", (3,), 22354),
    ("chest", "Haunted Chestpiece", (5, 20), 22349),
    ("hands", "Haunted Gloves", (10,), 22357),
    ("waist", "Haunted Belt", (6,), 22356),
    ("legs", "Haunted Leggings", (7,), 22352),
    ("feet", "Haunted Boots", (8,), 22358),
    ("wrist", "Haunted Bracers", (9,), 22355),
)
SLOT_KEYS = tuple(s[0] for s in SLOTS)
BIG_SLOTS = ("head", "shoulders", "chest", "legs")
SMALL_HASTE_SLOTS = ("hands", "wrist")
# The Tier 0 item level of each slot, for the new tank pieces (stock: head 62, chest 63, legs 61, shoulders 60, hands
# and feet 59, waist 58, wrist 57).
TIER0_ILVL = {"head": 62, "shoulders": 60, "chest": 63, "hands": 59, "waist": 58, "legs": 61, "feet": 59, "wrist": 57}

TOKEN_ENTRY_BASE = 70500
TOKEN_COST_BASE = 3000
TOKEN_DESCRIPTION = "A Haunted quartermaster trades it for the {noun} of your armor type's Haunted set."


def _secondaries(archetype_kind: str, slot: str) -> tuple[str, int]:
    """(secondary shape, socket bonus) of an archetype kind ('dps', 'plate_tank', 'leather_tank') in a slot."""
    if archetype_kind == "plate_tank":
        return ("Parry/Mastery" if slot in BIG_SLOTS else "Parry/Proc"), BONUS_PARRY_4
    if archetype_kind == "leather_tank":
        return ("Dodge/Mastery" if slot in BIG_SLOTS else "Dodge/Proc"), BONUS_DODGE_4
    if slot in BIG_SLOTS:
        return "Haste/Mastery", BONUS_HASTE_4
    if slot in SMALL_HASTE_SLOTS:
        return "Haste/Proc", BONUS_HASTE_4
    return "Mastery/Proc", BONUS_HASTE_4  # Mastery has no stock socket bonus: Haste, as in the wave 1 lists


# (set id, key prefix, archetype, primary shape, kind, stock entries by slot or None, new pieces {slot: (name, like)})
ARCHETYPES = (
    (181, "magisters", "Cloth Intellect", "Intellect (Solo)", "dps",
     dict(head=16686, shoulders=16689, chest=16688, hands=16684, waist=16685, legs=16687, feet=16682, wrist=16683)),
    (182, "devout", "Cloth Spirit", "Spirit (Solo)", "dps",
     dict(head=16693, shoulders=16695, chest=16690, hands=16692, waist=16696, legs=16694, feet=16691, wrist=16697)),
    (184, "shadowcraft", "Leather Agility", "Agility (Solo)", "dps",
     dict(head=16707, shoulders=16708, chest=16721, hands=16712, waist=16713, legs=16709, feet=16711, wrist=16710)),
    (185, "wildheart", "Leather Spirit", "Spirit (Solo)", "dps",
     dict(head=16720, shoulders=16718, chest=16706, hands=16717, waist=16716, legs=16719, feet=16715, wrist=16714)),
    (186, "beaststalkers", "Mail Agility", "Agility (Solo)", "dps",
     dict(head=16677, shoulders=16679, chest=16674, hands=16676, waist=16680, legs=16678, feet=16675, wrist=16681)),
    (187, "elements", "Mail Intellect", "Intellect (Solo)", "dps",
     dict(head=16667, shoulders=16669, chest=16666, hands=16672, waist=16673, legs=16668, feet=16670, wrist=16671)),
    (188, "lightforge", "Plate Intellect", "Intellect (Solo)", "dps",
     dict(head=16727, shoulders=16729, chest=16726, hands=16724, waist=16723, legs=16728, feet=16725, wrist=16722)),
    (189, "valor", "Plate Strength", "Strength (Solo)", "dps",
     dict(head=16731, shoulders=16733, chest=16730, hands=16737, waist=16736, legs=16732, feet=16734, wrist=16735)),
)

# The two new tank sets (designer names, scholomance-rework.md ruling 26; piece names proposed). Looks borrowed from
# stock sets no wave 1 list uses: Protector's from the Alliance rank 10 Dragonhide set (381) plus its girdle and
# armsplints, Shadowguard from Imperial Plate (321) plus Boneclenched Gauntlets (the Scholomance gauntlets cut for
# the token slots).
NEW_SETS = (
    (1000, "protectors", "Protector's Armor", "Leather Tank", "Agility (Solo)", "leather_tank", dict(
        head=("Protector's Cowl", 16424), shoulders=("Protector's Spaulders", 16423), chest=("Protector's Vest", 16421),
        hands=("Protector's Handguards", 16397), waist=("Protector's Belt", 16399),
        legs=("Protector's Leggings", 16422), feet=("Protector's Boots", 16393), wrist=("Protector's Bracers", 16395),
    )),
    (1001, "shadowguard", "Shadowguard Battlegear", "Plate Tank", "Strength (Solo)", "plate_tank", dict(
        head=("Shadowguard Helm", 12427), shoulders=("Shadowguard Pauldrons", 12428),
        chest=("Shadowguard Breastplate", 12422), hands=("Shadowguard Gauntlets", 14525),
        waist=("Shadowguard Girdle", 12424), legs=("Shadowguard Legplates", 12429),
        feet=("Shadowguard Sabatons", 12426), wrist=("Shadowguard Bracers", 12425),
    )),
)


def _sockets(slot: str, kind: str) -> tuple[int, ...]:
    first = B if kind != "dps" else R
    return (M, first) if slot == "head" else (first,)


def _piece_key(prefix: str, slot: str) -> str:
    return f"haunted_{prefix}_{slot}"


SET_ITEMS: dict[int, tuple[str, ...]] = {}

for _set_id, _prefix, _archetype, _primary, _kind, _stock in ARCHETYPES:
    for _slot in SLOT_KEYS:
        _secondary, _bonus = _secondaries(_kind, _slot)
        item(_piece_key(_prefix, _slot), base=_stock[_slot], primary=_primary, secondary=_secondary,
             sockets=_sockets(_slot, _kind), socket_bonus=_bonus, ladder=VANILLA_DUNGEON, bonding=BIND_ON_PICKUP)
    SET_ITEMS[_set_id] = tuple(_piece_key(_prefix, s) for s in SLOT_KEYS)

for _set_id, _prefix, _set_name, _archetype, _primary, _kind, _pieces in NEW_SETS:
    for _slot in SLOT_KEYS:
        _secondary, _bonus = _secondaries(_kind, _slot)
        _name, _like = _pieces[_slot]
        item(_piece_key(_prefix, _slot), name=_name, like=_like, ilvl=TIER0_ILVL[_slot], quality=Quality.RARE,
             primary=_primary, secondary=_secondary,
             extra_stamina=EXTRA_STAMINA if _kind == "leather_tank" else 0.0,
             sockets=_sockets(_slot, _kind), socket_bonus=_bonus, ladder=VANILLA_DUNGEON,
             bonding=BIND_ON_PICKUP, itemset=_set_id)
    SET_ITEMS[_set_id] = tuple(_piece_key(_prefix, s) for s in SLOT_KEYS)

# --- Sets: pieces and bonuses ----------------------------------------------------------------------------------------

for _set_id, _ in sorted(SET_ITEMS.items()):
    _three, _five = SET_BONUSES[_set_id]
    _name = next((n for s, _p, n, *_rest in NEW_SETS if s == _set_id), None)
    item_set(_set_id, name=_name, items=SET_ITEMS[_set_id], bonuses=((3, _three), (5, _five)))

# --- Tokens ----------------------------------------------------------------------------------------------------------

_TIERS = tuple(t.name for t in VANILLA_DUNGEON.tiers)
TOKEN_KEYS = tuple(f"haunted_token_{s[0]}" for s in SLOTS)

for _i, (_slot, _token_name, _inv_types, _look) in enumerate(SLOTS):
    set_token(
        f"haunted_token_{_slot}", name=_token_name, slots=_inv_types, ladder=VANILLA_DUNGEON, like=_look,
        ilvl=60, quality=Quality.RARE, required_level=0,
        description=TOKEN_DESCRIPTION.format(noun=_token_name.split(" ", 1)[1].lower()),
        entries={t: TOKEN_ENTRY_BASE + 5 * _i + n for n, t in enumerate(_TIERS)},
        costs={t: TOKEN_COST_BASE + 5 * _i + n for n, t in enumerate(_TIERS)},
    )

# --- Vendors (source/npcs/haunted_set/vendors.py): four per armor type, split by tier ---------------------------------

ARMOR_TYPE_SETS = {"cloth": (181, 182), "leather": (184, 1000, 185), "mail": (186, 187), "plate": (189, 1001, 188)}
VENDOR_TIERS = (("normal", "heroic"), ("empowered_1",), ("empowered_2",), ("empowered_3",))
# The "Normal & Heroic" vendor of each armor type stands on the user's spot: 300480 cloth, 300481 leather, 300482 mail,
# 300483 plate. The empowered ones (Molten, Draconic, Chthonic) follow: cloth 300484-300486, leather 300487-300489,
# mail 300490-300492, plate 300493-300495.
VENDORS = {}
for _n, _armor in enumerate(ARMOR_TYPE_SETS):
    VENDORS[(_armor, VENDOR_TIERS[0])] = 300480 + _n
    for _k, _tiers in enumerate(VENDOR_TIERS[1:]):
        VENDORS[(_armor, _tiers)] = 300484 + 3 * _n + _k

for (_armor, _tiers), _entry in VENDORS.items():
    set_vendor(_entry, sets=ARMOR_TYPE_SETS[_armor], tokens=TOKEN_KEYS, tiers=_tiers)
