/*
 * mod-dungeon-bosses, Scholomance S11:
 * Darkmaster Gandling (1853), normal and heroic, and the detention cycle.
 * STUB written by WP-KS (the Scholomance kit); WP-S11 owns this file from now on (S13 adds the hard mode).
 *
 * What the stub does:
 * - a melee BossAI on BOSS_GANDLING (stock slot 3; the instance's door data shuts the entrance gate 177374 and the six
 *   classroom gates while he fights, and opens them on his death, a wipe or an evade);
 * - hidden until the six instructors are DONE: Reset applies the instance's DATA_GANDLING_REVEALED (invisible and
 *   faction 35, or visible and faction 21; ApplyGandlingReveal); the instance yells "School is in session!" through
 *   this AI (Talk(0)) and calls DoAction(kActionGandlingRevealed) when the sixth instructor dies;
 * - the registry encounter, the arena leash (GandlingArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest scholo gandling info`.
 *
 * TODO(WP-S11):
 * - SC 3034-3101; handoff section 3.5 row S11, sections 3.6 (normal 280k, heroic 400k) and 3.7 (detention).
 * - Mechanics: GD1 Detention (the cycle: ScholomanceRework::CreateSoloLesson(room) per detention, owned by a lesson
 *   stalker 300546; teleport to kClassroomLandings, the gate via SetData(DataClassroomGate(room), 0 / 1), who is
 *   detained via SetGuidData(DataDetained(room), guid); 15 s; the return portal; Abort() every lesson on a wipe, his
 *   evade or death), GD2 Honor Roll, GD3 Expelled Student, GD4 Portal Volley (kStudyPortalPoints), GD4b Transfer (H).
 * - Data: the stock boss_darkmaster_gandling stays untouched (new name, bound by the dbc-tools stub); drop his 12
 *   dormant SmartAI rows; retire the Risen Guardian 11598; creature_text 1-6 (group 0 is stock).
 * - Adds: Expelled Student 300544 (display 9784), the Ravenian's echo 300545, the lesson and portal stalkers
 *   300546-300547 (declared by S11).
 * - Detention safety (handoff section 3.7): a detained student who dies, logs out or is the last one alive ends the
 *   lesson (TimedSoloLesson does) and opens the gate; the instance clears every DataDetained slot when his state leaves
 *   IN_PROGRESS and the door data opens every gate.
 * - S13: the Graduate Exam (gauntlet, examiners, final phase 200k; GetData(DATA_GANDLING_HARD_MODE)); the loot bit is
 *   the instance's.
 * - Pilot lessons: see any KS stub's list (boss_jandice_barov_rework.cpp).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GandlingLogic.h"
#include "InstanceScript.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;

namespace
{
    char const* const kBossLogName = "gandling";
}

struct boss_darkmaster_gandling_rework : public BossAI
{
    explicit boss_darkmaster_gandling_rework(Creature* creature)
        : BossAI(creature, BOSS_GANDLING), _arena(GandlingArena(), LeashOptions(kBossLogName)) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
        // Hidden until the six instructors are DONE (stock: Reset read the raw counter).
        ApplyGandlingReveal(me, instance && instance->GetData(DATA_GANDLING_REVEALED));
    }

    void DoAction(int32 action) override
    {
        if (action == kActionGandlingRevealed)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "revealed");
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_GANDLING;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} hardmode={} at=({:.1f}, {:.1f}, {:.1f})",
                DungeonKit::IsHeroicMap(me) ? 1 : 0, instance ? instance->GetData(DATA_GANDLING_HARD_MODE) : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
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
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off the study, or nobody in it for 10 s: evading

        events.Update(diff);
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
        return ScholoTest::ShowBossInfo(handler, NPC_GANDLING, BOSS_GANDLING);
    }

    ChatCommandTable const& GandlingTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_darkmaster_gandling_rework()
{
    RegisterDungeonReworkCreatureAI(boss_darkmaster_gandling_rework, ScholomanceRework::kInstanceScriptName);
    ScholoTest::RegisterBoss("gandling", GandlingTestCommands());
}
