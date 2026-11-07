// Host tests for SneedLogic.h (WP-B3): spell slice, malfunction picks, the reboot ladder, the repair break, Tazer's
// jumps, Sneed's cast queue (handoff section 5: 3 s spacing, Tazer first, nothing during a channel, Tazer 12 s after a
// channel start, skipped on a completed repair) and the geometry helpers.
#include "SneedLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <string>
#include <utility>
#include <vector>

using namespace Sneed;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        CHECK(kSlice.first == 205240u);
        CHECK(kSlice.last == 205269u);
        std::set<std::uint32_t> seen;
        for (std::uint32_t id : kAllSpells)
        {
            CHECK(kSlice.Contains(id));
            CHECK(seen.insert(id).second);
        }
        CHECK(seen.size() == kAllSpells.size());
    }

    void TestMalfunctionPick()
    {
        // The first pick covers all three.
        std::set<Malfunction> first;
        for (std::uint32_t roll = 0; roll < 6; ++roll)
            first.insert(PickMalfunction(std::nullopt, roll));
        CHECK(first.size() == 3);

        // Never the same twice in a row; both others reachable.
        for (std::uint8_t l = 0; l < kMalfunctionCount; ++l)
        {
            Malfunction const last = static_cast<Malfunction>(l);
            std::set<Malfunction> next;
            for (std::uint32_t roll = 0; roll < 50; ++roll)
            {
                Malfunction const m = PickMalfunction(last, roll);
                CHECK(m != last);
                next.insert(m);
                CHECK(PickChained(last, roll) != last);
            }
            CHECK(next.size() == 2);
        }

        // A long heroic sequence (first, chained, first, chained, ...): no two in a row are equal.
        std::optional<Malfunction> last;
        std::uint32_t seed = 12345;
        for (int i = 0; i < 200; ++i)
        {
            seed = seed * 1103515245u + 12345u;
            Malfunction const a = PickMalfunction(last, seed >> 8);
            if (last)
                CHECK(a != *last);
            seed = seed * 1103515245u + 12345u;
            Malfunction const b = PickChained(a, seed >> 8);
            CHECK(b != a);
            last = b;
        }
        CHECK(std::string(MalfunctionName(Malfunction::Runaway)) == "runaway");
    }

    void TestRebootLadder()
    {
        for (bool heroic : { false, true })
        {
            RebootLadder ladder;
            CHECK(ladder.RepairsLeft());
            CHECK(ladder.OnBreakdown() == Breakdown::Eject);
            CHECK(Near(ladder.OnReboot(heroic), heroic ? 40.f : 30.f));
            CHECK(ladder.OnBreakdown() == Breakdown::Eject);
            CHECK(ladder.RepairsLeft());
            CHECK(Near(ladder.OnReboot(heroic), heroic ? 20.f : 15.f));
            CHECK(!ladder.RepairsLeft());
            CHECK(ladder.OnBreakdown() == Breakdown::EjectAndOverload);    // the third breakdown overloads
            CHECK(ladder.OnReboot(heroic) == 0.f);                          // no third reboot
            CHECK(ladder.reboots == kMaxReboots);
            CHECK(ladder.breakdowns == 3);
        }

        // A group that stops every repair: one breakdown, never an overload.
        RebootLadder clean;
        CHECK(clean.OnBreakdown() == Breakdown::Eject);
        CHECK(clean.RepairsLeft());
    }

    void TestRepairBreak()
    {
        // Normal Sneed 5.7k: 570; heroic 142k: 14.2k (build spec).
        CHECK(RepairBreakThreshold(5700, false) == 570u);
        CHECK(RepairBreakThreshold(142000, true) == 14200u);
        CHECK(!BreaksRepair(569, 5700, false));
        CHECK(BreaksRepair(570, 5700, false));
        CHECK(BreaksRepair(20000, 142000, true));
        CHECK(!BreaksRepair(14199, 142000, true));
        CHECK(RepairBreakThreshold(1, false) == 1u);
        CHECK(kRepairChannelMs(false) == 6000 && kRepairChannelMs(true) == 4000);
    }

    void TestTazer()
    {
        CHECK(TazerTargets(false) == 3);
        CHECK(TazerTargets(true) == 4);
        CHECK(Near(TazerJumpPct(false, 0), 20.f) && Near(TazerJumpPct(false, 1), 14.f));
        CHECK(Near(TazerJumpPct(false, 2), 10.f));
        CHECK(TazerJumpPct(false, 3) == 0.f);
        CHECK(Near(TazerJumpPct(true, 0), 35.f) && Near(TazerJumpPct(true, 3), 12.f));
        CHECK(TazerJumpPct(true, 4) == 0.f);
        // Each jump never hits harder than the one before.
        for (bool heroic : { false, true })
            for (std::size_t j = 1; j < TazerTargets(heroic); ++j)
                CHECK(TazerJumpPct(heroic, j) < TazerJumpPct(heroic, j - 1));
    }

    // Drive a queue the way the AI does: start whatever Next() names, with the AI's cadences.
    struct Sim
    {
        CastQueue q;
        bool heroic = false;
        bool salvaged = false;
        std::vector<std::pair<Ms, Cast>> starts;

        void Tick(Ms now)
        {
            Cast const c = q.Next(now);
            if (c == Cast::None)
                return;
            starts.emplace_back(now, c);
            switch (c)
            {
                case Cast::Tazer:
                    q.Started(c, now, salvaged ? kTazerSalvagedEveryMs(heroic) : 0);
                    break;
                case Cast::RepairRun:
                    q.Started(c, now, kRepairEveryMs(heroic));
                    q.SetBusy(true);
                    break;
                case Cast::SawSpin:
                    q.Started(c, now, kSalvagedSawEveryMs(heroic));
                    break;
                case Cast::SawBoomerang:
                    q.Started(c, now, kBoomerangEveryMs(heroic));
                    break;
                case Cast::ClusterBomb:
                    q.Started(c, now, kClusterEveryMs(heroic));
                    break;
                default:
                    break;
            }
        }
    };

    void TestCastQueueBasics()
    {
        CastQueue q;
        CHECK(q.Next(0) == Cast::None);

        // Due casts start; the 3 s spacing holds the next one.
        q.Schedule(Cast::SawBoomerang, 1000);
        q.Schedule(Cast::RepairRun, 2000);
        CHECK(q.Next(999) == Cast::None);
        CHECK(q.Next(1000) == Cast::SawBoomerang);
        q.Started(Cast::SawBoomerang, 1000, 15000);
        CHECK(q.Due(Cast::SawBoomerang) == 16000);
        CHECK(q.Next(2000) == Cast::None);          // due, but within 3 s of the boomerang
        CHECK(q.Next(3999) == Cast::None);
        CHECK(q.Next(4000) == Cast::RepairRun);

        // Nothing during a repair run / channel.
        q.Started(Cast::RepairRun, 4000, 20000);
        q.SetBusy(true);
        q.ChannelStarted(5000, kTazerAfterChannelMs(false));
        CHECK(q.Due(Cast::Tazer) == 17000);         // 12 s after the channel start
        CHECK(q.Next(16000) == Cast::None);         // the boomerang is due, but the channel runs
        q.SetBusy(false);                           // the channel was stopped at 11 s
        CHECK(q.Next(16000) == Cast::None);         // Tazer is due within 3 s: everything else waits
        CHECK(q.Next(16999) == Cast::None);
        CHECK(q.Next(17000) == Cast::Tazer);        // Tazer first, ahead of the older boomerang
        q.Started(Cast::Tazer, 17000, 0);
        CHECK(q.Due(Cast::Tazer) == CastQueue::kNever);
        CHECK(q.Next(19999) == Cast::None);
        CHECK(q.Next(20000) == Cast::SawBoomerang); // 3 s after Tazer

        // Skipped on a completed repair.
        CastQueue r;
        r.ChannelStarted(0, kTazerAfterChannelMs(true));
        CHECK(r.Due(Cast::Tazer) == 12000);
        r.RepairCompleted();
        CHECK(r.Due(Cast::Tazer) == CastQueue::kNever);
        CHECK(r.Next(12000) == Cast::None);

        // Ties: the repair run goes first.
        CastQueue t;
        t.Schedule(Cast::ClusterBomb, 500);
        t.Schedule(Cast::RepairRun, 500);
        t.Schedule(Cast::SawBoomerang, 500);
        CHECK(t.Next(500) == Cast::RepairRun);
        // Earliest due first otherwise.
        CastQueue e;
        e.Schedule(Cast::ClusterBomb, 100);
        e.Schedule(Cast::RepairRun, 200);
        CHECK(e.Next(300) == Cast::ClusterBomb);
        CHECK(std::string(CastName(Cast::Tazer)) == "tazer");
    }

    // A whole heroic stage 2 at 100 ms ticks: every two starts are at least 3 s apart, nothing starts during a channel,
    // Tazer lands 12 s after each channel start (no other cast moved it).
    void TestCastQueueTimeline()
    {
        Sim s;
        s.heroic = true;
        s.q.Schedule(Cast::SawBoomerang, kBoomerangFirstMs(true));
        s.q.Schedule(Cast::RepairRun, kRepairFirstMs(true));
        s.q.Schedule(Cast::ClusterBomb, kClusterFirstMs(true));
        std::vector<Ms> channelStarts;
        Ms channelEnd = -1;
        Ms runStart = -1;
        for (Ms now = 0; now <= 60000; now += 100)
        {
            // A run reaches the wreck 1.5 s after it starts; the channel always gets stopped 2 s in (the group kicks).
            if (runStart >= 0 && now == runStart + 1500)
            {
                s.q.ChannelStarted(now, kTazerAfterChannelMs(true));
                channelStarts.push_back(now);
                channelEnd = now + 2000;
            }
            if (channelEnd >= 0 && now == channelEnd)
            {
                s.q.SetBusy(false);
                channelEnd = -1;
                runStart = -1;
            }
            std::size_t const before = s.starts.size();
            s.Tick(now);
            if (s.starts.size() > before && s.starts.back().second == Cast::RepairRun)
                runStart = now;
        }
        CHECK(!s.starts.empty());
        for (std::size_t i = 1; i < s.starts.size(); ++i)
            CHECK(s.starts[i].first - s.starts[i - 1].first >= kQueueSpacingMs);
        // Nothing between a run's start and its channel's end (run 1.5 s + channel 2 s).
        for (std::size_t i = 0; i < s.starts.size(); ++i)
            if (s.starts[i].second == Cast::RepairRun && i + 1 < s.starts.size())
                CHECK(s.starts[i + 1].first >= s.starts[i].first + 3500);
        // Tazer exactly 12 s after every channel start inside the window.
        std::size_t tazers = 0;
        for (auto const& [t, c] : s.starts)
            if (c == Cast::Tazer)
            {
                ++tazers;
                bool matched = false;
                for (Ms cs : channelStarts)
                    matched = matched || t == cs + kTazerAfterChannelMs(true);
                CHECK(matched);
            }
        CHECK(tazers >= 2);
        // First starts: the boomerang at 3 s, the run at 8 s, the bomb waits 3 s after the run's channel ends.
        CHECK(s.starts[0].first == 3000 && s.starts[0].second == Cast::SawBoomerang);
        CHECK(s.starts[1].first == 8000 && s.starts[1].second == Cast::RepairRun);
        CHECK(s.starts[2].second == Cast::ClusterBomb && s.starts[2].first == 11500);
    }

    // After the blast (Salvaged Saw): Tazer at 9 s then every 15 s, the saw at 6 s then every 15 s, all spaced.
    void TestCastQueueSalvaged()
    {
        Sim s;
        s.heroic = false;
        s.salvaged = true;
        s.q.Schedule(Cast::SawSpin, kSalvagedSawFirstMs(false));
        s.q.Schedule(Cast::Tazer, kTazerSalvagedFirstMs(false));
        s.q.Schedule(Cast::SawBoomerang, 7000);
        for (Ms now = 0; now <= 40000; now += 100)
            s.Tick(now);
        CHECK(s.starts.size() >= 5);
        CHECK(s.starts[0].first == 6000 && s.starts[0].second == Cast::SawSpin);
        CHECK(s.starts[1].first == 9000 && s.starts[1].second == Cast::Tazer);     // Tazer first over the boomerang
        CHECK(s.starts[2].first == 12000 && s.starts[2].second == Cast::SawBoomerang);
        CHECK(s.starts[3].second == Cast::SawSpin && s.starts[3].first == 21000);
        CHECK(s.starts[4].second == Cast::Tazer && s.starts[4].first == 24000);
        for (std::size_t i = 1; i < s.starts.size(); ++i)
            CHECK(s.starts[i].first - s.starts[i - 1].first >= kQueueSpacingMs);
    }

    void TestGeometry()
    {
        // LineEnd: through the target to the full length.
        Vec2 const e = LineEnd({ 0.f, 0.f }, { 3.f, 4.f }, 25.f, 0.f);
        CHECK(Near(e.x, 15.f) && Near(e.y, 20.f));
        Vec2 const f = LineEnd({ 1.f, 1.f }, { 1.f, 1.f }, 10.f, 0.f);    // target on top: the facing
        CHECK(Near(f.x, 11.f) && Near(f.y, 1.f));

        // Bomblets: 6 to 10 yd from the bomb.
        Vec2 const c{ -290.f, -513.f };
        auto const spots = BombletSpots(c, { { 0.f, 0.5f, 0.99f } }, { { 0.f, 0.5f, 1.f } }, true);
        CHECK(Near(DeadminesKit::Distance(c, spots[0]), 6.f));
        CHECK(Near(DeadminesKit::Distance(c, spots[1]), 8.f));
        CHECK(Near(DeadminesKit::Distance(c, spots[2]), 10.f));
        auto const clamped = BombletSpots(c, { { -1.f, 2.f, 0.25f } }, { { -3.f, 7.f, 0.f } }, false);
        for (Vec2 const& p : clamped)
        {
            float const d = DeadminesKit::Distance(c, p);
            CHECK(d >= 6.f - 0.01f && d <= 10.f + 0.01f);
        }

        // Frontal cone 90 degrees, 10 yd, facing +x.
        CHECK(InFrontalCone({ 0.f, 0.f }, 0.f, { 5.f, 0.f }, 90.f, 10.f));
        CHECK(InFrontalCone({ 0.f, 0.f }, 0.f, { 5.f, 4.9f }, 90.f, 10.f));     // 44.4 degrees off
        CHECK(!InFrontalCone({ 0.f, 0.f }, 0.f, { 5.f, 5.2f }, 90.f, 10.f));    // 46 degrees off
        CHECK(!InFrontalCone({ 0.f, 0.f }, 0.f, { -3.f, 0.f }, 90.f, 10.f));    // behind
        CHECK(!InFrontalCone({ 0.f, 0.f }, 0.f, { 11.f, 0.f }, 90.f, 10.f));
        CHECK(InFrontalCone({ 0.f, 0.f }, 0.f, { 11.f, 0.f }, 90.f, 10.f, 1.5f));
        CHECK(InFrontalCone({ 0.f, 0.f }, 6.2f, { 5.f, 0.f }, 90.f, 10.f));     // facing wraps past 2 pi
    }

    void TestNumbers()
    {
        // Build spec percentages and timers.
        CHECK(kSawSpinPct(false) == 40.f && kSprayPct(true) == 30.f && kRunawayPct(false) == 35.f);
        CHECK(kBoomerangPct(true) == 25.f && kOverloadPct(true) == 60.f && kClusterPct(true) == 30.f);
        CHECK(kBombletPct(true) == 30.f && kSprayTankPct(false) == 30.f);
        CHECK(kHaywireFirstMs(false) == 8000 && kHaywireEveryMs(true) == 15000);
        CHECK(!kChainedHaywire(false) && kChainedHaywire(true) && kChainWarnMs(true) == 1500);
        CHECK(!kClusterBomb(false) && kClusterBomb(true));
        CHECK(kRepairFirstMs(true) == 8000 && kRepairEveryMs(false) == 20000);
        CHECK(kOverloadRadius(false) == 10.f && kOverloadWarnMs(false) == 3000);
        // The return pass at about 10 yd comes 1.5 s after the out pass.
        float const d = 10.f;
        float const gap = (2.f * kBoomerangLength(false) - 2.f * d) / kBoomerangSpeed(false);
        CHECK(Near(gap, 1.5f));
    }
}

int main()
{
    TestSlice();
    TestMalfunctionPick();
    TestRebootLadder();
    TestRepairBreak();
    TestTazer();
    TestCastQueueBasics();
    TestCastQueueTimeline();
    TestCastQueueSalvaged();
    TestGeometry();
    TestNumbers();
    return Report("sneed_test");
}
