/*
 * mod-dungeon-bosses, Zul'Farrak D6:
 * boss_ukorz_rework (7267), boss_ruuzlu_rework (7797).
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-D6 owns this file from now on. Bound by the DT file and the S0
 * rev.
 *
 * What the stub does: a melee placeholder for each unit (the pull line OnBossPull, the arena leash with LeashOptions:
 * no grips, ZulFarrak::NoAssist every tick), a death log line and `.dbtest zf ukorz info`.
 *
 * TODO(WP-D6):
 * - SP 1719-1999 (Build spec 1910); handoff section 3.5 row D6, sections 3.6, 3.8, 3.10, 3.12; the kick and dispel
 *   table. Health and every room point and arena are in ZulFarrakRework.h.
 * - Mechanics: UK1-UK10 (Fury by percent and its fade, section 7 #41 A; the roars in the Fire school; Bladestorm; the
 *   stamp and the quicksand; the execute rules, #42 A; the donut on kMesaDonutCenter, #34 A), heroic the 30% hold, Call
 *   of Sul'thraze, the Lash, Creeping Sands. LethalGuard keeps Ukorz at 1 health until Ruuzlu is dead (encounter 600
 *   stays kill credit on Ukorz). Ruuzlu is a ScriptedAI: his reset follows Ukorz's (RB-1).
 * - Add scripts (registered here by WP-D6, in the change that declares the creature): npc_zf_quicksand (301025),
 *   npc_zf_creeping_sands (301026).
 * - Host-testable logic in UkorzLogic.h (spell ids in kSpellsUkorz, 214070-214109), tests/zf_ukorz_test.cpp, one
 *   `.dbtest zf ukorz <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), texts 7267 groups 4-7
 *   (0-3 stock), 7797 groups 0-2. Own SQL rev: data/sql/updates/pending_db_world/rev_ukorz_zul_farrak.sql (the stock
 *   SmartAI is dropped by S0's rev_skeleton_zul_farrak.sql).
 * - Rules (handoff section 3.5 rules 1-36, RB-1..RB-22, LESSONS L1-L9): ZulFarrak::NoAssist(me) first in UpdateAI (rule
 *   27, host-tested); loot and hard mode bits are the instance's, never in JustDied; emotes type 41; custom damage
 *   spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (script hits NO_REDIRECTION | NO_REFLECTION too); percent hits via
 *   DungeonKit::RefFlat / RefFlatOn with the boss as the owner; no summoned unit in ObjectData; _visuals.py constants
 *   only; every bot shape `.Within(UkorzFloorBounds())`; kickable casts and bars by the kick table (rule 24, LESSONS
 *   L2), dispels by rule 25; cleanup on reset, evade and death; mechanics include the tank; one log line per firing
 *   (DungeonKit::LogMechanic(kLogDungeon, ...)) and the pull line (OnBossPull, already here); every number a static
 *   constexpr in the Logic header's Tune (rule 32), health from ZulFarrakRework.h Health; the DC contract in the
 *   report.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "ScriptedCreature.h"
#include "UkorzLogic.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

// Chief Ukorz Sandscalp 7267
struct boss_ukorz_rework : public BossAI
{
    explicit boss_ukorz_rework(Creature* creature)
        : BossAI(creature, BOSS_UKORZ), _arena(MesaArena(), LeashOptions("ukorz")) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
    }

    void ScheduleTasks() override
    {
        // TODO(WP-D6): the timeline
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        OnBossPull(me, "ukorz");
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_UKORZ;
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
        DungeonKit::LogMechanic(kLogDungeon, "ukorz", "death", "boss_ukorz_rework");
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

// Ruuzlu 7797
struct boss_ruuzlu_rework : public ScriptedAI
{
    explicit boss_ruuzlu_rework(Creature* creature)
        : ScriptedAI(creature), _arena(MesaArena(), LeashOptions("ukorz")) { }

    void Reset() override
    {
        _arena.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);

        OnBossPull(me, "ukorz");
        _arena.Engage(me);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, "ukorz", "death", "boss_ruuzlu_rework");
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        scheduler.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_UKORZ, BOSS_UKORZ);
    }

    ChatCommandTable const& UkorzTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_ukorz_rework()
{
    RegisterDungeonReworkCreatureAI(boss_ukorz_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(boss_ruuzlu_rework, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("ukorz", UkorzTestCommands());
}
