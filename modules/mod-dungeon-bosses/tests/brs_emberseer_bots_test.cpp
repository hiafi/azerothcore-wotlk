// Host test for B10 (Pyroguard Emberseer): the bots' hits from the Furnace Pulse (EM2 nova, EM3 rings) with the user's
// rolling front rulings (HANDOFF section 10, 2026-11-15): ring 1's random slice shown 5 s ahead from the nova's edge,
// the nova on its own 2.5 s warning, rings 2-4 from the apex (startYd 0), each shown as the ring before it launches.
// The timing is the boss's own (EmberseerLogic.h PulseSpec through the kit's pure planner DungeonKitFrontLogic.h
// PlanRings, the plan FrontDirector registers); the bots are mod-boss-mechanics' brain model (tests/brain_model.h) on
// its solver, the hazards built as the bot view builds them (RF tests/front_test.cpp). Normal and heroic, 5 and 10
// bots, the group close (ranged 5-9 yd: the RF report's "within about 9 yd") or at its usual 15-19 yd.
//
// Needs mod-boss-mechanics' src and tests (not part of tests/run.sh's pure list): run.sh's BM_SRC block, or
//   g++ -std=c++20 -O1 -I src/Kit -I src/BlackrockSpire -I tests -I $BM/src -I $BM/tests
//       tests/brs_emberseer_bots_test.cpp
#include "check.h"
#include "EmberseerLogic.h"
#include "brain_model.h"
#include "MechanicFront.h"
#include "MechanicSolver.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <vector>

using namespace BossMechanics;
using Geo::Pose;
using Geo::Vec3;
using Solver::Hazard;
using Solver::Input;
using Ms = std::chrono::milliseconds;
namespace EM = BrsEmberseer;
namespace KF = DungeonKit::Fronts;

namespace
{
    constexpr float kMargin = 0.75f;            // BossMechanics.Bots.SafetyMarginYd

    // Straight paths inside the hall (its walls): a point outside is not walkable, a path toward one stops at the wall.
    struct BoxOracle : Solver::PathOracle
    {
        float x0 = 0.f, y0 = 0.f, x1 = 0.f, y1 = 0.f;

        BoxOracle(float ax, float ay, float bx, float by) : x0(ax), y0(ay), x1(bx), y1(by) { }

        Vec3 Clamp(Vec3 p) const
        {
            p.x = std::clamp(p.x, x0, x1);
            p.y = std::clamp(p.y, y0, y1);
            return p;
        }

        bool Find(Vec3 const& from, Vec3 const& to, std::vector<Vec3>& out) override
        {
            out = { from, Clamp(to) };
            return true;
        }

        bool Walkable(Vec3& p) override
        {
            return p.x >= x0 && p.x <= x1 && p.y >= y0 && p.y <= y1;
        }
    };

    Vec3 Polar(float bearing, float r)
    {
        return { std::cos(bearing) * r, std::sin(bearing) * r, 0.f };
    }

    // A ring as the bot view builds it from the boss's Mechanic::ConeFront (the kit registers each step of the plan).
    Hazard Ring(std::uint32_t id, KF::RingSequenceSpec const& s, KF::RingStep const& step, bool hasNext, Ms launch)
    {
        ConeFrontSpec spec;
        spec.sliceBearing = step.sliceBearing;
        spec.sliceDeg = s.sliceDeg;
        spec.startYd = step.startYd;
        spec.endYd = s.endYd;
        spec.bandYd = s.bandYd;
        spec.speed = s.speed;
        Hazard h;
        h.id = id;
        h.shape = Front::ConeShape(spec);
        h.poses = { Pose{ 0.f, 0.f, 0.f, Front::ConeFacing(spec) } };
        h.marginYd = kMargin;
        h.timing = Solver::MakeProjectile(Front::ConeParams(spec), launch);
        h.front = true;
        h.nextTurn = -Geo::DegToRad(hasNext ? s.turnDeg : 0.f);  // the kit's nextTurnDeg, as the bot view carries it
        return h;
    }

    Hazard Nova(std::uint32_t id, float r, Ms at)
    {
        Hazard h;
        h.id = id;
        h.shape = Shape::Circle(r);
        h.poses = { Pose{ 0.f, 0.f, 0.f, 0.f } };
        h.marginYd = kMargin;
        h.timing = Solver::MakeInstant(at, Ms(500));
        return h;
    }

    struct Case
    {
        char const* name;
        bool heroic;
        std::uint32_t stacks;
        std::uint32_t bots;
        float rangedYd;         // where the ranged half stands from the boss (the melee half at 3 yd)
        float maxRingPct;       // the gate on ring hits (% of the ring passes); < 0: reported only
        float maxNovaPct;       // the gate on nova hits; < 0: reported only
    };

    struct Result
    {
        BrainModel::Counters c;
        std::uint32_t novaHits = 0;
        std::uint32_t ringHits = 0;
        std::uint32_t ringPasses = 0;
        std::uint32_t novaPasses = 0;
        std::uint32_t firstRingHits = 0;        // ring 1 (from the nova's edge)
        std::uint32_t laterRingHits = 0;        // rings 2-4 (from the apex)
        std::array<std::uint32_t, 4> byRing{};  // hits by ring index
    };

    // 60 s of pulses at a fixed stack count (the rings and the nova radius of that count), the boss on the apex at the
    // dais's centre, the group round him drifting back to its spots between pulses (stock follow).
    Result Run(Case const& c, std::uint32_t seed)
    {
        BrainModel::Config cfg;
        cfg.params.marginMs = Ms(300);
        BrainModel::World world;
        world.cfg = cfg;
        std::vector<Vec3> slots;
        for (std::uint32_t k = 0; k < c.bots; ++k)
        {
            float const a = Geo::kTwoPi * static_cast<float>(k) / static_cast<float>(c.bots) + 0.37f * seed;
            float const r = k < c.bots / 2 ? 3.f : c.rangedYd + 2.f * static_cast<float>(k % 3);
            slots.push_back(Polar(a, r));
            BrainModel::Bot b;
            b.pos = slots.back();
            world.bots.push_back(b);
        }
        world.follow = [&slots](std::size_t i, Vec3& to)
        {
            to = slots[i];
            return true;
        };
        // The hall (EmberseerLogic.h kHall*, handoff section 3.8) round the dais centre, as hard spot bounds and walls.
        float const x0 = EM::kHallMinX - BlackrockSpireRework::kEmberseerSpawn.x;
        float const x1 = EM::kHallMaxX - BlackrockSpireRework::kEmberseerSpawn.x;
        float const y0 = EM::kHallMinY - BlackrockSpireRework::kEmberseerSpawn.y;
        float const y1 = EM::kHallMaxY - BlackrockSpireRework::kEmberseerSpawn.y;
        Solver::Bounds hall;
        Solver::BoundsArea area;
        area.polygon = { { x0, y0, 0.f }, { x1, y0, 0.f }, { x1, y1, 0.f }, { x0, y1, 0.f } };
        hall.areas.push_back(area);
        world.kinds = [&hall](std::size_t, Input& in, Ms, std::vector<BrainModel::Task>&)
        {
            in.bounds = { hall };
        };
        BoxOracle walls(x0, y0, x1, y1);
        world.oracle = &walls;

        struct Pending
        {
            Ms at;
            Hazard h;
        };
        std::vector<Pending> pending;
        std::vector<std::uint32_t> novas;
        std::vector<std::uint32_t> firstRings;
        std::vector<std::uint32_t> ringIndex(1, 0);     // by hazard id
        std::uint32_t id = 1;
        std::uint32_t rng = 0x9e3779b9u * (seed + 1);
        Ms const t0{ 100000 };
        Ms const end = t0 + Ms(60000);
        Ms const every{ EM::kPulseEveryMs(c.heroic) };
        Result out;
        for (Ms pulse = t0; pulse + Ms(10000) < end; pulse += every)
        {
            rng = rng * 1664525u + 1013904223u;
            float const first = static_cast<float>(rng >> 8) / 16777216.f * Geo::kTwoPi;
            KF::RingSequenceSpec const spec = EM::PulseSpec(c.stacks, c.heroic, first);
            std::vector<KF::RingStep> const plan = KF::PlanRings(spec);
            // The nova: registered at the cue with its 2.5 s warning, erupting as ring 1 launches.
            novas.push_back(id);
            pending.push_back({ pulse + Ms(EM::kNovaCueMs), Nova(id++, spec.startYd, pulse + Ms(EM::kEruptionMs)) });
            ++out.novaPasses;
            for (KF::RingStep const& step : plan)
            {
                if (step.index == 0)
                    firstRings.push_back(id);
                ringIndex.resize(id + 1, 0);
                ringIndex[id] = step.index;
                pending.push_back({ pulse + Ms(step.registerMs), Ring(id++, spec, step, step.index + 1 < plan.size(),
                    pulse + Ms(step.launchMs)) });
                ++out.ringPasses;
            }
        }
        for (Ms now = t0; now < end; now += cfg.step)
        {
            for (Pending& p : pending)
                if (p.h.id != 0 && p.at <= now)
                {
                    world.AddHazard(p.h);
                    p.h.id = 0;
                }
            world.Step(now);
        }
        out.c = world.Total();
        out.novaPasses *= c.bots;
        out.ringPasses *= c.bots;
        for (BrainModel::Bot const& b : world.bots)
            for (std::uint32_t hid : b.hitBy)
            {
                if (std::find(novas.begin(), novas.end(), hid) != novas.end())
                    ++out.novaHits;
                else
                {
                    ++out.ringHits;
                    ++out.byRing[std::min<std::size_t>(ringIndex[hid], out.byRing.size() - 1)];
                    ++(std::find(firstRings.begin(), firstRings.end(), hid) != firstRings.end() ? out.firstRingHits
                        : out.laterRingHits);
                }
            }
        return out;
    }

    void TestPulses()
    {
        // Normal 1 / 2 / 3 rings at 3 / 10 / 16 stacks (and 19: a 12.7 yd nova), heroic 2 / 3 / 4. Gates (the group
        // close, the setup the boss plays for): ring hits at most 2% (normal) / 3% (heroic up to 3 rings), nova hits
        // at most 15%. Heroic 4 rings (14+ stacks, reached only by missing posts; user ruling 2026-11-15 keeps the
        // design): rings at most 10%, nova at most 20% (WP-SF's ring orbit + the kit's nextTurnDeg hint: ~5.5%).
        // The ranged at 15 yd are reported only.
        Case const cases[] = {
            { "normal  3 stacks (1 ring)", false, 3, 5, 5.f, 2.f, 15.f },
            { "normal 10 stacks (2 rings)", false, 10, 5, 5.f, 2.f, 15.f },
            { "normal 16 stacks (3 rings)", false, 16, 5, 5.f, 2.f, 15.f },
            { "normal 19 stacks (3 rings)", false, 19, 5, 5.f, 2.f, 15.f },
            { "normal 10 stacks (2 rings)", false, 10, 10, 5.f, 2.f, 15.f },
            { "normal 16 stacks (3 rings)", false, 16, 10, 5.f, 2.f, 15.f },
            { "heroic  3 stacks (2 rings)", true, 3, 5, 5.f, 3.f, 15.f },
            { "heroic 10 stacks (3 rings)", true, 10, 5, 5.f, 3.f, 15.f },
            { "heroic 10 stacks (3 rings)", true, 10, 10, 5.f, 3.f, 15.f },
            { "heroic 16 stacks (4 rings)", true, 16, 5, 5.f, 10.f, 20.f },
            { "heroic 19 stacks (4 rings)", true, 19, 5, 5.f, 10.f, 20.f },
            { "heroic 16 stacks (4 rings)", true, 16, 10, 5.f, 10.f, 20.f },
            { "normal  3 stacks (1 ring)", false, 3, 5, 15.f, -1.f, -1.f },
            { "normal 16 stacks (3 rings)", false, 16, 5, 15.f, -1.f, -1.f },
            { "heroic 10 stacks (3 rings)", true, 10, 10, 15.f, -1.f, -1.f },
            { "heroic 16 stacks (4 rings)", true, 16, 10, 15.f, -1.f, -1.f },
        };
        for (Case const& c : cases)
        {
            Result sum;
            for (std::uint32_t seed = 0; seed < 4; ++seed)
            {
                Result const r = Run(c, seed);
                sum.c.Add(r.c);
                sum.novaHits += r.novaHits;
                sum.ringHits += r.ringHits;
                sum.ringPasses += r.ringPasses;
                sum.novaPasses += r.novaPasses;
                sum.firstRingHits += r.firstRingHits;
                sum.laterRingHits += r.laterRingHits;
                for (std::size_t k = 0; k < sum.byRing.size(); ++k)
                    sum.byRing[k] += r.byRing[k];
            }
            float const ringPct = 100.f * float(sum.ringHits) / float(std::max(1u, sum.ringPasses));
            float const novaPct = 100.f * float(sum.novaHits) / float(std::max(1u, sum.novaPasses));
            std::printf("emberseer bots %-27s %2u bots, ranged %2.0f yd: nova %3u of %3u (%4.1f%%), rings %3u of %3u "
                "(%4.1f%%; by ring %u/%u/%u/%u); solves %4u, fallback %4u, solve us max %4lld mean %4lld\n", c.name,
                c.bots, c.rangedYd, sum.novaHits, sum.novaPasses, novaPct, sum.ringHits, sum.ringPasses, ringPct,
                sum.byRing[0], sum.byRing[1], sum.byRing[2], sum.byRing[3], sum.c.solves, sum.c.Fallbacks(),
                static_cast<long long>(sum.c.solveUsMax),
                static_cast<long long>(sum.c.solves ? sum.c.solveUsTotal / sum.c.solves : 0));
            CHECK(sum.ringPasses > 0 && sum.novaPasses > 0);
            // Ring 1's slice, shown 5 s ahead (ruling 1), is always reached: no bot takes ring 1 in any case.
            CHECK(sum.firstRingHits == 0);
            if (c.maxRingPct >= 0.f)
                CHECK(ringPct <= c.maxRingPct);
            if (c.maxNovaPct >= 0.f)
                CHECK(novaPct <= c.maxNovaPct);
        }
    }
}

int main()
{
    TestPulses();
    return Report("brs_emberseer_bots_test");
}
