/*
 * mod-dungeon-bosses, Scholomance: the Scholomance kit's engine glue (ScholomanceKit.h).
 */

#include "ScholomanceKit.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GraduateExamLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "Player.h"
#include "StringFormat.h"
#include <utility>

namespace ScholomanceRework
{
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss)
    {
        DungeonKit::ArenaGuardOptions o;
        o.gripOnPull = false;
        o.gripBack = false;
        o.holdWhileVictimOff = true;
        o.switchWhenVictimOff = kLeashSwitchToInside;
        o.evadeWhenBossOff = true;
        o.bossGraceMs = kLeashBossGraceMs;
        o.evadeNoTargetInsideMs = kLeashNoTargetMs;
        o.logPrefix = "scholo " + boss + " arena";
        return o;
    }

    void ApplyGandlingReveal(Creature* gandling, bool revealed)
    {
        if (!gandling || !gandling->IsAlive())
            return;
        gandling->SetVisible(revealed);
        gandling->SetFaction(revealed ? kGandlingRevealedFaction : kGandlingHiddenFaction);
    }

    void GradeWatch::Begin(Creature* boss, Instructor who,
        std::function<void(BossMechanics::FailureEvent const&)> chain)
    {
        _who = who;
        _active = boss != nullptr;
        _ledger = std::make_shared<GradeLedger>();
        if (!boss)
            return;
        std::shared_ptr<GradeLedger> const ledger = _ledger;
        Mechanic::OnFailure(boss, [ledger, chain = std::move(chain)](BossMechanics::FailureEvent const& ev)
        {
            // Group failures (a missed soak: no player) never cost a grade (handoff section 7 #18); nor does a hit
            // the boss exempted for that player (Exempt).
            ledger->Record(ev.mechanicId, ev.player.GetRawValue());
            if (chain)
                chain(ev);
        });
    }

    void GradeWatch::Exempt(BossMechanics::MechanicHandle mechanic, ObjectGuid player)
    {
        if (_active && _ledger)
            _ledger->Exempt(mechanic.id, player.GetRawValue());
    }

    bool GradeWatch::HasFailed(ObjectGuid player) const
    {
        return _ledger && _ledger->HasFailed(player.GetRawValue());
    }

    uint32 GradeWatch::AwardAtDeath(Creature* boss)
    {
        // Grades come from a real instructor fight only: never from a stub before wave B binds the instructors
        // (kWaveBBound, R-A S-11).
        if (!kWaveBBound || !_active || !boss || !DungeonKit::IsHeroicMap(boss))
            return 0;
        InstanceScript* instance = boss->GetInstanceScript();
        if (!instance)
            return 0;
        // Only the players in the instructor's arena at the death (an unreleased body counts; orchestrator ruling
        // 2026-11-08): ScholoGraduateExam::EarnsPassingGrade.
        DungeonKit::Arena const arena = ScholoGraduateExam::GradeArena(_who);
        uint32 awarded = 0;
        uint32 away = 0;
        for (auto const& ref : boss->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player)
                continue;
            ScholoGraduateExam::GradeCandidate c;
            c.gameMaster = player->IsGameMaster();
            c.failed = HasFailed(player->GetGUID());
            c.released = player->HasPlayerFlag(PLAYER_FLAGS_GHOST);
            c.inArena = player->IsInWorld() && arena.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ());
            if (!ScholoGraduateExam::EarnsPassingGrade(c))
            {
                if (!c.gameMaster && !c.failed)
                    ++away;
                continue;
            }
            instance->SetGuidData(DataPassingGrade(_who), player->GetGUID());
            ++awarded;
        }
        DungeonKit::LogMechanic(kLogDungeon, kInstructorNames[std::size_t(_who)], "passing-grades",
            Acore::StringFormat("awarded={} failed={} away={}", awarded, FailedCount(), away));
        _active = false;
        return awarded;
    }

    void GradeWatch::Reset()
    {
        _active = false;
        _ledger.reset();
    }

    InstanceApi* GetInstanceApi(InstanceScript* instance)
    {
        return dynamic_cast<InstanceApi*>(instance);
    }
}
