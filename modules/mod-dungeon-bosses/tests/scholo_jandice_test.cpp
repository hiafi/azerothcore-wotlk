// Host tests for JandiceLogic.h (S1: Jandice Barov (10503)): the slice, the arena, the cast cadence, the Shell Game
// clock and find rule, the ring, the normal sigil points, the shuffle pairs and the Bloodlines reflection spots.
#include "JandiceLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <utility>
#include <string>
#include <vector>

using namespace ScholomanceRework;
using namespace ScholoJandice;

namespace
{
    // A small deterministic generator (the tests never touch the engine's random).
    struct Lcg
    {
        std::uint32_t state = 12345u;

        std::uint32_t Next()
        {
            state = state * 1664525u + 1013904223u;
            return state >> 8;
        }

        float Unit01() { return float(Next() % 1000000u) / 1000000.f; }
        std::uint32_t Below(std::uint32_t n) { return n ? Next() % n : 0; }
    };

    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // Steps the cadence in 100 ms ticks for `ms`, recording each cast with its time.
    struct CastAt
    {
        JandiceCast cast;
        std::uint32_t at;
    };

    std::vector<CastAt> Run(JandiceClock& clock, std::uint32_t& now, std::uint32_t ms, bool castsLive = false)
    {
        std::vector<CastAt> out;
        for (std::uint32_t t = 0; t < ms; t += 100)
        {
            now += 100;
            JandiceCast const c = clock.Update(100, castsLive);
            if (c != JandiceCast::None)
                out.push_back({ c, now });
        }
        return out;
    }

    // The registry's ExceptOne layout (mod-boss-mechanics MechanicMath.h CoverLaneOffsets): ceil(span / width) lanes,
    // the last clamped inside.
    std::vector<float> CoverOffsets(float span, float width)
    {
        std::uint32_t const n = std::uint32_t(std::ceil(span / width - 1e-4f));
        std::vector<float> out;
        for (std::uint32_t i = 0; i < n; ++i)
            out.push_back(std::min(i * width, span - width));
        return out;
    }

    void TestIds()
    {
        for (std::uint32_t id : { SPELL_JB_CURSE_OF_BLOOD, SPELL_JB_SHELL_GAME, SPELL_JB_SHATTER, SPELL_JB_SHATTER_LOOK,
            SPELL_JB_UNMASKED, SPELL_JB_BLOOD_SIGIL, SPELL_JB_BLOODLINES, SPELL_JB_BLOOD_PRICE,
            SPELL_JB_REFLECTION_POOF, SPELL_JB_SIGIL_BURST, SPELL_JB_FAKE_POP, SPELL_JB_BLOOD_THREAD,
            SPELL_JB_BLOOD_BEAM })
            CHECK(kSpellSlice.Contains(id));
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kCreaturesReservation.Contains(NPC_SC_REFLECTION));
        // The boss spawns inside her arena.
        CHECK(JandiceArena().Contains(kJandiceSpawn.XY(), kJandiceSpawn.z));
        CHECK(ArenaFor(BOSS_JANDICE).Contains(kJandiceSpawn.XY(), kJandiceSpawn.z));
    }

    void TestNumbers()
    {
        // Build spec JB1-JB9 (normal, heroic).
        CHECK(kSigilWarnMs(false) == 5000 && kSigilWarnMs(true) == 6000);
        CHECK(kSigilPct(false) == 40.f && kSigilPct(true) == 60.f);
        CHECK(kCopies(false) == 8 && kCopies(true) == 15);
        CHECK(kGameLimitMs(false) == 20000 && kGameLimitMs(true) == 25000);
        CHECK(kShatterPct(false) == 25.f && kShatterPct(true) == 40.f);
        CHECK(kFailedWarnMs(false) == 5000 && kFailedWarnMs(true) == 6000);
        CHECK(kFailedPct(false) == 40.f && kFailedPct(true) == 60.f);
        CHECK(kLinesWarnMs(false) == 5000 && kLinesWarnMs(true) == 5000);
        CHECK(kLinesPct(false) == 50.f && kLinesPct(true) == 70.f);
        CHECK(kBloodPricePct == 4.f && kBloodPriceEveryMs == 3000);
        CHECK(kShuffleEveryMs == 5000 && kShufflePairs == 3 && kThreadMs == 1000);
        CHECK(kSigilRadius == 8.f && kRingRadius == 12.f && kLaneWidth == 6.f);
        CHECK(kCurseEveryMs == 30000 && kCurseCastMs == 2000 && kCurseRadius == 10.f);
        CHECK(kCurseFirstMinMs == 3000 && kCurseFirstMaxMs == 11000);
        CHECK(kUnmaskedMs == 8000);
    }

    void TestCadence()
    {
        JandiceClock clock;
        clock.Start();
        std::uint32_t now = 0;
        // The pull: sigils at 8 s, lines at 18 s, the game at 25 s.
        std::vector<CastAt> casts = Run(clock, now, 25000);
        CHECK(casts.size() == 3);
        if (casts.size() == 3)
        {
            CHECK(casts[0].cast == JandiceCast::BloodSigil && casts[0].at == 8000);
            CHECK(casts[1].cast == JandiceCast::Bloodlines && casts[1].at == 18000);
            CHECK(casts[2].cast == JandiceCast::ShellGame && casts[2].at == 25000);
        }
        CHECK(clock.InGame());
        // Nothing while the game runs (its 20 s and the failed game's 5 s circles).
        CHECK(Run(clock, now, 25000).empty());
        // A failed normal game ends 5 s after its 20 s limit (at 50 s): sigils at 56 s, lines at 66 s, the next game
        // at 75 s (50 s start to start).
        clock.GameEnded();
        casts = Run(clock, now, 25000);
        CHECK(casts.size() == 3);
        if (casts.size() == 3)
        {
            CHECK(casts[0].cast == JandiceCast::BloodSigil && casts[0].at == 56000);
            CHECK(casts[1].cast == JandiceCast::Bloodlines && casts[1].at == 66000);
            CHECK(casts[2].cast == JandiceCast::ShellGame && casts[2].at == 75000);
        }

        // A due game waits while an outside cast's zones are live, and no outside cast fires meanwhile.
        JandiceClock wait;
        wait.Start();
        std::uint32_t t2 = 0;
        Run(wait, t2, 24000);
        std::vector<CastAt> held = Run(wait, t2, 6000, true);
        CHECK(held.empty());
        CHECK(!wait.InGame());
        std::vector<CastAt> go = Run(wait, t2, 100, false);
        CHECK(go.size() == 1 && go[0].cast == JandiceCast::ShellGame && go[0].at == 30100);
        // Start to start: the next game is 50 s after the delayed start.
        CHECK(wait.UntilGameMs() == kGameEveryMs);

        // A found game early: sigils 6 s later, then the alternation.
        JandiceClock found;
        found.Start();
        std::uint32_t t3 = 0;
        Run(found, t3, 25000);
        Run(found, t3, 3000);
        found.GameEnded();
        std::vector<CastAt> after = Run(found, t3, 16000);
        CHECK(after.size() == 2);
        if (after.size() == 2)
        {
            CHECK(after[0].cast == JandiceCast::BloodSigil && after[0].at == 34000);
            CHECK(after[1].cast == JandiceCast::Bloodlines && after[1].at == 44000);
        }
        CHECK(std::string(CastName(JandiceCast::ShellGame)) == "shell-game");
    }

    void TestGameClock()
    {
        // Normal: no Blood Price, no shuffle, the limit at 20 s.
        ShellGameClock normal;
        normal.Start(false);
        std::uint32_t prices = 0, shuffles = 0, limitAt = 0;
        for (std::uint32_t t = 100; t <= 30000; t += 100)
        {
            GameTick const tick = normal.Update(100);
            prices += tick.prices;
            shuffles += tick.shuffles;
            if (tick.limit)
                limitAt = t;
        }
        CHECK(prices == 0 && shuffles == 0);
        CHECK(limitAt == 20000);
        CHECK(!normal.Running());

        // Heroic: Blood Price at 3..24 s (8 ticks, about 32%), shuffles at 5, 10, 15, 20 s, the limit at 25 s.
        ShellGameClock heroic;
        heroic.Start(true);
        prices = shuffles = limitAt = 0;
        for (std::uint32_t t = 100; t <= 30000; t += 100)
        {
            GameTick const tick = heroic.Update(100);
            prices += tick.prices;
            shuffles += tick.shuffles;
            if (tick.limit)
                limitAt = t;
        }
        CHECK(prices == 8);
        CHECK(shuffles == 4);
        CHECK(limitAt == 25000);

        // A long update still counts every tick it crossed.
        ShellGameClock lag;
        lag.Start(true);
        GameTick const big = lag.Update(7000);
        CHECK(big.prices == 2 && big.shuffles == 1 && !big.limit);
        lag.Stop();
        CHECK(lag.Update(30000).limit == false);
    }

    void TestFinds()
    {
        CHECK(kFindsToEnd(false) == 1 && kFindsToEnd(true) == 2);
        CHECK(FindOutcome(false, 1) == FindResult::UnmaskAndEnd);
        // Q4 (provisional): heroic Unmasked lands at the game's end, the second find.
        CHECK(kHeroicUnmaskAtEnd);
        CHECK(FindOutcome(true, 1) == FindResult::Shuffle);
        CHECK(FindOutcome(true, 2) == FindResult::UnmaskAndEnd);

        // Direct hits (R-A B-1, Q3): a swing, or a harmful damaging spell aimed at the unit, from a player or a pet,
        // on the unit the caster has selected.
        auto spell = [](HitSource src, bool selected)
        {
            HitFacts h;
            h.source = src;
            h.onSelected = selected;
            h.harmful = true;
            h.needsUnitTarget = true;
            h.damage = true;
            return h;
        };
        HitFacts swing;
        swing.source = HitSource::Player;
        swing.onSelected = true;
        swing.melee = true;
        CHECK(CountsAsDirectHit(swing));
        HitFacts petSwing = swing;
        petSwing.source = HitSource::Pet;
        CHECK(CountsAsDirectHit(petSwing));
        CHECK(CountsAsDirectHit(spell(HitSource::Player, true)));      // Frostbolt on her
        CHECK(CountsAsDirectHit(spell(HitSource::Pet, true)));         // the imp's Firebolt
        // A proc or trigger landing on a figure the caster has not selected: Deep Wounds from a Whirlwind crit,
        // Ignite from a Flamestrike, Pestilence's Blood Plague, a seal proc on a Divine Storm target.
        CHECK(!CountsAsDirectHit(spell(HitSource::Player, false)));
        HitFacts offSwing = swing;
        offSwing.onSelected = false;
        CHECK(!CountsAsDirectHit(offSwing));
        // Totems and guardians never count (Searing Totem, Fire Elemental, Feral Spirits).
        CHECK(!kTotemsAndGuardiansCount);
        CHECK(!CountsAsDirectHit(spell(HitSource::Other, true)));
        HitFacts guardianSwing = swing;
        guardianSwing.source = HitSource::Other;
        CHECK(!CountsAsDirectHit(guardianSwing));
        // Chains (Cleave, Multi-Shot, Chain Lightning) and area spells never count, even on her.
        HitFacts chain = spell(HitSource::Player, true);
        chain.chain = true;
        CHECK(!CountsAsDirectHit(chain));
        HitFacts area = spell(HitSource::Player, true);
        area.area = true;
        CHECK(!CountsAsDirectHit(area));
        // Harmful spells that deal no damage (Taunt, Hunter's Mark, Faerie Fire) never count; nor a buff, nor a
        // spell with no unit target.
        HitFacts taunt = spell(HitSource::Player, true);
        taunt.damage = false;
        CHECK(!CountsAsDirectHit(taunt));
        HitFacts buff = spell(HitSource::Player, true);
        buff.harmful = false;
        CHECK(!CountsAsDirectHit(buff));
        HitFacts ground = spell(HitSource::Player, true);
        ground.needsUnitTarget = false;
        CHECK(!CountsAsDirectHit(ground));
        CHECK(kSpellFindDealsDamage && kHitsOnSelectedTargetOnly && !kNonDamageSpellsCount);
    }

    // Q5 (provisional): a bot's guess. On her it stays; else it switches to her under the chance; a guess that is
    // gone picks again. About a 25% chance per second.
    void TestBotGuesses()
    {
        CHECK(kBotFindChance == 0.25f && kBotGuessEveryMs == 1000);
        CHECK(NextGuess(true, true, 0.0f, kBotFindChance) == GuessStep::Keep);
        CHECK(NextGuess(true, true, 0.9f, kBotFindChance) == GuessStep::Keep);
        CHECK(NextGuess(false, true, 0.1f, kBotFindChance) == GuessStep::Her);
        CHECK(NextGuess(false, true, 0.3f, kBotFindChance) == GuessStep::Keep);
        CHECK(NextGuess(false, false, 0.3f, kBotFindChance) == GuessStep::Random);
        CHECK(NextGuess(false, false, 0.1f, kBotFindChance) == GuessStep::Her);
        // Over many seconds one bot finds her at about the chance per second (no instant find).
        Lcg lcg;
        std::uint32_t firstSecond = 0;
        std::uint32_t const trials = 20000;
        for (std::uint32_t t = 0; t < trials; ++t)
            if (NextGuess(false, true, lcg.Unit01(), kBotFindChance) == GuessStep::Her)
                ++firstSecond;
        float const rate = float(firstSecond) / float(trials);
        CHECK(rate > 0.23f && rate < 0.27f);
    }

    void TestRing()
    {
        // Where she stands at the pull (her alcove): the ring moves into the aisle, onto its middle line.
        Vec2 const center = RingCenter(kJandiceAisle, kJandiceSpawn.XY(), kRingRadius, kRingWallInset);
        CHECK(DungeonKit::InsideFrame(kJandiceAisle, center));
        CHECK(Near(center.y, 94.5f));
        CHECK(Near(center.x, kJandiceSpawn.x, 0.05f));
        // Near an end of the aisle, the ring keeps 13 yd off it.
        Vec2 const end = RingCenter(kJandiceAisle, { 230.f, 90.f }, kRingRadius, kRingWallInset);
        CHECK(Near(end.x, 228.f + 13.f));

        for (bool const heroic : { false, true })
            for (float const start : { 0.f, 0.4f, 1.3f, 2.9f })
            {
                std::vector<Vec2> const ring = RingPoints(kJandiceAisle, center, kRingRadius, kCopies(heroic) + 1,
                    start, kRingWallInset);
                CHECK(ring.size() == kCopies(heroic) + 1);
                float minGap = 1000.f;
                for (std::size_t i = 0; i < ring.size(); ++i)
                {
                    CHECK(DungeonKit::InsideFrame(kJandiceAisle, ring[i]));
                    // The failed game's middle stays safe: no copy's 8 yd circle reaches the ring's centre.
                    CHECK(DungeonKit::Distance(ring[i], center) > kSigilRadius);
                    for (std::size_t j = i + 1; j < ring.size(); ++j)
                        minGap = std::min(minGap, DungeonKit::Distance(ring[i], ring[j]));
                }
                // Figures never stand on top of each other (15 copies flatten against the long walls).
                CHECK(minGap > 2.f);
            }
    }

    void TestSigilPoints()
    {
        Lcg lcg;
        auto rand01 = [&lcg]() { return lcg.Unit01(); };
        std::vector<Vec2> const group{ { 256.f, 94.f }, { 258.f, 96.f }, { 250.f, 90.f }, { 262.f, 99.f },
            { 240.f, 100.f } };
        for (int round = 0; round < 200; ++round)
        {
            std::vector<Vec2> const points = PickSigilPoints(kJandiceAisle, group, kNormalSigils,
                kSigilMinFromPlayers, kSigilMinApart, kSigilFloorInset, rand01);
            CHECK(points.size() == kNormalSigils);
            for (std::size_t i = 0; i < points.size(); ++i)
            {
                CHECK(DungeonKit::InsideFrame(kJandiceAisle, points[i]));
                for (Vec2 const& p : group)
                    CHECK(DungeonKit::Distance(points[i], p) >= kSigilMinFromPlayers);
            }
        }
        // A crowd over the whole floor: fewer points, never one near a player.
        std::vector<Vec2> crowd;
        for (float x = 228.f; x <= 284.f; x += 5.f)
            for (float y = 84.f; y <= 105.f; y += 5.f)
                crowd.push_back({ x, y });
        std::vector<Vec2> const none = PickSigilPoints(kJandiceAisle, crowd, kNormalSigils, kSigilMinFromPlayers,
            kSigilMinApart, kSigilFloorInset, rand01);
        CHECK(none.empty());
    }

    void TestHeroicGrid()
    {
        // Any grid point can be the decoy and stays safe ground: no other grid circle, nor the alcove's, covers it.
        CHECK(kGridSigilRadius == 9.f);
        for (std::size_t d = 0; d < kJandiceSigilGrid.size(); ++d)
        {
            CHECK(DungeonKit::InsideFrame(kJandiceAisle, kJandiceSigilGrid[d]));
            for (std::size_t i = 0; i < kJandiceSigilGrid.size(); ++i)
                if (i != d)
                    CHECK(DungeonKit::Distance(kJandiceSigilGrid[i], kJandiceSigilGrid[d]) > kGridSigilRadius + 1.f);
            CHECK(DungeonKit::Distance(kJandiceAlcoveSigil, kJandiceSigilGrid[d]) > kSigilRadius + 1.f);
        }
        // R-A N-5: the grid leaves no pocket. With any decoy, every floor point no real circle covers lies closer to
        // the decoy's grid point than to any other: the decoy is the only safe ground.
        for (std::size_t d = 0; d < kJandiceSigilGrid.size(); ++d)
        {
            std::uint32_t uncovered = 0;
            for (float fx = 0.f; fx <= kJandiceAisle.sizeX + 0.001f; fx += 0.25f)
                for (float fy = 0.f; fy <= kJandiceAisle.sizeY + 0.001f; fy += 0.25f)
                {
                    Vec2 const p = DungeonKit::FramePoint(kJandiceAisle, fx, fy);
                    bool covered = false;
                    std::size_t nearest = 0;
                    for (std::size_t i = 0; i < kJandiceSigilGrid.size(); ++i)
                    {
                        float const dist = DungeonKit::Distance(p, kJandiceSigilGrid[i]);
                        if (i != d && dist <= kGridSigilRadius)
                            covered = true;
                        if (dist < DungeonKit::Distance(p, kJandiceSigilGrid[nearest]))
                            nearest = i;
                    }
                    if (covered)
                        continue;
                    ++uncovered;
                    CHECK(nearest == d);
                }
            CHECK(uncovered > 0);
        }
        // The alcove circle stays off the aisle frame (y 84 on).
        CHECK(kJandiceAlcoveSigil.y + kSigilRadius < 84.f);
        CHECK(JandiceArena().Contains(kJandiceAlcoveSigil, kJandiceFloorZ));
    }

    void TestShuffle()
    {
        Lcg lcg;
        auto rand = [&lcg](std::uint32_t n) { return lcg.Below(n); };
        for (int round = 0; round < 200; ++round)
        {
            auto const pairs = ShufflePairs(16, kShufflePairs, std::nullopt, rand);
            CHECK(pairs.size() == 3);
            std::set<std::size_t> seen;
            for (auto const& [a, b] : pairs)
            {
                CHECK(a != b && a < 16 && b < 16);
                seen.insert(a);
                seen.insert(b);
            }
            CHECK(seen.size() == 6);

            std::size_t const her = lcg.Below(9);
            auto const forced = ShufflePairs(9, kShufflePairs, her, rand);
            CHECK(!forced.empty() && forced[0].first == her && forced[0].second != her);
        }
        CHECK(ShufflePairs(1, 3, std::nullopt, rand).empty());
        CHECK(ShufflePairs(3, 3, std::nullopt, rand).size() == 1);
        CHECK(ShufflePairs(2, 3, std::size_t(1), rand).size() == 1);
    }

    void TestLanes()
    {
        // Across the 21 yd aisle (lanes along X): 4 lanes, the last clamped at 15 (3 yd over the third).
        std::vector<float> const across = CoverOffsets(kJandiceAisle.sizeY, kLaneWidth);
        CHECK(across.size() == 4 && Near(across[3], 15.f));
        // Along the 55.5 yd frame (lanes along Y): 10 lanes, the last clamped at 49.5.
        std::vector<float> const along = CoverOffsets(kJandiceAisle.sizeX, kLaneWidth);
        CHECK(along.size() == 10 && Near(along[9], 49.5f));

        for (std::vector<float> const* layout : { &across, &along })
            for (std::size_t freeIndex = 0; freeIndex < layout->size(); ++freeIndex)
            {
                std::vector<LaneSlot> slots;
                for (std::size_t i = 0; i < layout->size(); ++i)
                    if (i != freeIndex)
                        slots.push_back({ (*layout)[i], kLaneWidth, false });
                slots.push_back({ (*layout)[freeIndex], kLaneWidth, true });
                std::vector<float> const centers = LaneMarkCenters(slots);
                CHECK(centers.size() == slots.size());
                for (std::size_t i = 0; i < slots.size(); ++i)
                {
                    // Every reflection stands inside its own lane.
                    CHECK(centers[i] >= slots[i].offset - 0.01f && centers[i] <= slots[i].offset + kLaneWidth + 0.01f);
                    if (!slots[i].free)
                        continue;
                    // The free lane's reflection stands on the safe ground: in no real lane's hitbox.
                    for (LaneSlot const& real : slots)
                        if (!real.free)
                            CHECK(centers[i] <= real.offset + 0.01f || centers[i] >= real.offset + kLaneWidth - 0.01f);
                }
            }

        // The pinned case: the last lane free on the 21 yd aisle leaves the strip 18-21; its reflection at 19.5.
        std::vector<LaneSlot> const lastFree{ { 0.f, 6.f, false }, { 6.f, 6.f, false }, { 12.f, 6.f, false },
            { 15.f, 6.f, true } };
        std::vector<float> const c = LaneMarkCenters(lastFree);
        CHECK(Near(c[0], 3.f) && Near(c[1], 9.f) && Near(c[2], 15.f) && Near(c[3], 19.5f));
        // The second lane free: the clamped last lane's reflection stands past the third lane (18-21).
        std::vector<LaneSlot> const secondFree{ { 0.f, 6.f, false }, { 12.f, 6.f, false }, { 15.f, 6.f, false },
            { 6.f, 6.f, true } };
        std::vector<float> const c2 = LaneMarkCenters(secondFree);
        CHECK(Near(c2[0], 3.f) && Near(c2[1], 15.f) && Near(c2[2], 19.5f) && Near(c2[3], 9.f));

        // Lane ends sit inside the frame, on the chosen wall, facing down the lane.
        Vec2 const nearX = LaneEndPoint(kJandiceAisle, true, 9.f, false, kLaneEndInset);
        Vec2 const farX = LaneEndPoint(kJandiceAisle, true, 9.f, true, kLaneEndInset);
        CHECK(Near(nearX.x, 229.f) && Near(nearX.y, 93.f) && Near(farX.x, 282.5f));
        Vec2 const nearY = LaneEndPoint(kJandiceAisle, false, 27.f, false, kLaneEndInset);
        Vec2 const farY = LaneEndPoint(kJandiceAisle, false, 27.f, true, kLaneEndInset);
        CHECK(Near(nearY.x, 255.f) && Near(nearY.y, 85.f) && Near(farY.y, 104.f));
        CHECK(Near(LaneFacing(kJandiceAisle, true, false), 0.f));
        CHECK(Near(LaneFacing(kJandiceAisle, true, true), DungeonKit::kPi));
        CHECK(Near(LaneFacing(kJandiceAisle, false, false), DungeonKit::kPi * 0.5f));
        CHECK(Near(LaneFacing(kJandiceAisle, false, true), DungeonKit::kPi * 1.5f));
        for (Vec2 const p : { nearX, farX, nearY, farY })
            CHECK(DungeonKit::InsideFrame(kJandiceAisle, p) && JandiceArena().Contains(p, kJandiceFloorZ));

        // R-A S-9: the boss's lane width tiles each axis with whole lanes, so no lane is clamped over its neighbor
        // and every free lane is a full lane wide (9 of 6.17 yd across the 55.5 yd aisle, 4 of 5.25 yd along).
        float const wAcross = LaneWidthFor(kJandiceAisle.sizeX, kLaneWidth);
        float const wAlong = LaneWidthFor(kJandiceAisle.sizeY, kLaneWidth);
        CHECK(Near(wAcross, 55.5f / 9.f) && Near(wAlong, 5.25f));
        for (auto const& [span, w] : { std::pair{ kJandiceAisle.sizeX, wAcross }, std::pair{ kJandiceAisle.sizeY,
            wAlong } })
        {
            std::vector<float> const layout = CoverOffsets(span, w);
            CHECK(layout.size() == std::size_t(std::lround(span / w)));
            for (std::size_t i = 0; i < layout.size(); ++i)
                CHECK(Near(layout[i], float(i) * w));     // no clamp
            CHECK(Near(layout.back() + w, span));
            CHECK(w >= 5.f);
        }
    }
}

int main()
{
    TestIds();
    TestNumbers();
    TestCadence();
    TestGameClock();
    TestFinds();
    TestBotGuesses();
    TestRing();
    TestSigilPoints();
    TestHeroicGrid();
    TestShuffle();
    TestLanes();
    return Report("scholo_jandice_test");
}
