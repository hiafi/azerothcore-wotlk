// Host tests for GraduateExamLogic.h (S13: Darkmaster Gandling's hard mode, the Graduate Exam): the Passing Grade
// displays, the paper's refusals, the examiners' numbers, the rooms (spawns, landings, Gandling's region in each), his
// gauntlet modes, the room order and the gauntlet's steps; plus the Polkelt examiner's first batch (S13's hook there).
#include "GraduateExamLogic.h"
#include "PolkeltLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <set>
#include <string>

using namespace ScholomanceRework;
using namespace ScholoGraduateExam;

namespace
{
    bool InArena(Arena const& arena, Point4 const& p)
    {
        return arena.Contains(p.XY(), p.z);
    }

    // A fixed "random" pick: always the last index.
    std::size_t Last(std::size_t n)
    {
        return n - 1;
    }

    std::size_t First(std::size_t)
    {
        return 0;
    }

    void TestSpells()
    {
        std::set<std::uint32_t> ids;
        for (std::size_t i = 0; i < kInstructorCount; ++i)
        {
            std::uint32_t const id = PassingGradeSpell(Instructor(i));
            CHECK(kSpellSlice.Contains(id));
            CHECK(id == 206365 + i);
            ids.insert(id);
        }
        CHECK(ids.size() == kInstructorCount);
        CHECK(PassingGradeSpell(Instructor::Malicia) == SPELL_GE_GRADE_MALICIA);
        CHECK(PassingGradeSpell(Instructor::Illucia) == SPELL_GE_GRADE_ILLUCIA);
        CHECK(kSpellsReservation.Contains(kSpellSlice.first) && kSpellsReservation.Contains(kSpellSlice.last));
    }

    void TestGradeAuras()
    {
        GradeAuraChange c = GradeAuraDiff(0b000101, 0);
        CHECK(c.add == 0b000101 && c.remove == 0);
        c = GradeAuraDiff(0b000101, 0b000101);
        CHECK(c.add == 0 && c.remove == 0);
        c = GradeAuraDiff(0, 0b100001);         // the grades were cleared (a test command): the auras come off
        CHECK(c.add == 0 && c.remove == 0b100001);
        c = GradeAuraDiff(0b111111, 0b000011);
        CHECK(c.add == 0b111100 && c.remove == 0);
        c = GradeAuraDiff(0xFFFFFFFF, 0);       // unknown bits never become auras
        CHECK(c.add == kAllGradesMask);

        // The display follows the instance's table.
        PassingGrades g;
        g.Award(42, Instructor::Polkelt);
        g.Award(42, Instructor::Alexei);
        CHECK(GradeAuraDiff(g.MaskOf(42), 0).add == ((1u << 2) | (1u << 4)));
        CHECK(GradeAuraDiff(g.MaskOf(7), 0).add == 0);
    }

    void TestPaper()
    {
        PaperState ok;
        ok.heroic = true;
        ok.revealed = true;
        ok.honorsOpen = true;
        CHECK(CheckPaper(ok) == PaperRefusal::None);

        PaperState s = ok;
        s.heroic = false;
        CHECK(CheckPaper(s) == PaperRefusal::NotHeroic);
        s = ok;
        s.revealed = false;
        CHECK(CheckPaper(s) == PaperRefusal::NotRevealed);
        s = ok;
        s.gandlingState = DungeonKit::State::Done;
        CHECK(CheckPaper(s) == PaperRefusal::GandlingDone);
        s.revealed = false;                     // dead outranks hidden
        CHECK(CheckPaper(s) == PaperRefusal::GandlingDone);
        s = ok;
        s.gandlingState = DungeonKit::State::InProgress;
        CHECK(CheckPaper(s) == PaperRefusal::GandlingBusy);
        s = ok;
        s.gandlingEngaged = true;
        CHECK(CheckPaper(s) == PaperRefusal::GandlingBusy);
        s = ok;
        s.examRunning = true;
        CHECK(CheckPaper(s) == PaperRefusal::GandlingBusy);
        s = ok;
        s.honorsOpen = false;
        CHECK(CheckPaper(s) == PaperRefusal::HonorsClosed);

        // The instance's own rule agrees: a signature needs the honors open, heroic, revealed and an idle Gandling.
        CHECK(GandlingHardModeChangeAllowed(1, true, true, true, DungeonKit::State::NotStarted));
        CHECK(!GandlingHardModeChangeAllowed(1, true, true, true, DungeonKit::State::InProgress));
        // A wipe clears it (any time before his death); the kill keeps it.
        CHECK(GandlingHardModeChangeAllowed(0, true, true, true, DungeonKit::State::InProgress));
        CHECK(!GandlingHardModeChangeAllowed(0, true, true, true, DungeonKit::State::Done));
    }

    void TestNumbers()
    {
        CHECK(kFinalHealth == 200000);
        CHECK(ExaminerHealth(NPC_SC_EXAMINER_MALICIA) == 80000);
        CHECK(ExaminerHealth(NPC_SC_EXAMINER_KRASTINOV) == 80000);
        CHECK(ExaminerHealth(NPC_SC_EXAMINER_POLKELT) == 80000);
        CHECK(ExaminerHealth(NPC_SC_EXAMINER_RAVENIAN) == 60000);
        CHECK(ExaminerHealth(NPC_SC_EXAMINER_CORVANE) == 20000);
        CHECK(ExaminerHealth(NPC_SC_EXAMINER_ALEXEI) == 80000);
        CHECK(ExaminerHealth(NPC_SC_EXAMINER_ILLUCIA) == 80000);
        CHECK(ExaminerHealth(NPC_GANDLING) == 0);
        // The instructors' own examiner numbers agree.
        CHECK(ScholoPolkelt::kExaminerHealth == kExaminerHealth);
        CHECK(kOpenDelayMs == 5000 && kPortalDelayMs == 5000);

        // S13's hook in Polkelt (orchestrator default, S7 Q2): the examiner's first batch at 4 s, the boss's at 10 s.
        CHECK(ScholoPolkelt::ProfileFor(true, true).firstBatchMs == 4000);
        CHECK(ScholoPolkelt::ProfileFor(false, true).firstBatchMs == 4000);
        CHECK(ScholoPolkelt::ProfileFor(true, false).firstBatchMs == ScholoPolkelt::kFirstBatchMs);
        CHECK(ScholoPolkelt::ProfileFor(false, false).firstBatchMs == 10000);
    }

    void TestRooms()
    {
        std::set<std::uint32_t> examiners;
        for (std::size_t i = 0; i < kClassroomCount; ++i)
        {
            Classroom const c = Classroom(i);
            ExamRoom const& r = ExamRoomOf(c);
            Arena const arena = ClassroomArena(c);
            CHECK(r.room == c);
            // The room's examiner is the one Gandling's detention rule looks for (the Ravenian brings Corvane).
            CHECK(ScholoGandling::ExaminersOf(c).front() == r.examiner);
            CHECK(ExaminerHealth(r.examiner) > 0);
            examiners.insert(r.examiner);

            // The examiner stands on the instructor's spawn, in this room's arena only.
            CHECK(InArena(arena, r.examinerSpawn));
            for (std::size_t j = 0; j < kClassroomCount; ++j)
                if (j != i)
                    CHECK(!InArena(ClassroomArena(Classroom(j)), r.examinerSpawn));
            CHECK(!InArena(GandlingArena(), r.examinerSpawn));

            // The group lands in the room's arena and on its floor, 20 yd or more from the examiner, and every spot of
            // the ring around the landing is there too.
            for (std::size_t k = 0; k < 7; ++k)
            {
                Point4 const spot = SpreadLanding(r.groupLanding, k);
                CHECK(InArena(arena, spot));
                CHECK(InArena(RoomFloorArena(c), spot));
                CHECK(!InArena(GandlingArena(), spot));
                CHECK(DungeonKit::Distance(spot.XY(), r.groupLanding.XY()) <= kGroupSpreadYd + 0.01f);
            }
            CHECK(DungeonKit::Distance(r.groupLanding.XY(), r.examinerSpawn.XY()) >= 20.f);
            CHECK(r.floorZ >= arena.ZMin() && r.floorZ <= arena.ZMax());

            // Gandling's region in the room: its players are the room's arena, 8 distinct portal points on the walls of
            // its floor, and a lane from every portal through the landing has length and stays on the floor.
            ScholoGandling::GandlingRegion const region = RoomRegion(c);
            CHECK(region.players.Contains(r.groupLanding.XY(), r.groupLanding.z));
            CHECK(region.portalPoints.size() == 4 * kPortalsPerSide);
            CHECK(region.floorZ == r.floorZ);
            for (std::size_t a = 0; a < region.portalPoints.size(); ++a)
            {
                DungeonKit::Vec2 const p = region.portalPoints[a];
                CHECK(region.clip.Contains(p, r.floorZ));
                for (std::size_t b = a + 1; b < region.portalPoints.size(); ++b)
                    CHECK(DungeonKit::Distance(p, region.portalPoints[b]) > 1.f);
                DungeonKit::LinePath const lane = ScholoGandling::VolleyLane(region, p, r.groupLanding.XY());
                CHECK(lane.length > 0.f);
                CHECK(region.clip.Contains(lane.end, r.floorZ));
            }
        }
        CHECK(examiners.size() == kClassroomCount);
        CHECK(!examiners.count(NPC_SC_EXAMINER_CORVANE));       // the examiner Ravenian seats his own

        // The final phase's landing is the study.
        for (std::size_t k = 0; k < 7; ++k)
        {
            Point4 const spot = SpreadLanding(kStudyReturn, k);
            CHECK(InArena(GandlingArena(), spot));
            CHECK(InArena(ScholoGandling::StudyFloorArena(), spot));
            for (std::size_t j = 0; j < kClassroomCount; ++j)
                CHECK(!InArena(ClassroomArena(Classroom(j)), spot));
        }
        CHECK(DungeonKit::Distance(kStudyReturn.XY(), kGandlingSpawn.XY()) > 10.f);
    }

    void TestEdgePoints()
    {
        DungeonKit::FrameRect const f{ { 0.f, 0.f }, 0.f, 30.f, 10.f };
        std::vector<DungeonKit::Vec2> const pts = FrameEdgePoints(f, 2, 1.5f);
        CHECK(pts.size() == 8);
        for (DungeonKit::Vec2 const& p : pts)
        {
            CHECK(p.x >= 1.5f - 0.01f && p.x <= 28.5f + 0.01f);
            CHECK(p.y >= 1.5f - 0.01f && p.y <= 8.5f + 0.01f);
            bool const onWall = std::fabs(p.x - 1.5f) < 0.01f || std::fabs(p.x - 28.5f) < 0.01f
                || std::fabs(p.y - 1.5f) < 0.01f || std::fabs(p.y - 8.5f) < 0.01f;
            CHECK(onWall);
        }
        CHECK(FrameEdgePoints(f, 0, 1.5f).empty());
    }

    void TestModes()
    {
        ScholoGandling::GandlingMode const g = GauntletMode();
        CHECK(!g.detention);                    // SC GD5: no Detention in the gauntlet
        CHECK(!g.needsVictim);                  // he is in the study, the group in a classroom
        CHECK(g.volley && g.volleyPortals == 3 && g.lingerMs == 4000 && !g.lanesThroughEveryone);
        CHECK(g.volleyFirstMs == ScholoGandling::kVolleyFirstMs && g.volleyEveryMs == ScholoGandling::kVolleyEveryMs);
        CHECK(g.transfer && g.transferTankEligible && !g.transferRaisesExpelled);
        CHECK(g.transferFirstMs == ScholoGandling::kTransferFirstMs);

        ScholoGandling::GandlingMode const idle = IdleMode();
        CHECK(!idle.detention && !idle.volley && !idle.transfer && !idle.needsVictim);

        ScholoGandling::GandlingMode const f = ScholoGandling::FinalExamMode();
        CHECK(!f.detention && f.lanesThroughEveryone && f.needsVictim);
        CHECK(f.transfer && f.transferEveryMs == 15000 && f.transferRaisesExpelled);
        CHECK(f.volleyEveryMs == 20000 && f.lingerMs == 4000);
    }

    void TestOrder()
    {
        std::array<Classroom, kClassroomCount> o = ExamOrder(Last);
        std::set<Classroom> seen(o.begin(), o.end());
        CHECK(seen.size() == kClassroomCount);
        o = ExamOrder(First);
        seen = std::set<Classroom>(o.begin(), o.end());
        CHECK(seen.size() == kClassroomCount);
        for (std::size_t r = 0; r < kClassroomCount; ++r)
        {
            std::array<Classroom, kClassroomCount> const led = ExamOrder(First, int(r));
            CHECK(led[0] == Classroom(r));
            CHECK(std::set<Classroom>(led.begin(), led.end()).size() == kClassroomCount);
        }
        CHECK(ExamOrder(Last, 9) == ExamOrder(Last));
    }

    std::array<Classroom, kClassroomCount> Order()
    {
        return { { Classroom::Coven, Classroom::HallOfTheDamned, Classroom::HallOfSecrets, Classroom::RavenianVault,
            Classroom::BarovVault, Classroom::ShadowVault } };
    }

    void TestGauntlet()
    {
        ExamInputs none;
        GauntletRun run;
        CHECK(!run.Running());
        CHECK(run.Update(1000, none) == ExamAction::None);

        run.Start(Order());
        CHECK(run.Running() && run.Phase() == ExamPhase::Opening);
        CHECK(run.Update(kOpenDelayMs - 1, none) == ExamAction::None);
        CHECK(run.Update(1, none) == ExamAction::SendToRoom);
        CHECK(run.Room() == Classroom::Coven && run.RoomsCleared() == 0);

        for (std::size_t room = 0; room < kClassroomCount; ++room)
        {
            CHECK(run.Phase() == ExamPhase::Arriving);
            CHECK(run.Room() == Order()[room]);
            CHECK(run.Update(100, none) == ExamAction::None);
            ExamInputs arrived;
            arrived.arrived = true;
            CHECK(run.Update(100, arrived) == ExamAction::PullExaminer);
            CHECK(run.Phase() == ExamPhase::Examining);
            CHECK(run.Update(30000, none) == ExamAction::None);   // no clock while the examiner fights
            ExamInputs dead;
            dead.examinerDead = true;
            CHECK(run.Update(100, dead) == ExamAction::RoomCleared);
            CHECK(run.RoomsCleared() == room + 1);
            CHECK(run.Update(kPortalDelayMs - 1, none) == ExamAction::None);
            ExamAction const next = run.Update(1, none);
            CHECK(next == (room + 1 < kClassroomCount ? ExamAction::SendToRoom : ExamAction::ReturnToStudy));
        }
        CHECK(run.Phase() == ExamPhase::Returning && run.RoomsCleared() == kClassroomCount);
        CHECK(run.Update(kArrivalTimeoutMs - 1, none) == ExamAction::None);
        CHECK(run.Update(1, none) == ExamAction::StartFinal);     // the arrival times out: he is pulled anyway
        CHECK(run.Phase() == ExamPhase::Final);
        CHECK(run.Update(60000, none) == ExamAction::None);
        ExamInputs won;
        won.gandlingDead = true;
        CHECK(run.Update(100, won) == ExamAction::Passed);
        CHECK(!run.Running() && run.Phase() == ExamPhase::Passed);
        CHECK(run.Update(100, won) == ExamAction::None);

        // The arrival times out into the pull.
        run.Start(Order());
        run.Update(kOpenDelayMs, none);
        CHECK(run.Update(kArrivalTimeoutMs, none) == ExamAction::PullExaminer);

        // Wipes: nobody alive in any phase, an examiner lost, Gandling lost in the final phase.
        ExamInputs wiped;
        wiped.anyAlive = false;
        run.Start(Order());
        CHECK(run.Update(10, wiped) == ExamAction::Wipe);
        CHECK(!run.Running() && run.Phase() == ExamPhase::Idle);

        run.Start(Order());
        run.Update(kOpenDelayMs, none);
        run.Update(kArrivalTimeoutMs, none);
        ExamInputs lost;
        lost.examinerLost = true;
        CHECK(run.Update(10, lost) == ExamAction::Wipe);
        CHECK(!run.Running());

        run.Start(Order());
        run.Update(kOpenDelayMs, none);
        run.Update(kArrivalTimeoutMs, none);
        ExamInputs both;                        // a kill on the same tick as an evade counts as the kill
        both.examinerDead = true;
        both.examinerLost = true;
        CHECK(run.Update(10, both) == ExamAction::RoomCleared);

        run.SkipToStudy();
        CHECK(run.Update(1, none) == ExamAction::ReturnToStudy);
        run.Update(kArrivalTimeoutMs, none);
        CHECK(run.Phase() == ExamPhase::Final);
        ExamInputs gone;
        gone.gandlingLost = true;
        CHECK(run.Update(10, gone) == ExamAction::Wipe);
        CHECK(!run.Running());

        // A wipe while the portal is open, or on the way back.
        run.Start(Order());
        run.Update(kOpenDelayMs, none);
        run.Update(kArrivalTimeoutMs, none);
        ExamInputs killed;
        killed.examinerDead = true;
        run.Update(10, killed);
        CHECK(run.Phase() == ExamPhase::Portal);
        CHECK(run.Update(10, wiped) == ExamAction::Wipe);

        CHECK(std::string(PhaseName(ExamPhase::Examining)) == "examining");
    }
}

int main()
{
    TestSpells();
    TestGradeAuras();
    TestPaper();
    TestNumbers();
    TestRooms();
    TestEdgePoints();
    TestModes();
    TestOrder();
    TestGauntlet();
    CHECK(!PassingGrades().HonorsOpen());

    return Report("scholo_exam_test");
}
