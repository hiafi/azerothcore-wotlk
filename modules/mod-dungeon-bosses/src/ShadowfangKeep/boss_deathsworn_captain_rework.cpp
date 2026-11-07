/*
 * mod-dungeon-bosses, Shadowfang Keep: Deathsworn Captain (WP-S6). Build spec: SK 1044-1083 (build spec), SK 956-1043
 * (design), DC1-DC3; handoff section 3.5 rows DC and section 3.6 row S6.
 *
 * STUB from WP-K (the SFK layer): a plain melee BossAI on boss state BOSS_DEATHSWORN_CAPTAIN that begins the registry
 * encounter, bound by apps/dbc-tools source/npcs/shadowfang_keep/deathsworn_captain.py (ScriptName, AIName '', normal
 * health, immunities 1972), plus `.sfktest captain info`. WP-S6 owns this file, DeathswornCaptainLogic.h,
 * tests/sfk_deathsworn_captain_test.cpp, the DT file and its own SQL rev; shared files (ShadowfangKeepRework.h, the
 * instance, the loader, _common.py, tests/run.sh) are WP-K's: ask the orchestrator in the report.
 *
 * TODO(WP-S6), handoff section 3.6 row S6:
 *   - DC1 Deathsworn Charge / DC2 heroic Chain Charge: DungeonKit::LineStrike (3 / 5 / 4, warn 2 s, 35%, Weakened, clip
 *     DeathswornCaptainArena: on the walkway only along it); the chain starts at result.end, 1.5 s apart; then
 *     MoveCharge. Heroic sign-off waits on the Deadmines G8 sweep (handoff section 3.9).
 *   - DC3 Sweeping Cleave: CastBar 2 s + Cone(90, 10, TankExempt).Damage(40).Weakened(); the tank takes 2 swings.
 *   - Heroic Last Stand.
 *   - The 15% roll is the instance's (DATA_CAPTAIN_ROLL, RollOnce, saved; it despawns him on Absent). His patrol (path
 *     1345170) stays; he turns in Odo's doorway (handoff section 7 #25: his arena is the north hall plus the walkway,
 *     ArenaGuard grips back anyone who falls).
 *   - SQL rev: drop SmartAI 3872 (despawn roll, 7165, 15496, 9080); creature_text 0-1.
 *   - DT deathsworn_captain.py: spells 206010-206019 only.
 *   - ArenaGuard on DeathswornCaptainArena(); tests in tests/sfk_deathsworn_captain_test.cpp.
 *
 * Pilot lessons (handoff section 4): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit through
 * LaunchTarget + SetEffectValue; visuals and timers never ride a scheduler the cast bar pauses; SaveToDB after a
 * saved data change; mechanic emotes are type 41; every hit has a visible impact; filled circles only for real
 * threats (a range cue is an outline, NoFillTimer); telegraph shapes match the room; the boss cannot be kited off
 * its arena (DungeonKit::ArenaGuard on DeathswornCaptainArena()). Log each firing with DungeonKit::LogMechanic("sfk",
 * "captain", "<mechanic>", ...).
 */

#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DeathswornCaptainLogic.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include <string>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

// Deathsworn Captain 3872
struct boss_deathsworn_captain_rework : public BossAI
{
    explicit boss_deathsworn_captain_rework(Creature* creature) : BossAI(creature, BOSS_DEATHSWORN_CAPTAIN) { }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_DEATHSWORN_CAPTAIN;
        Mechanic::BeginEncounter(me, options);
        DungeonKit::LogMechanic(kLogDungeon, "captain", "engage",
            std::string("heroic=") + (DungeonKit::IsHeroicMap(me) ? "1" : "0"));
    }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_DEATHSWORN_CAPTAIN, BOSS_DEATHSWORN_CAPTAIN);
    }

    ChatCommandTable const& DeathswornCaptainTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_deathsworn_captain_rework()
{
    RegisterDungeonReworkCreatureAI(boss_deathsworn_captain_rework, ShadowfangKeepRework::kInstanceScriptName);
    SfkTest::RegisterBoss("captain", DeathswornCaptainTestCommands());
}
