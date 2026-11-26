// F-1d (STAGE-R-1-C Minor-1, DQ1, the BM-G note): GnomerWorkshop::PlatePlan against mod-boss-mechanics' own
// assignment (MechanicAssign.h ExclusiveSoakClaimers, the rule MechanicBotView.cpp runs for a oneClaimPerBot group).
// The plates while the Fallout schematic runs are D6's one exclusive group (tag 71): every lit plate a Soak of count
// 1, ordered by the dose (the highest first, no floor), the tank last unless it sheds (TankPlatesLast), served in the
// plan's order. Checked here: every bot holds at most one claim, every bot at 8 or more ends on the nearest lit plate
// not yet taken, and the tank goes only when DQ1 says so. The old two-group form (D6's plates by ETA plus the dose
// claim's own group, minStacks 8) is modelled too: a bot at 8 or more held a claim in both groups (the finding).
// Needs BM_SRC (tests/run.sh builds it beside kit_fronts_parity_test).
#include "MechanicAssign.h"
#include "ThermapluggHardModeLogic.h"
#include "check.h"
#include <algorithm>
#include <cstdint>
#include <map>
#include <vector>

using namespace GnomerWorkshop;
namespace Assign = BossMechanics::Assign;

namespace
{
    std::int64_t constexpr kRunYdPerSec = 7;
    std::int64_t constexpr kDeadline = std::int64_t(Tune::kWholeFightMs);     // a life-0 plate: everyone can come

    PlatePlayer Bot(std::uint64_t guid, std::uint32_t dose, Vec2 at, bool tank = false)
    {
        PlatePlayer p;
        p.guid = guid;
        p.dose = dose;
        p.bot = true;
        p.tank = tank;
        p.eligible = true;
        p.at = at;
        return p;
    }

    // One plate's BM input: the eligible players with their dose, ETA and tier, under the plate's rule.
    Assign::SoakInput Input(LitPlate const& plate, std::vector<PlatePlayer> const& players, bool orderedByDose,
        bool tankLast, std::uint32_t minStacks)
    {
        Assign::SoakInput in;
        for (PlatePlayer const& p : players)
        {
            if (!p.eligible)
                continue;
            Assign::Claimant c;
            c.guid = p.guid;
            c.bot = p.bot;
            c.stacks = orderedByDose ? p.dose : 0;
            c.etaMs = std::int64_t(DungeonKit::Distance(p.at, plate.at) * 1000.f) / kRunYdPerSec;
            c.last = tankLast && p.tank;
            in.players.push_back(c);
        }
        in.rule.count = 1;
        in.rule.ordered = orderedByDose;
        in.rule.ascending = false;
        in.rule.minStacks = minStacks;
        in.rule.deadlineMs = kDeadline;
        return in;
    }

    // The merged group as the bots see it: the plates in `order`, the dose ordering, the tank per DQ1.
    std::map<std::uint64_t, std::uint32_t> Claims(std::vector<LitPlate> const& plates,
        std::vector<std::uint32_t> const& order, std::vector<PlatePlayer> const& players, bool& oneEach)
    {
        bool const tankLast = TankPlatesLast(players);
        std::vector<Assign::SoakInput> inputs;
        for (std::uint32_t const face : order)
            for (LitPlate const& plate : plates)
                if (plate.face == face)
                    inputs.push_back(Input(plate, players, true, tankLast, 0));
        std::vector<std::vector<std::uint64_t>> const lists = Assign::ExclusiveSoakClaimers(inputs);
        std::map<std::uint64_t, std::uint32_t> out;
        oneEach = true;
        for (std::size_t i = 0; i < lists.size(); ++i)
            for (std::uint64_t const guid : lists[i])
            {
                oneEach = oneEach && !out.count(guid);
                out[guid] = order[i];
            }
        return out;
    }

    std::map<std::uint64_t, std::uint32_t> Planned(std::vector<LitPlate> const& plates,
        std::vector<PlatePlayer> const& players, bool& oneEach)
    {
        return Claims(plates, PlatePlan(plates, players, TankPlatesLast(players)), players, oneEach);
    }

    std::vector<std::uint32_t> RankOrder(std::vector<LitPlate> plates)
    {
        std::vector<std::uint32_t> out;
        std::sort(plates.begin(), plates.end(), [](LitPlate const& a, LitPlate const& b)
        {
            return a.rank != b.rank ? a.rank < b.rank : a.face < b.face;
        });
        for (LitPlate const& p : plates)
            out.push_back(p.face);
        return out;
    }

    void TestTheFinding()
    {
        // R-1-C's case: after an Override P1 (rank 0) and P2 (rank 2) are lit; B (9 dose) stands next to P1, A (12)
        // next to P2.
        std::vector<LitPlate> const plates{ { 0, { 0.f, 0.f }, 0 }, { 2, { 30.f, 0.f }, 2 } };
        std::vector<PlatePlayer> const players{ Bot(10, 9, { 2.f, 0.f }), Bot(11, 12, { 28.f, 0.f }) };

        // Before: two groups. D6's (tag 71, ETA, tank last) gives P1 to B; the claim's (tag 86, dose, minStacks 8)
        // gives P1 to A and P2 to B: B holds a claim in both groups, on two plates 30 yd apart.
        std::vector<Assign::SoakInput> d6, claim;
        for (LitPlate const& plate : plates)
        {
            d6.push_back(Input(plate, players, false, true, 0));
            claim.push_back(Input(plate, players, true, false, Tune::kPlateDoseFloor));
        }
        std::vector<std::vector<std::uint64_t>> const byEta = Assign::ExclusiveSoakClaimers(d6);
        std::vector<std::vector<std::uint64_t>> const byDose = Assign::ExclusiveSoakClaimers(claim);
        CHECK(byEta[0] == std::vector<std::uint64_t>({ 10 }) && byDose[0] == std::vector<std::uint64_t>({ 11 }));
        CHECK(byDose[1] == std::vector<std::uint64_t>({ 10 }));     // B: P1 in one group, P2 in the other

        // After, rank order alone (one group, the dose ordering): A is sent across the room to P1 (the BM-G note:
        // group order, not distance).
        bool oneEach = false;
        std::map<std::uint64_t, std::uint32_t> const ranked = Claims(plates, RankOrder(plates), players, oneEach);
        CHECK(oneEach && ranked.at(11) == 0 && ranked.at(10) == 2);

        // After, the plan's order: each at its nearest plate, one claim each.
        std::map<std::uint64_t, std::uint32_t> const planned = Planned(plates, players, oneEach);
        CHECK(oneEach && planned.at(10) == 0 && planned.at(11) == 2);
    }

    void TestTheTank()
    {
        std::vector<LitPlate> const plates{ { 0, { 0.f, 0.f }, 0 }, { 1, { 22.f, 0.f }, 1 } };
        // DQ1: another bot at 8 or more sheds first; the second plate goes to a non-tank under 8, not the tank.
        bool oneEach = false;
        std::map<std::uint64_t, std::uint32_t> waits = Planned(plates, { Bot(1, 16, { 11.f, 20.f }, true),
            Bot(2, 9, { 21.f, 1.f }), Bot(3, 4, { 1.f, 1.f }) }, oneEach);
        CHECK(oneEach && waits.at(2) == 1 && waits.at(3) == 0 && !waits.count(1));
        // Nobody else at 8 or more: the tank takes its nearest plate before anyone under 8 (under 8, the highest
        // dose goes first, wherever it stands: the dose ordering).
        std::map<std::uint64_t, std::uint32_t> const sheds = Planned(plates, { Bot(1, 16, { 20.f, 3.f }, true),
            Bot(2, 7, { 21.f, 1.f }), Bot(3, 4, { 1.f, 1.f }) }, oneEach);
        CHECK(oneEach && sheds.at(1) == 1 && sheds.at(2) == 0 && !sheds.count(3));
        // Nobody at 8 or more: non-tanks first (SP MT4), the highest dose first; the tank is never sent while a
        // non-tank bot is free.
        std::map<std::uint64_t, std::uint32_t> const low = Planned(plates, { Bot(1, 6, { 1.f, 0.f }, true),
            Bot(2, 5, { 21.f, 1.f }), Bot(3, 4, { 1.f, 1.f }) }, oneEach);
        CHECK(oneEach && !low.count(1) && low.size() == 2);
    }

    // Every layout: one claim a bot, and every bot at 8 or more that got a plate is on the nearest one no
    // higher-dose bot took (SP MT18, greedy by dose).
    void TestSweep()
    {
        std::uint32_t seed = 7;
        auto next = [&seed](std::uint32_t n)
        {
            seed = seed * 1664525u + 1013904223u;
            return (seed >> 8) % n;
        };
        for (int round = 0; round < 2000; ++round)
        {
            std::vector<LitPlate> plates;
            for (std::uint32_t face = 0; face < GnomereganRework::kFaceCount; ++face)
                if (next(2))
                    plates.push_back({ face, GnomereganRework::kPlateSpots[face].XY(), std::int32_t(next(6)) });
            std::vector<PlatePlayer> players;
            for (std::uint64_t guid = 1; guid <= 5; ++guid)
            {
                std::uint32_t const dose = next(20);
                float const x = -30.f + float(next(60));
                float const y = -30.f + float(next(60));
                PlatePlayer p = Bot(guid, dose, { x, y }, guid == 1);
                bool const human = guid == 5 && next(2) == 0;
                p.bot = !human;
                p.eligible = next(5) != 0;
                players.push_back(p);
            }
            bool oneEach = false;
            std::map<std::uint64_t, std::uint32_t> const got = Planned(plates, players, oneEach);
            CHECK(oneEach);
            CHECK(got.size() <= plates.size());
            std::vector<std::uint32_t> const plan = PlatePlan(plates, players, TankPlatesLast(players));
            CHECK(plan.size() == plates.size());
            bool const tankLast = TankPlatesLast(players);
            for (PlatePlayer const& p : players)
            {
                auto const it = got.find(p.guid);
                if (it == got.end() || p.dose < Tune::kPlateDoseFloor || (p.tank && tankLast))
                    continue;       // the tank, while last, takes only what the others leave
                // the plates no bot of a higher dose (or the same dose, lower guid) holds
                float mine = 0.f, best = 1e9f;
                for (LitPlate const& plate : plates)
                {
                    bool takenAbove = false;
                    for (PlatePlayer const& q : players)
                    {
                        auto const qt = got.find(q.guid);
                        if (qt != got.end() && qt->second == plate.face && q.guid != p.guid && q.dose >= p.dose)
                            takenAbove = true;      // a higher dose, or the same dose (the closer pair first)
                    }
                    float const yd = DungeonKit::Distance(p.at, plate.at);
                    if (plate.face == it->second)
                        mine = yd;
                    if (!takenAbove && yd < best)
                        best = yd;
                }
                CHECK(mine <= best + 0.01f);
            }
        }
    }
}

int main()
{
    TestTheFinding();
    TestTheTank();
    TestSweep();
    return Report("gnomer_plate_plan_bm_test");
}
