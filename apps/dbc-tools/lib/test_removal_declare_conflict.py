"""
Declared-vs-removed conflict guard: `generate.py --check` returns before `spell_tables.render_removal_blocks` runs, so a
row that the DSL both declares and removes (for example an old `unbind_bonus_coefficients` left on a spell that later
gained `ap_potency`, whose `spell_bonus_data` row is then auto-declared) only fails on the full run, after the headers are
rewritten and before any SQL exists. This test runs the same loader and the same call on the real source tree.

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_removal_declare_conflict.py -q
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402
from lib import dbcfmt, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry as dsl_registry  # noqa: E402

_CACHE: dict = {}


def _removal_inputs() -> tuple[dict, dict]:
    """The same class load and live-key plumbing generate.py main uses before render_removal_blocks (about 2 min)."""
    if not _CACHE:
        source_dir = generate.SOURCE_DIR
        ids_cfg = source.load_ids(source_dir / "ids.yaml")
        trainer_index = trainer_state.load_trainer_index()
        spell_table_index = spell_tables.load_spell_table_index()
        creature_table_index = spell_tables.load_creature_table_index()
        live_data = spell_tables.load_dsl_live_data()
        kwargs = dict(
            ids_cfg=ids_cfg, trainer_index=trainer_index,
            existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
            shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
            existing_creature_rows={int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")},
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data=live_data,
        )
        dsl_classes = dsl_registry.load_classes_dir(source_dir / "classes", **kwargs)
        generate._merge_npc_declarations(dsl_classes, dsl_registry.load_classes_dir(source_dir / "npcs", **kwargs))
        generate._merge_npc_declarations(
            dsl_classes, dsl_registry.load_classes_dir(source_dir / "world", ids_cfg=ids_cfg, live_data=live_data),
            "source/world/",
        )
        live_keys = {spec.name: spell_table_index.live_keys(spec.name) for spec in spell_tables.SPELL_TABLES}
        live_keys["trainer_spell"] = set(trainer_index.existing_trainer_spells.keys())
        _CACHE.update(dsl_classes=dsl_classes, live_keys=live_keys)
    return _CACHE["dsl_classes"], _CACHE["live_keys"]


class RemovalDeclareConflictTest(unittest.TestCase):
    def test_no_row_is_both_declared_and_removed(self):
        dsl_classes, live_keys = _removal_inputs()
        try:
            spell_tables.render_removal_blocks(dsl_classes, live_keys)
        except spell_tables.DeclareAndRemoveConflictError as exc:
            self.fail(f"generate.py's full run would raise: {exc}")

    def test_the_guard_fires_on_a_conflict(self):
        spec = spell_tables.REMOVAL_TABLES[0]
        row = {column: 1 for column in spec.key_columns}
        dsl_classes = {spec.removal_key: [dict(row)], spec.declared_key: [dict(row)]}
        with self.assertRaises(spell_tables.DeclareAndRemoveConflictError):
            spell_tables.render_removal_blocks(dsl_classes, {})


if __name__ == "__main__":
    unittest.main()
