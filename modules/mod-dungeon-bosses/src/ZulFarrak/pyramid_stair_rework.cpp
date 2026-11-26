/*
 * mod-dungeon-bosses, Zul'Farrak D4b:
 * no creature script yet.
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-D4b owns this file from now on.
 *
 * What the stub does: `.dbtest zf stair info`.
 *
 * TODO(WP-D4b):
 * - SP 1101-1432 (Build spec 1346; PY4-PY16); handoff section 3.5 row D4b, sections 3.6, 3.8, 3.10, 3.12; the kick and
 *   dispel table. Health and every room point and arena are in ZulFarrakRework.h.
 * - Stages 2 and 3 of the Pyramid: register their directors here (RegisterPyramidStage(2 / 3, ...), ZulFarrakKit.h).
 *   Stage 2 starts when the cages open (the instance) and again 10 s after a living player stands on the landing;
 *   OnStart spawns wave 1 from kWaveSpawns (z from the mesh), the sends up path 81553 (8 s, groups of 3, 4, 5, 6 and
 *   the rest), wave 2, the barrels; SetData(DATA_PYRAMID_COMPLETE, 2) at wave 2's last troll. Stage 3: OnStart(false)
 *   spawns wave 3 with Sezz'ziz and Nekrum, OnWait puts them back idle after a wipe or a reload; the instance wins it.
 * - Mechanics: PY4 Weegli's Barrels (the lane kStairPolygon from y kStairLaneYMin to kStairLaneYMax, Weegli through
 *   CR), PY5 the crew on the Stair (CR places them), PY6-PY11 the specialists, PY16 Blood Price (heroic,
 *   SetData(DATA_BLOOD_PRICE, total)).
 * - Add scripts (registered here by WP-D4b, in the change that declares the creature): npc_zf_sandfury_berserker
 *   (301015), npc_zf_sandfury_hexmaster (301016), npc_zf_sandfury_witch_doctor (301017), npc_zf_weegli_barrel (301018),
 *   the lane stalker 301019.
 * - Host-testable logic in StairLogic.h (spell ids in kSpellsStair, 213990-214029), tests/zf_stair_test.cpp, one
 *   `.dbtest zf stair <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), texts 7607 group 3
 *   (Weegli's barrel yell; CR's rev inserts the crew's rows), 7275 group 0. Own SQL rev:
 *   data/sql/updates/pending_db_world/rev_pyramid_stair_zul_farrak.sql (the stock SmartAI is dropped by S0's
 *   rev_skeleton_zul_farrak.sql).
 * - Rules (handoff section 3.5 rules 1-36, RB-1..RB-22, LESSONS L1-L9): ZulFarrak::NoAssist(me) first in UpdateAI (rule
 *   27, host-tested); loot and hard mode bits are the instance's, never in JustDied; emotes type 41; custom damage
 *   spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (script hits NO_REDIRECTION | NO_REFLECTION too); percent hits via
 *   DungeonKit::RefFlat / RefFlatOn with the boss as the owner; no summoned unit in ObjectData; _visuals.py constants
 *   only; every bot shape `.Within(StairFloorBounds())`; kickable casts and bars by the kick table (rule 24, LESSONS
 *   L2), dispels by rule 25; cleanup on reset, evade and death; mechanics include the tank; one log line per firing
 *   (DungeonKit::LogMechanic(kLogDungeon, ...)) and the pull line (OnBossPull, already here); every number a static
 *   constexpr in the Logic header's Tune (rule 32), health from ZulFarrakRework.h Health; the DC contract in the
 *   report.
 */

#include "Chat.h"
#include "StairLogic.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_SEZZZIZ, BOSS_PYRAMID);
    }

    ChatCommandTable const& StairTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_pyramid_stair_rework()
{
    ZfTest::RegisterBoss("stair", StairTestCommands());
}
