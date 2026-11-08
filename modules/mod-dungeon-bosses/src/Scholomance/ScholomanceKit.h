/*
 * mod-dungeon-bosses, Scholomance: the engine glue of the Scholomance kit (WP-KS; handoff section 3.2). The pure half
 * is ScholomanceRework.h, the solo lesson interface SoloLesson.h; the shared kit (src/Kit/) is under all of it.
 *
 *   LeashOptions       the arena guard of every Scholomance boss (user ruling on section 7 #8): no grips; the boss
 *                      never chases a victim off his arena (kLeashSwitchToInside: he turns to the top-threat unit on
 *                      it; nobody there: he holds at the edge), evades when he has been off it for kLeashBossGraceMs,
 *                      and evades when nobody in combat with him has been on it for 10 s
 *   ApplyGandlingReveal  Gandling hidden (invisible, faction 35) or revealed (visible, faction 21); the instance and
 *                      S11's Reset both call it, from the instance's DATA_GANDLING_REVEALED
 *   GradeWatch         an instructor's Passing Grades (ruling 22, section 7 #18): every registry failure with a
 *                      player during the heroic fight costs that player the grade; at the death, every other player
 *                      in the instance earns it (SetGuidData(DataPassingGrade(i), player))
 *   InstanceApi        what the instance exposes beyond Get/SetData (the grades table), via GetInstanceApi
 *
 * A Scholomance boss, in short (the KS stubs already do this):
 *
 *     boss_x_rework(Creature* c) : BossAI(c, BOSS_X), _arena(XArena(), ScholomanceRework::LeashOptions("x")) { }
 *     JustEngagedWith: BossAI::JustEngagedWith(who); Mechanic::BeginEncounter(me, { bossStateId = BOSS_X });
 *                      _grades.Begin(me, Instructor::X);  (instructors)  _arena.Engage(me);
 *     UpdateAI:        if (!UpdateVictim()) return; if (!_arena.Update(me, diff)) return; ...
 *     JustDied:        _grades.AwardAtDeath(me); BossAI::JustDied(killer);
 *     Reset / EnterEvadeMode / JustDied: _arena.Reset(); _grades.Reset();
 *
 * The instructors' gates are the instance's door data (DOOR_TYPE_ROOM on the boss state): they close on the pull
 * (IN_PROGRESS) and open on the death, a wipe or an evade (DONE, NOT_STARTED), with no code in the boss.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_KIT_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_KIT_H

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Define.h"
#include "ScholomanceRework.h"
#include <functional>
#include <memory>
#include <string>
#include <unordered_set>

class Creature;
class InstanceScript;

namespace ScholomanceRework
{
    uint32 constexpr kLeashNoTargetMs = 10000;      // user ruling: evade after 10 s with no target inside
    uint32 constexpr kLeashBossGraceMs = 2000;      // the boss himself off it this long (a charge or a knockback
                                                    // that ends outside does not reset him at once)
    // PROVISIONAL (orchestrator call on R-A Q1, F-A; the designer may change it): while his victim stands off the
    // arena the boss turns to the highest-threat unit on it (false: he holds at the edge, swinging at nothing, until
    // the victim comes back or the 10 s nobody-inside leash).
    bool constexpr kLeashSwitchToInside = true;
    // Gandling's reveal: InstanceScript -> Gandling's AI DoAction after the instance revealed him (S11's hook).
    int32 constexpr kActionGandlingRevealed = 0x5C01;

    // The arena guard options of a Scholomance boss: no grips at all (no pull grip, no grip back), never chase off the
    // arena (switch to the top-threat unit inside, kLeashSwitchToInside; else hold at the edge), the boss leash
    // (kLeashBossGraceMs) and the no-target leash (kLeashNoTargetMs). `boss` names the log prefix
    // "scholo <boss> arena".
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss);

    void ApplyGandlingReveal(Creature* gandling, bool revealed);

    // Passing Grades for one instructor's heroic fight.
    class GradeWatch
    {
    public:
        // After Mechanic::BeginEncounter. The registry keeps one failure handler per encounter (Mechanic::OnFailure):
        // a boss that needs its own (Alexei's Dean's Rod) passes it as `chain`, never calls OnFailure itself.
        void Begin(Creature* boss, Instructor who,
            std::function<void(BossMechanics::FailureEvent const&)> chain = {});
        // At the death (call before BossAI::JustDied): heroic only, every player in the instance (not a GM) with no
        // failure recorded earns the grade. Returns how many were awarded.
        uint32 AwardAtDeath(Creature* boss);
        void Reset();

        bool Active() const { return _active; }
        std::size_t FailedCount() const { return _failed ? _failed->size() : 0; }
        bool HasFailed(ObjectGuid player) const;

    private:
        std::shared_ptr<std::unordered_set<uint64>> _failed;
        Instructor _who = Instructor::Malicia;
        bool _active = false;
    };

    // The instance's extra surface (instance_scholomance_rework.cpp implements it).
    class InstanceApi
    {
    public:
        virtual ~InstanceApi() = default;
        virtual PassingGrades const& Grades() const = 0;
        virtual void ClearGrades() = 0;
    };

    // nullptr when `instance` is not the Scholomance rework instance.
    InstanceApi* GetInstanceApi(InstanceScript* instance);
}

#endif
