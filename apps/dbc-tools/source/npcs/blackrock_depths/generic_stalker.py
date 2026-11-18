"""
Blackrock Depths build: the generic stalker 300796 (handoff s3.3, the orchestrator's creature). An invisible,
untargetable helper any Blackrock Depths boss script summons as a look or cast source (Gerstahn's heroic pool, others
as they need one). No ScriptName: the summoning script drives it. Display 11686 is the invisible stalker skin every kit
helper uses, as in Blackrock Spire's 300713.
"""

from lib.dsl.registry import creature_model, creature_template

from ._common import KIT_HELPER
from ._visuals import DISPLAY_INVISIBLE_STALKER

generic_stalker_300796 = creature_template(
    300796, 'Blackrock Depths Stalker', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1},
)
creature_model(300796, display_id=DISPLAY_INVISIBLE_STALKER)
