/*
 * mod-dungeon-bosses, Zul'Farrak CR: Sergeant Bly's crew (Bly 7604, Raven 7605, Oro 7606, Weegli 7607, Murta 7608).
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-CR owns this file and BlyCrew.cpp from now on (handoff section
 * 3.12). Every later WP moves, heals, damages and restores a crew member only through this header (section 3.5 rule
 * 28); none writes a crew template.
 *
 * The instance (instance_zulfarrak_rework.cpp) stores each member's CrewMode, the living mask, the path and the
 * Test's key, and restores dead members by spawn id; this AI applies the mode. The interface CR builds on
 * (ZulFarrakKit.h and ZulFarrakRework.h):
 *
 *   GetCrewMode(instance, member) / SetCrewMode(instance, member, mode)   the mode (Set logs and notifies)
 *   DoAction(ACTION_ZF_CREW_MODE)        this member's mode changed: apply it
 *   DoAction(ACTION_ZF_PYRAMID_STAGE)    a stage began, was won or lost: DATA_PYRAMID_STAGE / _RUNNING (the stair,
 *                                        descent and gather walks: kCrewStairPoints, kCrewDescentPoints,
 *                                        kCrewGatherPoints)
 *   DoAction(ACTION_ZF_CREW_FIGHT)       slot 6 changed (D5's fight): GetBossState(BOSS_CREW), DATA_CREW_PATH
 *   DoAction(ACTION_ZF_POOL_RESET)       a pool wipe brought the five back (PoolAlly)
 *   SetData(DATA_END_DOOR, 1 / 3)        Weegli starts his door walk / his barrel goes off
 *   SetData(DATA_CREW_AT_POOL, 1)        the five arrived at the pool (the Test path)
 *   SetData(DATA_CREW_LOST, member)      optional: the instance sees crew deaths itself (OnUnitDeath)
 *
 * TODO(WP-CR): faction, react state, gossip (Bly's menu 941: the betrayal first, the Test only while DATA_TEST_KEY,
 * section 7 #18 A; Weegli's 940 no longer opens the door before the fight, #13 A), the stair, descent, gather and pool
 * walks, the stock ally kits (casts on a timer, healing by script), Weegli's 1 health floor until the pool and his door
 * walk (kWeegliDoorSpot, barrel 10772, then SetData(DATA_END_DOOR, DONE)), the prisoner state machine for D4a, the
 * restore and reload, the type_flags data row for the four missing CAN_ASSIST (section 7 #17 A), the crew's new text
 * rows (7604 groups 3-5, 7607 groups 3-4: CR's SQL rev), the hooks D4a, D4b, D5 and D7Ha plug into, BlyCrewLogic.h and
 * tests/zf_crew_test.cpp; `.dbtest zf band <subcommand>`. Never the assist timer (the crew help each other).
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_BLY_CREW_H
#define MOD_DUNGEON_BOSSES_ZF_BLY_CREW_H

#include "Define.h"
#include "ScriptedCreature.h"
#include "ZulFarrakRework.h"

class Creature;

namespace ZfCrew
{
    // The AI every crew member runs (one registered script per member, BlyCrew.cpp).
    struct BlyCrewAI : public ScriptedAI
    {
        BlyCrewAI(Creature* creature, uint32 member);

        void Reset() override;
        void DoAction(int32 action) override;
        void UpdateAI(uint32 diff) override;

        uint32 Member() const { return _member; }
        ZulFarrakRework::CrewMode Mode() const;

    protected:
        // Apply `mode` (the stub: faction and react state; out of the fight when passive).
        virtual void ApplyMode(ZulFarrakRework::CrewMode mode);

    private:
        uint32 _member;
    };
}

#endif
