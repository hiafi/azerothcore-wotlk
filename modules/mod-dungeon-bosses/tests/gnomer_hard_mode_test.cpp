// Host tests for ThermapluggHardModeLogic.h (D6Ha, the Whole Workshop part a): the ids and their slice, the tags of
// the Whole Workshop's block, MT15's lines, the dose arithmetic (ruling 49) and D2's halving rule as the plates use it,
// the venting count, the Reactor Leak's clock, the Wandering Puddle's drift and judge, the console's refusals.
// Constants read from other WPs' headers are named with their owner: ThermapluggLogic.h (D6), ViscousFalloutLogic.h
// (D2), GnomereganRework.h (S0).
#include "ThermapluggHardModeLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <string>
#include <vector>

using namespace GnomereganRework;
using namespace GnomerWorkshop;

namespace
{
    // A small deterministic generator (no <random>): the puddle walk's jitter.
    struct Lcg
    {
        std::uint32_t state = 12345;

        float Next(float lo, float hi)
        {
            state = state * 1664525u + 1013904223u;
            return lo + (hi - lo) * float(state >> 8) / float(1u << 24);
        }
    };

    void TestIdsAndSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation (S0).
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 214540 && kSpellSlice.last == 214579);
        std::set<std::uint32_t> ids;
        for (std::uint32_t const id : { std::uint32_t(SPELL_HM_IRRADIATED), std::uint32_t(SPELL_HM_DOSE_GLOW),
                std::uint32_t(SPELL_HM_DUPLICATION), std::uint32_t(SPELL_HM_VENT), std::uint32_t(SPELL_HM_PUDDLE),
                std::uint32_t(SPELL_HM_MELTDOWN), std::uint32_t(SPELL_HM_MELTDOWN_AURA),
                std::uint32_t(SPELL_HM_REACTOR_LEAK), std::uint32_t(SPELL_HM_LEAK_AURA) })
        {
            CHECK(kSpellSlice.Contains(id));
            ids.insert(id);
        }
        CHECK(ids.size() == 9);
        CHECK(*ids.rbegin() == kLastSpell);
        CHECK(kLastSpell - kSpellSlice.first + 1 == ids.size());   // no gap
        // D6's own spells (ThermapluggLogic.h) are never reused.
        CHECK(!kSpellSlice.Contains(GnomerThermaplugg::SPELL_MT_LOCKED_OUT));
        // The console's slice stays untouched (S0's kSpellsConsoleAndSpare).
        CHECK(!kSpellsConsoleAndSpare.Contains(kLastSpell));
        // the units (S0's enum)
        CHECK(NPC_WANDERING_PUDDLE == 301135 && NPC_ROOM_ALARM == 301137 && NPC_VENT_STALKER == 301138);
        CHECK(GO_CLEARANCE_CONSOLE == 301382);
        CHECK(kCreaturesReservation.Contains(NPC_WANDERING_PUDDLE));
        CHECK(kGameObjectsReservation.Contains(GO_CLEARANCE_CONSOLE));
    }

    void TestTags()
    {
        std::set<std::uint32_t> mine;
        for (DrillTag const& t : kDrillTags)
        {
            CHECK(t.tag >= GnomerThermaplugg::kFirstPackageTag && t.tag <= GnomerThermaplugg::kFirstPackageTag + 9);
            for (std::uint32_t const b : kPartBTags)
                CHECK(t.tag != b);
            mine.insert(t.tag);
        }
        CHECK(mine.size() == kDrillTags.size());
        CHECK(TAG_HM_PUDDLE == 81);     // BM MechanicDrill.h kGnTagHmPuddles (G1)
        CHECK(!mine.count(86));         // F-1d: the dose claim's own Soak group is gone (the plates are D6's, tag 71)
        CHECK(!mine.count(GnomerThermaplugg::TAG_MT_PLATE));
        // D6's own tags (70-79) are below the block.
        for (GnomerThermaplugg::DrillTag const& t : GnomerThermaplugg::kDrillTags)
            CHECK(t.tag < GnomerThermaplugg::kFirstPackageTag);
    }

    void TestSchematics()
    {
        // Ruling 45: part a's 90 / 75 (D6Hb's 60 / 45 / 30 are its own), kill order.
        CHECK(SchematicAt(90.f) == Schematic::Techbot);
        CHECK(SchematicAt(75.f) == Schematic::ViscousFallout);
        CHECK(!SchematicAt(60.f) && !SchematicAt(45.f) && !SchematicAt(30.f));
        CHECK(!SchematicAt(50.f));
        CHECK(!SchematicAt(0.f));
        CHECK(kSchematicPct[1] < kSchematicPct[0]);
        // MT15's lines: the yell is his package group (D6), the console's line D6Hb's form.
        CHECK(SAY_HM_SCHEMATIC == 9);
        CHECK(LoadLine(Schematic::Techbot) == "Loading schematic: TECHBOT");
        CHECK(LoadLine(Schematic::ViscousFallout) == "Loading schematic: VISCOUS FALLOUT");
        CHECK(Tune::kConsoleLineYd == 120.f);
        CHECK(kAlarmLastGroup == ALARM_FAILURE && ALARM_FAILURE == 4);
    }

    void TestDose()
    {
        // Ruling 49 / SP: a 70% blast is 89% at 9 dose and kills from full at 15 (70 x 1.45 = 101.5).
        float const blast = GnomerThermaplugg::Tune::kBombBlastPct[2];      // D6: the hard mode's 70%
        CHECK(blast == 70.f);
        CHECK(std::lround(blast * DamageTakenFactor(9)) == 89);
        CHECK(blast * DamageTakenFactor(15) >= 100.f);
        CHECK(blast * DamageTakenFactor(14) < 100.f);
        CHECK(DamageTakenFactor(0) == 1.f);
        // The plates halve it with D2's one rule (loses half, rounded up): 9 -> 4, 10 -> 5, 1 -> 0.
        CHECK(GnomerFallout::Halve(9) == 4 && GnomerFallout::Halve(10) == 5 && GnomerFallout::Halve(1) == 0);
        // SP rate check: a player who touches a plate each lockout swings between about 6 and 11.
        CHECK(GnomerFallout::Halve(11) <= 6);
        // The bots shed from 8, before Leaking at 10 and Meltdown at 20 (SP MT18).
        CHECK(Tune::kPlateDoseFloor == 8 && Tune::kLeakAt == 10 && Tune::kMeltdownAt == 20);
        CHECK(Tune::kAuraStackLimit == GnomerFallout::Tune::kAuraStackLimit);
        // MT17: 1 dose a player per open face.
        CHECK(VentDoses(0) == 0 && VentDoses(1) == 1 && VentDoses(6) == 6);
        GnomerThermaplugg::FaceMask open{};
        open[1] = open[4] = true;
        CHECK(VentDoses(GnomerThermaplugg::OpenCount(open)) == 2);
        // A vent only with the Fallout schematic and the face open.
        CHECK(VentWanted(true, true) && !VentWanted(false, true) && !VentWanted(true, false));
        // MT16's numbers (SP 1837) and the warning floor.
        CHECK(Tune::kDupFirstMs == 10000 && Tune::kDupRepeatMs == 10000 && Tune::kDupCastMs == 2000);
        CHECK(Tune::kDupCapAlive == 0);
        CHECK(Tune::kCastingBombPriority > GnomerThermaplugg::Tune::kBombTargetPriority);
    }

    void TestBeats()
    {
        // RB-17: a beat never fires twice in one tick and never starves.
        // One rule (RB-16, STAGE-R-1-C Nit-1): D6's NextDue(due, period, now); this header has no copy of its own.
        using GnomerThermaplugg::NextDue;
        CHECK(NextDue(8000, 8000, 8000) == 16000);
        CHECK(NextDue(8000, 8000, 30000) == 34000);
        // A 180 s pull at 8 s: 22 pulses from 8 s.
        std::uint64_t due = 8000;
        std::uint32_t pulses = 0;
        for (std::uint64_t now = 0; now <= 180000; now += 100)
            if (now >= due)
            {
                ++pulses;
                due = NextDue(due, Tune::kVentEveryMs, now);
            }
        CHECK(pulses == 22);
    }

    void TestLeakClock()
    {
        CHECK(Tune::kLeakStartMs == 180000);
        CHECK(!LeakOn(179999) && LeakOn(180000));
        CHECK(AlarmsDue(59999, 0).empty());
        std::vector<std::uint8_t> due = AlarmsDue(60000, 0);
        CHECK(due.size() == 1 && due[0] == ALARM_TWO_MINUTES);
        // Each line once, in order, even when the clock jumps.
        due = AlarmsDue(171000, 0x1);
        CHECK(due.size() == 3 && due[0] == ALARM_ONE_MINUTE && due[1] == ALARM_THIRTY && due[2] == ALARM_TEN);
        CHECK(AlarmsDue(175000, 0x0F).empty());
        // 2 min, 1 min, 30 s and 10 s left.
        for (std::size_t i = 0; i < Tune::kAlarmAtMs.size(); ++i)
            CHECK(Tune::kAlarmAtMs[i] < Tune::kLeakStartMs);
        CHECK(Tune::kLeakStartMs - Tune::kAlarmAtMs[0] == 120000 && Tune::kLeakStartMs - Tune::kAlarmAtMs[3] == 10000);
        CHECK(Tune::kLeakPct == 10.f && Tune::kLeakTickMs == 1000);
    }

    void TestPuddles()
    {
        Arena const room = RoomArena();
        // A drift that starts anywhere on the bowl stays on the floor, leg after leg (the turn at the walls).
        Lcg rng;
        std::uint32_t legs = 0;
        std::uint32_t stuck = 0;
        for (int start = 0; start < 40; ++start)
        {
            float const a = rng.Next(0.f, 2.f * kPi);
            float const r = rng.Next(0.f, 30.f);
            Vec2 at{ kRoomCenter.x + std::cos(a) * r, kRoomCenter.y + std::sin(a) * r };
            float const z = kRoomCenter.z;
            CHECK(room.Contains(at, z));
            float heading = rng.Next(0.f, 2.f * kPi);
            for (int step = 0; step < 60; ++step)
            {
                PuddleLeg const leg = NextPuddleLeg(room, at, z, heading,
                    rng.Next(-Tune::kPuddleBounceJitterDeg, Tune::kPuddleBounceJitterDeg));
                if (!leg.moved)
                {
                    ++stuck;
                    continue;
                }
                CHECK(LegInside(room, at, leg.to, z));
                float const dx = leg.to.x - at.x;
                float const dy = leg.to.y - at.y;
                CHECK(std::fabs(std::sqrt(dx * dx + dy * dy) - Tune::kPuddleLegYd) < 0.01f);
                at = leg.to;
                heading = leg.heading;
                ++legs;
            }
        }
        CHECK(legs > 2000);
        CHECK(stuck == 0);
        // Straight on while the floor goes on.
        Vec2 const center = kRoomCenter.XY();
        PuddleLeg const straight = NextPuddleLeg(room, center, kRoomCenter.z, 0.f, 0.f);
        CHECK(straight.moved && straight.heading == 0.f);
        // At a wall it turns back.
        Vec2 const nearWall{ center.x + std::cos(kPi / 2.f) * 36.f, center.y + std::sin(kPi / 2.f) * 36.f };
        if (room.Contains(nearWall, kRoomCenter.z))
        {
            PuddleLeg const bounce = NextPuddleLeg(room, nearWall, kRoomCenter.z, kPi / 2.f, 0.f, 30.f);
            CHECK(bounce.moved);
            CHECK(std::cos(bounce.heading - kPi / 2.f) < 0.f);
        }
        // The 2 yd/s drift covers a leg in 4 s, under the snag timeout.
        CHECK(Tune::kPuddleLegYd / Tune::kPuddleSpeedYdPerSec * 1000.f < float(Tune::kPuddleLegTimeoutMs));
        // The judge: armed after 1.5 s, 4 yd 2D, z band.
        std::vector<PuddleSpot> spots{ { { 0.f, 0.f }, 0.f, 1000 } };
        CHECK(!InAnyPuddle(spots, { 1.f, 1.f }, 0.f, 2000));    // still forming
        CHECK(InAnyPuddle(spots, { 1.f, 1.f }, 0.f, 2500));
        CHECK(InAnyPuddle(spots, { 4.f, 0.f }, 0.f, 2500));
        CHECK(!InAnyPuddle(spots, { 4.1f, 0.f }, 0.f, 2500));
        CHECK(!InAnyPuddle(spots, { 0.f, 0.f }, 7.f, 2500));
        spots.push_back({ { 6.f, 0.f }, 0.f, 0 });
        CHECK(InAnyPuddle(spots, { 5.f, 0.f }, 0.f, 2500));     // overlapping puddles: one tick, not two (the caller)
        // The puddle's disc is WP-V's 4 yd scale.
        CHECK(std::fabs(Tune::kPuddleDiscScale - 0.8333f) < 0.001f);
        // Ruling 52: 2 min each; SP: 2 yd/s, 8% and 1 dose a second.
        CHECK(Tune::kPuddleLifeMs == 120000 && Tune::kPuddlePct == 8.f && Tune::kPuddleDose == 1);
    }

    void TestConsole()
    {
        // The console spot is in the room (S0) and the screen has a line for every refusal but a bot's.
        CHECK(ArenaFor(BOSS_WHOLE_WORKSHOP).Contains(kConsoleSpot.XY(), kConsoleSpot.z));
        for (ConsoleVerdict const v : { CONSOLE_NOT_HEROIC, CONSOLE_IN_COMBAT, CONSOLE_NO_CARD, CONSOLE_BOSS_ENGAGED,
                CONSOLE_ALREADY_SET })
            CHECK(ConsoleRefusalText(v)[0] != '\0');
        CHECK(ConsoleRefusalText(CONSOLE_BOT)[0] == '\0');
        CHECK(ConsoleRefusalText(CONSOLE_ACCEPTED)[0] == '\0');
        // STAGE-R-1-C Nit-3: a dead Thermaplugg reads its own line, not "already at work".
        CHECK(std::string(ConsoleRefusalText(CONSOLE_BOSS_ENGAGED, true)) == kConsoleBossDone);
        CHECK(std::string(ConsoleRefusalText(CONSOLE_BOSS_ENGAGED, false)) != kConsoleBossDone);
        CHECK(std::string(ConsoleRefusalText(CONSOLE_NO_CARD, true)) != kConsoleBossDone);
        // S0's rule: a bot never sets it, even with every other condition met (rule 34).
        CHECK(ConsoleCheck(true, true, false, true, DungeonKit::State::NotStarted, 0) == CONSOLE_BOT);
        CHECK(ConsoleCheck(true, false, false, true, DungeonKit::State::NotStarted, 0) == CONSOLE_ACCEPTED);
        CHECK(kConsoleGossipMenu == 5300022 && kConsoleNpcText == 900029);
    }

    // F-1d (STAGE-R-1-C Minor-1, DQ1, the BM-G note): the plates' plan while the Fallout schematic runs.
    PlatePlayer Bot(std::uint64_t guid, std::uint32_t dose, Vec2 at, bool tank = false)
    {
        PlatePlayer p;
        p.guid = guid;
        p.dose = dose;
        p.bot = true;
        p.tank = tank;
        p.eligible = true;
        p.at = at;
        return p;
    }

    void TestPlatePlan()
    {
        // DQ1: the tank sheds last, unless it is the only one at 8 or more.
        Vec2 const o{ 0.f, 0.f };
        CHECK(TankPlatesLast({}));
        CHECK(TankPlatesLast({ Bot(1, 3, o, true), Bot(2, 2, o) }));          // nobody at 8: SP MT4, tank last
        CHECK(!TankPlatesLast({ Bot(1, 12, o, true), Bot(2, 7, o) }));        // only the tank at 8+: it goes
        CHECK(TankPlatesLast({ Bot(1, 15, o, true), Bot(2, 8, o) }));         // another at 8+: the tank waits
        PlatePlayer human = Bot(3, 9, o);
        human.bot = false;
        CHECK(TankPlatesLast({ Bot(1, 15, o, true), human }));                // any other player at 8+ counts
        PlatePlayer out = Bot(2, 9, o);
        out.eligible = false;                                                 // Locked Out: not eligible
        CHECK(!TankPlatesLast({ Bot(1, 15, o, true), out }));

        // R-1-C's case: P1 (rank 0) and P2 (rank 2) lit, bot B (9) next to P1, bot A (12) next to P2. Rank order
        // alone sends A to P1 and B to P2; the plan serves P2 first (A's), then P1 (B's): each at its nearest plate.
        std::vector<LitPlate> const two{ { 0, { 0.f, 0.f }, 0 }, { 2, { 40.f, 0.f }, 2 } };
        std::vector<PlatePlayer> const ab{ Bot(10, 9, { 2.f, 0.f }), Bot(11, 12, { 38.f, 0.f }) };
        CHECK(PlatePlan(two, ab, true) == std::vector<std::uint32_t>({ 2, 0 }));
        // Nobody at 8: face priority (rank, then face), every lit plate once.
        CHECK(PlatePlan(two, { Bot(10, 7, { 39.f, 0.f }) }, true) == std::vector<std::uint32_t>({ 0, 2 }));
        // One dose bot, two plates: its nearest first, the other after.
        CHECK(PlatePlan(two, { Bot(10, 8, { 39.f, 0.f }) }, true) == std::vector<std::uint32_t>({ 2, 0 }));
        // Two dose bots nearest the same plate: the higher dose takes it, the other the next nearest.
        std::vector<LitPlate> const three{ { 0, { 0.f, 0.f }, 0 }, { 1, { 20.f, 0.f }, 1 }, { 3, { 60.f, 0.f }, 3 } };
        CHECK(PlatePlan(three, { Bot(10, 9, { 1.f, 0.f }), Bot(11, 14, { 2.f, 0.f }) }, true)
            == std::vector<std::uint32_t>({ 0, 1, 3 }));
        CHECK(PlatePlan(three, { Bot(10, 9, { 59.f, 0.f }), Bot(11, 14, { 21.f, 0.f }) }, true)
            == std::vector<std::uint32_t>({ 1, 3, 0 }));
        // More dose bots than plates: every plate once.
        CHECK(PlatePlan(two, { Bot(10, 9, o), Bot(11, 10, o), Bot(12, 11, o) }, true).size() == 2);
        // The tank: left out while it is last, planned with the others when it sheds.
        std::vector<PlatePlayer> const tank{ Bot(1, 15, { 39.f, 0.f }, true), Bot(2, 9, { 1.f, 0.f }) };
        CHECK(TankPlatesLast(tank));
        CHECK(PlatePlan(two, tank, true) == std::vector<std::uint32_t>({ 0, 2 }));
        std::vector<PlatePlayer> const alone{ Bot(1, 15, { 39.f, 0.f }, true), Bot(2, 5, { 1.f, 0.f }) };
        CHECK(!TankPlatesLast(alone));
        CHECK(PlatePlan(two, alone, false) == std::vector<std::uint32_t>({ 2, 0 }));
        // Humans and Locked Out bots are never planned (BM sends bots only; Locked Out is excluded).
        CHECK(PlatePlan(two, { human, out }, true) == std::vector<std::uint32_t>({ 0, 2 }));
        CHECK(PlatePlan({}, ab, true).empty());
    }
}

int main()
{
    TestIdsAndSlice();
    TestTags();
    TestSchematics();
    TestDose();
    TestBeats();
    TestLeakClock();
    TestPuddles();
    TestConsole();
    TestPlatePlan();
    return Report("gnomer_hard_mode_test");
}
