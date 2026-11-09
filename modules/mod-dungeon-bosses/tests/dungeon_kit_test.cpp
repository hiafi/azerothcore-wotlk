// Host tests for the shared dungeon kit's pure part (WP-K0): DungeonKitMath.h, DungeonKitState.h, DungeonKitArena.h,
// DungeonKitLogic.h and DungeonKitIds.h, plus the parity of the Deadmines aliases (DeadminesKit, Greenskin) with the
// generic pieces they now name. Stratholme WP-KT-1: DungeonKitFloor.h (FloorPath and its parity with Gilnid's, floor
// spots, puddles, the inside clock) and DungeonKitFlow.h (weighted split, wave cap, cast queue, holds, percents).
#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include "DungeonKitArena.h"
#include "DungeonKitFloor.h"
#include "DungeonKitFlow.h"
#include "DungeonKitIds.h"
#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include "DungeonKitState.h"
#include "GilnidLogic.h"
#include "GreenskinLogic.h"
#include "check.h"
#include <cmath>
#include <span>
#include <string>
#include <type_traits>
#include <vector>

using namespace DungeonKit;

namespace
{
    bool Near(float a, float b, float tolerance)
    {
        return std::fabs(a - b) <= tolerance;
    }

    float Deg(float degrees)
    {
        return degrees * kPi / 180.f;
    }

    // A deterministic stand-in for urand: always the same index.
    struct FixedRand
    {
        std::uint32_t value = 0;
        std::uint32_t operator()(std::uint32_t n) const { return n ? value % n : 0; }
    };

    void TestAliases()
    {
        // The Deadmines names are the generic entities (WP-K0 moved them; nothing was copied).
        static_assert(std::is_same_v<DeadminesKit::Vec2, DungeonKit::Vec2>, "one Vec2");
        static_assert(std::is_same_v<DeadminesKit::Box2, DungeonKit::Box2>, "one Box2");
        static_assert(std::is_same_v<DeadminesKit::NH<float>, DungeonKit::NH<float>>, "one NH");
        static_assert(std::is_same_v<DeadminesRework::Vec2, DungeonKit::Vec2>, "DeadminesRework's Vec2");
        static_assert(std::is_same_v<Greenskin::FrameRect, DungeonKit::FrameRect>, "one FrameRect");
        static_assert(std::is_same_v<Greenskin::LaneAxis, DungeonKit::LaneAxis>, "one LaneAxis");
        static_assert(std::is_base_of_v<DungeonKit::GripTracker, Greenskin::GripTracker>, "Greenskin's tracker");
        CHECK(&DeadminesKit::Distance == &DungeonKit::Distance);
        CHECK(&DeadminesKit::RefFlatValue == &DungeonKit::RefFlatValue);
        CHECK(&DeadminesKit::SanitizeLoadedState == &DungeonKit::SanitizeLoadedState);
        CHECK(DeadminesKit::State::Done == State::Done);
        CHECK(DeadminesKit::JohnsonRoll::Present == Roll::Present && DeadminesKit::JohnsonRoll::Absent == Roll::Absent);
        CHECK(std::uint32_t(DeadminesRework::SPELL_DM_CAST_BAR) == std::uint32_t(SPELL_KIT_CAST_BAR));
        CHECK(std::uint32_t(DeadminesRework::SPELL_DM_STANDING_IN_IT) == std::uint32_t(SPELL_KIT_STANDING_IN_IT));
        CHECK(SPELL_KIT_CAST_BAR == 205200u && SPELL_KIT_STANDING_IN_IT == 205201u);
    }

    void TestGeometry()
    {
        std::array<Vec2, 4> constexpr square{ { { 0.f, 0.f }, { 10.f, 0.f }, { 10.f, 10.f }, { 0.f, 10.f } } };
        std::vector<Vec2> const squareVec(square.begin(), square.end());
        // the array and the runtime forms give the same answers
        for (float x = -2.f; x <= 12.f; x += 0.5f)
            for (float y = -2.f; y <= 12.f; y += 0.5f)
                CHECK(PointInPolygon(square, { x, y }) == PointInPolygon(squareVec, { x, y }));
        for (float deg = 0.f; deg < 360.f; deg += 7.5f)
        {
            auto const a = RayToPolygonEdge(square, { 3.f, 4.f }, Deg(deg));
            auto const b = RayToPolygonEdge(std::span<Vec2 const>(squareVec), { 3.f, 4.f }, Deg(deg));
            CHECK(a.has_value() == b.has_value() && (!a || *a == *b));
        }
        auto const end = LaneEndAtWall(squareVec, { 5.f, 5.f }, { 7.f, 5.f }, 0.5f);
        CHECK(end && Near(end->x, 9.5f, 1e-3f) && Near(end->y, 5.f, 1e-3f));
        CHECK(!PointInPolygon(std::vector<Vec2>{ { 0.f, 0.f }, { 1.f, 1.f } }, { 0.5f, 0.5f }));   // not a polygon
        // circle rays: from the center the rim is the radius; from inside, the far rim
        auto const r0 = RayToCircleEdge({ 0.f, 0.f }, 10.f, { 0.f, 0.f }, Deg(33.f));
        CHECK(r0 && Near(*r0, 10.f, 1e-4f));
        auto const r1 = RayToCircleEdge({ 0.f, 0.f }, 10.f, { 5.f, 0.f }, 0.f);
        CHECK(r1 && Near(*r1, 5.f, 1e-4f));
        auto const r2 = RayToCircleEdge({ 0.f, 0.f }, 10.f, { 5.f, 0.f }, kPi);
        CHECK(r2 && Near(*r2, 15.f, 1e-4f));
        CHECK(!RayToCircleEdge({ 0.f, 0.f }, 10.f, { 20.f, 0.f }, 0.f));     // outside
        // segment distance (Greenskin's DistanceToSegment forwards to it)
        float along = 0.f;
        CHECK(Near(SegmentDistance({ 0.f, 0.f }, { 10.f, 0.f }, { 4.f, 3.f }, &along), 3.f, 1e-5f));
        CHECK(Near(along, 4.f, 1e-5f));
        CHECK(Near(SegmentDistance({ 0.f, 0.f }, { 10.f, 0.f }, { 13.f, 4.f }), 5.f, 1e-5f));
        CHECK(Near(Greenskin::DistanceToSegment({ 0.f, 0.f }, { 10.f, 0.f }, { -3.f, 4.f }), 5.f, 1e-5f));
        // frontal cone
        CHECK(InFrontalCone({ 0.f, 0.f }, 0.f, { 5.f, 1.f }, 60.f, 10.f));
        CHECK(!InFrontalCone({ 0.f, 0.f }, 0.f, { -5.f, 0.f }, 60.f, 10.f));
        // box clamp
        Box2 constexpr box{ -1.f, 1.f, -2.f, 2.f };
        Vec2 const c = box.Clamp({ 5.f, -5.f });
        CHECK(c.x == 1.f && c.y == -2.f);
    }

    void TestFrames()
    {
        FrameRect constexpr f{ { 10.f, 20.f }, kPi / 2.f, 30.f, 8.f };      // X runs +y, Y runs -x
        Vec2 const p = FramePoint(f, 3.f, 2.f);
        CHECK(Near(p.x, 8.f, 1e-4f) && Near(p.y, 23.f, 1e-4f));
        Vec2 const back = ToFrame(f, p);
        CHECK(Near(back.x, 3.f, 1e-4f) && Near(back.y, 2.f, 1e-4f));
        CHECK(InsideFrame(f, p));
        CHECK(!InsideFrame(f, FramePoint(f, 31.f, 2.f)));
        CHECK(LanesFit(SpanFor(f, LaneAxis::Along), 1, 4.f, 6.f));
        CHECK(!LanesFit(SpanFor(f, LaneAxis::Along), 2, 4.f, 6.f));
        LaneSegment const lane = LaneOnFrame(f, LaneAxis::Across, 10.f, 4.f);
        CHECK(Near(Distance(lane.from, lane.to), f.sizeY, 1e-4f));
    }

    void TestSaveStrings()
    {
        // raw layer: the stock shape "D E 3 3"
        CHECK(FormatSave("DE", { 3, 3 }) == "D E 3 3");
        CHECK(FormatSave("SR", {}) == "S R ");
        std::vector<std::uint32_t> fields;
        CHECK(ReadSaveFields("D E 3 3 1", "DE", 2, 12, fields) && fields.size() == 3u && fields[2] == 1u);
        CHECK(ReadSaveFields("DE 3 3", "DE", 2, 12, fields));          // `>> char` reads "DE" as two characters
        CHECK(!ReadSaveFields("D M 3 3", "DE", 2, 12, fields));
        CHECK(!ReadSaveFields("D E 3", "DE", 2, 12, fields));
        CHECK(ReadSaveFields("D E 1 2 3 4 5", "DE", 2, 3, fields) && fields.size() == 3u);  // stops at maxFields
        CHECK(ReadSaveFields("D E 1 2 x 4", "DE", 2, 9, fields) && fields.size() == 2u);    // stops at a bad field

        // states + extras
        std::string const text = FormatStates("SR", { 3, 1, 5, 2, 0 }, { 7, 0, 2 });
        CHECK(text == "S R 3 1 0 2 0 7 0 2");                           // TO_BE_DECIDED written as NOT_STARTED
        StateSave s;
        CHECK(ParseStates(text, "SR", 5, 3, s));
        CHECK(s.states == (std::vector<std::uint32_t>{ 3, 0, 0, 0, 0 }));   // IN_PROGRESS and FAIL sanitized
        CHECK(s.extras == (std::vector<std::uint32_t>{ 7, 0, 2 }));
        // a short tail (an older build) keeps the defaults
        CHECK(ParseStates("S R 3 3", "SR", 5, 3, s));
        CHECK(s.states == (std::vector<std::uint32_t>{ 3, 3, 0, 0, 0 }));
        CHECK(s.extras == (std::vector<std::uint32_t>{ 0, 0, 0 }));
        CHECK(!ParseStates("S R", "SR", 5, 3, s));
        CHECK(!ParseStates("", "SR", 5, 3, s));
        // a foreign header: ignored, or read by the legacy reader (Scholomance's stock "<kirtonos> <miniBosses>")
        CHECK(!ParseStates("S K 3 3 3", "SR", 5, 3, s));
        LegacySaveReader const legacy = [](std::string const& in, StateSave& out)
        {
            std::vector<std::uint32_t> stock;
            if (!ReadSaveFields(in, "SK", 3, 3, stock))
                return false;
            out.states[0] = stock[0];
            out.states[1] = stock[1];
            out.extras[0] = stock[2];
            return true;
        };
        CHECK(ParseStates("S K 3 1 9", "SR", 5, 3, s, legacy));
        CHECK(s.states[0] == State::Done && s.states[1] == State::NotStarted && s.extras[0] == 9u);
        CHECK(!ParseStates("Q Q 1", "SR", 5, 3, s, legacy));
        // our own header with no fields does not go to the legacy reader
        CHECK(!ParseStates("S R", "SR", 5, 3, s, legacy));
    }

    void TestRolls()
    {
        CHECK(ResolveRoll(0, 15) == Roll::Present);
        CHECK(ResolveRoll(14, 15) == Roll::Present);
        CHECK(ResolveRoll(15, 15) == Roll::Absent);
        CHECK(ResolveRoll(99, 100) == Roll::Present);
        CHECK(ResolveRoll(0, 0) == Roll::Absent);
        int present = 0;
        for (std::uint32_t roll = 0; roll < 100; ++roll)
            if (ResolveRoll(roll, 15) == Roll::Present)
                ++present;
        CHECK(present == 15);
        CHECK(SanitizeLoadedRoll(2) == Roll::Absent && SanitizeLoadedRoll(3) == Roll::Unrolled);
        // Johnson's roll is the generic one at 40%
        for (std::uint32_t roll = 0; roll < 100; ++roll)
            CHECK(DeadminesKit::ResolveJohnsonRoll(roll) == ResolveRoll(roll, 40));
    }

    void TestArena()
    {
        Arena const room(
            ArenaRegion::Polygon({ { 0.f, 0.f }, { 20.f, 0.f }, { 20.f, 10.f }, { 0.f, 10.f } }, 0.f, 5.f));
        CHECK(room.Contains({ 5.f, 5.f }, 1.f));
        CHECK(!room.Contains({ 5.f, 5.f }, 6.f));       // above the band
        CHECK(!room.Contains({ 25.f, 5.f }, 1.f));
        CHECK(!Arena().Contains({ 0.f, 0.f }, 0.f));    // empty
        // a walkway on a second level (union of floors)
        Arena twoLevels = room;
        twoLevels.Add(ArenaRegion::Circle({ 30.f, 5.f }, 4.f, 10.f, 14.f));
        CHECK(twoLevels.Contains({ 31.f, 6.f }, 12.f));
        CHECK(!twoLevels.Contains({ 31.f, 6.f }, 2.f));
        CHECK(twoLevels.RegionAt({ 31.f, 6.f }, 12.f) == &twoLevels.regions[1]);
        CHECK(twoLevels.ZMin() == 0.f && twoLevels.ZMax() == 14.f);
        // rays to the edge of the region holding the origin
        auto const wall = room.RayToEdge({ 5.f, 5.f }, 1.f, 0.f);
        CHECK(wall && Near(*wall, 15.f, 1e-3f));
        auto const rim = twoLevels.RayToEdge({ 30.f, 5.f }, 12.f, kPi / 2.f);
        CHECK(rim && Near(*rim, 4.f, 1e-3f));
        CHECK(!room.RayToEdge({ 50.f, 5.f }, 1.f, 0.f));
        // a frame box arena
        FrameRect constexpr f{ { 0.f, 0.f }, kPi, 20.f, 10.f };
        Arena const deck(ArenaRegion::Frame(f, Box2{ -2.f, 22.f, -1.f, 11.f }, 0.f, 10.f));
        CHECK(deck.Contains(FramePoint(f, 21.f, 10.5f), 5.f));
        CHECK(!deck.Contains(FramePoint(f, 23.f, 5.f), 5.f));
        auto const deckWall = deck.RayToEdge(FramePoint(f, 0.f, 5.f), 5.f, kPi);    // toward +X of the frame
        CHECK(deckWall && Near(*deckWall, 22.f, 1e-3f));
    }

    // Greenskin's ship test and the kit arena that ArenaGuard runs on agree everywhere (the effect is unchanged).
    void TestShipArenaParity()
    {
        Arena const ship = Greenskin::ShipArena();
        int on = 0;
        for (float x = -125.f; x <= -25.f; x += 0.75f)
            for (float y = -860.f; y <= -780.f; y += 0.75f)
                for (float z : { 0.1f, 35.9f, 36.f, 41.f, 48.f, 48.1f, 55.f })
                {
                    bool const a = Greenskin::OnShip({ x, y }, z);
                    CHECK(a == ship.Contains({ x, y }, z));
                    on += a ? 1 : 0;
                }
        CHECK(on > 1000);
        CHECK(ship.Contains(DeadminesRework::kGreenskinSpawn, 41.6f));
    }

    void TestGripTracker()
    {
        GripTracker t(1000, 2000);
        CHECK(t.GraceMs() == 1000u && t.CooldownMs() == 2000u);
        CHECK(!t.Update(1, false, 500));
        CHECK(t.Update(1, false, 500));                 // off 1 s: grip
        t.Gripped(1);
        CHECK(!t.Update(1, false, 1000));               // cooling down
        CHECK(!t.Update(1, false, 999));
        CHECK(t.Update(1, false, 1));                   // cooldown over, off long enough
        CHECK(!t.Update(2, true, 5000));
        CHECK(t.PullNow(3, false) && !t.PullNow(3, true));
        t.Gripped(3);
        CHECK(!t.PullNow(3, false));
        t.Forget(3);
        CHECK(t.PullNow(3, false));
        // Greenskin's tracker keeps his 1.5 s / 3 s
        Greenskin::GripTracker g;
        CHECK(g.GraceMs() == Greenskin::kGripGraceMs && g.CooldownMs() == Greenskin::kGripCooldownMs);
    }

    void TestLanding()
    {
        Vec2 const l = LandingToward({ 0.f, 0.f }, { 10.f, 0.f }, 8.f);
        CHECK(Near(l.x, 8.f, 1e-4f) && Near(l.y, 0.f, 1e-4f));
        CHECK(LandingToward({ 1.f, 1.f }, { 1.f, 1.f }, 8.f).x == 1.f);    // on top of each other: the boss
        Vec2 const clamped = LandingToward({ 0.f, 0.f }, { 0.f, 50.f }, 8.f, Box2{ -2.f, 2.f, -3.f, 3.f });
        CHECK(clamped.y == 3.f);
        // Greenskin's landing is this one with his numbers
        for (float y = -860.f; y <= -780.f; y += 5.f)
        {
            Vec2 const g = Greenskin::GripLanding({ -60.f, -820.f }, { -40.f, y });
            Vec2 const k = LandingToward({ -60.f, -820.f }, { -40.f, y }, Greenskin::kGripLandYd,
                Greenskin::kGripLandBox);
            CHECK(g.x == k.x && g.y == k.y);
        }
    }

    void TestSplitDamage()
    {
        std::vector<std::uint32_t> s = SplitDamage(1000, 3, 0);
        CHECK(s.size() == 3u && s[0] == 334u && s[1] == 333u && s[2] == 333u);
        CHECK(s[0] + s[1] + s[2] == 1000u);
        s = SplitDamage(1000, 2, 400);
        CHECK(s == (std::vector<std::uint32_t>{ 400, 400 }));          // capped
        CHECK(SplitDamage(1000, 0, 0).empty());
        s = SplitDamage(5, 10, 0);
        std::uint32_t sum = 0;
        for (std::uint32_t v : s)
            sum += v;
        CHECK(sum == 5u && s[0] == 1u && s[9] == 0u);
    }

    void TestPicks()
    {
        std::vector<PickCandidate> const c = {
            { 1, 3.f, true, true },     // the tank, in melee
            { 2, 5.f, false, true },
            { 3, 12.f, false, false },  // no line of sight
            { 4, 25.f, false, true },
            { 5, 45.f, false, true },   // out of range
        };
        PickRule rule;
        rule.maxRange = 40.f;
        // every random pick is a non-tank in range
        for (std::uint32_t r = 0; r < 20; ++r)
        {
            auto const pick = PickFrom(c, rule, FixedRand{ r });
            CHECK(pick && c[*pick].id != 1 && c[*pick].id != 5);
        }
        rule.minRange = 8.f;
        rule.requireLos = true;
        auto const onlyFour = PickFrom(c, rule, FixedRand{ 0 });
        CHECK(onlyFour && c[*onlyFour].id == 4);
        rule.exclude = { 4 };
        CHECK(!PickFrom(c, rule, FixedRand{ 0 }));
        // farthest
        PickRule far;
        far.farthest = true;
        auto const farthest = PickFrom(c, far, FixedRand{ 0 });
        CHECK(farthest && c[*farthest].id == 5);    // the default range is 100 yd
        far.maxRange = 40.f;
        auto const farthestInRange = PickFrom(c, far, FixedRand{ 0 });
        CHECK(farthestInRange && c[*farthestInRange].id == 4);
        // a tank alone
        std::vector<PickCandidate> const solo = { { 9, 2.f, true, true } };
        CHECK(!PickFrom(solo, PickRule{}, FixedRand{ 0 }));
        PickRule soloRule;
        soloRule.tankIfAlone = true;
        auto const tank = PickFrom(solo, soloRule, FixedRand{ 0 });
        CHECK(tank && *tank == 0u);
        // distinct picks never repeat and stop when the pool is dry
        std::vector<std::size_t> const two = PickDistinctFrom(c, PickRule{}, 10, FixedRand{ 1 });
        CHECK(two.size() == 4u);    // 2, 3, 4, 5: every non-tank within 100 yd
        for (std::size_t i = 0; i < two.size(); ++i)
            for (std::size_t j = i + 1; j < two.size(); ++j)
                CHECK(two[i] != two[j]);
    }

    void TestSpeedStacksLethal()
    {
        CHECK(Near(SpeedFor(80.f), 0.8f, 1e-6f));
        CHECK(Near(SpeedFor(95.f), 0.95f, 1e-6f));
        CHECK(SpeedFor(-5.f) == 0.f);
        static_assert(SpeedFor(100.f) == 1.f, "a player's speed is rate 1");
        CHECK(ClampStacks(3, 2, 10) == 5u);
        CHECK(ClampStacks(9, 5, 10) == 10u);
        CHECK(ClampStacks(2, -5, 10) == 0u);
        CHECK(ClampStacks(2, 300, 0) == 302u);          // no cap
        CHECK(ClampLethal(1000, 999) == 999u);
        CHECK(ClampLethal(1000, 1000) == 999u);
        CHECK(ClampLethal(1000, 5000) == 999u);
        CHECK(ClampLethal(1, 50) == 0u);
    }

    void TestLineStrike()
    {
        // straight: 10 yd to the target plus 5 past it
        LinePath p = LineStrikePath({ 0.f, 0.f }, { 10.f, 0.f }, 5.f);
        CHECK(Near(p.length, 15.f, 1e-4f) && Near(p.end.x, 15.f, 1e-4f) && !p.clipped);
        // clipped by a room wall at x 12 (0.5 yd inset)
        Arena const room(
            ArenaRegion::Polygon({ { -5.f, -5.f }, { 12.f, -5.f }, { 12.f, 5.f }, { -5.f, 5.f } }, -1.f, 1.f));
        p = LineStrikePath({ 0.f, 0.f }, { 10.f, 0.f }, 5.f, 0.f, &room, 0.f, 0.5f);
        CHECK(p.clipped && Near(p.length, 11.5f, 1e-3f) && Near(p.end.x, 11.5f, 1e-3f));
        CHECK(room.Contains(p.end, 0.f));
        // a chained link starts at the last end
        LinePath const next = LineStrikePath(p.end, { 0.f, 4.f }, 5.f, 0.f, &room, 0.f, 0.5f);
        CHECK(room.Contains(next.end, 0.f));
        // the source outside the arena: no clip
        p = LineStrikePath({ 50.f, 0.f }, { 60.f, 0.f }, 5.f, 0.f, &room, 0.f);
        CHECK(!p.clipped && Near(p.length, 15.f, 1e-4f));
        // a target on the source keeps the fallback facing
        p = LineStrikePath({ 0.f, 0.f }, { 0.f, 0.f }, 6.f, kPi / 2.f);
        CHECK(Near(p.facing, kPi / 2.f, 1e-5f) && Near(p.end.y, 6.f, 1e-4f));
        // a circle arena
        Arena const ring(ArenaRegion::Circle({ 0.f, 0.f }, 10.f, -1.f, 1.f));
        p = LineStrikePath({ 0.f, 0.f }, { 8.f, 0.f }, 5.f, 0.f, &ring, 0.f, 0.5f);
        CHECK(p.clipped && Near(p.length, 9.5f, 1e-3f));
    }

    void TestDwell()
    {
        DwellTracker touch(0);
        CHECK(touch.Update({}, 250) == 0u);
        CHECK(touch.Update({ 7, 8 }, 250) == 7u);       // on touch: the first inside
        DwellTracker bell(1000);
        CHECK(bell.Update({ 1 }, 250) == 0u);
        CHECK(bell.Update({ 1, 2 }, 250) == 0u);
        CHECK(bell.Update({ 1, 2 }, 250) == 0u);
        CHECK(bell.Update({ 1, 2 }, 250) == 1u);        // 1 s without a break
        DwellTracker broken(1000);
        CHECK(broken.Update({ 1 }, 500) == 0u);
        CHECK(broken.Update({}, 250) == 0u);            // stepped out: starts again
        CHECK(broken.Update({ 1 }, 500) == 0u);
        CHECK(broken.Update({ 1 }, 500) == 1u);
    }
    // ---- R-K0 review fixes ----------------------------------------------------------------------------------------

    // S1: a guard that fired re-arms on Reset (a wipe after the phase change no longer leaves the boss at 1 health).
    void TestLethalLatch()
    {
        LethalLatch l;
        CHECK(l.Armed() && !l.Fired());
        LethalLatch::Result r = l.Apply(100, 50);
        CHECK(!r.clamped && !r.fire && r.damage == 50u);
        r = l.Apply(100, 150);
        CHECK(r.clamped && r.fire && r.damage == 99u && l.Fired());
        r = l.Apply(99, 500);                           // still armed: clamped, but fires once only
        CHECK(r.clamped && !r.fire && r.damage == 98u);
        l.Reset();                                      // the boss's Reset: the next pull fires again
        CHECK(l.Armed() && !l.Fired());
        r = l.Apply(1000, 1000);
        CHECK(r.clamped && r.fire && r.damage == 999u);
        l.Disarm();
        r = l.Apply(999, 5000);
        CHECK(!r.clamped && !r.fire && r.damage == 5000u);
        l.Arm();
        CHECK(l.Apply(10, 10).fire);
    }

    // S2: the boss's own leash. Grace 0 and on the ground: Greenskin's leash (the first check off the arena).
    void TestLeashTimer()
    {
        LeashTimer t;
        CHECK(!t.Update(true, false, 250, 0));
        CHECK(t.Update(false, false, 250, 0));          // Greenskin: at once
        t.Reset();
        CHECK(!t.Update(false, true, 250, 0));          // his own leap: no leash mid-air
        CHECK(!t.Update(false, true, 5000, 0));
        CHECK(t.OffMs() == 0u);
        CHECK(t.Update(false, false, 250, 0));          // landed off it: leash
        LeashTimer g;
        CHECK(!g.Update(false, false, 250, 1000));
        CHECK(!g.Update(false, true, 250, 1000));       // airborne: not counted
        CHECK(!g.Update(false, false, 250, 1000));
        CHECK(!g.Update(false, false, 250, 1000));
        CHECK(g.Update(false, false, 250, 1000));       // 1 s off on the ground
        CHECK(!g.Update(true, false, 250, 1000) && g.OffMs() == 0u);
    }

    // S3: a long grip is not gripped again mid-air; Greenskin's 3 s still covers his grips up to 62.5 yd.
    void TestGripCooldown()
    {
        CHECK(GripCooldownMs(3000, 50.f, 25.f) == 3000u);
        CHECK(GripCooldownMs(3000, 62.5f, 25.f) == 3000u);
        CHECK(GripCooldownMs(3000, 75.f, 25.f) == 3500u);
        CHECK(GripCooldownMs(3000, 112.f, 25.f) == 4980u);
        CHECK(GripCooldownMs(3000, 100.f, 0.f) == 3000u);
        CHECK(GripCooldownMs(0, 20.f, 20.f, 0) == 1000u);
        // the review's scenario: a 100 yd grip at 25 yd/s (4 s in the air), still off the arena while it flies
        GripTracker t(1500, 3000);
        t.Gripped(9, GripCooldownMs(t.CooldownMs(), 100.f, 25.f));
        std::uint32_t ms = 0;
        bool regripped = false;
        while (ms < 4250)
        {
            ms += 250;
            if (t.Update(9, false, 250))
            {
                regripped = true;
                break;
            }
        }
        CHECK(!regripped && ms == 4250u);               // not before it lands (4 s) plus the margin
        CHECK(t.Update(9, false, 250));                 // 4.5 s, still off the arena: gripped again
        // the plain Gripped keeps the tracker's cooldown (Greenskin's tests)
        t.Gripped(10);
        CHECK(!t.Update(10, false, 2999));
        CHECK(t.Update(10, false, 1));
    }

    // S4: a default landing the arena does not hold falls back to the boss's spot.
    void TestLandingOrBoss()
    {
        Arena const ring(ArenaRegion::Circle({ 0.f, 0.f }, 10.f, 0.f, 5.f));
        auto [inDest, inZ] = LandingOrBoss(ring, { 3.f, 0.f }, 1.f, { 0.f, 0.f }, 2.f);
        CHECK(inDest.x == 3.f && inZ == 1.f);
        auto [outDest, outZ] = LandingOrBoss(ring, { 30.f, 0.f }, 1.f, { 1.f, 2.f }, 2.f);
        CHECK(outDest.x == 1.f && outDest.y == 2.f && outZ == 2.f);
        auto [lowDest, lowZ] = LandingOrBoss(ring, { 3.f, 0.f }, -20.f, { 1.f, 2.f }, 2.f);   // under a ledge
        CHECK(lowDest.x == 1.f && lowZ == 2.f);
        // a two-floor arena: the upper floor's point is kept, a gap between the floors is not
        Arena floors(ArenaRegion::Circle({ 0.f, 0.f }, 10.f, 0.f, 5.f));
        floors.Add(ArenaRegion::Circle({ 30.f, 0.f }, 10.f, 15.f, 20.f));
        CHECK(LandingOrBoss(floors, { 30.f, 0.f }, 16.f, { 0.f, 0.f }, 1.f).second == 16.f);
        CHECK(LandingOrBoss(floors, { 15.f, 0.f }, 1.f, { 0.f, 0.f }, 1.f).first.x == 0.f);
        // Greenskin: his land box lies on the ship, so the fallback never moves his grips (his z search stays in the
        // deck band or falls back to his own z)
        Arena const ship = Greenskin::ShipArena();
        Box2 const box = Greenskin::kGripLandBox;
        for (float x = box.minX; x <= box.maxX; x += 0.5f)
            for (float y = box.minY; y <= box.maxY; y += 0.5f)
                CHECK(ship.Contains({ x, y }, 41.f));
    }

    // N1, N3, S6: stack caps, the pickup reach, the stand-in's quiet timer.
    void TestStackCapReachQuiet()
    {
        CHECK(StackCap(0, 5) == 5u);                   // max 0: the spell's own StackAmount
        CHECK(StackCap(3, 5) == 3u);
        CHECK(StackCap(0, 0) == 0u);                   // no cap anywhere
        CHECK(ClampStacks(4, 3, StackCap(0, 5)) == 5u);
        CHECK(ClampStacks(4, 3, StackCap(0, 0)) == 7u);

        CHECK(InPickupRange(1.9f, 5.9f, 2.f, 6.f));
        CHECK(InPickupRange(2.f, -6.f, 2.f, 6.f));
        CHECK(!InPickupRange(2.1f, 0.f, 2.f, 6.f));
        CHECK(!InPickupRange(1.f, -6.1f, 2.f, 6.f));
        CHECK(InPickupRange(1.f, 9.f, 2.f, 10.f));     // a taller band (stairs, a ramp)

        QuietTimer q(10000);
        CHECK(!q.Update(false, 60000));                 // out of combat: never
        CHECK(!q.Update(true, 9000));
        q.Hit();
        CHECK(!q.Update(true, 9000));
        CHECK(q.Update(true, 1000));                    // 10 s in combat without a hit: evade
        q.Reset();
        CHECK(!q.Update(true, 9999));
    }

    // N5: a legacy reader that resizes the arrays cannot change their counts.
    void TestLegacyReaderResize()
    {
        LegacySaveReader const greedy = [](std::string const&, StateSave& out)
        {
            out.states.assign(2, State::Done);
            out.extras.assign(9, 4);
            return true;
        };
        StateSave s;
        CHECK(ParseStates("Q Q 1", "SR", 5, 3, s, greedy));
        CHECK(s.states.size() == 5u && s.extras.size() == 3u);
        CHECK(s.states[0] == State::Done && s.states[4] == State::NotStarted && s.extras[2] == 4u);
    }

    // N8: trackers forget units that left.
    void TestTrackerForget()
    {
        GripTracker t;
        t.Update(1, false, 250);
        t.Update(2, false, 250);
        t.Gripped(3);
        CHECK(t.Size() == 3u);
        CHECK(t.ForgetIf([](std::uint64_t unit) { return unit != 2; }) == 2u);
        CHECK(t.Size() == 1u);
        CHECK(t.PullNow(3, false));                     // forgotten: no cooldown left
    }

    bool NearV(Vec2 a, Vec2 b, float tolerance = 0.01f)
    {
        return Near(a.x, b.x, tolerance) && Near(a.y, b.y, tolerance);
    }

    // A mover sampled every kMotionSampleEveryMs for `samples` samples from `start` at `speed` yd/s along `heading`.
    MotionTrack Walk(Vec2 start, float heading, float speed, int samples, std::uint32_t t0 = 1000)
    {
        MotionTrack track;
        for (int i = 0; i < samples; ++i)
        {
            float const d = speed * float(kMotionSampleEveryMs) / 1000.f * float(i);
            track.Add(t0 + std::uint32_t(i) * kMotionSampleEveryMs, Advance(start, heading, d));
        }
        return track;
    }

    // MotionTrack / PredictSpot (moved from Scholomance's IlluciaLogic.h with their tests): still = on the mover.
    void TestMotionTrack()
    {
        CHECK(kMotionSampleEveryMs == 200 && kMotionVelocityWindowMs == 400);
        MotionTrack empty;
        CHECK(PredictSpot(empty, 1500).still);

        // Standing: on the mover.
        Prediction const p0 = PredictSpot(Walk({ 240.f, 0.f }, 0.f, 0.f, 5), 1500);
        CHECK(p0.still);
        CHECK(NearV(p0.at, Vec2{ 240.f, 0.f }));

        // One sample: no heading yet.
        MotionTrack one;
        one.Add(1000, { 230.f, 2.f });
        CHECK(PredictSpot(one, 1500).still);

        // Running east at 7 yd/s: 10.5 yd ahead in 1.5 s.
        MotionTrack run = Walk({ 220.f, 0.f }, 0.f, 7.f, 6);
        Vec2 const now = run.Latest().p;
        Prediction const p1 = PredictSpot(run, 1500);
        CHECK(!p1.still);
        CHECK(Near(p1.speed, 7.f, 0.05f));
        CHECK(Near(p1.heading, 0.f, 0.01f));
        CHECK(NearV(p1.at, Vec2{ now.x + 10.5f, now.y }, 0.05f));

        // Running north-west: the heading follows.
        float const nw = 3.f * kPi / 4.f;
        MotionTrack diag = Walk({ 240.f, -5.f }, nw, 7.f, 4);
        Prediction const p2 = PredictSpot(diag, 1500);
        CHECK(!p2.still);
        CHECK(Near(p2.heading, nw, 0.01f));
        CHECK(Near(Distance(diag.Latest().p, p2.at), 10.5f, 0.05f));

        // A turn shows within the 400 ms window: east for 1 s, then north for 0.4 s.
        MotionTrack turn = Walk({ 220.f, 0.f }, 0.f, 7.f, 6, 1000);
        Vec2 const corner = turn.Latest().p;
        turn.Add(2200, { corner.x, corner.y + 1.4f });
        turn.Add(2400, { corner.x, corner.y + 2.8f });
        Prediction const p3 = PredictSpot(turn, 1500);
        CHECK(!p3.still);
        CHECK(Near(p3.heading, kPi / 2.f, 0.01f));

        // Stopping: the newest 400 ms show no movement, so the prediction is on the mover again.
        MotionTrack stop = Walk({ 220.f, 0.f }, 0.f, 7.f, 6, 1000);
        Vec2 const halt = stop.Latest().p;
        stop.Add(2200, halt);
        stop.Add(2400, halt);
        Prediction const p4 = PredictSpot(stop, 1500);
        CHECK(p4.still);
        CHECK(NearV(p4.at, halt));

        // Walking slowly still counts as moving; creeping does not; 40 yd/s is a jump, not a heading.
        CHECK(!PredictSpot(Walk({ 220.f, 0.f }, 0.f, 2.5f, 4), 1500).still);
        CHECK(PredictSpot(Walk({ 220.f, 0.f }, 0.f, 0.5f, 4), 1500).still);
        CHECK(PredictSpot(Walk({ 220.f, 0.f }, 0.f, 40.f, 4), 1500).still);

        // Samples closer than 50 ms replace the newest; a clock going back starts over.
        MotionTrack close;
        close.Add(1000, { 0.f, 0.f });
        close.Add(1200, { 1.f, 0.f });
        close.Add(1220, { 1.5f, 0.f });
        CHECK(close.Size() == 2);
        CHECK(NearV(close.Latest().p, Vec2{ 1.5f, 0.f }));
        close.Add(500, { 9.f, 9.f });
        CHECK(close.Size() == 1);

        // The ring keeps its newest kSize samples.
        MotionTrack many = Walk({ 0.f, 0.f }, 0.f, 7.f, 20);
        CHECK(many.Size() == MotionTrack::kSize);
        CHECK(many.Latest().t == 1000 + 19 * kMotionSampleEveryMs);
    }

    // TrailRecorder (moved from Scholomance's IlluciaLogic.h with its tests): 4 yd pieces, released 2.5 yd behind the
    // mover, restarted by a jump over 12 yd (Illucia's Memory trail values).
    void TestTrailRecorder()
    {
        float constexpr segment = 4.f;
        float constexpr clear = 2.5f;
        float constexpr maxStep = 12.f;

        // A straight 7 yd/s run sampled every 200 ms (1.4 yd a sample): the pieces tile the path end to end, each
        // released once the runner is `clear` past its end.
        TrailRecorder trail(segment, clear, maxStep);
        std::vector<TrailSegment> laid;
        for (int i = 0; i <= 30; ++i)
        {
            Vec2 const p{ 210.f + 1.4f * float(i), 0.f };
            for (TrailSegment const& s : trail.Feed(p))
            {
                CHECK(Distance(p, s.to) >= clear - 0.001f);
                laid.push_back(s);
            }
        }
        CHECK(laid.size() >= 8);
        for (std::size_t i = 0; i < laid.size(); ++i)
        {
            float const len = Distance(laid[i].from, laid[i].to);
            CHECK(len >= segment - 0.001f && len < segment + 1.4f);
            if (i)
                CHECK(NearV(laid[i].from, laid[i - 1].to));
        }
        CHECK(NearV(laid.front().from, Vec2{ 210.f, 0.f }));

        // Flush lays only what the runner has left behind.
        for (TrailSegment const& s : trail.Flush({ 252.f, 0.f }))
            CHECK(Distance(Vec2{ 252.f, 0.f }, s.to) >= clear);
        CHECK(!trail.Started());

        // Standing still lays nothing.
        TrailRecorder idle(segment, clear, maxStep);
        std::size_t idleLaid = 0;
        for (int i = 0; i < 10; ++i)
            idleLaid += idle.Feed({ 240.f, 1.f }).size();
        CHECK(idleLaid == 0);
        CHECK(idle.Flush({ 240.f, 1.f }).empty());

        // A teleport starts over: no piece across the jump.
        TrailRecorder jump(segment, clear, maxStep);
        for (int i = 0; i <= 6; ++i)
            jump.Feed({ 210.f + 1.4f * float(i), 0.f });
        CHECK(jump.Feed({ 260.f, 5.f }).empty());
        CHECK(jump.Pending() == 0);
        bool crossed = false;
        for (int i = 1; i <= 10; ++i)
            for (TrailSegment const& s : jump.Feed({ 260.f + 1.4f * float(i), 5.f }))
                crossed = crossed || s.from.x < 259.f;
        CHECK(!crossed);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Stratholme WP-KT-1
    // ----------------------------------------------------------------------------------------------------------------

    // A fixed run of [0, 1) numbers, repeating.
    struct SeqRand01
    {
        std::vector<float> values;
        std::size_t next = 0;

        float operator()()
        {
            if (values.empty())
                return 0.f;
            float const v = values[next % values.size()];
            ++next;
            return v;
        }
    };

    void TestFloorPath()
    {
        auto flat = [](float, float, float) -> std::optional<float> { return 10.f; };
        std::vector<FloorPathPoint> const path = FloorPath(Vec2{ 0.f, 0.f }, Vec2{ 7.f, 0.f }, 12.f, flat);
        // Both ends, a point every 2 yd: 0, 2, 4, 6, 7.
        CHECK(path.size() == 5);
        CHECK(Near(path.front().x, 0.f, 1e-4f) && Near(path.front().z, 12.f, 1e-4f));
        CHECK(Near(path.back().x, 7.f, 1e-4f) && Near(path.back().y, 0.f, 1e-4f));
        CHECK(Near(path[1].x, 2.f, 1e-4f) && Near(path[1].z, 10.f, 1e-4f));     // 2 yd below the start: taken
        CHECK(Near(FloorPathLength(path), 7.f, 1e-3f));

        // A probe more than maxStepZ from the last point (a wall top) or no floor keeps the last height.
        auto wall = [](float x, float, float) -> std::optional<float>
        {
            if (x > 3.f && x < 5.f)
                return 20.f;
            if (x > 5.f)
                return std::nullopt;
            return 0.5f;
        };
        std::vector<FloorPathPoint> const walled = FloorPath(Vec2{ 0.f, 0.f }, Vec2{ 8.f, 0.f }, 0.f, wall);
        for (FloorPathPoint const& p : walled)
            CHECK(p.z <= 0.5f + 1e-4f);
        CHECK(Near(walled[1].z, 0.5f, 1e-4f));

        // A ramp: every step within maxStepZ follows it.
        auto ramp = [](float x, float, float) -> std::optional<float> { return x * 0.5f; };
        std::vector<FloorPathPoint> const up = FloorPath(Vec2{ 0.f, 0.f }, Vec2{ 0.f, 10.f }, 0.f, ramp, 1.f);
        CHECK(up.size() == 11);
        CHECK(Near(up.back().z, 0.f, 1e-4f));                   // x stays 0 on a north-south lane
        std::vector<FloorPathPoint> const east = FloorPath(Vec2{ 0.f, 0.f }, Vec2{ 10.f, 0.f }, 0.f, ramp, 1.f);
        CHECK(Near(east.back().z, 5.f, 1e-4f));

        // A zero-length lane or step: the start only.
        CHECK(FloorPath(Vec2{ 1.f, 1.f }, Vec2{ 1.f, 1.f }, 3.f, flat).size() == 1);
        CHECK(FloorPath(Vec2{ 1.f, 1.f }, Vec2{ 5.f, 1.f }, 3.f, flat, 0.f).size() == 1);

        // Parity: the kit's FloorPath is Gilnid's (kit #12, lifted unchanged) on the same lane and probe.
        Gilnid::Lane lane;
        lane.from = { -40.f, -380.f };
        lane.to = { -12.f, -401.f };
        lane.length = Distance(lane.from, lane.to);
        auto bumpy = [](float x, float y, float z) -> std::optional<float>
        {
            float const h = 20.f + std::sin(x * 0.3f) * 1.5f + (y < -395.f ? 4.f : 0.f);
            return std::fabs(h - z) < 10.f ? std::optional<float>(h) : std::nullopt;
        };
        std::vector<Gilnid::PathPoint> const theirs = Gilnid::FloorPath(lane, 21.f, bumpy);
        std::vector<FloorPathPoint> const ours = FloorPath(lane.from, lane.to, 21.f, bumpy);
        CHECK(theirs.size() == ours.size());
        for (std::size_t i = 0; i < std::min(theirs.size(), ours.size()); ++i)
            CHECK(Near(theirs[i].x, ours[i].x, 1e-3f) && Near(theirs[i].y, ours[i].y, 1e-3f)
                && Near(theirs[i].z, ours[i].z, 1e-3f));
        CHECK(kFloorPathStepYd == Gilnid::kFloorPathStepYd && kFloorPathMaxStepZ == Gilnid::kFloorPathMaxStepZ);
    }

    void TestFloorSpots()
    {
        Vec2 const near{ 100.f, 100.f };

        // RingPoint stays in its ring.
        for (float u : { 0.f, 0.25f, 0.5f, 0.99f })
            for (float v : { 0.f, 0.3f, 0.7f })
            {
                float const d = Distance(near, RingPoint(near, 4.f, 9.f, u, v));
                CHECK(d >= 4.f - 1e-3f && d <= 9.f + 1e-3f);
            }
        CHECK(Near(Distance(near, RingPoint(near, 4.f, 9.f, 0.f, 0.f)), 4.f, 1e-3f));

        auto anyFloor = [](Vec2) -> std::optional<float> { return 5.f; };

        // No rules in the way: the first candidate, full, on the floor height.
        FloorSpotRules rules;
        rules.near = near;
        rules.minRange = 5.f;
        rules.maxRange = 10.f;
        SeqRand01 rand{ { 0.5f, 0.25f } };
        std::optional<FloorSpot> const first = PickFloorSpotFrom(rules, rand, anyFloor);
        CHECK(first && first->full && Near(first->z, 5.f, 1e-4f));
        CHECK(first && Distance(near, first->p) >= 5.f && Distance(near, first->p) <= 10.f);

        // An avoid circle over the whole east half: every pick lands west of it (or on its margin's far side).
        FloorSpotRules avoidEast = rules;
        avoidEast.avoid.push_back({ Vec2{ 120.f, 100.f }, 19.f });
        avoidEast.avoidMargin = 1.f;
        SeqRand01 sweep{ { 0.1f, 0.05f, 0.9f, 0.5f, 0.3f, 0.45f, 0.7f, 0.55f, 0.2f, 0.95f } };
        for (int i = 0; i < 6; ++i)
        {
            std::optional<FloorSpot> const s = PickFloorSpotFrom(avoidEast, sweep, anyFloor);
            CHECK(s && s->full);
            CHECK(s && Distance(s->p, Vec2{ 120.f, 100.f }) >= 20.f - 1e-3f);
        }

        // Away from the players: never within minFromAway of one.
        FloorSpotRules away = rules;
        away.awayFrom = { Vec2{ 107.f, 100.f }, Vec2{ 93.f, 100.f } };
        away.minFromAway = 4.f;
        SeqRand01 spread{ { 0.1f, 0.05f, 0.9f, 0.5f, 0.6f, 0.25f, 0.3f, 0.45f, 0.4f, 0.75f, 0.2f, 0.95f } };
        for (int i = 0; i < 6; ++i)
        {
            std::optional<FloorSpot> const s = PickFloorSpotFrom(away, spread, anyFloor);
            CHECK(s && s->full);
            for (Vec2 const& q : away.awayFrom)
                CHECK(s && Distance(s->p, q) >= 4.f - 1e-3f);
        }

        // No floor anywhere: nothing.
        auto noFloor = [](Vec2) -> std::optional<float> { return std::nullopt; };
        CHECK(!PickFloorSpotFrom(rules, sweep, noFloor));

        // Every random candidate blocked: the first fixed fallback that keeps the rules.
        FloorSpotRules blocked = rules;
        blocked.avoid.push_back({ near, 11.f });
        std::vector<Vec2> const fixed{ Vec2{ 105.f, 100.f }, Vec2{ 130.f, 100.f }, Vec2{ 140.f, 100.f } };
        std::optional<FloorSpot> const fb = PickFloorSpotFrom(blocked, sweep, anyFloor, fixed);
        CHECK(fb && fb->full && Near(fb->p.x, 130.f, 1e-4f));

        // Nothing keeps the rules: best effort gives the candidate with the most room, without it nothing.
        std::optional<FloorSpot> const best = PickFloorSpotFrom(blocked, sweep, anyFloor);
        CHECK(best && !best->full);
        FloorSpotRules strict = blocked;
        strict.bestEffort = false;
        CHECK(!PickFloorSpotFrom(strict, sweep, anyFloor));

        // A floor test that only takes the west half (the arena): every pick is west.
        auto westOnly = [](Vec2 p) -> std::optional<float>
        {
            return p.x < 100.f ? std::optional<float>(1.f) : std::nullopt;
        };
        for (int i = 0; i < 5; ++i)
        {
            std::optional<FloorSpot> const s = PickFloorSpotFrom(rules, sweep, westOnly);
            CHECK(!s || s->p.x < 100.f);
        }

        // Scores: an avoid hit costs more than any room.
        FloorSpotRules scoring = rules;
        scoring.avoid.push_back({ Vec2{ 0.f, 0.f }, 5.f });
        CHECK(ScoreFloorSpot(scoring, Vec2{ 1.f, 0.f }).avoidHits == 1);
        CHECK(ScoreFloorSpot(scoring, Vec2{ 60.f, 0.f }).Full());
        CHECK(ScoreFloorSpot(scoring, Vec2{ 60.f, 0.f }).Value() > ScoreFloorSpot(scoring, Vec2{ 1.f, 0.f }).Value());
    }

    void TestPuddles()
    {
        PuddleSet set(3.f);
        PuddleSet::AddResult const a = set.Add(0, { 0.f, 0.f }, 10.f, 5.f, 1000, 0, true);
        CHECK(a.id == 1 && !a.merged);

        // Arming: outline first, the puddle counts from armAfter.
        CHECK(!set.Contains(500, { 1.f, 0.f }, 10.f));
        CHECK(set.Contains(500, { 1.f, 0.f }, 10.f, true));
        CHECK(set.Contains(1000, { 1.f, 0.f }, 10.f));
        CHECK(!set.Contains(1000, { 5.5f, 0.f }, 10.f));
        CHECK(!set.Contains(1000, { 1.f, 0.f }, 14.f));        // another floor: out of the z band

        // The merge rule: a center inside a live puddle adds nothing; just outside it, a new one.
        PuddleSet::AddResult const merged = set.Add(2000, { 4.f, 0.f }, 10.f, 7.f, 1000, 0, true);
        CHECK(merged.merged && merged.id == a.id && set.Size() == 1);
        PuddleSet::AddResult const apart = set.Add(2000, { 6.f, 0.f }, 10.f, 5.f, 1000, 0, true);
        CHECK(!apart.merged && apart.id == 2 && set.Size() == 2);
        // Without the merge rule, a puddle on a puddle is its own.
        PuddleSet::AddResult const stacked = set.Add(2000, { 0.f, 0.f }, 10.f, 5.f, 0, 3000, false);
        CHECK(!stacked.merged && set.Size() == 3);
        // Another floor never merges.
        CHECK(!set.Add(2000, { 0.f, 0.f }, 20.f, 5.f, 0, 1000, true).merged);
        CHECK(set.Size() == 4);

        // The union: a spot under two puddles is one puddle (the first added).
        CHECK(set.PuddleAt(3000, { 0.5f, 0.f }, 10.f) == a.id);
        CHECK(set.PuddleAt(3000, { 9.f, 0.f }, 10.f) == apart.id);

        // Life: expired puddles leave; Prune names them.
        std::vector<std::uint32_t> gone = set.Prune(3500);
        CHECK(gone.size() == 1);                                // the z 20 one (life 1000 from 2000)
        gone = set.Prune(5000);
        CHECK(gone.size() == 1 && gone.front() == stacked.id);
        CHECK(set.Size() == 2 && !set.Find(stacked.id) && set.Find(a.id));
        CHECK(set.Remove(apart.id) && !set.Remove(apart.id) && set.Size() == 1);

        // Area: one 5 yd puddle is pi r^2; an identical one on top adds nothing; one apart doubles it.
        PuddleSet area;
        area.Add(0, { 0.f, 0.f }, 0.f, 5.f, 0, 0, false);
        float const one = area.CoveredArea(0);
        CHECK(Near(one, kPi * 25.f, kPi * 25.f * 0.03f));
        area.Add(0, { 0.f, 0.f }, 0.f, 5.f, 0, 0, false);
        CHECK(Near(area.CoveredArea(0), one, 0.01f));
        area.Add(0, { 30.f, 0.f }, 0.f, 5.f, 0, 0, false);
        CHECK(Near(area.CoveredArea(0), 2.f * one, one * 0.02f));
        // Two half-overlapping (centers 5 yd apart): the lens counts once.
        PuddleSet lens;
        lens.Add(0, { 0.f, 0.f }, 0.f, 5.f, 0, 0, false);
        lens.Add(0, { 5.f, 0.f }, 0.f, 5.f, 0, 0, false);
        float const overlap = 2.f * 25.f * std::acos(0.5f) - 2.5f * std::sqrt(100.f - 25.f);
        CHECK(Near(lens.CoveredArea(0), 2.f * kPi * 25.f - overlap, 2.f));
        area.Clear();
        CHECK(area.CoveredArea(0) == 0.f && area.Size() == 0);
    }

    void TestInsideClock()
    {
        InsideClock clock;
        auto times = clock.Update({ 1, 2 }, 250);
        CHECK(times.size() == 2 && times[0].second == 250 && times[1].second == 250);
        times = clock.Update({ 1, 2 }, 250);
        CHECK(clock.Of(1) == 500 && clock.Of(2) == 500);
        // Player 2 steps out for one poll: their time starts over.
        clock.Update({ 1 }, 250);
        CHECK(clock.Of(1) == 750 && clock.Of(2) == 0);
        clock.Update({ 1, 2 }, 250);
        CHECK(clock.Of(1) == 1000 && clock.Of(2) == 250);
        clock.Clear();
        CHECK(clock.Of(1) == 0);
    }

    void TestWeightedSplit()
    {
        // No stacks: exactly SplitDamage's even split.
        std::vector<std::uint32_t> const even = WeightedSplit(1000, { 0, 0, 0 }, 1.f);
        CHECK(even == SplitDamage(1000, 3, 0));
        CHECK(WeightedSplit(1000, {}, 1.f).empty());

        // The Death Knell (ruling 40: +100% per Death's Echo stack): 90% of 3,670 = 3,303 among three, stacks 0, 1, 2.
        std::uint32_t const total = RefFlatValue(3670, 3710, 90.f, false);
        CHECK(total == 3303);
        std::vector<std::uint32_t> const knell = WeightedSplit(total, { 0, 1, 2 }, 1.f);
        CHECK(knell.size() == 3);
        CHECK(knell[0] == 1101 && knell[1] == 2202 && knell[2] == 3303);
        // Alone with one stack: the whole hit twice over.
        CHECK(WeightedSplit(total, { 1 }, 1.f).front() == 2 * total);

        // Half a share per stack, and a cap per share.
        std::vector<std::uint32_t> const half = WeightedSplit(1000, { 0, 1 }, 0.5f);
        CHECK(half[0] == 500 && half[1] == 750);
        std::vector<std::uint32_t> const capped = WeightedSplit(1000, { 0, 3 }, 1.f, 1200);
        CHECK(capped[0] == 500 && capped[1] == 1200);
        // The remainder lands on the first shares, then each is weighted.
        std::vector<std::uint32_t> const rest = WeightedSplit(10, { 1, 0, 0 }, 1.f);
        CHECK(rest[0] == 8 && rest[1] == 3 && rest[2] == 3);
    }

    void TestCappedWave()
    {
        CHECK(CappedWaveSize(3, 0, 0) == 3);        // no cap
        CHECK(CappedWaveSize(3, 4, 6) == 2);        // the Baron's 6
        CHECK(CappedWaveSize(3, 6, 6) == 0);
        CHECK(CappedWaveSize(3, 9, 6) == 0);
        CHECK(CappedWaveSize(2, 1, 6) == 2);
    }

    void TestCastQueue()
    {
        enum : std::uint32_t
        {
            FILLER = 1,
            COCOON = 2,
            BROOD = 3,
            SKITTER = 4,
        };

        CastQueue q(1000);
        CHECK(!q.Next(0));
        q.Schedule(COCOON, 10000, 2);
        q.Schedule(BROOD, 10000, 3);
        q.Schedule(FILLER, 9000, 0);
        CHECK(q.Size() == 3 && q.Queued(BROOD) && q.DueAt(COCOON) == 10000u);
        CHECK(q.Next(9000) == FILLER);                  // only the filler is due
        q.Started(FILLER, 9000, 2000, false);           // a 2 s filler, unspaced
        CHECK(!q.Queued(FILLER));
        CHECK(!q.Next(10000));                          // the caster is still busy
        // Both mechanics due together: the higher priority first, the other waits for its end plus the spacing.
        CHECK(q.Next(11000) == BROOD);
        q.Started(BROOD, 11000, 3000);
        CHECK(!q.Next(13999));
        CHECK(!q.Next(14500));                          // the spacing after the brood call
        CHECK(q.Next(15000) == COCOON);
        q.Started(COCOON, 15000, 0);
        CHECK(!q.Next(15500) && q.Size() == 0);

        // Ties in priority: the earlier due, then the lower id.
        q.Reset();
        q.Schedule(SKITTER, 500, 1);
        q.Schedule(COCOON, 400, 1);
        CHECK(q.Next(600) == COCOON);
        q.Schedule(COCOON, 500, 1);                     // rescheduled: replaces
        CHECK(q.Size() == 2 && q.Next(600) == COCOON);
        q.Cancel(COCOON);
        CHECK(q.Next(600) == SKITTER);

        // A filler with dropAfter: skipped while it waits too long, then dropped.
        q.Reset();
        q.Schedule(FILLER, 1000, 0, 2000);
        q.SetBusy(true);
        CHECK(!q.Next(1500) && q.Waiting(1500));
        q.SetBusy(false);
        CHECK(!q.Next(3000));
        std::vector<std::uint32_t> const dropped = q.DropStale(3000);
        CHECK(dropped.size() == 1 && dropped.front() == FILLER && q.Size() == 0);

        // An interrupted cast frees the caster at once; the spacing counts from the interrupt.
        q.Reset();
        q.Schedule(SKITTER, 0, 1);
        q.Schedule(COCOON, 0, 1);
        CHECK(q.Next(0) == COCOON);                     // a tie: the lower id
        q.Started(COCOON, 0, 5000);
        q.Interrupted(1000);
        CHECK(!q.Next(1500));
        CHECK(q.Next(2000) == SKITTER);
    }

    void TestHoldBook()
    {
        HoldBook book;
        CHECK(book.Add(100, 1, 6000));
        CHECK(!book.Add(101, 1, 6000));                 // one hold per unit
        CHECK(!book.Add(2, 2, 6000));                   // nobody holds themselves
        CHECK(book.Add(101, 2, 3000));
        CHECK(book.HolderOf(1) == 100 && book.HolderOf(3) == 0 && book.Size() == 2);

        auto all = [](std::uint64_t) { return true; };
        CHECK(book.Update(2000, all, all).empty());
        // Holder 101 broken: its hold ends with HolderGone; 100's runs on.
        std::vector<HoldBook::Ended> ended = book.Update(500, [](std::uint64_t h) { return h != 101; }, all);
        CHECK(ended.size() == 1 && ended[0].held == 2 && ended[0].why == HoldEnd::HolderGone);
        // A gone holder outranks a gone held unit.
        HoldBook both;
        both.Add(7, 8, 1000);
        auto none = [](std::uint64_t) { return false; };
        ended = both.Update(10, none, none);
        CHECK(ended.size() == 1 && ended[0].why == HoldEnd::HolderGone);
        // The held unit gone.
        both.Add(7, 8, 1000);
        ended = both.Update(10, all, none);
        CHECK(ended.size() == 1 && ended[0].why == HoldEnd::HeldGone);
        // Timeout at maxHold: 6,000 ms in all for unit 1 (2,500 spent).
        ended = book.Update(3499, all, all);
        CHECK(ended.empty());
        ended = book.Update(1, all, all);
        CHECK(ended.size() == 1 && ended[0].held == 1 && ended[0].why == HoldEnd::Timeout && book.Size() == 0);
        // Release and Clear.
        book.Add(100, 5, 1000);
        book.Add(100, 6, 1000);
        std::optional<HoldBook::Ended> const let = book.Release(5);
        CHECK(let && let->why == HoldEnd::Released && !book.Release(5));
        ended = book.Clear();
        CHECK(ended.size() == 1 && ended[0].held == 6 && ended[0].why == HoldEnd::Cleared && book.Size() == 0);
        CHECK(std::string(HoldEndName(HoldEnd::Timeout)) == "timeout");
    }

    void TestEffectPercent()
    {
        // DBC base points are stored one lower with DieSides 1 (the shown value = base + 1).
        CHECK(EffectShownValue(2999, 1) == 3000);
        CHECK(EffectShownValue(3000, 0) == 3000);
        CHECK(EffectShownValue(3000, 5) == 3001);       // a range: its low end
        CHECK(Near(EffectPercent(3000, 0, false), 30.f, 1e-4f));
        CHECK(Near(EffectPercent(3000, 0, true), 30.f, 1e-4f));     // no heroic value: the normal one
        CHECK(Near(EffectPercent(3000, 4500, true), 45.f, 1e-4f));
        CHECK(Near(EffectPercent(3000, 4500, false), 30.f, 1e-4f));
        CHECK(Near(EffectPercent(50, 0, false), 0.5f, 1e-4f));
        CHECK(EffectPercent(-5, 0, false) == 0.f);
        // 30% of the normal pin: the registry's own rounding.
        CHECK(RefFlatValue(3670, 3710, EffectPercent(3000, 0, false), false) == 1101);
    }
}

int main()
{
    TestAliases();
    TestGeometry();
    TestFrames();
    TestSaveStrings();
    TestRolls();
    TestArena();
    TestShipArenaParity();
    TestGripTracker();
    TestLanding();
    TestSplitDamage();
    TestPicks();
    TestSpeedStacksLethal();
    TestLineStrike();
    TestDwell();
    TestLethalLatch();
    TestLeashTimer();
    TestGripCooldown();
    TestLandingOrBoss();
    TestStackCapReachQuiet();
    TestLegacyReaderResize();
    TestTrackerForget();
    TestMotionTrack();
    TestTrailRecorder();
    TestFloorPath();
    TestFloorSpots();
    TestPuddles();
    TestInsideClock();
    TestWeightedSplit();
    TestCappedWave();
    TestCastQueue();
    TestHoldBook();
    TestEffectPercent();
    return Report("dungeon_kit_test");
}
