// Host tests for CrowdPummelerLogic.h (Gnomeregan D5, Crowd Pummeler 9-60 in the glass window): the slice, the arena
// and its spots (S0's), the window's reach (section 7 #27 A, rule 33), the frame's shapes on the pocket (section 7
// #28 A: every pocket cell in exactly one half, the near line from the origin, the lane), the pocket-only damage rule,
// the rounds and the heroic growth, the chain roll and the One-Two (CP1, CP7), the timing (SP's heroic length check),
// the machine's contract timing for the hard mode fist, Trample's area, the knockback, the drill tags.
#include "CrowdPummelerLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <string>
#include <vector>

using namespace GnomereganRework;
using namespace GnomerPummeler;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // A deterministic stand-in for urand(0, n - 1).
    struct Lcg
    {
        std::uint64_t state = 0x9E3779B97F4A7C15ull;

        std::uint32_t operator()(std::uint32_t n)
        {
            state = state * 6364136223846793005ull + 1442695040888963407ull;
            return n ? static_cast<std::uint32_t>((state >> 33) % n) : 0u;
        }
    };

    // Every 0.5 yd cell of the pocket floor (PocketArena, the S0 polygon cut from the mesh).
    std::vector<Vec2> PocketCells()
    {
        std::vector<Vec2> out;
        Arena const pocket = PocketArena();
        for (float x = kPocketBoxMinX; x <= kPocketBoxMaxX; x += 0.5f)
            for (float y = kPocketBoxMinY; y <= kPocketBoxMaxY; y += 0.5f)
                if (pocket.Contains({ x, y }, kPocketFloorZ))
                    out.push_back({ x, y });
        return out;
    }

    void TestSliceAndSpots()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 214460 && kSpellSlice.last == 214489);
        CHECK(SPELL_LEFT_HOOK == 214460 && SPELL_SEEING_STARS == 214469);
        CHECK(ArenaFor(BOSS_CROWD_PUMMELER).Contains(kPummelerSpot.XY(), kPummelerSpot.z));
        CHECK(ArenaFor(BOSS_CROWD_PUMMELER).Contains(kPummelerChestSpot.XY(), kPummelerChestSpot.z));
        CHECK(ArenaFor(BOSS_CROWD_PUMMELER).Contains(kPummelerFrameOrigin.XY(), kPummelerFrameOrigin.z));
        // He floats under the pocket floor, off the pocket's own floor arena (the bots' bounds).
        CHECK(!PocketArena().Contains(kPummelerSpot.XY(), kPummelerSpot.z));
        CHECK(Near(kSpotDepthYd, 4.78f, 0.05f));
    }

    // Section 7 #27 A, rule 33: reach 10 at scale 5, never below, grown above; melee to 11.9 yd on the floor, hunters
    // too close inside 17.2 yd; the stock 8.25 (1.65 x 5) would give 10.0 yd.
    void TestWindowReach()
    {
        CHECK(Near(WindowReach(Tune::kWindowScale), 10.f));
        CHECK(Near(WindowReach(1.f), 10.f));
        CHECK(Near(WindowReach(0.5f), 10.f));
        CHECK(Near(WindowReach(6.f), 12.f));
        CHECK(Near(WindowReach(7.5f), 15.f));
        CHECK(ReachNeedsReset(8.25f, WindowReach(5.f)));     // the engine's rewrite after SetObjectScale(5)
        CHECK(!ReachNeedsReset(10.f, WindowReach(5.f)));
        CHECK(!ReachNeedsReset(10.005f, 10.f));
        float const melee = MeleeFloorReach(WindowReach(5.f));
        CHECK(melee > 11.8f && melee < 12.0f);
        CHECK(Near(MeleeFloorReach(8.25f), 9.96f, 0.1f));
        float const tooClose = HunterTooCloseFloor(WindowReach(5.f));
        CHECK(tooClose > 17.1f && tooClose < 17.3f);
        CHECK(Near(FloorReach(3.f, 4.f), 0.f));
        CHECK(Near(FloorReach(5.f, 3.f), 4.f));

        // The south half of the pocket keeps room for hunters: some floor lies past the too-close line.
        std::vector<Vec2> const cells = PocketCells();
        std::size_t inMelee = 0;
        std::size_t pastTooClose = 0;
        for (Vec2 const& c : cells)
        {
            float const d = DungeonKit::Distance(c, kPummelerSpot.XY());
            inMelee += d < melee ? 1 : 0;
            pastTooClose += d > tooClose ? 1 : 0;
        }
        CHECK(inMelee * 0.25f > 120.f);         // floor melee can stand on (0.25 sq yd a cell)
        CHECK(pastTooClose * 0.25f > 300.f);    // floor a hunter can shoot from
    }

    // Pull and damage only from the pocket box.
    void TestFromThePocket()
    {
        CHECK(FromThePocket(kPummelerFrameOrigin.x, kPummelerFrameOrigin.y, kPummelerFrameOrigin.z));
        CHECK(FromThePocket(kPummelerChestSpot.x, kPummelerChestSpot.y, kPummelerChestSpot.z));
        CHECK(FromThePocket(-905.f, 360.f, -270.f));                    // a jump in the pocket
        CHECK(!FromThePocket(-864.4f, 394.9f, -316.4f));                // Punchograph 3005-D, the lower room
        CHECK(!FromThePocket(-877.f, 364.f, -316.f));                   // right under him
        CHECK(!FromThePocket(-903.f, 326.f, -272.4f));                  // the east corridor (the door route)
        CHECK(!FromThePocket(kPummelerSpot.x, kPummelerSpot.y, kPummelerSpot.z));    // his own spot (his pets: none)
        // His victims: never under the pocket floor; the corridors stay valid.
        CHECK(VictimAllowed(kPocketFloorZ) && VictimAllowed(-272.4f));
        CHECK(!VictimAllowed(-316.4f));
    }

    // Section 7 #28 A: the frame from (-887.0, 364.2), due south; left = east (y < 364.2).
    void TestFrameShapes()
    {
        DungeonKit::ComboFrame const frame = PocketFrame();
        FrameParams const f;
        CHECK(Near(frame.origin.x, -887.f) && Near(frame.origin.y, 364.2f) && Near(frame.facing, DungeonKit::kPi));
        DungeonKit::PlacedShape const left = PlaceShape(frame, Shape::LeftHalf, f);
        DungeonKit::PlacedShape const right = PlaceShape(frame, Shape::RightHalf, f);
        DungeonKit::PlacedShape const pummel = PlaceShape(frame, Shape::Near, f);
        DungeonKit::PlacedShape const clinch = PlaceShape(frame, Shape::Far, f);
        DungeonKit::PlacedShape const lane = PlaceShape(frame, Shape::Lane, f);

        // The hooks: east and west, including the strip at the glass (melee's), excluding the other side.
        CHECK(left.Contains({ -895.f, 355.f }) && !left.Contains({ -895.f, 373.f }));
        CHECK(right.Contains({ -895.f, 373.f }) && !right.Contains({ -895.f, 355.f }));
        CHECK(left.Contains({ -885.5f, 358.f }) && right.Contains({ -885.5f, 370.f }));
        CHECK(left.Contains({ -910.f, 346.f }) && right.Contains({ -910.f, 384.f }));
        // Crowd Pummel within 12 yd of the origin, the Clinch past it to 40.
        CHECK(pummel.Contains({ -887.f, 364.2f }) && pummel.Contains({ -898.9f, 364.2f }));
        CHECK(!pummel.Contains({ -899.5f, 364.2f }) && clinch.Contains({ -899.5f, 364.2f }));
        CHECK(!clinch.Contains({ -890.f, 364.f }) && clinch.Contains({ -910.f, 380.f }));
        // The Uppercut: the center line from the glass to the south wall, 4 yd each side.
        CHECK(lane.Contains({ -884.6f, 364.2f }) && lane.Contains({ -912.f, 364.2f }));
        CHECK(lane.Contains({ -900.f, 360.3f }) && lane.Contains({ -900.f, 368.1f }));
        CHECK(!lane.Contains({ -900.f, 359.f }) && !lane.Contains({ -900.f, 369.5f }));

        // Every pocket cell: in a half (exactly one off the line), on one side of the near line, the lane along it.
        std::vector<Vec2> const cells = PocketCells();
        CHECK(cells.size() * 0.25f > 900.f && cells.size() * 0.25f < 1100.f);    // NM: 968 sq yd
        std::size_t missHalf = 0;
        std::size_t bothHalves = 0;
        std::size_t missRing = 0;
        std::size_t bothRing = 0;
        std::size_t laneOff = 0;
        std::size_t nearEast = 0;
        std::size_t nearWest = 0;
        std::size_t laneCells = 0;
        for (Vec2 const& c : cells)
        {
            bool const l = left.Contains(c);
            bool const r = right.Contains(c);
            bool const offLine = std::fabs(c.y - 364.2f) > 0.01f;
            missHalf += (!l && !r) ? 1 : 0;
            bothHalves += (l && r && offLine) ? 1 : 0;
            bool const n = pummel.Contains(c);
            bool const fa = clinch.Contains(c);
            missRing += (!n && !fa) ? 1 : 0;
            bothRing += (n && fa) ? 1 : 0;
            bool const inLane = lane.Contains(c);
            laneCells += inLane ? 1 : 0;
            laneOff += (inLane != (std::fabs(c.y - 364.2f) <= 4.f + 0.01f)) ? 1 : 0;
            nearEast += (n && l && !r) ? 1 : 0;
            nearWest += (n && r && !l) ? 1 : 0;
        }
        CHECK(missHalf == 0);
        CHECK(bothHalves == 0);
        CHECK(missRing == 0);
        CHECK(bothRing == 0);
        CHECK(laneOff == 0);
        // NM: the near quarters 113 to 129 sq yd at the frame origin (heroic's worst One-Two leaves one of them).
        CHECK(nearEast * 0.25f > 95.f && nearEast * 0.25f < 150.f);
        CHECK(nearWest * 0.25f > 95.f && nearWest * 0.25f < 150.f);
        // The lane is 8 yd wide down the pocket (NM: about 208 sq yd).
        CHECK(laneCells * 0.25f > 170.f && laneCells * 0.25f < 240.f);

        // Melee's floor (within 11.9 yd of him) is inside the near circle: the Pummel moves melee out (section 7
        // #27 A), and Trample (the near side) reaches everyone who could be in his reach. One 0.5 yd cell at the
        // east corner of the glass, (-887.0, 352.0), is 11.8 yd from him and 12.2 from the origin: under 1 sq yd.
        float const melee = MeleeFloorReach(WindowReach(Tune::kWindowScale));
        std::size_t meleeOutside = 0;
        for (Vec2 const& c : cells)
            if (DungeonKit::Distance(c, kPummelerSpot.XY()) < melee)
            {
                meleeOutside += pummel.Contains(c) ? 0 : 1;
                meleeOutside += InTrample(c) ? 0 : 1;
            }
        CHECK(meleeOutside * 0.25f <= 1.f);
    }

    // The machine's frame parameters for another caller (the hard mode fist, section 7 #33 A): near 50 yd of the
    // face, far beyond it, the halves split on the face-to-center line.
    void TestOtherFrame()
    {
        Vec2 const face = kFaceSpots[0].XY();
        DungeonKit::ComboFrame const fist = DungeonKit::FrameFacing(face, kRoomCenter.z, kRoomCenter.XY());
        FrameParams f;
        f.halfReachYd = 140.f;
        f.nearRadiusYd = 50.f;
        f.farOuterYd = 150.f;
        DungeonKit::PlacedShape const nearFist = PlaceShape(fist, Shape::Near, f);
        DungeonKit::PlacedShape const farFist = PlaceShape(fist, Shape::Far, f);
        DungeonKit::PlacedShape const leftFist = PlaceShape(fist, Shape::LeftHalf, f);
        DungeonKit::PlacedShape const rightFist = PlaceShape(fist, Shape::RightHalf, f);
        CHECK(nearFist.Contains(kRoomCenter.XY()));                     // the center is 50 yd from the face
        CHECK(farFist.Contains(kFaceSpots[3].XY()));                    // the opposite face is far
        std::size_t misses = 0;
        Arena const room = RoomArena();
        for (float x = -590.f; x <= -470.f; x += 2.f)
            for (float y = 610.f; y <= 730.f; y += 2.f)
                if (room.Contains({ x, y }, kRoomCenter.z))
                {
                    bool const l = leftFist.Contains({ x, y });
                    bool const r = rightFist.Contains({ x, y });
                    misses += (l || r) ? 0 : 1;
                }
        CHECK(misses == 0);
    }

    // CP1 rounds (normal) and growth (heroic).
    void TestLengths()
    {
        CHECK(RoundFor(100.f) == 1 && RoundFor(66.5f) == 1);
        CHECK(RoundFor(66.f) == 2 && RoundFor(34.f) == 2);
        CHECK(RoundFor(33.f) == 3 && RoundFor(1.f) == 3);
        CHECK(NormalLength(1) == 2 && NormalLength(2) == 3 && NormalLength(3) == 4);
        CHECK(NormalLength(0) == 2 && NormalLength(9) == 4);
        CHECK(HeroicLength(0, 0) == 3);
        CHECK(HeroicLength(1, 0) == 4 && HeroicLength(3, 0) == 6);
        CHECK(HeroicLength(2, 3) == 8);                                 // two thrown, three landed: 3 + 2 + 3
        CHECK(HeroicLength(1000, 1000) == Tune::kMaxPunches);           // the kit's limit, never a design cap
        CHECK(Tune::kMaxPunches * 2 <= 255);                            // a One-Two each: the kit's uint8 indexes fit
    }

    // CP1 / CP7: the chain roll.
    void TestRoll()
    {
        Lcg rng;
        std::uint32_t pairs = 0;
        std::uint32_t pairSlots = 0;
        std::set<int> normalShapes;
        std::set<int> heroicShapes;
        for (int run = 0; run < 2000; ++run)
        {
            std::vector<PunchRoll> const normal = RollChain(false, 4, rng);
            CHECK(normal.size() == 4);
            for (std::size_t i = 0; i < normal.size(); ++i)
            {
                PunchRoll const& p = normal[i];
                CHECK(!p.paired);
                CHECK(p.shape == Shape::LeftHalf || p.shape == Shape::RightHalf || p.shape == Shape::Near);
                normalShapes.insert(int(p.shape));
                if (i > 0)
                    CHECK(p.shape != normal[i - 1].shape);              // no free punch
            }
            std::vector<PunchRoll> const heroic = RollChain(true, 8, rng);
            CHECK(heroic.size() == 8);
            for (std::size_t i = 0; i < heroic.size(); ++i)
            {
                PunchRoll const& p = heroic[i];
                heroicShapes.insert(int(p.shape));
                if (p.paired)
                {
                    CHECK(i + 1 >= Tune::kOneTwoFromPunch);             // from the fourth punch on
                    CHECK(IsValidOneTwo(p));
                    heroicShapes.insert(int(*p.paired));
                    ++pairs;
                }
                else if (i > 0 && !heroic[i - 1].paired)
                    CHECK(p.shape != heroic[i - 1].shape);
                pairSlots += (i + 1 >= Tune::kOneTwoFromPunch) ? 1 : 0;
            }
        }
        CHECK(normalShapes.size() == 3);
        CHECK(heroicShapes.size() == 5);
        // Half of the punches from the fourth on (section 7 #37 A), within 5 points over 10,000 slots.
        float const share = float(pairs) / float(pairSlots);
        CHECK(share > 0.45f && share < 0.55f);
        CHECK(RollChain(true, 500, rng).size() == Tune::kMaxPunches);
        CHECK(RollChain(false, 0, rng).empty());
    }

    // CP1 timing: SP's heroic check (3, 4, 5 and 6 punches "about 7, 9, 11 and 13 sec"), normal's 1.5 s floor.
    void TestTiming()
    {
        CHECK(ChainLengthMs(true, 3) == 6200);
        CHECK(ChainLengthMs(true, 4) == 8400);
        CHECK(ChainLengthMs(true, 5) == 10600);
        CHECK(ChainLengthMs(true, 6) == 12800);
        CHECK(ChainLengthMs(false, 2) == 5500);
        CHECK(ChainLengthMs(false, 3) == 8500);
        CHECK(ChainLengthMs(false, 4) == 11500);
        std::vector<DungeonKit::PunchTimes> const t = DungeonKit::ComboTimeline(PummelerTiming(false), 3);
        CHECK(t[0].callFrom == 0 && t[0].callTo == 1000 && t[2].callFrom == 2000);
        CHECK(t[0].liveFrom == 3000 && t[0].strikeAt == 4500);
        CHECK(t[1].strikeAt - t[1].liveFrom == Tune::kLiveMs.normal);
        CHECK(t[2].strikeAt == 8500);
        std::vector<DungeonKit::PunchTimes> const h = DungeonKit::ComboTimeline(PummelerTiming(true), 4);
        CHECK(h[0].strikeAt == 4800 && h[3].strikeAt == 8400);
        CHECK(h[1].liveFrom == h[1].strikeAt - 800);
        // A punch is reported a registry tick after its strike.
        CHECK(!PunchReportDue(4500, 4500) && PunchReportDue(4900, 4500));

        // The contract's timing for the hard mode fist (ruling 69: wind-up 4 s, all three drawn at once, 2.5 s apart,
        // no separate live marker): strikes at 4.0, 6.5 and 9.0 s.
        DungeonKit::ComboTiming const fist = KitTiming(0, 4000, 0, 2500, true);
        CHECK(fist.mode == DungeonKit::ComboCallMode::AllAtOnce);
        std::vector<DungeonKit::PunchTimes> const ft = DungeonKit::ComboTimeline(fist, 3);
        CHECK(ft[0].strikeAt == 4000 && ft[1].strikeAt == 6500 && ft[2].strikeAt == 9000);
        CHECK(ft[2].callFrom == 0);
        DungeonKit::ComboTiming const seq = KitTiming(1000, 4000, 1500, 2000, false);
        CHECK(seq.mode == DungeonKit::ComboCallMode::Sequential && seq.callMs == 1000);
    }

    // CP4's knockback: about 7.5 yd (flight 2 x lift / g); Uppercut's knock up stays under fall damage.
    void TestKnocks()
    {
        float constexpr kGravity = 19.29110527f;
        float const flight = 2.f * Tune::kPummelKnockSpeedZ / kGravity;
        CHECK(Near(Tune::kPummelKnockSpeedXY * flight, 7.5f, 0.2f));
        float const height = Tune::kUppercutKnockSpeedZ * Tune::kUppercutKnockSpeedZ / (2.f * kGravity);
        CHECK(height > 3.f && height < 5.f);
    }

    // CP8 Trample: the near side; the chest and the far south are out of it.
    void TestTrample()
    {
        CHECK(InTrample(kPummelerFrameOrigin.XY()));
        CHECK(InTrample({ -885.f, 356.f }));
        CHECK(!InTrample(kPummelerChestSpot.XY()));                     // 12.04 yd from the origin
        CHECK(!InTrample({ -910.f, 364.f }));
        CHECK(Tune::kTramplePct.normal == 8.f && Tune::kTramplePct.heroic == 12.f);
        CHECK(Tune::kTrampleFirstMs < Tune::kComboFirstMs);
    }

    // The drill's tags (BM MechanicDrill.h kGnTagLeftHook 60 .. kGnTagUppercut 64): distinct, in the band.
    void TestTags()
    {
        std::set<std::uint32_t> seen;
        for (DrillTag const& t : kDrillTags)
        {
            CHECK(t.tag >= 60 && t.tag <= 69);
            CHECK(seen.insert(t.tag).second);
        }
        CHECK(kDrillTags[0].tag == 60 && kDrillTags[4].tag == 64);
        CHECK(TAG_TRAMPLE >= 60 && TAG_TRAMPLE <= 69 && !seen.count(TAG_TRAMPLE));
        CHECK(std::string(ShapeName(Shape::Lane)) == "uppercut");
    }

    // R-1-B M1: the bots' ranged band starts past the hunters' too-close line (3D, from his sunken origin), leaves room
    // on the pocket floor, and keeps a healer within 40 yd of a tank in melee on the far side.
    void TestRangedBand()
    {
        float const reach = WindowReach(Tune::kWindowScale);
        CHECK(Tune::kRangedBandMinYd > HunterTooCloseFloor(reach) + 1.5f);
        CHECK(PastHunterLine(Tune::kRangedBandMinYd, reach));
        CHECK(!PastHunterLine(HunterTooCloseFloor(reach) - 0.1f, reach));
        CHECK(PastHunterLine(HunterTooCloseFloor(reach) + 0.1f, reach));
        CHECK(Tune::kRangedBandMinYd > MeleeFloorReach(reach));
        CHECK(Tune::kRangedBandMaxYd + MeleeFloorReach(reach) < 40.f);
        std::size_t inBand = 0;
        for (Vec2 const& cell : PocketCells())
        {
            float const d = DungeonKit::Distance(kPummelerSpot.XY(), cell);
            if (d >= Tune::kRangedBandMinYd && d <= Tune::kRangedBandMaxYd)
                ++inBand;
        }
        CHECK(inBand * 0.25f > 250.f);     // about 345 sq yd of the pocket's 1,030 lie in the band

        // RF-1 Minor-4: the blind corner (NAVMESH D2's failing samples, each with its 3 yd cell) is clipped out, and
        // enough of the band stays to stand in.
        for (float x = -899.f; x <= -893.f; x += 3.f)
            for (float y = 379.f; y <= 388.f; y += 3.f)
                for (float dx : { -1.5f, 1.5f })
                    for (float dy : { -1.5f, 1.5f })
                        CHECK(InBlindCorner({ x + dx, y + dy }));
        CHECK(!InBlindCorner(kPummelerSpot.XY()));
        std::size_t clear = 0, clipped = 0;
        for (Vec2 const& cell : PocketCells())
        {
            float const d = DungeonKit::Distance(kPummelerSpot.XY(), cell);
            if (d < Tune::kRangedBandMinYd || d > Tune::kRangedBandMaxYd)
                continue;
            ++(InBlindCorner(cell) ? clipped : clear);
        }
        CHECK(clipped > 0);
        CHECK(clear * 0.25f > 200.f);       // about 270 sq yd clear, about 75 clipped
    }

    // R-1-B M2: a pet's chase loses its angle once per new chase, and again while it stays out of reach.
    // RF-1 Minor-3: "new" means not tracked since a fix (no generator address), and a spline aimed off the pocket is
    // fixed again.
    void TestPetChase()
    {
        CHECK(PetChaseNeedsFix(false, true, false, 0));
        CHECK(PetChaseNeedsFix(false, false, false, 0));
        CHECK(!PetChaseNeedsFix(true, true, false, 60000));
        CHECK(!PetChaseNeedsFix(true, false, false, Tune::kPetChaseRetryMs - 1));
        CHECK(PetChaseNeedsFix(true, false, false, Tune::kPetChaseRetryMs));
        CHECK(!PetChaseNeedsFix(true, true, true, Tune::kPetChaseAimRetryMs - 1));
        CHECK(PetChaseNeedsFix(true, true, true, Tune::kPetChaseAimRetryMs));
        static_assert(Tune::kPetChaseAimRetryMs < Tune::kPetChaseRetryMs);
        // RF-2 Minor-3: the sweep covers the pet and every PetAI controllable guardian (Feral Spirit, Treants,
        // Shadowfiend), not totems, charmed mobs or script-AI guardians.
        CHECK(SweepsControlled(true, false, true, false, false));       // a hunter or warlock pet
        CHECK(SweepsControlled(true, true, false, false, false));       // a pet on a script AI: as before
        CHECK(SweepsControlled(false, true, true, false, false));       // Feral Spirit, a Treant, the Shadowfiend
        CHECK(!SweepsControlled(false, true, false, false, false));     // a script-AI guardian keeps its own chase
        CHECK(!SweepsControlled(false, false, false, false, false));    // a plain guardian (no PetAI, no control)
        CHECK(!SweepsControlled(false, true, true, true, false));       // a totem
        CHECK(!SweepsControlled(false, false, true, false, true));      // a charmed mob
        CHECK(!SweepsControlled(true, true, true, false, true));

        // The angled chase aims at his back, the glass (off the pocket); a no-angle one at his pocket side.
        Point3 const& spot = kPummelerSpot;
        CHECK(!FromThePocket(spot.x + 3.f, spot.y, kPocketFloorZ));
        CHECK(FromThePocket(spot.x - 3.f, spot.y, kPocketFloorZ));

        // The tracker: a pet seen chasing him on every sweep since its fix stays tracked; one sweep without it (a
        // re-chase that reuses the old generator's memory) and the next chase reads as new.
        PetChaseTracker<int> pets;
        std::uint32_t at = 0;
        pets.Begin();
        CHECK(!pets.Seen(7, at));
        pets.Fixed(7, 100);
        pets.End();
        pets.Begin();
        CHECK(pets.Seen(7, at) && at == 100);
        pets.End();
        pets.Begin();       // the pet stopped (AttackStop, a recall, a new target): not seen
        pets.End();
        CHECK(pets.Size() == 0);
        pets.Begin();
        CHECK(!pets.Seen(7, at));
        pets.End();
        pets.Fixed(7, 300);
        pets.Clear();
        CHECK(pets.Size() == 0);
    }
}

int main()
{
    TestSliceAndSpots();
    TestWindowReach();
    TestFromThePocket();
    TestFrameShapes();
    TestOtherFrame();
    TestLengths();
    TestRoll();
    TestTiming();
    TestKnocks();
    TestTrample();
    TestTags();
    TestRangedBand();
    TestPetChase();
    return Report("gnomer_pummeler_test");
}
