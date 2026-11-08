/*
 * mod-dungeon-bosses, Scholomance: the solo lesson interface (SoloLesson.h), the clock and safety half every room's
 * lesson shares, and the per-room factory table.
 */

#include "SoloLesson.h"
#include "BossMechanics.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "Log.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "StringFormat.h"
#include <array>
#include <utility>

namespace ScholomanceRework
{
    namespace
    {
        std::array<SoloLessonFactory, kClassroomCount>& Factories()
        {
            static std::array<SoloLessonFactory, kClassroomCount> factories;
            return factories;
        }

        char const* EndName(LessonEnd e)
        {
            switch (e)
            {
                case LessonEnd::None:        return "none";
                case LessonEnd::TimeUp:      return "time-up";
                case LessonEnd::Finished:    return "finished";
                case LessonEnd::StudentDied: return "student-died";
                case LessonEnd::StudentLeft: return "student-left";
                case LessonEnd::LastAlive:   return "last-alive";
                case LessonEnd::Aborted:     return "aborted";
            }
            return "?";
        }
    }

    TimedSoloLesson::~TimedSoloLesson()
    {
        // A lesson dropped while running (its owner's AI went away): end the stalker's encounter so no handler keeps
        // counting. OnEnd cannot run here (the derived part is gone); S11 calls Abort() first.
        if (_clock.Running() && _map)
            if (Creature* owner = _map->GetCreature(_owner))
                Mechanic::EndEncounter(owner);
    }

    void TimedSoloLesson::Start(Creature* owner, Player* student, bool heroic)
    {
        if (!owner || !student || _clock.Started())
            return;
        _map = owner->GetMap();
        _owner = owner->GetGUID();
        _student = student->GetGUID();
        _heroic = heroic;
        _ended = false;
        _registryFailures = std::make_shared<uint32>(0);
        _clock.Start(DurationMs(heroic), AllowedFailures(heroic));

        Mechanic::BeginEncounter(owner);
        std::shared_ptr<uint32> const counter = _registryFailures;
        ObjectGuid const studentGuid = _student;
        Mechanic::OnFailure(owner, [counter, studentGuid](BossMechanics::FailureEvent const& ev)
        {
            // Group failures (no player) never count; only the student's own.
            if (ev.player == studentGuid)
                ++*counter;
        });

        DungeonKit::LogMechanic(kLogDungeon, "detention", "lesson-start",
            Acore::StringFormat("room={} student={} heroic={}", kClassroomNames[std::size_t(_room)],
                student->GetName(), heroic ? 1 : 0));
        OnStart(owner, student, heroic);
    }

    void TimedSoloLesson::Update(uint32 diff)
    {
        if (!_clock.Running() || !_map)
            return;

        Creature* owner = Owner();
        Player* student = Student();
        bool anyoneElseAlive = false;
        for (auto const& ref : _map->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (p && p->GetGUID() != _student && p->IsAlive() && !p->IsGameMaster())
            {
                anyoneElseAlive = true;
                break;
            }
        }
        LessonEnd const stop = LessonEndCheck(student != nullptr, student && student->IsAlive(), anyoneElseAlive,
            owner && owner->IsAlive());
        if (stop != LessonEnd::None)
        {
            Finish(stop);
            return;
        }

        SyncFailures();
        OnUpdate(diff, owner, student);
        if (!_clock.Running())
        {
            Finish(_clock.EndReason());
            return;
        }
        SyncFailures();
        if (_clock.Advance(diff))
            Finish(LessonEnd::TimeUp);
    }

    void TimedSoloLesson::Abort()
    {
        if (!_clock.Started() || _ended)
            return;
        Finish(LessonEnd::Aborted);
    }

    void TimedSoloLesson::FailStudent()
    {
        _clock.Fail();
    }

    void TimedSoloLesson::FinishEarly()
    {
        SyncFailures();
        _clock.End(LessonEnd::Finished);
    }

    Creature* TimedSoloLesson::Owner() const
    {
        return _map ? _map->GetCreature(_owner) : nullptr;
    }

    Player* TimedSoloLesson::Student() const
    {
        return _map ? ObjectAccessor::GetPlayer(_map, _student) : nullptr;
    }

    void TimedSoloLesson::SyncFailures()
    {
        if (!_registryFailures)
            return;
        // FailStudent's own count rides _clock; the registry's comes through the shared counter.
        while (*_registryFailures > 0)
        {
            --*_registryFailures;
            _clock.Fail();
        }
    }

    void TimedSoloLesson::Finish(LessonEnd why)
    {
        if (_ended)
            return;
        _ended = true;
        SyncFailures();
        _clock.End(why);
        Creature* owner = Owner();
        DungeonKit::LogMechanic(kLogDungeon, "detention", "lesson-end",
            Acore::StringFormat("room={} reason={} failures={} verdict={}", kClassroomNames[std::size_t(_room)],
                EndName(_clock.EndReason()), _clock.Failures(),
                _clock.Passed() ? "pass" : _clock.Failed() ? "fail" : "none"));
        OnEnd(_clock.EndReason(), owner);
        if (owner)
            Mechanic::EndEncounter(owner);
    }

    void RegisterSoloLesson(Classroom room, SoloLessonFactory factory)
    {
        std::size_t const i = std::size_t(room);
        if (i >= kClassroomCount)
            return;
        if (Factories()[i])
            LOG_ERROR(DungeonKit::kLogCategory, "scholo detention: a second lesson for {} replaces the first",
                kClassroomNames[i]);
        Factories()[i] = std::move(factory);
    }

    std::unique_ptr<SoloLesson> CreateSoloLesson(Classroom room)
    {
        std::size_t const i = std::size_t(room);
        if (i >= kClassroomCount || !Factories()[i])
            return nullptr;
        return Factories()[i]();
    }

    bool HasSoloLesson(Classroom room)
    {
        std::size_t const i = std::size_t(room);
        return i < kClassroomCount && Factories()[i];
    }
}
