/*
 * mod-dungeon-bosses, Blackrock Depths D13:
 * Bael'Gar (9016) and the Fallen Boulder (GO 301281), the pure, host-testable part (no engine headers). Build spec S2
 * "Bael'Gar" (docs/dungeons/blackrock-depths-2-shadowforge-city.md, BG1-BG6; rulings 49-51, 88), handoff sections 3.4
 * (row D13), 3.5, 3.6, 3.8 (NM: the cavern centre), 3.9 (the `hide` drill row, tag 16). Tested by
 * tests/brd_baelgar_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsBaelgar (211230-211259), declared in apps/dbc-tools
 *                  source/npcs/blackrock_depths/baelgar.py
 *   Tuning         NH<> constants straight from the build spec (normal / heroic); the unset "stock rescaled" cells
 *                  (Magma Splash) are this WP's defaults (report, designer questions)
 *   Timeline       the clocks (Rockfall, Molten Furnace, Fissure) and the rule "nothing lands during the Furnace's
 *                  cast": a beat due, or one whose marker would still be up when the cast starts, waits for the wave's
 *                  end. The engine runs this very struct; the test replays 400 s of it
 *   Cracks         the Fissure list shared by the Boulder check, the Rockfall spots and the lava zones: a Boulder
 *                  that lands on a crack falls in; a bearing is chosen among eight by floor length and spread
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_BAELGAR_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_BAELGAR_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitFloor.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace BrdBaelgar
{
    using BlackrockDepthsRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsBaelgar;

    enum BaelgarSpells : std::uint32_t
    {
        SPELL_BG_MAGMA_SPLASH        = kSpellSlice.first + 0,    // 211230 BG1 the tank hit + DoT + -250 armor (13880)
        SPELL_BG_ROCKFALL            = kSpellSlice.first + 1,    // 211231 BG2 a circle's hit (resolve copy)
        SPELL_BG_FALLING_BOULDER     = kSpellSlice.first + 2,    // 211232 BG3 the impact's hit (resolve copy)
        SPELL_BG_MOLTEN_FURNACE_CAST = kSpellSlice.first + 3,    // 211233 BG4 the 5 s cast bar
        SPELL_BG_MOLTEN_FURNACE      = kSpellSlice.first + 4,    // 211234 BG4 the wave's hit (resolve copy, Hide)
        SPELL_BG_FISSURE_CAST        = kSpellSlice.first + 5,    // 211235 BG6 the 2 s stomp bar
        SPELL_BG_FISSURE             = kSpellSlice.first + 6,    // 211236 BG6 the crack's hit (resolve copy)
        SPELL_BG_FISSURE_LAVA        = kSpellSlice.first + 7,    // 211237 BG6 the lava's tick (resolve copy)
        SPELL_BG_ROCKFALL_LOOK       = kSpellSlice.first + 8,    // 211238 look: Rock Shower dust at a circle
        SPELL_BG_BOULDER_LAND_LOOK   = kSpellSlice.first + 9,    // 211239 look: the Boulder's impact (shake, sound)
        SPELL_BG_BOULDER_MELT_LOOK   = kSpellSlice.first + 10,   // 211240 look: a Boulder melting (BG5)
        SPELL_BG_FISSURE_BURST_LOOK  = kSpellSlice.first + 11,   // 211241 look: the burst where the crack opens
        SPELL_BG_FISSURE_LAVA_LOOK   = kSpellSlice.first + 12,   // 211242 look: a lava patch (an aura on a stalker)
        // 211243-211259 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_BG_FISSURE_LAVA_LOOK;
    static_assert(kLastSpell <= kSpellSlice.last, "Bael'Gar's spells must stay in his slice");

    // Registry tags. 16 is the G1 drill's `hide` row (BM MechanicDrill.h kBrdTagHide: Bael'Gar BG4, gated at 0 in
    // DRILL_BARS); the others are this fight's own.
    enum BaelgarTags : std::uint32_t
    {
        TAG_BG_ROCKFALL = 1,    // BG2
        TAG_BG_BOULDER  = 2,    // BG3
        TAG_BG_FISSURE  = 3,    // BG6 the crack's hit
        TAG_BG_LAVA     = 4,    // BG6 the lasting lava
        TAG_BG_FURNACE  = 16,   // BG4 (= kBrdTagHide)
    };

    // creature_text groups of 9016 (S2 "Text"; he had none): 0, 1 and 2 are the spec's, 3 the Falling Boulder line
    // (handoff gap 38). Group 0 is a boss emote (type 41), the others emotes (16); all four map-wide (TextRange 3):
    // an emote's own range is 25 yd and the cavern is wider.
    enum BaelgarTexts : std::uint8_t
    {
        EMOTE_BAELGAR_FURNACE = 0,  // BG4 "Bael'Gar stokes the Molten Furnace! Get out of sight!"
        EMOTE_BAELGAR_MELT    = 1,  // BG5 "The boulders melt into slag!"
        EMOTE_BAELGAR_FISSURE = 2,  // BG6 "Bael'Gar slams the ground and the floor cracks open!"
        EMOTE_BAELGAR_BOULDER = 3,  // BG3 "A boulder tears loose from the ceiling!"
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (S2 "Build spec"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------

    // BG2 Rockfall: five 3 yd circles, a 1.5 s marker, every 15 s (heroic 12 s), the first at 5 s.
    inline constexpr NH<float> kRockfallPct{ 15.f, 25.f };
    inline constexpr float kRockfallRadiusYd = 3.f;
    inline constexpr std::uint32_t kRockfallWarnMs = 1500;
    inline constexpr std::uint32_t kRockfallCircles = 5;
    inline constexpr std::uint32_t kRockfallFirstMs = 5000;
    inline constexpr NH<std::uint32_t> kRockfallEveryMs{ 15000, 12000 };
    // "5 small circles at random spots": this many drop under distinct random players (the tank too, ruling 88), the
    // rest on random floor spots of the cavern (designer question 1). The Falling Boulder's carrier is never one.
    inline constexpr NH<std::uint32_t> kRockfallOnPlayers{ 3, 4 };
    inline constexpr float kRockfallSpotRangeYd = 30.f;     // the random spots lie within this of the fight spot
    inline constexpr float kRockfallSpotApartYd = 4.f;      // ... and this far from each other

    // BG3 Falling Boulder: with each Rockfall, an 8 yd impact that follows a random player for 3 s (the carrier takes
    // it to open floor; the carrier is never hit by their own marker), then lands. No Weakened (the spec's penalty cell
    // is empty).
    inline constexpr NH<float> kBoulderPct{ 40.f, 60.f };
    inline constexpr float kBoulderRadiusYd = 8.f;
    // The carrier is never the tank (orchestrator default after R-1-B m11); the Rockfall circles stay tank-inclusive.
    inline constexpr bool kBoulderCarrierNonTank = true;
    inline constexpr bool kRockfallNonTank = false;
    inline constexpr std::uint32_t kBoulderWarnMs = 3000;
    // GO 301281: display 3711 Lavarock01 (about 5 by 5 yd, 10 yd tall). The fallback is 5736 (Lavarock02): change this
    // one constant (the script sets the display at the summon; the template's displayId in the SQL rev must match,
    // lib/test_blackrock_depths_baelgar.py checks it) when the in-game line of sight check of 3711 fails.
    inline constexpr std::uint32_t kBoulderDisplay = 3711;
    inline constexpr float kBoulderFootprintYd = 2.5f;      // the model's half width: the Hide's blocker radius
    inline constexpr std::uint32_t kBoulderBackstopSec = 150;   // a Boulder lives at most two Furnaces
    inline constexpr std::size_t kBoulderCap = 8;           // never more standing at once (a runaway spawn guard)

    // BG4 Molten Furnace: a 5 s cast, then a wave on everyone he can see (real line of sight, BM Hide); every Boulder
    // melts when the wave ends. 40 s after the pull, then every 40 s (heroic 35 s).
    inline constexpr NH<float> kFurnacePct{ 80.f, 95.f };
    inline constexpr std::uint32_t kFurnaceCastMs = 5000;
    inline constexpr std::uint32_t kFurnaceFirstMs = 40000;
    inline constexpr NH<std::uint32_t> kFurnaceEveryMs{ 40000, 35000 };
    inline constexpr float kFurnaceRangeYd = 60.f;          // the Hide's search (the cavern is about 40 yd across)
    // The wave's own resolve must be seen within this of the cast's end, or the script melts the Boulders itself.
    inline constexpr std::uint32_t kMeltBackstopMs = 1500;

    // BG6 Fissure: a 2 s stomp wind-up, then a 4 yd crack about 40 yd long in a random direction, which stays as a lava
    // line for the rest of the fight. 15 s after the pull, then every 30 s (heroic 20 s).
    inline constexpr NH<float> kFissurePct{ 25.f, 40.f };
    inline constexpr NH<float> kLavaPctPerTick{ 6.f, 6.f };     // 6% a second
    inline constexpr float kFissureLengthYd = 40.f;
    inline constexpr float kFissureWidthYd = 4.f;
    inline constexpr std::uint32_t kFissureWarnMs = 2000;
    inline constexpr std::uint32_t kFissureFirstMs = 15000;
    inline constexpr NH<std::uint32_t> kFissureEveryMs{ 30000, 20000 };
    inline constexpr std::uint32_t kLavaTickMs = 1000;
    inline constexpr std::uint32_t kLavaLifeMs = 900000;    // "the fight": 15 minutes, cancelled with the encounter
    inline constexpr float kLavaLookEveryYd = 6.f;          // a lava patch look every 6 yd along a crack (VISUALS)
    inline constexpr std::uint32_t kFissureCandidates = 8;  // the bearings tried, evenly spread from a random offset
    inline constexpr float kFissureMinFullYd = 30.f;        // a crack of this length or more is "full" (NM: 32-40 fit)
    inline constexpr float kFissureMinFloorYd = 14.f;       // under this a bearing is only a last resort
    inline constexpr float kFissureMinSpreadDeg = 25.f;     // cracks this far apart in bearing, if possible
    inline constexpr float kFloorProbeStepYd = 2.f;
    inline constexpr float kFloorProbeBandYd = 6.f;         // a floor probe further off than this is a hole
    inline constexpr float kArenaRadiusYd = 36.f;           // the leash circle round the fight spot (BaelgarArena)
    inline constexpr float kArenaInsetYd = 1.f;             // a crack ends this far inside the leash circle

    // A Boulder whose centre lands this close to a crack's axis falls in and is lost: the crack's half width plus the
    // Boulder's footprint (designer question 3).
    inline constexpr float kBoulderLoseYd = kFissureWidthYd / 2.f + kBoulderFootprintYd;

    // BG1 Magma Splash 13880 (kept, on the tank, rescaled; copy in the slice, rule 15): 8 s after the pull, then every
    // 10 to 14 s. The numbers are unset in the spec ("stock rescaled", gaps 8 and 36): this WP's defaults (designer
    // question 2).
    inline constexpr NH<float> kMagmaSplashHitPct{ 10.f, 15.f };        // the instant Fire hit, of the tank's row
    inline constexpr NH<float> kMagmaSplashTickPct{ 1.5f, 2.5f };       // each 3 s tick of the 30 s Fire DoT
    inline constexpr std::uint32_t kMagmaSplashTickMs = 3000;
    inline constexpr std::uint32_t kMagmaSplashDotMs = 30000;
    inline constexpr std::int32_t kMagmaSplashArmor = -250;             // stock, kept
    inline constexpr std::uint32_t kMagmaSplashFirstMs = 8000;
    inline constexpr std::uint32_t kMagmaSplashEveryMinMs = 10000;
    inline constexpr std::uint32_t kMagmaSplashEveryMaxMs = 14000;
    inline constexpr std::uint32_t kRetryMs = 1000;                     // a refused cast tries again this soon

    // ----------------------------------------------------------------------------------------------------------------
    // Cadence
    // ----------------------------------------------------------------------------------------------------------------

    // The next start of a beat planned at `plannedMs` with cadence `everyMs`, after `nowMs` (a missed beat is skipped,
    // the cadence keeps its phase).
    constexpr std::uint64_t NextPlanned(std::uint64_t plannedMs, std::uint32_t everyMs, std::uint64_t nowMs)
    {
        std::uint64_t next = plannedMs + everyMs;
        while (everyMs && next <= nowMs)
            next += everyMs;
        return next;
    }

    enum class Beat : std::uint8_t
    {
        Rockfall,   // BG2 + BG3
        Furnace,    // BG4
        Fissure,    // BG6
    };

    // The three clocks of the fight, in the AI's own milliseconds (the pull is `Start`'s `now`). "BG2 and BG6 due
    // during BG4's cast wait until its wave ends" (S2 Build spec): the Furnace's window is its cast (kFurnaceCastMs)
    // from the moment it starts, and a beat whose marker would still be up when the cast starts waits too, so nothing
    // lands during the cast. A waiting beat fires at the wave's end; the next one keeps the grid.
    struct Timeline
    {
        bool heroic = false;
        std::uint64_t rockfallAt = 0;   // the next planned start of each beat
        std::uint64_t furnaceAt = 0;
        std::uint64_t fissureAt = 0;
        bool furnaceLive = false;       // a Furnace is casting or its wave has not been resolved yet
        std::uint64_t castStart = 0;    // the live Furnace's cast start
        std::uint64_t waveEnd = 0;      // ... and its wave (the cast's end)

        void Start(bool heroicForm, std::uint64_t now)
        {
            *this = Timeline{};
            heroic = heroicForm;
            rockfallAt = now + kRockfallFirstMs;
            furnaceAt = now + kFurnaceFirstMs;
            fissureAt = now + kFissureFirstMs;
        }

        std::uint64_t PlannedAt(Beat beat) const
        {
            switch (beat)
            {
                case Beat::Rockfall: return rockfallAt;
                case Beat::Furnace:  return furnaceAt;
                case Beat::Fissure:  return fissureAt;
            }
            return 0;
        }

        // `now` is inside the Furnace's cast (or would be by the time a beat's marker of `warnMs` lands).
        bool Blocked(std::uint64_t now, std::uint32_t warnMs) const
        {
            if (furnaceLive && now < waveEnd && now + warnMs > castStart)
                return true;
            return now + warnMs > furnaceAt && now < furnaceAt + kFurnaceCastMs;
        }

        // Planned time reached, and not held by the Furnace's window. The Furnace itself is never held (a cast already
        // going on is the script's to wait for).
        bool Due(Beat beat, std::uint64_t now) const
        {
            if (now < PlannedAt(beat))
                return false;
            switch (beat)
            {
                case Beat::Furnace:  return !furnaceLive;
                case Beat::Rockfall: return !Blocked(now, kBoulderWarnMs);
                case Beat::Fissure:  return !Blocked(now, kFissureWarnMs);
            }
            return false;
        }

        // The beat started at `now`: its clock moves on.
        void Fired(Beat beat, std::uint64_t now)
        {
            switch (beat)
            {
                case Beat::Rockfall:
                    rockfallAt = NextPlanned(rockfallAt, kRockfallEveryMs(heroic), now);
                    break;
                case Beat::Fissure:
                    fissureAt = NextPlanned(fissureAt, kFissureEveryMs(heroic), now);
                    break;
                case Beat::Furnace:
                    furnaceLive = true;
                    castStart = now;
                    waveEnd = now + kFurnaceCastMs;
                    furnaceAt = NextPlanned(furnaceAt, kFurnaceEveryMs(heroic), now);
                    break;
            }
        }

        // A refused start tries again `afterMs` from now (the planned time moves, the grid does not).
        void Retry(Beat beat, std::uint64_t now, std::uint32_t afterMs = kRetryMs)
        {
            switch (beat)
            {
                case Beat::Rockfall: rockfallAt = std::max<std::uint64_t>(rockfallAt, now + afterMs); break;
                case Beat::Furnace:  furnaceAt = std::max<std::uint64_t>(furnaceAt, now + afterMs); break;
                case Beat::Fissure:  fissureAt = std::max<std::uint64_t>(fissureAt, now + afterMs); break;
            }
        }

        // The wave resolved (the Boulders melt): the next Furnace is the one `furnaceAt` names.
        void WaveEnded() { furnaceLive = false; }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Cracks (BG6): the one list the Boulder check, the Rockfall spots and the lava zones share
    // ----------------------------------------------------------------------------------------------------------------

    struct Crack
    {
        Vec2 from;
        float bearing = 0.f;    // radians, the map's orientation
        float length = 0.f;
    };

    inline Vec2 CrackEnd(Crack const& crack)
    {
        return DungeonKit::Advance(crack.from, crack.bearing, crack.length);
    }

    // The distance from `p` to the crack's axis.
    inline float CrackDistance(Crack const& crack, Vec2 p)
    {
        return DungeonKit::SegmentDistance(crack.from, CrackEnd(crack), p);
    }

    // `p` within `withinYd` of any crack's axis.
    inline bool OnCrack(std::vector<Crack> const& cracks, Vec2 p, float withinYd)
    {
        for (Crack const& crack : cracks)
            if (CrackDistance(crack, p) <= withinYd)
                return true;
        return false;
    }

    // BG3: a Boulder that lands on a crack falls in and is lost.
    inline bool BoulderLost(std::vector<Crack> const& cracks, Vec2 p)
    {
        return OnCrack(cracks, p, kBoulderLoseYd);
    }

    // Circles along every crack (every `stepYd`, `radiusYd` round the axis) for a floor-spot pick to stay off them.
    inline std::vector<DungeonKit::AvoidCircle> CrackAvoidCircles(std::vector<Crack> const& cracks, float radiusYd,
        float stepYd = 3.f)
    {
        std::vector<DungeonKit::AvoidCircle> out;
        for (Crack const& crack : cracks)
            for (float s = 0.f; s <= crack.length + 1e-3f; s += stepYd)
                out.push_back({ DungeonKit::Advance(crack.from, crack.bearing, s), radiusYd });
        return out;
    }

    // The smaller angle between two bearings, in degrees [0, 180].
    inline float BearingGapDeg(float a, float b)
    {
        float d = std::fabs(std::fmod(a - b, DungeonKit::kTwoPi));
        if (d > DungeonKit::kPi)
            d = DungeonKit::kTwoPi - d;
        return d * 180.f / DungeonKit::kPi;
    }

    // The smallest gap from `bearing` to any of `priors` (180 with none).
    inline float MinBearingGapDeg(float bearing, std::vector<float> const& priors)
    {
        float gap = 180.f;
        for (float const prior : priors)
            gap = std::min(gap, BearingGapDeg(bearing, prior));
        return gap;
    }

    // How far a crack from `origin` along `bearing` runs over floor: the last `step` multiple up to `maxYd` whose floor
    // (`floor(Vec2)` -> the floor height, nullopt: none) is within `bandYd` of `refZ`; the first miss ends it.
    template <class Floor>
    float FloorLengthAlong(Vec2 origin, float bearing, float maxYd, float stepYd, float refZ, float bandYd,
        Floor&& floor)
    {
        float good = 0.f;
        for (float s = stepYd; s <= maxYd + 1e-3f; s += stepYd)
        {
            std::optional<float> const h = floor(DungeonKit::Advance(origin, bearing, s));
            if (!h || std::fabs(*h - refZ) > bandYd)
                break;
            good = s;
        }
        return good;
    }

    struct FissureCandidate
    {
        float bearing = 0.f;
        float length = 0.f;     // the floor length (clipped to the arena and kFissureLengthYd by the caller)
    };

    // The bearing a crack takes: random (`roll` modulo the count) among the best tier that has any, tiers in order
    //   1. a full length (>= kFissureMinFullYd) and kFissureMinSpreadDeg from every crack so far
    //   2. a full length
    //   3. at least kFissureMinFloorYd and spread
    //   4. at least kFissureMinFloorYd
    //   5. the longest of the rest (a crack of at least 6 yd)
    // nullopt: nothing opens (the stomp is skipped and tries again).
    inline std::optional<std::size_t> ChooseFissure(std::vector<FissureCandidate> const& candidates,
        std::vector<float> const& priors, std::uint32_t roll)
    {
        auto spread = [&](FissureCandidate const& c)
        {
            return MinBearingGapDeg(c.bearing, priors) >= kFissureMinSpreadDeg;
        };
        auto pickTier = [&](auto&& keeps) -> std::optional<std::size_t>
        {
            std::vector<std::size_t> pool;
            for (std::size_t i = 0; i < candidates.size(); ++i)
                if (keeps(candidates[i]))
                    pool.push_back(i);
            if (pool.empty())
                return std::nullopt;
            return pool[roll % pool.size()];
        };
        if (auto tier = pickTier([&](FissureCandidate const& c) { return c.length >= kFissureMinFullYd && spread(c); }))
            return tier;
        if (auto tier = pickTier([&](FissureCandidate const& c) { return c.length >= kFissureMinFullYd; }))
            return tier;
        if (auto tier = pickTier([&](FissureCandidate const& c)
            { return c.length >= kFissureMinFloorYd && spread(c); }))
            return tier;
        if (auto tier = pickTier([&](FissureCandidate const& c) { return c.length >= kFissureMinFloorYd; }))
            return tier;
        std::optional<std::size_t> longest;
        for (std::size_t i = 0; i < candidates.size(); ++i)
            if (candidates[i].length >= 6.f && (!longest || candidates[i].length > candidates[*longest].length))
                longest = i;
        return longest;
    }

    // The crack's length: the floor's, clipped to the leash circle (`arenaEdgeYd`: the ray to its rim from the origin,
    // nullopt when the origin is outside it), at most kFissureLengthYd.
    inline float CrackLength(float floorYd, std::optional<float> arenaEdgeYd)
    {
        float length = std::min(floorYd, kFissureLengthYd);
        if (arenaEdgeYd)
            length = std::min(length, std::max(0.f, *arenaEdgeYd - kArenaInsetYd));
        return length;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Rockfall
    // ----------------------------------------------------------------------------------------------------------------

    // How many of the circles drop under players, given the players on the fight and whether the Boulder's carrier is
    // one of them (the carrier is never under a circle).
    inline std::uint32_t RockfallPlayerCircles(bool heroic, std::uint32_t playersOnFight, bool carrierPicked)
    {
        std::uint32_t const taken = carrierPicked ? 1u : 0u;
        std::uint32_t const available = playersOnFight > taken ? playersOnFight - taken : 0u;
        return std::min({ std::uint32_t{ kRockfallOnPlayers(heroic) }, available, kRockfallCircles });
    }

    // The circles that drop on random floor spots: the rest of the five.
    inline std::uint32_t RockfallSpotCircles(std::uint32_t onPlayers)
    {
        return kRockfallCircles > onPlayers ? kRockfallCircles - onPlayers : 0u;
    }
}

#endif
