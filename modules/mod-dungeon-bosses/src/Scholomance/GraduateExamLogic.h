/*
 * mod-dungeon-bosses, Scholomance S13:
 * Darkmaster Gandling's hard mode, the Graduate Exam, the pure, host-testable part (no engine headers): its spell ids
 * (inside kSpellsGandlingHardMode of ScholomanceRework.h), the Passing Grade displays, the honors paper's refusals,
 * the gauntlet's rooms (where the examiner stands, where the group lands, the room's floor for Gandling's lanes), the
 * room order, the modes Gandling runs in the gauntlet, and the gauntlet's step machine. Tested by
 * tests/scholo_exam_test.cpp; the engine side is graduate_exam.cpp.
 *
 * Build spec: docs/dungeons/scholomance-rework.md SC 2909-3006 (the honors program, the gauntlet, the numbers),
 * SC 3046-3063 (Build spec: GD5, GD6, the examiners and the paper); handoff sections 3.5 row S13, 3.6, 3.10.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_GRADUATE_EXAM_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_GRADUATE_EXAM_LOGIC_H

#include "GandlingLogic.h"
#include "ScholomanceRework.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <utility>
#include <vector>

namespace ScholoGraduateExam
{
    using DungeonKit::FrameRect;
    using DungeonKit::Vec2;
    using ScholoGandling::GandlingMode;
    using ScholoGandling::GandlingRegion;
    using ScholomanceRework::Classroom;
    using ScholomanceRework::Instructor;
    using ScholomanceRework::kClassroomCount;
    using ScholomanceRework::kInstructorCount;
    using ScholomanceRework::Point4;

    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsGandlingHardMode;

    // apps/dbc-tools source/npcs/scholomance/graduate_exam.py declares each one. 206371-206384 are spare.
    enum GraduateExamSpells : std::uint32_t
    {
        // The Passing Grades (ruling 22): one display aura per instructor, in the Instructor order. The instance holds
        // the grades (saved); the auras only show them (a death, a release or a logout never loses a grade).
        SPELL_GE_GRADE_MALICIA      = 206365,
        SPELL_GE_GRADE_KRASTINOV    = 206366,
        SPELL_GE_GRADE_POLKELT      = 206367,
        SPELL_GE_GRADE_RAVENIAN     = 206368,
        SPELL_GE_GRADE_ALEXEI       = 206369,
        SPELL_GE_GRADE_ILLUCIA      = 206370,
    };

    constexpr std::uint32_t PassingGradeSpell(Instructor i)
    {
        return SPELL_GE_GRADE_MALICIA + std::uint32_t(i);
    }

    // ---- Passing Grade displays -------------------------------------------------------------------------------------
    // The auras a player should gain and lose: `held` is their grade mask (PassingGrades::MaskOf), `shown` the mask of
    // the grade auras they wear now.
    struct GradeAuraChange
    {
        std::uint32_t add = 0;
        std::uint32_t remove = 0;
    };

    constexpr GradeAuraChange GradeAuraDiff(std::uint32_t held, std::uint32_t shown)
    {
        held &= ScholomanceRework::kAllGradesMask;
        shown &= ScholomanceRework::kAllGradesMask;
        return { held & ~shown, shown & ~held };
    }

    std::uint32_t constexpr kGradeSweepMs = 2000;       // the instance re-shows the grades on every player this often

    // ---- Who earns a Passing Grade (GradeWatch::AwardAtDeath, ScholomanceKit.cpp) ----------------------------------
    // Orchestrator ruling 2026-11-08 (R-C EXAM designer question 2): at the instructor's death, a player earns the
    // grade when they are inside the instructor's arena (a body that has not released counts; a released ghost or a
    // player elsewhere on the map does not), recorded no failure of the fight, and are not a GM.
    struct GradeCandidate
    {
        bool gameMaster = false;
        bool failed = false;        // GradeWatch's ledger recorded a failure for them
        bool released = false;      // a ghost (PLAYER_FLAGS_GHOST)
        bool inArena = false;       // inside GradeArena(instructor) at the death (alive, or their unreleased body)
    };

    constexpr bool EarnsPassingGrade(GradeCandidate const& p)
    {
        return !p.gameMaster && !p.failed && !p.released && p.inArena;
    }

    // The arena a grade is earned in: the instructor's own (ArenaGuard's leash arena).
    inline DungeonKit::Arena GradeArena(Instructor i)
    {
        return ScholomanceRework::ArenaFor(ScholomanceRework::InstructorBoss(i));
    }

    // ---- The honors program paper (GO 301153) -----------------------------------------------------------------------
    enum class PaperRefusal : std::uint8_t
    {
        None,
        NotHeroic,          // the hard mode is heroic only
        GandlingDone,       // he is dead: nothing left to sign up for
        NotRevealed,        // Gandling is still hidden (an instructor stands)
        GandlingBusy,       // he fights already (or the exam is under way)
        HonorsClosed,       // an instructor lacks kHonorsMinHolders grades
    };

    struct PaperState
    {
        bool heroic = false;
        bool revealed = false;
        std::uint32_t gandlingState = DungeonKit::State::NotStarted;
        bool gandlingEngaged = false;
        bool examRunning = false;
        bool honorsOpen = false;
    };

    constexpr PaperRefusal CheckPaper(PaperState const& s)
    {
        if (!s.heroic)
            return PaperRefusal::NotHeroic;
        if (s.gandlingState == DungeonKit::State::Done)
            return PaperRefusal::GandlingDone;
        if (!s.revealed)
            return PaperRefusal::NotRevealed;
        if (s.examRunning || s.gandlingEngaged || s.gandlingState == DungeonKit::State::InProgress)
            return PaperRefusal::GandlingBusy;
        if (!s.honorsOpen)
            return PaperRefusal::HonorsClosed;
        return PaperRefusal::None;
    }

    // ---- Numbers (SC "Hard mode, the gauntlet" and its approved answers; handoff 3.6) -------------------------------
    std::uint32_t constexpr kExaminerHealth = 80000;            // each examiner; SC 2997
    std::uint32_t constexpr kExaminerRavenianHealth = 60000;    // the Ravenian 60k and Corvane 20k (his 50% drop stays)
    std::uint32_t constexpr kExaminerCorvaneHealth = 20000;
    std::uint32_t constexpr kFinalHealth = 200000;              // Gandling in the final phase (approved answers)

    // The health of each examiner entry (the DT test checks HealthModifier x class base against it).
    constexpr std::uint32_t ExaminerHealth(std::uint32_t entry)
    {
        using namespace ScholomanceRework;
        switch (entry)
        {
            case NPC_SC_EXAMINER_RAVENIAN: return kExaminerRavenianHealth;
            case NPC_SC_EXAMINER_CORVANE:  return kExaminerCorvaneHealth;
            case NPC_SC_EXAMINER_MALICIA:
            case NPC_SC_EXAMINER_KRASTINOV:
            case NPC_SC_EXAMINER_POLKELT:
            case NPC_SC_EXAMINER_ALEXEI:
            case NPC_SC_EXAMINER_ILLUCIA:  return kExaminerHealth;
            default:                       return 0;
        }
    }

    // ---- Timers -----------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kOpenDelayMs = 5000;        // the paper signed: yell line 4, then the first portal
    std::uint32_t constexpr kPortalDelayMs = 5000;      // SC: "a portal on each kill takes the group on after 5 sec"
    std::uint32_t constexpr kArrivalTimeoutMs = 4000;   // the group must land in the room (or the study) by then
    // R-C EXAM SF-1: after the arrival, the pull is retried every tick until the unit (the examiner, or Gandling in the
    // final phase) is engaged; only then does leaving combat count as a wipe. Never engaged this long with nobody
    // living inside the arena: a wipe. Never engaged after twice as long: a wipe whatever the reason (the gates are
    // shut; nobody waits forever).
    std::uint32_t constexpr kPullTimeoutMs = 15000;
    float constexpr kGroupSpreadYd = 2.5f;              // the group lands in a ring this wide, not on one spot
    float constexpr kPortalInsetYd = 1.5f;              // Gandling's portals sit this far inside the room's walls
    std::size_t constexpr kPortalsPerSide = 2;          // 8 portal points per room

    // ---- The rooms --------------------------------------------------------------------------------------------------
    float constexpr kLaneZToleranceYd = 6.f;            // the registry's default shape band (MechanicGeometry.h)
    float constexpr kBarovLaneZToleranceYd = 9.5f;      // z 64.5 to 83.5 around the vault's lane height 74
    // Each gauntlet room: the examiner Gandling raises there (the Vault of the Ravenian's examiner brings his own
    // Corvane), where it stands (the instructor's spawn), where the group lands (inside the room's arena, 20 yd or more
    // from the examiner, on open floor: NAVMESH-REPORT), and the floor his lanes cross (the room's frame and floor z).
    struct ExamRoom
    {
        Classroom room = Classroom::Coven;
        std::uint32_t examiner = 0;
        Point4 examinerSpawn;
        Point4 groupLanding;
        FrameRect floor;
        float floorZ = 0.f;
        // How far above or below floorZ his lanes reach (the registry's shape zTolerance, 6 by default). R-C EXAM N-6:
        // the Barov Family Vault's pit goes down to about z 66, 8 yd under its lane height; another floor never comes
        // this close (Krastinov's hall above it is at z 85).
        float laneZTolerance = kLaneZToleranceYd;
    };

    inline std::array<ExamRoom, kClassroomCount> const& ExamRooms()
    {
        using namespace ScholomanceRework;
        static std::array<ExamRoom, kClassroomCount> const rooms{ {
            // the Shadow Vault: she fights in the hall (handoff 7 #14); the group lands in the hall's middle
            { Classroom::ShadowVault, NPC_SC_EXAMINER_ILLUCIA, kIlluciaSpawn, { 240.0f, 0.5f, 74.9f, 0.f },
                kShadowVaultHall, 74.6f, kLaneZToleranceYd },
            // the Barov Family Vault: the group lands on the gate-side tier (z 75); the floor drops to z 72 at his end,
            // so one lane height serves both tiers [navmesh estimate]; its pit (about z 66) needs the deeper band
            { Classroom::BarovVault, NPC_SC_EXAMINER_ALEXEI, kAlexeiSpawn, { 181.0f, -48.0f, 75.5f, 4.71239f },
                kBarovVault, 74.0f, kBarovLaneZToleranceYd },
            // the Vault of the Ravenian: clear of the blocks and pillars of the middle cross
            { Classroom::RavenianVault, NPC_SC_EXAMINER_RAVENIAN, kRavenianSpawn, { 124.0f, -1.0f, 75.6f, 3.14159f },
                kRavenianVault, 75.4f, kLaneZToleranceYd },
            { Classroom::HallOfSecrets, NPC_SC_EXAMINER_POLKELT, kPolkeltSpawn, { 252.0f, 0.5f, 85.4f, 0.f },
                kHallOfSecrets, 85.3f, kLaneZToleranceYd },
            // the Hall of the Damned: the open hall in front of his apse (NAVMESH-REPORT option B, 8 yd further)
            { Classroom::HallOfTheDamned, NPC_SC_EXAMINER_KRASTINOV, kKrastinovSpawn,
                { 181.0f, -72.0f, 85.4f, 4.71239f }, kKrastinovHall, 85.3f, kLaneZToleranceYd },
            { Classroom::Coven, NPC_SC_EXAMINER_MALICIA, kMaliciaSpawn, { 110.0f, -1.0f, 85.4f, 3.14159f },
                kCovenFloor, 85.3f, kLaneZToleranceYd },
        } };
        return rooms;
    }

    inline ExamRoom const& ExamRoomOf(Classroom c)
    {
        return ExamRooms()[std::size_t(c)];
    }

    // The group comes back to the study for the final phase: 13 yd north of his spot, facing him.
    Point4 constexpr kStudyReturn{ 181.0f, 8.0f, 75.8f, 4.71239f };

    // Points on the four walls of `frame`: `perSide` a wall, evenly spaced (never a corner), `inset` yd inside.
    inline std::vector<Vec2> FrameEdgePoints(FrameRect const& frame, std::size_t perSide, float inset)
    {
        std::vector<Vec2> out;
        for (std::size_t k = 0; k < perSide; ++k)
        {
            float const f = float(k + 1) / float(perSide + 1);
            float const along = inset + f * (frame.sizeX - 2.f * inset);
            float const across = inset + f * (frame.sizeY - 2.f * inset);
            out.push_back(DungeonKit::FramePoint(frame, along, inset));                   // the y = 0 wall
            out.push_back(DungeonKit::FramePoint(frame, along, frame.sizeY - inset));     // the far y wall
            out.push_back(DungeonKit::FramePoint(frame, inset, across));                  // the x = 0 wall
            out.push_back(DungeonKit::FramePoint(frame, frame.sizeX - inset, across));    // the far x wall
        }
        return out;
    }

    // The room's floor as a box (Gandling's lanes stop at its walls), in the room arena's z band.
    inline DungeonKit::Arena RoomFloorArena(Classroom c)
    {
        ExamRoom const& r = ExamRoomOf(c);
        DungeonKit::Arena const arena = ScholomanceRework::ClassroomArena(c);
        return DungeonKit::Arena(DungeonKit::ArenaRegion::Frame(r.floor,
            DungeonKit::Box2{ 0.f, r.floor.sizeX, 0.f, r.floor.sizeY }, arena.ZMin(), arena.ZMax()));
    }

    // Where Gandling's mechanics act while the group sits a room's exam (GandlingFight.h SetRegion): the players in
    // the room's arena, the lanes clipped at its floor's walls, portals on those walls.
    inline GandlingRegion RoomRegion(Classroom c)
    {
        ExamRoom const& r = ExamRoomOf(c);
        GandlingRegion region;
        region.players = ScholomanceRework::ClassroomArena(c);
        region.clip = RoomFloorArena(c);
        region.portalPoints = FrameEdgePoints(r.floor, kPortalsPerSide, kPortalInsetYd);
        region.floorZ = r.floorZ;
        region.zTolerance = r.laneZTolerance;
        return region;
    }

    // The group's landing spots: the room's point, then a ring of kGroupSpreadYd around it (index 1..6, then round
    // again), so a group never lands on one spot.
    inline Point4 SpreadLanding(Point4 const& at, std::size_t index)
    {
        if (index == 0)
            return at;
        float const angle = float((index - 1) % 6) * DungeonKit::kTwoPi / 6.f;
        Vec2 const p = DungeonKit::Advance(at.XY(), angle, kGroupSpreadYd);
        return { p.x, p.y, at.z, at.o };
    }

    // ---- Gandling's modes in the hard mode (GandlingFight.h) --------------------------------------------------------
    // GD5: while the group sits an exam, he casts Portal Volley and Transfer into the room at heroic values, never
    // Detention, with no victim of his own (he stays in the study, not attackable).
    constexpr GandlingMode GauntletMode()
    {
        GandlingMode m = ScholoGandling::FightMode(true);
        m.detention = false;
        m.needsVictim = false;
        return m;
    }

    // Before the first room and between rooms (the 5 s portal): nothing.
    constexpr GandlingMode IdleMode()
    {
        GandlingMode m = GauntletMode();
        m.volley = false;
        m.transfer = false;
        return m;
    }

    // ---- The room order ---------------------------------------------------------------------------------------------
    // The six classrooms in a random order (`rand(n)` returns [0, n)). `first` (a test command) leads when in range.
    template <class Rand>
    std::array<Classroom, kClassroomCount> ExamOrder(Rand&& rand, int first = -1)
    {
        std::array<Classroom, kClassroomCount> order{};
        for (std::size_t i = 0; i < kClassroomCount; ++i)
            order[i] = Classroom(i);
        for (std::size_t i = kClassroomCount; i > 1; --i)     // Fisher-Yates
            std::swap(order[i - 1], order[rand(i)]);
        if (first >= 0 && std::size_t(first) < kClassroomCount)
            for (std::size_t i = 0; i < kClassroomCount; ++i)
                if (order[i] == Classroom(first))
                    std::swap(order[0], order[i]);
        return order;
    }

    // ---- The gauntlet's steps (GD5, GD6) ----------------------------------------------------------------------------
    enum class ExamPhase : std::uint8_t
    {
        Idle,
        Opening,        // signed: yell line 4, kOpenDelayMs, then the first portal
        Arriving,       // the group is on its way into a room
        Examining,      // the room's examiner fights
        Portal,         // the examiner died: kPortalDelayMs, then the next room (or the study)
        Returning,      // the group is on its way back to the study
        Final,          // GD6: Gandling at kFinalHealth
        Passed,         // he died in the final phase
    };

    // What the engine does now.
    enum class ExamAction : std::uint8_t
    {
        None,
        SendToRoom,     // teleport the group into Room()
        PullExaminer,   // raise Room()'s examiner and pull it; Gandling's lanes and swaps reach in (GauntletMode)
        RetryPull,      // the examiner (Examining) or Gandling (Final) was never engaged yet: pull the arena again
        RoomCleared,    // Gandling stops (IdleMode); the portal opens
        ReturnToStudy,  // teleport the group back; Gandling at 200k, attackable, yell line 5
        StartFinal,     // pull Gandling (FinalExamMode)
        Wipe,           // everything back as before the paper; the grades stay; the paper can be signed again
        Passed,         // the Graduate Exam is over (his own death ran the kill flag and the loot)
    };

    struct ExamInputs
    {
        bool anyAlive = true;           // a living player (not a GM) on the map
        bool arrived = false;           // every player sent is there (or gone, or dead)
        bool anyInside = true;          // a living player (not a GM) in the arena of the step (the room, the study)
        bool examinerDead = false;      // Room()'s examiner died (the Ravenian: his real death, after Corvane's)
        bool examinerGone = false;      // there is no examiner (never summoned, or gone without dying)
        bool examinerEngaged = false;   // it is in combat now
        bool gandlingDead = false;
        bool gandlingGone = false;      // he is gone
        bool gandlingEngaged = false;   // he is in combat now
    };

    class GauntletRun
    {
    public:
        void Start(std::array<Classroom, kClassroomCount> const& order)
        {
            _order = order;
            _index = 0;
            _phase = ExamPhase::Opening;
            _timerMs = 0;
            _engaged = false;
        }

        void Stop()
        {
            _phase = ExamPhase::Idle;
            _timerMs = 0;
            _engaged = false;
        }

        // A test command: the room under way counts as cleared and the rest are skipped; the next step returns the
        // group to the study.
        void SkipToStudy()
        {
            _index = kClassroomCount - 1;
            _phase = ExamPhase::Portal;
            _timerMs = kPortalDelayMs;
            _engaged = false;
        }

        ExamAction Update(std::uint32_t diff, ExamInputs const& in)
        {
            if (!Running())
                return ExamAction::None;
            if (!in.anyAlive)
            {
                Stop();
                return ExamAction::Wipe;
            }
            switch (_phase)
            {
                case ExamPhase::Opening:
                    if (Tick(diff, kOpenDelayMs))
                        return Enter(ExamPhase::Arriving, ExamAction::SendToRoom);
                    return ExamAction::None;
                case ExamPhase::Arriving:
                    if (in.arrived || Tick(diff, kArrivalTimeoutMs))
                        return Enter(ExamPhase::Examining, ExamAction::PullExaminer);
                    return ExamAction::None;
                case ExamPhase::Examining:
                    if (in.examinerDead)
                        return Enter(ExamPhase::Portal, ExamAction::RoomCleared);
                    return Hold(diff, in.examinerGone, in.examinerEngaged, in.anyInside);
                case ExamPhase::Portal:
                    if (!Tick(diff, kPortalDelayMs))
                        return ExamAction::None;
                    if (_index + 1 < kClassroomCount)
                    {
                        ++_index;
                        return Enter(ExamPhase::Arriving, ExamAction::SendToRoom);
                    }
                    return Enter(ExamPhase::Returning, ExamAction::ReturnToStudy);
                case ExamPhase::Returning:
                    if (in.arrived || Tick(diff, kArrivalTimeoutMs))
                        return Enter(ExamPhase::Final, ExamAction::StartFinal);
                    return ExamAction::None;
                case ExamPhase::Final:
                    if (in.gandlingDead)
                    {
                        _phase = ExamPhase::Passed;
                        return ExamAction::Passed;
                    }
                    return Hold(diff, in.gandlingGone, in.gandlingEngaged, in.anyInside);
                default:
                    return ExamAction::None;
            }
        }

        bool Running() const { return _phase != ExamPhase::Idle && _phase != ExamPhase::Passed; }
        ExamPhase Phase() const { return _phase; }
        // The step's unit (the examiner, Gandling in the final phase) has been engaged since its pull.
        bool Engaged() const { return _engaged; }
        std::size_t RoomIndex() const { return _index; }
        Classroom Room() const { return _order[_index]; }
        std::array<Classroom, kClassroomCount> const& Order() const { return _order; }

        // Rooms cleared so far (the room behind the open portal counts).
        std::size_t RoomsCleared() const
        {
            switch (_phase)
            {
                case ExamPhase::Portal:
                    return _index + 1;
                case ExamPhase::Returning:
                case ExamPhase::Final:
                case ExamPhase::Passed:
                    return kClassroomCount;
                default:
                    return _index;
            }
        }

    private:
        bool Tick(std::uint32_t diff, std::uint32_t limitMs)
        {
            _timerMs += diff;
            return _timerMs >= limitMs;
        }

        ExamAction Enter(ExamPhase phase, ExamAction action)
        {
            _phase = phase;
            _timerMs = 0;
            _engaged = false;
            return action;
        }

        // A fight step (Examining, Final) with its unit alive: gone is a wipe; once engaged, out of combat is a wipe
        // (an evade: the leash, an empty threat list); until then the pull is retried, up to kPullTimeoutMs with
        // nobody living inside, or twice that in any case.
        ExamAction Hold(std::uint32_t diff, bool gone, bool engaged, bool anyInside)
        {
            if (!gone && engaged)
            {
                _engaged = true;
                return ExamAction::None;
            }
            bool const timedOut = !_engaged && Tick(diff, kPullTimeoutMs)
                && (!anyInside || _timerMs >= 2 * kPullTimeoutMs);
            if (gone || _engaged || timedOut)
            {
                Stop();
                return ExamAction::Wipe;
            }
            return ExamAction::RetryPull;
        }

        std::array<Classroom, kClassroomCount> _order{};
        std::size_t _index = 0;
        ExamPhase _phase = ExamPhase::Idle;
        std::uint32_t _timerMs = 0;
        bool _engaged = false;
    };

    inline char const* PhaseName(ExamPhase p)
    {
        switch (p)
        {
            case ExamPhase::Idle:      return "idle";
            case ExamPhase::Opening:   return "opening";
            case ExamPhase::Arriving:  return "arriving";
            case ExamPhase::Examining: return "examining";
            case ExamPhase::Portal:    return "portal";
            case ExamPhase::Returning: return "returning";
            case ExamPhase::Final:     return "final";
            case ExamPhase::Passed:    return "passed";
        }
        return "?";
    }
}

#endif
