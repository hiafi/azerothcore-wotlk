// Host tests for RhahkZorLogic.h (WP-B1): ids in the slice, the build spec numbers, the heroic random spots (>= 6 yd
// from every player), circle and rubble counts, the once-per-wave ledger and the Evoker's cast order.
#include "RhahkZorLogic.h"
#include "check.h"
#include <cstdint>
#include <optional>
#include <vector>

using namespace RhahkZor;
using DeadminesKit::Distance;
using DeadminesKit::Vec2;

namespace
{
    // Deterministic sampler: a small LCG over a 40 x 40 yd box around (0, 0).
    struct Lcg
    {
        std::uint32_t state = 12345;

        float Next()
        {
            state = state * 1664525u + 1013904223u;
            return static_cast<float>(state >> 8) / static_cast<float>(1u << 24);
        }
    };

    void TestIds()
    {
        std::uint32_t const ids[] = { SPELL_RZ_CAVE_IN, SPELL_RZ_CAVE_IN_TREMOR, SPELL_RZ_CAVE_IN_ROCKS,
            SPELL_RZ_RUBBLE, SPELL_RZ_WHIRLWIND_CAST, SPELL_RZ_WHIRLWIND_SPIN, SPELL_RZ_WHIRLWIND,
            SPELL_RZ_WHIRLWIND_KNOCKBACK, SPELL_RZ_SPOTTED, SPELL_RZ_FIREBALL_VOLLEY };
        for (std::uint32_t id : ids)
            CHECK(kSlice.Contains(id));
        CHECK(kSlice.first == 205210u);
        CHECK(kSlice.last == 205229u);
    }

    void TestBuildSpecNumbers()
    {
        // DM Build spec: RZ1 20%, RZ2 5%, RZ3 5%/s, RZ4 15%/tick, RZ8 40%; same percent on both difficulties.
        CHECK(kCaveInPct(false) == 20.f && kCaveInPct(true) == 20.f);
        CHECK(kTremorPct(false) == 5.f && kTremorPct(true) == 5.f);
        CHECK(kRubblePct(true) == 5.f);
        CHECK(kWhirlwindPct(false) == 15.f && kWhirlwindPct(true) == 15.f);
        CHECK(kVolleyPct(true) == 40.f);
        // RefFlat on the Deadmines rows (normal 1,300, heroic 4,120 non-tank).
        CHECK(DeadminesKit::RefFlatValue(1300, 1290, kCaveInPct(false), false) == 260u);
        CHECK(DeadminesKit::RefFlatValue(4120, 4110, kCaveInPct(true), false) == 824u);
        CHECK(DeadminesKit::RefFlatValue(1300, 1290, kTremorPct(false), false) == 65u);
        CHECK(DeadminesKit::RefFlatValue(4120, 4110, kVolleyPct(true), false) == 1648u);
        // Shapes and timers.
        CHECK(kCaveInRadius == 5.f && kWhirlwindRadius == 8.f);
        CHECK(kRandomCircles(false) == 0u && kRandomCircles(true) == 5u);
        CHECK(kRandomMinFromPlayer > kCaveInRadius);        // a player at the minimum distance starts outside
        CHECK(kCaveInFirst == Ms(8000) && kCaveInEvery == Ms(15000) && kCaveInWarn == Ms(2000));
        CHECK(kLookoutWarn == Ms(1500));
        CHECK(kRubbleDuration == Ms(10000) && kRubbleTick == Ms(1000));
        CHECK(kWhirlwindFirst == Ms(20000) && kWhirlwindEvery == Ms(40000));
        CHECK(kWhirlwindCast == Ms(2000) && kWhirlwindSpin == Ms(4000) && kWhirlwindTick == Ms(1000));
        CHECK(kWhirlwindSpin / kWhirlwindTick == 4);       // four ticks per spin (ticks at 0, 1, 2, 3 s)
        CHECK(kSlamFirst == Ms(10000) && kSlamEvery == Ms(50000) && kSlamStun == Ms(1500));
        CHECK(kFlamestrikeFirst == Ms(5000) && kFlamestrikeEvery == Ms(12000) && kFlamestrikeGround == Ms(8000));
        CHECK(kVolleyFirst == Ms(8000) && kVolleyEvery == Ms(14000) && kFireballFirst == Ms(2000));
        CHECK(kWardFirstMin < kWardFirstMax && kWardEveryMin < kWardEveryMax);
        // Patch math (DM): a 10 s patch clears 5 s before the next wave 15 s later.
        CHECK(kRubbleDuration < kCaveInEvery);
        // The second wave lands 1.5 s after the first, before the rubble of the first expires.
        CHECK(kCaveInWarn + kLookoutWarn < kCaveInWarn + kRubbleDuration);
    }

    void TestCounts()
    {
        CHECK(PlayerCircleCount(false, 5) == 1u);
        CHECK(PlayerCircleCount(false, 1) == 1u);
        CHECK(PlayerCircleCount(false, 0) == 0u);
        CHECK(PlayerCircleCount(true, 5) == 5u);
        CHECK(PlayerCircleCount(true, 0) == 0u);
        // DM: a heroic wave is 10 circles (5 players + 5 random), each leaving rubble; at most 10 patches.
        CHECK(RubbleCount(true, 5, 5, false) == 10u);
        CHECK(RubbleCount(true, 5, 3, false) == 8u);
        CHECK(RubbleCount(true, 5, 0, true) == 0u);        // Lookout: no rubble
        CHECK(RubbleCount(false, 1, 0, false) == 0u);      // normal: no rubble
        CHECK(LookoutFollows(true, true));
        CHECK(!LookoutFollows(true, false));
        CHECK(!LookoutFollows(false, true));
    }

    void TestRandomSpots()
    {
        std::vector<Vec2> const players = { { 0.f, 0.f }, { 3.f, 2.f }, { -6.f, 4.f }, { 8.f, -7.f }, { 2.f, -12.f } };
        for (std::uint32_t seed = 1; seed <= 200; ++seed)
        {
            Lcg rng;
            rng.state = seed;
            auto sampler = [&rng]() -> std::optional<Vec2>
            {
                float const x = rng.Next() * 40.f - 20.f;
                float const y = rng.Next() * 40.f - 20.f;
                if (rng.Next() < 0.1f)
                    return std::nullopt;    // a blocked ray
                return Vec2{ x, y };
            };
            std::vector<Vec2> const spots = PickRandomSpots(5, kRandomTries, sampler, players, kRandomMinFromPlayer,
                kRandomMinApart);
            CHECK(spots.size() <= 5u);
            for (Vec2 const& s : spots)
            {
                for (Vec2 const& p : players)
                    CHECK(Distance(s, p) >= kRandomMinFromPlayer);
                // never inside a random circle at cast
                for (Vec2 const& p : players)
                    CHECK(Distance(s, p) > kCaveInRadius);
            }
            for (std::size_t i = 0; i < spots.size(); ++i)
                for (std::size_t j = i + 1; j < spots.size(); ++j)
                    CHECK(Distance(spots[i], spots[j]) >= kRandomMinApart);
            // A 40 x 40 box with five players has room: every seed places all five.
            CHECK(spots.size() == 5u);
        }

        // A crowded sampler (every candidate near a player): nothing is placed, and the tries bound the loop.
        std::uint32_t calls = 0;
        auto crowded = [&calls]() -> std::optional<Vec2>
        {
            ++calls;
            return Vec2{ 1.f, 1.f };
        };
        std::vector<Vec2> const none = PickRandomSpots(5, kRandomTries, crowded, players, kRandomMinFromPlayer,
            kRandomMinApart);
        CHECK(none.empty());
        CHECK(calls == kRandomTries);

        // Count 0 (normal) never samples.
        calls = 0;
        CHECK(PickRandomSpots(0, kRandomTries, crowded, players, kRandomMinFromPlayer, kRandomMinApart).empty());
        CHECK(calls == 0u);

        CHECK(!FarFromAll({ 5.f, 0.f }, players, 6.f));     // 2.8 yd from (3, 2)
        CHECK(FarFromAll({ 10.f, 0.f }, players, 6.f));     // 7.3 yd from (3, 2) and from (8, -7)
        CHECK(FarFromAll({ -20.f, -20.f }, players, 6.f));
        CHECK(FarFromAll({ 0.f, 0.f }, {}, 6.f));
    }

    void TestLedger()
    {
        WaveLedger l;
        std::uint32_t const w1 = l.BeginWave();
        CHECK(w1 == 1u);
        l.Assign(101, w1);
        l.Assign(102, w1);
        std::uint64_t const alice = 0xA;
        std::uint64_t const bob = 0xB;
        CHECK(l.MayHit(101, alice));
        l.NoteHit(101, alice);
        CHECK(!l.MayHit(102, alice));     // the second circle of the same wave skips her
        CHECK(l.MayHit(102, bob));
        CHECK(l.MayHit(999, alice));      // unknown mechanic: no filter

        std::uint32_t const w2 = l.BeginWave();  // Lookout: its own wave, may hit her again
        l.Assign(201, w2);
        CHECK(l.MayHit(201, alice));
        l.NoteHit(201, alice);
        CHECK(!l.MayHit(201, alice));
        CHECK(!l.MayHit(101, alice));     // wave 1 still remembered

        // Old waves are dropped after kKeptWaves new ones.
        for (std::uint32_t i = 0; i < WaveLedger::kKeptWaves; ++i)
            l.BeginWave();
        CHECK(l.WaveOf(101) == 0u);
        CHECK(l.MayHit(101, alice));
        CHECK(l.WaveOf(201) == 0u);

        l.Clear();
        CHECK(l.BeginWave() == 1u);
        l.Assign(0, 1);                   // an invalid handle is ignored
        CHECK(l.WaveOf(0) == 0u);
    }

    void TestEvokerOrder()
    {
        CHECK(NextEvokerCast(true, true, true) == EvokerCast::Volley);
        CHECK(NextEvokerCast(false, true, true) == EvokerCast::Flamestrike);
        CHECK(NextEvokerCast(false, false, true) == EvokerCast::Fireball);
        CHECK(NextEvokerCast(false, false, false) == EvokerCast::None);
        CHECK(NextEvokerCast(true, false, false) == EvokerCast::Volley);
    }

    void TestShoot()
    {
        CHECK(!ShootInRange(4.9f));
        CHECK(ShootInRange(5.f));
        CHECK(ShootInRange(30.f));
        CHECK(!ShootInRange(30.1f));
    }
}

int main()
{
    TestIds();
    TestBuildSpecNumbers();
    TestCounts();
    TestRandomSpots();
    TestLedger();
    TestEvokerOrder();
    TestShoot();
    return Report("rhahk_zor_test");
}
