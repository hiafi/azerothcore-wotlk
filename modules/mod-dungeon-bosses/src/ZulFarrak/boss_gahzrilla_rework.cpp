/*
 * mod-dungeon-bosses, Zul'Farrak D7:
 * boss_velratha_rework (7795), boss_gahzrilla_rework (7273).
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-D7 owns this file from now on. Bound by the DT file and the S0
 * rev.
 *
 * What the stub does: a melee placeholder for each unit (the pull line OnBossPull, the arena leash with LeashOptions:
 * no grips, ZulFarrak::NoAssist every tick), a death log line and `.dbtest zf pool info`.
 *
 * TODO(WP-D7):
 * - SP 2001-2415 (Build spec 2298); handoff section 3.5 row D7, sections 3.6, 3.8, 3.10, 3.12; the kick and dispel
 *   table. Health and every room point and arena are in ZulFarrakRework.h.
 * - Velratha (slot 0) strikes the gong at 30% (GZ10, ruling 37): SetData(DATA_GONG_STRUCK, 1); the instance arms the
 *   hard mode on its key and summons Gahz'rilla at kGahzrillaSummon; this WP walks him ashore to kGahzrillaAshore
 *   (section 7 #35 A). Her patrol 815700 is stopped by this WP's rev. A pool wipe: the instance reopens her slot after
 *   his and brings her back (section 7 #43 h A), and sinks a Gahz'rilla left out of combat.
 * - Mechanics: GZ1-GZ14 (Spill the Pool 4 s / 3 s and Icicle 2.5 s, section 10 #40 B; the water field (KT's
 *   WaterField), Storm Builds, Charged, Meltwater, Conductive, the Slam copy without its knock). PoolFight.h is this
 *   WP's (the hooks D7Ha and D7Hb plug into). Hard mode health: HardMode() (the flag, or the key at her pull) and
 *   ZulFarrakRework.h Health.
 * - Add scripts (registered here by WP-D7, in the change that declares the creature): npc_zf_puddle (301030).
 * - Host-testable logic in GahzrillaLogic.h (spell ids in kSpellsPool, 214110-214149), tests/zf_gahzrilla_test.cpp, one
 *   `.dbtest zf pool <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), texts 7795 groups 0-1,
 *   7273 group 0. Own SQL rev: data/sql/updates/pending_db_world/rev_gahzrilla_zul_farrak.sql (the stock SmartAI is
 *   dropped by S0's rev_skeleton_zul_farrak.sql).
 * - Rules (handoff section 3.5 rules 1-36, RB-1..RB-22, LESSONS L1-L9): ZulFarrak::NoAssist(me) first in UpdateAI (rule
 *   27, host-tested); loot and hard mode bits are the instance's, never in JustDied; emotes type 41; custom damage
 *   spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (script hits NO_REDIRECTION | NO_REFLECTION too); percent hits via
 *   DungeonKit::RefFlat / RefFlatOn with the boss as the owner; no summoned unit in ObjectData; _visuals.py constants
 *   only; every bot shape `.Within(PoolFloorBounds())`; kickable casts and bars by the kick table (rule 24, LESSONS
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
#include "GahzrillaLogic.h"
#include "InstanceScript.h"
#include "ScriptedCreature.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

// Hydromancer Velratha 7795
struct boss_velratha_rework : public BossAI
{
    explicit boss_velratha_rework(Creature* creature)
        : BossAI(creature, BOSS_VELRATHA), _arena(PoolArena(), LeashOptions("pool")) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
    }

    void ScheduleTasks() override
    {
        // TODO(WP-D7): the timeline
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        OnBossPull(me, "pool", HardMode());
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_VELRATHA;
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
        DungeonKit::LogMechanic(kLogDungeon, "pool", "death", "boss_velratha_rework");
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
    bool HardMode() const
    {
        InstanceScript const* instance = me->GetInstanceScript();
        return instance && (instance->GetData(DATA_HARD_MODE) || instance->GetData(DATA_HARD_MODE_KEY));
    }

    DungeonKit::ArenaGuard _arena;
};

// Gahz'rilla 7273
struct boss_gahzrilla_rework : public BossAI
{
    explicit boss_gahzrilla_rework(Creature* creature)
        : BossAI(creature, BOSS_GAHZRILLA), _arena(PoolArena(), LeashOptions("pool")) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
    }

    void ScheduleTasks() override
    {
        // TODO(WP-D7): the timeline
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        OnBossPull(me, "pool", HardMode());
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_GAHZRILLA;
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
        DungeonKit::LogMechanic(kLogDungeon, "pool", "death", "boss_gahzrilla_rework");
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
    bool HardMode() const
    {
        InstanceScript const* instance = me->GetInstanceScript();
        return instance && (instance->GetData(DATA_HARD_MODE) || instance->GetData(DATA_HARD_MODE_KEY));
    }

    DungeonKit::ArenaGuard _arena;
};

namespace
{
    bool HandleInfoVelratha(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_VELRATHA, BOSS_VELRATHA);
    }

    bool HandleInfoGahzrilla(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_GAHZRILLA, BOSS_GAHZRILLA);
    }

    ChatCommandTable const& PoolTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "velratha",  HandleInfoVelratha,  SEC_GAMEMASTER, Console::No },
            { "gahzrilla", HandleInfoGahzrilla, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_gahzrilla_rework()
{
    RegisterDungeonReworkCreatureAI(boss_velratha_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(boss_gahzrilla_rework, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("pool", PoolTestCommands());
}
