/*
 * mod-dungeon-bosses, Scholomance: the Scholomance kit's engine glue (ScholomanceKit.h).
 */

#include "ScholomanceKit.h"
#include "Creature.h"
#include "DungeonKit.h"
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
        _failed = std::make_shared<std::unordered_set<uint64>>();
        if (!boss)
            return;
        std::shared_ptr<std::unordered_set<uint64>> const failed = _failed;
        Mechanic::OnFailure(boss, [failed, chain = std::move(chain)](BossMechanics::FailureEvent const& ev)
        {
            // Group failures (a missed soak: no player) never cost a grade (handoff section 7 #18).
            if (!ev.player.IsEmpty())
                failed->insert(ev.player.GetRawValue());
            if (chain)
                chain(ev);
        });
    }

    bool GradeWatch::HasFailed(ObjectGuid player) const
    {
        return _failed && _failed->count(player.GetRawValue());
    }

    uint32 GradeWatch::AwardAtDeath(Creature* boss)
    {
        if (!_active || !boss || !DungeonKit::IsHeroicMap(boss))
            return 0;
        InstanceScript* instance = boss->GetInstanceScript();
        if (!instance)
            return 0;
        uint32 awarded = 0;
        for (auto const& ref : boss->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || player->IsGameMaster() || HasFailed(player->GetGUID()))
                continue;
            instance->SetGuidData(DataPassingGrade(_who), player->GetGUID());
            ++awarded;
        }
        DungeonKit::LogMechanic(kLogDungeon, kInstructorNames[std::size_t(_who)], "passing-grades",
            Acore::StringFormat("awarded={} failed={}", awarded, FailedCount()));
        _active = false;
        return awarded;
    }

    void GradeWatch::Reset()
    {
        _active = false;
        _failed.reset();
    }

    InstanceApi* GetInstanceApi(InstanceScript* instance)
    {
        return dynamic_cast<InstanceApi*>(instance);
    }
}
