// Host tests for VanCleefLogic.h (WP-B8): slice, stages, Ambush cadence and picks, the guns volley, the plan, the
// Blackguards' spots.
#include "VanCleefLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace VanCleef;

namespace
{
    void TestSlice()
    {
        CHECK(kSlice.first == 205360u);
        CHECK(kSlice.last == 205379u);
        for (std::uint32_t id : { SPELL_AMBUSH_VANISH, SPELL_AMBUSH_HIT, SPELL_SHADOW_IMAGE_VISUAL,
                 SPELL_FIRE_BOMB_TICK, SPELL_FIRE_BOMB_GROUND, SPELL_EXPOSE_ARMOR, SPELL_AMBUSH_STRIKE })
            CHECK(kSlice.Contains(id));
        // never B9's slice
        CHECK(!DeadminesRework::kSpellsHardMode.Contains(SPELL_AMBUSH_STRIKE));
    }

    void TestStages()
    {
        // normal
        CHECK(StagesReached(100.f, false) == 0u);
        CHECK(StagesReached(66.5f, false) == 0u);
        CHECK(StagesReached(66.f, false) == STAGE_GUNS);
        CHECK(StagesReached(50.f, false) == (STAGE_GUNS | STAGE_BROTHERHOOD));
        CHECK(StagesReached(40.f, false) == (STAGE_GUNS | STAGE_BROTHERHOOD));
        CHECK(StagesReached(33.f, false) == (STAGE_GUNS | STAGE_BROTHERHOOD | STAGE_RIGHTEOUS | STAGE_IMAGE));
        // heroic: the image from 50%
        CHECK(StagesReached(50.f, true) == (STAGE_GUNS | STAGE_BROTHERHOOD | STAGE_IMAGE));
        CHECK(StagesReached(51.f, true) == STAGE_GUNS);
        CHECK(StagesReached(10.f, true) == (STAGE_GUNS | STAGE_BROTHERHOOD | STAGE_RIGHTEOUS | STAGE_IMAGE));

        // one big hit from 70% to 30% runs every stage once, in order
        std::vector<Stage> all = NewStages(0, 30.f, false);
        CHECK(all.size() == 4u);
        CHECK(all.size() == 4u && all[0] == STAGE_GUNS && all[1] == STAGE_BROTHERHOOD && all[2] == STAGE_IMAGE
            && all[3] == STAGE_RIGHTEOUS);
        // done stages never repeat
        CHECK(NewStages(STAGE_GUNS | STAGE_BROTHERHOOD, 45.f, false).empty());
        std::vector<Stage> heroic = NewStages(STAGE_GUNS, 49.f, true);
        CHECK(heroic.size() == 2u && heroic[0] == STAGE_BROTHERHOOD && heroic[1] == STAGE_IMAGE);
        // a heal back above a threshold does not undo it (the caller keeps `done`)
        CHECK(NewStages(STAGE_GUNS, 80.f, false).empty());
    }

    void TestAmbushCadence()
    {
        CHECK(kAmbushFirstMs == 12000u);
        CHECK(AmbushCooldownMs(0) == 20000u);
        CHECK(AmbushCooldownMs(STAGE_GUNS | STAGE_BROTHERHOOD) == 20000u);
        CHECK(AmbushCooldownMs(STAGE_GUNS | STAGE_BROTHERHOOD | STAGE_RIGHTEOUS) == 15000u);
        // heroic at 45%: image in, still 20 s until 33%
        CHECK(AmbushCooldownMs(StagesReached(45.f, true)) == 20000u);
        CHECK(AmbushCircles(StagesReached(45.f, true)) == 2u);
        CHECK(AmbushCircles(StagesReached(45.f, false)) == 1u);
        CHECK(AmbushCircles(StagesReached(33.f, false)) == 2u);
        CHECK(kAmbushWarnMs(false) == 2000u && kAmbushWarnMs(true) == 2000u);
        CHECK(kAmbushPct(false) == 40.f && kAmbushPct(true) == 40.f);
        CHECK(kAmbushRadius == 5.f);
        // the guns never run faster than an Ambush plus its vanish
        CHECK(kGunsEveryMs > kAmbushEveryMs);
    }

    void TestPicks()
    {
        std::vector<AmbushCandidate> party;
        for (std::size_t i = 0; i < 5; ++i)
            party.push_back({ i, i == 2 });     // index 2 tanks

        // every rng draw: two distinct non-tanks, never the tank
        for (std::uint32_t a = 0; a < 4; ++a)
        {
            for (std::uint32_t b = 0; b < 3; ++b)
            {
                std::uint32_t call = 0;
                std::vector<std::size_t> picks = PickAmbushTargets(party, 2,
                    [&](std::uint32_t n) { std::uint32_t const v = call++ == 0 ? a : b; return v % n; });
                CHECK(picks.size() == 2u);
                CHECK(picks.size() == 2u && picks[0] != picks[1]);
                CHECK(std::find(picks.begin(), picks.end(), std::size_t(2)) == picks.end());
            }
        }

        // one circle: one non-tank
        std::vector<std::size_t> one = PickAmbushTargets(party, 1, [](std::uint32_t) { return 0u; });
        CHECK(one.size() == 1u && one[0] == 0u);

        // only one non-tank and the image is in: one circle (no second player to strike)
        std::vector<AmbushCandidate> duo{ { 0, true }, { 1, false } };
        std::vector<std::size_t> duoPicks = PickAmbushTargets(duo, 2, [](std::uint32_t n) { return n - 1; });
        CHECK(duoPicks.size() == 1u && duoPicks[0] == 1u);

        // solo (the tank alone): the tank, once
        std::vector<AmbushCandidate> solo{ { 7, true } };
        std::vector<std::size_t> soloPicks = PickAmbushTargets(solo, 2, [](std::uint32_t) { return 0u; });
        CHECK(soloPicks.size() == 1u && soloPicks[0] == 7u);

        // nobody
        CHECK(PickAmbushTargets({}, 2, [](std::uint32_t) { return 0u; }).empty());

        // an rng out of range is clamped
        std::vector<std::size_t> clamped = PickAmbushTargets(party, 2, [](std::uint32_t) { return 99u; });
        CHECK(clamped.size() == 2u && clamped[0] != clamped[1]);

        // uniform enough: every non-tank gets picked over a deterministic sweep
        std::set<std::size_t> seen;
        for (std::uint32_t r = 0; r < 8; ++r)
            for (std::size_t p : PickAmbushTargets(party, 2, [r](std::uint32_t n) { return r % n; }))
                seen.insert(p);
        CHECK(seen.size() == 4u && !seen.count(2));
    }

    void TestGuns()
    {
        Greenskin::LaneVolley const normal = GunsVolley(false);
        CHECK(normal.across == 3u && normal.along == 0u);
        CHECK(normal.warnMs == 2000u);
        CHECK(normal.lanePct == 40.f);
        CHECK(!normal.burnCrossings && normal.Crossings() == 0u);
        CHECK(normal.acrossTag == TAG_GUNS && normal.alongTag == TAG_GUNS && normal.cellTag == TAG_GUNS);

        Greenskin::LaneVolley const heroic = GunsVolley(true);
        CHECK(heroic.across == 4u && heroic.along == 2u);
        CHECK(heroic.Lanes() == 6u);                // DM VC3 count H: 6
        CHECK(heroic.warnMs == 2500u);
        CHECK(heroic.burnCrossings && heroic.Crossings() == 8u);
        CHECK(heroic.burnMs == 20000u && heroic.burnTickMs == 1000u && heroic.burnPct == 10.f);
        CHECK(heroic.acrossTag == TAG_GUNS && heroic.cellTag == TAG_GUNS);
        CHECK(kGunsEveryMs == 25000u);
    }

    void TestPlan()
    {
        Plan const n = PlanFor(false, false);
        CHECK(n.ambush && n.guns && n.brotherhood && !n.exposeArmor && !n.fireBomb);
        Plan const h = PlanFor(true, false);
        CHECK(h.ambush && h.guns && h.brotherhood && h.exposeArmor && h.fireBomb);
        // hard mode: no gun lanes, everything else heroic
        Plan const hm = PlanFor(true, true);
        CHECK(hm.ambush && !hm.guns && hm.brotherhood && hm.exposeArmor && hm.fireBomb);
    }

    void TestBlackguards()
    {
        Vec2 const c{ -87.4f, -819.9f };
        std::vector<Vec2> spots = BlackguardSpots(c, 0.f);
        CHECK(spots.size() == kBlackguardCount);
        for (Vec2 const& s : spots)
            CHECK(std::fabs(DeadminesKit::Distance(c, s) - kBlackguardSideYd) < 0.01f);
        CHECK(DeadminesKit::Distance(spots[0], spots[1]) > 11.9f);
        // facing +x: they stand on the y axis beside him
        CHECK(std::fabs(spots[0].x - c.x) < 0.01f && std::fabs(spots[1].x - c.x) < 0.01f);
        CHECK(kBlackguardLifeMs == 300000u);
        CHECK(kCheapShotMs == 2000u);
        CHECK(kFireBomb(true) && !kFireBomb(false));
        CHECK(kFireBombRadius == 6.f && kFireBombMs == 15000u && kFireBombTickMs == 1000u && kFireBombPct == 5.f);
        CHECK(kExposeArmor(true) && !kExposeArmor(false) && kExposeArmorMaxStacks == 5u);
    }
}

int main()
{
    TestSlice();
    TestStages();
    TestAmbushCadence();
    TestPicks();
    TestGuns();
    TestPlan();
    TestBlackguards();
    return Report("vancleef_test");
}
