// Host tests for GrebmarLogic.h (D3: Houndmaster Grebmar and his Kennel Hounds).
// The slice and the arena (WP-S0's), the command rotation, the horn against the pack cap, the leap's timing and
// shapes against the G1 drill's `leap` row, the double whistle, the tuning table and the room's points.
#include "GrebmarLogic.h"
#include "check.h"
#include <cmath>
#include <set>

using namespace BlackrockDepthsRework;
using namespace BrdGrebmar;

namespace
{
    bool InArena(Point3 const& p)
    {
        return GrebmarArena().Contains(p.XY(), p.z);
    }

    float Dist(Point3 const& a, Point3 const& b)
    {
        return DungeonKit::Distance(a.XY(), b.XY());
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210780 && kSpellSlice.last == 210809);
        // Contiguous from the slice's first id, every one inside it.
        std::uint32_t const spells[] = { SPELL_GR_WHISTLE_SIC_EM, SPELL_GR_WHISTLE_FETCH, SPELL_GR_WHISTLE_HEEL,
            SPELL_GR_SIC_EM_MARK, SPELL_GR_SIC_EM_LANDING, SPELL_GR_SIC_EM_LEAP, SPELL_GR_LEAP_LOOK, SPELL_GR_SNATCHED,
            SPELL_GR_FETCH_RUNNER, SPELL_GR_LICK_WOUNDS, SPELL_GR_FRENZY, SPELL_GR_FRENZY_FLASH, SPELL_GR_KENNEL_HORN,
            SPELL_GR_KENNEL_HORN_BURST, SPELL_GR_RELEASE_THE_HOUNDS, SPELL_GR_REND, SPELL_GR_PUMMEL };
        std::uint32_t expected = kSpellSlice.first;
        for (std::uint32_t const id : spells)
        {
            CHECK(id == expected);
            CHECK(kSpellSlice.Contains(id));
            ++expected;
        }
        CHECK(kLastSpell == expected - 1);
        // Bloodlust is the stock spell (outside every custom block).
        CHECK(!kSpellsReservation.Contains(SPELL_STOCK_BLOODLUST));
    }

    void TestCommands()
    {
        // R-1-A m2: only a free, fighting hound takes an order; crowd control keeps it out of every command
        CHECK(HoundObeys(true, true, false));
        CHECK(!HoundObeys(true, true, true));
        CHECK(!HoundObeys(true, false, false));
        CHECK(!HoundObeys(false, true, false));

        std::set<std::uint32_t> spells;
        std::set<std::uint8_t> texts;
        for (std::uint8_t i = 0; i < kCommandCount; ++i)
        {
            Command const c = static_cast<Command>(i);
            spells.insert(WhistleSpell(c));
            texts.insert(CommandText(c));
            Command back = Command::Heel;
            CHECK(CommandOfSpell(WhistleSpell(c), back));
            CHECK(back == c);
        }
        CHECK(spells.size() == kCommandCount);        // one whistle spell (and school) per command
        CHECK(texts == (std::set<std::uint8_t>{ SAY_GREBMAR_SIC_EM, SAY_GREBMAR_FETCH, SAY_GREBMAR_HEEL }));
        Command none = Command::SicEm;
        CHECK(!CommandOfSpell(SPELL_GR_PUMMEL, none));
        CHECK(!CommandOfSpell(0, none));

        // FirstCommand reaches all three.
        std::set<std::uint8_t> firsts;
        for (std::uint32_t roll = 0; roll < 9; ++roll)
            firsts.insert(static_cast<std::uint8_t>(FirstCommand(roll)));
        CHECK(firsts.size() == kCommandCount);

        // NextCommand never repeats, and both other commands are reachable from every command.
        for (std::uint8_t i = 0; i < kCommandCount; ++i)
        {
            Command const last = static_cast<Command>(i);
            std::set<std::uint8_t> nexts;
            for (std::uint32_t roll = 0; roll < 8; ++roll)
            {
                Command const next = NextCommand(last, roll);
                CHECK(next != last);
                nexts.insert(static_cast<std::uint8_t>(next));
            }
            CHECK(nexts.size() == 2);
        }

        // A long pseudo-random rotation: no command twice in a row, each comes up.
        std::uint32_t seed = 12345;
        Command last = FirstCommand(seed);
        std::uint32_t counts[kCommandCount] = {};
        for (int i = 0; i < 3000; ++i)
        {
            seed = seed * 1103515245u + 12345u;
            Command const next = NextCommand(last, seed >> 16);
            CHECK(next != last);
            ++counts[static_cast<std::uint8_t>(next)];
            last = next;
        }
        for (std::uint32_t const n : counts)
            CHECK(n > 600);
    }

    void TestHorn()
    {
        // Normal: 2 a blow, cap 6; heroic: 3 a blow, cap 8.
        CHECK(HornSummons(0, false) == 2);
        CHECK(HornSummons(4, false) == 2);
        CHECK(HornSummons(5, false) == 1);
        CHECK(HornSummons(6, false) == 0);
        CHECK(HornSummons(9, false) == 0);
        CHECK(HornSummons(4, true) == 3);
        CHECK(HornSummons(6, true) == 2);
        CHECK(HornSummons(7, true) == 1);
        CHECK(HornSummons(8, true) == 0);

        // Nobody killed for 5 minutes (horns at 30 s, then every 40 s, plus the finale's): the pack never passes the
        // cap, and it reaches it.
        for (bool const heroic : { false, true })
        {
            std::uint32_t alive = kPackAtPull;
            std::uint32_t const blows = 1 + (300000 - kHornFirstMs) / kHornEveryMs + 1;
            for (std::uint32_t b = 0; b < blows; ++b)
            {
                alive += HornSummons(alive, heroic);
                CHECK(alive <= kPackCap(heroic));
            }
            CHECK(alive == kPackCap(heroic));
        }

        // The doors alternate.
        CHECK(Dist(HornEntry(0), HornEntry(1)) > 10.f);
        CHECK(Dist(HornEntry(0), HornEntry(2)) < 0.01f);
    }

    void TestTimers()
    {
        CHECK(kWhistleFirstMs == 8000);
        CHECK(kWhistleEveryMs.normal == 12000 && kWhistleEveryMs.heroic == 10000);
        CHECK(kWhistleCastMs == 2000);
        CHECK(kHornFirstMs == 30000 && kHornEveryMs == 40000);
        // The double whistle (heroic below 30%): the second starts after the first ends (one kick fits each), and
        // both are over before the next pair.
        CHECK(kDoubleWhistleGapMs > kWhistleCastMs);
        CHECK(kDoubleWhistleGapMs - kWhistleCastMs <= 1000);
        CHECK(kDoubleWhistleGapMs + kWhistleCastMs + kLeapMs <= kWhistleEveryMs.heroic);
        // Sic 'em's mark lasts the whistle and the leap.
        CHECK(kSicEmMarkMs == kWhistleCastMs + kLeapMs);
        // Fetch: 15 s to kill the runner; Snatched outlasts the window (it is refreshed to 30 s on an escape).
        CHECK(kFetchWindowMs == 15000 && kSnatchedMs == 30000);
        CHECK(kSnatchedMs > kFetchWindowMs);
        // Heel: the run back plus the 5 s lick end before the next whistle.
        CHECK(kLickMs == 5000 && kFrenzyMs == 15000);
        CHECK(kHeelRunMs + kLickMs <= kWhistleEveryMs.heroic);
        CHECK(kLickMs % kLickTickMs == 0);
        // The stock timers kept (Pummel 5-7 s then 12-14 s; the hounds' Rend 7-11 s, 15 s, ticks of 3 s).
        CHECK(kPummelFirstMinMs <= kPummelFirstMaxMs && kPummelEveryMinMs <= kPummelEveryMaxMs);
        CHECK(kRendEveryMinMs <= kRendEveryMaxMs && kRendMs % kRendTickMs == 0);
    }

    void TestLeap()
    {
        // The G1 drill's `leap` row (BM MechanicDrill.h): 3 yd lines, a 5 yd landing, 1.5 s; tags 4 and 5.
        CHECK(kLeapLineWidth == 3.f);
        CHECK(kLandingRadius == 5.f);
        CHECK(kLeapMs == 1500);
        CHECK(TAG_GR_LEAP_LINE == 4 && TAG_GR_LEAP_LANDING == 5);
        CHECK(LeapPlan::LandMs() == kLeapMs);
        CHECK(LeapPlan::TakeOffMs() > 0 && LeapPlan::TakeOffMs() < LeapPlan::LandMs());
        CHECK(!DrawsLine(0.f));
        CHECK(!DrawsLine(kMinLineYd - 0.1f));
        CHECK(DrawsLine(kMinLineYd));
        CHECK(DrawsLine(40.f));
        // The landing's 5 yd at a walking 7 yd/s: 1.5 s leaves the marked player time to step out (5 yd needs 0.71 s).
        CHECK(kLandingRadius / 7.f * 1000.f < static_cast<float>(kLeapMs));
    }

    void TestTuning()
    {
        CHECK(kLandingPct.normal == 30.f && kLandingPct.heroic == 45.f);
        CHECK(kLeapLinePct.normal == 15.f && kLeapLinePct.heroic == 25.f);
        // S1: "heroic hits under 50%" (Weakened on top must not make one hit lethal).
        CHECK(kLandingPct.heroic < 50.f && kLeapLinePct.heroic < 50.f);
        CHECK(kPummelPct.normal < kPummelPct.heroic);
        CHECK(kRendPctPerTick.normal < kRendPctPerTick.heroic);
        CHECK(kSnatchedPct == 30 && kLickHealPctPerSec == 5 && kLickDamageTakenPct == 30 && kFrenzyHastePct == 30);
        CHECK(kFinalePct == 30.f);
        CHECK(kHoundHealth.normal == 5000 && kHoundHealth.heroic == 9000);
        CHECK(kWhistleKickPriorityHeroic > kWhistleKickPriorityNormal);
        CHECK(kRunnerPriority > kHoundPriority && kHoundPriority > 0);
        CHECK(kPackCap.normal == 6 && kPackCap.heroic == 8);
        CHECK(kHornHounds.normal == 2 && kHornHounds.heroic == 3);
    }

    void TestTexts()
    {
        // His groups sit in WP-S0's range for 9319 (0-6, all new).
        bool found = false;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_GREBMAR)
            {
                found = true;
                CHECK(r.first == SAY_GREBMAR_PULL);
                CHECK(r.last == SAY_GREBMAR_DEATH);
                CHECK(r.firstNew == 0);
            }
        CHECK(found);
        std::set<std::uint8_t> const groups{ SAY_GREBMAR_PULL, SAY_GREBMAR_SIC_EM, SAY_GREBMAR_FETCH, SAY_GREBMAR_HEEL,
            SAY_GREBMAR_FINALE, EMOTE_GREBMAR_HORN, SAY_GREBMAR_DEATH };
        CHECK(groups.size() == 7);
    }

    void TestGeometry()
    {
        // Houndmaster Grebmar spawns kGrebmarSpawn, inside the arena.
        CHECK(InArena(kGrebmarSpawn));
        CHECK(ArenaFor(BOSS_GREBMAR).Contains(kGrebmarSpawn.XY(), kGrebmarSpawn.z));
        // The pack at his feet: within 7 yd of him (the stock spots), inside the arena, apart.
        for (std::size_t i = 0; i < kPackSpots.size(); ++i)
        {
            CHECK(InArena(kPackSpots[i]));
            CHECK(Dist(kPackSpots[i], kGrebmarSpawn) <= 7.f);
            for (std::size_t j = i + 1; j < kPackSpots.size(); ++j)
                CHECK(Dist(kPackSpots[i], kPackSpots[j]) >= 1.5f);
        }
        // The kennel doors (26 and 31 yd from him) and the Fetch exit (45 yd) are on the arena: the leash never
        // pulls him off a hound he chases there, and a runner at the exit can still be killed in the fight.
        for (Point3 const& door : kHornEntries)
        {
            CHECK(InArena(door));
            CHECK(Dist(door, kGrebmarSpawn) > 20.f && Dist(door, kGrebmarSpawn) < 35.f);
        }
        CHECK(InArena(kFetchExit));
        CHECK(Dist(kFetchExit, kGrebmarSpawn) > 30.f);
        CHECK(std::fabs(kFetchExit.z - kFloorZ) < 0.5f);
        // The runner crosses the hall in about 6 s at a hound's 8 yd/s: well inside its 15 s window.
        CHECK(Dist(kFetchExit, kGrebmarSpawn) / 8.f * 1000.f < static_cast<float>(kFetchWindowMs));

        // The Heel ring: every spot kHeelRadius from him, distinct, for any pack size up to the heroic cap.
        Vec2 const center = kGrebmarSpawn.XY();
        for (std::uint32_t n = 1; n <= kPackCap.heroic; ++n)
            for (std::uint32_t i = 0; i < n; ++i)
            {
                Vec2 const at = HeelSpot(center, i, n);
                CHECK(std::fabs(DungeonKit::Distance(at, center) - kHeelRadius) < 0.01f);
                CHECK(GrebmarArena().Contains(at, kGrebmarSpawn.z));
                for (std::uint32_t j = i + 1; j < n; ++j)
                    CHECK(DungeonKit::Distance(at, HeelSpot(center, j, n)) > 1.f);
            }
        CHECK(std::fabs(DungeonKit::Distance(HeelSpot(center, 0, 0), center) - kHeelRadius) < 0.01f);
    }
}

int main()
{
    TestSlice();
    TestCommands();
    TestHorn();
    TestTimers();
    TestLeap();
    TestTuning();
    TestTexts();
    TestGeometry();
    return Report("brd_grebmar_test");
}
