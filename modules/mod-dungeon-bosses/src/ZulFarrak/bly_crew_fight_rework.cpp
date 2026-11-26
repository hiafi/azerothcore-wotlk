/*
 * mod-dungeon-bosses, Zul'Farrak D5:
 * no creature script yet.
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-D5 owns this file from now on.
 *
 * What the stub does: `.dbtest zf blyfight info`.
 *
 * TODO(WP-D5):
 * - SP 1434-1717 (Build spec 1625); handoff section 3.5 row D5, sections 3.6, 3.8, 3.10, 3.12; the kick and dispel
 *   table. Health and every room point and arena are in ZulFarrakRework.h.
 * - The crew's fight runs on CR's crew (BlyCrew.h): Bly's gossip sets DATA_CREW_PATH (1 betrayal, 2 the Test while
 *   DATA_TEST_KEY), the pull sends SetData(DATA_CREW_FIGHT, IN_PROGRESS) (the instance sets the four to
 *   CrewMode::Boss), a wipe NOT_STARTED (the instance restores all five and reopens the path), the end DONE (credit
 *   213841, the modes by path, the door watch). Slot 6 is never a BossAI's.
 * - Mechanics: BC1-BC13 (Gang Up, Bodyguard, Ambush, Gouge, Greater Heal, Rain of Fire, heroic Focus Fire, Singled Out,
 *   Set Up, Seed, No One Left Behind, Avenge), the Test's 30% yields; the stash chest with the crew list and the rod
 *   (section 7 #19 A).
 * - Add scripts (registered here by WP-D5, in the change that declares the creature): none (the crew are CR's; the
 *   stash chest GO 301360 / 301361 is hand SQL in this WP's rev).
 * - Host-testable logic in CrewFightLogic.h (spell ids in kSpellsCrewFight, 214030-214069),
 *   tests/zf_crewfight_test.cpp, one `.dbtest zf blyfight <mechanic>` subcommand per mechanic, the descriptor
 *   (Mechanic::Describe), texts 7604 groups 3-4 (CR's rev inserts them). Own SQL rev:
 *   data/sql/updates/pending_db_world/rev_bly_crew_fight_zul_farrak.sql (the stock SmartAI is dropped by S0's
 *   rev_skeleton_zul_farrak.sql).
 * - Rules (handoff section 3.5 rules 1-36, RB-1..RB-22, LESSONS L1-L9): ZulFarrak::NoAssist(me) first in UpdateAI (rule
 *   27, host-tested); loot and hard mode bits are the instance's, never in JustDied; emotes type 41; custom damage
 *   spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (script hits NO_REDIRECTION | NO_REFLECTION too); percent hits via
 *   DungeonKit::RefFlat / RefFlatOn with the boss as the owner; no summoned unit in ObjectData; _visuals.py constants
 *   only; every bot shape `.Within(PlazaFloorBounds())`; kickable casts and bars by the kick table (rule 24, LESSONS
 *   L2), dispels by rule 25; cleanup on reset, evade and death; mechanics include the tank; one log line per firing
 *   (DungeonKit::LogMechanic(kLogDungeon, ...)) and the pull line (OnBossPull, already here); every number a static
 *   constexpr in the Logic header's Tune (rule 32), health from ZulFarrakRework.h Health; the DC contract in the
 *   report.
 */

#include "Chat.h"
#include "CrewFightLogic.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_BLY, BOSS_CREW);
    }

    ChatCommandTable const& BlyfightTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_bly_crew_fight_rework()
{
    ZfTest::RegisterBoss("blyfight", BlyfightTestCommands());
}
