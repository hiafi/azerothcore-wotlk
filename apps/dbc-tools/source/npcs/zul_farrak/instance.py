"""
Zul'Farrak build WP-S0: the instance's own spells (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.2,
s3.3, s7 #5 A). The shared slice 213840-213859 (kSpellsShared of modules/mod-dungeon-bosses
src/ZulFarrak/ZulFarrakRework.h) is S0's, then the orchestrator's:

  213840  The Pyramid          encounter 598's credit: a server-side DUMMY never cast; once Sezz'ziz and Nekrum are
                               both dead (stage 3 won) the instance credits it (DungeonKit::CreditEncounterBySpell), and
                               WP-H re-points the stock row 598 (bit 5) and its heroic copy to it (creditType 1)
  213841  Sergeant Bly's Crew  encounter 599's credit: the same, when the crew's fight ends (slot 6 DONE, either path);
                               WP-H re-points 599 (bit 6)
  213842                       reserved: a script-applied Weakened copy, if a WP needs one
  213843-213844 spare; 213845-213859 CR's ally kits.

ObjectMgr::LoadInstanceEncounters only needs the spells to exist (the Scarlet Monastery 212300 precedent).
"""

from lib.dsl import RANGE_SELF, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT
from lib.dsl.registry import spell

from ._common import ATTR4_NO_CAST_LOG, TARGET_UNIT_CASTER, kit_raw

_SD = "Zul'Farrak build WP-S0 (the instance)"
_ICON_GENERIC = 1

SPELL_PYRAMID_CREDIT = 213840
SPELL_CREW_CREDIT = 213841


def _credit(spell_id: int, name: str, when: str):
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_GENERIC,
        notes=f'{_SD}: the encounter\'s credit. Never cast: {when} the instance credits it '
              f'(DungeonKit::CreditEncounterBySpell, spell {spell_id}), and WP-H\'s re-pointed instance_encounters row '
              'names it (creditType 1). ObjectMgr::LoadInstanceEncounters only needs the spell to exist. No effect.',
        raw_overrides=kit_raw('', instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


credit_213840 = _credit(SPELL_PYRAMID_CREDIT, 'The Pyramid',
                        "once Shadowpriest Sezz'ziz and Nekrum Gutchewer are both dead (the Altar won)")
credit_213841 = _credit(SPELL_CREW_CREDIT, "Sergeant Bly's Crew",
                        "when the crew's fight ends on either path (slot 6 DONE)")
