// Host tests for GreenskinLogic.h (WP-B7): the deck frame and the lanes inside it, the volley specs, the
// once-per-volley memory, the harpoon target pick and the rope's geometry; the ship's bounds and the grip
// (playtest 1).
#include "GreenskinLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <string>
#include <vector>

namespace
{
    using namespace Greenskin;
    using DeadminesKit::Vec2;

    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    bool NearV(Vec2 a, Vec2 b, float eps = 0.05f)
    {
        return Near(a.x, b.x, eps) && Near(a.y, b.y, eps);
    }

    void TestSlice()
    {
        CHECK(kSlice.first == 205340u);
        CHECK(kSlice.Contains(kSlice.last));
        for (std::uint32_t id : { SPELL_FIRE_ON_MY_MARK_HIT, SPELL_CROSSFIRE_HIT, SPELL_BURNING_DECK,
                 SPELL_FIRE_ON_MY_MARK_CAST, SPELL_CROSSFIRE_CAST, SPELL_REEL_EM_IN, SPELL_HARPOONED, SPELL_REEL_HIT,
                 SPELL_GRAPPLING_HOOK })
            CHECK(kSlice.Contains(id));
        // the rope anchor is the reservation's "harpoon rope unit" slot, inside creature 300420-300449
        CHECK(kNpcRopeAnchor >= 300420u && kNpcRopeAnchor <= 300449u);
    }

    // The deck frame's corners: the west rail at the sterncastle face (origin), the bow end at the bow tip's x, the
    // east rail 36 yd away (+y is west, so east is -y).
    void TestDeckFrame()
    {
        CHECK(NearV(FramePoint(kDeck, 0.f, 0.f), { -53.5f, -802.f }));
        CHECK(NearV(FramePoint(kDeck, kDeck.sizeX, 0.f), { -107.5f, -802.f }));
        CHECK(NearV(FramePoint(kDeck, 0.f, kDeck.sizeY), { -53.5f, -838.f }));
        CHECK(NearV(FramePoint(kDeck, kDeck.sizeX, kDeck.sizeY), { -107.5f, -838.f }));
        // the centreline (y -820) is half way across, at the sterncastle face
        CHECK(Near(ToFrame(kDeck, DeadminesRework::kDeckSternCenter).y, 18.f));
        CHECK(Near(ToFrame(kDeck, DeadminesRework::kDeckSternCenter).x, 0.f));
        // round trip
        Vec2 const p{ -80.f, -815.f };
        Vec2 const q = ToFrame(kDeck, p);
        CHECK(NearV(FramePoint(kDeck, q.x, q.y), p));
        // both bosses, the bow tip and Greenskin's patrol (path 793330) are on the frame
        CHECK(InsideFrame(kDeck, DeadminesRework::kGreenskinSpawn));
        CHECK(InsideFrame(kDeck, DeadminesRework::kVanCleefSpawn));
        CHECK(InsideFrame(kDeck, DeadminesRework::kDeckBowTip));
        for (Vec2 wp : { Vec2{ -83.58f, -833.45f }, Vec2{ -102.49f, -824.70f }, Vec2{ -102.28f, -814.22f },
                 Vec2{ -92.37f, -808.03f }, Vec2{ -56.08f, -808.81f }, Vec2{ -56.86f, -831.47f } })
            CHECK(InsideFrame(kDeck, wp));
        // off the deck: the sterncastle behind the face, the water past each rail
        CHECK(!InsideFrame(kDeck, { -45.f, -820.f }));
        CHECK(!InsideFrame(kDeck, { -70.f, -800.f }));
        CHECK(!InsideFrame(kDeck, { -70.f, -840.f }));
    }

    // Every lane the registry can place (offset 0 to span - width) runs rail to rail or stern to bow inside the frame.
    void TestLanesInsideDeck()
    {
        for (LaneAxis axis : { LaneAxis::Across, LaneAxis::Along })
        {
            float const span = SpanFor(kDeck, axis);
            for (float offset = 0.f; offset <= span - 4.f + 1e-3f; offset += 0.5f)
            {
                LaneSegment const lane = LaneOnFrame(kDeck, axis, offset, 4.f);
                CHECK(InsideFrame(kDeck, lane.from));
                CHECK(InsideFrame(kDeck, lane.to));
                // both edges of the lane stay inside too
                Vec2 const a = ToFrame(kDeck, lane.from);
                if (axis == LaneAxis::Across)
                {
                    CHECK(a.x - 2.f >= -0.01f && a.x + 2.f <= kDeck.sizeX + 0.01f);
                    CHECK(Near(DeadminesKit::Distance(lane.from, lane.to), kDeck.sizeY));   // rail to rail, 36 yd
                    CHECK(Near(lane.from.y, -802.f) && Near(lane.to.y, -838.f));
                }
                else
                {
                    CHECK(a.y - 2.f >= -0.01f && a.y + 2.f <= kDeck.sizeY + 0.01f);
                    CHECK(Near(DeadminesKit::Distance(lane.from, lane.to), kDeck.sizeX));   // stern to bow, 54 yd
                    CHECK(Near(lane.from.x, -53.5f) && Near(lane.to.x, -107.5f));
                }
            }
        }
        // across lanes cross the deck along the map y axis (perpendicular to the keel)
        LaneSegment const across = LaneOnFrame(kDeck, LaneAxis::Across, 10.f, 4.f);
        CHECK(Near(across.from.x, across.to.x));
        CHECK(Near(across.from.x, -53.5f - 12.f));
        LaneSegment const along = LaneOnFrame(kDeck, LaneAxis::Along, 0.f, 4.f);
        CHECK(Near(along.from.y, along.to.y));
        CHECK(Near(along.from.y, -804.f));
    }

    void TestVolleySpecs()
    {
        LaneVolley const n = kFireOnMyMark(false);
        LaneVolley const h = kFireOnMyMark(true);
        // GS2 normal: 4 lanes, 4 yd, gaps >= 6, 2 s, 40%; no crossfire, nothing burns
        CHECK(n.across == 4 && n.along == 0 && n.Lanes() == 4);
        CHECK(n.width == 4.f && n.minGap == 6.f && n.warnMs == 2000 && n.lanePct == 40.f);
        CHECK(n.Crossings() == 0);
        // heroic: 4 across + 2 bow to stern, 2.5 s, 8 burning crossings 20 s at 10% per 1 s
        CHECK(h.across == 4 && h.along == 2 && h.Lanes() == 6);
        CHECK(h.warnMs == 2500 && h.lanePct == 40.f);
        CHECK(h.burnCrossings && h.Crossings() == 8);
        CHECK(h.burnMs == 20000 && h.burnTickMs == 1000 && h.burnPct == 10.f);
        CHECK(h.acrossTag == TAG_FIRE_ON_MY_MARK && h.alongTag == TAG_CROSSFIRE && h.cellTag == TAG_BURNING_CROSSING);
        // the lanes fit the frame with their gaps (no even-spacing fallback): across over 54 yd, along over 36 yd
        CHECK(LanesFit(SpanFor(kDeck, LaneAxis::Across), h.across, h.width, h.minGap));
        CHECK(LanesFit(SpanFor(kDeck, LaneAxis::Along), h.along, h.width, h.minGap));
        // VanCleef's VC3 on normal: 3 lanes across (B8 builds it the same way)
        CHECK(LanesFit(SpanFor(kDeck, LaneAxis::Across), 3, 4.f, 6.f));
        // a volley that cannot fit is caught
        CHECK(!LanesFit(SpanFor(kDeck, LaneAxis::Along), 5, 4.f, 6.f));
        // the crossings only burn with lanes on both axes
        LaneVolley noAlong = h;
        noAlong.along = 0;
        CHECK(noAlong.Crossings() == 0);
        // coverage, normal: 4 x 4 yd of the 54 yd length is about 30% of the frame
        float const cover = n.across * n.width / kDeck.sizeX;
        CHECK(cover > 0.29f && cover < 0.30f);
    }

    void TestVolleyMemory()
    {
        VolleyMemory m;
        std::uint64_t const boss = 0xF130000287000001ull;
        std::uint64_t const other = 0xF13000027F000002ull;
        CHECK(!m.AlreadyHit(boss, 7, 1000));
        m.Record(boss, 7, 1000);
        CHECK(m.AlreadyHit(boss, 7, 1000));         // the second lane of the same volley skips him
        CHECK(m.AlreadyHit(boss, 7, 1000 + kVolleyWindowMs));
        CHECK(!m.AlreadyHit(boss, 8, 1000));        // another player is still hit
        CHECK(!m.AlreadyHit(other, 7, 1000));       // another owner's volley (VanCleef) is its own
        CHECK(!m.AlreadyHit(boss, 7, 1000 + kVolleyWindowMs + 1));     // the next volley hits him again
        m.Record(boss, 8, 21000);                   // a new volley starts a new list
        CHECK(!m.AlreadyHit(boss, 7, 21000));
        CHECK(m.AlreadyHit(boss, 8, 21000));
        m.Record(boss, 8, 21000);
        CHECK(m.Owners() == 1);
        m.Forget(boss);
        CHECK(m.Owners() == 0);
        CHECK(!m.AlreadyHit(boss, 8, 21000));
    }

    struct Seq
    {
        std::vector<std::uint32_t> picks;
        std::size_t i = 0;

        std::uint32_t operator()(std::uint32_t n)
        {
            std::uint32_t const v = i < picks.size() ? picks[i] : 0;
            ++i;
            return n ? v % n : 0;
        }
    };

    void TestHarpoonPick()
    {
        std::vector<HarpoonCandidate> const group{
            { 1, 3.f, true },       // the tank, never
            { 2, 4.f, false },      // melee, only as a fallback
            { 3, 15.f, false },
            { 4, 22.f, false },
            { 5, 45.f, false },     // out of range
        };
        // normal: one target from the far pool
        for (std::uint32_t r = 0; r < 4; ++r)
        {
            Seq rand{ { r } };
            std::vector<std::uint64_t> const one = PickHarpoonTargets(group, kHarpoonCount(false), rand);
            CHECK(one.size() == 1);
            CHECK(one[0] == 3 || one[0] == 4);
        }
        // heroic: two different targets, both far
        Seq r2{ { 1, 0 } };
        std::vector<std::uint64_t> const two = PickHarpoonTargets(group, kHarpoonCount(true), r2);
        CHECK(two.size() == 2);
        CHECK(two[0] != two[1]);
        CHECK((two[0] == 3 || two[0] == 4) && (two[1] == 3 || two[1] == 4));
        // only one far player on heroic: the second rope goes to the closer non-tank
        std::vector<HarpoonCandidate> const tight{ { 1, 3.f, true }, { 2, 4.f, false }, { 3, 12.f, false } };
        Seq r3{ { 0, 0 } };
        std::vector<std::uint64_t> const mixed = PickHarpoonTargets(tight, 2, r3);
        CHECK(mixed.size() == 2 && mixed[0] == 3 && mixed[1] == 2);
        // only the tank (or nobody in range): no harpoon
        std::vector<HarpoonCandidate> const solo{ { 1, 3.f, true }, { 9, 50.f, false } };
        Seq r4{ {} };
        CHECK(PickHarpoonTargets(solo, 2, r4).empty());
        // the 10 yd edge counts as far
        std::vector<HarpoonCandidate> const edge{ { 2, 9.9f, false }, { 3, 10.f, false } };
        Seq r5{ { 0 } };
        std::vector<std::uint64_t> const e = PickHarpoonTargets(edge, 1, r5);
        CHECK(e.size() == 1 && e[0] == 3);
    }

    void TestRopeGeometry()
    {
        Vec2 const boss{ 0.f, 0.f };
        Vec2 const target{ 20.f, 0.f };
        // on the rope, mid-way
        CHECK(StandsOnRope(boss, target, { 10.f, 0.5f }));
        CHECK(StandsOnRope(boss, target, { 10.f, -kRopeStandYd }));
        CHECK(!StandsOnRope(boss, target, { 10.f, kRopeStandYd + 0.1f }));
        // the tank at his feet never cuts it
        CHECK(!StandsOnRope(boss, target, { 2.f, 0.f }));
        CHECK(!StandsOnRope(boss, target, { kRopeBossClearYd - 0.1f, 0.f }));
        CHECK(StandsOnRope(boss, target, { kRopeBossClearYd + 0.1f, 0.f }));
        // nor the target's own end, nor anyone past it
        CHECK(!StandsOnRope(boss, target, { 19.f, 0.f }));
        CHECK(!StandsOnRope(boss, target, { 24.f, 0.f }));
        // a rope too short to stand on
        CHECK(!StandsOnRope(boss, { 6.f, 0.f }, { 3.f, 0.f }));
        // distance to the segment
        float along = 0.f;
        CHECK(Near(DistanceToSegment(boss, target, { 5.f, 3.f }, &along), 3.f));
        CHECK(Near(along, 5.f));
        CHECK(Near(DistanceToSegment(boss, target, { -3.f, 4.f }), 5.f));
        // snap at 25 yd
        CHECK(!RopeSnapped(24.9f));
        CHECK(RopeSnapped(25.f));
        // the object at the midpoint, moved when the midpoint drifts more than 3 yd
        CHECK(NearV(RopeMidpoint(boss, target), { 10.f, 0.f }));
        CHECK(!RopeObjectNeedsMove({ 10.f, 0.f }, { 12.f, 0.f }));
        CHECK(RopeObjectNeedsMove({ 10.f, 0.f }, { 13.5f, 0.f }));
        // reeled to 2.5 yd in front of him
        CHECK(NearV(ReelDestination(boss, 0.f), { kReelFrontYd, 0.f }));
        CHECK(NearV(ReelDestination({ -59.6f, -820.1f }, 3.14159265f), { -62.1f, -820.1f }));
    }

    void TestRopeStanders()
    {
        RopeStanders s;
        CHECK(!s.Update(7, true, 400));
        CHECK(!s.Update(7, true, 400));
        CHECK(s.Update(7, true, 200));             // 1 s on the rope cuts it
        s.Clear();
        CHECK(!s.Update(7, true, 600));
        CHECK(!s.Update(7, false, 100));           // stepped off: starts again
        CHECK(!s.Update(7, true, 600));
        CHECK(!s.Update(8, true, 900));            // two players count separately
        CHECK(s.Update(7, true, 400));
        CHECK(s.Update(8, true, 100));
        CHECK(s.Update(9, true, kRopeCutMs));      // one long tick
    }

    // Timers: the harpoon (cast and rope) never overlaps the volley's cast bar on either difficulty, and the first
    // casts land on the build spec's seconds.
    void TestTimeline()
    {
        CHECK(kFireFirstMs == 8000 && kFireEveryMs == 20000);
        CHECK(kReelFirstMs == 12000 && kReelEveryMs == 20000);
        CHECK(kCleaveFirstMinMs == 1000 && kCleaveFirstMaxMs == 7000 && kCleaveMinMs == 10000
            && kCleaveMaxMs == 15000);
        CHECK(kRopeMs == 4000 && kReelCastMs == 2000);
        for (bool heroic : { false, true })
        {
            std::uint32_t const warn = kFireOnMyMark(heroic).warnMs;
            for (std::uint32_t k = 0; k < 6; ++k)
            {
                std::uint32_t const fireStart = kFireFirstMs + k * kFireEveryMs;
                std::uint32_t const fireEnd = fireStart + warn;
                for (std::uint32_t j = 0; j < 6; ++j)
                {
                    std::uint32_t const reelStart = kReelFirstMs + j * kReelEveryMs;
                    std::uint32_t const reelEnd = reelStart + kReelCastMs + kRopeMs;
                    CHECK(reelEnd <= fireStart || reelStart >= fireEnd);
                }
            }
        }
        CHECK(kReelPct(false) == 30.f && kReelPct(true) == 30.f);
        CHECK(kHarpoonCount(false) == 1 && kHarpoonCount(true) == 2);
        // the snap distance is reachable within the rope's 4 s from the minimum target distance at 7 yd/s
        CHECK((kSnapYd - kHarpoonMinYd) / 7.f < kRopeMs / 1000.f);
    }

    void TestRopeEndNames()
    {
        CHECK(std::string(RopeEndName(RopeEnd::Snapped)) == "snapped");
        CHECK(std::string(RopeEndName(RopeEnd::Reeled)) == "reeled");
        CHECK(std::string(RopeEndName(RopeEnd::Clicked)) == "cut-by-click");
        CHECK(std::string(RopeEndName(RopeEnd::Stood)) == "cut-by-standing");
    }
    // Playtest 1: "on the ship" (frame box + z band), checked on the measured deck (NAVMESH-REPORT section 2).
    void TestShipBounds()
    {
        float const deckZ = 41.f;
        // every boss spot, the corners of the open deck, the side walkways, the bow
        CHECK(OnShip(DeadminesRework::kGreenskinSpawn, 41.6f));
        CHECK(OnShip(DeadminesRework::kVanCleefSpawn, 39.3f));
        CHECK(OnShip({ -55.f, -802.5f }, 42.f));        // west rail at the sterncastle face
        CHECK(OnShip({ -63.f, -840.f }, 42.f));         // east rail at the widest station
        CHECK(OnShip({ -45.f, -805.f }, 43.f));         // west stern walkway
        CHECK(OnShip({ -45.f, -834.f }, 43.f));         // east stern walkway
        CHECK(OnShip(DeadminesRework::kDeckBowTip, 38.f));
        CHECK(OnShip({ -59.f, -803.f }, 44.5f));        // the gangplank's deck end
        CHECK(OnShip(DeadminesRework::kPowderKegSpot, DeadminesRework::kPowderKegZ));
        // jumping on the deck stays aboard
        CHECK(OnShip(DeadminesRework::kGreenskinSpawn, 41.6f + 2.5f));
        // off: the scaffold past the gangplank, the dock, the water, the bowsprit, past the east rail
        CHECK(!OnShip({ -60.f, -795.f }, 39.f));        // scaffold (y -783..-800)
        CHECK(!OnShip({ -60.f, -799.5f }, 44.5f));      // the gangplank over the scaffold
        CHECK(!OnShip({ -22.8f, -797.3f }, 20.4f));     // Mr. Smite's dock
        CHECK(!OnShip(DeadminesRework::kGreenskinSpawn, 0.1f));    // the water under the ship
        CHECK(!OnShip({ -120.f, -822.f }, 39.f));       // the bowsprit
        CHECK(!OnShip({ -63.f, -845.f }, deckZ));       // overboard, east
        CHECK(!OnShip({ -67.6f, -853.7f }, 17.1f));     // Cookie's spot on the cove floor
        // the rigging and the sterncastle top are off (above the band)
        CHECK(!OnShip({ -80.f, -820.f }, 55.f));
        CHECK(!OnShip({ -40.f, -820.f }, 51.f));
    }

    void TestGripLanding()
    {
        Vec2 const boss = DeadminesRework::kGreenskinSpawn;
        // from the scaffold (west): lands 8 yd west of him, inside the stern landing box
        Vec2 const west = GripLanding(boss, { -60.f, -790.f });
        CHECK(kGripLandBox.Contains(west));
        CHECK(Near(DeadminesKit::Distance(boss, west), kGripLandYd, 0.6f) || west.y == kGripLandBox.maxY);
        // from the water far off the bow, or from the dock: always inside the box, always on the ship
        for (Vec2 const from : { Vec2{ -130.f, -820.f }, Vec2{ -22.8f, -797.3f }, Vec2{ -67.6f, -853.7f },
                 Vec2{ boss.x, boss.y } })
        {
            Vec2 const land = GripLanding(boss, from);
            CHECK(kGripLandBox.Contains(land));
            CHECK(OnShip(land, 41.f));
        }
        // Greenskin at the forward holes (he chased someone there): the landing is still the open stern deck
        Vec2 const fromHoles = GripLanding({ -95.f, -820.f }, { -95.f, -850.f });
        CHECK(kGripLandBox.Contains(fromHoles));
        // the box is inside the ship bounds
        CHECK(OnShip({ kGripLandBox.minX, kGripLandBox.minY }, 41.f) && OnShip({ kGripLandBox.maxX, kGripLandBox.maxY },
            41.f));
    }

    void TestGripTracker()
    {
        GripTracker t;
        // on the ship: never
        for (int i = 0; i < 20; ++i)
            CHECK(!t.Update(1, true, kGripCheckMs));
        // off: after the grace (1.5 s), not before
        std::uint32_t off = 0;
        bool fired = false;
        while (!fired && off < 10000)
        {
            off += kGripCheckMs;
            fired = t.Update(1, false, kGripCheckMs);
        }
        CHECK(fired && off == kGripGraceMs);
        t.Gripped(1);
        // mid-air: still off, but the cooldown holds it
        CHECK(!t.Update(1, false, kGripCheckMs));
        CHECK(!t.Update(1, false, kGripCooldownMs - 2 * kGripCheckMs));
        // the cooldown ran out and it stayed off past the grace: again
        CHECK(t.Update(1, false, kGripCheckMs));
        // a knockback that lands back on deck within the grace: nothing
        GripTracker k;
        CHECK(!k.Update(2, false, 1000));
        CHECK(!k.Update(2, true, kGripCheckMs));
        CHECK(!k.Update(2, false, 1000));
        // the pull grips anyone off at once, unless just gripped
        GripTracker pull;
        CHECK(pull.PullNow(3, false));
        CHECK(!pull.PullNow(3, true));
        pull.Gripped(3);
        CHECK(!pull.PullNow(3, false));
        pull.Clear();
        CHECK(pull.Size() == 0 && pull.PullNow(3, false));
    }
}

int main()
{
    TestSlice();
    TestDeckFrame();
    TestLanesInsideDeck();
    TestVolleySpecs();
    TestVolleyMemory();
    TestHarpoonPick();
    TestRopeGeometry();
    TestRopeStanders();
    TestTimeline();
    TestRopeEndNames();
    TestShipBounds();
    TestGripLanding();
    TestGripTracker();
    return Report("greenskin_test");
}
