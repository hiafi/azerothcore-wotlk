/*
 * mod-dungeon-bosses, Zul'Farrak CR: Sergeant Bly's crew (BlyCrew.h).
 * STUB written by WP-S0; WP-CR owns this file. Bound by the S0 rev (npc_bly_crew_bly, _raven, _oro, _weegli, _murta in
 * place of npc_sergeant_bly, npc_weegli_blastfuse and the SmartAI of 7605, 7606, 7608). The stub applies the mode's
 * faction and react state and fights in melee; no gossip, no walks, no kits yet: until CR, Bly offers nothing and
 * Weegli opens no door (the instance's fallback does, 60 s after slot 6 is DONE).
 */

#include "BlyCrew.h"
#include "BlyCrewLogic.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

namespace ZfCrew
{
    BlyCrewAI::BlyCrewAI(Creature* creature, uint32 member) : ScriptedAI(creature), _member(member) { }

    CrewMode BlyCrewAI::Mode() const
    {
        return GetCrewMode(me->GetInstanceScript(), _member);
    }

    void BlyCrewAI::Reset()
    {
        ApplyMode(Mode());
    }

    void BlyCrewAI::DoAction(int32 action)
    {
        if (action == ACTION_ZF_CREW_MODE || action == ACTION_ZF_POOL_RESET)
            ApplyMode(Mode());
    }

    void BlyCrewAI::UpdateAI(uint32 /*diff*/)
    {
        if (!UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }

    void BlyCrewAI::ApplyMode(CrewMode mode)
    {
        me->SetFaction(FactionFor(mode));
        if (FightsIn(mode))
        {
            me->SetReactState(REACT_AGGRESSIVE);
            return;
        }
        me->SetReactState(REACT_PASSIVE);
        if (me->IsEngaged())
            EnterEvadeMode();
    }
}

struct npc_bly_crew_bly : public ZfCrew::BlyCrewAI
{
    explicit npc_bly_crew_bly(Creature* creature) : BlyCrewAI(creature, CREW_BLY) { }
};

struct npc_bly_crew_raven : public ZfCrew::BlyCrewAI
{
    explicit npc_bly_crew_raven(Creature* creature) : BlyCrewAI(creature, CREW_RAVEN) { }
};

struct npc_bly_crew_oro : public ZfCrew::BlyCrewAI
{
    explicit npc_bly_crew_oro(Creature* creature) : BlyCrewAI(creature, CREW_ORO) { }
};

struct npc_bly_crew_weegli : public ZfCrew::BlyCrewAI
{
    explicit npc_bly_crew_weegli(Creature* creature) : BlyCrewAI(creature, CREW_WEEGLI) { }
};

struct npc_bly_crew_murta : public ZfCrew::BlyCrewAI
{
    explicit npc_bly_crew_murta(Creature* creature) : BlyCrewAI(creature, CREW_MURTA) { }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        ZfTest::PrintRunState(handler, instance);
        return true;
    }

    ChatCommandTable const& BandTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_zf_bly_crew()
{
    RegisterDungeonReworkCreatureAI(npc_bly_crew_bly, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_bly_crew_raven, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_bly_crew_oro, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_bly_crew_weegli, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_bly_crew_murta, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("band", BandTestCommands());
}
