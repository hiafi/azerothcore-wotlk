/*
 * mod-dungeon-bosses, Scholomance S8:
 * The Ravenian (10507) and Master Corvane.
 * STUB written by WP-KS (the Scholomance kit); WP-S8 owns this file from now on.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_RAVENIAN (the instance's boss state: doors, Gandling's reveal, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (RavenianArena, LeashOptions: no grips);
 * - Passing Grades (GradeWatch, heroic);
 * - an engage / death log line and `.dbtest scholo ravenian info`.
 *
 * TODO(WP-S8):
 * - SC 2193-2259; handoff section 3.5 row S8, section 3.6 (normal 160k (Corvane 50k), heroic 210k (Corvane 65k); the
 *   normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's overrides).
 * - Mechanics: RV1 Trample, RV2 Sweep, RV3 Smash, RV4 Order rotation, RV5 Transition, RV6 Unbound, RV7 Driven (H,
 *   uncapped, ruling 24), RV8 Mend Construct, RV9 Shadow Bolt, RV10 Bereaved, RV11 Sundering Cleave.
 * - Data: drop SmartAI 10507 x5; creature_text per ScholomanceRework.h's text enum (your SQL rev); your own
 *   DamageModifier (the live value is a mod-progression leftover, handoff section 2.3).
 * - Adds: Master Corvane 300542 (display 23277, 1972, unattackable until the Ravenian is below half), perch
 *   kCorvanePerch (no navmesh, height in game), landing kCorvaneLandings.
 * - User 2026-11-08: "Rivian can be sitting here" = kRavenianUserSpot (ScholomanceRework.h). It lies in Gandling's
 *   study, not the vault: confirm with the user whose spot it is before using it.
 * - Detention (S11, handoff section 3.7): write this room's solo lesson as a ScholomanceRework::TimedSoloLesson
 *   (SoloLesson.h) and register it from AddSC_ with RegisterSoloLesson(Classroom::RavenianVault, ...).
 * - Hard mode (S13): an examiner mode of this AI for the Graduate Examiner entry (ScholomanceRework.h
 *   NPC_SC_EXAMINER_*), both mechanics at heroic values, 80k (the Ravenian 60k, Corvane 20k).
 * - Passing Grades: GradeWatch is wired (Begin on the pull, AwardAtDeath at the death, heroic only): keep both calls; a
 *   boss with its own OnFailure handler passes it to Begin as `chain`.
 * - The classroom gate closes on the pull and opens on the death or a wipe by itself (the instance's door data on this
 *   boss state); the arena leash is the backstop.
 * - Arena: RavenianArena() with LeashOptions (no grips; hold at the edge, evade after 10 s with nobody inside). Tighten
 *   it in your own file if the room needs it.
 * - Host-testable logic in RavenianLogic.h (spell ids in kSpellsRavenian), one `.dbtest scholo ravenian <mechanic>`
 *   subcommand per mechanic, the descriptor (Mechanic::Describe), the registry calls of handoff section 3.4.
 * - Pilot lessons (handoff section 2.2): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit through
 *   LaunchTarget + SetEffectValue (tank hits too, so defensives work); every custom damage spell uses
 *   DungeonKit::RefFlat (DD never scales ids >= 200000); emotes are type 41; SaveToDB after a saved data change; no
 *   summoned unit in ObjectData; visuals and timers that must run during a cast never ride BossAI's paused scheduler;
 *   every hit has a visible impact; filled circles only for real threats (a range cue is an outline, NoFillTimer);
 *   telegraph shapes match the room; one log category module.dungeonbosses (DungeonKit::LogMechanic(kLogDungeon, ...)).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "RavenianLogic.h"
#include "ScholomanceRework.h"
#include "ScholomanceKit.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;

namespace
{
    char const* const kBossLogName = "ravenian";
}

struct boss_the_ravenian_rework : public BossAI
{
    explicit boss_the_ravenian_rework(Creature* creature)
        : BossAI(creature, BOSS_RAVENIAN), _arena(RavenianArena(), LeashOptions(kBossLogName)) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
        _grades.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RAVENIAN;
        Mechanic::BeginEncounter(me, options);
        _grades.Begin(me, Instructor::Ravenian);
        _arena.Engage(me);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", DungeonKit::IsHeroicMap(me) ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _arena.Reset();
        _grades.Reset();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        _grades.AwardAtDeath(me);
        BossAI::JustDied(killer);
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        events.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
    GradeWatch _grades;
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_RAVENIAN, BOSS_RAVENIAN);
    }

    ChatCommandTable const& RavenianTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_the_ravenian_rework()
{
    RegisterDungeonReworkCreatureAI(boss_the_ravenian_rework, ScholomanceRework::kInstanceScriptName);
    ScholoTest::RegisterBoss("ravenian", RavenianTestCommands());
}
