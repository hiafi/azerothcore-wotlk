/*
 * mod-dungeon-bosses, the shared dungeon kit: a boss at the edge of his arena (DungeonKitArenaEdge.h, Zul'Farrak
 * WP-KT). The engine half is Ragefire Chasm's RagefireChasmKit.cpp ArenaEdge, SelfLeash and ReachLeash, moved as
 * they are.
 */

#include "DungeonKitArenaEdge.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "MotionMaster.h"
#include "Timer.h"
#include "Unit.h"
#include "UnitDefines.h"
#include <utility>

namespace DungeonKit::EdgeFight
{
    ArenaGuardOptions SelfLeash(ArenaGuardOptions base)
    {
        base.switchWhenVictimOff = false;
        base.holdWhileVictimOff = false;
        base.evadeNoTargetInsideMs = 0;
        return base;
    }

    ArenaGuardOptions ReachLeash(ArenaGuardOptions base)
    {
        base.evadeWhenBossOff = false;
        base.logPrefix += " reach";
        return base;
    }

    ArenaEdge::ArenaEdge(std::span<Vec2 const> polygon, FloorFn floor)
    {
        Configure(polygon, std::move(floor));
    }

    void ArenaEdge::Configure(std::span<Vec2 const> polygon, FloorFn floor)
    {
        _polygon.assign(polygon.begin(), polygon.end());
        _floor = std::move(floor);
        Reset();
    }

    // MoveBackwardsChecks is not virtual, its countdown is public: put back while the step would end off his arena.
    void ArenaEdge::HoldBackstep(Creature* boss) const
    {
        if (!boss || _polygon.empty())
            return;
        Unit const* victim = boss->GetVictim();
        if (victim && boss->IsWithinMeleeRange(victim) && !BackstepStays(_polygon, PlaneOf(boss), PlaneOf(victim),
            boss->GetMeleeRange(victim) / 2.f))
            boss->m_moveBackwardsMovementTime = Creature::MOVE_BACKWARDS_CHECK_INTERVAL;
    }

    void ArenaEdge::Update(Creature* boss, ArenaGuard const& arena, ArenaGuard const& reach)
    {
        if (!boss || _polygon.empty())
            return;
        Unit* victim = boss->GetVictim();
        if (!victim || boss->HasUnitState(UNIT_STATE_JUMPING) || boss->IsFalling())
            return;
        MotionMaster* motion = boss->GetMotionMaster();
        EdgeView view;
        view.self = PlaneOf(boss);
        view.target = PlaneOf(victim);
        view.selfInside = arena.Contains(boss);
        view.targetInside = arena.Contains(victim);
        view.targetInReach = reach.Contains(victim);
        view.inMelee = boss->IsWithinMeleeRange(victim);
        EdgeStep const step = NextEdgeStep(_polygon, view);
        if (step.act == EdgeAct::Chase)
        {
            if (_held)
                motion->MoveChase(victim);
            _held = false;
            return;
        }
        _held = true;
        if (motion->GetCurrentMovementGeneratorType() == CHASE_MOTION_TYPE)
        {
            motion->Clear(false);
            boss->StopMoving();
        }
        bool const walking = motion->GetCurrentMovementGeneratorType() == POINT_MOTION_TYPE;
        if (step.act == EdgeAct::Stand)
        {
            if (!walking && view.inMelee)
                boss->SetInFront(victim);
            return;
        }
        if (walking ? Distance(step.spot, _spot) < kRepathYd
            : view.selfInside && Distance(step.spot, view.self) < kThereYd)
            return;     // on the way, or there
        uint32 const now = getMSTime();
        if (!walking && _walkedAtMs && getMSTimeDiff(_walkedAtMs, now) < kRepathMs
            && Distance(step.spot, _spot) < kThereYd)
            return;     // the last walk to it ended short: again in a moment
        _walkedAtMs = now;
        _spot = step.spot;
        float const z = _floor ? _floor(_spot, victim->GetPositionZ()).value_or(boss->GetPositionZ())
            : boss->GetPositionZ();
        motion->MovePoint(0, _spot.x, _spot.y, z);
    }

    void ArenaEdge::Reset()
    {
        _walkedAtMs = 0;
        _held = false;
    }
}
