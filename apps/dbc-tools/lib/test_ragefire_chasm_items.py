"""
The Ragefire Chasm boss list items (wave 4 dungeon items): source/items/ragefire_chasm.py.

Checks:
  - the list: 25 items on the dungeon ladder, keys `rfc_`, one declaration per stock entry (6 `base=` items), the four
    bosses' counts (6, 6, 6, 7) and the new items' level (18, required level 13 by default);
  - the doc's stats: each item's primary and secondaries are exactly the stats docs/dungeons/ragefire-chasm-rework.md
    ## Loot "Final list" names for it (Stamina is everywhere, so it is left out); when the loot copy
    docs/dungeons/dungeon-loot-vanilla.md "### Ragefire Chasm" is present, the same table is parsed and compared too
    (its Type and Slot columns included);
  - the doc's type and slot: the look donor (`like=`) or the stock entry (`base=`) has the class, subclass and
    InventoryType the doc names, and no declaration overrides one (the Scarlet Monastery gear review's M1);
  - every shape the list names exists (no pending shape is needed);
  - the ring carries secondaries only, the socket picks (trinkets, jewelry and Normal tiers never), Normal tiers Rare,
    new items Bind on Pickup with a look, the stock entries' type and slot unchanged, the kept effect (Cursed
    Felblade's Cripple) and no other declared effect, the declared multiplier, the Leather Tank head's extra Stamina;
  - the materialized rows: every doc stat has a point on every tier (the Blackrock gear review's S3).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_items.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl.items import NULL_PRIMARY_SHAPE, Quality, Socket  # noqa: E402
from lib.test_hard_mode_item_effects import (  # noqa: E402
    _load_items_registry, materialized_tier_stats,
)

R, Y, B = Socket.RED, Socket.YELLOW, Socket.BLUE

LEVEL = 18  # every stock rare of the dungeon (live item_template, 2026-11-24); required level 13

# key -> (boss, stock entry or None for a new item, the doc's stats in the doc's order).
LIST = {
    "rfc_chieftains_rockplate_pauldrons": ("Oggleflint", None, "Str Parry Vers"),
    "rfc_borer_chased_treads": ("Oggleflint", None, "Agi Haste Crit"),
    "rfc_tunnelers_hide_cap": ("Oggleflint", None, "Agi Dodge Vers"),
    "rfc_oggleflints_skullthumper": ("Oggleflint", None, "Str Crit"),
    "rfc_ring_of_the_cleft": ("Oggleflint", None, "Haste Crit"),
    "rfc_eye_of_the_earthborer": ("Oggleflint", None, "Agi Crit Mastery"),
    "rfc_robe_of_evocation": ("Jergosh", 14150, "Int Crit Mastery"),
    "rfc_cavedweller_bracers": ("Jergosh", 14147, "Int Haste Vers"),
    "rfc_chanting_blade": ("Jergosh", 14151, "Int Haste"),
    "rfc_searing_blade_ritual_leggings": ("Jergosh", None, "Int Haste Mastery"),
    "rfc_invokers_staff_of_embers": ("Jergosh", None, "Spi Haste Crit Mastery"),
    "rfc_shard_of_the_blood_filled_orb": ("Jergosh", None, "Spi Haste Vers"),
    "rfc_cleft_of_shadow_grips": ("Bazzalan", None, "Agi Crit Haste"),
    "rfc_satyrs_kris": ("Bazzalan", None, "Agi Crit"),
    "rfc_satyrhide_mantle": ("Bazzalan", None, "Int Crit Vers"),
    "rfc_felhoof_kilt": ("Bazzalan", None, "Int Mastery Crit"),
    "rfc_shadowstep_slippers": ("Bazzalan", None, "Int Haste Crit"),
    "rfc_idol_of_the_corrupted_grove": ("Bazzalan", None, "Int Crit Haste"),
    "rfc_crystalline_cuffs": ("Taragaman", 14148, "Spi Crit Haste"),
    "rfc_subterranean_cape": ("Taragaman", 14149, "Str Crit Vers"),
    "rfc_cursed_felblade": ("Taragaman", 14145, "Str Parry"),
    "rfc_hungerers_legplates": ("Taragaman", None, "Str Crit Haste Mastery"),
    "rfc_crested_helm_of_the_beast": ("Taragaman", None, "Int Haste Vers"),
    "rfc_libram_of_the_hungerer": ("Taragaman", None, "Str Crit Mastery"),
    "rfc_searing_blade_talisman": ("Taragaman", None, "Int Crit Haste"),
}
# key -> the doc's item name (every row of the doc's Final list, in the doc's spelling).
NAMES = {
    "rfc_chieftains_rockplate_pauldrons": "Chieftain's Rockplate Pauldrons",
    "rfc_borer_chased_treads": "Borer-chased Treads",
    "rfc_tunnelers_hide_cap": "Tunneler's Hide Cap",
    "rfc_oggleflints_skullthumper": "Oggleflint's Skullthumper",
    "rfc_ring_of_the_cleft": "Ring of the Cleft",
    "rfc_eye_of_the_earthborer": "Eye of the Earthborer",
    "rfc_robe_of_evocation": "Robe of Evocation",
    "rfc_cavedweller_bracers": "Cavedweller Bracers",
    "rfc_chanting_blade": "Chanting Blade",
    "rfc_searing_blade_ritual_leggings": "Searing Blade Ritual Leggings",
    "rfc_invokers_staff_of_embers": "Invoker's Staff of Embers",
    "rfc_shard_of_the_blood_filled_orb": "Shard of the Blood Filled Orb",
    "rfc_cleft_of_shadow_grips": "Cleft of Shadow Grips",
    "rfc_satyrs_kris": "Satyr's Kris",
    "rfc_satyrhide_mantle": "Satyrhide Mantle",
    "rfc_felhoof_kilt": "Felhoof Kilt",
    "rfc_shadowstep_slippers": "Shadowstep Slippers",
    "rfc_idol_of_the_corrupted_grove": "Idol of the Corrupted Grove",
    "rfc_crystalline_cuffs": "Crystalline Cuffs",
    "rfc_subterranean_cape": "Subterranean Cape",
    "rfc_cursed_felblade": "Cursed Felblade",
    "rfc_hungerers_legplates": "Hungerer's Legplates",
    "rfc_crested_helm_of_the_beast": "Crested Helm of the Beast",
    "rfc_libram_of_the_hungerer": "Libram of the Hungerer",
    "rfc_searing_blade_talisman": "Searing Blade Talisman",
}
# The doc's (Type, Slot) -> item_template (class, subclass, InventoryType) values it allows.
DOC_TYPES = {
    ("Plate", "Head"): (4, 4, 1), ("Plate", "Shoulder"): (4, 4, 3), ("Plate", "Legs"): (4, 4, 7),
    ("Mail", "Legs"): (4, 3, 7), ("Mail", "Feet"): (4, 3, 8), ("Mail", "Wrist"): (4, 3, 9),
    ("Leather", "Head"): (4, 2, 1), ("Leather", "Shoulder"): (4, 2, 3), ("Leather", "Legs"): (4, 2, 7),
    ("Leather", "Hands"): (4, 2, 10),
    ("Cloth", "Chest"): (4, 1, 20), ("Cloth", "Feet"): (4, 1, 8), ("Cloth", "Wrist"): (4, 1, 9),
    ("Cloak", "Back"): (4, 1, 16), ("Ring", "Finger"): (4, 0, 11), ("Trinket", "Trinket"): (4, 0, 12),
    ("Mace", "One-hand"): (2, 4, 13), ("Sword", "One-hand"): (2, 7, 13), ("Dagger", "One-hand"): (2, 15, 13),
    ("Staff", "Two-hand"): (2, 10, 17), ("Libram", "Relic"): (4, 7, 28), ("Idol", "Relic"): (4, 8, 28),
}
# key -> the doc's (Type, Slot) (the loot copy says "Relic" for both relics; the dungeon doc names the kind).
TYPES = {
    "rfc_chieftains_rockplate_pauldrons": ("Plate", "Shoulder"),
    "rfc_borer_chased_treads": ("Mail", "Feet"),
    "rfc_tunnelers_hide_cap": ("Leather", "Head"),
    "rfc_oggleflints_skullthumper": ("Mace", "One-hand"),
    "rfc_ring_of_the_cleft": ("Ring", "Finger"),
    "rfc_eye_of_the_earthborer": ("Trinket", "Trinket"),
    "rfc_robe_of_evocation": ("Cloth", "Chest"),
    "rfc_cavedweller_bracers": ("Mail", "Wrist"),
    "rfc_chanting_blade": ("Dagger", "One-hand"),
    "rfc_searing_blade_ritual_leggings": ("Leather", "Legs"),
    "rfc_invokers_staff_of_embers": ("Staff", "Two-hand"),
    "rfc_shard_of_the_blood_filled_orb": ("Trinket", "Trinket"),
    "rfc_cleft_of_shadow_grips": ("Leather", "Hands"),
    "rfc_satyrs_kris": ("Dagger", "One-hand"),
    "rfc_satyrhide_mantle": ("Leather", "Shoulder"),
    "rfc_felhoof_kilt": ("Mail", "Legs"),
    "rfc_shadowstep_slippers": ("Cloth", "Feet"),
    "rfc_idol_of_the_corrupted_grove": ("Idol", "Relic"),
    "rfc_crystalline_cuffs": ("Cloth", "Wrist"),
    "rfc_subterranean_cape": ("Cloak", "Back"),
    "rfc_cursed_felblade": ("Sword", "One-hand"),
    "rfc_hungerers_legplates": ("Plate", "Legs"),
    "rfc_crested_helm_of_the_beast": ("Plate", "Head"),
    "rfc_libram_of_the_hungerer": ("Libram", "Relic"),
    "rfc_searing_blade_talisman": ("Trinket", "Trinket"),
}
BOSS_COUNT = {"Oggleflint": 6, "Jergosh": 6, "Bazzalan": 6, "Taragaman": 7}
# The doc's Boss column spelling -> this file's boss keys.
DOC_BOSS = {"Oggleflint": "Oggleflint", "Jergosh the Invoker": "Jergosh", "Bazzalan": "Bazzalan",
            "Taragaman the Hungerer": "Taragaman"}
STAT_NAMES = {"Str": "Strength", "Agi": "Agility", "Int": "Intellect", "Spi": "Spirit", "Crit": "Crit",
              "Haste": "Haste", "Mastery": "Mastery", "Vers": "Versatility", "CDH": "CDH", "Proc": "Proc",
              "Dodge": "Dodge", "Parry": "Parry", "Block": "Block"}
PRIMARIES = {"Strength", "Agility", "Intellect", "Spirit"}

# The six stock entries keep their stock row (item level 18, required level 13) as the Normal tier.
STOCK_ENTRIES = {14150, 14147, 14151, 14148, 14149, 14145}

# One socketed standalone piece per boss (the doc names none: designer question). The first socket is red, blue on
# tank gear; the bonuses are stock +4 ratings (2874 Crit, 3267 Haste, 3359 Parry).
SOCKETS = {
    "rfc_chieftains_rockplate_pauldrons": (B,),   # Oggleflint, Plate Tank
    "rfc_searing_blade_ritual_leggings": (R,),    # Jergosh
    "rfc_cleft_of_shadow_grips": (R,),            # Bazzalan
    "rfc_hungerers_legplates": (R,),              # Taragaman
}
BONUS = {
    "rfc_chieftains_rockplate_pauldrons": 3359, "rfc_searing_blade_ritual_leggings": 3267,
    "rfc_cleft_of_shadow_grips": 2874, "rfc_hungerers_legplates": 2874,
}
TRINKETS = {"rfc_eye_of_the_earthborer", "rfc_shard_of_the_blood_filled_orb", "rfc_searing_blade_talisman"}
RELICS = {"rfc_libram_of_the_hungerer", "rfc_idol_of_the_corrupted_grove"}
# The ring: secondaries only.
JEWELRY = {"rfc_ring_of_the_cleft"}
KEPT_EFFECTS = {"rfc_cursed_felblade"}  # Cripple 18381, Chance on hit (stock slot 1)
# Caster main-hand dagger (the stock level is below 60): the 60-100 physical cell on every tier.
DECLARED_MULTS = {"rfc_chanting_blade": 0.445}


def stat_names(decl) -> set[str]:
    """The stats a declaration's shapes name, as the doc spells them (Stamina left out)."""
    names = set()
    for shape in (decl.primary, decl.secondary):
        if shape is None or shape == NULL_PRIMARY_SHAPE:
            continue
        for part in shape.replace(" (Solo)", "").replace(" (Any)", "").split("/"):
            names.add(part.strip())
    return names


def _doc_rows(path: Path, header_re: str, stop_re: str) -> dict[str, tuple[str, str]]:
    """{item name: (doc boss, stats cell)} of the markdown table that follows the header line."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if re.match(header_re, line))
    rows = {}
    for line in lines[start + 1:]:
        if re.match(stop_re, line):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or cells[0] in ("Slot", "Boss", "Item") or set(cells[0]) <= {"-", " "}:
            continue
        rows[cells[0], cells[1]] = cells
    return rows


class RagefireChasmItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations
                     if e["id"].startswith("rfc_") and e["_decl"].ladder.name == "vanilla_dungeon"}

    # --- the list ------------------------------------------------------------------------------------------------

    def test_the_list(self):
        self.assertEqual(set(self.decls), set(LIST))
        self.assertEqual(set(self.decls), set(NAMES))
        self.assertEqual(len(self.decls), 25)
        counts = {}
        for boss, _, _ in LIST.values():
            counts[boss] = counts.get(boss, 0) + 1
        self.assertEqual(counts, BOSS_COUNT)
        bases = [d.base for d in self.decls.values() if d.base is not None]
        self.assertEqual(len(bases), len(set(bases)))  # one declaration per stock entry
        self.assertEqual(set(bases), STOCK_ENTRIES)
        self.assertEqual(set(bases), {stock for _, stock, _ in LIST.values() if stock is not None})
        self.assertEqual(len(bases), 6)
        for key, decl in self.decls.items():
            self.assertEqual(decl.ladder.name, "vanilla_dungeon", key)
            self.assertEqual(decl.base, LIST[key][1], key)

    def test_the_doc_stats(self):
        for key, (_, _, stats) in LIST.items():
            wanted = {STAT_NAMES[s] for s in stats.split()}
            self.assertEqual(stat_names(self.decls[key]), wanted, key)
            decl = self.decls[key]
            # a primary shape names exactly one primary; a secondary shape only secondaries
            if decl.primary is not None:
                self.assertEqual(len(stat_names(decl) & PRIMARIES), 1, key)
            self.assertFalse(
                set(decl.secondary.replace(" (Solo)", "").replace(" (Any)", "").split("/")) & PRIMARIES, key)

    def test_the_doc_table_when_present(self):
        """The dungeon-loot copy of the doc's table, parsed: names, boss and stats equal this file's tables. The
        docs/ checkout is a nested private repo and may be absent (CI), so a missing file is a skip."""
        path = REPO_ROOT / "docs" / "dungeons" / "dungeon-loot-vanilla.md"
        if not path.is_file():
            self.skipTest("docs/dungeons/dungeon-loot-vanilla.md is not checked out here")
        rows = _doc_rows(path, r"^### Ragefire Chasm\s*$", r"^\*\*Hard mode|^### ")
        by_name = {key: NAMES[key] for key in NAMES}
        parsed = {}
        for cells in rows.values():
            boss, item, call, kind, slot, stats = cells[:6]
            parsed[item.strip("*")] = (DOC_BOSS[boss], call, kind, slot, stats)
        self.assertEqual(set(parsed), set(by_name.values()))
        for key, name in by_name.items():
            boss, call, kind, slot, stats = parsed[name]
            self.assertEqual(boss, LIST[key][0], key)
            self.assertEqual(call == "Alter", LIST[key][1] is not None, key)
            wanted_kind, wanted_slot = TYPES[key]
            self.assertEqual((kind, slot), ("Relic" if wanted_slot == "Relic" else wanted_kind, wanted_slot), key)
            wanted = {STAT_NAMES[s] for s in LIST[key][2].split()}
            got = {s.strip() for s in stats.split(";")[0].split(",")}
            self.assertEqual(got, wanted, key)

    def test_type_and_slot(self):
        """like= and base= bring class, subclass and InventoryType: every donor or stock row is of the doc's type."""
        self.assertEqual(set(TYPES), set(LIST))
        rows = id_blocks.spell_tables.load_live_item_template_rows()
        for key, decl in self.decls.items():
            row = rows[decl.base if decl.base is not None else decl.like]
            got = (int(row["class"]), int(row["subclass"]), int(row["InventoryType"]))
            self.assertEqual(got, DOC_TYPES[TYPES[key]], key)
            self.assertFalse({"class", "subclass", "InventoryType"} & set(dict(decl.columns)), key)

    def test_new_items(self):
        for key, decl in self.decls.items():
            if decl.base is not None:
                continue
            self.assertEqual(dict(decl.columns).get("bonding"), 1, key)  # a new boss item binds on pickup
            self.assertIsNotNone(decl.like, key)
            self.assertEqual(decl.name, NAMES[key], key)
            self.assertEqual(decl.ilvl, LEVEL, key)  # every stock rare of the dungeon is item level 18
            self.assertIsNone(decl.required_level, key)  # defaults to the item level - 5 (13, the stock value)
            self.assertIn(decl.quality, (None, Quality.RARE), key)

    def test_stock_levels(self):
        """A stock item keeps its stock level, required level and quality (all 18 / 13 / Rare live)."""
        for key, decl in self.decls.items():
            if decl.base is None:
                continue
            self.assertIsNone(decl.ilvl, key)
            self.assertIsNone(decl.required_level, key)
            self.assertIsNone(decl.quality, key)

    def test_shapes_exist(self):
        from lib import item_variants  # noqa: PLC0415

        _, catalog = item_variants.load_itemization_tables()
        known = {shape["name"] for shape in catalog.values()}
        for key, decl in self.decls.items():
            for name in (decl.primary, decl.secondary):
                if name is not None:
                    self.assertIn(name, known, f"{key}: {name}")  # no pending shape: the list needs no new one

    def test_jewelry(self):
        for key in JEWELRY:
            decl = self.decls[key]
            self.assertIsNone(decl.primary, key)
            self.assertEqual(decl.primary_share, 0, key)
            self.assertNotRegex(decl.secondary, r"Dodge|Parry|Block|MP5", key)
        for key, decl in self.decls.items():
            if decl.primary is None:
                self.assertIn(key, JEWELRY, key)
            self.assertNotEqual(decl.primary, NULL_PRIMARY_SHAPE, key)

    def test_sockets(self):
        socketed = {k: d.sockets for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, SOCKETS)
        self.assertEqual({k: d.socket_bonus for k, d in self.decls.items() if d.sockets}, BONUS)
        for key in TRINKETS | JEWELRY | RELICS:
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets, jewelry and relics never
        for key, decl in self.decls.items():
            self.assertEqual(decl.sockets is None, decl.socket_bonus is None, key)
        # exactly one socketed piece per boss
        per_boss = {}
        for key in SOCKETS:
            per_boss[LIST[key][0]] = per_boss.get(LIST[key][0], 0) + 1
        self.assertEqual(per_boss, {boss: 1 for boss in BOSS_COUNT})
        # the tank piece is blue, the damage and healing pieces red
        self.assertEqual(SOCKETS["rfc_chieftains_rockplate_pauldrons"], (B,))
        for key, sockets in SOCKETS.items():
            if key != "rfc_chieftains_rockplate_pauldrons":
                self.assertEqual(sockets, (R,), key)
        self.assertNotIn(Y, [c for s in SOCKETS.values() for c in s])  # no two-hander carries one: no second socket

    def test_column_edits(self):
        """The list changes no stock entry's class, subclass or slot, and no new item sets a column but its look."""
        for key, decl in self.decls.items():
            columns = dict(decl.columns)
            if decl.base is not None:
                self.assertEqual(set(columns), set(), f"{key}: a stock entry overrides no column")
        self.assertEqual(self.decls["rfc_tunnelers_hide_cap"].extra_stamina, 0.25)  # the Leather Tank head
        for key, decl in self.decls.items():
            if key != "rfc_tunnelers_hide_cap":
                self.assertEqual(decl.extra_stamina, 0.0, key)

    def test_kept_effects(self):
        self.assertEqual({k for k, d in self.decls.items() if d.keep_spells}, KEPT_EFFECTS)
        for key, decl in self.decls.items():
            self.assertIsNone(decl.spells, key)  # no declared effect: the one stock spell is kept, not rewritten

    def test_declared_multipliers(self):
        declared = {k: d.budget_mult for k, d in self.decls.items() if d.budget_mult is not None}
        self.assertEqual(declared, DECLARED_MULTS)

    def test_every_shape_stat_is_on_every_tier(self):
        """The materialized rows, not the declaration: every stat of the item's shapes has at least one point on every
        tier (blackrock gear REVIEW S3)."""
        from lib import item_variants  # noqa: PLC0415

        _, catalog = item_variants.load_itemization_tables()
        by_name = {shape["name"]: shape for shape in catalog.values()}
        stats = materialized_tier_stats(self.decls)
        for key, decl in self.decls.items():
            wanted = set()
            for name in (decl.primary, decl.secondary):
                if name is not None:
                    wanted |= set(by_name[name]["stats"])
            for tier, got in stats[key].items():
                self.assertFalse(sorted(wanted - set(got)), f"{key} {tier}: a shape stat rounds to 0 ({got})")


if __name__ == "__main__":
    unittest.main()
