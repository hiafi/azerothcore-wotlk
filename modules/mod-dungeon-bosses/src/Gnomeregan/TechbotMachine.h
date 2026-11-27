/*
 * mod-dungeon-bosses, Gnomeregan D1: the Duplicator machine's engine half (GnomereganMachines.h, handoff section 3.2
 * item 7; SP TB3, MT16). The pure half (the clock per tracked unit) is TechbotLogic.h DupRule / DupClock.
 *
 * How it runs (TechbotMachine.cpp), for any owner:
 *   - Track(unit) starts the unit's life clock; at `firstAfterMs` of life (then every `repeatMs`; 0 once) the unit
 *     casts `barSpellId` on itself (not triggered: a kick or a stun stops it, the reward), says `emoteGroup` and,
 *     when the bar completes, the owner summons a copy of the same entry beside it at the source's current health
 *     (ruling 51).
 *     A due cast waits while `capAlive` tracked units live, the bars in flight counted as the copies they will be; a
 *     completed bar at the cap makes no copy (logged "copy-capped"); a refused start retries in 1 s.
 *   - Completion is the bar's own aura on its caster (the bar spell applies a short aura of itself: techbot.py
 *     214302 / 214303, the hard mode's 214542). A bar spell with an aura is judged by that aura alone (a kick in its
 *     last moments is a stop); one without falls back on the bar's remaining time last seen fitting the time since. A
 *     kicked or stunned bar is lost (a once-only unit never retries).
 *   - The copy: TEMPSUMMON_CORPSE_TIMED_DESPAWN (5 s corpse), tracked by the machine, then `onCopy(source, copy)`;
 *     the owner's AI JustSummoned sees it too (the caller sets targets there or in onCopy, never Track again). A
 *     once-only spec's copies never duplicate (repeatMs 0: normal Dupe Bugs, STAGE-R-1-A DQ1); a repeating spec's
 *     copies run their own clock from the copy.
 *   - Clear() despawns every tracked unit still alive and forgets them all.
 *   - Logs: "gnomer-build <logKey> duplicator <start|stopped|copy|refused|clear> ...".
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_TECHBOT_MACHINE_H
#define MOD_DUNGEON_BOSSES_GNOMER_TECHBOT_MACHINE_H

#include "GnomereganMachines.h"
#include "TechbotLogic.h"

namespace GnomereganMachines
{
    // The spec of Techbot's own Dupe Bugs on a difficulty (the hard mode builds its own spec for the bombs).
    DuplicatorSpec TechbotBugSpec(bool heroic);
}

#endif
