/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef MODULE_DPSSIM_SIMREPORT_H
#define MODULE_DPSSIM_SIMREPORT_H

#include "SimDaemon.h"
#include <string>

// Serializes one RunResult (plus the RunConfig that produced it) to a JSON file, for later
// rendering into the M3 HTML DPS-breakdown report - see the plan doc's Forward-look section.
// Deliberately does NOT resolve spell names, build HTML, or do anything presentation-layer here:
// per the user's own direction (2026-09-11), spell-id-to-name lookups happen when the report is
// built (outside this process, against the DB directly), not inside the sim. This keeps the C++
// side simple (no DB-query plumbing, no HTML templating, no new third-party JSON library - this
// repo has none vendored, so output is hand-written, not parsed - see SimReport.cpp) and keeps
// the JSON schema stable regardless of how spell names end up getting looked up later.
namespace SimReport
{
    // Writes `result` (and the `config` that produced it) as a JSON file at `path`. Returns false
    // (logging why) on failure to open/write the file - most likely `path`'s directory not
    // existing (this does not create directories).
    //
    // Schema (top-level object):
    //   "config":  {actorLevel, targetLevel, spellPower, durationMs, targetCount, targetSpreadYards,
    //               targetRank ("boss"|"elite")}
    //   "summary": {elapsedMs, totalDamage, dps, castCount, critCount, critRatePct, actorDiedAtMs, dpsPerTarget,
    //               targetSwitches} - dps is total damage across every dummy / duration, dpsPerTarget that over
    //               targetCount; targetSwitches is RunResult::TargetSwitches.
    //   "spells":  [{spellId, isPet, hitCount, critCount, totalDamage, pctOfTotal, castCount, targetsHit}, ...] -
    //              castCount is the cast log's count for that spell id (triggered included, 0 for a pet row), so
    //              hitCount / castCount is hits per cast; targetsHit is the number of distinct dummies hit.
    //              Aggregated from
    //              HitSpellIds/HitDamages/HitCrits, one entry per distinct (spell id, isPet) pair - isPet marks
    //              damage dealt by the actor's pet/guardian/totem (S0 stage; periodic ticks are recorded under
    //              the aura's spell id too) - sorted by
    //              totalDamage descending. hitCount counts every landed hit: direct hits, DoT ticks
    //              and pet/guardian hits alike, so for a DoT or a pet spell it is not a cast count
    //              (per-spell casts are castCount above).
    //   "hits":    [{timestampMs, spellId, damage, crit, isPet, target}, ...] in landing order; target is the dummy
    //              index.
    //   "auraEvents": [{timestampMs, unit ("actor"|"target"), spellId, stackAmount, positive,
    //                  applied, targetIndex}, ...] - see RunResult::AuraEvent's doc comment for field meanings
    //                  (targetIndex -1 = on the actor).
    //   "manaSamples": [{timestampMs, manaPct}, ...] - actor's mana, sampled periodically rather
    //                  than every tick, see RunResult::ManaSamples's doc comment.
    //   "casts": [{timestampMs, spellId, triggered, target}, ...] - every spell the actor cast, in cast
    //             order, damage or not (Evocation, self-buffs, ...) - see RunResult::CastEvents's
    //             doc comment. Distinct from "hits" above: a cast here is logged the moment it
    //             fires (Spell::cast() completing), a hit in "hits" is logged when a direct-damage
    //             effect actually lands, so a travel-time spell's cast and hit timestamps differ,
    //             and a non-damage cast (Evocation) appears only here, never in "hits". `triggered`
    //             is Spell::IsTriggered() - false for a deliberate cast ("requires a button press"),
    //             true for a proc/internal trigger (a talent's passive effect being granted, a free
    //             proc-triggered cast, ...) - the report groups on this to separate real ability
    //             usage from buffs that just showed up on their own. `target` is the explicit unit target's
    //             dummy index, -1 for self, none, ground or a non-dummy.
    //   "targets": [{index, totalDamage, pctOfTotal}, ...] - damage per dummy, in index order.
    bool WriteJson(std::string const& path, SimDaemon::RunConfig const& config, SimDaemon::RunResult const& result);
}

#endif
