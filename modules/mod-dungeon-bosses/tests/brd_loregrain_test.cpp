// Host tests for LoregrainLogic.h (D7: Pyromancer Loregrain): the slice, the arena, the corridor and its ward spots,
// the ward's radius by totems and Wraths, the ward move, the Fury meter, the tide's percent, the repel landing, the
// hold, the totem spots, the patch shelter, Fire Ward's absorb and the cadences.
#include "LoregrainLogic.h"
#include "check.h"
#include <cmath>
#include <set>

using namespace BlackrockDepthsRework;
using namespace BrdLoregrain;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndTexts()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation, and are distinct.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        std::set<std::uint32_t> const ids{ SPELL_LG_TIDE_HIT, SPELL_LG_TIDE_CAST, SPELL_LG_WRATH_CAST_N,
            SPELL_LG_WRATH_CAST_H, SPELL_LG_WRATH_HIT, SPELL_LG_WARD_REPEL, SPELL_LG_DEFILING_PRESENCE,
            SPELL_LG_SPLASH_LOB, SPELL_LG_SPLASH_HIT, SPELL_LG_PATCH_HIT, SPELL_LG_PATCH_LOOK, SPELL_LG_FURY,
            SPELL_LG_FIRE_WARD, SPELL_LG_MOLTEN_BLAST, SPELL_LG_FLAME_SHOCK, SPELL_LG_SEARING_BOLT };
        CHECK(ids.size() == 16);
        for (std::uint32_t id : ids)
            CHECK(kSpellSlice.Contains(id));
        CHECK(*ids.begin() == 211020);
        CHECK(*ids.rbegin() == 211035);

        // The text groups sit in the header's ranges (9024 0-4; 9542 group 0, D10's copy group 1).
        TextRange const* lg = nullptr;
        TextRange const* spirit = nullptr;
        for (TextRange const& r : kTextRanges)
        {
            if (r.entry == NPC_LOREGRAIN)
                lg = &r;
            if (r.entry == NPC_FRANCLORNS_SPIRIT)
                spirit = &r;
        }
        CHECK(lg && spirit);
        if (lg && spirit)
        {
            for (std::uint8_t g : { YELL_LG_PULL, YELL_LG_TIDE, YELL_LG_WRATH, YELL_LG_DEATH, EMOTE_LG_WARD_MOVE })
                CHECK(g >= lg->first && g <= lg->last);
            CHECK(SAY_FRANCLORN_THANKS >= spirit->first && SAY_FRANCLORN_THANKS <= spirit->last);
            CHECK(SAY_FRANCLORN_THANKS != 1);     // D10's copy line
        }
        // The G1 drill row `ward` keys: Stack/11, Zone/12.
        CHECK(TAG_LG_WARD == 11);
        CHECK(TAG_LG_TIDE == 12);
        CHECK(TAG_LG_SPLASH != TAG_LG_PATCH && TAG_LG_SPLASH != TAG_LG_WARD && TAG_LG_PATCH != TAG_LG_TIDE);
    }

    void TestCorridorAndSpots()
    {
        // Pyromancer Loregrain spawns kLoregrainSpawn, inside the arena and the corridor.
        CHECK(LoregrainArena().Contains(kLoregrainSpawn.XY(), kLoregrainSpawn.z));
        CHECK(ArenaFor(BOSS_LOREGRAIN).Contains(kLoregrainSpawn.XY(), kLoregrainSpawn.z));
        CHECK(InCorridor(kLoregrainSpawn.XY()));

        // The axis is a unit vector; the corridor frame round-trips.
        CHECK(Near(kCorridorAxis.x * kCorridorAxis.x + kCorridorAxis.y * kCorridorAxis.y, 1.f, 0.001f));
        Vec2 const p{ 545.f, -250.f };
        Vec2 const back = FromCorridor(ToCorridor(p));
        CHECK(Near(back.x, p.x, 0.01f) && Near(back.y, p.y, 0.01f));

        // NAVMESH: the spots are 19.1 / 14.9 / 34.0 yd apart from the statue's own spot (527, -241), which is on the
        // wall line; from the floor spot (530.0, -243.5) the statue-to-middle leg is 15.2 and end to end 30.1 (the
        // spec's 15 / 15). All on the axis (within 1 yd), inside the arena; a 6 yd ward leaves 2 yd each side of the
        // 16 yd corridor.
        CHECK(Near(DungeonKit::Distance({ 527.f, -241.f }, kWardSpots[1].XY()), 19.1f, 0.2f));
        CHECK(Near(DungeonKit::Distance(kWardSpots[0].XY(), kWardSpots[1].XY()), 15.2f, 0.2f));
        CHECK(Near(DungeonKit::Distance(kWardSpots[1].XY(), kWardSpots[2].XY()), 14.9f, 0.2f));
        CHECK(Near(DungeonKit::Distance(kWardSpots[0].XY(), kWardSpots[2].XY()), 30.1f, 0.2f));
        for (Point3 const& spot : kWardSpots)
        {
            CHECK(std::fabs(ToCorridor(spot.XY()).w) < 1.f);
            CHECK(LoregrainArena().Contains(spot.XY(), spot.z));
            CHECK(InCorridor(spot.XY()));
            CHECK(kCorridorHalfWidthYd - WardRadius(false, 0, 0) >= 2.f);
        }
        CHECK(kWardSpotAtPull == 0);
        // Review Q1 (orchestrator default): the ward forms at the first tide, at the spot the move from the statue
        // reaches, well clear of his spawn (530.17, -243.93), so the pull throws nobody.
        CHECK(kWardSpotFirst == NextWardSpot(kWardSpotAtPull, false));
        CHECK(kWardSpotFirst == NextWardSpot(kWardSpotAtPull, true));
        CHECK(DungeonKit::Distance({ 530.17f, -243.93f }, kWardSpots[kWardSpotFirst].XY())
            > WardRadius(false, 0, 0) + kRepelLandYd + 5.f);
        // The usable floor sits inside the arena (the boss's landings never leash him).
        for (float s : { kCorridorMinS, 0.f, 20.f, kCorridorMaxS })
            for (float w : { -kCorridorUsableHalfYd, 0.f, kCorridorUsableHalfYd })
                CHECK(LoregrainArena().Contains(FromCorridor({ s, w }), kFloorZ));
        // Clamp.
        CorridorPoint const c = ToCorridor(ClampToCorridor(FromCorridor({ 80.f, 20.f })));
        CHECK(Near(c.s, kCorridorMaxS) && Near(c.w, kCorridorUsableHalfYd));
    }

    void TestWard()
    {
        // LG3: 6 / 5 yd, -1 per totem, min 2; heroic -1 per Wrath, base min 3.
        CHECK(Near(WardRadius(false, 0, 0), 6.f));
        CHECK(Near(WardRadius(false, 1, 0), 5.f));
        CHECK(Near(WardRadius(false, 3, 0), 3.f));
        CHECK(Near(WardRadius(false, 0, 5), 6.f));          // normal never cracks
        CHECK(Near(WardRadius(false, 9, 0), 2.f));
        CHECK(Near(WardRadius(true, 0, 0), 5.f));
        CHECK(Near(WardRadius(true, 0, 1), 4.f));
        CHECK(Near(WardRadius(true, 0, 2), 3.f));
        CHECK(Near(WardRadius(true, 0, 7), 3.f));           // the base stops at 3
        CHECK(Near(WardRadius(true, 1, 7), 2.f));
        CHECK(Near(WardRadius(true, 3, 0), 2.f));           // the floor is 2
        CHECK(Near(WardRadius(true, 3, 3), 2.f));
        for (std::uint32_t totems = 0; totems <= kTotemCap + 2; ++totems)
            for (std::uint32_t cracks = 0; cracks <= 5; ++cracks)
                for (bool heroic : { false, true })
                {
                    float const r = WardRadius(heroic, totems, cracks);
                    CHECK(r >= kWardMinYd && r <= kWardBaseYd(heroic));
                    // more totems never grow it
                    CHECK(WardRadius(heroic, totems + 1, cracks) <= r);
                }

        // LG2: from the middle either way, from an end to the middle; never the same spot, never end to end.
        CHECK(NextWardSpot(0, false) == 1 && NextWardSpot(0, true) == 1);
        CHECK(NextWardSpot(2, false) == 1 && NextWardSpot(2, true) == 1);
        CHECK(NextWardSpot(1, false) == 0 && NextWardSpot(1, true) == 2);
        for (std::uint8_t from = 0; from < kWardSpotCount; ++from)
            for (bool far : { false, true })
            {
                std::uint8_t const to = NextWardSpot(from, far);
                CHECK(to != from && to < kWardSpotCount);
                CHECK(DungeonKit::Distance(kWardSpots[from].XY(), kWardSpots[to].XY()) < 20.f);
            }
    }

    void TestRepelAndHold()
    {
        // Inside the ward (less the slack) he is thrown; on the edge he is not.
        CHECK(RepelDue(0.f, 2.f));
        CHECK(RepelDue(5.5f, 6.f));
        CHECK(!RepelDue(5.8f, 6.f));
        CHECK(!RepelDue(7.f, 6.f));

        // Every landing is clear of the ward by at least 1 yd and on the corridor's usable floor, from any point of
        // the ward at every spot and radius.
        for (Point3 const& spot : kWardSpots)
            for (float r : { 2.f, 3.f, 5.f, 6.f })
                for (int a = 0; a < 24; ++a)
                    for (float f : { 0.f, 0.3f, 0.9f })
                    {
                        float const ang = DungeonKit::kTwoPi * float(a) / 24.f;
                        Vec2 const boss{ spot.x + std::cos(ang) * r * f, spot.y + std::sin(ang) * r * f };
                        Vec2 const land = RepelLanding(spot.XY(), boss, r);
                        CHECK(DungeonKit::Distance(land, spot.XY()) >= r + 1.f - 0.01f);
                        CorridorPoint const c = ToCorridor(land);
                        CHECK(c.s >= kCorridorMinS - 0.01f && c.s <= kCorridorMaxS + 0.01f);
                        CHECK(std::fabs(c.w) <= kCorridorUsableHalfYd + 0.01f);
                        CHECK(LoregrainArena().Contains(land, kFloorZ));
                    }
        // Straight out: from the middle spot, a boss 2 yd north-east of the center lands 9 yd out the same way.
        Vec2 const mid = kWardSpots[1].XY();
        Vec2 const boss{ mid.x + kCorridorAxis.x * 2.f, mid.y + kCorridorAxis.y * 2.f };
        Vec2 const land = RepelLanding(mid, boss, 6.f);
        CHECK(Near(DungeonKit::Distance(land, mid), 9.f, 0.05f));
        CHECK(ToCorridor(land).s > ToCorridor(mid).s);
        // On the center of the statue spot: along the corridor toward the far end; of the far spot: toward the statue.
        CHECK(ToCorridor(RepelLanding(kWardSpots[0].XY(), kWardSpots[0].XY(), 6.f)).s > 5.f);
        CHECK(ToCorridor(RepelLanding(kWardSpots[2].XY(), kWardSpots[2].XY(), 6.f)).s < ToCorridor(
            kWardSpots[2].XY()).s);

        // The hold: his victim inside, he at the edge (+1.5 yd).
        CHECK(HoldAtEdge(6.5f, 3.f, 6.f));
        CHECK(HoldAtEdge(7.5f, 5.9f, 6.f));
        CHECK(!HoldAtEdge(7.6f, 3.f, 6.f));     // farther: he walks in to the edge first
        CHECK(!HoldAtEdge(6.5f, 6.2f, 6.f));    // his victim outside: no hold

        // R-1-A M2: after a throw (radius + 3 yd out) he walks to the edge spot, which is inside the hold band and
        // outside the repel: from any landing at every spot and radius, he never walks into the ward.
        for (Point3 const& spot : kWardSpots)
            for (float r : { 2.f, 3.f, 5.f, 6.f })
                for (int a = 0; a < 24; ++a)
                {
                    float const ang = DungeonKit::kTwoPi * float(a) / 24.f;
                    Vec2 const inside{ spot.x + std::cos(ang) * r * 0.5f, spot.y + std::sin(ang) * r * 0.5f };
                    Vec2 const land = RepelLanding(spot.XY(), inside, r);
                    Vec2 const edge = HoldSpot(spot.XY(), land, r);
                    float const d = DungeonKit::Distance(edge, spot.XY());
                    CHECK(!RepelDue(d, r));
                    CHECK(HoldAtEdge(d, 0.f, r));
                    CorridorPoint const c = ToCorridor(edge);
                    CHECK(c.s >= kCorridorMinS - 0.01f && c.s <= kCorridorMaxS + 0.01f);
                    CHECK(std::fabs(c.w) <= kCorridorUsableHalfYd + 0.01f);
                }
        // Straight out from the middle: the edge spot sits on his side, kHoldStandYd past the edge.
        Vec2 const far{ mid.x + kCorridorAxis.x * 12.f, mid.y + kCorridorAxis.y * 12.f };
        Vec2 const edge = HoldSpot(mid, far, 6.f);
        CHECK(Near(DungeonKit::Distance(edge, mid), 6.f + kHoldStandYd, 0.05f));
        CHECK(ToCorridor(edge).s > ToCorridor(mid).s);
        // The statue end leaves no room past a ward at spot 0 toward the statue: the far side instead.
        Vec2 const behind = FromCorridor({ kCorridorMinS, 0.f });
        CHECK(!RepelDue(DungeonKit::Distance(HoldSpot(kWardSpots[0].XY(), behind, 6.f), kWardSpots[0].XY()), 6.f));
        // The cooldown only spaces two throws (the jump itself is skipped by its motion, not by this).
        CHECK(kRepelCooldownMs <= 1000);
    }

    void TestFuryAndTides()
    {
        // LG6: clamps, the per-second gains, the events.
        CHECK(FuryAdd(0, -15) == 0);
        CHECK(FuryAdd(95, 10) == 100);
        CHECK(FuryAdd(50, kFuryBlastLanded) == 60);
        CHECK(FuryAdd(50, kFuryBlastInterrupted) == 35);
        CHECK(FuryAdd(50, kFuryTotemKilled) == 40);
        CHECK(FuryAdd(50, kFuryWardBroken) == 30);
        CHECK(FuryAfterSecond(0, false, 0) == 0);
        CHECK(FuryAfterSecond(0, true, 0) == 3);
        CHECK(FuryAfterSecond(0, false, 3) == 6);
        CHECK(FuryAfterSecond(10, true, 2) == 17);
        CHECK(FuryAfterSecond(99, true, 3) == 100);
        CHECK(!WrathDue(99) && WrathDue(100));
        CHECK(kFuryAfterWrath == 30);
        // Fire Ward alone (30 s up, every 30 s) and nothing else: 90 by the time it is recast, 100 at 34 s.
        std::uint32_t fury = 0;
        std::uint32_t seconds = 0;
        while (!WrathDue(fury) && seconds < 200)
        {
            fury = FuryAfterSecond(fury, true, 0);
            ++seconds;
        }
        CHECK(seconds == 34);

        // LG1: 30% / 45% x (1 + Fury / 100), at most 75%.
        CHECK(Near(TidePct(false, 0), 30.f));
        CHECK(Near(TidePct(false, 50), 45.f));
        CHECK(Near(TidePct(false, 100), 60.f));
        CHECK(Near(TidePct(false, 250), 60.f));       // Fury never passes 100
        CHECK(Near(TidePct(true, 0), 45.f));
        CHECK(Near(TidePct(true, 50), 67.5f));
        CHECK(Near(TidePct(true, 100), 75.f));        // the cap (ruling 91)
        for (std::uint32_t f = 0; f <= 100; ++f)
        {
            CHECK(TidePct(false, f) <= 60.f + 0.001f);  // the normal ladder: up to 75% needs a 4 s+ warning, it has 4 s
            CHECK(TidePct(true, f) <= kTideCapPct);
        }
        // Section 7 #21: the Wrath's warning is 4 s on normal, 2 s on heroic; the Fire Tide's 4 s.
        CHECK(kWrathWarnMs(false) == 4000 && kWrathWarnMs(true) == 2000);
        CHECK(kTideWarnMs == 4000);
        CHECK(kTideOuterYd == 45.f);

        // Two tides keep 3 s between a landing and the next start.
        CHECK(TideStartAfter(20000, 0) == 20000);
        CHECK(TideStartAfter(20000, 18000) == 21000);
        CHECK(TideStartAfter(30000, 18000) == 30000);

        // The cadences: the build spec's first and every.
        CHECK(kTideFirstMs == 20000 && kTideEveryMs(false) == 30000 && kTideEveryMs(true) == 25000);
        CHECK(kTotemFirstMs == 10000 && kTotemEveryMs(false) == 15000 && kTotemEveryMs(true) == 12000);
        CHECK(kSplashFirstMs == 6000 && kSplashEveryMs(false) == 10000 && kSplashEveryMs(true) == 8000);
        CHECK(kSplashCount(false) == 2 && kSplashCount(true) == 3);
        CHECK(kFireWardFirstMs == 5000 && kFireWardEveryMs == 30000);
        CHECK(kMoltenBlastEveryMs == 12000 && kMoltenBlastCastMs == 2000);
        CHECK(NextPlanned(20000, 30000, 25000) == 50000);
        CHECK(NextPlanned(20000, 30000, 55000) == 80000);   // a missed beat is skipped, the phase kept
        // A 2 s cast never starts within 2.5 s of a due tide.
        CHECK(CastBlocksTide(18000, 2000, 20000));
        CHECK(!CastBlocksTide(17000, 2000, 20000));
    }

    void TestTotemsPatchesWard()
    {
        // Totem spots: inside the ward (inset), uniform-ish, over every corner of [0, 1]^2.
        for (Point3 const& spot : kWardSpots)
            for (float r : { 2.f, 3.f, 6.f })
                for (float u : { 0.f, 0.25f, 0.5f, 1.f })
                    for (float v : { 0.f, 0.3f, 0.7f, 1.f })
                    {
                        Vec2 const t = TotemSpot(spot.XY(), r, u, v);
                        float const d = DungeonKit::Distance(t, spot.XY());
                        CHECK(d <= std::max(0.5f, r - kTotemInsetYd) + 0.001f);
                        CHECK(d < r);
                        CHECK(InCorridor(t));
                    }
        CHECK(kTotemCap == 3);

        // Shelter: a patch centered in the ward stays; one outside is washed.
        Vec2 const c = kWardSpots[1].XY();
        CHECK(Sheltered(c, c, 2.f));
        CHECK(Sheltered({ c.x + 3.f, c.y }, c, 3.f));
        CHECK(!Sheltered({ c.x + 3.1f, c.y }, c, 3.f));
        CHECK(!Sheltered(kWardSpots[0].XY(), c, 6.f));
        // Gap 20 default and the hits.
        CHECK(Near(kPatchPct(false), 4.f) && Near(kPatchPct(true), 6.f));
        CHECK(Near(kSplashPct(false), 20.f) && Near(kSplashPct(true), 35.f));
        CHECK(kSplashWarnMs == 2000 && Near(kSplashRadiusYd, 4.f) && Near(kPatchRadiusYd, 4.f));
        // The normal ladder: a 2 s marker allows up to 40%.
        CHECK(kSplashPct(false) <= 40.f);

        // Fire Ward: 8% of his health (130k normal, 220k heroic).
        CHECK(FireWardAbsorb(130000) == 10400);
        CHECK(FireWardAbsorb(220000) == 17600);
        CHECK(FireWardAbsorb(0) == 0);
        CHECK(kFireWardMs >= kFireWardEveryMs);     // it never lapses between casts on its own
    }
}

int main()
{
    TestSliceAndTexts();
    TestCorridorAndSpots();
    TestWard();
    TestRepelAndHold();
    TestFuryAndTides();
    TestTotemsPatchesWard();
    return Report("brd_loregrain_test");
}
