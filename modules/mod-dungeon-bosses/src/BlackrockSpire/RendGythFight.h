/*
 * mod-dungeon-bosses, Blackrock Spire B12: the two AIs of one encounter talking to each other.
 *
 * Rend's AI (boss_rend_blackhand_rework.cpp) runs the show (RendShow): the acts, the rounds, the Nefarius copy, the
 * Mark and the Freezing Sweep it hangs on Gyth. Gyth's AI (boss_gyth_rework.cpp) is the drake (GythDrake): his melee,
 * Corrosive Acid with the taunt swap at 10, Knock Away, the riderless breath, the hover. Each finds the other through
 * the instance (BOSS_REND / its own summon guid) and a dynamic_cast to these interfaces; every call is made from the
 * caller's own UpdateAI or hook, and a call that ends the attempt (a death, an evade) is only noted by the callee and
 * acted on in its own next update.
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_REND_GYTH_FIGHT_H
#define MOD_DUNGEON_BOSSES_BRS_REND_GYTH_FIGHT_H

#include "Define.h"
#include "ObjectGuid.h"

class Creature;
class Unit;

namespace BrsRendGyth
{
    // Rend's AI as Gyth sees it.
    class RendShow
    {
    public:
        virtual ~RendShow() = default;

        // Gyth engaged (his pull: the Mark starts 5 s later).
        virtual void OnGythEngaged(Creature* gyth) = 0;
        // Gyth died: act 3 (noted; Rend leaps from his corpse in his next update).
        virtual void OnGythDied(Creature* gyth) = 0;
        // Gyth evaded (nobody left on the arena, or off it): the attempt is over (noted; the wipe runs in Rend's next
        // update).
        virtual void OnGythEvaded(Creature* gyth) = 0;
        // The flex count held for the show (5..10).
        virtual uint8 ShowPlayers() const = 0;
        // Rend's guid (his current victim is the other tank on the failing path).
        virtual ObjectGuid RendGuid() const = 0;
    };

    // Gyth's AI as Rend sees it.
    class GythDrake
    {
    public:
        virtual ~GythDrake() = default;

        // Rend's show owns him (the summoner); `heroic` and the count are the show's.
        virtual void JoinShow(ObjectGuid rend, uint8 players) = 0;
        // RG6: he rises over the portcullis end for `ms` (no melee, no acid; the tank he left keeps its stacks held),
        // then lands and takes that tank back. Refused while he walks in (false).
        virtual bool Hover(uint32 ms) = 0;
        virtual bool Hovering() const = 0;
        // Fighting the group (engaged, walked in): the rounds' registry owner (RendGythLogic.h RoundOwnerFor).
        virtual bool Fighting() const = 0;
        // RG6: the breath that sends a wall (the look, Chromatic Protection: Frost).
        virtual void BreatheWall() = 0;
        // RG9: he turns on the marked player and breathes (the look, Chromatic Protection: Fire). The hits are the
        // registry's.
        virtual void BreatheAt(Unit* target) = 0;
        // RG3: Rend left the saddle (the model swap goes; the riderless front starts 5 s later).
        virtual void Dismount() = 0;
        virtual bool Riderless() const = 0;
        // Rend died with him alive (the failing path): the show's descriptor goes with Nefarius's encounter, so his own
        // encounter gets his kill entry and, at 10, his taunt swap (R-2 m-1).
        virtual void RendFell() = 0;
    };
}

#endif
