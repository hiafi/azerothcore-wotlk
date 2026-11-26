/*
 * mod-dungeon-bosses, Zul'Farrak D7Hb:
 * no creature script yet.
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-D7Hb owns this file from now on.
 *
 * What the stub does: `.dbtest zf deluge info`.
 *
 * TODO(WP-D7Hb):
 * - SP 2221-2415 (GZ22-GZ24); handoff section 3.5 row D7Hb, sections 3.6, 3.8, 3.10, 3.12; the kick and dispel table.
 *   Health and every room point and arena are in ZulFarrakRework.h.
 * - The Deluge at 40% (GZ22-GZ24): the floes (SpotBounds union, Strict), Storm Strikes three a second, Icicle every 5
 *   s, through D7's PoolFight.h.
 * - Add scripts (registered here by WP-D7Hb, in the change that declares the creature): the second head 301032, the
 *   strike stalker 301033.
 * - Host-testable logic in GahzrillaDelugeLogic.h (spell ids in kSpellsDeluge, 214190-214209),
 *   tests/zf_deluge_test.cpp, one `.dbtest zf deluge <mechanic>` subcommand per mechanic, the descriptor
 *   (Mechanic::Describe), texts 7273 group 1. Own SQL rev:
 *   data/sql/updates/pending_db_world/rev_gahzrilla_deluge_zul_farrak.sql (the stock SmartAI is dropped by S0's
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
#include "GahzrillaDelugeLogic.h"
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

    ChatCommandTable const& DelugeTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_gahzrilla_deluge()
{
    ZfTest::RegisterBoss("deluge", DelugeTestCommands());
}
