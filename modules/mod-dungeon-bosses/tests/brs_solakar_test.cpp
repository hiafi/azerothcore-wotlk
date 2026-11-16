// Host tests for SolakarLogic.h (B11: Solakar Flamewreath): the slice and the ids, the heat table (SP ruling 56),
// Scorched Hands and the bots' hold times, who may catch, Flamewreath and the enrage, the fight's clock (the Hunt, War
// Stomp never inside it, heroic Spear Wound halfway between Hunts), the clutches built from the Rookery's real eggs
// (gameobject 175124, read-only SELECT 2026-11-15) and the hatch picks.
#include "SolakarLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace BlackrockSpireRework;
using namespace BrsSolakar;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // The 141 stock eggs on the Rookery floor (SolakarArena's box: x 48..108, y -338.5..-252, z 88..100).
    std::vector<Vec2> const kRookeryEggs = {
        { 100.6f, -312.5f }, { 101.5f, -311.5f }, { 102.4f, -304.4f }, { 104.2f, -289.4f }, { 104.3f, -302.8f },
        { 104.4f, -299.4f }, { 104.6f, -288.0f }, { 104.9f, -286.1f }, { 105.0f, -300.9f }, { 106.2f, -299.8f },
        { 106.4f, -281.4f }, { 106.6f, -283.8f }, { 107.2f, -287.7f }, { 107.4f, -282.5f }, { 107.9f, -299.9f },
        { 48.8f, -337.1f }, { 50.2f, -316.7f }, { 51.3f, -338.1f }, { 51.6f, -315.0f }, { 51.9f, -316.6f },
        { 54.3f, -255.4f }, { 54.6f, -336.7f }, { 55.4f, -254.4f }, { 56.8f, -332.3f }, { 56.9f, -253.3f },
        { 56.9f, -255.4f }, { 57.9f, -336.1f }, { 57.9f, -256.7f }, { 58.1f, -253.9f }, { 58.8f, -334.1f },
        { 59.0f, -271.1f }, { 59.2f, -255.1f }, { 59.2f, -317.3f }, { 59.3f, -332.2f }, { 59.4f, -337.4f },
        { 60.2f, -270.2f }, { 60.4f, -312.3f }, { 60.7f, -268.1f }, { 61.0f, -315.7f }, { 61.1f, -313.9f },
        { 61.3f, -272.0f }, { 62.5f, -334.3f }, { 63.3f, -317.1f }, { 63.6f, -336.6f }, { 64.2f, -268.5f },
        { 64.9f, -317.1f }, { 65.3f, -267.9f }, { 65.6f, -305.1f }, { 66.0f, -303.6f }, { 66.8f, -302.5f },
        { 68.1f, -302.4f }, { 68.3f, -314.9f }, { 68.7f, -307.1f }, { 69.5f, -303.6f }, { 69.7f, -332.2f },
        { 69.9f, -326.6f }, { 70.0f, -329.3f }, { 70.5f, -334.1f }, { 70.9f, -305.0f }, { 71.7f, -306.1f },
        { 71.8f, -278.2f }, { 72.0f, -328.4f }, { 72.0f, -331.2f }, { 72.1f, -325.8f }, { 72.1f, -276.6f },
        { 72.1f, -285.9f }, { 73.1f, -306.7f }, { 73.5f, -324.2f }, { 74.0f, -287.3f }, { 74.1f, -291.8f },
        { 74.2f, -273.6f }, { 74.4f, -307.4f }, { 74.8f, -275.8f }, { 75.2f, -292.9f }, { 76.2f, -277.4f },
        { 76.6f, -263.6f }, { 76.9f, -275.6f }, { 77.3f, -262.1f }, { 77.5f, -292.3f }, { 77.7f, -295.1f },
        { 78.6f, -266.5f }, { 79.0f, -331.7f }, { 79.1f, -328.4f }, { 79.2f, -262.5f }, { 79.6f, -291.5f },
        { 79.8f, -326.0f }, { 80.5f, -316.6f }, { 80.8f, -253.6f }, { 80.9f, -328.5f }, { 81.0f, -332.5f },
        { 81.0f, -265.0f }, { 81.1f, -330.1f }, { 81.8f, -326.1f }, { 81.8f, -317.4f }, { 82.0f, -336.0f },
        { 82.5f, -315.9f }, { 82.8f, -267.7f }, { 82.9f, -330.6f }, { 83.0f, -333.1f }, { 83.2f, -327.7f },
        { 83.7f, -252.4f }, { 84.0f, -325.9f }, { 84.0f, -315.1f }, { 84.1f, -268.8f }, { 84.7f, -301.8f },
        { 85.6f, -293.5f }, { 85.7f, -314.0f }, { 85.8f, -295.4f }, { 86.1f, -302.5f }, { 87.2f, -252.5f },
        { 87.3f, -254.4f }, { 87.4f, -278.1f }, { 87.8f, -314.7f }, { 87.9f, -303.2f }, { 87.9f, -280.0f },
        { 88.1f, -333.2f }, { 88.7f, -301.1f }, { 88.8f, -316.1f }, { 89.1f, -290.1f }, { 89.9f, -301.8f },
        { 90.0f, -318.2f }, { 90.3f, -332.6f }, { 90.6f, -320.0f }, { 91.8f, -291.3f }, { 91.9f, -301.9f },
        { 92.1f, -334.9f }, { 92.1f, -279.9f }, { 92.6f, -288.2f }, { 92.6f, -304.4f }, { 93.7f, -290.1f },
        { 93.8f, -305.5f }, { 93.9f, -288.3f }, { 94.6f, -281.1f }, { 94.9f, -288.6f }, { 95.5f, -313.6f },
        { 96.1f, -287.5f }, { 96.3f, -280.5f }, { 97.1f, -281.9f }, { 97.2f, -310.9f }, { 97.3f, -313.4f },
        { 98.9f, -313.0f }
    };

    void TestSliceAndIds()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210390u && kSpellSlice.last == 210429u);
        for (std::uint32_t id : { SPELL_SK_FATHER_FLAME, SPELL_SK_TOSS, SPELL_SK_SEARING_HEAT, SPELL_SK_SCORCHED_HANDS,
                 SPELL_SK_CATCH_FLARE, SPELL_SK_HATCH_BURST, SPELL_SK_HATCHER_HATCH, SPELL_SK_STOLEN_FLAME,
                 SPELL_SK_FLAMEWREATH, SPELL_SK_FLAMEWREATH_H, SPELL_SK_WREATHED, SPELL_SK_WREATHED_TICK,
                 SPELL_SK_HUNT_ROAR, SPELL_SK_HUNT, SPELL_SK_HUNTED, SPELL_SK_WAR_STOMP_BAR, SPELL_SK_WAR_STOMP,
                 SPELL_SK_STOMP_LOOK, SPELL_SK_WAR_STOMP_STUN, SPELL_SK_GROUND_STOMP_BAR, SPELL_SK_GROUND_STOMP,
                 SPELL_SK_SPEAR_THROW, SPELL_SK_SPEAR_WOUND, SPELL_SK_SPEAR_TEAR, SPELL_SK_CAUTERIZE })
            CHECK(kSpellSlice.Contains(id));
        CHECK(SPELL_SK_FATHER_FLAME == 210390u);
        CHECK(SPELL_SK_TOSS == 210391u);
        CHECK(SPELL_SK_CAUTERIZE == 210414u);
        // The one flame (R-2 ruling: the custom bag item, the stock off-hand only the keepsake) and the flame whelp S0
        // reserved.
        CHECK(kItemFatherFlame == 70610u);
        CHECK(kItemFatherFlameKeepsake == 13371u);
        CHECK(kItemFatherFlame != kItemFatherFlameKeepsake);
        CHECK(NPC_BRS_FLAME_WHELP == 300731u);
        CHECK(kCreaturesWave2.Contains(NPC_BRS_FLAME_WHELP));
        CHECK(GO_FLOOR_FLAME == 185555u);
        // He is summoned at kSolakarPosBoss, inside his arena; Father Flame (the brazier) too.
        CHECK(SolakarArena().Contains(kSolakarPosBoss.XY(), kSolakarPosBoss.z));
        CHECK(ArenaFor(BOSS_SOLAKAR).Contains(kSolakarPosBoss.XY(), kSolakarPosBoss.z));
        CHECK(SolakarArena().Contains({ kFatherFlame.x, kFatherFlame.y }, kFatherFlame.z));
        CHECK(SolakarArena().Contains(kSolakarPosLeft.XY(), kSolakarPosLeft.z));
        CHECK(SolakarArena().Contains(kSolakarPosRight.XY(), kSolakarPosRight.z));
        // The instance's event: Solakar at 30 s (SK1); the two actions are distinct.
        CHECK(kSolakarArriveMs == 30000u);
        CHECK(ACTION_SOLAKAR_ARRIVE != ACTION_SOLAKAR_RESET);
    }

    void TestHeatTable()
    {
        // SP ruling 56: first second, rise, over a 6 s hold.
        CHECK(Near(SearingHeatPct(false, false, 1), 1.f));
        CHECK(Near(SearingHeatPct(false, false, 2), 1.5f));
        CHECK(Near(SearingHeatPct(false, true, 1), 2.f));
        CHECK(Near(SearingHeatPct(false, true, 2), 3.f));
        CHECK(Near(SearingHeatPct(true, false, 2), 2.f));
        CHECK(Near(SearingHeatPct(true, true, 2), 3.5f));
        CHECK(Near(SearingHeatPct(false, false, 0), 0.f));
        CHECK(Near(SearingHeatTotalPct(false, false, 6), 13.5f));
        CHECK(Near(SearingHeatTotalPct(false, true, 6), 27.f));
        CHECK(Near(SearingHeatTotalPct(true, false, 6), 21.f));
        CHECK(Near(SearingHeatTotalPct(true, true, 6), 34.5f));
        // "about 13% over a 6 sec hold, 45% over 12" (normal at 5).
        CHECK(Near(SearingHeatTotalPct(false, false, 12), 45.f));
        // The unhealed death: about 19 / 13 / 14 / 11 s.
        CHECK(SecondsToBurnOut(false, false) == 19u);
        CHECK(SecondsToBurnOut(false, true) == 13u);
        CHECK(SecondsToBurnOut(true, false) == 14u);
        CHECK(SecondsToBurnOut(true, true) == 11u);
        // It never stops rising (ruling 57).
        for (std::uint32_t t = 1; t < 40; ++t)
            CHECK(SearingHeatPct(true, true, t + 1) > SearingHeatPct(true, true, t));
        // The holder always has time to throw: 30% is passed at 10 / 7 / 8 / 6 s (SP's "7" for heroic at 5 is 28%).
        auto passes30 = [](bool heroic, bool big)
        {
            std::uint32_t s = 0;
            while (SearingHeatTotalPct(heroic, big, s) < 30.f)
                ++s;
            return s;
        };
        CHECK(passes30(false, false) == 10u);
        CHECK(passes30(false, true) == 7u);
        CHECK(passes30(true, false) == 8u);
        CHECK(passes30(true, true) == 6u);
        // Scorched Hands and the bots' hold before a throw.
        CHECK(ScorchedHandsMs(false, false) == 15000u);
        CHECK(ScorchedHandsMs(false, true) == 25000u);
        CHECK(ScorchedHandsMs(true, false) == 10000u);
        CHECK(ScorchedHandsMs(true, true) == 25000u);
        CHECK(ThrowHoldMs(false, false) == 6000u);
        CHECK(ThrowHoldMs(false, true) == 4000u);
        CHECK(ThrowHoldMs(true, false) == 4000u);
        CHECK(ThrowHoldMs(true, true) == 3000u);
        // A bot's throw always comes before a third of the unhealed death.
        for (bool heroic : { false, true })
            for (bool big : { false, true })
                CHECK(ThrowHoldMs(heroic, big) / 1000 * 3 <= SecondsToBurnOut(heroic, big));
        // Size: 6 or more.
        CHECK(!IsBig(5));
        CHECK(IsBig(6));
        CHECK(IsBig(10));
        // The toss: 0.75 s at 25 yd, inside the pass's flight at 30 yd.
        CHECK(Near(25.f / kTossSpeed, 0.758f, 0.01f));
        CHECK(kTossRangeYd / kTossSpeed * 1000.f < static_cast<float>(kTossFlightMs));
        CHECK(kReadyCatchers.At(5) == 1u);
        CHECK(kReadyCatchers.At(6) == 2u);
    }

    void TestCatchAndWreath()
    {
        // Not Scorched; on heroic the wounded catch even while Scorched.
        CHECK(CanCatch(false, false, false));
        CHECK(!CanCatch(true, false, false));
        CHECK(!CanCatch(true, true, false));
        CHECK(CanCatch(true, true, true));
        CHECK(!CanCatch(true, false, true));
        CHECK(CanCatch(false, true, true));
        // Flamewreath: +20% (heroic +25%) a stack, cap 3.
        CHECK(Near(WreathMult(false, 0), 1.f));
        CHECK(Near(WreathMult(false, 1), 1.2f));
        CHECK(Near(WreathMult(false, 3), 1.6f));
        CHECK(Near(WreathMult(false, 9), 1.6f));
        CHECK(Near(WreathMult(true, 2), 1.5f));
        CHECK(Near(WreathMult(true, 3), 1.75f));
        // Three stacks, then the fourth is the enrage, once.
        std::uint32_t stacks = 0;
        bool enraged = false;
        for (int i = 0; i < 3; ++i)
        {
            WreathStep const step = AddWreath(stacks, enraged);
            CHECK(step.stacks == stacks + 1);
            CHECK(!step.enrage);
            stacks = step.stacks;
        }
        WreathStep const fourth = AddWreath(stacks, enraged);
        CHECK(fourth.stacks == kFlamewreathCap);
        CHECK(fourth.enrage);
        enraged = true;
        CHECK(!AddWreath(kFlamewreathCap, enraged).enrage);
        // The sear and the wound.
        CHECK(kSearMs == 2000u);
        CHECK(kSpearWoundMs == 12000u);
        CHECK(kSpearTargets.At(5) == 1u);
        CHECK(kSpearTargets.At(10) == 2u);
        CHECK(kWhelpCap.At(5) == 6u);
        CHECK(kWhelpCap.At(6) == 12u);
    }

    struct Fired
    {
        std::vector<std::uint64_t> hunts;
        std::vector<std::uint64_t> stomps;
        std::vector<std::uint64_t> spears;
    };

    // The clock over `ms` at 100 ms steps, a holder always there (or never), always free; a Hunt books its whole
    // window, a stomp its bar.
    Fired RunClock(bool heroic, std::uint64_t ms, bool holder = true)
    {
        FightClock clock;
        clock.Start(heroic);
        Fired out;
        for (std::uint64_t now = 0; now <= ms; now += 100)
        {
            for (int guard = 0; guard < 3; ++guard)
            {
                Beat const beat = clock.Next(now, true, holder);
                if (beat == Beat::None)
                {
                    if (now >= clock.NextHunt() && !holder && !clock.InHunt(now))
                        clock.HuntWaits(now);
                    break;
                }
                if (beat == Beat::Hunt)
                    out.hunts.push_back(now);
                else if (beat == Beat::Stomp)
                    out.stomps.push_back(now);
                else
                    out.spears.push_back(now);
                clock.Started(beat, now);
            }
        }
        return out;
    }

    void TestFightClock()
    {
        // Normal: Hunts at 10 s, then every 25 s; the first stomp waits out the first Hunt (10 s + 1.5 + 8 + 1).
        Fired const n = RunClock(false, 180000);
        CHECK(!n.hunts.empty() && n.hunts.front() == 10000u);
        for (std::size_t i = 1; i < n.hunts.size(); ++i)
            CHECK(n.hunts[i] - n.hunts[i - 1] == 25000u);
        CHECK(!n.stomps.empty() && n.stomps.front() == 20500u);
        CHECK(n.spears.empty());
        // Never a stomp inside a Hunt (its roar and its chase), nor within a second after one.
        for (std::uint64_t s : n.stomps)
            for (std::uint64_t h : n.hunts)
                CHECK(!(s >= h && s < h + kHuntRoarMs + kHuntChaseMs + kStompAfterHuntMs));
        // And never a Hunt inside a stomp's bar.
        for (std::uint64_t h : n.hunts)
            for (std::uint64_t s : n.stomps)
                CHECK(!(h >= s && h < s + kStompCastMs));
        // About one stomp every 20 s (some wait for a Hunt): 7 or more in 3 minutes.
        CHECK(n.stomps.size() >= 7u);

        // Heroic: Hunts every 20 s, a spear 10 s after each Hunt starts (halfway between them).
        Fired const h = RunClock(true, 180000);
        CHECK(!h.hunts.empty() && h.hunts.front() == 10000u);
        for (std::size_t i = 1; i < h.hunts.size(); ++i)
            CHECK(h.hunts[i] - h.hunts[i - 1] == 20000u);
        CHECK(!h.spears.empty() && h.spears.front() == 20000u);
        CHECK(h.spears.size() + 1 >= h.hunts.size());
        for (std::size_t i = 0; i < h.spears.size(); ++i)
            CHECK(h.spears[i] == h.hunts[i] + kSpearAfterHuntMs);
        for (std::uint64_t s : h.stomps)
            for (std::uint64_t hu : h.hunts)
                CHECK(!(s >= hu && s < hu + kHuntRoarMs + kHuntChaseMs + kStompAfterHuntMs));

        // Nobody holds the flame: no Hunt (it waits), the stomps go on.
        Fired const none = RunClock(false, 60000, false);
        CHECK(none.hunts.empty());
        CHECK(!none.stomps.empty() && none.stomps.front() == kStompFirstMs);

        // A Hunt that ends early (a Reclaim) frees the stomp a second later.
        FightClock clock;
        clock.Start(false);
        CHECK(clock.Next(10000, true, true) == Beat::Hunt);
        clock.Started(Beat::Hunt, 10000);
        CHECK(clock.Next(15000, true, true) == Beat::None);
        clock.HuntEnded(15000);
        CHECK(clock.Next(15500, true, true) == Beat::None);
        CHECK(clock.Next(16000, true, true) == Beat::Stomp);
        // He is running for a dropped flame: nothing starts.
        CHECK(clock.Next(16000, false, true) == Beat::None);
    }

    void TestClutches()
    {
        // A chain within 3 yd is one clutch; an egg 5 yd away is its own.
        std::vector<Vec2> const small = { { 0.f, 0.f }, { 2.f, 0.f }, { 4.f, 0.f }, { 9.f, 0.f } };
        std::vector<Clutch> const two = BuildClutches(small);
        CHECK(two.size() == 2u);
        CHECK(two[0].eggs.size() == 3u);
        CHECK(Near(two[0].center.x, 2.f));
        CHECK(Near(two[0].radius, 2.f));
        CHECK(two[1].eggs.size() == 1u);
        CHECK(Near(two[1].radius, 0.f));
        CHECK(Near(ClutchZoneRadius(2.f), 3.5f));
        // A long chain (10 eggs, 2.5 yd apart, 22.5 yd) is split until each part spreads at most 4 yd.
        std::vector<Vec2> chain;
        for (int i = 0; i < 10; ++i)
            chain.push_back({ 2.5f * static_cast<float>(i), 0.f });
        std::vector<Clutch> const parts = BuildClutches(chain);
        CHECK(parts.size() >= 3u);
        std::size_t total = 0;
        for (Clutch const& c : parts)
        {
            CHECK(c.radius <= kClutchMaxYd + 0.001f);
            total += c.eggs.size();
        }
        CHECK(total == chain.size());

        // The real Rookery: every egg in exactly one clutch, every clutch at most 4 yd wide, about 40 of them.
        std::vector<Clutch> const rookery = BuildClutches(kRookeryEggs);
        CHECK(kRookeryEggs.size() == 141u);
        std::set<std::size_t> seen;
        for (Clutch const& c : rookery)
        {
            CHECK(c.radius <= kClutchMaxYd + 0.001f);
            CHECK(!c.eggs.empty());
            for (std::size_t i : c.eggs)
                CHECK(seen.insert(i).second);
        }
        CHECK(seen.size() == kRookeryEggs.size());
        CHECK(rookery.size() >= 30u && rookery.size() <= 60u);
        // Deterministic.
        std::vector<Clutch> const again = BuildClutches(kRookeryEggs);
        CHECK(again.size() == rookery.size());
        for (std::size_t i = 0; i < again.size() && i < rookery.size(); ++i)
            CHECK(again[i].eggs == rookery[i].eggs);
    }

    void TestHatchPicks()
    {
        std::vector<Vec2> const eggs = { { 0.f, 0.f }, { 1.f, 0.f }, { 2.f, 0.f }, { 10.f, 0.f }, { 11.f, 0.f },
            { 30.f, 0.f } };
        std::vector<bool> live(eggs.size(), true);
        // The catch's 4 yd: the three near ones, nearest first.
        std::vector<std::size_t> const near = EggsWithin(eggs, live, { 0.5f, 0.f }, kCatchEggYd);
        CHECK(near.size() == 3u);
        CHECK(near.front() == 0u || near.front() == 1u);
        // A hatched egg is gone.
        live[1] = false;
        CHECK(EggsWithin(eggs, live, { 0.5f, 0.f }, kCatchEggYd).size() == 2u);
        // The stir: the nearest live egg.
        CHECK(NearestEgg(eggs, live, { 29.f, 0.f }) == std::optional<std::size_t>(5u));
        CHECK(NearestEgg(eggs, live, { 1.f, 0.f }) == std::optional<std::size_t>(0u));
        // The Hatcher's clutch: 3 or more live eggs. With egg 1 gone the near clutch has 2: it runs to none of them.
        std::vector<Clutch> const clutches = BuildClutches(eggs);
        CHECK(!NearestClutch(eggs, live, clutches, { 0.f, 0.f }).has_value());
        live[1] = true;
        std::optional<Vec2> const run = NearestClutch(eggs, live, clutches, { 20.f, 0.f });
        CHECK(run.has_value() && Near(run->x, 1.f));
        // No live egg anywhere: nothing.
        std::vector<bool> const none(eggs.size(), false);
        CHECK(!NearestEgg(eggs, none, { 0.f, 0.f }).has_value());
        CHECK(EggsWithin(eggs, none, { 0.f, 0.f }, 50.f).empty());
        // A clutch's live part shrinks with its eggs.
        std::optional<Clutch> const whole = LivePart(eggs, live, clutches[0]);
        CHECK(whole.has_value() && whole->eggs.size() == 3u);
        live[0] = false;
        std::optional<Clutch> const part = LivePart(eggs, live, clutches[0]);
        CHECK(part.has_value() && part->eggs.size() == 2u && Near(part->center.x, 1.5f));
        // The real Rookery: a clutch of 3+ is in reach of the stock spawn spots.
        std::vector<bool> const all(kRookeryEggs.size(), true);
        CHECK(NearestClutch(kRookeryEggs, all, BuildClutches(kRookeryEggs), kSolakarPosRight.XY()).has_value());
    }

    // R-2 fixes: a run that cannot reach the flame gives up into a Reclaim (m-5); held and dropped flames never save
    // the instance (n-1), while the attempt's end (nobody, the brazier) does.
    void TestRunAndFlameSave()
    {
        // The budget: the straight run at his speed, half again, plus the grace.
        CHECK(RunBudgetMs(0.f, 10.f) == kRunGraceMs);
        CHECK(RunBudgetMs(10.f, 10.f) == 1500u + kRunGraceMs);
        CHECK(RunBudgetMs(-3.f, 10.f) == kRunGraceMs);
        CHECK(RunBudgetMs(10.f, 0.f) == 15000u + kRunGraceMs);    // a stopped boss counts as 1 yd/s
        // The Rookery box's diagonal (48..108 x -338.5..-252, about 105 yd) at his 10 yd/s run (speed_run 1.43) fits
        // with room: a legit run never gives up.
        float const diagonal = std::sqrt(60.f * 60.f + 86.5f * 86.5f);
        std::uint64_t const budget = RunBudgetMs(diagonal, 10.f);
        CHECK(budget > static_cast<std::uint64_t>(diagonal / 10.f * 1000.f) + 3000u);
        CHECK(budget < 25000u);
        CHECK(!RunGivesUp(1000, budget, 1000));
        CHECK(!RunGivesUp(1000, budget, 1000 + budget - 1));
        CHECK(RunGivesUp(1000, budget, 1000 + budget));
        CHECK(SolakarFlameSaved(FLAME_NONE));
        CHECK(SolakarFlameSaved(FLAME_BRAZIER));
        CHECK(!SolakarFlameSaved(FLAME_HOLDER));
        CHECK(!SolakarFlameSaved(FLAME_FLOOR));
    }
}

int main()
{
    TestSliceAndIds();
    TestHeatTable();
    TestCatchAndWreath();
    TestFightClock();
    TestClutches();
    TestHatchPicks();
    TestRunAndFlameSave();
    return Report("brs_solakar_test");
}
