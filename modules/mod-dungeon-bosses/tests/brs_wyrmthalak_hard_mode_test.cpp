// Host tests for WyrmthalakHardModeLogic.h (B9: Overlord Wyrmthalak's hard mode, the war horn): the slice, the horn's
// refusals (against the instance's rule), the hard mode health x the flex ladder, Tribal Ward, the unlocks and their
// cast book (a fight simulation of the queue hand-over), the shard's Overcharge, the chained axes' G1 drill parity,
// the rider cap, Caustic Poison and Rabies numbers, the cap-3 burn fallback, the spit's patches and its picks.
#include "UrokLogic.h"
#include "WyrmthalakHardModeLogic.h"
#include "check.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <map>
#include <set>
#include <vector>

using namespace BlackrockSpireRework;
using namespace BrsWarHorn;
using BrsWyrmthalak::Tribe;

namespace
{
    bool Near(double a, double b, double eps = 0.5)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation, and never in B8's.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210290 && kSpellSlice.last == 210339);
        std::set<std::uint32_t> ids;
        for (std::uint32_t id = kFirstSpell; id <= kLastSpell; ++id)
        {
            CHECK(kSpellSlice.Contains(id));
            CHECK(!BrsWyrmthalak::kSpellSlice.Contains(id));
            ids.insert(id);
        }
        CHECK(ids.size() == 17);
        CHECK(kFirstSpell == 210290 && kLastSpell == 210306);
        // The hard mode's kill slot is its own and fights in its boss's arena.
        CHECK(IsHardModeSlot(BOSS_WAR_HORN));
        CHECK(!ArenaFor(BOSS_WAR_HORN).Empty());
        CHECK(GO_BRS_WAR_HORN == 301255);
        CHECK(kGameObjectsReservation.Contains(GO_BRS_WAR_HORN));
        // The horn stands at the ramp head (handoff section 3.8), on the ledge's south-west shoulder.
        CHECK(Near(kWarHornSpot.x, -52.5) && Near(kWarHornSpot.y, -503.0) && Near(kWarHornSpot.z, 89.1));
        // Tags clear of B8's (1-6).
        CHECK(TAG_WH_SHARD > 6);
    }

    void TestHorn()
    {
        using DungeonKit::State::Done;
        using DungeonKit::State::InProgress;
        using DungeonKit::State::NotStarted;
        std::uint32_t const fail = DungeonKit::State::Fail;
        CHECK(HornRefusalFor(true, NotStarted, false) == HornRefusal::None);
        CHECK(HornRefusalFor(true, fail, false) == HornRefusal::None);      // again after a wipe
        CHECK(HornRefusalFor(false, NotStarted, false) == HornRefusal::NotHeroic);
        CHECK(HornRefusalFor(true, InProgress, false) == HornRefusal::Fighting);
        CHECK(HornRefusalFor(true, Done, false) == HornRefusal::Dead);
        CHECK(HornRefusalFor(true, NotStarted, true) == HornRefusal::AlreadyBlown);
        // The object never offers what the instance refuses (WarHornChangeAllowed is the instance's rule for 1).
        for (bool heroic : { false, true })
            for (std::uint32_t state : { NotStarted, InProgress, fail, Done })
            {
                bool const usable = HornRefusalFor(heroic, state, false) == HornRefusal::None;
                CHECK(usable == WarHornChangeAllowed(1, heroic, state));
            }
        for (HornRefusal r : { HornRefusal::NotHeroic, HornRefusal::Fighting, HornRefusal::Dead,
            HornRefusal::AlreadyBlown })
            CHECK(HornRefusalText(r)[0] != '\0');
        CHECK(HornRefusalText(HornRefusal::None)[0] == '\0');
        // The flag is per pull: an attempt that ends (a wipe) clears it; a kill records slot 26.
        CHECK(AttemptEnded(InProgress, NotStarted));
        CHECK(AttemptEnded(InProgress, fail));
        CHECK(!AttemptEnded(InProgress, Done));
        CHECK(BOSS_WAR_HORN == 26);
        CHECK(DATA_WAR_HORN == 33);
        CHECK(BrsWyrmthalak::EMOTE_WT_HORN == 7);
    }

    void TestHealth()
    {
        // Section 7 #22: the hard mode numbers x the ladder (SP: 900,000 / 225,000 / 13,500 at 10).
        CHECK(DungeonKit::Flex::HealthAt(5, kBossHealthAt5) == 400000);
        CHECK(DungeonKit::Flex::HealthAt(10, kBossHealthAt5) == 900000);
        CHECK(DungeonKit::Flex::HealthAt(10, kChampionHealthAt5) == 225000);
        CHECK(DungeonKit::Flex::HealthAt(10, kRiderHealthAt5) == 13500);
        CHECK(DungeonKit::Flex::HealthAt(7, kBossHealthAt5) == 600000);
        // SP tuning: 700,000 at 5 (400k + 3 x 100k), about 3:05 at 4,440 x 0.85.
        std::uint32_t const total = kBossHealthAt5 + 3 * kChampionHealthAt5;
        CHECK(total == 700000);
        CHECK(Near(total / (4440. * 0.85), 185.5, 1.0));
        // His heroic base comes back on a reset: the held max over the ladder (260k at 5, every count).
        for (std::uint32_t n = 5; n <= 10; ++n)
        {
            std::uint32_t const held = DungeonKit::Flex::HealthAt(n, 260000);
            CHECK(BaseBeforeHardMode(held, n) == 260000);
        }
        CHECK(BaseBeforeHardMode(260000, 0) == 260000);      // not held: the ladder of 5
        CHECK(BaseBeforeHardMode(260000, 3) == 260000);      // clamped to 5
    }

    void TestTribalWard()
    {
        CHECK(TribalWardTakenPct(0) == 0);
        CHECK(TribalWardTakenPct(1) == -20);
        CHECK(TribalWardTakenPct(2) == -40);
        CHECK(TribalWardTakenPct(3) == -60);
        CHECK(TribalWardTakenPct(7) == -60);
        CHECK(TribalWardStacks(3) == kTribalWardMaxStacks);
        CHECK(kTribesPerOrder == 2);
        // Two tribes an order (B8's OrderTribes), in turn.
        std::vector<Tribe> two = BrsWyrmthalak::OrderTribes(Tribe::Spirestone, kTribesPerOrder);
        CHECK(two.size() == 2 && two[0] == Tribe::Spirestone && two[1] == Tribe::Smolderthorn);
    }

    void TestUnlocks()
    {
        CHECK(UnlockOf(Tribe::Bloodaxe) == Unlock::CausticVenom);
        CHECK(UnlockOf(Tribe::Smolderthorn) == Unlock::EmpoweredDragonfire);
        CHECK(UnlockOf(Tribe::Spirestone) == Unlock::ShadowflameSpit);
        std::set<std::uint32_t> casts;
        for (Unlock u : kUnlocks)
        {
            CastRule const r = RuleOf(u);
            CHECK(r.id > BrsWyrmthalak::kHardModeCastBase);
            CHECK(r.id != BrsWyrmthalak::CAST_BREATH);
            CHECK(UnlockOfCast(r.id) == u);
            CHECK(r.priority < BrsWyrmthalak::kBreathPriority);
            CHECK(r.holdMs < r.everyMs);
            casts.insert(r.id);
            CHECK(UnlockName(u)[0] != '?');
        }
        CHECK(casts.size() == 3);
        CHECK(!UnlockOfCast(BrsWyrmthalak::CAST_BREATH));
        CHECK(!UnlockOfCast(0));
        // SP: Caustic Roar 8 s after the unlock, every 20 s, 2.5 s; Spear 10 s, 30 s; Spit 5 s, 15 s.
        CHECK(RuleOf(Unlock::CausticVenom).firstMs == 8000 && RuleOf(Unlock::CausticVenom).everyMs == 20000);
        CHECK(RuleOf(Unlock::CausticVenom).holdMs == 2500);
        CHECK(RuleOf(Unlock::EmpoweredDragonfire).firstMs == 10000);
        CHECK(RuleOf(Unlock::EmpoweredDragonfire).everyMs == 30000);
        CHECK(RuleOf(Unlock::ShadowflameSpit).firstMs == 5000 && RuleOf(Unlock::ShadowflameSpit).everyMs == 15000);

        UnlockBook book;
        CHECK(!book.IsOpen(Unlock::CausticVenom));
        CHECK(!book.DueAt(Unlock::CausticVenom));
        CHECK(book.TakePushes(0).empty());
        CHECK(book.Open(Unlock::CausticVenom, 40000));
        CHECK(!book.Open(Unlock::CausticVenom, 50000));     // once
        CHECK(book.DueAt(Unlock::CausticVenom) == 48000u);
        std::vector<UnlockBook::Push> p = book.TakePushes(40000);
        CHECK(p.size() == 1 && p[0].id == CAST_CAUSTIC_ROAR && p[0].inMs == 8000 && p[0].priority == 1);
        CHECK(book.TakePushes(40100).empty());              // handed over once
        book.Started(Unlock::CausticVenom, 48300);
        p = book.TakePushes(48350);
        CHECK(p.size() == 1 && p[0].inMs == 19950);         // 20 s from the start
        book.Refused(Unlock::CausticVenom, 68300);
        p = book.TakePushes(68300);
        CHECK(p.size() == 1 && p[0].inMs == BrsWyrmthalak::kRetryMs);
        p = book.TakePushes(80000);
        CHECK(p.empty());
        // Overdue (pushed late): due now.
        CHECK(book.Open(Unlock::ShadowflameSpit, 1000));
        p = book.TakePushes(9000);
        CHECK(p.size() == 1 && p[0].id == CAST_SHADOWFLAME_SPIT && p[0].inMs == 0);
    }

    // A model of B8's queue as the hard mode sees it: the entry is consumed (StartHardModeCast), OnCast is answered;
    // the next OnUpdate pushes the next due time. Every unlocked cast keeps firing on its cadence (never lost, never
    // doubled), whatever the order of the deaths.
    void TestCastCadence()
    {
        UnlockBook book;
        std::map<std::uint32_t, std::uint64_t> queue;          // id -> due (B8's queue)
        std::map<std::uint32_t, std::vector<std::uint64_t>> fired;
        std::uint64_t busyUntil = 0;
        std::uint64_t const tick = 100;
        for (std::uint64_t now = 0; now <= 300000; now += tick)
        {
            if (now == 30000)
                book.Open(UnlockOf(Tribe::Bloodaxe), now);
            if (now == 90000)
                book.Open(UnlockOf(Tribe::Smolderthorn), now);
            if (now == 150000)
                book.Open(UnlockOf(Tribe::Spirestone), now);
            // OnUpdate (before B8's beats).
            for (UnlockBook::Push const& push : book.TakePushes(now))
                queue[push.id] = now + push.inMs;
            // RunQueue: the earliest due when not busy (all priority 1; the breath ignored here).
            if (now < busyUntil)
                continue;
            std::uint32_t best = 0;
            for (auto const& [id, due] : queue)
                if (due <= now && (!best || due < queue[best]))
                    best = id;
            if (!best)
                continue;
            std::optional<Unlock> const u = UnlockOfCast(best);
            CHECK(u.has_value());
            book.Started(*u, now);                          // OnCast
            fired[best].push_back(now);
            busyUntil = now + RuleOf(*u).holdMs + 1000;     // hold + B8's spacing
            queue.erase(best);                              // StartHardModeCast
        }
        CHECK(fired[CAST_CAUSTIC_ROAR].size() >= 13);
        CHECK(fired[CAST_CAUSTIC_ROAR].front() == 38000);
        CHECK(fired[CAST_SPEAR_CHAIN].front() >= 100000 && fired[CAST_SPEAR_CHAIN].front() <= 103500);
        CHECK(fired[CAST_SHADOWFLAME_SPIT].front() >= 155000 && fired[CAST_SHADOWFLAME_SPIT].front() <= 158500);
        for (auto const& [id, times] : fired)
        {
            std::uint32_t const every = RuleOf(*UnlockOfCast(id)).everyMs;
            for (std::size_t i = 1; i < times.size(); ++i)
            {
                // Never sooner than its cadence, never more than one spacing-and-hold of the others late.
                CHECK(times[i] - times[i - 1] >= every);
                CHECK(times[i] - times[i - 1] <= every + 2 * 3500);
            }
        }
    }

    void TestShardsAndOvercharge()
    {
        CHECK(kShardWaitMs == 10000);
        CHECK(kStolenPowerCap == 5);
        CHECK(!OverchargesAt(4));
        CHECK(OverchargesAt(5));
        CHECK(OverchargesAt(6));
        CHECK(Near(kOverchargePct, 40.0, 0.01));
        // Urok's shard numbers (UrokLogic.h, reused through UrokShards.h): 2 yd, 3 yd/s; the cap is the heroic one.
        CHECK(Near(BrsUrok::kShardRadiusYd, 2.0, 0.01));
        CHECK(Near(BrsUrok::kShardCrawlYdPerSec, 3.0, 0.01));
        CHECK(BrsUrok::kStolenPowerCap(true) == kStolenPowerCap);
    }

    void TestChainedAxes()
    {
        // The G1 drill's rows 5 and 6 (MechanicDrill.h, `blackrock-spire-followups`): the chain line 5 ... width=2
        // persist=6000 tick=2000 pct=10 weak=1 after a 2 s warning; the haul width=3, 1.5 s, pct=35 weak=1, no
        // exclusion (tag 6, the gate).
        CHECK(Near(kAxeChainWidth, 2.0, 0.01));
        CHECK(kAxeChainWarnMs == 2000);
        CHECK(kAxeChainLifeMs - kAxeChainWarnMs == 6000);
        CHECK(kAxeChainTickMs == 2000);
        CHECK(Near(kAxeChainPct, 10.0, 0.01));
        CHECK(Near(kHaulWidth, 3.0, 0.01));
        CHECK(kHaulWarnMs == 1500);
        CHECK(Near(kHaulPct, 35.0, 0.01));
        CHECK(kHaulExcludeChampionEnd == 0.f);
        // The crossing ticks: 2, 4, 6, 8 s after the axes land; the haul resolves 1.5 s after the chain ends, and the
        // axe object outlives both.
        std::vector<std::uint32_t> ticks;
        for (std::uint32_t t = kAxeChainWarnMs; t <= kAxeChainLifeMs; t += kAxeChainTickMs)
            ticks.push_back(t);
        CHECK(ticks.size() == 4 && ticks.back() == kAxeChainLifeMs);
        CHECK(kAxeObjectLifeSec * 1000 > kAxeChainLifeMs + kHaulWarnMs);
        // Each Axe Volley marks 2 / 4 (B8's kAxeTargets): as many chains.
        CHECK(BrsWyrmthalak::kAxeTargets.At(5) == 2 && BrsWyrmthalak::kAxeTargets.At(10) == 4);
    }

    void TestRiders()
    {
        CHECK(kRiderCap.At(5) == 4);
        CHECK(kRiderCap.At(6) == 8);
        CHECK(kRiderCap.At(10) == 8);
        CHECK(KeepRider(0, 5));
        CHECK(KeepRider(3, 5));
        CHECK(!KeepRider(4, 5));
        CHECK(KeepRider(7, 10));
        CHECK(!KeepRider(8, 10));
        CHECK(kRiderRetargetMs == 8000);
        // An order brings 2 / 4 riders (B8's kRiderTargets): with two tribes an order the Bloodaxe answers every
        // other order at most, so the cap fills in two answers at 5 players.
        CHECK(BrsWyrmthalak::kRiderTargets.At(5) * 2 == kRiderCap.At(5));
        CHECK(BrsWyrmthalak::kRiderTargets.At(10) * 2 == kRiderCap.At(10));
        // Rabies (HG6 heroic): 1.5% a stack every 3 s, 5 stacks: 7.5% every 3 s at the cap.
        CHECK(kRabiesHundredthsPerStack == 150);
        CHECK(kRabiesTickMs == 3000 && kRabiesMaxStacks == 5);
        CHECK(kRabiesMs > kRabiesTickMs * 2);
    }

    void TestVenomAndSpear()
    {
        CHECK(kPoisonHundredthsPerStack == 50);             // 0.5% a stack
        CHECK(kPoisonTickMs == 2000 && kPoisonMaxStacks == 10 && kPoisonMs == 20000);
        CHECK(kRoarCastMs == 2500);
        CHECK(Near(kRoarPct, 20.0, 0.01));
        CHECK(kRoarPoisonStacks == 2);
        // Ten stacks: 5% of the row every 2 s, as much as standing in a burn.
        CHECK(kPoisonHundredthsPerStack * kPoisonMaxStacks == 500);
        CHECK(Near(kSpearImpactPct, 10.0, 0.01));
        CHECK(Near(kSpearChainWidth, 2.0, 0.01));
        CHECK(kSpearChainMs == 20000 && kSpearChainTickMs == 2000);
        CHECK(Near(kSpearChainPct, 10.0, 0.01));
        // The spear lands well inside its throw's hold from anywhere on the ledge (about 45 yd across at most).
        CHECK(45.f / kSpearMissileSpeed * 1000.f < 2000.f);
        // A chain lives 20 s and comes every 30 s: one at a time.
        CHECK(kSpearChainMs < RuleOf(Unlock::EmpoweredDragonfire).everyMs);
    }

    void TestBurns()
    {
        BurnNumbers const heroic{};
        CHECK(Near(heroic.length, 20.0, 0.01) && heroic.lifeMs == 8000 && heroic.graceMs == 3000);
        BurnNumbers const before = HardModeBurn(heroic, false);
        CHECK(before.lifeMs == heroic.lifeMs && before.maxAlive == 0 && Near(before.length, 20.0, 0.01));
        BurnNumbers const after = HardModeBurn(heroic, true);
        CHECK(after.lifeMs == 120000);
        CHECK(Near(after.length, BrsWyrmthalak::kBreathLength, 0.01));     // the whole cone
        CHECK(after.graceMs == 3000);
        CHECK(after.maxAlive == 3);
        // Section 7 #28: the open edge is short of the edge walk, so the cap-3 fallback is the one built. Uncapped,
        // a breath every 15 s for 120 s is 8 burns, far over the ledge; three whole cones fit under it.
        CHECK(kOpenEdgeChordYd < kEdgeWalkNeedsYd);
        std::uint32_t const uncapped = after.lifeMs / BrsWyrmthalak::kBreathEveryMs;
        CHECK(uncapped == 8);
        float const cone = ConeArea(BrsWyrmthalak::kBreathLength, BrsWyrmthalak::kBreathAngleDeg);
        CHECK(Near(cone, 327.2, 1.0));
        CHECK(uncapped * cone > 2.f * kLedgeAreaSqYd);
        CHECK(after.maxAlive * cone < kLedgeAreaSqYd);
    }

    void TestSpit()
    {
        CHECK(Near(kSpitRadius, 4.0, 0.01) && kSpitWarnMs == 2000 && Near(kSpitPct, 25.0, 0.01));
        CHECK(kSpitPatches.At(5) == 2 && kSpitPatches.At(6) == 3 && kSpitPatches.At(10) == 3);
        CHECK(kPatchLifeMs == 40000 && kPatchTickMs == 1000 && Near(kPatchPct, 5.0, 0.01));
        // SP: up to 9 patches at once at 10 players (3 spits of 3), 6 at 5.
        CHECK(MaxPatchesAlive(10) == 9);
        CHECK(MaxPatchesAlive(5) == 6);
        // The spit lands inside its warning from anywhere on the ledge.
        CHECK(45.f / kSpitMissileSpeed * 1000.f < float(kSpitWarnMs) + 500.f);

        // Picks: distinct, in range, k capped by n, every index reachable.
        std::uint32_t seed = 12345;
        auto rand = [&seed](std::uint32_t m) -> std::uint32_t
        {
            seed = seed * 1103515245u + 12345u;
            return m ? (seed >> 8) % m : 0;
        };
        std::set<std::uint32_t> seen;
        for (int round = 0; round < 200; ++round)
        {
            std::vector<std::uint32_t> pick = PickIndices(10, 3, rand);
            CHECK(pick.size() == 3);
            std::set<std::uint32_t> unique(pick.begin(), pick.end());
            CHECK(unique.size() == 3);
            for (std::uint32_t i : pick)
            {
                CHECK(i < 10);
                seen.insert(i);
            }
        }
        CHECK(seen.size() == 10);
        CHECK(PickIndices(2, 3, rand).size() == 2);
        CHECK(PickIndices(0, 3, rand).empty());
        CHECK(PickIndices(5, 0, rand).empty());
    }
}

int main()
{
    TestSlice();
    TestHorn();
    TestHealth();
    TestTribalWard();
    TestUnlocks();
    TestCastCadence();
    TestShardsAndOvercharge();
    TestChainedAxes();
    TestRiders();
    TestVenomAndSpear();
    TestBurns();
    TestSpit();

    return Report("brs_wyrmthalak_hard_mode_test");
}
