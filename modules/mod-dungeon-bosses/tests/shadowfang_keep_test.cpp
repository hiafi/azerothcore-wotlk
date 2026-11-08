// Host tests for the Shadowfang Keep layer (WP-K): ShadowfangKeepRework.h (boss states, data ids, slices, the save
// string, the measured points and the arenas). Points are the handoff's section 3.8 / NAVMESH-REPORT values; DB
// positions (spawns, doors, levers, patrol points) are exact.
#include "ShadowfangKeepRework.h"
#include "check.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <functional>
#include <set>
#include <string>
#include <utility>
#include <vector>

using namespace ShadowfangKeepRework;

namespace
{
    bool Near(float a, float b, float tolerance)
    {
        return std::fabs(a - b) <= tolerance;
    }

    bool In(Arena const& arena, Point3 const& p)
    {
        return arena.Contains(p.XY(), p.z);
    }

    void TestBossStates()
    {
        // Hummel's BossAI writes boss slot 4 (stock DATA_APOTHECARY_HUMMEL): the table must keep it there.
        CHECK(BOSS_APOTHECARY_HUMMEL == 4);
        CHECK(kBossCount == 11);
        CHECK(BOSS_FACE_HIM_ALONE == kBossCount - 1);
        std::set<std::uint32_t> const ids{ BOSS_RETHILGORE, BOSS_RAZORCLAW, BOSS_SILVERLAINE, BOSS_SPRINGVALE,
            BOSS_APOTHECARY_HUMMEL, BOSS_ODO, BOSS_DEATHSWORN_CAPTAIN, BOSS_FENRUS, BOSS_NANDOS, BOSS_ARUGAL,
            BOSS_FACE_HIM_ALONE };
        CHECK(ids.size() == kBossCount);
        CHECK(*ids.rbegin() == kBossCount - 1);
        for (char const* name : kBossNames)
            CHECK(name && *name);
    }

    void TestDataIds()
    {
        // The stock ids the stock SmartAI and Hummel write keep their values.
        CHECK(DATA_COURTYARD == 0);
        CHECK(DATA_LEGACY_FENRUS == 1);
        CHECK(DATA_LEGACY_NANDOS == 2);
        CHECK(DATA_SPAWN_VALENTINE_ADDS == 5);
        // The prisoners' edited action lists (S9) write 21.
        CHECK(DATA_PRISONER == 21);
        std::set<std::uint32_t> const data{ DATA_COURTYARD, DATA_LEGACY_FENRUS, DATA_LEGACY_NANDOS,
            DATA_SPAWN_VALENTINE_ADDS, DATA_PRISONER, DATA_HARD_MODE, DATA_CAPTAIN_ROLL, DATA_HARD_MODE_KILLED };
        CHECK(data.size() == 8);
        CHECK(LairPrisonerEntry(Prisoner::Ashcrombe) == NPC_SFK_LAIR_ASHCROMBE);
        CHECK(LairPrisonerEntry(Prisoner::Adamant) == NPC_SFK_LAIR_ADAMANT);
        CHECK(LairPrisonerEntry(Prisoner::None) == 0);

        // R2 S-2: the guards' "another live boss" set: the nine bosses, nothing else.
        for (std::uint32_t const boss : { NPC_RETHILGORE, NPC_RAZORCLAW, NPC_SILVERLAINE, NPC_SPRINGVALE, NPC_ODO,
                 NPC_DEATHSWORN_CAPTAIN, NPC_FENRUS, NPC_NANDOS, NPC_ARUGAL })
            CHECK(IsSfkBossEntry(boss));
        for (std::uint32_t const other : { std::uint32_t(NPC_ADAMANT), std::uint32_t(NPC_SFK_LAIR_ASHCROMBE),
                 std::uint32_t(NPC_ARUGALS_VOIDWALKER), std::uint32_t(NPC_SFK_PACK_BLEAK_WORG), 0u })
            CHECK(!IsSfkBossEntry(other));

        // R1 S-1: the wait rule, asked on Nandos's DONE and after a load.
        CHECK(LairPrisonerWaits(DungeonKit::State::Done, DungeonKit::State::NotStarted, 0));
        CHECK(LairPrisonerWaits(DungeonKit::State::Done, DungeonKit::State::Fail, 0));
        CHECK(LairPrisonerWaits(DungeonKit::State::Done, DungeonKit::State::InProgress, 0));
        CHECK(!LairPrisonerWaits(DungeonKit::State::Done, DungeonKit::State::Done, 0));
        CHECK(!LairPrisonerWaits(DungeonKit::State::Done, DungeonKit::State::NotStarted, 1));
        CHECK(!LairPrisonerWaits(DungeonKit::State::NotStarted, DungeonKit::State::NotStarted, 0));
        CHECK(!LairPrisonerWaits(DungeonKit::State::ToBeDecided, DungeonKit::State::NotStarted, 0));

        // R2 N-6: the hard mode flag is not lit mid-fight, and never changes once Arugal is dead.
        CHECK(HardModeChangeAllowed(DungeonKit::State::NotStarted, 1));
        CHECK(HardModeChangeAllowed(DungeonKit::State::Fail, 1));
        CHECK(!HardModeChangeAllowed(DungeonKit::State::InProgress, 1));
        CHECK(HardModeChangeAllowed(DungeonKit::State::InProgress, 0));
        CHECK(!HardModeChangeAllowed(DungeonKit::State::Done, 0));
        CHECK(!HardModeChangeAllowed(DungeonKit::State::Done, 1));
        CHECK(kCaptainPresentChancePct == 15);
    }

    void TestSlices()
    {
        // The boss slices tile the reservation in order, with the spare at the end.
        std::uint32_t next = kSpellsReservation.first;
        for (IdSlice const& slice : kBossSpellSlices)
        {
            CHECK(slice.first == next);
            CHECK(slice.first <= slice.last);
            next = slice.last + 1;
        }
        CHECK(kSpellsSpare.first == next);
        CHECK(kSpellsSpare.last == kSpellsReservation.last);
        CHECK(kSpellsReservation.first == 205900 && kSpellsReservation.last == 206099);
        // Handoff section 3.4.
        CHECK(kSpellsRethilgore.first == 205910 && kSpellsRazorclaw.first == 205930);
        CHECK(kSpellsSilverlaine.first == 205945 && kSpellsSpringvale.first == 205965);
        CHECK(kSpellsOdo.first == 205990 && kSpellsDeathswornCaptain.first == 206010);
        CHECK(kSpellsFenrus.first == 206020 && kSpellsNandos.first == 206040 && kSpellsArugal.first == 206060);
        CHECK(kSpellsArugal.Contains(kSpellsFaceHimAlone.first) && kSpellsArugal.Contains(kSpellsFaceHimAlone.last));
        // The kit-wide spells are not ours.
        CHECK(!kSpellsReservation.Contains(DungeonKit::SPELL_KIT_CAST_BAR));
        CHECK(!kSpellsReservation.Contains(DungeonKit::SPELL_KIT_STANDING_IN_IT));

        for (std::uint32_t entry : { NPC_SFK_CELL_DOOR, NPC_SFK_SOUL_FRAGMENT, NPC_SFK_TAINTED_FRAGMENT,
            NPC_SFK_ECHO_OF_RETHILGORE, NPC_SFK_ECHO_OF_RAZORCLAW, NPC_SFK_ECHO_OF_ODO, NPC_SFK_GUARDSMAN_LIGHT,
            NPC_SFK_GUARDSMAN_HAMMER, NPC_SFK_GUARDSMAN_ALTAR, NPC_SFK_PACK_BLEAK_WORG, NPC_SFK_PACK_LUPINE_HORROR,
            NPC_SFK_PACK_SLAVERING_WORG, NPC_SFK_PACK_WOLFGUARD_WORG, NPC_SFK_LAIR_ASHCROMBE, NPC_SFK_LAIR_ADAMANT,
            NPC_SFK_WARD_STALKER, NPC_SFK_STRIKE_STALKER })
            CHECK(kCreaturesReservation.Contains(entry));
        CHECK(NPC_SFK_CELL_DOOR == 300500 && NPC_SFK_STRIKE_STALKER == 300516);
        CHECK(NPC_SFK_LAIR_ASHCROMBE == 300513 && NPC_SFK_LAIR_ADAMANT == 300514);
        CHECK(kGameObjectsReservation.Contains(GO_SFK_CELL_KEY));
        CHECK(kGameObjectsReservation.Contains(GO_SFK_ALARM_BELL));
    }

    void TestSaveString()
    {
        SfkSave save;
        for (std::size_t i = 0; i < kBossCount; ++i)
            save.states[i] = DungeonKit::State::NotStarted;
        save.states[BOSS_RETHILGORE] = DungeonKit::State::Done;
        save.states[BOSS_NANDOS] = DungeonKit::State::Done;
        save.states[BOSS_APOTHECARY_HUMMEL] = DungeonKit::State::Done;
        save.courtyard = DungeonKit::State::Done;
        save.prisoner = Prisoner::Adamant;
        save.hardMode = 1;
        save.captainRoll = DungeonKit::Roll::Absent;

        std::string const text = FormatSfkSave(save);
        CHECK(text == "S R 3 0 0 0 3 0 0 0 3 0 0 3 2 1 2");

        SfkSave back;
        CHECK(ParseSfkSave(text, back));
        CHECK(back.states == save.states);
        CHECK(back.courtyard == DungeonKit::State::Done);
        CHECK(back.prisoner == Prisoner::Adamant);
        CHECK(back.hardMode == 1);
        CHECK(back.captainRoll == DungeonKit::Roll::Absent);

        // A stock save ("S K <courtyard> <fenrus> <nandos>") is ignored (handoff section 7 #2).
        CHECK(!ParseSfkSave("S K 3 3 0", back));
        CHECK(!ParseSfkSave("", back));
        CHECK(!ParseSfkSave("S R", back));

        // In-progress states never survive a reload; out-of-range fields fall back.
        CHECK(ParseSfkSave("S R 1 2 4 5 3 0 0 0 0 0 0 2 9 7 9", back));
        CHECK(back.states[0] == DungeonKit::State::NotStarted);
        CHECK(back.states[1] == DungeonKit::State::NotStarted);
        CHECK(back.states[2] == DungeonKit::State::NotStarted);
        CHECK(back.states[3] == DungeonKit::State::NotStarted);
        CHECK(back.states[4] == DungeonKit::State::Done);
        CHECK(back.courtyard == DungeonKit::State::NotStarted);
        CHECK(back.prisoner == Prisoner::None);
        CHECK(back.hardMode == 1);
        CHECK(back.captainRoll == DungeonKit::Roll::Unrolled);

        // A shorter save (an older build) leaves the tail at its defaults.
        CHECK(ParseSfkSave("S R 3 3", back));
        CHECK(back.states[0] == DungeonKit::State::Done && back.states[1] == DungeonKit::State::Done);
        CHECK(back.states[2] == DungeonKit::State::NotStarted);
        CHECK(back.captainRoll == DungeonKit::Roll::Unrolled && back.hardMode == 0);
    }

    void TestReportFrames()
    {
        // ReportPoint inverts the report's own conversion (keep grid: x = x0 - 0.367u + 0.930v,
        // y = y0 - 0.930u - 0.367v).
        Vec2 const o{ -247.8f, 2125.2f };
        Vec2 const p = ReportPoint(o, kKeepUp, 9.45f, 3.3f);
        CHECK(Near(p.x, -247.8f - 0.367f * 9.45f + 0.930f * 3.3f, 0.05f));
        CHECK(Near(p.y, 2125.2f - 0.930f * 9.45f - 0.367f * 3.3f, 0.05f));
        // Springvale's frame: x = x0 + 0.259u + 0.966v, y = y0 - 0.966u + 0.259v.
        Vec2 const s = ReportPoint(kSpringvaleSpawn.XY(), kSpringvaleUp, -5.f, -9.f);
        CHECK(Near(s.x, -222.6f + 0.259f * -5.f + 0.966f * -9.f, 0.05f));
        CHECK(Near(s.y, 2259.4f - 0.966f * -5.f + 0.259f * -9.f, 0.05f));
        // The S door sits 9.4 yd right of the M door on the door line (v ~ 0).
        Vec2 const q = DungeonKit::ToFrame(ReportFrame(o, kKeepUp), kCellDoors[CELL_S].XY());
        CHECK(Near(q.x, 0.f, 0.2f));
        CHECK(Near(-q.y, 9.4f, 0.2f));
    }

    void TestCellBlock()
    {
        Arena const corridor = CorridorArena();
        std::array<Arena, kCellCount> const cells{ { CellArena(CELL_S), CellArena(CELL_M), CellArena(CELL_N) } };
        Arena const room = RethilgoreArena();

        CHECK(In(corridor, kRethilgoreSpawn));
        CHECK(In(room, kRethilgoreSpawn));
        for (std::size_t c = 0; c < kCellCount; ++c)
        {
            CHECK(!In(cells[c], kRethilgoreSpawn));
            // The landing point is in its own cell only.
            for (std::size_t o = 0; o < kCellCount; ++o)
                CHECK(In(cells[o], kCellLandings[c]) == (o == c));
            CHECK(!In(corridor, kCellLandings[c]));
            // The lever is on the corridor side; the point in front of the door is in the corridor.
            CHECK(In(corridor, kCellLevers[c]));
            Vec2 const out = InFrontOfCell(CellId(c));
            CHECK(corridor.Contains(out, kCellBlockFloorZ));
            for (Arena const& cell : cells)
                CHECK(!cell.Contains(out, kCellBlockFloorZ));
            CHECK(Near(DungeonKit::Distance(out, kCellDoors[c].XY()), 2.5f, 0.01f));
        }
        // The stock occupants (DB): Adamant S, Ashcrombe M, Stilwell N.
        CHECK(In(cells[CELL_S], { -243.7f, 2113.7f, 81.3f }));
        CHECK(In(cells[CELL_M], { -240.9f, 2122.6f, 81.3f }));
        CHECK(In(cells[CELL_N], { -239.5f, 2132.8f, 81.3f }));
        CHECK(kCellOccupants[CELL_S] == NPC_ADAMANT && kCellOccupants[CELL_M] == NPC_ASHCROMBE);

        // Fragment points: corridor side, 3 to 6.5 yd from their door, at least 2 yd apart.
        auto fragments = [&](CellId c, std::vector<Vec2> const& points)
        {
            for (std::size_t i = 0; i < points.size(); ++i)
            {
                CHECK(corridor.Contains(points[i], kCellBlockFloorZ));
                float const d = DungeonKit::Distance(points[i], kCellDoors[c].XY());
                CHECK(d >= 3.f && d <= 6.5f);
                for (std::size_t j = i + 1; j < points.size(); ++j)
                    CHECK(DungeonKit::Distance(points[i], points[j]) >= 2.f);
            }
        };
        fragments(CELL_S, { kFragmentPointsS.begin(), kFragmentPointsS.end() });
        fragments(CELL_M, { kFragmentPointsM.begin(), kFragmentPointsM.end() });
        fragments(CELL_N, { kFragmentPointsN.begin(), kFragmentPointsN.end() });

        // Key landings: in the corridor, 8 to 12 yd from him.
        for (Point3 const& k : kKeyLandings)
        {
            CHECK(In(corridor, k));
            float const d = DungeonKit::Distance(k.XY(), kRethilgoreSpawn.XY());
            CHECK(d >= 8.f && d <= 12.f);
        }
        // The stair at the corridor's WNW end (z 87) is off the arena.
        CHECK(!room.Contains(kRethilgoreSpawn.XY(), 87.f));
    }

    struct NamedArena
    {
        char const* name;
        std::function<Arena()> make;
        Point3 spawn;
    };

    void TestBossArenas()
    {
        std::vector<NamedArena> const arenas{
            { "rethilgore", RethilgoreArena, kRethilgoreSpawn },
            { "razorclaw", RazorclawArena, kRazorclawSpawn },
            { "silverlaine", SilverlaineArena, kSilverlaineSpawn },
            { "springvale", SpringvaleArena, kSpringvaleSpawn },
            { "odo", OdoArena, kOdoSpawn },
            { "captain", DeathswornCaptainArena, kCaptainSpawn },
            { "fenrus", FenrusArena, kFenrusSpawn },
            { "nandos", NandosArena, kNandosSpawn },
            { "arugal", ArugalArena, kArugalSpawn },
        };
        // Every boss stands in his own arena and in no other.
        for (NamedArena const& a : arenas)
            for (NamedArena const& b : arenas)
                CHECK(In(b.make(), a.spawn) == (a.name == b.name));
    }

    void TestRoomPoints()
    {
        Arena const springvale = SpringvaleArena();
        for (Point3 const& p : kGuardsmanRisePoints)
        {
            CHECK(In(springvale, p));
            float const d = DungeonKit::Distance(p.XY(), kSpringvaleSpawn.XY());
            CHECK(d >= 9.5f && d <= 15.f);
        }

        Arena const odo = OdoArena();
        CHECK(In(odo, kOdoDoor));
        for (std::size_t i = 0; i < kBellSpots.size(); ++i)
        {
            CHECK(In(odo, kBellSpots[i]));
            for (std::size_t j = i + 1; j < kBellSpots.size(); ++j)
                CHECK(DungeonKit::Distance(kBellSpots[i].XY(), kBellSpots[j].XY()) >= 19.f);
        }

        // The Captain's patrol (path 1345170, DB): every point on his arena (north hall plus walkway); point 5 is in
        // Odo's doorway.
        Arena const captain = DeathswornCaptainArena();
        std::array<Point3, 10> const path{ { { -191.9f, 2124.7f, 97.4f }, { -203.3f, 2100.5f, 97.4f },
            { -213.8f, 2098.0f, 97.4f }, { -239.9f, 2108.1f, 97.4f }, { -245.8f, 2110.5f, 100.0f },
            { -239.8f, 2107.8f, 97.4f }, { -212.2f, 2097.5f, 97.4f }, { -202.2f, 2102.7f, 97.4f },
            { -187.1f, 2133.9f, 97.4f }, { -190.0f, 2128.5f, 97.4f } } };
        for (Point3 const& p : path)
            CHECK(In(captain, p));
        // The inner yard under the walkway (z 77 to 81) is off it.
        CHECK(!captain.Contains(path[3].XY(), 79.f));

        Arena const fenrus = FenrusArena();
        for (Vec2 const& p : kFenrusStrikePoints)
        {
            CHECK(fenrus.Contains(p, kFenrusFloorZ));
            CHECK(DungeonKit::Distance(p, kFenrusSpawn.XY()) >= 7.f);
        }
        CHECK(In(fenrus, kFenrusBaitPoint));
        CHECK(DungeonKit::Distance(kFenrusBaitPoint.XY(), kFenrusSpawn.XY()) >= 25.f);
        CHECK(!In(fenrus, kSorcerersGate));     // the gate is in the exit passage

        Arena const nandos = NandosArena();
        for (Point3 const& p : kPackSpawns)
            CHECK(In(nandos, p));
        CHECK(In(nandos, kNandosOpenPoint));
        CHECK(In(nandos, kLairPrisonerWait));
        CHECK(In(nandos, kArugalsLairDoor));
        Point3 const arugalSideOfDoor{ -115.8f, 2160.8f, 155.8f };
        CHECK(!In(nandos, arugalSideOfDoor));

        Arena const arugal = ArugalArena();
        CHECK(In(arugal, arugalSideOfDoor));
        CHECK(!In(arugal, kLairPrisonerWait));
        // The two spots S9 uses (7587 is dropped as unreachable and lies outside the arena).
        CHECK(In(arugal, kShadowPortSpots[0]));
        CHECK(In(arugal, kShadowPortSpots[1]));
        CHECK(!In(arugal, kShadowPortSpots[2]));
        CHECK(In(arugal, kLairPrisonerGallery));
        // Fenrus's room is right below Nandos's; neither arena reaches the other's floor.
        CHECK(!nandos.Contains(kFenrusSpawn.XY(), kFenrusSpawn.z));
        CHECK(!fenrus.Contains(kNandosOpenPoint.XY(), kNandosOpenPoint.z));
    }
}

int main()
{
    TestBossStates();
    TestDataIds();
    TestSlices();
    TestSaveString();
    TestReportFrames();
    TestCellBlock();
    TestBossArenas();
    TestRoomPoints();
    return Report("shadowfang_keep_test");
}
