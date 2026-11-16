// Host tests for HalyconGizrulLogic.h (B7: Halycon and Gizrul). The slice and arena checks are WP-S0's; the rest is
// WP-B7's: the spells, the counts, the Pack Fury clock, the charge plan (and its reading of HG3 against the G1 drill),
// the charge lines in the den, Rabies' tick skipper, Torn Hide against the user's taunt rule (a two-tank, two-wolf
// simulation of the bots' swap and trade rules), and Rabid Trail's puddles and space math.
#include "HalyconGizrulLogic.h"
#include "check.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <set>

using namespace BlackrockSpireRework;
using namespace BrsHalyconGizrul;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndArena()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210210 && kSpellSlice.last == 210249);
        std::set<std::uint32_t> ids;
        for (std::uint32_t id : { SPELL_HG_SAVAGE_CHARGE, SPELL_HG_PACK_POUNCE, SPELL_HG_THRASH, SPELL_HG_RABID_FROTH,
            SPELL_HG_RABID_TRAIL, SPELL_HG_RABIES, SPELL_HG_CALL_OF_THE_PACK, SPELL_HG_PACK_FURY,
            SPELL_HG_BLOODIED_PACK, SPELL_HG_GRIEF, SPELL_HG_TORN_HIDE, SPELL_HG_CHARGE_BAR, SPELL_HG_THRASH_BAR,
            SPELL_HG_FROTH_BAR, SPELL_HG_CHARGE_LOOK, SPELL_HG_LEAP_LOOK, SPELL_HG_MAUL_LOOK, SPELL_HG_WHIRL_LOOK,
            SPELL_HG_FROTH_LOOK, SPELL_HG_SPRINT, SPELL_HG_TRAIL_PUDDLE })
        {
            CHECK(id >= kSpellSlice.first && id <= kSpellSlice.last);
            ids.insert(id);
        }
        CHECK(ids.size() == 21);
        CHECK(kLastSpell == 210230);

        // Both wolves on their stock slots (Halycon 7, Gizrul 6), one script.
        CHECK(BossOfEntry(NPC_HALYCON) == std::optional<std::uint32_t>(BOSS_HALYCON));
        CHECK(BossOfEntry(NPC_GIZRUL) == std::optional<std::uint32_t>(BOSS_GIZRUL));

        // She spawns kHalyconSpawn, inside the arena.
        CHECK(HalyconGizrulArena().Contains(kHalyconSpawn.XY(), kHalyconSpawn.z));
        CHECK(ArenaFor(BOSS_HALYCON).Contains(kHalyconSpawn.XY(), kHalyconSpawn.z));
        // Gizrul runs in from his level (outside) to the den mouth (inside): he is engaged only at the mouth.
        CHECK(!HalyconGizrulArena().Contains(kGizrulSpawn.XY(), kGizrulSpawn.z));
        CHECK(HalyconGizrulArena().Contains(kHalyconDenMouth, 64.f));
        CHECK(ArenaFor(BOSS_GIZRUL).Contains(kHalyconDenMouth, 64.f));
        // The run: spawn to the ramp foot plus path 402450 is about 81 yd; at his 10 yd/s doubled, about 4 s.
        float const ramp = DungeonKit::Distance(kGizrulSpawn.XY(), Vec2{ -166.797f, -381.557f });
        float const path = 11.25f + 13.96f + 14.88f + 12.75f + 5.75f;     // the five legs [db: waypoint_data 402450]
        float const runSpeed = 7.f * 1.42857f * (1.f + kSprintSpeedPct / 100.f);
        CHECK(Near((ramp + path) / runSpeed * 1000.f, static_cast<float>(kGizrulArriveMs), 500.f));
        CHECK(kGizrulRunTimeoutMs > kGizrulArriveMs * 2);
        CHECK(kSprintMs > kGizrulArriveMs);
    }

    void TestCountsAndTuning()
    {
        // HG2: one line at 5 players, two at 6 or more (ruling 8).
        CHECK(kChargeLines.At(0) == 1 && kChargeLines.At(5) == 1);
        for (std::uint32_t n = 6; n <= 10; ++n)
            CHECK(kChargeLines.At(n) == 2);
        // HG3: normal the first line only, heroic every line.
        CHECK(PounceOn(0, false) && !PounceOn(1, false));
        CHECK(PounceOn(0, true) && PounceOn(1, true));
        // SP's numbers; heroic hits under 50% (the 2026-11-01 rule).
        CHECK(kChargePct(false) == 30.f && kChargePct(true) == 40.f);
        CHECK(kPouncePct(false) == 25.f && kPouncePct(true) == 30.f);
        CHECK(kThrashPct(false) == 25.f && kThrashPct(true) == 30.f);
        CHECK(kFrothPct(false) == 20.f && kFrothPct(true) == 25.f);
        CHECK(kRabiesPctPerStack(false) == 1.f && kRabiesPctPerStack(true) == 1.5f);
        CHECK(kGriefDamagePct(false) == 25 && kGriefDamagePct(true) == 40);
        for (float pct : { kChargePct(true), kPouncePct(true), kThrashPct(true), kFrothPct(true) })
            CHECK(pct < 50.f);
        // A charge line and its pounce together: 55% normal (SP: "survivable at full"), 70% heroic.
        CHECK(kChargePct(false) + kPouncePct(false) == 55.f);
        // The rings alternate every 10 s (Thrash 10, 30, 50 s; Froth 20, 40, 60 s).
        CHECK(kThrashFirstMs == 10000 && kThrashEveryMs == 20000 && kFrothFirstMs == 20000 && kFrothEveryMs == 20000);
        CHECK(kFrothFirstMs - kThrashFirstMs == kThrashEveryMs / 2);
        CHECK(kCallFirstMs == 15000 && kCallEveryMs == 25000 && kCallCastMs == 3000 && kPackFuryMs == 15000);
        CHECK(kCallKickPriorityHeroic > kCallKickPriorityNormal);
        CHECK(kBloodiedPackMax == 5 && kBloodiedPackDamagePct == 10 && kRabiesMaxStacks == 5);
    }

    void TestFuryClock()
    {
        CHECK(FuryStep(100, false) == 100 && FuryStep(100, true) == 150);
        // 18 s becomes 12 s under Pack Fury.
        Cooldown c;
        CHECK(!c.Armed() && !c.Due());
        c.Arm(kChargeEveryMs);
        std::uint32_t wall = 0;
        while (!c.Due())
        {
            c.Advance(100, true);
            wall += 100;
        }
        CHECK(wall == 12000);
        c.Arm(kChargeEveryMs);
        wall = 0;
        while (!c.Due())
        {
            c.Advance(100, false);
            wall += 100;
        }
        CHECK(wall == kChargeEveryMs);
        // Half and half: 9 s normal, then the rest at 1.5x (6 s).
        c.Arm(kChargeEveryMs);
        for (int i = 0; i < 90; ++i)
            c.Advance(100, false);
        CHECK(c.Left() == 9000);
        wall = 0;
        while (!c.Due())
        {
            c.Advance(100, true);
            wall += 100;
        }
        CHECK(wall == 6000);
        c.Disarm();
        c.Advance(100000, true);
        CHECK(!c.Due() && c.Left() == Cooldown::kNever);
        // Torn Hide's bite: 6 s, 4 s under the fury.
        CHECK(TornHideBiteMs(false) == 6000 && TornHideBiteMs(true) == 4000);
    }

    void TestChargePlan()
    {
        // Line 0: registered at 0, the paw 3 s, the dash 0.75 s, the pounce 1.5 s later.
        CHECK(ChargePlan::RegisterMs(0) == 0 && ChargePlan::ResolveMs(0) == 3000);
        CHECK(ChargePlan::ArriveMs(0) == 3750 && ChargePlan::PounceLandMs(0) == 5250);
        CHECK(ChargePlan::LeapStartMs(0) == 4250);
        // Line 1 (6+): 1 s apart.
        CHECK(ChargePlan::RegisterMs(1) == 1000 && ChargePlan::ResolveMs(1) == 4000);
        CHECK(ChargePlan::ResolveMs(1) - ChargePlan::ResolveMs(0) == kChargeGapMs);
        CHECK(ChargePlan::PounceLandMs(1) == 6250);
        // The second dash starts after the first one ended (he is at line 0's end, its start).
        CHECK(ChargePlan::ArriveMs(0) <= ChargePlan::ResolveMs(1));
        // Heroic: she leaps from line 0's end to line 1's within the 1 s between the landings.
        CHECK(ChargePlan::LeapStartMs(1) >= ChargePlan::PounceLandMs(0));
        // The circle is drawn with the line (SP's reading of HG3): its warning is the paw + the dash + 1.5 s.
        CHECK(ChargePlan::PounceWarnMs() == ChargePlan::PounceLandMs(0) - ChargePlan::RegisterMs(0));
        CHECK(ChargePlan::PounceWarnMs() == 5250);
        // The G1 drill (tag 4) registers the circle at the charge's resolve with a 1.5 s warning: stricter. Built:
        // SP's reading; the circle is on the floor 3.75 s before the drill's.
        std::uint32_t const drillWarnMs = kPounceDelayMs;
        CHECK(ChargePlan::PounceWarnMs() - drillWarnMs == kPawMs + kChargeTravelMs);
        // He holds at the end until the last pounce lands, else 1.5 s.
        CHECK(ChargePlan::ReturnMs(1, true) == 5250 && ChargePlan::ReturnMs(1, false) == 3750 + kHoldNoPounceMs);
        CHECK(ChargePlan::ReturnMs(2, true) == 6250 && ChargePlan::ReturnMs(2, false) == 4750 + kHoldNoPounceMs);
        // A charge cycle under Pack Fury (12 s) still ends before the next starts.
        CHECK(ChargePlan::ReturnMs(2, true) < kChargeEveryMs * 2 / 3);
        // Halycon's casts wait for a pounce that takes off during them; one queued mid-cast takes off after it.
        CHECK(ChargePlan::LeapStartMs(0) > kCallCastMs && ChargePlan::LeapStartMs(0) > kThrashWarnMs);
    }

    void TestChargeReach()
    {
        Arena const arena = HalyconGizrulArena();
        float const z = 64.5f;
        // Every line stays in [6, 30] and its end on the arena (R-1-B m5: also the short ones, which turn toward open
        // floor instead of crossing the wall).
        int clipped = 0;
        int turned = 0;
        for (Vec2 from : { kHalyconSpawn.XY(), kHalyconDenMouth, Vec2{ -189.8f, -324.2f }, Vec2{ -192.f, -345.f } })
            for (int deg = 0; deg < 360; deg += 15)
            {
                float const facing = static_cast<float>(deg) * DungeonKit::kPi / 180.f;
                ChargeAim const aim = AimCharge(arena, from, z, facing);
                CHECK(aim.length >= kChargeMinYd && aim.length <= kChargeLength);
                CHECK(aim.length == ChargeReach(arena, from, z, facing));
                for (float d = 0.5f; d <= aim.length; d += 0.5f)
                    CHECK(arena.Contains(DungeonKit::Advance(from, aim.facing, d), z));
                if (aim.length < kChargeLength)
                    ++clipped;
                if (aim.facing != facing)
                {
                    ++turned;
                    CHECK(ArenaReach(arena, from, z, facing) < kChargeMinYd);
                }
            }
        CHECK(clipped > 0);
        CHECK(turned > 0);
        // From the den's mouth east and south into the hall: the line runs on (the union of both regions).
        float const intoHall = ChargeReach(arena, kHalyconDenMouth, z, DungeonKit::BearingTo(kHalyconDenMouth,
            Vec2{ -167.f, -360.f }));
        CHECK(intoHall >= 25.f);
        // Across the den (along x) a line is wall to wall, well under 30 yd (the den is 20 yd wide at y -330).
        float const across = ChargeReach(arena, Vec2{ -200.f, -330.f }, z, 0.f);
        CHECK(across < 25.f);
        // From Halycon's spot (2.2 yd from the west wall) toward the wall: the floor that way is 1.2 yd, so the line
        // turns (the nearest turn with 6 yd of floor) and stays on the arena.
        CHECK(ArenaReach(arena, kHalyconSpawn.XY(), z, DungeonKit::kPi) < kChargeMinYd);
        ChargeAim const wall = AimCharge(arena, kHalyconSpawn.XY(), z, DungeonKit::kPi);
        CHECK(wall.facing != DungeonKit::kPi && wall.length >= kChargeMinYd);
        CHECK(arena.Contains(DungeonKit::Advance(kHalyconSpawn.XY(), wall.facing, wall.length), z));
        // Off the arena there is no floor anywhere: the old minimum along the facing.
        ChargeAim const off = AimCharge(arena, Vec2{ 0.f, 0.f }, z, 1.f);
        CHECK(off.facing == 1.f && off.length == kChargeMinYd);
    }

    void TestRabies()
    {
        // Every 1.5 s tick without the fury: ticks 2, 4, 6 deal (every 3 s); with it every tick (every 1.5 s).
        CHECK(!RabiesTickDeals(1, false) && RabiesTickDeals(2, false) && !RabiesTickDeals(3, false));
        CHECK(RabiesTickDeals(1, true) && RabiesTickDeals(2, true));
        int dealt = 0;
        int dealtFury = 0;
        for (std::uint32_t tick = 1; tick <= kRabiesMs / kRabiesAmplitudeMs; ++tick)
        {
            dealt += RabiesTickDeals(tick, false) ? 1 : 0;
            dealtFury += RabiesTickDeals(tick, true) ? 1 : 0;
        }
        CHECK(dealt == 10 && dealtFury == 20);      // 30 s: 10 ticks, twice as many under Pack Fury

        // R-1-B M2: a new stack restarts the engine's tick number (the periodic timer runs on). A heroic Rabid Trail
        // adds a stack every 2 s while the aura ticks every 1.5 s: 30 s in the trail.
        std::uint32_t engineDealt = 0;
        std::uint32_t ownDealt = 0;
        std::uint32_t engineTick = 0;
        RabiesTicker ticker;
        for (std::uint32_t t = 100; t <= 30000; t += 100)
        {
            if (t % kTrailTickMs == 0)
                engineTick = 0;                     // Aura::RefreshTimers -> CalculatePeriodic(load = false)
            if (t % kRabiesAmplitudeMs == 0)
            {
                ++engineTick;
                engineDealt += RabiesTickDeals(engineTick, false) ? 1 : 0;
                ownDealt += ticker.Next(false) ? 1 : 0;
            }
        }
        std::printf("rabies: 30 s in a trail, ticks dealt by the engine's tick number %u, by the script's own %u\n",
            engineDealt, ownDealt);
        CHECK(ownDealt == 10);                      // every 3 s, whatever the refreshes
        CHECK(engineDealt < ownDealt * 2 / 3);      // the old skipper: about a third of a tick per 2 s
        // Under Pack Fury every tick deals; the parity carries on after it.
        RabiesTicker fury;
        CHECK(fury.Next(true) && fury.Next(true) && fury.Next(true));
        CHECK(fury.Next(false) && !fury.Next(false) && fury.Next(false));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Torn Hide against the user's taunt rule (R-1 ruling 2): a model of the fight's own timers at 10 players (two
    // charge lines), with the downtime that keeps a wolf from biting: Gizrul's charge (the paw, two dashes, the hold
    // until the last pounce lands, the run back), Halycon's pounces (take-off to landing, 0.5 s recover, the run back),
    // the cast bars (Thrash, Froth, Call of the Pack), Pack Fury's 1.5x clock, and the walk to a new tank after a
    // taunt. The bots' rules (MechanicTauntSwap.h): swap when the holder is at the count and the taker has none of
    // that wolf's stacks; a tank holding both wolves gives one to the free tank whose stacks of it are gone. 100 ms
    // ticks, 8 s taunt cooldowns.
    // ----------------------------------------------------------------------------------------------------------------
    enum class Fury : std::uint8_t
    {
        None,       // no howl lands (kicked every time)
        Always,     // the worst case: every timer at 1.5x all fight
        Calls,      // the howls land: 15 s of fury from each (the mixed case)
    };

    struct FightSetup
    {
        bool halycon = true;            // up at the pull
        bool gizrul = true;             // arrives at kGizrulArriveMs
        bool heroic = true;
        Fury fury = Fury::Calls;
        std::uint32_t runBackMs = 1500; // back in reach after a charge or a pounce
        std::uint32_t tauntWalkMs = 1000;
        bool hold = true;               // the fix: Torn Hide holds on the target while its wolf cannot bite
        std::uint32_t normalMs = TornHideMs(false);
        std::uint32_t furyMs = TornHideMs(true);
        std::uint32_t totalMs = 180000;
    };

    struct WolfResult
    {
        std::uint32_t bites = 0;
        std::uint32_t reached = 0;          // the holder reached the count
        std::uint32_t early = 0;            // ... while the other tank still carried this wolf's stacks
        std::uint32_t lost = 0;             // the holder's stacks fell off below the count (the M1 symptom)
        std::uint32_t swaps = 0;            // taunts at the count (trades not counted)
        std::uint32_t tauntsWithStacks = 0;
        std::uint32_t peak = 0;
        std::uint32_t waitMs = 0;           // a holder at or past the count with no legal taker
        std::uint32_t maxWaitMs = 0;
    };

    struct FightResult
    {
        std::array<WolfResult, 2> wolf;     // 0 Halycon, 1 Gizrul
        std::uint32_t trades = 0;
    };

    FightResult SimulateFight(FightSetup const& f)
    {
        std::uint32_t constexpr kStep = 100;
        std::uint32_t constexpr kTauntCdMs = 8000;
        std::uint32_t constexpr kLines = 2;
        struct Wolf
        {
            bool up = false;
            bool lone = false;
            int holder = 0;
            Cooldown charge, call, thrash, froth, bite;
            std::uint32_t castEnd = 0, busyEnd = 0, reachAt = 0, wait = 0;
            std::array<std::uint32_t, 2> stacks{ { 0, 0 } };
            std::array<std::uint32_t, 2> expires{ { 0, 0 } };
        };
        struct Leap
        {
            std::uint32_t at;
            std::uint32_t busyUntil;
        };
        FightResult r;
        std::array<Wolf, 2> w;
        std::vector<Leap> leaps;            // Halycon's pending pounces
        std::array<std::uint32_t, 2> tauntReady{ { 0, 0 } };
        std::uint32_t furyEnd = 0;
        std::uint32_t callLands = 0;
        bool const gizrulLone = f.gizrul && !f.halycon;
        bool const halyconLone = f.halycon && !f.gizrul;

        if (f.halycon)
        {
            Wolf& h = w[0];
            h.up = true;
            h.lone = halyconLone;
            h.thrash.Arm(kThrashFirstMs);
            h.call.Arm(kCallFirstMs);
            h.bite.Arm(kTornHideBiteFirstMs);
            if (halyconLone)
                h.charge.Arm(kGizrulArriveMs);
        }
        auto leapSoon = [&](std::uint32_t t, std::uint32_t window)
        {
            for (Leap const& l : leaps)
                if (l.at > t && l.at <= t + window)
                    return true;
            return false;
        };
        auto taunt = [&](int wolf, int tank, std::uint32_t t, bool trade)
        {
            if (w[wolf].stacks[tank])
                ++r.wolf[wolf].tauntsWithStacks;
            w[wolf].holder = tank;
            w[wolf].reachAt = t + f.tauntWalkMs;
            tauntReady[tank] = t + kTauntCdMs;
            if (trade)
                ++r.trades;
            else
                ++r.wolf[wolf].swaps;
        };

        for (std::uint32_t t = 0; t <= f.totalMs; t += kStep)
        {
            if (f.fury == Fury::Calls && callLands && t >= callLands)
            {
                callLands = 0;
                furyEnd = t + kPackFuryMs;
            }
            bool const fury = f.fury == Fury::Always || t < furyEnd;
            if (f.gizrul && !w[1].up && t >= kGizrulArriveMs)
            {
                Wolf& g = w[1];
                g.up = true;
                g.lone = gizrulLone;
                g.holder = w[0].up ? w[0].holder : 0;     // he engages on Halycon's tank
                g.charge.Arm(0);
                g.froth.Arm(t + kFrothMinFirstMs < kFrothFirstMs ? kFrothFirstMs - t : kFrothMinFirstMs);
                g.bite.Arm(kTornHideBiteFirstMs);
                if (gizrulLone)
                    g.call.Arm(kCallFirstMs - t);
            }
            for (Wolf& x : w)
                if (x.up && t > 0)
                {
                    x.charge.Advance(kStep, fury);
                    x.thrash.Advance(kStep, fury);
                    x.froth.Advance(kStep, fury);
                    x.bite.Advance(kStep, fury);
                    x.call.Advance(kStep, false);
                }
            for (Leap const& l : leaps)
                if (t >= l.at)
                    w[0].busyEnd = std::max(w[0].busyEnd, l.busyUntil);
            leaps.erase(std::remove_if(leaps.begin(), leaps.end(), [t](Leap const& l) { return t >= l.at; }),
                leaps.end());

            for (int i = 0; i < 2; ++i)
            {
                Wolf& x = w[i];
                if (!x.up)
                    continue;
                bool const canBite = t >= x.castEnd && t >= x.busyEnd && t >= x.reachAt;
                if (f.hold && !canBite && x.stacks[x.holder])
                    x.expires[x.holder] += kStep;
                for (int k = 0; k < 2; ++k)
                    if (x.stacks[k] && t >= x.expires[k])
                    {
                        if (k == x.holder && x.stacks[k] < kTornHideSwapAt)
                            ++r.wolf[i].lost;
                        x.stacks[k] = 0;
                    }
            }

            // The AIs' RunTimers, in their order; a move that starts ends the wolf's turn.
            for (int i = 0; i < 2; ++i)
            {
                Wolf& x = w[i];
                if (!x.up)
                    continue;
                bool const halycon = i == 0;
                bool const casting = t < x.castEnd;
                bool const busy = t < x.busyEnd;
                bool const charger = !halycon || x.lone;
                if (charger && x.charge.Due() && !casting && !busy && !(halycon && leapSoon(t, kPawMs)))
                {
                    x.charge.Arm(kChargeEveryMs);
                    x.castEnd = t + kPawMs;
                    if (halycon)    // a lone Halycon Thrashes where the charge ends, then runs back
                        x.busyEnd = t + std::max(ChargePlan::ReturnMs(kLines, false),
                            ChargePlan::ArriveMs(kLines - 1) + kThrashWarnMs) + f.runBackMs;
                    else
                    {
                        std::uint32_t const lastPounce = f.heroic ? kLines - 1 : 0;
                        bool const pounces = w[0].up && !w[0].lone;
                        x.busyEnd = t + ChargePlan::ReturnMs(kLines, pounces && PounceOn(kLines - 1, f.heroic))
                            + f.runBackMs;
                        if (pounces)
                            leaps.push_back({ t + ChargePlan::LeapStartMs(0),
                                t + ChargePlan::PounceLandMs(lastPounce) + kPounceRecoverMs + f.runBackMs });
                    }
                    continue;
                }
                bool const howler = halycon ? true : x.lone;
                if (howler && x.call.Due() && !casting && !busy
                    && !(halycon && leapSoon(t, kCallCastMs + kPounceClearMs)))
                {
                    x.call.Arm(kCallEveryMs);
                    x.castEnd = t + kCallCastMs;
                    callLands = t + kCallCastMs;
                    continue;
                }
                if (halycon && x.thrash.Due() && !casting && !busy && !leapSoon(t, kThrashWarnMs + kPounceClearMs))
                {
                    x.thrash.Arm(kThrashEveryMs);
                    x.castEnd = t + kThrashWarnMs;
                    continue;
                }
                if (!halycon && x.froth.Due() && !casting && !busy)
                {
                    x.froth.Arm(kFrothEveryMs);
                    x.castEnd = t + kFrothWarnMs;
                    continue;
                }
                if (x.bite.Due() && !casting && !busy && t >= x.reachAt)
                {
                    int const h = x.holder;
                    ++x.stacks[h];
                    x.expires[h] = t + (fury ? f.furyMs : f.normalMs);
                    x.bite.Arm(kTornHideBiteEveryMs);
                    WolfResult& wr = r.wolf[i];
                    ++wr.bites;
                    wr.peak = std::max(wr.peak, x.stacks[h]);
                    if (x.stacks[h] == kTornHideSwapAt)
                    {
                        ++wr.reached;
                        if (x.stacks[1 - h])
                            ++wr.early;
                    }
                }
            }

            // The bots: swap at the count, then a trade when one tank holds both.
            for (int i = 0; i < 2; ++i)
            {
                Wolf& x = w[i];
                if (!x.up)
                    continue;
                int const other = 1 - x.holder;
                if (x.stacks[x.holder] >= kTornHideSwapAt && !x.stacks[other] && t >= tauntReady[other])
                    taunt(i, other, t, false);
            }
            if (w[0].up && w[1].up && w[0].holder == w[1].holder)
            {
                int const busyTank = w[0].holder;
                int const freeTank = 1 - busyTank;
                int give = -1;
                for (int i = 0; i < 2; ++i)
                    if (!w[i].stacks[freeTank] && (give < 0 || w[i].stacks[busyTank] > w[give].stacks[busyTank]))
                        give = i;
                if (give >= 0 && t >= tauntReady[freeTank])
                    taunt(give, freeTank, t, true);
            }
            for (int i = 0; i < 2; ++i)
            {
                Wolf& x = w[i];
                if (!x.up)
                    continue;
                x.wait = x.stacks[x.holder] >= kTornHideSwapAt ? x.wait + kStep : 0;
                if (x.wait)
                    r.wolf[i].waitMs += kStep;
                r.wolf[i].maxWaitMs = std::max(r.wolf[i].maxWaitMs, x.wait);
            }
        }
        return r;
    }

    void PrintFight(char const* name, FightResult const& r)
    {
        std::printf("torn hide %-34s", name);
        for (int i = 0; i < 2; ++i)
        {
            WolfResult const& x = r.wolf[i];
            if (!x.bites)
                continue;
            std::printf(" | %s bites=%u at3=%u early=%u lost=%u swaps=%u peak=%u wait=%u/%ums", i ? "giz" : "hal",
                x.bites, x.reached, x.early, x.lost, x.swaps, x.peak, x.maxWaitMs, x.waitMs);
        }
        std::printf(" | trades=%u\n", r.trades);
    }

    void TestTornHide()
    {
        // R-1 ruling 2: SP's 15 s at the 6 s bite, about 10-11 s under Pack Fury's 4 s bite; the bound is D < 3I.
        CHECK(TornHideMs(false) == 15000 && TornHideMs(true) == 10000);
        CHECK(TornHideFallsOffInTime(6000, 17900, 3) && !TornHideFallsOffInTime(6000, 18000, 3));
        CHECK(TornHideFallsOffInTime(4000, 11000, 3) && !TornHideFallsOffInTime(4000, 12000, 3));
        CHECK(TornHideStacks(TornHideBiteMs(true), TornHideMs(true)));
        CHECK(TornHideMs(true) > TornHideBiteMs(false));    // a fury stack bridges a normal bite
        // The hold is applied a second at a time, or at once before the aura would run out.
        CHECK(!TornHideHoldDue(300, 8000) && TornHideHoldDue(1000, 8000));
        CHECK(TornHideHoldDue(200, 600) && !TornHideHoldDue(200, 800));

        // Each wolf alone (the other fell first), so its own stacks drive every swap, at both bite rates and every
        // run back up to 3 s (30 yd for Gizrul, 24 for Halycon).
        for (Fury const fury : { Fury::None, Fury::Always, Fury::Calls })
            for (std::uint32_t runBack : { 0u, 1500u, 3000u })
                for (bool const gizrul : { false, true })
                {
                    FightSetup s;
                    s.halycon = !gizrul;
                    s.gizrul = gizrul;
                    s.fury = fury;
                    s.runBackMs = runBack;
                    FightResult const r = SimulateFight(s);
                    WolfResult const& x = r.wolf[gizrul ? 1 : 0];
                    CHECK(x.lost == 0);                 // the stacks always build to the count
                    CHECK(x.reached >= 4);              // ... several times in 3 min
                    CHECK(x.swaps >= 4);
                    CHECK(x.tauntsWithStacks == 0);     // the user's rule holds in the model itself
                    CHECK(x.peak <= kTornHideSwapAt + 1);
                    if (fury != Fury::Calls)
                    {
                        // One bite rate all fight: the old holder is always clear before the new one's third stack.
                        CHECK(x.early == 0);
                        CHECK(x.waitMs == 0);
                    }
                    else
                        // Pack Fury landing right after a swap: the old holder's normal 15 s stack against the new
                        // holder's 4 s bites keeps the new holder at 3 for at most 15 - 3 x 4 = 3 s.
                        CHECK(x.maxWaitMs <= TornHideMs(false) - kTornHideSwapAt * TornHideBiteMs(true));
                    if (runBack == 1500 && fury != Fury::None)
                        PrintFight(gizrul ? (fury == Fury::Always ? "gizrul alone, always fury" : "gizrul alone, calls")
                            : (fury == Fury::Always ? "halycon alone, always fury" : "halycon alone, calls"), r);
                }

        // The pair (heroic and normal pounces): Halycon's stacks build and drive the swaps; each of her swaps lands
        // on the tank holding Gizrul and the trade moves him too, so his stacks rarely reach the count there (the
        // tank never carries more than his count either way).
        for (Fury const fury : { Fury::None, Fury::Always, Fury::Calls })
            for (std::uint32_t runBack : { 0u, 1500u, 3000u })
                for (bool const heroic : { false, true })
                {
                    FightSetup s;
                    s.fury = fury;
                    s.runBackMs = runBack;
                    s.heroic = heroic;
                    FightResult const r = SimulateFight(s);
                    for (WolfResult const& x : r.wolf)
                    {
                        CHECK(x.tauntsWithStacks == 0);
                        CHECK(x.peak <= kTornHideSwapAt + 1);
                        if (fury != Fury::Calls)
                            CHECK(x.early == 0 && x.waitMs == 0);
                        else
                            CHECK(x.maxWaitMs <= TornHideMs(false) - kTornHideSwapAt * TornHideBiteMs(true));
                    }
                    CHECK(r.wolf[0].lost == 0 && r.wolf[1].lost == 0);
                    CHECK(r.wolf[0].reached >= 4);
                    CHECK(r.trades >= 4);
                    if (runBack == 1500 && heroic)
                        PrintFight(fury == Fury::None ? "pair, no fury" : (fury == Fury::Always
                            ? "pair, always fury" : "pair, calls"), r);
                }

        // The negative control (the R-1-B M1 finding): without the hold the debuff runs down while a wolf is away,
        // and a lone Gizrul under Pack Fury (12 s cycle, about 9 s away) loses his stacks before the count at any
        // duration under 3I; the old 10 s / 7 s pair loses them too.
        {
            FightSetup s;
            s.halycon = false;
            s.fury = Fury::Always;
            s.hold = false;
            FightResult const noHold = SimulateFight(s);
            PrintFight("gizrul alone, always fury, no hold", noHold);
            CHECK(noHold.wolf[1].lost > 0);
            CHECK(noHold.wolf[1].reached == 0);
            s.furyMs = 3 * TornHideBiteMs(true) - 100;  // the longest duration the bound allows
            CHECK(SimulateFight(s).wolf[1].reached == 0);
            FightSetup old;
            old.halycon = false;
            old.hold = false;
            old.fury = Fury::None;
            old.normalMs = 10000;
            old.runBackMs = 3000;
            CHECK(SimulateFight(old).wolf[1].lost > 0);
        }

        // The damage: +10% per stack, from that wolf only.
        CHECK(TornHideDamage(1000, 0) == 1000 && TornHideDamage(1000, 3) == 1300 && TornHideDamage(999, 1) == 1098);
    }

    void TestTrail()
    {
        // Puddles every 8 yd from 4 yd in: a 30 yd trail 4, a 6 yd one 1, none past the end.
        Vec2 const a{ 0.f, 0.f };
        std::vector<Vec2> const full = TrailPuddles(a, Vec2{ 30.f, 0.f });
        CHECK(full.size() == 4);
        CHECK(Near(full.front().x, 4.f) && Near(full.back().x, 28.f));
        CHECK(TrailPuddles(a, Vec2{ 6.f, 0.f }).size() == 1);
        for (Vec2 const& p : full)
            CHECK(p.x <= 30.f + 0.01f);
        CHECK(TrailPuddles(a, a).size() == 1);

        // Trails at once (SP: at most 2 at 5 players, 4 at 6 or more for under 3 s).
        CHECK(TrailsAtOnce(1, false) == 1 && TrailsAtOnce(1, true) == 2);
        CHECK(TrailsAtOnce(2, false) == 2 && TrailsAtOnce(2, true) == 4);
        float const line = TrailSqYd(kChargeLength);
        CHECK(Near(line, 150.f));
        float const worst5 = TrailsAtOnce(1, true) * line;
        float const worst10 = TrailsAtOnce(2, true) * line;
        std::printf("rabid trail: 5p up to %.0f sq yd (%.0f%% of the den, %.0f%% with the hall's west half); 6+ up "
            "to %.0f (%.0f%%, %.0f%%); 6+ outside Pack Fury %.0f (%.0f%%)\n", worst5, 100.f * worst5 / kDenSqYd,
            100.f * worst5 / kDenAndHallSqYd, worst10, 100.f * worst10 / kDenSqYd, 100.f * worst10 / kDenAndHallSqYd,
            2 * line, 100.f * 2 * line / kDenSqYd);
        CHECK(worst5 / kDenSqYd < 0.5f);            // 5 players: under half the den
        CHECK(worst10 / kDenSqYd > 0.75f);          // 6+ under Pack Fury: most of the den (the report's question)
        CHECK(worst10 / kDenAndHallSqYd < 0.5f);    // ...under half once the hall's west half is used
        // Torn Hide, trails and lines never outlast the charge cycle by more than the second line's second.
        CHECK(kTrailMs + kChargeGapMs >= kChargeEveryMs * 2 / 3);
    }
}

int main()
{
    TestSliceAndArena();
    TestCountsAndTuning();
    TestFuryClock();
    TestChargePlan();
    TestChargeReach();
    TestRabies();
    TestTornHide();
    TestTrail();
    return Report("brs_halycon_gizrul_test");
}
