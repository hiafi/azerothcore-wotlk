"""
Shadowfang Keep build: shared kit helpers (orchestrator-owned; .agents/plans/shadowfang-keep-build/
shadowfang-keep-build.HANDOFF.md s3.4).

- 300516 Strike Stalker: the invisible visual stalker (mod-boss-mechanics stalker display 11686, trigger flag so players
  never see or target it). Fenrus summons it for the heroic Shadow Lightning bolt on a miss (WP-S7); Odo summons it at a
  cracked bell for the smoke (WP-S5). No script, no heroic template.
"""

from lib.dsl.registry import creature_model, creature_template

from ._common import KIT_HELPER

strike_stalker_300516 = creature_template(
    300516, 'Strike Stalker', **{**KIT_HELPER, 'minlevel': 20, 'maxlevel': 20, 'rank': 0, 'unit_class': 1,
                                 'type': 10, 'flags_extra': 0x40 | 0x80, 'ScriptName': ''},
)
creature_model(300516, display_id=11686)
