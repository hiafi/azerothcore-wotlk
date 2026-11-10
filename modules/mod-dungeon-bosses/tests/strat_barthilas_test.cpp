// Host tests for BarthilasLogic.h (S9: Magistrate Barthilas, "The Epidemic").
#include "BarthilasLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <optional>
#include <vector>

using namespace StratholmeRework;
using namespace StratBarthilas;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // A flat floor everywhere at z 138.
    std::optional<float> Flat(Vec2)
    {
        return 138.f;
    }

    bool Has(std::vector<uint64_t> const& v, uint64_t id)
    {
        return std::find(v.begin(), v.end(), id) != v.end();
    }

    void TestSliceAndArena()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        for (uint32_t id : { SPELL_BT_INFECTION, SPELL_BT_COUGH, SPELL_BT_COUGHING, SPELL_BT_RECOVERED,
                 SPELL_BT_GRAIN_THROW, SPELL_BT_GRAIN_IMPACT, SPELL_BT_PLAGUE_FOG, SPELL_BT_PURGE, SPELL_BT_FEVER,
                 SPELL_BT_BEDLAM })
            CHECK(kSpellSlice.Contains(id));
        // The boss spawns inside his arena.
        CHECK(BarthilasArena().Contains(kBarthilasSpawn.XY(), kBarthilasSpawn.z));
        CHECK(ArenaFor(BOSS_BARTHILAS).Contains(kBarthilasSpawn.XY(), kBarthilasSpawn.z));
        // The measured ward anchor and the spawn wards lie on his arena.
        CHECK(BarthilasArena().Contains(kBarthilasWardAnchor.XY(), 138.f));
        for (Point3 const& w : kBarthilasSpawnWards)
            CHECK(BarthilasArena().Contains(w.XY(), w.z));
    }

    void TestNumbers()
    {
        // ST build spec table.
        CHECK(kPatients(false) == 1 && kPatients(true) == 2);
        CHECK(kContagionHoldMs(false) == 1000 && kContagionHoldMs(true) == 500);
        CHECK(Near(kCoughPct(false), 30.f) && Near(kCoughPct(true), 40.f));
        CHECK(kPileLifeMs(false) == 30000 && kPileLifeMs(true) == 45000);
        CHECK(kPileCap(false) == 2 && kPileCap(true) == 3);
        CHECK(kQuarantineWarnMs(false) == 5000 && kQuarantineWarnMs(true) == 4000);
        CHECK(Near(kWardYd(false), 6.f) && Near(kWardYd(true), 5.f));
        CHECK(Near(kFeverDamagePct(false), 5.f) && Near(kFeverDamagePct(true), 6.f));
        // 4% every 2 s for 10 s: 20% over the course.
        CHECK(Near(kInfectionTickPct * float(kInfectionMs / kInfectionTickMs), 20.f));
        // A ward's edge is 3 yd from him: each center its radius + 3, both edges 6 yd apart.
        for (bool heroic : { false, true })
        {
            float const r = kWardYd(heroic);
            CHECK(Near(2.f * WardOffset(r) - 2.f * r, kWardEdgeGapYd));
            CHECK(Near(WardOffset(r) - r, 3.f));
        }
        CHECK(Near(WardOffset(kWardYd(false)), kBarthilasWardOffsetYd));
        // The spawn wards are the measured north-south pair, 9 yd either side of his spawn.
        for (Point3 const& w : kBarthilasSpawnWards)
            CHECK(Near(DungeonKit::Distance(w.XY(), kBarthilasSpawn.XY()), 9.f, 0.1f));
        // The cough always clears the contagion range (the 8 yd RunOut covers the 5 yd one).
        CHECK(kCoughYd > kContagionYd);
        // Fever: one stack every 20 s from the clock alone.
        CHECK(FeverTicksAt(0) == 0 && FeverTicksAt(19999) == 0 && FeverTicksAt(20000) == 1);
        CHECK(FeverTicksAt(73000) == 3);
    }

    void TestGrain()
    {
        // "Now and then": the first throw and every third after it.
        CHECK(GrainYells(1));
        CHECK(!GrainYells(2) && !GrainYells(3));
        CHECK(GrainYells(4) && GrainYells(7));
        CHECK(!GrainYells(0));
        // The sack lands as the marker resolves: 20 yd at 20 yd/s takes 1 s, so it leaves 1 s in.
        CHECK(SackLaunchDelayMs(20.f) == 1000);
        CHECK(SackLaunchDelayMs(0.f) == kGrainWarnMs);
        CHECK(SackLaunchDelayMs(60.f) == 0);
        CHECK(SackLaunchDelayMs(10.f, 0.f) == 0);
        // The pile cap: at most 2 (heroic 3) stand once the new one is down.
        CHECK(PilesToDrop(0, 2) == 0);
        CHECK(PilesToDrop(1, 2) == 0);
        CHECK(PilesToDrop(2, 2) == 1);
        CHECK(PilesToDrop(3, 2) == 2);
        CHECK(PilesToDrop(2, 3) == 0);
        CHECK(PilesToDrop(3, 3) == 1);
    }

    // BT2: a healthy player held within 5 yd of a carrier catches it after 1 s (heroic 0.5 s); stepping out resets.
    void TestContagionHold()
    {
        for (bool heroic : { false, true })
        {
            uint32_t const hold = kContagionHoldMs(heroic);
            DungeonKit::InsideClock clock;
            uint64_t const a = 1;
            uint64_t const b = 2;
            uint32_t elapsed = 0;
            bool aCaught = false;
            // `a` stands near a carrier the whole time; `b` is near for two polls, then away for one, and again.
            for (uint32_t poll = 1; poll <= 12; ++poll)
            {
                std::vector<uint64_t> near{ a };
                if (poll % 3 != 0)
                    near.push_back(b);
                elapsed += kContagionPollMs;
                std::vector<uint64_t> const caught = Catches(clock.Update(near, kContagionPollMs), hold);
                if (Has(caught, a) && !aCaught)
                {
                    aCaught = true;
                    CHECK(elapsed == hold);     // exactly the hold time
                }
                // `b` is never held 1 s (500 ms at most); on heroic 500 ms is enough.
                if (!heroic)
                    CHECK(!Has(caught, b));
                else
                    CHECK(Has(caught, b) == (poll % 3 == 2));
            }
            CHECK(aCaught);
        }
        // Carriers and recovering players never catch.
        CHECK(CanCatch(false, false));
        CHECK(!CanCatch(true, false));
        CHECK(!CanCatch(false, true));
    }

    void TestPurge()
    {
        // Outside both wards: 40%, carrier or not.
        CHECK(PurgeFor({ false, false, false, false }, false) == PurgeFate::Hit);
        CHECK(PurgeFor({ true, false, false, false }, true) == PurgeFate::Hit);
        CHECK(PurgeFor({ false, true, false, false }, false) == PurgeFate::Hit);
        // Carriers in the Sick Ward are cured.
        CHECK(PurgeFor({ true, false, true, false }, false) == PurgeFate::Cured);
        // A healthy player in the Sick Ward catches it; a recovering one does not.
        CHECK(PurgeFor({ false, false, true, false }, false) == PurgeFate::Caught);
        CHECK(PurgeFor({ false, true, true, false }, false) == PurgeFate::Safe);
        // The Well Ward is safe unless a carrier stands in it.
        CHECK(PurgeFor({ false, false, false, true }, false) == PurgeFate::Safe);
        CHECK(PurgeFor({ false, false, false, true }, true) == PurgeFate::Caught);
        CHECK(PurgeFor({ false, true, false, true }, true) == PurgeFate::Safe);
        // The carrier in the Well Ward stays sick (not cured, not hit).
        CHECK(PurgeFor({ true, false, false, true }, true) == PurgeFate::Safe);
        // Inside: the radius on the plane, and the floor.
        Vec2 const c{ 0.f, 0.f };
        CHECK(InWard({ 5.9f, 0.f }, 138.f, c, 138.f, 6.f));
        CHECK(InWard({ 6.f, 0.f }, 138.f, c, 138.f, 6.f));
        CHECK(!InWard({ 6.1f, 0.f }, 138.f, c, 138.f, 6.f));
        CHECK(!InWard({ 1.f, 0.f }, 143.f, c, 138.f, 6.f));
    }

    void TestWardLine()
    {
        Vec2 const boss = kBarthilasWardAnchor.XY();
        for (bool heroic : { false, true })
        {
            float const r = kWardYd(heroic);
            // Open floor, no piles: the first line wins, centers WardOffset from him on opposite sides.
            std::optional<WardLine> line = PickWardLine(boss, r, {}, 0.f, Flat);
            CHECK(line.has_value());
            if (!line)
                continue;
            CHECK(line->full);
            CHECK(Near(DungeonKit::Distance(line->a, boss), WardOffset(r)));
            CHECK(Near(DungeonKit::Distance(line->b, boss), WardOffset(r)));
            // Edge to edge 6 yd, each edge 3 yd from him.
            CHECK(Near(DungeonKit::Distance(line->a, line->b) - 2.f * r, kWardEdgeGapYd));
            CHECK(Near(line->za, 138.f) && Near(line->zb, 138.f));

            // A pile on that line's first ward: never on a pile, so another bearing is taken.
            std::vector<DungeonKit::AvoidCircle> const piles{ { line->a, kPileYd } };
            std::optional<WardLine> moved = PickWardLine(boss, r, piles, 0.f, Flat);
            CHECK(moved && moved->full);
            if (moved)
            {
                CHECK(DungeonKit::Distance(moved->a, piles[0].center) >= kPileYd + r);
                CHECK(DungeonKit::Distance(moved->b, piles[0].center) >= kPileYd + r);
            }
        }

        // The ruin by his spawn: only a north-south line fits there (x is north). Floor only within 4.6 yd of the
        // north-south axis through him. The candidates start 5 steps in, so the fit is the 20th candidate.
        Vec2 const spawn = kBarthilasSpawn.XY();
        auto ruin = [spawn](Vec2 p) -> std::optional<float>
        {
            if (std::fabs(p.y - spawn.y) <= 4.6f)
                return 138.f;
            return std::nullopt;
        };
        float const start = 5.f * DungeonKit::kPi / float(kWardBearings);
        std::optional<WardLine> ns = PickWardLine(spawn, kWardYd(false), {}, start, ruin);
        CHECK(ns && ns->full);
        if (ns)
        {
            CHECK(Near(ns->a.y, spawn.y) && Near(ns->b.y, spawn.y));
            // The pair is the measured spawn wards.
            Vec2 const north = ns->a.x > ns->b.x ? ns->a : ns->b;
            Vec2 const south = ns->a.x > ns->b.x ? ns->b : ns->a;
            CHECK(Near(north.x, kBarthilasSpawnWards[0].x, 0.1f) && Near(north.y, kBarthilasSpawnWards[0].y, 0.1f));
            CHECK(Near(south.x, kBarthilasSpawnWards[1].x, 0.1f) && Near(south.y, kBarthilasSpawnWards[1].y, 0.1f));
        }

        // Nowhere fits: the best effort still answers (the fewest floor misses), never full.
        auto none = [](Vec2) -> std::optional<float> { return std::nullopt; };
        std::optional<WardLine> worst = PickWardLine(boss, kWardYd(false), {}, 0.f, none);
        CHECK(worst && !worst->full && worst->floorMisses == 10);
        CHECK(!PickWardLine(boss, kWardYd(false), {}, 0.f, Flat, 0).has_value());
    }

    void TestPatients()
    {
        auto first = [](std::size_t) { return std::size_t(0); };
        std::vector<PatientCandidate> const group{ { 1, true, false }, { 2, false, true }, { 3, false, false },
            { 4, false, false }, { 5, false, false } };
        // Never a carrier; the fresh ones first, distinct.
        std::vector<uint64_t> const two = PickPatients(group, 2, first);
        CHECK(two.size() == 2 && two[0] == 3 && two[1] == 4);
        // A recovering player only when the fresh ones run out.
        std::vector<uint64_t> const four = PickPatients(group, 4, first);
        CHECK(four.size() == 4 && four[3] == 2);
        CHECK(!Has(four, 1));
        // Everyone sick: nobody.
        std::vector<PatientCandidate> const sick{ { 1, true, false }, { 2, true, true } };
        CHECK(PickPatients(sick, 2, first).empty());
    }
}

int main()
{
    TestSliceAndArena();
    TestNumbers();
    TestGrain();
    TestContagionHold();
    TestPurge();
    TestWardLine();
    TestPatients();

    return Report("strat_barthilas_test");
}
