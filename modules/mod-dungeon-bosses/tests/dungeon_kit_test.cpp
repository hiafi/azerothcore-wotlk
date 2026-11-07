// Host tests for the shared dungeon kit's pure part (WP-K0): DungeonKitMath.h, DungeonKitState.h, DungeonKitArena.h,
// DungeonKitLogic.h and DungeonKitIds.h, plus the parity of the Deadmines aliases (DeadminesKit, Greenskin) with the
// generic pieces they now name.
#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include "DungeonKitArena.h"
#include "DungeonKitIds.h"
#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include "DungeonKitState.h"
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
    return Report("dungeon_kit_test");
}
