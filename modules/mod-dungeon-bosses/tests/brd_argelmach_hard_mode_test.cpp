// Host tests for ArgelmachHardModeLogic.h (D16: Golem Lord Argelmach's hard mode, the Prototype): the slice, the
// spec's numbers, the wake order on D15's GolemsToWake, the wrecks and their cores, the Flamethrower cone and the
// cloud bursts, the console's refusals and spot.
#include "ArgelmachHardModeLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <string>

using namespace BlackrockDepthsRework;
using namespace BrdPrototype;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    ConsoleCheck Ready()
    {
        ConsoleCheck c;
        c.heroic = true;
        c.wave2Bound = true;
        c.argelmachAlive = true;
        c.argelmachState = DungeonKit::State::NotStarted;
        return c;
    }
}

int main()
{
    // ---- The slice (S0's checks kept): every spell inside it, inside the dungeon's reservation. ----
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 211370 && kSpellSlice.last == 211409);
    std::uint32_t const spells[] = { SPELL_PT_INCINERATION, SPELL_PT_INCINERATION_HIT, SPELL_PT_INCINERATION_LOOK,
        SPELL_PT_CLOUD_BURST, SPELL_PT_FLAMETHROWER, SPELL_PT_FLAMETHROWER_HIT, SPELL_PT_FLAMETHROWER_LOOK,
        SPELL_PT_SALVAGED_CORE };
    std::set<std::uint32_t> ids;
    for (std::uint32_t id : spells)
    {
        CHECK(kSpellSlice.Contains(id));
        ids.insert(id);
    }
    CHECK(ids.size() == std::size(spells));
    CHECK(*ids.begin() == 211370 && *ids.rbegin() == 211377);
    // Not D15's spells (its slice ends at 211369).
    CHECK(!kSpellsArgelmach.Contains(SPELL_PT_INCINERATION));
    // The hard mode's kill slot is its own and fights in its boss's arena.
    CHECK(IsHardModeSlot(BOSS_PROTOTYPE));
    CHECK(!ArenaFor(BOSS_PROTOTYPE).Empty());
    // The tags are the ones D15 reserved.
    CHECK(kTagIncineration == 6 && kTagFlamethrower == 7);

    // ---- The spec's numbers (S3 "Hard mode", the tuning table, handoff 3.6 / 7 #21). ----
    CHECK(kBossHealth == 500000 && kGolemHealth == 50000 && kMagmatronHealth == 100000);
    CHECK(kIncinerationFirstMs == 10000 && kIncinerationEveryMs == 25000 && kIncinerationCastMs == 3000);
    CHECK(Near(kIncinerationPct, 15.f) && Near(kBurstPct, 30.f) && Near(kBurstRadiusYd, 8.f));
    CHECK(kFlameFirstMs == 6000 && kFlameEveryMs == 15000 && kFlameWarnMs == 2000);
    CHECK(Near(kFlamePct, 35.f) && Near(kFlameAngleDeg, 60.f) && Near(kFlameLengthYd, 25.f));
    // The two bars cannot both start: 6 + 15n and 10 + 25n meet only within a bar (the retry handles it).
    CHECK(kRetryMs < kFlameEveryMs);

    // ---- AR4 (hard): 80 / 60 / 40, in D15's fixed order; one at a time; a big hit wakes all it passed. ----
    CHECK(Near(WakePct(Golem::Toxitron), 80.f));
    CHECK(Near(WakePct(Golem::Electron), 60.f));
    CHECK(Near(WakePct(Golem::Arcanoton), 40.f));
    {
        std::array<bool, BrdArgelmach::kGolemCount> woken{};
        CHECK(BrdArgelmach::GolemsToWake(100.f, kWakePct, woken).empty());
        CHECK(BrdArgelmach::GolemsToWake(85.f, kWakePct, woken).empty());     // D15's 90% no longer wakes Toxitron
        auto first = BrdArgelmach::GolemsToWake(80.f, kWakePct, woken);
        CHECK(first.size() == 1 && first[0] == Golem::Toxitron);
        woken[0] = true;
        CHECK(BrdArgelmach::GolemsToWake(61.f, kWakePct, woken).empty());
        auto big = BrdArgelmach::GolemsToWake(39.f, kWakePct, woken);
        CHECK(big.size() == 2 && big[0] == Golem::Electron && big[1] == Golem::Arcanoton);
    }
    // About 26 s between wakes at the hard mode's 4,440 DPS (S3: "about 26 s on hard mode (20%)").
    {
        float const gapS = (WakePct(Golem::Toxitron) - WakePct(Golem::Electron)) / 100.f * kBossHealth / 4440.f
            / 0.85f;
        CHECK(gapS > 24.f && gapS < 29.f);
    }

    // ---- AR13 the wrecks and their cores. ----
    CHECK(kWreckCount == 4);
    for (Golem g : BrdArgelmach::kGolems)
    {
        Wreck const w = WreckOf(g);
        CHECK(GolemOf(w) && *GolemOf(w) == g);
        Point3 const a = PedestalOf(w);
        Point3 const b = BrdArgelmach::PedestalOf(g);
        CHECK(Near(a.x, b.x) && Near(a.y, b.y) && Near(a.z, b.z));
        CHECK(CoreEveryMs(w) == 30000);
    }
    CHECK(!GolemOf(Wreck::Magmatron));
    CHECK(Near(PedestalOf(Wreck::Magmatron).x, BrdArgelmach::kPedestal4.x)
        && Near(PedestalOf(Wreck::Magmatron).y, BrdArgelmach::kPedestal4.y));
    // Half rate: the wreck's Incineration is twice the live one's; the golems' signatures at most half as often as on
    // heroic (Chemical Bomb 12 s, Lethal Attraction 15 s, the orb 15 s).
    CHECK(CoreEveryMs(Wreck::Magmatron) == 2 * kIncinerationEveryMs);
    CHECK(CoreEveryMs(Wreck::Toxitron) >= 2 * BrdArgelmach::kBombEveryMs(true));
    CHECK(CoreEveryMs(Wreck::Electron) == 2 * BrdArgelmach::kTetherEveryMs(true));
    CHECK(CoreEveryMs(Wreck::Arcanoton) == 2 * BrdArgelmach::kOrbEveryMs(true));
    CHECK(kCoreBombMarks == 1);
    CHECK(kCoreFirstMs > 0 && kCoreFirstMs < 30000);
    {
        std::set<std::string> names;
        for (Wreck w : kWrecks)
            names.insert(NameOf(w));
        CHECK(names.size() == kWreckCount);
    }

    // ---- The fourth pedestal and Magmatron: inside the chamber, apart from the other three, facing the middle. ----
    CHECK(BrdArgelmach::InChamber(BrdArgelmach::kPedestal4.XY()));
    for (Golem g : BrdArgelmach::kGolems)
        CHECK(DungeonKit::Distance(BrdArgelmach::PedestalOf(g).XY(), BrdArgelmach::kPedestal4.XY()) >= 14.f);
    {
        Vec2 const ahead = DungeonKit::Advance(BrdArgelmach::kPedestal4.XY(), MagmatronFacing(), 5.f);
        CHECK(DungeonKit::Distance(ahead, BrdArgelmach::kChamberMiddle)
            < DungeonKit::Distance(BrdArgelmach::kPedestal4.XY(), BrdArgelmach::kChamberMiddle));
    }

    // ---- AR12 the cone: 60 degrees, 25 yd, fixed toward the target. ----
    {
        Vec2 const apex = BrdArgelmach::kPedestal4.XY();
        Vec2 const target = BrdArgelmach::kChamberMiddle;
        float const bearing = DungeonKit::BearingTo(apex, target);
        CHECK(InFlamethrower(apex, bearing, target));                                   // the target itself
        CHECK(InFlamethrower(apex, bearing, DungeonKit::Advance(apex, bearing + 0.5f, 10.f)));     // 28.6 degrees
        CHECK(!InFlamethrower(apex, bearing, DungeonKit::Advance(apex, bearing + 0.55f, 10.f)));   // 31.5 degrees
        CHECK(InFlamethrower(apex, bearing, DungeonKit::Advance(apex, bearing, 24.9f)));
        CHECK(!InFlamethrower(apex, bearing, DungeonKit::Advance(apex, bearing, 25.2f)));
        CHECK(!InFlamethrower(apex, bearing, DungeonKit::Advance(apex, bearing + DungeonKit::kPi, 5.f)));   // behind
        // A player standing still on the target spot is hit; one 9 yd to the side at 10 yd out is clear (the dodge).
        CHECK(!InFlamethrower(apex, bearing, DungeonKit::Advance(DungeonKit::Advance(apex, bearing, 10.f),
            bearing + DungeonKit::kPi / 2.f, 9.f)));
    }

    // ---- AR11 the bursts: 8 yd round each ignited cloud (bigger than the 5 yd cloud: step well clear). ----
    {
        Vec2 const cloud{ 850.f, 20.f };
        CHECK(InBurst(cloud, cloud));
        CHECK(InBurst(cloud, Vec2{ 858.f, 20.f }));
        CHECK(!InBurst(cloud, Vec2{ 858.1f, 20.f }));
        CHECK(kBurstRadiusYd > BrdArgelmach::kCloudRadiusYd);
    }

    // ---- The console: outside the chamber by the passage mouth, near the fourth pedestal, facing it. ----
    CHECK(!BrdArgelmach::InChamber(kConsole.XY()));
    {
        float const toP4 = DungeonKit::Distance(kConsole.XY(), BrdArgelmach::kPedestal4.XY());
        CHECK(toP4 > 8.f && toP4 < 16.f);
        Vec2 const ahead = DungeonKit::Advance(kConsole.XY(), ConsoleFacing(), toP4);
        CHECK(DungeonKit::Distance(ahead, BrdArgelmach::kPedestal4.XY()) < 0.1f);
        CHECK(kConsole.z > BrdArgelmach::kChamberZMin && kConsole.z < BrdArgelmach::kChamberZMax);
    }

    // ---- The P4 statue is dormant by its state, never by an aura (R-2-A MA-1: the stock Stoned never landed, and the
    // idle hook re-summoned the statue every second). ----
    CHECK(StatueDormant(true, false, true));
    CHECK(!StatueDormant(false, false, true));      // dead: replaced (idle) or cleared (console)
    CHECK(!StatueDormant(true, true, true));        // fighting
    CHECK(!StatueDormant(true, false, false));      // woken at the pull, then a wipe: replaced

    // ---- The console's refusals (section 7 #15: heroic only, per pull, before the pull). ----
    CHECK(ConsoleRefusalFor(Ready()) == ConsoleRefusal::None);
    {
        ConsoleCheck c = Ready();
        c.heroic = false;
        CHECK(ConsoleRefusalFor(c) == ConsoleRefusal::NotHeroic);
        c = Ready();
        c.wave2Bound = false;
        CHECK(ConsoleRefusalFor(c) == ConsoleRefusal::NotBound);
        c = Ready();
        c.argelmachAlive = false;
        CHECK(ConsoleRefusalFor(c) == ConsoleRefusal::ArgelmachGone);
        c = Ready();
        c.argelmachState = DungeonKit::State::Done;
        CHECK(ConsoleRefusalFor(c) == ConsoleRefusal::ArgelmachGone);
        c = Ready();
        c.argelmachBusy = true;
        CHECK(ConsoleRefusalFor(c) == ConsoleRefusal::ArgelmachFighting);
        c = Ready();
        c.argelmachState = DungeonKit::State::InProgress;
        CHECK(ConsoleRefusalFor(c) == ConsoleRefusal::ArgelmachFighting);
        c = Ready();
        c.armed = true;
        CHECK(ConsoleRefusalFor(c) == ConsoleRefusal::Armed);
        // After a wipe (FAIL, or NOT_STARTED again) the instance has cleared the flag: usable again.
        c = Ready();
        c.argelmachState = DungeonKit::State::Fail;
        CHECK(ConsoleRefusalFor(c) == ConsoleRefusal::None);
    }
    // The instance's own gate agrees on every slot state (it refuses what the console refuses, and more never).
    for (std::uint32_t state : { DungeonKit::State::NotStarted, DungeonKit::State::InProgress, DungeonKit::State::Fail,
        DungeonKit::State::Done })
    {
        ConsoleCheck c = Ready();
        c.argelmachState = state;
        CHECK((ConsoleRefusalFor(c) == ConsoleRefusal::None) == ConsoleAllowed(1, true, true, state));
    }
    CHECK(ConsoleRefusalText(ConsoleRefusal::None)[0] == '\0');
    for (ConsoleRefusal r : { ConsoleRefusal::NotHeroic, ConsoleRefusal::NotBound, ConsoleRefusal::ArgelmachGone,
        ConsoleRefusal::ArgelmachFighting, ConsoleRefusal::Armed })
        CHECK(ConsoleRefusalText(r)[0] != '\0');

    return Report("brd_argelmach_hard_mode_test");
}
