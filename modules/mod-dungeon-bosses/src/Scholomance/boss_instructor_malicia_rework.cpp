/*
 * mod-dungeon-bosses, Scholomance S5:
 * Instructor Malicia (10505).
 * STUB written by WP-KS (the Scholomance kit); WP-S5 owns this file from now on.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_MALICIA (the instance's boss state: doors, Gandling's reveal, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (MaliciaArena, LeashOptions: no grips);
 * - Passing Grades (GradeWatch, heroic);
 * - an engage / death log line and `.dbtest scholo malicia info`.
 *
 * TODO(WP-S5):
 * - SC 1431-1488; handoff section 3.5 row S5, section 3.6 (normal 160k, heroic 250k; the normal HealthModifier is set
 *   by the dbc-tools stub, heroic is WP-H's overrides).
 * - Mechanics: MA1 Soul, MA2 Soul Drain, MA3 Loose Soul, MA4 Call a Student, MA5 Bound Soul, MA6 Soulstorm, MA7 Shadow
 *   Heal, MA8 Slow (stock 13747), MA9 Corruption (stock 18376).
 * - Data: drop SmartAI 10505 x7; creature_text per ScholomanceRework.h's text enum (your SQL rev); your own
 *   DamageModifier (the live value is a mod-progression leftover, handoff section 2.3).
 * - Adds: Malicia's Shade 300536 (display 4629), Loose Soul 300537 (wisp 1825, handoff section 7 #20). Her room trash
 *   keeps the stock npc_scholomance_occultist AI (Dark Shade at 30%).
 * - Heroic: everyone drained, 5 s fade, two shades, a Soulstorm circle per player.
 * - Detention (S11, handoff section 3.7): write this room's solo lesson as a ScholomanceRework::TimedSoloLesson
 *   (SoloLesson.h) and register it from AddSC_ with RegisterSoloLesson(Classroom::Coven, ...).
 * - Hard mode (S13): an examiner mode of this AI for the Graduate Examiner entry (ScholomanceRework.h
 *   NPC_SC_EXAMINER_*), both mechanics at heroic values, 80k (the Ravenian 60k, Corvane 20k).
 * - Passing Grades: GradeWatch is wired (Begin on the pull, AwardAtDeath at the death, heroic only): keep both calls; a
 *   boss with its own OnFailure handler passes it to Begin as `chain`.
 * - The classroom gate closes on the pull and opens on the death or a wipe by itself (the instance's door data on this
 *   boss state); the arena leash is the backstop.
 * - Arena: MaliciaArena() with LeashOptions (no grips; hold at the edge, evade after 10 s with nobody inside). Tighten
 *   it in your own file if the room needs it.
 * - Host-testable logic in MaliciaLogic.h (spell ids in kSpellsMalicia), one `.dbtest scholo malicia <mechanic>`
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
#include "MaliciaLogic.h"
#include "ScholomanceRework.h"
#include "ScholomanceKit.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;

namespace
{
    char const* const kBossLogName = "malicia";
}

struct boss_instructor_malicia_rework : public BossAI
{
    explicit boss_instructor_malicia_rework(Creature* creature)
        : BossAI(creature, BOSS_MALICIA), _arena(MaliciaArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_MALICIA;
        Mechanic::BeginEncounter(me, options);
        _grades.Begin(me, Instructor::Malicia);
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
        return ScholoTest::ShowBossInfo(handler, NPC_MALICIA, BOSS_MALICIA);
    }

    ChatCommandTable const& MaliciaTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_instructor_malicia_rework()
{
    RegisterDungeonReworkCreatureAI(boss_instructor_malicia_rework, ScholomanceRework::kInstanceScriptName);
    ScholoTest::RegisterBoss("malicia", MaliciaTestCommands());
}
