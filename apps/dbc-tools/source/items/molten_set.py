"""
The Molten dungeon set family (level 60 dungeon sets; designer source docs/dungeons/dungeon-loot-vanilla.md "Dungeon
sets (level 60)" and "Molten set bonuses (approved 2026-11-06)", docs/dungeons/boss-rework-systems.md section 2 Loot
lists (Molten split), blackrock-spire-rework.md and blackrock-depths-rework.md Loot): 10 archetype sets of 8 pieces,
one token per slot, and 16 vendors (four per armor type, split by tier) that trade a token for a piece. The bonus
spells are molten_set_bonuses.py, the vendor creatures source/npcs/molten_set/vendors.py. The Haunted family
(haunted_set.py) is the template: same ladder, tiers, sockets, token ids and vendor split.

**Sets.** Molten reuses the stock Tier 0.5 entries (item sets 511 to 519) for eight archetypes and adds two new tank
sets, Guardian's (Leather Tank, set 1002) and Impenetrable (Plate Tank, set 1003). Deathmist (518, the third cloth set)
retires: it is not declared here, its pieces stay as they are. Stock set to archetype:

    511 Battlegear of Heroism     Plate Strength      515 Beastmaster Armor        Mail Agility
    512 Darkmantle Armor          Leather Agility     516 Soulforge Armor          Plate Intellect
    513 Feralheart Raiment        Leather Spirit      517 Sorcerer's Regalia       Cloth Intellect
    514 Vestments of the Virtuous Cloth Spirit        519 The Five Thunders        Mail Intellect

**Item level** (blackrock-gear handoff section 5, the approved "two families per archetype at the same item level"):
the Normal tier is Rare at Haunted's Tier 0 level of the slot (head 62, chest 63, legs 61, shoulders 60, hands and feet
59, waist 58, wrist 57), not the stock Tier 0.5 levels (60 Epic / 65-66 Rare, which would sit on top of Heroic 66);
required level = item level - 5 (the stock Tier 0 rule Haunted kept). Then Heroic 66 Epic with the Heroic flag,
Molten / Draconic / Chthonic Empowered 76 / 86 / 96 (ladders.py VANILLA_DUNGEON). Every tier keeps the set's `itemset`
(the stock row's for a base= piece, `itemset=` for a new one), so every tier counts toward the set and pays the
budget's set discount (0.9). Bind on Pickup on every tier (bought with a Bind on Pickup token).

**The stock Tier 0.5 pieces were quest rewards.** The quest reward itemization (source/items/quest_rewards.lock) owns
all 72 Tier 0.5 entries, one `qr_<entry>` key each. The 64 kept here leave that lock (its header: "To hand an entry to
another declaration (a dungeon item file), delete its line first"), so the Tier 0.5 quest chain now rewards the Molten
Normal pieces (the design's "the stock Tier 0.5 quest chain loses its armor rewards; what it becomes is settled at
wave 2", scholomance-rework.md). Their item_ids.lock base lines are keyed `qr_<entry>` and the lock never hands a
stock entry to a second key, so these pieces keep that key (`_piece_key`); their minted tiers are new lines under it.

**Stats** (approved 2026-11-06). The archetype's primary (Leather Tank: Agility and extra Stamina, a quarter more) and
two of the family's three secondaries by slot; tanks swap the first stat of each pair for their avoidance (Plate Tank
Block, Leather Tank Dodge):

    head, shoulders, chest, legs   Crit/Versatility        Plate Tank Block/Versatility   Leather Tank Dodge/Versatility
    hands, wrist                   Crit/Cooldown Haste     Plate Tank Block/CDH           Leather Tank Dodge/CDH
    waist, feet                    Versatility/CDH         Plate Tank Block/CDH           Leather Tank Dodge/CDH

The waist and feet pair is the stock shape "CDH/Versatility" (an even split, so the order does not change the stats).
Block/Versatility, Block/CDH, Dodge/Versatility and Dodge/CDH are new shapes (the integration's pending itemization
SQL). Every piece also gets the budget's baseline Stamina.

**Sockets** (as Haunted: 1 socket, heads a meta plus 1, from Heroic up). The first socket is red on damage and healing
pieces, blue on tank pieces. The socket bonus is the stock +4 rating of the piece's first secondary: Crit 2874, Block
2972, Dodge 2871; Versatility has no stock enchant, so a Versatility-first piece (waist, feet) takes Crit, the
Deadmines substitute.

**Tokens** (one per slot, Bind on Pickup, never stackable; the look of the cloth and leather Desecrated tokens, the
plate ones being Haunted's). The token a boss drops is the tier of the kill; one token of a tier buys any piece of its
slot at the same tier. Blackrock Spire drops the gloves, shoulders, chestpiece and boots (Voone, Wyrmthalak,
Drakkisath, Rend and Gyth; ruling 76), Blackrock Depths the helmet, leggings, bracers and belt (the Emperor, the Ring
of Law, Incendius, Argelmach; ruling 85); the dungeons' loot stages wire them. Token `i` (Haunted's slot order) at tier
`t` is entry 70540 + 5i + t with ItemExtendedCost 3040 + 5i + t (source/ids.yaml `item_set_token`,
`item_extended_cost`).

**Vendors** (user ruling 2026-11-14): Haunted's split, four per armor type ("Normal & Heroic", "Molten Empowered",
"Draconic Empowered", "Chthonic Empowered"), 16 creatures 300670-300685, each spawned in both Ironforge and Orgrimmar
(faction 35, friendly to both; the spawn SQL is hand SQL).
"""

from lib.dsl.items import Quality, Socket, item
from lib.dsl.sets import item_set, set_token, set_vendor

from .ladders import VANILLA_DUNGEON
from .molten_set_bonuses import SET_BONUSES

R, B, M = Socket.RED, Socket.BLUE, Socket.META
BONUS_CRIT_4 = 2874
BONUS_BLOCK_4 = 2972
BONUS_DODGE_4 = 2871
EXTRA_STAMINA = 0.25  # Leather Tank: "Agility and extra Stamina" (the wave 1 tank items' quarter)
BIND_ON_PICKUP = 1
NEW_ITEM_LEVEL_GAP = 5  # required level = item level - 5 (the stock Tier 0 rows; lib/dsl/items.py's default)

# Slot order (tokens, ids, vendor lists; Haunted's): (slot key, token name, InventoryTypes, Desecrated token look).
SLOTS = (
    ("head", "Molten Helmet", (1,), 22360),
    ("shoulders", "Molten Shoulders", (3,), 22361),
    ("chest", "Molten Chestpiece", (5, 20), 22350),
    ("hands", "Molten Gloves", (10,), 22364),
    ("waist", "Molten Belt", (6,), 22363),
    ("legs", "Molten Leggings", (7,), 22359),
    ("feet", "Molten Boots", (8,), 22365),
    ("wrist", "Molten Bracers", (9,), 22362),
)
SLOT_KEYS = tuple(s[0] for s in SLOTS)
BIG_SLOTS = ("head", "shoulders", "chest", "legs")
SMALL_CRIT_SLOTS = ("hands", "wrist")
# The Normal tier's level by slot: Haunted's Tier 0 levels (haunted_set.TIER0_ILVL), the same item level per archetype.
TIER0_ILVL = {"head": 62, "shoulders": 60, "chest": 63, "hands": 59, "waist": 58, "legs": 61, "feet": 59, "wrist": 57}

TOKEN_ENTRY_BASE = 70540
TOKEN_COST_BASE = 3040
TOKEN_DESCRIPTION = "A Molten quartermaster trades it for the {noun} of your armor type's Molten set."


def _secondaries(archetype_kind: str, slot: str) -> tuple[str, int]:
    """(secondary shape, socket bonus) of an archetype kind ('dps', 'plate_tank', 'leather_tank') in a slot."""
    if archetype_kind == "plate_tank":
        return ("Block/Versatility" if slot in BIG_SLOTS else "Block/CDH"), BONUS_BLOCK_4
    if archetype_kind == "leather_tank":
        return ("Dodge/Versatility" if slot in BIG_SLOTS else "Dodge/CDH"), BONUS_DODGE_4
    if slot in BIG_SLOTS:
        return "Crit/Versatility", BONUS_CRIT_4
    if slot in SMALL_CRIT_SLOTS:
        return "Crit/CDH", BONUS_CRIT_4
    return "CDH/Versatility", BONUS_CRIT_4  # Versatility first: no stock enchant, so Crit (the Deadmines substitute)


# (set id, key prefix, archetype, primary shape, kind, stock entries by slot)
ARCHETYPES = (
    (517, "sorcerers", "Cloth Intellect", "Intellect (Solo)", "dps",
     dict(head=22065, shoulders=22068, chest=22069, hands=22066, waist=22062, legs=22067, feet=22064, wrist=22063)),
    (514, "virtuous", "Cloth Spirit", "Spirit (Solo)", "dps",
     dict(head=22080, shoulders=22082, chest=22083, hands=22081, waist=22078, legs=22085, feet=22084, wrist=22079)),
    (512, "darkmantle", "Leather Agility", "Agility (Solo)", "dps",
     dict(head=22005, shoulders=22008, chest=22009, hands=22006, waist=22002, legs=22007, feet=22003, wrist=22004)),
    (513, "feralheart", "Leather Spirit", "Spirit (Solo)", "dps",
     dict(head=22109, shoulders=22112, chest=22113, hands=22110, waist=22106, legs=22111, feet=22107, wrist=22108)),
    (515, "beastmasters", "Mail Agility", "Agility (Solo)", "dps",
     dict(head=22013, shoulders=22016, chest=22060, hands=22015, waist=22010, legs=22017, feet=22061, wrist=22011)),
    (519, "five_thunders", "Mail Intellect", "Intellect (Solo)", "dps",
     dict(head=22097, shoulders=22101, chest=22102, hands=22099, waist=22098, legs=22100, feet=22096, wrist=22095)),
    (516, "soulforge", "Plate Intellect", "Intellect (Solo)", "dps",
     dict(head=22091, shoulders=22093, chest=22089, hands=22090, waist=22086, legs=22092, feet=22087, wrist=22088)),
    (511, "heroism", "Plate Strength", "Strength (Solo)", "dps",
     dict(head=21999, shoulders=22001, chest=21997, hands=21998, waist=21994, legs=22000, feet=21995, wrist=21996)),
)

# The two new tank sets (designer names, scholomance-rework.md ruling 26; piece names proposed). Looks borrowed from
# fire-themed stock pieces no Molten or wave 1 list uses: Guardian's from the Volcanic leather set (141) and its kin,
# Impenetrable from the Dark Iron plate pieces.
NEW_SETS = (
    (1002, "guardians", "Guardian's Armor", "Leather Tank", "Agility (Solo)", "leather_tank", dict(
        head=("Guardian's Cowl", 8348), shoulders=("Guardian's Shoulderguards", 15055),
        chest=("Guardian's Chestguard", 15053), hands=("Guardian's Grips", 12464), waist=("Guardian's Belt", 15388),
        legs=("Guardian's Leggings", 15054), feet=("Guardian's Boots", 22275), wrist=("Guardian's Wristguards", 15387),
    )),
    (1003, "impenetrable", "Impenetrable Battlegear", "Plate Tank", "Strength (Solo)", "plate_tank", dict(
        head=("Impenetrable Helm", 19148), shoulders=("Impenetrable Pauldrons", 11605),
        chest=("Impenetrable Breastplate", 11604), hands=("Impenetrable Gauntlets", 12111),
        waist=("Impenetrable Girdle", 22197), legs=("Impenetrable Legplates", 17013),
        feet=("Impenetrable Sabatons", 13527), wrist=("Impenetrable Bracers", 17014),
    )),
)


def _sockets(slot: str, kind: str) -> tuple[int, ...]:
    first = B if kind != "dps" else R
    return (M, first) if slot == "head" else (first,)


def _piece_key(prefix: str, slot: str, base: int | None = None) -> str:
    """A stock Tier 0.5 piece keeps the key item_ids.lock records for its entry (`qr_<entry>`, the quest reward
    itemization's): the lock never hands a stock entry to a second key. A new piece is molten_<set>_<slot>."""
    return f"qr_{base}" if base is not None else f"molten_{prefix}_{slot}"


SET_ITEMS: dict[int, tuple[str, ...]] = {}

for _set_id, _prefix, _archetype, _primary, _kind, _stock in ARCHETYPES:
    for _slot in SLOT_KEYS:
        _secondary, _bonus = _secondaries(_kind, _slot)
        _ilvl = TIER0_ILVL[_slot]
        item(_piece_key(_prefix, _slot, _stock[_slot]), base=_stock[_slot], ilvl=_ilvl, quality=Quality.RARE,
             required_level=_ilvl - NEW_ITEM_LEVEL_GAP, primary=_primary, secondary=_secondary,
             sockets=_sockets(_slot, _kind), socket_bonus=_bonus, ladder=VANILLA_DUNGEON, bonding=BIND_ON_PICKUP)
    SET_ITEMS[_set_id] = tuple(_piece_key(_prefix, s, _stock[s]) for s in SLOT_KEYS)

for _set_id, _prefix, _set_name, _archetype, _primary, _kind, _pieces in NEW_SETS:
    for _slot in SLOT_KEYS:
        _secondary, _bonus = _secondaries(_kind, _slot)
        _name, _like = _pieces[_slot]
        _ilvl = TIER0_ILVL[_slot]
        item(_piece_key(_prefix, _slot), name=_name, like=_like, ilvl=_ilvl, quality=Quality.RARE,
             required_level=_ilvl - NEW_ITEM_LEVEL_GAP, primary=_primary, secondary=_secondary,
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
TOKEN_KEYS = tuple(f"molten_token_{s[0]}" for s in SLOTS)

for _i, (_slot, _token_name, _inv_types, _look) in enumerate(SLOTS):
    set_token(
        f"molten_token_{_slot}", name=_token_name, slots=_inv_types, ladder=VANILLA_DUNGEON, like=_look,
        ilvl=60, quality=Quality.RARE, required_level=0,
        description=TOKEN_DESCRIPTION.format(noun=_token_name.split(" ", 1)[1].lower()),
        entries={t: TOKEN_ENTRY_BASE + 5 * _i + n for n, t in enumerate(_TIERS)},
        costs={t: TOKEN_COST_BASE + 5 * _i + n for n, t in enumerate(_TIERS)},
    )

# --- Vendors (source/npcs/molten_set/vendors.py): four per armor type, split by tier ----------------------------------

ARMOR_TYPE_SETS = {"cloth": (517, 514), "leather": (512, 1002, 513), "mail": (515, 519), "plate": (511, 1003, 516)}
VENDOR_TIERS = (("normal", "heroic"), ("empowered_1",), ("empowered_2",), ("empowered_3",))
# The "Normal & Heroic" vendor of each armor type: 300670 cloth, 300671 leather, 300672 mail, 300673 plate. The
# empowered ones (Molten, Draconic, Chthonic) follow: cloth 300674-300676, leather 300677-300679, mail 300680-300682,
# plate 300683-300685 (Haunted's layout, 190 higher).
VENDOR_ENTRY_BASE = 300670
VENDORS = {}
for _n, _armor in enumerate(ARMOR_TYPE_SETS):
    VENDORS[(_armor, VENDOR_TIERS[0])] = VENDOR_ENTRY_BASE + _n
    for _k, _tiers in enumerate(VENDOR_TIERS[1:]):
        VENDORS[(_armor, _tiers)] = VENDOR_ENTRY_BASE + 4 + 3 * _n + _k

for (_armor, _tiers), _entry in VENDORS.items():
    set_vendor(_entry, sets=ARMOR_TYPE_SETS[_armor], tokens=TOKEN_KEYS, tiers=_tiers)
