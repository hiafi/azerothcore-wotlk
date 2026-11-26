/*
 * mod-dungeon-bosses, Zul'Farrak D1:
 * boss_theka_rework (7272).
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-D1 owns this file from now on. Bound by the DT file and the S0
 * rev.
 *
 * What the stub does: a melee placeholder for each unit (the pull line OnBossPull, the arena leash with LeashOptions:
 * no grips, ZulFarrak::NoAssist every tick), a death log line and `.dbtest zf theka info`.
 *
 * TODO(WP-D1):
 * - SP 321-532 (Build spec 463); handoff section 3.5 row D1, sections 3.6, 3.8, 3.10, 3.12; the kick and dispel table.
 *   Health and every room point and arena are in ZulFarrakRework.h.
 * - Mechanics: TK1-TK6 (the persecutor swarms on the rise points kThekaRisePoints, the plague, Hallowed Suffering, the
 *   Lament), heroic the paired swarms (one NW, one NE: section 7 #27 A) and the uncapped stacks (ruling 45). His patrol
 *   814630 is stopped by this WP's rev (section 7 #21 A); the courtyard Scarabs burrow for the fight (section 7 #22 A).
 * - Add scripts (registered here by WP-D1, in the change that declares the creature): npc_zf_persecutor_swarm (301005),
 *   npc_zf_penitent_swarm (301006), the stalker 301007.
 * - Host-testable logic in ThekaLogic.h (spell ids in kSpellsTheka, 213860-213889), tests/zf_theka_test.cpp, one
 *   `.dbtest zf theka <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), texts 7272 groups 0-4.
 *   Own SQL rev: data/sql/updates/pending_db_world/rev_theka_zul_farrak.sql (the stock SmartAI is dropped by S0's
 *   rev_skeleton_zul_farrak.sql).
 * - Rules (handoff section 3.5 rules 1-36, RB-1..RB-22, LESSONS L1-L9): ZulFarrak::NoAssist(me) first in UpdateAI (rule
 *   27, host-tested); loot and hard mode bits are the instance's, never in JustDied; emotes type 41; custom damage
 *   spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (script hits NO_REDIRECTION | NO_REFLECTION too); percent hits via
 *   DungeonKit::RefFlat / RefFlatOn with the boss as the owner; no summoned unit in ObjectData; _visuals.py constants
 *   only; every bot shape `.Within(ThekaFloorBounds())`; kickable casts and bars by the kick table (rule 24, LESSONS
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
#include "ThekaLogic.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

// Theka the Martyr 7272
struct boss_theka_rework : public BossAI
{
    explicit boss_theka_rework(Creature* creature)
        : BossAI(creature, BOSS_THEKA), _arena(CourtyardArena(), LeashOptions("theka")) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
    }

    void ScheduleTasks() override
    {
        // TODO(WP-D1): the timeline
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        OnBossPull(me, "theka");
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_THEKA;
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
        DungeonKit::LogMechanic(kLogDungeon, "theka", "death", "boss_theka_rework");
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

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_THEKA, BOSS_THEKA);
    }

    ChatCommandTable const& ThekaTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_theka_rework()
{
    RegisterDungeonReworkCreatureAI(boss_theka_rework, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("theka", ThekaTestCommands());
}
