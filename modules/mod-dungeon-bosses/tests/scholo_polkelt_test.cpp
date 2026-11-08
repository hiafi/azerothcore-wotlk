// Host tests for PolkeltLogic.h (S7: Lorekeeper Polkelt (10901), "Chain Reaction"): the chain (ring overlap, the 1 s
// chained fuse, a ripe burst never reacts), the pool cap, the raise points, the bots' kill target, the reaction's
// numbers, the soft enrage, the examiner profile and the Hall of Secrets lesson.
#include "PolkeltLogic.h"
#include "SoloLessonLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <vector>

using namespace ScholomanceRework;
using namespace ScholoPolkelt;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // A small deterministic generator in [0, 1).
    struct Lcg
    {
        std::uint32_t state = 12345;

        float operator()()
        {
            state = state * 1664525u + 1013904223u;
            return static_cast<float>(state >> 8) / static_cast<float>(1u << 24);
        }
    };

    bool AnyFloor(Vec2)
    {
        return true;
    }

    void TestIds()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(SPELL_PK_SPECIMEN_BURST == 206250);
        CHECK(SPELL_PK_RIPENING == 206264);
        CHECK(kSpellSlice.Contains(SPELL_PK_SPECIMEN_BURST) && kSpellSlice.Contains(SPELL_PK_RIPENING));
        CHECK(NPC_SC_UNSTABLE_SPECIMEN == 300540 && NPC_SC_ROOTED_SPECIMEN == 300541);
        CHECK(NPC_SC_EXAMINER_POLKELT == 300550);
        // The boss spawns inside his arena.
        CHECK(PolkeltArena().Contains(kPolkeltSpawn.XY(), kPolkeltSpawn.z));
        CHECK(ArenaFor(BOSS_POLKELT).Contains(kPolkeltSpawn.XY(), kPolkeltSpawn.z));
    }

    void TestNumbers()
    {
        // SC "Build spec": batches, bursts, ripe, pools, the reaction, the enrage.
        CHECK(kFirstBatchMs == 10000 && kBatchEveryMs == 15000);
        CHECK(kWalkersPerBatch(false) == 2 && kRootedPerBatch(false) == 1);
        CHECK(kWalkersPerBatch(true) == 3 && kRootedPerBatch(true) == 3);
        CHECK(kSpecimenHealth(false) == 6000 && kSpecimenHealth(true) == 9000);
        CHECK(kFuseMs == 2000 && kChainedFuseMs == 1000 && Near(kBurstRadius, 6.f));
        CHECK(Near(kBurstPct(false), 30.f) && Near(kBurstPct(true), 40.f));
        CHECK(kRipeAfterMs == 30000 && kRipeWarnMs == 3000 && Near(kRipeRadius, 12.f));
        CHECK(Near(kRipePct(false), 40.f) && Near(kRipePct(true), 55.f));
        CHECK(Near(kPoolRadius, 6.f) && kPoolMs == 60000 && Near(kPoolPct(false), 8.f) && Near(kPoolPct(true), 12.f));
        CHECK(kPoolCap(false) == 6 && kPoolCap(true) == 8);     // the user's ruling: kept
        CHECK(kCorrodedPctPerStack == 5 && kCorrodedMs == 20000 && kCorrodedMaxStacks == 10);
        CHECK(kHardenedPct == 90);
        CHECK(kNoxiousEveryMs == 10000 && Near(kNoxiousPctPerStack, 0.3f));
        CHECK(kVolatileFirstMinMs == 7000 && kVolatileFirstMaxMs == 15000 && kVolatileEveryMs == 40000);

        // The pools on the measured hall (1,236 sq yd main hall, NAVMESH-REPORT section 7): the caps cover 55% / 73%,
        // the user's "about 75%" at heroic.
        float const pool = 3.14159265f * kPoolRadius * kPoolRadius;
        CHECK(Near(kPoolCap(false) * pool / 1236.f, 0.55f, 0.01f));
        CHECK(Near(kPoolCap(true) * pool / 1236.f, 0.73f, 0.01f));
    }

    void TestKillChain()
    {
        // A at the origin, B 5 yd away, C 10 yd from A (5 from B), D 20 yd away.
        SpecimenChain chain;
        std::uint32_t const a = chain.Add({ 0.f, 0.f }, false, 0);
        std::uint32_t const b = chain.Add({ 5.f, 0.f }, true, 0);
        std::uint32_t const c = chain.Add({ 10.f, 0.f }, false, 0);
        std::uint32_t const d = chain.Add({ 20.f, 0.f }, false, 0);

        auto fa = chain.Kill(a, 1000);
        CHECK(fa && fa->kind == BurstKind::Kill && fa->warnMs == 2000 && Near(fa->radius, 6.f));
        // A burning fuse is never lit or killed again.
        CHECK(!chain.Kill(a, 1100) && !chain.Light(a, 1100));
        CHECK(chain.Count(SpecimenPhase::Fusing) == 1);

        CHECK(chain.TakeBursts(2999).empty());
        std::vector<Burst> first = chain.TakeBursts(3000);
        CHECK(first.size() == 1 && first[0].id == a && first[0].kind == BurstKind::Kill);
        // B (5 yd) is lit, C (10 yd) is not: a 1 s chained fuse from now.
        CHECK(first[0].lit.size() == 1 && first[0].lit[0].id == b);
        CHECK(first[0].lit[0].kind == BurstKind::Chained && first[0].lit[0].warnMs == 1000);
        CHECK(!first[0].leavesPool);
        // Never in the same update: B resolves a second later, and lights C; D is never reached.
        CHECK(chain.TakeBursts(3000).empty());
        CHECK(chain.TakeBursts(3999).empty());
        std::vector<Burst> second = chain.TakeBursts(4000);
        CHECK(second.size() == 1 && second[0].id == b && second[0].kind == BurstKind::Chained);
        CHECK(second[0].lit.size() == 1 && second[0].lit[0].id == c);
        std::vector<Burst> third = chain.TakeBursts(5000);
        CHECK(third.size() == 1 && third[0].id == c && third[0].lit.empty());
        CHECK(chain.Find(d)->phase == SpecimenPhase::Standing);
        CHECK(chain.Live() == 1);
        chain.Compact();
        CHECK(chain.All().size() == 1 && chain.All()[0].id == d);
    }

    void TestOverlap()
    {
        // Two kills at once: two separate rings (overlaps stack in the registry: one hit per ring), resolved in order;
        // both rings hold the third specimen, which lights once.
        SpecimenChain chain;
        std::uint32_t const a = chain.Add({ 0.f, 0.f }, false, 0);
        std::uint32_t const b = chain.Add({ 2.f, 0.f }, false, 0);
        std::uint32_t const c = chain.Add({ 1.f, 3.f }, false, 0);
        CHECK(chain.Kill(b, 0).has_value());
        CHECK(chain.Kill(a, 0).has_value());
        std::vector<Burst> bursts = chain.TakeBursts(2000);
        CHECK(bursts.size() == 2 && bursts[0].id == a && bursts[1].id == b);
        CHECK(bursts[0].lit.size() == 1 && bursts[0].lit[0].id == c);
        CHECK(bursts[1].lit.empty());
        CHECK(chain.Find(c)->phase == SpecimenPhase::Fusing);
    }

    void TestCatalyst()
    {
        // His bounding radius 1 yd: a kill or chained ring 6 yd reaches him up to 7 yd off.
        CHECK(CatalystReacts(BurstKind::Kill, 6.9f, 6.f, 1.f));
        CHECK(CatalystReacts(BurstKind::Chained, 0.f, 6.f, 1.f));
        CHECK(!CatalystReacts(BurstKind::Kill, 7.1f, 6.f, 1.f));
        // A ripe burst never reacts, even on top of him.
        CHECK(!CatalystReacts(BurstKind::Ripe, 0.f, 12.f, 1.f));

        SpecimenChain chain;
        std::uint32_t const a = chain.Add({ 0.f, 0.f }, false, 0);
        std::uint32_t const b = chain.Add({ 4.f, 0.f }, false, 0);
        chain.Kill(a, 0);
        std::vector<Burst> one = chain.TakeBursts(2000, Vec2{ 3.f, 0.f }, 1.f);
        CHECK(one.size() == 1 && one[0].catalyst && one[0].lit.size() == 1);
        std::vector<Burst> two = chain.TakeBursts(3000, Vec2{ 3.f, 0.f }, 1.f);
        CHECK(two.size() == 1 && two[0].id == b && two[0].catalyst);
        // No boss (the detention lesson): never a reaction.
        SpecimenChain lesson(LessonChain());
        std::uint32_t const l = lesson.Add({ 0.f, 0.f }, false, 0);
        lesson.Kill(l, 0);
        std::vector<Burst> lb = lesson.TakeBursts(2000);
        CHECK(lb.size() == 1 && !lb[0].catalyst);

        // The reaction's hit: 1.5% of his health, divided by his Corroded so the hit lands at 1.5%.
        CHECK(CatalystBasePoints(175000, 0) == 2625);
        CHECK(CatalystBasePoints(175000, 10) == 1750);
        CHECK(CatalystBasePoints(360000, 0) == 5400);
        CHECK(CatalystBasePoints(360000, 20) == 3600);      // capped at 10 stacks (+50%)
        CHECK(CorrodedAfterReaction(0) == 1 && CorrodedAfterReaction(9) == 10 && CorrodedAfterReaction(10) == 10);
    }

    void TestRipe()
    {
        SpecimenChain chain;
        std::uint32_t const a = chain.Add({ 0.f, 0.f }, true, 1000);
        std::uint32_t const b = chain.Add({ 11.f, 0.f }, false, 20000);    // risen later, inside the 12 yd ring
        CHECK(chain.MsToRipe(a, 1000) == 30000);
        CHECK(chain.MsToRipe(a, 28000) == 3000);
        CHECK(chain.TakeRipening(30999).empty());
        std::vector<FuseStart> ripe = chain.TakeRipening(31000);
        CHECK(ripe.size() == 1 && ripe[0].id == a && ripe[0].kind == BurstKind::Ripe);
        CHECK(ripe[0].warnMs == 3000 && Near(ripe[0].radius, 12.f));
        CHECK(chain.Find(a)->phase == SpecimenPhase::Ripening);
        CHECK(chain.MsToRipe(a, 31000) == 0);
        // A ripening specimen cannot be killed or lit.
        CHECK(!chain.Kill(a, 32000) && !chain.Light(a, 32000));
        std::vector<Burst> bursts = chain.TakeBursts(34000, Vec2{ 0.f, 0.f }, 1.f);
        CHECK(bursts.size() == 1 && bursts[0].kind == BurstKind::Ripe);
        CHECK(!bursts[0].catalyst);                 // the catalyst has gone stale
        CHECK(bursts[0].leavesPool && Near(bursts[0].radius, 12.f));
        CHECK(bursts[0].lit.size() == 1 && bursts[0].lit[0].id == b && bursts[0].lit[0].kind == BurstKind::Chained);

        // `.dbtest scholo polkelt ripe`: every standing one starts its ripe fuse now, whatever its age.
        SpecimenChain forced;
        forced.Add({ 0.f, 0.f }, false, 5000);
        std::uint32_t const fusing = forced.Add({ 20.f, 0.f }, false, 5000);
        forced.Kill(fusing, 5000);
        std::vector<FuseStart> now = forced.RipenNow(6000);
        CHECK(now.size() == 1 && now[0].kind == BurstKind::Ripe && now[0].warnMs == kRipeWarnMs);

        // The lesson's specimens never ripen.
        SpecimenChain lesson(LessonChain());
        std::uint32_t const l = lesson.Add({ 0.f, 0.f }, false, 0);
        CHECK(lesson.TakeRipening(600000).empty());
        CHECK(lesson.MsToRipe(l, 600000) == UINT64_MAX);

        // The swell: 1 at the raise, 1.5 when it ripens.
        CHECK(Near(SwellScale(0), 1.f) && Near(SwellScale(15000), 1.25f) && Near(SwellScale(30000), 1.5f));
        CHECK(Near(SwellScale(90000), 1.5f));
    }

    void TestRemove()
    {
        SpecimenChain chain;
        std::uint32_t const a = chain.Add({ 0.f, 0.f }, false, 0);
        std::uint32_t const b = chain.Add({ 1.f, 0.f }, false, 0);
        chain.Remove(b);                            // despawned: never lit, never bursts
        chain.Kill(a, 0);
        std::vector<Burst> bursts = chain.TakeBursts(2000);
        CHECK(bursts.size() == 1 && bursts[0].lit.empty());
        CHECK(chain.Live() == 0);
        // A walker moves; a fusing one keeps its ring's spot.
        std::uint32_t const c = chain.Add({ 0.f, 0.f }, false, 0);
        chain.SetPos(c, { 3.f, 4.f });
        CHECK(Near(chain.Find(c)->pos.x, 3.f) && Near(chain.Find(c)->pos.y, 4.f));
        chain.Kill(c, 0);
        chain.SetPos(c, { 9.f, 9.f });
        CHECK(Near(chain.Find(c)->pos.x, 3.f));
    }

    void TestPools()
    {
        PoolQueue pools;
        for (std::uint32_t i = 1; i <= 6; ++i)
            CHECK(pools.Push(i, { float(i), 0.f }, i * 1000, kPoolCap(false)).empty());
        CHECK(pools.Size() == 6);
        // The seventh dries up the oldest.
        std::vector<PoolQueue::Pool> dried = pools.Push(7, { 7.f, 0.f }, 7000, kPoolCap(false));
        CHECK(dried.size() == 1 && dried[0].handle == 1);
        CHECK(pools.Size() == 6 && pools.All().front().handle == 2);
        // 60 s life: by 62 s the second has dried by itself.
        CHECK(pools.Expire(62000) == 1);
        CHECK(pools.Size() == 5 && pools.All().front().handle == 3);
        // Heroic cap 8.
        PoolQueue heroic;
        for (std::uint32_t i = 1; i <= 8; ++i)
            CHECK(heroic.Push(i, { 0.f, 0.f }, 0, kPoolCap(true)).empty());
        CHECK(heroic.Push(9, { 0.f, 0.f }, 0, kPoolCap(true)).size() == 1);
        CHECK(heroic.Size() == 8);
    }

    void TestSpots()
    {
        // The measured rooted spots: on the hall floor, in the arena, every pair at least 13 yd apart.
        std::vector<Vec2> const fixed = RootedFallbackSpots();
        CHECK(fixed.size() == 3);
        SpotRules const rooted = RaiseRules(true);
        CHECK(Near(rooted.minApart, 13.f) && Near(rooted.minFromPlayers, 8.f));
        for (std::size_t i = 0; i < fixed.size(); ++i)
        {
            CHECK(OnHallFloor(rooted, fixed[i]));
            CHECK(PolkeltArena().Contains(fixed[i], kRootedSpecimenSpots[i].z));
            for (std::size_t j = i + 1; j < fixed.size(); ++j)
                CHECK(DungeonKit::Distance(fixed[i], fixed[j]) >= kRootedMinApart);
        }

        // A heroic batch: 3 rooted 13 yd apart, 3 walkers, none within 8 yd of a player, none in a pool.
        std::vector<Vec2> const players{ { 268.f, 1.f }, { 264.f, 4.f }, { 265.f, -3.f }, { 270.f, -1.f } };
        std::vector<Vec2> const poolsAt{ { 240.f, 0.f } };
        for (std::uint32_t seed = 1; seed <= 40; ++seed)
        {
            Lcg rng;
            rng.state = seed * 7919u;
            std::vector<Vec2> const r = PickSpots(rooted, 3, players, {}, poolsAt, rng, AnyFloor, fixed);
            CHECK(r.size() == 3);
            for (std::size_t i = 0; i < r.size(); ++i)
            {
                CHECK(OnHallFloor(rooted, r[i]));
                SpotScore const s = ScoreSpot(rooted, r[i], players, {}, poolsAt, {});
                CHECK(s.players && s.avoid);
                for (std::size_t j = i + 1; j < r.size(); ++j)
                    CHECK(DungeonKit::Distance(r[i], r[j]) >= kRootedMinApart);
            }
            std::vector<Vec2> const w = PickSpots(RaiseRules(false), 3, players, {}, poolsAt, rng, AnyFloor);
            CHECK(w.size() == 3);
            for (Vec2 const& p : w)
                CHECK(ScoreSpot(RaiseRules(false), p, players, {}, poolsAt, {}).players);
        }

        // Random points that all fail (the generator always returns the same corner, a player stands on it): the
        // measured spots are the fallback.
        std::vector<Vec2> const crowd{ { 224.5f, -8.5f } };
        auto corner = []() { return 0.f; };
        std::vector<Vec2> const fb = PickSpots(rooted, 3, crowd, {}, {}, corner, AnyFloor, fixed);
        CHECK(fb.size() == 3);
        CHECK(fb.size() == 3 && Near(fb[0].x, 236.f) && Near(fb[1].x, 249.f) && Near(fb[2].x, 262.f));
        // Nothing fits at all (no fallback): the best scored point still rises.
        std::vector<Vec2> const best = PickSpots(rooted, 1, crowd, {}, {}, corner, AnyFloor);
        CHECK(best.size() == 1);
        // No floor at all: nothing.
        CHECK(PickSpots(rooted, 2, crowd, {}, {}, corner, [](Vec2) { return false; }).empty());
    }

    void TestBots()
    {
        CHECK(IsKillTarget(6.f, 20000));
        CHECK(IsKillTarget(30.f, 3000));
        CHECK(!IsKillTarget(6.5f, 3001));
        CHECK(!IsKillTarget(20.f, UINT64_MAX));
    }

    void TestNoxious()
    {
        CHECK(NoxiousStacksAt(9999) == 0 && NoxiousStacksAt(10000) == 1);
        // SC: 9 stacks at the 95 s target (2.7% per second), 13 at 130 s (3.9%).
        CHECK(NoxiousStacksAt(95000) == 9 && Near(NoxiousStacksAt(95000) * kNoxiousPctPerStack, 2.7f));
        CHECK(NoxiousStacksAt(130000) == 13 && Near(NoxiousStacksAt(130000) * kNoxiousPctPerStack, 3.9f));
        CHECK(InRange(7000, 15000, 0.f) == 7000 && InRange(7000, 15000, 1.f) == 15000);
    }

    void TestProfiles()
    {
        FightProfile const n = ProfileFor(false, false);
        CHECK(!n.heroic && !n.hardened && !n.noxious && n.talks && n.grades && n.bossState);
        CHECK(n.walkers == 2 && n.rooted == 1 && n.poolCap == 6 && n.maxHealth == 0);
        FightProfile const h = ProfileFor(true, false);
        CHECK(h.heroic && h.hardened && h.noxious && h.grades && h.bossState);
        CHECK(h.walkers == 3 && h.rooted == 3 && h.poolCap == 8);
        // The Graduate Examiner: heroic values for both mechanics, 80k, no enrage, no texts, no grades, no boss state.
        FightProfile const e = ProfileFor(false, true);
        CHECK(e.heroic && e.hardened && !e.noxious && !e.talks && !e.grades && !e.bossState);
        CHECK(e.walkers == 3 && e.rooted == 3 && e.poolCap == 8 && e.maxHealth == 80000);
        CHECK(ProfileFor(true, true).maxHealth == kExaminerHealth);
    }

    void TestLesson()
    {
        CHECK(kLessonSpecimens(false) == 3 && kLessonSpecimens(true) == 4);
        CHECK(LessonSpawnAtMs(0) == 0 && LessonSpawnAtMs(3) == 6000);
        CHECK(LessonSpawnAtMs(kLessonSpecimens(true) - 1) < kLessonMs);
        CHECK(Near(kLessonReachYd, 2.5f));
        CHECK(kLessonFailurePctNormal == 15 && kLessonFailurePctHeroic == 25);   // + Weakened (SoloLesson.h)

        // The student lands on Polkelt's spot (17863): every specimen rises 10-14 yd from them, on the hall floor.
        Vec2 const student = kClassroomLandings[std::size_t(Classroom::HallOfSecrets)].XY();
        SpotRules const rules = LessonRules(student);
        for (std::uint32_t seed = 1; seed <= 40; ++seed)
        {
            Lcg rng;
            rng.state = seed * 104729u;
            std::vector<Vec2> const spots = PickSpots(rules, 1, { student }, {}, {}, rng, AnyFloor);
            CHECK(spots.size() == 1);
            float const d = DungeonKit::Distance(spots[0], student);
            CHECK(d >= kLessonMinFromStudent && d <= kLessonMaxFromStudent);
            CHECK(OnHallFloor(rules, spots[0]));
        }
        CHECK(!LessonCleared(2, 3, 0));
        CHECK(!LessonCleared(3, 3, 1));
        CHECK(LessonCleared(3, 3, 0));
    }
}

int main()
{
    TestIds();
    TestNumbers();
    TestKillChain();
    TestOverlap();
    TestCatalyst();
    TestRipe();
    TestRemove();
    TestPools();
    TestSpots();
    TestBots();
    TestNoxious();
    TestProfiles();
    TestLesson();

    return Report("scholo_polkelt_test");
}
