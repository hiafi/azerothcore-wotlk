// Host test (Blackrock Spire WP-KT-B2): the kit's pure front rules (src/Kit/DungeonKitFrontLogic.h) against
// mod-boss-mechanics' own (src/MechanicFront.h): the mirrored placement rules give the same answers, the kit's timing
// matches BM's projectile model, and the kit's carrier spots and wall frame sit where BM's hitbox is. tests/run.sh
// builds it only when BM's source is found (BM_SRC, else ../mod-boss-mechanics/src).
#include "DungeonKitFrontLogic.h"
#include "MechanicFront.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <optional>
#include <random>
#include <utility>
#include <vector>

namespace
{
    namespace BM = BossMechanics;
    namespace Kit = DungeonKit::Fronts;

    bool Near(float a, float b, float tolerance = 1e-3f)
    {
        return std::fabs(a - b) <= tolerance;
    }

    void TestPlacementParity()
    {
        std::mt19937 rng(11);
        std::uniform_real_distribution<float> U(0.f, 1.f);
        for (int i = 0; i < 20000; ++i)
        {
            float const wall = 5.f + U(rng) * 70.f;
            float const gap = 1.f + U(rng) * 12.f;
            std::vector<std::pair<float, float>> blocked;
            int const n = static_cast<int>(U(rng) * 6.f);
            for (int k = 0; k < n; ++k)
            {
                float const c = (U(rng) - 0.5f) * wall;
                float const r = U(rng) * 8.f;
                blocked.push_back({ c - r, c + r });
            }
            float const u = U(rng);
            int const side = static_cast<int>(U(rng) * 3.f) - 1;
            float const edge = U(rng) * 3.f;
            float const near = (U(rng) - 0.5f) * wall;
            float const within = U(rng) < 0.5f ? -1.f : U(rng) * 30.f;
            std::optional<float> const a = Kit::PlaceGap(wall, gap, blocked, u, side, edge, near, within);
            std::optional<float> const b = BM::Front::PlaceGap(wall, gap, blocked, u, side, edge, near, within);
            CHECK(a.has_value() == b.has_value());
            if (a && b)
                CHECK(*a == *b);
            float const probe = (U(rng) - 0.5f) * wall;
            CHECK(Kit::GapClear(probe, gap, blocked) == BM::Front::GapClear(probe, gap, blocked));
            CHECK(Kit::SideOf(probe) == BM::Front::SideOf(probe));
        }
        for (std::uint32_t ring = 0; ring < 12; ++ring)
            for (float first : { -3.f, -1.f, 0.f, 0.7f, 3.1f })
                for (float turn : { 45.f, 60.f, 90.f })
                    CHECK(Near(Kit::SliceBearing(first, ring, turn), BM::Front::SliceBearing(first, ring, turn),
                        1e-5f));
    }

    void TestTimingParity()
    {
        for (float start : { 0.f, 7.f, 10.9f, 13.f })
            for (float speed : { 6.f, 8.f, 10.f })
            {
                BM::ConeFrontSpec spec{ 0.f, 60.f, start, 45.f, 4.f, speed };
                BM::ProjectileParams const p = BM::Front::ConeParams(spec);
                CHECK(Kit::OverMs(start, 45.f, speed) == static_cast<std::uint32_t>(BM::Front::Duration(p).count()));
                for (float yd : { 15.f, 21.f, 30.f })
                {
                    std::uint32_t const reach = Kit::ReachMs(start, 4.f, speed, yd);
                    if (reach > 0)
                        CHECK(Near(BM::Front::BandAt(p, static_cast<float>(reach) / 1000.f).outer, yd, 0.01f));
                    std::uint32_t const pass = Kit::PassMs(start, speed, yd);
                    if (pass > 0)
                        CHECK(Near(BM::Front::BandAt(p, static_cast<float>(pass) / 1000.f).inner, yd, 0.01f));
                }
            }
        for (float travel : { 40.f, 86.f })
        {
            BM::LineFrontSpec spec;
            spec.facing = 3.14159265f;
            spec.travelYd = travel;
            spec.widthYd = 68.f;
            spec.gaps = { { 0.f, 8.f } };
            BM::ProjectileParams const p = BM::Front::LineParams(spec);
            CHECK(Kit::WallOverMs(travel, 8.f) == static_cast<std::uint32_t>(BM::Front::Duration(p).count()));
            std::uint32_t const reach = Kit::WallReachMs(4.f, 8.f, 30.f);
            CHECK(Near(BM::Front::BandAt(p, static_cast<float>(reach) / 1000.f).outer, 30.f, 0.01f));
            std::uint32_t const pass = Kit::WallPassMs(8.f, 30.f);
            CHECK(Near(BM::Front::BandAt(p, static_cast<float>(pass) / 1000.f).inner, 30.f, 0.01f));
        }
    }

    void TestFrameParity()
    {
        std::mt19937 rng(5);
        std::uniform_real_distribution<float> U(0.f, 1.f);
        for (int i = 0; i < 2000; ++i)
        {
            Kit::WallFrame f{ { (U(rng) - 0.5f) * 400.f, (U(rng) - 0.5f) * 400.f }, (U(rng) - 0.5f) * 6.28f,
                20.f + U(rng) * 80.f, 10.f + U(rng) * 60.f };
            BM::LineFrontSpec spec;
            spec.facing = f.facing;
            spec.travelYd = f.travelYd;
            spec.widthYd = f.widthYd;
            BM::Shape const line = BM::Front::LineShape(spec);
            BM::Geo::Pose const pose{ f.start.x, f.start.y, 100.f, f.facing };
            DungeonKit::Vec2 const p{ f.start.x + (U(rng) - 0.5f) * 200.f, f.start.y + (U(rng) - 0.5f) * 200.f };
            BM::Geo::LineCoords const lc = BM::Geo::ToLineCoords(line, pose, { p.x, p.y, 100.f });
            Kit::WallCoords const kc = Kit::ToWallCoords(f, p);
            CHECK(Near(kc.s, lc.s, 1e-2f) && Near(kc.t, lc.t, 1e-2f));
            float const r = U(rng) * 8.f;
            auto const a = Kit::PoolBlocks(f, { p, r });
            auto const b = BM::Front::BlockedBy(line, pose, { p.x, p.y, 100.f }, r);
            CHECK(a.has_value() == b.has_value());
            if (a && b)
                CHECK(Near(a->first, b->first, 1e-2f) && Near(a->second, b->second, 1e-2f));
        }
    }

    // The kit's carrier spots: inside BM's hitbox (never in the gap or the slice), so a carrier rides the band.
    void TestCarriersOnHitbox()
    {
        Kit::WallFrame const f{ { 194.f, -420.f }, 3.14159265f, 86.f, 68.f };
        BM::LineFrontSpec spec;
        spec.facing = f.facing;
        spec.travelYd = f.travelYd;
        spec.widthYd = f.widthYd;
        for (float g : { -20.f, -5.f, 0.f, 11.f, 30.f })
        {
            spec.gaps = { { g, 8.f } };
            BM::Shape const line = BM::Front::LineShape(spec);
            BM::Geo::Pose const pose{ f.start.x, f.start.y, 111.f, f.facing };
            std::vector<std::pair<float, float>> const gaps{ { g, 8.f } };
            std::vector<float> const slots = Kit::WallCarrierSlots(f.widthYd, 6.f, gaps);
            CHECK(!slots.empty());
            for (float t : slots)
                for (float s : { 2.f, 40.f, 84.f })
                {
                    DungeonKit::Vec2 const q = Kit::FromWallCoords(f, s, t);
                    CHECK(BM::Front::Contains(line, pose, spec.gaps, { q.x, q.y, 111.f }));
                }
            DungeonKit::Vec2 const inGap = Kit::FromWallCoords(f, 40.f, std::clamp(g, -30.f, 30.f));
            CHECK(!BM::Front::Contains(line, pose, spec.gaps, { inGap.x, inGap.y, 111.f }));
        }

        for (float slice : { -2.f, 0.f, 1.3f })
            for (float sliceDeg : { 45.f, 60.f })
            {
                BM::ConeFrontSpec cone{ slice, sliceDeg, 7.f, 45.f, 4.f, 8.f };
                BM::Shape const shape = BM::Front::ConeShape(cone);
                BM::Geo::Pose const apex{ 144.f, -260.f, 92.f, BM::Front::ConeFacing(cone) };
                for (float b : Kit::RingCarrierBearings(slice, sliceDeg, 9.f, 4.f))
                {
                    BM::Geo::Vec3 const q{ 144.f + std::cos(b) * 9.f, -260.f + std::sin(b) * 9.f, 92.f };
                    CHECK(BM::Geo::Contains(shape, apex, q));
                }
                BM::Geo::Vec3 const mid{ 144.f + std::cos(slice) * 9.f, -260.f + std::sin(slice) * 9.f, 92.f };
                CHECK(!BM::Geo::Contains(shape, apex, mid));
            }
    }
}

int main()
{
    TestPlacementParity();
    TestTimingParity();
    TestFrameParity();
    TestCarriersOnHitbox();
    return Report("kit_fronts_parity_test");
}
