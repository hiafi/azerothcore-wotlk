// Host tests for ThermapluggHardModeMachinesLogic.h (Gnomeregan D6Hb, the Whole Workshop part b): the slice, the tags
// (G1 row 10) and texts, the loads (MT15, ruling 45) and the console line, the Voltage rules on him (MT21, MT22: the
// machine's pure clock with the hard mode's numbers), the lights' start and reach (MT23), and the fist (MT24, rulings
// 68 and 69, section 7 #33 A): its frame from every face, the halves and near / far covering the room exactly once,
// near's area per face, the numerals' spots, the timing (4.0 / 6.5 / 9.0 s), the roll, and every chain survivable
// from the room's center at run speed.
#include "ThermapluggHardModeMachinesLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace GnomereganRework;
using namespace GnomerSchematics;

namespace
{
    float constexpr kFloorZ = -326.5f;
    float constexpr kCellYd = 1.f;
    float constexpr kRunYdPerSec = 7.f;     // a player's run speed

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

    // Every 1 yd cell of Thermaplugg's room (RoomArena, S0's polygon and the bowl disc).
    std::vector<Vec2> RoomCells()
    {
        std::vector<Vec2> out;
        Arena const room = RoomArena();
        for (float x = -600.f; x <= -460.f; x += kCellYd)
            for (float y = 600.f; y <= 740.f; y += kCellYd)
                if (room.Contains({ x, y }, kFloorZ))
                    out.push_back({ x, y });
        return out;
    }

    void TestSliceTagsTexts()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 214580 && kSpellSlice.last == 214619);
        CHECK(SPELL_HMB_VOLTAGE == 214580 && SPELL_HMB_FACE_LIGHT == 214586);
        CHECK(kSpellSlice.first + kSpellCount - 1 == SPELL_HMB_FACE_LIGHT);
        // Every spell is inside the slice and none is another WP's.
        for (IdSlice const& other : kSpellSlices)
            if (other.first != kSpellSlice.first)
                CHECK(!other.Contains(SPELL_HMB_VOLTAGE) && !other.Contains(SPELL_HMB_FACE_LIGHT));

        // G1 row 10: 80-85 (reported); the lights' floor one past the lights (D4's rule); the drill names unique.
        CHECK(TAG_HMB_MINES == 80 && TAG_HMB_PUDDLES == 81 && TAG_HMB_LIGHTS == 82 && TAG_HMB_LIGHTS_FLOOR == 83);
        CHECK(TAG_HMB_FIST == 84 && TAG_HMB_JUSTICE == 85);
        std::set<std::uint32_t> tags;
        for (DrillTag const& t : kDrillTags)
            tags.insert(t.tag);
        CHECK(tags.size() == kDrillTags.size());
        CHECK(!tags.count(TAG_HMB_LIGHTS_FLOOR));
        // Never one of D6's (70-79) nor below the packages' first tag.
        for (std::uint32_t const t : tags)
            CHECK(t >= GnomerThermaplugg::kFirstPackageTag && t <= 85);

        // Texts: D6's package groups are 9 to 11; D6Hb's 10 and 11 (9 is D6Ha's yell).
        CHECK(EMOTE_HMB_JUSTICE == 10 && EMOTE_HMB_FIST == 11);
        CHECK(GnomerThermaplugg::kFirstPackageTextGroup == 9);
    }

    void TestLoads()
    {
        // Ruling 45: Electrocutioner 60%, the Alert System 45%, Crowd Pummeler 30%, highest first.
        std::vector<float> const t = Thresholds();
        CHECK(t.size() == 3 && t[0] == 60.f && t[1] == 45.f && t[2] == 30.f);
        CHECK(SchematicAt(60.f) == Schematic::Electrocutioner);
        CHECK(SchematicAt(45.f) == Schematic::AlertSystem);
        CHECK(SchematicAt(30.f) == Schematic::Pummeler);
        CHECK(!SchematicAt(90.f) && !SchematicAt(75.f) && !SchematicAt(50.f));
        // D6's latch hands them over highest first, each once, however far one hit takes him.
        GnomerThermaplugg::ThresholdLatch latch;
        latch.Arm(Thresholds());
        CHECK(latch.Crossed(61.f).empty());
        std::vector<float> const both = latch.Crossed(44.f);
        CHECK(both.size() == 2 && both[0] == 60.f && both[1] == 45.f);
        CHECK(latch.Crossed(44.f).empty());
        CHECK(latch.Crossed(1.f).size() == 1 && latch.Left() == 0);

        CHECK(LoadLine(Schematic::Electrocutioner) == "Loading schematic: ELECTROCUTIONER 6000");
        CHECK(LoadLine(Schematic::AlertSystem) == "Loading schematic: THE MOBILE ALERT SYSTEM");
        CHECK(LoadLine(Schematic::Pummeler) == "Loading schematic: CROWD PUMMELER 9-60");
        CHECK(SchematicOfKey("electro") == Schematic::Electrocutioner);
        CHECK(SchematicOfKey("alert") == Schematic::AlertSystem);
        CHECK(SchematicOfKey("pummeler") == Schematic::Pummeler);
        CHECK(!SchematicOfKey("techbot"));
    }

    void TestVoltage()
    {
        // MT21: +1 every 5 s by itself, never resets, no pause: the first Justice due at 30 s with no mistakes.
        GnomerElectro::VoltageClock clock(VoltageRules());
        CHECK(clock.Advance(29999) == 5 && !clock.JusticeDue());
        CHECK(clock.Advance(1) == 1 && clock.Stacks() == 6 && clock.JusticeDue());
        clock.StartJustice(Tune::kJusticeCastMs);
        CHECK(clock.Running() && !clock.Paused());
        // Mistakes keep counting during the bar (no pause on the hard mode) and the Voltage stays.
        CHECK(clock.Add(VoltsForHit(3)) == 3 && clock.Stacks() == 9);
        clock.LandJustice();
        CHECK(clock.Stacks() == 9 && clock.NextAt() == 12 && clock.Justices() == 1);
        CHECK(clock.Add(VoltsForHit(5)) == 5 && clock.JusticeDue());
        // 3% to all his damage a stack (the factor on D6's hits, his aura, the Spotted hit and the fist).
        CHECK(Near(GnomerElectro::DamageMultiplier(6, Tune::kVoltagePctPerStack), 1.18f));
        CHECK(Near(GnomerElectro::DamageMultiplier(0, Tune::kVoltagePctPerStack), 1.f));
        CHECK(Near(Scaled(Tune::kFistPct, 1.18f), 70.8f));
        CHECK(Near(Scaled(Tune::kSpottedPct, 0.f), 0.f) && Near(Scaled(50.f, -1.f), 0.f));
        CHECK(VoltsForHit(0) == 0 && VoltsForHit(5) == 5);
        // Mines and walking bombs always charge; the Sticky Bomb and The Big One by their switches.
        CHECK(SourceCharges(0) && SourceCharges(1));
        CHECK(SourceCharges(2) == Tune::kStickyCharges && SourceCharges(3) == Tune::kBigOneCharges);
        CHECK(!SourceCharges(4));
        // MT22: the safe hole and the bar as SP's row.
        CHECK(Tune::kJusticeSafeYd == 8.f && Tune::kJusticeCastMs == 4000 && Tune::kJusticePct == 75.f);
        CHECK(Tune::kJusticeEvery == 6 && Tune::kVoltageTickMs == 5000);
        // The donut reaches the whole room from the center and from the bowl's rim (the machine's outer edge).
        float const fromCenter = GnomerElectro::JusticeOuterYd(RoomArena(), kRoomCenter.XY(), Tune::kJusticeSafeYd);
        CHECK(fromCenter >= 52.f);
        for (Vec2 const& c : RoomCells())
            CHECK(DungeonKit::Distance(c, kRoomCenter.XY()) <= fromCenter);
    }

    void TestLights()
    {
        CHECK(Tune::kLightsCones == 2 && Tune::kLightsConeDeg == 30.f && Tune::kLightsDegPerSec == 12.f);
        CHECK(Tune::kSpottedPct == 50.f && !Tune::kSpottedWeakened && Tune::kSpottedOpensFace);
        // The opening lights nobody on his tank's line: light 0 starts 90 degrees off his facing, light 1 opposite.
        float const facing = 2.91f;
        float const start = LightsStartBearing(facing);
        CHECK(Near(start, std::fmod(facing + DungeonKit::kPi * 0.5f, DungeonKit::kTwoPi), 0.001f));
        CHECK(start >= 0.f && start < DungeonKit::kTwoPi);
        CHECK(LightsStartBearing(DungeonKit::kTwoPi - 0.1f) < DungeonKit::kPi);
        // "From the boss to the wall": from any cell of the room the cone reaches every other cell.
        std::vector<Vec2> const cells = RoomCells();
        float widest = 0.f;
        for (std::size_t i = 0; i < cells.size(); i += 37)
            for (std::size_t j = 0; j < cells.size(); j += 41)
                widest = std::max(widest, DungeonKit::Distance(cells[i], cells[j]));
        CHECK(widest > 90.f && widest <= Tune::kLightsRangeYd);
    }

    void TestFistFrameAndShapes()
    {
        std::vector<Vec2> const cells = RoomCells();
        CHECK(cells.size() > 7000);
        for (std::uint32_t face = 0; face < kFaceCount; ++face)
        {
            DungeonKit::ComboFrame const frame = FistFrame(face);
            // The frame stands on the face (ruling 68), facing the room's center, about 50 yd out.
            CHECK(Near(frame.origin.x, kFaceSpots[face].x) && Near(frame.origin.y, kFaceSpots[face].y));
            float const out = DungeonKit::Distance(frame.origin, kRoomCenter.XY());
            CHECK(out > 48.f && out < 51.f);
            CHECK(Near(frame.facing, DungeonKit::BearingTo(frame.origin, kRoomCenter.XY()), 0.001f));

            DungeonKit::PlacedShape const left = FistShape(face, Shape::LeftHalf);
            DungeonKit::PlacedShape const right = FistShape(face, Shape::RightHalf);
            DungeonKit::PlacedShape const nearShape = FistShape(face, Shape::Near);
            DungeonKit::PlacedShape const farShape = FistShape(face, Shape::Far);
            std::uint32_t nearCells = 0;
            std::uint32_t badHalves = 0;
            std::uint32_t badDistance = 0;
            std::uint32_t wrongNear = 0;
            for (Vec2 const& c : cells)
            {
                // Every cell of the room in exactly one half and in exactly one of near and far (no free spot).
                badHalves += (left.Contains(c) ? 1u : 0u) + (right.Contains(c) ? 1u : 0u) != 1u ? 1u : 0u;
                badDistance += (nearShape.Contains(c) ? 1u : 0u) + (farShape.Contains(c) ? 1u : 0u) != 1u ? 1u : 0u;
                if (nearShape.Contains(c))
                {
                    ++nearCells;
                    // Section 7 #33 A: near is within 50 yd of the face itself.
                    wrongNear += DungeonKit::Distance(c, frame.origin) > Tune::kFistNearYd + 0.01f ? 1u : 0u;
                }
            }
            CHECK(badHalves == 0);
            CHECK(badDistance == 0);
            CHECK(wrongNear == 0);
            // Section 7 #33 A: near holds 2,000 to 4,100 sq yd of floor by face (measured 2,700 to 2,950).
            CHECK(nearCells >= 2000 && nearCells <= 4100);

            // The halves split on the face-to-center line: the center's two sides are in different halves.
            Vec2 const toLeft = frame.Point(50.f, 10.f);
            Vec2 const toRight = frame.Point(50.f, -10.f);
            CHECK(left.Contains(toLeft) && !left.Contains(toRight) && right.Contains(toRight));

            // Each numeral stands on the bowl's floor, inside its own shape and out of the other of its pair.
            Arena const room = RoomArena();
            for (Shape const s : kFistShapes)
            {
                Vec2 const label = FistLabel(face, s);
                CHECK(room.Contains(label, kFloorZ));
                CHECK(DungeonKit::Distance(label, kRoomCenter.XY()) < kRoomBowlRadius);
                CHECK(FistShape(face, s).Contains(label));
            }
            CHECK(!right.Contains(FistLabel(face, Shape::LeftHalf)));
            CHECK(!left.Contains(FistLabel(face, Shape::RightHalf)));
            CHECK(!farShape.Contains(FistLabel(face, Shape::Near)));
            CHECK(!nearShape.Contains(FistLabel(face, Shape::Far)));

            // The fist's body: behind the face's plane, facing the center.
            Point3 const body = FistSpot(face);
            CHECK(Near(DungeonKit::Distance(body.XY(), kRoomCenter.XY()), out + Tune::kFistBodyBehindYd, 0.05f));
            CHECK(Near(body.o, frame.facing, 0.001f));
        }
    }

    void TestFistTimingAndRoll()
    {
        // Ruling 69: the first punch 4 s after the call, then 2.5 s apart; all three drawn at once.
        CHECK(FistStrikeMs(0) == 4000 && FistStrikeMs(1) == 6500 && FistStrikeMs(2) == 9000);
        DungeonKit::ComboTiming const t = FistTiming();
        CHECK(t.mode == DungeonKit::ComboCallMode::AllAtOnce);
        std::vector<DungeonKit::PunchTimes> const times = DungeonKit::ComboTimeline(t, 3);
        for (DungeonKit::PunchTimes const& p : times)
        {
            CHECK(p.callFrom == 0);
            CHECK(p.strikeAt - p.liveFrom == Tune::kFistLiveMs);
        }
        // D5's pin (the contract's 0 / 4000 / 0 / 2500) gives the same strikes: the live fill sits inside the 4 s.
        std::vector<DungeonKit::PunchTimes> const d5 =
            DungeonKit::ComboTimeline(GnomerPummeler::KitTiming(0, 4000, 0, 2500, true), 3);
        for (std::size_t i = 0; i < 3; ++i)
            CHECK(d5[i].strikeAt == times[i].strikeAt);
        CHECK(Tune::kFistEveryMs == 18000 && Tune::kFistPct == 60.f && Tune::kFistWeakened);

        // The roll: three distinct shapes of the four, never the lane; every order comes up; faces 0 to 5.
        Lcg rand;
        std::set<std::vector<Shape>> seen;
        std::set<std::uint32_t> faces;
        for (int i = 0; i < 4000; ++i)
        {
            std::vector<Shape> const chain = RollFistChain(rand);
            CHECK(chain.size() == Tune::kFistPunches);
            std::set<Shape> const distinct(chain.begin(), chain.end());
            CHECK(distinct.size() == chain.size());
            CHECK(!distinct.count(Shape::Lane));
            seen.insert(chain);
            faces.insert(RollFace(rand));
        }
        CHECK(seen.size() == 24);       // 4 x 3 x 2 orders
        CHECK(faces.size() == kFaceCount && *faces.rbegin() == kFaceCount - 1);
    }

    // Every chain from every face can be dodged by a player who starts at the room's center (melee, the tank) and
    // runs at 7 yd/s: a cell clear of punch 1 within 4 s of running, then clear of punch 2 within 2.5 s of that cell,
    // then clear of punch 3 (a grid search over 2 yd cells; the paths through the arms' mouths are not checked).
    void TestEveryChainHasAWayOut()
    {
        std::vector<Vec2> cells;
        for (Vec2 const& c : RoomCells())
            if (std::fmod(std::fabs(c.x), 2.f) < 0.5f && std::fmod(std::fabs(c.y), 2.f) < 0.5f)
                cells.push_back(c);
        std::vector<std::vector<Shape>> chains;
        for (Shape const a : kFistShapes)
            for (Shape const b : kFistShapes)
                for (Shape const c : kFistShapes)
                    if (a != b && b != c && a != c)
                        chains.push_back({ a, b, c });
        CHECK(chains.size() == 24);
        std::uint32_t stuck = 0;
        for (std::uint32_t face = 0; face < kFaceCount; ++face)
            for (std::vector<Shape> const& chain : chains)
            {
                std::vector<Vec2> from{ kRoomCenter.XY() };
                std::uint32_t last = 0;
                for (std::size_t i = 0; i < chain.size() && !from.empty(); ++i)
                {
                    std::uint32_t const at = FistStrikeMs(i);
                    float const reach = kRunYdPerSec * float(at - last) / 1000.f;
                    last = at;
                    DungeonKit::PlacedShape const punch = FistShape(face, chain[i]);
                    std::vector<Vec2> next;
                    for (Vec2 const& c : cells)
                    {
                        if (punch.Contains(c))
                            continue;
                        for (Vec2 const& f : from)
                            if (DungeonKit::Distance(c, f) <= reach)
                            {
                                next.push_back(c);
                                break;
                            }
                    }
                    from.swap(next);
                }
                stuck += from.empty() ? 1u : 0u;
            }
        CHECK(stuck == 0);
    }
}

int main()
{
    TestSliceTagsTexts();
    TestLoads();
    TestVoltage();
    TestLights();
    TestFistFrameAndShapes();
    TestFistTimingAndRoll();
    TestEveryChainHasAWayOut();
    // S0's pin: bomb start 01 (the alcove mouth of face 01) is on the hard mode's arena.
    CHECK(ArenaFor(BOSS_WHOLE_WORKSHOP).Contains(kBombStarts[0].XY(), kBombStarts[0].z));

    return Report("gnomer_hard_mode_machines_test");
}
