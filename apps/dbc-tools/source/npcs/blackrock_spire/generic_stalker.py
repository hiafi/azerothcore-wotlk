"""
Blackrock Spire build: the generic stalker 300713 (handoff s3.3, the orchestrator's creature). An invisible,
untargetable helper any Blackrock Spire boss script summons as a look or cast source (Zigris's keg fuse and mortar, ZG;
others as they need one). No ScriptName: the summoning script drives it. Display 11686 is the invisible stalker skin
every kit helper uses (_visuals.py DISPLAY_INVISIBLE_STALKER, as Stratholme's).
"""

from lib.dsl.registry import creature_model, creature_template

from ._common import KIT_HELPER
from ._visuals import DISPLAY_INVISIBLE_STALKER

generic_stalker_300713 = creature_template(
    300713, 'Blackrock Spire Stalker', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1},
)
creature_model(300713, display_id=DISPLAY_INVISIBLE_STALKER)
