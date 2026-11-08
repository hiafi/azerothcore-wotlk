/*
 * mod-dungeon-bosses, Scholomance: the solo lesson interface (handoff section 3.7; built by WP-KS, used by the
 * instructor WPs S5-S10 for their room's lesson and by S11 for Gandling's detention cycle).
 *
 * Gandling's Detention (GD1) teleports one student into a classroom behind its shut gate for 15 s. The room runs its
 * instructor's solo lesson (SC "Detention" notes, SC 2960-2971):
 *
 *   the Coven              drained on landing, 3 / 4 souls spill and fade in 10 / 6 s         (S5 Malicia)
 *   the Hall of the Damned the bench straps the student in and its saw casts Incision 3 times  (S6 Krastinov)
 *   the Hall of Secrets    3 / 4 Unstable Specimens walk at the student                        (S7 Polkelt)
 *   the Vault of the Ravenian  the echo carries out 3 orders, Corvane's markers                (S8 the Ravenian)
 *   the Barov Family Vault No running and Out of bounds, a fortune in reach                    (S9 Alexei)
 *   the Shadow Vault       one Foresight chain, 3 / 5 markers                                  (S10 Illucia)
 *
 * Any failure hit is 15% / 25% of the reference row plus Weakened (kLessonFailurePctNormal / Heroic).
 *
 * The owner. Each lesson registers its mechanics under the room's invisible lesson stalker (NPC_SC_LESSON_STALKER
 * 300546, summoned by S11), with `.Targets({ student })` or a single-player eligibility, so its failures land in the
 * stalker's ledger, never Gandling's, and the registry cleans up when the stalker despawns.
 *
 * An instructor WP writes its lesson in its own file, as a TimedSoloLesson, and registers its factory from its AddSC_:
 *
 *     class CovenLesson : public ScholomanceRework::TimedSoloLesson
 *     {
 *     public:
 *         CovenLesson() : TimedSoloLesson(Classroom::Coven) { }
 *     protected:
 *         void OnStart(Creature* owner, Player* student, bool heroic) override { ... spill the souls ... }
 *         void OnUpdate(uint32 diff, Creature* owner, Player* student) override { ... }
 *         void OnEnd(LessonEnd why, Creature* owner) override { ... despawn what OnStart spawned ... }
 *     };
 *
 *     void AddSC_boss_instructor_malicia_rework()
 *     {
 *         ...
 *         ScholomanceRework::RegisterSoloLesson(Classroom::Coven,
 *             [] { return std::unique_ptr<SoloLesson>(new CovenLesson()); });
 *     }
 *
 * S11 runs one per detention:
 *
 *     _lesson = ScholomanceRework::CreateSoloLesson(room);     // nullptr: no lesson registered for that room yet
 *     _lesson->Start(stalker, student, heroic);
 *     ... every tick: _lesson->Update(diff); if (_lesson->Done()) { Failed() ? Expelled Student : Honor Roll; }
 *     ... on a wipe, his evade or death: _lesson->Abort();
 *
 * TimedSoloLesson owns the 15 s clock, the failure count (every registry failure of the student under the owner's
 * encounter, plus FailStudent() for a script's own hit) and the safety stops (the student died, left or is the last
 * one alive; the owner is gone): it ends the owner's encounter and calls OnEnd once, whatever the reason.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_SOLO_LESSON_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_SOLO_LESSON_H

#include "Define.h"
#include "ObjectGuid.h"
#include "ScholomanceRework.h"
#include "SoloLessonLogic.h"
#include <functional>
#include <memory>

class Creature;
class Map;
class Player;

namespace ScholomanceRework
{
    class SoloLesson
    {
    public:
        virtual ~SoloLesson() = default;

        // `owner`: the room's lesson stalker (its registry encounter holds the lesson's mechanics); `student`: the
        // detained player; `heroic`: the heroic lesson (SC table, the second number).
        virtual void Start(Creature* owner, Player* student, bool heroic) = 0;
        virtual void Update(uint32 diff) = 0;
        // Ended, for any reason (Failed() and Passed() only hold after a full run).
        virtual bool Done() const = 0;
        virtual bool Failed() const = 0;
        virtual bool Passed() const = 0;
        // Stop now with no verdict (a wipe, Gandling's evade or death, a reset); cleans up at once.
        virtual void Abort() = 0;
        virtual Classroom Room() const = 0;
    };

    class TimedSoloLesson : public SoloLesson
    {
    public:
        explicit TimedSoloLesson(Classroom room) : _room(room) { }
        ~TimedSoloLesson() override;

        void Start(Creature* owner, Player* student, bool heroic) final;
        void Update(uint32 diff) final;
        bool Done() const final { return _clock.Done(); }
        bool Failed() const final { return _clock.Failed(); }
        bool Passed() const final { return _clock.Passed(); }
        void Abort() final;
        Classroom Room() const final { return _room; }

        LessonClock const& Clock() const { return _clock; }
        LessonEnd EndReason() const { return _clock.EndReason(); }
        bool Heroic() const { return _heroic; }
        ObjectGuid StudentGuid() const { return _student; }
        ObjectGuid OwnerGuid() const { return _owner; }

    protected:
        // How many student failures still pass (SC: the bench allows 1 Incision on normal, none on heroic).
        virtual uint32 AllowedFailures(bool /*heroic*/) const { return 0; }
        virtual uint32 DurationMs(bool /*heroic*/) const { return kLessonMs; }

        virtual void OnStart(Creature* owner, Player* student, bool heroic) = 0;
        virtual void OnUpdate(uint32 /*diff*/, Creature* /*owner*/, Player* /*student*/) { }
        // Once, whatever ended the lesson; `owner` may be null (it despawned). Despawn what OnStart spawned here.
        virtual void OnEnd(LessonEnd /*why*/, Creature* /*owner*/) { }

        // A failure the registry does not see (a script's own spell hit the student).
        void FailStudent();
        // The lesson's last job resolved early: end it now with its verdict.
        void FinishEarly();

        Creature* Owner() const;
        Player* Student() const;

    private:
        void Finish(LessonEnd why);
        void SyncFailures();

        Classroom _room;
        LessonClock _clock;
        Map* _map = nullptr;
        ObjectGuid _owner;
        ObjectGuid _student;
        bool _heroic = false;
        bool _ended = false;
        // Registry failures of the student, counted by the owner's OnFailure handler (shared: the handler may outlive
        // this object until the owner's encounter ends).
        std::shared_ptr<uint32> _registryFailures;
    };

    using SoloLessonFactory = std::function<std::unique_ptr<SoloLesson>()>;

    // An instructor WP registers its room's lesson from its AddSC_ (a second registration for a room replaces the
    // first, with an error log).
    void RegisterSoloLesson(Classroom room, SoloLessonFactory factory);
    // A new lesson for `room`, or nullptr when none is registered (S11 then skips the room or uses a fallback).
    std::unique_ptr<SoloLesson> CreateSoloLesson(Classroom room);
    bool HasSoloLesson(Classroom room);

    // LessonFailurePct (a lesson's failure hit, 15% / 25%) is pure: SoloLessonLogic.h.
}

#endif
