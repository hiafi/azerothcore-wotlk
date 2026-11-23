// Host tests for HollisGreyLogic.h (D7: Lector Hollis Grey, the Librarian; LIB LB1-LB9).
#include "DungeonKitWingLogic.h"
#include "HollisGreyLogic.h"
#include "check.h"
#include <array>
#include <cmath>
#include <set>
#include <vector>

using namespace ScarletMonasteryRework;
using namespace SmHollisGrey;

namespace
{
    // A deterministic stand-in for urand: a linear congruential stream.
    struct Lcg
    {
        std::uint32_t state = 12345;

        std::uint32_t operator()(std::uint32_t n)
        {
            state = state * 1103515245u + 12345u;
            return n ? (state >> 8) % n : 0;
        }
    };

    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndIds()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 212610 && kSpellSlice.last == 212669);
        CHECK(kSpellSlice.Contains(SPELL_LB_OPEN_THE_INDEX));
        CHECK(kSpellSlice.Contains(kLastSpell));
        CHECK(SPELL_LB_OPEN_THE_INDEX == 212610);
        CHECK(SPELL_LB_SEARING_REBUKE == 212640);
        CHECK(SPELL_LB_WEB == 212644);
        // One story aura and one emote per story, in the spec's order.
        CHECK(StorySpell(Story::Spider) == SPELL_LB_STORY_SPIDER);
        CHECK(StorySpell(Story::Aftermath) == SPELL_LB_STORY_AFTERMATH);
        CHECK(StoryText(Story::Spider) == 1);
        CHECK(StoryText(Story::Aftermath) == 6);
        CHECK(SAY_LB_AGGRO == 0 && SAY_LB_DEATH == 7);
        // The text groups sit in S0's range for 300913 (0-7, all new).
        bool found = false;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_SM_HOLLIS_GREY)
            {
                found = true;
                CHECK(r.first == SAY_LB_AGGRO && r.last == SAY_LB_DEATH && r.firstNew == 0);
            }
        CHECK(found);
        CHECK(NPC_SM_HOLLIS_GREY == 300913 && NPC_SM_CURSED_BOOK == 300914 && NPC_SM_INFERNAL == 300915);
        CHECK(NPC_SM_SPIDERLING == 300916 && NPC_SM_SPECTRAL_TROLL == 300917 && NPC_SM_PHANTOM_GRUNT == 300918);
        CHECK(kBound);
        CHECK(!IsWave2Boss(BOSS_HOLLIS_GREY));
    }

    void TestSpot()
    {
        // His spot is S0's pocket (section 7 #26 A), inside his arena; the floor z is the hall's [db] 20.48.
        CHECK(Near(kHollisGreyPocket.x, kHollisGreySpot.x) && Near(kHollisGreyPocket.y, kHollisGreySpot.y));
        CHECK(HollisGreyArena().Contains(kHollisGreyPocket.XY(), kHollisGreyPocket.z));
        CHECK(ArenaFor(BOSS_HOLLIS_GREY).Contains(kHollisGreySpot.XY(), kHollisGreySpot.z));
        CHECK(kHollisGreyPocket.z > 20.f && kHollisGreyPocket.z < 21.f);
        // Every floor point is inside his arena and inside the bots' bounds rectangle.
        for (Point3 const& p : kHallFloor)
        {
            CHECK(HollisGreyArena().Contains(p.XY(), p.z));
            CHECK(p.x >= kHallBounds[0].x && p.x <= kHallBounds[1].x);
            CHECK(p.y <= kHallBounds[0].y && p.y >= kHallBounds[2].y);
            CHECK(p.z >= kHallZMin && p.z <= kHallZMax);
        }
        // The 10-20 yd ring round the pocket has floor to throw to (NAVMESH: 71% floor).
        std::size_t inRing = 0;
        for (Point3 const& p : kHallFloor)
        {
            float const d = DungeonKit::Distance(kHollisGreyPocket.XY(), p.XY());
            if (d >= kThrowMinYd && d <= kThrowMaxYd)
                ++inRing;
        }
        CHECK(inRing >= 30);
        // The longest shapes fit the hall (NAVMESH: rings to 32 yd, 35 yd lines).
        CHECK(StompRingAt(kStompRingsMax - 1).outer <= 32.f);
        CHECK(kAxeLengthYd <= 35.f);
    }

    void TestShelf()
    {
        Lcg rand;
        Shelf shelf;
        shelf.Shuffle(rand);
        // Six books, no repeat until all six are read, then a fresh shuffle.
        for (int round = 0; round < 5; ++round)
        {
            std::set<std::uint8_t> seen;
            for (int i = 0; i < kStoryCount; ++i)
            {
                CHECK(shelf.ReadThisRound() == i);
                Story const s = shelf.Take(rand);
                CHECK(static_cast<std::uint8_t>(s) < kStoryCount);
                seen.insert(static_cast<std::uint8_t>(s));
            }
            CHECK(seen.size() == kStoryCount);
            CHECK(shelf.ReadThisRound() == 0);
        }
        // The order is not always the same (the shuffle moves books).
        std::set<std::uint8_t> firsts;
        for (int i = 0; i < 40; ++i)
        {
            shelf.Shuffle(rand);
            firsts.insert(static_cast<std::uint8_t>(shelf.Peek()));
        }
        CHECK(firsts.size() >= 4);
        // PutNext: the GM's pick comes next, and the round still holds each book once.
        shelf.Shuffle(rand);
        shelf.PutNext(Story::Dream);
        CHECK(shelf.Peek() == Story::Dream);
        std::set<std::uint8_t> round;
        for (Story s : shelf.Order())
            round.insert(static_cast<std::uint8_t>(s));
        CHECK(round.size() == kStoryCount);
    }

    void TestOpening()
    {
        CHECK(kOpenFirstMs(false) == 8000 && kOpenEveryMs(false) == 20000 && kOpenCastMs(false) == 2000);
        CHECK(kOpenFirstMs(true) == 6000 && kOpenEveryMs(true) == 15000 && kOpenCastMs(true) == 3000);
        // Normal: no new book while 2 are open; heroic: no cap.
        CHECK(MayOpenBook(0, false) && MayOpenBook(1, false) && !MayOpenBook(2, false) && !MayOpenBook(3, false));
        CHECK(MayOpenBook(2, true) && MayOpenBook(6, true));
        // Heroic: a finished cast opens on page 2, a kicked one on page 1; normal always page 1.
        CHECK(OpeningPage(true, false) == 2);
        CHECK(OpeningPage(true, true) == 1);
        CHECK(OpeningPage(false, false) == 1 && OpeningPage(false, true) == 1);
    }

    void TestPages()
    {
        // Normal stops at page 3; heroic keeps turning.
        CHECK(NextPage(1, false) == 2 && NextPage(2, false) == 3 && NextPage(3, false) == 3);
        CHECK(NextPage(3, true) == 4 && NextPage(9, true) == 10);
        CHECK(kPageEveryMs == 10000);
        // Reader's Ward: 25% per open book, 50% (2 books) / 75% (3 books) at most (the kit's WardRule).
        DungeonKit::WardRule normal{ kWardPctPerBook, kWardCapPct(false) };
        DungeonKit::WardRule heroic{ kWardPctPerBook, kWardCapPct(true) };
        CHECK(normal.Stacks(1) == 1 && normal.Stacks(2) == 2 && normal.Stacks(5) == 2);
        CHECK(Near(normal.ReductionPct(4), 50.f));
        CHECK(heroic.Stacks(3) == 3 && heroic.Stacks(6) == 3);
        CHECK(Near(heroic.ReductionPct(6), 75.f));
        CHECK(Near(heroic.ReductionPct(1), 25.f));
    }

    void TestStories()
    {
        // LB2: 2 spiderlings a web, +1 a page; normal holds 3 webs (the 4th fades the oldest), heroic none.
        CHECK(SpiderlingsPerWeb(1) == 2 && SpiderlingsPerWeb(2) == 3 && SpiderlingsPerWeb(3) == 4);
        CHECK(!WebsOverCap(3, false) && WebsOverCap(4, false) && !WebsOverCap(9, true));
        CHECK(kWebFirstMs == 2000 && kWebEveryMs == 8000 && kWebWarnMs == 2000 && Near(kWebRadiusYd, 6.f));
        // LB3: 1 meteor a fall, +1 a page; normal 2 Infernals alive per book.
        CHECK(MeteorsPerFall(1) == 1 && MeteorsPerFall(3) == 3);
        CHECK(InfernalMayRise(0, false) && InfernalMayRise(1, false) && !InfernalMayRise(2, false));
        CHECK(InfernalMayRise(5, true));
        CHECK(kMeteorFirstMs == 0 && kMeteorEveryMs == 15000 && kMeteorWarnMs == 4000);
        CHECK(Near(kMeteorPct(false), 50.f) && Near(kMeteorPct(true), 60.f) && Near(kMeteorRadiusYd, 8.f));
        CHECK(kMeteorLookLeadMs < kMeteorWarnMs);
        // LB4: 2 axes, +1 a page; the line 35 yd from the troll.
        CHECK(AxesPerVolley(1) == 2 && AxesPerVolley(2) == 3);
        CHECK(Near(AxeOverrun(10.f), 25.f) && Near(AxeOverrun(35.f), 0.f) && Near(AxeOverrun(40.f), 0.f));
        CHECK(Near(kAxePct(false), 35.f) && Near(kAxePct(true), 45.f) && Near(kAxeWidthYd, 3.f));
        CHECK(kAxeFirstMs == 2000 && kAxeEveryMs == 6000 && kAxeWarnMs == 2000 && kAxeLookLeadMs < kAxeWarnMs);
        // LB5: 3 rings on page 1, +1 a page to 4 (32 yd); 1.5 s apart, the first after 2 s.
        CHECK(StompRings(1) == 3 && StompRings(2) == 4 && StompRings(3) == 4 && StompRings(8) == 4);
        CHECK(Near(StompRingAt(0).inner, 0.f) && Near(StompRingAt(0).outer, 8.f) && StompRingAt(0).warnMs == 2000);
        CHECK(Near(StompRingAt(1).inner, 8.f) && Near(StompRingAt(1).outer, 16.f) && StompRingAt(1).warnMs == 3500);
        CHECK(Near(StompRingAt(2).outer, 24.f) && StompRingAt(2).warnMs == 5000);
        CHECK(Near(StompRingAt(3).outer, 32.f) && StompRingAt(3).warnMs == 6500);
        // The last ring of a full stomp lands before the next stomp is marked.
        CHECK(StompRingAt(kStompRingsMax - 1).warnMs < kStompEveryMs);
        CHECK(Near(kStompPct(false), 35.f) && Near(kStompPct(true), 45.f));
        // LB6: 6 yd, +3 yd a page (normal 12 yd at page 3).
        CHECK(Near(MistRadius(1), 6.f) && Near(MistRadius(2), 9.f) && Near(MistRadius(3), 12.f));
        CHECK(Near(MistRadius(4), 15.f));
        // LB7: 1 grunt, +1 a page; 50% / 60%.
        CHECK(GruntsPerCharge(1) == 1 && GruntsPerCharge(2) == 2);
        CHECK(Near(kChargePct(false), 50.f) && Near(kChargePct(true), 60.f) && Near(kChargeWidthYd, 6.f));
        CHECK(kChargeFirstMs == 3000 && kChargeEveryMs == 10000 && kChargeWarnMs == 3000);
        // LB8 and LB9.
        CHECK(kRebukeFirstMs == 5000 && kRebukeEveryMs == 10000 && kRebukeCastMs == 2500);
        CHECK(Near(kRebukePct(false), 20.f) && Near(kRebukePct(true), 30.f));
        CHECK(Near(kBurningBookYd, 5.f) && Near(kBurningBookPct, 10.f));
        // Hits against warnings (the approval check): the 2 s hits stay under the 40% ladder on normal.
        CHECK(kAxePct(false) < 40.f && kStompPct(false) < 40.f);
    }

    void TestDrowsy()
    {
        // A stack off a second outside, kept inside; the sleep at five.
        CHECK(DrowsyCheck(3, false, true).stacks == 2 && !DrowsyCheck(3, false, true).sleep);
        CHECK(DrowsyCheck(3, true, true).stacks == 3);
        CHECK(DrowsyCheck(3, false, false).stacks == 3);
        CHECK(DrowsyCheck(0, false, true).stacks == 0);
        CHECK(DrowsyCheck(5, true, false).sleep && DrowsyCheck(5, true, false).stacks == 0);
        CHECK(DrowsyCheck(6, false, true).sleep);
        CHECK(kDreamSleepMs == 2000 && kDreamingMs == 6000 && Near(kDreamingMistYd, 6.f));
        // A player standing in the mist sleeps after five ticks (5 s).
        std::uint8_t stacks = 0;
        int seconds = 0;
        bool slept = false;
        while (!slept && seconds < 20)
        {
            ++seconds;
            stacks = static_cast<std::uint8_t>(stacks + 1);     // the mist's tick (the rider)
            DrowsyStep const s = DrowsyCheck(stacks, true, true);
            stacks = s.stacks;
            slept = s.sleep;
        }
        CHECK(slept && seconds == 5);
    }

    void TestKillOrder()
    {
        CHECK(BookPriority(1) == 2 && BookPriority(2) == 3 && BookPriority(3) == 4 && BookPriority(7) == 4);
        CHECK(BookPriority(1) > 0 && kStoryAddPriority < 0);
        // The adds' first target: the nearest tank, else the nearest player.
        std::array<ArrivalCandidate, 3> c{ { { 4.f, false }, { 12.f, true }, { 2.f, false } } };
        CHECK(PickArrival(c) == 1);
        std::array<ArrivalCandidate, 2> noTank{ { { 9.f, false }, { 3.f, false } } };
        CHECK(PickArrival(noTank) == 1);
        std::array<ArrivalCandidate, 3> twoTanks{ { { 9.f, true }, { 3.f, true }, { 1.f, false } } };
        CHECK(PickArrival(twoTanks) == 1);
        CHECK(PickArrival(std::span<ArrivalCandidate const>()) == -1);
    }

    void TestThrow()
    {
        Lcg rand;
        Vec2 const pocket = kHollisGreyPocket.XY();
        // Every pick from the pocket is 10-20 yd off and on the floor table.
        for (int i = 0; i < 200; ++i)
        {
            std::optional<std::size_t> pick = PickThrowSpot(pocket, kHallFloor, std::span<Vec2 const>(), rand);
            CHECK(pick && *pick < kHallFloor.size());
            if (!pick)
                continue;
            float const d = DungeonKit::Distance(pocket, kHallFloor[*pick].XY());
            CHECK(d >= kThrowMinYd && d <= kThrowMaxYd);
        }
        // An open book keeps the next one 6 yd off.
        std::vector<Vec2> books{ Vec2{ 264.f, -389.f } };
        for (int i = 0; i < 200; ++i)
        {
            std::optional<std::size_t> pick = PickThrowSpot(pocket, kHallFloor, books, rand);
            CHECK(pick.has_value());
            if (pick)
                CHECK(DungeonKit::Distance(books[0], kHallFloor[*pick].XY()) >= kBookSpacingYd);
        }
        // Pulled far off (55 yd away): the floor point nearest to 15 yd from him, on the hall's near side.
        Vec2 const far{ 200.f, -389.f };
        std::optional<std::size_t> pick = PickThrowSpot(far, kHallFloor, std::span<Vec2 const>(), rand);
        CHECK(pick.has_value());
        if (pick)
            CHECK(kHallFloor[*pick].x <= 250.f);
        CHECK(!PickThrowSpot(pocket, std::span<Point3 const>(), std::span<Vec2 const>(), rand).has_value());
    }

    void TestWindows()
    {
        // Rule 20: a book at the spec's group DPS and at the measured bot throughput (about half).
        float const specN = BookCloseSeconds(kBookHealth(false), kSpecGroupDps(false));
        float const botN = BookCloseSeconds(kBookHealth(false), kSpecGroupDps(false) / 2);
        float const specH = BookCloseSeconds(kBookHealth(true), kSpecGroupDps(true));
        float const botH = BookCloseSeconds(kBookHealth(true), kSpecGroupDps(true) / 2);
        CHECK(specN > 5.f && specN < 5.5f);        // the spec's "about 5 s"
        CHECK(botN > 10.f && botN < 11.f);         // bots: one page turn before it closes
        CHECK(specH > 4.5f && specH < 5.f);
        CHECK(botH > 9.f && botH < 10.f);
        // Even at bot pace a book closes before the next is thrown, so 2 open books need a miss.
        CHECK(botN < static_cast<float>(kOpenEveryMs(false)) / 1000.f);
        CHECK(botH < static_cast<float>(kOpenEveryMs(true)) / 1000.f);
        CHECK(kBossHealth(false) == 36000 && kBossHealth(true) == 220000);
        CHECK(kInfernalHealth(false) == 4000 && kSpiderlingHealth(false) == 500);
    }
}

int main()
{
    TestSliceAndIds();
    TestSpot();
    TestShelf();
    TestOpening();
    TestPages();
    TestStories();
    TestDrowsy();
    TestKillOrder();
    TestThrow();
    TestWindows();
    return Report("sm_hollis_grey_test");
}
