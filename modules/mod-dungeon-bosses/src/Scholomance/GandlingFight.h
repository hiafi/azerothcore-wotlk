/*
 * mod-dungeon-bosses, Scholomance S11: what Darkmaster Gandling's AI (boss_darkmaster_gandling_rework.cpp) exposes to
 * the Graduate Exam (S13, graduate_exam.cpp). The pure half (modes, regions, numbers) is GandlingLogic.h.
 *
 * The fight engine ticks from his AI's UpdateAI and runs the mechanics its mode enables, in its region:
 *   Detention (GD1, with the report card GD2 / GD3), Portal Volley (GD4), Transfer (GD4b).
 * S11's own fight sets FightMode(heroic) in the study (StudyRegion()) at the pull. S13 drives the rest:
 *
 *     GandlingFightApi* fight = GetGandlingFight(gandling);       // nullptr: not the rework AI
 *     // the gauntlet: he stays in the study, unattackable, his lanes and swaps reaching into the examiner's room
 *     GandlingMode m = FightMode(true);
 *     m.detention = false;                                        // SC: no Detention in the gauntlet
 *     m.needsVictim = false;                                      // he has no victim while the group is away
 *     fight->SetRegion(region);                                   // GandlingRegion: the room's players, walls, portals
 *     fight->SetMode(m);                                          // timers restart from now
 *     fight->SetTankProvider([] { return examinerVictim; });      // who counts as the tank (never a lane / Detention)
 *     ...
 *     fight->SetRegion(StudyRegion());
 *     fight->SetEngageMode(FinalExamMode());                      // GD6 at his pull: lanes through everyone, swaps
 *                                                                 // raise GD3 (or SetMode once he fights)
 *
 * Gandling's own health (200k in the final phase), visibility, flags, his yells 4 and 5, the examiners, the gauntlet
 * portals and the reset of all of it on a wipe are S13's. Abort() ends every running detention, Volley and Transfer
 * now (a wipe, a phase change); his evade and death call it too.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_GANDLING_FIGHT_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_GANDLING_FIGHT_H

#include "GandlingLogic.h"
#include "ObjectGuid.h"
#include <functional>
#include <optional>

class Creature;

namespace ScholoGandling
{
    class GandlingFightApi
    {
    public:
        virtual ~GandlingFightApi() = default;

        // The mechanics to run from now; restarts their timers (first casts at the mode's `*FirstMs`).
        virtual void SetMode(GandlingMode const& mode) = 0;
        virtual GandlingMode const& Mode() const = 0;
        // Where the mechanics read players and draw lanes (default: StudyRegion()).
        virtual void SetRegion(GandlingRegion const& region) = 0;
        // Who counts as the tank (never detained, never a lane target unless the mode says so). Default: his victim.
        // An empty function restores the default.
        virtual void SetTankProvider(std::function<ObjectGuid()> tank) = 0;
        // Ends a running detention (no verdict; the gate opens if the student is still in the room), the pending
        // Volley and Transfer, and clears their markers.
        virtual void Abort() = 0;
        virtual bool DetentionRunning() const = 0;
        // Raises an Expelled Student fixated on `student` beside them (GD3; the final phase's swaps use it too).
        virtual void RaiseExpelled(ObjectGuid student) = 0;
        // The mode his next pull starts in (S13's final phase: FinalExamMode()); empty: FightMode(heroic), as S11's
        // fight. His Reset (a wipe, an evade) clears it.
        virtual void SetEngageMode(std::optional<GandlingMode> mode) = 0;
    };

    // Gandling's fight engine, or nullptr when `gandling` does not run boss_darkmaster_gandling_rework.
    GandlingFightApi* GetGandlingFight(Creature* gandling);
}

#endif
