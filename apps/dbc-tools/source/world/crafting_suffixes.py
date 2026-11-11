"""
Crafting rework C4: random suffix stats on crafted gear, and the Missives that choose one of them
(`.agents/plans/crafting-rework/crafting-rework.PLAN.md` "C4 rulings", DESIGN "Random stats" / "Missives").

**Suffixes.** Crafted gear carries its primaries and Stamina; its secondaries come from a random suffix, a pair of
secondary stats. The item's `item_itemization.secondary_shape_id` is 0, so its secondary budget is left unspent and
`GenerateEnchSuffixFactor` returns it as the suffix factor (ItemBudget::GetSuffixFactor, ruling A1). A suffix part
grants `AllocationPct * factor / 10000`, so a 5000/5000 pair splits the secondary budget evenly. `AllocationPct` is
5000 over the stat's budget cost (`item_stat_cost`; all nine stats cost 1.0 today, `lib/test_crafting_suffixes.py`
checks the table below against it), so a pair always spends the same budget.

  - Throughput pool 9000: the 15 pairs of Crit, Haste, Mastery, Versatility, Cooldown Haste and Proc Chance.
  - Tank pool 9001 (ruling C3): Block/Dodge, Block/Parry, Dodge/Parry, and each tank stat with Mastery and with
    Versatility (9 pairs). An item's `item_template.RandomSuffix` names its pool: the tank flag of ruling D3. A tank
    item crafted without a Missive rolls from the tank pairs only (E1).

**Missives.** Nine Inscription consumables (items 70710-70718, item_template rows in hand-written pending world SQL;
Item.dbc rows in source/items.csv). Using one applies a visible buff, "Your next crafted item gains <stat>", for 24
hours of play time (positive auras do not tick while offline; no AURA_EXPIRES_OFFLINE), kept through death
(AttributesEx3 ALLOW_AURA_WHILE_DEAD) and arena entry (AttributesEx4 ALLOW_ENTERING_ARENA). The aura's
EffectMiscValue_1 is the ItemMod stat it picks: that is the aura -> stat map the script reads
(src/server/scripts/Custom/custom_crafting_missives.cpp, bound as `spell_crafting_missive`). The script refuses a
second Missive while one is active (the item is not spent), and when the player crafts a gear piece whose pool has a
pair with that stat, sets the item's suffix to a random such pair and removes the buff. A Missive whose stat has no
pair in the item's pool (a Parry Missive on a cloth robe) stays active (ruling F1).

**Recipes.** One per Missive, learned by every Inscriptionist on skill value 1 (AcquireMethod 1: professions sit at the
cap, R2). Reagents 2 Lion's Ink + 1 Light Parchment, the Virtuoso Inking Set as the tool, like the stock scroll recipes
(Scroll of Stamina 45382 is the template for the row's flags, visual and icon). One Missive serves every tier (R13).

Ids (source/ids.yaml): enchants 5000-5008 (suffix parts), suffixes 1000-1023, pools 9000-9001, `crafting` reservation
spells 207000-207008 (buffs) and 207010-207018 (recipes), SkillLineAbility 30900-30908.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.enchants import stat_enchant, suffix, suffix_pool
from lib.dsl.registry import ItemMod, scripted_by, skill_line_ability, spell

SKILL_INSCRIPTION = 773
THROUGHPUT_POOL = 9000
TANK_POOL = 9001

# The suffix stats, in suffix order: (ItemMod, budget cost in item_stat_cost, part enchant id, display name, Missive).
SUFFIX_STATS = {
    "crit": (ItemMod.CRIT_RATING, 1.0, 5000, "Critical Strike Rating", "Critical Strike"),
    "haste": (ItemMod.HASTE_RATING, 1.0, 5001, "Haste Rating", "Haste"),
    "mastery": (ItemMod.MASTERY_RATING, 1.0, 5002, "Mastery Rating", "Mastery"),
    "versatility": (ItemMod.VERSATILITY_RATING, 1.0, 5003, "Versatility Rating", "Versatility"),
    "cooldown": (ItemMod.COOLDOWN_RATING, 1.0, 5004, "Cooldown Haste Rating", "Cooldown Haste"),
    "proc": (ItemMod.PROC_RATING, 1.0, 5005, "Proc Chance Rating", "Proc Chance"),
    "block": (ItemMod.BLOCK_RATING, 1.0, 5006, "Block Rating", "Block"),
    "dodge": (ItemMod.DODGE_RATING, 1.0, 5007, "Dodge Rating", "Dodge"),
    "parry": (ItemMod.PARRY_RATING, 1.0, 5008, "Parry Rating", "Parry"),
}
PAIR_SHARE = 5000  # each stat's share of a pair, in budget terms (ruling A1: every suffix is a 5000/5000 pair)

# (suffix id, first stat, second stat, name): the archetype names (user 2026-11-10, scheme A; no stock suffix has one).
THROUGHPUT_PAIRS = (
    (1000, "crit", "haste", "Duelist"),
    (1001, "crit", "mastery", "Assassin"),
    (1002, "crit", "versatility", "Gladiator"),
    (1003, "crit", "cooldown", "Executioner"),
    (1004, "crit", "proc", "Gambler"),
    (1005, "haste", "mastery", "Tempest"),
    (1006, "haste", "versatility", "Skirmisher"),
    (1007, "haste", "cooldown", "Zealot"),
    (1008, "haste", "proc", "Storm"),
    (1009, "mastery", "versatility", "Adept"),
    (1010, "mastery", "cooldown", "Savant"),
    (1011, "mastery", "proc", "Arcanist"),
    (1012, "versatility", "cooldown", "Wanderer"),
    (1013, "versatility", "proc", "Trickster"),
    (1014, "cooldown", "proc", "Fanatic"),
)
TANK_PAIRS = (
    (1015, "block", "dodge", "Sentinel"),
    (1016, "block", "parry", "Bulwark"),
    (1017, "dodge", "parry", "Warden"),
    (1018, "block", "mastery", "Bastion"),
    (1019, "block", "versatility", "Rampart"),
    (1020, "dodge", "mastery", "Phantom"),
    (1021, "dodge", "versatility", "Nomad"),
    (1022, "parry", "mastery", "Swordmaster"),
    (1023, "parry", "versatility", "Vanguard"),
)

# --- Suffix parts, suffixes and pools ---------------------------------------------------------------------------------

PARTS = {key: stat_enchant(row[2], row[0]) for key, row in SUFFIX_STATS.items()}


def _allocation(key: str) -> int:
    return round(PAIR_SHARE / SUFFIX_STATS[key][1])


def _pair_suffix(suffix_id: int, first: str, second: str, name: str) -> dict:
    return suffix(suffix_id, f"of the {name}", name, (PARTS[first], _allocation(first)),
                  (PARTS[second], _allocation(second)))


THROUGHPUT_SUFFIXES = [_pair_suffix(*pair) for pair in THROUGHPUT_PAIRS]
TANK_SUFFIXES = [_pair_suffix(*pair) for pair in TANK_PAIRS]
suffix_pool(THROUGHPUT_POOL, *THROUGHPUT_SUFFIXES)
suffix_pool(TANK_POOL, *TANK_SUFFIXES)

# --- Missives ---------------------------------------------------------------------------------------------------------

_TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}
_TARGET_UNIT_CASTER = 1
_ATTR0_IS_TRADESKILL = 0x00000020
_ATTR0_NOT_SHAPESHIFTED = 0x00010000
_ATTR1_NO_THREAT = 0x00000400  # the stock recipes' AttributesEx
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000
_ATTR4_ALLOW_ENTERING_ARENA = 0x00200000  # arena entry strips buffs without it
_EFFECT_CREATE_ITEM = 24
_INTERRUPT_MOVEMENT_PUSHBACK_INTERRUPT_DAMAGE = 15  # the stock recipes' InterruptFlags
_TOTEM_CATEGORY_INKING_SET = 121  # Virtuoso Inking Set (and its upgrades)
_LIONS_INK = 43116
_LIGHT_PARCHMENT = 39354
_ICON_LETTER = 2031  # INV_Letter_05, the Missive item's icon too (ItemDisplayInfo 3018)
_ICON_INSCRIPTION = 2557  # the stock scroll recipes' icon
_SV_INSCRIPTION = 10130  # the stock scroll recipes' cast visual
_DAY_MS = 24 * 60 * 60 * 1000

# (key, buff spell, recipe spell, SkillLineAbility, item entry)
MISSIVES = (
    ("crit", 207000, 207010, 30900, 70710),
    ("haste", 207001, 207011, 30901, 70711),
    ("mastery", 207002, 207012, 30902, 70712),
    ("versatility", 207003, 207013, 30903, 70713),
    ("cooldown", 207004, 207014, 30904, 70714),
    ("proc", 207005, 207015, 30905, 70715),
    ("block", 207006, 207016, 30906, 70716),
    ("dodge", 207007, 207017, 30907, 70717),
    ("parry", 207008, 207018, 30908, 70718),
)

MISSIVE_BUFFS = {}
for _key, _buff_id, _recipe_id, _sla_id, _item_entry in MISSIVES:
    _stat, _cost, _enchant, _stat_name, _missive = SUFFIX_STATS[_key]
    MISSIVE_BUFFS[_key] = spell(
        id=_buff_id, name=f"Missive of {_missive}", school=School.NORMAL, attributes=0, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=_DAY_MS,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, misc_value=int(_stat),
                        implicit_target_a=_TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_LETTER,
        notes=f'Crafting rework C4: the Missive of {_missive} buff (item {_item_entry}). EffectMiscValue_1 = ItemMod '
              f'{int(_stat)}, the stat the script gives the next crafted gear piece. 24 h of play time, kept through '
              f'death, visible (not passive, so it is saved at logout and shown).',
        raw_overrides={
            'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'CastingTimeIndex': 1,
            'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD, 'AttributesEx4': _ATTR4_ALLOW_ENTERING_ARENA,
            'Description_Lang_enUS': f'Your next crafted gear piece with random stats gains {_stat_name}, paired with '
                                     f'a random second stat. Lasts $d of play time. Only one Missive can be active '
                                     f'at a time.',
            'AuraDescription_Lang_enUS': f'Your next crafted item gains {_stat_name}.',
            **_TEXT_MASKS,
        },
    )
    scripted_by(MISSIVE_BUFFS[_key], "spell_crafting_missive")

    spell(
        id=_recipe_id, name=f"Missive of {_missive}", school=School.NORMAL,
        attributes=_ATTR0_IS_TRADESKILL | _ATTR0_NOT_SHAPESHIFTED, cast_time_ms=3000, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=_EFFECT_CREATE_ITEM, implicit_target_a=_TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_INSCRIPTION,
        notes=f'Crafting rework C4: the Inscription recipe of the Missive of {_missive} (item {_item_entry}). Row '
              f'shape copied from the stock Scroll of Stamina recipe 45382.',
        raw_overrides={
            'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'AttributesEx': _ATTR1_NO_THREAT,
            'InterruptFlags': _INTERRUPT_MOVEMENT_PUSHBACK_INTERRUPT_DAMAGE, 'ProcChance': 101,
            'EffectItemType_1': _item_entry, 'Reagent_1': _LIONS_INK, 'ReagentCount_1': 2,
            'Reagent_2': _LIGHT_PARCHMENT, 'ReagentCount_2': 1,
            'RequiredTotemCategoryID_1': _TOTEM_CATEGORY_INKING_SET, 'SpellVisualID_1': _SV_INSCRIPTION,
            'Description_Lang_enUS': '', 'AuraDescription_Lang_enUS': '', **_TEXT_MASKS,
        },
    )
    skill_line_ability(id=_sla_id, skill_line=SKILL_INSCRIPTION, spell_id=_recipe_id, min_skill_line_rank=1,
                       acquire_method=1,
                       raw_overrides={'TrivialSkillLineRankHigh': 1, 'TrivialSkillLineRankLow': 1})
