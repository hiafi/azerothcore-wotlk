// Host tests for OmokkLogic.h (B1: Highlord Omokk): the slice and the arena, the band and the shove, Haymaker's line,
// Pelting's hold-off, the crowd's ledger, the bridge's landings, lanes and throws, the Pit Drop line.
#include "OmokkLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <set>
#include <utility>
#include <vector>

using namespace BlackrockSpireRework;
using namespace BrsOmokk;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    float Dist(Vec2 a, Vec2 b)
    {
        return std::sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));
    }

    // The 2D distance from `p` to the segment a-b.
    float SegDist(Vec2 a, Vec2 b, Vec2 p)
    {
        return DungeonKit::SegmentDistance(a, b, p);
    }

    bool InHallFloor(Vec2 p)
    {
        return p.x >= -26.8f && p.x <= -14.8f && p.y >= -358.8f && p.y <= -294.8f;
    }

    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210020 && kSpellSlice.last == 210059);
        for (std::uint32_t id : { std::uint32_t(SPELL_OM_CROWD_SHOVE), std::uint32_t(SPELL_OM_HAYMAKER),
            std::uint32_t(SPELL_OM_BOTTLE_LAST), std::uint32_t(SPELL_OM_OGRE_MOJO), std::uint32_t(SPELL_OM_PIT_DROP) })
            CHECK(kSpellSlice.Contains(id));
        CHECK(SPELL_OM_CROWD_SHOVE == 210020 && SPELL_OM_PIT_DROP == 210042);
        CHECK(kBottleCount == 6);
        // He spawns kOmokkSpawn, inside his arena; so are the bridge and its landings.
        CHECK(OmokkArena().Contains(kOmokkSpawn.XY(), kOmokkSpawn.z));
        CHECK(ArenaFor(BOSS_OMOKK).Contains(kOmokkSpawn.XY(), kOmokkSpawn.z));
        CHECK(OmokkArena().Contains(kOmokkShowdownLanding.XY(), kOmokkShowdownLanding.z));
        for (Point3 const& l : kOmokkLandings)
            CHECK(OmokkArena().Contains(l.XY(), l.z));
        CHECK(OmokkArena().Contains(kOmokkHaulUpWest.XY(), kOmokkHaulUpWest.z));
        CHECK(OmokkArena().Contains(kOmokkHaulUpEast.XY(), kOmokkHaulUpEast.z));
        // Texts 0-7 (kTextRanges), none stock.
        CHECK(kTextRanges[0].entry == NPC_OMOKK && kTextRanges[0].last == SAY_OM_DEATH);
        CHECK(EMOTE_OM_HAYMAKER == 1 && SAY_OM_TO_THE_BRIDGE == 5 && EMOTE_OM_MOJO == 6);
        // The crowd's entries.
        CHECK(NPC_BRS_BRAWL_FAN == 300700 && NPC_BRS_BRAWLER == 300701 && NPC_BRS_MOJO_MYSTIC == 300702);
    }

    void TestBand()
    {
        // The pile strip runs along the hall's south edge (x -26.8), the alcove strips along the north wall (x -14.8),
        // every strip 2 yd wide and long enough to draw (the line ladder takes aspect 1-64).
        for (Strip const& s : kHallBand)
        {
            float const len = Dist(s.from, s.to);
            CHECK(len >= 8.f);
            CHECK(len / kBandWidth <= 64.f);
        }
        CHECK(Near(kHallBand[0].from.x, -26.f) && Near(kHallBand[0].to.x, -26.f));
        CHECK(Dist(kHallBand[0].from, kHallBand[0].to) >= 55.f);
        // Half the strip is on the floor's edge: a player 1 yd in from the wall is in it, 3 yd in is not.
        CHECK(SegDist(kHallBand[0].from, kHallBand[0].to, { -25.8f, -320.f }) <= kBandWidth / 2.f);
        CHECK(SegDist(kHallBand[0].from, kHallBand[0].to, { -23.8f, -320.f }) > kBandWidth / 2.f);
        CHECK(SegDist(kHallBand[1].from, kHallBand[1].to, { -15.f, -320.f }) <= kBandWidth / 2.f);
        // He spawns clear of every strip (his tank stands near him at the pull).
        for (Strip const& s : kHallBand)
            CHECK(SegDist(s.from, s.to, kOmokkSpawn.XY()) > 3.f);
        // The ring left between the strips is about 9 yd wide (12 yd floor less the two half strips).
        float const ring = (kHallBand[1].from.x - kBandWidth / 2.f) - (kHallBand[0].from.x + kBandWidth / 2.f);
        CHECK(ring >= 8.5f && ring <= 10.5f);
        // The bridge strips: the haul-up spots stay clear of them, and players landing do too.
        for (Strip const& s : kBridgeBand)
        {
            CHECK(SegDist(s.from, s.to, kOmokkHaulUpWest.XY()) > kBandWidth / 2.f + 0.5f);
            CHECK(SegDist(s.from, s.to, kOmokkHaulUpEast.XY()) > kBandWidth / 2.f + 0.5f);
            for (Point3 const& l : kOmokkLandings)
                CHECK(SegDist(s.from, s.to, l.XY()) > kBandWidth / 2.f + 2.f);
            CHECK(SegDist(s.from, s.to, kOmokkShowdownLanding.XY()) > 10.f);
        }
        CHECK(kCrowdShovePct(false) == 25.f && kCrowdShovePct(true) == 35.f);
    }

    void TestPileAndShove()
    {
        // R-1-A m1: the shove's lockout aura is Omokk's, and it outlasts the band's next tick (one shove, one hit).
        CHECK(SPELL_OM_SHOVED == 210045 && SPELL_OM_SHOVED <= kSpellSlice.last);
        CHECK(kShoveLockoutMs >= 3 * kBandTickMs);
        // On the pile: south of the strip and up off the floor.
        CHECK(OnThePile({ -32.f, -320.f }, 37.f));
        CHECK(!OnThePile({ -32.f, -320.f }, kHallFloorZ));        // the floor at the pile's foot
        CHECK(!OnThePile({ -20.f, -320.f }, 37.f));               // the hall
        CHECK(!OnThePile(kOmokkSpawn.XY(), kOmokkSpawn.z));
        // The ledge's terrace pair stands outside the pile check? They are trash at x -47/-52 (outside kPileMinX).
        CHECK(!OnThePile({ -52.41f, -306.9f }, 43.34f));
        // A shove throws toward the ring's middle line: from the pile north, from an alcove south.
        Vec2 const fromPile{ -27.f, -320.f };
        Vec2 const t = HallShoveToward(fromPile);
        CHECK(Near(t.x, kRingMidX) && Near(t.y, -320.f));
        Vec2 const src = KnockSourceToward(fromPile, t);
        CHECK(src.x < fromPile.x);                                  // pushed away from a point south of it
        Vec2 const fromAlcove{ -14.f, -315.f };
        CHECK(KnockSourceToward(fromAlcove, HallShoveToward(fromAlcove)).x > fromAlcove.x);
        // The doorway's strip throws west, back into the hall (the middle line ends at y -352).
        Vec2 const fromDoor{ -20.f, -357.f };
        Vec2 const td = HallShoveToward(fromDoor);
        CHECK(Near(td.y, kRingMidYMin));
        CHECK(KnockSourceToward(fromDoor, td).y < fromDoor.y);
        // 8 yd lands inside the hall's floor from any strip.
        for (Strip const& s : kHallBand)
        {
            Vec2 const mid{ (s.from.x + s.to.x) / 2.f, (s.from.y + s.to.y) / 2.f };
            Vec2 const to = HallShoveToward(mid);
            float const d = Dist(mid, to);
            Vec2 const land = d > 0.01f ? Vec2{ mid.x + (to.x - mid.x) / d * kCrowdShoveKnockYd,
                mid.y + (to.y - mid.y) / d * kCrowdShoveKnockYd } : mid;
            CHECK(InHallFloor(land));
        }
    }

    void TestKnockbacks()
    {
        for (float d : { 8.f, 15.f, 20.f })
            for (float vz : { 6.f, 7.f, 8.f })
                CHECK(Near(KnockbackDistance(KnockbackSpeedXY(d, vz), vz), d, 0.01f));
        CHECK(KnockbackSpeedXY(10.f, 0.f) == 0.f);
        CHECK(Near(KnockbackSpeedXY(kCrowdShoveKnockYd, kCrowdShoveSpeedZ), 12.86f, 0.05f));
        // The source is exactly 1 yd behind the unit, away from the target.
        Vec2 const s = KnockSourceToward({ 0.f, 0.f }, { 10.f, 0.f });
        CHECK(Near(s.x, -1.f) && Near(s.y, 0.f));
        Vec2 const same = KnockSourceToward({ 3.f, 4.f }, { 3.f, 4.f });
        CHECK(Near(Dist(same, { 3.f, 4.f }), 1.f));
    }

    void TestHaymaker()
    {
        Vec2 const from{ -22.8f, -300.7f };
        Vec2 const end = HaymakerEnd(from, { -20.f, -320.f }, 0.f);
        CHECK(Near(Dist(from, end), kHaymakerLength, 0.01f));
        // Aimed at the target's spot: the target sits on the line.
        CHECK(SegDist(from, end, { -20.f, -320.f }) < 0.01f);
        // A target on his spot: straight ahead along his facing.
        Vec2 const ahead = HaymakerEnd(from, from, 0.f);
        CHECK(Near(ahead.x, from.x + kHaymakerLength) && Near(ahead.y, from.y));
        CHECK(kHaymakerPct(false) == 40.f && kHaymakerPct(true) == 50.f);
        CHECK(kHaymakerTargets.At(5) == 1 && kHaymakerTargets.At(6) == 2 && kHaymakerTargets.At(10) == 2);
        // The drill (blackrock-spire-followups row 0): 5 x 30 yd, 2.5 s, the follow-up 1.5 s, tag 2.
        CHECK(kHaymakerWidth == 5.f && kHaymakerCastMs == 2500 && kHaymakerTwoMs == 1500);
        CHECK(TAG_OM_HAYMAKER_TWO == 2);
        // Into the band on top of it: 65% normal, 85% heroic (the build spec's "survivable at full").
        CHECK(kHaymakerPct(false) + kCrowdShovePct(false) == 65.f);
        CHECK(kHaymakerPct(true) + kCrowdShovePct(true) == 85.f);
    }

    void TestPelting()
    {
        CHECK(PeltingTargets(5, false) == 2 && PeltingTargets(6, false) == 4);
        CHECK(PeltingTargets(5, true) == 3 && PeltingTargets(10, true) == 6);
        CHECK(kPeltingEveryMs(false) == 12000 && kPeltingEveryMs(true) == 10000);
        CHECK(kPeltingPct(false) == 25.f && kPeltingPct(true) == 30.f);
        // Bottles leave so they land with the circle.
        CHECK(BottleLaunchDelayMs(0.f) == kPeltingFlightMs);
        CHECK(BottleLaunchDelayMs(10.f) == 1000);
        CHECK(BottleLaunchDelayMs(30.f) == 0);
        // No windows: at once.
        CHECK(FirstClearStart(6000, 2000, {}) == 6000);
        // A Haymaker registered at 10 s (normal: punch at 12.5 s, window to 13.5 s): a volley due at 9 s would land at
        // 11 s, inside it, so it waits to land at 13.501 s.
        std::vector<Window> w{ { 10000, 13500 } };
        CHECK(FirstClearStart(9000, 2000, w) == 11501);
        CHECK(FirstClearStart(7000, 2000, w) == 7000);              // lands at 9 s, before the line is down
        CHECK(FirstClearStart(8000, 2000, w) == 11501);             // lands at 10 s, the line's first instant
        CHECK(FirstClearStart(12000, 2000, w) == 12000);            // lands at 14 s, after it
        // Two windows back to back: past both.
        std::vector<Window> two{ { 10000, 13500 }, { 13000, 18000 } };
        std::uint64_t const s = FirstClearStart(9000, 2000, two);
        CHECK(s == 16001);
        for (Window const& x : two)
            CHECK(!(s + 2000 >= x.from && s + 2000 <= x.to));
        // The real cadence: a heroic fight never lands a volley on a line, over 10 minutes.
        std::uint64_t nextHay = kHaymakerFirstMs;
        std::uint64_t nextPelt = kPeltingFirstMs;
        std::vector<Window> past;
        std::uint64_t const span = kHaymakerCastMs + kHaymakerTwoMs + kPeltingAfterPunchMs;
        int volleys = 0;
        for (std::uint64_t t = 0; t < 600000; t += 100)
        {
            if (t >= nextHay)
            {
                past.push_back({ t, t + span });
                nextHay = t + kHaymakerEveryMs;
            }
            if (t >= nextPelt)
            {
                std::vector<Window> ws;
                if (!past.empty())
                    ws.push_back(past.back());
                ws.push_back({ nextHay, nextHay + span });
                std::uint64_t const start = FirstClearStart(t, kPeltingFlightMs, ws);
                if (start > t)
                    nextPelt = start;
                else
                {
                    ++volleys;
                    std::uint64_t const landing = t + kPeltingFlightMs;
                    for (Window const& x : past)
                        CHECK(!(landing >= x.from && landing <= x.to));
                    if (!(landing < nextHay || landing > nextHay + span))
                        CHECK(false);
                    nextPelt = t + kPeltingEveryMs(true);
                }
            }
        }
        // 60 at a free 10 s cadence; the holds (5 s of every 15 s heroic) leave about 41.
        CHECK(volleys >= 38 && volleys <= 60);
    }

    void TestCrowdBook()
    {
        CrowdBook b;
        CHECK(b.Roar() == 0 && b.Booed() == 0);
        // A clean group: booed every 30 s, the yell at the third, nothing more after the cap.
        JudgeResult r = b.Judge();
        CHECK(r.verdict == Verdict::Booed && r.booed == 1 && r.booedAdded && !r.yell && r.roar == 0);
        r = b.Judge();
        CHECK(r.booed == 2 && !r.yell);
        r = b.Judge();
        CHECK(r.booed == 3 && r.yell);
        r = b.Judge();
        CHECK(r.verdict == Verdict::Booed && r.booed == 3 && !r.booedAdded && !r.yell);
        // "A clean group reaches 3 Booed stacks by 1:30".
        CHECK(3 * kJudgeEveryMs == 90000);
        // Feeding: one stack each, capped at 5; the judge cheers and keeps them.
        CrowdBook f;
        for (int i = 0; i < 7; ++i)
            f.Feed();
        CHECK(f.Roar() == kRoarMaxStacks);
        CHECK(f.FeedsThisWindow() == 7);
        r = f.Judge();
        CHECK(r.verdict == Verdict::Cheered && r.roar == 5 && r.booed == 0);
        CHECK(f.FeedsThisWindow() == 0);
        // The next window clean: one Roar off, one Booed on.
        r = f.Judge();
        CHECK(r.verdict == Verdict::Booed && r.roar == 4 && r.booed == 1);
        // The Mojo's stacks are not a feed.
        CrowdBook m;
        CHECK(m.Grant(kMojoRoarStacks) == 2);
        CHECK(m.FeedsThisWindow() == 0);
        CHECK(m.Grant(kMojoRoarStacks) == 4 && m.Grant(kMojoRoarStacks) == 5);
        r = m.Judge();
        CHECK(r.verdict == Verdict::Booed && r.roar == 4);
        m.Reset();
        CHECK(m.Roar() == 0 && m.Booed() == 0 && m.FeedsThisWindow() == 0);
        // The cap is about the stock Frenzy (+50% damage).
        CHECK(kRoarMaxStacks * kRoarDamagePct == kMojoFrenzyDamagePct);
        CHECK(kBooedMaxStacks * kBooedTakenPct == 30);
    }

    void TestMojo()
    {
        CHECK(kMojoTargets.At(5) == 1 && kMojoTargets.At(6) == 2);
        CHECK(kMojoFirstMs == 20000 && kMojoEveryMs == 25000 && kMojoCastMs == 3000);
        CHECK(kMojoMysticHealth == 12000);
        CHECK(DungeonKit::Flex::HealthAt(10, kMojoMysticHealth) == 27000);
        // Every step-out spot is within the chant's range of anywhere he stands (the hall, the bridge).
        for (MysticPost const& p : kHallMysticPosts)
        {
            CHECK(InHallFloor(p.stepOut.XY()));
            CHECK(Dist(p.stepOut.XY(), kOmokkSpawn.XY()) < kMojoRangeYd);
            CHECK(Dist(p.stepOut.XY(), { -20.8f, -355.f }) < kMojoRangeYd);
        }
        for (MysticPost const& p : kBridgeMysticPosts)
        {
            CHECK(OmokkArena().Contains(p.stepOut.XY(), p.stepOut.z));
            CHECK(Dist(p.stepOut.XY(), kOmokkShowdownLanding.XY()) < kMojoRangeYd);
        }
    }

    void TestLandings()
    {
        CHECK(LandingCount(5) == 5 && LandingCount(4) == 5 && LandingCount(6) == 7 && LandingCount(10) == 7);
        // His victim lands at the span's north end; the others fill the rest, then share with an offset.
        CHECK(LandingFor(0, 5).spot == kLandingVictim && LandingFor(0, 5).yOffset == 0.f);
        std::set<int> used;
        for (std::size_t i = 0; i < 5; ++i)
        {
            Landing const l = LandingFor(i, 5);
            CHECK(l.yOffset == 0.f);
            used.insert(l.spot);
        }
        CHECK(used.size() == 5);
        std::set<std::pair<int, float>> seen;
        for (std::size_t i = 0; i < 20; ++i)
        {
            Landing const l = LandingFor(i, 7);
            CHECK(l.spot < 7);
            CHECK(seen.insert({ l.spot, l.yOffset }).second);       // nobody lands on someone else
        }
        CHECK(LandingFor(7, 7).yOffset != 0.f);
        // Every landing is on the deck, clear of the edge, and on the bridge's band side of nothing.
        for (Point3 const& l : kOmokkLandings)
        {
            Extent const e = BridgeExtentAt(l.y);
            CHECK(l.x > e.minX + 1.5f && l.x < e.maxX - 1.5f);
        }
        Extent const mid = BridgeExtentAt(kOmokkShowdownLanding.y);
        CHECK(kOmokkShowdownLanding.x > mid.minX && kOmokkShowdownLanding.x < mid.maxX);
        // The trip's speed: 2 s for the distance, never under 8 yd/s.
        CHECK(Near(TripSpeedXY(100.f, 2000), 50.f));
        CHECK(TripSpeedXY(4.f, 2000) == 8.f);
        CHECK(kBridgeOgres.size() == 4);
        for (StepAside const& s : kBridgeOgres)
            CHECK(s.spawnId == 43519 || s.spawnId == 43520 || s.spawnId == 43506 || s.spawnId == 43523);
    }

    void TestBridgeMechanics()
    {
        // Lanes start at the doors and run 20 yd toward the target.
        Vec2 const t{ -37.5f, -420.f };
        Vec2 const e = BullRushEnd(kWestDoor, t);
        CHECK(Near(Dist(kWestDoor, e), kBullRushLength, 0.01f));
        CHECK(SegDist(kWestDoor, e, { -37.4f, -410.f }) < 0.5f);
        Vec2 const down = BullRushEnd(kEastDoor, kEastDoor);
        CHECK(down.y > kEastDoor.y);                                 // the east door's lane runs west, down the bridge
        CHECK(kBullRushTargets.At(5) == 1 && kBullRushTargets.At(7) == 2);
        // The sideways throw: past the near edge, on the span and on the cross platform.
        SideThrow const span = SideThrowAt({ -36.f, -418.f });
        CHECK(span.sign > 0.f && Near(span.distance, (-33.8f + 36.f) + kBullRushOverEdgeYd));
        SideThrow const south = SideThrowAt({ -40.f, -418.f });
        CHECK(south.sign < 0.f && Near(south.distance, 1.2f + kBullRushOverEdgeYd));
        SideThrow const platform = SideThrowAt({ -30.f, -434.f });
        CHECK(platform.sign > 0.f && Near(platform.distance, 7.8f + kBullRushOverEdgeYd));
        // Every throw from anywhere on the deck ends off it.
        for (float y = -400.f; y >= -442.f; y -= 0.5f)
        {
            Extent const ex = BridgeExtentAt(y);
            for (float x = ex.minX; x <= ex.maxX; x += 0.5f)
            {
                SideThrow const th = SideThrowAt({ x, y });
                float const land = x + th.sign * th.distance;
                CHECK(land > ex.maxX || land < ex.minX);
            }
        }
        // A Bull Rush is never down during a Belly Slam cast: the slam at 20 s (cast 20-22 s), a lane due at 19 s
        // would be down 19-21 s, so it waits until the slam has landed.
        std::vector<Window> slam{ { 20000, 20000 + kBellySlamCastMs + kBullRushWarnMs } };
        std::uint64_t const s = FirstClearStart(19000, kBullRushWarnMs, slam);
        CHECK(s >= 20000 + kBellySlamCastMs);
        CHECK(FirstClearStart(17000, kBullRushWarnMs, slam) == 17000);  // down 17-19 s, before the cast
        CHECK(kBellySlamRadius == 8.f && kBellySlamPct == 15.f && kBellySlamKnockYd == 20.f);
        CHECK(kBullRushWidth == 3.f && kBullRushPct == 15.f && kBullRushEveryMs == 8000);
        // The busiest moment the build spec counts: 2 lanes (6 of 8-9 yd) for 20 yd plus the slam.
        CHECK(2 * kBullRushWidth == 6.f);
    }

    void TestPitDrop()
    {
        CHECK(PitDropPct(false) == 70.f && PitDropPct(true) == 35.f);
        // One failure on the bridge: a Bull Rush and the catch, 85% (survivable at full).
        CHECK(kBullRushPct + kPitDropPct == 85.f);
        // The catch line leaves margin above the pit floor (50.8 yd under the deck).
        CHECK(Near(kOmokkBridgeDeckZ - kOmokkPitFloorZ, 50.7f, 0.2f));
        float const line = kOmokkBridgeDeckZ - kPitDropBelowYd;
        CHECK(line - kOmokkPitFloorZ >= 35.f);
        CHECK(line < kPitMaxZ);
        // The pit region holds the whole drop under the bridge and none of the deck.
        DungeonKit::Arena const pit(BoxRegion(kPitMinX, kPitMaxX, kPitMinY, kPitMaxY, kPitMinZ, kPitMaxZ));
        for (Point3 const& l : kOmokkLandings)
        {
            CHECK(!pit.Contains(l.XY(), l.z));
            CHECK(pit.Contains(l.XY(), line - 1.f));
            CHECK(pit.Contains(l.XY(), kOmokkPitFloorZ));
        }
        CHECK(!pit.Contains(kOmokkHaulUpWest.XY(), kOmokkHaulUpWest.z));
        // A throw off the cross platform's ends still falls inside the region (x -52.2 - 3, x -22.2 + 3).
        CHECK(pit.Contains({ -52.2f - kBullRushOverEdgeYd, -434.f }, 10.f));
        CHECK(pit.Contains({ -22.2f + kBullRushOverEdgeYd, -434.f }, 10.f));
        // R-1-A M1: a thrown player is still flying sideways at the catch line. From every deck point, the widest
        // throw (Belly Slam either way along x; Bull Rush toward its near edge) is still inside the box when the server
        // sees him under the line, and the whole Firebrand camp floor (x -72..3, y -437..-402) is inside too.
        float const line2 = kOmokkBridgeDeckZ - kPitDropBelowYd - 0.5f;
        float const slamReach = PitThrowReachYd(kBellySlamKnockYd, kBellySlamSpeedZ);
        CHECK(slamReach > 40.f && slamReach < 50.f);
        float widestRush = 0.f;
        for (float y = -400.f; y >= -442.f; y -= 0.5f)
        {
            Extent const ex = BridgeExtentAt(y);
            for (float x = ex.minX; x <= ex.maxX; x += 0.5f)
            {
                CHECK(pit.Contains({ x + slamReach, y }, line2));
                CHECK(pit.Contains({ x - slamReach, y }, line2));
                SideThrow const th = SideThrowAt({ x, y });
                float const rush = PitThrowReachYd(th.distance, kBullRushSpeedZ);
                widestRush = std::max(widestRush, rush);
                CHECK(pit.Contains({ x + th.sign * rush, y }, line2));
            }
        }
        CHECK(widestRush > 45.f);
        for (float x = -72.f; x <= 3.f; x += 1.f)
            for (float y = -437.f; y >= -402.f; y -= 1.f)
                CHECK(pit.Contains({ x, y }, kOmokkPitFloorZ));
        // The old box (x -56..-18) lost a Belly Slam victim beside him on the span.
        CHECK(-37.f + slamReach > -18.f && -37.f - slamReach < -56.f);
        // The haul-up goes to the nearer door.
        CHECK(Near(HaulUpFor(-405.f).y, kOmokkHaulUpWest.y));
        CHECK(Near(HaulUpFor(-436.f).y, kOmokkHaulUpEast.y));
        CHECK(Near(HaulUpFor(-420.29f).y, kOmokkHaulUpWest.y));
    }
}

int main()
{
    TestSliceAndArena();
    TestBand();
    TestPileAndShove();
    TestKnockbacks();
    TestHaymaker();
    TestPelting();
    TestCrowdBook();
    TestMojo();
    TestLandings();
    TestBridgeMechanics();
    TestPitDrop();

    return Report("brs_omokk_test");
}
