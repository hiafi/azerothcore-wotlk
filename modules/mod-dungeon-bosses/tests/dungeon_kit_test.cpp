// Host tests for the shared dungeon kit's pure part (WP-K0): DungeonKitMath.h, DungeonKitState.h, DungeonKitArena.h,
// DungeonKitLogic.h and DungeonKitIds.h, plus the parity of the Deadmines aliases (DeadminesKit, Greenskin) with the
// generic pieces they now name. Stratholme WP-KT-1: DungeonKitFloor.h (FloorPath and its parity with Gilnid's, floor
// spots, puddles, the inside clock) and DungeonKitFlow.h (weighted split, wave cap, cast queue, holds, percents).
// Blackrock Spire WP-KT-B1: DungeonKitFlexRules.h (the flex 5-10 rules) and DungeonKitChaseLogic.h (the chaser's
// clock, the crawl clock, the fall catch book). Blackrock Depths WP-KT-D1: DungeonKitBodyLogic.h (death spots, held
// bodies) and DungeonKitEdgeLogic.h (the push over a floor's edge, edge bands). WP-KT-D2: DungeonKitPoolLogic.h (the
// shared health pool, the damage tally). Scarlet Monastery WP-KT-SM: DungeonKitZoneLogic.h (growth, rungs, turning
// beams) and DungeonKitWingLogic.h (portal travelers, trigger clearance, the seal, stragglers, credit latch, the ward).
#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include "DungeonKitArena.h"
#include "DungeonKitBodyLogic.h"
#include "DungeonKitChaseLogic.h"
#include "DungeonKitEdgeLogic.h"
#include "DungeonKitFlexRules.h"
#include "DungeonKitFloor.h"
#include "DungeonKitFlow.h"
#include "DungeonKitIds.h"
#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include "DungeonKitPoolLogic.h"
#include "DungeonKitState.h"
#include "DungeonKitWingLogic.h"
#include "DungeonKitZoneLogic.h"
#include "GilnidLogic.h"
#include "GreenskinLogic.h"
#include "check.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>
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
        // a rule that skips the healer never picks one, and a tank and healer alone get nobody (no fallback)
        PickCandidate healerC;
        healerC.id = 7;
        healerC.distance = 6.f;
        healerC.healer = true;
        PickCandidate tankC;
        tankC.id = 8;
        tankC.tank = true;
        PickCandidate dpsC;
        dpsC.id = 9;
        dpsC.distance = 9.f;
        PickRule noHealer;
        noHealer.nonHealer = true;
        std::vector<PickCandidate> const group = { tankC, healerC, dpsC };
        for (std::uint32_t r = 0; r < 20; ++r)
        {
            auto const pick = PickFrom(group, noHealer, FixedRand{ r });
            CHECK(pick && group[*pick].id == 9);
        }
        CHECK(PickFrom(group, PickRule{}, FixedRand{ 1 }).has_value());     // off by default: the healer qualifies
        std::vector<PickCandidate> const tankAndHealer = { tankC, healerC };
        PickRule tankAndHealerRule;
        tankAndHealerRule.nonHealer = true;
        tankAndHealerRule.tankIfAlone = true;       // the tank fallback never brings the healer back
        auto const fallback = PickFrom(tankAndHealer, tankAndHealerRule, FixedRand{ 0 });
        CHECK(!fallback.has_value() || tankAndHealer[*fallback].id == 8);
        tankAndHealerRule.tankIfAlone = false;
        CHECK(!PickFrom(tankAndHealer, tankAndHealerRule, FixedRand{ 0 }).has_value());
        CHECK(PickDistinctFrom(group, noHealer, 5, FixedRand{ 0 }).size() == 1u);
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

    void TestPerStackAmount()
    {
        // R-1-KIT F1: a recalculation without a caster never falls back to the raw hundredths.
        PerStackAmount fresh;
        CHECK(fresh.Resolve(std::nullopt, std::nullopt) == 0);                // nothing known: 0, not 400
        CHECK(fresh.Resolve(std::nullopt, 147) == 147);                        // the owner's row
        CHECK(!fresh.Cached());                                                 // the owner's value is not kept
        PerStackAmount amount;
        CHECK(amount.Resolve(147, 999) == 147);                                 // the caster's value wins
        CHECK(amount.Cached() && *amount.Cached() == 147);
        CHECK(amount.Resolve(std::nullopt, 999) == 147);                       // the stalker despawned: cached
        CHECK(amount.Resolve(std::nullopt, std::nullopt) == 147);
        CHECK(amount.Resolve(150, std::nullopt) == 150);                       // a later caster recalculation
        CHECK(amount.Resolve(std::nullopt, std::nullopt) == 150);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Blackrock Spire WP-KT-B1
    // ----------------------------------------------------------------------------------------------------------------

    void TestFlexRules()
    {
        // The count: clamped to 5..10; 0 ("not held") reads as 5.
        CHECK(Flex::Clamp(0) == 5 && Flex::Clamp(3) == 5 && Flex::Clamp(5) == 5 && Flex::Clamp(7) == 7);
        CHECK(Flex::Clamp(10) == 10 && Flex::Clamp(15) == 10 && Flex::Clamp(40) == 10);
        // The ladder: 1.00 .. 2.25 in steps of 0.25.
        double const ladder[] = { 1.0, 1.25, 1.5, 1.75, 2.0, 2.25 };
        for (std::uint32_t n = 5; n <= 10; ++n)
            CHECK(std::fabs(Flex::Ladder(n) - ladder[n - 5]) < 1e-9);
        CHECK(Flex::Ladder(0) == 1.0 && Flex::Ladder(12) == 2.25);
        // Health: base x ladder, rounded, at least 1, saturating.
        CHECK(Flex::HealthAt(5, 100000) == 100000 && Flex::HealthAt(6, 100000) == 125000);
        CHECK(Flex::HealthAt(10, 400000) == 900000 && Flex::HealthAt(0, 3000) == 3000);
        CHECK(Flex::HealthAt(7, 3) == 5);           // 4.5 rounds up
        CHECK(Flex::HealthAt(5, 0) == 1);
        CHECK(Flex::HealthAt(10, 0xFFFFFFFFu) == 0xFFFFFFFFu);
        // Target counts: a at 5, b at 6 or more (and at 0: a).
        CHECK(Flex::TargetCount(0, 1, 2) == 1 && Flex::TargetCount(5, 1, 2) == 1);
        CHECK(Flex::TargetCount(6, 1, 2) == 2 && Flex::TargetCount(10, 3, 6) == 6 && Flex::TargetCount(12, 3, 6) == 6);
        CHECK(FlexCount(5, 2, 4) == 2 && FlexCount(6, 2, 4) == 4);
        static_assert(FlexCount(9, 1, 2) == 2, "constexpr");
        // Loot: one roll below 10, two at 10.
        for (std::uint32_t n = 0; n < 10; ++n)
            CHECK(Flex::LootRolls(n) == 1);
        CHECK(Flex::LootRolls(10) == 2 && Flex::LootRolls(15) == 2);
        // The taunt swap: only at 10 (after the clamp).
        for (std::uint32_t n = 0; n < 10; ++n)
            CHECK(!Flex::TankSwapOn(n));
        CHECK(Flex::TankSwapOn(10) && Flex::TankSwapOn(11));
        // The flex loot bits: LootMode 4 (+ 8 with the hard mode) only on a two-roll kill; never bit 2.
        CHECK(Flex::LootBits(5, false) == 0 && Flex::LootBits(9, true) == 0);
        CHECK(Flex::LootBits(10, false) == 0x04 && Flex::LootBits(10, true) == 0x0C);
        CHECK((Flex::kLootModeFlexMask & 0x02) == 0 && Flex::kLootModeFlexMask == 0x0C);
    }

    void TestChaseClock()
    {
        ChaseTuning t;
        t.pauseMs = 1000;
        t.reach = 2.f;
        // A plain chase: move until within reach, then arrive once and end.
        {
            ChaseClock c(t);
            CHECK(c.Update(100, false, true, 10.f) == ChaseStep::Move);
            CHECK(c.Update(100, false, true, 2.5f) == ChaseStep::Move);
            CHECK(c.Update(100, false, true, 2.f) == ChaseStep::Arrive);
            CHECK(c.Done() && c.Update(100, false, true, 1.f) == ChaseStep::Expire);
        }
        // A short toss: held 1 s from its start, though the toss itself lasts 300 ms.
        {
            ChaseClock c(t);
            CHECK(c.Update(100, true, true, 10.f) == ChaseStep::Hold);      // tossed: 1000 left
            CHECK(c.Update(300, true, true, 10.f) == ChaseStep::Hold);      // 700
            CHECK(c.Update(300, false, true, 10.f) == ChaseStep::Hold);     // landed: 400
            CHECK(c.Holding());
            CHECK(c.Update(300, false, true, 10.f) == ChaseStep::Hold);     // 100
            CHECK(c.Update(100, false, true, 10.f) == ChaseStep::Move);     // 0: off again
            CHECK(!c.Holding());
        }
        // A long stun: held for the stun, then nothing more (the pause counts from the start).
        {
            ChaseClock c(t);
            CHECK(c.Update(50, true, true, 10.f) == ChaseStep::Hold);
            for (int i = 0; i < 30; ++i)
                CHECK(c.Update(100, true, true, 10.f) == ChaseStep::Hold);   // 3 s stunned
            CHECK(c.Update(50, false, true, 10.f) == ChaseStep::Move);
        }
        // A hold ignores the target and the arrival; after it, a dead target asks for a retarget.
        {
            ChaseClock c(t);
            CHECK(c.Update(100, true, false, 0.f) == ChaseStep::Hold);
            CHECK(c.Update(100, true, true, 1.f) == ChaseStep::Hold);       // within reach, but stunned
            CHECK(c.Update(1000, false, false, 0.f) == ChaseStep::Retarget);
            c.Retargeted();
            CHECK(c.Update(100, false, true, 8.f) == ChaseStep::Move);
        }
        // No-threat mode: a retarget every 3 s, the period restarting at each pick.
        {
            ChaseTuning nt = t;
            nt.retargetEveryMs = 3000;
            ChaseClock c(nt);
            CHECK(c.Update(2900, false, true, 9.f) == ChaseStep::Move);
            CHECK(c.Update(100, false, true, 9.f) == ChaseStep::Retarget);
            c.Retargeted();
            CHECK(c.Update(2999, false, true, 9.f) == ChaseStep::Move);
            CHECK(c.Update(1, false, true, 9.f) == ChaseStep::Retarget);
        }
        // Life: expires even mid-hold, and stays expired.
        {
            ChaseTuning lt = t;
            lt.lifeMs = 10000;
            ChaseClock c(lt);
            CHECK(c.Update(9900, false, true, 9.f) == ChaseStep::Move);
            CHECK(c.Update(50, true, true, 9.f) == ChaseStep::Hold);
            CHECK(c.Update(50, true, true, 9.f) == ChaseStep::Expire);
            CHECK(c.Done() && c.Update(10, false, true, 1.f) == ChaseStep::Expire);
        }
        // Keep chasing (whelps on the flame holder): Arrive once per contact, again only after leaving reach + 1.
        {
            ChaseTuning kt = t;
            kt.endOnArrive = false;
            ChaseClock c(kt);
            CHECK(c.Update(100, false, true, 1.f) == ChaseStep::Arrive);
            CHECK(c.Update(100, false, true, 1.5f) == ChaseStep::Move);
            CHECK(c.Update(100, false, true, 2.9f) == ChaseStep::Move);     // within the slack: same contact
            CHECK(c.Update(100, false, true, 1.f) == ChaseStep::Move);
            CHECK(c.Update(100, false, true, 3.5f) == ChaseStep::Move);     // left
            CHECK(c.Update(100, false, true, 2.f) == ChaseStep::Arrive);
            CHECK(!c.Done());
            CHECK(c.Update(100, true, true, 1.f) == ChaseStep::Hold);       // a stun ends the contact
            CHECK(c.Update(1000, false, true, 1.f) == ChaseStep::Arrive);
        }
        // Restart clears everything.
        {
            ChaseClock c(t);
            c.Update(100, false, true, 1.f);
            CHECK(c.Done());
            c.Restart();
            CHECK(!c.Done() && c.ElapsedMs() == 0 && c.Update(100, false, true, 9.f) == ChaseStep::Move);
        }
    }

    void TestCrawlClock()
    {
        // Urok's shard on normal: 10 s lying still, then a crawl until 1.5 yd from him.
        {
            CrawlClock c(10000, 0, 1.5f);
            CHECK(c.Update(9750, true, 30.f) == CrawlStep::Wait);
            CHECK(!c.Crawling());
            CHECK(c.Update(250, true, 30.f) == CrawlStep::Crawl);
            CHECK(c.Crawling());
            CHECK(c.Update(250, true, 1.6f) == CrawlStep::Crawl);
            CHECK(c.Update(250, true, 1.5f) == CrawlStep::Reach);
            CHECK(c.Done() && c.Update(250, true, 9.f) == CrawlStep::Reach);
        }
        // No goal (the pile gone, no Urok yet): it waits however long; a goal later starts the crawl at once.
        {
            CrawlClock c(7000, 0, 1.5f);
            CHECK(c.Update(20000, false, 0.f) == CrawlStep::Wait);
            CHECK(c.Update(250, true, 12.f) == CrawlStep::Crawl);
        }
        // Lying still inside reach of the goal does not count until the wait is over (a shard dropped at his feet).
        {
            CrawlClock c(7000, 0, 1.5f);
            CHECK(c.Update(250, true, 0.5f) == CrawlStep::Wait);
            CHECK(c.Update(6750, true, 0.5f) == CrawlStep::Reach);
        }
        // Crawl off: never moves; a life ends it.
        {
            CrawlClock c(0, 5000, 1.5f, false);
            CHECK(c.Update(4999, true, 0.f) == CrawlStep::Wait);
            CHECK(c.Update(1, true, 0.f) == CrawlStep::Expire);
        }
    }

    void TestFallCatch()
    {
        // Omokk's Pit Drop: deck at 100, caught 15 yd under it, inside the pit only, 3 s grace.
        CHECK(!BelowDeck(86.f, 100.f, 15.f) && BelowDeck(85.f, 100.f, 15.f) && BelowDeck(40.f, 100.f, 15.f));
        FallCatchBook book(3000);
        CHECK(!book.Check(1, 90.f, true, 100.f, 15.f, 0));          // falling, not deep enough yet
        CHECK(!book.Check(1, 80.f, false, 100.f, 15.f, 100));       // deep, but outside the pit (another level)
        CHECK(book.Check(1, 84.f, true, 100.f, 15.f, 200));         // caught
        CHECK(book.Size() == 1);
        CHECK(!book.Check(1, 84.f, true, 100.f, 15.f, 1200));       // still climbing back: no second catch
        CHECK(book.Check(2, 50.f, true, 100.f, 15.f, 1200));        // the pit floor: caught the same way
        CHECK(!book.Check(1, 84.f, true, 100.f, 15.f, 3199));
        CHECK(book.Check(1, 84.f, true, 100.f, 15.f, 3200));        // a second fall after the grace
        book.Prune(4199);
        CHECK(book.Size() == 2);
        book.Prune(4200);
        CHECK(book.Size() == 1);
        book.Prune(6200);
        CHECK(book.Size() == 0);
        book.Check(3, 10.f, true, 100.f, 15.f, 7000);
        book.Clear();
        CHECK(book.Size() == 0 && book.Check(3, 10.f, true, 100.f, 15.f, 7001));

        // K-m5: the pet watch takes pets and guardians, never totems or charmed mobs.
        static_assert(WatchesControlled(true, true, false, false));     // a hunter pet (pets are guardians)
        static_assert(WatchesControlled(false, true, false, false));    // a guardian (Water Elemental, treants)
        CHECK(!WatchesControlled(false, false, true, false));           // a totem (a minion)
        CHECK(!WatchesControlled(false, true, true, false));            // a totem even if flagged guardian
        CHECK(!WatchesControlled(false, false, false, true));           // a mind-controlled mob
        CHECK(!WatchesControlled(true, true, false, true));             // a charmed pet
        CHECK(!WatchesControlled(false, false, false, false));          // any other minion
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Blackrock Depths WP-KT-D1: death spots, held bodies, the push over the edge, edge bands
    // ----------------------------------------------------------------------------------------------------------------

    DeathSpot Spot(std::uint64_t id, std::uint32_t entry, float x, float y, std::uint64_t atMs, std::uint32_t tag = 0)
    {
        DeathSpot s;
        s.id = id;
        s.entry = entry;
        s.at = { x, y };
        s.z = -70.f;
        s.atMs = atMs;
        s.tag = tag;
        return s;
    }

    void TestDeathSpots()
    {
        // Raise Dead (SP S1 AN1): beasts die over a wave; Anub'shiah raises 1 or 2 at their spots, each spot once.
        DeathSpotBook book;
        book.Record(Spot(1, 9001, 0.f, 0.f, 100));
        book.Record(Spot(2, 9002, 10.f, 0.f, 200));
        book.Record(Spot(3, 9001, 20.f, 0.f, 300, 7));
        CHECK(book.Size() == 3 && book.Count() == 3);
        CHECK(book.Count({ 9001, 0, true }) == 2);
        CHECK(book.Count({ 0, 7, true }) == 1);

        std::vector<DeathSpot> taken = book.TakeOldest(1, { 9001, 0, true });
        CHECK(taken.size() == 1 && taken[0].id == 1 && taken[0].used);
        CHECK(book.Count({ 9001, 0, true }) == 1);             // spot 1 is spent
        CHECK(book.Count() == 3);                               // but still stored (Acid Burst may read it)
        taken = book.TakeOldest(5);
        CHECK(taken.size() == 2 && taken[0].id == 2 && taken[1].id == 3);
        CHECK(book.TakeOldest(1).empty());                      // nothing unused left
        CHECK(book.Mark(2, false) && book.Count({ 0, 0, true }) == 1);
        CHECK(!book.Mark(99));

        // A revived unit that dies again replaces its spot (unused again, the newest).
        book.Record(Spot(1, 9001, 5.f, 5.f, 400));
        CHECK(book.Size() == 3);
        std::optional<DeathSpot> const one = book.Find(1);
        CHECK(one && !one->used && Near(one->at.x, 5.f, 1e-4f) && one->atMs == 400);
        CHECK(book.All().back().id == 1);
        CHECK(!book.Find(42));

        // Random picks: distinct, marked used, never more than the pool.
        DeathSpotBook pool;
        for (std::uint64_t i = 1; i <= 4; ++i)
            pool.Record(Spot(i, 9003, static_cast<float>(i), 0.f, i * 10));
        std::vector<DeathSpot> const picked = pool.TakeRandom(3, FixedRand{ 1 });
        CHECK(picked.size() == 3);
        CHECK(picked[0].id == 2 && picked[1].id == 3 && picked[2].id == 4);    // index 1 of the remaining each time
        CHECK(pool.TakeRandom(3, FixedRand{ 7 }).size() == 1);                  // one left
        CHECK(pool.TakeRandom(1, FixedRand{ 0 }).empty());

        // Nearest (Acid Burst at the corpse nearest a point; the body itself is gone).
        DeathSpotBook near;
        near.Record(Spot(1, 9004, 0.f, 0.f, 0));
        near.Record(Spot(2, 9004, 10.f, 0.f, 0));
        std::optional<DeathSpot> n = near.Nearest({ 8.f, 0.f });
        CHECK(n && n->id == 2);
        CHECK(!near.Nearest({ 8.f, 30.f }, 5.f));                               // none within 5 yd
        near.TakeOldest(1);
        n = near.Nearest({ 1.f, 0.f });
        CHECK(n && n->id == 2);                                                 // spot 1 spent
        n = near.Nearest({ 1.f, 0.f }, 0.f, { 0, 0, false });
        CHECK(n && n->id == 1);                                                 // unless spent ones count

        // The cap drops the oldest death; Expire and Forget.
        DeathSpotBook capped(2);
        capped.Record(Spot(1, 1, 0.f, 0.f, 0));
        capped.Record(Spot(2, 1, 0.f, 0.f, 1000));
        capped.Record(Spot(3, 1, 0.f, 0.f, 2000));
        CHECK(capped.Size() == 2 && !capped.Find(1) && capped.Find(3));
        capped.Expire(2500, 1000);
        CHECK(capped.Size() == 1 && capped.Find(3));
        CHECK(capped.Forget(3) && !capped.Forget(3) && capped.Size() == 0);
        capped.Record(Spot(4, 1, 0.f, 0.f, 0));
        capped.Clear();
        CHECK(capped.Size() == 0);
    }

    void TestHeldBody()
    {
        // Korv's Ancestral Spirit (SP S1 EN5): one hold per member; a revived member dies for real.
        HeldBodyLatch body(1);
        CHECK(body.State() == BodyState::Up && body.HoldsLeft());
        HeldBodyLatch::Result r = body.Apply(1000, 400);
        CHECK(!r.clamped && !r.fell && r.damage == 400);
        r = body.Apply(600, 900);
        CHECK(r.clamped && r.fell && r.damage == 599 && body.Fallen() && body.Falls() == 1);
        r = body.Apply(1, 5000);                                    // a hit on the body: absorbed
        CHECK(r.clamped && !r.fell && r.damage == 0 && body.Fallen());
        r = body.Apply(1, 0);
        CHECK(!r.clamped && r.damage == 0);
        CHECK(!body.Update(60000));                                 // no hold limit: it lies until revived
        CHECK(body.Revive() && body.State() == BodyState::Up && body.Revives() == 1);
        CHECK(!body.Revive());                                      // only from Fallen
        CHECK(!body.HoldsLeft());
        r = body.Apply(500, 900);                                   // the second lethal hit is the real death
        CHECK(!r.clamped && r.damage == 900 && body.State() == BodyState::Dead);   // R-1-FW MIN-4
        CHECK(!body.HoldsLeft() && !body.Revive());
        std::vector<BodyState> const pair{ BodyState::Fallen, body.State() };
        CHECK(AllDown(pair));
        body.Reset();                                               // the next pull
        CHECK(body.HoldsLeft() && body.Falls() == 0 && body.Revives() == 0);

        // The Encore ends: a fallen body is finished (the real death); a finished body never falls again.
        CHECK(body.Apply(100, 100).fell);
        CHECK(body.Finish() && body.State() == BodyState::Dead);
        CHECK(!body.Finish() && !body.Revive());
        r = body.Apply(100, 100);
        CHECK(!r.clamped && r.damage == 100);

        // Acid Burst's swell (SP S1 RW6): held 2 s, then finished once.
        HeldBodyLatch swell(1, 2000);
        CHECK(!swell.Update(5000));                                 // standing: no clock
        CHECK(swell.Apply(50, 80).fell);
        CHECK(!swell.Update(1500) && swell.FallenMs() == 1500);
        CHECK(swell.Update(500));
        CHECK(!swell.Update(100));                                  // once
        CHECK(swell.Finish());

        // No holds: every lethal hit is real.
        HeldBodyLatch none(0);
        CHECK(!none.HoldsLeft() && !none.Apply(10, 10).clamped);
        CHECK(none.State() == BodyState::Dead);

        // Two holds (a unit raised twice).
        HeldBodyLatch twice(2);
        CHECK(twice.Apply(10, 10).fell && twice.Revive() && twice.Apply(10, 10).fell && twice.Falls() == 2);
        CHECK(twice.Revive() && !twice.Apply(10, 10).clamped);
        CHECK(twice.State() == BodyState::Dead);
        HeldBodyLatch chip(0);
        CHECK(!chip.Apply(10, 9).clamped && chip.State() == BodyState::Up);    // not lethal: still up

        // The team is down when every member lies or is dead.
        std::vector<BodyState> team{ BodyState::Fallen, BodyState::Dead, BodyState::Fallen };
        CHECK(AllDown(team));
        team.push_back(BodyState::Up);
        CHECK(!AllDown(team));
        CHECK(!AllDown(std::span<BodyState const>()));
    }

    // A 50 x 24 floor (x along it), and the same floor wound the other way.
    std::vector<Vec2> const kFloorCcw{ { 0.f, 0.f }, { 50.f, 0.f }, { 50.f, 24.f }, { 0.f, 24.f } };
    std::vector<Vec2> const kFloorCw{ { 0.f, 0.f }, { 0.f, 24.f }, { 50.f, 24.f }, { 50.f, 0.f } };

    void TestEdgePush()
    {
        float const south = Deg(270.f);
        float const north = Deg(90.f);

        // Nearest edge and its inward normal, either winding.
        std::optional<EdgePoint> e = NearestEdge(kFloorCcw, { 25.f, 6.f });
        CHECK(e && Near(e->distance, 6.f, 1e-4f) && e->edge == 0 && Near(e->point.x, 25.f, 1e-4f));
        Vec2 in = InwardNormal(kFloorCcw, 0);
        CHECK(Near(in.x, 0.f, 1e-5f) && Near(in.y, 1.f, 1e-5f));
        in = InwardNormal(kFloorCw, 3);                             // (50,0) -> (0,0): the same edge, reversed
        CHECK(Near(in.x, 0.f, 1e-5f) && Near(in.y, 1.f, 1e-5f));
        CHECK(!NearestEdge(std::vector<Vec2>{ { 0.f, 0.f } }, { 1.f, 1.f }));

        // The way out: to the nearest edge; on the edge, along its outward normal; off the floor, farther away.
        CHECK(Near(OutwardBearing(kFloorCcw, { 25.f, 2.f }), south, 1e-4f));
        CHECK(Near(OutwardBearing(kFloorCw, { 25.f, 2.f }), south, 1e-4f));
        CHECK(Near(OutwardBearing(kFloorCcw, { 25.f, 21.f }), north, 1e-4f));
        CHECK(Near(OutwardBearing(kFloorCcw, { 2.f, 12.f }), kPi, 1e-4f));
        CHECK(Near(OutwardBearing(kFloorCcw, { 25.f, 0.f }), south, 1e-4f));
        CHECK(Near(OutwardBearing(kFloorCcw, { 25.f, -3.f }), south, 1e-4f));
        CHECK(Near(OutwardBearing(std::vector<Vec2>{}, { 0.f, 0.f }, 1.25f), 1.25f, 1e-6f));

        // Away from the centre line (SP S2 913).
        CHECK(Near(AwayFromLine({ 0.f, 12.f }, { 50.f, 12.f }, { 25.f, 20.f }), north, 1e-4f));
        CHECK(Near(AwayFromLine({ 0.f, 12.f }, { 50.f, 12.f }, { 25.f, 4.f }), south, 1e-4f));
        CHECK(Near(AwayFromLine({ 0.f, 12.f }, { 50.f, 12.f }, { 25.f, 12.f }, 0.5f), 0.5f, 1e-6f));

        // Over the edge from the first band and from deep in a later one (plan section 8 #42): always 4 yd past it.
        EdgePush p = PlanOverEdge(kFloorCcw, { 25.f, 2.f }, south);
        CHECK(p.overEdge && Near(p.exitYd, 2.f, 1e-3f) && Near(p.landing.y, -4.f, 1e-3f));
        CHECK(Near(p.distance, 6.f, 1e-3f));
        p = PlanOverEdge(kFloorCcw, { 25.f, 10.f }, OutwardBearing(kFloorCcw, { 25.f, 10.f }));
        CHECK(p.overEdge && Near(p.exit.y, 0.f, 1e-3f) && Near(p.landing.y, -4.f, 1e-3f));
        CHECK(Near(p.distance, 14.f, 1e-3f));
        CHECK(!PointInPolygon(kFloorCcw, p.landing));
        p = PlanOverEdge(kFloorCcw, { 25.f, 10.f }, south, 6.f);
        CHECK(Near(p.landing.y, -6.f, 1e-3f));
        // Arm Sweep: thrown toward the far edge, wherever it stands across the width.
        p = PlanOverEdge(kFloorCcw, { 25.f, 3.f }, north);
        CHECK(p.overEdge && Near(p.landing.y, 28.f, 1e-3f) && Near(p.exitYd, 21.f, 1e-3f));
        // A start already off the floor keeps going.
        p = PlanOverEdge(kFloorCcw, { 25.f, -1.f }, south);
        CHECK(p.overEdge && p.exitYd == 0.f && Near(p.landing.y, -5.f, 1e-3f) && Near(p.distance, 4.f, 1e-3f));

        // A concave floor: a notch 10 yd wide is a drop of its own (beyond the edge is not floor), so the throw ends
        // in it, 4 yd past its near side.
        std::vector<Vec2> const notched{ { 0.f, 0.f }, { 30.f, 0.f }, { 30.f, 20.f }, { 20.f, 20.f }, { 20.f, 5.f },
            { 10.f, 5.f }, { 10.f, 20.f }, { 0.f, 20.f } };
        p = PlanOverEdge(notched, { 5.f, 10.f }, 0.f);
        CHECK(p.overEdge && Near(p.exit.x, 10.f, 1e-2f) && Near(p.landing.x, 14.f, 1e-2f));
        CHECK(!PointInPolygon(notched, p.landing));
        // A slit narrower than beyondYd: landing 4 yd on would be floor again, so the throw crosses it, re-enters,
        // and leaves for good at the far side.
        std::vector<Vec2> const slit{ { 0.f, 0.f }, { 30.f, 0.f }, { 30.f, 20.f }, { 12.f, 20.f }, { 12.f, 5.f },
            { 10.f, 5.f }, { 10.f, 20.f }, { 0.f, 20.f } };
        p = PlanOverEdge(slit, { 5.f, 10.f }, 0.f);
        CHECK(p.overEdge && Near(p.exit.x, 30.f, 1e-2f) && Near(p.landing.x, 34.f, 1e-2f));
        CHECK(!PointInPolygon(slit, p.landing));
        // The same slit with a 1 yd beyond: the landing fits in it.
        p = PlanOverEdge(slit, { 5.f, 10.f }, 0.f, 1.f);
        CHECK(Near(p.exit.x, 10.f, 1e-2f) && Near(p.landing.x, 11.f, 1e-2f));

        // Magma Fist's 10 yd knockback (SP S2 816): on the floor when it fits, past the edge (never on the rim) when
        // it does not.
        p = PlanKnockback(kFloorCcw, { 25.f, 12.f }, south, 10.f);
        CHECK(!p.overEdge && Near(p.landing.y, 2.f, 1e-3f) && Near(p.distance, 10.f, 1e-3f));
        p = PlanKnockback(kFloorCcw, { 25.f, 6.f }, south, 10.f);
        CHECK(p.overEdge && Near(p.landing.y, -4.f, 1e-3f) && Near(p.distance, 10.f, 1e-3f));
        p = PlanKnockback(kFloorCcw, { 25.f, 8.f }, south, 10.f);                  // would land 2 yd in: 4 past
        CHECK(p.overEdge && Near(p.landing.y, -4.f, 1e-3f) && Near(p.distance, 12.f, 1e-3f));
        p = PlanKnockback(kFloorCcw, { 25.f, 3.f }, south, 10.f);                  // the full 10 yd
        CHECK(p.overEdge && Near(p.landing.y, -7.f, 1e-3f) && Near(p.distance, 10.f, 1e-3f));
        p = PlanKnockback(kFloorCcw, { 25.f, 12.f }, south, 0.f);
        CHECK(!p.overEdge && p.distance == 0.f);

        // The jump: 0.8 s flights, never slower than 8 yd/s.
        CHECK(Near(EdgeJumpSpeedXY(10.f), 12.5f, 1e-4f));
        CHECK(Near(EdgeJumpSpeedXY(4.f), kEdgeMinSpeedXY, 1e-4f));
        CHECK(Near(EdgeJumpSpeedXY(10.f, 0), kEdgeMinSpeedXY, 1e-4f));
        CHECK(EdgeFlightMs(10.f, 12.5f) == 800 && EdgeFlightMs(4.f, 8.f) == 500 && EdgeFlightMs(4.f, 0.f) == 0);
    }

    void TestEdgeBands()
    {
        // The crumble (SP S2 909): the outer 4 yd along an edge, then the next 4 yd in.
        WallLine band = EdgeBand(kFloorCcw, 0, 0.f, 4.f);
        CHECK(Near(band.width, 4.f, 1e-5f) && Near(band.from.y, 2.f, 1e-4f) && Near(band.to.y, 2.f, 1e-4f));
        CHECK(Near(band.from.x, 0.f, 1e-4f) && Near(band.to.x, 50.f, 1e-4f));
        band = EdgeBand(kFloorCw, 3, 4.f, 8.f);                    // the same edge, the other winding
        CHECK(Near(band.width, 4.f, 1e-5f) && Near(band.from.y, 6.f, 1e-4f) && Near(band.from.x, 50.f, 1e-4f));
        band = EdgeBand(kFloorCcw, 1, 0.f, 2.f, 1.f);               // the east edge, 2 yd, ends stretched 1 yd
        CHECK(Near(band.from.x, 49.f, 1e-4f) && Near(band.from.y, -1.f, 1e-4f) && Near(band.to.y, 25.f, 1e-4f));
        CHECK(EdgeBand(kFloorCcw, 0, 4.f, 4.f).width == 0.f);
        CHECK(EdgeBand(std::vector<Vec2>{ { 0.f, 0.f }, { 1.f, 0.f } }, 0, 0.f, 4.f).width == 0.f);

        // Every point of a band is on the floor and is pushed past the edge it runs along.
        band = EdgeBand(kFloorCcw, 0, 0.f, 4.f);
        for (float y : { 0.5f, 2.f, 3.9f })
        {
            Vec2 const at{ 25.f, y };
            CHECK(PointInPolygon(kFloorCcw, at) && InsideWall(band, at));
            EdgePush const p = PlanOverEdge(kFloorCcw, at, OutwardBearing(kFloorCcw, at));
            CHECK(p.overEdge && !PointInPolygon(kFloorCcw, p.landing) && Near(p.landing.y, -4.f, 1e-3f));
        }
        CHECK(!InsideWall(band, { 25.f, 4.5f }));

        // All edges, or the listed ones (Lord of the Lake: the long edges only); empty steps are dropped.
        CHECK(EdgeBands(kFloorCcw, {}, 0.f, 4.f).size() == 4);
        std::vector<std::size_t> const longEdges{ 0, 2 };
        std::vector<WallLine> const two = EdgeBands(kFloorCcw, longEdges, 2.f, 4.f);
        CHECK(two.size() == 2 && Near(two[0].from.y, 3.f, 1e-4f) && Near(two[1].from.y, 21.f, 1e-4f));
        CHECK(EdgeBands(kFloorCcw, longEdges, 4.f, 2.f).empty());
    }

    PoolHit Hit(std::uint64_t attacker, PoolHitKind kind, std::uint64_t member, std::uint32_t amount, std::uint64_t ms)
    {
        PoolHit h;
        h.attacker = attacker;
        h.kind = kind;
        h.member = member;
        h.amount = amount;
        h.atMs = ms;
        return h;
    }

    // WP-KT-D2: the Seven's shared pool (handoff section 3.11 #4): the cleave-once rule, heals, the mirror, the
    // all-die tick.
    void TestHealthPool()
    {
        HealthPool pool(320000);
        CHECK(pool.Max() == 320000 && pool.Current() == 320000 && !pool.Emptied());
        CHECK(pool.Mirror(320000) == 320000 && pool.Mirror(2614) == 2614 && pool.Mirror(0) == 0);

        // A single hit comes off in full.
        HealthPool::Result r = pool.Damage(Hit(1, PoolHitKind::Spell, 100, 1000, 1000));
        CHECK(r.change == 1000 && !r.merged && !r.emptied && pool.Current() == 319000);

        // A cleave: the same attacker and kind on two other members in the same tick counts as its largest hit.
        r = pool.Damage(Hit(2, PoolHitKind::Spell, 100, 800, 2000));
        CHECK(r.change == 800 && !r.merged);
        r = pool.Damage(Hit(2, PoolHitKind::Spell, 101, 600, 2000));
        CHECK(r.change == 0 && r.merged);
        r = pool.Damage(Hit(2, PoolHitKind::Spell, 102, 900, 2000));
        CHECK(r.change == 100 && r.merged);             // 900 replaces 800 as the cast's top: +100
        CHECK(pool.Current() == 319000 - 900);

        // A missile cleave inside the cast window still merges; past it, a new cast.
        std::uint32_t const atStart = pool.Current();
        pool.Damage(Hit(3, PoolHitKind::Spell, 100, 500, 5000));
        r = pool.Damage(Hit(3, PoolHitKind::Spell, 101, 500, 5000 + kPoolCastWindowMs));
        CHECK(r.change == 0 && r.merged);
        r = pool.Damage(Hit(3, PoolHitKind::Spell, 102, 500, 5000 + kPoolCastWindowMs + 1));
        CHECK(r.change == 500 && !r.merged);
        CHECK(pool.Current() == atStart - 1000);

        // A second hit on a member the cast already hit is a new cast (two swings, two ticks).
        std::uint32_t const beforeSwings = pool.Current();
        pool.Damage(Hit(4, PoolHitKind::Melee, 100, 300, 6000));
        r = pool.Damage(Hit(4, PoolHitKind::Melee, 100, 300, 6000));
        CHECK(r.change == 300 && !r.merged);
        CHECK(pool.Current() == beforeSwings - 600);

        // Different attackers, or different kinds of one attacker, never merge.
        std::uint32_t const beforeTwo = pool.Current();
        pool.Damage(Hit(5, PoolHitKind::Spell, 100, 200, 7000));
        r = pool.Damage(Hit(6, PoolHitKind::Spell, 101, 200, 7000));
        CHECK(r.change == 200 && !r.merged);
        r = pool.Damage(Hit(5, PoolHitKind::Melee, 101, 200, 7000));
        CHECK(r.change == 200 && !r.merged);
        // Unknown attacker or kind Other: always in full.
        pool.Damage(Hit(0, PoolHitKind::Spell, 100, 50, 7000));
        r = pool.Damage(Hit(0, PoolHitKind::Spell, 101, 50, 7000));
        CHECK(r.change == 50 && !r.merged);
        pool.Damage(Hit(7, PoolHitKind::Other, 100, 50, 7000));
        r = pool.Damage(Hit(7, PoolHitKind::Other, 101, 50, 7000));
        CHECK(r.change == 50 && !r.merged);
        CHECK(pool.Current() == beforeTwo - 800);

        // DoTs: one tick only (an AoE DoT on two members merges; a tick 1 ms apart does not).
        std::uint32_t const beforeDots = pool.Current();
        pool.Damage(Hit(8, PoolHitKind::Periodic, 100, 400, 8000));
        r = pool.Damage(Hit(8, PoolHitKind::Periodic, 101, 400, 8000));
        CHECK(r.change == 0 && r.merged);
        r = pool.Damage(Hit(8, PoolHitKind::Periodic, 102, 400, 8001));
        CHECK(r.change == 400 && !r.merged);
        CHECK(pool.Current() == beforeDots - 800);

        // Old casts are pruned (the window plus 1 s).
        pool.Damage(Hit(9, PoolHitKind::Spell, 100, 1, 20000));
        CHECK(pool.OpenCasts() == 1);

        // Heals: into the pool, capped at the max, once per cast too.
        HealthPool heal(1000);
        heal.Damage(Hit(1, PoolHitKind::Spell, 100, 600, 0));
        r = heal.Heal(Hit(2, PoolHitKind::Heal, 100, 100, 10));
        CHECK(r.change == 100 && heal.Current() == 500);
        r = heal.Heal(Hit(2, PoolHitKind::Heal, 101, 100, 10));
        CHECK(r.change == 0 && r.merged && heal.Current() == 500);
        CHECK(heal.Restore(50) == 50 && heal.Current() == 550);
        CHECK(heal.RestorePct(5.f) == 50 && heal.Current() == 600);          // Vile Communion's 5%
        CHECK(heal.RestorePct(0.f) == 0);
        CHECK(heal.Restore(10000) == 400 && heal.Current() == 1000);         // capped
        r = heal.Heal(Hit(3, PoolHitKind::Heal, 100, 10, 20));
        CHECK(r.change == 0);

        // The mirror: each member's share of its own max health, rounded up, at least 1.
        HealthPool mirror(320000);
        mirror.Damage(Hit(1, PoolHitKind::Other, 100, 160000, 0));
        CHECK(mirror.Mirror(320000) == 160000);
        CHECK(mirror.Mirror(2614) == 1307);
        CHECK(Near(mirror.Pct(), 50.f, 1e-4f));
        mirror.Damage(Hit(1, PoolHitKind::Other, 100, 159999, 0));
        CHECK(mirror.Current() == 1 && mirror.Mirror(2614) == 1 && mirror.Mirror(320000) == 1);

        // The all-die tick: the emptying hit (overkill capped), then everything absorbed, then one death tick.
        HealthPool death(1000);
        CHECK(!death.TakeDeathTick());
        r = death.Damage(Hit(1, PoolHitKind::Spell, 100, 400, 0));
        CHECK(!r.emptied);
        r = death.Damage(Hit(2, PoolHitKind::Spell, 101, 5000, 0));
        CHECK(r.emptied && r.change == 600 && death.Current() == 0 && death.Emptied());
        CHECK(death.Mirror(2614) == 1);                 // held at 1 health until the tick
        r = death.Damage(Hit(3, PoolHitKind::Spell, 102, 100, 0));
        CHECK(r.change == 0 && !r.emptied);             // emptied once only
        CHECK(death.Heal(Hit(4, PoolHitKind::Heal, 100, 500, 0)).change == 0);
        CHECK(death.Restore(500) == 0 && death.Current() == 0);
        CHECK(death.TakeDeathTick());
        CHECK(!death.TakeDeathTick());                  // the tick fires once
        CHECK(death.DeathTaken());

        // R-2-FW MIN-1 / R-2-B MN-1: the death tick's killer: recorded, else a loot recipient, else a map player,
        // only then a self-kill (which finds no player: no credit, no bind).
        CHECK(ChoosePoolKiller(true, true, true) == PoolKiller::Recorded);
        CHECK(ChoosePoolKiller(true, false, false) == PoolKiller::Recorded);
        CHECK(ChoosePoolKiller(false, true, true) == PoolKiller::LootRecipient);
        CHECK(ChoosePoolKiller(false, false, true) == PoolKiller::MapPlayer);
        CHECK(ChoosePoolKiller(false, false, false) == PoolKiller::Self);

        // A cleave that empties the pool: the merged part is what counts (the top hit), emptied once.
        HealthPool edge(1000);
        edge.Damage(Hit(1, PoolHitKind::Other, 100, 500, 0));
        r = edge.Damage(Hit(2, PoolHitKind::Spell, 100, 300, 10));
        CHECK(r.change == 300 && !r.emptied);
        r = edge.Damage(Hit(2, PoolHitKind::Spell, 101, 700, 10));
        CHECK(r.change == 200 && r.merged && r.emptied);

        // Start: the next pull, full again with every latch cleared (0 keeps the max).
        death.Start();
        CHECK(death.Max() == 1000 && death.Current() == 1000 && !death.Emptied() && !death.DeathTaken());
        CHECK(death.OpenCasts() == 0);
        death.Start(450000);
        CHECK(death.Max() == 450000 && death.Current() == 450000);

        // No max: nothing happens.
        HealthPool none;
        CHECK(none.Damage(Hit(1, PoolHitKind::Spell, 100, 10, 0)).change == 0 && !none.Emptied());
        CHECK(none.Mirror(100) == 100);
    }

    // WP-KT-D2: Phalanx's Throw Out tally (handoff section 3.11 #5): the 10 s window, ties, exclusions. Pet credit is
    // the engine's (the hit is recorded under its player's id), so here a "pet" hit is a hit under its owner's id.
    void TestDamageTally()
    {
        DamageTally tally;
        CHECK(tally.WindowMs() == kTallyWindowMs);
        CHECK(!tally.Top(0));

        tally.Record(1, 500, 1000);
        tally.Record(2, 400, 2000);
        tally.Record(2, 300, 3000);         // player 2's pet: credited to 2
        tally.Record(3, 0, 3000);           // nothing
        tally.Record(0, 999, 3000);         // no one
        CHECK(tally.Size() == 3);
        CHECK(tally.Total(2, 3000) == 700 && tally.Total(1, 3000) == 500 && tally.Total(3, 3000) == 0);
        std::optional<TallyStanding> top = tally.Top(3000);
        CHECK(top && top->who == 2 && top->total == 700 && top->lastMs == 3000 && top->firstMs == 2000);

        // The window: a hit exactly 10 s old has left it.
        CHECK(tally.Total(1, 10999) == 500);
        CHECK(tally.Total(1, 11000) == 0);
        top = tally.Top(12000);
        CHECK(top && top->who == 2 && top->total == 300);
        CHECK(!tally.Top(13000));
        CHECK(tally.Size() == 0);

        // Ties: who reached the total first (the earlier newest hit).
        DamageTally ties;
        ties.Record(10, 300, 0);            // 10 reaches 300 at 0
        ties.Record(11, 200, 100);
        ties.Record(12, 300, 150);          // 12 reaches 300 at 150
        ties.Record(11, 100, 200);          // 11 reaches 300 at 200
        ties.Record(10, 0, 500);            // not a hit
        std::vector<TallyStanding> rank = ties.Ranking(600);
        CHECK(rank.size() == 3 && rank[0].who == 10 && rank[1].who == 12 && rank[2].who == 11);
        CHECK(rank[0].total == 300 && rank[1].total == 300 && rank[2].total == 300);
        // 20 reached 200 first (50); 21 and 22 both at 100: the earlier first hit (21, at 0) wins.
        DamageTally sameLast;
        sameLast.Record(21, 100, 0);
        sameLast.Record(20, 200, 50);
        sameLast.Record(21, 100, 100);
        sameLast.Record(20, 0, 100);
        sameLast.Record(22, 200, 100);
        rank = sameLast.Ranking(100);
        CHECK(rank.size() == 3 && rank[0].who == 20 && rank[1].who == 21 && rank[2].who == 22);

        // Exclusions (the victim, the last one thrown) and a predicate (alive, on the map).
        std::vector<std::uint64_t> const exclude{ 10 };
        top = ties.Top(600, exclude);
        CHECK(top && top->who == 12);
        std::vector<std::uint64_t> const all{ 10, 11, 12 };
        CHECK(!ties.Top(600, all));
        top = ties.TopIf(600, [](std::uint64_t who) { return who == 11; });
        CHECK(top && top->who == 11 && top->total == 300);

        // A short window and Clear.
        DamageTally shortWindow(2000);
        shortWindow.Record(1, 100, 0);
        shortWindow.Record(2, 50, 1500);
        CHECK(shortWindow.Top(1999)->who == 1);
        CHECK(shortWindow.Top(2000)->who == 2);
        shortWindow.Clear();
        CHECK(shortWindow.Size() == 0 && !shortWindow.Top(2000));
    }
    // ----------------------------------------------------------------------------------------------------------------
    // Scarlet Monastery WP-KT-SM: DungeonKitZoneLogic.h and DungeonKitWingLogic.h
    // ----------------------------------------------------------------------------------------------------------------

    bool Approx(float a, float b, float eps = 1e-3f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestGrowthPlan()
    {
        // Ironspine's heroic Grave Rot: 7 to 10 yd over 30 s, a step every 10 s.
        GrowthPlan const rot{ 7.f, 10.f, 30000, 10000 };
        CHECK(rot.Timed() && rot.StepCount() == 3);
        CHECK(Approx(rot.RadiusAt(0), 7.f) && Approx(rot.RadiusAt(9999), 7.f));
        CHECK(Approx(rot.RadiusAt(10000), 8.f) && Approx(rot.RadiusAt(20000), 9.f));
        CHECK(Approx(rot.RadiusAt(30000), 10.f) && Approx(rot.RadiusAt(600000), 10.f));
        CHECK(rot.NextStepInMs(0) == 10000u && rot.NextStepInMs(12500) == 7500u);
        CHECK(!rot.NextStepInMs(30000));

        // A step that does not divide the time: 6 to 12 over 25 s at 10 s = 3 steps (ceil), 2 yd each.
        GrowthPlan const odd{ 6.f, 12.f, 25000, 10000 };
        CHECK(odd.StepCount() == 3 && Approx(odd.RadiusAt(10000), 8.f) && Approx(odd.RadiusAt(30000), 12.f));

        // Not timed: by hand only (the mist), or no change.
        GrowthPlan const byHand{ 6.f, 6.f, 0, 0 };
        CHECK(!byHand.Timed() && byHand.StepCount() == 0 && Approx(byHand.RadiusAt(99999), 6.f));
        CHECK(!byHand.NextStepInMs(0));
        GrowthPlan const noStep{ 6.f, 9.f, 30000, 0 };
        CHECK(!noStep.Timed() && Approx(noStep.RadiusAt(30000), 6.f));

        // A shrinking zone works the same way.
        GrowthPlan const shrink{ 10.f, 4.f, 6000, 2000 };
        CHECK(Approx(shrink.RadiusAt(2000), 8.f) && Approx(shrink.RadiusAt(6000), 4.f));
    }

    void TestNearestRung()
    {
        std::array<float, 4> const rot{ { 7.f, 8.f, 9.f, 10.f } };
        CHECK(NearestRung(rot, 7.f) == 0u && NearestRung(rot, 9.f) == 2u && NearestRung(rot, 14.f) == 3u);
        CHECK(NearestRung(rot, 7.4f) == 0u && NearestRung(rot, 7.6f) == 1u);
        CHECK(NearestRung(rot, 7.5f) == 1u);        // a tie goes to the larger rung
        CHECK(NearestRung(rot, 2.f) == 0u);
        std::array<float, 3> const mist{ { 6.f, 9.f, 12.f } };
        CHECK(NearestRung(mist, 15.f) == 2u);       // past the ladder: the last rung
        CHECK(!NearestRung(std::span<float const>(), 6.f));
    }

    void TestBeamClock()
    {
        // Herod's beacon: two beams opposite, 30 degrees a step.
        BeamClock clock(0.f, 30.f, 2);
        CHECK(clock.Count() == 2 && clock.Direction() == 1 && clock.Steps() == 0);
        CHECK(Approx(clock.BearingOf(0), 0.f) && Approx(clock.BearingOf(1), kPi));
        CHECK(Approx(clock.NextBearingOf(0), kPi / 6.f));
        clock.Step();
        CHECK(Approx(clock.BearingOf(0), kPi / 6.f) && Approx(clock.BearingOf(1), kPi + kPi / 6.f));
        CHECK(clock.Steps() == 1);
        // A full turn: 12 steps back to the start (about 18 s at 1.5 s).
        for (int i = 0; i < 11; ++i)
            clock.Step();
        CHECK(clock.Steps() == 12 && (Approx(clock.Bearing(), 0.f, 1e-3f) || Approx(clock.Bearing(), kTwoPi, 1e-3f)));
        // Flip: the next step goes back the other way and wraps below 0.
        clock.Flip();
        CHECK(clock.Direction() == -1);
        clock.Step();
        CHECK(Approx(clock.Bearing(), kTwoPi - kPi / 6.f, 1e-3f));
        clock.Flip();
        clock.Step();
        CHECK(Approx(clock.Bearing(), 0.f, 1e-3f) || Approx(clock.Bearing(), kTwoPi, 1e-3f));

        // Three beams 120 apart, clockwise; a zero count is held at one beam.
        BeamClock three(kPi / 2.f, 45.f, 3, -1);
        CHECK(Approx(three.BearingOf(1), kPi / 2.f + kTwoPi / 3.f) && three.Direction() == -1);
        CHECK(Approx(three.BearingOf(3), kPi / 2.f));
        BeamClock none(0.f, 30.f, 0);
        CHECK(none.Count() == 1);
        CHECK(Approx(BeamClock::Wrap(-kPi / 2.f), 1.5f * kPi) && Approx(BeamClock::Wrap(5.f * kPi), kPi, 1e-3f));
    }

    void TestBeamSegment()
    {
        Vec2 const axe{ 1961.2f, -431.8f };
        // 3 yd off the axe, 10 yd long, east.
        std::optional<BeamLane> lane = BeamSegment(axe, 0.f, 3.f, 10.f);
        CHECK(lane && Approx(lane->from.x, axe.x + 3.f) && Approx(lane->to.x, axe.x + 13.f));
        CHECK(lane && Approx(lane->length, 10.f));
        CHECK(lane && !lane->clipped);
        // The pit's edge 11.7 yd out: stops 0.5 yd short.
        lane = BeamSegment(axe, kPi / 2.f, 3.f, 14.f, 11.7f);
        CHECK(lane && lane->clipped && Approx(lane->length, 8.2f) && Approx(lane->to.y, axe.y + 11.2f));
        // A far wall changes nothing.
        lane = BeamSegment(axe, 0.f, 3.f, 10.f, 30.f);
        CHECK(lane && !lane->clipped && Approx(lane->length, 10.f));
        // A wall inside the inner offset: no lane.
        CHECK(!BeamSegment(axe, 0.f, 3.f, 10.f, 3.2f));

        // Through the arena's own ray (the pit as a circle of 11.7 yd).
        Arena const pit(ArenaRegion::Circle(axe, 11.7f, 0.f, 12.f));
        std::optional<float> wall = pit.RayToEdge(axe, 6.4f, kPi);
        CHECK(wall && Approx(*wall, 11.7f, 0.01f));
        lane = BeamSegment(axe, kPi, 3.f, 14.f, wall);
        CHECK(lane && lane->clipped && Approx(lane->length, 8.2f, 0.01f));
    }

    void TestTravelers()
    {
        TravelerFacts user;
        user.isUser = true;
        CHECK(JudgeTraveler(user) == TravelVerdict::Go);
        user.inCombat = true;
        CHECK(JudgeTraveler(user) == TravelVerdict::InCombat);
        CHECK(JudgeTraveler(user, kPortalEscortYd, true) == TravelVerdict::Go);
        user.inCombat = false;
        user.distYd = 500.f;                // the user's own distance never counts
        CHECK(JudgeTraveler(user) == TravelVerdict::Go);
        user.alive = false;
        CHECK(JudgeTraveler(user) == TravelVerdict::Dead);

        TravelerFacts escort;
        escort.distYd = 19.9f;
        CHECK(JudgeTraveler(escort) == TravelVerdict::Go);
        escort.distYd = 20.f;
        CHECK(JudgeTraveler(escort) == TravelVerdict::Go);  // within 20 yd: 20 counts
        escort.distYd = 20.1f;
        CHECK(JudgeTraveler(escort) == TravelVerdict::TooFar);
        escort.distYd = 5.f;
        escort.inCombat = true;
        CHECK(JudgeTraveler(escort, kPortalEscortYd, true) == TravelVerdict::InCombat);    // escorts never in combat
        escort.inCombat = false;
        escort.busy = true;
        CHECK(JudgeTraveler(escort) == TravelVerdict::Busy);
        escort.busy = false;
        escort.alive = false;
        CHECK(JudgeTraveler(escort) == TravelVerdict::Dead);
        escort.sameMap = false;
        CHECK(JudgeTraveler(escort) == TravelVerdict::OtherMap);
        CHECK(std::string(TravelVerdictName(TravelVerdict::TooFar)) == "too-far");
        CHECK(kPortalEscortYd == 20.f);

        // Trigger clearance (section 7 #15: 8 yd from the wing exits).
        std::array<Vec2, 2> const exits{ { { 0.f, 0.f }, { 30.f, 0.f } } };
        CHECK(Approx(NearestTrigger({ 10.f, 0.f }, exits), 10.f));
        CHECK(ClearOfTriggers({ 10.f, 0.f }, exits, 8.f));
        CHECK(!ClearOfTriggers({ 25.f, 0.f }, exits, 8.f));
        CHECK(ClearOfTriggers({ 22.f, 0.f }, exits, 8.f));      // exactly 8 yd is clear
        CHECK(ClearOfTriggers({ 0.f, 0.f }, std::span<Vec2 const>(), 8.f));
    }

    void TestSealClock()
    {
        SealClock seal;
        CHECK(seal.IsOpen() && !seal.Update(5000));
        CHECK(!seal.Release());                 // nothing to undo

        // Section 7 #22: closes 3 s after the pull, once.
        seal.Engage(kSealDelayMs);
        CHECK(seal.IsClosing() && seal.LeftMs() == 3000);
        CHECK(!seal.Update(1000) && !seal.Update(1999));
        CHECK(seal.Update(1) && seal.IsSealed());
        CHECK(!seal.Update(1000) && seal.IsSealed());
        seal.Engage(kSealDelayMs);              // a re-engage changes nothing
        CHECK(seal.IsSealed());
        CHECK(seal.Release() && seal.IsOpen());

        // A wipe before the close: the pending close is undone.
        seal.Engage(3000);
        CHECK(!seal.Update(2000) && seal.Release() && seal.IsOpen() && !seal.Update(5000));
        // A re-engage while closing keeps the first delay.
        seal.Engage(3000);
        seal.Update(2000);
        seal.Engage(3000);
        CHECK(seal.LeftMs() == 1000 && seal.Update(1000));
        // No delay: sealed at the next update.
        SealClock now;
        now.Engage(0);
        CHECK(now.Update(0) && now.IsSealed());
    }

    void TestStragglers()
    {
        StragglerFacts f;
        f.distYd = 30.f;
        CHECK(IsStraggler(f));
        f.distYd = 60.f;
        CHECK(IsStraggler(f));                  // within 60 yd: 60 counts
        f.distYd = 60.5f;
        CHECK(!IsStraggler(f));
        CHECK(IsStraggler(f, 70.f));
        f.distYd = 10.f;
        f.inArena = true;
        CHECK(!IsStraggler(f));
        f.inArena = false;
        f.alive = false;
        CHECK(!IsStraggler(f));
        f.alive = true;
        f.sameWing = false;
        CHECK(!IsStraggler(f));
        f.sameWing = true;
        f.busy = true;
        CHECK(!IsStraggler(f));
        f.busy = false;
        f.gameMaster = true;
        CHECK(!IsStraggler(f));
        CHECK(kSealPullInYd == 60.f && kSealDelayMs == 3000u);
    }

    void TestCreditLatch()
    {
        // The council: Azshir and the Fallen Champion, either order, credit once at the second death.
        std::uint64_t const azshir = 6490, champion = 6488;
        CreditLatch council({ azshir, champion });
        CHECK(!council.MarkDead(champion) && council.IsDead(champion) && !council.Fired());
        CHECK(!council.MarkDead(champion));     // a second death of one changes nothing
        CHECK(!council.MarkDead(1234));         // a stranger changes nothing
        CHECK(council.DeadCount() == 1);
        CHECK(council.MarkDead(azshir) && council.Fired());
        CHECK(!council.MarkDead(azshir) && !council.MarkDead(champion));   // once only

        // A wipe forgets the deaths; a reload of a DONE encounter restores without firing.
        council.Reset();
        CHECK(!council.Fired() && council.DeadCount() == 0);
        CHECK(!council.MarkDead(azshir) && council.MarkDead(champion));
        CreditLatch reloaded({ azshir, champion });
        reloaded.Restore();
        CHECK(reloaded.Fired() && !reloaded.MarkDead(azshir));

        // One key: the first death fires. No keys: never.
        CreditLatch single({ 7 });
        CHECK(single.MarkDead(7));
        CreditLatch empty;
        CHECK(!empty.MarkDead(7) && !empty.Fired());
        // The same entry twice (two of one kind): both deaths are needed.
        CreditLatch pair({ 5, 5 });
        CHECK(!pair.MarkDead(5) && pair.MarkDead(5));
    }

    void TestWardRule()
    {
        // Blood Pact: 20% per living risen, up to 80%.
        WardRule const pact{ 20.f, 80.f };
        CHECK(Approx(pact.ReductionPct(0), 0.f) && Approx(pact.ReductionPct(2), 40.f));
        CHECK(Approx(pact.ReductionPct(4), 80.f));
        CHECK(Approx(pact.ReductionPct(9), 80.f));
        CHECK(pact.Stacks(0) == 0 && pact.Stacks(3) == 3 && pact.Stacks(9) == 4);
        CHECK(pact.Scale(1000, 0) == 1000 && pact.Scale(1000, 2) == 600 && pact.Scale(1000, 4) == 200);

        // Reader's Ward: 25% per open book, normal at most 50, heroic 75.
        WardRule const normal{ 25.f, 50.f }, heroic{ 25.f, 75.f };
        CHECK(normal.Stacks(3) == 2 && Approx(normal.ReductionPct(3), 50.f));
        CHECK(heroic.Stacks(3) == 3 && Approx(heroic.ReductionPct(4), 75.f) && heroic.Stacks(4) == 3);

        // Inquisitor's Ward: 50% while he lives.
        WardRule const inquisitor{ 50.f, 50.f };
        CHECK(inquisitor.Stacks(1) == 1 && inquisitor.Scale(999, 1) == 500);

        // Never full immunity: the cap is held at 95; a hit stays at least 1.
        WardRule const greedy{ 50.f, 100.f };
        CHECK(Approx(greedy.ReductionPct(3), 95.f) && greedy.Stacks(3) == 1);
        CHECK(greedy.Scale(1, 3) == 1 && greedy.Scale(0, 3) == 0);
        WardRule const off{ 0.f, 50.f };
        CHECK(off.Stacks(5) == 0 && Approx(off.ReductionPct(5), 0.f) && off.Scale(100, 5) == 100);
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
    TestPerStackAmount();
    TestFlexRules();
    TestChaseClock();
    TestCrawlClock();
    TestFallCatch();
    TestDeathSpots();
    TestHeldBody();
    TestEdgePush();
    TestEdgeBands();
    TestHealthPool();
    TestDamageTally();
    TestGrowthPlan();
    TestNearestRung();
    TestBeamClock();
    TestBeamSegment();
    TestTravelers();
    TestSealClock();
    TestStragglers();
    TestCreditLatch();
    TestWardRule();
    return Report("dungeon_kit_test");
}
