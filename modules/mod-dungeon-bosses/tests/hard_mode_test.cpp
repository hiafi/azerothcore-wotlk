// Host tests for HardModeLogic.h (WP-B9): the slice, the 3:00 schedule, the fire front's stripes and the merged
// burning deck, the mainmast and its wall, the powder placement rule, the deck mask, the ship's bounds, the keg's rule.
#include "HardModeLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <vector>

using namespace HardMode;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    std::uint32_t Count(std::vector<Beat> const& beats, BeatKind kind)
    {
        std::uint32_t n = 0;
        for (Beat const& b : beats)
            n += b.kind == kind ? 1 : 0;
        return n;
    }

    void TestSlice()
    {
        CHECK(kSlice.first == 205380u);
        CHECK(kSlice.last == 205389u);
        for (std::uint32_t id : { SPELL_FIRE_FRONT_HIT, SPELL_BURNING_DECK_TICK, SPELL_POWDER_BLAST_HIT,
                 SPELL_MAINMAST_HIT, SPELL_POWDER_SPARKS, SPELL_POWDER_BLAST_VISUAL, SPELL_BURNING_LOOK,
                 SPELL_MAINMAST_CRASH, SPELL_SHIP_EXPLOSION })
        {
            CHECK(kSlice.Contains(id));
            CHECK(!DeadminesRework::kSpellsVanCleef.Contains(id));
        }
    }

    void TestSchedule()
    {
        std::vector<Beat> const all = BeatsBetween(0, kTimerMs);
        CHECK(Count(all, BeatKind::FrontMarker) == 18u);
        CHECK(Count(all, BeatKind::FrontLanded) == 18u);
        CHECK(Count(all, BeatKind::Powder) == 17u);
        CHECK(Count(all, BeatKind::MastWarn) == 1u);
        CHECK(Count(all, BeatKind::MastLanded) == 1u);
        CHECK(Count(all, BeatKind::OffMyShip) == 1u);
        CHECK(Count(all, BeatKind::Explosion) == 1u);
        // in time order, the explosion last at 3:00
        for (std::size_t i = 1; i < all.size(); ++i)
            CHECK(all[i - 1].atMs <= all[i].atMs);
        CHECK(!all.empty() && all.back().kind == BeatKind::Explosion && all.back().atMs == 180000u);

        std::map<BeatKind, std::vector<std::uint32_t>> at;
        for (Beat const& b : all)
            at[b.kind].push_back(b.atMs);
        // fire front: 5 s, then every 10 s; lands 2 s later
        CHECK(at[BeatKind::FrontMarker].front() == 5000u && at[BeatKind::FrontMarker].back() == 175000u);
        CHECK(at[BeatKind::FrontLanded].front() == 7000u && at[BeatKind::FrontLanded].back() == 177000u);
        // powder: 10 s, every 10 s, the last at 2:50
        CHECK(at[BeatKind::Powder].front() == 10000u && at[BeatKind::Powder].back() == 170000u);
        // mast at 2:00 (lands 2:04), yell at 2:45
        CHECK(at[BeatKind::MastWarn].front() == 120000u);
        CHECK(at[BeatKind::MastLanded].front() == 124000u);
        CHECK(at[BeatKind::OffMyShip].front() == 165000u);
        // 5 s out of step: no front marker or landing at a blast's marker or landing (2 s later)
        std::set<std::uint32_t> front(at[BeatKind::FrontMarker].begin(), at[BeatKind::FrontMarker].end());
        front.insert(at[BeatKind::FrontLanded].begin(), at[BeatKind::FrontLanded].end());
        for (std::uint32_t p : at[BeatKind::Powder])
        {
            CHECK(!front.count(p));
            CHECK(!front.count(p + kPowderWarnMs));
            CHECK(p % kFrontEveryMs == 0 && FrontMarkerMs(0) % kFrontEveryMs == 5000u);
        }
        // the mast's beat comes before a blast at the same moment (2:00), so the blast can avoid it
        for (std::size_t i = 1; i < all.size(); ++i)
            if (all[i].atMs == kMastMs && all[i].kind == BeatKind::Powder)
                CHECK(all[i - 1].kind == BeatKind::MastWarn);

        // any split into steps fires each beat once
        for (std::uint32_t step : { 1u, 7u, 33u, 100u, 999u, 2000u, 10000u, 45000u })
        {
            std::vector<Beat> stepped;
            for (std::uint32_t t = 0; t < kTimerMs; t += step)
            {
                std::vector<Beat> part = BeatsBetween(t, std::min(t + step, kTimerMs));
                stepped.insert(stepped.end(), part.begin(), part.end());
            }
            CHECK(stepped.size() == all.size());
            bool same = stepped.size() == all.size();
            for (std::size_t i = 0; same && i < all.size(); ++i)
                same = stepped[i].atMs == all[i].atMs && stepped[i].kind == all[i].kind
                    && stepped[i].index == all[i].index;
            CHECK(same);
        }
        CHECK(BeatsBetween(5000, 5000).empty());
        CHECK(BeatsBetween(6000, 5000).empty());
        CHECK(BeatsBetween(4999, 5000).size() == 1u);
        CHECK(BeatsBetween(5000, 6999).empty());

        // stripes landed
        CHECK(StripesLandedBy(0) == 0u);
        CHECK(StripesLandedBy(6999) == 0u);
        CHECK(StripesLandedBy(7000) == 1u);
        CHECK(StripesLandedBy(120000) == 12u);  // DM: 12 by 2:00
        CHECK(StripesLandedBy(160000) == 16u);  // 16 by 2:40
        CHECK(StripesLandedBy(180000) == 18u);  // 18 by 3:00
    }

    void TestFireFront()
    {
        CHECK(Near(kStripeDepth, 2.73f));
        // stripe 0 starts at the sterncastle face and holds the keg
        Strip const s0 = StripeRect(0);
        CHECK(Near(s0.xHi, -53.5f));
        CHECK(Near(s0.width, kStripeDepth));
        CHECK(s0.Contains(DeadminesRework::kPowderKegSpot));
        // each stripe lands just ahead (bow-ward) of the last: no gap, no overlap
        for (std::uint32_t k = 0; k + 1 < kStripeCount; ++k)
        {
            Strip const a = StripeRect(k);
            Strip const b = StripeRect(k + 1);
            CHECK(Near(a.xLo, b.xHi));
            CHECK(b.CenterX() < a.CenterX());
            CHECK(Near(b.width, kStripeDepth));
        }
        // rail to rail: the stripe covers every deck cell across its x
        Strip const s5 = StripeRect(5);
        for (float y = -802.f; y >= -840.f; y -= 1.f)
            CHECK(s5.Contains({ s5.CenterX(), y }));
        CHECK(Near(s5.from.y, kStripeWestY) && Near(s5.facing, 4.71238898f) && Near(s5.length, 42.f));
        CHECK(Near(s5.from.x, s5.CenterX()));
        // section 3.8: front at x -86.3 at 2:00, about 10 yd of bow left at 2:40, about 4.5-5 yd at 3:00
        CHECK(Near(FrontX(12), -86.26f, 0.05f));
        float const bowTip = DeadminesRework::kDeckBowTip.x;
        CHECK(std::fabs((FrontX(16) - bowTip) - 10.f) <= 0.5f);
        CHECK(FrontX(18) - bowTip > 4.f && FrontX(18) - bowTip < 5.5f);
        CHECK(FrontX(kStripeCount) > bowTip);  // never past the bow

        // the merged burning deck: face to front, every landed stripe inside, nothing ahead of the front
        CHECK(!BurntDeck(0));
        for (std::uint32_t n = 1; n <= kStripeCount; ++n)
        {
            std::optional<Strip> const deck = BurntDeck(n);
            CHECK(deck.has_value());
            if (!deck)
                continue;
            CHECK(Near(deck->xHi, -53.5f));
            CHECK(Near(deck->xLo, FrontX(n)));
            CHECK(Near(deck->width, n * kStripeDepth, 0.02f));
            for (std::uint32_t k = 0; k < n; ++k)
                CHECK(deck->Contains({ StripeRect(k).CenterX(), -820.f }));
            CHECK(!deck->Contains({ FrontX(n) - 0.1f, -820.f }));
            // the line marker ladder draws aspects 1/4 .. 64 (length / width)
            CHECK(deck->length / deck->width >= 0.25f && deck->length / deck->width <= 64.f);
        }
    }

    void TestMast()
    {
        Strip const mast = MastRect(StripesLandedBy(kMastMs));
        // 6 yd wide, just ahead of the front at 2:00 (handoff: about x -88..-94)
        CHECK(Near(mast.width, kMastWidth));
        CHECK(Near(mast.xHi, FrontX(12) - kMastGapYd));
        CHECK(mast.xHi < FrontX(12));
        CHECK(mast.xLo > -95.f && mast.xHi < -86.f);
        // the wall keeps the part ahead of the front, then goes
        std::optional<Strip> const whole = WallAhead(mast, FrontX(12));
        CHECK(whole && Near(whole->xLo, mast.xLo) && Near(whole->xHi, mast.xHi));
        std::optional<Strip> const part = WallAhead(mast, FrontX(14));   // front at about -91.7: inside the mast
        CHECK(part && Near(part->xHi, FrontX(14)) && Near(part->xLo, mast.xLo));
        CHECK(part && part->width < mast.width);
        CHECK(!WallAhead(mast, FrontX(15)));                              // front at about -94.5: past it
        // the clipped wall and the burning deck never overlap
        for (std::uint32_t n = 12; n <= kStripeCount; ++n)
        {
            std::optional<Strip> const wall = WallAhead(mast, FrontX(n));
            std::optional<Strip> const deck = BurntDeck(n);
            if (wall && deck)
                CHECK(wall->xHi <= deck->xLo + 1e-4f);
        }
    }

    void TestDeckMask()
    {
        for (char const* row : kDeckMask)
        {
            std::size_t len = 0;
            while (row[len])
                ++len;
            CHECK(len == kDeckMaskColumns);
        }
        CHECK(OnDeck(DeadminesRework::kVanCleefSpawn));      // on the centre strip
        CHECK(OnDeck(DeadminesRework::kGreenskinSpawn));
        CHECK(OnDeck(DeadminesRework::kPowderKegSpot));      // the keg stands on the deck
        CHECK(OnDeck({ -106.f, -819.5f }));                  // the bow
        CHECK(!OnDeck({ -95.f, -820.f }));                   // the 10 yd hole in the centre (x -89.5..-98)
        CHECK(!OnDeck({ -70.f, -806.f }));                   // overhead structure, west side
        CHECK(!OnDeck({ -60.f, -845.f }));                   // past the east rail
        CHECK(!OnDeck({ -45.f, -820.f }));                   // the sterncastle
        CHECK(!OnDeck({ -115.f, -820.f }));                  // the bowsprit (not mapped)
        CHECK(Near(DeckZ(-53.5f), 43.f) && Near(DeckZ(-107.5f), 38.f) && Near(DeckZ(-80.5f), 40.5f));
        CHECK(Near(DeckZ(0.f), 43.f) && Near(DeckZ(-200.f), 38.f));
    }

    void TestPowder()
    {
        std::vector<Vec2> const nobody;
        // early fight: plenty of deck, every candidate obeys the rule
        for (std::uint32_t n : { 1u, 6u, 12u, 15u })
        {
            std::vector<Vec2> const players{ { -70.f, -820.f }, { -80.f, -810.f }, { -95.f, -830.f } };
            std::optional<Strip> const mast = n >= 12 ? std::optional<Strip>(MastRect(12)) : std::nullopt;
            std::vector<Vec2> const c = PowderCandidates(n, players, mast);
            CHECK(!c.empty());
            for (Vec2 const& p : c)
            {
                CHECK(OnDeck(p));
                CHECK(p.x <= FrontX(n + 1) - kPowderAheadYd);   // ahead of the front, past the next stripe
                CHECK(p.x < FrontX(n));
                for (Vec2 const& pl : players)
                    CHECK(DeadminesKit::Distance(p, pl) >= kPowderMinPlayerYd);
                if (mast)
                    CHECK(!mast->Contains(p));
            }
        }
        // a player near a cell removes it; 6.0 yd exactly is allowed
        std::vector<Vec2> const all = PowderCandidates(1, nobody);
        std::vector<Vec2> const one = PowderCandidates(1, { { -80.f, -820.f } });
        CHECK(one.size() < all.size());
        bool sixAllowed = false;
        for (Vec2 const& p : one)
            sixAllowed = sixAllowed || Near(DeadminesKit::Distance(p, { -80.f, -820.f }), 6.f);
        CHECK(sixAllowed);
        // the pick is uniform over the candidates and deterministic for a given rng
        std::optional<Vec2> const first = PickPowderSpot(1, nobody, std::nullopt, [](std::uint32_t) { return 0u; });
        CHECK(first && Near(first->x, all.front().x) && Near(first->y, all.front().y));
        std::optional<Vec2> const last =
            PickPowderSpot(1, nobody, std::nullopt, [](std::uint32_t n) { return n - 1; });
        CHECK(last && Near(last->x, all.back().x) && Near(last->y, all.back().y));
        std::optional<Vec2> const clamped =
            PickPowderSpot(1, nobody, std::nullopt, [](std::uint32_t n) { return n + 5; });
        CHECK(clamped && Near(clamped->x, all.back().x));
        // skipped when the bow is crowded: players every 4 yd over the deck ahead of the front
        std::vector<Vec2> crowd;
        for (float x = -55.f; x >= -110.f; x -= 4.f)
            for (float y = -800.f; y >= -842.f; y -= 4.f)
                crowd.push_back({ x, y });
        CHECK(PowderCandidates(1, crowd).empty());
        CHECK(!PickPowderSpot(1, crowd, std::nullopt, [](std::uint32_t) { return 0u; }));
        // no deck ahead once the front reaches the bow
        CHECK(PowderCandidates(kStripeCount + 3, nobody).empty());
        // late fight, group on the bow: the rule usually skips (DM: "skipped if none")
        std::vector<Vec2> const bowGroup{ { -104.f, -815.f }, { -104.f, -824.f }, { -100.f, -819.f },
                                          { -106.f, -820.f } };
        CHECK(PowderCandidates(16, bowGroup).empty());
    }

    void TestShip()
    {
        CHECK(OnShip(-87.4f, -819.9f, 39.3f));     // VanCleef's spawn
        CHECK(OnShip(-59.6f, -820.1f, 41.6f));     // Greenskin's spawn
        CHECK(OnShip(-40.f, -820.f, 52.f));        // the sterncastle top
        CHECK(OnShip(-59.f, -803.f, 44.5f));       // the gangplank
        CHECK(OnShip(-120.f, -822.f, 38.f));       // the bowsprit
        CHECK(!OnShip(-87.f, -820.f, 20.f));       // the dock and water below
        CHECK(!OnShip(-150.f, -820.f, 40.f));      // off the bow
        CHECK(!OnShip(-80.f, -780.f, 40.f));       // the scaffold beside the ship
    }

    void TestKeg()
    {
        KegInputs ok;
        ok.heroic = true;
        ok.vanCleefFound = true;
        ok.vanCleefAlive = true;
        ok.vanCleefVisible = true;
        ok.encounterOpen = true;
        CHECK(KegUse(ok) == KegRefusal::None);

        KegInputs in = ok;
        in.heroic = false;
        CHECK(KegUse(in) == KegRefusal::NotHeroic);
        in = ok;
        in.hardModeLit = true;
        CHECK(KegUse(in) == KegRefusal::AlreadyLit);
        in = ok;
        in.vanCleefAlive = false;
        CHECK(KegUse(in) == KegRefusal::NoVanCleef);
        in = ok;
        in.vanCleefFound = false;
        CHECK(KegUse(in) == KegRefusal::NoVanCleef);
        in = ok;
        in.vanCleefVisible = false;                 // Greenskin alive: he is hidden
        CHECK(KegUse(in) == KegRefusal::VanCleefHidden);
        in = ok;
        in.vanCleefInCombat = true;
        CHECK(KegUse(in) == KegRefusal::VanCleefInCombat);
        in = ok;
        in.encounterOpen = false;
        CHECK(KegUse(in) == KegRefusal::EncounterClosed);
        CHECK(std::string(KegRefusalName(KegRefusal::None)) == "usable");
        CHECK(std::string(KegRefusalName(KegRefusal::VanCleefInCombat)) == "vancleef-in-combat");
    }

    void TestTuning()
    {
        CHECK(kFuseHealth == 500000u);
        CHECK(kTimerMs == 180000u);
        CHECK(kFrontPct == 30.f && kBurnPct == 10.f && kPowderPct == 40.f && kMastPct == 60.f);
        CHECK(kPowderRadius == 6.f && kPowderBurnMs == 15000u && kMastWarnMs == 4000u && kMastWidth == 6.f);
        // ruling 15: Weakened only under 50% (the front and the blast); the mast's 60% has none
        CHECK(kFrontPct < 50.f && kPowderPct < 50.f && kMastPct >= 50.f);
        State const s;
        CHECK(!s.lit && s.elapsedMs == 0u && s.burntDeckHandle == 0u && s.wallHandle == 0u);
        CHECK(s.walkwayHandle == 0u && s.retiredDeckHandle == 0u && s.retiredWallHandle == 0u && s.retireAtMs == 0u);
        // the replaced zone goes after its landing pass and before the new zone's first (one tick later)
        CHECK(kRetireDelayMs > 0u && kRetireDelayMs < kBurnTickMs);
    }

    // R2 S-2: the side walkways aft of the sterncastle face burn from stripe 0's landing (7 s) to the end, as one
    // zone that meets the burning deck at the face; points on both walkways are covered from 7 s on, never before.
    void TestAftWalkways()
    {
        Strip const w = AftWalkways();
        CHECK(Near(w.xHi, kAftWalkwayX) && Near(w.xLo, kFrontStartX));
        CHECK(Near(w.xLo, StripeRect(0).xHi));      // no gap to the deck
        CHECK(w.length / w.width >= 0.25f && w.length / w.width <= 64.f);     // the marker ladder's aspects
        Vec2 const west{ -45.f, -806.f };
        Vec2 const east{ -45.f, -832.f };
        for (std::uint32_t t = 0; t <= kTimerMs; t += 250)
        {
            bool const burning = StripesLandedBy(t) > 0;     // FrontLanded k == 0 registers it
            CHECK(burning == (t >= FrontLandMs(0)));
            CHECK(!burning || (w.Contains(west) && w.Contains(east)));
            // the deck zone never reaches them
            if (std::optional<Strip> const deck = BurntDeck(StripesLandedBy(t)))
                CHECK(!deck->Contains(west) && !deck->Contains(east));
        }
        CHECK(FrontLandMs(0) == 7000u);
    }
}

int main()
{
    TestSlice();
    TestSchedule();
    TestFireFront();
    TestMast();
    TestDeckMask();
    TestPowder();
    TestShip();
    TestKeg();
    TestTuning();
    TestAftWalkways();
    return Report("hard_mode_test");
}
