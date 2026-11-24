// Host tests for IronspineLogic.h (D2: Ironspine, GY 378-433; handoff section 3.5 row D2, section 7 #24 A).
#include "IronspineLogic.h"
#include "check.h"
#include <cmath>
#include <set>

using namespace ScarletMonasteryRework;
using namespace SmIronspine;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation, all distinct.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        std::set<std::uint32_t> ids;
        for (std::uint32_t id : { SPELL_IR_GRAVE_ROT_CAST, SPELL_IR_GRAVE_ROT, SPELL_IR_GRAVE_ROT_LOOK_7,
            SPELL_IR_GRAVE_ROT_LOOK_8, SPELL_IR_GRAVE_ROT_LOOK_9, SPELL_IR_GRAVE_ROT_LOOK_10, SPELL_IR_SHATTER,
            SPELL_IR_REASSEMBLED, SPELL_IR_REASSEMBLE_HEAL, SPELL_IR_FIST_SLAM, SPELL_IR_FIST_LANDING, SPELL_IR_CRUSH,
            SPELL_IR_CRUSH_TICK, SPELL_IR_RIBCAGE_CLOSED, SPELL_IR_EYE_SIGHT, SPELL_IR_GLARE_CAST, SPELL_IR_GLARE })
        {
            CHECK(kSpellSlice.Contains(id));
            ids.insert(id);
        }
        CHECK(ids.size() == 17);
        CHECK(SPELL_IR_GRAVE_ROT_CAST == 212350);
        CHECK(SPELL_IR_GLARE == 212366);
        // The rung looks ascend 7..10 yd and are the four look spells.
        CHECK(kRotRungs.size() == 4);
        for (std::size_t i = 0; i < kRotRungs.size(); ++i)
        {
            CHECK(Near(kRotRungs[i].radiusYd, 7.f + static_cast<float>(i)));
            CHECK(kRotRungs[i].spellId == SPELL_IR_GRAVE_ROT_LOOK_7 + i);
        }
    }

    void TestTexts()
    {
        // Text groups inside the header's ranges.
        bool boss = false;
        bool eye = false;
        for (TextRange const& r : kTextRanges)
        {
            if (r.entry == NPC_IRONSPINE)
            {
                boss = true;
                CHECK(r.first == EMOTE_IR_GRAVE_ROT && r.last == EMOTE_IR_RIBCAGE && r.firstNew == 0);
            }
            if (r.entry == NPC_SM_IRONSPINE_EYE)
            {
                eye = true;
                CHECK(r.first == EMOTE_IR_EYE_GLARE && r.last == EMOTE_IR_EYE_GLARE);
            }
        }
        CHECK(boss);
        CHECK(eye);
    }

    void TestParts()
    {
        CHECK(PartEntry(Part::Fist) == 300900);
        CHECK(PartEntry(Part::Ribcage) == 300901);
        CHECK(PartEntry(Part::Eye) == 300902);
        for (Part p : kShatterOrder)
        {
            CHECK(PartOf(PartEntry(p)) == p);
            CHECK(kCreaturesWave1.Contains(PartEntry(p)));
        }
        CHECK(!PartOf(NPC_IRONSPINE).has_value());
        CHECK(PartsKilled(0) == 0);
        CHECK(PartsKilled(kAllPartsMask) == 3);
        CHECK(PartsKilled(PartBit(Part::Eye)) == 1);
    }

    void TestRotCadence()
    {
        // GY IR1: 14, 12, 10, 8 s; never under 8.
        CHECK(RotEveryMs(0) == 14000);
        CHECK(RotEveryMs(1) == 12000);
        CHECK(RotEveryMs(2) == 10000);
        CHECK(RotEveryMs(3) == 8000);
        CHECK(RotEveryMs(4) == 8000);
        CHECK(RotEveryMs(100) == 8000);
        CHECK(kRotFirstMs == 6000 && kRotCastMs == 1500);
        CHECK(Near(kRotPct(false), 5.f) && Near(kRotPct(true), 8.f));
        CHECK(Near(kRotToYd(false), kRotFromYd) && Near(kRotToYd(true), 10.f));
        CHECK(kRotLifeMs(false) == 0 && kRotLifeMs(true) == 60000);
        // Heroic growth: 7 -> 10 in 10 s steps over 30 s = three steps of 1 yd: every rung is used.
        CHECK(kRotGrowOverMs / kRotGrowStepMs == 3);
        CHECK(Near((kRotToYd(true) - kRotFromYd) / static_cast<float>(kRotGrowOverMs / kRotGrowStepMs), 1.f));
    }

    void TestShatterQueue()
    {
        ShatterQueue q;
        // Order Fist, Ribcage, Eye.
        std::vector<Part> a = q.Take(1);
        CHECK(a.size() == 1 && a[0] == Part::Fist);
        // The Fist returns: to the back.
        q.Return(Part::Fist);
        CHECK(q.Order().size() == 3);
        CHECK(q.Order()[0] == Part::Ribcage && q.Order()[1] == Part::Eye && q.Order()[2] == Part::Fist);
        // Heroic takes two.
        std::vector<Part> b = q.Take(2);
        CHECK(b.size() == 2 && b[0] == Part::Ribcage && b[1] == Part::Eye);
        // The Ribcage is killed: never back.
        q.Kill(Part::Ribcage);
        q.Return(Part::Ribcage);
        CHECK(!q.Queued(Part::Ribcage) && q.Killed(Part::Ribcage));
        CHECK(q.KilledCount() == 1);
        // The Eye returns behind the Fist; returning twice does not double it.
        q.Return(Part::Eye);
        q.Return(Part::Eye);
        CHECK(q.Order().size() == 2 && q.Order()[0] == Part::Fist && q.Order()[1] == Part::Eye);
        // Taking more than there is.
        std::vector<Part> c = q.Take(5);
        CHECK(c.size() == 2);
        CHECK(q.Take(1).empty());
        q.Kill(Part::Fist);
        q.Kill(Part::Eye);
        CHECK(q.AllKilled());
        q.Reset();
        CHECK(q.Order().size() == 3 && q.KilledCount() == 0);
        // `.dbtest` takes one named part; a part not at home is refused.
        CHECK(q.TakePart(Part::Eye));
        CHECK(!q.TakePart(Part::Eye));
        CHECK(q.Order().size() == 2 && q.Order()[0] == Part::Fist && q.Order()[1] == Part::Ribcage);
        q.Reset();
        CHECK(kPartsPerShatter(false) == 1 && kPartsPerShatter(true) == 2);
        CHECK(kShatterEveryMs(false) == 22000 && kShatterEveryMs(true) == 20000 && kShatterFirstMs == 12000);
    }

    void TestReassembled()
    {
        // Normal caps at 3 (the group-failure cap below 60); heroic has no cap (the aura's own max).
        CHECK(ReassembledAfter(0, false) == 1);
        CHECK(ReassembledAfter(2, false) == 3);
        CHECK(ReassembledAfter(3, false) == 3);
        CHECK(ReassembledAfter(3, true) == 4);
        CHECK(ReassembledAfter(50, true) == 51);
        CHECK(ReassembledAfter(kReassembledAuraMax, true) == kReassembledAuraMax);
        CHECK(ReassembledCap(false) == 3 && ReassembledCap(true) == kReassembledAuraMax);
        CHECK(Near(kReattachHealPct(false), 10.f) && Near(kReattachHealPct(true), 15.f));
        CHECK(PctOfMax(36000, 10.f) == 3600);
        CHECK(PctOfMax(240000, 15.f) == 36000);
        // GY failing path: a part home (3.6k) costs more than killing it (3k).
        CHECK(PctOfMax(36000, kReattachHealPct(false)) > 3000);
    }

    void TestHops()
    {
        Vec2 const boss{ 0.f, 0.f };
        float const stop = 2.f;
        // From 20 yd: a 6 yd hop toward him.
        Hop h = NextHop({ 20.f, 0.f }, boss, stop);
        CHECK(!h.last);
        CHECK(Near(h.to.x, 14.f) && Near(h.to.y, 0.f));
        // From 7.5 yd (5.5 to his edge): the last hop, to his edge.
        h = NextHop({ 0.f, 7.5f }, boss, stop);
        CHECK(h.last);
        CHECK(Near(h.to.x, 0.f) && Near(h.to.y, 2.f));
        // Already at his edge.
        h = NextHop({ 1.f, 0.f }, boss, stop);
        CHECK(h.last && Near(h.to.x, 1.f));
        // From 15-20 yd the Fist takes 3 hops (9 s) home at a 2 yd reach: the spec's 8 to 13 s.
        CHECK(HopsHome(15.f - stop) == 3);
        CHECK(HopsHome(20.f - stop) == 3);
        CHECK(HopsHome(0.f) == 0);
        // Walking a whole path: every hop is 6 yd or less and ends at the edge.
        Vec2 p{ -12.f, 13.f };
        std::uint32_t hops = 0;
        for (; hops < 10; ++hops)
        {
            Hop const next = NextHop(p, boss, stop);
            CHECK(DungeonKit::Distance(p, next.to) <= kFistHopYd + 0.01f);
            p = next.to;
            if (next.last)
                break;
        }
        CHECK(hops < 10);
        CHECK(Near(DungeonKit::Distance(p, boss), stop, 0.05f));
        CHECK(Arrived(DungeonKit::Distance(p, boss), stop));
        CHECK(!Arrived(stop + kArriveSlackYd + 0.5f, stop));
        // The hop rhythm: a marker 2 s before each landing, a landing every 3 s, the first 3 s after it lands.
        CHECK(kFistFirstMarkerMs + kFistMarkerWarnMs == kFistHopEveryMs);
        CHECK(kFistJumpLeadMs < kFistMarkerWarnMs);
        CHECK(Near(kFistPct(false), 35.f) && Near(kFistPct(true), 45.f));
        // 2 yd/s.
        CHECK(Near(kFistHopYd / (static_cast<float>(kFistHopEveryMs) / 1000.f), 2.f));
    }

    void TestCrush()
    {
        // Ticks weighted 1 to 6, 50% normal (2.4, 4.8, 7.1, 9.5, 11.9, 14.3) and 120% heroic by the timeout.
        CHECK(CrushWeightSum() == 21);
        float n = 0.f;
        float h = 0.f;
        for (std::uint32_t t = 1; t <= kCrushTicks; ++t)
        {
            n += CrushTickPct(false, t);
            h += CrushTickPct(true, t);
            if (t > 1)
                CHECK(CrushTickPct(false, t) > CrushTickPct(false, t - 1));
        }
        CHECK(Near(n, 50.f, 0.01f));
        CHECK(Near(h, 120.f, 0.01f));
        CHECK(Near(CrushTickPct(false, 1), 2.38f, 0.01f));
        CHECK(Near(CrushTickPct(false, 6), 14.29f, 0.01f));
        CHECK(Near(CrushTickPct(false, 0), 0.f) && Near(CrushTickPct(true, 7), 0.f));
        // The last tick lands at the timeout: 6 x 2 s = 12 s.
        CHECK(kCrushTicks * kCrushTickMs == kCageHoldMs);
        CHECK(Near(kCageNearbyYd(false), 0.f) && Near(kCageNearbyYd(true), 6.f));
    }

    void TestEye()
    {
        CHECK(Near(kEyeSpeedYdPerSec, 1.5f));
        // 15-20 yd at 1.5 yd/s: 9 to 12 s home to a 2 yd reach (the spec's "about 8 to 13 s").
        CHECK((kLandMinYd - 2.f) / kEyeSpeedYdPerSec >= 8.f);
        CHECK((kLandMaxYd - 2.f) / kEyeSpeedYdPerSec <= 13.f);
        CHECK(kGlareFirstMs == 6000 && kGlareEveryMs == 6000 && kGlareCastMs == 2000);
        CHECK(kEyePools == 2 && kEyePoolWarnMs == 2000);
    }

    void TestArena()
    {
        // His home is the lawn (section 7 #24 A); the stock walled plot is out of his arena now.
        Arena const arena = FightArena();
        CHECK(arena.Contains(kIronspineHome.XY(), kIronspineHome.z));
        CHECK(!arena.Contains(kIronspineStockSpawn.XY(), kIronspineStockSpawn.z));
        CHECK(ArenaFor(BOSS_IRONSPINE).Contains(kIronspineHome.XY(), kIronspineHome.z));
        CHECK(Near(kHome.x, 1796.5f) && Near(kHome.y, 1285.5f));
        // Every landing ring candidate around his home is 15-20 yd out and inside the arena with the inset.
        std::vector<Vec2> const ring = LandingRing(kHome, 0.3f, {}, {});
        CHECK(ring.size() == 36);
        for (Vec2 const& p : ring)
        {
            float const d = DungeonKit::Distance(p, kHome);
            CHECK(d >= kLandMinYd - 0.01f && d <= kLandMaxYd + 0.01f);
            CHECK(arena.Contains(p, kHomeZ));
        }
        // A boss dragged to the arena's edge: candidates past the edge are dropped.
        Vec2 const edge = DungeonKit::Advance(kHome, 1.f, 34.f);
        for (Vec2 const& p : LandingRing(edge, 0.f, {}, {}))
            CHECK(DungeonKit::Distance(p, kHome) <= kArenaRadiusYd - kLandingInsetYd + 0.01f);
        CHECK(LandingRing(edge, 0.f, {}, {}).size() < 36);
        // Pools and other parts push a candidate to the back.
        std::vector<Circle2> pools{ { DungeonKit::Advance(kHome, 0.f, 17.5f), 7.f } };
        std::vector<Vec2> const sorted = LandingRing(kHome, 0.f, pools, {});
        CHECK(sorted.size() == 36);
        CHECK(DungeonKit::Distance(sorted.front(), pools[0].center) > 8.f);
        CHECK(DungeonKit::Distance(sorted.back(), pools[0].center) <= 8.f);
        std::vector<Vec2> const taken{ DungeonKit::Advance(kHome, 0.f, 17.5f) };
        CHECK(DungeonKit::Distance(LandingRing(kHome, 0.f, {}, taken).front(), taken[0]) > 6.f);
        // Flight time: 17.5 yd at 20 yd/s is under a second and a quarter.
        CHECK(FlightMs(17.5f) == 875 + kLandSlackMs);
        CHECK(FlightMs(0.f) == kLandSlackMs);
        // The bots' bounds stay inside the arena.
        CHECK(kBoundsRadiusYd < kArenaRadiusYd);
        // The heroic pool (10 yd) and the 20 yd landing fit inside the 40 yd disc around his home.
        CHECK(kLandMaxYd + kRotToYd(true) <= kArenaRadiusYd);

        // R-1-GY MN-3: the yard stops short of the council (63 yd north). Every corner of the arena, the bots' bounds
        // and every landing stays 30+ yd from the council's spot; the arena still holds his home and the full ring.
        Vec2 const council = kCouncilLawn.XY();
        CHECK(DungeonKit::Distance(kHome, council) > 62.f);
        for (Vec2 const& p : YardPolygon(kArenaRadiusYd, kYardNorthY))
        {
            CHECK(DungeonKit::Distance(p, council) >= 31.f);
            CHECK(DungeonKit::Distance(p, kHome) <= kArenaRadiusYd + 0.01f);
        }
        for (Vec2 const& p : YardPolygon(kBoundsRadiusYd, kYardNorthY - kBoundsNorthInsetYd))
            CHECK(DungeonKit::Distance(p, council) >= 33.f);
        CHECK(!arena.Contains({ kHome.x, kYardNorthY + 1.f }, kHomeZ));
        CHECK(arena.Contains({ kHome.x, kYardNorthY - 1.f }, kHomeZ));
        CHECK(arena.Contains({ kHome.x, kHome.y - 39.f }, kHomeZ));     // the south keeps the full 40 yd
        // A boss dragged to the north cut: every candidate stays the landing inset short of it.
        Vec2 const north{ kHome.x, kYardNorthY - 2.f };
        std::vector<Vec2> const northRing = LandingRing(north, 0.f, {}, {});
        CHECK(!northRing.empty() && northRing.size() < 36);
        for (Vec2 const& p : northRing)
        {
            CHECK(p.y <= kYardNorthY - kLandingInsetYd + 0.01f);
            CHECK(DungeonKit::Distance(p, council) >= 31.f + kLandingInsetYd - 0.01f);
            CHECK(arena.Contains(p, kHomeZ));
        }
        CHECK(InYard(kHome, kLandingInsetYd) && !InYard({ kHome.x, kYardNorthY - 1.f }, kLandingInsetYd));
    }

    void TestPriorities()
    {
        // Nearer parts first; the held cage above every loose part; every part above him (0).
        CHECK(PartPriority(3.f) == 4);
        CHECK(PartPriority(10.f) == 3);
        CHECK(PartPriority(30.f) == 2);
        CHECK(PartPriority(500.f) == 1);
        CHECK(kCagePriority > PartPriority(0.f));
        for (NearTier const& t : kNearTiers)
            CHECK(t.priority > 0);
    }
}

int main()
{
    TestSlice();
    TestTexts();
    TestParts();
    TestRotCadence();
    TestShatterQueue();
    TestReassembled();
    TestHops();
    TestCrush();
    TestEye();
    TestArena();
    TestPriorities();
    CHECK(!IsWave2Boss(BOSS_IRONSPINE));
    return Report("sm_ironspine_test");
}
