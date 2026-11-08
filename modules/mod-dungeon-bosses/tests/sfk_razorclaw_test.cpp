// Host tests for Razorclaw the Butcher (WP-S2): RazorclawLogic.h. Handoff section 5: hook lines never within 3 s of a
// Cut, twin targets distinct, line ends inside the walls; plus the tuning per difficulty (and the echo's), the pick
// rule, the once-per-throw memory, the drag's flight, the bleed's ticks, Tenderize and the slick's pools.
#include "RazorclawLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace ShadowfangKeepRework;
using namespace Razorclaw;

namespace
{
    // A deterministic rand(n): a linear congruential sequence, so a seed sweep covers many picks.
    struct SeqRand
    {
        std::uint32_t state;

        std::uint32_t operator()(std::uint32_t n)
        {
            state = state * 1664525u + 1013904223u;
            return n ? (state >> 8) % n : 0;
        }
    };

    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Razorclaw::kSlice.first));
        CHECK(kSpellsReservation.Contains(Razorclaw::kSlice.last));
        CHECK(Razorclaw::kSlice.first <= Razorclaw::kSlice.last);
        CHECK(RazorclawArena().Contains(kRazorclawSpawn.XY(), kRazorclawSpawn.z));
        CHECK(kSlice.first == 205930u && kSlice.last == 205944u);
        for (std::uint32_t id = SPELL_RC_MEAT_HOOK_CAST; id <= SPELL_RC_OFFAL_SLICK; ++id)
            CHECK(kSlice.Contains(id));
        CHECK(kGameObjectsReservation.Contains(GO_SFK_OFFAL_SLICK));
        CHECK(GO_SFK_OFFAL_SLICK != GO_SFK_CELL_KEY && GO_SFK_OFFAL_SLICK != GO_SFK_ALARM_BELL);
    }

    // SK RC1: 35% on both difficulties, one line on normal, two on heroic, the heroic bleed 20% over 8 s (35 + 20 = 55,
    // under the 75% single-failure cap); BS4's echo throws the normal hook on both difficulties.
    void TestHookTuning()
    {
        HookTuning const n = HookFor(false);
        HookTuning const h = HookFor(true);
        CHECK(n.lines == 1 && h.lines == 2);
        CHECK(Near(n.pct, 35.f) && Near(h.pct, 35.f));
        CHECK(Near(n.bleedPct, 0.f) && Near(h.bleedPct, 20.f));
        CHECK(h.pct + h.bleedPct <= 75.f);
        for (HookTuning const& t : { n, h })
        {
            CHECK(Near(t.widthYd, 3.f) && Near(t.overrunYd, 5.f) && Near(t.excludeYd, 4.f));
            CHECK(t.warnMs == 2000);
            CHECK(Near(t.minRangeYd, 8.f));
            // the 2 s warning allows at most 40% (shared doc section 4)
            CHECK(t.pct <= 40.f);
            CHECK(t.tag == TAG_MEAT_HOOK);
        }
        CHECK(Near(BleedTickPct(h), 5.f));
        CHECK(Near(BleedTickPct(n), 0.f));
        CHECK(h.bleedMs / h.bleedTickMs == 4);
        CHECK(Near(BleedTickPct(h) * static_cast<float>(h.bleedMs / h.bleedTickMs), h.bleedPct));
        // reference rows (normal 1,300 / heroic 4,120): the chop and the bleed tick
        CHECK(DungeonKit::RefFlatValue(1300, 1290, n.pct, false) == 455);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, h.pct, false) == 1442);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, BleedTickPct(h), false) == 206);
        CHECK(kHookFirstMs == 8000 && kHookEveryMs == 15000);
    }

    // Twin Hooks: distinct non-tanks at least 8 yd away; one when only one qualifies; none (skipped) when nobody is
    // 8 yd out; never the tank or melee; the `.sfktest` widen lets a lone tank (the GM) be picked.
    void TestHookPicks()
    {
        std::vector<DungeonKit::PickCandidate> const group{
            { 1, 3.f, true, true },     // the tank
            { 2, 4.f, false, true },    // melee
            { 3, 12.f, false, true },   // ranged
            { 4, 15.f, false, true },   // healer
            { 5, 9.f, false, false },   // ranged, no line of sight
        };
        for (std::uint32_t seed = 1; seed < 300; ++seed)
        {
            SeqRand rand{ seed };
            std::vector<std::size_t> const twin = PickHookTargets(group, HookFor(true), false, rand);
            CHECK(twin.size() == 2);
            std::set<std::uint64_t> ids;
            for (std::size_t i : twin)
            {
                CHECK(!group[i].tank);
                CHECK(group[i].distance >= 8.f);
                CHECK(group[i].inLos);
                ids.insert(group[i].id);
            }
            CHECK(ids.size() == twin.size());
            CHECK(ids.count(3) == 1 && ids.count(4) == 1);

            std::vector<std::size_t> const one = PickHookTargets(group, HookFor(false), false, rand);
            CHECK(one.size() == 1);
            CHECK(group[one.front()].id == 3 || group[one.front()].id == 4);
        }

        std::vector<DungeonKit::PickCandidate> const lone{ { 1, 3.f, true, true }, { 2, 10.f, false, true } };
        SeqRand rand{ 7 };
        CHECK(PickHookTargets(lone, HookFor(true), false, rand).size() == 1);

        std::vector<DungeonKit::PickCandidate> const close{ { 1, 3.f, true, true }, { 2, 5.f, false, true },
            { 3, 7.9f, false, true } };
        CHECK(PickHookTargets(close, HookFor(true), false, rand).empty());

        std::vector<DungeonKit::PickCandidate> const gmAlone{ { 1, 10.f, true, true } };
        CHECK(PickHookTargets(gmAlone, HookFor(false), false, rand).empty());
        CHECK(PickHookTargets(gmAlone, HookFor(false), true, rand).size() == 1);
    }

    // Lines from his spot run 5 yd past the target and stop inside the kitchen's walls, in every direction.
    void TestLineEndsInsideWalls()
    {
        DungeonKit::Arena const kitchen = RazorclawArena();
        Vec2 const from = kRazorclawSpawn.XY();
        HookTuning const t = HookFor(false);
        int clipped = 0;
        for (int deg = 0; deg < 360; deg += 5)
        {
            float const o = static_cast<float>(deg) * DungeonKit::kPi / 180.f;
            for (float d : { 8.f, 10.f, 13.f, 18.f })
            {
                Vec2 const target = DungeonKit::Advance(from, o, d);
                DungeonKit::LinePath const path = DungeonKit::LineStrikePath(from, target, t.overrunYd, 0.f,
                    &kitchen, kRazorclawSpawn.z, 0.5f);
                CHECK(kitchen.Contains(path.end, kRazorclawSpawn.z));
                CHECK(path.length <= d + t.overrunYd + 0.01f);
                CHECK(path.length > t.excludeYd);
                if (path.clipped)
                    ++clipped;
                else
                    CHECK(Near(path.length, d + t.overrunYd));
            }
        }
        CHECK(clipped > 0);     // the overrun reaches a wall in most directions (NAVMESH-REPORT s2)
    }

    // spell_sfk_meat_hook_once: a unit an earlier line of the same throw hit is not hit again; the next throw (15 s
    // later on Razorclaw, 5 s on the echo) starts clean; throwers are separate.
    void TestOncePerThrow()
    {
        HookVolleyMemory m;
        CHECK(!m.AlreadyHit(10, 1, 1000));
        m.Record(10, 1, 1000);
        CHECK(m.AlreadyHit(10, 1, 1000));          // the second line, same tick
        CHECK(!m.AlreadyHit(10, 2, 1000));
        CHECK(!m.AlreadyHit(11, 1, 1000));         // another thrower
        CHECK(m.AlreadyHit(10, 1, 1000 + HookVolleyMemory::kVolleyWindowMs));
        CHECK(!m.AlreadyHit(10, 1, 1001 + HookVolleyMemory::kVolleyWindowMs));
        m.Record(10, 2, 6000);                     // the next throw resets the list
        CHECK(!m.AlreadyHit(10, 1, 6000));
        CHECK(m.AlreadyHit(10, 2, 6000));
        CHECK(m.Throwers() == 1);
        m.Forget(10);
        CHECK(m.Throwers() == 0);
        CHECK(HookVolleyMemory::kVolleyWindowMs < 5000);
    }

    // "The pull lasts under 1 sec": the drag's flight over the kitchen's longest line (18.7 yd + overrun) and a short
    // one.
    void TestDrag()
    {
        HookTuning const t = HookFor(false);
        for (float d : { 2.f, 5.f, 8.f, 13.f, 18.7f, 23.7f, 32.7f })
        {
            float const speed = DragSpeedXY(d, t);
            CHECK(speed >= kDragMinSpeedXY);
            float const flight = JumpFlightMs(d, speed, kDragMinSpeedZ);
            CHECK(flight < 1000.f);
            CHECK(flight > 0.f);
        }
        CHECK(Near(DragSpeedXY(30.f, t), 40.f));
        CHECK(t.frontYd > 0.f && t.frontYd < kCutLengthYd);    // the drag lands in the Cut's cone
    }

    // RC2 / RC3: +10% per stack, the Cut at 3, the cone's tank check.
    void TestTenderizeAndCut()
    {
        CHECK(Near(TenderizedMultiplier(0), 1.f));
        CHECK(Near(TenderizedMultiplier(1), 1.1f));
        CHECK(Near(TenderizedMultiplier(2), 1.2f));
        CHECK(Near(TenderizedMultiplier(3), 1.3f));
        CHECK(Near(TenderizedMultiplier(9), 1.3f));
        // stacks 0, 1, 2 before the Cut: +10% on average over the three swings (SK "Tuning": "stacks average +10%")
        CHECK(Near((TenderizedMultiplier(0) + TenderizedMultiplier(1) + TenderizedMultiplier(2)) / 3.f, 1.1f));
        CHECK(kCutStacks == 3 && kTenderizeMaxStacks == kCutStacks);
        CHECK(Near(kCutPct(false), 40.f) && Near(kCutPct(true), 40.f));
        CHECK(Near(kCutTankWeaponPct, 250.f));
        CHECK(kCutWarnMs == 2000);
        CHECK(DungeonKit::RefFlatValue(1300, 1290, kCutPct(false), false) == 520);

        Vec2 const boss{ 0.f, 0.f };
        CHECK(InCutCone(boss, 0.f, { 3.f, 0.f }, 1.5f));           // the tank in front
        CHECK(InCutCone(boss, 0.f, { 6.f, 5.5f }, 0.f));           // 42 degrees off the axis
        CHECK(!InCutCone(boss, 0.f, { 3.f, 3.5f }, 0.f));          // 49 degrees off the axis
        CHECK(!InCutCone(boss, 0.f, { -3.f, 0.f }, 1.5f));         // behind him
        CHECK(!InCutCone(boss, 0.f, { 12.f, 0.f }, 1.5f));         // past 10 yd + reach
    }

    // Handoff section 5: "hook lines never within 3 s of a Cut". A simulated fight: his swing (none while a cast bar
    // runs, an overdue one at its end), a hook due every 15 s (retried every 250 ms while held), the Cut at 3 stacks;
    // every Cut starts at least 3 s after the last hook landed, no hook starts while a Cut is due or running, and
    // hooks keep coming.
    void TestRhythm()
    {
        for (std::uint32_t swingMs : { 3200u, 2000u, 4000u })
        {
            for (std::uint32_t firstSwingMs : { 0u, 1000u, 2500u })
            {
                Rhythm r;
                std::uint64_t castEnd = 0;
                std::uint64_t nextSwing = firstSwingMs;
                std::uint64_t nextHook = kHookFirstMs;
                std::uint32_t stacks = 0;
                std::uint64_t lastHookLand = 0;
                bool hooked = false;
                std::uint64_t cutResolveAt = 0;
                bool cutPending = false;
                int hooks = 0;
                int cuts = 0;
                for (std::uint64_t now = 0; now <= 180000; now += 50)
                {
                    if (cutPending && now >= cutResolveAt)
                    {
                        cutPending = false;
                        r.CutLanded();
                        stacks = 0;
                    }
                    if (now < castEnd)
                        continue;
                    if (r.CutMayStart(now, stacks))
                    {
                        CHECK(!hooked || now >= lastHookLand + kHookCutGapMs);
                        r.CutStarted(now, kCutWarnMs);
                        castEnd = now + kCutWarnMs;
                        cutResolveAt = now + kCutWarnMs;
                        cutPending = true;
                        ++cuts;
                        continue;
                    }
                    if (now >= nextHook)
                    {
                        if (!r.HookMayStart(now, stacks))
                        {
                            CHECK(stacks >= kHookDeferStacks || cutPending);
                            nextHook = now + kHookRetryMs;
                        }
                        else
                        {
                            CHECK(!cutPending && stacks < kCutStacks);
                            r.HookThrown(now, HookFor(false).warnMs);
                            hooked = true;
                            lastHookLand = now + HookFor(false).warnMs;
                            castEnd = now + HookFor(false).warnMs;
                            nextHook = now + kHookEveryMs;
                            ++hooks;
                            continue;
                        }
                    }
                    if (now >= nextSwing)
                    {
                        stacks = std::min(stacks + 1, kTenderizeMaxStacks);
                        nextSwing = now + swingMs;
                    }
                }
                CHECK(hooks >= 9);      // 180 s: one every 15 s, a little later when held
                CHECK(cuts >= 10);
            }
        }

        // the guard on its own
        Rhythm r;
        CHECK(r.HookMayStart(0, 0));
        CHECK(r.HookMayStart(0, 1));
        CHECK(!r.HookMayStart(0, 2));               // the Cut is one swing away
        CHECK(!r.CutMayStart(0, 2));
        CHECK(r.CutMayStart(0, 3));                 // no hook yet
        r.HookThrown(10000, 2000);                  // lands at 12 s
        CHECK(r.CutNotBeforeMs() == 15000);
        CHECK(!r.CutMayStart(14999, 3));
        CHECK(r.CutMayStart(15000, 3));
        r.CutStarted(15000, 2000);
        CHECK(!r.HookMayStart(16000, 0));           // casting
        CHECK(!r.CutMayStart(17000, 3));            // resolve not back yet
        CHECK(!r.HookMayStart(17500, 0));
        r.CutLanded();
        CHECK(r.HookMayStart(17500, 0));
        r.CutStarted(30000, 2000);                  // a resolve that never comes back stops holding after the grace
        CHECK(!r.HookMayStart(32000 + kCutResolveGraceMs - 1, 0));
        CHECK(r.HookMayStart(32000 + kCutResolveGraceMs, 0));
        r.Reset();
        CHECK(r.CutNotBeforeMs() == 0);
        CHECK(r.HookMayStart(0, 0));
    }

    // RC4: heroic only, 30 s, 5% a second; the three pools sit inside the 90 degree / 10 yd cone and inside the kitchen
    // for a Cut from his spot in every facing.
    void TestOffalSlick()
    {
        CHECK(!kOffalSlick(false) && kOffalSlick(true));
        CHECK(kSlickMs == 30000 && kSlickTickMs == 1000);
        CHECK(Near(kSlickPct, 5.f));
        DungeonKit::Arena const kitchen = RazorclawArena();
        Vec2 const boss = kRazorclawSpawn.XY();
        for (int deg = 0; deg < 360; deg += 15)
        {
            float const facing = static_cast<float>(deg) * DungeonKit::kPi / 180.f;
            for (Vec2 const& p : SlickPoolPoints(boss, facing))
            {
                CHECK(InCutCone(boss, facing, p, 0.f));
                CHECK(kitchen.Contains(p, kRazorclawSpawn.z));
            }
        }
    }
}

int main()
{
    TestSliceAndArena();
    TestHookTuning();
    TestHookPicks();
    TestLineEndsInsideWalls();
    TestOncePerThrow();
    TestDrag();
    TestTenderizeAndCut();
    TestRhythm();
    TestOffalSlick();
    return Report("sfk_razorclaw_test");
}
