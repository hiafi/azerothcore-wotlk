/*
 * mod-dungeon-bosses, Zul'Farrak D3:
 * boss_zumrah_rework (7271).
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-D3 owns this file from now on. Bound by the DT file and the S0
 * rev.
 *
 * What the stub does: a melee placeholder for each unit (the pull line OnBossPull, the arena leash with LeashOptions:
 * no grips, ZulFarrak::NoAssist every tick), a death log line and `.dbtest zf zumrah info`.
 *
 * TODO(WP-D3):
 * - SP 809-1099 (Build spec 1009); handoff section 3.5 row D3, sections 3.6, 3.8, 3.10, 3.12; the kick and dispel
 *   table. Health and every room point and arena are in ZulFarrakRework.h.
 * - Mechanics: ZR1-ZR8 (Spirit Rend, the walkers and the souls from the graves within kGraveReachYd, the ward, Bound
 *   Dead at kBoundDeadSpots then kBoundDeadOverflow), heroic flood, Soul Burn, Echo, Wail, Graves; type 11
 *   invisibility; the bolt copy of 12739 (section 2.5).
 * - Add scripts (registered here by WP-D3, in the change that declares the creature): npc_zf_empty_vessel (301010),
 *   npc_zf_lost_soul (301011), npc_zf_bound_dead (301012), the grave stalker 301013.
 * - Host-testable logic in ZumrahLogic.h (spell ids in kSpellsZumrah, 213920-213959), tests/zf_zumrah_test.cpp, one
 *   `.dbtest zf zumrah <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), texts 7271 groups 3-4
 *   (0-1 stock). Own SQL rev: data/sql/updates/pending_db_world/rev_zumrah_zul_farrak.sql (the stock SmartAI is dropped
 *   by S0's rev_skeleton_zul_farrak.sql).
 * - Rules (handoff section 3.5 rules 1-36, RB-1..RB-22, LESSONS L1-L9): ZulFarrak::NoAssist(me) first in UpdateAI (rule
 *   27, host-tested); loot and hard mode bits are the instance's, never in JustDied; emotes type 41; custom damage
 *   spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (script hits NO_REDIRECTION | NO_REFLECTION too); percent hits via
 *   DungeonKit::RefFlat / RefFlatOn with the boss as the owner; no summoned unit in ObjectData; _visuals.py constants
 *   only; every bot shape `.Within(ZumrahFloorBounds())`; kickable casts and bars by the kick table (rule 24, LESSONS
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
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"
#include "ZumrahLogic.h"

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

// Witch Doctor Zum'rah 7271
struct boss_zumrah_rework : public BossAI
{
    explicit boss_zumrah_rework(Creature* creature)
        : BossAI(creature, BOSS_ZUMRAH), _arena(BowlArena(), LeashOptions("zumrah")) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
        // Faction 35 until area trigger 962's SmartAI sets 37 (DC hook 5 reads 35 / 37): his stock SmartAI's
        // reset row restored it; it is dropped, so Reset does.
        me->RestoreFaction();
    }

    void ScheduleTasks() override
    {
        // TODO(WP-D3): the timeline
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        OnBossPull(me, "zumrah");
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ZUMRAH;
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
        DungeonKit::LogMechanic(kLogDungeon, "zumrah", "death", "boss_zumrah_rework");
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
        return ZfTest::ShowBossInfo(handler, NPC_ZUMRAH, BOSS_ZUMRAH);
    }

    ChatCommandTable const& ZumrahTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_zumrah_rework()
{
    RegisterDungeonReworkCreatureAI(boss_zumrah_rework, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("zumrah", ZumrahTestCommands());
}
