// Host tests for ZumrahLogic.h (D3, Witch Doctor Zum'rah): the slice, the bowl and its spots, the cast timeline (the
// Rend's grid, the Volley never into a Rend, the Bolts only where they fit), the soul cadence, the graves of section
// 7 #29 A, the walk rotation, the Ward of the Dead (ruling 45), the Bound Dead spots and the stack math of the spec.
#include "ZumrahLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace ZulFarrakRework;
using namespace ZfZumrah;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    struct CastLog
    {
        std::vector<std::uint64_t> rends;
        std::vector<std::uint64_t> volleys;
        std::vector<std::uint64_t> bolts;
        std::vector<std::uint64_t> wards;
        std::uint32_t boltSkips = 0;
    };

    // Runs the timeline for `ms` in 100 ms ticks, as the AI does: the Ward whatever he does, a new cast only while he
    // is not casting; rolls are fixed (`volleyGap`, `boltGap`, `wardGap`).
    CastLog Run(bool heroic, std::uint32_t ms, std::uint32_t volleyGap, std::uint32_t boltGap, std::uint32_t wardGap)
    {
        CastLog log;
        Timeline t;
        t.Start(heroic);
        std::uint64_t castingUntil = 0;
        for (std::uint32_t now = 0; now <= ms; now += 100)
        {
            if (now)
                t.Advance(100);
            if (t.WardDue())
            {
                log.wards.push_back(t.Now());
                t.WardDone(wardGap);
            }
            if (t.Now() < castingUntil)
                continue;
            if (t.SkipBolt(boltGap))
                ++log.boltSkips;
            Act const act = t.Next();
            switch (act)
            {
                case Act::Rend:
                    log.rends.push_back(t.Now());
                    castingUntil = t.Now() + Tune::kRendCastMs;
                    t.Done(act);
                    break;
                case Act::Volley:
                    log.volleys.push_back(t.Now());
                    castingUntil = t.Now() + Tune::kVolleyCastMs(heroic);
                    t.Done(act, volleyGap);
                    break;
                case Act::Bolt:
                    log.bolts.push_back(t.Now());
                    castingUntil = t.Now() + Tune::kBoltCastMs;
                    t.Done(act, boltGap);
                    break;
                case Act::None:
                    break;
            }
        }
        return log;
    }

    // Every cast [start, start + cast) ends before the next start of `others`.
    bool EndsBeforeNext(std::vector<std::uint64_t> const& starts, std::uint32_t castMs,
        std::vector<std::uint64_t> const& others)
    {
        for (std::uint64_t const s : starts)
            for (std::uint64_t const o : others)
                if (o > s && s + castMs > o)
                    return false;
        return true;
    }
}

int main()
{
    // ---- The slice, the arena and its spots ----
    CHECK(kSpellsReservation.Contains(ZfZumrah::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfZumrah::kSpellSlice.last));
    CHECK(kSpellSlice.Contains(SPELL_ZR_SPIRIT_REND));
    CHECK(kSpellSlice.Contains(SPELL_ZR_GRAVE_ERUPTION));
    CHECK(SPELL_ZR_GRAVE_ERUPTION == kSpellSlice.first + 19);
    CHECK(BowlArena().Contains(kZumrahSpawn.XY(), kZumrahSpawn.z));
    CHECK(ArenaFor(BOSS_ZUMRAH).Contains(kZumrahSpawn.XY(), kZumrahSpawn.z));
    CHECK(BowlArena().Contains(kCauldron.XY(), kCauldron.z));
    CHECK(BowlArena().Contains(kBoundDeadOverflow.XY(), kBoundDeadOverflow.z));
    CHECK(kSpiritWorldType == 11);

    // ---- The timeline (normal): the Rend's grid, nothing run into it ----
    {
        CastLog const log = Run(false, 120000, 14000, 3500, 33000);
        std::vector<std::uint64_t> const rends{ 15000, 40000, 65000, 90000, 115000 };
        CHECK(log.rends == rends);
        CHECK(!log.volleys.empty() && log.volleys.front() == Tune::kVolleyFirstMs);
        CHECK(EndsBeforeNext(log.volleys, Tune::kVolleyCastMs.normal, log.rends));
        CHECK(EndsBeforeNext(log.bolts, Tune::kBoltCastMs, log.rends));
        CHECK(EndsBeforeNext(log.bolts, Tune::kBoltCastMs, log.volleys));
        CHECK(EndsBeforeNext(log.rends, Tune::kRendCastMs, log.volleys));
        CHECK(!log.bolts.empty() && log.bolts.front() == Tune::kBoltFirstMs);
        // Volleys keep their pace: never closer than one interrupter's 10 s, never later than the roll plus a Rend bar
        // and the Volley's own cast.
        for (std::size_t i = 1; i < log.volleys.size(); ++i)
        {
            std::uint64_t const gap = log.volleys[i] - log.volleys[i - 1];
            CHECK(gap >= Tune::kVolleyMinGapMs);
            CHECK(gap <= 14000 + Tune::kRendCastMs + Tune::kVolleyCastMs.normal + 500);
        }
        // 120 s: eight or more Volleys on a 14 s roll (8, 22, 36, ...).
        CHECK(log.volleys.size() >= 7);
        // The Ward: 2 s, then the roll.
        CHECK(log.wards.size() == 4 && log.wards[0] == Tune::kWardFirstMs && log.wards[1] == 35000);
        // Bolts are cast between the set pieces (more than a few), and skips happen near them.
        CHECK(log.bolts.size() >= 10);
        CHECK(log.boltSkips >= 1);
    }

    // ---- The timeline (heroic): the 2 s Volley, the 25 s Ward ----
    {
        CastLog const log = Run(true, 120000, 12000, 3000, Tune::kWardEveryMinMs.heroic);
        CHECK(log.rends.size() == 5 && log.rends[0] == 15000);
        CHECK(EndsBeforeNext(log.volleys, Tune::kVolleyCastMs.heroic, log.rends));
        CHECK(EndsBeforeNext(log.bolts, Tune::kBoltCastMs, log.rends));
        for (std::size_t i = 1; i < log.volleys.size(); ++i)
            CHECK(log.volleys[i] - log.volleys[i - 1] >= Tune::kVolleyMinGapMs);
        CHECK(log.wards.size() == 5 && log.wards[1] == 27000);
    }

    // ---- A refused cast is retried, and a late Rend keeps its grid ----
    {
        Timeline t;
        t.Start(false);
        t.Advance(15000);
        CHECK(t.Next() == Act::Rend);
        t.Retry(Act::Rend);
        CHECK(t.Next() != Act::Rend);
        t.Advance(kRetryMs);
        CHECK(t.Next() == Act::Rend);
        t.Done(Act::Rend);
        CHECK(t.In(Act::Rend) == 40000 - 15500);
    }

    // ---- The walk never overlaps the next one ----
    CHECK(Tune::kRendCastMs + Tune::kWalkMs + 1000 <= Tune::kRendEveryMs);
    // SP: "in 15 sec at 40% faster a walker covers about 145 yd" (a 7 yd/s run).
    CHECK(Near(7.f * (1.f + Tune::kWalkSpeedPct / 100.f) * Tune::kWalkMs / 1000.f, 147.f, 0.5f));

    // ---- The soul cadence ----
    {
        SoulClock c;
        c.Start(false);
        std::uint32_t risen = 0;
        for (std::uint32_t now = 0; now <= 100000; now += 100)
            risen += c.Rises(now);
        CHECK(risen == 17);         // 0, 6, ... 96 s: SP "about 16 in a 100 sec fight"
        SoulClock h;
        h.Start(true);
        risen = 0;
        for (std::uint32_t now = 0; now <= 110000; now += 100)
        {
            std::uint32_t const n = h.Rises(now);
            CHECK(n <= 1);
            risen += n;
        }
        CHECK(risen == 56);         // SP "about 55 in the fight"
        SoulClock late;
        late.Start(false);
        CHECK(late.Rises(0) == 1);
        CHECK(late.Rises(12500) == 2);  // a long tick raises the missed ones
        CHECK(late.In(12500) == 5500);
    }

    // ---- The graves (section 7 #29 A) ----
    {
        std::vector<std::size_t> const rise = RiseGraves();
        CHECK(rise.size() == 30);
        float farthest = 0.f;
        float nearest = 1000.f;
        for (std::size_t const i : rise)
        {
            float const d = DungeonKit::Distance(kGraves[i].XY(), kCauldron.XY());
            farthest = std::max(farthest, d);
            nearest = std::min(nearest, d);
            CHECK(d <= kGraveReachYd);
        }
        CHECK(farthest > 57.f && nearest > 19.f && nearest < 20.f);
        for (Point3 const& g : kGraves)
            CHECK(BowlArena().Contains(g.XY(), g.z));
        // A straight crawl from the farthest rise grave: about 20 s on normal, 15 on heroic (section 7 #29 A).
        CHECK(farthest / Tune::kSoulSpeed.normal <= 20.f);
        CHECK(farthest / Tune::kSoulSpeed.heroic <= 15.f);
        // Grasping Graves: a walker at the cauldron has none within 20 yd but the nearest two; one in the bowl's
        // middle has several.
        CHECK(GravesNear(kCauldron.XY(), Tune::kGravesRangeYd).size() == 2);
        CHECK(GravesNear({ 1866.f, 1030.f }, Tune::kGravesRangeYd).size() >= 6);
        CHECK(GravesNear({ 1950.f, 1100.f }, Tune::kGravesRangeYd).empty());
    }

    // ---- Who walks: everyone in turn ----
    {
        std::vector<std::uint64_t> const group{ 1, 2, 3, 4, 5 };
        std::set<std::uint64_t> walked;
        std::uint64_t last = 0;
        std::set<std::uint64_t> seen;
        for (int walk = 0; walk < 5; ++walk)
        {
            std::vector<std::uint64_t> const c = RendCandidates(group, walked, last);
            CHECK(!c.empty());
            CHECK(!walked.count(c.front()));
            last = c.front();
            walked.insert(last);
            seen.insert(last);
        }
        CHECK(seen.size() == 5);
        // The sixth walk resets the rotation and never repeats the fifth walker.
        std::vector<std::uint64_t> const sixth = RendCandidates(group, walked, last);
        CHECK(sixth.size() == 4);
        for (std::uint64_t const g : sixth)
            CHECK(g != last);
        CHECK(walked.empty());
        // A lone player walks every time.
        std::set<std::uint64_t> solo{ 7 };
        CHECK(RendCandidates({ 7 }, solo, 7) == std::vector<std::uint64_t>{ 7 });
        // A player who joined late is first in line.
        std::set<std::uint64_t> some{ 1, 2 };
        CHECK(RendCandidates({ 1, 2, 9 }, some, 2) == std::vector<std::uint64_t>{ 9 });
    }

    // ---- The Ward of the Dead (ruling 45) ----
    CHECK(WardReductionPct(0, false) == 0);
    CHECK(WardReductionPct(1, false) == 10);
    CHECK(WardReductionPct(4, false) == 40);
    CHECK(WardReductionPct(6, false) == 40);     // never past the normal cap
    CHECK(WardReductionPct(1, true) == 15);
    CHECK(WardReductionPct(4, true) == 60);
    CHECK(WardReductionPct(5, true) == 66);
    CHECK(WardReductionPct(6, true) == 71);
    CHECK(WardReductionPct(12, true) < 100);     // no immunity, however many
    for (std::uint32_t n = 1; n < 20; ++n)
        CHECK(WardReductionPct(n, true) >= WardReductionPct(n - 1, true));
    CHECK(BindsOrLost(3, false) && !BindsOrLost(4, false) && BindsOrLost(40, true));

    // ---- The Bound Dead spots ----
    {
        std::set<std::pair<int, int>> spots;
        for (std::size_t slot = 0; slot < 20; ++slot)
        {
            Point3 const p = BoundDeadSpot(slot);
            CHECK(BowlArena().Contains(p.XY(), p.z));
            // Every Bound Dead stands near the cauldron: a walker delivering there meets its Wail (heroic).
            CHECK(DungeonKit::Distance(p.XY(), kCauldron.XY()) <= Tune::kWailRangeYd + 1.f);
            if (slot < 17)
                spots.insert({ int(std::lround(p.x * 10)), int(std::lround(p.y * 10)) });
        }
        CHECK(spots.size() == 17);  // the four, the neck mouth, twelve on its rings: all distinct
        for (std::size_t slot = 0; slot < 4; ++slot)
            CHECK(Near(BoundDeadSpot(slot).x, kBoundDeadSpots[slot].x) && Near(BoundDeadSpot(slot).y,
                kBoundDeadSpots[slot].y));
        CHECK(Near(BoundDeadSpot(4).x, kBoundDeadOverflow.x));
        for (std::size_t slot = 5; slot < 17; ++slot)
            CHECK(DungeonKit::Distance(BoundDeadSpot(slot).XY(), kBoundDeadOverflow.XY()) <= 3.01f);
        CHECK(FirstFreeSlot({}) == 0);
        CHECK(FirstFreeSlot({ true, true, false, true }) == 2);
        CHECK(FirstFreeSlot({ true, true, true, true }) == 4);
    }

    // ---- The Wails are staggered a second apart ----
    CHECK(WailFirstMs(0) == 1000 && WailFirstMs(1) == 2000 && WailFirstMs(3) == 4000 && WailFirstMs(4) == 1000);

    // ---- Stack math of the spec ----
    // Skeletons: a hit every 2 s carries 3% (heroic 5%); four on an unguarded husk for a whole walk is about 90%.
    CHECK(Near(SkeletonStrikePct(false), 3.f) && Near(SkeletonStrikePct(true), 5.f));
    CHECK(Near(4.f * Tune::kSkeletonPctPerSec.normal * Tune::kWalkMs / 1000.f, 90.f));
    // Heroic Soul Burn: a 10-soul walk is about 60% on the walker.
    CHECK(Near(10.f * Tune::kSoulBurnPct, 60.f));
    // Rule 26 (section 3.6): the built health at bot throughput (2,500 normal, 5,500 heroic) and the spec's average
    // ward (15% normal, 25% heroic) kills inside the spec's 100 s / 110 s.
    CHECK(Health::kZumrah.normal / (2500.f * 0.85f) < 100.f);
    CHECK(Health::kZumrah.heroic / (5500.f * 0.75f) < 110.f);
    // At the spec's target group (1,140 normal, 2,215 heroic after the ward) the built health runs long: reported.
    CHECK(Health::kZumrah.normal / 1140.f > 100.f);
    // The Volley reaches everyone on the tongue and the neck.
    CHECK(DungeonKit::Distance(kZumrahSpawn.XY(), kBoundDeadOverflow.XY()) < Tune::kVolleyRangeYd);

    return Report("zf_zumrah_test");
}
