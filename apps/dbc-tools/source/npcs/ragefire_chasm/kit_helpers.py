"""
Ragefire Chasm build: shared kit helpers (WP-S0 until it reports, then orchestrator-owned;
.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.3).

- 300988 Ragefire Chasm Stalker: the invisible visual stalker (display 11686, trigger flag so players never see or
  target it; the Shadowfang Keep 300516 shape). Any boss WP summons it for a look on the floor: Jergosh's offering patch
  (SHIPPED_SHADOW_POOL_4), Taragaman's fel spots, the pour at the lava. No script, no heroic template.
"""

from lib.dsl.registry import creature_model, creature_template

from ._common import KIT_HELPER

stalker_300988 = creature_template(
    300988, 'Ragefire Chasm Stalker', **{**KIT_HELPER, 'minlevel': 16, 'maxlevel': 16, 'rank': 0, 'unit_class': 1,
                                         'type': 10, 'flags_extra': 0x40 | 0x80, 'ScriptName': ''},
)
creature_model(300988, display_id=11686)
