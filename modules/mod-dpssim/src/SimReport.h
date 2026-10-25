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
    //   "powerSamples": [{timestampMs, powerType, power, maxPower[, runes: {blood, frost, unholy, death}]}, ...] - the
    //                  actor's class power every 500 ms in the playerbot DPS run and the tank run (empty in others);
    //                  power and maxPower as the player reads them (rage and runic power are divided by ten), powerType
    //                  the core's Powers enum (6 = runic power); runes (Death Knight only) the READY runes by current
    //                  type, see RunResult::PowerSample.
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

    // The heal-mode counterpart (plan .agents/plans/healing-sim/healing-sim.PLAN.md, section 5): one file per
    // iteration of a heal run, "kind": "heal" at the top level (a DPS report has no "kind"). Hand-written like
    // WriteJson(), spell names stay out of it (looked up when the report is built). All times are ms since the pull.
    //
    // Schema (top-level object):
    //   "kind":    "heal"
    //   "config":  {actorLevel, actorRace, actorClass, durationMs, stepMs, group ("party"|"raid10"|"raid20"),
    //               healTargets (canonical text, SimHeal::TargetsText()), infiniteMana, pinMaxHealth,
    //               allyMaxHealthTank, allyMaxHealthDps, drainPulseMs, allySpreadYards}
    //   "summary": {elapsedMs, effectiveHealing, rawHealing, overhealing, overhealPct, healAbsorbed, absorbHealing,
    //               hps, rawHps, hpsBeforeOom, castCount, triggeredCasts, critRatePct, manaSpent, healingPerMana,
    //               oomAtMs, deaths, firstDeathAtMs, resurrections, actorDiedAtMs, damageDone, dps, wallClockMs,
    //               pinHits, pinRaises, drainHits, driverCastFailures}
    //                hps = (effective healing + absorbs) / elapsed seconds, the headline; rawHps = (raw healing +
    //                absorbs) / seconds, before overheal and heal-absorb. overhealPct = overhealing / rawHealing.
    //                oomAtMs = first mana sample under 5% (null if never, or if the healer had no mana at all);
    //                hpsBeforeOom = (effective + absorbs up to oomAtMs) / oomAtMs, equal to hps when oomAtMs is null.
    //                castCount counts the healer's deliberate casts (not triggered ones); manaSpent sums the power
    //                cost paid at cast time, healingPerMana = (effective + absorbs) / manaSpent. critRatePct =
    //                crits / (direct heals + ticks). damageDone / dps are the healer's own damage to the boss.
    //                deaths counts every death of every target (the healer's own included).
    //   "spells":  [{spellId, isPet, casts, hits, ticks, crits, effective, overheal, overhealPct, healAbsorbed,
    //                absorbed, events, total, pctOfTotal, avgHit, manaSpent, hpm, targetsHit}, ...] by (spellId,
    //                isPet), sorted by total descending. total = effective + absorbed, events = hits + ticks + shield
    //                hits, avgHit = total / events. casts = the cast log's count for that id (triggered included, 0
    //                for a pet row). A spell that was only cast (a buff) has a row with zeros when it cost mana.
    //                hpm = total / manaSpent, null without mana.
    //   "targets": [{index, role, mode ("pin"|"drain"), value, percent, subgroup, maxHealth, healingReceived,
    //                effectiveReceived, absorbReceived, overheal, damageRequested, damageMitigated, damageAbsorbed,
    //                damageTaken, damagePrevented, deaths, diedAtMs, minHealthPct, avgHealthPct, msBelow35Pct,
    //                pinHits, pinRaises}, ...] in index order. damageTaken = health lost to the boss's hits (after
    //                mitigation and shields); damagePrevented = damageAbsorbed + damageMitigated.
    //   "heals", "absorbs", "damageTaken", "healthSamples", "deaths", "resurrections", "groupAuraEvents", "casts"
    //   (with powerCost), "manaSamples": the event arrays of the iteration, field names as in SimHeal.h and
    //   SimDaemon::RunResult.
    bool WriteHealJson(std::string const& path, SimDaemon::RunConfig const& config, SimDaemon::RunResult const& result);

    // The tank-mode counterpart (plan .agents/plans/tank-sim/tank-sim.PLAN.md, sections 4 and 5; tank runs are DPS runs
    // that also get hit): the DPS report exactly as WriteJson() writes it, plus "kind": "tank" as the first key and a
    // "tank" section as the last one. A DPS report has no "kind"; a heal report has "kind": "heal".
    //
    // Time bases: swing timestamps are the tick start, samples (health, power, threat) and the time of death are read
    // after the tick, so the swing that killed the actor is stamped one step before "actorDiedAtMs". All times are ms
    // since the pull. Rates (DTPS, net DTPS, self-HPS, power per second) divide by "rateBaseMs": the time of death in
    // the survive scenario when the actor died, the full duration otherwise.
    //
    // The "tank" object:
    //   "config":  {scenario ("dps"|"survive"), hitDamage {min,max} (the boss), packHitDamage {min,max}, dummyKind
    //               ("boss" = a single target, whatever its rank; "pack" = 2 or more targets), dummyCount, swingMs,
    //               dummyCrit, stepMs, pullAuras [spell ids], dummies [{index, hitMin, hitMax, swingMs, level,
    //               levelForTarget, armor, expectedCritPct (after the first second), weaponMin, weaponMax, attackPower,
    //               damageModifier, basePct, fieldMin, fieldMax}]}
    //   "actor":   {afterFirstSecond, atPull}, each {level, health, armor, defenseSkill, maxSkillForLevel, dodgePct,
    //               parryPct, blockPct, blockValue, critImmune}. afterFirstSecond is the character sheet (stance and
    //               the first buffs up), atPull the read before the bot acted.
    //   "summary": {scenario, rateBaseMs, swings, swingsLanded, swingsOutsideFrontArc, outcomes {miss, dodge, parry,
    //               block, fullBlock, crit, crush, hit, glancing, other} (counts), outcomePct (same keys, percent of
    //               all swings), blockAnyPct (block + fullBlock), avoidancePct (miss + dodge + parry), expectedPct
    //               {miss, dodge, parry, block, crit} (what the core rolled, mean over the swings), expectedCritPct,
    //               observedCritPct, critBugCount (crits on a swing whose rolled crit chance was 0), critBugAtMs [ms],
    //               mitigation {avoided, armor, block, absorb, resist, taken, gross} (damage, gross = their sum),
    //               mitigationPct (percent of gross), preArmorDamage, damageTaken (post-absorb), damageAbsorbed, dtps,
    //               dtpsBeforeShields, selfHealEffective, selfHealOverheal, selfHealOverhealPct, selfHps, netDtps,
    //               ttdMs (survive: the time of death, or the duration when the actor lived; null in dps), survived,
    //               died, minHealthPct, msUnder35Pct (the health samples under 35%, each up to the next sample but not
    //               past rateBaseMs), powerType (POWER_*, the type most samples were in), rageGained / rageGainedPerSec
    //               (the actor's rage across the swings, damage-taken rage and procs; display units; rage only, so 0
    //               for a tank on another resource), rageSwingsMeasured, avoidedSwingsMeasured, avoidedSwingsWithRage,
    //               tps, dpsAlive, tpsAlive, totalThreat, lowestThreat, lowestThreatDummy}
    //               netDtps = (damageTaken - selfHealEffective) / seconds. damageTaken is already after the shields, so
    //               the absorbs are never subtracted again. mitigation.avoided is the pre-armor damage of the swings
    //               that missed, dodged or parried. dpsAlive / tpsAlive = the actor's damage / the threat on the
    //               dummies over rateBaseMs (the time alive: the time of death, else the duration), and tps is the same
    //               number as tpsAlive; the top-level summary.dps stays total damage over the full duration, as in
    //               every DPS report.
    //               critBugCount counts a crit on a swing whose own rolled crit chance was 0 (SwingEvent::ExpectedCrit,
    //               read in the roll hook). The run log's warning is wider: it also fires on any crit when the first
    //               dummy's expected crit was 0 at the pull, so the log can flag a run the JSON count calls clean.
    //   "perDummy": [{index, swings, outcomes, outcomePct, preArmorDamage, damageTaken, swingsOutsideFrontArc, threat}]
    //               - outcomes / outcomePct hold the full outcome split of that dummy's swings, as in summary
    //   "absorbsBySpell": [{spellId, amount, events, pctOfAbsorbed}] - the shields that took damage off the swings,
    //               from SwingAbsorbs only (RunResult::AbsorbEvents describe the same shields: never add them).
    //   "selfHeals": [{spellId, isPet, casts, hits, ticks, crits, effective, overheal, overhealPct, healAbsorbed}]
    //   "swings":  [{timestampMs, dummy, outcome, preArmor, armor, blocked, absorbed, resisted, final, rageTenths
    //               (null without rage), expected {miss, dodge, parry, block, crit} (percent), inFrontArc, takenMult}]
    //   "samples": [{timestampMs, health, maxHealth, powerType, power, maxPower, bulwarkStacks}] every 500 ms; rage
    //               and runic power are in display units (the core stores them x10). The dps scenario's samples are
    //               read before the step's health refill.
    //   "threat":  [{dummy, samples: [[timestampMs, threat], ...]}] every second
    bool WriteTankJson(std::string const& path, SimDaemon::RunConfig const& config, SimDaemon::RunResult const& result);
}

#endif
