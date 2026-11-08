// Host tests for the Scholomance kit (WP-KS): ScholomanceRework.h (boss states, data ids, instructors and classrooms,
// slices, measured points, arenas, Gandling's reveal, the keepsake and hard mode rules, the Passing Grades, the save
// string and its stock reader) and SoloLessonLogic.h (the lesson clock and the safety stops). DB positions (spawns,
// gates, landings) are exact; the rest is the NAVMESH-REPORT's.
#include "ScholomanceRework.h"
#include "SoloLessonLogic.h"
#include "check.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <set>
#include <string>
#include <vector>

using namespace ScholomanceRework;

namespace
{
    bool In(Arena const& arena, Point4 const& p)
    {
        return arena.Contains(p.XY(), p.z);
    }

    bool In(Arena const& arena, Point3 const& p)
    {
        return arena.Contains(p.XY(), p.z);
    }

    std::array<Point4, kBossCount> const kSpawnByBoss{ {
        kJandiceSpawn, kRattlegoreSpawn, kVectusSpawn, kGandlingSpawn, kRasSpawn, kMaliciaSpawn, kKrastinovSpawn,
        kPolkeltSpawn, kRavenianSpawn, kAlexeiSpawn, kIlluciaSpawn } };

    void TestBossStates()
    {
        CHECK(kBossCount == 11);
        CHECK(BOSS_GANDLING == 3);      // the stock Gandling BossAI's slot
        std::set<std::uint32_t> const ids{ BOSS_JANDICE, BOSS_RATTLEGORE, BOSS_MARDUK_VECTUS, BOSS_GANDLING, BOSS_RAS,
            BOSS_MALICIA, BOSS_KRASTINOV, BOSS_POLKELT, BOSS_RAVENIAN, BOSS_ALEXEI, BOSS_ILLUCIA };
        CHECK(ids.size() == kBossCount);
        CHECK(*ids.rbegin() == kBossCount - 1);
        for (char const* name : kBossNames)
            CHECK(name && *name);
    }

    void TestDataIds()
    {
        // The stock ids the stock scripts write keep their values.
        CHECK(DATA_KIRTONOS_THE_HERALD == 0);
        CHECK(DATA_MINI_BOSSES == 1);
        CHECK(DATA_RAS_HUMAN == 2);
        CHECK(DATA_DARKMASTER_GANDLING == 3);
        std::set<std::uint32_t> data{ DATA_KIRTONOS_THE_HERALD, DATA_MINI_BOSSES, DATA_RAS_HUMAN,
            DATA_DARKMASTER_GANDLING, DATA_KEEPSAKE_PAGE, DATA_KEEPSAKE_PAGE_COUNT, DATA_KEEPSAKE_BOUND,
            DATA_RAS_HARD_MODE, DATA_RAS_HARD_MODE_KILLED, DATA_GANDLING_HARD_MODE, DATA_GANDLING_HARD_MODE_KILLED,
            DATA_GANDLING_REVEALED, DATA_HONORS_OPEN };
        CHECK(data.size() == 13);
        for (std::size_t i = 0; i < kInstructorCount; ++i)
            data.insert(DataGradeHolders(Instructor(i)));
        for (std::size_t i = 0; i < kClassroomCount; ++i)
            data.insert(DataClassroomGate(Classroom(i)));
        CHECK(data.size() == 13 + kInstructorCount + kClassroomCount);

        // Guid ids: ObjectData slots, the grade and detention ranges; none is a stock GetGuidData key (an entry).
        std::set<std::uint32_t> guids{ DATA_JANDICE_GUID, DATA_RATTLEGORE_GUID, DATA_MARDUK_GUID, DATA_VECTUS_GUID,
            DATA_RAS_GUID, DATA_MALICIA_GUID, DATA_KRASTINOV_GUID, DATA_POLKELT_GUID, DATA_RAVENIAN_GUID,
            DATA_ALEXEI_GUID, DATA_ILLUCIA_GUID, DATA_GANDLING_GUID, DATA_VIEWING_ROOM_DOOR_GUID,
            DATA_GANDLING_ENTRANCE_GUID, DATA_EMBALMING_FLUID_GUID };
        for (std::size_t i = 0; i < kClassroomCount; ++i)
        {
            guids.insert(DataClassroomGateGuid(Classroom(i)));
            guids.insert(DataDetained(Classroom(i)));
        }
        for (std::size_t i = 0; i < kInstructorCount; ++i)
            guids.insert(DataPassingGrade(Instructor(i)));
        CHECK(guids.size() == 15 + 2 * kClassroomCount + kInstructorCount);
        for (std::uint32_t g : guids)
            CHECK(g < NPC_GANDLING && g < GO_BRAZIER_KIRTONOS);
    }

    void TestInstructorsAndClassrooms()
    {
        std::set<std::uint32_t> bosses;
        std::set<int> rooms;
        for (std::size_t i = 0; i < kInstructorCount; ++i)
        {
            Instructor const who = Instructor(i);
            std::uint32_t const boss = InstructorBoss(who);
            bosses.insert(boss);
            CHECK(InstructorOfBoss(boss).has_value() && *InstructorOfBoss(boss) == who);
            Classroom const room = InstructorClassroom(who);
            rooms.insert(int(room));
            CHECK(ClassroomInstructor(room) == who);
            CHECK(ClassroomOfGate(ClassroomGate(room)) == room);
        }
        CHECK(bosses.size() == kInstructorCount);
        CHECK(rooms.size() == kClassroomCount);
        for (std::uint32_t boss : { BOSS_JANDICE, BOSS_RATTLEGORE, BOSS_MARDUK_VECTUS, BOSS_GANDLING, BOSS_RAS })
            CHECK(!InstructorOfBoss(boss).has_value());
        CHECK(!ClassroomOfGate(GO_GATE_GANDLING_ENTRANCE).has_value());

        // The stock order of boss_darkmaster_gandling.cpp (GandlingGateIds / GandlingPortalSpells / SummonPos).
        CHECK(ClassroomGate(Classroom::ShadowVault) == 177371);
        CHECK(ClassroomGate(Classroom::BarovVault) == 177373);
        CHECK(ClassroomGate(Classroom::RavenianVault) == 177372);
        CHECK(ClassroomGate(Classroom::HallOfSecrets) == 177376);
        CHECK(ClassroomGate(Classroom::HallOfTheDamned) == 177377);
        CHECK(ClassroomGate(Classroom::Coven) == 177375);
        CHECK(kClassroomPortalSpells[std::size_t(Classroom::ShadowVault)] == 17944);
        CHECK(kClassroomPortalSpells[std::size_t(Classroom::Coven)] == 17943);
        CHECK(InstructorClassroom(Instructor::Illucia) == Classroom::ShadowVault);
        CHECK(InstructorClassroom(Instructor::Malicia) == Classroom::Coven);
    }

    void TestSlices()
    {
        // Contiguous, inside the reservation, no overlap, covering it exactly.
        std::uint32_t next = kSpellsReservation.first;
        for (IdSlice const& s : kSpellSlices)
        {
            CHECK(s.first == next);
            CHECK(s.last >= s.first);
            CHECK(kSpellsReservation.Contains(s.first) && kSpellsReservation.Contains(s.last));
            next = s.last + 1;
        }
        CHECK(next == kSpellsReservation.last + 1);
        CHECK(kSpellsReservation.first == 206100 && kSpellsReservation.last == 206399);

        for (std::uint32_t c : { NPC_SC_REFLECTION, NPC_SC_LOOSE_PART, NPC_SC_UNFINISHED_CONSTRUCT, NPC_SC_GRADUATE,
                 NPC_SC_BLIZZARD_ANCHOR, NPC_SC_ICE_TOMB, NPC_SC_MALICIAS_SHADE, NPC_SC_LOOSE_SOUL, NPC_SC_WORK_BENCH,
                 NPC_SC_FAILED_PATIENT, NPC_SC_UNSTABLE_SPECIMEN, NPC_SC_ROOTED_SPECIMEN, NPC_SC_MASTER_CORVANE,
                 NPC_SC_BAROV_FORTUNE, NPC_SC_EXPELLED_STUDENT, NPC_SC_RAVENIANS_ECHO, NPC_SC_LESSON_STALKER,
                 NPC_SC_PORTAL_STALKER, NPC_SC_EXAMINER_MALICIA, NPC_SC_EXAMINER_ILLUCIA })
            CHECK(kCreaturesReservation.Contains(c));
        CHECK(NPC_SC_EXAMINER_ILLUCIA - NPC_SC_EXAMINER_MALICIA == 6);
        for (std::uint32_t go : { GO_SC_TORN_PAGE, GO_SC_KEEPSAKE_BOOK, GO_SC_KEEPSAKE_BOOK_BOUND, GO_SC_HONORS_PAPER,
                 GO_SC_ALCHEMY_TABLE })
            CHECK(kGameObjectsReservation.Contains(go));

        std::set<std::uint32_t> entries{ NPC_JANDICE, NPC_RATTLEGORE, NPC_MARDUK, NPC_VECTUS, NPC_RAS, NPC_MALICIA,
            NPC_KRASTINOV, NPC_POLKELT, NPC_RAVENIAN, NPC_ALEXEI, NPC_ILLUCIA, NPC_GANDLING };
        CHECK(entries.size() == 12);
        for (std::uint32_t e : entries)
            CHECK(IsScholoBossEntry(e));
        CHECK(!IsScholoBossEntry(NPC_KIRTONOS));
        CHECK(!IsScholoBossEntry(NPC_SC_MASTER_CORVANE));
    }

    void TestArenas()
    {
        // Each boss spawns inside his own arena and no other (the z bands keep the stacked rooms apart).
        for (std::uint32_t own = 0; own < kBossCount; ++own)
            for (std::uint32_t other = 0; other < kBossCount; ++other)
                CHECK(In(ArenaFor(other), kSpawnByBoss[own]) == (own == other));
        CHECK(In(ViewingRoomArena(), kMardukSpawn));

        // Every classroom gate lies outside its instructor's arena (the gate keeps the fight in, the leash backs it).
        for (std::size_t i = 0; i < kClassroomCount; ++i)
            CHECK(!In(ClassroomArena(Classroom(i)), kClassroomGatePoints[i]));
        // The three lower gates lie inside Gandling's arena (shut while he fights), the upper three and the entrance
        // do not.
        CHECK(In(GandlingArena(), kClassroomGatePoints[std::size_t(Classroom::ShadowVault)]));
        CHECK(In(GandlingArena(), kClassroomGatePoints[std::size_t(Classroom::BarovVault)]));
        CHECK(In(GandlingArena(), kClassroomGatePoints[std::size_t(Classroom::RavenianVault)]));
        CHECK(!In(GandlingArena(), kClassroomGatePoints[std::size_t(Classroom::HallOfSecrets)]));
        CHECK(!In(GandlingArena(), kClassroomGatePoints[std::size_t(Classroom::HallOfTheDamned)]));
        CHECK(!In(GandlingArena(), kClassroomGatePoints[std::size_t(Classroom::Coven)]));
        CHECK(!In(GandlingArena(), kGandlingEntranceGate));

        // Every detention landing (spell_target_position) is in its classroom's arena and no other boss's.
        for (std::size_t i = 0; i < kClassroomCount; ++i)
            for (std::uint32_t boss = 0; boss < kBossCount; ++boss)
                CHECK(In(ArenaFor(boss), kClassroomLandings[i])
                    == (boss == InstructorBoss(ClassroomInstructor(Classroom(i)))));

        // The measured points of each room are in its arena.
        for (Point3 const& p : kConstructSpots)
            CHECK(In(RattlegoreArena(), p));
        CHECK(!In(RattlegoreArena(), Point3{ 163.0f, 171.0f, 109.0f }));    // the stair top, on the hatchling floor
        for (Point3 const& p : kRootedSpecimenSpots)
            CHECK(In(PolkeltArena(), p));
        for (Point3 const& p : kCorvaneLandings)
            CHECK(In(RavenianArena(), p));
        CHECK(In(KrastinovArena(), kFailedPatientRise));
        CHECK(In(IlluciaArena(), kIlluciaHallPoint));
        CHECK(In(RasArena(), Point3{ kEmbalmingFluid.x, kEmbalmingFluid.y, kEmbalmingFluid.z }));
        for (Vec2 const& v : kStudyPortalPoints)
            CHECK(GandlingArena().Contains(v, kStudyFloorZ));
        for (Vec2 const& v : kJandiceSigilGrid)
            CHECK(JandiceArena().Contains(v, kJandiceFloorZ));
        for (Vec2 const& v : kBarovDesks)
            CHECK(AlexeiArena().Contains(v, 75.0f));
        // The user's seat "right behind the Ravenian" lies in his vault.
        CHECK(In(RavenianArena(), kRavenianUserSpot));
        // Page 3 lies in the Viewing Room; the book, the table and the honors paper are in no boss arena.
        CHECK(In(ViewingRoomArena(), kKeepsakePages[2]));
        for (std::uint32_t boss = 0; boss < kBossCount; ++boss)
        {
            CHECK(!In(ArenaFor(boss), kKeepsakePages[0]) && !In(ArenaFor(boss), kKeepsakePages[1]));
            CHECK(!In(ArenaFor(boss), kKeepsakeBook));
            CHECK(!In(ArenaFor(boss), kHardModeTable));
            CHECK(!In(ArenaFor(boss), kHonorsPaper));
        }
        CHECK(ArenaFor(kBossCount).Empty());
    }

    void TestReveal()
    {
        std::array<std::uint32_t, kBossCount> states{};
        CHECK(InstructorsDone(states) == 0);
        CHECK(!GandlingRevealed(states));
        // The non-instructor bosses never count (stock: Jandice, Rattlegore, Marduk, Vectus and Ras never sent it).
        for (std::uint32_t b : { BOSS_JANDICE, BOSS_RATTLEGORE, BOSS_MARDUK_VECTUS, BOSS_RAS, BOSS_GANDLING })
            states[b] = DungeonKit::State::Done;
        CHECK(InstructorsDone(states) == 0);
        for (std::size_t i = 0; i < kInstructorCount; ++i)
        {
            CHECK(!GandlingRevealed(states));
            states[InstructorBoss(Instructor(i))] = DungeonKit::State::Done;
            CHECK(InstructorsDone(states) == i + 1);
        }
        CHECK(GandlingRevealed(states));
        // A state that is not DONE does not count (no raw counter to double).
        states[BOSS_ALEXEI] = DungeonKit::State::InProgress;
        CHECK(!GandlingRevealed(states));
    }

    void TestKeepsakeAndHardModes()
    {
        using DungeonKit::State::Done;
        using DungeonKit::State::InProgress;
        using DungeonKit::State::NotStarted;
        CHECK(kKeepsakeAllPages == 7);
        CHECK(KeepsakePageCount(0) == 0 && KeepsakePageCount(5) == 2 && KeepsakePageCount(7) == 3);
        CHECK(KeepsakePageAllowed(0, true, NotStarted));
        CHECK(KeepsakePageAllowed(2, true, InProgress));
        CHECK(!KeepsakePageAllowed(3, true, NotStarted));
        CHECK(!KeepsakePageAllowed(0, false, NotStarted));       // heroic only
        CHECK(!KeepsakePageAllowed(0, true, Done));              // never after Ras dies
        CHECK(KeepsakeBindAllowed(7, true, NotStarted));
        CHECK(!KeepsakeBindAllowed(3, true, NotStarted));
        CHECK(!KeepsakeBindAllowed(7, false, NotStarted));
        CHECK(!KeepsakeBindAllowed(7, true, Done));

        CHECK(RasHardModeChangeAllowed(1, true, true, NotStarted));
        CHECK(!RasHardModeChangeAllowed(1, false, true, NotStarted));    // the book must be bound
        CHECK(!RasHardModeChangeAllowed(1, true, false, NotStarted));    // heroic only
        CHECK(!RasHardModeChangeAllowed(1, true, true, InProgress));     // never lit mid-fight
        CHECK(!RasHardModeChangeAllowed(1, true, true, Done));
        CHECK(RasHardModeChangeAllowed(0, false, false, InProgress));    // cleared any time before his death
        CHECK(!RasHardModeChangeAllowed(0, true, true, Done));

        CHECK(GandlingHardModeChangeAllowed(1, true, true, true, NotStarted));
        CHECK(!GandlingHardModeChangeAllowed(1, false, true, true, NotStarted));
        CHECK(!GandlingHardModeChangeAllowed(1, true, false, true, NotStarted));
        CHECK(!GandlingHardModeChangeAllowed(1, true, true, false, NotStarted));
        CHECK(!GandlingHardModeChangeAllowed(1, true, true, true, InProgress));
        CHECK(!GandlingHardModeChangeAllowed(1, true, true, true, Done));
        CHECK(GandlingHardModeChangeAllowed(0, false, false, false, InProgress));
    }

    void TestPassingGrades()
    {
        PassingGrades g;
        CHECK(!g.HonorsOpen());
        CHECK(!g.Award(0, Instructor::Malicia));                 // no player
        CHECK(g.Award(11, Instructor::Malicia));
        CHECK(!g.Award(11, Instructor::Malicia));                // once
        CHECK(g.Award(11, Instructor::Alexei));
        CHECK(g.Has(11, Instructor::Malicia) && g.Has(11, Instructor::Alexei) && !g.Has(11, Instructor::Polkelt));
        CHECK(!g.Has(12, Instructor::Malicia));
        CHECK(g.Holders(Instructor::Malicia) == 1);

        // 3 of 5 per instructor opens the honors program; 2 do not.
        PassingGrades h;
        for (std::uint32_t p : { 1u, 2u })
            for (std::size_t i = 0; i < kInstructorCount; ++i)
                h.Award(p, Instructor(i));
        CHECK(!h.HonorsOpen());
        for (std::size_t i = 0; i + 1 < kInstructorCount; ++i)
            h.Award(3, Instructor(i));
        CHECK(!h.HonorsOpen());                                  // Illucia has only 2
        h.Award(4, Instructor::Illucia);
        CHECK(h.HonorsOpen());
        CHECK(h.Holders(Instructor::Illucia) == 3);
        CHECK(h.HonorsOpen(4) == false);

        // The slots fill; a new player past them is refused, the holders keep theirs.
        PassingGrades full;
        for (std::uint32_t p = 1; p <= kGradeSlots; ++p)
            CHECK(full.Award(p, Instructor::Polkelt));
        CHECK(!full.Award(kGradeSlots + 1, Instructor::Polkelt));
        CHECK(full.Award(1, Instructor::Ravenian));
        CHECK(full.Holders(Instructor::Polkelt) == kGradeSlots);

        // Write / Read round trip, and sanitizing.
        std::vector<std::uint32_t> fields;
        h.Write(fields);
        CHECK(fields.size() == 2 * kGradeSlots);
        PassingGrades back;
        back.Read(fields, 0);
        CHECK(back.HonorsOpen());
        for (std::uint32_t p : { 1u, 2u, 3u, 4u })
            CHECK(back.MaskOf(p) == h.MaskOf(p));
        std::vector<std::uint32_t> junk{ 9, 0xFFFF, 9, 1, 0, 3, 8, 0 };
        PassingGrades clean;
        clean.Read(junk, 0);
        CHECK(clean.MaskOf(9) == kAllGradesMask);                // unknown bits cleared, the duplicate dropped
        CHECK(clean.MaskOf(8) == 0);                              // no grade: dropped
        CHECK(clean.Holders(Instructor::Malicia) == 1);
    }

    void TestSave()
    {
        ScholoSave s;
        s.states[BOSS_JANDICE] = DungeonKit::State::Done;
        s.states[BOSS_ILLUCIA] = DungeonKit::State::Done;
        s.states[BOSS_GANDLING] = DungeonKit::State::ToBeDecided;
        s.kirtonos = DungeonKit::State::Done;
        s.keepsakePages = 5;
        s.keepsakeBound = 0;
        s.rasHardMode = 1;
        s.rasHardModeKilled = 1;
        s.gandlingHardMode = 1;
        s.gandlingHardModeKilled = 0;
        s.grades.Award(42, Instructor::Krastinov);
        s.grades.Award(43, Instructor::Illucia);
        std::string const text = FormatScholoSave(s);
        CHECK(text.rfind("S C 3 0 0 0 0 0 0 0 0 0 3 3 5 0 1 1 1 0 42 2 43 32", 0) == 0);

        ScholoSave back;
        CHECK(ParseScholoSave(text, back));
        CHECK(back.states[BOSS_JANDICE] == DungeonKit::State::Done);
        CHECK(back.states[BOSS_ILLUCIA] == DungeonKit::State::Done);
        CHECK(back.states[BOSS_GANDLING] == DungeonKit::State::NotStarted);
        CHECK(back.kirtonos == DungeonKit::State::Done);
        CHECK(back.keepsakePages == 5 && back.keepsakeBound == 0);
        CHECK(back.rasHardMode == 1 && back.rasHardModeKilled == 1);
        CHECK(back.gandlingHardMode == 1 && back.gandlingHardModeKilled == 0);
        CHECK(back.grades.Has(42, Instructor::Krastinov) && back.grades.Has(43, Instructor::Illucia));
        CHECK(FormatScholoSave(back) == text);

        // An "S C" save ignores the encounter mask (it carries its own states).
        ScholoSave masked;
        CHECK(ParseScholoSave(text, masked, 0xFFFFFFFFu));
        CHECK(masked.states[BOSS_RAS] == DungeonKit::State::NotStarted);

        // Loaded junk is sanitized; a short tail (an older build) keeps the defaults.
        ScholoSave junk;
        CHECK(ParseScholoSave("S C 1 2 4 9 3 3 3 3 3 3 3 1 15 9 9 9 9", junk));
        CHECK(junk.states[0] == DungeonKit::State::NotStarted);
        CHECK(junk.states[1] == DungeonKit::State::NotStarted);
        CHECK(junk.states[2] == DungeonKit::State::NotStarted);
        CHECK(junk.states[3] == DungeonKit::State::NotStarted);
        CHECK(junk.states[4] == DungeonKit::State::Done);
        CHECK(junk.kirtonos == DungeonKit::State::NotStarted);   // IN_PROGRESS reloads as NOT_STARTED
        CHECK(junk.keepsakePages == 7 && junk.keepsakeBound == 1 && junk.rasHardMode == 1);
        CHECK(junk.gandlingHardModeKilled == 0);                 // past the tail: default
        ScholoSave shortTail;
        CHECK(ParseScholoSave("S C 3 3", shortTail));
        CHECK(shortTail.states[0] == DungeonKit::State::Done && shortTail.states[1] == DungeonKit::State::Done);
        CHECK(shortTail.states[2] == DungeonKit::State::NotStarted && shortTail.kirtonos == 0);

        // Nothing that reads as neither.
        ScholoSave none;
        CHECK(!ParseScholoSave("", none));
        CHECK(!ParseScholoSave("D E 3 3", none));
        CHECK(!ParseScholoSave("3", none));                      // a stock save has two fields
        CHECK(!ParseScholoSave("S C", none));
    }

    void TestStockSave()
    {
        // instance_scholomance's WriteSaveDataMore: "<kirtonos> <miniBosses>", no header and no boss states.
        ScholoSave s;
        CHECK(ParseScholoSave("3 6", s));
        CHECK(s.kirtonos == DungeonKit::State::Done);
        for (std::size_t i = 0; i < kInstructorCount; ++i)
            CHECK(s.states[InstructorBoss(Instructor(i))] == DungeonKit::State::Done);
        CHECK(GandlingRevealed(s.states));
        CHECK(s.states[BOSS_JANDICE] == DungeonKit::State::NotStarted);
        CHECK(s.keepsakePages == 0 && s.rasHardMode == 0 && !s.grades.HonorsOpen());

        // The stock reload bug: a saved Kirtonos IN_PROGRESS (1) blocked the re-summon; now NOT_STARTED.
        ScholoSave k;
        CHECK(ParseScholoSave("1 2", k));
        CHECK(k.kirtonos == DungeonKit::State::NotStarted);
        CHECK(InstructorsDone(k.states) == 0);                   // a raw count under 6 names no instructor

        // The completed-encounter mask (DBC bits 0-12) fills in the states a stock save cannot name.
        ScholoSave m;
        std::uint32_t const mask = (1u << 0) | (1u << 1) | (1u << 3) | (1u << 6) | (1u << 11);
        CHECK(ParseScholoSave("0 2", m, mask));
        CHECK(m.kirtonos == DungeonKit::State::Done);
        CHECK(m.states[BOSS_JANDICE] == DungeonKit::State::Done);
        CHECK(m.states[BOSS_MARDUK_VECTUS] == DungeonKit::State::NotStarted);   // Marduk without Vectus
        CHECK(m.states[BOSS_MALICIA] == DungeonKit::State::Done);
        CHECK(m.states[BOSS_ILLUCIA] == DungeonKit::State::Done);
        CHECK(m.states[BOSS_RATTLEGORE] == DungeonKit::State::NotStarted);
        ScholoSave both;
        CHECK(ParseScholoSave("0 0", both, (1u << 3) | (1u << 4) | (1u << 12) | (1u << 5)));
        CHECK(both.states[BOSS_MARDUK_VECTUS] == DungeonKit::State::Done);
        CHECK(both.states[BOSS_GANDLING] == DungeonKit::State::Done);
        CHECK(both.states[BOSS_RAS] == DungeonKit::State::Done);
        // Written back in the new form.
        CHECK(FormatScholoSave(both).rfind("S C ", 0) == 0);
    }

    void TestLessonClock()
    {
        LessonClock c;
        CHECK(!c.Started() && !c.Running() && !c.Done() && !c.Failed() && !c.Passed());
        c.Start();
        CHECK(c.Running() && c.RemainingMs() == kLessonMs);
        CHECK(!c.Advance(14999));
        CHECK(c.Advance(1));
        CHECK(c.Done() && c.EndReason() == LessonEnd::TimeUp && c.Passed() && !c.Failed());
        CHECK(!c.Advance(100));                                  // no second end

        LessonClock f;
        f.Start();
        f.Fail();
        f.Advance(kLessonMs);
        CHECK(f.Failed() && !f.Passed() && f.Failures() == 1);

        // Krastinov's normal lesson allows one Incision.
        LessonClock k;
        k.Start(kLessonMs, 1);
        k.Fail();
        k.Advance(kLessonMs);
        CHECK(k.Passed());
        LessonClock k2;
        k2.Start(kLessonMs, 1);
        k2.Fail();
        k2.Fail();
        k2.End(LessonEnd::Finished);
        CHECK(k2.Failed() && k2.EndReason() == LessonEnd::Finished);
        k2.Fail();
        CHECK(k2.Failures() == 2);                               // no failure counts after the end

        // A safety end has no verdict.
        LessonClock s;
        s.Start();
        s.Fail();
        s.End(LessonEnd::StudentDied);
        CHECK(s.Done() && !s.HasVerdict() && !s.Failed() && !s.Passed());
        s.End(LessonEnd::Finished);
        CHECK(s.EndReason() == LessonEnd::StudentDied);          // the first end stays

        CHECK(LessonEndCheck(true, true, true, true) == LessonEnd::None);
        CHECK(LessonEndCheck(true, true, true, false) == LessonEnd::Aborted);
        CHECK(LessonEndCheck(false, false, false, true) == LessonEnd::StudentLeft);
        CHECK(LessonEndCheck(true, false, true, true) == LessonEnd::StudentDied);
        CHECK(LessonEndCheck(true, true, false, true) == LessonEnd::LastAlive);
        CHECK(IsSafetyEnd(LessonEnd::LastAlive) && !IsSafetyEnd(LessonEnd::TimeUp)
            && !IsSafetyEnd(LessonEnd::Finished));
    }
}

int main()
{
    TestBossStates();
    TestDataIds();
    TestInstructorsAndClassrooms();
    TestSlices();
    TestArenas();
    TestReveal();
    TestKeepsakeAndHardModes();
    TestPassingGrades();
    TestSave();
    TestStockSave();
    TestLessonClock();
    return Report("scholomance_test");
}
