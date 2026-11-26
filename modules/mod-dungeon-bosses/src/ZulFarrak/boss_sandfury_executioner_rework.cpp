/*
 * mod-dungeon-bosses, Zul'Farrak D4a:
 * boss_sandfury_executioner_rework (7274).
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-D4a owns this file from now on. Bound by the DT file and the S0
 * rev.
 *
 * What the stub does: a melee placeholder for each unit (the pull line OnBossPull, the arena leash with LeashOptions:
 * no grips, ZulFarrak::NoAssist every tick), a death log line and `.dbtest zf block info`.
 *
 * TODO(WP-D4a):
 * - SP 1101-1432 (Build spec 1346; PY1-PY3, PY16); handoff section 3.5 row D4a, sections 3.6, 3.8, 3.10, 3.12; the kick
 *   and dispel table. Health and every room point and arena are in ZulFarrakRework.h.
 * - He is stage 1 of the Pyramid, not a BossAI: the instance writes slot 5 (ZulFarrakKit.h PyramidStageDirector). The
 *   stub already sends SetData(DATA_PYRAMID_START, 1) at the pull and DATA_PYRAMID_FAIL after an evade; his death wins
 *   the stage (the instance sees it). Register stage 1's director here (RegisterPyramidStage) if the Block needs hooks;
 *   PyramidFight.h is this WP's.
 * - Mechanics: PY1 the Block (the prisoner through CR's BlyCrew.h: SetCrewMode Prisoner, the chain, the 4 s Behead, a
 *   Soak on the prisoner; unsoaked: the crew member dies and the instance counts the Offering or 30 Blood Price
 *   itself), PY2 Grievous Wound (heroic), PY3 Offerings (the buff on every Sandfury from DATA_OFFERINGS), PY16 Blood
 *   Price (heroic: SetData(DATA_BLOOD_PRICE, total) each second a player bleeds; the instance snapshots and restores
 *   it).
 * - Add scripts (registered here by WP-D4a, in the change that declares the creature): the chain stalker 301019 (shared
 *   with D4b).
 * - Host-testable logic in BlockLogic.h (spell ids in kSpellsBlock, 213960-213989), tests/zf_block_test.cpp, one
 *   `.dbtest zf block <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), texts 7274 group 2 (0-1
 *   stock). Own SQL rev: data/sql/updates/pending_db_world/rev_sandfury_executioner_zul_farrak.sql (the stock SmartAI
 *   is dropped by S0's rev_skeleton_zul_farrak.sql).
 * - Rules (handoff section 3.5 rules 1-36, RB-1..RB-22, LESSONS L1-L9): ZulFarrak::NoAssist(me) first in UpdateAI (rule
 *   27, host-tested); loot and hard mode bits are the instance's, never in JustDied; emotes type 41; custom damage
 *   spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (script hits NO_REDIRECTION | NO_REFLECTION too); percent hits via
 *   DungeonKit::RefFlat / RefFlatOn with the boss as the owner; no summoned unit in ObjectData; _visuals.py constants
 *   only; every bot shape `.Within(BlockFloorBounds())`; kickable casts and bars by the kick table (rule 24, LESSONS
 *   L2), dispels by rule 25; cleanup on reset, evade and death; mechanics include the tank; one log line per firing
 *   (DungeonKit::LogMechanic(kLogDungeon, ...)) and the pull line (OnBossPull, already here); every number a static
 *   constexpr in the Logic header's Tune (rule 32), health from ZulFarrakRework.h Health; the DC contract in the
 *   report.
 */

#include "ArenaGuard.h"
#include "BlockLogic.h"
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

// Sandfury Executioner 7274
struct boss_sandfury_executioner_rework : public ScriptedAI
{
    explicit boss_sandfury_executioner_rework(Creature* creature)
        : ScriptedAI(creature), _arena(PyramidTopArena(), LeashOptions("block")) { }

    void Reset() override
    {
        _arena.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);

        OnBossPull(me, "block");
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_PYRAMID;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        if (InstanceScript* instance = me->GetInstanceScript())
            instance->SetData(DATA_PYRAMID_START, PYRAMID_STAGE_BLOCK);     // refused unless it is the stage in play
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
        // After the base: he is out of combat, so the instance's wipe does not evade him a second time.
        if (InstanceScript* instance = me->GetInstanceScript())
            instance->SetData(DATA_PYRAMID_FAIL, PYRAMID_STAGE_BLOCK);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, "block", "death", "boss_sandfury_executioner_rework");
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
        return ZfTest::ShowBossInfo(handler, NPC_EXECUTIONER, BOSS_PYRAMID);
    }

    ChatCommandTable const& BlockTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_sandfury_executioner_rework()
{
    RegisterDungeonReworkCreatureAI(boss_sandfury_executioner_rework, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("block", BlockTestCommands());
}
