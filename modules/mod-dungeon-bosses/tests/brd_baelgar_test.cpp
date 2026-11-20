// Host tests for BaelgarLogic.h (D13: Bael'Gar): the slice, the text groups, the spec's numbers, the arena and the
// cracks inside it, the timeline (the first beats, the cadences, "nothing lands during the Furnace's cast", the
// Boulders each Furnace finds), the crack list (the Boulder that falls in, the Rockfall spots off the cracks), the
// bearing choice, the floor probe and the Rockfall's circle counts.
#include "BaelgarLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdBaelgar;
using DungeonKit::Advance;
using DungeonKit::Vec2;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    // One start of a beat, as the engine's UpdateAI runs it: the Furnace first, then the Rockfall, then the Fissure,
    // every 100 ms; the wave ends (the Boulders melt) at the cast's end.
    struct Fire
    {
        std::uint64_t at = 0;
        Beat beat = Beat::Rockfall;
    };

    struct Replay
    {
        std::vector<Fire> fires;
        std::vector<std::uint64_t> waveEnds;
    };

    Replay Run(bool heroic, std::uint64_t horizonMs)
    {
        Replay out;
        Timeline t;
        t.Start(heroic, 0);
        for (std::uint64_t now = 0; now <= horizonMs; now += 100)
        {
            if (t.furnaceLive && now >= t.waveEnd)
            {
                out.waveEnds.push_back(now);
                t.WaveEnded();
            }
            for (Beat const beat : { Beat::Furnace, Beat::Rockfall, Beat::Fissure })
                if (t.Due(beat, now))
                {
                    t.Fired(beat, now);
                    out.fires.push_back({ now, beat });
                }
        }
        return out;
    }

    std::vector<std::uint64_t> Times(Replay const& r, Beat beat)
    {
        std::vector<std::uint64_t> out;
        for (Fire const& f : r.fires)
            if (f.beat == beat)
                out.push_back(f.at);
        return out;
    }

    void TestSliceAndTexts()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation, and are distinct.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        std::set<std::uint32_t> const ids{ SPELL_BG_MAGMA_SPLASH, SPELL_BG_ROCKFALL, SPELL_BG_FALLING_BOULDER,
            SPELL_BG_MOLTEN_FURNACE_CAST, SPELL_BG_MOLTEN_FURNACE, SPELL_BG_FISSURE_CAST, SPELL_BG_FISSURE,
            SPELL_BG_FISSURE_LAVA, SPELL_BG_ROCKFALL_LOOK, SPELL_BG_BOULDER_LAND_LOOK, SPELL_BG_BOULDER_MELT_LOOK,
            SPELL_BG_FISSURE_BURST_LOOK, SPELL_BG_FISSURE_LAVA_LOOK };
        CHECK(ids.size() == 13);
        for (std::uint32_t id : ids)
            CHECK(kSpellSlice.Contains(id));
        CHECK(*ids.begin() == 211230);
        CHECK(*ids.rbegin() == 211242);

        // The text groups sit in the header's range (9016 0-3, all new).
        TextRange const* bg = nullptr;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_BAELGAR)
                bg = &r;
        CHECK(bg != nullptr);
        if (bg)
        {
            for (std::uint8_t g : { EMOTE_BAELGAR_FURNACE, EMOTE_BAELGAR_MELT, EMOTE_BAELGAR_FISSURE,
                EMOTE_BAELGAR_BOULDER })
                CHECK(g >= bg->first && g <= bg->last);
            CHECK(bg->first == 0 && bg->last == 3);
        }
        CHECK(GO_BRD_FALLEN_BOULDER == 301281);
        CHECK(BOSS_BAELGAR == 8);
    }

    void TestSpecNumbers()
    {
        // S2 "New mechanics" and "Build spec": damage N / H and cadences.
        CHECK(kRockfallPct.normal == 15.f && kRockfallPct.heroic == 25.f);
        CHECK(kBoulderPct.normal == 40.f && kBoulderPct.heroic == 60.f);
        // R-1-B m11 (orchestrator default): the Boulder's carrier is never the tank; the Rockfall circles are.
        CHECK(kBoulderCarrierNonTank);
        CHECK(!kRockfallNonTank);
        CHECK(kFurnacePct.normal == 80.f && kFurnacePct.heroic == 95.f);
        CHECK(kFissurePct.normal == 25.f && kFissurePct.heroic == 40.f);
        CHECK(kLavaPctPerTick.normal == 6.f && kLavaPctPerTick.heroic == 6.f);
        CHECK(kRockfallFirstMs == 5000 && kRockfallEveryMs.normal == 15000 && kRockfallEveryMs.heroic == 12000);
        CHECK(kFurnaceFirstMs == 40000 && kFurnaceEveryMs.normal == 40000 && kFurnaceEveryMs.heroic == 35000);
        CHECK(kFissureFirstMs == 15000 && kFissureEveryMs.normal == 30000 && kFissureEveryMs.heroic == 20000);
        CHECK(kRockfallCircles == 5 && Near(kRockfallRadiusYd, 3.f) && kRockfallWarnMs == 1500);
        CHECK(Near(kBoulderRadiusYd, 8.f) && kBoulderWarnMs == 3000);
        CHECK(kFurnaceCastMs == 5000 && kFissureWarnMs == 2000);
        CHECK(Near(kFissureWidthYd, 4.f) && Near(kFissureLengthYd, 40.f));
        CHECK(kBoulderDisplay == 3711);
        // The Boulder's lose distance: the crack's half width and the footprint.
        CHECK(Near(kBoulderLoseYd, 4.5f));
        // The Furnace stays below lethal for a full health player (S2 "Single failure"): 95% at most.
        CHECK(kFurnacePct.heroic < 100.f);
        // The Boulder's marker is the longest warning of the Rockfall beat (the timeline holds the beat by it).
        CHECK(kBoulderWarnMs >= kRockfallWarnMs);
    }

    void TestArenaAndPoints()
    {
        // Bael'Gar spawns kBaelgarSpawn, inside the arena; the tank holds him at kBaelgarFightSpot.
        CHECK(BaelgarArena().Contains(kBaelgarSpawn.XY(), kBaelgarSpawn.z));
        CHECK(ArenaFor(BOSS_BAELGAR).Contains(kBaelgarSpawn.XY(), kBaelgarSpawn.z));
        CHECK(BaelgarArena().Contains(kBaelgarFightSpot.XY(), kBaelgarFightSpot.z));
        CHECK(ArenaFor(BOSS_BAELGAR).Contains(kBaelgarFightSpot.XY(), kBaelgarFightSpot.z));
        // The leash circle's radius constant is the arena's (a point just inside is in, just outside is out).
        Vec2 const center = kBaelgarFightSpot.XY();
        CHECK(BaelgarArena().Contains({ center.x + kArenaRadiusYd - 0.1f, center.y }, kBaelgarFightSpot.z));
        CHECK(!BaelgarArena().Contains({ center.x + kArenaRadiusYd + 0.1f, center.y }, kBaelgarFightSpot.z));
        // A crack of 40 yd from the fight spot ends inside the leash circle in every direction once clipped to the
        // rim: CrackLength takes the ray to the rim less the inset.
        for (std::uint32_t i = 0; i < 8; ++i)
        {
            float const bearing = float(i) * DungeonKit::kTwoPi / 8.f;
            std::optional<float> const edge = DungeonKit::RayToCircleEdge(center, kArenaRadiusYd, center, bearing);
            CHECK(edge.has_value());
            float const length = CrackLength(kFissureLengthYd, edge);
            CHECK(Near(length, 35.f));
            Crack const crack{ center, bearing, length };
            CHECK(BaelgarArena().Contains(CrackEnd(crack), kBaelgarFightSpot.z));
        }
        // From the spawn (25 yd off the centre) the same ray is shorter on the far side and the crack follows it.
        Vec2 const spawn = kBaelgarSpawn.XY();
        float const toward = DungeonKit::BearingTo(spawn, center);
        float const away = toward + DungeonKit::kPi;
        float const near = *DungeonKit::RayToCircleEdge(center, kArenaRadiusYd, spawn, away);
        float const far = *DungeonKit::RayToCircleEdge(center, kArenaRadiusYd, spawn, toward);
        CHECK(near < far);
        CHECK(CrackLength(kFissureLengthYd, near) < CrackLength(kFissureLengthYd, far) + 0.01f);
        CHECK(Near(CrackLength(kFissureLengthYd, near), std::min(40.f, near - kArenaInsetYd)));
        // No arena (the origin outside it): the floor's length and the cap rule alone.
        CHECK(Near(CrackLength(22.f, std::nullopt), 22.f));
        CHECK(Near(CrackLength(80.f, std::nullopt), 40.f));
        CHECK(Near(CrackLength(30.f, 20.f), 19.f));
        CHECK(Near(CrackLength(30.f, 0.5f), 0.f));
    }

    void TestCadenceMath()
    {
        CHECK(NextPlanned(5000, 15000, 5000) == 20000);
        CHECK(NextPlanned(5000, 15000, 19999) == 20000);
        CHECK(NextPlanned(5000, 15000, 20000) == 35000);       // a fired beat never fires again at its own time
        CHECK(NextPlanned(80000, 15000, 85000) == 95000);      // deferred 5 s: the grid keeps its phase
        CHECK(NextPlanned(5000, 15000, 100000) == 110000);     // a long stall skips the missed beats
        CHECK(NextPlanned(5000, 0, 100) == 5000);              // no cadence: no loop
    }

    void TestFirstBeats()
    {
        // The pull is 0: Rockfall 5 s, Fissure 15 s, Furnace 40 s (both difficulties).
        for (bool const heroic : { false, true })
        {
            Timeline t;
            t.Start(heroic, 12345);
            CHECK(t.PlannedAt(Beat::Rockfall) == 12345 + 5000);
            CHECK(t.PlannedAt(Beat::Fissure) == 12345 + 15000);
            CHECK(t.PlannedAt(Beat::Furnace) == 12345 + 40000);
            CHECK(!t.Due(Beat::Rockfall, 12345 + 4999));
            CHECK(t.Due(Beat::Rockfall, 12345 + 5000));
            CHECK(!t.Due(Beat::Furnace, 12345 + 39999));
            CHECK(t.Due(Beat::Furnace, 12345 + 40000));
            CHECK(!t.furnaceLive);
        }
        // Normal: the Rockfalls at 5, 20, 35 give the first Furnace its Boulders (S2 "The cover loop"); heroic 5, 17,
        // 29 (and the one at 41 waits for the wave).
        Replay const n = Run(false, 60000);
        std::vector<std::uint64_t> const rn = Times(n, Beat::Rockfall);
        CHECK(rn.size() >= 4 && rn[0] == 5000 && rn[1] == 20000 && rn[2] == 35000 && rn[3] == 50000);
        Replay const h = Run(true, 60000);
        std::vector<std::uint64_t> const rh = Times(h, Beat::Rockfall);
        CHECK(rh.size() >= 4 && rh[0] == 5000 && rh[1] == 17000 && rh[2] == 29000 && rh[3] == 45000);
    }

    void TestCadences()
    {
        for (bool const heroic : { false, true })
        {
            Replay const r = Run(heroic, 600000);
            std::vector<std::uint64_t> const furnaces = Times(r, Beat::Furnace);
            std::uint32_t const every = kFurnaceEveryMs(heroic);
            CHECK(furnaces.size() >= 10);
            for (std::size_t i = 0; i < furnaces.size(); ++i)
                CHECK(furnaces[i] == 40000 + i * every);        // the Furnace never waits
            // One wave ends per Furnace, 5 s after its cast starts.
            CHECK(r.waveEnds.size() >= furnaces.size() - 1);
            for (std::size_t i = 0; i < r.waveEnds.size() && i < furnaces.size(); ++i)
                CHECK(r.waveEnds[i] == furnaces[i] + kFurnaceCastMs);
            // The Fissures keep their grid (15 s then every 30 s / 20 s) except those that wait for a wave.
            std::vector<std::uint64_t> const fissures = Times(r, Beat::Fissure);
            std::uint32_t const fissureEvery = kFissureEveryMs(heroic);
            for (std::uint64_t const at : fissures)
            {
                std::uint64_t const grid = 15000 + ((at > 15000 ? at - 15000 : 0) / fissureEvery) * fissureEvery;
                std::uint64_t const late = at - grid;
                CHECK(late == 0 || late <= kFurnaceCastMs);     // on the grid, or held up by one cast at most
            }
            std::vector<std::uint64_t> const rockfalls = Times(r, Beat::Rockfall);
            std::uint32_t const rockEvery = kRockfallEveryMs(heroic);
            for (std::uint64_t const at : rockfalls)
            {
                std::uint64_t const grid = 5000 + ((at > 5000 ? at - 5000 : 0) / rockEvery) * rockEvery;
                CHECK(at - grid <= kFurnaceCastMs + kBoulderWarnMs);
            }
            // Roughly the cadence's count over ten minutes.
            CHECK(rockfalls.size() >= 600000 / rockEvery - 2);
            CHECK(fissures.size() >= 600000 / fissureEvery - 3);
        }
    }

    void TestNothingLandsDuringTheCast()
    {
        for (bool const heroic : { false, true })
        {
            Replay const r = Run(heroic, 600000);
            std::vector<std::uint64_t> const furnaces = Times(r, Beat::Furnace);
            for (std::uint64_t const cast : furnaces)
            {
                std::uint64_t const waveEnd = cast + kFurnaceCastMs;
                // A Rockfall's Boulder (3 s), its circles (1.5 s) and a Fissure's stomp (2 s) resolve at fire + warn:
                // never inside (cast, waveEnd); a Rockfall or a Fissure starting inside the cast does not exist.
                for (std::uint64_t const at : Times(r, Beat::Rockfall))
                {
                    CHECK(!(at + kBoulderWarnMs > cast && at < waveEnd));
                    CHECK(!(at + kRockfallWarnMs > cast && at + kRockfallWarnMs < waveEnd));
                }
                for (std::uint64_t const at : Times(r, Beat::Fissure))
                    CHECK(!(at + kFissureWarnMs > cast && at < waveEnd));
            }
        }
        // The window in hand: due at the Furnace's own start, a beat waits; due at the wave's end, it goes.
        Timeline t;
        t.Start(false, 0);
        t.rockfallAt = 80000;
        t.furnaceAt = 80000;
        CHECK(!t.Due(Beat::Rockfall, 80000));       // the Furnace is due now: the window is [80, 85)
        CHECK(!t.Due(Beat::Rockfall, 84999));
        CHECK(t.Due(Beat::Furnace, 80000));
        t.Fired(Beat::Furnace, 80000);
        CHECK(t.furnaceLive && t.castStart == 80000 && t.waveEnd == 85000 && t.furnaceAt == 120000);
        CHECK(!t.Due(Beat::Rockfall, 80000));
        CHECK(!t.Due(Beat::Rockfall, 84999));
        CHECK(t.Due(Beat::Rockfall, 85000));        // the wave's end
        CHECK(!t.Due(Beat::Furnace, 90000));        // never two live Furnaces
        t.WaveEnded();
        CHECK(!t.furnaceLive);
        // A beat just before the cast whose marker would still be up when it starts waits as well; one that resolves
        // exactly at the cast's start does not.
        Timeline u;
        u.Start(false, 0);
        u.furnaceAt = 40000;
        u.rockfallAt = 0;
        CHECK(!u.Due(Beat::Rockfall, 37001));       // 37.001 + 3 s lands after 40 s
        CHECK(u.Due(Beat::Rockfall, 37000));        // lands at 40 s: before the cast
        u.fissureAt = 0;
        CHECK(!u.Due(Beat::Fissure, 38001));
        CHECK(u.Due(Beat::Fissure, 38000));
        // A refused start tries again later; the planned time never moves back.
        u.Retry(Beat::Rockfall, 1000);
        CHECK(u.PlannedAt(Beat::Rockfall) == 2000);
        u.Retry(Beat::Rockfall, 0);
        CHECK(u.PlannedAt(Beat::Rockfall) == 2000);
    }

    void TestBouldersEachFurnaceFinds()
    {
        // "The cover loop": Rockfalls give about 3 Boulders before the first Furnace; each Boulder lands 3 s after its
        // Rockfall starts and lives to the next wave's end. Count the Boulders standing when each Furnace starts.
        for (bool const heroic : { false, true })
        {
            Replay const r = Run(heroic, 400000);
            std::vector<std::uint64_t> const furnaces = Times(r, Beat::Furnace);
            std::vector<std::uint64_t> const rockfalls = Times(r, Beat::Rockfall);
            std::vector<std::size_t> found;
            for (std::size_t i = 0; i < furnaces.size(); ++i)
            {
                std::uint64_t const from = i == 0 ? 0 : furnaces[i - 1] + kFurnaceCastMs;
                std::size_t count = 0;
                for (std::uint64_t const at : rockfalls)
                {
                    std::uint64_t const lands = at + kBoulderWarnMs;
                    if (lands > from && lands <= furnaces[i])
                        ++count;
                }
                found.push_back(count);
            }
            CHECK(found.size() >= 8);
            // The first Furnace always finds three.
            CHECK(found[0] == 3);
            if (heroic)
            {
                // Heroic: three every time through the first nine Furnaces; later a Rockfall whose marker would land
                // in a cast (the grids drift against each other) leaves one with two.
                for (std::size_t i = 0; i < found.size(); ++i)
                    CHECK(found[i] == 3 || (i >= 9 && found[i] == 2));
                for (std::size_t i = 0; i < 9; ++i)
                    CHECK(found[i] == 3);
            }
            else
            {
                // Normal: three, except the Furnace whose Rockfall coincides with its cast (the grids meet every 120
                // s: the Rockfall due at 80 s waits for the wave), which finds two (designer question 4).
                for (std::size_t i = 0; i < found.size(); ++i)
                    CHECK(found[i] == ((i % 3 == 1) ? 2u : 3u));
            }
        }
    }

    void TestCracks()
    {
        Crack const crack{ { 100.f, 100.f }, 0.f, 40.f };      // along +x from (100, 100) to (140, 100)
        CHECK(Near(CrackEnd(crack).x, 140.f) && Near(CrackEnd(crack).y, 100.f));
        CHECK(Near(CrackDistance(crack, { 120.f, 103.f }), 3.f));
        CHECK(Near(CrackDistance(crack, { 95.f, 100.f }), 5.f));    // past the start: the distance to the end point
        CHECK(Near(CrackDistance(crack, { 150.f, 100.f }), 10.f));
        std::vector<Crack> const none;
        CHECK(!BoulderLost(none, { 120.f, 100.f }));
        std::vector<Crack> const cracks{ crack };
        // On the axis and within the crack's half width plus the footprint: lost; just beyond: stands.
        CHECK(BoulderLost(cracks, { 120.f, 100.f }));
        CHECK(BoulderLost(cracks, { 120.f, 104.4f }));
        CHECK(BoulderLost(cracks, { 120.f, 95.6f }));
        CHECK(!BoulderLost(cracks, { 120.f, 104.6f }));
        CHECK(!BoulderLost(cracks, { 120.f, 95.4f }));
        CHECK(BoulderLost(cracks, { 143.f, 100.f }));               // off the end by less than the margin
        CHECK(!BoulderLost(cracks, { 146.f, 100.f }));
        CHECK(OnCrack(cracks, { 120.f, 108.f }, 8.f));
        CHECK(!OnCrack(cracks, { 120.f, 108.f }, 7.9f));
        // Two cracks: either one takes it.
        std::vector<Crack> const two{ crack, { { 100.f, 100.f }, DungeonKit::kPi / 2.f, 40.f } };
        CHECK(BoulderLost(two, { 100.f, 120.f }));
        CHECK(!BoulderLost(two, { 80.f, 80.f }));

        // The avoid circles cover the axis from end to end and nothing else.
        std::vector<DungeonKit::AvoidCircle> const circles = CrackAvoidCircles(cracks, 5.f, 4.f);
        CHECK(circles.size() == 11);                    // 0, 4 ... 40
        for (DungeonKit::AvoidCircle const& c : circles)
            CHECK(Near(c.radius, 5.f) && Near(c.center.y, 100.f));
        CHECK(Near(circles.front().center.x, 100.f) && Near(circles.back().center.x, 140.f));
        DungeonKit::FloorSpotRules rules;
        rules.avoid = circles;
        // A point on the crack scores as inside an avoid circle; one 8 yd off the axis does not.
        CHECK(!DungeonKit::ScoreFloorSpot(rules, { 122.f, 100.f }).Full());
        CHECK(DungeonKit::ScoreFloorSpot(rules, { 122.f, 108.f }).Full());
        CHECK(CrackAvoidCircles(none, 5.f).empty());
    }

    void TestBearingChoice()
    {
        CHECK(Near(BearingGapDeg(0.f, 0.f), 0.f));
        CHECK(Near(BearingGapDeg(0.1f, DungeonKit::kTwoPi - 0.1f), 0.2f * 180.f / DungeonKit::kPi, 0.01f));
        CHECK(Near(BearingGapDeg(0.f, DungeonKit::kPi), 180.f, 0.01f));
        CHECK(Near(BearingGapDeg(1.f, 2.f), 180.f / DungeonKit::kPi, 0.01f));
        CHECK(Near(MinBearingGapDeg(1.f, {}), 180.f));
        CHECK(Near(MinBearingGapDeg(0.f, { 1.f, 3.f, 6.f }), 0.2831853f * 180.f / DungeonKit::kPi, 0.01f));

        auto ring = [](std::vector<float> const& lengths)
        {
            std::vector<FissureCandidate> out;
            for (std::size_t i = 0; i < lengths.size(); ++i)
                out.push_back({ float(i) * DungeonKit::kTwoPi / float(lengths.size()), lengths[i] });
            return out;
        };
        // All full, no cracks yet: any of the eight, by the roll.
        std::vector<FissureCandidate> const full = ring({ 38, 38, 38, 38, 38, 38, 38, 38 });
        std::set<std::size_t> picked;
        for (std::uint32_t roll = 0; roll < 8; ++roll)
            picked.insert(*ChooseFissure(full, {}, roll));
        CHECK(picked.size() == 8);
        // A crack at bearing 0 already: the candidate on top of it is out.
        std::vector<float> const priors{ 0.f };
        for (std::uint32_t roll = 0; roll < 16; ++roll)
        {
            std::size_t const i = *ChooseFissure(full, priors, roll);
            CHECK(i != 0);
        }
        // Short ones lose to full ones even when the short ones are the spread ones.
        std::vector<FissureCandidate> const mixed = ring({ 38, 20, 20, 20, 20, 20, 20, 20 });
        for (std::uint32_t roll = 0; roll < 8; ++roll)
            CHECK(*ChooseFissure(mixed, {}, roll) == 0);
        // Only the full one is on top of the crack: tier 2 (full, not spread) beats a spread short one.
        for (std::uint32_t roll = 0; roll < 8; ++roll)
            CHECK(*ChooseFissure(mixed, priors, roll) == 0);
        // No full length: the 14 yd floor tier, spread first.
        std::vector<FissureCandidate> const shorts = ring({ 20, 20, 10, 10, 10, 10, 10, 10 });
        for (std::uint32_t roll = 0; roll < 8; ++roll)
            CHECK(*ChooseFissure(shorts, priors, roll) == 1);
        // Nothing reaches 14: the longest of at least 6 yd.
        std::vector<FissureCandidate> const stubs = ring({ 8, 10, 12, 7, 6, 3, 2, 0 });
        CHECK(*ChooseFissure(stubs, {}, 3) == 2);
        // Nothing opens at all: nullopt (the stomp tries again).
        CHECK(!ChooseFissure(ring({ 4, 2, 0, 0, 0, 0, 0, 0 }), {}, 0).has_value());
        CHECK(!ChooseFissure({}, {}, 0).has_value());
    }

    void TestFloorProbe()
    {
        // A flat floor with a hole from 20 yd out along +x: the crack is the 18 yd before it.
        auto flat = [](Vec2 p) -> std::optional<float>
        {
            if (p.x >= 120.f && p.x < 130.f)
                return std::nullopt;
            return -72.f;
        };
        CHECK(Near(FloorLengthAlong({ 100.f, 100.f }, 0.f, 40.f, 2.f, -72.f, 6.f, flat), 18.f));
        // The same row the other way is all floor.
        CHECK(Near(FloorLengthAlong({ 100.f, 100.f }, DungeonKit::kPi, 40.f, 2.f, -72.f, 6.f, flat), 40.f));
        // A step of more than the band ends it (a wall's top, the level above), a small slope does not.
        auto stepped = [](Vec2 p) -> std::optional<float> { return p.x > 110.f ? -60.f : -72.f; };
        CHECK(Near(FloorLengthAlong({ 100.f, 100.f }, 0.f, 40.f, 2.f, -72.f, 6.f, stepped), 10.f));
        auto sloped = [](Vec2 p) -> std::optional<float> { return -72.f + (p.x - 100.f) * 0.1f; };
        CHECK(Near(FloorLengthAlong({ 100.f, 100.f }, 0.f, 40.f, 2.f, -72.f, 6.f, sloped), 40.f));
        // No floor at all.
        auto nothing = [](Vec2) -> std::optional<float> { return std::nullopt; };
        CHECK(Near(FloorLengthAlong({ 100.f, 100.f }, 0.f, 40.f, 2.f, -72.f, 6.f, nothing), 0.f));
        // The first step off the floor ends it even when floor comes back after (a gap, not a ledge).
        auto gap = [](Vec2 p) -> std::optional<float>
        {
            if (p.x >= 106.f && p.x < 112.f)
                return std::nullopt;
            return -72.f;
        };
        CHECK(Near(FloorLengthAlong({ 100.f, 100.f }, 0.f, 40.f, 2.f, -72.f, 6.f, gap), 4.f));
    }

    void TestRockfallCounts()
    {
        // Five circles in all: 3 (heroic 4) under distinct players, the rest on random spots; the carrier is never
        // under one; a small group gets fewer player circles.
        CHECK(RockfallPlayerCircles(false, 5, true) == 3);
        CHECK(RockfallPlayerCircles(true, 5, true) == 4);
        CHECK(RockfallPlayerCircles(false, 5, false) == 3);
        CHECK(RockfallPlayerCircles(true, 5, false) == 4);
        CHECK(RockfallPlayerCircles(false, 3, true) == 2);
        CHECK(RockfallPlayerCircles(true, 3, true) == 2);
        CHECK(RockfallPlayerCircles(false, 1, true) == 0);
        CHECK(RockfallPlayerCircles(false, 1, false) == 1);
        CHECK(RockfallPlayerCircles(false, 0, false) == 0);
        CHECK(RockfallPlayerCircles(true, 40, true) == 4);
        for (bool const heroic : { false, true })
            for (std::uint32_t players = 0; players <= 6; ++players)
                for (bool const carrier : { false, true })
                {
                    std::uint32_t const onPlayers = RockfallPlayerCircles(heroic, players, carrier);
                    CHECK(onPlayers + RockfallSpotCircles(onPlayers) == kRockfallCircles);
                }
        CHECK(RockfallSpotCircles(3) == 2 && RockfallSpotCircles(4) == 1 && RockfallSpotCircles(0) == 5);
        CHECK(RockfallSpotCircles(9) == 0);
    }

    void TestMagmaSplash()
    {
        // The stock Magma Splash kept: -250 armor, a 30 s Fire DoT every 3 s (10 ticks), the first cast at 8 s, then 10
        // to 14 s. The percent defaults grow with the heroic form.
        CHECK(kMagmaSplashArmor == -250);
        CHECK(kMagmaSplashDotMs / kMagmaSplashTickMs == 10);
        CHECK(kMagmaSplashFirstMs == 8000 && kMagmaSplashEveryMinMs == 10000 && kMagmaSplashEveryMaxMs == 14000);
        CHECK(kMagmaSplashHitPct.heroic > kMagmaSplashHitPct.normal);
        CHECK(kMagmaSplashTickPct.heroic > kMagmaSplashTickPct.normal);
        // The whole DoT never beats one Furnace (it is a tank tax, not a killer).
        CHECK(kMagmaSplashTickPct.heroic * 10.f + kMagmaSplashHitPct.heroic < kFurnacePct.normal);
    }
}

int main()
{
    TestSliceAndTexts();
    TestSpecNumbers();
    TestArenaAndPoints();
    TestCadenceMath();
    TestFirstBeats();
    TestCadences();
    TestNothingLandsDuringTheCast();
    TestBouldersEachFurnaceFinds();
    TestCracks();
    TestBearingChoice();
    TestFloorProbe();
    TestRockfallCounts();
    TestMagmaSplash();

    return Report("brd_baelgar_test");
}
