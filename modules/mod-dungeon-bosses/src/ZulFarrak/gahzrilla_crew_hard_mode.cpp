/*
 * mod-dungeon-bosses, Zul'Farrak D7Ha:
 * no creature script yet.
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-D7Ha owns this file from now on.
 *
 * What the stub does: `.dbtest zf poolcrew info`.
 *
 * TODO(WP-D7Ha):
 * - SP 2221-2415 (the HM column, GZ15-GZ21); handoff section 3.5 row D7Ha, sections 3.6, 3.8, 3.10, 3.12; the kick and
 *   dispel table. Health and every room point and arena are in ZulFarrakRework.h.
 * - The crew at the pool (CrewMode::PoolAlly, DATA_CREW_AT_POOL) through CR's BlyCrew.h; the key DATA_HARD_MODE_KEY at
 *   Velratha's pull (her 200,000), the flag DATA_HARD_MODE from the gong (the instance arms it, sets the loot bit and
 *   the kill slot 8). A crew death at the pool: the instance clears its bit for the attempt (DATA_CREW_LOST or the
 *   death itself); a pool wipe brings all five back (ACTION_ZF_POOL_RESET).
 * - Mechanics: Wellspring, Blasting Charge, Storm's Chosen, Overcharge, Conductive on everyone, Twin Call, the five
 *   answers and their dead fallbacks (SP 2253-2265), through D7's PoolFight.h.
 * - Add scripts (registered here by WP-D7Ha, in the change that declares the creature): npc_zf_wellspring (301031).
 * - Host-testable logic in GahzrillaCrewHardModeLogic.h (spell ids in kSpellsPoolCrew, 214150-214189),
 *   tests/zf_hard_mode_test.cpp, one `.dbtest zf poolcrew <mechanic>` subcommand per mechanic, the descriptor
 *   (Mechanic::Describe), texts 7604 group 5, 7607 group 4 (CR's rev), 7273 group 2. Own SQL rev:
 *   data/sql/updates/pending_db_world/rev_gahzrilla_crew_hard_mode_zul_farrak.sql (the stock SmartAI is dropped by S0's
 *   rev_skeleton_zul_farrak.sql).
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

#include "Chat.h"
#include "GahzrillaCrewHardModeLogic.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_GAHZRILLA, BOSS_CREW_AT_THE_POOL);
    }

    ChatCommandTable const& PoolcrewTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_gahzrilla_crew_hard_mode()
{
    ZfTest::RegisterBoss("poolcrew", PoolcrewTestCommands());
}
