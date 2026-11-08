/*
 * mod-dungeon-bosses, Scholomance S9:
 * Lord Alexei Barov (10504).
 * STUB written by WP-KS (the Scholomance kit); WP-S9 owns this file from now on.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_ALEXEI (the instance's boss state: doors, Gandling's reveal, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (AlexeiArena, LeashOptions: no grips);
 * - Passing Grades (GradeWatch, heroic);
 * - an engage / death log line and `.dbtest scholo alexei info`.
 *
 * TODO(WP-S9):
 * - SC 2460-2533; handoff section 3.5 row S9, section 3.6 (normal 160k, heroic 250k; the normal HealthModifier is set
 *   by the dbc-tools stub, heroic is WP-H's overrides).
 * - Mechanics: AB1 Rule, AB2 No running, AB3 Assembly, AB4 Keep your distance, AB5 Out of bounds, AB6 Line up (H), AB7
 *   To your desks (H), AB8 Heroic pairs, AB9 Demerit and the Dean's Rod (ruling 19), AB10 The Barov fortune, AB11 Veil
 *   of Shadow, AB12 Unholy Aura (stock 17467, on aggro).
 * - Data: drop SmartAI 10504 x4; formation 48863 -> 48862 / 48864 and their linked_respawn rows deleted; creature_text
 *   per ScholomanceRework.h's text enum (your SQL rev); your own DamageModifier (the live value is a mod-progression
 *   leftover, handoff section 2.3).
 * - Adds: the Barov fortune 300543 (GODI 2614 look). Thirds kBarovThirdsY, lane kBarovLaneMinX/MaxX, desks kBarovDesks.
 * - The Dean's Rod rides OnFailure: pass its handler to GradeWatch::Begin as `chain` (the registry keeps one failure
 *   handler per encounter).
 * - Detention (S11, handoff section 3.7): write this room's solo lesson as a ScholomanceRework::TimedSoloLesson
 *   (SoloLesson.h) and register it from AddSC_ with RegisterSoloLesson(Classroom::BarovVault, ...).
 * - Hard mode (S13): an examiner mode of this AI for the Graduate Examiner entry (ScholomanceRework.h
 *   NPC_SC_EXAMINER_*), both mechanics at heroic values, 80k (the Ravenian 60k, Corvane 20k).
 * - Passing Grades: GradeWatch is wired (Begin on the pull, AwardAtDeath at the death, heroic only): keep both calls; a
 *   boss with its own OnFailure handler passes it to Begin as `chain`.
 * - The classroom gate closes on the pull and opens on the death or a wipe by itself (the instance's door data on this
 *   boss state); the arena leash is the backstop.
 * - Arena: AlexeiArena() with LeashOptions (no grips; hold at the edge, evade after 10 s with nobody inside). Tighten
 *   it in your own file if the room needs it.
 * - Host-testable logic in AlexeiLogic.h (spell ids in kSpellsAlexei), one `.dbtest scholo alexei <mechanic>`
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
#include "AlexeiLogic.h"
#include "ScholomanceRework.h"
#include "ScholomanceKit.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;

namespace
{
    char const* const kBossLogName = "alexei";
}

struct boss_lord_alexei_barov_rework : public BossAI
{
    explicit boss_lord_alexei_barov_rework(Creature* creature)
        : BossAI(creature, BOSS_ALEXEI), _arena(AlexeiArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_ALEXEI;
        Mechanic::BeginEncounter(me, options);
        _grades.Begin(me, Instructor::Alexei);
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
        return ScholoTest::ShowBossInfo(handler, NPC_ALEXEI, BOSS_ALEXEI);
    }

    ChatCommandTable const& AlexeiTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_lord_alexei_barov_rework()
{
    RegisterDungeonReworkCreatureAI(boss_lord_alexei_barov_rework, ScholomanceRework::kInstanceScriptName);
    ScholoTest::RegisterBoss("alexei", AlexeiTestCommands());
}
