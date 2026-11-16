/*
 * mod-dungeon-bosses, the shared dungeon kit: rolling front sequences (DungeonKitFronts.h, Blackrock Spire WP-KT-B2).
 */

#include "DungeonKitFronts.h"
#include "Creature.h"
#include "DungeonKitFields.h"
#include "Map.h"
#include "MoveSplineInit.h"
#include "ObjectAccessor.h"
#include "Random.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>
#include <cmath>
#include <string>

namespace DungeonKit
{
    namespace
    {
        // A carrier lingers this long past its front's end before its timer despawns it (the spline's last step).
        uint32 constexpr kCarrierTailMs = 1000;

        // The floor under (x, y) near `z` (kept when the floor is not found close by).
        float FloorZ(Unit const* ref, float x, float y, float z)
        {
            float const h = ref->GetMapHeight(x, y, z + 3.f);
            if (h <= INVALID_HEIGHT + 1.f || h < z - 8.f || h > z + 4.f)
                return z;
            return h;
        }

        // One carrier from `from` to `to` (2D; z from the floor) at `speed`, alive for `lifeMs`.
        ObjectGuid SpawnCarrier(Unit* owner, FrontCarrierSpec const& c, Vec2 from, Vec2 to, float z, float speed,
            uint32 lifeMs)
        {
            float const z0 = FloorZ(owner, from.x, from.y, z) + c.zOffset;
            float const z1 = FloorZ(owner, to.x, to.y, z) + c.zOffset;
            Position const at(from.x, from.y, z0, BearingTo(from, to));
            TempSummon* u = owner->SummonCreature(c.entry, at, TEMPSUMMON_TIMED_DESPAWN, lifeMs);
            if (!u)
                return ObjectGuid::Empty;
            if (c.aura)
                u->CastSpell(u, c.aura, true);
            if (Distance(from, to) > 0.1f && speed > 0.f)
            {
                Movement::MoveSplineInit init(u);
                init.MoveTo(to.x, to.y, z1, false, true);
                init.SetVelocity(speed);
                init.Launch();
            }
            return u->GetGUID();
        }
    }

    std::vector<Fronts::PoolCircle> PoolsOf(PuddleField const& field)
    {
        std::vector<Fronts::PoolCircle> out;
        uint64 const now = field.ClockMs();
        for (Puddle const& p : field.All())
            if (!p.Expired(now))
                out.push_back({ p.center, p.radius });
        return out;
    }

    // --------------------------------------------------------------------------------------------------------------
    // Start
    // --------------------------------------------------------------------------------------------------------------

    uint32 FrontDirector::StartRings(Unit* owner, Position const& apex, RingSequence spec)
    {
        if (!owner || !owner->IsInWorld() || _busy)
            return 0;
        std::vector<Fronts::RingStep> plan = Fronts::PlanRings(spec.plan);
        if (plan.empty())
        {
            LogMechanic(spec.dungeon, spec.boss, "ring-front-refused", "invalid ring plan");
            return 0;
        }
        Sequence s;
        s.id = _nextId++;
        s.rings = true;
        s.at = apex;
        s.startMs = _clockMs;
        s.ring = std::move(spec);
        s.plan = std::move(plan);
        for (Fronts::RingStep const& r : s.plan)
        {
            Step step;
            step.index = r.index;
            step.registerMs = r.registerMs;
            step.launchMs = r.launchMs;
            step.overMs = r.overMs;
            step.sliceBearing = r.sliceBearing;
            step.startYd = r.startYd;
            s.steps.push_back(step);
        }
        LogMechanic(s.ring.dungeon, s.ring.boss, "ring-front-start", "rings=" + std::to_string(s.steps.size())
            + " slice=" + std::to_string(static_cast<int>(s.ring.plan.sliceDeg)) + " turn="
            + std::to_string(static_cast<int>(s.ring.plan.turnDeg)));
        _seqs.push_back(std::move(s));
        uint32 const id = _seqs.back().id;
        _busy = true;
        Tick(owner, _seqs.back());
        _busy = false;
        return id;
    }

    uint32 FrontDirector::StartWalls(Unit* owner, Position const& start, WallSequence spec)
    {
        if (!owner || !owner->IsInWorld() || _busy || spec.walls == 0 || spec.travelYd <= 0.f || spec.widthYd <= 0.f
            || spec.speed <= 0.f || spec.bandYd < 0.5f || spec.gaps.gapYd <= 0.f)
        {
            LogMechanic(spec.dungeon, spec.boss, "wall-front-refused", "invalid wall sequence");
            return 0;
        }
        Sequence s;
        s.id = _nextId++;
        s.rings = false;
        s.at = start;
        s.startMs = _clockMs;
        s.wall = std::move(spec);
        uint32 const over = Fronts::WallOverMs(s.wall.travelYd, s.wall.speed);
        for (uint32 k = 0; k < s.wall.walls; ++k)
        {
            Step step;
            step.index = k;
            step.launchMs = s.wall.firstWarnMs + k * s.wall.spacingMs;
            step.registerMs = (k == 0 || !s.wall.revealAtPreviousLaunch) ? 0 : s.steps.back().launchMs;
            step.overMs = step.launchMs + over;
            s.steps.push_back(step);
        }
        LogMechanic(s.wall.dungeon, s.wall.boss, "wall-front-start", "walls=" + std::to_string(s.steps.size()));
        _seqs.push_back(std::move(s));
        uint32 const id = _seqs.back().id;
        _busy = true;
        Tick(owner, _seqs.back());
        _busy = false;
        return id;
    }

    // --------------------------------------------------------------------------------------------------------------
    // Clock
    // --------------------------------------------------------------------------------------------------------------

    void FrontDirector::Update(Unit* owner, uint32 diff)
    {
        _clockMs += diff;
        if (_seqs.empty())
            return;
        if (!owner || !owner->IsInWorld())
            return;
        _busy = true;
        for (Sequence& s : _seqs)
            Tick(owner, s);
        _busy = false;
        _seqs.erase(std::remove_if(_seqs.begin(), _seqs.end(), [](Sequence const& s)
        {
            if (s.rings && !s.cued && s.ring.onCue)
                return false;
            return std::all_of(s.steps.begin(), s.steps.end(), [](Step const& st)
            {
                return st.registered && st.launched && st.carriers.empty() && !st.front.IsValid();
            });
        }), _seqs.end());
    }

    void FrontDirector::Tick(Unit* owner, Sequence& s)
    {
        uint32 const elapsed = static_cast<uint32>(_clockMs - s.startMs);
        if (s.rings && !s.cued && s.ring.onCue && elapsed >= s.ring.cueMs)
        {
            s.cued = true;
            s.ring.onCue(s.at);
        }
        // Registration in step order (a wall's gap reads the previous wall's).
        for (Step& step : s.steps)
            if (!step.registered && elapsed >= step.registerMs)
                Register(owner, s, step, elapsed);
        for (Step& step : s.steps)
        {
            if (step.registered && !step.launched && elapsed >= step.launchMs)
                Launch(owner, s, step);
            if (step.launched && elapsed >= step.overMs + kCarrierTailMs)
            {
                Despawn(owner, step);
                step.front = {};    // over: the registry has dropped it
                step.safe = {};
            }
        }
    }

    Fronts::WallFrame FrontDirector::FrameOf(Sequence const& s) const
    {
        return { { s.at.GetPositionX(), s.at.GetPositionY() }, s.wall.facing, s.wall.travelYd, s.wall.widthYd };
    }

    void FrontDirector::Register(Unit* owner, Sequence& s, Step& step, uint32 elapsed)
    {
        step.registered = true;
        Milliseconds const warn(step.launchMs > elapsed ? step.launchMs - elapsed : 0);
        Unit const* parked = nullptr;
        bool const safe = s.rings ? s.ring.safeSlot : s.wall.safeSlot;
        ObjectGuid const parkedGuid = s.rings ? s.ring.parked : s.wall.parked;
        if (safe && !parkedGuid.IsEmpty())
            parked = ObjectAccessor::GetUnit(*owner, parkedGuid);

        if (s.rings)
        {
            BossMechanics::ConeFrontSpec spec;
            spec.sliceBearing = step.sliceBearing;
            spec.sliceDeg = s.ring.plan.sliceDeg;
            spec.startYd = step.startYd;
            spec.endYd = s.ring.plan.endYd;
            spec.bandYd = s.ring.plan.bandYd;
            // WP-SF: a ring with a next ring tells the bots' ring orbit which way the next slice turns
            spec.nextTurnDeg = step.index + 1 < s.steps.size() ? s.ring.plan.turnDeg : 0.f;
            spec.speed = s.ring.plan.speed;
            {
                BossMechanics::MechanicRef ref = Mechanic::ConeFront(owner, s.at, spec, warn);
                if (ref.IsValid())
                {
                    if (s.ring.within)
                        ref.Within(*s.ring.within);
                    if (s.ring.decorate)
                        s.ring.decorate(ref, step.index);
                }
                step.front = ref;
            }   // committed here
            if (step.front && safe && (parkedGuid.IsEmpty() || parked) && spec.sliceDeg > 0.f)
            {
                BossMechanics::MechanicRef ref = Mechanic::FrontSafe(owner, step.front, parked, s.ring.safeUntilYd);
                step.safe = ref;
            }
            return;
        }

        Fronts::WallFrame const frame = FrameOf(s);
        std::vector<Fronts::PoolCircle> const pools = s.wall.pools ? s.wall.pools()
            : std::vector<Fronts::PoolCircle>{};
        std::optional<float> previous;
        for (Step const& other : s.steps)
            if (other.index + 1 == step.index && other.gap)
                previous = other.gap->centre;
        Fronts::GapPick const gap = Fronts::PlaceWallGap(frame, s.wall.gaps, pools, previous, frand(0.f, 1.f));
        step.gap = gap;

        BossMechanics::LineFrontSpec spec;
        spec.facing = s.wall.facing;
        spec.travelYd = s.wall.travelYd;
        spec.widthYd = s.wall.widthYd;
        spec.bandYd = s.wall.bandYd;
        spec.speed = s.wall.speed;
        spec.gaps = { { gap.centre, s.wall.gaps.gapYd } };
        {
            BossMechanics::MechanicRef ref = Mechanic::LineFront(owner, s.at, spec, warn);
            if (ref.IsValid())
            {
                if (s.wall.within)
                    ref.Within(*s.wall.within);
                if (s.wall.decorate)
                    s.wall.decorate(ref, step.index);
            }
            step.front = ref;
        }   // committed here
        if (step.front && safe && (parkedGuid.IsEmpty() || parked))
        {
            BossMechanics::MechanicRef ref = Mechanic::FrontSafe(owner, step.front, parked, s.wall.safeUntilYd, 0);
            step.safe = ref;
        }
        LogMechanic(s.wall.dungeon, s.wall.boss, "wall-front-gap", "wall=" + std::to_string(step.index) + " t="
            + std::to_string(static_cast<int>(std::lround(gap.centre))) + " pools=" + std::to_string(pools.size())
            + (gap.offPools ? "" : " poolSqYd=" + std::to_string(static_cast<int>(std::lround(gap.poolAreaSqYd))))
            + (gap.keptSide ? "" : " sameSide=1")
            + (gap.keptWithin ? "" : " far=1"));
    }

    void FrontDirector::Launch(Unit* owner, Sequence& s, Step& step)
    {
        step.launched = true;
        if (!step.front)
            return;     // refused at registration: nothing rolls
        float const z = s.at.GetPositionZ();
        Vec2 const origin{ s.at.GetPositionX(), s.at.GetPositionY() };
        uint32 const life = step.overMs - step.launchMs + kCarrierTailMs;

        if (s.rings)
        {
            FrontCarrierSpec const& c = s.ring.carriers;
            Fronts::RingSequenceSpec const& p = s.ring.plan;
            if (c.entry)
            {
                float const r0 = step.startYd + p.bandYd * 0.5f;
                float const r1 = p.endYd + p.bandYd * 0.5f;
                for (float b : Fronts::RingCarrierBearings(step.sliceBearing, p.sliceDeg, r0, c.spacingYd, c.maxCount))
                {
                    ObjectGuid const g = SpawnCarrier(owner, c, Advance(origin, b, r0), Advance(origin, b, r1), z,
                        p.speed, life);
                    if (!g.IsEmpty())
                        step.carriers.push_back(g);
                }
            }
            if (s.ring.onLaunch)
            {
                Position at = s.at;
                at.SetOrientation(step.sliceBearing);
                s.ring.onLaunch(step.index, at);
            }
            return;
        }

        FrontCarrierSpec const& c = s.wall.carriers;
        if (c.entry && step.gap)
        {
            Fronts::WallFrame const frame = FrameOf(s);
            std::vector<std::pair<float, float>> const gaps{ { step.gap->centre, s.wall.gaps.gapYd } };
            float const sFrom = s.wall.bandYd * 0.5f;
            float const sTo = std::max(sFrom, s.wall.travelYd - s.wall.bandYd * 0.5f);
            for (float t : Fronts::WallCarrierSlots(s.wall.widthYd, c.spacingYd, gaps, c.maxCount))
            {
                ObjectGuid const g = SpawnCarrier(owner, c, Fronts::FromWallCoords(frame, sFrom, t),
                    Fronts::FromWallCoords(frame, sTo, t), z, s.wall.speed, life);
                if (!g.IsEmpty())
                    step.carriers.push_back(g);
            }
        }
        if (s.wall.onLaunch)
        {
            Position at = s.at;
            at.SetOrientation(s.wall.facing);
            s.wall.onLaunch(step.index, at);
        }
    }

    // --------------------------------------------------------------------------------------------------------------
    // Ending
    // --------------------------------------------------------------------------------------------------------------

    void FrontDirector::Despawn(Unit* owner, Step& step)
    {
        if (owner && owner->IsInWorld())
            for (ObjectGuid const& g : step.carriers)
                if (Creature* c = owner->GetMap()->GetCreature(g))
                    c->DespawnOrUnsummon();
        step.carriers.clear();
    }

    void FrontDirector::CancelStep(Unit* owner, Step& step)
    {
        if (owner)
        {
            if (step.safe)
                Mechanic::Cancel(owner, step.safe);
            if (step.front)
                Mechanic::Cancel(owner, step.front);
        }
        step.safe = {};
        step.front = {};
        Despawn(owner, step);
        step.registered = true;
        step.launched = true;
    }

    void FrontDirector::Cancel(Unit* owner, uint32 id)
    {
        if (_busy)
        {
            LogMechanic("kit", "front", "front-director-refused", "Cancel from a callback");
            return;
        }
        for (auto it = _seqs.begin(); it != _seqs.end(); ++it)
        {
            if (it->id != id)
                continue;
            for (Step& step : it->steps)
                CancelStep(owner, step);
            _seqs.erase(it);
            return;
        }
    }

    void FrontDirector::Clear(Unit* owner)
    {
        if (_busy)
        {
            LogMechanic("kit", "front", "front-director-refused", "Clear from a callback");
            return;
        }
        for (Sequence& s : _seqs)
            for (Step& step : s.steps)
                CancelStep(owner, step);
        _seqs.clear();
    }

    // --------------------------------------------------------------------------------------------------------------
    // Reading
    // --------------------------------------------------------------------------------------------------------------

    FrontDirector::Sequence const* FrontDirector::Find(uint32 id) const
    {
        for (Sequence const& s : _seqs)
            if (s.id == id)
                return &s;
        return nullptr;
    }

    std::vector<BossMechanics::MechanicHandle> FrontDirector::Handles(uint32 id) const
    {
        std::vector<BossMechanics::MechanicHandle> out;
        if (Sequence const* s = Find(id))
            for (Step const& step : s->steps)
                if (step.front)
                    out.push_back(step.front);
        return out;
    }

    std::vector<Fronts::RingStep> const* FrontDirector::RingPlan(uint32 id) const
    {
        Sequence const* s = Find(id);
        return s && s->rings ? &s->plan : nullptr;
    }

    std::vector<Fronts::GapPick> FrontDirector::Gaps(uint32 id) const
    {
        std::vector<Fronts::GapPick> out;
        if (Sequence const* s = Find(id))
            for (Step const& step : s->steps)
                if (step.gap)
                    out.push_back(*step.gap);
        return out;
    }

    uint32 FrontDirector::ElapsedMs(uint32 id) const
    {
        Sequence const* s = Find(id);
        return s ? static_cast<uint32>(_clockMs - s->startMs) : 0;
    }
}
