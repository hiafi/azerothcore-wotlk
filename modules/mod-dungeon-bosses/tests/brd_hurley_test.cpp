// Host tests for HurleyLogic.h (D18: Hurley Blackbreath, the Cronies, the kegs and the puddles).
// The slice and the arena (WP-S0's), the Keg Run's state machine, the keg pick, the walk and its deadline, the breath
// cone (the tank, the puddles, the heroic double width), the wake-up (the escort path, the Cronies' copy, the reload
// check) against D17's BarModel, the tuning table and the room's points.
#include "GuzzlerLogic.h"
#include "HurleyLogic.h"
#include "check.h"
#include <cmath>
#include <set>

using namespace BlackrockDepthsRework;
using namespace BrdHurley;

namespace
{
    bool InArena(Point3 const& p)
    {
        return GuzzlerLowerArena().Contains(p.XY(), p.z);
    }

    float Dist(Point3 const& a, Point3 const& b)
    {
        return DungeonKit::Distance(a.XY(), b.XY());
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation, contiguous from its first id.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211430 && kSpellSlice.last == 211459);
        CHECK(SPELL_HU_MORTAL_STRIKE == 211430);
        CHECK(kLastSpell == 211445);
        CHECK(kLastSpell - SPELL_HU_MORTAL_STRIKE + 1 == 16);
        // The Cronies' kept stock spells are not in the slice (no copy: not rescaled).
        CHECK(!kSpellSlice.Contains(SPELL_STOCK_SINISTER_STRIKE));
        CHECK(!kSpellSlice.Contains(SPELL_STOCK_RUPTURE));
        // Tags are distinct.
        std::set<std::uint32_t> const tags{ TAG_HU_FLAME_BREATH, TAG_HU_BURNING_LAGER, TAG_HU_BOTTLE_TOSS };
        CHECK(tags.size() == 3);
        // Texts: S0's range for 9537 is 0-5 (0-1 stock).
        CHECK(SAY_HURLEY_WAKE == 0 && SAY_HURLEY_ARRIVE == 1 && SAY_HURLEY_DEATH == 5);
    }

    void TestArena()
    {
        // He spawns on his arena, and the six keg spots, the escort path and the stock keg cluster are on it.
        CHECK(InArena(kHurleySpawn));
        CHECK(ArenaFor(BOSS_HURLEY).Contains(kHurleySpawn.XY(), kHurleySpawn.z));
        for (Point3 const& keg : kKegSpots)
            CHECK(InArena(keg));
        for (Point3 const& node : kWakePath)
            CHECK(InArena(node));
        // The keg spots are NM's six (K4 moved mid-floor, clear of the bar patrons), on the lower floor's level.
        CHECK(kKegSpots.size() == 6);
        CHECK(std::fabs(kKegSpots[3].x - 907.f) < 0.01f && std::fabs(kKegSpots[3].y + 158.5f) < 0.01f);
        // [db] the nearest Grim Guzzler patron (faction 674) to K4 is 23 yd away; the old K4 stood 1.5 yd from one.
        CHECK(Dist(kKegSpots[3], Point3{ 878.4f, -158.2f, -49.7f }) > 20.f);
        for (Point3 const& keg : kKegSpots)
            CHECK(std::fabs(keg.z - kFloorZ) < 0.5f);
        // The legs NM measured: 17-25 yd between neighbours (7-10 s at his walk).
        CHECK(Dist(kKegSpots[0], kKegSpots[1]) > 16.f && Dist(kKegSpots[0], kKegSpots[1]) < 18.f);   // K1-K2 17.2
        CHECK(Dist(kKegSpots[4], kKegSpots[5]) > 21.f && Dist(kKegSpots[4], kKegSpots[5]) < 23.f);   // K5-K6 22.0
        // Two puddles never overlap a keg spot's neighbour: every pair of spots more than two puddle radii apart.
        for (std::size_t i = 0; i < kKegSpots.size(); ++i)
            for (std::size_t j = i + 1; j < kKegSpots.size(); ++j)
                CHECK(Dist(kKegSpots[i], kKegSpots[j]) > 2.f * kPuddleRadius);
        // The Finder start S4b (843.8, -167.8) is off his arena: a group arriving there pulls nothing.
        CHECK(!InArena(Point3{ 843.8f, -167.8f, -49.7f }));
    }

    void TestKegRun()
    {
        KegRun run;
        CHECK(run.Left() == 6);
        CHECK(run.CanStart());
        CHECK(run.Pending() == -1);

        // A drink: walk, arrive, drink, a stack; the keg is gone.
        CHECK(run.Start(2));
        CHECK(run.phase == LurchPhase::Walking && run.marked == 2);
        CHECK(!run.CanStart());
        CHECK(!run.Start(3));               // one lurch at a time
        CHECK(!run.DrinkDone());            // not drinking yet
        CHECK(run.Arrived());
        CHECK(!run.Arrived());              // once
        CHECK(run.phase == LurchPhase::Drinking);
        CHECK(run.DrinkDone());
        CHECK(run.stacks == 1 && run.Left() == 5 && !run.Alive(2) && run.marked == -1);
        CHECK(run.phase == LurchPhase::None);
        CHECK(!run.Start(2));               // drained

        // Smashed on the way: he turns back, no stack.
        CHECK(run.Start(0));
        CHECK(run.Died(0) == KegEnd::Smashed);
        CHECK(run.phase == LurchPhase::None && run.marked == -1 && run.stacks == 1 && run.smashed == 1);
        CHECK(run.Died(0) == KegEnd::Ignored);

        // Smashed during the drink: no heal, no stack.
        CHECK(run.Start(1));
        CHECK(run.Arrived());
        CHECK(run.Died(1) == KegEnd::Smashed);
        CHECK(!run.DrinkDone());
        CHECK(run.stacks == 1 && run.smashed == 2);

        // Another keg (not the marked one) dying spills but changes nothing else.
        CHECK(run.Start(3));
        CHECK(run.Died(4) == KegEnd::Spilled);
        CHECK(run.phase == LurchPhase::Walking && run.marked == 3);

        // Gave up (the deadline, too far): the same keg is the next lurch's.
        CHECK(run.GiveUp());
        CHECK(!run.GiveUp());
        CHECK(run.Pending() == 3);
        CHECK(run.Restart());
        CHECK(run.phase == LurchPhase::Walking && run.marked == 3);
        CHECK(run.Arrived() && run.DrinkDone());
        CHECK(run.stacks == 2);

        // The last keg: then no more lurches.
        CHECK(run.Left() == 1 && run.Alive(5));
        CHECK(run.Start(5) && run.Arrived() && run.DrinkDone());
        CHECK(run.Left() == 0 && !run.CanStart() && run.stacks == 3);
        CHECK(PickKeg(run.alive, 7) == -1);

        // Six drinks at most: the Liquid Courage cap is the keg count.
        KegRun all;
        for (std::uint8_t i = 0; i < kKegCount; ++i)
            CHECK(all.Start(i) && all.Arrived() && all.DrinkDone());
        CHECK(all.stacks == kKegCount && all.Left() == 0);
    }

    void TestPickKeg()
    {
        // Every standing keg can be picked, never a gone one.
        std::uint8_t const alive = 0b101101;    // K1, K3, K4, K6
        std::set<int> picked;
        for (std::uint32_t roll = 0; roll < 16; ++roll)
        {
            std::int8_t const k = PickKeg(alive, roll);
            CHECK(k >= 0 && ((alive >> k) & 1u));
            picked.insert(k);
        }
        CHECK(picked == (std::set<int>{ 0, 2, 3, 5 }));
        CHECK(PickKeg(kAllKegs, 0) == 0 && PickKeg(kAllKegs, 5) == 5 && PickKeg(kAllKegs, 6) == 0);
        CHECK(PickKeg(0, 3) == -1);
        CHECK(PickKeg(0b010000, 99) == 4);
    }

    void TestWalk()
    {
        // He stops 3 yd short of the keg, on the line from where he stands.
        Vec2 const from{ 880.f, -150.f };
        Vec2 const keg{ 900.f, -150.f };
        Vec2 const to = ApproachPoint(from, keg, kKegStandOffYd);
        CHECK(std::fabs(to.x - 897.f) < 0.01f && std::fabs(to.y + 150.f) < 0.01f);
        // Already that close: he stays.
        Vec2 const near{ 898.f, -150.f };
        Vec2 const stay = ApproachPoint(near, keg, kKegStandOffYd);
        CHECK(stay.x == near.x && stay.y == near.y);
        // The deadline: the plain walk (2.5 yd/s) plus 4 s; the spec's 6-10 s legs fit.
        CHECK(LurchDeadlineMs(0.f) == kLurchSlackMs);
        CHECK(LurchDeadlineMs(25.f) == 10000 + kLurchSlackMs);
        CHECK(LurchDeadlineMs(-3.f) == kLurchSlackMs);
        // From his spawn the farthest keg (K6, 38.7 yd) is a 15.5 s walk: longer than a heroic interval with the drink,
        // which is fine, since a lurch only starts once the last one has ended (KegRun::CanStart).
        float const far = Dist(kHurleySpawn, kKegSpots[5]);
        CHECK(far > 38.f && far < 40.f);
    }

    void TestBreath()
    {
        // The cone: 15 yd, 60 degrees; heroic after a drink twice as wide; normal never.
        CHECK(BreathAngleDeg(false, false) == 60.f && BreathAngleDeg(false, true) == 60.f);
        CHECK(BreathAngleDeg(true, false) == 60.f && BreathAngleDeg(true, true) == 120.f);
        Vec2 const apex{ 0.f, 0.f };
        float const facing = 0.f;   // along +x
        // A tank in front (reach 1.5) is in the arc; one behind is not.
        CHECK(CircleInCone(apex, facing, 60.f, kBreathLengthYd, Vec2{ 3.f, 0.f }, 1.5f));
        CHECK(!CircleInCone(apex, facing, 60.f, kBreathLengthYd, Vec2{ -3.f, 0.f }, 1.5f));
        // A puddle centered just past the tip still touches it (its 5 yd radius); one 21 yd out does not.
        CHECK(CircleInCone(apex, facing, 60.f, kBreathLengthYd, Vec2{ 19.f, 0.f }, kPuddleRadius));
        CHECK(!CircleInCone(apex, facing, 60.f, kBreathLengthYd, Vec2{ 21.f, 0.f }, kPuddleRadius));
        // A puddle at 45 degrees, 12 yd out: outside the 60 degree cone's half-angle (30) widened by asin(5/12) (24.6),
        // so it touches; at 70 degrees it does not; the 120 degree breath (half 60) reaches it.
        auto at = [](float deg, float d)
        {
            float const r = deg * DungeonKit::kPi / 180.f;
            return Vec2{ d * std::cos(r), d * std::sin(r) };
        };
        CHECK(CircleInCone(apex, facing, 60.f, kBreathLengthYd, at(45.f, 12.f), kPuddleRadius));
        CHECK(!CircleInCone(apex, facing, 60.f, kBreathLengthYd, at(70.f, 14.f), kPuddleRadius));
        CHECK(CircleInCone(apex, facing, 120.f, kBreathLengthYd, at(70.f, 14.f), kPuddleRadius));
        // The facing wraps (a cone pointing at pi covers -pi + a little).
        CHECK(CircleInCone(apex, DungeonKit::kPi, 60.f, kBreathLengthYd, at(-175.f, 8.f), 0.5f));
        // A puddle under him always burns.
        CHECK(CircleInCone(apex, facing, 60.f, kBreathLengthYd, Vec2{ -2.f, 1.f }, kPuddleRadius));
    }

    void TestWake()
    {
        // The stock escort path [db], from his spawn to the cellar side; the last node is his home.
        CHECK(kWakePath.size() == 3);
        CHECK(Dist(kHurleySpawn, kWakePath[0]) < 10.f);
        CHECK(Dist(kWakePath[2], kWakePath[1]) < 6.f);
        // A Crony's copy keeps its offset from him; one standing on his spawn follows his nodes.
        Point3 const crony{ 879.0f, -155.3f, -49.8f };
        Point3 const n = CronyNode(kWakePath[2], crony, kHurleySpawn);
        CHECK(std::fabs((n.x - kWakePath[2].x) - (crony.x - kHurleySpawn.x)) < 0.01f);
        CHECK(std::fabs((n.y - kWakePath[2].y) - (crony.y - kHurleySpawn.y)) < 0.01f);
        CHECK(n.z == kWakePath[2].z);
        Point3 const same = CronyNode(kWakePath[1], kHurleySpawn, kHurleySpawn);
        CHECK(same.x == kWakePath[1].x && same.y == kWakePath[1].y);
        // The three stock Cronies' spawns [db] end within 4 yd of his home (the trio stays together).
        for (Point3 const& c : { Point3{ 879.018f, -155.273f, -49.76f }, Point3{ 876.961f, -151.796f, -49.76f },
            Point3{ 876.535f, -154.334f, -49.76f } })
        {
            Point3 const end = CronyNode(kWakePath[2], c, kHurleySpawn);
            CHECK(Dist(end, kWakePath[2]) < 4.f);
            CHECK(InArena(end));
        }
        // The reload check: all three keg GOs found and none standing.
        CHECK(WakeFromUsedKegs(3, 0));
        CHECK(!WakeFromUsedKegs(3, 1));
        CHECK(!WakeFromUsedKegs(2, 0));     // a grid not loaded: never a wake from missing objects
        CHECK(!WakeFromUsedKegs(0, 0));
        // The keg GOs sit 37-41 yd from his spawn [db]: inside the scan.
        CHECK(Dist(kHurleySpawn, Point3{ 918.7f, -154.0f, -49.8f }) < kKegGoScanYd);

        // D17's bar model: the third keg wakes him, once; nothing else of the bar moves (BarModel::KegUsed).
        BrdGuzzler::BarModel bar;
        CHECK(!bar.KegUsed() && !bar.KegUsed());
        CHECK(bar.hurley == BrdGuzzler::HurleyState::Hidden);
        CHECK(bar.KegUsed());
        CHECK(bar.hurley == BrdGuzzler::HurleyState::Awake);
        CHECK(!bar.KegUsed());
        CHECK(BrdGuzzler::kKegsToWakeHurley == kStockKegGos);
        // His wake data is the keg SmartAI's SET_DATA 1,1, never the patrons' drink pair (1, 4).
        CHECK(DATA_HURLEY_WAKE == 1 && DATA_HURLEY_WAKE_VALUE == 1);
        CHECK(DATA_HURLEY_WAKE_VALUE != DATA_DARK_IRON_ALE_DRINK);
        CHECK(DATA_HURLEY_AWAKE != DATA_HURLEY_WAKE);
    }

    void TestTuning()
    {
        // S4 "Build spec".
        CHECK(kBreathPct.normal == 30.f && kBreathPct.heroic == 45.f);
        CHECK(kBreathTankPct.normal == 10.f && kBreathTankPct.heroic == 15.f);
        CHECK(kBurningLagerPct == 8.f && kBottleTossPct == 25.f);
        CHECK(kDrinkHealPct == 10 && kCourageDamagePct == 15 && kCourageHastePct == 10);
        CHECK(kLagerBuzzPct == 10 && kTipsyPct == 30 && kMortalStrikeHealingPct == 50);
        CHECK(kHurleyHealth.normal == 140000 && kHurleyHealth.heroic == 200000);
        CHECK(kCronyHealth.normal == 8000 && kCronyHealth.heroic == 12000);
        CHECK(kKegHealth.normal == 6000 && kKegHealth.heroic == 9000);
        CHECK(kKegRunFirstMs == 15000 && kKegRunEveryMs.normal == 25000 && kKegRunEveryMs.heroic == 20000);
        CHECK(kDrinkMs == 3000 && kBreathFirstMs == 8000 && kBreathEveryMs == 15000 && kBreathCastMs == 2000);
        CHECK(kPuddleLifeMs == 30000 && kBurningLagerMs == 20000 && kLagerBuzzMs == 5000);
        CHECK(kBottleTossFirstMs == 6000 && kBottleTossEveryMs == 12000 && kBottleTossWarnMs == 1500);
        CHECK(kPuddleRadius == 5.f && kBottleRadius == 3.f && kBreathLengthYd == 15.f);
        // Space math (S4): at most two amber puddles at once (30 s puddles, a lurch every 25 s; heroic 20 s), so
        // never more than two thirds of a keg run apart.
        CHECK(kPuddleLifeMs / kKegRunEveryMs.normal + 1 <= 2);
        CHECK(kPuddleLifeMs / kKegRunEveryMs.heroic + 1 <= 2);
        // The failing path (S4): a drink heals 10% of 140k = 14,000, a smash costs 6,000.
        CHECK(kHurleyHealth.normal / 100 * kDrinkHealPct > kKegHealth.normal);
        // A drink always ends before the next lurch is due (walk + drink inside the interval at the longest leg).
        CHECK(LurchDeadlineMs(25.f) + kDrinkMs < kKegRunEveryMs.heroic);
    }
}

int main()
{
    TestSlice();
    TestArena();
    TestKegRun();
    TestPickKeg();
    TestWalk();
    TestBreath();
    TestWake();
    TestTuning();
    return Report("brd_hurley_test");
}
