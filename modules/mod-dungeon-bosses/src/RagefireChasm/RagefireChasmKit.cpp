/*
 * mod-dungeon-bosses, Ragefire Chasm: the Ragefire Chasm skeleton's engine glue (RagefireChasmKit.h).
 */

#include "RagefireChasmKit.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "MotionMaster.h"
#include "StringFormat.h"
#include "Timer.h"
#include "Unit.h"
#include "UnitDefines.h"
#include <utility>
#include <vector>

namespace RagefireChasmRework
{
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss)
    {
        DungeonKit::LeashSpec spec;
        spec.bossGraceMs = kLeashBossGraceMs;
        spec.noTargetInsideMs = kLeashNoTargetMs;
        spec.switchToInside = kLeashSwitchToInside;
        return DungeonKit::LeashPreset(std::string(kLogDungeon) + " " + boss + " arena", spec);
    }

    DungeonKit::ArenaGuardOptions SelfLeash(std::string const& boss)
    {
        DungeonKit::ArenaGuardOptions o = LeashOptions(boss);
        o.switchWhenVictimOff = false;
        o.holdWhileVictimOff = false;
        o.evadeNoTargetInsideMs = 0;
        return o;
    }

    DungeonKit::ArenaGuardOptions ReachLeash(std::string const& boss)
    {
        DungeonKit::ArenaGuardOptions o = LeashOptions(boss);
        o.evadeWhenBossOff = false;
        o.logPrefix += " reach";
        return o;
    }

    // MoveBackwardsChecks is not virtual, its countdown is public: put back while the step would end off his arena.
    void ArenaEdge::HoldBackstep(Creature* boss) const
    {
        Unit const* victim = boss->GetVictim();
        if (victim && boss->IsWithinMeleeRange(victim) && !BackstepStays(_polygon, DungeonKit::PlaneOf(boss),
            DungeonKit::PlaneOf(victim), boss->GetMeleeRange(victim) / 2.f))
            boss->m_moveBackwardsMovementTime = Creature::MOVE_BACKWARDS_CHECK_INTERVAL;
    }

    void ArenaEdge::Update(Creature* boss, DungeonKit::ArenaGuard const& arena, DungeonKit::ArenaGuard const& reach)
    {
        Unit* victim = boss->GetVictim();
        if (!victim || boss->HasUnitState(UNIT_STATE_JUMPING) || boss->IsFalling())
            return;
        MotionMaster* motion = boss->GetMotionMaster();
        EdgeView view;
        view.self = DungeonKit::PlaneOf(boss);
        view.target = DungeonKit::PlaneOf(victim);
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
        if (walking ? DungeonKit::Distance(step.spot, _spot) < kRepathYd
            : view.selfInside && DungeonKit::Distance(step.spot, view.self) < kThereYd)
            return;     // on the way, or there
        uint32 const now = getMSTime();
        if (!walking && _walkedAtMs && getMSTimeDiff(_walkedAtMs, now) < kRepathMs
            && DungeonKit::Distance(step.spot, _spot) < kThereYd)
            return;     // the last walk to it ended short: again in a moment
        _walkedAtMs = now;
        _spot = step.spot;
        motion->MovePoint(0, _spot.x, _spot.y, _floor(_spot, victim->GetPositionZ()).value_or(boss->GetPositionZ()));
    }

    void ArenaEdge::Reset()
    {
        _walkedAtMs = 0;
        _held = false;
    }

    void OnBossPull(Creature* boss, char const* bossKey, bool hardMode)
    {
        if (!boss)
            return;
        DungeonKit::LogMechanic(kLogDungeon, bossKey, "pull", Acore::StringFormat("health={} heroic={} hardmode={}",
            boss->GetMaxHealth(), DungeonKit::IsHeroicMap(boss) ? 1 : 0, hardMode ? 1 : 0));
    }

    BossMechanics::SpotBounds BoundsOf(Arena const& arena)
    {
        BossMechanics::SpotBounds bounds;
        for (ArenaRegion const& region : arena.regions)
        {
            if (region.kind != ArenaRegion::Kind::Polygon)
                continue;       // every Ragefire Chasm arena is a polygon
            std::vector<Position> points;
            points.reserve(region.polygon.size());
            for (Vec2 const& p : region.polygon)
                points.emplace_back(p.x, p.y, 0.f);
            bounds.Polygon(std::move(points), region.zMin, region.zMax);
        }
        return bounds;
    }

    BossMechanics::SpotBounds OggleflintFloorBounds()
    {
        return BoundsOf(OggleflintArena());
    }

    BossMechanics::SpotBounds JergoshFloorBounds()
    {
        return BoundsOf(JergoshArena());
    }

    BossMechanics::SpotBounds BazzalanFloorBounds()
    {
        return BoundsOf(BazzalanArena());
    }

    BossMechanics::SpotBounds TaragamanFloorBounds()
    {
        return BoundsOf(TaragamanArena());
    }

    // The Deadmines' SetVanCleefHidden, visible (section 7 #9 A). NOT_SELECTABLE keeps assist calls, AoE and pets off
    // him; the flag also remembers that the gate set his react state, so an open gate touches nothing.
    bool ApplyTaragamanGate(Creature* taragaman)
    {
        if (!taragaman || !taragaman->IsAlive())
            return false;
        InstanceScript* instance = taragaman->GetInstanceScript();
        if (!instance)
            return false;

        bool const dormant = instance->GetData(DATA_TARAGAMAN_DORMANT) != 0;
        if (dormant)
        {
            taragaman->SetImmuneToAll(true);
            taragaman->SetReactState(REACT_PASSIVE);
            taragaman->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        }
        else if (taragaman->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE))
        {
            taragaman->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            taragaman->SetImmuneToAll(false);
            taragaman->SetReactState(REACT_AGGRESSIVE);
        }
        return dormant;
    }
}
