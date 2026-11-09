/*
 * mod-dungeon-bosses, Stratholme S9:
 * Magistrate Barthilas (10435), "The Epidemic": the pure, host-testable part (no engine headers). Build spec ST
 * 2355-2407 (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows BT and 3.5 row S9. The engine half is
 * boss_magistrate_barthilas_rework.cpp; the spells and kit creatures are apps/dbc-tools
 * source/npcs/stratholme/magistrate_barthilas.py (same ids). Tested by tests/strat_barthilas_test.cpp.
 *
 * Mechanic ids follow the build spec table (ST 2366-2378): BT1 Infection, BT2 Contagion, BT3 the cough, BT4 Plagued
 * Grain, BT5 the grain pile, BT6 Quarantine, BT7 the purge, BT8 Fever, BT9 Bedlam (heroic), BT10 the cough puddle
 * (heroic), BT11 the stock tank kit.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_BARTHILAS_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_BARTHILAS_LOGIC_H

#include "DungeonKitFloor.h"
#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace StratBarthilas
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsBarthilas;

    // The dbc-tools twins: source/npcs/stratholme/magistrate_barthilas.py (same ids).
    enum BarthilasSpells : std::uint32_t
    {
        SPELL_BT_INFECTION      = 206605,   // BT1 Disease: 4% per 2 s, 10 s (spell_dungeon_refflat_periodic)
        SPELL_BT_COUGH          = 206606,   // BT3 the cough's hit: resolve copy (Nature), 30% / 40% + Weakened
        SPELL_BT_COUGHING       = 206607,   // BT3 the look on the carrier as the cough goes off
        SPELL_BT_RECOVERED      = 206608,   // BT3 10 s after a cough: cannot catch Infection
        SPELL_BT_GRAIN_THROW    = 206609,   // BT4 the thrown sack (a missile at the marker, look only)
        SPELL_BT_GRAIN_IMPACT   = 206610,   // BT4 the landing's hit: resolve copy (Nature), 30% + Weakened
        SPELL_BT_PLAGUE_FOG     = 206611,   // BT5 / BT10 the pile and puddle look (an area aura at the stalker)
        SPELL_BT_PURGE          = 206612,   // BT7 the purge's hit outside both wards: resolve copy (Nature), 40%
        SPELL_BT_FEVER          = 206613,   // BT8 his stacking buff (+5% / +6% damage, +3% attack speed a stack)
        SPELL_BT_BEDLAM         = 206614,   // BT9 heroic: the 3 s kickable cast
    };
    static_assert(kSpellSlice.Contains(SPELL_BT_INFECTION) && kSpellSlice.Contains(SPELL_BT_BEDLAM),
        "BT spells sit in the slice");

    // Registry tags (one per mechanic; the ledger and `.mech` show them).
    enum BarthilasTags : std::uint32_t
    {
        TAG_BT_CONTAGION        = 0x5B0902,     // BT2 the rolling 5 yd RunOut on every carrier (bots only)
        TAG_BT_COUGH            = 0x5B0903,
        TAG_BT_GRAIN            = 0x5B0904,
        TAG_BT_PILE             = 0x5B0905,
        TAG_BT_WARD_SICK        = 0x5B0906,
        TAG_BT_WARD_WELL        = 0x5B0907,
        TAG_BT_PURGE            = 0x5B0908,
        TAG_BT_PUDDLE           = 0x5B090A,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Numbers (ST build spec table; damage in percent of the reference row, N = level 60 normal, H = heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // BT1 Infection
    std::uint32_t constexpr kInfectionFirstMs = 8000;
    std::uint32_t constexpr kInfectionEveryMs = 15000;
    std::uint32_t constexpr kInfectionMs = 10000;               // the aura's duration (the cough lands at its end)
    std::uint32_t constexpr kInfectionTickMs = 2000;
    float constexpr kInfectionTickPct = 4.f;                    // 20% over the course, not avoidable
    inline constexpr NH<std::uint32_t> kPatients{ 1, 2 };       // heroic: two patients

    // BT2 Contagion
    float constexpr kContagionYd = 5.f;
    inline constexpr NH<std::uint32_t> kContagionHoldMs{ 1000, 500 };
    std::uint32_t constexpr kContagionPollMs = 250;
    float constexpr kContagionZYd = 4.f;                        // a carrier on another floor never counts
    // The rolling RunOut for the bots (the Ras pattern): re-registered every kRunOutRefreshMs with a kRunOutWarnMs
    // warning, the old one cancelled before it resolves (telegraph-only, so it would hit nobody anyway).
    std::uint32_t constexpr kRunOutWarnMs = 4000;
    std::uint32_t constexpr kRunOutRefreshMs = 2000;
    static_assert(kRunOutRefreshMs < kRunOutWarnMs, "the rolling RunOut is replaced before it resolves");

    // BT3 the cough
    float constexpr kCoughYd = 8.f;
    inline constexpr NH<float> kCoughPct{ 30.f, 40.f };         // Weakened on both (handoff section 7 #17)
    std::uint32_t constexpr kRecoveredMs = 10000;               // immune to catching it again

    // BT4 Plagued Grain, BT5 the pile
    std::uint32_t constexpr kGrainFirstMs = 12000;
    std::uint32_t constexpr kGrainEveryMs = 20000;
    std::uint32_t constexpr kGrainWarnMs = 2000;
    float constexpr kGrainYd = 6.f;
    float constexpr kGrainPct = 30.f;
    float constexpr kGrainSackSpeed = 20.f;                     // yd/s: the sack's flight (the throw spell's Speed)
    std::uint32_t constexpr kGrainYellEvery = 3;                // "now and then": the 1st, 4th, 7th ... throw
    float constexpr kPileYd = 5.f;
    inline constexpr NH<std::uint32_t> kPileLifeMs{ 30000, 45000 };
    inline constexpr NH<std::uint32_t> kPileCap{ 2, 3 };
    std::uint32_t constexpr kPileGraceMs = 500;                 // standing inside this long catches it
    std::uint32_t constexpr kPileTickMs = 250;

    // BT6 Quarantine, BT7 the purge
    std::uint32_t constexpr kQuarantineFirstMs = 25000;
    std::uint32_t constexpr kQuarantineEveryMs = 30000;
    inline constexpr NH<std::uint32_t> kQuarantineWarnMs{ 5000, 4000 };
    inline constexpr NH<float> kWardYd{ 6.f, 5.f };
    float constexpr kWardEdgeGapYd = 6.f;                       // edge to edge (ruling 36)
    float constexpr kPurgePct = 40.f;                           // no Weakened (ST BT7 lists none; over 30%)
    float constexpr kWardZYd = 4.f;                             // a player this far above or below is not inside
    float constexpr kWardFloorZBand = 2.5f;                     // a ward's floor this far off his is a ruin or a step
    std::uint32_t constexpr kWardBearings = 24;                 // candidate lines over half a turn (7.5 degrees apart)

    // BT8 Fever
    std::uint32_t constexpr kFeverEveryMs = 20000;
    inline constexpr NH<float> kFeverDamagePct{ 5.f, 6.f };     // per stack (the spell's value is the normal one)
    float constexpr kFeverHastePct = 3.f;
    std::uint32_t constexpr kBedlamFever = 5;

    // BT9 Bedlam (heroic)
    std::uint32_t constexpr kBedlamFirstMs = 35000;
    std::uint32_t constexpr kBedlamEveryMs = 30000;
    std::uint32_t constexpr kBedlamCastMs = 3000;
    std::uint8_t constexpr kBedlamKickPriority = 3;

    // BT10 the cough puddle (heroic)
    float constexpr kPuddleYd = 4.f;
    std::uint32_t constexpr kPuddleLifeMs = 20000;

    // BT11 the stock tank kit (the stock SmartAI timers)
    std::uint32_t constexpr kMightyBlowFirstMs = 11000;
    std::uint32_t constexpr kMightyBlowEveryMs = 15000;
    std::uint32_t constexpr kDrainingBlowFirstMs = 4000;
    std::uint32_t constexpr kDrainingBlowMinMs = 12000;
    std::uint32_t constexpr kDrainingBlowMaxMs = 15000;

    // Bedlam lands between Quarantines (ST: "so it lands between Quarantines").
    static_assert(kBedlamFirstMs > kQuarantineFirstMs && kBedlamFirstMs < kQuarantineFirstMs + kQuarantineEveryMs,
        "the first Bedlam lands between the first two Quarantines");
    static_assert(kBedlamEveryMs == kQuarantineEveryMs, "Bedlam keeps its place between Quarantines");

    // A ward's center: its radius plus 3 yd from him (9 yd normal, 8 yd heroic), so the two edges are 6 yd apart.
    constexpr float WardOffset(float wardRadius)
    {
        return wardRadius + kWardEdgeGapYd / 2.f;
    }
    static_assert(WardOffset(6.f) == 9.f && WardOffset(5.f) == 8.f, "ST: centers 9 yd (normal), 8 yd (heroic)");

    // The Fever stacks the 20 s clock has given by `ms` into the pull (the clock's own share, not the catches).
    constexpr std::uint32_t FeverTicksAt(std::uint64_t ms)
    {
        return static_cast<std::uint32_t>(ms / kFeverEveryMs);
    }

    // Does the n-th grain throw (1-based) carry the yell ("now and then")?
    constexpr bool GrainYells(std::uint32_t throwNumber)
    {
        return throwNumber > 0 && (throwNumber - 1) % kGrainYellEvery == 0;
    }

    // When to launch the sack so it lands as the marker resolves: the warning minus its flight, never negative.
    inline std::uint32_t SackLaunchDelayMs(float distanceYd, float speed = kGrainSackSpeed,
        std::uint32_t warnMs = kGrainWarnMs)
    {
        if (speed <= 0.f)
            return 0;
        float const flightMs = std::max(0.f, distanceYd) / speed * 1000.f;
        return flightMs >= float(warnMs) ? 0u : warnMs - static_cast<std::uint32_t>(flightMs);
    }

    // How many old piles leave before a new one lands, so at most `cap` stand once it is down.
    constexpr std::uint32_t PilesToDrop(std::uint32_t live, std::uint32_t cap)
    {
        return cap == 0 ? live : (live + 1 > cap ? live + 1 - cap : 0);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BT2 Contagion: who catches it. `near` is the kit's InsideClock answer (each healthy player within 5 yd of a
    // carrier, with the time they have stood that close without a break); a player held there for `holdMs` catches.
    // ----------------------------------------------------------------------------------------------------------------

    inline std::vector<std::uint64_t> Catches(std::vector<std::pair<std::uint64_t, std::uint32_t>> const& near,
        std::uint32_t holdMs)
    {
        std::vector<std::uint64_t> caught;
        for (auto const& [id, ms] : near)
            if (ms >= holdMs)
                caught.push_back(id);
        return caught;
    }

    // Can this player catch Infection now (a fresh one from contagion, a pile, a puddle or a ward)?
    constexpr bool CanCatch(bool infected, bool recovered)
    {
        return !infected && !recovered;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BT7 the purge: what happens to one player as the wards close (ST BT7)
    // ----------------------------------------------------------------------------------------------------------------

    enum class PurgeFate : std::uint8_t
    {
        Safe,       // in the right ward (or recovering where they stand)
        Hit,        // outside both wards: 40%
        Cured,      // a carrier in the Sick Ward: cured, no cough
        Caught      // healthy in the Sick Ward, or in the Well Ward with a carrier: Infected (Fever +1)
    };

    struct PurgeSubject
    {
        bool infected = false;
        bool recovered = false;     // the 10 s after a cough: cannot catch it
        bool inSick = false;
        bool inWell = false;
    };

    // `carrierInWell`: a carrier stands in the Well Ward at the purge (it infects every healthy player in it).
    constexpr PurgeFate PurgeFor(PurgeSubject const& s, bool carrierInWell)
    {
        if (!s.inSick && !s.inWell)
            return PurgeFate::Hit;
        if (s.inSick)
            return s.infected ? PurgeFate::Cured : (CanCatch(false, s.recovered) ? PurgeFate::Caught : PurgeFate::Safe);
        return carrierInWell && CanCatch(s.infected, s.recovered) ? PurgeFate::Caught : PurgeFate::Safe;
    }

    // Inside a ward: within its radius on the map plane, and on its floor.
    inline bool InWard(Vec2 player, float playerZ, Vec2 center, float centerZ, float radius)
    {
        return DungeonKit::Distance(player, center) <= radius && std::fabs(playerZ - centerZ) <= kWardZYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BT6 the ward line: two wards on a line through him, each center WardOffset(r) from him, never on a pile.
    // ----------------------------------------------------------------------------------------------------------------

    struct WardLine
    {
        Vec2 a;
        Vec2 b;
        float za = 0.f;
        float zb = 0.f;
        float bearing = 0.f;            // radians, from him to `a`
        std::uint32_t floorMisses = 0;  // disc sample points with no floor (0: both discs stand on floor)
        std::uint32_t pileHits = 0;     // piles a ward disc overlaps
        bool full = false;              // on floor and off every pile
    };

    // The five points a ward disc is tested at: its center and four points at 3/4 of its radius.
    inline std::vector<Vec2> WardSamples(Vec2 center, float radius)
    {
        float const d = radius * 0.75f;
        return { center, { center.x + d, center.y }, { center.x - d, center.y }, { center.x, center.y + d },
            { center.x, center.y - d } };
    }

    // Candidate lines every half turn / `bearings`, from `startBearing`; each side's disc is probed by `floorAt`
    // (Vec2 -> std::optional<float>: the floor's height there, nullopt when there is none on his floor or the point is
    // off his arena). The first full line wins; else the one with the fewest floor misses, then the fewest pile
    // overlaps (the first such in bearing order). nullopt only when `bearings` is 0. A center with no floor keeps
    // z 0: the caller uses the boss's height there.
    template <class FloorAt>
    std::optional<WardLine> PickWardLine(Vec2 boss, float wardRadius, std::vector<DungeonKit::AvoidCircle> const& piles,
        float startBearing, FloorAt&& floorAt, std::uint32_t bearings = kWardBearings)
    {
        std::optional<WardLine> best;
        auto better = [](WardLine const& x, WardLine const& y)
        {
            if (x.floorMisses != y.floorMisses)
                return x.floorMisses < y.floorMisses;
            return x.pileHits < y.pileHits;
        };
        float const offset = WardOffset(wardRadius);
        for (std::uint32_t i = 0; i < bearings; ++i)
        {
            WardLine line;
            line.bearing = startBearing + DungeonKit::kPi * float(i) / float(bearings);
            line.a = DungeonKit::Advance(boss, line.bearing, offset);
            line.b = DungeonKit::Advance(boss, line.bearing + DungeonKit::kPi, offset);
            for (int side = 0; side < 2; ++side)
            {
                Vec2 const center = side == 0 ? line.a : line.b;
                std::vector<Vec2> const samples = WardSamples(center, wardRadius);
                for (std::size_t k = 0; k < samples.size(); ++k)
                {
                    std::optional<float> const z = floorAt(samples[k]);
                    if (!z)
                        ++line.floorMisses;
                    else if (k == 0)
                        (side == 0 ? line.za : line.zb) = *z;
                }
                for (DungeonKit::AvoidCircle const& pile : piles)
                    if (DungeonKit::Distance(center, pile.center) < pile.radius + wardRadius)
                        ++line.pileHits;
            }
            line.full = line.floorMisses == 0 && line.pileHits == 0;
            if (line.full)
                return line;
            if (!best || better(line, *best))
                best = line;
        }
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Patients (BT1): who he coughs on. Anyone, the tank included, never a carrier; a recovering player only when
    // nobody else is left.
    // ----------------------------------------------------------------------------------------------------------------

    struct PatientCandidate
    {
        std::uint64_t id = 0;
        bool infected = false;
        bool recovered = false;
    };

    // Up to `count` distinct picks (rand(n) returns [0, n)).
    template <class Rand>
    std::vector<std::uint64_t> PickPatients(std::vector<PatientCandidate> const& candidates, std::uint32_t count,
        Rand&& rand)
    {
        std::vector<std::uint64_t> fresh;
        std::vector<std::uint64_t> recovering;
        for (PatientCandidate const& c : candidates)
        {
            if (c.infected)
                continue;
            (c.recovered ? recovering : fresh).push_back(c.id);
        }
        std::vector<std::uint64_t> picked;
        for (std::vector<std::uint64_t>* pool : { &fresh, &recovering })
            while (picked.size() < count && !pool->empty())
            {
                std::size_t const i = static_cast<std::size_t>(rand(pool->size())) % pool->size();
                picked.push_back((*pool)[i]);
                pool->erase(pool->begin() + static_cast<std::ptrdiff_t>(i));
            }
        return picked;
    }
}

#endif
