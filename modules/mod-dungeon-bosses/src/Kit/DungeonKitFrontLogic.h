/*
 * mod-dungeon-bosses, the shared dungeon kit (Blackrock Spire WP-KT-B2, handoff section 3.11 #7): the pure script side
 * of mod-boss-mechanics' rolling fronts (BM MechanicFront.h, Mechanic::ConeFront / LineFront / FrontSafe). No engine
 * or BM headers: boss Logic headers and their host tests include it as they are. The engine half is
 * DungeonKitFronts.h (FrontDirector); tests/kit_fronts_test.cpp covers this file, tests/kit_fronts_parity_test.cpp
 * pins its mirrors against BM's MechanicFront.h.
 *
 *   ReachMs / PassMs / OverMs     ring front timing after the launch: the band's outer edge reaches a radius, its inner
 *                                 edge passes one, the front is over (the same model as BM's ConeParams)
 *   WallReachMs / WallPassMs ...  the same for a line front (s along the facing from the start line)
 *   SliceBearing                  ring k's safe slice, turned k x turnDeg clockwise (mirror of BM Front::SliceBearing)
 *   SliceAwayFrom                 a slice on the far side of the apex from a point (the tank, the group)
 *   PlanRings                     a ring sequence (Emberseer EM3): when each ring registers, launches and is over, its
 *                                 slice and start radius; LastPassMs / FirstReachMs for the posts' timing (EM6)
 *   WallFrame, ToWallCoords       a line front's frame: s along the facing, t across it (left of the facing positive,
 *                                 BM Geo::ToLineCoords)
 *   PoolBlocks / PoolBlocksAll    a pool's lateral interval on a wall (mirror of BM Front::BlockedBy, plus a margin)
 *   PlaceGap                      a gap centre clear of blocked intervals (mirror of BM Front::PlaceGap)
 *   PlaceWallGap / PlanWallGaps   Rend RG6: one gap per wall off live pools inside the usable span; a later wall's gap
 *                                 on the other side, near the previous one; when no lane is pool-free, the lane with
 *                                 the least floor under pools (LanePoolArea), so a gap is always placed
 *   WallCarrierSlots              lateral spots for visual carriers along a wall, none in a gap
 *   RingCarrierBearings           bearings for visual carriers over a ring's band (none in the slice)
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FRONT_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FRONT_LOGIC_H

#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <optional>
#include <span>
#include <utility>
#include <vector>

namespace DungeonKit::Fronts
{
    float constexpr kDefaultSpeed = 8.f;            // yd/s (SP EM3, RG6)
    float constexpr kDefaultBandYd = 4.f;
    float constexpr kMaxSliceDeg = 330.f;           // BM Front::kMaxSliceDeg
    float constexpr kMinSegmentYd = 0.25f;          // BM Front::kMinSegmentYd

    // (-pi, pi], as BM Geo::WrapPi.
    inline float WrapPi(float a)
    {
        a = std::fmod(a, kTwoPi);
        if (a <= -kPi)
            a += kTwoPi;
        else if (a > kPi)
            a -= kTwoPi;
        return a;
    }

    inline float DegToRad(float deg)
    {
        return deg * kPi / 180.f;
    }

    // Seconds to ms, rounded up (BM MsOf: a time "after which" is never early).
    inline std::uint32_t MsOfSeconds(float s)
    {
        return s <= 0.f ? 0u : static_cast<std::uint32_t>(std::ceil(s * 1000.f - 1e-3f));
    }

    // ---- timing -----------------------------------------------------------------------------------------------------

    // A ring front's band starts with its inner edge on `startYd` and its outer edge on startYd + band at the launch.
    // ms after the launch until the outer edge reaches `yd` (0: already there).
    inline std::uint32_t ReachMs(float startYd, float bandYd, float speed, float yd)
    {
        return speed > 0.f ? MsOfSeconds((yd - startYd - bandYd) / speed) : 0u;
    }

    // ms after the launch until the inner edge has passed `yd` (the ground at yd is clear from then).
    inline std::uint32_t PassMs(float startYd, float speed, float yd)
    {
        return speed > 0.f ? MsOfSeconds((yd - startYd) / speed) : 0u;
    }

    // ms after the launch until the front is over (its inner edge passes endYd): BM ProjectileDuration of ConeParams.
    inline std::uint32_t OverMs(float startYd, float endYd, float speed)
    {
        return PassMs(startYd, speed, endYd);
    }

    // A line front: the wall's back edge is on the start line (s 0) at the launch, its front edge at s = band.
    inline std::uint32_t WallReachMs(float bandYd, float speed, float s)
    {
        return speed > 0.f ? MsOfSeconds((s - bandYd) / speed) : 0u;
    }

    inline std::uint32_t WallPassMs(float speed, float s)
    {
        return speed > 0.f ? MsOfSeconds(s / speed) : 0u;
    }

    inline std::uint32_t WallOverMs(float travelYd, float speed)
    {
        return WallPassMs(speed, travelYd);
    }

    // ---- slices -----------------------------------------------------------------------------------------------------

    // Ring `ring` (0 = the first) of a sequence: its slice turned ring x turnDeg clockwise from `first` (radians).
    // Clockwise is a negative turn in the map's counter-clockwise angles. Mirror of BM Front::SliceBearing.
    inline float SliceBearing(float first, std::uint32_t ring, float turnDeg)
    {
        return WrapPi(first - DegToRad(turnDeg) * static_cast<float>(ring));
    }

    // A slice on the far side of `apex` from `from` (the bearing from `from` through the apex): behind the boss from
    // his tank, where melee already stands (RF designer question 1, option B). `from` on the apex: bearing 0.
    inline float SliceAwayFrom(Vec2 apex, Vec2 from)
    {
        if (Distance(apex, from) < 0.01f)
            return 0.f;
        return WrapPi(std::atan2(apex.y - from.y, apex.x - from.x));
    }

    // Is bearing `b` (radians, from the apex) inside a slice of `sliceDeg` centred on `sliceBearing`?
    inline bool InSlice(float b, float sliceBearing, float sliceDeg)
    {
        return std::fabs(WrapPi(b - sliceBearing)) <= DegToRad(sliceDeg) * 0.5f;
    }

    // ---- ring sequences (Emberseer EM3) ---------------------------------------------------------------------------

    struct RingSequenceSpec
    {
        std::uint32_t rings = 1;            // N 1 / 2 / 3, H 2 / 3 / 4 (by stacks; the boss picks)
        float firstSlice = 0.f;             // radians: ring 0's safe slice (SP: random)
        float turnDeg = 45.f;               // each later ring's slice turned clockwise (N 45, H 60)
        float sliceDeg = 60.f;              // N 60 (a 300 degree front), H 45 (315)
        float startYd = 0.f;                // the band's inner edge at launch: the nova's radius
        float laterStartYd = -1.f;          // rings 1+ (< 0: startYd; 0: from the apex, user ruling for Emberseer)
        float endYd = 45.f;                 // over once the inner edge passes this (Emberseer's walls)
        float bandYd = kDefaultBandYd;
        float speed = kDefaultSpeed;
        std::uint32_t firstWarnMs = 2500;   // ring 0: registration to launch (user ruling for Emberseer: 5000)
        std::uint32_t spacingMs = 2000;     // launch to launch (N 2 s, H 1.5 s)
        // SP EM3: "later rings: [slice shown] as the ring before launches": ring k registers at ring k-1's launch with
        // a warning of spacingMs. false: every ring registers at once (ring k warns firstWarn + k x spacing).
        bool revealAtPreviousLaunch = true;
    };

    // One ring of a planned sequence (ms from the sequence's start).
    struct RingStep
    {
        std::uint32_t index = 0;
        std::uint32_t registerMs = 0;       // Mechanic::ConeFront is called then, with warn = launchMs - registerMs
        std::uint32_t launchMs = 0;
        std::uint32_t overMs = 0;           // its inner edge passed endYd
        float sliceBearing = 0.f;
        float startYd = 0.f;

        std::uint32_t WarnMs() const { return launchMs - registerMs; }
    };

    inline bool Valid(RingSequenceSpec const& s)
    {
        float const later = s.laterStartYd < 0.f ? s.startYd : s.laterStartYd;
        return s.rings > 0 && s.speed > 0.f && s.bandYd >= 0.5f && s.startYd >= 0.f && s.endYd > s.startYd
            && s.endYd > later && s.sliceDeg >= 0.f && s.sliceDeg <= kMaxSliceDeg && std::isfinite(s.firstSlice);
    }

    inline std::vector<RingStep> PlanRings(RingSequenceSpec const& s)
    {
        std::vector<RingStep> out;
        if (!Valid(s))
            return out;
        out.reserve(s.rings);
        for (std::uint32_t k = 0; k < s.rings; ++k)
        {
            RingStep r;
            r.index = k;
            r.launchMs = s.firstWarnMs + k * s.spacingMs;
            if (k == 0 || !s.revealAtPreviousLaunch)
                r.registerMs = 0;
            else
                r.registerMs = out.back().launchMs;
            r.startYd = (k == 0 || s.laterStartYd < 0.f) ? s.startYd : s.laterStartYd;
            r.sliceBearing = SliceBearing(s.firstSlice, k, s.turnDeg);
            r.overMs = r.launchMs + OverMs(r.startYd, s.endYd, s.speed);
            out.push_back(r);
        }
        return out;
    }

    // ms from the sequence's start until every ring's inner edge has passed `yd` (EM6: the posts flare once the last
    // ring has passed 21 yd). 0 for an empty plan.
    inline std::uint32_t LastPassMs(std::span<RingStep const> plan, RingSequenceSpec const& s, float yd)
    {
        std::uint32_t at = 0;
        for (RingStep const& r : plan)
            at = std::max(at, r.launchMs + PassMs(r.startYd, s.speed, yd));
        return at;
    }

    // ms from the sequence's start until the first ring's outer edge reaches `yd` (EM6: the next pulse waits so its
    // first ring cannot reach 15 yd before the posts fire).
    inline std::uint32_t FirstReachMs(std::span<RingStep const> plan, RingSequenceSpec const& s, float yd)
    {
        if (plan.empty())
            return 0;
        return plan.front().launchMs + ReachMs(plan.front().startYd, s.bandYd, s.speed, yd);
    }

    // ms from the sequence's start until its last ring is over.
    inline std::uint32_t SequenceOverMs(std::span<RingStep const> plan)
    {
        std::uint32_t at = 0;
        for (RingStep const& r : plan)
            at = std::max(at, r.overMs);
        return at;
    }

    // ---- line fronts: frame, pools, gaps (Rend RG6) ---------------------------------------------------------------

    // A line front as BM poses it: `start` the middle of the start line, travelling along `facing` (radians) for
    // `travelYd`, `widthYd` across.
    struct WallFrame
    {
        Vec2 start;
        float facing = 0.f;
        float travelYd = 0.f;
        float widthYd = 0.f;
    };

    struct WallCoords
    {
        float s = 0.f;      // along the facing from the start line
        float t = 0.f;      // across: left of the facing positive
    };

    inline WallCoords ToWallCoords(WallFrame const& f, Vec2 p)
    {
        float const ux = std::cos(f.facing);
        float const uy = std::sin(f.facing);
        float const dx = p.x - f.start.x;
        float const dy = p.y - f.start.y;
        return { dx * ux + dy * uy, -dx * uy + dy * ux };
    }

    inline Vec2 FromWallCoords(WallFrame const& f, float s, float t)
    {
        float const ux = std::cos(f.facing);
        float const uy = std::sin(f.facing);
        return { f.start.x + ux * s - uy * t, f.start.y + uy * s + ux * t };
    }

    struct PoolCircle
    {
        Vec2 center;
        float radius = 0.f;
    };

    // The lateral interval a pool (grown by `marginYd`) covers on the wall's axis, when it reaches into the wall's path
    // at all (BM Front::BlockedBy with radius + margin).
    inline std::optional<std::pair<float, float>> PoolBlocks(WallFrame const& f, PoolCircle const& pool,
        float marginYd = 0.f)
    {
        float const r = pool.radius + std::max(0.f, marginYd);
        WallCoords const c = ToWallCoords(f, pool.center);
        if (c.s < -r || c.s > f.travelYd + r)
            return std::nullopt;
        return std::make_pair(c.t - r, c.t + r);
    }

    inline std::vector<std::pair<float, float>> PoolBlocksAll(WallFrame const& f, std::span<PoolCircle const> pools,
        float marginYd = 0.f)
    {
        std::vector<std::pair<float, float>> out;
        for (PoolCircle const& p : pools)
            if (auto b = PoolBlocks(f, p, marginYd))
                out.push_back(*b);
        return out;
    }

    // Is a gap centred at `centre` (width `width`) clear of every blocked lateral interval? Mirror of BM
    // Front::GapClear.
    inline bool GapClear(float centre, float width, std::vector<std::pair<float, float>> const& blocked)
    {
        float const a = centre - width * 0.5f;
        float const b = centre + width * 0.5f;
        for (auto const& [lo, hi] : blocked)
            if (b > lo && a < hi)
                return false;
        return true;
    }

    // Mirror of BM Front::PlaceGap (tests/kit_fronts_parity_test.cpp pins it): a gap centre on a wall of `wallWidth`,
    // its whole width `edgeYd` inside the ends, clear of every blocked interval, on `side` (+1 left, -1 right, 0 any),
    // within `within` of `near` (within < 0: anywhere); `u` in [0, 1) picks uniformly over the free centres.
    inline std::optional<float> PlaceGap(float wallWidth, float gapWidth, std::vector<std::pair<float, float>> blocked,
        float u, int side = 0, float edgeYd = 0.f, float near = 0.f, float within = -1.f)
    {
        float lo = -wallWidth * 0.5f + edgeYd + gapWidth * 0.5f;
        float hi = wallWidth * 0.5f - edgeYd - gapWidth * 0.5f;
        if (within >= 0.f)
        {
            lo = std::max(lo, near - within);
            hi = std::min(hi, near + within);
        }
        if (side > 0)
            lo = std::max(lo, 0.f);
        else if (side < 0)
            hi = std::min(hi, 0.f);
        if (hi < lo)
            return std::nullopt;
        std::vector<std::pair<float, float>> free{ { lo, hi } };
        for (auto const& [blo, bhi] : blocked)
        {
            float const a = blo - gapWidth * 0.5f;
            float const b = bhi + gapWidth * 0.5f;
            std::vector<std::pair<float, float>> next;
            for (auto const& [fl, fh] : free)
            {
                if (b <= fl || a >= fh)
                {
                    next.push_back({ fl, fh });
                    continue;
                }
                if (a > fl)
                    next.push_back({ fl, a });
                if (b < fh)
                    next.push_back({ b, fh });
            }
            free = std::move(next);
        }
        float total = 0.f;
        for (auto const& [fl, fh] : free)
            total += fh - fl;
        if (free.empty())
            return std::nullopt;
        if (total <= 1e-4f)
            return free.front().first;
        float pick = std::clamp(u, 0.f, 0.9999f) * total;
        for (auto const& [fl, fh] : free)
        {
            if (pick <= fh - fl)
                return fl + pick;
            pick -= fh - fl;
        }
        return free.back().second;
    }

    // +1 left of the centreline, -1 right, 0 on it (mirror of BM Front::SideOf).
    inline int SideOf(float centre)
    {
        return centre > 1e-3f ? 1 : (centre < -1e-3f ? -1 : 0);
    }

    struct WallGapSpec
    {
        float gapYd = 8.f;                  // SP RG6: one 8 yd gap
        // The span the gap must sit in, centred `spanCentreYd` across from the wall's centreline (0: the wall's whole
        // width). Rend: the wall spans the end bays (68 yd) but the gap must be in the 40 yd main strip.
        float spanYd = 0.f;
        float spanCentreYd = 0.f;
        float edgeYd = 1.f;                 // the gap's whole width this far inside the span's ends
        float poolMarginYd = 1.f;           // a pool grown by this before it counts against a gap
        bool otherSide = true;              // a later wall's gap on the other side of the span's middle (RG6 heroic)
        float withinYd = 20.f;              // ... and within this of the previous gap (< 0: anywhere; RF question 3)
    };

    // Where one gap went and which rules it kept.
    struct GapPick
    {
        float centre = 0.f;                 // lateral t on the wall
        bool offPools = true;               // no live pool anywhere in the gap's lane (the strict rule)
        float poolAreaSqYd = 0.f;           // else: the lane's floor under pools (the least the rules allowed)
        bool keptSide = true;               // the other side from the previous gap (true when no rule applied)
        bool keptWithin = true;             // within withinYd of the previous gap (true when no rule applied)
    };

    // The free centre range of a gap on a span centred on 0 (PlaceGap's rules without the blocked intervals).
    inline std::optional<std::pair<float, float>> GapRange(float spanWidth, float gapWidth, int side, float edgeYd,
        float near, float within)
    {
        float lo = -spanWidth * 0.5f + edgeYd + gapWidth * 0.5f;
        float hi = spanWidth * 0.5f - edgeYd - gapWidth * 0.5f;
        if (within >= 0.f)
        {
            lo = std::max(lo, near - within);
            hi = std::min(hi, near + within);
        }
        if (side > 0)
            lo = std::max(lo, 0.f);
        else if (side < 0)
            hi = std::min(hi, 0.f);
        if (hi < lo)
            return std::nullopt;
        return std::make_pair(lo, hi);
    }

    // The floor (sq yd) of the gap's lane (the strip |t - centre| <= width / 2 the gap sweeps along the whole travel)
    // that lies under the pools in the wall's path, each grown by `marginYd`.
    inline float LanePoolArea(WallFrame const& f, std::span<PoolCircle const> pools, float marginYd, float centre,
        float width)
    {
        float area = 0.f;
        float const a = centre - width * 0.5f;
        float const b = centre + width * 0.5f;
        for (PoolCircle const& p : pools)
        {
            float const r = p.radius + std::max(0.f, marginYd);
            WallCoords const c = ToWallCoords(f, p.center);
            if (r <= 0.f || c.s < -r || c.s > f.travelYd + r)
                continue;
            float const lo = std::max(a, c.t - r);
            float const hi = std::min(b, c.t + r);
            if (hi <= lo)
                continue;
            // The disc's chord across the strip, midpoint rule.
            int constexpr kSteps = 16;
            float const dt = (hi - lo) / kSteps;
            for (int i = 0; i < kSteps; ++i)
            {
                float const t = lo + (static_cast<float>(i) + 0.5f) * dt - c.t;
                area += 2.f * std::sqrt(std::max(0.f, r * r - t * t)) * dt;
            }
        }
        return area;
    }

    // One wall's gap. `pools`: the live pools; `previous`: the previous wall's gap centre of the same call (nullopt:
    // the first wall). Always places a gap, in this order (RF question 3 and SP RG6: a reachable second gap outranks a
    // pool-free lane, since a player can stand in the lane beside a pool but cannot outrun a wall):
    //   1. off every pool, other side, within          (the strict rule; `u` picks uniformly over the free centres)
    //   2. the lane with the least floor under pools, other side, within
    //   3. ... other side, anywhere   4. ... any side, within   5. ... anywhere
    //   (2-5: `u` picks among the centres, 0.25 yd apart, within 0.5 sq yd of the least)
    // With no span left at all (a span narrower than the gap), the span's middle.
    inline GapPick PlaceWallGap(WallFrame const& f, WallGapSpec const& g, std::span<PoolCircle const> pools,
        std::optional<float> previous, float u)
    {
        float const span = g.spanYd > 0.f ? std::min(g.spanYd, f.widthYd) : f.widthYd;
        float const c = g.spanCentreYd;
        // PlaceGap works on a span centred on 0: shift the blocked intervals and `near` by the span's centre.
        std::vector<std::pair<float, float>> shifted;
        for (auto const& [lo, hi] : PoolBlocksAll(f, pools, g.poolMarginYd))
            shifted.push_back({ lo - c, hi - c });

        // Sides are of the span's middle line (the wall's centreline when spanCentreYd is 0).
        float const near = previous ? *previous - c : 0.f;
        bool const wantSide = previous && g.otherSide && SideOf(near) != 0;
        bool const wantWithin = previous && g.withinYd >= 0.f;
        int const side = wantSide ? -SideOf(near) : 0;

        auto finish = [&](float shiftedCentre)
        {
            GapPick p;
            p.centre = shiftedCentre + c;
            p.poolAreaSqYd = LanePoolArea(f, pools, g.poolMarginYd, p.centre, g.gapYd);
            p.offPools = GapClear(shiftedCentre, g.gapYd, shifted);
            p.keptSide = !wantSide || SideOf(shiftedCentre) != -side;     // the middle line counts as the other
            p.keptWithin = !wantWithin || std::fabs(shiftedCentre - near) <= g.withinYd + 1e-3f;
            return p;
        };

        // 1. strict
        if (std::optional<float> at = PlaceGap(span, g.gapYd, shifted, u, side, g.edgeYd, near,
            wantWithin ? g.withinYd : -1.f))
            return finish(*at);

        // 2-5. least pool floor
        struct Try
        {
            bool side;
            bool within;
        };
        Try const tries[] = { { true, true }, { true, false }, { false, true }, { false, false } };
        for (Try const& t : tries)
        {
            auto range = GapRange(span, g.gapYd, t.side ? side : 0, g.edgeYd, near,
                (t.within && wantWithin) ? g.withinYd : -1.f);
            if (!range)
                continue;
            float constexpr kStep = 0.25f;
            std::vector<std::pair<float, float>> scored;        // shifted centre, area
            for (float x = range->first; x <= range->second + 1e-4f; x += kStep)
                scored.push_back({ x, LanePoolArea(f, pools, g.poolMarginYd, x + c, g.gapYd) });
            float best = scored.front().second;
            for (auto const& [x, area] : scored)
                best = std::min(best, area);
            std::vector<float> ties;
            for (auto const& [x, area] : scored)
                if (area <= best + 0.5f)
                    ties.push_back(x);
            std::size_t const i = std::min(ties.size() - 1,
                static_cast<std::size_t>(std::clamp(u, 0.f, 0.9999f) * static_cast<float>(ties.size())));
            return finish(ties[i]);
        }
        return finish(0.f);
    }

    // `walls` gaps for one call (RG6 heroic: two walls, gaps on opposite sides), all off the same pools. `rolls` holds
    // one u in [0, 1) per wall (fewer: 0.5 for the rest).
    inline std::vector<GapPick> PlanWallGaps(WallFrame const& f, WallGapSpec const& g, std::uint32_t walls,
        std::span<PoolCircle const> pools, std::span<float const> rolls)
    {
        std::vector<GapPick> out;
        std::optional<float> previous;
        for (std::uint32_t k = 0; k < walls; ++k)
        {
            float const u = k < rolls.size() ? rolls[k] : 0.5f;
            GapPick const p = PlaceWallGap(f, g, pools, previous, u);
            out.push_back(p);
            previous = p.centre;
        }
        return out;
    }

    // ---- visual carriers ------------------------------------------------------------------------------------------

    // Lateral spots (t) for carriers along a wall of `widthYd`, about `spacingYd` apart, none inside a gap (gaps as
    // { centre, width }): each wall segment gets ceil(len / spacing) spots spread evenly over it. At most `maxCount`
    // spots in all (the widest segments keep theirs; 0: no cap).
    inline std::vector<float> WallCarrierSlots(float widthYd, float spacingYd,
        std::span<std::pair<float, float> const> gaps, std::uint32_t maxCount = 0)
    {
        std::vector<float> out;
        if (widthYd <= 0.f || spacingYd <= 0.f)
            return out;
        float const half = widthYd * 0.5f;
        std::vector<std::pair<float, float>> cut;
        for (auto const& [centre, width] : gaps)
        {
            float const a = std::max(-half, centre - width * 0.5f);
            float const b = std::min(half, centre + width * 0.5f);
            if (b > a)
                cut.push_back({ a, b });
        }
        std::sort(cut.begin(), cut.end());
        std::vector<std::pair<float, float>> segs;
        float at = -half;
        for (auto const& [a, b] : cut)
        {
            if (a - at >= kMinSegmentYd)
                segs.push_back({ at, a });
            at = std::max(at, b);
        }
        if (half - at >= kMinSegmentYd)
            segs.push_back({ at, half });
        for (auto const& [lo, hi] : segs)
        {
            float const len = hi - lo;
            std::uint32_t const n = std::max<std::uint32_t>(1, static_cast<std::uint32_t>(std::ceil(len / spacingYd)));
            for (std::uint32_t i = 0; i < n; ++i)
                out.push_back(lo + len * (static_cast<float>(i) + 0.5f) / static_cast<float>(n));
        }
        if (maxCount && out.size() > maxCount)
        {
            // Thin evenly: keep every k-th spot.
            std::vector<float> kept;
            float const step = static_cast<float>(out.size()) / static_cast<float>(maxCount);
            for (std::uint32_t i = 0; i < maxCount; ++i)
                kept.push_back(out[std::min<std::size_t>(out.size() - 1,
                    static_cast<std::size_t>((static_cast<float>(i) + 0.5f) * step))]);
            out = std::move(kept);
        }
        return out;
    }

    // Bearings (radians) for carriers over a ring's band at `radiusYd`, about `spacingYd` apart along the arc, none in
    // the slice (sliceDeg 0: a full ring). At most `maxCount` (0: no cap).
    inline std::vector<float> RingCarrierBearings(float sliceBearing, float sliceDeg, float radiusYd, float spacingYd,
        std::uint32_t maxCount = 0)
    {
        std::vector<float> out;
        if (radiusYd <= 0.f || spacingYd <= 0.f)
            return out;
        float const arc = DegToRad(360.f - std::clamp(sliceDeg, 0.f, kMaxSliceDeg));
        std::uint32_t n = std::max<std::uint32_t>(1, static_cast<std::uint32_t>(std::ceil(arc * radiusYd / spacingYd)));
        if (maxCount)
            n = std::min(n, maxCount);
        // The arc runs from the slice's left edge round to its right edge.
        float const from = sliceBearing + DegToRad(sliceDeg) * 0.5f;
        for (std::uint32_t i = 0; i < n; ++i)
            out.push_back(WrapPi(from + arc * (static_cast<float>(i) + 0.5f) / static_cast<float>(n)));
        return out;
    }
}

#endif
