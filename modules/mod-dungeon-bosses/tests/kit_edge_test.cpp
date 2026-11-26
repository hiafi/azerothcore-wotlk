// Host tests for the shared dungeon kit's edge fight (Zul'Farrak WP-KT, F57): DungeonKitArenaEdgeLogic.h, promoted from
// Ragefire Chasm's RagefireChasmRework.h. The kit's rules must give Ragefire's answer on every cell of Bazzalan's and
// Taragaman's floors (parity), and keep the edge rules on a small hand-made arena.
#include "BazzalanLogic.h"
#include "DungeonKitArenaEdgeLogic.h"
#include "RagefireChasmRework.h"
#include "TaragamanLogic.h"
#include "check.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <optional>
#include <span>

namespace Kit = DungeonKit::EdgeFight;
namespace Rfc = RagefireChasmRework;
using DungeonKit::Arena;
using DungeonKit::Vec2;

namespace
{
    bool Same(Vec2 a, Vec2 b)
    {
        return a.x == b.x && a.y == b.y;
    }

    void TestConstants()
    {
        CHECK(Kit::kEdgeReachYd == Rfc::kEdgeReachYd);
        CHECK(Kit::kStandInsetYd == Rfc::kStandInsetYd);
        CHECK(Kit::kStandMarginYd == Rfc::kStandMarginYd);
        CHECK(Kit::kStandSearchYd == Rfc::kStandSearchYd);
        CHECK(Kit::kReachMelee3dYd == Rfc::kReachMelee3dYd);
        CHECK(Kit::kReachBandsYd == Rfc::kReachBandsYd);
        for (float const yd : Kit::kReachBandsYd)
            CHECK(Kit::ReachRiseYd(yd) == Rfc::ReachRiseYd(yd));
    }

    struct Box
    {
        float x0, x1, y0, y1;
    };

    Box BoxOf(std::span<Vec2 const> polygon, float pad)
    {
        Box b{ polygon[0].x, polygon[0].x, polygon[0].y, polygon[0].y };
        for (Vec2 const& p : polygon)
        {
            b.x0 = std::min(b.x0, p.x);
            b.x1 = std::max(b.x1, p.x);
            b.y0 = std::min(b.y0, p.y);
            b.y1 = std::max(b.y1, p.y);
        }
        return { b.x0 - pad, b.x1 + pad, b.y0 - pad, b.y1 + pad };
    }

    // Every rule, every 0.5 yd cell of the polygon's box grown by 6 yd, every view: the kit equals Ragefire.
    std::uint32_t Parity(char const* name, std::span<Vec2 const> polygon, Arena const& kitReach,
        Arena const& rfcReach, float z)
    {
        Box const box = BoxOf(polygon, 6.f);
        std::uint32_t cells = 0;
        std::uint32_t diffs = 0;
        for (float x = box.x0; x <= box.x1; x += 0.5f)
            for (float y = box.y0; y <= box.y1; y += 0.5f)
            {
                Vec2 const p{ x, y };
                ++cells;
                diffs += Kit::InsideBy(polygon, p) == Rfc::InsideBy(polygon, p) ? 0 : 1;
                diffs += Same(Kit::StandSpot(polygon, p), Rfc::StandSpot(polygon, p)) ? 0 : 1;
                diffs += Same(Kit::ClampInto(polygon, p), Rfc::ClampInto(polygon, p)) ? 0 : 1;
                diffs += kitReach.Contains(p, z) == rfcReach.Contains(p, z) ? 0 : 1;
                for (int k = 0; k < 8; k += 3)
                {
                    Vec2 const t = DungeonKit::Advance(p, float(k) * DungeonKit::kPi / 4.f, 3.f);
                    diffs += Same(Kit::BackSpot(polygon, p, t), Rfc::BackSpot(polygon, p, t)) ? 0 : 1;
                    diffs += Kit::BackstepStays(polygon, p, t, 2.5f) == Rfc::BackstepStays(polygon, p, t, 2.5f) ? 0 : 1;
                    for (int bits = 0; bits < 16; ++bits)
                    {
                        Kit::EdgeView kv;
                        Rfc::EdgeView rv;
                        kv.self = rv.self = p;
                        kv.target = rv.target = t;
                        kv.selfInside = rv.selfInside = (bits & 1) != 0;
                        kv.targetInside = rv.targetInside = (bits & 2) != 0;
                        kv.targetInReach = rv.targetInReach = (bits & 4) != 0;
                        kv.inMelee = rv.inMelee = (bits & 8) != 0;
                        Kit::EdgeStep const ks = Kit::NextEdgeStep(polygon, kv);
                        Rfc::EdgeStep const rs = Rfc::NextEdgeStep(polygon, rv);
                        diffs += static_cast<int>(ks.act) == static_cast<int>(rs.act) && Same(ks.spot, rs.spot) ? 0 : 1;
                    }
                }
            }
        CHECK(cells > 1000);
        CHECK(diffs == 0);
        std::printf("%s parity: %u cells, %u differences\n", name, cells, diffs);
        return diffs;
    }

    void TestParity()
    {
        // Bazzalan: the climbing east edges (13 to 20) take the banded growth.
        std::span<Vec2 const> const ridge(Rfc::kRidgeArenaPolygon);
        Arena const kitRidge = Kit::EdgeReachArena(Rfc::BazzalanArena(), ridge, Rfc::kRidgeZMin, Rfc::kRidgeZMax,
            RfcBazzalan::ClimbFloor);
        Parity("bazzalan", ridge, kitRidge, RfcBazzalan::ReachArena(), 9.5f);
        Parity("bazzalan high", ridge, kitRidge, RfcBazzalan::ReachArena(), 11.f);

        // Taragaman: a level floor all round (the kit's short form).
        std::span<Vec2 const> const plateau(Rfc::kPlateauArenaPolygon);
        Arena const kitPlateau = Kit::EdgeReachArena(Rfc::TaragamanArena(), plateau, Rfc::kPlateauZMin,
            Rfc::kPlateauZMax);
        Parity("taragaman", plateau, kitPlateau, RfcTaragaman::ReachArena(), -15.f);
    }

    // A 20 by 10 yd box: the rules themselves, with the kit's names only.
    void TestBox()
    {
        std::array<Vec2, 4> const box{ { { 0.f, 0.f }, { 20.f, 0.f }, { 20.f, 10.f }, { 0.f, 10.f } } };
        std::span<Vec2 const> const poly(box);
        CHECK(std::fabs(Kit::InsideBy(poly, { 10.f, 5.f }) - 5.f) < 1e-4f);
        CHECK(Kit::InsideBy(poly, { 25.f, 5.f }) == 0.f);

        // Strictly inside: a point on the band past the east edge stands 0.25 yd in from it.
        Vec2 const stand = Kit::StandSpot(poly, { 22.f, 5.f });
        CHECK(std::fabs(stand.x - 19.75f) < 1e-3f && std::fabs(stand.y - 5.f) < 1e-3f);
        CHECK(Kit::InsideBy(poly, stand) >= Kit::kStandMarginYd);
        // A corner: never the bare corner, always strictly inside.
        Vec2 const corner = Kit::StandSpot(poly, { 22.f, 12.f });
        CHECK(Kit::InsideBy(poly, corner) >= Kit::kStandMarginYd);
        CHECK(DungeonKit::Distance(corner, { 20.f, 10.f }) <= Kit::kStandSearchYd);

        Kit::EdgeView v;
        v.self = { 19.f, 5.f };
        v.target = { 22.f, 5.f };
        v.targetInside = false;
        v.targetInReach = true;
        v.inMelee = true;
        CHECK(Kit::NextEdgeStep(poly, v).act == Kit::EdgeAct::Stand);         // on the band, in range: from here
        v.inMelee = false;
        Kit::EdgeStep const walk = Kit::NextEdgeStep(poly, v);
        CHECK(walk.act == Kit::EdgeAct::Walk && Same(walk.spot, stand));    // on the band, out of range: to the edge
        v.targetInReach = false;
        CHECK(Kit::NextEdgeStep(poly, v).act == Kit::EdgeAct::Stand);         // out of reach: the reach guard's
        v.targetInside = true;
        CHECK(Kit::NextEdgeStep(poly, v).act == Kit::EdgeAct::Chase);
        v.self = { 21.f, 5.f };
        v.selfInside = false;
        v.targetInside = false;
        Kit::EdgeStep const back = Kit::NextEdgeStep(poly, v);
        CHECK(back.act == Kit::EdgeAct::Walk && Kit::InsideBy(poly, back.spot) >= Kit::kStandMarginYd);

        // The engine's step back near the east edge would leave the box: held.
        CHECK(!Kit::BackstepStays(poly, { 19.5f, 5.f }, { 18.f, 5.f }, 2.5f));
        CHECK(Kit::BackstepStays(poly, { 10.f, 5.f }, { 8.5f, 5.f }, 2.5f));

        // The level reach arena: the band holds a point 4 yd out, not 5.
        Arena const reach = Kit::EdgeReachArena(Arena(DungeonKit::ArenaRegion::Polygon(
            std::vector<Vec2>(box.begin(), box.end()), 0.f, 5.f)), poly, 0.f, 5.f);
        CHECK(reach.Contains({ 24.f, 5.f }, 1.f));
        CHECK(!reach.Contains({ 25.f, 5.f }, 1.f));
        CHECK(reach.Contains({ 23.f, 12.5f }, 1.f));                         // the corner's circle
        CHECK(!reach.Contains({ 24.f, 5.f }, 6.f));                          // over the z band
    }
}

int main()
{
    TestConstants();
    TestParity();
    TestBox();
    return Report("kit_edge_test");
}
