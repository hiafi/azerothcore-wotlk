// Host tests for BaronessLogic.h (S10: Baroness Anastari (10436)): the ids, the build spec numbers (ST 2630-2677), the
// isolation pick, the Death Knell split and Death's Echo, the cast plan (cadences, no overlap, the stock filler yields)
// and the arena.
#include "BaronessLogic.h"
#include "check.h"
#include <cmath>

using namespace StratholmeRework;
using namespace StratBaroness;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    Candidate At(std::uint64_t id, float x, float y, float distToBoss, float z = 140.f)
    {
        Candidate c;
        c.id = id;
        c.pos = { x, y };
        c.z = z;
        c.distToBoss = distToBoss;
        return c;
    }

    struct Start
    {
        CastPlan::Cast cast;
        std::uint64_t at;
    };

    // Plays the plan for `endMs`: one decision every `stepMs`, a cast holds her for its cast time (the caster is busy).
    std::vector<Start> Simulate(bool heroic, std::uint64_t endMs, std::uint64_t stepMs = 100)
    {
        CastPlan plan;
        plan.Reset(heroic);
        std::vector<Start> out;
        std::uint64_t busyUntil = 0;
        for (std::uint64_t now = 0; now <= endMs; now += stepMs)
        {
            if (now < busyUntil)
                continue;
            std::optional<CastPlan::Cast> const next = plan.Next(now);
            if (!next)
                continue;
            plan.Started(*next, now);
            out.push_back({ *next, now });
            busyUntil = now + CastPlan::CastMs(*next, heroic);
        }
        return out;
    }

    std::vector<std::uint64_t> StartsOf(std::vector<Start> const& all, CastPlan::Cast cast)
    {
        std::vector<std::uint64_t> out;
        for (Start const& s : all)
            if (s.cast == cast)
                out.push_back(s.at);
        return out;
    }

    // No two casts overlap, and the stock filler never made a mechanic late (every mechanic start is on its nominal
    // time or behind another mechanic cast).
    bool NeverOverlap(std::vector<Start> const& all, bool heroic)
    {
        for (std::size_t i = 1; i < all.size(); ++i)
            if (all[i].at < all[i - 1].at + CastPlan::CastMs(all[i - 1].cast, heroic))
                return false;
        return true;
    }
}

int main()
{
    // ---- ids and slice --------------------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 206625 && kSpellSlice.last == 206644);
    CHECK(SPELL_BA_KEENED == 206625 && SPELL_BA_LAMENT == 206635);
    for (std::uint32_t id : { std::uint32_t(SPELL_BA_KEENED), std::uint32_t(SPELL_BA_DEATH_KNELL),
        std::uint32_t(SPELL_BA_DEATHS_ECHO), std::uint32_t(SPELL_BA_WAIL_BAR), std::uint32_t(SPELL_BA_WAIL_HIT),
        std::uint32_t(SPELL_BA_TERRIFIED), std::uint32_t(SPELL_BA_WAIL_ECHO_HIT), std::uint32_t(SPELL_BA_VISAGE_BAR),
        std::uint32_t(SPELL_BA_VISAGE_BAR_HEROIC), std::uint32_t(SPELL_BA_VISAGE_HIT), std::uint32_t(SPELL_BA_LAMENT) })
    {
        CHECK(kSpellSlice.Contains(id));
        CHECK(!kSpellsBarthilas.Contains(id));
        CHECK(!kSpellsNerubenkan.Contains(id));
    }
    // The stock kit she keeps: Banshee Wail 16565.
    CHECK(SPELL_BANSHEE_WAIL == 16565);

    // ---- the boss's place -----------------------------------------------------------------------------------------
    CHECK(BOSS_BARONESS == 9);
    CHECK(BaronessArena().Contains(kBaronessSpawn.XY(), kBaronessSpawn.z));
    CHECK(ArenaFor(BOSS_BARONESS).Contains(kBaronessSpawn.XY(), kBaronessSpawn.z));

    // ---- build spec numbers (ST 2630-2677) -------------------------------------------------------------------------
    CHECK(kKeen.first == 6000 && kKeen.every == 30000);
    CHECK(kKeenMs(false) == 6000 && kKeenMs(true) == 5000);
    CHECK(kKnellPct(false) == 90.f && kKnellPct(true) == 100.f);
    CHECK(kKnellRadius == 6.f && kIsolationRadius == 10.f);
    CHECK(kEchoPerStack == 1.f && kEchoDurationMs == 45000);
    CHECK(kWail.first == 16000 && kWail.every == 20000 && kWailCastMs == 3000 && kWailRadius == 12.f);
    CHECK(kWailPct(false) == 45.f && kWailPct(true) == 50.f);
    CHECK(kWailEchoInner == 8.f && kWailEchoWarnMs == 2000 && kWailEchoPct == 40.f);
    // The donut keeps the marker's hole: an inner / outer ratio of 0.25 or more (orchestrator ruling).
    CHECK(kWailEchoInner / kWailEchoOuter >= 0.25f);
    CHECK(kVisage.first == 12000 && kVisage.every == 20000);
    CHECK(kVisageCastMs(false) == 2000 && kVisageCastMs(true) == 1500);
    CHECK(kVisageAngleDeg == 60.f && kVisageLengthYd == 30.f);
    CHECK(kVisagePct(false) == 30.f && kVisagePct(true) == 35.f);
    CHECK(kVisageCones(false) == 1 && kVisageCones(true) == 2);
    CHECK(kLament.first == 21000 && kLament.every == 30000 && kLamentCastMs == 2500);
    CHECK(kTerrifiedMs == 2000);
    CHECK(kBansheeWail.every == 4000 && kStockBansheeWailCastMs == 1500);

    // ---- reference numbers: damage = percent x reference health (normal 3,670 / 3,710; heroic 4,120 / 4,110) --------
    CHECK(DungeonKit::RefFlatValue(3670, 3710, kKnellPct(false), false) == 3303u);
    CHECK(DungeonKit::RefFlatValue(4120, 4110, kKnellPct(true), false) == 4120u);
    CHECK(DungeonKit::RefFlatValue(3670, 3710, kWailPct(false), false) == 1652u);     // 1,651.5 rounds up
    CHECK(DungeonKit::RefFlatValue(3670, 3710, kWailPct(false), true) == 1670u);
    CHECK(DungeonKit::RefFlatValue(4120, 4110, kWailPct(true), false) == 2060u);
    CHECK(DungeonKit::RefFlatValue(3670, 3710, kVisagePct(false), false) == 1101u);
    CHECK(DungeonKit::RefFlatValue(4120, 4110, kVisagePct(true), false) == 1442u);
    CHECK(DungeonKit::RefFlatValue(4120, 4110, kWailEchoPct, false) == 1648u);

    // ---- BA1: the most isolated player -----------------------------------------------------------------------------
    {
        // A group of four at (0, 0) and one at 30 yd: the loner is doomed.
        std::vector<Candidate> group = { At(1, 0, 0, 20), At(2, 2, 0, 20), At(3, 0, 3, 22), At(4, 4, 4, 22),
            At(5, 30, 0, 25) };
        CHECK(PickIsolated(group, kIsolationRadius, kIsolationZBand, 0.f) == 4u);
        CHECK(PickIsolated(group, kIsolationRadius, kIsolationZBand, 0.99f) == 4u);
        // The tank is a candidate: a lone tank 5 yd off the group still has the group within 10 yd and is not it.
        std::vector<Candidate> tankNear = { At(1, 0, 0, 12), At(2, 3, 0, 14), At(3, 6, 0, 16), At(4, 22, 0, 20) };
        CHECK(PickIsolated(tankNear, kIsolationRadius, kIsolationZBand, 0.5f) == 3u);
        // Ties: everyone has the same allies (one pair each): the one farthest from her.
        std::vector<Candidate> pairs = { At(1, 0, 0, 10), At(2, 2, 0, 10), At(3, 40, 0, 31), At(4, 42, 0, 33) };
        CHECK(PickIsolated(pairs, kIsolationRadius, kIsolationZBand, 0.f) == 3u);
        // The farthest wins by more than half a yard; within half a yard counts as a tie and the roll picks.
        std::vector<Candidate> close = { At(1, 0, 0, 10), At(2, 2, 0, 10), At(3, 40, 0, 31), At(4, 42, 0, 31.3f) };
        CHECK(PickIsolated(close, kIsolationRadius, kIsolationZBand, 0.f) == 2u);
        CHECK(PickIsolated(close, kIsolationRadius, kIsolationZBand, 0.9f) == 3u);
        // Height counts: two players on top of each other on different floors are not allies.
        std::vector<Candidate> floors = { At(1, 0, 0, 10, 140.f), At(2, 1, 0, 11, 150.f), At(3, 2, 0, 12, 140.f) };
        CHECK(AlliesNear(floors, 0, kIsolationRadius, kIsolationZBand) == 1u);
        CHECK(AlliesNear(floors, 1, kIsolationRadius, kIsolationZBand) == 0u);
        CHECK(PickIsolated(floors, kIsolationRadius, kIsolationZBand, 0.f) == 1u);
        // Alone: the only candidate. Nobody: nothing.
        CHECK(PickIsolated({ At(9, 5, 5, 12) }, kIsolationRadius, kIsolationZBand, 0.5f) == 0u);
        CHECK(!PickIsolated({}, kIsolationRadius, kIsolationZBand, 0.5f).has_value());
    }

    // ---- BA2 / BA3: who shares the Knell, and the shares -----------------------------------------------------------
    {
        std::vector<Candidate> g = { At(1, 0, 0, 12), At(2, 5.9f, 0, 14), At(3, 6.1f, 0, 14), At(4, 0, -5, 16),
            At(5, 20, 0, 20), At(6, 3, 3, 14, 151.f) };
        std::vector<std::size_t> const inside = KnellInside(g, { 0.f, 0.f }, 140.f, kKnellRadius, kKnellZBand);
        // 1 (the doomed), 2 (5.9 yd), 4 (5 yd); 3 is 6.1 yd out, 5 far, 6 on another floor.
        CHECK(inside.size() == 3 && inside[0] == 0 && inside[1] == 1 && inside[2] == 3);
        CHECK(KnellInside(g, { 20.f, 0.f }, 140.f, kKnellRadius, kKnellZBand) == std::vector<std::size_t>{ 4 });

        // 90% of the normal row: 3,303 alone, split evenly among the takers.
        std::uint32_t const total = DungeonKit::RefFlatValue(3670, 3710, kKnellPct(false), false);
        CHECK((KnellShares(total, { 0 }) == std::vector<std::uint32_t>{ 3303 }));
        CHECK((KnellShares(total, { 0, 0 }) == std::vector<std::uint32_t>{ 1652, 1651 }));
        CHECK((KnellShares(total, { 0, 0, 0 }) == std::vector<std::uint32_t>{ 1101, 1101, 1101 }));
        // Death's Echo: +100% per stack on the taker's own share.
        CHECK((KnellShares(total, { 1, 0, 0 }) == std::vector<std::uint32_t>{ 2202, 1101, 1101 }));
        CHECK((KnellShares(total, { 2, 0, 0 }) == std::vector<std::uint32_t>{ 3303, 1101, 1101 }));
        // The doomed alone with a stack: 6,606 on a 3,670-health reference: dead (alone, 90%, then twice).
        CHECK(KnellShares(total, { 1 })[0] == 6606u);
        // The whole group of five with no stacks: 661 each, 18% of the row (ST "Failing path check").
        CHECK(KnellShares(total, { 0, 0, 0, 0, 0 })[0] == 661u);
        CHECK(Near(float(KnellShares(total, { 0, 0, 0, 0, 0 })[0]) / 3670.f * 100.f, 18.f, 0.1f));
        // Two teams of three and two take turns: 30% and 45% per player (ST).
        CHECK(Near(float(KnellShares(total, { 0, 0, 0 })[0]) / 3670.f * 100.f, 30.f, 0.1f));
        CHECK(Near(float(KnellShares(total, { 0, 0 })[0]) / 3670.f * 100.f, 45.f, 0.1f));
        // Heroic 100%: a lone doomed player dies at full health (4,120 on a 4,120 row).
        CHECK(KnellShares(DungeonKit::RefFlatValue(4120, 4110, kKnellPct(true), false), { 0 })[0] == 4120u);
    }

    // ---- BA6: the cone is fixed at the cast start and holds the target's spot --------------------------------------
    {
        Vec2 const boss{ 3855.f, -3716.f };
        Vec2 const target{ 3840.f, -3700.f };
        float const facing = DungeonKit::BearingTo(boss, target);
        CHECK(DungeonKit::InFrontalCone(boss, facing, target, kVisageAngleDeg, kVisageLengthYd));
        // The player 40 yd away on the line is past the 30 yd; one 40 degrees off the line is out of the 60 degree
        // cone.
        CHECK(!DungeonKit::InFrontalCone(boss, facing, DungeonKit::Advance(boss, facing, 40.f), kVisageAngleDeg,
            kVisageLengthYd));
        CHECK(!DungeonKit::InFrontalCone(boss, facing, DungeonKit::Advance(boss, facing + 0.7f, 15.f),
            kVisageAngleDeg, kVisageLengthYd));
        CHECK(DungeonKit::InFrontalCone(boss, facing, DungeonKit::Advance(boss, facing + 0.4f, 15.f),
            kVisageAngleDeg, kVisageLengthYd));
    }

    // ---- the cast plan: normal -------------------------------------------------------------------------------------
    {
        std::vector<Start> const all = Simulate(false, 140000);
        CHECK(NeverOverlap(all, false));
        // Every mechanic start is on its planned second: Visage 12 / 32 / 52 ..., Wail 16 / 36 / 56 ... (ST).
        CHECK(StartsOf(all, CastPlan::Wail) == (std::vector<std::uint64_t>{ 16000, 36000, 56000, 76000, 96000, 116000,
            136000 }));
        CHECK(StartsOf(all, CastPlan::Visage) == (std::vector<std::uint64_t>{ 12000, 32000, 52000, 72000, 92000,
            112000, 132000 }));
        CHECK(StartsOf(all, CastPlan::Lament).empty());
        // The stock Banshee Wail runs between them, every 4 s from its start (never two in a row inside a cast).
        std::vector<std::uint64_t> const filler = StartsOf(all, CastPlan::BansheeWail);
        CHECK(filler.size() > 20 && filler.front() == 2000);
        for (std::size_t i = 1; i < filler.size(); ++i)
            CHECK(filler[i] >= filler[i - 1] + 4000);
        // A Wail inside a keen: keens at 6, 36 and 66 s last 6 s; the Wail at 36 s starts with the second keen (ST:
        // every third Wail lands inside one).
        CHECK(kWail.first + 1 * kWail.every == kKeen.first + 1 * kKeen.every);
        int insideKeen = 0;
        for (std::uint64_t at : StartsOf(all, CastPlan::Wail))
            for (std::uint64_t keen = kKeen.first; keen < 140000; keen += kKeen.every)
                if (at >= keen && at < keen + kKeenMs(false))
                    ++insideKeen;
        CHECK(insideKeen == 2);     // the 2nd and the 5th of seven: 36 s and 96 s
        // Her mechanic casts do not overlap each other on the nominal times either: Wail 16-19 s, Visage 12-14 s.
        CHECK(kVisage.first + kVisageCastMs(false) < kWail.first);
    }

    // ---- the cast plan: heroic -------------------------------------------------------------------------------------
    {
        std::vector<Start> const all = Simulate(true, 140000);
        CHECK(NeverOverlap(all, true));
        CHECK(StartsOf(all, CastPlan::Lament) == (std::vector<std::uint64_t>{ 21000, 51000, 81000, 111000 }));
        std::vector<std::uint64_t> const visage = StartsOf(all, CastPlan::Visage);
        // The Visage at 52 s waits for the Lament (51 to 53.5 s, then the 0.3 s gap); the next ones are on time.
        CHECK(visage.size() >= 6);
        CHECK(visage[0] == 12000 && visage[1] == 32000);
        CHECK(visage[2] >= 53500 && visage[2] <= 54500);
        CHECK(visage[3] == 72000 && visage[4] == 92000);
        std::vector<std::uint64_t> const wail = StartsOf(all, CastPlan::Wail);
        CHECK(wail[0] == 16000 && wail[1] == 36000 && wail[2] == 56000 && wail[3] == 76000);
        // The Lament goes before a Visage or a Wail that are due at the same time (priority 3).
        CastPlan plan;
        plan.Reset(true);
        CHECK(plan.Heroic());
        CHECK(plan.DueAt(CastPlan::Lament) == 21000u);
        CHECK(!CastPlan().DueAt(CastPlan::Lament).has_value());
    }

    // ---- the stock filler yields to the mechanics ------------------------------------------------------------------
    {
        CastPlan plan;
        plan.Reset(false);
        // A filler due at 2 s starts at 2 s.
        CHECK(plan.Next(2000) == CastPlan::BansheeWail);
        plan.Started(CastPlan::BansheeWail, 2000);
        CHECK(plan.DueAt(CastPlan::BansheeWail) == 6000u);
        // The Visage is due at 12 s: a filler at 10.6 s would end at 12.1 s, so it waits (pretend it came late).
        plan.Started(CastPlan::BansheeWail, 6000);          // next 10 s
        CHECK(plan.DueAt(CastPlan::BansheeWail) == 10000u);
        CHECK(plan.Next(10000) == CastPlan::BansheeWail);   // 12 s is 2 s away: 1.65 s window, it may start
        CastPlan late;
        late.Reset(false);
        late.Started(CastPlan::BansheeWail, 6000);          // booked for 10 s
        late.Started(CastPlan::BansheeWail, 10600);         // booked for 14.6 s
        late.Started(CastPlan::Visage, 12100);              // behind the filler; her cast ends at 14.1 s
        CHECK(late.DueAt(CastPlan::BansheeWail) == 14600u);
        // At 14.6 s the Wail (16 s) is 1.4 s away: inside the 1.65 s window, so the filler does not start.
        CHECK(!late.Next(14600).has_value());
        // It keeps waiting while the Wail is that close, and the Wail goes first when its turn comes.
        CHECK(!late.Next(14900).has_value());
        CHECK(late.Next(16000) == CastPlan::Wail);
        // A refused cast is retried a second later with the cadence unchanged.
        CastPlan refused;
        refused.Reset(false);
        CHECK(refused.Next(12000) == CastPlan::Visage);
        refused.Refused(CastPlan::Visage, 12000);
        CHECK(!refused.Next(12500).has_value() || refused.Next(12500) != CastPlan::Visage);
        CHECK(refused.Next(13000) == CastPlan::Visage);
        refused.Started(CastPlan::Visage, 13000);
        CHECK(refused.DueAt(CastPlan::Visage) == 32000u);   // the planned 12 s + 20 s, not the late start + 20 s
    }

    return Report("strat_baroness_test");
}
