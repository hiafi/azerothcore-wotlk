/*
 * mod-dungeon-bosses, Zul'Farrak D2:
 * boss_antusul_rework (8127), npc_antusul_servant_rework (8156).
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-D2 owns this file from now on. Bound by the DT file and the S0
 * rev.
 *
 * What the stub does: a melee placeholder for each unit (the pull line OnBossPull, the arena leash with LeashOptions:
 * no grips, ZulFarrak::NoAssist every tick), a death log line and `.dbtest zf antusul info`.
 *
 * TODO(WP-D2):
 * - SP 534-807 (Build spec 733); handoff section 3.5 row D2, sections 3.6, 3.8, 3.10, 3.12; the kick and dispel table.
 *   Health and every room point and arena are in ZulFarrakRework.h.
 * - Mechanics: AS1-AS8 (Calcify and the gaze, Shatterbolt, Earthen Shockwave, the Servants on kServantRisePoints,
 *   Stoneflesh), the wake by area trigger 1447 (SetData(1, 1), kept by section 7 #25 A; the chamber fight, #28 A).
 * - Add scripts (registered here by WP-D2, in the change that declares the creature): npc_antusul_servant_rework (8156,
 *   stub registered here; the Earthgrab totem 6066's SmartAI is this WP's to drop).
 * - Host-testable logic in AntusulLogic.h (spell ids in kSpellsAntusul, 213890-213919), tests/zf_antusul_test.cpp, one
 *   `.dbtest zf antusul <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), texts 8127 group 3
 *   (0-2 stock). Own SQL rev: data/sql/updates/pending_db_world/rev_antusul_zul_farrak.sql (the stock SmartAI is
 *   dropped by S0's rev_skeleton_zul_farrak.sql).
 * - Rules (handoff section 3.5 rules 1-36, RB-1..RB-22, LESSONS L1-L9): ZulFarrak::NoAssist(me) first in UpdateAI (rule
 *   27, host-tested); loot and hard mode bits are the instance's, never in JustDied; emotes type 41; custom damage
 *   spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (script hits NO_REDIRECTION | NO_REFLECTION too); percent hits via
 *   DungeonKit::RefFlat / RefFlatOn with the boss as the owner; no summoned unit in ObjectData; _visuals.py constants
 *   only; every bot shape `.Within(AntusulFloorBounds())`; kickable casts and bars by the kick table (rule 24, LESSONS
 *   L2), dispels by rule 25; cleanup on reset, evade and death; mechanics include the tank; one log line per firing
 *   (DungeonKit::LogMechanic(kLogDungeon, ...)) and the pull line (OnBossPull, already here); every number a static
 *   constexpr in the Logic header's Tune (rule 32), health from ZulFarrakRework.h Health; the DC contract in the
 *   report.
 */

#include "AntusulLogic.h"
#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "ScriptedCreature.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

// Antu'sul 8127
struct boss_antusul_rework : public BossAI
{
    explicit boss_antusul_rework(Creature* creature)
        : BossAI(creature, BOSS_ANTUSUL), _arena(DenArena(), LeashOptions("antusul")) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
        // TODO(WP-D2): area trigger 1447's SetData(1, 1) wakes him (section 7 #25 A, #28 A);
        // DC's wake hook sends the same.
    }

    void ScheduleTasks() override
    {
        // TODO(WP-D2): the timeline
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        OnBossPull(me, "antusul");
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ANTUSUL;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _arena.Reset();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, "antusul", "death", "boss_antusul_rework");
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        events.Update(diff);
        scheduler.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
};

// Servant of Antu'sul 8156 (no spawn: Antu'sul's summons)
struct npc_antusul_servant_rework : public ScriptedAI
{
    explicit npc_antusul_servant_rework(Creature* creature) : ScriptedAI(creature) { }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (!UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_ANTUSUL, BOSS_ANTUSUL);
    }

    ChatCommandTable const& AntusulTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_antusul_rework()
{
    RegisterDungeonReworkCreatureAI(boss_antusul_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_antusul_servant_rework, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("antusul", AntusulTestCommands());
}
