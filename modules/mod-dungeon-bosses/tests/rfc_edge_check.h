// Shared by rfc_bazzalan_test.cpp and rfc_taragaman_test.cpp: a boss at the edge of his arena (RagefireChasmRework.h
// StandSpot, NextEdgeStep, BackstepStays; RF-1 RF-M1), swept over every quarter-yard cell of his floor.
#ifndef RFC_EDGE_CHECK_H
#define RFC_EDGE_CHECK_H

#include "RagefireChasmRework.h"
#include "check.h"
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <span>

namespace RfcEdgeCheck
{
    using namespace RagefireChasmRework;

    struct Box
    {
        float x0, x1, y0, y1;
    };

    // Strictly inside: every point within 0.1 yd is on the arena too (no float coin flip for the leash).
    inline bool StrictlyInside(Arena const& arena, Vec2 p, float z)
    {
        for (int k = 0; k < 16; ++k)
            if (!arena.Contains(DungeonKit::Advance(p, float(k) * DungeonKit::kPi / 8.f, 0.1f), z))
                return false;
        return arena.Contains(p, z);
    }

    // `meleeYd`: his melee range; `closeYd`: the engine steps back from a target nearer than this.
    inline void CheckEdge(char const* boss, std::span<Vec2 const> polygon, Arena const& arena, Arena const& floor,
        Arena const& reach, float z, Box const& box, float meleeYd, float closeYd)
    {
        float constexpr runYd = 7.f;                // a creature's run, a second
        std::uint32_t band = 0;
        std::uint32_t bareSpots = 0;                // what ClampInto alone would have given
        float margin = 99.f;
        float farBack = 0.f;
        for (float x = box.x0; x <= box.x1; x += 0.25f)
            for (float y = box.y0; y <= box.y1; y += 0.25f)
            {
                Vec2 const p{ x, y };
                if (!floor.Contains(p, z))
                    continue;
                // Every walk of his ends strictly inside, whatever the cell.
                Vec2 const spot = StandSpot(polygon, p);
                CHECK(StrictlyInside(arena, spot, z));
                margin = std::min(margin, InsideBy(polygon, spot));
                if (arena.Contains(p, z))
                {
                    CHECK(DungeonKit::Distance(spot, p) < 1.f);
                    continue;
                }
                bool const inReach = reach.Contains(p, z);
                if (inReach)
                {
                    ++band;
                    bareSpots += StrictlyInside(arena, ClampInto(polygon, p), z) ? 0 : 1;
                    CHECK(DungeonKit::Distance(spot, p) <= meleeYd - 0.1f);
                }

                // Off his arena himself, on this cell: back onto it, whoever he fights and in whatever range, well
                // inside the leash's 2 s.
                EdgeView view;
                view.self = p;
                view.selfInside = false;
                view.targetInside = false;
                for (bool const melee : { false, true })
                    for (bool const targetReach : { false, true })
                        for (int k = 0; k < 8; ++k)
                        {
                            view.inMelee = melee;
                            view.targetInReach = targetReach;
                            view.target = DungeonKit::Advance(p, float(k) * DungeonKit::kPi / 4.f, melee ? 3.f : 8.f);
                            EdgeStep const step = NextEdgeStep(polygon, view);
                            CHECK(step.act == EdgeAct::Walk && StrictlyInside(arena, step.spot, z));
                            if (inReach)
                                farBack = std::max(farBack, DungeonKit::Distance(p, step.spot));
                        }
                // His target inside and in range (a chase that ended off his arena): back, no farther from it.
                view.targetInside = true;
                view.targetInReach = true;
                view.inMelee = true;
                for (int k = 0; k < 32; ++k)
                    for (float const d : { 1.f, 3.f, meleeYd - 0.1f })
                    {
                        view.target = DungeonKit::Advance(p, float(k) * DungeonKit::kPi / 16.f, d);
                        if (InsideBy(polygon, view.target) < 2.f * kStandInsetYd)
                            continue;
                        EdgeStep const step = NextEdgeStep(polygon, view);
                        CHECK(step.act == EdgeAct::Walk && StrictlyInside(arena, step.spot, z));
                        CHECK(DungeonKit::Distance(step.spot, view.target) <= d + 0.01f);
                    }
                // Inside but out of range: the chase brings him back by itself.
                view.inMelee = false;
                CHECK(NextEdgeStep(polygon, view).act == EdgeAct::Chase);

                // On his arena, the target on this cell: never a step off it.
                EdgeView on;
                on.self = spot;
                on.target = p;
                on.targetInside = false;
                on.targetInReach = inReach;
                on.inMelee = false;
                EdgeStep const step = NextEdgeStep(polygon, on);
                CHECK(step.act == (inReach ? EdgeAct::Walk : EdgeAct::Stand));
                if (step.act == EdgeAct::Walk)
                    CHECK(StrictlyInside(arena, step.spot, z));
                on.inMelee = true;
                CHECK(NextEdgeStep(polygon, on).act == EdgeAct::Stand);
                on.targetInside = true;
                CHECK(NextEdgeStep(polygon, on).act == EdgeAct::Chase);
            }
        CHECK(band > 5000);
        CHECK(bareSpots > 0);                       // the bug was real on this floor
        CHECK(margin >= kStandMarginYd);
        CHECK(farBack < runYd);                     // under 1 s of the 2 s

        // The engine's step back from a target inside him: allowed only when it ends strictly inside.
        std::uint32_t off = 0;
        for (float x = box.x0; x <= box.x1; x += 0.5f)
            for (float y = box.y0; y <= box.y1; y += 0.5f)
            {
                Vec2 const him{ x, y };
                if (!arena.Contains(him, z))
                    continue;
                for (int k = 0; k < 16; ++k)
                    for (float const d : { 0.4f, closeYd * 0.5f, closeYd - 0.05f })
                    {
                        Vec2 const target = DungeonKit::Advance(him, float(k) * DungeonKit::kPi / 8.f, d);
                        Vec2 const to = DungeonKit::Advance(target, DungeonKit::BearingTo(target, him), meleeYd / 2.f);
                        off += arena.Contains(to, z) ? 0 : 1;
                        if (BackstepStays(polygon, him, target, meleeYd / 2.f))
                            CHECK(StrictlyInside(arena, to, z));
                        else
                            CHECK(InsideBy(polygon, to) < kStandMarginYd);
                    }
            }
        CHECK(off > 0);
        std::printf("%s edge: %u band cells, %u of their bare clamps not strictly inside, margin %.2f, back %.1f yd at "
            "most, %u engine back steps held\n", boss, band, bareSpots, margin, farBack, off);
    }
}

#endif
