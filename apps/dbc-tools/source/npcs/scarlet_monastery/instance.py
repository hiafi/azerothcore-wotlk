"""
Scarlet Monastery build WP-S0: the instance's own spells (.agents/plans/scarlet-monastery-build/
scarlet-monastery-build.HANDOFF.md s3.2, s3.3, s3.11 #3). The shared slice 212300-212319 (kSpellsShared of
modules/mod-dungeon-bosses src/ScarletMonastery/ScarletMonasteryRework.h) is S0's, then the orchestrator's:

  212300  The council          the encounter's credit: a server-side DUMMY never cast; once Azshir and the Fallen
                               Champion are both dead the instance credits it (DungeonKit::CreditEncounterBySpell)
                               and FD-SM's new normal row (and its heroic copy) names it (creditType 1)
  212301  The Last Stand       the encounter's credit: the same, sent when Mograine falls at 1% (D13 sets
                               DATA_LAST_STAND = DONE); FD-SM re-points the stock row 449 (bit 5) to it
  212302-212319 spare (the portal teleport, the kit cast bars and the lawn checks if a WP needs one).

ObjectMgr::LoadInstanceEncounters only needs the spells to exist (the BRD 211066 precedent).

The generic stalkers (the orchestrator's creatures, declared here with S0's file): 300922 for wave 1 and 300958 for
wave 2 (NPC_SM_STALKER / NPC_SM_STALKER_WAVE2). Invisible, untargetable helpers a boss script summons as a look or
cast source; no ScriptName (the summoning script drives them), display 11686, as Blackrock Depths' 300796. They run on
their normal entry on heroic (no heroic template: source/world/dungeons/scarlet_monastery.py).
"""

from lib.dsl import RANGE_SELF, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    SPELL_COUNCIL_CREDIT,
    SPELL_LAST_STAND_CREDIT,
    TARGET_UNIT_CASTER,
    kit_raw,
)
from ._visuals import DISPLAY_INVISIBLE_STALKER

_SD = 'Scarlet Monastery build WP-S0 (the instance)'
_ICON_GENERIC = 1


def _credit(spell_id: int, name: str, when: str):
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_GENERIC,
        notes=f'{_SD}: the encounter\'s credit. Never cast: {when} the instance credits it '
              f'(DungeonKit::CreditEncounterBySpell, spell {spell_id}), and FD-SM\'s instance_encounters row '
              'names it (creditType 1). ObjectMgr::LoadInstanceEncounters only needs the spell to exist. No effect.',
        raw_overrides=kit_raw('', instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


credit_212300 = _credit(SPELL_COUNCIL_CREDIT, 'Azshir the Sleepless and the Fallen Champion',
                        'once Azshir and the Fallen Champion are both dead')
credit_212301 = _credit(SPELL_LAST_STAND_CREDIT, 'The Last Stand',
                        'when Scarlet Commander Mograine falls at 1% (the Last Stand DONE)')


# The generic stalkers (BRD 300796's columns).
GENERIC_STALKER = 300922
GENERIC_STALKER_WAVE_2 = 300958

generic_stalker_300922 = creature_template(
    300922, 'Scarlet Monastery Stalker', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1},
)
creature_model(300922, display_id=DISPLAY_INVISIBLE_STALKER)
generic_stalker_300958 = creature_template(
    300958, 'Scarlet Monastery Stalker', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1},
)
creature_model(300958, display_id=DISPLAY_INVISIBLE_STALKER)
