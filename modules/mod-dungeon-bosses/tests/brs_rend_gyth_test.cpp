// Host tests for RendGythLogic.h (B12: Warchief Rend Blackhand and Gyth): the slice, the texts, the program and the
// rounds, the picks (Dress Hunt, Thumbs Down), the Freezing Sweep's walls against KT-B2's plan, the taunt swaps at 10
// against the user's rule with the real gaps (wave 2 lesson 1: SimulateSwaps, B7 / B14's model, both bosses and the
// heroic trade), and the room.
#include "DungeonKitFrontLogic.h"
#include "RendGythLogic.h"
#include "check.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <set>
#include <span>
#include <string>
#include <vector>

using namespace BlackrockSpireRework;
using namespace BrsRendGyth;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        std::set<std::uint32_t> ids;
        for (std::uint32_t id = kFirstSpell; id <= kLastSpell; ++id)
        {
            CHECK(kSpellSlice.Contains(id));
            ids.insert(id);
        }
        CHECK(ids.size() == 23);
        CHECK(kFirstSpell == 210430 && kLastSpell == 210452);
        CHECK(!kSpellSlice.Contains(SPELL_RG_CORROSIVE_ACID) && !kSpellSlice.Contains(SPELL_RG_MORTAL_STRIKE));
        CHECK(!kSpellsBeast.Contains(kLastSpell));
    }

    void TestTexts()
    {
        TextRange const* nef = nullptr;
        TextRange const* rend = nullptr;
        for (TextRange const& r : kTextRanges)
        {
            if (r.entry == NPC_BRS_NEFARIUS)
                nef = &r;
            if (r.entry == NPC_REND)
                rend = &r;
        }
        CHECK(nef && nef->first == 0 && nef->last == 19 && nef->firstNew == 12);
        CHECK(nef && YELL_NEF_MYSELF == nef->firstNew && SAY_NEF_INSULTED_AGAIN == nef->last);
        CHECK(YELL_NEF_MORTALS_FALLEN == 11 && YELL_NEF_WELCOME == 0 && YELL_NEF_DRESS == 2);
        CHECK(rend && rend->first == 0 && rend->last == 4 && rend->firstNew == 3);
        CHECK(rend && EMOTE_REND_MARK == rend->firstNew && EMOTE_REND_BANNER == rend->last);
    }

    void TestProgram()
    {
        // RG1: group 2 at 15 s, act 2 at 30 s; RG2: 75 s normal, 60 s heroic.
        CHECK(kGroupTwoMs < kActTwoMs && kActTwoMs == 30000);
        CHECK(ActTwoLengthMs(false) == 75000 && ActTwoLengthMs(true) == 60000);
        // 2 / 3 whelps per group; Dress Hunt 3 / 6 normal, 4 / 8 heroic (a count not held reads as 5).
        CHECK(kGroupWhelps.At(5) == 2 && kGroupWhelps.At(6) == 3 && kGroupWhelps.At(10) == 3);
        CHECK(HuntWhelps(false, 5) == 3 && HuntWhelps(false, 10) == 6);
        CHECK(HuntWhelps(true, 5) == 4 && HuntWhelps(true, 6) == 8 && HuntWhelps(true, 0) == 4);
        CHECK(kCondemned.At(5) == 1 && kCondemned.At(7) == 2);
        CHECK(std::string(ActName(Act::Drake)) == "drake");
    }

    void TestRounds()
    {
        // Fixed order: normal 5, 6, 7 and around; heroic 5, 6, 7, 8.
        CHECK(RoundAt(0, false) == Round::DressHunt && RoundAt(1, false) == Round::FreezingSweep);
        CHECK(RoundAt(2, false) == Round::Shadowflame && RoundAt(3, false) == Round::DressHunt);
        CHECK(RoundAt(3, true) == Round::ThumbsDown && RoundAt(4, true) == Round::DressHunt);
        // Heroic: a call every 10 s while each round lasts 15 s (the last 5 s overlap the next).
        CHECK(CallEveryMs(true, 0) == 10000 && kRoundMs - CallEveryMs(true, 0) == 5000);
        CHECK(CallEveryMs(false, 0) == 30000);
        // The bored host: normal past 1:30 every 20 s, past 2:30 two per call; heroic past 1:15 every 7 s, past 2:00
        // every 5 s (three rounds live at once).
        CHECK(BoredStep(false, 89999) == 0 && BoredStep(false, 90000) == 1 && BoredStep(false, 150000) == 2);
        CHECK(CallEveryMs(false, 1) == 20000 && RoundsPerCall(false, 1) == 1 && RoundsPerCall(false, 2) == 2);
        CHECK(BoredStep(true, 74999) == 0 && BoredStep(true, 75000) == 1 && BoredStep(true, 120000) == 2);
        CHECK(CallEveryMs(true, 1) == 7000 && CallEveryMs(true, 2) == 5000 && RoundsPerCall(true, 2) == 1);
        CHECK((kRoundMs + CallEveryMs(true, 2) - 1) / CallEveryMs(true, 2) == 3);
        // Heroic: the Shadowflame pools (25 s) are gone before the next Sweep, 27 s after they land (SP).
        std::uint32_t const loop = RoundCount(true) * CallEveryMs(true, 0);
        CHECK(loop == 40000);
        std::uint32_t const poolsLand = 2 * CallEveryMs(true, 0) + kShadowflameWarnMs;
        std::uint32_t const nextSweep = loop + CallEveryMs(true, 0) + kSweepWarnMs;
        CHECK(poolsLand + PoolMs(true) < nextSweep && nextSweep - poolsLand == 27000 + kSweepWarnMs);
    }

    void TestPicks()
    {
        // Dress Hunt: split over the healers in turn; no healer: the fallback; nobody: none.
        auto t = HuntTargets(6, { 11, 12 }, 99);
        CHECK(t.size() == 6 && std::count(t.begin(), t.end(), 11u) == 3 && std::count(t.begin(), t.end(), 12u) == 3);
        t = HuntTargets(3, {}, 99);
        CHECK(t.size() == 3 && t[0] == 99 && t[2] == 99);
        CHECK(HuntTargets(3, {}, 0).empty());

        // Thumbs Down: the lowest health percent among the non-victims (the second tank stays eligible).
        std::vector<CondemnCandidate> players{
            { 1, 20.f, 1000, true },        // Gyth's tank: never
            { 2, 40.f, 2000, false },       // the second tank (not a victim): eligible
            { 3, 55.f, 3000, false },
            { 4, 40.f, 1500, false },       // ties on percent: the lower health first
            { 5, 90.f, 4000, false },
        };
        auto c = PickCondemned(players, 1);
        CHECK(c.size() == 1 && c[0] == 4);
        c = PickCondemned(players, 2);
        CHECK(c.size() == 2 && c[0] == 4 && c[1] == 2);
        CHECK(PickCondemned({ { 1, 10.f, 10, true } }, 1).empty());
        // R-2 m-5: the second condemned stands 16 yd or more from the first (the next lowest that far); nobody that
        // far: the next lowest anyway.
        std::vector<CondemnCandidate> spread{
            { 1, 30.f, 1000, false, { 0.f, 0.f } },
            { 2, 35.f, 1000, false, { 5.f, 0.f } },     // next lowest, but 5 yd from the first
            { 3, 60.f, 1000, false, { 20.f, 0.f } },    // 20 yd away: picked second
            { 4, 50.f, 1000, false, { 10.f, 0.f } },    // 10 yd: too close
        };
        c = PickCondemned(spread, 2);
        CHECK(c.size() == 2 && c[0] == 1 && c[1] == 3);
        spread[2].at = { 8.f, 0.f };
        c = PickCondemned(spread, 2);
        CHECK(c.size() == 2 && c[0] == 1 && c[1] == 2);    // nobody 16 yd away: the next lowest
        CHECK(kCondemnedApartYd == 16.f && kCondemnedApartYd >= 2.f * kThumbsRadius);
        // The split: 30% each with 5, 37.5% with 4, 50% with 3; alone 150% (a lone condemned player dies).
        CHECK(Near(ThumbsSharePct(5), 30.f) && Near(ThumbsSharePct(4), 37.5f) && Near(ThumbsSharePct(3), 50.f));
        CHECK(Near(ThumbsSharePct(1), 150.f) && ThumbsSharePct(1) > 100.f && Near(ThumbsSharePct(0), 0.f));
        // Pools: a burn on entering, then every 2 s.
        CHECK(PoolBurnDue(false, 0) && !PoolBurnDue(true, 1999) && PoolBurnDue(true, 2000));
        CHECK(BannerDamage(1000, false) == 1000 && BannerDamage(1000, true) == 1250);
        CHECK(AcidDamage(1000, 0) == 1000 && AcidDamage(1000, 3) == 1300);

        // R-2 M-2: the rounds' owner fights the group (Gyth, then Rend on the floor); Nefarius only in between.
        CHECK(RoundOwnerFor(true, false) == RoundOwner::Gyth && RoundOwnerFor(true, true) == RoundOwner::Gyth);
        CHECK(RoundOwnerFor(false, true) == RoundOwner::Rend && RoundOwnerFor(false, false) == RoundOwner::Nefarius);
        // R-2 B-1: the entry door is shut only while the show runs (IN_PROGRESS); the kill opens it.
        CHECK(!EntryDoorOpen(kRendStateInProgress));
        CHECK(EntryDoorOpen(0) && EntryDoorOpen(2) && EntryDoorOpen(3));
        // R-2 M-1: aloft (no victim: passive) the tank he left holds, all hover long; on the ground his victim holds
        // only while he cannot breathe on it.
        CHECK(AcidHoldFor(true, 0, 42, true).on == 42 && AcidHoldFor(true, 0, 42, true).holding);
        CHECK(AcidHoldFor(true, 7, 42, false).on == 42);
        CHECK(AcidHoldFor(true, 0, 0, false).on == 0 && !AcidHoldFor(true, 0, 0, false).holding);
        CHECK(AcidHoldFor(false, 7, 42, true).on == 7 && !AcidHoldFor(false, 7, 42, true).holding);
        CHECK(AcidHoldFor(false, 7, 42, false).on == 7 && AcidHoldFor(false, 7, 42, false).holding);
        CHECK(!AcidHoldFor(false, 0, 42, false).holding);
        CHECK(kLandFallbackMs > 0 && kLandFallbackMs <= kAcidSwapEveryMs);
    }

    void TestSweep()
    {
        using namespace DungeonKit::Fronts;
        // The timing agrees with KT-B2's plan: over = warn + spacing x (walls - 1) + travel at the speed.
        CHECK(SweepOverMs(false) == kSweepWarnMs + WallOverMs(kSweepTravelYd, kSweepSpeed));
        CHECK(SweepOverMs(true) == kSweepWarnMs + kSweepSpacingMs + WallOverMs(kSweepTravelYd, kSweepSpeed));
        CHECK(SweepWalls(false) == 1 && SweepWalls(true) == 2);
        // About 10 s end to end (SP).
        CHECK(WallOverMs(kSweepTravelYd, kSweepSpeed) >= 10000 && WallOverMs(kSweepTravelYd, kSweepSpeed) <= 11000);
        // The wall reaches the way-in door: start x 194, 86 yd west lands on x 108.
        CHECK(Near(kSweepStartX - kSweepTravelYd, 108.f));

        // The gaps (rolling front ruling 3): 1,000 rolls, no pools: every gap inside the 40 yd strip, and the heroic
        // second gap on the other side within 20 yd of the first.
        WallFrame const frame{ { kSweepStartX, kSweepStartY }, DungeonKit::kPi, kSweepTravelYd, kSweepWidthYd };
        WallGapSpec gaps;
        gaps.gapYd = kSweepGapYd;
        gaps.spanYd = kSweepSpanYd;
        gaps.withinYd = kSweepWithinYd;
        std::uint32_t bad = 0;
        for (std::uint32_t i = 0; i < 1000; ++i)
        {
            std::array<float, 2> const rolls{ { static_cast<float>(i) / 1000.f, static_cast<float>((i * 7919u) % 1000u)
                / 1000.f } };
            std::vector<PoolCircle> const none;
            std::vector<GapPick> const picks = PlanWallGaps(frame, gaps, 2, std::span<PoolCircle const>(none),
                std::span<float const>(rolls));
            if (picks.size() != 2)
            {
                ++bad;
                continue;
            }
            for (GapPick const& p : picks)
                if (std::fabs(p.centre) + kSweepGapYd * 0.5f > kSweepSpanYd * 0.5f + 0.01f)
                    ++bad;
            if (!picks[1].keptSide || !picks[1].keptWithin || !SecondGapOk(picks[0].centre, picks[1].centre))
                ++bad;
        }
        CHECK(bad == 0);
        // A gap never on a live pool when one fits: a pool in the strip's north half pushes the gap south.
        std::vector<PoolCircle> const pool{ { { 150.f, -410.2f }, kShadowflameRadius } };
        std::array<float, 1> const roll{ { 0.9f } };
        std::vector<GapPick> const one = PlanWallGaps(frame, gaps, 1, std::span<PoolCircle const>(pool),
            std::span<float const>(roll));
        CHECK(one.size() == 1 && one[0].offPools);
        // The ice wall pieces: never in the gap, at most the cap.
        std::array<std::pair<float, float>, 1> const cut{ { { 6.f, kSweepGapYd } } };
        std::vector<float> const slots = WallCarrierSlots(kSweepWidthYd, kSweepCarrierSpacingYd,
            std::span<std::pair<float, float> const>(cut), kSweepCarrierMax);
        CHECK(!slots.empty() && slots.size() <= kSweepCarrierMax);
        for (float s : slots)
            CHECK(std::fabs(s - 6.f) >= kSweepGapYd * 0.5f);
        // Gyth hovers for the whole Sweep.
        CHECK(HoverMs(false) > SweepOverMs(false) && HoverMs(true) > SweepOverMs(true));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The taunt swaps at 10 against the user's rule (a tank taunts only with none of that boss's stacks; a trade takes
    // a boss whose debuff is gone from the taker), with the fight's real gaps: Gyth's Freezing Sweep hover (on the
    // round calls, the bored host included), Knock Away (the tank out of reach 2.5 s), the riderless breath's 2 s bar
    // (act 3, Gyth up); Rend's Whirlwind (2 s wind-up, 6 s whirl, a 1.5 s run back); the 1 s walk to a new tank after
    // a taunt; 8 s taunt cooldowns. Two tanks; one on Gyth from his arrival, the other picks Rend up when he lands.
    // 100 ms steps (the B14 model, both bosses).
    // ----------------------------------------------------------------------------------------------------------------
    struct SwapSetup
    {
        bool heroic = false;
        bool hold = true;                   // the B7 hold: the target's stacks hold while its boss cannot strike
        bool holdAloft = true;              // R-2 M-1: aloft (no victim) the tank Gyth left holds (AcidHoldFor)
        std::uint32_t gythDiesMs = 57000;   // SP tuning: Gyth's health at 5 (normal about 57 s, heroic about 72 s)
        std::uint32_t rendLandsMs = 57000;  // act 3: Gyth's death or the act 2 timer, whichever first
        std::uint32_t totalMs = 140000;
        std::uint32_t durationMs = kAcidMs; // both debuffs (the same 15 s)
        std::uint32_t tauntWalkMs = 1000;
        std::uint32_t knockOutMs = 2500;
        std::uint32_t whirlRunBackMs = 1500;
        std::uint32_t takeoffMs = 1500;
    };

    struct SwapResult
    {
        std::uint32_t strikes = 0;
        std::uint32_t lost = 0;             // a holder's stacks fell off below the count
        std::uint32_t swaps = 0;
        std::uint32_t trades = 0;
        std::uint32_t tauntsWithStacks = 0;
        std::uint32_t peak = 0;
        std::uint32_t waitMs = 0;           // a holder at or past the count with no legal taker
        std::uint32_t bothOnOneMs = 0;      // one tank holding both bosses (heroic)
        std::uint32_t maxGapMs = 0;         // the longest real gap between two strikes of one boss on one holder
        std::uint32_t sweeps = 0;
    };

    struct SimBoss
    {
        bool present = false;
        int victim = 0;
        std::array<std::uint32_t, 2> stacks{ { 0, 0 } };
        std::array<std::uint32_t, 2> expires{ { 0, 0 } };
        std::uint32_t nextStrike = 0;
        std::uint32_t downUntil = 0;        // cannot strike (hover, bar, whirl, the tank knocked away)
        std::uint32_t aloftUntil = 0;       // Gyth hovering: no victim (passive), the bots judge no swap on him
        std::uint32_t reachAt = 0;          // walking to a new tank
        std::uint32_t lastStrike = 0;
        bool struck = false;
    };

    SwapResult SimulateSwaps(SwapSetup const& f)
    {
        std::uint32_t constexpr kStep = 100;
        std::uint32_t constexpr kTauntCdMs = 8000;
        SwapResult r;
        std::array<SimBoss, 2> boss;        // 0 Gyth, 1 Rend
        std::array<std::uint32_t, 2> tauntReady{ { 0, 0 } };
        SimBoss& gyth = boss[0];
        SimBoss& rend = boss[1];
        gyth.present = true;
        gyth.victim = 0;
        gyth.nextStrike = kAcidSwapEveryMs;
        std::uint32_t nextCall = kRoundsFirstMs;
        std::uint32_t roundIndex = 0;
        std::uint32_t nextKnock = kKnockFirstMinMs;
        std::uint32_t nextBreath = 0;
        std::uint32_t nextWhirl = 0;

        auto holding = [&boss](int tank)
        {
            int n = 0;
            for (SimBoss const& b : boss)
                if (b.present && b.victim == tank)
                    ++n;
            return n;
        };
        auto taunt = [&](SimBoss& b, int tank, std::uint32_t t, bool trade)
        {
            if (b.stacks[tank])
                ++r.tauntsWithStacks;
            b.victim = tank;
            b.reachAt = t + f.tauntWalkMs;
            b.struck = false;
            tauntReady[tank] = t + kTauntCdMs;
            ++(trade ? r.trades : r.swaps);
        };

        for (std::uint32_t t = 0; t <= f.totalMs; t += kStep)
        {
            // The phases: Gyth until he dies, Rend from his landing (picked up by the tank holding nothing).
            if (gyth.present && t >= f.gythDiesMs)
                gyth.present = false;
            if (!rend.present && t >= f.rendLandsMs)
            {
                rend.present = true;
                rend.victim = gyth.present ? 1 - gyth.victim : gyth.victim;
                rend.nextStrike = t + kWoundsFirstMs;
                nextWhirl = t + kWhirlFirstMs;
                nextBreath = t + kRiderlessFirstMs;
            }
            std::uint32_t const act3 = rend.present ? t - f.rendLandsMs : 0;

            // The rounds: a Freezing Sweep call lifts Gyth for the hover (only while he lives).
            if (t >= nextCall)
            {
                std::uint8_t const step = BoredStep(f.heroic, act3);
                for (std::uint32_t k = 0; k < RoundsPerCall(f.heroic, step); ++k)
                    if (RoundAt(roundIndex++, f.heroic) == Round::FreezingSweep && gyth.present)
                    {
                        gyth.downUntil = std::max(gyth.downUntil, t + f.takeoffMs + HoverMs(f.heroic));
                        gyth.aloftUntil = std::max(gyth.aloftUntil, t + f.takeoffMs + HoverMs(f.heroic));
                        ++r.sweeps;
                    }
                nextCall = t + CallEveryMs(f.heroic, step);
            }
            if (gyth.present && t >= nextKnock)
            {
                gyth.downUntil = std::max(gyth.downUntil, t + f.knockOutMs);
                nextKnock = t + (kKnockEveryMinMs + kKnockEveryMaxMs) / 2;
            }
            if (gyth.present && rend.present && t >= nextBreath)
            {
                gyth.downUntil = std::max(gyth.downUntil, t + kRiderlessCastMs);
                nextBreath = t + kRiderlessEveryMs;
            }
            if (rend.present && t >= nextWhirl)
            {
                rend.downUntil = std::max(rend.downUntil, t + kWhirlWindupMs + kWhirlMs + f.whirlRunBackMs);
                nextWhirl = t + kWhirlEveryMs;
            }

            for (SimBoss& b : boss)
            {
                bool const canStrike = b.present && t >= b.downUntil && t >= b.reachAt;
                // The engine's path (boss_gyth_rework HoldAcid): aloft, his victim is empty and the remembered tank
                // (the holder, ids 1 / 2 here) holds; on the ground his victim holds while he cannot strike.
                bool const aloft = &b == &gyth && t < b.aloftUntil;
                std::uint64_t const tankId = static_cast<std::uint64_t>(b.victim) + 1;
                AcidHold const h = AcidHoldFor(aloft, aloft ? 0 : tankId, f.holdAloft ? tankId : 0, canStrike);
                if (f.hold && b.present && h.holding && h.on == tankId && b.stacks[b.victim])
                    b.expires[b.victim] += kStep;
                for (int k = 0; k < 2; ++k)
                    if (b.stacks[k] && t >= b.expires[k])
                    {
                        if (b.present && k == b.victim && b.stacks[k] < kSwapAt)
                            ++r.lost;
                        b.stacks[k] = 0;
                    }
                std::uint32_t const every = &b == &gyth ? kAcidSwapEveryMs : kWoundsEveryMs;
                if (canStrike && t >= b.nextStrike)
                {
                    ++b.stacks[b.victim];
                    b.expires[b.victim] = t + f.durationMs;
                    if (b.struck)
                        r.maxGapMs = std::max(r.maxGapMs, t - b.lastStrike);
                    b.struck = true;
                    b.lastStrike = t;
                    b.nextStrike = t + every;
                    ++r.strikes;
                    r.peak = std::max(r.peak, b.stacks[b.victim]);
                }
            }

            // The bots (MechanicTauntSwap.h): a boss whose holder is at the count goes to a tank with none of its
            // stacks and a ready taunt, a tank holding no swap boss first; a tank holding both gives one to a free tank
            // that has none of that boss's stacks (the most stacked on the holder first).
            for (SimBoss& b : boss)
            {
                // A boss on nobody (Gyth aloft) is not judged (MechanicTauntSwap.h).
                if (!b.present || b.stacks[b.victim] < kSwapAt || (&b == &gyth && t < b.aloftUntil))
                    continue;
                int const other = 1 - b.victim;
                if (b.stacks[other] == 0 && t >= tauntReady[other])
                    taunt(b, other, t, false);
                else
                    r.waitMs += kStep;
            }
            for (int tank = 0; tank < 2; ++tank)
            {
                if (holding(tank) < 2 || holding(1 - tank) != 0)
                    continue;
                int const free = 1 - tank;
                SimBoss* give = nullptr;
                for (SimBoss& b : boss)
                    if (b.present && b.victim == tank && b.stacks[free] == 0
                        && (!give || b.stacks[tank] > give->stacks[tank]) && !(&b == &gyth && t < b.aloftUntil))
                        give = &b;
                if (give && t >= tauntReady[free])
                    taunt(*give, free, t, true);
            }
            // Both bosses on one tank (aloft, Gyth has nobody: he lands on the tank he left, and a trade follows).
            if (gyth.present && rend.present && gyth.victim == rend.victim && t >= gyth.aloftUntil)
                r.bothOnOneMs += kStep;
        }
        return r;
    }

    void TestSwapTimeline()
    {
        SwapSetup normal;
        SwapResult const n = SimulateSwaps(normal);
        // R-2 M-1: the engine's first cut (the hold dropped while he had no victim aloft) lost stacks.
        SwapSetup dropAloft = normal;
        dropAloft.holdAloft = false;
        SwapResult const nDrop = SimulateSwaps(dropAloft);
        normal.hold = false;
        SwapResult const nLoose = SimulateSwaps(normal);

        SwapSetup heroic;
        heroic.heroic = true;
        heroic.gythDiesMs = 72000;          // SP: about 72 s of Gyth against a 60 s act: about 12 s two at once
        heroic.rendLandsMs = 60000;
        heroic.totalMs = 141000;            // Rend about 81 s
        SwapResult const h = SimulateSwaps(heroic);
        // The failing path (heroic, Gyth slow to die): two at once for a long stretch, the tanks trading.
        SwapSetup slow = heroic;
        slow.gythDiesMs = 130000;
        SwapResult const hs = SimulateSwaps(slow);
        SwapSetup slowDrop = slow;
        slowDrop.holdAloft = false;
        SwapResult const hsDrop = SimulateSwaps(slowDrop);
        slow.hold = false;
        SwapResult const hsLoose = SimulateSwaps(slow);

        std::printf("rend+gyth swaps, normal: strikes=%u swaps=%u lost=%u peak=%u wait=%ums maxgap=%ums sweeps=%u | "
            "no hold lost=%u\n", n.strikes, n.swaps, n.lost, n.peak, n.waitMs, n.maxGapMs, n.sweeps, nLoose.lost);
        std::printf("rend+gyth swaps, heroic: swaps=%u trades=%u lost=%u peak=%u wait=%ums both-on-one=%ums "
            "maxgap=%ums sweeps=%u\n", h.swaps, h.trades, h.lost, h.peak, h.waitMs, h.bothOnOneMs, h.maxGapMs,
            h.sweeps);
        std::printf("rend+gyth swaps, heroic two at once for 70 s: swaps=%u trades=%u lost=%u peak=%u wait=%ums "
            "both-on-one=%ums maxgap=%ums | no hold lost=%u\n", hs.swaps, hs.trades, hs.lost, hs.peak, hs.waitMs,
            hs.bothOnOneMs, hs.maxGapMs, hsLoose.lost);

        for (SwapResult const* r : { &n, &h, &hs })
        {
            CHECK(r->lost == 0);
            CHECK(r->tauntsWithStacks == 0);
            CHECK(r->swaps >= 3);
            CHECK(r->peak == kSwapAt);
            CHECK(r->waitMs == 0);
            CHECK(r->sweeps >= 1);
        }
        // The heroic overlap trades: the tank taking one boss gives the other away at once (a short both-on-one).
        // (R-2 M-1: with Gyth judged by nobody while aloft, the model runs the engine's path: fewer trades, still no
        // both-on-one time on the ground past the trade.)
        CHECK(hs.trades >= 1);
        CHECK(hs.bothOnOneMs <= 1000u * (hs.swaps + hs.trades));
        // The real gaps: a Sweep keeps Gyth off his tank past the debuff, so without the hold the holder drops stacks.
        CHECK(n.maxGapMs > kAcidMs && hs.maxGapMs > kAcidMs);
        CHECK(nLoose.lost > 0 && hsLoose.lost > 0);
        std::printf("rend+gyth swaps, hold dropped aloft (the R-2 M-1 bug): normal lost=%u heroic two at once "
            "lost=%u\n", nDrop.lost, hsDrop.lost);
        CHECK(nDrop.lost > 0 && hsDrop.lost > 0);
        // A debuff past the bound (3 x 8 s) breaks the taunt rule's timing: the holder waits at the count.
        SwapSetup longer = normal;
        longer.hold = true;
        longer.durationMs = 32000;
        CHECK(SimulateSwaps(longer).waitMs > 0);
    }

    void TestRoom()
    {
        // Every bay corner and the strip sit inside the leash arena; the balcony (Rend's and Nefarius's spawns) is not
        // in the room or the arena (Rend is engaged on the floor, S0 risk 8).
        for (auto const& box : { kWestBay, kMainStrip, kEastBay })
            for (Vec2 const& p : box)
                CHECK(RendGythArena().Contains(p, kFloorZ));
        CHECK(!RendGythArena().Contains(kRendSpawn.XY(), kRendSpawn.z));
        CHECK(!RendGythArena().Contains(kNefariusSpawn.XY(), kNefariusSpawn.z));
        CHECK(kRendSpawn.z > kRoomZMax && kNefariusSpawn.z > kRoomZMax);
        CHECK(InRoom(kStadiumTrigger.XY()) && InRoom(kGythHoverGround.XY()) && InRoom(kRendLanding));
        CHECK(RendGythArena().Contains(kStadiumTrigger.XY(), kStadiumTrigger.z));
        CHECK(ArenaFor(BOSS_REND).Contains(kGythHoverGround.XY(), kGythHoverGround.z));
        CHECK(ArenaFor(BOSS_GYTH).Contains(kRendLanding, kFloorZ));
        // The wall starts on the portcullis line, inside the room, and its 68 yd spans the bays.
        CHECK(InRoom({ kSweepStartX - 1.f, kSweepStartY }));
        CHECK(Near(kEastBay[2].y - kEastBay[0].y, 67.6f, 0.5f) && kSweepWidthYd >= kEastBay[2].y - kEastBay[0].y);
        CHECK(Near(kMainStrip[2].y - kMainStrip[0].y, 39.4f, 0.5f) && kSweepSpanYd <= 40.f);
        // The wave spots are behind the portcullis (x > 194), outside the arena.
        for (Vec2 const& p : kWaveSpots)
            CHECK(p.x > kSweepStartX && !RendGythArena().Contains(p, kWaveZ));
        // Nefarius is within insult range of the arena floor below his balcony.
        CHECK(DungeonKit::Distance(kNefariusSpawn.XY(), kStadiumTrigger.XY()) < kInsultRangeYd);
    }
}

int main()
{
    TestSlice();
    TestTexts();
    TestProgram();
    TestRounds();
    TestPicks();
    TestSweep();
    TestSwapTimeline();
    TestRoom();
    return Report("brs_rend_gyth_test");
}
